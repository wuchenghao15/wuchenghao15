#!/usr/bin/env python3
"""
🧪 扁鹊 (Bianque) — 仙女座 代码诊断修复系统 — Bug定位/性能调优/重构建议
"""
from __future__ import annotations
import json, os, sys, time, uuid, argparse
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from andromeda_base import BaseAndromedaSubsystem, PROJECT_ROOT, DB_PATH, detect_ollama


class BianqueEngine(BaseAndromedaSubsystem):
    SUBSYSTEM_NAME = "扁鹊"
    SUBSYSTEM_ICON = "🧪"
    SUBSYSTEM_DESC = "代码诊断修复系统 — Bug定位/性能调优/重构建议"
    DB_TABLE = "mt_bianque_tasks"
    DB_SCHEMA = """
CREATE TABLE IF NOT EXISTS mt_bianque_tasks (
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
CREATE INDEX IF NOT EXISTS idxbianque_status ON mt_bianque_tasks(status, created_at);
"""
    ARTIFACT_DIR = "bianque_artifacts"
    ARTIFACT_EXT = "md"
    DAEMON_NAME = "sys_bianque"
    DAEMON_DUTY = "代码诊断修复系统 — Bug定位/性能调优/重构建议"
    AI_EMPLOYEES = [
        ("bq_yi", "医", "BugDoctor", 9, "扁鹊神医. 看一眼代码就知道 Bug 在哪, 药到病除."),
        ("bq_fang", "方", "PerfEngineer", 8, "性能优化专家. 慢代码变快, 快代码变飞."),
        ("bq_jian", "鉴", "CodeReviewer", 7, "代码体检专家. 坏味道一扫光.")
    ]

    MODES = {
    "diagnose": {
        "name": "Bug诊断", "icon": "🔍", "desc": "报错堆栈 → 根因 + 修复",
        "prompt": lambda topic, kw: f"""诊断代码问题: {topic}\n列出可能根因 (按概率) + 修复建议 + 验证方法"""
    },
    "performance": {
        "name": "性能调优", "icon": "⚡", "desc": "慢代码 → 优化方案 + 预期提升",
        "prompt": lambda topic, kw: f"""为以下慢代码/慢查询提出性能优化: {topic}\n给出 3 个优化点 + 预期提升百分比 + 改后代码"""
    },
    "refactor": {
        "name": "重构建议", "icon": "♻️", "desc": "代码坏味道 → 重构方案",
        "prompt": lambda topic, kw: f"""对以下代码给出重构建议: {topic}\n识别 3 种坏味道 + 重构方案 + 改后代码片段"""
    },
    "security": {
        "name": "安全扫描", "icon": "🛡️", "desc": "代码 → 安全漏洞清单 + 修复",
        "prompt": lambda topic, kw: f"""扫描以下代码的安全问题: {topic}\n列出 Top 5 风险 (SQL注入/XSS/硬编码/权限) + 修复代码"""
    },
    "testgen": {
        "name": "测试生成", "icon": "🧪", "desc": "函数 → pytest/unittest 测试用例",
        "prompt": lambda topic, kw: f"""为以下函数生成单元测试: {topic}\n覆盖正常/边界/异常 3 种情况, 用 pytest"""
    }
    }

    def write(self, mode: str, topic: str, **kwargs) -> str:
        m = self.MODES.get(mode)
        if not m:
            print(f"  Unknown mode: {mode}"); return ""
        task_id = self.new_task_id(prefix="bia")
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
    ap = argparse.ArgumentParser(description="🧪 扁鹊")
    ap.add_argument("mode", nargs="?", choices=list(BianqueEngine.MODES.keys()), default="help")
    ap.add_argument("topic", nargs="?")
    ap.add_argument("--modes", action="store_true")
    ap.add_argument("--list", "-l", type=int, const=5, nargs="?")
    args = ap.parse_args()
    eng = BianqueEngine()
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
