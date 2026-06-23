import { useState } from 'react';
import { useNavigate, useLocation } from 'react-router-dom';
import { Form, Input, Button, Card, Typography, message, Space } from 'antd';
import { UserOutlined, LockOutlined } from '@ant-design/icons';
import { useAuth } from '../../contexts/AuthContext';

export default function LoginPage() {
  const [loading, setLoading] = useState(false);
  const { login } = useAuth();
  const navigate = useNavigate();
  const location = useLocation();
  const from = (location.state as { from?: { pathname: string } })?.from?.pathname || '/dashboard';

  const onFinish = async (values: { email: string; password: string }) => {
    setLoading(true);
    try {
      await login(values.email, values.password);
      message.success('Login successful');
      navigate(from, { replace: true });
    } catch {
      message.error('Invalid credentials');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div style={{ minHeight: '100vh', display: 'flex', justifyContent: 'center', alignItems: 'center', background: '#f0f2f5' }}>
      <Card style={{ width: 400, boxShadow: '0 2px 8px rgba(0,0,0,0.1)' }}>
        <Space direction="vertical" size="large" style={{ width: '100%' }}>
          <Typography.Title level={2} style={{ textAlign: 'center', margin: 0 }}>
            Payroll System
          </Typography.Title>
          <Typography.Text type="secondary" style={{ display: 'block', textAlign: 'center' }}>
            Sign in to your account
          </Typography.Text>
          <Form name="login" onFinish={onFinish} layout="vertical" size="large">
            <Form.Item name="email" rules={[{ required: true, type: 'email', message: 'Please enter a valid email' }]}>
              <Input prefix={<UserOutlined />} placeholder="Email" />
            </Form.Item>
            <Form.Item name="password" rules={[{ required: true, message: 'Please enter your password' }]}>
              <Input.Password prefix={<LockOutlined />} placeholder="Password" />
            </Form.Item>
            <Form.Item>
              <Button type="primary" htmlType="submit" loading={loading} block>
                Sign In
              </Button>
            </Form.Item>
          </Form>
        </Space>
      </Card>
    </div>
  );
}
