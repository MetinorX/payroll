"""Seed script: creates default deduction rules and sample employees."""
import asyncio
from datetime import date, time

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.database import async_session_factory, engine
from app.database import Base
from app.models.attendance import Attendance, AttendanceStatus
from app.models.deduction_rule import DeductionRule, RuleType
from app.models.employee import Employee
from app.models.salary_component import ComponentType, SalaryComponent
from app.models.user import User, UserRole
from app.services.auth import hash_password



async def seed():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async with async_session_factory() as db:
        # Check if already seeded
        result = await db.execute(select(User).limit(1))
        if result.scalar_one_or_none():
            print("Database already seeded, skipping.")
            return

        # Create deduction rules
        rules = [
            DeductionRule(name="PF Employee 12%", rule_type=RuleType.pf, rate=12.0, max_income=15000, employer_rate=12.0, is_active=True),
            DeductionRule(name="ESI Employee 0.75%", rule_type=RuleType.esi, rate=0.75, max_income=21000, employer_rate=3.25, is_active=True),
            DeductionRule(name="Professional Tax ₹200", rule_type=RuleType.professional_tax, rate=200.0, min_income=10000, is_active=True),
            DeductionRule(name="Income Tax 0-2.5L", rule_type=RuleType.income_tax, rate=0.0, min_income=0, max_income=250000, is_active=True),
            DeductionRule(name="Income Tax 2.5L-5L", rule_type=RuleType.income_tax, rate=5.0, min_income=250000, max_income=500000, is_active=True),
            DeductionRule(name="Income Tax 5L-10L", rule_type=RuleType.income_tax, rate=20.0, min_income=500000, max_income=1000000, is_active=True),
            DeductionRule(name="Income Tax 10L+", rule_type=RuleType.income_tax, rate=30.0, min_income=1000000, is_active=True),
        ]
        for r in rules:
            db.add(r)
        await db.flush()

        # Create admin user
        admin = User(email="admin@example.com", hashed_password=hash_password("admin123"), role=UserRole.admin)
        db.add(admin)
        await db.flush()

        # Create HR user
        hr_user = User(email="hr@example.com", hashed_password=hash_password("hr123"), role=UserRole.hr)
        db.add(hr_user)
        await db.flush()

        # Create employee users
        emp_data = [
            ("emp1@example.com", "emp123", "EMP001", "Aarav", "Sharma", "Engineering", "Senior Developer", 80000),
            ("emp2@example.com", "emp123", "EMP002", "Priya", "Patel", "Engineering", "Junior Developer", 50000),
            ("emp3@example.com", "emp123", "EMP003", "Rahul", "Verma", "HR", "HR Manager", 60000),
        ]

        employees = []
        for email, pwd, code, fn, ln, dept, desig, salary in emp_data:
            user = User(email=email, hashed_password=hash_password(pwd), role=UserRole.employee)
            db.add(user)
            await db.flush()

            emp = Employee(
                user_id=user.id, employee_code=code, first_name=fn, last_name=ln,
                department=dept, designation=desig, date_of_joining=date(2024, 1, 1), basic_salary=salary,
            )
            db.add(emp)
            await db.flush()

            # Salary components
            components = [
                SalaryComponent(employee_id=emp.id, component_type=ComponentType.basic, amount=salary * 0.5, effective_from=date(2026, 1, 1)),
                SalaryComponent(employee_id=emp.id, component_type=ComponentType.hra, amount=salary * 0.25, effective_from=date(2026, 1, 1)),
                SalaryComponent(employee_id=emp.id, component_type=ComponentType.conveyance, amount=1600, effective_from=date(2026, 1, 1)),
                SalaryComponent(employee_id=emp.id, component_type=ComponentType.medical, amount=1250, effective_from=date(2026, 1, 1)),
                SalaryComponent(employee_id=emp.id, component_type=ComponentType.special, amount=salary * 0.25 - 1600 - 1250, effective_from=date(2026, 1, 1)),
            ]
            for c in components:
                db.add(c)
            employees.append(emp)

        await db.flush()

        # Attendance records for June 2024
        for emp in employees:
            for day in range(1, 22):
                if day % 7 == 0:
                    continue  # Skip Sundays
                db.add(Attendance(
                    employee_id=emp.id, date=date(2026, 6, day),
                    clock_in_time=time(9, 0),
                    clock_out_time=time(18, 0),
                    status=AttendanceStatus.present,
                ))

        await db.commit()
        print("Seed data created successfully!")
        print(f"  - {len(rules)} deduction rules")
        print(f"  - 1 admin, 1 HR, {len(employees)} employees")
        print(f"  - Salary components for each employee")
        print(f"  - Attendance records for June 2024")

if __name__ == "__main__":
    asyncio.run(seed())
