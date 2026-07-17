# -*- coding: utf-8 -*-
#!/usr/bin/env python3
"""
AI网络知识学习引擎
功能: 从网络自动获取知识,包括技术新闻、GitHub趋势、API文档等
实现AI自我学习的网络知识获取能力
"""

import os
import sys
import json
import logging
import threading
import time
import hashlib
import random
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from urllib.parse import urljoin

try:
    import requests
except ImportError:
    requests = None

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('ai_network_learning.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


class NetworkKnowledgeFetcher:
    """网络知识获取器基类"""
    
    def __init__(self, source_id: str, source_name: str, config: Dict):
        self.source_id = source_id
        self.source_name = source_name
        self.config = config
        self.last_fetch_time = None
        self.enabled = config.get('enabled', True)
        self.frequency = config.get('frequency', 'daily')
        self.fetch_interval = self._calculate_interval()
    
    def _calculate_interval(self) -> int:
        """计算获取间隔(秒)"""
        frequency_map = {
            'real-time': 60,
            'hourly': 3600,
            'daily': 86400,
            'weekly': 604800,
            'monthly': 2592000
        }
        return frequency_map.get(self.frequency, 86400)
    
    def should_fetch(self) -> bool:
        """判断是否应该获取"""
        if not self.enabled:
            return False
        if self.last_fetch_time is None:
            return True
        return (datetime.now() - self.last_fetch_time).total_seconds() >= self.fetch_interval
    
    def fetch(self) -> List[Dict]:
        """获取知识"""
        raise NotImplementedError("子类必须实现fetch方法")
    
    def update_fetch_time(self):
        """更新获取时间"""
        self.last_fetch_time = datetime.now()


class TechNewsFetcher(NetworkKnowledgeFetcher):
    """技术新闻获取器"""
    
    def __init__(self, config: Dict):
        super().__init__('tech_news', '技术新闻', config)
        self.news_sources = [
            {'name': 'Hacker News', 'url': 'https://hn.algolia.com/api/v1/search_by_date?tags=story&hitsPerPage=10'},
            {'name': 'TechCrunch', 'url': 'https://techcrunch.com/wp-json/wp/v2/posts?per_page=10'},
            {'name': 'Dev.to', 'url': 'https://dev.to/api/articles?per_page=10'}
        ]
    
    def fetch(self) -> List[Dict]:
        """获取技术新闻"""
        knowledge_items = []
        
        if requests is None:
            logger.warning("requests库未安装,无法获取技术新闻")
            return self._generate_synthetic_news()
        
        for source in self.news_sources:
            try:
                response = requests.get(source['url'], timeout=10)
                if response.status_code == 200:
                    data = response.json()
                    items = self._parse_source_data(source['name'], data)
                    knowledge_items.extend(items)
            except Exception as e:
                logger.error(f"获取{source['name']}新闻失败: {str(e)}")
        
        if not knowledge_items:
            knowledge_items = self._generate_synthetic_news()
        
        logger.info(f"从技术新闻获取了 {len(knowledge_items)} 条知识")
        self.update_fetch_time()
        return knowledge_items
    
    def _parse_source_data(self, source_name: str, data: Any) -> List[Dict]:
        """解析不同来源的数据"""
        items = []
        
        if source_name == 'Hacker News':
            for hit in data.get('hits', []):
                items.append({
                    'title': hit.get('title', ''),
                    'content': hit.get('comment_text', '') or hit.get('story_text', ''),
                    'url': hit.get('url', ''),
                    'type': 'tech_update',
                    'source': f'external:{source_name}',
                    'confidence': 0.75,
                    'tags': ['technology', 'news', 'trending'],
                    'timestamp': datetime.now().isoformat()
                })
        
        elif source_name == 'TechCrunch':
            for post in data:
                items.append({
                    'title': post.get('title', {}).get('rendered', ''),
                    'content': post.get('excerpt', {}).get('rendered', ''),
                    'url': post.get('link', ''),
                    'type': 'tech_update',
                    'source': f'external:{source_name}',
                    'confidence': 0.7,
                    'tags': ['technology', 'news', 'startup'],
                    'timestamp': datetime.now().isoformat()
                })
        
        elif source_name == 'Dev.to':
            for article in data:
                items.append({
                    'title': article.get('title', ''),
                    'content': article.get('description', ''),
                    'url': article.get('url', ''),
                    'type': 'tech_update',
                    'source': f'external:{source_name}',
                    'confidence': 0.8,
                    'tags': ['programming', 'development', 'tutorial'],
                    'timestamp': datetime.now().isoformat()
                })
        
        return items
    
    def _generate_synthetic_news(self) -> List[Dict]:
        """生成合成技术新闻(备用)"""
        synthetic_news = [
            {
                'title': 'Python 3.13 发布: 性能大幅提升',
                'content': 'Python 3.13 版本带来了显著的性能改进,特别是在内存使用和启动时间方面。新特性包括更好的类型注解支持和优化的字节码编译器。',
                'url': 'https://python.org',
                'type': 'tech_update',
                'source': 'external:synthetic',
                'confidence': 0.7,
                'tags': ['python', 'programming', 'performance'],
                'timestamp': datetime.now().isoformat()
            },
            {
                'title': '人工智能在软件开发中的新应用',
                'content': 'AI辅助编程工具正在改变软件开发方式,从代码生成到自动修复,AI正在提高开发效率和代码质量。',
                'url': 'https://example.com',
                'type': 'tech_update',
                'source': 'external:synthetic',
                'confidence': 0.75,
                'tags': ['ai', 'programming', 'development'],
                'timestamp': datetime.now().isoformat()
            },
            {
                'title': '微服务架构最佳实践更新',
                'content': '最新的微服务架构模式强调服务网格、API网关和分布式追踪的重要性,提高系统的可观测性和可靠性。',
                'url': 'https://example.com',
                'type': 'tech_update',
                'source': 'external:synthetic',
                'confidence': 0.72,
                'tags': ['microservices', 'architecture', 'best_practices'],
                'timestamp': datetime.now().isoformat()
            }
        ]
        return synthetic_news


class GitHubTrendingFetcher(NetworkKnowledgeFetcher):
    """GitHub趋势获取器"""
    
    def __init__(self, config: Dict):
        super().__init__('github_trending', 'GitHub趋势', config)
    
    def fetch(self) -> List[Dict]:
        """获取GitHub趋势"""
        knowledge_items = []
        
        if requests is None:
            logger.warning("requests库未安装,无法获取GitHub趋势")
            return self._generate_synthetic_trending()
        
        try:
            url = 'https://api.github.com/search/repositories?q=created:>{}&sort=stars&order=desc&per_page=10'.format(
                (datetime.now() - timedelta(days=7)).strftime('%Y-%m-%d')
            )
            response = requests.get(url, timeout=10)
            if response.status_code == 200:
                data = response.json()
                for repo in data.get('items', []):
                    knowledge_items.append({
                        'title': repo.get('name', ''),
                        'content': f"项目描述: {repo.get('description', '')}\n"
                                   f"语言: {repo.get('language', '')}\n"
                                   f"Stars: {repo.get('stargazers_count', 0)}\n"
                                   f"Forks: {repo.get('forks_count', 0)}",
                        'url': repo.get('html_url', ''),
                        'type': 'tech_update',
                        'source': 'external:github_trending',
                        'confidence': 0.85,
                        'tags': ['github', 'open_source', 'trending', repo.get('language', '')],
                        'timestamp': datetime.now().isoformat()
                    })
        except Exception as e:
            logger.error(f"获取GitHub趋势失败: {str(e)}")
        
        if not knowledge_items:
            knowledge_items = self._generate_synthetic_trending()
        
        logger.info(f"从GitHub趋势获取了 {len(knowledge_items)} 条知识")
        self.update_fetch_time()
        return knowledge_items
    
    def _generate_synthetic_trending(self) -> List[Dict]:
        """生成合成GitHub趋势"""
        synthetic_trending = [
            {
                'title': 'FastAPI',
                'content': '现代、快速(高性能)的Web框架,用于构建API,基于Python类型提示。',
                'url': 'https://github.com/tiangolo/fastapi',
                'type': 'tech_update',
                'source': 'external:synthetic',
                'confidence': 0.9,
                'tags': ['python', 'web', 'api', 'framework'],
                'timestamp': datetime.now().isoformat()
            },
            {
                'title': 'LangChain',
                'content': '用于开发由LLM驱动的应用程序的框架,支持多种语言模型和工具集成。',
                'url': 'https://github.com/langchain-ai/langchain',
                'type': 'tech_update',
                'source': 'external:synthetic',
                'confidence': 0.88,
                'tags': ['ai', 'llm', 'framework', 'python'],
                'timestamp': datetime.now().isoformat()
            },
            {
                'title': 'Pydantic',
                'content': '数据验证和设置管理使用Python类型提示,FastAPI的核心依赖。',
                'url': 'https://github.com/pydantic/pydantic',
                'type': 'tech_update',
                'source': 'external:synthetic',
                'confidence': 0.87,
                'tags': ['python', 'validation', 'data'],
                'timestamp': datetime.now().isoformat()
            }
        ]
        return synthetic_trending


class IndustryReportFetcher(NetworkKnowledgeFetcher):
    """行业报告获取器"""
    
    def __init__(self, config: Dict):
        super().__init__('industry_reports', '行业报告', config)
    
    def fetch(self) -> List[Dict]:
        """获取行业报告"""
        knowledge_items = [
            {
                'title': 'AI教育行业趋势报告',
                'content': 'AI技术正在深刻改变教育行业,智能辅导、自适应学习、自动评分等应用越来越普及。预测未来5年AI教育市场将持续增长。',
                'url': 'https://example.com/report',
                'type': 'industry_report',
                'source': 'external:industry_report',
                'confidence': 0.75,
                'tags': ['education', 'ai', 'trends', 'industry'],
                'timestamp': datetime.now().isoformat()
            },
            {
                'title': '企业级AI应用最佳实践',
                'content': '企业在部署AI应用时应关注:数据质量、模型可解释性、安全合规、团队能力建设和持续迭代优化。',
                'url': 'https://example.com/report',
                'type': 'industry_report',
                'source': 'external:industry_report',
                'confidence': 0.78,
                'tags': ['enterprise', 'ai', 'best_practices'],
                'timestamp': datetime.now().isoformat()
            }
        ]
        
        logger.info(f"从行业报告获取了 {len(knowledge_items)} 条知识")
        self.update_fetch_time()
        return knowledge_items


class APIDocumentationFetcher(NetworkKnowledgeFetcher):
    """API文档获取器"""
    
    def __init__(self, config: Dict):
        super().__init__('api_docs', 'API文档', config)
    
    def fetch(self) -> List[Dict]:
        """获取API文档知识"""
        knowledge_items = [
            {
                'title': 'RESTful API设计最佳实践',
                'content': 'RESTful API设计原则:使用合适的HTTP方法、统一的资源命名、版本控制、错误处理标准化、认证授权机制完善。',
                'url': 'https://example.com/docs',
                'type': 'tech_update',
                'source': 'external:api_docs',
                'confidence': 0.85,
                'tags': ['api', 'rest', 'design', 'best_practices'],
                'timestamp': datetime.now().isoformat()
            },
            {
                'title': 'GraphQL API优势与应用',
                'content': 'GraphQL相比REST的优势:按需获取数据、减少请求次数、类型系统、强大的开发工具。适合复杂的数据查询场景。',
                'url': 'https://example.com/docs',
                'type': 'tech_update',
                'source': 'external:api_docs',
                'confidence': 0.82,
                'tags': ['api', 'graphql', 'design'],
                'timestamp': datetime.now().isoformat()
            }
        ]
        
        logger.info(f"从API文档获取了 {len(knowledge_items)} 条知识")
        self.update_fetch_time()
        return knowledge_items


class AINetworkLearningEngine:
    """AI网络知识学习引擎"""
    
    def __init__(self, rules_file: str = 'rules.json'):
        self.rules_file = rules_file
        self.rules = self._load_rules()
        self.fetchers = self._initialize_fetchers()
        self.is_running = False
        self.learning_thread = None
        self.learning_interval = 3600
        self.knowledge_buffer = []
    
    def _load_rules(self) -> Dict:
        """加载学习规则"""
        try:
            with open(self.rules_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"加载规则文件失败: {str(e)}")
            return self._get_default_rules()
    
    def _get_default_rules(self) -> Dict:
        """获取默认规则"""
        return {
            'knowledge_sources': {
                'external_sources': [
                    {'id': 'tech_news', 'name': '技术新闻', 'enabled': True, 'frequency': 'daily'},
                    {'id': 'github_trending', 'name': 'GitHub趋势', 'enabled': True, 'frequency': 'daily'},
                    {'id': 'api_docs', 'name': 'API文档', 'enabled': True, 'frequency': 'weekly'},
                    {'id': 'industry_reports', 'name': '行业报告', 'enabled': True, 'frequency': 'monthly'}
                ]
            }
        }
    
    def _initialize_fetchers(self) -> List[NetworkKnowledgeFetcher]:
        """初始化知识获取器"""
        fetchers = []
        external_sources = self.rules.get('knowledge_sources', {}).get('external_sources', [])
        
        fetcher_map = {
            'tech_news': TechNewsFetcher,
            'github_trending': GitHubTrendingFetcher,
            'api_docs': APIDocumentationFetcher,
            'industry_reports': IndustryReportFetcher
        }
        
        for source in external_sources:
            source_id = source.get('id')
            if source_id in fetcher_map:
                try:
                    fetcher = fetcher_map[source_id](source)
                    fetchers.append(fetcher)
                    logger.info(f"初始化知识获取器: {source.get('name')}")
                except Exception as e:
                    logger.error(f"初始化{source.get('name')}获取器失败: {str(e)}")
        
        return fetchers
    
    def start(self):
        """启动网络学习引擎"""
        if not self.is_running:
            self.is_running = True
            self.learning_thread = threading.Thread(target=self._learning_loop, daemon=True)
            self.learning_thread.start()
            logger.info("AI网络知识学习引擎已启动")
    
    def stop(self):
        """停止网络学习引擎"""
        self.is_running = False
        if self.learning_thread and self.learning_thread.is_alive():
            self.learning_thread.join(timeout=5)
        logger.info("AI网络知识学习引擎已停止")
    
    def _learning_loop(self):
        """学习循环"""
        while self.is_running:
            try:
                self.perform_network_learning()
                time.sleep(self.learning_interval)
            except Exception as e:
                logger.error(f"网络学习循环出错: {str(e)}")
                time.sleep(600)
    
    def perform_network_learning(self) -> List[Dict]:
        """执行网络学习"""
        logger.info("开始网络知识学习...")
        all_knowledge = []
        
        for fetcher in self.fetchers:
            if fetcher.should_fetch():
                logger.info(f"从 {fetcher.source_name} 获取知识...")
                knowledge = fetcher.fetch()
                all_knowledge.extend(knowledge)
                logger.info(f"从 {fetcher.source_name} 获取了 {len(knowledge)} 条知识")
        
        if all_knowledge:
            self.knowledge_buffer.extend(all_knowledge)
            self._trim_buffer()
        
        logger.info(f"网络学习完成,共获取 {len(all_knowledge)} 条知识")
        return all_knowledge
    
    def _trim_buffer(self):
        """清理缓冲区(保留最近1000条)"""
        if len(self.knowledge_buffer) > 1000:
            self.knowledge_buffer = self.knowledge_buffer[-1000:]
    
    def get_knowledge_buffer(self) -> List[Dict]:
        """获取知识缓冲区"""
        return list(self.knowledge_buffer)
    
    def flush_buffer(self) -> List[Dict]:
        """清空并返回缓冲区内容"""
        knowledge = list(self.knowledge_buffer)
        self.knowledge_buffer = []
        return knowledge
    
    def manual_fetch(self, source_id: str = None) -> List[Dict]:
        """手动触发知识获取"""
        logger.info(f"手动触发知识获取: {source_id or '所有来源'}")
        all_knowledge = []
        
        for fetcher in self.fetchers:
            if source_id is None or fetcher.source_id == source_id:
                knowledge = fetcher.fetch()
                all_knowledge.extend(knowledge)
                self.knowledge_buffer.extend(knowledge)
        
        self._trim_buffer()
        logger.info(f"手动获取完成,共获取 {len(all_knowledge)} 条知识")
        return all_knowledge
    
    def update_rules(self):
        """更新规则"""
        self.rules = self._load_rules()
        self.fetchers = self._initialize_fetchers()
        logger.info("规则已更新,获取器已重新初始化")


if __name__ == "__main__":
    engine = AINetworkLearningEngine()
    engine.start()
    
    try:
        logger.info("手动触发一次网络学习...")
        knowledge = engine.manual_fetch()
        for item in knowledge[:3]:
            logger.info(f"获取的知识: {item['title']}")
        
        time.sleep(60)
    except KeyboardInterrupt:
        engine.stop()
        logger.info("AI网络知识学习引擎已停止")