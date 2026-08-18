---
name: "ai-act-readonly-intent"
description: "向 ai act 安全新增只读操作意图的标准流程(注册三元组+只读执行分支+双层意图验证)。当用户反馈 ai act 无法识别某操作、要给 act/execute_task 增加白名单动作(查看/诊断/统计/同步类, 非改代码)时调用。"
---

# ai act 新增只读操作意图标准流程 (MTSCOS)

配套 `local-ai-cli`（工具链总览）。本技能只覆盖一件事：**让 `ai act "XXX"` 能识别并安全执行一个新的操作型指令**。

## 触发场景
- 用户运行 `ai act "XXX"` 返回「未识别的操作意图」，但该操作属于**非代码修改类**（查看状态/统计/诊断/日志/同步等）。
- 用户要求给 `ai act` / `execute_task` 增加新的白名单动作。
- 边界判断：**写代码/改源码类需求不走本流程**（只读意图注册），代码修复走 `code_fix` 意图→auto_fix、代码生成用 `ai act "ai code ..."`。`ai act` 本流程只承载**只读**或固定白名单副作用操作。（v22.18.0 起 `ai fix` 已废除并入 `ai act`）

## 核心文件
- `flask-app/ai_engines/local_ai_unified_gateway.py`
  - `OPERATION_INTENTS`：意图注册表（约 L712）
  - `_detect_operation_intents()`：关键词确定性匹配（零推理）
  - `_ai_classify_intents()`：本地 Ollama 意图分类（零 token，只从注册 ID 选，永不生成 shell）
  - `_execute_task_impl()`：动作执行分支
  - `act()`：CLI `ai act` 入口（关键词→AI分类双层，已接线，勿绕过）

## 五步流程

### 1. 注册意图三元组（OPERATION_INTENTS）
结构为 `intent_id: (动作描述, 关键词列表, 规范指令串)`：
- **动作描述**：给 AI 分类器和用户看，标明「(只读:…)」与副作用边界。
- **关键词**：确定性匹配用，覆盖口语变体（如「电脑卡/电脑有点卡/电脑卡顿」「看日志/查看日志/最近日志」）；去重，勿与既有意图关键词撞车（撞了会链式误触发）。
- **规范指令串**：`act()` 会把它传给 `execute_task` 二次识别，**必须内含能被关键词命中的词**，否则内层识别不到。

### 2. 在 _execute_task_impl 加执行分支
位置：非 git 动作区（`engine_health` / `system_diagnose` / `feature_expand` 等同级），**插在「===== 以下为 git 仓库类动作 =====」注释之前**。

分支骨架（照抄结构）：
```python
if intent == "your_intent":
    if _CLI:
        _banner("🔍 中文标题", "全程只读(零副作用)", "副标题")
    nd = _Nodes("节点清单标题", [("节点1", 预估秒, "group1"), ("节点2", 预估秒, "group2")])
    nd.start()
    try:
        if dry_run:
            nd.skip_pending("dry-run 预览")
            plan("[只读] 计划动作A", "[只读] 计划动作B")   # 只登记不执行
            return result
        _ae_dir = os.path.dirname(os.path.abspath(__file__))  # 必须在使用前定义!
        nd.run(0)
        steps.append({"cmd": "[只读] 动作A", "ok": True, "rc": 0, "output": "真实数据"})
        nd.ok(0, note="小结")
        # ... 更多节点
        result["success"] = True
        return result
    finally:
        nd.close()
```

### 3. 安全红线（违反即返工）
- **只读铁律**：新增意图默认只读；任何删除/修改/启停/推送类副作用必须是独立意图且命令走固定白名单模板，AI 永不生成原始 shell。
- 子进程一律 `_run_cmd(["cmd", "arg"], repo_root, timeout=N)`（数组形式，禁 shell 字符串拼接）。
- 数据库**只读 SELECT**；表/库可能不存在，逐表 try/except 跳过，**禁止编造数字**（表不存在就标 N/A，不猜）。
- 数据可能分散在多个库：`ai_engines/app.db`、`engines/app.db`、`core/app.db`；跨候选库汇总。
- runtime 目录有多个（`repo/_runtime`、`repo/flask-app/_runtime`、`ai_engines/../_runtime`），全部探测。
- 状态列名容错：先 `PRAGMA table_info(表)` 取列，再按候选名（`current_state`/`status`/`state`）匹配。
- 失败路径必须 `result["error"]` 有值；分支内异常让 `act()` 全局 try/except 兜底，永不出空 JSON。

### 4. 兜底链路确认（三处）
关键词匹配不到时，本地 AI 分类（零 token）必须能兜住。新增意图后确认这三处都会落到 `_ai_classify_intents`：
- `act()`：关键词空 → AI 分类（已内置，无需改）。
- `_execute_task_impl()` 开头：关键词空 → AI 分类 → 仍空才报「未识别」。
- `auto_fix()` 分流点：操作类指令要分流到 execute_task，关键词空时同样先 AI 分类。
未命中报错的 `hint` 要可操作：提示换说法 + 引导 `ai chat`（咨询）/`ai think`（方案）/`code_fix` 修复指令·`ai act "ai code ..."`（改代码）。

### 5. 验证（四层，缺一不可）
1. 编译：`python3 -m py_compile local_ai_unified_gateway.py`。
2. **关键词识别冒烟**：对全部意图各造一个关键词用例，`_detect_operation_intent()` 必须 100% 命中（防回归/防撞车）。
3. **纯自然语言 AI 分类**：造一个**不含任何关键词**的口语句子（如「帮我看看后台进程都活着没」），验证 `_ai_classify_intents()` 能选出新意图（走 Ollama，需本地模型在线）。
4. **端到端**：`python3 local_ai_unified_gateway.py act "..."` 先 `--dry-run` 再真实执行。
   - CLI 输出含节点清单渲染行，解析时从第一个 `{` 起做 JSON decode（输出落盘再解析，勿直接 pipe 给 json.load）。
   - 断言 `success=True` 且 steps 里是真实数据。

## 本项目踩过的坑（新增时直接规避）
- `UnboundLocalError: _ae_dir`：分支里用了 `_ae_dir` 但在本分支没定义（别的分支定义的变量不共享）——分支内自己 `os.path.dirname(os.path.abspath(__file__))`。
- **解析型意图必须传用户原文**：`act()` 默认把 `OPERATION_INTENTS[intent][2]` 规范指令串传给 `execute_task`（如 dev_audit 的"功能区体检与缺口分析"），这会丢失用户原文里的目标参数（如"**学生**功能"里的"学生"）。凡是需要从用户原话解析参数（目标模块/文件名/范围）的意图，在 `act()` 的动作循环里改为传原文：
  `_exec_text = request if intent == "your_intent" else canonical` 再 `execute_task(_exec_text, ...)`。典型例：`dev_audit`（功能区体检）靠原文识别"学生/考试/教育"等模块关键词。
- **开放式"全面完善/优化XX"走只读审计，不直接改码**：用户说"完善XX所有功能/前端/后端安全/中间件"是大范围开发任务，`ai act` 对此不落地改代码，而是出**只读缺口报告 + 任务清单**（每项给可执行的 `ai act "修复xxx"` 文案），落地逐条由用户授权执行 `code_fix`（auto_fix）。对应意图 `dev_audit`（关键词：完善/补齐/功能体检/缺口分析/前端显示/后端数据安全/中间件功能）。审查结论必须基于真实扫到的文件（模板数/路由数/权限装饰器覆盖），不编造未读到的文件。
- 关键词缺口：口语副词变体（"电脑有点卡""改了啥"）要补全；同一意图内关键词去重。
- OneDrive 上文件可能有同步延迟，改完立即测偶发读到旧内容；以磁盘文件最终编译结果为准。
- `engines/` 下的巡检 daemon（deep_inspection / auto_patrol）会自动改源码；它们的"未使用导入注释"修复器已加固为"临时文件编译验证通过才原子替换"，新增意图代码若含多行括号 import 不会再被它改坏（它会跳过多行/`__future__` 导入）。
- 全意图回归：新增后对**每个**意图各造一个关键词用例跑 `_detect_operation_intent()`，确认新意图关键词不与既有意图撞车（撞了会链式误触发）。
