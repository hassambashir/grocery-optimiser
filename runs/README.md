# Locked Week 1 and executed Week 2 — 21 October 2026

These are simulated purchases and consumption, not actual household transactions. Week 1 preserves the original result from commit `11f26beb71e85705149ec59ea40b2626705bdde6`; it was not regenerated. Its 24 closing balances and all per-recipe consumption quantities were checked against `docs/validation_report.md`. Week 2 executed against `28c06ea50bc375f05af80bdf76995c75a61740c2`, which adds only mathematical documentation to that baseline.

All Week 1 leftovers intentionally survive into Week 2, including opened/fresh food. No spoilage or outside consumption is applied. The original `config/initial_inventory.csv`, catalogue, recipe data and optimiser remain unchanged.

## Results

| Metric | Week 1 | Week 2 |
|---|---:|---:|
| Simulated shopping expenditure | £39.88 | £20.44 |
| Estimated consumed ingredient value | £23.99 | £23.62 |
| Dinners, each serving two | 7 | 7 |
| Distinct products purchased (basket lines) | 35 | 19 |
| Retail packs/reference portions purchased | 44 | 26 |
| Ingredient balances carried in | 1 | 24 |
| Nonzero ending balances, carried forward | 24 | 22 |
| Combined objective | 41.34858654 | 21.57313462 |
| Solver status | Optimal (recorded) | Optimal (executed) |

Shopping expenditure is the price of whole purchased products. Consumption value is a separate weighted-average estimate, with opening inventory valued at the cheapest snapshot unit price rather than historical acquisition cost. Neither the expenditure/consumption difference nor closing inventory measures waste. Week 2 requires £19.44 less cash than Week 1 in this scenario; this is not an estimate of permanent savings.

Both weeks select chicken fajita traybake, beef cottage pie, beef chilli with baked potatoes, sweet potato and black bean enchiladas, mushroom stroganoff, tuna sweetcorn jacket potatoes, and lentil shepherd's pie. Recipes and pack quantities remain jointly chosen; none were forced for Week 2.

## Inventory reuse

23 ingredient balances supply Week 2 consumption. Of those, 16 need no additional purchase: beef stock cubes, butter, cheddar, cucumber, cumin, mayonnaise, mustard, peas, flour, red chilli, smoked paprika, sweet potato, tomato puree, fresh tomatoes, vegetable oil and vegetable stock cubes. Carrots, egg noodles, mushrooms, passata, potatoes, sweetcorn and tuna also use opening stock but require top-ups. Carrots fall from three to two reference portions and tuna from two cans to one.

The sole completely unused opening ingredient is the original 10,000 g rice, preserved in full. Many partially used ingredients retain balances; the table below reports these explicitly. Allocation to opening stock is an accounting assumption (use opening stock first); the model does not distinguish physical batches.

| Ingredient | Unit | Opening | Opening stock used | Purchased quantity | Ending |
|---|---|---:|---:|---:|---:|
| beef_stock_mix | cube | 9.5 | 0.5 | 0 | 9 |
| butter | g | 210 | 40 | 0 | 170 |
| carrot | g | 80 | 80 | 320 | 0 |
| cheddar | g | 260 | 140 | 0 | 120 |
| cucumber | each | 0.5 | 0.5 | 0 | 0 |
| egg_noodles | g | 70 | 70 | 250 | 140 |
| ground_cumin | g | 94 | 6 | 0 | 88 |
| long_grain_rice | g | 10000 | 0 | 0 | 10000 |
| mayonnaise | ml | 390 | 60 | 0 | 330 |
| mushrooms | g | 50 | 50 | 400 | 100 |
| mustard | g | 175 | 5 | 0 | 170 |
| passata | g | 200 | 200 | 500 | 400 |
| peas | g | 660 | 240 | 0 | 420 |
| plain_flour | g | 1492 | 8 | 0 | 1484 |
| potatoes | g | 100 | 100 | 1000 | 200 |
| red_chilli | g | 54 | 6 | 0 | 48 |
| smoked_paprika | g | 38.4 | 9.6 | 0 | 28.8 |
| sweet_potato | g | 550 | 450 | 0 | 100 |
| sweetcorn | g | 40 | 40 | 160 | 80 |
| tomato_puree | g | 168 | 32 | 0 | 136 |
| tomatoes | g | 135 | 120 | 0 | 15 |
| tuna | g | 59 | 59 | 102 | 16 |
| vegetable_oil | ml | 965 | 35 | 0 | 930 |
| vegetable_stock | cube | 9 | 1 | 0 | 8 |

## Validation and reproducibility

Each week includes `plan.json` (complete result including costs), `recipes.csv`, `basket.csv`, `consumption.csv`, `opening_inventory.csv`, `ending_inventory.csv`, and `reconciliation.csv`. Week 2 additionally includes complete CBC and application output in `solver_output.txt`. `manifest.json` records parameters, source commits, assumptions, and SHA-256 fingerprints of snapshot and model inputs. These provide an auditable Git snapshot and edit detection, not an automatic or tamper-proof household stock ledger.

Week 2 opening CSV is byte-for-byte identical to Week 1 ending CSV, and all 24 nonzero quantities match the JSON exactly. All purchases are positive integer retail packs/reference portions and eligible catalogue products. Both weeks satisfy opening + purchases - consumption = ending within numerical tolerance, with no consumption beyond supply. CBC reports `Result - Optimal solution found` and objective `21.57313462` for Week 2. The fresh regression solve also reaches the saved optimal objective; it does not require one arbitrary tie-breaking solution.

Executed commands:

```sh
python scripts/validate_seed_data.py
python -m unittest discover -s tests -v
python scripts/optimise_week.py --days 7 --fresh-penalty 0.50 --deviation-penalty 2.0 --show-solver --inventory runs/week_02/opening_inventory.csv --output-json /tmp/week_02_reproduced.json --ending-inventory /tmp/week_02_ending.csv
```

Use new output paths when reproducing; preserve the saved snapshots. Install `requirements.txt` first. Exact saved Week 1 provenance is retained rather than substituting a new solve; later solver versions may choose alternative equal optima.

Actual validation output (`data_validation.txt`):

```text
Seed-data validation PASSED
recipes: 40
used_ingredients: 125
canonical_ingredients: 133
recipe_ingredient_rows: 372
products: 240
eligible_products: 222
covered_ingredients: 125
missing: []
alternatives: 92
Excluded product rows: 18
```

Actual full-suite result (`tests.txt`):

```text
Ran 30 tests in 12.794s

OK
```

## Findings and next extensions

- All seven meals repeat because variety constraints apply within a week. Cross-week recipe history or repetition penalties would improve rotation; none were added here.
- Stock quantities carry correctly, but expiry, opened dates and freezer/storage location need batch-level state. In particular cucumber, mushrooms, opened tuna, cream/dairy and opened canned produce should not automatically be treated as safe for another week. This simulation deliberately retains every balance, without making that safety claim.
- Historical cost per batch would improve consumed-value accounting. Current opening-stock revaluation is an estimate.
- Sequential weekly optimisation need not minimise a joint multiweek objective. Rice remains unused because the current single-week objective and recipe choices do not force stock depletion.
- Future actual-purchase/consumption reconciliation should promote a checked ending balance into household state. These files remain simulation-only; no actual purchase records or automatic state promotion were introduced.
