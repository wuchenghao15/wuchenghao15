# -*- coding: utf-8 -*-
"""
AgentOrchestrator - Agent编排器
协调5大核心Agent之间的协作流程
实现异常捕捉→代码寻断→自动修复→运维巡检→版本升级的完整链路
"""
import json
import logging
import threading
import time
from datetime import datetime
from typing import Dict, Any, List

logger = logging.getLogger(__name__)


class AgentOrchestrator:
    """Agent编排器"""
    
    _instance = None
    _lock = threading.Lock()
    
    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        if hasattr(self, '_initialized'):
            return
        
        self._initialized = True
        self.agents = {}
        self.workflow_running = False
        self._init_agents()
    
    def _init_agents(self):
        """初始化所有核心Agent"""
        try:
            from app.agents.exception_capture_agent import ExceptionCaptureAgent
            from app.agents.code_debug_agent import CodeDebugAgent
            from app.agents.auto_fix_agent import AutoFixAgent
            from app.agents.ops_inspection_agent import OpsInspectionAgent
            from app.agents.version_upgrade_agent import VersionUpgradeAgent
            from app.agents.deployment_architecture_agent import DeploymentArchitectureAgent
            
            self.agents['exception_capture'] = ExceptionCaptureAgent()
            self.agents['code_debug'] = CodeDebugAgent()
            self.agents['auto_fix'] = AutoFixAgent()
            self.agents['ops_inspection'] = OpsInspectionAgent()
            self.agents['version_upgrade'] = VersionUpgradeAgent()
            self.agents['deployment_architecture'] = DeploymentArchitectureAgent()
            
            logger.info("[Agent编排器] 5大核心Agent初始化完成")
        except Exception as e:
            logger.error(f"[Agent编排器] 初始化Agent失败: {e}")
    
    def get_agent(self, agent_type: str):
        """获取指定类型的Agent"""
        return self.agents.get(agent_type)
    
    def get_all_agents(self) -> Dict:
        """获取所有Agent"""
        return {k: v.get_status() for k, v in self.agents.items()}
    
    def run_workflow(self, workflow_type: str = 'full', context: Dict = None) -> Dict:
        """运行工作流"""
        if self.workflow_running:
            return {'success': False, 'error': '工作流已在运行中'}
        
        self.workflow_running = True
        
        try:
            workflows = {
                'full': self._run_full_workflow,
                'debug_fix': self._run_debug_fix_workflow,
                'ops_check': self._run_ops_check_workflow,
                'upgrade': self._run_upgrade_workflow,
                'architecture': self._run_architecture_workflow
            }
            
            if workflow_type not in workflows:
                return {'success': False, 'error': f'未知工作流类型: {workflow_type}'}
            
            result = workflows[workflow_type](context)
            
            return {
                'success': True,
                'workflow_type': workflow_type,
                'timestamp': datetime.now().isoformat(),
                'result': result
            }
        
        finally:
            self.workflow_running = False
    
    def _run_full_workflow(self, context: Dict = None) -> Dict:
        """运行完整工作流"""
        logger.info("[Agent编排器] 开始运行完整工作流")
        
        results = {}
        
        results['step_1_exception_capture'] = self._run_exception_capture()
        
        if results['step_1_exception_capture'].get('success'):
            error_count = results['step_1_exception_capture'].get('error_count', 0)
            
            if error_count > 0:
                results['step_2_code_debug'] = self._run_code_debug()
                
                if results['step_2_code_debug'].get('success'):
                    issues = results['step_2_code_debug'].get('issues', [])
                    
                    if issues:
                        results['step_3_auto_fix'] = self._run_auto_fix({'issues': issues})
        
        results['step_4_ops_inspection'] = self._run_ops_inspection()
        
        return results
    
    def _run_debug_fix_workflow(self, context: Dict = None) -> Dict:
        """运行调试修复工作流"""
        logger.info("[Agent编排器] 开始运行调试修复工作流")
        
        results = {}
        
        results['code_debug'] = self._run_code_debug()
        
        if results['code_debug'].get('success'):
            issues = results['code_debug'].get('issues', [])
            
            if issues:
                results['auto_fix'] = self._run_auto_fix({'issues': issues})
        
        return results
    
    def _run_ops_check_workflow(self, context: Dict = None) -> Dict:
        """运行运维巡检工作流"""
        logger.info("[Agent编排器] 开始运行运维巡检工作流")
        
        results = {}
        results['ops_inspection'] = self._run_ops_inspection()
        
        return results
    
    def _run_upgrade_workflow(self, context: Dict = None) -> Dict:
        """运行版本升级工作流"""
        logger.info("[Agent编排器] 开始运行版本升级工作流")
        
        results = {}
        results['version_check'] = self._run_version_upgrade({'action': 'check'})
        
        if context and context.get('action') == 'upgrade':
            results['version_upgrade'] = self._run_version_upgrade(context)
        
        return results
    
    def _run_architecture_workflow(self, context: Dict = None) -> Dict:
        """运行部署架构工作流"""
        logger.info("[Agent编排器] 开始运行部署架构工作流")
        
        results = {}
        results['discover'] = self._run_deployment_architecture({'action': 'discover'})
        
        if context and context.get('action') == 'plan':
            results['plan'] = self._run_deployment_architecture(context)
        
        return results
    
    def _run_exception_capture(self, context: Dict = None) -> Dict:
        """运行异常捕捉Agent"""
        agent = self.agents.get('exception_capture')
        if agent:
            return agent.execute(context)
        return {'success': False, 'error': '异常捕捉Agent未初始化'}
    
    def _run_code_debug(self, context: Dict = None) -> Dict:
        """运行代码问题寻断Agent"""
        agent = self.agents.get('code_debug')
        if agent:
            return agent.execute(context)
        return {'success': False, 'error': '代码问题寻断Agent未初始化'}
    
    def _run_auto_fix(self, context: Dict = None) -> Dict:
        """运行自动修复Agent"""
        agent = self.agents.get('auto_fix')
        if agent:
            return agent.execute(context)
        return {'success': False, 'error': '自动修复Agent未初始化'}
    
    def _run_ops_inspection(self, context: Dict = None) -> Dict:
        """运行运维巡检Agent"""
        agent = self.agents.get('ops_inspection')
        if agent:
            return agent.execute(context)
        return {'success': False, 'error': '运维巡检Agent未初始化'}
    
    def _run_version_upgrade(self, context: Dict = None) -> Dict:
        """运行版本迭代升级Agent"""
        agent = self.agents.get('version_upgrade')
        if agent:
            return agent.execute(context)
        return {'success': False, 'error': '版本迭代升级Agent未初始化'}
    
    def _run_deployment_architecture(self, context: Dict = None) -> Dict:
        """运行部署架构Agent"""
        agent = self.agents.get('deployment_architecture')
        if agent:
            return agent.execute(context)
        return {'success': False, 'error': '部署架构Agent未初始化'}
    
    def start_scheduled_tasks(self):
        """启动定时任务"""
        logger.info("[Agent编排器] 启动定时任务")
        
        def scheduled_ops_inspection():
            while True:
                try:
                    self._run_ops_inspection()
                except Exception as e:
                    logger.error(f"[Agent编排器] 定时运维巡检失败: {e}")
                time.sleep(3600)
        
        def scheduled_exception_scan():
            while True:
                try:
                    self._run_exception_capture()
                except Exception as e:
                    logger.error(f"[Agent编排器] 定时异常扫描失败: {e}")
                time.sleep(600)
        
        threading.Thread(target=scheduled_ops_inspection, daemon=True).start()
        threading.Thread(target=scheduled_exception_scan, daemon=True).start()
        
        logger.info("[Agent编排器] 定时任务已启动")


def get_orchestrator() -> AgentOrchestrator:
    """获取Agent编排器实例"""
    return AgentOrchestrator()


def init_orchestrator():
    """初始化Agent编排器"""
    orchestrator = get_orchestrator()
    orchestrator.start_scheduled_tasks()
    return orchestrator
