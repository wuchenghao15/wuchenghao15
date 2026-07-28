#!/usr/bin/env python3
import requests
import json
import os
import re
import sqlite3
from datetime import datetime
from urllib.parse import quote, urljoin
from bs4 import BeautifulSoup

DATABASE_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'app.db')

class ResourceCollector:
    """多源资源采集器 - 从抖音、小红书、GitHub、CSDN等平台获取学习资源"""
    
    def __init__(self):
        self.conn = sqlite3.connect(DATABASE_PATH)
        self.conn.row_factory = sqlite3.Row
        self.cursor = self.conn.cursor()
        self._create_tables()
        
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
            'Accept-Encoding': 'gzip, deflate',
        }
    
    def _create_tables(self):
        """创建资源采集相关表"""
        # 资源来源配置表
        self.cursor.execute(''' CREATE TABLE IF NOT EXISTS resource_sources ( id INTEGER PRIMARY KEY AUTOINCREMENT, source_name TEXT UNIQUE NOT NULL, source_type TEXT, base_url TEXT, api_endpoint TEXT, enabled INTEGER DEFAULT 1, last_crawl_time TEXT, crawl_interval_hours INTEGER DEFAULT 24, config_json TEXT, created_at TEXT DEFAULT CURRENT_TIMESTAMP, updated_at TEXT DEFAULT CURRENT_TIMESTAMP ) ''')
        
        # 采集到的资源表
        self.cursor.execute(''' CREATE TABLE IF NOT EXISTS collected_resources ( id INTEGER PRIMARY KEY AUTOINCREMENT, title TEXT NOT NULL, url TEXT UNIQUE NOT NULL, source TEXT NOT NULL, resource_type TEXT, category TEXT, author TEXT, description TEXT, keywords TEXT, publish_date TEXT, view_count INTEGER DEFAULT 0, like_count INTEGER DEFAULT 0, collect_count INTEGER DEFAULT 0, tags TEXT, content_summary TEXT, difficulty TEXT, language TEXT, file_type TEXT, file_size TEXT, quality_score REAL DEFAULT 0.0, crawled_at TEXT DEFAULT CURRENT_TIMESTAMP, processed INTEGER DEFAULT 0, process_result TEXT, metadata TEXT ) ''')
        
        # 采集任务记录表
        self.cursor.execute(''' CREATE TABLE IF NOT EXISTS crawl_tasks ( id INTEGER PRIMARY KEY AUTOINCREMENT, source TEXT NOT NULL, task_type TEXT, status TEXT DEFAULT 'pending', start_time TEXT, end_time TEXT, total_found INTEGER DEFAULT 0, total_saved INTEGER DEFAULT 0, errors TEXT, created_at TEXT DEFAULT CURRENT_TIMESTAMP ) ''')
        
        self.conn.commit()
        
        self._init_sources()
    
    def _init_sources(self):
        """初始化资源来源配置"""
        sources = [
            ('抖音', 'video', 'https://www.douyin.com', 'https://www.douyin.com/api/', 1, 24,
            json.dumps({'search_url': 'https://www.douyin.com/search/{keyword}'})),
            ('小红书', 'social', 'https://www.xiaohongshu.com', 'https://www.xiaohongshu.com/api/', 1, 24,
            json.dumps({'search_url': 'https://www.xiaohongshu.com/search_result?keyword={keyword}'})),
            ('GitHub', 'code', 'https://github.com', 'https://api.github.com/', 1, 12,
            json.dumps({'search_url': 'https://api.github.com/search/repositories?q={keyword}'})),
            ('CSDN', 'article', 'https://www.csdn.net', 'https://www.csdn.net/api/', 1, 24,
            json.dumps({'search_url': 'https://www.csdn.net/api/v1/search?q={keyword}&type=article'})),
            ('网络爬虫', 'web', '', '', 1, 24, json.dumps({'targets': []})),
        ]
        
        for name, type_, base_url, api, enabled, interval, config in sources:
            self.cursor.execute(''' INSERT OR IGNORE INTO resource_sources (source_name, source_type, base_url, api_endpoint, enabled, crawl_interval_hours, config_json) VALUES (?, ?, ?, ?, ?, ?, ?) ''', (name, type_, base_url, api, enabled, interval, config))
        
        self.conn.commit()
    
    def crawl_douyin(self, keywords):
        """采集抖音资源"""
        results = []
        for keyword in keywords:
            try:
                search_url = f"https://www.douyin.com/search/{quote(keyword)}"
                response = requests.get(search_url, headers=self.headers, timeout=15)
                if response.status_code == 200:
                    soup = BeautifulSoup(response.text, 'html.parser')
                    
                    video_cards = soup.find_all('div', class_=re.compile('video-card|aweme-card'))
                    for card in video_cards[:10]:
                        title_elem = card.find('span', class_=re.compile('title|desc'))
                        link_elem = card.find('a', href=True)
                        
                        if title_elem and link_elem:
                            results.append({
                                'title': title_elem.get_text(strip=True),
                                'url': urljoin('https://www.douyin.com', link_elem['href']),
                                'source': '抖音',
                                'resource_type': 'video',
                                'description': title_elem.get_text(strip=True)[:200],
                            })
            except Exception as e:
                logger.info(f"抖音采集失败 [{keyword}]: {e}")
        
        return results
    
    def crawl_xiaohongshu(self, keywords):
        """采集小红书资源"""
        results = []
        for keyword in keywords:
            try:
                search_url = f"https://www.xiaohongshu.com/search_result?keyword={quote(keyword)}"
                response = requests.get(search_url, headers=self.headers, timeout=15)
                if response.status_code == 200:
                    soup = BeautifulSoup(response.text, 'html.parser')
                    
                    note_cards = soup.find_all('div', class_=re.compile('note-card|search-item'))
                    for card in note_cards[:10]:
                        title_elem = card.find('h3') or card.find('span', class_=re.compile('title'))
                        link_elem = card.find('a', href=True)
                        
                        if title_elem and link_elem:
                            results.append({
                                'title': title_elem.get_text(strip=True),
                                'url': urljoin('https://www.xiaohongshu.com', link_elem['href']),
                                'source': '小红书',
                                'resource_type': 'article',
                                'description': title_elem.get_text(strip=True)[:200],
                            })
            except Exception as e:
                logger.info(f"小红书采集失败 [{keyword}]: {e}")
        
        return results
    
    def crawl_github(self, keywords):
        """采集GitHub资源"""
        results = []
        for keyword in keywords:
            try:
                search_url = f"https://api.github.com/search/repositories?q={quote(keyword)}&per_page=10"
                response = requests.get(search_url, headers=self.headers, timeout=15)
                if response.status_code == 200:
                    data = response.json()
                    for item in data.get('items', []):
                        results.append({
                            'title': item['name'],
                            'url': item['html_url'],
                            'source': 'GitHub',
                            'resource_type': 'code',
                            'author': item['owner']['login'],
                            'description': item['description'] or '',
                            'language': item.get('language', ''),
                            'stars': item.get('stargazers_count', 0),
                            'forks': item.get('forks_count', 0),
                            'watchers': item.get('watchers_count', 0),
                        })
            except Exception as e:
                logger.info(f"GitHub采集失败 [{keyword}]: {e}")
        
        return results
    
    def crawl_csdn(self, keywords):
        """采集CSDN资源"""
        results = []
        for keyword in keywords:
            try:
                search_url = f"https://www.csdn.net/api/v1/search?q={quote(keyword)}&type=article&page_size=10"
                response = requests.get(search_url, headers=self.headers, timeout=15)
                if response.status_code == 200:
                    data = response.json()
                    for item in data.get('result_vos', []):
                        results.append({
                            'title': item.get('title', ''),
                            'url': item.get('url', ''),
                            'source': 'CSDN',
                            'resource_type': 'article',
                            'author': item.get('nickname', ''),
                            'description': item.get('description', '')[:200],
                            'view_count': item.get('view_count', 0),
                            'like_count': item.get('digg_count', 0),
                            'collect_count': item.get('collect_count', 0),
                            'publish_date': item.get('create_time', ''),
                        })
            except Exception as e:
                logger.info(f"CSDN采集失败 [{keyword}]: {e}")
        
        return results
    
    def crawl_web(self, urls, keywords=None):
        """通用网页爬虫"""
        results = []
        for url in urls:
            try:
                response = requests.get(url, headers=self.headers, timeout=15)
                if response.status_code == 200:
                    soup = BeautifulSoup(response.text, 'html.parser')
                    title = soup.title.get_text(strip=True) if soup.title else ''
                    
                    content_div = soup.find('article') or soup.find('div', class_=re.compile('content|article'))
                    description = ''
                    if content_div:
                        description = content_div.get_text(strip=True)[:300]
                    
                    results.append({
                        'title': title,
                        'url': url,
                        'source': '网络爬虫',
                        'resource_type': 'article',
                        'description': description,
                    })
            except Exception as e:
                logger.info(f"网页采集失败 [{url}]: {e}")
        
        return results
    
    def save_resources(self, resources):
        """保存采集到的资源"""
        saved_count = 0
        for resource in resources:
            try:
                self.cursor.execute(''' INSERT OR IGNORE INTO collected_resources (title, url, source, resource_type, category, author, description, keywords, publish_date, view_count, like_count, collect_count, tags, content_summary, difficulty, language, file_type, file_size, quality_score, metadata) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?) ''', (
                    resource.get('title', ''),
                    resource.get('url', ''),
                    resource.get('source', ''),
                    resource.get('resource_type', ''),
                    resource.get('category', ''),
                    resource.get('author', ''),
                    resource.get('description', ''),
                    resource.get('keywords', ''),
                    resource.get('publish_date', ''),
                    resource.get('view_count', 0),
                    resource.get('like_count', 0) or resource.get('stars', 0),
                    resource.get('collect_count', 0),
                    resource.get('tags', ''),
                    resource.get('content_summary', ''),
                    resource.get('difficulty', ''),
                    resource.get('language', ''),
                    resource.get('file_type', ''),
                    resource.get('file_size', ''),
                    resource.get('quality_score', self._calculate_quality(resource)),
                    json.dumps(resource)
                ))
                saved_count += 1
            except Exception as e:
                logger.info(f"保存资源失败 [{resource.get('title')}]: {e}")
        
        self.conn.commit()
        return saved_count
    
    def _calculate_quality(self, resource):
        """计算资源质量分数"""
        score = 0.5
        
        if resource.get('source') == 'GitHub':
            stars = resource.get('stars', 0)
            forks = resource.get('forks', 0)
            score = min(0.95, 0.5 + (stars + forks) / 500)
        
        elif resource.get('source') == 'CSDN':
            views = resource.get('view_count', 0)
            likes = resource.get('like_count', 0)
            score = min(0.95, 0.5 + (views + likes * 10) / 10000)
        
        elif resource.get('description') and len(resource['description']) > 50:
            score += 0.1
        
        return round(score, 2)
    
    def run_collection(self, keywords=None, sources=None):
        """执行资源采集"""
        if keywords is None:
            keywords = ['AI学习', '机器学习', '深度学习', 'Python', '数据科学', '大数据', '算法']
        
        if sources is None:
            sources = ['抖音', '小红书', 'GitHub', 'CSDN']
        
        total_found = 0
        total_saved = 0
        
        logger.info(f"开始采集资源，关键词: {keywords}")
        logger.info(f"采集来源: {sources}")
        
        for source in sources:
            logger.info(f"\n--- 正在采集 {source} ---")
            
            if source == '抖音':
                resources = self.crawl_douyin(keywords)
            elif source == '小红书':
                resources = self.crawl_xiaohongshu(keywords)
            elif source == 'GitHub':
                resources = self.crawl_github(keywords)
            elif source == 'CSDN':
                resources = self.crawl_csdn(keywords)
            elif source == '网络爬虫':
                resources = []
            else:
                continue
            
            logger.info(f"找到 {len(resources)} 条资源")
            total_found += len(resources)
            
            saved = self.save_resources(resources)
            logger.info(f"成功保存 {saved} 条资源")
            total_saved += saved
        
        logger.info(f"\n=== 采集完成 ===")
        logger.info(f"共发现: {total_found} 条")
        logger.info(f"共保存: {total_saved} 条")
        
        return {'found': total_found, 'saved': total_saved}
    
    def get_collected_resources(self, source=None, limit=20):
        """获取采集到的资源"""
        query = 'SELECT * FROM collected_resources'
        params = []
        
        if source:
            query += ' WHERE source = ?'
            params.append(source)
        
        query += ' ORDER BY quality_score DESC, crawled_at DESC LIMIT ?'
        params.append(limit)
        
        self.cursor.execute(query, params)
        return [dict(row) for row in self.cursor.fetchall()]
    
    def get_resource_stats(self):
        """获取资源统计信息"""
        self.cursor.execute('SELECT source, COUNT(*) FROM collected_resources GROUP BY source')
        source_stats = dict(self.cursor.fetchall())
        
        self.cursor.execute('SELECT resource_type, COUNT(*) FROM collected_resources GROUP BY resource_type')
        type_stats = dict(self.cursor.fetchall())
        
        self.cursor.execute('SELECT COUNT(*) FROM collected_resources')
        total = self.cursor.fetchone()[0]
        
        return {
            'total': total,
            'by_source': source_stats,
            'by_type': type_stats,
        }
    
    def close(self):
        """关闭数据库连接"""
        self.conn.close()

if __name__ == '__main__':
    collector = ResourceCollector()
    
    keywords = ['AI学习', '机器学习', '深度学习', 'Python', '数据科学', '大数据', '算法', '神经网络']
    sources = ['抖音', '小红书', 'GitHub', 'CSDN']
    
    result = collector.run_collection(keywords=keywords, sources=sources)
    
    logger.info("\n=== 资源统计 ===")
    stats = collector.get_resource_stats()
    logger.info(f"总资源数: {stats['total']}")
    logger.info(f"按来源分布: {stats['by_source']}")
    logger.info(f"按类型分布: {stats['by_type']}")
    
    logger.info("\n=== 高质量资源（TOP 10）===")
    top_resources = collector.get_collected_resources(limit=10)
    for i, res in enumerate(top_resources, 1):
        logger.info(f"{i}. [{res['source']}] {res['title'][:50]} - 质量分: {res['quality_score']}")
        logger.info(f"   URL: {res['url'][:80]}")
    
    collector.close()