# Tesco mapping and staged-recipe coverage — 22 October 2026

This is a **working backlog**, not a claim that all mappings are complete. Seven staged recipe-ingredient batches (R041–R200) were compared with the active ingredient and product catalogues. Another conversation may be updating the repository concurrently, so **recompute before acting**.

## Corrections committed in this pass

- Cardamom is already modelled in grams. P233 Rajah Whole Green Cardamoms 50 g is listed online in the saved snapshot; P046 and P234 are marked out of stock. Active R008 uses 0.6 g for roughly three pods; staged R199 uses 1 g. Do not convert cardamom to each or assume 2–3 g per individual green pod.
- Courgette: P029 loose reference 200 g -> usable 1 each; P030 500 g -> estimated usable 2.5 each. Recipes may use half a courgette.
- Baking potato: ingredient unit changed to g, using an approximate 300 g per large whole potato. P239–P241 four-packs -> usable 1200 g; P242 loose -> usable 300 g. R021 and R034 -> 600 g for two whole jacket potatoes.
- Red chilli: ingredient and active/staged recipe rows converted from each to g, using a documented approximate 6 g per chilli, to match P076 Tesco Red Chillies 60 g.
- Staged spring onion entries using each were converted to grams at an approximate 15 g per spring onion (nine recipe rows).
- No product columns were removed. The deferred column-cleanup plan is in `docs/catalogue-cleanup-deferred.md`.

## Missing Tesco product coverage in staged recipes

**Many new staged ingredients do not have any mapped product in `data/products.csv`.** This is the primary remaining blocker for enabling all staged recipes. The following ingredients need product discovery, identity/pack/price/source verification, product-evidence rows and eligibility checks; do not fabricate Tesco SKU IDs or prices.

### More frequently used in staged recipes
chipotle_paste, green_pepper, burger_buns, lettuce, gnocchi, creme_fraiche, hard_cheese, chorizo, asparagus, leek, baby_corn, teriyaki_sauce, sesame_seeds, pork_mince, ketjap_manis, naan, turkey_mince, pesto, rocket, pumpkin_seeds, sausages, apple, chives, falafel, peanut_butter, peanuts, honey, bacon_lardons, balsamic_vinegar, butternut_squash, fresh_sage, pork_loin_steaks, savoy_cabbage, sea_bass, serrano_ham, butter_beans, ciabatta, shallot, turkey_steaks, mixed_beans, walnuts, pomegranate, yellow_pepper, fish_pie_mix, gochujang, sweet_chilli_sauce, avocado, hot_sauce, green_chilli, sun_dried_tomatoes, lasagne_sheets, thai_green_curry_paste, puff_pastry, black_bean_sauce, dried_apricots, jerk_seasoning, pineapple, instant_polenta, udon_noodles, orange, goats_cheese, giant_couscous, tamarind_paste, fresh_thyme, cannelloni_tubes, zaatar, jalfrezi_paste, fennel_seeds, garlic_paste, korma_paste, radishes, diced_beef, beansprouts, red_pesto, tahini, dried_thyme, fresh_rosemary.

**Potential ingredient-ID consolidation to check first:** `green_pepper` and `yellow_pepper` should likely use the already established `red_pepper` ID meaning *bell pepper of any colour*, rather than creating colour-specific Tesco product mappings. Confirm whether any recipes specifically require a colour before changing staged IDs.

**Availability exceptions:** `garlic_paste` has an existing mapped product P061 but it is marked out of stock in the saved snapshot. Find another verified eligible Tesco product rather than silently treating P061 as available.

## Follow-up steps

1. Re-run an actual CSV-aware audit of **active and all seven staged** recipe ingredients and Tesco products on the latest commit, including unit and availability checks.
2. Consolidate genuinely identical ingredient IDs without changing the intended recipe.
3. Find verified Tesco SKUs for each remaining ingredient; record pack and usable quantities, current price, URL, and evidence. Prefer multiple useful pack sizes.
4. Check for out-of-stock products and expired prices/offers using the target Tesco delivery area or slot; `listed_online` does **not** guarantee local delivery availability.
5. Run `scripts/validate_seed_data.py`, the repository tests, and `scripts/optimise_week.py` on a realistic two-person week. Record any failures and fix them before marking mapping complete.

**Status:** partially corrected; staged Tesco product coverage, live stock/price refresh, and full end-to-end validation remain outstanding.
