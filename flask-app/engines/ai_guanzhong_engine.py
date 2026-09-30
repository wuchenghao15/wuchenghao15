#!/usr/bin/env python3
"""
🏛️ 管仲 (Guanzhong) — 仙女座 治理规范系统 — 规则制定/流程优化/合规检查
"""
from __future__ import annotations
import json, os, sys, time, uuid, argparse
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from andromeda_base import BaseAndromedaSubsystem, PROJECT_ROOT, DB_PATH, detect_ollama


class GuanzhongEngine(BaseAndromedaSubsystem):
    SUBSYSTEM_NAME = "管仲"
    SUBSYSTEM_ICON = "🏛️"
    SUBSYSTEM_DESC = "治理规范系统 — 规则制定/流程优化/合规检查"
    DB_TABLE = "mt_guanzhong_tasks"
    DB_SCHEMA = """
CREATE TABLE IF NOT EXISTS mt_guanzhong_tasks (
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
CREATE INDEX IF NOT EXISTS idxguanzhong_status ON mt_guanzhong_tasks(status, created_at);
"""
    ARTIFACT_DIR = "guanzhong_artifacts"
    ARTIFACT_EXT = "md"
    DAEMON_NAME = "sys_guanzhong"
    DAEMON_DUTY = "治理规范系统 — 规则制定/流程优化/合规检查"
    AI_EMPLOYEES = [
        ("gz_xiangguo", "相国", "RuleMaker", 9, "管仲相国. 规则制定, 滴水不漏."),
        ("gz_libian", "利弊", "ProcessOptimizer", 8, "流程优化专家. 去掉冗余, 提升效率."),
        ("gz_jiancha", "检查", "ComplianceAuditor", 7, "检查清单专家. 20 项覆盖所有维度.")
    ]

    MODES = {
    "rule": {
        "name": "规则制定", "icon": "📜", "desc": "场景 → 完整规则条文",
        "prompt": lambda topic, kw: f"""为以下场景制定完整的规则/规范: {topic}\n含: 目的/适用范围/条款(5-10)/违规处理/生效日期"""
    },
    "process": {
        "name": "流程优化", "icon": "🔄", "desc": "现有流程 → 优化方案",
        "prompt": lambda topic, kw: f"""对以下流程提出优化: {topic}\n当前痛点 → 优化建议 → 新流程步骤 → 预期效果"""
    },
    "checklist": {
        "name": "检查清单", "icon": "✅", "desc": "领域 → 合规/质量检查清单",
        "prompt": lambda topic, kw: f"""为 {topic} 生成一个 20 项的检查清单 (每项 Yes/No + 备注): 覆盖合规/安全/质量/文档"""
    },
    "policy": {
        "name": "政策解读", "icon": "📖", "desc": "政策/法规 → 通俗解读 + 影响分析",
        "prompt": lambda topic, kw: f"""解读以下政策/法规: {topic}\n用大白话讲清楚 + 对仙女座系统的影响 + 需要调整什么"""
    },
    "gap": {
        "name": "差距分析", "icon": "📊", "desc": "现状 vs 目标 → 差距清单 + 行动计划",
        "prompt": lambda topic, kw: f"""差距分析: {topic}\n列出 5 个关键差距 + 填平所需时间/成本/资源 + 优先级排序"""
    }
    }

    def write(self, mode: str, topic: str, **kwargs) -> str:
        m = self.MODES.get(mode)
        if not m:
            print(f"  Unknown mode: {mode}"); return ""
        task_id = self.new_task_id(prefix="gua")
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
    ap = argparse.ArgumentParser(description="🏛️ 管仲")
    ap.add_argument("mode", nargs="?", choices=list(GuanzhongEngine.MODES.keys()), default="help")
    ap.add_argument("topic", nargs="?")
    ap.add_argument("--modes", action="store_true")
    ap.add_argument("--list", "-l", type=int, const=5, nargs="?")
    args = ap.parse_args()
    eng = GuanzhongEngine()
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
