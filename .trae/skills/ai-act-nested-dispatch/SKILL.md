---
name: "ai-act-nested-dispatch"
description: "向 ai act 新增可递归嵌套子命令(ai fix/chat/code/think/act/run/sync 等指令套指令)的标准流程: 白名单子命令+正则标记+分发映射+真实产出注入+深度护栏+看板命名。当用户要求 ai act 能递归调用别的 ai 子命令、或反馈 ai act 里写 'ai XXX' 不生效时调用。"
---

# ai act 递归嵌套分发新增标准流程 (MTSCOS)

配套 `local-ai-cli`（工具链总览）与 `ai-act-readonly-intent`（新增白名单只读**运维动作**）。
本技能覆盖另一件事：**让 `ai act "..."` 里能嵌套 `ai <子命令>` 并真实分发执行（非模拟）**，即"指令套指令"的递归能力。

> **v22.18.0 变更**：`ai fix` 子命令已废除并入加强版 `ai act`（`code_fix` 意图内部路由 `auto_fix`）。
> 嵌套写法 `ai fix ...` 仍兼容（`_NESTED_SUBS`/`_NESTED_CMD_RE` 保留 `fix`，分发到同一 auto_fix）；
> 新文档/新提示一律写 `ai act "修复xxx"`。

## 边界判断（先分流，勿走错流程）
- 要加的是**只读/固定副作用运维动作**（daemon状态/看日志/统计/诊断）→ 走 `ai-act-readonly-intent`（改 `OPERATION_INTENTS` + `_execute_task_impl` 分支）。
- 要让 act 里**调用已有的网关入口函数**（改代码/对话/思考/同步/分析）→ 走本流程（改嵌套分发链）。
- 两者可共存于一条指令：`ai act "看daemon状态, 然后 ai fix 完善 engines/x.py"` = 一个 op 动作 + 一个嵌套 ai 子命令。

## 触发场景
- 用户写 `ai act "ai fix ..."` / `ai act "ai chat ..."` 希望 act 递归执行子命令而非报"未识别"。
- 需要把一个新的网关入口（如 `review`/`analyze`/未来新函数）开放为可嵌套子命令。
- 用户强调"真实落实 act 要求，不要模拟"。

## 核心文件与锚点（local_ai_unified_gateway.py）
- `_NESTED_SUBS`（约 L1125）：可嵌套子命令白名单集合。
- `_NESTED_CMD_RE`（约 L1128）：匹配 `ai <sub>` 标记的正则，**要求 ai 后有空白再跟英文子命令+词边界**（避免误伤"ai员工/ai状态"等中文词）。
- `_MAX_ACT_DEPTH = 3`（约 L1132）：嵌套 `ai act` 最大递归深度。
- `_parse_nested_steps()`（约 L2041）：把请求解析为有序步骤 `("ai", sub, text)` / `("op", intent, seg)`。
- `_clean_nested_text()`（约 L2075）：清连接词（然后/再/接着…）首尾。
- `_dispatch_nested()`（约 L2094）：子命令→网关函数的真实分发映射 + 深度护栏。
- `_inject_nested_step()`（约 L2138）：把子命令真实产出落为一条 step（看板可见/可追溯）。
- `_run_nested_act()`（约 L2168）：递归执行路径（动态节点 + 失败即停 + 空指令跳过）。
- `act()`（约 L2258）：入口，开头检测 `_NESTED_CMD_RE.search(request)` 命中即走 `_run_nested_act`，带 `_depth` 参数。
- 看板：项目根 `ai`（bash 包装脚本）里 act 分支的 `names` 字典与 `route` 标签。

## 六步流程（新增一个可嵌套子命令）

### 1. 注册白名单与正则（两处都要加，缺一不识别）
- `_NESTED_SUBS` 集合加入子命令名，如 `"review"`。
- `_NESTED_CMD_RE` 的交替组 `(fix|optimize|code|chat|think|act|run|sync|analyze|compile|review|classify)` 同步加入该名。
- 子命令名必须是**英文 token**（正则靠 `ai\s+<token>\b` 匹配，中文不进此链）。

### 2. 在 _dispatch_nested 加真实分发分支
照抄既有结构，**真实调用对应网关函数，禁止打印"将执行"类模拟话术**：
```python
if sub == "review":
    return review(text, flow_id=flow_id)
```
- `fix` → `auto_fix(text, "", dry_run, flow_id)`：project_root 传 `""` 让其自动定位 flask-app（显式相对路径才解析得到）。
- `optimize` → `optimize_file(text, write_back=not dry_run, flow_id=flow_id)`：dry_run 时不写回。
- `chat/code/think/analyze/compile/review/classify` → 直接转发，注意被调函数签名（多数收 `flow_id=` 关键字）。
- `run` → `execute_task(text, repo_root, dry_run, flow_id)`；`sync` → `execute_task("同步GitHub", ...)`。
- `act` → 递归 `act(text, repo_root, dry_run, flow_id, _depth=depth+1)`，**进入前先判深度护栏**。
- 未知 sub：返回 `success:False` + `error:"不支持的嵌套子命令: ai <sub>"` + 可用列表 hint。

### 3. 深度护栏（递归 act 专属，不可省）
```python
if sub == "act":
    if depth >= _MAX_ACT_DEPTH:
        return {"success": False, "kind": "act",
                "error": f"递归深度超过上限({_MAX_ACT_DEPTH}), 已停止嵌套 'ai act' 以防无限递归"}
    return act(text, ..., _depth=depth + 1)
```
- 护栏判在**分发层**（`_dispatch_nested`），depth=3 直接拒绝、depth=2 才递归为 3。

### 4. 真实产出注入 _inject_nested_step
嵌套子命令本身不带 shell `steps`，必须把其**真实结果**落为一条 step 供看板展示/落库追溯：
- `chat/think/code`：取 `response`（真实模型回答/生成）。
- `fix`：非 dry_run 取 `actually_modified_files`（真实落盘文件清单）；dry_run 取 `verification` 预览。
- `analyze/compile/review/classify`：取 `response`/`summary`。
- `act`：取 `executed` 列表。
- `run/sync/optimize`：若已有真实 shell steps 则**不重复注入**，否则补错误/结论。
- step 结构：`{"cmd": f"ai {sub} {text[:40]}", "ok": success, "rc": 0/1, "output": 产出[:500]}`。

### 5. 空指令与解析健壮性（_run_nested_act / _parse_nested_steps）
- 叠写 `ai act ai act xxx` 会被扁平解析，外层 `ai act` 文本为空：循环里 `if not sub_text.strip(): nd.ok(...); continue` 跳过，不报错。
- 连接词清理要同时处理**尾部**（`ai fix A 然后 ai chat B` 中 fix 文本尾部残留"然后"）：`_clean_nested_text` 循环剥首/尾连接词与标点。
- 首个嵌套标记前的自由文本也要 `_emit_ops()` 识别运维动作（支持"先看状态，再 ai fix"混合链）。

### 6. 看板适配（项目根 ai bash 脚本）
- act 分支渲染 Python 里 `names` 字典加入 `ai_<sub>` 中文/图标名（如 `'ai_chat':'💬 ai chat 本地对话'`）。注意：分发后 `r["intent"]` 被设为 `f"ai_{sub}"`。
- `route` 标签识别 `routed_by == 'nested_recursive'` 显示"递归指令链(真实分发)"。

## 安全红线（违反即返工）
- **AI 永不生成任意 shell**：子命令是固定白名单，参数文本只交给对应网关函数；副作用命令仍走 `execute_task` 的固定模板。
- **真实执行，非模拟**：默认 `dry_run=False` 时 fix 真落盘（auto_fix 自带 .tmp→ast 校验→os.replace 原子替换→失败回滚）、sync 真 git；只有 `--dry-run` 才预览，且 dry_run 必须一路透传到嵌套 fix/optimize。
- **深度护栏不可绕过**：嵌套 act 必须 +1 并在 `_MAX_ACT_DEPTH` 截断。
- 失败即停：任一步骤失败 `nd.skip_pending` + break，不继续后续。
- 模块级需 `import re`（正则常量在模块加载时编译，函数内 `import re` 不够）。

## 验证（五层，缺一不可）
1. 编译：`python3 -m py_compile local_ai_unified_gateway.py`。
2. **解析器单测**：`_parse_nested_steps()` 对 `ai chat 你好` / `看daemon状态, 然后 ai fix ...` / `ai fix A 然后 ai chat B` 输出正确步骤序列；且 `ai员工多少` 等中文**不误判**为嵌套（应走 op）。
3. **护栏/分发单测**（用 monkeypatch 桩替 auto_fix/chat/execute_task，桩签名收 `**kw`/`flow_id=`）：
   - 混合链真实分发：断言 fix 收到 `dry=False` 且文本正确、chat 被调用、op 走 execute_task。
   - dry_run 透传：`_run_nested_act(..., dry_run=True)` 时 fix 收到 `dry=True`。
   - 深度：`_dispatch_nested('act', ..., depth=3)` 返回失败且 error 含"递归深度"；`depth=2` 递归调用 act 且 `_depth=3`。
   - 未知 sub 返回失败。
4. **端到端**：`./ai act "ai chat 用一句话回答:1加1等于几"`，输出重定向到文件再解析（CLI 有节点清单动画，勿直接 pipe 给 json.load）；断言看板显示真实回答、路由="递归指令链(真实分发)"。
5. 混合链 E2E：`./ai act "查看daemon状态, 然后 ai chat ..."` 断言 2/2 完成，op 读到真实库数据、chat 有真实回答。

## 管道模式（v22.19.0 新增）

**语法**：`ai act "ai 'XXX'"` 或 `ai act 'ai "XXX"'`

**两阶段执行**：
1. **阶段1**：`ai 'XXX'` → 调用 `chat()` 产出简洁指令（≤20字，用专门的 system prompt 约束）
2. **阶段2**：把阶段1产出当新 request 递归调用 `act()` 真实执行

**实现要点**：
- 新增正则 `_AI_PIPE_RE = re.compile(r'ai\s+[\'"]([^\'"]+)[\'"]', re.IGNORECASE)` 匹配引号包裹的 ai 指令
- 在 `act()` 入口处优先检测管道模式（在嵌套分发 `_NESTED_CMD_RE` 之前）
- 阶段1 system prompt：要求输出简洁指令（≤20字），用关键词而非完整句子，查看/统计类用动词开头，修复类用"修复"开头
- 两阶段步骤合并到最终结果，返回 `pipe_mode=True` 和 `pipe_stage1` 字段供追溯

**优先级**：`_AI_PIPE_RE` 检测在 `_NESTED_CMD_RE` 之前，因为 `ai 'XXX'` 是引号包裹的特殊形式，不同于 `ai chat XXX` 等子命令嵌套

**示例**：
```bash
# 阶段1产出"查看仓库状态"，阶段2识别为 git_status 并真实执行
./ai act "ai '查看仓库状态'"

# 阶段1产出"同步GitHub"，阶段2识别为 git_sync 并真实执行
./ai act "ai '同步代码到GitHub'"
```

**注意**：避免阶段1产出大段 markdown 说明导致阶段2意图识别混乱，必须用专门的 system prompt 约束产出简洁。

## 本项目踩过的坑（直接规避）
- `NameError: re`：`_NESTED_CMD_RE` 在模块级 compile，必须文件顶部 `import re`，不能只靠各函数内的局部 `import re`。
- `plan_result` 未定义：auto_fix 走显式路径分支不经过 AI 定位时，引用 `plan_result` 会 `UnboundLocalError/AttributeError: NoneType`。分支前先 `plan_result = None`，返回处用 `plan_result.get(...) if plan_result else ""`。
- 测试桩签名：网关函数多收 `flow_id=`/`project_root=` 关键字，桩用 `def fake(text, *a, **kw)` 否则 `TypeError: unexpected keyword argument`。
- 尾连接词残留：只清首部会让 `ai fix A 然后 ...` 的 fix 文本变成 `"A 然后"`，必须首尾都清。
- 叠写空 act：`ai act ai act xxx` 扁平解析后外层 act 文本为空，直接分发会报"未识别操作意图"；空文本步骤要跳过。
- 看板不显示嵌套产出：嵌套子命令无 shell steps，若不 `_inject_nested_step`，看板只显示动作名不显示真实回答/落盘文件。
- OneDrive 同步延迟：改完立即测偶发读旧内容，以磁盘最终编译结果为准；E2E 输出落盘再解析。
- 管道模式阶段1产出啰嗦：未用专门的 system prompt 约束时，阶段1产出大段 markdown 说明，导致阶段2意图识别出多个动作。必须用 system prompt 要求输出简洁指令（≤20字，关键词形式）。
