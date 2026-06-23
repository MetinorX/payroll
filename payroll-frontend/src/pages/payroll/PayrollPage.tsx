import { useState, useEffect } from 'react';
import { Card, Button, Table, DatePicker, message, Typography, Space, Spin, Alert, Select } from 'antd';
import { PayCircleOutlined, FileTextOutlined, CheckCircleOutlined } from '@ant-design/icons';
import { payrollApi, employeeApi } from '../../api/endpoints';
import { adaptPayslipList, type BackendPayslip, type FrontendPayslip } from '../../utils/adapters';
import { formatCurrency } from '../../utils/helpers';
import dayjs from 'dayjs';
import PayslipDetailModal from '../payslip/PayslipDetailModal';

const { MonthPicker } = DatePicker;

export default function PayrollPage() {
  const [month, setMonth] = useState<dayjs.Dayjs>(dayjs());
  const [employeeId, setEmployeeId] = useState<number | undefined>(undefined);
  const [employees, setEmployees] = useState<{ id: number; firstName: string; lastName: string; employeeCode: string }[]>([]);
  const [payslips, setPayslips] = useState<FrontendPayslip[]>([]);
  const [loading, setLoading] = useState(false);
  const [running, setRunning] = useState(false);
  const [selectedPayslipId, setSelectedPayslipId] = useState<number | null>(null);
  const [finalizing, setFinalizing] = useState<number | null>(null);

  useEffect(() => {
    employeeApi.list({ page_size: 100 }).then(({ data }) => {
      setEmployees((data.items || []).map((e: { id: number; firstName: string; lastName: string; employeeCode: string }) => ({
        id: e.id,
        firstName: e.firstName,
        lastName: e.lastName,
        employeeCode: e.employeeCode,
      })));
    }).catch(() => {});
  }, []);

  const handleFinalize = async (id: number) => {
    setFinalizing(id);
    try {
      await payrollApi.finalize(id);
      message.success('Payslip finalized');
      fetchPayslips();
    } catch {
      message.error('Failed to finalize payslip');
    } finally {
      setFinalizing(null);
    }
  };

  const fetchPayslips = async () => {
    setLoading(true);
    try {
      const params: Record<string, unknown> = { month: month.month() + 1, year: month.year() };
      if (employeeId) params.employee_id = employeeId;
      const { data } = await payrollApi.list(params);
      const items: BackendPayslip[] = data.items || [];
      setPayslips(adaptPayslipList(items));
    } catch {
      message.error('Failed to load payslips');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { fetchPayslips(); }, [month, employeeId]);

  const handleRunPayroll = async () => {
    setRunning(true);
    try {
      if (employeeId) {
        await payrollApi.run({ employee_id: employeeId, month: month.month() + 1, year: month.year() });
        message.success('Payroll run for employee');
      } else {
        const { data } = await payrollApi.runAll({ month: month.month() + 1, year: month.year() });
        message.success(`Payroll run for ${data.length || 0} employees`);
      }
      fetchPayslips();
    } catch {
      message.error('Failed to run payroll');
    } finally {
      setRunning(false);
    }
  };

  const columns = [
    { title: 'ID', dataIndex: 'id', key: 'id' },
    { title: 'Period', dataIndex: 'period', key: 'period' },
    { title: 'Gross Pay', dataIndex: 'grossPay', key: 'grossPay', render: (v: number) => formatCurrency(v) },
    { title: 'Net Pay', dataIndex: 'netPay', key: 'netPay', render: (v: number) => formatCurrency(v) },
    { title: 'Status', dataIndex: 'status', key: 'status' },
    {
      title: 'Actions', key: 'actions',
      render: (_: unknown, record: FrontendPayslip) => (
        <Space>
          <Button type="link" icon={<FileTextOutlined />} onClick={() => { setSelectedPayslipId(record.id); }}>View</Button>
          {record.status === 'draft' && (
            <Button type="primary" size="small" icon={<CheckCircleOutlined />} loading={finalizing === record.id} onClick={() => handleFinalize(record.id)}>
              Finalize
            </Button>
          )}
        </Space>
      ),
    },
  ];

  return (
    <div>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 16, flexWrap: 'wrap', gap: 8 }}>
        <Typography.Title level={4} style={{ margin: 0 }}>Payroll Processing</Typography.Title>
        <Space wrap>
          <Select
            placeholder="All Employees"
            allowClear
            style={{ width: 200 }}
            value={employeeId}
            onChange={setEmployeeId}
            options={employees.map(e => ({ value: e.id, label: `${e.firstName} ${e.lastName} (${e.employeeCode})` }))}
          />
          <MonthPicker value={month} onChange={(d) => d && setMonth(d)} />
          <Button type="primary" icon={<PayCircleOutlined />} loading={running} onClick={handleRunPayroll}>
            {employeeId ? 'Run Payroll' : 'Run All'}
          </Button>
        </Space>
      </div>
      {running && (
        <Alert message="Processing payroll..." description="Please wait while payroll is being calculated." type="info" showIcon icon={<Spin />} style={{ marginBottom: 16 }} />
      )}
      <Card>
        <Table
          dataSource={payslips}
          columns={columns}
          rowKey="id"
          loading={loading}
        />
      </Card>

      <PayslipDetailModal
        payslipId={selectedPayslipId}
        open={!!selectedPayslipId}
        onClose={() => setSelectedPayslipId(null)}
      />
    </div>
  );
}
