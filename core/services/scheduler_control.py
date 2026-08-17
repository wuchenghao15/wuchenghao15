from core.db_path import get_db_path as _mtscos_get_db_path
#!/usr/bin/env python3
"""
MTSCOS AI 调度引擎控制脚本 - 增强版
功能：
1. 启动/停止/重启/状态查询调度引擎
2. 看门狗守护进程：监控调度引擎并自动重启
3. 意外终止检测：区分崩溃/被杀与正常停止
4. 自动重启机制：指数退避、最大重试次数、冷却期
5. 崩溃记录与恢复日志到数据库
6. 人工终止时显示警告框，需要确认和填写原因
"""

import os
import sys
import json
import sqlite3
import subprocess
import getpass
import time
import signal
import threading
from datetime import datetime, timedelta

DATABASE_PATH = _mtscos_get_db_path('app.db')
PID_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), '.scheduler_pid')
HEARTBEAT_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), '.scheduler_heartbeat')
WATCHDOG_PID_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), '.watchdog_pid')
SCHEDULER_SCRIPT = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'auto_scheduler.py')
LOG_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'scheduler_control.log')

# 看门狗配置常量
WATCHDOG_CHECK_INTERVAL = 5          # 检查间隔（秒）
WATCHDOG_HEARTBEAT_TIMEOUT = 30      # 心跳超时（秒）- 超过此时长判定为死锁
WATCHDOG_MAX_RESTARTS = 10           # 最大重启次数
WATCHDOG_RESTART_DELAY_INITIAL = 5   # 初始重启延迟（秒）
WATCHDOG_RESTART_DELAY_MAX = 300     # 最大重启延迟（秒）
WATCHDOG_COOLDOWN_PERIOD = 300       # 冷却期（秒）- 成功运行超过此时长后重置重启计数
WATCHDOG_BACKOFF_MULTIPLIER = 2      # 退避乘数

import logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    handlers=[
        logging.FileHandler(LOG_FILE, encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger('SchedulerControl')


def get_db_connection():
    return sqlite3.connect(DATABASE_PATH)


def get_rule_value(rule_code, default=None):
    """从system_rules读取规则值"""
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT rule_value FROM system_rules WHERE rule_code = ? AND is_active = 1',
                          (rule_code,))
            result = cursor.fetchone()
            return result[0] if result else default
    except Exception:
        return default


def get_rule_bool(rule_code, default=False):
    val = get_rule_value(rule_code)
    if val is not None:
        return val in ('1', 'true', 'True', 'yes', 'Yes')
    return default


def get_rule_int(rule_code, default=0):
    val = get_rule_value(rule_code)
    try:
        return int(val) if val is not None else default
    except (ValueError, TypeError):
        return default


def log_operation(operation_type, target, result, details=''):
    """记录操作日志到数据库"""
    try:
        with get_db_connection() as conn:
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


# ==================== 崩溃记录 ====================

def log_crash(pid, crash_type, exit_code=None, signal_received=None, details=''):
    """
    记录崩溃信息到数据库
    crash_type: 'crash' (意外崩溃), 'killed' (被信号终止), 'heartbeat_timeout' (心跳超时)
    """
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS scheduler_crash_logs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    pid INTEGER,
                    crash_type TEXT NOT NULL,
                    exit_code INTEGER,
                    signal_received INTEGER,
                    details TEXT,
                    crashed_at TEXT NOT NULL,
                    restarted_at TEXT,
                    restart_pid INTEGER,
                    restart_status TEXT DEFAULT 'pending'
                )
            ''')
            cursor.execute('''
                INSERT INTO scheduler_crash_logs
                (pid, crash_type, exit_code, signal_received, details, crashed_at)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (pid, crash_type, exit_code, signal_received, details,
                  datetime.now().strftime('%Y-%m-%d %H:%M:%S')))
            conn.commit()
            logger.error(f"[崩溃记录] PID:{pid} 类型:{crash_type} 退出码:{exit_code} 信号:{signal_received}")
    except Exception as e:
        logger.error(f"记录崩溃信息失败: {e}")


def update_crash_restart(pid, restart_pid, restart_status):
    """更新崩溃记录的重启信息"""
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                UPDATE scheduler_crash_logs
                SET restarted_at = ?, restart_pid = ?, restart_status = ?
                WHERE pid = ? AND restart_status = 'pending'
                ORDER BY crashed_at DESC LIMIT 1
            ''', (datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                  restart_pid, restart_status, pid))
            conn.commit()
    except Exception as e:
        logger.error(f"更新崩溃重启记录失败: {e}")


# ==================== 进程管理 ====================

def get_scheduler_pid():
    """获取调度引擎PID"""
    if os.path.exists(PID_FILE):
        try:
            with open(PID_FILE, 'r') as f:
                pid = int(f.read().strip())
            try:
                os.kill(pid, 0)
                return pid
            except OSError:
                os.remove(PID_FILE)
        except (ValueError, IOError):
            pass

    try:
        result = subprocess.run(
            ['ps', 'aux'],
            capture_output=True, text=True, timeout=10
        )
        for line in result.stdout.split('\n'):
            if 'auto_scheduler.py' in line and 'grep' not in line and 'scheduler_control' not in line:
                parts = line.split()
                if len(parts) > 1:
                    return int(parts[1])
    except Exception:
        pass

    return None


def get_watchdog_pid():
    """获取看门狗进程PID"""
    if os.path.exists(WATCHDOG_PID_FILE):
        try:
            with open(WATCHDOG_PID_FILE, 'r') as f:
                pid = int(f.read().strip())
            try:
                os.kill(pid, 0)
                return pid
            except OSError:
                os.remove(WATCHDOG_PID_FILE)
        except (ValueError, IOError):
            pass

    try:
        result = subprocess.run(
            ['ps', 'aux'],
            capture_output=True, text=True, timeout=10
        )
        for line in result.stdout.split('\n'):
            if 'scheduler_control.py' in line and 'watchdog' in line and 'grep' not in line:
                parts = line.split()
                if len(parts) > 1:
                    return int(parts[1])
    except Exception:
        pass

    return None


def _write_pid_file(filepath, pid):
    """写入PID文件"""
    try:
        with open(filepath, 'w') as f:
            f.write(str(pid))
    except Exception as e:
        logger.error(f"写入PID文件失败: {e}")


def _read_heartbeat():
    """读取心跳文件"""
    if os.path.exists(HEARTBEAT_FILE):
        try:
            with open(HEARTBEAT_FILE, 'r') as f:
                return json.load(f)
        except Exception:
            pass
    return None


def _is_process_alive(pid):
    """检查进程是否存活"""
    try:
        os.kill(pid, 0)
        return True
    except OSError:
        return False


# ==================== 对话框 ====================

def show_warning_dialog(title, message):
    """显示macOS原生警告框"""
    try:
        script = f'''
        display dialog "{message}" ¬
            with title "{title}" ¬
            with icon caution ¬
            buttons {{"取消", "确认终止"}} ¬
            default button "取消"
        '''
        result = subprocess.run(
            ['osascript', '-e', script],
            capture_output=True, text=True, timeout=60
        )
        return result.returncode == 0
    except subprocess.TimeoutExpired:
        print("⚠ 警告框超时，操作已取消")
        return False
    except Exception:
        print(f"\n{'='*60}")
        print(f"  ⚠ 警告: {title}")
        print(f"  {'='*60}")
        print(f"  {message}")
        print(f"  {'='*60}")
        response = input("\n确认终止？(输入 'yes' 确认，其他取消): ")
        return response.strip().lower() == 'yes'


def show_reason_dialog():
    """显示终止原因输入框"""
    min_length = get_rule_int('AUTO_SCHEDULER_TERMINATION_REASON_MIN_LENGTH', 10)

    try:
        script = f'''
        set dialogResult to display dialog "请输入终止调度引擎的原因（至少{min_length}个字符）:" ¬
            with title "终止原因" ¬
            with icon caution ¬
            default answer "" ¬
            buttons {{"取消", "提交"}} ¬
            default button "提交"
        return text returned of dialogResult
        '''
        result = subprocess.run(
            ['osascript', '-e', script],
            capture_output=True, text=True, timeout=120
        )
        if result.returncode == 0:
            reason = result.stdout.strip()
            if len(reason) < min_length:
                print(f"✗ 终止原因太短（需要至少{min_length}个字符）")
                return None
            return reason
        return None
    except Exception:
        reason = input(f"请输入终止原因（至少{min_length}个字符）: ")
        if len(reason.strip()) < min_length:
            print(f"✗ 终止原因太短（需要至少{min_length}个字符）")
            return None
        return reason.strip()


def show_info_dialog(title, message):
    """显示信息对话框"""
    try:
        script = f'display dialog "{message}" with title "{title}" with icon note buttons {{"确定"}} default button "确定"'
        subprocess.run(['osascript', '-e', script], capture_output=True, text=True, timeout=30)
    except Exception:
        print(f"[{title}] {message}")


# ==================== 启动/停止/重启命令 ====================

def cmd_start():
    """启动调度引擎"""
    pid = get_scheduler_pid()
    if pid:
        print(f"⚠ 调度引擎已在运行中 (PID: {pid})")
        log_operation('start_attempt', 'scheduler', 'warning', f'引擎已在运行 PID:{pid}')
        return False

    print("正在启动调度引擎...")

    log_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'auto_scheduler.log')
    with open(log_path, 'a') as log_file:
        proc = subprocess.Popen(
            [sys.executable, SCHEDULER_SCRIPT],
            stdout=log_file, stderr=log_file,
            start_new_session=True
        )

    time.sleep(2)

    new_pid = get_scheduler_pid()
    if new_pid:
        operator = getpass.getuser()
        print(f"✓ 调度引擎已启动 (PID: {new_pid})")
        log_operation('start', 'scheduler', 'success',
                     f'调度引擎启动 PID:{new_pid} 操作者:{operator}')
        show_info_dialog("启动成功", f"调度引擎已成功启动\nPID: {new_pid}")
        return True
    else:
        print("✗ 调度引擎启动失败")
        log_operation('start', 'scheduler', 'failure', '启动失败')
        return False


def cmd_stop():
    """停止调度引擎（带警告框和原因确认）"""
    pid = get_scheduler_pid()
    if not pid:
        print("⚠ 调度引擎未在运行")
        return False

    operator = getpass.getuser()

    if get_rule_bool('AUTO_SCHEDULER_TERMINATION_WARNING_ENABLED', True):
        warning_msg = (
            f"您正在尝试终止自动化调度引擎 (PID: {pid})\\n\\n" +
            f"终止后将停止以下自动化任务:\\n" +
            f"  • 数据库健康检查\\n" +
            f"  • 规则状态同步\\n" +
            f"  • 日志清理\\n" +
            f"  • 版本号检查\\n" +
            f"  • AI员工状态检查\\n" +
            f"  • Git同步检查\\n" +
            f"  • 权限同步\\n" +
            f"  • 沙盒健康检查\\n" +
            f"  • 文档清理\\n" +
            f"  • 自动修复监控\\n" +
            f"  • AI安全防御\\n\\n" +
            f"确定要终止吗？"
        )

        if not show_warning_dialog("终止调度引擎警告", warning_msg):
            print("✓ 用户取消终止操作")
            log_operation('stop_cancelled', 'scheduler', 'info', '用户取消终止')
            return False

    if get_rule_bool('AUTO_SCHEDULER_TERMINATION_REQUIRE_REASON', True):
        reason = show_reason_dialog()
        if not reason:
            print("✗ 未提供终止原因，操作已取消")
            log_operation('stop_cancelled', 'scheduler', 'warning', '未提供终止原因')
            return False
    else:
        reason = 'no_reason_required'

    # 设置正常停止标记
    _set_normal_stop_flag(True)

    log_operation('stop', 'scheduler', 'warning',
                 f'人工终止 PID:{pid} 操作者:{operator} 原因:{reason}')

    print(f"正在终止调度引擎 (PID: {pid})...")
    try:
        os.kill(pid, signal.SIGTERM)
    except OSError:
        print("⚠ SIGTERM被拦截，使用强制终止...")
        log_operation('force_stop', 'scheduler', 'warning',
                     f'强制终止 PID:{pid} 操作者:{operator}')
        os.kill(pid, signal.SIGKILL)

    for i in range(10):
        time.sleep(1)
        try:
            os.kill(pid, 0)
        except OSError:
            break
    else:
        print("⚠ 进程未响应，强制终止...")
        try:
            os.kill(pid, signal.SIGKILL)
        except OSError:
            pass

    if os.path.exists(PID_FILE):
        os.remove(PID_FILE)

    # 清除正常停止标记
    _set_normal_stop_flag(False)

    if get_scheduler_pid() is None:
        print(f"✓ 调度引擎已终止 (PID: {pid})")
        log_operation('stop_success', 'scheduler', 'success',
                     f'终止成功 PID:{pid} 操作者:{operator} 原因:{reason}')
        show_info_dialog("终止成功", f"调度引擎已终止\nPID: {pid}\n原因: {reason}")
        return True
    else:
        print(f"✗ 终止失败，进程仍在运行")
        log_operation('stop_failed', 'scheduler', 'failure',
                     f'终止失败 PID:{pid}')
        return False


def cmd_restart():
    """重启调度引擎"""
    print("正在重启调度引擎...")
    operator = getpass.getuser()

    log_operation('restart', 'scheduler', 'info', f'重启请求 操作者:{operator}')

    pid = get_scheduler_pid()
    if pid:
        if not cmd_stop():
            print("✗ 停止失败，取消重启")
            return False
        time.sleep(3)

    return cmd_start()


# ==================== 正常停止标记 ====================

_NORMAL_STOP_FLAG = False


def _set_normal_stop_flag(value):
    """设置正常停止标记"""
    global _NORMAL_STOP_FLAG
    _NORMAL_STOP_FLAG = value


def _is_normal_stop():
    """检查是否是正常停止"""
    return _NORMAL_STOP_FLAG


# ==================== 看门狗守护进程 ====================

class WatchdogDaemon:
    """看门狗守护进程 - 监控调度引擎并自动重启"""

    def __init__(self):
        self._running = False
        self._thread = None
        self._restart_count = 0
        self._last_restart_time = 0
        self._last_success_start_time = 0
        self._current_delay = WATCHDOG_RESTART_DELAY_INITIAL
        self._lock = threading.Lock()

    def start(self, auto_start_scheduler=True):
        """启动看门狗守护进程"""
        if self._running:
            print("⚠ 看门狗已在运行")
            return False

        if get_watchdog_pid():
            print("⚠ 看门狗进程已在运行")
            return False

        print("正在启动看门狗守护进程...")

        # 写入看门狗PID文件
        _write_pid_file(WATCHDOG_PID_FILE, os.getpid())

        # 如果调度器未运行，先启动
        if auto_start_scheduler and not get_scheduler_pid():
            print("  调度引擎未运行，启动调度引擎...")
            if cmd_start():
                self._last_success_start_time = time.time()
            else:
                print("  ✗ 调度引擎启动失败")

        self._running = True
        self._thread = threading.Thread(target=self._watchdog_loop, daemon=True)
        self._thread.start()

        logger.info("[看门狗] 守护进程已启动")
        log_operation('watchdog_start', 'scheduler', 'success', '看门狗守护进程启动')
        print("✓ 看门狗守护进程已启动")
        return True

    def stop(self):
        """停止看门狗守护进程"""
        if not self._running:
            print("⚠ 看门狗未在运行")
            return False

        print("正在停止看门狗守护进程...")
        self._running = False

        if self._thread:
            self._thread.join(timeout=10)

        # 清除看门狗PID文件
        if os.path.exists(WATCHDOG_PID_FILE):
            os.remove(WATCHDOG_PID_FILE)

        logger.info("[看门狗] 守护进程已停止")
        log_operation('watchdog_stop', 'scheduler', 'success', '看门狗守护进程停止')
        print("✓ 看门狗守护进程已停止")
        return True

    def _watchdog_loop(self):
        """看门狗主循环"""
        while self._running:
            try:
                self._check_and_recover()
            except Exception as e:
                logger.error(f"[看门狗] 监控循环异常: {e}")

            for _ in range(WATCHDOG_CHECK_INTERVAL):
                if not self._running:
                    break
                time.sleep(1)

    def _check_and_recover(self):
        """检查调度引擎状态并进行恢复"""
        pid = get_scheduler_pid()

        if not pid:
            # 调度器未运行
            if _is_normal_stop():
                logger.debug("[看门狗] 检测到正常停止，跳过重启")
                return

            self._handle_scheduler_down()
            return

        # 调度器运行中，检查心跳
        heartbeat = _read_heartbeat()
        if heartbeat:
            try:
                heartbeat_time = datetime.strptime(
                    heartbeat.get('timestamp', ''),
                    '%Y-%m-%d %H:%M:%S'
                ).timestamp()
                if time.time() - heartbeat_time > WATCHDOG_HEARTBEAT_TIMEOUT:
                    logger.warning(f"[看门狗] 心跳超时: 上次心跳 {heartbeat.get('timestamp')}")
                    self._handle_heartbeat_timeout(pid)
                    return
            except Exception:
                pass

        # 检查冷却期 - 成功运行超过冷却期则重置重启计数
        if self._last_success_start_time and \
           time.time() - self._last_success_start_time > WATCHDOG_COOLDOWN_PERIOD:
            self._reset_restart_count()

    def _handle_scheduler_down(self):
        """处理调度器崩溃/停止"""
        with self._lock:
            if self._restart_count >= WATCHDOG_MAX_RESTARTS:
                logger.error(f"[看门狗] 已达到最大重启次数 ({WATCHDOG_MAX_RESTARTS})，停止自动重启")
                log_operation('watchdog_max_restarts', 'scheduler', 'critical',
                             f'达到最大重启次数 {WATCHDOG_MAX_RESTARTS}，停止自动重启')
                self.stop()
                return

            # 计算延迟
            delay = min(self._current_delay, WATCHDOG_RESTART_DELAY_MAX)

            logger.warning(f"[看门狗] 检测到调度引擎停止，{delay}秒后重启 (第{self._restart_count + 1}/{WATCHDOG_MAX_RESTARTS}次)")
            log_operation('watchdog_detect_down', 'scheduler', 'warning',
                         f'检测到停止，{delay}秒后重启 (第{self._restart_count + 1}/{WATCHDOG_MAX_RESTARTS}次)')

            time.sleep(delay)

            # 再次检查状态（可能已经被手动启动）
            if get_scheduler_pid():
                logger.info("[看门狗] 调度引擎已被手动启动")
                self._last_success_start_time = time.time()
                return

            # 记录崩溃
            log_crash(0, 'crash', details=f"看门狗检测到停止，重启计数:{self._restart_count}")

            # 启动调度器
            print(f"[看门狗] 尝试重启调度引擎 (第{self._restart_count + 1}次)...")
            if cmd_start():
                self._restart_count += 1
                self._last_restart_time = time.time()
                self._last_success_start_time = time.time()
                self._current_delay *= WATCHDOG_BACKOFF_MULTIPLIER

                new_pid = get_scheduler_pid()
                update_crash_restart(0, new_pid, 'success')
                logger.info(f"[看门狗] 重启成功 (PID: {new_pid}, 第{self._restart_count}次)")
                log_operation('watchdog_restart_success', 'scheduler', 'success',
                             f'重启成功 PID:{new_pid} 次数:{self._restart_count}')
            else:
                self._restart_count += 1
                self._last_restart_time = time.time()
                self._current_delay *= WATCHDOG_BACKOFF_MULTIPLIER

                update_crash_restart(0, None, 'failed')
                logger.error(f"[看门狗] 重启失败 (第{self._restart_count}次)")
                log_operation('watchdog_restart_failed', 'scheduler', 'failure',
                             f'重启失败 次数:{self._restart_count}')

    def _handle_heartbeat_timeout(self, pid):
        """处理心跳超时（死锁检测）"""
        logger.error(f"[看门狗] 检测到心跳超时，强制重启 PID:{pid}")
        log_crash(pid, 'heartbeat_timeout', details=f"心跳超时 {WATCHDOG_HEARTBEAT_TIMEOUT}秒")

        # 强制终止
        try:
            os.kill(pid, signal.SIGKILL)
            time.sleep(2)
        except OSError:
            pass

        # 清理PID文件
        if os.path.exists(PID_FILE):
            os.remove(PID_FILE)

        # 重启
        self._handle_scheduler_down()

    def _reset_restart_count(self):
        """重置重启计数（成功运行超过冷却期后）"""
        with self._lock:
            if self._restart_count > 0:
                logger.info(f"[看门狗] 成功运行超过冷却期，重置重启计数 ({self._restart_count} → 0)")
                self._restart_count = 0
                self._current_delay = WATCHDOG_RESTART_DELAY_INITIAL

    def get_status(self):
        """获取看门狗状态"""
        with self._lock:
            return {
                'running': self._running,
                'restart_count': self._restart_count,
                'max_restarts': WATCHDOG_MAX_RESTARTS,
                'current_delay': self._current_delay,
                'last_restart_time': self._last_restart_time,
                'last_success_start_time': self._last_success_start_time,
                'cooldown_period': WATCHDOG_COOLDOWN_PERIOD,
                'check_interval': WATCHDOG_CHECK_INTERVAL,
                'heartbeat_timeout': WATCHDOG_HEARTBEAT_TIMEOUT
            }


# ==================== 看门狗命令 ====================

_watchdog_daemon = None


def _get_watchdog():
    """获取看门狗实例"""
    global _watchdog_daemon
    if _watchdog_daemon is None:
        _watchdog_daemon = WatchdogDaemon()
    return _watchdog_daemon


def cmd_watchdog_start():
    """启动看门狗守护进程"""
    return _get_watchdog().start()


def cmd_watchdog_stop():
    """停止看门狗守护进程"""
    return _get_watchdog().stop()


def cmd_watchdog_status():
    """查看看门狗状态"""
    wd = _get_watchdog()
    status = wd.get_status()
    pid = get_watchdog_pid()

    print("=" * 60)
    print("  MTSCOS AI 看门狗守护进程状态")
    print("=" * 60)

    print(f"  进程状态:   {'运行中 ✓' if pid else '未运行 ✗'}")
    if pid:
        print(f"  进程PID:    {pid}")

    print(f"  守护状态:   {'活动' if status['running'] else '停止'}")
    print(f"  重启次数:   {status['restart_count']}/{status['max_restarts']}")
    print(f"  当前延迟:   {status['current_delay']}秒")
    print(f"  检查间隔:   {status['check_interval']}秒")
    print(f"  心跳超时:   {status['heartbeat_timeout']}秒")
    print(f"  冷却周期:   {status['cooldown_period']}秒")

    if status['last_restart_time']:
        print(f"  上次重启:   {datetime.fromtimestamp(status['last_restart_time']).strftime('%Y-%m-%d %H:%M:%S')}")

    if status['last_success_start_time']:
        uptime = int(time.time() - status['last_success_start_time'])
        print(f"  成功运行:   {uptime}秒")

    # 检查是否接近最大重启次数
    if status['restart_count'] >= status['max_restarts'] - 2:
        print(f"\n  ⚠ 警告: 重启次数接近上限")

    print("=" * 60)

    log_operation('watchdog_status', 'scheduler', 'info', f'看门狗状态查询')


def cmd_watchdog_restart():
    """重启看门狗守护进程"""
    print("正在重启看门狗守护进程...")
    _get_watchdog().stop()
    time.sleep(2)
    return _get_watchdog().start()


# ==================== 状态查询命令 ====================

def cmd_status():
    """查询调度引擎状态"""
    pid = get_scheduler_pid()
    wd_pid = get_watchdog_pid()

    print("=" * 60)
    print("  MTSCOS AI 调度引擎状态")
    print("=" * 60)

    print(f"\n  调度引擎:")
    if pid:
        print(f"    状态:     运行中 ✓")
        print(f"    PID:      {pid}")

        if os.path.exists(HEARTBEAT_FILE):
            try:
                with open(HEARTBEAT_FILE, 'r') as f:
                    heartbeat = json.load(f)
                print(f"    心跳时间: {heartbeat.get('timestamp', 'unknown')}")
                print(f"    总执行数: {heartbeat.get('total_runs', 'unknown')}")
            except Exception:
                print("    心跳文件: 读取失败")

        try:
            result = subprocess.run(
                ['ps', '-p', str(pid), '-o', 'etime='],
                capture_output=True, text=True, timeout=5
            )
            if result.stdout.strip():
                print(f"    运行时间: {result.stdout.strip()}")
        except Exception:
            pass
    else:
        print(f"    状态:     未运行 ✗")

    print(f"\n  看门狗:")
    if wd_pid:
        print(f"    状态:     运行中 ✓")
        print(f"    PID:      {wd_pid}")
    else:
        print(f"    状态:     未运行 ✗")

    # 数据库日志统计
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM system_maintenance_logs WHERE timestamp > ?",
                          ((datetime.now() - timedelta(hours=24)).strftime('%Y-%m-%d %H:%M:%S'),))
            log_count = cursor.fetchone()[0]
            print(f"\n  24小时日志: {log_count} 条")

            cursor.execute("""SELECT operation_type, result, COUNT(*) 
                            FROM system_maintenance_logs 
                            WHERE timestamp > ?
                            GROUP BY operation_type, result
                            ORDER BY COUNT(*) DESC LIMIT 5""",
                          ((datetime.now() - timedelta(hours=24)).strftime('%Y-%m-%d %H:%M:%S'),))
            recent = cursor.fetchall()
            if recent:
                print(f"\n  近24小时操作统计:")
                for op in recent:
                    print(f"    {op[0]:25} | {op[1]:10} | {op[2]} 次")

            # 崩溃统计
            cursor.execute("SELECT COUNT(*) FROM scheduler_crash_logs")
            crash_count = cursor.fetchone()[0]
            print(f"\n  崩溃记录总数: {crash_count}")

            cursor.execute("SELECT COUNT(*) FROM scheduler_crash_logs WHERE crashed_at > ?",
                          ((datetime.now() - timedelta(hours=24)).strftime('%Y-%m-%d %H:%M:%S'),))
            crash_count_24h = cursor.fetchone()[0]
            print(f"  近24小时崩溃: {crash_count_24h}")
    except Exception as e:
        print(f"  日志统计: 读取失败 ({e})")

    print("\n" + "=" * 60)

    log_operation('status_query', 'scheduler', 'info', f'状态查询 PID:{"运行中" if pid else "未运行"}')


def cmd_logs(limit=20):
    """查看最近操作日志"""
    print(f"\n=== 最近 {limit} 条操作日志 ===\n")

    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT operation_type, target, result, details, timestamp
                FROM system_maintenance_logs
                WHERE operation_type IN ('engine_start', 'engine_stop', 'engine_crash',
                    'termination_requested', 'stop', 'start', 'restart', 'force_stop',
                    'signal_received', 'stop_cancelled', 'stop_success', 'stop_failed',
                    'watchdog_start', 'watchdog_stop', 'watchdog_restart_success',
                    'watchdog_restart_failed', 'watchdog_max_restarts')
                ORDER BY timestamp DESC
                LIMIT ?
            """, (limit,))
            logs = cursor.fetchall()

            if logs:
                for log in logs:
                    print(f"  [{log[4]}] {log[0]:25} | {log[1]:15} | {log[2]:8} | {log[3]}")
            else:
                print("  无操作日志")
    except Exception as e:
        print(f"  读取日志失败: {e}")


def cmd_crash_logs(limit=10):
    """查看崩溃记录"""
    print(f"\n=== 最近 {limit} 条崩溃记录 ===\n")

    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT pid, crash_type, exit_code, signal_received, details, 
                       crashed_at, restarted_at, restart_pid, restart_status
                FROM scheduler_crash_logs
                ORDER BY crashed_at DESC
                LIMIT ?
            """, (limit,))
            logs = cursor.fetchall()

            if logs:
                for log in logs:
                    status = log[8] if log[8] else 'pending'
                    print(f"  [{log[5]}] PID:{log[0]} 类型:{log[1]} 退出码:{log[2]} 信号:{log[3]}")
                    if log[4]:
                        print(f"           详情: {log[4]}")
                    if log[6]:
                        print(f"           重启于: {log[6]} PID:{log[7]} 状态:{status}")
            else:
                print("  无崩溃记录")
    except Exception as e:
        print(f"  读取崩溃记录失败: {e}")


# ==================== 守护进程模式 ====================

def run_daemon():
    """以守护进程模式运行看门狗"""
    print("[看门狗] 启动守护进程模式...")
    logger.info("[看门狗] 守护进程模式启动")

    # 忽略中断信号
    signal.signal(signal.SIGINT, signal.SIG_IGN)
    signal.signal(signal.SIGTERM, signal.SIG_IGN)

    # 启动看门狗
    _get_watchdog().start(auto_start_scheduler=True)

    # 主循环 - 保持进程存活
    while True:
        time.sleep(60)


# ==================== 帮助信息 ====================

def show_help():
    """显示帮助"""
    print("""
MTSCOS AI 调度引擎控制脚本
========================

用法:
  python3 scheduler_control.py <命令>

命令:
  start         启动调度引擎
  stop          停止调度引擎（带警告框和原因确认）
  restart       重启调度引擎
  status        查看调度引擎和看门狗状态
  logs          查看最近操作日志
  crash_logs    查看崩溃记录
  watchdog      看门狗命令: start/stop/restart/status

看门狗子命令:
  python3 scheduler_control.py watchdog start    启动看门狗守护进程
  python3 scheduler_control.py watchdog stop     停止看门狗守护进程
  python3 scheduler_control.py watchdog restart  重启看门狗守护进程
  python3 scheduler_control.py watchdog status   查看看门狗状态

守护进程模式:
  python3 scheduler_control.py daemon

安全规则:
  - 人工终止时显示警告框，列出所有受影响的任务
  - 需要二次确认才能终止
  - 需要填写终止原因（至少10个字符）
  - 所有操作记录到system_maintenance_logs表

看门狗功能:
  - 每5秒检查调度引擎状态
  - 心跳超时(30秒)判定为死锁，强制重启
  - 意外终止自动重启，指数退避策略
  - 最大重启次数10次，防止无限循环
  - 成功运行超过5分钟(冷却期)后重置重启计数
  - 崩溃信息记录到scheduler_crash_logs表
""")


if __name__ == '__main__':
    if len(sys.argv) < 2:
        show_help()
        sys.exit(0)

    cmd = sys.argv[1].lower()

    if cmd == 'start':
        cmd_start()
    elif cmd == 'stop':
        cmd_stop()
    elif cmd == 'restart':
        cmd_restart()
    elif cmd == 'status':
        cmd_status()
    elif cmd == 'logs':
        limit = int(sys.argv[2]) if len(sys.argv) > 2 else 20
        cmd_logs(limit)
    elif cmd == 'crash_logs':
        limit = int(sys.argv[2]) if len(sys.argv) > 2 else 10
        cmd_crash_logs(limit)
    elif cmd == 'watchdog':
        if len(sys.argv) < 3:
            print("看门狗命令需要子命令: start/stop/restart/status")
            sys.exit(1)
        sub_cmd = sys.argv[2].lower()
        if sub_cmd == 'start':
            cmd_watchdog_start()
        elif sub_cmd == 'stop':
            cmd_watchdog_stop()
        elif sub_cmd == 'restart':
            cmd_watchdog_restart()
        elif sub_cmd == 'status':
            cmd_watchdog_status()
        else:
            print(f"未知看门狗命令: {sub_cmd}")
    elif cmd == 'daemon':
        run_daemon()
    elif cmd == 'help':
        show_help()
    else:
        print(f"未知命令: {cmd}")
        show_help()
        sys.exit(1)
