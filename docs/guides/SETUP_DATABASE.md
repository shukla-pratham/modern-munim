# Database Setup Guide

## Quick Setup

The application requires PostgreSQL to be running. Here are your options:

### Option 1: Local PostgreSQL (Recommended for Development)

1. **Install PostgreSQL** (if not installed):
   ```bash
   # macOS (using Homebrew)
   brew install postgresql@14
   brew services start postgresql@14
   
   # Or download from: https://www.postgresql.org/download/
   ```

2. **Create Database**:
   ```bash
   createdb marketplace_db
   ```

3. **Update .env file**:
   ```bash
   DATABASE_URL=postgresql://$(whoami)@localhost:5432/marketplace_db
   ```

4. **Run Migrations**:
   ```bash
   cd backend
   alembic upgrade head
   ```

### Option 2: Free Cloud PostgreSQL (Recommended for Quick Start)

Use a free-tier PostgreSQL service:

1. **Railway** (https://railway.app):
   - Sign up (free)
   - Create PostgreSQL database
   - Copy connection string to `DATABASE_URL` in `.env`

2. **Render** (https://render.com):
   - Sign up (free)
   - Create PostgreSQL database
   - Copy connection string to `DATABASE_URL` in `.env`

3. **Supabase** (https://supabase.com):
   - Sign up (free)
   - Create new project
   - Get connection string from Settings > Database
   - Copy to `DATABASE_URL` in `.env`

4. **Neon** (https://neon.tech):
   - Sign up (free)
   - Create database
   - Copy connection string to `DATABASE_URL` in `.env`

### Option 3: Docker PostgreSQL

```bash
docker run --name marketplace-postgres \
  -e POSTGRES_PASSWORD=postgres \
  -e POSTGRES_DB=marketplace_db \
  -p 5432:5432 \
  -d postgres:14

# Update .env:
DATABASE_URL=postgresql://postgres:postgres@localhost:5432/marketplace_db
```

## After Database Setup

1. **Run Migrations**:
   ```bash
   cd backend
   alembic upgrade head
   ```

2. **Seed Demo Data** (optional):
   ```bash
   python -m app.seed_data
   ```

3. **Start Backend**:
   ```bash
   uvicorn app.main:app --reload --port 8000
   ```

4. **Test Connection**:
   ```bash
   curl http://localhost:8000/health
   ```

## Troubleshooting

### "Connection refused" or "Could not connect"
- PostgreSQL is not running
- Wrong `DATABASE_URL` in `.env`
- Database doesn't exist

### "Authentication failed"
- Wrong username/password in `DATABASE_URL`
- Check PostgreSQL user permissions

### "Database does not exist"
- Create the database: `createdb marketplace_db`
- Or use a cloud provider (they create it for you)

## Current Status

Your `.env` file has:
```
DATABASE_URL=postgresql://user:password@localhost:5432/marketplace_db
```

**This is a placeholder!** You need to:
1. Set up PostgreSQL (local or cloud)
2. Update `DATABASE_URL` with real credentials
3. Run migrations: `alembic upgrade head`
