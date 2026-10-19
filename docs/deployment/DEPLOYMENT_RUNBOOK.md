# Modern Munim deployment runbook

This runbook matches the repository as of the deployment-readiness pass on 2026-10-14. Production traffic uses FastAPI for every `/api` route. Spring Boot is an optional development process. The Vite dev proxy is the only place that splits business routes to Spring.

## What you need

- PostgreSQL 14 (the verified local server is 14.23 on `localhost:5432`)
- Python 3.12 with `backend/venv` already installed
- Node.js for `final-frontend`
- JDK 22 and Maven for optional Spring checks
- A Gmail app password (or another SMTP account) for production OTP email

Do not commit `.env` files. Do not print `SECRET_KEY`, `SMTP_PASSWORD`, or database passwords.

## Environment

`backend/.env` is loaded by FastAPI. Required names:

| Name | Development | Production |
|---|---|---|
| `DATABASE_URL` | PostgreSQL URL for `marketplace_db` | Required. Must start with `postgresql://` |
| `SECRET_KEY` | At least 32 characters | Required. At least 32 characters |
| `ENVIRONMENT` | `development` | `production` |
| `DEBUG` | `false` | Must be false |
| `CORS_ORIGINS` | SPA origins, no `*` | Required, explicit origins, no `*` |
| `ALLOWED_HOSTS` | `localhost,127.0.0.1` | Hosts the API will accept |
| `SMTP_HOST` | `smtp.gmail.com` | Passed by Compose |
| `SMTP_PORT` | `587` | Passed by Compose |
| `SMTP_USER` | Sender mailbox | Required. Compose refuses to start without it |
| `SMTP_PASSWORD` | App password | Required. Compose refuses to start without it |
| `SMTP_FROM` | Usually the same mailbox | Optional. Defaults to `SMTP_USER` |
| `EMAIL_OTP_DEV_LOG` | Defaults to true if unset | Must be `false`. Production startup rejects `true` |
| `ALGORITHM` | `HS256` | Same |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | `30` | Same |

Frontend production build:

```bash
VITE_API_URL=https://your-api-host npm run build
```

`VITE_API_URL` must be an absolute `http` or `https` URL. The production image does not split `/api` across two backends. Point it at FastAPI.

Development-only (do not set these in production):

- `VITE_USE_SPRING_PRODUCTS=true` sends products, inventory, orders, expenses, vendors, dashboard, and purchase orders to Spring.
- `/api/auth` and `/api/ai` stay on FastAPI in both modes.

## Database migration

From `backend/`, with `.env` loaded:

```bash
set -a && source .env && set +a
./venv/bin/alembic current
./venv/bin/alembic upgrade head
```

Head revision: `008_user_store_type`.

That revision adds `users.mfa_enabled`, `users.mfa_secret`, `users.store_name`, `users.store_type`, and the `email_otps` table. It does not delete accounts.

Hibernate on Spring is `ddl-auto: validate`. It must not create or alter tables. If Spring fails validation, fix the migration. Do not switch Hibernate to `update`.

## Backup

```bash
pg_dump --format=custom --no-owner --file "$HOME/modern-munim-backups/marketplace_db-$(date +%Y%m%d-%H%M%S).dump" "$DATABASE_URL"
pg_restore --list "$HOME/modern-munim-backups/marketplace_db-YYYYMMDD-HHMMSS.dump" >/dev/null
```

Keep dumps outside the git repository. Do not overwrite an existing file.

A verified pre-migration dump from 2026-10-14 is:

`/Users/prathamshukla/modern-munim-backups/marketplace_db-20261014-155541.dump` (76,002 bytes). `pg_restore --list` succeeded. That dump is the database **before** revision `008`.

## Restore

Stop FastAPI first. Restore into an empty database, or into a new database name, and point `DATABASE_URL` at it. Do not restore over `marketplace_db` until you have a newer dump.

```bash
createdb marketplace_db_restore
pg_restore --no-owner --dbname marketplace_db_restore /path/to/dump
```

If the dump is from before `008`, run `alembic upgrade head` after restore.

## Start the API

```bash
cd backend
set -a && source .env && set +a
./venv/bin/uvicorn app.main:app --host 127.0.0.1 --port 8000
```

Health:

```bash
curl -sS http://127.0.0.1:8000/health
```

Expect `{"status":"healthy","database":"healthy","version":"2.0.0"}`. A database failure returns `database: "unhealthy"` without the exception text.

## Start the SPA (development)

Port 3000 may already be used by another application. Pick a free port.

```bash
cd final-frontend
npx vite --host 127.0.0.1 --port 3010 --strictPort
```

Sign-in is email, password, then store name and type for a new address, then a 6-digit email code. In development, if SMTP fails and `EMAIL_OTP_DEV_LOG` is on, the code is written to the API log. It is not returned in the JSON body.

## Docker Compose

`docker-compose.yml` runs Postgres, FastAPI (`ENVIRONMENT=production`), and the SPA. Spring is profile `java` only and is not what the SPA image calls. Nginx serves the SPA and does not proxy `/api`. Set `VITE_API_URL` to the FastAPI origin the browser can reach. For the default port map that is `http://localhost:8000`. `http://localhost/api` will not work.

Compose requires `SMTP_USER` and `SMTP_PASSWORD` in the environment or a gitignored project `.env`. It sets `EMAIL_OTP_DEV_LOG=false`. It also requires `POSTGRES_PASSWORD`, `SECRET_KEY`, and `VITE_API_URL`. The API container uses its own Postgres service. It does not attach to PostgreSQL on the host.

Do not enable the `java` profile when port 8080 is already taken. On 2026-10-14 that port was `alphaforge-app`. The default stack does not bind 8080.

Default host ports are `127.0.0.1:8000` for the API and `80` for the SPA. If 8000 is already in use, start with the staging override instead of editing `docker-compose.yml`:

```bash
docker compose -p modernmunim-staging \
  -f docker-compose.yml -f docker-compose.staging.yml \
  up -d --build
docker exec -w /app marketplace_backend alembic upgrade head
```

That override publishes the API on `127.0.0.1:18000` and the SPA on `127.0.0.1:8088`. Pass `VITE_API_URL=http://127.0.0.1:18000` and `CORS_ORIGINS=http://127.0.0.1:8088` for that map. The image bakes `VITE_API_URL` at build time.

On 2026-10-14 this staging command exited 0 after base images were pulled. `GET http://127.0.0.1:18000/health` returned 200. The new volume is `modernmunim-staging_postgres_data`. Stop it with `docker compose -p modernmunim-staging down` and do not add `-v` if you want to keep that database.

If the build fails with `failed to xattr` and `operation not permitted` on `._*` files, those are macOS AppleDouble files. Both Docker ignore files exclude `._*`. Delete any that already exist beside the source tree and build again. Do not copy `.env` into the image; `backend/.dockerignore` already excludes it.

The first postgres image pull in that session stalled and had to be retried with `docker pull postgres:15-alpine`. A stalled pull is not a successful boot.

## Auth checks that must stay true

- `POST /api/auth/register` and `POST /api/auth/login` return 400.
- `POST /api/auth/start` for an unknown email returns `needs_onboarding` and does not insert a user.
- OTP values are bcrypt hashes in `email_otps`. Responses contain `status`, `email`, and `message` only.
- Business routes, including `GET /api/products` and all `/api/orders` routes, require an admin JWT.

## Tenants, demo data, and onboarding

Do not treat this application as multi-tenant. Alembic head `008_user_store_type` has no workspace or tenant table. `users.store_name` and `users.store_type` are signup fields. They do not scope products, vendors, expenses, purchase orders, inventory, dashboards, or AI rows.

Any admin JWT can read and write the shared catalog. `GET /api/orders` returns every order. `GET /api/orders/my-orders` is the only list filtered by `orders.user_id`, and it still requires admin.

There is no founder role and no server check for `shuklapratham758@gmail.com`. Do not hide demo data with a frontend email comparison.

`python -m app.seed_data` is manual. It is not run at API startup. It writes untagged global rows. Products, vendors, and purchase orders skip an existing name or `po_number`. Expenses are inserted again on every run. Do not run it against `marketplace_db` or the staging volume until rows are owned by a workspace and regeneration cannot touch real data.

Sign-in onboarding is one step: store name and store type, then OTP. It is not a skippable product tour stored on the user. The cinematic intro can be skipped in the browser, but `introSeen` is not read on the next load, so the intro returns after refresh.

A read-only mapping of the six host users is in `MODERN_MUNIM_USER_WORKSPACE_MAPPING_PLAN.md`. The founder address is not one of those accounts. Do not add `workspace_id` until the operator approves or corrects that plan. `store_name` is nullable and not unique, so it is not that mapping.

## Rollback of a bad migration

Do not run `alembic downgrade` on `marketplace_db` without a fresh dump. Revisions `006`–`008` drop the columns and `email_otps` on downgrade, which deletes OTP rows and store fields. Prefer restoring the custom-format dump into a new database.
