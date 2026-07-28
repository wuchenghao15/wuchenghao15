#!/usr/bin/env python3
# -*- coding: utf-8 -*-
""" MTSCOS技能管理服务 支持用户自定义添加、管理、加载skill功能 """

import os
import sys
import json
import importlib
import inspect
import threading
import sqlite3
from datetime import datetime
from typing import Dict, Any, Optional, List

logger = print

class SkillInfo:
    """技能信息"""
    
    def __init__(self, skill_id: str, name: str, description: str, 
                 body: str = '', author: str = None, version: str = '1.0.0',
                 category: str = 'general', enabled: bool = True, 
                 created_at: str = None):
        self.skill_id = skill_id
        self.name = name
        self.description = description
        self.body = body
        self.author = author
        self.version = version
        self.category = category
        self.enabled = enabled
        self.created_at = created_at or datetime.now().isoformat()
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            'skill_id': self.skill_id,
            'name': self.name,
            'description': self.description,
            'body': self.body,
            'author': self.author,
            'version': self.version,
            'category': self.category,
            'enabled': self.enabled,
            'created_at': self.created_at
        }

class SkillManager:
    """技能管理器"""
    
    def __init__(self):
        self.skills: Dict[str, SkillInfo] = {}
        self.skill_instances: Dict[str, Any] = {}
        self.is_running = False
        self.lock = threading.Lock()
        
        self.config = self._load_config()
        self._init_database()
        self._load_skills()
    
    def _load_config(self) -> Dict[str, Any]:
        """加载配置"""
        config_path = os.path.join(os.path.dirname(__file__), 'skill_config.json')
        if os.path.exists(config_path):
            with open(config_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        
        return {
            'enabled': True,
            'skills_dir': 'skills',
            'auto_reload': False,
            'reload_interval': 300,
            'max_skills': 100
        }
    
    def _save_config(self):
        """保存配置"""
        config_path = os.path.join(os.path.dirname(__file__), 'skill_config.json')
        with open(config_path, 'w', encoding='utf-8') as f:
            json.dump(self.config, f, indent=2, ensure_ascii=False)
    
    def _init_database(self):
        """初始化数据库"""
        try:
            conn = sqlite3.connect('app.db')
            cursor = conn.cursor()
            
            cursor.execute(''' CREATE TABLE IF NOT EXISTS skills ( id INTEGER PRIMARY KEY AUTOINCREMENT, skill_id TEXT NOT NULL UNIQUE, name TEXT NOT NULL, description TEXT, body TEXT, author TEXT, version TEXT DEFAULT '1.0.0', category TEXT DEFAULT 'general', enabled INTEGER DEFAULT 1, created_at TEXT DEFAULT CURRENT_TIMESTAMP, updated_at TEXT DEFAULT CURRENT_TIMESTAMP ) ''')
            
            cursor.execute(''' CREATE INDEX IF NOT EXISTS idx_skills_id ON skills(skill_id) ''')
            
            cursor.execute(''' CREATE INDEX IF NOT EXISTS idx_skills_category ON skills(category) ''')
            
            conn.commit()
            conn.close()
        except Exception as e:
            logger(f"[技能] 初始化数据库失败: {e}")
    
    def _load_skills(self):
        """加载技能"""
        skills_dir = self.config['skills_dir']
        os.makedirs(skills_dir, exist_ok=True)
        
        self._load_skills_from_db()
        self._load_skills_from_files()
    
    def _load_skills_from_db(self):
        """从数据库加载技能"""
        try:
            conn = sqlite3.connect('app.db')
            cursor = conn.cursor()
            
            cursor.execute('SELECT skill_id, name, description, body, author, version, category, enabled, created_at FROM skills')
            
            for row in cursor.fetchall():
                skill_id, name, description, body, author, version, category, enabled, created_at = row
                
                skill = SkillInfo(
                    skill_id=skill_id,
                    name=name,
                    description=description,
                    body=body,
                    author=author,
                    version=version,
                    category=category,
                    enabled=bool(enabled),
                    created_at=created_at
                )
                
                self.skills[skill_id] = skill
            
            conn.close()
            logger(f"[技能] 从数据库加载了 {len(self.skills)} 个技能")
        except Exception as e:
            logger(f"[技能] 从数据库加载失败: {e}")
    
    def _load_skills_from_files(self):
        """从文件加载技能"""
        skills_dir = self.config['skills_dir']
        
        for filename in os.listdir(skills_dir):
            if filename.endswith('.json'):
                skill_id = filename[:-5]
                
                if skill_id not in self.skills:
                    filepath = os.path.join(skills_dir, filename)
                    
                    try:
                        with open(filepath, 'r', encoding='utf-8') as f:
                            skill_data = json.load(f)
                        
                        skill = SkillInfo(
                            skill_id=skill_id,
                            name=skill_data.get('name', skill_id),
                            description=skill_data.get('description', ''),
                            body=skill_data.get('body', ''),
                            author=skill_data.get('author', None),
                            version=skill_data.get('version', '1.0.0'),
                            category=skill_data.get('category', 'general'),
                            enabled=skill_data.get('enabled', True),
                            created_at=skill_data.get('created_at', datetime.now().isoformat())
                        )
                        
                        self.skills[skill_id] = skill
                    except Exception as e:
                        logger(f"[技能] 加载技能文件失败: {filename} - {e}")
        
        logger(f"[技能] 从文件加载了 {len(self.skills)} 个技能")
    
    def add_skill(self, skill_id: str, name: str, description: str, 
                  body: str = '', author: str = None, version: str = '1.0.0',
                  category: str = 'general', enabled: bool = True) -> bool:
        """添加技能"""
        if len(self.skills) >= self.config['max_skills']:
            logger(f"[技能] 达到最大技能数量限制")
            return False
        
        if skill_id in self.skills:
            logger(f"[技能] 技能已存在: {skill_id}")
            return False
        
        skill = SkillInfo(
            skill_id=skill_id,
            name=name,
            description=description,
            body=body,
            author=author,
            version=version,
            category=category,
            enabled=enabled
        )
        
        with self.lock:
            self.skills[skill_id] = skill
        
        self._save_skill_to_db(skill)
        self._save_skill_to_file(skill)
        
        logger(f"[技能] 添加技能成功: {name}")
        return True
    
    def _save_skill_to_db(self, skill: SkillInfo):
        """保存技能到数据库"""
        try:
            conn = sqlite3.connect('app.db')
            cursor = conn.cursor()
            
            cursor.execute(''' INSERT INTO skills (skill_id, name, description, body, author, version, category, enabled, created_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?) ''', (
                skill.skill_id, skill.name, skill.description, skill.body,
                skill.author, skill.version, skill.category,
                1 if skill.enabled else 0, skill.created_at
            ))
            
            conn.commit()
            conn.close()
        except Exception as e:
            logger(f"[技能] 保存技能到数据库失败: {e}")
    
    def _save_skill_to_file(self, skill: SkillInfo):
        """保存技能到文件"""
        skills_dir = self.config['skills_dir']
        os.makedirs(skills_dir, exist_ok=True)
        
        filepath = os.path.join(skills_dir, f"{skill.skill_id}.json")
        
        try:
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(skill.to_dict(), f, indent=2, ensure_ascii=False)
        except Exception as e:
            logger(f"[技能] 保存技能到文件失败: {e}")
    
    def update_skill(self, skill_id: str, **kwargs) -> bool:
        """更新技能"""
        with self.lock:
            if skill_id not in self.skills:
                logger(f"[技能] 技能不存在: {skill_id}")
                return False
            
            skill = self.skills[skill_id]
            
            if 'name' in kwargs:
                skill.name = kwargs['name']
            if 'description' in kwargs:
                skill.description = kwargs['description']
            if 'body' in kwargs:
                skill.body = kwargs['body']
            if 'author' in kwargs:
                skill.author = kwargs['author']
            if 'version' in kwargs:
                skill.version = kwargs['version']
            if 'category' in kwargs:
                skill.category = kwargs['category']
            if 'enabled' in kwargs:
                skill.enabled = kwargs['enabled']
        
        self._update_skill_in_db(skill_id, kwargs)
        self._save_skill_to_file(skill)
        
        logger(f"[技能] 更新技能成功: {skill_id}")
        return True
    
    def _update_skill_in_db(self, skill_id: str, updates: Dict[str, Any]):
        """更新数据库中的技能"""
        try:
            conn = sqlite3.connect('app.db')
            cursor = conn.cursor()
            
            set_clause = []
            params = []
            
            for key, value in updates.items():
                if key == 'enabled':
                    set_clause.append(f"{key} = ?")
                    params.append(1 if value else 0)
                else:
                    set_clause.append(f"{key} = ?")
                    params.append(value)
            
            params.append(skill_id)
            
            cursor.execute(f'UPDATE skills SET {", ".join(set_clause)} WHERE skill_id = ?', params)
            
            conn.commit()
            conn.close()
        except Exception as e:
            logger(f"[技能] 更新数据库失败: {e}")
    
    def delete_skill(self, skill_id: str) -> bool:
        """删除技能"""
        with self.lock:
            if skill_id not in self.skills:
                logger(f"[技能] 技能不存在: {skill_id}")
                return False
            
            del self.skills[skill_id]
            
            if skill_id in self.skill_instances:
                del self.skill_instances[skill_id]
        
        self._delete_skill_from_db(skill_id)
        self._delete_skill_from_file(skill_id)
        
        logger(f"[技能] 删除技能成功: {skill_id}")
        return True
    
    def _delete_skill_from_db(self, skill_id: str):
        """从数据库删除技能"""
        try:
            conn = sqlite3.connect('app.db')
            cursor = conn.cursor()
            
            cursor.execute('DELETE FROM skills WHERE skill_id = ?', (skill_id,))
            
            conn.commit()
            conn.close()
        except Exception as e:
            logger(f"[技能] 从数据库删除失败: {e}")
    
    def _delete_skill_from_file(self, skill_id: str):
        """从文件删除技能"""
        skills_dir = self.config['skills_dir']
        filepath = os.path.join(skills_dir, f"{skill_id}.json")
        
        try:
            if os.path.exists(filepath):
                os.remove(filepath)
        except Exception as e:
            logger(f"[技能] 从文件删除失败: {e}")
    
    def enable_skill(self, skill_id: str) -> bool:
        """启用技能"""
        return self.update_skill(skill_id, enabled=True)
    
    def disable_skill(self, skill_id: str) -> bool:
        """禁用技能"""
        return self.update_skill(skill_id, enabled=False)
    
    def get_skill(self, skill_id: str) -> Optional[SkillInfo]:
        """获取技能"""
        return self.skills.get(skill_id)
    
    def get_skills(self, category: str = None, enabled_only: bool = False) -> List[SkillInfo]:
        """获取技能列表"""
        result = []
        
        with self.lock:
            for skill in self.skills.values():
                if category and skill.category != category:
                    continue
                if enabled_only and not skill.enabled:
                    continue
                result.append(skill)
        
        result.sort(key=lambda x: x.created_at, reverse=True)
        return result
    
    def get_categories(self) -> List[str]:
        """获取所有分类"""
        categories = set()
        
        with self.lock:
            for skill in self.skills.values():
                categories.add(skill.category)
        
        return sorted(list(categories))
    
    def execute_skill(self, skill_id: str, **kwargs) -> Any:
        """执行技能"""
        with self.lock:
            if skill_id not in self.skills:
                logger(f"[技能] 技能不存在: {skill_id}")
                return None
            
            skill = self.skills[skill_id]
            
            if not skill.enabled:
                logger(f"[技能] 技能已禁用: {skill_id}")
                return None
        
        if skill_id in self.skill_instances:
            instance = self.skill_instances[skill_id]
            
            if hasattr(instance, 'execute'):
                try:
                    return instance.execute(**kwargs)
                except Exception as e:
                    logger(f"[技能] 执行技能失败: {skill_id} - {e}")
                    return None
        
        if skill.body:
            try:
                local_vars = {}
                exec(skill.body, globals(), local_vars)
                
                if 'execute' in local_vars:
                    return local_vars['execute'](**kwargs)
                elif 'main' in local_vars:
                    return local_vars['main'](**kwargs)
            except Exception as e:
                logger(f"[技能] 执行技能代码失败: {skill_id} - {e}")
        
        logger(f"[技能] 技能没有可执行的方法: {skill_id}")
        return None
    
    def get_status(self) -> Dict[str, Any]:
        """获取服务状态"""
        with self.lock:
            enabled_count = sum(1 for skill in self.skills.values() if skill.enabled)
            disabled_count = len(self.skills) - enabled_count
            
            return {
                'status': 'running',
                'total_skills': len(self.skills),
                'enabled_skills': enabled_count,
                'disabled_skills': disabled_count,
                'categories': self.get_categories(),
                'max_skills': self.config['max_skills'],
                'skills_dir': self.config['skills_dir']
            }

skill_manager = SkillManager()
