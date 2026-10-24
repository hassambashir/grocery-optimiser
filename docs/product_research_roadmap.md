# Grocery Optimiser — product and research roadmap

Updated: 24 October 2026. Planning document; priorities are proposals, not delivered features.

## Primary goals (in order)
1. Publish a credible LinkedIn research/engineering demonstration: explain the household meal-and-retail-pack MILP, verified data, modelling trade-offs, limitations, and measured benchmark results without disclosing private commercial implementation.
2. Conduct a small opt-in household pilot through a browser-based interface, capturing practical feedback and real-world discrepancies.
3. Develop a sustainable free/premium product only after usability and optimisation value are validated.

## Current baseline (verify before external claims)
See README.md, docs/application.md, and runs/README.md. The README describes 200 recipes, 355 Tesco listings, a weekly pack-and-recipe MILP, and a simulated two-week run. The app is locally implemented but not publicly deployed. Simulated cost differences are NOT measured savings or proof of superiority to an independent-shopping baseline.

## Feature backlog and indicative priority
Scores: user value and engineering effort, 1=low to 5=high; judgement estimates, not user research.

| Area / feature | Value | Effort | Stage |
| --- | ---: | ---: | --- |
| Accurate Tesco product/price/pack shopping list | 5 | 3 | Demo/pilot |
| Weekly budget and whole-pack optimisation | 5 | 4 | Demo/pilot |
| Ingredient sharing and reasonable surplus / bulk purchase behaviour | 5 | 4 | Demo/pilot |
| Verified dietary exclusions and gluten-free substitutions | 5 | 4 | Demo/pilot (verify end-to-end) |
| Weekly recipe/protein/method diversity | 4 | 2 | Demo/pilot |
| Cooking time and household size | 4 | 2 | Pilot |
| Household feedback (like/dislike/never again) | 4 | 3 | Pilot |
| Meal completion and real inventory carryover | 5 | 5 | Pilot / later refinement |
| Rolling 28-day recipe repetition | 4 | 3 | After history is reliable |
| Calories, protein, macro/micronutrient targets | 4 | 4 | Later; validated nutrition data required |
| 28-day planning with weekly purchasing | 3 | 5 | Later; multi-period MILP |
| Multi-supermarket comparison | 4 | 5 | Later |
| Premium accounts, billing and subscription entitlements | 3 | 4 | After pilot |
| Individual household member diets, storage and expiry models | 4 | 5 | Later |
| Exports, reminders, meal calendar, recipe feedback UX | 3 | 2 | Incremental |

## Recommended milestones

### A — Credible public demonstration (highest priority)
- Validate code, catalogue provenance, recipe feasibility and end-to-end gluten-free filtering.
- Execute reproducible baseline comparisons: same meals/requirements and prices; independent pack purchasing vs jointly optimised basket; report checkout spend, surplus quantities and assumptions.
- Create one clear visual: recipe selection -> ingredient demand -> integer pack choices -> inventory/surplus -> consolidated shopping list.
- Present real computed results with exact definitions; distinguish estimated fresh surplus risk from measured waste and simulations from real users.
- Prepare a concise LinkedIn post and optional public methodology page. Cite van Rooijen et al. (2024) accurately; do not imply endorsement from Tesco, Gousto, authors or data/tool providers.

### B — Small browser pilot
- Deploy the existing app to a secure test environment with working database, authentication, per-household data isolation and RLS.
- Start with a small invite-only group. Capture household settings, selected plan, actual purchases, skipped/cooked meals, practical recipe feedback and mismatches.
- Offer opt-in research feedback and explain data retention/privacy; do not publish identifiable household data.
- Measure plan completion, estimated vs actual basket cost, quantity errors, user-reported surplus and whether users would return.

### C — Product refinement and premium
- Keep one optimisation engine, with optional persisted inventory/history/preferences.
- Free: useful single-week plan, accurate full checkout cost, practical pack choices; no automatic ongoing household memory.
- Premium: persistent household profile, inventory, dated meal history, rolling repetition, adaptive planning; only later consider 28-day multi-period optimisation and billing.
- For bulk buying: distinguish checkout expenditure from unit-price savings and credible future-use value. Do not credit unverified future consumption.

## Modelling and architecture decisions to preserve
- Hard constraints for medical/allergen exclusions; no unsafe product admitted through a soft penalty.
- Budget uses actual pack expenditure, not future-use-adjusted effective cost.
- Never Again = exclusion; Dislike and Like = preferences subject to defined scoring.
- Do not count a planned-but-skipped meal as consumed. Preserve dated history for rolling variety.
- Variety includes exact recipe, protein, cooking method/cuisine, and side/starch categories when metadata supports them.
- Monthly planning requires time-indexed purchases/inventory, not merely setting days=28.
- Nutrition constraints require reliable per-ingredient/per-portion nutrition evidence.
- Free and premium should share the same solver; tier differences are persistence, history, forecast quality and convenience, not basic dietary safety.

## Public sharing and intellectual property
- Share high-level equations, experimental methodology, charts, limitations and reproducible non-sensitive examples.
- Keep proprietary pricing/data pipelines, user information, production credentials and commercial algorithms private as appropriate.
- Verify third-party data rights, trademarks, source attribution and platform/API terms before public release.
- Name/tag researchers, companies and tool providers only when factually relevant; attribution is not endorsement.

## Decision gate before wider launch
1. Can the system generate feasible, practical, dietary-safe weekly plans consistently?
2. Are actual Tesco pack quantities and checkout totals correct?
3. Is improvement against a fair baseline measurable and reproducible?
4. Do pilot households find it useful and return to it?
