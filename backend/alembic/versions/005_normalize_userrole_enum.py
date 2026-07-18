"""Normalize userrole enum values to lowercase

Revision ID: 005_normalize_userrole
Revises: 004_po_if_missing
Create Date: 2026-06-07

"""
from alembic import op

revision = "005_normalize_userrole"
down_revision = "004_po_if_missing"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # PostgreSQL: new enum labels must be committed before they can be used in UPDATE.
    with op.get_context().autocommit_block():
        for value in ("customer", "admin"):
            op.execute(f"ALTER TYPE userrole ADD VALUE IF NOT EXISTS '{value}'")

    op.execute("UPDATE users SET role = 'admin' WHERE role::text = 'ADMIN'")
    op.execute("UPDATE users SET role = 'customer' WHERE role::text = 'CUSTOMER'")
    op.execute("UPDATE users SET role = 'manager' WHERE role::text = 'MANAGER'")


def downgrade() -> None:
    pass
