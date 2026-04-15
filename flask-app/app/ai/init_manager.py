#!/usr/bin/env python3
"""
自动化初始化管理脚本
用于管理和监控项目的所有初始化脚本，确保它们按顺序执行，避免长时间无输出或死循环
"""

import os
import sys
import time
import subprocess
import signal
import logging
from app.utils.logging import logger
from app.ai.script_monitor import ScriptMonitorAI

class InitializationManager:
    """初始化管理类"""
    
    def __init__(self):
        self.script_monitor = ScriptMonitorAI()
        self.init_scripts = [
            'create_user.py',
            'add_system_configs.py',
            'add_caopw_to_user_group.py',
            'update_database.py',
            'update_japanese_level_table.py'
        ]
        self.script_dir = '/Users/wuchenghao/Library/CloudStorage/OneDrive-个人/文档/MTSCOS_AI_Project/flask-app'
        
    def run_initialization(self):
        """执行所有初始化脚本"""
        logger.info("开始自动化初始化流程...")
        
        # 先修复所有脚本
        logger.info("第一步：修复所有脚本文件...")
        self.script_monitor.auto_fix_all_scripts(self.script_dir)
        logger.info("脚本修复完成")
        
        # 按顺序执行初始化脚本
        logger.info("第二步：执行初始化脚本...")
        for script in self.init_scripts:
            script_path = os.path.join(self.script_dir, script)
            if os.path.exists(script_path):
                logger.info(f"执行初始化脚本: {script}")
                result = self.script_monitor.monitor_script(script_path, timeout=60)
                if not result:
                    logger.error(f"脚本 {script} 执行失败，尝试跳过...")
                else:
                    logger.info(f"脚本 {script} 执行成功")
            else:
                logger.warning(f"初始化脚本 {script} 不存在，跳过...")
        
        logger.info("初始化流程完成")
        return True
    
    def monitor_initialization(self):
        """监控初始化过程"""
        logger.info("启动初始化监控...")
        
        # 设置全局超时
        signal.signal(signal.SIGALRM, self._timeout_handler)
        signal.alarm(300)  # 5分钟全局超时
        
        try:
            result = self.run_initialization()
            signal.alarm(0)  # 取消超时
            return result
        except Exception as e:
            logger.error(f"初始化监控出错: {str(e)}")
            signal.alarm(0)  # 取消超时
            return False
    
    def _timeout_handler(self, signum, frame):
        """初始化超时处理"""
        logger.error("初始化过程超时，自动终止")
        sys.exit(1)

# 创建全局初始化管理器实例
init_manager = InitializationManager()
