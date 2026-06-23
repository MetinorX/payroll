"""initial migration

Revision ID: 0001
Revises: 
Create Date: 2026-06-23

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "0001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "users",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("email", sa.String(length=255), nullable=False),
        sa.Column("hashed_password", sa.String(length=255), nullable=False),
        sa.Column(
            "role",
            sa.Enum("admin", "hr", "employee", name="userrole"),
            nullable=False,
        ),
        sa.Column("is_active", sa.Boolean(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_users_email"), "users", ["email"], unique=True)

    op.create_table(
        "deduction_rules",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("name", sa.String(length=100), nullable=False),
        sa.Column(
            "rule_type",
            sa.Enum("pf", "esi", "professional_tax", "income_tax", name="ruletype"),
            nullable=False,
        ),
        sa.Column("rate", sa.Float(), nullable=False),
        sa.Column("min_income", sa.Float(), nullable=True),
        sa.Column("max_income", sa.Float(), nullable=True),
        sa.Column("employer_rate", sa.Float(), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_table(
        "employees",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("employee_code", sa.String(length=20), nullable=False),
        sa.Column("first_name", sa.String(length=100), nullable=False),
        sa.Column("last_name", sa.String(length=100), nullable=False),
        sa.Column("department", sa.String(length=100), nullable=False),
        sa.Column("designation", sa.String(length=100), nullable=False),
        sa.Column("date_of_joining", sa.Date(), nullable=False),
        sa.Column("basic_salary", sa.Float(), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"],),
        sa.UniqueConstraint("user_id"),
    )
    op.create_index(op.f("ix_employees_employee_code"), "employees", ["employee_code"], unique=True)

    op.create_table(
        "attendance",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("employee_id", sa.Integer(), nullable=False),
        sa.Column("date", sa.Date(), nullable=False),
        sa.Column("clock_in_time", sa.Time(), nullable=True),
        sa.Column("clock_out_time", sa.Time(), nullable=True),
        sa.Column(
            "status",
            sa.Enum("present", "absent", "leave", "half_day", name="attendancestatus"),
            nullable=False,
        ),
        sa.Column(
            "leave_type",
            sa.Enum("sick", "casual", "earned", "unpaid", name="leavetype"),
            nullable=True,
        ),
        sa.Column("notes", sa.String(length=500), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(["employee_id"], ["employees.id"],),
    )
    op.create_index(op.f("ix_attendance_employee_id"), "attendance", ["employee_id"])
    op.create_index(op.f("ix_attendance_date"), "attendance", ["date"])

    op.create_table(
        "salary_components",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("employee_id", sa.Integer(), nullable=False),
        sa.Column(
            "component_type",
            sa.Enum(
                "basic", "hra", "da", "conveyance", "medical", "special", "bonus",
                name="componenttype",
            ),
            nullable=False,
        ),
        sa.Column("amount", sa.Float(), nullable=False),
        sa.Column("effective_from", sa.Date(), nullable=False),
        sa.Column("effective_to", sa.Date(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(["employee_id"], ["employees.id"],),
    )
    op.create_index(op.f("ix_salary_components_employee_id"), "salary_components", ["employee_id"])

    op.create_table(
        "payslips",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("employee_id", sa.Integer(), nullable=False),
        sa.Column("month", sa.Integer(), nullable=False),
        sa.Column("year", sa.Integer(), nullable=False),
        sa.Column("gross_pay", sa.Float(), nullable=False),
        sa.Column("total_deductions", sa.Float(), nullable=False),
        sa.Column("net_pay", sa.Float(), nullable=False),
        sa.Column(
            "status",
            sa.Enum("draft", "finalized", name="payslipstatus"),
            nullable=False,
        ),
        sa.Column("pdf_path", sa.String(length=500), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(["employee_id"], ["employees.id"],),
    )
    op.create_index(op.f("ix_payslips_employee_id"), "payslips", ["employee_id"])

    op.create_table(
        "payslip_line_items",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("payslip_id", sa.Integer(), nullable=False),
        sa.Column("description", sa.String(length=200), nullable=False),
        sa.Column("amount", sa.Float(), nullable=False),
        sa.Column(
            "line_type",
            sa.Enum("earning", "deduction", name="linetype"),
            nullable=False,
        ),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(["payslip_id"], ["payslips.id"],),
    )
    op.create_index(op.f("ix_payslip_line_items_payslip_id"), "payslip_line_items", ["payslip_id"])


def downgrade() -> None:
    op.drop_table("payslip_line_items")
    op.drop_table("payslips")
    op.drop_table("salary_components")
    op.drop_table("attendance")
    op.drop_table("employees")
    op.drop_table("deduction_rules")
    op.drop_table("users")

    op.execute("DROP TYPE IF EXISTS userrole")
    op.execute("DROP TYPE IF EXISTS ruletype")
    op.execute("DROP TYPE IF EXISTS attendancestatus")
    op.execute("DROP TYPE IF EXISTS leavetype")
    op.execute("DROP TYPE IF EXISTS componenttype")
    op.execute("DROP TYPE IF EXISTS payslipstatus")
    op.execute("DROP TYPE IF EXISTS linetype")
