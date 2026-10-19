# Modern Munim — Project Documentation

**Command Center for B2B Operations**

| | |
|---|---|
| **Product name** | Modern Munim (MM) |
| **Repository** | https://github.com/shukla-pratham/marketplace |
| **Type** | Full-stack B2B operations platform |
| **Version** | Backend API 2.0.0 |
| **License** | Proprietary |

This document explains the project for **business / non-technical readers** and for **engineers**. Use Part A for product understanding and stakeholder briefings; use Part B for architecture, setup, and maintenance.

---

# Part A — Non-Technical Overview

## 1. What is Modern Munim?

Modern Munim is an internal **operations command center** for B2B businesses. It brings inventory, spending, suppliers, purchase orders, and AI-assisted recommendations into one dashboard so operations, managers, and admins can see stock health, costs, and supplier performance without juggling spreadsheets or separate tools.

Think of it as a digital “munim” (accountant / operations keeper): it tracks what you have, what you spend, whom you buy from, and what you should do next.

## 2. Who is it for?

| Audience | How they use it |
|----------|-----------------|
| **Admins / owners** | Full control: products, stock, expenses, vendors, purchase orders, AI insights, dashboards |
| **Managers** | Role exists in the system for B2B workflows (seeded demo account); admin-level API access is currently reserved for the Admin role |
| **Ops / internal users** | Day-to-day operational records (customer-role accounts for internal use) |
| **Stakeholders** | High-level view of sales, expenses, stock risk, and vendor rankings |

## 3. Problems it solves

Without a unified ops tool, teams often face:

- Stockouts discovered too late  
- Dead inventory tying up cash  
- Unclear which vendor is actually reliable  
- Expenses scattered across categories with weak budget visibility  
- Purchase orders tracked in email or spreadsheets  
- “Gut feel” restocking instead of data-backed recommendations  

Modern Munim centralizes these into one application with live data and explainable AI suggestions.

## 4. Core capabilities (business view)

### Inventory
- Maintain product catalog (name, price, stock levels, thresholds)  
- Record stock in / stock out  
- See which items are healthy, low, or at risk  

### Expenses
- Log spending by category (inventory, operations, marketing, and related types)  
- Compare budgets vs actual spend  
- Visual charts for trend and breakdown  

### Vendors (supplier intelligence)
- Maintain supplier records and products they supply  
- Rank and compare vendors on performance  
- Scorecards and sourcing guidance for better purchasing decisions  

### Purchase orders
- Create and track POs with line items, costs, and delivery dates  
- Filter by vendor  
- Keep buying history in one place  

### Dashboard
- Revenue, expenses, profit-style metrics  
- Stock status overview  
- Sales and outbound signals for leadership  

### AI insights (decision support)
Not a black-box chatbot. Batch analytics produce:

| Insight | Business meaning |
|---------|------------------|
| **Demand forecasts** | How much of a product you are likely to need |
| **Stockout predictions** | How many days until you run out, and risk level |
| **Restocking recommendations** | Whether / how much / when to reorder (with reasons) |
| **Dead-stock detection** | Items that may need clearance, discount, or stop-ordering |
| **Alerts** | Actionable warnings surfaced for the team |

Recommendations include **human-readable explanations** so managers can trust and challenge the advice.

### Authentication & access
- Secure admin sign-in (email + password + email OTP; store onboarding for new accounts)  
- Admin-only application access (no customer storefront accounts)  

## 5. User journey (simple)

1. Open the web app (local: http://localhost:3000; production: your domain).  
2. Optional short intro animation, then **Login** or **Register**.  
3. Land on the **Dashboard**.  
4. Navigate: Inventory → Vendors → Purchase Orders → Expenses → AI Insights → Settings.  
5. Admins run or refresh AI batch insights when they want updated forecasts and alerts.  

## 6. Authentication (admin-only)

There are **no seeded demo accounts**. Every successful sign-in creates or restores an **admin** session:

1. Email + password  
2. New email → “Looks like you're new here” → store name + store type → create admin  
3. Existing email → password verified → skip onboarding  
4. 6-digit OTP → JWT → application  

OTP is emailed when SMTP is configured; in local development without SMTP it is logged by the FastAPI process only.

## 7. Value proposition (one paragraph)

Modern Munim gives a B2B team a single private command center for stock, spend, suppliers, and purchase orders, plus explainable AI that flags stockouts, dead inventory, and restock opportunities—without requiring paid third-party AI APIs. It is designed to be self-hosted, Docker-deployable, and usable by both operators and technical teams.

## 8. What is *not* in scope (current product)

- Public consumer marketplace storefront as the primary product  
- Mobile-native apps (it is a responsive web app)  
- Automatic payment gateway / ERP replacement for all finance functions  
- Real-time streaming AI on every click (AI is **batch-oriented**)  
- Treating the `nexus-ops` folder as production UI (that is an earlier prototype)  

---

# Part B — Technical Documentation

## 1. Architecture overview

```
┌─────────────────────┐     HTTPS / HTTP      ┌──────────────────────┐
│  final-frontend     │ ───────────────────► │  FastAPI backend     │
│  React + Vite + TS  │   /api/* (JSON/JWT)   │  Python 3.12         │
│  Port 3000 (dev)    │ ◄─────────────────── │  Port 8000           │
│  Port 80 (Docker)   │                       └──────────┬───────────┘
└─────────────────────┘                                  │
                                                         │ SQLAlchemy
                                                         ▼
                                              ┌──────────────────────┐
                                              │  PostgreSQL 15       │
                                              │  marketplace_db      │
                                              └──────────────────────┘
```

| Layer | Technology | Responsibility |
|-------|------------|----------------|
| Presentation | React 18, TypeScript, Vite 5, Tailwind, Radix/shadcn, Recharts, Framer Motion | SPA UI, charts, auth screens |
| API | FastAPI, Pydantic, Gunicorn + Uvicorn | REST API, validation, auth |
| Domain | Service modules under `backend/app/services/` | Business rules, ML pipelines |
| Data | PostgreSQL 15, SQLAlchemy 2, Alembic | Persistence, migrations |
| Ops | Docker Compose, Nginx (frontend image) | Packaging and production serve |

**Production frontend:** `final-frontend/` (wired to the live API).  
**Prototype (not deployed):** `nexus-ops/` — Lovable/mock UI with local mock data only.

## 2. Repository layout

```
marketplace/
├── backend/                 # FastAPI application
│   ├── app/
│   │   ├── api/             # HTTP route modules
│   │   ├── core/            # Config, DB, security, middleware, rate limits
│   │   ├── models/          # SQLAlchemy models
│   │   ├── schemas/         # Pydantic request/response schemas
│   │   ├── services/        # Business + ML logic
│   │   ├── jobs/            # AI batch job
│   │   ├── seed_data.py     # Demo data
│   │   └── main.py          # App entry
│   ├── alembic/             # DB migrations
│   ├── Dockerfile
│   ├── gunicorn.conf.py
│   ├── requirements.txt
│   └── .env.example
├── final-frontend/          # Production React SPA
├── nexus-ops/               # UI prototype (mock data; not in Docker Compose)
├── docker-compose.yml
├── run.sh                   # Local: backend :8000 + frontend :3000
├── DEPLOY.md
├── README.md
└── PROJECT_DOCUMENTATION.md # This file
```

## 3. Backend deep dive

### 3.1 Application entry

- **File:** `backend/app/main.py`  
- Mounts routers under `/api/...`, exposes `GET /health` and root.  
- Production uses Gunicorn with Uvicorn workers (`backend/gunicorn.conf.py`).

### 3.2 API surface

| Prefix | Module | Purpose |
|--------|--------|---------|
| `/api/auth` | `api/auth.py` | Register, login, current user (`/me`) |
| `/api/products` | `api/products.py` | Product CRUD (mutations admin) |
| `/api/orders` | `api/orders.py` | Place / list orders |
| `/api/inventory` | `api/inventory.py` | Stock in/out, transactions, thresholds |
| `/api/expenses` | `api/expenses.py` | Expense CRUD |
| `/api/dashboard` | `api/dashboard.py` | Aggregated ops metrics |
| `/api/ai` | `api/ai_insights.py` | Forecasts, stockouts, restock, dead stock, alerts, batch |
| `/api/vendors` | `api/vendors.py` | Vendors, rankings, compare, scorecards |
| `/api/purchase-orders` | `api/purchase_orders.py` | Create / list POs |
| `/health` | `main.py` | Liveness + DB health |

Interactive docs (dev): http://127.0.0.1:8000/docs  

### 3.3 Domain models

Located in `backend/app/models/`:

| Model area | Examples |
|------------|----------|
| Identity | `User` (`customer`, `admin`, `manager`) |
| Catalog & stock | `Product`, `StockTransaction`, `InventorySnapshot` |
| Commerce | `Order`, `OrderItem` |
| Spend | `Expense` (+ category/type enums) |
| Supply | `Vendor`, `VendorProduct`, `VendorPerformanceMetric` |
| Buying | `PurchaseOrder`, `PurchaseOrderItem` |
| AI outputs | `DemandForecast`, `StockoutPrediction`, `RestockingRecommendation`, `DeadStockDetection`, `AIAlert` |
| Jobs | `JobRun` (batch lock / status) |

### 3.4 Services

| Service | Role |
|---------|------|
| `auth_service` | Register, authenticate, JWT issuance |
| `product_service` / `order_service` / `inventory_service` / `expense_service` | Domain CRUD and rules |
| `dashboard_service` | Aggregations for the home dashboard |
| `vendor_service` / `vendor_scoring` / `vendor_ai` | Rankings, scores, delay-oriented intelligence |
| `ml_service` / `ai_persistence_service` | Forecasting, risk, restock, dead stock, persistence |
| `jobs/ai_batch_job.py` | Locked batch execution of AI pipelines |

### 3.5 Security & hardening

| Concern | Implementation |
|---------|----------------|
| Passwords | bcrypt via passlib (`core/security.py`) |
| Sessions | JWT (Bearer; optional HTTPOnly cookie via `JWT_COOKIE_NAME`) |
| Authorization | `get_current_user` / `get_current_admin` in `core/dependencies.py` |
| Login abuse | In-memory rate limit (`RATE_LIMIT_LOGIN_PER_MINUTE`) |
| Production config | Fail-fast validation (`startup_validation.py`, `config.py`) |
| CORS / hosts | Strict origins; Trusted Hosts in production |
| Observability | Structured logging, `/health` with DB check |
| Concurrency | Transaction helpers / row locks for stock-sensitive paths |
| Secrets | Env-based; `.env` gitignored; examples only in `.env.example` |

**Important:** Admin API routes require `role == admin`. The Manager role is stored and seeded but is not given the same API privileges as Admin by the current dependency.

### 3.6 Database migrations (Alembic)

Path: `backend/alembic/versions/`

| Migration | Intent |
|-----------|--------|
| `001_initial_migration` | Base schema |
| `002_add_manager_role_and_b2b_tables` | Manager role + B2B tables |
| `003_add_vendor_intelligence_schema` | Vendor intelligence |
| `004_create_purchase_orders_if_missing` | PO tables safety |
| `005_normalize_userrole_enum` | UserRole enum normalization |

Commands:

```bash
cd backend
alembic upgrade head
python -m app.seed_data   # optional demo data
```

### 3.7 AI / ML design

Documented in detail in `PHASE2_AI.md`. Summary:

| Principle | Meaning |
|-----------|---------|
| Batch, not realtime | Insights generated by jobs / `POST /api/ai/batch-process` |
| Explainable | Stored explanations with recommendations |
| Profit-aware | Restock logic weighs margin and cost, not only demand |
| No paid AI APIs | Prophet, pandas, numpy, scikit-learn-style tooling; optional Prophet with statistical fallback |
| Separated ML | Logic in services; routes only expose results |

Feature set:

1. Demand forecasting (Prophet + fallback)  
2. Stockout risk (velocity-based days-to-zero)  
3. Restock recommendations (weighted factors: demand, risk, margin, cost)  
4. Dead-stock scoring and suggested actions  
5. Alerts for operational follow-up  
6. Vendor scoring / comparison / delay-oriented signals  

## 4. Frontend deep dive (`final-frontend`)

### 4.1 Stack

React 18 + TypeScript + Vite 5 + React Router 6 + Tailwind + Radix/shadcn + Recharts + Framer Motion + Axios + React Hook Form + Zod.

### 4.2 Key pages

| Page | Path (conceptual) | Purpose |
|------|-------------------|---------|
| Login / Register | Auth screens | Credential entry |
| Dashboard | `/` (authenticated) | KPIs and charts |
| Inventory | Inventory route | SKUs and stock actions |
| Vendors | Vendors route | Rankings, compare, sourcing |
| Purchase Orders | PO route | Create / list POs |
| Expenses | Expenses route | Spend tracking and charts |
| AI Insights | AI route | Forecasts, alerts, recommendations |
| Settings | Settings route | Theme (light/dark) |

### 4.3 Auth flow

1. Optional cinematic intro (`CinematicIntro` / `IntroScene`).  
2. Unauthenticated users see Welcome / Sign In (`LoginPage`; `/register` redirects here).  
3. `POST /api/auth/start` with email + password → `needs_onboarding` or `otp_sent`.  
4. New users: `POST /api/auth/onboard` (store name + type) then OTP; existing users go straight to OTP.  
5. `POST /api/auth/verify-otp` returns JWT; stored in `localStorage` as `access_token`.  
6. Axios attaches `Authorization: Bearer …`; `/api/auth/me` hydrates on load/refresh (admin-only).  
7. Authenticated shell: `Layout` + feature routes (`App.tsx`). Non-admins are rejected.  

### 4.4 API client

`final-frontend/src/lib/api.ts` exports typed helpers (`authAPI`, `dashboardAPI`, `aiAPI`, `vendorsAPI`, `purchaseOrdersAPI`, `productsAPI`, `inventoryAPI`, etc.).

- **Dev:** Often proxies `/api` to the backend (Vite).  
- **Production:** Set `VITE_API_URL` at build time (required).  

### 4.5 `nexus-ops` (prototype)

| | final-frontend | nexus-ops |
|--|----------------|-----------|
| Role | Production SPA | Design / Lovable spike |
| Data | Live backend | Mock TS data |
| Deployed | Yes (Compose / run.sh) | No |

Do not treat `nexus-ops` as the live product UI.

## 5. Roles & permissions (technical)

| Role | Typical access |
|------|----------------|
| **Public** | Product list/get; register; login |
| **Authenticated (customer)** | Own orders, `/me` |
| **Admin** | Inventory, expenses, dashboard, AI, vendors, POs, product mutations, all orders |
| **Manager** | Present in schema/seed; not elevated by `get_current_admin` today |

## 6. Local development

### Prerequisites

- Python 3.12  
- Node.js 20+  
- PostgreSQL 14/15  
- npm  

### Quick path

```bash
# Database
createdb marketplace_db
cd backend
python -m venv venv && source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env   # set DATABASE_URL, SECRET_KEY
alembic upgrade head
python -m app.seed_data

# From repo root — both servers
./run.sh
```

| Service | URL |
|---------|-----|
| Frontend | http://localhost:3000 |
| Backend | http://127.0.0.1:8000 |
| OpenAPI | http://127.0.0.1:8000/docs |
| Health | http://127.0.0.1:8000/health |

## 7. Environment variables

### Backend (`backend/.env`)

| Variable | Purpose |
|----------|---------|
| `DATABASE_URL` | PostgreSQL connection string |
| `SECRET_KEY` | JWT signing secret (≥ 32 chars) |
| `ALGORITHM` | JWT algorithm (default HS256) |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | Token lifetime |
| `CORS_ORIGINS` | Allowed browser origins |
| `ENVIRONMENT` | `development` / `production` |
| `DEBUG` | Debug flag |
| `LOG_LEVEL` | Logging verbosity |
| `ALLOWED_HOSTS` | Trusted hosts (production) |
| `AI_BATCH_JOB_TIMEOUT_HOURS` | Stale AI job handling |
| `RATE_LIMIT_LOGIN_PER_MINUTE` | Login rate limit |
| `JWT_COOKIE_NAME` | Optional cookie-based JWT |

### Frontend (`final-frontend/.env`)

| Variable | Purpose |
|----------|---------|
| `VITE_API_URL` | Backend base URL (required for production builds) |

### Docker Compose (root `.env`)

`POSTGRES_USER`, `POSTGRES_PASSWORD`, `POSTGRES_DB`, `SECRET_KEY`, `CORS_ORIGINS`, `VITE_API_URL`, `ALLOWED_HOSTS`, `LOG_LEVEL`

Generate a secret:

```bash
python3 -c "import secrets; print(secrets.token_urlsafe(32))"
```

## 8. Production deployment

Primary guide: **`DEPLOY.md`**.

### Docker Compose (single VPS)

Services in `docker-compose.yml`:

| Service | Role | Ports |
|---------|------|-------|
| `postgres` | DB + volume | Internal |
| `backend` | API | `127.0.0.1:8000` |
| `frontend` | Nginx static SPA | `80` |

```bash
cp .env.example .env
# fill secrets and public URLs
docker compose up -d --build
docker compose exec backend alembic upgrade head
# optional:
docker compose exec backend python -m app.seed_data
```

Put Nginx/Caddy in front for TLS: `/` → frontend, `/api` → backend.

### Split cloud

- Backend + Postgres: Render / Railway / similar  
- Frontend: Vercel / Netlify / static host with `VITE_API_URL` pointing at the API  

### Security checklist (short)

- Strong `POSTGRES_PASSWORD` and `SECRET_KEY`  
- Private GitHub / private hosting as appropriate  
- HTTPS everywhere  
- Restrict `CORS_ORIGINS` and `ALLOWED_HOSTS`  
- Do not commit `.env`  
- Do not seed demo users; create admins only through the auth onboarding flow  

## 9. Data & AI flow (end-to-end)

```
Orders / stock movements / expenses / vendor metrics
        │
        ▼
   PostgreSQL (source of truth)
        │
        ▼
   AI batch job (ml_service + persistence)
        │
        ├── DemandForecast
        ├── StockoutPrediction
        ├── RestockingRecommendation
        ├── DeadStockDetection
        └── AIAlert
        │
        ▼
   GET /api/ai/*  →  final-frontend AI Insights / Dashboard
```

## 10. Testing & verification (practical)

| Check | How |
|-------|-----|
| API up | `curl http://127.0.0.1:8000/health` |
| Docs | Open `/docs` |
| Auth | `POST /api/auth/start` → (onboard if new) → `/verify-otp`; then `GET /api/auth/me` |
| Seed | `python -m app.seed_data` (catalog data only; no demo users) |
| Frontend | Load http://localhost:3000 and complete email + password + OTP |
| Compose | `docker compose ps` + health endpoints |

## 11. Related project docs

| File | Contents |
|------|----------|
| `README.md` | Quick overview and start |
| `QUICK_START.md` | Short setup path |
| `DEPLOY.md` | Production deploy |
| `PHASE2_AI.md` | AI feature design |
| `HARDENING_SUMMARY.md` | Security / reliability work |
| `CONFIGURATION.md` | Configuration deep dive |
| `NO_API_KEYS.md` | Why no third-party AI keys |
| `SYSTEM_AUDIT.md` | Audit notes |

## 12. Roadmap-oriented notes (technical debt / awareness)

- Elevate **Manager** with a dedicated dependency if managers should access admin APIs.  
- Register endpoint can accept a role string—tighten this in production (force customer on public register).  
- AI is batch; schedule `batch-process` via cron if continuous freshness is required.  
- Keep `nexus-ops` archived or clearly labeled to avoid deploying the wrong UI.  

---

# Part C — Quick Reference Cards

## For executives

- **What:** Private B2B ops command center with AI decision support.  
- **Why:** Fewer stockouts, clearer vendor choices, controlled spend, one dashboard.  
- **How hosted:** Your server or cloud; private GitHub repo.  
- **Risk:** Demo passwords and open register role must be hardened before real users.  

## For developers

```text
Clone → Postgres → backend/.env → alembic upgrade → seed → ./run.sh
Frontend: :3000 | Backend: :8000 | Health: /health | Docs: /docs
Production: docker compose up -d --build && alembic upgrade head
```

## For operators (day-to-day)

1. Log in as Admin.  
2. Keep Inventory and POs current.  
3. Log Expenses regularly.  
4. Review Vendors before large buys.  
5. Run / open AI Insights after meaningful sales or stock changes.  
6. Act on high stockout and dead-stock alerts.  

---

*Document generated for the Modern Munim marketplace repository. For deployment specifics, prefer `DEPLOY.md`; for AI math and batch design, prefer `PHASE2_AI.md`.*
