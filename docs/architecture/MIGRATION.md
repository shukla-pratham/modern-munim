# Modern Munim — Migration Log

Living document for the FastAPI → Spring Boot migration. Describes what **actually exists**.

## Sprint #1 status (2026-08-11)

### Migrated (working in `backend-java/`)

| Domain | FastAPI source | Spring component | Status |
|--------|----------------|------------------|--------|
| Products CRUD | `app/api/products.py`, `product_service.py` | `ProductController`, `ProductService`, `Product` entity | Migrated |
| Inventory stock-in/out/threshold/transactions | `app/api/inventory.py`, `inventory_service.py` | `InventoryController`, `InventoryService`, `StockTransaction` | Migrated |
| Orders create/list/get | `app/api/orders.py`, `order_service.py` | `OrderController`, `OrderService`, `Order`/`OrderItem` | Migrated (ledger stronger than FastAPI) |
| PO receiving (deliver) | `vendor_service.mark_purchase_order_delivered` (no HTTP route; broken `TransactionType.IN`) | `PurchaseOrderController#deliver`, `PurchaseOrderService` | Migrated (Spring-only; ledger `in`) |
| Expenses CRUD | `app/api/expenses.py`, `expense_service.py` | `ExpenseController`, `ExpenseService`, `Expense` entity | Migrated (financial only; no stock/ledger) |
| Auth login / me / safer register | `app/api/auth.py`, `auth_service.py` | `AuthController`, `AuthService`, JWT filter | Partial (see differences) |
| Health | `GET /health` | `HealthController` | Migrated |

### Intentionally not migrated yet

- Dashboard, vendors redesign, PO create/list/cancel/payment
- AI/ML pipeline (`ml_service`, batch job, AI read APIs) — stays Python
- Rate limiting, Gunicorn, trusted hosts
- Orders SPA UI / PO receiving UI / Expenses mutation UI (list/filter is live in TASK 14; mock page had no create/edit/delete)

### FastAPI backend

**Untouched and still the production default.** Do not delete.

---

## Orders migration notes (TASK 3)

- Status on create remains **`completed`** (FastAPI parity).
- Spring **writes `stock_transactions`** (`out`, `quantity_change=-qty`, `reason=Order #<id>`) inside the same `@Transactional` as stock deduction — intentional integrity improvement over FastAPI.
- **No schema changes**; Alembic still owner; `ddl-auto=validate`.
- Dual-run proxy: `VITE_USE_SPRING_PRODUCTS=true` also routes `/api/orders` → Spring `:8080`.
- Cross-backend JWT (FastAPI token → Spring orders) verified during smoke.

---

## API mapping (Product + Inventory + Orders)

| Method | Path | Auth | Spring class |
|--------|------|------|--------------|
| GET | `/api/products` | Public | `ProductController#list` |
| GET | `/api/products/{id}` | Public | `ProductController#get` |
| POST | `/api/products` | ADMIN | `ProductController#create` |
| PUT | `/api/products/{id}` | ADMIN | `ProductController#update` |
| DELETE | `/api/products/{id}` | ADMIN | `ProductController#delete` |
| POST | `/api/inventory/stock-in` | ADMIN | `InventoryController#stockIn` |
| POST | `/api/inventory/stock-out` | ADMIN | `InventoryController#stockOut` |
| GET | `/api/inventory/transactions` | ADMIN | `InventoryController#transactions` |
| PUT | `/api/inventory/products/{id}/threshold` | ADMIN | `InventoryController#updateThreshold` |
| POST | `/api/orders` | Authenticated | `OrderController#create` |
| GET | `/api/orders` | ADMIN | `OrderController#listAll` |
| GET | `/api/orders/my-orders` | Authenticated | `OrderController#listMine` |
| GET | `/api/orders/{id}` | Owner or ADMIN | `OrderController#get` |
| POST | `/api/purchase-orders/{id}/deliver` | ADMIN | `PurchaseOrderController#deliver` |
| GET | `/api/expenses` | ADMIN | `ExpenseController#list` |
| POST | `/api/expenses` | ADMIN | `ExpenseController#create` |
| PUT | `/api/expenses/{id}` | ADMIN | `ExpenseController#update` |
| DELETE | `/api/expenses/{id}` | ADMIN | `ExpenseController#delete` |
| POST | `/api/auth/login` | Public (form) | `AuthController#login` *(Spring dual-run stub; SPA auth is FastAPI-owned)* |
| POST | `/api/auth/register` | Public | `AuthController#register` *(Spring dual-run stub)* |
| POST | `/api/auth/bootstrap-admin` | Bootstrap token | `AuthController#bootstrapAdmin` *(Spring dual-run stub)* |
| GET | `/api/auth/me` | Authenticated | `AuthController#me` *(Spring dual-run stub)* |

> **Live SPA auth (authoritative):** FastAPI admin flow — `POST /api/auth/start` → optional `/onboard` → `/verify-otp` → JWT → `GET /api/auth/me`. No demo seed users.
| GET | `/health` | Public | `HealthController` |

JSON uses **snake_case** (`stock_quantity`, `access_token`, …) to match FastAPI / frontend.

---

## Entity mapping

| Table | JPA entity | Notes |
|-------|------------|-------|
| `users` | `User` | PG enum `userrole` |
| `products` | `Product` | CHECK constraints remain in DB |
| `stock_transactions` | `StockTransaction` | PG enum `transactiontype` (`in`/`out`) |
| `orders` / `order_items` | `Order` / `OrderItem` | PG enum `orderstatus`; cascade items |
| `purchase_orders` / `purchase_order_items` | `PurchaseOrder` / `PurchaseOrderItem` | status VARCHAR (`created`/`ordered`/`delivered`/`cancelled`); deliver only |
| `vendors` | `Vendor` | Minimal (id, name) for PO response mapping |
| `expenses` | `Expense` | PG enums `expensecategory` / `expensetype`; optional `product_id` |

`inventory_snapshots` exists in DB but has **no runtime FastAPI API** — not migrated; documented as future analytics only.

---

## Expenses migration (TASK 9)

- Endpoints: `GET/POST /api/expenses`, `PUT/DELETE /api/expenses/{id}` — **ADMIN only** (FastAPI `get_current_admin` parity).
- No `GET /{id}` HTTP route (FastAPI service has `get_expense` but no router; Spring service `get` exists for update/delete/tests only).
- Enums: live PG labels are lowercase `inventory|operations|marketing` and `one_time|recurring`. Java constants stay uppercase; `ExpenseCategoryConverter` / `ExpenseTypeConverter` + `?::expensecategory` / `?::expensetype` bind the PG labels. HTTP API remains lowercase `inventory` / `one_time`.
- **TASK 15:** Hibernate `@Enumerated` + `NAMED_ENUM` previously bound `Enum.name()` (`OPERATIONS`) and failed against lowercase PG labels. SPA Expenses now has create/edit/delete using existing Inventory/Vendors modal patterns. FastAPI was not changed (same enum-name bug remains there).
- List: `skip`/`limit` (1–100), optional `category`/`product_id`; invalid category filter ignored; sort `created_at DESC`.
- Default `expense_type=one_time` on create.
- Does **not** mutate stock or `stock_transactions`.
- Dual-run: `VITE_USE_SPRING_PRODUCTS=true` routes `/api/expenses` → Spring.
- **SPA cutover (TASK 14):** Expenses page lists real `/api/expenses` records (category filter, spend-by-category chart, record table). Mock budget-vs-actual departments are not mapped. No create/edit/delete UI existed on the mock page and was not added. FastAPI remains the flag-off fallback.
- Known parity gap: update cannot clear `product_id` to null via JSON null (null = leave unchanged, like other Spring update DTOs).

---

## Dashboard analytics (TASK 12)

Backend contract migration only. FastAPI `dashboard_service.py` remains the source of truth for semantics; Spring reproduces it with **database aggregations** (JPQL SUM/COUNT/GROUP BY). Existing list APIs are **not** used (they cap at 100 and would undercount).

| Endpoint | Auth | Query | Notes |
|----------|------|-------|-------|
| `GET /api/dashboard/revenue` | ADMIN | `days` default 30, 1–365 | Completed orders only; `total_revenue`, `period=last_{days}_days`, `daily_revenue[]` |
| `GET /api/dashboard/expenses` | ADMIN | `days` default 30, 1–365 | `by_category` always includes `inventory`/`operations`/`marketing`; `by_type` always `one_time`/`recurring`; monthly `YYYY-MM` |
| `GET /api/dashboard/profit` | ADMIN | `days` default 30, 1–365 | `net_profit = revenue - expenses`; product rows from completed `order_items` + expense SUM by `product_id` |
| `GET /api/dashboard/stock-status` | ADMIN | none | Products only: total, low (`qty>0 AND qty<=threshold`), out (`qty==0`), `SUM(price*qty)` |
| `GET /api/dashboard/sales` | ADMIN | `days` default 30, 1–365 | Completed order count + product qty/revenue + daily orders/revenue |

- Cutoff: `now(UTC) - days` inclusive of today (`created_at >= cutoff`), matching FastAPI `datetime.utcnow() - timedelta(days=days)`.
- Read-only: `@Transactional(readOnly = true)`; no INSERT/UPDATE/DELETE.
- Tables used: `orders`, `order_items`, `expenses`, `products`. Not used: `stock_transactions`, `inventory_snapshots`, vendors, AI.
- **SPA cutover (TASK 13):** when `VITE_USE_SPRING_PRODUCTS=true`, Vite `/api/dashboard` → Spring. SPA Dashboard fetches the five endpoints (`days=30`). Unsupported mock widgets (Inventory Health, Vendor Reliability, AI Alerts, Inventory Movement, Vendor Performance) are hidden — not mapped to invented metrics. Flag off keeps `/api/dashboard` on FastAPI. FastAPI dashboard routes are **not** deleted.
- **Not a production gateway cutover.** Dual-run flag only.

---

## Purchase order receiving (TASK 7)

- Endpoint: `POST /api/purchase-orders/{id}/deliver` (ADMIN). Optional query `actualDeliveryDate`.
- Atomic `@Transactional`: pessimistic lock PO → idempotent if already `delivered` → lock each product → `stock_quantity += qty` → ledger `transaction_type=in`, `quantity_change=+qty`, reason `Purchase order {po_number} delivered` → set `status=delivered`, `actual_delivery_date`, `delay_days`.
- Delay rule (FastAPI parity): if promised set, `delay_days = max(0, ChronoUnit.DAYS between promised and actual)` (whole 24h periods, matching Python `timedelta.days`); early = 0; no promised → `null`. Do **not** use calendar local-dates after timestamptz→UTC normalization (that caused off-by-one in smoke).
- Missing product fails the whole TX (stricter than FastAPI, which silently skipped).
- **No** FastAPI / Alembic / schema changes. FastAPI create/list unchanged.
- Dual-run proxy (`VITE_USE_SPRING_PRODUCTS=true`): regex `^/api/purchase-orders/[^/]+/deliver` → Spring only; create/list remain FastAPI. No deliver UI button yet.

---

## Database migration strategy (decision)

**Choice: A — preserve existing Alembic schema; Spring validates only.**

- Alembic remains the **single schema owner** while FastAPI still runs.
- Spring Boot uses `spring.jpa.hibernate.ddl-auto=validate`.
- **Flyway is not introduced** in Sprint #1 to avoid two competing migration systems.
- After FastAPI cutover, baseline Flyway from the live schema in a later sprint.

No destructive migrations were applied in this sprint.

---

## Security mapping

| Concern | FastAPI | Spring (Sprint #1) |
|---------|---------|---------------------|
| Password | bcrypt (passlib) | `BCryptPasswordEncoder` (verifies existing hashes) |
| JWT | HS256, `sub`=user id string | Same contract via `JwtService` + shared `SECRET_KEY` |
| Admin APIs | `get_current_admin` | `hasRole("ADMIN")` |
| Manager | Enum exists; no elevated deps | `ROLE_MANAGER` granted; not used for inventory yet |
| Register | Client can pass `role=admin` | **Always creates `customer`** |
| Admin create | Via register | `POST /api/auth/bootstrap-admin` + `BOOTSTRAP_ADMIN_TOKEN` when no admin exists |

---

## Inventory ledger

**Current:** `stock_transactions` is a **partial** event ledger (type, qty delta, reason, timestamp). Missing: actor, reference id, balance-after. Orders do not write ledger rows in FastAPI.

**Sprint #1:** Migrated existing inventory API behavior only (stock-in/out write ledger). Did **not** redesign schema.

**Future minimal model (documented, not implemented):** extend `stock_transactions` or add `inventory_movements` with `user_id`, `reference_type`, `reference_id`, `balance_after` — only after dual-run cutover plan.

---

## AI boundary

```
React → Spring Boot (business) → PostgreSQL
                │
                └── HTTP → Python AI service (forecast / stockout / restock / dead stock)
                                │
                                └── persist results → PostgreSQL (read by Spring later)
```

`AiServiceClient` is scaffolding only. FastAPI still owns AI routes and batch jobs.

---

## Known differences vs FastAPI

1. Public register cannot self-elevate to admin.
2. Spring listens on **8080** by default (FastAPI **8000**).
3. Login rate limiting not yet ported.
4. Optional JWT cookie not ported (Bearer only).
5. Product list pagination uses in-memory skip after filter (fine for current catalog size; harden later).

---

## Frontend changes

- `final-frontend/vite.config.ts`: optional dual proxy via `VITE_USE_SPRING_PRODUCTS=true`
  - Also routes PO **deliver** only to Spring (create/list stay FastAPI)
- `final-frontend/src/lib/api.ts`: register no longer sends `role: 'admin'`
- Inventory UI already called real product/inventory APIs — no page rewrite
- No PO receiving button/UI yet
- **No** SPA client for `/api/orders` (Orders remain API-only)

---

## Dual-run routing matrix (TASK 8)

Applies to **Vite DEV proxy** when `VITE_USE_SPRING_PRODUCTS=true`.  
Production uses a single `VITE_API_URL` target (one backend) — dual-run split is a local/dev concern unless an external gateway mirrors this matrix.

| Operation | SPA calls? | Flag off (default) | Flag on | Notes |
|-----------|---------------|--------------------|---------|-------|
| Auth login/register/me | Yes | FastAPI `:8000` | FastAPI `:8000` | Catch-all; JWT shared with Spring |
| Products CRUD | Yes (list/create) | FastAPI | Spring `:8080` | Spring has full CRUD |
| Inventory stock-in/out | Yes | FastAPI | Spring | Ledger on both FastAPI + Spring |
| Orders create/list/get | **No SPA client** | FastAPI | Spring | Spring = canonical ledger; FastAPI deducts stock **without** ledger |
| Expenses list/filter | Yes (TASK 14) | FastAPI | Spring | SPA lists real records; no mutation UI (mock had none). CRUD API exists. |
| PO create | Yes | FastAPI | FastAPI | Spring has no create |
| PO list | Yes | FastAPI | FastAPI | Spring has no list |
| PO deliver | **No SPA client** | N/A (FastAPI has **no** deliver route) | Spring only | Regex proxy `^/api/purchase-orders/[^/]+/deliver` |
| Vendors | Yes | FastAPI | Spring | TASK 10; SPA live |
| Dashboard | Yes (TASK 13) | FastAPI | Spring | Flag on: SPA live against Spring. Flag off: FastAPI. AI Insights still mock. |
| AI | Partial/mock | FastAPI | FastAPI | Out of scope |

**TASK 8 decision:** No further proxy code change. Existing Vite rules already prevent routing unsupported PO ops to Spring and only send deliver to Spring when the flag is on.

### Order cutover status

- SPA does **not** call `/api/orders` (`api.ts` has no `ordersAPI`).
- With flag on, any direct/Vite `/api/orders` traffic goes to Spring (endpoints exist; not a dead route).
- Do **not** auto-cut over production to Spring Orders until an explicit gateway/proxy decision.
- FastAPI Orders remain legacy with incomplete ledger when the flag is off / FastAPI is the sole API.

### Ledger safety (Spring-routed stock mutators)

| Path | Mutates stock? | Ledger in same TX? | Classification |
|------|----------------|--------------------|----------------|
| Spring inventory stock-in | Yes ↑ | Yes (`in`) | VERIFIED |
| Spring inventory stock-out | Yes ↓ | Yes (`out`) | VERIFIED |
| Spring order create | Yes ↓ | Yes (`out`, reason `Order #<id>`) | VERIFIED |
| Spring PO deliver | Yes ↑ | Yes (`in`, reason `Purchase order {po} delivered`) | VERIFIED |
| Spring product create with initial stock | Sets stock | **No** ledger | KNOWN GAP (not fixed in TASK 8) |
| FastAPI order create | Yes ↓ | **No** ledger | KNOWN GAP (do not fix; avoid when Spring flag on) |
| FastAPI PO deliver | Intended ↑ | Broken / unrouted | KNOWN GAP (intentional; use Spring) |

---

## Remaining work (next sprints)

1. Vendors redesign, PO create/list in Spring (deliver + expenses + vendor HTTP done)
2. Python AI as dedicated service; Spring orchestrates (Dashboard SPA is on Spring when the dual-run flag is on; AI is not)
3. Flyway baseline after FastAPI decommission
4. Manager RBAC on operational endpoints
5. Integration/Testcontainers tests + concurrency stock tests
6. Full cutover + retire FastAPI business routes
7. Optional: Orders / PO receiving SPA wiring; Expenses create/edit/delete UI (list is live)
8. FastAPI order ledger gap (known; do not treat as solved while flag off)
9. Product initial-stock ledger gap (known; not TASK 9)
