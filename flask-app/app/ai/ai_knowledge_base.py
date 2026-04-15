#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
AI知识库模块
由AI职业介绍所管理，支持自动升级扩展
"""

import os
import json
import logging
import requests
from datetime import datetime
from typing import Dict, List, Any, Optional, Set
from bs4 import BeautifulSoup

# 配置日志
logger = logging.getLogger('ai_knowledge_base')

class AIKnowledgeBase:
    """AI知识库类"""
    
    def __init__(self, data_dir: str = None):
        """初始化AI知识库"""
        # 数据目录
        self.data_dir = data_dir or os.path.join(os.path.dirname(__file__), '../../data')
        os.makedirs(self.data_dir, exist_ok=True)
        
        # 数据文件路径
        self.knowledge_file = os.path.join(self.data_dir, 'knowledge_base.json')
        self.learning_history_file = os.path.join(self.data_dir, 'learning_history.json')
        self.sources_file = os.path.join(self.data_dir, 'knowledge_sources.json')
        
        # 知识库数据
        self.knowledge_base = {
            'categories': {},
            'total_entries': 0,
            'last_updated': datetime.now().isoformat()
        }
        
        # 学习历史
        self.learning_history = []
        
        # 知识来源
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
        
        # 初始化类别
        self._initialize_categories()
        
        # 加载数据
        self._load_data()
        
        logger.info("AI知识库初始化完成")
    
    # 数据持久化方法
    
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
    
    # 初始化方法
    
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
        
        # 计算总条目数
        self._update_total_entries()
    
    def _update_total_entries(self):
        """更新总条目数"""
        total = 0
        for category in self.knowledge_base['categories'].values():
            total += len(category.get('entries', {}))
        self.knowledge_base['total_entries'] = total
    
    # 知识管理方法
    
    def add_knowledge(self, category: str, title: str, content: str, 
                     source: str = None, tags: List[str] = None) -> bool:
        """添加知识条目"""
        try:
            if category not in self.knowledge_base['categories']:
                logger.error(f"类别不存在: {category}")
                return False
            
            # 生成唯一ID
            entry_id = f"{category}_{datetime.now().timestamp()}"
            
            # 创建知识条目
            knowledge_entry = {
                'id': entry_id,
                'title': title,
                'content': content,
                'source': source,
                'tags': tags or [],
                'created_at': datetime.now().isoformat(),
                'updated_at': datetime.now().isoformat(),
                'access_count': 0
            }
            
            # 添加到知识库
            self.knowledge_base['categories'][category]['entries'][entry_id] = knowledge_entry
            self._update_total_entries()
            self._save_data()
            
            # 记录学习历史
            self._record_learning_history('add_knowledge', {
                'category': category,
                'title': title,
                'source': source
            })
            
            logger.info(f"知识添加成功: {title} (类别: {category})")
            return True
        except Exception as e:
            logger.error(f"添加知识失败: {str(e)}")
            return False
    
    def search_knowledge(self, query: str, category: str = None, 
                        tags: List[str] = None) -> List[Dict[str, Any]]:
        """搜索知识"""
        results = []
        
        try:
            # 确定搜索范围
            categories_to_search = []
            if category:
                if category in self.knowledge_base['categories']:
                    categories_to_search = [category]
            else:
                categories_to_search = list(self.knowledge_base['categories'].keys())
            
            # 搜索知识
            for cat in categories_to_search:
                category_info = self.knowledge_base['categories'][cat]
                for entry_id, entry in category_info['entries'].items():
                    # 检查标题和内容
                    match = query.lower() in entry['title'].lower() or \
                            query.lower() in entry['content'].lower()
                    
                    # 检查标签
                    if tags:
                        tag_match = any(tag in entry['tags'] for tag in tags)
                        match = match and tag_match
                    
                    if match:
                        # 增加访问计数
                        entry['access_count'] += 1
                        entry['updated_at'] = datetime.now().isoformat()
                        
                        results.append({
                            'id': entry['id'],
                            'category': cat,
                            'title': entry['title'],
                            'content': entry['content'],
                            'source': entry['source'],
                            'tags': entry['tags'],
                            'access_count': entry['access_count'],
                            'created_at': entry['created_at']
                        })
            
            # 按访问计数排序
            results.sort(key=lambda x: x['access_count'], reverse=True)
            
            # 保存更新
            self._save_data()
            
            # 记录学习历史
            self._record_learning_history('search_knowledge', {
                'query': query,
                'category': category,
                'tags': tags,
                'results_count': len(results)
            })
            
            logger.info(f"搜索知识完成: '{query}' 找到 {len(results)} 条结果")
            return results
        except Exception as e:
            logger.error(f"搜索知识失败: {str(e)}")
            return []
    
    def get_knowledge_by_category(self, category: str) -> List[Dict[str, Any]]:
        """按类别获取知识"""
        try:
            if category not in self.knowledge_base['categories']:
                return []
            
            category_info = self.knowledge_base['categories'][category]
            entries = category_info['entries']
            
            results = []
            for entry_id, entry in entries.items():
                results.append({
                    'id': entry['id'],
                    'title': entry['title'],
                    'content': entry['content'],
                    'source': entry['source'],
                    'tags': entry['tags'],
                    'access_count': entry['access_count'],
                    'created_at': entry['created_at']
                })
            
            # 按创建时间排序
            results.sort(key=lambda x: x['created_at'], reverse=True)
            
            logger.info(f"获取 {category} 类别知识: {len(results)} 条")
            return results
        except Exception as e:
            logger.error(f"按类别获取知识失败: {str(e)}")
            return []
    
    # 自动升级扩展方法
    
    def auto_update_knowledge(self) -> Dict[str, Any]:
        """自动更新知识库"""
        update_result = {
            'success': True,
            'updated_categories': [],
            'new_entries': 0,
            'errors': []
        }
        
        try:
            logger.info("开始自动更新知识库")
            
            # 为每个类别更新知识
            for category, sources in self.knowledge_sources.items():
                if category in self.knowledge_base['categories']:
                    logger.info(f"更新 {category} 类别知识")
                    category_result = self._update_category_knowledge(category, sources)
                    
                    if category_result['success']:
                        update_result['updated_categories'].append(category)
                        update_result['new_entries'] += category_result['new_entries']
                    else:
                        update_result['errors'].append(category_result['error'])
            
            # 保存更新
            self._save_data()
            
            # 记录学习历史
            self._record_learning_history('auto_update', {
                'updated_categories': update_result['updated_categories'],
                'new_entries': update_result['new_entries'],
                'errors': update_result['errors']
            })
            
            logger.info(f"自动更新完成: {update_result['new_entries']} 条新条目")
            return update_result
        except Exception as e:
            logger.error(f"自动更新知识库失败: {str(e)}")
            update_result['success'] = False
            update_result['errors'].append(str(e))
            return update_result
    
    def _update_category_knowledge(self, category: str, sources: List[str]) -> Dict[str, Any]:
        """更新特定类别的知识"""
        result = {
            'success': True,
            'new_entries': 0,
            'error': None
        }
        
        try:
            headers = {
                'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
            }
            
            for source in sources:
                try:
                    logger.info(f"从 {source} 获取 {category} 知识")
                    response = requests.get(source, headers=headers, timeout=10)
                    response.raise_for_status()
                    
                    # 解析内容
                    soup = BeautifulSoup(response.content, 'html.parser')
                    
                    # 根据不同网站提取知识
                    if 'python.org' in source:
                        entries = self._extract_python_knowledge(soup)
                    elif 'flask.palletsprojects.com' in source:
                        entries = self._extract_flask_knowledge(soup)
                    elif 'git-scm.com' in source:
                        entries = self._extract_git_knowledge(soup)
                    elif 'sqlite.org' in source:
                        entries = self._extract_sqlite_knowledge(soup)
                    elif 'stackoverflow.com' in source:
                        entries = self._extract_stackoverflow_knowledge(soup)
                    else:
                        entries = self._extract_generic_knowledge(soup)
                    
                    # 添加到知识库
                    for entry in entries[:5]:  # 限制数量
                        if self.add_knowledge(
                            category,
                            entry['title'],
                            entry['content'],
                            source,
                            entry.get('tags', [])
                        ):
                            result['new_entries'] += 1
                except Exception as e:
                    logger.warning(f"从 {source} 获取知识失败: {str(e)}")
                    continue
            
            return result
        except Exception as e:
            result['success'] = False
            result['error'] = str(e)
            return result
    
    # 知识提取方法
    
    def _extract_python_knowledge(self, soup: BeautifulSoup) -> List[Dict[str, Any]]:
        """从Python文档提取知识"""
        entries = []
        # 简单的提取逻辑
        for h2 in soup.find_all('h2', limit=5):
            title = h2.text.strip()
            content = ''
            next_sibling = h2.find_next_sibling()
            while next_sibling and next_sibling.name not in ['h2', 'h1']:
                content += next_sibling.text.strip() + '\n'
                next_sibling = next_sibling.find_next_sibling()
            
            if title and content:
                entries.append({
                    'title': title,
                    'content': content,
                    'tags': ['python', 'documentation']
                })
        return entries
    
    def _extract_flask_knowledge(self, soup: BeautifulSoup) -> List[Dict[str, Any]]:
        """从Flask文档提取知识"""
        entries = []
        for h2 in soup.find_all('h2', limit=5):
            title = h2.text.strip()
            content = ''
            next_sibling = h2.find_next_sibling()
            while next_sibling and next_sibling.name not in ['h2', 'h1']:
                content += next_sibling.text.strip() + '\n'
                next_sibling = next_sibling.find_next_sibling()
            
            if title and content:
                entries.append({
                    'title': title,
                    'content': content,
                    'tags': ['flask', 'web', 'framework']
                })
        return entries
    
    def _extract_git_knowledge(self, soup: BeautifulSoup) -> List[Dict[str, Any]]:
        """从Git文档提取知识"""
        entries = []
        for h2 in soup.find_all('h2', limit=5):
            title = h2.text.strip()
            content = ''
            next_sibling = h2.find_next_sibling()
            while next_sibling and next_sibling.name not in ['h2', 'h1']:
                content += next_sibling.text.strip() + '\n'
                next_sibling = next_sibling.find_next_sibling()
            
            if title and content:
                entries.append({
                    'title': title,
                    'content': content,
                    'tags': ['git', 'version-control']
                })
        return entries
    
    def _extract_sqlite_knowledge(self, soup: BeautifulSoup) -> List[Dict[str, Any]]:
        """从SQLite文档提取知识"""
        entries = []
        for h2 in soup.find_all('h2', limit=5):
            title = h2.text.strip()
            content = ''
            next_sibling = h2.find_next_sibling()
            while next_sibling and next_sibling.name not in ['h2', 'h1']:
                content += next_sibling.text.strip() + '\n'
                next_sibling = next_sibling.find_next_sibling()
            
            if title and content:
                entries.append({
                    'title': title,
                    'content': content,
                    'tags': ['sqlite', 'database']
                })
        return entries
    
    def _extract_stackoverflow_knowledge(self, soup: BeautifulSoup) -> List[Dict[str, Any]]:
        """从Stack Overflow提取知识"""
        entries = []
        for question in soup.find_all('div', class_='question-summary', limit=5):
            title_elem = question.find('h3')
            if title_elem:
                title = title_elem.text.strip()
                content_elem = question.find('div', class_='excerpt')
                content = content_elem.text.strip() if content_elem else ''
                
                if title and content:
                    entries.append({
                        'title': title,
                        'content': content,
                        'tags': ['stackoverflow', 'question']
                    })
        return entries
    
    def _extract_generic_knowledge(self, soup: BeautifulSoup) -> List[Dict[str, Any]]:
        """提取通用知识"""
        entries = []
        for h2 in soup.find_all('h2', limit=5):
            title = h2.text.strip()
            content = ''
            next_sibling = h2.find_next_sibling()
            while next_sibling and next_sibling.name not in ['h2', 'h1']:
                content += next_sibling.text.strip() + '\n'
                next_sibling = next_sibling.find_next_sibling()
            
            if title and content:
                entries.append({
                    'title': title,
                    'content': content,
                    'tags': ['general']
                })
        return entries
    
    # 学习历史方法
    
    def _record_learning_history(self, action: str, details: Dict[str, Any]):
        """记录学习历史"""
        history_entry = {
            'action': action,
            'details': details,
            'timestamp': datetime.now().isoformat()
        }
        self.learning_history.append(history_entry)
        
        # 限制历史记录数量
        if len(self.learning_history) > 1000:
            self.learning_history = self.learning_history[-1000:]
    
    def get_learning_history(self, limit: int = 50) -> List[Dict[str, Any]]:
        """获取学习历史"""
        return self.learning_history[-limit:]
    
    # 统计方法
    
    def get_statistics(self) -> Dict[str, Any]:
        """获取知识库统计信息"""
        try:
            stats = {
                'total_entries': self.knowledge_base['total_entries'],
                'categories': {},
                'last_updated': self.knowledge_base['last_updated'],
                'learning_history_count': len(self.learning_history),
                'sources_count': {}
            }
            
            # 按类别统计
            for category_id, category_info in self.knowledge_base['categories'].items():
                stats['categories'][category_id] = {
                    'name': category_info['name'],
                    'entry_count': len(category_info.get('entries', {})),
                    'description': category_info['description']
                }
            
            # 按来源统计
            for category, sources in self.knowledge_sources.items():
                stats['sources_count'][category] = len(sources)
            
            return stats
        except Exception as e:
            logger.error(f"获取统计信息失败: {str(e)}")
            return {}

# 创建全局AI知识库实例
ai_knowledge_base = AIKnowledgeBase()

if __name__ == '__main__':
    print("AI知识库初始化成功")
    print(f"知识类别数量: {len(ai_knowledge_base.knowledge_base['categories'])}")
    print(f"总知识条目: {ai_knowledge_base.knowledge_base['total_entries']}")
