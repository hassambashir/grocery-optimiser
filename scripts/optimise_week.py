#!/usr/bin/env python3
"""First weekly household MILP. Install: pip install pulp
Run from repository root: python scripts/optimise_week.py
This is a deterministic prototype; surplus-risk is NOT measured food waste.
"""
import argparse
import csv
import json
import math
from collections import defaultdict
from pathlib import Path

import pulp

from catalogue import ROOT, read_csv, exclusion_reason, effective_pack, consumption_step, positive


def solve(days=7, fresh_penalty=0.50, deviation_penalty=2.0, show_solver=False,
          inventory_path="config/initial_inventory.csv", required_recipes=None):
    catalogue = read_csv("data/recipes.csv")
    all_lines = read_csv("data/recipe_ingredients.csv")
    ingredients = {r["ingredient_id"]: r for r in read_csv("data/ingredients.csv")}
    products = read_csv("data/products.csv")
    inventory_rows = read_csv(inventory_path)
    inventory_ids = {r["ingredient_id"] for r in inventory_rows if float(r["quantity"]) > 0}
    supplied = {p["ingredient_id"] for p in products if not exclusion_reason(p, ingredients)}
    required = defaultdict(set)
    for line in all_lines:
        required[line["recipe_id"]].add(line["ingredient_id"])
    requested = set(required_recipes or [])
    known_ids = {r["recipe_id"] for r in catalogue}
    if requested - known_ids:
        raise ValueError("Unknown requested recipes: " + ", ".join(sorted(requested - known_ids)))
    recipes = [r for r in catalogue if required[r["recipe_id"]]
               and required[r["recipe_id"]] <= supplied | inventory_ids]
    eligible_ids = {r["recipe_id"] for r in recipes}
    if requested - eligible_ids:
        raise ValueError("Requested recipes lack eligible supply: " + ", ".join(sorted(requested - eligible_ids)))
    lines = [line for line in all_lines if line["recipe_id"] in eligible_ids]
    print(f"Eligible recipes: {len(recipes)} of {len(catalogue)} (based on ingredient supply)")
    flex = {r["flexibility_class"]: r for r in read_csv("config/flexibility_classes.csv")}
    inventory = defaultdict(float)
    for row in inventory_rows:
        ingredient = row["ingredient_id"]
        if row["unit"] != ingredients[ingredient]["preferred_model_unit"]:
            raise ValueError("Initial inventory unit mismatch for " + ingredient)
        if not positive(row["quantity"], allow_zero=True):
            raise ValueError("Invalid initial inventory quantity: " + ingredient)
        inventory[ingredient] += float(row["quantity"])

    if not 1 <= days <= len(recipes):
        raise ValueError("days must be between 1 and the number of distinct recipes")
    if not all(math.isfinite(x) and x >= 0 for x in (fresh_penalty, deviation_penalty)):
        raise ValueError("Penalty weights must be non-negative")

    used = {r["ingredient_id"] for r in lines}
    available = defaultdict(list)
    for p in products:
        i = p["ingredient_id"]
        if i not in used or exclusion_reason(p, ingredients):
            continue
        qty, _ = effective_pack(p)
        available[i].append((p, qty, float(p["regular_price_gbp"])))

    missing = sorted(i for i in used if not available[i] and inventory[i] <= 0)
    if missing:
        raise ValueError("Ingredients without retail supply or stock: " + ", ".join(missing))

    model = pulp.LpProblem("weekly_grocery_plan", pulp.LpMinimize)
    chosen = {r["recipe_id"]: pulp.LpVariable("meal_" + r["recipe_id"], cat="Binary") for r in recipes}
    model += pulp.lpSum(chosen.values()) == days, "dinner_count"
    for rid in sorted(requested):
        model += chosen[rid] == 1, "required_" + rid
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
    for i in sorted(used):
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
        step = consumption_step(i, ingredients[i]["preferred_model_unit"])
        amount = pulp.LpVariable("use_" + str(n), lowBound=0)
        if step:
            portions = pulp.LpVariable("portions_" + str(n), lowBound=0, cat="Integer")
            model += amount == step * portions
        model += amount >= preferred * low * chosen[rid]
        model += amount <= preferred * high * chosen[rid]
        consumption[i].append(amount)
        recipe_consumption.append((rid, i, preferred, amount))
        # Penalise BOTH shrinking and inflating portions; leftovers need not be eaten.
        shortfall = pulp.LpVariable("shortfall_" + str(n), lowBound=0)
        model += shortfall >= preferred * chosen[rid] - amount
        model += shortfall >= amount - preferred * chosen[rid]
        deviation_cost.append(deviation_penalty * shortfall / preferred)

    end, risk = {}, []
    for i in sorted(used | set(inventory)):
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
    if pulp.LpStatus[status] != "Optimal" or model.sol_status != pulp.LpSolutionOptimal:
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
        qty, unit = effective_pack(p)
        quantity_note = f" | usable {qty * n:g} {unit}"
        # Counts are guidance only; gram quantities remain authoritative.
        typical_weight = {"carrot": 61, "tomatoes": 80}.get(p["ingredient_id"])
        if unit == "g" and typical_weight:
            quantity_note += f" (about {qty * n / typical_weight:.0f} items; size and charged weight may vary)"
        print("  " + str(n) + " x " + p["product_name"] + quantity_note + " | GBP " + format(amount, ".2f"))
    print("\nShopping cost: GBP " + format(spent, ".2f"))
    print("PLANNING NOTE: Loose-produce weights, edible yields and converted usable quantities are estimates; checkout quantities and charges may vary.")
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
    print("Quantity deviation penalty: " + format(sum(pulp.value(x) for x in deviation_cost), ".2f"))
    print("Ending inventory (nonzero):")
    for i, v in sorted(end.items()):
        if pulp.value(v) > 0.01:
            print("  " + i + ": " + format(pulp.value(v), ".1f") + " " + ingredients[i]["preferred_model_unit"])
    actual = [{"recipe_id": rid, "ingredient_id": i, "preferred_quantity": preferred,
               "quantity": pulp.value(amount), "unit": ingredients[i]["preferred_model_unit"]}
              for rid, i, preferred, amount in recipe_consumption if pulp.value(chosen[rid]) > 0.5]
    # Independent arithmetic checks against solver output before declaring success.
    if len(selected) != days or len({r["recipe_id"] for r in selected}) != days:
        raise RuntimeError("Incorrect number of distinct dinners")
    for p, count, _ in bought:
        raw = pulp.value(purchase[p["product_id"]])
        if count < 1 or abs(raw - count) > 1e-5 or exclusion_reason(p, ingredients):
            raise RuntimeError("Invalid retail purchase: " + p["product_id"])
    for i, value in end.items():
        expected = inventory[i] + sum(effective_pack(p)[0] * n for p, n, _ in bought if p["ingredient_id"] == i) - sum(r["quantity"] for r in actual if r["ingredient_id"] == i)
        if expected < -1e-4 or abs(expected - pulp.value(value)) > 1e-4:
            raise RuntimeError("Inventory balance failed: " + i)
    return {"status": "Optimal", "recipes": selected, "basket": bought, "spend_gbp": spent,
            "eligible_recipe_count": len(recipes), "consumption": actual,
            "opening_inventory": dict(inventory),
            "ending_inventory": {i: pulp.value(v) for i, v in end.items()},
            "fresh_surplus_penalty": sum(pulp.value(x) for x in risk),
            "quantity_deviation_penalty": sum(pulp.value(x) for x in deviation_cost),
            "objective": pulp.value(model.objective),
            "consumption_value_gbp_estimate": total_consumption_value}

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--days", type=int, default=7)
    parser.add_argument("--fresh-penalty", type=float, default=0.50)
    parser.add_argument("--deviation-penalty", type=float, default=2.0)
    parser.add_argument("--show-solver", action="store_true")
    parser.add_argument("--inventory", default="config/initial_inventory.csv")
    parser.add_argument("--require-recipes", nargs="*", default=[])
    parser.add_argument("--output-json")
    parser.add_argument("--ending-inventory")
    args = parser.parse_args()
    from validate_seed_data import validate
    errors, _ = validate()
    if errors:
        raise ValueError("Dataset validation failed:\n" + "\n".join(errors))
    result = solve(args.days, args.fresh_penalty, args.deviation_penalty, args.show_solver,
                   args.inventory, args.require_recipes)
    if args.output_json:
        Path(args.output_json).write_text(json.dumps(result, indent=2) + "\n")
    if args.ending_inventory:
        units = {r["ingredient_id"]: r["preferred_model_unit"] for r in read_csv("data/ingredients.csv")}
        with Path(args.ending_inventory).open("w", newline="") as handle:
            writer = csv.DictWriter(handle, fieldnames=["ingredient_id", "quantity", "unit", "inventory_policy", "notes"])
            writer.writeheader()
            for i, qty in sorted(result["ending_inventory"].items()):
                if qty > 1e-6:
                    writer.writerow(dict(ingredient_id=i, quantity=round(qty, 6), unit=units[i],
                                         inventory_policy="carried_forward", notes="Check usable condition before next week."))

