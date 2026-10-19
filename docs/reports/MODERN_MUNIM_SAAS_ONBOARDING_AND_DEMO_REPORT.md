# Modern Munim SaaS onboarding and demo audit

Date: 2026-10-14. Source inspection plus one database-free pytest file. The host database was not opened. Spring was not started. Port 8080 was not changed. No migration was added. No records were seeded or deleted.

## Verdict

**READY FOR STAGING ONLY**

Tenant isolation, founder-only demo data, and persistent guided onboarding are not implemented. Staging purchase-order behavior from the earlier pass is unchanged and is not re-stated here as SaaS acceptance.

## Schema blocker

**BLOCKED.** Existing rows cannot be mapped to workspaces without guessing.

Alembic head is `008_user_store_type`. That revision adds nullable `users.store_type` only. Earlier revisions add MFA columns, `store_name`, and `email_otps`. None add `workspaces`, `tenant_id`, or `workspace_id`.

`users.store_name` is a nullable string. It is not unique and it is not a foreign key. `orders.user_id` points at the user who placed a customer order. It is not a store boundary. Products, vendors, expenses, purchase orders, stock transactions, inventory snapshots, and AI forecast tables have no owner column.

The prior readiness pass recorded 6 host users (2 `admin`, 4 `customer`) and an empty host catalog. This pass did not re-query those rows. Two admins cannot be split into “founder” and “ordinary store” from role alone. The four customer rows have no store. Staging still holds the purchase-order smoke rows (product, vendor, purchase order, one `in` ledger row) with no owner column. Attaching any of that to `shuklapratham758@gmail.com` would be an assumption.

No Alembic revision was written.

## 1. Workspace model

**VERIFIED** by inspection: a coherent tenant or workspace model does not exist.

Evidence: `backend/app/models/user.py` columns are `id`, `email`, `password_hash`, `role`, `mfa_enabled`, `mfa_secret`, `store_name`, `store_type`, `created_at`. Roles are `customer`, `admin`, `manager`. `backend-java` `User.java` maps the same columns. Business entities listed below have no `tenant_id` or `workspace_id`.

## 2. Authorization and scoping

Admin means “any admin sees the whole database.” It does not mean “this admin’s store.”

| Area | Auth boundary | Workspace scope | Label |
|---|---|---|---|
| Products list, get, create, update, delete | FastAPI `get_current_admin`. Spring `hasRole("ADMIN")` on `/api/products/**` | `product_service.get_products` is `db.query(Product)` with search, price, and stock filters only | **VERIFIED** unscoped |
| Vendors list, create, delete, rankings, products, scorecard | Admin on both stacks | Queries filter by vendor id or active flag, not by user | **VERIFIED** unscoped |
| Expenses list, create, update, delete | Admin | `Expense` has optional `product_id` only | **VERIFIED** unscoped |
| Purchase orders create, list, deliver | Admin | List filters optional `vendor_id` and limit. Deliver loads by purchase-order id | **VERIFIED** unscoped |
| Inventory stock-in, stock-out, transactions, threshold | Admin | Ledger rows key off `product_id` | **VERIFIED** unscoped |
| Dashboard revenue, expenses, profit, stock, sales | Admin | `get_revenue_data` sums every completed order in the window. Spring `sumInventoryValue()` sums every product | **VERIFIED** unscoped |
| Orders create | Admin; row stores `current_user.id` | Create is attributed, not isolated from other admins | **PARTIALLY VERIFIED** |
| `GET /api/orders` | Admin | `get_all_orders` | **VERIFIED** global |
| `GET /api/orders/my-orders` | Admin | `Order.user_id == current user` | **VERIFIED** user filter, still not a workspace |
| `GET /api/orders/{id}` | Admin | Loaded by id. Optional user filter only when `user_id` is passed | **VERIFIED** any admin can read any order through the list-all path |
| AI forecasts, alerts, batch | FastAPI admin routes | Rows hang off `product_id` | **VERIFIED** unscoped |
| Exports | No export route in `backend/app/api` | Not implemented | **NOT VERIFIED** as a feature; absence **VERIFIED** by route list |

`get_current_admin` checks `role == "admin"` from the JWT user id. It does not read the email. Spring `SecurityConfig` uses the same role prefixes and does not add a workspace matcher.

Customer tokens are rejected with 403 on these business prefixes. That was verified in the earlier staging pass for products and orders. It was not re-run here. Label for this pass: **PARTIALLY VERIFIED** (source plus prior staging note). Unauthenticated calls remain 401 in that earlier pass.

## 3. Founder account

**NOT VERIFIED** that `shuklapratham758@gmail.com` is the only founder account in a database. This pass did not query users.

**VERIFIED** by inspection that the address is not a server-side authorization rule. It does not appear in `admin_auth_service.py`, `SecurityConfig.java`, or the frontend auth modules. `PROJECT_REPORT.md` names it as a git author, which does not grant access.

There is no founder role. Every successful onboard inserts `role=ADMIN`. A second admin has the same catalog rights as the first.

Frontend email checks for this address: **VERIFIED** absent. That is not a control, because the server does not enforce it either.

## 4. Demo records

**VERIFIED** by inspection: demo rows are not tagged, not limited to a founder workspace, and not safe to regenerate beside real data.

`backend/app/main.py` does not import `seed_data`. Startup does not seed. **VERIFIED.**

`python -m app.seed_data` is a manual script. It does not create users. Products skip an existing name. Vendors skip an existing name. Purchase orders skip an existing `po_number`. Expenses are appended on every run with no existence check. Nothing sets `is_demo` or a workspace id. A second run of expenses duplicates rows in the shared tables. Deleting “demo” later cannot be limited to demo rows, because they look like normal products and expenses.

The staging purchase-order rows from the earlier pass (`STAGING-PO-20261014`, vendor, PO, one inbound ledger row) are ordinary rows. They are not founder demo data.

## 5. Ordinary users and guided onboarding

**VERIFIED** by inspection: a new email does not receive an isolated workspace or a persistent guided tour.

`start_auth` returns `needs_onboarding` and does not insert a user. `complete_onboarding` inserts one global admin with `store_name` and `store_type`, then sends OTP. That flow was covered by `tests/test_admin_auth.py` on `marketplace_auth_test` in the earlier pass (**PARTIALLY VERIFIED** here: not re-run, because that file opens `DATABASE_URL`).

After login, the SPA shows `CinematicIntro`. Skip calls `onComplete`. `App.tsx` sets `introSeen` in local settings and does not read it, so a refresh shows the intro again. There is no server checklist, no step id, and no resume. Store-type collection is the signup form, not in-app guidance.

Ordinary users are not a separate product path. The only non-admin role that business routes accept is none: customers and managers fail `get_current_admin`.

## 6. Tests this pass

`cd backend && ./venv/bin/pytest tests/test_saas_isolation_gap.py -q --noconftest`

**5 passed** in 0.13s.

The file reads source text. It does not import `app.main` and does not connect to PostgreSQL. It checks:

- no `tenant_id` or `workspace_id` in the listed model, security, dashboard, auth, and seed files
- founder email absent from FastAPI admin auth and Spring security config
- dashboard revenue function has no `user_id` or `workspace`
- seed script is not referenced from `main.py` and has no demo or workspace key
- orders are the only inspected business model with `user_id`, and the list route is documented as all orders for any admin

Tests that two tenants’ reads and writes return 403, that dashboard totals ignore another tenant, that a non-founder cannot regenerate demo data, and that onboarding step state survives a new session: **BLOCKED**. They need a workspace key and a persisted onboarding row that do not exist.

`mvn test` was not run. Spring test slices can open the datasource in `application.yml`, which points at the host database. Host access was out of scope.

## 7. What was not done

- No host `psql`, no counts, no deletes
- No Spring process and no change to port 8080
- No public deploy
- No Alembic or Flyway change
- No seed run
- No commit

## Recommended next task

The mapping proposal is `MODERN_MUNIM_USER_WORKSPACE_MAPPING_PLAN.md`. The founder email is not one of the six host accounts. Do not add `workspace_id`, do not backfill `store_name`, and do not run `seed_data` until the operator approves or corrects that plan.
