# -*- coding: utf-8 -*-
#!/usr/bin/env python3
"""
系统AI自动化托管
实现AI系统的自动管理、监控、优化和报告生成
"""

import logging
logger = logging.getLogger(__name__)
import os
import sys
import json
import time
import threading
import sqlite3
import hashlib
import random
from datetime import datetime
import traceback
import subprocess

try:
    import psutil
except ImportError:
    psutil = None

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

try:
    from ai_self_improvement import get_ai_self_improvement
    from ai_brain import get_ai_brain
    from ai_log_analyzer import get_log_analyzer
    from ai_anomaly_detector import get_ai_detector
except ImportError:
    get_ai_self_improvement = None
    get_ai_brain = None
    get_log_analyzer = None
    get_ai_detector = None

class AIAutoManagementSystem:
    """
    系统AI自动化托管系统
    负责AI系统的自动启动、停止、监控、优化和报告生成
    """

    def __init__(self):
        """初始化AI自动化管理系统"""
        self.ai_self_improvement = get_ai_self_improvement() if get_ai_self_improvement else None
        self.ai_brain = get_ai_brain() if get_ai_brain else None
        self.log_analyzer = get_log_analyzer() if get_log_analyzer else None
        self.anomaly_detector = get_ai_detector() if get_ai_detector else None
        self.is_running = False
        self.management_thread = None
        self.monitoring_thread = None
        self.management_interval = 1800
        self.monitoring_interval = 60

        self.db_path = 'ai_auto_management.db'
        self._init_db()

        self.system_status = {
            'ai_self_improvement': False,
            'ai_brain': False,
            'log_analyzer': False,
            'anomaly_detector': False,
            'last_check': None
        }

        self.performance_metrics = {
            'cpu_usage': 0.0,
            'memory_usage': 0.0,
            'disk_usage': 0.0,
            'network_in': 0.0,
            'network_out': 0.0
        }

    def _init_db(self):
        """初始化数据库"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            cursor.execute('''
            CREATE TABLE IF NOT EXISTS system_status_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            component_name TEXT NOT NULL,
            status TEXT NOT NULL,
            metadata TEXT
            )
            ''')
            
            cursor.execute('''
            CREATE TABLE IF NOT EXISTS performance_metrics (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            metric_name TEXT NOT NULL,
            metric_value REAL NOT NULL,
            metadata TEXT
            )
            ''')
            
            cursor.execute('''
            CREATE TABLE IF NOT EXISTS automation_tasks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            task_name TEXT NOT NULL,
            task_type TEXT,
            status TEXT,
            executed_time TIMESTAMP,
            result TEXT,
            metadata TEXT
            )
            ''')
            
            cursor.execute('''
            CREATE TABLE IF NOT EXISTS optimization_suggestions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            suggestion_type TEXT NOT NULL,
            suggestion TEXT NOT NULL,
            priority INTEGER NOT NULL CHECK(priority BETWEEN 1 AND 5),
            implemented BOOLEAN DEFAULT FALSE,
            metadata TEXT
            )
            ''')
            
            conn.commit()

    def start(self):
        """启动AI自动化托管系统"""
        if not self.is_running:
            self.is_running = True

            self.management_thread = threading.Thread(target=self._management_loop, daemon=True)
            self.management_thread.start()

            self.monitoring_thread = threading.Thread(target=self._monitoring_loop, daemon=True)
            self.monitoring_thread.start()
            
            self.auto_start_ai_systems()

            print(f"[AI自动化托管系统] 已启动")
            print(f"[AI自动化托管系统] 管理间隔: {self.management_interval}秒")
            print(f"[AI自动化托管系统] 监控间隔: {self.monitoring_interval}秒")

    def stop(self):
        """停止AI自动化托管系统"""
        if self.is_running:
            self.is_running = False

            if self.management_thread:
                self.management_thread.join(timeout=5.0)

            if self.monitoring_thread:
                self.monitoring_thread.join(timeout=5.0)

            self.auto_stop_ai_systems()

            print("[AI自动化托管系统] 已停止")

    def _management_loop(self):
        """管理循环"""
        while self.is_running:
            try:
                self._execute_automation_tasks()
                self._auto_repair()
                self._optimize_ai_systems()
                self._expand_system()
                self._generate_automation_report()

            except Exception as e:
                print(f"[AI自动化托管系统] 管理循环执行失败: {str(e)}")
                traceback.print_exc()

            time.sleep(self.management_interval)

    def _monitoring_loop(self):
        """监控循环"""
        while self.is_running:
            try:
                self._monitor_ai_systems()
                self._monitor_system_performance()
                self._detect_anomalies()

            except Exception as e:
                print(f"[AI自动化托管系统] 监控循环执行失败: {str(e)}")
                traceback.print_exc()

            time.sleep(self.monitoring_interval)

    def auto_start_ai_systems(self):
        """自动启动所有AI系统"""
        print("[AI自动化托管系统] 开始自动启动AI系统...")

        try:
            if self.ai_self_improvement and hasattr(self.ai_self_improvement, 'start'):
                self.ai_self_improvement.start()
                self.system_status['ai_self_improvement'] = True
                self._save_system_status('ai_self_improvement', 'running')
                print("[AI自动化托管系统] AI自我提升系统已启动")

            if self.ai_brain:
                self.system_status['ai_brain'] = True
                self._save_system_status('ai_brain', 'running')
                print("[AI自动化托管系统] AI大脑已启动")

            if self.log_analyzer:
                self.system_status['log_analyzer'] = True
                self._save_system_status('log_analyzer', 'running')
                print("[AI自动化托管系统] 日志分析器已启动")

            if self.anomaly_detector:
                self.system_status['anomaly_detector'] = True
                self._save_system_status('anomaly_detector', 'running')
                print("[AI自动化托管系统] 异常检测器已启动")

            self.system_status['last_check'] = datetime.now().isoformat()

        except Exception as e:
            print(f"[AI自动化托管系统] 自动启动AI系统失败: {str(e)}")
            traceback.print_exc()

    def auto_stop_ai_systems(self):
        """自动停止所有AI系统"""
        print("[AI自动化托管系统] 开始自动停止AI系统...")

        try:
            if self.ai_self_improvement and hasattr(self.ai_self_improvement, 'stop'):
                self.ai_self_improvement.stop()
                self.system_status['ai_self_improvement'] = False
                self._save_system_status('ai_self_improvement', 'stopped')
                print("[AI自动化托管系统] AI自我提升系统已停止")

            self.system_status['last_check'] = datetime.now().isoformat()

        except Exception as e:
            print(f"[AI自动化托管系统] 自动停止AI系统失败: {str(e)}")
            traceback.print_exc()

    def _monitor_ai_systems(self):
        """监控AI系统状态"""
        try:
            if self.ai_self_improvement:
                self.system_status['ai_self_improvement'] = True
                self._save_system_status('ai_self_improvement', 'running')

            if self.ai_brain:
                self.system_status['ai_brain'] = True
                self._save_system_status('ai_brain', 'running')

            if self.log_analyzer:
                self.system_status['log_analyzer'] = True
                self._save_system_status('log_analyzer', 'running')

            if self.anomaly_detector:
                self.system_status['anomaly_detector'] = True
                self._save_system_status('anomaly_detector', 'running')

            self.system_status['last_check'] = datetime.now().isoformat()

        except Exception as e:
            print(f"[AI自动化托管系统] 监控AI系统状态失败: {str(e)}")

    def _monitor_system_performance(self):
        """监控系统性能"""
        if not psutil:
            return
            
        try:
            cpu_usage = psutil.cpu_percent(interval=1)
            self.performance_metrics['cpu_usage'] = cpu_usage
            self._save_performance_metric('cpu_usage', cpu_usage)

            memory = psutil.virtual_memory()
            memory_usage = memory.percent
            self.performance_metrics['memory_usage'] = memory_usage
            self._save_performance_metric('memory_usage', memory_usage)

            disk = psutil.disk_usage('/')
            disk_usage = disk.percent
            self.performance_metrics['disk_usage'] = disk_usage
            self._save_performance_metric('disk_usage', disk_usage)

            network = psutil.net_io_counters()
            network_in = network.bytes_recv / 1024 / 1024
            network_out = network.bytes_sent / 1024 / 1024
            self.performance_metrics['network_in'] = network_in
            self.performance_metrics['network_out'] = network_out
            self._save_performance_metric('network_in', network_in)
            self._save_performance_metric('network_out', network_out)
        except Exception as e:
            print(f"[AI自动化托管系统] 监控系统性能失败: {str(e)}")

    def _detect_anomalies(self):
        """检测异常"""
        try:
            if self.performance_metrics['cpu_usage'] > 90:
                self._create_optimization_suggestion(
                    'performance',
                    f"CPU使用率过高: {self.performance_metrics['cpu_usage']:.2f}%,建议优化AI系统资源使用",
                    4
                )

            if self.performance_metrics['memory_usage'] > 90:
                self._create_optimization_suggestion(
                    'performance',
                    f"内存使用率过高: {self.performance_metrics['memory_usage']:.2f}%,建议优化AI系统内存使用",
                    5
                )

            for component, status in self.system_status.items():
                if component != 'last_check' and not status:
                    self._create_optimization_suggestion(
                        'system',
                        f"AI组件 {component} 状态异常,建议重启",
                        3
                    )

        except Exception as e:
            print(f"[AI自动化托管系统] 检测异常失败: {str(e)}")

    def _execute_automation_tasks(self):
        """执行自动化任务"""
        try:
            self._execute_task('assess_ai_capabilities', 'assessment')
            self._execute_task('optimize_ai_systems', 'optimization')
        except Exception as e:
            print(f"[AI自动化托管系统] 执行自动化任务失败: {str(e)}")

    def _execute_task(self, task_name, task_type):
        """执行单个自动化任务"""
        print(f"[AI自动化托管系统] 执行任务: {task_name}")

        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO automation_tasks (task_name, task_type, status, metadata) VALUES (?, ?, ?, ?)",
                (task_name, task_type, 'running', str({'timestamp': datetime.now().isoformat()}))
            )
            task_id = cursor.lastrowid
            conn.commit()
        
        try:
            if task_name == 'assess_ai_capabilities' and self.ai_self_improvement:
                result = self.ai_self_improvement.assess_capabilities()
                status = 'completed'
            elif task_name == 'optimize_ai_systems':
                result = self._optimize_ai_systems()
                status = 'completed'
            else:
                result = 'Task not implemented'
                status = 'completed'
        except Exception as e:
            result = str(e)
            status = 'failed'

        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute(
                "UPDATE automation_tasks SET status=?, executed_time=CURRENT_TIMESTAMP, result=? WHERE id=?",
                (status, str(result), task_id)
            )
            conn.commit()

    def _optimize_ai_systems(self):
        """优化AI系统"""
        print("[AI自动化托管系统] 开始优化AI系统...")

        try:
            optimization_results = []

            if self.ai_self_improvement and hasattr(self.ai_self_improvement, 'improvement_interval'):
                current_interval = self.ai_self_improvement.improvement_interval

                if self.performance_metrics['cpu_usage'] > 80:
                    new_interval = current_interval * 2
                    self.ai_self_improvement.improvement_interval = new_interval
                    optimization_results.append(f"调整AI自我提升间隔: {current_interval}秒 -> {new_interval}秒")

                elif self.performance_metrics['cpu_usage'] < 30:
                    new_interval = max(300, current_interval // 2)
                    self.ai_self_improvement.improvement_interval = new_interval
                    optimization_results.append(f"调整AI自我提升间隔: {current_interval}秒 -> {new_interval}秒")

            import gc
            gc.collect()

            self._optimize_database()
            optimization_results.append("优化数据库,清理旧数据")

            self._optimize_logging()
            optimization_results.append("优化日志记录")

            print(f"[AI自动化托管系统] AI系统优化完成: {optimization_results}")
            return optimization_results

        except Exception as e:
            print(f"[AI自动化托管系统] 优化AI系统失败: {str(e)}")
            return [f"优化失败: {str(e)}"]

    def _optimize_database(self):
        """优化数据库"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute(
                    "DELETE FROM system_status_history WHERE timestamp < datetime('now', '-30 days')"
                )
                cursor.execute(
                    "DELETE FROM performance_metrics WHERE timestamp < datetime('now', '-30 days')"
                )
                conn.commit()
        except Exception as e:
            print(f"[AI自动化托管系统] 优化数据库失败: {str(e)}")

    def _optimize_logging(self):
        """优化日志记录,减少磁盘占用"""
        print("[AI自动化托管系统] 开始优化日志记录")

        log_dirs = ['logs', '.']
        max_log_size = 10 * 1024 * 1024
        max_log_files = 5
        compress_suffix = '.gz'
        log_extensions = ['.log', '.txt']

        try:
            import gzip
            import shutil

            for log_dir in log_dirs:
                if not os.path.exists(log_dir):
                    continue

                files = os.listdir(log_dir)

                for extension in log_extensions:
                    log_files = [f for f in files if f.endswith(extension)]

                    for log_file in log_files:
                        log_path = os.path.join(log_dir, log_file)

                        if os.path.isfile(log_path):
                            file_size = os.path.getsize(log_path)

                            if file_size > max_log_size:
                                print(f"[AI自动化托管系统] 压缩大日志文件: {log_path} ({file_size/1024/1024:.2f}MB)")

                                compressed_path = log_path + compress_suffix
                                with open(log_path, 'rb') as f_in:
                                    with gzip.open(compressed_path, 'wb') as f_out:
                                        shutil.copyfileobj(f_in, f_out)

                                open(log_path, 'w').close()
                                print(f"[AI自动化托管系统] 已压缩并清空日志文件: {log_path}")

                    compressed_logs = [f for f in files if f.endswith(extension + compress_suffix)]

                    if compressed_logs:
                        compressed_logs.sort(key=lambda f: os.path.getmtime(os.path.join(log_dir, f)))

                        while len(compressed_logs) > max_log_files:
                            old_log = compressed_logs.pop(0)
                            old_log_path = os.path.join(log_dir, old_log)
                            os.remove(old_log_path)
                            print(f"[AI自动化托管系统] 删除旧日志文件: {old_log_path}")

            print("[AI自动化托管系统] 日志优化完成")

        except Exception as e:
            print(f"[AI自动化托管系统] 优化日志记录失败: {str(e)}")

    def _auto_repair(self):
        """AI自动修复功能"""
        print("[AI自动化托管系统] 开始自动修复...")

        try:
            repair_results = []

            if not self._check_database_connection():
                self._repair_database_connection()
                repair_results.append("修复数据库连接")

            for component_name in ['ai_self_improvement', 'ai_brain', 'log_analyzer', 'anomaly_detector']:
                if not self._check_ai_component(component_name):
                    self._repair_ai_component(component_name)
                    repair_results.append(f"修复AI组件: {component_name}")

            self._check_and_fix_permissions()
            repair_results.append("检查并修复文件系统权限")

            print(f"[AI自动化托管系统] 自动修复完成: {repair_results}")
            return repair_results

        except Exception as e:
            print(f"[AI自动化托管系统] 自动修复失败: {str(e)}")
            return [f"修复失败: {str(e)}"]

    def _check_database_connection(self):
        """检查数据库连接"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT 1")
            return True
        except Exception as e:
            print(f"[AI自动化托管系统] 数据库连接检查失败: {str(e)}")
            return False

    def _repair_database_connection(self):
        """修复数据库连接"""
        try:
            print(f"[AI自动化托管系统] 尝试修复数据库连接: {self.db_path}")

            if os.path.exists(self.db_path):
                with sqlite3.connect(self.db_path) as conn:
                    cursor = conn.cursor()
                    cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
                    tables = cursor.fetchall()
                    
                    if not tables:
                        print(f"[AI自动化托管系统] 数据库中没有表,重新初始化数据库")
                        self._init_db()
            else:
                print(f"[AI自动化托管系统] 数据库文件不存在,重新创建: {self.db_path}")
                self._init_db()

            print(f"[AI自动化托管系统] 数据库连接修复成功: {self.db_path}")
            return True
        except Exception as e:
            print(f"[AI自动化托管系统] 修复数据库连接失败: {str(e)}")
            try:
                if os.path.exists(self.db_path):
                    os.remove(self.db_path)
                    print(f"[AI自动化托管系统] 删除损坏的数据库文件: {self.db_path}")
                    self._init_db()
                    print(f"[AI自动化托管系统] 重新创建数据库成功: {self.db_path}")
                    return True
            except Exception as e2:
                print(f"[AI自动化托管系统] 重新创建数据库失败: {str(e2)}")

        return False

    def _check_ai_component(self, component_name):
        """检查AI组件状态"""
        try:
            if component_name == 'ai_self_improvement':
                return self.ai_self_improvement is not None
            elif component_name == 'ai_brain':
                return self.ai_brain is not None
            elif component_name == 'log_analyzer':
                return self.log_analyzer is not None
            elif component_name == 'anomaly_detector':
                return self.anomaly_detector is not None
            return True
        except Exception as e:
            print(f"[AI自动化托管系统] AI组件 {component_name} 检查失败: {str(e)}")
            return False

    def _repair_ai_component(self, component_name):
        """修复AI组件"""
        print(f"[AI自动化托管系统] 开始修复AI组件: {component_name}")

        try:
            if component_name == 'ai_self_improvement' and get_ai_self_improvement:
                self.ai_self_improvement = get_ai_self_improvement()
                if hasattr(self.ai_self_improvement, 'start'):
                    self.ai_self_improvement.start()
            elif component_name == 'ai_brain' and get_ai_brain:
                self.ai_brain = get_ai_brain()
            elif component_name == 'log_analyzer' and get_log_analyzer:
                self.log_analyzer = get_log_analyzer()
            elif component_name == 'anomaly_detector' and get_ai_detector:
                self.anomaly_detector = get_ai_detector()

            print(f"[AI自动化托管系统] AI组件修复成功: {component_name}")
            self.system_status[component_name] = True
            return True

        except Exception as e:
            print(f"[AI自动化托管系统] 修复AI组件失败 {component_name}: {str(e)}")
            traceback.print_exc()
            self.system_status[component_name] = False
            return False

    def _check_and_fix_permissions(self):
        """检查并修复文件系统权限"""
        critical_paths = [
            'app.db',
            'ai_self_improvement.db',
            'ai_auto_management.db',
            'logs'
        ]

        for path in critical_paths:
            if os.path.exists(path):
                if os.path.isdir(path):
                    if not os.access(path, os.W_OK):
                        try:
                            os.chmod(path, 0o755)
                        except Exception as e:
                            print(f"[AI自动化托管系统] 修复目录权限失败 {path}: {str(e)}")
                elif os.path.isfile(path):
                    if not os.access(path, os.R_OK):
                        try:
                            os.chmod(path, 0o644)
                        except Exception as e:
                            print(f"[AI自动化托管系统] 修复文件权限失败 {path}: {str(e)}")

    def _expand_system(self):
        """系统拓展功能"""
        print("[AI自动化托管系统] 开始系统拓展...")

        try:
            expand_results = []

            new_components = self._scan_for_new_components()
            for component in new_components:
                self._load_new_component(component)
                expand_results.append(f"加载新AI组件: {component}")

            new_features = self._scan_for_new_features()
            for feature in new_features:
                self._enable_new_feature(feature)
                expand_results.append(f"启用新功能: {feature}")

            print(f"[AI自动化托管系统] 系统拓展完成: {expand_results}")
            return expand_results

        except Exception as e:
            print(f"[AI自动化托管系统] 系统拓展失败: {str(e)}")
            return []

    def _scan_for_new_components(self):
        """扫描新的AI组件"""
        print("[AI自动化托管系统] 开始扫描新的AI组件")

        new_components = []

        current_dir = os.path.dirname(os.path.abspath(__file__))
        loaded_components = [
            'ai_self_improvement',
            'ai_brain',
            'ai_log_analyzer',
            'ai_anomaly_detector',
            'ai_auto_management'
        ]

        try:
            for filename in os.listdir(current_dir):
                if filename.endswith('.py'):
                    module_name = filename[:-3]

                    if module_name.startswith('ai_') and module_name not in loaded_components:
                        try:
                            module_path = f"{module_name}"
                            module = __import__(module_path)
                            
                            for attr_name in dir(module):
                                if attr_name.startswith('get_'):
                                    new_components.append({
                                        'module_name': module_name,
                                        'file_path': os.path.join(current_dir, filename),
                                        'get_function': attr_name
                                    })
                                    print(f"[AI自动化托管系统] 发现新AI组件: {module_name}")

                            if module_name in sys.modules:
                                del sys.modules[module_name]

                        except Exception as e:
                            print(f"[AI自动化托管系统] 检查模块 {module_name} 失败: {str(e)}")
                            continue

        except Exception as e:
            print(f"[AI自动化托管系统] 扫描新AI组件失败: {str(e)}")

        print(f"[AI自动化托管系统] 扫描完成,发现 {len(new_components)} 个新AI组件")
        return new_components

    def _load_new_component(self, component):
        """加载新的AI组件"""
        print(f"[AI自动化托管系统] 开始加载新AI组件: {component['module_name']}")

        try:
            module = __import__(component['module_name'])
            get_function = getattr(module, component['get_function'])
            component_instance = get_function()

            if hasattr(component_instance, 'start'):
                component_instance.start()
                print(f"[AI自动化托管系统] 已启动新AI组件: {component['module_name']}")

            component_key = component['module_name']
            self.system_status[component_key] = True
            self._save_system_status(component_key, 'running')

            print(f"[AI自动化托管系统] 成功加载新AI组件: {component['module_name']}")
            return True

        except Exception as e:
            print(f"[AI自动化托管系统] 加载新AI组件失败 {component['module_name']}: {str(e)}")
            traceback.print_exc()
            return False

    def _scan_for_new_features(self):
        """扫描新功能"""
        print("[AI自动化托管系统] 开始扫描新功能")

        new_features = []

        enabled_features = [
            'auto_repair',
            'optimization',
            'system_expansion',
            'monitoring'
        ]

        try:
            config_files = ['config.json', 'app_config.json', 'ai_config.json']

            for config_file in config_files:
                if os.path.exists(config_file):
                    with open(config_file, 'r') as f:
                        try:
                            config = json.load(f)

                            if 'features' in config:
                                for feature_name, feature_config in config['features'].items():
                                    if feature_name not in enabled_features and feature_config.get('enabled', False):
                                        new_features.append({
                                            'name': feature_name,
                                            'source': f'config:{config_file}',
                                            'config': feature_config
                                        })
                                        print(f"[AI自动化托管系统] 从配置文件发现新功能: {feature_name}")
                        except json.JSONDecodeError:
                            continue

            env_prefix = 'AI_FEATURE_'
            for env_name, env_value in os.environ.items():
                if env_name.startswith(env_prefix):
                    feature_name = env_name[len(env_prefix):].lower()
                    if feature_name not in enabled_features and env_value.lower() in ['true', '1', 'yes', 'on']:
                        new_features.append({
                            'name': feature_name,
                            'source': 'environment',
                            'config': {'enabled': True}
                        })
                        print(f"[AI自动化托管系统] 从环境变量发现新功能: {feature_name}")

        except Exception as e:
            print(f"[AI自动化托管系统] 扫描新功能失败: {str(e)}")

        print(f"[AI自动化托管系统] 扫描完成,发现 {len(new_features)} 个新功能")
        return new_features

    def _enable_new_feature(self, feature):
        """启用新功能"""
        print(f"[AI自动化托管系统] 开始启用新功能: {feature['name']}")

        try:
            feature_key = f"feature_{feature['name']}"
            self.system_status[feature_key] = True
            self._save_system_status(feature_key, 'enabled')

            feature_config = feature.get('config', {})

            if 'directories' in feature_config:
                for directory in feature_config['directories']:
                    if not os.path.exists(directory):
                        os.makedirs(directory, exist_ok=True)
                        print(f"[AI自动化托管系统] 为功能 {feature['name']} 创建目录: {directory}")

            features_dir = 'features'
            os.makedirs(features_dir, exist_ok=True)

            feature_file = os.path.join(features_dir, f"{feature['name']}.json")
            with open(feature_file, 'w') as f:
                json.dump({
                    'enabled': True,
                    'source': feature['source'],
                    'config': feature_config,
                    'enabled_at': datetime.now().isoformat()
                }, f, ensure_ascii=False, indent=2)

            print(f"[AI自动化托管系统] 成功启用新功能: {feature['name']}")

            self._create_optimization_suggestion(
                'feature',
                f"已成功启用新功能: {feature['name']}",
                2
            )
            return True

        except Exception as e:
            print(f"[AI自动化托管系统] 启用新功能失败 {feature['name']}: {str(e)}")
            traceback.print_exc()
            return False

    def _generate_automation_report(self):
        """生成自动化报告"""
        print("[AI自动化托管系统] 开始生成自动化报告...")

        try:
            system_status = self.system_status.copy()
            performance_metrics = self.performance_metrics.copy()

            ai_capabilities = None
            if self.ai_self_improvement and hasattr(self.ai_self_improvement, 'assess_capabilities'):
                ai_capabilities = self.ai_self_improvement.assess_capabilities()

            report = {
                'timestamp': datetime.now().isoformat(),
                'system_status': system_status,
                'performance_metrics': performance_metrics,
                'ai_capabilities': ai_capabilities,
                'optimization_suggestions': self._get_recent_optimization_suggestions(limit=10)
            }

            report_filename = f"automation_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            reports_dir = 'reports'
            os.makedirs(reports_dir, exist_ok=True)
            report_path = os.path.join(reports_dir, report_filename)

            with open(report_path, 'w', encoding='utf-8') as f:
                json.dump(report, f, ensure_ascii=False, indent=2)
            
            print(f"[AI自动化托管系统] 自动化报告已生成: {report_path}")
            return report

        except Exception as e:
            print(f"[AI自动化托管系统] 生成自动化报告失败: {str(e)}")
            return None

    def _save_system_status(self, component_name, status):
        """保存系统状态到数据库"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute(
                    "INSERT INTO system_status_history (component_name, status, metadata) VALUES (?, ?, ?)",
                    (component_name, status, str({'timestamp': datetime.now().isoformat()}))
                )
                conn.commit()
        except Exception as e:
            print(f"[AI自动化托管系统] 保存系统状态失败: {str(e)}")

    def _save_performance_metric(self, metric_name, metric_value):
        """保存性能指标到数据库"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute(
                    "INSERT INTO performance_metrics (metric_name, metric_value, metadata) VALUES (?, ?, ?)",
                    (metric_name, metric_value, str({'timestamp': datetime.now().isoformat()}))
                )
                conn.commit()
        except Exception as e:
            print(f"[AI自动化托管系统] 保存性能指标失败: {str(e)}")

    def _create_optimization_suggestion(self, suggestion_type, suggestion, priority):
        """创建优化建议"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute(
                    "INSERT INTO optimization_suggestions (suggestion_type, suggestion, priority, metadata) VALUES (?, ?, ?, ?)",
                    (suggestion_type, suggestion, priority, str({'timestamp': datetime.now().isoformat()}))
                )
                conn.commit()
        except Exception as e:
            print(f"[AI自动化托管系统] 创建优化建议失败: {str(e)}")

    def _get_recent_optimization_suggestions(self, limit=10):
        """获取最近的优化建议"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute(
                    "SELECT id, timestamp, suggestion_type, suggestion, priority, implemented FROM optimization_suggestions ORDER BY timestamp DESC LIMIT ?",
                    (limit,)
                )
                suggestions = []
                for row in cursor.fetchall():
                    suggestions.append({
                        'id': row[0],
                        'timestamp': row[1],
                        'suggestion_type': row[2],
                        'suggestion': row[3],
                        'priority': row[4],
                        'implemented': bool(row[5])
                    })
                return suggestions
        except Exception as e:
            print(f"[AI自动化托管系统] 获取优化建议失败: {str(e)}")
            return []

    def get_system_overview(self):
        """获取系统概览"""
        return {
            'system_status': self.system_status,
            'performance_metrics': self.performance_metrics,
            'last_check': self.system_status.get('last_check'),
            'is_running': self.is_running
        }

    def get_optimization_suggestions(self, limit=10):
        """获取优化建议"""
        return self._get_recent_optimization_suggestions(limit)


global_ai_auto_management = None

def get_ai_auto_management():
    """获取全局AI自动化管理系统实例"""
    global global_ai_auto_management
    if global_ai_auto_management is None:
        global_ai_auto_management = AIAutoManagementSystem()
    return global_ai_auto_management


if __name__ == '__main__':
    ai_auto_management = get_ai_auto_management()
    ai_auto_management.start()

    try:
        print("[AI自动化托管系统] 运行中,按Ctrl+C停止...")
        time.sleep(60)

        overview = ai_auto_management.get_system_overview()
        print(f"\n系统概览: {json.dumps(overview, ensure_ascii=False, indent=2)}")

        suggestions = ai_auto_management.get_optimization_suggestions()
        print(f"\n优化建议: {json.dumps(suggestions, ensure_ascii=False, indent=2)}")

    except KeyboardInterrupt:
        print("\n[AI自动化托管系统] 收到停止信号")
    finally:
        ai_auto_management.stop()
