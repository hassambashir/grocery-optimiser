# Tesco allergen catalogue report — 24 October 2026

## Scope and result

The catalogue stores one status for every combination of 355 Tesco products and the 14 UK regulated allergen groups: 4,970 classifications. All 355 product pages were assessed. Evidence was extracted from the Tesco ingredient list, allergy information, dietary information and product claims and retained in `data/product_allergen_evidence.csv` with the checked date, source URL and content hash.

The four allowed statuses are:

- `contains`: the ingredient list declares the allergen;
- `may_contain`: Tesco displays a precautionary warning;
- `free`: Tesco makes an explicit free-from claim, or a complete online ingredient/allergy label has no declaration;
- `unknown`: the page is incomplete or could not be fetched.

`free` describes the checked Tesco online label, not an independent medical certification. Tesco states that formulations and allergen information can change. An application must fail closed for household exclusions: `unknown` must not be treated as `free`, and the physical pack must be checked.

## Gluten-free catalogue expansion

Twenty-three eligible gluten-free Tesco listings now provide 21 direct canonical ingredient mappings. Sixteen products were added in the first pass and seven more after targeted gap searches. They cover pasta, spaghetti, orzo, lasagne sheets, gnocchi, tortillas, flatbreads, pittas, plain flour, breadcrumbs, puff pastry, soy sauce/tamari, sausages, burger buns/rolls, naan, hoisin sauce, black-bean sauce, teriyaki sauce, falafel, ciabatta and vinegar.

The catalogue preserves labelled gross units. Three stir-fry pouches are sold in grams while their canonical recipes use millilitres; those rows retain the project's disclosed approximate sauce conversion and are flagged `quantity_adjustment_required=yes`. Dried pasta, gnocchi, bread, pastry, naan, falafel and sausage alternatives are flagged where the cook should follow pack-specific heating, handling or cooking instructions.

## Unresolved direct gluten-free mappings

Existing recipes use 27 ingredient identities for which at least one currently catalogued product declares cereals containing gluten. Twenty of those identities now have an eligible verified direct gluten-free product; `sausages` was also covered proactively. These seven direct gaps remain:

| Recipe ingredient | Reason not activated as a direct mapping |
|---|---|
| `couscous` | Gluten-free orzo/rice is a culinary substitution, not couscous, and changes cooking instructions. |
| `crispy_onions` | Current Tesco crispy-onion listings found use wheat or have precautionary gluten warnings. |
| `egg_noodles` | Rice noodles are gluten-free but are not egg noodles and require different cooking instructions. |
| `giant_couscous` | Gluten-free orzo is a possible recipe adaptation, not a direct product match. |
| `oyster_sauce` | Verified gluten-free Tesco listings were out of stock at the checked date, so they are not optimiser-eligible. |
| `udon_noodles` | Rice noodles are a possible adaptation, not a direct udon product and cook differently. |
| `wholewheat_noodles` | A gluten-free product cannot be wholewheat; changing to rice noodles is a recipe substitution. |

These are documented gaps rather than false mappings. Cross-ingredient recipe substitutions need a separate substitution model so that product identity stays truthful and altered quantities/instructions remain visible.

## Remaining evidence uncertainty

Four historic Tesco URLs returned HTTP 404 after repeated attempts: P270, P271, P272 and P273. Their 56 allergen cells remain `unknown`. Other products can still have individual `unknown` cells when Tesco supplies only an ingredient list or omits both ingredients and allergy information. This is deliberate: absence from an incomplete webpage is not evidence of being allergen-free.

## Validation commands

Executed validation result:

```text
Seed-data validation PASSED
recipes: 200
used_ingredients: 205
canonical_ingredients: 209
recipe_ingredient_rows: 1777
products: 355
eligible_products: 330
covered_ingredients: 205
missing: []
alternatives: 124
allergen_assessed_products: 355
allergen_classifications: 4970
fully_classified_products: 118
products_with_unknown_allergens: 237
allergen_fetch_failures: 4
gluten_free_alternatives: 23
gluten_free_ingredient_mappings: 21
Excluded product rows: 25
```

Additional executed checks:

```text
40 tests passed in 105.590s
Recipe catalogue audit PASSED
recipes_solved_individually: 200
infeasible_recipes: 0
Seven-day optimiser: 7 distinct dinners, GBP 31.08 shopping cost,
GBP 18.85 estimated consumed value, valid whole-pack basket
```

Commands used:

```text
python scripts/validate_seed_data.py
python -m unittest discover -s tests -v
python scripts/audit_recipe_catalogue.py --solve-all
python scripts/optimise_week.py --days 7
```

The allergen refresh command is:

```text
python scripts/fetch_tesco_allergens.py --workers 6 --checked-at YYYY-MM-DD
```

It performs live requests, so transient network failures must be reviewed rather than reclassified as absence of allergens.
