import { useState, useEffect } from 'react';
import { Card, Table, Button, Select, InputNumber, Drawer, Form, message, Typography, Space, Spin, Input } from 'antd';
import { PlusOutlined } from '@ant-design/icons';
import { employeeApi, salaryApi } from '../../api/endpoints';
import { COMPONENT_TYPES } from '../../utils/constants';
import { formatCurrency } from '../../utils/helpers';
import dayjs from 'dayjs';

interface SalaryComponent {
  id: number;
  componentType: string;
  amount: number;
  effectiveFrom: string;
  effectiveTo: string | null;
}

export default function SalaryPage() {
  const [employees, setEmployees] = useState<{ id: number; employeeCode: string; firstName: string; lastName: string; department: string }[]>([]);
  const [selectedEmployee, setSelectedEmployee] = useState<number | null>(null);
  const [components, setComponents] = useState<SalaryComponent[]>([]);
  const [totalMonthly, setTotalMonthly] = useState(0);
  const [loading, setLoading] = useState(false);
  const [drawerOpen, setDrawerOpen] = useState(false);
  const [saving, setSaving] = useState(false);
  const [form] = Form.useForm();

  useEffect(() => {
    employeeApi.list({ page_size: 100 }).then(({ data }) => {
      const items = data.items || [];
      setEmployees(items.map((e: { id: number; employeeCode: string; firstName: string; lastName: string; department: string }) => ({
        id: e.id,
        employeeCode: e.employeeCode,
        firstName: e.firstName,
        lastName: e.lastName,
        department: e.department,
      })));
    }).catch(() => {});
  }, []);

  const fetchComponents = async (employeeId: number) => {
    setLoading(true);
    try {
      const { data } = await salaryApi.get(employeeId);
      setComponents(data.components || []);
      setTotalMonthly(data.totalMonthly || 0);
    } catch {
      setComponents([]);
      setTotalMonthly(0);
    } finally {
      setLoading(false);
    }
  };

  const handleEmployeeChange = (value: number) => {
    setSelectedEmployee(value);
    fetchComponents(value);
  };

  const handleAdd = () => {
    form.resetFields();
    form.setFieldsValue({ effectiveFrom: dayjs().format('YYYY-MM-DD') });
    setDrawerOpen(true);
  };

  const handleSave = async () => {
    const values = await form.validateFields();
    setSaving(true);
    try {
      if (selectedEmployee) {
        await salaryApi.create(selectedEmployee, {
          component_type: values.componentType,
          amount: values.amount,
          effective_from: values.effectiveFrom || dayjs().format('YYYY-MM-DD'),
          effective_to: values.effectiveTo || null,
        });
        message.success('Component added');
        setDrawerOpen(false);
        fetchComponents(selectedEmployee);
      }
    } catch {
      message.error('Failed to save');
    } finally {
      setSaving(false);
    }
  };

  const columns = [
    {
      title: 'Component', dataIndex: 'componentType', key: 'componentType',
      render: (v: string) => {
        const ct = COMPONENT_TYPES.find(c => c.value === v);
        return ct?.label || v;
      },
    },
    { title: 'Amount', dataIndex: 'amount', key: 'amount', render: (v: number) => formatCurrency(v) },
    { title: 'Effective From', dataIndex: 'effectiveFrom', key: 'effectiveFrom' },
    { title: 'Effective To', dataIndex: 'effectiveTo', key: 'effectiveTo', render: (v: string | null) => v || 'Current' },
  ];

  return (
    <div>
      <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 16 }}>
        <Typography.Title level={4} style={{ margin: 0 }}>Salary Configuration</Typography.Title>
        {selectedEmployee && (
          <Button type="primary" icon={<PlusOutlined />} onClick={handleAdd}>Add Component</Button>
        )}
      </div>
      <Card>
        <Space direction="vertical" style={{ width: '100%' }}>
          <Typography.Text strong>Select Employee</Typography.Text>
          <Select
            showSearch
            placeholder="Search employee..."
            style={{ width: 300 }}
            value={selectedEmployee}
            onChange={handleEmployeeChange}
            optionFilterProp="label"
            options={employees.map(e => ({ value: e.id, label: `${e.firstName} ${e.lastName} (${e.employeeCode}) - ${e.department}` }))}
          />
          {loading ? (
            <div style={{ textAlign: 'center', padding: 40 }}><Spin /></div>
          ) : selectedEmployee ? (
            <Table
              dataSource={components}
              columns={columns}
              rowKey="id"
              pagination={false}
              summary={() => (
                <Table.Summary.Row>
                  <Table.Summary.Cell index={0}><Typography.Text strong>Total Monthly</Typography.Text></Table.Summary.Cell>
                  <Table.Summary.Cell index={1}><Typography.Text strong>{formatCurrency(totalMonthly)}</Typography.Text></Table.Summary.Cell>
                  <Table.Summary.Cell index={2} />
                  <Table.Summary.Cell index={3} />
                </Table.Summary.Row>
              )}
            />
          ) : (
            <Typography.Text type="secondary" style={{ padding: 40, display: 'block', textAlign: 'center' }}>
              Select an employee to view salary components
            </Typography.Text>
          )}
        </Space>
      </Card>
      <Drawer
        title="Add Salary Component"
        open={drawerOpen}
        onClose={() => setDrawerOpen(false)}
        width={400}
        extra={<Button type="primary" onClick={handleSave} loading={saving}>Save</Button>}
      >
        <Form form={form} layout="vertical">
          <Form.Item name="componentType" label="Component Type" rules={[{ required: true }]}>
            <Select options={COMPONENT_TYPES.map(c => ({ value: c.value, label: c.label }))} />
          </Form.Item>
          <Form.Item name="amount" label="Amount" rules={[{ required: true }]}>
            <InputNumber style={{ width: '100%' }} prefix="₹" min={0} />
          </Form.Item>
          <Form.Item name="effectiveFrom" label="Effective From">
            <Input placeholder="YYYY-MM-DD" />
          </Form.Item>
          <Form.Item name="effectiveTo" label="Effective To">
            <Input placeholder="YYYY-MM-DD (leave blank if current)" />
          </Form.Item>
        </Form>
      </Drawer>
    </div>
  );
}
