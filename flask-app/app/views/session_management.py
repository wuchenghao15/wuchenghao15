from app.utils.security import security_utils
from app.utils.logging import logger
from app.utils.session_manager import session_manager

# 创建蓝图
session_management_bp = Blueprint('session_management', __name__)

@session_management_bp.route('/sessions')
@security_utils.login_required
def manage_sessions():
    """管理会话页面"""
    try:
        user_id = session.get('user_id')
        username = session.get('username')
        
        # 获取用户的所有会话
        sessions = session_manager.get_user_sessions(user_id)
        
        # 获取当前会话ID
        current_session_id = session.get('session_id')
        
        # 获取用户设备限制
        device_limit = session_manager.get_device_limit(user_id)
        
        return render_template('session_management.html', 
                             sessions=sessions, 
                             current_session_id=current_session_id,
                             device_limit=device_limit,
                             username=username)
    except Exception as e:
        logger.error(f"获取会话列表失败: {str(e)}")
        flash('获取会话列表失败', 'danger')
        return redirect(url_for('main.index'))

@session_management_bp.route('/session/<session_id>/invalidate', methods=['POST'])
@security_utils.login_required
def invalidate_session(session_id):
    """使特定会话失效"""
    try:
        # 获取当前用户ID
        user_id = session.get('user_id')
        username = session.get('username')
        
        # 验证会话是否属于当前用户
        sessions = session_manager.get_user_sessions(user_id)
        session_found = any(s['session_id'] == session_id for s in sessions)
        
        if not session_found:
            flash('会话不存在或不属于当前用户', 'danger')
            return redirect(url_for('session_management.manage_sessions'))
        
        # 使会话失效
        if session_manager.invalidate_session(session_id):
            logger.info(f"用户 {username} 使会话 {session_id[:10]}... 失效")
            flash('会话已失效', 'success')
        else:
            flash('使会话失效失败', 'danger')
            
    except Exception as e:
        logger.error(f"使会话失效失败: {str(e)}")
        flash(f'操作失败: {str(e)}', 'danger')
    
    return redirect(url_for('session_management.manage_sessions'))

@session_management_bp.route('/sessions/invalidate_all', methods=['POST'])
@security_utils.login_required
def invalidate_all_sessions():
    """使所有会话失效"""
    try:
        # 获取当前用户ID
        user_id = session.get('user_id')
        username = session.get('username')
        
        # 使所有会话失效
        if session_manager.invalidate_all_user_sessions(user_id):
            logger.info(f"用户 {username} 使所有会话失效")
            # 清除当前会话
            session.clear()
            flash('所有会话已失效，请重新登录', 'success')
            return redirect(url_for('main.index'))
        else:
            flash('使所有会话失效失败', 'danger')
            
    except Exception as e:
        logger.error(f"使所有会话失效失败: {str(e)}")
        flash(f'操作失败: {str(e)}', 'danger')
    
    return redirect(url_for('session_management.manage_sessions'))

@session_management_bp.route('/api/sessions', methods=['GET'])
@security_utils.login_required
def get_sessions_api():
    """获取会话列表的API端点"""
    try:
        user_id = session.get('user_id')
        
        # 获取用户的所有会话
        sessions = session_manager.get_user_sessions(user_id)
        
        return jsonify({
            'success': True,
            'sessions': sessions
        })
    except Exception as e:
        logger.error(f"获取会话列表API失败: {str(e)}")
        return jsonify({
            'success': False,
            'message': f'获取会话列表失败: {str(e)}'
        }), 500

@session_management_bp.route('/api/session/<session_id>/invalidate', methods=['POST'])
@security_utils.login_required
def invalidate_session_api(session_id):
    """使特定会话失效的API端点"""
    try:
        # 获取当前用户ID
        user_id = session.get('user_id')
        
        # 验证会话是否属于当前用户
        sessions = session_manager.get_user_sessions(user_id)
        session_found = any(s['session_id'] == session_id for s in sessions)
        
        if not session_found:
            return jsonify({
                'success': False,
                'message': '会话不存在或不属于当前用户'
            }), 403
        
        # 使会话失效
        if session_manager.invalidate_session(session_id):
            return jsonify({
                'success': True,
                'message': '会话已失效'
            })
        else:
            return jsonify({
                'success': False,
                'message': '使会话失效失败'
            }), 500
            
    except Exception as e:
        logger.error(f"使会话失效API失败: {str(e)}")
        return jsonify({
            'success': False,
            'message': f'操作失败: {str(e)}'
        }), 500

@session_management_bp.route('/api/sessions/invalidate_all', methods=['POST'])
@security_utils.login_required
def invalidate_all_sessions_api():
    """使所有会话失效的API端点"""
    try:
        # 获取当前用户ID
        user_id = session.get('user_id')
        
        # 使所有会话失效
        if session_manager.invalidate_all_user_sessions(user_id):
            return jsonify({
                'success': True,
                'message': '所有会话已失效，请重新登录'
            })
        else:
            return jsonify({
                'success': False,
                'message': '使所有会话失效失败'
            }), 500
            
    except Exception as e:
        logger.error(f"使所有会话失效API失败: {str(e)}")
        return jsonify({
            'success': False,
            'message': f'操作失败: {str(e)}'
        }), 500
