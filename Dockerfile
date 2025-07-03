# 使用多阶段构建减小镜像大小

# 构建阶段
FROM python:3.9-alpine AS builder

WORKDIR /app

# 安装构建依赖
RUN apk add --no-cache --virtual .build-deps gcc musl-dev

# 复制并安装依赖
COPY requirements.txt .
RUN pip install --no-cache-dir --user -r requirements.txt

# 最终阶段
FROM python:3.9-alpine

WORKDIR /app

# 设置时区为亚洲/上海
RUN apk add --no-cache tzdata && \
    cp /usr/share/zoneinfo/Asia/Shanghai /etc/localtime && \
    echo "Asia/Shanghai" > /etc/timezone && \
    apk del tzdata

# 从构建阶段复制Python包
COPY --from=builder /root/.local /root/.local
ENV PATH=/root/.local/bin:$PATH

# 复制应用程序文件
COPY downpump.py .

# 设置卷，用于持久化日志和配置
VOLUME ["/app/logs", "/app/config.yaml"]

# 运行应用
CMD ["python", "downpump.py"]