#!/usr/bin/env python3
"""
🌱 神农 (Shennong) — 仙女座 教育/学习系统 — 课程/教案/学习路径自动生成
"""
from __future__ import annotations
import json, os, sys, time, uuid, argparse
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from andromeda_base import BaseAndromedaSubsystem, PROJECT_ROOT, DB_PATH, detect_ollama


class ShennongEngine(BaseAndromedaSubsystem):
    SUBSYSTEM_NAME = "神农"
    SUBSYSTEM_ICON = "🌱"
    SUBSYSTEM_DESC = "教育/学习系统 — 课程/教案/学习路径自动生成"
    DB_TABLE = "mt_shennong_tasks"
    DB_SCHEMA = """
CREATE TABLE IF NOT EXISTS mt_shennong_tasks (
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
CREATE INDEX IF NOT EXISTS idxshennong_status ON mt_shennong_tasks(status, created_at);
"""
    ARTIFACT_DIR = "shennong_artifacts"
    ARTIFACT_EXT = "md"
    DAEMON_NAME = "sys_shennong"
    DAEMON_DUTY = "教育/学习系统 — 课程/教案/学习路径自动生成"
    AI_EMPLOYEES = [
        ("sn_yanhuang", "炎黄", "CourseDesigner", 9, "神农尝百草. 课程设计, 因材施教."),
        ("sn_kejia", "教案", "LessonWriter", 8, "教案专家. 导入/新授/互动/总结."),
        ("sn_fuxi", "伏羲", "PathFinder", 7, "学习路径专家. 从零基础到精通.")
    ]

    MODES = {
    "course": {
        "name": "课程设计", "icon": "📚", "desc": "主题 → 完整课程大纲 (6-10 节)",
        "prompt": lambda topic, kw: f"""为 {topic} 设计一个 8 节的课程大纲: 每节标题 + 3 个知识点 + 1 个小练习 + 预计时长"""
    },
    "lesson": {
        "name": "教案", "icon": "📖", "desc": "单课 → 详细教案 (目标/内容/互动/作业)",
        "prompt": lambda topic, kw: f"""为以下课题写详细教案: {topic}\n含: 教学目标/导入/新授/互动/总结/作业/板书设计"""
    },
    "path": {
        "name": "学习路径", "icon": "🗺️", "desc": "起点 → 目标 → 分阶段路径图",
        "prompt": lambda topic, kw: f"""从零基础到精通 {topic} 的学习路径: 5 个阶段 + 每个阶段的里程碑 + 推荐资源"""
    },
    "quiz": {
        "name": "小测验", "icon": "📝", "desc": "课程 → 5 题小测验 + 答案解析",
        "prompt": lambda topic, kw: f"""为 {topic} 生成 5 道随堂小测验: 3 选择 + 2 填空 + 答案 + 解析"""
    },
    "feedback": {
        "name": "学习反馈", "icon": "💬", "desc": "答题记录 → 针对性建议",
        "prompt": lambda topic, kw: f"""基于以下答题记录给学习反馈: {topic}\n分析薄弱点 + 针对性练习建议 + 鼓励"""
    }
    }

    def write(self, mode: str, topic: str, **kwargs) -> str:
        m = self.MODES.get(mode)
        if not m:
            print(f"  Unknown mode: {mode}"); return ""
        task_id = self.new_task_id(prefix="she")
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
    ap = argparse.ArgumentParser(description="🌱 神农")
    ap.add_argument("mode", nargs="?", choices=list(ShennongEngine.MODES.keys()), default="help")
    ap.add_argument("topic", nargs="?")
    ap.add_argument("--modes", action="store_true")
    ap.add_argument("--list", "-l", type=int, const=5, nargs="?")
    args = ap.parse_args()
    eng = ShennongEngine()
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
