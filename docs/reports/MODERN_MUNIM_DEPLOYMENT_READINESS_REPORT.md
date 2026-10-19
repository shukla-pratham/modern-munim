# Modern Munim deployment readiness report

Date: 2026-10-14. Branch `main` at `9cb755e`, with the existing uncommitted product work left in place. This pass changed authorization, enum binding, production mail checks, the AI Insights placeholder, tests, Compose SMTP wiring, and these two documents. It did not commit.

## Verdict

**READY FOR STAGING ONLY**

SMTP delivery, a local Compose boot, a new-admin browser sign-in, and one staging purchase-order delivery were verified on 2026-10-14. The project is still not deployment-ready: four customer rows remain on the host `marketplace_db`, the host catalog is empty, the Compose stack uses a local port override, and Spring was not started.

A later same-day audit of tenant isolation, founder-only demo data, and guided onboarding did not change this verdict. Those SaaS criteria are **not** implemented. Evidence is in `MODERN_MUNIM_SAAS_ONBOARDING_AND_DEMO_REPORT.md`. No schema change was applied. The host database, Spring, and port 8080 were not touched in that audit.

## Architecture and routing

- FastAPI on `127.0.0.1:8000` owns `/api/auth` and `/api/ai`, and in production owns every `/api` route.
- Vite dev server: with `VITE_USE_SPRING_PRODUCTS` unset, all `/api` goes to FastAPI. With it set to `true`, products, inventory, orders, expenses, vendors, dashboard, and purchase orders go to Spring. Auth and AI do not.
- Production `final-frontend` build uses one `VITE_API_URL`. `docker-compose.yml` states that the image does not split traffic. Spring is Compose profile `java` only. Hibernate `ddl-auto` is `validate`.
- On this machine, port 3000 served a different application (Aegis). Modern Munim’s dev server was started on port 3010. Port 8080 is `alphaforge-app`, not this Spring service. Those processes were not stopped.

## Database

Re-verified before edits:

- Host `localhost`, port `5432`, database `marketplace_db`, PostgreSQL 14.23, `ENVIRONMENT=development`.
- Alembic `008_user_store_type` (already applied in the previous task). No further migration was required or applied.
- `email_otps` exists and matches `EmailOtp` (`email` primary key, `code_hash`, `store_name`, `expires_at`, `attempt_count`, `created_at`).
- `users` has `mfa_enabled`, `mfa_secret`, `store_name`, `store_type`.
- Accounts unchanged: 6 users, 2 `admin`, 4 `customer`. Products 0. OTP rows 0. No accounts were deleted.

PostgreSQL enum labels on `marketplace_db` are lowercase (`pending`/`completed`/`cancelled`, `inventory`/`operations`/`marketing`, `one_time`/`recurring`, `in`/`out`). A fresh `marketplace_auth_test` database migrated with `alembic upgrade head` has the same labels.

Backup from the previous task, taken before `008`, still stands:

`/Users/prathamshukla/modern-munim-backups/marketplace_db-20261014-155541.dump` (76,002 bytes, custom format, `pg_restore --list` succeeded). This pass did not take a second dump because it did not change the schema.

## Defects fixed

1. **Dashboard queries sent `COMPLETED` into an enum that only accepts `completed`.** Fresh-database auth test `test_existing_user_login_flow` failed on `GET` revenue. `SQLEnum` columns for orders, expenses, stock transactions, job runs, and forecast trends now persist the enum values, same pattern as `User.role`. Re-run: 13 passed on `marketplace_auth_test`.
2. **Spring converters wrote uppercase and `STOCK_IN` labels.** They now write the lowercase labels that Alembic creates. Enum unit tests were updated.
3. **Product reads were public, and Spring allowed any logged-in user to create or read orders.** FastAPI `GET /api/products` and `GET /api/products/{id}` now require `get_current_admin`. Spring requires `ROLE_ADMIN` for `/api/products`, `/api/orders`, and the other business prefixes. Live check: unauthenticated `GET /api/products` returned 401. `POST /api/auth/register` still returns 400.
4. **Production could start without SMTP and could log OTPs.** `enforce_production_mail` rejects production when `SMTP_USER` or `SMTP_PASSWORD` is missing, or when `EMAIL_OTP_DEV_LOG` is true. Compose passes those variables and sets `EMAIL_OTP_DEV_LOG=false`. Health checks no longer put the database exception string in the JSON body.
5. **AI Insights showed fabricated forecasts, including a $12,400 figure.** The page now says results appear only after the batch job and shows “No AI results yet.”

## Authentication verification

Isolated database `marketplace_auth_test` (created for tests, not a replacement for `marketplace_db`), Alembic `008_user_store_type`:

`DATABASE_URL` pointed at that database only for the pytest process.

`pytest tests/test_admin_auth.py tests/test_production_config.py -q` → **13 passed**.

Covered there: new-user onboard to admin, password hash, OTP verify, existing-user login, wrong password, non-admin 403 on orders, forgot-password then password update, unauthenticated product reads, production mail guards.

Live `marketplace_db` smoke, no account created:

- `GET /health` → 200, `status` healthy, `database` healthy.
- `POST /api/auth/start` for an unknown address was already verified in the previous task (`needs_onboarding`, user count unchanged).
- Browser on `http://127.0.0.1:3010/`: Welcome / Sign In, then Continue with `audit-browser-20261014@example.com`. The next screen was store name and store type (“Looks like you're new here.”). Onboarding was not submitted, so no OTP was issued and no mail was sent. Afterward: still 6 users, 0 rows matching `audit-%`, 0 OTP rows.

Full browser OTP entry, refresh, and logout were **not** run. Completing onboarding on the live API would create an admin and send mail. Those steps are covered by the isolated tests with a captured OTP, not by the browser.

## SMTP

Re-tested on interface `en0`, gateway `172.20.112.1` (not `utun6`):

| Stage | Result |
|---|---|
| DNS | 1 address |
| Banner / EHLO | 250 |
| STARTTLS | 250 |
| AUTH | 235 |
| Application `send_email` | SMTP DATA **250** `2.0.0 OK` |
| Inbox | **Confirmed** by IMAP search: 1 message with subject `Modern Munim SMTP delivery check 2026-10-14` |

The recipient was the configured SMTP mailbox (`gmail.com`), which is also the sender. No message was sent to the six database accounts. The API response and server logs did not contain an OTP for that check; the message body had none.

## Tests

| Check | Result |
|---|---|
| `pytest` auth + production config on `marketplace_auth_test` | 13 passed |
| `mvn test` in `backend-java` | exit 0, Surefire 150 tests, 0 failures |
| `npx tsc --noEmit` | exit 0 |
| `npx vitest run` | 32 passed |
| `VITE_API_URL=http://127.0.0.1:8000 npx vite build` | exit 0 (chunk size warning only) |
| Docker Compose staging boot | exit 0. See the verification section below |
| Live purchase-order delivery | **not run** (catalog empty; not executed against `marketplace_db`) |
| AI batch job | **not run** |
| Pytest / Maven / Vitest this pass | **not re-run**. Application code did not change. Counts above are from the prior pass |

Spring order auth regression: `OrderControllerAuthTest` (customer create and get-by-id are 403, anonymous create is 401).

## Security still open

- Four `customer` rows remain. They were not deleted. FastAPI login is disabled, and business routes reject non-admins. They are leftover data, not a login path through the SPA.
- Spring `POST /api/auth/register` can still insert a customer if that process is exposed. Those tokens cannot call business routes after this change. FastAPI remains the auth owner.
- Dev OTP logging stays available when `ENVIRONMENT=development` and SMTP fails. Production rejects that flag.
- Swagger on Spring is still public if Spring is started.
- In-process rate limits trust `X-Forwarded-For` and reset is still tied to resend. Not changed in this pass.
- The host catalog is still empty. Stock reconciliation below is on the staging database only.

No critical issue from the audit remains open. The verdict stays staging-only because the host catalog and the four customer rows are unchanged, and the default Compose port map was not the one started.

## Compose and sign-in verification (2026-10-14)

Project `modernmunim-staging`. Files: `docker-compose.yml` plus `docker-compose.staging.yml`. The Java profile was not started. `alphaforge-app` stayed up on `127.0.0.1:8080`.

| Service | Host |
|---|---|
| `marketplace_postgres` | no host port; volume `modernmunim-staging_postgres_data` |
| `marketplace_backend` | `127.0.0.1:18000` → container `8000` |
| `marketplace_frontend` | `127.0.0.1:8088` → container `80` |

The container database host is `postgres`, name `marketplace_db`, Alembic `008_user_store_type` after `alembic upgrade head` inside the API container. It is not the host PostgreSQL on `127.0.0.1:5432`. After the test, that staging database had 0 users and 0 OTP rows. The host database still had 6 users (2 admin, 4 customer) and revision `008_user_store_type`.

Container environment: `ENVIRONMENT=production`, `EMAIL_OTP_DEV_LOG=false`, SMTP user and password set, `DEBUG` unset. `GET http://127.0.0.1:18000/health` returned 200 with `database: healthy`. The built SPA contains `http://127.0.0.1:18000`. `GET http://127.0.0.1:8088/health` returned HTML, because nginx does not proxy `/api`. `.env.example` now uses `http://localhost:8000` for the default Compose port map.

The first `docker compose up` stalled while pulling `postgres:15-alpine` (layer about 101.7 MB of 108 MB) and was stopped. A separate `docker pull` then succeeded. The next build failed with `failed to xattr ... operation not permitted` on AppleDouble `._*` files under `/Volumes/bheekh`. Those files were removed (1,358) and `._*` was added to both Docker ignore files. The following build and start exited 0. Backend and Postgres health checks reported healthy.

Browser sign-in on `http://127.0.0.1:8088` against that API only:

- Unknown mailbox reached store name and store type. No user existed before Continue on that step.
- Onboarding created one `admin` (`Staging Store`, Grocery) and sent one login-code email. IMAP found that message. The code was not in the page copy, the API JSON, or container logs (`DEV OTP` lines: 0).
- Verify opened `/dashboard`. `GET /api/auth/me` was 200 with `role=admin`. `GET /api/products` with the session was 200 and an empty list. The same call without a token was 401.
- Reload of `/dashboard` stayed signed in after Skip Intro.
- Logout cleared `localStorage.access_token` and returned to Welcome / Sign In. Opening `/dashboard` again redirected to `/`.
- Reusing the OTP returned 400 and no token. A wrong password returned 401 and no token.
- A customer JWT created only in the staging database received 403 from `GET /api/products` and `GET /api/orders`. That row was deleted.
- The staging admin row was deleted after the test.

The existing-user OTP path was not repeated in the browser. It remains covered by the earlier isolated pytest run.

## Staging purchase-order delivery (2026-10-14)

Re-checked before the run: `modernmunim-staging` containers were up, API `GET /health` was 200, database host inside the API container was `postgres` (not `localhost`), Alembic was `008_user_store_type`, and staging had 0 users, 0 products, 0 vendors, 0 purchase orders, and 0 stock rows. `alphaforge-app` was left on port 8080. The host database stayed at 6 users and 0 products.

FastAPI had `mark_purchase_order_delivered` but no HTTP route. Spring already exposes `POST /api/purchase-orders/{id}/deliver`. Staging traffic uses FastAPI, so delivery could not be called. The route was added. The service also called `TransactionType.IN`, which does not exist after the enum was renamed to `STOCK_IN` (`in`). That line was corrected. Creating a purchase order still does not change stock; the first delivery adds stock and one `in` ledger row; a second delivery returns the order and does not write again.

`DATABASE_URL=postgresql://prathamshukla@localhost:5432/marketplace_auth_test ./venv/bin/pytest tests/test_purchase_order_delivery.py -q` → **1 passed**. That database is not the host `marketplace_db` and not the staging volume. The test deleted its own rows (0 leftover `po-deliver-%` products).

The staging API image was rebuilt and `marketplace_backend` was recreated. Unauthenticated `POST /api/purchase-orders/1/deliver` returned 401. The workflow then used that API with a staging-only admin (user id 3, role admin). Records were left in place.

| Step | Result |
|---|---|
| `POST /api/products` | 201. Product **1**, name `STAGING-PO-20261014`, stock **2**. No ledger row |
| `POST /api/vendors` | 201. Vendor **1**, name `STAGING-VENDOR-20261014` |
| `POST /api/vendors/1/products` | 201. Min order qty 1, unit cost 4.25 |
| `POST /api/purchase-orders` | 200. PO **1**, `PO-20261014-1-1`, status `created`, qty **3**. Stock stayed **2**. Ledger count **0** |
| `POST /api/purchase-orders/1/deliver` | 200. Status `delivered`. Stock **5**. Ledger row **1**: product 1, type `in`, quantity 3, reason `Purchase order PO-20261014-1-1 delivered` |
| Same deliver again | 200. Status stayed `delivered`. Stock stayed **5**. Ledger count stayed **1** |
| `POST /api/purchase-orders/999999/deliver` | 404 `Purchase order 999999 not found`. Stock and ledger unchanged |
| Deliver with `actual_delivery_date=not-a-date` | 422. Stock stayed **5**. Ledger count stayed **1** |

Reconciliation: opening stock 2 is stored on the product and is not a ledger row. Ledger sum is 3. Expected on-hand is 2 + 3 = **5**, which matches `products.stock_quantity`. There is no purchase-order foreign key on `stock_transactions`; the PO number is in `reason`. Direct SQL on the staging database matched the API. After the run the host database was still 6 users, 0 products, 0 purchase orders, and 0 stock rows. Staging health remained 200.

## How to reproduce

1. Load `backend/.env` (do not print it).
2. `./venv/bin/alembic current` shows `008_user_store_type`.
3. `curl -sS http://127.0.0.1:8000/health`
4. `curl -sS http://127.0.0.1:8000/api/products` → 401.
5. Isolated tests: create or reuse `marketplace_auth_test`, `alembic upgrade head` against that URL, then pytest as above.
6. SPA: `npx vite --host 127.0.0.1 --port 3010 --strictPort` in `final-frontend`.

See `DEPLOYMENT_RUNBOOK.md` for backup, restore, and Compose.

## SaaS isolation audit (2026-10-14)

Source inspection only. `pytest tests/test_saas_isolation_gap.py -q --noconftest` from `backend/` → **5 passed**. That file does not open a database. It records that business models have no `tenant_id` or `workspace_id`, that `shuklapratham758@gmail.com` is not a server authorization check, that dashboard revenue is unscoped, that `seed_data` is not started from `main.py`, and that `GET /api/orders` lists every order for any admin.

Runtime cross-tenant denial tests were not run. They are blocked until a workspace key exists. This SaaS section did not query the host database. Alembic remains `008_user_store_type`. No migration was added because the six host users cannot be assigned to workspaces from `store_name` alone.

A later read-only pass did query `marketplace_db` and wrote `MODERN_MUNIM_USER_WORKSPACE_MAPPING_PLAN.md`. The founder email is not among the six users. Workspace assignment stays blocked until the operator approves that plan.
