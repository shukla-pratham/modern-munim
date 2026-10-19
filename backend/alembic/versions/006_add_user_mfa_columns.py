"""Add MFA columns to users

Revision ID: 006_add_user_mfa
Revises: 005_normalize_userrole
Create Date: 2026-10-06

"""
from alembic import op
import sqlalchemy as sa

revision = "006_add_user_mfa"
down_revision = "005_normalize_userrole"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "users",
        sa.Column("mfa_enabled", sa.Boolean(), nullable=False, server_default=sa.text("false")),
    )
    op.add_column(
        "users",
        sa.Column("mfa_secret", sa.String(), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("users", "mfa_secret")
    op.drop_column("users", "mfa_enabled")
