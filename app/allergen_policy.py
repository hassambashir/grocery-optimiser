"""Household allergen policy: convert label evidence into solver-ready choices.

The mathematical optimiser receives only eligible products and numeric penalties.
Unknown is never assumed free. Inventory without product provenance is not safe
for strict exclusions.
"""
from collections import defaultdict

STATUSES = frozenset(("contains", "may_contain", "free", "unknown"))
MODES = frozenset(("strict", "preference"))
# Provisional optimisation weights, not retail costs or medical risk scores.
DEFAULT_PENALTIES = {"free": 0.0, "unknown": 2.0, "may_contain": 3.0, "contains": 10.0}


def prepare(products, product_allergens, rules, ingredients, recipes, lines,
            inventory=None, penalties=None):
    if not isinstance(rules, dict) or any(mode not in MODES for mode in rules.values()):
        raise ValueError("Allergen rules must use strict or preference.")
    inventory = inventory or {}
    if inventory and "strict" in rules.values():
        raise ValueError("Strict allergen planning requires product-verified inventory; ingredient-only stock cannot be certified.")
    penalties = penalties or DEFAULT_PENALTIES
    if set(penalties) != STATUSES or any(not isinstance(v, (int, float)) or v < 0 for v in penalties.values()):
        raise ValueError("Invalid allergen preference penalty weights.")
    status = {(r["product_id"], r["allergen_id"]): r["status"]
              for r in product_allergens}
    eligible = []
    costs = {}
    excluded = defaultdict(list)
    for product in products:
        pid = product["product_id"]
        reasons = [a for a, mode in rules.items()
                   if mode == "strict" and status.get((pid, a), "unknown") != "free"]
        if reasons:
            excluded[product["ingredient_id"]].append({"product_id": pid, "allergens": reasons})
            continue
        eligible.append(product)
        costs[pid] = sum(penalties[status.get((pid, a), "unknown")]
                         for a, mode in rules.items() if mode == "preference")
    from catalogue import exclusion_reason
    supplied = {p["ingredient_id"] for p in eligible if not exclusion_reason(p, ingredients)}
    supplied.update(i for i, q in inventory.items() if q > 0)
    required = defaultdict(set)
    for line in lines:
        required[line["recipe_id"]].add(line["ingredient_id"])
    unavailable = {r["recipe_id"]: sorted(required[r["recipe_id"]] - supplied)
                   for r in recipes if required[r["recipe_id"]] - supplied}
    return {"products": eligible, "product_penalties": costs,
            "unavailable_recipes": unavailable, "excluded_products": dict(excluded)}
