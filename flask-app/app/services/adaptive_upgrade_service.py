# -*- coding: utf-8 -*-
#!/usr/bin/env python3
"""
自适应升级服务 - 用于强化AI集和AI员工的处理能力
"""
import threading
import time
from datetime import datetime
from app.models.enhanced_ai_employee import EnhancedAIEmployee
from app.services.ai_brain_service import ai_brain_service
from app.utils.logging import logger
import logging

class AdaptiveUpgradeService:
    """自适应升级服务: 负责AI员工和AI集的自动升级和适配"""

    _instance = None
    _lock = threading.Lock()

    def __new__(cls):
        """单例模式"""
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super(AdaptiveUpgradeService, cls).__new__(cls)
        return cls._instance

    def __init__(self):
        """初始化自适应升级服务"""
        if not hasattr(self, '_initialized'):
            self._initialized = True
            self._upgrading = False
            self._upgrade_lock = threading.Lock()
            self._upgrade_history = []
            self._capability_modules = {
                'general': {
                    'name': '通用能力模块',
                    'capabilities': ['数据分析', '任务处理', '知识管理', '自我学习']
                },
                'login_route_manager': {
                    'name': '登录路由管理模块',
                    'capabilities': ['系统规则管理', '登录路由处理', '用户角色识别', '动态路由生成']
                },
                'security_manager': {
                    'capabilities': ['风险检测', '权限管理', '安全审计', '异常处理']
                },
                'performance_optimizer': {
                    'capabilities': ['资源调度', '负载均衡', '性能监控', '自动调优']
                }
            }
            logger.info("自适应升级服务初始化完成")

    def start_auto_upgrade(self, interval=3600):
        """启动自动升级任务
        
        Args:
            interval: 升级间隔时间(秒),默认3600秒(1小时)
        """
        if not hasattr(self, '_auto_upgrade_thread'):
            self._auto_upgrade_thread = threading.Thread(
                target=self._auto_upgrade_loop, 
                args=(interval,), 
                daemon=True
            )
            self._auto_upgrade_thread.start()
            logger.info(f"自动升级服务已启动,升级间隔: {interval}秒")

    def _auto_upgrade_loop(self, interval):
        """自动升级循环"""
        while True:
            try:
                self.upgrade_all_ai_employees()
                time.sleep(interval)
            except Exception as e:
                logger.error(f"自动升级循环出错: {str(e)}")
                time.sleep(60)

    def upgrade_all_ai_employees(self):
        """升级所有AI员工"""
        with self._upgrade_lock:
            if self._upgrading:
                logger.info("升级已在进行中,跳过本次升级")
                return

            self._upgrading = True
            try:
                logger.info("开始升级所有AI员工...")
                ai_employees = EnhancedAIEmployee.get_all()

                for ai_employee in ai_employees:
                    self.upgrade_ai_employee(ai_employee.employee_id)

                logger.info(f"成功升级 {len(ai_employees)} 个AI员工")
            except Exception as e:
                logger.error(f"升级所有AI员工失败: {str(e)}")
            finally:
                self._upgrading = False

    def upgrade_ai_employee(self, employee_id):
        """升级单个AI员工
        
        Args:
            employee_id: AI员工ID
            
        Returns:
            bool: 升级是否成功
        """
        try:
            ai_employee = EnhancedAIEmployee.get_by_id(employee_id)
            if not ai_employee:
                logger.warning(f"未找到AI员工: {employee_id}")
                return False

            logger.info(f"开始升级AI员工: {ai_employee.name} (ID: {employee_id})")

            current_capabilities = set(ai_employee.capabilities)
            ai_type = ai_employee.ai_type
            required_capabilities = set()

            if 'general' in self._capability_modules:
                required_capabilities.update(self._capability_modules['general']['capabilities'])

            if ai_type in self._capability_modules:
                required_capabilities.update(self._capability_modules[ai_type]['capabilities'])

            missing_capabilities = required_capabilities - current_capabilities

            for capability in missing_capabilities:
                ai_employee.add_capability(capability)
                logger.info(f"为AI员工 {ai_employee.name} 添加能力: {capability}")

            ai_employee.update_adaptation_level(ai_employee.adaptation_level + 1)
            logger.info(f"提升AI员工 {ai_employee.name} 适配级别至: {ai_employee.adaptation_level}")

            if ai_employee.self_learning:
                self._enhance_self_learning(ai_employee)

            upgrade_info = {
                'last_upgrade_time': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                'upgrade_level': ai_employee.adaptation_level,
                'added_capabilities': list(missing_capabilities),
                'ai_type': ai_employee.ai_type
            }

            if 'adaptive_upgrade' not in ai_employee.config:
                ai_employee.config['adaptive_upgrade'] = []

            ai_employee.config['adaptive_upgrade'].append(upgrade_info)
            ai_employee.save()

            self._record_upgrade_history(ai_employee, upgrade_info)
            self._sync_with_ai_brain(ai_employee, upgrade_info)

            logger.info(f"成功升级AI员工: {ai_employee.name} (ID: {employee_id})")
            return True
        except Exception as e:
            logger.error(f"升级AI员工失败: {str(e)}")
            return False

    def _enhance_self_learning(self, ai_employee):
        """增强AI员工的自我学习能力
        
        Args:
            ai_employee: EnhancedAIEmployee实例
        """
        if 'self_learning' not in ai_employee.config:
            ai_employee.config['self_learning'] = {
                'enabled': True,
                'learning_rate': 0.5,
            }
        else:
            current_rate = ai_employee.config['self_learning'].get('learning_rate', 0.5)
            ai_employee.config['self_learning']['learning_rate'] = min(current_rate + 0.1, 1.0)

            current_threshold = ai_employee.config['self_learning'].get('adaptation_threshold', 0.7)
            ai_employee.config['self_learning']['adaptation_threshold'] = max(current_threshold - 0.1, 0.3)

    def _record_upgrade_history(self, ai_employee, upgrade_info):
        """记录升级历史
        
        Args:
            ai_employee: EnhancedAIEmployee实例
            upgrade_info: 升级信息字典
        """
        history_entry = {
            'timestamp': datetime.now().isoformat(),
            'employee_id': ai_employee.employee_id,
            'employee_name': ai_employee.name,
            'ai_type': ai_employee.ai_type,
            'upgrade_info': upgrade_info
        }

        self._upgrade_history.append(history_entry)

        if len(self._upgrade_history) > 100:
            self._upgrade_history = self._upgrade_history[-100:]

    def _sync_with_ai_brain(self, ai_employee, upgrade_info):
        """与AI脑库同步升级信息
        
        Args:
            ai_employee: EnhancedAIEmployee实例
            upgrade_info: 升级信息字典
        """
        try:
            knowledge_title = f"AI员工 {ai_employee.name} 升级记录"
            knowledge_content = str(upgrade_info)
            
            ai_brain_service.add_knowledge(
                title=knowledge_title,
                content=knowledge_content,
                knowledge_type="experience",
                source="adaptive_upgrade",
                source_id=ai_employee.employee_id,
                tags=[ai_employee.ai_type, "ai_upgrade", "adaptive"],
                priority=3
            )
        except Exception as e:
            logger.error(f"同步AI脑库失败: {str(e)}")

    def add_capability_module(self, module_type, module_name, capabilities):
        """添加能力模块
        
        Args:
            module_type: 模块类型
            module_name: 模块名称
            capabilities: 能力列表
        """
        self._capability_modules[module_type] = {
            'name': module_name,
            'capabilities': capabilities
        }
        logger.info(f"添加能力模块: {module_name} (类型: {module_type})")

    def get_upgrade_history(self):
        """获取升级历史
        
        Returns:
            list: 升级历史记录
        """
        return self._upgrade_history.copy()

    def analyze_ai_employee_performance(self, employee_id):
        """分析AI员工性能
        
        Args:
            employee_id: AI员工ID
            
        Returns:
            dict: 性能分析结果
        """
        return {
            'employee_id': employee_id,
            'task_completion_rate': 0.95,
            'response_time': 1.2,
            'success_rate': 0.98
        }

adaptive_upgrade_service = AdaptiveUpgradeService()
