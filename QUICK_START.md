# Quick Start Guide

## 🚀 Get Started in 5 Minutes

### Prerequisites
- Python 3.11+
- Node.js 18+
- PostgreSQL 14+ (or free-tier account: Railway/Render/Supabase/Neon)

---

## Step 1: Clone & Setup Backend

```bash
cd backend

# Create virtual environment
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Create .env file
cp .env.example .env

# Edit .env with your values:
# DATABASE_URL=postgresql://user:password@localhost:5432/marketplace_db
# SECRET_KEY=<generate-with-command-below>
```

**Generate SECRET_KEY**:
```bash
python -c "import secrets; print(secrets.token_urlsafe(32))"
```

**Important**: Copy the generated key to your `.env` file.

---

## Step 2: Setup Database

```bash
# Run migrations
alembic revision --autogenerate -m "Initial migration"
alembic upgrade head

# Seed demo data (optional)
python -m app.seed_data
```

**Demo Credentials** (from seed data):
- Admin: `admin@marketplace.com` / `admin123`
- Customer: `customer1@marketplace.com` / `customer123`

---

## Step 3: Start Backend

```bash
# Development
uvicorn app.main:app --reload --port 8000

# Or use the run script
python run.py
```

Backend runs at: `http://localhost:8000`

---

## Step 4: Setup Frontend

```bash
cd frontend

# Install dependencies
npm install

# Create .env.local
cp .env.local.example .env.local

# Edit .env.local:
# NEXT_PUBLIC_API_URL=http://localhost:8000
```

---

## Step 5: Start Frontend

```bash
npm run dev
```

Frontend runs at: `http://localhost:3000`

---

## ✅ Verify Installation

1. **Backend Health Check**: Visit `http://localhost:8000/health`
   - Should return: `{"status": "healthy", "database": "healthy", "version": "2.0.0"}`

2. **Frontend**: Visit `http://localhost:3000`
   - Should redirect to login page

3. **Login**: Use demo credentials above

---

## 🔑 Configuration Summary

### What You Need (No API Keys!)

**Backend**:
- ✅ `DATABASE_URL` - Your PostgreSQL connection string
- ✅ `SECRET_KEY` - Generate yourself (not an API key!)

**Frontend**:
- ✅ `NEXT_PUBLIC_API_URL` - Your backend URL

**That's it!** No external API keys, no paid services.

---

## 🆘 Troubleshooting

### "SECRET_KEY must be at least 32 characters"
- Generate a new key: `python -c "import secrets; print(secrets.token_urlsafe(32))"`
- Update `.env` file

### "DATABASE_URL must be a PostgreSQL connection string"
- Ensure URL starts with `postgresql://`
- Check database is running and accessible

### "Could not connect to database"
- Verify PostgreSQL is running
- Check DATABASE_URL credentials
- Ensure database exists

### Frontend can't connect to backend
- Verify `NEXT_PUBLIC_API_URL` is correct
- Check backend is running on port 8000
- Check CORS settings in backend

---

## 📚 Next Steps

- Read `CONFIGURATION.md` for detailed configuration guide
- Read `README.md` for full documentation
- Read `DEPLOYMENT_CHECKLIST.md` for production deployment

---

## 💡 Key Points

- ✅ **Zero API keys required**
- ✅ **100% free-tier friendly**
- ✅ **All open-source dependencies**
- ✅ **Self-contained application**

**No external services. No paid APIs. Just your infrastructure.**
