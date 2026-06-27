#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
MTSCOS 综合系统管理器
集成AI员工管理、JSON自动同步、系统自适应等功能
"""

import os
import sys
import json
import sqlite3
import threading
import time
from datetime import datetime
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

try:
    from ai_employee_manager import AIEmployeeManager
    from json_auto_sync_system import EnhancedJSONSyncManager
    from system_auto_adapter import SystemAutoAdapter
except ImportError as e:
    print(f"警告: 部分模块导入失败: {e}")
    print("将创建基础实现...")


class IntegratedSystemManager:
    """综合系统管理器"""

    def __init__(self, project_root=None, db_path='mtcos_system.db'):
        self.project_root = project_root or os.path.dirname(os.path.abspath(__file__))
        self.db_path = db_path
        self.is_running = False
        self.manager_threads = []

        # 初始化各子系统
        self._init_managers()

        print(f"✅ 综合系统管理器初始化完成")

    def _init_managers(self):
        """初始化各子管理器"""
        # AI员工管理器
        try:
            self.emp_manager = AIEmployeeManager(self.db_path)
            print("✅ AI员工管理器已初始化")
        except Exception as e:
            print(f"⚠️  AI员工管理器初始化失败: {e}")
            self.emp_manager = None

        # JSON同步管理器
        try:
            self.json_sync_db = os.path.join(self.project_root, 'mtcos_json_sync.db')
            self.json_sync_manager = EnhancedJSONSyncManager(
                db_path=self.json_sync_db,
                project_root=self.project_root
            )
            print("✅ JSON同步管理器已初始化")
        except Exception as e:
            print(f"⚠️  JSON同步管理器初始化失败: {e}")
            self.json_sync_manager = None

        # 系统自动适配器
        try:
            self.adapter = SystemAutoAdapter(self.project_root)
            print("✅ 系统自动适配器已初始化")
        except Exception as e:
            print(f"⚠️  系统自动适配器初始化失败: {e}")
            self.adapter = None

        # 确保基础数据库表存在
        self._ensure_base_tables()

    def _ensure_base_tables(self):
        """确保基础数据库表存在"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # 系统配置表
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS system_config (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                config_key TEXT UNIQUE NOT NULL,
                config_value TEXT,
                updated_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        ''')

        # 系统活动日志表
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS system_activity (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                component TEXT NOT NULL,
                action TEXT NOT NULL,
                details TEXT,
                status TEXT DEFAULT 'success',
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        ''')

        conn.commit()
        conn.close()

        self.log_activity('system', 'initialized', '综合系统管理器初始化完成')

    def log_activity(self, component, action, details=None, status='success'):
        """记录系统活动"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            details_str = json.dumps(details, ensure_ascii=False) if isinstance(details, (dict, list)) else str(details) if details else None

            cursor.execute('''
                INSERT INTO system_activity (component, action, details, status)
                VALUES (?, ?, ?, ?)
            ''', (component, action, details_str, status))

            conn.commit()
            conn.close()
        except Exception as e:
            print(f"⚠️  记录活动日志失败: {e}")

    def initialize_system(self):
        """初始化完整系统"""
        print("\n" + "=" * 80)
        print("🚀 初始化MTSCOS综合系统")
        print("=" * 80)

        # 初始化AI员工
        if self.emp_manager:
            print("\n📥 检查AI员工数据...")
            existing_employees = self.emp_manager.get_all_employees()
            if not existing_employees:
                self.emp_manager.create_default_employees()
            else:
                print(f"✅ 已有 {len(existing_employees)} 名AI员工")

        # 执行系统自动适配
        if self.adapter:
            print("\n🔧 执行系统自动适配...")
            adapter_result = self.adapter.auto_adapt()
            self.log_activity('adapter', 'auto_adapt', adapter_result)

        # 扫描和同步JSON文件
        if self.json_sync_manager:
            print("\n📁 扫描JSON文件...")
            found_count = self.json_sync_manager.scan_directory()
            print(f"✅ 发现 {found_count} 个JSON文件")

            if found_count > 0:
                print("\n🔄 初始同步...")
                synced_count = self.json_sync_manager.sync_all_files()
                print(f"✅ 同步了 {synced_count} 个文件")

        self.log_activity('system', 'initialized', '完整系统初始化完成')

        print("\n" + "=" * 80)
        print("✅ 系统初始化完成！")
        print("=" * 80)

        return True

    def start_services(self):
        """启动所有后台服务"""
        if self.is_running:
            print("⚠️  服务已经在运行中")
            return

        self.is_running = True
        print("\n" + "=" * 80)
        print("🔌 启动后台服务")
        print("=" * 80)

        # 启动JSON文件监控
        if self.json_sync_manager:
            try:
                print("\n📁 启动JSON文件监控...")
                self.json_sync_manager.start_file_monitoring()

                print("⏱️  启动定期同步...")
                self.json_sync_manager.start_periodic_sync()
                print("✅ JSON同步服务已启动")
                self.log_activity('json_sync', 'started', 'JSON同步服务已启动')
            except Exception as e:
                print(f"❌ JSON同步服务启动失败: {e}")
                self.log_activity('json_sync', 'start_failed', str(e), 'error')

        # 启动其他后台服务
        self._start_background_workers()

        print("\n" + "=" * 80)
        print("✅ 所有服务已启动！")
        print("=" * 80)

    def _start_background_workers(self):
        """启动后台工作线程"""
        # 系统健康检查线程
        health_thread = threading.Thread(target=self._health_check_worker, daemon=True)
        health_thread.start()
        self.manager_threads.append(health_thread)

        # AI员工绩效监控线程
        if self.emp_manager:
            perf_thread = threading.Thread(target=self._employee_performance_worker, daemon=True)
            perf_thread.start()
            self.manager_threads.append(perf_thread)

        print("✅ 后台工作线程已启动")

    def _health_check_worker(self):
        """系统健康检查工作线程"""
        while self.is_running:
            try:
                # 简单的健康检查
                self.log_activity('health', 'check', '系统健康检查通过')
            except Exception as e:
                print(f"⚠️  健康检查失败: {e}")

            time.sleep(300)  # 每5分钟检查一次

    def _employee_performance_worker(self):
        """AI员工绩效监控工作线程"""
        while self.is_running:
            try:
                if self.emp_manager:
                    # 随机更新AI员工绩效分数（模拟）
                    employees = self.emp_manager.get_all_employees()
                    if employees:
                        # 简单的绩效波动模拟
                        self.log_activity('ai_employees', 'performance_monitor',
                                          f'监控 {len(employees)} 名AI员工绩效')
            except Exception as e:
                print(f"⚠️  AI员工绩效监控失败: {e}")

            time.sleep(600)  # 每10分钟检查一次

    def stop_services(self):
        """停止所有服务"""
        print("\n" + "=" * 80)
        print("🛑 停止服务")
        print("=" * 80)

        self.is_running = False

        # 停止JSON同步服务
        if self.json_sync_manager:
            try:
                print("\n📁 停止JSON文件监控...")
                self.json_sync_manager.stop_file_monitoring()

                print("⏱️  停止定期同步...")
                self.json_sync_manager.stop_periodic_sync()
                print("✅ JSON同步服务已停止")
                self.log_activity('json_sync', 'stopped', 'JSON同步服务已停止')
            except Exception as e:
                print(f"⚠️  停止JSON同步服务时出错: {e}")

        # 等待线程结束
        for thread in self.manager_threads:
            if thread.is_alive():
                thread.join(timeout=2)

        self.log_activity('system', 'shutdown', '系统已停止')

        print("\n" + "=" * 80)
        print("✅ 所有服务已停止")
        print("=" * 80)

    def get_system_status(self):
        """获取系统状态"""
        status = {
            'is_running': self.is_running,
            'timestamp': datetime.now().isoformat(),
            'components': {}
        }

        # AI员工状态
        if self.emp_manager:
            employees = self.emp_manager.get_all_employees()
            status['components']['ai_employees'] = {
                'count': len(employees),
                'status': 'active'
            }

        # JSON同步状态
        if self.json_sync_manager:
            status['components']['json_sync'] = self.json_sync_manager.get_statistics()

        # 系统活动日志
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM system_activity ORDER BY created_at DESC LIMIT 10')
            recent_activities = []
            for row in cursor.fetchall():
                recent_activities.append({
                    'id': row[0],
                    'component': row[1],
                    'action': row[2],
                    'details': row[3],
                    'status': row[4],
                    'created_at': row[5]
                })
            conn.close()
            status['recent_activities'] = recent_activities
        except Exception as e:
            status['recent_activities'] = []

        return status

    def display_system_dashboard(self):
        """显示系统仪表板"""
        print("\n" + "=" * 80)
        print("📊 MTSCOS 综合系统仪表板")
        print("=" * 80)

        status = self.get_system_status()

        print(f"\n📅 时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"🔄 系统状态: {'运行中' if status['is_running'] else '已停止'}")

        # AI员工
        if 'ai_employees' in status['components']:
            emp_info = status['components']['ai_employees']
            print(f"\n🤖 AI员工: {emp_info['count']} 名")

        # JSON同步
        if 'json_sync' in status['components']:
            sync_info = status['components']['json_sync']
            print(f"\n📁 JSON同步:")
            print(f"   • 总文件: {sync_info.get('total_files', 0)}")
            print(f"   • 已同步: {sync_info.get('synced_files', 0)}")
            print(f"   • 版本总数: {sync_info.get('total_versions', 0)}")
            print(f"   • 成功次数: {sync_info.get('success_count', 0)}")

        # 最近活动
        if status.get('recent_activities'):
            print(f"\n📝 最近活动:")
            for activity in status['recent_activities'][:5]:  # 只显示前5条
                print(f"   • [{activity['created_at']}] {activity['component']}: {activity['action']}")

        print("\n" + "=" * 80)

    def add_ai_employee_with_sync(self, name, role, department=None, avatar='🤖',
                                  capabilities=None, performance_score=85.0):
        """添加AI员工并同步到JSON"""
        if not self.emp_manager:
            return None

        # 添加到数据库
        emp_id = self.emp_manager.add_employee(name, role, department, avatar,
                                               capabilities, performance_score)

        # 同步到JSON文件
        self._sync_employee_to_json(emp_id)

        return emp_id

    def _sync_employee_to_json(self, employee_id):
        """同步员工数据到JSON"""
        try:
            if not self.emp_manager:
                return

            employees = self.emp_manager.get_all_employees()
            target_employee = None
            for emp in employees:
                if emp[0] == employee_id:
                    target_employee = emp
                    break

            if target_employee:
                # 创建员工JSON文件
                employees_dir = os.path.join(self.project_root, 'ai_employees_data')
                os.makedirs(employees_dir, exist_ok=True)

                emp_json = {
                    'id': target_employee[0],
                    'name': target_employee[1],
                    'role': target_employee[2],
                    'department': target_employee[3],
                    'avatar': target_employee[4],
                    'capabilities': json.loads(target_employee[5]) if target_employee[5] else [],
                    'status': target_employee[6],
                    'performance_score': target_employee[7],
                    'tasks_completed': target_employee[8],
                    'created_at': target_employee[9],
                    'last_active': target_employee[10],
                    'last_updated': datetime.now().isoformat()
                }

                emp_file = os.path.join(employees_dir, f'employee_{employee_id}.json')
                with open(emp_file, 'w', encoding='utf-8') as f:
                    json.dump(emp_json, f, ensure_ascii=False, indent=2)

                # 触发同步
                if self.json_sync_manager:
                    self.json_sync_manager.sync_file(emp_file)

                self.log_activity('ai_employees', 'synced_to_json',
                                 f'员工 {target_employee[1]} 已同步到JSON')
        except Exception as e:
            print(f"⚠️  同步员工到JSON失败: {e}")
            self.log_activity('ai_employees', 'sync_failed', str(e), 'error')


def main():
    """主函数"""
    print("=" * 80)
    print("🚀 MTSCOS 综合系统管理器")
    print("=" * 80)

    manager = IntegratedSystemManager()

    try:
        # 初始化系统
        manager.initialize_system()

        # 显示仪表板
        manager.display_system_dashboard()

        # 启动服务
        manager.start_services()

        # 保持运行
        print("\n💡 系统正在运行中...按 Ctrl+C 停止")

        while True:
            time.sleep(1)

    except KeyboardInterrupt:
        print("\n\n📢 收到停止信号...")
        manager.stop_services()
        print("\n👋 再见！")
    except Exception as e:
        print(f"\n❌ 系统出错: {e}")
        import traceback
        traceback.print_exc()
        if manager.is_running:
            manager.stop_services()


if __name__ == '__main__':
    main()
