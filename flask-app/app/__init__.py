# -*- coding: utf-8 -*-
"""
系统初始化模块 - 统一管理所有组件的初始化流程和顺序
"""
import os
import sys
import time
import logging
from typing import Dict, List, Any, Optional

logger = logging.getLogger(__name__)

DATABASE_PATH = None


class Color:
    RESET = '\033[0m'
    RED = '\033[31m'
    GREEN = '\033[32m'
    YELLOW = '\033[33m'
    BLUE = '\033[34m'
    MAGENTA = '\033[35m'
    CYAN = '\033[36m'
    WHITE = '\033[37m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'


def print_color(text: str, color: str = Color.WHITE, bold: bool = False):
    prefix = Color.BOLD if bold else ''
    print(f"{prefix}{color}{text}{Color.RESET}")


def print_progress(current: int, total: int, label: str = ""):
    bar_length = 40
    percent = current / total
    filled_length = int(bar_length * percent)
    bar = '█' * filled_length + '░' * (bar_length - filled_length)
    sys.stdout.write(f"\r{Color.CYAN}[{bar}] {Color.GREEN}{current}/{total} {Color.RESET}{label}")
    sys.stdout.flush()


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
    
    print(f"\n{Color.BOLD}{Color.BLUE}┌─────────────────────────────────────────────────────────────┐")
    print(f"│  阶段2: 核心管理器初始化 ({len(managers)}个组件)                │")
    print(f"└─────────────────────────────────────────────────────────────┘{Color.RESET}")
    
    for i, manager in enumerate(managers, 1):
        try:
            mod = __import__(manager['module'], fromlist=[manager['func']])
            func = getattr(mod, manager['func'])
            func(*manager['args'])
            results[manager['name']] = True
            print_progress(i, len(managers), f"{Color.GREEN}✓ {manager['name']}{Color.RESET}")
            logger.info(f"[初始化] {manager['name']} 初始化成功")
        except Exception as e:
            results[manager['name']] = False
            print_progress(i, len(managers), f"{Color.RED}✗ {manager['name']}: {e}{Color.RESET}")
            logger.warning(f"[初始化] {manager['name']} 初始化失败: {e}")
    
    print()
    return results


def _init_middlewares(app) -> Dict[str, bool]:
    """初始化所有中间件"""
    results = {}
    
    middleware_modules = [
        {'name': '安全头中间件', 'module': 'app.middlewares.security_headers'},
        {'name': 'SQL注入防护中间件', 'module': 'app.middlewares.sql_injection_protection'},
        {'name': '安全中间件', 'module': 'app.middlewares.security_middleware'},
        {'name': 'IP白名单中间件', 'module': 'app.middlewares.ip_whitelist'},
        {'name': '认证中间件', 'module': 'app.middlewares.authentication'},
        {'name': '登录验证中间件', 'module': 'app.middlewares.login_required'},
        {'name': '访问控制中间件', 'module': 'app.middlewares.access_control'},
        {'name': '统一权限控制中间件', 'module': 'app.middlewares.unified_permission'},
        {'name': '访客权限中间件', 'module': 'app.middlewares.guest_permission'},
        {'name': '系统约束中间件', 'module': 'app.middlewares.system_constraints'},
        {'name': '路由约束引擎', 'module': 'app.middlewares.route_constraint_engine'},
        {'name': '防火墙中间件', 'module': 'app.middlewares.firewall_middleware'},
        {'name': '监控中间件', 'module': 'app.middlewares.monitoring'},
        {'name': 'AI智能缓存中间件', 'module': 'app.middlewares.ai_smart_cache'},
        {'name': 'AI智能路由中间件', 'module': 'app.middlewares.ai_smart_routing'},
        {'name': 'AI请求分类器', 'module': 'app.middlewares.ai_request_classifier'},
        {'name': 'AI大脑中间件', 'module': 'app.middlewares.ai_brain_middleware'},
        {'name': 'AI学习中间件', 'module': 'app.middlewares.ai_middleware_learning'},
        {'name': 'AI自学习中间件', 'module': 'app.middlewares.ai_self_learning_middleware'},
        {'name': 'AI优化器中间件', 'module': 'app.middlewares.ai_middleware_optimizer'},
        {'name': '权限装饰器', 'module': 'app.middlewares.permission_decorators'}
    ]
    
    init_func_patterns = ['init_', 'middleware', 'register', 'setup']
    
    print(f"\n{Color.BOLD}{Color.CYAN}┌─────────────────────────────────────────────────────────────┐")
    print(f"│  阶段3: 中间件初始化 ({len(middleware_modules)}个组件)              │")
    print(f"└─────────────────────────────────────────────────────────────┘{Color.RESET}")
    
    for i, mw in enumerate(middleware_modules, 1):
        try:
            mod = __import__(mw['module'], fromlist=[''])
            
            init_func = None
            for name in dir(mod):
                if callable(getattr(mod, name)):
                    if any(name.startswith(p) for p in init_func_patterns) or name.endswith('_middleware'):
                        init_func = getattr(mod, name)
                        break
            
            if init_func:
                result = init_func(app) if callable(init_func) and init_func.__code__.co_argcount > 0 else init_func()
                if result and isinstance(result, type(app)):
                    app = result
                results[mw['name']] = True
                print_progress(i, len(middleware_modules), f"{Color.GREEN}✓ {mw['name']}{Color.RESET}")
                logger.info(f"[中间件] {mw['name']} 应用成功")
            else:
                for name in dir(mod):
                    obj = getattr(mod, name)
                    if isinstance(obj, type) and hasattr(obj, '__call__'):
                        try:
                            middleware_instance = obj(app)
                            if hasattr(middleware_instance, 'before_request') or hasattr(middleware_instance, '__call__'):
                                app.before_request(middleware_instance.before_request)
                                results[mw['name']] = True
                                print_progress(i, len(middleware_modules), f"{Color.GREEN}✓ {mw['name']}{Color.RESET}")
                                logger.info(f"[中间件] {mw['name']} 作为类实例应用成功")
                                break
                        except:
                            pass
                if mw['name'] not in results:
                    results[mw['name']] = False
                    print_progress(i, len(middleware_modules), f"{Color.YELLOW}~ {mw['name']} 无可用中间件函数{Color.RESET}")
                    logger.warning(f"[中间件] {mw['name']} 无可用中间件函数")
        except ImportError:
            results[mw['name']] = False
            print_progress(i, len(middleware_modules), f"{Color.YELLOW}~ {mw['name']} 模块未找到{Color.RESET}")
            logger.warning(f"[中间件] {mw['name']} 模块未找到")
        except Exception as e:
            results[mw['name']] = False
            print_progress(i, len(middleware_modules), f"{Color.YELLOW}~ {mw['name']}: {str(e)[:20]}...{Color.RESET}")
            logger.warning(f"[中间件] {mw['name']} 应用失败: {e}")
    
    print()
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
                ('app.api.ai_distributed_db_api', 'ai_distributed_db_api', '/api'),
            ]
        }
    ]
    
    total_blueprints = sum(len(g['blueprints']) for g in blueprint_groups)
    current = 0
    
    print(f"\n{Color.BOLD}{Color.MAGENTA}┌─────────────────────────────────────────────────────────────┐")
    print(f"│  阶段4: 蓝图注册 ({total_blueprints}个蓝图)                     │")
    print(f"└─────────────────────────────────────────────────────────────┘{Color.RESET}")
    
    for group in blueprint_groups:
        print(f"\n  {Color.BOLD}{group['group']}:{Color.RESET}")
        for module_name, bp_name, url_prefix in group['blueprints']:
            current += 1
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
                print_progress(current, total_blueprints, f"{Color.GREEN}✓ {bp_name}{Color.RESET}")
                logger.info(f"[蓝图] {bp_name} 注册成功")
            except ImportError as e:
                results[bp_name] = False
                print_progress(current, total_blueprints, f"{Color.YELLOW}~ {bp_name} 未找到{Color.RESET}")
                logger.warning(f"[蓝图] {bp_name} 未找到，跳过注册: {e}")
            except Exception as e:
                results[bp_name] = False
                print_progress(current, total_blueprints, f"{Color.RED}✗ {bp_name}: {str(e)[:30]}...{Color.RESET}")
                logger.warning(f"[蓝图] {bp_name} 注册失败: {e}")
    
    print()
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
    
    print(f"\n{Color.BOLD}{Color.YELLOW}┌─────────────────────────────────────────────────────────────┐")
    print(f"│  阶段7: 自动开发运维组件 ({len(components)}个组件)               │")
    print(f"└─────────────────────────────────────────────────────────────┘{Color.RESET}")
    
    for i, component in enumerate(components, 1):
        try:
            mod = __import__(component['module'], fromlist=[component['func']])
            func = getattr(mod, component['func'])
            func()
            results[component['name']] = True
            print_progress(i, len(components), f"{Color.GREEN}✓ {component['name']}{Color.RESET}")
            logger.info(f"[自动开发运维] {component['name']} 初始化完成 - {component['desc']}")
        except Exception as e:
            results[component['name']] = False
            print_progress(i, len(components), f"{Color.YELLOW}~ {component['name']}: {str(e)[:30]}...{Color.RESET}")
            logger.warning(f"[自动开发运维] {component['name']} 初始化失败: {e}")
    
    print()
    return results


def _init_dynamic_systems(app) -> Dict[str, bool]:
    """初始化动态系统"""
    results = {}
    
    systems = [
        {'name': '动态路由管理器', 'module': 'app.utils.dynamic_route_manager', 'func': 'init_dynamic_routes', 'args': (app,)},
        {'name': '角色路由跳转API', 'module': 'app.utils.role_router', 'func': 'role_router_bp', 'is_blueprint': True}
    ]
    
    print(f"\n{Color.BOLD}{Color.CYAN}┌─────────────────────────────────────────────────────────────┐")
    print(f"│  阶段5: 动态系统初始化 ({len(systems)}个组件)                   │")
    print(f"└─────────────────────────────────────────────────────────────┘{Color.RESET}")
    
    for i, system in enumerate(systems, 1):
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
            print_progress(i, len(systems), f"{Color.GREEN}✓ {system['name']}{Color.RESET}")
            logger.info(f"[动态系统] {system['name']} 初始化成功")
        except Exception as e:
            results[system['name']] = False
            print_progress(i, len(systems), f"{Color.RED}✗ {system['name']}: {e}{Color.RESET}")
            logger.warning(f"[动态系统] {system['name']} 初始化失败: {e}")
    
    print()
    return results, app


def _init_auto_routes(app) -> Dict[str, bool]:
    """初始化自动路由发现"""
    results = {}
    
    print(f"\n{Color.BOLD}{Color.MAGENTA}┌─────────────────────────────────────────────────────────────┐")
    print(f"│  阶段6: 自动路由发现                                         │")
    print(f"└─────────────────────────────────────────────────────────────┘{Color.RESET}")
    
    try:
        from app.routes.auto_discover import init_auto_routes
        route_result = init_auto_routes(app)
        results['自动路由发现'] = True
        print(f"  {Color.GREEN}✓ 自动路由发现完成: 注册 {route_result['registered']} 个蓝图, 失败 {route_result['failed']} 个, 总路由数 {route_result['total_routes']}{Color.RESET}")
        logger.info(f"[路由] 自动路由发现完成: 注册 {route_result['registered']} 个蓝图, "
                    f"失败 {route_result['failed']} 个, 总路由数 {route_result['total_routes']}")
    except Exception as e:
        results['自动路由发现'] = False
        print(f"  {Color.RED}✗ 自动路由发现失败: {e}{Color.RESET}")
        logger.error(f"[路由] 自动路由发现失败: {e}")
    
    return results


def _init_services() -> Dict[str, bool]:
    """初始化服务层组件"""
    results = {}
    
    services = [
        {'name': '客户端监控服务', 'module': 'app.services.client_monitor_service'},
        {'name': '代码修复服务', 'module': 'app.services.code_repair_service'},
        {'name': '端口监控服务', 'module': 'app.services.port_monitor_service'},
        {'name': '用户行为监控', 'module': 'app.services.user_behavior_service'},
        {'name': '系统优化服务', 'module': 'app.services.system_optimization_service'},
        {'name': '自动规则引擎', 'module': 'app.agents.auto_rule_engine'},
        {'name': '智能决策引擎', 'module': 'app.services.intelligent_decision_engine'},
        {'name': '增强知识库服务', 'module': 'app.services.enhanced_knowledge_graph'},
        {'name': '智能题目生成器', 'module': 'app.services.intelligent_paper_generator'},
        {'name': '试卷分析服务', 'module': 'app.services.exam_data_analysis_service'},
        {'name': '问题解决服务', 'module': 'app.services.problem_solving_service'},
        {'name': '搜索引擎服务', 'module': 'app.services.search_engine_service'},
        {'name': '缓存服务', 'module': 'app.services.cache_service'},
        {'name': '通知服务', 'module': 'app.services.notification_service'},
        {'name': '系统设置服务', 'module': 'app.services.system_settings_service'},
        {'name': '版本管理服务', 'module': 'app.services.version_manager'},
        {'name': '数据层服务', 'module': 'app.services.data_layer_service'},
        {'name': '数据库存储服务', 'module': 'app.services.db_storage_service'},
        {'name': 'AI错误修复服务', 'module': 'app.services.ai_error_fixer'},
        {'name': 'AI编排服务', 'module': 'app.services.ai_orchestrator'},
        {'name': '防火墙系统', 'module': 'app.services.firewall_system'},
        {'name': '安全防护服务', 'module': 'app.services.security_defense'},
        {'name': '深度保护服务', 'module': 'app.services.deep_protection'},
        {'name': '反作弊服务', 'module': 'app.services.anti_cheating_service'},
        {'name': '监考服务', 'module': 'app.services.exam_proctor_service'},
        {'name': '题库服务', 'module': 'app.services.question_bank_service'},
        {'name': '增强题库服务', 'module': 'app.services.enhanced_question_bank_service'},
        {'name': '题目质量服务', 'module': 'app.services.question_quality_service'},
        {'name': '智能题目标签服务', 'module': 'app.services.smart_question_tagger'},
        {'name': '用户答案分析服务', 'module': 'app.services.user_answer_analysis_service'},
        {'name': '系统增强服务', 'module': 'app.services.system_enhancement_service'},
        {'name': '自适应升级服务', 'module': 'app.services.adaptive_upgrade_service'},
        {'name': 'OTA升级服务', 'module': 'app.services.ota_upgrade_service'},
        {'name': '升级管理服务', 'module': 'app.services.upgrade_management'},
        {'name': '自动版本更新器', 'module': 'app.services.auto_version_updater'},
        {'name': '备份管理服务', 'module': 'app.services.backup_management_service'},
        {'name': '版本备份管理器', 'module': 'app.services.version_backup_manager'},
        {'name': '配置服务', 'module': 'app.services.config_service'},
        {'name': '日志管理器', 'module': 'app.services.log_manager'},
        {'name': '服务管理器', 'module': 'app.services.service_manager'},
        {'name': '服务引导器', 'module': 'app.services.service_bootstrapper'},
        {'name': '教师系统', 'module': 'app.services.teacher_system'},
        {'name': '学生流式系统', 'module': 'app.services.student_stream_system'},
        {'name': '家长监控服务', 'module': 'app.services.parent_monitor_service'},
        {'name': '用户组管理', 'module': 'app.services.user_group_manager'},
        {'name': '用户资料服务', 'module': 'app.services.user_profile_service'},
        {'name': '用户管理客户端', 'module': 'app.services.user_management_client'},
        {'name': '用户管理器服务', 'module': 'app.services.user_manager_service'},
        {'name': '访客用户管理', 'module': 'app.services.guest_user_manager'},
        {'name': '班级管理', 'module': 'app.services.class_manager'},
        {'name': '学习小组服务', 'module': 'app.services.learning_group_service'},
        {'name': '等级题库服务', 'module': 'app.services.grade_bank_service'},
        {'name': '等级管理', 'module': 'app.services.grade_manager'},
        {'name': '考试AI助手', 'module': 'app.services.exam_ai_assistant'},
        {'name': '考试增强服务', 'module': 'app.services.exam_enhancement_service'},
        {'name': '考试扩展服务', 'module': 'app.services.exam_expansion_service'},
        {'name': '考试生成服务', 'module': 'app.services.exam_generation_service'},
        {'name': '考试管理器', 'module': 'app.services.exam_manager'},
        {'name': '考试服务', 'module': 'app.services.exam_service'},
        {'name': '升学考试服务', 'module': 'app.services.promotion_exam_service'},
        {'name': '分班测试服务', 'module': 'app.services.placement_test_service'},
        {'name': '成人考试题目生成器', 'module': 'app.services.adult_exam_question_generator'},
        {'name': '基于等级的题目生成器', 'module': 'app.services.level_based_question_generator'},
        {'name': '海量题目生成器', 'module': 'app.services.massive_question_generator'},
        {'name': '题目生成服务', 'module': 'app.services.question_generator_service'},
        {'name': '题目分析服务', 'module': 'app.services.question_analysis_service'},
        {'name': '题目爬虫服务', 'module': 'app.services.question_crawler_service'},
        {'name': '矩阵题库管理器', 'module': 'app.services.matrix_question_bank_manager'},
        {'name': '数据分析服务', 'module': 'app.services.exam_data_analysis_service'},
        {'name': '数据上传服务', 'module': 'app.services.data_upload_service'},
        {'name': 'JSON数据上传服务', 'module': 'app.services.json_data_upload_service'},
        {'name': 'JSON导入代理服务', 'module': 'app.services.json_import_agent_service'},
        {'name': 'JSON同步管理器', 'module': 'app.services.json_sync_manager'},
        {'name': '数据库配置管理器', 'module': 'app.services.db_config_manager'},
        {'name': '数据库加密管理器', 'module': 'app.services.db_encryption_manager'},
        {'name': 'SSL数据库管理器', 'module': 'app.services.ssl_db_manager'},
        {'name': 'SSL管理器', 'module': 'app.services.ssl_manager'},
        {'name': '双加密管理器', 'module': 'app.services.dual_encryption_manager'},
        {'name': '分布式数据库服务', 'module': 'app.services.distributed_db_service'},
        {'name': '分布式服务器', 'module': 'app.services.distributed_server'},
        {'name': '集群服务', 'module': 'app.services.cluster_service'},
        {'name': 'CDN服务', 'module': 'app.services.cdn_service'},
        {'name': '渲染引擎服务', 'module': 'app.services.render_engine_service'},
        {'name': '数学公式服务', 'module': 'app.services.math_formula_service'},
        {'name': '物理引擎服务', 'module': 'app.services.physics_engine_service'},
        {'name': '粒子引擎服务', 'module': 'app.services.particle_engine_service'},
        {'name': 'Arduino服务', 'module': 'app.services.arduino_service'},
        {'name': 'Arduino高级服务', 'module': 'app.services.arduino_advanced_service'},
        {'name': 'Arduino API适配器', 'module': 'app.services.arduino_api_adapter'},
        {'name': '本地AI聊天服务', 'module': 'app.services.local_ai_chat_service'},
        {'name': '音频管理器', 'module': 'app.services.audio_manager'},
        {'name': '序列化监控', 'module': 'app.services.serial_monitor'},
        {'name': '服务器系统', 'module': 'app.services.server_system'},
        {'name': '项目管家', 'module': 'app.services.project_butler'},
        {'name': '管家系统', 'module': 'app.services.butler_system'},
        {'name': '教授系统', 'module': 'app.services.professor_system'},
        {'name': '规则管理服务', 'module': 'app.services.rule_management'},
        {'name': '规则权限服务', 'module': 'app.services.rules_permissions'},
        {'name': '智能预测器', 'module': 'app.services.intelligent_predictor'},
        {'name': '错误报告服务', 'module': 'app.services.error_report_service'},
        {'name': '系统逻辑管理器', 'module': 'app.services.system_logic_manager'},
        {'name': '系统映射服务', 'module': 'app.services.system_mapping_service'},
        {'name': '系统版本服务', 'module': 'app.services.system_version_service'},
        {'name': '用户行为服务器', 'module': 'app.services.user_behavior_server'},
        {'name': '用户证书管理器', 'module': 'app.services.user_certificate_manager'},
        {'name': 'Redis集成', 'module': 'app.services.redis_integration'},
        {'name': 'NoSQL服务', 'module': 'app.services.nosql_service'},
        {'name': 'JavaScript优化服务', 'module': 'app.services.javascript_optimization_service'},
        {'name': '深度优化服务', 'module': 'app.services.deep_optimization_service'},
        {'name': '告警机器人', 'module': 'app.services.alarm_bot'},
        {'name': '审批服务', 'module': 'app.services.approval_service'},
        {'name': 'API服务', 'module': 'app.services.api_service'},
        {'name': '登录路由服务', 'module': 'app.services.login_route_service'},
        {'name': '主题管理器', 'module': 'app.services.theme_manager'},
        {'name': 'Git管理器', 'module': 'app.services.git_manager'},
        {'name': '数据库读写服务', 'module': 'app.services.database_rw_service'},
        {'name': 'AI题目过滤服务', 'module': 'app.services.ai_question_filter_service'}
    ]
    
    print(f"\n{Color.BOLD}{Color.GREEN}┌─────────────────────────────────────────────────────────────┐")
    print(f"│  阶段8: 服务层初始化 ({len(services)}个服务)                     │")
    print(f"└─────────────────────────────────────────────────────────────┘{Color.RESET}")
    
    for i, service in enumerate(services, 1):
        try:
            mod = __import__(service['module'], fromlist=[''])
            init_func = None
            service_class = None
            service_instance = None
            
            for name in dir(mod):
                obj = getattr(mod, name)
                if callable(obj):
                    try:
                        if name.startswith('init_'):
                            init_func = obj
                            break
                        elif name.startswith('create_'):
                            init_func = obj
                            break
                        elif name.startswith('start_'):
                            init_func = obj
                            break
                        elif name.startswith('setup_'):
                            init_func = obj
                            break
                        elif isinstance(obj, type) and name.endswith('Service'):
                            service_class = obj
                            break
                    except:
                        pass
            
            for name in dir(mod):
                obj = getattr(mod, name)
                if not callable(obj) and isinstance(obj, object) and not isinstance(obj, type):
                    if name.endswith('_service') or name.endswith('_system') or name.endswith('_manager'):
                        service_instance = obj
                        break
            
            if init_func:
                try:
                    arg_count = init_func.__code__.co_argcount if hasattr(init_func, '__code__') else 0
                    if arg_count == 0:
                        init_func()
                    elif arg_count == 1:
                        try:
                            init_func(DATABASE_PATH)
                        except:
                            init_func()
                    else:
                        try:
                            init_func(DATABASE_PATH, 30)
                        except:
                            init_func()
                    results[service['name']] = True
                    print_progress(i, len(services), f"{Color.GREEN}✓ {service['name']}{Color.RESET}")
                    logger.info(f"[服务层] {service['name']} 初始化成功")
                except TypeError:
                    try:
                        init_func()
                        results[service['name']] = True
                        print_progress(i, len(services), f"{Color.GREEN}✓ {service['name']}{Color.RESET}")
                        logger.info(f"[服务层] {service['name']} 初始化成功")
                    except:
                        results[service['name']] = False
                        print_progress(i, len(services), f"{Color.YELLOW}~ {service['name']} 参数不匹配{Color.RESET}")
                        logger.warning(f"[服务层] {service['name']} 参数不匹配")
            elif service_class:
                try:
                    if service_class.__init__.__code__.co_argcount <= 1:
                        service_class()
                    else:
                        try:
                            service_class(DATABASE_PATH)
                        except:
                            service_class()
                    results[service['name']] = True
                    print_progress(i, len(services), f"{Color.GREEN}✓ {service['name']}{Color.RESET}")
                    logger.info(f"[服务层] {service['name']} 类实例化成功")
                except:
                    results[service['name']] = False
                    print_progress(i, len(services), f"{Color.YELLOW}~ {service['name']} 类实例化失败{Color.RESET}")
                    logger.warning(f"[服务层] {service['name']} 类实例化失败")
            elif service_instance:
                results[service['name']] = True
                print_progress(i, len(services), f"{Color.GREEN}✓ {service['name']}{Color.RESET}")
                logger.info(f"[服务层] {service['name']} 已存在实例")
            else:
                results[service['name']] = False
                print_progress(i, len(services), f"{Color.YELLOW}~ {service['name']} 无可用初始化方式{Color.RESET}")
                logger.warning(f"[服务层] {service['name']} 无可用初始化方式")
        except ImportError:
            results[service['name']] = False
            print_progress(i, len(services), f"{Color.YELLOW}~ {service['name']} 模块未找到{Color.RESET}")
            logger.warning(f"[服务层] {service['name']} 模块未找到")
        except Exception as e:
            results[service['name']] = False
            print_progress(i, len(services), f"{Color.YELLOW}~ {service['name']}: {str(e)[:20]}...{Color.RESET}")
            logger.warning(f"[服务层] {service['name']} 初始化失败: {e}")
    
    print()
    return results


def _init_employees() -> Dict[str, bool]:
    """初始化所有AI员工"""
    results = {}
    
    init_func_patterns = ['init_', 'create_', 'get_', 'start_', 'build_', 'setup_']
    
    employees = [
        {'name': '监控员工', 'module': 'app.services.client_monitor_service'},
        {'name': '修复员工', 'module': 'app.services.code_repair_service'},
        {'name': '批量任务管理器', 'module': 'app.agents.batch_task_manager', 'check_none': True},
        {'name': 'AI执行器', 'module': 'app.agents.agent_executor'},
        {'name': 'Agent管理器', 'module': 'app.agents.agent_manager'},
        {'name': 'Agent编排器', 'module': 'app.agents.agent_orchestrator'},
        {'name': 'Agent运行时', 'module': 'app.agents.agent_runtime'},
        {'name': 'AI员工集成', 'module': 'app.agents.agent_ai_employee_integration'},
        {'name': '基础核心Agent', 'module': 'app.agents.base_core_agent'},
        {'name': '自动修复Agent', 'module': 'app.agents.auto_fix_agent'},
        {'name': '代码调试Agent', 'module': 'app.agents.code_debug_agent'},
        {'name': '协同任务调度器', 'module': 'app.agents.collaborative_task_scheduler'},
        {'name': '部署架构Agent', 'module': 'app.agents.deployment_architecture_agent'},
        {'name': '异常捕获Agent', 'module': 'app.agents.exception_capture_agent'},
        {'name': 'GitHub集成', 'module': 'app.agents.github_integration'},
        {'name': '灰度发布管理器', 'module': 'app.agents.gray_release_manager'},
        {'name': '本地Agent运行器', 'module': 'app.agents.local_agent_runner'},
        {'name': '监控收集器', 'module': 'app.agents.monitoring_collector'},
        {'name': '运维检查Agent', 'module': 'app.agents.ops_inspection_agent'},
        {'name': '规则自动生成器', 'module': 'app.agents.rule_auto_generator'},
        {'name': '版本升级Agent', 'module': 'app.agents.version_upgrade_agent'},
        {'name': '考试规则模板', 'module': 'app.agents.exam_rule_templates'},
        {'name': '前端增强规则模板', 'module': 'app.agents.frontend_enhancement_rule_templates'},
        {'name': '网络安全规则模板', 'module': 'app.agents.network_security_rule_templates'},
        {'name': '题目库规则模板', 'module': 'app.agents.question_bank_rule_templates'},
        {'name': '安全规则模板', 'module': 'app.agents.security_rule_templates'},
        {'name': '听力题库AI', 'module': 'ai_engines.listening_question_employee'},
        {'name': '日语听力音频AI', 'module': 'ai_engines.japanese_listening_audio_ai'}
    ]
    
    print(f"\n{Color.BOLD}{Color.MAGENTA}┌─────────────────────────────────────────────────────────────┐")
    print(f"│  阶段9: AI员工与Agent初始化 ({len(employees)}个组件)            │")
    print(f"└─────────────────────────────────────────────────────────────┘{Color.RESET}")
    
    for i, employee in enumerate(employees, 1):
        try:
            mod = __import__(employee['module'], fromlist=[''])
            init_func = None
            employee_class = None
            employee_instance = None
            
            for name in dir(mod):
                obj = getattr(mod, name)
                if callable(obj):
                    try:
                        for pattern in init_func_patterns:
                            if name.startswith(pattern):
                                init_func = obj
                                break
                        if init_func:
                            break
                        elif isinstance(obj, type) and (name.endswith('Agent') or name.endswith('Manager') or name.endswith('Executor') or name.endswith('Runner') or name.endswith('Collector') or name.endswith('Scheduler')):
                            employee_class = obj
                            break
                    except:
                        pass
            
            for name in dir(mod):
                obj = getattr(mod, name)
                if not callable(obj) and isinstance(obj, object) and not isinstance(obj, type):
                    if name.endswith('_agent') or name.endswith('_manager') or name.endswith('_executor') or name.endswith('_runner'):
                        employee_instance = obj
                        break
            
            if init_func:
                try:
                    arg_count = init_func.__code__.co_argcount if hasattr(init_func, '__code__') else 0
                    if arg_count == 0:
                        result = init_func()
                    else:
                        try:
                            result = init_func(DATABASE_PATH)
                        except:
                            result = init_func()
                    
                    if employee.get('check_none'):
                        if result:
                            results[employee['name']] = True
                            print_progress(i, len(employees), f"{Color.GREEN}✓ {employee['name']}{Color.RESET}")
                            logger.info(f"[AI员工] {employee['name']} 初始化成功")
                        else:
                            results[employee['name']] = False
                            print_progress(i, len(employees), f"{Color.YELLOW}~ {employee['name']} 返回None{Color.RESET}")
                            logger.warning(f"[AI员工] {employee['name']} 初始化返回None")
                    else:
                        results[employee['name']] = True
                        print_progress(i, len(employees), f"{Color.GREEN}✓ {employee['name']}{Color.RESET}")
                        logger.info(f"[AI员工] {employee['name']} 初始化成功")
                except TypeError:
                    try:
                        result = init_func()
                        if employee.get('check_none') and not result:
                            results[employee['name']] = False
                            print_progress(i, len(employees), f"{Color.YELLOW}~ {employee['name']} 返回None{Color.RESET}")
                            logger.warning(f"[AI员工] {employee['name']} 初始化返回None")
                        else:
                            results[employee['name']] = True
                            print_progress(i, len(employees), f"{Color.GREEN}✓ {employee['name']}{Color.RESET}")
                            logger.info(f"[AI员工] {employee['name']} 初始化成功")
                    except:
                        results[employee['name']] = False
                        print_progress(i, len(employees), f"{Color.YELLOW}~ {employee['name']} 参数不匹配{Color.RESET}")
                        logger.warning(f"[AI员工] {employee['name']} 参数不匹配")
            elif employee_class:
                try:
                    if employee_class.__init__.__code__.co_argcount <= 1:
                        employee_class()
                    else:
                        try:
                            employee_class(DATABASE_PATH)
                        except:
                            employee_class()
                    results[employee['name']] = True
                    print_progress(i, len(employees), f"{Color.GREEN}✓ {employee['name']}{Color.RESET}")
                    logger.info(f"[AI员工] {employee['name']} 类实例化成功")
                except:
                    results[employee['name']] = False
                    print_progress(i, len(employees), f"{Color.YELLOW}~ {employee['name']} 类实例化失败{Color.RESET}")
                    logger.warning(f"[AI员工] {employee['name']} 类实例化失败")
            elif employee_instance:
                results[employee['name']] = True
                print_progress(i, len(employees), f"{Color.GREEN}✓ {employee['name']}{Color.RESET}")
                logger.info(f"[AI员工] {employee['name']} 已存在实例")
            else:
                results[employee['name']] = False
                print_progress(i, len(employees), f"{Color.YELLOW}~ {employee['name']} 无可用初始化方式{Color.RESET}")
                logger.warning(f"[AI员工] {employee['name']} 无可用初始化方式")
        except Exception as e:
            results[employee['name']] = False
            print_progress(i, len(employees), f"{Color.YELLOW}~ {employee['name']}: {str(e)[:20]}...{Color.RESET}")
            logger.warning(f"[AI员工] {employee['name']} 初始化失败: {e}")
    
    print()
    return results


def _init_middleware_objects(app) -> Dict[str, bool]:
    """初始化中间件对象"""
    results = {}
    
    middleware_objects = [
        {'name': '客户端监控中间件', 'module': 'app.middleware.monitor_middleware', 'class_name': 'ClientMonitorMiddleware', 'args': (app,)},
    ]
    
    print(f"\n{Color.BOLD}{Color.CYAN}┌─────────────────────────────────────────────────────────────┐")
    print(f"│  阶段10: 中间件对象注册 ({len(middleware_objects)}个)            │")
    print(f"└─────────────────────────────────────────────────────────────┘{Color.RESET}")
    
    for i, mw in enumerate(middleware_objects, 1):
        try:
            mod = __import__(mw['module'], fromlist=[mw['class_name']])
            mw_class = getattr(mod, mw['class_name'])
            mw_class(*mw['args'])
            results[mw['name']] = True
            print_progress(i, len(middleware_objects), f"{Color.GREEN}✓ {mw['name']}{Color.RESET}")
            logger.info(f"[中间件对象] {mw['name']} 注册成功")
        except Exception as e:
            results[mw['name']] = False
            print_progress(i, len(middleware_objects), f"{Color.YELLOW}~ {mw['name']}: {e}{Color.RESET}")
            logger.warning(f"[中间件对象] {mw['name']} 注册失败: {e}")
    
    print()
    return results


def _init_rules_permissions_auto_complete(db_path: str) -> Dict[str, bool]:
    """自动补全规则和权限"""
    results = {}
    
    print(f"\n{Color.BOLD}{Color.BLUE}┌─────────────────────────────────────────────────────────────┐")
    print(f"│  阶段11: 规则和权限自动补全                                   │")
    print(f"└─────────────────────────────────────────────────────────────┘{Color.RESET}")
    
    try:
        from app.services.rules_permissions import init_rules_and_permissions
        init_rules_and_permissions()
        results['规则权限初始化'] = True
        print(f"  {Color.GREEN}✓ 规则权限初始化完成{Color.RESET}")
        logger.info("[规则权限] 规则权限初始化完成")
    except Exception as e:
        results['规则权限初始化'] = False
        print(f"  {Color.YELLOW}~ 规则权限初始化失败: {e}{Color.RESET}")
        logger.warning(f"[规则权限] 规则权限初始化失败: {e}")
    
    try:
        from app.services.rule_management import rule_management_service, RuleManagementService
        if rule_management_service:
            rule_management_service.init_rule_manager_ai()
            results['规则管理器AI'] = True
            print(f"  {Color.GREEN}✓ 规则管理器AI初始化完成{Color.RESET}")
            logger.info("[规则权限] 规则管理器AI初始化完成")
        else:
            rule_manager = RuleManagementService()
            results['规则管理器AI'] = True
            print(f"  {Color.GREEN}✓ 规则管理器AI初始化完成{Color.RESET}")
            logger.info("[规则权限] 规则管理器AI初始化完成")
    except Exception as e:
        results['规则管理器AI'] = False
        print(f"  {Color.YELLOW}~ 规则管理器AI初始化失败: {e}{Color.RESET}")
        logger.warning(f"[规则权限] 规则管理器AI初始化失败: {e}")
    
    try:
        from app.utils.permission_manager import init_permission_manager
        init_permission_manager(db_path)
        results['权限管理器'] = True
        print(f"  {Color.GREEN}✓ 权限管理器初始化完成{Color.RESET}")
        logger.info("[规则权限] 权限管理器初始化完成")
    except Exception as e:
        results['权限管理器'] = False
        print(f"  {Color.YELLOW}~ 权限管理器初始化失败: {e}{Color.RESET}")
        logger.warning(f"[规则权限] 权限管理器初始化失败: {e}")
    
    try:
        from app.config.unified_rules import init_unified_rules
        init_unified_rules(db_path)
        results['统一规则配置'] = True
        print(f"  {Color.GREEN}✓ 统一规则配置中心初始化完成{Color.RESET}")
        logger.info("[规则权限] 统一规则配置中心初始化完成")
    except Exception as e:
        results['统一规则配置'] = False
        print(f"  {Color.YELLOW}~ 统一规则配置初始化失败: {e}{Color.RESET}")
        logger.warning(f"[规则权限] 统一规则配置初始化失败: {e}")
    
    return results


def init_database_tables(db_path: str):
    """初始化数据库表结构"""
    import sqlite3
    
    try:
        from app.models.local_agent import init_local_agent_tables
        from app.utils.db import DatabaseManager
        
        db_manager = DatabaseManager()
        init_local_agent_tables(db_manager)
        logger.info("[数据库] 本地Agent表初始化完成")
    except Exception as e:
        logger.error(f"[数据库] 本地Agent表初始化失败: {e}")
    
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
    start_time = time.time()
    
    print(f"\n{Color.BOLD}{Color.CYAN}═══════════════════════════════════════════════════════════════════")
    print(f"                    MTSCOS AI 系统初始化")
    print(f"═══════════════════════════════════════════════════════════════════{Color.RESET}")
    
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
        'phase_10_middleware_objects': {},
        'phase_11_rules_permissions': {}
    }
    
    app_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    db_path = init_database_path(app_root)
    
    print(f"\n{Color.BOLD}{Color.BLUE}┌─────────────────────────────────────────────────────────────┐")
    print(f"│  阶段1: 数据库表初始化                                       │")
    print(f"└─────────────────────────────────────────────────────────────┘{Color.RESET}")
    phase_start = time.time()
    results['phase_1_database'] = init_database_tables(db_path)
    phase_time = time.time() - phase_start
    if results['phase_1_database']:
        print(f"  {Color.GREEN}✓ 数据库表初始化完成 ({phase_time:.2f}s){Color.RESET}")
    else:
        print(f"  {Color.RED}✗ 数据库表初始化失败{Color.RESET}")
    
    phase_start = time.time()
    results['phase_2_core'] = _init_core_managers(db_path)
    phase_time = time.time() - phase_start
    print(f"  {Color.CYAN}阶段2耗时: {phase_time:.2f}s{Color.RESET}")
    
    phase_start = time.time()
    results['phase_3_middlewares'], app = _init_middlewares(app)
    phase_time = time.time() - phase_start
    print(f"  {Color.CYAN}阶段3耗时: {phase_time:.2f}s{Color.RESET}")
    
    phase_start = time.time()
    results['phase_4_blueprints'] = _register_blueprints(app)
    phase_time = time.time() - phase_start
    print(f"  {Color.CYAN}阶段4耗时: {phase_time:.2f}s{Color.RESET}")
    
    phase_start = time.time()
    results['phase_5_dynamic'], app = _init_dynamic_systems(app)
    phase_time = time.time() - phase_start
    print(f"  {Color.CYAN}阶段5耗时: {phase_time:.2f}s{Color.RESET}")
    
    phase_start = time.time()
    results['phase_6_auto_routes'] = _init_auto_routes(app)
    phase_time = time.time() - phase_start
    print(f"  {Color.CYAN}阶段6耗时: {phase_time:.2f}s{Color.RESET}")
    
    phase_start = time.time()
    results['phase_7_auto_dev'] = _init_auto_dev_components()
    phase_time = time.time() - phase_start
    print(f"  {Color.CYAN}阶段7耗时: {phase_time:.2f}s{Color.RESET}")
    
    phase_start = time.time()
    results['phase_8_services'] = _init_services()
    phase_time = time.time() - phase_start
    print(f"  {Color.CYAN}阶段8耗时: {phase_time:.2f}s{Color.RESET}")
    
    phase_start = time.time()
    results['phase_9_employees'] = _init_employees()
    phase_time = time.time() - phase_start
    print(f"  {Color.CYAN}阶段9耗时: {phase_time:.2f}s{Color.RESET}")
    
    phase_start = time.time()
    results['phase_10_middleware_objects'] = _init_middleware_objects(app)
    phase_time = time.time() - phase_start
    print(f"  {Color.CYAN}阶段10耗时: {phase_time:.2f}s{Color.RESET}")
    
    phase_start = time.time()
    results['phase_11_rules_permissions'] = _init_rules_permissions_auto_complete(db_path)
    phase_time = time.time() - phase_start
    print(f"  {Color.CYAN}阶段11耗时: {phase_time:.2f}s{Color.RESET}")
    
    total_time = time.time() - start_time
    
    success_count = sum(
        sum(v.values()) for v in results.values() if isinstance(v, dict)
    ) + (1 if results['phase_1_database'] else 0)
    
    total_count = sum(
        len(v) for v in results.values() if isinstance(v, dict)
    ) + 1
    
    print(f"\n{Color.BOLD}{Color.GREEN}═══════════════════════════════════════════════════════════════════")
    print(f"                    初始化完成")
    print(f"═══════════════════════════════════════════════════════════════════{Color.RESET}")
    
    print(f"\n{Color.BOLD}📊 初始化统计:{Color.RESET}")
    print(f"  {Color.GREEN}✓ 成功: {success_count}{Color.RESET}")
    print(f"  {Color.RED}✗ 失败: {total_count - success_count}{Color.RESET}")
    print(f"  {Color.CYAN}⏱️ 总耗时: {total_time:.2f}秒{Color.RESET}")
    print(f"  {Color.MAGENTA}📈 成功率: {(success_count / total_count * 100):.1f}%{Color.RESET}")
    
    for phase_name, phase_result in results.items():
        if isinstance(phase_result, dict) and phase_result:
            phase_success = sum(phase_result.values())
            phase_total = len(phase_result)
            print(f"\n  {Color.BOLD}{phase_name}:{Color.RESET}")
            print(f"    {Color.GREEN}✓ {phase_success}/{phase_total} 成功{Color.RESET}")
    
    logger.info(f"[初始化] 系统初始化流程完成，耗时 {total_time:.2f}秒，{success_count}/{total_count} 组件成功")
    
    return results, app