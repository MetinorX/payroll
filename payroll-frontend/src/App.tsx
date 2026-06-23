import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { ConfigProvider } from 'antd';
import { AuthProvider } from './contexts/AuthContext';
import AppLayout from './components/layout/AppLayout';
import ProtectedRoute from './components/layout/ProtectedRoute';
import LoginPage from './pages/login/LoginPage';
import DashboardPage from './pages/dashboard/DashboardPage';
import EmployeesPage from './pages/employees/EmployeesPage';
import AttendancePage from './pages/attendance/AttendancePage';
import SalaryPage from './pages/salary/SalaryPage';
import PayrollPage from './pages/payroll/PayrollPage';
import PayslipPage from './pages/payslip/PayslipPage';
import ReportsPage from './pages/reports/ReportsPage';

export default function App() {
  return (
    <ConfigProvider theme={{ token: { colorPrimary: '#1677ff' } }}>
      <BrowserRouter>
        <AuthProvider>
          <Routes>
            <Route path="/login" element={<LoginPage />} />
            <Route
              element={
                <ProtectedRoute>
                  <AppLayout />
                </ProtectedRoute>
              }
            >
              <Route path="/dashboard" element={<DashboardPage />} />
              <Route path="/employees" element={<ProtectedRoute roles={['admin', 'hr']}><EmployeesPage /></ProtectedRoute>} />
              <Route path="/attendance" element={<AttendancePage />} />
              <Route path="/salary" element={<ProtectedRoute roles={['admin', 'hr']}><SalaryPage /></ProtectedRoute>} />
              <Route path="/payroll" element={<ProtectedRoute roles={['admin', 'hr']}><PayrollPage /></ProtectedRoute>} />
              <Route path="/payslips" element={<PayslipPage />} />
              <Route path="/reports" element={<ProtectedRoute roles={['admin', 'hr']}><ReportsPage /></ProtectedRoute>} />
              <Route path="/" element={<Navigate to="/dashboard" replace />} />
            </Route>
            <Route path="*" element={<Navigate to="/dashboard" replace />} />
          </Routes>
        </AuthProvider>
      </BrowserRouter>
    </ConfigProvider>
  );
}
