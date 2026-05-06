#!/usr/bin/env python3
"""
服务器性能优化AI - 实时监控并优化服务器性能

import os
import time
import threading
import psutil
# JSON import removed - using database
from datetime import datetime
from utils.logging import logger
from utils.db import db_manager
from config.config import config

class ServerOptimizerAI:
    """服务器性能优化AI"""

    _instance = None
    _lock = threading.Lock()

    def __new__(cls):
        if not cls._instance:
            with cls._lock:
                if not cls._instance:
                    cls._instance._initialize()
        return cls._instance

    def _initialize(self):
        """初始化服务器优化AI"""
        self.monitoring_enabled = True
        self.optimization_enabled = True
        self.last_optimization = 0
        self.optimization_interval = 300  # 5分钟
        self.thresholds = {
            'cpu': 80.0,  # CPU使用率阈值
            'memory': 85.0,  # 内存使用率阈值
            'disk': 90.0,  # 磁盘使用率阈值
            'network': 1024 * 1024 * 1024  # 网络流量阈值 (1GB)
        }

        # 性能数据
        self.performance_data = {
            'cpu': [],
            'memory': [],
            'disk': [],
            'network': [],
            'processes': [],
            'optimizations': []
        }

        self._initialize_database()

        # 启动监控线程
        self._start_monitoring_threads()

        logger.info("服务器性能优化AI初始化成功")

    def _initialize_database(self):
        """初始化数据库表"""
        try:
            # 服务器性能数据表
            db_manager.execute('''
                CREATE TABLE IF NOT EXISTS server_performance (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TEXT NOT NULL,
                    cpu_usage REAL NOT NULL,
                    memory_usage REAL NOT NULL,
                    memory_available INTEGER NOT NULL,
                    disk_usage REAL NOT NULL,
                    disk_available INTEGER NOT NULL,
                    network_sent INTEGER NOT NULL,
                    network_received INTEGER NOT NULL,
                    active_processes INTEGER NOT NULL,
                    load_avg REAL NOT NULL,
                    uptime INTEGER NOT NULL,
                    metadata TEXT
                )
            ''')

            # 优化记录表
            db_manager.execute('''
                CREATE TABLE IF NOT EXISTS optimization_record (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    optimization_type TEXT NOT NULL,
                    target TEXT NOT NULL,
                    after_value REAL,
                    status TEXT NOT NULL,
                    execution_time REAL,
                    details TEXT
                )
            ''')

            # 进程监控表
            db_manager.execute('''
                CREATE TABLE IF NOT EXISTS process_monitoring (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    process_id INTEGER NOT NULL,
                    cpu_usage REAL NOT NULL,
                    memory_rss INTEGER NOT NULL,
                    status TEXT NOT NULL,
                    username TEXT
                )
            ''')

            db_manager.execute('''
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    event_type TEXT NOT NULL,
                    severity TEXT NOT NULL,
                    details TEXT,
                    resolved_at TEXT
            ''')
            # 创建索引
            db_manager.execute('CREATE INDEX IF NOT EXISTS idx_performance_timestamp ON server_performance(timestamp)')
            db_manager.execute('CREATE INDEX IF NOT EXISTS idx_optimization_timestamp ON optimization_record(timestamp)')
            db_manager.execute('CREATE INDEX IF NOT EXISTS idx_process_timestamp ON process_monitoring(timestamp)')
            db_manager.execute('CREATE INDEX IF NOT EXISTS idx_event_timestamp ON server_event(timestamp)')

            logger.info("服务器性能优化数据库表创建成功")

        except Exception as e:
            logger.error(f"创建服务器性能优化数据库表失败: {str(e)}")

    def _start_monitoring_threads(self):
        # 性能监控线程
        performance_thread = threading.Thread(target=self._monitor_performance, daemon=True)
        performance_thread.start()

        # 优化线程
        optimization_thread = threading.Thread(target=self._optimize_server, daemon=True)
        optimization_thread.start()

        # 进程监控线程
        process_thread = threading.Thread(target=self._monitor_processes, daemon=True)
        process_thread.start()

        # 事件处理线程
        event_thread = threading.Thread(target=self._process_events, daemon=True)
        event_thread.start()

        logger.info("服务器性能优化监控线程启动成功")

    def _monitor_performance(self):
        """监控服务器性能"""
        while self.monitoring_enabled:
            try:
                # 收集性能数据
                performance_data = self._collect_performance_data()
                # 记录到数据库
                self._record_performance_data(performance_data)

                # 检查是否需要优化
                if self._needs_optimization(performance_data):
                    self._trigger_optimization()

                time.sleep(10)  # 每10秒收集一次数据

            except Exception as e:
                logger.error(f"性能监控失败: {str(e)}")
                time.sleep(10)

    def _monitor_processes(self):
        """监控进程"""
        while self.monitoring_enabled:
            try:
                # 收集进程数据
                processes_data = self._collect_processes_data()
                # 记录到数据库
                for process_data in processes_data:
                    self._record_process_data(process_data)

                time.sleep(30)  # 每30秒收集一次进程数据

            except Exception as e:
                logger.error(f"进程监控失败: {str(e)}")
                time.sleep(30)

    def _optimize_server(self):
        """优化服务器"""
        while self.optimization_enabled:
            try:
                current_time = time.time()
                if current_time - self.last_optimization > self.optimization_interval:
                    self._perform_optimization()
                    self.last_optimization = current_time

                time.sleep(60)  # 每分钟检查一次
            except Exception as e:
                logger.error(f"服务器优化失败: {str(e)}")
                time.sleep(60)

    def _process_events(self):
        """处理服务器事件"""
        while self.monitoring_enabled:
            try:
                # 检查性能数据，生成事件
                recent_performance = self.performance_data['cpu'][-5:] if self.performance_data['cpu'] else []
                if recent_performance:
                    avg_cpu = sum([item['value'] for item in recent_performance]) / len(recent_performance)
                    if avg_cpu > self.thresholds['cpu']:
                        self._create_event(
                            'high_cpu_usage',
                            'warning',
                            f'CPU使用率过高: {avg_cpu:.2f}%'
                        )

                time.sleep(60)  # 每分钟检查一次

            except Exception as e:
                logger.error(f"事件处理失败: {str(e)}")
                time.sleep(60)

    def _collect_performance_data(self):
        """收集性能数据"""
            # CPU信息
            cpu_usage = psutil.cpu_percent(interval=1)

            # 内存信息
            memory = psutil.virtual_memory()
            memory_usage = memory.percent
            memory_available = memory.available

            # 磁盘信息
            disk = psutil.disk_usage('/')
            disk_usage = disk.percent
            disk_available = disk.free

            # 网络信息
            network = psutil.net_io_counters()
            network_sent = network.bytes_sent

            # 进程信息
            active_processes = len(psutil.pids())

            uptime = int(time.time() - psutil.boot_time())

            data = {
                'timestamp': datetime.now().isoformat(),
                'cpu_usage': cpu_usage,
                'memory_usage': memory_usage,
                'memory_available': memory_available,
                'disk_usage': disk_usage,
                'disk_available': disk_available,
                'network_sent': network_sent,
                'network_received': network_received,
                'active_processes': active_processes,
                'load_avg': load_avg,
                'uptime': uptime
            }

            self.performance_data['cpu'].append({'timestamp': data['timestamp'], 'value': cpu_usage})
            self.performance_data['memory'].append({'timestamp': data['timestamp'], 'value': memory_usage})
            self.performance_data['disk'].append({'timestamp': data['timestamp'], 'value': disk_usage})
            self.performance_data['network'].append({'timestamp': data['timestamp'], 'value': network_sent + network_received})

            # 保持数据量在合理范围
            for key in self.performance_data:
                if len(self.performance_data[key]) > 1000:
                    self.performance_data[key] = self.performance_data[key][-1000:]

            return data

        except Exception as e:
            logger.error(f"收集性能数据失败: {str(e)}")
            return {}

    def _collect_processes_data(self):
        """收集进程数据"""
        try:
            processes = []
            for proc in psutil.process_iter(['pid', 'name', 'cpu_percent', 'memory_percent', 'memory_info', 'status', 'create_time', 'username']):
                try:
                    process_data = {
                        'timestamp': datetime.now().isoformat(),
                        'process_id': proc_info['pid'],
                        'cpu_usage': proc_info['cpu_percent'] if proc_info['cpu_percent'] is not None else 0.0,
                        'memory_usage': proc_info['memory_percent'] if proc_info['memory_percent'] is not None else 0.0,
                        'memory_rss': proc_info['memory_info'].rss if proc_info['memory_info'] else 0,
                        'status': proc_info['status'],
                        'uptime': int(time.time() - proc_info['create_time']) if proc_info['create_time'] else 0,
                        'username': proc_info['username'] or 'unknown'
                    }
                    processes.append(process_data)
                    pass

            # 更新进程数据
            self.performance_data['processes'] = processes[:100]  # 只保留前100个进程

            return processes

        except Exception as e:
            logger.error(f"收集进程数据失败: {str(e)}")
            return []

    def _record_performance_data(self, data):
        """记录性能数据到数据库"""
        try:
            db_manager.insert('server_performance', {
                'timestamp': data.get('timestamp'),
                'cpu_usage': data.get('cpu_usage'),
                'memory_usage': data.get('memory_usage'),
                'disk_usage': data.get('disk_usage'),
                'disk_available': data.get('disk_available'),
                'network_received': data.get('network_received'),
                'active_processes': data.get('active_processes'),
                'load_avg': data.get('load_avg'),
                'uptime': data.get('uptime'),
                'metadata': str(data)
            })
        except Exception as e:
            logger.error(f"记录性能数据失败: {str(e)}")

    def _record_process_data(self, data):
        """记录进程数据到数据库"""
        try:
            db_manager.insert('process_monitoring', {
                'timestamp': data.get('timestamp'),
                'process_name': data.get('process_name'),
                'process_id': data.get('process_id'),
                'memory_usage': data.get('memory_usage'),
                'memory_rss': data.get('memory_rss'),
                'status': data.get('status'),
                'uptime': data.get('uptime'),
                'username': data.get('username')
            })
        except Exception as e:
            logger.error(f"记录进程数据失败: {str(e)}")

    def _needs_optimization(self, performance_data):
        """检查是否需要优化"""
        if not performance_data:
            return False

        # 检查CPU使用率
        if performance_data.get('cpu_usage', 0) > self.thresholds['cpu']:
            return True

        # 检查内存使用率
        if performance_data.get('memory_usage', 0) > self.thresholds['memory']:
            return True

        # 检查磁盘使用率
        if performance_data.get('disk_usage', 0) > self.thresholds['disk']:
            return True

        return False

    def _trigger_optimization(self):
        """触发优化"""
        logger.info("触发紧急优化")

    def _perform_optimization(self):
        """执行优化"""

            optimizations = []

            # 内存优化
                optimizations.append(memory_optimization)

            process_optimization = self._optimize_processes()
            if process_optimization:
                optimizations.append(process_optimization)

            # 磁盘优化
            disk_optimization = self._optimize_disk()
            if disk_optimization:
                optimizations.append(disk_optimization)

            # 网络优化
            network_optimization = self._optimize_network()
            if network_optimization:
                optimizations.append(network_optimization)

            # 记录优化结果
                self._record_optimization(optimization)

            self.performance_data['optimizations'].append({
                'optimizations': optimizations,
            })

            logger.info(f"服务器优化完成，执行了 {len(optimizations)} 项优化")

        except Exception as e:
            logger.error(f"执行优化失败: {str(e)}")

    def _optimize_memory(self):
        """优化内存"""
        try:
            before_memory = psutil.virtual_memory().available

            # 清理Python垃圾回收
            import gc

            # 尝试清理系统缓存
            if os.name == 'posix':
                try:
                    os.system('sync && echo 3 > /proc/sys/vm/drop_caches')
                except:
                    pass

            improvement = (after_memory - before_memory) / (1024 * 1024)  # MB

            if improvement > 10:
                optimization = {
                    'optimization_type': 'memory',
                    'target': 'system_memory',
                    'before_value': before_memory,
                    'after_value': after_memory,
                    'improvement': improvement,
                    'status': 'success',
                    'details': f'释放了 {improvement:.2f} MB 内存'
                logger.info(f"内存优化: 释放了 {improvement:.2f} MB 内存")

        except Exception as e:
            logger.error(f"内存优化失败: {str(e)}")

        return None

    def _optimize_processes(self):
        try:
            # 找到占用CPU和内存最多的进程
            processes = []
            for proc in psutil.process_iter(['pid', 'name', 'cpu_percent', 'memory_percent']):
                try:
                    proc_info = proc.info
                    cpu_percent = float(proc_info.get('cpu_percent', 0))
                    memory_percent = float(proc_info.get('memory_percent', 0))
                    if cpu_percent > 10 or memory_percent > 5:
                except (psutil.NoSuchProcess, psutil.AccessDenied, ValueError, TypeError):
                    pass

            # 按CPU使用率排序
            processes.sort(key=lambda x: float(x.get('cpu_percent', 0)), reverse=True)

            # 记录进程优化
                top_process = processes[0]
                cpu_percent = float(top_process.get('cpu_percent', 0))
                optimization = {
                    'optimization_type': 'process',
                    'target': top_process['name'],
                    'before_value': cpu_percent,
                    'after_value': 0,
                    'improvement': cpu_percent,
                    'status': 'monitored',
                    'details': f'监控高CPU进程: {top_process["name"]} (PID: {top_process["pid"]}, CPU: {cpu_percent}%)'
                }
                logger.info(f"进程优化: 监控高CPU进程 {top_process['name']} (PID: {top_process['pid']}, CPU: {cpu_percent}%)")

        except Exception as e:
            logger.error(f"进程优化失败: {str(e)}")

        return None

    def _optimize_disk(self):
        """优化磁盘"""
        try:
            # 清理临时文件
            temp_dirs = ['/tmp', '/var/tmp']
            cleaned_files = 0
            cleaned_size = 0

                    for root, dirs, files in os.walk(temp_dir):
                        for file in files:
                            try:
                                if os.path.isfile(file_path):
                                    file_size = os.path.getsize(file_path)
                                    os.remove(file_path)
                                    cleaned_files += 1
                                    cleaned_size += file_size
                                pass

                cleaned_size_mb = cleaned_size / (1024 * 1024)
                optimization = {
                    'optimization_type': 'disk',
                    'target': 'temporary_files',
                    'before_value': cleaned_size,
                    'after_value': 0,
                    'improvement': cleaned_size_mb,
                    'status': 'success',
                    'details': f'清理了 {cleaned_files} 个临时文件，释放了 {cleaned_size_mb:.2f} MB 磁盘空间'
                }
                logger.info(f"磁盘优化: 清理了 {cleaned_files} 个临时文件，释放了 {cleaned_size_mb:.2f} MB 磁盘空间")

        except Exception as e:
            logger.error(f"磁盘优化失败: {str(e)}")

        return None

    def _optimize_network(self):
        """优化网络"""
            # 网络IO统计（优先获取）
            net_io = psutil.net_io_counters()
            bytes_sent = net_io.bytes_sent
            bytes_recv = net_io.bytes_recv

            # 尝试获取网络连接数，但不依赖它
            connection_count = 0
                # 尝试获取网络连接，但使用更安全的方式
                connections = psutil.net_connections()
                established_connections = []
                # 安全处理连接信息
                for c in connections:
                    try:
                        if hasattr(c, 'status') and c.status == 'ESTABLISHED':
                            # 只处理IPv4和IPv6连接
                                established_connections.append(c)
                    except (psutil.AccessDenied, psutil.NoSuchProcess, AttributeError, TypeError, OSError):
                        # 忽略所有错误，继续处理其他连接

                connection_count = len(established_connections)

            except Exception as e:
                # 网络连接获取失败，不影响整体优化

            # 生成优化记录
            if connection_count > 0:
                optimization = {
                    'optimization_type': 'network',
                    'target': 'network_io',
                    'before_value': bytes_sent + bytes_recv,
                    'after_value': bytes_sent + bytes_recv,
                    'improvement': 0,
                    'status': 'monitored',
                }

            else:
                # 没有获取到连接数，只记录网络IO
                optimization = {
                    'target': 'network_io',
                    'before_value': bytes_sent + bytes_recv,
                    'after_value': bytes_sent + bytes_recv,
                    'improvement': 0,
                    'status': 'monitored',
                    'details': f'网络IO: 发送 {bytes_sent/1024/1024:.2f}MB, 接收 {bytes_recv/1024/1024:.2f}MB'
                }
            return optimization

        except Exception as e:
            logger.warning(f"网络优化失败: {str(e)}")

            # 尝试获取最基本的网络信息
            try:
                # 尝试获取网络接口信息
                net_if_addrs = psutil.net_if_addrs()

                optimization = {
                    'optimization_type': 'network',
                    'target': 'network_interfaces',
                    'before_value': interface_count,
                    'after_value': interface_count,
                    'status': 'monitored',
                    'details': f'网络接口数: {interface_count}'
                }

                return optimization
            except:
                # 如果所有方法都失败，返回None
                logger.error(f"网络优化完全失败: {str(e)}")

        return None

    def _record_optimization(self, optimization):
        """记录优化到数据库"""
        try:
            db_manager.insert('optimization_record', {
                'timestamp': datetime.now().isoformat(),
                'optimization_type': optimization.get('optimization_type'),
                'target': optimization.get('target'),
                'before_value': optimization.get('before_value'),
                'after_value': optimization.get('after_value'),
                'improvement': optimization.get('improvement'),
                'status': optimization.get('status'),
                'execution_time': optimization.get('execution_time'),
                'details': optimization.get('details')
        except Exception as e:

    def _create_event(self, event_type, severity, message, details=None):
        """创建服务器事件"""
        try:
            db_manager.insert('server_event', {
                'timestamp': datetime.now().isoformat(),
                'event_type': event_type,
                'severity': severity,
                'message': message,
                'details': details
            })

        except Exception as e:

        """获取性能数据"""
        try:
            # 从数据库获取性能数据
            from datetime import timedelta
            start_time = (datetime.now() - timedelta(hours=hours)).isoformat()

            performance_data = db_manager.fetch_all(
                'SELECT * FROM server_performance WHERE timestamp >= ? ORDER BY timestamp',
            )
            return performance_data
    def get_optimization_history(self, days=7):
        try:
            start_time = (datetime.now() - timedelta(days=days)).isoformat()
            optimizations = db_manager.fetch_all(
                'SELECT * FROM optimization_record WHERE timestamp >= ? ORDER BY timestamp DESC',
                (start_time,)
            )
            return optimizations
        except Exception as e:
            return []

    def get_server_events(self, days=7):
        """获取服务器事件"""
            from datetime import timedelta
            start_time = (datetime.now() - timedelta(days=days)).isoformat()

            events = db_manager.fetch_all(
                (start_time,)

            return []

    def get_current_status(self):
        """获取当前状态"""
            # 收集当前性能数据
            performance_data = self._collect_performance_data()
            processes = self.performance_data['processes'][:10]  # 前10个进程

            # 获取最近的优化
            recent_optimizations = self.performance_data['optimizations'][-5:] if self.performance_data['optimizations'] else []

            status = {
                'top_processes': processes,
                'recent_optimizations': recent_optimizations,
            }

        except Exception as e:
            logger.error(f"获取当前状态失败: {str(e)}")
            return {}

    def shutdown(self):
        """关闭服务器优化AI"""
        self.monitoring_enabled = False
        self.optimization_enabled = False
        logger.info("服务器性能优化AI已关闭")

# 创建服务器优化AI实例
server_optimizer_ai = ServerOptimizerAI()
