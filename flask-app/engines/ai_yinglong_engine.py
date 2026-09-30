#!/usr/bin/env python3
"""
🐉 应龙 (Yinglong) — 仙女座 自动化编排系统 — 任务流水线/定时任务/工作流
"""
from __future__ import annotations
import json, os, sys, time, uuid, argparse
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from andromeda_base import BaseAndromedaSubsystem, PROJECT_ROOT, DB_PATH, detect_ollama


class YinglongEngine(BaseAndromedaSubsystem):
    SUBSYSTEM_NAME = "应龙"
    SUBSYSTEM_ICON = "🐉"
    SUBSYSTEM_DESC = "自动化编排系统 — 任务流水线/定时任务/工作流"
    DB_TABLE = "mt_yinglong_tasks"
    DB_SCHEMA = """
CREATE TABLE IF NOT EXISTS mt_yinglong_tasks (
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
CREATE INDEX IF NOT EXISTS idxyinglong_status ON mt_yinglong_tasks(status, created_at);
"""
    ARTIFACT_DIR = "yinglong_artifacts"
    ARTIFACT_EXT = "json"
    DAEMON_NAME = "sys_yinglong"
    DAEMON_DUTY = "自动化编排系统 — 任务流水线/定时任务/工作流"
    AI_EMPLOYEES = [
        ("yl_dragon", "应龙", "WorkflowEngineer", 9, "应龙飞龙. 工作流设计, 行云流水."),
        ("yl_paibu", "排布", "PipelineDesigner", 8, "流水线编排专家. 步骤间数据无缝传递."),
        ("yl_dingshi", "定时", "Scheduler", 7, "定时任务专家. crontab 精准.")
    ]

    MODES = {
    "workflow": {
        "name": "工作流设计", "icon": "🔄", "desc": "目标 → 步骤式工作流 JSON",
        "prompt": lambda topic, kw: f"""设计一个工作流来完成: {topic}\n输出 JSON 格式: [{step_id, action, subsystem, input_schema, output_schema, depends_on}]"""
    },
    "pipeline": {
        "name": "流水线", "icon": "🔗", "desc": "多步任务 → 编排方案",
        "prompt": lambda topic, kw: f"""编排一个多步骤流水线: {topic}\n每步调哪个仙女位子系统 + 输入输出格式 + 条件分支"""
    },
    "cron": {
        "name": "定时任务", "icon": "⏰", "desc": "需求 → crontab 配置 + 说明",
        "prompt": lambda topic, kw: f"""设计定时任务: {topic}\n给出 crontab 表达式 + 任务脚本 + 日志策略"""
    },
    "trigger": {
        "name": "触发器", "icon": "⚡", "desc": "事件 → 触发条件 + 动作",
        "prompt": lambda topic, kw: f"""设计触发器: 当 {topic} 发生时, 触发什么动作?\n条件 (threshold/interval/event) + 动作 (调用哪个子系统)"""
    },
    "monitor": {
        "name": "监控规则", "icon": "📡", "desc": "指标 → 告警阈值 + 处理流程",
        "prompt": lambda topic, kw: f"""设计监控规则: {topic}\n监控哪些指标 + 告警阈值 + 通知方式 + 自动处理流程"""
    }
    }

    def write(self, mode: str, topic: str, **kwargs) -> str:
        m = self.MODES.get(mode)
        if not m:
            print(f"  Unknown mode: {mode}"); return ""
        task_id = self.new_task_id(prefix="yin")
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
    ap = argparse.ArgumentParser(description="🐉 应龙")
    ap.add_argument("mode", nargs="?", choices=list(YinglongEngine.MODES.keys()), default="help")
    ap.add_argument("topic", nargs="?")
    ap.add_argument("--modes", action="store_true")
    ap.add_argument("--list", "-l", type=int, const=5, nargs="?")
    args = ap.parse_args()
    eng = YinglongEngine()
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
