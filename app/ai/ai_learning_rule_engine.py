#!/usr/bin/env python3
""" AI学习规则引擎 实现自我发现学习方向，自动写入学习规则到系统规则表，并严格执行学习政策 """

import os
import re
import json
import time
import random
import sqlite3
import threading
from datetime import datetime, timedelta
from collections import defaultdict

DB_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), '..', 'app.db')

LEARNING_RULE_PREFIX = 'LEARNING_'
SELF_DISCOVERY_RULE_PREFIX = 'SELF_DISCOVERY_'

class LearningRuleEngine:
    """学习规则引擎"""
    
    def __init__(self):
        self.is_running = False
        self.rule_thread = None
        self.discovered_rules = []
        self.executed_policies = []
        self._lock = threading.Lock()
        self._init_database()
        self.network_collector = None
    
    def set_network_collector(self, collector):
        """设置网络知识采集器（用于执行学习政策时进行针对性学习）"""
        self.network_collector = collector
        logger.info("[LearningRuleEngine] 已设置网络知识采集器")
    
    def _init_database(self):
        try:
            conn = sqlite3.connect(DB_PATH)
            cursor = conn.cursor()
            cursor.execute(''' CREATE TABLE IF NOT EXISTS learning_rules ( id INTEGER PRIMARY KEY AUTOINCREMENT, rule_code TEXT UNIQUE NOT NULL, rule_name TEXT NOT NULL, rule_value TEXT, rule_type TEXT DEFAULT 'learning', learning_domain TEXT, learning_priority TEXT DEFAULT 'normal', discovery_source TEXT, confidence REAL DEFAULT 0.0, execution_count INTEGER DEFAULT 0, last_executed TEXT, is_active INTEGER DEFAULT 1, created_at TEXT DEFAULT CURRENT_TIMESTAMP, updated_at TEXT DEFAULT CURRENT_TIMESTAMP, description TEXT ) ''')
            cursor.execute(''' CREATE TABLE IF NOT EXISTS learning_policy_executions ( id INTEGER PRIMARY KEY AUTOINCREMENT, policy_id TEXT NOT NULL, policy_name TEXT NOT NULL, execution_type TEXT, target_domain TEXT, target_employees TEXT, execution_params TEXT, execution_result TEXT, success INTEGER DEFAULT 0, executed_at TEXT DEFAULT CURRENT_TIMESTAMP, notes TEXT ) ''')
            conn.commit()
            conn.close()
            logger.info("[LearningRuleEngine] 数据库表初始化完成")
        except Exception as e:
            logger.info(f"[LearningRuleEngine] 初始化数据库失败: {e}")
    
    def _get_connection(self):
        return sqlite3.connect(DB_PATH)
    
    def _get_rule_value(self, rule_code, default=None):
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            cursor.execute('SELECT rule_value FROM system_rules WHERE rule_code = ? AND is_active = 1', (rule_code,))
            result = cursor.fetchone()
            conn.close()
            return result[0] if result else default
        except Exception:
            return default
    
    def _get_rule_bool(self, rule_code, default=False):
        val = self._get_rule_value(rule_code)
        if val is not None:
            return val in ('1', 'true', 'True', 'yes', 'Yes')
        return default
    
    def discover_learning_directions(self):
        """自我发现学习方向"""
        logger.info("[LearningRuleEngine] 开始自我发现学习方向...")
        
        discovered = []
        
        discovered.extend(self._analyze_learning_history())
        discovered.extend(self._analyze_upgrade_records())
        discovered.extend(self._analyze_maintenance_logs())
        discovered.extend(self._analyze_error_patterns())
        discovered.extend(self._analyze_network_learning())
        
        discovered = self._prioritize_rules(discovered)
        
        for rule in discovered:
            self._write_rule_to_system_rules(rule)
            self._save_learning_rule(rule)
        
        logger.info(f"[LearningRuleEngine] 发现 {len(discovered)} 条学习规则")
        return discovered
    
    def _analyze_learning_history(self):
        """分析学习历史记录"""
        rules = []
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            
            cursor.execute(''' SELECT domain, topic, COUNT(*) as count, AVG(proficiency_gain) as avg_gain FROM brain_learning_records WHERE created_at > ? GROUP BY domain, topic ORDER BY count DESC, avg_gain DESC LIMIT 20 ''', ((datetime.now() - timedelta(days=30)).isoformat(),))
            
            rows = cursor.fetchall()
            conn.close()
            
            domain_stats = defaultdict(list)
            for row in rows:
                domain_stats[row[0]].append({
                    'topic': row[1],
                    'count': row[2],
                    'avg_gain': row[3]
                })
            
            for domain, topics in domain_stats.items():
                if len(topics) >= 3:
                    rule = {
                        'rule_code': f'{SELF_DISCOVERY_RULE_PREFIX}HIGH_FREQUENCY_DOMAIN_{domain.upper()}',
                        'rule_name': f'高频学习领域-{domain}',
                        'rule_value': '1',
                        'rule_type': 'learning',
                        'learning_domain': domain,
                        'learning_priority': 'high',
                        'discovery_source': 'brain_learning_records',
                        'confidence': min(1.0, len(topics) * 0.2),
                        'description': f'{domain}领域学习频率高，建议加强该领域学习资源采集'
                    }
                    rules.append(rule)
            
            for topic_info in rows[:10]:
                domain, topic, count, avg_gain = topic_info
                if avg_gain < 0.1:
                    rule = {
                        'rule_code': f'{SELF_DISCOVERY_RULE_PREFIX}KNOWLEDGE_GAP_{domain.upper()}_{topic.upper()[:20]}',
                        'rule_name': f'知识缺口-{domain}-{topic}',
                        'rule_value': '1',
                        'rule_type': 'learning',
                        'learning_domain': domain,
                        'learning_priority': 'high',
                        'discovery_source': 'brain_learning_records',
                        'confidence': min(1.0, count * 0.15),
                        'description': f'{topic}知识熟练度提升缓慢，存在知识缺口，需加强学习'
                    }
                    rules.append(rule)
            
        except Exception as e:
            logger.info(f"[LearningRuleEngine] 分析学习历史失败: {e}")
        
        return rules
    
    def _analyze_upgrade_records(self):
        """分析升级记录"""
        rules = []
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            
            cursor.execute(''' SELECT upgrade_type, upgrade_category, COUNT(*) as count FROM ai_upgrade_records WHERE created_at > ? AND status = 'completed' GROUP BY upgrade_type, upgrade_category ORDER BY count DESC LIMIT 15 ''', ((datetime.now() - timedelta(days=30)).isoformat(),))
            
            rows = cursor.fetchall()
            conn.close()
            
            for row in rows:
                upgrade_type, category, count = row
                if count >= 5:
                    rule = {
                        'rule_code': f'{SELF_DISCOVERY_RULE_PREFIX}UPGRADE_PATTERN_{upgrade_type.upper( )}_{category.upper()}',
                        'rule_name': f'升级模式-{upgrade_type}-{category}',
                        'rule_value': '1',
                        'rule_type': 'learning',
                        'learning_domain': 'upgrade',
                        'learning_priority': 'medium',
                        'discovery_source': 'ai_upgrade_records',
                        'confidence': min(1.0, count * 0.1),
                        'description': f'{upgrade_type}类型升级频繁，建议学习相关升级技术和最佳实践'
                    }
                    rules.append(rule)
            
        except Exception as e:
            logger.info(f"[LearningRuleEngine] 分析升级记录失败: {e}")
        
        return rules
    
    def _analyze_maintenance_logs(self):
        """分析维护日志"""
        rules = []
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            
            cursor.execute(''' SELECT operation_type, target, COUNT(*) as count FROM system_maintenance_logs WHERE created_at > ? AND result = 'success' GROUP BY operation_type, target ORDER BY count DESC LIMIT 15 ''', ((datetime.now() - timedelta(days=7)).isoformat(),))
            
            rows = cursor.fetchall()
            conn.close()
            
            maintenance_patterns = ['brain_learning', 'brain_upgrade', 'auto_repair', 'cluster_coordination']
            
            for row in rows:
                op_type, target, count = row
                if op_type in maintenance_patterns and count >= 10:
                    rule = {
                        'rule_code': f'{SELF_DISCOVERY_RULE_PREFIX}MAINTENANCE_FOCUS_{op_type.upper()}',
                        'rule_name': f'维护重点-{op_type}',
                        'rule_value': '1',
                        'rule_type': 'learning',
                        'learning_domain': 'maintenance',
                        'learning_priority': 'high',
                        'discovery_source': 'system_maintenance_logs',
                        'confidence': min(1.0, count * 0.05),
                        'description': f'{op_type}操作频繁，是系统维护重点，建议深入学习相关知识'
                    }
                    rules.append(rule)
            
        except Exception as e:
            logger.info(f"[LearningRuleEngine] 分析维护日志失败: {e}")
        
        return rules
    
    def _analyze_error_patterns(self):
        """分析错误模式"""
        rules = []
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            
            cursor.execute(''' SELECT error_type, COUNT(*) as count FROM error_logs WHERE created_at > ? AND status = 'open' GROUP BY error_type ORDER BY count DESC LIMIT 10 ''', ((datetime.now() - timedelta(days=7)).isoformat(),))
            
            rows = cursor.fetchall()
            conn.close()
            
            for row in rows:
                error_type, count = row
                if count >= 5:
                    rule = {
                        'rule_code': f'{SELF_DISCOVERY_RULE_PREFIX}ERROR_FOCUS_{error_type.upper()}',
                        'rule_name': f'错误聚焦-{error_type}',
                        'rule_value': '1',
                        'rule_type': 'learning',
                        'learning_domain': 'error_handling',
                        'learning_priority': 'high',
                        'discovery_source': 'error_logs',
                        'confidence': min(1.0, count * 0.15),
                        'description': f'{error_type}类型错误频繁发生，需加强相关错误处理知识学习'
                    }
                    rules.append(rule)
            
        except Exception as e:
            logger.info(f"[LearningRuleEngine] 分析错误模式失败: {e}")
        
        return rules
    
    def _analyze_network_learning(self):
        """分析网络学习记录"""
        rules = []
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            
            cursor.execute(''' SELECT domain, COUNT(*) as count, AVG(confidence) as avg_confidence FROM network_learning_records WHERE collected_at > ? GROUP BY domain ORDER BY count DESC LIMIT 10 ''', ((datetime.now() - timedelta(days=7)).isoformat(),))
            
            rows = cursor.fetchall()
            conn.close()
            
            for row in rows:
                domain, count, avg_confidence = row
                if avg_confidence > 0.7:
                    rule = {
                        'rule_code': f'{SELF_DISCOVERY_RULE_PREFIX}NETWORK_FOCUS_{domain.upper()}',
                        'rule_name': f'网络学习重点-{domain}',
                        'rule_value': '1',
                        'rule_type': 'learning',
                        'learning_domain': domain,
                        'learning_priority': 'medium',
                        'discovery_source': 'network_learning_records',
                        'confidence': min(1.0, avg_confidence),
                        'description': f'{domain}领域网络知识质量高，建议持续采集该领域知识'
                    }
                    rules.append(rule)
            
        except Exception as e:
            logger.info(f"[LearningRuleEngine] 分析网络学习失败: {e}")
        
        return rules
    
    def _prioritize_rules(self, rules):
        """优先级排序"""
        priority_weights = {'high': 3, 'medium': 2, 'low': 1}
        
        for rule in rules:
            weight = priority_weights.get(rule.get('learning_priority', 'normal'), 1)
            rule['score'] = rule.get('confidence', 0) * weight
        
        rules.sort(key=lambda x: x.get('score', 0), reverse=True)
        return rules[:30]
    
    def _write_rule_to_system_rules(self, rule):
        """写入规则到system_rules表"""
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            
            cursor.execute(''' INSERT OR REPLACE INTO system_rules (rule_code, rule_name, rule_value, rule_type, description, is_active, updated_at) VALUES (?, ?, ?, ?, ?, ?, ?) ''', (
                rule['rule_code'],
                rule['rule_name'],
                rule['rule_value'],
                rule['rule_type'],
                rule.get('description', ''),
                1,
                datetime.now().isoformat()
            ))
            
            conn.commit()
            conn.close()
            logger.info(f"[LearningRuleEngine] 写入规则: {rule['rule_code']}")
        except Exception as e:
            logger.info(f"[LearningRuleEngine] 写入规则失败: {e}")
    
    def _save_learning_rule(self, rule):
        """保存学习规则到learning_rules表"""
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            
            cursor.execute(''' INSERT OR REPLACE INTO learning_rules (rule_code, rule_name, rule_value, rule_type, learning_domain, learning_priority, discovery_source, confidence, is_active, updated_at, description) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?) ''', (
                rule['rule_code'],
                rule['rule_name'],
                rule['rule_value'],
                rule['rule_type'],
                rule.get('learning_domain', ''),
                rule.get('learning_priority', 'normal'),
                rule.get('discovery_source', ''),
                rule.get('confidence', 0),
                1,
                datetime.now().isoformat(),
                rule.get('description', '')
            ))
            
            conn.commit()
            conn.close()
        except Exception as e:
            logger.info(f"[LearningRuleEngine] 保存学习规则失败: {e}")
    
    def execute_learning_policy(self):
        """执行学习政策"""
        logger.info("[LearningRuleEngine] 开始执行学习政策...")
        
        active_rules = self._get_active_learning_rules()
        if not active_rules:
            logger.info("[LearningRuleEngine] 无活动学习规则")
            return {'success': False, 'message': '无活动学习规则'}
        
        executed_count = 0
        for rule in active_rules:
            result = self._execute_rule(rule)
            if result['success']:
                executed_count += 1
            self._record_policy_execution(rule, result)
        
        logger.info(f"[LearningRuleEngine] 执行完成, 成功 {executed_count}/{len(active_rules)}")
        return {'success': True, 'executed': executed_count, 'total': len(active_rules)}
    
    def _get_active_learning_rules(self):
        """获取活动学习规则"""
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            cursor.execute(''' SELECT * FROM learning_rules WHERE is_active = 1 AND confidence >= 0.5 ORDER BY learning_priority DESC, confidence DESC LIMIT 20 ''')
            rows = cursor.fetchall()
            conn.close()
            
            rules = []
            for row in rows:
                rules.append({
                    'rule_code': row[1],
                    'rule_name': row[2],
                    'rule_value': row[3],
                    'learning_domain': row[5],
                    'learning_priority': row[6],
                    'confidence': row[8],
                    'description': row[14]
                })
            
            return rules
        except Exception as e:
            logger.info(f"[LearningRuleEngine] 获取活动规则失败: {e}")
            return []
    
    def _execute_rule(self, rule):
        """执行单个规则"""
        domain = rule.get('learning_domain', '')
        
        executions = {
            'Python': self._execute_python_learning,
            'Flask': self._execute_flask_learning,
            'SQLite': self._execute_database_learning,
            'Security': self._execute_security_learning,
            'AI': self._execute_ai_learning,
            'upgrade': self._execute_upgrade_learning,
            'maintenance': self._execute_maintenance_learning,
            'error_handling': self._execute_error_handling_learning,
        }
        
        executor = executions.get(domain, self._execute_default_learning)
        
        try:
            result = executor(rule)
            self._update_rule_execution(rule['rule_code'])
            return result
        except Exception as e:
            logger.info(f"[LearningRuleEngine] 执行规则失败 {rule['rule_code']}: {e}")
            return {'success': False, 'error': str(e)}
    
    def _execute_python_learning(self, rule):
        """执行Python领域学习政策 - 采集针对性知识"""
        keywords = ['Python', 'Python编程', 'Python进阶', 'Python性能优化']
        return self._execute_targeted_learning(rule, keywords)
    
    def _execute_flask_learning(self, rule):
        """执行Flask领域学习政策 - 采集针对性知识"""
        keywords = ['Flask', 'Flask路由', 'Flask中间件', 'Flask安全']
        return self._execute_targeted_learning(rule, keywords)
    
    def _execute_database_learning(self, rule):
        """执行数据库领域学习政策 - 采集针对性知识"""
        keywords = ['SQLite', '数据库优化', 'SQL性能', '数据存储']
        return self._execute_targeted_learning(rule, keywords)
    
    def _execute_security_learning(self, rule):
        """执行安全领域学习政策 - 采集针对性知识"""
        keywords = ['网络安全', 'XSS防护', 'CSRF防护', 'SQL注入', '安全加固']
        return self._execute_targeted_learning(rule, keywords)
    
    def _execute_ai_learning(self, rule):
        """执行AI领域学习政策 - 采集针对性知识"""
        topic = rule.get('rule_name', '')
        keywords = ['人工智能', '机器学习', '深度学习', '神经网络', '强化学习', 'LLM']
        if '强化学习' in topic:
            keywords = ['强化学习', 'RL算法', 'Q学习', '策略梯度']
        elif '神经网络' in topic:
            keywords = ['神经网络', '深度学习', 'CNN', 'Transformer']
        return self._execute_targeted_learning(rule, keywords)
    
    def _execute_upgrade_learning(self, rule):
        """执行升级领域学习政策 - 采集针对性知识"""
        keywords = ['系统升级', '软件更新', '版本管理', '升级策略']
        return self._execute_targeted_learning(rule, keywords)
    
    def _execute_maintenance_learning(self, rule):
        """执行维护领域学习政策 - 采集针对性知识"""
        keywords = ['系统维护', '故障排查', '性能监控', '运维管理']
        return self._execute_targeted_learning(rule, keywords)
    
    def _execute_error_handling_learning(self, rule):
        """执行错误处理学习政策 - 采集针对性知识"""
        topic = rule.get('rule_name', '')
        keywords = ['错误处理', '异常处理', 'HTTP错误', '调试技巧']
        if 'HTTP_500' in topic or '500' in topic:
            keywords = ['HTTP 500', '服务器错误', '错误日志', '故障诊断']
        return self._execute_targeted_learning(rule, keywords)
    
    def _execute_default_learning(self, rule):
        """执行默认学习政策 - 采集针对性知识"""
        domain = rule.get('learning_domain', '')
        keywords = [domain, rule.get('rule_name', '')]
        return self._execute_targeted_learning(rule, keywords)
    
    def _execute_targeted_learning(self, rule, keywords):
        """执行针对性学习 - 使用网络采集器搜索相关知识（去重）"""
        logger.info(f"[LearningRuleEngine] 执行针对性学习: {rule['rule_name']}, 关键词: {keywords}")
        
        if self.network_collector:
            try:
                unsearched = self.network_collector.get_unsearched_keywords(keywords)
                
                if not unsearched:
                    logger.info(f"[LearningRuleEngine] 所有关键词已搜索过，跳过")
                    return {'success': True, 'message': '所有关键词已搜索过', 'points_collected': 0}
                
                self.network_collector.set_dynamic_keywords(unsearched)
                points = self.network_collector._search_web_for_keywords(unsearched, max_results=2)
                
                if points:
                    self.network_collector._save_knowledge(points)
                    self.network_collector.feed_to_brain()
                    self.network_collector.mark_keywords_searched(unsearched)
                    logger.info(f"[LearningRuleEngine] 成功采集 {len(points)} 个知识点并投喂到脑库")
                    
                    domain = rule.get('learning_domain', '')
                    self._adjust_learning_policy(domain, success=True, points_collected=len(points))
                    
                    return {'success': True, 'message': f"成功采集 {len(points)} 个知识点并投喂到脑库",
                    'points_collected': len(points)}
                else:
                    logger.info(f"[LearningRuleEngine] 未采集到知识点")
                    
                    domain = rule.get('learning_domain', '')
                    self._adjust_learning_policy(domain, success=False, points_collected=0)
                    
                    return {'success': True, 'message': '未采集到知识点', 'points_collected': 0}
            except Exception as e:
                logger.info(f"[LearningRuleEngine] 针对性学习失败: {e}")
                return {'success': False, 'error': str(e)}
        else:
            logger.info(f"[LearningRuleEngine] 网络采集器未设置，仅记录政策执行")
            return {'success': True, 'message': '网络采集器未设置，政策已记录', 'points_collected': 0}
    
    def _adjust_learning_policy(self, domain, success, points_collected):
        """根据学习结果调整系统学习政策"""
        if not domain:
            return
        
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            
            if success and points_collected > 0:
                new_confidence = max(0.1, 0.3 - points_collected * 0.05)
                cursor.execute(''' INSERT OR REPLACE INTO system_rules (rule_code, rule_name, rule_value, rule_type, description, is_active) VALUES (?, ?, ?, ?, ?, 1) ''', (
                    f'SELF_LEARNING_MIN_CONFIDENCE_{domain}',
                    f'{domain}领域最低置信度',
                    str(new_confidence),
                    'learning',
                    f'{domain}领域学习成功，降低置信度阈值至{new_confidence}'
                ))
                logger.info(f"[LearningRuleEngine] 更新政策: {domain}领域置信度阈值调整为{new_confidence}")
            else:
                cursor.execute(''' INSERT OR REPLACE INTO system_rules (rule_code, rule_name, rule_value, rule_type, description, is_active) VALUES (?, ?, ?, ?, ?, 1) ''', (
                    f'SELF_LEARNING_RETRY_COUNT_{domain}',
                    f'{domain}领域重试次数',
                    '3',
                    'learning',
                    f'{domain}领域学习失败，设置重试次数为3'
                ))
                logger.info(f"[LearningRuleEngine] 更新政策: {domain}领域设置重试次数为3")
            
            conn.commit()
            conn.close()
        except Exception as e:
            logger.info(f"[LearningRuleEngine] 调整学习政策失败: {e}")
    
    def _update_rule_execution(self, rule_code):
        """更新规则执行计数"""
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            cursor.execute(''' UPDATE learning_rules SET execution_count = execution_count + 1, last_executed = ?, updated_at = ? WHERE rule_code = ? ''', (datetime.now().isoformat(), datetime.now().isoformat(), rule_code))
            conn.commit()
            conn.close()
        except Exception as e:
            logger.info(f"[LearningRuleEngine] 更新规则执行计数失败: {e}")
    
    def _record_policy_execution(self, rule, result):
        """记录政策执行"""
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            
            cursor.execute(''' INSERT INTO learning_policy_executions (policy_id, policy_name, execution_type, target_domain, execution_result, success, executed_at) VALUES (?, ?, ?, ?, ?, ?, ?) ''', (
                rule['rule_code'],
                rule['rule_name'],
                'learning_policy',
                rule.get('learning_domain', ''),
                result.get('message', ''),
                1 if result.get('success') else 0,
                datetime.now().isoformat()
            ))
            
            conn.commit()
            conn.close()
        except Exception as e:
            logger.info(f"[LearningRuleEngine] 记录政策执行失败: {e}")
    
    def get_discovered_rules(self):
        """获取发现的规则"""
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            cursor.execute(''' SELECT * FROM learning_rules ORDER BY confidence DESC, learning_priority DESC ''')
            rows = cursor.fetchall()
            conn.close()
            
            rules = []
            for row in rows:
                rules.append({
                    'rule_code': row[1],
                    'rule_name': row[2],
                    'rule_value': row[3],
                    'learning_domain': row[5],
                    'learning_priority': row[6],
                    'confidence': row[8],
                    'execution_count': row[9],
                    'last_executed': row[10],
                    'is_active': row[11],
                    'description': row[14]
                })
            
            return rules
        except Exception as e:
            logger.info(f"[LearningRuleEngine] 获取发现规则失败: {e}")
            return []
    
    def get_policy_executions(self, limit=100):
        """获取政策执行记录"""
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            cursor.execute(''' SELECT * FROM learning_policy_executions ORDER BY executed_at DESC LIMIT ? ''', (limit,))
            rows = cursor.fetchall()
            conn.close()
            
            executions = []
            for row in rows:
                executions.append({
                    'id': row[0],
                    'policy_id': row[1],
                    'policy_name': row[2],
                    'execution_type': row[3],
                    'target_domain': row[4],
                    'execution_result': row[6],
                    'success': row[7],
                    'executed_at': row[8]
                })
            
            return executions
        except Exception as e:
            logger.info(f"[LearningRuleEngine] 获取政策执行记录失败: {e}")
            return []
    
    def start_auto_discovery(self, interval=7200):
        """启动自动发现"""
        if self.is_running:
            return {'success': False, 'message': '自动发现已在运行'}
        
        self.is_running = True
        self.rule_thread = threading.Thread(target=self._discovery_loop, args=(interval,), daemon=True)
        self.rule_thread.start()
        return {'success': True, 'message': f'自动发现已启动, 间隔 {interval} 秒'}
    
    def stop_auto_discovery(self):
        """停止自动发现"""
        self.is_running = False
        if self.rule_thread:
            self.rule_thread.join(timeout=10)
        return {'success': True, 'message': '自动发现已停止'}
    
    def _discovery_loop(self, interval):
        """发现循环"""
        while self.is_running:
            self.discover_learning_directions()
            self.execute_learning_policy()
            
            for i in range(interval):
                if not self.is_running:
                    break
                time.sleep(1)

learning_rule_engine = LearningRuleEngine()