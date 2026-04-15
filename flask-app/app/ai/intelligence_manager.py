#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
智体管家，自动管理系统所有需要管理的功能包括AI
"""

import os
import sys
import time
import logging
import threading
from datetime import datetime
from typing import Dict, List, Any, Optional

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

logger = logging.getLogger(__name__)

class IntelligenceManager:
    """
    智体管家，自动管理系统所有需要管理的功能包括AI
    """
    
    def __init__(self):
        """初始化智体管家"""
        self.logger = logging.getLogger(__name__)
        self.logger.info("智体管家已初始化")
        
        # 组件状态
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
        
        # 系统资源状态
        self.system_resources = {
            'cpu': {'usage': 0, 'last_check': None},
            'memory': {'usage': 0, 'last_check': None},
            'disk': {'usage': 0, 'last_check': None},
            'network': {'usage': 0, 'last_check': None},
        }
        
        # 配置信息
        self.config = {
            'monitor_interval': 60,  # 监控间隔（秒）
            'auto_fix_enabled': True,  # 自动修复开关
            'auto_upgrade_enabled': True,  # 自动升级开关
            'report_interval': 3600,  # 报告生成间隔（秒）
            'resource_threshold': 0.8,  # 资源使用阈值
        }
        
        # 监控线程
        self.monitor_thread = None
        self.report_thread = None
        self.running = False
        
        # 线程安全锁
        self.lock = threading.RLock()
        
        # 初始化所有组件
        self._initialize_components()
    
    def _initialize_components(self):
        """初始化所有AI组件"""
        self.logger.info("正在初始化所有AI组件...")
        
        # 尝试导入所有AI组件
        components = {
            'ai_route_optimizer': 'app.ai.route_optimizer',
            'ai_question_generator': 'app.ai.question_generator',
            'ai_self_learning_system': 'app.ai.self_learning_system',
            'ai_monitoring': 'app.ai.monitoring',
            'user_ai_manager': 'app.ai.user_ai_manager',
            'ai_instance_manager': 'app.ai.instances',
            'ai_self_upgrading_system': 'app.ai.self_upgrading_system',
            'ai_learning': 'app.ai.learning',
        }
        
        for component_name, module_path in components.items():
            try:
                __import__(module_path)
                self.component_status[component_name]['status'] = 'initialized'
                self.component_status[component_name]['last_check'] = datetime.now().isoformat()
                self.logger.info(f"{component_name} 组件初始化成功")
            except Exception as e:
                self.component_status[component_name]['status'] = f'error: {str(e)}'
                self.component_status[component_name]['last_check'] = datetime.now().isoformat()
                self.logger.error(f"{component_name} 组件初始化失败: {str(e)}")
    
    def start(self):
        """启动智体管家"""
        if self.running:
            self.logger.warning("智体管家已经在运行中")
            return
        
        self.logger.info("正在启动智体管家...")
        self.running = True
        
        # 启动监控线程
        self.monitor_thread = threading.Thread(target=self._monitor_loop, daemon=True)
        self.monitor_thread.start()
        self.logger.info("监控线程已启动")
        
        # 启动报告线程
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
        
        # 等待线程结束
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
            self.logger.info("开始监控所有组件...")
            
            # 检查所有组件状态
            for component_name in self.component_status.keys():
                self._check_component_status(component_name)
            
            # 检查系统资源
            self._check_system_resources()
            
            # 检查AI安全和合规
            self._check_ai_security()
            
            # 休眠监控间隔
            time.sleep(self.config['monitor_interval'])
    
    def _check_component_status(self, component_name: str):
        """检查单个组件状态"""
        self.logger.debug(f"正在检查 {component_name} 组件状态...")
        
        with self.lock:
            # 更新状态为检查中
            self.component_status[component_name]['last_check'] = datetime.now().isoformat()
            self.component_status[component_name]['status'] = 'checking'
            
            # 尝试导入组件以检查其状态
            components = {
                'ai_route_optimizer': lambda: self._check_route_optimizer(),
                'ai_question_generator': lambda: self._check_question_generator(),
                'ai_self_learning_system': lambda: self._check_self_learning_system(),
                'ai_monitoring': lambda: self._check_monitoring_system(),
                'user_ai_manager': lambda: self._check_user_ai_manager(),
                'ai_instance_manager': lambda: self._check_instance_manager(),
                'ai_self_upgrading_system': lambda: self._check_self_upgrading_system(),
                'ai_learning': lambda: self._check_learning_system(),
            }
            
            if component_name in components:
                try:
                    status = components[component_name]()
                    self.component_status[component_name]['status'] = status
                    self.component_status[component_name]['last_success'] = datetime.now().isoformat()
                    self.logger.debug(f"{component_name} 组件状态: {status}")
                    
                    # 如果组件状态为error，尝试自动修复
                    if 'error' in status and self.config['auto_fix_enabled']:
                        self.logger.info(f"尝试自动修复 {component_name} 组件...")
                        self.restart_component(component_name)
                except Exception as e:
                    error_msg = f'error: {str(e)}'
                    self.component_status[component_name]['status'] = error_msg
                    self.component_status[component_name]['last_error'] = datetime.now().isoformat()
                    self.component_status[component_name]['error_count'] = self.component_status[component_name].get('error_count', 0) + 1
                    self.logger.error(f"检查 {component_name} 组件状态失败: {str(e)}")
                    
                    # 尝试自动修复
                    if self.config['auto_fix_enabled']:
                        self.logger.info(f"尝试自动修复 {component_name} 组件...")
                        self.restart_component(component_name)
            else:
                self.component_status[component_name]['status'] = 'unknown'
                self.logger.warning(f"未知组件: {component_name}")
    
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
    
    def _check_monitoring_system(self) -> str:
        """检查AI监控系统状态"""
        try:
            from app.ai.monitoring import ai_monitor
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
    
    def _check_learning_system(self) -> str:
        """检查AI学习系统状态"""
        try:
            from app.ai.learning import ai_learning
            return 'running'
        except Exception as e:
            return f'error: {str(e)}'
    
    def _check_system_resources(self):
        """检查系统资源使用情况"""
        self.logger.debug("正在检查系统资源使用情况...")
        
        with self.lock:
            try:
                import psutil
                
                # 检查CPU使用率
                cpu_usage = psutil.cpu_percent(interval=0.1)
                self.system_resources['cpu']['usage'] = cpu_usage
                self.system_resources['cpu']['last_check'] = datetime.now().isoformat()
                
                # 检查内存使用率
                memory = psutil.virtual_memory()
                memory_usage = memory.percent
                self.system_resources['memory']['usage'] = memory_usage
                self.system_resources['memory']['last_check'] = datetime.now().isoformat()
                
                # 检查磁盘使用率
                disk = psutil.disk_usage('/')
                disk_usage = disk.percent
                self.system_resources['disk']['usage'] = disk_usage
                self.system_resources['disk']['last_check'] = datetime.now().isoformat()
                
                # 检查网络使用率（简化版）
                network = psutil.net_io_counters()
                network_usage = (network.bytes_sent + network.bytes_recv) / (1024 * 1024)  # MB
                self.system_resources['network']['usage'] = network_usage
                self.system_resources['network']['last_check'] = datetime.now().isoformat()
                
                self.logger.debug(f"系统资源使用情况: CPU={cpu_usage}%, 内存={memory_usage}%, 磁盘={disk_usage}%, 网络={network_usage:.2f}MB")
                
                # 检查资源使用阈值
                if cpu_usage > 80:
                    self.logger.warning(f"CPU使用率过高: {cpu_usage}%")
                if memory_usage > 80:
                    self.logger.warning(f"内存使用率过高: {memory_usage}%")
                if disk_usage > 80:
                    self.logger.warning(f"磁盘使用率过高: {disk_usage}%")
            except ImportError:
                self.logger.warning("psutil模块未安装，无法检查系统资源")
            except Exception as e:
                self.logger.error(f"检查系统资源失败: {str(e)}")
    
    def _check_ai_security(self):
        """检查AI安全和合规问题"""
        self.logger.debug("正在检查AI安全和合规问题...")
        
        # 这里可以实现AI安全检查逻辑
        # 例如检查AI生成内容的质量和合规性
    
    def _report_loop(self):
        """报告生成循环"""
        while self.running:
            self.logger.info("正在生成系统报告...")
            
            # 生成系统报告
            report = self.generate_report()
            
            # 保存报告
            self._save_report(report)
            
            # 休眠报告间隔
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
        
        # 检查组件状态
        for component_name, status_info in self.component_status.items():
            if 'error' in status_info['status']:
                recommendations.append(f"修复 {component_name} 组件: {status_info['status']}")
            elif status_info.get('error_count', 0) > 3:
                recommendations.append(f"{component_name} 组件错误次数过多，建议检查配置")
        
        # 检查资源使用情况
        if self.system_resources['cpu']['usage'] > 80:
            recommendations.append(f"CPU使用率过高: {self.system_resources['cpu']['usage']}%，建议优化任务调度")
        if self.system_resources['memory']['usage'] > 80:
            recommendations.append(f"内存使用率过高: {self.system_resources['memory']['usage']}%，建议释放内存或增加内存")
        if self.system_resources['disk']['usage'] > 80:
            recommendations.append(f"磁盘使用率过高: {self.system_resources['disk']['usage']}%，建议清理磁盘空间")
        
        # 检查组件健康状态
        for component_name, status_info in self.component_status.items():
            last_check = status_info.get('last_check')
            if last_check:
                last_check_time = datetime.fromisoformat(last_check)
                if (datetime.now() - last_check_time).total_seconds() > 300:  # 5分钟未检查
                    recommendations.append(f"{component_name} 组件长时间未检查，可能存在问题")
        
        return recommendations
    
    def _save_report(self, report: Dict[str, Any]):
        """保存系统报告"""
        # 这里可以实现报告保存逻辑
        # 例如保存到数据库或文件系统
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
            # 这里可以实现组件重启逻辑
            # 目前先更新状态为重启中
            self.component_status[component_name]['status'] = 'restarting'
            self.component_status[component_name]['last_check'] = datetime.now().isoformat()
            
            # 尝试重新初始化组件
            try:
                components = {
                    'ai_route_optimizer': lambda: self._restart_route_optimizer(),
                    'ai_question_generator': lambda: self._restart_question_generator(),
                    'ai_self_learning_system': lambda: self._restart_self_learning_system(),
                    'ai_monitoring': lambda: self._restart_monitoring_system(),
                    'user_ai_manager': lambda: self._restart_user_ai_manager(),
                    'ai_instance_manager': lambda: self._restart_instance_manager(),
                    'ai_self_upgrading_system': lambda: self._restart_self_upgrading_system(),
                    'ai_learning': lambda: self._restart_learning_system(),
                }
                
                if component_name in components:
                    components[component_name]()
                    self.component_status[component_name]['status'] = 'running'
                    self.logger.info(f"{component_name} 组件重启成功")
                else:
                    self.component_status[component_name]['status'] = 'unknown'
                    self.logger.warning(f"未知组件: {component_name}")
            except Exception as e:
                self.component_status[component_name]['status'] = f'error: {str(e)}'
                self.logger.error(f"重启 {component_name} 组件失败: {str(e)}")
    
    # 重启各个组件的方法
    def _restart_route_optimizer(self):
        """重启AI路由优化器"""
        from app.ai.route_optimizer import AIRouteOptimizer
        global ai_route_optimizer
        ai_route_optimizer = AIRouteOptimizer()
    
    def _restart_question_generator(self):
        """重启AI题目生成器"""
        from app.ai.question_generator import AIQuestionGenerator
        global ai_question_generator
        ai_question_generator = AIQuestionGenerator()
    
    def _restart_self_learning_system(self):
        """重启AI自学习系统"""
        from app.ai.self_learning_system import SelfLearningSystem
        global self_learning_system
        self_learning_system = SelfLearningSystem()
    
    def _restart_monitoring_system(self):
        """重启AI监控系统"""
        from app.ai.monitoring import AIMonitor
        global ai_monitor
        ai_monitor = AIMonitor()
    
    def _restart_user_ai_manager(self):
        """重启用户AI管理器"""
        from app.ai.user_ai_manager import UserAIManager
        global user_ai_manager
        user_ai_manager = UserAIManager()
    
    def _restart_instance_manager(self):
        """重启AI实例管理器"""
        from app.ai.instances import AIInstanceManager
        global ai_instance_manager
        ai_instance_manager = AIInstanceManager()
    
    def _restart_self_upgrading_system(self):
        """重启AI自我升级系统"""
        from app.ai.self_upgrading_system import SelfUpgradingSystem
        global self_upgrading_system
        self_upgrading_system = SelfUpgradingSystem()
    
    def _restart_learning_system(self):
        """重启AI学习系统"""
        from app.ai.learning import AILearning
        global ai_learning
        ai_learning = AILearning()
    
    def optimize_system(self):
        """优化整个系统"""
        self.logger.info("正在优化整个系统...")
        
        with self.lock:
            # 重启所有出现错误的组件
            for component_name, status_info in self.component_status.items():
                if 'error' in status_info['status']:
                    self.restart_component(component_name)
            
            # 调整配置
            # 这里可以添加配置调整逻辑
            
        self.logger.info("系统优化完成")

# 初始化智体管家实例
intelligence_manager = IntelligenceManager()
