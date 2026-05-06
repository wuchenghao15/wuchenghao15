#!/usr/bin/env python3
"""
项目启动器和监控工具
监控项目中所有已激活的AI员工、功能状态和用户状态

import os
import sys
import time
import threading
import subprocess
# JSON import removed - using database
from datetime import datetime
from typing import Dict, List, Optional

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

# 导入项目模块
from app.config import Config
from app.ai.instances import ai_instance_manager
from app.ai.ai_ensemble import ai_ensemble
from app.models.user import User
from app.utils.logging import logger

class ProjectMonitor:
    """项目监控器，用于监控AI员工、功能状态和用户状态"""

    def __init__(self):
        self.monitor_interval = 30  # 监控间隔（秒）
        self.running = False
        self.flask_process: Optional[subprocess.Popen] = None
        self.monitor_thread: Optional[threading.Thread] = None

    def start_flask_app(self):
        """启动Flask应用"""
        print("\n" + "="*60)
        print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] 正在启动Flask应用...")
        print("="*60 + "\n")

        # 启动Flask应用
        cmd = [sys.executable, "-m", "flask", "--app", "app", "run", "--port", "8888", "--debug"]
        self.flask_process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            cwd=os.path.abspath(os.path.dirname(__file__))
        )

        # 读取并打印Flask输出
        def read_flask_output():
            while self.flask_process and self.flask_process.poll() is None:
                try:
                    line = self.flask_process.stdout.readline()
                    if line:
                        print(line.strip())
                except Exception:
                    break

        # 启动线程读取Flask输出
        output_thread = threading.Thread(target=read_flask_output, daemon=True)
        output_thread.start()

        # 等待Flask应用启动
        time.sleep(5)

    def stop_flask_app(self):
        """停止Flask应用"""
        if self.flask_process:
            print("\n" + "="*60)
            print("="*60 + "\n")

                # 尝试优雅关闭
                self.flask_process.terminate()
                self.flask_process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                # 强制关闭
                self.flask_process.kill()
                self.flask_process.wait()

            self.flask_process = None

    def get_ai_instance_status(self):
        """获取AI实例状态"""
        try:
            # 获取AI实例统计信息
            ai_stats = ai_instance_manager.get_instance_stats()
            # 获取所有AI实例
            all_instances = ai_instance_manager.get_all_instances()
            active_instances = [ai for ai in all_instances if ai.get('status') == 'active']

            # 统计各类型AI实例数量
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
            # 获取项目功能列表
            # 获取所需AI类型
            required_ai_types = ai_ensemble.required_ai_types

            # 获取AI集统计信息
            ensemble_stats = ai_ensemble.get_ensemble_stats()

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
    def get_user_status(self):
        """获取用户状态"""
            # 获取所有用户
            all_users = User.get_all_users()
            # 统计各角色用户数量
            inactive_users = []

            for user in all_users:
                role = user.role
                role_stats[role] = role_stats.get(role, 0) + 1

                if user.is_active == 1:
                    active_users.append(user.username)
                else:
                    inactive_users.append(user.username)

            return {
                'total_users': len(all_users),
                'active_users_count': len(active_users),
                'inactive_users_count': len(inactive_users),
                'role_distribution': role_stats,
                'active_users': active_users,
                'inactive_users': inactive_users
        except Exception as e:
            logger.error(f"获取用户状态失败: {str(e)}")
            return {
                'error': str(e),
                'total_users': 0,
                'active_users_count': 0,
                'inactive_users_count': 0,
                'role_distribution': {},
                'active_users': [],
            }
    def monitor_loop(self):
        """监控循环"""
        while self.running:
            try:
                print("\n" + "="*60)

                # 获取并打印AI实例状态
                print("\n1. AI员工状态:")
                print(f"  总AI实例数: {ai_status['total_instances']}")
                print(f"  活跃AI实例数: {ai_status['active_instances']}")
                print(f"  已绑定AI实例数: {ai_status['bound_instances']}")
                print(f"  AI类型分布: {str(ai_status['instance_types'])}")
                print(f"  活跃AI实例列表: {str([ai['name'] for ai in ai_status['active_instances_list']])}")

                # 获取并打印功能状态
                print("\n2. 功能状态:")
                print("-" * 40)
                feature_status = self.get_feature_status()
                print(f"  项目功能: {str(feature_status['project_features'])}")
                print(f"  所需AI类型: {str(feature_status['required_ai_types'])}")
                print(f"  AI集统计: {str(feature_status['ensemble_stats'])}")

                # 获取并打印用户状态
                print("\n3. 用户状态:")
                print("-" * 40)
                user_status = self.get_user_status()
                print(f"  总用户数: {user_status['total_users']}")
                print(f"  活跃用户数: {user_status['active_users_count']}")
                print(f"  非活跃用户数: {user_status['inactive_users_count']}")
                print(f"  角色分布: {str(user_status['role_distribution'])}")
                print(f"  活跃用户: {str(user_status['active_users'])}")

                # 打印监控结束
                print("\n" + "="*60)
                print("="*60)
            except Exception as e:
                logger.error(f"监控循环出错: {str(e)}")
                print(f"监控出错: {str(e)}")

            time.sleep(self.monitor_interval)

    def start(self):
        """启动监控器"""
        self.running = True

        # 启动Flask应用

        # 启动监控线程
        self.monitor_thread = threading.Thread(target=self.monitor_loop, daemon=True)

        # 保持主程序运行
        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            self.stop()
    def stop(self):
        """停止监控器"""
        self.running = False
        # 停止Flask应用
        self.stop_flask_app()

        # 等待监控线程结束
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

    # 创建并启动监控器
    monitor = ProjectMonitor()
    monitor.start()
if __name__ == "__main__":
    main()
