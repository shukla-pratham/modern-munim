# FF Marketplace — Final README

B2B internal operations platform for inventory, vendor intelligence, expenses, and AI-powered analytics. Admin-only; no customer role.

---

## Tech Stack

| Layer    | Stack                    |
|----------|--------------------------|
| Backend  | FastAPI, Python 3.12+    |
| Frontend | Next.js 14, React, TypeScript |
| Database | PostgreSQL 14+           |
| Auth     | JWT                      |

---

## Prerequisites

- **Python 3.12+**
- **Node.js 18+**
- **PostgreSQL 14+** (local, Docker, or cloud)

---

## First-Time Setup

### 1. Backend

```bash
cd backend
python -m venv venv
source venv/bin/activate   # Windows: venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env
# Edit .env: set DATABASE_URL and SECRET_KEY
alembic upgrade head
# Optional: python -m app.seed_data
```

### 2. Frontend

```bash
cd frontend
npm install
cp .env.local.example .env.local
# Edit .env.local: NEXT_PUBLIC_API_URL=http://localhost:8000
```

### 3. Database

Ensure PostgreSQL is running and `DATABASE_URL` in `backend/.env` is correct. Example for local Postgres:

```bash
createdb marketplace_db
# DATABASE_URL=postgresql://USER@localhost:5432/marketplace_db
```

---

## How to Run

### Option A — One command (recommended)

From the project root:

```bash
./run.sh
```

This frees ports 8000 and 3000 if needed, then starts backend and frontend. Press **Ctrl+C** to stop both.

### Option B — Two terminals

**Terminal 1 — Backend**

```bash
cd backend && source venv/bin/activate && uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

**Terminal 2 — Frontend**

From project root:

```bash
npm run dev
```

Or from frontend folder:

```bash
cd frontend && npm run dev
```

---

## URLs

| Service  | URL                      |
|----------|--------------------------|
| Frontend | http://localhost:3000    |
| Backend  | http://127.0.0.1:8000    |
| API docs | http://127.0.0.1:8000/docs |

---

## Using the App

1. Open **http://localhost:3000**.
2. On the landing page, choose **Register** or **Login**.
3. **Register:** Enter email and password. New accounts are created as **admin** (no role choice). You are then redirected to the login page.
4. **Login:** Sign in with the same email and password. You are taken to the admin dashboard.
5. From the dashboard you can manage products, inventory, expenses, vendor intelligence, and AI insights.

---

## Project Layout

```
marketplace/
├── backend/          # FastAPI app (uvicorn)
├── frontend/         # Next.js app (npm run dev)
├── run.sh            # Start backend + frontend
├── package.json      # Root scripts (e.g. npm run dev → frontend)
├── FINAL_README.md   # This file
└── ffmarketplace.md  # Full product and API documentation
```

---

## Troubleshooting

- **Port in use:** Run `./run.sh`; it will stop processes on 8000 and 3000 before starting. Or stop them manually and start again.
- **`npm run dev` at root:** Use `npm run dev` from the project root (it runs the frontend). Backend must be started separately or via `./run.sh`.
- **Blank page:** Ensure the backend is running and `NEXT_PUBLIC_API_URL` in `frontend/.env.local` is `http://localhost:8000`.
- **Database errors:** Run `alembic upgrade head` from the `backend` folder and check `DATABASE_URL` in `backend/.env`.

---

For full feature list, API details, and schema, see **ffmarketplace.md**.
