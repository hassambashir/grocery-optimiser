# Problem definition

## User problem

A normal meal-planning app often asks the user to choose recipes first and then totals the ingredients. This project starts one level earlier: the system should choose a sensible mix of meals itself and make those choices jointly with supermarket package decisions.

The practical goal is:

> Automatically choose a good sequence of meals and a sensible basket so that short-life food is rarely discarded, larger packs are used when they are genuinely economical, and durable leftovers can carry forward naturally.

## Decisions the model should eventually make

1. **Recipe selection**
   - Select meals automatically from a candidate recipe library.
   - Avoid an obviously repetitive week.
   - Allow variety rules to be modelled separately from waste/cost.

2. **Recipe quantity**
   - A recipe ingredient need not always be a single rigid number.
   - Each ingredient can later have `minimum`, `preferred`, and `maximum` usable quantities.
   - Example: a nominal 150 g yoghurt requirement might tolerate 120–170 g, while a baking ingredient may have a much tighter range.

3. **Retail package selection**
   - Choose whole retail packs where the product is sold as a fixed pack.
   - Allow variable-weight products where the retailer sells loose produce.
   - Do not assume the smallest pack is best: a larger pack may have a lower unit price and may be useful in later meals.

4. **Inventory and carryover**
   - Track what remains after each meal.
   - Remaining stock should not automatically be called waste.
   - Carry stock into later planning cycles when it is still usable.
   - Distinguish package quantity from usable quantity where required (for example drained tins).

5. **Rolling planning**
   - Do not hard-code “exactly seven days” as the universal optimal shopping cycle.
   - The system may commit to the next shopping period while looking further ahead to estimate the value of leftovers.
   - Re-optimise as time passes and stock/real life changes.

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

The shopping interval itself is therefore a candidate experimental variable, not a fixed truth.

## Initial scope

For the first implementation:

- 2-person dinners;
- 10 real Gousto recipes;
- chicken-focused, no fish;
- real Tesco UK package/price snapshot;
- published recipe quantities retained exactly where possible;
- home pantry basics such as salt, cooking oil and water excluded from the first basket model;
- no nutrition optimisation yet;
- no live Tesco integration yet.

The purpose of this scope is to get a small real model working before adding more recipes, nutrients, live product data, stochastic behaviour, or an interface.
