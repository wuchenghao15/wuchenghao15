#!/usr/bin/env python3
"""
🔮 紫微 (Ziwei) — 仙女座 预测推演系统 — 趋势预测/风险预警/决策辅助
"""
from __future__ import annotations
import json, os, sys, time, uuid, argparse
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from andromeda_base import BaseAndromedaSubsystem, PROJECT_ROOT, DB_PATH, detect_ollama


class ZiweiEngine(BaseAndromedaSubsystem):
    SUBSYSTEM_NAME = "紫微"
    SUBSYSTEM_ICON = "🔮"
    SUBSYSTEM_DESC = "预测推演系统 — 趋势预测/风险预警/决策辅助"
    DB_TABLE = "mt_ziwei_tasks"
    DB_SCHEMA = """
CREATE TABLE IF NOT EXISTS mt_ziwei_tasks (
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
CREATE INDEX IF NOT EXISTS idxziwei_status ON mt_ziwei_tasks(status, created_at);
"""
    ARTIFACT_DIR = "ziwei_artifacts"
    ARTIFACT_EXT = "md"
    DAEMON_NAME = "sys_ziwei"
    DAEMON_DUTY = "预测推演系统 — 趋势预测/风险预警/决策辅助"
    AI_EMPLOYEES = [
        ("zw_tianji", "天机", "Forecaster", 9, "紫微预测大师. 趋势推演精准, 善于从混沌中找出规律."),
        ("zw_fengjiao", "风控", "RiskManager", 8, "风险预警专家. 提前识别黑天鹅事件."),
        ("zw_cehua", "策话", "Strategist", 7, "决策辅助专家. 多方案对比, 给出清晰推荐.")
    ]

    MODES = {
    "forecast": {
        "name": "趋势预测", "icon": "📈", "desc": "基于历史数据推演未来走势",
        "prompt": lambda topic, kw: f"""基于以下信息, 预测未来 3 个月的趋势: {topic}\n给出 5 个关键指标 + 置信度 + 拐点预警"""
    },
    "risk": {
        "name": "风险预警", "icon": "⚠️", "desc": "识别潜在风险点 + 应对方案",
        "prompt": lambda topic, kw: f"""分析以下场景的潜在风险: {topic}\n列出 Top 5 风险 + 概率 + 影响 + 应对策略"""
    },
    "decision": {
        "name": "决策辅助", "icon": "🧭", "desc": "多方案对比 + 推荐最优解",
        "prompt": lambda topic, kw: f"""针对下面的决策场景, 给出 3 个可选方案并推荐最优: {topic}\n每个方案的利弊 + 成本 + 风险"""
    },
    "scenario": {
        "name": "情景模拟", "icon": "🎲", "desc": "假设性推演 (如 X 发生会怎样)",
        "prompt": lambda topic, kw: f"""情景模拟: 假设 {topic}, 会发生什么?\n推演 3 个时间节点 (1天/1周/1月) 的连锁反应"""
    },
    "backcast": {
        "name": "归因分析", "icon": "🔍", "desc": "倒推事件根因 (为什么发生)",
        "prompt": lambda topic, kw: f"""归因分析: {topic}\n列出 5 个可能的根因, 按可能性排序, 给出验证方法"""
    }
    }

    def write(self, mode: str, topic: str, **kwargs) -> str:
        m = self.MODES.get(mode)
        if not m:
            print(f"  Unknown mode: {mode}"); return ""
        task_id = self.new_task_id(prefix="ziw")
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
    ap = argparse.ArgumentParser(description="🔮 紫微")
    ap.add_argument("mode", nargs="?", choices=list(ZiweiEngine.MODES.keys()), default="help")
    ap.add_argument("topic", nargs="?")
    ap.add_argument("--modes", action="store_true")
    ap.add_argument("--list", "-l", type=int, const=5, nargs="?")
    args = ap.parse_args()
    eng = ZiweiEngine()
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
