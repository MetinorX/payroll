import { useEffect, useState } from 'react';
import { Modal, Table, Button, Descriptions, Typography, Spin, message, Divider, Space } from 'antd';
import { DownloadOutlined } from '@ant-design/icons';
import { payrollApi, employeeApi } from '../../api/endpoints';
import { adaptPayslip, type BackendPayslip, type FrontendPayslip } from '../../utils/adapters';
import { formatCurrency } from '../../utils/helpers';

interface PayslipDetailModalProps {
  payslipId: number | null;
  open: boolean;
  onClose: () => void;
}

export default function PayslipDetailModal({ payslipId, open, onClose }: PayslipDetailModalProps) {
  const [payslip, setPayslip] = useState<FrontendPayslip | null>(null);
  const [employeeName, setEmployeeName] = useState('');
  const [loading, setLoading] = useState(false);
  const [downloading, setDownloading] = useState(false);
  const [finalizing, setFinalizing] = useState(false);

  useEffect(() => {
    if (!payslipId || !open) return;
    setLoading(true);
    payrollApi.get(payslipId)
      .then(({ data }) => {
        const adapted = adaptPayslip(data as BackendPayslip);
        setPayslip(adapted);
        if (data.employeeId) {
          employeeApi.get(data.employeeId).then(({ data: emp }) => {
            setEmployeeName(`${emp.firstName} ${emp.lastName}`);
          }).catch(() => {});
        }
      })
      .catch(() => message.error('Failed to load payslip'))
      .finally(() => setLoading(false));
  }, [payslipId, open]);

  const handleFinalize = async () => {
    if (!payslipId) return;
    setFinalizing(true);
    try {
      await payrollApi.finalize(payslipId);
      message.success('Payslip finalized');
      const { data } = await payrollApi.get(payslipId);
      setPayslip(adaptPayslip(data as BackendPayslip));
    } catch {
      message.error('Failed to finalize payslip');
    } finally {
      setFinalizing(false);
    }
  };

  const handleDownload = async () => {
    if (!payslipId) return;
    setDownloading(true);
    try {
      const response = await payrollApi.download(payslipId);
      const url = window.URL.createObjectURL(new Blob([response.data]));
      const link = document.createElement('a');
      link.href = url;
      link.setAttribute('download', `payslip-${payslipId}.pdf`);
      document.body.appendChild(link);
      link.click();
      link.remove();
      window.URL.revokeObjectURL(url);
    } catch {
      message.error('Failed to download payslip');
    } finally {
      setDownloading(false);
    }
  };

  const earningColumns = [
    { title: 'Earning', dataIndex: 'name', key: 'name' },
    { title: 'Amount', dataIndex: 'amount', key: 'amount', render: (v: number) => formatCurrency(v) },
  ];

  const deductionColumns = [
    { title: 'Deduction', dataIndex: 'name', key: 'name' },
    { title: 'Amount', dataIndex: 'amount', key: 'amount', render: (v: number) => formatCurrency(v) },
  ];

  return (
    <Modal
      title="Payslip Detail"
      open={open}
      onCancel={onClose}
      footer={
        <Space>
          {payslip?.status === 'draft' && (
            <Button type="primary" loading={finalizing} onClick={handleFinalize}>
              Finalize
            </Button>
          )}
          <Button icon={<DownloadOutlined />} loading={downloading} onClick={handleDownload}>
            Download PDF
          </Button>
        </Space>
      }
      width={700}
    >
      {loading ? (
        <div style={{ textAlign: 'center', padding: 40 }}><Spin /></div>
      ) : payslip ? (
        <div>
          <Descriptions column={2} bordered size="small">
            <Descriptions.Item label="Employee">{employeeName}</Descriptions.Item>
            <Descriptions.Item label="Period">{payslip.period}</Descriptions.Item>
            <Descriptions.Item label="Gross Pay">{formatCurrency(payslip.grossPay)}</Descriptions.Item>
            <Descriptions.Item label="Status">{payslip.status}</Descriptions.Item>
          </Descriptions>
          <Divider />
          <Typography.Title level={5}>Earnings</Typography.Title>
          <Table dataSource={payslip.earnings} columns={earningColumns} pagination={false} size="small" rowKey="name" />
          <Divider />
          <Typography.Title level={5}>Deductions</Typography.Title>
          <Table dataSource={payslip.deductions} columns={deductionColumns} pagination={false} size="small" rowKey="name" />
          <Divider />
          <Space style={{ width: '100%', justifyContent: 'flex-end' }}>
            <Typography.Text strong style={{ fontSize: 18 }}>
              Net Pay: <Typography.Text type="success">{formatCurrency(payslip.netPay)}</Typography.Text>
            </Typography.Text>
          </Space>
        </div>
      ) : (
        <Typography.Text type="secondary">No payslip data</Typography.Text>
      )}
    </Modal>
  );
}
