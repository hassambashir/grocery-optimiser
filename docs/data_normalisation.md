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

## Recipe classification

`main_protein` is a controlled grouping used by the optimiser's variety constraint. Its permitted values are `chicken`, `turkey`, `pork`, `beef`, `lamb`, `fish`, `shrimp`, `tofu`, `cheese`, `legumes` and `vegetable`. Salmon, cod, tuna, sea bass and mixed fish use `fish`. Prawns use `shrimp`; the vague `seafood` label is not permitted. `vegetable` is used where a recipe has no distinct protein rather than mixing the dietary label `vegetarian` with ingredient groups.

`primary_side` describes the staple family rather than its spelling or shape. Permitted values are `rice`, `potato`, `sweet_potato`, `pasta`, `noodles`, `tortilla`, `bread`, `couscous`, `bulgur`, `legumes`, `vegetables`, `salad`, `pastry` and `polenta`. For example, brown rice is `rice`; spaghetti, orzo and gnocchi are grouped as `pasta`; and pitta, naan and flatbreads are grouped as `bread`. Sweet potato remains distinct from ordinary potato.

## Cooking-method quality

The structured ingredient rows are authoritative for shopping. Cooking instructions may be source-adapted or AI-composed, but they must stand on their own: use every listed ingredient, introduce no unlisted ingredient other than water, give a practical sequence and timings, and include safe doneness guidance where relevant. A source URL is optional provenance, not proof of quality and not a promotion requirement. AI-composed or materially simplified methods must say so in `ingredient_notes`; untested methods must not be described as kitchen-tested.

Methods are deliberately optimised for an ordinary two-person kitchen as well as for readability. Reuse a pan or tray when this does not contaminate cooked food, assemble toppings directly on the plate or wrap, and do not pre-mix two finishing ingredients in a separate bowl when applying them separately gives the same result. For example, mayonnaise can be spread onto a taco and chipotle dotted over it; the dataset should not require a bowl merely to name the combination “chipotle mayo”. Separate mixing remains appropriate when it materially affects coating, hydration, emulsification, marination, texture or food safety.

Prepared-component labels copied from meal-kit prose, such as “your garlic mayo”, are not acceptable unless the component and a genuinely necessary preparation step have already been explained. The staging validator rejects these unexplained labels and surfaces explicit bowl language for human review. It cannot determine culinary equivalence mechanically, so minimal equipment remains a review criterion rather than a blanket ban on bowls.

## Purchasing eligibility

The validator and optimiser call the same `exclusion_reason` function. The active catalogue has no mapping-status or package-type flags. A product is eligible when it has a verified Tesco identity and canonical `ingredient_id`, is `listed_online`, has a finite positive price and quantity, and its effective unit matches the ingredient's model unit. Effective supply is `usable_quantity`/`usable_unit` when present and otherwise `pack_quantity`/`pack_unit`. Having starting inventory never counts as complete catalogue coverage.

Alternative brands, pack sizes and varieties that genuinely supply the same canonical ingredient simply share its `ingredient_id`; they do not need a “direct” or “substitution” label. Products whose equivalence or usable quantity is unresolved remain outside the active catalogue in `staging/product_candidates.csv`. Future ingredient-to-ingredient substitution rules belong in a separate substitution model rather than in product rows.

## Interchangeability

Closed-cup/chestnut mushrooms, suitable egg pack sizes, plain chopped-tomato brands, suitable beef mince fat levels and dry starch pack sizes compete within their ingredient family. Fresh tomatoes, cherry tomatoes, chopped canned tomatoes, passata and puree remain separate. Dry noodles are not supplied by cooked noodles. Black beans are canned/drained, not dry beans. Garden peas are frozen. Raw peeled prawns are not cooked or shell-on prawns. Plain tofu is not silken, smoked or flavoured tofu. Thin-cut beef can be sliced into strips before cooking.

Whole flatbreads are ordinary meal-sized breads. Tiny 35 g folded flatbreads were not treated as equivalent to a full meal-sized bread. Bay leaves have a verified 10-leaf retail pack, avoiding a guessed leaves-per-gram conversion.

## Composite ingredients

Ingredients sold separately must remain separate canonical ingredients, recipe rows and product mappings. The former coriander-and-mint herb entry was removed: R010 now requests 5 g `fresh_coriander` and 5 g `fresh_mint`, and each maps to its own Tesco herb pack.

A limited allow-list covers mixtures that are themselves the purchased product: stock cubes, ginger-and-garlic paste, canned mixed beans and fish pie mix. These remain single ingredients because splitting them would make the optimiser buy several separate products instead of the one retail pack required by the recipe. The validators reject any new combined ingredient unless it is added deliberately to this documented retail-composite allow-list and has a resolved Tesco product identity.

## Pack and usable quantities

`pack_quantity` describes the bought retail unit in `pack_unit`. `usable_quantity` and `usable_unit`, when both populated, override it for supply. No package-type flag is required. Gross and drained masses are retained separately: a 145 g tuna can supplies 102 g drained, and four cans supply 408 g; Tesco black beans supply 235 g per 400 g can; Tesco lentils supply 235 g per 390 g can. No double draining or cooked-to-dry conversion is applied.

Count-labelled egg/bread packs use counts directly. Loose produce is bought in integer reference portions; actual weights/charges vary. Weighted onion bags retain disclosed estimated counts. Garlic bulb packs retain the inherited conservative estimate of 24 g edible garlic per bulb; this is not a verified Tesco net weight. These approximations are surfaced in basket output and must be checked against the actual produce.

## Tesco label discrepancy

Listing 279695475 names a 220 g salmon pack and displays Pack size 220 g; GBP 4.90 / GBP 22.27 per kg also implies 220 g. Its Net Contents section says 260 g. The catalogue uses the conservative, multiply-supported 220 g, preserves both observations in evidence, and documents the conflict in product notes. Other verified salmon packs remain alternatives.

## Snapshot evidence and offers

`product_evidence.csv` records factual observations and canonical Tesco URLs, checked 21 October 2026. Pages can change by retrieval, location and delivery slot. Stock states are snapshots, not delivery guarantees. Expired single-product Clubcard prices were cleared; current offers are retained. Conditional multibuys remain textual and are not applied as unconditional prices. The offline validator verifies integrity and agreement with stored evidence; it does not claim to re-fetch live Tesco stock.
