"""Audit the promoted recipe catalogue for duplication, quality and feasibility."""
import argparse
import contextlib
import difflib
import io
import re
from collections import Counter, defaultdict

from catalogue import ROOT, read_csv
from optimise_week import solve
from validate_seed_data import validate as validate_seed
from validate_staging_data import method_quality_issues, provenance_warnings


def normalise_name(value):
    return " ".join(re.findall(r"[a-z0-9]+", value.lower().replace("&", " and ")))


def audit(root=ROOT, solve_all=False):
    errors, warnings = [], []
    seed_errors, _ = validate_seed(root)
    errors.extend(seed_errors)
    recipes = read_csv("data/recipes.csv", root)
    lines = read_csv("data/recipe_ingredients.csv", root)
    ingredients_by_recipe = defaultdict(set)
    for line in lines:
        ingredients_by_recipe[line["recipe_id"]].add(line["ingredient_id"])

    names = defaultdict(list)
    signatures = defaultdict(list)
    for recipe in recipes:
        rid = recipe["recipe_id"]
        names[normalise_name(recipe["recipe_name"])].append(rid)
        signatures[tuple(sorted(ingredients_by_recipe[rid]))].append(rid)
        method_errors, method_warnings = method_quality_issues(recipe)
        errors.extend(method_errors)
        warnings.extend(method_warnings)
        warnings.extend(provenance_warnings(recipe))

    exact_name_groups = [ids for ids in names.values() if len(ids) > 1]
    identical_ingredient_groups = [ids for ids in signatures.values() if len(ids) > 1]
    for ids in exact_name_groups:
        errors.append("duplicate normalised recipe name: " + ", ".join(ids))

    near_duplicates = []
    for index, first in enumerate(recipes):
        first_id = first["recipe_id"]
        first_set = ingredients_by_recipe[first_id]
        for second in recipes[index + 1:]:
            second_id = second["recipe_id"]
            second_set = ingredients_by_recipe[second_id]
            union = first_set | second_set
            overlap = len(first_set & second_set) / len(union) if union else 0
            similarity = difflib.SequenceMatcher(
                None,
                normalise_name(first["recipe_name"]),
                normalise_name(second["recipe_name"]),
            ).ratio()
            if similarity >= 0.86 and overlap >= 0.65:
                near_duplicates.append((first_id, second_id, similarity, overlap))
    for first_id, second_id, similarity, overlap in near_duplicates:
        errors.append(
            f"probable duplicate recipes {first_id}/{second_id}: "
            f"name similarity {similarity:.2f}, ingredient overlap {overlap:.2f}"
        )

    infeasible = []
    if solve_all and not errors:
        for recipe in recipes:
            with contextlib.redirect_stdout(io.StringIO()):
                try:
                    result = solve(days=1, required_recipes=[recipe["recipe_id"]])
                except Exception as exc:  # retain the recipe-specific failure
                    infeasible.append((recipe["recipe_id"], str(exc)))
                    continue
            if [row["recipe_id"] for row in result["recipes"]] != [recipe["recipe_id"]]:
                infeasible.append((recipe["recipe_id"], "solver selected a different recipe"))
        errors.extend(f"{rid}: infeasible ({reason})" for rid, reason in infeasible)

    stats = {
        "recipes": len(recipes),
        "ingredient_lines": len(lines),
        "unique_ingredients": len({line["ingredient_id"] for line in lines}),
        "exact_duplicate_name_groups": len(exact_name_groups),
        "probable_duplicate_pairs": len(near_duplicates),
        "identical_ingredient_set_groups": len(identical_ingredient_groups),
        "recipes_without_source_url": sum(not recipe.get("inspiration_url", "").strip() for recipe in recipes),
        "recipes_solved_individually": len(recipes) if solve_all else 0,
        "infeasible_recipes": len(infeasible),
        "protein_distribution": dict(sorted(Counter(recipe["main_protein"] for recipe in recipes).items())),
    }
    return errors, warnings, stats


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--solve-all", action="store_true")
    args = parser.parse_args()
    errors, warnings, stats = audit(solve_all=args.solve_all)
    print("Recipe catalogue audit " + ("FAILED" if errors else "PASSED"))
    for key, value in stats.items():
        print(f"{key}: {value}")
    print(f"warnings: {len(warnings)}")
    for error in errors:
        print("- " + error)
    return bool(errors)


if __name__ == "__main__":
    raise SystemExit(main())
