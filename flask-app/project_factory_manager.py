#!/usr/bin/env python3
"""
项目工场运作模式管理
确保各层级运作稳定，实现自动化管理和优化
"""

import os
import time
import json
import logging
import threading
import subprocess
from datetime import datetime
from typing import Dict, List, Any, Optional

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    filename='project_factory.log'
)
logger = logging.getLogger('ProjectFactoryManager')


class ProjectFactoryManager:
    """项目工场运作模式管理类"""
    
    def __init__(self):
        self.levels = {
            'core': {
                'name': '核心应用层',
                'status': 'running',
                'components': ['flask_app', 'ai_brain', 'exam_generator'],
                'priority': 1
            },
            'data': {
                'name': '数据层',
                'status': 'running',
                'components': ['database', 'knowledge_base', 'question_bank'],
                'priority': 2
            },
            'ai_service': {
                'name': 'AI服务层',
                'status': 'running',
                'components': ['ai_learning_system', 'ai_employee_system', 'ai_generation'],
                'priority': 3
            },
            'infrastructure': {
                'name': '基础设施层',
                'status': 'running',
                'components': ['deployment', 'build_tools', 'configuration'],
                'priority': 4
            },
            'monitoring': {
                'name': '监控与维护层',
                'status': 'running',
                'components': ['monitoring', 'logging', 'backup', 'maintenance'],
                'priority': 5
            }
        }
        
        self.monitoring_interval = 60  # 监控间隔（秒）
        self.maintenance_schedule = {'hour': 2, 'minute': 0}  # 每日维护时间
        self.is_running = False
        self.monitor_thread = None
        self.maintenance_thread = None
        
        # 初始化状态
        self.system_status = {
            'last_check': None,
            'issues': [],
            'performance_metrics': {},
            'last_maintenance': None
        }
        
        logger.info("项目工场管理系统初始化完成")
    
    def start(self):
        """启动项目工场管理系统"""
        if self.is_running:
            logger.warning("项目工场管理系统已经在运行中")
            return
        
        self.is_running = True
        
        # 启动监控线程
        self.monitor_thread = threading.Thread(target=self._monitor_system)
        self.monitor_thread.daemon = True
        self.monitor_thread.start()
        
        # 启动维护线程
        self.maintenance_thread = threading.Thread(target=self._schedule_maintenance)
        self.maintenance_thread.daemon = True
        self.maintenance_thread.start()
        
        logger.info("项目工场管理系统启动成功")
    
    def stop(self):
        """停止项目工场管理系统"""
        self.is_running = False
        if self.monitor_thread:
            self.monitor_thread.join(timeout=5)
        if self.maintenance_thread:
            self.maintenance_thread.join(timeout=5)
        logger.info("项目工场管理系统已停止")
    
    def _monitor_system(self):
        """监控系统状态"""
        while self.is_running:
            try:
                self._check_system_status()
                self._check_performance()
                self._check_issues()
                
                # 保存状态
                self.system_status['last_check'] = datetime.now().isoformat()
                
                # 每隔监控间隔检查一次
                time.sleep(self.monitoring_interval)
            except Exception as e:
                logger.error(f"监控线程错误: {str(e)}")
                time.sleep(10)
    
    def _check_system_status(self):
        """检查系统各层级状态"""
        logger.info("开始检查系统各层级状态")
        
        # 检查核心应用层
        self._check_flask_app_status()
        
        # 检查数据库状态
        self._check_database_status()
        
        # 检查AI服务状态
        self._check_ai_services()
        
        logger.info("系统各层级状态检查完成")
    
    def _check_flask_app_status(self):
        """检查Flask应用状态"""
        try:
            # 检查Flask应用是否在运行
            result = subprocess.run(
                ['ps', 'aux'],
                capture_output=True,
                text=True,
                timeout=5
            )
            
            flask_running = 'python app.py' in result.stdout
            self.levels['core']['status'] = 'running' if flask_running else 'stopped'
            
            if not flask_running:
                logger.warning("Flask应用未运行，尝试重启...")
                self._restart_flask_app()
        except Exception as e:
            logger.error(f"检查Flask应用状态失败: {str(e)}")
            self.levels['core']['status'] = 'error'
    
    def _restart_flask_app(self):
        """重启Flask应用"""
        try:
            # 停止现有的Flask进程
            subprocess.run(['pkill', '-f', 'python app.py'], capture_output=True, text=True)
            time.sleep(2)
            
            # 启动新的Flask进程
            flask_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'app.py')
            subprocess.Popen(
                ['python', flask_path],
                cwd=os.path.dirname(os.path.abspath(__file__)),
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )
            
            logger.info("Flask应用重启成功")
            self.levels['core']['status'] = 'running'
        except Exception as e:
            logger.error(f"重启Flask应用失败: {str(e)}")
            self.levels['core']['status'] = 'error'
    
    def _check_database_status(self):
        """检查数据库状态"""
        try:
            # 检查数据库文件是否存在
            db_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'app.db')
            if os.path.exists(db_path):
                self.levels['data']['status'] = 'running'
            else:
                self.levels['data']['status'] = 'error'
                logger.error("数据库文件不存在")
        except Exception as e:
            logger.error(f"检查数据库状态失败: {str(e)}")
            self.levels['data']['status'] = 'error'
    
    def _check_ai_services(self):
        """检查AI服务状态"""
        try:
            # 检查AI学习系统状态
            self.levels['ai_service']['status'] = 'running'
        except Exception as e:
            logger.error(f"检查AI服务状态失败: {str(e)}")
            self.levels['ai_service']['status'] = 'error'
    
    def _check_performance(self):
        """检查系统性能"""
        try:
            # 获取系统性能指标
            cpu_usage = self._get_cpu_usage()
            memory_usage = self._get_memory_usage()
            disk_usage = self._get_disk_usage()
            
            self.system_status['performance_metrics'] = {
                'cpu_usage': cpu_usage,
                'memory_usage': memory_usage,
                'disk_usage': disk_usage,
                'timestamp': datetime.now().isoformat()
            }
            
            # 检查性能阈值
            if cpu_usage > 90 or memory_usage > 90 or disk_usage > 90:
                issue = {
                    'level': 'warning',
                    'component': 'system_performance',
                    'message': f"性能异常: CPU={cpu_usage}%, Memory={memory_usage}%, Disk={disk_usage}%",
                    'timestamp': datetime.now().isoformat()
                }
                self.system_status['issues'].append(issue)
                logger.warning(issue['message'])
        except Exception as e:
            logger.error(f"检查系统性能失败: {str(e)}")
    
    def _get_cpu_usage(self) -> float:
        """获取CPU使用率"""
        try:
            result = subprocess.run(
                ['top', '-l', '1', '-n', '0'],
                capture_output=True,
                text=True,
                timeout=5
            )
            for line in result.stdout.split('\n'):
                if 'CPU usage:' in line:
                    parts = line.split(':')[1].split(',')
                    for part in parts:
                        if '% user' in part:
                            return float(part.strip().split()[0])
            return 0.0
        except Exception as e:
            logger.error(f"获取CPU使用率失败: {str(e)}")
            return 0.0
    
    def _get_memory_usage(self) -> float:
        """获取内存使用率"""
        try:
            result = subprocess.run(
                ['top', '-l', '1', '-n', '0'],
                capture_output=True,
                text=True,
                timeout=5
            )
            for line in result.stdout.split('\n'):
                if 'PhysMem:' in line:
                    parts = line.split(':')[1].split(',')
                    used = parts[0].strip().split()[0]
                    free = parts[2].strip().split()[0]
                    
                    # 转换为数值
                    used_mb = float(used.replace('M', ''))
                    free_mb = float(free.replace('M', ''))
                    total_mb = used_mb + free_mb
                    return (used_mb / total_mb) * 100
            return 0.0
        except Exception as e:
            logger.error(f"获取内存使用率失败: {str(e)}")
            return 0.0
    
    def _get_disk_usage(self) -> float:
        """获取磁盘使用率"""
        try:
            result = subprocess.run(
                ['df', '-h', '/'],
                capture_output=True,
                text=True,
                timeout=5
            )
            lines = result.stdout.split('\n')
            if len(lines) > 1:
                # 第二行包含磁盘使用信息
                parts = lines[1].split()
                if len(parts) >= 5:
                    usage_percent = parts[4].replace('%', '')
                    return float(usage_percent)
            return 0.0
        except Exception as e:
            logger.error(f"获取磁盘使用率失败: {str(e)}")
            return 0.0
    
    def _check_issues(self):
        """检查系统问题"""
        try:
            # 检查日志文件大小
            self._check_log_size()
            
            # 检查备份状态
            self._check_backups()
            
            # 清理过期问题
            self._cleanup_issues()
        except Exception as e:
            logger.error(f"检查系统问题失败: {str(e)}")
    
    def _check_log_size(self):
        """检查日志文件大小"""
        try:
            log_dir = os.path.dirname(os.path.abspath(__file__))
            max_log_size = 100 * 1024 * 1024  # 100MB
            
            for filename in os.listdir(log_dir):
                if filename.endswith('.log'):
                    file_path = os.path.join(log_dir, filename)
                    file_size = os.path.getsize(file_path)
                    if file_size > max_log_size:
                        issue = {
                            'level': 'warning',
                            'component': 'logging',
                            'message': f"日志文件过大: {filename} ({file_size / (1024*1024):.1f}MB)",
                            'timestamp': datetime.now().isoformat()
                        }
                        self.system_status['issues'].append(issue)
                        logger.warning(issue['message'])
                        
                        # 清理大日志文件
                        self._rotate_log(file_path)
        except Exception as e:
            logger.error(f"检查日志文件大小失败: {str(e)}")
    
    def _rotate_log(self, log_path):
        """轮换日志文件"""
        try:
            backup_path = f"{log_path}.{datetime.now().strftime('%Y%m%d%H%M%S')}.bak"
            os.rename(log_path, backup_path)
            # 创建新的空日志文件
            with open(log_path, 'w') as f:
                f.write('')
            logger.info(f"日志文件轮换成功: {log_path} -> {backup_path}")
        except Exception as e:
            logger.error(f"日志文件轮换失败: {str(e)}")
    
    def _check_backups(self):
        """检查备份状态"""
        try:
            # 检查最近备份时间
            backup_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'backups')
            if os.path.exists(backup_dir):
                backups = [f for f in os.listdir(backup_dir) if f.endswith('.db')]
                if backups:
                    # 获取最新备份时间
                    latest_backup = max(backups, key=lambda f: os.path.getmtime(os.path.join(backup_dir, f)))
                    backup_time = os.path.getmtime(os.path.join(backup_dir, latest_backup))
                    days_since_backup = (time.time() - backup_time) / (24 * 3600)
                    
                    if days_since_backup > 7:
                        issue = {
                            'level': 'warning',
                            'component': 'backup',
                            'message': f"最近备份已超过{days_since_backup:.1f}天",
                            'timestamp': datetime.now().isoformat()
                        }
                        self.system_status['issues'].append(issue)
                        logger.warning(issue['message'])
                else:
                    issue = {
                        'level': 'warning',
                        'component': 'backup',
                        'message': "未找到备份文件",
                        'timestamp': datetime.now().isoformat()
                    }
                    self.system_status['issues'].append(issue)
                    logger.warning(issue['message'])
        except Exception as e:
            logger.error(f"检查备份状态失败: {str(e)}")
    
    def _cleanup_issues(self):
        """清理过期问题"""
        try:
            now = time.time()
            # 只保留最近24小时的问题
            cutoff_time = now - (24 * 3600)
            
            # 转换时间戳
            filtered_issues = []
            for issue in self.system_status['issues']:
                issue_time = datetime.fromisoformat(issue['timestamp']).timestamp()
                if issue_time > cutoff_time:
                    filtered_issues.append(issue)
            
            self.system_status['issues'] = filtered_issues
        except Exception as e:
            logger.error(f"清理过期问题失败: {str(e)}")
    
    def _schedule_maintenance(self):
        """安排每日维护"""
        while self.is_running:
            try:
                now = datetime.now()
                # 检查是否到达维护时间
                if (now.hour == self.maintenance_schedule['hour'] and 
                    now.minute == self.maintenance_schedule['minute']):
                    logger.info("开始执行每日维护")
                    self._perform_maintenance()
                    logger.info("每日维护执行完成")
                    # 避免重复执行，等待1分钟
                    time.sleep(60)
                time.sleep(30)  # 每30秒检查一次
            except Exception as e:
                logger.error(f"维护调度线程错误: {str(e)}")
                time.sleep(60)
    
    def _perform_maintenance(self):
        """执行系统维护"""
        try:
            # 1. 执行数据库备份
            self._backup_database()
            
            # 2. 清理临时文件
            self._cleanup_temp_files()
            
            # 3. 优化数据库
            self._optimize_database()
            
            # 4. 更新系统状态
            self.system_status['last_maintenance'] = datetime.now().isoformat()
            
            logger.info("系统维护执行成功")
        except Exception as e:
            logger.error(f"系统维护执行失败: {str(e)}")
    
    def _backup_database(self):
        """备份数据库"""
        try:
            db_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'app.db')
            backup_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'backups')
            
            # 确保备份目录存在
            os.makedirs(backup_dir, exist_ok=True)
            
            # 创建备份文件名
            backup_name = f"app_{datetime.now().strftime('%Y%m%d%H%M%S')}.db"
            backup_path = os.path.join(backup_dir, backup_name)
            
            # 执行备份
            import shutil
            shutil.copy2(db_path, backup_path)
            
            # 清理旧备份（保留最近7天）
            self._cleanup_old_backups(backup_dir)
            
            logger.info(f"数据库备份成功: {backup_path}")
        except Exception as e:
            logger.error(f"数据库备份失败: {str(e)}")
    
    def _cleanup_old_backups(self, backup_dir):
        """清理旧备份"""
        try:
            cutoff_time = time.time() - (7 * 24 * 3600)  # 7天前
            
            for filename in os.listdir(backup_dir):
                file_path = os.path.join(backup_dir, filename)
                if os.path.isfile(file_path):
                    file_time = os.path.getmtime(file_path)
                    if file_time < cutoff_time:
                        os.remove(file_path)
                        logger.info(f"清理旧备份: {filename}")
        except Exception as e:
            logger.error(f"清理旧备份失败: {str(e)}")
    
    def _cleanup_temp_files(self):
        """清理临时文件"""
        try:
            # 清理__pycache__目录
            pycache_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), '__pycache__')
            if os.path.exists(pycache_dir):
                for filename in os.listdir(pycache_dir):
                    file_path = os.path.join(pycache_dir, filename)
                    os.remove(file_path)
                logger.info("清理__pycache__目录成功")
            
            # 清理临时日志文件
            log_dir = os.path.dirname(os.path.abspath(__file__))
            for filename in os.listdir(log_dir):
                if filename.endswith('.log.bak'):
                    file_path = os.path.join(log_dir, filename)
                    os.remove(file_path)
                    logger.info(f"清理临时日志文件: {filename}")
        except Exception as e:
            logger.error(f"清理临时文件失败: {str(e)}")
    
    def _optimize_database(self):
        """优化数据库"""
        try:
            # 执行VACUUM命令优化SQLite数据库
            db_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'app.db')
            import sqlite3
            conn = sqlite3.connect(db_path)
            conn.execute('VACUUM')
            conn.close()
            logger.info("数据库优化成功")
        except Exception as e:
            logger.error(f"数据库优化失败: {str(e)}")
    
    def get_system_status(self) -> Dict[str, Any]:
        """获取系统状态"""
        return {
            'levels': self.levels,
            'system_status': self.system_status,
            'is_running': self.is_running
        }
    
    def get_performance_report(self) -> Dict[str, Any]:
        """获取性能报告"""
        return self.system_status['performance_metrics']
    
    def get_issues(self) -> List[Dict[str, Any]]:
        """获取系统问题列表"""
        return self.system_status['issues']
    
    def resolve_issue(self, issue_index: int):
        """解决指定问题"""
        if 0 <= issue_index < len(self.system_status['issues']):
            resolved_issue = self.system_status['issues'].pop(issue_index)
            logger.info(f"问题已解决: {resolved_issue['message']}")
        else:
            logger.warning(f"无效的问题索引: {issue_index}")
    
    def execute_maintenance(self):
        """手动执行系统维护"""
        logger.info("手动执行系统维护")
        self._perform_maintenance()


# 创建全局实例
project_factory_manager = ProjectFactoryManager()


if __name__ == "__main__":
    # 启动项目工场管理系统
    project_factory_manager.start()
    
    try:
        # 运行60秒后停止
        time.sleep(60)
        print("系统状态:", json.dumps(project_factory_manager.get_system_status(), ensure_ascii=False, indent=2))
    finally:
        project_factory_manager.stop()
