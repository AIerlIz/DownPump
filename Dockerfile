FROM python:3.9-slim

WORKDIR /app

# 设置时区为亚洲/上海
RUN apt-get update && \
    apt-get install -y tzdata && \
    ln -fs /usr/share/zoneinfo/Asia/Shanghai /etc/localtime && \
    dpkg-reconfigure -f noninteractive tzdata && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

# 复制依赖文件并安装依赖
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 复制应用程序文件
COPY downpump.py .
COPY config.yaml .

# 设置卷，用于持久化日志
VOLUME ["/app/logs"]

# 运行应用
CMD ["python", "downpump.py"]