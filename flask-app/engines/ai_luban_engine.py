#!/usr/bin/env python3
"""
⚙️ 鲁班 (Luban) — 仙女座 硬件/Arduino工程系统 — 电路图/代码/DIY方案
"""
from __future__ import annotations
import json, os, sys, time, uuid, argparse
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from andromeda_base import BaseAndromedaSubsystem, PROJECT_ROOT, DB_PATH, detect_ollama


class LubanEngine(BaseAndromedaSubsystem):
    SUBSYSTEM_NAME = "鲁班"
    SUBSYSTEM_ICON = "⚙️"
    SUBSYSTEM_DESC = "硬件/Arduino工程系统 — 电路图/代码/DIY方案"
    DB_TABLE = "mt_luban_tasks"
    DB_SCHEMA = """
CREATE TABLE IF NOT EXISTS mt_luban_tasks (
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
CREATE INDEX IF NOT EXISTS idxluban_status ON mt_luban_tasks(status, created_at);
"""
    ARTIFACT_DIR = "luban_artifacts"
    ARTIFACT_EXT = "md"
    DAEMON_NAME = "sys_luban"
    DAEMON_DUTY = "硬件/Arduino工程系统 — 电路图/代码/DIY方案"
    AI_EMPLOYEES = [
        ("lb_shifu", "师傅", "CircuitDesigner", 9, "鲁班大师. 电路图 + 代码 + 成本全考虑."),
        ("lb_xiaojiang", "小将", "FirmwareDev", 8, "Arduino 固件专家. 模块化、中文注释、含 setup/loop."),
        ("lb_gongjiang", "工匠", "DIYGuide", 7, "DIY 指南专家. 新手友好, 每步都有图和坑.")
    ]

    MODES = {
    "circuit": {
        "name": "电路设计", "icon": "🔌", "desc": "需求 → 电路图 + 元件清单",
        "prompt": lambda topic, kw: f"""为以下需求设计电路图: {topic}\n给出元件清单 (型号+数量+单价) + 连线说明 + 注意事项"""
    },
    "firmware": {
        "name": "固件代码", "icon": "💾", "desc": "功能需求 → Arduino 代码",
        "prompt": lambda topic, kw: f"""为以下功能写 Arduino (Uno/Nano) 代码: {topic}\n要求: 中文注释 + 模块化 + 含 setup/loop"""
    },
    "diy": {
        "name": "DIY方案", "icon": "🛠️", "desc": "给新手的分步制作指南",
        "prompt": lambda topic, kw: f"""写一个新手能跟着做的分步 DIY 指南: {topic}\n每步配文字说明 + 关键代码片段 + 常见坑"""
    },
    "sensor": {
        "name": "传感器选型", "icon": "📡", "desc": "需求 → 推荐传感器 + 接线 + 代码",
        "prompt": lambda topic, kw: f"""根据测量需求推荐传感器: {topic}\n对比 3 款 (精度/价格/难度/是否推荐) + 接线图描述 + 测试代码"""
    },
    "troubleshoot": {
        "name": "硬件排障", "icon": "🔧", "desc": "现象 → 可能原因 + 排查步骤",
        "prompt": lambda topic, kw: f"""硬件故障排障: 现象是 {topic}\n列出 5 个可能原因 + 逐步排查流程 + 解决办法"""
    }
    }

    def write(self, mode: str, topic: str, **kwargs) -> str:
        m = self.MODES.get(mode)
        if not m:
            print(f"  Unknown mode: {mode}"); return ""
        task_id = self.new_task_id(prefix="lub")
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
    ap = argparse.ArgumentParser(description="⚙️ 鲁班")
    ap.add_argument("mode", nargs="?", choices=list(LubanEngine.MODES.keys()), default="help")
    ap.add_argument("topic", nargs="?")
    ap.add_argument("--modes", action="store_true")
    ap.add_argument("--list", "-l", type=int, const=5, nargs="?")
    args = ap.parse_args()
    eng = LubanEngine()
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
