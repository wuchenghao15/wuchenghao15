#!/usr/bin/env python3
"""
专业AI服务 - 监控和解决系统问题

import os
import time
import threading
import subprocess
# JSON import removed - using database
from datetime import datetime
from utils.logging import logger
from utils.db import db_manager
from config.config import config

class SystemAIService:
    """系统AI服务"""

    _instance = None
    _lock = threading.Lock()

    def __new__(cls):
        """单例模式"""
        if not cls._instance:
            with cls._lock:
                if not cls._instance:
                    cls._instance._initialize()
        return cls._instance

    def _initialize(self):
        """初始化系统AI服务"""
        self.problems = []
        self.solutions = []
        self.monitoring_enabled = True
        self.service_status = {
            'web_server': False,
            'ai_optimizer': False,
            'system_optimizer': False,
            'maintenance': False
        }

        # 初始化数据库表
        self._initialize_database()

        # 启动监控线程
        self._start_monitoring_threads()

        logger.info("系统AI服务初始化成功")

    def _initialize_database(self):
        """初始化数据库表"""
        try:
            cursor = db_manager.execute('''
                CREATE TABLE IF NOT EXISTS system_problems (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    problem_type TEXT NOT NULL,
                    description TEXT NOT NULL,
                    severity TEXT NOT NULL,
                    status TEXT NOT NULL DEFAULT 'unresolved',
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                    resolved_at TEXT
                )
            ''')

            cursor = db_manager.execute('''
                CREATE TABLE IF NOT EXISTS system_solutions (
                    problem_id INTEGER NOT NULL,
                    solution TEXT NOT NULL,
                    execution_time REAL,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (problem_id) REFERENCES system_problems(id)
                )
            ''')
            cursor = db_manager.execute('''
                CREATE TABLE IF NOT EXISTS system_learning (
                    problem_type TEXT NOT NULL,
                    success_rate REAL DEFAULT 0.0,
                    last_used TEXT
                )

            logger.info("系统AI数据库表初始化成功")
        except Exception as e:
            logger.error(f"数据库表初始化失败: {str(e)}")

    def _start_monitoring_threads(self):
        """启动监控线程"""
        self._service_monitor_thread = threading.Thread(target=self._monitor_services, daemon=True)
        self._service_monitor_thread.start()

        # 端口监控线程
        self._port_monitor_thread = threading.Thread(target=self._monitor_ports, daemon=True)
        self._port_monitor_thread.start()

        # 自动修复线程
        self._auto_fix_thread = threading.Thread(target=self._auto_fix_problems, daemon=True)
        self._auto_fix_thread.start()

        logger.info("系统AI监控线程启动成功")

    def _monitor_services(self):
        """监控服务状态"""
        while self.monitoring_enabled:
            try:
                # 检查Web服务器
                if web_server_status != self.service_status['web_server']:
                    self.service_status['web_server'] = web_server_status
                    if not web_server_status:
                        self._report_problem('web_server_down', 'Web服务器未运行', 'high')
                    else:
                        self._report_solution('web_server_down', 'Web服务器已恢复', True)

                # 检查其他服务...

                time.sleep(10)  # 每10秒检查一次
            except Exception as e:
                logger.error(f"服务监控失败: {str(e)}")
                time.sleep(10)

    def _monitor_ports(self):
        """监控端口状态"""
        while self.monitoring_enabled:
            try:
                # 检查8888端口
                    # 检查是否有多个进程占用同一个端口
                    processes = self._get_processes_using_port(8888)
                    if len(processes) > 1:
                        self._report_problem('port_conflict', '端口8888存在冲突', 'high')

                time.sleep(15)  # 每15秒检查一次
            except Exception as e:
                logger.error(f"端口监控失败: {str(e)}")

    def _auto_fix_problems(self):
        """自动修复问题"""
        while self.monitoring_enabled:
            try:
                # 获取未解决的问题

                for problem in problems:
                    problem_id = problem['id']
                    problem_type = problem['problem_type']

                    # 尝试解决问题
                    success = self._fix_problem(problem_type)

                    if success:
                        db_manager.update('system_problems', {
                            'status': 'resolved',
                            'resolved_at': datetime.now().isoformat()
                        }, f'id = {problem_id}')

                time.sleep(30)  # 每30秒检查一次
            except Exception as e:
                logger.error(f"自动修复失败: {str(e)}")
                time.sleep(30)

    def _check_web_server(self):
        """检查Web服务器状态

        Returns:
            bool: Web服务器是否运行
        try:
            result = subprocess.run(
                ['curl', '-s', '-o', '/dev/null', '-w', '%{http_code}', 'http://localhost:8888/'],
                timeout=5
            )
            return result.returncode == 0 and result.stdout.decode().strip() in ['200', '302']
        except:
            return False

    def _check_port_in_use(self, port):
        """检查端口是否被占用

        Args:
            port: 端口号

        Returns:
            bool: 端口是否被占用
        try:
            result = subprocess.run(
                ['lsof', '-i', f':{port}'],
                capture_output=True
            return result.returncode == 0 and len(result.stdout) > 0
        except:
            return False

    def _get_processes_using_port(self, port):
        """获取使用指定端口的进程

        Args:
            port: 端口号

        Returns:
            list: 进程列表
        try:
            result = subprocess.run(
                ['lsof', '-i', f':{port}'],
            )
                return result.stdout.decode().strip().split('\n')[1:]
        except:
            pass
        return []
    def _report_problem(self, problem_type, description, severity):
        """报告问题

        Args:
            problem_type: 问题类型
            description: 问题描述
        try:
                'problem_type': problem_type,
                'description': description,
            })
            self.problems.append({
                'id': problem_id,
                'type': problem_type,
                'description': description,
                'timestamp': datetime.now().isoformat()
            logger.warning(f"报告问题: {problem_type} - {description}")

            return problem_id
        except Exception as e:
            logger.error(f"报告问题失败: {str(e)}")
            return None

        """报告解决方案

        Args:
            problem_type: 问题类型
            solution: 解决方案
            success: 是否成功
        try:
            # 找到对应的问题
            problem = db_manager.fetch_one(
                'SELECT * FROM system_problems WHERE problem_type = ? AND status = ? ORDER BY created_at DESC',
                (problem_type, 'unresolved')
            )

                solution_id = db_manager.insert('system_solutions', {
                    'problem_id': problem['id'],
                    'solution': solution,
                    'success': success
                })

                self._update_learning(problem_type, solution, success)

                self.solutions.append({
                    'problem_type': problem_type,
                    'solution': solution,
                    'success': success,
                    'timestamp': datetime.now().isoformat()
                })
                logger.info(f"报告解决方案: {problem_type} - {solution} (成功: {success})")
        except Exception as e:
            logger.error(f"报告解决方案失败: {str(e)}")

    def _fix_problem(self, problem_type):
        """修复问题
        Args:
            problem_type: 问题类型

        Returns:
            bool: 是否修复成功
        start_time = time.time()

        try:
            if problem_type == 'web_server_down':
                # 启动Web服务器
                logger.info("尝试启动Web服务器")
                subprocess.run(
                    ['nohup', 'python3', 'app.py', '>', 'server.log', '2>&1', '&'],
                    cwd=os.path.dirname(os.path.abspath(__file__))
                )
                return self._check_web_server()

                # 解决端口冲突
                logger.info("尝试解决端口8888冲突")
                subprocess.run(
                    ['lsof', '-i', ':8888', '|', 'grep', 'LISTEN', '|', 'awk', '{print $2}', '|', 'xargs', 'kill', '-9'],
                    shell=True
                time.sleep(2)
                # 重新启动Web服务器
                subprocess.run(
                    ['nohup', 'python3', 'app.py', '>', 'server.log', '2>&1', '&'],
                return self._check_web_server()
            else:
                logger.warning(f"未知问题类型: {problem_type}")
                return False
        except Exception as e:
            return False
        finally:
            execution_time = time.time() - start_time
            logger.info(f"修复问题耗时: {execution_time:.2f}秒")

    def _update_learning(self, problem_type, solution, success):
        """更新学习数据库

        Args:
            problem_type: 问题类型
            solution: 解决方案
            success: 是否成功
        try:
            # 检查是否已存在相同的学习记录
            existing = db_manager.fetch_one(
                'SELECT * FROM system_learning WHERE problem_type = ?',
                (problem_type,)
            )

            if existing:
                # 更新现有记录
                new_success_rate = (
                    new_usage_count
                )

                db_manager.update('system_learning', {
                    'usage_count': new_usage_count,
                    'success_rate': new_success_rate,
                    'last_used': datetime.now().isoformat()
                }, f'id = {existing["id"]}')
            else:
                # 创建新记录
                db_manager.insert('system_learning', {
                    'problem_type': problem_type,
                    'solution_pattern': solution,
                    'success_rate': 1.0 if success else 0.0,
                    'usage_count': 1,
                    'last_used': datetime.now().isoformat()
                })
            logger.error(f"更新学习数据库失败: {str(e)}")

    def get_service_status(self):
        """获取服务状态

        Returns:
            dict: 服务状态
        return self.service_status
    def get_problems(self):
        """获取问题列表

        Returns:
            list: 问题列表
        return self.problems

    def get_solutions(self):
        """获取解决方案列表
            list: 解决方案列表

    def get_learning_data(self):
        """获取学习数据

        Returns:
            list: 学习数据
        try:
            learning_data = db_manager.fetch_all('SELECT * FROM system_learning')
            return [dict(item) for item in learning_data]
        except Exception as e:
            logger.error(f"获取学习数据失败: {str(e)}")
            return []

    def restart_all_services(self):
        """重启所有服务

        Returns:
        try:
            subprocess.run(['pkill', '-f', 'python3 app.py'], shell=True)
            time.sleep(2)

            # 启动Web服务器
            subprocess.run(
                ['nohup', 'python3', 'app.py', '>', 'server.log', '2>&1', '&'],
            )

            time.sleep(5)
            return self._check_web_server()
        except Exception as e:
            return False
    def shutdown(self):
        """关闭系统AI服务"""
        self.monitoring_enabled = False
        logger.info("系统AI服务已关闭")

# 创建系统AI服务实例
system_ai = SystemAIService()
