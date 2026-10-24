# Research roadmap — normalised multi-objective grocery optimisation

**Status:** Proposed research and implementation plan (24 October 2026). No experiment results or performance claims are implied by this document.

## Research question

Can a mixed-integer linear programming (MILP) model jointly choose household meals and integer supermarket retail packs while balancing actual checkout expenditure, surplus risk, meal variety and household preferences?

**Primary short-term outcome:** A reproducible, technically credible case study suitable for a LinkedIn research/engineering post, followed by a small opt-in browser-based household pilot. A subscription product, 28-day solver, nutrition targets and multi-retailer support are not prerequisites.

## Existing model: baseline, not the final formulation

The current `scripts/optimise_week.py` minimises actual pack purchase expenditure plus a short-shelf-life ending-stock *proxy* penalty, preferred-quantity deviation and optional product penalties. It enforces integer pack purchasing, ingredient inventory balance, unique recipes in the weekly plan and conditional main-protein/cooking-method diversity caps. **It does not measure realised food waste.** Preserve this implementation as a benchmark.

See `README.md`, `docs/application.md`, and `runs/README.md`. The recorded two-week simulation is not measured household savings, and a cheaper second-week basket with opening inventory is not proof of superiority over a fair alternative.

## Target formulation

For feasible weekly decisions `x`, minimise

```text
Z(x) = wC * C_norm(x)
     + wS * S_norm(x)
     + wV * V_norm(x)
     + wP * P_norm(x)
     + wQ * Q_norm(x)
```

where:
- **C:** actual checkout expenditure for integer packs; report in GBP and apply any weekly budget to actual expenditure, never a discounted/effective-cost proxy.
- **S:** explicitly defined surplus/waste-risk measure; distinguish short-life leftovers, useful shelf-stable inventory, and *observed* food waste. Do not label an ending-stock proxy as measured waste.
- **V:** measurable concentration/repetition across recipes, main proteins, side/starch types and cuisine or cooking methods, subject to available, validated recipe tags.
- **P:** household preference dissatisfaction; `Never Again` is a hard recipe exclusion, while Like/Dislike can be modelled as graded preferences.
- **Q:** deviation from recipe-preferred quantities; ensure units and portion bounds are consistent.

Normalised terms must have documented, defensible reference bounds or scales. The weights (e.g. nonnegative and summing to 1) must be calibrated and tested, not treated as objectively correct. Normalisation alone does not improve optimisation quality. Preserve linear or MILP-representable terms; avoid introducing nonlinear expressions without a justified linearisation.

### Non-negotiable constraints and design decisions

- Medical/allergen exclusions are hard feasibility filters, never compensated by objective weights. Verify complete end-to-end gluten-free alternatives and ingredient/product mappings before claiming dietary safety.
- Respect real retail pack quantities, actual purchase prices, household portions and inventory conservation.
- Distinguish a household's willingness to stock up from unit-price minimisation: buying a 10 kg pack is not automatically cheaper in **checkout pounds** than buying a 500 g pack. If future-use value is included, bound it using credible demand/storage assumptions and report it separately from checkout expenditure.
- Do not assume skipped meals were cooked or ingredients consumed. Rolling 28-day repetition should use dated history when it is eventually implemented.
- Existing within-week diversity caps are hard constraints, not an existing composite variety score.
- A full 28-day purchase plan requires time-indexed purchasing/inventory and expiry assumptions; it is a separate future research phase.

## Implementation work packages

### WP1 — Define and validate metrics
1. Specify exact C, S, V, P and Q equations, units, domains and metadata needs.
2. Audit recipe protein, cooking method, side/starch and cuisine tags for completeness and consistency.
3. Decide how zero-stock/free one-off planning versus persistent-inventory households value surplus.
4. Define practical feasibility rules, edge cases, and sensible default weights.

**Exit criterion:** Each term is independently computable from model outputs, interpretable, and unit-tested.

### WP2 — Implement configurable normalised MILP
1. Retain the original solver as a reproducible baseline.
2. Implement the new terms and defensible normalisation; keep hard constraints separate.
3. Make weights and household settings configurable without asking users to manually tune coefficients.
4. Record solver status, objective components, actual basket cost, end inventory and runtime.

**Exit criterion:** Reproducible optimal solutions on fixed test fixtures, with documented weights/scales.

### WP3 — Verify correctness
- Tests for integer retail packs, ingredient supply and balance, preferred-quantity bounds, eligibility and strict dietary exclusions.
- Check whether a changed weight alters the intended objective component, including adversarial examples.
- Check solver optimality status, reproducibility, metadata coverage and feasibility under tight budgets.
- Distinguish estimated surplus risk from realised waste; validate claimed savings against a fair baseline.

**Exit criterion:** Automated tests pass and model limitations are explicit.

### WP4 — Run comparative experiments
Hold the catalogue snapshot, household size, time horizon and hard constraints fixed where comparisons require it.

| Experiment | Optimisation setting | Main question |
| --- | --- | --- |
| E1 | Cost-only | What is the cheapest feasible weekly basket? |
| E2 | Cost + surplus | What does reducing surplus risk cost? |
| E3 | Cost + surplus + variety | What is the price of greater meal diversity? |
| E4 | Full normalised weighted objective | How do preferences and portion fidelity change the plan? |
| E5 | Weight/budget/household sensitivity | Are recommendations stable and defensible? |

Additionally compare the *existing unnormalised baseline* with the new formulation. For a fair independent-recipe-shopping benchmark, define identical requirements and measure the same checkout-price and quantity outcomes. Do not claim real-world household savings from simulation.

### WP5 — Pareto and sensitivity checks
- Sweep plausible weights and report actual (unnormalised) expenditure, surplus, variety, dissatisfaction and quantity deviation alongside weighted scores.
- Identify dominated solutions and consider epsilon-constraint benchmarks: weighted-sum scalarisation can miss non-supported Pareto-efficient solutions in integer models.
- Document infeasibility, trade-offs, solve times and the impact of reference scales.

### WP6 — Publish case study
Prepare four evidence-based visuals:
1. Model flow: recipe choices -> ingredient demand -> integer retail packs -> inventory/surplus -> shopping list.
2. Scenario comparison across E1–E5, using actual computed values.
3. Cost/variety/surplus trade-off plot with appropriate caveats.
4. One fully worked seven-dinner household plan with pack choices, checkout total and leftovers.

Write a concise LinkedIn research post and optional public methodology page. Cite relevant literature accurately (including van Rooijen et al., 2024, DOI: 10.1016/j.resconrec.2024.107559). Mention/tag Tesco, Gousto, researchers or tools only for verified contributions; do not imply collaboration, approval or endorsement. Review repository visibility, intellectual-property exposure, data rights and sensitive information before sharing links.

**Publication gate:** All numerical claims trace to saved, reproducible experiments; methodology, limitations, source snapshot and model version are clear.

## Later pilot and product work (not a blocker)
- Deploy the existing browser app securely with authentication, household isolation/RLS, consent and privacy controls.
- Invite a small number of households; measure usability, actual purchases, plan completion, recipe feedback and mismatch between predicted and observed outcomes.
- Explore persistent inventory, rolling monthly repetition, bulk-purchase preferences, and later nutrition and 28-day multi-period planning.
- Keep free/premium entitlements at the application layer; one solver can accept optional history, inventory and preference inputs.

## Immediate next step
**WP1: define and test each objective metric and its normalisation before implementing or publishing the full weighted objective.** Keep experimental results separate from plans and assumptions.
