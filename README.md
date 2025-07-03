# DownPump

DownPump 是一个用于消耗并记录下载流量的工具，可以配置下载时间段、多个下载URL、每日下载量上限和下载速度限制。程序只消耗下载流量，不会将下载的数据写入磁盘。

## 功能特点

- 只消耗下载流量，不写入磁盘
- 定期记录已下载流量到日志文件
- 配置可下载时间段，支持多个时间段设置
- 配置多个下载URL，随机选择
- 配置每日下载量上限（单位：GB）
- 配置下载速度限制（单位：MB/s）
- 自动创建下一个可下载时间的定时任务
- 支持Docker部署

## 配置说明

配置文件为 `config.yaml`，包含以下配置项：

```yaml
# 注意：程序已修改为不写入磁盘，仅消耗下载流量

# 每日下载流量上限 (GB)
daily_limit_gb: 10

# 下载速度限制 (MB/s)
speed_limit_mb: 5

# 流量记录间隔 (秒)
record_interval_seconds: 60

# 下载时间段配置（允许下载的时间范围）
download_time_ranges:
  - start: "01:00"  # 开始时间 (24小时制)
    end: "07:00"    # 结束时间 (24小时制)
  - start: "23:00"  # 开始时间 (24小时制)
    end: "00:00"    # 结束时间 (24小时制)
# 注意：只要当前时间在任何一个配置的时间段内，就会进行下载

# 下载URL列表 (随机选择)
download_urls:
  - "https://speed.hetzner.de/100MB.bin"
  - "https://proof.ovh.net/files/100Mb.dat"
  - "https://speed.cloudflare.com/100mb.bin"
  - "https://download.thinkbroadband.com/100MB.zip"
```

## 使用方法

### 使用 Docker Compose（推荐）

1. 确保已安装 Docker 和 Docker Compose
2. 克隆或下载本项目
3. 根据需要修改 `config.yaml` 配置文件
4. 在项目目录下运行：

```bash
docker-compose up -d
```

### 使用 Docker

1. 构建 Docker 镜像：

```bash
docker build -t downpump .
```

2. 运行 Docker 容器：

```bash
docker run -d \
  --name downpump \
  -v $(pwd)/logs:/app/logs \
  -v $(pwd)/config.yaml:/app/config.yaml \
  --restart unless-stopped \
  downpump
```

### 直接运行（不使用 Docker）

1. 确保已安装 Python 3.7+
2. 安装依赖：

```bash
pip install -r requirements.txt
```

3. 运行程序：

```bash
python downpump.py
```

## 日志

程序运行日志保存在 `downpump.log` 文件中，同时也会输出到控制台。

## 流量记录

程序会定期记录当日已下载的流量数据到 `logs/traffic_YYYYMMDD.log` 文件中，记录间隔可通过 `config.yaml` 中的 `record_interval_seconds` 配置项设置，默认为60秒。

流量记录文件格式示例：
```
2023-05-01 00:00:00 - 已下载: 0.00 MB (0.00 GB) - 重置后初始流量
2023-05-01 12:00:00 - 已下载: 256.00 MB (0.25 GB)
2023-05-01 12:01:00 - 已下载: 512.00 MB (0.50 GB)
2023-05-01 23:59:59 - 已下载: 1024.00 MB (1.00 GB) - 重置前最终流量
2023-05-02 00:00:00 - 已下载: 0.00 MB (0.00 GB) - 重置后初始流量
```

特殊记录点：
- 程序启动时会记录一次初始流量
- 每日流量重置前后各记录一次
- 下载任务完成后记录一次
- 按配置的时间间隔定期记录

## 下载时间段说明

下载时间段是指允许程序进行下载的时间范围。DownPump的工作原理如下：

- 只要当前时间在任何一个配置的时间段内，程序就会进行下载
- 当前时间不在任何配置的时间段内时，程序会停止下载并等待下一个下载时间段
- 程序会在每个时间段的开始时间自动启动下载任务
- 程序会在每个时间段的结束时间自动停止下载任务
- 如果没有配置任何下载时间段，程序会默认全天候下载
- 支持配置多个不连续的时间段，程序会在每个时间段内自动下载
- 支持配置跨天的时间段（如23:00-06:00），程序会正确处理

## 注意事项

- 程序只消耗下载流量，不会将数据写入磁盘
- 每日下载量统计在程序重启后会重置，如需持久化可以修改代码实现
- 即使在下载时间段内，如果达到每日下载上限，程序也会停止下载