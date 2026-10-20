"""Validate the model-ready seed dataset.

Uses only the Python standard library. Run from the repository root:

    python scripts/validate_seed_data.py
"""

from __future__ import annotations

import csv
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def read_csv(relative_path: str) -> list[dict[str, str]]:
    with (ROOT / relative_path).open(newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def require(condition: bool, message: str, errors: list[str]) -> None:
    if not condition:
        errors.append(message)


def require_unique(rows: list[dict[str, str]], key: str, label: str, errors: list[str]) -> None:
    counts = Counter(row[key] for row in rows if row.get(key))
    for value, count in counts.items():
        require(count == 1, f"Duplicate {label}: {value}", errors)


def main() -> int:
    recipes = read_csv("data/recipes.csv")
    recipe_ingredients = read_csv("data/recipe_ingredients.csv")
    ingredients = read_csv("data/ingredients.csv")
    products = read_csv("data/products.csv")
    conversions = read_csv("data/unit_conversions.csv")
    flexibility = read_csv("config/flexibility_classes.csv")
    inventory = read_csv("config/initial_inventory.csv")

    errors: list[str] = []

    require_unique(recipes, "recipe_id", "recipe_id", errors)
    require_unique(ingredients, "ingredient_id", "ingredient_id", errors)
    require_unique(products, "product_id", "product_id", errors)
    require_unique(conversions, "conversion_id", "conversion_id", errors)

    recipe_ids = {r["recipe_id"] for r in recipes}
    ingredient_map = {r["ingredient_id"]: r for r in ingredients}
    ingredient_ids = set(ingredient_map)
    product_ingredient_ids = {r["ingredient_id"] for r in products}
    staple_ids = {
        r["ingredient_id"]
        for r in ingredients
        if r["inventory_policy"] == "assumed_on_hand_staple"
    }
    flex_classes = {r["flexibility_class"] for r in flexibility}

    for row in recipe_ingredients:
        rid = row["recipe_id"]
        iid = row["ingredient_id"]
        require(rid in recipe_ids, f"Unknown recipe_id in recipe_ingredients: {rid}", errors)
        require(iid in ingredient_ids, f"Unknown ingredient_id in recipe_ingredients: {iid}", errors)
        require(bool(row["normalized_quantity"]), f"Missing normalized_quantity: {rid}/{iid}", errors)
        require(bool(row["normalized_unit"]), f"Missing normalized_unit: {rid}/{iid}", errors)
        try:
            require(float(row["normalized_quantity"]) > 0, f"Non-positive normalized quantity: {rid}/{iid}", errors)
        except ValueError:
            errors.append(f"Non-numeric normalized quantity: {rid}/{iid}")

        if iid in ingredient_map:
            require(
                row["normalized_unit"] == ingredient_map[iid]["preferred_model_unit"],
                f"Recipe/model unit mismatch: {rid}/{iid}",
                errors,
            )

    used_ids = {r["ingredient_id"] for r in recipe_ingredients}
    for iid in sorted(used_ids):
        require(
            iid in product_ingredient_ids or iid in staple_ids,
            f"No retail supply or assumed-on-hand policy for: {iid}",
            errors,
        )

    for row in ingredients:
        fc = row["default_flexibility_class"]
        require(bool(fc), f"Missing default flexibility class: {row['ingredient_id']}", errors)
        require(fc in flex_classes, f"Unknown flexibility class {fc}: {row['ingredient_id']}", errors)
        require(
            row["shelf_life_class"] in {"short", "medium", "long", "unknown"},
            f"Unknown shelf_life_class: {row['ingredient_id']}",
            errors,
        )

    for row in products:
        pid = row["product_id"]
        iid = row["ingredient_id"]
        require(iid in ingredient_ids, f"Unknown ingredient on product {pid}", errors)

        try:
            require(float(row["pack_quantity"]) > 0, f"Non-positive pack quantity: {pid}", errors)
        except ValueError:
            errors.append(f"Non-numeric pack quantity: {pid}")

        try:
            require(float(row["regular_price_gbp"]) >= 0, f"Negative price: {pid}", errors)
        except ValueError:
            errors.append(f"Non-numeric regular price: {pid}")

        if row["usable_quantity"]:
            require(bool(row["usable_unit"]), f"usable_quantity has no usable_unit: {pid}", errors)

        if iid in ingredient_map:
            effective_unit = row["usable_unit"] if row["usable_quantity"] else row["pack_unit"]
            require(
                effective_unit == ingredient_map[iid]["preferred_model_unit"],
                f"Retail/model unit mismatch: {pid}/{iid}",
                errors,
            )

        require(
            row["mapping_status"] != "needs_weight_conversion",
            f"Stale unresolved product mapping: {pid}",
            errors,
        )

    for row in conversions:
        require(bool(row["multiplier"]), f"Blank conversion multiplier: {row['conversion_id']}", errors)
        try:
            require(float(row["multiplier"]) > 0, f"Non-positive conversion multiplier: {row['conversion_id']}", errors)
        except ValueError:
            errors.append(f"Non-numeric conversion multiplier: {row['conversion_id']}")

    for row in inventory:
        iid = row["ingredient_id"]
        require(iid in ingredient_ids, f"Unknown ingredient in initial inventory: {iid}", errors)
        if iid in ingredient_map:
            require(
                row["unit"] == ingredient_map[iid]["preferred_model_unit"],
                f"Initial-inventory/model unit mismatch: {iid}",
                errors,
            )

    if errors:
        print("Seed-data validation FAILED")
        for error in errors:
            print(f"- {error}")
        return 1

    print("Seed-data validation PASSED")
    print(f"Recipes: {len(recipes)}")
    print(f"Recipe-ingredient rows: {len(recipe_ingredients)}")
    print(f"Canonical ingredients: {len(ingredients)}")
    print(f"Retail product rows: {len(products)}")
    print(f"Unit conversions: {len(conversions)}")
    print(f"Flexibility classes: {len(flexibility)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
