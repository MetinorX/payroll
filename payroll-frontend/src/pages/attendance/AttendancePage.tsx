import { useState, useEffect, useCallback, useMemo } from 'react';
import { Button, Table, Tag, Space, DatePicker, message, Typography, Select, Input } from 'antd';
import { ClockCircleOutlined, CheckCircleOutlined } from '@ant-design/icons';
import { attendanceApi, employeeApi } from '../../api/endpoints';
import { adaptAttendanceList, type BackendAttendance, type FrontendAttendance } from '../../utils/adapters';
import { useAuth } from '../../contexts/AuthContext';
import dayjs from 'dayjs';

const { RangePicker } = DatePicker;

const statusColors: Record<string, string> = {
  present: 'green', absent: 'red', half_day: 'gold', leave: 'blue',
};

export default function AttendancePage() {
  const { user } = useAuth();
  const [records, setRecords] = useState<FrontendAttendance[]>([]);
  const [loading, setLoading] = useState(false);
  const [dateRange, setDateRange] = useState<[dayjs.Dayjs | null, dayjs.Dayjs | null]>([null, null]);
  const [employeeId, setEmployeeId] = useState<number | undefined>(user?.role === 'employee' ? user.employeeId : undefined);
  const [clockInTime, setClockInTime] = useState(dayjs().format('HH:mm:ss'));
  const [clockOutTime, setClockOutTime] = useState(dayjs().format('HH:mm:ss'));
  const [employees, setEmployees] = useState<{ id: number; firstName: string; lastName: string; employeeCode: string }[]>([]);

  useEffect(() => {
    if (user?.role === 'admin' || user?.role === 'hr') {
      employeeApi.list({ page_size: 100 }).then(({ data }) => {
        setEmployees((data.items || []).map((e: { id: number; firstName: string; lastName: string; employeeCode: string }) => ({
          id: e.id,
          firstName: e.firstName,
          lastName: e.lastName,
          employeeCode: e.employeeCode,
        })));
      }).catch(() => {});
    }
  }, [user]);

  const employeeNameMap = useMemo(
    () => Object.fromEntries(employees.map(e => [e.id, `${e.firstName} ${e.lastName}`])),
    [employees]
  );

  const fetchAttendance = useCallback(async () => {
    setLoading(true);
    try {
      const params: Record<string, unknown> = {};
      if (dateRange[0]) params.date_from = dateRange[0].format('YYYY-MM-DD');
      if (dateRange[1]) params.date_to = dateRange[1].format('YYYY-MM-DD');
      if (employeeId) params.employee_id = employeeId;
      const { data } = await attendanceApi.list(params);
      const items: BackendAttendance[] = data.items || [];
      setRecords(adaptAttendanceList(items));
    } catch {
      message.error('Failed to load attendance');
    } finally {
      setLoading(false);
    }
  }, [dateRange, employeeId]);

  useEffect(() => { fetchAttendance(); }, [fetchAttendance]);

  const handleClockIn = async () => {
    try {
      await attendanceApi.clockIn({
        employee_id: user?.employeeId || user?.id || 0,
        date: dayjs().format('YYYY-MM-DD'),
        clock_in_time: clockInTime,
      });
      message.success('Clocked in');
      fetchAttendance();
    } catch {
      message.error('Failed to clock in');
    }
  };

  const handleClockOut = async () => {
    try {
      await attendanceApi.clockOut({
        employee_id: user?.employeeId || user?.id || 0,
        date: dayjs().format('YYYY-MM-DD'),
        clock_out_time: clockOutTime,
      });
      message.success('Clocked out');
      fetchAttendance();
    } catch {
      message.error('Failed to clock out');
    }
  };

  const columns = [
    { title: 'Date', dataIndex: 'date', key: 'date', render: (v: string) => v ? dayjs(v).format('MMM DD, YYYY') : '-' },
    {
      title: 'Employee', dataIndex: 'employeeId', key: 'employeeName',
      render: (v: number) => employeeNameMap[v] || `#${v}`,
    },
    { title: 'Clock In', dataIndex: 'clockIn', key: 'clockIn', render: (v: string | null) => v || '-' },
    { title: 'Clock Out', dataIndex: 'clockOut', key: 'clockOut', render: (v: string | null) => v || '-' },
    {
      title: 'Status', dataIndex: 'status', key: 'status',
      render: (v: string) => <Tag color={statusColors[v] || 'default'}>{v || 'pending'}</Tag>,
    },
    { title: 'Notes', dataIndex: 'note', key: 'note', ellipsis: true },
  ];

  return (
    <div>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 16, flexWrap: 'wrap', gap: 8 }}>
        <Typography.Title level={4} style={{ margin: 0 }}>Attendance</Typography.Title>
        <Space wrap>
          {user?.role !== 'admin' && user?.role !== 'hr' && (
            <>
              <Input type="time" value={clockInTime} onChange={e => setClockInTime(e.target.value)} style={{ width: 120 }} />
              <Button type="primary" icon={<ClockCircleOutlined />} onClick={handleClockIn}>Clock In</Button>
              <Input type="time" value={clockOutTime} onChange={e => setClockOutTime(e.target.value)} style={{ width: 120 }} />
              <Button icon={<CheckCircleOutlined />} onClick={handleClockOut}>Clock Out</Button>
            </>
          )}
          {user?.role === 'admin' || user?.role === 'hr' ? (
            <Select
              placeholder="All Employees"
              allowClear
              style={{ width: 200 }}
              value={employeeId}
              onChange={setEmployeeId}
              options={employees.map(e => ({ value: e.id, label: `${e.firstName} ${e.lastName} (${e.employeeCode})` }))}
            />
          ) : null}
          <RangePicker value={dateRange as [dayjs.Dayjs, dayjs.Dayjs]} onChange={(dates) => setDateRange(dates ? [dates[0], dates[1]] : [null, null])} />
        </Space>
      </div>
      <Table
        dataSource={records}
        columns={columns}
        rowKey="id"
        loading={loading}
        pagination={{ pageSize: 15 }}
      />
    </div>
  );
}
