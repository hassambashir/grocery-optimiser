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
    recipes = [r for r in read_csv("data/recipes.csv") if r["readiness"] == "ready_for_existing_optimizer"]
    lines = [line for line in read_csv("data/recipe_ingredients.csv") if line["recipe_id"] in {recipe["recipe_id"] for recipe in recipes}]
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
    snapshot_unavailable = set()
    compatible_products = set()
    for p in products:
        i = p["ingredient_id"]
        if i not in used:
            continue
        if p["mapping_status"] == "compatible_candidate":
            compatible_products.add(p["product_id"])
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
        if p["availability_status"] == "out_of_stock":
            snapshot_unavailable.add(p["product_id"])

    missing = sorted(i for i in used if not available[i] and inventory[i] <= 0)
    if missing:
        raise ValueError("Ingredients without retail supply or stock: " + ", ".join(missing))

    model = pulp.LpProblem("weekly_grocery_plan", pulp.LpMinimize)
    chosen = {r["recipe_id"]: pulp.LpVariable("meal_" + r["recipe_id"], cat="Binary") for r in recipes}
    model += pulp.lpSum(chosen.values()) == days, "dinner_count"
    # Diversity constraints apply only when tagged, model-ready options exist.
    catalogue = {r["recipe_id"]: r for r in recipes}
    if days >= 4:
        for field, cap in (("main_protein", max(2, (days + 1) // 2)),
                           ("cooking_method", max(2, (days + 1) // 2))):
            groups = defaultdict(list)
            for r in recipes:
                value = catalogue.get(r["recipe_id"], {}).get(field, "").strip().lower()
                if value:
                    groups[value].append(chosen[r["recipe_id"]])
            for value, variables in groups.items():
                # Do not make a chicken-only seed dataset infeasible.
                if len(recipes) - len(variables) < days - cap:
                    continue
                model += pulp.lpSum(variables) <= cap, "diversity_" + field + "_" + value.replace("-", "_").replace(" ", "_")


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
    recipe_consumption = []
    for n, row in enumerate(lines):
        rid, i = row["recipe_id"], row["ingredient_id"]
        preferred = float(row["preferred_quantity"])
        klass = flex[ingredients[i]["default_flexibility_class"]]
        low, high = float(klass["min_factor"]), float(klass["max_factor"])
        amount = pulp.LpVariable("use_" + str(n), lowBound=0, cat="Integer" if ingredients[i]["preferred_model_unit"] == "each" else "Continuous")
        model += amount >= preferred * low * chosen[rid]
        model += amount <= preferred * high * chosen[rid]
        consumption[i].append(amount)
        recipe_consumption.append((rid, i, preferred, amount))
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
    flagged = [p["product_name"] for p, _, _ in bought if p["product_id"] in snapshot_unavailable]
    if flagged:
        print("WARNING: Snapshot marks purchased products out of stock (prototype ignores stock status):")
        for name in flagged:
            print("  " + name)
    compatible_selected = [p["product_name"] for p, _, _ in bought if p["product_id"] in compatible_products]
    if compatible_selected:
        print("WARNING: Purchased compatible-but-not-exact product mappings; review before shopping:")
        for name in compatible_selected:
            print("  " + name)
    print("\nIngredient consumption and estimated value:")
    # Weighted-average valuation. Opening inventory has no recorded cost basis:
    # estimate its unit value using the cheapest listed retail unit price.
    total_consumption_value = 0.0
    for i in sorted(used):
        used_qty = sum(pulp.value(x) for x in consumption[i])
        if used_qty < 0.0001:
            continue
        purchases = [(qty * pulp.value(purchase[p["product_id"]]), price * pulp.value(purchase[p["product_id"]]))
                     for p, qty, price in available[i]]
        purchased_qty = sum(q for q, _ in purchases)
        purchased_cost = sum(c for _, c in purchases)
        opening_qty = inventory[i]
        opening_unit_estimate = min((price / qty for _, qty, price in available[i]), default=0.0)
        opening_estimated_value = opening_qty * opening_unit_estimate
        unit_cost = ((purchased_cost + opening_estimated_value) / (purchased_qty + opening_qty)
                     if purchased_qty + opening_qty > 0 else 0.0)
        value = used_qty * unit_cost
        total_consumption_value += value
        print("  " + i + ": " + format(used_qty, ".1f") + " " +
              ingredients[i]["preferred_model_unit"] + " | estimated GBP " + format(value, ".2f"))
    print("Estimated consumed-ingredient value (includes opening stock): GBP " +
          format(total_consumption_value, ".2f"))
    print("VALUATION NOTE: Weighted-average cost; opening inventory valued at lowest snapshot retail unit price.")
    print("This is an estimate, not this week's cash spend or measured food waste.")
    print("\nPer-recipe ingredient quantities (preferred -> actual):")
    for rid, i, preferred, amount in recipe_consumption:
        if pulp.value(chosen[rid]) > 0.5:
            print("  " + rid + " " + i + ": " + format(preferred, ".1f") + " -> " +
                  format(pulp.value(amount), ".1f") + " " + ingredients[i]["preferred_model_unit"])
    print("Fresh surplus risk proxy: GBP " + format(sum(pulp.value(x) for x in risk), ".2f"))
    print("Quantity shortfall penalty: " + format(sum(pulp.value(x) for x in deviation_cost), ".2f"))
    print("Ending inventory (nonzero):")
    for i, v in sorted(end.items()):
        if pulp.value(v) > 0.01:
            print("  " + i + ": " + format(pulp.value(v), ".1f") + " " + ingredients[i]["preferred_model_unit"])
    return {"status": "Optimal", "recipes": selected, "basket": bought, "spend_gbp": spent,
            "ending_inventory": {i: pulp.value(v) for i, v in end.items()},
            "consumption_value_gbp_estimate": total_consumption_value}

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--days", type=int, default=7)
    parser.add_argument("--fresh-penalty", type=float, default=0.50)
    parser.add_argument("--deviation-penalty", type=float, default=2.0)
    parser.add_argument("--show-solver", action="store_true")
    args = parser.parse_args()
    solve(args.days, args.fresh_penalty, args.deviation_penalty, args.show_solver)
