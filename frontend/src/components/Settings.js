import React, { useState, useEffect } from 'react';
import { Form, Input, Button, Switch, InputNumber, TimePicker, Card, Table, Space, Modal, Typography, message } from 'antd';
import { PlusOutlined, DeleteOutlined, EditOutlined } from '@ant-design/icons';
import moment from 'moment';

const { Title } = Typography;

const Settings = ({ config, updateConfig }) => {
  const [form] = Form.useForm();
  const [sources, setSources] = useState([]);
  const [editModalVisible, setEditModalVisible] = useState(false);
  const [editForm] = Form.useForm();
  const [editingIndex, setEditingIndex] = useState(null);

  // 初始化表单数据
  useEffect(() => {
    if (config) {
      // 设置基本配置
      form.setFieldsValue({
        interval_seconds: config.interval_seconds,
        daily_limit_gb: config.daily_limit_gb,
        speed_limit_kbps: config.speed_limit_kbps,
        active_hours_enabled: config.active_hours?.enabled,
        active_hours_start: config.active_hours?.start_time ? moment(config.active_hours.start_time, 'HH:mm') : null,
        active_hours_end: config.active_hours?.end_time ? moment(config.active_hours.end_time, 'HH:mm') : null,
        enabled: config.enabled
      });

      // 设置下载源
      if (config.download_sources) {
        setSources(config.download_sources);
      }
    }
  }, [config, form]);

  // 提交表单
  const onFinish = (values) => {
    // 构建新的配置对象
    const newConfig = {
      ...config,
      interval_seconds: values.interval_seconds,
      daily_limit_gb: values.daily_limit_gb,
      speed_limit_kbps: values.speed_limit_kbps,
      active_hours: {
        enabled: values.active_hours_enabled,
        start_time: values.active_hours_start ? values.active_hours_start.format('HH:mm') : '00:00',
        end_time: values.active_hours_end ? values.active_hours_end.format('HH:mm') : '23:59'
      },
      enabled: values.enabled,
      download_sources: sources
    };

    // 更新配置
    updateConfig(newConfig);
  };

  // 添加下载源
  const addSource = () => {
    setEditingIndex(null);
    editForm.resetFields();
    setEditModalVisible(true);
  };

  // 编辑下载源
  const editSource = (index) => {
    const source = sources[index];
    setEditingIndex(index);
    editForm.setFieldsValue({
      name: source.name,
      url: source.url,
      enabled: source.enabled
    });
    setEditModalVisible(true);
  };

  // 删除下载源
  const deleteSource = (index) => {
    Modal.confirm({
      title: '确认删除',
      content: '确定要删除这个下载源吗？',
      onOk: () => {
        const newSources = [...sources];
        newSources.splice(index, 1);
        setSources(newSources);
        message.success('下载源已删除');
      }
    });
  };

  // 保存下载源
  const saveSource = () => {
    editForm.validateFields().then(values => {
      const newSources = [...sources];
      const sourceData = {
        name: values.name,
        url: values.url,
        enabled: values.enabled
      };

      if (editingIndex !== null) {
        // 更新现有源
        newSources[editingIndex] = sourceData;
      } else {
        // 添加新源
        newSources.push(sourceData);
      }

      setSources(newSources);
      setEditModalVisible(false);
      message.success(editingIndex !== null ? '下载源已更新' : '下载源已添加');
    });
  };

  // 下载源表格列定义
  const columns = [
    {
      title: '名称',
      dataIndex: 'name',
      key: 'name',
    },
    {
      title: 'URL',
      dataIndex: 'url',
      key: 'url',
      ellipsis: true,
    },
    {
      title: '状态',
      dataIndex: 'enabled',
      key: 'enabled',
      render: (enabled) => (
        <Switch checked={enabled} disabled />
      ),
    },
    {
      title: '操作',
      key: 'action',
      render: (_, record, index) => (
        <Space size="middle">
          <Button 
            type="text" 
            icon={<EditOutlined />} 
            onClick={() => editSource(index)}
          />
          <Button 
            type="text" 
            danger 
            icon={<DeleteOutlined />} 
            onClick={() => deleteSource(index)}
          />
        </Space>
      ),
    },
  ];

  return (
    <div>
      <Title level={3}>设置</Title>
      
      {/* 基本设置表单 */}
      <Card title="基本设置" className="settings-form">
        <Form
          form={form}
          layout="vertical"
          onFinish={onFinish}
          initialValues={{
            interval_seconds: 60,
            daily_limit_gb: 0,
            speed_limit_kbps: 0,
            active_hours_enabled: false,
            enabled: true
          }}
        >
          <Form.Item
            name="interval_seconds"
            label="下载间隔（秒）"
            rules={[{ required: true, message: '请输入下载间隔时间' }]}
          >
            <InputNumber min={0} style={{ width: '100%' }} />
          </Form.Item>

          <Form.Item
            name="daily_limit_gb"
            label="每日流量限制（GB，0表示无限制）"
            rules={[{ required: true, message: '请输入每日流量限制' }]}
          >
            <InputNumber min={0} style={{ width: '100%' }} />
          </Form.Item>

          <Form.Item
            name="speed_limit_kbps"
            label="下载速度限制（KB/s，0表示无限制）"
            rules={[{ required: true, message: '请输入下载速度限制' }]}
          >
            <InputNumber min={0} style={{ width: '100%' }} />
          </Form.Item>

          <Form.Item
            name="active_hours_enabled"
            label="启用活跃时间段"
            valuePropName="checked"
          >
            <Switch />
          </Form.Item>

          <Form.Item
            name="active_hours_start"
            label="活跃开始时间"
            dependencies={['active_hours_enabled']}
          >
            <TimePicker format="HH:mm" style={{ width: '100%' }} disabled={!form.getFieldValue('active_hours_enabled')} />
          </Form.Item>

          <Form.Item
            name="active_hours_end"
            label="活跃结束时间"
            dependencies={['active_hours_enabled']}
          >
            <TimePicker format="HH:mm" style={{ width: '100%' }} disabled={!form.getFieldValue('active_hours_enabled')} />
          </Form.Item>

          <Form.Item
            name="enabled"
            label="启用下载"
            valuePropName="checked"
          >
            <Switch />
          </Form.Item>

          <Form.Item>
            <Button type="primary" htmlType="submit">
              保存设置
            </Button>
          </Form.Item>
        </Form>
      </Card>

      {/* 下载源管理 */}
      <Card 
        title="下载源管理" 
        className="settings-form" 
        style={{ marginTop: '24px' }}
        extra={
          <Button type="primary" icon={<PlusOutlined />} onClick={addSource}>
            添加下载源
          </Button>
        }
      >
        <Table 
          columns={columns} 
          dataSource={sources.map((source, index) => ({ ...source, key: index }))} 
          pagination={false}
        />
      </Card>

      {/* 编辑下载源对话框 */}
      <Modal
        title={editingIndex !== null ? '编辑下载源' : '添加下载源'}
        visible={editModalVisible}
        onOk={saveSource}
        onCancel={() => setEditModalVisible(false)}
      >
        <Form
          form={editForm}
          layout="vertical"
        >
          <Form.Item
            name="name"
            label="名称"
            rules={[{ required: true, message: '请输入下载源名称' }]}
          >
            <Input />
          </Form.Item>

          <Form.Item
            name="url"
            label="URL"
            rules={[{ required: true, message: '请输入下载源URL' }]}
          >
            <Input />
          </Form.Item>

          <Form.Item
            name="enabled"
            label="启用"
            valuePropName="checked"
            initialValue={true}
          >
            <Switch />
          </Form.Item>
        </Form>
      </Modal>
    </div>
  );
};

export default Settings;