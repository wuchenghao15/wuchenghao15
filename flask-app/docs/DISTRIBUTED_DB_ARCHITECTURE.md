# MTSCOS AI Project - 分布式数据库架构

## 概述

本项目已实现分库分表分布式数据库功能，支持多种分片策略和数据迁移。

## 架构设计

### 整体架构

```
┌──────────────────────────────────────────────────────────────────────┐
│                      应用层 (Application Layer)                    │
│   ┌──────────┐  ┌──────────┐  ┌──────────┐                       │
│   │  Node 1  │  │  Node 2  │  │  Node 3  │                       │
│   └────┬─────┘  └────┬─────┘  └────┬─────┘                       │
│        │             │             │                               │
├────────┼─────────────┼─────────────┼───────────────────────────────┤
│              分片路由层 (Shard Router)                             │
│                      │                                            │
│        ┌─────────────┴─────────────┐                              │
│        │                          │                              │
│        ▼                          ▼                              │
│   一致性哈希环                分片策略引擎                          │
│   (Consistent Hash)          (Shard Strategy)                    │
│        │                          │                              │
│        └─────────────┬─────────────┘                              │
│                      │                                            │
├──────────────────────┼─────────────────────────────────────────────┤
│                     分片节点层 (Shard Nodes)                       │
│   ┌────────────┐ ┌────────────┐ ┌────────────┐ ┌────────────┐    │
│   │ Shard 1    │ │ Shard 2    │ │ Shard 3    │ │ Shard 4    │    │
│   │ DB: mtscos │ │ DB: mtscos │ │ DB: mtscos │ │ DB: mtscos │    │
│   │ _db_1      │ │ _db_2      │ │ _db_3      │ │ _db_4      │    │
│   └────────────┘ └────────────┘ └────────────┘ └────────────┘    │
│        │             │             │             │                │
│        └─────────────┼─────────────┼─────────────┘                │
│                      ▼                                            │
│               数据存储层                                           │
└──────────────────────────────────────────────────────────────────────┘
```

### 分片策略

| 策略 | 说明 | 适用场景 | 示例 |
|------|------|----------|------|
| **HASH** | 哈希分片 | 均匀分布数据 | 用户ID哈希 |
| **RANGE** | 范围分片 | 按范围查询频繁 | 时间范围、ID范围 |
| **LIST** | 列表分片 | 固定映射关系 | 地区、类型映射 |
| **MODULO** | 取模分片 | 简单均匀分布 | 用户ID取模 |
| **CONSISTENT_HASH** | 一致性哈希 | 动态节点扩展 | 分布式缓存 |

### 分片类型

| 类型 | 说明 | 优点 | 缺点 |
|------|------|------|------|
| **库级分片** | 按数据库分片 | 隔离性好 | 跨库查询复杂 |
| **表级分片** | 按表分片 | 灵活度高 | 需要路由管理 |

## 快速使用

### 基础用法

```python
from app.services.distributed_db_service import distributed_db_service, ShardStrategy

# 注册分片表
distributed_db_service.register_table(
    table_name='users',
    shard_key='user_id',
    strategy=ShardStrategy.HASH
)

# 在分片上执行查询
result = distributed_db_service.execute_on_shard(
    table_name='users',
    shard_value='user123',
    query='SELECT * FROM users WHERE user_id = ?',
    params=('user123',)
)

# 跨分片查询
results = distributed_db_service.execute_across_shards(
    table_name='users',
    query='SELECT COUNT(*) FROM users',
    shard_values=['user1', 'user2', 'user3']
)

# 跨分片事务
operations = [
    {'table': 'orders', 'shard_value': 'order1', 'query': 'INSERT INTO orders (...)', 'params': (...)},
    {'table': 'users', 'shard_value': 'user1', 'query': 'UPDATE users SET balance = balance - ?', 'params': (100,)}
]
success = distributed_db_service.execute_transaction_across_shards(operations)
```

### 添加分片节点

```python
# 添加分片节点
success = distributed_db_service.add_node({
    'id': 'shard-node-5',
    'host': 'postgres-shard-5',
    'port': 5432,
    'database': 'mtscos_db_5',
    'username': 'admin',
    'password': 'password',
    'weight': 2  # 权重越高，分配的数据越多
})

# 移除分片节点
success = distributed_db_service.remove_node('shard-node-5')
```

### 数据迁移

```python
# 迁移分片数据
success = distributed_db_service.migrate_shard(
    source_node_id='shard-node-1',
    target_node_id='shard-node-5',
    table_name='users'
)
```

### 获取统计信息

```python
stats = distributed_db_service.get_stats()
print(stats)
```

## 分片策略详解

### 哈希分片 (HASH)

```python
# 注册哈希分片表
distributed_db_service.register_table(
    table_name='orders',
    shard_key='order_id',
    strategy=ShardStrategy.HASH
)

# 数据会根据 order_id 的哈希值均匀分布到各个节点
```

### 范围分片 (RANGE)

```python
# 注册范围分片表，需要配置范围映射
distributed_db_service.register_table(
    table_name='logs',
    shard_key='created_at',
    strategy=ShardStrategy.RANGE,
    nodes=['shard-node-1', 'shard-node-2', 'shard-node-3', 'shard-node-4']
)

# 配置范围（在metadata中）
table = distributed_db_service._tables['logs']
table.metadata['ranges'] = [
    ('shard-node-1', 0, 99),
    ('shard-node-2', 100, 199),
    ('shard-node-3', 200, 299),
    ('shard-node-4', 300, 399)
]
```

### 列表分片 (LIST)

```python
# 注册列表分片表
distributed_db_service.register_table(
    table_name='products',
    shard_key='category',
    strategy=ShardStrategy.LIST
)

# 配置映射关系
table = distributed_db_service._tables['products']
table.metadata['mapping'] = {
    'electronics': 'shard-node-1',
    'clothing': 'shard-node-2',
    'books': 'shard-node-3',
    'food': 'shard-node-4'
}
```

### 取模分片 (MODULO)

```python
# 注册取模分片表
distributed_db_service.register_table(
    table_name='transactions',
    shard_key='transaction_id',
    strategy=ShardStrategy.MODULO
)

# 数据会根据 transaction_id % node_count 分配到对应节点
```

### 一致性哈希 (CONSISTENT_HASH)

```python
# 注册一致性哈希分片表
distributed_db_service.register_table(
    table_name='cache_items',
    shard_key='cache_key',
    strategy=ShardStrategy.CONSISTENT_HASH
)

# 支持动态添加/移除节点，数据迁移量最小
```

## 两阶段提交 (2PC)

### 跨分片事务流程

```
阶段1: 准备阶段 (Prepare)
    │
    ├─ 向所有涉及的分片节点发送准备请求
    ├─ 每个节点执行事务但不提交
    ├─ 如果所有节点都成功，返回准备成功
    └─ 如果有任何节点失败，返回准备失败

阶段2: 提交阶段 (Commit)
    │
    ├─ 如果准备成功，向所有节点发送提交请求
    ├─ 所有节点提交事务
    └─ 返回事务成功

阶段3: 回滚阶段 (Rollback)
    │
    ├─ 如果准备失败，向所有节点发送回滚请求
    ├─ 所有节点回滚事务
    └─ 返回事务失败
```

### 使用示例

```python
# 跨分片转账事务
operations = [
    {
        'table': 'accounts',
        'shard_value': 'user1',
        'query': 'UPDATE accounts SET balance = balance - ? WHERE user_id = ?',
        'params': (100, 'user1')
    },
    {
        'table': 'accounts',
        'shard_value': 'user2',
        'query': 'UPDATE accounts SET balance = balance + ? WHERE user_id = ?',
        'params': (100, 'user2')
    }
]

success = distributed_db_service.execute_transaction_across_shards(operations)
```

## 一致性哈希环

### 工作原理

```python
# 一致性哈希环实现
hash_ring = ConsistentHashRing(replicas=100)

# 添加节点（每个节点有100个虚拟节点）
hash_ring.add_node('shard-node-1', weight=1)
hash_ring.add_node('shard-node-2', weight=2)  # 权重为2，虚拟节点数量翻倍

# 获取键对应的节点
node_id = hash_ring.get_node('user123')
```

### 节点添加/移除

```python
# 添加节点 - 只有少量数据需要迁移
hash_ring.add_node('shard-node-5')

# 移除节点 - 只有该节点的数据需要迁移到其他节点
hash_ring.remove_node('shard-node-1')
```

## 配置建议

### 环境变量配置

```bash
# .env 文件
SHARD_NODE_COUNT=4
SHARD_STRATEGY=hash
DB_USER=admin
DB_PASSWORD=password
```

### 生产环境配置

```python
# 增加分片节点数量
for i in range(8):
    distributed_db_service.add_node({
        'id': f'shard-node-{i+1}',
        'host': f'postgres-shard-{i+1}',
        'weight': 1
    })

# 注册分片表
distributed_db_service.register_table('users', 'user_id', ShardStrategy.HASH)
distributed_db_service.register_table('orders', 'order_id', ShardStrategy.HASH)
distributed_db_service.register_table('logs', 'created_at', ShardStrategy.RANGE)
distributed_db_service.register_table('products', 'category', ShardStrategy.LIST)
```

## 最佳实践

### 1. 选择合适的分片键

```python
# ✅ 推荐：使用查询频繁的字段
distributed_db_service.register_table('orders', 'user_id', ShardStrategy.HASH)

# ❌ 不推荐：使用查询不频繁的字段
distributed_db_service.register_table('orders', 'order_status', ShardStrategy.HASH)
```

### 2. 避免跨分片查询

```python
# ✅ 推荐：根据分片键查询
result = distributed_db_service.execute_on_shard(
    'orders', 'user123',
    'SELECT * FROM orders WHERE user_id = ?',
    ('user123',)
)

# ❌ 不推荐：跨分片全表扫描
results = distributed_db_service.execute_across_shards(
    'orders', 'SELECT * FROM orders'
)
```

### 3. 数据预热

```python
def warmup_shards():
    """预热分片数据"""
    # 预先创建表结构
    for node_id in distributed_db_service._nodes.keys():
        create_table_query = """
            CREATE TABLE IF NOT EXISTS users (
                user_id VARCHAR(64) PRIMARY KEY,
                username VARCHAR(100),
                email VARCHAR(255)
            )
        """
        # 在每个节点上执行
```

### 4. 监控分片状态

```python
def monitor_shards():
    """监控分片状态"""
    stats = distributed_db_service.get_stats()
    
    for node in stats['nodes']:
        if node['status'] != 'active':
            logger.warning(f"分片节点 {node['id']} 状态异常")
```

## 故障处理

### 节点故障

```python
# 自动检测故障节点
def handle_node_failure(node_id):
    """处理节点故障"""
    # 1. 将节点标记为不可用
    node = distributed_db_service._nodes.get(node_id)
    if node:
        node.status = 'down'
    
    # 2. 迁移数据到其他节点
    for table_name in distributed_db_service._tables.keys():
        distributed_db_service.migrate_shard(
            source_node_id=node_id,
            target_node_id='shard-node-backup',
            table_name=table_name
        )
    
    # 3. 从哈希环移除节点
    distributed_db_service.remove_node(node_id)
```

### 数据一致性

```python
def check_data_consistency():
    """检查数据一致性"""
    # 比较各个分片的数据
    inconsistencies = []
    
    for table_name in distributed_db_service._tables.keys():
        # 检查每个分片的数据完整性
        pass
    
    return inconsistencies
```

## 性能优化

### 1. 分片数量选择

```python
# 根据数据量选择分片数量
data_size_gb = 1000  # 1TB数据
shard_count = min(data_size_gb // 100, 32)  # 每100GB一个分片，最多32个
distributed_db_service.set_shard_count(shard_count)
```

### 2. 查询优化

```python
# 使用分片键作为查询条件
@read_only
def get_user_orders(user_id):
    return distributed_db_service.execute_on_shard(
        'orders', user_id,
        'SELECT * FROM orders WHERE user_id = ?',
        (user_id,)
    )
```

### 3. 批量操作

```python
# 批量插入到同一分片
def batch_insert_users(users):
    # 按分片键分组
    users_by_shard = {}
    for user in users:
        shard_value = user['user_id']
        if shard_value not in users_by_shard:
            users_by_shard[shard_value] = []
        users_by_shard[shard_value].append(user)
    
    # 批量插入到各个分片
    for shard_value, users_in_shard in users_by_shard.items():
        # 执行批量插入
        pass
```

## 总结

分布式数据库服务已完成，主要特性：

1. **多种分片策略**: 哈希、范围、列表、取模、一致性哈希
2. **一致性哈希环**: 支持动态节点扩展，最小数据迁移
3. **两阶段提交**: 跨分片事务支持
4. **数据迁移**: 支持分片数据迁移
5. **分片管理**: 动态添加/移除分片节点

所有功能已完整实现，可以直接使用！
