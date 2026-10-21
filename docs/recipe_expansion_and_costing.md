# Recipe expansion and consumption-cost reporting

## Recipe ownership and source policy
The repository is an independent household recipe collection, not a Gousto catalogue. Gousto and other sites are inspirations; adapted recipes use household names, servings, ingredients, and original instructions. Keep source links as optional provenance only, not as the recipe identity. Original household recipes require no external source. Do not reproduce copyrighted recipe instructions verbatim: write independently phrased, cookable steps grounded in the actual ingredient quantities and methods. Each ready recipe must be self-contained, with equipment, preparation, cooking sequence, heat/oven temperature where relevant, approximate times, and food-safety cues. A recipe may remain in the catalogue as draft until ingredients and instructions are complete.

## Candidate staging
`data/recipe_candidates.csv` contains source-linked candidate recipes, not model-ready recipes. The current optimiser reads only `data/recipes.csv` and `data/recipe_ingredients.csv`. Candidates must not be added to either until the complete two-serving ingredient list has been checked against the source, converted into canonical ingredients, and every ingredient has a feasible Tesco product or explicit household inventory.

Preserve the source URL, original recipe name, cuisine, and source quantities. Record every household substitution separately. Never silently replace a branded sauce, stock mix, paste, or rice type. For ingredients with no ordinary retail equivalent, hold the recipe out until a justified adaptation is documented.

## Useful variety dimensions
- `main_protein`: chicken, beef, lamb, paneer, fish, legumes, etc.
- `cooking_method`: oven_bake, oven_roast, pan_fry, stir_fry, grill, pan_curry, oven_stew, etc.
- `primary_side`: basmati_rice, jasmine_rice, potato_mash, baby_potatoes, sweet_potato, noodles, pitta, etc.
- `vegetable_side`: slaw, greens, salad, peas, beans, etc.
- `cuisine`: source label; not sufficient by itself for variety.

Avoid enforcing hard weekly diversity constraints before enough feasible recipes are available. First report variety; then introduce configurable limits or soft penalties, with transparent trade-offs.

## Rice policy proposal (not yet implemented)
Standardise ordinary household rice purchases to basmati and jasmine where the cooking method permits. Do not silently convert risotto/arborio, brown rice, or specialist sticky rice to either; these are materially different preparations. Mark any rice adaptation as such and review its recipe method. Existing initial long-grain rice stock needs an explicit transition decision.

## Two distinct weekly cost measures
1. **Cash outlay**: sum of full Tesco pack prices purchased this week, currently printed as `Shopping cost`.
2. **Ingredient consumption value**: value of the actual ingredient quantities consumed in the seven meals, including ingredients drawn from opening inventory. This is an accounting estimate, not cash spent this week.

To calculate consumption value consistently, store a cost basis for opening inventory and assign a unit cost to purchases. For each ingredient, reconcile opening quantity + purchased quantity = consumed quantity + closing quantity, and separately reconcile the monetary values. Choose and document a costing method such as weighted-average cost; use a clear estimate flag when opening-stock acquisition cost is unknown. Never equate leftover pack value with food waste.

Report both cash outlay and consumption value, plus fresh-surplus risk, without adding these unlike measures together. Keep shopping optimisation based on cash outlay and separately documented risk/deviation weights.
