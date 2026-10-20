# Grocery Optimiser

A research prototype for automatically selecting meals and supermarket packs together, with the aim of reducing avoidable food waste without forcing unrealistic zero-leftover behaviour.

The project starts from a mixed-integer meal-planning idea in van Rooijen et al. (2024), then adapts it to a UK household setting with real recipe data and Tesco package/price snapshots.

## What the optimiser should eventually decide

- which meals to cook automatically — the user should not have to choose recipes first;
- how much of each flexible recipe ingredient to use within sensible bounds;
- which supermarket pack sizes and quantities to buy;
- what stock to carry forward into the next planning cycle;
- how to balance purchase cost, spoilage risk, convenience and useful carryover.

Meal acceptability is controlled primarily by the **candidate recipe library**: the optimiser chooses only from recipes already considered acceptable to the household. It does not need to invent a taste score for arbitrary meals.

The planning horizon is intended to be rolling rather than a rigid seven-day box. Later simulation experiments will investigate which shopping intervals and package-size policies work best over time.

## Seed data

This repository deliberately starts with real data rather than toy recipes:

- `data/recipes.csv` — 10 Gousto dinner recipes for 2 people, currently chicken-focused and fish-free.
- `data/recipe_ingredients.csv` — 105 source ingredient rows mapped to canonical ingredient IDs and model units.
- `data/ingredients.csv` — 60 canonical ingredients with inventory and flexibility policies.
- `data/products.csv` — 83 Tesco UK product/package options covering every canonical ingredient used by the seed recipes.
- `data/unit_conversions.csv` — explicit source-unit → model-unit conversions with source/method/confidence.
- `data/flexibility_classes.csv` — first-pass recipe-quantity flexibility assumptions.
- `config/initial_inventory.csv` — household-specific starting stock; currently includes 10 kg long-grain rice.

Only recipe ingredient lists and metadata are stored; cooking instructions remain at the linked source pages.

Tesco prices, promotions and listings are time-sensitive. Every retail row carries a source URL and `source_checked_at` date. This is research seed data, not a live price feed.

## Data-normalisation principle

The source recipe quantity is never overwritten. The optimisation layer uses a canonical unit for each ingredient — usually grams for divisible solids and millilitres for suitable liquids.

Household measures such as `each`, `clove`, `tsp`, `tbsp`, `nest`, `pod` and `packet` are converted through a separate, auditable conversion table. Some conversions are well sourced; others are deliberately marked provisional when only an approximate value is justified.

This follows the spirit of van Rooijen et al. (2024), who standardised recipe ingredients to a common food-code system, converted household measures to grams using a portion-size database, and used edible weights.

See `docs/data_normalisation.md`.

## Inventory policies

The first model distinguishes:

- **assumed-on-hand staples** — e.g. long-grain rice in the current household scenario;
- **durable tracked inventory** — spices, dry goods and long-lived sauces that persist across planning cycles;
- **fresh tracked inventory** — meat, dairy, vegetables and herbs where package size and spoilage matter more.

A leftover quantity is therefore not automatically “waste”.

## Recipe quantity flexibility

Instead of manually inventing min/preferred/max values for every recipe ingredient, the seed model assigns one of four provisional classes:

- `fixed`: 100% of the published quantity;
- `tight`: 90–110%;
- `moderate`: 80–120%;
- `wide`: 70–130%.

These are **modelling assumptions, not food-science facts**. They exist to make the first optimiser testable and must later be sensitivity-tested or overridden for specific recipe ingredients when evidence or cooking logic justifies it.

## Current stage

**Stage 1 — model-ready real-data seed set.**

The current data pass is complete enough to begin the first optimiser:

- all 105 recipe-ingredient rows have model quantities/units;
- all 60 canonical ingredients used by the recipes have a Tesco supply option or household-stock policy;
- all required unit conversions have a first-pass value;
- every canonical ingredient has a first-pass flexibility class.

Important approximations remain explicitly labelled rather than hidden, especially some count/spoon conversions, product-form substitutions and the Gousto saffron packet proxy.

The next stage is **Stage 2 — first deterministic optimisation model**. No live Tesco integration, rolling simulation or UI is required before that.

## Research reference

M. A. van Rooijen, J. C. Gerdessen, G. D. H. Claassen, and S. L. J. M. de Leeuw (2024), *Optimizing household food waste: The impact of meal planning, package sizes, and performance indicators*, Resources, Conservation & Recycling 205, 107559.  
https://doi.org/10.1016/j.resconrec.2024.107559
