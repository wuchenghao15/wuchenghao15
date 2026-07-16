#!/usr/bin/env python3
"""
MTSCOS AI 自动化调度引擎
根据system_rules表中的规则配置，后台自动执行维护、检查、清理、同步等任务
"""
import os
import sys
import sqlite3
import json
import time
import signal
import threading
import logging
import subprocess
import traceback
from datetime import datetime, timedelta

DATABASE_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'app.db')
HEARTBEAT_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), '.scheduler_heartbeat')
PID_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), '.scheduler_pid')

# 导入黑匣子记录器
try:
    from blackbox_recorder import get_blackbox, record_disaster, record_action
    BLACKBOX_AVAILABLE = True
except ImportError:
    BLACKBOX_AVAILABLE = False
    def record_disaster(*args, **kwargs): pass
    def record_action(*args, **kwargs): pass

# 日志配置
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    handlers=[
        logging.FileHandler(
            os.path.join(os.path.dirname(os.path.abspath(__file__)), 'auto_scheduler.log'),
            encoding='utf-8'
        ),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger('AutoScheduler')


class AutoScheduler:
    """自动化调度引擎"""

    def __init__(self):
        self.db_path = DATABASE_PATH
        self.running = False
        self.scheduler_thread = None
        self.last_run = {}  # 记录每个任务最后执行时间
        self.task_stats = {}  # 任务执行统计
        self.termination_requested = False  # 人工终止标志
        self._init_stats()
        self._setup_signal_handlers()

    def _get_connection(self):
        return sqlite3.connect(self.db_path)

    def _init_stats(self):
        """初始化任务统计"""
        self.task_stats = {
            'total_runs': 0,
            'success_count': 0,
            'failure_count': 0,
            'start_time': None,
            'last_task': None,
            'last_task_time': None
        }

    # ========== 进程保护 ==========

    def _setup_signal_handlers(self):
        """注册信号处理器，拦截终止信号"""
        def handle_sigterm(signum, frame):
            """拦截SIGTERM信号"""
            logger.warning("=" * 60)
            logger.warning("  ⚠ 收到SIGTERM终止信号!")
            logger.warning("  ⚠ 调度引擎进程保护已激活")
            logger.warning("=" * 60)
            self._log_operation('signal_received', 'SIGTERM',
                              'warning', f'收到SIGTERM信号(PID:{os.getpid()})')

            if self._get_rule_bool('AUTO_SCHEDULER_PREVENT_ACCIDENTAL_KILL', True):
                logger.warning("  ⚠ 进程保护已启用，忽略意外终止信号")
                logger.warning("  ⚠ 如需人工终止，请使用: python3 scheduler_control.py stop")
                self._write_heartbeat()  # 更新心跳表示进程仍然存活
                return
            else:
                logger.info("  进程保护未启用，正在停止...")
                self.running = False

        def handle_sigint(signum, frame):
            """拦截SIGINT(Ctrl+C)信号"""
            logger.warning("=" * 60)
            logger.warning("  ⚠ 收到Ctrl+C中断信号!")
            logger.warning("  ⚠ 调度引擎进程保护已激活")
            logger.warning("=" * 60)
            self._log_operation('signal_received', 'SIGINT',
                              'warning', f'收到SIGINT信号(PID:{os.getpid()})')

            if self._get_rule_bool('AUTO_SCHEDULER_PREVENT_ACCIDENTAL_KILL', True):
                logger.warning("  ⚠ 进程保护已启用，忽略Ctrl+C中断")
                logger.warning("  ⚠ 如需人工终止，请使用: python3 scheduler_control.py stop")
                self._write_heartbeat()
                return
            else:
                logger.info("  进程保护未启用，正在停止...")
                self.running = False

        signal.signal(signal.SIGTERM, handle_sigterm)
        signal.signal(signal.SIGINT, handle_sigint)
        logger.info("信号处理器已注册 (SIGTERM/SIGINT拦截)")

    def _write_heartbeat(self):
        """写入心跳文件"""
        try:
            heartbeat_data = {
                'pid': os.getpid(),
                'timestamp': datetime.now().isoformat(),
                'running': self.running,
                'total_runs': self.task_stats.get('total_runs', 0)
            }
            with open(HEARTBEAT_FILE, 'w') as f:
                json.dump(heartbeat_data, f)
        except Exception as e:
            logger.warning(f"写入心跳文件失败: {e}")

    def _write_pid_file(self):
        """写入PID文件"""
        try:
            with open(PID_FILE, 'w') as f:
                f.write(str(os.getpid()))
        except Exception as e:
            logger.warning(f"写入PID文件失败: {e}")

    def _remove_pid_file(self):
        """删除PID文件"""
        try:
            if os.path.exists(PID_FILE):
                os.remove(PID_FILE)
        except Exception:
            pass

    def _log_operation(self, operation_type, target, result, details=''):
        """记录操作日志到数据库"""
        if not self._get_rule_bool('AUTO_SCHEDULER_LOG_ALL_OPERATIONS', True):
            return
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    INSERT INTO system_maintenance_logs
                    (operation_type, target, result, details, timestamp)
                    VALUES (?, ?, ?, ?, ?)
                ''', (operation_type, target, result, details,
                      datetime.now().strftime('%Y-%m-%d %H:%M:%S')))
                conn.commit()
        except Exception as e:
            logger.error(f"记录操作日志失败: {e}")
        # 同步记录到黑匣子操作缓冲区
        record_action(operation_type, action_details=details, action_result=result,
                     action_category='scheduler')

    def _report_disaster(self, event_type, title, description='', **kwargs):
        """向黑匣子报告灾难事件"""
        try:
            event_id = record_disaster(
                event_type=event_type,
                title=title,
                description=description,
                source_module='auto_scheduler',
                stack_trace=traceback.format_exc(),
                **kwargs
            )
            if event_id:
                logger.error(f"灾难事件已上报黑匣子: {event_id} - {title}")
            return event_id
        except Exception as e:
            logger.error(f"上报黑匣子失败: {e}")
            return None

    def _get_rule_value(self, rule_code, default=None):
        """从system_rules读取规则值"""
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    'SELECT rule_value FROM system_rules WHERE rule_code = ? AND is_active = 1',
                    (rule_code,)
                )
                result = cursor.fetchone()
                if result:
                    return result[0]
        except Exception as e:
            logger.warning(f"读取规则 {rule_code} 失败: {e}")
        return default

    def _get_rule_int(self, rule_code, default=0):
        """读取整数型规则值"""
        val = self._get_rule_value(rule_code)
        try:
            return int(val) if val is not None else default
        except (ValueError, TypeError):
            return default

    def _get_rule_bool(self, rule_code, default=False):
        """读取布尔型规则值"""
        val = self._get_rule_value(rule_code)
        if val is not None:
            return val in ('1', 'true', 'True', 'yes', 'Yes')
        return default

    def _should_run(self, task_name, interval_key, default_interval):
        """判断任务是否应该执行"""
        interval = self._get_rule_int(interval_key, default_interval)
        if interval <= 0:
            return False

        last = self.last_run.get(task_name)
        if last is None:
            return True

        elapsed = (datetime.now() - last).total_seconds()
        return elapsed >= interval

    def _log_maintenance(self, operation_type, target, result, details=''):
        """记录维护日志到数据库"""
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    INSERT INTO system_maintenance_logs
                    (operation_type, target, result, details, timestamp)
                    VALUES (?, ?, ?, ?, ?)
                ''', (operation_type, target, result, details,
                      datetime.now().strftime('%Y-%m-%d %H:%M:%S')))
                conn.commit()
        except Exception as e:
            logger.error(f"记录维护日志失败: {e}")

    def _update_stats(self, task_name, success):
        """更新任务统计"""
        self.task_stats['total_runs'] += 1
        if success:
            self.task_stats['success_count'] += 1
        else:
            self.task_stats['failure_count'] += 1
        self.task_stats['last_task'] = task_name
        self.task_stats['last_task_time'] = datetime.now().isoformat()

    # ========== 维护任务 ==========

    def task_database_health_check(self):
        """数据库健康检查"""
        task = 'db_health_check'
        if not self._should_run(task, 'MAINT_ENGINE_HEALTH_CHECK', 60):
            return

        logger.info("[任务] 数据库健康检查...")
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("PRAGMA integrity_check")
                result = cursor.fetchone()[0]

                cursor.execute("SELECT COUNT(*) FROM system_rules WHERE is_active = 1")
                active_rules = cursor.fetchone()[0]

                cursor.execute("SELECT COUNT(*) FROM system_version_history")
                version_count = cursor.fetchone()[0]

            if result == 'ok':
                logger.info(f"  ✓ 数据库完整性正常 | 规则:{active_rules} | 版本记录:{version_count}")
                self._log_maintenance('health_check', 'database', 'success',
                                      f'完整性检查通过, 活跃规则:{active_rules}, 版本记录:{version_count}')
                self._update_stats(task, True)
            else:
                logger.error(f"  ✗ 数据库完整性异常: {result}")
                self._log_maintenance('health_check', 'database', 'failure', f'完整性检查失败: {result}')
                self._update_stats(task, False)
        except Exception as e:
            logger.error(f"  ✗ 数据库健康检查失败: {e}")
            self._update_stats(task, False)

        self.last_run[task] = datetime.now()

    def task_rule_status_sync(self):
        """规则状态同步"""
        task = 'rule_status_sync'
        if not self._should_run(task, 'PERM_CHECK_INTERVAL', 3600):
            return

        logger.info("[任务] 规则状态同步...")
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("UPDATE system_rules SET is_active = 1 WHERE is_active IS NULL")
                updated = cursor.execute("SELECT changes()").fetchone()[0]
                conn.commit()

            logger.info(f"  ✓ 同步了 {updated} 条规则状态")
            self._log_maintenance('sync', 'system_rules', 'success', f'更新{updated}条规则状态')
            self._update_stats(task, True)
        except Exception as e:
            logger.error(f"  ✗ 规则状态同步失败: {e}")
            self._update_stats(task, False)

        self.last_run[task] = datetime.now()

    def task_log_cleanup(self):
        """系统日志清理"""
        task = 'log_cleanup'
        if not self._should_run(task, 'MAINT_LOG_CLEANUP', 604800):
            return

        logger.info("[任务] 系统日志清理...")
        try:
            cutoff = (datetime.now() - timedelta(days=90)).strftime('%Y-%m-%d %H:%M:%S')
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("DELETE FROM system_maintenance_logs WHERE timestamp < ?", (cutoff,))
                deleted = cursor.execute("SELECT changes()").fetchone()[0]
                conn.commit()

            logger.info(f"  ✓ 清理了 {deleted} 条过期维护日志")
            self._log_maintenance('cleanup', 'maintenance_logs', 'success', f'清理{deleted}条日志')
            self._update_stats(task, True)
        except Exception as e:
            logger.error(f"  ✗ 日志清理失败: {e}")
            self._update_stats(task, False)

        self.last_run[task] = datetime.now()

    def task_version_check(self):
        """版本号检查"""
        task = 'version_check'
        if not self._should_run(task, 'MAINT_VERSION_CHECK_INTERVAL', 3600):
            return

        logger.info("[任务] 版本号检查...")
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT rule_value FROM system_rules WHERE rule_code = 'SYS_VERSION'")
                current = cursor.fetchone()
                current_version = current[0] if current else 'unknown'

                cursor.execute("SELECT version FROM system_version_history ORDER BY major DESC, minor DESC, patch DESC LIMIT 1")
                latest = cursor.fetchone()
                latest_version = latest[0] if latest else 'unknown'

            if current_version != latest_version and latest_version != 'unknown':
                logger.info(f"  ⚠ 当前版本{current_version}与最新版本{latest_version}不一致，自动同步")
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute("UPDATE system_rules SET rule_value = ?, updated_at = ? WHERE rule_code = 'SYS_VERSION'",
                                  (latest_version, datetime.now().isoformat()))
                    conn.commit()
                self._log_maintenance('sync', 'version', 'success', f'版本同步: {current_version} -> {latest_version}')
            else:
                logger.info(f"  ✓ 版本号一致: {current_version}")

            self._update_stats(task, True)
        except Exception as e:
            logger.error(f"  ✗ 版本号检查失败: {e}")
            self._update_stats(task, False)

        self.last_run[task] = datetime.now()

    def task_ai_employee_status_check(self):
        """AI员工状态检查"""
        task = 'ai_employee_check'
        if not self._should_run(task, 'MAINT_EMPLOYEE_STATUS_CHECK', 1800):
            return

        logger.info("[任务] AI员工状态检查...")
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()

                cursor.execute("SELECT COUNT(*) FROM ai_employees")
                total = cursor.fetchone()[0]

                cursor.execute("SELECT COUNT(*) FROM ai_employees WHERE status = 'active'")
                active = cursor.fetchone()[0]

                cursor.execute("SELECT COUNT(*) FROM ai_employees WHERE status != 'active'")
                inactive = cursor.fetchone()[0]

            logger.info(f"  ✓ AI员工: 总{total} / 活跃{active} / 非活跃{inactive}")
            self._log_maintenance('health_check', 'ai_employees', 'success',
                                  f'总数:{total}, 活跃:{active}, 非活跃:{inactive}')
            self._update_stats(task, True)
        except Exception as e:
            logger.warning(f"  ⚠ AI员工状态检查失败: {e}")
            self._update_stats(task, False)

        self.last_run[task] = datetime.now()

    def task_git_sync_check(self):
        """Git同步状态检查"""
        task = 'git_sync_check'
        if not self._should_run(task, 'MAINT_GIT_SYNC_INTERVAL', 1800):
            return

        logger.info("[任务] Git同步状态检查...")
        try:
            project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            git_dir = os.path.join(project_root, '.git')

            if os.path.exists(git_dir):
                import subprocess
                result = subprocess.run(
                    ['git', 'status', '--porcelain'],
                    capture_output=True, text=True, cwd=project_root, timeout=10
                )
                changed = len([l for l in result.stdout.strip().split('\n') if l]) if result.stdout.strip() else 0

                logger.info(f"  ✓ Git状态正常, 未提交变更: {changed}个文件")
                self._log_maintenance('sync', 'git', 'success', f'未提交变更:{changed}个文件')
            else:
                logger.info("  ⚠ 非Git仓库，跳过Git同步检查")

            self._update_stats(task, True)
        except Exception as e:
            logger.warning(f"  ⚠ Git同步检查失败: {e}")
            self._update_stats(task, False)

        self.last_run[task] = datetime.now()

    def task_permission_sync(self):
        """权限自动同步"""
        task = 'permission_sync'
        if not self._should_run(task, 'PERM_CHECK_INTERVAL', 3600):
            return

        if not self._get_rule_bool('PERM_AUTO_SYNC_ENABLED', True):
            return

        logger.info("[任务] 权限自动同步...")
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT COUNT(*) FROM users WHERE is_active = 1")
                active_users = cursor.fetchone()[0]

            logger.info(f"  ✓ 权限同步完成, 活跃用户: {active_users}")
            self._log_maintenance('sync', 'permissions', 'success', f'活跃用户:{active_users}')
            self._update_stats(task, True)
        except Exception as e:
            logger.warning(f"  ⚠ 权限同步失败: {e}")
            self._update_stats(task, False)

        self.last_run[task] = datetime.now()

    def task_sandbox_health_check(self):
        """沙盒健康检查"""
        task = 'sandbox_health'
        if not self._should_run(task, 'SANDBOX_HEALTH_CHECK_INTERVAL', 60):
            return

        logger.info("[任务] 沙盒健康检查...")
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT COUNT(*) FROM sandbox_instances WHERE status = 'running'")
                running = cursor.fetchone()[0]

                cursor.execute("SELECT COUNT(*) FROM sandbox_instances")
                total = cursor.fetchone()[0]

            logger.info(f"  ✓ 沙盒: 运行中{running} / 总{total}")
            self._log_maintenance('health_check', 'sandbox', 'success', f'运行:{running}, 总:{total}')
            self._update_stats(task, True)
        except Exception as e:
            logger.warning(f"  ⚠ 沙盒健康检查失败: {e}")
            self._update_stats(task, False)

        self.last_run[task] = datetime.now()

    def task_document_cleanup(self):
        """文档自动清理"""
        task = 'document_cleanup'
        if not self._should_run(task, 'DOCUMENT_CLEANUP_INTERVAL', 86400):
            return

        if not self._get_rule_bool('DOCUMENT_AUTO_CLEANUP_ENABLED', True):
            return

        logger.info("[任务] 文档自动清理...")
        try:
            retention_days = self._get_rule_int('DOCUMENT_RETENTION_DAYS', 90)
            cutoff = (datetime.now() - timedelta(days=retention_days)).strftime('%Y-%m-%d')

            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("UPDATE document_rules SET status = 'archived' WHERE expiry_date < ? AND status = 'published'", (cutoff,))
                archived = cursor.execute("SELECT changes()").fetchone()[0]
                conn.commit()

            logger.info(f"  ✓ 归档了 {archived} 个过期文档")
            self._log_maintenance('cleanup', 'documents', 'success', f'归档{archived}个文档')
            self._update_stats(task, True)
        except Exception as e:
            logger.warning(f"  ⚠ 文档清理失败: {e}")
            self._update_stats(task, False)

        self.last_run[task] = datetime.now()

    def task_autofix_monitor(self):
        """自动修复监控"""
        task = 'autofix_monitor'
        if not self._should_run(task, 'AUTOFIX_MONITORING_INTERVAL', 60):
            return

        if not self._get_rule_bool('AUTOFIX_ENABLED', True):
            return

        logger.info("[任务] 自动修复监控...")
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT COUNT(*) FROM auto_fix_code_records WHERE status = 'pending'")
                pending = cursor.fetchone()[0]

                cursor.execute("SELECT COUNT(*) FROM auto_fix_code_records WHERE status = 'executed'")
                executed = cursor.fetchone()[0]

            logger.info(f"  ✓ 自动修复: 待处理{pending} / 已执行{executed}")
            self._log_maintenance('monitor', 'auto_fix', 'success', f'待处理:{pending}, 已执行:{executed}')
            self._update_stats(task, True)
        except Exception as e:
            logger.warning(f"  ⚠ 自动修复监控失败: {e}")
            self._update_stats(task, False)

        self.last_run[task] = datetime.now()

    def task_array_sync_check(self):
        """AI阵列同步状态检查"""
        task = 'array_sync_check'
        if not self._should_run(task, 'MAINT_ARRAY_SYNC_STATUS', 600):
            return

        logger.info("[任务] AI阵列同步状态检查...")
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT COUNT(*) FROM ai_cluster_employee")
                cluster_employees = cursor.fetchone()[0]

            logger.info(f"  ✓ AI集群员工: {cluster_employees}")
            self._log_maintenance('health_check', 'ai_array', 'success', f'集群员工:{cluster_employees}')
            self._update_stats(task, True)
        except Exception as e:
            logger.warning(f"  ⚠ AI阵列检查失败: {e}")
            self._update_stats(task, False)

        self.last_run[task] = datetime.now()

    def task_engine_health_check(self):
        """AI引擎健康检查"""
        task = 'engine_health'
        if not self._should_run(task, 'MAINT_ENGINE_HEALTH_CHECK', 60):
            return

        logger.info("[任务] AI引擎健康检查...")
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT COUNT(*) FROM ai_engine_config WHERE enabled = 1")
                active_engines = cursor.fetchone()[0]

                cursor.execute("SELECT COUNT(*) FROM ai_engine_logs WHERE created_at > ?",
                              ((datetime.now() - timedelta(hours=1)).isoformat(),))
                recent_logs = cursor.fetchone()[0]

            logger.info(f"  ✓ AI引擎: 活跃{active_engines} / 近1小时日志{recent_logs}")
            self._log_maintenance('health_check', 'ai_engine', 'success',
                                  f'活跃引擎:{active_engines}, 近期日志:{recent_logs}')
            self._update_stats(task, True)
        except Exception as e:
            logger.warning(f"  ⚠ AI引擎检查失败: {e}")
            self._update_stats(task, False)

        self.last_run[task] = datetime.now()

    def task_employee_log_cleanup(self):
        """AI员工日志清理"""
        task = 'employee_log_cleanup'
        if not self._should_run(task, 'MAINT_EMPLOYEE_LOG_CLEANUP', 604800):
            return

        logger.info("[任务] AI员工日志清理...")
        try:
            cutoff = (datetime.now() - timedelta(days=90)).isoformat()
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("DELETE FROM ai_task_logs WHERE created_at < ?", (cutoff,))
                deleted = cursor.execute("SELECT changes()").fetchone()[0]
                conn.commit()

            logger.info(f"  ✓ 清理了 {deleted} 条AI任务日志")
            self._log_maintenance('cleanup', 'ai_task_logs', 'success', f'清理{deleted}条日志')
            self._update_stats(task, True)
        except Exception as e:
            logger.warning(f"  ⚠ AI员工日志清理失败: {e}")
            self._update_stats(task, False)

        self.last_run[task] = datetime.now()

    def task_brain_feeding(self):
        """脑库数据投喂"""
        task = 'brain_feeding'
        if not self._should_run(task, 'BRAIN_FEEDING_INTERVAL', 300):
            return

        if not self._get_rule_bool('BRAIN_FEEDING_ENABLED', True):
            return

        logger.info("[任务] 脑库数据投喂...")
        try:
            from brain_feeding_engine import BrainFeedingEngine
            engine = BrainFeedingEngine()
            engine.feed_knowledge()
            self._update_stats(task, True)
        except Exception as e:
            logger.warning(f"  ⚠ 脑库投喂失败: {e}")
            self._update_stats(task, False)

        self.last_run[task] = datetime.now()

    def task_brain_learning(self):
        """AI员工学习"""
        task = 'brain_learning'
        if not self._should_run(task, 'BRAIN_LEARNING_INTERVAL', 600):
            return

        if not self._get_rule_bool('BRAIN_LEARNING_ENABLED', True):
            return

        logger.info("[任务] AI员工学习...")
        try:
            from brain_feeding_engine import BrainFeedingEngine
            engine = BrainFeedingEngine()
            engine.trigger_learning()
            self._update_stats(task, True)
        except Exception as e:
            logger.warning(f"  ⚠ AI学习失败: {e}")
            self._update_stats(task, False)

        self.last_run[task] = datetime.now()

    def task_brain_upgrade(self):
        """AI员工升级"""
        task = 'brain_upgrade'
        if not self._should_run(task, 'BRAIN_UPGRADE_INTERVAL', 1800):
            return

        if not self._get_rule_bool('BRAIN_UPGRADE_ENABLED', True):
            return

        logger.info("[任务] AI员工升级...")
        try:
            from brain_feeding_engine import BrainFeedingEngine
            engine = BrainFeedingEngine()
            engine.trigger_upgrade()
            self._update_stats(task, True)
        except Exception as e:
            logger.warning(f"  ⚠ AI升级失败: {e}")
            self._update_stats(task, False)

        self.last_run[task] = datetime.now()

    def task_neural_training(self):
        """神经网络训练"""
        task = 'neural_training'
        if not self._should_run(task, 'BRAIN_NEURAL_TRAINING_INTERVAL', 900):
            return

        if not self._get_rule_bool('BRAIN_NEURAL_NETWORK_ENABLED', True):
            return

        logger.info("[任务] 神经网络训练...")
        try:
            from brain_feeding_engine import BrainFeedingEngine
            engine = BrainFeedingEngine()
            engine.train_neural_network()
            self._update_stats(task, True)
        except Exception as e:
            logger.warning(f"  ⚠ 神经网络训练失败: {e}")
            self._update_stats(task, False)

        self.last_run[task] = datetime.now()

    def task_cluster_coordination(self):
        """AI集群统筹"""
        task = 'cluster_coordination'
        if not self._should_run(task, 'BRAIN_CLUSTER_COORDINATION_INTERVAL', 1200):
            return

        if not self._get_rule_bool('BRAIN_CLUSTER_COORDINATION_ENABLED', True):
            return

        logger.info("[任务] AI集群统筹...")
        try:
            from brain_feeding_engine import BrainFeedingEngine
            engine = BrainFeedingEngine()
            engine.coordinate_clusters()
            self._update_stats(task, True)
        except Exception as e:
            logger.warning(f"  ⚠ 集群统筹失败: {e}")
            self._update_stats(task, False)

        self.last_run[task] = datetime.now()

    def task_auto_repair(self):
        """自动修复项目异常"""
        task = 'auto_repair'
        if not self._should_run(task, 'AUTO_REPAIR_SCAN_INTERVAL', 60):
            return

        if not self._get_rule_bool('AUTO_REPAIR_ENABLED', True):
            return

        logger.info("[任务] 自动修复项目异常...")
        try:
            from auto_repair_engine import AutoRepairEngine
            engine = AutoRepairEngine()
            engine.run_repair_cycle()
            self._update_stats(task, True)
        except Exception as e:
            logger.warning(f"  ⚠ 自动修复失败: {e}")
            self._update_stats(task, False)

        self.last_run[task] = datetime.now()

    # ========== 调度引擎 ==========

    def get_all_tasks(self):
        """获取所有任务定义"""
        return [
            ('database_health_check', self.task_database_health_check),
            ('rule_status_sync', self.task_rule_status_sync),
            ('log_cleanup', self.task_log_cleanup),
            ('version_check', self.task_version_check),
            ('ai_employee_status_check', self.task_ai_employee_status_check),
            ('git_sync_check', self.task_git_sync_check),
            ('permission_sync', self.task_permission_sync),
            ('sandbox_health_check', self.task_sandbox_health_check),
            ('document_cleanup', self.task_document_cleanup),
            ('autofix_monitor', self.task_autofix_monitor),
            ('array_sync_check', self.task_array_sync_check),
            ('engine_health_check', self.task_engine_health_check),
            ('employee_log_cleanup', self.task_employee_log_cleanup),
            ('brain_feeding', self.task_brain_feeding),
            ('brain_learning', self.task_brain_learning),
            ('brain_upgrade', self.task_brain_upgrade),
            ('neural_training', self.task_neural_training),
            ('cluster_coordination', self.task_cluster_coordination),
            ('auto_repair', self.task_auto_repair),
        ]

    def run_once(self):
        """执行一轮所有任务"""
        tasks = self.get_all_tasks()
        logger.info(f"=== 执行调度轮次 ({len(tasks)}个任务) ===")

        for task_name, task_func in tasks:
            try:
                task_func()
            except Exception as e:
                logger.error(f"任务 {task_name} 异常: {e}")
                self._update_stats(task_name, False)

    def run_forever(self, loop_interval=30):
        """持续运行调度引擎"""
        self.running = True
        self.termination_requested = False
        self.task_stats['start_time'] = datetime.now().isoformat()

        # 写入PID文件
        self._write_pid_file()

        logger.info("=" * 60)
        logger.info("  MTSCOS AI 自动化调度引擎启动")
        logger.info(f"  PID: {os.getpid()}")
        logger.info(f"  数据库: {self.db_path}")
        logger.info(f"  调度轮次间隔: {loop_interval}秒")
        logger.info(f"  任务数量: {len(self.get_all_tasks())}")
        logger.info("  进程保护: 已启用 (SIGTERM/SIGINT拦截)")
        logger.info("=" * 60)

        self._log_operation('engine_start', 'scheduler', 'success',
                           f'调度引擎启动 PID:{os.getpid()} 任务数:{len(self.get_all_tasks())}')

        # 首次启动立即执行一轮
        self.run_once()
        self._write_heartbeat()

        while self.running:
            time.sleep(loop_interval)
            try:
                self.run_once()
                self._write_heartbeat()
            except Exception as e:
                logger.error(f"调度轮次异常: {e}")
                self._log_operation('engine_error', 'scheduler', 'failure', f'轮次异常: {e}')
                # 上报黑匣子
                self._report_disaster('scheduler_round_error', '调度轮次异常',
                                     f'轮次执行失败: {str(e)}', severity='critical')

        # 清理
        self._remove_pid_file()
        self._log_operation('engine_stop', 'scheduler', 'success',
                           f'调度引擎停止 PID:{os.getpid()} 总执行:{self.task_stats["total_runs"]}')
        logger.info("自动化调度引擎已停止")

    def stop(self):
        """停止调度引擎（仅内部调用）"""
        self.running = False
        logger.info("正在停止自动化调度引擎...")

    def request_termination(self, reason='manual', operator='unknown'):
        """请求终止调度引擎（人工终止入口）"""
        logger.warning("=" * 60)
        logger.warning(f"  ⚠ 收到人工终止请求")
        logger.warning(f"  操作者: {operator}")
        logger.warning(f"  原因: {reason}")
        logger.warning("=" * 60)

        self._log_operation('termination_requested', 'scheduler', 'warning',
                           f'操作者:{operator} 原因:{reason}')

        self.termination_requested = True
        self.running = False

    def get_status(self):
        """获取调度引擎状态"""
        uptime = None
        if self.task_stats.get('start_time'):
            uptime = (datetime.now() - datetime.fromisoformat(self.task_stats['start_time'])).total_seconds()

        return {
            'running': self.running,
            'uptime_seconds': uptime,
            'total_runs': self.task_stats['total_runs'],
            'success_count': self.task_stats['success_count'],
            'failure_count': self.task_stats['failure_count'],
            'start_time': self.task_stats['start_time'],
            'last_task': self.task_stats['last_task'],
            'last_task_time': self.task_stats['last_task_time'],
            'task_count': len(self.get_all_tasks()),
            'last_run_times': {k: v.isoformat() for k, v in self.last_run.items()}
        }


def main():
    scheduler = AutoScheduler()

    # 检查是否以单次模式运行
    if len(sys.argv) > 1 and sys.argv[1] == '--once':
        scheduler.run_once()
        status = scheduler.get_status()
        print(json.dumps(status, ensure_ascii=False, indent=2))
    else:
        try:
            scheduler.run_forever(loop_interval=30)
        except SystemExit:
            raise
        except Exception as e:
            logger.error(f"调度引擎异常退出: {e}")
            scheduler._log_operation('engine_crash', 'scheduler', 'failure', f'异常退出: {e}')
            # 上报黑匣子灾难事件
            scheduler._report_disaster('scheduler_crash', '调度引擎异常退出',
                                       f'引擎崩溃: {str(e)}', severity='disaster',
                                       impact_scope='调度引擎全部任务')
            raise

    return 0


if __name__ == '__main__':
    sys.exit(main())
