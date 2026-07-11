# MTSCOS AI Project - 搜索引擎和 NoSQL 架构

## 概述

本项目已实现全文搜索引擎和 NoSQL 数据库功能，支持倒排索引、BM25 评分、键值存储、文档存储等。

## 架构设计

### 整体架构

```
┌──────────────────────────────────────────────────────────────────────┐
│                        应用层 (Application)                         │
├──────────────────────────────────────────────────────────────────────┤
│              ┌──────────────────┐  ┌──────────────────┐            │
│              │  Search Engine   │  │    NoSQL DB      │            │
│              │  (全文搜索)      │  │  (键值/文档)     │            │
│              └────────┬─────────┘  └────────┬─────────┘            │
│                       │                      │                     │
│                       ▼                      ▼                     │
│              ┌──────────────────┐  ┌──────────────────┐            │
│              │  倒排索引        │  │  KV存储/集合     │            │
│              │  (Inverted Index)│  │  (Memory Store)  │            │
│              └──────────────────┘  └──────────────────┘            │
├──────────────────────────────────────────────────────────────────────┤
│                         持久化层                                    │
│              ┌──────────────────────────────────────────┐          │
│              │         JSON 文件 / Redis               │          │
│              └──────────────────────────────────────────┘          │
└──────────────────────────────────────────────────────────────────────┘
```

## 搜索引擎

### 倒排索引结构

```python
# 倒排索引示例
index = {
    'python': [('doc1', 3), ('doc2', 1), ('doc3', 5)],  # (文档ID, 词频)
    '编程': [('doc1', 2), ('doc4', 4)],
    '教程': [('doc2', 1), ('doc3', 2)]
}
```

### BM25 评分算法

```
BM25 = Σ [IDF(q_i) * (TF(q_i,d) * (k1 + 1)) / (TF(q_i,d) + k1 * (1 - b + b * |d|/avgdl))]

其中：
- IDF(q_i) = log(N / (df(q_i) + 0.5))
- TF(q_i,d) = 词频
- k1 = 1.5 (调节因子)
- b = 0.75 (文档长度影响)
- |d| = 文档长度
- avgdl = 平均文档长度
```

### 快速使用

```python
from app.services.search_engine_service import search_engine_service

# 索引文档
search_engine_service.index_document(
    doc_id='doc1',
    title='Python编程教程',
    content='Python是一种高级编程语言，非常适合初学者学习编程。',
    metadata={'category': '技术', 'author': '张三'}
)

# 搜索文档
results = search_engine_service.search('Python编程', limit=10)
for result in results:
    print(f"{result.title} - 分数: {result.score}")
    print(f"摘要: {result.content}")
    if result.highlight:
        print(f"高亮: {result.highlight}")

# 带过滤条件的搜索
filtered_results = search_engine_service.search_with_filters(
    query='编程',
    filters={'category': '技术'},
    limit=5
)

# 获取文档
doc = search_engine_service.get_document('doc1')

# 更新文档
search_engine_service.update_document(
    doc_id='doc1',
    content='更新后的内容...'
)

# 删除文档
search_engine_service.delete_document('doc1')

# 保存/加载索引
search_engine_service.save_index()
search_engine_service.load_index()

# 获取统计
stats = search_engine_service.get_stats()
```

### 搜索结果示例

```python
# 搜索结果结构
SearchResult(
    doc_id='doc1',
    title='Python编程教程',
    content='Python是一种高级编程语言...',
    score=2.3456,
    highlight='...<em>Python</em>是一种高级<em>编程</em>语言...',
    metadata={'category': '技术', 'author': '张三'}
)
```

## NoSQL 数据库

### 支持的数据结构

| 数据结构 | 说明 | 操作示例 |
|----------|------|----------|
| **String** | 字符串值 | set/get/delete |
| **Hash** | 哈希表 | hset/hget/hgetall |
| **List** | 列表 | lpush/rpush/lpop/rpop |
| **Set** | 无序集合 | sadd/smembers/srem |
| **ZSet** | 有序集合 | zadd/zrange/zrank |
| **Document** | 文档集合 | insert/find/update/delete |

### 快速使用

```python
from app.services.nosql_service import nosql_service

# 键值操作
nosql_service.set('user:123', {'name': '张三', 'age': 25}, ttl=3600)
user = nosql_service.get('user:123')
nosql_service.delete('user:123')

# 计数器
nosql_service.incr('page:views', 1)
count = nosql_service.get('page:views')

# 哈希操作
nosql_service.hset('user:123', 'name', '张三')
name = nosql_service.hget('user:123', 'name')
user_data = nosql_service.hgetall('user:123')

# 列表操作（队列）
nosql_service.rpush('queue:tasks', 'task1', 'task2', 'task3')
task = nosql_service.lpop('queue:tasks')

# 集合操作
nosql_service.sadd('users:active', 'user1', 'user2', 'user3')
active_users = nosql_service.smembers('users:active')

# 有序集合（排行榜）
nosql_service.zadd('ranking:scores', 95, 'user1', 88, 'user2', 92, 'user3')
top_users = nosql_service.zrange('ranking:scores', 0, 2, withscores=True)

# 文档操作
doc_id = nosql_service.insert_document('articles', {
    'title': 'Python教程',
    'content': '学习Python编程',
    'tags': ['python', 'programming']
})
articles = nosql_service.find_document('articles', {'tags': 'python'})
nosql_service.update_document('articles', {'_id': doc_id}, {'views': 100})
nosql_service.delete_document('articles', {'_id': doc_id})

# 事务操作
operations = [
    {'type': 'set', 'key': 'user:123', 'value': 'updated'},
    {'type': 'incr', 'key': 'counter', 'amount': 1}
]
success = nosql_service.transaction(operations)

# 批量操作
values = nosql_service.mget(['key1', 'key2', 'key3'])
nosql_service.mset([('key1', 'value1'), ('key2', 'value2')])

# 持久化
nosql_service.save('/path/to/nosql_data.json')
nosql_service.load('/path/to/nosql_data.json')

# 获取统计
stats = nosql_service.get_stats()
```

### 文档操作示例

```python
# 插入文档
doc_id = nosql_service.insert_document('products', {
    'name': 'iPhone 15',
    'price': 5999,
    'category': 'electronics',
    'stock': 100
})

# 查询文档
products = nosql_service.find_document('products', {'category': 'electronics'})

# 查询单个文档
product = nosql_service.find_one_document('products', {'_id': doc_id})

# 更新文档
updated = nosql_service.update_document(
    'products',
    {'_id': doc_id},
    {'stock': 99, 'price': 5899}
)

# 删除文档
deleted = nosql_service.delete_document('products', {'_id': doc_id})
```

### 排行榜示例

```python
# 创建排行榜
nosql_service.zadd('game:scores', 1500, 'player1', 2300, 'player2', 1800, 'player3')

# 获取前三名
top3 = nosql_service.zrange('game:scores', 0, 2, withscores=True)
# [('player2', 2300.0), ('player3', 1800.0), ('player1', 1500.0)]

# 获取玩家排名
rank = nosql_service.zrank('game:scores', 'player1')  # 2

# 获取玩家分数
score = nosql_service.zscore('game:scores', 'player2')  # 2300.0
```

### 队列示例

```python
# 任务队列
nosql_service.rpush('queue:email', 'email1', 'email2', 'email3')

# 处理任务
while True:
    task = nosql_service.lpop('queue:email')
    if not task:
        break
    process_task(task)
```

## 性能优化

### 搜索引擎优化

```python
# 1. 使用批量索引
documents = [
    {'doc_id': 'doc1', 'title': '...', 'content': '...'},
    {'doc_id': 'doc2', 'title': '...', 'content': '...'}
]
for doc in documents:
    search_engine_service.index_document(**doc)

# 2. 定期保存索引
search_engine_service.save_index()

# 3. 使用过滤条件减少结果集
results = search_engine_service.search_with_filters(
    query='关键词',
    filters={'category': '技术'},
    limit=10
)
```

### NoSQL 优化

```python
# 1. 使用 TTL 自动清理过期数据
nosql_service.set('session:abc123', 'user_data', ttl=1800)  # 30分钟过期

# 2. 使用批量操作减少开销
nosql_service.mset([('k1', 'v1'), ('k2', 'v2'), ('k3', 'v3')])

# 3. 使用事务保证原子性
operations = [
    {'type': 'set', 'key': 'a', 'value': 10},
    {'type': 'set', 'key': 'b', 'value': 20}
]
nosql_service.transaction(operations)
```

## 生产环境配置

### 搜索引擎配置

```python
from app.services.search_engine_service import search_engine_service, SearchEngineType

# 设置搜索引擎类型
search_engine_service.set_engine_type(SearchEngineType.ELASTICSEARCH)

# 加载预建索引
search_engine_service.load_index()

# 预热索引
def warmup_search():
    hot_topics = ['Python', '编程', '教程', '技术']
    for topic in hot_topics:
        search_engine_service.search(topic, limit=1)
```

### NoSQL 配置

```python
from app.services.nosql_service import nosql_service, NoSQLType

# 设置数据库类型
nosql_service.set_db_type(NoSQLType.REDIS)

# 加载持久化数据
nosql_service.load('/data/nosql_backup.json')

# 定期保存
import threading
def periodic_save():
    while True:
        nosql_service.save('/data/nosql_backup.json')
        time.sleep(3600)  # 每小时保存一次

threading.Thread(target=periodic_save, daemon=True).start()
```

## 监控与统计

### 搜索引擎统计

```python
stats = search_engine_service.get_stats()
print(stats)
# {
#     'engine_type': 'local',
#     'total_documents': 1000,
#     'total_tokens': 50000
# }
```

### NoSQL 统计

```python
stats = nosql_service.get_stats()
print(stats)
# {
#     'db_type': 'redis',
#     'kv_keys_count': 500,
#     'collections': ['users', 'products', 'articles'],
#     'documents_count': {'users': 100, 'products': 50, 'articles': 200}
# }
```

## 总结

搜索引擎和 NoSQL 功能已完成，主要特性：

### 搜索引擎
1. **倒排索引**: 高效的全文搜索
2. **BM25 评分**: 精准的搜索排序
3. **高亮显示**: 搜索词高亮
4. **过滤搜索**: 支持元数据过滤
5. **索引持久化**: 支持保存/加载

### NoSQL 数据库
1. **多种数据结构**: String、Hash、List、Set、ZSet、Document
2. **TTL 支持**: 自动过期清理
3. **事务操作**: 原子性保证
4. **批量操作**: 高效的数据读写
5. **持久化**: JSON 文件存储

所有功能已完整实现，可以直接使用！
