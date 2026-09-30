#!/usr/bin/env python3
"""
文曲星 (WENQUXING) — 仙女座文字编辑子系统
==========================================

仙女座 25 域星中的【文学域】专属子系统.
本地 Ollama 推理 · 零 token 消耗 · 7 种文字编辑模式.

┌──────────────────────────────────────────────────────────┐
│                                                          │
│   📜 模式 1: 文案生成     "写一篇关于冰山的技术白皮书"    │
│   ✏️ 模式 2: 文本改写     "把这段写得更通俗易懂"          │
│   🔍 模式 3: 段落梳理     "帮我整理这段混乱的草稿"        │
│   📏 模式 4: 长文撰写     "写 3000 字关于 XX 的分析"      │
│   🧹 模式 5: 文本纠错     "修复错别字 + 病句 + 标点"      │
│   💡 模式 6: 润色增强     "让这段话更有文采"              │
│   🔄 模式 7: 风格转换     "转成古风 / 学术 / 口语"        │
│                                                          │
└──────────────────────────────────────────────────────────┘

依赖:
  - Ollama (自动发现端口 11434/11435/11436)
  - mt_wenquxing_tasks (新表)
  - mt_andromeda_employee_registry (5 位写作专家 AI 员工)
  - EigenFlux 12 天团 (Phase 1 脑暴)
"""

from __future__ import annotations
import json, os, sqlite3, subprocess, sys, time, hashlib, uuid, re, threading
from datetime import datetime
from pathlib import Path
from enum import Enum, auto

# ═══════════════════════════════════════════════════════════
# DB
# ═══════════════════════════════════════════════════════════
_PROJECT_ROOT = Path(__file__).parent.parent
_DB_CANDIDATES = [
    _PROJECT_ROOT / "database" / "app.db",
    _PROJECT_ROOT / "app.db",
]
_DB_PATH = next((p for p in _DB_CANDIDATES if p.exists()), _DB_CANDIDATES[0])

# Ollama — 自动发现
def _detect_ollama():
    import urllib.request as _ur, json as _j
    for p in [11434, 11435, 11436]:
        try:
            resp = _j.loads(_ur.urlopen(f"http://127.0.0.1:{p}/api/tags", timeout=2).read())
            models = [m["name"] for m in resp.get("models", [])]
            # 优先选 14B (最够写作)
            writer = None
            for pref in ["qwen2.5:14b-q5", "qwen2.5:14b", "qwen2.5-coder:14b", "qwen2.5:7b"]:
                if pref in models: writer = pref; break
            return p, writer or (models[0] if models else "qwen2.5:7b"), models
        except Exception: continue
    return 11434, "qwen2.5:7b", []

_OLLAMA_PORT, OLLAMA_WRITER_MODEL, _ALL_MODELS = _detect_ollama()
OLLAMA_URL = f"http://127.0.0.1:{_OLLAMA_PORT}"
print(f"[📜 文曲星] Ollama={OLLAMA_URL} model={OLLAMA_WRITER_MODEL} available={_ALL_MODELS}")

# ═══════════════════════════════════════════════════════════
# 7 种编辑模式 + Prompt 模板
# ═══════════════════════════════════════════════════════════
MODELS = {
    "copy": {
        "name": "文案生成",
        "icon": "📜",
        "desc": "从零写一篇完整文案/文章",
        "prompt": lambda t,c,s,w: f"""# 文曲星 · 文案生成

## 需求
- **主题**: {t}
- **读者**: {c}
- **风格**: {s}
- **目标字数**: {w} 字

## 要求
1. 结构清晰 (引言 → 4+ 主体小节 → 总结)
2. 每节有 ## 小标题
3. 每节末尾放一句 **加粗金句**
4. 观点独到, 数据扎实, 给具体建议
5. 字数必须够 {w} 字以上!

## 开始
""",
    },
    "rewrite": {
        "name": "文本改写",
        "icon": "✏️",
        "desc": "重写已有文本 (换风格/加深/简化)",
        "prompt": lambda t,c,s,w: f"""# 文曲星 · 文本改写

## 原文
{t}

## 改写要求
- **目标读者**: {c}
- **新风格**: {s}
- **字数**: 目标 {w} 字

## 规则
1. 保留原文核心观点, 重新组织表达
2. 结构更清晰 (小标题)
3. 语言更流畅有力
4. 标注改动亮点 (文末"改写亮点: ...")

## 改写后
""",
    },
    "outline": {
        "name": "段落梳理",
        "icon": "🔍",
        "desc": "把混乱的草稿整理成清晰的段落结构",
        "prompt": lambda t,c,s,w: f"""# 文曲星 · 段落梳理

## 原文 (可能混乱)
{t}

## 任务
请把上面这段内容, 整理成一个结构清晰的大纲 + 展开:

1. **先给大纲**: 列出 3-6 个要点 (用 - 列表)
2. **再展开**: 每个要点写 3-5 句说明
3. **补充金句**: 每个要点配一句 **加粗金句**

## 目标读者
{c}

## 输出 (大纲 + 展开)
""",
    },
    "longform": {
        "name": "长文撰写",
        "icon": "📏",
        "desc": "3000+ 字深度长文 (多章节)",
        "prompt": lambda t,c,s,w: f"""# 文曲星 · 长文撰写

## 需求
- **主题**: {t}
- **读者**: {c}
- **风格**: {s}
- **目标**: {w} 字以上的完整长文

## 结构要求 (8+ 章节)
## 引言 — 为什么这个主题重要
## 一、背景与历史
## 二、核心概念解析
## 三、现状与挑战  
## 四、主流解决方案对比
## 五、创新方向与案例
## 六、实操指南 (step-by-step)
## 七、未来展望
## 参考资料

## 写作规则
1. 每节 300-500 字, 总字数必须 ≥ {w}
2. 每节末尾放 **加粗金句**
3. 数据要有依据 (用 [1][2] 标注)
4. 给具体可操作的建议

## 开始 — 先写 ## 引言
""",
    },
    "proofread": {
        "name": "文本纠错",
        "icon": "🧹",
        "desc": "修复错别字/病句/标点/语病",
        "prompt": lambda t,c,s,w: f"""# 文曲星 · 文本纠错

## 原文
{t}

## 任务
1. 逐句检查: 错别字 / 病句 / 标点 / 歧义
2. 直接输出**纠错后的完整文本** (不要只列问题)
3. 文末附"修改清单": 改了哪几处, 为什么改

## 读者
{c}

## 纠错后文本
""",
    },
    "polish": {
        "name": "润色增强",
        "icon": "💡",
        "desc": "让文本更有文采/说服力/专业感",
        "prompt": lambda t,c,s,w: f"""# 文曲星 · 润色增强

## 原文
{t}

## 润色方向
- **目标读者**: {c}
- **增强风格**: {s}
- **字数**: 目标 {w} 字 (可适度扩展)

## 增强手法 (任选)
1. 增加生动比喻 / 典故
2. 加入权威数据 / 案例
3. 金句收尾 / 排比增强
4. 反问 / 设问 / 悬念
5. 专业术语 + 通俗解释

## 润色后
""",
    },
    "transform": {
        "name": "风格转换",
        "icon": "🔄",
        "desc": "转成古风/学术/口语/新闻等",
        "prompt": lambda t,c,s,w: f"""# 文曲星 · 风格转换

## 原文
{t}

## 转换目标
- **目标风格**: {s}
- **目标读者**: {c}
- **字数**: 目标 {w} 字

## 可选风格示例
- 学术论文风格: 严谨、引述多、术语准
- 新闻快讯风格: 5W1H、简洁有力
- 古风文言文: 典雅、用典、平仄
- 社交媒体风格: 活泼、Emoji、短段落
- 小说散文风格: 细腻、情感、修辞

## 转换后文本
""",
    },
}

MODE_NAME_TO_KEY = {v["name"]: k for k,v in MODELS.items()}


# ═══════════════════════════════════════════════════════════
# DB Schema
# ═══════════════════════════════════════════════════════════
SCHEMA = """
CREATE TABLE IF NOT EXISTS mt_wenquxing_tasks (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    task_id         TEXT UNIQUE,                 -- "wqx_" + uuid[:12]
    mode            TEXT NOT NULL,               -- copy/rewrite/outline/longform/proofread/polish/transform
    mode_name       TEXT,                        -- 文案生成/文本改写/...
    topic           TEXT NOT NULL,               -- 用户输入 (主题或原文)
    audience        TEXT DEFAULT '技术读者',
    style           TEXT DEFAULT '专业客观',
    target_words    INTEGER DEFAULT 1500,
    status          TEXT DEFAULT 'pending',      -- pending/generating/done/failed
    drafts          TEXT,                        -- 多版本 JSON [{version,content,score}]
    final_text      TEXT,                        -- 最终输出
    revisions       INTEGER DEFAULT 0,           -- 迭代次数
    tokens_saved    INTEGER DEFAULT 0,
    duration_sec    INTEGER,
    created_at      TEXT DEFAULT CURRENT_TIMESTAMP,
    done_at         TEXT
);
CREATE INDEX IF NOT EXISTS idx_wqx_tasks_status ON mt_wenquxing_tasks(status, created_at);
CREATE INDEX IF NOT EXISTS idx_wqx_tasks_mode   ON mt_wenquxing_tasks(mode);
"""


class WenquxingEngine:
    """文曲星 — 仙女座文字编辑子系统"""

    def __init__(self):
        self.db = sqlite3.connect(str(_DB_PATH), timeout=10)
        self.db.executescript(SCHEMA)
        self.db.commit()
        self._ollama_online = self._check_ollama()
        print(f"[📜 文曲星] v1.0 — {len(MODELS)} 种模式 · Ollama {OLLAMA_WRITER_MODEL} online={self._ollama_online}")

    def _check_ollama(self) -> bool:
        try:
            import urllib.request as _ur
            _ur.urlopen(f"{OLLAMA_URL}/api/tags", timeout=3)
            return True
        except Exception: return False

    def _generate(self, prompt: str, model: str | None = None,
                 temperature: float = 0.8, max_tokens: int = 2048,
                 timeout_sec: int = 300) -> str:
        """本地 Ollama 推理."""
        import urllib.request, json as _j
        if not self._ollama_online:
            return f"[OllamaOffline] {prompt[:80]}"
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
    # 核心: 7 种编辑模式入口
    # ═══════════════════════════════════════════════════════
    def write(self, mode: str, topic: str, audience: str = "技术读者",
              style: str = "专业客观", target_words: int = 1500) -> str:
        """统一入口: mode=copy/rewrite/outline/longform/proofread/polish/transform"""
        task_id = f"wqx_{uuid.uuid4().hex[:12]}"
        start = time.time()

        m = MODELS.get(mode) or MODELS.get(MODE_NAME_TO_KEY.get(mode))
        if not m:
            print(f"[📜 文曲星] ❌ 未知模式: {mode} (可用: {list(MODELS.keys())})")
            return ""

        print(f"\n{'═'*60}")
        print(f"📜 文曲星 · {m['icon']} {m['name']}")
        print(f"   task_id: {task_id}")
        print(f"   主题: {topic[:60]}")
        print(f"   读者: {audience} · 风格: {style} · 字数: {target_words}")
        print(f"{'═'*60}")

        # 落库初始状态
        self.db.execute(
            "INSERT OR IGNORE INTO mt_wenquxing_tasks "
            "(task_id, mode, mode_name, topic, audience, style, target_words, status) "
            "VALUES (?,?,?,?,?,?,?,?)" ,
            (task_id, mode, m["name"], topic, audience, style, target_words, "generating"))
        self.db.commit()

        try:
            prompt = m["prompt"](topic, audience, style, target_words)
            print(f"  ⏳ Ollama 生成中... (可能 30-180s)")
            draft = self._generate(prompt, max_tokens=max(target_words * 2, 2048))
            duration = int(time.time() - start)

            word_count = len(draft.replace(" ", "").replace("\n", ""))
            print(f"  ✅ 完成: {word_count:,} 字 · {duration}s")

            # 落库
            self.db.execute(
                "UPDATE mt_wenquxing_tasks SET final_text=?, status='done', "
                "duration_sec=?, tokens_saved=?, done_at=CURRENT_TIMESTAMP WHERE task_id=?",
                (draft, duration, target_words * 2, task_id))
            self.db.commit()

            # 写入 artifact 文件
            artifact_dir = _PROJECT_ROOT / "static" / "wenquxing_artifacts"
            artifact_dir.mkdir(parents=True, exist_ok=True)
            artifact = artifact_dir / f"{task_id}.md"
            header = (f"# 文曲星 · {m['icon']} {m['name']}\n\n"
                      f"> **仙女座文字编辑子系统**  \n"
                      f"> 生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}  \n"
                      f"> 模型: Ollama `{OLLAMA_WRITER_MODEL}` · 零 token  \n"
                      f"> 主题: {topic[:80]}  \n"
                      f"> 读者: {audience} · 风格: {style} · 目标: {target_words} 字  \n"
                      f"> 实际: {word_count:,} 字 · 耗时 {duration}s\n\n"
                      f"---\n\n")
            artifact.write_text(header + draft)
            print(f"  📄 产物: {artifact}")
            print(f"  🔗 API:  /api/wqx/task/{task_id}")

        except Exception as e:
            print(f"  💥 失败: {e}")
            self.db.execute("UPDATE mt_wenquxing_tasks SET status='failed' WHERE task_id=?", (task_id,))
            self.db.commit()
            raise

        print(f"\n{'═'*60}")
        print(f"# ✅ {m['icon']} {m['name']} 完成! task_id={task_id}")
        print(f"{'═'*60}")
        return task_id

    # 便捷方法 (直接调模式)
    def copy(self, topic, audience="技术读者", style="专业客观", words=1500):
        return self.write("copy", topic, audience, style, words)
    def rewrite(self, text, audience="更通俗", style="简明流畅", words=800):
        return self.write("rewrite", text, audience, style, words)
    def outline(self, text, audience="读者", style="结构化", words=600):
        return self.write("outline", text, audience, style, words)
    def longform(self, topic, audience="深度读者", style="学术严谨", words=3000):
        return self.write("longform", topic, audience, style, words)
    def proofread(self, text, audience="任何读者", style="标准书面", words=0):
        return self.write("proofread", text, audience, style, len(text))
    def polish(self, text, audience="目标读者", style="文采增强", words=0):
        return self.write("polish", text, audience, style, len(text) * 2)
    def transform(self, text, audience="新读者", style="古风", words=0):
        return self.write("transform", text, audience, style, len(text))

    # ═══════════════════════════════════════════════════════
    # 查询
    # ═══════════════════════════════════════════════════════
    def get_task(self, task_id: str) -> dict | None:
        row = self.db.execute("SELECT * FROM mt_wenquxing_tasks WHERE task_id=?", (task_id,)).fetchone()
        if not row: return None
        cols = [c[1] for c in self.db.execute("PRAGMA table_info(mt_wenquxing_tasks)").fetchall()]
        return dict(zip(cols, row))

    def list_tasks(self, limit: int = 20, mode: str | None = None) -> list[dict]:
        sql = "SELECT * FROM mt_wenquxing_tasks"
        args = []
        if mode: sql += " WHERE mode=?"; args.append(mode)
        sql += " ORDER BY id DESC LIMIT ?"
        args.append(limit)
        rows = self.db.execute(sql, args).fetchall()
        cols = [c[1] for c in self.db.execute("PRAGMA table_info(mt_wenquxing_tasks)").fetchall()]
        return [dict(zip(cols, r)) for r in rows]


# ═══════════════════════════════════════════════════════════
# CLI
# ═══════════════════════════════════════════════════════════
if __name__ == "__main__":
    import argparse
    ap = argparse.ArgumentParser(description="📜 文曲星 · 仙女座文字编辑子系统")
    ap.add_argument("mode", nargs="?", default="copy",
                    choices=list(MODELS.keys()),
                    help="编辑模式: " + "/".join(MODELS.keys()))
    ap.add_argument("topic", nargs="?", help="主题或原文")
    ap.add_argument("--audience", "-a", default="技术读者")
    ap.add_argument("--style", "-s", default="专业客观")
    ap.add_argument("--words", "-w", type=int, default=1500)
    ap.add_argument("--task", help="查看已有 task")
    ap.add_argument("--list", "-l", type=int, const=10, nargs="?", help="最近 N 个 task")
    ap.add_argument("--modes", action="store_true", help="列出所有模式")
    args = ap.parse_args()

    eng = WenquxingEngine()

    if args.modes:
        print("📜 文曲星 · 7 种编辑模式:")
        for k,v in MODELS.items():
            print(f"  {v['icon']} {k:12s} → {v['name']:8s} · {v['desc']}")
    elif args.task:
        t = eng.get_task(args.task)
        if t: print(json.dumps({k: v for k, v in t.items() if k != 'final_text'}, ensure_ascii=False, indent=2))
        else: print(f"❌ task {args.task} 不存在")
    elif args.list:
        tasks = eng.list_tasks(args.list)
        for t in tasks:
            print(f"  {t['task_id']}  [{t['mode']:10s}] {t['status']:10s} {t['topic'][:40]:40s} {t.get('duration_sec','?')}s")
    elif args.topic:
        task_id = eng.write(args.mode, args.topic, args.audience, args.style, args.words)
        print(f"\n🎯 task_id={task_id}")
    else:
        ap.print_help()
        print("\n💡 示例:")
        print("  python3 ai_wenquxing_engine.py copy '冰山规则底座系统设计' -w 2000")
        print("  python3 ai_wenquxing_engine.py rewrite '这里放一段原文' -s '更通俗易懂'")
        print("  python3 ai_wenquxing_engine.py outline '一段混乱的草稿'")
        print("  python3 ai_wenquxing_engine.py proofread '他的话让人很感动'")
        print("  python3 ai_wenquxing_engine.py --modes")
