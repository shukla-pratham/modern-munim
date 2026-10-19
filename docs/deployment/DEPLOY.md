# Production Deployment Guide

This document describes how to deploy the Marketplace (FastAPI + PostgreSQL + React) in production. The application is containerized and can run on a single VPS with Docker or split across cloud services.

---

## Option A — Single VPS (Docker)

### Prerequisites

- Docker Engine and Docker Compose V2 on the server
- A domain (or IP) for the app and, if desired, a separate subdomain for the API

### 1. Install Docker

**Ubuntu/Debian:**

```bash
sudo apt-get update
sudo apt-get install -y ca-certificates curl
sudo install -m 0755 -d /etc/apt/keyrings
sudo curl -fsSL https://download.docker.com/linux/ubuntu/gpg -o /etc/apt/keyrings/docker.asc
sudo chmod a+r /etc/apt/keyrings/docker.asc
echo "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.asc] https://download.docker.com/linux/ubuntu $(. /etc/os-release && echo "$VERSION_CODENAME") stable" | sudo tee /etc/apt/sources.list.d/docker.list > /dev/null
sudo apt-get update
sudo apt-get install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin
```

### 2. Clone and set environment variables

```bash
cd /opt
sudo git clone <your-repo-url> marketplace
cd marketplace
```

Create a production env file (do not commit secrets):

```bash
sudo cp .env.example .env
sudo nano .env
```

Set at least:

```env
POSTGRES_USER=marketplace
POSTGRES_PASSWORD=<strong-random-password>
POSTGRES_DB=marketplace_db
SECRET_KEY=<at-least-32-chars>
CORS_ORIGINS=https://yourdomain.com
VITE_API_URL=https://yourdomain.com/api
ALLOWED_HOSTS=yourdomain.com,www.yourdomain.com
```

Generate `SECRET_KEY`:

```bash
python3 -c "import secrets; print(secrets.token_urlsafe(32))"
```

### 3. Build and run with Docker Compose

```bash
sudo docker compose up -d --build
```

Containers: `postgres`, `backend`, `frontend`. Frontend serves the SPA on port 80; backend listens internally on 8000.

### 4. Run database migrations

Migrations are **not** run automatically at container start. Run them once (and after code updates that include new migrations):

```bash
sudo docker compose exec backend alembic upgrade head
```

To create seed data (optional):

```bash
sudo docker compose exec backend python -m app.seed_data
```

### 5. Reverse proxy and HTTPS

Put Nginx (or Caddy) in front so that:

- `https://yourdomain.com` → frontend container (port 80)
- `https://yourdomain.com/api` → backend container (port 8000)

**Example Nginx snippet (proxy to host ports):**

If you expose backend on 8000 and frontend on 80, and Nginx is on the same host:

```nginx
server {
    listen 443 ssl http2;
    server_name yourdomain.com;
    ssl_certificate     /etc/ssl/certs/yourdomain.crt;
    ssl_certificate_key /etc/ssl/private/yourdomain.key;

    location /api {
        proxy_pass http://127.0.0.1:8000;
        proxy_http_version 1.1;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    location / {
        proxy_pass http://127.0.0.1:80;
        proxy_http_version 1.1;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

Then set:

- `CORS_ORIGINS=https://yourdomain.com`
- `VITE_API_URL=https://yourdomain.com` (frontend calls same origin; proxy forwards `/api` to backend)

Rebuild frontend with that `VITE_API_URL` and restart:

```bash
export VITE_API_URL=https://yourdomain.com
sudo docker compose up -d --build frontend
```

### 6. HTTPS with Let’s Encrypt (optional)

```bash
sudo apt-get install certbot python3-certbot-nginx
sudo certbot --nginx -d yourdomain.com
```

---

## Option B — Cloud split (Backend + Frontend separate)

### Backend (e.g. Render, Railway)

1. Create a PostgreSQL database (Render Postgres, Railway Postgres, or external).
2. Create a Web Service; connect the repo and set build command to use the `backend` context (or root with `dockerfile: backend/Dockerfile` if the platform supports it). If the platform runs Python directly:
   - Build: `pip install -r backend/requirements.txt`
   - Start: `gunicorn app.main:app -k uvicorn.workers.UvicornWorker -b 0.0.0.0:$PORT -c backend/gunicorn.conf.py`
3. Set environment variables:
   - `DATABASE_URL` = production Postgres URL
   - `SECRET_KEY` = 32+ character secret
   - `ENVIRONMENT=production`
   - `CORS_ORIGINS=https://your-frontend.vercel.app`
   - `ALLOWED_HOSTS` = hostname of the backend (e.g. `yourapp.onrender.com`)
4. After deploy, run migrations (one-off, or via release command):
   ```bash
   alembic -c backend/alembic.ini upgrade head
   ```
   (Adjust path if your platform runs from repo root.)

### Frontend (e.g. Vercel)

1. Connect the repo; set root directory to `final-frontend` (or the folder that contains the Vite app).
2. Build command: `npm run build` or `npm ci && npm run build`.
3. Set **Build environment variable**:
   - `VITE_API_URL` = full backend API URL (e.g. `https://yourapp.onrender.com`).
4. Output directory: `dist`. Vercel will serve the SPA automatically.

### Exact commands (summary)

**Backend (Render/Railway style):**

- Install: `pip install -r backend/requirements.txt` (or use Docker with `backend/Dockerfile`).
- Start: `gunicorn app.main:app -k uvicorn.workers.UvicornWorker -b 0.0.0.0:$PORT`.
- Migrations: `alembic upgrade head` (run once per release from `backend` or project root with correct `alembic.ini`).

**Frontend (Vercel):**

- Install: `npm ci`
- Build: `VITE_API_URL=https://your-backend-url npm run build`
- Publish: `dist` as static assets.

---

## Database migrations (all environments)

- Migrations are managed by Alembic. **Do not** auto-run `alembic upgrade head` inside the application process; run it as a separate step (release command, one-off job, or manual).
- From project root (with `backend` as cwd or `ALEMBIC_CONFIG` set):

  ```bash
  cd backend && alembic upgrade head
  ```

- In Docker:

  ```bash
  docker compose exec backend alembic upgrade head
  ```

---

## Security checklist

- [ ] `SECRET_KEY` is 32+ characters and not committed.
- [ ] `POSTGRES_PASSWORD` (and `DATABASE_URL`) are strong and not committed.
- [ ] `ENVIRONMENT=production` and `DEBUG=false` in production.
- [ ] `CORS_ORIGINS` set to the exact frontend origin(s); no `*`.
- [ ] `ALLOWED_HOSTS` set to the backend hostname(s).
- [ ] HTTPS enabled at the reverse proxy or platform.
- [ ] Run migrations only via explicit command, not blindly at every container start.

---

## Running locally (development)

Use the dev script; it does **not** kill ports in production contexts and is intended for local use only:

```bash
./run.sh
```

Backend: http://127.0.0.1:8000  
Frontend: http://localhost:3000  

For production, use Docker Compose and the steps above; do not rely on `run.sh`.
