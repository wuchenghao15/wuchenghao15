# MTSCOS AI Project - 数据与应用分离架构

## 概述

本项目已实现数据与应用的完全分离，通过分层架构设计，实现数据层、业务层和表示层的解耦。

## 架构设计

### 整体架构图

```
┌─────────────────────────────────────────────────────────────────────────┐
│                           表示层 (Presentation Layer)                   │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐                  │
│  │   REST API   │  │   Web UI     │  │   CLI        │                  │
│  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘                  │
├─────────┼─────────────────┼─────────────────┼──────────────────────────┤
│                           业务层 (Service Layer)                        │
│  ┌──────────────────────────────────────────────────────────────────┐   │
│  │  UserService    ExamService    ApprovalService    DataService   │   │
│  └───────────────────────┬────────────────────────────────────────┘   │
├───────────────────────────┼─────────────────────────────────────────────┤
│                           数据访问层 (Data Access Layer)               │
│  ┌──────────────────────────────────────────────────────────────────┐   │
│  │                         DAO Layer                               │   │
│  │  ┌─────────┐ ┌─────────┐ ┌─────────┐ ┌──────────────┐          │   │
│  │  │UserDAO │ │ExamDAO  │ │Approval │ │BaseDAO      │          │   │
│  │  └────┬────┘ └────┬────┘ └────┬────┘ └──────┬───────┘          │   │
│  └───────┼───────────┼───────────┼──────────────┼──────────────────┘   │
├─────────┼───────────┼───────────┼──────────────┼───────────────────────┤
│                           数据库层 (Database Layer)                     │
│  ┌──────────────────────────────────────────────────────────────────┐   │
│  │                    Database Manager                               │   │
│  │  ┌─────────────┐     ┌─────────────┐     ┌─────────────┐       │   │
│  │  │   SQLite    │     │ PostgreSQL  │     │   Redis     │       │   │
│  │  └─────────────┘     └─────────────┘     └─────────────┘       │   │
│  └──────────────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────────────┘
```

### 分层职责

| 层级 | 职责 | 关键组件 |
|------|------|----------|
| **表示层** | 处理用户请求和响应 | REST API、Web UI、CLI |
| **业务层** | 实现业务逻辑 | UserService、ExamService、ApprovalService |
| **数据访问层** | 封装数据访问逻辑 | DAO类、数据层服务 |
| **数据库层** | 数据持久化 | SQLite、PostgreSQL、Redis |

## 数据层组件

### 1. DAO层 (Data Access Object)

#### 基础DAO类
```python
from app.data.dao import BaseDAO

# 使用基础DAO操作任意表
result = BaseDAO.list(table_name='users', filters={'status': 'active'})
```

#### 用户DAO
```python
from app.data.dao import UserDAO

# 查询用户
user = UserDAO.find_by_username('admin')
users = UserDAO.list_active_users(page=1, page_size=20)

# 创建用户
user_id = UserDAO.create({
    'username': 'new_user',
    'email': 'user@example.com',
    'role': 'user'
})

# 更新用户
UserDAO.update(user_id, {'email': 'new_email@example.com'})

# 删除用户
UserDAO.delete(user_id)
```

#### 考试DAO
```python
from app.data.dao import ExamDAO, QuestionDAO, ExamPaperDAO, ExamResultDAO

# 考试操作
exams = ExamDAO.list_active_exams()
questions = QuestionDAO.list_by_exam(exam_id)
papers = ExamPaperDAO.list_by_user(user_id)
results = ExamResultDAO.list_by_user(user_id)
```

#### 审批DAO
```python
from app.data.dao import ApprovalRequestDAO, ApprovalNotificationDAO

# 审批操作
requests = ApprovalRequestDAO.list_by_status('pending')
notifications = ApprovalNotificationDAO.list_unread(user_id)
```

### 2. 数据层服务

```python
from app.data import data_layer_service

# 创建备份
backup_path = data_layer_service.create_backup()

# 恢复备份
data_layer_service.restore_backup(backup_path)

# 列出备份
backups = data_layer_service.list_backups()

# 导出表
export_path = data_layer_service.export_table('users', format_type='json')

# 导入表
data_layer_service.import_table('users', export_path)

# 获取数据库统计
stats = data_layer_service.get_database_stats()

# 数据迁移
result = data_layer_service.migrate_data(source_db_uri)
```

## 数据目录结构

```
flask-app/
├── app/
│   ├── data/                    # 数据层
│   │   ├── __init__.py          # 数据层入口
│   │   └── dao/                 # 数据访问对象
│   │       ├── __init__.py
│   │       ├── base_dao.py      # 基础DAO类
│   │       ├── user_dao.py      # 用户DAO
│   │       ├── exam_dao.py      # 考试DAO
│   │       └── approval_dao.py  # 审批DAO
│   └── services/
│       └── data_layer_service.py # 数据层服务
├── data/                        # 数据文件目录（外部挂载）
│   ├── app.db                   # SQLite数据库
│   ├── uploads/                 # 上传文件
│   ├── exports/                 # 导出文件
│   └── temp/                    # 临时文件
└── backups/                     # 备份目录（外部挂载）
```

## 数据与应用分离的优势

### 1. 关注点分离
- **业务逻辑**与**数据访问**解耦
- 业务层不依赖具体数据库实现
- 便于测试和维护

### 2. 灵活的数据库切换
```python
# 通过配置切换数据库
# .env 文件配置
DATABASE_TYPE=sqlite
# DATABASE_TYPE=postgresql
```

### 3. 独立的数据管理
- 数据备份/恢复独立于应用
- 数据导入/导出支持多种格式
- 数据迁移支持跨数据库

### 4. 便于扩展
- 新增业务只需添加新的DAO类
- 支持读写分离
- 支持分库分表

## 使用示例

### 示例1：用户管理

```python
from app.data.dao import UserDAO

# 创建用户
user_id = UserDAO.create({
    'username': 'john_doe',
    'email': 'john@example.com',
    'password': 'hashed_password',
    'role': 'user',
    'status': 'active'
})

# 查询用户
user = UserDAO.get(user_id)
user_by_email = UserDAO.find_by_email('john@example.com')

# 更新用户
UserDAO.update(user_id, {'email': 'john.doe@example.com'})

# 删除用户
UserDAO.delete(user_id)
```

### 示例2：数据备份与恢复

```python
from app.data import data_layer_service

# 定期备份
backup_path = data_layer_service.create_backup()
print(f"备份成功: {backup_path}")

# 查看所有备份
backups = data_layer_service.list_backups()
for backup in backups:
    print(f"{backup['name']} - {backup['size']} bytes")

# 恢复备份（如有需要）
data_layer_service.restore_backup(backups[0]['path'])
```

### 示例3：数据迁移

```python
from app.data import data_layer_service

# 迁移所有表
result = data_layer_service.migrate_data(
    source_db_uri='sqlite:///old_app.db'
)

# 迁移指定表
result = data_layer_service.migrate_data(
    source_db_uri='sqlite:///old_app.db',
    target_tables=['users', 'exams']
)

print(f"成功迁移: {result['migrated_tables']}")
print(f"失败: {result['failed_tables']}")
```

## 最佳实践

### 1. 使用DAO进行数据访问
```python
# ✅ 推荐：使用DAO层
from app.data.dao import UserDAO
user = UserDAO.find_by_username('admin')

# ❌ 不推荐：直接使用数据库管理器
from app.utils.db import db_manager
user = db_manager.fetch_one("SELECT * FROM users WHERE username = ?", ('admin',))
```

### 2. 事务管理
```python
from app.utils.lock_sync_manager import synchronized

@synchronized(resource='user_operation', lock_type=LockType.WRITE)
def update_user_profile(user_id, data):
    # 多个数据库操作在同一事务中
    UserDAO.update(user_id, data)
    # 其他操作...
```

### 3. 数据验证
```python
from app.utils.data_validator import DataValidator

def create_user(data):
    # 验证数据
    validator = DataValidator()
    errors = validator.validate(data, user_schema)
    if errors:
        raise ValidationError(errors)
    
    # 创建用户
    return UserDAO.create(data)
```

### 4. 日志记录
```python
from app.utils.logging import logger

def get_user(user_id):
    try:
        user = UserDAO.get(user_id)
        if user:
            logger.info(f"用户查询成功: {user_id}")
        else:
            logger.warning(f"用户不存在: {user_id}")
        return user
    except Exception as e:
        logger.error(f"查询用户失败: {str(e)}")
        raise
```

## 未来扩展

### 1. 读写分离
```python
# 配置读写分离
# .env
DATABASE_READ_URI=postgresql://user:pass@read-db:5432/mtscos_db
DATABASE_WRITE_URI=postgresql://user:pass@write-db:5432/mtscos_db
```

### 2. 分布式数据库
```python
# 支持分布式数据库
from app.data.dao import ShardedDAO

# 分片查询
users = ShardedDAO.query('users', shard_key='user_id', filters={...})
```

### 3. 数据缓存层
```python
# 添加缓存
from app.data.dao import CachedDAO

# 查询时自动使用缓存
users = CachedDAO.list('users', cache_ttl=300)
```

## 总结

通过数据与应用的分离设计，系统实现了：

1. **模块化**: 各层职责清晰，便于开发和维护
2. **可测试性**: DAO层可以独立测试
3. **可扩展性**: 支持多种数据库和存储方案
4. **数据安全**: 统一的数据访问控制和事务管理
5. **运维友好**: 独立的数据备份、恢复和迁移功能
