# Household application — first working version

The application adds persistent household state and a mobile-friendly interface to the existing optimiser. It is a single-household prototype with password access, not a multi-user production service. The code has been executed and tested locally. No Supabase project or public application deployment was created in this session: authenticated access to those providers is not available.

## What works

- Browse all 40 recipes, read ingredients and methods, and pin required meals.
- Generate one to seven dinners for two, jointly selecting recipes and integer Tesco packs.
- Save ingredient/recipe exclusions and optionally avoid the most recent plan with confirmed purchases.
- Start with genuinely empty stock. Neither the example rice nor simulated leftovers are imported.
- Add stock, correct a total, record a discard and optionally date a batch.
- Save draft plans without changing stock; inspect separate shopping and consumption estimates.
- Abandon unused drafts; confirm actual received pack counts, including zero for missing items.
- Record a meal cooked using the displayed quantities, or skip it without consuming anything.
- Use the resulting actual stock in the next optimisation. Every inventory change has an audit event.

## Database design

| Table | Fields and purpose |
|---|---|
| `households` | Household ID, revision counter and saved preferences. This version intentionally operates one household (`home`). |
| `inventory_batches` | Ingredient, canonical unit, remaining quantity, creation date, optional use-by date and source. Each addition is a new batch. |
| `inventory_events` | Unique request ID, timestamp, operation, submitted payload and ingredient quantity deltas. Records actual changes and prevents duplicate processing. |
| `plans` | Immutable solver inputs/output snapshot, opening revision, creation date, purchase-confirmation flag, abandoned flag and per-recipe cooked/skipped status. |

Recipes, ingredient definitions and Tesco products remain authoritative CSV catalogue files. They are not duplicated into a second mutable catalogue. Plans keep full product, quantity and price snapshots as JSON so later catalogue changes do not rewrite history. The small first version uses JSON for plan details/preferences; separate detail tables can be introduced when cross-household reporting needs them.

`app/database.py` defines the shared SQLAlchemy schema. `db/001_initial.sql` is the initial Supabase/PostgreSQL DDL. SQLite runs the local prototype and automated tests. PostgreSQL support and DDL are supplied but have not been executed against a live Supabase account. Future schema changes need explicit versioned migrations; `create_all` only creates missing tables and does not upgrade existing ones.

All application tables enable PostgreSQL row-level security with no public policies. The SQL migration also revokes `anon`/`authenticated` access. The backend must connect using its private database owner connection. This is server-only database access, not browser access through Supabase's Data API. Never put the database password in frontend code.

## Inventory rules

- **Add stock:** existing 200 g + new 1,000 g = 1,200 g.
- **Correct total:** entered 1,000 g becomes the total. This retires existing batches for the ingredient and creates one corrected batch; previous expiry information is replaced. The UI explains this.
- **Discard:** subtracts stock with an explicit event; a discard greater than recorded stock is rejected.
- Dates before today's server date exclude a batch from planning and cooking but retain it visibly for review/discard. Undated stock is assumed available; expiry over future cooking days is not modelled.
- Cooking consumes earliest dated usable batches first, then undated batches. Exact physical batch use is still a user assumption.
- Receipt confirmation adds only received packs, using the saved product's usable quantity. For substitutions, mark the planned product zero and add the substitute's usable quantity manually.
- Recording a cooked meal deducts the displayed solver quantities atomically. If any ingredient is insufficient, the entire transaction rolls back. Correct discrepancies before retrying; partial recipe consumption is not yet editable.
- Request identifiers make retries safe. A second confirmation with a different request identifier is also rejected after a plan's purchases or a meal have been recorded.
- Stock corrections include a revision check; stale browser edits are rejected. Database locking serialises changes; a plan is not saved if stock/preferences changed during its solve.
- Simulated ending inventory and projected plan leftovers never automatically become actual household stock.

## Solver integration

`POST /api/plans` launches an isolated Python process (`app/solver_job.py`). It supplies the database stock and filters excluded recipes/ingredients before calling the unchanged `solve()` function. Required recipes remain solver constraints. Isolation prevents request-specific catalogue filtering leaking between requests. Original scripts and historical snapshot fingerprints remain unchanged.

The backend waits up to 120 seconds; only proven optimal results are saved. The app accepts one simultaneous solve per server process. Run a single application worker for this initial personal deployment. Larger experiments need a job queue and resource/time limits at the solver level.

Servings are fixed at two. No budget, dietary certification or nutrition switches are presented without underlying solver support. Exclusions refer to canonical recipe ingredients and are not allergen certification of product labels.

## Run locally

Install Python 3.11+ and run from the repository root:

```sh
python -m pip install -r requirements-app.txt
# Set APP_PASSWORD (12+ characters) and SESSION_SECRET (32+ characters)
# in your local shell or hosting secret manager; do not commit them.
# For local HTTP only, set COOKIE_SECURE=false.
python -m uvicorn app.main:create_app --factory --host 127.0.0.1 --port 8000
```

Open `http://127.0.0.1:8000`. SQLite defaults to `grocery.db`, which is ignored by Git. Preserve that file if using the local app. The app does not automatically load `.env`; `.env.example` documents required environment variables. Obtain a random session secret with `python -c "import secrets; print(secrets.token_hex(32))"` locally and store it privately.

## Hosted deployment

A `Dockerfile` and `render.yaml` are provided. The backend serves both the HTML/JavaScript interface and API from one origin. No separate frontend host or MCP is required.

1. Connect a Supabase project and run `db/001_initial.sql` as the database owner.
2. Supply its backend PostgreSQL connection as `DATABASE_URL`, with `sslmode=require`. Use a supported session/direct connection, not an anonymous API key.
3. Deploy this repository's Docker service on a Python/container host. Configure `APP_PASSWORD`, `SESSION_SECRET` and `COOKIE_SECURE=true` privately. The Render blueprint marks the first two user-supplied values and generates a session secret.
4. Use the resulting HTTPS URL on a phone. The web manifest requests a standalone Home Screen experience. It is online-only; native iPhone installation has not been tested.

A cloud SQLite file on ephemeral storage is not an acceptable substitute for the hosted database. Free hosting may sleep and has compute limits. No paid resources have been provisioned. Hosting can be completed once provider access is connected.

## Authentication and limits

Signed, HTTP-only, same-site session cookies protect the single household. Mutations require a custom same-origin request header; cross-origin access is not enabled. Password comparison is constant-time; a process-wide login-attempt cap limits repeated guesses. Password and session secret are required at startup. Use TLS and one worker for personal testing. Before public multi-user use, replace the shared password with per-user identity, membership authorisation and distributed rate limits.

Frontend implementation uses plain HTML, CSS and JavaScript with no external CDN dependency. This deliberately keeps the first workflow small; the HTTP API can support React or MCP later. The design is responsive, with four views: This week, Recipes, My kitchen and Preferences. No browser or API response is cached for offline use.

Not implemented: Tesco account/basket integration, live price refresh, payment, opened-date tracking, actual paid-price accounting, automatic expiry forecasts, arbitrary servings, or a rolling multiweek objective.

## Executed verification

The data validator passed: 40 recipes, 125 covered recipe ingredients, 240 products, 222 eligible products, zero missing mappings. Full suite: **27 tests passed** (17 existing + 10 application tests), including actual solver calls through the HTTP API, persistence, receipt retries, partial shopping, atomic cooking rollback, exclusions, repetition, abandoned plans and next-plan carry-over. `node --check app/static/app.js` passed.

HTTP tests also serve the real HTML and test authentication. Interactive browser/visual QA could not be completed: the managed preview supervisor runs in a separate environment where the Python interpreter used for the tested backend is unavailable (`python: not found`, including the absolute runtime path). No browser rendering or iPhone installation is claimed as verified.
