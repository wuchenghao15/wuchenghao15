# -*- coding: utf-8 -*-
# MTSCOS AI Project 路由管理系统

"""
集中管理所有路由注册,包括API路由和视图路由
"""

from flask import Flask
from typing import Dict, List, Any
from app.utils.logging import logger


class RouteManager:
    """路由管理器,负责集中管理和注册所有路由"""

    def __init__(self):
        self.api_routes: List[Dict[str, Any]] = []
        self.view_routes: List[Dict[str, Any]] = []
        self.registered_routes: List[str] = []

    def register_api_blueprint(self, blueprint, url_prefix: str, description: str = ""):
        """注册API蓝图

        Args:
            blueprint: Flask蓝图对象
            url_prefix: URL前缀
            description: 蓝图描述
        """
        self.api_routes.append({
            'blueprint': blueprint,
            'url_prefix': url_prefix,
            'description': description
        })

    def register_view_blueprint(self, blueprint, url_prefix: str, description: str = ""):
        """注册视图蓝图

        Args:
            blueprint: Flask蓝图对象
            url_prefix: URL前缀
            description: 蓝图描述
        """
        self.view_routes.append({
            'blueprint': blueprint,
            'url_prefix': url_prefix,
            'description': description
        })

    def register_all_routes(self, app: Flask):
        """注册所有路由到Flask应用

        Args:
            app: Flask应用实例
        """
        logger.info("开始注册所有路由...")
        
        # 注册API路由
        for route in self.api_routes:
            try:
                app.register_blueprint(route['blueprint'], url_prefix=route['url_prefix'])
                logger.info(f"✓ API路由注册成功: {route['blueprint'].name} -> {route['url_prefix']}")
                self.registered_routes.append(f"API: {route['blueprint'].name} -> {route['url_prefix']}")
            except Exception as e:
                logger.error(f"✗ API路由注册失败: {route['blueprint'].name} -> {route['url_prefix']}, 错误: {str(e)}")

        # 注册视图路由
        logger.info("注册视图路由...")
        for route in self.view_routes:
            try:
                app.register_blueprint(route['blueprint'], url_prefix=route['url_prefix'])
                logger.info(f"✓ 视图路由注册成功: {route['blueprint'].name} -> {route['url_prefix']}")
                self.registered_routes.append(f"VIEW: {route['blueprint'].name} -> {route['url_prefix']}")
            except Exception as e:
                logger.error(f"✗ 视图路由注册失败: {route['blueprint'].name} -> {route['url_prefix']}, 错误: {str(e)}")

        # 注册主路由(首页)
        self._register_main_route(app)

        logger.info("路由注册完成")
        logger.info(f"共注册 {len(self.registered_routes)} 个路由")

    def _register_main_route(self, app: Flask):
        """注册主路由(首页)- 现在由main_bp处理,这里只记录日志

        Args:
            app: Flask应用实例
        """
        logger.info("主路由已由main_bp处理,跳过重复注册")

    def get_registered_routes(self) -> List[str]:
        """获取已注册的路由列表

        Returns:
            已注册路由列表
        """
        return self.registered_routes.copy()

    def print_routes(self):
        """打印已注册的路由"""
        logger.info("已注册路由列表:")
        for route in self.registered_routes:
            logger.info(f"  - {route}")


# 创建全局路由管理器实例
route_manager = RouteManager()


def init_api_routes():
    """初始化API路由"""
    logger.info("初始化API路由...")

    # 认证API
    try:
        from app.api.auth_api import auth_api
        route_manager.register_api_blueprint(
            auth_api,
            url_prefix="",
            description="认证API"
        )
    except Exception as e:
        logger.error(f"初始化认证API路由失败: {str(e)}")

    # 报关数据API
    try:
        from app.api.customs_api import customs_api
        route_manager.register_api_blueprint(
            customs_api,
            url_prefix="",
            description="报关数据API"
        )
    except Exception as e:
        logger.error(f"初始化报关数据API路由失败: {str(e)}")

    # AI自动学习升级API
    try:
        from app.api.auto_learning_api import auto_learning_api
        route_manager.register_api_blueprint(
            auto_learning_api,
            url_prefix="",
            description="AI自动学习升级API"
        )
    except Exception as e:
        logger.error(f"初始化AI自动学习升级API路由失败: {str(e)}")

    # AI脑库学习API
    try:
        from app.api.brain_learning_api import brain_learning_api
        route_manager.register_api_blueprint(
            brain_learning_api,
            url_prefix="",
            description="AI脑库学习API"
        )
    except Exception as e:
        logger.error(f"初始化AI脑库学习API路由失败: {str(e)}")

    # 自动计划调度API
    try:
        from app.api.scheduler_api import scheduler_api
        route_manager.register_api_blueprint(
            scheduler_api,
            url_prefix="",
            description="自动计划调度API"
        )
    except Exception as e:
        logger.error(f"初始化自动计划调度API路由失败: {str(e)}")

    # 路由优化API
    try:
        from app.api.route_optimization_api import route_optimization_api
        route_manager.register_api_blueprint(
            route_optimization_api,
            url_prefix="",
            description="路由优化API"
        )
    except Exception as e:
        logger.error(f"初始化路由优化API路由失败: {str(e)}")

    # AI脑库API
    try:
        from app.blueprints.ai_brain_api import ai_brain_api
        route_manager.register_api_blueprint(
            ai_brain_api,
            url_prefix="/api/ai-brain",
            description="AI脑库API"
        )
    except Exception as e:
        logger.error(f"初始化AI脑库API路由失败: {str(e)}")

    # 学习系统API
    try:
        from app.blueprints.learning_system_api import learning_system_api
        route_manager.register_api_blueprint(
            learning_system_api,
            url_prefix="/api/learning",
            description="学习系统API"
        )
    except Exception as e:
        logger.error(f"初始化学习系统API路由失败: {str(e)}")

    # 规则系统API
    try:
        from app.rules.apis.rule_api import rule_api
        route_manager.register_api_blueprint(
            rule_api,
            url_prefix="/api/rules",
            description="规则系统API"
        )
    except Exception as e:
        logger.error(f"初始化规则系统API路由失败: {str(e)}")

    # 文件系统API
    try:
        from app.filesystem.api import filesystem_bp
        route_manager.register_api_blueprint(
            filesystem_bp,
            url_prefix="/api/filesystem",
            description="文件系统API"
        )
    except Exception as e:
        logger.error(f"初始化文件系统API路由失败: {str(e)}")

    # AI学习API
    try:
        from app.services.ai_learning_api import ai_learning_bp
        route_manager.register_api_blueprint(
            ai_learning_bp,
            url_prefix="/api/ai-learning",
            description="AI学习系统API"
        )
    except Exception as e:
        logger.error(f"初始化AI学习API路由失败: {str(e)}")

    # 服务器系统API
    try:
        from app.api.server_system_api import server_system_bp
        route_manager.register_api_blueprint(
            server_system_bp,
            url_prefix="/api/server-system",
            description="服务器系统API"
        )
    except Exception as e:
        logger.error(f"初始化服务器系统API路由失败: {str(e)}")

    # 防火墙系统API
    try:
        from app.api.firewall_api import firewall_api_bp
        route_manager.register_api_blueprint(
            firewall_api_bp,
            url_prefix="/api/firewall",
            description="防火墙系统API"
        )
    except Exception as e:
        logger.error(f"初始化防火墙系统API路由失败: {str(e)}")

    # 集群管理API
    try:
        from app.api.cluster_api import cluster_api_bp
        route_manager.register_api_blueprint(
            cluster_api_bp,
            url_prefix="/api/cluster",
            description="集群管理API"
        )
    except Exception as e:
        logger.error(f"初始化集群管理API路由失败: {str(e)}")

    # AI员工集群API
    try:
        from app.api.ai_cluster_api import ai_cluster_api_bp
        route_manager.register_api_blueprint(
            ai_cluster_api_bp,
            url_prefix="/api/ai-cluster",
            description="AI员工集群API"
        )
    except Exception as e:
        logger.error(f"初始化AI员工集群API路由失败: {str(e)}")

    # 题库管理API
    try:
        from app.api.question_bank_api import question_bank_api
        route_manager.register_api_blueprint(
            question_bank_api,
            url_prefix="/api/question_bank",
            description="题库管理API(CRUD、AI智能出题、统计分析、导入导出、智能组卷)"
        )
    except Exception as e:
        logger.error(f"初始化题库管理API路由失败: {str(e)}")
    
    # AI题库管理智能助手API（听力题系统）
    try:
        from app.api.question_bank_ai_api import question_bank_ai_api
        route_manager.register_api_blueprint(
            question_bank_ai_api,
            url_prefix="/api/question_bank_ai",
            description="AI题库管理智能助手API(听力题智能生成、多口音多音色、质量分析、智能推荐)"
        )
    except Exception as e:
        logger.error(f"初始化AI题库管理智能助手API路由失败: {str(e)}")

    # 物理引擎和数学模型API
    try:
        from app.api.physics_api import physics_api_bp
        route_manager.register_api_blueprint(
            physics_api_bp,
            url_prefix="",
            description="物理引擎和数学模型API"
        )
    except Exception as e:
        logger.error(f"初始化物理引擎API路由失败: {str(e)}")

    # AI自学习系统API
    try:
        from app.api.self_learning_api import self_learning_api
        route_manager.register_api_blueprint(
            self_learning_api,
            url_prefix="/api/self-learning",
            description="AI自学习系统API"
        )
    except Exception as e:
        logger.error(f"初始化AI自学习系统API路由失败: {str(e)}")

    # 智能仪表盘API
    try:
        from app.routes.intelligent_dashboard_api import intelligent_dashboard_bp
        route_manager.register_api_blueprint(
            intelligent_dashboard_bp,
            url_prefix="",
            description="智能仪表盘API"
        )
    except Exception as e:
        logger.error(f"初始化智能仪表盘API路由失败: {str(e)}")

    # AI线程进程管理器API
    try:
        from app.api.thread_process_manager_api import thread_process_manager_api_bp
        route_manager.register_api_blueprint(
            thread_process_manager_api_bp,
            url_prefix="/api/thread-process-manager",
            description="AI线程进程管理器API"
        )
    except Exception as e:
        logger.error(f"初始化AI线程进程管理器API路由失败: {str(e)}")

    # AI自动更新管理器API
    try:
        from app.api.auto_update_api import auto_update_api_bp
        route_manager.register_api_blueprint(
            auto_update_api_bp,
            url_prefix="/api/auto-update",
            description="AI自动更新管理器API"
        )
    except Exception as e:
        logger.error(f"初始化AI自动更新管理器API路由失败: {str(e)}")

    # 考试测试系统API
    try:
        from app.api.exam_test_api import exam_test_api
        route_manager.register_api_blueprint(
            exam_test_api,
            url_prefix="/api",
            description="考试测试系统API"
        )
    except Exception as e:
        logger.error(f"初始化考试测试系统API路由失败: {str(e)}")

    # 考试超时锁定系统API
    try:
        from app.api.timeout_lock_api import timeout_lock_api
        route_manager.register_api_blueprint(
            timeout_lock_api,
            url_prefix="",
            description="考试超时锁定系统API"
        )
    except Exception as e:
        logger.error(f"初始化考试超时锁定系统API路由失败: {str(e)}")

    # 智能考试助手AI API
    try:
        from app.api.exam_ai_api import exam_ai_api
        route_manager.register_api_blueprint(
            exam_ai_api,
            url_prefix="",
            description="智能考试助手AI API"
        )
    except Exception as e:
        logger.error(f"初始化智能考试助手AI API路由失败: {str(e)}")

    # 本地AI对话API
    try:
        from app.api.ai_chat_api import ai_chat_bp
        route_manager.register_api_blueprint(
            ai_chat_bp,
            url_prefix="",
            description="本地AI对话API"
        )
    except Exception as e:
        logger.error(f"初始化本地AI对话API路由失败: {str(e)}")

    # 用户中心API
    try:
        from app.api.user_center_api import user_center_bp
        route_manager.register_api_blueprint(
            user_center_bp,
            url_prefix="",
            description="用户中心API（个人资料、通知、消息）"
        )
    except Exception as e:
        logger.error(f"初始化用户中心API路由失败: {str(e)}")

    # 系统增强API
    try:
        from app.api.system_enhancement_api import system_enhancement_bp
        route_manager.register_api_blueprint(
            system_enhancement_bp,
            url_prefix="",
            description="系统增强API（文件、搜索、导出）"
        )
    except Exception as e:
        logger.error(f"初始化系统增强API路由失败: {str(e)}")

    # 考试系统优化API
    try:
        from app.blueprints.exam_optimization_api import exam_optimization_api
        route_manager.register_api_blueprint(
            exam_optimization_api,
            url_prefix="/api/exam-optimization",
            description="考试系统优化API(集成错题管理,老师AI和学习分析)"
        )
    except Exception as e:
        logger.error(f"初始化考试系统优化API路由失败: {str(e)}")

    # 锁定系统API
    try:
        from app.views.lock import lock_bp
        route_manager.register_api_blueprint(
            lock_bp,
            url_prefix="",
            description="锁定系统API"
        )
    except Exception as e:
        logger.error(f"初始化锁定系统API路由失败: {str(e)}")

    # 本地存储API
    try:
        from app.views.local_storage import local_storage_bp
        route_manager.register_api_blueprint(
            local_storage_bp,
            url_prefix="",
            description="本地存储API"
        )
    except Exception as e:
        logger.error(f"初始化本地存储API路由失败: {str(e)}")

    logger.info("API路由初始化完成")


def init_view_routes():
    """初始化视图路由"""
    logger.info("初始化视图路由...")

    # 主视图蓝图
    try:
        from app.views.main import main_bp
        route_manager.register_view_blueprint(
            main_bp,
            url_prefix=None,
            description="主视图"
        )
    except Exception as e:
        logger.error(f"初始化主视图路由失败: {str(e)}")

    # 认证视图蓝图
    try:
        from app.views.auth import auth_bp
        route_manager.register_view_blueprint(
            auth_bp,
            url_prefix="/auth",
            description="认证视图"
        )
    except Exception as e:
        logger.error(f"初始化认证视图路由失败: {str(e)}")

    # 系统管理视图蓝图
    try:
        from app.views.system import system_bp
        route_manager.register_view_blueprint(
            system_bp,
            url_prefix="/system",
            description="系统管理视图"
        )
    except Exception as e:
        logger.error(f"初始化系统管理视图路由失败: {str(e)}")

    # AI管理视图蓝图
    try:
        from app.views.ai import ai_bp
        route_manager.register_view_blueprint(
            ai_bp,
            url_prefix="/ai",
            description="AI管理视图"
        )
    except Exception as e:
        logger.error(f"初始化AI管理视图路由失败: {str(e)}")

    # 监控管理视图蓝图
    try:
        from app.routes.monitoring import monitoring_bp
        route_manager.register_view_blueprint(
            monitoring_bp,
            url_prefix="/monitoring",
            description="监控管理视图"
        )
    except Exception as e:
        logger.error(f"初始化监控管理视图路由失败: {str(e)}")

    # 安全监控视图蓝图
    try:
        from app.routes.security import security_bp
        route_manager.register_view_blueprint(
            security_bp,
            url_prefix="/security",
            description="安全监控视图"
        )
    except Exception as e:
        logger.error(f"初始化安全监控视图路由失败: {str(e)}")

    # 用户管理视图蓝图
    try:
        from app.routes.user_manager import user_manager_bp
        route_manager.register_view_blueprint(
            user_manager_bp,
            url_prefix="/user-manager",
            description="用户管理视图"
        )
    except Exception as e:
        logger.error(f"初始化用户管理视图路由失败: {str(e)}")

    # 整合设计页面蓝图
    try:
        from app.views.integrated_design import integrated_design_bp
        route_manager.register_view_blueprint(
            integrated_design_bp,
            url_prefix="/integrated-design",
            description="整合设计页面"
        )
    except Exception as e:
        logger.error(f"初始化整合设计页面路由失败: {str(e)}")

    # 语言测试系统路由
    try:
        from app.views.language_tests import language_tests_bp
        route_manager.register_view_blueprint(
            language_tests_bp,
            url_prefix="",
            description="语言测试系统"
        )
    except Exception as e:
        logger.error(f"初始化语言测试系统路由失败: {str(e)}")

    # 集成设置视图蓝图
    try:
        from app.blueprints.integrated_settings import integrated_settings_bp
        route_manager.register_view_blueprint(
            integrated_settings_bp,
            url_prefix="/settings",
            description="集成设置视图"
        )
    except Exception as e:
        logger.error(f"初始化集成设置路由失败: {str(e)}")

    # 物理引擎视图蓝图
    try:
        from app.views.physics_engine import physics_engine_bp, init_physics_permissions
        route_manager.register_view_blueprint(
            physics_engine_bp,
            url_prefix="/physics-engine",
            description="物理引擎与粒子系统视图"
        )
        init_physics_permissions()
    except Exception as e:
        logger.error(f"初始化物理引擎视图路由失败: {str(e)}")

    # 考试系统视图蓝图
    try:
        from app.views.exam_system import exam_system_bp
        route_manager.register_view_blueprint(
            exam_system_bp,
            url_prefix="",
            description="考试系统视图"
        )
    except Exception as e:
        logger.error(f"初始化考试系统视图路由失败: {str(e)}")

    # 教师系统视图蓝图
    try:
        from app.views.teacher import teacher_bp
        route_manager.register_view_blueprint(
            teacher_bp,
            url_prefix="",
            description="教师系统视图"
        )
    except Exception as e:
        logger.error(f"初始化教师系统视图路由失败: {str(e)}")

    # 系统维护路由
    try:
        from app.routes.maintenance_routes import maintenance_bp, docs_bp
        route_manager.register_view_blueprint(
            maintenance_bp,
            url_prefix="/maintenance",
            description="系统维护路由"
        )
        route_manager.register_view_blueprint(
            docs_bp,
            url_prefix="/docs",
            description="文档路由"
        )
    except Exception as e:
        logger.error(f"初始化系统维护路由失败: {str(e)}")


def init_routes():
    """初始化所有路由"""
    logger.info("初始化所有路由...")
    init_api_routes()
    logger.info("API路由初始化完成")
    logger.info("开始初始化视图路由...")
    init_view_routes()
    logger.info("视图路由初始化完成")
    logger.info("所有路由初始化完成")