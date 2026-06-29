# -*- coding: utf-8 -*-
"""
发布管理API - 灰度发布系统RESTful接口
提供发布计划管理、灰度控制、回滚操作、健康检查等接口
"""
from flask import Blueprint, request, jsonify
import logging
import time

logger = logging.getLogger(__name__)

release_api = Blueprint('release_api', __name__, url_prefix='/api/release')


def get_release_manager():
    """获取灰度发布管理器"""
    try:
        from app.agents.gray_release_manager import get_release_manager
        return get_release_manager()
    except Exception as e:
        logger.error(f"获取灰度发布管理器失败: {e}")
        return None


@release_api.route('/plan', methods=['POST'])
def create_release_plan():
    """创建发布计划"""
    try:
        data = request.get_json() or {}
        version = data.get('version', '')
        description = data.get('description', '')
        strategy = data.get('strategy', 'percentage')
        commit_hash = data.get('commit_hash', '')
        
        if not version:
            return jsonify({'success': False, 'error': '版本号不能为空'}), 400
        
        manager = get_release_manager()
        if not manager:
            return jsonify({'success': False, 'error': '灰度发布管理器未初始化'}), 500
        
        release_id = manager.create_release(version, description, strategy, commit_hash)
        
        return jsonify({
            'success': True,
            'release_id': release_id,
            'version': version,
            'message': '发布计划创建成功'
        })
    
    except Exception as e:
        logger.error(f"创建发布计划失败: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@release_api.route('/plan/<release_id>', methods=['GET'])
def get_release_plan(release_id):
    """获取发布计划详情"""
    try:
        manager = get_release_manager()
        if not manager:
            return jsonify({'success': False, 'error': '灰度发布管理器未初始化'}), 500
        
        release = manager.get_release_status(release_id)
        if not release:
            return jsonify({'success': False, 'error': '发布计划不存在'}), 404
        
        return jsonify({
            'success': True,
            'release': release
        })
    
    except Exception as e:
        logger.error(f"获取发布计划失败: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@release_api.route('/plans', methods=['GET'])
def get_release_plans():
    """获取所有发布计划"""
    try:
        manager = get_release_manager()
        if not manager:
            return jsonify({'success': False, 'error': '灰度发布管理器未初始化'}), 500
        
        limit = int(request.args.get('limit', 20))
        releases = manager.get_release_history(limit)
        
        return jsonify({
            'success': True,
            'releases': releases,
            'total': len(releases)
        })
    
    except Exception as e:
        logger.error(f"获取发布计划列表失败: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@release_api.route('/start/<release_id>', methods=['POST'])
def start_release(release_id):
    """开始发布"""
    try:
        manager = get_release_manager()
        if not manager:
            return jsonify({'success': False, 'error': '灰度发布管理器未初始化'}), 500
        
        success = manager.start_release(release_id)
        
        if not success:
            return jsonify({'success': False, 'error': '开始发布失败'}), 400
        
        release = manager.get_release_status(release_id)
        
        return jsonify({
            'success': True,
            'release_id': release_id,
            'status': release['status'],
            'message': '发布已开始'
        })
    
    except Exception as e:
        logger.error(f"开始发布失败: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@release_api.route('/gray/<release_id>', methods=['POST'])
def set_gray_percentage(release_id):
    """设置灰度比例"""
    try:
        data = request.get_json() or {}
        percentage = data.get('percentage', 0)
        
        if percentage < 0 or percentage > 100:
            return jsonify({'success': False, 'error': '灰度比例必须在0-100之间'}), 400
        
        manager = get_release_manager()
        if not manager:
            return jsonify({'success': False, 'error': '灰度发布管理器未初始化'}), 500
        
        success = manager.set_gray_percentage(release_id, percentage)
        
        if not success:
            return jsonify({'success': False, 'error': '设置灰度比例失败'}), 400
        
        release = manager.get_release_status(release_id)
        
        return jsonify({
            'success': True,
            'release_id': release_id,
            'gray_percentage': percentage,
            'status': release['status'],
            'message': f'灰度比例已设置为 {percentage}%'
        })
    
    except Exception as e:
        logger.error(f"设置灰度比例失败: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@release_api.route('/gray/users/<release_id>', methods=['POST'])
def add_gray_users(release_id):
    """添加灰度用户"""
    try:
        data = request.get_json() or {}
        users = data.get('users', [])
        
        if not users:
            return jsonify({'success': False, 'error': '用户列表不能为空'}), 400
        
        manager = get_release_manager()
        if not manager:
            return jsonify({'success': False, 'error': '灰度发布管理器未初始化'}), 500
        
        success = manager.add_gray_users(release_id, users)
        
        if not success:
            return jsonify({'success': False, 'error': '添加灰度用户失败'}), 400
        
        release = manager.get_release_status(release_id)
        
        return jsonify({
            'success': True,
            'release_id': release_id,
            'gray_users_count': len(release['gray_users']),
            'message': f'已添加 {len(users)} 个灰度用户'
        })
    
    except Exception as e:
        logger.error(f"添加灰度用户失败: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@release_api.route('/gray/ips/<release_id>', methods=['POST'])
def add_gray_ips(release_id):
    """添加灰度IP"""
    try:
        data = request.get_json() or {}
        ips = data.get('ips', [])
        
        if not ips:
            return jsonify({'success': False, 'error': 'IP列表不能为空'}), 400
        
        manager = get_release_manager()
        if not manager:
            return jsonify({'success': False, 'error': '灰度发布管理器未初始化'}), 500
        
        success = manager.add_gray_ips(release_id, ips)
        
        if not success:
            return jsonify({'success': False, 'error': '添加灰度IP失败'}), 400
        
        release = manager.get_release_status(release_id)
        
        return jsonify({
            'success': True,
            'release_id': release_id,
            'gray_ips_count': len(release['gray_ips']),
            'message': f'已添加 {len(ips)} 个灰度IP'
        })
    
    except Exception as e:
        logger.error(f"添加灰度IP失败: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@release_api.route('/full/<release_id>', methods=['POST'])
def full_release(release_id):
    """全量发布"""
    try:
        manager = get_release_manager()
        if not manager:
            return jsonify({'success': False, 'error': '灰度发布管理器未初始化'}), 500
        
        success = manager.full_release(release_id)
        
        if not success:
            return jsonify({'success': False, 'error': '全量发布失败'}), 400
        
        release = manager.get_release_status(release_id)
        
        return jsonify({
            'success': True,
            'release_id': release_id,
            'status': release['status'],
            'gray_percentage': 100,
            'message': '全量发布已执行'
        })
    
    except Exception as e:
        logger.error(f"全量发布失败: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@release_api.route('/complete/<release_id>', methods=['POST'])
def complete_release(release_id):
    """完成发布"""
    try:
        manager = get_release_manager()
        if not manager:
            return jsonify({'success': False, 'error': '灰度发布管理器未初始化'}), 500
        
        success = manager.complete_release(release_id)
        
        if not success:
            return jsonify({'success': False, 'error': '完成发布失败'}), 400
        
        release = manager.get_release_status(release_id)
        
        return jsonify({
            'success': True,
            'release_id': release_id,
            'status': release['status'],
            'completed_at': release['completed_at'],
            'message': '发布已完成'
        })
    
    except Exception as e:
        logger.error(f"完成发布失败: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@release_api.route('/rollback/<release_id>', methods=['POST'])
def rollback_release(release_id):
    """回滚发布"""
    try:
        data = request.get_json() or {}
        reason = data.get('reason', '手动回滚')
        
        manager = get_release_manager()
        if not manager:
            return jsonify({'success': False, 'error': '灰度发布管理器未初始化'}), 500
        
        success = manager.rollback(release_id, reason)
        
        if not success:
            return jsonify({'success': False, 'error': '回滚失败'}), 400
        
        release = manager.get_release_status(release_id)
        
        return jsonify({
            'success': True,
            'release_id': release_id,
            'status': release['status'],
            'rollback_reason': release['rollback_reason'],
            'rolled_back_at': release['rolled_back_at'],
            'message': '回滚已执行'
        })
    
    except Exception as e:
        logger.error(f"回滚失败: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@release_api.route('/current', methods=['GET'])
def get_current_release():
    """获取当前进行中的发布"""
    try:
        manager = get_release_manager()
        if not manager:
            return jsonify({'success': False, 'error': '灰度发布管理器未初始化'}), 500
        
        release = manager.get_current_release()
        
        return jsonify({
            'success': True,
            'release': release
        })
    
    except Exception as e:
        logger.error(f"获取当前发布失败: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@release_api.route('/gray/percentage', methods=['GET'])
def get_gray_percentage():
    """获取当前灰度比例"""
    try:
        manager = get_release_manager()
        if not manager:
            return jsonify({'success': False, 'error': '灰度发布管理器未初始化'}), 500
        
        percentage = manager.get_gray_percentage()
        
        return jsonify({
            'success': True,
            'gray_percentage': percentage
        })
    
    except Exception as e:
        logger.error(f"获取灰度比例失败: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@release_api.route('/health', methods=['GET'])
def get_health_status():
    """获取健康状态"""
    try:
        manager = get_release_manager()
        if not manager:
            return jsonify({'success': False, 'error': '灰度发布管理器未初始化'}), 500
        
        health = manager.get_health_status()
        
        return jsonify({
            'success': True,
            'health': health
        })
    
    except Exception as e:
        logger.error(f"获取健康状态失败: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@release_api.route('/is-gray', methods=['GET'])
def check_is_gray():
    """检查当前请求是否为灰度流量"""
    try:
        user_id = request.args.get('user_id')
        ip = request.remote_addr
        
        manager = get_release_manager()
        if not manager:
            return jsonify({'success': False, 'error': '灰度发布管理器未初始化'}), 500
        
        is_gray = manager.is_gray_user(user_id, ip)
        
        return jsonify({
            'success': True,
            'is_gray': is_gray,
            'user_id': user_id,
            'ip': ip,
            'current_percentage': manager.get_gray_percentage()
        })
    
    except Exception as e:
        logger.error(f"检查灰度状态失败: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@release_api.route('/auto-release', methods=['POST'])
def auto_release():
    """自动灰度发布流程"""
    try:
        data = request.get_json() or {}
        version = data.get('version', '')
        description = data.get('description', '')
        steps = data.get('steps', [
            {'percentage': 10, 'duration': 60},
            {'percentage': 30, 'duration': 60},
            {'percentage': 50, 'duration': 60},
            {'percentage': 100, 'duration': 30}
        ])
        
        if not version:
            return jsonify({'success': False, 'error': '版本号不能为空'}), 400
        
        manager = get_release_manager()
        if not manager:
            return jsonify({'success': False, 'error': '灰度发布管理器未初始化'}), 500
        
        release_id = manager.create_release(version, description)
        manager.start_release(release_id)
        
        import threading
        
        def auto_release_worker():
            import time
            try:
                for step in steps:
                    percentage = step['percentage']
                    duration = step['duration']
                    
                    logger.info(f"[自动发布] 设置灰度比例: {percentage}%")
                    manager.set_gray_percentage(release_id, percentage)
                    
                    health = manager.get_health_status()
                    if health['status'] != 'healthy':
                        logger.error(f"[自动发布] 健康检查失败，触发回滚")
                        manager.rollback(release_id, reason='健康检查失败')
                        return
                    
                    logger.info(f"[自动发布] 等待 {duration} 秒...")
                    time.sleep(duration)
                
                manager.full_release(release_id)
                manager.complete_release(release_id)
                logger.info(f"[自动发布] 发布完成: {release_id}")
                
            except Exception as e:
                logger.error(f"[自动发布] 自动发布失败: {e}")
                manager.rollback(release_id, reason=f'自动发布异常: {str(e)}')
        
        thread = threading.Thread(target=auto_release_worker, daemon=True)
        thread.start()
        
        return jsonify({
            'success': True,
            'release_id': release_id,
            'version': version,
            'steps': steps,
            'message': '自动灰度发布已启动'
        })
    
    except Exception as e:
        logger.error(f"启动自动发布失败: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@release_api.route('/preview/<release_id>', methods=['GET'])
def preview_release(release_id):
    """预览发布影响范围"""
    try:
        manager = get_release_manager()
        if not manager:
            return jsonify({'success': False, 'error': '灰度发布管理器未初始化'}), 500
        
        release = manager.get_release_status(release_id)
        if not release:
            return jsonify({'success': False, 'error': '发布计划不存在'}), 404
        
        preview = {
            'release_id': release_id,
            'version': release['version'],
            'strategy': release['strategy'],
            'estimated_impact': {
                'percentage': release['gray_percentage'],
                'users': len(release['gray_users']),
                'ips': len(release['gray_ips'])
            },
            'risk_level': 'low' if release['gray_percentage'] <= 30 else 'medium' if release['gray_percentage'] <= 70 else 'high',
            'rollback_available': release['status'] in ['gray', 'full'],
            'previous_version': release['previous_version']
        }
        
        return jsonify({
            'success': True,
            'preview': preview
        })
    
    except Exception as e:
        logger.error(f"预览发布影响失败: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500