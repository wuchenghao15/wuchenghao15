#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""强化版AI自主学习系统 - 自动学习、知识共享和能力增强"""

import os
import re
# import json removed - using database storage
import sqlite3
import logging
import requests
import subprocess
import threading
import time
from datetime import datetime
from typing import Dict, List, Any, Tuple
from collections import defaultdict

logging.basicConfig(
    level=logging.INFO, 
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('ai_learning_system')

class EnhancedAILearningSystem:
    def __init__(self):
        self.project_dir = os.getcwd()
        self.db_path = 'app.db'
        self.is_running = False
        self.knowledge_base = {}
        self.learning_modules = {}
        self.init_learning_modules()
    
    def init_learning_modules(self):
        """初始化学习模块"""
        self.learning_modules = {
            'project_analyzer': ProjectAnalyzer(self),
            'runtime_learner': RuntimeLearner(self),
            'web_crawler': WebKnowledgeCrawler(self),
            'knowledge_integrator': KnowledgeIntegrator(self),
            'self_enhancer': SelfEnhancer(self),
            'brain_sync': BrainDatabaseSync(self)
        }
        logger.info("AI学习模块初始化完成")
    
    def start(self):
        """启动AI学习系统"""
        print("="*80)
        print("          强化版AI自主学习系统 - 启动中...")
        print("="*80)
        
        self.is_running = True
        
        for name, module in self.learning_modules.items():
            module.start()
            print(f"  ✓ {name} 启动成功")
        
        print("\n" + "="*80)
        print("          AI自主学习系统已启动！")
        print("="*80)
        
        self.main_learning_loop()
    
    def main_learning_loop(self):
        """主学习循环"""
        cycle = 0
        while self.is_running:
            cycle += 1
            print(f"\n[学习周期 #{cycle}] 开始学习...")
            
            try:
                # 分析项目代码
                self.learning_modules['project_analyzer'].analyze_project()
                
                # 学习运行时数据
                self.learning_modules['runtime_learner'].learn_from_runtime()
                
                # 从网络获取知识
                self.learning_modules['web_crawler'].crawl_knowledge()
                
                # 整合知识
                self.learning_modules['knowledge_integrator'].integrate_knowledge()
                
                # 自我增强
                self.learning_modules['self_enhancer'].enhance_abilities()
                
                # 同步到脑库
                self.learning_modules['brain_sync'].sync_to_brain()
                
                print(f"[学习周期 #{cycle}] 完成！")
                
            except Exception as e:
                logger.error(f"学习周期 #{cycle} 出错: {e}")
            
            time.sleep(3600)  # 每小时学习一次
    
    def stop(self):
        """停止学习系统"""
        print("\n" + "="*80)
        print("          AI自主学习系统 - 停止中...")
        print("="*80)
        
        self.is_running = False
        
        for name, module in self.learning_modules.items():
            module.stop()
            print(f"  ✓ {name} 已停止")
        
        print("\n" + "="*80)
        print("          AI自主学习系统已停止")
        print("="*80)

class ProjectAnalyzer:
    """项目分析器 - 从项目代码中学习"""
    def __init__(self, parent):
        self.parent = parent
        self.is_active = False
        self.analysis_results = []
    
    def start(self):
        self.is_active = True
        logger.info("项目分析器启动")
    
    def stop(self):
        self.is_active = False
    
    def analyze_project(self):
        """分析项目代码"""
        if not self.is_active:
            return
        
        logger.info("分析项目代码...")
        
        patterns_to_learn = [
            (r'def\s+(\w+)\s*\(', '函数定义'),
            (r'class\s+(\w+)', '类定义'),
            (r'@(\w+)', '装饰器'),
            (r'import\s+(\w+)', '导入'),
            (r'from\s+(\w+)\s+import', '从模块导入')
        ]
        
        code_patterns = defaultdict(int)
        
        for root, dirs, files in os.walk(self.parent.project_dir):
            if 'node_modules' in root or '.git' in root:
                continue
            for file in files:
                if file.endswith('.py'):
                    try:
                        with open(os.path.join(root, file), 'r', encoding='utf-8') as f:
                            content = f.read()
                            
                            for pattern, desc in patterns_to_learn:
                                matches = re.findall(pattern, content)
                                for match in matches:
                                    code_patterns[(desc, match)] += 1
                    except Exception as e:
                        pass
        
        self.analysis_results.append({
            'timestamp': datetime.now().isoformat(),
            'patterns': dict(code_patterns),
            'total_patterns': len(code_patterns)
        })
        
        logger.info(f"发现 {len(code_patterns)} 种代码模式")
        self.save_analysis_results(code_patterns)
    
    def save_analysis_results(self, patterns):
        """保存分析结果到数据库"""
        try:
            conn = sqlite3.connect(self.parent.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS code_patterns (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    pattern_type TEXT,
                    pattern_name TEXT,
                    occurrence_count INTEGER,
                    last_seen TEXT
                )
            ''')
            
            for (pattern_type, pattern_name), count in patterns.items():
                cursor.execute('''
                    INSERT OR REPLACE INTO code_patterns 
                    (pattern_type, pattern_name, occurrence_count, last_seen)
                    VALUES (?, ?, COALESCE((SELECT occurrence_count FROM code_patterns WHERE pattern_type=? AND pattern_name=?), 0) + ?, ?)
                ''', (pattern_type, pattern_name, pattern_type, pattern_name, count, datetime.now().isoformat()))
            
            conn.commit()
            conn.close()
        except Exception as e:
            logger.error(f"保存分析结果失败: {e}")

class RuntimeLearner:
    """运行时学习器 - 从运行时数据中学习"""
    def __init__(self, parent):
        self.parent = parent
        self.is_active = False
        self.runtime_data = []
    
    def start(self):
        self.is_active = True
        logger.info("运行时学习器启动")
    
    def stop(self):
        self.is_active = False
    
    def learn_from_runtime(self):
        """从运行时数据学习"""
        if not self.is_active:
            return
        
        logger.info("学习运行时数据...")
        
        runtime_insights = []
        
        # 学习系统指标
        metrics = self.get_system_metrics()
        runtime_insights.append({
            'type': 'system_metrics',
            'data': metrics,
            'timestamp': datetime.now().isoformat()
        })
        
        # 学习修复历史
        fix_patterns = self.learn_from_fix_history()
        runtime_insights.append({
            'type': 'fix_patterns',
            'data': fix_patterns,
            'timestamp': datetime.now().isoformat()
        })
        
        self.runtime_data.extend(runtime_insights)
        self.save_runtime_insights(runtime_insights)
    
    def get_system_metrics(self):
        """获取系统指标"""
        try:
            result = subprocess.run(['top', '-l', '1', '-n', '0'], capture_output=True, text=True)
            cpu_usage = 0
            for line in result.stdout.split('\n'):
                if 'CPU usage' in line:
                    parts = line.split()
                    cpu_usage = float(parts[3].replace('%', ''))
            return {'cpu_usage': cpu_usage}
        except:
            return {'cpu_usage': 0}
    
    def learn_from_fix_history(self):
        """从修复历史学习"""
        try:
            conn = sqlite3.connect(self.parent.db_path)
            cursor = conn.cursor()
            
            cursor.execute('SELECT issue_type, COUNT(*) FROM code_fix_logs GROUP BY issue_type')
            fix_patterns = {row[0]: row[1] for row in cursor.fetchall()}
            
            conn.close()
            return fix_patterns
        except Exception as e:
            logger.error(f"学习修复历史失败: {e}")
            return {}
    
    def save_runtime_insights(self, insights):
        """保存运行时洞察到数据库"""
        try:
            conn = sqlite3.connect(self.parent.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS runtime_insights (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    insight_type TEXT,
                    insight_data TEXT,
                    timestamp TEXT
                )
            ''')
            
            for insight in insights:
                cursor.execute('''
                    INSERT INTO runtime_insights (insight_type, insight_data, timestamp)
                    VALUES (?, ?, ?)
                ''', (insight['type'], str(insight['data']), insight['timestamp']))
            
            conn.commit()
            conn.close()
        except Exception as e:
            logger.error(f"保存运行时洞察失败: {e}")

class WebKnowledgeCrawler:
    """网络知识爬虫 - 从网络获取AI相关知识"""
    def __init__(self, parent):
        self.parent = parent
        self.is_active = False
        self.crawled_knowledge = []
        
        self.knowledge_sources = [
            {'name': 'Python技巧', 'url': 'https://raw.githubusercontent.com/vinta/awesome-python/master/README.md'},
            {'name': 'Flask最佳实践', 'url': 'https://flask.palletsprojects.com/en/2.0.x/'},
            {'name': 'SQLite指南', 'url': 'https://www.sqlite.org/docs.html'}
        ]
    
    def start(self):
        self.is_active = True
        logger.info("网络知识爬虫启动")
    
    def stop(self):
        self.is_active = False
    
    def crawl_knowledge(self):
        """爬取网络知识"""
        if not self.is_active:
            return
        
        logger.info("爬取网络知识...")
        
        for source in self.knowledge_sources:
            try:
                response = requests.get(source['url'], timeout=10)
                if response.status_code == 200:
                    knowledge = self.extract_knowledge(source['name'], response.text)
                    self.crawled_knowledge.extend(knowledge)
                    logger.info(f"从 {source['name']} 获取 {len(knowledge)} 条知识")
            except Exception as e:
                logger.error(f"爬取 {source['name']} 失败: {e}")
        
        self.save_crawled_knowledge()
    
    def extract_knowledge(self, source_name, content):
        """从内容中提取知识"""
        knowledge_items = []
        
        if source_name == 'Python技巧':
            # 提取Python库和工具
            lines = content.split('\n')
            for line in lines:
                if line.startswith('- ['):
                    match = re.match(r'-\s*\[([^\]]+)\]\([^)]+\)', line)
                    if match:
                        knowledge_items.append({
                            'source': source_name,
                            'category': 'Python库',
                            'title': match.group(1),
                            'content': line.strip(),
                            'timestamp': datetime.now().isoformat()
                        })
        
        return knowledge_items
    
    def save_crawled_knowledge(self):
        """保存爬取的知识到数据库"""
        try:
            conn = sqlite3.connect(self.parent.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS web_knowledge (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    source TEXT,
                    category TEXT,
                    title TEXT,
                    content TEXT,
                    timestamp TEXT
                )
            ''')
            
            for item in self.crawled_knowledge:
                cursor.execute('''
                    INSERT OR IGNORE INTO web_knowledge 
                    (source, category, title, content, timestamp)
                    VALUES (?, ?, ?, ?, ?)
                ''', (item['source'], item['category'], item['title'], item['content'], item['timestamp']))
            
            conn.commit()
            conn.close()
        except Exception as e:
            logger.error(f"保存网络知识失败: {e}")

class KnowledgeIntegrator:
    """知识整合器 - 将知识整合到脑库"""
    def __init__(self, parent):
        self.parent = parent
        self.is_active = False
    
    def start(self):
        self.is_active = True
        logger.info("知识整合器启动")
    
    def stop(self):
        self.is_active = False
    
    def integrate_knowledge(self):
        """整合所有知识"""
        if not self.is_active:
            return
        
        logger.info("整合知识到脑库...")
        
        try:
            conn = sqlite3.connect(self.parent.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS ai_brain_integrated (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    knowledge_type TEXT,
                    knowledge_key TEXT,
                    knowledge_value TEXT,
                    confidence REAL DEFAULT 0.8,
                    usage_count INTEGER DEFAULT 0,
                    source TEXT,
                    timestamp TEXT
                )
            ''')
            
            # 整合代码模式
            cursor.execute('SELECT pattern_type, pattern_name, occurrence_count FROM code_patterns')
            for row in cursor.fetchall():
                cursor.execute('''
                    INSERT OR REPLACE INTO ai_brain_integrated
                    (knowledge_type, knowledge_key, knowledge_value, source, timestamp)
                    VALUES (?, ?, ?, ?, ?)
                ''', ('code_pattern', row[1], f"{row[0]}: {row[2]} occurrences", 'project_analysis', datetime.now().isoformat()))
            
            # 整合运行时洞察
            cursor.execute('SELECT insight_type, insight_data FROM runtime_insights ORDER BY timestamp DESC LIMIT 10')
            for row in cursor.fetchall():
                cursor.execute('''
                    INSERT OR REPLACE INTO ai_brain_integrated
                    (knowledge_type, knowledge_key, knowledge_value, source, timestamp)
                    VALUES (?, ?, ?, ?, ?)
                ''', ('runtime_insight', row[0], row[1], 'runtime_learning', datetime.now().isoformat()))
            
            # 整合网络知识
            cursor.execute('SELECT category, title, content FROM web_knowledge')
            for row in cursor.fetchall():
                cursor.execute('''
                    INSERT OR REPLACE INTO ai_brain_integrated
                    (knowledge_type, knowledge_key, knowledge_value, source, timestamp)
                    VALUES (?, ?, ?, ?, ?)
                ''', ('web_knowledge', row[1], row[2], 'web_crawler', datetime.now().isoformat()))
            
            conn.commit()
            conn.close()
            
            logger.info("知识整合完成")
        except Exception as e:
            logger.error(f"知识整合失败: {e}")

class SelfEnhancer:
    """自我增强器 - 自动增强AI能力"""
    def __init__(self, parent):
        self.parent = parent
        self.is_active = False
        self.enhancement_history = []
    
    def start(self):
        self.is_active = True
        logger.info("自我增强器启动")
    
    def stop(self):
        self.is_active = False
    
    def enhance_abilities(self):
        """增强AI能力"""
        if not self.is_active:
            return
        
        logger.info("自我增强中...")
        
        enhancements = []
        
        # 分析知识缺口并增强
        gap_analysis = self.analyze_knowledge_gaps()
        for gap in gap_analysis:
            enhancement = self.generate_enhancement(gap)
            if enhancement:
                enhancements.append(enhancement)
        
        self.enhancement_history.extend(enhancements)
        self.save_enhancements(enhancements)
    
    def analyze_knowledge_gaps(self):
        """分析知识缺口"""
        gaps = []
        
        try:
            conn = sqlite3.connect(self.parent.db_path)
            cursor = conn.cursor()
            
            cursor.execute('SELECT knowledge_type, COUNT(*) FROM ai_brain_integrated GROUP BY knowledge_type')
            type_counts = dict(cursor.fetchall())
            
            # 识别缺口
            expected_types = ['code_pattern', 'runtime_insight', 'web_knowledge', 'fix_strategy', 'optimization']
            for expected in expected_types:
                if expected not in type_counts or type_counts[expected] < 10:
                    gaps.append({'type': expected, 'current_count': type_counts.get(expected, 0), 'needed': 10})
            
            conn.close()
        except Exception as e:
            logger.error(f"分析知识缺口失败: {e}")
        
        return gaps
    
    def generate_enhancement(self, gap):
        """生成增强方案"""
        enhancement = {
            'gap_type': gap['type'],
            'current_count': gap['current_count'],
            'needed': gap['needed'],
            'strategy': f"需要增加 {gap['needed'] - gap['current_count']} 条 {gap['type']} 知识",
            'timestamp': datetime.now().isoformat()
        }
        return enhancement
    
    def save_enhancements(self, enhancements):
        """保存增强记录"""
        try:
            conn = sqlite3.connect(self.parent.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS ai_enhancements (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    gap_type TEXT,
                    strategy TEXT,
                    executed INTEGER DEFAULT 0,
                    timestamp TEXT
                )
            ''')
            
            for enhancement in enhancements:
                cursor.execute('''
                    INSERT INTO ai_enhancements (gap_type, strategy, timestamp)
                    VALUES (?, ?, ?)
                ''', (enhancement['gap_type'], enhancement['strategy'], enhancement['timestamp']))
            
            conn.commit()
            conn.close()
        except Exception as e:
            logger.error(f"保存增强记录失败: {e}")

class BrainDatabaseSync:
    """脑库同步器 - 同步知识到中央脑库"""
    def __init__(self, parent):
        self.parent = parent
        self.is_active = False
        self.sync_history = []
    
    def start(self):
        self.is_active = True
        logger.info("脑库同步器启动")
    
    def stop(self):
        self.is_active = False
    
    def sync_to_brain(self):
        """同步知识到脑库"""
        if not self.is_active:
            return
        
        logger.info("同步知识到脑库...")
        
        try:
            conn = sqlite3.connect(self.parent.db_path)
            cursor = conn.cursor()
            
            # 确保脑库主表存在
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS ai_brain_knowledge_master (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    knowledge_id TEXT UNIQUE,
                    knowledge_type TEXT,
                    knowledge_key TEXT,
                    knowledge_value TEXT,
                    confidence REAL DEFAULT 0.8,
                    usage_count INTEGER DEFAULT 0,
                    source TEXT,
                    sync_status TEXT DEFAULT 'synced',
                    last_sync TEXT,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # 同步整合的知识到主脑库
            cursor.execute('SELECT knowledge_type, knowledge_key, knowledge_value, source FROM ai_brain_integrated')
            for row in cursor.fetchall():
                knowledge_id = f"{row[0]}_{row[1]}"
                cursor.execute('''
                    INSERT OR REPLACE INTO ai_brain_knowledge_master
                    (knowledge_id, knowledge_type, knowledge_key, knowledge_value, source, last_sync)
                    VALUES (?, ?, ?, ?, ?, ?)
                ''', (knowledge_id, row[0], row[1], row[2], row[3], datetime.now().isoformat()))
            
            conn.commit()
            conn.close()
            
            self.sync_history.append({
                'timestamp': datetime.now().isoformat(),
                'status': 'success'
            })
            
            logger.info("脑库同步完成")
        except Exception as e:
            logger.error(f"脑库同步失败: {e}")
            self.sync_history.append({
                'timestamp': datetime.now().isoformat(),
                'status': 'failed',
                'error': str(e)
            })

def main():
    learning_system = EnhancedAILearningSystem()
    learning_system.start()

if __name__ == "__main__":
    main()