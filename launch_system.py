#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
MTSCOS 完整系统启动器
一键启动所有服务并自动配置
"""

import os
import sys
import subprocess
import threading
import time
import signal
from datetime import datetime


class SystemLauncher:
    """系统启动器"""

    def __init__(self):
        self.project_root = os.path.dirname(os.path.abspath(__file__))
        self.processes = []
        self.running = False

        # 更改工作目录
        os.chdir(self.project_root)

    def print_banner(self):
        """打印横幅"""
        print("=" * 80)
        print("🚀 MTSCOS AI Project - 完整系统启动器")
        print("=" * 80)
        print(f"启动时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"工作目录: {self.project_root}")
        print("=" * 80)

    def check_dependencies(self):
        """检查依赖"""
        print("\n📦 检查依赖...")

        dependencies = {
            'flask': 'Flask',
            'watchdog': 'Watchdog',
            'flask_cors': 'Flask-CORS'
        }

        for module, name in dependencies.items():
            try:
                __import__(module)
                print(f"  ✅ {name}")
            except ImportError:
                print(f"  ⚠️ {name} 未安装，尝试安装...")
                try:
                    subprocess.check_call([sys.executable, '-m', 'pip', 'install', module.replace('_', '-')])
                    print(f"  ✅ {name} 安装成功")
                except Exception as e:
                    print(f"  ❌ {name} 安装失败: {e}")

    def initialize_system(self):
        """初始化系统"""
        print("\n🔧 初始化系统...")

        try:
            # 先尝试初始化AI员工管理器
            from ai_employee_manager import AIEmployeeManager
            emp_manager = AIEmployeeManager()
            employees = emp_manager.get_all_employees()
            if not employees:
                print("  📥 创建默认AI员工...")
                emp_manager.create_default_employees()
                print("  ✅ 默认AI员工创建完成")
            else:
                print(f"  ✅ 已存在 {len(employees)} 名AI员工")

        except Exception as e:
            print(f"  ⚠️ AI员工初始化失败: {e}")

        print("  ✅ 系统初始化完成")

    def start_background_process(self, target, name, args=()):
        """启动后台进程"""
        thread = threading.Thread(target=target, args=args, name=name, daemon=True)
        thread.start()
        return thread

    def start_json_sync_service(self):
        """启动JSON同步服务"""
        print("\n📁 启动JSON同步服务...")
        try:
            from integrated_system_manager import IntegratedSystemManager

            manager = IntegratedSystemManager()
            manager.initialize_system()
            manager.start_services()

            self.running = True
            print("  ✅ JSON同步服务已启动")

            # 保持运行
            while self.running:
                time.sleep(1)

        except Exception as e:
            print(f"  ❌ JSON同步服务启动失败: {e}")
            import traceback
            traceback.print_exc()

    def start_api_server(self):
        """启动API服务器"""
        print("\n📡 启动增强版API服务器...")
        try:
            import enhanced_api_server

            enhanced_api_server.main()

        except Exception as e:
            print(f"  ❌ API服务器启动失败: {e}")
            import traceback
            traceback.print_exc()

    def start_http_server(self):
        """启动HTTP服务器"""
        print("\n🌐 启动HTTP服务器...")
        try:
            import http.server
            import socketserver

            PORT = 8888
            Handler = http.server.SimpleHTTPRequestHandler

            with socketserver.TCPServer(("", PORT), Handler) as httpd:
                print(f"  ✅ HTTP服务器已启动在 http://localhost:{PORT}")
                httpd.serve_forever()

        except Exception as e:
            print(f"  ❌ HTTP服务器启动失败: {e}")

    def setup_signal_handlers(self):
        """设置信号处理器"""
        def signal_handler(signum, frame):
            print(f"\n\n📢 接收到停止信号...")
            self.running = False
            self.stop_all_services()

        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)

    def stop_all_services(self):
        """停止所有服务"""
        print("\n🛑 正在停止所有服务...")
        self.running = False

        # 等待线程结束
        for proc in self.processes:
            if proc.is_alive():
                proc.join(timeout=2)

        print("✅ 所有服务已停止")
        print("\n👋 再见!")

    def print_service_info(self):
        """打印服务信息"""
        print("\n" + "=" * 80)
        print("✅ 系统启动完成!")
        print("=" * 80)

        print("\n📡 可用服务:")
        print("  • 增强版API服务器: http://localhost:5002")
        print("  • HTTP服务器: http://localhost:8888")

        print("\n🔗 有用的API端点:")
        print("  • 健康检查: http://localhost:5002/api/health")
        print("  • 系统版本: http://localhost:5002/api/version")
        print("  • 系统状态: http://localhost:5002/api/system/status")
        print("  • AI员工列表: http://localhost:5002/api/ai-employees")
        print("  • 部门统计: http://localhost:5002/api/departments")
        print("  • JSON同步状态: http://localhost:5002/api/json-sync/status")
        print("  • 系统统计: http://localhost:5002/api/statistics")

        print("\n💡 提示:")
        print("  • 按 Ctrl+C 停止所有服务")
        print("  • 所有JSON文件变化会自动同步到数据库")
        print("  • AI员工数据会自动保存和同步")

        print("\n" + "=" * 80)

    def launch(self):
        """启动系统"""
        # 打印横幅
        self.print_banner()

        # 设置信号处理器
        self.setup_signal_handlers()

        # 检查依赖
        self.check_dependencies()

        # 初始化系统
        self.initialize_system()

        # 启动JSON同步服务
        sync_thread = self.start_background_process(
            self.start_json_sync_service,
            "JSON-Sync-Service"
        )
        self.processes.append(sync_thread)

        # 等待一点时间
        time.sleep(2)

        # 启动API服务器
        api_thread = self.start_background_process(
            self.start_api_server,
            "API-Server"
        )
        self.processes.append(api_thread)

        # 启动HTTP服务器
        http_thread = self.start_background_process(
            self.start_http_server,
            "HTTP-Server"
        )
        self.processes.append(http_thread)

        # 打印服务信息
        self.print_service_info()

        # 保持主线程运行
        try:
            self.running = True
            while self.running:
                time.sleep(1)
        except KeyboardInterrupt:
            self.stop_all_services()


def main():
    """主函数"""
    launcher = SystemLauncher()
    launcher.launch()


if __name__ == '__main__':
    main()
