# Mathematical formulation — implementation-aligned (21 October 2026)

**Source:** `scripts/optimise_week.py` on `main`. This is a transcription of the implemented MILP, not a claim of a fresh solver run.

## Sets and parameters

- (R): eligible recipes; (I): ingredients; (P_i): eligible Tesco products supplying ingredient (i).
- (c_p): regular price of product (p); (q_p): usable canonical quantity per pack; (s_i): opening inventory.
- (a_{ir}): preferred ingredient quantity in recipe (r); (ell_i,h_i): minimum/maximum flexibility factors.
- (k_i=min_{pin P_i} c_p/q_p): cheapest listed unit price; (I_{short}): short-life ingredients.
- (alpha=0.50): fresh-surplus proxy weight; (eta=2.0): proportional deviation penalty; (d=7) dinners by default.

## Variables

(x_rin\{0,1\}): selected recipe; (y_pinmathbb Z_{ge0}): purchased packs; (u_{ir}ge0): consumed amount; (e_ige0): ending inventory; (delta_{ir}ge0): absolute deviation.

## Objective

[
min Z = sum_p c_p y_p
+alphasum_{iin I_{short}:P_i
eemptyset} k_i e_i
+etasum_{(i,r)}rac{delta_{ir}}{a_{ir}}.
]

This is **purchase expenditure + value-based fresh-surplus risk proxy + proportional two-sided deviation**. It is **not** actual food waste, and it is **not** consumed-ingredient cost.

## Constraints

[
sum_{rin R}x_r=d
]

[
ell_i a_{ir}x_rle u_{ir}le h_i a_{ir}x_rqquadorall(i,r)
]

[
e_i=s_i+sum_{pin P_i}q_p y_p-sum_r u_{ir}qquadorall i
]

[
delta_{ir}ge a_{ir}x_r-u_{ir},qquad
delta_{ir}ge u_{ir}-a_{ir}x_r
]

[
x_rin\{0,1\},quad y_pinmathbb Z_{ge0},quad u_{ir},e_i,delta_{ir}ge0.
]

For count-constrained ingredients, (u_{ir}=g_i n_{ir}) where (n_{ir}inmathbb Z_{ge0}) and (g_i) is the consumption step (e.g. 1 egg, 0.5 cucumber, 0.5 stock cube). For grams/ml, quantities are divisible.

For each feasible protein or cooking-method group (G), when (dge4):

[
sum_{rin G}x_rle max(2,lfloor(d+1)/2floor).
]

The code skips a group cap when insufficient eligible alternatives would make it infeasible. Explicitly required recipes have (x_r=1).

## Rolling inventory

Ending inventory can be exported and loaded into a **separate** next-week optimisation:

[
s_{i,t+1}leftarrow e_{i,t},
]

after checking and adjusting for actual consumption, spoilage and usable condition. This is **sequential single-week optimisation**, not a multiweek joint objective.

## Reporting and limitations

Actual cash basket cost is (sum_p c_p y_p). Estimated consumed-ingredient cost is calculated **after** optimisation using weighted-average unit valuation and estimated opening stock costs.

The repository's 21 October 2026 validation report records 40 recipes, 125 used ingredients, 240 Tesco listings, full eligible coverage, 15 passing tests and an optimal example with £39.88 basket cost and £23.99 estimated consumed value.

Not implemented: measured waste, expiry-aware stock ageing, joint multiweek optimisation, nutrition, day-by-day meal ordering, live Tesco checkout/slot stock, delivery fees or conditional multibuy optimisation.

**Sources:** [optimiser code](../scripts/optimise_week.py), [validation report](validation_report.md), [README](../README.md).