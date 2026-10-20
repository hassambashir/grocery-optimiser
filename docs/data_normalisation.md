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

This separation also prevents a supermarket product name from becoming the definition of an ingredient.

## What the research paper did

Van Rooijen et al. (2024) used recipes from the Netherlands Nutrition Centre. To create a common ingredient vocabulary, the authors standardised recipe ingredients to **NEVO food codes**. They converted household measures such as tablespoons to grams using the Dutch RIVM portion-size database and converted food quantities to **edible weights**. Their final recipe database contained 263 dinners. Retail data then supplied net weight, package size and package price for each food item.

Reference: https://doi.org/10.1016/j.resconrec.2024.107559

## Our UK adaptation

We are using the same basic idea, but we are not pretending to have conversions that have not yet been justified.

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

Canonicalisation is about identity, not yet about quantity conversion.

### 3. Normalise only when conversion is exact

If Gousto gives `130 g`, the normalised value can safely be `130 g`.

If Gousto gives `15 ml`, the normalised value can safely be `15 ml`.

But if the recipe says:

- 1 red pepper
- 1 garlic clove
- 2 carrots
- 0.5 tsp turmeric
- 2 tbsp miso
- 2 noodle nests

we keep that source measure and mark it `needs_conversion`.

A later conversion table should provide evidence-backed average/usable weights or product-specific handling. It is better to carry an unresolved value than to invent precision.

### 4. Keep composite ingredients intact until a split is justified

The Harissa Chicken recipe supplies `Coriander & mint (10g)` as one combined quantity. It is currently represented as `fresh_herb_mix_coriander_mint`.

We should not arbitrarily call that 5 g coriander + 5 g mint.

### 5. Keep product form explicit

Two foods can be related without being identical.

Examples:

- red pepper vs a mixed-pepper pack;
- natural yoghurt vs Greek-style yoghurt;
- fresh chicken thigh fillet vs bone-in chicken thigh;
- generic soy sauce vs light/dark soy sauce;
- tomato paste vs tomato puree.

`products.csv` therefore includes a `product_form` and a `mapping_status`. Substitution should later be an explicit rule, not an accidental consequence of sharing a word.

### 6. Package quantity is not always usable quantity

A 200 g tin may contain less than 200 g of edible/drained ingredient. Tesco already displays some canned products using a drained-weight unit price.

The retail schema therefore contains both:

- `pack_quantity`
- `usable_quantity`

`usable_quantity` is left blank until verified when the exact yield is not known.

This distinction will also matter for bones, peels, trimming and cooked/raw yields.

### 7. Variable-weight products are different from fixed packs

Loose carrots, onions and courgettes are not ordinary integer package choices. Tesco allows a selected weight/quantity and the actual weight may vary.

They are marked `variable_weight` so the optimisation model can decide later whether to:
- model them continuously;
- model realistic discrete increments; or
- exclude loose produce from the first MILP.

That is a modelling decision, not a data-cleaning shortcut.

## Files

### `data/ingredients.csv`

One row per canonical ingredient.

### `data/recipe_ingredients.csv`

Many-to-many bridge between recipes and canonical ingredients. It retains the original recipe quantity.

### `data/products.csv`

Specific retail products mapped to canonical ingredients. Multiple products can map to the same ingredient, which is what creates the package-size choice.

## Next normalisation work

Before the first optimiser is trustworthy we should resolve, in a controlled way:

- counts → edible grams for common produce;
- chicken breast `piece` → usable weight;
- tsp/tbsp → grams or ml by ingredient;
- noodle nests → grams;
- exact drained weights for canned food;
- product substitutions and acceptable forms;
- shelf-life/opened-life rules;
- optional mapping to a UK food composition identifier such as CoFID if nutrition is later added.
