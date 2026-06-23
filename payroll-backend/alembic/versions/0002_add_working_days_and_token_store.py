"""add working_days/attended_days to payslips, token_store table

Revision ID: 0002
Revises: 0001
Create Date: 2026-06-23

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "0002"
down_revision: Union[str, None] = "0001"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("payslips", sa.Column("working_days", sa.Integer(), nullable=True))
    op.add_column("payslips", sa.Column("attended_days", sa.Integer(), nullable=True))

    op.create_table(
        "token_store",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("jti", sa.String(length=128), nullable=False),
        sa.Column("user_email", sa.String(length=255), nullable=False),
        sa.Column("is_used", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_token_store_jti"), "token_store", ["jti"], unique=True)
    op.create_index(op.f("ix_token_store_user_email"), "token_store", ["user_email"])


def downgrade() -> None:
    op.drop_column("payslips", "attended_days")
    op.drop_column("payslips", "working_days")
    op.drop_table("token_store")
