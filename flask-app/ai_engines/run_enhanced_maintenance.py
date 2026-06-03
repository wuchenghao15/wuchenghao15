# -*- coding: utf-8 -*-
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
例行自动维护系统 - 带数据库上报和实时显示
Enhanced Routine Maintenance with Database Reporting and Real-time Display
"""

import sys
import os
import time
import json
import logging
from datetime import datetime
from typing import Dict, List, Any

sys.path.insert(0, os.path.join(os.path.dirname(__file__)))

from app.ai.auto_routine_maintenance import (
    auto_routine_maintenance_system,
    TaskType
)

try:
    from app.ai.system_integration import (
        system_integration_hub,
        enhanced_db_reporter,
        ReportPriority
    )
    DB_REPORTING_ENABLED = True
except ImportError:
    DB_REPORTING_ENABLED = False
    print("⚠️  数据库上报模块未加载,使用模拟模式")

logger = logging.getLogger('enhanced_maintenance')


class EnhancedMaintenanceDisplay:
    """增强型维护显示"""

    COLORS = {
        'header': '\033[95m',
        'success': '\033[92m',
        'warning': '\033[93m',
        'error': '\033[91m',
        'info': '\033[96m',
        'bold': '\033[1m',
        'end': '\033[0m'
    }

    @staticmethod
    def print_header(title: str, subtitle: str = ""):
        """打印标题"""
        print("\n" + "=" * 80)
        print(f"{EnhancedMaintenanceDisplay.COLORS['bold']}{EnhancedMaintenanceDisplay.COLORS['header']}"
              f"  🚀 {title} 🚀{EnhancedMaintenanceDisplay.COLORS['end']}")
        if subtitle:
            print(f"{EnhancedMaintenanceDisplay.COLORS['info']}  {subtitle}{EnhancedMaintenanceDisplay.COLORS['end']}")
        print("=" * 80)

    @staticmethod
    def print_section(title: str):
        """打印分节标题"""
        print(f"\n{EnhancedMaintenanceDisplay.COLORS['bold']}{'─' * 80}{EnhancedMaintenanceDisplay.COLORS['end']}")
        print(f"{EnhancedMaintenanceDisplay.COLORS['header']}📋 {title}{EnhancedMaintenanceDisplay.COLORS['end']}")
        print(f"{EnhancedMaintenanceDisplay.COLORS['bold']}{'─' * 80}{EnhancedMaintenanceDisplay.COLORS['end']}")

    @staticmethod
    def print_task_start(task_name: str, task_type: str):
        """打印任务开始"""
        print(f"\n{EnhancedMaintenanceDisplay.COLORS['info']}▶ 开始任务: "
              f"{EnhancedMaintenanceDisplay.COLORS['bold']}{task_name}"
              f"{EnhancedMaintenanceDisplay.COLORS['end']} "
              f"({EnhancedMaintenanceDisplay.COLORS['warning']}{task_type}"
              f"{EnhancedMaintenanceDisplay.COLORS['end']})")

    @staticmethod
    def print_task_complete(task_name: str, duration: float, status: str):
        """打印任务完成"""
        if status == 'completed':
            status_text = f"{EnhancedMaintenanceDisplay.COLORS['success']}✓ 成功"
        elif status == 'failed':
            status_text = f"{EnhancedMaintenanceDisplay.COLORS['error']}✗ 失败"
        else:
            status_text = f"{EnhancedMaintenanceDisplay.COLORS['warning']}⚠ {status}"

        print(f"{status_text}{EnhancedMaintenanceDisplay.COLORS['end']} "
              f"({EnhancedMaintenanceDisplay.COLORS['info']}耗时: {duration:.2f}秒"
              f"{EnhancedMaintenanceDisplay.COLORS['end']})")

    @staticmethod
    def print_metric(label: str, value: Any, unit: str = ""):
        """打印指标"""
        print(f"  {EnhancedMaintenanceDisplay.COLORS['info']}•{EnhancedMaintenanceDisplay.COLORS['end']} "
              f"{label}: {EnhancedMaintenanceDisplay.COLORS['bold']}{value}"
              f"{EnhancedMaintenanceDisplay.COLORS['end']} {unit}")

    @staticmethod
    def print_status(label: str, value: str, status_type: str = "info"):
        """打印状态"""
        if status_type == "success":
            color = EnhancedMaintenanceDisplay.COLORS['success']
            icon = "✓"
        elif status_type == "error":
            color = EnhancedMaintenanceDisplay.COLORS['error']
            icon = "✗"
        elif status_type == "warning":
            color = EnhancedMaintenanceDisplay.COLORS['warning']
            icon = "⚠"
        else:
            color = EnhancedMaintenanceDisplay.COLORS['info']
            icon = "•"

        print(f"  {color}{icon}{EnhancedMaintenanceDisplay.COLORS['end']} "
              f"{label}: {color}{value}{EnhancedMaintenanceDisplay.COLORS['end']}")

    @staticmethod
    def print_progress(current: int, total: int, task_name: str = ""):
        """打印进度"""
        percentage = (current / total) * 100 if total > 0 else 0
        bar_length = 40
        filled = int(bar_length * current / total) if total > 0 else 0
        bar = '█' * filled + '░' * (bar_length - filled)

        print(f"\r{EnhancedMaintenanceDisplay.COLORS['info']}[{bar}] "
              f"{percentage:5.1f}% ({current}/{total}){EnhancedMaintenanceDisplay.COLORS['end']} "
              f"{task_name}", end='', flush=True)


class DatabaseReporter:
    """数据库上报器(本地实现)"""

    def __init__(self):
        self.reports = []
        self.maintenance_records = []
        self.task_execution_records = []

    def report_maintenance_start(self, maintenance_type: str, tasks_count: int):
        """上报维护开始"""
        record = {
            'type': 'maintenance_start',
            'maintenance_type': maintenance_type,
            'tasks_count': tasks_count,
            'timestamp': datetime.now().isoformat(),
            'status': 'started'
        }
        self.reports.append(record)
        self.maintenance_records.append(record)

    def report_maintenance_complete(self, maintenance_type: str, result: Dict):
        """上报维护完成"""
        record = {
            'type': 'maintenance_complete',
            'maintenance_type': maintenance_type,
            'tasks_executed': result.get('tasks_executed', 0),
            'tasks_succeeded': result.get('tasks_succeeded', 0),
            'tasks_failed': result.get('tasks_failed', 0),
            'duration': result.get('duration', 0),
            'timestamp': datetime.now().isoformat(),
            'status': 'completed'
        }
        self.reports.append(record)
        self.maintenance_records.append(record)

    def report_task_execution(self, task_name: str, task_type: str, status: str,
                             duration: float, result: Dict = None):
        """上报任务执行"""
        record = {
            'type': 'task_execution',
            'task_name': task_name,
            'task_type': task_type,
            'status': status,
            'duration': duration,
            'result': result or {},
            'timestamp': datetime.now().isoformat()
        }
        self.reports.append(record)
        self.task_execution_records.append(record)

    def report_system_health(self, health_data: Dict):
        """上报系统健康"""
        record = {
            'type': 'system_health',
            'health_score': health_data.get('overall_score', 0),
            'status': health_data.get('status', 'unknown'),
            'checks_passed': health_data.get('checks_passed', 0),
            'checks_failed': health_data.get('checks_failed', 0),
            'timestamp': datetime.now().isoformat()
        }
        self.reports.append(record)

    def report_upgrade_check(self, upgrade_info: Dict):
        """上报升级检查"""
        record = {
            'type': 'upgrade_check',
            'current_version': upgrade_info.get('current_version'),
            'available_version': upgrade_info.get('available_version'),
            'upgrade_available': upgrade_info.get('upgrade_available', False),
            'changes': upgrade_info.get('changes', []),
            'timestamp': datetime.now().isoformat()
        }
        self.reports.append(record)

    def get_reports(self) -> List[Dict]:
        """获取所有报表"""
        return self.reports

    def get_maintenance_summary(self) -> Dict:
        """获取维护汇总"""
        return {
            'total_maintenance': len(self.maintenance_records),
            'maintenance_by_type': self._count_by_type(),
            'task_executions': len(self.task_execution_records),
            'reports_count': len(self.reports)
        }

    def _count_by_type(self) -> Dict:
        """按类型统计"""
        counts = {}
        for record in self.maintenance_records:
            mtype = record.get('maintenance_type', 'unknown')
            counts[mtype] = counts.get(mtype, 0) + 1
        return counts


class EnhancedRoutineMaintenance:
    """增强型例行自动维护系统"""

    def __init__(self):
        self.display = EnhancedMaintenanceDisplay()
        self.db_reporter = DatabaseReporter() if not DB_REPORTING_ENABLED else None
        self.start_time = None
        self.results = []

    def execute_full_maintenance(self) -> Dict:
        """执行完整维护"""
        self.start_time = time.time()

        # 打印标题
        self.display.print_header(
            "例行自动维护系统",
            f"开始时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
        )

        # 1. 执行日维护
        daily_result = self._execute_daily_maintenance()

        # 2. 执行周维护
        weekly_result = self._execute_weekly_maintenance()

        # 3. 执行月维护
        monthly_result = self._execute_monthly_maintenance()

        # 4. 系统健康检查
        health_result = self._execute_health_check()

        # 5. 升级检查
        upgrade_result = self._execute_upgrade_check()

        # 6. 系统资源检查
        resource_result = self._execute_system_check()

        # 7. 显示汇总
        summary = self._display_summary(
            daily_result, weekly_result, monthly_result,
            health_result, upgrade_result, resource_result
        )

        # 8. 上报数据库
        self._report_to_database(
            daily_result, weekly_result, monthly_result,
            health_result, upgrade_result
        )

        return summary

    def _execute_daily_maintenance(self) -> Dict:
        """执行日维护"""
        self.display.print_section("📅 日维护窗口 (Daily Maintenance)")

        # 上报开始
        if self.db_reporter:
            self.db_reporter.report_maintenance_start('daily', 4)

        # 上报系统
        if DB_REPORTING_ENABLED:
            enhanced_db_reporter.report_data_point(
                'maintenance_window',
                {'window': 'daily', 'phase': 'start'},
                ReportPriority.HIGH
            )

        start_time = time.time()
        result = auto_routine_maintenance_system.execute_maintenance_window('daily')
        duration = time.time() - start_time

        result['duration'] = duration

        # 显示结果
        self.display.print_status(f"执行任务", f"{result.get('tasks_executed', 0)}", "info")
        self.display.print_status(f"成功", f"{result.get('tasks_succeeded', 0)}", "success")
        self.display.print_status(f"失败", f"{result.get('tasks_failed', 0)}", "error" if result.get('tasks_failed', 0) > 0 else "success")
        self.display.print_status(f"耗时", f"{duration:.2f}秒", "info")

        # 上报完成
        if self.db_reporter:
            self.db_reporter.report_maintenance_complete('daily', result)

        if DB_REPORTING_ENABLED:
            enhanced_db_reporter.report_data_point(
                'maintenance_window',
                {
                    'window': 'daily',
                    'phase': 'complete',
                    'tasks_executed': result.get('tasks_executed', 0),
                    'tasks_succeeded': result.get('tasks_succeeded', 0),
                    'duration': duration
                },
                ReportPriority.HIGH
            )

        # 显示任务详情
        if result.get('task_results'):
            print(f"\n{self.display.COLORS['info']}任务详情:{self.display.COLORS['end']}")
            for task_result in result.get('task_results', []):
                status_icon = "✓" if task_result.get('status') == 'completed' else "✗"
                status_color = "success" if task_result.get('status') == 'completed' else "error"
                self.display.print_status(task_result.get('name', 'Unknown'), status_icon, status_color)

        return result

    def _execute_weekly_maintenance(self) -> Dict:
        """执行周维护"""
        self.display.print_section("📆 周维护窗口 (Weekly Maintenance)")

        if self.db_reporter:
            self.db_reporter.report_maintenance_start('weekly', 3)

        if DB_REPORTING_ENABLED:
            enhanced_db_reporter.report_data_point(
                'maintenance_window',
                {'window': 'weekly', 'phase': 'start'},
                ReportPriority.HIGH
            )

        start_time = time.time()
        result = auto_routine_maintenance_system.execute_maintenance_window('weekly')
        duration = time.time() - start_time

        result['duration'] = duration

        self.display.print_status(f"执行任务", f"{result.get('tasks_executed', 0)}", "info")
        self.display.print_status(f"成功", f"{result.get('tasks_succeeded', 0)}", "success")
        self.display.print_status(f"失败", f"{result.get('tasks_failed', 0)}", "error" if result.get('tasks_failed', 0) > 0 else "success")
        self.display.print_status(f"耗时", f"{duration:.2f}秒", "info")

        if self.db_reporter:
            self.db_reporter.report_maintenance_complete('weekly', result)

        if DB_REPORTING_ENABLED:
            enhanced_db_reporter.report_data_point(
                'maintenance_window',
                {
                    'window': 'weekly',
                    'phase': 'complete',
                    'tasks_executed': result.get('tasks_executed', 0),
                    'tasks_succeeded': result.get('tasks_succeeded', 0),
                    'duration': duration
                },
                ReportPriority.HIGH
            )

        if result.get('task_results'):
            print(f"\n{self.display.COLORS['info']}任务详情:{self.display.COLORS['end']}")
            for task_result in result.get('task_results', []):
                status_icon = "✓" if task_result.get('status') == 'completed' else "✗"
                status_color = "success" if task_result.get('status') == 'completed' else "error"
                self.display.print_status(task_result.get('name', 'Unknown'), status_icon, status_color)

        return result

    def _execute_monthly_maintenance(self) -> Dict:
        """执行月维护"""
        self.display.print_section("📅 月维护窗口 (Monthly Maintenance)")

        if self.db_reporter:
            self.db_reporter.report_maintenance_start('monthly', 3)

        if DB_REPORTING_ENABLED:
            enhanced_db_reporter.report_data_point(
                'maintenance_window',
                {'window': 'monthly', 'phase': 'start'},
                ReportPriority.HIGH
            )

        start_time = time.time()
        result = auto_routine_maintenance_system.execute_maintenance_window('monthly')
        duration = time.time() - start_time

        result['duration'] = duration

        self.display.print_status(f"执行任务", f"{result.get('tasks_executed', 0)}", "info")
        self.display.print_status(f"成功", f"{result.get('tasks_succeeded', 0)}", "success")
        self.display.print_status(f"失败", f"{result.get('tasks_failed', 0)}", "error" if result.get('tasks_failed', 0) > 0 else "success")
        self.display.print_status(f"耗时", f"{duration:.2f}秒", "info")

        if self.db_reporter:
            self.db_reporter.report_maintenance_complete('monthly', result)

        if DB_REPORTING_ENABLED:
            enhanced_db_reporter.report_data_point(
                'maintenance_window',
                {
                    'window': 'monthly',
                    'phase': 'complete',
                    'tasks_executed': result.get('tasks_executed', 0),
                    'tasks_succeeded': result.get('tasks_succeeded', 0),
                    'duration': duration
                },
                ReportPriority.HIGH
            )

        if result.get('task_results'):
            print(f"\n{self.display.COLORS['info']}任务详情:{self.display.COLORS['end']}")
            for task_result in result.get('task_results', []):
                status_icon = "✓" if task_result.get('status') == 'completed' else "✗"
                status_color = "success" if task_result.get('status') == 'completed' else "error"
                self.display.print_status(task_result.get('name', 'Unknown'), status_icon, status_color)

        return result

    def _execute_health_check(self) -> Dict:
        """执行健康检查"""
        self.display.print_section("🏥 系统健康检查 (Health Check)")

        health_task = auto_routine_maintenance_system.scheduler.schedule_task(
            task_type=TaskType.HEALTH_CHECK,
            name='综合健康检查'
        )
        auto_routine_maintenance_system.scheduler.execute_task(health_task.id)
        time.sleep(2)

        status = auto_routine_maintenance_system.scheduler.get_task_status(health_task.id)
        result_data = status.get('result', {}) if status else {}

        self.display.print_status(f"健康评分", f"{result_data.get('overall_score', 0)}/100", "success")
        self.display.print_status(f"状态", f"{result_data.get('status', 'unknown')}", "success")
        self.display.print_status(f"通过检查", f"{result_data.get('checks_passed', 0)}", "success")
        self.display.print_status(f"失败检查", f"{result_data.get('checks_failed', 0)}", "error" if result_data.get('checks_failed', 0) > 0 else "success")

        if result_data.get('components'):
            print(f"\n{self.display.COLORS['info']}组件状态:{self.display.COLORS['end']}")
            for component, state in result_data.get('components', {}).items():
                status_icon = "✓" if state == 'healthy' else "⚠"
                status_color = "success" if state == 'healthy' else "warning"
                self.display.print_status(component, status_icon, status_color)

        if self.db_reporter:
            self.db_reporter.report_system_health(result_data)

        if DB_REPORTING_ENABLED:
            enhanced_db_reporter.report_health_analysis({
                'health_score': result_data.get('overall_score', 0),
                'status': result_data.get('status', 'unknown'),
                'issues': [],
                'recommendations': [],
                'analysis_time': datetime.now().isoformat()
            })

        return result_data

    def _execute_upgrade_check(self) -> Dict:
        """执行升级检查"""
        self.display.print_section("🔄 系统升级检查 (Upgrade Check)")

        upgrade_info = auto_routine_maintenance_system.check_and_perform_upgrades()

        self.display.print_status(f"当前版本", upgrade_info.get('current_version', 'unknown'), "info")
        self.display.print_status(f"可用版本", upgrade_info.get('available_version') or '无', "info")
        self.display.print_status(f"升级可用", "是" if upgrade_info.get('upgrade_available') else "否", "success")

        if upgrade_info.get('changes'):
            print(f"\n{self.display.COLORS['info']}变更内容:{self.display.COLORS['end']}")
            for change in upgrade_info.get('changes', []):
                print(f"  {self.display.COLORS['success']}•{self.display.COLORS['end']} {change}")

        if self.db_reporter:
            self.db_reporter.report_upgrade_check(upgrade_info)

        if DB_REPORTING_ENABLED:
            enhanced_db_reporter.report_data_point(
                'upgrade_check',
                {
                    'current_version': upgrade_info.get('current_version'),
                    'available_version': upgrade_info.get('available_version'),
                    'upgrade_available': upgrade_info.get('upgrade_available', False),
                    'changes': upgrade_info.get('changes', [])
                },
                ReportPriority.NORMAL
            )

        return upgrade_info

    def _execute_system_check(self) -> Dict:
        """执行系统资源检查"""
        self.display.print_section("💻 系统资源检查 (System Resources)")

        import psutil

        cpu_percent = psutil.cpu_percent()
        memory = psutil.virtual_memory()
        disk = psutil.disk_usage('/')

        self.display.print_metric("CPU使用率", f"{cpu_percent}%", "")
        self.display.print_metric("内存使用率", f"{memory.percent}%", f"(可用: {memory.available / (1024**3):.2f} GB)")
        self.display.print_metric("磁盘使用率", f"{disk.percent}%", f"(可用: {disk.free / (1024**3):.2f} GB)")

        if DB_REPORTING_ENABLED:
            enhanced_db_reporter.report_system_metrics({
                'cpu_percent': cpu_percent,
                'memory_percent': memory.percent,
                'disk_percent': disk.percent
            })

        return {
            'cpu_percent': cpu_percent,
            'memory_percent': memory.percent,
            'disk_percent': disk.percent
        }

    def _display_summary(self, daily, weekly, monthly, health, upgrade, resources) -> Dict:
        """显示汇总"""
        self.display.print_section("📊 维护汇总报告 (Summary Report)")

        total_tasks = (
            daily.get('tasks_executed', 0) +
            weekly.get('tasks_executed', 0) +
            monthly.get('tasks_executed', 0)
        )

        total_success = (
            daily.get('tasks_succeeded', 0) +
            weekly.get('tasks_succeeded', 0) +
            monthly.get('tasks_succeeded', 0)
        )

        total_failed = (
            daily.get('tasks_failed', 0) +
            weekly.get('tasks_failed', 0) +
            monthly.get('tasks_failed', 0)
        )

        total_duration = (
            daily.get('duration', 0) +
            weekly.get('duration', 0) +
            monthly.get('duration', 0)
        )

        self.display.print_status("执行时间", datetime.now().strftime('%Y-%m-%d %H:%M:%S'), "info")
        self.display.print_status("总任务数", total_tasks, "info")
        self.display.print_status("成功任务", total_success, "success")
        self.display.print_status("失败任务", total_failed, "error" if total_failed > 0 else "success")
        self.display.print_status("总耗时", f"{total_duration:.2f}秒", "info")
        self.display.print_status("成功率", f"{(total_success/total_tasks*100) if total_tasks > 0 else 0:.1f}%", "success")

        print(f"\n{self.display.COLORS['bold']}{self.display.COLORS['success']}"
              f"🎉 维护完成!系统已优化并准备就绪!"
              f"{self.display.COLORS['end']}")

        return {
            'total_tasks': total_tasks,
            'total_success': total_success,
            'total_failed': total_failed,
            'total_duration': total_duration,
            'health_score': health.get('overall_score', 0),
            'current_version': upgrade.get('current_version')
        }

    def _report_to_database(self, daily, weekly, monthly, health, upgrade):
        """上报数据库"""
        if not DB_REPORTING_ENABLED and not self.db_reporter:
            print(f"\n{self.display.COLORS['warning']}⚠️  数据库上报功能未启用{self.display.COLORS['end']}")
            return

        print(f"\n{self.display.COLORS['info']}📤 正在上报数据到数据库...{self.display.COLORS['end']}")

        if self.db_reporter:
            summary = self.db_reporter.get_maintenance_summary()
            print(f"{self.display.COLORS['success']}✓ 已上报 {summary.get('reports_count', 0)} 条记录到本地数据库{self.display.COLORS['end']}")

        if DB_REPORTING_ENABLED:
            print(f"{self.display.COLORS['success']}✓ 已上报到系统数据库{self.display.COLORS['end']}")

            try:
                enhanced_db_reporter.flush_all()
                print(f"{self.display.COLORS['success']}✓ 数据刷新完成{self.display.COLORS['end']}")
            except Exception as e:
                print(f"{self.display.COLORS['error']}✗ 数据刷新失败: {str(e)}{self.display.COLORS['end']}")


def main():
    """主函数"""
    maintenance = EnhancedRoutineMaintenance()

    try:
        summary = maintenance.execute_full_maintenance()

        print("\n" + "=" * 80)
        print(f"{maintenance.display.COLORS['bold']}✅ 例行自动维护完成!{maintenance.display.COLORS['end']}")
        print("=" * 80)

        return 0

    except KeyboardInterrupt:
        print(f"\n{maintenance.display.COLORS['warning']}⚠️  用户中断维护{maintenance.display.COLORS['end']}")
        return 1
    except Exception as e:
        print(f"\n{maintenance.display.COLORS['error']}✗ 维护执行失败: {str(e)}{maintenance.display.COLORS['end']}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
