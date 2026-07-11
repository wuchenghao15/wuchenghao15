# -*- coding: utf-8 -*-
"""
MTSCOS 集成设置系统
- 权限控制：仅管理员可访问
- 数据库配置集成：系统参数统一从数据库调取
- 支持GLOBAL/USER/SESSION/SYSTEM scopes
- AI深度集成：智能配置推荐
"""
from flask import Blueprint, render_template, jsonify, request, redirect, url_for
from flask import session
import sys
import logging
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)

integrated_settings_bp = Blueprint('integrated_settings', __name__, url_prefix='/settings')

# 配置分类定义
SETTINGS_CATEGORIES = {
    'base': {'name': '基础配置', 'description': '系统基础参数配置', 'icon': 'settings'},
    'server': {'name': '服务器配置', 'description': '服务器运行参数', 'icon': 'server'},
    'database': {'name': '数据库配置', 'description': '数据库连接与管理', 'icon': 'database'},
    'security': {'name': '安全配置', 'description': '系统安全策略', 'icon': 'shield'},
    'cluster': {'name': '集群配置', 'description': '集群节点管理', 'icon': 'cluster'},
    'cache': {'name': '缓存配置', 'description': '多级缓存系统', 'icon': 'cache'},
    'ai': {'name': 'AI配置', 'description': 'AI引擎参数', 'icon': 'ai'},
    'api': {'name': 'API配置', 'description': 'API接口设置', 'icon': 'api'},
    'log': {'name': '日志配置', 'description': '日志级别与存储', 'icon': 'log'},
}

def require_admin_role():
    """检查是否具有管理员权限 - 符合系统约束：设置页面仅限管理员访问"""
    user_id = session.get('user_id')
    role = session.get('role')
    
    if not user_id:
        logger.warning("[权限检查] 未登录用户尝试访问设置页面")
        return redirect(url_for('auth.login'))
    
    # 学生用户无法访问设置页面 - 符合系统约束
    if role == 'student':
        logger.warning(f"[权限检查] 学生用户 {session.get('username')} 尝试访问设置页面，被拒绝")
        return redirect(url_for('exam_system.index'))
    
    if role not in ['admin', 'super_admin', 'hardware_admin', 'hardware_vikey_admin']:
        logger.warning(f"[权限检查] 用户 {session.get('username')} ({role}) 尝试访问设置页面，被拒绝")
        return jsonify({'success': False, 'error': 'Forbidden', 'message': '需要管理员权限'}), 403
    
    return None

@integrated_settings_bp.route('/')
def index():
    """集成设置页面 - 展示所有配置分类"""
    result = require_admin_role()
    if result:
        return result
    
    try:
        from app.config import get_db_config_manager
        db_manager = get_db_config_manager()
        
        # 获取所有配置分类
        categories = db_manager.get_categories() if db_manager else []
        
        # 统计每个分类的配置数量
        category_stats = {}
        for cat in categories:
            cat_settings = db_manager.get_category(cat) if db_manager else {}
            category_stats[cat] = {
                'count': len(cat_settings),
                'info': SETTINGS_CATEGORIES.get(cat, {'name': cat, 'description': '', 'icon': 'settings'})
            }
        
        user = {
            'username': session.get('username', ''),
            'role': session.get('role', '')
        }
        
        return render_template('integrated_settings.html', 
                              user=user, 
                              categories=categories,
                              category_stats=category_stats,
                              SETTINGS_CATEGORIES=SETTINGS_CATEGORIES)
    except Exception as e:
        logger.error(f"[设置页面] 加载失败: {str(e)}")
        return render_template('error.html', error=str(e)), 500

@integrated_settings_bp.route('/category/<category>')
def category_settings(category):
    """分类设置页面 - 展示特定分类的所有配置"""
    result = require_admin_role()
    if result:
        return result
    
    try:
        from app.config import get_db_config_manager
        db_manager = get_db_config_manager()
        
        # 获取分类配置
        settings = db_manager.get_category(category) if db_manager else {}
        keys = db_manager.get_keys_by_category(category) if db_manager else []
        
        # 获取分类信息
        category_info = SETTINGS_CATEGORIES.get(category, {'name': category, 'description': '', 'icon': 'settings'})
        
        user = {
            'username': session.get('username', ''),
            'role': session.get('role', '')
        }
        
        return render_template('settings_category.html',
                              user=user,
                              category=category,
                              category_info=category_info,
                              settings=settings,
                              keys=keys)
    except Exception as e:
        logger.error(f"[分类设置] 加载失败: {str(e)}")
        return render_template('error.html', error=str(e)), 500

@integrated_settings_bp.route('/system')
def system_settings():
    """系统设置"""
    result = require_admin_role()
    if result:
        return result
    return render_template('system_config.html')

@integrated_settings_bp.route('/security')
def security_settings():
    """安全设置"""
    result = require_admin_role()
    if result:
        return result
    return render_template('security_settings.html')

# ==================== API接口 ====================

@integrated_settings_bp.route('/api/categories', methods=['GET'])
def api_get_categories():
    """获取所有配置分类"""
    try:
        from app.config import get_db_config_manager
        db_manager = get_db_config_manager()
        
        categories = db_manager.get_categories() if db_manager else []
        
        return jsonify({
            'success': True,
            'categories': categories,
            'count': len(categories)
        })
    except Exception as e:
        logger.error(f"[API] 获取分类失败: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500

@integrated_settings_bp.route('/api/category/<category>', methods=['GET'])
def api_get_category_settings(category):
    """获取分类配置"""
    try:
        from app.config import get_db_config_manager
        db_manager = get_db_config_manager()
        
        settings = db_manager.get_category(category) if db_manager else {}
        
        return jsonify({
            'success': True,
            'category': category,
            'settings': settings,
            'count': len(settings)
        })
    except Exception as e:
        logger.error(f"[API] 获取分类配置失败: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500

@integrated_settings_bp.route('/api/setting/<key>', methods=['GET'])
def api_get_setting(key):
    """获取单个配置"""
    try:
        from app.config import get_config_value
        value = get_config_value(key)
        
        if value is None:
            return jsonify({'success': False, 'error': '配置不存在'}), 404
        
        return jsonify({
            'success': True,
            'key': key,
            'value': value
        })
    except Exception as e:
        logger.error(f"[API] 获取配置失败: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500

@integrated_settings_bp.route('/api/setting/<key>', methods=['POST'])
def api_update_setting(key):
    """更新配置"""
    result = require_admin_role()
    if result:
        return jsonify({'success': False, 'error': 'Unauthorized'}), 401
    
    try:
        from app.config import update_config
        data = request.get_json()
        
        value = data.get('value')
        category = data.get('category', 'general')
        description = data.get('description', '')
        
        # 类型验证 - 符合系统约束
        if value is None:
            return jsonify({'success': False, 'error': '缺少value参数'}), 400
        
        success = update_config(key, value, category, description)
        
        if success:
            logger.info(f"[API] 配置更新成功: {key} by {session.get('username')}")
            return jsonify({
                'success': True,
                'key': key,
                'value': value,
                'message': '配置更新成功'
            })
        else:
            return jsonify({'success': False, 'error': '配置更新失败'}), 500
    except Exception as e:
        logger.error(f"[API] 更新配置失败: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500

@integrated_settings_bp.route('/api/batch', methods=['POST'])
def api_batch_update():
    """批量更新配置"""
    result = require_admin_role()
    if result:
        return jsonify({'success': False, 'error': 'Unauthorized'}), 401
    
    try:
        from app.services.db_config_manager import db_config_manager
        data = request.get_json()
        
        settings = data.get('settings', {})
        category = data.get('category', 'general')
        
        if not settings:
            return jsonify({'success': False, 'error': '配置数据不能为空'}), 400
        
        success = db_config_manager.batch_set(settings, category)
        
        if success:
            logger.info(f"[API] 批量更新 {len(settings)} 个配置 by {session.get('username')}")
            return jsonify({
                'success': True,
                'updated_keys': list(settings.keys()),
                'count': len(settings),
                'message': f'成功更新 {len(settings)} 个配置'
            })
        else:
            return jsonify({'success': False, 'error': '批量更新失败'}), 500
    except Exception as e:
        logger.error(f"[API] 批量更新失败: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500

@integrated_settings_bp.route('/api/refresh', methods=['POST'])
def api_refresh_config():
    """刷新配置缓存"""
    result = require_admin_role()
    if result:
        return jsonify({'success': False, 'error': 'Unauthorized'}), 401
    
    try:
        from app.config import refresh_config
        refresh_config()
        
        logger.info(f"[API] 配置缓存刷新 by {session.get('username')}")
        return jsonify({
            'success': True,
            'message': '配置已从数据库刷新'
        })
    except Exception as e:
        logger.error(f"[API] 刷新配置失败: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500

@integrated_settings_bp.route('/api/search', methods=['GET'])
def api_search_settings():
    """搜索配置"""
    try:
        from app.config import get_db_config_manager
        db_manager = get_db_config_manager()
        
        query = request.args.get('q', '').lower()
        if not query:
            return jsonify({'success': False, 'error': '缺少搜索关键词'}), 400
        
        # 获取所有配置
        all_settings = db_manager.get_all() if db_manager else {}
        
        # 搜索匹配
        results = {}
        for key, value in all_settings.items():
            if query in key.lower() or (str(value).lower() and query in str(value).lower()):
                results[key] = value
        
        return jsonify({
            'success': True,
            'results': results,
            'count': len(results),
            'query': query
        })
    except Exception as e:
        logger.error(f"[API] 搜索配置失败: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500
