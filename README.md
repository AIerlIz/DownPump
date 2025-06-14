# DownPump 下载泵

DownPump（下载泵）是一个 Docker 镜像，用于创建一个持续下载数据的容器，可以用于网络测试、带宽测试或其他需要持续产生下载流量的场景。

## 功能特点

- WebUI仪表盘和配置界面
- 持续从指定的URL下载数据
- 可配置下载间隔时间
- 可配置多个下载源
- 实时显示下载进度和统计信息
- 支持设置每日流量上限，超出后自动暂停至次日
- 支持设置下载时间段，只在指定时间内下载
- 支持设置下载速度限制，控制带宽使用
- 自动记录每日下载流量，保存到日志文件
- 轻量级设计，基于Alpine Linux
- 支持Docker Compose部署

## 安装与使用

### 前提条件

- 安装 [Docker](https://docs.docker.com/get-docker/)
- 安装 [Docker Compose](https://docs.docker.com/compose/install/) (可选，但推荐)

### 使用 Docker Compose 部署

1. 克隆仓库

```bash
git clone https://github.com/yourusername/downpump.git
cd downpump
```

2. 构建并启动容器

```bash
docker-compose up -d
```

3. 访问WebUI

打开浏览器，访问 `http://localhost:8080`

### 使用 Docker 命令部署

1. 构建镜像

```bash
docker build -t downpump .
```

2. 运行容器

```bash
docker run -d --name downpump -p 8080:8080 -v $(pwd)/logs:/app/logs downpump
```

3. 访问WebUI

打开浏览器，访问 `http://localhost:8080`

## 配置说明

通过WebUI界面，您可以配置以下参数：

- **下载源**：可添加多个下载URL，支持启用/禁用单个源
- **下载间隔**：每次下载完成后的等待时间（秒）
- **每日流量限制**：设置每日最大下载流量（GB），超出后自动暂停至次日
- **下载速度限制**：限制下载速度（KB/s）
- **活跃时间段**：设置只在特定时间段内下载

## 注意事项

- 此容器会持续产生网络流量，请注意您的网络使用情况
- 下载的文件不会保存在容器中，而是直接输出到/dev/null，不占用任何磁盘空间
- 容器运行过程中不会因为下载文件而增加磁盘占用
- 如果您需要测试更大的带宽，可以增加下载源的数量或选择更大的文件

## 开发

### 前端开发

```bash
cd frontend
npm install
npm start
```

### 后端开发

```bash
cd backend
pip install -r requirements.txt
python app.py
```

## 许可证

MIT