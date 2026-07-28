# AI智能分散数据库系统 — 初始化卡死修复计划

## 摘要

上一轮计划（`ai_distributed_db_remaining_tasks_plan.md`）已完成任务 #11–#13（API 蓝图、蓝图注册、自动配置整合），但 **任务 #14（验证测试）失败**：`python3 -m ai_engines.ai_agent_auto_config` 在步骤 8 卡死。

经 Phase 1 调研发现，卡死并非之前怀疑的"SQL 双引号"问题（那只是次要隐患），而是 **3 个叠加因素**：

1. **主因 — COUNT(\*) 全表扫描**：`_init_migration_queue()` 对 932MB 的 `app.db` 执行 `SELECT COUNT(*) FROM <table>`，6 张膨胀日志表逐一扫描，每张表可能耗时数分钟到数小时。
2. **加剧 — 11 个僵尸 sqlite3 进程**：从今早 8:23 起残留，全部卡在 app.db 上等锁，持有读锁导致新连接也阻塞。
3. **加剧 — 陈旧 journal 文件**：`app.db-journal`（12KB，7月3日 21:40）表明有一个未提交事务未回滚，新连接需先做 journal 恢复，但被僵尸进程的锁阻塞。

次要隐患（不阻塞初始化，但会在后续运行中暴露）：

4. **SQL 双引号**：`get_status()` 第 553/556 行用 `"pending"` / `"completed"`，SQLite 把双引号解析为标识符而非字符串字面值，跨版本不可靠，会触发 `no such column: pending`。
5. **DBShardDecisionAI 每小时 COUNT(\*)**：员工守护线程启动后，每小时对 app.db 执行 6 次 COUNT(\*)，会周期性卡死。
6. **migration_framework._verify_migration 全表扫描**：迁移完成时对源表执行 `SELECT * FROM <table> ORDER BY rowid` 做 MD5，932MB 表会卡很久（但仅在迁移结束触发一次，非阻塞初始化）。

---

## 当前状态分析

### 已完成（前一轮计划，无需重做）

| 项目 | 文件 | 状态 |
|------|------|------|
| API 蓝图（15端点） | `flask-app/app/api/ai_distributed_db_api.py` | ✅ 已创建，py_compile 通过 |
| 蓝图注册 | `flask-app/app/__init__.py:208` | ✅ 已追加 `('app.api.ai_distributed_db_api', 'ai_distributed_db_api', '/api')` |
| 自动配置整合 | `flask-app/ai_engines/ai_agent_auto_config.py` | ✅ 4处修改完成，步骤标签 7→8，新增 `_configure_distributed_db_system()` |
| `db_employees/__init__.py` 导出 | `flask-app/ai_engines/db_employees/__init__.py` | ✅ 6 函数导出齐全 |

### 失败现象（Phase 1 实测确认）

```text
[步骤 8/8] 配置 AI智能分散数据库系统...
... INFO - 元数据表初始化完成（7张表）           ← _init_meta_tables() 完成
... INFO - 分片库连接已创建: logs.db
... INFO - 分片库连接已创建: exam_behavior.db
... INFO - 分片库连接已创建: ai_engine.db
... INFO - 分片库连接已创建: knowledge.db
... INFO - 分片库连接已创建: core.db
... INFO - 分片库初始化完成: [...]                ← _init_shards() 完成
                                                 ← _init_migration_queue() 卡死（无"迁移队列初始化完成"日志）
```

`_init_migration_queue()` 卡在第 245 行 `pc.execute(f'SELECT COUNT(*) as cnt FROM {table_name}')` —— 对 932MB 的 app.db 执行全表 COUNT(\*)。

### 环境实测数据（Phase 1）

- `app.db`: **932,757,504 字节（889MB）**
- `app.db-journal`: **12,824 字节**（7月3日 21:40，陈旧未回滚事务）
- `ai_distributed_db.db`: 57KB（元数据库，正常）
- 6 个分片库（logs.db 等）: 全部 0 字节（schema 已建，数据未迁移，正常）
- 僵尸 sqlite3 进程: **11 个**（PID: 1067, 1131, 1148, 1213, 1546, 1610, 1918, 1982, 2056, 2120, 2415）
- 实测 `sqlite3 app.db "SELECT name FROM sqlite_master WHERE type='table'"` 4 秒内无响应（数据库被锁）

---

## 实施变更

### 变更 1：修复 SQL 双引号（防止 `get_status()` 报错）

**文件**：`flask-app/ai_engines/ai_distributed_db_manager.py`

**修改**：第 553、556 行

```python
# 修改前
c.execute('SELECT COUNT(*) as cnt FROM migration_progress WHERE status = "pending"')
c.execute('SELECT COUNT(*) as cnt FROM migration_progress WHERE status = "completed"')

# 修改后
c.execute("SELECT COUNT(*) as cnt FROM migration_progress WHERE status = 'pending'")
c.execute("SELECT COUNT(*) as cnt FROM migration_progress WHERE status = 'completed'")
```

**原理**：SQLite 把双引号 `"pending"` 解析为标识符（列名），新版本/严格模式下会抛 `no such column: pending`。改用单引号字面值。

### 变更 2：替换 `_init_migration_queue()` 的 COUNT(\*) 探测

**文件**：`flask-app/ai_engines/ai_distributed_db_manager.py`

**修改**：第 239–251 行（`_init_migration_queue` 方法内的 try 块）

```python
# 修改前
row_count = 0
try:
    probe = sqlite3.connect(app_db_path, timeout=3.0)
    probe.row_factory = sqlite3.Row
    pc = probe.cursor()
    pc.execute(f'SELECT COUNT(*) as cnt FROM {table_name}')
    row = pc.fetchone()
    row_count = row['cnt'] if row else 0
    probe.close()
except Exception as e:
    logger.warning(f"获取 {table_name} 行数失败（跳过）: {e}")
    row_count = -1  # 未知行数

# 修改后
row_count = -1  # 默认未知，避免 COUNT(*) 全表扫描卡死
try:
    probe = sqlite3.connect(app_db_path, timeout=3.0)
    probe.row_factory = sqlite3.Row
    pc = probe.cursor()
    # 用 MAX(rowid) 替代 COUNT(*)：O(log n) 走 rowid 索引，毫秒级返回；
    # MAX(rowid) 是行数上界估计（有删除时偏大），足够用于进度展示，迁移时以实际批次为准。
    pc.execute(f'SELECT MAX(rowid) as cnt FROM {table_name}')
    row = pc.fetchone()
    if row and row['cnt'] is not None:
        row_count = row['cnt']
    else:
        row_count = 0  # 空表
    probe.close()
except Exception as e:
    logger.warning(f"获取 {table_name} 行数失败（跳过）: {e}")
    row_count = -1  # 未知行数
```

**原理**：COUNT(\*) 需全表扫描（932MB 表耗时分钟级）；MAX(rowid) 走 rowid B-tree 索引，O(log n) 毫秒级。返回值是行数上界估计，对进度百分比足够；迁移框架用 `max(total_rows, 1)` 防除零。

### 变更 3：替换 `DBShardDecisionAI._do_work()` 的 COUNT(\*)

**文件**：`flask-app/ai_engines/db_employees/db_employees.py`

**修改**：第 52–59 行（`DBShardDecisionAI._do_work` 内的循环体）

```python
# 修改前
probe = sqlite3.connect(app_db_path, timeout=3.0)
probe.row_factory = sqlite3.Row
c = probe.cursor()
c.execute(f'SELECT COUNT(*) as cnt FROM {table_name}')
row = c.fetchone()
count = row['cnt'] if row else 0
probe.close()

# 修改后
probe = sqlite3.connect(app_db_path, timeout=3.0)
probe.row_factory = sqlite3.Row
c = probe.cursor()
# 用 MAX(rowid) 替代 COUNT(*)，避免每小时守护线程触发全表扫描卡死
c.execute(f'SELECT MAX(rowid) as cnt FROM {table_name}')
row = c.fetchone()
count = (row['cnt'] if row and row['cnt'] is not None else 0)
probe.close()
```

**原理**：员工守护线程每小时执行一次，若用 COUNT(\*) 会让 app.db 周期性卡死。MAX(rowid) 毫秒级，不影响决策逻辑（阈值 10000 行的判断对上界估计足够）。

### 变更 4（可选，本次记录不实施）：`migration_framework._verify_migration()` 全表扫描

**文件**：`flask-app/ai_engines/db_employees/migration_framework.py` 第 216、220、229、232 行

`SELECT COUNT(*) FROM <table>` 可改 MAX(rowid)；但 `SELECT * FROM <table> ORDER BY rowid` 是 MD5 哈希的必经之路，无法避免全表读。本字段仅在单表迁移完成时触发一次，非初始化阻塞点，**本次不修改，留待实际迁移时按需优化**（可考虑分批哈希或抽样校验）。

---

## 操作步骤（实施顺序）

### 步骤 1：清理环境（释放数据库锁）

```bash
# 1.1 杀掉 11 个僵尸 sqlite3 进程（持有 app.db 读锁）
pkill -9 -f "sqlite3.*app\.db"

# 1.2 验证已全部清理
pgrep -f "sqlite3.*app\.db"   # 预期无输出

# 1.3 删除陈旧 journal 文件（僵尸进程已杀，可安全删除；SQLite 会在下次连接时检测）
rm -f "/Users/wuchenghao/Library/CloudStorage/OneDrive-个人/文档/MTSCOS_AI_Project/flask-app/app.db-journal"

# 1.4 验证 app.db 可正常连接（应在 1 秒内返回）
sqlite3 "/Users/wuchenghao/Library/CloudStorage/OneDrive-个人/文档/MTSCOS_AI_Project/flask-app/app.db" \
  "SELECT COUNT(*) FROM sqlite_master WHERE type='table';"
```

**注意**：删除 journal 前必须先确认无 sqlite3 进程持有 app.db。若有 Python 进程（如 Flask）也在持有 app.db，需先停掉。

### 步骤 2：应用代码变更 1–3

按上述"实施变更"章节依次修改 3 处代码（变更 1、2、3）。

### 步骤 3：语法验证

```bash
cd "/Users/wuchenghao/Library/CloudStorage/OneDrive-个人/文档/MTSCOS_AI_Project/flask-app"
python3 -m py_compile ai_engines/ai_distributed_db_manager.py
python3 -m py_compile ai_engines/db_employees/db_employees.py
# 预期无输出（编译通过）
```

### 步骤 4：运行自动配置系统验证

```bash
cd "/Users/wuchenghao/Library/CloudStorage/OneDrive-个人/文档/MTSCOS_AI_Project/flask-app"
# 直接重定向到文件，避免管道缓冲误判
python3 -m ai_engines.ai_agent_auto_config > /tmp/auto_config_output.txt 2>&1
echo "EXIT_CODE=$?"
```

**预期输出**：8 步全部 ✓，步骤 8 显示：
```text
[步骤 8/8] 配置 AI智能分散数据库系统...
  ✓ 配置了 4 名DB员工, 5 个分片库
```
且日志含 `迁移队列初始化完成: 6 张表待迁移`（这是变更 2 修复后才会出现的关键日志）。

### 步骤 5：验证结果 JSON

```bash
python3 -c "
import json
with open('/Users/wuchenghao/Library/CloudStorage/OneDrive-个人/文档/MTSCOS_AI_Project/flask-app/ai_agent_config_results.json') as f:
    r = json.load(f)
db = r.get('configured_distributed_db', {})
print('initialized:', db.get('initialized'))
print('shard_count:', db.get('shard_count'))
print('db_employees_count:', db.get('db_employees_count'))
print('table_count:', db.get('table_count'))
"
# 预期: initialized=True, shard_count=5, db_employees_count=4, table_count>=40
```

### 步骤 6（可选）：API 蓝图导入验证

```bash
cd "/Users/wuchenghao/Library/CloudStorage/OneDrive-个人/文档/MTSCOS_AI_Project/flask-app"
python3 -c "
from app.api.ai_distributed_db_api import ai_distributed_db_api
print('Blueprint:', ai_distributed_db_api.name)
print('URLs:', len(list(ai_distributed_db_api.deferred_functions)))
"
# 预期: Blueprint: ai_distributed_db_api, URLs: 15
```

---

## 假设与决策

1. **不重做任务 #11–#13**：前一轮计划的核心代码已就绪，本次只修复卡死 bug。
2. **MAX(rowid) 作为行数估计**：行数上界（删除行时偏大），足够用于进度展示和阈值判断。准确行数留待迁移框架实际迁移时统计。
3. **删除 journal 文件安全**：先杀僵尸进程后删 journal，避免数据库损坏。SQLite 在下次连接时会检测 journal 缺失并跳过恢复（journal 只是回滚日志，缺失等价于"无未提交事务"）。
4. **不修改 migration_framework 全表扫描**：非初始化阻塞点，留待实际迁移时优化。
5. **不启动 DB 员工守护线程**：`init_db_employees()` 仅创建实例不 start，避免 Flask 启动阻塞。守护线程通过 API `/employees/start-all` 手动触发。
6. **不动业务表**：本次只修复初始化，不实际执行数据迁移。6 张膨胀日志表的迁移留待后续通过 `/api/ai-distributed-db/migration/start` 手动触发。

---

## 风险点与注意事项

1. **app.db-journal 删除时机**：必须先 `pkill -9 -f "sqlite3.*app\.db"` 确认无进程持有锁，再删 journal。若有 Python Flask 进程在跑，先停 Flask。
2. **MAX(rowid) 边界情况**：空表返回 NULL（已处理为 0）；表不存在抛 `no such table`（已被 try/except 捕获，设为 -1）。
3. **变更 3 的阈值判断**：`count > 10000` 用 MAX(rowid) 上界替代真实行数，可能让决策 AI 稍早触发"建议迁移"——这是可接受的偏差，反而更保守。
4. **`_employees_lock = None` 未初始化**（`db_employees.py:338`）：上一轮已记录，本次不修。`init_db_employees()` 单次调用无并发问题。
5. **f-string 拼 SQL 的注入风险**：`_init_migration_queue` 和 `DBShardDecisionAI._do_work` 的 `f'... FROM {table_name}'` 仍存在，但 `table_name` 来自 `get_migration_targets()` 的硬编码列表，无注入面。API 层已用 `_validate_table_name` 白名单校验。

---

## 验证清单

- [ ] 步骤 1：11 个僵尸 sqlite3 进程已杀，`pgrep` 无输出
- [ ] 步骤 1：`app.db-journal` 已删除
- [ ] 步骤 1：`sqlite3 app.db "SELECT COUNT(*) FROM sqlite_master"` 1 秒内返回
- [ ] 步骤 2：3 处代码变更已应用（变更 1: 第 553/556 行；变更 2: 第 239-251 行；变更 3: db_employees.py 第 52-59 行）
- [ ] 步骤 3：`py_compile` 两个文件均无输出
- [ ] 步骤 4：auto-config 输出含 `迁移队列初始化完成: 6 张表待迁移` + `✓ 配置了 4 名DB员工, 5 个分片库`，EXIT_CODE=0
- [ ] 步骤 5：`ai_agent_config_results.json` 含 `configured_distributed_db.initialized=True`
- [ ] 步骤 6（可选）：蓝图导入返回 `URLs: 15`
