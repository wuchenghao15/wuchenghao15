#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
MTSCOS完整系统启动器
自动适配新功能并启动所有服务
"""
import os
import sys
import subprocess
import time
from datetime import datetime

def check_python_version():
    """检查Python版本"""
    print(f"✓ Python {sys.version.split()[0]}")
    return True

def check_dependencies():
    """检查并安装依赖"""
    print("\n检查依赖库...")

    deps = {
        'watchdog': 'watchdog',
        'flask': 'flask',
        'flask_cors': 'flask-cors'
    }

    for name, package in deps.items():
        try:
            __import__(name)
            print(f"  ✓ {package}")
        except ImportError:
            print(f"  ✗ {package} 未安装，正在安装...")
            try:
                subprocess.check_call([sys.executable, "-m", "pip", "install", package])
                print(f"  ✓ {package} 已安装")
            except:
                print(f"  ⚠ {package} 安装失败")

def start_auto_adapter():
    """启动自动适配器"""
    print("\n执行系统自动适配...")
    try:
        from system_auto_adapter import SystemAutoAdapter

        project_root = os.path.dirname(os.path.abspath(__file__))
        adapter = SystemAutoAdapter(project_root)
        result = adapter.auto_adapt()

        return result
    except Exception as e:
        print(f"✗ 自动适配失败: {e}")
        return None

def start_services():
    """启动服务"""
    print("\n启动后台服务...")

    services = []

    # 启动Flask API服务
    print("  启动Flask API服务...")
    try:
        flask_proc = subprocess.Popen(
            [sys.executable, "api_server.py"],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            cwd=os.path.dirname(os.path.abspath(__file__))
        )
        services.append(('Flask API', flask_proc))
        print(f"  ✓ Flask API PID: {flask_proc.pid}")
    except Exception as e:
        print(f"  ✗ Flask API启动失败: {e}")

    # 启动HTTP服务
    print("  启动HTTP服务...")
    try:
        http_proc = subprocess.Popen(
            [sys.executable, "-m", "http.server", "8888"],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            cwd=os.path.dirname(os.path.abspath(__file__))
        )
        services.append(('HTTP Server', http_proc))
        print(f"  ✓ HTTP Server PID: {http_proc.pid}")
    except Exception as e:
        print(f"  ✗ HTTP Server启动失败: {e}")

    return services

def main():
    """主函数"""
    print("=" * 60)
    print("MTSCOS AI Project - 完整系统启动")
    print("=" * 60)
    print(f"启动时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()

    # 检查Python版本
    print("[1/5] 检查Python环境...")
    check_python_version()

    # 检查依赖
    print("\n[2/5] 检查依赖库...")
    check_dependencies()

    # 执行自动适配
    print("\n[3/5] 执行系统自动适配...")
    adapter_result = start_auto_adapter()

    # 启动服务
    print("\n[4/5] 启动后台服务...")
    services = start_services()

    # 显示完成信息
    print("\n" + "=" * 60)
    print("✓ 系统启动完成!")
    print("=" * 60)
    print()
    print("服务地址:")
    print("  - API Server: http://localhost:5000")
    print("  - HTTP Server: http://localhost:8888")
    print()
    print("已加载模块:")
    if adapter_result:
        print(f"  - JSON自动同步: ✓")
    print()
    print("后台进程:")
    for name, proc in services:
        print(f"  - {name}: PID {proc.pid}")
    print()

    print("查看日志:")
    print("  - API Server: ps aux | grep api_server.py")
    print("  - HTTP Server: ps aux | grep http.server")
    print("  - JSON Sync: ps aux | grep system_auto_adapter")
    print()

    print("停止服务:")
    pids = [str(proc.pid) for _, proc in services]
    if pids:
        print(f"  kill {' '.join(pids)}")
    print("=" * 60)

    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
