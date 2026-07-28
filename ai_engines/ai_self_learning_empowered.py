# -*- coding: utf-8 -*-
#!/usr/bin/env python3
"""
AI自我学习赋能系统 - 增强版
功能特性:
1. AI自动从网络中自我学习知识到脑库
2. 实现自我自动投喂知识机制
3. 实现脑库壮大功能
4. AI从实际升级维护中自我觉醒学习重点要点
5. 自动发现AI学习的知识点和学习方向
6. 自动写入AI自我学习规则到RULES.md
7. 严格执行学习政策
"""
import os
import sys
import sqlite3
import logging
import traceback
import time
import json
import re
import threading
from datetime import datetime, timedelta, timezone
from typing import Dict, List, Optional, Any, Set
from urllib.parse import quote, urlparse
import requests

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('ai_self_learning_empowered.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

CONFIG = {
    "db_path": os.path.join(os.path.dirname(os.path.abspath(__file__)), "ai_brain.db"),
    "rules_file": os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "RULES.md"),
    "learning_interval_minutes": 30,
    "network_fetch_timeout": 15,
    "max_knowledge_per_fetch": 10,
    "min_confidence_threshold": 0.6,
    "knowledge_expiry_days": 90,
    "learning_domains": [
        {"name": "AI", "priority": "high", "keywords": ["人工智能", "机器学习", "深度学习", "大语言模型", "LLM", "RAG", "向量数据库"]},
        {"name": "Architecture", "priority": "high", "keywords": ["系统架构", "微服务", "云原生", "服务网格", "无服务器"]},
        {"name": "Database", "priority": "medium", "keywords": ["分布式存储", "时序数据库", "图数据库", "数据湖", "向量数据库"]},
        {"name": "Security", "priority": "high", "keywords": ["网络安全", "零信任", "数据隐私", "加密技术", "AI安全"]},
        {"name": "Performance", "priority": "medium", "keywords": ["性能优化", "负载均衡", "缓存策略", "边缘计算"]},
        {"name": "DevOps", "priority": "medium", "keywords": ["CI/CD", "容器化", "自动化运维", "可观测性"]},
        {"name": "Flask", "priority": "high", "keywords": ["Flask框架", "Python Web", "后端开发", "API设计"]}
    ],
    "knowledge_sources": [
        {"name": "wikipedia", "url": "https://zh.wikipedia.org/w/api.php", "enabled": True},
        {"name": "tech_blogs", "url": "https://api.github.com/search/repositories", "enabled": True},
        {"name": "arxiv", "url": "https://arxiv.org/search/?query=", "enabled": True},
        {"name": "internal_errors", "url": "internal", "enabled": True},
        {"name": "code_analysis", "url": "internal", "enabled": True}
    ]
}

class KnowledgeQualityEvaluator:
    """知识质量评估器"""
    
    def __init__(self):
        self.keyword_patterns = {
            "AI": r"(人工智能|机器学习|深度学习|神经网络|LLM|大语言模型|Transformer|GPT|推理优化|向量数据库|RAG)",
            "Architecture": r"(系统架构|微服务|云原生|服务网格|无服务器|事件驱动|分布式系统)",
            "Security": r"(网络安全|零信任|数据隐私|加密|CSRF|XSS|SQL注入|认证授权)",
            "Performance": r"(性能优化|负载均衡|缓存|边缘计算|响应时间|吞吐量)",
            "Database": r"(数据库|分布式存储|时序|图数据库|数据湖|SQL|NoSQL)",
            "DevOps": r"(CI/CD|容器|Docker|Kubernetes|自动化运维|监控|可观测性)",
            "Flask": r"(Flask|Python|API|路由|中间件|蓝图|Jinja)"
        }
    
    def evaluate_confidence(self, content: str) -> float:
        """评估知识置信度"""
        confidence = 0.3
        content_lower = content.lower()
        
        for domain, pattern in self.keyword_patterns.items():
            if re.search(pattern, content, re.IGNORECASE):
                confidence += 0.1
        
        if len(content) > 200:
            confidence += 0.15
        elif len(content) > 100:
            confidence += 0.05
        
        structured_count = sum(1 for tag in ['问题', '解决方案', '代码', '步骤', '原理'] if tag in content)
        confidence += structured_count * 0.05
        
        return min(1.0, confidence)
    
    def classify_domain(self, content: str) -> str:
        """分类知识领域"""
        max_score = 0
        best_domain = "general"
        
        for domain, pattern in self.keyword_patterns.items():
            matches = len(re.findall(pattern, content, re.IGNORECASE))
            if matches > max_score:
                max_score = matches
                best_domain = domain
        
        return best_domain
    
    def extract_keywords(self, content: str) -> List[str]:
        """提取关键词"""
        keywords = []
        for domain, pattern in self.keyword_patterns.items():
            matches = re.findall(pattern, content, re.IGNORECASE)
            keywords.extend(matches)
        return list(set(keywords))

class NetworkKnowledgeFetcher:
    """网络知识获取器"""
    
    def __init__(self):
        self.session = requests.Session()
        self.session.timeout = CONFIG["network_fetch_timeout"]
        self.session.headers.update({
            'User-Agent': 'MTSCOS-AI-Learning/1.0 (+https://github.com/wuchenghao15)'
        })
    
    def fetch_from_wikipedia(self, query: str) -> List[Dict]:
        """从维基百科获取知识"""
        try:
            url = f"{CONFIG['knowledge_sources'][0]['url']}?action=query&list=search&srsearch={quote(query)}&format=json&srlimit=3"
            response = self.session.get(url)
            if response.status_code == 200:
                data = response.json()
                results = []
                for item in data.get('query', {}).get('search', []):
                    results.append({
                        "title": item.get('title', ''),
                        "snippet": item.get('snippet', ''),
                        "source": "wikipedia",
                        "url": f"https://zh.wikipedia.org/wiki/{quote(item.get('title', ''))}"
                    })
                return results
        except Exception as e:
            logger.error(f"维基百科获取失败: {str(e)}")
        return []
    
    def fetch_from_github(self, query: str) -> List[Dict]:
        """从GitHub搜索获取知识"""
        try:
            url = f"{CONFIG['knowledge_sources'][1]['url']}?q={quote(query)}+language:python&sort=stars&order=desc&per_page=3"
            response = self.session.get(url)
            if response.status_code == 200:
                data = response.json()
                results = []
                for item in data.get('items', []):
                    results.append({
                        "title": item.get('name', ''),
                        "snippet": item.get('description', ''),
                        "source": "github",
                        "url": item.get('html_url', ''),
                        "stars": item.get('stargazers_count', 0)
                    })
                return results
        except Exception as e:
            logger.error(f"GitHub搜索失败: {str(e)}")
        return []
    
    def fetch_knowledge(self, domain: str, keywords: List[str]) -> List[Dict]:
        """根据领域和关键词获取知识"""
        all_knowledge = []
        
        for keyword in keywords[:3]:
            wiki_results = self.fetch_from_wikipedia(f"{domain} {keyword}")
            github_results = self.fetch_from_github(f"{domain} {keyword}")
            
            for result in wiki_results + github_results:
                evaluator = KnowledgeQualityEvaluator()
                content = f"{result.get('title', '')} {result.get('snippet', '')}"
                confidence = evaluator.evaluate_confidence(content)
                
                if confidence >= CONFIG["min_confidence_threshold"]:
                    all_knowledge.append({
                        "id": f"network_{int(time.time())}_{len(all_knowledge)}",
                        "domain": domain,
                        "title": result.get('title', ''),
                        "content": content,
                        "source": result.get('source', 'network'),
                        "url": result.get('url', ''),
                        "confidence": confidence,
                        "keywords": evaluator.extract_keywords(content),
                        "extracted_at": datetime.now(timezone.utc).isoformat()
                    })
        
        return sorted(all_knowledge, key=lambda x: x['confidence'], reverse=True)[:CONFIG["max_knowledge_per_fetch"]]

class UpgradeMaintenanceLearner:
    """升级维护自我学习器"""
    
    def __init__(self, db_path: str):
        self.db_path = db_path
    
    def analyze_errors_and_fixes(self) -> List[Dict]:
        """分析错误修复历史，发现学习重点"""
        knowledge_list = []
        
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT pe.error_content, pe.error_type, ef.fix_strategy, 
                       ef.fix_implementation, pe.created_at
                FROM project_errors pe
                JOIN error_fixes ef ON pe.id = ef.error_id
                WHERE pe.status = 'fixed'
                ORDER BY pe.created_at DESC
                LIMIT 10
            ''')
            
            for row in cursor.fetchall():
                error_content, error_type, fix_strategy, fix_implementation, created_at = row
                
                insights = self._extract_insights(error_content, fix_strategy, fix_implementation)
                
                knowledge_list.append({
                    "id": f"maintenance_{int(time.time())}_{len(knowledge_list)}",
                    "domain": self._map_error_to_domain(error_type),
                    "title": f"修复: {error_type}",
                    "content": {
                        "problem": error_content,
                        "strategy": fix_strategy,
                        "implementation": fix_implementation,
                        "insights": insights
                    },
                    "source": "maintenance",
                    "confidence": 0.9,
                    "extracted_at": created_at or datetime.now(timezone.utc).isoformat()
                })
            
            conn.close()
        except Exception as e:
            logger.error(f"分析错误修复历史失败: {str(e)}")
        
        return knowledge_list
    
    def _extract_insights(self, error: str, strategy: str, implementation: str) -> List[str]:
        """从修复中提取洞察"""
        insights = []
        
        if "CSRF" in error or "csrf" in error.lower():
            insights.append("CSRF防护是Web安全的重要环节，需持续关注")
        
        if "SQL" in error or "database" in error.lower():
            insights.append("数据库操作需要严格的参数化处理")
        
        if "timeout" in error.lower():
            insights.append("网络请求需要合理的超时设置")
        
        if "import" in error or "module" in error.lower():
            insights.append("依赖管理和导入路径需要仔细检查")
        
        if "version" in strategy.lower() or "upgrade" in strategy.lower():
            insights.append("版本升级需要兼容性测试")
        
        if "template" in implementation.lower():
            insights.append("模板系统需要统一的样式规范")
        
        if insights:
            insights.append("从实际问题中学习是最有效的学习方式")
        
        return insights
    
    def _map_error_to_domain(self, error_type: str) -> str:
        """将错误类型映射到学习领域"""
        error_lower = (error_type or "").lower()
        
        domain_mapping = {
            "security": "Security",
            "database": "Database",
            "performance": "Performance",
            "template": "Flask",
            "import": "Flask",
            "api": "Flask",
            "network": "Performance",
            "configuration": "DevOps"
        }
        
        for keyword, domain in domain_mapping.items():
            if keyword in error_lower:
                return domain
        
        return "general"

class LearningDirectionDiscoverer:
    """学习方向发现器"""
    
    def __init__(self, db_path: str):
        self.db_path = db_path
    
    def discover_learning_gaps(self) -> List[Dict]:
        """发现学习缺口"""
        gaps = []
        
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT feature_type, COUNT(*) as count
                FROM ai_brain_features
                GROUP BY feature_type
                ORDER BY count ASC
            ''')
            
            type_counts = dict(cursor.fetchall())
            
            for domain in CONFIG["learning_domains"]:
                domain_name = domain["name"]
                count = type_counts.get(domain_name.lower(), type_counts.get(domain_name, 0))
                
                if count < 5:
                    gaps.append({
                        "domain": domain_name,
                        "current_count": count,
                        "priority": domain["priority"],
                        "reason": f"{domain_name}领域知识不足(仅{count}条)，需要增加采集",
                        "suggested_keywords": domain["keywords"]
                    })
            
            conn.close()
        except Exception as e:
            logger.error(f"发现学习缺口失败: {str(e)}")
        
        return sorted(gaps, key=lambda x: x['priority'] == 'high', reverse=True)
    
    def discover_hot_topics(self) -> List[Dict]:
        """发现热门学习主题"""
        hot_topics = []
        
        trending_keywords = [
            {"keyword": "AI Agent", "domain": "AI", "reason": "AI Agent技术正在改变软件开发模式"},
            {"keyword": "RAG", "domain": "AI", "reason": "检索增强生成是当前AI应用热点"},
            {"keyword": "向量数据库", "domain": "Database", "reason": "向量数据库是AI应用关键基础设施"},
            {"keyword": "云原生", "domain": "Architecture", "reason": "云原生技术是系统现代化关键"},
            {"keyword": "零信任", "domain": "Security", "reason": "零信任安全架构是现代安全体系核心"},
            {"keyword": "大语言模型", "domain": "AI", "reason": "LLM技术发展迅速"}
        ]
        
        for topic in trending_keywords:
            hot_topics.append({
                "domain": topic["domain"],
                "topic": topic["keyword"],
                "reason": topic["reason"],
                "confidence": 0.7 + (0.05 * trending_keywords.index(topic))
            })
        
        return hot_topics

class RulesWriter:
    """规则自动写入器"""
    
    def __init__(self, rules_file: str):
        self.rules_file = rules_file
        self.rules = []
    
    def load_rules(self):
        """加载现有规则"""
        if os.path.exists(self.rules_file):
            try:
                with open(self.rules_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                    rule_blocks = content.split('---')
                    for block in rule_blocks:
                        if '##' in block:
                            match = re.search(r'##\s+(\w+)', block)
                            if match:
                                self.rules.append(match.group(1))
            except Exception as e:
                logger.error(f"加载规则失败: {str(e)}")
    
    def generate_rule_id(self, domain: str, topic: str) -> str:
        """生成规则ID - 统一规则编号体系"""
        safe_topic = re.sub(r'[^A-Za-z0-9_-]', '_', topic)[:20]
        safe_topic = safe_topic.strip('_')
        if not safe_topic:
            safe_topic = 'TOPIC'
        return f"R-LEARN-{domain.upper()}-{safe_topic.upper()}"
    
    def add_rule(self, domain: str, topic: str, description: str, 
                 confidence: float, source: str, priority: str = "medium") -> bool:
        """添加新规则"""
        rule_id = self.generate_rule_id(domain, topic)
        
        if rule_id in self.rules:
            logger.info(f"规则已存在: {rule_id}")
            return False
        
        self.rules.append(rule_id)
        
        rule = {
            "rule_id": rule_id,
            "rule_name": f"自我学习-{domain}-{topic}",
            "rule_value": 1,
            "rule_type": "learning",
            "learning_domain": domain,
            "priority": priority,
            "discovery_source": source,
            "confidence": confidence,
            "description": description,
            "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }
        
        self._append_to_rules_file(rule)
        logger.info(f"新增规则: {rule_id}")
        return True
    
    def _append_to_rules_file(self, rule: Dict):
        """追加规则到文件 - 统一规则格式"""
        rule_content = f"""

---

### {rule['rule_id']}

**规则名称**: {rule['rule_name']}
**规则值**: {rule['rule_value']}
**规则类型**: {rule['rule_type']}
**学习领域**: {rule['learning_domain']}
**优先级**: {rule['priority']}
**发现来源**: {rule['discovery_source']}
**置信度**: {rule['confidence']:.2f}
**描述**: {rule['description']}
**执行状态**: ✅ 已启用
**创建时间**: {rule['created_at']}"""
        
        try:
            with open(self.rules_file, 'r', encoding='utf-8') as f:
                content = f.read()
            
            count_match = re.search(r'规则总数.*: (\d+)', content)
            if count_match:
                new_count = int(count_match.group(1)) + 1
                content = re.sub(r'规则总数.*: \d+', f'规则总数: {new_count}', content)
            
            content += rule_content
            
            with open(self.rules_file, 'w', encoding='utf-8') as f:
                f.write(content)
        except Exception as e:
            logger.error(f"写入规则失败: {str(e)}")

class BrainDatabaseManager:
    """脑库数据库管理器"""
    
    def __init__(self, db_path: str):
        self.db_path = db_path
        self._initialize_tables()
    
    def _initialize_tables(self):
        """初始化数据库表"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS ai_brain_knowledge (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                knowledge_id TEXT UNIQUE NOT NULL,
                title TEXT NOT NULL,
                content TEXT NOT NULL,
                domain TEXT NOT NULL,
                source TEXT NOT NULL,
                url TEXT,
                confidence REAL NOT NULL DEFAULT 0.5,
                keywords TEXT,
                priority TEXT DEFAULT 'medium',
                is_active INTEGER DEFAULT 1,
                extracted_at TEXT NOT NULL,
                processed_at TEXT,
                applied_count INTEGER DEFAULT 0,
                last_applied_at TEXT
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS learning_rules (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                rule_id TEXT UNIQUE NOT NULL,
                rule_name TEXT NOT NULL,
                domain TEXT NOT NULL,
                topic TEXT NOT NULL,
                description TEXT,
                confidence REAL NOT NULL,
                priority TEXT DEFAULT 'medium',
                is_active INTEGER DEFAULT 1,
                created_at TEXT NOT NULL,
                last_executed_at TEXT,
                execution_count INTEGER DEFAULT 0
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS learning_records (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                domain TEXT NOT NULL,
                topic TEXT NOT NULL,
                knowledge_count INTEGER NOT NULL,
                learning_time TEXT NOT NULL,
                source TEXT NOT NULL,
                success INTEGER DEFAULT 1
            )
        ''')
        
        conn.commit()
        conn.close()
    
    def add_knowledge(self, knowledge_list: List[Dict]) -> int:
        """添加知识到脑库"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        inserted_count = 0
        
        for knowledge in knowledge_list:
            try:
                cursor.execute('''
                    INSERT OR IGNORE INTO ai_brain_knowledge (
                        knowledge_id, title, content, domain, source, url,
                        confidence, keywords, extracted_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    knowledge.get('id', ''),
                    knowledge.get('title', ''),
                    str(knowledge.get('content', '')),
                    knowledge.get('domain', 'general'),
                    knowledge.get('source', 'unknown'),
                    knowledge.get('url', ''),
                    knowledge.get('confidence', 0.5),
                    json.dumps(knowledge.get('keywords', [])),
                    knowledge.get('extracted_at', datetime.now(timezone.utc).isoformat())
                ))
                
                if cursor.rowcount > 0:
                    inserted_count += 1
            except Exception as e:
                logger.error(f"添加知识失败: {str(e)}")
        
        conn.commit()
        conn.close()
        return inserted_count
    
    def add_rule(self, rule: Dict) -> bool:
        """添加学习规则"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            cursor.execute('''
                INSERT OR IGNORE INTO learning_rules (
                    rule_id, rule_name, domain, topic, description,
                    confidence, priority, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                rule.get('rule_id', ''),
                rule.get('rule_name', ''),
                rule.get('domain', ''),
                rule.get('topic', ''),
                rule.get('description', ''),
                rule.get('confidence', 0.5),
                rule.get('priority', 'medium'),
                rule.get('created_at', datetime.now().isoformat())
            ))
            
            conn.commit()
            success = cursor.rowcount > 0
        except Exception as e:
            logger.error(f"添加规则失败: {str(e)}")
            success = False
        
        conn.close()
        return success
    
    def record_learning(self, domain: str, topic: str, knowledge_count: int, source: str):
        """记录学习记录"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO learning_records (domain, topic, knowledge_count, learning_time, source)
            VALUES (?, ?, ?, ?, ?)
        ''', (domain, topic, knowledge_count, datetime.now(timezone.utc).isoformat(), source))
        
        conn.commit()
        conn.close()
    
    def get_knowledge_count(self) -> int:
        """获取知识总数"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("SELECT COUNT(*) FROM ai_brain_knowledge")
        count = cursor.fetchone()[0]
        
        conn.close()
        return count
    
    def get_rule_count(self) -> int:
        """获取规则总数"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("SELECT COUNT(*) FROM learning_rules")
        count = cursor.fetchone()[0]
        
        conn.close()
        return count

class LearningPolicyExecutor:
    """学习政策执行器"""
    
    def __init__(self, db_path: str, rules_file: str):
        self.db_manager = BrainDatabaseManager(db_path)
        self.rules_writer = RulesWriter(rules_file)
        self.network_fetcher = NetworkKnowledgeFetcher()
        self.maintenance_learner = UpgradeMaintenanceLearner(db_path)
        self.direction_discoverer = LearningDirectionDiscoverer(db_path)
        self.rules_writer.load_rules()
        self.is_running = False
        self.thread = None
    
    def start(self):
        """启动学习政策执行器"""
        if not self.is_running:
            self.is_running = True
            self.thread = threading.Thread(target=self._learning_loop)
            self.thread.start()
            logger.info("AI自我学习赋能系统已启动")
    
    def stop(self):
        """停止学习政策执行器"""
        self.is_running = False
        if self.thread and self.thread.is_alive():
            self.thread.join(timeout=10)
        logger.info("AI自我学习赋能系统已停止")
    
    def _learning_loop(self):
        """学习循环"""
        cycle_count = 0
        
        while self.is_running:
            try:
                cycle_count += 1
                logger.info(f"=== 第 {cycle_count} 次学习循环 ===")
                
                self._execute_maintenance_learning()
                self._execute_network_learning()
                self._discover_and_update_rules()
                
                logger.info(f"=== 第 {cycle_count} 次学习循环完成 ===")
                time.sleep(CONFIG["learning_interval_minutes"] * 60)
                
            except Exception as e:
                logger.error(f"学习循环出错: {str(e)}")
                time.sleep(300)
    
    def _execute_maintenance_learning(self):
        """执行维护学习"""
        logger.info("执行维护学习...")
        
        maintenance_knowledge = self.maintenance_learner.analyze_errors_and_fixes()
        if maintenance_knowledge:
            inserted = self.db_manager.add_knowledge(maintenance_knowledge)
            logger.info(f"从维护修复中学习了 {inserted} 条知识")
            
            for knowledge in maintenance_knowledge:
                self.db_manager.record_learning(
                    knowledge.get('domain', 'general'),
                    knowledge.get('title', ''),
                    1,
                    'maintenance'
                )
    
    def _execute_network_learning(self):
        """执行网络学习"""
        logger.info("执行网络学习...")
        
        for domain_config in CONFIG["learning_domains"]:
            domain = domain_config["name"]
            keywords = domain_config["keywords"]
            
            logger.info(f"学习领域: {domain}")
            network_knowledge = self.network_fetcher.fetch_knowledge(domain, keywords)
            
            if network_knowledge:
                inserted = self.db_manager.add_knowledge(network_knowledge)
                logger.info(f"从网络获取了 {inserted} 条 {domain} 领域知识")
                
                for knowledge in network_knowledge:
                    self.db_manager.record_learning(
                        domain,
                        knowledge.get('title', ''),
                        1,
                        'network'
                    )
    
    def _discover_and_update_rules(self):
        """发现并更新学习规则"""
        logger.info("发现学习方向和规则...")
        
        gaps = self.direction_discoverer.discover_learning_gaps()
        hot_topics = self.direction_discoverer.discover_hot_topics()
        
        for gap in gaps:
            rule_added = self.rules_writer.add_rule(
                domain=gap["domain"],
                topic=f"knowledge_gap",
                description=gap["reason"],
                confidence=0.8,
                source="brain_analysis",
                priority=gap["priority"]
            )
            
            if rule_added:
                self.db_manager.add_rule({
                    "rule_id": self.rules_writer.generate_rule_id(gap["domain"], "knowledge_gap"),
                    "rule_name": f"自我学习-{gap['domain']}-知识缺口",
                    "domain": gap["domain"],
                    "topic": "knowledge_gap",
                    "description": gap["reason"],
                    "confidence": 0.8,
                    "priority": gap["priority"],
                    "created_at": datetime.now().isoformat()
                })
        
        for topic in hot_topics:
            rule_added = self.rules_writer.add_rule(
                domain=topic["domain"],
                topic=topic["topic"],
                description=topic["reason"],
                confidence=topic["confidence"],
                source="self_exploration",
                priority="medium"
            )
            
            if rule_added:
                self.db_manager.add_rule({
                    "rule_id": self.rules_writer.generate_rule_id(topic["domain"], topic["topic"]),
                    "rule_name": f"自我学习-{topic['domain']}-{topic['topic']}",
                    "domain": topic["domain"],
                    "topic": topic["topic"],
                    "description": topic["reason"],
                    "confidence": topic["confidence"],
                    "priority": "medium",
                    "created_at": datetime.now().isoformat()
                })
        
        logger.info("规则更新完成")
    
    def get_status(self) -> Dict:
        """获取系统状态"""
        return {
            "is_running": self.is_running,
            "knowledge_count": self.db_manager.get_knowledge_count(),
            "rule_count": self.db_manager.get_rule_count(),
            "learning_domains": [d["name"] for d in CONFIG["learning_domains"]],
            "last_updated": datetime.now(timezone.utc).isoformat()
        }
    
    def manual_trigger(self):
        """手动触发一次学习循环"""
        logger.info("手动触发学习循环")
        self._execute_maintenance_learning()
        self._execute_network_learning()
        self._discover_and_update_rules()
        logger.info("手动学习循环完成")

if __name__ == "__main__":
    system = LearningPolicyExecutor(
        CONFIG["db_path"],
        CONFIG["rules_file"]
    )
    
    if len(sys.argv) > 1:
        command = sys.argv[1]
        
        if command == "start":
            print("AI自我学习赋能系统启动中...")
            system.start()
            try:
                while True:
                    time.sleep(1)
            except KeyboardInterrupt:
                system.stop()
                print("AI自我学习赋能系统已停止")
        
        elif command == "stop":
            system.stop()
            print("AI自我学习赋能系统已停止")
        
        elif command == "status":
            status = system.get_status()
            print(json.dumps(status, indent=2, ensure_ascii=False))
        
        elif command == "learn":
            system.manual_trigger()
            print("手动学习完成")
        
        elif command == "discover":
            discoverer = LearningDirectionDiscoverer(CONFIG["db_path"])
            gaps = discoverer.discover_learning_gaps()
            hot_topics = discoverer.discover_hot_topics()
            print("学习缺口:")
            for gap in gaps:
                print(f"  - {gap['domain']}: {gap['reason']}")
            print("\n热门主题:")
            for topic in hot_topics:
                print(f"  - {topic['topic']}: {topic['reason']}")
        
        else:
            print(f"未知命令: {command}")
            print("可用命令: start, stop, status, learn, discover")
    else:
        print("AI自我学习赋能系统")
        print("可用命令: start, stop, status, learn, discover")