#!/usr/bin/env python3
"""
🎪 貔貅 (Pixiu) — 仙女座 趣味/娱乐系统 — 笑话/故事/互动小游戏
"""
from __future__ import annotations
import json, os, sys, time, uuid, argparse
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from andromeda_base import BaseAndromedaSubsystem, PROJECT_ROOT, DB_PATH, detect_ollama


class PixiuEngine(BaseAndromedaSubsystem):
    SUBSYSTEM_NAME = "貔貅"
    SUBSYSTEM_ICON = "🎪"
    SUBSYSTEM_DESC = "趣味/娱乐系统 — 笑话/故事/互动小游戏"
    DB_TABLE = "mt_pixiu_tasks"
    DB_SCHEMA = """
CREATE TABLE IF NOT EXISTS mt_pixiu_tasks (
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
CREATE INDEX IF NOT EXISTS idxpixiu_status ON mt_pixiu_tasks(status, created_at);
"""
    ARTIFACT_DIR = "pixiu_artifacts"
    ARTIFACT_EXT = "md"
    DAEMON_NAME = "sys_pixiu"
    DAEMON_DUTY = "趣味/娱乐系统 — 笑话/故事/互动小游戏"
    AI_EMPLOYEES = [
        ("px_nawang", "魔王", "JokeMaster", 9, "貔貅魔王. 段子信手拈来."),
        ("px_wenyou", "文游", "StoryTeller", 8, "故事大王. 300 字讲一个好故事."),
        ("px_xiaoxi", "小溪", "GameDev", 7, "小游戏开发. Canvas + JS.")
    ]

    MODES = {
    "joke": {
        "name": "段子笑话", "icon": "😂", "desc": "主题 → 3 个原创笑话",
        "prompt": lambda topic, kw: f"""写 3 个关于 {topic} 的原创段子, 短小精悍 (20 字内)"""
    },
    "story": {
        "name": "故事", "icon": "📖", "desc": "主题 → 短故事 (300字)",
        "prompt": lambda topic, kw: f"""写一个 300 字以内的短故事, 主题是: {topic}"""
    },
    "game": {
        "name": "小游戏", "icon": "🎮", "desc": "需求 → 一个 HTML 小游戏代码",
        "prompt": lambda topic, kw: f"""生成一个单文件 HTML 小游戏 (纯前端, Canvas + JS), 玩法: {topic}"""
    },
    "poem": {
        "name": "写诗", "icon": "📜", "desc": "主题 → 一首七言绝句",
        "prompt": lambda topic, kw: f"""写一首七言绝句, 主题是 {topic}, 要求平起首句押韵"""
    },
    "brainteaser": {
        "name": "脑筋急转弯", "icon": "🧠", "desc": "主题 → 3 个急转弯 + 答案",
        "prompt": lambda topic, kw: f"""出 3 个关于 {topic} 的脑筋急转弯, 答案放在文末"""
    }
    }

    def write(self, mode: str, topic: str, **kwargs) -> str:
        m = self.MODES.get(mode)
        if not m:
            print(f"  Unknown mode: {mode}"); return ""
        task_id = self.new_task_id(prefix="pix")
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
    ap = argparse.ArgumentParser(description="🎪 貔貅")
    ap.add_argument("mode", nargs="?", choices=list(PixiuEngine.MODES.keys()), default="help")
    ap.add_argument("topic", nargs="?")
    ap.add_argument("--modes", action="store_true")
    ap.add_argument("--list", "-l", type=int, const=5, nargs="?")
    args = ap.parse_args()
    eng = PixiuEngine()
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
