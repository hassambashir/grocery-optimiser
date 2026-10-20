"""Validate the model-ready seed dataset.

Uses only the Python standard library. Run from the repository root:

    python scripts/validate_seed_data.py
"""

from __future__ import annotations

import csv
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def read_csv(relative_path: str) -> list[dict[str, str]]:
    with (ROOT / relative_path).open(newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def require(condition: bool, message: str, errors: list[str]) -> None:
    if not condition:
        errors.append(message)


def main() -> int:
    recipes = read_csv("data/recipes.csv")
    recipe_ingredients = read_csv("data/recipe_ingredients.csv")
    ingredients = read_csv("data/ingredients.csv")
    products = read_csv("data/products.csv")
    conversions = read_csv("data/unit_conversions.csv")
    flexibility = read_csv("data/flexibility_classes.csv")
    inventory = read_csv("config/initial_inventory.csv")

    errors: list[str] = []

    recipe_ids = {r["recipe_id"] for r in recipes}
    ingredient_ids = {r["ingredient_id"] for r in ingredients}
    product_ingredient_ids = {r["ingredient_id"] for r in products}
    staple_ids = {
        r["ingredient_id"]
        for r in ingredients
        if r["inventory_policy"] == "assumed_on_hand_staple"
    }
    flex_classes = {r["flexibility_class"] for r in flexibility}

    # Recipe integrity.
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

    # Every used ingredient must be obtainable or deliberately assumed on hand.
    used_ids = {r["ingredient_id"] for r in recipe_ingredients}
    for iid in sorted(used_ids):
        require(
            iid in product_ingredient_ids or iid in staple_ids,
            f"No retail supply or assumed-on-hand policy for: {iid}",
            errors,
        )

    # Flexibility classes must resolve.
    for row in ingredients:
        fc = row["default_flexibility_class"]
        require(bool(fc), f"Missing default flexibility class: {row['ingredient_id']}", errors)
        require(fc in flex_classes, f"Unknown flexibility class {fc}: {row['ingredient_id']}", errors)

    # Product rows must be numerically usable.
    for row in products:
        pid = row["product_id"]
        require(row["ingredient_id"] in ingredient_ids, f"Unknown ingredient on product {pid}", errors)
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

    # All declared conversion rows in the seed dataset must have a multiplier.
    for row in conversions:
        require(bool(row["multiplier"]), f"Blank conversion multiplier: {row['conversion_id']}", errors)
        try:
            require(float(row["multiplier"]) > 0, f"Non-positive conversion multiplier: {row['conversion_id']}", errors)
        except ValueError:
            errors.append(f"Non-numeric conversion multiplier: {row['conversion_id']}")

    # Starting inventory must reference known ingredients.
    for row in inventory:
        require(
            row["ingredient_id"] in ingredient_ids,
            f"Unknown ingredient in initial inventory: {row['ingredient_id']}",
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
