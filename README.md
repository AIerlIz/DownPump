# DownPump

一个基于Docker的下载泵工具，可以按照设定的时间和流量限制自动下载文件。

## 功能特点

- 支持多URL下载
- 可设置下载时间段
- 可设置每日流量上限
- 可设置下载速度限制
- 自动记录流量使用情况

## 使用方法

### 本地运行

1. 克隆仓库
   ```bash
   git clone https://github.com/yourusername/DownPump.git
   cd DownPump
   ```

2. 修改配置
   在`docker-compose.yml`文件中修改环境变量：
   ```yaml
   environment:
     - DOWNLOAD_INTERVAL=5            # 下载间隔（秒）
     - DOWNLOAD_URLS=http://example.com/file1 http://example.com/file2  # 下载链接，空格分隔
     - DAILY_TRAFFIC_LIMIT=1          # 每日流量上限（GB）
     - DOWNLOAD_START_TIME=09:00      # 下载开始时间
     - DOWNLOAD_END_TIME=18:00        # 下载结束时间
     - TRAFFIC_LOG_FILE=/app/traffic.log  # 流量日志文件
     - DOWNLOAD_SPEED_LIMIT=0         # 下载速度限制（MB/s），0表示不限速
   ```

3. 启动容器
   ```bash
   docker-compose up -d
   ```

### 使用Docker Hub镜像

```bash
docker run -d \
  --name downpump \
  -e DOWNLOAD_INTERVAL=5 \
  -e DOWNLOAD_URLS="http://example.com/file1 http://example.com/file2" \
  -e DAILY_TRAFFIC_LIMIT=1 \
  -e DOWNLOAD_START_TIME=09:00 \
  -e DOWNLOAD_END_TIME=18:00 \
  -e TRAFFIC_LOG_FILE=/app/traffic.log \
  -e DOWNLOAD_SPEED_LIMIT=0 \
  -v ./logs:/app/logs \
  yourusername/downpump:latest
```

## GitHub Actions 自动构建

本项目使用GitHub Actions自动构建Docker镜像并发布到Docker Hub。

### 设置步骤

1. 在GitHub仓库中，进入 Settings -> Secrets and variables -> Actions
2. 添加以下密钥：
   - `DOCKERHUB_USERNAME`: 你的Docker Hub用户名
   - `DOCKERHUB_TOKEN`: 你的Docker Hub访问令牌（不是密码）

### 触发构建

以下操作会触发自动构建：

- 向`main`分支推送代码
- 创建Pull Request到`main`分支
- 创建版本标签（格式：`v*.*.*`，例如`v1.0.0`）

### 镜像标签

- `latest`: 最新的`main`分支构建
- `vX.Y.Z`: 对应版本标签
- `vX.Y`: 主要和次要版本
- 分支名: 对应分支的最新构建
- SHA: 提交的短SHA值

## 注意事项

- 确保`download.sh`脚本有执行权限
- Windows用户可能需要处理行尾符号问题（CRLF vs LF）