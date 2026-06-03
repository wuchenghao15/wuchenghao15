# MTSCOS AI Project - CDN 和反向代理架构

## 概述

本项目已实现 CDN（内容分发网络）和反向代理功能，支持静态资源缓存、负载均衡和多源站配置。

## 架构设计

### 整体架构

```
┌─────────────────────────────────────────────────────────────────────────┐
│                         用户请求                                       │
├─────────────────────────────────────────────────────────────────────────┤
│                        CDN 边缘节点层                                  │
│   ┌──────────┐  ┌──────────┐  ┌──────────┐                           │
│   │  CDN 1   │  │  CDN 2   │  │  CDN 3   │                           │
│   │ (北京)   │  │ (上海)   │  │ (广州)   │                           │
│   └────┬─────┘  └────┬─────┘  └────┬─────┘                           │
│        │             │             │                                  │
│        └─────────────┼─────────────┘                                  │
│                      ▼                                               │
│              Nginx 反向代理层                                         │
│        ┌─────────────────────────────┐                               │
│        │  负载均衡 / 缓存 / SSL终止  │                               │
│        └─────────────────────────────┘                               │
│                      │                                               │
│        ┌─────────────┼─────────────┐                                  │
│        │             │             │                                  │
│        ▼             ▼             ▼                                  │
│   ┌──────────┐ ┌──────────┐ ┌──────────┐                             │
│   │ 源站1    │ │ 源站2    │ │ 源站3    │                             │
│   │ (主)     │ │ (从)     │ │ (从)     │                             │
│   └──────────┘ └──────────┘ └──────────┘                             │
└─────────────────────────────────────────────────────────────────────────┘
```

### CDN 工作流程

```
用户请求 → CDN边缘节点 → 缓存命中? → 返回缓存内容
                          │
                          ↓ 未命中
                     反向代理 → 源站集群 → 返回内容 → 缓存 → 返回用户
```

### 组件说明

| 组件 | 职责 | 说明 |
|------|------|------|
| **CDN边缘节点** | 缓存静态资源，快速响应 | 分布式部署，降低延迟 |
| **Nginx反向代理** | 负载均衡、SSL终止、缓存 | 核心代理层 |
| **源站集群** | 提供原始内容 | 主从架构，高可用 |

## 快速使用

### CDN服务

```python
from app.services.cdn_service import cdn_service, CDNProvider

# 设置CDN提供商
cdn_service.set_provider(CDNProvider.ALIYUN)

# 添加源站服务器
cdn_service.add_origin_server({
    'id': 'origin-primary',
    'host': 'api.mtscos.com',
    'port': 80,
    'protocol': 'https',
    'weight': 3
})

# 提供资源服务
result = cdn_service.serve('/static/images/logo.png')
if result['status'] == 'hit':
    content = result['content']
    etag = result['etag']

# 清除缓存
cdn_service.purge_cache('/static/images/logo.png')  # 清除指定URL
cdn_service.purge_cache()  # 清除所有缓存

# 获取统计
stats = cdn_service.get_stats()
print(stats)
```

### 启动定期清理

```python
# 启动定期缓存清理（每24小时）
cdn_service.start_cache_cleanup(interval_hours=24)
```

## Nginx 配置详解

### 缓存配置

```nginx
# 缓存路径和大小
proxy_cache_path /var/cache/nginx/cdn_cache 
                 levels=1:2 
                 keys_zone=cdn_cache:100m 
                 max_size=10g 
                 inactive=7d 
                 use_temp_path=off;

# 缓存键
proxy_cache_key "$scheme$request_method$host$request_uri";

# 缓存有效期
proxy_cache_valid 200 302 12h;
proxy_cache_valid 404 1m;
```

### 静态资源缓存

```nginx
# 静态资源（30天缓存）
location ~* \.(jpg|jpeg|png|gif|css|js|woff|woff2)$ {
    proxy_cache cdn_cache;
    expires 30d;
    add_header Cache-Control "public, immutable";
    add_header X-Cache-Status $upstream_cache_status;
    proxy_pass http://cdn_origins;
}
```

### API路由（不缓存）

```nginx
location /api/ {
    proxy_pass http://mtscos_cluster;
    proxy_no_cache 1;
    proxy_cache_bypass 1;
}
```

## 缓存策略

### 缓存时间配置

| 文件类型 | 缓存时间 | 说明 |
|----------|----------|------|
| 图片 (jpg, png, webp) | 7天 | 可变性低 |
| 样式/脚本 (css, js) | 30天 | 带版本号 |
| 字体 (woff, ttf) | 30天 | 几乎不变 |
| HTML页面 | 5分钟 | 可变性高 |
| API响应 | 不缓存 | 动态内容 |

### ETag缓存验证

```python
# 生成ETag
def generate_etag(content: bytes) -> str:
    return hashlib.md5(content).hexdigest()

# 验证ETag
def validate_etag(resource, request_etag):
    if resource.etag == request_etag:
        return 304  # Not Modified
    return 200
```

## 反向代理配置

### 上游服务器

```nginx
upstream mtscos_cluster {
    ip_hash;  # 会话保持
    server mtscos-app-1:8888 weight=3;
    server mtscos-app-2:8888 weight=2;
    server mtscos-app-3:8888 weight=2;
    keepalive 64;
}
```

### 负载均衡策略

| 策略 | 配置 | 适用场景 |
|------|------|----------|
| **IP Hash** | `ip_hash;` | 需要会话保持 |
| **Round Robin** | 默认 | 通用场景 |
| **Least Conn** | `least_conn;` | 连接时间差异大 |
| **Weighted** | `weight=N;` | 服务器性能差异大 |

### 故障转移

```nginx
proxy_next_upstream error timeout invalid_header http_500 http_502 http_503 http_504;
proxy_next_upstream_tries 3;
```

## CDN 统计监控

### 获取统计

```python
stats = cdn_service.get_stats()
print(stats)
# {
#     'provider': 'aliyun',
#     'total_requests': 10000,
#     'hits': 8500,
#     'misses': 1500,
#     'hit_rate': 85.0,
#     'bytes_served': 104857600,  # 100MB
#     'origin_requests': 1500,
#     'cached_resources': 500,
#     'origin_servers': ['origin-primary', 'origin-secondary']
# }
```

### 监控指标

| 指标 | 说明 | 告警阈值 |
|------|------|----------|
| **Hit Rate** | 缓存命中率 | < 80% |
| **Origin Requests** | 源站请求数 | > 阈值 |
| **Bytes Served** | 服务字节数 | 监控趋势 |
| **Cached Resources** | 缓存资源数 | 容量管理 |

## SSL/TLS 配置

### 证书配置

```nginx
server {
    listen 443 ssl http2;
    
    ssl_certificate /etc/nginx/ssl/cert.pem;
    ssl_certificate_key /etc/nginx/ssl/key.pem;
    
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers HIGH:!aNULL:!MD5;
}
```

### HTTP/2 支持

```nginx
server {
    listen 443 ssl http2;
    # ...
}
```

## 性能优化

### Gzip压缩

```nginx
gzip on;
gzip_types text/plain text/css application/json application/javascript;
gzip_comp_level 6;
gzip_min_length 1024;
```

### 响应头优化

```nginx
add_header X-Frame-Options DENY;
add_header X-Content-Type-Options nosniff;
add_header Strict-Transport-Security "max-age=31536000";
proxy_hide_header X-Powered-By;
```

### 连接优化

```nginx
sendfile on;
tcp_nopush on;
tcp_nodelay on;
keepalive_timeout 65;
```

## 生产环境配置建议

### 多区域CDN部署

```
┌─────────────┐    ┌─────────────┐    ┌─────────────┐
│   北京节点   │    │   上海节点   │    │   广州节点   │
│  cdn-bj     │    │  cdn-sh     │    │  cdn-gz     │
└──────┬──────┘    └──────┬──────┘    └──────┬──────┘
       │                  │                  │
       └──────────────────┼──────────────────┘
                          ▼
                   负载均衡器
                          │
              ┌───────────┴───────────┐
              ▼                       ▼
         主源站集群              备源站集群
```

### 缓存预热

```python
def warmup_cdn():
    """预热CDN缓存"""
    hot_resources = [
        '/static/css/main.css',
        '/static/js/app.js',
        '/static/images/logo.png',
        '/static/images/banner.jpg'
    ]
    
    for resource in hot_resources:
        cdn_service.serve(resource)
    
    logger.info("CDN缓存预热完成")
```

### 灰度发布

```nginx
# 灰度发布配置
upstream gray_cluster {
    server mtscos-app-gray:8888 weight=1;
    server mtscos-app-1:8888 weight=9;
}

location / {
    # 根据Cookie决定是否走灰度
    if ($cookie_gray = "true") {
        proxy_pass http://gray_cluster;
    }
    proxy_pass http://mtscos_cluster;
}
```

## 故障处理

### 源站故障

```python
def handle_origin_failure(server_id):
    """处理源站故障"""
    # 标记源站为不可用
    cdn_service.remove_origin_server(server_id)
    
    # 清除相关缓存，强制回源
    cdn_service.purge_cache()
    
    logger.warning(f"源站 {server_id} 故障，已移除")
```

### 缓存击穿

```python
# 使用互斥锁防止缓存击穿
def get_with_mutex(key):
    value = cdn_service.get_resource(key)
    if value:
        return value
    
    with mutex:
        # 双重检查
        value = cdn_service.get_resource(key)
        if value:
            return value
        
        # 从源站获取
        result = cdn_service.serve(key)
        return result['content']
```

## 总结

CDN 和反向代理功能已完成，主要特性：

1. **CDN服务**: 静态资源缓存、ETag验证、缓存清理
2. **多提供商支持**: 本地、阿里云、腾讯云、Cloudflare、AWS
3. **反向代理**: 负载均衡、SSL终止、故障转移
4. **性能优化**: Gzip压缩、HTTP/2、连接优化
5. **监控统计**: 命中率、请求数、字节数

所有功能已完整实现，可以直接使用！
