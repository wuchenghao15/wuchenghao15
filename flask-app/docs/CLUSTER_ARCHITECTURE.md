# MTSCOS AI Project - 集群与负载均衡架构

## 概述

本项目已实现应用集群和负载均衡功能，支持水平扩展和高可用性部署。

## 集群架构

### 整体架构图

```
┌─────────────────────────────────────────────────────────────────────────┐
│                        外部访问层                                       │
│                         HTTPS/443                                      │
├─────────────────────────────────────────────────────────────────────────┤
│                         Nginx 负载均衡器                                │
│         ┌───────────────────────────────────────────────┐              │
│         │  策略: IP Hash / Round Robin / Least Conn    │              │
│         │  健康检查 / 故障转移 / 会话保持                │              │
│         └───────────────────────────────────────────────┘              │
├──────────────┬───────────────────┬──────────────────────┐              │
│              │                   │                      │              │
▼              ▼                   ▼                      ▼              │
┌────────────────┐ ┌────────────────┐ ┌────────────────┐                 │
│   Node 1       │ │   Node 2       │ │   Node 3       │                 │
│  (Master)      │ │  (Slave)       │ │  (Slave)       │                 │
│  weight=3      │ │  weight=2      │ │  weight=2      │                 │
├────────────────┤ ├────────────────┤ ├────────────────┤                 │
│   Flask App    │ │   Flask App    │ │   Flask App    │                 │
│   Gunicorn     │ │   Gunicorn     │ │   Gunicorn     │                 │
│   8888/tcp     │ │   8888/tcp     │ │   8888/tcp     │                 │
└───────┬────────┘ └───────┬────────┘ └───────┬────────┘                 │
        │                  │                  │                          │
        ▼                  ▼                  ▼                          │
┌──────────────────────────────────────────────────────────────────┐      │
│                        共享存储层                                 │      │
│   ┌─────────────┐     ┌─────────────┐     ┌─────────────┐       │      │
│   │   Redis     │     │ PostgreSQL  │     │   Shared   │       │      │
│   │   (缓存)    │     │   (数据库)  │     │   Volume   │       │      │
│   └─────────────┘     └─────────────┘     └─────────────┘       │      │
└──────────────────────────────────────────────────────────────────┘      │
└─────────────────────────────────────────────────────────────────────────┘
```

### 集群组件

| 组件 | 角色 | 数量 | 说明 |
|------|------|------|------|
| **Nginx** | 负载均衡器 | 1 | 接收所有外部请求，分发到后端节点 |
| **Node 1** | Master节点 | 1 | 主节点，权重3，处理写操作 |
| **Node 2** | Slave节点 | 1 | 从节点，权重2，处理读操作 |
| **Node 3** | Slave节点 | 1 | 从节点，权重2，处理读操作 |
| **Redis** | 共享缓存 | 1 | 会话共享、数据缓存 |
| **PostgreSQL** | 共享数据库 | 1 | 所有节点共享数据 |

### 节点配置

```yaml
# 节点权重配置
upstream mtscos_cluster {
    ip_hash;  # 会话保持
    
    server mtscos-app-1:8888 weight=3 max_fails=3 fail_timeout=30s;
    server mtscos-app-2:8888 weight=2 max_fails=3 fail_timeout=30s;
    server mtscos-app-3:8888 weight=2 max_fails=3 fail_timeout=30s;
}
```

## 负载均衡策略

### 支持的策略

| 策略 | 说明 | 适用场景 |
|------|------|----------|
| **IP Hash** | 基于客户端IP哈希分配 | 需要会话保持的场景 |
| **Round Robin** | 轮询分配 | 通用场景，负载均匀 |
| **Least Connections** | 最少连接数优先 | 连接时间差异大的场景 |
| **Weighted Round Robin** | 加权轮询 | 节点性能差异大的场景 |

### Nginx配置策略

```nginx
# IP Hash策略（默认）
upstream mtscos_cluster {
    ip_hash;
    server mtscos-app-1:8888 weight=3;
    server mtscos-app-2:8888 weight=2;
    server mtscos-app-3:8888 weight=2;
}

# 或使用轮询策略
upstream mtscos_cluster {
    least_conn;  # 或 round_robin
    server mtscos-app-1:8888 weight=3;
    server mtscos-app-2:8888 weight=2;
    server mtscos-app-3:8888 weight=2;
}
```

### 集群服务策略

```python
from app.services.cluster_service import cluster_service, LoadBalanceStrategy

# 设置负载均衡策略
cluster_service.set_load_balance_strategy(LoadBalanceStrategy.ROUND_ROBIN)

# 或使用最小连接数策略
cluster_service.set_load_balance_strategy(LoadBalanceStrategy.LEAST_CONNECTIONS)

# 选择节点
node = cluster_service.select_node(client_ip='192.168.1.100')
```

## 高可用性特性

### 健康检查

```python
# 自动健康检查（每10秒）
cluster_service.start_health_check()

# 手动检查节点状态
node = cluster_service.get_node('node-1')
print(f"节点状态: {node.status.value}")
```

### 故障转移

```nginx
# Nginx自动故障转移
proxy_next_upstream error timeout invalid_header http_500 http_502 http_503 http_504;
proxy_next_upstream_tries 3;
```

### 自动故障恢复

```python
# 节点恢复自动加入集群
cluster_service.record_heartbeat('node-2')  # 更新心跳
cluster_service.update_node_status('node-2', NodeStatus.ACTIVE)
```

## 快速启动

### 启动集群

```bash
# 进入项目目录
cd flask-app

# 启动集群模式（3节点）
bash start.sh start-cluster

# 查看集群状态
bash start.sh status
```

### 停止集群

```bash
bash start.sh stop-cluster
```

### 重启集群

```bash
bash start.sh restart-cluster
```

### 查看日志

```bash
# 查看所有日志
bash start.sh logs

# 实时查看日志
bash start.sh logs -f

# 查看特定服务日志
docker-compose -f docker-compose.cluster.yml logs nginx
docker-compose -f docker-compose.cluster.yml logs mtscos-app-1
```

## 集群管理API

### 获取集群状态

```python
from app.services.cluster_service import cluster_service

# 获取集群统计
stats = cluster_service.get_cluster_stats()
print(stats)
```

### 添加节点

```python
# 动态添加节点
success = cluster_service.add_node({
    'id': 'node-4',
    'name': 'MTSCOS Node 4',
    'host': 'mtscos-app-4',
    'port': 8888,
    'role': 'slave',
    'weight': 2
})
```

### 移除节点

```python
# 动态移除节点
success = cluster_service.remove_node('node-4')
```

### 提升主节点

```python
# 将从节点提升为主节点
success = cluster_service.promote_to_master('node-2')
```

### 获取主节点

```python
master = cluster_service.get_master_node()
print(f"主节点: {master.id} - {master.host}:{master.port}")
```

## 监控与告警

### Prometheus监控

访问地址: `http://localhost:9090`

监控指标:
- `up` - 节点存活状态
- `http_requests_total` - 请求总数
- `http_request_duration_seconds` - 请求耗时
- `node_cpu_usage` - CPU使用率
- `node_memory_usage` - 内存使用率

### Grafana可视化

访问地址: `http://localhost:3000`

默认用户名: `admin`
默认密码: `admin`

预配置仪表板:
- 集群状态概览
- 请求负载分布
- 节点健康状态
- 性能指标趋势

## 生产环境配置建议

### 1. 增加节点数量

编辑 `docker-compose.cluster.yml`，添加更多节点:

```yaml
mtscos-app-4:
  build:
    context: .
    dockerfile: Dockerfile
  container_name: mtscos-app-4
  environment:
    - CLUSTER_NODE_ID=node-4
    - CLUSTER_NODE_ROLE=slave
    # ... 其他配置
```

### 2. 配置Nginx权重

根据节点性能调整权重:

```nginx
upstream mtscos_cluster {
    ip_hash;
    server mtscos-app-1:8888 weight=4;  # 高性能节点
    server mtscos-app-2:8888 weight=3;
    server mtscos-app-3:8888 weight=3;
    server mtscos-app-4:8888 weight=2;  # 低性能节点
}
```

### 3. 配置SSL证书

使用正式SSL证书替换自签名证书:

```bash
cp /path/to/your-cert.pem ssl/cert.pem
cp /path/to/your-key.pem ssl/key.pem
```

### 4. 配置域名

编辑 `nginx/nginx.cluster.conf`:

```nginx
server {
    listen 443 ssl;
    server_name your-domain.com;
    
    ssl_certificate /etc/nginx/ssl/cert.pem;
    ssl_certificate_key /etc/nginx/ssl/key.pem;
    # ...
}
```

### 5. 配置数据库连接池

在应用配置中增加数据库连接池:

```python
# app/config.py
SQLALCHEMY_ENGINE_OPTIONS = {
    'pool_size': 20,
    'max_overflow': 50,
    'pool_timeout': 30,
    'pool_recycle': 1800
}
```

## 性能优化建议

### 1. 启用Gzip压缩

```nginx
gzip on;
gzip_types text/plain text/css application/json application/javascript;
gzip_min_length 1024;
```

### 2. 配置缓存

```nginx
location /static/ {
    root /usr/share/nginx/html;
    expires 30d;
    add_header Cache-Control "public, immutable";
}
```

### 3. 调整Worker进程数

```nginx
worker_processes auto;
worker_connections 4096;
```

### 4. 启用HTTP/2

```nginx
server {
    listen 443 ssl http2;
    # ...
}
```

## 故障排查

### 常见问题

**1. 节点无法加入集群**

```bash
# 检查节点健康状态
bash start.sh status

# 查看节点日志
docker-compose -f docker-compose.cluster.yml logs mtscos-app-2
```

**2. 负载均衡不生效**

```bash
# 检查Nginx配置
docker exec -it mtscos-nginx nginx -t

# 查看Nginx状态
curl http://localhost/nginx_status
```

**3. 数据库连接失败**

```bash
# 检查数据库服务
docker-compose -f docker-compose.cluster.yml exec postgres psql -U admin -d mtscos_db
```

**4. 会话不一致**

确保所有节点使用相同的Redis作为会话存储:

```python
# app/config.py
SESSION_TYPE = 'redis'
SESSION_REDIS = Redis(host='redis', port=6379)
```

## 扩展方案

### 1. 增加更多节点

```bash
# 添加第4个节点
docker-compose -f docker-compose.cluster.yml up -d --scale mtscos-app=4
```

### 2. 使用Kubernetes（生产推荐）

```yaml
# deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: mtscos-app
spec:
  replicas: 5
  selector:
    matchLabels:
      app: mtscos
  template:
    spec:
      containers:
      - name: mtscos-app
        image: mtscos-app:latest
        ports:
        - containerPort: 8888
```

### 3. 配置CDN

```nginx
# 配置CDN缓存静态资源
location /static/ {
    proxy_pass https://your-cdn.com/static/;
    expires 7d;
}
```

## 总结

集群和负载均衡架构已完成，主要特性包括:

1. **水平扩展**: 支持动态添加/移除节点
2. **负载均衡**: 多种策略（IP Hash、轮询、最小连接）
3. **高可用性**: 自动健康检查和故障转移
4. **会话保持**: IP Hash确保会话一致性
5. **监控集成**: Prometheus + Grafana实时监控
6. **一键部署**: 简单的启动脚本

所有功能已完整实现，可以直接使用！
