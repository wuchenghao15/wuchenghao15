#!/usr/bin/env python3
"""
服务器日志汇总工具
收集所有正在运行的服务器的最新日志信息
"""

import subprocess
import time
import json
from datetime import datetime

def get_server_logs():
    """获取所有服务器的日志信息"""
    servers = [
        {
            'name': 'ViKey WebSocket服务器',
            'port': 8765,
            'type': 'WebSocket',
            'terminal_id': '637d12be-3bf4-457d-a12f-6ba228276f9e'
        },
        {
            'name': 'HTTP测试服务器 (8085)',
            'port': 8085,
            'type': 'HTTP',
            'terminal_id': 'e7352ebb-1604-42c8-a2fb-c8793560af04'
        },
        {
            'name': 'HTTP测试服务器 (8080)',
            'port': 8080,
            'type': 'HTTP',
            'terminal_id': 'b8af70c3-f34d-4fc0-9061-86f999e3de9d'
        },
        {
            'name': 'HTTP测试服务器 (8082)',
            'port': 8082,
            'type': 'HTTP',
            'terminal_id': 'd6057c28-a72c-48a3-82cf-ebad285f2700'
        }
    ]
    
    print("=" * 80)
    print(f"🖥️  服务器状态报告 - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 80)
    
    for i, server in enumerate(servers, 1):
        print(f"\n📋 服务器 {i}: {server['name']}")
        print(f"   端口: {server['port']}")
        print(f"   类型: {server['type']}")
        print(f"   终端ID: {server['terminal_id']}")
        
        # 检查端口是否在监听
        try:
            result = subprocess.run(['lsof', '-i', f':{server["port"]}'], 
                                  capture_output=True, text=True, timeout=5)
            if result.returncode == 0:
                print(f"   状态: ✅ 运行中")
                # 解析lsof输出获取进程信息
                lines = result.stdout.strip().split('\n')
                if len(lines) > 1:
                    parts = lines[1].split()
                    if len(parts) >= 2:
                        print(f"   进程: {parts[0]} (PID: {parts[1]})")
            else:
                print(f"   状态: ❌ 未运行")
        except subprocess.TimeoutExpired:
            print(f"   状态: ⏰ 检查超时")
        except Exception as e:
            print(f"   状态: ❓ 检查失败 - {str(e)}")
    
    print("\n" + "=" * 80)
    print("📊 网络连接统计")
    print("=" * 80)
    
    # 检查所有相关端口的连接状态
    ports = [8765, 8080, 8082, 8085]
    for port in ports:
        try:
            result = subprocess.run(['netstat', '-an'], 
                                  capture_output=True, text=True, timeout=5)
            connections = [line for line in result.stdout.split('\n') 
                          if f'.{port}' in line and 'LISTEN' in line]
            if connections:
                print(f"端口 {port}: {len(connections)} 个监听连接")
            else:
                print(f"端口 {port}: 无监听连接")
        except Exception as e:
            print(f"端口 {port}: 检查失败 - {str(e)}")
    
    print("\n" + "=" * 80)
    print("🔍 最近的服务器访问日志")
    print("=" * 80)
    
    # 尝试读取最近的HTTP访问日志
    log_files = [
        '/Users/wuchenghao/Library/CloudStorage/OneDrive-个人/文档/MTSCOS_AI_Project/Logs/http_server.log',
        '/Users/wuchenghao/Library/CloudStorage/OneDrive-个人/文档/MTSCOS_AI_Project/Logs/server.log'
    ]
    
    for log_file in log_files:
        try:
            with open(log_file, 'r', encoding='utf-8') as f:
                lines = f.readlines()
                if lines:
                    print(f"\n📝 {log_file.split('/')[-1]} (最后5条):")
                    for line in lines[-5:]:
                        print(f"   {line.strip()}")
        except FileNotFoundError:
            continue
        except Exception as e:
            print(f"读取 {log_file} 失败: {str(e)}")
    
    print("\n" + "=" * 80)
    print("✅ 服务器状态汇总完成")
    print("=" * 80)

if __name__ == "__main__":
    get_server_logs()