# -*- coding: utf-8 -*-
#!/usr/bin/env python3
"""
项目启动器和监控工具
监控项目中所有已激活的AI员工、功能状态和用户状态
"""

import logging
logger = logging.getLogger(__name__)
import os
import sys
import time
import threading
import subprocess
from datetime import datetime
from typing import Dict, List, Optional

sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from app.config import Config
from app.ai.instances import ai_instance_manager
from app.ai.ai_ensemble import ai_ensemble
from app.models.user import User
from app.utils.logging import logger


class ProjectMonitor:
    """项目监控器,用于监控AI员工、功能状态和用户状态"""

    def __init__(self):
        self.monitor_interval = 30
        self.running = False
        self.flask_process: Optional[subprocess.Popen] = None
        self.monitor_thread: Optional[threading.Thread] = None

    def start_flask_app(self):
        """启动Flask应用"""
        print("\n" + "="*60)
        print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] 正在启动Flask应用...")
        print("="*60 + "\n")

        cmd = [sys.executable, "-m", "flask", "--app", "app", "run", "--port", "8888", "--debug"]
        self.flask_process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            cwd=os.path.abspath(os.path.dirname(__file__))
        )

        def read_flask_output():
            while self.flask_process and self.flask_process.poll() is None:
                try:
                    line = self.flask_process.stdout.readline()
                    if line:
                        print(line.strip())
                except Exception:
                    break

        output_thread = threading.Thread(target=read_flask_output, daemon=True)
        output_thread.start()

        time.sleep(5)

    def stop_flask_app(self):
        """停止Flask应用"""
        if self.flask_process:
            print("\n" + "="*60)
            print("正在停止Flask应用...")
            print("="*60 + "\n")

            try:
                self.flask_process.terminate()
                self.flask_process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                self.flask_process.kill()
                self.flask_process.wait()

            self.flask_process = None

    def get_ai_instance_status(self):
        """获取AI实例状态"""
        try:
            ai_stats = ai_instance_manager.get_instance_stats()
            all_instances = ai_instance_manager.get_all_instances()
            active_instances = [ai for ai in all_instances if ai.get('status') == 'active']

            ai_type_stats = {}
            for ai in all_instances:
                ai_type = ai.get('type', 'unknown')
                ai_type_stats[ai_type] = ai_type_stats.get(ai_type, 0) + 1

            return {
                'total_instances': ai_stats.get('total_instances', 0),
                'active_instances': ai_stats.get('active_instances', 0),
                'bound_instances': ai_stats.get('bound_instances', 0),
                'instance_types': ai_type_stats,
                'active_instances_list': [{
                    'id': ai.get('id'),
                    'name': ai.get('name'),
                    'type': ai.get('type'),
                    'status': ai.get('status'),
                    'bound_user': ai.get('bound_user'),
                    'created_at': ai.get('created_at')
                } for ai in active_instances]
            }
        except Exception as e:
            logger.error(f"获取AI实例状态失败: {str(e)}")
            return {
                'error': str(e),
                'total_instances': 0,
                'active_instances': 0,
                'bound_instances': 0,
                'active_instances_list': []
            }

    def get_feature_status(self):
        """获取功能状态"""
        try:
            required_ai_types = ai_ensemble.required_ai_types if hasattr(ai_ensemble, 'required_ai_types') else []
            ensemble_stats = ai_ensemble.get_ensemble_stats() if hasattr(ai_ensemble, 'get_ensemble_stats') else {}

            project_features = [
                "AI对话系统",
                "题库管理",
                "用户管理",
                "考试系统",
                "AI脑库"
            ]

            return {
                'project_features': project_features,
                'required_ai_types': required_ai_types,
                'ensemble_stats': ensemble_stats
            }
        except Exception as e:
            return {
                'error': str(e),
                'project_features': [],
                'required_ai_types': [],
                'ensemble_stats': {}
            }

    def get_user_status(self):
        """获取用户状态"""
        try:
            all_users = User.get_all_users() if hasattr(User, 'get_all_users') else []
            role_stats = {}
            active_users = []
            inactive_users = []

            for user in all_users:
                role = user.role if hasattr(user, 'role') else 'unknown'
                role_stats[role] = role_stats.get(role, 0) + 1

                if hasattr(user, 'is_active') and user.is_active == 1:
                    active_users.append(user.username if hasattr(user, 'username') else str(user.id))
                else:
                    inactive_users.append(user.username if hasattr(user, 'username') else str(user.id))

            return {
                'total_users': len(all_users),
                'active_users_count': len(active_users),
                'inactive_users_count': len(inactive_users),
                'role_distribution': role_stats,
                'active_users': active_users,
                'inactive_users': inactive_users
            }
        except Exception as e:
            logger.error(f"获取用户状态失败: {str(e)}")
            return {
                'error': str(e),
                'total_users': 0,
                'active_users_count': 0,
                'inactive_users_count': 0,
                'role_distribution': {},
                'active_users': [],
                'inactive_users': []
            }

    def monitor_loop(self):
        """监控循环"""
        while self.running:
            try:
                print("\n" + "="*60)
                print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] 监控报告")
                print("="*60)

                ai_status = self.get_ai_instance_status()
                print("\n1. AI员工状态:")
                print("-" * 40)
                print(f"  总AI实例数: {ai_status['total_instances']}")
                print(f"  活跃AI实例数: {ai_status['active_instances']}")
                print(f"  已绑定AI实例数: {ai_status['bound_instances']}")
                print(f"  AI类型分布: {str(ai_status['instance_types'])}")
                print(f"  活跃AI实例列表: {str([ai['name'] for ai in ai_status['active_instances_list']])}")

                feature_status = self.get_feature_status()
                print("\n2. 功能状态:")
                print("-" * 40)
                print(f"  项目功能: {str(feature_status['project_features'])}")
                print(f"  所需AI类型: {str(feature_status['required_ai_types'])}")
                print(f"  AI集统计: {str(feature_status['ensemble_stats'])}")

                user_status = self.get_user_status()
                print("\n3. 用户状态:")
                print("-" * 40)
                print(f"  总用户数: {user_status['total_users']}")
                print(f"  活跃用户数: {user_status['active_users_count']}")
                print(f"  非活跃用户数: {user_status['inactive_users_count']}")
                print(f"  角色分布: {str(user_status['role_distribution'])}")
                print(f"  活跃用户: {str(user_status['active_users'])}")

                print("\n" + "="*60)
                print(f"下次监控将在 {self.monitor_interval} 秒后执行")
                print("="*60)
            except Exception as e:
                logger.error(f"监控循环出错: {str(e)}")
                print(f"监控出错: {str(e)}")

            time.sleep(self.monitor_interval)

    def start(self):
        """启动监控器"""
        self.running = True

        self.start_flask_app()

        self.monitor_thread = threading.Thread(target=self.monitor_loop, daemon=True)
        self.monitor_thread.start()

        try:
            while self.running:
                time.sleep(1)
        except KeyboardInterrupt:
            self.stop()

    def stop(self):
        """停止监控器"""
        self.running = False
        self.stop_flask_app()

        if self.monitor_thread:
            self.monitor_thread.join(timeout=5)
            self.monitor_thread = None

        print("\n监控器已停止")


def main():
    """主函数"""
    print("="*60)
    print("MTSCOS AI项目启动器和监控工具")
    print("="*60)
    print("此工具将启动项目并监控所有已激活的AI员工、功能状态和用户状态")
    print("按 Ctrl+C 停止监控和项目")
    print("="*60 + "\n")

    monitor = ProjectMonitor()
    monitor.start()


if __name__ == "__main__":
    main()
