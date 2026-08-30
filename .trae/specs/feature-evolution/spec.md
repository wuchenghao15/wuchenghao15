# Spec: AI建议+模拟环境 功能演进轮巡（flow_feature_evolution）

## 背景
1. 用户要求：按 AI 建议 + 模拟环境加入轮巡，自动更新、完善和拓展系统所有未完善或未开发功能，
   并配套自动智能修复及上传方案。
2. 既有资产：`simulation_sandbox_engine`（多智能体模拟磋商，GAP_PROPOSAL 场景，确定性 seed，
   单轮 0.1s，落库 mt_sandbox_*）；`ai_suggested_repair_engine`（v22.4.0 语法/缩进修复专属）；
   隔离 git 仓（MTSCOS 分支）；建议池 mt_patrol_eigenflux_suggestions。
3. 现状盘点：flask-app 73 处未完成标记（15 文件）；5 个顶层包缺 `__init__.py`；引擎与 daemon
   命名不一致导致部分引擎未被识别为已挂载。

## 需求
新引擎 `ai_feature_evolution_engine.py`（daemon `sys_feature_evolution`，900s 轮巡，once 模式）六步闭环：
1. **ABSORB** 吸收+真实扫描：未完成标记（TODO/FIXME/XXX:/NotImplementedError/占位）+ 未挂载引擎
   检测（归一化双侧匹配，剥离 ai/sys 前缀与 engine 后缀）+ 缺失 `__init__.py` 包检测；
   陈旧 ENGINE_MOUNT 建议自动收敛（SKIPPED_STALE）
2. **SIMULATE 模拟环境磋商**：复用 simulation_sandbox_engine 跑 GAP_PROPOSAL 场景（seed=轮次哈希）
   → 共识分（实测 0.843/0.962）
3. **EVOLVE 完善/拓展**：决策核心 `evolve_decision(consensus, require, category)` 纯函数；
   共识达标 → 确定性完善沙盒先行（缺失 `__init__.py` 创建）；拓展建议（FEATURE_EXPAND，
   带行号+完善方向）与挂载建议（ENGINE_MOUNT，可被 smart_mount AI_SUGGESTION 流水线消费）落池
4. **VERIFY**：沙盒 py_compile + import smoke（子进程 30s 超时）
5. **UPLOAD**：验证通过 → 备份正本 → promote → 隔离仓 `add -f` + commit + push origin MTSCOS
6. **PERSIST**：`mt_feature_evolution_log` 明细 + `mt_ai_brain_feed_log` 投喂（列名 1:1）

## 安全约束（硬）
- 语法/缩进修复归 v22.4.0 引擎专属，本引擎不重复消费该两类建议
- 所有写动作沙盒先行（`_runtime/feature_evolution_sandbox/<round>/`），验证通过才 promote；
  promote 前备份原文件；备份字节不一致跳过
- 上传白名单：仅 flask-app 内 .py 且不含 SKIP 目录段；git add -f（隔离仓 gitignore 含 flask-app/*）
- 建议落池 uid 幂等（advice_uid 哈希去重）；引擎扫描跳过自身文件防自引用
- push 失败不阻塞落库

## 验收标准
- AC-1 once 单轮闭环跑通（吸收→模拟→演进→验证→上传→落库）
- AC-2 真实扫描 + 幂等（重复运行不重复落池/补全；mounted 误报自动收敛）
- AC-3 模拟环境磋商产出共识分并驱动 evolve/suggest_only 决策
- AC-4 沙盒先行 + 备份 + promote 白名单（promote_ok 拒绝非法备份状态）
- AC-5 1000 轮决策矩阵（400+300+300）AST 1:1 真源零漏洞
- AC-6 daemon 挂载成功（sys_feature_evolution，900s）

## 实跑证据
- round `20260830_205729`：candidates=75(expand=34/mount=39/init=2) consensus=0.843
  promoted=2(缺失__init__.py) uploaded=2 commit=3a72fce（已推送）
- round `20260830_205903`：candidates=49(expand=34/mount=15/init=0) closed_stale=24
  consensus=0.962 幂等验证通过
