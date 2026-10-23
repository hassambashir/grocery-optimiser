# Recipe catalogue and optimisation

The authoritative recipe collection is `data/recipes.csv`. It contains 200 two-person dinners. Every recipe has a structured ingredient list in `data/recipe_ingredients.csv`, a complete household cooking method, controlled protein/method/side classifications and eligible Tesco purchasing coverage.

`data/ingredients.csv` defines 209 canonical ingredients and their optimiser units. The 200 recipes use 205 of them. `data/products.csv` contains the Tesco pack and price snapshot; purchasing eligibility follows verified Tesco identity, availability, positive price and a usable quantity in the canonical ingredient unit.

The former batches R041–R200 were promoted only after the following gates passed:

- unique recipe IDs and normalised names;
- no probable duplicate pair based on both name similarity and ingredient overlap;
- valid canonical ingredient references and units;
- complete eligible Tesco coverage;
- method-length and prepared-component checks;
- all 200 recipes solved individually;
- a proven-optimal seven-dinner solve across the complete catalogue.

Source URLs are optional provenance rather than an activation requirement. A missing URL does not make a complete household adaptation unusable, but it remains visible in the catalogue audit. Ratings are blank unless a numeric value from 0 to 5 was retained with the recipe.

Diversity is constrained by protein and cooking method when sufficient alternatives exist. Shopping expenditure remains distinct from estimated consumed-ingredient value. Opening stock is valued approximately, not at a documented acquisition cost.

Future recipe batches should be created outside the authoritative data files, checked with `scripts/validate_staging_data.py`, and promoted only after the active catalogue audit and complete test suite pass.
