# Grocery Optimiser

A research prototype for automatically selecting meals and supermarket packs together, with the aim of reducing avoidable food waste without forcing unrealistic zero-leftover behaviour.

The project starts from a mixed-integer meal-planning idea in van Rooijen et al. (2024), then adapts it to a UK household setting with real recipe data and Tesco package/price snapshots.

## What the optimiser should eventually decide

- which meals to cook automatically — the user should not have to choose recipes first;
- how much of each flexible recipe ingredient to use within sensible bounds;
- which supermarket pack sizes and quantities to buy;
- what stock to carry forward into the next planning cycle;
- how to balance purchase cost, spoilage risk, variety, convenience and useful carryover.

The planning horizon is intended to be rolling rather than a rigid seven-day box. Later simulation experiments will investigate which shopping intervals and package-size policies work best over time.

## Seed data

This repository deliberately starts with real data rather than toy recipes:

- `data/recipes.csv` — 10 Gousto dinner recipes for 2 people, currently chicken-focused and fish-free.
- `data/recipe_ingredients.csv` — source ingredient quantities mapped to canonical ingredient IDs.
- `data/ingredients.csv` — canonical ingredient layer used to join recipes to retail products.
- `data/products.csv` — initial Tesco UK product/package/price snapshot captured on 2026-10-20.

Only recipe ingredient lists and metadata are stored; cooking instructions remain at the linked source pages.

Tesco prices, promotions and listings are time-sensitive. Every retail row therefore carries a source URL and `source_checked_at` date. This is research seed data, not a live price feed.

## Data-normalisation principle

The source recipe quantity is never overwritten. Exact gram and millilitre quantities can be normalised directly. Household measures such as `each`, `clove`, `tsp`, `tbsp`, `nest`, `pod` and `packet` remain unresolved until a defensible conversion is added.

This follows the spirit of van Rooijen et al. (2024), who standardised recipe ingredients to a common food-code system, converted household measures to grams using a portion-size database, and used edible weights. Our UK version keeps the same separation of concerns but does not invent conversions that we have not yet sourced.

See `docs/data_normalisation.md`.

## Current stage

**Stage 0 — real-data foundation.**

There is intentionally no optimiser code yet. The first objective is to make the recipe → canonical ingredient → retail product relationship explicit and identify real-world data problems before writing the mathematical model.

Known issues already surfaced include:

- recipes expressed in grams, millilitres, counts, teaspoons, tablespoons and nests;
- loose produce with variable weights;
- retail net weight versus usable/drained weight;
- several valid pack sizes for one ingredient;
- product-form differences and substitutions that must not be silently treated as identical;
- temporary prices such as Clubcard promotions.

## Research reference

M. A. van Rooijen, J. C. Gerdessen, G. D. H. Claassen, and S. L. J. M. de Leeuw (2024), *Optimizing household food waste: The impact of meal planning, package sizes, and performance indicators*, Resources, Conservation & Recycling 205, 107559.  
https://doi.org/10.1016/j.resconrec.2024.107559
