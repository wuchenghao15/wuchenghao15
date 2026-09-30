#!/usr/bin/env python3
"""
🧬 伏羲 (Fuxi) — 仙女座 数据挖掘系统 — 关联分析/聚类/模式发现
"""
from __future__ import annotations
import json, os, sys, time, uuid, argparse
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from andromeda_base import BaseAndromedaSubsystem, PROJECT_ROOT, DB_PATH, detect_ollama


class FuxiEngine(BaseAndromedaSubsystem):
    SUBSYSTEM_NAME = "伏羲"
    SUBSYSTEM_ICON = "🧬"
    SUBSYSTEM_DESC = "数据挖掘系统 — 关联分析/聚类/模式发现"
    DB_TABLE = "mt_fuxi_tasks"
    DB_SCHEMA = """
CREATE TABLE IF NOT EXISTS mt_fuxi_tasks (
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
CREATE INDEX IF NOT EXISTS idxfuxi_status ON mt_fuxi_tasks(status, created_at);
"""
    ARTIFACT_DIR = "fuxi_artifacts"
    ARTIFACT_EXT = "md"
    DAEMON_NAME = "sys_fuxi"
    DAEMON_DUTY = "数据挖掘系统 — 关联分析/聚类/模式发现"
    AI_EMPLOYEES = [
        ("fx_bagua", "八卦", "DataMiner", 9, "伏羲八卦数据挖掘大师. 善从混沌数据中发现隐藏规律."),
        ("fx_yinyang", "阴阳", "PatternFinder", 8, "模式发现专家. 周期性/对称性/因果关系一眼看出."),
        ("fx_generation", "生成", "Profiler", 7, "画像生成专家. 用最少的数据勾勒最精准的画像.")
    ]

    MODES = {
    "associate": {
        "name": "关联发现", "icon": "🔗", "desc": "从海量数据中找隐藏关联",
        "prompt": lambda topic, kw: f"""在以下数据中发现隐藏的关联关系: {topic}\n用 -> 表示因果/相关, 给每个关联打分 1-10"""
    },
    "cluster": {
        "name": "聚类分组", "icon": "📊", "desc": "自动分组 + 各组特征画像",
        "prompt": lambda topic, kw: f"""把下面的数据分成 3-5 组, 每组给出一个标签 + 特征画像: {topic}"""
    },
    "pattern": {
        "name": "模式挖掘", "icon": "🔄", "desc": "发现重复模式/周期性/异常",
        "prompt": lambda topic, kw: f"""在下面的数据中挖掘模式: 周期性? 重复行为? 异常点? {topic}"""
    },
    "anomaly": {
        "name": "异常检测", "icon": "🚨", "desc": "识别离群点 + 可能原因",
        "prompt": lambda topic, kw: f"""异常检测: 在 {topic} 中找出异常点 (离群值/突变/不符合模式的), 说明为什么异常"""
    },
    "profile": {
        "name": "画像生成", "icon": "👤", "desc": "基于数据生成用户/群体画像",
        "prompt": lambda topic, kw: f"""基于以下信息生成画像: {topic}\n用 5 个维度描述 (如年龄/兴趣/行为/偏好/风险)"""
    }
    }

    def write(self, mode: str, topic: str, **kwargs) -> str:
        m = self.MODES.get(mode)
        if not m:
            print(f"  Unknown mode: {mode}"); return ""
        task_id = self.new_task_id(prefix="fux")
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
    ap = argparse.ArgumentParser(description="🧬 伏羲")
    ap.add_argument("mode", nargs="?", choices=list(FuxiEngine.MODES.keys()), default="help")
    ap.add_argument("topic", nargs="?")
    ap.add_argument("--modes", action="store_true")
    ap.add_argument("--list", "-l", type=int, const=5, nargs="?")
    args = ap.parse_args()
    eng = FuxiEngine()
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
