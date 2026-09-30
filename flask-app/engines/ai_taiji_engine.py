#!/usr/bin/env python3
"""
⚖️ 太极 (TAIJI) — 仙女座动态平衡系统
==========================================

仙女座 25 域星中的【元系统域】专属子系统.
动态监控仙女座各子系统负载 + 冰山规则底座适配.
**最特殊的引擎** — 直接查 DB 聚合真实数据, 用 Ollama 分析给建议.
零 token 消耗 · 5 种元系统模式.

┌──────────────────────────────────────────────────────────┐
│   ⚖️ balance   负载平衡   (各子系统 task 数量/耗时/错误率) │
│   🧊 adapt     冰山适配   (冰山规则 vs 仙女座子系统)        │
│   🎛️ tune      参数调优   (temperature/max_tokens/timeout) │
│   📊 schedule  任务编排   (多子系统协同流水线)              │
│   🔍 diagnose  健康诊断   (全系统巡检 + 瓶颈定位)           │
└──────────────────────────────────────────────────────────┘

AI 员工: 太极(L9 平衡大师) · 冰山(L8 冰山专家) · 巡检(L7 健康检查)
"""

from __future__ import annotations
import json, os, sys, time, uuid, sqlite3
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from andromeda_base import BaseAndromedaSubsystem, PROJECT_ROOT, DB_PATH, detect_ollama


class TaijiEngine(BaseAndromedaSubsystem):
    """⚖️ 太极 — 仙女座动态平衡系统 (元系统)"""

    SUBSYSTEM_NAME = "太极"
    SUBSYSTEM_ICON = "⚖️"
    SUBSYSTEM_DESC = "动态平衡 · 负载监控 · 冰山适配 · 健康诊断"
    DB_TABLE = "mt_taiji_balance_log"
    DB_SCHEMA = """
CREATE TABLE IF NOT EXISTS mt_taiji_balance_log (
    id                  INTEGER PRIMARY KEY AUTOINCREMENT,
    task_id             TEXT UNIQUE,
    mode                TEXT NOT NULL,
    subsystem_status_json TEXT,
    load_metrics_json   TEXT,
    balance_suggestion  TEXT,
    final_text          TEXT,
    created_at          TEXT DEFAULT CURRENT_TIMESTAMP
);
CREATE TABLE IF NOT EXISTS mt_taiji_adjustments (
    id                  INTEGER PRIMARY KEY AUTOINCREMENT,
    adjustment_id       TEXT UNIQUE,
    target_subsystem    TEXT,
    param_name          TEXT,
    old_value           TEXT,
    new_value           TEXT,
    reason              TEXT,
    applied             INTEGER DEFAULT 0,
    created_at          TEXT DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX IF NOT EXISTS idx_taiji_mode ON mt_taiji_balance_log(mode);
"""
    ARTIFACT_DIR = "taiji_artifacts"
    ARTIFACT_EXT = "md"
    PREFERRED_MODELS = ["qwen2.5:14b-q5", "qwen2.5:14b"]
    DAEMON_NAME = "sys_taiji"
    DAEMON_DUTY = "⚖️ 太极动态平衡系统"

    AI_EMPLOYEES = [
        ("tj_taiji",   "太极", "balance_master",  9, "平衡大师. 跨子系统负载分析. 资源调度优化. 稳态维持."),
        ("tj_bingshan","冰山", "iceberg_expert",   8, "冰山规则底座专家. 规则冲突检测. 需求适配. 缺口分析."),
        ("tj_xunjian", "巡检", "health_inspector", 7, "系统健康检查. 瓶颈定位. 错误日志分析. 告警建议."),
    ]

    # ── 被监控的子系统 ──────────────────────────────────
    TARGET_TABLES = {
        "wqx":  "mt_wenquxing_tasks",
        "yc":   "mt_yaochi_tasks",
        "fy":   "mt_fanyin_tasks",
        "fh":   "mt_fanhua_tasks",
        "htl":  "mt_huntianling_calls",
        # 其他已知表
        "smart_mount": "mt_ai_smart_mount_processes",
    }

    # ── 5 种模式 ──────────────────────────────────────────
    MODES = {
        "balance": {
            "name": "负载平衡", "icon": "⚖️",
            "desc": "各子系统 task 数量/耗时/错误率",
            "prompt": lambda metrics: f"""# 太极 · 负载平衡 (balance)

## 实时数据 (来自 DB)
```json
{json.dumps(metrics, ensure_ascii=False, indent=2)}
```

## 任务
分析各子系统负载, 给出调度建议:
1. **热点识别**: 哪个子系统过载?
2. **冷点发现**: 哪个子系统闲置?
3. **均衡方案**: 具体的调度/限流/扩容建议
4. **阈值告警**: 建议设置的 warning/critical 阈值
"""
        },
        "adapt": {
            "name": "冰山适配", "icon": "🧊",
            "desc": "冰山规则 vs 仙女座子系统需求",
            "prompt": lambda metrics: f"""# 太极 · 冰山适配 (adapt)

## 当前冰山规则状态
```json
{json.dumps(metrics, ensure_ascii=False, indent=2)}
```

## 任务
分析冰山规则底座与仙女座子系统需求的匹配度:
1. **冲突检测**: 规则 vs 子系统能力的冲突点
2. **缺口识别**: 哪些子系统能力缺少规则覆盖
3. **适配建议**: 如何调整规则或子系统配置
4. **优先级**: 建议修复/适配的先后顺序
"""
        },
        "tune": {
            "name": "参数调优", "icon": "🎛️",
            "desc": "temperature/max_tokens/timeout 动态调整",
            "prompt": lambda metrics: f"""# 太极 · 参数调优 (tune)

## 各子系统参数快照
```json
{json.dumps(metrics, ensure_ascii=False, indent=2)}
```

## 任务
根据历史表现, 给出参数调优建议:
1. **temperature**: 不同任务类型的最优值 (creative=0.8, precise=0.3)
2. **max_tokens**: 根据 topic 长度/模式动态调整
3. **timeout_sec**: 慢模型/长文本需要更长超时
4. **并发数**: 同时运行的子系统上限
5. **Ollama 模型路由**: 什么任务用什么模型
"""
        },
        "schedule": {
            "name": "任务编排", "icon": "📊",
            "desc": "多子系统协同流水线",
            "prompt": lambda metrics: f"""# 太极 · 任务编排 (schedule)

## 子系统能力矩阵
```json
{json.dumps(metrics, ensure_ascii=False, indent=2)}
```

## 任务
设计多子系统协同流水线:
1. **典型场景**: 从创意→美术→音乐→分镜→API 的流水线
2. **依赖关系**: 哪些子系统必须等上游完成
3. **并行化**: 哪些可以并行执行
4. **失败降级**: 某子系统失败时的替代方案
5. **SLA**: 端到端耗时预估
"""
        },
        "diagnose": {
            "name": "健康诊断", "icon": "🔍",
            "desc": "全系统巡检 + 瓶颈定位",
            "prompt": lambda metrics: f"""# 太极 · 健康诊断 (diagnose)

## 系统巡检数据
```json
{json.dumps(metrics, ensure_ascii=False, indent=2)}
```

## 任务
全面健康诊断:
1. **Daemon 状态**: 哪些 daemon 异常?
2. **DB 健康**: 表大小/查询耗时/锁等待
3. **Ollama 状态**: 端口/模型/内存占用
4. **错误热点**: 哪个子系统失败率最高?
5. **瓶颈定位**: 端到端最耗时的环节
6. **修复建议**: 优先级排序的修复清单
"""
        },
    }

    # ────────────────────────────────────────────────────────
    # ⭐ 核心: 直接查 DB 聚合真实数据
    # ────────────────────────────────────────────────────────
    def _collect_load_metrics(self) -> dict:
        """聚合各子系统的真实运行数据"""
        metrics = {
            "timestamp": datetime.now().isoformat(),
            "subsystems": {},
            "daemons": {},
            "db_stats": {},
        }

        # 1. 各子系统 task 统计
        for key, table in self.TARGET_TABLES.items():
            try:
                row = self.db.execute(f"""
                    SELECT
                        COUNT(*) as total,
                        SUM(CASE WHEN status='done' THEN 1 ELSE 0 END) as done,
                        SUM(CASE WHEN status='failed' THEN 1 ELSE 0 END) as failed,
                        SUM(CASE WHEN status='generating' THEN 1 ELSE 0 END) as generating,
                        AVG(duration_sec) as avg_duration,
                        MAX(created_at) as last_activity
                    FROM {table}
                """).fetchone()
                metrics["subsystems"][key] = {
                    "table": table,
                    "total_tasks": row[0] or 0,
                    "done": row[1] or 0,
                    "failed": row[2] or 0,
                    "generating": row[3] or 0,
                    "failed_rate": round((row[2] or 0) / max(row[0] or 1, 1), 4),
                    "avg_duration_sec": round(row[4] or 0, 1),
                    "last_activity": row[5],
                }
            except sqlite3.OperationalError:
                metrics["subsystems"][key] = {
                    "table": table, "total_tasks": 0, "note": "表不存在或无数据"}

        # 2. Daemon 状态
        try:
            rows = self.db.execute("""
                SELECT process_name, status, restart_count, last_heartbeat
                FROM mt_daemon_registry
                ORDER BY process_name
            """).fetchall()
            for name, status, restarts, hb in rows:
                metrics["daemons"][name] = {
                    "status": status,
                    "restart_count": restarts or 0,
                    "last_heartbeat": hb,
                }
        except sqlite3.OperationalError as e:
            metrics["daemons"]["error"] = str(e)

        # 3. DB 基础统计
        try:
            # 表数量
            tables = self.db.execute(
                "SELECT name FROM sqlite_master WHERE type='table'").fetchall()
            metrics["db_stats"]["total_tables"] = len(tables)

            # WAL checkpoint (安全查询)
            metrics["db_stats"]["db_path"] = str(DB_PATH)
            metrics["db_stats"]["db_size_bytes"] = DB_PATH.stat().st_size if DB_PATH.exists() else 0
        except Exception as e:
            metrics["db_stats"]["error"] = str(e)

        return metrics

    def _collect_iceberg_status(self) -> dict:
        """收集冰山规则底座状态"""
        iceberg = {"rules": [], "employees": 0, "models": []}
        try:
            # AI 员工数量
            row = self.db.execute(
                "SELECT COUNT(*) FROM mt_andromeda_employee_registry").fetchone()
            iceberg["employees"] = row[0] if row else 0

            # daemon 列表
            rows = self.db.execute(
                "SELECT process_name, status FROM mt_daemon_registry").fetchall()
            iceberg["daemon_count"] = len(rows)
            iceberg["daemon_list"] = [{"name": r[0], "status": r[1]} for r in rows]

            # 尝试列规则表
            try:
                rules = self.db.execute(
                    "SELECT name FROM sqlite_master WHERE type='table' "
                    "AND name LIKE '%rule%'").fetchall()
                iceberg["rule_tables"] = [r[0] for r in rules]
            except Exception: pass

        except Exception as e:
            iceberg["error"] = str(e)
        return iceberg

    # ═══════════════════════════════════════════════════════
    def write(self, mode: str, topic: str = "", **kwargs) -> str:
        """太极生成入口 — 特殊: 直接查 DB 聚合真实数据"""
        m = self.MODES.get(mode)
        if not m:
            print(f"[{self.SUBSYSTEM_ICON}] ❌ 未知模式 {mode}, 可用: {list(self.MODES.keys())}")
            return ""

        task_id = self.new_task_id("tj")
        start = time.time()

        print(f"\n{'═'*56}")
        print(f"{self.SUBSYSTEM_ICON} 太极 · {m['icon']} {m['name']}")
        print(f"   task_id: {task_id}")
        print(f"   主题: {topic or '(自动聚合)'}")
        print(f"{'═'*56}")

        # ⭐ 太极特殊: 先查 DB 聚合真实数据
        print(f"  📊 正在聚合各子系统真实数据...")
        load_metrics = self._collect_load_metrics()
        iceberg_status = self._collect_iceberg_status()

        # 合并成一份完整快照
        combined_metrics = {
            "load": load_metrics,
            "iceberg": iceberg_status,
            "user_topic": topic,
        }

        # 先落库初始 (太极特殊, 先有数据再生成)
        self.db_insert_task(task_id, mode=mode,
            subsystem_status_json=json.dumps(iceberg_status, ensure_ascii=False),
            load_metrics_json=json.dumps(load_metrics, ensure_ascii=False))

        try:
            # 把真实数据喂给 Ollama 分析
            prompt = m["prompt"](combined_metrics)
            print(f"  ⏳ Ollama 分析中 (基于真实 DB 数据)...")
            analysis = self.ollama_generate(prompt, max_tokens=2048)
            duration = int(time.time() - start)

            # 保存 Markdown 报告
            report_path = self.artifact_path / f"{task_id}.md"
            report = (
                f"# ⚖️ 太极 · {m['icon']} {m['name']}\n\n"
                f"> **仙女座动态平衡系统** · 元系统\n"
                f"> 时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
                f"> task_id: {task_id}\n"
                f"> 耗时: {duration}s\n\n"
                f"---\n\n"
                f"## 📊 原始数据快照\n\n"
                f"```json\n{json.dumps(combined_metrics, ensure_ascii=False, indent=2)[:3000]}\n```\n\n"
                f"---\n\n"
                f"## 🤖 AI 分析与建议\n\n"
                f"{analysis}\n"
            )
            report_path.write_text(report, encoding="utf-8")

            # 更新 DB
            self.db.execute(
                "UPDATE mt_taiji_balance_log SET balance_suggestion=?, final_text=? "
                "WHERE task_id=?",
                (analysis[:2000], analysis, task_id))
            self.db.commit()

            # 打印摘要
            subs = load_metrics.get("subsystems", {})
            print(f"  📊 聚合 {len(subs)} 个子系统 | "
                  f"{len(load_metrics.get('daemons', {}))} 个 daemon | "
                  f"DB {load_metrics.get('db_stats', {}).get('total_tables', '?')} 表")
            print(f"  ✅ 完成: {duration}s")
            print(f"  📄 报告: {report_path}")

        except Exception as e:
            print(f"  💥 失败: {e}")
            raise

        return task_id


def _SELF_TEST():
    print("\n" + "=" * 56)
    print("⚖️ 太极 (TAIJI) — 自检测")
    print("=" * 56)
    try:
        e = TaijiEngine()
        print(f"  ✅ 引擎实例化成功")
        print(f"  ✅ DB_TABLE: {e.DB_TABLE}")
        print(f"  ✅ MODES: {list(e.MODES.keys())}")
        print(f"  ✅ AI_EMPLOYEES: {len(e.AI_EMPLOYEES)} 位")
        print(f"  ✅ TARGET_TABLES: {list(e.TARGET_TABLES.keys())}")
        # 测试数据聚合
        metrics = e._collect_load_metrics()
        print(f"  ✅ 负载聚合: {len(metrics.get('subsystems', {}))} 子系统 | "
              f"{len(metrics.get('daemons', {}))} daemon")
        e.register_daemon()
        e.register_ai_employees()
        print(f"  ✅ _SELF_TEST PASSED\n")
        return True
    except Exception as ex:
        print(f"  ❌ _SELF_TEST FAILED: {ex}\n")
        import traceback; traceback.print_exc()
        return False


if __name__ == "__main__":
    import argparse
    ap = argparse.ArgumentParser(description="⚖️ 太极 · 仙女座动态平衡系统 (元系统)")
    ap.add_argument("mode", nargs="?", default="balance",
                    help="模式: balance/adapt/tune/schedule/diagnose")
    ap.add_argument("topic", nargs="?", default="", help="可选: 聚焦主题")
    ap.add_argument("--modes", action="store_true", help="列出模式")
    ap.add_argument("--list", "-l", type=int, const=10, nargs="?", help="最近 N 个 task")
    ap.add_argument("--self-test", action="store_true", help="自检测")
    ap.add_argument("--snapshot", action="store_true", help="仅打印数据快照, 不调 Ollama")
    args = ap.parse_args()

    if args.self_test:
        _SELF_TEST()
    else:
        eng = TaijiEngine()
        if args.modes:
            print("⚖️ 太极 · 5 种元系统模式:")
            for k, v in eng.MODES.items():
                print(f"  {v['icon']} {k:10s} → {v['name']:10s} · {v['desc']}")
        elif args.snapshot:
            print("📊 太极数据快照 (实时 DB 聚合):")
            metrics = eng._collect_load_metrics()
            print(json.dumps(metrics, ensure_ascii=False, indent=2))
        elif args.list:
            tasks = eng.db.execute(
                "SELECT * FROM mt_taiji_balance_log ORDER BY id DESC LIMIT ?",
                (args.list,)).fetchall()
            cols = [c[1] for c in eng.db.execute(
                "PRAGMA table_info(mt_taiji_balance_log)").fetchall()]
            for t in tasks:
                d = dict(zip(cols, t))
                print(f"  {d.get('task_id','?')}  [{d.get('mode','?'):10s}] "
                      f"{str(d.get('created_at',''))[:19]}")
        else:
            task_id = eng.write(args.mode, args.topic)
            print(f"\n🎯 task_id={task_id}")
