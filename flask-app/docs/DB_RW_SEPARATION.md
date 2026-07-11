# MTSCOS AI Project - 数据库读写分离架构

## 概述

本项目已实现数据库读写分离功能，支持主从复制、负载均衡和自动故障转移。

## 架构设计

### 整体架构

```
┌─────────────────────────────────────────────────────────────────┐
│                      应用层 (Application Layer)               │
│   ┌──────────┐  ┌──────────┐  ┌──────────┐                  │
│   │  Node 1  │  │  Node 2  │  │  Node 3  │                  │
│   └────┬─────┘  └────┬─────┘  └────┬─────┘                  │
│        │             │             │                          │
├────────┼─────────────┼─────────────┼──────────────────────────┤
│                读写分离路由层 (Router Layer)                   │
│                      │                                       │
│        ┌─────────────┴─────────────┐                         │
│        │                          │                         │
│        ▼                          ▼                         │
│   ┌───────────┐          ┌─────────────────┐                │
│   │   主库    │          │     从库集群    │                │
│   │  Master  │◄───────► │   Slaves       │                │
│   │ (写操作) │  复制    │ (读操作负载均衡) │                │
│   └───────────┘          └───────┬─────────┘                │
│                                  │                          │
│                    ┌─────────────┼─────────────┐            │
│                    ▼             ▼             ▼            │
│              ┌──────────┐ ┌──────────┐ ┌──────────┐         │
│              │ Slave 1  │ │ Slave 2  │ │ Slave 3  │         │
│              └──────────┘ └──────────┘ └──────────┘         │
└─────────────────────────────────────────────────────────────────┘
```

### 读写分离流程图

```
用户请求
    │
    ├─ 读操作 ──► 从库选择策略 ──► 执行查询 ──► 返回结果
    │                    │
    │                    ├─ Round Robin
    │                    ├─ Least Connections
    │                    └─ Weighted Round Robin
    │
    └─ 写操作 ──► 主库 ──► 执行写入 ──► 主从复制 ──► 返回结果
```

### 组件说明

| 组件 | 职责 | 说明 |
|------|------|------|
| **读写路由器** | 路由读写操作到正确的数据库 | 自动判断SQL类型或使用装饰器 |
| **主库** | 处理所有写操作 | 支持事务、索引更新 |
| **从库集群** | 处理读操作 | 支持负载均衡、故障转移 |
| **主从复制** | 同步主库数据到从库 | PostgreSQL流复制 |
| **健康检查** | 监控数据库状态 | 自动剔除故障节点 |

## 快速使用

### 基础用法

```python
from app.services.database_rw_service import database_rw_service

# 执行读操作（自动路由到从库）
result = database_rw_service.execute_read(
    "SELECT * FROM users WHERE status = ?",
    ('active',)
)

# 执行写操作（路由到主库）
result = database_rw_service.execute_write(
    "INSERT INTO users (username, email) VALUES (?, ?)",
    ('john', 'john@example.com')
)

# 执行事务
operations = [
    {'query': "UPDATE accounts SET balance = balance - ? WHERE id = ?", 'params': (100, 1)},
    {'query': "UPDATE accounts SET balance = balance + ? WHERE id = ?", 'params': (100, 2)}
]
success = database_rw_service.transaction(operations)
```

### 使用装饰器

```python
from app.utils.db_rw_decorator import read_only, write_only, transactional

# 只读操作
@read_only
def get_user(user_id):
    return db.query(User).filter_by(id=user_id).first()

# 只写操作
@write_only  
def create_user(data):
    user = User(**data)
    db.session.add(user)
    db.session.commit()
    return user

# 事务操作
@transactional
def transfer_funds(from_id, to_id, amount):
    from_account = db.query(Account).get(from_id)
    to_account = db.query(Account).get(to_id)
    from_account.balance -= amount
    to_account.balance += amount
```

### 添加从库

```python
# 添加从库
success = database_rw_service.add_slave({
    'id': 'slave-4',
    'host': 'postgres-slave-4',
    'port': 5432,
    'database': 'mtscos_db',
    'username': 'admin',
    'password': 'password',
    'weight': 2
})

# 移除从库
success = database_rw_service.remove_slave('slave-4')
```

### 设置负载均衡策略

```python
from app.services.database_rw_service import database_rw_service, LoadBalanceStrategy

# 设置轮询策略（默认）
database_rw_service.set_load_balance_strategy(LoadBalanceStrategy.ROUND_ROBIN)

# 设置最小连接数策略
database_rw_service.set_load_balance_strategy(LoadBalanceStrategy.LEAST_CONNECTIONS)

# 设置加权轮询策略
database_rw_service.set_load_balance_strategy(LoadBalanceStrategy.WEIGHTED_ROUND_ROBIN)
```

## 负载均衡策略

### 支持的策略

| 策略 | 说明 | 适用场景 |
|------|------|----------|
| **Round Robin** | 轮询分配 | 从库性能相近 |
| **Least Connections** | 最少连接优先 | 连接时间差异大 |
| **Weighted Round Robin** | 加权轮询 | 从库性能差异大 |

### 策略选择建议

```python
# 根据场景选择策略
if slave_performance_varies:
    database_rw_service.set_load_balance_strategy(LoadBalanceStrategy.WEIGHTED_ROUND_ROBIN)
elif connection_time_varies:
    database_rw_service.set_load_balance_strategy(LoadBalanceStrategy.LEAST_CONNECTIONS)
else:
    database_rw_service.set_load_balance_strategy(LoadBalanceStrategy.ROUND_ROBIN)
```

## 健康检查

### 自动健康检查

```python
# 启动健康检查（每30秒检查一次）
database_rw_service.start_health_check()

# 停止健康检查
database_rw_service.stop_health_check()
```

### 手动检查

```python
# 获取数据库状态
stats = database_rw_service.get_stats()
print(stats)
```

## 主从复制配置

### PostgreSQL主从复制

```bash
# 主库配置 (postgresql.conf)
listen_addresses = '*'
wal_level = replica
max_wal_senders = 10
wal_keep_size = 1GB

# 从库配置 (recovery.conf)
standby_mode = 'on'
primary_conninfo = 'host=postgres port=5432 user=replica password=password'
restore_command = 'cp /var/lib/postgresql/15/main/wal/%f "%p"'
```

### Docker Compose配置

```yaml
# docker-compose.cluster.yml 添加从库
postgres-slave-1:
  image: postgres:15-alpine
  environment:
    - POSTGRES_DB=mtscos_db
    - POSTGRES_USER=admin
    - POSTGRES_PASSWORD=password
    - POSTGRES_REPLICATION_MODE=slave
    - POSTGRES_MASTER_HOST=postgres
  volumes:
    - ./postgres-slave-1-data:/var/lib/postgresql/data
```

## 配置建议

### 环境变量配置

```bash
# .env 文件
DB_MASTER_HOST=postgres
DB_MASTER_PORT=5432
DB_NAME=mtscos_db
DB_USER=admin
DB_PASSWORD=password
DB_SLAVE_COUNT=3
```

### 生产环境配置

```python
# 增加从库数量
for i in range(5):
    database_rw_service.add_slave({
        'id': f'slave-{i+1}',
        'host': f'postgres-slave-{i+1}',
        'weight': 1 if i < 3 else 2  # 高性能从库权重更高
    })

# 设置最小连接数策略
database_rw_service.set_load_balance_strategy(LoadBalanceStrategy.LEAST_CONNECTIONS)

# 启动健康检查
database_rw_service.start_health_check()
```

## 最佳实践

### 1. 区分读写操作

```python
# ✅ 推荐：使用装饰器明确标识
@read_only
def get_user_list():
    return db.query(User).all()

@write_only
def update_user(user_id, data):
    user = db.query(User).get(user_id)
    for key, value in data.items():
        setattr(user, key, value)
    db.session.commit()
```

### 2. 处理读写一致性

```python
# 写入后立即读取可能需要从主库读取
def create_and_get_user(data):
    # 写入主库
    user = create_user(data)
    
    # 如果需要立即获取最新数据，从主库读取
    return get_user_from_master(user.id)
```

### 3. 批量操作优化

```python
# 批量写入使用事务
@transactional
def batch_create_users(users_data):
    for data in users_data:
        user = User(**data)
        db.session.add(user)
```

### 4. 监控从库延迟

```python
def check_replication_delay():
    """检查主从复制延迟"""
    stats = database_rw_service.get_stats()
    for slave in stats['slaves']:
        # 检查复制延迟
        delay = get_replication_delay(slave['host'])
        if delay > 60:  # 超过60秒
            logger.warning(f"从库 {slave['id']} 复制延迟过高: {delay}秒")
```

## 故障处理

### 从库故障

```python
# 自动故障转移
# 当从库不可用时，自动从活跃列表中移除
# 所有读操作路由到其他健康的从库或主库

# 获取可用从库
slave = database_rw_service.select_slave()
if not slave:
    # 降级到主库
    logger.warning("没有可用的从库，使用主库")
```

### 主库故障

```python
# 主库故障需要手动或自动提升从库为主库
def failover_to_slave(slave_id):
    """故障转移到从库"""
    # 提升从库为主库
    database_rw_service.promote_to_master(slave_id)
    
    # 更新其他从库指向新主库
    update_slave_replication()
```

### 数据一致性保障

```python
# 使用事务保证数据一致性
@transactional
def critical_operation():
    # 多个操作在同一事务中
    operation_a()
    operation_b()
    # 如果任何操作失败，自动回滚
```

## 性能优化

### 1. 读写比例控制

```python
# 根据读写比例调整从库数量
read_write_ratio = get_read_write_ratio()  # 例如 8:2

# 从库数量建议 = 读比例 / 写比例
slave_count = int(read_write_ratio * 2)
```

### 2. 连接池配置

```python
# app/config.py
SQLALCHEMY_ENGINE_OPTIONS = {
    'pool_size': 20,           # 连接池大小
    'max_overflow': 50,        # 最大溢出连接
    'pool_timeout': 30,        # 连接超时
    'pool_recycle': 1800       # 连接回收时间
}
```

### 3. 查询优化

```python
# 使用索引优化读操作
@read_only
def get_users_by_status(status):
    # 确保 status 字段有索引
    return db.query(User).filter_by(status=status).all()
```

## 监控与告警

### 监控指标

| 指标 | 说明 | 告警阈值 |
|------|------|----------|
| 主库连接数 | 当前主库连接数 | > 80% of max_connections |
| 从库连接数 | 当前从库连接数 | > 80% of max_connections |
| 复制延迟 | 从库与主库的延迟 | > 60秒 |
| 从库健康状态 | 从库是否健康 | 不健康数量 > 0 |

### 告警示例

```python
def monitor_databases():
    stats = database_rw_service.get_stats()
    
    # 检查从库健康状态
    unhealthy_slaves = sum(1 for s in stats['slaves'] if s['status'] != 'healthy')
    if unhealthy_slaves > 0:
        send_alert(f"有 {unhealthy_slaves} 个从库不健康")
    
    # 检查连接数
    if stats['total_connections'] > 100:
        send_alert("数据库连接数过高")
```

## 总结

数据库读写分离已完成，主要特性：

1. **主从架构**: 主库写，从库读
2. **负载均衡**: 支持轮询、最小连接数、加权轮询
3. **健康检查**: 自动检测故障节点
4. **故障转移**: 自动降级到主库
5. **事务支持**: 主库事务保证一致性
6. **装饰器支持**: 简化读写操作标识

所有功能已完整实现，可以直接使用！
