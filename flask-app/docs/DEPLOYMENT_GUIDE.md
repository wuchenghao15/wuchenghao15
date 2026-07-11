
# MTSCOS AI Project - 容器化部署指南

## 概述

本项目已完整容器化，支持一键部署和运行。以下是详细的部署说明。

## 环境要求

- **Docker**: 20.10+
- **Docker Compose**: 2.0+
- **操作系统**: Linux / macOS / Windows (WSL2)

## 快速开始

### 1. 启动服务

```bash
# 进入项目目录
cd flask-app

# 启动服务（首次启动会自动构建镜像）
bash start.sh start
```

### 2. 访问服务

- **主页面**: https://localhost
- **API接口**: https://localhost/api
- **健康检查**: https://localhost/health

### 3. 停止服务

```bash
bash start.sh stop
```

## 服务架构

```
┌─────────────────────────────────────────────────────────────────┐
│                    Docker Compose Network                       │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│   ┌──────────────┐    ┌──────────────┐    ┌──────────────┐    │
│   │   Nginx      │    │   Redis      │    │   PostgreSQL │    │
│   │   (反向代理) │    │   (缓存)    │    │   (可选)     │    │
│   │   :80, :443  │    │   :6379      │    │   :5432      │    │
│   └──────┬───────┘    └──────┬───────┘    └──────┬───────┘    │
│          │                   │                   │             │
│          ▼                   ▼                   ▼             │
│   ┌──────────────┐    ┌──────────────┐    ┌──────────────┐    │
│   │   Flask App  │◄───│   Gunicorn  │    │   Prometheus │    │
│   │   (主应用)   │    │   (WSGI)    │    │   (监控)     │    │
│   │   :8888      │    └──────────────┘    └──────┬───────┘    │
│   └──────────────┘                               │             │
│                                                  ▼             │
│                                           ┌──────────────┐    │
│                                           │   Grafana    │    │
│                                           │   (可视化)   │    │
│                                           │   :3000      │    │
│                                           └──────────────┘    │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

## 服务配置

### 环境变量

编辑 `.env` 文件配置服务：

```bash
cp .env.example .env
vim .env
```

**主要配置项**:

| 配置项 | 说明 | 默认值 |
|--------|------|--------|
| `SECRET_KEY` | 应用密钥 | your-secret-key-here |
| `FLASK_ENV` | 运行环境 | production |
| `DATABASE_URI` | 数据库连接 | sqlite:///data/app.db |
| `SERVER_PORT` | 服务端口 | 8888 |
| `REDIS_HOST` | Redis地址 | redis |
| `POSTGRES_DB` | PostgreSQL库名 | mtscos_db |

### 启动选项

```bash
# 启动基础服务（Flask + Redis + Nginx）
bash start.sh start

# 启动时包含PostgreSQL
bash start.sh start --with-postgres

# 启动时包含监控服务（Prometheus + Grafana）
bash start.sh start --with-monitoring

# 启动所有服务
bash start.sh start --with-postgres --with-monitoring
```

## 管理命令

```bash
# 查看服务状态
bash start.sh status

# 查看日志
bash start.sh logs
bash start.sh logs -f  # 实时日志

# 重启服务
bash start.sh restart

# 重新构建镜像
bash start.sh build

# 连接到Redis
bash start.sh redis-cli

# 连接到PostgreSQL（需要 --with-postgres）
bash start.sh psql

# 清理所有数据（危险操作）
bash start.sh clean
```

## 目录结构

```
flask-app/
├── app/                    # 应用代码
├── data/                   # SQLite数据库（挂载卷）
├── logs/                   # 日志文件（挂载卷）
├── ssl/                    # SSL证书（挂载卷）
├── backups/                # 备份文件（挂载卷）
├── nginx/                  # Nginx配置
│   ├── nginx.conf          # 主配置
│   └── conf.d/
│       └── mtscos.conf     # 虚拟主机配置
├── prometheus/             # Prometheus配置（可选）
├── grafana/                # Grafana配置（可选）
├── redis-data/             # Redis数据（挂载卷）
├── docker-compose.yml      # Docker Compose配置
├── Dockerfile              # Docker镜像构建文件
├── .env                    # 环境变量配置
└── start.sh                # 启动脚本
```

## 生产环境部署建议

### 1. 配置HTTPS

默认使用自签名证书用于开发测试。生产环境请配置正式SSL证书：

```bash
# 将正式证书放入 ssl/ 目录
cp /path/to/cert.pem ssl/cert.pem
cp /path/to/key.pem ssl/key.pem
```

### 2. 配置域名

编辑 `nginx/conf.d/mtscos.conf`，修改 `server_name`：

```nginx
server_name your-domain.com;
```

### 3. 配置PostgreSQL（推荐）

生产环境建议使用PostgreSQL替代SQLite：

```bash
# 启动时启用PostgreSQL
bash start.sh start --with-postgres

# 修改 .env 配置数据库
DATABASE_URI=postgresql://admin:password@postgres:5432/mtscos_db
```

### 4. 配置监控

```bash
# 启动监控服务
bash start.sh start --with-monitoring

# 访问Grafana
https://localhost:3000
# 默认用户名: admin
# 默认密码: admin（在.env中配置）
```

## 故障排查

### 常见问题

**1. 服务无法启动**

```bash
# 查看日志
bash start.sh logs

# 检查端口占用
netstat -tlnp | grep 80
netstat -tlnp | grep 443
```

**2. SSL证书问题**

```bash
# 重新生成证书
rm -rf ssl/*
bash start.sh start
```

**3. 数据库连接失败**

```bash
# 检查数据库服务状态
bash start.sh status

# 查看数据库日志
docker-compose logs postgres
```

**4. 权限问题**

```bash
# 确保目录权限正确
chown -R $USER:$USER data logs ssl backups
```

## 性能优化建议

### 1. 调整Gunicorn工作进程数

编辑 `Dockerfile`：

```dockerfile
CMD ["gunicorn", "-w", "4", "-b", "0.0.0.0:8888", "--timeout", "120", "app:app"]
```

建议工作进程数 = CPU核心数 * 2 + 1

### 2. 启用Redis缓存

确保配置文件中启用了Redis：

```bash
CACHE_TYPE=redis
REDIS_HOST=redis
REDIS_PORT=6379
```

### 3. 配置Nginx负载均衡

如需多实例部署，可在 `nginx/conf.d/mtscos.conf` 中配置负载均衡。

## 备份与恢复

### 备份数据库

```bash
# SQLite备份
cp data/app.db data/app.db.backup.$(date +%Y%m%d_%H%M%S)

# PostgreSQL备份
docker-compose exec postgres pg_dump -U admin mtscos_db > backup.sql
```

### 恢复数据库

```bash
# SQLite恢复
cp data/app.db.backup data/app.db

# PostgreSQL恢复
docker-compose exec -T postgres psql -U admin mtscos_db < backup.sql
```

## 版本更新

```bash
# 停止服务
bash start.sh stop

# 拉取最新代码
git pull

# 重新构建并启动
bash start.sh build
bash start.sh start
```

## 联系我们

如有问题，请联系开发团队。
