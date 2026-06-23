export interface BackendEmployee {
  id: number;
  userId: number;
  employeeCode: string;
  firstName: string;
  lastName: string;
  department: string;
  designation: string;
  dateOfJoining: string;
  basicSalary: number;
  isActive: boolean;
  email: string;
  role: string;
}

export interface FrontendEmployee {
  id: number;
  employeeCode: string;
  firstName: string;
  lastName: string;
  fullName: string;
  email: string;
  department: string;
  position: string;
  salary: number;
  status: string;
  hireDate: string;
  role: string;
}

export interface BackendAttendance {
  id: number;
  employeeId: number;
  date: string;
  clockInTime: string | null;
  clockOutTime: string | null;
  status: string;
  leaveType: string | null;
  notes: string | null;
}

export interface FrontendAttendance {
  id: number;
  employeeId: number;
  employeeName: string;
  date: string;
  clockIn: string | null;
  clockOut: string | null;
  status: string;
  note: string | null;
}

export interface BackendLineItem {
  id: number;
  payslipId: number;
  description: string;
  amount: number;
  lineType: string;
}

export interface BackendPayslip {
  id: number;
  employeeId: number;
  month: number;
  year: number;
  grossPay: number;
  totalDeductions: number;
  netPay: number;
  status: string;
  pdfPath?: string;
  lineItems?: BackendLineItem[];
}

export interface FrontendPayslip {
  id: number;
  employeeName: string;
  period: string;
  netPay: number;
  status: string;
  grossPay: number;
  earnings: { name: string; amount: number }[];
  deductions: { name: string; amount: number }[];
}

export function adaptEmployee(raw: BackendEmployee): FrontendEmployee {
  return {
    id: raw.id,
    employeeCode: raw.employeeCode,
    firstName: raw.firstName,
    lastName: raw.lastName,
    fullName: `${raw.firstName} ${raw.lastName}`,
    email: raw.email,
    department: raw.department,
    position: raw.designation,
    salary: raw.basicSalary,
    status: raw.isActive ? 'active' : 'inactive',
    hireDate: raw.dateOfJoining,
    role: raw.role,
  };
}

export function adaptEmployeeList(items: BackendEmployee[]): FrontendEmployee[] {
  return items.map(adaptEmployee);
}

export function adaptAttendance(raw: BackendAttendance): FrontendAttendance {
  return {
    id: raw.id,
    employeeId: raw.employeeId,
    employeeName: '',
    date: raw.date,
    clockIn: raw.clockInTime,
    clockOut: raw.clockOutTime,
    status: raw.status,
    note: raw.notes,
  };
}

export function adaptAttendanceList(items: BackendAttendance[]): FrontendAttendance[] {
  return items.map(adaptAttendance);
}

export function adaptPayslip(raw: BackendPayslip): FrontendPayslip {
  const earnings = (raw.lineItems || []).filter(li => li.lineType === 'earning');
  const deductions = (raw.lineItems || []).filter(li => li.lineType === 'deduction');
  return {
    id: raw.id,
    employeeName: '',
    period: `${raw.month}/${raw.year}`,
    netPay: raw.netPay,
    status: raw.status,
    grossPay: raw.grossPay,
    earnings: earnings.map(e => ({ name: e.description, amount: e.amount })),
    deductions: deductions.map(d => ({ name: d.description, amount: d.amount })),
  };
}

export function adaptPayslipList(items: BackendPayslip[]): FrontendPayslip[] {
  return items.map(adaptPayslip);
}

