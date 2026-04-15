import uuid
from datetime import datetime, timedelta
from flask import session, request
from app.utils.logging import logger
from app.utils.db import db_manager

class SessionManager:
    """会话管理器，用于处理多设备同时登录"""
    
    @staticmethod
    def create_session(user_id, username, login_type='password', device_info=None, expires_at=None, remember=False):
        """创建新会话"""
        try:
            # 检查设备限制
            if not SessionManager.check_device_limit(user_id):
                logger.warning(f"用户 {username} 设备数量已达上限")
                return False, "设备数量已达上限"
            
            # 生成唯一会话ID
            session_id = str(uuid.uuid4())
            
            # 获取IP地址和用户代理
            ip_address = request.remote_addr if request else 'unknown'
            user_agent = request.user_agent.string if request else 'unknown'
            
            # 设置过期时间
            if not expires_at:
                if remember:
                    # 如果用户选择记住我，设置30天过期
                    expires_at = (datetime.now() + timedelta(days=30)).strftime('%Y-%m-%d %H:%M:%S')
                else:
                    # 默认24小时过期
                    expires_at = (datetime.now() + timedelta(hours=24)).strftime('%Y-%m-%d %H:%M:%S')
            else:
                expires_at = expires_at.strftime('%Y-%m-%d %H:%M:%S')
            
            # 保存会话到数据库
            db_manager.execute(
                'INSERT INTO user_sessions (session_id, user_id, username, ip_address, user_agent, device_info, expires_at, login_type) VALUES (?, ?, ?, ?, ?, ?, ?, ?)',
                (session_id, user_id, username, ip_address, user_agent, device_info, expires_at, login_type)
            )
            
            # 设置当前会话
            session['session_id'] = session_id
            session['user_id'] = user_id
            session['username'] = username
            session['login_type'] = login_type
            
            logger.info(f"为用户 {username} 创建新会话: {session_id[:10]}...，登录类型: {login_type}")
            return True, session_id
        except Exception as e:
            logger.error(f"创建会话失败: {str(e)}")
            return False, f"创建会话失败: {str(e)}"
    
    @staticmethod
    def check_device_limit(user_id):
        """检查用户设备数量是否超过限制"""
        try:
            # 获取用户的设备限制
            limit_data = db_manager.fetch_one(
                'SELECT max_devices FROM user_device_limits WHERE user_id = ?',
                (user_id,)
            )
            
            max_devices = limit_data[0] if limit_data else 5  # 默认允许5个设备
            
            # 获取当前活跃会话数量
            active_sessions = db_manager.fetch_one(
                'SELECT COUNT(*) FROM user_sessions WHERE user_id = ? AND is_active = 1',
                (user_id,)
            )
            
            current_devices = active_sessions[0] if active_sessions else 0
            
            return current_devices < max_devices
        except Exception as e:
            logger.error(f"检查设备限制失败: {str(e)}")
            return True  # 出现错误时允许登录
    
    @staticmethod
    def get_user_sessions(user_id):
        """获取用户的所有会话"""
        try:
            sessions = db_manager.fetch_all(
                'SELECT session_id, ip_address, user_agent, device_info, is_active, created_at, updated_at, last_activity, expires_at, login_type FROM user_sessions WHERE user_id = ? ORDER BY last_activity DESC',
                (user_id,)
            )
            
            return [{
                'session_id': session[0],
                'ip_address': session[1],
                'user_agent': session[2],
                'device_info': session[3],
                'is_active': session[4],
                'created_at': session[5],
                'updated_at': session[6],
                'last_activity': session[7],
                'expires_at': session[8],
                'login_type': session[9]
            } for session in sessions]
        except Exception as e:
            logger.error(f"获取用户会话失败: {str(e)}")
            return []
    
    @staticmethod
    def update_session_activity(session_id):
        """更新会话活动时间"""
        try:
            # 更新会话的最后活动时间
            db_manager.execute(
                'UPDATE user_sessions SET last_activity = CURRENT_TIMESTAMP WHERE session_id = ?',
                (session_id,)
            )
            return True
        except Exception as e:
            logger.error(f"更新会话活动时间失败: {str(e)}")
            return False
    
    @staticmethod
    def invalidate_session(session_id):
        """使会话失效"""
        try:
            # 使会话失效
            db_manager.execute(
                'UPDATE user_sessions SET is_active = 0 WHERE session_id = ?',
                (session_id,)
            )
            logger.info(f"会话已失效: {session_id[:10]}...")
            return True
        except Exception as e:
            logger.error(f"使会话失效失败: {str(e)}")
            return False
    
    @staticmethod
    def invalidate_all_user_sessions(user_id):
        """使用户的所有会话失效"""
        try:
            # 使所有会话失效
            db_manager.execute(
                'UPDATE user_sessions SET is_active = 0 WHERE user_id = ?',
                (user_id,)
            )
            logger.info(f"用户 {user_id} 的所有会话已失效")
            return True
        except Exception as e:
            logger.error(f"使用户所有会话失效失败: {str(e)}")
            return False
    
    @staticmethod
    def validate_session(session_id):
        """验证会话是否有效"""
        try:
            # 查询会话
            session_data = db_manager.fetch_one(
                'SELECT is_active, expires_at FROM user_sessions WHERE session_id = ?',
                (session_id,)
            )
            
            if not session_data:
                logger.warning(f"会话不存在: {session_id[:10]}...")
                return False, "会话不存在"
            
            is_active, expires_at = session_data
            
            # 检查会话是否激活
            if not is_active:
                logger.warning(f"会话已失效: {session_id[:10]}...")
                return False, "会话已失效"
            
            # 检查会话是否过期
            if datetime.now() > datetime.strptime(expires_at, '%Y-%m-%d %H:%M:%S'):
                logger.warning(f"会话已过期: {session_id[:10]}...")
                # 自动使过期会话失效
                SessionManager.invalidate_session(session_id)
                return False, "会话已过期"
            
            # 更新会话活动时间
            SessionManager.update_session_activity(session_id)
            
            logger.info(f"会话验证成功: {session_id[:10]}...")
            return True, "会话有效"
        except Exception as e:
            logger.error(f"验证会话失败: {str(e)}")
            return False, f"验证会话失败: {str(e)}"
    
    @staticmethod
    def cleanup_expired_sessions():
        """清理过期会话"""
        try:
            # 获取当前时间
            current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            
            # 清理过期会话
            result = db_manager.execute(
                'UPDATE user_sessions SET is_active = 0 WHERE expires_at < ? AND is_active = 1',
                (current_time,)
            )
            
            logger.info(f"清理过期会话完成，影响 {result.rowcount} 个会话")
            return True
        except Exception as e:
            logger.error(f"清理过期会话失败: {str(e)}")
            return False
    
    @staticmethod
    def set_device_limit(user_id, max_devices):
        """设置用户设备限制"""
        try:
            # 检查是否已存在
            existing = db_manager.fetch_one(
                'SELECT id FROM user_device_limits WHERE user_id = ?',
                (user_id,)
            )
            
            if existing:
                # 更新现有限制
                db_manager.execute(
                    'UPDATE user_device_limits SET max_devices = ? WHERE user_id = ?',
                    (max_devices, user_id)
                )
            else:
                # 添加新限制
                db_manager.execute(
                    'INSERT INTO user_device_limits (user_id, max_devices) VALUES (?, ?)',
                    (user_id, max_devices)
                )
            
            logger.info(f"设置用户 {user_id} 的设备限制为 {max_devices}")
            return True
        except Exception as e:
            logger.error(f"设置设备限制失败: {str(e)}")
            return False
    
    @staticmethod
    def get_device_limit(user_id):
        """获取用户设备限制"""
        try:
            # 获取用户的设备限制
            limit_data = db_manager.fetch_one(
                'SELECT max_devices FROM user_device_limits WHERE user_id = ?',
                (user_id,)
            )
            
            return limit_data[0] if limit_data else 5  # 默认允许5个设备
        except Exception as e:
            logger.error(f"获取设备限制失败: {str(e)}")
            return 5  # 默认允许5个设备
    
    @staticmethod
    def get_active_session_count(user_id):
        """获取用户活跃会话数量"""
        try:
            # 获取当前活跃会话数量
            active_sessions = db_manager.fetch_one(
                'SELECT COUNT(*) FROM user_sessions WHERE user_id = ? AND is_active = 1',
                (user_id,)
            )
            
            return active_sessions[0] if active_sessions else 0
        except Exception as e:
            logger.error(f"获取活跃会话数量失败: {str(e)}")
            return 0
    
    @staticmethod
    def update_session_data(session_id, **kwargs):
        """更新会话数据"""
        try:
            # 构建更新语句
            update_fields = []
            params = []
            
            for key, value in kwargs.items():
                update_fields.append(f"{key} = ?")
                params.append(value)
            
            if not update_fields:
                return True
            
            params.append(session_id)
            query = f'UPDATE user_sessions SET {", ".join(update_fields)}, updated_at = CURRENT_TIMESTAMP WHERE session_id = ?'
            
            db_manager.execute(query, params)
            logger.info(f"更新会话数据: {session_id[:10]}...")
            return True
        except Exception as e:
            logger.error(f"更新会话数据失败: {str(e)}")
            return False

# 初始化会话管理器
session_manager = SessionManager()
