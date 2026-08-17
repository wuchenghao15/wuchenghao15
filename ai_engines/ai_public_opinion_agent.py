#!/usr/bin/env python3
"""AI智能舆情分析Agent"""

import os
import re
import logging
import json
from datetime import datetime
from typing import Dict, List, Any
from ai_engines.ai_employee_system import AIEmployee

logger = logging.getLogger(__name__)

class AIPublicOpinionAgent(AIEmployee):
    """AI舆情分析Agent"""
    
    def __init__(self, employee_id: str, name: str = "AI舆情分析专家"):
        super().__init__(employee_id, name, 'public_opinion', 8)
        self.skills = [
            '舆情监测', '情感分析', '热点追踪',
            '风险预警', '舆情报告', '媒体分析',
            '话题分析', '传播路径', '危机处理'
        ]
        self.monitored_topics = {}
        self.analysis_history = []
        self.total_analyses = 0
    
    def add_monitored_topic(self, topic: str, keywords: List[str]) -> Dict[str, Any]:
        """添加监控话题"""
        topic_id = f"topic_{datetime.now().timestamp()}"
        
        self.monitored_topics[topic_id] = {
            'topic_id': topic_id,
            'topic': topic,
            'keywords': keywords,
            'status': 'active',
            'created_at': datetime.now().isoformat(),
            'mentions': []
        }
        
        return self.monitored_topics[topic_id]
    
    def analyze_sentiment(self, text: str) -> Dict[str, Any]:
        """分析情感"""
        positive_words = ['好', '棒', '优秀', '喜欢', '满意', '赞', '推荐', '完美', '出色', '精彩']
        negative_words = ['差', '烂', '糟糕', '失望', '不满', '投诉', '问题', '失败', '垃圾', '坑']
        
        positive_count = sum(1 for word in positive_words if word in text)
        negative_count = sum(1 for word in negative_words if word in text)
        
        total = positive_count + negative_count
        
        if total == 0:
            sentiment = 'neutral'
            score = 0
        elif positive_count > negative_count:
            sentiment = 'positive'
            score = positive_count / total
        else:
            sentiment = 'negative'
            score = -negative_count / total
        
        return {
            'text': text[:100],
            'sentiment': sentiment,
            'score': round(score, 2),
            'positive_count': positive_count,
            'negative_count': negative_count,
            'timestamp': datetime.now().isoformat()
        }
    
    def track_mention(self, topic_id: str, text: str, source: str = 'unknown') -> Dict[str, Any]:
        """追踪提及"""
        if topic_id not in self.monitored_topics:
            return {'error': '话题不存在'}
        
        topic = self.monitored_topics[topic_id]
        
        sentiment = self.analyze_sentiment(text)
        
        mention = {
            'id': f"mention_{datetime.now().timestamp()}",
            'text': text,
            'source': source,
            'sentiment': sentiment['sentiment'],
            'sentiment_score': sentiment['score'],
            'timestamp': datetime.now().isoformat()
        }
        
        topic['mentions'].append(mention)
        
        return mention
    
    def analyze_topic(self, topic_id: str) -> Dict[str, Any]:
        """分析话题"""
        if topic_id not in self.monitored_topics:
            return {'error': '话题不存在'}
        
        topic = self.monitored_topics[topic_id]
        mentions = topic.get('mentions', [])
        
        total_mentions = len(mentions)
        positive_count = sum(1 for m in mentions if m['sentiment'] == 'positive')
        negative_count = sum(1 for m in mentions if m['sentiment'] == 'negative')
        neutral_count = sum(1 for m in mentions if m['sentiment'] == 'neutral')
        
        if total_mentions > 0:
            positive_ratio = positive_count / total_mentions * 100
            negative_ratio = negative_count / total_mentions * 100
            neutral_ratio = neutral_count / total_mentions * 100
        else:
            positive_ratio = negative_ratio = neutral_ratio = 0
        
        risk_level = 'low'
        if negative_ratio > 30:
            risk_level = 'medium'
        if negative_ratio > 50:
            risk_level = 'high'
        
        self.total_analyses += 1
        
        result = {
            'topic_id': topic_id,
            'topic': topic['topic'],
            'total_mentions': total_mentions,
            'sentiment_distribution': {
                'positive': round(positive_ratio, 2),
                'negative': round(negative_ratio, 2),
                'neutral': round(neutral_ratio, 2)
            },
            'risk_level': risk_level,
            'recent_mentions': mentions[-10:],
            'timestamp': datetime.now().isoformat()
        }
        
        self.analysis_history.append(result)
        
        return result
    
    def generate_report(self, topic_id: str) -> str:
        """生成报告"""
        analysis = self.analyze_topic(topic_id)
        
        report_lines = []
        report_lines.append(f"# 舆情分析报告 - {analysis['topic']}")
        report_lines.append(f"生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        report_lines.append("")
        
        report_lines.append("## 基本信息")
        report_lines.append(f"- 话题ID: {analysis['topic_id']}")
        report_lines.append(f"- 提及总数: {analysis['total_mentions']}")
        report_lines.append(f"- 风险等级: {analysis['risk_level']}")
        report_lines.append("")
        
        report_lines.append("## 情感分布")
        dist = analysis['sentiment_distribution']
        report_lines.append(f"- 正面: {dist['positive']}%")
        report_lines.append(f"- 负面: {dist['negative']}%")
        report_lines.append(f"- 中性: {dist['neutral']}%")
        report_lines.append("")
        
        report_lines.append("## 风险提示")
        if analysis['risk_level'] == 'high':
            report_lines.append("- ⚠️ 高风险：负面提及超过50%，建议立即采取措施")
        elif analysis['risk_level'] == 'medium':
            report_lines.append("- ⚡ 中等风险：负面提及超过30%，建议持续关注")
        else:
            report_lines.append("- ✅ 低风险：舆情状况良好")
        
        return '\n'.join(report_lines)
    
    def get_stats(self) -> Dict:
        """获取统计"""
        return {
            'total_analyses': self.total_analyses,
            'monitored_topics': len(self.monitored_topics),
            'recent_analyses': self.analysis_history[-5:]
        }

public_opinion_agent = AIPublicOpinionAgent('ai_public_opinion_001')
