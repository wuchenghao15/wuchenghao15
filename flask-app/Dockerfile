
# MTSCOS AI Project - Dockerfile
# 基于Python 3.11构建的Flask应用容器

# 第一阶段：构建依赖
FROM python:3.11-slim AS builder

WORKDIR /app

# 安装系统依赖
RUN apt-get update && apt-get install -y \
    gcc \
    python3-dev \
    libssl-dev \
    libffi-dev \
    && rm -rf /var/lib/apt/lists/*

# 复制requirements文件
COPY requirements.txt .

# 安装Python依赖到单独目录
RUN pip install --upgrade pip && \
    pip install --prefix=/install -r requirements.txt

# 第二阶段：运行时镜像
FROM python:3.11-slim AS runtime

WORKDIR /app

# 安装运行时依赖
RUN apt-get update && apt-get install -y \
    openssl \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/*

# 从构建阶段复制依赖
COPY --from=builder /install /usr/local

# 复制应用代码
COPY . .

# 创建必要的目录
RUN mkdir -p logs ssl data backups

# 设置环境变量
ENV FLASK_APP=app.py
ENV FLASK_ENV=production
ENV PYTHONPATH=/app
ENV TZ=Asia/Shanghai

# 暴露端口
EXPOSE 8443 8888

# 健康检查
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
    CMD curl -f http://localhost:8888/health || exit 1

# 启动命令
CMD ["gunicorn", "-w", "4", "-b", "0.0.0.0:8888", "--timeout", "120", "app:app"]
