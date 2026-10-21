# Executed validation report — 21 October 2026

## Result

Completed catalogue coverage and local end-to-end validation against main baseline `107907c0ca7dd72a01cd1b568d8184269351acc4`.

40 recipes; 125 used ingredients (124 before separating baking potatoes); 133 canonical entries; 372 recipe-ingredient rows. 240 Tesco products (112 added), 222 eligible overall, 217 eligible for used ingredients, 92 additional eligible alternatives. All 125 used ingredients covered; zero coverage exceptions.

## What was corrected

- Rechecked all 128 existing product pages and researched every missing ingredient. Added alternative brands, counts, pack sizes and suitable varieties; retained 14 unavailable listings and four unapproved mappings as excluded audit rows.
- Refreshed prices, availability, names and current single-product Clubcard offers; conditional multibuys are recorded, not incorrectly applied. Added per-product evidence.
- Separated large baking potatoes from generic mash/roast potatoes; fixed coconut milk to ml; retained half cucumbers, whole eggs and half/full dry stock cubes. Used real counts for whole aubergines, fresh lemongrass stems and bay leaves instead of invented gram/count yields.
- Distinguished can gross/drained weights, including tuna 145 g net / 102 g drained and the 408 g drained multipack. Corrected salmon to supported 220 g despite conflicting 260 g Net Contents text.
- Added missing cooking butter and oil requirements, supplied eight blank household cooking methods, and regenerated recipe notes so they agree with quantities. Standardised tablespoons/teaspoons of oil to 15/5 ml.
- Corrected fresh-herb/vegetable and durable pantry shelf-life classifications. Kept existing garlic/onion yield approximations explicitly labelled.
- Replaced permissive validation with strict CSV, finite positive numbers, references, unique IDs, evidence/URL agreement, quantity checks and actual eligible-product coverage. Inventory cannot hide a catalogue gap.
- Shared product eligibility with the optimiser; unknown/out-of-stock/unapproved rows cannot enter the basket.
- Separated whole retail purchase units from half-unit kitchen consumption. Added symmetric quantity-deviation penalties and preserved unrelated starting inventory.
- Added JSON and next-inventory exports, required-recipe scenarios, independent post-solve balance checks, pinned solver dependency and automatic push/PR CI configuration.

## Actual validator output

```text
Seed-data validation PASSED
recipes: 40
used_ingredients: 125
canonical_ingredients: 133
recipe_ingredient_rows: 372
products: 240
eligible_products: 222
covered_ingredients: 125
missing: []
alternatives: 92
Excluded product rows: 18
Offline integrity/eligibility check; postcode-specific stock and future prices require checkout verification.
```

## Actual test output

```text
test_drain_and_inventory_corruption_fail (test_project.DataTests.test_drain_and_inventory_corruption_fail) ... ok
test_ids_references_urls_and_units_fail (test_project.DataTests.test_ids_references_urls_and_units_fail) ... ok
test_invalid_prices_and_quantities_fail (test_project.DataTests.test_invalid_prices_and_quantities_fail) ... ok
test_inventory_cannot_hide_missing_purchase_coverage (test_project.DataTests.test_inventory_cannot_hide_missing_purchase_coverage) ... ok
test_known_drained_quantities (test_project.DataTests.test_known_drained_quantities) ... ok
test_malformed_csv_fails (test_project.DataTests.test_malformed_csv_fails) ... ok
test_real_catalogue_complete (test_project.DataTests.test_real_catalogue_complete) ... ok
test_unsafe_statuses_excluded (test_project.DataTests.test_unsafe_statuses_excluded) ... ok
test_alternative_pack_mix_and_leftovers (test_project.OptimiserTests.test_alternative_pack_mix_and_leftovers) ... ok
test_each_of_all_40_recipes_is_feasible (test_project.OptimiserTests.test_each_of_all_40_recipes_is_feasible) ... ok
test_half_cucumber_half_cube_and_whole_eggs (test_project.OptimiserTests.test_half_cucumber_half_cube_and_whole_eggs) ... ok
test_inventory_is_used_and_unrelated_stock_retained (test_project.OptimiserTests.test_inventory_is_used_and_unrelated_stock_retained) ... ok
test_no_free_inflation_to_consume_durable_stock (test_project.OptimiserTests.test_no_free_inflation_to_consume_durable_stock) ... ok
test_second_week_carry_forward (test_project.OptimiserTests.test_second_week_carry_forward) ... ok
test_seven_day_real_plan (test_project.OptimiserTests.test_seven_day_real_plan) ... ok

----------------------------------------------------------------------
Ran 15 tests in 6.008s

OK
```

The 40-recipe feasibility check runs each recipe in a separate subtest. Pack-choice tests use a known exact optimum, demonstrate a mixed pack basket, and verify that inventory changes the optimum. Other tests exercise missing mappings, invalid numbers, duplicate IDs, units, malformed CSV, half counts, whole eggs, durable carry-over and unused inventory preservation.

## Seven-day optimiser output

Status: **Optimal**. Eligible recipes: **40/40**. Seven distinct dinners generated. Regular-price shopping spend: **GBP 39.88**, excluding delivery. Whole retail purchases only; quantity balances verified independently after solving.

```text
Eligible recipes: 40 of 40 (based on ingredient supply)
Selected two-person dinners (7):
  R011 Chicken fajita traybake
  R018 Beef cottage pie
  R021 Beef chilli with baked potatoes
  R027 Sweet potato and black bean enchiladas
  R029 Mushroom stroganoff
  R034 Tuna sweetcorn jacket potatoes
  R036 Lentil shepherd's pie

Tesco shopping basket (regular-price snapshot):
  1 x Tesco British Chicken Breast Fillets 350g | usable 350 g | GBP 2.67
  2 x Tesco Red Peppers Each | usable 2 each | GBP 1.40
  6 x Tesco Brown Onions Loose | usable 6 each | GBP 0.66
  3 x Tesco Carrots Loose | usable 480 g | GBP 0.33
  1 x Tesco Sweet Potatoes 1Kg | usable 1000 g | GBP 1.19
  1 x Tesco Naturally Sweet Sweetcorn 200G | usable 160 g | GBP 0.50
  1 x Tesco Tomato Puree 200G | usable 200 g | GBP 0.59
  1 x Tesco Beef Stock Cubes 10 Pack 100g | usable 10 cube | GBP 1.00
  1 x Tesco Mayonnaise 450Ml | usable 450 ml | GBP 0.86
  1 x Tesco Red Chillies 60G | usable 60 g | GBP 0.51
  1 x Tesco Smoked Paprika 48G | usable 48 g | GBP 1.00
  1 x Tesco Limes Each | usable 1 each | GBP 0.23
  1 x Tesco Vegetable Stock Cubes 10 Pack 100g | usable 10 cube | GBP 1.00
  1 x Tesco Whole Cucumber Each | usable 1 each | GBP 0.99
  1 x Tesco Closed Cup Mushrooms 400G | usable 400 g | GBP 1.29
  1 x Grower's Harvest Chopped Tomatoes 400G | usable 400 g | GBP 0.43
  1 x Tesco Tomato Passata 500G | usable 500 g | GBP 0.60
  1 x Tesco Red Kidney Beans In Water 400G | usable 240 g | GBP 0.39
  1 x Tesco Green Lentils In Water 390G | usable 235 g | GBP 0.45
  1 x Tesco British Soured Cream 150Ml | usable 150 ml | GBP 0.70
  1 x Tesco 10% Fat Beef Mince 500g | usable 500 g | GBP 5.60
  1 x Tesco Medium Cheddar 400G | usable 400 g | GBP 3.20
  1 x Tesco Plain White Tortilla Wraps 8 Pack | usable 8 each | GBP 1.40
  1 x Rajah Jeera Ground Cumin 100G | usable 100 g | GBP 1.50
  1 x Tesco Baby Potatoes 1Kg | usable 1000 g | GBP 0.99
  1 x Tesco Sweet Vine Ripened Tomatoes 255G | usable 255 g (about 3 items; size varies) | GBP 1.25
  1 x Tesco Pure Vegetable Oil 1L | usable 1000 ml | GBP 1.45
  1 x Tesco British Salted Block Butter 250G | usable 250 g | GBP 1.85
  1 x Stockwell & Co. Plain Flour 1.5Kg | usable 1500 g | GBP 0.70
  1 x Grower's Harvest Garden Peas 900G | usable 900 g | GBP 1.15
  1 x Tesco Black Beans 400G | usable 235 g | GBP 0.46
  1 x Tesco Medium Egg Noodles 250G | usable 250 g | GBP 0.95
  1 x Tesco Wholegrain Mustard 180G | usable 180 g | GBP 0.44
  2 x Tesco Tuna Chunks In Spring Water 145G | usable 204 g | GBP 1.30
  1 x Tesco Baking Potatoes 4 Pack | usable 4 each | GBP 0.85

Shopping cost: GBP 39.88
Planning estimates (actual produce weights/yields and charges vary):
  Tesco Brown Onions Loose
  Tesco Carrots Loose

Ingredient consumption and estimated value:
  baking_potato: 4.0 each | estimated GBP 0.85
  beef_mince: 500.0 g | estimated GBP 5.60
  beef_stock_mix: 0.5 cube | estimated GBP 0.05
  black_beans: 235.0 g | estimated GBP 0.46
  brown_onion: 6.0 each | estimated GBP 0.66
  butter: 40.0 g | estimated GBP 0.30
  carrot: 400.0 g | estimated GBP 0.28
  cheddar: 140.0 g | estimated GBP 1.12
  chicken_breast: 350.0 g | estimated GBP 2.67
  chopped_tomatoes: 400.0 g | estimated GBP 0.43
  cucumber: 0.5 each | estimated GBP 0.49
  egg_noodles: 180.0 g | estimated GBP 0.68
  ground_cumin: 6.0 g | estimated GBP 0.09
  kidney_beans: 240.0 g | estimated GBP 0.39
  lime: 1.0 each | estimated GBP 0.23
  mayonnaise: 60.0 ml | estimated GBP 0.11
  mushrooms: 350.0 g | estimated GBP 1.13
  mustard: 5.0 g | estimated GBP 0.01
  passata: 300.0 g | estimated GBP 0.36
  peas: 240.0 g | estimated GBP 0.31
  plain_flour: 8.0 g | estimated GBP 0.00
  potatoes: 900.0 g | estimated GBP 0.89
  red_chilli: 6.0 g | estimated GBP 0.05
  red_pepper: 2.0 each | estimated GBP 1.40
  smoked_paprika: 9.6 g | estimated GBP 0.20
  sour_cream: 150.0 ml | estimated GBP 0.70
  sweet_potato: 450.0 g | estimated GBP 0.54
  sweetcorn: 120.0 g | estimated GBP 0.38
  tinned_lentils: 235.0 g | estimated GBP 0.45
  tomato_puree: 32.0 g | estimated GBP 0.09
  tomatoes: 120.0 g | estimated GBP 0.59
  tortillas: 8.0 each | estimated GBP 1.40
  tuna: 145.0 g | estimated GBP 0.92
  vegetable_oil: 35.0 ml | estimated GBP 0.05
  vegetable_stock: 1.0 cube | estimated GBP 0.10
Estimated consumed-ingredient value (includes opening stock): GBP 23.99
VALUATION NOTE: Weighted-average cost; opening inventory valued at lowest snapshot retail unit price.
This is an estimate, not this week's cash spend or measured food waste.

Per-recipe ingredient quantities (preferred -> actual):
  R011 chicken_breast: 350.0 -> 350.0 g
  R011 red_pepper: 2.0 -> 2.0 each
  R011 brown_onion: 1.0 -> 1.0 each
  R011 tortillas: 4.0 -> 4.0 each
  R011 smoked_paprika: 2.4 -> 2.4 g
  R011 ground_cumin: 2.0 -> 2.0 g
  R011 lime: 1.0 -> 1.0 each
  R011 vegetable_oil: 15.0 -> 15.0 ml
  R018 beef_mince: 300.0 -> 260.0 g
  R018 potatoes: 450.0 -> 450.0 g
  R018 brown_onion: 1.0 -> 1.0 each
  R018 carrot: 200.0 -> 200.0 g
  R018 peas: 120.0 -> 120.0 g
  R018 tomato_puree: 16.0 -> 16.0 g
  R018 beef_stock_mix: 0.5 -> 0.5 cube
  R018 butter: 20.0 -> 20.0 g
  R021 beef_mince: 300.0 -> 240.0 g
  R021 baking_potato: 2.0 -> 2.0 each
  R021 brown_onion: 1.0 -> 1.0 each
  R021 kidney_beans: 240.0 -> 240.0 g
  R021 chopped_tomatoes: 400.0 -> 400.0 g
  R021 ground_cumin: 2.0 -> 2.0 g
  R021 smoked_paprika: 2.4 -> 2.4 g
  R021 red_chilli: 6.0 -> 6.0 g
  R027 sweet_potato: 450.0 -> 450.0 g
  R027 black_beans: 240.0 -> 235.0 g
  R027 tortillas: 4.0 -> 4.0 each
  R027 passata: 300.0 -> 300.0 g
  R027 cheddar: 100.0 -> 100.0 g
  R027 brown_onion: 1.0 -> 1.0 each
  R027 ground_cumin: 2.0 -> 2.0 g
  R027 smoked_paprika: 2.4 -> 2.4 g
  R027 vegetable_oil: 10.0 -> 10.0 ml
  R029 mushrooms: 350.0 -> 350.0 g
  R029 egg_noodles: 180.0 -> 180.0 g
  R029 brown_onion: 1.0 -> 1.0 each
  R029 sour_cream: 150.0 -> 150.0 ml
  R029 mustard: 5.0 -> 5.0 g
  R029 vegetable_stock: 0.5 -> 0.5 cube
  R029 smoked_paprika: 2.4 -> 2.4 g
  R029 plain_flour: 8.0 -> 8.0 g
  R029 vegetable_oil: 10.0 -> 10.0 ml
  R034 baking_potato: 2.0 -> 2.0 each
  R034 tuna: 145.0 -> 145.0 g
  R034 sweetcorn: 120.0 -> 120.0 g
  R034 mayonnaise: 60.0 -> 60.0 ml
  R034 cheddar: 40.0 -> 40.0 g
  R034 cucumber: 0.5 -> 0.5 each
  R034 tomatoes: 120.0 -> 120.0 g
  R036 tinned_lentils: 240.0 -> 235.0 g
  R036 potatoes: 450.0 -> 450.0 g
  R036 brown_onion: 1.0 -> 1.0 each
  R036 carrot: 200.0 -> 200.0 g
  R036 peas: 120.0 -> 120.0 g
  R036 vegetable_stock: 0.5 -> 0.5 cube
  R036 tomato_puree: 16.0 -> 16.0 g
  R036 butter: 20.0 -> 20.0 g
Fresh surplus risk proxy: GBP 0.72
Quantity deviation penalty: 0.75
Ending inventory (nonzero):
  beef_stock_mix: 9.5 cube
  butter: 210.0 g
  carrot: 80.0 g
  cheddar: 260.0 g
  cucumber: 0.5 each
  egg_noodles: 70.0 g
  ground_cumin: 94.0 g
  long_grain_rice: 10000.0 g
  mayonnaise: 390.0 ml
  mushrooms: 50.0 g
  mustard: 175.0 g
  passata: 200.0 g
  peas: 660.0 g
  plain_flour: 1492.0 g
  potatoes: 100.0 g
  red_chilli: 54.0 g
  smoked_paprika: 38.4 g
  sweet_potato: 550.0 g
  sweetcorn: 40.0 g
  tomato_puree: 168.0 g
  tomatoes: 135.0 g
  tuna: 59.0 g
  vegetable_oil: 965.0 ml
  vegetable_stock: 9.0 cube
```

## Remaining limitations

No unresolved ingredient purchasing gaps. This result is a verified public-catalogue snapshot and a tested deterministic optimiser, not a guarantee of stock for a particular Tesco delivery slot. Tesco prices and stock can change. Clubcard multibuys/delivery fees are not optimised. Loose produce charges and garlic/onion yields are estimates. Shelf-life is ingredient-level and does not track opened packs or freezer state. A set of seven dinners is produced, without expiry-aware day ordering or nutritional optimisation. Check carried fresh inventory before reusing it.

The salmon page conflict is documented and the supported lower 220 g quantity is used. Other verified salmon packs remain available.
