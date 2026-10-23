# Tesco mapping and staged-recipe coverage — 22 October 2026

This is a **working backlog**, not a claim that all mappings are complete. Seven staged recipe-ingredient batches (R041–R200) were compared with the active ingredient and product catalogues. Another conversation may be updating the repository concurrently, so **recompute before acting**.

> **Closed on 23 October 2026:** this document is retained as historical research notes. The live validators now report zero active or staged purchasing gaps. See [the current staged validation report](staging_validation_report.md) and [generated catalogue coverage](catalogue_coverage.md); do not use the older counts below as current status.

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

**Confirmed pepper modelling decision (23 October):** Keep `red_pepper`, `green_pepper` and `yellow_pepper` as separate ingredient IDs. Single-colour peppers map directly to their own IDs. Mixed-colour multipacks may be substitutions for colour-specific peppers, but only with explicit allocation constraints preventing the same purchased pack from being counted more than once. Do not merge these ingredient IDs.

**Availability exceptions:** `garlic_paste` has an existing mapped product P061 but it is marked out of stock in the saved snapshot. Find another verified eligible Tesco product rather than silently treating P061 as available.

## Follow-up steps

1. Re-run an actual CSV-aware audit of **active and all seven staged** recipe ingredients and Tesco products on the latest commit, including unit and availability checks.
2. Consolidate genuinely identical ingredient IDs without changing the intended recipe.
3. Find verified Tesco SKUs for each remaining ingredient; record pack and usable quantities, current price, URL, and evidence. Prefer multiple useful pack sizes.
4. Check for out-of-stock products and expired prices/offers using the target Tesco delivery area or slot; `listed_online` does **not** guarantee local delivery availability.
5. Run `scripts/validate_seed_data.py`, the repository tests, and `scripts/optimise_week.py` on a realistic two-person week. Record any failures and fix them before marking mapping complete.

**Status:** partially corrected; staged Tesco product coverage, live stock/price refresh, and full end-to-end validation remain outstanding.

## Reconciled audit — 23 October 2026

The latest `data/products.csv` contains 310 product rows and no repeated Tesco retailer product IDs. All seven staged ingredient batches and the active ingredient catalogue were compared against the product catalogue by exact ingredient ID. This is an **identity-level audit**, not an end-to-end optimiser test.

### Nine ingredient IDs still without any exact Tesco product row

`fresh_herb_mix_coriander_mint`, `savoy_cabbage`, `shallot`, `hot_sauce`, `instant_polenta`, `zaatar`, `jalfrezi_paste`, `korma_paste`, `dried_thyme`.

These nine must **not** be treated as resolved. Tesco listings exist for several of these ingredient types, but exact Tesco SKU IDs and corresponding verified pack/price combinations have not been established in this pass. A combined coriander-and-mint product must not be fabricated: it may need two separately priced Tesco products and recipe ingredient rows split into the canonical herb IDs. Similarly a Savoy cabbage sold each must not be assigned a fictional weight without an explicit estimate.

### Eleven ingredient IDs have product rows but no listed-online unit-compatible SKU

`garlic_paste`, `pumpkin_seeds`, `baby_corn`, `dried_apricots`, `ketjap_manis`, `cannelloni_tubes`, `giant_couscous`, `fennel_seeds`, `tamarind_paste`, `green_chilli`, `mixed_beans`.

Their mapped products are recorded as out of stock. These are not purchasable candidates until a live alternative is verified. The `butternut_squash` product is sold each while the ingredient model uses grams; correct with a documented estimated edible weight or a weight-sold SKU before optimiser use.

### Pepper allocation

`red_pepper`, `green_pepper`, `yellow_pepper` are distinct ingredients. The existing P016–P018 mixed pepper packs are currently attached to `red_pepper`. They are **not yet implemented** as shared multi-colour allocations. The optimiser must use one purchased mixed pack and assign its actual colour counts across recipes without double counting; do not duplicate the SKU under each ingredient ID.

### Verification limitations

Tesco stock is postcode and slot dependent. `listed_online` is not a guarantee of availability in the intended Northern Ireland delivery slot. Earlier catalogue records and price snapshots require refresh before checkout. The optimiser and recipe-to-product end-to-end validator were not run as part of this audit.

## Further verified Tesco matches — 23 October (latest)

Added P312 Tropical Sun Jamaican Hot Pepper Sauce 85 ml at GBP 0.80, P313 Pataks Indian Korma Curry Paste 283 g at GBP 3.35 (GBP 2.60 Clubcard), P314 Pataks Indian Jalfrezi Curry Paste 283 g at GBP 3.35 (GBP 2.60 Clubcard), and P315 Tesco Savoy Cabbage each at GBP 0.77 with an explicitly estimated 600 g usable weight. Korma page has conflicting pack-size text (title 283 g; description/net contents 290 g); check the label before optimisation. Clubcard offer ends 26 October 2026.

**Five unmapped ingredient IDs remain:** `fresh_herb_mix_coriander_mint`, `shallot`, `instant_polenta`, `zaatar`, `dried_thyme`. Tesco search for polenta returned no eligible dry instant polenta groceries, only ready-made out-of-stock polenta and unrelated products. Do not substitute ready-made polenta for instant dry polenta. Coriander-and-mint mix likely requires a two-ingredient recipe split and separate eligible Tesco herb products. No exact SKU, pack, and price combination was established for the other three during this pass.

**Not complete:** stock/availability blockers, pepper mixed-pack allocation, and optimiser end-to-end testing remain unresolved.
