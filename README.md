# Grocery Optimiser

A research prototype that jointly chooses approved meals and supermarket pack sizes, with the aim of reducing avoidable food waste and unnecessary spend while carrying useful inventory forward.

The project is inspired by van Rooijen et al. (2024) and adapts optimisation-based household meal planning to a UK/Tesco setting with real recipes, real retail pack sizes, flexible recipe quantities and rolling household inventory.

## Current stage

**Stage 1 complete: cleaned household seed recipes + resolved retail products.**

The optimiser-facing recipe layer now contains **10 household-cleaned dinners** derived from Gousto recipes. The original Gousto metadata and ingredient lists are preserved separately for audit.

Cleaning removed meal-kit artefacts where they distorted normal household cooking. Examples include:
- reducing Gousto's double-chicken Greek recipe from 500 g to a normal two-person chicken portion;
- using two noodle nests for two adults in the smaller-portioned hoisin noodle recipe;
- replacing ginger/garlic pastes with fresh ginger and garlic where practical;
- replacing the combined coriander-and-mint meal-kit pack with ordinary fresh coriander;
- removing saffron from the harissa recipe;
- simplifying the quick-kit korma into a more normal yoghurt/coconut/spice structure;
- using the full usable amount of a small sweetcorn tin instead of preserving a 150 g meal-kit quantity.

The repository currently contains:
- 10 cleaned household recipes;
- 105 cleaned recipe-ingredient rows;
- the original 10 Gousto recipes and 105 source ingredient rows;
- 61 canonical ingredients;
- 83 real Tesco product/package rows, each resolved to an exact Tesco product ID/page;
- 23 documented source-unit conversions;
- 4 provisional recipe-flexibility classes;
- household starting inventory configuration.

The dataset is now sufficient for the **first deterministic optimiser**. It is still a seed library; scaling from 10 recipes toward roughly 100–300 comes after the model formulation is working.

## Repository structure

```text
config/
  initial_inventory.csv
  flexibility_classes.csv

data/
  recipes.csv
  recipe_ingredients.csv
  source_recipes.csv
  source_recipe_ingredients.csv
  ingredients.csv
  products.csv
  unit_conversions.csv

docs/
  problem_definition.md
  data_normalisation.md

scripts/
  validate_seed_data.py
```

### Optimiser-facing vs source data

- `data/recipes.csv` and `data/recipe_ingredients.csv` are the **cleaned household recipes used by the optimiser**.
- `data/source_recipes.csv` and `data/source_recipe_ingredients.csv` preserve the original Gousto recipe representation and conversions.
- `data/ingredients.csv` is the canonical ingredient vocabulary.
- `data/products.csv` is the real Tesco product/package table.
- `data/unit_conversions.csv` documents household-measure conversions used when interpreting source recipes.

## Core v1 principles

- The optimiser chooses only from a pre-approved recipe library.
- Recipe cleansing happens **before optimisation**; the optimiser does not decide to drop inconvenient ingredients from a recipe.
- Cleaned recipe quantities are preferred household quantities, not blindly copied meal-kit sachet sizes.
- Divisible solids are generally modelled in grams; suitable liquids in millilitres.
- Retail products are bought in real pack sizes; `usable_quantity` overrides labelled pack weight where the edible/drained amount materially differs.
- Starting inventory can exist for any ingredient. Omitted ingredients start at zero.
- Usable ending inventory rolls into the next planning cycle.
- Rice is currently configured as 10 kg starting stock; that is a household scenario, not a special rule in the optimiser.
- Quantity flexibility is a separate modelling assumption and will be sensitivity-tested.

## Data freshness

Tesco product identities/URLs were resolved on 2026-10-21. Price fields remain a research snapshot around 2026-10-20/21 and should not be treated as permanently current.

## Reference

M. A. van Rooijen, J. C. Gerdessen, G. D. H. Claassen, and S. L. J. M. de Leeuw (2024), *Optimizing household food waste: The impact of meal planning, package sizes, and performance indicators*, Resources, Conservation & Recycling 205, 107559.  
https://doi.org/10.1016/j.resconrec.2024.107559
