# Data normalisation

## Why a canonical ingredient layer is necessary

Recipes and supermarkets describe the same food differently.

A recipe may say:

- `Chicken breast strips`
- `Large British chicken breast fillet`
- `Chicken breast portions`
- `Diced chicken breast`

Tesco may sell:

- 350 g chicken breast fillets
- 650 g chicken breast fillets
- 1 kg chicken breast fillets
- 1.6 kg chicken fillet packs

The optimiser needs one stable concept — for example `chicken_breast` — between those two layers.

The data model therefore separates:

1. **Source recipe ingredient** — the wording and quantity as published.
2. **Canonical ingredient** — the normalised food concept.
3. **Retail product** — a specific Tesco pack/SKU that can satisfy that ingredient.
4. **Unit conversion** — a transparent parameter converting source household measures to the model unit when necessary.

This separation prevents either recipe wording or a supermarket product name from becoming the definition of an ingredient.

## What the research paper did

Van Rooijen et al. (2024) used recipes from the Netherlands Nutrition Centre. To create a common ingredient vocabulary, the authors standardised recipe ingredients to **NEVO food codes**. They converted household measures such as tablespoons to grams using the Dutch RIVM portion-size database and converted food quantities to **edible weights**. Their final recipe database contained 263 dinners. Retail data then supplied net weight, package size and package price for each food item.

Reference: https://doi.org/10.1016/j.resconrec.2024.107559

## Our UK adaptation

We use the same core idea: retain the source measurement, map it to a canonical food, then convert only when the optimisation model requires a common unit.

### 1. Preserve source quantities

`recipe_ingredients.csv` keeps:

- `source_ingredient_name`
- `source_quantity`
- `source_unit`

These are the audit trail back to the recipe.

### 2. Map to a canonical ingredient ID

Examples:

- `Chicken breast strips` → `chicken_breast`
- `Chicken breast portions` → `chicken_breast`
- `White long grain rice` → `long_grain_rice`
- `Natural yoghurt` → `natural_yogurt`

Canonicalisation is about identity; conversion is handled separately.

### 3. Preferred model units

For the first model:

- most solid foods → **grams**;
- liquids sold/measured volumetrically → **millilitres**;
- count units remain only where count is genuinely the better representation.

This means recipe measures such as `1 onion`, `1 garlic clove`, `1 red pepper`, `2 carrots` and `1 noodle nest` can ultimately become grams even though the source recipe stays unchanged.

Why grams for produce? Because retail supply may come from either:
- a loose item;
- a weight-based loose purchase;
- a multipack;
- a fixed-weight bag.

A common mass unit lets those options compete in one stock balance.

### 4. Approximate conversions are allowed when the decision impact is low

Earlier versions of this project marked every non-exact household measure as unresolved. That is too strict.

We now distinguish **precision from materiality**.

Examples:
- a garlic clove can be represented by an average edible gram weight;
- an onion sold `each` can be represented by an average edible gram weight;
- half a teaspoon of turmeric can be converted using an ingredient-specific approximate weight;
- a noodle nest can be converted using the product/pack serving weight.

These values must still be documented in `data/unit_conversions.csv`, but they do not need false precision.

A 0.3 g spice error should not receive the same modelling effort as a 300 g chicken error.

### 5. Fresh aromatics

For the initial model:
- garlic → grams;
- fresh ginger → grams;
- onions → grams.

This allows partial use and inventory carryover naturally.

For example, the recipe may ask for one garlic clove, but the optimiser consumes the corresponding estimated grams from the garlic stock. Retail garlic can then be represented as a bulb/pack with an estimated usable gram quantity.

We do **not** need to force garlic inventory to remain an integer number of cloves after cooking. The physical cooking behaviour is continuous enough for this purpose.

### 6. Durable pantry ingredients

Spices and pantry ingredients should be tracked as persistent inventory rather than weekly leftovers.

Examples:
- turmeric;
- garam masala;
- paprika;
- dried oregano;
- cornflour.

A jar may be purchased once and then used over many planning cycles. Their small recipe measures are converted to grams/ml so stock can be decremented, but remaining stock is not penalised as weekly waste.

### 7. Staples can be assumed on hand

Some household staples do not need to participate in package-choice optimisation in the first experiment.

For the current household scenario, long-grain rice is treated as a bulk staple with a large starting inventory (for example 10 kg). Meals consume that stock, but the optimiser does not select a new rice package until a later model introduces reorder logic.

This prevents a cheap, long-lived staple from adding needless complexity to the first package-selection experiment.

### 8. Keep composite ingredients intact until a split is justified

The Harissa Chicken recipe supplies `Coriander & mint (10g)` as one combined quantity. It is currently represented as `fresh_herb_mix_coriander_mint`.

We should not arbitrarily call that 5 g coriander + 5 g mint.

### 9. Keep product form explicit

Two foods can be related without being identical.

Examples:

- red pepper vs a mixed-pepper pack;
- natural yoghurt vs Greek-style yoghurt;
- fresh chicken thigh fillet vs bone-in chicken thigh;
- generic soy sauce vs light/dark soy sauce;
- tomato paste vs tomato puree.

`products.csv` therefore includes a `product_form` and a `mapping_status`. Substitution should later be an explicit rule, not an accidental consequence of sharing a word.

### 10. Effective usable package quantity

The optimiser ultimately needs one number describing how much usable ingredient a retail purchase supplies.

For most products:

`effective usable quantity = pack quantity`

Only override this when the difference is material and known, for example a canned ingredient with a meaningful drained weight.

We do not need a complicated yield model for every food at the beginning.

### 11. Variable-weight products

Loose produce such as onions, carrots and courgettes can be treated as weight-based supply.

Later we can decide whether the optimiser sees this as:
- continuous grams at a price per kg;
- realistic discrete increments; or
- a bounded approximation around average item weights.

That choice belongs in the mathematical model, not in the source-data cleaning.

## Files

### `data/ingredients.csv`

One row per canonical ingredient.

### `data/recipe_ingredients.csv`

Many-to-many bridge between recipes and canonical ingredients. It retains the original recipe quantity.

### `data/products.csv`

Specific retail products mapped to canonical ingredients. Multiple products can map to the same ingredient, which creates the package-size choice.

### `data/unit_conversions.csv`

Documented conversion parameters between household source measures and canonical model units.

## Next normalisation work

Before the first optimiser is trustworthy, resolve the conversions that actually affect the seed recipes:

- chicken breast `piece` → usable grams;
- garlic `clove` → average edible grams;
- onion/pepper/carrot/courgette/sweet potato `each` → average edible grams;
- tsp/tbsp → ingredient-specific grams or ml;
- noodle nest → grams;
- retail `each` produce → effective grams where needed;
- material drained weight for canned food;
- product substitutions and acceptable forms;
- shelf-life/opened-life rules.

Each conversion should include its source, method and confidence rather than being hidden inside code.
