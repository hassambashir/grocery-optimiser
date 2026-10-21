#!/usr/bin/env python3
"""First weekly household MILP. Install: pip install pulp
Run from repository root: python scripts/optimise_week.py
This is a deterministic prototype; surplus-risk is NOT measured food waste.
"""
import argparse
import csv
from collections import defaultdict
from pathlib import Path

import pulp

ROOT = Path(__file__).resolve().parents[1]

def read_csv(path):
    with (ROOT / path).open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))

def solve(days=7, fresh_penalty=0.50, deviation_penalty=2.0, show_solver=False):
    recipes = read_csv("data/recipes.csv")
    lines = read_csv("data/recipe_ingredients.csv")
    ingredients = {r["ingredient_id"]: r for r in read_csv("data/ingredients.csv")}
    products = read_csv("data/products.csv")
    flex = {r["flexibility_class"]: r for r in read_csv("config/flexibility_classes.csv")}
    inventory = defaultdict(float)
    for row in read_csv("config/initial_inventory.csv"):
        ingredient = row["ingredient_id"]
        if row["unit"] != ingredients[ingredient]["preferred_model_unit"]:
            raise ValueError("Initial inventory unit mismatch for " + ingredient)
        inventory[ingredient] += float(row["quantity"])

    if not 1 <= days <= len(recipes):
        raise ValueError("days must be between 1 and the number of distinct recipes")
    if min(fresh_penalty, deviation_penalty) < 0:
        raise ValueError("Penalty weights must be non-negative")

    used = {r["ingredient_id"] for r in lines}
    available = defaultdict(list)
    for p in products:
        i = p["ingredient_id"]
        if i not in used or p["availability_status"] == "out_of_stock":
            continue
        if p["mapping_status"] == "substitution_candidate":
            continue  # Mixed-colour peppers etc. need explicit approval.
        if p["regular_price_gbp"] == "":
            continue
        unit = p["usable_unit"] or p["pack_unit"]
        if unit != ingredients[i]["preferred_model_unit"]:
            raise ValueError("Pack unit mismatch: " + p["product_id"])
        qty = float(p["usable_quantity"] or p["pack_quantity"])
        if qty <= 0:
            raise ValueError("Nonpositive pack quantity: " + p["product_id"])
        available[i].append((p, qty, float(p["regular_price_gbp"])))

    missing = sorted(i for i in used if not available[i] and inventory[i] <= 0)
    if missing:
        raise ValueError("Ingredients without retail supply or stock: " + ", ".join(missing))

    model = pulp.LpProblem("weekly_grocery_plan", pulp.LpMinimize)
    chosen = {r["recipe_id"]: pulp.LpVariable("meal_" + r["recipe_id"], cat="Binary") for r in recipes}
    model += pulp.lpSum(chosen.values()) == days, "dinner_count"

    purchase, supply, cost = {}, defaultdict(list), []
    for i in used:
        for p, qty, price in available[i]:
            pid = p["product_id"]
            # Loose produce: multiples of the Tesco reference weight, not arbitrary fractions.
            # Thus the selected quantity is an approximation, NOT true variable-weight pricing.
            v = pulp.LpVariable("packs_" + pid, lowBound=0, cat="Integer")
            purchase[pid] = v
            supply[i].append(qty * v)
            cost.append(price * v)

    consumption, deviation_cost = defaultdict(list), []
    for n, row in enumerate(lines):
        rid, i = row["recipe_id"], row["ingredient_id"]
        preferred = float(row["preferred_quantity"])
        klass = flex[ingredients[i]["default_flexibility_class"]]
        low, high = float(klass["min_factor"]), float(klass["max_factor"])
        amount = pulp.LpVariable("use_" + str(n), lowBound=0)
        model += amount >= preferred * low * chosen[rid]
        model += amount <= preferred * high * chosen[rid]
        consumption[i].append(amount)
        # Discourage systematically shrinking portions; unitless proportional deviation.
        shortfall = pulp.LpVariable("shortfall_" + str(n), lowBound=0)
        model += shortfall >= preferred * chosen[rid] - amount
        deviation_cost.append(deviation_penalty * shortfall / preferred)

    end, risk = {}, []
    for i in sorted(used):
        v = pulp.LpVariable("end_" + i, lowBound=0)
        end[i] = v
        model += v == inventory[i] + pulp.lpSum(supply[i]) - pulp.lpSum(consumption[i])
        if ingredients[i]["shelf_life_class"] == "short":
            # Proxy: penalise the VALUE of fresh ending stock, not its mass.
            # This does not assert that all fresh leftovers spoil.
            prices = [price / qty for _, qty, price in available[i]]
            if prices:
                risk.append(fresh_penalty * min(prices) * v)

    model += pulp.lpSum(cost) + pulp.lpSum(risk) + pulp.lpSum(deviation_cost)
    status = model.solve(pulp.PULP_CBC_CMD(msg=show_solver))
    if pulp.LpStatus[status] != "Optimal":
        raise RuntimeError("Solver status: " + pulp.LpStatus[status])

    selected = [r for r in recipes if pulp.value(chosen[r["recipe_id"]]) > 0.5]
    bought = []
    for p in products:
        v = purchase.get(p["product_id"])
        if v is not None and pulp.value(v) > 0.001:
            bought.append((p, round(pulp.value(v)), float(p["regular_price_gbp"]) * pulp.value(v)))
    spent = sum(x[2] for x in bought)
    print("Selected two-person dinners (" + str(days) + "):")
    for r in selected:
        print("  " + r["recipe_id"] + " " + r["recipe_name"])
    print("\nTesco shopping basket (regular-price snapshot):")
    for p, n, amount in bought:
        print("  " + str(n) + " x " + p["product_name"] + " | GBP " + format(amount, ".2f"))
    print("\nShopping cost: GBP " + format(spent, ".2f"))
    print("Fresh surplus risk proxy: GBP " + format(sum(pulp.value(x) for x in risk), ".2f"))
    print("Quantity shortfall penalty: " + format(sum(pulp.value(x) for x in deviation_cost), ".2f"))
    print("Ending inventory (nonzero):")
    for i, v in sorted(end.items()):
        if pulp.value(v) > 0.01:
            print("  " + i + ": " + format(pulp.value(v), ".1f") + " " + ingredients[i]["preferred_model_unit"])
    return {"status": "Optimal", "recipes": selected, "basket": bought, "spend_gbp": spent,
            "ending_inventory": {i: pulp.value(v) for i, v in end.items()}}

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--days", type=int, default=7)
    parser.add_argument("--fresh-penalty", type=float, default=0.50)
    parser.add_argument("--deviation-penalty", type=float, default=2.0)
    parser.add_argument("--show-solver", action="store_true")
    args = parser.parse_args()
    solve(args.days, args.fresh_penalty, args.deviation_penalty, args.show_solver)
