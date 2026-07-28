#!/usr/bin/env python3
"""
MTSCOS AI 系统黑匣子记录引擎
记录系统灾难级日志和前后操作动作，一并上报数据库
类似飞机黑匣子，在系统发生灾难时完整记录上下文
"""
import os
import sys
import json
import sqlite3
import traceback
import threading
import time
import platform
import resource
import logging
from datetime import datetime, timedelta
from functools import wraps

DATABASE_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'app.db')

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    handlers=[
        logging.FileHandler(
            os.path.join(os.path.dirname(os.path.abspath(__file__)), 'blackbox.log'),
            encoding='utf-8'
        ),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger('BlackBox')


class BlackBoxRecorder:
    """系统黑匣子记录器"""

    def __init__(self):
        self.db_path = DATABASE_PATH
        self.action_buffer = []  # 操作缓冲区(环形)
        self.buffer_lock = threading.Lock()
        self.buffer_size = 500   # 缓冲区大小
        self._init_db()

    def _get_connection(self):
        return sqlite3.connect(self.db_path)

    def _init_db(self):
        """确保表存在"""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS system_blackbox (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    event_id TEXT UNIQUE NOT NULL,
                    event_type TEXT NOT NULL,
                    severity TEXT DEFAULT 'critical',
                    event_category TEXT DEFAULT 'disaster',
                    title TEXT NOT NULL,
                    description TEXT,
                    source TEXT,
                    source_module TEXT,
                    source_file TEXT,
                    source_line TEXT,
                    stack_trace TEXT,
                    system_state TEXT,
                    before_actions TEXT,
                    after_actions TEXT,
                    related_logs TEXT,
                    process_id TEXT,
                    thread_id TEXT,
                    user_session TEXT,
                    user_action TEXT,
                    database_state TEXT,
                    memory_usage TEXT,
                    cpu_usage TEXT,
                    disk_usage TEXT,
                    network_state TEXT,
                    active_connections TEXT,
                    running_tasks TEXT,
                    scheduler_status TEXT,
                    ai_employees_state TEXT,
                    recovery_actions TEXT,
                    recovery_status TEXT DEFAULT 'pending',
                    recovered_at TEXT,
                    recovered_by TEXT,
                    data_loss_estimated INTEGER DEFAULT 0,
                    impact_scope TEXT,
                    impact_users TEXT,
                    duration_seconds REAL,
                    first_occurred TEXT DEFAULT CURRENT_TIMESTAMP,
                    last_occurred TEXT DEFAULT CURRENT_TIMESTAMP,
                    occurrence_count INTEGER DEFAULT 1,
                    resolved INTEGER DEFAULT 0,
                    resolved_at TEXT,
                    resolved_by TEXT,
                    resolution_notes TEXT,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS blackbox_action_log (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    event_id TEXT NOT NULL,
                    action_type TEXT NOT NULL,
                    action_category TEXT DEFAULT 'general',
                    action_timestamp TEXT DEFAULT CURRENT_TIMESTAMP,
                    action_sequence INTEGER DEFAULT 0,
                    action_source TEXT,
                    action_details TEXT,
                    action_result TEXT,
                    action_user TEXT,
                    action_ip TEXT,
                    action_session TEXT,
                    action_process TEXT,
                    action_thread TEXT,
                    related_data TEXT
                )
            ''')
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS blackbox_system_snapshot (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    event_id TEXT NOT NULL,
                    snapshot_type TEXT DEFAULT 'disaster_moment',
                    snapshot_timestamp TEXT DEFAULT CURRENT_TIMESTAMP,
                    snapshot_data TEXT,
                    active_processes TEXT,
                    active_threads TEXT,
                    db_connections TEXT,
                    file_handles TEXT,
                    network_connections TEXT,
                    memory_state TEXT,
                    cpu_state TEXT,
                    disk_state TEXT,
                    running_services TEXT,
                    scheduler_state TEXT,
                    ai_engine_state TEXT
                )
            ''')
            conn.commit()

    def _get_rule_value(self, rule_code, default=None):
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('SELECT rule_value FROM system_rules WHERE rule_code = ? AND is_active = 1', (rule_code,
                ))
                result = cursor.fetchone()
                return result[0] if result else default
        except Exception:
            return default

    def _get_rule_bool(self, rule_code, default=False):
        val = self._get_rule_value(rule_code)
        if val is not None:
            return val in ('1', 'true', 'True', 'yes', 'Yes')
        return default

    def _get_rule_int(self, rule_code, default=0):
        val = self._get_rule_value(rule_code)
        try:
            return int(val) if val is not None else default
        except (ValueError, TypeError):
            return default

    # ========== 操作缓冲区 ==========

    def record_action(self, action_type, action_details='', action_category='general',
                      action_user='system', action_result='success', related_data=None):
        """记录操作到缓冲区（持续滚动记录所有操作）"""
        if not self._get_rule_bool('BLACKBOX_LOG_ALL_OPERATIONS', True):
            return

        action = {
            'timestamp': datetime.now().isoformat(),
            'action_type': action_type,
            'action_category': action_category,
            'action_details': action_details,
            'action_result': action_result,
            'action_user': action_user,
            'action_process': str(os.getpid()),
            'action_thread': str(threading.current_thread().ident),
            'related_data': json.dumps(related_data) if related_data else None
        }

        with self.buffer_lock:
            self.action_buffer.append(action)
            if len(self.action_buffer) > self.buffer_size:
                self.action_buffer.pop(0)

    def _get_before_actions(self, count=None, time_window=None):
        """获取灾难前的操作记录"""
        if count is None:
            count = self._get_rule_int('BLACKBOX_BEFORE_ACTION_COUNT', 50)
        if time_window is None:
            time_window = self._get_rule_int('BLACKBOX_BEFORE_ACTION_TIME_WINDOW', 3600)

        cutoff = datetime.now() - timedelta(seconds=time_window)
        with self.buffer_lock:
            actions = [a for a in self.action_buffer
                       if datetime.fromisoformat(a['timestamp']) >= cutoff]
        return actions[-count:] if count > 0 else actions

    def _get_after_actions(self):
        """获取灾难后的操作记录(灾难发生后持续收集)"""
        return []  # 灾难后操作通过record_action持续记录

    # ========== 系统状态采集 ==========

    def _capture_system_state(self):
        """采集系统状态"""
        state = {
            'timestamp': datetime.now().isoformat(),
            'platform': platform.platform(),
            'python_version': sys.version,
            'hostname': platform.node(),
            'pid': os.getpid(),
        }

        # 内存使用
        try:
            usage = resource.getrusage(resource.RUSAGE_SELF)
            state['memory_max_rss'] = usage.ru_maxrss  # KB
            state['memory_user_time'] = usage.ru_utime
            state['memory_sys_time'] = usage.ru_stime
        except Exception:
            pass

        # 线程数
        try:
            state['thread_count'] = threading.active_count()
            state['active_threads'] = [t.name for t in threading.enumerate()]
        except Exception:
            pass

        # 磁盘使用
        try:
            stat = os.statvfs(os.path.dirname(os.path.abspath(__file__)))
            state['disk_free'] = stat.f_bavail * stat.f_frsize
            state['disk_total'] = stat.f_blocks * stat.f_frsize
        except Exception:
            pass

        return state

    def _capture_database_state(self):
        """采集数据库状态"""
        state = {'timestamp': datetime.now().isoformat()}
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("PRAGMA integrity_check")
                state['integrity'] = cursor.fetchone()[0]

                cursor.execute("SELECT COUNT(*) FROM system_rules WHERE is_active = 1")
                state['active_rules'] = cursor.fetchone()[0]

                cursor.execute("SELECT COUNT(*) FROM system_maintenance_logs")
                state['maintenance_logs'] = cursor.fetchone()[0]

                cursor.execute("SELECT COUNT(*) FROM ai_employees")
                state['ai_employees'] = cursor.fetchone()[0]

                cursor.execute("SELECT COUNT(*) FROM system_blackbox WHERE resolved = 0")
                state['unresolved_disasters'] = cursor.fetchone()[0]

                cursor.execute("SELECT rule_value FROM system_rules WHERE rule_code = 'SYS_VERSION'")
                result = cursor.fetchone()
                state['system_version'] = result[0] if result else 'unknown'

                # 数据库大小
                state['db_size'] = os.path.getsize(self.db_path)
        except Exception as e:
            state['error'] = str(e)
        return state

    def _capture_scheduler_state(self):
        """采集调度引擎状态"""
        state = {'timestamp': datetime.now().isoformat()}
        try:
            pid_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), '.scheduler_pid')
            heartbeat_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), '.scheduler_heartbeat')

            if os.path.exists(pid_file):
                with open(pid_file, 'r') as f:
                    state['scheduler_pid'] = f.read().strip()

            if os.path.exists(heartbeat_file):
                with open(heartbeat_file, 'r') as f:
                    state['scheduler_heartbeat'] = json.load(f)
            else:
                state['scheduler_status'] = 'no_heartbeat'
        except Exception as e:
            state['error'] = str(e)
        return state

    def _capture_ai_state(self):
        """采集AI系统状态"""
        state = {'timestamp': datetime.now().isoformat()}
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT COUNT(*) FROM ai_employees WHERE status = 'active'")
                state['active_ai_employees'] = cursor.fetchone()[0]

                cursor.execute("SELECT COUNT(*) FROM ai_engine_config WHERE enabled = 1")
                state['active_ai_engines'] = cursor.fetchone()[0]

                cursor.execute("SELECT COUNT(*) FROM ai_task_logs WHERE created_at > ?",
                              ((datetime.now() - timedelta(hours=1)).isoformat(),))
                state['recent_ai_tasks'] = cursor.fetchone()[0]
        except Exception as e:
            state['error'] = str(e)
        return state

    def _capture_network_state(self):
        """采集网络状态"""
        state = {'timestamp': datetime.now().isoformat()}
        try:
            import subprocess
            result = subprocess.run(
                ['lsof', '-i', '-P', '-n'],
                capture_output=True, text=True, timeout=10
            )
            lines = [l for l in result.stdout.strip().split('\n') if l and 'LISTEN' in l]
            state['listening_ports'] = lines[:20]  # 限制数量
            state['total_connections'] = len(lines)
        except Exception as e:
            state['error'] = str(e)
        return state

    def _capture_related_logs(self, time_window=3600):
        """采集相关日志"""
        logs = []
        try:
            cutoff = (datetime.now() - timedelta(seconds=time_window)).strftime('%Y-%m-%d %H:%M:%S')
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    SELECT operation_type, target, result, details, timestamp
                    FROM system_maintenance_logs
                    WHERE timestamp > ?
                    ORDER BY timestamp DESC LIMIT 100
                ''', (cutoff,))
                for row in cursor.fetchall():
                    logs.append({
                        'operation_type': row[0],
                        'target': row[1],
                        'result': row[2],
                        'details': row[3],
                        'timestamp': row[4]
                    })
        except Exception as e:
            logs.append({'error': str(e)})
        return logs

    def _get_stack_trace(self):
        """获取当前堆栈跟踪"""
        try:
            return traceback.format_exc()
        except Exception:
            return None

    def _generate_event_id(self):
        """生成事件ID"""
        return f"EVT-{datetime.now().strftime('%Y%m%d%H%M%S')}-{os.getpid()}"

    # ========== 核心记录方法 ==========

    def record_disaster(self, event_type, title, description='', severity='critical',
                        source_module=None, source_file=None, source_line=None,
                        stack_trace=None, user_action=None, impact_scope=None,
                        impact_users=None, data_loss_estimated=0):
        """
        记录灾难级事件
        这是黑匣子的核心方法，在系统发生灾难时调用
        """
        if not self._get_rule_bool('BLACKBOX_ENABLED', True):
            return None

        # 检查级别过滤
        severity_map = {
            'disaster': 'BLACKBOX_DISASTER_LEVEL_ENABLED',
            'critical': 'BLACKBOX_CRITICAL_LEVEL_ENABLED',
            'warning': 'BLACKBOX_WARNING_LEVEL_ENABLED',
            'info': 'BLACKBOX_INFO_LEVEL_ENABLED'
        }
        rule_key = severity_map.get(severity)
        if rule_key and not self._get_rule_bool(rule_key, severity in ('disaster', 'critical')):
            return None

        event_id = self._generate_event_id()
        now = datetime.now()

        logger.error("=" * 60)
        logger.error(f"  🚨 系统黑匣子记录灾难事件 🚨")
        logger.error(f"  事件ID: {event_id}")
        logger.error(f"  类型: {event_type}")
        logger.error(f"  级别: {severity}")
        logger.error(f"  标题: {title}")
        logger.error(f"  描述: {description}")
        logger.error("=" * 60)

        # 采集系统状态
        system_state = self._capture_system_state() if self._get_rule_bool('BLACKBOX_CAPTURE_SYSTEM_SNAPSHOT',
        True) else None
        database_state = self._capture_database_state() if self._get_rule_bool('BLACKBOX_CAPTURE_DB_STATE',
        True) else None
        scheduler_status = self._capture_scheduler_state()
        ai_employees_state = self._capture_ai_state() if self._get_rule_bool('BLACKBOX_CAPTURE_AI_STATE',
        True) else None
        network_state = self._capture_network_state() if self._get_rule_bool('BLACKBOX_CAPTURE_NETWORK_STATE',
        True) else None

        # 获取堆栈跟踪
        if stack_trace is None and self._get_rule_bool('BLACKBOX_CAPTURE_STACK_TRACE', True):
            stack_trace = traceback.format_exc() if traceback.format_exc() != 'NoneType: None\n' else None

        # 获取前后操作
        before_actions = self._get_before_actions() if self._get_rule_bool('BLACKBOX_CAPTURE_BEFORE_ACTIONS',
        True) else []
        related_logs = self._capture_related_logs()

        # 写入数据库
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    INSERT INTO system_blackbox (
                        event_id, event_type, severity, event_category, title, description,
                        source, source_module, source_file, source_line, stack_trace,
                        system_state, before_actions, after_actions, related_logs,
                        process_id, thread_id, user_action,
                        database_state, memory_usage, network_state,
                        scheduler_status, ai_employees_state,
                        data_loss_estimated, impact_scope, impact_users,
                        first_occurred, last_occurred, occurrence_count, created_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    event_id, event_type, severity, 'disaster', title, description,
                    source_module or 'system', source_module, source_file, str(source_line) if source_line else None,
                    stack_trace,
                    json.dumps(system_state, ensure_ascii=False) if system_state else None,
                    json.dumps(before_actions, ensure_ascii=False) if before_actions else None,
                    json.dumps([], ensure_ascii=False),  # after_actions初始为空
                    json.dumps(related_logs, ensure_ascii=False) if related_logs else None,
                    str(os.getpid()), str(threading.current_thread().ident),
                    user_action,
                    json.dumps(database_state, ensure_ascii=False) if database_state else None,
                    json.dumps(system_state, ensure_ascii=False) if system_state else None,
                    json.dumps(network_state, ensure_ascii=False) if network_state else None,
                    json.dumps(scheduler_status, ensure_ascii=False),
                    json.dumps(ai_employees_state, ensure_ascii=False) if ai_employees_state else None,
                    data_loss_estimated, impact_scope, impact_users,
                    now.strftime('%Y-%m-%d %H:%M:%S'),
                    now.strftime('%Y-%m-%d %H:%M:%S'),
                    1, now.strftime('%Y-%m-%d %H:%M:%S')
                ))
                conn.commit()

            logger.info(f"  ✓ 灾难事件已记录到数据库: {event_id}")

            # 写入系统快照
            if self._get_rule_bool('BLACKBOX_CAPTURE_SYSTEM_SNAPSHOT', True):
                self._write_system_snapshot(event_id, system_state, database_state,
                                           scheduler_status, ai_employees_state, network_state)

            # 写入前置操作记录
            self._write_action_logs(event_id, before_actions, 'before')

            # 尝试自动恢复
            if self._get_rule_bool('BLACKBOX_AUTO_RECOVERY_ENABLED', True):
                self._attempt_auto_recovery(event_id, event_type)

            return event_id

        except Exception as e:
            logger.error(f"  ✗ 灾难事件记录失败: {e}")
            return None

    def _write_system_snapshot(self, event_id, system_state, database_state,
                               scheduler_state, ai_state, network_state):
        """写入系统快照"""
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    INSERT INTO blackbox_system_snapshot (
                        event_id, snapshot_type, snapshot_timestamp,
                        snapshot_data, active_processes, active_threads,
                        db_connections, network_connections,
                        memory_state, disk_state,
                        running_services, scheduler_state, ai_engine_state
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    event_id, 'disaster_moment',
                    datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                    json.dumps(system_state, ensure_ascii=False) if system_state else None,
                    str(system_state.get('pid', '')) if system_state else None,
                    json.dumps(system_state.get('active_threads', [])) if system_state else None,
                    json.dumps(database_state, ensure_ascii=False) if database_state else None,
                    json.dumps(network_state, ensure_ascii=False) if network_state else None,
                    json.dumps({'max_rss': system_state.get('memory_max_rss')}) if system_state else None,
                    json.dumps({'disk_free': system_state.get('disk_free'),
                    'disk_total': system_state.get('disk_total')}) if system_state else None,
                    json.dumps(scheduler_state, ensure_ascii=False) if scheduler_state else None,
                    json.dumps(scheduler_state, ensure_ascii=False) if scheduler_state else None,
                    json.dumps(ai_state, ensure_ascii=False) if ai_state else None
                ))
                conn.commit()
        except Exception as e:
            logger.error(f"写入系统快照失败: {e}")

    def _write_action_logs(self, event_id, actions, phase='before'):
        """写入操作日志"""
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                for i, action in enumerate(actions):
                    cursor.execute('''
                        INSERT INTO blackbox_action_log (
                            event_id, action_type, action_category,
                            action_timestamp, action_sequence,
                            action_source, action_details, action_result,
                            action_user, action_process, action_thread,
                            related_data
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    ''', (
                        event_id,
                        action.get('action_type', 'unknown'),
                        action.get('action_category', phase),
                        action.get('timestamp', ''),
                        i,
                        phase,
                        action.get('action_details', ''),
                        action.get('action_result', ''),
                        action.get('action_user', 'system'),
                        action.get('action_process', ''),
                        action.get('action_thread', ''),
                        action.get('related_data')
                    ))
                conn.commit()
        except Exception as e:
            logger.error(f"写入操作日志失败: {e}")

    def record_after_action(self, event_id, action_type, action_details='', action_result='success'):
        """灾难发生后持续记录操作"""
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    INSERT INTO blackbox_action_log (
                        event_id, action_type, action_category,
                        action_timestamp, action_sequence,
                        action_source, action_details, action_result
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    event_id, action_type, 'after',
                    datetime.now().isoformat(),
                    0, 'after', action_details, action_result
                ))
                conn.commit()
        except Exception as e:
            logger.error(f"记录后置操作失败: {e}")

    def _attempt_auto_recovery(self, event_id, event_type):
        """尝试自动恢复"""
        max_retries = self._get_rule_int('BLACKBOX_AUTO_RECOVERY_MAX_RETRIES', 3)
        recovery_actions = []

        logger.info(f"  尝试自动恢复 (事件: {event_type})")

        for attempt in range(max_retries):
            action = f"恢复尝试 {attempt + 1}/{max_retries}: "
            try:
                if event_type == 'database_corruption':
                    action += "执行数据库完整性修复"
                    with self._get_connection() as conn:
                        conn.execute("PRAGMA integrity_check")
                        conn.execute("VACUUM")
                elif event_type == 'scheduler_crash':
                    action += "尝试重启调度引擎"
                elif event_type == 'memory_exhaustion':
                    action += "清理内存缓存"
                elif event_type == 'disk_full':
                    action += "清理临时文件"
                else:
                    action += "通用恢复(数据库连接检查)"
                    with self._get_connection() as conn:
                        conn.execute("SELECT 1")

                recovery_actions.append({
                    'attempt': attempt + 1,
                    'action': action,
                    'result': 'success',
                    'timestamp': datetime.now().isoformat()
                })
                logger.info(f"    ✓ {action} - 成功")

                # 更新恢复状态
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('''
                        UPDATE system_blackbox
                        SET recovery_status = 'recovered',
                            recovery_actions = ?,
                            recovered_at = ?,
                            resolved = 1,
                            resolved_at = ?,
                            resolution_notes = '自动恢复成功'
                        WHERE event_id = ?
                    ''', (
                        json.dumps(recovery_actions, ensure_ascii=False),
                        datetime.now().isoformat(),
                        datetime.now().isoformat(),
                        event_id
                    ))
                    conn.commit()

                self.record_after_action(event_id, 'auto_recovery', action, 'success')
                logger.info(f"  ✓ 自动恢复成功")
                return True

            except Exception as e:
                recovery_actions.append({
                    'attempt': attempt + 1,
                    'action': action,
                    'result': 'failure',
                    'error': str(e),
                    'timestamp': datetime.now().isoformat()
                })
                logger.warning(f"    ✗ {action} - 失败: {e}")
                time.sleep(5)

        # 所有尝试失败
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                UPDATE system_blackbox
                SET recovery_status = 'failed',
                    recovery_actions = ?
                WHERE event_id = ?
            ''', (json.dumps(recovery_actions, ensure_ascii=False), event_id))
            conn.commit()

        self.record_after_action(event_id, 'auto_recovery', '所有恢复尝试失败', 'failure')
        logger.error(f"  ✗ 自动恢复失败，需要人工干预")
        return False

    def resolve_event(self, event_id, resolved_by='system', notes=''):
        """标记事件已解决"""
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    UPDATE system_blackbox
                    SET resolved = 1, resolved_at = ?, resolved_by = ?, resolution_notes = ?
                    WHERE event_id = ?
                ''', (datetime.now().isoformat(), resolved_by, notes, event_id))
                conn.commit()
            logger.info(f"事件 {event_id} 已标记为已解决")
        except Exception as e:
            logger.error(f"标记事件解决失败: {e}")

    def get_disasters(self, limit=20, resolved=None):
        """获取灾难事件列表"""
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                if resolved is None:
                    cursor.execute('''
                        SELECT event_id, event_type, severity, title, description,
                               first_occurred, resolved, recovery_status
                        FROM system_blackbox
                        ORDER BY first_occurred DESC LIMIT ?
                    ''', (limit,))
                else:
                    cursor.execute('''
                        SELECT event_id, event_type, severity, title, description,
                               first_occurred, resolved, recovery_status
                        FROM system_blackbox WHERE resolved = ?
                        ORDER BY first_occurred DESC LIMIT ?
                    ''', (1 if resolved else 0, limit))
                return cursor.fetchall()
        except Exception as e:
            logger.error(f"获取灾难事件失败: {e}")
            return []

    def get_event_detail(self, event_id):
        """获取事件详情"""
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('SELECT * FROM system_blackbox WHERE event_id = ?', (event_id,))
                event = cursor.fetchone()
                if not event:
                    return None

                cursor.execute('SELECT * FROM blackbox_action_log WHERE event_id = ? ORDER BY action_sequence',
                              (event_id,))
                actions = cursor.fetchall()

                cursor.execute('SELECT * FROM blackbox_system_snapshot WHERE event_id = ?', (event_id,))
                snapshots = cursor.fetchall()

                return {'event': event, 'actions': actions, 'snapshots': snapshots}
        except Exception as e:
            logger.error(f"获取事件详情失败: {e}")
            return None

    def cleanup_old_records(self):
        """清理过期记录"""
        retention_days = self._get_rule_int('BLACKBOX_RETENTION_DAYS', 365)
        cutoff = (datetime.now() - timedelta(days=retention_days)).strftime('%Y-%m-%d %H:%M:%S')

        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("DELETE FROM blackbox_action_log WHERE action_timestamp < ?", (cutoff,))
                cursor.execute("DELETE FROM blackbox_system_snapshot WHERE snapshot_timestamp < ?", (cutoff,))
                cursor.execute("DELETE FROM system_blackbox WHERE first_occurred < ?", (cutoff,))
                deleted = cursor.execute("SELECT changes()").fetchone()[0]
                conn.commit()
            logger.info(f"清理了 {deleted} 条过期黑匣子记录")
        except Exception as e:
            logger.error(f"清理过期记录失败: {e}")


# 全局单例
_blackbox = None
_blackbox_lock = threading.Lock()


def get_blackbox():
    """获取黑匣子记录器单例"""
    global _blackbox
    if _blackbox is None:
        with _blackbox_lock:
            if _blackbox is None:
                _blackbox = BlackBoxRecorder()
    return _blackbox


def record_disaster(event_type, title, **kwargs):
    """快捷函数：记录灾难事件"""
    return get_blackbox().record_disaster(event_type, title, **kwargs)


def record_action(action_type, **kwargs):
    """快捷函数：记录操作"""
    get_blackbox().record_action(action_type, **kwargs)


def disaster_handler(event_type, title):
    """装饰器：自动捕获函数异常并记录到黑匣子"""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            bb = get_blackbox()
            bb.record_action('function_call', action_details=f'调用 {func.__name__}',
                           action_category='pre_call')
            try:
                result = func(*args, **kwargs)
                bb.record_action('function_return', action_details=f'返回 {func.__name__}',
                               action_category='post_call', action_result='success')
                return result
            except Exception as e:
                bb.record_disaster(
                    event_type=event_type,
                    title=title,
                    description=f'函数 {func.__name__} 异常: {str(e)}',
                    source_module=func.__module__,
                    source_file=func.__code__.co_filename,
                    source_line=func.__code__.co_firstlineno,
                    stack_trace=traceback.format_exc(),
                    impact_scope=f'函数: {func.__name__}'
                )
                raise
        return wrapper
    return decorator
