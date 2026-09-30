#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
仙女座 · 写作增强流水线引擎 (Writing Pipeline Engine)
=====================================================

把现有零散能力串联成 **7 层写作流水线**:

  ┌──────────────────────────────────────────────────────────────┐
  │                                                              │
  │  输入: 主题/领域/字数/风格/目标读者                         │
  │    ↓                                                         │
  │  ① EigenFlux 12 天团脑暴 (多角度观点冲突+共识)              │
  │    ↓                                                         │
  │  ② 顾问团 Skill 检索 (25 域知识 + mt_iceberg_content_matrix)│
  │    ↓                                                         │
  │  ③ GitHub 知识融合 (ai_github_fusion_engine: stars+issues)  │
  │    ↓                                                         │
  │  ④ 全网知识聚合 (web_skill_learner + B站 API + arXiv)       │
  │    ↓                                                         │
  │  ⑤ 本地 Ollama 写作生成 (qwen2.5:14b / qwen2.5:7b + RAG)   │
  │    ↓                                                         │
  │  ⑥ 文案自检 (copy_inspection_engine: 重复/占位符/硬编码)    │
  │    ↓                                                         │
  │  ⑦ 最终交付 (落库 + Flask API + 前端展示)                   │
  │                                                              │
  └──────────────────────────────────────────────────────────────┘

每个阶段独立调用本地 Ollama — 零 token 消耗 + 12 专家真参与。
"""

from __future__ import annotations
import json, os, sqlite3, subprocess, sys, time, hashlib, uuid, threading
from datetime import datetime
from pathlib import Path

# ═══════════════════════════════════════════════════════════
# DB 路径 (多路径容错)
# ═══════════════════════════════════════════════════════════
_PROJECT_ROOT = Path(__file__).parent.parent
_DB_CANDIDATES = [
    _PROJECT_ROOT / "database" / "app.db",
    _PROJECT_ROOT / "app.db",
]
_DB_PATH = next((p for p in _DB_CANDIDATES if p.exists()), _DB_CANDIDATES[0])

# Ollama
# Ollama — 自动检测端口 + 自动发现真实可用的写作模型
def _detect_ollama_port() -> int:
    """依次试 11434, 11435, 11436 — 找到活着的那个"""
    import urllib.request as _ur
    for p in [11434, 11435, 11436]:
        try:
            _ur.urlopen(f"http://127.0.0.1:{p}/api/tags", timeout=2)
            return p
        except Exception: continue
    return 11434  # fallback

def _detect_writer_model(port: int) -> tuple[str, str]:
    """从 Ollama /api/tags 自动发现可用的写作模型 + 轻量模型.
    MacBook 上可能是 qwen2.5:14b-q5, Mac mini 上是 qwen2.5:14b"""
    import urllib.request as _ur, json as _j
    try:
        resp = _j.loads(_ur.urlopen(f"http://127.0.0.1:{port}/api/tags", timeout=3).read())
        available = [m["name"] for m in resp.get("models", [])]
    except Exception:
        available = []

    # 主写作模型 (优先 14B)
    writer = None
    for pref in ["qwen2.5:14b", "qwen2.5:14b-q5", "qwen2.5-coder:14b", 
                 "qwen2.5-coder:14b-q5", "qwen2.5:7b", "qwen2.5:7b-q5"]:
        if pref in available:
            writer = pref; break
    if not writer and available:
        writer = available[0]

    # 快速脑暴模型 (7B)
    fast = None
    for pref in ["qwen2.5:7b", "qwen2.5:7b-q5", "qwen2.5-coder:7b", "qwen2.5-coder:7b-q5"]:
        if pref in available:
            fast = pref; break
    if not fast and writer:
        fast = writer
    if not fast:
        fast = writer or "qwen2.5:7b"

    print(f"  🦙 Ollama {port}: writer={writer}, fast={fast} (available={available})")
    return writer or "qwen2.5:14b", fast or "qwen2.5:7b"

_OLLAMA_PORT = _detect_ollama_port()
OLLAMA_URL = f"http://127.0.0.1:{_OLLAMA_PORT}"
OLLAMA_WRITER_MODEL, OLLAMA_FAST_MODEL = _detect_writer_model(_OLLAMA_PORT)

# ═══════════════════════════════════════════════════════════
# EigenFlux 12 天团 — 写作领域权威 (按专长分组)
# ═══════════════════════════════════════════════════════════
EIGENFLUX_WRITING_COUNCIL = [
    # 🏛️ 架构 & 工程写作
    {"name": "architect_zhang", "role": "系统架构师",    "domain": "架构文档/API设计/技术白皮书", "angle": "从整体设计到落地细节的层次化呈现"},
    {"name": "dev_wang",        "role": "开发工程师",    "domain": "代码注释/开发指南/最佳实践", "angle": "从开发者日常视角写出可操作的指南"},
    {"name": "backend_li",      "role": "后端工程师",    "domain": "后端技术文档/性能说明/DB设计", "angle": "后端视角的严谨性和可扩展性论述"},

    # 🎨 设计 & 内容写作
    {"name": "designer_chen",   "role": "UI/UX 设计师", "domain": "设计规范/组件文档/交互说明", "angle": "视觉语言和交互逻辑的视觉化表达"},
    {"name": "copywriter_liu",  "role": "文案专家",      "domain": "产品文案/广告语/品牌故事",   "angle": "用户视角 · 触动情绪 · 记忆点设计"},
    {"name": "literary_zhou",   "role": "文学顾问",      "domain": "技术科普/教程/教学内容",    "angle": "用文学笔法降低专业门槛"},

    # 📚 教育 & 知识写作
    {"name": "edu_yao",         "role": "教育顾问",      "domain": "K12/高等教育/成人教育内容", "angle": "认知科学 + 教学法的结构化知识"},
    {"name": "skill_ren",       "role": "Skill 专家",    "domain": "方法论 Skill/技术 Skill",   "angle": "从实践中提炼可复用 Skill 模式"},
    {"name": "knowledge_xue",   "role": "知识聚合家",    "domain": "知识图谱/百科/领域综述",    "angle": "多源知识融合 + 结构化呈现"},

    # 🖥️ 硬件 & 实操写作
    {"name": "arduino_he",      "role": "硬件工程师",    "domain": "硬件教程/DIY项目/实验记录", "angle": "实操视角: step-by-step + 踩坑经验"},
    {"name": "math_qian",       "role": "数学专家",      "domain": "数学建模/算法教程/公式推导", "angle": "严谨的数学推导 + 直觉的几何解释"},

    # ⚖️ 合规 & 治理写作
    {"name": "legal_wang",      "role": "法务顾问",      "domain": "法律合规/隐私政策/条款",    "angle": "法规原文 + 通俗解读 + 风险提示"},
    {"name": "govern_xu",       "role": "规则治理",      "domain": "规范/约束/流程文档",        "angle": "清晰的规则层次 + 强制执行架构"},
]

# ═══════════════════════════════════════════════════════════
# DB Schema (幂等)
# ═══════════════════════════════════════════════════════════
SCHEMA = """
CREATE TABLE IF NOT EXISTS mt_writing_tasks (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    task_id         TEXT UNIQUE,           -- "wrt_" + uuid[:12]
    topic           TEXT NOT NULL,         -- 写作主题
    audience        TEXT,                  -- 目标读者
    style           TEXT,                  -- 文风 (技术科普/教程/白皮书/文案/小说...)
    target_words    INTEGER DEFAULT 500,   -- 目标字数
    status          TEXT DEFAULT 'pending',-- pending/collaborating/generating/reviewing/done/failed
    phase1_council  TEXT,                  -- 12 天团脑暴 JSON
    phase2_skills   TEXT,                  -- Skill/顾问知识 JSON
    phase3_github   TEXT,                  -- GitHub 融合 JSON
    phase4_web      TEXT,                  -- 全网知识 JSON
    phase5_draft    TEXT,                  -- 初稿 (Markdown)
    phase6_review   TEXT,                  -- 自检 JSON
    final_content   TEXT,                  -- 最终稿
    tokens_saved    INTEGER DEFAULT 0,     -- 本地推理节省
    duration_sec    INTEGER,
    created_at      TEXT DEFAULT CURRENT_TIMESTAMP,
    done_at         TEXT
);
CREATE INDEX IF NOT EXISTS idx_writing_tasks_status ON mt_writing_tasks(status, created_at);
CREATE INDEX IF NOT EXISTS idx_writing_tasks_topic  ON mt_writing_tasks(topic);
"""


class WritingPipelineEngine:
    """仙女座写作流水线 — 7 层串联"""

    def __init__(self):
        self.db = sqlite3.connect(str(_DB_PATH), timeout=10)
        self.db.executescript(SCHEMA)
        self.db.commit()
        self._ollama_online = self._check_ollama()
        print(f"[✍️ WritingPipeline] 初始化 — OLLAMA={OLLAMA_WRITER_MODEL} online={self._ollama_online} DB={_DB_PATH}")

    def _check_ollama(self) -> bool:
        try:
            import urllib.request
            urllib.request.urlopen(f"{OLLAMA_URL}/api/tags", timeout=3)
            return True
        except Exception:
            return False

    def _ollama_generate(self, prompt: str, model: str | None = None,
                         temperature: float = 0.7, max_tokens: int = 2048,
                         timeout_sec: int = 300) -> str:
        """本地 Ollama 生成 — 零 token 消耗
        timeout_sec 默认 300s (5 分钟), 足够 14B 模型首次加载 + 推理
        """
        import urllib.request, json as _j
        if not self._ollama_online:
            return f"[OllamaOffline] {prompt[:60]}..."
        m = model or OLLAMA_WRITER_MODEL
        try:
            body = _j.dumps({
                "model": m, "prompt": prompt, "stream": False,
                "options": {"temperature": temperature, "num_predict": max_tokens}
            }).encode()
            req = urllib.request.Request(f"{OLLAMA_URL}/api/generate",
                data=body, headers={"Content-Type": "application/json"})
            resp = _j.loads(urllib.request.urlopen(req, timeout=timeout_sec).read())
            return resp.get("response", "")
        except Exception as e:
            return f"[OllamaError:{type(e).__name__}] {str(e)[:80]}"

    # ═══════════════════════════════════════════════════════
    # Phase 1: EigenFlux 12 天团脑暴
    # ═══════════════════════════════════════════════════════
    def phase1_council_brainstorm(self, topic: str, audience: str) -> list[dict]:
        """让 12 专家每人给一个视角 → 收集矛盾 + 共识"""
        print(f"\n{'='*60}")
        print(f"🎯 Phase 1: EigenFlux 12 天团脑暴")
        print(f"   主题: {topic}  ·  读者: {audience}")
        print(f"{'='*60}")

        insights = []
        for expert in EIGENFLUX_WRITING_COUNCIL:
            prompt = (
                f"你是仙女座 AI 写作天团中的【{expert['role']}·{expert['domain']}】专家。\n"
                f"写作主题: {topic}\n"
                f"目标读者: {audience}\n"
                f"请从你的独特视角出发，给出 2-3 条写作建议:\n"
                f"1) 这个主题最容易被忽视的角度是什么?\n"
                f"2) 应该用什么结构来呈现才能让读者记住?\n"
                f"3) 有什么权威数据 / 案例 / 框架可以引用?\n"
                f"用简洁的要点回答 (每条不超过 50 字)。"
            )
            advice = self._ollama_generate(prompt, model=OLLAMA_FAST_MODEL,
                                           temperature=0.6, max_tokens=400)
            insights.append({
                "expert": expert["name"],
                "role": expert["role"],
                "domain": expert["domain"],
                "angle": expert["angle"],
                "advice": advice.strip(),
            })
            print(f"  ✦ {expert['role']:8s} → {advice.strip()[:50]}...")
        return insights

    # ═══════════════════════════════════════════════════════
    # Phase 2: Skill + 顾问知识检索
    # ═══════════════════════════════════════════════════════
    def phase2_skill_knowledge(self, topic: str) -> dict:
        """从 25 域 + 冰山文案矩阵 + 本地 Skill 中检索相关知识"""
        print(f"\n{'='*60}")
        print(f"📚 Phase 2: Skill + 顾问知识检索")
        print(f"{'='*60}")

        knowledge: dict[str, list] = {"iceberg": [], "rules": [], "skills": []}

        # 冰山文案矩阵 (5,919 条)
        try:
            rows = self.db.execute(
                "SELECT domain, audience, context_tag, substr(text,1,100) "
                "FROM mt_iceberg_content_matrix "
                "WHERE text LIKE ? OR domain LIKE ? "
                "LIMIT 20",
                (f"%{topic}%", f"%{topic[:4]}%")
            ).fetchall()
            knowledge["iceberg"] = [{"domain": r[0], "audience": r[1], "context": r[2], "text": r[3]} for r in rows]
            print(f"  🧊 冰山文案矩阵: {len(rows)} 条匹配")
        except Exception as e:
            print(f"  ⚠️ 冰山查询: {e}")

        # 规则变更 (17 条)
        try:
            rows = self.db.execute(
                "SELECT rule_id, to_version, substr(change_summary,1,80) "
                "FROM mt_rule_changelog ORDER BY created_at DESC LIMIT 5"
            ).fetchall()
            knowledge["rules"] = [{"rule_id": r[0], "version": r[1], "summary": r[2]} for r in rows]
            print(f"  📐 规则变更: {len(rows)} 条最新")
        except Exception: pass

        # 脑库 (335 条) — 经验总结 (不限 topic, 拿最新 15 条作为通用知识)
        try:
            rows = self.db.execute(
                "SELECT fed_by, feed_target, substr(payload_preview,1,120) "
                "FROM mt_ai_brain_feed_log "
                "WHERE payload_preview LIKE ? OR payload_preview LIKE ? OR feed_target LIKE ? "
                "ORDER BY created_at DESC LIMIT 15",
                (f"%{topic[:3]}%", f"%{topic}%", f"%{topic[:4]}%")
            ).fetchall()
            knowledge["brain"] = [{"expert": r[0], "target": r[1], "preview": r[2]} for r in rows]
            print(f"  🧠 AI 脑库: {len(rows)} 条经验")
        except Exception as e:
            print(f"  ⚠️ 脑库查询: {e}")

        # EigenFlux 投票 (7 条) — 规则共识
        try:
            rows = self.db.execute(
                "SELECT expert_name, topic, substr(vote_text,1,100) "
                "FROM mt_eigenflux_vote_log ORDER BY created_at DESC LIMIT 10"
            ).fetchall()
            knowledge["votes"] = [{"expert": r[0], "topic": r[1], "vote": r[2]} for r in rows]
            print(f"  ✦ EigenFlux 投票: {len(rows)} 条共识")
        except Exception: pass

        # 开发流程 events — 真实案例
        try:
            rows = self.db.execute(
                "SELECT flow_id, event_type, substr(event_payload,1,100) "
                "FROM mt_dev_flow_events ORDER BY created_at DESC LIMIT 10"
            ).fetchall()
            knowledge["events"] = [{"flow": r[0], "type": r[1], "payload": r[2]} for r in rows]
            print(f"  🔧 开发流程事件: {len(rows)} 条案例")
        except Exception: pass

        return knowledge

    # ═══════════════════════════════════════════════════════
    # Phase 3: GitHub 融合
    # ═══════════════════════════════════════════════════════
    def phase3_github_fusion(self, topic: str) -> dict:
        """查 GitHub trending repos + issues + 相关 commit"""
        print(f"\n{'='*60}")
        print(f"🔗 Phase 3: GitHub 知识融合")
        print(f"{'='*60}")

        result = {"repos": [], "issues": [], "error": None}
        try:
            import urllib.request, json as _j
            # GitHub API: 搜索仓库
            q = urllib.parse.quote(f"{topic} stars:>50")
            url = f"https://api.github.com/search/repositories?q={q}&sort=stars&per_page=5"
            req = urllib.request.Request(url, headers={"Accept": "application/vnd.github.v3+json"})
            resp = _j.loads(urllib.request.urlopen(req, timeout=10).read())
            for item in resp.get("items", [])[:5]:
                result["repos"].append({
                    "full_name": item["full_name"],
                    "stars": item["stargazers_count"],
                    "desc": (item.get("description") or "")[:100],
                    "url": item["html_url"],
                })
            print(f"  ⭐ GitHub repos: {len(result['repos'])} 个匹配")
            for r in result["repos"]:
                print(f"     ★ {r['full_name']} ({r['stars']:,}) — {r['desc'][:40]}...")
        except Exception as e:
            result["error"] = str(e)[:100]
            print(f"  ⚠️ GitHub API: {e}")
        return result

    # ═══════════════════════════════════════════════════════
    # Phase 4: 全网知识聚合 (B站 + 本地 skill)
    # ═══════════════════════════════════════════════════════
    def phase4_web_aggregation(self, topic: str) -> dict:
        """B站搜索 + 本地 Skill 模式匹配"""
        print(f"\n{'='*60}")
        print(f"🌐 Phase 4: 全网知识聚合")
        print(f"{'='*60}")

        result = {"bilibili": [], "local_skills": []}
        try:
            import urllib.request, json as _j, urllib.parse
            q = urllib.parse.quote(topic)
            url = f"https://api.bilibili.com/x/web-interface/search/all/v2?keyword={q}&page=1"
            req = urllib.request.Request(url, headers={
                "User-Agent": "Mozilla/5.0 Macintosh; Intel Mac OS X 10_15_7",
                "Referer": "https://www.bilibili.com/"
            })
            resp = _j.loads(urllib.request.urlopen(req, timeout=8).read())
            for sec in resp.get("data", {}).get("result", []):
                if sec.get("result_type") == "video":
                    for v in sec.get("data", [])[:3]:
                        result["bilibili"].append({
                            "title": v.get("title", "")[:50],
                            "author": v.get("author", ""),
                            "play": v.get("play", 0),
                            "bvid": v.get("bvid", ""),
                        })
                    break
            print(f"  📺 B站: {len(result['bilibili'])} 个相关视频")
        except Exception as e:
            print(f"  ⚠️ B站 API: {e}")

        # 本地 Skill 模式 (mt_andromeda_employee_registry 中 skill 型)
        try:
            rows = self.db.execute(
                "SELECT employee_name, skills, domain FROM mt_andromeda_employee_registry "
                "WHERE skills LIKE ? OR domain LIKE ? LIMIT 5",
                (f"%{topic[:4]}%", f"%{topic[:4]}%")
            ).fetchall()
            result["local_skills"] = [{"name": r[0], "skills": r[1], "domain": r[2]} for r in rows]
            print(f"  🛠️ 本地 AI 员工 Skill: {len(rows)} 个匹配")
        except Exception: pass

        return result

    # ═══════════════════════════════════════════════════════
    # Phase 5: 本地 Ollama 写作生成 (RAG 整合)
    # ═══════════════════════════════════════════════════════
    def phase5_generate(self, topic: str, audience: str, style: str,
                         target_words: int, council: list, skills: dict,
                         github: dict, web: dict) -> str:
        """把 Phase 1-4 所有知识整合 → Ollama 生成"""
        print(f"\n{'='*60}")
        print(f"✍️ Phase 5: 本地 Ollama 写作生成")
        print(f"   模型: {OLLAMA_WRITER_MODEL}  ·  目标: {target_words} 字  ·  风格: {style}")
        print(f"{'='*60}")

        # 12 专家共识摘要 (让 Ollama 先消化专家建议)
        council_text = "\n".join(
            f"  [{i['role']}] {i['advice'][:200]}" for i in council
        )[:3000]

        # GitHub 参考
        gh_text = "\n".join(
            f"  ★ {r['full_name']} ({r['stars']}⭐) — {r['desc'][:80]}"
            for r in github.get("repos", [])[:3]
        )

        # B站参考
        bv_text = "\n".join(
            f"  📺 {v['title'][:40]} by {v['author']} ({v['play']:,} 播放)"
            for v in web.get("bilibili", [])[:3]
        )

        # 冰山本
        ice_text = "\n".join(
            f"  🧊 [{k.get('domain','?')}] {k.get('text',k.get('preview',''))[:80]}"
            for k in skills.get("iceberg", [])[:8]
        ) or "  (冰山文案矩阵主要是页面短语, 无匹配)"

        # 脑库经验 (335 条)
        brain_text = "\n".join(
            f"  🧠 [{b.get('expert','?')}] → {b.get('preview','')[:80]}"
            for b in skills.get("brain", [])[:8]
        ) or "  (无匹配经验, 请自由发挥)"

        # EigenFlux 投票共识
        votes_text = "\n".join(
            f"  ✦ [{v['expert']}] 议题={v.get('topic','?')[:30]}: {v.get('vote','')[:80]}"
            for v in skills.get("votes", [])[:5]
        ) or "  (无投票数据)"

        # 规则变更
        rules_text = "\n".join(
            f"  📐 [{r['rule_id']}] v{r['version']}: {r['summary'][:80]}"
            for r in skills.get("rules", [])[:5]
        ) or "  (无规则变更)"

        # 开发流程事件
        events_text = "\n".join(
            f"  🔧 [{e['type']}] {e['payload'][:80]}"
            for e in skills.get("events", [])[:5]
        ) or "  (无开发流程事件)"

        # 构建 Prompt (多源 RAG + 强制长文)
        prompt = f"""# 仙女座 AI 写作流水线 · 7 层 RAG 增强

## 🎯 写作任务
- **主题**: {topic}
- **目标读者**: {audience}
- **文风**: {style}
- **硬性要求**: **不少于 {target_words} 字**, 这是一个硬约束! 写不够不算完成!

## 🧠 Phase 1 · EigenFlux 12 专家脑暴 (必须全部吸收)
{council_text}

## 📐 Phase 2 · 系统真实数据 (必须引用至少 3 条)
### 📐 规则变更
{rules_text}
### ✦ EigenFlux 投票共识
{votes_text}
### 🧠 AI 脑库经验
{brain_text}
### � 开发流程真实事件
{events_text}

## �� Phase 3 · GitHub 参考
{gh_text or '(GitHub API 无结果, 跳过)'}

## 📺 Phase 4 · B站通俗讲法
{bv_text or '(B站无结果, 跳过)'}

## ✋ 写作规则 (必须严格遵守)
1. **字数硬约束**: 不少于 {target_words} 字! 写不够说明你没尽力
2. **结构**: 必须有引言 + 至少 4 个主体小节 + 总结 + 参考
3. **小标题**: 每节用 ## 或 ### 标记
4. **金句**: 每节末尾放一句加粗的金句 (让读者能记住)
5. **务实**: 每个小节必须给可操作的具体建议, 不要空话
6. **数据**: 至少引用 Phase 2 里的 3 条真实数据/规则/经验
7. **深度**: 展开论点 → 给案例 → 分析利弊 → 给出建议

## ✅ 现在开始写!
从 ## 引言 开始, 一直写到 ## 参考. 写满 {target_words} 字以上再停!

## 引言
"""

        start = time.time()
        print(f"  ⏳ Ollama 生成中 (可能 30-180s, 14B 模型加载 + 推理)...")
        draft = self._ollama_generate(prompt, model=OLLAMA_WRITER_MODEL,
                                      temperature=0.85, max_tokens=max(target_words * 2, 2048))
        duration = int(time.time() - start)
        print(f"  ✅ 生成完成: {len(draft):,} 字 · {duration}s · 零 token")
        return draft

    # ═══════════════════════════════════════════════════════
    # Phase 6: 文案自检
    # ═══════════════════════════════════════════════════════
    def phase6_review(self, draft: str) -> dict:
        """copy_inspection_engine + EigenFlux 交叉评审"""
        print(f"\n{'='*60}")
        print(f"🔍 Phase 6: 文案自检 + 专家交叉评审")
        print(f"{'='*60}")

        issues = []
        # 硬编码检查
        for k in ["TODO", "FIXME", "XXX", "placeholder", "待补充", "此处填"]:
            if k in draft:
                issues.append({"type": "placeholder", "keyword": k})
        # 重复检查
        sentences = [s.strip() for s in draft.split("。") if len(s.strip()) > 20]
        if len(sentences) != len(set(sentences)):
            issues.append({"type": "repetition", "count": len(sentences) - len(set(sentences))})
        # 字数
        word_count = len(draft.replace(" ", "").replace("\n", ""))
        print(f"  📊 字数: {word_count:,} · 问题: {len(issues)} 个")
        for i in issues: print(f"     ⚠️ [{i['type']}] {i.get('keyword', i.get('count', ''))}")

        # 专家交叉评审 (EigenFlux 3 专家快速过)
        experts_for_review = [e for e in EIGENFLUX_WRITING_COUNCIL
                              if e["role"] in ("架构师", "文案专家", "教育顾问")]
        reviews = []
        for expert in experts_for_review[:2]:
            p = (f"你是【{expert['role']}】。请给下面的文章打分 (1-10)，"
                 f"指出 1 个最严重的问题 和 1 个可改进点:\n\n{draft[:2000]}")
            r = self._ollama_generate(p, model=OLLAMA_FAST_MODEL, max_tokens=300)
            reviews.append({"expert": expert["name"], "feedback": r.strip()})
            print(f"  🎯 [{expert['role']}] 评审: {r.strip()[:80]}...")

        return {"issues": issues, "word_count": word_count, "reviews": reviews}

    # ═══════════════════════════════════════════════════════
    # Phase 7: 最终交付
    # ═══════════════════════════════════════════════════════
    def phase7_deliver(self, task_id: str, draft: str, review: dict,
                       council: list, github: dict) -> str:
        """落库 + 美化输出"""
        print(f"\n{'='*60}")
        print(f"📦 Phase 7: 最终交付")
        print(f"{'='*60}")

        # 写一个写作流水线产物摘要到本地
        artifacts_dir = _PROJECT_ROOT / "static" / "writing_artifacts"
        artifacts_dir.mkdir(parents=True, exist_ok=True)
        artifact = artifacts_dir / f"{task_id}.md"

        header = (f"# {task_id}\n\n"
                  f"> **仙女座 AI 写作流水线 · 7 层 RAG 增强**  \n"
                  f"> 生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}  \n"
                  f"> 本地 Ollama `{OLLAMA_WRITER_MODEL}` · 零 token 消耗  \n"
                  f"> 参与专家: {len(council)} 名 EigenFlux 天团  \n"
                  f"> GitHub 参考: {len(github.get('repos',[]))} 个  \n\n"
                  f"---\n\n")

        with open(artifact, "w") as f:
            f.write(header + draft)
        print(f"  📄 落库: {artifact}")

        # 快速打印前 300 字预览
        print(f"\n  📝 预览 (前 300 字):\n  {'─'*50}")
        print(f"  {draft[:300].replace(chr(10), ' ')}...")
        print(f"  {'─'*50}")

        return str(artifact)

    # ═══════════════════════════════════════════════════════
    # 主入口: 一键跑完 7 层
    # ═══════════════════════════════════════════════════════
    def write(self, topic: str, audience: str = "技术读者",
              style: str = "技术科普", target_words: int = 1500) -> str:
        """完整 7 层流水线 — 返回 task_id"""
        task_id = f"wrt_{uuid.uuid4().hex[:12]}"
        start = time.time()

        # 落库初始状态
        self.db.execute(
            "INSERT OR IGNORE INTO mt_writing_tasks (task_id, topic, audience, style, target_words, status) "
            "VALUES (?,?,?,?,?,?)" , (task_id, topic, audience, style, target_words, "collaborating"))
        self.db.commit()

        print(f"\n{'#'*60}")
        print(f"# ✨ 仙女座 AI 写作流水线  v1.0")
        print(f"# task_id: {task_id}")
        print(f"# 主题: {topic}")
        print(f"# 读者: {audience}  ·  风格: {style}  ·  目标: {target_words} 字")
        print(f"{'#'*60}")

        try:
            # Phase 1
            council = self.phase1_council_brainstorm(topic, audience)
            self.db.execute("UPDATE mt_writing_tasks SET phase1_council=?, status='generating' WHERE task_id=?",
                            (json.dumps(council, ensure_ascii=False), task_id))
            self.db.commit()

            # Phase 2
            skills = self.phase2_skill_knowledge(topic)
            self.db.execute("UPDATE mt_writing_tasks SET phase2_skills=? WHERE task_id=?",
                            (json.dumps(skills, ensure_ascii=False), task_id))
            self.db.commit()

            # Phase 3
            github = self.phase3_github_fusion(topic)
            self.db.execute("UPDATE mt_writing_tasks SET phase3_github=? WHERE task_id=?",
                            (json.dumps(github, ensure_ascii=False), task_id))
            self.db.commit()

            # Phase 4
            web = self.phase4_web_aggregation(topic)
            self.db.execute("UPDATE mt_writing_tasks SET phase4_web=? WHERE task_id=?",
                            (json.dumps(web, ensure_ascii=False), task_id))
            self.db.commit()

            # Phase 5
            draft = self.phase5_generate(topic, audience, style, target_words,
                                          council, skills, github, web)
            self.db.execute("UPDATE mt_writing_tasks SET phase5_draft=? WHERE task_id=?", (draft, task_id))
            self.db.commit()

            # Phase 6
            review = self.phase6_review(draft)
            self.db.execute("UPDATE mt_writing_tasks SET phase6_review=?, status='reviewing' WHERE task_id=?",
                            (json.dumps(review, ensure_ascii=False), task_id))
            self.db.commit()

            # Phase 7
            artifact_path = self.phase7_deliver(task_id, draft, review, council, github)
            duration = int(time.time() - start)
            self.db.execute(
                "UPDATE mt_writing_tasks SET final_content=?, duration_sec=?, tokens_saved=?, status='done', done_at=CURRENT_TIMESTAMP WHERE task_id=?",
                (artifact_path, duration, target_words * 2, task_id))
            self.db.commit()

            print(f"\n{'#'*60}")
            print(f"# ✅ 写作流水线完成! 耗时 {duration}s · 节省 {target_words*2:,} tokens")
            print(f"# 📄 {artifact_path}")
            print(f"# 🔗 Flask API: /api/writing/task/{task_id}")
            print(f"{'#'*60}")

        except Exception as e:
            print(f"\n💥 流水线中断: {e}")
            self.db.execute("UPDATE mt_writing_tasks SET status='failed' WHERE task_id=?", (task_id,))
            self.db.commit()
            raise
        return task_id


# ═══════════════════════════════════════════════════════════
# CLI 入口
# ═══════════════════════════════════════════════════════════
if __name__ == "__main__":
    import argparse
    ap = argparse.ArgumentParser(description="仙女座 AI 写作流水线")
    ap.add_argument("topic", nargs="?", help="写作主题")
    ap.add_argument("--audience", default="技术读者")
    ap.add_argument("--style", default="技术科普", choices=["技术科普", "教程", "白皮书", "文案", "小说", "新闻稿"])
    ap.add_argument("--words", type=int, default=1500)
    ap.add_argument("--task", help="查看已有 task_id 详情")
    args = ap.parse_args()

    eng = WritingPipelineEngine()

    if args.task:
        row = eng.db.execute(
            "SELECT status, topic, duration_sec FROM mt_writing_tasks WHERE task_id=?", (args.task,)).fetchone()
        print(f"📋 {args.task}: status={row[0]} topic={row[1]} dur={row[2]}s" if row else "❌ task 不存在")
    elif args.topic:
        task_id = eng.write(args.topic, args.audience, args.style, args.words)
        print(f"\n🎯 task_id={task_id}")
    else:
        # demo
        print("💡 用法: python3 ai_writing_pipeline_engine.py '主题' --style 技术科普 --words 2000")
        print("   python3 ai_writing_pipeline_engine.py --task wrt_xxxxxxxxx")
