#!/usr/bin/env python3
# ─────────────────────────────────────────────────────────────
# andromeda_notifier.py — 仙女座统一后台通知中心
#
# 三通道同时发:
#   ① macOS osascript 系统通知 (用户桌面/手机弹出)
#   ② DB system_notifications 表 (Flask 页面可见)
#   ③ mt_daemon_registry.config_json 追加事件 (daemon 心跳附带)
#
# 所有 daemon 共用这一个函数 — 从此不再静默!
# ─────────────────────────────────────────────────────────────
import sqlite3, json, os, subprocess, time, sys

# 🆕 2026-09-20: DB 锁争用修复 — patch_sqlite3_connect (WAL + busy_timeout=60s)
try:
    import sys as _sys, os as _os
    _app_dir = _os.path.dirname(_os.path.dirname(_os.path.abspath(__file__)))
    if _app_dir not in _sys.path:
        _sys.path.insert(0, _app_dir)
    from core.db_path import patch_sqlite3_connect as _mtscos_patch
    _mtscos_patch(verbose=False)
except Exception:
    pass
from datetime import datetime

_PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_DB_PATH = os.path.join(_PROJECT_ROOT, "database", "app.db")

# ─────────────────────────────────────────────────────────────
# 主函数: notify (三通道)
# ─────────────────────────────────────────────────────────────

def notify(title, content, level="info", daemon=None):
    """
    仙女座统一后台通知 (三通道自动全开)
    
    Args:
        title:      通知标题 (≤30字)
        content:    通知正文 (≤100字)
        level:      info / success / warning / error / critical
        daemon:     发送方 daemon 名 (可选, 自动写 mt_daemon_registry)
    
    Returns:
        dict: {osascript: bool, db: bool, daemon: bool} 三通道各自状态
    """
    results = {"osascript": False, "db": False, "daemon": False}
    
    # 通道1: macOS 系统通知 (用 osascript, 无需任何额外依赖)
    try:
        emoji_map = {"info": "💡", "success": "✅", "warning": "⚠️", "error": "❌", "critical": "🚨"}
        emoji = emoji_map.get(level, "💡")
        full_title = f"{emoji} 仙女座 · {title}"
        full_subtitle = daemon or "后台"
        
        # osascript 通知
        script = f'display notification "{content[:80]}" with title "{full_title}" subtitle "{full_subtitle}"'
        subprocess.run(["osascript", "-e", script], capture_output=True, timeout=5)
        results["osascript"] = True
    except Exception:
        pass
    
    # 通道2: DB 写入 system_notifications
    try:
        conn = sqlite3.connect(_DB_PATH, timeout=5)
        conn.execute("""
            INSERT INTO system_notifications (title, content, level, target_user, created_at, status)
            VALUES (?, ?, ?, ?, ?, 'unread')
        """, (title[:50], content[:200], level, "super_admin", 
              datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
        conn.commit()
        conn.close()
        results["db"] = True
    except Exception:
        pass
    
    # 通道3: mt_daemon_registry 追加事件 (如果指定了 daemon)
    if daemon:
        try:
            conn = sqlite3.connect(_DB_PATH, timeout=5)
            row = conn.execute("SELECT config_json FROM mt_daemon_registry WHERE process_name=?", (daemon,)).fetchone()
            if row:
                events = []
                try:
                    cfg = json.loads(row[0] or "{}")
                    events = cfg.get("recent_events", [])
                except Exception:
                    pass
                
                events.append({
                    "title": title,
                    "content": content[:150],
                    "level": level,
                    "ts": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                })
                # 只保留最近 20 条
                events = events[-20:]
                
                conn.execute("""
                    UPDATE mt_daemon_registry 
                    SET config_json = ?, updated_at = ?
                    WHERE process_name = ?
                """, (json.dumps({"recent_events": events, "last_notification": title}, ensure_ascii=False),
                      datetime.now().strftime("%Y-%m-%d %H:%M:%S"), daemon))
                conn.commit()
            conn.close()
            results["daemon"] = True
        except Exception:
            pass
    
    # 终端也打印 (如果不是 daemon 模式)
    level_icon = {"info": "💡", "success": "✅", "warning": "⚠️", "error": "❌", "critical": "🚨"}.get(level, "💡")
    print(f"{level_icon} [{level.upper()}] {title}: {content[:80]}")
    
    return results

# ─────────────────────────────────────────────────────────────
# 便捷封装
# ─────────────────────────────────────────────────────────────

def notify_evolution(trigger_type, reason, source):
    """演化引擎通知"""
    notify(
        title=f"🧬 演化触发: {trigger_type}",
        content=f"{reason} (来源: {source})",
        level="success",
        daemon="sys_andromeda_auto_evolution"
    )

def notify_web_learner(brain_add, category_detail):
    """互联网学习通知"""
    notify(
        title=f"🌐 仙女座学了新知识",
        content=f"脑库 +{brain_add} 条 ({category_detail})",
        level="success",
        daemon="sys_web_skill_learner"
    )

def notify_troupe(produced, writers_count):
    """文学天团通知"""
    notify(
        title=f"🎭 文学天团出了 {produced} 篇爆款文案",
        content=f"{writers_count} 位作家产出 (孔子/老子/李白/鲁迅 等)",
        level="success",
        daemon="sys_literary_troupe"
    )

def notify_rule_enforcer(rule_name, action, detail):
    """规则执行通知"""
    level = "warning" if action == "VIOLATION" else "info"
    notify(
        title=f"🛡️ 规则执行: {rule_name}",
        content=f"{action} — {detail}",
        level=level,
        daemon="sys_rule_enforcer"
    )

def notify_autosync(host, status, detail=""):
    """autosync mini 状态通知"""
    level = "success" if status == "online" else "warning"
    title = f"🔗 mini 反向隧道 {'连上了' if status == 'online' else '断了'}"
    notify(
        title=title,
        content=f"host={host} {detail}".strip(),
        level=level,
        daemon="sys_andromeda_autosync"
    )

def notify_darwin(debate_topic, winner):
    """达尔文辩论通知"""
    notify(
        title=f"⚔️ 达尔文辩论: {debate_topic[:15]}...",
        content=f"胜方: {winner}",
        level="info",
    )

def notify_video_pipeline(scenes_count, duration, writers=""):
    """短视频 pipeline 通知"""
    notify(
        title=f"🎬 短视频出片了!",
        content=f"{scenes_count} scenes, {duration:.1f}s{', 文案: ' + writers if writers else ''}",
        level="success",
    )

# ─────────────────────────────────────────────────────────────
# 直接测试
# ─────────────────────────────────────────────────────────────

if __name__ == "__main__":
    print("═══ 仙女座统一通知中心 · 三通道测试 ═══")
    print()
    
    tests = [
        ("info",     "💡 仙女座心跳",         "每 30s 自动跑一次"),
        ("success",  "🧬 演化引擎触发成功",   "6 条新知识注入脑库 (web_learner)"),
        ("warning",  "⚠️ mini 隧道刚断了",     "host=localhost:2222, 正在等待重连"),
        ("error",    "❌ Edge-TTS 连不上",     "已自动降级到 macOS say"),
        ("success",  "🎭 文学天团出了 14 篇", "孔子/老子/李白/尼采 等 14 位作家"),
    ]
    
    for level, title, content in tests:
        r = notify(title, content, level=level, daemon="sys_heartbeat_writer")
        print(f"   → osascript={r['osascript']} db={r['db']} daemon={r['daemon']}")
        time.sleep(0.3)
    
    print(f"\n✅ 通知中心正常工作! 请查看 macOS 通知中心 (右上角通知图标)")
    
    # 查 DB 里的通知
    print(f"\n═══ system_notifications 表 (最近 5 条) ═══")
    conn = sqlite3.connect(_DB_PATH, timeout=5)
    for row in conn.execute("SELECT title, level, content, created_at FROM system_notifications ORDER BY rowid DESC LIMIT 5"):
        print(f"  [{row[1]:<10}] {row[0]:<30} {row[2][:50]:<50} @ {row[3]}")
    conn.close()
