# DownPump 下载泵

DownPump（下载泵）是一个 Docker 镜像，用于创建一个持续下载数据的容器，可以用于网络测试、带宽测试或其他需要持续产生下载流量的场景。

## 功能特点

- 持续从指定的URL下载数据
- 可配置下载间隔时间
- 可配置多个下载源
- 实时显示下载进度和统计信息
- 支持设置每日流量上限，超出后自动暂停至次日
- 支持设置下载时间段，只在指定时间内下载
- 支持设置下载速度限制，控制带宽使用
- 自动记录每日下载流量，保存到日志文件
- 轻量级设计，基于Alpine Linux

## 构建镜像

在包含Dockerfile的目录中执行以下命令构建Docker镜像：

```bash
docker build -t downpump .
```

## 运行容器

### 使用Docker命令运行

#### 使用默认配置运行

```bash
docker run -d --name downpump downpump
```

#### 自定义配置示例

```bash
docker run -d --name downpump \
  -e DOWNLOAD_INTERVAL=10 \
  -e DOWNLOAD_URLS="http://speedtest.ftp.otenet.gr/files/test100Mb.db http://speedtest.tele2.net/100MB.zip" \
  -e DAILY_TRAFFIC_LIMIT=2 \
  -e DOWNLOAD_START_TIME="08:30" \
  -e DOWNLOAD_END_TIME="17:30" \
  -e DOWNLOAD_SPEED_LIMIT=1 \
  downpump
```

### 使用Docker Compose运行

项目中提供了`docker-compose.yml`文件，可以使用Docker Compose更方便地管理容器：

#### 使用默认配置运行

```bash
docker-compose up -d
```

#### 自定义配置

您可以编辑`docker-compose.yml`文件，修改环境变量的值来自定义配置：

```yaml
version: '3'

services:
  downpump:
    build:
      context: .
      dockerfile: Dockerfile
    container_name: downpump
    restart: unless-stopped
    environment:
      - DOWNLOAD_INTERVAL=10
      - DOWNLOAD_URLS=http://speedtest.ftp.otenet.gr/files/test100Mb.db http://speedtest.tele2.net/100MB.zip
      - DAILY_TRAFFIC_LIMIT=2
      - DOWNLOAD_START_TIME=08:30
      - DOWNLOAD_END_TIME=17:30
      - DOWNLOAD_SPEED_LIMIT=1
    volumes:
      - ./logs:/app/logs
```

## 环境变量

| 环境变量 | 描述 | 默认值 |
|----------|------|--------|
| `DOWNLOAD_INTERVAL` | 每轮下载之间的等待时间（秒） | 5 |
| `DOWNLOAD_URLS` | 要下载的URL列表，用空格分隔 | "http://speedtest.ftp.otenet.gr/files/test10Mb.db http://speedtest.tele2.net/10MB.zip" |
| `DAILY_TRAFFIC_LIMIT` | 每日下载流量上限（GB），超出后暂停至次日 | 1 |
| `DOWNLOAD_START_TIME` | 允许下载的开始时间（24小时制，格式：HH:MM） | "09:00" |
| `DOWNLOAD_END_TIME` | 允许下载的结束时间（24小时制，格式：HH:MM） | "18:00" |
| `TRAFFIC_LOG_FILE` | 流量日志文件路径 | "/app/traffic.log" |
| `DOWNLOAD_SPEED_LIMIT` | 下载速度限制（MB/s），设为0表示不限速 | 0 |

## 查看日志

```bash
docker logs -f downpump
```

## 停止容器

### 使用Docker命令停止

```bash
docker stop downpump
```

### 使用Docker Compose停止

```bash
docker-compose down
```

## 注意事项

- 此容器会持续产生网络流量，请注意您的网络使用情况
- 下载的文件不会保存在容器中，而是直接输出到/dev/null，不占用任何磁盘空间
- 容器运行过程中不会因为下载文件而增加磁盘占用
- 如果您需要测试更大的带宽，可以增加下载源的数量或选择更大的文件