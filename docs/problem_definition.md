# Problem definition

Choose seven distinct, approved two-person dinners and whole Tesco purchase units to balance affordability, variety and avoidable fresh surplus. There are 200 recipes spanning meat, fish and vegetarian dishes. Every recipe ingredient has a purchasing option; the solver cannot drop inconvenient ingredients.

## Decisions and accounting

Binary recipe variables choose exactly the requested number of dinners. Integer product variables buy retail packs/reference portions. Consumption stays within the configured recipe bounds, with whole eggs, half stock cubes and documented practical fractions of selected whole produce. Every ingredient obeys:

`ending inventory = opening inventory + usable purchased quantity - consumption`

All balances must be nonnegative. Unrelated starting inventory is preserved in the result. Inventory omitted from configuration starts at zero. The example 10 kg rice stock is configuration, not an unlimited free staple rule.

The solver compares all eligible alternatives jointly and can mix pack sizes. Gross can weight does not masquerade as edible supply. Unknown/out-of-stock listings and unapproved substitutions are excluded. A positive but insufficient inventory balance does not create supply: the model still has to satisfy exact quantity balances.

## Objective

Minimise regular-price shopping expenditure plus fresh-surplus proxy plus symmetric proportional quantity-deviation penalty. The default fresh penalty is 0.50 times the cheapest eligible unit value times ending stock for `short` ingredients. The deviation coefficient is 2.0 times absolute deviation divided by preferred quantity. Both directions are penalised to avoid free consumption inflation. Fixed quantities cannot move; tight/moderate/wide bounds are +/-10%, +/-20%, +/-30% respectively.

These coefficients and shelf-life classes are assumptions, not validated spoilage forecasts. Durable stock has no weekly surplus penalty and need not be consumed. Frozen/fresh alternatives currently share the ingredient-level shelf-life class, so their risk treatment is conservative; product-level expiry, opened containers and freezer allocation are not yet modelled.

Protein and cooking-method groups are capped at at most four of seven dinners, when that cap is feasible with the available recipe pool. There is no repeated recipe within a plan. This provides basic variety without claiming nutritional optimisation.

## Scope and evidence

The offline snapshot has been checked against Tesco UK product pages, with evidence stored per product. It is not a live checkout quote, and Northern Ireland slot availability is not verified. Loose produce and garlic/onion yields remain labelled planning estimates. The model returns seven dinner choices, not an expiry-aware cooking-day schedule.

Regression checks include every recipe individually, a seven-dinner solve, exact pack-choice fixtures, fractional consumption, available inventory, durable-stock carry-over and negative/malformed data. `docs/validation_report.md` records actual execution output. Future work can add expiry scheduling, nutrition constraints, live checkout refresh, Clubcard multibuys and a multiweek objective without weakening current data checks.
