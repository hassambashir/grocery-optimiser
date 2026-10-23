# Product catalogue schema cleanup — completed 23 October 2026

## Decision

The active catalogue no longer contains `mapping_status` or `package_type`. Neither field represented an independent optimiser decision:

- Canonical equivalence is expressed by `ingredient_id`.
- Effective supply is `usable_quantity`/`usable_unit` when present, otherwise `pack_quantity`/`pack_unit`.
- Availability, verified identity, positive price and unit compatibility determine eligibility.
- Every retail product is still purchased in an integer number of listing units.

Values such as `effective_usable_quantity` and `direct_variable_weight` duplicated quantity and pack fields. Candidate and substitution labels mixed unresolved research with active purchasing data.

## Candidate products

P071 (Italian herbs proposed for Mediterranean seasoning) and P278 (whole butternut squash without a defensible usable gram weight) were moved to `staging/product_candidates.csv`. They are preserved for research but cannot enter an optimisation.

The validator enforces that a candidate product ID cannot also appear in `data/products.csv`. Ingredient-to-ingredient substitution, when implemented, will use a separate substitution model rather than a product-row flag.

## Quantity transparency

Gross, net, drained and estimated usable quantities remain explicit through `pack_quantity`, `pack_unit`, `usable_quantity`, `usable_unit`, evidence and notes. The command-line output now gives a general planning notice because loose weights and estimated yields can differ at checkout; it does not infer uncertainty from a mapping label.

Historical Week 1 and Week 2 snapshots retain the former columns because they are immutable records of the schema used when those simulations were executed.
