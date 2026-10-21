# Problem definition

## Goal

Automatically choose a sensible set of meals and supermarket packs so that avoidable food waste and unnecessary spend are reduced, while useful inventory carries forward naturally.

The optimiser chooses only from a **pre-approved recipe library**. Meal acceptability therefore comes primarily from which recipes are allowed into the candidate set rather than from an artificial taste score.

## Current v1 scope

- 2-person dinners;
- 10 household-cleaned recipes derived from real Gousto recipes;
- chicken-focused, no fish;
- real Tesco UK pack/price snapshot;
- household starting inventory;
- flexible recipe quantities;
- no nutrition optimisation;
- no live Tesco basket integration;
- no probabilistic shelf-life model yet.

## Decisions

### 1. Recipe selection

The model chooses meals automatically from the approved candidate recipes.

Simple variety constraints can be added where useful, such as preventing exact recipe repetition in the same planning window.

### 2. Recipe quantity

Household-cleaned recipe quantities are the preferred quantities. The original Gousto quantities are retained separately as source data, but the optimiser operates on the cleaned household layer.

The first model uses:

| Class | Minimum | Preferred | Maximum |
|---|---:|---:|---:|
| fixed | 100% | 100% | 100% |
| tight | 90% | 100% | 110% |
| moderate | 80% | 100% | 120% |
| wide | 70% | 100% | 130% |

These are modelling assumptions, not food-science facts. They must later be sensitivity-tested and can be overridden for specific ingredients/recipes.

Current default assignment:
- spices and stock: fixed;
- starches, sauces and pantry items: tight;
- protein and dairy: moderate;
- vegetables and fresh aromatics: wide.

### 3. Retail package selection

The model chooses among whole fixed packs and, where Tesco sells produce by weight, variable-weight options.

A larger pack may be preferred when its lower unit cost and future usefulness outweigh the extra inventory.

### 4. Inventory

Every canonical ingredient may have starting inventory.

Conceptually:

`ending inventory = starting inventory + purchases - consumption`

Usable ending inventory becomes starting inventory for the next planning cycle.

The first household scenario starts with 10 kg long-grain rice. That is configuration, not a universal assumption.

### 5. Usable package quantity

Where labelled pack weight materially differs from edible supply, the model uses an effective usable quantity.

Example: a can may be labelled 325 g but provide about 260 g drained sweetcorn. The optimiser should treat the purchase as 260 g of usable sweetcorn while retaining the labelled pack size as source metadata.

No open/sealed package-state tracking is included in v1.

## Inventory policies

### Assumed-on-hand staples

Some household staples may start with a large inventory and therefore not trigger a purchase in the current planning cycle.

### Durable tracked inventory

Spices, dry goods and long-lived sauces remain inventory across planning cycles rather than being treated as weekly waste.

### Fresh tracked inventory

Meat, dairy, vegetables and herbs are tracked as ordinary inventory. Shelf-life/spoilage penalties will be added in a later stage rather than guessed in the first deterministic model.

## Quantity units

The model uses units that make recipe demand and retail supply comparable:

- divisible solids: usually grams;
- liquids: usually millilitres;
- count measures from source recipes are converted using ingredient-specific parameters where needed.

The cleaned optimiser layer is already expressed in canonical model units. `data/unit_conversions.csv` documents the conversions used to interpret the preserved source recipes.

## Objective

The first deterministic prototype objective is **shopping expenditure + a provisional fresh-surplus risk penalty + a penalty for reducing preferred recipe quantities**. It is implemented in `scripts/optimise_week.py` with PuLP and CBC. Fresh-surplus risk is estimated as 50% of the cheapest mapped unit price multiplied by ending inventory for short-shelf-life ingredients; **this is not observed food waste, an expiry forecast, or a validated spoilage probability**. Durable inventory has no waste penalty. The relative quantity shortfall penalty defaults to 2 per ingredient when an ingredient is reduced by 100% of its preferred amount, scaled proportionally. These arbitrary coefficients require sensitivity analysis.

Run `pip install pulp` then `python scripts/optimise_week.py --days 7` from the repository root. The solver selects seven distinct two-person dinners, buys integer multiples of listed product quantities and carries unused inventory forward. The `--fresh-penalty` and `--deviation-penalty` flags adjust assumptions.

**Limitations:** Tesco prices are a dated snapshot, not live checkout quotes; loose produce is approximated as integer multiples of its reference weight; recipes lack an audited full pantry-ingredient/cooking-method layer; expiry is not tracked; product mapping compatibility is provisional for some rows; no meal scheduling or 90-day simulation is included. Results require a successful execution and manual plausibility review before use as a real shopping list.

## Later simulation

After the deterministic optimiser works, simulation can test questions such as:

- which shopping horizon performs best;
- when larger packs are worthwhile;
- how much flexible recipe quantity helps;
- how sensitive results are to uncertain conversions and shelf life;
- how plans behave when meals are skipped or the household eats out.

Those are later experiments, not requirements for the first solver.


## Recipe cleansing boundary

Recipe design is deliberately separated from optimisation.

Before a recipe enters the candidate library, it is converted from the meal-kit source into a normal household version. This is where we remove or substitute meal-kit artefacts, correct implausible portions and add ordinary ingredients when they genuinely improve the dish.

The optimiser does **not** get permission to remove an ingredient simply because it is expensive or inconvenient. It chooses among the already-cleaned recipes and, separately, may adjust quantities only within the explicit flexibility rules.
