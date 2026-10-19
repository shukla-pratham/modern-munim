# Modern Munim — complete forensic audit

Audit date: 2026-10-14. Scope: repository at `/Volumes/bheekh/marketplace`. Method: source inspection, Git state, read-only SQL, SMTP handshake (no message sent), Spring tests on H2, frontend unit tests and `tsc --noEmit`.

This audit did not change source, configuration, environment files, database rows, migrations, dependencies, or Git state. The only file added is this report.

Evidence labels: **VERIFIED**, **PARTIALLY VERIFIED**, **NOT VERIFIED**, **KNOWN GAP**, **OUT OF SCOPE**, **REGRESSION**.

---

## 1. Executive summary

The working tree contains a large uncommitted admin-auth and Spring migration on top of commit `9cb755e`. That code describes an admin-only email → password → (store onboarding if new) → OTP → JWT product. The database the app is configured to use does not match that code.

`marketplace_db` on `localhost:5432` is at Alembic revision `004_po_if_missing`. Head in the tree is `008_user_store_type`. The `users` table has only `id`, `email`, `password_hash`, `role`, `created_at`. There is no `email_otps` table and no `store_name`, `store_type`, or MFA columns. Starting the current FastAPI auth flow against this database will fail when it tries to write an OTP.

FastAPI (`:8000`) and Spring (`:8080`) were not listening during this audit. Vite (`:3000`) returned HTTP 200. Catalog tables (products, vendors, orders, expenses, stock ledger) are empty. Six user rows remain: 4 `customer`, 2 `admin`.

Unit tests that do not touch this database passed (Spring 146, frontend 32, `tsc` clean). FastAPI pytest was not run because those tests insert and delete rows in `DATABASE_URL`.

**Verdict: NOT READY.** The SPA and the uncommitted auth implementation cannot complete sign-in on the current schema, and the API processes are down.

---

## 2. Repository and runtime state

| Item | Evidence |
|---|---|
| Root | `/Volumes/bheekh/marketplace` **VERIFIED** |
| Branch | `main`, tracking `origin/main` (GitHub `shukla-pratham/marketplace`) **VERIFIED** |
| HEAD | `9cb755e09fd14cc709956a2e06e25cf615e8fbb1` — “Add demo customer account abcd@fufu.com to seed data” **VERIFIED** |
| Working tree | `git status --short` count 56. Not committed. Includes modified auth, frontend, compose, docs, plus untracked `backend-java/`, Alembic `006`–`008`, auth services, and frontend auth helpers **VERIFIED** |
| Recent history | `9cb755e`, `2b5d6b3` flatten repos, `d70bf3f` / `39a6d76` env examples, `f608a7e` initial **VERIFIED** |

### Uncommitted work vs findings

Uncommitted work is the auth rewrite, Spring backend, Vite split proxy, and docs. It is not “broken by this audit.” Findings below are mismatches between that tree, the live database, and processes that are actually running.

HEAD `seed_data` still documents a demo customer. The modified `backend/app/seed_data.py` in the working tree skips user creation. Runtime `main.py` does not call seed. **VERIFIED** (code). Whether an operator has run the old seed is **NOT VERIFIED**.

### Components

| Area | Location | Role |
|---|---|---|
| SPA | `final-frontend/` | Vite/React app the product uses |
| Legacy UI | `nexus-ops/` | Separate Vite app with mock data. Not in Compose. **OUT OF SCOPE** for the product, still in the repo |
| API (auth owner) | `backend/` | FastAPI |
| API (business, optional) | `backend-java/` | Spring Boot 3.4.5, untracked |
| DB | PostgreSQL `marketplace_db` | Alembic intended owner |
| AI | `backend/app/services/ml_service.py`, `ai_persistence_service.py`, `jobs/ai_batch_job.py` | In-process Prophet/rules, not a separate service |
| Deploy | `docker-compose.yml`, Dockerfiles | FastAPI + Postgres + SPA; Spring behind Compose profile `java` |

### Processes (this audit)

| Port | State | Evidence |
|---|---|---|
| 3000 | Listening (`node`, `*:3000`). `GET /` → 200 | **VERIFIED** |
| 8000 | Not listening. Health curl failed | **VERIFIED** |
| 8080 | Not listening. Health curl failed | **VERIFIED** |
| 5432 | Postgres listening on localhost | **VERIFIED** |

Vite process environment had no `VITE_*` variables. `vite.config.ts` sends every `/api` prefix to FastAPI unless `VITE_USE_SPRING_PRODUCTS=true`. Current dev server is therefore flag-off. **VERIFIED** (process env + config default).

---

## 3. Architecture and request routing

Development (`final-frontend/vite.config.ts`):

- Flag off: `/api` → FastAPI `127.0.0.1:8000`.
- Flag on: `/api/products`, `/api/inventory`, `/api/orders`, `/api/expenses`, `/api/vendors`, `/api/dashboard`, `/api/purchase-orders` → Spring `127.0.0.1:8080`.
- Everything else, including `/api/auth` and `/api/ai`, stays on FastAPI. There is no blanket Spring catch-all.

Production (`docker-compose.yml`, `final-frontend/Dockerfile`, `nginx.conf`):

- Frontend build takes one `VITE_API_URL`. Nginx serves the SPA and does not proxy `/api`.
- Compose `backend` is FastAPI. `backend-java` is profile `java` only and is not a dependency of the frontend.
- The dev split is not reproduced in production. **VERIFIED** from Compose and Vite comments.

Axios (`final-frontend/src/lib/api.ts`): dev `baseURL` is empty (proxy). Production requires `VITE_API_URL` starting with `http`. Bearer token from `localStorage.access_token`. HTTP 401 clears the token and sends the browser to `/`. Timeout 20000 ms.

---

## 4. Frontend feature inventory

Routes in `final-frontend/src/App.tsx` when the session user role is `admin` (case-insensitive): `/dashboard`, `/inventory`, `/vendors`, `/purchase-orders`, `/expenses`, `/ai-insights`, `/settings`. `/` and unknown paths redirect to `/dashboard`.

Logged-out routes: `/` login, `/register` (page still mounted; backend register is disabled). Other paths redirect to `/`. Non-admin sessions see an access-denied state and sign out. `sessionStorage` key `pending_password_reset=1` shows `SetNewPasswordGate` before the app shell.

| Page | Implementation | Status |
|---|---|---|
| Login / onboard / OTP / forgot password | `LoginPage.tsx`, `authFlow.ts`, `auth-context.tsx` call `/api/auth/start`, `/onboard`, `/verify-otp`, `/resend-otp`, `/forgot-password` | Code **VERIFIED**. Live browser flow **NOT VERIFIED** (API down, schema behind) |
| Set new password | `PATCH /api/auth/password` after OTP login | Code **VERIFIED**. Live **NOT VERIFIED** |
| Dashboard | Five dashboard APIs. Cards navigate to expenses, inventory, purchase orders. Pie slices go to `/expenses?category=` | Code **VERIFIED**. Live **NOT VERIFIED** |
| Expenses | CRUD client + category query param | Code **VERIFIED**. Live **NOT VERIFIED** |
| Inventory / Vendors / Purchase orders | Real API clients | Code **VERIFIED**. Live **NOT VERIFIED** |
| Settings | Account fields from `/me`. “Reset All Mock Data” only clears `ff-settings` and `ff-auth` in `localStorage` (`useSettings.ts`). It does not call the API | **VERIFIED** (misleading label, local-only behavior) |
| AI Insights | Static array in `AIInsights.tsx` (includes “Estimated savings: $12,400”). `aiAPI` in `api.ts` is not used by the page | **KNOWN GAP** / mock UI |
| Index, NotFound | Files exist, not mounted by `App.tsx` | Dead pages **VERIFIED** |
| Orders UI | Comment in `api.ts`: no orders page; do not add `ordersAPI` | **KNOWN GAP** |
| PO receiving | `purchaseOrdersAPI` has create/list only. Comment: SPA has no receiving UI | **KNOWN GAP** |
| Header Add menu | Navigates to `/inventory` or `/vendors`. It does not open the add dialogs; those pages have their own buttons | **VERIFIED** |
| `nexus-ops` | Mock dashboard/vendors; login field `defaultValue="password"` | Separate app **OUT OF SCOPE** |

Currency in the live SPA pages uses `₹`, except the hardcoded AI Insights dollar figure. **VERIFIED** by search.

Frontend tests cover display helpers and auth-flow units, not page integration. They do not prove the SPA against a running API. **VERIFIED**.

---

## 5. FastAPI endpoint and security audit

Routers are mounted in `backend/app/main.py`. Authenticated business routes use `get_current_admin` (`dependencies.py`), which loads the user from the JWT `sub` and requires `role == "admin"`. No business route depends on `get_current_user` alone. **VERIFIED**.

Public:

- `GET /`, `GET /health`
- `GET /api/products`, `GET /api/products/{id}` (`products.py` docstring: public)
- Auth pre-session routes listed below
- Default FastAPI OpenAPI docs (docs URL not disabled)

Admin:

- Product writes, inventory, expenses, dashboard, AI, vendors, purchase orders, all order routes including `GET /my-orders` and `GET /{order_id}`

Auth routes (`backend/app/api/auth.py`):

| Method | Path | Auth | Behavior |
|---|---|---|---|
| GET | `/api/auth/store-types` | none | Static store-type list |
| POST | `/api/auth/start` | none | New email → `needs_onboarding` (no user row). Existing + correct password → OTP. Wrong password → 401 |
| POST | `/api/auth/onboard` | none | Creates `UserRole.ADMIN`, then OTP |
| POST | `/api/auth/resend-otp` | none | Re-issues OTP for an existing user |
| POST | `/api/auth/verify-otp` | none | Checks OTP, forces `role=admin`, deletes OTP row, returns JWT |
| POST | `/api/auth/forgot-password` | none | Email only. Existing user gets OTP. Missing user gets the same status with a different message |
| PATCH | `/api/auth/password` | admin | Sets a new hash. Does not require the old password |
| POST | `/register`, `/login`, `/request-otp` | none | Always HTTP 400. They do not issue tokens |
| GET | `/api/auth/me` | admin | Profile |

Error JSON from `app/core/middleware.py` uses `error`, not FastAPI’s `detail`, except validation errors which include both. **VERIFIED**.

Purchase orders: create and list only. No deliver route in `backend/app/api/purchase_orders.py`. **VERIFIED**. Spring has `POST /api/purchase-orders/{id}/deliver`.

Startup (`main.py`) does not seed, wipe, or create users. **VERIFIED**.

`/health` returns `status: healthy` even when the database string is `unhealthy: …` only if the check passes; on failure status is `degraded` and the exception text is included. **VERIFIED** (code). Live health **NOT VERIFIED** (process down).

---

## 6. Authentication flow audit

Intended flow vs `admin_auth_service.py`:

- New: `start_auth` returns `needs_onboarding` without inserting a user (lines 93–99). `complete_onboarding` inserts `role=ADMIN`, hashes the password, issues OTP (lines 153–170). `verify_otp` issues the JWT.
- Existing: correct password issues OTP (lines 101–112).

That matches the intended sequence in source. **VERIFIED** (code). **NOT VERIFIED** live.

OTP (`admin_auth_service.py`, `email_service.py`):

- 6 digits, `secrets.randbelow`.
- Stored as bcrypt (`get_password_hash`). Not present on `AuthStartResponse` (`status`, `email`, `message` only).
- Expiry `EMAIL_OTP_EXPIRE_MINUTES` default 10.
- Single-use: row deleted after success.
- `MAX_OTP_ATTEMPTS = 5`. A resend sets `attempt_count = 0`, so the cap resets.
- Dev log: if `ENVIRONMENT == "development"` and `EMAIL_OTP_DEV_LOG` (default **True**), SMTP failure or missing SMTP logs the code. Current `.env` does not set `EMAIL_OTP_DEV_LOG`, so the default applies. `ENVIRONMENT=development` is set. Production Compose sets `ENVIRONMENT=production`, which skips the log path.
- Bcrypt rounds are 4 when `ENVIRONMENT == "development"` at import (`security.py`), otherwise 12.

JWT: HS256, `SECRET_KEY` (set, length 43, value not recorded), expiry 30 minutes, claim is `sub` only. Cookie is set only if `JWT_COOKIE_NAME` is non-empty (default empty). Session in the SPA is `localStorage.access_token`. Logout clearing that key is in the client; live refresh/logout **NOT VERIFIED** this session.

`verify_otp` assigns `UserRole.ADMIN` before the admin check (lines 280–291). Any account that can complete OTP becomes admin, including a pre-existing customer. That is consistent with “every successful login is admin,” and it also means forgot-password (email + inbox access, no current password) promotes and logs the user in.

Legacy `auth_service.create_user` still defaults to customer, but no router calls it. `email_otp_service.py` always raises 400. MFA helpers exist; there is no MFA route. **VERIFIED**.

Rate limits: start, onboard, resend, forgot-password. `verify-otp` has no IP limiter. The limiter is in-process and trusts the first `X-Forwarded-For` hop. **VERIFIED** (code).

### Live schema blocks the flow — REGRESSION

`alembic current` → `004_po_if_missing`. `alembic heads` → `008_user_store_type`. `alembic_version.version_num` is `004_po_if_missing`. **VERIFIED**.

Not applied:

| Revision | File | Tracked in Git? | Effect (from revision chain) |
|---|---|---|---|
| `005_normalize_userrole` | `005_normalize_userrole_enum.py` | Yes (committed) | Normalizes `userrole` labels |
| `006_add_user_mfa` | `006_add_user_mfa_columns.py` | No (untracked) | MFA columns |
| `007_store_email_otp` | `007_add_store_name_and_email_otps.py` | No | `store_name` + `email_otps` |
| `008_user_store_type` | `008_add_user_store_type.py` | No | `store_type` |

`information_schema.columns` for `users` has no store or MFA columns. `pg_tables` has no `email_otps`. **VERIFIED**.

Pytest in `backend/tests/test_admin_auth.py` (11 tests) uses `SessionLocal()` and commits cleanup deletes. It was **not** run, to avoid writing the live database. Result: **NOT VERIFIED**.

No account was created or deleted for this audit.

---

## 7. SMTP / OTP delivery

`.env` (values redacted): `SMTP_HOST=smtp.gmail.com`, `SMTP_PORT=587`, user and from-address are the same `gmail.com` mailbox, app password length 16. `EMAIL_OTP_DEV_LOG` key absent (code default true). **VERIFIED**.

Handshake on 2026-10-14, no message sent:

| Stage | Result |
|---|---|
| DNS | OK (1 address) |
| TCP 587 | OK |
| SMTP banner / EHLO | OK, code 250, ~0.62s |
| STARTTLS (certifi CA bundle) | OK, EHLO 250 |
| AUTH | OK, code 235 |
| Message delivery | **NOT VERIFIED** (intentionally not sent) |
| Route | Interface `en0`, gateway `172.20.112.1` |

The earlier failure mode (TCP open, banner timeout, route via `utun6`) was **not** reproduced. AUTH was reached and succeeded, so this is not an invalid-credential result. Whether Gmail accepts a message from this network remains **PARTIALLY VERIFIED**.

`email_service.py` uses an 8s SMTP timeout and certifi for `starttls`. On failure in development it logs the OTP and returns delivery mode `log`. Production re-raises. Compose `backend` environment does **not** pass `SMTP_*`. With `ENVIRONMENT=production`, OTP send fails closed (503) rather than logging the code. A production deploy as written cannot email OTPs. **VERIFIED** (Compose + code). Live production **NOT VERIFIED**.

---

## 8. Spring migration and parity

Spring is untracked, not running, and not on the production request path unless `VITE_API_URL` is pointed at it or the dev flag is on.

`application.yml`: `ddl-auto: validate` on the default profile (no schema mutation). Profile `test` uses H2 `create-drop`. **VERIFIED**.

Security (`SecurityConfig.java`), first match wins:

- Public: health, actuator health/info, Swagger, `POST /api/auth/login|register|bootstrap-admin`, `GET /api/products` and `GET /api/products/**`.
- `hasRole("ADMIN")`: inventory, product writes, `GET /api/orders` (collection), purchase orders, expenses, vendors, dashboard.
- Any authenticated user: `POST /api/orders`, `GET /api/orders/my-orders`, `GET /api/orders/**`, `GET /api/auth/me`.

`AuthService.register` always saves `UserRole.customer`. `login` issues a JWT for any valid password. `bootstrapAdmin` returns 403 unless `BOOTSTRAP_ADMIN_TOKEN` matches and no admin exists (`AuthService.java` lines 35–67). FastAPI `/login` and `/register` are disabled. The two stacks do not share an auth flow. They can share `SECRET_KEY` and the `users` table, so a Spring-issued customer token is a real token for Spring’s “authenticated” matchers. **VERIFIED** (code).

Parity gaps that matter when the dev flag is on:

- Order create and get-by-id are admin-only on FastAPI and not on Spring.
- Spring has PO deliver with row lock and “already delivered → return current row” (`PurchaseOrderService.deliver`, lines 122–128). FastAPI and the SPA do not expose deliver.
- Spring has no `/api/ai` controller. `AiServiceClient` only has a health call and is unused.
- Enum converters write uppercase `orderstatus` / `expensecategory` / `expensetype` and `STOCK_IN`/`STOCK_OUT`, matching labels observed previously on this project. This audit’s empty tables did not re-sample stored enum values beyond type labels. Converter code **VERIFIED**. Live rows **NOT VERIFIED** (tables empty).

`User.role` still uses Hibernate `NAMED_ENUM` (`User.java`). `userrole` labels in this database were not fully re-listed after the failed query batch; 005 is unapplied. Treat role label compatibility as **PARTIALLY VERIFIED** until 005 is applied and a login is attempted.

Maven tests: 16 Surefire files, **146 tests, 0 failures, 0 errors, 0 skipped**, exit 0. They use H2, not `marketplace_db`. **VERIFIED**.

---

## 9. Database and data integrity

Database name `marketplace_db` on `localhost:5432`. Other local databases exist (`alphaforge`, `alphaforge_test`, `postgres`) and were not inspected.

Counts (**VERIFIED**, read-only):

| Table | Rows |
|---|---|
| users | 6 (4 customer, 2 admin) |
| products, vendors, vendor_products, purchase_orders, purchase_order_items, orders, order_items, stock_transactions, expenses | 0 |

`email_otps` does not exist. Business catalog is empty. This audit did not delete those rows. Why the catalog is empty is **NOT VERIFIED** (no destructive history was reconstructed).

Hibernate will not create the missing auth tables (`ddl-auto: validate`). If Spring starts against this schema it should fail validation once it maps `store_type` / OTP-unrelated columns that exist on the entity. `User.java` maps `storeType`; that column is absent. Spring startup against this DB is expected to fail validation. **PARTIALLY VERIFIED** (mapping + information_schema; process was not started, on purpose).

Stock ledger vs quantity: no rows, so consistency is vacuously true and **NOT VERIFIED** as a behavior. PO deliver idempotency is implemented and covered by H2 tests, not by this database.

No startup path in `main.py` wipes users. **VERIFIED**.

---

## 10. AI and integrations

| Feature | State |
|---|---|
| `GET /api/ai/*` | Reads stored forecast/alert rows. Admin-only. Tables exist and were not counted after the query stopped on `email_otps`. Computation is not on the request path |
| `POST /api/ai/batch-process` | Calls `run_ai_batch_processing`. Not scheduled by `main.py` |
| `ml_service.py` | Prophet if importable and ≥14 points; else moving average. `requirements.txt` pins `prophet==1.1.5` and notes the fallback. Trend via `numpy.polyfit`. Stockout is stock/velocity. No external LLM API |
| `vendor_ai.py` / `vendor_scoring.py` | Rules and weighted scores. Comment: no external ML APIs |
| SPA AI Insights | Mock cards. Not wired to `/api/ai` |
| Spring `AiServiceClient` | Unused health client |

Live batch job and Prophet fit: **NOT VERIFIED**. UI is placeholder: **VERIFIED**.

---

## 11. Security findings

### Critical

None that were shown by a live exploit. The auth schema gap is a release blocker (section 16) more than an exposure.

### High

1. **Auth cannot run on the current database.** Missing `email_otps` and store columns. Impact: sign-in 500s once FastAPI is started. Evidence: Alembic `004` vs head `008`; information_schema. Safe check: `alembic current` and `\d users` (read-only).
2. **Spring can mint non-admin JWTs and then allow `POST /api/orders`.** `AuthService.register` creates customers; `SecurityConfig` allows any authenticated user to create orders and read `GET /api/orders/**`. FastAPI order routes are admin-only. Impact appears only if Spring is reachable. Evidence: `SecurityConfig.java` lines 55–58, `AuthService.java` lines 35–43.
3. **Production Compose has no SMTP settings** while `ENVIRONMENT=production` disables the log fallback. Impact: deployed sign-in cannot deliver or reveal an OTP. Evidence: `docker-compose.yml` backend `environment` block; `email_service.py` lines 74–100.

### Medium

4. **Product GET is public** on both stacks. Admin-only product still exposes the catalog without a token. `products.py` lines 15–36; `SecurityConfig.java` line 50.
5. **Forgot-password plus `verify_otp` promotes to admin** without the current password. By design for recovery; inbox access is full account takeover and role upgrade. `admin_auth_service.py` lines 174–201 and 280–284.
6. **Resend resets the 5-attempt OTP cap.** `verify-otp` has no IP rate limit. `auth.py` lines 124–138; service resend path resets `attempt_count`.
7. **Rate-limit key trusts `X-Forwarded-For`.** `auth.py` lines 26–30.
8. **Development bcrypt cost is 4.** `security.py`. Current `ENVIRONMENT=development`.
9. **Dev OTP log default is on** when SMTP fails. `.env` omits `EMAIL_OTP_DEV_LOG`. Codes can land in server logs.
10. **`/health` and dev 500 bodies include exception text.** `main.py` lines 80–81; `middleware.py` development branch.
11. **Swagger is permitAll** on Spring. `SecurityConfig.java` line 47.
12. **Four customer rows remain** in `users`. They are not created by current `main.py`. They contradict the admin-only data model. Emails not recorded here.

### Low

13. **Settings button says “Reset All Mock Data”** but only clears local UI keys.
14. **AI Insights shows a fake $12,400 savings figure.**
15. **`start_auth` distinguishes unknown email (200 onboarding) from bad password (401).** Enumeration. Forgot-password is closer to uniform, but the message text still differs.
16. **In-memory rate limit** does not span multiple Gunicorn workers.
17. **`nexus-ops` login field defaults to the literal `password`.** Unused by Compose.

Secrets: `.env` is gitignored (`.gitignore` lines 26–28). `git ls-files` showed no tracked `.env`. This report does not contain passwords, OTPs, tokens, or full email addresses. SMTP AUTH used the configured app password and did not print it.

No destructive probes were run.

---

## 12. Test, build, and runtime results

| Check | Command | Result |
|---|---|---|
| Frontend types | `npx tsc --noEmit -p .` in `final-frontend` | Exit 0 **VERIFIED** |
| Frontend unit | `npx vitest run` | 6 files, 32 tests, all passed **VERIFIED** |
| Spring | `mvn -q test` in `backend-java` | Exit 0. Surefire: 146 tests, 0 failures, 0 errors, 0 skipped. H2 only **VERIFIED** |
| FastAPI auth tests | `pytest tests/test_admin_auth.py` | **NOT RUN.** Tests commit to `DATABASE_URL`. Schema is missing `email_otps`. Running them would write or error against the live DB |
| Frontend production build | `vite build` | **NOT RUN.** Would write `dist/`. Types and unit tests were used instead |
| ESLint | not run | **NOT VERIFIED** |
| FastAPI / Spring health | curl | Down. **VERIFIED** as inaccessible |
| Vite | curl `:3000/` | 200 **VERIFIED** |
| Browser click-through | not performed | **NOT VERIFIED.** APIs are down, so a login walkthrough could not succeed |
| Alembic | `alembic current` / `heads` | current `004_po_if_missing`, head `008_user_store_type` **VERIFIED** |
| SMTP through AUTH | Python `smtplib` | 235 **VERIFIED**. No mail sent |

---

## 13. Deployment and documentation gaps

- README and `QUICK_START.md` in the working tree say there are no demo users and describe email + password + OTP. That matches the uncommitted code and **not** HEAD (`9cb755e` adds a demo customer to seed) and **not** the live database (customers exist, OTP tables do not).
- Many root markdown files (`ARCHITECTURE.md`, `MIGRATION.md`, `PROJECT_DOCUMENTATION.md`, `PROJECT_REPORT.md`, and others) are untracked. They were not treated as current truth.
- Compose production image does not split `/api` the way Vite does, and does not inject SMTP.
- Spring healthcheck uses `GET /health` (`HealthController`), which is present. Frontend service has no healthcheck.
- `005` is committed but not applied. `006`–`008` are not even committed. A fresh clone of `origin/main` does not contain the auth migration files or `backend-java/`.

---

## 14. Unfinished features and limitations

- AI Insights page is mock data.
- No orders UI. FastAPI order APIs exist and are admin-only; the SPA does not call them.
- No purchase-order receiving UI. Spring deliver exists; FastAPI deliver does not.
- Header Add menu only navigates.
- MFA code is unused.
- `nexus-ops` is a second, mock-driven frontend.
- Dashboard “last 30 days” will show zeros whenever business dates are older or, as now, tables are empty.
- In-process rate limits and dev OTP logging are local-development behavior.
- Dual-run routing exists only in the Vite dev server.

---

## 15. Regressions and potential regressions

**REGRESSION (runtime vs this working tree):** Alembic is at `004` while auth code requires `007`/`008`. OTP sign-in cannot succeed. Catalog tables are empty, so any UI that used to show products, vendors, expenses, or purchase orders will show empty states once the APIs are up. This audit did not establish who emptied them.

**Potential:** Starting Spring against this database with `ddl-auto: validate` should fail because `User.storeType` (and related auth columns) are mapped but absent. Not executed.

**Potential:** Turning `VITE_USE_SPRING_PRODUCTS=true` while Spring’s order matchers stay non-admin reopens customer order access that FastAPI closed.

**Not a regression of this audit:** FastAPI and Spring were already stopped when the audit started.

---

## 16. Prioritized remediation

Do these in order. Do not treat green unit tests as a substitute for the schema.

1. **Backup `marketplace_db`, then apply Alembic through `008_user_store_type`.** Confirm `email_otps`, `users.store_name`, `users.store_type`, and MFA columns exist. Do not start Spring until `ddl-auto: validate` succeeds.
2. **Start FastAPI only, hit `GET /health`, then exercise `/api/auth/start` on a sacrificial address.** Confirm unknown email returns onboarding and does not insert a user; confirm OTP is absent from JSON. Decide whether the dev log fallback stays on.
3. **Decide what to do with the 4 customer rows** before calling the product admin-only. Do not delete them as part of an unplanned cleanup.
4. **Add `SMTP_*` to the production Compose backend** (secrets via the environment, not the image) or document that production sign-in is impossible.
5. **If Spring stays in the dev proxy:** make order create and get-by-id `hasRole("ADMIN")`, and disable or guard `POST /api/auth/register` so it cannot create customers beside FastAPI’s admin flow.
6. **Replace AI Insights mock data** or remove the page until `/api/ai` is wired.
7. **Commit or explicitly shelve** `backend-java/` and migrations `006`–`008` so `origin/main` is not the only artifact reviewers see. HEAD still advertises a demo customer.

---

## 17. Recommended next task

**Apply the pending schema and prove one auth request. Do not redesign auth.**

Scope:

- Read-only backup or dump of `marketplace_db` first.
- `alembic upgrade head` from `backend/` so revision becomes `008_user_store_type`.
- Start FastAPI with the existing `.env` (no secret changes).
- `GET /health` returns database healthy.
- `POST /api/auth/start` with an unknown email returns `needs_onboarding`, does not insert a `users` row, and does not return an OTP.
- `POST /api/auth/register` and `POST /api/auth/login` still return 400.
- Stop there. Do not create a real admin unless a separate task asks for it. Do not change OTP rules, hashing, or the FastAPI-owned flow.

Acceptance fails if `email_otps` is still missing, if health is degraded, or if any response contains a 6-digit code.

---

## 18. Not verified, and why

- Browser login, refresh, logout, and direct URL entry. APIs were down and the schema cannot store an OTP.
- FastAPI pytest. It writes the live database.
- Sending an email. AUTH succeeded; delivery was not attempted.
- Prophet batch job and AI table contents.
- Spring process boot against PostgreSQL (`ddl-auto: validate`).
- Why catalog tables are empty.
- Contents of `alphaforge` databases.
- Production Docker runtime.
- ESLint and `vite build`.

---

## Compact status

| Area | Status | Evidence | Risk | Recommended action |
|---|---|---|---|---|
| Git / working tree | Uncommitted auth + Spring on `9cb755e` | `git status`, `git log` | High (origin lacks the product) | Commit only after schema and auth smoke pass |
| Vite | Up, flag off | curl 200; no `VITE_*` in process env | Low | Keep flag off until Spring boots cleanly |
| FastAPI process | Down | port 8000 closed | High | Start after migrations |
| Spring process | Down | port 8080 closed | Medium | Start only after `validate` succeeds |
| Auth code | Matches intended flow | `admin_auth_service.py`, `auth.py` | — | Do not change it in the next task |
| Auth schema | Behind head | Alembic `004` vs `008`; no `email_otps` | Critical for sign-in | `alembic upgrade head` |
| Users data | 4 customer, 2 admin | `select role, count(*)` | High vs admin-only claim | Review before deleting anything |
| Catalog data | Empty | counts 0 | High for demos | Confirm this is the intended database |
| SMTP AUTH | Succeeded on `en0` | EHLO 250, STARTTLS, AUTH 235 | Low today | Do not weaken fallback; add SMTP to Compose |
| SMTP send | Not tried | — | Unknown | Optional later, to a chosen recipient |
| Frontend units | 32 passed, tsc clean | vitest, tsc | Low | Not a substitute for API smoke |
| Spring units | 146 passed on H2 | Surefire | Medium if mistaken for prod proof | Re-check on Postgres after migrate |
| FastAPI tests | Not run | would write live DB | — | Run only against a disposable database |
| Orders UI / PO receive / AI page | Missing or mock | `api.ts`, `AIInsights.tsx` | Medium | Separate product tasks |
| Prod routing | Single `VITE_API_URL` | Compose, Dockerfile | Medium | Do not assume the Vite split ships |
| Public product GET | Both stacks | `products.py`, `SecurityConfig` | Medium | Close if the catalog is private |
| Spring order auth | Weaker than FastAPI | `SecurityConfig` 55–58 | High if flag on | Align with admin-only |

---

## Overall verdict

**NOT READY.**

The uncommitted application describes a coherent admin OTP login and a Spring business API, and the automated tests that avoid this Postgres instance passed. The database that `DATABASE_URL` points at is still on Alembic `004`, has no OTP storage, still has customer accounts, and has an empty catalog. Both API servers are stopped. Until migrations are applied and one auth request succeeds against that database, the project is not ready to test the product end to end and not ready to deploy.
