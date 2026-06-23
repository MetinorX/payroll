import { useState, useEffect } from 'react';
import { Row, Col, Card, Statistic, Spin, Alert } from 'antd';
import { TeamOutlined, CheckCircleOutlined, UserOutlined } from '@ant-design/icons';
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts';
import { dashboardApi } from '../../api/endpoints';
import { formatCurrency } from '../../utils/helpers';
import dayjs from 'dayjs';

export default function DashboardPage() {
  const [stats, setStats] = useState<{
    totalEmployees: number;
    activeEmployees: number;
    totalPayslipsThisMonth: number;
    finalizedPayslipsThisMonth: number;
    monthlyGrossPay: number;
    monthlyNetPay: number;
    monthlyTotalDeductions: number;
  } | null>(null);
  const [chartData, setChartData] = useState<{ month: string; totalGross: number; totalNet: number }[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  useEffect(() => {
    const fetchData = async () => {
      try {
        const currentMonth = dayjs().month() + 1;
        const currentYear = dayjs().year();
        const [statsRes, chartRes] = await Promise.all([
          dashboardApi.stats({ month: currentMonth, year: currentYear }),
          dashboardApi.payrollChart({ year: currentYear }),
        ]);
        setStats(statsRes.data);
        setChartData(chartRes.data?.data || []);
      } catch {
        setError('Failed to load dashboard data. Is the backend running?');
      } finally {
        setLoading(false);
      }
    };
    fetchData();
  }, []);

  if (loading) return <div style={{ textAlign: 'center', padding: 80 }}><Spin size="large" /></div>;
  if (error) return <Alert message={error} type="warning" showIcon />;

  return (
    <div>
      <Row gutter={[16, 16]}>
        <Col xs={24} sm={12} lg={6}>
          <Card hoverable>
            <Statistic title="Total Employees" value={stats?.totalEmployees || 0} prefix={<TeamOutlined />} />
          </Card>
        </Col>
        <Col xs={24} sm={12} lg={6}>
          <Card hoverable>
            <Statistic title="Active Employees" value={stats?.activeEmployees || 0} prefix={<UserOutlined />} />
          </Card>
        </Col>
        <Col xs={24} sm={12} lg={6}>
          <Card hoverable>
            <Statistic title="Payslips This Month" value={stats?.totalPayslipsThisMonth || 0} prefix={<CheckCircleOutlined />} />
          </Card>
        </Col>
        <Col xs={24} sm={12} lg={6}>
          <Card hoverable>
            <Statistic title="Monthly Gross Pay" value={stats?.monthlyGrossPay || 0} prefix="₹" precision={2} valueStyle={{ fontSize: 18 }} />
          </Card>
        </Col>
      </Row>
      <Card title="Monthly Payroll Trend" style={{ marginTop: 16 }}>
        {chartData.length > 0 ? (
          <ResponsiveContainer width="100%" height={300}>
            <BarChart data={chartData}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="month" />
              <YAxis />
              <Tooltip formatter={(value: unknown) => formatCurrency(Number(value))} />
              <Bar dataKey="totalGross" fill="#1677ff" radius={[4, 4, 0, 0]} name="Gross Pay" />
              <Bar dataKey="totalNet" fill="#52c41a" radius={[4, 4, 0, 0]} name="Net Pay" />
            </BarChart>
          </ResponsiveContainer>
        ) : (
          <div style={{ textAlign: 'center', padding: 40, color: '#999' }}>No payroll data yet</div>
        )}
      </Card>
    </div>
  );
}
