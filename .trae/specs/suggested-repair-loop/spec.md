# Spec: AI建议驱动的扫描检测轮巡 + 智能修复 + 自动上传（flow_suggested_repair）

## 背景
1. `mt_patrol_eigenflux_suggestions` 积压 **11920 条 PENDING** 建议（deep_inspection/巡逻队持续产出，
   含大量已确认的 `syntax_error` / `indentation_error`），无人处理。
2. `auto_patrol_engine.py` 已有修复能力（缩进/括号/模式修复 + 写后验证），但没有对接建议表、
   修复后没有 git 自动上传 —— 闭环断在「建议吸收 → 修复 → 上传」。
3. 隔离 git 仓 `_runtime/git_push_ws/mtscos_push`（MTSCOS 分支）已稳定运行（flow 交付均走此通道）。

## 需求
新引擎 `ai_suggested_repair_engine.py`（daemon `sys_ai_suggested_repair`，600s 轮巡，once 模式）六步闭环：
1. **ABSORB** 吸收建议：PENDING 按 quality_score DESC 限量（100/轮），防积压无限重扫
2. **DECIDE** 处置决策（纯函数）：路径安全 → Python 文件 → 类型白名单 → 质量门槛 → fix
3. **VERIFY_FIRST** 现场复核：py_compile 已通过 → 建议过时 `STALE_CLOSED`（不修）
4. **FIX+VERIFY** 智能修复：复用 AutoPatrolEngine 修复策略；修复前磁盘备份；验证失败必须回滚
5. **UPLOAD** 自动上传：本轮 fixed 文件复制到隔离仓 commit+push（MTSCOS 分支）
6. **PERSIST** 落库：建议状态更新（FIXED/REPAIR_FAILED/STALE_CLOSED/SKIP_NONFIXABLE）+
   `mt_suggested_repair_log` 明细 + 脑库投喂

## 安全约束（硬）
- 修复范围仅 `flask-app/**/*.py`；SKIP：Database_Backups/recovery_snapshots/backups/git_push_ws 等
- 修复前备份（`_runtime/suggested_repair_backups/<round>/`），验证失败必须回滚
- 上传仅含本轮 fixed+verified 文件；push 失败不阻塞落库（FIXED_NOT_UPLOADED 由 log 区分）
- 决策核心为纯函数 `decide_action(finding_type, quality_score, path)`，1:1 真源千轮测试

## 验收标准
AC-1 引擎 once 模式单轮闭环跑通（吸收→决策→修复/关闭→上传→落库）
AC-2 建议状态正确更新，不再无限重扫
AC-3 备份与回滚验证通过（失败场景回滚后文件与原始一致）
AC-4 git 上传成功（隔离仓 commit hash 落库）
AC-5 1000 轮决策矩阵（400+300+300）零漏洞
AC-6 daemon 挂载成功且心跳正常
