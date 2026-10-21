#!/usr/bin/env python3
"""Audit household recipe ingredient coverage against canonical ingredients and Tesco products.

Keeps draft recipes out of the optimiser until every ingredient has a verified
quantity/unit mapping and an available retail product. Does not invent prices.
"""
import csv
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
def rows(path):
    with (ROOT / path).open(encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f))

ALIASES = {
    "chicken breast":"chicken_breast", "chicken thighs":"chicken_thigh",
    "chicken thigh":"chicken_thigh", "red pepper":"red_pepper",
    "pepper":"red_pepper", "peppers":"red_pepper", "onion":"brown_onion",
    "red onion":"red_onion", "garlic cloves":"garlic", "garlic clove":"garlic",
    "ginger":"fresh_ginger", "spinach":"spinach", "sweet potatoes":"sweet_potato",
    "sweet potato":"sweet_potato", "cherry tomatoes":"cherry_tomatoes",
    "carrot":"carrot", "carrots":"carrot", "courgette":"courgette",
    "green beans":"green_beans", "mangetout":"mangetout",
    "natural yoghurt":"natural_yogurt", "yoghurt":"natural_yogurt",
    "soy sauce":"soy_sauce", "hoisin":"hoisin_sauce",
    "hoisin sauce":"hoisin_sauce", "sesame oil":"sesame_oil",
    "smoked paprika":"smoked_paprika", "paprika":"smoked_paprika",
    "garam masala":"garam_masala", "turmeric":"turmeric",
    "oregano":"dried_oregano", "couscous":"couscous",
    "cornflour":"cornflour", "rice vinegar":"rice_vinegar",
    "tomato puree":"tomato_puree", "soft cheese":"soft_cheese",
    "mayonnaise":"mayonnaise", "sweetcorn":"sweetcorn",
    "chilli":"red_chilli", "coriander":"fresh_coriander",
    "parsley":"parsley", "brown rice":"brown_rice",
    "arborio rice":"arborio_rice", "long grain rice":"long_grain_rice",
    "stock":"chicken_stock_mix", "chicken stock":"chicken_stock_mix",
    "beef stock":"beef_stock_mix", "flaked almonds":"flaked_almonds",
    "harissa paste":"harissa_paste",
}
# This is a coverage audit, not an automated cooking-unit converter.
def main():
    known = {x["ingredient_id"] for x in rows("data/ingredients.csv")}
    supplied = {x["ingredient_id"] for x in rows("data/products.csv")
                if x["regular_price_gbp"] and x["availability_status"] != "out_of_stock"
                and x["mapping_status"] != "substitution_candidate"}
    output = []
    for recipe in rows("data/household_recipe_library.csv"):
        for token in recipe["ingredient_list_two_servings"].split(";"):
            token = token.strip()
            match = re.match(r"^(?:\\d+(?:\\.\\d+)?\\s*(?:g|kg|ml|l|tsp|tbsp|tin|tins|cloves?|stalks?)?\\s*)?(.*)$", token, re.I)
            name = (match.group(1) if match else token).strip().lower()
            # Exact aliases only: never silently collapse basmati/jasmine into long-grain.
            iid = ALIASES.get(name, "")
            status = ("needs_canonical_ingredient" if not iid or iid not in known
                      else "needs_tesco_product" if iid not in supplied
                      else "needs_quantity_unit_review")
            output.append({"recipe_id":recipe["recipe_id"],"recipe_name":recipe["recipe_name"],
                           "source_ingredient":token,"canonical_ingredient_id":iid,
                           "mapping_status":status})
    out = ROOT / "data/household_ingredient_mapping_audit.csv"
    with out.open("w", newline="", encoding="utf-8") as f:
        w=csv.DictWriter(f, fieldnames=list(output[0]));w.writeheader();w.writerows(output)
    from collections import Counter
    print("Household recipe mapping audit:",len(rows("data/household_recipe_library.csv")),"recipes,",len(output),"ingredient lines")
    print(dict(Counter(x["mapping_status"] for x in output)))
    print("No draft recipe was activated. Review quantity, units and retail mappings first.")
if __name__ == "__main__":
    main()
