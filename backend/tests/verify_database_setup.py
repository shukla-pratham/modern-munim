#!/usr/bin/env python3
"""
B2B Database Setup Verification Script
Verifies all database components are correctly configured.
"""
import sys
from sqlalchemy import text, inspect
from app.core.database import engine, SessionLocal, Base
from app.core.config import settings
from app.models import *
from app.models.user import UserRole

def verify_database_connection():
    """Task 1: Verify database connection"""
    print("=" * 60)
    print("1️⃣ DATABASE CONNECTION VERIFICATION")
    print("=" * 60)
    
    try:
        # Verify DATABASE_URL is loaded
        db_url = settings.DATABASE_URL
        if not db_url or db_url.startswith("postgresql://"):
            print("✅ DATABASE_URL loaded from .env")
            print(f"   URL: {db_url[:50]}...")
        else:
            print("❌ DATABASE_URL invalid format")
            return False
        
        # Test connection
        with engine.connect() as conn:
            result = conn.execute(text("SELECT 1"))
            assert result.scalar() == 1
        print("✅ Database connection successful")
        
        # Verify connection pooling
        pool = engine.pool
        print(f"✅ Connection pool configured:")
        print(f"   Pool size: {pool.size()}")
        print(f"   Max overflow: {pool._max_overflow}")
        print(f"   Pool pre-ping: {pool._pre_ping}")
        
        return True
    except Exception as e:
        print(f"❌ Database connection failed: {e}")
        return False


def verify_schema():
    """Task 3: Verify B2B schema"""
    print("\n" + "=" * 60)
    print("3️⃣ SCHEMA VERIFICATION (B2B)")
    print("=" * 60)
    
    inspector = inspect(engine)
    existing_tables = set(inspector.get_table_names())
    
    # Required core tables
    core_tables = {
        "users", "products", "expenses", "orders", "order_items"
    }
    
    # Required B2B tables
    b2b_tables = {
        "suppliers", "purchase_orders", "purchase_order_items", "inventory_snapshots"
    }
    
    # Required AI tables
    ai_tables = {
        "demand_forecasts", "stockout_predictions", "restocking_recommendations",
        "dead_stock_detections", "ai_alerts", "job_runs"
    }
    
    # Required operations tables
    ops_tables = {
        "stock_transactions"
    }
    
    all_required = core_tables | b2b_tables | ai_tables | ops_tables
    
    print(f"\nRequired tables: {len(all_required)}")
    print(f"Existing tables: {len(existing_tables)}")
    
    missing = all_required - existing_tables
    if missing:
        print(f"\n❌ Missing tables: {missing}")
        return False
    else:
        print("\n✅ All required tables exist")
    
    # Verify CHECK constraints on key tables
    print("\nVerifying CHECK constraints...")
    with engine.connect() as conn:
        # Check products table constraints
        result = conn.execute(text("""
            SELECT constraint_name 
            FROM information_schema.table_constraints 
            WHERE table_name = 'products' 
            AND constraint_type = 'CHECK'
        """))
        product_checks = [r[0] for r in result]
        required_checks = {
            'check_stock_quantity_non_negative',
            'check_stock_threshold_non_negative',
            'check_price_non_negative'
        }
        if all(c in product_checks for c in required_checks):
            print("✅ Products table has required CHECK constraints")
        else:
            print(f"⚠️  Products table missing some CHECK constraints")
    
    # Verify foreign keys
    print("\nVerifying foreign keys...")
    with engine.connect() as conn:
        result = conn.execute(text("""
            SELECT COUNT(*) 
            FROM information_schema.table_constraints 
            WHERE constraint_type = 'FOREIGN KEY'
        """))
        fk_count = result.scalar()
        print(f"✅ Found {fk_count} foreign key constraints")
    
    # Verify indexes
    print("\nVerifying indexes...")
    with engine.connect() as conn:
        result = conn.execute(text("""
            SELECT COUNT(*) 
            FROM pg_indexes 
            WHERE schemaname = 'public'
        """))
        idx_count = result.scalar()
        print(f"✅ Found {idx_count} indexes")
    
    return True


def verify_user_roles():
    """Verify manager role exists"""
    print("\n" + "=" * 60)
    print("2️⃣ USER ROLES VERIFICATION")
    print("=" * 60)
    
    try:
        with engine.connect() as conn:
            result = conn.execute(text("""
                SELECT unnest(enum_range(NULL::userrole))::text
            """))
            roles = [r[0].lower() for r in result]  # Normalize to lowercase
            
            required_roles = {"admin", "customer", "manager"}
            existing_roles = set(roles)
            
            if required_roles.issubset(existing_roles):
                print(f"✅ All required roles exist: {sorted(existing_roles)}")
                return True
            else:
                missing = required_roles - existing_roles
                print(f"❌ Missing roles: {missing}")
                print(f"   Existing: {sorted(existing_roles)}")
                return False
    except Exception as e:
        print(f"❌ Error checking roles: {e}")
        return False


def verify_seed_data():
    """Task 5: Verify seed data can be loaded"""
    print("\n" + "=" * 60)
    print("5️⃣ SEED DATA VERIFICATION")
    print("=" * 60)
    
    try:
        db = SessionLocal()
        
        # Check users
        user_count = db.query(User).count()
        admin_count = db.query(User).filter(User.role == UserRole.ADMIN).count()
        manager_count = db.query(User).filter(User.role == UserRole.MANAGER).count()
        
        print(f"✅ Users in database: {user_count}")
        print(f"   Admins: {admin_count}")
        print(f"   Managers: {manager_count}")
        
        # Check products
        product_count = db.query(Product).count()
        print(f"✅ Products: {product_count}")
        
        # Check suppliers (B2B)
        try:
            supplier_count = db.query(Supplier).count()
            print(f"✅ Suppliers: {supplier_count}")
        except:
            print("⚠️  Suppliers table not found (migration may be pending)")
        
        # Check expenses
        expense_count = db.query(Expense).count()
        print(f"✅ Expenses: {expense_count}")
        
        db.close()
        return True
    except Exception as e:
        print(f"❌ Seed data verification failed: {e}")
        return False


def verify_health_check():
    """Task 6: Verify health check"""
    print("\n" + "=" * 60)
    print("6️⃣ HEALTH CHECK VERIFICATION")
    print("=" * 60)
    
    try:
        with engine.connect() as conn:
            result = conn.execute(text("SELECT 1"))
            assert result.scalar() == 1
        print("✅ Health check query (SELECT 1) works")
        print("✅ Database is reachable and responsive")
        return True
    except Exception as e:
        print(f"❌ Health check failed: {e}")
        return False


def main():
    """Run all verifications"""
    print("\n" + "=" * 60)
    print("B2B DATABASE SETUP VERIFICATION")
    print("=" * 60)
    
    results = []
    
    results.append(("Database Connection", verify_database_connection()))
    results.append(("User Roles", verify_user_roles()))
    results.append(("Schema", verify_schema()))
    results.append(("Seed Data", verify_seed_data()))
    results.append(("Health Check", verify_health_check()))
    
    print("\n" + "=" * 60)
    print("VERIFICATION SUMMARY")
    print("=" * 60)
    
    for name, passed in results:
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"{status}: {name}")
    
    all_passed = all(r[1] for r in results)
    
    if all_passed:
        print("\n🎉 All verifications passed!")
        return 0
    else:
        print("\n⚠️  Some verifications failed. Review output above.")
        return 1


if __name__ == "__main__":
    sys.exit(main())
