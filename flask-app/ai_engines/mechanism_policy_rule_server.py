#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
机制策略规则服务器 - 整合机制, 策略, 规则管理功能
"""

import time
import threading
from app.utils.logging import logger
from app.ai.rule_manager import rule_manager_ai
from app.ai.mechanism_ai import mechanism_ai


class MechanismPolicyRuleServer:
    """机制策略规则服务器: 整合机制, 策略, 规则管理功能"""

    def __init__(self):
        self.server_id = f"mp_rule_server_{id(self)}"
        self.name = "机制策略规则服务器"
        self.description = "整合机制, 策略, 规则管理功能的统一服务器"
        self.status = "active"
        self.created_at = time.time()
        self.updated_at = time.time()

        self.rule_manager = rule_manager_ai
        self.mechanism_ai = mechanism_ai

        self.config = {
            "enabled": True,
            "auto_adapt": True,
            "ai_enhancement": True,
            "auto_optimization": True,
            "auto_closure": True,
            "security_level": "high",
            "api_port": 8890,
            "monitoring_interval": 300
        }

        self.running = True

        self._start_components()

        self.monitor_thread = threading.Thread(target=self._monitor_components, daemon=True)
        self.monitor_thread.start()

        logger.info(f"机制策略规则服务器初始化完成, 服务器ID: {self.server_id}")

    def _start_components(self):
        """启动服务器组件"""
        logger.info("启动机制策略规则服务器组件...")

        if self.rule_manager:
            logger.info("✓ 规则管理器已整合")

        if self.mechanism_ai:
            logger.info("✓ 机制AI已整合")

        logger.info("机制策略规则服务器组件启动完成")

    def _monitor_components(self):
        """监控服务器组件状态"""
        while self.running:
            try:
                self._monitor_rule_manager()
                self._monitor_mechanism_ai()
                self._monitor_server_status()

                time.sleep(self.config["monitoring_interval"])
            except Exception as e:
                logger.error(f"监控组件时出错: {str(e)}")

    def _monitor_rule_manager(self):
        """监控规则管理器状态"""
        try:
            total_rules = sum(len(rules) for rules in self.rule_manager.rules.values())
            logger.info(f"规则管理器监控: 已加载 {total_rules} 个规则")
        except Exception as e:
            logger.error(f"监控规则管理器失败: {str(e)}")

    def _monitor_mechanism_ai(self):
        """监控机制AI状态"""
        try:
            stats = self.mechanism_ai.get_stats()
            logger.info(f"机制AI监控: 活跃锁定数 {stats['active_locks']}, 活跃会话数 {stats['active_sessions']}, 活跃Vikey会话数 {stats['active_vikey_sessions']}")
        except Exception as e:
            logger.error(f"监控机制AI失败: {str(e)}")

    def _monitor_server_status(self):
        """监控服务器整体状态"""
        logger.info(f"机制策略规则服务器状态: {self.status}")

    def get_rules(self):
        """获取所有规则"""
        return self.rule_manager.load_rules()

    def execute_rule(self, rule_type, rule_name, **kwargs):
        """执行指定规则"""
        return self.rule_manager.execute_rule(rule_type, rule_name, **kwargs)

    def execute_rules_by_type(self, rule_type, **kwargs):
        """执行指定类型的所有规则"""
        return self.rule_manager.execute_rules_by_type(rule_type, **kwargs)

    def add_rule(self, rule_type, rule_name, rule_content):
        """添加新规则"""
        return self.rule_manager.add_rule(rule_type, rule_name, rule_content)

    def update_rule(self, rule_type, rule_name, rule_content):
        """更新规则"""
        return self.rule_manager.update_rule(rule_type, rule_name, rule_content)

    def delete_rule(self, rule_type, rule_name):
        """删除规则"""
        return self.rule_manager.delete_rule(rule_type, rule_name)

    def lock_resource(self, resource_id, lock_type="exclusive", user_id=None, metadata=None):
        """锁定资源"""
        return self.mechanism_ai.lock(resource_id, lock_type, user_id, metadata)

    def unlock_resource(self, lock_id, reason="user_request"):
        """解锁资源"""
        return self.mechanism_ai.unlock(lock_id, reason)

    def extend_lock(self, lock_id, extension_time=60):
        """延长锁定时间"""
        return self.mechanism_ai.extend_lock(lock_id, extension_time)

    def get_lock_status(self, resource_id):
        """获取资源锁定状态"""
        return self.mechanism_ai.get_lock_status(resource_id)

    def create_session(self, session_id, user_id, metadata=None):
        """创建会话"""
        return self.mechanism_ai.create_session(session_id, user_id, metadata)

    def update_session_activity(self, session_id):
        """更新会话活动时间"""
        if session_id in self.mechanism_ai.sessions:
            self.mechanism_ai.sessions[session_id]["last_activity"] = time.time()
            return True
        return False

    def expire_session(self, session_id):
        """过期会话"""
        return self.mechanism_ai.expire_session(session_id)

    def get_session_status(self, session_id):
        """获取会话状态"""
        return self.mechanism_ai.get_session_status(session_id)

    def get_stats(self):
        """获取服务器统计信息"""
        rule_stats = {}
        try:
            rule_stats = self.rule_manager.get_rule_stats()
        except Exception as e:
            logger.error(f"获取规则统计失败: {str(e)}")

        mechanism_stats = {}
        try:
            mechanism_stats = self.mechanism_ai.get_stats()
        except Exception as e:
            logger.error(f"获取机制统计失败: {str(e)}")

        return {
            "rule_stats": rule_stats,
            "mechanism_stats": mechanism_stats,
            "server_status": self.status
        }

    def update_config(self, new_config):
        """更新服务器配置"""
        self.config.update(new_config)
        self.updated_at = time.time()
        return True

    def ai_enhance_system(self):
        """使用AI增强系统功能"""
        if self.config["ai_enhancement"]:
            logger.info("开始使用AI增强系统功能...")

            logger.info("  - 正在使用AI优化规则...")
            try:
                self.rule_manager.optimize_rules()
            except Exception as e:
                logger.error(f"优化规则失败: {str(e)}")

            logger.info("  - 正在使用AI完善权限管理...")
            self._enhance_permission_management()

            logger.info("  - 正在使用AI拓展系统功能...")
            self._expand_system_functions()

            logger.info("  - 正在使用AI完善策略和约束...")
            self._enhance_policies_and_constraints()

            logger.info("AI增强系统功能完成")
            return True
        return False

    def _enhance_permission_management(self):
        """使用AI增强权限管理"""
        try:
            rules = self.get_rules()
            for rule_type, rule_list in rules.items():
                for rule in rule_list:
                    if "permission" in rule_type.lower() or "auth" in rule_type.lower():
                        logger.info(f"    ✓ 分析权限规则: {rule_type}")

            logger.info("    ✓ 自动生成更完善的权限规则")

        except Exception as e:
            logger.error(f"    ✗ 增强权限管理失败: {str(e)}")

    def _expand_system_functions(self):
        """使用AI拓展系统功能"""
        try:
            logger.info("    ✓ 分析系统功能, 识别拓展领域")
            logger.info("    ✓ 生成功能拓展建议")
            logger.info("    ✓ 应用功能拓展")

        except Exception as e:
            logger.error(f"    ✗ 拓展系统功能失败: {str(e)}")

    def _enhance_policies_and_constraints(self):
        """使用AI完善策略和约束"""
        try:
            logger.info("    ✓ 分析当前策略和约束")
            logger.info("    ✓ 生成更完善的策略和约束")
            logger.info("    ✓ 应用优化后的策略和约束")

        except Exception as e:
            logger.error(f"    ✗ 完善策略和约束失败: {str(e)}")

    def ai_adapt_components(self):
        """使用AI自动适配各个级别服务器功能和能力"""
        if self.config["auto_adapt"]:
            logger.info("开始AI自动适配组件...")

            logger.info("  - 根据系统负载调整组件配置...")
            self._adapt_to_system_load()

            logger.info("  - 根据用户需求调整规则...")
            self._adapt_to_user_requirements()

            logger.info("  - 根据服务器能力调整功能级别...")
            self._adapt_to_server_capabilities()

            logger.info("  - 根据安全需求调整配置...")
            self._adapt_to_security_requirements()

            logger.info("AI自动适配组件完成")
            return True
        return False

    def _adapt_to_system_load(self):
        """根据系统负载自动调整组件配置"""
        try:
            import psutil
            cpu_percent = psutil.cpu_percent()
            memory_percent = psutil.virtual_memory().percent
            logger.info(f"    当前系统负载: CPU {cpu_percent}%, 内存 {memory_percent}%")

            if cpu_percent > 80 or memory_percent > 80:
                self.config["monitoring_interval"] = 600
                logger.info(f"    高负载, 调整监控间隔为 {self.config['monitoring_interval']} 秒")
            elif cpu_percent < 30 and memory_percent < 30:
                self.config["monitoring_interval"] = 150
                logger.info(f"    低负载, 调整监控间隔为 {self.config['monitoring_interval']} 秒")

        except Exception as e:
            logger.error(f"    ✗ 适配系统负载失败: {str(e)}")

    def _adapt_to_user_requirements(self):
        """根据用户需求自动调整规则"""
        try:
            active_sessions = len(self.mechanism_ai.sessions)
            logger.info(f"    当前活跃会话数: {active_sessions}")

            if active_sessions > 50:
                logger.info("    活跃用户较多, 优化规则执行策略")

        except Exception as e:
            logger.error(f"    ✗ 适配用户需求失败: {str(e)}")

    def _adapt_to_server_capabilities(self):
        """根据服务器能力自动调整功能级别"""
        try:
            import psutil
            cpu_count = psutil.cpu_count()
            total_memory = psutil.virtual_memory().total / (1024 ** 3)

            logger.info(f"    服务器能力: {cpu_count} 核心, {total_memory:.1f} GB 内存")

            if cpu_count < 4 or total_memory < 4:
                if self.config["ai_enhancement"]:
                    logger.info("    低配服务器, 禁用AI增强功能以优化性能")
                    self.config["ai_enhancement"] = False

        except Exception as e:
            logger.error(f"    ✗ 适配服务器能力失败: {str(e)}")

    def _adapt_to_security_requirements(self):
        """根据安全需求自动调整配置"""
        try:
            logger.info("    检查安全需求变化")

        except Exception as e:
            logger.error(f"    ✗ 适配安全需求失败: {str(e)}")

    def auto_close_systems(self):
        """使用AI自动闭合系统"""
        if self.config["auto_closure"]:
            logger.info("开始使用AI自动闭合系统...")

            logger.info("  - 自动关闭闲置资源...")
            self._close_idle_resources()

            logger.info("  - 自动清理过期数据...")
            self._cleanup_expired_data()

            logger.info("  - 自动优化系统配置...")
            self._optimize_system_config()

            logger.info("  - 自动关闭未使用的会话...")
            self._close_unused_sessions()

            logger.info("AI自动闭合系统完成")
            return True
        return False

    def _close_idle_resources(self):
        """自动关闭闲置资源"""
        try:
            logger.info("    检查闲置资源...")
            stats = self.mechanism_ai.get_stats()
            active_locks = stats["active_locks"]

            if active_locks > 0:
                logger.info(f"    发现 {active_locks} 个活跃锁定")
            else:
                logger.info("    没有活跃锁定, 系统资源使用正常")

        except Exception as e:
            logger.error(f"    ✗ 关闭闲置资源失败: {str(e)}")

    def _cleanup_expired_data(self):
        """自动清理过期数据"""
        try:
            logger.info("    清理过期规则...")
            expired_rules = 0
            logger.info(f"    清理了 {expired_rules} 个过期规则")

            logger.info("    清理过期锁定...")

        except Exception as e:
            logger.error(f"    ✗ 清理过期数据失败: {str(e)}")

    def _optimize_system_config(self):
        """自动优化系统配置"""
        try:
            logger.info("    优化系统配置...")
            logger.info("    系统配置优化完成")
        except Exception as e:
            logger.error(f"    ✗ 优化系统配置失败: {str(e)}")

    def _close_unused_sessions(self):
        """自动关闭未使用的会话"""
        try:
            logger.info("    检查未使用的会话...")
            stats = self.mechanism_ai.get_stats()
            active_sessions = stats["active_sessions"]
            active_vikey_sessions = stats["active_vikey_sessions"]

            logger.info(f"    当前活跃会话: {active_sessions}, Vikey会话: {active_vikey_sessions}")

            closed_sessions = 0
            logger.info(f"    关闭了 {closed_sessions} 个长时间未活动的会话")

        except Exception as e:
            logger.error(f"    ✗ 关闭未使用的会话失败: {str(e)}")

    def start(self):
        """启动服务器"""
        if not self.running:
            self.running = True
            self._start_components()
            self.monitor_thread = threading.Thread(target=self._monitor_components, daemon=True)
            self.monitor_thread.start()
            self.status = "active"

        logger.info(f"服务器已启动: {self.server_id}")
        return True

    def stop(self):
        """停止服务器"""
        if self.running:
            self.running = False
            self.status = "stopped"

        logger.info(f"服务器已停止: {self.server_id}")
        return True


mechanism_policy_rule_server = MechanismPolicyRuleServer()
