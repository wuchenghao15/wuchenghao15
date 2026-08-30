# Spec: AI建议驱动的教辅同步/题库/听力题/母题/历年习题 扫描更新 + 智能修复 + 自动上传（flow_edu_bank_suggested）

## 背景
1. 用户要求：按 AI 建议自动扫描教辅同步、题库更新、听力题更新、接替母题更新、历年习题更新等功能，
   并配套自动智能修复及上传方案。
2. 既有资产：`ai_edu_sync_engine`（教辅同步）、`ai_suggested_repair_engine`（v22.4.0 修复引擎，含
   decide_action/repair_step/_compiles/_compile_error/_backup/_rollback）、隔离 git 仓
   `_runtime/git_push_ws/mtscos_push`（MTSCOS 分支）。
3. 建议池 `mt_patrol_eigenflux_suggestions` 持续产出教育域建议，无人消费。

## 需求
新引擎 `ai_suggested_edu_bank_engine.py`（daemon `sys_ai_edu_bank_suggested`，600s 轮巡，once 模式）六步闭环：
1. **ABSORB+REPAIR** 吸收教育域建议（关键词×4列 LIKE + 教育引擎文件名命中，按文件去重 FIFO），
   指向教育引擎 .py 的语法/缩进错误委托 `ai_suggested_repair_engine`（备份+验证+失败字节级回滚）
2. **SCAN 五域扫描更新**（决策核心为纯函数，全部真实数据）：
   - 教辅同步：`mt_edu_sync_log` 最新 synced_at 距今 >7 天 → 触发 `ai_edu_sync_engine.sync_all()`
   - 题库更新：从 `adult_education_questions`+`professional_exam_questions` 真实计数重算
     `question_bank_meta` + 写 `question_bank_inspection_logs`
   - 听力题更新：`jp_listening` 种子补全（AI_GENERATED 幂等）+ 存量行完整性检查 → 缺口建议落池
   - 接替母题：`mt_edu_sync_question_types` ACTIVE 母题 >30 天未更新 → 旧版 SUPERSEDED /
     新版 patch+1 ACTIVE / 解题步骤确定性重生成 + 接替记录写 `mt_edu_sync_log`
   - 历年习题：年份解析（严格 1980-2099 四位）→ `question_freshness_tracker`
     实数据填充（freshness=2^(-age/365d)）→ score<0.25 入 `question_outdated_tracking`
3. **UPLOAD** git 自动上传：本轮修复成功且编译验证通过的教育引擎文件 → 隔离仓 commit+push origin MTSCOS
4. **PERSIST** 落库：`mt_edu_bank_suggested_log` 明细 + `mt_ai_brain_feed_log` 投喂（列名 1:1：
   flow_id/feed_target/payload_preview/fed_at/fed_by）

## 安全约束（硬）
- 数据真实性：更新全部来源于真实计数/真实行变换；听力种子沿用 `AI_GENERATED` 惯例（内容自撰非虚构数据源）
- 上传范围仅 flask-app 内 .py 且不含 `_UPLOAD_SKIP_DIRS` 段；修复失败回滚后与原始字节一致
- 决策核心纯函数化（edu_domain_decision/freshness_score/freshness_action/parse_year/
  listening_row_complete/mother_succession_version/meta_recompute/upload_eligible），供 §14 千轮测试 AST 1:1 提取
- push 失败不阻塞落库；隔离仓未初始化时引擎不代建（防半初始化）

## 验收标准
- AC-1 引擎 once 模式单轮闭环跑通（吸收→五域扫描→修复→上传→落库）
- AC-2 五域扫描全部基于真实数据且幂等（重复运行不重复插入）
- AC-3 教育域建议吸收→修复→状态机收敛（FIXED/REPAIR_FAILED/STALE_CLOSED）
- AC-4 git 上传仅限 fixed+verified+.py，push 成功留 commit hash
- AC-5 1000 轮决策矩阵（400+300+300）AST 1:1 真源零漏洞
- AC-6 daemon 挂载成功（sys_ai_edu_bank_suggested，600s）

## 实跑证据
round `20260830_202715`：absorbed=0 fixed=0 domains_updated=8643
（edu_sync=38 / question_bank=104 / listening=3 / mother_question=0 / past_year=8498）
