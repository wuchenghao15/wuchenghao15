# -*- coding: utf-8 -*-
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
系统彻底重启脚本
停止所有服务、清理缓存、重新初始化
"""

import os
import sys
import time
import subprocess
from datetime import datetime

def stop_running_processes():
    """停止所有相关进程"""
    logger.info("[1/5] 停止运行中的进程...")
    
    processes = [
        "python main.py",
        "python3 main.py",
        "flask run",
        "gunicorn",
        "uwsgi"
    ]
    
    for proc in processes:
        try:
            result = subprocess.run(f"pkill -f '{proc}'", shell=True, capture_output=True)
            if result.returncode == 0:
                logger.info(f"  ✓ 已停止: {proc}")
        except Exception as e:
            pass
    
    # 检查并清理PID文件
    pid_files = ["server.pid", ".python.pid", ".node.pid", ".mtscos_ai_launcher.pid"]
    for pid_file in pid_files:
        if os.path.exists(pid_file):
            try:
                with open(pid_file, 'r') as f:
                    pid = f.read().strip()
                    if pid:
                        subprocess.run(f"kill -9 {pid}", shell=True, capture_output=True)
                os.remove(pid_file)
                logger.info(f"  ✓ 已清理PID文件: {pid_file}")
            except Exception:
                pass

def clear_caches():
    """清理缓存文件"""
    logger.info("[2/5] 清理缓存文件...")
    
    cache_dirs = [
        ".cache",
        "cache",
        "__pycache__",
        "**/__pycache__",
        "*.pyc",
        "**/*.pyc",
        "node_modules/.cache"
    ]
    
    for cache in cache_dirs:
        try:
            if cache.endswith('.pyc'):
                result = subprocess.run(f"find . -name '{cache}' -delete", shell=True)
            elif cache.startswith('**/'):
                result = subprocess.run(f"find . -type d -name '{cache[3:]}' -exec rm -rf {{}} +", shell=True)
            else:
                result = subprocess.run(f"rm -rf {cache}", shell=True)
            
            if result.returncode == 0:
                logger.info(f"  ✓ 已清理: {cache}")
        except Exception as e:
            pass

def cleanup_logs():
    """清理旧日志文件"""
    logger.info("[3/5] 清理旧日志文件...")
    
    try:
        # 保留最近7天的日志
        result = subprocess.run("find Logs -name '*.log' -mtime +7 -delete", shell=True)
        if result.returncode == 0:
            logger.info("  ✓ 已清理7天前的日志")
        
        # 清理临时日志
        result = subprocess.run("rm -f *.log 2>/dev/null", shell=True)
        if result.returncode == 0:
            logger.info("  ✓ 已清理根目录日志")
    except Exception as e:
        pass

def verify_database():
    """验证数据库完整性"""
    logger.info("[4/5] 验证数据库...")
    
    db_files = ["app.db", "engineer_ai.db", "mtscos.db", "shadow_app.db"]
    
    for db_file in db_files:
        if os.path.exists(db_file):
            try:
                result = subprocess.run(f"sqlite3 {db_file} \"SELECT 1\"", shell=True, capture_output=True)
                if result.returncode == 0:
                    size = os.path.getsize(db_file) / (1024 * 1024)
                    logger.info(f"  ✓ {db_file}: {size:.2f} MB - 正常")
                else:
                    logger.info(f"  ✗ {db_file}: 数据库异常")
            except Exception as e:
                logger.info(f"  ✗ {db_file}: {e}")

def start_system():
    """启动系统服务"""
    logger.info("[5/5] 启动系统服务...")
    
    # 创建启动脚本
    start_script = """
#!/bin/bash
cd /Users/wuchenghao/Library/CloudStorage/OneDrive-个人/文档/MTSCOS_AI_Project
source .venv/bin/activate
python main.py > startup.log 2>&1 &
echo $! > server.pid
echo "System started with PID: $!"
"""
    
    with open('/tmp/start_mtscos.sh', 'w') as f:
        f.write(start_script)
    
    os.chmod('/tmp/start_mtscos.sh', 0o755)
    
    result = subprocess.run('/tmp/start_mtscos.sh', shell=True, capture_output=True)
    if result.returncode == 0:
        logger.info("  ✓ 系统启动脚本已执行")
        
        time.sleep(2)
        
        if os.path.exists('server.pid'):
            with open('server.pid', 'r') as f:
                pid = f.read().strip()
            logger.info(f"  ✓ 系统已启动，PID: {pid}")
            logger.info(f"  ✓ 日志文件: startup.log")
    else:
        logger.info(f"  ✗ 启动失败: {result.stderr.decode()}")

def main():
    """主入口"""
    logger.info("=" * 70)
    logger.info("MTSCOS AI 系统彻底重启")
    logger.info("=" * 70)
    logger.info(f"时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
    
    stop_running_processes()
    logger.info()
    
    clear_caches()
    logger.info()
    
    cleanup_logs()
    logger.info()
    
    verify_database()
    logger.info()
    
    start_system()
    
    logger.info("\n" + "=" * 70)
    logger.info("系统重启完成！")
    logger.info("=" * 70)
    logger.info("\n后续操作:")
    logger.info("  • 查看日志: tail -f startup.log")
    logger.info("  • 检查状态: curl http://localhost:5000/status")
    logger.info("  • 停止服务: pkill -f 'python main.py'")

if __name__ == "__main__":
    main()