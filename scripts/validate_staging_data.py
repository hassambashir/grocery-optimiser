"""Validate every staged recipe batch before promotion into the active dataset."""
import csv
import glob
import re
from collections import Counter, defaultdict
from pathlib import Path

from catalogue import (ROOT, INTENTIONAL_RETAIL_COMPOSITES, MAIN_PROTEINS,
                       PRIMARY_SIDES, exclusion_reason,
                       looks_like_composite_ingredient, positive, read_csv)


HELLOFRESH_RECIPE = re.compile(r"https://www\.hellofresh\.co\.uk/recipes/.+-[0-9a-f]{24}/?$")
PREPARED_COMPONENT_REFERENCE = re.compile(
    r"\byour\s+(?:[a-z]+\s+){0,2}(?:mayo|mayonnaise|yoghurt|yogurt|dressing|salsa|sauce)\b",
    re.I,
)


def method_quality_issues(recipe):
    """Return objective failures and review prompts for a household method.

    Vessel minimisation is partly culinary judgement, so only clearly
    unhelpful source-style fragments fail automatically.  Possible extra-bowl
    language is surfaced for review rather than rejected blindly.
    """
    rid = recipe["recipe_id"]
    method = recipe.get("cooking_instructions", "").strip()
    errors, warnings = [], []
    if not method:
        errors.append(f"{rid}: missing cooking instructions")
        return errors, warnings
    if len(method.split()) < 35:
        errors.append(f"{rid}: cooking instructions are too abbreviated")
    if PREPARED_COMPONENT_REFERENCE.search(method):
        errors.append(
            f"{rid}: method uses an unexplained source-style prepared-component label"
        )
    if re.search(r"\b(?:separate|small) bowl\b|\bin a bowl\b", method, re.I):
        warnings.append(
            f"{rid}: review whether the named bowl is genuinely needed or the ingredients can be assembled directly"
        )
    return errors, warnings


def provenance_warnings(recipe):
    """A source link is useful provenance, but is not a recipe-quality gate."""
    rid = recipe["recipe_id"]
    url = recipe.get("inspiration_url", "").strip()
    if not url:
        return [f"{rid}: no inspiration URL; method must stand on its own"]
    if "hellofresh.co.uk" in url and not HELLOFRESH_RECIPE.fullmatch(url):
        return [f"{rid}: inspiration URL is a generic HelloFresh path, not a verified recipe page"]
    return []


def validate(root=ROOT):
    errors, warnings = [], []
    recipe_files = sorted(Path(root, "staging").glob("recipes_batch_*.csv"))
    line_files = sorted(Path(root, "staging").glob("recipe_ingredients_batch_*.csv"))
    ingredient_files = sorted(Path(root, "staging").glob("ingredients_batch_*.csv"))
    if not recipe_files or len(recipe_files) != len(line_files) or len(recipe_files) != len(ingredient_files):
        return ["Staging batch file sets are incomplete"], [], {}

    active_recipes = read_csv("data/recipes.csv", root)
    active_ingredients = read_csv("data/ingredients.csv", root)
    products = read_csv("data/products.csv", root)
    recipes, lines, staged_definitions = [], [], []
    for path in recipe_files:
        recipes.extend(read_csv(path.relative_to(root), root))
    for path in line_files:
        lines.extend(read_csv(path.relative_to(root), root))
    for path in ingredient_files:
        staged_definitions.extend(read_csv(path.relative_to(root), root))

    def unique(rows, key, label):
        values = [row.get(key, "") for row in rows]
        if any(not value for value in values):
            errors.append(f"{label}: blank {key}")
        for value, count in Counter(values).items():
            if value and count > 1:
                errors.append(f"{label}: duplicate {key} {value}")

    unique(recipes, "recipe_id", "staged recipes")
    unique(staged_definitions, "ingredient_id", "staged ingredient definitions")
    active_recipe_ids = {row["recipe_id"] for row in active_recipes}
    for row in recipes:
        if row["recipe_id"] in active_recipe_ids:
            errors.append(f"{row['recipe_id']}: already exists in active recipes")

    definitions = {row["ingredient_id"]: row for row in active_ingredients}
    for row in staged_definitions:
        existing = definitions.get(row["ingredient_id"])
        if existing and any(existing.get(key) != row.get(key) for key in row):
            errors.append(f"{row['ingredient_id']}: staged definition conflicts with active definition")
        definitions[row["ingredient_id"]] = row
    for iid, row in definitions.items():
        if looks_like_composite_ingredient(row) and iid not in INTENTIONAL_RETAIL_COMPOSITES:
            errors.append(f"{iid}: unapproved composite canonical ingredient")
    if "fresh_herb_mix_coriander_mint" in definitions:
        errors.append("fresh_herb_mix_coriander_mint: removed composite ingredient has returned")

    recipe_map = {row["recipe_id"]: row for row in recipes}
    line_pairs = Counter((row["recipe_id"], row["ingredient_id"]) for row in lines)
    for pair, count in line_pairs.items():
        if count > 1:
            errors.append(f"duplicate staged recipe ingredient {pair}")
    for row in lines:
        rid, iid = row["recipe_id"], row["ingredient_id"]
        if rid not in recipe_map:
            errors.append(f"{rid}/{iid}: unknown staged recipe")
        if iid not in definitions:
            errors.append(f"{rid}/{iid}: unknown canonical ingredient")
        elif row["unit"] != definitions[iid]["preferred_model_unit"]:
            errors.append(f"{rid}/{iid}: {row['unit']} does not match canonical {definitions[iid]['preferred_model_unit']}")
        if not positive(row["preferred_quantity"]):
            errors.append(f"{rid}/{iid}: invalid preferred quantity")

    for row in recipes:
        rid = row["recipe_id"]
        if row["servings"] != "2":
            errors.append(f"{rid}: expected two servings")
        if row["main_protein"] not in MAIN_PROTEINS:
            errors.append(f"{rid}: non-standard main protein {row['main_protein']}")
        if row["primary_side"] not in PRIMARY_SIDES:
            errors.append(f"{rid}: non-standard primary side {row['primary_side']}")
        method_errors, method_warnings = method_quality_issues(row)
        errors.extend(method_errors)
        warnings.extend(method_warnings)
        warnings.extend(provenance_warnings(row))
        rating = row.get("rating", "").strip()
        if rating:
            try:
                if not 0 <= float(rating) <= 5:
                    raise ValueError
            except ValueError:
                errors.append(f"{rid}: rating must be blank or numeric from 0 to 5")
        if not any(line["recipe_id"] == rid for line in lines):
            errors.append(f"{rid}: no ingredient lines")

    for row in staged_definitions:
        if row["shelf_life_class"] == "short" and row["inventory_policy"] != "fresh_tracked":
            errors.append(f"{row['ingredient_id']}: short-life ingredient must be fresh_tracked")

    eligible = defaultdict(list)
    for product in products:
        if not exclusion_reason(product, definitions):
            eligible[product["ingredient_id"]].append(product)
    used = {row["ingredient_id"] for row in lines}
    missing_products = sorted(used - set(eligible))
    for iid in missing_products:
        errors.append(f"{iid}: no eligible Tesco product for staged recipes")

    stats = {
        "batches": len(recipe_files),
        "recipes": len(recipes),
        "ingredient_lines": len(lines),
        "used_ingredients": len(used),
        "canonical_ingredients": len(definitions),
        "ingredients_with_eligible_products": len(used & set(eligible)),
        "missing_product_ingredients": missing_products,
        "instruction_errors": sum(
            "instructions" in error or "prepared-component" in error
            for error in errors
        ),
        "provenance_warnings": sum("inspiration URL" in warning for warning in warnings),
    }
    return errors, warnings, stats


def main():
    errors, warnings, stats = validate()
    print("Staging validation " + ("FAILED" if errors else "PASSED"))
    for key, value in stats.items():
        print(f"{key}: {value}")
    if stats.get("provenance_warnings"):
        print(
            f"WARNING: {stats['provenance_warnings']} recipes have no specific inspiration URL; "
            "provenance is optional"
        )
    for warning in warnings:
        if "inspiration URL" not in warning:
            print("WARNING: " + warning)
    for error in errors:
        print("- " + error)
    return bool(errors)


if __name__ == "__main__":
    raise SystemExit(main())
