import React from 'react';
import { Row, Col, Card, Statistic, Button, Progress, Table, Tag, Typography } from 'antd';
import { DownloadOutlined, PauseOutlined, ReloadOutlined } from '@ant-design/icons';

const { Title } = Typography;

const Dashboard = ({ stats, config, startDownload, stopDownload }) => {
  // 格式化字节数为可读格式
  const formatBytes = (bytes, decimals = 2) => {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const dm = decimals < 0 ? 0 : decimals;
    const sizes = ['Bytes', 'KB', 'MB', 'GB', 'TB', 'PB', 'EB', 'ZB', 'YB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(dm)) + ' ' + sizes[i];
  };

  // 计算每日流量限制的进度
  const getDailyLimitProgress = () => {
    if (!config || config.daily_limit_gb <= 0 || !stats) return 0;
    const limitBytes = config.daily_limit_gb * 1024 * 1024 * 1024;
    return Math.min(100, (stats.today_downloaded / limitBytes) * 100);
  };

  // 获取下载源表格数据
  const getSourcesData = () => {
    if (!config || !config.download_sources) return [];
    
    return config.download_sources.map((source, index) => ({
      key: index,
      name: source.name,
      url: source.url,
      status: source.enabled ? '启用' : '禁用',
    }));
  };

  // 表格列定义
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
      dataIndex: 'status',
      key: 'status',
      render: (status) => (
        <Tag color={status === '启用' ? 'green' : 'red'}>
          {status}
        </Tag>
      ),
    },
  ];

  return (
    <div>
      <Title level={3}>仪表盘</Title>
      
      {/* 状态卡片 */}
      <Row gutter={16}>
        <Col xs={24} sm={12} md={8} lg={8} xl={8}>
          <Card className="dashboard-card">
            <Statistic
              title="当前状态"
              value={stats?.is_downloading ? '下载中' : '已停止'}
              valueStyle={{ color: stats?.is_downloading ? '#52c41a' : '#cf1322' }}
              prefix={stats?.is_downloading ? <DownloadOutlined /> : <PauseOutlined />}
            />
            <div className="control-buttons">
              <Button 
                type="primary" 
                onClick={startDownload} 
                disabled={stats?.is_downloading || !config?.enabled}
              >
                开始下载
              </Button>
              <Button 
                danger 
                onClick={stopDownload} 
                disabled={!stats?.is_downloading}
              >
                停止下载
              </Button>
            </div>
          </Card>
        </Col>
        <Col xs={24} sm={12} md={8} lg={8} xl={8}>
          <Card className="dashboard-card">
            <Statistic
              title="今日已下载"
              value={formatBytes(stats?.today_downloaded || 0)}
              prefix={<DownloadOutlined />}
            />
            {config?.daily_limit_gb > 0 && (
              <Progress 
                percent={getDailyLimitProgress()} 
                status={getDailyLimitProgress() >= 100 ? 'exception' : 'active'}
                format={percent => `${percent.toFixed(2)}%`}
              />
            )}
          </Card>
        </Col>
        <Col xs={24} sm={12} md={8} lg={8} xl={8}>
          <Card className="dashboard-card">
            <Statistic
              title="总计已下载"
              value={formatBytes(stats?.total_downloaded || 0)}
              prefix={<DownloadOutlined />}
            />
          </Card>
        </Col>
      </Row>

      {/* 当前下载信息 */}
      {stats?.current_download && (
        <Card title="当前下载" className="dashboard-card">
          <Row gutter={16}>
            <Col span={8}>
              <Statistic title="下载源" value={stats.current_download.name} />
            </Col>
            <Col span={16}>
              <Statistic 
                title="URL" 
                value={stats.current_download.url} 
                formatter={value => (
                  <span style={{ fontSize: '14px', wordBreak: 'break-all' }}>{value}</span>
                )}
              />
            </Col>
          </Row>
        </Card>
      )}

      {/* 下载源列表 */}
      <Card title="下载源列表" className="dashboard-card">
        <Table 
          columns={columns} 
          dataSource={getSourcesData()} 
          pagination={false} 
          size="middle"
        />
      </Card>

      {/* 配置信息 */}
      <Card title="配置信息" className="dashboard-card">
        <Row gutter={16}>
          <Col span={8}>
            <Statistic 
              title="下载间隔" 
              value={config?.interval_seconds || 0} 
              suffix="秒" 
            />
          </Col>
          <Col span={8}>
            <Statistic 
              title="每日流量限制" 
              value={config?.daily_limit_gb > 0 ? config.daily_limit_gb : '无限制'} 
              suffix={config?.daily_limit_gb > 0 ? 'GB' : ''} 
            />
          </Col>
          <Col span={8}>
            <Statistic 
              title="下载速度限制" 
              value={config?.speed_limit_kbps > 0 ? config.speed_limit_kbps : '无限制'} 
              suffix={config?.speed_limit_kbps > 0 ? 'KB/s' : ''} 
            />
          </Col>
        </Row>
      </Card>
    </div>
  );
};

export default Dashboard;