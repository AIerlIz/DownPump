FROM alpine:latest

# 安装必要的软件包
RUN apk add --no-cache \
    curl \
    wget \
    bash \
    nodejs \
    npm \
    python3 \
    py3-pip \
    tzdata

# 设置工作目录
WORKDIR /app

# 复制应用文件
COPY ./backend /app/backend
COPY ./frontend/build /app/frontend

# 安装Python依赖
RUN pip3 install --no-cache-dir -r /app/backend/requirements.txt

# 设置时区为亚洲/上海
RUN cp /usr/share/zoneinfo/Asia/Shanghai /etc/localtime \
    && echo "Asia/Shanghai" > /etc/timezone

# 暴露端口
EXPOSE 8080

# 启动应用
CMD ["python3", "/app/backend/app.py"]