import { useState, useEffect } from 'react';
import { Card, Row, Col, Statistic, Table, Button, DatePicker, Space, Typography, message } from 'antd';
import { DownloadOutlined } from '@ant-design/icons';
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, PieChart, Pie, Cell, Legend } from 'recharts';
import { reportApi } from '../../api/endpoints';
import { formatCurrency } from '../../utils/helpers';
import dayjs from 'dayjs';

const { MonthPicker } = DatePicker;
const COLORS = ['#1677ff', '#52c41a', '#faad14', '#ff4d4f', '#722ed1', '#13c2c2'];

export default function ReportsPage() {
  const [month, setMonth] = useState<dayjs.Dayjs>(dayjs());
  const [summary, setSummary] = useState<{
    total_employees: number;
    total_gross_pay: number;
    total_deductions: number;
    total_net_pay: number;
    finalized_count: number;
  } | null>(null);
  const [deptData, setDeptData] = useState<{ department: string; employee_count: number; total_gross: number; total_net: number }[]>([]);
  const [loading, setLoading] = useState(false);

  const fetchReports = async () => {
    setLoading(true);
    const params = { month: month.month() + 1, year: month.year() };
    try {
      const summaryRes = await reportApi.monthly(params);
      setSummary(summaryRes.data);
    } catch (err) {
      console.error('Failed to load monthly report:', err);
      message.error('Failed to load summary');
    }
    try {
      const deptRes = await reportApi.department(params);
      setDeptData(deptRes.data || []);
    } catch (err) {
      console.error('Failed to load department report:', err);
      message.error('Failed to load department breakdown');
    }
    setLoading(false);
  };

  useEffect(() => { fetchReports(); }, [month]);

  const handleExport = async () => {
    try {
      const response = await reportApi.export({ month: month.month() + 1, year: month.year() });
      const url = window.URL.createObjectURL(new Blob([response.data]));
      const link = document.createElement('a');
      link.href = url;
      link.setAttribute('download', `payroll-report-${month.format('YYYY-MM')}.csv`);
      document.body.appendChild(link);
      link.click();
      link.remove();
      window.URL.revokeObjectURL(url);
      message.success('Report exported as CSV');
    } catch {
      message.error('Failed to export report');
    }
  };

  const deptColumns = [
    { title: 'Department', dataIndex: 'department', key: 'department' },
    { title: 'Employees', dataIndex: 'employee_count', key: 'employee_count' },
    { title: 'Total Gross', dataIndex: 'total_gross', key: 'total_gross', render: (v: number) => formatCurrency(v) },
    { title: 'Total Net', dataIndex: 'total_net', key: 'total_net', render: (v: number) => formatCurrency(v) },
  ];

  const deptChartData = deptData.map(d => ({
    department: d.department,
    amount: d.total_gross,
  }));

  return (
    <div>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 16, flexWrap: 'wrap', gap: 8 }}>
        <Typography.Title level={4} style={{ margin: 0 }}>Reports</Typography.Title>
        <Space wrap>
          <MonthPicker value={month} onChange={(d) => d && setMonth(d)} />
          <Button type="primary" onClick={fetchReports}>Generate</Button>
          <Button icon={<DownloadOutlined />} onClick={handleExport}>Export CSV</Button>
        </Space>
      </div>

      {summary && (
        <Row gutter={[16, 16]}>
          <Col xs={12} lg={6}>
            <Card><Statistic title="Total Employees" value={summary.total_employees} /></Card>
          </Col>
          <Col xs={12} lg={6}>
            <Card><Statistic title="Gross Pay" value={summary.total_gross_pay} precision={2} prefix="₹" /></Card>
          </Col>
          <Col xs={12} lg={6}>
            <Card><Statistic title="Net Pay" value={summary.total_net_pay} precision={2} prefix="₹" /></Card>
          </Col>
          <Col xs={12} lg={6}>
            <Card><Statistic title="Total Deductions" value={summary.total_deductions} precision={2} prefix="₹" /></Card>
          </Col>
        </Row>
      )}

      <Row gutter={16} style={{ marginTop: 16 }}>
        <Col xs={24} lg={14}>
          <Card title="Department Payroll Breakdown">
            {deptChartData.length > 0 ? (
              <ResponsiveContainer width="100%" height={300}>
                <BarChart data={deptChartData}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis dataKey="department" />
                  <YAxis />
                  <Tooltip formatter={(value: unknown) => formatCurrency(Number(value))} />
                  <Bar dataKey="amount" fill="#1677ff" radius={[4, 4, 0, 0]} />
                </BarChart>
              </ResponsiveContainer>
            ) : (
              <div style={{ textAlign: 'center', padding: 40, color: '#999' }}>No data</div>
            )}
          </Card>
        </Col>
        <Col xs={24} lg={10}>
          <Card title="Distribution">
            {deptChartData.length > 0 ? (
              <ResponsiveContainer width="100%" height={300}>
                <PieChart>
                  <Pie data={deptChartData} dataKey="amount" nameKey="department" cx="50%" cy="50%" outerRadius={80} label>
                    {deptChartData.map((_, i) => <Cell key={i} fill={COLORS[i % COLORS.length]} />)}
                  </Pie>
                  <Legend />
                  <Tooltip formatter={(value: unknown) => formatCurrency(Number(value))} />
                </PieChart>
              </ResponsiveContainer>
            ) : (
              <div style={{ textAlign: 'center', padding: 40, color: '#999' }}>No data</div>
            )}
          </Card>
        </Col>
      </Row>

      <Card title="Department Summary" style={{ marginTop: 16 }}>
        <Table dataSource={deptData} columns={deptColumns} rowKey="department" loading={loading} pagination={false} />
      </Card>
    </div>
  );
}
