# Recipe catalogue and optimisation

The sole recipe collection is `data/recipes.csv`. A recipe is only admitted when its two-person ingredient list and independently written cooking instructions exist. Source URLs are optional attribution/reference, not separate source records.

`data/recipe_ingredients.csv` stores canonical, model-unit ingredient quantities for the recipes that can be optimised. `data/ingredients.csv` defines ingredients, and `data/products.csv` holds Tesco pack/pricing snapshots. These are relational supporting tables, not additional recipe catalogues.

The collection currently has 40 recipes: ten with canonical model ingredient rows and thirty with ingredient quantities in `recipes.csv` pending normalisation to `recipe_ingredients.csv`. The 17 prior name-only candidates were removed because they had no ingredient list. The optimiser currently selects only the ten model-ready recipes. Never add name-only entries or invent retail prices to activate recipes.

Diversity is constrained by protein and cooking method only where enough eligible options exist. Actual weekly shopping cost is distinct from estimated consumed-ingredient value. Opening stock is valued approximately, not at a documented acquisition cost.

## Next necessary work
Convert the thirty complete textual ingredient lists into canonical `recipe_ingredients.csv` rows, add missing Tesco mappings using verified products, and activate them. Obtain and independently rewrite complete instructions for the ten original recipes that still lack instructions. Run validation and the optimiser and verify CI. Do not recreate candidate/source/household recipe files.
