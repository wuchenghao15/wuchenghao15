#!/usr/bin/env python3
"""
MTSCOS AI Project Application Initialization
负责Flask应用的完整初始化流程
"""

import os
import sys
import logging
from datetime import datetime

logger = logging.getLogger(__name__)


def _register_blueprints(app):
    """注册所有API蓝图"""
    blueprints = [
        ('agent_management_api', 'app.api.agent_management_api'),
        ('ai_dashboard_api', 'app.api.ai_dashboard_api'),
        ('ai_professional_api', 'app.api.ai_professional_api'),
        ('ai_recommendation_api', 'app.api.ai_recommendation_api'),
        ('ai_prediction_api', 'app.api.ai_prediction_api'),
        ('ai_decision_api', 'app.api.ai_decision_api'),
        ('ai_cognitive_api', 'app.api.ai_cognitive_api'),
        ('ai_qna_api', 'app.api.ai_qna_api'),
        ('ai_adaptive_api', 'app.api.ai_adaptive_api'),
        ('ai_evaluation_api', 'app.api.ai_evaluation_api'),
        ('ai_emotion_api', 'app.api.ai_emotion_api'),
        ('ai_memory_api', 'app.api.ai_memory_api'),
        ('system_extension_api', 'app.api.system_extension_api'),
        ('version_unified_api', 'app.api.version_unified_api'),
        ('health_api', 'app.api.health_api'),
        ('log_api', 'app.api.log_api'),
        ('config_api', 'app.api.config_api'),
        ('activity_api', 'app.api.activity_api'),
        ('export_api', 'app.api.export_api'),
        ('ai_engine_api', 'app.api.ai_engine_api'),
        ('ai_brain_api', 'app.api.ai_brain_api'),
        ('ai_cluster_api', 'app.api.ai_cluster_api'),
        ('ai_self_learning_api', 'app.api.ai_self_learning_api'),
        ('ai_gamification_api', 'app.api.ai_gamification_api'),
        ('ai_monitoring_api', 'app.api.ai_monitoring_api'),
        ('ai_auto_upgrade_api', 'app.api.ai_auto_upgrade_api'),
        ('ai_test_api', 'app.api.ai_test_api'),
        ('history_api', 'app.api.history_api'),
        ('ai_enterprise_api', 'app.api.ai_enterprise_api'),
        ('chinese_listening_api', 'app.api.chinese_listening_api'),
        ('unified_question_api', 'app.api.unified_question_api'),
        ('dynamic_question_api', 'app.api.dynamic_question_api'),
    ]
    
    registered = 0
    failed = 0
    
    for bp_name, module_path in blueprints:
        try:
            module = __import__(module_path, fromlist=[bp_name])
            bp = getattr(module, bp_name)
            app.register_blueprint(bp)
            registered += 1
            logger.info(f"✓ 注册蓝图: {bp_name}")
        except Exception as e:
            failed += 1
            logger.warning(f"✗ 注册蓝图失败: {bp_name} - {str(e)}")
    
    return {'registered': registered, 'failed': failed}


def _init_database(app):
    """初始化数据库"""
    try:
        from fix_system_rules import create_system_rules_table
        create_system_rules_table()
        logger.info("✓ 系统规则表初始化完成")
    except Exception as e:
        logger.warning(f"✗ 系统规则表初始化失败: {str(e)}")
    
    try:
        from db_manager import init_database
        init_database()
        logger.info("✓ 主数据库初始化完成")
    except Exception as e:
        logger.warning(f"✗ 主数据库初始化失败: {str(e)}")
    
    try:
        from init_ai_fixer_db import init_ai_fixer_database
        init_ai_fixer_database()
        logger.info("✓ AI修复数据库初始化完成")
    except Exception as e:
        logger.warning(f"✗ AI修复数据库初始化失败: {str(e)}")
    
    return True


def _init_services(app):
    """初始化系统服务"""
    services = [
        ('cache_manager', '缓存管理器'),
        ('backup_manager', '备份管理器'),
        ('system_monitor', '系统监控'),
        ('task_scheduler', '任务调度'),
        ('audit_service', '审计服务'),
        ('email_service', '邮件服务'),
        ('sms_service', '短信服务'),
        ('data_validator', '数据验证器'),
        ('search_service', '搜索服务'),
        ('file_manager', '文件管理器'),
    ]
    
    initialized = []
    failed = []
    
    for service_name, display_name in services:
        try:
            module = __import__(service_name, fromlist=[''])
            if hasattr(module, 'init'):
                module.init()
            elif hasattr(module, '__init__'):
                pass
            initialized.append(display_name)
            logger.info(f"✓ 初始化服务: {display_name}")
        except ImportError:
            logger.info(f"○ 服务未安装: {display_name}")
        except Exception as e:
            failed.append(f"{display_name}: {str(e)}")
            logger.warning(f"✗ 服务初始化失败: {display_name} - {str(e)}")
    
    return {'initialized': initialized, 'failed': failed}


def _init_ai_employees(app):
    """初始化AI员工系统"""
    try:
        from ai_engines.all_ai_employees_loader import load_all_employees
        load_all_employees()
        logger.info("✓ AI员工加载完成")
    except Exception as e:
        logger.warning(f"✗ AI员工加载失败: {str(e)}")
    
    try:
        from ai_engines.data_sync import sync_all_employees
        sync_all_employees()
        logger.info("✓ AI员工数据同步完成")
    except Exception as e:
        logger.warning(f"✗ AI员工数据同步失败: {str(e)}")
    
    return True


def _init_github_upload(app):
    """初始化GitHub自动上传Agent"""
    try:
        from ai_engines.github_auto_upload_agent import init_github_upload_agent
        init_github_upload_agent(app)
        logger.info("✓ GitHub自动上传Agent初始化完成")
    except Exception as e:
        logger.warning(f"✗ GitHub自动上传Agent初始化失败: {str(e)}")
    
    return True


def run_full_initialization(app):
    """执行完整的应用初始化流程"""
    logger.info("=" * 60)
    logger.info("  MTSCOS AI Project 应用初始化")
    logger.info(f"  时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    logger.info("=" * 60)
    
    results = {}
    
    logger.info("\n[阶段1] 注册蓝图...")
    bp_result = _register_blueprints(app)
    results['blueprints'] = bp_result
    logger.info(f"  蓝图注册结果: 成功 {bp_result['registered']} 个, 失败 {bp_result['failed']} 个")
    
    logger.info("\n[阶段2] 初始化数据库...")
    db_result = _init_database(app)
    results['database'] = {'success': db_result}
    
    logger.info("\n[阶段3] 初始化系统服务...")
    service_result = _init_services(app)
    results['services'] = service_result
    logger.info(f"  服务初始化结果: 成功 {len(service_result['initialized'])} 个, 失败 {len(service_result['failed'])} 个")
    
    logger.info("\n[阶段4] 初始化AI员工系统...")
    ai_result = _init_ai_employees(app)
    results['ai_employees'] = {'success': ai_result}
    
    logger.info("\n[阶段5] 初始化GitHub上传Agent...")
    github_result = _init_github_upload(app)
    results['github_upload'] = {'success': github_result}
    
    logger.info("\n" + "=" * 60)
    logger.info("  应用初始化完成")
    logger.info("=" * 60)
    
    return results, app


def create_app():
    """创建并初始化Flask应用"""
    from flask import Flask
    
    app = Flask(__name__)
    
    app.config['JSON_AS_ASCII'] = False
    app.config['TEMPLATES_AUTO_RELOAD'] = True
    
    run_full_initialization(app)
    
    return app


if __name__ == '__main__':
    app = create_app()
    # 安全修复：通过环境变量控制debug模式，避免生产环境泄露信息
    app.run(host='0.0.0.0', port=8888, debug=os.environ.get('FLASK_DEBUG', '0') == '1')