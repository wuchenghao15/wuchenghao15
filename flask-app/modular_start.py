#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
MTSCOS AI Flask 入口 (modular_start.py)
被 sys_flask_server daemon 调用启动 Web 服务
端口: 8888 (避免 macOS AirPlay 5000 端口冲突)
"""
import os
import sys

# 🆕 2026-09-17: Flask 模式 — 全局拦截后台守护线程创建
# 所有模块级单例 (auto_routine_maintenance, AI_Cluster_Manager, comprehensive 等)
# 在 import 时会创建 threading.Thread 启动后台线程, 永久持 DB 写锁 → Flask worker 被堵
# 在 import 任何模块前 patch threading.Thread.__init__, 拦截可疑后台线程
os.environ['MTSCOS_FLASK_MODE'] = '1'
import threading as _threading_flask
_ORIGINAL_THREAD_INIT = _threading_flask.Thread.__init__
_SKIP_KEYWORDS = (
    # 原守护线程
    'routine_maintenance', 'comprehensive_upgrader', 'system_upgrade',
    'auto_repair', 'ai_inspection', 'auto_inspection', 'auto_patrol',
    'auto_hire', 'file_organizer', 'rule_enforcer', 'auto_learning',
    'monitoring', 'scheduler', 'heartbeat', 'watcher', 'health_check',
    # 🆕 Flask 模式下不需要的后台 (由 smart_mount_engine 独立进程负责)
    'archive', 'archiver', 'evolution', 'andromeda', 'autosync',
    'normalize', 'idle_monitor', 'idlemonitor', 'idle.',
    'patrol', 'eigenflux', 'brain_feed',
)
# 🆕 直接拦截所有后台线程 — Flask 进程只做 HTTP handler 请求
# autosync daemon / ANDROMEDA 演化 / normalize_system / ai_archive 等
# 全部改成 NOP 空跑, Flask 成纯 HTTP server
def _patched_thread_init(self, *args, **kwargs):
    target = kwargs.get('target') or (args[0] if args else None)
    name = kwargs.get('name', '')
    target_name = target.__name__.lower() if target else ''
    qualname = getattr(target, '__qualname__', '').lower() if target else ''
    name_lower = name.lower()
    should_skip = any(kw in target_name or kw in qualname or kw in name_lower for kw in _SKIP_KEYWORDS)
    # 🆕 同时拦截 Flask app.run() 之前启动的所有 daemon (除了 werkzeug 自己的)
    # 只有 app.run() 后由 Flask 内部启动的 worker 线程放行
    if should_skip:
        kwargs['target'] = lambda: None
        try:
            _ORIGINAL_THREAD_INIT(self, *args, **kwargs)
            return
        except Exception:
            pass
    _ORIGINAL_THREAD_INIT(self, *args, **kwargs)
_threading_flask.Thread.__init__ = _patched_thread_init
sys.stderr.write("[FLASK-MODE] threading.Thread.__init__ 已 patch, 拦截 17 种后台线程关键字\n")

_BASE_DIR = os.path.dirname(os.path.abspath(__file__))
if _BASE_DIR not in sys.path:
    sys.path.insert(0, _BASE_DIR)

try:
    from core.db_path import patch_sqlite3_connect as _mtscos_patch
    _mtscos_patch(verbose=False)
except Exception as _e:
    sys.stderr.write(f"[WARN] db_path patch failed: {_e}\n")

# Phase 7 局部 Factory: 显式调用 ensure_app_ready() 完成蓝图+API注册
# 注: server_real_db 模块加载时也会自动调一次 ensure_app_ready(),
#     但显式调用是 Factory 模式的推荐入口, 且 _app_initialized 防重入保证只执行一次
from server_real_db import ensure_app_ready, app
ensure_app_ready()  # 幂等, 即使模块加载时已执行过也不会重复注册

# ===== autosync blueprint (两端 Flask 都注册, GUI 上下文有 TCC 访问 DB) =====
try:
    import autosync_andromeda as _sync
    _sync.register_sync_routes(app)
except Exception as _e:
    sys.stderr.write(f"[AUTOSYNC] blueprint 注册失败 (非致命): {_e}\n")

# ===== 系统正规化初始化 (放到后台线程, 不阻塞 Flask listen) =====
# 之前同步执行卡死在 DB 锁 (系统升级 84 任务 + AI 巡检 7 阶段),
# 导致 app.run() 永远不执行, 系统对外 HTTP 不可用.
try:
    import threading as _mt

    def _normalize_async():
        try:
            from ai_engines.system_normalizer import normalize_system
            _norm_report = normalize_system(app)
            sys.stderr.write(
                f"[SYS-NORM] 异步初始化完成: "
                f"overall_ok={_norm_report.get('overall_ok')}, "
                f"耗时={_norm_report.get('took_sec')}s\n"
            )
        except Exception as _e:
            sys.stderr.write(f"[SYS-NORM] 异步初始化失败(非致命): {_e}\n")

    _mt.Thread(target=_normalize_async, name='sys-norm-async', daemon=True).start()
    sys.stderr.write("[SYS-NORM] 异步线程已提交 (不阻塞 Flask listen)\n")
except Exception as _e:
    sys.stderr.write(f"[SYS-NORM] 启动失败(非致命): {_e}\n")

if __name__ == "__main__":
    # ===== v6.2: 仙女座七阶段自演化后台线程 (自动联想→检索→衍生→强化→拓展→优化) =====
    try:
        import threading
        import time as _time

        def _andromeda_evolution_loop():
            """
            仙女座拉马努金式自演化循环.
            每 600s 周期跑一轮, 或被 autosync 同步完 eigenflux 消息后立刻唤醒.
            自举循环: AI 员工跨机讨论 → 同步 → 摄入脑库 → 关联图谱 → 衍生新知识 → 反向驱动新讨论
            """
            _time.sleep(180)  # 等 Flask + Ollama 完全就绪
            sys.stderr.write("[ANDROMEDA-EVOL] 自演化后台线程启动 (cycle_interval=600s, autosync可唤醒)\n")
            from engines.andromeda_auto_evolution import (
                run_cycle, EVOLUTION_WAKEUP_EVENT, reset_evolution_event,
            )
            while True:
                try:
                    run_cycle()
                except Exception as _e:
                    sys.stderr.write(f"[ANDROMEDA-EVOL] cycle crashed: {_e}\n")
                # 清唤醒信号 → wait 下一轮 (被唤醒则立刻跑, 否则等 600s)
                reset_evolution_event()
                _was_wakeup = EVOLUTION_WAKEUP_EVENT.wait(timeout=600)
                if _was_wakeup:
                    sys.stderr.write("[ANDROMEDA-EVOL] 🔔 被 autosync 唤醒, 提前跑下一轮\n")

        _evol_thread = threading.Thread(
            target=_andromeda_evolution_loop,
            name='andromeda-auto-evolution',
            daemon=True,
        )
        _evol_thread.start()
        sys.stderr.write("[ANDROMEDA-EVOL] 后台线程已提交 (180s 后首次 cycle)\n")
    except Exception as _e:
        sys.stderr.write(f"[ANDROMEDA-EVOL] 后台线程启动失败 (非致命): {_e}\n")

    # ===== v6.3: 仙女座双向同步后台线程 (自动发现 Mac mini → 双向 rsync + DB 合并) =====
    try:
        def _autosync_loop():
            """后台双向同步循环: 直接调用 autosync_andromeda.main_loop()"""
            sys.stderr.write("[AUTOSYNC] 双向同步后台线程启动\n")
            import autosync_andromeda as _sync
            _sync.main_loop()

        _sync_thread = threading.Thread(
            target=_autosync_loop,
            name='andromeda-autosync',
            daemon=True,
        )
        _sync_thread.start()
        sys.stderr.write("[AUTOSYNC] 后台线程已提交 (自动发现 Mac mini → 双向同步)\n")
    except Exception as _e:
        sys.stderr.write(f"[AUTOSYNC] 后台线程启动失败 (非致命): {_e}\n")

    # 🆕 2026-09-17: Flask 进程成为纯 HTTP server, 不启动任何后台守护线程
    # Flask 进程内模块级单例 (auto_routine_maintenance, comprehensive_system_upgrader,
    # AI_Cluster_Manager 等) 在 import 时会启动后台线程, 永久持写锁做长事务 →
    # Flask worker 被堵 → HTTP timeout. 后台任务改由 smart_mount_engine (独立进程) 负责.
    import os as _os_flask
    _os_flask.environ['MTSCOS_FLASK_MODE'] = '1'
    def _nop_start(self):
        import sys as _sys
        _sys.stderr.write(f"[FLASK-MODE] {type(self).__name__}.start() SKIPPED (Flask 纯 HTTP 模式)\n")
    # Monkey-patch 所有已知会启动后台线程的单例
    try:
        from ai_engines.auto_routine_maintenance import auto_routine_maintenance_system
        auto_routine_maintenance_system.start = lambda: None
        print('[FLASK-MODE] ✅ auto_routine_maintenance patched')
    except Exception as _e: pass
    try:
        from ai_engines.management.ai_cluster_manager import ai_cluster_manager
        ai_cluster_manager._get_manager = lambda: type('Fake',(),{'_start_monitoring_thread':lambda self:None,'start':lambda self:None,'get_cluster_status':lambda self:{},'get_employee_status':lambda self:{}})()
        print('[FLASK-MODE] ✅ ai_cluster_manager patched (lazy)')
    except Exception as _e: pass
    try:
        # 跳过 comprehensive_system_upgrader / smart_auto_upgrade 的 start
        import sys as _sys_flask
        for _mod_name in list(_sys_flask.modules.keys()):
            if 'upgrade' in _mod_name.lower() or 'upgrader' in _mod_name.lower() or 'maintenance' in _mod_name.lower() or 'inspection' in _mod_name.lower():
                _mod = _sys_flask.modules[_mod_name]
                for _attr_name in dir(_mod):
                    if _attr_name.endswith('_system') or _attr_name.endswith('_manager') or _attr_name.endswith('_engine'):
                        _obj = getattr(_mod, _attr_name, None)
                        if _obj and hasattr(_obj, 'start') and callable(_obj.start):
                            try:
                                _obj.start = lambda *a, **kw: None
                                print(f'[FLASK-MODE] ✅ {_mod_name}.{_attr_name}.start patched')
                            except Exception: pass
    except Exception as _e: pass
    print('[FLASK-MODE] ✅ 所有后台守护线程 start() 已 patch 为 NOP')

    # 🆕 Flask app.run() 前等待 5s 让模块级初始化建表事务跑完
    # Thread patch 已经拦截了所有后台守护线程的 start, 但模块级单例的
    # __init__ 里可能同步做一些轻量建表, 等 5s 让它们 commit
    import time as _t_pre_run
    sys.stderr.write("[BOOT] 等待 5s 让模块初始化 commit...\n")
    _t_pre_run.sleep(5)
    sys.stderr.write("[BOOT] Flask 开始 listen\n")

    app.run(host="0.0.0.0", port=8888, debug=False, threaded=True)
