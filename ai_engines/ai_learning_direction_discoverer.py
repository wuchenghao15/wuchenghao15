# -*- coding: utf-8 -*-
#!/usr/bin/env python3
"""
AI学习方向自动发现系统
功能: 自动发现AI学习的知识点和学习方向
自动写入AI自我学习规则到《规则》
"""

import os
import sys
import json
import logging
import threading
import time
import sqlite3
import hashlib
from datetime import datetime
from typing import Dict, List, Optional, Any

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('ai_learning_direction.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


class GapAnalyzer:
    """知识差距分析器"""
    
    def __init__(self, db_path: str = 'ai_brain.db'):
        self.db_path = db_path
        self.knowledge_categories = ['security', 'performance', 'bug_fix', 'tech_update', 
                                     'architecture', 'best_practice', 'industry_report', 'general']
    
    def analyze_knowledge_gaps(self) -> List[Dict]:
        """分析知识差距"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT type, COUNT(*) as count, AVG(confidence) as avg_confidence
            FROM ai_brain_knowledge 
            WHERE is_active = 1 
            GROUP BY type
        ''')
        
        category_stats = {row[0]: {'count': row[1], 'avg_confidence': row[2]} for row in cursor.fetchall()}
        
        cursor.execute('SELECT COUNT(*) FROM ai_brain_knowledge WHERE is_active = 1')
        total_knowledge = cursor.fetchone()[0]
        
        conn.close()
        
        gaps = []
        
        for category in self.knowledge_categories:
            stats = category_stats.get(category, {'count': 0, 'avg_confidence': 0})
            expected_ratio = self._get_expected_ratio(category)
            
            if total_knowledge > 0:
                actual_ratio = stats['count'] / total_knowledge
                gap_score = abs(expected_ratio - actual_ratio)
            else:
                gap_score = expected_ratio
            
            if gap_score > 0.05 or stats['count'] < 10:
                gaps.append({
                    'category': category,
                    'gap_score': gap_score,
                    'current_count': stats['count'],
                    'expected_count': int(total_knowledge * expected_ratio) if total_knowledge > 0 else 50,
                    'avg_confidence': stats['avg_confidence'],
                    'priority': self._calculate_gap_priority(gap_score, category),
                    'action': f"需要补充{category}类知识"
                })
        
        gaps.sort(key=lambda x: x['priority'])
        return gaps
    
    def _get_expected_ratio(self, category: str) -> float:
        """获取各类知识的期望比例"""
        ratio_map = {
            'security': 0.15,
            'performance': 0.15,
            'bug_fix': 0.20,
            'tech_update': 0.20,
            'architecture': 0.10,
            'best_practice': 0.10,
            'industry_report': 0.05,
            'general': 0.05
        }
        return ratio_map.get(category, 0.05)
    
    def _calculate_gap_priority(self, gap_score: float, category: str) -> int:
        """计算差距优先级"""
        priority_multiplier = {
            'security': 1.5,
            'performance': 1.3,
            'bug_fix': 1.4,
            'tech_update': 1.2,
            'architecture': 1.0,
            'best_practice': 1.0,
            'industry_report': 0.8,
            'general': 0.5
        }
        
        adjusted_score = gap_score * priority_multiplier.get(category, 1.0)
        
        if adjusted_score > 0.15:
            return 1
        elif adjusted_score > 0.10:
            return 2
        elif adjusted_score > 0.05:
            return 3
        else:
            return 4


class TrendAnalyzer:
    """趋势分析器"""
    
    def __init__(self):
        self.trend_keywords = {
            'ai_ml': ['artificial intelligence', 'machine learning', 'deep learning', 'neural network', 'llm', 'gpt'],
            'cloud_native': ['cloud native', 'kubernetes', 'docker', 'microservices', 'serverless'],
            'security': ['cybersecurity', 'zero trust', 'encryption', 'vulnerability', 'threat'],
            'performance': ['performance', 'optimization', 'latency', 'throughput', 'scalability'],
            'data': ['big data', 'data engineering', 'data science', 'data analytics', 'data pipeline'],
            'devops': ['devops', 'ci/cd', 'continuous integration', 'continuous deployment', 'monitoring']
        }
    
    def analyze_trends(self, recent_knowledge: List[Dict]) -> List[Dict]:
        """分析技术趋势"""
        trend_scores = {}
        
        for knowledge in recent_knowledge:
            title = str(knowledge.get('title', '')).lower()
            content = str(knowledge.get('content', '')).lower()
            text = f"{title} {content}"
            
            for trend, keywords in self.trend_keywords.items():
                score = sum(1 for keyword in keywords if keyword in text)
                if score > 0:
                    trend_scores[trend] = trend_scores.get(trend, 0) + score
        
        trends = []
        for trend, score in trend_scores.items():
            trends.append({
                'trend': trend,
                'score': score,
                'priority': self._calculate_trend_priority(score),
                'keywords': self.trend_keywords[trend],
                'action': f"关注{trend}趋势,增加相关学习"
            })
        
        trends.sort(key=lambda x: x['priority'])
        return trends
    
    def _calculate_trend_priority(self, score: int) -> int:
        """计算趋势优先级"""
        if score >= 10:
            return 1
        elif score >= 5:
            return 2
        elif score >= 2:
            return 3
        else:
            return 4


class ProblemDrivenDiscoverer:
    """问题驱动学习方向发现器"""
    
    def __init__(self, db_path: str = 'ai_self_awakening.db'):
        self.db_path = db_path
    
    def discover_problem_driven_directions(self) -> List[Dict]:
        """发现问题驱动的学习方向"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT event_type, learning_focus, COUNT(*) as count
            FROM awakening_events 
            WHERE processed = 0 
            GROUP BY event_type, learning_focus
            ORDER BY count DESC
            LIMIT 10
        ''')
        
        problem_directions = []
        for row in cursor.fetchall():
            event_type, learning_focus, count = row
            problem_directions.append({
                'event_type': event_type,
                'learning_focus': learning_focus,
                'frequency': count,
                'priority': self._calculate_problem_priority(event_type, count),
                'action': f"针对{learning_focus}问题进行深入学习"
            })
        
        conn.close()
        
        problem_directions.sort(key=lambda x: x['priority'])
        return problem_directions
    
    def _calculate_problem_priority(self, event_type: str, count: int) -> int:
        """计算问题优先级"""
        priority_map = {
            'security_incident': 1,
            'error_frequency': 2,
            'performance_degradation': 2,
            'upgrade_failure': 3,
            'feature_requests': 4
        }
        
        base_priority = priority_map.get(event_type, 4)
        
        if count >= 5:
            return min(base_priority, 2)
        elif count >= 3:
            return min(base_priority, 3)
        else:
            return base_priority


class SuccessPatternExtractor:
    """成功模式提取器"""
    
    def __init__(self, db_path: str = 'ai_brain.db'):
        self.db_path = db_path
    
    def extract_success_patterns(self) -> List[Dict]:
        """提取成功模式"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT type, source, AVG(confidence) as avg_confidence, COUNT(*) as count
            FROM ai_brain_knowledge 
            WHERE is_active = 1 AND confidence >= 0.85
            GROUP BY type, source
            ORDER BY avg_confidence DESC, count DESC
            LIMIT 10
        ''')
        
        success_patterns = []
        for row in cursor.fetchall():
            knowledge_type, source, avg_confidence, count = row
            success_patterns.append({
                'type': knowledge_type,
                'source': source,
                'avg_confidence': avg_confidence,
                'count': count,
                'priority': 3,
                'action': f"从{source}继续学习{knowledge_type}类高质量知识"
            })
        
        conn.close()
        
        return success_patterns


class RuleAutoUpdater:
    """规则自动更新器"""
    
    def __init__(self, rules_file: str = 'rules.json'):
        self.rules_file = rules_file
    
    def update_rules_with_directions(self, directions: List[Dict]):
        """使用发现的学习方向更新规则"""
        with open(self.rules_file, 'r', encoding='utf-8') as f:
            rules = json.load(f)
        
        learning_priorities = rules.get('learning_policy', {}).get('learning_priorities', [])
        
        for direction in directions:
            existing_priority = None
            for priority in learning_priorities:
                category_match = direction.get('category')
                trend_match = direction.get('trend')
                focus_match = direction.get('learning_focus')
                
                if (category_match and category_match in priority['category']) or \
                   (trend_match and trend_match in priority['category']) or \
                   (focus_match and focus_match in priority['category']):
                    existing_priority = priority
                    break
            
            if existing_priority:
                existing_priority['priority'] = min(existing_priority['priority'], direction.get('priority', 5))
                existing_priority['description'] = direction.get('action', existing_priority['description'])
                logger.info(f"更新现有学习优先级: {existing_priority['category']}")
            else:
                new_category = direction.get('category') or direction.get('trend') or direction.get('learning_focus')
                if new_category:
                    new_priority = {
                        'priority': direction.get('priority', 5),
                        'category': new_category,
                        'description': direction.get('action', f"学习{new_category}相关知识")
                    }
                    learning_priorities.append(new_priority)
                    logger.info(f"添加新学习优先级: {new_category}")
        
        learning_priorities.sort(key=lambda x: x['priority'])
        
        rules['learning_policy']['learning_priorities'] = learning_priorities
        rules['last_updated'] = datetime.now().isoformat()
        
        with open(self.rules_file, 'w', encoding='utf-8') as f:
            json.dump(rules, f, ensure_ascii=False, indent=2)
        
        logger.info("规则文件已更新")
    
    def add_new_knowledge_source(self, source_info: Dict):
        """添加新知识源"""
        with open(self.rules_file, 'r', encoding='utf-8') as f:
            rules = json.load(f)
        
        external_sources = rules.get('knowledge_sources', {}).get('external_sources', [])
        
        source_id = source_info.get('id')
        if source_id not in [s['id'] for s in external_sources]:
            external_sources.append(source_info)
            logger.info(f"添加新知识源: {source_info.get('name')}")
        
        rules['knowledge_sources']['external_sources'] = external_sources
        rules['last_updated'] = datetime.now().isoformat()
        
        with open(self.rules_file, 'w', encoding='utf-8') as f:
            json.dump(rules, f, ensure_ascii=False, indent=2)


class AILearningDirectionDiscoverer:
    """AI学习方向自动发现系统"""
    
    def __init__(self, rules_file: str = 'rules.json'):
        self.rules_file = rules_file
        self.rules = self._load_rules()
        
        self.gap_analyzer = GapAnalyzer()
        self.trend_analyzer = TrendAnalyzer()
        self.problem_discoverer = ProblemDrivenDiscoverer()
        self.success_extractor = SuccessPatternExtractor()
        self.rule_updater = RuleAutoUpdater(rules_file)
        
        self.is_running = False
        self.discovery_thread = None
        self.discovery_interval = 86400
    
    def _load_rules(self) -> Dict:
        """加载规则"""
        try:
            with open(self.rules_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"加载规则文件失败: {str(e)}")
            return {}
    
    def start(self):
        """启动学习方向发现系统"""
        if not self.is_running:
            self.is_running = True
            self.discovery_thread = threading.Thread(target=self._discovery_loop, daemon=True)
            self.discovery_thread.start()
            logger.info("AI学习方向自动发现系统已启动")
    
    def stop(self):
        """停止学习方向发现系统"""
        self.is_running = False
        if self.discovery_thread and self.discovery_thread.is_alive():
            self.discovery_thread.join(timeout=5)
        logger.info("AI学习方向自动发现系统已停止")
    
    def _discovery_loop(self):
        """发现循环"""
        while self.is_running:
            try:
                self.discover_learning_directions()
                time.sleep(self.discovery_interval)
            except Exception as e:
                logger.error(f"发现循环出错: {str(e)}")
                time.sleep(3600)
    
    def discover_learning_directions(self) -> Dict:
        """执行学习方向发现"""
        logger.info("开始发现学习方向...")
        
        gap_directions = self.gap_analyzer.analyze_knowledge_gaps()
        logger.info(f"发现 {len(gap_directions)} 个知识差距方向")
        
        recent_knowledge = self._get_recent_knowledge()
        trend_directions = self.trend_analyzer.analyze_trends(recent_knowledge)
        logger.info(f"发现 {len(trend_directions)} 个趋势方向")
        
        problem_directions = self.problem_discoverer.discover_problem_driven_directions()
        logger.info(f"发现 {len(problem_directions)} 个问题驱动方向")
        
        success_directions = self.success_extractor.extract_success_patterns()
        logger.info(f"发现 {len(success_directions)} 个成功模式方向")
        
        all_directions = gap_directions + trend_directions + problem_directions + success_directions
        
        if all_directions:
            self.rule_updater.update_rules_with_directions(all_directions)
            self.rules = self._load_rules()
        
        result = {
            'gap_directions': len(gap_directions),
            'trend_directions': len(trend_directions),
            'problem_directions': len(problem_directions),
            'success_directions': len(success_directions),
            'total_directions': len(all_directions)
        }
        
        logger.info(f"学习方向发现完成: {result}")
        return result
    
    def _get_recent_knowledge(self, limit: int = 100) -> List[Dict]:
        """获取最近的知识"""
        conn = sqlite3.connect('ai_brain.db')
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT title, content, type, tags, confidence
            FROM ai_brain_knowledge 
            WHERE is_active = 1 
            ORDER BY created_at DESC 
            LIMIT ?
        ''', (limit,))
        
        recent_knowledge = []
        for row in cursor.fetchall():
            recent_knowledge.append({
                'title': row[0],
                'content': row[1],
                'type': row[2],
                'tags': json.loads(row[3]) if row[3] else [],
                'confidence': row[4]
            })
        
        conn.close()
        return recent_knowledge
    
    def get_current_directions(self) -> List[Dict]:
        """获取当前学习方向"""
        gap_directions = self.gap_analyzer.analyze_knowledge_gaps()
        recent_knowledge = self._get_recent_knowledge()
        trend_directions = self.trend_analyzer.analyze_trends(recent_knowledge)
        problem_directions = self.problem_discoverer.discover_problem_driven_directions()
        success_directions = self.success_extractor.extract_success_patterns()
        
        all_directions = gap_directions + trend_directions + problem_directions + success_directions
        all_directions.sort(key=lambda x: x['priority'])
        
        return all_directions[:20]
    
    def get_learning_priorities(self) -> List[Dict]:
        """获取学习优先级"""
        return self.rules.get('learning_policy', {}).get('learning_priorities', [])


if __name__ == "__main__":
    discoverer = AILearningDirectionDiscoverer()
    discoverer.start()
    
    try:
        logger.info("执行学习方向发现...")
        result = discoverer.discover_learning_directions()
        
        logger.info("获取当前学习方向...")
        directions = discoverer.get_current_directions()
        for direction in directions[:5]:
            logger.info(f"学习方向: {direction.get('category', direction.get('trend', '未知'))} (优先级: {direction['priority']})")
        
        logger.info("获取学习优先级...")
        priorities = discoverer.get_learning_priorities()
        for priority in priorities[:5]:
            logger.info(f"优先级 {priority['priority']}: {priority['category']}")
        
        time.sleep(30)
    except KeyboardInterrupt:
        discoverer.stop()
        logger.info("AI学习方向自动发现系统已停止")