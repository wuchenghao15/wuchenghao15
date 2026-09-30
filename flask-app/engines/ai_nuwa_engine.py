#!/usr/bin/env python3
"""
🌐 女娲 (Nuwa) — 仙女座 前端UI/UX生成系统 — 页面/组件/设计稿自动生成
"""
from __future__ import annotations
import json, os, sys, time, uuid, argparse
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from andromeda_base import BaseAndromedaSubsystem, PROJECT_ROOT, DB_PATH, detect_ollama


class NuwaEngine(BaseAndromedaSubsystem):
    SUBSYSTEM_NAME = "女娲"
    SUBSYSTEM_ICON = "🌐"
    SUBSYSTEM_DESC = "前端UI/UX生成系统 — 页面/组件/设计稿自动生成"
    DB_TABLE = "mt_nuwa_tasks"
    DB_SCHEMA = """
CREATE TABLE IF NOT EXISTS mt_nuwa_tasks (
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
CREATE INDEX IF NOT EXISTS idxnuwa_status ON mt_nuwa_tasks(status, created_at);
"""
    ARTIFACT_DIR = "nuwa_artifacts"
    ARTIFACT_EXT = "html"
    DAEMON_NAME = "sys_nuwa"
    DAEMON_DUTY = "前端UI/UX生成系统 — 页面/组件/设计稿自动生成"
    AI_EMPLOYEES = [
        ("nw_niangniang", "娘娘", "PageGen", 9, "女娲造人. 描述到完整页面, 一行代码一行心血."),
        ("nw_fashou", "巧手", "ComponentGen", 8, "组件生成专家. Vue/React 组件, Props/Events/Slots 齐全."),
        ("nw_meiyu", "美玉", "Designer", 7, "设计规范专家. Element Plus Token, 配色精准.")
    ]

    MODES = {
    "page": {
        "name": "页面生成", "icon": "📄", "desc": "描述 → 完整 HTML 页面代码",
        "prompt": lambda topic, kw: f"""根据需求生成一个完整的单文件 HTML 页面 (含 CSS + JS): {topic}\n要求: 现代化设计, 响应式, 用 Element Plus 风格配色 (#0B0A1E 主色)"""
    },
    "component": {
        "name": "组件生成", "icon": "🧩", "desc": "描述 → Vue/React 组件代码",
        "prompt": lambda topic, kw: f"""生成一个 Vue 单文件组件: {topic}\n<template>+<script>+<style scoped>"""
    },
    "design": {
        "name": "设计规范", "icon": "🎨", "desc": "生成 Element Plus 风格设计 Token",
        "prompt": lambda topic, kw: f"""为以下场景生成完整设计 Token (颜色/字体/间距/圆角): {topic}"""
    },
    "layout": {
        "name": "布局方案", "icon": "📐", "desc": "同需求 3 种布局方案对比",
        "prompt": lambda topic, kw: f"""为 {topic} 给出 3 种布局方案 (侧边栏/顶栏/分栏), 每种的优缺点 + 适用场景"""
    },
    "css": {
        "name": "CSS 生成", "icon": "🎯", "desc": "描述 → 纯 CSS 动画/效果代码",
        "prompt": lambda topic, kw: f"""生成纯 CSS (无 JS) 实现的效果: {topic}"""
    }
    }

    def write(self, mode: str, topic: str, **kwargs) -> str:
        m = self.MODES.get(mode)
        if not m:
            print(f"  Unknown mode: {mode}"); return ""
        task_id = self.new_task_id(prefix="nuw")
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
    ap = argparse.ArgumentParser(description="🌐 女娲")
    ap.add_argument("mode", nargs="?", choices=list(NuwaEngine.MODES.keys()), default="help")
    ap.add_argument("topic", nargs="?")
    ap.add_argument("--modes", action="store_true")
    ap.add_argument("--list", "-l", type=int, const=5, nargs="?")
    args = ap.parse_args()
    eng = NuwaEngine()
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
