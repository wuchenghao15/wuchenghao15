#!/usr/bin/env python3
"""
用户管理服务模块
负责用户管理和自动填充拓展功能
"""

import os
import sys
import sqlite3
import json
import time
from datetime import datetime

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

class UserManagerService:
    """用户管理服务类"""
    
    def __init__(self, db_path="app.db"):
        """初始化用户管理服务"""
        self.db_path = db_path
        self.conn = None
        self.cursor = None
        
        # 自动填充配置
        self.auto_fill_config = {
            "enabled": True,
            "fields": ["name", "email", "phone", "address", "company", "job_title"],
            "sync_with_browser": True,
            "auto_save": True
        }
    
    def connect(self):
        """连接数据库"""
        try:
            self.conn = sqlite3.connect(self.db_path)
            self.cursor = self.conn.cursor()
            return True
        except Exception as e:
            print(f"连接数据库失败: {str(e)}")
            return False
    
    def close(self):
        """关闭数据库连接"""
        if self.conn:
            self.conn.close()
    
    def get_user_profile(self, user_id):
        """获取用户个人信息"""
        if not self.connect():
            return None
        
        try:
            sql = """
            SELECT id, user_id, full_name, email, phone, address, company, job_title, 
                   birthday, avatar, preferences, created_at, updated_at
            FROM user_profiles
            WHERE user_id = ?
            """
            self.cursor.execute(sql, (user_id,))
            row = self.cursor.fetchone()
            
            if row:
                profile = {
                    "id": row[0],
                    "user_id": row[1],
                    "full_name": row[2],
                    "email": row[3],
                    "phone": row[4],
                    "address": row[5],
                    "company": row[6],
                    "job_title": row[7],
                    "birthday": row[8],
                    "avatar": row[9],
                    "preferences": json.loads(row[10]) if row[10] else {},
                    "created_at": row[11],
                    "updated_at": row[12]
                }
                return profile
            return None
        except Exception as e:
            print(f"获取用户个人信息失败: {str(e)}")
            return None
        finally:
            self.close()
    
    def update_user_profile(self, user_id, profile_data):
        """更新用户个人信息"""
        if not self.connect():
            return False
        
        try:
            # 检查用户是否存在
            existing_profile = self.get_user_profile(user_id)
            
            if existing_profile:
                # 更新现有信息
                sql = """
                UPDATE user_profiles
                SET full_name = ?, email = ?, phone = ?, address = ?, company = ?, 
                    job_title = ?, birthday = ?, avatar = ?, preferences = ?, updated_at = CURRENT_TIMESTAMP
                WHERE user_id = ?
                """
                params = (
                    profile_data.get("full_name"),
                    profile_data.get("email"),
                    profile_data.get("phone"),
                    profile_data.get("address"),
                    profile_data.get("company"),
                    profile_data.get("job_title"),
                    profile_data.get("birthday"),
                    profile_data.get("avatar"),
                    json.dumps(profile_data.get("preferences", {})),
                    user_id
                )
                self.cursor.execute(sql, params)
            else:
                # 创建新信息
                sql = """
                INSERT INTO user_profiles 
                (user_id, full_name, email, phone, address, company, job_title, 
                 birthday, avatar, preferences)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """
                params = (
                    user_id,
                    profile_data.get("full_name"),
                    profile_data.get("email"),
                    profile_data.get("phone"),
                    profile_data.get("address"),
                    profile_data.get("company"),
                    profile_data.get("job_title"),
                    profile_data.get("birthday"),
                    profile_data.get("avatar"),
                    json.dumps(profile_data.get("preferences", {}))
                )
                self.cursor.execute(sql, params)
            
            self.conn.commit()
            
            # 自动保存到自动填充数据
            if self.auto_fill_config["auto_save"]:
                self.save_auto_fill_data(user_id, profile_data)
            
            return True
        except Exception as e:
            print(f"更新用户个人信息失败: {str(e)}")
            return False
        finally:
            self.close()
    
    def save_auto_fill_data(self, user_id, data):
        """保存自动填充数据"""
        if not self.connect():
            return False
        
        try:
            for field_name, field_value in data.items():
                if field_name in self.auto_fill_config["fields"] and field_value:
                    # 检查是否已存在
                    sql = """
                    SELECT id, usage_count FROM auto_fill_data
                    WHERE user_id = ? AND field_name = ? AND field_value = ?
                    """
                    self.cursor.execute(sql, (user_id, field_name, field_value))
                    existing = self.cursor.fetchone()
                    
                    if existing:
                        # 更新使用次数
                        sql = """
                        UPDATE auto_fill_data
                        SET usage_count = usage_count + 1, last_used = CURRENT_TIMESTAMP, updated_at = CURRENT_TIMESTAMP
                        WHERE id = ?
                        """
                        self.cursor.execute(sql, (existing[0],))
                    else:
                        # 插入新数据
                        sql = """
                        INSERT INTO auto_fill_data (user_id, field_name, field_value, usage_count, last_used)
                        VALUES (?, ?, ?, 1, CURRENT_TIMESTAMP)
                        """
                        self.cursor.execute(sql, (user_id, field_name, field_value))
            
            self.conn.commit()
            return True
        except Exception as e:
            print(f"保存自动填充数据失败: {str(e)}")
            return False
        finally:
            self.close()
    
    def get_auto_fill_data(self, user_id, field_name=None):
        """获取自动填充数据"""
        if not self.connect():
            return []
        
        try:
            if field_name:
                sql = """
                SELECT field_name, field_value, usage_count, last_used
                FROM auto_fill_data
                WHERE user_id = ? AND field_name = ?
                ORDER BY usage_count DESC, last_used DESC
                """
                self.cursor.execute(sql, (user_id, field_name))
            else:
                sql = """
                SELECT field_name, field_value, usage_count, last_used
                FROM auto_fill_data
                WHERE user_id = ?
                ORDER BY field_name, usage_count DESC, last_used DESC
                """
                self.cursor.execute(sql, (user_id,))
            
            results = []
            for row in self.cursor.fetchall():
                result = {
                    "field_name": row[0],
                    "field_value": row[1],
                    "usage_count": row[2],
                    "last_used": row[3]
                }
                results.append(result)
            
            return results
        except Exception as e:
            print(f"获取自动填充数据失败: {str(e)}")
            return []
        finally:
            self.close()
    
    def get_user_preferences(self, user_id, category=None):
        """获取用户偏好设置"""
        if not self.connect():
            return {}
        
        try:
            if category:
                sql = """
                SELECT preference_key, preference_value
                FROM user_preferences
                WHERE user_id = ? AND category = ?
                """
                self.cursor.execute(sql, (user_id, category))
            else:
                sql = """
                SELECT preference_key, preference_value, category
                FROM user_preferences
                WHERE user_id = ?
                """
                self.cursor.execute(sql, (user_id,))
            
            preferences = {}
            for row in self.cursor.fetchall():
                if len(row) == 3:
                    key, value, cat = row
                    if cat not in preferences:
                        preferences[cat] = {}
                    preferences[cat][key] = value
                else:
                    key, value = row
                    preferences[key] = value
            
            return preferences
        except Exception as e:
            print(f"获取用户偏好设置失败: {str(e)}")
            return {}
        finally:
            self.close()
    
    def set_user_preference(self, user_id, preference_key, preference_value, category=None):
        """设置用户偏好设置"""
        if not self.connect():
            return False
        
        try:
            sql = """
            INSERT OR REPLACE INTO user_preferences 
            (user_id, preference_key, preference_value, category, updated_at)
            VALUES (?, ?, ?, ?, CURRENT_TIMESTAMP)
            """
            self.cursor.execute(sql, (user_id, preference_key, preference_value, category))
            self.conn.commit()
            return True
        except Exception as e:
            print(f"设置用户偏好设置失败: {str(e)}")
            return False
        finally:
            self.close()
    
    def record_user_behavior(self, user_id, action_type, action_data=None, ip_address=None, user_agent=None):
        """记录用户行为"""
        if not self.connect():
            return False
        
        try:
            sql = """
            INSERT INTO user_behavior (user_id, action_type, action_data, ip_address, user_agent)
            VALUES (?, ?, ?, ?, ?)
            """
            self.cursor.execute(sql, (
                user_id,
                action_type,
                json.dumps(action_data) if action_data else None,
                ip_address,
                user_agent
            ))
            self.conn.commit()
            return True
        except Exception as e:
            print(f"记录用户行为失败: {str(e)}")
            return False
        finally:
            self.close()
    
    def get_user_behavior(self, user_id, limit=50, offset=0):
        """获取用户行为记录"""
        if not self.connect():
            return []
        
        try:
            sql = """
            SELECT id, action_type, action_data, timestamp, ip_address, user_agent
            FROM user_behavior
            WHERE user_id = ?
            ORDER BY timestamp DESC
            LIMIT ? OFFSET ?
            """
            self.cursor.execute(sql, (user_id, limit, offset))
            
            behaviors = []
            for row in self.cursor.fetchall():
                behavior = {
                    "id": row[0],
                    "action_type": row[1],
                    "action_data": json.loads(row[2]) if row[2] else None,
                    "timestamp": row[3],
                    "ip_address": row[4],
                    "user_agent": row[5]
                }
                behaviors.append(behavior)
            
            return behaviors
        except Exception as e:
            print(f"获取用户行为记录失败: {str(e)}")
            return []
        finally:
            self.close()
    
    def get_auto_fill_suggestions(self, user_id, field_name, context=None):
        """获取自动填充建议"""
        if not self.connect():
            return []
        
        try:
            # 获取该字段的历史数据
            sql = """
            SELECT field_value, usage_count
            FROM auto_fill_data
            WHERE user_id = ? AND field_name = ?
            ORDER BY usage_count DESC, last_used DESC
            LIMIT 5
            """
            self.cursor.execute(sql, (user_id, field_name))
            
            suggestions = []
            for row in self.cursor.fetchall():
                suggestions.append({
                    "value": row[0],
                    "score": row[1]
                })
            
            return suggestions
        except Exception as e:
            print(f"获取自动填充建议失败: {str(e)}")
            return []
        finally:
            self.close()
    
    def sync_with_browser(self, user_id, browser_data):
        """与浏览器同步自动填充数据"""
        if not self.auto_fill_config["sync_with_browser"]:
            return False
        
        try:
            # 这里可以实现与浏览器的同步逻辑
            # 例如，接收浏览器发送的自动填充数据并保存
            for field_name, field_value in browser_data.items():
                if field_name in self.auto_fill_config["fields"] and field_value:
                    self.save_auto_fill_data(user_id, {field_name: field_value})
            return True
        except Exception as e:
            print(f"与浏览器同步失败: {str(e)}")
            return False

# 全局用户管理服务实例
user_manager_service = None

def get_user_manager_service():
    """获取用户管理服务实例"""
    global user_manager_service
    if user_manager_service is None:
        user_manager_service = UserManagerService()
    return user_manager_service

if __name__ == "__main__":
    # 测试用户管理服务
    service = UserManagerService()
    
    # 测试更新用户个人信息
    user_id = 1
    profile_data = {
        "full_name": "张三",
        "email": "zhangsan@example.com",
        "phone": "13800138000",
        "address": "北京市海淀区",
        "company": "MTSCOS",
        "job_title": "工程师"
    }
    
    print("更新用户个人信息...")
    result = service.update_user_profile(user_id, profile_data)
    print(f"更新结果: {result}")
    
    # 测试获取用户个人信息
    print("\n获取用户个人信息...")
    profile = service.get_user_profile(user_id)
    print(f"用户信息: {json.dumps(profile, indent=2, ensure_ascii=False)}")
    
    # 测试获取自动填充数据
    print("\n获取自动填充数据...")
    auto_fill_data = service.get_auto_fill_data(user_id)
    print(f"自动填充数据: {json.dumps(auto_fill_data, indent=2, ensure_ascii=False)}")
    
    # 测试获取自动填充建议
    print("\n获取自动填充建议...")
    suggestions = service.get_auto_fill_suggestions(user_id, "email")
    print(f"邮箱建议: {json.dumps(suggestions, indent=2, ensure_ascii=False)}")
    
    # 测试设置用户偏好
    print("\n设置用户偏好...")
    result = service.set_user_preference(user_id, "theme", "dark", "appearance")
    print(f"设置结果: {result}")
    
    # 测试获取用户偏好
    print("\n获取用户偏好...")
    preferences = service.get_user_preferences(user_id)
    print(f"用户偏好: {json.dumps(preferences, indent=2, ensure_ascii=False)}")
    
    # 测试记录用户行为
    print("\n记录用户行为...")
    result = service.record_user_behavior(user_id, "login", {"method": "email"}, "127.0.0.1", "Mozilla/5.0")
    print(f"记录结果: {result}")
    
    # 测试获取用户行为
    print("\n获取用户行为...")
    behaviors = service.get_user_behavior(user_id)
    print(f"用户行为: {json.dumps(behaviors, indent=2, ensure_ascii=False)}")
