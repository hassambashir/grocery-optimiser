# Data normalisation

## Purpose

Recipes and supermarkets describe the same food differently. The optimiser therefore separates four layers:

1. **Source recipe ingredient** — original wording and quantity from the recipe.
2. **Canonical ingredient** — stable internal ingredient identity.
3. **Unit conversion** — conversion from household recipe measures to the model unit where required.
4. **Retail product** — a specific Tesco pack or variable-weight option that can supply the canonical ingredient.

Example:

`Chicken breast strips` / `Chicken breast portions` / `Diced chicken breast`
→ `chicken_breast`
→ Tesco 350 g / 650 g / 1 kg / 1.6 kg / 2 kg options.

## Relation to the research paper

Van Rooijen et al. (2024) standardised recipe ingredients to NEVO food codes, converted household measures to grams using a Dutch portion-size database, and worked with edible weights.

This project uses the same separation principle, adapted to real UK recipe and Tesco data.

Reference: https://doi.org/10.1016/j.resconrec.2024.107559

## Source quantities are preserved

`data/recipe_ingredients.csv` keeps:

- `source_ingredient_name`;
- `source_quantity`;
- `source_unit`;
- the resulting canonical ingredient and model quantity.

The published recipe value is never silently overwritten.

## Canonical units

For the first model:

- most divisible solid foods use grams;
- suitable liquids use millilitres.

Recipe measures such as `1 onion`, `2 garlic cloves`, `0.5 tsp turmeric` or `1 noodle nest` are converted using `data/unit_conversions.csv`.

## Conversion quality

Conversions do not all deserve the same precision.

A material error in chicken quantity may change the pack decision. A small error in half a teaspoon of turmeric probably will not.

Each conversion therefore records:

- multiplier;
- conversion method;
- status;
- confidence;
- source URL;
- notes.

Some conversions are sourced directly; others remain explicit provisional approximations and should later be sensitivity-tested.

## Canonical ingredient metadata

`data/ingredients.csv` stores:

- canonical ID/name;
- category;
- preferred model unit;
- coarse shelf-life class;
- inventory policy;
- default quantity-flexibility class.

The current `shelf_life_class` values are deliberately coarse: `short`, `medium`, `long`, or `unknown`. They are metadata for later spoilage modelling; v1 does not yet turn them into exact expiry-day constraints.

## Retail products

`data/products.csv` stores Tesco package/price options mapped to canonical ingredients.

Multiple products can map to one ingredient so the optimiser can choose among pack sizes.

Every row in `products.csv` now represents one real Tesco product/listing and carries an exact `retailer_product_id`, exact Tesco product URL, and `product_resolution_status=resolved_exact`.

Ingredient-to-product compatibility is still a separate question. `mapping_status` may therefore be direct, compatible candidate, substitution candidate, estimated usable weight, variable-weight supply, or effective usable quantity.

These labels preserve uncertainty rather than pretending every match is exact.

## Usable quantity

For most products:

`usable quantity = labelled pack quantity`

When that is materially false, `usable_quantity` is populated and should be used by the optimiser.

Examples include drained canned food and count-based produce packs that need an estimated edible gram quantity.

There is no open/sealed package-state model in v1.

## Variable-weight produce

Loose onions, carrots, courgettes and similar products are represented as weight-based supply when Tesco sells them that way.

The mathematical model can later decide whether to treat this as continuous grams or realistic purchase increments.

## Composite ingredients

A combined source quantity is not split without evidence.

For example, Gousto's `Coriander & mint (10g)` remains one composite canonical ingredient because the source does not tell us the internal split.

The earlier synthetic `Coriander 30G + Mint 30G Retail Bundle` row has been removed from `products.csv`. Real Tesco coriander and mint products exist, but mapping a single 10 g combined recipe quantity onto two separate retail products requires a modelling rule we have not yet justified. This remains one explicit retail-mapping exception rather than fabricated data.

## Product-form compatibility

Related products are not automatically treated as identical.

Examples:
- red pepper vs mixed-pepper pack;
- tomato paste vs tomato puree;
- generic soy sauce vs light soy;
- Gousto seasoning blend vs a retail substitute.

Compatibility is explicit in `mapping_status` and notes.

## Flexibility is separate from conversion

`config/flexibility_classes.csv` controls how far the optimiser may deliberately move away from the preferred recipe quantity.

This is separate from unit conversion:

- conversion asks **what does the source quantity mean in model units?**
- flexibility asks **how far may the optimiser adjust that quantity?**

Keeping them separate avoids confusing measurement uncertainty with a deliberate recipe adjustment.

## Starting inventory

`config/initial_inventory.csv` can contain any ingredient already in the household.

Ingredients not listed start at zero. Usable end-of-cycle inventory is intended to roll into the next cycle.

## Deliberately deferred

The first deterministic model does not require:

- exact shelf-life distributions;
- live Tesco availability;
- pantry scanning/detection;
- cooking-yield models for every food;
- nutrition optimisation;
- open/sealed package-state tracking.

Those should be added only if later experiments show that they materially improve the model.
