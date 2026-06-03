# MTSCOS JSON自动同步系统

## 概述

MTSCOS系统现在支持JSON数据自动同步功能，一旦有JSON数据或JSON数据变化，系统会自动同步到数据库。

## 功能特性

### 1. 实时监控
- 监控项目中的所有JSON文件
- 自动检测文件创建、修改事件
- 使用watchdog库实现高效文件监控

### 2. 自动同步
- 检测到变化自动同步到数据库
- 支持定期同步（默认10秒间隔）
- 版本控制，每次变更记录新版本

### 3. 哈希校验
- 使用SHA256校验文件内容
- 避免重复同步
- 数据完整性保证

### 4. 完整的日志系统
- 记录所有同步操作
- 状态追踪和错误报告
- 历史版本管理

## 核心文件

### json_auto_sync_system.py
JSON自动同步系统核心模块

**主要类:**
- `EnhancedJSONSyncManager`: 增强的JSON同步管理器
- `JSONSyncAPI`: Flask API集成

**主要方法:**
- `scan_directory()`: 扫描目录中的JSON文件
- `register_json_file()`: 注册JSON文件
- `sync_file()`: 同步单个文件
- `sync_all_files()`: 同步所有文件
- `start_file_monitoring()`: 启动文件监控
- `get_statistics()`: 获取同步统计
- `get_sync_logs()`: 获取同步日志

### system_auto_adapter.py
系统自动适配器

**主要功能:**
- 自动检测新模块
- 自动注册和加载模块
- 自动更新系统配置
- 统一启动管理

**主要方法:**
- `detect_new_modules()`: 检测新增模块
- `register_module()`: 注册模块
- `auto_adapt()`: 执行自动适配
- `get_module_status()`: 获取模块状态

## 使用方法

### 方式1: 使用完整启动脚本（推荐）

```bash
# 启动完整系统（自动适配+所有服务）
python3 start_full_system.py

# 或使用Shell脚本
./start_complete_system.sh
```

### 方式2: 单独启动JSON同步

```bash
# 启动JSON同步系统
python3 start_json_sync.py

# 快速测试
python3 quick_test.py
```

### 方式3: 集成到现有系统

```python
from system_auto_adapter import SystemAutoAdapter

# 创建适配器
adapter = SystemAutoAdapter(project_root)

# 执行自动适配
result = adapter.auto_adapt()

# 获取模块状态
status = adapter.get_module_status()
```

## API接口

启动系统后，可以通过以下API访问JSON同步功能：

### 获取同步状态
```
GET /api/json-sync/status
```

### 获取已注册文件列表
```
GET /api/json-sync/files
```

### 获取同步日志
```
GET /api/json-sync/logs?limit=50
```

### 手动触发同步
```
POST /api/json-sync/sync
```

### 扫描新文件
```
POST /api/json-sync/scan
```

### 获取JSON内容
```
GET /api/json-sync/file/文件路径
GET /api/json-sync/file/文件路径?version=1
```

## 数据库结构

### json_sync_config
存储JSON文件配置信息

| 字段 | 类型 | 说明 |
|------|------|------|
| id | INTEGER | 主键 |
| file_path | TEXT | 文件路径 |
| file_name | TEXT | 文件名 |
| directory | TEXT | 目录 |
| enabled | BOOLEAN | 是否启用 |
| sync_enabled | BOOLEAN | 是否启用同步 |
| last_sync | TEXT | 最后同步时间 |
| last_modified | REAL | 最后修改时间 |
| content_hash | TEXT | 内容哈希 |
| version | INTEGER | 版本号 |
| created_at | TEXT | 创建时间 |
| updated_at | TEXT | 更新时间 |

### json_sync_data
存储JSON文件内容

| 字段 | 类型 | 说明 |
|------|------|------|
| id | INTEGER | 主键 |
| file_path | TEXT | 文件路径 |
| file_name | TEXT | 文件名 |
| content | TEXT | JSON内容 |
| content_hash | TEXT | 内容哈希 |
| sync_time | TEXT | 同步时间 |
| version | INTEGER | 版本号 |
| created_at | TEXT | 创建时间 |

### json_sync_logs
存储同步日志

| 字段 | 类型 | 说明 |
|------|------|------|
| id | INTEGER | 主键 |
| file_path | TEXT | 文件路径 |
| file_name | TEXT | 文件名 |
| action | TEXT | 操作类型 |
| status | TEXT | 状态 |
| message | TEXT | 消息 |
| sync_time | TEXT | 同步时间 |

## 配置说明

系统在 `system_config.json` 中自动维护以下配置：

```json
{
  "modules": {
    "json_auto_sync": {
      "name": "json_auto_sync",
      "type": "sync_module",
      "version": "1.0.0",
      "description": "JSON数据自动同步系统",
      "auto_start": true
    }
  },
  "auto_adapt": {
    "enabled": true,
    "scan_interval": 60,
    "auto_load_modules": true
  }
}
```

## 监控目录

默认监控项目根目录：
```
/Users/wuchenghao/Library/CloudStorage/OneDrive-个人/文档/MTSCOS_AI_Project
```

可以在创建 `EnhancedJSONSyncManager` 时指定其他目录：

```python
sync_manager = EnhancedJSONSyncManager(
    db_path="mtcos_json_sync.db",
    project_root="/path/to/directory"
)
```

## 统计信息

系统提供完整的同步统计：

```python
stats = sync_manager.get_statistics()
# {
#   'total_files': 10,
#   'synced_files': 8,
#   'total_versions': 25,
#   'success_count': 22
# }
```

## 版本控制

每次文件变更，系统会自动增加版本号：

```python
# 获取当前版本
version = sync_manager._get_current_version(file_path)

# 获取特定版本内容
content = sync_manager.get_json_content(file_path, version=1)

# 获取最新内容
content = sync_manager.get_json_content(file_path)
```

## 故障排除

### 问题1: watchdog未安装
```bash
pip3 install watchdog
```

### 问题2: 数据库锁定
确保没有其他进程同时访问数据库

### 问题3: 权限不足
确保有读取JSON文件和写入数据库的权限

## 性能优化

1. **定期同步间隔**: 默认10秒，可根据需求调整
2. **文件过滤**: 可配置忽略特定目录
3. **增量同步**: 只同步变更的文件
4. **批量操作**: 减少数据库IO次数

## 安全性

- 内容哈希校验防止篡改
- 版本控制支持回滚
- 完整的操作日志
- 异常保护机制

## 扩展开发

### 添加新的模块类型

```python
class SystemAutoAdapter:
    def register_module(self, module_info: Dict[str, Any]) -> bool:
        if module_info['type'] == 'custom_module':
            self.load_custom_module(module_info)
            return True
        return False
```

### 自定义同步策略

```python
class EnhancedJSONSyncManager:
    def __init__(self, ...):
        self.sync_interval = 30  # 自定义同步间隔

    def _should_sync(self, file_path: str) -> bool:
        # 自定义同步逻辑
        return True
```

## 更新日志

### v1.0.0 (2026-05-31)
- 实现JSON文件自动监控
- 实现数据库同步
- 实现版本控制
- 实现自动适配器
- 提供完整API接口
- 支持Flask集成

## 作者

MTSCOS AI Team

## 许可

MIT License

## 联系方式

技术支持: MTSCOS Support Team
