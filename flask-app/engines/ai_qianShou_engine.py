#!/usr/bin/env python3
"""
🤲 千手 (Qianshou) — 仙女座 中枢神经元系统 — 统一路由/负载均衡/请求汇聚
"""
from __future__ import annotations
import json, os, sys, time, uuid, argparse
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from andromeda_base import BaseAndromedaSubsystem, PROJECT_ROOT, DB_PATH, detect_ollama


class QianshouEngine(BaseAndromedaSubsystem):
    SUBSYSTEM_NAME = "千手"
    SUBSYSTEM_ICON = "🤲"
    SUBSYSTEM_DESC = "中枢神经元系统 — 统一路由/负载均衡/请求汇聚"
    DB_TABLE = "mt_qianshou_routes"
    DB_SCHEMA = """
CREATE TABLE IF NOT EXISTS mt_qianshou_routes (
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
CREATE INDEX IF NOT EXISTS idxqianShou_status ON mt_qianshou_routes(status, created_at);
"""
    ARTIFACT_DIR = "qianshou_artifacts"
    ARTIFACT_EXT = "json"
    DAEMON_NAME = "sys_qianshou"
    DAEMON_DUTY = "中枢神经元系统 — 统一路由/负载均衡/请求汇聚"
    AI_EMPLOYEES = [
        ("qs_router", "路由", "Router", 9, "千手中枢路由专家. 快速判断请求类型 → 精准路由到对应子系统. 输出 JSON 格式路由决策."),
        ("qs_compose", "编排", "Composer", 8, "多子系统编排专家. 设计流水线让多个子系统协同完成复杂任务. 输出步骤清单."),
        ("qs_merge", "汇聚", "Merger", 7, "多源结果汇聚专家. 把分散的子系统输出整合成统一、连贯的最终报告.")
    ]

    MODES = {
    "route": {
        "name": "智能路由", "icon": "🛤️", "desc": "根据请求类型分发到对应子系统",
        "prompt": lambda topic, kw: f"""分析下面的请求, 决定应该路由到哪个仙女位子系统 (文曲星/瑶池/梵音/繁花/混天绫/太极 等), 给出理由和完整路由方案:\n{topic}"""
    },
    "compose": {
        "name": "多子系统编排", "icon": "🔗", "desc": "串联多个子系统完成复杂任务",
        "prompt": lambda topic, kw: f"""设计一个多子系统协作流水线, 完成: {topic}\n列出每个环节用哪个子系统 + 输入输出格式"""
    },
    "broadcast": {
        "name": "广播通知", "icon": "📢", "desc": "向所有子系统广播状态更新",
        "prompt": lambda topic, kw: f"""写一条仙女座全系统广播通知, 主题: {topic}"""
    },
    "merge": {
        "name": "结果汇聚", "icon": "🔀", "desc": "聚合多个子系统输出为统一结果",
        "prompt": lambda topic, kw: f"""把下面来自多个子系统的输出, 汇聚成一个统一的最终报告:\n{topic}"""
    },
    "registry": {
        "name": "注册表", "icon": "📋", "desc": "查看所有子系统状态/能力/健康度",
        "prompt": lambda topic, kw: f"""列出仙女座 25 星域所有子系统的能力清单: {topic}"""
    }
    }

    def write(self, mode: str, topic: str, **kwargs) -> str:
        m = self.MODES.get(mode)
        if not m:
            print(f"  Unknown mode: {mode}"); return ""
        task_id = self.new_task_id(prefix="qia")
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
    ap = argparse.ArgumentParser(description="🤲 千手")
    ap.add_argument("mode", nargs="?", choices=list(QianshouEngine.MODES.keys()), default="help")
    ap.add_argument("topic", nargs="?")
    ap.add_argument("--modes", action="store_true")
    ap.add_argument("--list", "-l", type=int, const=5, nargs="?")
    args = ap.parse_args()
    eng = QianshouEngine()
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
