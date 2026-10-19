# Modern Munim — Complete Descriptive Project Report

**Command Center for B2B Operations**

---

## Project at a Glance

| Field | Details |
|-------|---------|
| **Project Name** | Modern Munim (MM) |
| **Problem Solved** | Fragmented B2B operations—inventory, expenses, vendors, and purchase decisions tracked across spreadsheets and disconnected tools, with little data-backed restocking guidance |
| **Target Users** | Admins / owners, managers (role present; limited API privileges), ops / internal users, and stakeholders needing stock, spend, and supplier visibility |
| **Main Features** | Authentication (JWT), product & inventory management, customer orders, expenses, vendor intelligence & rankings, purchase orders, dashboard metrics API, batch AI insights (forecasts, stockouts, restocking, dead stock, alerts), settings (theme) |
| **Frontend** | React 18, TypeScript, Vite 5, Tailwind CSS, React Router 6 (`final-frontend/`) |
| **Backend** | FastAPI 2.0.0 (Python 3.12), SQLAlchemy 2, Alembic, Gunicorn + Uvicorn |
| **Database** | PostgreSQL 15 |
| **Key Technologies** | FastAPI, React, PostgreSQL, JWT/bcrypt, Prophet (optional) + pandas/numpy, Docker Compose, Nginx |
| **Project Status** | Functional full-stack application with Docker deployment support; backend APIs largely complete; frontend fully live for auth, inventory, vendors, and purchase orders; dashboard, expenses, and AI Insights UI currently use mock/static data while backend endpoints exist |

---

## 1. Title Page

| | |
|---|---|
| **Project Title** | Modern Munim (MM) — Command Center for B2B Operations |
| **Tagline** | Unified inventory, expense, vendor, purchase-order, and AI-assisted operations platform |
| **Technology / Domain** | Full-stack web application · B2B operations / inventory & procurement intelligence |
| **Repository** | https://github.com/shukla-pratham/marketplace |
| **Backend API Version** | 2.0.0 |
| **Primary Contributor (from git history)** | shukla-pratham \<shuklapratham758@gmail.com\> |
| **Team Members** | Not explicitly documented beyond the repository author above |
| **Institution / Course** | Not explicitly implemented/documented in the current project |
| **License** | Proprietary (as stated in README) |
| **Report Date** | 10 August 2026 |

---

## 2. Abstract

Modern Munim is a full-stack **B2B operations command center** that consolidates product inventory, stock movements, expense tracking, vendor performance, purchase orders, and batch-generated AI insights into a single web application.

The problem it addresses is operational fragmentation: businesses often manage stock, spending, and suppliers in separate spreadsheets or tools, leading to late stockout discovery, unclear vendor reliability, weak budget visibility, and restocking decisions based on intuition rather than data.

The proposed solution is a self-hosted platform with a **FastAPI** REST backend, **PostgreSQL** persistence, and a **React (Vite)** single-page application. Authentication uses JWT with bcrypt password hashing and role fields (`admin`, `manager`, `customer`). Domain services implement inventory adjustments, orders, expenses, vendor scoring, and an offline-style AI pipeline (Prophet with statistical fallback, plus pandas/numpy) that persists forecasts, stockout predictions, restocking recommendations, dead-stock detections, and alerts.

Major technologies include Python 3.12, FastAPI, SQLAlchemy 2, Alembic, PostgreSQL 15, React 18, TypeScript, Tailwind CSS, Axios, Recharts, Docker Compose, and Nginx.

Key implemented capabilities include secure login/registration, admin-protected operational APIs, vendor rankings and purchase-order creation, and a runnable AI batch job. The overall outcome is a deployable operations platform suitable for demonstration and self-hosted use, with clear separation between completed backend intelligence and frontend screens that still rely partly on mock data.

---

## 3. Introduction

### 3.1 Background

B2B operations teams need continuous visibility into what is in stock, what is being spent, which suppliers perform well, and when to reorder. Traditional approaches rely on spreadsheets, email-based purchase orders, and disconnected accounting or inventory tools. “Munim” historically refers to a bookkeeper or operations keeper; Modern Munim digitizes that role as a private command center.

### 3.2 Context and Problem Area

The project sits in the domain of **internal operations software** (not a public consumer storefront as the primary product). It combines inventory control, expense categorization, supplier intelligence, and analytics-driven recommendations.

### 3.3 Relevance

Digital operations platforms reduce stockouts, free capital tied in dead inventory, and improve purchasing decisions. AI-assisted forecasting and risk scoring—implemented here without paid third-party AI APIs—make the system relevant for academic demonstration of full-stack engineering plus applied ML pipelines.

### 3.4 Motivation

Development motivation, as evidenced by documentation and architecture (Phase 1 core ops + Phase 2 AI/ML), is to unify operational records and add explainable, batch-oriented intelligence on top of the same database of orders, stock, and vendors.

### 3.5 Overview of the Solution

Users authenticate via a React SPA, then manage inventory, vendors, and purchase orders against live APIs. Backend services aggregate dashboard metrics and run AI batch processing that stores insights for later retrieval. Production packaging uses Docker Compose (PostgreSQL + backend + Nginx-served frontend).

---

## 4. Problem Statement

### 4.1 The Problem Being Solved

Operations teams struggle to:

- Discover stockouts too late  
- Identify dead inventory that ties up cash  
- Compare vendor reliability, cost, and lead time objectively  
- Track expenses by category with budget context  
- Maintain purchase-order history outside email/spreadsheets  
- Restock based on data rather than gut feel  

### 4.2 Existing Difficulties / Limitations

Without a unified system, data is siloed, reporting is manual, and AI-style recommendations are unavailable or depend on expensive external APIs. The project documentation explicitly notes no requirement for external AI API keys.

### 4.3 Who Experiences the Problem

Admins/owners, managers, ops staff, and stakeholders who need stock health, cost visibility, and supplier performance in one place.

### 4.4 Why a Software-Based Solution Is Useful

A software system can enforce consistent records, enforce authorization on sensitive mutations, aggregate metrics programmatically, and run repeatable forecasting/scoring jobs against historical order and purchase-order data.

---

## 5. Aim and Objectives

### 5.1 Aim

To design and implement a self-hosted B2B operations platform that unifies inventory, expenses, vendors, purchase orders, and explainable AI-assisted operational insights behind a secure web interface and REST API.

### 5.2 Objectives

1. Build a FastAPI backend with PostgreSQL persistence and Alembic migrations.  
2. Implement JWT authentication and role fields with admin-gated operational endpoints.  
3. Provide product catalog and stock in/out transaction APIs.  
4. Support customer order placement and admin order listing.  
5. Implement expense CRUD with category and type classification.  
6. Implement vendor records, rankings, scorecards, and product sourcing associations.  
7. Support purchase-order creation and listing.  
8. Implement dashboard aggregation endpoints (revenue, expenses, profit, stock status, sales).  
9. Implement batch AI pipelines for demand forecast, stockout risk, restocking, dead stock, and alerts.  
10. Deliver a React SPA for authentication and primary operational workflows.  
11. Package the stack for local development (`run.sh`) and production (Docker Compose).  

### 5.3 Goals Achieved by the Implementation

- Backend API version 2.0.0 with nine router modules plus health checks  
- Seeded demo users, products, vendors, POs, and related data  
- Live frontend workflows for login/register, inventory, vendors, and purchase orders  
- Dockerized backend, frontend (Nginx), and PostgreSQL  

---

## 6. Proposed Solution

### 6.1 How the Project Solves the Problem

Modern Munim stores all operational entities in PostgreSQL and exposes them through authenticated REST APIs. The SPA presents dashboards and management screens. AI services analyze sales and inventory history offline (batch), persist results, and expose them via `/api/ai/*` for decision support.

### 6.2 Overall Approach

Layered architecture:

1. **Presentation** — React SPA (`final-frontend`)  
2. **API** — FastAPI routers with Pydantic validation  
3. **Domain services** — Business rules and ML pipelines  
4. **Data** — SQLAlchemy models + Alembic migrations on PostgreSQL  
5. **Ops** — Docker Compose, Gunicorn, Nginx  

An earlier UI prototype (`nexus-ops/`) exists with mock-only data and is **not** part of the Docker production path.

### 6.3 Main Workflow

1. User opens the web app and completes (or skips) a cinematic intro.  
2. User registers or logs in; JWT is stored (Bearer in `localStorage`).  
3. Authenticated layout provides navigation to Dashboard, Inventory, Vendors, Purchase Orders, Expenses, AI Insights, and Settings.  
4. Inventory/Vendors/PO screens call live APIs; Dashboard/Expenses/AI Insights currently render mock/static UI data.  
5. Admins can trigger AI batch processing via API (`POST /api/ai/batch-process`) or the CLI job module.  

### 6.4 User Interaction

- Forms for login, registration, add SKU, stock adjust, create vendor, place PO  
- Tables and ranking lists for products and vendors  
- Charts on dashboard and expenses pages (frontend mock data today)  
- Settings for theme and motion preferences (client-side)  

### 6.5 Contribution of System Parts

| Part | Contribution |
|------|----------------|
| Auth module | Identity and JWT issuance |
| Products / inventory | Stock truth and SKU catalog |
| Orders | Demand signal for ML and revenue |
| Expenses | Spend tracking API |
| Vendors / POs | Procurement and scoring inputs |
| ML + AI persistence | Forecasts and recommendations |
| Frontend | Operator UX |
| Docker / Nginx | Deployable packaging |

---

## 7. Project Scope

### 7.1 What the Project Currently Covers

- User registration and login  
- Product CRUD (mutations admin-only)  
- Stock in/out and transaction listing (admin)  
- Orders (create, my-orders, admin list)  
- Expenses CRUD (admin API)  
- Dashboard metric APIs (admin)  
- Vendor intelligence APIs and PO create/list  
- AI insight storage and retrieval APIs + batch job  
- React SPA with branded intro and operational pages  
- Local and Docker deployment paths  

### 7.2 Target Users

Admins (full API privileges for ops modules), seeded manager accounts (role exists but not elevated like admin in dependencies), and customer/ops accounts for login and order-related endpoints.

### 7.3 Main Use Cases

1. Admin manages catalog and stock levels.  
2. Admin reviews vendor rankings and creates purchase orders.  
3. Authenticated user places customer orders (API).  
4. Admin logs expenses and views dashboard aggregations (API).  
5. Admin runs AI batch and reads forecasts/alerts (API).  

### 7.4 Functional Boundaries

- Primary product is an **internal ops command center**, not a public marketplace storefront.  
- AI is **batch-oriented**, not realtime streaming on every click.  
- Frontend role-based UI gating is not implemented (auth presence only).  

### 7.5 Outside Current Scope

- Native mobile apps  
- Payment gateway / full ERP replacement  
- Automatic HTTPS reverse proxy baked into Compose (documented separately in DEPLOY.md)  
- Treating `nexus-ops` as production UI  
- Full frontend wiring of dashboard, expenses, and AI APIs (backend exists; UI uses mock/static content)  
- HTTP endpoints for marking POs delivered and for inventory snapshots (service/model exist without full API exposure)  

---

## 8. Key Features

### 8.1 Authentication and User Management

- **Purpose:** Secure access to the platform.  
- **How it works:** Register creates a user (API maps only explicit `admin` role request to admin; otherwise customer). Login uses OAuth2-style password form, verifies bcrypt hash, returns JWT. Optional HTTPOnly cookie if `JWT_COOKIE_NAME` is set.  
- **User interaction:** Login and Register pages; token persisted in `localStorage` as `access_token`.  
- **Technical implementation:** `auth.py`, `auth_service.py`, `security.py`, `dependencies.py`; frontend `auth-context.tsx` and `authAPI`.  
- **Modules:** Backend `api/auth`, `services/auth_service`; frontend `LoginPage`, `RegisterPage`, `lib/auth-context`.  

### 8.2 Product Catalog

- **Purpose:** Maintain sellable/stocked products (name, description, price, stock, threshold).  
- **How it works:** Public GET list/detail; admin POST/PUT/DELETE.  
- **User interaction:** Inventory page lists products, add SKU modal, detail panel.  
- **Technical implementation:** `Product` model with non-negative checks; `product_service` + `products` API.  

### 8.3 Inventory Stock Movements

- **Purpose:** Record stock in/out and thresholds.  
- **How it works:** Admin posts stock-in or stock-out; creates `StockTransaction` and updates `stock_quantity`.  
- **User interaction:** Adjust stock modal on Inventory page.  
- **Modules:** `inventory.py`, `inventory_service.py`, `StockTransaction` model.  

### 8.4 Customer Orders

- **Purpose:** Capture outbound demand and revenue events.  
- **How it works:** Authenticated users create orders; stock decremented; admins list all orders.  
- **User interaction:** Order UI is primarily API-level in the current SPA (no dedicated orders page in `App.tsx` routes).  
- **Modules:** `orders.py`, `order_service.py`, `Order` / `OrderItem`.  

### 8.5 Expense Tracking (Backend Complete; Frontend Mock)

- **Purpose:** Log categorized spend (`inventory` / `operations` / `marketing`; `one_time` / `recurring`).  
- **How it works:** Admin CRUD via `/api/expenses`.  
- **User interaction:** Expenses page shows budget-style charts from **mock data**, not live API.  
- **Modules:** `expenses.py`, `expense_service.py`; frontend `Expenses.tsx` + mock dataset.  

### 8.6 Dashboard Metrics (Backend Complete; Frontend Mock)

- **Purpose:** Leadership view of revenue, expenses, profit, stock status, sales.  
- **How it works:** Aggregation queries in `dashboard_service` exposed under `/api/dashboard/*`.  
- **User interaction:** Dashboard page uses hard-coded KPIs and `@/data/mockData` charts; `dashboardAPI` is defined but unused by pages.  

### 8.7 Vendor Intelligence

- **Purpose:** Rank and compare suppliers; manage vendor catalogs.  
- **How it works:** Vendors store reliability/cost/overall scores; rankings by `overall_score`; scorecards, best-vendor-for-product, compare endpoints; create/delete vendor; add products to vendor.  
- **User interaction:** Vendors page—rankings, radar comparison, products panel, place order, add/delete vendor.  
- **Technical implementation:** `vendor_scoring.py`, `vendor_ai.py`, `vendor_service.py`, vendor models.  

### 8.8 Purchase Orders

- **Purpose:** Create and list procurement orders with line items and delivery dates.  
- **How it works:** Admin POST creates PO with items; GET lists with optional `vendor_id` filter. Status values include created/ordered/delivered/cancelled. Service includes `mark_purchase_order_delivered` but **no dedicated HTTP route** exposes it.  
- **User interaction:** Purchase Orders page lists POs and shows a derived timeline UI.  

### 8.9 AI Insights Pipeline

- **Purpose:** Explainable operational recommendations from historical data.  
- **How it works:** `ml_service` builds sales time series, trends (linear regression), Prophet forecast (fallback to moving average), stockout days/risk, restocking recommendations, dead-stock detection. `ai_persistence_service` stores results and alerts; batch via `POST /api/ai/batch-process` or `app/jobs/ai_batch_job.py` with `JobRun` locking.  
- **User interaction:** AI Insights page currently shows **static** cards and a confidence gauge; live `aiAPI` is largely unused in the UI (alerts client method defined but unused).  

### 8.10 Settings and Theming

- **Purpose:** Client preferences.  
- **How it works:** `SettingsContext` / `useSettings` persist theme, reduced motion, animation intensity, chart density, introSeen to `localStorage`. Theme toggles `.dark` on `document.documentElement`.  
- **Note:** Some settings (e.g., chart density) are stored but not fully applied to charts; intro runs every load despite `introSeen`.  

### 8.11 Health Check and Production Hardening

- **Purpose:** Operability and baseline security.  
- **How it works:** `GET /health` runs `SELECT 1`; CORS; optional Trusted Hosts; login rate limit; structured logging; production startup config validation.  

### 8.12 Cinematic Intro

- **Purpose:** Brand presentation.  
- **How it works:** `CinematicIntro` with optional Three.js rings (`IntroScene`); skip control; ~4.5s experience before auth screens.  

---

## 9. Technology Stack

### 9.1 Frontend Technologies

| Technology | Why / How Used |
|------------|----------------|
| React 18 | SPA UI components and state |
| TypeScript | Typed frontend codebase |
| Vite 5 | Dev server (port 3000), build tool, `/api` proxy to backend |
| React Router 6 | Client routes for auth and app pages |
| Tailwind CSS | Styling of app screens |
| Radix UI / shadcn scaffolding | Dependency and `components/ui` kit present; feature pages mostly custom Tailwind |
| Axios | HTTP client with Bearer token interceptor |
| Recharts | Charts on Dashboard/Expenses (mock data) |
| Framer Motion | Animations (intro / motion helpers) |
| Three.js / React Three Fiber / Drei | Optional 3D intro and AI Insights scene |
| React Hook Form + Zod | Form validation stack available in dependencies |
| Lucide React | Icons |
| Vitest + Testing Library | Test runner (placeholder test only) |

### 9.2 Backend Technologies

| Technology | Why / How Used |
|------------|----------------|
| Python 3.12 | Runtime (Dockerfile base) |
| FastAPI | REST API framework |
| Uvicorn / Gunicorn | Dev ASGI server; production workers |
| SQLAlchemy 2 | ORM |
| Alembic | Schema migrations |
| Pydantic / pydantic-settings | Request schemas and configuration |
| python-jose | JWT create/decode |
| passlib + bcrypt | Password hashing |
| psycopg2-binary | PostgreSQL driver |
| python-multipart | OAuth2 password form login |

### 9.3 Database

PostgreSQL 15 (local or `postgres:15-alpine` in Docker) — primary system of record.

### 9.4 Authentication / Authorization

JWT (HS256 by default), bcrypt hashes, FastAPI dependencies `get_current_user` / `get_current_admin`.

### 9.5 AI / ML

| Technology | Use |
|------------|-----|
| Prophet | Optional demand forecasting |
| pandas / numpy | Time series, trends, scoring inputs |
| Custom statistical logic | Fallback forecast, stockout, restock, dead stock, vendor delay signals |

No paid external AI APIs are required (`NO_API_KEYS.md` / `.env.example` notes).

### 9.6 Deployment

Docker, Docker Compose, Nginx Alpine (static SPA + gzip + security headers), multi-stage frontend build.

### 9.7 Package Managers / Tools

- Backend: `pip` + `requirements.txt`, Python venv  
- Frontend: `npm` + `package-lock.json`  
- Root scripts proxy to `final-frontend`  

### 9.8 Testing Tools

- Backend: scripts such as `test_database_setup.py`, `verify_database_setup.py` (setup verification; not a full unit suite)  
- Frontend: Vitest with one example assertion  

---

## 10. System Architecture

### 10.1 Overview Diagram

```text
┌──────────────────────────────┐
│  User (Browser)              │
└──────────────┬───────────────┘
               │ HTTP(S)
               ▼
┌──────────────────────────────┐
│  final-frontend              │
│  React + Vite SPA            │
│  Nginx (production :80)      │
│  Auth, Layout, Pages         │
└──────────────┬───────────────┘
               │ /api/* JSON + JWT Bearer
               ▼
┌──────────────────────────────┐
│  FastAPI Backend (:8000)     │
│  Routers → Services          │
│  Auth, RBAC (admin checks)   │
│  ML batch + persistence      │
└──────────────┬───────────────┘
               │ SQLAlchemy
               ▼
┌──────────────────────────────┐
│  PostgreSQL 15               │
│  users, products, orders,    │
│  expenses, vendors, POs,     │
│  AI tables, job_runs, ...    │
└──────────────────────────────┘

Optional / parallel:
  python -m app.jobs.ai_batch_job  →  AI services  →  DB
  nexus-ops/  →  mock UI only (not in Compose)
```

### 10.2 Data Flow (Example: Stock Adjustment)

1. Admin opens Inventory → Adjust Stock.  
2. Frontend calls `POST /api/inventory/stock-in` or `stock-out` with Bearer token.  
3. `get_current_admin` validates JWT and `role == admin`.  
4. Inventory service updates product quantity and inserts `stock_transactions`.  
5. JSON response returned; UI refreshes product list.  

### 10.3 AI Data Flow

1. Admin or cron invokes batch process.  
2. Job acquires `job_runs` lock.  
3. ML analyzes completed order history per product; vendor intelligence may update scores.  
4. Results written to forecast/prediction/recommendation/detection/alert tables.  
5. Clients read via `/api/ai/*` (admin).  

### 10.4 External Services

Not explicitly implemented beyond optional Prophet library (local). No cloud AI provider integration in code.

---

## 11. Project Structure

```text
marketplace/
├── backend/                      # FastAPI application
│   ├── app/
│   │   ├── api/                  # Route modules (auth, products, orders, …)
│   │   ├── core/                 # Config, DB, security, middleware, rate limit, logging
│   │   ├── models/               # SQLAlchemy models
│   │   ├── schemas/              # Pydantic schemas
│   │   ├── services/             # Business + ML logic
│   │   ├── jobs/                 # AI batch job entry
│   │   ├── seed_data.py          # Demo seed script
│   │   └── main.py               # FastAPI app entry
│   ├── alembic/                  # Migrations (001–005)
│   ├── Dockerfile
│   ├── gunicorn.conf.py
│   ├── requirements.txt
│   └── .env.example
├── final-frontend/               # Production-oriented React SPA
│   ├── src/
│   │   ├── components/           # Login, Register, Layout, Intro, ui/
│   │   ├── pages/                # Dashboard, Inventory, Vendors, …
│   │   ├── lib/                  # api.ts, auth-context
│   │   ├── contexts/             # Settings
│   │   ├── hooks/                # useSettings, toast, mobile
│   │   ├── data/                 # mockData used by some pages
│   │   ├── App.tsx, main.tsx
│   ├── nginx.conf
│   ├── Dockerfile
│   └── package.json
├── nexus-ops/                    # Earlier mock prototype (not Dockerized)
├── docker-compose.yml            # postgres + backend + frontend
├── run.sh                        # Local: backend :8000 + frontend :3000
├── .env.example                  # Compose env template
├── DEPLOY.md                     # Production deployment guide
├── README.md                     # Project overview
├── PROJECT_DOCUMENTATION.md      # Existing product/tech docs
└── PROJECT_REPORT.md             # This report
```

**Important directories explained**

- `backend/app/api` — HTTP endpoints only; thin controllers over services.  
- `backend/app/services` — Domain rules and AI logic.  
- `backend/app/models` — Persistence schema.  
- `final-frontend/src/pages` — Route-level screens.  
- `final-frontend/src/lib/api.ts` — Central Axios API surface.  
- `nexus-ops` — Alternate Lovable-style UI with fake login and mock dashboards; not the deployed frontend.  

---

## 12. Functional Modules

### 12.1 Auth Module

- **Purpose:** Identity.  
- **Responsibilities:** Register, login, `/me`.  
- **Data:** `users` table.  
- **Interactions:** Supplies JWT for all protected modules.  

### 12.2 Catalog & Inventory Module

- **Purpose:** Products and stock truth.  
- **Components:** products API, inventory API, Inventory page.  
- **Data:** `products`, `stock_transactions` (`inventory_snapshots` model exists without API).  

### 12.3 Orders Module

- **Purpose:** Outbound sales events.  
- **Data:** `orders`, `order_items`.  
- **Interactions:** Feeds ML sales time series and dashboard revenue.  

### 12.4 Expenses Module

- **Purpose:** Spend records.  
- **Data:** `expenses`.  
- **Frontend:** Mock visualization only today.  

### 12.5 Dashboard Module

- **Purpose:** Aggregated KPIs via API.  
- **Frontend:** Mock charts/KPIs today.  

### 12.6 Vendor & Procurement Module

- **Purpose:** Supplier intelligence and buying.  
- **Data:** `vendors`, `vendor_products`, `vendor_performance_metrics`, `purchase_orders`, `purchase_order_items`.  
- **Interactions:** Scoring from PO history; UI create PO from vendor products.  

### 12.7 AI Insights Module

- **Purpose:** Batch analytics and alerts.  
- **Data:** AI forecast tables + `job_runs`.  
- **Interactions:** Consumes orders/products; vendor batch may update scores.  

### 12.8 Presentation / Settings Module

- **Purpose:** UX shell, theme, intro.  
- **Data:** Browser `localStorage` only.  

---

## 13. User Roles and Permissions

### 13.1 Roles Defined

From `UserRole` enum in `backend/app/models/user.py`:

| Role | Value | Notes |
|------|-------|-------|
| Customer | `customer` | Default; can authenticate, place orders, view own orders |
| Admin | `admin` | Full operational API access via `get_current_admin` |
| Manager | `manager` | Seeded and stored; **no dedicated dependency elevates manager** to admin APIs |

### 13.2 What Each Role Can Do (API)

| Capability | Public | Any authenticated | Admin only |
|------------|--------|-------------------|------------|
| Register / login | ✓ | | |
| List/get products | ✓ | | |
| `/api/auth/me`, create order, my-orders | | ✓ | |
| Product mutations, inventory, expenses, dashboard, AI, vendors, POs, list all orders | | | ✓ |

### 13.3 Frontend Authorization

- Gate is **logged-in vs not logged-in** only.  
- `user.role` is not used to hide routes.  
- Register UI sends `role: 'admin'` (backend will honor admin if that field equals admin).  
- Purchase Orders page may show a message when API returns 403.  

### 13.4 Restrictions Summary

Manager accounts behave like customers for authorization purposes unless role string equals `admin`. This is an important gap relative to documentation that describes managers as B2B actors.

---

## 14. Database Design

### 14.1 Technology

PostgreSQL 15 with SQLAlchemy 2 models and Alembic migrations `001`–`005`.

### 14.2 Schema Description (Implemented Models)

**users**  
- PK `id`  
- `email` unique, `password_hash`, `role` (`customer`/`admin`/`manager`), `created_at`  
- Rel: orders  

**products**  
- PK `id`  
- `name`, `description`, `price`, `stock_quantity`, `stock_threshold`, timestamps  
- Checks: quantities and price ≥ 0  

**orders** / **order_items**  
- Order: `user_id` FK, `total_amount`, `status` (pending/completed/cancelled)  
- Items: `order_id`, `product_id`, `quantity`, `price_at_purchase`  

**expenses**  
- `category`, `description`, `amount`, `expense_type`, optional `product_id`  

**stock_transactions**  
- `product_id`, `quantity_change`, `transaction_type` (`in`/`out`), `reason`  

**vendors**  
- Scores (`reliability_score`, `cost_score`, `overall_score`), `avg_lead_time_days`, `is_active`  

**vendor_products**  
- `vendor_id`, `product_id`, `unit_cost`, `min_order_qty`, `lead_time_days`  

**vendor_performance_metrics**  
- Per-date performance fields (lead time, on-time rate, costs, delays, etc.)  

**purchase_orders** / **purchase_order_items**  
- `po_number` unique, status, costs, order/promised/actual delivery dates, `delay_days`  
- Items: quantity, unit/total cost, product FK  

**AI tables**  
- `demand_forecasts`, `stockout_predictions`, `restocking_recommendations`, `dead_stock_detections`, `ai_alerts`  

**inventory_snapshots**  
- Historical quantity/value snapshots — **no API routes**  

**job_runs**  
- Batch job status/locking (`lock_id` unique)  

### 14.3 Migration Notes

Migration `002` historically introduced a legacy `suppliers` concept; runtime models use `vendors` from later migrations. Enum normalization in `005` maps uppercase role labels to lowercase values.

### 14.4 Application Interaction

Services open SQLAlchemy sessions; APIs depend on DB session injection. Seed script populates demo entities. Migrations are **not** auto-run on container start—operators run `alembic upgrade head`.

---

## 15. API Documentation

Base (dev): `http://127.0.0.1:8000`  
Interactive docs: `/docs` (FastAPI Swagger UI)

### 15.1 Summary Table

| Method | Endpoint | Purpose | Authentication |
|--------|----------|---------|----------------|
| GET | `/` | API welcome + version | Public |
| GET | `/health` | App + DB health | Public |
| POST | `/api/auth/start` | Email+password → onboarding or OTP | Public |
| POST | `/api/auth/onboard` | New admin + store fields → OTP | Public |
| POST | `/api/auth/verify-otp` | OTP → JWT admin session | Public |
| GET | `/api/auth/me` | Current admin profile | Admin |
| GET | `/api/products` | List products | Public |
| GET | `/api/products/{id}` | Product detail | Public |
| POST | `/api/products` | Create product | Admin |
| PUT | `/api/products/{id}` | Update product | Admin |
| DELETE | `/api/products/{id}` | Delete product | Admin |
| POST | `/api/orders` | Create order | Admin |
| GET | `/api/orders` | List all orders | Admin |
| GET | `/api/orders/my-orders` | Current admin orders | Admin |
| GET | `/api/orders/{id}` | Order detail | Admin |
| POST | `/api/inventory/stock-in` | Increase stock | Admin |
| POST | `/api/inventory/stock-out` | Decrease stock | Admin |
| GET | `/api/inventory/transactions` | List stock transactions | Admin |
| PUT | `/api/inventory/products/{id}/threshold` | Update threshold | Admin |
| GET | `/api/expenses` | List expenses | Admin |
| POST | `/api/expenses` | Create expense | Admin |
| PUT | `/api/expenses/{id}` | Update expense | Admin |
| DELETE | `/api/expenses/{id}` | Delete expense | Admin |
| GET | `/api/dashboard/revenue` | Revenue metrics | Admin |
| GET | `/api/dashboard/expenses` | Expense breakdown | Admin |
| GET | `/api/dashboard/profit` | Profit metrics | Admin |
| GET | `/api/dashboard/stock-status` | Stock status | Admin |
| GET | `/api/dashboard/sales` | Sales metrics | Admin |
| GET | `/api/ai/forecasts` | Demand forecasts | Admin |
| GET | `/api/ai/stockout-predictions` | Stockout predictions | Admin |
| GET | `/api/ai/restocking-recommendations` | Restock recommendations | Admin |
| GET | `/api/ai/dead-stock-detections` | Dead stock detections | Admin |
| GET | `/api/ai/alerts` | AI alerts | Admin |
| PUT | `/api/ai/alerts/{id}/read` | Mark alert read | Admin |
| GET | `/api/ai/products/{id}/insights` | Product AI insights | Admin |
| POST | `/api/ai/batch-process` | Run AI batch | Admin |
| POST | `/api/vendors` | Create vendor | Admin |
| DELETE | `/api/vendors/{id}` | Delete vendor | Admin |
| GET | `/api/vendors/rankings` | Ranked vendors | Admin |
| GET | `/api/vendors/best-for-product/{product_id}` | Best vendor | Admin |
| GET | `/api/vendors/{id}/performance` | Performance series | Admin |
| GET | `/api/vendors/compare-for-product/{product_id}` | Compare vendors | Admin |
| GET | `/api/vendors/{id}/products` | Vendor catalog | Admin |
| POST | `/api/vendors/{id}/products` | Add vendor product | Admin |
| GET | `/api/vendors/{id}/scorecard` | Scorecard | Admin |
| POST | `/api/purchase-orders` | Create PO | Admin |
| GET | `/api/purchase-orders` | List POs | Admin |

### 15.2 Request / Response Notes

- Login expects form fields `username` (email) and `password`; response includes access token.  
- Protected routes expect `Authorization: Bearer <token>` (or configured cookie).  
- Validation errors return structured FastAPI/Pydantic error payloads via custom exception handlers.  

---

## 16. Detailed Working / Workflow

### 16.1 First-Time Local Use

1. Create PostgreSQL database and configure `backend/.env`.  
2. Run `alembic upgrade head` and optionally `python -m app.seed_data`.  
3. Start backend (`uvicorn`) and frontend (`npm run dev`) or `./run.sh`.  
4. Open `http://localhost:3000`.  

### 16.2 Authentication Workflow

1. Cinematic intro completes.  
2. User submits login credentials.  
3. Backend verifies password and returns JWT.  
4. Frontend stores token and calls `/api/auth/me`.  
5. App renders authenticated `Layout` and redirects to `/dashboard`.  

### 16.3 Inventory Workflow

1. Inventory page loads `GET /api/products`.  
2. Admin adds SKU via `POST /api/products`.  
3. Admin adjusts stock via stock-in/out endpoints.  
4. Table updates with new quantities and status badges.  

### 16.4 Vendor Purchase Workflow

1. Vendors page loads rankings.  
2. User opens a vendor’s products.  
3. User places a purchase order → `POST /api/purchase-orders`.  
4. Purchase Orders page lists POs via `GET /api/purchase-orders`.  

### 16.5 AI Batch Workflow

1. Admin calls `POST /api/ai/batch-process` or runs the job module.  
2. Job lock prevents concurrent runs.  
3. ML writes forecasts and related rows.  
4. Admin fetches results from `/api/ai/*` (available via API; SPA page not fully wired).  

---

## 17. UI/UX Description

### 17.1 Main Screens

| Screen | Purpose |
|--------|---------|
| Cinematic Intro | Branded onboarding animation |
| Login / Register | Authentication |
| Dashboard | KPI cards + charts (**mock data**) |
| Inventory | Live product table, modals for add/adjust |
| Vendors | Rankings, compare radar, order placement |
| Purchase Orders | PO list and status timeline UI |
| Expenses | Budget vs actual UI (**mock data**) |
| AI Insights | Insight cards + optional 3D (**static content**) |
| Settings | Theme and motion preferences |

### 17.2 Navigation

Sidebar in `Layout.tsx` with routes to all authenticated pages, theme toggle, logout, and header “Add” shortcuts to inventory/vendors.

### 17.3 Forms, Tables, Charts

- Forms: login, register, add SKU, stock adjust, vendor/product/PO actions  
- Tables: inventory products; vendor lists  
- Charts: Recharts area/bar/pie/line on Dashboard and Expenses (mock)  
- Modals: inventory add/adjust; vendor-related panels  

### 17.4 Notifications / Feedback

Axios 401 interceptor clears token and redirects to `/`. PO page surfaces 403 messaging. Toast helpers exist in the UI kit but are not central to app pages.

### 17.5 Responsive Behavior

Tailwind-based layout intended for desktop and mobile browser use. Native apps are out of scope.

### 17.6 Design System Note

A full shadcn `components/ui` library is scaffolded; primary screens largely use custom Tailwind rather than those primitives.

---

## 18. Security

### 18.1 Implemented Mechanisms

| Area | Implementation |
|------|----------------|
| Authentication | JWT access tokens |
| Password handling | bcrypt (passlib); password truncated to 72 bytes |
| Authorization | Admin dependency on sensitive routes |
| Session/token | Bearer header; optional HTTPOnly cookie |
| Login protection | In-memory rate limit per IP |
| CORS | Configurable allowed origins |
| Host protection | Optional `TrustedHostMiddleware` |
| Secrets | Environment variables; `.env` gitignored; examples only |
| Production | Startup validation for required secrets |
| Frontend headers (Nginx) | `X-Frame-Options`, `X-Content-Type-Options`, `Referrer-Policy` |

### 18.2 Limitations / Potential Vulnerabilities

- **JWT in `localStorage`** — vulnerable to XSS token theft compared with HTTPOnly cookies (cookie mode optional but not default).  
- **Dev bcrypt rounds = 4** — weaker hashing when `ENVIRONMENT=development`.  
- **In-memory rate limit** — not shared across Gunicorn workers.  
- **Manager role unused** for elevation — misleading if assumed privileged.  
- **Public product read APIs** — intentional but exposes catalog without auth.  
- **Register can request admin** — frontend always sends `role: 'admin'`; backend accepts admin registration when role is admin (significant risk if exposed publicly without further controls).  
- **Demo passwords** in seed docs are weak — must be changed for real deployments.  
- **No evidence** of CSRF tokens for cookie mode, content-security-policy beyond basic Nginx headers, or automated security scanning in-repo.  

---

## 19. Error Handling and Validation

### 19.1 Backend

- Pydantic schemas validate request bodies.  
- Custom handlers for validation errors, HTTP exceptions, and general exceptions in `main.py`.  
- Auth failures return 401; non-admin access to admin routes returns 403.  
- Vendor delete blocked when purchase orders exist (business rule).  

### 19.2 Frontend

- Login/register forms collect email/password; API errors surface in UI flows.  
- Loading spinner while auth bootstraps.  
- Axios timeout 10s; 401 global redirect.  
- Empty/error handling varies by page (e.g., PO 403 message).  

### 19.3 Database Errors

Handled primarily through SQLAlchemy exceptions within services/handlers; exact user messaging depends on exception handler formatting. Dedicated DB health reported by `/health`.

---

## 20. Performance and Optimization

### 20.1 Identified Techniques

- Gunicorn worker recycling (`max_requests` + jitter)  
- Worker count clamped (2–4) via config  
- Nginx gzip and long-cache for static assets; `index.html` no-cache  
- Vite production build drops `console`/`debugger`  
- AI designed as **batch**, avoiding heavy ML on every request  
- Inventory/PO paths use transactional patterns and locking where implemented in vendor/PO services  
- Dev bcrypt rounds reduced for faster local auth (tradeoff vs security)  

### 20.2 Not Explicitly Implemented / Limited

- No Redis or distributed cache layer found  
- No frontend code-splitting strategy documented beyond Vite defaults  
- React Query is a dependency but **not wired** in `App.tsx`  
- Dashboard/AI frontend does not yet leverage live APIs (so end-to-end optimization of those views is incomplete)  

---

## 21. Testing

| Type | Status |
|------|--------|
| Frontend unit tests | Vitest configured; only `example.test.ts` (`expect(true).toBe(true)`) |
| Backend automated unit/integration suite | Not present as a comprehensive pytest suite in the explored tree |
| DB verification scripts | `verify_database_setup.py`, `test_database_setup.py`, related markdown results |
| E2E tests | Not explicitly implemented/documented |
| Manual testing | Supported via SPA admin onboarding + OTP, Swagger `/docs`, and local run scripts |

**Conclusion:** Automated test coverage is minimal; verification relies heavily on manual exercise and setup scripts.

---

## 22. Installation and Setup

### 22.1 Prerequisites

- Python 3.12  
- Node.js 20+  
- PostgreSQL 15  
- npm  
- (Production) Docker + Docker Compose V2  

### 22.2 Database Setup

```bash
createdb marketplace_db
cd backend
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env   # set DATABASE_URL, SECRET_KEY
alembic upgrade head
python -m app.seed_data   # optional
```

Helper scripts/docs also exist: `setup_local_postgres.sh`, `SETUP_DATABASE.md`, `SETUP_LOCAL_DB.md`.

### 22.3 Backend Run

```bash
cd backend
source venv/bin/activate
uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

### 22.4 Frontend Run

```bash
cd final-frontend
npm install
npm run dev
```

Frontend: `http://localhost:3000` (proxies `/api` → `127.0.0.1:8000`).

### 22.5 One-Command Dev

```bash
./run.sh
```

### 22.6 Environment Variables

**Backend (`backend/.env`):** `DATABASE_URL`, `SECRET_KEY`, `ALGORITHM`, `ACCESS_TOKEN_EXPIRE_MINUTES`, `CORS_ORIGINS`, `LOG_LEVEL`, `ENVIRONMENT`, `DEBUG`, `ALLOWED_HOSTS`, `AI_BATCH_JOB_TIMEOUT_HOURS`, `RATE_LIMIT_LOGIN_PER_MINUTE`, `JWT_COOKIE_NAME`

**Frontend:** `VITE_API_URL` (required in production builds)

**Compose (`.env`):** `POSTGRES_USER`, `POSTGRES_PASSWORD`, `POSTGRES_DB`, `SECRET_KEY`, `CORS_ORIGINS`, `VITE_API_URL`, `ALLOWED_HOSTS`, `LOG_LEVEL`

### 22.7 Authentication (admin-only)

No seeded demo credentials. Sign in via email → password → (store onboarding if new) → email OTP → JWT admin session. Optional catalog seed (`python -m app.seed_data`) does **not** create users.

### 22.8 Build Commands

```bash
cd final-frontend && npm run build
cd final-frontend && npm run preview
cd final-frontend && npm test
```

---

## 23. Deployment

Deployment **is implemented** via Docker Compose and documented in `DEPLOY.md`.

### 23.1 Compose Services

1. **postgres** — PostgreSQL 15 Alpine + volume + healthcheck  
2. **backend** — built from `backend/Dockerfile`, Gunicorn on `:8000`, healthcheck against `/health`  
3. **frontend** — multi-stage Node build + Nginx Alpine on `:80`  

### 23.2 Typical Production Steps

```bash
cp .env.example .env
# set POSTGRES_PASSWORD, SECRET_KEY, CORS_ORIGINS, VITE_API_URL, ALLOWED_HOSTS
docker compose up -d --build
docker compose exec backend alembic upgrade head
docker compose exec backend python -m app.seed_data   # optional
```

### 23.3 HTTPS / Reverse Proxy

Not fully automated inside Compose; `DEPLOY.md` describes host Nginx/Caddy proxying frontend `:80` and backend `:8000`, including path `/api`.

### 23.4 Split Deploy

`DEPLOY.md` also discusses splitting backend (e.g., Render/Railway) and frontend (e.g., Vercel)—as guidance, not in-repo platform-specific configs beyond Docker.

### 23.5 CI/CD

Not explicitly implemented/documented as a pipeline in the repository (no GitHub Actions workflow found in the explored project root set).

---

## 24. Advantages

1. **Single operational source of truth** for products, stock, vendors, and POs versus scattered spreadsheets.  
2. **Explainable, self-hosted AI** without paid external AI APIs.  
3. **Clear API layer** enabling Swagger exploration and future clients.  
4. **Role field and admin guards** on sensitive mutations.  
5. **Dockerized** path for reproducible deployment.  
6. **Batch ML design** keeps interactive API latency manageable.  
7. **Vendor scoring and comparison** support better procurement decisions than manual ranking.  
8. **Seed data** accelerates demos and evaluation.  

---

## 25. Limitations

1. Dashboard, Expenses, and AI Insights **UI not wired** to live APIs (mock/static).  
2. Manager role **not privileged** in API dependencies.  
3. PO delivery workflow service method **not exposed** via HTTP.  
4. Inventory snapshots model **without API**.  
5. No comprehensive automated test suite.  
6. Login rate limiting is process-local.  
7. Open admin registration risk if API is publicly reachable.  
8. JWT in localStorage XSS exposure.  
9. Frontend intro cannot be skipped across reloads via stored preference (preference written but not used to skip).  
10. `nexus-ops` may confuse newcomers though it is not production.  
11. Legacy migration artifacts (`suppliers`) vs current `vendors` naming.  
12. Scalability of AI batch and in-memory limits not proven for large multi-tenant SaaS.  
13. No native mobile application.  
14. Payment/ERP breadth explicitly out of scope.  

---

## 26. Future Enhancements

### Short-term

- Wire Dashboard, Expenses, and AI Insights pages to existing APIs.  
- Enforce frontend route guards by role; stop unrestricted admin self-registration in production.  
- Skip cinematic intro when `introSeen` is set.  
- Expose PO delivery endpoint and surface status updates in UI.  
- Replace placeholder Vitest with real component/API tests.  

### Medium-term

- Elevate or clearly define Manager permissions.  
- Distributed rate limiting (e.g., Redis).  
- Prefer HTTPOnly secure cookies for tokens.  
- Cron-based scheduled AI jobs in deployment.  
- Apply settings (chart density, animation intensity) consistently.  
- Add inventory snapshot APIs and historical stock charts.  

### Long-term

- Multi-tenant organizations and audit logs.  
- Deeper ERP/accounting integrations.  
- Real-time notifications for critical stockout alerts.  
- Mobile clients against the same API.  
- Advanced forecasting model management and backtesting UI.  

---

## 27. Challenges and Development Considerations

| Area | Consideration evident in the project |
|------|--------------------------------------|
| Architecture | Separating Phase 1 CRUD from Phase 2 AI while sharing one DB |
| Database | Evolving schema across five migrations; vendor vs earlier supplier concepts |
| Authentication | JWT + optional cookies; bcrypt compatibility fallbacks |
| Authorization | Role enum richer than enforced privileges |
| API integration | Frontend partial wiring creates split brain (live vs mock) |
| State management | Local React state + localStorage; React Query unused |
| Scalability | In-memory rate limits; batch job locking; worker count caps |
| Security | Production validation vs open registration and token storage choices |
| Deployment | Manual migrations; reverse proxy documented separately |
| Third-party | Avoiding paid AI APIs by embedding Prophet/pandas with fallbacks |
| UX consistency | Scaffolded shadcn kit vs custom screens; prototype `nexus-ops` retained |

---

## 28. Results / Outcome

### Successfully Implemented

- Full FastAPI backend (v2.0.0) with auth, products, orders, inventory, expenses, dashboard, AI, vendors, and purchase orders  
- PostgreSQL schema + Alembic migrations + seed data  
- Vendor scoring and AI batch pipelines with persisted outputs  
- React SPA with branded intro, auth, and live Inventory/Vendors/PO flows  
- Docker Compose production packaging and deployment documentation  

### What the System Can Currently Accomplish

- Authenticate users and protect admin operations at the API layer  
- Manage SKUs and stock movements  
- Rank vendors and create purchase orders from the UI  
- Compute and store AI operational insights via batch jobs  
- Serve health checks and run in containerized environments  

### Alignment with Objectives

Core aim—an ops command center with inventory, expenses, vendors, POs, and AI—is achieved at the **backend and data** layers. The **frontend** fully demonstrates several workflows and partially demonstrates others via mock UI, so end-to-end product completeness is high for procurement/inventory and partial for analytics screens.

---

## 29. Conclusion

Modern Munim addresses the fragmentation of B2B operational data by providing a self-hosted command center for inventory, spending, suppliers, purchase orders, and batch AI recommendations. Built with **FastAPI**, **PostgreSQL**, and **React/Vite**, and packaged with **Docker Compose**, it demonstrates a complete layered architecture from authentication through domain services to optional Prophet-based forecasting with statistical fallbacks.

The system is effective as a demonstration and self-hosted foundation: administrators can manage stock and vendors, create purchase orders, and run AI batch intelligence against real database entities. Remaining gaps—especially frontend wiring of dashboard/expenses/AI pages, manager authorization, and stronger production auth defaults—define a clear path for maturation without changing the project’s core value proposition.

With continued integration hardening and test coverage, Modern Munim has strong potential as a practical internal operations platform and as a comprehensive full-stack + applied-ML academic project.

---

## 30. References

Resources actually relevant to technologies and docs present in this repository:

1. FastAPI Documentation — https://fastapi.tiangolo.com/  
2. SQLAlchemy 2.0 Documentation — https://docs.sqlalchemy.org/  
3. Alembic Documentation — https://alembic.sqlalchemy.org/  
4. PostgreSQL 15 Documentation — https://www.postgresql.org/docs/15/  
5. Pydantic Documentation — https://docs.pydantic.dev/  
6. React Documentation — https://react.dev/  
7. Vite Documentation — https://vitejs.dev/  
8. React Router Documentation — https://reactrouter.com/  
9. Tailwind CSS Documentation — https://tailwindcss.com/  
10. Axios Documentation — https://axios-http.com/  
11. Recharts Documentation — https://recharts.org/  
12. Prophet (Meta) Documentation — https://facebook.github.io/prophet/  
13. pandas Documentation — https://pandas.pydata.org/docs/  
14. python-jose — https://python-jose.readthedocs.io/  
15. Passlib Documentation — https://passlib.readthedocs.io/  
16. Docker Documentation — https://docs.docker.com/  
17. Nginx Documentation — https://nginx.org/en/docs/  
18. Gunicorn Documentation — https://docs.gunicorn.org/  
19. Project README — `/Volumes/bheekh/marketplace/README.md`  
20. Project Technical Documentation — `/Volumes/bheekh/marketplace/PROJECT_DOCUMENTATION.md`  
21. Deployment Guide — `/Volumes/bheekh/marketplace/DEPLOY.md`  
22. Phase 2 AI Notes — `/Volumes/bheekh/marketplace/PHASE2_AI.md`  
23. GitHub Repository — https://github.com/shukla-pratham/marketplace  

---

*End of Report*
