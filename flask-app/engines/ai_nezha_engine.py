#!/usr/bin/env python3
"""
🔔 哪吒 (Nezha) — 仙女座 通知告警系统 — 多通道通知/告警升级/心跳保活
"""
from __future__ import annotations
import json, os, sys, time, uuid, argparse
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from andromeda_base import BaseAndromedaSubsystem, PROJECT_ROOT, DB_PATH, detect_ollama


class NezhaEngine(BaseAndromedaSubsystem):
    SUBSYSTEM_NAME = "哪吒"
    SUBSYSTEM_ICON = "🔔"
    SUBSYSTEM_DESC = "通知告警系统 — 多通道通知/告警升级/心跳保活"
    DB_TABLE = "mt_nezha_tasks"
    DB_SCHEMA = """
CREATE TABLE IF NOT EXISTS mt_nezha_tasks (
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
CREATE INDEX IF NOT EXISTS idxnezha_status ON mt_nezha_tasks(status, created_at);
"""
    ARTIFACT_DIR = "nezha_artifacts"
    ARTIFACT_EXT = "md"
    DAEMON_NAME = "sys_nezha"
    DAEMON_DUTY = "通知告警系统 — 多通道通知/告警升级/心跳保活"
    AI_EMPLOYEES = [
        ("nz_sanhai", "三太子", "NotifyMaster", 9, "哪吒三太子. 通知设计, 风火轮一般快."),
        ("nz_qiankun", "乾坤", "EscalationDesigner", 8, "升级策略专家. 1/2/3 级清晰."),
        ("nz_jinzhuan", "金转", "ChannelConfig", 7, "通道配置专家.")
    ]

    MODES = {
    "notify": {
        "name": "通知设计", "icon": "📢", "desc": "场景 → 通知模板 + 通道",
        "prompt": lambda topic, kw: f"""为以下场景设计通知: {topic}\n每个通知的标题/正文/优先级 (INFO/WARN/CRIT) + 发送通道 (飞书/邮件/短信)"""
    },
    "escalation": {
        "name": "升级策略", "icon": "📈", "desc": "告警 → 1-3 级升级流程",
        "prompt": lambda topic, kw: f"""设计告警升级策略: {topic}\n1 级 (通知值班) → 10 分钟无响应升级 2 级 (通知组长) → 20 分钟升级 3 级 (通知主管)"""
    },
    "heartbeat": {
        "name": "心跳方案", "icon": "💓", "desc": "服务 → 心跳/超时/恢复策略",
        "prompt": lambda topic, kw: f"""为 {topic} 设计心跳方案: 心跳间隔 + 超时阈值 + 连续几次失败触发告警 + 恢复后怎么通知"""
    },
    "channel": {
        "name": "通道配置", "icon": "📡", "desc": "通道 → 接入 + 鉴权 + 测试",
        "prompt": lambda topic, kw: f"""为 {topic} 配置通知通道: 飞书 webhook / SMTP 邮件 / API 调用 → 接入步骤 + 鉴权方式 + 测试代码"""
    },
    "template": {
        "name": "模板设计", "icon": "📝", "desc": "类型 → 通知模板 (变量+格式)",
        "prompt": lambda topic, kw: f"""为 {topic} 设计 5 个通知模板: 每个含 {{变量}} 占位符 + 示例 + 发送通道"""
    }
    }

    def write(self, mode: str, topic: str, **kwargs) -> str:
        m = self.MODES.get(mode)
        if not m:
            print(f"  Unknown mode: {mode}"); return ""
        task_id = self.new_task_id(prefix="nez")
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
    ap = argparse.ArgumentParser(description="🔔 哪吒")
    ap.add_argument("mode", nargs="?", choices=list(NezhaEngine.MODES.keys()), default="help")
    ap.add_argument("topic", nargs="?")
    ap.add_argument("--modes", action="store_true")
    ap.add_argument("--list", "-l", type=int, const=5, nargs="?")
    args = ap.parse_args()
    eng = NezhaEngine()
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
