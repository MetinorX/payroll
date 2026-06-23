import { useState, useEffect, useCallback } from 'react';
import { Table, Button, Card, Typography, Space, DatePicker } from 'antd';
import { EyeOutlined } from '@ant-design/icons';
import { payrollApi } from '../../api/endpoints';
import { adaptPayslipList, type BackendPayslip, type FrontendPayslip } from '../../utils/adapters';
import { formatCurrency } from '../../utils/helpers';
import dayjs from 'dayjs';
import PayslipDetailModal from './PayslipDetailModal';

const { MonthPicker } = DatePicker;

export default function PayslipPage() {
  const [payslips, setPayslips] = useState<FrontendPayslip[]>([]);
  const [loading, setLoading] = useState(false);
  const [selectedId, setSelectedId] = useState<number | null>(null);
  const [month, setMonth] = useState<dayjs.Dayjs>(dayjs());

  const fetchPayslips = useCallback(async () => {
    setLoading(true);
    try {
      const { data } = await payrollApi.list({ month: month.month() + 1, year: month.year() });
      const items: BackendPayslip[] = data.items || [];
      setPayslips(adaptPayslipList(items));
    } catch {
      setPayslips([]);
    } finally {
      setLoading(false);
    }
  }, [month]);

  useEffect(() => { fetchPayslips(); }, [fetchPayslips]);

  const columns = [
    { title: 'Period', dataIndex: 'period', key: 'period' },
    { title: 'Gross Pay', dataIndex: 'grossPay', key: 'grossPay', render: (v: number) => formatCurrency(v) },
    { title: 'Net Pay', dataIndex: 'netPay', key: 'netPay', render: (v: number) => formatCurrency(v) },
    { title: 'Status', dataIndex: 'status', key: 'status' },
    {
      title: 'Actions', key: 'actions',
      render: (_: unknown, record: FrontendPayslip) => (
        <Button type="link" icon={<EyeOutlined />} onClick={() => setSelectedId(record.id)}>View</Button>
      ),
    },
  ];

  return (
    <div>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 16 }}>
        <Typography.Title level={4} style={{ margin: 0 }}>My Payslips</Typography.Title>
        <Space>
          <MonthPicker value={month} onChange={(d) => d && setMonth(d)} />
        </Space>
      </div>
      <Card>
        <Table dataSource={payslips} columns={columns} rowKey="id" loading={loading} />
      </Card>
      <PayslipDetailModal payslipId={selectedId} open={!!selectedId} onClose={() => setSelectedId(null)} />
    </div>
  );
}
