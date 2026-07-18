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
├── docker-compose.yml       # Postgres + backend + frontend
├── run.sh                   # Local dev: start backend + frontend
├── DEPLOY.md                # Production deployment guide
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
- **Production:** Docker and Docker Compose (see [DEPLOY.md](DEPLOY.md))

---

## Quick Start (Local Development)

### 1. Database

Create the database and run migrations:

```bash
createdb marketplace_db
cd backend && source venv/bin/activate
cp .env.example .env   # Edit DATABASE_URL, SECRET_KEY if needed
alembic upgrade head
python -m app.seed_data   # Optional: seed users, products, vendors, etc.
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

See **[DEPLOY.md](DEPLOY.md)** for:

- Single VPS (Docker) with reverse proxy and HTTPS
- Split deploy (e.g. backend on Render/Railway, frontend on Vercel)
- Security checklist and migration commands

---

## API Overview

| Area | Prefix | Description |
|------|--------|-------------|
| Auth | `/api/auth` | Login, register, `/me` |
| Products | `/api/products` | CRUD products |
| Orders | `/api/orders` | Customer orders |
| Inventory | `/api/inventory` | Stock in/out, snapshots |
| Expenses | `/api/expenses` | CRUD expenses |
| Dashboard | `/api/dashboard` | Aggregated metrics |
| AI | `/api/ai` | Alerts, forecasts, recommendations, detections |
| Vendors | `/api/vendors` | Rankings, products per vendor, create vendor, add product |
| Purchase orders | `/api/purchase-orders` | List, create, filter by vendor |
| Health | `/health` | DB and app status |

---

## Demo Credentials (after seed)

| Role | Email | Password |
|------|--------|----------|
| Admin | admin@marketplace.com | admin123 |
| Manager | manager@marketplace.com | manager123 |
| Ops | ops@marketplace.com | ops123 |

---

## License

Proprietary. All rights reserved.

---

## Summary

Modern Munim is a B2B operations command center built with **FastAPI**, **PostgreSQL**, **React**, and **Vite**. It includes inventory, expenses, vendor management, purchase orders, and AI-driven insights, with Docker-based deployment and production hardening (health checks, logging, CORS, rate limiting). Use **run.sh** for local dev and **DEPLOY.md** for production.
