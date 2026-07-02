# -*- coding: utf-8 -*-
"""
系统初始化模块 - 统一管理所有组件的初始化流程和顺序
"""
import os
import logging
from typing import Dict, List, Any

logger = logging.getLogger(__name__)

DATABASE_PATH = None


def init_database_path(app_root: str):
    """初始化数据库路径"""
    global DATABASE_PATH
    DATABASE_PATH = os.path.join(app_root, 'app.db')
    logger.info(f"[初始化] 数据库路径: {DATABASE_PATH}")
    return DATABASE_PATH


def _init_core_managers(db_path: str) -> Dict[str, bool]:
    """初始化核心管理器（按依赖顺序）"""
    results = {}
    
    managers = [
        {'name': '权限管理器', 'module': 'app.utils.permission_manager', 'func': 'init_permission_manager', 'args': (db_path,)},
        {'name': '会话管理器', 'module': 'app.utils.session_manager', 'func': 'init_session_manager', 'args': (db_path, 30)},
        {'name': '规则管理器', 'module': 'app.utils.rule_manager', 'func': 'init_rule_manager', 'args': (db_path,)},
        {'name': '统一规则配置中心', 'module': 'app.config.unified_rules', 'func': 'init_unified_rules', 'args': (db_path,)},
        {'name': '配置管理器', 'module': 'app.utils.config_manager', 'func': 'init_config_manager', 'args': (db_path, 30)},
        {'name': '监控管理器', 'module': 'app.utils.monitor_manager', 'func': 'init_monitor_manager', 'args': (db_path, 10)},
        {'name': '备份管理器', 'module': 'app.utils.backup_manager', 'func': 'init_backup_manager', 'args': (db_path, None, 300)}
    ]
    
    for manager in managers:
        try:
            mod = __import__(manager['module'], fromlist=[manager['func']])
            func = getattr(mod, manager['func'])
            func(*manager['args'])
            results[manager['name']] = True
            logger.info(f"[初始化] {manager['name']} 初始化成功")
        except Exception as e:
            results[manager['name']] = False
            logger.warning(f"[初始化] {manager['name']} 初始化失败: {e}")
    
    return results


def _init_middlewares(app) -> Dict[str, bool]:
    """初始化中间件"""
    results = {}
    
    middlewares = [
        {'name': '访问控制中间件', 'module': 'app.middlewares.access_control', 'func': 'access_control_middleware', 'args': (app,)},
        {'name': '认证中间件', 'module': 'app.middlewares.authentication', 'func': 'authentication_middleware', 'args': (app,)},
        {'name': '统一权限控制中间件', 'module': 'app.middlewares.unified_permission', 'func': 'unified_permission_middleware', 'args': (app,)},
        {'name': '系统约束中间件', 'module': 'app.middlewares.system_constraints', 'func': 'system_constraints_middleware', 'args': (app,)}
    ]
    
    for middleware in middlewares:
        try:
            mod = __import__(middleware['module'], fromlist=[middleware['func']])
            func = getattr(mod, middleware['func'])
            result = func(*middleware['args'])
            if result:
                app = result
            results[middleware['name']] = True
            logger.info(f"[中间件] {middleware['name']} 应用成功")
        except Exception as e:
            results[middleware['name']] = False
            logger.warning(f"[中间件] {middleware['name']} 应用失败: {e}")
    
    return results, app


def _register_blueprints(app) -> Dict[str, bool]:
    """注册所有蓝图（按功能模块分类）"""
    results = {}
    
    blueprint_groups = [
        {
            'group': '视图蓝图',
            'blueprints': [
                ('app.views.exam_system', 'exam_system_bp', None),
                ('app.views.test_system', 'test_system_bp', None),
                ('app.views.learning_system', 'learning_system_bp', None),
                ('app.views.user_system', 'user_system_bp', None),
                ('app.views.about', 'about_bp', None),
                ('app.views.k12_education', 'k12_bp', None),
            ]
        },
        {'group': 'API蓝图',
            'blueprints': [
                ('app.api.ai_fixer_api', 'ai_fixer_api', None),
                ('app.api.batch_auto_api', 'batch_auto_api', None),
                ('app.api.exam_api', 'exam_api', '/api/exam'),
                ('app.api.user_info_api', 'user_info_api', None),
                ('app.api.auth_api', 'auth_api', None),
                ('app.api.core_agents_api', 'core_agents_api', None),
                ('app.api.monitoring_api', 'monitoring_api', None),
                ('app.api.release_api', 'release_api', None),
                ('app.api.super_admin_data_api', 'super_admin_data_api', '/api'),
                ('app.api.ai_employee_enhanced_api', 'ai_employee_enhanced_api', '/api'),
                ('app.api.data_integrity_api', 'data_integrity_api', '/api'),
                ('app.api.proactive_ai_api', 'proactive_ai_api', '/api'),
                ('app.api.brain_bank_api', 'brain_bank_api', '/api'),
                ('app.api.admin_monitoring_api', 'admin_monitoring_api', '/api'),
                ('app.api.alert_api', 'alert_api', '/api'),
                ('app.api.auto_dev_api', 'auto_dev_api', None),
                ('app.api.exam_enhancement_api', 'exam_enhancement_api', None),
                ('app.api.exam_expansion_api', 'exam_expansion_api', None),
                ('app.api.version_api', 'version_api', '/api/version'),
                ('app.api.parent_api', 'parent_api', None),
                ('app.api.teacher_k12_api', 'teacher_k12_api', None),
                ('app.api.iteration_api', 'iteration_api', '/api'),
            ]
        }
    ]
    
    for group in blueprint_groups:
        for module_name, bp_name, url_prefix in group['blueprints']:
            try:
                mod = __import__(module_name, fromlist=[bp_name])
                blueprint = getattr(mod, bp_name)
                
                if hasattr(mod, 'init_enhanced_system'):
                    mod.init_enhanced_system()
                    logger.info(f"[蓝图] {bp_name} 增强系统初始化完成")
                
                if url_prefix:
                    app.register_blueprint(blueprint, url_prefix=url_prefix)
                else:
                    app.register_blueprint(blueprint)
                
                results[bp_name] = True
                logger.info(f"[蓝图] {bp_name} 注册成功")
            except ImportError as e:
                results[bp_name] = False
                logger.warning(f"[蓝图] {bp_name} 未找到，跳过注册: {e}")
            except Exception as e:
                results[bp_name] = False
                logger.warning(f"[蓝图] {bp_name} 注册失败: {e}")
    
    return results


def _init_auto_dev_components() -> Dict[str, bool]:
    """初始化自动开发运维组件"""
    results = {}
    
    components = [
        {'name': '人机协同审批系统', 'module': 'app.agents.approval_manager', 'func': 'init_approval_system', 'desc': '操作等级控制、审批流程、日志记录'},
        {'name': '自动化测试框架', 'module': 'app.agents.auto_test_runner', 'func': 'init_test_runner', 'desc': '单元测试、API测试、页面测试、压力测试'},
        {'name': 'Git源码自动操作', 'module': 'app.agents.git_auto_ops', 'func': 'init_git_auto_ops', 'desc': '分支管理、代码修改、安全推送'},
        {'name': '被动升级扫描器', 'module': 'app.agents.dependency_scanner', 'func': 'init_dependency_scanner', 'desc': '漏洞扫描、自动升级、兼容性测试'},
        {'name': '迭代规则引擎', 'module': 'app.agents.iteration_rules', 'func': 'init_iteration_rules', 'desc': '迭代周期、触发条件、AI员工分配、审批规则'},
        {'name': '主动迭代引擎', 'module': 'app.agents.iteration_engine', 'func': 'init_iteration_engine', 'desc': '运行数据分析、需求生成、代码优化'},
        {'name': '运维报告生成器', 'module': 'app.agents.ops_report_generator', 'func': 'init_report_generator', 'desc': '每日报告、智能建议'},
        {'name': '版本自动更新服务', 'module': 'app.services.auto_version_updater', 'func': 'init_auto_version_updater', 'desc': '版本号自动升级、Git提交、GitHub同步'},
        {'name': '问题诊断服务', 'module': 'app.services.problems_and_diagnostics', 'func': 'init_problems_and_diagnostics', 'desc': '系统健康检查、问题检测、诊断报告'},
        {'name': 'AI任务调度器', 'module': 'app.ai.ai_task_scheduler', 'func': 'init_ai_task_scheduler', 'desc': '动态任务调度、AI员工协同、强力修复引擎'},
        {'name': '题库自动维护调度器', 'module': 'ai_engines.question_bank_auto_scheduler', 'func': 'init_question_bank_auto_scheduler', 'desc': '题库自动扩充、整理、质量检查、AI生成题目'}
    ]
    
    for component in components:
        try:
            mod = __import__(component['module'], fromlist=[component['func']])
            func = getattr(mod, component['func'])
            func()
            results[component['name']] = True
            logger.info(f"[自动开发运维] {component['name']} 初始化完成 - {component['desc']}")
        except Exception as e:
            results[component['name']] = False
            logger.warning(f"[自动开发运维] {component['name']} 初始化失败: {e}")
    
    return results


def _init_dynamic_systems(app) -> Dict[str, bool]:
    """初始化动态系统"""
    results = {}
    
    systems = [
        {'name': '动态路由管理器', 'module': 'app.utils.dynamic_route_manager', 'func': 'init_dynamic_routes', 'args': (app,)},
        {'name': '角色路由跳转API', 'module': 'app.utils.role_router', 'func': 'role_router_bp', 'is_blueprint': True}
    ]
    
    for system in systems:
        try:
            mod = __import__(system['module'], fromlist=[system['func']])
            
            if system.get('is_blueprint'):
                blueprint = getattr(mod, system['func'])
                app.register_blueprint(blueprint)
                
                if hasattr(mod, 'create_role_routes'):
                    app = mod.create_role_routes(app)
            else:
                func = getattr(mod, system['func'])
                func(*system.get('args', []))
            
            results[system['name']] = True
            logger.info(f"[动态系统] {system['name']} 初始化成功")
        except Exception as e:
            results[system['name']] = False
            logger.warning(f"[动态系统] {system['name']} 初始化失败: {e}")
    
    return results, app


def _init_auto_routes(app) -> Dict[str, bool]:
    """初始化自动路由发现"""
    results = {}
    
    try:
        from app.routes.auto_discover import init_auto_routes
        route_result = init_auto_routes(app)
        results['自动路由发现'] = True
        logger.info(f"[路由] 自动路由发现完成: 注册 {route_result['registered']} 个蓝图, "
                    f"失败 {route_result['failed']} 个, 总路由数 {route_result['total_routes']}")
    except Exception as e:
        results['自动路由发现'] = False
        logger.error(f"[路由] 自动路由发现失败: {e}")
    
    return results


def _init_services() -> Dict[str, bool]:
    """初始化服务层组件"""
    results = {}
    
    services = [
        {'name': '客户端监控服务', 'module': 'app.services.client_monitor_service', 'func': 'init_monitor_tables'},
        {'name': '代码修复服务', 'module': 'app.services.code_repair_service', 'func': 'init_repair_tables'},
        {'name': '端口监控服务', 'module': 'app.services.port_monitor_service', 'func': 'init_port_monitor'},
        {'name': '用户行为监控', 'module': 'app.services.user_behavior_service', 'func': 'init_behavior_monitor'},
        {'name': '系统优化服务', 'module': 'app.services.system_optimization_service', 'func': 'init_system_optimizer'},
        {'name': '自动规则引擎', 'module': 'app.agents.auto_rule_engine', 'func': 'init_rule_engine'},
    ]
    
    for service in services:
        try:
            mod = __import__(service['module'], fromlist=[service['func']])
            func = getattr(mod, service['func'])
            func()
            results[service['name']] = True
            logger.info(f"[服务层] {service['name']} 初始化成功")
        except Exception as e:
            results[service['name']] = False
            logger.warning(f"[服务层] {service['name']} 初始化失败: {e}")
    
    return results


def _init_employees() -> Dict[str, bool]:
    """初始化AI员工"""
    results = {}
    
    employees = [
        {'name': '监控员工', 'module': 'app.services.client_monitor_service', 'func': 'create_monitor_employee'},
        {'name': '修复员工', 'module': 'app.services.code_repair_service', 'func': 'create_repair_employee'},
        {'name': '批量任务管理器', 'module': 'app.agents.batch_task_manager', 'func': 'get_batch_manager', 'check_none': True},
    ]
    
    for employee in employees:
        try:
            mod = __import__(employee['module'], fromlist=[employee['func']])
            func = getattr(mod, employee['func'])
            result = func()
            if employee.get('check_none'):
                if result:
                    results[employee['name']] = True
                    logger.info(f"[AI员工] {employee['name']} 初始化成功")
                else:
                    results[employee['name']] = False
                    logger.warning(f"[AI员工] {employee['name']} 初始化返回None")
            else:
                results[employee['name']] = True
                logger.info(f"[AI员工] {employee['name']} 初始化成功")
        except Exception as e:
            results[employee['name']] = False
            logger.warning(f"[AI员工] {employee['name']} 初始化失败: {e}")
    
    return results


def _init_middleware_objects(app) -> Dict[str, bool]:
    """初始化中间件对象"""
    results = {}
    
    middleware_objects = [
        {'name': '客户端监控中间件', 'module': 'app.middleware.monitor_middleware', 'class_name': 'ClientMonitorMiddleware', 'args': (app,)},
    ]
    
    for mw in middleware_objects:
        try:
            mod = __import__(mw['module'], fromlist=[mw['class_name']])
            mw_class = getattr(mod, mw['class_name'])
            mw_class(*mw['args'])
            results[mw['name']] = True
            logger.info(f"[中间件对象] {mw['name']} 注册成功")
        except Exception as e:
            results[mw['name']] = False
            logger.warning(f"[中间件对象] {mw['name']} 注册失败: {e}")
    
    return results


def init_database_tables(db_path: str):
    """初始化数据库表结构"""
    import sqlite3
    
    tables = [
        '''CREATE TABLE IF NOT EXISTS approvals (
            approval_id TEXT PRIMARY KEY,
            operation_type TEXT,
            operation_level TEXT,
            status TEXT,
            requester TEXT,
            approver TEXT,
            description TEXT,
            details TEXT,
            created_at TEXT,
            approved_at TEXT,
            rejected_at TEXT,
            expires_at TEXT,
            executed_at TEXT,
            execution_result TEXT,
            audit_log TEXT
        )''',
        '''CREATE TABLE IF NOT EXISTS test_results (
            test_id TEXT PRIMARY KEY,
            test_type TEXT,
            status TEXT,
            total_cases INTEGER,
            passed_cases INTEGER,
            failed_cases INTEGER,
            error_message TEXT,
            executed_at TEXT,
            duration REAL
        )''',
        '''CREATE TABLE IF NOT EXISTS vulnerability_scans (
            scan_id TEXT PRIMARY KEY,
            scan_time TEXT,
            status TEXT,
            total_packages INTEGER,
            vulnerable_packages INTEGER,
            critical_count INTEGER,
            high_count INTEGER,
            medium_count INTEGER,
            low_count INTEGER,
            details TEXT
        )''',
        '''CREATE TABLE IF NOT EXISTS git_operations (
            op_id TEXT PRIMARY KEY,
            operation_type TEXT,
            branch TEXT,
            status TEXT,
            changes TEXT,
            error_message TEXT,
            executed_at TEXT
        )''',
        '''CREATE TABLE IF NOT EXISTS iteration_plans (
            plan_id TEXT PRIMARY KEY,
            status TEXT,
            iteration_type TEXT,
            priority TEXT,
            description TEXT,
            requirements TEXT,
            code_changes TEXT,
            approval_id TEXT,
            test_results TEXT,
            created_at TEXT,
            executed_at TEXT
        )''',
        '''CREATE TABLE IF NOT EXISTS ops_reports (
            report_id TEXT PRIMARY KEY,
            report_date TEXT,
            report_type TEXT,
            status TEXT,
            content TEXT,
            created_at TEXT
        )'''
    ]
    
    try:
        with sqlite3.connect(db_path) as conn:
            cursor = conn.cursor()
            for table_sql in tables:
                cursor.execute(table_sql)
            conn.commit()
        logger.info(f"[数据库] 表结构初始化完成")
        return True
    except Exception as e:
        logger.error(f"[数据库] 表结构初始化失败: {e}")
        return False


def run_full_initialization(app) -> Dict[str, Any]:
    """执行完整的系统初始化流程"""
    logger.info("=" * 60)
    logger.info("[初始化] 开始执行系统完整初始化流程")
    logger.info("=" * 60)
    
    results = {
        'phase_1_database': False,
        'phase_2_core': {},
        'phase_3_middlewares': {},
        'phase_4_blueprints': {},
        'phase_5_dynamic': {},
        'phase_6_auto_routes': {},
        'phase_7_auto_dev': {},
        'phase_8_services': {},
        'phase_9_employees': {},
        'phase_10_middleware_objects': {}
    }
    
    app_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    db_path = init_database_path(app_root)
    
    logger.info("\n--- 阶段1: 数据库表初始化 ---")
    results['phase_1_database'] = init_database_tables(db_path)
    
    logger.info("\n--- 阶段2: 核心管理器初始化 ---")
    results['phase_2_core'] = _init_core_managers(db_path)
    
    logger.info("\n--- 阶段3: 中间件初始化 ---")
    results['phase_3_middlewares'], app = _init_middlewares(app)
    
    logger.info("\n--- 阶段4: 蓝图注册 ---")
    results['phase_4_blueprints'] = _register_blueprints(app)
    
    logger.info("\n--- 阶段5: 动态系统初始化 ---")
    results['phase_5_dynamic'], app = _init_dynamic_systems(app)
    
    logger.info("\n--- 阶段6: 自动路由发现 ---")
    results['phase_6_auto_routes'] = _init_auto_routes(app)
    
    logger.info("\n--- 阶段7: 自动开发运维组件初始化 ---")
    results['phase_7_auto_dev'] = _init_auto_dev_components()
    
    logger.info("\n--- 阶段8: 服务层初始化 ---")
    results['phase_8_services'] = _init_services()
    
    logger.info("\n--- 阶段9: AI员工初始化 ---")
    results['phase_9_employees'] = _init_employees()
    
    logger.info("\n--- 阶段10: 中间件对象注册 ---")
    results['phase_10_middleware_objects'] = _init_middleware_objects(app)
    
    logger.info("\n" + "=" * 60)
    logger.info("[初始化] 系统初始化流程完成")
    logger.info("=" * 60)
    
    success_count = sum(
        sum(v.values()) for v in results.values() if isinstance(v, dict)
    ) + (1 if results['phase_1_database'] else 0)
    
    total_count = sum(
        len(v) for v in results.values() if isinstance(v, dict)
    ) + 1
    
    logger.info(f"[初始化] 初始化结果: {success_count}/{total_count} 组件成功")
    
    return results, app