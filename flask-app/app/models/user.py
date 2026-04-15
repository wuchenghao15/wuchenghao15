from app.utils.logging import logger
from app.services.user_management_client import get_user_management_client

class User:
    """用户数据模型"""
    
    def __init__(self, user_id=None, username=None, email=None, password=None, role="user", created_at=None, updated_at=None, is_active=1, super_admin_approved=0, hardware_admin_approved=0, avatar=None, reset_token=None, reset_token_expiry=None, password_modified_at=None, password_modified_by=None, phone=None):
        self.user_id = user_id
        self.username = username
        self.email = email
        self.password = password
        self.role = role
        self.created_at = created_at
        self.updated_at = updated_at
        self.is_active = is_active
        self.super_admin_approved = super_admin_approved
        self.hardware_admin_approved = hardware_admin_approved
        self.avatar = avatar
        self.reset_token = reset_token
        self.reset_token_expiry = reset_token_expiry
        self.password_modified_at = password_modified_at
        self.password_modified_by = password_modified_by
        self.phone = phone
    
    def get_verification_info(self, verification_type=None):
        """获取用户的验证信息"""
        try:
            from app.utils.db import db_manager
            
            if verification_type:
                # 获取特定类型的验证信息
                verification_data = db_manager.fetch_one(
                    'SELECT verification_value, is_active FROM user_verification WHERE user_id = ? AND verification_type = ?',
                    (self.user_id, verification_type)
                )
                if verification_data:
                    return {
                        'verification_type': verification_type,
                        'verification_value': verification_data[0],
                        'is_active': verification_data[1]
                    }
                return None
            else:
                # 获取所有验证信息
                verification_data = db_manager.fetch_all(
                    'SELECT verification_type, verification_value, is_active FROM user_verification WHERE user_id = ?',
                    (self.user_id,)
                )
                return [{
                    'verification_type': item[0],
                    'verification_value': item[1],
                    'is_active': item[2]
                } for item in verification_data]
        except Exception as e:
            logger.error(f"获取用户验证信息失败: {str(e)}")
            return []
    
    def save_verification_info(self, verification_type, verification_value):
        """保存用户的验证信息"""
        try:
            from app.utils.db import db_manager
            
            # 检查是否已存在该类型的验证信息
            existing = db_manager.fetch_one(
                'SELECT id FROM user_verification WHERE user_id = ? AND verification_type = ?',
                (self.user_id, verification_type)
            )
            
            if existing:
                # 更新现有验证信息
                db_manager.execute(
                    'UPDATE user_verification SET verification_value = ?, updated_at = CURRENT_TIMESTAMP WHERE user_id = ? AND verification_type = ?',
                    (verification_value, self.user_id, verification_type)
                )
                logger.info(f"更新用户验证信息: {self.username}, 类型: {verification_type}")
            else:
                # 插入新的验证信息
                db_manager.execute(
                    'INSERT INTO user_verification (user_id, username, verification_type, verification_value) VALUES (?, ?, ?, ?)',
                    (self.user_id, self.username, verification_type, verification_value)
                )
                logger.info(f"保存用户验证信息: {self.username}, 类型: {verification_type}")
            return True
        except Exception as e:
            logger.error(f"保存用户验证信息失败: {str(e)}")
            return False
    
    def delete_verification_info(self, verification_type):
        """删除用户的验证信息"""
        try:
            from app.utils.db import db_manager
            
            db_manager.execute(
                'DELETE FROM user_verification WHERE user_id = ? AND verification_type = ?',
                (self.user_id, verification_type)
            )
            logger.info(f"删除用户验证信息: {self.username}, 类型: {verification_type}")
            return True
        except Exception as e:
            logger.error(f"删除用户验证信息失败: {str(e)}")
            return False
    
    @staticmethod
    def create_table():
        """创建用户表 - 调用远程服务"""
        try:
            client = get_user_management_client()
            # 调用健康检查接口，确保服务可用
            health_status = client.health_check()
            if health_status.get('success'):
                logger.info("用户管理服务健康状态正常")
            else:
                logger.error("用户管理服务健康检查失败")
        except Exception as e:
            logger.error(f"调用用户管理服务失败: {str(e)}")
    
    def save(self):
        """保存用户信息 - 使用直接的SQLite连接"""
        try:
            # 直接使用SQLite连接保存用户
            import sqlite3
            import os
            
            # 使用绝对路径连接数据库
            db_path = os.path.abspath('app.db')
            print(f"DEBUG: Connecting to database: {db_path}")
            
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            
            if self.user_id:
                # 更新现有用户
                print(f"DEBUG: Updating user: {self.username}")
                cursor.execute('''
                    UPDATE users SET 
                        username = ?, 
                        email = ?, 
                        password = ?, 
                        role = ?, 
                        is_active = ? 
                    WHERE id = ?
                ''', (
                    self.username, 
                    self.email, 
                    self.password, 
                    self.role, 
                    self.is_active, 
                    self.user_id
                ))
                conn.commit()
                logger.info(f"更新用户: {self.username}")
                conn.close()
                return self.user_id
            else:
                # 创建新用户
                print(f"DEBUG: Creating user: {self.username}")
                cursor.execute('''
                    INSERT INTO users (username, email, password, role, is_active)
                    VALUES (?, ?, ?, ?, ?)
                ''', (
                    self.username, 
                    self.email, 
                    self.password, 
                    self.role, 
                    self.is_active
                ))
                conn.commit()
                self.user_id = cursor.lastrowid
                logger.info(f"创建用户: {self.username}")
                conn.close()
                return self.user_id
        except Exception as e:
            logger.error(f"保存用户信息失败: {str(e)}")
            print(f"DEBUG: Error saving user: {e}")
            import traceback
            traceback.print_exc()
            return None
    
    @staticmethod
    def get_by_username(username):
        """通过用户名获取用户 - 使用统一的数据库管理器"""
        try:
            print(f"DEBUG: Starting get_by_username for: {username}")
            
            # 直接从users表中查询用户
            import sqlite3
            import os
            
            # 使用绝对路径连接数据库
            db_path = os.path.abspath('app.db')
            print(f"DEBUG: Connecting to database: {db_path}")
            
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            
            # 查询users表
            print(f"DEBUG: Querying users table for: {username}")
            cursor.execute('SELECT id, username, email, password, role, is_active FROM users WHERE username = ?', (username,))
            user_data = cursor.fetchone()
            
            if user_data:
                user_id, username, email, password, role, is_active = user_data
                print(f"DEBUG: Found user in users table: {username}, role: {role}, is_active: {is_active}")
                logger.info(f"数据库获取用户成功: {username}")
                conn.close()
                return User(
                    user_id=user_id,
                    username=username,
                    email=email,
                    password='',  # 不返回密码
                    role=role,
                    is_active=is_active,
                    super_admin_approved=1,
                    hardware_admin_approved=1
                )
            else:
                print(f"DEBUG: User not found in users table: {username}")
                conn.close()
                return None
        except Exception as e:
            logger.error(f"通过用户名获取用户失败: {str(e)}")
            print(f"DEBUG: Error getting user: {str(e)}")
            import traceback
            traceback.print_exc()
            return None
    
    @staticmethod
    def get_by_id(user_id):
        """通过用户ID获取用户 - 调用远程服务"""
        try:
            client = get_user_management_client()
            result = client.get_user(user_id)
            if result.get('success'):
                user_data = result.get('user')
                if user_data:
                    return User(
                        user_id=user_data.get('id'),
                        username=user_data.get('username'),
                        email=user_data.get('email'),
                        password='',  # 不返回密码
                        role=user_data.get('role'),
                        created_at=user_data.get('created_at'),
                        updated_at=user_data.get('created_at'),
                        is_active=user_data.get('is_active'),
                        super_admin_approved=0,
                        hardware_admin_approved=0,
                        avatar=user_data.get('avatar')
                    )
            return None
        except Exception as e:
            logger.error(f"通过用户ID获取用户失败: {str(e)}")
            return None
    
    @staticmethod
    def verify_credentials(username, password):
        """验证用户凭证 - 使用直接的SQLite连接"""
        try:
            print(f"DEBUG: Starting verify_credentials for: {username}")
            
            # 直接从users表中查询用户
            import sqlite3
            import os
            from app.utils.security import security_utils
            
            # 使用绝对路径连接数据库
            db_path = os.path.abspath('app.db')
            print(f"DEBUG: Connecting to database: {db_path}")
            
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            
            # 先尝试通过用户名查询用户
            print(f"DEBUG: Querying users table for username: {username}")
            cursor.execute('SELECT id, username, email, password, role, is_active, phone FROM users WHERE username = ?', (username,))
            user_data = cursor.fetchone()
            
            # 如果用户名不存在，尝试通过手机号查询用户
            if not user_data:
                print(f"DEBUG: Username not found, trying phone: {username}")
                cursor.execute('SELECT id, username, email, password, role, is_active, phone FROM users WHERE phone = ?', (username,))
                user_data = cursor.fetchone()
            
            if user_data:
                user_id, username, email, stored_password, role, is_active, phone = user_data
                print(f"DEBUG: Found user in users table: {username}, role: {role}, is_active: {is_active}")
                
                # 检查是否是明文密码，如果是则自动更新为哈希密码
                if len(stored_password) < 80:  # 简单判断，哈希密码通常较长
                    # 计算哈希密码
                    hashed_password = security_utils.hash_password(password)
                    # 更新数据库中的密码
                    cursor.execute('UPDATE users SET password = ? WHERE id = ?', (hashed_password, user_id))
                    conn.commit()
                    # 验证成功
                    conn.close()
                    return User(
                        user_id=user_id,
                        username=username,
                        email=email,
                        password='',  # 不存储密码
                        role=role,
                        is_active=is_active,
                        super_admin_approved=1,
                        hardware_admin_approved=1,
                        phone=phone
                    )
                else:
                    # 使用哈希密码验证
                    try:
                        if security_utils.verify_password(stored_password, password):
                            print(f"DEBUG: Hashed password match for: {username}")
                            logger.info(f"哈希密码验证成功: {username}")
                            conn.close()
                            return User(
                                user_id=user_id,
                                username=username,
                                email=email,
                                password='',  # 不存储密码
                                role=role,
                                is_active=is_active,
                                super_admin_approved=1,
                                hardware_admin_approved=1,
                                phone=phone
                            )
                        else:
                            print(f"DEBUG: Password mismatch for: {username}")
                            logger.warning(f"密码验证失败: {username}")
                            conn.close()
                            return None
                    except Exception as hash_error:
                        print(f"DEBUG: Hash verification error: {hash_error}")
                        # 如果哈希验证失败，返回None
                        conn.close()
                        return None
            else:
                print(f"DEBUG: User not found in users table: {username}")
                conn.close()
                return None
        except Exception as e:
            logger.error(f"验证用户凭证失败: {str(e)}")
            print(f"DEBUG: Error verifying credentials: {str(e)}")
            import traceback
            traceback.print_exc()
            return None
    
    def update_password(self, new_password):
        """更新用户密码 - 调用远程服务"""
        try:
            client = get_user_management_client()
            result = client.update_user(self.user_id, password=new_password)
            if result.get('success'):
                logger.info(f"更新用户密码: {self.username}")
                return True
            else:
                logger.error(f"更新用户密码失败: {result.get('error')}")
                return False
        except Exception as e:
            logger.error(f"更新用户密码失败: {str(e)}")
            return False
    
    def update_role(self, new_role):
        """更新用户角色 - 调用远程服务"""
        try:
            client = get_user_management_client()
            result = client.update_user(self.user_id, role=new_role)
            if result.get('success'):
                self.role = new_role
                logger.info(f"更新用户角色: {self.username} -> {new_role}")
                return True
            else:
                logger.error(f"更新用户角色失败: {result.get('error')}")
                return False
        except Exception as e:
            logger.error(f"更新用户角色失败: {str(e)}")
            return False
    
    @staticmethod
    def get_all_users():
        """获取所有用户 - 调用远程服务"""
        try:
            client = get_user_management_client()
            result = client.get_all_users()
            if result.get('success'):
                users = []
                for user_data in result.get('users', []):
                    users.append(User(
                        user_id=user_data.get('id'),
                        username=user_data.get('username'),
                        email=user_data.get('email'),
                        password='',  # 不返回密码
                        role=user_data.get('role'),
                        created_at=user_data.get('created_at'),
                        updated_at=user_data.get('created_at'),
                        is_active=user_data.get('is_active'),
                        super_admin_approved=0,
                        hardware_admin_approved=0,
                        avatar=user_data.get('avatar')
                    ))
                return users
            return []
        except Exception as e:
            logger.error(f"获取所有用户失败: {str(e)}")
            return []
    
    def delete(self):
        """删除用户 - 调用远程服务"""
        try:
            client = get_user_management_client()
            result = client.delete_user(self.user_id)
            if result.get('success'):
                logger.info(f"删除用户: {self.username}")
                return True
            else:
                logger.error(f"删除用户失败: {result.get('error')}")
                return False
        except Exception as e:
            logger.error(f"删除用户失败: {str(e)}")
            return False
    
    @staticmethod
    def get_by_email(email):
        """通过邮箱获取用户"""
        try:
            from app.utils.db import db_manager
            
            # 从数据库查询用户
            user_data = db_manager.fetch_one('SELECT id, username, email, password, role, is_active FROM users WHERE email = ?', (email,))
            
            if user_data:
                user_id, username, email, hashed_password, role, is_active = user_data
                logger.info(f"通过邮箱获取用户成功: {email}")
                return User(
                    user_id=user_id,
                    username=username,
                    email=email,
                    password='',  # 不返回密码
                    role=role,
                    is_active=is_active,
                    super_admin_approved=1,
                    hardware_admin_approved=1
                )
            return None
        except Exception as e:
            logger.error(f"通过邮箱获取用户失败: {str(e)}")
            return None
    
    @staticmethod
    def get_by_phone(phone):
        """通过手机号获取用户"""
        try:
            from app.utils.db import db_manager
            
            # 从数据库查询用户
            user_data = db_manager.fetch_one('SELECT id, username, email, password, role, is_active, phone FROM users WHERE phone = ?', (phone,))
            
            if user_data:
                user_id, username, email, hashed_password, role, is_active, phone = user_data
                logger.info(f"通过手机号获取用户成功: {phone}")
                return User(
                    user_id=user_id,
                    username=username,
                    email=email,
                    password='',  # 不返回密码
                    role=role,
                    is_active=is_active,
                    super_admin_approved=1,
                    hardware_admin_approved=1,
                    phone=phone
                )
            return None
        except Exception as e:
            logger.error(f"通过手机号获取用户失败: {str(e)}")
            return None
    
    @staticmethod
    def get_by_reset_token(token):
        """通过重置令牌获取用户"""
        try:
            from app.utils.db import db_manager
            
            # 从数据库查询用户
            user_data = db_manager.fetch_one('SELECT id, username, email, password, role, is_active, reset_token_expiry FROM users WHERE reset_token = ?', (token,))
            
            if user_data:
                user_id, username, email, hashed_password, role, is_active, reset_token_expiry = user_data
                logger.info(f"通过重置令牌获取用户成功: {username}")
                return User(
                    user_id=user_id,
                    username=username,
                    email=email,
                    password='',  # 不返回密码
                    role=role,
                    is_active=is_active,
                    super_admin_approved=1,
                    hardware_admin_approved=1,
                    reset_token=token,
                    reset_token_expiry=reset_token_expiry
                )
            return None
        except Exception as e:
            logger.error(f"通过重置令牌获取用户失败: {str(e)}")
            return None
    
    def update(self):
        """更新用户信息"""
        try:
            from app.utils.db import db_manager
            
            # 更新用户信息，包含密码字段
            db_manager.execute(
                'UPDATE users SET email = ?, password = ?, role = ?, is_active = ?, reset_token = ?, reset_token_expiry = ?, password_modified_at = ?, password_modified_by = ? WHERE id = ?',
                (self.email, self.password, self.role, self.is_active, self.reset_token, self.reset_token_expiry, self.password_modified_at, self.password_modified_by, self.user_id)
            )
            logger.info(f"更新用户信息: {self.username}")
            return True
        except Exception as e:
            logger.error(f"更新用户信息失败: {str(e)}")
            return False
    
    def add_password_history(self, password_hash):
        """添加密码历史记录"""
        try:
            from app.utils.db import db_manager
            
            db_manager.execute(
                'INSERT INTO password_history (user_id, password_hash) VALUES (?, ?)',
                (self.user_id, password_hash)
            )
            logger.info(f"添加密码历史记录: {self.username}")
            return True
        except Exception as e:
            logger.error(f"添加密码历史记录失败: {str(e)}")
            return False
    
    def get_password_history(self, limit=10):
        """获取密码历史记录"""
        try:
            from app.utils.db import db_manager
            
            history = db_manager.fetch_all(
                'SELECT id, password_hash, created_at FROM password_history WHERE user_id = ? ORDER BY created_at DESC LIMIT ?',
                (self.user_id, limit)
            )
            return history
        except Exception as e:
            logger.error(f"获取密码历史记录失败: {str(e)}")
            return []
    
    def is_password_used_before(self, password_hash):
        """检查密码是否在历史记录中使用过"""
        try:
            from app.utils.db import db_manager
            
            result = db_manager.fetch_one(
                'SELECT id FROM password_history WHERE user_id = ? AND password_hash = ?',
                (self.user_id, password_hash)
            )
            return result is not None
        except Exception as e:
            logger.error(f"检查密码历史失败: {str(e)}")
            return False
    
    @staticmethod
    def is_common_password(password):
        """检查是否为常用密码"""
        common_passwords = [
            'Password123', 'Qwerty123', '12345678', 'Admin123', 
            'Letmein123', 'Welcome123', 'Monkey123', 'Dragon123',
            'Password1!', 'Qwerty1!', '123456789', '12345678a',
            'Password2024', 'Password2025', 'Password2026'
        ]
        return password in common_passwords
