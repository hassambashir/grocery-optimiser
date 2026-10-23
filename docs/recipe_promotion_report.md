# Recipe promotion report — 23 October 2026

## Outcome

All seven staged batches were promoted into the authoritative recipe catalogue. The active optimiser now contains 200 two-person recipes and 1,777 recipe-ingredient rows. The batch CSV files were removed after promotion; `staging/product_candidates.csv` remains because unresolved product candidates are separate from recipe promotion.

## Promotion gates

| Check | Result |
|---|---:|
| Active recipes | 200 |
| Recipe-ingredient rows | 1,777 |
| Used canonical ingredients | 205 |
| Ingredients with eligible Tesco products | 205 |
| Exact duplicate normalised names | 0 |
| Probable duplicate pairs | 0 |
| Identical ingredient-set groups | 0 |
| Recipes solved individually | 200 |
| Infeasible recipes | 0 |
| Recipes without a source URL | 92 warnings |

The provenance warnings are intentional. Source URLs are useful evidence but are not a substitute for a complete, internally consistent household method. Missing URLs do not block a recipe.

## Corrections discovered during promotion

- Added `rating` to the authoritative recipe schema and made the validator reject nonnumeric or out-of-range ratings.
- Removed stale “draft”, “pending mapping” and “pending reconciliation” labels after the relevant gates passed, while retaining honest “not kitchen-tested” notes.
- Corrected missing units in six older instruction phrases for hoisin, oyster and BBQ sauces.
- Extended kitchen-consumption increments for practical fractions: lettuce by quarters and cucumber, courgette, lemon and red onion by halves. Retail product purchases remain positive whole packs/reference portions.
- Corrected the historical two-week regression test so an immutable saved Week 2 remains auditable without forcing an expanded live catalogue to reproduce its old objective and basket.
- Reduced fully pinned solves to the requested recipes before model construction and enabled CBC to use up to eight available CPU threads.

## Executed results

```text
Seed-data validation PASSED
recipes: 200
used_ingredients: 205
canonical_ingredients: 209
recipe_ingredient_rows: 1777
products: 332
eligible_products: 307
covered_ingredients: 205
missing: []
alternatives: 101
Excluded product rows: 25
```

```text
Recipe catalogue audit PASSED
recipes: 200
ingredient_lines: 1777
unique_ingredients: 205
exact_duplicate_name_groups: 0
probable_duplicate_pairs: 0
identical_ingredient_set_groups: 0
recipes_without_source_url: 92
recipes_solved_individually: 200
infeasible_recipes: 0
```

The full-catalogue seven-dinner solve reached a proven optimum in approximately 32 seconds in the validation environment. It selected R029, R036, R068, R070, R071, R113 and R160. Shopping expenditure was GBP 31.08 and estimated consumed-ingredient value was GBP 18.85. The result used whole retail packs and reconciled all inventory balances.

The complete regression suite passed all 33 tests in 85.175 seconds.

The expanded optimum should not be compared directly with the locked Week 1 result as if it were a price saving: the recipe choice set is different, and the saved Week 1 simulation remains an immutable historical result.

## Distribution observation

The catalogue is substantially broader, but it is not perfectly balanced: chicken has 45 recipes and cheese 43, while tofu has 4, lamb 5 and vegetable-led meals 5. This is not a validation failure because weekly caps still enforce variety when feasible. It is the clearest direction for the next recipe-expansion pass.
