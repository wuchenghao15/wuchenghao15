#!/usr/bin/env python3
"""
🔭 羲和 (Xihe) — 仙女座 监控巡检系统 — 系统健康/日志分析/瓶颈定位
"""
from __future__ import annotations
import json, os, sys, time, uuid, argparse
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from andromeda_base import BaseAndromedaSubsystem, PROJECT_ROOT, DB_PATH, detect_ollama


class XiheEngine(BaseAndromedaSubsystem):
    SUBSYSTEM_NAME = "羲和"
    SUBSYSTEM_ICON = "🔭"
    SUBSYSTEM_DESC = "监控巡检系统 — 系统健康/日志分析/瓶颈定位"
    DB_TABLE = "mt_xihe_tasks"
    DB_SCHEMA = """
CREATE TABLE IF NOT EXISTS mt_xihe_tasks (
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
CREATE INDEX IF NOT EXISTS idxxihe_status ON mt_xihe_tasks(status, created_at);
"""
    ARTIFACT_DIR = "xihe_artifacts"
    ARTIFACT_EXT = "md"
    DAEMON_NAME = "sys_xihe"
    DAEMON_DUTY = "监控巡检系统 — 系统健康/日志分析/瓶颈定位"
    AI_EMPLOYEES = [
        ("xh_sun", "日御", "HealthChecker", 9, "羲和御日. 系统健康, 一查便知."),
        ("xh_chakan", "察看", "LogAnalyzer", 8, "日志分析专家. 错误分类, 趋势判断."),
        ("xh_pinggu", "评估", "CapacityPlanner", 7, "容量规划专家.")
    ]

    MODES = {
    "health": {
        "name": "健康检查", "icon": "💚", "desc": "目标系统 → 健康快照 + 评分",
        "prompt": lambda topic, kw: f"""为 {topic} 做健康检查: CPU/内存/磁盘/网络/进程/端口 → 每项 OK/WARN/CRIT + 总体评分 0-100"""
    },
    "loganalyze": {
        "name": "日志分析", "icon": "📋", "desc": "日志 → 错误分类 + 趋势 + Top N",
        "prompt": lambda topic, kw: f"""分析以下日志: {topic}\n错误分类 (按类型) + 最近趋势 (是否恶化) + Top 3 高频错误 + 解决建议"""
    },
    "bottleneck": {
        "name": "瓶颈定位", "icon": "🔍", "desc": "慢系统 → 瓶颈定位 + 优化",
        "prompt": lambda topic, kw: f"""定位性能瓶颈: {topic}\n从 CPU/IO/网络/DB 锁 4 个角度排查 → 瓶颈在哪里 + 优化方案 + 预期提升"""
    },
    "capacity": {
        "name": "容量规划", "icon": "📈", "desc": "当前负载 → 未来 6 个月扩容建议",
        "prompt": lambda topic, kw: f"""容量规划: {topic}\n当前使用率 → 增长趋势 → 什么时候需要扩容 → 扩多少 + 成本估算"""
    },
    "alarm": {
        "name": "告警规则", "icon": "🚨", "desc": "关键指标 → 告警阈值 + 升级策略",
        "prompt": lambda topic, kw: f"""设计告警规则: {topic}\n告警阈值 (WARN/CRIT) + 通知方式 (钉钉/飞书/短信) + 1-3 级升级策略"""
    }
    }

    def write(self, mode: str, topic: str, **kwargs) -> str:
        m = self.MODES.get(mode)
        if not m:
            print(f"  Unknown mode: {mode}"); return ""
        task_id = self.new_task_id(prefix="xih")
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
    ap = argparse.ArgumentParser(description="🔭 羲和")
    ap.add_argument("mode", nargs="?", choices=list(XiheEngine.MODES.keys()), default="help")
    ap.add_argument("topic", nargs="?")
    ap.add_argument("--modes", action="store_true")
    ap.add_argument("--list", "-l", type=int, const=5, nargs="?")
    args = ap.parse_args()
    eng = XiheEngine()
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
