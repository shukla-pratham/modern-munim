# Modern Munim

**Command Center for B2B Operations**

Modern Munim (MM) is a full-stack B2B operations platform for inventory, expenses, vendor management, purchase orders, and AI-powered insights. It provides a single dashboard for admins, managers, and ops teams to manage products, stock, vendors, and spending with forecasting and recommendations.

---

## About the Project

Modern Munim unifies:

- **Inventory** — Products, SKUs, stock levels, and adjustments
- **Expenses** — Categorised spending (inventory, operations, marketing) with budgets
- **Vendors** — Supplier rankings, comparison, performance metrics, and product sourcing
- **Purchase orders** — Create and track POs with delivery and cost data
- **AI insights** — Demand forecasts, stockout predictions, restocking recommendations, dead-stock detection, and alerts

The app supports role-based access (Admin, Manager, Customer) and is built for both local development and production deployment with Docker.

---

## Tech Stack

### Backend

| Technology | Purpose |
|------------|--------|
| **Python 3.12** | Runtime |
| **FastAPI** | REST API framework |
| **SQLAlchemy 2** | ORM and database layer |
| **PostgreSQL 15** | Primary database |
| **Alembic** | Database migrations |
| **Pydantic** | Validation and settings |
| **python-jose** | JWT tokens |
| **passlib (bcrypt)** | Password hashing |
| **Gunicorn + Uvicorn** | Production ASGI server |
| **Prophet** | Time-series forecasting (optional) |
| **pandas / numpy** | Data processing and ML pipelines |

### Frontend

| Technology | Purpose |
|------------|--------|
| **React 18** | UI framework |
| **TypeScript** | Typing |
| **Vite 5** | Build tool and dev server |
| **React Router 6** | Client-side routing |
| **Tailwind CSS** | Styling |
| **Radix UI** | Accessible components (dialogs, tabs, etc.) |
| **Recharts** | Charts (dashboard, expenses, vendor comparison) |
| **Framer Motion** | Animations |
| **React Hook Form + Zod** | Forms and validation |
| **Axios** | HTTP client |
| **Lucide React** | Icons |

### DevOps & Deployment

| Technology | Purpose |
|------------|--------|
| **Docker** | Backend and frontend containers |
| **Docker Compose** | Postgres + backend + frontend orchestration |
| **Nginx (Alpine)** | Static frontend and gzip in production |
| **PostgreSQL 15 (Alpine)** | Database in Docker |

---

## Project Structure

```
marketplace/
├── backend/                 # FastAPI application
│   ├── app/
│   │   ├── api/             # Route modules (auth, products, orders, inventory, expenses, dashboard, ai_insights, vendors, purchase_orders)
│   │   ├── core/            # Config, database, security, middleware, logging, rate limiting
│   │   ├── models/          # SQLAlchemy models
│   │   ├── schemas/         # Pydantic schemas
│   │   ├── services/        # Business logic (auth, ML, vendor scoring, etc.)
│   │   └── main.py
│   ├── alembic/             # Migrations
│   ├── Dockerfile
│   ├── gunicorn.conf.py
│   ├── requirements.txt
│   └── .env.example
├── final-frontend/         # React (Vite) application
│   ├── src/
│   │   ├── components/      # Layout, Login, Register, UI
│   │   ├── pages/           # Dashboard, Inventory, Vendors, Purchase Orders, Expenses, AI Insights, Settings
│   │   ├── lib/             # API client
│   │   ├── contexts/        # Settings (theme)
│   │   └── main.tsx, App.tsx
│   ├── nginx.conf           # Production static + SPA fallback
│   ├── Dockerfile
│   ├── package.json
│   └── vite.config.ts
├── docs/                    # All project documentation
│   ├── architecture/        # System design, migration, AI layer
│   ├── deployment/          # Deploy guide, checklist, runbook
│   ├── guides/              # Configuration, database setup
│   └── reports/             # Audits, status reports
├── docker-compose.yml       # Postgres + backend + frontend
├── run.sh                   # Local dev: start backend + frontend
├── .env.example             # Example env for Docker Compose
└── README.md                # This file
```

---

## Features

- **Authentication** — Register, login, JWT (Bearer or optional HTTPOnly cookie), role-based routes
- **Dashboard** — Sales, outbound, expense breakdown, high-level metrics
- **Inventory** — Product list, add SKU, stock in/out, detail panel
- **Vendors** — Ranked list, vendor comparison (radar + scores), inventory & place order per vendor
- **Purchase orders** — List, filter by vendor, create PO with items and delivery date
- **Expenses** — By category/type, charts, budget vs actual
- **AI insights** — Forecasts, stockout predictions, restocking recommendations, dead-stock detection, alerts
- **Settings** — Theme (light/dark)
- **Production** — Health check, structured logging, CORS, rate-limited login, optional trusted-host and secure cookies

---

## Prerequisites

- **Local dev:** Python 3.12, Node.js 20+, PostgreSQL 15, npm
- **Production:** Docker and Docker Compose (see [DEPLOY.md](docs/deployment/DEPLOY.md))

---

## Quick Start (Local Development)

### 1. Database

Create the database and run migrations:

```bash
createdb marketplace_db
cd backend && source venv/bin/activate
cp .env.example .env   # Edit DATABASE_URL, SECRET_KEY if needed
alembic upgrade head
python -m app.seed_data   # Optional: seed products/vendors/etc. (does NOT create demo users)
```

### 2. Backend

```bash
cd backend
python -m venv venv
source venv/bin/activate   # On Windows: venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

Backend: **http://127.0.0.1:8000**

### 3. Frontend

```bash
cd final-frontend
npm install
npm run dev
```

Frontend: **http://localhost:3000**

### 4. One-command dev (backend + frontend)

From the project root:

```bash
./run.sh
```

Starts backend on port 8000 and frontend on port 3000. Use Ctrl+C to stop both.

---

## Environment Variables

### Backend (`backend/.env`)

| Variable | Description |
|----------|-------------|
| `DATABASE_URL` | PostgreSQL URL, e.g. `postgresql://user:pass@localhost:5432/marketplace_db` |
| `SECRET_KEY` | JWT secret (min 32 characters) |
| `CORS_ORIGINS` | Allowed origins (comma-separated) |
| `ENVIRONMENT` | `development` or `production` |
| `LOG_LEVEL` | e.g. `INFO` |
| `ALLOWED_HOSTS` | Comma-separated host names (production) |
| `JWT_COOKIE_NAME` | Optional: set for HTTPOnly cookie auth |

### Frontend (`final-frontend/.env`)

| Variable | Description |
|----------|-------------|
| `VITE_API_URL` | Backend API URL. In dev often left unset (Vite proxy to `/api`). In production **required** (e.g. `https://api.example.com`). |

---

## Production Deployment

The app is containerised and production-ready. Use **Docker Compose** for a single-server deploy:

```bash
cp .env.example .env
# Set POSTGRES_PASSWORD, SECRET_KEY, CORS_ORIGINS, VITE_API_URL, ALLOWED_HOSTS
docker compose up -d --build
docker compose exec backend alembic upgrade head
```

See **[DEPLOY.md](docs/deployment/DEPLOY.md)** for:

- Single VPS (Docker) with reverse proxy and HTTPS
- Split deploy (e.g. backend on Render/Railway, frontend on Vercel)
- Security checklist and migration commands

---

## API Overview

| Area | Prefix | Description |
|------|--------|-------------|
| Auth | `/api/auth` | Admin email+password+OTP (`/start`, `/onboard`, `/verify-otp`, `/me`) |
| Products | `/api/products` | CRUD products |
| Orders | `/api/orders` | Admin-only order APIs |
| Inventory | `/api/inventory` | Stock in/out, snapshots |
| Expenses | `/api/expenses` | CRUD expenses |
| Dashboard | `/api/dashboard` | Aggregated metrics |
| AI | `/api/ai` | Alerts, forecasts, recommendations, detections |
| Vendors | `/api/vendors` | Rankings, products per vendor, create vendor, add product |
| Purchase orders | `/api/purchase-orders` | List, create, filter by vendor |
| Health | `/health` | DB and app status |

---

## Authentication (admin-only)

There are **no demo / seed user accounts**. Create the first admin through the SPA:

1. Email + password  
2. If the email is new → store name + store type (“Looks like you're new here.”)  
3. 6-digit email OTP (SMTP, or FastAPI server log in development when SMTP is unset)  
4. JWT session (`localStorage` `access_token`); `/api/auth/me` restores after refresh  

Optional SMTP: `SMTP_HOST`, `SMTP_PORT`, `SMTP_USER`, `SMTP_PASSWORD`, `SMTP_FROM`.

---

## License

Proprietary. All rights reserved.

---

## Full documentation

See **[PROJECT_DOCUMENTATION.md](PROJECT_DOCUMENTATION.md)** for a detailed technical and non-technical overview (product value, architecture, APIs, AI, setup, and deployment).

### Java migration (in progress)

Spring Boot business backend lives in **`backend-java/`**. FastAPI remains the default API on `:8000`.

Migrated in Spring today: **Products**, **Inventory**, **Auth**, **Orders** (with ledger), **PO deliver**, **Expenses**.

Still FastAPI: vendors, dashboard, AI, **PO create/list**.

- **[MIGRATION.md](docs/architecture/MIGRATION.md)** — ownership matrix, dual-run routing, ledger gaps
- **[ARCHITECTURE.md](docs/architecture/ARCHITECTURE.md)** — dual-run architecture
- Local Spring: `backend-java/run-local.sh` (port **8080**)
- Optional frontend dual proxy: `VITE_USE_SPRING_PRODUCTS=true npm run dev`
  - Routes products/inventory/orders/expenses → Spring
  - Routes **only** `POST /api/purchase-orders/:id/deliver` → Spring (create/list stay FastAPI)
- Optional Compose profile: `docker compose --profile java up`

---

## Documentation

All detailed documentation is organised under [`docs/`](docs/README.md):

| Category | Contents |
|----------|----------|
| [Architecture](docs/architecture/) | System design, migration strategy, AI layer |
| [Deployment](docs/deployment/) | Production deploy guide, checklist, runbook |
| [Guides](docs/guides/) | Configuration, database setup, API keys |
| [Reports](docs/reports/) | Audits, status reports, implementation records |

---

## Summary

Modern Munim is a B2B operations command center built with **FastAPI**, **PostgreSQL**, **React**, and **Vite**, with an in-progress **Spring Boot** migration for core business APIs. It includes inventory, expenses, vendor management, purchase orders, and AI-driven insights, with Docker-based deployment and production hardening (health checks, logging, CORS, rate limiting). Use **run.sh** for local FastAPI+frontend, **backend-java/run-local.sh** for Spring, and **[DEPLOY.md](docs/deployment/DEPLOY.md)** for production.
