# AI 智能分散数据库系统实现计划

## Context（背景与目标）

### 问题
- `app.db` 已达 **889MB**，`ai_engines/mtscos_ai_project.db` 达 **1.4GB**，日志表膨胀严重
- 26 个备份文件共约 **24GB** 冗余存储
- `app.py` 中 71 处 `sqlite3.connect(DATABASE_PATH)` 未设置 timeout，高并发下易触发 `database is locked`
- 已有 4 套分布式数据库代码（`distributed_db_manager.py`、`distributed_db_service.py`、`read_write_splitter.py`、`ai_master_slave_manager.py`），但**蓝图均未注册、未接入主应用**
- **没有任何"智能分散"逻辑**——所有分片都是静态规则，无负载感知、无 AI 决策

### 目标
建立 **AI 智能分散数据库系统**：激活现有分布式代码并注册蓝图，在其之上新增 AI 智能层（4 个数据库管理 AI 员工），按"表类型 + 功能模块 + 数据热度"三维分散数据，先迁移最膨胀的日志/历史表，业务表暂不动。

### 用户确认的决策
1. **策略**：激活现有代码 + AI 增强（不重复造轮子）
2. **分散维度**：表类型 + 功能模块 + 数据热度（三者结合）
3. **迁移范围**：建立架构 + 迁移框架，先迁移日志表，业务表不动
4. **AI 员工**：4 个专门的数据库管理 AI 员工

---

## 核心设计决策

1. **延迟单例包装** `DistributedDatabaseManager`（避免其模块级实例化阻塞启动，参考 `version_agent_ai.py` 的 `get_version_agent_ai()` 模式）
2. **三维分类注册表** `db_schema_registry.py` 统一管理表分类（避免策略散落各处）
3. **模板化守护线程** `base_db_employee.py`（4 个员工只实现 `_do_work`，统一 start/stop/status）
4. **独立元数据库** `ai_distributed_db.db`（7 张元数据表，彻底隔离配置与业务数据，参考 `ai_agent_config.db` 模式）
5. **安全迁移原则**：先小表试水 → 分批 1000 条 → MD5 校验 → 断点续传 → 原表保留 → 双写过渡

---

## 物理数据库结构

分散到 `databases/` 目录下的 6 个库：

| 数据库文件 | 分类 | 包含表（示例） | 热度 |
|-----------|------|---------------|------|
| `core.db` | core | users、exams、questions、exam_sessions | hot |
| `logs.db` | logs | system_logs、access_logs、error_logs、operation_logs | warm |
| `exam_behavior.db` | behavior | exam_behavior_logs、cheating_detection_results、screen_switch_logs | warm |
| `ai_engine.db` | ai_engine | exam_ai_sessions、exam_ai_conversations、code_repair_logs | warm |
| `knowledge.db` | knowledge | knowledge_base_questions、student_mistakes、learning_paths | hot |
| `archive.db` | archive | 90天以上的历史数据 | cold |

> 业务表（users、exams、questions 等）本次**不迁移**，仅建立路由元数据。先迁移 `logs.db` 中的 6 张膨胀表。

---

## 文件清单

### 新建文件（7 个）

| # | 文件路径 | 职责 |
|---|---------|------|
| 1 | `ai_engines/db_schema_registry.py` | 三维分类注册表：表→分类/模块/热度映射 |
| 2 | `ai_engines/ai_distributed_db_manager.py` | AI 智能分散数据库核心管理器（延迟单例） |
| 3 | `ai_engines/db_employees/__init__.py` | 包初始化 |
| 4 | `ai_engines/db_employees/base_db_employee.py` | 数据库员工基类（模板化守护线程） |
| 5 | `ai_engines/db_employees/db_employees.py` | 4 个数据库管理 AI 员工实现 |
| 6 | `app/api/ai_distributed_db_api.py` | AI 分散数据库 API 蓝图 |
| 7 | `ai_engines/db_employees/migration_framework.py` | 数据迁移框架（分批/校验/断点续传） |

### 修改文件（2 个）

| # | 文件路径 | 修改内容 |
|---|---------|---------|
| 1 | `app/__init__.py` | 在 `_register_blueprints()` 中注册 `distributed_db_api`、`read_write_splitter_api`、`ai_distributed_db_api` 三个蓝图 |
| 2 | `ai_engines/ai_agent_auto_config.py` | 在 7 步配置流程中新增"AI 分散数据库"配置步骤，注册 4 个数据库员工 |

---

## 核心类设计

### 1. `db_schema_registry.py` — 三维分类注册表

```python
class TableCategory(Enum):
    CORE = "core"          # 核心业务表
    LOGS = "logs"          # 日志表
    BEHAVIOR = "behavior"  # 考试行为表
    AI_ENGINE = "ai_engine"  # AI引擎表
    KNOWLEDGE = "knowledge"  # 题库表
    ARCHIVE = "archive"    # 归档表

class DataHeat(Enum):
    HOT = "hot"    # 高频读写
    WARM = "warm"  # 中频
    COLD = "cold"  # 低频归档

# 表→库映射注册表
TABLE_REGISTRY = {
    'system_logs':       {'category': LOGS,      'module': 'system',  'heat': WARM, 'shard_db': 'logs.db'},
    'access_logs':       {'category': LOGS,      'module': 'system',  'heat': WARM, 'shard_db': 'logs.db'},
    'error_logs':        {'category': LOGS,      'module': 'system',  'heat': WARM, 'shard_db': 'logs.db'},
    'operation_logs':    {'category': LOGS,      'module': 'system',  'heat': WARM, 'shard_db': 'logs.db'},
    'audit_events':      {'category': LOGS,      'module': 'system',  'heat': WARM, 'shard_db': 'logs.db'},
    'change_logs':       {'category': LOGS,      'module': 'system',  'heat': WARM, 'shard_db': 'logs.db'},
    'users':             {'category': CORE,      'module': 'auth',    'heat': HOT,  'shard_db': 'core.db'},
    'exams':             {'category': CORE,      'module': 'exam',    'heat': HOT,  'shard_db': 'core.db'},
    # ... 其余表
}
```

### 2. `ai_distributed_db_manager.py` — 核心管理器

```python
class AIDistributedDatabaseManager:
    """AI智能分散数据库管理器（延迟单例）"""

    def __init__(self):
        self.db_dir = os.path.join(app_root, 'databases')
        self.meta_db = 'ai_distributed_db.db'  # 元数据库
        self._init_meta_tables()         # 7张元数据表
        self.shard_connections = {}      # {db_name: sqlite3.Connection}
        self.query_router = None         # DBQueryRouterAI 引用
        self._init_shards()              # 初始化6个分片库（CREATE TABLE IF NOT EXISTS）

    # === 元数据表（ai_distributed_db.db）===
    # 1. shard_registry       — 分片库注册（db_name, category, table_count, size_bytes, status）
    # 2. table_routing         — 表路由（table_name, shard_db, category, module, heat, migrated）
    # 3. migration_progress    — 迁移进度（table_name, batch_size, total, completed, status, md5_check）
    # 4. query_stats           — 查询统计（shard_db, query_count, avg_time, last_access）
    # 5. heat_metrics          — 热度指标（table_name, read_count, write_count, last_access, heat_level）
    # 6. employee_status       — 员工状态（employee_id, name, status, last_task, task_count）
    # 7. decision_log          — AI决策日志（decision_type, details, timestamp）

    def route_query(self, table_name, operation): ...
    def get_shard_connection(self, db_name): ...
    def register_shard(self, db_name, category): ...
    def update_heat(self, table_name, access_type): ...
    def get_status(self): ...
```

### 3. `base_db_employee.py` — 员工基类

```python
class BaseDBEmployee(AIEmployee):
    """数据库管理AI员工基类（模板方法模式）"""
    def __init__(self, employee_id, name, role, skills, interval=300):
        super().__init__(employee_id, name, role, skills)
        self.interval = interval        # 守护线程循环间隔（秒）
        self._running = False
        self._thread = None
        self._manager = None            # AIDistributedDatabaseManager 引用

    def start(self): ...                # 启动 daemon 守护线程
    def stop(self): ...                 # 停止
    def _run_loop(self): ...            # 模板：while running → _do_work() → sleep
    def _do_work(self): ...             # 子类实现：具体工作逻辑
    def get_status(self): ...           # 返回状态（含 task_count, last_task）
```

### 4. `db_employees.py` — 4 个数据库管理 AI 员工

```python
class DBShardDecisionAI(BaseDBEmployee):
    """数据分散决策AI - 分析表数据量/增长率，决策是否需要重新分片"""
    employee_id = 'db_shard_decision_001'
    interval = 3600  # 每小时分析一次
    def _do_work(self):
        # 1. 扫描各分片库表数据量
        # 2. 计算增长率（对比历史指标）
        # 3. 生成重分片建议（写入 decision_log）
        # 4. 热度降级/升级（hot→warm→cold）

class DBMigrationAI(BaseDBEmployee):
    """数据迁移执行AI - 执行分批迁移，MD5校验，断点续传"""
    employee_id = 'db_migration_001'
    interval = 60  # 每分钟检查迁移队列
    def _do_work(self):
        # 1. 读取 migration_progress 表中 status='pending' 的任务
        # 2. 调用 migration_framework 执行下一批迁移
        # 3. MD5 一致性校验
        # 4. 更新迁移进度

class DBQueryRouterAI(BaseDBEmployee):
    """查询路由优化AI - 智能路由查询，缓存热点，优化跨分片"""
    employee_id = 'db_query_router_001'
    interval = 300  # 每5分钟优化路由表
    def _do_work(self):
        # 1. 分析 query_stats 统计
        # 2. 更新热度指标（heat_metrics）
        # 3. 优化路由缓存策略
        # 4. 识别热点查询并预缓存

class DBHealthMonitorAI(BaseDBEmployee):
    """数据库健康监控AI - 监控容量/锁状态/性能，触发清理"""
    employee_id = 'db_health_monitor_001'
    interval = 120  # 每2分钟检查一次
    def _do_work(self):
        # 1. 检查各分片库文件大小
        # 2. 检查锁状态（PRAGMA journal_mode）
        # 3. 触发清理（旧数据归档到 archive.db）
        # 4. 容量预警（写入 decision_log）
```

### 5. `migration_framework.py` — 迁移框架

```python
class MigrationFramework:
    """安全数据迁移框架"""
    BATCH_SIZE = 1000

    def migrate_table(self, table_name, target_db): ...
        # 1. 读取 migration_progress（断点续传）
        # 2. 分批读取源表（每批1000条，OFFSET 翻页）
        # 3. 写入目标库
        # 4. MD5 校验（源 vs 目标）
        # 5. 更新 migration_progress
        # 6. 标记原表数据为已迁移（migrated=1，不删除）

    def verify_migration(self, table_name): ...
        # 全表 MD5 校验

    def get_progress(self, table_name): ...
        # 返回迁移进度百分比
```

### 6. `ai_distributed_db_api.py` — API 蓝图

```text
蓝图名: ai_distributed_db_api
URL前缀: /api/ai-distributed-db

端点:
GET  /status           — 系统整体状态
GET  /shards           — 分片库列表（含大小、表数、状态）
GET  /shards/<name>    — 单个分片库详情
GET  /routing          — 表路由表
GET  /migration/status — 迁移进度
POST /migration/start  — 启动指定表迁移
POST /migration/stop   — 暂停迁移
GET  /employees        — 4个数据库员工状态
POST /employees/<id>/start — 启动员工
POST /employees/<id>/stop  — 停止员工
GET  /health           — 健康检查报告
GET  /decisions        — AI决策日志
POST /route/test       — 测试查询路由
```

---

## 实施步骤（按依赖顺序）

### 步骤 1：创建三维分类注册表
- 新建 `ai_engines/db_schema_registry.py`
- 定义 `TableCategory`、`DataHeat` 枚举
- 建立 `TABLE_REGISTRY` 字典（覆盖所有已知膨胀表）

### 步骤 2：创建核心管理器
- 新建 `ai_engines/ai_distributed_db_manager.py`
- 实现 `AIDistributedDatabaseManager` 类（延迟单例 `get_ai_distributed_db_manager()`）
- 初始化 7 张元数据表（`ai_distributed_db.db`）
- 初始化 6 个分片库目录和空表结构

### 步骤 3：创建员工基类和 4 个员工
- 新建 `ai_engines/db_employees/__init__.py`
- 新建 `ai_engines/db_employees/base_db_employee.py`（模板方法模式）
- 新建 `ai_engines/db_employees/db_employees.py`（4 个员工实现）

### 步骤 4：创建迁移框架
- 新建 `ai_engines/db_employees/migration_framework.py`
- 实现分批迁移、MD5 校验、断点续传

### 步骤 5：创建 API 蓝图
- 新建 `app/api/ai_distributed_db_api.py`
- 实现所有端点

### 步骤 6：注册蓝图
- 修改 `app/__init__.py` 的 `_register_blueprints()`
- 在 API 蓝图组中新增 3 个蓝图：
  - `('app.api.distributed_db_api', 'distributed_db_api', '/api/distributed-db')`
  - `('app.api.read_write_splitter_api', 'read_write_splitter_api', '/api/read-write')`
  - `('app.api.ai_distributed_db_api', 'ai_distributed_db_api', '/api/ai-distributed-db')`

### 步骤 7：整合到自动配置系统
- 修改 `ai_engines/ai_agent_auto_config.py`
- 在 `auto_configure_all()` 中新增步骤（7步→8步）：
  - 步骤 8：配置 AI 智能分散数据库系统
  - 初始化 `AIDistributedDatabaseManager`
  - 注册 4 个数据库员工到 `ai_employee_manager`
- 在 `_configure_auto_generator` 的 planned_features 中新增 `distributed_database` 功能

### 步骤 8：初始化迁移队列
- 在 `AIDistributedDatabaseManager` 初始化时，向 `migration_progress` 表插入 6 张日志表的待迁移记录：
  - system_logs → logs.db
  - access_logs → logs.db
  - error_logs → logs.db
  - operation_logs → logs.db
  - audit_events → logs.db
  - change_logs → logs.db

---

## 复用的现有代码

| 现有文件 | 复用方式 |
|---------|---------|
| `app/utils/distributed_db_manager.py` | `DistributedDatabaseManager` 类被 `AIDistributedDatabaseManager` 包装调用（分片策略、连接管理） |
| `app/services/distributed_db_service.py` | `ConsistentHashRing` 一致性哈希环被查询路由复用 |
| `ai_engines/ai_employees.py` | `AIEmployee` 基类被 `BaseDBEmployee` 继承 |
| `ai_engines/ai_agent_auto_config.py` | 配置流程扩展点（`auto_configure_all` 方法） |
| `app/__init__.py` | `_register_blueprints()` 蓝图注册入口 |

---

## 验证方法

### 1. 单元验证（配置脚本）
```bash
cd flask-app && python3 -u ai_engines/ai_agent_auto_config.py
```
预期：8 步全部成功，输出 "配置分散数据库AI员工数: 4"

### 2. API 验证
```bash
# 系统状态
curl http://127.0.0.1:8888/api/ai-distributed-db/status
# 分片库列表
curl http://127.0.0.1:8888/api/ai-distributed-db/shards
# 迁移进度
curl http://127.0.0.1:8888/api/ai-distributed-db/migration/status
# 员工状态
curl http://127.0.0.1:8888/api/ai-distributed-db/employees
```

### 3. 数据库验证
```bash
# 检查元数据库
sqlite3 flask-app/ai_distributed_db.db ".tables"
# 预期7张表：shard_registry, table_routing, migration_progress, query_stats, heat_metrics, employee_status, decision_log

# 检查分片库
sqlite3 flask-app/databases/logs.db ".tables"
# 预期：system_logs, access_logs, error_logs, operation_logs, audit_events, change_logs
```

### 4. 迁移验证
```bash
# 启动单表迁移
curl -X POST http://127.0.0.1:8888/api/ai-distributed-db/migration/start \
  -H "Content-Type: application/json" \
  -d '{"table": "system_logs"}'
# 检查进度
curl http://127.0.0.1:8888/api/ai-distributed-db/migration/status
# 预期：status=completed, md5_check=passed
```

### 5. 员工守护线程验证
```bash
# 启动所有员工
curl -X POST http://127.0.0.1:8888/api/ai-distributed-db/employees/db_health_monitor_001/start
# 等待2分钟后检查状态
curl http://127.0.0.1:8888/api/ai-distributed-db/employees
# 预期：status=running, task_count>0
```

---

## 风险点和注意事项

1. **避免导入阻塞**：所有管理器和员工必须使用延迟单例（参考 `version_agent_ai.py` 的 `get_version_agent_ai()` 模式），不在模块级创建实例
2. **独立元数据库**：使用 `ai_distributed_db.db`（非 app.db），避免与 889MB 主库冲突
3. **SQLite 连接安全**：所有连接添加 `check_same_thread=False, timeout=30.0`
4. **迁移不删除原数据**：迁移后原表数据保留（`migrated=1` 标记），仅标记不删除，确保回滚能力
5. **业务表不动**：本次仅迁移 6 张日志表，users/exams/questions 等业务表保持原位
6. **daemon 线程**：所有守护线程设置 `daemon=True`，确保主进程退出时自动清理
7. **蓝图注册容错**：`distributed_db_api` 和 `read_write_splitter_api` 可能有依赖问题，注册时需 try/except 容错
8. **databases/ 目录**：需确保目录存在，初始化时 `os.makedirs(db_dir, exist_ok=True)`
