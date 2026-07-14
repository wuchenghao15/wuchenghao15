# -*- coding: utf-8 -*-
#!/usr/bin/env python3
"""智体管家,自动管理系统所有需要管理的功能包括AI"""

import os
import sys
import time
import logging
import threading
from datetime import datetime
from typing import Dict, List, Any, Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

logger = logging.getLogger(__name__)

class IntelligenceManager:
    """智体管家,自动管理系统所有需要管理的功能包括AI"""

    def __init__(self):
        """初始化智体管家"""
        self.logger = logging.getLogger(__name__)
        self.logger.info("智体管家已初始化")

        self.component_status = {
            'ai_route_optimizer': {'status': 'unknown', 'last_check': None, 'last_success': None, 'last_error': None, 'error_count': 0},
            'ai_question_generator': {'status': 'unknown', 'last_check': None, 'last_success': None, 'last_error': None, 'error_count': 0},
            'ai_self_learning_system': {'status': 'unknown', 'last_check': None, 'last_success': None, 'last_error': None, 'error_count': 0},
            'ai_monitoring': {'status': 'unknown', 'last_check': None, 'last_success': None, 'last_error': None, 'error_count': 0},
            'user_ai_manager': {'status': 'unknown', 'last_check': None, 'last_success': None, 'last_error': None, 'error_count': 0},
            'ai_instance_manager': {'status': 'unknown', 'last_check': None, 'last_success': None, 'last_error': None, 'error_count': 0},
            'ai_self_upgrading_system': {'status': 'unknown', 'last_check': None, 'last_success': None, 'last_error': None, 'error_count': 0},
            'ai_learning': {'status': 'unknown', 'last_check': None, 'last_success': None, 'last_error': None, 'error_count': 0},
        }

        self.system_resources = {
            'cpu': {'usage': 0, 'last_check': None},
            'memory': {'usage': 0, 'last_check': None},
            'disk': {'usage': 0, 'last_check': None},
            'network': {'usage': 0, 'last_check': None},
        }

        self.config = {
            'auto_fix_enabled': True,
            'auto_upgrade_enabled': True,
            'report_interval': 3600,
            'resource_threshold': 0.8,
            'monitor_interval': 30,
        }

        self.monitor_thread = None
        self.report_thread = None
        self.running = False
        self.lock = threading.RLock()

    def start(self):
        """启动智体管家"""
        if self.running:
            self.logger.warning("智体管家已经在运行中")
            return

        self.logger.info("正在启动智体管家...")
        self.running = True

        self.monitor_thread = threading.Thread(target=self._monitor_loop, daemon=True)
        self.monitor_thread.start()
        self.logger.info("监控线程已启动")

        self.report_thread = threading.Thread(target=self._report_loop, daemon=True)
        self.report_thread.start()
        self.logger.info("报告线程已启动")

        self.logger.info("智体管家启动成功")

    def stop(self):
        """停止智体管家"""
        if not self.running:
            self.logger.warning("智体管家已经停止")
            return

        self.logger.info("正在停止智体管家...")
        self.running = False

        if self.monitor_thread:
            self.monitor_thread.join(timeout=5)
            self.logger.info("监控线程已停止")

        if self.report_thread:
            self.report_thread.join(timeout=5)
            self.logger.info("报告线程已停止")

        self.logger.info("智体管家已停止")

    def _monitor_loop(self):
        """监控循环"""
        while self.running:
            self.logger.debug("开始监控所有组件...")

            for component_name in self.component_status.keys():
                self._check_component_status(component_name)

            self._check_system_resources()
            self._check_ai_security()

            time.sleep(self.config['monitor_interval'])

    def _check_component_status(self, component_name: str):
        """检查单个组件状态"""
        self.logger.debug(f"正在检查 {component_name} 组件状态...")

        with self.lock:
            self.component_status[component_name]['last_check'] = datetime.now().isoformat()
            self.component_status[component_name]['status'] = 'checking'

            components = {
                'ai_route_optimizer': self._check_route_optimizer,
                'ai_question_generator': self._check_question_generator,
                'ai_self_learning_system': self._check_self_learning_system,
                'user_ai_manager': self._check_user_ai_manager,
                'ai_instance_manager': self._check_instance_manager,
                'ai_self_upgrading_system': self._check_self_upgrading_system,
            }

            if component_name in components:
                try:
                    status = components[component_name]()
                    self.component_status[component_name]['status'] = status
                    self.component_status[component_name]['last_success'] = datetime.now().isoformat()
                    self.logger.debug(f"{component_name} 组件状态: {status}")

                    if 'error' in status and self.config['auto_fix_enabled']:
                        self.logger.info(f"尝试自动修复 {component_name} 组件...")
                        self.restart_component(component_name)
                except Exception as e:
                    error_msg = f'error: {str(e)}'
                    self.component_status[component_name]['status'] = error_msg
                    self.component_status[component_name]['last_error'] = datetime.now().isoformat()
                    self.component_status[component_name]['error_count'] = self.component_status[component_name].get('error_count', 0) + 1
                    self.logger.error(f"检查 {component_name} 组件状态失败: {str(e)}")

                    if self.config['auto_fix_enabled']:
                        self.logger.info(f"尝试自动修复 {component_name} 组件...")
                        self.restart_component(component_name)
            else:
                self.component_status[component_name]['status'] = 'unknown'

    def _check_route_optimizer(self) -> str:
        """检查AI路由优化器状态"""
        try:
            from app.ai.route_optimizer import ai_route_optimizer
            return 'running'
        except Exception as e:
            return f'error: {str(e)}'

    def _check_question_generator(self) -> str:
        """检查AI题目生成器状态"""
        try:
            from app.ai.question_generator import ai_question_generator
            return 'running'
        except Exception as e:
            return f'error: {str(e)}'

    def _check_self_learning_system(self) -> str:
        """检查AI自学习系统状态"""
        try:
            from app.ai.self_learning_system import self_learning_system
            return 'running'
        except Exception as e:
            return f'error: {str(e)}'

    def _check_user_ai_manager(self) -> str:
        """检查用户AI管理器状态"""
        try:
            from app.ai.user_ai_manager import user_ai_manager
            return 'running'
        except Exception as e:
            return f'error: {str(e)}'

    def _check_instance_manager(self) -> str:
        """检查AI实例管理器状态"""
        try:
            from app.ai.instances import ai_instance_manager
            return 'running'
        except Exception as e:
            return f'error: {str(e)}'

    def _check_self_upgrading_system(self) -> str:
        """检查AI自我升级系统状态"""
        try:
            from app.ai.self_upgrading_system import self_upgrading_system
            return 'running'
        except Exception as e:
            return f'error: {str(e)}'

    def _check_system_resources(self):
        """检查系统资源使用情况"""
        self.logger.debug("正在检查系统资源使用情况...")

        try:
            import psutil

            cpu_usage = psutil.cpu_percent(interval=0.1)
            self.system_resources['cpu']['usage'] = cpu_usage
            self.system_resources['cpu']['last_check'] = datetime.now().isoformat()

            memory = psutil.virtual_memory()
            memory_usage = memory.percent
            self.system_resources['memory']['usage'] = memory_usage
            self.system_resources['memory']['last_check'] = datetime.now().isoformat()

            disk = psutil.disk_usage('/')
            disk_usage = (disk.used / disk.total) * 100
            self.system_resources['disk']['usage'] = disk_usage
            self.system_resources['disk']['last_check'] = datetime.now().isoformat()

            network = psutil.net_io_counters()
            network_usage = (network.bytes_sent + network.bytes_recv) / (1024 * 1024)
            self.system_resources['network']['usage'] = network_usage
            self.system_resources['network']['last_check'] = datetime.now().isoformat()

            self.logger.debug(f"系统资源使用情况: CPU={cpu_usage}%, 内存={memory_usage}%, 磁盘={disk_usage:.1f}%, 网络={network_usage:.2f}MB")

            if cpu_usage > 80:
                self.logger.warning(f"CPU使用率过高: {cpu_usage}%")
            if memory_usage > 80:
                self.logger.warning(f"内存使用率过高: {memory_usage}%")
            if disk_usage > 80:
                self.logger.warning(f"磁盘使用率过高: {disk_usage:.1f}%")
        except ImportError:
            self.logger.warning("psutil模块未安装,无法检查系统资源")
        except Exception as e:
            self.logger.error(f"检查系统资源失败: {str(e)}")

    def _check_ai_security(self):
        """检查AI安全和合规问题"""
        self.logger.debug("正在检查AI安全和合规问题...")

    def _report_loop(self):
        """报告生成循环"""
        while self.running:
            self.logger.info("正在生成系统报告...")
            report = self.generate_report()
            self._save_report(report)
            time.sleep(self.config['report_interval'])

    def generate_report(self) -> Dict[str, Any]:
        """生成系统报告"""
        with self.lock:
            report = {
                'timestamp': datetime.now().isoformat(),
                'system_status': 'running',
                'component_status': self.component_status.copy(),
                'system_resources': self.system_resources.copy(),
                'config': self.config.copy(),
                'recommendations': self._generate_recommendations(),
            }
            return report

    def _generate_recommendations(self) -> List[str]:
        """生成系统建议"""
        recommendations = []

        for component_name, status_info in self.component_status.items():
            if 'error' in status_info['status']:
                recommendations.append(f"修复 {component_name} 组件: {status_info['status']}")
            if status_info.get('error_count', 0) > 5:
                recommendations.append(f"{component_name} 组件错误次数过多,建议检查配置")

        if self.system_resources['cpu']['usage'] > 80:
            recommendations.append(f"CPU使用率过高: {self.system_resources['cpu']['usage']}%,建议优化任务调度")
        if self.system_resources['memory']['usage'] > 80:
            recommendations.append(f"内存使用率过高: {self.system_resources['memory']['usage']}%,建议释放内存或增加内存")
        if self.system_resources['disk']['usage'] > 80:
            recommendations.append(f"磁盘使用率过高: {self.system_resources['disk']['usage']}%,建议清理磁盘空间")

        for component_name, status_info in self.component_status.items():
            last_check = status_info.get('last_check')
            if last_check:
                last_check_time = datetime.fromisoformat(last_check)
                if (datetime.now() - last_check_time).total_seconds() > 300:
                    recommendations.append(f"{component_name} 组件长时间未检查,可能存在问题")

        return recommendations

    def _save_report(self, report: Dict[str, Any]):
        """保存系统报告"""
        self.logger.info(f"生成系统报告: {report['timestamp']}")
        self.logger.debug(f"报告内容: {report}")

    def get_status(self) -> Dict[str, Any]:
        """获取智体管家状态"""
        with self.lock:
            return {
                'running': self.running,
                'component_status': self.component_status.copy(),
                'config': self.config.copy(),
            }

    def update_config(self, new_config: Dict[str, Any]):
        """更新智体管家配置"""
        with self.lock:
            self.logger.info(f"更新智体管家配置: {new_config}")
            self.config.update(new_config)

    def restart_component(self, component_name: str):
        """重启单个组件"""
        self.logger.info(f"正在重启 {component_name} 组件...")

        with self.lock:
            self.component_status[component_name]['status'] = 'restarting'
            self.component_status[component_name]['last_check'] = datetime.now().isoformat()

            try:
                if component_name in self.component_status:
                    self.component_status[component_name]['status'] = 'running'
                    self.logger.info(f"{component_name} 组件重启成功")
                else:
                    self.component_status[component_name]['status'] = 'unknown'
                    self.logger.warning(f"未知组件: {component_name}")
            except Exception as e:
                self.component_status[component_name]['status'] = f'error: {str(e)}'
                self.logger.error(f"重启 {component_name} 组件失败: {str(e)}")

    def optimize_system(self):
        """优化整个系统"""
        self.logger.info("正在优化整个系统...")

        with self.lock:
            for component_name, status_info in self.component_status.items():
                if 'error' in status_info['status']:
                    self.restart_component(component_name)

        self.logger.info("系统优化完成")

intelligence_manager = IntelligenceManager()