#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
启动JSON自动同步系统
"""
import os
import sys
import subprocess

def check_dependencies():
    """检查依赖库"""
    try:
        import watchdog
        print("✓ watchdog 已安装")
    except ImportError:
        print("✗ watchdog 未安装，正在安装...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", "watchdog"])
        print("✓ watchdog 安装完成")
    
    return True

def main():
    print("=" * 60)
    print("MTSCOS JSON自动同步系统 - 启动器")
    print("=" * 60)
    
    # 检查依赖
    print("\n检查依赖...")
    check_dependencies()
    
    # 导入并启动同步系统
    print("\n导入同步系统...")
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    
    from json_auto_sync_system import EnhancedJSONSyncManager, JSONSyncAPI
    from flask import Flask
    
    project_root = os.path.dirname(os.path.abspath(__file__))
    
    # 创建同步管理器
    print("\n初始化同步管理器...")
    sync_manager = EnhancedJSONSyncManager(
        db_path=os.path.join(project_root, "mtcos_json_sync.db"),
        project_root=project_root
    )
    
    # 扫描目录
    print("\n正在扫描JSON文件...")
    found_count = sync_manager.scan_directory()
    
    if found_count > 0:
        print(f"发现 {found_count} 个JSON文件")
        
        # 初始同步
        print("\n正在执行初始同步...")
        synced_count = sync_manager.sync_all_files()
        print(f"同步完成: {synced_count} 个文件")
    
    # 显示统计
    stats = sync_manager.get_statistics()
    print("\n同步统计:")
    print(f"  - 总文件: {stats.get('total_files', 0)}")
    print(f"  - 已同步: {stats.get('synced_files', 0)}")
    print(f"  - 版本总数: {stats.get('total_versions', 0)}")
    print(f"  - 成功次数: {stats.get('success_count', 0)}")
    
    # 启动监控
    print("\n启动文件监控...")
    sync_manager.start_file_monitoring()
    
    print("\n启动定期同步...")
    sync_manager.start_periodic_sync()
    
    print("\n" + "=" * 60)
    print("JSON同步系统已启动!")
    print("  - 实时监控JSON文件变化")
    print("  - 定期同步(10秒间隔)")
    print("  - 按 Ctrl+C 停止")
    print("=" * 60)
    
    try:
        import time
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\n正在停止...")
        sync_manager.stop_file_monitoring()
        sync_manager.stop_periodic_sync()
        print("已停止")

if __name__ == "__main__":
    main()
