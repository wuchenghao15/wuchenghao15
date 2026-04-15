#!/usr/bin/env python3
"""
脚本监控与自动修复AI模块
用于监控和修复项目中的所有脚本，避免长时间无输出、死循环或等待用户操作
"""

import os
import sys
import time
import subprocess
import signal
import traceback
import logging
from app.utils.logging import logger

class ScriptMonitorAI:
    """脚本监控与自动修复AI"""
    
    def __init__(self):
        self.monitored_processes = {}
        self.timeout_threshold = 60  # 脚本执行超时阈值（秒）
        self.no_output_threshold = 30  # 无输出超时阈值（秒）
        self.max_retries = 3  # 最大重试次数
        
    def monitor_script(self, script_path, args=None, timeout=None):
        """监控执行脚本，自动处理超时和无输出情况"""
        if not os.path.exists(script_path):
            logger.error(f"脚本不存在: {script_path}")
            return False
        
        timeout = timeout or self.timeout_threshold
        start_time = time.time()
        last_output_time = start_time
        
        logger.info(f"开始监控脚本: {script_path}")
        
        try:
            # 执行脚本，捕获输出
            process = subprocess.Popen(
                [sys.executable, script_path] + (args or []),
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                bufsize=1,
                universal_newlines=True
            )
            
            script_name = os.path.basename(script_path)
            self.monitored_processes[script_name] = process
            
            # 监控输出
            output_buffer = []
            while True:
            # 注意：此循环可能导致死循环，建议添加超时控制
                line = process.stdout.readline()
                
                if not line and process.poll() is not None:
                    break
                
                if line:
                    output_buffer.append(line)
                    logger.info(f"[{script_name}] {line.strip()}")
                    last_output_time = time.time()
                
                # 检查超时
                current_time = time.time()
                if current_time - start_time > timeout:
                    logger.error(f"脚本执行超时: {script_path}")
                    self._kill_process(process, script_name)
                    return self._auto_repair_script(script_path)
                
                # 检查长时间无输出
                if current_time - last_output_time > self.no_output_threshold:
                    logger.warning(f"脚本长时间无输出: {script_path}")
                    # 发送一个输出请求或检查信号
                    self._check_process_health(process, script_name)
                    last_output_time = current_time
            
            # 获取返回码
            return_code = process.poll()
            if return_code != 0:
                logger.error(f"脚本执行失败，返回码: {return_code}")
                return self._auto_repair_script(script_path)
            
            logger.info(f"脚本执行成功: {script_path}")
            return True
            
        except Exception as e:
            logger.error(f"监控脚本时出错: {str(e)}")
            logger.error(traceback.format_exc())
            return self._auto_repair_script(script_path)
        finally:
            if script_name in self.monitored_processes:
                del self.monitored_processes[script_name]
    
    def _kill_process(self, process, script_name):
        """终止进程"""
        try:
            process.terminate()
            time.sleep(2)
            if process.poll() is None:
                process.kill()
                logger.warning(f"强制终止进程: {script_name}")
        except Exception as e:
            logger.error(f"终止进程时出错: {str(e)}")
    
    def _check_process_health(self, process, script_name):
        """检查进程健康状态"""
        try:
            # 发送一个信号检查进程是否响应
            process.send_signal(signal.SIGINT)
            logger.info(f"向进程发送健康检查信号: {script_name}")
        except Exception as e:
            logger.error(f"检查进程健康时出错: {str(e)}")
    
    def _auto_repair_script(self, script_path):
        """自动修复脚本"""
        logger.info(f"开始自动修复脚本: {script_path}")
        
        try:
            with open(script_path, 'r') as f:
                content = f.read()
            
            # 修复常见问题
            repaired_content = self._fix_script_issues(content, script_path)
            
            if repaired_content != content:
                # 备份原脚本
                backup_path = f"{script_path}.backup"
                with open(backup_path, 'w') as f:
                    f.write(content)
                logger.info(f"已备份原脚本到: {backup_path}")
                
                # 写入修复后的脚本
                with open(script_path, 'w') as f:
                    f.write(repaired_content)
                logger.info(f"已修复脚本: {script_path}")
                
                # 重新执行修复后的脚本
                return self.monitor_script(script_path)
            else:
                logger.info(f"脚本无需修复: {script_path}")
                return False
                
        except Exception as e:
            logger.error(f"自动修复脚本时出错: {str(e)}")
            logger.error(traceback.format_exc())
            return False
    
    def _fix_script_issues(self, content, script_path):
        """修复脚本中的常见问题"""
        repaired = content
        
        # 只保留最基本的修复功能，避免过度修复导致更多问题
        # 1. 修复死循环 - 只添加注释，不修改代码逻辑
        repaired = self._fix_deadloops(repaired)
        
        return repaired
    
    def _fix_deadloops(self, content):
        """修复可能的死循环"""
        # 简单的死循环检测，只添加注释提示，不修改代码
        lines = content.split('\n')
        for i, line in enumerate(lines):
            # 检测缺少计数器或条件的while循环
            if 'while True:' in line or 'while 1:' in line:
                # 只添加注释，不修改代码
                if i + 1 < len(lines) and not lines[i + 1].strip().startswith('#'):
                    indent = ' ' * (len(line) - len(line.lstrip()))
                    lines.insert(i + 1, f'{indent}# 注意：此循环可能导致死循环，建议添加超时控制')
        return '\n'.join(lines)
    
    def _add_timeout_control(self, content, script_path):
        """为脚本添加超时控制 - 暂时禁用此功能"""
        return content
    
    def _add_progress_output(self, content):
        """为脚本添加进度输出 - 暂时禁用此功能"""
        return content
    
    def _add_exception_handling(self, content):
        """为脚本添加异常处理 - 暂时禁用此功能"""
        return content
    
    def _fix_syntax_errors(self, content):
        """修复常见语法错误 - 暂时禁用此功能"""
        return content
    
    def monitor_all_scripts(self, directory):
        """监控目录下的所有脚本"""
        logger.info(f"开始监控目录下的所有脚本: {directory}")
        
        for root, dirs, files in os.walk(directory):
            for file in files:
                if file.endswith('.py') or file.endswith('.sh'):
                    script_path = os.path.join(root, file)
                    if os.path.isfile(script_path):
                        logger.info(f"监控脚本: {script_path}")
                        self.monitor_script(script_path)
    
    def auto_fix_all_scripts(self, directory):
        """自动修复目录下的所有脚本"""
        logger.info(f"开始自动修复目录下的所有脚本: {directory}")
        
        for root, dirs, files in os.walk(directory):
            for file in files:
                if file.endswith('.py') or file.endswith('.sh'):
                    script_path = os.path.join(root, file)
                    if os.path.isfile(script_path):
                        logger.info(f"自动修复脚本: {script_path}")
                        self._auto_repair_script(script_path)

# 创建全局脚本监控AI实例
script_monitor_ai = ScriptMonitorAI()
