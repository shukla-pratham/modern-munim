# Local PostgreSQL Setup Guide

## Quick Setup Options

### Option 1: Docker PostgreSQL (Easiest - Recommended)

```bash
# Start PostgreSQL in Docker
docker run --name marketplace-postgres \
  -e POSTGRES_USER=marketplace_user \
  -e POSTGRES_PASSWORD=marketplace_pass \
  -e POSTGRES_DB=marketplace_db \
  -p 5432:5432 \
  -d postgres:14

# Update .env file
cd backend
cat > .env << EOF
DATABASE_URL=postgresql://marketplace_user:marketplace_pass@localhost:5432/marketplace_db
SECRET_KEY=cz4_kKeyU3OrqzbNzdILX3RRLNtS-U8wXTclsz1cbzg
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
CORS_ORIGINS=http://localhost:3000,http://localhost:3001
LOG_LEVEL=INFO
ENVIRONMENT=development
AI_BATCH_JOB_TIMEOUT_HOURS=2
EOF

# Run migrations
alembic upgrade head

# Seed data
python -m app.seed_data
```

### Option 2: Homebrew PostgreSQL (macOS)

```bash
# Install PostgreSQL
brew install postgresql@14

# Start PostgreSQL service
brew services start postgresql@14

# Create database and user
createdb marketplace_db
createuser marketplace_user -P
# Enter password when prompted (e.g., marketplace_pass)

# Grant permissions
psql marketplace_db -c "GRANT ALL PRIVILEGES ON DATABASE marketplace_db TO marketplace_user;"
psql marketplace_db -c "ALTER USER marketplace_user CREATEDB;"

# Update .env file
cd backend
cat > .env << EOF
DATABASE_URL=postgresql://marketplace_user:marketplace_pass@localhost:5432/marketplace_db
SECRET_KEY=cz4_kKeyU3OrqzbNzdILX3RRLNtS-U8wXTclsz1cbzg
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
CORS_ORIGINS=http://localhost:3000,http://localhost:3001
LOG_LEVEL=INFO
ENVIRONMENT=development
AI_BATCH_JOB_TIMEOUT_HOURS=2
EOF

# Run migrations
alembic upgrade head

# Seed data
python -m app.seed_data
```

### Option 3: System PostgreSQL (if already installed)

```bash
# Check if PostgreSQL is running
pg_isready

# Create database
createdb marketplace_db

# Create user (optional, can use your system user)
# If using system user, DATABASE_URL will be:
# postgresql://$(whoami)@localhost:5432/marketplace_db

# Update .env file
cd backend
# Edit .env and set DATABASE_URL to:
# postgresql://your_username@localhost:5432/marketplace_db

# Run migrations
alembic upgrade head

# Seed data
python -m app.seed_data
```

## Verification

After setup, verify the connection:

```bash
# Test database connection
cd backend
python -c "from app.core.database import engine; from sqlalchemy import text; conn = engine.connect(); result = conn.execute(text('SELECT 1')); print('✅ Database connected!')"

# Check health endpoint
curl http://localhost:8000/health
# Should return: {"status": "healthy", "database": "healthy", ...}
```

## Troubleshooting

### "Connection refused"
- PostgreSQL is not running
- Start it: `brew services start postgresql@14` or `docker start marketplace-postgres`

### "Role does not exist"
- User doesn't exist in PostgreSQL
- Create user: `createuser marketplace_user -P`

### "Database does not exist"
- Database not created
- Create it: `createdb marketplace_db`

### Port 5432 already in use
- Another PostgreSQL instance is running
- Stop it or use a different port

## Quick Commands Reference

```bash
# Start Docker PostgreSQL
docker start marketplace-postgres

# Stop Docker PostgreSQL
docker stop marketplace-postgres

# View Docker logs
docker logs marketplace-postgres

# Connect to database (Docker)
docker exec -it marketplace-postgres psql -U marketplace_user -d marketplace_db

# Connect to database (Local)
psql marketplace_db
```
