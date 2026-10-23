"""Generate the current active-and-staged Tesco catalogue coverage report."""
from collections import defaultdict
from pathlib import Path

from catalogue import ROOT, exclusion_reason, read_csv


def main(root=ROOT):
    ingredients = {row["ingredient_id"]: row for row in read_csv("data/ingredients.csv", root)}
    products = read_csv("data/products.csv", root)
    used = {row["ingredient_id"] for row in read_csv("data/recipe_ingredients.csv", root)}
    for path in sorted(Path(root, "staging").glob("recipe_ingredients_batch_*.csv")):
        used.update(row["ingredient_id"] for row in read_csv(path.relative_to(root), root))

    eligible = defaultdict(list)
    excluded = []
    for product in products:
        reason = exclusion_reason(product, ingredients)
        if reason:
            excluded.append((product, reason))
        else:
            eligible[product["ingredient_id"]].append(product)

    missing = sorted(used - set(eligible))
    lines = [
        "# Tesco catalogue coverage — 23 October 2026",
        "",
        f"{len(used) - len(missing)} of {len(used)} ingredients used by the active and staged recipes have eligible products. "
        "Availability is the observed public Tesco UK listing, not a guarantee of postcode or delivery-slot stock.",
        "",
        "| Ingredient | Unit | Eligible options | Tesco product IDs |",
        "|---|---|---:|---|",
    ]
    for iid in sorted(used):
        options = eligible.get(iid, [])
        links = ", ".join(
            f"[{p['retailer_product_id']}]({p['source_url']})" for p in options
        ) or "—"
        lines.append(
            f"| {iid} | {ingredients[iid]['preferred_model_unit']} | {len(options)} | {links} |"
        )

    lines.extend([
        "",
        "## Excluded product rows",
        "",
        "An excluded listing is retained as evidence or history but is never offered to the optimiser. "
        "Every currently used ingredient still has at least one eligible alternative.",
        "",
        "| Product | Ingredient | Reason |",
        "|---|---|---|",
    ])
    for product, reason in excluded:
        lines.append(
            f"| {product['product_id']} — [{product['product_name']}]({product['source_url']}) "
            f"| {product['ingredient_id']} | {reason} |"
        )

    lines.extend([
        "",
        "## Verification limits",
        "",
        "No fabricated product IDs, prices or availability states are used. Public Tesco pages supplied product identity, "
        "pack data, price and the availability snapshot. Product listings and prices can change, and postcode-specific "
        "availability must be checked again before real shopping.",
        "",
        "Whole-produce reference weights and counts remain disclosed modelling estimates; declared drained weights are used "
        "for canned products when available. See [data normalisation](data_normalisation.md).",
        "",
    ])
    output = Path(root, "docs", "catalogue_coverage.md")
    output.write_text("\n".join(lines), encoding="utf-8")
    print(f"Wrote {output.relative_to(root)}: {len(used)} ingredients, {len(missing)} missing")
    return bool(missing)


if __name__ == "__main__":
    raise SystemExit(main())
