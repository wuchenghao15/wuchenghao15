import time, Blueprint

lock_bp = Blueprint('lock', __name__)

# 模拟用户活动时间存储
user_activity = {}
# 锁定设置
lock_settings = {
    'lock_mask_opacity': 0.8,
    'idle_timeout_minutes': 15,  # 15分钟无活动自动锁定
    'max_idle_time_minutes': 30  # 30分钟无活动自动退出
}

@lock_bp.route('/api/lock/settings', methods=['GET'])
def get_lock_settings():
    """获取锁定设置"""
    return jsonify({
        'success': True,
        'settings': lock_settings
    })

@lock_bp.route('/api/lock/check-status', methods=['GET'])
def check_lock_status():
    """检查用户锁定状态"""
    user_id = session.get('user_id', 'guest')
    current_time = time.time()
    
    # 检查用户是否有活动记录
    if user_id in user_activity:
        last_activity = user_activity[user_id]
        idle_time = (current_time - last_activity) / 60  # 转换为分钟
        
        # 检查是否超时
        if idle_time >= lock_settings['max_idle_time_minutes']:
            # 超时退出
            session.clear()
            return jsonify({
                'locked': False,
                'timeout': True
            })
        elif idle_time >= lock_settings['idle_timeout_minutes']:
            # 自动锁定
            return jsonify({
                'locked': True,
                'timeout': False
            })
    
    # 未锁定
    return jsonify({
        'locked': False,
        'timeout': False
    })

@lock_bp.route('/api/lock/update-activity', methods=['GET', 'POST'])
def update_activity():
    """更新用户活动时间"""
    user_id = session.get('user_id', 'guest')
    user_activity[user_id] = time.time()
    return jsonify({
        'success': True
    })

@lock_bp.route('/api/lock/unlock/password', methods=['POST'])
def unlock_with_password():
    """密码解锁"""
    data = request.get_json()
    password = data.get('password')
    
    # 简单的密码验证（实际项目中应该使用更安全的验证方式）
    if password == 'admin123':  # 示例密码
        user_id = session.get('user_id', 'guest')
        user_activity[user_id] = time.time()
        return jsonify({
            'success': True
        })
    else:
        return jsonify({
            'success': False,
            'message': '密码错误'
        })

@lock_bp.route('/api/lock/unlock/hardware', methods=['POST'])
def unlock_with_hardware():
    """硬件ID解锁"""
    data = request.get_json()
    vikey_id = data.get('vikey_id')
    
    # 简单的硬件ID验证（实际项目中应该使用更安全的验证方式）
    if vikey_id == '123456':  # 示例硬件ID
        user_id = session.get('user_id', 'guest')
        user_activity[user_id] = time.time()
        return jsonify({
            'success': True
        })
    else:
        return jsonify({
            'success': False,
            'message': '硬件ID错误'
        })
