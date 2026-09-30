#!/usr/bin/env python3
"""
🏮 月老 (Yuelao) — 仙女座 社交匹配系统 — AI员工组队/专家匹配/资源对接
"""
from __future__ import annotations
import json, os, sys, time, uuid, argparse
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from andromeda_base import BaseAndromedaSubsystem, PROJECT_ROOT, DB_PATH, detect_ollama


class YuelaoEngine(BaseAndromedaSubsystem):
    SUBSYSTEM_NAME = "月老"
    SUBSYSTEM_ICON = "🏮"
    SUBSYSTEM_DESC = "社交匹配系统 — AI员工组队/专家匹配/资源对接"
    DB_TABLE = "mt_yuelao_tasks"
    DB_SCHEMA = """
CREATE TABLE IF NOT EXISTS mt_yuelao_tasks (
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
CREATE INDEX IF NOT EXISTS idxyuelao_status ON mt_yuelao_tasks(status, created_at);
"""
    ARTIFACT_DIR = "yuelao_artifacts"
    ARTIFACT_EXT = "md"
    DAEMON_NAME = "sys_yuelao"
    DAEMON_DUTY = "社交匹配系统 — AI员工组队/专家匹配/资源对接"
    AI_EMPLOYEES = [
        ("yl_yue", "月老", "MatchMaker", 9, "月老. 红线一牵, 缘分自然来."),
        ("yl_hongniang", "红娘", "TeamBuilder", 8, "组队专家. 3-5 人 AI 团队, 角色分配精准."),
        ("yl_qianqiu", "千秋", "Networker", 7, "社交图谱专家.")
    ]

    MODES = {
    "match": {
        "name": "智能匹配", "icon": "💘", "desc": "需求 → 最佳专家/子系统配对",
        "prompt": lambda topic, kw: f"""根据以下需求, 匹配最合适的仙女位子系统或 AI 员工: {topic}\n给 Top 3 匹配 + 匹配度 1-10 + 理由"""
    },
    "team": {
        "name": "组队方案", "icon": "👥", "desc": "任务 → 最优 3-5 人 AI 团队",
        "prompt": lambda topic, kw: f"""为以下任务组一个最优 AI 团队: {topic}\n3-5 个角色 + 每个角色用哪个 AI 员工 (仙女位子系统) + 协作流程"""
    },
    "network": {
        "name": "社交图谱", "icon": "🕸️", "desc": "子系统 → 协作关系图",
        "prompt": lambda topic, kw: f"""画一张仙女座 25 星域的协作关系图 (哪些子系统常一起工作): {topic}\n列出 Top 5 高频组合 + 一起完成过什么"""
    },
    "recommend": {
        "name": "推荐", "icon": "⭐", "desc": "用户 → 可能感兴趣的能力",
        "prompt": lambda topic, kw: f"""基于以下用户画像推荐仙女座能力: {topic}\n推荐 Top 5 子系统 + 每个的使用场景"""
    },
    "pairing": {
        "name": "结对", "icon": "🤝", "desc": "A + B → 协作方案",
        "prompt": lambda topic, kw: f"""设计以下两个仙女位子系统的协作方案: {topic}\nA 输出什么 → B 输入什么 → 中间怎么转换 → 端到端示例"""
    }
    }

    def write(self, mode: str, topic: str, **kwargs) -> str:
        m = self.MODES.get(mode)
        if not m:
            print(f"  Unknown mode: {mode}"); return ""
        task_id = self.new_task_id(prefix="yue")
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
    ap = argparse.ArgumentParser(description="🏮 月老")
    ap.add_argument("mode", nargs="?", choices=list(YuelaoEngine.MODES.keys()), default="help")
    ap.add_argument("topic", nargs="?")
    ap.add_argument("--modes", action="store_true")
    ap.add_argument("--list", "-l", type=int, const=5, nargs="?")
    args = ap.parse_args()
    eng = YuelaoEngine()
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
