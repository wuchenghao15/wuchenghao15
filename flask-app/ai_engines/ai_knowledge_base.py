# -*- coding: utf-8 -*-
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
AI知识库模块
由AI职业介绍所管理,支持自动升级扩展
"""

import os
import json
import logging
import requests
from datetime import datetime
from typing import Dict, List, Any, Optional, Set
from bs4 import BeautifulSoup

logger = logging.getLogger('ai_knowledge_base')

class AIKnowledgeBase:
    """AI知识库类"""

    def __init__(self, data_dir: str = None):
        """初始化AI知识库"""
        self.data_dir = data_dir or os.path.join(os.path.dirname(__file__), '../../data')
        os.makedirs(self.data_dir, exist_ok=True)

        self.knowledge_file = os.path.join(self.data_dir, 'knowledge_base.json')
        self.learning_history_file = os.path.join(self.data_dir, 'learning_history.json')
        self.sources_file = os.path.join(self.data_dir, 'knowledge_sources.json')

        self.knowledge_base = {
            'categories': {},
            'total_entries': 0,
            'last_updated': datetime.now().isoformat()
        }

        self.learning_history = []

        self.knowledge_sources = {
            'python': [
                'https://docs.python.org/3/',
                'https://realpython.com/',
                'https://stackoverflow.com/questions/tagged/python'
            ],
            'flask': [
                'https://flask.palletsprojects.com/',
                'https://stackoverflow.com/questions/tagged/flask'
            ],
            'git': [
                'https://git-scm.com/doc',
                'https://stackoverflow.com/questions/tagged/git'
            ],
            'sqlite': [
                'https://sqlite.org/docs.html',
                'https://stackoverflow.com/questions/tagged/sqlite'
            ],
            'ai': [
                'https://www.ibm.com/topics/artificial-intelligence',
                'https://en.wikipedia.org/wiki/Artificial_intelligence'
            ]
        }

        self._initialize_categories()
        self._load_data()

        logger.info("AI知识库初始化完成")

    def _load_data(self):
        """从文件加载数据"""
        try:
            if os.path.exists(self.knowledge_file):
                with open(self.knowledge_file, 'r', encoding='utf-8') as f:
                    self.knowledge_base = json.load(f)
                logger.info(f"知识库数据加载成功: {self.knowledge_base.get('total_entries', 0)} 条")

            if os.path.exists(self.learning_history_file):
                with open(self.learning_history_file, 'r', encoding='utf-8') as f:
                    self.learning_history = json.load(f)
                logger.info(f"学习历史加载成功: {len(self.learning_history)} 条")

            if os.path.exists(self.sources_file):
                with open(self.sources_file, 'r', encoding='utf-8') as f:
                    self.knowledge_sources = json.load(f)
                logger.info(f"知识来源加载成功: {len(self.knowledge_sources)} 个类别")
        except Exception as e:
            logger.error(f"加载数据失败: {str(e)}")

    def _save_data(self):
        """保存数据到文件"""
        try:
            self.knowledge_base['last_updated'] = datetime.now().isoformat()

            with open(self.knowledge_file, 'w', encoding='utf-8') as f:
                json.dump(self.knowledge_base, f, ensure_ascii=False, indent=2)

            with open(self.learning_history_file, 'w', encoding='utf-8') as f:
                json.dump(self.learning_history, f, ensure_ascii=False, indent=2)

            with open(self.sources_file, 'w', encoding='utf-8') as f:
                json.dump(self.knowledge_sources, f, ensure_ascii=False, indent=2)

            logger.info("知识库数据保存成功")
        except Exception as e:
            logger.error(f"保存数据失败: {str(e)}")

    def _initialize_categories(self):
        """初始化知识类别"""
        default_categories = {
            'python': {
                'name': 'Python',
                'description': 'Python编程语言相关知识',
                'entries': {}
            },
            'flask': {
                'name': 'Flask',
                'description': 'Flask框架相关知识',
                'entries': {}
            },
            'git': {
                'name': 'Git',
                'description': 'Git版本控制相关知识',
                'entries': {}
            },
            'sqlite': {
                'name': 'SQLite',
                'description': 'SQLite数据库相关知识',
                'entries': {}
            },
            'ai': {
                'name': 'AI',
                'description': '人工智能相关知识',
                'entries': {}
            },
            'education': {
                'name': '教育',
                'description': '教育相关知识',
                'entries': {}
            },
            'engineering': {
                'name': '工程',
                'description': '软件工程相关知识',
                'entries': {}
            }
        }

        for category_id, category_info in default_categories.items():
            if category_id not in self.knowledge_base['categories']:
                self.knowledge_base['categories'][category_id] = category_info

        self._update_total_entries()

    def _update_total_entries(self):
        """更新总条目数"""
        total = 0
        for category in self.knowledge_base['categories'].values():
            total += len(category.get('entries', {}))
        self.knowledge_base['total_entries'] = total

    def add_knowledge(self, category: str, title: str, content: str,
                      source: str = None, tags: List[str] = None) -> bool:
        """添加知识条目"""
        try:
            if category not in self.knowledge_base['categories']:
                logger.error(f"类别不存在: {category}")
                return False

            entry_id = f"{category}_{len(self.knowledge_base['categories'][category]['entries'])}"
            
            self.knowledge_base['categories'][category]['entries'][entry_id] = {
                'title': title,
                'content': content,
                'source': source,
                'tags': tags or [],
                'created_at': datetime.now().isoformat()
            }

            self._update_total_entries()
            self._save_data()
            
            self._record_learning_history('add_knowledge', {
                'category': category,
                'title': title
            })
            
            return True
        except Exception as e:
            logger.error(f"添加知识失败: {str(e)}")
            return False

    def _record_learning_history(self, action: str, details: Dict[str, Any]):
        """记录学习历史"""
        history_entry = {
            'action': action,
            'details': details,
            'timestamp': datetime.now().isoformat()
        }
        self.learning_history.append(history_entry)

        if len(self.learning_history) > 1000:
            self.learning_history = self.learning_history[-1000:]

    def get_learning_history(self, limit: int = 100) -> List[Dict]:
        """获取学习历史"""
        return self.learning_history[-limit:]

    def search_knowledge(self, query: str, category: str = None) -> List[Dict]:
        """搜索知识"""
        results = []
        query_lower = query.lower()

        categories_to_search = [category] if category else self.knowledge_base['categories'].keys()

        for cat_id in categories_to_search:
            if cat_id in self.knowledge_base['categories']:
                for entry_id, entry in self.knowledge_base['categories'][cat_id]['entries'].items():
                    if query_lower in entry.get('title', '').lower() or \
                       query_lower in entry.get('content', '').lower():
                        results.append({
                            'entry_id': entry_id,
                            'category': cat_id,
                            **entry
                        })

        return results

    def get_knowledge_by_category(self, category: str) -> List[Dict]:
        """获取指定类别的知识"""
        if category not in self.knowledge_base['categories']:
            return []

        entries = self.knowledge_base['categories'][category]['entries']
        return [{'entry_id': k, **v} for k, v in entries.items()]

    def get_all_categories(self) -> List[Dict]:
        """获取所有类别"""
        return [
            {'category_id': k, 'name': v['name'], 'description': v['description']}
            for k, v in self.knowledge_base['categories'].items()
        ]
