---
name: "local-ai-cli"
description: "MTSCOS 本地 Ollama 零积分 AI 工具链(ai 命令/统一网关/流式进度/安全写回/白名单 git 操作)。当用户要在终端用本地 AI 对话、思考、生成代码、审查、自动修代码(ai act 加强版 code_fix: 写前验证+回滚, v22.18.0 起 ai fix 已并入 act)、只读运维操作(ai act: 同步/daemon状态/AI员工/日志/系统诊断/功能体检dev_audit)、同步 GitHub，或维护 ai 命令、local_ai_unified_gateway.py、ai_ollama_engine.py 时调用。"
---

# MTSCOS 本地 AI CLI 工具链 (零云端积分)

## 适用场景
- 用户想在**终端**用本地 AI（对话 / 思考 / 编码 / 审查 / Bug 定位 / 自动改代码 / 同步 GitHub），且不消耗云端积分。
- 维护或扩展本地 AI 工具：根目录 `ai` 脚本、`flask-app/ai_engines/local_ai_unified_gateway.py`、`ai_ollama_engine.py`、`local_ai_mcp_server.py`。
- 出现「ai 命令无输出 / 假卡死 / 模型路由到云端 / AI 写回文件污染 / git 同步卡住」等问题时按本技能排查。

## 核心文件
| 文件 | 职责 |
|------|------|
| `ai`（项目根，已入 PATH） | zsh CLI 入口，解析子命令并渲染表格/进度 |
| `flask-app/ai_engines/local_ai_unified_gateway.py` | 统一网关：路由、流式、进度、auto_fix、execute_task |
| `flask-app/ai_engines/ai_ollama_engine.py` | Ollama 引擎（chat/classify/review/bug_analyze，含 use_coder） |
| `flask-app/ai_engines/local_ai_mcp_server.py` | MCP 工具：local_ai_chat / _think / _code / _code_review / _bug_locate / _health |

## 模型与路由（极致本地优先，云端默认关闭）
- 本地模型（`ollama list`）：`qwen2.5:7b`（通用）、`qwen2.5-coder:7b`（编码）。
- 路由在 `_route_chat()`：**本地 Ollama（零 token）为唯一默认通路**；云端火山方舟 ark **默认禁用**，不"一失败就上云"。
- **本地瞬时失败重试**：本地在线但单次调用失败（模型冷启动/换模型/网络抖动）时，本地重试 `_LOCAL_MAX_ATTEMPTS=3` 次（退避 1.5s/4s，`_LOCAL_RETRY_BACKOFF`），吸收抖动后仍走本地，不再因此泄漏云端 token；成功结果带 `local_attempts`。
- **云端门控** `_cloud_fallback_enabled()`：仅当环境变量 `MTSCOS_AI_ALLOW_CLOUD=1/true/yes/on` 才允许云端应急；默认关闭时本地真不可用返回 `route=local_only_unavailable`、`cloud_blocked=true`、零云端 token，错误文案提示启动 Ollama 或临时开云。
- **命中率可观测**：`_ROUTE_STATS` 记 local/cloud/local_retry/blocked_cloud/none；`health()` 输出 `routing_stats`、`local_hit_rate`、`cloud_volcengine.fallback_enabled`，体检/诊断展示"云端兜底关闭(纯本地零token)"。
- `use_coder=True`（code/review/bug/optimize/auto_fix）自动选 `qwen2.5-coder:7b`；交互式 `ai chat/code/think` 走 `_ollama_stream`（纯本地流式），流式失败回退 `_route_chat`（同样受云端门控）。
- 应急：Ollama 起不来又必须出结果时，用户在**自己的 Terminal** `MTSCOS_AI_ALLOW_CLOUD=1 ai "..."` 临时上云；用完取消该变量。

## 本地模型规则约束层（`_PROJECT_RULES`，强制注入、无例外）
本地 7b 模型不懂项目规范，**必须**通过 system prompt 强制注入硬规则，否则会产出裸路由/假数据/硬编码颜色/越权链接。
- 常量 `_PROJECT_RULES`（对齐 `.trae/rules` 九篇规范）9 条：①路由必鉴权（`@system_container`/`_check_login`/`_check_admin`，禁裸路由）②带 `user_id` 端点必做归属校验防 IDOR（学生只访问本人、教职/SA 可跨查、`manual_adjust` 限教职）③SQLite 唯一数据源禁假数据 ④前端用 `var(--el-*)` 设计 Token 禁硬编码色 ⑤学生/前台页禁链 `/admin_app/*`（admin 命名空间）⑥AI 优先本地推理零 token ⑦4 空格/120 字符/Service 层/`{code,message,data,timestamp}` 统一响应/输入白名单校验 ⑧规则文档禁弱约束词（应该/建议/尽量…改必须/禁止）⑨大改动走 §14 十二步骤、规则改 7 步审批。
- 拼装助手 `_with_rules(system)` = 角色说明 + `_CODE_RULES`（只输出代码/禁 shell 指令）+ `_PROJECT_RULES`，**调用方无法豁免**。
- 已强制注入点：`code()`、`optimize_file()`、`auto_fix` 文件生成 `opt_system`（均 `_with_rules(...)`）；`review()` 在审查输入前注入 7 项规则审查清单并标记 `rules_enforced=True`。
- 维护：项目规范变更时同步改 `_PROJECT_RULES` 文本；新增代码类 AI 入口一律走 `_with_rules()`，禁止直接调 `_route_chat` 不带规则。规则文本与 `_audit_route_idor`/`_audit_template_links` 的静态审计互为双保险（prompt 约束 + 写回后审计）。

## ai 命令清单
```
ai "问题"                 # 对话(流式打字机)
ai think "问题"           # 深度思考(流式)
ai code "需求"            # 代码生成(coder模型,流式)
ai optimize <文件>        # 优化建议(前后对比表,不改文件)
ai optimize <文件> --write# 优化并写回
ai act "指令"             # 加强版一体化(v22.18.0): 运维+代码修复(code_fix意图→auto_fix), 见下表
ai act "修复 engines/x.py 的yyy"  # 改代码→AI定位+生成+写前验证+原子写回(失败自动回滚)
ai act "..." --dry-run    # 只预览将执行的步骤/修改, 不落地
# (v22.18.0 起 ai fix 已废除并入 ai act; 旧写法自动路由 act, 网关层 fix 命令仅兼容保留)
ai sync [--dry-run]       # 安全同步 GitHub(非强推)
ai pull / ai status       # 拉取 / 仓库状态
ai run "同步GitHub"       # 通用操作执行入口(等价 act 的白名单执行)
ai review "<代码>" / ai bug "<错误>" / ai health
```
注意：终端里不要粘贴 `#` 注释行（zsh 交互模式下 `#` 非注释符，括号会触发 glob 报错）。

### `ai act` 一体化边界（v22.18.0 起 fix 并入 act, 关键）
- **运维类意图**（查状态/看日志/体检/诊断/同步类）：AI 只做意图分类、**永不生成 shell**；越界需求（"写首诗"）被拒并引导（咨询→`ai chat`、方案→`ai think`、代码生成→`ai act "ai code ..."`）。
- **`code_fix` 意图（真改代码）**：请求含修复/改代码语义时 act 内部路由 `auto_fix`。AI 定位≤8文件→生成→**写前 ast/围栏校验→.tmp→os.replace 原子写回→失败自动回滚**，写回后跑 IDOR/越权链接静态审计；返回 `actually_modified_files`（真实落盘清单），`success=False` 且该列表为空=未发生任何代码修改。
  - **auto_fix 内部只有真正的操作执行型指令（git_sync/git_pull/git_status/run_tests/install_deps）才分流回 execute_task**；只读分析类意图（dev_audit/feature_expand/日志/员工统计等）**不劫持**改码流程——用户要求改码就真改码，绝不偷偷降级为只读。
- 开放式大需求（"完善学生功能/前端/后端/中间件"）走 `ai act "完善XX"`（dev_audit 只读体检）出带证据清单 → 再按 P0→P1→P2 逐条 `ai act "修复xxx"`。禁止一条修复盲改几十个文件（AI 上限 8 文件，见下文方法论）。

### `ai act` 支持的 13 类操作意图（OPERATION_INTENTS，零 token 本地分类）
| 意图 | 能力 | 副作用 |
|------|------|--------|
| `git_sync` | 同步/推送 GitHub（`--ff-only`、永不 force、排除 .bak） | 写 git |
| `git_pull` | 拉取远端最新 | 写 git |
| `git_status` | 查看仓库状态/变更 | 只读 |
| `run_tests` | 运行项目测试 | 只读(跑测试) |
| `install_deps` | 安装 requirements.txt 依赖 | 写环境 |
| `engine_health` | 本地 AI 引擎健康检查 | 只读 |
| `system_diagnose` | 系统性能诊断（磁盘/负载/内存/进程/AI引擎 + 优化建议） | 只读 |
| `feature_expand` | 系统功能拓展分析（盘点引擎/AI集/模型，AI 出扩充建议） | 只读 |
| `daemon_status` | 自动化 daemon 运行状态（PID 存活 + mt_daemon_registry） | 只读 |
| `ai_workforce` | AI 员工/EigenFlux 队伍统计（跨候选 app.db，不编数字） | 只读 |
| `view_logs` | tail 最新运行日志（_runtime/logs） | 只读 |
| `dev_audit` | 功能区体检与缺口分析（盘点 templates/routes/middlewares，AI 出 P0/P1/P2 任务清单，每条给 ai act 修复指令文案） | 只读 |
| `code_fix` | 代码修复/修改/重构（内部路由 auto_fix：定位→AI改码→AST校验→原子写回+备份回滚） | 写代码 |

意图识别双层：先**关键词确定性匹配**（`_detect_operation_intent`，零推理最可靠），未命中再走**本地 AI 分类**（`_ai_classify_intents`，Ollama 零 token，只认白名单动作）。新增意图=注册三元组（描述/口语关键词/规范指令串）+ 只读执行分支 + dry-run，详见 `ai-act-readonly-intent` 技能。


## 终端实时反馈约定（消除"假卡死"）
- 所有交互反馈走 **stderr**，机器可读结果（JSON）走 stdout；`ai` 脚本用 `RESULT=$(...)` 捕获 stdout，stderr 实时透传（**不要** `2>/dev/null` 吞掉进度）。
- 网关内 `_CLI` 开关：`main()` 调 `_prog_on()` 启用；MCP/程序导入时默认关闭（保持 JSON 干净）。
- 组件：`_banner()` 紫框头、`_stage()` 带时间戳阶段行、`_Spin` 上下文管理器（spinner+秒数，完成打印 ✓耗时）、`_Nodes` 节点清单跟踪器（v22.16.0 新增）、`_ollama_stream()` 直连 `http://localhost:11434/api/chat` 逐 token 流式。
- **`_Nodes` 节点清单**：多行实时渲染（仅TTY），`📊 [进度条] n/N · 待完成 x · 预计剩余 · 预计完成时刻` 头部 + 节点行（`✓已完成·耗时` / `⠙执行中·已用+剩~倒计时` / `○待执行·预估` / `✗失败` / `⤳跳过`）。节点元组 `(label, est秒, group)`；`ok()` 把实际耗时回写同组待执行节点预估（滚动ETA，缓存 `_NODE_EST_CACHE`）。嵌套（act→execute_task）时内层自动从属：不渲染、`log()` 上抛父级。非TTY只靠 `close()` 打印最终静态清单。`_stage/_banner/_Spin/_run_cmd` 在清单活跃时必须走 `_NODES.log()`（`_cli_log`），禁止直写 stderr 破坏重绘。
- chat/code/think 走 `_run_interactive()`：流式输出到 stdout，**不打印 JSON**；其余命令最后由 `ai` 脚本渲染结果表。
- 长耗时子进程（git/AI）必须包在 `_Spin` 里，禁止长时间无输出。

## 写回安全（防 markdown 围栏污染）
AI 常返回 ``````py ... `````` 包裹的代码。写回文件前**必须**剥离围栏：
- 优先用正则 `re.search(r"```(?:\w+)?\n(.*?)```", s, re.DOTALL)` 提取；
- **无收尾围栏时**也要逐行剥离首/尾独立围栏行（`lstrip().startswith("```")`）；
- 末尾 `strip("\n") + "\n"`。
- 教训：围栏或截断内容写进 `.py` 会导致 `SyntaxError: line 1 ```py`；auto_fix 写回前先 `shutil.copy2` 生成 `.bak`。
- **auto_fix 智能验证门（已内置，勿绕过）**：AI 生成代码不直接覆盖原文件，而是写 `.tmp` → 校验 → `os.replace` 原子替换：
  - `.py` 用 `ast.parse` 做语法校验（**不 import**，否则触发整应用初始化几百行日志）；其余类型查围栏污染（独立行 ```` ``` ````）。
  - 校验失败 → 删 `.tmp`、**原文件不动（自动回滚）**、记 `rolled_back:true`；dry-run 也跑同样校验提前暴露坏代码。
  - 返回 `verification{written_verified, rolled_back, dry_run_blocked, warnings, warning_items, all_verified}`；`success` 按"有写回通过 或 dry-run 有产物"判定，不再无脑 True。
  - 写回通过后跑**提示级静态审计**（不阻断）：`_audit_route_idor`（routes/ 下路由块按 `@` 装饰器边界切块，用到 `user_id` 但无 `_check_login/_check_admin/_is_staff/system_container/归属比较` 等任一标记 → 报疑似 IDOR）、`_audit_template_links`（student/portal 模板出现 `<a href="/admin_app/...">` → 报越权引导）。审计特征宁保守勿误报；新增鉴权写法时把标记加进 `_OWNERSHIP_MARKERS`。

## 白名单真实操作（execute_task）
- 意图识别用**关键词确定性匹配**（`_detect_operation_intent`，零推理，比模型分类可靠），支持 git_sync / git_pull / git_status / run_tests。
- 命令**只能来自固定模板**，AI 永不生成任意 shell；`subprocess.run(shell=False, cmd=[...])`。
- git 安全铁律：**永不 `--force`**；push 用 `git push -u MTSCOS HEAD`（自动建上游）；pull 用 `--ff-only`；add 用 `git add -A -- :!*.bak`（排除备份）。
- 提交信息由本地 AI 生成中文（50 字内）；失败路径必须填 `error` 字段，`main()` 全局 try/except 兜底，永不出空 JSON。

## `ai fix "完善XX"` 大需求：P0→P1→P2 逐级、证据驱动（勿一条盲改）
开放式需求（如"完善学生功能/前端/后端安全/中间件"）覆盖几十个文件，**禁止**让 auto_fix 一次盲改。正确链路：先 `ai act "完善XX"`（只读 `dev_audit` 意图）出带证据清单 → 人工/模型按下面三级小步落地，每级编译+冒烟后再进下一级：

- **P0 可用+安全（最高优先）**
  - 先让功能**真能跑**：导入模块 `python3 -c "import routes.x"` + `hasattr(m,'符号')` 查"函数只在某 helper 内定义、模块级从未绑定"的 NameError（典型：`_current_safe_user`/`_MT_ADMIN_ROLES` 只在 `_get_shared_funcs()` 内 import，模块级没绑定 → 该蓝图所有路由首行 NameError→500，整个子系统静默不可用）。修法：对齐兄弟路由文件，在模块级定义 `_current_safe_user()`（懒加载 server_real_db + session 兜底，返回 `uid/username/role/logged_in/is_super_admin`）。
  - 鉴权**别看装饰器计数**：`@system_container` 之外，助手式 `_check_login()`/`_check_admin()`（返回 `(False,(401/403,msg))`）也是真实鉴权；逐路由扫函数体前 14 行确认每个端点都有其一，别因"装饰器少"就重复加。
  - **IDOR 横向越权**：凡带 `user_id` 的端点（path 参或 body），除登录外必须校验"非教职只能访问本人"（`str(user.uid)==str(user_id)`，教职/SA 放行）；写操作里的人工调整类型（如 `manual_adjust`）限教职。加 `logger.warning` 审计。
- **P1 功能+真实数据（SSOT，禁止假数据）**：后端通了再把前端面板接到真实接口（`fetch` 本人数据，uid 用 Jinja `{{ user.user_id | tojson }}` 注入）；无档案/0 数据要温和提示（"暂无…，完成练习即可解锁"），**不编造数字**。
- **P2 前端体验**：一律用设计 Token（`var(--el-*)`），禁硬编码色；死链（路由 grep 不到）做成 `.disabled`"建设中"态而非跳 404；`/admin_app/*` 存疑链接无证据前不动；加 `@media(max-width:640px)` flex-wrap 防移动端溢出。
- **`/admin_app/<name>` 是管理员命名空间**（`server_real_db.py` 通配路由 `admin_app_pages`，装饰器 `@system_container(require_auth='admin')`，白名单 `unified_pages` 统一渲染 dashboard.html）。**学生/普通用户页卡片禁止链接 `/admin_app/*`**——非管理员访问会被 `redirect('/admin_app/login')`（越权引导到管理员登录页）。学生可用功能页应建在学生命名空间（如 `/student/*` 页面），数据源复用现成 API（`/api/exam/*`、`/api/k12/*` 这些都是 JSON API 非 HTML 页面，需另建学生 HTML 页承接）。判定页面 vs API：蓝图 `url_prefix=/api/...` 且无 `render_template` 的是纯数据接口。

**验证用 Flask test_client 越权矩阵**（比 py_compile 有力；设会话用 `c.session_transaction()`）：未登录→401、学生查自己→非 403/500、学生查他人→403、教师查他人→放行、学生手工调分/给他人加分→403。模板用 `jinja2.Environment().parse(src)` 验语法。
**证据纪律**：每条"已修复/无问题"必须对齐到具体文件/路由/测试结果；路由是否存在以 `grep route` 实测为准，不臆测；不确定的链接列为"待确认"而非改。

## 环境排查要点（本项目踩过的坑）
1. **OneDrive 沙箱**：`.git` 与 pack 在 OneDrive 上，Trae 沙箱内 git 读 2.7GB 云端 pack 会 `mmap failed: Operation timed out`。真正 push/pull/status 让用户在**自己的 Terminal**跑；`GIT_OPTIONAL_LOCKS=0`。
2. **卡死 git 进程**：`sys_git_sync` daemon（`ai_smart_mount_engine.py`）每 300s 调 `sync_github.sh push`；旧脚本用 `git push --force` 且 remote 名错误（`origin` 不存在，实际为 `MTSCOS`），在 OneDrive 上挂成 D 状态、`timeout` SIGKILL 无法回收，堆积并持锁。处置：可逆改名禁用脚本（`sync_github.sh`→`.disabled`，引擎检测到缺失只记日志）；精确 PID `kill -9`（批量 pkill/pkill -f 易误杀执行 shell 自身，用 `comm`/全路径匹配 + 纯数字 PID 列表）；删除陈旧 `.git/index.lock`、`.git/refs/.../*.lock` 前确认无 git 进程。
3. **ps/grep 中文与反引号**：脚本里避免裸反引号；`ps` 输出含非 UTF-8 字节用 `errors="replace"`；`LC_ALL=C` 规避 awk 多字节错误。
4. **macOS 无 `timeout` 命令**；OneDrive 上删除大云端占位文件用 Python `os.unlink`（shell rm/find -delete 可能卡住）。
5. 网关导入引擎必须 `except Exception` 降级为 None，引擎文件损坏不让整个网关崩溃。

## 修改后验证
- `python3 -m py_compile local_ai_unified_gateway.py ai_ollama_engine.py`；`bash -n ai`。
- 用 /tmp 小仓库做端到端：`ai fix "同步GitHub" --project-root /tmp/x`（bare remote 验证 add→commit→push 真实生效、.bak 被排除）。
- 扫描全目录 `.py` 首行围栏：`首行.lstrip().startswith("```")` 即损坏。
