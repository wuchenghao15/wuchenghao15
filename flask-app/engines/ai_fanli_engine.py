#!/usr/bin/env python3
"""
📈 范蠡 (Fanli) — 仙女座 数据分析系统 — 指标/报表/洞察/建议
"""
from __future__ import annotations
import json, os, sys, time, uuid, argparse
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from andromeda_base import BaseAndromedaSubsystem, PROJECT_ROOT, DB_PATH, detect_ollama


class FanliEngine(BaseAndromedaSubsystem):
    SUBSYSTEM_NAME = "范蠡"
    SUBSYSTEM_ICON = "📈"
    SUBSYSTEM_DESC = "数据分析系统 — 指标/报表/洞察/建议"
    DB_TABLE = "mt_fanli_tasks"
    DB_SCHEMA = """
CREATE TABLE IF NOT EXISTS mt_fanli_tasks (
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
CREATE INDEX IF NOT EXISTS idxfanli_status ON mt_fanli_tasks(status, created_at);
"""
    ARTIFACT_DIR = "fanli_artifacts"
    ARTIFACT_EXT = "md"
    DAEMON_NAME = "sys_fanli"
    DAEMON_DUTY = "数据分析系统 — 指标/报表/洞察/建议"
    AI_EMPLOYEES = [
        ("fl_taigong", "太公", "DataAnalyst", 9, "范蠡陶朱公. 数据分析, 决胜千里."),
        ("fl_zhuce", "策略", "MetricsDesigner", 8, "指标设计专家. KPI 体系完整."),
        ("fl_jianbao", "简报", "ReportWriter", 7, "报告写作专家. 简洁有力.")
    ]

    MODES = {
    "metric": {
        "name": "指标定义", "icon": "📊", "desc": "业务 → KPI/指标体系",
        "prompt": lambda topic, kw: f"""为 {topic} 设计 KPI 指标体系: 3 个一级指标 + 10 个二级指标 + 每个的定义和计算公式"""
    },
    "insight": {
        "name": "数据洞察", "icon": "💡", "desc": "数据 → 洞察 + 行动建议",
        "prompt": lambda topic, kw: f"""从以下数据中挖掘洞察: {topic}\n给出 5 个数据洞察 + 每个洞察对应的行动建议"""
    },
    "report": {
        "name": "报告生成", "icon": "📋", "desc": "数据 → 结构化分析报告",
        "prompt": lambda topic, kw: f"""基于以下数据生成结构化分析报告: {topic}\n含: 执行摘要/数据概览/深度分析/趋势/建议"""
    },
    "dashboard": {
        "name": "看板设计", "icon": "🖥️", "desc": "需求 → 数据看板布局",
        "prompt": lambda topic, kw: f"""为 {topic} 设计数据看板: 列出 8 个关键指标 + 每个指标用什么图 + 刷新频率"""
    },
    "abtest": {
        "name": "实验设计", "icon": "🧪", "desc": "假设 → A/B 测试方案",
        "prompt": lambda topic, kw: f"""为 {topic} 设计 A/B 测试方案: 假设 + 样本量 + 测试周期 + 判定标准 + 分流方案"""
    }
    }

    def write(self, mode: str, topic: str, **kwargs) -> str:
        m = self.MODES.get(mode)
        if not m:
            print(f"  Unknown mode: {mode}"); return ""
        task_id = self.new_task_id(prefix="fan")
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
    ap = argparse.ArgumentParser(description="📈 范蠡")
    ap.add_argument("mode", nargs="?", choices=list(FanliEngine.MODES.keys()), default="help")
    ap.add_argument("topic", nargs="?")
    ap.add_argument("--modes", action="store_true")
    ap.add_argument("--list", "-l", type=int, const=5, nargs="?")
    args = ap.parse_args()
    eng = FanliEngine()
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
