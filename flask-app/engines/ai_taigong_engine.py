#!/usr/bin/env python3
"""
🧙 太公 (Taigong) — 仙女座 策略规划系统 — 商业/产品/战略方案
"""
from __future__ import annotations
import json, os, sys, time, uuid, argparse
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from andromeda_base import BaseAndromedaSubsystem, PROJECT_ROOT, DB_PATH, detect_ollama


class TaigongEngine(BaseAndromedaSubsystem):
    SUBSYSTEM_NAME = "太公"
    SUBSYSTEM_ICON = "🧙"
    SUBSYSTEM_DESC = "策略规划系统 — 商业/产品/战略方案"
    DB_TABLE = "mt_taigong_tasks"
    DB_SCHEMA = """
CREATE TABLE IF NOT EXISTS mt_taigong_tasks (
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
CREATE INDEX IF NOT EXISTS idxtaigong_status ON mt_taigong_tasks(status, created_at);
"""
    ARTIFACT_DIR = "taigong_artifacts"
    ARTIFACT_EXT = "md"
    DAEMON_NAME = "sys_taigong"
    DAEMON_DUTY = "策略规划系统 — 商业/产品/战略方案"
    AI_EMPLOYEES = [
        ("tg_wangjiang", "望将", "Strategist", 9, "太公望. 战略规划, 决胜千里."),
        ("tg_jiangmen", "将门", "ProductManager", 8, "产品专家. MVP + 路线图."),
        ("tg_business", "商业", "BizPlanner", 7, "商业计划专家.")
    ]

    MODES = {
    "strategy": {
        "name": "战略方案", "icon": "🎯", "desc": "目标 → 3 种战略 + 推荐",
        "prompt": lambda topic, kw: f"""为达成 {topic}, 设计 3 种可选战略方案: 每个的思路/优劣势/资源需求/推荐指数 (1-10)"""
    },
    "product": {
        "name": "产品规划", "icon": "📱", "desc": "需求 → MVP + 迭代路线图",
        "prompt": lambda topic, kw: f"""为以下产品需求做规划: {topic}\nMVP (最小可行产品) 功能清单 + 3 个月迭代路线图 + 技术选型"""
    },
    "business": {
        "name": "商业计划", "icon": "💼", "desc": "创意 → 商业计划要点",
        "prompt": lambda topic, kw: f"""为以下创意写商业计划要点: {topic}\n含: 目标用户/价值主张/商业模式/竞争壁垒/里程碑"""
    },
    "campaign": {
        "name": "营销活动", "icon": "📣", "desc": "目标 → 3 个活动方案",
        "prompt": lambda topic, kw: f"""为 {topic} 设计 3 种营销活动方案: 每个的创意/渠道/预算/预期效果"""
    },
    "pricing": {
        "name": "定价策略", "icon": "💰", "desc": "产品 → 3 档定价 + 依据",
        "prompt": lambda topic, kw: f"""为 {topic} 设计定价策略: 免费/基础/高级 三档定价 + 每档包含的功能 + 定价依据"""
    }
    }

    def write(self, mode: str, topic: str, **kwargs) -> str:
        m = self.MODES.get(mode)
        if not m:
            print(f"  Unknown mode: {mode}"); return ""
        task_id = self.new_task_id(prefix="tai")
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
    ap = argparse.ArgumentParser(description="🧙 太公")
    ap.add_argument("mode", nargs="?", choices=list(TaigongEngine.MODES.keys()), default="help")
    ap.add_argument("topic", nargs="?")
    ap.add_argument("--modes", action="store_true")
    ap.add_argument("--list", "-l", type=int, const=5, nargs="?")
    args = ap.parse_args()
    eng = TaigongEngine()
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
