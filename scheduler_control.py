#!/usr/bin/env python3
"""
MTSCOS AI 调度引擎控制脚本
提供启动、停止、重启、状态查询功能
人工终止时显示警告框，需要确认和填写原因
所有操作记录日志并上报数据库
"""
import os
import sys
import json
import sqlite3
import subprocess
import getpass
from datetime import datetime

DATABASE_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'app.db')
PID_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), '.scheduler_pid')
HEARTBEAT_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), '.scheduler_heartbeat')
SCHEDULER_SCRIPT = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'auto_scheduler.py')
LOG_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'scheduler_control.log')

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


def get_scheduler_pid():
    """获取调度引擎PID"""
    # 方式1: 从PID文件读取
    if os.path.exists(PID_FILE):
        try:
            with open(PID_FILE, 'r') as f:
                pid = int(f.read().strip())
            # 验证进程是否存活
            try:
                os.kill(pid, 0)
                return pid
            except OSError:
                # 进程不存在，清理PID文件
                os.remove(PID_FILE)
        except (ValueError, IOError):
            pass

    # 方式2: 通过ps命令查找
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


def show_warning_dialog(title, message):
    """显示macOS原生警告框"""
    try:
        # 使用osascript显示macOS原生对话框
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
        # 如果用户点击"取消"，osascript返回非0退出码
        return result.returncode == 0
    except subprocess.TimeoutExpired:
        print("⚠ 警告框超时，操作已取消")
        return False
    except Exception as e:
        # 如果osascript不可用，回退到终端确认
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
        # 回退到终端输入
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


def cmd_start():
    """启动调度引擎"""
    pid = get_scheduler_pid()
    if pid:
        print(f"⚠ 调度引擎已在运行中 (PID: {pid})")
        log_operation('start_attempt', 'scheduler', 'warning', f'引擎已在运行 PID:{pid}')
        return False

    print("正在启动调度引擎...")

    # 后台启动
    log_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'auto_scheduler.log')
    with open(log_path, 'a') as devnull:
        proc = subprocess.Popen(
            [sys.executable, SCHEDULER_SCRIPT],
            stdout=devnull, stderr=devnull,
            start_new_session=True
        )

    # 等待进程启动
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

    # 检查是否需要警告框
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
            f"  • 阵列同步检查\\n" +
            f"  • 引擎健康检查\\n" +
            f"  • 员工日志清理\\n\\n" +
            f"确定要终止吗？"
        )

        if not show_warning_dialog("终止调度引擎警告", warning_msg):
            print("✓ 用户取消终止操作")
            log_operation('stop_cancelled', 'scheduler', 'info', '用户取消终止')
            return False

    # 检查是否需要填写原因
    if get_rule_bool('AUTO_SCHEDULER_TERMINATION_REQUIRE_REASON', True):
        reason = show_reason_dialog()
        if not reason:
            print("✗ 未提供终止原因，操作已取消")
            log_operation('stop_cancelled', 'scheduler', 'warning', '未提供终止原因')
            return False
    else:
        reason = 'no_reason_required'

    # 记录终止操作
    log_operation('stop', 'scheduler', 'warning',
                 f'人工终止 PID:{pid} 操作者:{operator} 原因:{reason}')

    # 发送SIGTERM信号
    print(f"正在终止调度引擎 (PID: {pid})...")
    try:
        os.kill(pid, signal.SIGTERM)
    except OSError:
        # SIGTERM被拦截，使用SIGKILL作为最后手段
        print("⚠ SIGTERM被拦截，使用强制终止...")
        log_operation('force_stop', 'scheduler', 'warning',
                     f'强制终止 PID:{pid} 操作者:{operator}')
        os.kill(pid, signal.SIGKILL)

    # 等待进程退出
    import time
    for i in range(10):
        time.sleep(1)
        try:
            os.kill(pid, 0)
        except OSError:
            # 进程已退出
            break
    else:
        # 进程仍然存活，强制kill
        print("⚠ 进程未响应，强制终止...")
        try:
            os.kill(pid, signal.SIGKILL)
        except OSError:
            pass

    # 清理PID文件
    if os.path.exists(PID_FILE):
        os.remove(PID_FILE)

    # 验证
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

    # 先停止
    pid = get_scheduler_pid()
    if pid:
        if not cmd_stop():
            print("✗ 停止失败，取消重启")
            return False

        # 等待进程完全退出
        import time
        time.sleep(3)

    # 再启动
    return cmd_start()


def cmd_status():
    """查询调度引擎状态"""
    pid = get_scheduler_pid()

    print("=" * 60)
    print("  MTSCOS AI 调度引擎状态")
    print("=" * 60)

    if pid:
        print(f"  状态:     运行中 ✓")
        print(f"  PID:      {pid}")

        # 读取心跳
        if os.path.exists(HEARTBEAT_FILE):
            try:
                with open(HEARTBEAT_FILE, 'r') as f:
                    heartbeat = json.load(f)
                print(f"  心跳时间: {heartbeat.get('timestamp', 'unknown')}")
                print(f"  总执行数: {heartbeat.get('total_runs', 'unknown')}")
            except Exception:
                print("  心跳文件: 读取失败")

        # 进程运行时间
        try:
            result = subprocess.run(
                ['ps', '-p', str(pid), '-o', 'etime='],
                capture_output=True, text=True, timeout=5
            )
            if result.stdout.strip():
                print(f"  运行时间: {result.stdout.strip()}")
        except Exception:
            pass
    else:
        print(f"  状态:     未运行 ✗")

    # 数据库日志统计
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM system_maintenance_logs WHERE timestamp > ?",
                          ((datetime.now() - timedelta(hours=24)).strftime('%Y-%m-%d %H:%M:%S'),))
            log_count = cursor.fetchone()[0]
            print(f"  24小时日志: {log_count} 条")

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
    except Exception as e:
        print(f"  日志统计: 读取失败 ({e})")

    print("=" * 60)

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
                    'signal_received', 'stop_cancelled', 'stop_success', 'stop_failed')
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


def show_help():
    """显示帮助"""
    print("""
MTSCOS AI 调度引擎控制脚本
========================

用法:
  python3 scheduler_control.py <命令>

命令:
  start     启动调度引擎
  stop      停止调度引擎（带警告框和原因确认）
  restart   重启调度引擎
  status    查看调度引擎状态
  logs      查看最近操作日志
  help      显示帮助

安全规则:
  - 人工终止时显示警告框，列出所有受影响的任务
  - 需要二次确认才能终止
  - 需要填写终止原因（至少10个字符）
  - 所有操作记录到system_maintenance_logs表
  - 进程保护拦截SIGTERM/SIGINT信号
""")


if __name__ == '__main__':
    import time
    import signal
    from datetime import timedelta

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
    elif cmd == 'help':
        show_help()
    else:
        print(f"未知命令: {cmd}")
        show_help()
        sys.exit(1)
