FROM alpine:latest

# 安装必要的工具
RUN apk add --no-cache curl wget bash bc sed

# 创建工作目录
WORKDIR /app

# 复制下载脚本到容器中
COPY download.sh /app/

# 确保脚本使用Unix格式的行尾并添加执行权限
RUN sed -i 's/\r$//' /app/download.sh && chmod +x /app/download.sh

# 设置环境变量，可以通过环境变量控制下载行为
ENV DOWNLOAD_INTERVAL=5 \
    DOWNLOAD_URLS="http://speedtest.ftp.otenet.gr/files/test10Mb.db http://speedtest.tele2.net/10MB.zip" \
    DAILY_TRAFFIC_LIMIT=1 \
    DOWNLOAD_START_TIME="09:00" \
    DOWNLOAD_END_TIME="18:00" \
    TRAFFIC_LOG_FILE="/app/traffic.log" \
    DOWNLOAD_SPEED_LIMIT=0

# 运行下载脚本
CMD ["/app/download.sh"]