# Staged recipe data validation

Revalidated on 23 October 2026 after applying the controlled recipe classifications.

## Decision

The staged data is structurally consistent but is **not ready for wholesale promotion** into the active optimiser dataset. Recipe IDs, ingredient references, canonical units, quantities, serving counts, instruction-length checks and inventory flags pass. Tesco purchasing coverage remains incomplete. Missing inspiration links are reported as provenance warnings rather than promotion blockers.

| Batch | Recipes | Ingredient lines | Specific source URLs | Short instructions | Ingredients without an eligible Tesco product | Status |
|---|---:|---:|---:|---:|---:|---|
| 01 | 20 | 171 | 20 | 0 | 3 | Hold for product coverage |
| 02 | 20 | 121 | 1 | 0 | 3 | Hold for product coverage |
| 03 | 20 | 130 | 6 | 0 | 1 | Hold for product coverage |
| 04 | 20 | 148 | 3 | 0 | 1 | Hold for product coverage |
| 05 | 20 | 154 | 0 | 0 | 6 | Hold for product coverage |
| 06 | 20 | 204 | 20 | 0 | 4 | Hold for product coverage |
| 07 | 40 | 476 | 40 | 0 | 2 | Hold for product coverage |

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

## Remaining blockers

### Instruction quality and provenance

- All 160 staged recipes now pass the objective instruction checks: a nonempty method of at least 35 words and no unexplained meal-kit label such as “your garlic mayo”.
- Batch 2's 20 placeholder methods were replaced with complete two-person methods using the structured ingredient lists. They give sequence, timings and doneness guidance and deliberately reuse pans or trays where practical.
- Nineteen generic Batch 2 HelloFresh paths were cleared rather than retained as if they were verified recipe pages. Those methods are declared AI-simplified and not kitchen-tested.
- Seventy recipes now have no inspiration URL. This is a visible provenance warning, not a failure: the method must be internally complete and honestly labelled whether or not a publisher link exists.
- R042, R055, R058 and R153 were simplified to remove unnecessary sauce or dressing vessels. Ingredients are combined directly on the food, in the cooking pan or in the potato saucepan already in use.

Specific links are still retained when already verified: 20 in Batch 1, 1 in Batch 2, 6 in Batch 3, 3 in Batch 4, 20 in Batch 6 and 40 in Batch 7. A link is provenance only; full culinary suitability and ingredient-to-method alignment remain review questions.

### Tesco purchasing coverage

The staged recipes use 200 unique ingredients. Of these, 186 currently have at least one eligible Tesco product under the optimiser's exact unit and mapping rules. The 14 without an eligible product are:

`baby_corn`, `butternut_squash`, `cannelloni_tubes`, `dried_apricots`, `dried_thyme`, `fennel_seeds`, `giant_couscous`, `green_chilli`, `instant_polenta`, `ketjap_manis`, `mixed_beans`, `pumpkin_seeds`, `tamarind_paste`, `zaatar`.

The whole butternut squash row is retained as a compatibility candidate because Tesco sells it by count while the recipes use grams. It must not become optimiser-eligible until a defensible usable gram quantity is recorded.

### Classification fields

The classification fields now use controlled vocabularies across the active and staged recipes. Fish such as salmon, cod and tuna use `fish`; prawns use `shrimp`; and the vague `seafood` value has been removed. Recipes without a distinct protein use `vegetable` rather than mixing dietary labels such as `vegetarian` with ingredient families.

Primary-side synonyms have also been consolidated. Examples include `potato` rather than `potatoes`, `tortilla` rather than `tortillas`, `rice` for brown-rice variants, `pasta` for spaghetti/orzo/gnocchi, and `bread` for pitta, naan and other flatbreads. Meaningfully different sides such as ordinary potato and sweet potato remain separate.

## Corrections made in this pass

- Repaired the malformed quoting in product `P232`, preserving the explicit statement that 40 cloves is an estimate rather than a Tesco-declared weight.
- Added `clove` to the validator's supported units.
- Promoted 77 non-conflicting canonical ingredient definitions so product mappings for staged recipes retain referential integrity.
- Changed `P278` whole butternut squash from `direct` to `compatible_candidate`; it cannot directly satisfy gram demand without a verified usable weight.
- Cleared nonnumeric prose from the rating fields for R082 and R085 and retained the verification note in `ingredient_notes`.
- Added `scripts/validate_staging_data.py` so future staged batches are checked consistently before promotion.
- Standardised `main_protein` and `primary_side` across all 200 active and staged recipes, and made both validators reject labels outside the controlled vocabularies.
- Reclassified missing or generic recipe links as warnings rather than failures, because a URL does not establish method quality.
- Replaced all 20 abbreviated Batch 2 methods and added regression tests for complete staged methods, optional provenance and direct assembly of simple finishing sauces.
- Corrected the locked two-week regression so historical run artifacts remain immutable without requiring the evolving live catalogue to equal its old snapshot rows.

## Validation commands

```text
python scripts/validate_seed_data.py
Seed-data validation PASSED
recipes: 40
used_ingredients: 125
canonical_ingredients: 209
recipe_ingredient_rows: 373
products: 316
eligible_products: 288
covered_ingredients: 125
missing: []
alternatives: 94
Excluded product rows: 28
```

```text
python scripts/validate_staging_data.py
Staging validation FAILED
batches: 7
recipes: 160
ingredient_lines: 1404
used_ingredients: 200
canonical_ingredients: 209
ingredients_with_eligible_products: 186
missing_product_ingredients: ['baby_corn', 'butternut_squash', 'cannelloni_tubes', 'dried_apricots', 'dried_thyme', 'fennel_seeds', 'giant_couscous', 'green_chilli', 'instant_polenta', 'ketjap_manis', 'mixed_beans', 'pumpkin_seeds', 'tamarind_paste', 'zaatar']
instruction_errors: 0
provenance_warnings: 70
```

The staging failure is now caused only by the 14 ingredients without eligible Tesco products. Provenance notices are warnings and do not make the validation fail. Promotion should occur after purchasing coverage is completed or the affected recipes are explicitly excluded.
