#!/usr/bin/env python3
"""
🌊 共工 (Gonggong) — 仙女座 资源管理系统 — 算力/存储/带宽/令牌管理
"""
from __future__ import annotations
import json, os, sys, time, uuid, argparse
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from andromeda_base import BaseAndromedaSubsystem, PROJECT_ROOT, DB_PATH, detect_ollama


class GonggongEngine(BaseAndromedaSubsystem):
    SUBSYSTEM_NAME = "共工"
    SUBSYSTEM_ICON = "🌊"
    SUBSYSTEM_DESC = "资源管理系统 — 算力/存储/带宽/令牌管理"
    DB_TABLE = "mt_gonggong_tasks"
    DB_SCHEMA = """
CREATE TABLE IF NOT EXISTS mt_gonggong_tasks (
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
CREATE INDEX IF NOT EXISTS idxgonggong_status ON mt_gonggong_tasks(status, created_at);
"""
    ARTIFACT_DIR = "gonggong_artifacts"
    ARTIFACT_EXT = "md"
    DAEMON_NAME = "sys_gonggong"
    DAEMON_DUTY = "资源管理系统 — 算力/存储/带宽/令牌管理"
    AI_EMPLOYEES = [
        ("gg_water", "水神", "ResourceManager", 9, "共工水神. 资源调度, 如臂使指."),
        ("gg_panpian", "盘盘", "Allocator", 8, "分配专家. 5 个子系统间最优分配."),
        ("gg_qingli", "清理", "CleanupExpert", 7, "清理方案专家.")
    ]

    MODES = {
    "resource": {
        "name": "资源盘点", "icon": "📦", "desc": "系统 → 资源使用快照",
        "prompt": lambda topic, kw: f"""盘点 {topic} 的资源使用: 算力/GPU/存储/带宽/令牌 → 每项总量/已用/剩余/使用率"""
    },
    "alloc": {
        "name": "资源分配", "icon": "🎲", "desc": "需求 → 最优分配方案",
        "prompt": lambda topic, kw: f"""为以下需求分配资源: {topic}\n在 5 个子系统间分配算力/存储/令牌 → 每项分到多少 + 依据"""
    },
    "cleanup": {
        "name": "清理", "icon": "🧹", "desc": "磁盘/缓存 → 清理方案 + 预计释放",
        "prompt": lambda topic, kw: f"""为 {topic} 设计清理方案: 哪些可以删 + 预计释放多少空间 + 风险 + 执行步骤"""
    },
    "quota": {
        "name": "配额管理", "icon": "📊", "desc": "用户/子系统 → 配额方案",
        "prompt": lambda topic, kw: f"""为 {topic} 设计配额方案: 每个用户/子系统的 token 上限/存储上限/API 调用频率 + 超额处理"""
    },
    "cost": {
        "name": "成本分析", "icon": "💰", "desc": "资源 → 月度/年度成本估算",
        "prompt": lambda topic, kw: f"""为 {topic} 做成本分析: 月度电费/云服务费/硬件折旧 → 给出降本 3 个建议"""
    }
    }

    def write(self, mode: str, topic: str, **kwargs) -> str:
        m = self.MODES.get(mode)
        if not m:
            print(f"  Unknown mode: {mode}"); return ""
        task_id = self.new_task_id(prefix="gon")
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
    ap = argparse.ArgumentParser(description="🌊 共工")
    ap.add_argument("mode", nargs="?", choices=list(GonggongEngine.MODES.keys()), default="help")
    ap.add_argument("topic", nargs="?")
    ap.add_argument("--modes", action="store_true")
    ap.add_argument("--list", "-l", type=int, const=5, nargs="?")
    args = ap.parse_args()
    eng = GonggongEngine()
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
