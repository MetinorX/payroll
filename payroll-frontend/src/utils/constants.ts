export const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

export const CURRENCY_SYMBOL = '₹';
export const CURRENCY_CODE = 'INR';

export const ROLES = {
  ADMIN: 'admin',
  HR: 'hr',
  EMPLOYEE: 'employee',
} as const;

export const ROLE_LABELS: Record<string, string> = {
  admin: 'Admin',
  hr: 'HR',
  employee: 'Employee',
};

export const MENU_ITEMS: Record<string, { key: string; label: string; path: string; roles: string[] }[]> = {
  main: [
    { key: 'dashboard', label: 'Dashboard', path: '/dashboard', roles: ['admin', 'hr', 'employee'] },
    { key: 'employees', label: 'Employees', path: '/employees', roles: ['admin', 'hr'] },
    { key: 'attendance', label: 'Attendance', path: '/attendance', roles: ['admin', 'hr', 'employee'] },
    { key: 'salary', label: 'Salary Config', path: '/salary', roles: ['admin', 'hr'] },
    { key: 'payroll', label: 'Payroll Run', path: '/payroll', roles: ['admin', 'hr'] },
    { key: 'reports', label: 'Reports', path: '/reports', roles: ['admin', 'hr'] },
    { key: 'payslips', label: 'My Payslips', path: '/payslips', roles: ['admin', 'hr', 'employee'] },
  ],
};

export const PAYSLIP_STATUS = {
  DRAFT: 'draft',
  FINALIZED: 'finalized',
} as const;

export const ATTENDANCE_STATUS = {
  PRESENT: 'present',
  ABSENT: 'absent',
  HALF_DAY: 'half_day',
  LEAVE: 'leave',
} as const;

export const LEAVE_TYPES = {
  SICK: 'sick',
  CASUAL: 'casual',
  EARNED: 'earned',
  UNPAID: 'unpaid',
} as const;

export const COMPONENT_TYPES = [
  { value: 'basic', label: 'Basic Salary' },
  { value: 'hra', label: 'House Rent Allowance' },
  { value: 'da', label: 'Dearness Allowance' },
  { value: 'conveyance', label: 'Conveyance Allowance' },
  { value: 'medical', label: 'Medical Allowance' },
  { value: 'special', label: 'Special Allowance' },
  { value: 'bonus', label: 'Bonus' },
] as const;
