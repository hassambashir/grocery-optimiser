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
   - Every canonical ingredient may have a starting inventory quantity. Missing rows in the starting-inventory file mean zero, not “this ingredient cannot be carried”.
   - Track purchases, consumption and remaining usable stock.
   - Remaining stock should not automatically be called waste.
   - End-of-cycle usable stock becomes the next cycle's starting stock.
   - Use an effective usable quantity for products where packaging/net weight materially differs from edible/drained supply.
   - Preserve package state where it matters: an unopened tin is not equivalent to a partly used opened tin.

5. **Rolling planning**
   - Do not hard-code “exactly seven days” as the universal optimal shopping cycle.
   - The system may commit to the next shopping period while looking further ahead to estimate the value of leftovers.
   - Re-optimise as time passes and stock/real life changes.

## Inventory policies

Not every ingredient needs the same optimisation treatment.

### A. Assumed-on-hand staples

Some foods are household staples kept in bulk and should not distort weekly meal choice.

For the first household scenario, **long-grain rice is one example of non-zero starting inventory** (currently 10 kg). The same mechanism applies to every ingredient: yoghurt, garlic, spices, vegetables or anything else may start with a non-zero quantity if it is already in the kitchen.

The optimiser consumes from starting stock first as part of the same inventory balance. Whatever usable stock remains at the end of one planning cycle rolls into the next cycle. Ingredients omitted from the starting-inventory file simply start at zero.

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


## Opened-package behaviour

Usable quantity and package-opening behaviour are separate concepts.

For a can of sweetcorn, for example:
- the retail can may be labelled 325 g;
- the edible/drained supply may be about 260 g;
- the optimiser must buy whole cans;
- an **unopened** extra can can carry forward normally;
- a **partly used opened** can is undesirable and should usually be finished soon.

The first model therefore marks tinned sweetcorn products with `prefer_full_pack_once_opened`.

This should be a **strong preference rather than an absolute rule**. A hard rule could force an unreasonable portion. The optimiser should instead have several ways to avoid an opened remainder:

1. choose the smaller can if it fits the recipe better;
2. adjust the recipe quantity within its allowed flexibility;
3. select another approved recipe that can use the remaining sweetcorn;
4. use the remainder in another selected meal within the relevant period;
5. accept a small opened remainder only when the alternatives are worse.

This is important because aggregate inventory alone cannot distinguish “one unopened tin left” from “220 g left in a tin that had to be opened”. The optimisation model should explicitly distinguish whole unopened packs from the residual of a partially used pack for products whose `package_consumption_policy` requires it.

Conceptually, for a fixed usable pack size (Q):

- whole unused packs can roll forward without an opened-food penalty;
- once a pack is partially consumed, the residual (Q - 	ext{partial use}) receives a strong penalty;
- recipe flexibility and recipe selection are allowed to reduce that residual.

The exact linear formulation belongs in Stage 2 rather than in the data-cleaning layer.


## Starting-inventory state

For ordinary bulk/divisible stock, an ingredient quantity is enough (for example 10,000 g rice or 40 g garlic).

For package-sensitive products, quantity alone can lose important information. For example:
- one sealed 160 g sweetcorn tin;
- 160 g of already-opened sweetcorn

have the same grams but different practical value.

`config/initial_inventory.csv` therefore supports an optional `product_id` and `stock_state`. The first implementation can use states such as:
- `bulk` — ordinary divisible stock;
- `sealed` — unopened retail pack(s);
- `opened` — already-opened remainder.

This same state representation should be carried from one planning cycle into the next where package state materially affects waste.
