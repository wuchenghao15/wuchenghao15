#!/usr/bin/env python3
# -*- coding: utf-8 -*-
""" MTSCOS AI提示词模板管理服务 提供模板化提示词、变量替换和版本管理 """

import os
import sys
import json
import time
import re
import threading
import sqlite3
from datetime import datetime
from typing import Dict, Any, Optional, List

logger = print

# 变量模式 {{variable_name}}
VAR_PATTERN = re.compile(r'\{\{(\w+)\}\}')


class PromptTemplate:
    """提示词模板"""

    def __init__(self, template_id: str, name: str, content: str,
                 category: str = 'general', description: str = '',
                 variables: List[Dict[str, Any]] = None,
                 model_id: str = '', tags: List[str] = None):
        self.template_id = template_id
        self.name = name
        self.content = content
        self.category = category
        self.description = description
        self.variables = variables or []
        self.model_id = model_id
        self.tags = tags or []
        self.version = 1
        self.is_active = True
        self.usage_count = 0
        self.avg_rating = 0.0
        self.rating_count = 0
        self.created_at = datetime.now().isoformat()
        self.updated_at = self.created_at

    def extract_variables(self) -> List[str]:
        """从模板内容中提取变量"""
        return VAR_PATTERN.findall(self.content)

    def render(self, params: Dict[str, Any]) -> str:
        """渲染模板"""
        content = self.content

        # 替换变量
        def replace_var(match):
            var_name = match.group(1)
            value = params.get(var_name, match.group(0))
            return str(value)

        content = VAR_PATTERN.sub(replace_var, content)

        return content

    def to_dict(self) -> Dict[str, Any]:
        return {
            'template_id': self.template_id,
            'name': self.name,
            'content': self.content,
            'category': self.category,
            'description': self.description,
            'variables': self.variables,
            'extracted_variables': self.extract_variables(),
            'model_id': self.model_id,
            'tags': self.tags,
            'version': self.version,
            'is_active': self.is_active,
            'usage_count': self.usage_count,
            'avg_rating': round(self.avg_rating, 2),
            'rating_count': self.rating_count,
            'created_at': self.created_at,
            'updated_at': self.updated_at
        }


class PromptVersion:
    """提示词版本"""

    def __init__(self, version_id: str, template_id: str, version: int,
                 content: str, change_note: str = ''):
        self.version_id = version_id
        self.template_id = template_id
        self.version = version
        self.content = content
        self.change_note = change_note
        self.created_at = datetime.now().isoformat()

    def to_dict(self) -> Dict[str, Any]:
        return {
            'version_id': self.version_id,
            'template_id': self.template_id,
            'version': self.version,
            'content': self.content,
            'change_note': self.change_note,
            'created_at': self.created_at
        }


class AIPromptManager:
    """AI提示词模板管理服务"""

    def __init__(self):
        self.templates: Dict[str, PromptTemplate] = {}
        self.versions: Dict[str, List[PromptVersion]] = {}
        self.is_running = False
        self.lock = threading.Lock()

        self._init_database()
        self._register_default_templates()

    def _init_database(self):
        try:
            conn = sqlite3.connect('app.db')
            cursor = conn.cursor()

            cursor.execute(''' CREATE TABLE IF NOT EXISTS ai_prompt_templates ( id INTEGER PRIMARY KEY AUTOINCREMENT, template_id TEXT NOT NULL UNIQUE, name TEXT NOT NULL, content TEXT NOT NULL, category TEXT DEFAULT 'general', description TEXT, variables TEXT, model_id TEXT, tags TEXT, version INTEGER DEFAULT 1, is_active INTEGER DEFAULT 1, usage_count INTEGER DEFAULT 0, avg_rating REAL DEFAULT 0, rating_count INTEGER DEFAULT 0, created_at TEXT DEFAULT CURRENT_TIMESTAMP, updated_at TEXT ) ''')

            cursor.execute(''' CREATE TABLE IF NOT EXISTS ai_prompt_versions ( id INTEGER PRIMARY KEY AUTOINCREMENT, version_id TEXT NOT NULL UNIQUE, template_id TEXT NOT NULL, version INTEGER NOT NULL, content TEXT NOT NULL, change_note TEXT, created_at TEXT DEFAULT CURRENT_TIMESTAMP ) ''')

            cursor.execute(''' CREATE INDEX IF NOT EXISTS idx_prompt_templates_category ON ai_prompt_templates(category) ''')

            cursor.execute(''' CREATE INDEX IF NOT EXISTS idx_prompt_versions_template ON ai_prompt_versions(template_id) ''')

            conn.commit()
            conn.close()
        except Exception as e:
            logger(f"[提示词] 初始化数据库失败: {e}")

    def _register_default_templates(self):
        """注册默认模板"""
        defaults = [
            PromptTemplate(
                'tpl_system', '系统提示词',
                '你是MTSCOS AI助手，一个企业级智能管理系统的人工智能。你的职责是帮助用户完成系统操作、回答问题和提供建议。',
                category='system',
                description='基础系统提示词',
                tags=['system', 'base']
            ),
            PromptTemplate(
                'tpl_qa', '问答模板',
                '请回答以下问题：\n\n问题：{{question}}\n\n请提供准确、简洁的答案。如果不确定，请说明。',
                category='qa',
                description='标准问答提示词模板',
                variables=[
                    {'name': 'question', 'type': 'string', 'required': True, 'description': '用户问题'}
                ],
                tags=['qa', 'question']
            ),
            PromptTemplate(
                'tpl_summary', '摘要模板',
                '请为以下内容生成摘要：\n\n内容：{{content}}\n\n要求：\n1. 摘要不超过{{max_words}}字\n2. 保留关键信息\n3. 语言简洁',
                category='summary',
                description='内容摘要生成模板',
                variables=[
                    {'name': 'content', 'type': 'string', 'required': True, 'description': '待摘要内容'},
                    {'name': 'max_words', 'type': 'number', 'default': 200, 'description': '最大字数'}
                ],
                tags=['summary', 'compression']
            ),
            PromptTemplate(
                'tpl_translation', '翻译模板',
                '请将以下{{source_lang}}文本翻译为{{target_lang}}：\n\n原文：{{text}}\n\n要求翻译准确、通顺。',
                category='translation',
                description='多语言翻译模板',
                variables=[
                    {'name': 'source_lang', 'type': 'string', 'default': '中文', 'description': '源语言'},
                    {'name': 'target_lang', 'type': 'string', 'required': True, 'description': '目标语言'},
                    {'name': 'text', 'type': 'string', 'required': True, 'description': '待翻译文本'}
                ],
                tags=['translation', 'language']
            ),
            PromptTemplate(
                'tpl_code_review', '代码审查模板',
                '请审查以下{{language}}代码：\n\n```{{language}}\n{{code}}\n```\n\n请从以下方面评估：\n1. 代码质量\n2. 安全性\n3. 性能\n4.  可读性\n5. 改进建议',
                category='code',
                description='代码审查提示词模板',
                variables=[
                    {'name': 'language', 'type': 'string', 'required': True, 'description': '编程语言'},
                    {'name': 'code', 'type': 'string', 'required': True, 'description': '代码内容'}
                ],
                tags=['code', 'review']
            ),
            PromptTemplate(
                'tpl_data_analysis', '数据分析模板',
                '请分析以下数据：\n\n数据：{{data}}\n\n分析要求：{{requirements}}\n\n请提供：\n1. 数据概述\n2. 关键发现\n3. 趋势分析\n4. 建议',
                category='analysis',
                description='数据分析提示词模板',
                variables=[
                    {'name': 'data', 'type': 'string', 'required': True, 'description': '数据内容'},
                    {'name': 'requirements', 'type': 'string', 'default': '全面分析', 'description': '分析要求'}
                ],
                tags=['data', 'analysis']
            ),
            PromptTemplate(
                'tpl_exam_gen', '考试题目生成模板',
                '请根据以下信息生成{{count}}道{{question_type}}题目：\n\n知识点：{{topic}}\n难度：{{difficulty}}\n\n要求：\n1. 题目覆盖核心知识点\n2.  提供标准答案\n3. 提供解析',
                category='exam',
                description='考试题目生成模板',
                variables=[
                    {'name': 'count', 'type': 'number', 'default': 5, 'description': '题目数量'},
                    {'name': 'question_type', 'type': 'string', 'default': '选择题', 'description': '题型'},
                    {'name': 'topic', 'type': 'string', 'required': True, 'description': '知识点'},
                    {'name': 'difficulty', 'type': 'string', 'default': '中等', 'description': '难度'}
                ],
                tags=['exam', 'education']
            ),
        ]

        for template in defaults:
            self.templates[template.template_id] = template
            self._save_template_to_db(template)
            self._save_version(template)

    def _save_template_to_db(self, template: PromptTemplate):
        try:
            conn = sqlite3.connect('app.db')
            cursor = conn.cursor()

            cursor.execute(''' INSERT OR REPLACE INTO ai_prompt_templates (template_id, name, content, category, description, variables, model_id, tags, version, is_active, usage_count, avg_rating, rating_count, updated_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?) ''', (
                template.template_id, template.name, template.content,
                template.category, template.description,
                json.dumps(template.variables), template.model_id,
                json.dumps(template.tags), template.version,
                1 if template.is_active else 0, template.usage_count,
                template.avg_rating, template.rating_count, template.updated_at
            ))

            conn.commit()
            conn.close()
        except Exception as e:
            logger(f"[提示词] 保存模板失败: {e}")

    def _save_version(self, template: PromptTemplate, change_note: str = ''):
        try:
            import uuid
            version_id = f"ver_{uuid.uuid4().hex[:12]}"

            version = PromptVersion(
                version_id, template.template_id,
                template.version, template.content, change_note
            )

            if template.template_id not in self.versions:
                self.versions[template.template_id] = []
            self.versions[template.template_id].append(version)

            conn = sqlite3.connect('app.db')
            cursor = conn.cursor()

            cursor.execute(''' INSERT INTO ai_prompt_versions (version_id, template_id, version, content, change_note) VALUES (?, ?, ?, ?, ?) ''', (version.version_id, version.template_id,
                  version.version, version.content, version.change_note))

            conn.commit()
            conn.close()
        except Exception as e:
            logger(f"[提示词] 保存版本失败: {e}")

    def create_template(self, name: str, content: str, category: str = 'general',
                        description: str = '', variables: List[Dict[str, Any]] = None,
                        model_id: str = '', tags: List[str] = None) -> str:
        """创建模板"""
        import uuid
        template_id = f"tpl_{uuid.uuid4().hex[:8]}"

        template = PromptTemplate(
            template_id, name, content, category, description,
            variables, model_id, tags
        )

        with self.lock:
            self.templates[template_id] = template

        self._save_template_to_db(template)
        self._save_version(template, '初始版本')
        logger(f"[提示词] 创建模板: {name}")

        return template_id

    def render_template(self, template_id: str,
                        params: Dict[str, Any]) -> Optional[str]:
        """渲染模板"""
        with self.lock:
            template = self.templates.get(template_id)
            if not template:
                return None

            template.usage_count += 1

        self._save_template_to_db(template)

        return template.render(params)

    def update_template(self, template_id: str, content: str = None,
                        name: str = None, description: str = None,
                        change_note: str = '') -> bool:
        """更新模板（创建新版本）"""
        with self.lock:
            template = self.templates.get(template_id)
            if not template:
                return False

            if content:
                template.content = content
            if name:
                template.name = name
            if description:
                template.description = description

            template.version += 1
            template.updated_at = datetime.now().isoformat()

        self._save_template_to_db(template)
        self._save_version(template, change_note or f'更新到版本 {template.version}')

        return True

    def rate_template(self, template_id: str, rating: float) -> bool:
        """评分模板"""
        with self.lock:
            template = self.templates.get(template_id)
            if not template:
                return False

            total = template.avg_rating * template.rating_count + rating
            template.rating_count += 1
            template.avg_rating = total / template.rating_count

        self._save_template_to_db(template)
        return True

    def get_template(self, template_id: str) -> Optional[Dict[str, Any]]:
        template = self.templates.get(template_id)
        return template.to_dict() if template else None

    def get_templates(self, category: str = None,
                      active_only: bool = False) -> List[Dict[str, Any]]:
        with self.lock:
            templates = list(self.templates.values())

            if category:
                templates = [t for t in templates if t.category == category]
            if active_only:
                templates = [t for t in templates if t.is_active]

            return [t.to_dict() for t in templates]

    def get_versions(self, template_id: str) -> List[Dict[str, Any]]:
        versions = self.versions.get(template_id, [])
        return [v.to_dict() for v in versions]

    def rollback_version(self, template_id: str, version: int) -> bool:
        """回滚到指定版本"""
        with self.lock:
            template = self.templates.get(template_id)
            if not template:
                return False

            versions = self.versions.get(template_id, [])
            target = None
            for v in versions:
                if v.version == version:
                    target = v
                    break

            if not target:
                return False

            template.content = target.content
            template.version += 1
            template.updated_at = datetime.now().isoformat()

        self._save_template_to_db(template)
        self._save_version(template, f'回滚到版本 {version}')
        return True

    def get_categories(self) -> List[Dict[str, Any]]:
        with self.lock:
            cat_counts: Dict[str, int] = {}
            for t in self.templates.values():
                cat_counts[t.category] = cat_counts.get(t.category, 0) + 1

            return [{'category': k, 'count': v} for k, v in sorted(cat_counts.items())]

    def get_stats(self) -> Dict[str, Any]:
        with self.lock:
            total_usage = sum(t.usage_count for t in self.templates.values())
            avg_rating = 0.0
            rated = [t for t in self.templates.values() if t.rating_count > 0]
            if rated:
                avg_rating = sum(t.avg_rating for t in rated) / len(rated)

            return {
                'total_templates': len(self.templates),
                'active_templates': sum(1 for t in self.templates.values() if t.is_active),
                'total_versions': sum(len(v) for v in self.versions.values()),
                'total_usage': total_usage,
                'avg_rating': round(avg_rating, 2),
                'categories': len(self.get_categories())
            }

    def get_status(self) -> Dict[str, Any]:
        return {
            'status': 'running' if self.is_running else 'stopped',
            'total_templates': len(self.templates)
        }

    def start(self):
        if self.is_running:
            return
        self.is_running = True
        logger(f"[提示词] 提示词管理服务已启动")

    def stop(self):
        self.is_running = False
        logger(f"[提示词] 提示词管理服务已停止")


ai_prompt_manager = AIPromptManager()



