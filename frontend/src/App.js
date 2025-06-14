import React, { useState, useEffect } from 'react';
import { Layout, Menu, Typography, Spin, message } from 'antd';
import {
  DashboardOutlined,
  SettingOutlined,
  HistoryOutlined,
  GithubOutlined
} from '@ant-design/icons';
import './App.css';
import Dashboard from './components/Dashboard';
import Settings from './components/Settings';
import History from './components/History';
import axios from 'axios';

const { Header, Content, Footer, Sider } = Layout;
const { Title } = Typography;

function App() {
  const [collapsed, setCollapsed] = useState(false);
  const [currentPage, setCurrentPage] = useState('dashboard');
  const [loading, setLoading] = useState(true);
  const [config, setConfig] = useState(null);
  const [stats, setStats] = useState(null);

  // 加载配置和统计信息
  useEffect(() => {
    const fetchData = async () => {
      try {
        const [configRes, statsRes] = await Promise.all([
          axios.get('/api/config'),
          axios.get('/api/stats')
        ]);
        setConfig(configRes.data);
        setStats(statsRes.data);
        setLoading(false);
      } catch (error) {
        console.error('加载数据失败:', error);
        message.error('加载数据失败，请刷新页面重试');
        setLoading(false);
      }
    };

    fetchData();

    // 定时刷新统计信息
    const statsInterval = setInterval(async () => {
      try {
        const statsRes = await axios.get('/api/stats');
        setStats(statsRes.data);
      } catch (error) {
        console.error('刷新统计信息失败:', error);
      }
    }, 5000); // 每5秒刷新一次

    return () => clearInterval(statsInterval);
  }, []);

  // 更新配置
  const updateConfig = async (newConfig) => {
    try {
      setLoading(true);
      await axios.post('/api/config', newConfig);
      setConfig(newConfig);
      message.success('配置已更新');
      setLoading(false);
    } catch (error) {
      console.error('更新配置失败:', error);
      message.error('更新配置失败');
      setLoading(false);
    }
  };

  // 启动下载
  const startDownload = async () => {
    try {
      await axios.post('/api/control/start');
      const configRes = await axios.get('/api/config');
      setConfig(configRes.data);
      message.success('下载已启动');
    } catch (error) {
      console.error('启动下载失败:', error);
      message.error('启动下载失败');
    }
  };

  // 停止下载
  const stopDownload = async () => {
    try {
      await axios.post('/api/control/stop');
      const configRes = await axios.get('/api/config');
      setConfig(configRes.data);
      message.success('下载已停止');
    } catch (error) {
      console.error('停止下载失败:', error);
      message.error('停止下载失败');
    }
  };

  // 重置统计信息
  const resetStats = async () => {
    try {
      await axios.post('/api/reset-stats');
      const statsRes = await axios.get('/api/stats');
      setStats(statsRes.data);
      message.success('统计信息已重置');
    } catch (error) {
      console.error('重置统计信息失败:', error);
      message.error('重置统计信息失败');
    }
  };

  // 渲染当前页面内容
  const renderContent = () => {
    if (loading) {
      return (
        <div className="loading-container">
          <Spin size="large" />
          <p>加载中...</p>
        </div>
      );
    }

    switch (currentPage) {
      case 'dashboard':
        return <Dashboard stats={stats} config={config} startDownload={startDownload} stopDownload={stopDownload} />;
      case 'settings':
        return <Settings config={config} updateConfig={updateConfig} />;
      case 'history':
        return <History stats={stats} resetStats={resetStats} />;
      default:
        return <Dashboard stats={stats} config={config} startDownload={startDownload} stopDownload={stopDownload} />;
    }
  };

  return (
    <Layout style={{ minHeight: '100vh' }}>
      <Sider collapsible collapsed={collapsed} onCollapse={setCollapsed}>
        <div className="logo">
          {!collapsed && <span>DownPump</span>}
        </div>
        <Menu theme="dark" selectedKeys={[currentPage]} mode="inline">
          <Menu.Item key="dashboard" icon={<DashboardOutlined />} onClick={() => setCurrentPage('dashboard')}>
            仪表盘
          </Menu.Item>
          <Menu.Item key="settings" icon={<SettingOutlined />} onClick={() => setCurrentPage('settings')}>
            设置
          </Menu.Item>
          <Menu.Item key="history" icon={<HistoryOutlined />} onClick={() => setCurrentPage('history')}>
            历史记录
          </Menu.Item>
        </Menu>
      </Sider>
      <Layout className="site-layout">
        <Header className="site-layout-background" style={{ padding: 0 }}>
          <Title level={4} style={{ margin: '16px 24px' }}>
            DownPump 下载泵
          </Title>
        </Header>
        <Content style={{ margin: '0 16px' }}>
          <div className="site-layout-background" style={{ padding: 24, minHeight: 360 }}>
            {renderContent()}
          </div>
        </Content>
        <Footer style={{ textAlign: 'center' }}>
          DownPump ©{new Date().getFullYear()} Created with <GithubOutlined /> 
        </Footer>
      </Layout>
    </Layout>
  );
}

export default App;