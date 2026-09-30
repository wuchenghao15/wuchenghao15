#!/usr/bin/env python3
"""
📚 仓颉 (Cangjie) — 仙女座 知识/题库系统 — 知识点/题目/解析自动生成
"""
from __future__ import annotations
import json, os, sys, time, uuid, argparse
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from andromeda_base import BaseAndromedaSubsystem, PROJECT_ROOT, DB_PATH, detect_ollama


class CangjieEngine(BaseAndromedaSubsystem):
    SUBSYSTEM_NAME = "仓颉"
    SUBSYSTEM_ICON = "📚"
    SUBSYSTEM_DESC = "知识/题库系统 — 知识点/题目/解析自动生成"
    DB_TABLE = "mt_cangjie_tasks"
    DB_SCHEMA = """
CREATE TABLE IF NOT EXISTS mt_cangjie_tasks (
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
CREATE INDEX IF NOT EXISTS idxcangjie_status ON mt_cangjie_tasks(status, created_at);
"""
    ARTIFACT_DIR = "cangjie_artifacts"
    ARTIFACT_EXT = "md"
    DAEMON_NAME = "sys_cangjie"
    DAEMON_DUTY = "知识/题库系统 — 知识点/题目/解析自动生成"
    AI_EMPLOYEES = [
        ("cj_zaoshi", "造字", "KnowledgeBuilder", 9, "仓颉造字. 每个知识点都精准."),
        ("cj_wenda", "问答", "QuestionMaker", 8, "出题专家. 选择/填空/问答样样精通."),
        ("cj_jiexi", "解析", "Explainer", 7, "解析专家. 为什么/为什么不/举一反三.")
    ]

    MODES = {
    "knowledge": {
        "name": "知识点生成", "icon": "💡", "desc": "主题 → 结构化知识点",
        "prompt": lambda topic, kw: f"""为以下主题生成 5-8 个核心知识点 (含定义/示例/易混点): {topic}"""
    },
    "question": {
        "name": "出题", "icon": "❓", "desc": "知识点 → 题目 (选择/填空/问答)",
        "prompt": lambda topic, kw: f"""为以下知识点各出 2 道选择题 + 1 道问答题: {topic}\n含选项 + 答案 + 详细解析"""
    },
    "explain": {
        "name": "解析", "icon": "📖", "desc": "题目 + 答案 → 详细解析",
        "prompt": lambda topic, kw: f"""为以下题目写详细解析: {topic}\n从 3 个角度 (为什么/为什么不/举一反三) 解释"""
    },
    "outline": {
        "name": "大纲", "icon": "📑", "desc": "学科 → 完整知识树大纲",
        "prompt": lambda topic, kw: f"""为 {topic} 生成完整知识树大纲 (三级目录), 每个叶子节点写一句话说明"""
    },
    "summary": {
        "name": "总结", "icon": "📝", "desc": "长文 → 结构化摘要 + 金句",
        "prompt": lambda topic, kw: f"""为下面的长文生成 300 字摘要 + 5 个金句: {topic}"""
    }
    }

    def write(self, mode: str, topic: str, **kwargs) -> str:
        m = self.MODES.get(mode)
        if not m:
            print(f"  Unknown mode: {mode}"); return ""
        task_id = self.new_task_id(prefix="can")
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
    ap = argparse.ArgumentParser(description="📚 仓颉")
    ap.add_argument("mode", nargs="?", choices=list(CangjieEngine.MODES.keys()), default="help")
    ap.add_argument("topic", nargs="?")
    ap.add_argument("--modes", action="store_true")
    ap.add_argument("--list", "-l", type=int, const=5, nargs="?")
    args = ap.parse_args()
    eng = CangjieEngine()
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
