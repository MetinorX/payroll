import { useState } from 'react';
import { Outlet, useNavigate, useLocation } from 'react-router-dom';
import { Layout, Menu, Button, Dropdown, Avatar, Typography, theme } from 'antd';
import {
  DashboardOutlined, TeamOutlined, CalendarOutlined,
  PayCircleOutlined, BarChartOutlined, FileTextOutlined,
  MenuFoldOutlined, MenuUnfoldOutlined,
  UserOutlined, LogoutOutlined, SettingOutlined,
} from '@ant-design/icons';
import { useAuth } from '../../contexts/AuthContext';
import { MENU_ITEMS, ROLE_LABELS } from '../../utils/constants';

const { Header, Sider, Content } = Layout;

const iconMap: Record<string, React.ReactNode> = {
  dashboard: <DashboardOutlined />,
  employees: <TeamOutlined />,
  attendance: <CalendarOutlined />,
  salary: <span style={{ fontWeight: 700 }}>₹</span>,
  payroll: <PayCircleOutlined />,
  payslips: <FileTextOutlined />,
  reports: <BarChartOutlined />,
};

export default function AppLayout() {
  const [collapsed, setCollapsed] = useState(false);
  const { user, logout, hasRole } = useAuth();
  const navigate = useNavigate();
  const location = useLocation();
  const { token: { colorBgContainer, borderRadiusLG } } = theme.useToken();

  const filteredMenuItems = MENU_ITEMS.main
    .filter((item) => hasRole(...item.roles))
    .map((item) => ({
      key: item.path,
      icon: iconMap[item.key],
      label: item.label,
    }));

  const handleLogout = () => {
    logout();
    navigate('/login');
  };

  const userMenu = {
    items: [
      { key: 'profile', icon: <SettingOutlined />, label: 'Profile' },
      { type: 'divider' as const },
      { key: 'logout', icon: <LogoutOutlined />, label: 'Logout', danger: true },
    ],
    onClick: ({ key }: { key: string }) => {
      if (key === 'logout') handleLogout();
    },
  };

  return (
    <Layout style={{ minHeight: '100vh' }}>
      <Sider trigger={null} collapsible collapsed={collapsed} breakpoint="lg" onBreakpoint={(broken) => setCollapsed(broken)}>
        <div style={{ height: 64, display: 'flex', alignItems: 'center', justifyContent: 'center', color: '#fff', fontWeight: 700, fontSize: collapsed ? 16 : 20 }}>
          {collapsed ? '💵' : 'Payroll System'}
        </div>
        <Menu
          theme="dark"
          mode="inline"
          selectedKeys={[location.pathname]}
          items={filteredMenuItems}
          onClick={({ key }) => navigate(key)}
        />
      </Sider>
      <Layout>
        <Header style={{ padding: '0 24px', background: colorBgContainer, display: 'flex', alignItems: 'center', justifyContent: 'space-between', boxShadow: '0 1px 4px rgba(0,0,0,0.08)' }}>
          <Button
            type="text"
            icon={collapsed ? <MenuUnfoldOutlined /> : <MenuFoldOutlined />}
            onClick={() => setCollapsed(!collapsed)}
          />
          <Dropdown menu={userMenu} placement="bottomRight">
            <div style={{ cursor: 'pointer', display: 'flex', alignItems: 'center', gap: 8 }}>
              <Avatar icon={<UserOutlined />} style={{ backgroundColor: '#1890ff' }} />
              <div style={{ lineHeight: 1.2 }}>
                <Typography.Text strong style={{ display: 'block' }}>{user?.email}</Typography.Text>
                <Typography.Text type="secondary" style={{ fontSize: 12 }}>{user && ROLE_LABELS[user.role]}</Typography.Text>
              </div>
            </div>
          </Dropdown>
        </Header>
        <Content style={{ margin: 24 }}>
          <div style={{ padding: 24, minHeight: 360, background: colorBgContainer, borderRadius: borderRadiusLG }}>
            <Outlet />
          </div>
        </Content>
      </Layout>
    </Layout>
  );
}
