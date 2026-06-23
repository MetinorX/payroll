import calendar
from dataclasses import dataclass
from datetime import date
from typing import List

from sqlalchemy import select, func, and_
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.attendance import Attendance, AttendanceStatus
from app.models.deduction_rule import DeductionRule, RuleType
from app.models.salary_component import ComponentType, SalaryComponent


@dataclass
class DeductionBreakdown:
    pf_employee: float = 0.0
    pf_employer: float = 0.0
    esi_employee: float = 0.0
    esi_employer: float = 0.0
    professional_tax: float = 0.0
    income_tax: float = 0.0
    total_employee_deductions: float = 0.0


@dataclass
class PayrollResult:
    gross_pay: float
    basic: float
    hra: float
    da: float
    conveyance: float
    medical: float
    special: float
    bonus: float
    deductions: DeductionBreakdown
    net_pay: float
    working_days: int = 0
    attended_days: int = 0
    attendance_factor: float = 1.0


def working_days_in_month(month: int, year: int) -> int:
    _, days_in_month = calendar.monthrange(year, month)
    count = 0
    for day in range(1, days_in_month + 1):
        d = date(year, month, day)
        if d.weekday() < 5:
            count += 1
    return count


async def attended_days(db: AsyncSession, employee_id: int, month: int, year: int) -> int:
    result = await db.execute(
        select(func.count(Attendance.id)).where(
            and_(
                Attendance.employee_id == employee_id,
                func.extract("month", Attendance.date) == month,
                func.extract("year", Attendance.date) == year,
                Attendance.status != AttendanceStatus.absent,
            )
        )
    )
    return result.scalar() or 0


async def get_active_components(db: AsyncSession, employee_id: int) -> dict[ComponentType, float]:
    result = await db.execute(
        select(SalaryComponent).where(
            SalaryComponent.employee_id == employee_id,
            SalaryComponent.effective_to.is_(None),
        )
    )
    components: dict[ComponentType, float] = {}
    for c in result.scalars().all():
        components[c.component_type] = components.get(c.component_type, 0) + c.amount
    return components


async def get_tax_rules(db: AsyncSession) -> dict[RuleType, List[DeductionRule]]:
    result = await db.execute(
        select(DeductionRule).where(DeductionRule.is_active.is_(True))
    )
    rules: dict[RuleType, list[DeductionRule]] = {}
    for r in result.scalars().all():
        rules.setdefault(r.rule_type, []).append(r)
    return rules


def calculate_pf(basic: float, rules: List[DeductionRule]) -> tuple[float, float]:
    pf_rules = [r for r in rules if r.rule_type == RuleType.pf]
    if not pf_rules:
        return 0.0, 0.0
    rule = pf_rules[0]
    applicable_basic = min(basic, rule.max_income or float("inf"))
    employee_contrib = applicable_basic * rule.rate / 100
    employer_contrib = applicable_basic * (rule.employer_rate or rule.rate) / 100
    return round(employee_contrib, 2), round(employer_contrib, 2)


def calculate_esi(gross: float, rules: List[DeductionRule]) -> tuple[float, float]:
    esi_rules = [r for r in rules if r.rule_type == RuleType.esi]
    if not esi_rules:
        return 0.0, 0.0
    rule = esi_rules[0]
    if gross > (rule.max_income or 0):
        return 0.0, 0.0
    employee_contrib = gross * rule.rate / 100
    employer_contrib = gross * (rule.employer_rate or 3.25) / 100
    return round(employee_contrib, 2), round(employer_contrib, 2)


def calculate_professional_tax(gross: float, rules: List[DeductionRule]) -> float:
    pt_rules = [r for r in rules if r.rule_type == RuleType.professional_tax]
    if not pt_rules:
        return 0.0
    rule = pt_rules[0]
    if gross > (rule.min_income or 0):
        return rule.rate
    return 0.0


def calculate_income_tax(annual_gross: float, rules: List[DeductionRule]) -> float:
    tax_rules = sorted(
        [r for r in rules if r.rule_type == RuleType.income_tax],
        key=lambda x: x.min_income or 0,
    )
    tax = 0.0
    remaining = annual_gross

    for rule in tax_rules:
        slab_min = rule.min_income or 0
        slab_max = rule.max_income or float("inf")
        taxable_in_slab = max(0, min(remaining, slab_max - slab_min))
        tax += taxable_in_slab * rule.rate / 100
        remaining -= taxable_in_slab
        if remaining <= 0:
            break

    return round(tax, 2)


async def compute_payroll(
    db: AsyncSession,
    employee_id: int,
    month: int,
    year: int,
) -> PayrollResult:
    components = await get_active_components(db, employee_id)
    rules = await get_tax_rules(db)

    basic = components.get(ComponentType.basic, 0)
    hra = components.get(ComponentType.hra, 0)
    da = components.get(ComponentType.da, 0)
    conveyance = components.get(ComponentType.conveyance, 0)
    medical = components.get(ComponentType.medical, 0)
    special = components.get(ComponentType.special, 0)
    bonus = components.get(ComponentType.bonus, 0)

    full_gross = basic + hra + da + conveyance + medical + special + bonus

    w_days = working_days_in_month(month, year)
    a_days = await attended_days(db, employee_id, month, year)
    attendance_factor = a_days / w_days if w_days > 0 and a_days > 0 else 1.0
    if a_days == 0:
        attendance_factor = 1.0

    gross_pay = round(full_gross * attendance_factor, 2)
    prorated_basic = round(basic * attendance_factor, 2)

    pf_emp, pf_er = calculate_pf(prorated_basic, rules.get(RuleType.pf, []))
    esi_emp, esi_er = calculate_esi(gross_pay, rules.get(RuleType.esi, []))
    pt = calculate_professional_tax(gross_pay, rules.get(RuleType.professional_tax, []))

    annual_gross = full_gross * 12
    annual_income_tax = calculate_income_tax(annual_gross, rules.get(RuleType.income_tax, []))
    monthly_income_tax = round(annual_income_tax / 12, 2)

    deductions = DeductionBreakdown(
        pf_employee=pf_emp,
        pf_employer=pf_er,
        esi_employee=esi_emp,
        esi_employer=esi_er,
        professional_tax=pt,
        income_tax=monthly_income_tax,
        total_employee_deductions=round(pf_emp + esi_emp + pt + monthly_income_tax, 2),
    )

    net_pay = round(gross_pay - deductions.total_employee_deductions, 2)

    return PayrollResult(
        gross_pay=gross_pay,
        basic=basic,
        hra=hra,
        da=da,
        conveyance=conveyance,
        medical=medical,
        special=special,
        bonus=bonus,
        deductions=deductions,
        net_pay=net_pay,
        working_days=w_days,
        attended_days=a_days,
        attendance_factor=attendance_factor,
    )
