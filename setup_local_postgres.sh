#!/bin/bash
# Setup script for local PostgreSQL database

set -e

echo "═══════════════════════════════════════════════════════"
echo "🚀 Setting up Local PostgreSQL Database"
echo "═══════════════════════════════════════════════════════"
echo ""

# Check if Homebrew is installed
if ! command -v brew &> /dev/null; then
    echo "❌ Homebrew is not installed. Please install it first:"
    echo "   /bin/bash -c \"\$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)\""
    exit 1
fi

echo "✅ Homebrew found"
echo ""

# Install PostgreSQL if not installed
if ! command -v psql &> /dev/null; then
    echo "📦 Installing PostgreSQL 14..."
    brew install postgresql@14
    echo "✅ PostgreSQL installed"
else
    echo "✅ PostgreSQL already installed"
fi

echo ""

# Start PostgreSQL service
echo "🔄 Starting PostgreSQL service..."
brew services start postgresql@14
sleep 3
echo "✅ PostgreSQL service started"
echo ""

# Create database
echo "📝 Creating database..."
if psql -lqt | cut -d \| -f 1 | grep -qw marketplace_db; then
    echo "⚠️  Database 'marketplace_db' already exists"
else
    createdb marketplace_db
    echo "✅ Database 'marketplace_db' created"
fi
echo ""

# Create user (optional - can use system user)
DB_USER="marketplace_user"
DB_PASS="marketplace_pass"

echo "👤 Setting up database user..."
if psql -tAc "SELECT 1 FROM pg_roles WHERE rolname='$DB_USER'" | grep -q 1; then
    echo "⚠️  User '$DB_USER' already exists"
else
    psql -d marketplace_db -c "CREATE USER $DB_USER WITH PASSWORD '$DB_PASS';"
    psql -d marketplace_db -c "GRANT ALL PRIVILEGES ON DATABASE marketplace_db TO $DB_USER;"
    psql -d marketplace_db -c "ALTER USER $DB_USER CREATEDB;"
    echo "✅ User '$DB_USER' created"
fi
echo ""

# Update .env file
echo "📝 Updating backend/.env file..."
cd backend

# Get current username as fallback
CURRENT_USER=$(whoami)

cat > .env << EOF
# Required Environment Variables
DATABASE_URL=postgresql://$DB_USER:$DB_PASS@localhost:5432/marketplace_db
SECRET_KEY=cz4_kKeyU3OrqzbNzdILX3RRLNtS-U8wXTclsz1cbzg

# Optional Environment Variables (have defaults)
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
CORS_ORIGINS=http://localhost:3000,http://localhost:3001
LOG_LEVEL=INFO
ENVIRONMENT=development
AI_BATCH_JOB_TIMEOUT_HOURS=2

# IMPORTANT NOTES:
# - NO external API keys are required
# - SECRET_KEY is internally generated (not from a third party)
# - DATABASE_URL is your PostgreSQL connection string (not an API key)
EOF

echo "✅ .env file updated"
echo ""

# Test connection
echo "🔍 Testing database connection..."
python3 -c "
from app.core.database import engine
from sqlalchemy import text
try:
    with engine.connect() as conn:
        result = conn.execute(text('SELECT 1'))
    print('✅ Database connection successful!')
except Exception as e:
    print(f'❌ Database connection failed: {e}')
    exit(1)
" || {
    echo ""
    echo "⚠️  Connection test failed. Trying with system user..."
    # Try with system user
    cat > .env << EOF
# Required Environment Variables
DATABASE_URL=postgresql://$CURRENT_USER@localhost:5432/marketplace_db
SECRET_KEY=cz4_kKeyU3OrqzbNzdILX3RRLNtS-U8wXTclsz1cbzg

# Optional Environment Variables (have defaults)
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
CORS_ORIGINS=http://localhost:3000,http://localhost:3001
LOG_LEVEL=INFO
ENVIRONMENT=development
AI_BATCH_JOB_TIMEOUT_HOURS=2
EOF
    echo "✅ Updated .env to use system user: $CURRENT_USER"
    python3 -c "
from app.core.database import engine
from sqlalchemy import text
try:
    with engine.connect() as conn:
        result = conn.execute(text('SELECT 1'))
    print('✅ Database connection successful with system user!')
except Exception as e:
    print(f'❌ Connection still failed: {e}')
    print('Please check PostgreSQL is running and credentials are correct')
    exit(1)
    "
}

echo ""
echo "═══════════════════════════════════════════════════════"
echo "✅ PostgreSQL Setup Complete!"
echo "═══════════════════════════════════════════════════════"
echo ""
echo "📋 Next steps:"
echo "   1. Run migrations: cd backend && alembic upgrade head"
echo "   2. Seed data: python -m app.seed_data"
echo "   3. Restart backend server"
echo ""
echo "🔗 Database Info:"
echo "   Database: marketplace_db"
echo "   User: $DB_USER (or $CURRENT_USER)"
echo "   Host: localhost:5432"
echo ""
