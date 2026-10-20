# Grocery Optimiser

A research prototype that jointly chooses approved meals and supermarket pack sizes, with the aim of reducing avoidable food waste and unnecessary spend while carrying useful inventory forward.

The project is inspired by van Rooijen et al. (2024) and adapts optimisation-based household meal planning to a UK/Tesco setting with real recipes, real retail pack sizes, flexible recipe quantities and rolling household inventory.

## Current stage

**Stage 1 complete: model-ready seed dataset.**

The repository currently contains:

- 10 real Gousto dinners for 2 people;
- 105 recipe-ingredient rows;
- 60 canonical ingredients;
- 83 Tesco product/package rows;
- 23 explicit household-measure conversions;
- 4 provisional recipe-flexibility classes;
- household starting inventory configuration.

The next stage is the first deterministic optimisation model. Live Tesco integration, shelf-life simulation and a user interface are deliberately deferred.

## Repository structure

```text
config/
  initial_inventory.csv
  flexibility_classes.csv

data/
  recipes.csv
  recipe_ingredients.csv
  ingredients.csv
  products.csv
  unit_conversions.csv

docs/
  problem_definition.md
  data_normalisation.md

scripts/
  validate_seed_data.py
```

### What each part means

- `docs/problem_definition.md` — what the optimiser is supposed to decide and the current modelling assumptions.
- `docs/data_normalisation.md` — how recipe wording, canonical ingredients, units and Tesco products are reconciled.
- `config/` — household/model assumptions that may change between scenarios.
- `data/` — source and reference data used by the model.
- `scripts/validate_seed_data.py` — consistency checks for the seed dataset.

## Core v1 principles

- The optimiser chooses only from a pre-approved recipe library.
- Divisible solids are generally modelled in grams; suitable liquids in millilitres.
- Source recipe quantities are preserved, with conversions stored separately.
- Retail products are bought in real pack sizes; `usable_quantity` overrides labelled pack weight where the edible/drained amount materially differs.
- Starting inventory can exist for any ingredient. Omitted ingredients start at zero.
- Usable ending inventory rolls into the next planning cycle.
- Rice is currently configured as 10 kg starting stock; that is a household scenario, not a special rule in the optimiser.
- Quantity flexibility is a modelling assumption and will be sensitivity-tested.

## Data freshness

Tesco prices and listings are snapshots, currently checked on 2026-10-20. The optimiser should not assume they are permanently current.

## Reference

M. A. van Rooijen, J. C. Gerdessen, G. D. H. Claassen, and S. L. J. M. de Leeuw (2024), *Optimizing household food waste: The impact of meal planning, package sizes, and performance indicators*, Resources, Conservation & Recycling 205, 107559.  
https://doi.org/10.1016/j.resconrec.2024.107559
