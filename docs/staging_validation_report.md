# Staged recipe data validation — pre-promotion record

> All 160 recipes covered by this report were promoted into the active catalogue on 23 October 2026. The counts below preserve the final pre-promotion audit; current authoritative totals are in `data/recipes.csv`, `data/recipe_ingredients.csv` and `docs/recipe_promotion_report.md`.

Revalidated on 23 October 2026 after applying the controlled recipe classifications.

## Decision

The staged data is structurally consistent and all Tesco purchasing-coverage gates now pass. Recipe IDs, ingredient references, canonical units, quantities, serving counts, instruction checks and inventory flags pass. Missing inspiration links remain visible provenance warnings rather than promotion blockers. Promotion can therefore proceed in reviewed batches; culinary review and deduplication are still sensible before merging all 160 recipes into the active set.

| Batch | Recipes | Ingredient lines | Specific source URLs | Short instructions | Ingredients without an eligible Tesco product | Status |
|---|---:|---:|---:|---:|---:|---|
| 01 | 20 | 171 | 20 | 0 | 0 | Catalogue-ready; recipe review remains |
| 02 | 20 | 121 | 1 | 0 | 0 | Catalogue-ready; recipe review remains |
| 03 | 20 | 130 | 6 | 0 | 0 | Catalogue-ready; recipe review remains |
| 04 | 20 | 148 | 3 | 0 | 0 | Catalogue-ready; recipe review remains |
| 05 | 20 | 154 | 0 | 0 | 0 | Catalogue-ready; recipe review remains |
| 06 | 20 | 204 | 20 | 0 | 0 | Catalogue-ready; recipe review remains |
| 07 | 40 | 476 | 40 | 0 | 0 | Catalogue-ready; recipe review remains |

“Specific source URL” means the field points to a particular publisher recipe rather than being blank or resolving to a generic recipe landing page. It does not by itself prove that every adapted quantity and instruction matches the publisher's version.

## Checks that pass

- 160 unique staged recipe IDs and 1,404 ingredient lines.
- All recipes specify two servings and have cooking instructions.
- No duplicate recipe/ingredient pairs.
- No missing recipe or canonical ingredient references.
- All quantities are numeric and positive.
- Every ingredient line uses its canonical model unit.
- Spring onions are measured in grams; instructions give approximate whole-spring-onion counts.
- No duplicate staged ingredient IDs or conflicting definitions.
- No unapproved composite canonical ingredients; coriander and mint are separate recipe and product mappings.
- Short-life staged ingredients use `fresh_tracked` inventory policy.
- No exact duplicate recipe names were detected.
- Product IDs and Tesco retailer IDs are unique after repairing the malformed `P232` CSV row.

## Remaining review work

### Instruction quality and provenance

- All 160 staged recipes now pass the objective instruction checks: a nonempty method of at least 35 words and no unexplained meal-kit label such as “your garlic mayo”.
- Batch 2's 20 placeholder methods were replaced with complete two-person methods using the structured ingredient lists. They give sequence, timings and doneness guidance and deliberately reuse pans or trays where practical.
- Nineteen generic Batch 2 HelloFresh paths were cleared rather than retained as if they were verified recipe pages. Those methods are declared AI-simplified and not kitchen-tested.
- Seventy recipes now have no inspiration URL. This is a visible provenance warning, not a failure: the method must be internally complete and honestly labelled whether or not a publisher link exists.
- R042, R055, R058 and R153 were simplified to remove unnecessary sauce or dressing vessels. Ingredients are combined directly on the food, in the cooking pan or in the potato saucepan already in use.

Specific links are still retained when already verified: 20 in Batch 1, 1 in Batch 2, 6 in Batch 3, 3 in Batch 4, 20 in Batch 6 and 40 in Batch 7. A link is provenance only; full culinary suitability and ingredient-to-method alignment remain review questions.

### Tesco purchasing coverage

The staged recipes now use 198 unique ingredients, and all 198 have at least one eligible Tesco product under the optimiser's identity, availability, quantity and unit rules. Eighteen verified current listings were added for 11 previously uncovered ingredients, including multiple pack or brand choices for butternut squash, thyme, fennel seeds, mixed beans, pumpkin seeds and tamarind paste.

Three unavailable product forms were corrected at recipe level rather than inventing stock. The cannelloni recipe is now a lasagne-roll recipe using eligible lasagne sheets; ketjap manis is replaced in two recipes by separately measured soy sauce and brown sugar; and instant polenta is standardised as non-instant `polenta_cornmeal`, matching Tesco's available fine cornmeal. Green chilli is standardised to grams across recipe, ingredient and product data.

Tesco's fresh-vegetable category showed baby corn available to add at the recorded price while its detail result presented conflicting availability. The row follows the current category snapshot, but postcode-specific stock must be checked at shopping time.

| Original gap | Resolution used by staged recipes |
|---|---|
| `baby_corn` | Existing P253 reverified as currently listed |
| `butternut_squash` | P319 frozen chunks and P320 fresh diced |
| `cannelloni_tubes` | Recipe adapted to lasagne rolls using eligible P268 sheets |
| `dried_apricots` | P321 Tesco Soft Apricots |
| `dried_thyme` | P322 Tesco and P323 Schwartz thyme |
| `fennel_seeds` | P324 Tesco plus P325/P326 East End packs |
| `giant_couscous` | P327 Osem Israeli pearl couscous |
| `green_chilli` | P328 Tesco Finger Chillies, measured in grams |
| `instant_polenta` | Standardised to `polenta_cornmeal`; P329 Natco Fine Corn Meal |
| `ketjap_manis` | Two recipes use P080 soy sauce plus eligible brown sugar instead of an unavailable bottle |
| `mixed_beans` | P330 Tesco drained three-bean can and P331 Merchant Gourmet pouch |
| `pumpkin_seeds` | P332 Tesco and P333 Tesco Organic |
| `tamarind_paste` | P334 Niru and P335 Thai Taste |
| `zaatar` | P336 Schwartz Za'atar |

### Classification fields

The classification fields now use controlled vocabularies across the active and staged recipes. Fish such as salmon, cod and tuna use `fish`; prawns use `shrimp`; and the vague `seafood` value has been removed. Recipes without a distinct protein use `vegetable` rather than mixing dietary labels such as `vegetarian` with ingredient families.

Primary-side synonyms have also been consolidated. Examples include `potato` rather than `potatoes`, `tortilla` rather than `tortillas`, `rice` for brown-rice variants, `pasta` for spaghetti/orzo/gnocchi, and `bread` for pitta, naan and other flatbreads. Meaningfully different sides such as ordinary potato and sweet potato remain separate.

## Corrections made in this pass

- Repaired the malformed quoting in product `P232`, preserving the explicit statement that 40 cloves is an estimate rather than a Tesco-declared weight.
- Added `clove` to the validator's supported units.
- Promoted 77 non-conflicting canonical ingredient definitions so product mappings for staged recipes retain referential integrity.
- Moved `P278` whole butternut squash out of the active catalogue; it cannot satisfy gram demand without a verified usable weight.
- Cleared nonnumeric prose from the rating fields for R082 and R085 and retained the verification note in `ingredient_notes`.
- Added `scripts/validate_staging_data.py` so future staged batches are checked consistently before promotion.
- Standardised `main_protein` and `primary_side` across all 200 active and staged recipes, and made both validators reject labels outside the controlled vocabularies.
- Reclassified missing or generic recipe links as warnings rather than failures, because a URL does not establish method quality.
- Replaced all 20 abbreviated Batch 2 methods and added regression tests for complete staged methods, optional provenance and direct assembly of simple finishing sauces.
- Corrected the locked two-week regression so historical run artifacts remain immutable without requiring the evolving live catalogue to equal its old snapshot rows.
- Removed the redundant `mapping_status` and `package_type` columns. Eligibility now follows directly from canonical ingredient identity, effective quantity/unit, verified Tesco identity, availability and price; unresolved P071 and P278 rows are isolated in `staging/product_candidates.csv`.
- Added 18 verified Tesco listings covering 11 ingredient families, using the declared 246 g drained weight for Tesco Three Bean Salad.
- Adapted three recipes where Tesco has no current cannelloni, ketjap manis or instant-polenta listing, preserving the meal concepts without fabricating products.
- Added a regression test that requires every staged ingredient to retain an eligible purchasing option and a generated active-and-staged catalogue coverage report.

## Validation commands

```text
python scripts/validate_seed_data.py
Seed-data validation PASSED
recipes: 40
used_ingredients: 125
canonical_ingredients: 209
recipe_ingredient_rows: 373
products: 332
eligible_products: 307
covered_ingredients: 125
missing: []
alternatives: 94
Excluded product rows: 25
```

```text
python scripts/validate_staging_data.py
Staging validation PASSED
batches: 7
recipes: 160
ingredient_lines: 1404
used_ingredients: 198
canonical_ingredients: 209
ingredients_with_eligible_products: 198
missing_product_ingredients: []
instruction_errors: 0
provenance_warnings: 70
```

Both data validators pass. Provenance notices remain warnings and do not make validation fail.
