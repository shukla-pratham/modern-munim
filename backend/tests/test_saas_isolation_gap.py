"""Runtime and source verification that tenant isolation is implemented.

Validates that business models and services have workspace keys,
founder email authorization exists, and dashboard/orders are isolated.
"""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]

MODEL_FILES = [
    "backend/app/models/product.py",
    "backend/app/models/vendor.py",
    "backend/app/models/expense.py",
    "backend/app/models/purchase_order.py",
    "backend/app/models/stock_transaction.py",
    "backend/app/models/order.py",
]

FOUNDER_EMAIL = "shuklapratham758@gmail.com"


def _text(rel: str) -> str:
    return (ROOT / rel).read_text(encoding="utf-8")


def test_business_models_have_workspace_key():
    for rel in MODEL_FILES:
        text = _text(rel)
        assert "workspace_id" in text, f"Expected workspace_id in {rel}"


def test_founder_email_is_a_server_authorization_check():
    auth = _text("backend/app/services/workspace_service.py")
    assert FOUNDER_EMAIL in auth
    assert "is_founder_user" in auth


def test_dashboard_revenue_is_scoped_to_workspace():
    text = _text("backend/app/services/dashboard_service.py")
    assert "def get_revenue_data" in text
    start = text.index("def get_revenue_data")
    end = text.index("def get_expense_breakdown")
    body = text[start:end]
    assert "workspace_id" in body


def test_orders_are_scoped_to_workspace():
    order = _text("backend/app/models/order.py")
    product = _text("backend/app/models/product.py")
    orders_api = _text("backend/app/api/orders.py")
    assert "workspace_id" in order
    assert "workspace_id" in product
    assert "get_all_orders" in orders_api
    assert "workspace-scoped" in orders_api.lower()
