#!/usr/bin/env python3
"""
🎯 后羿 (Houyi) — 仙女座 精准搜索/RAG系统 — 语义搜索/知识召回/精准匹配
"""
from __future__ import annotations
import json, os, sys, time, uuid, argparse
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from andromeda_base import BaseAndromedaSubsystem, PROJECT_ROOT, DB_PATH, detect_ollama


class HouyiEngine(BaseAndromedaSubsystem):
    SUBSYSTEM_NAME = "后羿"
    SUBSYSTEM_ICON = "🎯"
    SUBSYSTEM_DESC = "精准搜索/RAG系统 — 语义搜索/知识召回/精准匹配"
    DB_TABLE = "mt_houyi_tasks"
    DB_SCHEMA = """
CREATE TABLE IF NOT EXISTS mt_houyi_tasks (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    task_id TEXT UNIQUE,
    mode TEXT,
    mode_name TEXT,
    topic TEXT,
    final_text TEXT,
    artifact_path TEXT,
    status TEXT DEFAULT 'pending',
    duration_sec INTEGER,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
    done_at TEXT
);
CREATE INDEX IF NOT EXISTS idxhouyi_status ON mt_houyi_tasks(status, created_at);
"""
    ARTIFACT_DIR = "houyi_artifacts"
    ARTIFACT_EXT = "md"
    DAEMON_NAME = "sys_houyi"
    DAEMON_DUTY = "精准搜索/RAG系统 — 语义搜索/知识召回/精准匹配"
    AI_EMPLOYEES = [
        ("hy_she", "射", "SearchMaster", 9, "后羿射日. 搜索精准, 百发百中."),
        ("hy_suan", "算", "Analyst", 8, "对比分析专家. A vs B 一目了然."),
        ("hy_yuan", "源", "Researcher", 7, "溯源专家. 每个观点都有出处.")
    ]

    MODES = {
    "search": {
        "name": "语义搜索", "icon": "🔍", "desc": "查询 → 最相关的知识片段",
        "prompt": lambda topic, kw: f"""对以下查询做语义搜索, 返回 Top 5 最相关内容 (含来源 + 相关度 1-10): {topic}"""
    },
    "deepsearch": {
        "name": "深度搜索", "icon": "🕳️", "desc": "复杂问题 → 多源深度答案",
        "prompt": lambda topic, kw: f"""深度搜索: {topic}\n从 3 个角度 (是什么/为什么/怎么做) 给出完整答案 + 引用来源"""
    },
    "compare": {
        "name": "对比", "icon": "⚖️", "desc": "A vs B → 详细对比表 + 选择建议",
        "prompt": lambda topic, kw: f"""对比分析: {topic}\n用表格列出 5 个维度的对比 + 各自适用场景 + 推荐选择"""
    },
    "source": {
        "name": "溯源", "icon": "📖", "desc": "观点 → 原始出处 + 演变历史",
        "prompt": lambda topic, kw: f"""溯源: {topic}\n这个观点最早出自哪里? 怎么演变的? 现在有哪些不同版本?"""
    },
    "faq": {
        "name": "FAQ生成", "icon": "❓", "desc": "主题 → 10 个高频问题 + 答案",
        "prompt": lambda topic, kw: f"""为 {topic} 生成 10 个用户最常问的问题 + 简洁答案 (每问 ≤30 字)"""
    }
    }

    def write(self, mode: str, topic: str, **kwargs) -> str:
        m = self.MODES.get(mode)
        if not m:
            print(f"  Unknown mode: {mode}"); return ""
        task_id = self.new_task_id(prefix="hou")
        print("\n" + "=" * 55)
        print(f"  {self.SUBSYSTEM_ICON} {self.SUBSYSTEM_NAME} - {m['icon']} {m['name']}")
        print(f"  task_id: {task_id} · topic: {topic[:50]}")
        print("=" * 55)

        self.db_insert_task(task_id=task_id, mode=mode, mode_name=m["name"],
                             topic=topic, status="generating")
        t0 = time.time()
        print("  Ollama generating...")
        prompt = m["prompt"](topic, kwargs)
        raw = self.ollama_generate(prompt, max_tokens=1024)
        dur = int(time.time() - t0)
        print(f"  Done: {dur}s · {len(raw)} chars")

        artifact = self.save_artifact(task_id, raw, header_lines=[
            f"# {self.SUBSYSTEM_ICON} {self.SUBSYSTEM_NAME} - {m['name']}",
            f"> Topic: {topic[:80]} · {dur}s",
        ])
        self.write_task(task_id, raw, artifact_path=str(artifact), duration_sec=dur)
        print(f"  Artifact: {artifact}")
        return task_id


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description="🎯 后羿")
    ap.add_argument("mode", nargs="?", choices=list(HouyiEngine.MODES.keys()), default="help")
    ap.add_argument("topic", nargs="?")
    ap.add_argument("--modes", action="store_true")
    ap.add_argument("--list", "-l", type=int, const=5, nargs="?")
    args = ap.parse_args()
    eng = HouyiEngine()
    if args.modes or args.mode == "help":
        print(f"{eng.SUBSYSTEM_ICON} {eng.SUBSYSTEM_NAME} - {len(eng.MODES)} modes:")
        for k,v in eng.MODES.items():
            print(f"  {v['icon']} {k:12s} {v['name']:10s} - {v['desc']}")
    elif args.list:
        for t in eng.db_list_tasks(args.list):
            print(f"  {t['task_id']} [{t.get('status','?')}] {t.get('topic','')[:40]}")
    elif args.topic:
        tid = eng.write(args.mode, args.topic)
        print(f"\nDone task_id={tid}")
    else:
        ap.print_help()
