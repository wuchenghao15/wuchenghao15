#!/usr/bin/env python3
"""
AI自我修复与升级模块
负责自动发现问题、分析问题并执行修复操作
"""

import threading
import time
import traceback
from app.utils.logging import logger
from app.config import Config

class SelfHealingSystem:
    """AI自我修复系统，负责自动发现和修复问题"""
    
    def __init__(self, ai_instance_manager):
        self.ai_instance_manager = ai_instance_manager
        self.detection_interval = Config.SELF_HEALING_INTERVAL if hasattr(Config, 'SELF_HEALING_INTERVAL') else 300
        self.fix_history = []
        self.running = False
        self.thread = None
        self.issue_detectors = {
            'instance_health': self.detect_instance_health,
            'configuration_issues': self.detect_configuration_issues,
            'resource_leaks': self.detect_resource_leaks,
            'performance_issues': self.detect_performance_issues,
            'dependency_issues': self.detect_dependency_issues
        }
        self.issue_fixers = {
            'instance_health': self.fix_instance_health,
            'configuration_issues': self.fix_configuration_issues,
            'resource_leaks': self.fix_resource_leaks,
            'performance_issues': self.fix_performance_issues,
            'dependency_issues': self.fix_dependency_issues
        }
    
    def start(self):
        """启动自我修复系统后台线程"""
        if not self.running:
            self.running = True
            self.thread = threading.Thread(target=self._run_detection_loop, daemon=True)
            self.thread.start()
            logger.info(f"AI自我修复系统已启动，检测间隔: {self.detection_interval}秒")
    
    def stop(self):
        """停止自我修复系统"""
        self.running = False
        if self.thread:
            self.thread.join()
            self.thread = None
        logger.info("AI自我修复系统已停止")
    
    def _run_detection_loop(self):
        """运行检测循环"""
        while self.running:
            try:
                self.perform_comprehensive_check()
            except Exception as e:
                logger.error(f"自我修复系统检测循环出错: {str(e)}")
                traceback.print_exc()
            time.sleep(self.detection_interval)
    
    def perform_comprehensive_check(self):
        """执行全面检查"""
        logger.info("开始执行全面问题检测...")
        detected_issues = []
        
        # 运行所有检测器
        for detector_name, detector_func in self.issue_detectors.items():
            try:
                issues = detector_func()
                if issues:
                    detected_issues.extend(issues)
            except Exception as e:
                logger.error(f"检测器 {detector_name} 执行出错: {str(e)}")
                traceback.print_exc()
        
        # 修复检测到的问题
        if detected_issues:
            logger.info(f"共检测到 {len(detected_issues)} 个问题，开始修复...")
            self.fix_issues(detected_issues)
        else:
            logger.info("未检测到问题")
    
    def detect_instance_health(self):
        """检测AI实例健康状况"""
        issues = []
        instances = self.ai_instance_manager.ai_instances.values()
        
        for instance in instances:
            # 检查实例状态
            if instance['status'] != 'active':
                issues.append({
                    'type': 'instance_health',
                    'severity': 'medium',
                    'description': f"AI实例 {instance['instance_id']} 状态异常: {instance['status']}",
                    'instance_id': instance['instance_id'],
                    'details': {'current_status': instance['status'], 'expected_status': 'active'}
                })
            
            # 检查实例最后使用时间
            if time.time() - instance['last_used'] > 3600 * 24:  # 超过24小时未使用
                issues.append({
                    'type': 'instance_health',
                    'severity': 'low',
                    'description': f"AI实例 {instance['instance_id']} 长时间未使用",
                    'instance_id': instance['instance_id'],
                    'details': {'last_used': instance['last_used']}
                })
        
        return issues
    
    def detect_configuration_issues(self):
        """检测配置问题"""
        issues = []
        instances = self.ai_instance_manager.ai_instances.values()
        
        for instance in instances:
            config = instance.get('config', {})
            
            # 检查配置版本
            if 'version' not in config or config['version'] < 1.2:
                issues.append({
                    'type': 'configuration_issues',
                    'severity': 'medium',
                    'description': f"AI实例 {instance['instance_id']} 配置版本过低",
                    'instance_id': instance['instance_id'],
                    'details': {'current_version': config.get('version'), 'expected_version': 1.2}
                })
            
            # 检查必要配置项
            if not instance.get('functions') or not instance.get('responsibilities'):
                issues.append({
                    'type': 'configuration_issues',
                    'severity': 'high',
                    'description': f"AI实例 {instance['instance_id']} 缺少必要的功能或责任配置",
                    'instance_id': instance['instance_id'],
                    'details': {'has_functions': bool(instance.get('functions')), 'has_responsibilities': bool(instance.get('responsibilities'))}
                })
        
        return issues
    
    def detect_resource_leaks(self):
        """检测资源泄漏问题"""
        issues = []
        instances = self.ai_instance_manager.ai_instances.values()
        
        # 检查沙盒资源泄漏
        from app.ai.sandbox_manager import sandbox_manager
        if sandbox_manager.is_sandbox_enabled():
            for instance in instances:
                sandbox = instance.get('sandbox')
                if sandbox and sandbox.get('status') == 'running':
                    # 检查沙盒运行时间
                    if 'created_at' in sandbox:
                        sandbox_uptime = time.time() - sandbox['created_at']
                        if sandbox_uptime > 3600:  # 沙盒运行超过1小时
                            issues.append({
                                'type': 'resource_leaks',
                                'severity': 'medium',
                                'description': f"AI实例 {instance['instance_id']} 的沙盒运行时间过长",
                                'instance_id': instance['instance_id'],
                                'details': {'sandbox_uptime': sandbox_uptime, 'sandbox_id': sandbox.get('sandbox_id')}
                            })
        
        return issues
    
    def detect_performance_issues(self):
        """检测性能问题"""
        issues = []
        # 这里可以添加性能检测逻辑
        # 例如：检查CPU使用率、内存使用情况等
        return issues
    
    def detect_dependency_issues(self):
        """检测依赖问题"""
        issues = []
        # 这里可以添加依赖检测逻辑
        # 例如：检查必要服务是否可用
        return issues
    
    def fix_issues(self, issues):
        """修复检测到的问题"""
        for issue in issues:
            try:
                fixer_func = self.issue_fixers.get(issue['type'])
                if fixer_func:
                    result = fixer_func(issue)
                    if result:
                        logger.info(f"成功修复问题: {issue['description']}")
                        self.fix_history.append({
                            'issue': issue,
                            'fixed_at': time.time(),
                            'result': 'success'
                        })
                    else:
                        logger.warning(f"修复问题失败: {issue['description']}")
                        self.fix_history.append({
                            'issue': issue,
                            'fixed_at': time.time(),
                            'result': 'failed'
                        })
                else:
                    logger.warning(f"未找到修复器: {issue['type']}")
            except Exception as e:
                logger.error(f"修复问题出错: {issue['description']} - {str(e)}")
                traceback.print_exc()
                self.fix_history.append({
                    'issue': issue,
                    'fixed_at': time.time(),
                    'result': 'error',
                    'error': str(e)
                })
    
    def fix_instance_health(self, issue):
        """修复实例健康问题"""
        instance_id = issue['instance_id']
        instance = self.ai_instance_manager.get_ai_instance(instance_id)
        
        if instance:
            if instance['status'] != 'active':
                # 更新实例状态为active
                return self.ai_instance_manager.update_ai_instance(instance_id, {'status': 'active'})
            
            # 对于长时间未使用的实例，可以选择优化或保留
            # 这里选择优化配置
            if 'last_used' in issue['details']:
                return self.ai_instance_manager.auto_upgrade()
        
        return False
    
    def fix_configuration_issues(self, issue):
        """修复配置问题"""
        instance_id = issue['instance_id']
        instance = self.ai_instance_manager.get_ai_instance(instance_id)
        
        if instance:
            # 运行自动升级来修复配置问题
            return self.ai_instance_manager.auto_upgrade()
        
        return False
    
    def fix_resource_leaks(self, issue):
        """修复资源泄漏问题"""
        instance_id = issue['instance_id']
        instance = self.ai_instance_manager.get_ai_instance(instance_id)
        
        if instance and 'sandbox' in instance:
            # 重置沙盒
            from app.ai.sandbox_manager import sandbox_manager
            if sandbox_manager.is_sandbox_enabled():
                sandbox_manager.destroy_sandbox(instance_id)
                sandbox = sandbox_manager.create_sandbox(instance_id, instance['ai_type'])
                if sandbox:
                    instance['sandbox'] = sandbox
                    return True
        
        return False
    
    def fix_performance_issues(self, issue):
        """修复性能问题"""
        # 这里可以添加性能修复逻辑
        return False
    
    def fix_dependency_issues(self, issue):
        """修复依赖问题"""
        # 这里可以添加依赖修复逻辑
        return False
    
    def get_fix_history(self, limit=10):
        """获取修复历史"""
        return self.fix_history[-limit:]
    
    def get_system_health(self):
        """获取系统健康状况"""
        stats = self.ai_instance_manager.get_instance_stats()
        
        # 运行快速检查
        detected_issues = []
        for detector_name, detector_func in self.issue_detectors.items():
            try:
                issues = detector_func()
                if issues:
                    detected_issues.extend(issues)
            except Exception as e:
                logger.error(f"快速健康检查出错: {str(e)}")
        
        health_score = 100
        if detected_issues:
            # 基于问题数量和严重程度计算健康分数
            for issue in detected_issues:
                if issue['severity'] == 'high':
                    health_score -= 20
                elif issue['severity'] == 'medium':
                    health_score -= 10
                else:
                    health_score -= 5
            
            health_score = max(0, min(100, health_score))
        
        return {
            'health_score': health_score,
            'detected_issues': detected_issues,
            'instance_stats': stats,
            'last_check_time': time.time()
        }
