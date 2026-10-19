# Modern Munim — Architecture

Describes the architecture **as of Sprint #1** (dual-run migration).

## High-level

```
┌─────────────────────┐
│  final-frontend     │  React + TypeScript + Vite
│  (port 3000 / :80)  │
└─────────┬───────────┘
          │ /api/*
          ▼
┌─────────────────────┐     optional dual-run
│  Vite / Nginx proxy │────────────────────────────┐
└─────────┬───────────┘                            │
          │                                        │
          ▼                                        ▼
┌─────────────────────┐                 ┌─────────────────────┐
│  FastAPI backend    │                 │  Spring Boot        │
│  :8000 (default)    │                 │  backend-java :8080 │
│  full business+AI   │                 │  Products, Inventory│
│  + PO create/list   │                 │  Auth, Orders,      │
│                     │                 │  PO deliver,        │
│                     │                 │  Expenses           │
└─────────┬───────────┘                 └─────────┬───────────┘
          │                                       │
          └───────────────────┬───────────────────┘
                              ▼
                    ┌──────────────────┐
                    │  PostgreSQL 15   │
                    │  marketplace_db  │
                    │  (Alembic schema)│
                    └──────────────────┘
```

`nexus-ops/` is a legacy Lovable prototype and is **not** deployed.

## Request flow (Inventory, dual-run enabled)

1. Browser calls `POST /api/inventory/stock-in` with `Authorization: Bearer <jwt>`.
2. Vite proxies to Spring (`VITE_USE_SPRING_PRODUCTS=true`) or FastAPI (default).
3. JWT filter loads `users` by `sub` claim → `UserPrincipal` with `ROLE_ADMIN` / `ROLE_MANAGER` / `ROLE_CUSTOMER`.
4. Method/security rules require `ADMIN` for inventory mutations.
5. `InventoryService` opens a transaction, `SELECT … FOR UPDATE` on product, updates `stock_quantity`, inserts `stock_transactions`.
6. Response DTO (snake_case JSON) returns to the UI.

## Database flow

- Schema owned by **Alembic** (`backend/alembic/versions`).
- Spring: `ddl-auto=validate` — refuses to start if entities diverge.
- Business writes go to the same tables FastAPI uses (`products`, `stock_transactions`, `users`).

## Authentication flow

```
Login (form username/password)
   → verify bcrypt password_hash
   → JWT HS256 { sub: userId, exp }
   → client stores access_token
   → subsequent requests: Authorization: Bearer …

Register (public)
   → always role=customer (Spring)
   → FastAPI path still exists; frontend no longer sends role=admin

Bootstrap admin (Spring only)
   → X-Bootstrap-Token must match BOOTSTRAP_ADMIN_TOKEN
   → only if no admin row exists
```

Shared `SECRET_KEY` allows FastAPI-issued tokens to authorize Spring endpoints during dual-run (and vice versa).

## AI flow (target; Python remains owner)

```
Ops trigger / scheduler
   → Python AI service (pandas/numpy/Prophet)
   → write demand_forecasts, stockout_predictions, …
   → Spring (future) reads tables for dashboard / PO suggestions
```

Sprint #1 ships `AiServiceClient` stub only. FastAPI still serves `/api/ai/*` and batch jobs.

## Deployment architecture

### Local dual-run

| Service | Command / port |
|---------|----------------|
| Postgres | local `marketplace_db` |
| FastAPI | `uvicorn` `:8000` |
| Spring | `backend-java/run-local.sh` `:8080` |
| Frontend | `npm run dev` `:3000` (+ optional `VITE_USE_SPRING_PRODUCTS=true`) |

### Docker Compose (current + planned)

Existing: `postgres` + FastAPI `backend` + `final-frontend`.

Sprint #1 adds optional `backend-java` service on `8080` without removing FastAPI. Docker daemon was unavailable during Sprint #1 validation; image build is prepared via `backend-java/Dockerfile`.

## Product principle (operational intelligence loop)

```
Business data → Inventory/Sales/Expenses/Vendors
  → Analytics → Forecast → Stockout risk → Recommendation
  → Vendor decision → PO → Approval → Receiving → Inventory update
  → New data → Continuous improvement
```

Framework migration must preserve this loop — not invent unrelated features.
