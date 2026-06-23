import os
from io import BytesIO

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

from app.services.tax_calculator import PayrollResult


def generate_payslip_pdf(
    employee_name: str,
    employee_code: str,
    department: str,
    designation: str,
    month: int,
    year: int,
    result: PayrollResult,
    output_dir: str = "payslips",
) -> str:
    os.makedirs(output_dir, exist_ok=True)
    filename = f"{output_dir}/payslip_{employee_code}_{year}_{month:02d}.pdf"
    filename = os.path.abspath(filename)

    doc = SimpleDocTemplate(filename, pagesize=A4)
    styles = getSampleStyleSheet()
    elements = []

    elements.append(Paragraph(f"PAYSLIP - {month:02d}/{year}", styles["Title"]))
    elements.append(Spacer(1, 5 * mm))

    emp_data = [
        ["Employee", f"{employee_name} ({employee_code})"],
        ["Department", department],
        ["Designation", designation],
    ]
    t = Table(emp_data, colWidths=[100, 300])
    t.setStyle(TableStyle([
        ("FONTNAME", (0, 0), (0, -1), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, -1), 10),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
    ]))
    elements.append(t)
    elements.append(Spacer(1, 10 * mm))

    earnings = [
        ["Earnings", "Amount (₹)"],
        ["Basic", f"{result.basic:.2f}"],
        ["HRA", f"{result.hra:.2f}"],
        ["DA", f"{result.da:.2f}"],
        ["Conveyance", f"{result.conveyance:.2f}"],
        ["Medical", f"{result.medical:.2f}"],
        ["Special", f"{result.special:.2f}"],
        ["Bonus", f"{result.bonus:.2f}"],
        ["Gross Pay", f"{result.gross_pay:.2f}"],
    ]
    t1 = Table(earnings, colWidths=[200, 150])
    t1.setStyle(TableStyle([
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTNAME", (0, -1), (-1, -1), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, -1), 10),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
        ("BACKGROUND", (0, 0), (-1, 0), colors.lightgrey),
        ("ALIGN", (1, 0), (1, -1), "RIGHT"),
    ]))
    elements.append(t1)
    elements.append(Spacer(1, 5 * mm))

    deductions_data = [
        ["Deductions", "Amount (₹)"],
        ["PF (Employee)", f"{result.deductions.pf_employee:.2f}"],
        ["ESI (Employee)", f"{result.deductions.esi_employee:.2f}"],
        ["Professional Tax", f"{result.deductions.professional_tax:.2f}"],
        ["Income Tax", f"{result.deductions.income_tax:.2f}"],
        ["Total Deductions", f"{result.deductions.total_employee_deductions:.2f}"],
    ]
    t2 = Table(deductions_data, colWidths=[200, 150])
    t2.setStyle(TableStyle([
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTNAME", (0, -1), (-1, -1), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, -1), 10),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
        ("BACKGROUND", (0, 0), (-1, 0), colors.lightgrey),
        ("ALIGN", (1, 0), (1, -1), "RIGHT"),
    ]))
    elements.append(t2)
    elements.append(Spacer(1, 5 * mm))

    net_data = [["Net Pay", f"₹ {result.net_pay:.2f}"]]
    t3 = Table(net_data, colWidths=[200, 150])
    t3.setStyle(TableStyle([
        ("FONTNAME", (0, 0), (-1, -1), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, -1), 14),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.black),
        ("BACKGROUND", (0, 0), (-1, -1), colors.lightblue),
        ("ALIGN", (1, 0), (1, -1), "RIGHT"),
        ("TOPPADDING", (0, 0), (-1, -1), 8),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
    ]))
    elements.append(t3)

    doc.build(elements)
    return filename
