#!/usr/bin/env python3
"""
系统自动优化服务 - 自动优化所有系统项目、功能和服务器

import os
import time
import threading
# JSON import removed - using database
import psutil
import subprocess
from datetime import datetime
from utils.logging import logger
from utils.db import db_manager

class SystemOptimizer:
    """系统自动优化器"""

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
        """初始化系统优化器"""
        self.projects = {}
        self.optimization_history = []
        self.server_metrics = {}
        self.lock = threading.RLock()

        # 启动自动优化线程
        self._start_auto_optimization_thread()

        # 启动服务器监控线程
        self._start_server_monitoring_thread()

        logger.info("系统自动优化器初始化成功")

    def _start_auto_optimization_thread(self):
        """启动自动优化线程"""
        self._optimization_thread = threading.Thread(target=self._auto_optimize, daemon=True)
        self._optimization_thread.start()
        logger.info("系统自动优化线程启动成功")

    def _start_server_monitoring_thread(self):
        """启动服务器监控线程"""
        self._monitoring_thread = threading.Thread(target=self._monitor_servers, daemon=True)
        self._monitoring_thread.start()
        logger.info("服务器监控线程启动成功")

    def scan_projects(self, root_path):
        """扫描项目

        Args:
            root_path: 根目录路径

        Returns:
            list: 项目列表
        logger.info(f"开始扫描项目: {root_path}")
        projects = []

        try:
            for item in os.listdir(root_path):
                item_path = os.path.join(root_path, item)
                if os.path.isdir(item_path):
                    # 检查是否为项目目录
                    if self._is_project_directory(item_path):
                        project_info = self._analyze_project(item_path, item)
                        projects.append(project_info)
                        self.projects[item] = project_info
                        logger.info(f"发现项目: {item}")
        except Exception as e:
            logger.error(f"扫描项目失败: {str(e)}")

        logger.info(f"扫描完成，共发现 {len(projects)} 个项目")
        return projects

    def _is_project_directory(self, path):
        """检查目录是否为项目目录

        Args:
            path: 目录路径

            bool: 是否为项目目录
        project_indicators = [
            'package.json', 'requirements.txt', 'setup.py', 'Cargo.toml',
            'go.mod', 'pom.xml', 'build.gradle', 'Gemfile', 'Pipfile'
        ]

        for indicator in project_indicators:
            if os.path.exists(os.path.join(path, indicator)):
                return True

        return False

    def _analyze_project(self, path, name):
        """分析项目

        Args:
            path: 项目路径
            name: 项目名称

            dict: 项目信息
        project_info = {
            'name': name,
            'path': path,
            'type': self._detect_project_type(path),
            'size': self._calculate_directory_size(path),
            'file_count': self._count_files(path),
            'last_modified': datetime.now().isoformat(),
            'optimization_status': 'pending',
            'issues': [],
            'recommendations': []
        }

        # 检测项目问题
        project_info['issues'] = self._detect_project_issues(path, project_info['type'])

        # 生成优化建议
        project_info['recommendations'] = self._generate_optimization_recommendations(
            path, project_info['type'], project_info['issues']
        )

        return project_info

    def _detect_project_type(self, path):
        """检测项目类型

        Args:
            path: 项目路径

        Returns:
            str: 项目类型
            return 'nodejs'
        elif os.path.exists(os.path.join(path, 'requirements.txt')):
            return 'python'
            return 'python'
        elif os.path.exists(os.path.join(path, 'Cargo.toml')):
            return 'rust'
        elif os.path.exists(os.path.join(path, 'go.mod')):
            return 'go'
        elif os.path.exists(os.path.join(path, 'pom.xml')):
            return 'java'
        elif os.path.exists(os.path.join(path, 'build.gradle')):
            return 'java'
        elif os.path.exists(os.path.join(path, 'Gemfile')):
        else:
            return 'unknown'

    def _calculate_directory_size(self, path):
        """计算目录大小

        Args:
            path: 目录路径
        Returns:
            int: 目录大小（字节）
        total_size = 0
            for dirpath, dirnames, filenames in os.walk(path):
                for filename in filenames:
                    filepath = os.path.join(dirpath, filename)
                    try:
                    except:
                        pass
        except:
            pass
        return total_size
    def _count_files(self, path):
        """计算文件数量

            path: 目录路径

        Returns:
            int: 文件数量
        count = 0
        try:
                count += len(filenames)
        except:
            pass

        """检测项目问题
        Args:
            path: 项目路径
            project_type: 项目类型
        Returns:
            list: 问题列表
        issues = []

        if project_type == 'nodejs':
            node_modules = os.path.join(path, 'node_modules')
            if os.path.exists(node_modules):
                size = self._calculate_directory_size(node_modules)
                    'type': 'large_dependency_folder',
                    'severity': 'medium',
                })

            if os.path.exists(pycache):
                issues.append({
                    'type': 'pycache_exists',
                    'severity': 'low',
                    'description': '__pycache__目录存在，可以清理'
                })

        # 检查是否有日志文件
        log_files = self._find_large_log_files(path)
        if log_files:
            issues.append({
                'type': 'large_log_files',
                'severity': 'medium',
                'description': f'发现 {len(log_files)} 个过大的日志文件',
                'files': log_files
            })

        # 检查依赖配置文件
        if project_type == 'python':
            requirements = os.path.join(path, 'requirements.txt')
            if not os.path.exists(requirements):
                issues.append({
                    'type': 'missing_requirements',
                    'severity': 'high',
                    'description': '缺少requirements.txt文件'
                })

        return issues

    def _find_large_log_files(self, path, max_size_mb=10):

        Args:
            path: 目录路径
            max_size_mb: 最大文件大小（MB）

        Returns:
            list: 大日志文件列表
        large_files = []
            for dirpath, dirnames, filenames in os.walk(path):
                dirnames[:] = [d for d in dirnames if d not in ['node_modules', '.git', '__pycache__']]

                    if filename.endswith('.log'):
                        filepath = os.path.join(dirpath, filename)
                        try:
                            size = os.path.getsize(filepath)
                            if size > max_size_mb * 1024 * 1024:
                                large_files.append({
                                })
                        except:
                            pass
            pass
        return large_files

    def _generate_optimization_recommendations(self, path, project_type, issues):
        """生成优化建议

        Args:
            project_type: 项目类型
            issues: 问题列表

        Returns:
        recommendations = []

        for issue in issues:
                recommendations.append({
                    'action': 'clean_dependency_cache',
                    'command': self._get_clean_command(project_type)
                })
            elif issue['type'] == 'pycache_exists':
                recommendations.append({
                    'action': 'clean_pycache',
                    'description': '清理Python缓存',
                    'command': 'find . -type d -name __pycache__ -exec rm -rf {} +'
                })

            elif issue['type'] == 'large_log_files':
                    'action': 'rotate_or_clear_logs',
                })

                recommendations.append({
                    'description': '创建requirements.txt文件',
                    'command': 'pip freeze > requirements.txt'
                })

        return recommendations

    def _get_clean_command(self, project_type):
        """获取清理命令

        Args:
            project_type: 项目类型
        Returns:
            str: 清理命令
        commands = {
            'nodejs': 'rm -rf node_modules && npm install',
            'python': 'pip freeze > requirements.txt',
            'rust': 'cargo clean',
            'go': 'go clean -cache',
            'java': 'mvn clean',
        }
        return commands.get(project_type, '')

    def _format_size(self, size):
        """格式化文件大小

        Args:
            size: 字节大小

        Returns:
            str: 格式化后的大小
        for unit in ['B', 'KB', 'MB', 'GB']:
            if size < 1024.0:
            size /= 1024.0
        return f"{size:.2f} TB"

    def optimize_project(self, project_name):

        Args:

        Returns:
            dict: 优化结果
        if project_name not in self.projects:
            return {'status': 'error', 'message': '项目不存在'}

        logger.info(f"开始优化项目: {project_name}")

        result = {
            'project': project_name,
            'optimizations_applied': [],
            'status': 'success'

        try:
            # 应用优化建议
            for recommendation in project['recommendations']:
                action = recommendation['action']

                if action == 'clean_dependency_cache':
                    # 清理依赖缓存
                    cmd = recommendation['command']
                    if cmd:
                        subprocess.run(cmd, shell=True, cwd=project['path'], capture_output=True)
                        result['optimizations_applied'].append({
                            'action': action,
                            'description': recommendation['description'],
                            'status': 'success'
                        })

                elif action == 'clean_pycache':
                    # 清理Python缓存
                    for root, dirs, files in os.walk(project['path']):
                        if '__pycache__' in dirs:
                            pycache_path = os.path.join(root, '__pycache__')
                            import shutil
                            shutil.rmtree(pycache_path)
                            result['optimizations_applied'].append({
                                'action': action,
                                'status': 'success'
                            })

                elif action == 'rotate_or_clear_logs':
                    # 处理日志文件
                    for file_info in project['issues']:
                        if file_info['type'] == 'large_log_files':
                            for log_file in file_info.get('files', []):
                                try:
                                    # 清空日志文件
                                    with open(log_file['path'], 'w') as f:
                                        f.write('')
                                    result['optimizations_applied'].append({
                                        'action': 'clear_log',
                                        'description': f'清空日志文件 {log_file["path"]}',
                                        'status': 'success'
                                    })
                                except Exception as e:
                                    result['optimizations_applied'].append({
                                        'action': 'clear_log',
                                        'description': f'清空日志文件 {log_file["path"]} 失败: {str(e)}',
                                        'status': 'failed'
                                    })

            # 更新项目状态
            project['optimization_status'] = 'completed'
            project['last_optimized'] = datetime.now().isoformat()

            result['end_time'] = datetime.now().isoformat()

            # 记录优化历史
            with self.lock:
                self.optimization_history.append(result)
            logger.info(f"项目 {project_name} 优化完成，应用了 {len(result['optimizations_applied'])} 项优化")

        except Exception as e:
            result['status'] = 'failed'
            result['error'] = str(e)
            logger.error(f"优化项目 {project_name} 失败: {str(e)}")

        return result

    def _auto_optimize(self):
        """自动优化"""
        while True:
            try:
                # 检查系统资源使用情况
                # 如果内存使用率超过80%，进行优化
                if memory.percent > 80:
                    logger.info("检测到内存使用率过高，开始自动优化")

                    # 清理内存缓存
                    self._optimize_memory()

                    # 清理临时文件
                    self._cleanup_temp_files()

                    for project_name in list(self.projects.keys()):
                time.sleep(300)  # 每5分钟检查一次
            except Exception as e:
                logger.error(f"自动优化失败: {str(e)}")
                time.sleep(300)
    def _optimize_memory(self):
        """优化内存"""

        try:
            # 触发垃圾回收
            import gc
            gc.collect()

        except Exception as e:
            logger.error(f"内存优化失败: {str(e)}")

    def _cleanup_temp_files(self):
        """清理临时文件"""

        temp_dirs = [
            '/tmp',
            '/var/tmp',
        ]

        for temp_dir in temp_dirs:
            if os.path.exists(temp_dir):
                try:
                    count = 0
                    for item in os.listdir(temp_dir):
                            if os.path.isfile(item_path):
                                # 删除超过24小时的临时文件
                                if time.time() - os.path.getmtime(item_path) > 86400:
                                    os.remove(item_path)
                                    count += 1
                            elif os.path.isdir(item_path):
                                # 删除超过24小时的临时目录
                                if time.time() - os.path.getmtime(item_path) > 86400:
                                    import shutil
                                    shutil.rmtree(item_path)
                                    count += 1
                        except:
                            pass
                    logger.info(f"从 {temp_dir} 清理了 {count} 个临时文件")
                    logger.error(f"清理临时文件失败: {str(e)}")

    def _monitor_servers(self):
        """监控服务器"""
        while True:
                # 获取服务器指标
                cpu_percent = psutil.cpu_percent(interval=1)
                memory = psutil.virtual_memory()
                net_io = psutil.net_io_counters()

                self.server_metrics = {
                    'timestamp': datetime.now().isoformat(),
                    'cpu': {
                        'usage': cpu_percent,
                        'count': psutil.cpu_count(),
                        'freq': psutil.cpu_freq()._asdict() if psutil.cpu_freq() else None
                    },
                        'total': memory.total,
                        'available': memory.available,
                        'used': memory.used,
                        'percent': memory.percent
                    },
                    'disk': {
                        'total': disk.total,
                        'used': disk.used,
                        'free': disk.free,
                        'percent': disk.percent
                    'network': {
                        'bytes_sent': net_io.bytes_sent,
                        'bytes_recv': net_io.bytes_recv,
                        'packets_sent': net_io.packets_sent,
                        'packets_recv': net_io.packets_recv
                }

                # 检查是否需要优化
                if memory.percent > 85 or cpu_percent > 90:
                    logger.warning(f"服务器资源使用率过高: CPU={cpu_percent}%, Memory={memory.percent}%")
                    self._trigger_emergency_optimization()

            except Exception as e:
                logger.error(f"服务器监控失败: {str(e)}")
                time.sleep(30)

    def _trigger_emergency_optimization(self):
        """触发紧急优化"""

        # 立即清理内存
        self._optimize_memory()

        # 清理临时文件

        # 记录紧急优化
        with self.lock:
            self.optimization_history.append({
                'type': 'emergency',
                'timestamp': datetime.now().isoformat(),
                'metrics_before': self.server_metrics
            })

    def get_optimization_report(self):
        """获取优化报告

        Returns:
            dict: 优化报告
        report = {
            'generated_at': datetime.now().isoformat(),
            'total_projects': len(self.projects),
            'projects': list(self.projects.values()),
            'optimization_history': self.optimization_history[-50:],  # 最近50条记录
            'server_metrics': self.server_metrics,
        }
        return report

    def get_server_metrics(self):
        """获取服务器指标

        Returns:
        return self.server_metrics

# 创建系统优化器实例
system_optimizer = SystemOptimizer()
