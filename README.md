# Grocery Optimiser

Choose seven varied dinners for two people and integer Tesco retail packs, balancing shopping cost, fresh surplus risk and small departures from preferred recipe quantities. Useful leftovers remain inventory; there is no requirement to finish a pack within one week.

## Verified snapshot: 23 October 2026

- 40 active recipes, 373 active recipe-ingredient rows, 125 active ingredients used and 209 canonical ingredient definitions.
- 160 additional staged recipes with 1,404 ingredient lines and 198 staged ingredients; all pass the staged coverage validator.
- 332 distinct Tesco listings, each with product-page verification evidence.
- 307 eligible product rows overall; 219 serve currently active ingredients, providing 94 alternatives beyond one option per active ingredient.
- All 125 used ingredients have an eligible purchasing option; no ingredient coverage exceptions.
- All 205 ingredients used across the active and staged recipes have an eligible purchasing option.
- 25 unavailable or unresolved product rows are retained for audit and excluded from purchasing.

See [validation report](docs/validation_report.md) for executed results, the seven-dinner basket, corrections and limitations; [coverage audit](docs/catalogue_coverage.md) lists every ingredient and excluded product.

## Run

Python 3.11+:

```sh
python -m pip install -r requirements-app.txt
python scripts/validate_seed_data.py
python -m unittest discover -s tests -v
python scripts/optimise_week.py --days 7
```

PuLP is pinned to 3.3.0, including the CBC solver used in the tests. A successful result requires proven solver optimality, not just a feasible incumbent.

Optional outputs and scenarios:

```sh
python scripts/optimise_week.py --days 7 --output-json plan.json --ending-inventory next_inventory.csv
python scripts/optimise_week.py --days 7 --inventory next_inventory.csv
python scripts/optimise_week.py --days 3 --require-recipes R015 R017 R018
```

Before reusing inventory, remove anything eaten, discarded or no longer usable. Exporting a balance does not establish food safety or expiry. The regression test carries durable stock to week two without assuming opened fresh food lasts another week.

## Data and code

| File | Purpose |
|---|---|
| `data/recipes.csv` | Forty household dinners with methods and two servings |
| `data/recipe_ingredients.csv` | Authoritative preferred quantities and canonical units |
| `data/ingredients.csv` | Ingredient identities, units, shelf-life classes and flexibility |
| `data/products.csv` | Active Tesco products with canonical ingredient IDs, gross/usable quantities, prices, availability and URLs |
| `data/product_evidence.csv` | Observed Tesco product-page facts for every listing |
| `data/unit_conversions.csv` | Documented historical household/source conversions, including explicit approximations |
| `config/initial_inventory.csv` | Actual model starting stock; example includes 10 kg rice |
| `config/flexibility_classes.csv` | Bounds on preferred quantities |
| `scripts/catalogue.py` | Shared strict CSV reader and eligibility rules |
| `scripts/validate_seed_data.py` | Active-data integrity, evidence and complete eligible-coverage gate |
| `scripts/validate_staging_data.py` | Equivalent coverage, unit and method checks for every staged batch |
| `scripts/generate_catalogue_coverage.py` | Rebuild the active-and-staged catalogue coverage audit |
| `scripts/optimise_week.py` | Joint recipe, pack and inventory MILP |
| `tests/test_project.py` | Data-corruption, purchasing and end-to-end regression tests |

The old `source_recipes.csv` and `source_recipe_ingredients.csv` files are not present in this repository. Inspiration URLs are optional provenance; cooking methods are household adaptations, not claimed verbatim source recipes. Staged methods may be AI-simplified from the structured ingredient list when declared in their notes. They are reviewed for practical sequencing, food safety and minimal unnecessary equipment before promotion.

## Model behaviour

Purchases are whole retail packs or integer reference portions of loose produce. Consumption is independent: eggs and whole-item recipes use integer quantities; cucumber and stock cubes allow half units; grams and millilitres are divisible. Single and soured cream and canned coconut milk use millilitres. Tinned beans, tuna, olives and mozzarella use labelled drained quantities where relevant.

The objective is purchase expenditure plus a provisional value-based short-life surplus penalty plus a proportional penalty for deviations **in either direction** from recipe preferences. The last term prevents free inflation of portions to absorb surplus. Default weights are `--fresh-penalty 0.50` and `--deviation-penalty 2.0`. These are modelling assumptions, not measured food-waste probabilities. Long-life stock has no surplus penalty. Variety caps apply to protein and cooking-method groups when feasible; recipes cannot repeat within a plan.

Prices are regular-price snapshots. Active single-product Clubcard prices are recorded, but this model deliberately costs regular prices; conditional multibuys are documented rather than incorrectly converted into single-product discounts. Delivery fees, Clubcard multibuy optimisation and postcode/slot-specific availability are not modelled.

## Important scope

This is a deterministic planning prototype. Online listing availability does not guarantee stock for a Northern Ireland delivery postcode. Fresh/frozen alternatives require appropriate thawing and storage. Loose-produce weights and garlic/onion yields are disclosed estimates; checkout weights may differ. Shelf-life classes are coarse, without opened-pack or freezer-location tracking. There is no nutrition constraint, expiry-aware cooking schedule, live basket integration or rolling multiweek objective. Ending inventory is an accounting balance, not measured waste.

## Research inspiration

M. A. van Rooijen et al. (2024), *Optimizing household food waste: The impact of meal planning, package sizes, and performance indicators*, Resources, Conservation & Recycling 205, 107559. https://doi.org/10.1016/j.resconrec.2024.107559

## Saved two-week simulation

[Locked Week 1 and executed Week 2](runs/README.md) preserve the £39.88 original basket and a £20.44 optimal second-week basket using all 24 opening leftover balances. Both weeks include complete plans, inventory and reconciliation files. This is explicitly simulated consumption, assuming all leftovers survive; it does not overwrite the baseline inventory or represent actual purchases. The full 32-test suite includes product-schema, staged-coverage, recipe-method quality, snapshot-integrity and two-week balance regression checks.

## Household web application

The first mobile-friendly application is implemented in [`app/`](app/) with a Python API and persistent inventory. Browse recipes, pin meals, save exclusions, generate plans, confirm received products and record cooked/skipped meals. Manual stock entry distinguishes additions from total corrections. New households start empty; simulations never become actual stock automatically.

See [application setup, database design and tested behaviour](docs/application.md). Install `requirements-app.txt` to run the app and full test suite. [Supabase SQL](db/001_initial.sql), a Dockerfile and a Render deployment blueprint are supplied. This version has been tested locally but is **not yet deployed to a live database or public phone URL**.
