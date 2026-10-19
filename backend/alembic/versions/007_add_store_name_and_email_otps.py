"""Add store_name on users and email_otps table

Revision ID: 007_store_email_otp
Revises: 006_add_user_mfa
Create Date: 2026-10-06

"""
from alembic import op
import sqlalchemy as sa

revision = "007_store_email_otp"
down_revision = "006_add_user_mfa"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("users", sa.Column("store_name", sa.String(), nullable=True))
    op.create_table(
        "email_otps",
        sa.Column("email", sa.String(), primary_key=True, nullable=False),
        sa.Column("code_hash", sa.String(), nullable=False),
        sa.Column("store_name", sa.String(), nullable=True),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("attempt_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=True,
        ),
    )


def downgrade() -> None:
    op.drop_table("email_otps")
    op.drop_column("users", "store_name")
