#!/usr/bin/env python3
"""
AI自我修复与升级模块
负责自动发现问题, 分析问题并执行修复操作
"""
import threading
import time
import traceback
from app.utils.logging import logger
from app.config import Config

class SelfHealingSystem:
    """AI自我修复系统: 负责自动发现和修复问题"""

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
            logger.info(f"AI自我修复系统已启动,检测间隔: {self.detection_interval}秒")

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

        for detector_name, detector_func in self.issue_detectors.items():
            try:
                issues = detector_func()
                if issues:
                    detected_issues.extend(issues)
            except Exception as e:
                logger.error(f"检测器 {detector_name} 执行出错: {str(e)}")
                traceback.print_exc()

        if detected_issues:
            logger.info(f"共检测到 {len(detected_issues)} 个问题, 开始修复...")
            for issue in detected_issues:
                self._fix_issue(issue)
        else:
            logger.info("未检测到问题")

    def detect_instance_health(self):
        """检测AI实例健康状况"""
        issues = []
        instances = self.ai_instance_manager.ai_instances.values()

        for instance in instances:
            if instance['status'] != 'active':
                issues.append({
                    'type': 'instance_health',
                    'severity': 'medium',
                    'description': f"AI实例 {instance['instance_id']} 状态异常: {instance['status']}",
                    'instance_id': instance['instance_id'],
                    'details': {'current_status': instance['status'], 'expected_status': 'active'}
                })

            if time.time() - instance['last_used'] > 3600 * 24:
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

            if 'version' not in config or config['version'] < 1.2:
                issues.append({
                    'type': 'configuration_issues',
                    'severity': 'medium',
                    'description': f"AI实例 {instance['instance_id']} 配置版本过低",
                    'instance_id': instance['instance_id'],
                    'details': {'current_version': config.get('version'), 'expected_version': 1.2}
                })

            if not instance.get('functions') and not instance.get('responsibilities'):
                issues.append({
                    'type': 'configuration_issues',
                    'severity': 'high',
                    'description': f"AI实例 {instance['instance_id']} 缺少必要的功能或责任配置",
                    'details': {'has_functions': bool(instance.get('functions')), 'has_responsibilities': bool(instance.get('responsibilities'))}
                })

        return issues

    def detect_resource_leaks(self):
        """检测资源泄漏问题"""
        issues = []
        instances = self.ai_instance_manager.ai_instances.values()

        try:
            from app.ai.sandbox_manager import sandbox_manager
            if sandbox_manager.is_sandbox_enabled():
                for instance in instances:
                    sandbox = instance.get('sandbox')
                    if sandbox and sandbox.get('status') == 'running':
                        sandbox_uptime = time.time() - sandbox['created_at']
                        if sandbox_uptime > 3600:
                            issues.append({
                                'type': 'resource_leaks',
                                'severity': 'medium',
                                'description': f"AI实例 {instance['instance_id']} 的沙盒运行时间过长",
                                'instance_id': instance['instance_id'],
                                'details': {'sandbox_uptime': sandbox_uptime, 'sandbox_id': sandbox.get('sandbox_id')}
                            })
        except ImportError:
            pass

        return issues

    def detect_performance_issues(self):
        """检测性能问题"""
        issues = []
        return issues

    def detect_dependency_issues(self):
        """检测依赖问题"""
        issues = []
        return issues

    def _fix_issue(self, issue):
        """修复问题"""
        issue_type = issue['type']
        if issue_type in self.issue_fixers:
            fixer = self.issue_fixers[issue_type]
            success = fixer(issue)

            self.fix_history.append({
                'issue': issue,
                'success': success,
                'timestamp': time.time()
            })

            if success:
                logger.info(f"问题修复成功: {issue['description']}")
            else:
                logger.warning(f"问题修复失败: {issue['description']}")

    def fix_instance_health(self, issue):
        """修复实例健康问题"""
        instance_id = issue['instance_id']
        instance = self.ai_instance_manager.get_ai_instance(instance_id)

        if instance:
            if instance['status'] != 'active':
                instance['status'] = 'active'
                logger.info(f"已将实例 {instance_id} 状态更新为 active")

            if 'last_used' in issue['details']:
                return self.ai_instance_manager.auto_upgrade()

        return True

    def fix_configuration_issues(self, issue):
        """修复配置问题"""
        instance_id = issue['instance_id']
        instance = self.ai_instance_manager.get_ai_instance(instance_id)

        if instance:
            return self.ai_instance_manager.auto_upgrade()

        return False

    def fix_resource_leaks(self, issue):
        """修复资源泄漏问题"""
        instance_id = issue['instance_id']
        instance = self.ai_instance_manager.get_ai_instance(instance_id)

        if instance and 'sandbox' in instance:
            try:
                from app.ai.sandbox_manager import sandbox_manager
                sandbox_manager.stop_sandbox(instance['sandbox']['sandbox_id'])
                logger.info(f"已停止实例 {instance_id} 的沙盒")
                return True
            except Exception as e:
                logger.error(f"停止沙盒失败: {str(e)}")
                return False

        return False

    def fix_performance_issues(self, issue):
        """修复性能问题"""
        return False

    def fix_dependency_issues(self, issue):
        """修复依赖问题"""
        return False

    def get_fix_history(self, limit=10):
        """获取修复历史"""
        return self.fix_history[-limit:]

    def get_system_health(self):
        """获取系统健康状况"""
        stats = self.ai_instance_manager.get_instance_stats()

        detected_issues = []
        for detector_name, detector_func in self.issue_detectors.items():
            try:
                issues = detector_func()
                if issues:
                    detected_issues.extend(issues)
            except Exception as e:
                logger.error(f"快速健康检查出错: {str(e)}")

        health_score = 100
        for issue in detected_issues:
            if issue['severity'] == 'high':
                health_score -= 20
            elif issue['severity'] == 'medium':
                health_score -= 10
            elif issue['severity'] == 'low':
                health_score -= 5

        health_score = max(0, health_score)

        return {
            'health_score': health_score,
            'detected_issues': detected_issues,
            'stats': stats
        }
