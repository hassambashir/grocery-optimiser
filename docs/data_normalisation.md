# Data normalisation and substitution policy

The authoritative optimiser inputs are `recipes.csv`, `recipe_ingredients.csv`, `ingredients.csv` and `products.csv`. Recipe notes are regenerated from the structured quantities so they do not request whole cucumbers or liquid stock while the model uses halves and dry cubes. The removed historical source CSVs are not claimed to be present.

## Units

- Grams for divisible solids and millilitres for liquids, including single/soured cream and canned coconut milk.
- Stock demand is 0.5 or 1 dry cube. Retail gross mass remains 100 g, with usable quantity 10 cubes. Water belongs in cooking instructions.
- Cucumber demand is 0.5 each; purchases are whole cucumbers. Eggs are whole eggs.
- Aubergine and lemongrass recipes each use one whole item/stem, matching retail counts without inventing an edible gram yield.
- Jacket-potato recipes use two large `baking_potato` items. General `potatoes` are measured in grams for mash/roasting; larger roasting potatoes are cut to similar-sized pieces. Baby potatoes cannot satisfy a jacket-potato count.
- A household tablespoon is 15 ml and teaspoon 5 ml. Do not silently equate grams with millilitres for sauces.
- Existing source conversions are historical explanatory records, not automatically applied to already-normalised recipe quantities. Provisional conversions remain explicitly marked as such.

## Purchasing eligibility

The validator and optimiser call the same `exclusion_reason` function. A product requires Tesco identity, an exact product ID/URL, an approved mapping, `listed_online` snapshot status, a finite positive price and effective quantity, and a matching canonical unit. Unknown statuses, unapproved compatibility and substitution candidates are excluded. Having starting inventory never counts as complete catalogue coverage.

Approved mappings are `direct`, `direct_variable_weight`, `effective_usable_quantity` and `estimated_usable_weight`. The last two are not claims that physical yields are exact. Mixed-colour peppers remain excluded from a red-pepper-only requirement. An unused Italian-herb approximation remains unapproved.

## Interchangeability

Closed-cup/chestnut mushrooms, suitable egg pack sizes, plain chopped-tomato brands, suitable beef mince fat levels and dry starch pack sizes compete within their ingredient family. Fresh tomatoes, cherry tomatoes, chopped canned tomatoes, passata and puree remain separate. Dry noodles are not supplied by cooked noodles. Black beans are canned/drained, not dry beans. Garden peas are frozen. Raw peeled prawns are not cooked or shell-on prawns. Plain tofu is not silken, smoked or flavoured tofu. Thin-cut beef can be sliced into strips before cooking.

Whole flatbreads are ordinary meal-sized breads. Tiny 35 g folded flatbreads were not treated as equivalent to a full meal-sized bread. Bay leaves have a verified 10-leaf retail pack, avoiding a guessed leaves-per-gram conversion.

## Pack and usable quantities

`pack_quantity` describes the bought pack in `pack_unit`. `usable_quantity` and `usable_unit`, when both populated, override it for supply. Gross and drained masses are retained separately: a 145 g tuna can supplies 102 g drained, and four cans supply 408 g; Tesco black beans supply 235 g per 400 g can; Tesco lentils supply 235 g per 390 g can. No double draining or cooked-to-dry conversion is applied.

Count-labelled egg/bread packs use counts directly. Loose produce is bought in integer reference portions; actual weights/charges vary. Weighted onion bags retain disclosed estimated counts. Garlic bulb packs retain the inherited conservative estimate of 24 g edible garlic per bulb; this is not a verified Tesco net weight. These approximations are surfaced in basket output and must be checked against the actual produce.

## Tesco label discrepancy

Listing 279695475 names a 220 g salmon pack and displays Pack size 220 g; GBP 4.90 / GBP 22.27 per kg also implies 220 g. Its Net Contents section says 260 g. The catalogue uses the conservative, multiply-supported 220 g, preserves both observations in evidence, and documents the conflict in product notes. Other verified salmon packs remain alternatives.

## Snapshot evidence and offers

`product_evidence.csv` records factual observations and canonical Tesco URLs, checked 21 October 2026. Pages can change by retrieval, location and delivery slot. Stock states are snapshots, not delivery guarantees. Expired single-product Clubcard prices were cleared; current offers are retained. Conditional multibuys remain textual and are not applied as unconditional prices. The offline validator verifies integrity and agreement with stored evidence; it does not claim to re-fetch live Tesco stock.
