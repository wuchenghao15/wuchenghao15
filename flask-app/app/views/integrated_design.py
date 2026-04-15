#!/usr/bin/env python3
"""
整合设计页面视图，负责展示和管理系统的所有可设置参数和用户数据
"""

from flask import Blueprint, render_template, request, session, redirect, url_for, flash, jsonify
from app.utils.logging import logger
from app.models.system_config import SystemConfig
from app.models.user import User
from app.services.config_service import config_service
from app.ai.ai_ensemble import AIEnsemble
from app.ai.instances import ai_instance_manager
from threading import Thread
import time

# 导入用户状态检查装饰器
from app.views.main import check_user_status

# 创建蓝图
integrated_design_bp = Blueprint('integrated_design', __name__, url_prefix='/integrated-design')

# AI集实例
ai_ensemble = AIEnsemble()


@integrated_design_bp.route('/')
@check_user_status
def integrated_design():
    """整合设计页面，展示和管理系统的所有可设置参数和用户数据"""
    try:
        # 准备用户信息
        user = {
            'username': session.get('username', 'Guest'),
            'role': session.get('user_level', 'guest')
        }
        
        # 检查用户权限，管理员和设计师可以访问
        user_role = session.get('user_level', 'guest')
        if user_role not in ['admin', 'super_admin', 'hardware_vikey_admin', 'designer']:
            flash('您没有权限访问此页面', 'error')
            return redirect(url_for('main.index'))
        
        # 从数据库读取所有系统配置（包括未激活的）
        system_configs = SystemConfig.get_all_configs_with_inactive()
        
        # 从数据库读取所有用户数据
        users = User.get_all_users()
        
        # 获取AI实例信息
        ai_instances = ai_instance_manager.get_all_instances()
        
        # 获取AI集信息
        ai_collections = ai_instance_manager.get_all_collections()
        
        # 获取AI集统计信息
        ai_stats = ai_instance_manager.get_instance_stats()
        
        # 获取主AI集信息
        ai_ensemble_info = ai_ensemble.get_ensemble_stats()
        
        # 准备页面数据
        page_data = {
            'system_configs': system_configs,
            'users': users,
            'ai_instances': ai_instances,
            'ai_collections': ai_collections,
            'ai_stats': ai_stats,
            'ai_ensemble_info': ai_ensemble_info,
            'user': user
        }
        
        return render_template('integrated_design.html', **page_data)
    except Exception as e:
        logger.error(f"访问整合设计页面时发生错误: {str(e)}")
        return f"访问整合设计页面时发生错误: {str(e)}", 500


@integrated_design_bp.route('/update-config', methods=['POST'])
@check_user_status
def update_config():
    """更新系统配置"""
    try:
        # 获取配置数据
        config_id = request.form.get('config_id')
        config_value = request.form.get('config_value')
        
        if not config_id or not config_value:
            return jsonify({'success': False, 'message': '缺少必要参数'})
        
        # 更新配置
        config = SystemConfig.get_by_id(config_id)
        if not config:
            return jsonify({'success': False, 'message': '配置不存在'})
        
        config.config_value = config_value
        config.save()
        
        # 刷新配置缓存
        config_service.refresh_config()
        
        return jsonify({'success': True, 'message': '配置更新成功'})
    except Exception as e:
        logger.error(f"更新配置时发生错误: {str(e)}")
        return jsonify({'success': False, 'message': f'更新配置时发生错误: {str(e)}'})


@integrated_design_bp.route('/toggle-config-status', methods=['POST'])
@check_user_status
def toggle_config_status():
    """切换系统配置状态"""
    try:
        # 获取配置数据
        config_id = request.form.get('config_id')
        
        if not config_id:
            return jsonify({'success': False, 'message': '缺少必要参数'})
        
        # 更新配置状态
        config = SystemConfig.get_by_id(config_id)
        if not config:
            return jsonify({'success': False, 'message': '配置不存在'})
        
        config.is_active = not config.is_active
        config.save()
        
        # 刷新配置缓存
        config_service.refresh_config()
        
        return jsonify({'success': True, 'message': '配置状态已切换'})
    except Exception as e:
        logger.error(f"切换配置状态时发生错误: {str(e)}")
        return jsonify({'success': False, 'message': f'切换配置状态时发生错误: {str(e)}'})


@integrated_design_bp.route('/delete-config', methods=['POST'])
@check_user_status
def delete_config():
    """删除系统配置"""
    try:
        # 获取配置数据
        config_id = request.form.get('config_id')
        
        if not config_id:
            return jsonify({'success': False, 'message': '缺少必要参数'})
        
        # 删除配置
        config = SystemConfig.get_by_id(config_id)
        if not config:
            return jsonify({'success': False, 'message': '配置不存在'})
        
        config.delete()
        
        # 刷新配置缓存
        config_service.refresh_config()
        
        return jsonify({'success': True, 'message': '配置已删除'})
    except Exception as e:
        logger.error(f"删除配置时发生错误: {str(e)}")
        return jsonify({'success': False, 'message': f'删除配置时发生错误: {str(e)}'})


@integrated_design_bp.route('/add-config', methods=['POST'])
@check_user_status
def add_config():
    """添加系统配置"""
    try:
        # 获取配置数据
        config_key = request.form.get('config_key')
        config_value = request.form.get('config_value')
        config_type = request.form.get('config_type', 'string')
        description = request.form.get('description', '')
        
        if not config_key or not config_value:
            return jsonify({'success': False, 'message': '缺少必要参数'})
        
        # 检查配置是否已存在
        existing_config = SystemConfig.get_by_key(config_key)
        if existing_config:
            return jsonify({'success': False, 'message': '配置键已存在'})
        
        # 添加配置
        config = SystemConfig(
            config_key=config_key,
            config_value=config_value,
            config_type=config_type,
            description=description
        )
        config.save()
        
        # 刷新配置缓存
        config_service.refresh_config()
        
        return jsonify({'success': True, 'message': '配置添加成功'})
    except Exception as e:
        logger.error(f"添加配置时发生错误: {str(e)}")
        return jsonify({'success': False, 'message': f'添加配置时发生错误: {str(e)}'})


@integrated_design_bp.route('/update-user', methods=['POST'])
@check_user_status
def update_user():
    """更新用户数据"""
    try:
        # 获取用户数据
        user_id = request.form.get('user_id')
        username = request.form.get('username')
        email = request.form.get('email')
        role = request.form.get('role')
        is_active = request.form.get('is_active')
        
        if not user_id or not username or not email or not role:
            return jsonify({'success': False, 'message': '缺少必要参数'})
        
        # 更新用户
        user = User.get_by_id(user_id)
        if not user:
            return jsonify({'success': False, 'message': '用户不存在'})
        
        user.username = username
        user.email = email
        user.role = role
        user.is_active = int(is_active)
        user.save()
        
        return jsonify({'success': True, 'message': '用户数据更新成功'})
    except Exception as e:
        logger.error(f"更新用户数据时发生错误: {str(e)}")
        return jsonify({'success': False, 'message': f'更新用户数据时发生错误: {str(e)}'})


@integrated_design_bp.route('/toggle-user-status', methods=['POST'])
@check_user_status
def toggle_user_status():
    """切换用户状态"""
    try:
        # 获取用户数据
        user_id = request.form.get('user_id')
        is_active = request.form.get('is_active')
        
        if not user_id or is_active is None:
            return jsonify({'success': False, 'message': '缺少必要参数'})
        
        # 更新用户状态
        user = User.get_by_id(user_id)
        if not user:
            return jsonify({'success': False, 'message': '用户不存在'})
        
        user.is_active = int(is_active)
        user.save()
        
        return jsonify({'success': True, 'message': '用户状态已切换'})
    except Exception as e:
        logger.error(f"切换用户状态时发生错误: {str(e)}")
        return jsonify({'success': False, 'message': f'切换用户状态时发生错误: {str(e)}'})


@integrated_design_bp.route('/delete-user', methods=['POST'])
@check_user_status
def delete_user():
    """删除用户"""
    try:
        # 获取用户数据
        user_id = request.form.get('user_id')
        
        if not user_id:
            return jsonify({'success': False, 'message': '缺少必要参数'})
        
        # 删除用户
        user = User.get_by_id(user_id)
        if not user:
            return jsonify({'success': False, 'message': '用户不存在'})
        
        user.delete()
        
        return jsonify({'success': True, 'message': '用户已删除'})
    except Exception as e:
        logger.error(f"删除用户时发生错误: {str(e)}")
        return jsonify({'success': False, 'message': f'删除用户时发生错误: {str(e)}'})


@integrated_design_bp.route('/add-user', methods=['POST'])
@check_user_status
def add_user():
    """添加用户"""
    try:
        # 获取用户数据
        username = request.form.get('username')
        email = request.form.get('email')
        password = request.form.get('password')
        role = request.form.get('role', 'user')
        
        if not username or not email or not password:
            return jsonify({'success': False, 'message': '缺少必要参数'})
        
        # 检查用户是否已存在
        existing_user = User.get_by_username(username)
        if existing_user:
            return jsonify({'success': False, 'message': '用户名已存在'})
        
        # 添加用户
        user = User(
            username=username,
            email=email,
            password=password,  # 密码会在save()中自动加密
            role=role
        )
        user.save()
        
        return jsonify({'success': True, 'message': '用户添加成功'})
    except Exception as e:
        logger.error(f"添加用户时发生错误: {str(e)}")
        return jsonify({'success': False, 'message': f'添加用户时发生错误: {str(e)}'})


@integrated_design_bp.route('/manage-ai-employee', methods=['POST'])
@check_user_status
def manage_ai_employee():
    """管理AI员工"""
    try:
        # 获取AI员工数据
        ai_id = request.form.get('ai_id')
        action = request.form.get('action')
        
        if not ai_id or not action:
            return jsonify({'success': False, 'message': '缺少必要参数'})
        
        # 执行AI员工管理操作
        if action == 'start':
            result = ai_instance_manager.start_instance(ai_id)
        elif action == 'stop':
            result = ai_instance_manager.stop_instance(ai_id)
        elif action == 'restart':
            result = ai_instance_manager.restart_instance(ai_id)
        else:
            return jsonify({'success': False, 'message': '无效的操作'})
        
        return jsonify({'success': result, 'message': f'AI员工 {action} 操作成功' if result else f'AI员工 {action} 操作失败'})
    except Exception as e:
        logger.error(f"管理AI员工时发生错误: {str(e)}")
        return jsonify({'success': False, 'message': f'管理AI员工时发生错误: {str(e)}'})


@integrated_design_bp.route('/manage-thread', methods=['POST'])
@check_user_status
def manage_thread():
    """管理线程"""
    try:
        # 获取线程数据
        thread_id = request.form.get('thread_id')
        action = request.form.get('action')
        
        if not thread_id or not action:
            return jsonify({'success': False, 'message': '缺少必要参数'})
        
        # 执行线程管理操作
        # 这里需要实现线程AI管理的具体逻辑
        # 暂时返回成功
        return jsonify({'success': True, 'message': f'线程 {action} 操作成功'})
    except Exception as e:
        logger.error(f"管理线程时发生错误: {str(e)}")
        return jsonify({'success': False, 'message': f'管理线程时发生错误: {str(e)}'})


@integrated_design_bp.route('/manage-ai-ensemble', methods=['POST'])
@check_user_status
def manage_ai_ensemble():
    """管理AI集"""
    try:
        # 获取AI集数据
        ensemble_id = request.form.get('ensemble_id')
        action = request.form.get('action')
        
        if not ensemble_id or not action:
            return jsonify({'success': False, 'message': '缺少必要参数'})
        
        # 执行AI集管理操作
        if action == 'activate':
            result = ai_ensemble.activate_ensemble(ensemble_id)
        elif action == 'deactivate':
            result = ai_ensemble.deactivate_ensemble(ensemble_id)
        elif action == 'optimize':
            result = ai_ensemble.optimize_ensemble(ensemble_id)
        elif action == 'dispatch_task':
            # 获取任务数据
            task_data = request.form.get('task_data')
            import json
            task_data = json.loads(task_data) if task_data else {}
            result = ai_ensemble.dispatch_task(ensemble_id, task_data)
        else:
            return jsonify({'success': False, 'message': '无效的操作'})
        
        return jsonify({'success': result, 'message': f'AI集 {action} 操作成功' if result else f'AI集 {action} 操作失败'})
    except Exception as e:
        logger.error(f"管理AI集时发生错误: {str(e)}")
        return jsonify({'success': False, 'message': f'管理AI集时发生错误: {str(e)}'})


@integrated_design_bp.route('/get-ai-ensemble-stats', methods=['GET'])
def get_ai_ensemble_stats():
    """获取AI集统计信息"""
    try:
        # 获取AI集统计信息
        ai_ensemble_stats = ai_ensemble.get_ensemble_stats()
        
        return jsonify({'success': True, 'ai_ensemble_stats': ai_ensemble_stats})
    except Exception as e:
        logger.error(f"获取AI集统计信息时发生错误: {str(e)}")
        return jsonify({'success': False, 'message': f'获取AI集统计信息时发生错误: {str(e)}'})


@integrated_design_bp.route('/refresh-ai-ensemble', methods=['POST'])
@check_user_status
def refresh_ai_ensemble():
    """刷新AI集"""
    try:
        # 刷新AI集
        result = ai_ensemble.refresh_ensemble()
        
        return jsonify({'success': result, 'message': 'AI集已刷新' if result else 'AI集刷新失败'})
    except Exception as e:
        logger.error(f"刷新AI集时发生错误: {str(e)}")
        return jsonify({'success': False, 'message': f'刷新AI集时发生错误: {str(e)}'})


@integrated_design_bp.route('/run-threaded-task', methods=['POST'])
@check_user_status
def run_threaded_task():
    """运行线程任务"""
    try:
        # 获取任务数据
        task_type = request.form.get('task_type')
        
        if not task_type:
            return jsonify({'success': False, 'message': '缺少必要参数'})
        
        # 在线程中运行任务
        def threaded_task():
            """线程任务函数"""
            logger.info(f"开始运行线程任务: {task_type}")
            # 这里需要实现具体的线程任务逻辑
            time.sleep(5)  # 模拟任务运行
            logger.info(f"线程任务完成: {task_type}")
        
        # 启动线程
        thread = Thread(target=threaded_task)
        thread.daemon = True
        thread.start()
        
        return jsonify({'success': True, 'message': '线程任务已启动'})
    except Exception as e:
        logger.error(f"运行线程任务时发生错误: {str(e)}")
        return jsonify({'success': False, 'message': f'运行线程任务时发生错误: {str(e)}'})


@integrated_design_bp.route('/update-collection-status', methods=['POST'])
@check_user_status
def update_collection_status():
    """更新AI集状态"""
    try:
        # 获取AI集数据
        collection_id = request.form.get('collection_id')
        status = request.form.get('status')
        
        if not collection_id or not status:
            return jsonify({'success': False, 'message': '缺少必要参数'})
        
        # 执行AI集状态更新操作
        result = ai_instance_manager.update_collection(collection_id, {'status': status})
        
        return jsonify({'success': result, 'message': f'AI集状态已更新为 {status}' if result else 'AI集状态更新失败'})
    except Exception as e:
        logger.error(f"更新AI集状态时发生错误: {str(e)}")
        return jsonify({'success': False, 'message': f'更新AI集状态时发生错误: {str(e)}'})


@integrated_design_bp.route('/delete-collection', methods=['POST'])
@check_user_status
def delete_collection():
    """删除AI集"""
    try:
        # 获取AI集数据
        collection_id = request.form.get('collection_id')
        
        if not collection_id:
            return jsonify({'success': False, 'message': '缺少必要参数'})
        
        # 执行AI集删除操作
        result = ai_instance_manager.delete_collection(collection_id)
        
        return jsonify({'success': result, 'message': 'AI集已删除' if result else 'AI集删除失败'})
    except Exception as e:
        logger.error(f"删除AI集时发生错误: {str(e)}")
        return jsonify({'success': False, 'message': f'删除AI集时发生错误: {str(e)}'})


@integrated_design_bp.route('/delete-ai-employee', methods=['POST'])
@check_user_status
def delete_ai_employee():
    """删除AI员工"""
    try:
        # 获取AI员工数据
        ai_id = request.form.get('ai_id')
        
        if not ai_id:
            return jsonify({'success': False, 'message': '缺少必要参数'})
        
        # 执行AI员工删除操作
        result = ai_instance_manager.delete_ai_instance(ai_id)
        
        return jsonify({'success': result, 'message': 'AI员工已删除' if result else 'AI员工删除失败'})
    except Exception as e:
        logger.error(f"删除AI员工时发生错误: {str(e)}")
        return jsonify({'success': False, 'message': f'删除AI员工时发生错误: {str(e)}'})


@integrated_design_bp.route('/create-security-manager', methods=['POST'])
@check_user_status
def create_security_manager():
    """创建安全管理器AI员工"""
    try:
        # 创建安全管理器AI员工
        security_manager_id = "security-manager-001"
        
        # 检查安全管理器是否已存在
        existing_instance = ai_instance_manager.get_ai_instance(security_manager_id)
        if existing_instance:
            return jsonify({'success': False, 'message': '安全管理器AI员工已存在'})
        
        # 创建安全管理器AI实例
        security_manager = ai_instance_manager.create_ai_instance(
            instance_id=security_manager_id,
            ai_type="security_manager",
            name="安全管理器AI",
            description="负责处理关键点管理和数据安全参数管理",
            functions=["key_point_management", "data_security_management", "security_monitoring", "security_report_generation", "security_policy_enforcement"],
            responsibilities=["管理系统关键点", "管理数据安全参数", "监控系统安全状态", "生成安全报告", "执行安全策略"],
            config={
                "key_point_management": {
                    "enabled": True,
                    "auto_detection": True,
                    "notification_enabled": True
                },
                "data_security": {
                    "encryption_enabled": True,
                    "access_control": "strict",
                    "audit_logging": True
                },
                "security_monitoring": {
                    "enabled": True,
                    "interval": 300,
                    "alert_threshold": 5
                }
            },
            collection_id="security_ai_collection"
        )
        
        if security_manager:
            return jsonify({'success': True, 'message': '安全管理器AI员工创建成功'})
        else:
            return jsonify({'success': False, 'message': '安全管理器AI员工创建失败'})
    except Exception as e:
        logger.error(f"创建安全管理器AI员工时发生错误: {str(e)}")
        return jsonify({'success': False, 'message': f'创建安全管理器AI员工时发生错误: {str(e)}'})


@integrated_design_bp.route('/get-key-points', methods=['GET'])
def get_key_points():
    """获取系统关键点"""
    try:
        # 这里需要实现获取系统关键点的逻辑
        # 暂时返回模拟数据
        key_points = [
            {
                "id": "key-point-001",
                "name": "系统配置",
                "description": "系统核心配置参数",
                "security_level": "high",
                "status": "active",
                "last_updated": "2026-02-24 10:00:00"
            },
            {
                "id": "key-point-002",
                "name": "用户管理",
                "description": "用户数据和权限管理",
                "security_level": "high",
                "status": "active",
                "last_updated": "2026-02-24 10:00:00"
            },
            {
                "id": "key-point-003",
                "name": "AI员工管理",
                "description": "AI员工的创建、配置和管理",
                "security_level": "medium",
                "status": "active",
                "last_updated": "2026-02-24 10:00:00"
            }
        ]
        
        return jsonify({'success': True, 'key_points': key_points})
    except Exception as e:
        logger.error(f"获取系统关键点时发生错误: {str(e)}")
        return jsonify({'success': False, 'message': f'获取系统关键点时发生错误: {str(e)}'})


@integrated_design_bp.route('/get-security-parameters', methods=['GET'])
def get_security_parameters():
    """获取数据安全参数"""
    try:
        # 从系统配置中获取安全相关参数
        security_parameters = []
        system_configs = SystemConfig.get_all_configs()
        
        for config in system_configs:
            if 'security' in config.config_key.lower() or 'key' in config.config_key.lower() or 'secret' in config.config_key.lower():
                security_parameters.append({
                    "id": config.config_id,
                    "key": config.config_key,
                    "value": config.config_value,
                    "type": config.config_type,
                    "description": config.description,
                    "status": "active" if config.is_active else "inactive"
                })
        
        return jsonify({'success': True, 'security_parameters': security_parameters})
    except Exception as e:
        logger.error(f"获取数据安全参数时发生错误: {str(e)}")
        return jsonify({'success': False, 'message': f'获取数据安全参数时发生错误: {str(e)}'})


@integrated_design_bp.route('/get-thread-ai', methods=['GET'])
def get_thread_ai():
    """获取线程AI数据"""
    try:
        # 获取所有AI实例
        ai_instances = ai_instance_manager.get_all_instances()
        
        # 筛选出线程管理AI
        thread_ai = []
        for ai in ai_instances:
            if ai['ai_type'] == 'thread_manager':
                # 添加当前线程数和最大线程数
                ai['current_threads'] = ai.get('current_threads', 0)
                ai['max_threads'] = ai.get('max_threads', 10)
                thread_ai.append(ai)
        
        return jsonify({'success': True, 'thread_ai': thread_ai})
    except Exception as e:
        logger.error(f"获取线程AI数据时发生错误: {str(e)}")
        return jsonify({'success': False, 'message': f'获取线程AI数据时发生错误: {str(e)}'})


@integrated_design_bp.route('/create-thread-ai', methods=['POST'])
@check_user_status
def create_thread_ai():
    """创建线程AI"""
    try:
        # 创建线程管理AI实例
        thread_ai_id = f"thread-manager-{int(time.time())}"
        
        # 创建线程管理AI实例
        thread_ai = ai_instance_manager.create_ai_instance(
            instance_id=thread_ai_id,
            ai_type="thread_manager",
            name="线程管理AI",
            description="负责管理系统线程，避免数据堵塞",
            functions=["thread_management", "thread_monitoring", "thread_optimization", "deadlock_detection", "resource_allocation"],
            responsibilities=["管理系统线程", "监控线程状态", "优化线程资源分配", "检测死锁", "分配系统资源"],
            config={
                "thread_management": {
                    "enabled": True,
                    "auto_adjust": True,
                    "max_threads": 10,
                    "thread_timeout": 3600
                },
                "monitoring": {
                    "enabled": True,
                    "interval": 60,
                    "alert_enabled": True
                },
                "deadlock_detection": {
                    "enabled": True,
                    "interval": 120
                }
            },
            collection_id="thread_ai_collection"
        )
        
        if thread_ai:
            return jsonify({'success': True, 'message': '线程AI创建成功'})
        else:
            return jsonify({'success': False, 'message': '线程AI创建失败'})
    except Exception as e:
        logger.error(f"创建线程AI时发生错误: {str(e)}")
        return jsonify({'success': False, 'message': f'创建线程AI时发生错误: {str(e)}'})


@integrated_design_bp.route('/manage-thread-ai', methods=['POST'])
@check_user_status
def manage_thread_ai():
    """管理线程AI"""
    try:
        # 获取线程AI数据
        ai_id = request.form.get('ai_id')
        action = request.form.get('action')
        
        if not ai_id or not action:
            return jsonify({'success': False, 'message': '缺少必要参数'})
        
        # 执行线程AI管理操作
        if action == 'start':
            result = ai_instance_manager.update_ai_instance(ai_id, {'status': 'active'})
        elif action == 'stop':
            result = ai_instance_manager.update_ai_instance(ai_id, {'status': 'inactive'})
        else:
            return jsonify({'success': False, 'message': '无效的操作'})
        
        return jsonify({'success': result, 'message': f'线程AI {action} 操作成功' if result else f'线程AI {action} 操作失败'})
    except Exception as e:
        logger.error(f"管理线程AI时发生错误: {str(e)}")
        return jsonify({'success': False, 'message': f'管理线程AI时发生错误: {str(e)}'})


@integrated_design_bp.route('/delete-thread-ai', methods=['POST'])
@check_user_status
def delete_thread_ai():
    """删除线程AI"""
    try:
        # 获取线程AI数据
        ai_id = request.form.get('ai_id')
        
        if not ai_id:
            return jsonify({'success': False, 'message': '缺少必要参数'})
        
        # 执行线程AI删除操作
        result = ai_instance_manager.delete_ai_instance(ai_id)
        
        return jsonify({'success': result, 'message': '线程AI已删除' if result else '线程AI删除失败'})
    except Exception as e:
        logger.error(f"删除线程AI时发生错误: {str(e)}")
        return jsonify({'success': False, 'message': f'删除线程AI时发生错误: {str(e)}'})


@integrated_design_bp.route('/get-system-threads', methods=['GET'])
def get_system_threads():
    """获取系统线程数据"""
    try:
        # 这里需要实现获取系统线程数据的逻辑
        # 暂时返回模拟数据
        threads = [
            {
                "thread_id": "thread-1",
                "name": "数据同步线程",
                "type": "data-sync",
                "status": "running",
                "created_at": "2026-02-24 10:00:00"
            },
            {
                "thread_id": "thread-2",
                "name": "AI管理线程",
                "type": "ai-manager",
                "status": "running",
                "created_at": "2026-02-24 09:30:00"
            },
            {
                "thread_id": "thread-3",
                "name": "监控线程",
                "type": "monitor",
                "status": "running",
                "created_at": "2026-02-24 09:00:00"
            }
        ]
        
        return jsonify({'success': True, 'threads': threads})
    except Exception as e:
        logger.error(f"获取系统线程数据时发生错误: {str(e)}")
        return jsonify({'success': False, 'message': f'获取系统线程数据时发生错误: {str(e)}'})


# 注册蓝图到主应用
def register_blueprint(app):
    """注册整合设计蓝图"""
    app.register_blueprint(integrated_design_bp)
