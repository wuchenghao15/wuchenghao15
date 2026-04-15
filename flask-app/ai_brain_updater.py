#!/usr/bin/env python3
"""
AI脑库自动更新脚本
从网络上爬取学习案例适配方法和成功案例，自动更新AI脑库

该脚本是项目的核心脚本，负责AI脑库的自动更新和维护
"""

import os
import sys
import json
from datetime import datetime
import logging
import time
import uuid
from urllib.parse import urljoin, urlparse
from typing import List, Dict, Any, Optional
import argparse
import configparser
from concurrent.futures import ThreadPoolExecutor, as_completed

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# 配置独立日志系统，完全不依赖项目模块
logger = logging.getLogger('ai_brain_updater')
logger.setLevel(logging.INFO)

# 创建文件处理器
file_handler = logging.FileHandler('ai_brain_updater.log')
file_handler.setLevel(logging.INFO)

# 创建控制台处理器
console_handler = logging.StreamHandler()
console_handler.setLevel(logging.INFO)

# 设置日志格式
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
file_handler.setFormatter(formatter)
console_handler.setFormatter(formatter)

# 清空现有的处理器，避免重复日志
logger.handlers.clear()
logger.addHandler(file_handler)
logger.addHandler(console_handler)

# 确保logger不会传播到根日志器
logger.propagate = False

# 完全不使用项目配置系统，始终使用独立配置
try:
    # 尝试从配置文件加载配置
    config_file = 'ai_brain_updater.conf'
    config_parser = configparser.ConfigParser()
    if os.path.exists(config_file):
        config_parser.read(config_file, encoding='utf-8')
        logger.info(f"已从配置文件 {config_file} 加载配置")
    else:
        logger.info(f"未找到配置文件 {config_file}，将使用默认配置")
    
    # 创建简单的配置服务
    class SimpleConfigService:
        def __init__(self):
            # 默认配置
            self.config = {
                'ai_brain': {
                    'update_interval_hours': 24,
                    'max_workers': 4,
                    'sources': [
                        {
                            'name': 'AI案例库',
                            'url': 'https://ai.example.com/cases',
                            'type': 'case_study',
                            'parser': 'parse_demo_cases'
                        }
                    ]
                }
            }
            
            # 从配置文件更新配置
            if 'ai_brain' in config_parser:
                ai_brain_config = dict(config_parser['ai_brain'])
                
                # 更新整数配置
                for key in ['max_workers', 'update_interval_hours']:
                    if key in ai_brain_config:
                        try:
                            self.config['ai_brain'][key] = int(ai_brain_config[key])
                        except ValueError:
                            logger.warning(f"配置项 {key} 的值无效，将使用默认值")
        
        def get(self, section, key, default=None):
            return self.config.get(section, {}).get(key, default)
    
    config_service = SimpleConfigService()
    USE_PROJECT_CONFIG = False
    logger.info("已初始化独立配置服务")
except Exception as e:
    logger.error(f"初始化配置服务失败: {str(e)}")
    
    # 使用硬编码的默认配置作为最后的回退
    class FallbackConfigService:
        def get(self, section, key, default=None):
            return default
    
    config_service = FallbackConfigService()
    USE_PROJECT_CONFIG = False
    logger.warning("已回退到最简单的配置服务")

# 尝试导入可选的网络爬取库
try:
    import requests
    from bs4 import BeautifulSoup
    HAS_WEB_CRAWLING = True
    logger.debug("已成功导入网络爬取库")
except ImportError:
    HAS_WEB_CRAWLING = False
    requests = None
    BeautifulSoup = None
    logger.warning("未找到requests和beautifulsoup4库，将使用演示数据")

class AIBrainUpdater:
    """AI脑库自动更新器"""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """初始化更新器
        
        Args:
            config: 配置字典，覆盖默认配置
        """
        self.config = config or {}
        self.max_workers = self.config.get('max_workers', config_service.get('ai_brain', 'max_workers', 4))
        
        # 只有在web crawling可用时才初始化请求会话
        if HAS_WEB_CRAWLING and requests is not None:
            self.session = requests.Session()
            self.session.headers.update({
                'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
            })
        else:
            self.session = None
        
        # 数据源配置
        self.data_sources = self.config.get('sources', config_service.get('ai_brain', 'sources', []))
        
        # 统计信息
        self.stats = {
            'total_sources': len(self.data_sources),
            'processed_sources': 0,
            'total_items': 0,
            'added_items': 0,
            'failed_sources': 0,
            'start_time': datetime.now()
        }
        
    def fetch_page(self, url: str, timeout: int = 10) -> Optional[str]:
        """获取网页内容
        
        Args:
            url: 要获取的网页URL
            timeout: 请求超时时间（秒）
            
        Returns:
            网页内容字符串，如果获取失败或web crawling不可用则返回None
        """
        # 如果web crawling不可用，直接返回None
        if not HAS_WEB_CRAWLING or self.session is None or requests is None:
            logger.info(f"跳过网页获取，因为web crawling不可用: {url}")
            return None
        
        try:
            response = self.session.get(url, timeout=timeout)
            response.raise_for_status()
            return response.text
        except requests.exceptions.ConnectionError as e:
            logger.error(f"连接失败 {url}: {str(e)}")
            return None
        except requests.exceptions.Timeout as e:
            logger.error(f"超时失败 {url}: {str(e)}")
            return None
        except requests.exceptions.HTTPError as e:
            logger.error(f"HTTP错误 {url}: {str(e)}")
            return None
        except Exception as e:
            logger.error(f"获取页面失败 {url}: {str(e)}")
            return None
    
    def parse_csdn_ai(self, html: str, source: Dict[str, Any]) -> List[Dict[str, Any]]:
        """解析CSDN AI专栏
        
        Args:
            html: CSDN AI专栏页面HTML内容
            source: 数据源配置
            
        Returns:
            解析后的文章列表
        """
        soup = BeautifulSoup(html, 'html.parser')
        articles = []
        
        # 查找所有文章
        article_elements = soup.find_all('article', class_='blog-list-box')
        logger.debug(f"从CSDN找到 {len(article_elements)} 篇文章")
        
        for article in article_elements:
            try:
                title_tag = article.find('h4', class_='blog-list-box-title')
                if not title_tag:
                    continue
                    
                title = title_tag.text.strip()
                link_tag = title_tag.find('a')
                if not link_tag:
                    continue
                    
                link = link_tag['href']
                
                # 获取文章详情
                detail_html = self.fetch_page(link)
                if detail_html:
                    detail_soup = BeautifulSoup(detail_html, 'html.parser')
                    content_tag = detail_soup.find('div', id='articleContentId')
                    if content_tag:
                        content = content_tag.text.strip()
                        articles.append({
                            'title': title,
                            'content': content,
                            'url': link,
                            'knowledge_type': 'case_study',
                            'source': source['name']
                        })
            except Exception as e:
                logger.error(f"解析CSDN文章失败: {str(e)}")
                continue
        
        logger.info(f"从CSDN解析了 {len(articles)} 篇有效文章")
        return articles
    
    def parse_zhihu_ai(self, html: str, source: Dict[str, Any]) -> List[Dict[str, Any]]:
        """解析知乎AI话题
        
        Args:
            html: 知乎AI话题页面HTML内容
            source: 数据源配置
            
        Returns:
            解析后的回答列表
        """
        soup = BeautifulSoup(html, 'html.parser')
        answers = []
        
        # 查找所有回答
        answer_elements = soup.find_all('div', class_='List-item')
        logger.debug(f"从知乎找到 {len(answer_elements)} 个回答")
        
        for answer in answer_elements:
            try:
                title_tag = answer.find('h2', class_='ContentItem-title')
                if not title_tag:
                    continue
                    
                title = title_tag.text.strip()
                content_tag = answer.find('div', class_='RichContent-inner')
                if not content_tag:
                    continue
                    
                content = content_tag.text.strip()
                link_tag = answer.find('a', class_='ContentItem-title')
                link = link_tag['href'] if link_tag else source['url']
                
                answers.append({
                    'title': title,
                    'content': content,
                    'url': urljoin(source['url'], link),
                    'knowledge_type': 'method',
                    'source': source['name']
                })
            except Exception as e:
                logger.error(f"解析知乎回答失败: {str(e)}")
                continue
        
        logger.info(f"从知乎解析了 {len(answers)} 个有效回答")
        return answers
    
    def parse_yanxishe(self, html: str, source: Dict[str, Any]) -> List[Dict[str, Any]]:
        """解析AI研习社
        
        Args:
            html: AI研习社页面HTML内容
            source: 数据源配置
            
        Returns:
            解析后的文章列表
        """
        soup = BeautifulSoup(html, 'html.parser')
        articles = []
        
        # 查找所有文章
        article_elements = soup.find_all('div', class_='course-item')
        logger.debug(f"从AI研习社找到 {len(article_elements)} 篇文章")
        
        for article in article_elements:
            try:
                title_tag = article.find('h3', class_='course-title')
                if not title_tag:
                    continue
                    
                title = title_tag.text.strip()
                link_tag = title_tag.find('a')
                if not link_tag:
                    continue
                    
                link = link_tag['href']
                full_link = urljoin(source['url'], link)
                
                # 获取文章详情
                detail_html = self.fetch_page(full_link)
                if detail_html:
                    detail_soup = BeautifulSoup(detail_html, 'html.parser')
                    content_tag = detail_soup.find('div', class_='course-detail-content')
                    if content_tag:
                        content = content_tag.text.strip()
                        articles.append({
                            'title': title,
                            'content': content,
                            'url': full_link,
                            'knowledge_type': 'method',
                            'source': source['name']
                        })
            except Exception as e:
                logger.error(f"解析AI研习社文章失败: {str(e)}")
                continue
        
        logger.info(f"从AI研习社解析了 {len(articles)} 篇有效文章")
        return articles
    
    def parse_demo_cases(self, html: Optional[str], source: Dict[str, Any]) -> List[Dict[str, Any]]:
        """解析演示案例数据
        
        Args:
            html: 页面HTML内容（未使用）
            source: 数据源配置
            
        Returns:
            演示案例列表
        """
        # 演示数据，模拟从网络获取的案例
        demo_cases = [
            {
                'title': 'AI学习案例适配方法',
                'content': 'AI学习案例适配是指将已有的AI案例适配到不同的应用场景中。主要包括以下步骤：1. 分析原案例的核心技术点；2. 评估目标场景的适配性；3. 调整模型和算法；4. 测试和验证。通过这种方法，可以快速将成熟的AI案例应用到新的场景中，提高开发效率。',
                'url': source['url'],
                'knowledge_type': 'method',
                'source': source['name']
            },
            {
                'title': 'AI智能升级脑库成功案例',
                'content': '某企业通过AI智能升级脑库，实现了以下成果：1. 知识库容量提升50%；2. 知识检索准确率达到95%；3. 智能推荐系统的点击率提升30%。该案例采用了自动化爬取和智能分类技术，实现了脑库的持续更新和优化。',
                'url': source['url'],
                'knowledge_type': 'case_study',
                'source': source['name']
            },
            {
                'title': '机器学习模型适配技术',
                'content': '机器学习模型适配技术包括模型压缩、迁移学习和联邦学习等。模型压缩可以减小模型体积，提高部署效率；迁移学习可以将预训练模型应用到新的任务中；联邦学习可以在保护数据隐私的前提下进行模型训练。这些技术可以帮助企业快速将AI模型部署到不同的设备和场景中。',
                'url': source['url'],
                'knowledge_type': 'method',
                'source': source['name']
            },
            {
                'title': 'AI脑库自动更新系统',
                'content': 'AI脑库自动更新系统采用了定时爬虫和智能分析技术，可以从网络上自动获取最新的AI知识和案例，并将其添加到脑库中。该系统具有以下特点：1. 支持多种数据源；2. 自动去重和分类；3. 智能提取关键信息；4. 自动更新和优化。通过这种方式，可以确保AI脑库始终保持最新的状态。',
                'url': source['url'],
                'knowledge_type': 'case_study',
                'source': source['name']
            },
            {
                'title': 'Python技术爬取在AI脑库中的应用',
                'content': 'Python技术爬取是AI脑库自动更新的核心技术之一。通过使用requests和BeautifulSoup等库，可以从互联网上高效地获取各种AI相关的技术文章、案例和方法。这些内容经过处理后，可以丰富AI脑库的知识储备，提高AI系统的智能水平。',
                'url': source['url'],
                'knowledge_type': 'method',
                'source': source['name']
            }
        ]
        
        logger.info(f"使用演示数据生成了 {len(demo_cases)} 个案例")
        return demo_cases
    
    def extract_tags(self, content: str) -> List[str]:
        """从内容中提取标签
        
        Args:
            content: 文本内容
            
        Returns:
            提取的标签列表，最多5个
        """
        # 扩展关键词列表
        keywords = [
            'AI', '机器学习', '深度学习', '案例', '方法', '适配', '升级', '智能', '技术',
            'Python', '爬虫', '自动化', '脑库', '数据', '算法', '模型', '训练', '部署',
            '自然语言处理', '计算机视觉', '推荐系统', '知识图谱'
        ]
        
        tags = []
        content_lower = content.lower()
        
        for keyword in keywords:
            if keyword in content or keyword.lower() in content_lower:
                tags.append(keyword)
        
        # 去重并限制最多5个标签
        unique_tags = list(set(tags))
        return unique_tags[:5]
    
    def update_brain(self, knowledge_items: List[Dict[str, Any]], dry_run: bool = False) -> int:
        """更新AI脑库
        
        Args:
            knowledge_items: 要添加的知识项列表
            dry_run: 是否为模拟运行模式，不实际更新数据库
            
        Returns:
            成功添加的知识项数量
        """
        # 如果是模拟运行模式，直接返回知识项数量
        if dry_run:
            logger.info(f"模拟运行模式，跳过实际数据库更新，将添加 {len(knowledge_items)} 条知识项")
            self.stats['added_items'] = len(knowledge_items)
            return len(knowledge_items)
        
        try:
            from app.models.ai_brain import AIBrainKnowledge
            from app.models.ai_brain import AIBrainActivity
            from uuid import uuid4
            
            added_count = 0
            total_items = len(knowledge_items)
            logger.info(f"准备更新AI脑库，共 {total_items} 条知识项")
            
            for i, item in enumerate(knowledge_items):
                # 进度日志
                if (i + 1) % 10 == 0 or (i + 1) == total_items:
                    logger.info(f"处理进度: {i + 1}/{total_items}")
                
                try:
                    # 检查是否已存在
                    existing = AIBrainKnowledge.search(item['title'])
                    if not existing:
                        # 创建新知识
                        knowledge = AIBrainKnowledge(
                            knowledge_id=f"knowledge-{uuid4().hex[:8]}",
                            title=item['title'],
                            content=item['content'],
                            knowledge_type=item['knowledge_type'],
                            source=item['source'],
                            source_id=item['url'],
                            tags=self.extract_tags(item['content']),
                            priority=5,
                            is_active=True
                        )
                        knowledge.save()
                        added_count += 1
                        
                        # 记录活动日志
                        activity = AIBrainActivity(
                            activity_type='knowledge_added',
                            description=f"添加新知识: {item['title']}",
                            source=item['source'],
                            source_id=item['url']
                        )
                        activity.save()
                except Exception as e:
                    logger.error(f"处理知识项失败 [{i + 1}/{total_items}]: {str(e)}")
                    continue
            
            logger.info(f"成功添加 {added_count} 条新知识，跳过 {total_items - added_count} 条已存在的知识")
            self.stats['added_items'] = added_count
            return added_count
        except ImportError as e:
            logger.error(f"导入AI脑库模型失败: {str(e)}")
            return 0
        except Exception as e:
            logger.error(f"更新AI脑库失败: {str(e)}")
            return 0
    
    def _process_source(self, source: Dict[str, Any]) -> List[Dict[str, Any]]:
        """处理单个数据源
        
        Args:
            source: 数据源配置
            
        Returns:
            从该数据源获取的知识项列表
        """
        logger.info(f"正在处理数据源: {source['name']}")
        
        try:
            # 获取页面内容
            html = self.fetch_page(source['url'])
            
            # 如果获取页面失败，使用演示数据
            if not html:
                logger.warning(f"获取页面失败，使用演示数据代替: {source['name']}")
                knowledge_items = self.parse_demo_cases(None, source)
            else:
                # 调用相应的解析函数
                parser_func = getattr(self, source['parser'], self.parse_demo_cases)
                knowledge_items = parser_func(html, source)
            
            logger.info(f"从 {source['name']} 成功获取了 {len(knowledge_items)} 条信息")
            self.stats['processed_sources'] += 1
            return knowledge_items
        except Exception as e:
            logger.error(f"处理数据源 {source['name']} 失败: {str(e)}")
            self.stats['failed_sources'] += 1
            return []
    
    def run(self, dry_run: bool = False) -> Dict[str, Any]:
        """运行更新器
        
        Args:
            dry_run: 是否为模拟运行模式，不实际更新数据库
            
        Returns:
            运行结果统计信息
        """
        logger.info("=== 开始AI脑库自动更新 ===")
        logger.info(f"运行模式: {'模拟运行' if dry_run else '实际运行'}")
        self.stats['start_time'] = datetime.now()
        self.stats['dry_run'] = dry_run
        
        all_knowledge = []
        
        if not self.data_sources:
            logger.warning("没有配置数据源，使用默认演示数据")
            default_demo = {
                'name': '默认演示数据',
                'url': 'https://ai.example.com/default'
            }
            all_knowledge = self.parse_demo_cases(None, default_demo)
        else:
            logger.info(f"开始处理 {len(self.data_sources)} 个数据源")
            
            # 使用并发处理数据源
            with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
                # 提交所有任务
                future_to_source = {executor.submit(self._process_source, source): source 
                                 for source in self.data_sources}
                
                # 收集结果
                for future in as_completed(future_to_source):
                    source = future_to_source[future]
                    try:
                        knowledge_items = future.result()
                        all_knowledge.extend(knowledge_items)
                    except Exception as e:
                        logger.error(f"处理数据源 {source['name']} 时发生异常: {str(e)}")
                        self.stats['failed_sources'] += 1
        
        # 统计获取的知识项数量
        self.stats['total_items'] = len(all_knowledge)
        logger.info(f"总共获取了 {self.stats['total_items']} 条知识项")
        
        # 更新AI脑库
        added_count = self.update_brain(all_knowledge, dry_run=dry_run)
        
        # 完成统计
        self.stats['end_time'] = datetime.now()
        self.stats['duration'] = self.stats['end_time'] - self.stats['start_time']
        
        # 生成详细报告
        self._generate_report()
        
        # 更新系统版本号
        try:
            import sqlite3
            import os
            
            # 获取数据库路径
            db_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'app.db')
            
            # 连接数据库
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            
            # 确保系统配置表存在
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS system_config (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    config_key TEXT UNIQUE NOT NULL,
                    config_value TEXT NOT NULL,
                    config_type TEXT NOT NULL DEFAULT 'string',
                    description TEXT DEFAULT '',
                    is_active INTEGER DEFAULT 1,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                    updated_at TEXT DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # 获取当前版本号
            current_version = '1.0.0'
            cursor.execute('SELECT config_value FROM system_config WHERE config_key=? AND is_active=1', ('system_version',))
            row = cursor.fetchone()
            if row:
                current_version = row[0]
            
            # 简单的版本号升级逻辑（可以根据实际需求修改）
            # 这里只是示例，实际可以根据更新内容或日期来更新版本号
            parts = current_version.split('.')
            if len(parts) >= 3:
                parts[-1] = str(int(parts[-1]) + 1)
                new_version = '.'.join(parts)
            else:
                new_version = f"{current_version}.1"
            
            # 更新版本号
            cursor.execute('''
                INSERT OR REPLACE INTO system_config 
                (config_key, config_value, config_type, description, is_active, updated_at)
                VALUES (?, ?, ?, ?, 1, CURRENT_TIMESTAMP)
            ''', ('system_version', new_version, 'string', '系统版本号'))
            
            # 提交更改
            conn.commit()
            conn.close()
            
            logger.info(f"系统版本号已更新: {current_version} -> {new_version}")
        except Exception as e:
            logger.error(f"更新系统版本号失败: {str(e)}")
        
        logger.info("=== AI脑库自动更新完成 ===")
        
        return self.stats
    
    def _generate_report(self) -> None:
        """生成运行报告"""
        report = f"""
        === AI脑库更新报告 ===
        开始时间: {self.stats['start_time']}
        结束时间: {self.stats['end_time']}
        持续时间: {self.stats['duration']}
        
        数据源统计:
        - 总数据源数: {self.stats['total_sources']}
        - 成功处理: {self.stats['processed_sources']}
        - 处理失败: {self.stats['failed_sources']}
        
        内容统计:
        - 总获取知识项: {self.stats['total_items']}
        - 成功添加到脑库: {self.stats['added_items']}
        - 重复跳过: {self.stats['total_items'] - self.stats['added_items']}
        
        处理效率:
        - 平均每个数据源耗时: {self.stats['duration'] / max(self.stats['total_sources'], 1)}
        - 平均每个知识项处理耗时: {self.stats['duration'] / max(self.stats['total_items'], 1)}
        """
        
        logger.info(report)
        
        # 将报告写入日志文件
        with open('ai_brain_update_report.log', 'a', encoding='utf-8') as f:
            f.write(report)
            f.write('\n' + '='*50 + '\n')
    
    def run_scheduled(self, interval_hours: int = 24) -> None:
        """定时运行更新器
        
        Args:
            interval_hours: 更新间隔时间（小时）
        """
        logger.info(f"=== 启动AI脑库定时更新服务，更新间隔: {interval_hours} 小时 ===")
        
        while True:
            try:
                self.run()
            except Exception as e:
                logger.error(f"定时更新执行失败: {str(e)}")
            
            next_update_time = datetime.now() + timedelta(hours=interval_hours)
            logger.info(f"下次更新将在 {next_update_time} 进行（{interval_hours} 小时后）")
            time.sleep(interval_hours * 3600)

def load_config(config_file: str) -> Dict[str, Any]:
    """加载配置文件
    
    Args:
        config_file: 配置文件路径
        
    Returns:
        配置字典
    """
    config = configparser.ConfigParser()
    config.read(config_file, encoding='utf-8')
    
    result = {}
    if 'ai_brain' in config:
        ai_brain_config = dict(config['ai_brain'])
        
        # 解析整数配置
        for key in ['max_workers', 'update_interval_hours']:
            if key in ai_brain_config:
                ai_brain_config[key] = int(ai_brain_config[key])
        
        result['ai_brain'] = ai_brain_config
    
    return result

def main():
    """主函数，处理命令行参数并执行相应操作"""
    parser = argparse.ArgumentParser(description='AI脑库自动更新脚本')
    
    # 核心功能参数
    parser.add_argument('--mode', '-m', choices=['once', 'scheduled'], default='once',
                      help='运行模式：once（单次运行）或 scheduled（定时运行）')
    
    # 配置参数
    parser.add_argument('--config', '-c', type=str, default=None,
                      help='配置文件路径')
    parser.add_argument('--max-workers', type=int, default=None,
                      help='并发工作线程数')
    parser.add_argument('--interval', '-i', type=int, default=None,
                      help='定时更新间隔（小时）')
    
    # 数据源参数
    parser.add_argument('--sources', '-s', type=str, default=None,
                      help='数据源配置文件路径')
    
    # 日志参数
    parser.add_argument('--log-level', type=str, choices=['DEBUG', 'INFO', 'WARNING', 'ERROR'],
                      default=None, help='日志级别')
    
    # 其他参数
    parser.add_argument('--dry-run', action='store_true',
                      help='模拟运行，不实际更新数据库')
    parser.add_argument('--verbose', '-v', action='store_true',
                      help='详细输出模式')
    
    args = parser.parse_args()
    
    # 设置日志级别
    if args.log_level:
        logger.setLevel(getattr(logging, args.log_level))
    elif args.verbose:
        logger.setLevel(logging.DEBUG)
    
    # 初始化更新器
    updater = AIBrainUpdater(config={})
    
    # 执行相应操作
    if args.mode == 'scheduled':
        # 获取更新间隔
        interval = args.interval or config_service.get('ai_brain', 'update_interval_hours', 24)
        updater.run_scheduled(interval)
    else:
        # 单次运行
        result = updater.run(dry_run=args.dry_run)
        
        # 打印结果摘要
        print("\n=== AI脑库更新结果摘要 ===")
        print(f"运行模式: {'模拟运行' if args.dry_run else '实际运行'}")
        print(f"总数据源: {result['total_sources']}")
        print(f"成功处理: {result['processed_sources']}")
        print(f"处理失败: {result['failed_sources']}")
        print(f"总获取知识项: {result['total_items']}")
        print(f"成功添加到脑库: {result['added_items']}")
        print(f"持续时间: {result['duration']}")
        print(f"开始时间: {result['start_time']}")
        print(f"结束时间: {result['end_time']}")

if __name__ == '__main__':
    from datetime import timedelta
    main()
