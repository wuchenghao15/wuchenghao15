# -*- coding: utf-8 -*-
from flask import Blueprint, render_template, session, redirect, url_for, flash, request, jsonify
from functools import wraps
from app.services.rules_permissions import permission_manager, ResourceType, ActionType, PermissionLevel
from app.utils.logging import logger
import time

physics_engine_bp = Blueprint('physics_engine', __name__, url_prefix='/physics-engine')

RATE_LIMIT_WINDOW = 60
MAX_REQUESTS_PER_WINDOW = 100
request_timestamps = {}

PERMISSION_REQUIREMENTS = {
    'view': {
        'roles': ['user', 'teacher', 'researcher', 'admin', 'super_admin', 'hardware_admin'],
        'min_level': PermissionLevel.VIEW.value
    },
    'simulate': {
        'roles': ['teacher', 'researcher', 'admin', 'super_admin', 'hardware_admin'],
        'min_level': PermissionLevel.EDIT.value
    },
    'manage': {
        'roles': ['researcher', 'admin', 'super_admin', 'hardware_admin'],
        'min_level': PermissionLevel.MANAGE.value
    }
}


def check_rate_limit(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        user_id = session.get('user_id', 'anonymous')
        now = time.time()
        
        if user_id not in request_timestamps:
            request_timestamps[user_id] = []
        
        request_timestamps[user_id] = [
            ts for ts in request_timestamps[user_id]
            if now - ts < RATE_LIMIT_WINDOW
        ]
        
        if len(request_timestamps[user_id]) >= MAX_REQUESTS_PER_WINDOW:
            logger.warning(f"用户 {user_id} 触发物理引擎频率限制")
            return jsonify({
                'success': False,
                'error': '请求过于频繁，请稍后再试',
                'retry_after': RATE_LIMIT_WINDOW
            }), 429
        
        request_timestamps[user_id].append(now)
        return f(*args, **kwargs)
    return decorated_function


def require_permission(action='view'):
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            user_id = session.get('user_id')
            role = session.get('role', 'guest')
            
            if not user_id:
                flash('请先登录后访问此功能', 'warning')
                return redirect(url_for('auth.login', next=request.path))
            
            req = PERMISSION_REQUIREMENTS.get(action, PERMISSION_REQUIREMENTS['view'])
            
            has_role_access = role in req['roles']
            
            has_perm = permission_manager.check_access(
                user_id=str(user_id),
                resource_type=ResourceType.DATA.value,
                action=ActionType.EXECUTE.value if action == 'simulate' else ActionType.READ.value,
                ip_address=request.remote_addr
            )
            
            if not has_role_access and not has_perm:
                logger.warning(f"用户 {user_id} (角色: {role}) 尝试访问物理引擎 {action} 权限不足")
                from flask import abort
                abort(403)
            
            return f(*args, **kwargs)
        return decorated_function
    return decorator


def log_access(action):
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            user_id = session.get('user_id', 'anonymous')
            logger.info(f"物理引擎访问: 用户={user_id}, 动作={action}, IP={request.remote_addr}")
            return f(*args, **kwargs)
        return decorated_function
    return decorator


@physics_engine_bp.route('/')
@require_permission('view')
@log_access('view_dashboard')
@check_rate_limit
def index():
    user_id = session.get('user_id')
    username = session.get('username', '用户')
    role = session.get('role', 'guest')
    
    can_simulate = role in PERMISSION_REQUIREMENTS['simulate']['roles']
    can_manage = role in PERMISSION_REQUIREMENTS['manage']['roles']
    
    return render_template('physics_engine.html',
                         username=username,
                         role=role,
                         can_simulate=can_simulate,
                         can_manage=can_manage)


@physics_engine_bp.route('/api/permission-check')
def check_permission_api():
    user_id = session.get('user_id')
    role = session.get('role', 'guest')
    
    return jsonify({
        'success': True,
        'user_id': user_id,
        'role': role,
        'permissions': {
            'can_view': role in PERMISSION_REQUIREMENTS['view']['roles'],
            'can_simulate': role in PERMISSION_REQUIREMENTS['simulate']['roles'],
            'can_manage': role in PERMISSION_REQUIREMENTS['manage']['roles']
        }
    })


def init_physics_permissions():
    logger.info("初始化物理引擎权限...")
    
    physics_perms = [
        ('physics:view', '查看物理引擎'),
        ('physics:simulate', '运行物理模拟'),
        ('physics:particle_create', '创建粒子系统'),
        ('physics:particle_delete', '删除粒子系统'),
        ('physics:render', '使用渲染引擎'),
        ('physics:formula_manage', '管理物理公式'),
        ('physics:model_manage', '管理数学模型'),
        ('physics:constants_manage', '管理物理常数'),
        ('physics:admin', '物理引擎管理权限')
    ]
    
    for perm_id, desc in physics_perms:
        permission_manager.define_permission(perm_id, desc)
    
    role_permissions = {
        'user': ['physics:view', 'physics:render'],
        'teacher': ['physics:view', 'physics:simulate', 'physics:render', 'physics:particle_create'],
        'researcher': ['physics:view', 'physics:simulate', 'physics:render', 'physics:particle_create',
                       'physics:particle_delete', 'physics:formula_manage', 'physics:model_manage'],
        'admin': ['physics:view', 'physics:simulate', 'physics:render', 'physics:particle_create',
                  'physics:particle_delete', 'physics:formula_manage', 'physics:model_manage',
                  'physics:constants_manage'],
        'super_admin': ['physics:view', 'physics:simulate', 'physics:render', 'physics:particle_create',
                        'physics:particle_delete', 'physics:formula_manage', 'physics:model_manage',
                        'physics:constants_manage', 'physics:admin'],
        'hardware_admin': ['physics:view', 'physics:simulate', 'physics:render', 'physics:particle_create',
                          'physics:particle_delete', 'physics:formula_manage', 'physics:model_manage',
                          'physics:constants_manage', 'physics:admin']
    }
    
    for role_id, perms in role_permissions.items():
        if role_id in permission_manager.roles:
            for perm in perms:
                permission_manager.assign_permission_to_role(role_id, perm)
    
    permission_manager.add_rule(
        'physics_rate_limit',
        lambda ctx: ctx.get('request_count', 0) > MAX_REQUESTS_PER_WINDOW,
        lambda ctx: {'action': 'throttle', 'message': '请求过于频繁'},
        priority=10
    )
    
    permission_manager.add_rule(
        'physics_simulate_restriction',
        lambda ctx: ctx.get('action') == 'simulate' and ctx.get('role') in ['user', 'guest'],
        lambda ctx: {'action': 'deny', 'message': '模拟功能仅对教师及以上角色开放'},
        priority=9
    )
    
    permission_manager.add_rule(
        'physics_particle_limit',
        lambda ctx: ctx.get('particle_count', 0) > 1000 and ctx.get('role') not in ['admin', 'super_admin', 'hardware_admin'],
        lambda ctx: {'action': 'limit', 'message': '粒子数量限制为1000个，请升级权限'},
        priority=8
    )
    
    logger.info("物理引擎权限初始化完成")
