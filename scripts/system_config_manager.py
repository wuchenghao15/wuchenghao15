#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
MTSCOS AI 系统配置管理器
System Configuration Manager - Database Edition
"""

import sqlite3
import json
import logging
from datetime import datetime
from typing import Any, Optional, Dict, List

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('system_config.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger('system_config')

class SystemConfigManager:
    """系统配置管理器"""
    
    def __init__(self, db_path: str = "system_config.db"):
        self.db_path = db_path
        self._init_database()
        self._init_default_configs()
        
    def _init_database(self):
        """初始化数据库"""
        conn = sqlite3.connect(self.db_path, check_same_thread=False)
        cursor = conn.cursor()
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS system_config (
                config_key TEXT PRIMARY KEY,
                config_value TEXT NOT NULL,
                config_type TEXT DEFAULT 'string',
                config_group TEXT DEFAULT 'general',
                config_label TEXT,
                config_description TEXT,
                is_encrypted INTEGER DEFAULT 0,
                is_system INTEGER DEFAULT 0,
                updated_at TEXT,
                created_at TEXT
            )
        """)
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS user_preferences (
                user_id TEXT NOT NULL,
                preference_key TEXT NOT NULL,
                preference_value TEXT,
                updated_at TEXT,
                PRIMARY KEY (user_id, preference_key)
            )
        """)
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS config_audit (
                audit_id INTEGER PRIMARY KEY AUTOINCREMENT,
                config_key TEXT,
                action TEXT,
                old_value TEXT,
                new_value TEXT,
                user_id TEXT,
                timestamp TEXT
            )
        """)
        
        conn.commit()
        conn.close()
        logger.info("数据库初始化完成")
        
    def _init_default_configs(self):
        """初始化默认配置"""
        default_configs = {
            'system.name': {
                'value': 'MTSCOS AI',
                'type': 'string',
                'group': 'system',
                'label': '系统名称',
                'description': '系统的显示名称',
                'system': True
            },
            'system.version': {
                'value': '3.2.0',
                'type': 'string',
                'group': 'system',
                'label': '系统版本',
                'description': '当前系统版本号',
                'system': True
            },
            'system.max_login_attempts': {
                'value': '5',
                'type': 'number',
                'group': 'security',
                'label': '最大登录尝试次数',
                'description': '用户连续登录失败的最大次数',
                'system': True
            },
            'system.session_timeout': {
                'value': '3600',
                'type': 'number',
                'group': 'security',
                'label': '会话超时时间',
                'description': '会话超时时间（秒）',
                'system': True
            },
            'system.allow_guest_access': {
                'value': 'false',
                'type': 'boolean',
                'group': 'access',
                'label': '允许访客访问',
                'description': '是否允许未登录用户访问系统',
                'system': True
            },
            'exam.max_exam_duration': {
                'value': '120',
                'type': 'number',
                'group': 'exam',
                'label': '最大考试时长',
                'description': '考试最大持续时间（分钟）',
                'system': True
            },
            'exam.passing_score': {
                'value': '60',
                'type': 'number',
                'group': 'exam',
                'label': '及格分数',
                'description': '考试的及格分数线',
                'system': True
            },
            'exam.allow_review': {
                'value': 'true',
                'type': 'boolean',
                'group': 'exam',
                'label': '允许查看答案',
                'description': '考试结束后是否允许查看答案',
                'system': True
            },
            'student.nine_year.enabled': {
                'value': 'true',
                'type': 'boolean',
                'group': 'education',
                'label': '启用9年制教育',
                'description': '是否启用9年制学生功能',
                'system': True
            },
            'student.adult.enabled': {
                'value': 'true',
                'type': 'boolean',
                'group': 'education',
                'label': '启用成人教育',
                'description': '是否启用成人学生功能',
                'system': True
            },
            'ui.theme': {
                'value': 'cybertech',
                'type': 'select',
                'group': 'ui',
                'label': '界面主题',
                'description': '系统界面主题风格',
                'system': True
            },
            'ui.particles_enabled': {
                'value': 'true',
                'type': 'boolean',
                'group': 'ui',
                'label': '启用粒子效果',
                'description': '是否在界面中显示粒子动画效果',
                'system': True
            },
            'ui.language': {
                'value': 'zh-CN',
                'type': 'select',
                'group': 'ui',
                'label': '界面语言',
                'description': '系统界面显示语言',
                'system': True
            },
            'permission.enable_auto_detect': {
                'value': 'true',
                'type': 'boolean',
                'group': 'permission',
                'label': '启用自动检测',
                'description': '是否根据用户名自动检测用户组别',
                'system': True
            },
            'permission.default_group': {
                'value': 'student',
                'type': 'select',
                'group': 'permission',
                'label': '默认用户组别',
                'description': '未匹配到规则时的默认用户组别',
                'system': True
            }
        }
        
        conn = sqlite3.connect(self.db_path, check_same_thread=False)
        cursor = conn.cursor()
        
        for key, config in default_configs.items():
            cursor.execute("SELECT config_key FROM system_config WHERE config_key = ?", (key,))
            if not cursor.fetchone():
                cursor.execute("""
                    INSERT INTO system_config 
                    (config_key, config_value, config_type, config_group, config_label, 
                     config_description, is_system, updated_at, created_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    key,
                    config['value'],
                    config['type'],
                    config['group'],
                    config['label'],
                    config['description'],
                    config.get('system', False),
                    datetime.now().isoformat(),
                    datetime.now().isoformat()
                ))
        
        conn.commit()
        conn.close()
        logger.info("默认配置初始化完成")
        
    def get_config(self, key: str, default: Any = None) -> Any:
        """获取配置值"""
        conn = sqlite3.connect(self.db_path, check_same_thread=False)
        cursor = conn.cursor()
        
        cursor.execute("SELECT config_value, config_type FROM system_config WHERE config_key = ?", (key,))
        result = cursor.fetchone()
        conn.close()
        
        if result:
            value, config_type = result
            if config_type == 'number':
                return int(value)
            elif config_type == 'boolean':
                return value.lower() == 'true'
            return value
        return default
        
    def set_config(self, key: str, value: Any, user_id: str = 'system') -> bool:
        """设置配置值"""
        conn = sqlite3.connect(self.db_path, check_same_thread=False)
        cursor = conn.cursor()
        
        cursor.execute("SELECT config_value FROM system_config WHERE config_key = ?", (key,))
        old_result = cursor.fetchone()
        old_value = old_result[0] if old_result else None
        
        if isinstance(value, bool):
            value = 'true' if value else 'false'
        elif not isinstance(value, str):
            value = str(value)
            
        cursor.execute("""
            INSERT OR REPLACE INTO system_config 
            (config_key, config_value, updated_at)
            VALUES (?, ?, ?)
        """, (key, value, datetime.now().isoformat()))
        
        cursor.execute("""
            INSERT INTO config_audit 
            (config_key, action, old_value, new_value, user_id, timestamp)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (key, 'update', old_value, value, user_id, datetime.now().isoformat()))
        
        conn.commit()
        conn.close()
        logger.info(f"配置更新: {key} = {value}")
        return True
        
    def get_all_configs(self, group: str = None) -> List[Dict]:
        """获取所有配置"""
        conn = sqlite3.connect(self.db_path, check_same_thread=False)
        cursor = conn.cursor()
        
        if group:
            cursor.execute("""
                SELECT config_key, config_value, config_type, config_group, 
                       config_label, config_description, is_system, updated_at
                FROM system_config 
                WHERE config_group = ?
                ORDER BY config_group, config_key
            """, (group,))
        else:
            cursor.execute("""
                SELECT config_key, config_value, config_type, config_group, 
                       config_label, config_description, is_system, updated_at
                FROM system_config 
                ORDER BY config_group, config_key
            """)
            
        results = cursor.fetchall()
        conn.close()
        
        configs = []
        for row in results:
            configs.append({
                'key': row[0],
                'value': row[1],
                'type': row[2],
                'group': row[3],
                'label': row[4],
                'description': row[5],
                'is_system': bool(row[6]),
                'updated_at': row[7]
            })
            
        return configs
    
    def get_config_groups(self) -> List[str]:
        """获取所有配置分组"""
        conn = sqlite3.connect(self.db_path, check_same_thread=False)
        cursor = conn.cursor()
        
        cursor.execute("SELECT DISTINCT config_group FROM system_config ORDER BY config_group")
        results = cursor.fetchall()
        conn.close()
        
        return [row[0] for row in results]
    
    def delete_config(self, key: str, user_id: str = 'system') -> bool:
        """删除配置"""
        conn = sqlite3.connect(self.db_path, check_same_thread=False)
        cursor = conn.cursor()
        
        cursor.execute("SELECT config_key FROM system_config WHERE config_key = ? AND is_system = 1", (key,))
        if cursor.fetchone():
            logger.warning(f"尝试删除系统配置: {key}")
            conn.close()
            return False
            
        cursor.execute("SELECT config_value FROM system_config WHERE config_key = ?", (key,))
        old_result = cursor.fetchone()
        old_value = old_result[0] if old_result else None
        
        cursor.execute("DELETE FROM system_config WHERE config_key = ?", (key,))
        
        cursor.execute("""
            INSERT INTO config_audit 
            (config_key, action, old_value, new_value, user_id, timestamp)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (key, 'delete', old_value, None, user_id, datetime.now().isoformat()))
        
        conn.commit()
        conn.close()
        logger.info(f"配置删除: {key}")
        return True
        
    def get_user_preference(self, user_id: str, key: str, default: Any = None) -> Any:
        """获取用户偏好设置"""
        conn = sqlite3.connect(self.db_path, check_same_thread=False)
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT preference_value FROM user_preferences 
            WHERE user_id = ? AND preference_key = ?
        """, (user_id, key))
        
        result = cursor.fetchone()
        conn.close()
        
        return result[0] if result else default
        
    def set_user_preference(self, user_id: str, key: str, value: Any) -> bool:
        """设置用户偏好设置"""
        conn = sqlite3.connect(self.db_path, check_same_thread=False)
        cursor = conn.cursor()
        
        if not isinstance(value, str):
            value = json.dumps(value)
            
        cursor.execute("""
            INSERT OR REPLACE INTO user_preferences 
            (user_id, preference_key, preference_value, updated_at)
            VALUES (?, ?, ?, ?)
        """, (user_id, key, value, datetime.now().isoformat()))
        
        conn.commit()
        conn.close()
        return True
        
    def export_config(self) -> Dict:
        """导出所有配置"""
        return {
            'system': self.get_all_configs(),
            'groups': self.get_config_groups(),
            'exported_at': datetime.now().isoformat()
        }
        
    def import_config(self, config_data: Dict, overwrite: bool = False) -> int:
        """导入配置"""
        imported_count = 0
        
        if 'system' in config_data:
            for config in config_data['system']:
                if overwrite or not self.get_config(config['key']):
                    self.set_config(config['key'], config['value'])
                    imported_count += 1
                    
        return imported_count

def main():
    """测试主函数"""
    print("\n🔧 MTSCOS AI 系统配置管理器")
    print("=" * 60)
    
    config_manager = SystemConfigManager()
    
    print("\n📋 系统配置信息:")
    print(f"  系统名称: {config_manager.get_config('system.name')}")
    print(f"  系统版本: {config_manager.get_config('system.version')}")
    print(f"  最大登录尝试: {config_manager.get_config('system.max_login_attempts')} 次")
    print(f"  会话超时: {config_manager.get_config('system.session_timeout')} 秒")
    print(f"  允许访客访问: {config_manager.get_config('system.allow_guest_access')}")
    
    print("\n📚 教育配置:")
    print(f"  启用9年制: {config_manager.get_config('student.nine_year.enabled')}")
    print(f"  启用成人教育: {config_manager.get_config('student.adult.enabled')}")
    
    print("\n🎨 界面配置:")
    print(f"  界面主题: {config_manager.get_config('ui.theme')}")
    print(f"  粒子效果: {config_manager.get_config('ui.particles_enabled')}")
    print(f"  界面语言: {config_manager.get_config('ui.language')}")
    
    print("\n🔐 权限配置:")
    print(f"  自动检测: {config_manager.get_config('permission.enable_auto_detect')}")
    print(f"  默认组别: {config_manager.get_config('permission.default_group')}")
    
    print("\n📊 配置分组:")
    groups = config_manager.get_config_groups()
    for group in groups:
        print(f"  - {group}")
    
    print("\n" + "=" * 60)
    print("✅ 配置管理器测试完成")

if __name__ == '__main__':
    main()
