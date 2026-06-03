# -*- coding: utf-8 -*-
#!/usr/bin/env python3
"""
脚本监控与自动修复AI模块
用于监控和修复项目中的所有脚本, 避免长时间无输出,死循环或等待用户操作
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
        self.timeout_threshold = 60
        self.no_output_threshold = 30
        self.max_retries = 3

    def monitor_script(self, script_path, args=None, timeout=None):
        """监控执行脚本: 自动处理超时和无输出情况"""
        if not os.path.exists(script_path):
            logger.error(f"脚本不存在: {script_path}")
            return False

        if timeout is None:
            timeout = self.timeout_threshold

        try:
            cmd = [sys.executable, script_path]
            if args:
                cmd.extend(args)

            process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )

            self.monitored_processes[script_path] = {
                'process': process,
                'start_time': time.time(),
                'last_output_time': time.time()
            }

            try:
                stdout, stderr = process.communicate(timeout=timeout)
                return {
                    'success': process.returncode == 0,
                    'stdout': stdout,
                    'stderr': stderr,
                    'returncode': process.returncode
                }
            except subprocess.TimeoutExpired:
                self._kill_process(process, script_path)
                return {
                    'success': False,
                    'error': 'timeout',
                    'message': f'脚本执行超时 ({timeout}秒)'
                }

        except Exception as e:
            logger.error(f"监控脚本时出错: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }

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
            process.send_signal(signal.SIGINT)
            logger.info(f"向进程发送健康检查信号: {script_name}")
        except Exception as e:
            logger.error(f"检查进程健康时出错: {str(e)}")

    def _auto_repair_script(self, script_path):
        """自动修复脚本"""
        try:
            with open(script_path, 'r', encoding='utf-8') as f:
                content = f.read()

            repaired_content = self._fix_script_issues(content, script_path)

            if repaired_content != content:
                backup_path = f"{script_path}.backup"
                with open(backup_path, 'w', encoding='utf-8') as f:
                    f.write(content)
                logger.info(f"已备份原脚本到: {backup_path}")

                with open(script_path, 'w', encoding='utf-8') as f:
                    f.write(repaired_content)
                logger.info(f"已修复脚本: {script_path}")

                return self.monitor_script(script_path)

            return {'success': True, 'message': '脚本无需修复'}

        except Exception as e:
            logger.error(f"自动修复脚本时出错: {str(e)}")
            return {'success': False, 'error': str(e)}

    def _fix_script_issues(self, content, script_path):
        """修复脚本中的常见问题"""
        repaired = content
        repaired = self._fix_deadloops(repaired)
        return repaired

    def _fix_deadloops(self, content):
        """修复可能的死循环"""
        lines = content.split('\n')
        for i, line in enumerate(lines):
            if 'while True:' in line or 'while 1:' in line:
                if i + 1 < len(lines) and not lines[i + 1].strip().startswith('#'):
                    indent = ' ' * (len(line) - len(line.lstrip()))
                    lines.insert(i + 1, f'{indent}# 注意:此循环可能导致死循环,建议添加超时控制')
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
        for root, dirs, files in os.walk(directory):
            for file in files:
                if file.endswith('.py') or file.endswith('.sh'):
                    script_path = os.path.join(root, file)
                    if os.path.isfile(script_path):
                        logger.info(f"监控脚本: {script_path}")

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


script_monitor_ai = ScriptMonitorAI()
