import client from './client';

export const authApi = {
  login: (data: { email: string; password: string }) => client.post('/auth/login', data),
  refresh: (data: { refresh_token: string }) => client.post('/auth/refresh', data),
  me: () => client.get('/auth/me'),
};

export const employeeApi = {
  list: (params?: { page?: number; page_size?: number; department?: string; designation?: string; is_active?: boolean; search?: string }) =>
    client.get('/employees', { params }),
  get: (id: number) => client.get(`/employees/${id}`),
  create: (data: Record<string, unknown>) => client.post('/employees', data),
  update: (id: number, data: Record<string, unknown>) => client.put(`/employees/${id}`, data),
  delete: (id: number) => client.delete(`/employees/${id}`),
};

export const attendanceApi = {
  list: (params?: { employee_id?: number; date_from?: string; date_to?: string; page?: number; page_size?: number }) =>
    client.get('/attendance', { params }),
  clockIn: (data: { employee_id: number; date: string; clock_in_time: string }) => client.post('/attendance/clock-in', data),
  clockOut: (data: { employee_id: number; date: string; clock_out_time: string }) => client.post('/attendance/clock-out', data),
  leave: (data: { employee_id: number; date: string; leave_type: string; notes?: string }) => client.post('/attendance/leave', data),
};

export const salaryApi = {
  get: (employeeId: number) => client.get(`/salary-config/${employeeId}`),
  create: (employeeId: number, data: { component_type: string; amount: number; effective_from: string; effective_to?: string | null }) =>
    client.post(`/salary-config/${employeeId}`, data),
  bulkUpdate: (employeeId: number, data: { components: Array<{ component_type: string; amount: number; effective_from: string; effective_to?: string | null }> }) =>
    client.post(`/salary-config/${employeeId}/bulk`, data),
};

export const payrollApi = {
  run: (data: { employee_id: number; month: number; year: number }) => client.post('/payroll/run', data),
  runAll: (data: { month: number; year: number }) => client.post('/payroll/run-all', data),
  list: (params?: { employee_id?: number; month?: number; year?: number; page?: number; page_size?: number }) =>
    client.get('/payroll/payslips', { params }),
  get: (id: number) => client.get(`/payroll/payslips/${id}`),
  finalize: (id: number) => client.post(`/payroll/payslips/${id}/finalize`),
  download: (id: number) =>
    client.get(`/payroll/download/${id}`, { responseType: 'blob' }),
};

export const reportApi = {
  monthly: (params?: { month?: number; year?: number }) =>
    client.get('/reports/monthly', { params }),
  department: (params?: { month?: number; year?: number }) =>
    client.get('/reports/department', { params }),
  ytd: (params?: { employee_id?: number; year?: number }) =>
    client.get('/reports/ytd', { params }),
  export: (params: { month: number; year: number }) =>
    client.get('/reports/export', { params, responseType: 'blob' }),
};

export const dashboardApi = {
  stats: (params?: { month?: number; year?: number }) => client.get('/dashboard/stats', { params }),
  payrollChart: (params?: { year?: number }) => client.get('/dashboard/payroll-chart', { params }),
};
