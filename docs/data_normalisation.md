# Data normalisation

## Purpose

The repository separates the original meal-kit source from the recipes actually given to the optimiser.

The pipeline is:

**Gousto source recipe → canonical ingredient interpretation → household-cleaned recipe → Tesco retail supply**

This avoids optimising Gousto's sachet and meal-kit design as if it were a normal household recipe.

## Source layer

`data/source_recipes.csv` and `data/source_recipe_ingredients.csv` preserve the original Gousto recipe metadata, ingredient wording, source quantities and the unit-normalisation work already done.

The source layer is the audit trail. It is not the direct optimiser input.

## Household-cleaned recipe layer

`data/recipes.csv` and `data/recipe_ingredients.csv` are the optimiser-facing recipes.

Each cleaned ingredient row contains:
- `recipe_id`;
- canonical `ingredient_id`;
- `preferred_quantity`;
- model `unit`;
- `change_type` describing whether the household recipe kept, adjusted, added or substituted the source ingredient;
- a short note where the reason is material.

An ingredient removed during cleansing is absent from the cleaned recipe but remains visible in the preserved source layer.

## What recipe cleansing is allowed to do

Cleaning happens before optimisation and may:
- round impractical meal-kit quantities;
- use a whole sensible retail portion where that is how a household would normally cook;
- replace proprietary/sachet-style ingredients with ordinary household equivalents;
- reduce meal-kit upsells such as double-protein variants;
- increase under-sized vegetable or starch portions;
- remove decorative or unusually expensive flourishes that do not materially define the dish;
- add a normal ingredient where the source used a shortcut product.

The aim is not to make every recipe share the same ingredients. Changes should still make culinary sense.

## Examples in the current seed

- R001 uses 160 g usable sweetcorn so the small drained tin is naturally consumed.
- R003 drops crispy onions and uses the same ordinary chicken stock family used elsewhere.
- R005 removes the double-chicken configuration and replaces mayonnaise/garlic paste with yoghurt and fresh garlic.
- R006 uses two noodle nests for two adults and replaces ginger-garlic paste with fresh ingredients.
- R008 removes quick-kit mango chutney/tomato/stock shortcuts and uses yoghurt, fresh ginger, garlic and coriander.
- R010 removes saffron and replaces Gousto's combined coriander-and-mint pack with ordinary fresh coriander.

## Canonical ingredient layer

`data/ingredients.csv` is the stable vocabulary joining recipes to retail products.

It stores:
- canonical ID/name;
- category;
- preferred model unit;
- coarse shelf-life class;
- inventory policy;
- default quantity-flexibility class.

Source-only canonical ingredients may remain in this table even when the cleaned v1 recipes no longer use them. That preserves source auditability without forcing them into the optimiser basket.

## Unit conversions

`data/unit_conversions.csv` documents conversions such as:
- onion `each → g`;
- garlic `clove → g`;
- spice `tsp → g`;
- noodle `nest → g`.

These conversions are primarily needed to interpret source recipes and compare them with retail supply.

Conversions record method, status, confidence, source and notes so approximate values are visible rather than hidden.

## Retail products

`data/products.csv` stores real Tesco package/price options mapped to canonical ingredients.

Each row represents one real Tesco listing and carries:
- an exact Tesco `retailer_product_id`;
- exact product URL;
- pack quantity/unit;
- price snapshot;
- product form;
- mapping status.

Multiple retail products may supply the same canonical ingredient so the optimiser can choose among pack sizes.

## Usable quantity

For most products:

`usable quantity = labelled pack quantity`

When that is materially false, `usable_quantity` is populated and should override the label quantity in stock calculations.

The sweetcorn tins are the clearest current example because drained edible weight differs materially from can net weight.

## Variable-weight produce

Loose onions, carrots, courgettes and similar products are represented as weight-based supply where Tesco sells them that way.

The mathematical model will decide how to represent realistic purchase increments.

## Flexibility is separate from cleansing

Recipe cleansing answers:

**What is the sensible household version of this recipe?**

Quantity flexibility answers:

**Once that recipe is fixed, how far may a selected ingredient reasonably move around its preferred household quantity?**

The current flexibility-class assumptions live in `config/flexibility_classes.csv` and should be sensitivity-tested later.

## Starting inventory

`config/initial_inventory.csv` can contain any ingredient already in the household.

Ingredients not listed start at zero. End-of-cycle usable stock is intended to roll into the next planning cycle.

## Deliberately deferred

The first deterministic model does not require:
- exact shelf-life distributions;
- live Tesco availability;
- pantry scanning/detection;
- cooking-yield models for every food;
- nutrition optimisation;
- open/sealed package-state tracking.

Those should be added only if later experiments show that they materially improve the model.
