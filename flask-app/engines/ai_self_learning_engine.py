#!/usr/bin/env python3
"""
AI自我学习引擎 - 编排层
整合网络知识采集、自我觉醒分析、学习规则生成与执行、脑库投喂的完整闭环

核心功能：
1. 网络知识自动采集 - AI从网络中自我学习知识
2. 自我觉醒分析 - 从实际升级维护中发现学习重点
3. 学习规则自动生成 - 将发现的知识点和方向写入系统规则
4. 学习政策严格执行 - 确保学习规则被有效执行
5. 脑库壮大功能 - 持续向脑库投喂知识
"""

import os
import sys
import json
import sqlite3
import logging
import threading
import time
import random
import uuid
import hashlib
from datetime import datetime, timedelta

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), 'app'))

DATABASE_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'app.db')

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    handlers=[
        logging.FileHandler(
            os.path.join(os.path.dirname(os.path.abspath(__file__)), 'ai_self_learning.log'),
            encoding='utf-8'
        ),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger('AISelfLearning')


class SelfAwarenessAnalyzer:
    """自我觉醒分析器 - 从系统运行中发现学习重点"""

    def __init__(self, db_path=DATABASE_PATH, retention_days=90):
        self.db_path = db_path
        self.discovered_insights = []
        self.learning_priorities = {}
        self.retention_days = retention_days

    def _get_connection(self):
        return sqlite3.connect(self.db_path)

    def cleanup_stale_test_data(self):
        """清理陈旧数据（使用保留期而非分析窗口），防止历史数据无限增长"""
        try:
            conn = self._get_connection()
            cursor = conn.cursor()

            cutoff = (datetime.now() - timedelta(days=self.retention_days)).isoformat()

            cursor.execute('DELETE FROM error_logs WHERE created_at < ?', (cutoff,))
            deleted_errors = cursor.execute('SELECT changes()').fetchone()[0]

            cursor.execute('DELETE FROM brain_learning_records WHERE created_at < ?', (cutoff,))
            deleted_learning = cursor.execute('SELECT changes()').fetchone()[0]

            cursor.execute('DELETE FROM ai_upgrade_records WHERE created_at < ?', (cutoff,))
            deleted_upgrades = cursor.execute('SELECT changes()').fetchone()[0]

            cursor.execute('DELETE FROM system_maintenance_logs WHERE created_at < ?', (cutoff,))
            deleted_maintenance = cursor.execute('SELECT changes()').fetchone()[0]

            cursor.execute('DELETE FROM network_learning_records WHERE collected_at < ?', (cutoff,))
            deleted_network = cursor.execute('SELECT changes()').fetchone()[0]

            cursor.execute('DELETE FROM learning_policy_executions WHERE executed_at < ?', (cutoff,))
            deleted_policy = cursor.execute('SELECT changes()').fetchone()[0]

            conn.commit()
            conn.close()

            total_deleted = deleted_errors + deleted_learning + deleted_upgrades + deleted_maintenance + deleted_network + deleted_policy
            if total_deleted > 0:
                logger.info(f"[数据清理] 清理了 {deleted_errors} 条错误日志, {deleted_learning} 条学习记录, "
                           f"{deleted_upgrades} 条升级记录, {deleted_maintenance} 条维护日志, "
                           f"{deleted_network} 条网络学习记录, {deleted_policy} 条政策执行记录")

        except Exception as e:
            logger.error(f"[数据清理] 清理失败: {e}")

    def analyze_upgrade_history(self):
        """分析升级历史，发现需要加强的学习方向"""
        insights = []
        try:
            conn = self._get_connection()
            cursor = conn.cursor()

            cursor.execute('''
                SELECT upgrade_type, upgrade_category, COUNT(*) as count,
                       AVG(upgrade_score) as avg_score
                FROM ai_upgrade_records
                WHERE created_at > ? AND status = 'completed'
                GROUP BY upgrade_type, upgrade_category
                ORDER BY count DESC
                LIMIT 20
            ''', ((datetime.now() - timedelta(days=30)).isoformat(),))

            rows = cursor.fetchall()
            conn.close()

            for row in rows:
                upgrade_type, category, count, avg_score = row
                if avg_score and avg_score < 0.7:
                    insights.append({
                        'type': 'upgrade_gap',
                        'domain': upgrade_type,
                        'topic': category,
                        'insight': f'{upgrade_type}类型升级成功率低(得分:{avg_score:.2f})，需加强相关知识学习',
                        'priority': 'high',
                        'confidence': min(1.0, count * 0.15),
                        'source': 'ai_upgrade_records'
                    })

                if count >= 10:
                    insights.append({
                        'type': 'upgrade_pattern',
                        'domain': upgrade_type,
                        'topic': category,
                        'insight': f'{upgrade_type}-{category}升级频繁，是系统进化重点方向',
                        'priority': 'medium',
                        'confidence': min(1.0, count * 0.1),
                        'source': 'ai_upgrade_records'
                    })

        except Exception as e:
            logger.error(f"分析升级历史失败: {e}")

        return insights

    def analyze_error_patterns(self):
        """分析错误模式，发现知识缺口"""
        insights = []
        try:
            conn = self._get_connection()
            cursor = conn.cursor()

            cursor.execute('''
                SELECT error_type, error_message, COUNT(*) as count
                FROM error_logs
                WHERE created_at > ? AND status = 'open'
                GROUP BY error_type, SUBSTR(error_message, 1, 100)
                ORDER BY count DESC
                LIMIT 15
            ''', ((datetime.now() - timedelta(days=7)).isoformat(),))

            rows = cursor.fetchall()
            conn.close()

            for row in rows:
                error_type, message, count = row
                if count >= 3:
                    insights.append({
                        'type': 'error_focus',
                        'domain': 'error_handling',
                        'topic': error_type,
                        'insight': f'{error_type}错误频繁发生({count}次)，需加强错误处理知识',
                        'priority': 'high',
                        'confidence': min(1.0, count * 0.2),
                        'source': 'error_logs'
                    })

        except Exception as e:
            logger.error(f"分析错误模式失败: {e}")

        return insights

    def analyze_maintenance_effectiveness(self):
        """分析维护效果，发现优化方向"""
        insights = []
        try:
            conn = self._get_connection()
            cursor = conn.cursor()

            cursor.execute('''
                SELECT operation_type, target, COUNT(*) as count,
                       SUM(CASE WHEN result = 'success' THEN 1 ELSE 0 END) as success_count
                FROM system_maintenance_logs
                WHERE created_at > ?
                GROUP BY operation_type, target
                ORDER BY count DESC
                LIMIT 15
            ''', ((datetime.now() - timedelta(days=7)).isoformat(),))

            rows = cursor.fetchall()
            conn.close()

            for row in rows:
                op_type, target, count, success_count = row
                success_rate = success_count / count if count > 0 else 0

                if success_rate < 0.7:
                    insights.append({
                        'type': 'maintenance_improvement',
                        'domain': 'maintenance',
                        'topic': op_type,
                        'insight': f'{op_type}维护成功率低({success_rate:.0%})，需学习更好的维护策略',
                        'priority': 'high',
                        'confidence': min(1.0, (1 - success_rate) * count * 0.1),
                        'source': 'system_maintenance_logs'
                    })

                if count >= 20:
                    insights.append({
                        'type': 'maintenance_focus',
                        'domain': 'maintenance',
                        'topic': op_type,
                        'insight': f'{op_type}是高频维护操作，需建立标准化流程',
                        'priority': 'medium',
                        'confidence': min(1.0, count * 0.05),
                        'source': 'system_maintenance_logs'
                    })

        except Exception as e:
            logger.error(f"分析维护效果失败: {e}")

        return insights

    def analyze_learning_gaps(self):
        """分析学习记录，发现知识缺口"""
        insights = []
        try:
            conn = self._get_connection()
            cursor = conn.cursor()

            cursor.execute('''
                SELECT domain, topic, COUNT(*) as learning_count,
                       AVG(proficiency_gain) as avg_gain,
                       AVG(proficiency_after) as avg_prof
                FROM brain_learning_records
                WHERE created_at > ?
                GROUP BY domain, topic
                ORDER BY avg_gain ASC
                LIMIT 15
            ''', ((datetime.now() - timedelta(days=14)).isoformat(),))

            rows = cursor.fetchall()
            conn.close()

            for row in rows:
                domain, topic, learning_count, avg_gain, avg_prof = row
                if avg_gain and avg_gain < 0.05:
                    insights.append({
                        'type': 'knowledge_gap',
                        'domain': domain,
                        'topic': topic,
                        'insight': f'{domain}-{topic}学习效果差(熟练度提升:{avg_gain:.4f})，存在知识缺口',
                        'priority': 'high',
                        'confidence': min(1.0, learning_count * 0.15),
                        'source': 'brain_learning_records'
                    })

                if avg_prof and avg_prof < 0.3:
                    insights.append({
                        'type': 'low_proficiency',
                        'domain': domain,
                        'topic': topic,
                        'insight': f'{domain}-{topic}整体熟练度低({avg_prof:.2f})，需加强基础学习',
                        'priority': 'medium',
                        'confidence': min(1.0, (1 - avg_prof) * 0.8),
                        'source': 'brain_learning_records'
                    })

        except Exception as e:
            logger.error(f"分析学习缺口失败: {e}")

        return insights

    def analyze_network_learning_quality(self):
        """分析网络学习质量，优化采集策略"""
        insights = []
        try:
            conn = self._get_connection()
            cursor = conn.cursor()

            cursor.execute('''
                SELECT domain, source_name, COUNT(*) as count,
                       AVG(confidence) as avg_confidence,
                       SUM(fed_to_brain) as fed_count
                FROM network_learning_records
                WHERE collected_at > ?
                GROUP BY domain, source_name
                ORDER BY avg_confidence DESC
                LIMIT 15
            ''', ((datetime.now() - timedelta(days=7)).isoformat(),))

            rows = cursor.fetchall()
            conn.close()

            for row in rows:
                domain, source_name, count, avg_confidence, fed_count = row
                feed_rate = fed_count / count if count > 0 else 0

                if avg_confidence > 0.8 and feed_rate < 0.5:
                    insights.append({
                        'type': 'high_quality_source',
                        'domain': domain,
                        'topic': source_name,
                        'insight': f'{source_name}知识质量高(置信度:{avg_confidence:.2f})，但投喂率低，需增加采集频率',
                        'priority': 'medium',
                        'confidence': min(1.0, avg_confidence),
                        'source': 'network_learning_records'
                    })

                if avg_confidence < 0.4:
                    insights.append({
                        'type': 'low_quality_source',
                        'domain': domain,
                        'topic': source_name,
                        'insight': f'{source_name}知识质量低(置信度:{avg_confidence:.2f})，考虑调整采集策略',
                        'priority': 'low',
                        'confidence': min(1.0, (1 - avg_confidence) * 0.6),
                        'source': 'network_learning_records'
                    })

        except Exception as e:
            logger.error(f"分析网络学习质量失败: {e}")

        return insights

    def analyze_cluster_coordination(self):
        """分析集群协调效果，发现优化方向"""
        insights = []
        try:
            conn = self._get_connection()
            cursor = conn.cursor()

            cursor.execute('''
                SELECT coordination_type, AVG(efficiency_score) as avg_eff,
                       COUNT(*) as count
                FROM cluster_coordination_records
                WHERE created_at > ?
                GROUP BY coordination_type
                ORDER BY avg_eff ASC
                LIMIT 10
            ''', ((datetime.now() - timedelta(days=7)).isoformat(),))

            rows = cursor.fetchall()
            conn.close()

            for row in rows:
                coord_type, avg_eff, count = row
                if avg_eff and avg_eff < 0.7:
                    insights.append({
                        'type': 'coordination_improvement',
                        'domain': 'cluster',
                        'topic': coord_type,
                        'insight': f'{coord_type}协调效率低({avg_eff:.2f})，需优化集群协作策略',
                        'priority': 'medium',
                        'confidence': min(1.0, (1 - avg_eff) * count * 0.1),
                        'source': 'cluster_coordination_records'
                    })

        except Exception as e:
            logger.error(f"分析集群协调失败: {e}")

        return insights

    def analyze_knowledge_growth(self):
        """分析脑库知识增长趋势，发现知识扩展方向"""
        insights = []
        try:
            conn = self._get_connection()
            cursor = conn.cursor()

            cursor.execute('''
                SELECT knowledge_type, COUNT(*) as count
                FROM ai_brain_knowledge
                WHERE created_at > ?
                GROUP BY knowledge_type
                ORDER BY count DESC
                LIMIT 10
            ''', ((datetime.now() - timedelta(days=7)).isoformat(),))

            rows = cursor.fetchall()

            cursor.execute('''
                SELECT COUNT(*) FROM ai_brain_knowledge WHERE created_at > ?
            ''', ((datetime.now() - timedelta(days=1)).isoformat(),))
            recent_count = cursor.fetchone()[0]

            conn.close()

            for row in rows:
                knowledge_type, count = row
                if count < 10:
                    insights.append({
                        'type': 'knowledge_growth',
                        'domain': 'brain',
                        'topic': knowledge_type,
                        'insight': f'{knowledge_type}类型知识增长缓慢(仅{count}条)，需增加相关知识采集',
                        'priority': 'medium',
                        'confidence': min(1.0, (1 - count / 50) * 0.8),
                        'source': 'ai_brain_knowledge'
                    })

            if recent_count < 5:
                insights.append({
                    'type': 'knowledge_growth',
                    'domain': 'brain',
                    'topic': 'knowledge_acceleration',
                    'insight': f'最近24小时脑库知识增长缓慢(仅{recent_count}条)，需加速知识采集',
                    'priority': 'high',
                    'confidence': 0.7,
                    'source': 'ai_brain_knowledge'
                })

        except Exception as e:
            logger.error(f"分析知识增长失败: {e}")

        return insights

    def _discover_dynamic_topics_from_network(self):
        """从网络学习记录中动态发现新的技术趋势话题"""
        dynamic_topics = []
        try:
            conn = self._get_connection()
            cursor = conn.cursor()

            cursor.execute('''
                SELECT domain, category, AVG(confidence) as avg_confidence, COUNT(*) as count
                FROM network_learning_records
                WHERE collected_at > ? AND confidence > 0.6 AND category IS NOT NULL
                GROUP BY domain, category
                ORDER BY avg_confidence DESC, count DESC
                LIMIT 10
            ''', ((datetime.now() - timedelta(days=3)).isoformat(),))

            rows = cursor.fetchall()
            conn.close()

            for row in rows:
                domain, topic, avg_confidence, count = row
                if topic and topic not in [t[2] for t in dynamic_topics]:
                    dynamic_topics.append((
                        domain,
                        topic,
                        topic,
                        f'{topic}知识质量高(置信度:{avg_confidence:.2f})，是当前热门学习方向，需深入学习'
                    ))

            if dynamic_topics:
                logger.info(f"[自我觉醒] 从网络学习中发现 {len(dynamic_topics)} 个新话题")

        except Exception as e:
            logger.error(f"[自我觉醒] 动态发现话题失败: {e}")

        return dynamic_topics

    def generate_exploration_insights(self):
        """生成随机探索洞察，促进系统进化"""
        insights = []

        exploration_topics = [
            ('AI', '大语言模型', 'LLM', '大语言模型技术发展迅速，需持续学习最新进展'),
            ('AI', '向量数据库', 'vector_database', '向量数据库是AI应用关键基础设施，需深入学习'),
            ('AI', 'RAG技术', 'RAG', '检索增强生成技术是当前AI应用热点，需掌握'),
            ('AI', '多模态AI', 'multimodal', '多模态AI是下一代AI技术核心，需关注进展'),
            ('AI', 'Agent技术', 'agent', 'AI Agent技术正在改变软件开发模式，需学习'),
            ('AI', '微调技术', 'fine_tuning', '模型微调是提升AI应用效果的关键技术，需掌握'),
            ('AI', '量化技术', 'quantization', '模型量化是部署AI应用的重要优化手段，需了解'),
            ('AI', '推理优化', 'inference', 'AI推理优化是提升应用性能的核心，需深入研究'),

            ('Security', '零信任架构', 'zero_trust', '零信任安全架构是现代安全体系核心，需学习'),
            ('Security', 'AI安全', 'AI_security', 'AI安全和对抗攻击是新兴安全领域，需关注'),
            ('Security', '应用安全', 'app_security', 'Web应用安全是攻防核心，需持续学习'),
            ('Security', '数据隐私', 'data_privacy', '数据隐私保护是合规要求，需掌握'),
            ('Security', '加密技术', 'encryption', '现代加密技术是安全基础，需深入理解'),

            ('Architecture', '微服务架构', 'microservices', '微服务架构是现代应用主流模式，需深化理解'),
            ('Architecture', '云原生', 'cloud_native', '云原生技术是系统现代化关键，需持续学习'),
            ('Architecture', '服务网格', 'service_mesh', '服务网格是微服务治理的重要工具，需学习'),
            ('Architecture', '无服务器', 'serverless', '无服务器架构是未来发展方向，需了解'),
            ('Architecture', '事件驱动', 'event_driven', '事件驱动架构是高并发系统的核心，需掌握'),

            ('Performance', '边缘计算', 'edge_computing', '边缘计算能提升响应速度，需了解应用场景'),
            ('Performance', '缓存策略', 'caching', '高效缓存策略是性能优化核心，需学习最佳实践'),
            ('Performance', '负载均衡', 'load_balancing', '负载均衡是高可用系统的关键，需深入研究'),
            ('Performance', '分布式系统', 'distributed', '分布式系统是大规模应用的基础，需掌握'),

            ('Database', '时序数据库', 'timeseries_db', '时序数据库适用于监控数据，需掌握'),
            ('Database', '图数据库', 'graph_db', '图数据库在关系分析场景有独特优势，需学习'),
            ('Database', '分布式存储', 'distributed_storage', '分布式存储是大规模数据的基础，需了解'),
            ('Database', '数据湖', 'data_lake', '数据湖架构是现代数据处理的主流，需掌握'),

            ('DevOps', 'CI/CD', 'cicd', 'CI/CD是持续交付的核心，需学习最佳实践'),
            ('DevOps', '容器化', 'containerization', '容器化是现代化部署的基础，需掌握'),
            ('DevOps', '自动化运维', 'auto_ops', '自动化运维是提升效率的关键，需深入研究'),
            ('DevOps', '可观测性', 'observability', '可观测性是复杂系统的必备能力，需学习'),
        ]

        dynamic_topics = self._discover_dynamic_topics_from_network()
        exploration_topics.extend(dynamic_topics)

        selected = random.sample(exploration_topics, min(5, len(exploration_topics)))

        for domain, topic, topic_key, insight_text in selected:
            insight = {
                'type': 'exploration',
                'domain': domain,
                'topic': topic_key,
                'insight': insight_text,
                'priority': 'medium',
                'confidence': 0.5 + random.random() * 0.3,
                'source': 'self_exploration'
            }

            if not self._insight_exists(insight):
                insights.append(insight)

        logger.info(f"[自我觉醒] 生成 {len(insights)} 条探索性洞察")

        return insights

    def discover_learning_insights(self):
        """综合发现所有学习洞察"""
        logger.info("[自我觉醒] 开始分析系统运行数据，发现学习重点...")

        self.cleanup_stale_test_data()

        insights = []
        insights.extend(self.analyze_upgrade_history())
        insights.extend(self.analyze_error_patterns())
        insights.extend(self.analyze_maintenance_effectiveness())
        insights.extend(self.analyze_learning_gaps())
        insights.extend(self.analyze_network_learning_quality())
        insights.extend(self.analyze_cluster_coordination())
        insights.extend(self.analyze_knowledge_growth())
        insights.extend(self.generate_exploration_insights())

        insights = self._prioritize_insights(insights)

        new_insights = []
        for insight in insights:
            if not self._insight_exists(insight):
                new_insights.append(insight)

        self.discovered_insights = new_insights

        self._save_insights_to_db(new_insights)

        logger.info(f"[自我觉醒] 发现 {len(new_insights)} 条新学习洞察（共分析 {len(insights)} 条）")
        for insight in new_insights[:10]:
            logger.info(f"  - [{insight['priority']}] {insight['domain']}: {insight['insight'][:50]}...")

        return new_insights

    def _generate_insight_hash(self, insight):
        """生成洞察内容的哈希值用于去重"""
        content = f"{insight.get('type', '')}_{insight.get('domain', '')}_{insight.get('topic', '')}_{insight.get('insight', '')[:100]}"
        return hashlib.sha256(content.encode('utf-8')).hexdigest()

    def _insight_exists(self, insight):
        """检查相似洞察是否已存在（放宽去重条件，允许同一方向多次学习）"""
        try:
            conn = self._get_connection()
            cursor = conn.cursor()

            cursor.execute('''
                SELECT COUNT(*) FROM self_learning_insights
                WHERE insight_type = ? AND domain = ? AND topic = ?
                AND created_at > ?
            ''', (
                insight.get('type', ''),
                insight.get('domain', ''),
                insight.get('topic', ''),
                (datetime.now() - timedelta(hours=6)).isoformat()
            ))

            count = cursor.fetchone()[0]
            conn.close()
            return count > 2
        except Exception:
            return False

    def _save_insights_to_db(self, insights):
        """保存洞察到数据库（去重）"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            saved_count = 0
            for insight in insights:
                if self._insight_exists(insight):
                    logger.debug(f"[自我觉醒] 洞察已存在，跳过: {insight.get('topic', '')}")
                    continue

                cursor.execute('''
                    INSERT INTO self_learning_insights
                    (insight_type, domain, topic, insight, priority, confidence, score, source)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    insight.get('type', ''),
                    insight.get('domain', ''),
                    insight.get('topic', ''),
                    insight.get('insight', ''),
                    insight.get('priority', 'low'),
                    insight.get('confidence', 0.0),
                    insight.get('score', 0.0),
                    insight.get('source', '')
                ))
                saved_count += 1

            conn.commit()
            conn.close()
            logger.info(f"[自我觉醒] 已保存 {saved_count} 条新洞察到数据库（共发现 {len(insights)} 条）")
        except Exception as e:
            logger.error(f"[自我觉醒] 保存洞察失败: {e}")

    def get_saved_insights(self):
        """从数据库获取已保存的洞察"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            cursor.execute('''
                SELECT * FROM self_learning_insights
                ORDER BY created_at DESC LIMIT 20
            ''')

            rows = cursor.fetchall()
            columns = [desc[0] for desc in cursor.description]
            conn.close()

            insights = []
            for row in rows:
                insight = dict(zip(columns, row))
                insights.append(insight)

            return insights
        except Exception as e:
            logger.error(f"[自我觉醒] 获取洞察失败: {e}")
            return []

    def _prioritize_insights(self, insights):
        """优先级排序"""
        priority_weights = {'high': 3, 'medium': 2, 'low': 1}

        for insight in insights:
            weight = priority_weights.get(insight.get('priority', 'low'), 1)
            insight['score'] = insight.get('confidence', 0) * weight

        insights.sort(key=lambda x: x.get('score', 0), reverse=True)
        return insights[:50]

    def generate_learning_rules(self):
        """将洞察转换为学习规则"""
        rules = []
        for insight in self.discovered_insights:
            if insight.get('confidence', 0) >= 0.3:
                rule = {
                    'rule_code': f"SELF_LEARNING_{insight['type'].upper()}_{insight['domain'].upper()}_{insight['topic'].upper()[:15]}",
                    'rule_name': f"自我学习-{insight['domain']}-{insight['topic']}",
                    'rule_value': '1',
                    'rule_type': 'learning',
                    'learning_domain': insight['domain'],
                    'learning_priority': insight.get('priority', 'medium'),
                    'discovery_source': insight.get('source', 'self_awareness'),
                    'confidence': insight.get('confidence', 0),
                    'description': insight.get('insight', '')
                }
                rules.append(rule)

        return rules


class AISelfLearningEngine:
    """AI自我学习引擎 - 编排层"""

    def __init__(self):
        self.db_path = DATABASE_PATH
        self.is_running = False
        self.learning_thread = None
        self.self_awareness_analyzer = SelfAwarenessAnalyzer()
        self.network_collector = None
        self.learning_rule_engine = None
        self._init_components()

    def _init_components(self):
        """初始化各组件"""
        try:
            from app.ai.ai_network_learner import NetworkKnowledgeCollector
            from app.ai.ai_learning_rule_engine import LearningRuleEngine

            self.network_collector = NetworkKnowledgeCollector()
            self.learning_rule_engine = LearningRuleEngine()
            self.learning_rule_engine.set_network_collector(self.network_collector)
            logger.info("[初始化] 网络知识采集器和学习规则引擎加载完成")
        except Exception as e:
            logger.warning(f"[初始化] 加载组件失败(部分功能受限): {e}")

    def _get_connection(self):
        return sqlite3.connect(self.db_path)

    def _get_rule_bool(self, rule_code, default=True):
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            cursor.execute('SELECT rule_value FROM system_rules WHERE rule_code = ? AND is_active = 1', (rule_code,))
            result = cursor.fetchone()
            conn.close()
            if result:
                return result[0] in ('1', 'true', 'True', 'yes', 'Yes')
            return default
        except Exception:
            return default

    def _save_learning_rule_to_db(self, rule):
        """保存学习规则到数据库和《规则》文档"""
        try:
            conn = self._get_connection()
            cursor = conn.cursor()

            cursor.execute('''
                INSERT OR REPLACE INTO system_rules
                (rule_code, rule_name, rule_value, rule_type, description, is_active, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (
                rule['rule_code'],
                rule['rule_name'],
                rule['rule_value'],
                rule['rule_type'],
                rule.get('description', ''),
                1,
                datetime.now().isoformat()
            ))

            cursor.execute('''
                INSERT OR REPLACE INTO learning_rules
                (rule_code, rule_name, rule_value, rule_type, learning_domain, learning_priority,
                 discovery_source, confidence, is_active, updated_at, description)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                rule['rule_code'],
                rule['rule_name'],
                rule['rule_value'],
                rule['rule_type'],
                rule.get('learning_domain', ''),
                rule.get('learning_priority', 'normal'),
                rule.get('discovery_source', 'self_learning_engine'),
                rule.get('confidence', 0),
                1,
                datetime.now().isoformat(),
                rule.get('description', '')
            ))

            conn.commit()
            conn.close()
            logger.info(f"[规则写入] 成功写入学习规则: {rule['rule_code']}")

            self._write_rule_to_rules_document(rule)

        except Exception as e:
            logger.error(f"[规则写入] 保存学习规则失败: {e}")

    def _write_rule_to_rules_document(self, rule):
        """将学习规则写入《规则》文档（去重）"""
        rules_doc_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'RULES.md')

        rule_entry = f"""
## {rule['rule_code']}

**规则名称**: {rule['rule_name']}
**规则值**: {rule['rule_value']}
**规则类型**: {rule['rule_type']}
**学习领域**: {rule.get('learning_domain', '未分类')}
**优先级**: {rule.get('learning_priority', 'normal')}
**发现来源**: {rule.get('discovery_source', 'self_learning')}
**置信度**: {rule.get('confidence', 0):.2f}
**描述**: {rule.get('description', '')}
**创建时间**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

---
"""

        try:
            if os.path.exists(rules_doc_path):
                with open(rules_doc_path, 'r', encoding='utf-8') as f:
                    content = f.read()

                if f"## {rule['rule_code']}" in content:
                    logger.info(f"[规则文档] 规则 {rule['rule_code']} 已存在，跳过写入")
                    return

                with open(rules_doc_path, 'a', encoding='utf-8') as f:
                    f.write(rule_entry)

                self._update_rules_count(rules_doc_path)
            else:
                header = f"""# AI自我学习规则文档

> 自动生成的AI自我学习规则，由AI自我学习引擎发现并写入

**生成时间**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
**规则总数**: 1

---

{rule_entry}"""
                with open(rules_doc_path, 'w', encoding='utf-8') as f:
                    f.write(header)

            logger.info(f"[规则文档] 规则 {rule['rule_code']} 已写入 RULES.md")
        except Exception as e:
            logger.error(f"[规则文档] 写入规则文档失败: {e}")

    def _update_rules_count(self, rules_doc_path):
        """更新规则文档中的规则总数"""
        try:
            with open(rules_doc_path, 'r', encoding='utf-8') as f:
                content = f.read()

            import re
            count = len(re.findall(r'^## ', content, re.MULTILINE))

            content = re.sub(
                r'\*\*规则总数\*\*: \d+',
                f'**规则总数**: {count}',
                content
            )

            with open(rules_doc_path, 'w', encoding='utf-8') as f:
                f.write(content)
        except Exception as e:
            logger.error(f"[规则文档] 更新规则总数失败: {e}")

    def _feed_knowledge_to_brain(self, knowledge_list):
        """将知识投喂到脑库"""
        try:
            conn = self._get_connection()
            cursor = conn.cursor()

            fed_count = 0
            for knowledge in knowledge_list:
                knowledge_id = f"K-SL-{uuid.uuid4().hex[:8]}"

                cursor.execute('''
                    INSERT OR IGNORE INTO ai_brain_knowledge
                    (knowledge_id, title, content, knowledge_type, source, tags, priority, status, created_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    knowledge_id,
                    knowledge.get('title', 'Untitled'),
                    knowledge.get('content', ''),
                    knowledge.get('knowledge_type', 'self_learning'),
                    'self_learning_engine',
                    f"{knowledge.get('domain', '')},{knowledge.get('topic', '')}",
                    knowledge.get('priority', 5),
                    'active',
                    datetime.now().isoformat()
                ))

                cursor.execute('''
                    INSERT OR IGNORE INTO brain_feeding_queue
                    (feed_id, feed_type, feed_source, feed_data, knowledge_type, priority,
                     status, scheduled_at, data_size, tags, description, created_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    f"FED-SL-{uuid.uuid4().hex[:12]}",
                    'knowledge',
                    'self_learning_engine',
                    json.dumps(knowledge, ensure_ascii=False),
                    knowledge.get('knowledge_type', 'self_learning'),
                    knowledge.get('priority', 5),
                    'completed',
                    datetime.now().isoformat(),
                    len(knowledge.get('content', '').encode('utf-8')),
                    knowledge.get('domain', ''),
                    f"自我学习知识: {knowledge.get('title', 'Untitled')}",
                    datetime.now().isoformat()
                ))

                cursor.execute('''
                    INSERT INTO ai_brain_activity
                    (knowledge_id, activity_type, details, timestamp)
                    VALUES (?, ?, ?, ?)
                ''', (
                    knowledge_id, 'self_learned',
                    f"自我学习发现并投喂: {knowledge.get('title', 'unknown')}",
                    datetime.now().isoformat()
                ))

                fed_count += 1

            conn.commit()
            conn.close()
            logger.info(f"[脑库投喂] 成功投喂 {fed_count} 条知识到脑库")
            return fed_count
        except Exception as e:
            logger.error(f"[脑库投喂] 投喂失败: {e}")
            return 0

    def run_self_learning_cycle(self):
        """执行完整的自我学习周期"""
        logger.info("=" * 60)
        logger.info("  AI自我学习引擎 - 执行学习周期")
        logger.info("=" * 60)

        stats = {
            'network_knowledge': 0,
            'discovered_insights': 0,
            'generated_rules': 0,
            'executed_rules': 0,
            'fed_to_brain': 0
        }

        stats['discovered_insights'] = self._execute_self_awareness()

        if stats['discovered_insights'] > 0:
            stats['generated_rules'] = self._execute_rule_generation()

        if self._get_rule_bool('SELF_LEARNING_NETWORK_ENABLED', True):
            stats['network_knowledge'] = self._execute_network_learning()

        if stats['generated_rules'] > 0:
            stats['executed_rules'] = self._execute_learning_policy()

        stats['fed_to_brain'] = self._execute_brain_feeding()

        logger.info("=" * 60)
        logger.info(f"  洞察发现: {stats['discovered_insights']} | 规则生成: {stats['generated_rules']}")
        logger.info(f"  网络知识: {stats['network_knowledge']} | 规则执行: {stats['executed_rules']}")
        logger.info(f"  脑库投喂: {stats['fed_to_brain']}")
        logger.info("=" * 60)

        return stats

    def _execute_network_learning(self):
        """执行网络知识采集（包含基于自我觉醒的动态搜索）"""
        logger.info("[网络学习] 开始从网络采集知识...")
        if not self.network_collector:
            logger.warning("[网络学习] 采集器未初始化，跳过")
            return 0

        try:
            dynamic_keywords = self._extract_dynamic_keywords_from_insights()
            if dynamic_keywords:
                self.network_collector.set_dynamic_keywords(dynamic_keywords)

            collected_points = self.network_collector.run_collection()
            logger.info(f"[网络学习] 采集完成，获取 {len(collected_points)} 个知识点")

            self._feed_knowledge_to_brain(collected_points)

            self.network_collector.feed_to_brain()

            return len(collected_points)
        except Exception as e:
            logger.error(f"[网络学习] 采集失败: {e}")
            return 0

    def _extract_dynamic_keywords_from_insights(self):
        """从自我觉醒洞察中提取动态搜索关键词"""
        keywords = []

        if self.self_awareness_analyzer:
            for insight in self.self_awareness_analyzer.discovered_insights:
                topic = insight.get('topic', '')
                domain = insight.get('domain', '')

                if topic:
                    keywords.append(topic)
                    if '_' in topic:
                        keywords.extend(topic.split('_'))
                if domain and domain != topic:
                    keywords.append(domain)
                    if '_' in domain:
                        keywords.extend(domain.split('_'))

                insight_text = insight.get('insight', '')
                if insight_text:
                    for kw in ['HTTP 500', '错误处理', '强化学习', '神经网络', 'AI', '安全', '性能', '优化', '架构',
                               '维护', '升级', '故障', '调试', '监控', '数据库', 'Flask', 'Python', '算法', '模型']:
                        if kw in insight_text:
                            keywords.append(kw)

                    import re
                    tech_terms = re.findall(r'(?:Python|Flask|SQLite|HTTP|API|JSON|机器学习|深度学习|人工智能|神经网络|强化学习|自然语言处理|计算机视觉|数据挖掘)', insight_text)
                    keywords.extend(tech_terms)

        keywords = [kw for kw in list(set(keywords)) if len(kw) >= 2]
        logger.info(f"[网络学习] 从自我觉醒中提取 {len(keywords)} 个动态搜索关键词: {keywords[:10]}")
        return keywords

    def _execute_self_awareness(self):
        """执行自我觉醒分析"""
        logger.info("[自我觉醒] 开始分析系统运行数据...")
        insights = self.self_awareness_analyzer.discover_learning_insights()

        for insight in insights[:5]:
            logger.info(f"  ✓ 发现: {insight['insight'][:60]}...")

        return len(insights)

    def _execute_rule_generation(self):
        """执行学习规则生成"""
        logger.info("[规则生成] 将洞察转换为学习规则...")
        rules = self.self_awareness_analyzer.generate_learning_rules()

        for rule in rules:
            self._save_learning_rule_to_db(rule)

        logger.info(f"[规则生成] 成功生成 {len(rules)} 条学习规则")
        return len(rules)

    def _execute_learning_policy(self):
        """执行学习政策"""
        logger.info("[政策执行] 开始执行学习政策...")
        if not self.learning_rule_engine:
            logger.warning("[政策执行] 规则引擎未初始化，跳过")
            return 0

        try:
            result = self.learning_rule_engine.execute_learning_policy()
            executed = result.get('executed', 0)
            logger.info(f"[政策执行] 执行完成，成功 {executed} 条")
            return executed
        except Exception as e:
            logger.error(f"[政策执行] 执行失败: {e}")
            return 0

    def _execute_brain_feeding(self):
        """执行脑库投喂"""
        logger.info("[脑库投喂] 补充内置知识库...")
        internal_knowledge = [
            {
                'title': '自我学习方法论',
                'content': 'AI自我学习应遵循: 观察→分析→洞察→规则→执行→反思的闭环流程',
                'knowledge_type': 'methodology',
                'domain': 'AI',
                'topic': 'self_learning',
                'priority': 8
            },
            {
                'title': '知识优先级评估',
                'content': '知识优先级根据: 使用频率、影响范围、紧急程度、演化潜力四个维度评估',
                'knowledge_type': 'methodology',
                'domain': 'AI',
                'topic': 'knowledge_management',
                'priority': 7
            },
            {
                'title': '学习效果评估',
                'content': '学习效果通过熟练度提升、错误减少、效率提高三个指标综合评估',
                'knowledge_type': 'methodology',
                'domain': 'AI',
                'topic': 'learning_evaluation',
                'priority': 6
            },
            {
                'title': '自适应学习策略',
                'content': '根据知识缺口动态调整学习重点，优先弥补短板领域',
                'knowledge_type': 'strategy',
                'domain': 'AI',
                'topic': 'adaptive_learning',
                'priority': 8
            },
            {
                'title': '知识融合机制',
                'content': '将不同来源的知识进行融合，形成系统性知识体系',
                'knowledge_type': 'architecture',
                'domain': 'AI',
                'topic': 'knowledge_fusion',
                'priority': 7
            }
        ]

        return self._feed_knowledge_to_brain(internal_knowledge)

    def start_auto_learning(self, interval=3600):
        """启动自动学习"""
        if self.is_running:
            return {'success': False, 'message': '自动学习已在运行'}

        self.is_running = True
        self.learning_thread = threading.Thread(
            target=self._learning_loop,
            args=(interval,),
            daemon=True
        )
        self.learning_thread.start()
        logger.info(f"[自动学习] 已启动，间隔 {interval} 秒")
        return {'success': True, 'message': f'自动学习已启动, 间隔 {interval} 秒'}

    def stop_auto_learning(self):
        """停止自动学习"""
        self.is_running = False
        if self.learning_thread:
            self.learning_thread.join(timeout=10)
        logger.info("[自动学习] 已停止")
        return {'success': True, 'message': '自动学习已停止'}

    def _learning_loop(self, interval):
        """学习循环"""
        while self.is_running:
            try:
                self.run_self_learning_cycle()
            except Exception as e:
                logger.error(f"[学习循环] 执行失败: {e}")

            for i in range(interval):
                if not self.is_running:
                    break
                time.sleep(1)

    def get_learning_status(self):
        """获取学习状态"""
        return {
            'is_running': self.is_running,
            'component_status': {
                'network_collector': 'ready' if self.network_collector else 'unavailable',
                'learning_rule_engine': 'ready' if self.learning_rule_engine else 'unavailable',
                'self_awareness_analyzer': 'ready'
            },
            'last_discovered_insights': len(self.self_awareness_analyzer.discovered_insights),
            'discovery_time': datetime.now().isoformat()
        }


def main():
    engine = AISelfLearningEngine()

    if len(sys.argv) > 1:
        if sys.argv[1] == '--once':
            engine.run_self_learning_cycle()
        elif sys.argv[1] == '--network':
            engine._execute_network_learning()
        elif sys.argv[1] == '--awareness':
            engine._execute_self_awareness()
        elif sys.argv[1] == '--rules':
            engine._execute_rule_generation()
        elif sys.argv[1] == '--feed':
            engine._execute_brain_feeding()
        elif sys.argv[1] == '--start':
            interval = int(sys.argv[2]) if len(sys.argv) > 2 else 3600
            engine.start_auto_learning(interval)
            print(f"自动学习已启动，间隔 {interval} 秒")
            while True:
                time.sleep(60)
        elif sys.argv[1] == '--status':
            status = engine.get_learning_status()
            print(json.dumps(status, ensure_ascii=False, indent=2))
        elif sys.argv[1] == '--stop':
            engine.stop_auto_learning()
        else:
            print("未知参数")
            print("可用参数: --once, --network, --awareness, --rules, --feed, --start [间隔], --status, --stop")
    else:
        engine.run_self_learning_cycle()


if __name__ == '__main__':
    main()
