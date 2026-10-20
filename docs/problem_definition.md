# Problem definition

## User problem

A normal meal-planning app often asks the user to choose recipes first and then totals the ingredients. This project starts one level earlier: the system should choose a sensible mix of meals itself and make those choices jointly with supermarket package decisions.

The practical goal is:

> Automatically choose a good sequence of meals and a sensible basket so that short-life food is rarely discarded, larger packs are used when they are genuinely economical, and useful stock carries forward naturally.

## Decisions the model should eventually make

1. **Recipe selection**
   - Select meals automatically from a **pre-approved candidate recipe library**.
   - The recipe library is the main quality/acceptability filter: if a meal is not something the household would want to eat, it should not be in the candidate set.
   - Avoid an obviously repetitive plan without building a subjective “taste score” for arbitrary recipes.
   - Allow simple variety rules to be modelled separately from waste/cost when needed.

2. **Recipe quantity**
   - A recipe ingredient need not always be a single rigid number.
   - The first model uses four **flexibility classes** instead of manually inventing min/preferred/max for every recipe row: `fixed`, `tight`, `moderate`, and `wide`.
   - These classes generate a first-pass allowable interval around the published recipe quantity.
   - The class boundaries are modelling assumptions and will be sensitivity-tested; recipe-specific overrides can be added later.

3. **Retail package selection**
   - Choose whole retail packs where the product is sold as a fixed pack.
   - Allow variable-weight products where the retailer sells loose produce.
   - Do not assume the smallest pack is best: a larger pack may have a lower unit price and may be useful in later meals.

4. **Inventory and carryover**
   - Track what remains after each meal.
   - Remaining stock should not automatically be called waste.
   - Carry stock into later planning cycles when it is still usable.
   - Use an effective usable quantity for products where packaging/net weight materially differs from edible/drained supply.

5. **Rolling planning**
   - Do not hard-code “exactly seven days” as the universal optimal shopping cycle.
   - The system may commit to the next shopping period while looking further ahead to estimate the value of leftovers.
   - Re-optimise as time passes and stock/real life changes.

## Inventory policies

Not every ingredient needs the same optimisation treatment.

### A. Assumed-on-hand staples

Some foods are household staples kept in bulk and should not distort weekly meal choice.

For the first household scenario, **long-grain rice is assumed to be already available in bulk** (for example a 10 kg starting stock). The optimiser consumes from that stock but does not choose a new rice pack during the initial meal-planning experiment.

Later simulation can add a reorder threshold so staples are replenished when stock becomes low.

Likely examples include:
- long-grain rice;
- salt;
- cooking oil;
- water.

This list is household-specific rather than universal.

### B. Durable tracked inventory

Spices, dry pantry goods and long-lived sauces are bought in jars/packs and then persist across many planning cycles.

Examples:
- turmeric;
- paprika;
- garam masala;
- dried oregano;
- cornflour;
- sesame oil.

The model should buy these only when existing stock is insufficient, subtract recipe usage, and carry the remainder forward. A partly used spice jar is inventory, not weekly food waste.

### C. Fresh / spoilage-sensitive inventory

Meat, dairy, fresh greens, herbs and most vegetables require the strongest stock and shelf-life treatment.

Examples:
- chicken;
- yoghurt;
- spinach;
- peppers;
- fresh herbs.

These are the ingredients for which package size, recipe overlap, flexible serving quantity and shopping horizon matter most.

## Quantity modelling principle

The model should optimise in units that make recipe demand and retail supply comparable.

As a default:

- solid foods are modelled in grams;
- liquids are modelled in millilitres where that matches retail labelling;
- true count items can remain `each` only when count is stable and meaningful.

Recipe measures such as `1 onion`, `1 garlic clove`, `1 red pepper`, `0.5 tsp turmeric` and `1 noodle nest` can be converted to model units using **ingredient-specific conversion parameters**.

These conversions do not all need laboratory precision. A small error in the assumed weight of a garlic clove or half-teaspoon of turmeric is unlikely to change an economically meaningful shopping decision. The model should spend precision where it materially affects cost or spoilage.

This is a deliberate **materiality principle**:
- high-impact foods: model carefully;
- low-cost, durable, small-quantity foods: defensible approximations are acceptable.

## Objective — not finalised yet

The first model should not optimise “leftover grams” alone.

The eventual objective is expected to combine at least:

- purchase cost;
- spoilage / discarded food;
- value of usable carryover;
- meal variety / acceptability;
- shopping convenience or frequency.

Weights, priorities, or lexicographic ordering are research decisions and should be tested rather than assumed.

## Simulation layer

The optimiser answers: **what should I buy and cook now?**

A later simulation layer will answer policy questions such as:

- Is a 3-, 5-, 7-, or 10-day shopping interval better for this household?
- When does a 1 kg pack outperform a 500 g pack after spoilage and future use are considered?
- Which recipes repeatedly act as useful “connector recipes” for leftover stock?
- How much does flexible recipe quantity reduce waste?
- How robust is the plan when a meal is skipped or the household eats out?
- When should bulk staples be reordered?

The shopping interval itself is therefore a candidate experimental variable, not a fixed truth.

## Initial scope

For the first implementation:

- 2-person dinners;
- 10 real Gousto recipes;
- chicken-focused, no fish;
- real Tesco UK package/price snapshot;
- published recipe quantities retained exactly as source data;
- a separate conversion layer maps household measures into model units;
- long-grain rice treated as an assumed-on-hand staple in the first household scenario;
- salt, cooking oil and water excluded from the first basket model;
- durable pantry ingredients carried across planning cycles;
- no nutrition optimisation yet;
- no live Tesco integration yet.

The purpose of this scope is to get a small real model working before adding more recipes, nutrients, live product data, stochastic behaviour, or an interface.


## First-model flexibility assumptions

The seed model currently uses:

| Class | Minimum | Preferred | Maximum | Typical first-pass use |
|---|---:|---:|---:|---|
| fixed | 100% | 100% | 100% | spices and stock |
| tight | 90% | 100% | 110% | starches, sauces, pantry items |
| moderate | 80% | 100% | 120% | protein and dairy |
| wide | 70% | 100% | 130% | vegetables and fresh aromatics |

These values are deliberately provisional. The purpose is to let the first optimiser test the value of quantity flexibility without pretending we already know the true culinary tolerance of every ingredient.

A later experiment should compare these classes with:
- completely fixed recipes;
- narrower/wider class definitions;
- recipe-specific bounds where justified.

## Data-readiness checkpoint — 2026-10-20

The initial real-data pass is now sufficient for the first deterministic model:

- 10 recipes;
- 105 recipe-ingredient rows;
- 60 canonical ingredients;
- 83 Tesco product/package rows;
- no recipe ingredient lacks a normalised model quantity;
- no required source-unit conversion is blank;
- every used ingredient has a retail supply option or household-stock policy;
- every canonical ingredient has a default flexibility class.

Remaining uncertainty is recorded explicitly as confidence/status metadata and should be tested rather than silently treated as exact.
