# -*- coding: utf-8 -*-
#!/usr/bin/env python3
"""
AI脑库自动更新脚本
从网络上爬取学习案例适配方法和成功案例,自动更新AI脑库

该脚本是项目的核心脚本,负责AI脑库的自动更新和维护
"""

import os
import sys
import json
from datetime import datetime, timedelta
import logging
import time
import uuid
from urllib.parse import urljoin, urlparse
from typing import List, Dict, Any, Optional
import argparse
import configparser
from concurrent.futures import ThreadPoolExecutor, as_completed

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

logger = logging.getLogger('ai_brain_updater')
logger.setLevel(logging.INFO)

file_handler = logging.FileHandler('ai_brain_updater.log')
file_handler.setLevel(logging.INFO)

console_handler = logging.StreamHandler()
console_handler.setLevel(logging.INFO)

formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
file_handler.setFormatter(formatter)
console_handler.setFormatter(formatter)

logger.handlers.clear()
logger.addHandler(file_handler)
logger.addHandler(console_handler)

logger.propagate = False

try:
    config_file = 'ai_brain_updater.conf'
    config_parser = configparser.ConfigParser()
    if os.path.exists(config_file):
        config_parser.read(config_file, encoding='utf-8')
        logger.info(f"已从配置文件 {config_file} 加载配置")
    else:
        logger.info(f"未找到配置文件 {config_file},将使用默认配置")

    class SimpleConfigService:
        def __init__(self):
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
            if 'ai_brain' in config_parser:
                ai_brain_config = dict(config_parser['ai_brain'])

                for key in ['max_workers', 'update_interval_hours']:
                    if key in ai_brain_config:
                        try:
                            ai_brain_config[key] = int(ai_brain_config[key])
                        except ValueError:
                            logger.warning(f"配置项 {key} 的值无效,将使用默认值")

                self.config['ai_brain'].update(ai_brain_config)

        def get(self, section, key, default=None):
            return self.config.get(section, {}).get(key, default)

    config_service = SimpleConfigService()
    USE_PROJECT_CONFIG = False
    logger.info("已初始化独立配置服务")
except Exception as e:
    logger.error(f"初始化配置服务失败: {str(e)}")

    class FallbackConfigService:
        def get(self, section, key, default=None):
            return default

    config_service = FallbackConfigService()
    logger.warning("已回退到最简单的配置服务")

try:
    import requests
    from bs4 import BeautifulSoup
    HAS_WEB_CRAWLING = True
    logger.debug("已成功导入网络爬取库")
except ImportError:
    HAS_WEB_CRAWLING = False
    requests = None
    BeautifulSoup = None
    logger.warning("未找到requests和beautifulsoup4库,将使用演示数据")

class AIBrainUpdater:
    """AI脑库自动更新器"""

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """初始化更新器

        Args:
            config: 配置字典,覆盖默认配置
        """
        self.config = config or {}
        self.max_workers = self.config.get('max_workers', config_service.get('ai_brain', 'max_workers', 4))

        if HAS_WEB_CRAWLING and requests is not None:
            self.session = requests.Session()
            self.session.headers.update({
                'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
            })
        else:
            self.session = None

        self.data_sources = self.config.get('sources', config_service.get('ai_brain', 'sources', []))

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
            timeout: 请求超时时间(秒)

        Returns:
            网页内容字符串,如果获取失败或web crawling不可用则返回None
        """
        if not HAS_WEB_CRAWLING or self.session is None or requests is None:
            logger.info(f"跳过网页获取,因为web crawling不可用: {url}")
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
        """解析CSDN AI文章

        Args:
            html: CSDN AI页面HTML内容
            source: 数据源配置

        Returns:
            解析后的文章列表
        """
        soup = BeautifulSoup(html, 'html.parser')
        articles = []
        article_elements = soup.find_all('article', class_='blog-list-box')
        logger.debug(f"从CSDN找到 {len(article_elements)} 篇文章")
        for article in article_elements:
            try:
                title_tag = article.find('h4', class_='blog-list-box-title')
                if not title_tag:
                    continue
                link_tag = title_tag.find('a')
                if not link_tag:
                    continue

                title = title_tag.text.strip()
                link = link_tag['href']

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
        article_elements = soup.find_all('div', class_='course-item')
        logger.debug(f"从AI研习社找到 {len(article_elements)} 篇文章")

        for article in article_elements:
            try:
                title_tag = article.find('h3', class_='course-title')
                if not title_tag:
                    continue
                title = title_tag.text.strip()
                link_tag = article.find('a')
                if not link_tag:
                    continue

                full_link = urljoin(source['url'], link_tag.get('href', ''))
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

        return articles

    def parse_demo_cases(self, html: str, source: Dict[str, Any]) -> List[Dict[str, Any]]:
        """解析演示案例数据

        Args:
            html: 页面HTML内容(未使用)
            source: 数据源配置

        Returns:
            演示案例列表
        """
        demo_cases = [
            {
                'title': 'AI学习案例适配方法',
                'content': 'AI学习案例适配方法包括数据预处理、特征工程、模型选择和评估等步骤.通过系统化的方法,可以有效地将学习案例应用到实际项目中.',
                'url': source['url'],
                'knowledge_type': 'method',
                'source': source['name']
            },
            {
                'title': 'AI脑库智能升级案例',
                'content': '某企业通过AI智能升级脑库,实现了以下成果:1. 知识库容量提升50%;2. 知识检索准确率达到95%;3. 智能推荐系统的点击率提升30%.该案例采用了自动化爬取和智能分类技术,实现了脑库的持续更新和优化.',
                'url': source['url'],
                'knowledge_type': 'case_study',
                'source': source['name']
            },
            {
                'title': '机器学习模型适配技术',
                'content': '机器学习模型适配技术包括模型压缩、迁移学习和联邦学习等.模型压缩可以减小模型体积,提高部署效率;迁移学习可以将预训练模型应用到新的任务中;联邦学习可以在保护数据隐私的前提下进行模型训练.这些技术可以帮助企业快速将AI模型部署到不同的设备和场景中.',
                'url': source['url'],
                'knowledge_type': 'method',
                'source': source['name']
            },
            {
                'title': 'AI脑库自动更新系统',
                'content': 'AI脑库自动更新系统采用了定时爬虫和智能分析技术,可以从网络上自动获取最新的AI知识和案例,并将其添加到脑库中.该系统具有以下特点:1. 支持多种数据源;2. 自动去重和分类;3. 智能提取关键信息;4. 自动更新和优化.通过这种方式,可以确保AI脑库始终保持最新的状态.',
                'url': source['url'],
                'knowledge_type': 'case_study',
                'source': source['name']
            },
            {
                'title': 'Python技术爬取在AI脑库中的应用',
                'content': 'Python爬虫技术在AI脑库建设中发挥着重要作用.通过requests、BeautifulSoup等库,可以高效地从各种网站获取结构化数据.结合自然语言处理技术,可以自动提取关键信息并进行分类存储.',
                'url': source['url'],
                'knowledge_type': 'method',
                'source': source['name']
            }
        ]
        logger.info(f"使用演示数据生成了 {len(demo_cases)} 个案例")
        return demo_cases

    def extract_tags(self, content: str) -> List[str]:
        """提取标签

        Args:
            content: 内容文本

        Returns:
            提取的标签列表
        """
        keywords = [
            'AI', '机器学习', '深度学习', '案例', '方法', '适配', '升级', '智能', '技术',
            'Python', '爬虫', '自动化', '脑库', '数据', '算法', '模型', '训练', '部署',
            'NLP', '计算机视觉', '推荐系统', '知识图谱'
        ]

        tags = []
        content_lower = content.lower()
        for keyword in keywords:
            if keyword.lower() in content_lower:
                tags.append(keyword)

        unique_tags = list(set(tags))
        return unique_tags[:5]

    def update_brain(self, knowledge_items: List[Dict[str, Any]], dry_run: bool = False) -> int:
        """更新AI脑库

        Args:
            knowledge_items: 要添加的知识项列表
            dry_run: 是否为模拟运行模式,不实际更新数据库

        Returns:
            成功添加的知识项数量
        """
        if dry_run:
            logger.info(f"模拟运行模式,跳过实际数据库更新,将添加 {len(knowledge_items)} 条知识项")
            self.stats['added_items'] = len(knowledge_items)
            return len(knowledge_items)

        try:
            from app.models.ai_brain import AIBrainKnowledge
            from app.models.ai_brain import AIBrainActivity
            from uuid import uuid4
            added_count = 0
            total_items = len(knowledge_items)

            for i, item in enumerate(knowledge_items):
                try:
                    if i % 10 == 0:
                        logger.info(f"处理进度: {i + 1}/{total_items}")

                    existing = AIBrainKnowledge.query.filter_by(title=item['title']).first()
                    if not existing:
                        knowledge = AIBrainKnowledge(
                            knowledge_id=str(uuid4()),
                            title=item['title'],
                            content=item['content'],
                            source=item['source'],
                            tags=self.extract_tags(item['content']),
                            priority=5,
                        )
                        knowledge.save()

                        activity = AIBrainActivity(
                            activity_id=str(uuid4()),
                            activity_type='knowledge_added',
                            description=f"添加新知识: {item['title']}",
                            source=item['source'],
                            source_id=item['url']
                        )
                        activity.save()
                        added_count += 1
                except Exception as e:
                    logger.error(f"处理知识项失败 [{i + 1}/{total_items}]: {str(e)}")

            logger.info(f"成功添加 {added_count} 条新知识,跳过 {total_items - added_count} 条已存在的知识")
            self.stats['added_items'] = added_count
            return added_count
        except ImportError as e:
            logger.error(f"导入AI脑库模型失败: {str(e)}")
            logger.info("使用备用方式保存知识项...")
            
            db_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'app.db')
            import sqlite3
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
            CREATE TABLE IF NOT EXISTS ai_brain_knowledge (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                knowledge_id TEXT UNIQUE,
                title TEXT NOT NULL,
                content TEXT,
                source TEXT,
                url TEXT,
                tags TEXT,
                created_at TEXT
            )
            ''')
            
            added_count = 0
            for item in knowledge_items:
                try:
                    cursor.execute('''
                    INSERT OR IGNORE INTO ai_brain_knowledge (knowledge_id, title, content, source, url, tags, created_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                    ''', (
                        str(uuid.uuid4()),
                        item['title'],
                        item['content'],
                        item['source'],
                        item['url'],
                        ','.join(self.extract_tags(item['content'])),
                        datetime.now().isoformat()
                    ))
                    if cursor.rowcount > 0:
                        added_count += 1
                except Exception as e:
                    logger.error(f"保存知识项失败: {str(e)}")
            
            conn.commit()
            conn.close()
            
            self.stats['added_items'] = added_count
            return added_count
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
            html = self.fetch_page(source['url'])

            if not html:
                knowledge_items = self.parse_demo_cases(None, source)
            else:
                parser_name = source.get('parser', 'parse_demo_cases')
                parser_func = getattr(self, parser_name, self.parse_demo_cases)
                knowledge_items = parser_func(html, source)

            logger.info(f"从 {source['name']} 成功获取了 {len(knowledge_items)} 条信息")
            self.stats['processed_sources'] += 1
            self.stats['total_items'] += len(knowledge_items)
            return knowledge_items
        except Exception as e:
            logger.error(f"处理数据源 {source['name']} 失败: {str(e)}")
            self.stats['failed_sources'] += 1
            return []

    def run(self, dry_run: bool = False) -> Dict[str, Any]:
        """运行更新器

        Args:
            dry_run: 是否为模拟运行模式,不实际更新数据库

        Returns:
            运行结果统计信息
        """
        logger.info("=== 开始AI脑库自动更新 ===")
        self.stats['start_time'] = datetime.now()
        self.stats['dry_run'] = dry_run

        all_knowledge = []

        if not self.data_sources:
            logger.warning("没有配置数据源,使用默认演示数据")
            default_demo = {
                'name': '默认演示数据',
                'url': 'https://ai.example.com/default'
            }
            all_knowledge = self.parse_demo_cases(None, default_demo)
            self.stats['total_items'] = len(all_knowledge)
        else:
            with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
                future_to_source = {executor.submit(self._process_source, source): source
                                 for source in self.data_sources}

                for future in as_completed(future_to_source):
                    source = future_to_source[future]
                    try:
                        knowledge_items = future.result()
                        all_knowledge.extend(knowledge_items)
                    except Exception as e:
                        logger.error(f"处理数据源 {source['name']} 时发生异常: {str(e)}")
                        self.stats['failed_sources'] += 1

        logger.info(f"总共获取了 {self.stats['total_items']} 条知识项")

        if all_knowledge:
            self.update_brain(all_knowledge, dry_run)

        self.stats['end_time'] = datetime.now()
        self.stats['duration'] = self.stats['end_time'] - self.stats['start_time']

        self._generate_report()

        try:
            import sqlite3
            db_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'app.db')

            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
            CREATE TABLE IF NOT EXISTS system_config (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                config_key TEXT UNIQUE NOT NULL,
                config_value TEXT NOT NULL,
                config_type TEXT NOT NULL DEFAULT 'string',
                description TEXT,
                is_active INTEGER DEFAULT 1,
                updated_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
            ''')
            
            current_version = '1.0.0'
            cursor.execute('SELECT config_value FROM system_config WHERE config_key=? AND is_active=1', ('system_version',))
            row = cursor.fetchone()
            if row:
                current_version = row[0]
            
            parts = current_version.split('.')
            if len(parts) >= 3:
                parts[-1] = str(int(parts[-1]) + 1)
                new_version = '.'.join(parts)
            else:
                new_version = f"{current_version}.1"
            
            cursor.execute('''
            INSERT OR REPLACE INTO system_config
            (config_key, config_value, config_type, description, is_active, updated_at)
            VALUES (?, ?, ?, ?, 1, CURRENT_TIMESTAMP)
            ''', ('system_version', new_version, 'string', '系统版本号'))
            
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
        === AI脑库更新报告 == 开始时间: {self.stats['start_time']}
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

        with open('ai_brain_update_report.log', 'a', encoding='utf-8') as f:
            f.write(report)
            f.write('\n' + '='*50 + '\n')

    def run_scheduled(self, interval_hours: int = 24) -> None:
        """定时运行更新器

        Args:
            interval_hours: 更新间隔时间(小时)
        """
        logger.info(f"=== 启动AI脑库定时更新服务,更新间隔: {interval_hours} 小时 ===")

        while True:
            try:
                self.run()
            except Exception as e:
                logger.error(f"定时更新执行失败: {str(e)}")

            next_update_time = datetime.now() + timedelta(hours=interval_hours)
            logger.info(f"下次更新将在 {next_update_time} 进行({interval_hours} 小时后)")
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

        for key in ['max_workers', 'update_interval_hours']:
            if key in ai_brain_config:
                ai_brain_config[key] = int(ai_brain_config[key])

        result['ai_brain'] = ai_brain_config

    return result

def main():
    """主函数,处理命令行参数并执行相应操作"""
    parser = argparse.ArgumentParser(description='AI脑库自动更新脚本')

    parser.add_argument('--mode', '-m', choices=['once', 'scheduled'], default='once',
                      help='运行模式:once(单次运行)或 scheduled(定时运行)')

    parser.add_argument('--config', '-c', type=str, default=None,
                      help='配置文件路径')
    parser.add_argument('--workers', '-w', type=int, default=None,
                      help='并发工作线程数')
    parser.add_argument('--interval', '-i', type=int, default=None,
                      help='定时更新间隔(小时)')

    parser.add_argument('--sources', '-s', type=str, default=None,
                      help='数据源配置文件路径')

    parser.add_argument('--log-level', type=str, choices=['DEBUG', 'INFO', 'WARNING', 'ERROR'],
                      default=None, help='日志级别')

    parser.add_argument('--dry-run', '-n', action='store_true',
                      help='模拟运行,不实际更新数据库')
    parser.add_argument('--verbose', '-v', action='store_true',
                      help='详细输出模式')
    args = parser.parse_args()

    if args.log_level:
        logger.setLevel(getattr(logging, args.log_level))
    elif args.verbose:
        logger.setLevel(logging.DEBUG)

    updater = AIBrainUpdater(config={})

    if args.mode == 'scheduled':
        interval = args.interval or config_service.get('ai_brain', 'update_interval_hours', 24)
        updater.run_scheduled(interval)
    else:
        result = updater.run(dry_run=args.dry_run)

        print("\n == AI脑库更新结果摘要 ===")
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
    main()
