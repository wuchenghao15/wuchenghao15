# MTSCOS AI Project - 多级缓存架构

## 概述

本项目已实现多级缓存系统，包含L1内存缓存、L2 Redis缓存和L3文件缓存，支持自动缓存提升和多种缓存策略。

## 缓存架构

### 多级缓存层次

```
┌─────────────────────────────────────────────────────────────────┐
│                        L1 - 内存缓存                            │
│   容量: 1024项  | 速度: 最快(微秒级) | TTL: 3600秒           │
│   策略: LRU/LFU/FIFO                                           │
├─────────────────────────────────────────────────────────────────┤
│                        L2 - Redis缓存                           │
│   容量: 较大    | 速度: 较快(毫秒级) | TTL: 3600秒           │
│   共享缓存，支持集群                                            │
├─────────────────────────────────────────────────────────────────┤
│                        L3 - 文件缓存                            │
│   容量: 超大    | 速度: 较慢(毫秒级) | TTL: 86400秒          │
│   持久化存储，适合大数据                                        │
├─────────────────────────────────────────────────────────────────┤
│                        数据库层                                 │
│   容量: 无限    | 速度: 最慢(毫秒/秒级)                        │
└─────────────────────────────────────────────────────────────────┘
```

### 缓存级别对比

| 级别 | 类型 | 容量 | 速度 | TTL | 持久性 | 适用场景 |
|------|------|------|------|-----|--------|----------|
| **L1** | 内存 | 小(1024项) | 最快(μs) | 1小时 | 无 | 高频访问、热点数据 |
| **L2** | Redis | 较大 | 较快(ms) | 1小时 | 有 | 共享缓存、会话数据 |
| **L3** | 文件 | 超大 | 较慢(ms) | 24小时 | 有 | 大数据缓存、冷数据 |

### 缓存策略

| 策略 | 说明 | 适用场景 |
|------|------|----------|
| **LRU** | 最近最少使用 | 通用场景 |
| **LFU** | 最不经常使用 | 访问频率差异大 |
| **FIFO** | 先进先出 | 顺序访问场景 |
| **TTL** | 时间过期 | 时效性数据 |

## 快速使用

### 基础用法

```python
from app.services.cache_service import cache_service

# 设置缓存
cache_service.set('user:123', {'name': '张三', 'email': 'zhangsan@example.com'})

# 获取缓存
user = cache_service.get('user:123')

# 删除缓存
cache_service.delete('user:123')

# 获取统计
stats = cache_service.get_stats()
```

### 使用装饰器

```python
from app.utils.cache_decorator import cached, l1_cached, l2_cached

# 基础缓存装饰器
@cached(key_prefix='user_data', ttl=3600)
def get_user_data(user_id):
    # 从数据库查询
    return db.query(User).filter_by(id=user_id).first()

# 仅使用L1缓存
@l1_cached(key_prefix='config', ttl=600)
def get_config():
    return db.query(Config).all()

# 仅使用L2缓存
@l2_cached(key_prefix='session', ttl=1800)
def get_session(session_id):
    return redis.get(session_id)
```

### 设置缓存策略

```python
from app.services.cache_service import cache_service, CacheStrategy

# 设置为LFU策略
cache_service.set_strategy(CacheStrategy.LFU)

# 设置为LRU策略（默认）
cache_service.set_strategy(CacheStrategy.LRU)
```

### 缓存预热

```python
# 预热缓存
warmup_data = {
    'config:default': get_default_config(),
    'stats:daily': get_daily_stats(),
    'users:active': get_active_users()
}
cache_service.warmup(warmup_data)
```

### 定期清理

```python
# 启动定期清理（每24小时）
cache_service.start_periodic_cleanup(interval_hours=24)
```

## 缓存工作流程

### 读取流程

```
用户请求 → L1缓存? → 命中返回
       ↓ 未命中
    L2缓存? → 命中返回 + 提升到L1
       ↓ 未命中
    L3缓存? → 命中返回 + 提升到L1/L2
       ↓ 未命中
    数据库查询 → 设置L1/L2缓存 → 返回
```

### 写入流程

```
数据更新 → 删除L1/L2/L3缓存
       ↓
    写入数据库
       ↓
    可选：预热缓存
```

### 缓存提升机制

当从低级缓存命中数据时，自动提升到高级缓存：

```
L3命中 → L2缓存 + L1缓存
L2命中 → L1缓存
L1命中 → 保持不变
```

## 最佳实践

### 1. 选择合适的缓存级别

```python
# 高频访问数据 - 使用L1/L2
@cached(key_prefix='hot_data', ttl=3600)
def get_hot_data():
    pass

# 中等频率数据 - 使用L2
@l2_cached(key_prefix='medium_data', ttl=3600)
def get_medium_data():
    pass

# 低频访问/大数据 - 使用L3
@l3_cached(key_prefix='large_data', ttl=86400)
def get_large_data():
    pass
```

### 2. 设置合理的TTL

```python
# 实时数据 - 短TTL
@cached(key_prefix='realtime', ttl=60)
def get_realtime_data():
    pass

# 静态数据 - 长TTL
@cached(key_prefix='static', ttl=86400)
def get_static_data():
    pass
```

### 3. 使用缓存键命名规范

```python
# 推荐的键命名格式
user:123                    # 用户数据
session:abc123              # 会话数据
config:default              # 配置数据
stats:daily:20240101        # 日期相关数据
api:users:page:1:size:20    # API响应缓存
```

### 4. 缓存失效策略

```python
def update_user(user_id, data):
    # 更新数据库
    db.session.update(data)
    db.session.commit()
    
    # 失效相关缓存
    cache_service.delete(f'user:{user_id}')
    cache_service.delete('users:active')
```

### 5. 异步缓存更新

```python
import threading

def async_update_cache(key, data):
    """异步更新缓存"""
    def update():
        cache_service.set(key, data)
    threading.Thread(target=update, daemon=True).start()
```

## 缓存统计

### 获取统计信息

```python
stats = cache_service.get_stats()
print(stats)
```

### 统计字段说明

```python
{
    'strategy': 'lru',              # 当前缓存策略
    'hits': {
        'l1': 1000,                 # L1命中次数
        'l2': 500,                  # L2命中次数
        'l3': 100                   # L3命中次数
    },
    'misses': {
        'l1': 200,                  # L1未命中次数
        'l2': 300,                  # L2未命中次数
        'l3': 50                    # L3未命中次数
    },
    'sets': 1500,                   # 设置缓存次数
    'deletes': 200,                 # 删除缓存次数
    'evictions': 50,                # 缓存驱逐次数
    'total_requests': 2150,         # 总请求次数
    'hit_rate': 83.72,              # 命中率(%)
    'sizes': {
        'l1': 512,                  # L1缓存大小
        'l2': 10000,                # L2缓存大小
        'l3': 50000                 # L3缓存大小
    }
}
```

## 性能优化建议

### 1. 热点数据预热

```python
def on_app_start():
    """应用启动时预热缓存"""
    hot_keys = [
        'config:default',
        'stats:overview',
        'users:popular'
    ]
    
    warmup_data = {}
    for key in hot_keys:
        warmup_data[key] = fetch_data_from_db(key)
    
    cache_service.warmup(warmup_data)
```

### 2. 批量操作

```python
# 批量设置缓存
def batch_set(items):
    for key, value in items.items():
        cache_service.set(key, value)

# 批量获取缓存
def batch_get(keys):
    results = {}
    for key in keys:
        results[key] = cache_service.get(key)
    return results
```

### 3. 使用压缩（对于大数据）

```python
import gzip
import base64

def compress_data(data):
    """压缩数据"""
    json_str = json.dumps(data)
    compressed = gzip.compress(json_str.encode())
    return base64.b64encode(compressed).decode()

def decompress_data(compressed_str):
    """解压数据"""
    compressed = base64.b64decode(compressed_str)
    json_str = gzip.decompress(compressed).decode()
    return json.loads(json_str)
```

### 4. 监控缓存命中率

```python
def check_cache_efficiency():
    """检查缓存效率"""
    stats = cache_service.get_stats()
    
    if stats['hit_rate'] < 80:
        logger.warning(f"缓存命中率较低: {stats['hit_rate']}%")
        # 可以触发缓存策略调整或预热
    
    return stats['hit_rate']
```

## 缓存一致性

### 写穿透策略

```python
def write_through(key, value):
    """写穿透：同时写入缓存和数据库"""
    cache_service.set(key, value)
    db.insert(value)
```

### 写回策略（异步）

```python
def write_back(key, value):
    """写回：先写缓存，异步写数据库"""
    cache_service.set(key, value)
    schedule_db_write(key, value)
```

### 缓存失效策略

```python
def invalidate_on_update(entity_type, entity_id):
    """数据更新时失效相关缓存"""
    pattern = f"{entity_type}:{entity_id}"
    cache_service.delete(pattern)
    
    # 失效相关缓存
    related_keys = [
        f"{entity_type}:list",
        f"{entity_type}:{entity_id}:detail"
    ]
    for key in related_keys:
        cache_service.delete(key)
```

## 故障处理

### 降级策略

```python
def get_data_with_fallback(key, fallback_func):
    """带降级的缓存获取"""
    try:
        value = cache_service.get(key)
        if value is not None:
            return value
    except Exception as e:
        logger.warning(f"缓存获取失败: {str(e)}")
    
    # 降级到数据库
    return fallback_func()
```

### 缓存雪崩应对

```python
# 随机TTL避免同时过期
import random

def set_with_random_ttl(key, value, base_ttl=3600):
    """设置带随机TTL的缓存"""
    ttl = base_ttl + random.randint(0, 300)  # 添加0-5分钟随机偏移
    cache_service.set(key, value, ttl)
```

### 缓存击穿应对

```python
from threading import Lock

def get_with_mutex(key, fetch_func, ttl=3600):
    """带互斥锁的缓存获取，防止击穿"""
    value = cache_service.get(key)
    if value is not None:
        return value
    
    # 获取锁
    with Lock():
        # 双重检查
        value = cache_service.get(key)
        if value is not None:
            return value
        
        # 获取数据
        value = fetch_func()
        cache_service.set(key, value, ttl)
    
    return value
```

## 配置建议

### 环境变量配置

```bash
# .env 文件
REDIS_HOST=redis
REDIS_PORT=6379
CACHE_L1_SIZE=1024
CACHE_L1_TTL=3600
CACHE_L2_TTL=3600
CACHE_L3_TTL=86400
```

### 生产环境配置

```python
# 生产环境：更大的缓存容量
cache_service._l1_cache = LRUCache(max_size=4096)

# 调整清理间隔
cache_service.start_periodic_cleanup(interval_hours=12)
```

## 总结

多级缓存系统已完成，主要特性：

1. **三级缓存**: L1(内存) → L2(Redis) → L3(文件)
2. **自动提升**: 低级缓存命中自动提升到高级缓存
3. **多种策略**: LRU、LFU、FIFO、TTL
4. **缓存装饰器**: 简化缓存使用
5. **缓存预热**: 支持启动时预热
6. **统计监控**: 完整的命中率统计
7. **故障降级**: 支持缓存失效时降级

所有功能已完整实现，可以直接使用！
