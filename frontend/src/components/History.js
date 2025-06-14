import React from 'react';
import { Card, Button, Table, Typography, Row, Col, Statistic, Empty } from 'antd';
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts';
import { DownloadOutlined, ReloadOutlined } from '@ant-design/icons';

const { Title } = Typography;

const History = ({ stats, resetStats }) => {
  // 格式化字节数为可读格式
  const formatBytes = (bytes, decimals = 2) => {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const dm = decimals < 0 ? 0 : decimals;
    const sizes = ['Bytes', 'KB', 'MB', 'GB', 'TB', 'PB', 'EB', 'ZB', 'YB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(dm)) + ' ' + sizes[i];
  };

  // 准备图表数据
  const getChartData = () => {
    if (!stats || !stats.download_history || stats.download_history.length === 0) {
      return [];
    }

    return stats.download_history.map(item => ({
      date: item.date,
      downloaded: item.downloaded / (1024 * 1024 * 1024), // 转换为GB
    }));
  };

  // 准备表格数据
  const getTableData = () => {
    if (!stats || !stats.download_history || stats.download_history.length === 0) {
      return [];
    }

    return stats.download_history.map((item, index) => ({
      key: index,
      date: item.date,
      downloaded: formatBytes(item.downloaded),
      downloadedBytes: item.downloaded,
    }));
  };

  // 表格列定义
  const columns = [
    {
      title: '日期',
      dataIndex: 'date',
      key: 'date',
      sorter: (a, b) => new Date(a.date) - new Date(b.date),
      defaultSortOrder: 'descend',
    },
    {
      title: '下载量',
      dataIndex: 'downloaded',
      key: 'downloaded',
      sorter: (a, b) => a.downloadedBytes - b.downloadedBytes,
    },
  ];

  // 计算总下载量
  const getTotalDownloaded = () => {
    if (!stats || !stats.download_history || stats.download_history.length === 0) {
      return 0;
    }

    return stats.download_history.reduce((total, item) => total + item.downloaded, 0);
  };

  // 计算平均每日下载量
  const getAverageDownloaded = () => {
    if (!stats || !stats.download_history || stats.download_history.length === 0) {
      return 0;
    }

    const total = getTotalDownloaded();
    return total / stats.download_history.length;
  };

  return (
    <div>
      <Title level={3}>历史记录</Title>
      
      {/* 统计卡片 */}
      <Row gutter={16}>
        <Col xs={24} sm={12} md={8} lg={8} xl={8}>
          <Card className="dashboard-card">
            <Statistic
              title="历史总下载量"
              value={formatBytes(getTotalDownloaded())}
              prefix={<DownloadOutlined />}
            />
          </Card>
        </Col>
        <Col xs={24} sm={12} md={8} lg={8} xl={8}>
          <Card className="dashboard-card">
            <Statistic
              title="平均每日下载量"
              value={formatBytes(getAverageDownloaded())}
              prefix={<DownloadOutlined />}
            />
          </Card>
        </Col>
        <Col xs={24} sm={12} md={8} lg={8} xl={8}>
          <Card className="dashboard-card">
            <Statistic
              title="记录天数"
              value={stats?.download_history?.length || 0}
              suffix="天"
            />
            <div className="control-buttons">
              <Button 
                type="primary" 
                danger 
                icon={<ReloadOutlined />} 
                onClick={resetStats}
              >
                重置统计
              </Button>
            </div>
          </Card>
        </Col>
      </Row>

      {/* 历史图表 */}
      <Card title="下载历史图表" className="dashboard-card">
        {getChartData().length > 0 ? (
          <div className="chart-container">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart
                data={getChartData()}
                margin={{
                  top: 5,
                  right: 30,
                  left: 20,
                  bottom: 5,
                }}
              >
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="date" />
                <YAxis name="下载量 (GB)" />
                <Tooltip formatter={(value) => [`${value.toFixed(2)} GB`, '下载量']} />
                <Bar dataKey="downloaded" fill="#1890ff" name="下载量 (GB)" />
              </BarChart>
            </ResponsiveContainer>
          </div>
        ) : (
          <Empty description="暂无历史数据" />
        )}
      </Card>

      {/* 历史表格 */}
      <Card title="下载历史详情" className="dashboard-card">
        <Table 
          columns={columns} 
          dataSource={getTableData()} 
          pagination={{ pageSize: 10 }}
        />
      </Card>
    </div>
  );
};

export default History;