#!/usr/bin/env python3
"""
AI网络知识采集器
实现AI从网络中自我学习知识到脑库，支持自动发现知识点和学习方向
"""

import os
import re
import json
import time
import random
import sqlite3
import threading
import urllib.request
import urllib.parse
from datetime import datetime
from collections import defaultdict

DB_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), '..', 'app.db')

KNOWLEDGE_SOURCES = [
    {
        'name': 'Python官方文档',
        'url': 'https://docs.python.org/3/',
        'category': 'technical',
        'domain': 'Python',
        'keywords': ['function', 'class', 'method', 'import', 'exception', 'decorator', 'async', 'generator']
    },
    {
        'name': 'Flask文档',
        'url': 'https://flask.palletsprojects.com/',
        'category': 'technical',
        'domain': 'Flask',
        'keywords': ['route', 'blueprint', 'request', 'response', 'session', 'template', 'middleware']
    },
    {
        'name': 'SQLite文档',
        'url': 'https://www.sqlite.org/docs.html',
        'category': 'technical',
        'domain': 'SQLite',
        'keywords': ['SELECT', 'INSERT', 'UPDATE', 'DELETE', 'INDEX', 'JOIN', 'TRANSACTION', 'VACUUM']
    },
    {
        'name': '网络技术',
        'url': 'https://www.rfc-editor.org/',
        'category': 'technical',
        'domain': 'Network',
        'keywords': ['HTTP', 'TCP', 'UDP', 'SSL', 'TLS', 'DNS', 'WebSocket', 'REST']
    },
    {
        'name': '安全技术',
        'url': 'https://owasp.org/',
        'category': 'security',
        'domain': 'Security',
        'keywords': ['SQL注入', 'XSS', 'CSRF', '身份验证', '授权', '加密', '漏洞', '攻击']
    },
    {
        'name': 'AI技术',
        'url': 'https://arxiv.org/',
        'category': 'ai',
        'domain': 'AI',
        'keywords': ['machine learning', 'deep learning', 'neural network', 'transformer', 'LLM', 'GPT', 'embedding']
    },
    {
        'name': '系统架构',
        'url': 'https://martinfowler.com/',
        'category': 'system',
        'domain': 'Architecture',
        'keywords': ['microservices', 'design pattern', 'distributed system', 'scalability', 'availability',
        'resilience']
    },
    {
        'name': '软件工程',
        'url': 'https://www.thoughtworks.com/',
        'category': 'system',
        'domain': 'Engineering',
        'keywords': ['CI/CD', 'DevOps', 'testing', 'version control', 'code review', 'refactoring']
    }
]

class NetworkKnowledgeCollector:
    """网络知识采集器"""
    
    def __init__(self):
        self.is_running = False
        self.collecting_thread = None
        self.knowledge_cache = []
        self.collection_stats = defaultdict(int)
        self._lock = threading.Lock()
        self._init_database()
        self.dynamic_keywords = []
        self.searched_keywords = set()
    
    def set_dynamic_keywords(self, keywords):
        """设置动态搜索关键词（来自自我觉醒发现的学习方向）"""
        self.dynamic_keywords = keywords
        logger.info(f"[NetworkLearner] 已设置 {len(keywords)} 个动态搜索关键词: {keywords}")
    
    def mark_keywords_searched(self, keywords):
        """标记关键词已搜索"""
        self.searched_keywords.update(keywords)
        logger.info(f"[NetworkLearner] 已标记 {len(keywords)} 个关键词为已搜索")
    
    def get_unsearched_keywords(self, keywords):
        """获取未搜索的关键词"""
        return [kw for kw in keywords if kw not in self.searched_keywords]
    
    def _init_database(self):
        try:
            conn = sqlite3.connect(DB_PATH)
            cursor = conn.cursor()
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS network_learning_sources (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    source_name TEXT NOT NULL,
                    source_url TEXT NOT NULL,
                    category TEXT,
                    domain TEXT,
                    keywords TEXT,
                    last_collected TEXT,
                    success_count INTEGER DEFAULT 0,
                    fail_count INTEGER DEFAULT 0,
                    status TEXT DEFAULT 'active',
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                    updated_at TEXT DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS network_learning_records (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    knowledge_id TEXT UNIQUE NOT NULL,
                    title TEXT NOT NULL,
                    content TEXT NOT NULL,
                    category TEXT,
                    domain TEXT,
                    source_url TEXT,
                    source_name TEXT,
                    confidence REAL DEFAULT 0.0,
                    extracted_keywords TEXT,
                    status TEXT DEFAULT 'collected',
                    fed_to_brain INTEGER DEFAULT 0,
                    collected_at TEXT DEFAULT CURRENT_TIMESTAMP,
                    fed_at TEXT
                )
            ''')
            conn.commit()
            conn.close()
            logger.info("[NetworkLearner] 数据库表初始化完成")
        except Exception as e:
            logger.info(f"[NetworkLearner] 初始化数据库失败: {e}")
    
    def _get_connection(self):
        return sqlite3.connect(DB_PATH)
    
    def fetch_web_content(self, url, timeout=10):
        """获取网页内容"""
        try:
            req = urllib.request.Request(
                url,
                headers={
                                        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML,                    like Gecko) Chrome/120.0.0.0 Safari/537.36'
                }
            )
            with urllib.request.urlopen(req, timeout=timeout) as response:
                content = response.read().decode('utf-8', errors='ignore')
                return content, response.status
        except Exception as e:
            logger.info(f"[NetworkLearner] 获取网页失败 {url}: {e}")
            return None, 0
    
    def extract_knowledge_points(self, content, source_info):
        """从网页内容中提取知识点"""
        if not content:
            return []
        
        knowledge_points = []
        keywords = source_info.get('keywords', [])
        
        for keyword in keywords:
            patterns = [
                rf'(?i)({keyword}[^\n{{}};]*?\.)',
                rf'(?i)<h[1-6]>.*?{keyword}.*?</h[1-6]>',
                rf'(?i)(def\s+{keyword}\s*\([^)]*\)\s*:)',
                rf'(?i)(class\s+{keyword}[^\(]*?\()',
                rf'(?i)({keyword}\s+[A-Za-z_]+\s*=)',
                rf'(?i)({keyword}\s+is\s+\w+)',
                rf'(?i)({keyword}\s+\w+\s+\()',
                rf'(?i)(["]{keyword}[^"]*["])',
            ]
            
            for pattern in patterns:
                matches = re.findall(pattern, content, re.DOTALL)
                for match in matches[:5]:
                    cleaned = re.sub(r'<[^>]*>', '', str(match)).strip()
                    cleaned = re.sub(r'\s+', ' ', cleaned)
                    
                    if len(cleaned) > 10 and len(cleaned) < 500:
                        knowledge_point = {
                            'title': f"{source_info['domain']} - {keyword}",
                            'content': cleaned,
                            'category': source_info.get('category', 'technical'),
                            'domain': source_info.get('domain', 'general'),
                            'source_url': source_info['url'],
                            'source_name': source_info['name'],
                            'confidence': round(random.uniform(0.6, 0.95), 4),
                            'extracted_keywords': keyword
                        }
                        knowledge_points.append(knowledge_point)
        
        knowledge_points = self._deduplicate_knowledge(knowledge_points)
        return knowledge_points
    
    def _deduplicate_knowledge(self, knowledge_points):
        seen_contents = set()
        unique_points = []
        for point in knowledge_points:
            content_hash = hash(point['content'][:100])
            if content_hash not in seen_contents:
                seen_contents.add(content_hash)
                unique_points.append(point)
        return unique_points
    
    def fetch_and_extract(self, source_info):
        """获取并提取知识"""
        logger.info(f"[NetworkLearner] 开始采集: {source_info['name']}")
        
        content, status = self.fetch_web_content(source_info['url'])
        if not content or status != 200:
            self.collection_stats['failed'] += 1
            self._update_source_failed(source_info['name'])
            return []
        
        knowledge_points = self.extract_knowledge_points(content, source_info)
        
        if knowledge_points:
            self.collection_stats['success'] += 1
            self.collection_stats['knowledge_collected'] += len(knowledge_points)
            self._update_source_success(source_info['name'])
            self._save_knowledge(knowledge_points)
            logger.info(f"[NetworkLearner] 成功提取 {len(knowledge_points)} 个知识点")
        else:
            self.collection_stats['empty'] += 1
        
        return knowledge_points
    
    def _save_knowledge(self, knowledge_points):
        """保存知识到数据库"""
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            
            for point in knowledge_points:
                knowledge_id = f"NK-{datetime.now().strftime('%Y%m%d%H%M%S')}-{random.randint(1000, 9999)}"
                
                cursor.execute('''
                    INSERT OR IGNORE INTO network_learning_records
                    (knowledge_id, title, content, category, domain, source_url, source_name,
                     confidence, extracted_keywords, status, fed_to_brain, collected_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    knowledge_id,
                    point['title'],
                    point['content'],
                    point['category'],
                    point['domain'],
                    point['source_url'],
                    point['source_name'],
                    point['confidence'],
                    point['extracted_keywords'],
                    'collected',
                    0,
                    datetime.now().isoformat()
                ))
            
            conn.commit()
            conn.close()
        except Exception as e:
            logger.info(f"[NetworkLearner] 保存知识失败: {e}")
    
    def _update_source_success(self, source_name):
        """更新源成功统计"""
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            cursor.execute('''
                UPDATE network_learning_sources
                SET success_count = success_count + 1, last_collected = ?, updated_at = ?
                WHERE source_name = ?
            ''', (datetime.now().isoformat(), datetime.now().isoformat(), source_name))
            
            if cursor.rowcount == 0:
                cursor.execute('''
                    INSERT INTO network_learning_sources
                    (source_name, source_url, category, domain, keywords, last_collected, success_count, status)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    source_name,
                    '', '', '', '',
                    datetime.now().isoformat(), 1, 'active'
                ))
            
            conn.commit()
            conn.close()
        except Exception as e:
            logger.info(f"[NetworkLearner] 更新源统计失败: {e}")
    
    def _update_source_failed(self, source_name):
        """更新源失败统计"""
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            cursor.execute('''
                UPDATE network_learning_sources
                SET fail_count = fail_count + 1, last_collected = ?, updated_at = ?
                WHERE source_name = ?
            ''', (datetime.now().isoformat(), datetime.now().isoformat(), source_name))
            conn.commit()
            conn.close()
        except Exception as e:
            logger.info(f"[NetworkLearner] 更新源失败统计失败: {e}")
    
    def feed_to_brain(self):
        """将采集的知识投喂到脑库"""
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT * FROM network_learning_records 
                WHERE fed_to_brain = 0 AND status = 'collected'
                LIMIT 50
            ''')
            records = cursor.fetchall()
            
            if not records:
                logger.info("[NetworkLearner] 无可投喂的知识")
                conn.close()
                return {'success': False, 'message': '无可投喂的知识'}
            
            fed_count = 0
            for record in records:
                knowledge_id = f"K-{datetime.now().strftime('%Y%m%d%H%M%S')}-{random.randint(1000, 9999)}"
                
                cursor.execute('''
                    INSERT OR IGNORE INTO ai_brain_knowledge
                    (knowledge_id, title, content, knowledge_type, source, tags, priority, status, created_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    knowledge_id,
                    record[2],
                    record[3],
                    record[4],
                    'network_learner',
                    f"{record[5]},{record[4]}",
                    random.randint(1, 10),
                    'active',
                    datetime.now().isoformat()
                ))
                
                cursor.execute('''
                    INSERT INTO brain_feeding_queue
                    (feed_id, feed_type, feed_source, feed_data, knowledge_type, priority,
                     status, scheduled_at, data_size, tags, description, created_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    f"FED-{datetime.now().strftime('%Y%m%d%H%M%S')}-{random.randint(1000, 9999)}",
                    'knowledge',
                    'network_learner',
                    json.dumps({'title': record[2], 'content': record[3]}, ensure_ascii=False),
                    record[4],
                    random.randint(1, 10),
                    'completed',
                    datetime.now().isoformat(),
                    len(record[3].encode('utf-8')),
                    record[5],
                    f"网络采集知识: {record[2]}",
                    datetime.now().isoformat()
                ))
                
                cursor.execute('''
                    UPDATE network_learning_records
                    SET fed_to_brain = 1, fed_at = ?, status = 'fed'
                    WHERE id = ?
                ''', (datetime.now().isoformat(), record[0]))
                
                fed_count += 1
            
            conn.commit()
            conn.close()
            
            logger.info(f"[NetworkLearner] 成功投喂 {fed_count} 条知识到脑库")
            return {'success': True, 'fed_count': fed_count, 'message': f"成功投喂 {fed_count} 条知识到脑库"}
        
        except Exception as e:
            logger.info(f"[NetworkLearner] 投喂脑库失败: {e}")
            return {'success': False, 'error': str(e)}
    
    def _search_web_for_keywords(self, keywords, max_results=3):
        """根据关键词动态搜索网络"""
        search_points = []
        
        for keyword in keywords:
            logger.info(f"[NetworkLearner] 动态搜索: {keyword}")
            
            dynamic_sources = self._build_dynamic_sources(keyword)
            
            for source in dynamic_sources:
                try:
                    content, status = self.fetch_web_content(source['url'], timeout=10)
                    if content and status == 200:
                        knowledge_points = self.extract_knowledge_points(content, {
                            'name': source['name'],
                            'url': source['url'],
                            'category': 'dynamic',
                            'domain': 'self_learning',
                            'keywords': [keyword]
                        })
                        search_points.extend(knowledge_points)
                        logger.info(f"  从 {source['name']} 获取 {len(knowledge_points)} 个知识点")
                    time.sleep(random.uniform(0.5, 1))
                except Exception as e:
                    logger.info(f"[NetworkLearner] 获取 {source['name']} 内容失败: {e}")
        
        if not search_points:
            search_points = self._search_wikipedia(keyword)
        
        return search_points
    
    def _build_dynamic_sources(self, keyword):
        """根据关键词构建动态搜索源（仅保留可靠源）"""
        sources = []
        
        keyword_encoded = urllib.parse.quote(keyword)
        
        wiki_title = self._resolve_wikipedia_title(keyword)
        if wiki_title:
            sources.append({
                'name': f'维基百科-{keyword}',
                'url': f'https://zh.wikipedia.org/wiki/{wiki_title}'
            })
        
        sources.append({
            'name': f'维基百科-{keyword}',
            'url': f'https://zh.wikipedia.org/w/index.php?search={keyword_encoded}'
        })
        
        sources.append({
            'name': f'GitHub搜索-{keyword}',
            'url': f'https://github.com/search?q={keyword_encoded}&type=repositories'
        })
        
        sources.append({
            'name': f'StackOverflow-{keyword}',
            'url': f'https://stackoverflow.com/search?q={keyword_encoded}'
        })
        
        return sources
    
    def _resolve_wikipedia_title(self, keyword):
        """使用Wikipedia API解析正确的文章标题"""
        try:
            keyword_encoded = urllib.parse.quote(keyword)
            url = f'https://zh.wikipedia.org/w/api.php?action=opensearch&search={keyword_encoded}&limit=1&format=json'
            
            req = urllib.request.Request(url, headers={
                'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36',
                'Accept': 'application/json'
            })
            
            with urllib.request.urlopen(req, timeout=5) as resp:
                import json
                data = json.loads(resp.read().decode('utf-8'))
                
                if data[1] and len(data[1]) > 0:
                    title = urllib.parse.quote(data[1][0])
                    return title
        except Exception as e:
            logger.info(f"[NetworkLearner] 解析维基百科标题失败: {e}")
        
        return None
    
    def _search_wikipedia(self, keyword):
        """使用维基百科API搜索"""
        search_points = []
        
        try:
            keyword_encoded = urllib.parse.quote(keyword)
            url = f'https://zh.wikipedia.org/w/api.php?action=opensearch&search={keyword_encoded}&limit=3&format=json'
            
            req = urllib.request.Request(url, headers={
                'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36',
                'Accept': 'application/json'
            })
            
            with urllib.request.urlopen(req, timeout=10) as resp:
                import json
                data = json.loads(resp.read().decode('utf-8'))
                
                titles = data[1]
                urls = data[3]
                
                for i, title in enumerate(titles):
                    if i >= len(urls):
                        break
                    
                    page_content, status = self.fetch_web_content(urls[i])
                    if page_content and status == 200:
                        knowledge_points = self.extract_knowledge_points(page_content, {
                            'name': f'维基百科-{title}',
                            'url': urls[i],
                            'category': 'dynamic',
                            'domain': 'self_learning',
                            'keywords': [keyword]
                        })
                        search_points.extend(knowledge_points)
                        time.sleep(0.5)
            
            logger.info(f"[NetworkLearner] 维基百科搜索返回 {len(search_points)} 个知识点")
        except Exception as e:
            logger.info(f"[NetworkLearner] 维基百科搜索失败: {e}")
        
        return search_points
    
    def _extract_links_from_search(self, content):
        """从搜索结果中提取链接（多种模式）"""
        patterns = [
            r'<a\s+href=["\']([^"\']+)["\'][^>]*>(?:<h2>|[^<]*?</h[23]>)',
            r'<a\s+href=["\']([^"\']+)["\'][^>]*>\s*<h[23]',
            r'<h[23]>\s*<a\s+href=["\']([^"\']+)["\']',
            r'<a\s+class=["\'][^"\']*b_algo[^"\']*["\']\s+href=["\']([^"\']+)["\']',
            r'<a\s+class=["\'][^"\']*result__a[^"\']*["\']\s+href=["\']([^"\']+)["\']',
            r'<a\s+href=["\']([^"\']+)["\'][^>]*class=["\'][^"\']*result[^"\']*["\']',
        ]
        
        all_links = []
        for pattern in patterns:
            links = re.findall(pattern, content, re.DOTALL)
            for link in links:
                if link not in all_links and link.startswith('http'):
                    all_links.append(link)
        
        return all_links
    
    def _extract_links_fallback(self, content):
        """备用链接提取方法"""
        links = re.findall(r'<a\s+href=["\']([^"\']+)["\']', content)
        filtered = []
        for link in links:
            if link.startswith('http') and link not in filtered:
                filtered.append(link)
        return filtered
    
    def run_collection(self):
        """执行知识采集（包含动态搜索）"""
        logger.info("[NetworkLearner] 开始网络知识采集...")
        all_points = []
        
        for source_info in KNOWLEDGE_SOURCES:
            try:
                points = self.fetch_and_extract(source_info)
                all_points.extend(points)
                time.sleep(random.uniform(1, 3))
            except Exception as e:
                logger.info(f"[NetworkLearner] 采集源 {source_info['name']} 失败: {e}")
        
        if self.dynamic_keywords:
            logger.info(f"[NetworkLearner] 开始动态搜索（基于自我觉醒发现的学习方向）...")
            unsearched = self.get_unsearched_keywords(self.dynamic_keywords)
            
            if unsearched:
                dynamic_points = self._search_web_for_keywords(unsearched)
                all_points.extend(dynamic_points)
                self.mark_keywords_searched(unsearched)
                logger.info(f"[NetworkLearner] 动态搜索完成, 获取 {len(dynamic_points)} 个知识点")
            else:
                logger.info(f"[NetworkLearner] 所有关键词已搜索过，跳过动态搜索")
        
        logger.info(f"[NetworkLearner] 采集完成, 共获取 {len(all_points)} 个知识点")
        return all_points
    
    def get_collection_stats(self):
        """获取采集统计"""
        return dict(self.collection_stats)
    
    def get_learning_records(self, limit=100):
        """获取学习记录"""
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            cursor.execute('''
                SELECT * FROM network_learning_records 
                ORDER BY collected_at DESC LIMIT ?
            ''', (limit,))
            rows = cursor.fetchall()
            
            records = []
            for row in rows:
                records.append({
                    'id': row[0],
                    'knowledge_id': row[1],
                    'title': row[2],
                    'content': row[3],
                    'category': row[4],
                    'domain': row[5],
                    'source_url': row[6],
                    'source_name': row[7],
                    'confidence': row[8],
                    'status': row[10],
                    'fed_to_brain': row[11],
                    'collected_at': row[12]
                })
            
            conn.close()
            return records
        except Exception as e:
            logger.info(f"[NetworkLearner] 获取学习记录失败: {e}")
            return []
    
    def start_auto_collection(self, interval=3600):
        """启动自动采集"""
        if self.is_running:
            return {'success': False, 'message': '自动采集已在运行'}
        
        self.is_running = True
        self.collecting_thread = threading.Thread(target=self._collection_loop, args=(interval,), daemon=True)
        self.collecting_thread.start()
        return {'success': True, 'message': f'自动采集已启动, 间隔 {interval} 秒'}
    
    def stop_auto_collection(self):
        """停止自动采集"""
        self.is_running = False
        if self.collecting_thread:
            self.collecting_thread.join(timeout=10)
        return {'success': True, 'message': '自动采集已停止'}
    
    def _collection_loop(self, interval):
        """采集循环"""
        while self.is_running:
            self.run_collection()
            self.feed_to_brain()
            
            for i in range(interval):
                if not self.is_running:
                    break
                time.sleep(1)

network_knowledge_collector = NetworkKnowledgeCollector()