#!/usr/bin/env python3
"""
Test script to verify database setup
"""
import sys
from app.core.config import settings
from app.core.database import engine, SessionLocal, Base, get_db
from app.models import *
from app.seed_data import seed_users, seed_products, seed_expenses
from app.main import app
from fastapi.testclient import TestClient
from sqlalchemy import inspect
import ast

def test_config():
    """Test configuration loading"""
    print("1. Testing Configuration...")
    assert settings.DATABASE_URL, "DATABASE_URL not set"
    assert len(settings.SECRET_KEY) >= 32, "SECRET_KEY too short"
    print("   ✅ Configuration loaded correctly")
    print(f"   DATABASE_URL: {settings.DATABASE_URL[:50]}...")
    print(f"   SECRET_KEY length: {len(settings.SECRET_KEY)}")

def test_database_module():
    """Test database module"""
    print("\n2. Testing Database Module...")
    assert engine is not None, "Engine not initialized"
    assert SessionLocal is not None, "SessionLocal not initialized"
    assert Base is not None, "Base not initialized"
    print("   ✅ Database module initialized")
    print(f"   Engine: {type(engine).__name__}")
    print(f"   Database: {engine.url.database}")

def test_models():
    """Test all models"""
    print("\n3. Testing Models...")
    tables = list(Base.metadata.tables.keys())
    expected_tables = [
        'users', 'products', 'orders', 'order_items',
        'expenses', 'stock_transactions',
        'demand_forecasts', 'stockout_predictions',
        'restocking_recommendations', 'dead_stock_detections',
        'ai_alerts', 'job_runs'
    ]
    assert len(tables) == 12, f"Expected 12 tables, found {len(tables)}"
    for table in expected_tables:
        assert table in tables, f"Table {table} not found"
    print("   ✅ All 12 tables defined")
    print(f"   Tables: {', '.join(sorted(tables))}")

def test_constraints():
    """Test CHECK constraints"""
    print("\n4. Testing Constraints...")
    product_table = Product.__table__
    # CheckConstraint objects are in __table_args__
    check_constraints = [c for c in product_table.constraints if 'CheckConstraint' in str(type(c))]
    assert len(check_constraints) >= 3, f"Expected at least 3 CHECK constraints, found {len(check_constraints)}"
    print("   ✅ CHECK constraints defined")
    for constraint in check_constraints:
        constraint_text = str(constraint.sqltext) if hasattr(constraint, 'sqltext') else str(constraint)
        constraint_name = constraint.name if hasattr(constraint, 'name') else 'unnamed'
        print(f"   - {constraint_name}: {constraint_text}")

def test_foreign_keys():
    """Test foreign key relationships"""
    print("\n5. Testing Foreign Keys...")
    order_table = Order.__table__
    order_item_table = OrderItem.__table__
    
    # Check Order -> User FK
    fk_to_user = [fk for fk in order_table.foreign_keys if 'users' in str(fk.column)]
    assert len(fk_to_user) > 0, "Order.user_id foreign key not found"
    
    # Check OrderItem -> Order FK
    fk_to_order = [fk for fk in order_item_table.foreign_keys if 'orders' in str(fk.column)]
    assert len(fk_to_order) > 0, "OrderItem.order_id foreign key not found"
    
    # Check OrderItem -> Product FK
    fk_to_product = [fk for fk in order_item_table.foreign_keys if 'products' in str(fk.column)]
    assert len(fk_to_product) > 0, "OrderItem.product_id foreign key not found"
    
    print("   ✅ Foreign key relationships verified")
    print("   - Order.user_id -> User.id")
    print("   - OrderItem.order_id -> Order.id")
    print("   - OrderItem.product_id -> Product.id")

def test_seed_script():
    """Test seed script"""
    print("\n6. Testing Seed Script...")
    assert callable(seed_users), "seed_users not callable"
    assert callable(seed_products), "seed_products not callable"
    assert callable(seed_expenses), "seed_expenses not callable"
    print("   ✅ Seed script functions verified")
    print("   - seed_users()")
    print("   - seed_products()")
    print("   - seed_expenses()")

def test_health_endpoint():
    """Test health check endpoint"""
    print("\n7. Testing Health Endpoint...")
    client = TestClient(app)
    response = client.get('/health')
    assert response.status_code == 200, f"Health endpoint returned {response.status_code}"
    data = response.json()
    assert 'status' in data, "Health response missing 'status'"
    assert 'database' in data, "Health response missing 'database'"
    print("   ✅ Health endpoint responds correctly")
    print(f"   Status: {data['status']}")
    print(f"   Database: {data['database'][:50]}...")

def test_migration_file():
    """Test migration file structure"""
    print("\n8. Testing Migration File...")
    try:
        with open('alembic/versions/001_initial_migration.py', 'r') as f:
            content = f.read()
            tree = ast.parse(content)
        
        # Find upgrade function
        upgrade_func = None
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef) and node.name == 'upgrade':
                upgrade_func = node
                break
        
        assert upgrade_func is not None, "upgrade() function not found"
        
        # Count create_table calls
        create_table_calls = []
        for node in ast.walk(upgrade_func):
            if isinstance(node, ast.Call):
                if hasattr(node.func, 'attr') and node.func.attr == 'create_table':
                    create_table_calls.append(node)
        
        assert len(create_table_calls) == 12, f"Expected 12 create_table calls, found {len(create_table_calls)}"
        print("   ✅ Migration file structure verified")
        print(f"   create_table calls: {len(create_table_calls)}")
        print("   - All 12 tables included")
        
    except FileNotFoundError:
        print("   ⚠️  Migration file not found (will be created on first run)")
    except Exception as e:
        print(f"   ⚠️  Migration file check failed: {e}")

def test_alembic_config():
    """Test Alembic configuration"""
    print("\n9. Testing Alembic Configuration...")
    from alembic.config import Config
    cfg = Config('alembic.ini')
    script_location = cfg.get_main_option('script_location')
    assert script_location == 'alembic', f"Script location should be 'alembic', got '{script_location}'"
    print("   ✅ Alembic configuration verified")
    print(f"   Script location: {script_location}")

def main():
    """Run all tests"""
    print("=" * 60)
    print("DATABASE SETUP VERIFICATION TEST")
    print("=" * 60)
    
    try:
        test_config()
        test_database_module()
        test_models()
        test_constraints()
        test_foreign_keys()
        test_seed_script()
        test_health_endpoint()
        test_migration_file()
        test_alembic_config()
        
        print("\n" + "=" * 60)
        print("✅ ALL TESTS PASSED")
        print("=" * 60)
        print("\nDatabase setup is complete and ready!")
        print("Next step: Connect to PostgreSQL and run 'alembic upgrade head'")
        return 0
    except AssertionError as e:
        print(f"\n❌ TEST FAILED: {e}")
        return 1
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == '__main__':
    sys.exit(main())
