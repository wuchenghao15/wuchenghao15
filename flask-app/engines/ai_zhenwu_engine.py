#!/usr/bin/env python3
"""
🛡️ 真武 (Zhenwu) — 仙女座 安全审查系统 — 代码/配置/API 安全扫描
"""
from __future__ import annotations
import json, os, sys, time, uuid, argparse
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from andromeda_base import BaseAndromedaSubsystem, PROJECT_ROOT, DB_PATH, detect_ollama


class ZhenwuEngine(BaseAndromedaSubsystem):
    SUBSYSTEM_NAME = "真武"
    SUBSYSTEM_ICON = "🛡️"
    SUBSYSTEM_DESC = "安全审查系统 — 代码/配置/API 安全扫描"
    DB_TABLE = "mt_zhenwu_tasks"
    DB_SCHEMA = """
CREATE TABLE IF NOT EXISTS mt_zhenwu_tasks (
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
CREATE INDEX IF NOT EXISTS idxzhenwu_status ON mt_zhenwu_tasks(status, created_at);
"""
    ARTIFACT_DIR = "zhenwu_artifacts"
    ARTIFACT_EXT = "md"
    DAEMON_NAME = "sys_zhenwu"
    DAEMON_DUTY = "安全审查系统 — 代码/配置/API 安全扫描"
    AI_EMPLOYEES = [
        ("zw_jiangjun", "将军", "SecurityAuditor", 9, "真武将军. 安全扫描, 火眼金睛."),
        ("zw_mishi", "谋士", "ThreatModeler", 8, "威胁建模专家. 攻击面无一遗漏."),
        ("zw_falv", "法吕", "ComplianceChecker", 7, "合规检查专家. 法律/隐私都覆盖.")
    ]

    MODES = {
    "scan": {
        "name": "安全扫描", "icon": "🔍", "desc": "代码 → 漏洞清单 + 风险等级",
        "prompt": lambda topic, kw: f"""对以下代码做安全扫描: {topic}\n列出所有发现的问题 (SQL注入/XSS/硬编码/权限/加密) + 风险等级 (HIGH/MEDIUM/LOW)"""
    },
    "config": {
        "name": "配置审计", "icon": "⚙️", "desc": "系统配置 → 安全建议",
        "prompt": lambda topic, kw: f"""审计以下系统配置的安全性: {topic}\n列出 5 个安全加固点 + 推荐配置"""
    },
    "threat": {
        "name": "威胁建模", "icon": "⚠️", "desc": "系统架构 → 攻击面分析",
        "prompt": lambda topic, kw: f"""对 {topic} 做威胁建模: 列出所有攻击面 + TOP 3 攻击场景 + 防御方案"""
    },
    "compliance": {
        "name": "合规检查", "icon": "📋", "desc": "行为 → 法律/隐私合规分析",
        "prompt": lambda topic, kw: f"""对以下操作做合规检查 (法律/隐私/数据保护): {topic}\n列出潜在违规点 + 建议"""
    },
    "hardening": {
        "name": "加固方案", "icon": "🔐", "desc": "系统 → 安全加固 checklist",
        "prompt": lambda topic, kw: f"""为 {topic} 提供安全加固方案: 列出 10 个加固项 + 实施优先级 + 预期收益"""
    }
    }

    def write(self, mode: str, topic: str, **kwargs) -> str:
        m = self.MODES.get(mode)
        if not m:
            print(f"  Unknown mode: {mode}"); return ""
        task_id = self.new_task_id(prefix="zhe")
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
    ap = argparse.ArgumentParser(description="🛡️ 真武")
    ap.add_argument("mode", nargs="?", choices=list(ZhenwuEngine.MODES.keys()), default="help")
    ap.add_argument("topic", nargs="?")
    ap.add_argument("--modes", action="store_true")
    ap.add_argument("--list", "-l", type=int, const=5, nargs="?")
    args = ap.parse_args()
    eng = ZhenwuEngine()
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
