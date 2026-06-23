import { useState, useEffect, useCallback } from 'react';
import { Table, Button, Input, Space, Drawer, Form, Select, DatePicker, Popconfirm, message, Typography } from 'antd';
import { PlusOutlined, EditOutlined, DeleteOutlined, SearchOutlined } from '@ant-design/icons';
import { employeeApi } from '../../api/endpoints';
import { adaptEmployeeList, type FrontendEmployee } from '../../utils/adapters';
import { formatCurrency } from '../../utils/helpers';
import { useAuth } from '../../contexts/AuthContext';
import dayjs from 'dayjs';

export default function EmployeesPage() {
  const { user } = useAuth();
  const [employees, setEmployees] = useState<FrontendEmployee[]>([]);
  const [total, setTotal] = useState(0);
  const [loading, setLoading] = useState(false);
  const [page, setPage] = useState(1);
  const [search, setSearch] = useState('');
  const [drawerOpen, setDrawerOpen] = useState(false);
  const [editingEmployee, setEditingEmployee] = useState<FrontendEmployee | null>(null);
  const [saving, setSaving] = useState(false);
  const [form] = Form.useForm();

  const fetchEmployees = useCallback(async () => {
    setLoading(true);
    try {
      const { data } = await employeeApi.list({ page, page_size: 10, search });
      setEmployees(adaptEmployeeList(data.items || []));
      setTotal(data.total || 0);
    } catch {
      message.error('Failed to load employees');
    } finally {
      setLoading(false);
    }
  }, [page, search]);

  useEffect(() => { fetchEmployees(); }, [fetchEmployees]);

  const openDrawer = (employee?: FrontendEmployee) => {
    setEditingEmployee(employee || null);
    if (employee) {
      form.setFieldsValue({
        ...employee,
        hireDate: employee.hireDate ? dayjs(employee.hireDate) : undefined,
      });
    } else {
      form.resetFields();
    }
    setDrawerOpen(true);
  };

  const handleSave = async () => {
    const values = await form.validateFields();
    setSaving(true);
    try {
      const payload: Record<string, unknown> = {
        first_name: values.firstName,
        last_name: values.lastName,
        email: values.email,
        department: values.department,
        designation: values.position,
        basic_salary: Number(values.salary),
        date_of_joining: values.hireDate ? (values.hireDate as dayjs.Dayjs).format('YYYY-MM-DD') : undefined,
        employee_code: values.employeeCode,
      };
      if (!editingEmployee) {
        payload.password = values.password;
      }
      if (editingEmployee) {
        await employeeApi.update(editingEmployee.id, payload);
        message.success('Employee updated');
      } else {
        await employeeApi.create(payload);
        message.success('Employee created');
      }
      setDrawerOpen(false);
      fetchEmployees();
    } catch {
      message.error('Failed to save employee');
    } finally {
      setSaving(false);
    }
  };

  const handleDelete = async (id: number) => {
    try {
      await employeeApi.delete(id);
      message.success('Employee deleted');
      fetchEmployees();
    } catch {
      message.error('Failed to delete employee');
    }
  };

  const columns = [
    { title: 'Code', dataIndex: 'employeeCode', key: 'employeeCode' },
    { title: 'Name', dataIndex: 'fullName', key: 'fullName', sorter: true },
    { title: 'Email', dataIndex: 'email', key: 'email' },
    { title: 'Department', dataIndex: 'department', key: 'department', sorter: true },
    { title: 'Position', dataIndex: 'position', key: 'position' },
    {
      title: 'Salary', dataIndex: 'salary', key: 'salary', sorter: true,
      render: (v: number) => formatCurrency(v),
    },
    { title: 'Status', dataIndex: 'status', key: 'status' },
    {
      title: 'Actions', key: 'actions',
      render: (_: unknown, record: FrontendEmployee) => (
        <Space>
          <Button type="link" icon={<EditOutlined />} onClick={() => openDrawer(record)}>Edit</Button>
          {user?.role === 'admin' && (
            <Popconfirm title="Delete this employee?" onConfirm={() => handleDelete(record.id)} okText="Yes" cancelText="No">
              <Button type="link" danger icon={<DeleteOutlined />}>Delete</Button>
            </Popconfirm>
          )}
        </Space>
      ),
    },
  ];

  return (
    <div>
      <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 16 }}>
        <Typography.Title level={4} style={{ margin: 0 }}>Employee Management</Typography.Title>
        <Space>
          <Input placeholder="Search..." prefix={<SearchOutlined />} value={search} onChange={(e) => { setSearch(e.target.value); setPage(1); }} style={{ width: 250 }} allowClear />
          <Button type="primary" icon={<PlusOutlined />} onClick={() => openDrawer()}>Add Employee</Button>
        </Space>
      </div>
      <Table
        dataSource={employees}
        columns={columns}
        rowKey="id"
        loading={loading}
        pagination={{ current: page, total, pageSize: 10, onChange: setPage }}
      />
      <Drawer
        title={editingEmployee ? 'Edit Employee' : 'Add Employee'}
        open={drawerOpen}
        onClose={() => setDrawerOpen(false)}
        width={480}
        extra={<Button type="primary" onClick={handleSave} loading={saving}>Save</Button>}
      >
        <Form form={form} layout="vertical">
          <Form.Item name="employeeCode" label="Employee Code" rules={[{ required: true }]}>
            <Input />
          </Form.Item>
          <Form.Item name="firstName" label="First Name" rules={[{ required: true }]}>
            <Input />
          </Form.Item>
          <Form.Item name="lastName" label="Last Name" rules={[{ required: true }]}>
            <Input />
          </Form.Item>
          <Form.Item name="email" label="Email" rules={[{ required: true, type: 'email' }]}>
            <Input />
          </Form.Item>
          <Form.Item name="department" label="Department" rules={[{ required: true }]}>
            <Select options={[
              { value: 'Engineering', label: 'Engineering' },
              { value: 'Marketing', label: 'Marketing' },
              { value: 'Sales', label: 'Sales' },
              { value: 'HR', label: 'HR' },
              { value: 'Finance', label: 'Finance' },
              { value: 'Operations', label: 'Operations' },
            ]} />
          </Form.Item>
          <Form.Item name="position" label="Position" rules={[{ required: true }]}>
            <Input />
          </Form.Item>
          <Form.Item name="salary" label="Basic Salary" rules={[{ required: true }]}>
            <Input type="number" prefix="₹" />
          </Form.Item>
          <Form.Item name="hireDate" label="Date of Joining">
            <DatePicker style={{ width: '100%' }} />
          </Form.Item>
          {!editingEmployee && (
            <Form.Item name="password" label="Password" rules={[{ required: !editingEmployee, min: 6 }]}>
              <Input.Password />
            </Form.Item>
          )}
        </Form>
      </Drawer>
    </div>
  );
}
