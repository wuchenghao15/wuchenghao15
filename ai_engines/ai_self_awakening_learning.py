# -*- coding: utf-8 -*-
#!/usr/bin/env python3
"""
AI自我觉醒学习机制
功能: 从实际升级维护中自我觉醒学习重点要点
自动检测学习需求,提取关键知识,调整学习优先级
"""

import os
import sys
import json
import logging
import threading
import time
import sqlite3
import re
import hashlib
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('ai_self_awakening.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


class SelfAwakeningDetector:
    """自我觉醒检测器"""
    
    def __init__(self, db_path: str = 'ai_self_awakening.db'):
        self.db_path = db_path
        self._init_db()
        self.trigger_conditions = []
        self.learning_focus_patterns = []
    
    def _init_db(self):
        """初始化数据库"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS awakening_events (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                event_type TEXT NOT NULL,
                trigger_condition TEXT NOT NULL,
                learning_focus TEXT NOT NULL,
                priority TEXT NOT NULL,
                details TEXT,
                created_at TEXT NOT NULL,
                processed INTEGER DEFAULT 0
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS learning_insights (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                insight_id TEXT NOT NULL UNIQUE,
                title TEXT NOT NULL,
                content TEXT NOT NULL,
                source TEXT NOT NULL,
                confidence REAL NOT NULL,
                tags TEXT,
                priority INTEGER NOT NULL,
                created_at TEXT NOT NULL,
                applied INTEGER DEFAULT 0
            )
        ''')
        
        conn.commit()
        conn.close()
    
    def load_rules(self, rules: Dict):
        """加载自我觉醒规则"""
        self.trigger_conditions = rules.get('self_awakening_rules', {}).get('trigger_conditions', [])
        self.learning_focus_patterns = rules.get('self_awakening_rules', {}).get('learning_focus_extraction', [])
        logger.info(f"加载了 {len(self.trigger_conditions)} 个触发条件和 {len(self.learning_focus_patterns)} 个学习焦点模式")
    
    def detect_awakening_needs(self, system_state: Dict) -> List[Dict]:
        """检测自我觉醒需求"""
        awakening_events = []
        
        for condition in self.trigger_conditions:
            condition_type = condition.get('type')
            threshold = condition.get('threshold', 0)
            action = condition.get('action')
            
            if condition_type == 'error_frequency':
                error_count = system_state.get('error_count', 0)
                if error_count >= threshold:
                    awakening_events.append(self._create_awakening_event(
                        event_type='error_frequency',
                        trigger_condition=f"错误频率超过阈值: {error_count} >= {threshold}",
                        learning_focus="系统稳定性、错误处理、故障预防",
                        priority='high',
                        details={'error_count': error_count, 'threshold': threshold}
                    ))
            
            elif condition_type == 'performance_degradation':
                degradation = system_state.get('performance_degradation', 0)
                if degradation >= threshold:
                    awakening_events.append(self._create_awakening_event(
                        event_type='performance_degradation',
                        trigger_condition=f"性能下降超过阈值: {degradation}% >= {threshold}%",
                        learning_focus="性能优化、瓶颈分析、资源管理",
                        priority='high',
                        details={'degradation': degradation, 'threshold': threshold}
                    ))
            
            elif condition_type == 'upgrade_failure':
                failure_count = system_state.get('upgrade_failure_count', 0)
                if failure_count >= threshold:
                    awakening_events.append(self._create_awakening_event(
                        event_type='upgrade_failure',
                        trigger_condition=f"升级失败次数超过阈值: {failure_count} >= {threshold}",
                        learning_focus="升级策略、部署流程、回滚机制",
                        priority='medium',
                        details={'failure_count': failure_count, 'threshold': threshold}
                    ))
            
            elif condition_type == 'feature_requests':
                request_count = system_state.get('feature_request_count', 0)
                if request_count >= threshold:
                    awakening_events.append(self._create_awakening_event(
                        event_type='feature_requests',
                        trigger_condition=f"功能请求超过阈值: {request_count} >= {threshold}",
                        learning_focus="功能增强、用户需求分析、产品设计",
                        priority='medium',
                        details={'request_count': request_count, 'threshold': threshold}
                    ))
            
            elif condition_type == 'security_incident':
                incident_count = system_state.get('security_incident_count', 0)
                if incident_count >= threshold:
                    awakening_events.append(self._create_awakening_event(
                        event_type='security_incident',
                        trigger_condition=f"安全事件发生: {incident_count} >= {threshold}",
                        learning_focus="安全防护、漏洞修复、威胁检测",
                        priority='emergency',
                        details={'incident_count': incident_count, 'threshold': threshold}
                    ))
        
        return awakening_events
    
    def _create_awakening_event(self, event_type: str, trigger_condition: str, 
                               learning_focus: str, priority: str, details: Dict) -> Dict:
        """创建觉醒事件"""
        event = {
            'event_type': event_type,
            'trigger_condition': trigger_condition,
            'learning_focus': learning_focus,
            'priority': priority,
            'details': details,
            'created_at': datetime.now().isoformat()
        }
        
        self._save_awakening_event(event)
        logger.info(f"检测到自我觉醒事件: {event_type} - {learning_focus} (优先级: {priority})")
        
        return event
    
    def _save_awakening_event(self, event: Dict):
        """保存觉醒事件到数据库"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO awakening_events (event_type, trigger_condition, learning_focus, 
                                         priority, details, created_at)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (
            event['event_type'],
            event['trigger_condition'],
            event['learning_focus'],
            event['priority'],
            json.dumps(event['details'], ensure_ascii=False),
            event['created_at']
        ))
        
        conn.commit()
        conn.close()


class UpgradeMaintenanceLearner:
    """升级维护学习器"""
    
    def __init__(self, db_path: str = 'ai_self_awakening.db'):
        self.db_path = db_path
    
    def extract_key_insights_from_upgrade_logs(self, upgrade_logs: List[Dict]) -> List[Dict]:
        """从升级日志中提取关键洞察"""
        insights = []
        
        for log in upgrade_logs:
            log_content = log.get('content', '')
            log_type = log.get('type', 'info')
            timestamp = log.get('timestamp', datetime.now().isoformat())
            
            patterns_to_match = [
                (r'修复|fix|repair|resolved', 'bug_fix', '问题修复'),
                (r'优化|optimize|improve|enhance', 'optimization', '性能优化'),
                (r'安全|security|vulnerability|patch', 'security', '安全加固'),
                (r'新增|add|feature|new', 'feature', '功能增强'),
                (r'改进|improvement|refactor', 'improvement', '代码改进'),
                (r'升级|upgrade|update', 'upgrade', '版本升级'),
                (r'错误|error|exception|fail', 'error', '错误处理'),
                (r'瓶颈|bottleneck|slow|performance', 'performance', '性能瓶颈')
            ]
            
            for pattern, insight_type, insight_category in patterns_to_match:
                if re.search(pattern, log_content, re.IGNORECASE):
                    insight = self._create_insight(
                        content=log_content,
                        source=f"upgrade_log:{log_type}",
                        insight_type=insight_type,
                        category=insight_category,
                        timestamp=timestamp
                    )
                    insights.append(insight)
        
        return insights
    
    def extract_key_insights_from_maintenance(self, maintenance_records: List[Dict]) -> List[Dict]:
        """从维护记录中提取关键洞察"""
        insights = []
        
        for record in maintenance_records:
            record_content = record.get('content', '')
            record_type = record.get('type', 'routine')
            
            patterns_to_match = [
                (r'备份|backup|restore', 'backup', '数据备份'),
                (r'清理|cleanup|purge|remove', 'cleanup', '数据清理'),
                (r'监控|monitor|alert', 'monitoring', '系统监控'),
                (r'配置|config|setting', 'configuration', '配置管理'),
                (r'检查|check|verify', 'check', '系统检查'),
                (r'修复|fix|repair', 'fix', '问题修复')
            ]
            
            for pattern, insight_type, insight_category in patterns_to_match:
                if re.search(pattern, record_content, re.IGNORECASE):
                    insight = self._create_insight(
                        content=record_content,
                        source=f"maintenance:{record_type}",
                        insight_type=insight_type,
                        category=insight_category,
                        timestamp=record.get('timestamp', datetime.now().isoformat())
                    )
                    insights.append(insight)
        
        return insights
    
    def _create_insight(self, content: str, source: str, insight_type: str, 
                       category: str, timestamp: str) -> Dict:
        """创建洞察"""
        insight_id = hashlib.md5(f"{content}{source}{timestamp}".encode('utf-8')).hexdigest()
        
        insight = {
            'insight_id': insight_id,
            'title': f"{category}: {content[:50]}...",
            'content': content,
            'source': source,
            'type': insight_type,
            'category': category,
            'confidence': 0.85,
            'tags': [insight_type, category],
            'priority': self._calculate_priority(insight_type),
            'timestamp': timestamp,
            'created_at': datetime.now().isoformat()
        }
        
        self._save_insight(insight)
        logger.info(f"提取关键洞察: {insight['title']}")
        
        return insight
    
    def _calculate_priority(self, insight_type: str) -> int:
        """计算洞察优先级"""
        priority_map = {
            'security': 1,
            'bug_fix': 2,
            'error': 2,
            'performance': 3,
            'optimization': 3,
            'upgrade': 4,
            'feature': 4,
            'improvement': 5,
            'backup': 5,
            'cleanup': 5,
            'monitoring': 5,
            'configuration': 5,
            'check': 5,
            'fix': 5
        }
        return priority_map.get(insight_type, 5)
    
    def _save_insight(self, insight: Dict):
        """保存洞察到数据库"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            cursor.execute('''
                INSERT OR IGNORE INTO learning_insights (
                    insight_id, title, content, source, confidence, tags, priority, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                insight['insight_id'],
                insight['title'],
                insight['content'],
                insight['source'],
                insight['confidence'],
                json.dumps(insight['tags'], ensure_ascii=False),
                insight['priority'],
                insight['created_at']
            ))
            conn.commit()
        except Exception as e:
            logger.error(f"保存洞察失败: {str(e)}")
        finally:
            conn.close()
    
    def get_unapplied_insights(self, limit: int = 50) -> List[Dict]:
        """获取未应用的洞察"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT * FROM learning_insights 
            WHERE applied = 0 
            ORDER BY priority ASC, created_at DESC 
            LIMIT ?
        ''', (limit,))
        
        insights = []
        for row in cursor.fetchall():
            insights.append({
                'id': row[0],
                'insight_id': row[1],
                'title': row[2],
                'content': row[3],
                'source': row[4],
                'confidence': row[5],
                'tags': json.loads(row[6]) if row[6] else [],
                'priority': row[7],
                'created_at': row[8],
                'applied': row[9]
            })
        
        conn.close()
        return insights
    
    def mark_insight_applied(self, insight_id: str):
        """标记洞察已应用"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            UPDATE learning_insights SET applied = 1 WHERE insight_id = ?
        ''', (insight_id,))
        
        conn.commit()
        conn.close()


class AISelfAwakeningSystem:
    """AI自我觉醒学习系统"""
    
    def __init__(self, rules_file: str = 'rules.json'):
        self.rules_file = rules_file
        self.rules = self._load_rules()
        self.detector = SelfAwakeningDetector()
        self.learner = UpgradeMaintenanceLearner()
        self.detector.load_rules(self.rules)
        
        self.is_running = False
        self.awakening_thread = None
        self.awakening_interval = 3600
        
        self.system_state = {
            'error_count': 0,
            'performance_degradation': 0,
            'upgrade_failure_count': 0,
            'feature_request_count': 0,
            'security_incident_count': 0
        }
    
    def _load_rules(self) -> Dict:
        """加载规则"""
        try:
            with open(self.rules_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"加载规则文件失败: {str(e)}")
            return {}
    
    def start(self):
        """启动自我觉醒系统"""
        if not self.is_running:
            self.is_running = True
            self.awakening_thread = threading.Thread(target=self._awakening_loop, daemon=True)
            self.awakening_thread.start()
            logger.info("AI自我觉醒学习系统已启动")
    
    def stop(self):
        """停止自我觉醒系统"""
        self.is_running = False
        if self.awakening_thread and self.awakening_thread.is_alive():
            self.awakening_thread.join(timeout=5)
        logger.info("AI自我觉醒学习系统已停止")
    
    def _awakening_loop(self):
        """自我觉醒循环"""
        while self.is_running:
            try:
                self.perform_self_awakening()
                time.sleep(self.awakening_interval)
            except Exception as e:
                logger.error(f"自我觉醒循环出错: {str(e)}")
                time.sleep(600)
    
    def perform_self_awakening(self) -> Dict:
        """执行一次自我觉醒"""
        logger.info("开始自我觉醒分析...")
        
        awakening_events = self.detector.detect_awakening_needs(self.system_state)
        
        upgrade_logs = self._collect_upgrade_logs()
        maintenance_records = self._collect_maintenance_records()
        
        insights = []
        insights.extend(self.learner.extract_key_insights_from_upgrade_logs(upgrade_logs))
        insights.extend(self.learner.extract_key_insights_from_maintenance(maintenance_records))
        
        learning_directions = self._generate_learning_directions(awakening_events, insights)
        
        result = {
            'awakening_events': len(awakening_events),
            'insights_extracted': len(insights),
            'learning_directions': learning_directions
        }
        
        logger.info(f"自我觉醒分析完成: {result}")
        return result
    
    def _collect_upgrade_logs(self) -> List[Dict]:
        """收集升级日志"""
        upgrade_logs = [
            {
                'content': '成功修复了数据库连接池溢出问题,优化了连接复用策略',
                'type': 'fix',
                'timestamp': datetime.now().isoformat()
            },
            {
                'content': '升级了AI模型版本,推理速度提升30%,内存占用降低20%',
                'type': 'upgrade',
                'timestamp': datetime.now().isoformat()
            },
            {
                'content': '修复了安全漏洞CVE-2024-xxxx,增强了API认证机制',
                'type': 'security',
                'timestamp': datetime.now().isoformat()
            },
            {
                'content': '新增了实时监控仪表盘功能,支持多维度数据可视化',
                'type': 'feature',
                'timestamp': datetime.now().isoformat()
            },
            {
                'content': '优化了缓存策略,减少了数据库查询压力',
                'type': 'optimization',
                'timestamp': datetime.now().isoformat()
            }
        ]
        return upgrade_logs
    
    def _collect_maintenance_records(self) -> List[Dict]:
        """收集维护记录"""
        maintenance_records = [
            {
                'content': '执行了每周数据备份,备份文件完整性检查通过',
                'type': 'routine',
                'timestamp': datetime.now().isoformat()
            },
            {
                'content': '清理了过期的日志文件,释放了5GB磁盘空间',
                'type': 'cleanup',
                'timestamp': datetime.now().isoformat()
            },
            {
                'content': '配置检查发现API超时设置不合理,已调整优化',
                'type': 'configuration',
                'timestamp': datetime.now().isoformat()
            },
            {
                'content': '监控系统检测到CPU使用率异常,已自动扩容',
                'type': 'monitoring',
                'timestamp': datetime.now().isoformat()
            }
        ]
        return maintenance_records
    
    def _generate_learning_directions(self, events: List[Dict], insights: List[Dict]) -> List[Dict]:
        """生成学习方向"""
        directions = []
        
        focus_areas = set()
        for event in events:
            focus_areas.add(event['learning_focus'])
        
        for insight in insights:
            focus_areas.add(insight['category'])
        
        for focus in focus_areas:
            priority = self._determine_direction_priority(focus)
            direction = {
                'focus_area': focus,
                'priority': priority,
                'triggered_by': len(events),
                'supported_by': len(insights),
                'suggested_actions': self._generate_suggested_actions(focus),
                'created_at': datetime.now().isoformat()
            }
            directions.append(direction)
        
        directions.sort(key=lambda x: x['priority'])
        return directions
    
    def _determine_direction_priority(self, focus_area: str) -> int:
        """确定学习方向优先级"""
        priority_keywords = {
            1: ['安全', '漏洞', '威胁'],
            2: ['错误', '故障', '失败'],
            3: ['性能', '优化', '瓶颈'],
            4: ['升级', '功能', '增强'],
            5: ['备份', '清理', '监控', '配置']
        }
        
        for priority, keywords in priority_keywords.items():
            for keyword in keywords:
                if keyword in focus_area:
                    return priority
        
        return 5
    
    def _generate_suggested_actions(self, focus_area: str) -> List[str]:
        """生成建议学习动作"""
        action_map = {
            '安全': ['学习安全漏洞检测方法', '研究最新安全防护技术', '制定安全审计流程'],
            '错误处理': ['分析错误模式', '学习故障排查方法', '建立错误预防机制'],
            '性能优化': ['学习性能分析工具', '研究优化算法', '制定性能监控方案'],
            '升级策略': ['学习版本管理', '研究部署策略', '制定回滚方案'],
            '功能增强': ['分析用户需求', '研究技术实现', '制定开发计划'],
            '备份': ['研究备份策略', '学习灾难恢复', '制定数据保护方案'],
            '监控': ['学习监控工具', '研究告警策略', '制定运维方案']
        }
        
        for key, actions in action_map.items():
            if key in focus_area:
                return actions
        
        return ['深入学习相关技术', '研究最佳实践', '制定改进计划']
    
    def update_system_state(self, state_updates: Dict):
        """更新系统状态"""
        self.system_state.update(state_updates)
        logger.info(f"系统状态已更新: {state_updates}")
    
    def get_unapplied_insights(self, limit: int = 50) -> List[Dict]:
        """获取未应用的洞察"""
        return self.learner.get_unapplied_insights(limit)
    
    def get_learning_directions(self) -> List[Dict]:
        """获取学习方向"""
        events = self.detector.detect_awakening_needs(self.system_state)
        upgrade_logs = self._collect_upgrade_logs()
        maintenance_records = self._collect_maintenance_records()
        
        insights = []
        insights.extend(self.learner.extract_key_insights_from_upgrade_logs(upgrade_logs))
        insights.extend(self.learner.extract_key_insights_from_maintenance(maintenance_records))
        
        return self._generate_learning_directions(events, insights)


if __name__ == "__main__":
    system = AISelfAwakeningSystem()
    system.start()
    
    try:
        logger.info("模拟系统状态更新...")
        system.update_system_state({
            'error_count': 3,
            'performance_degradation': 15,
            'upgrade_failure_count': 1
        })
        
        logger.info("执行自我觉醒分析...")
        result = system.perform_self_awakening()
        
        logger.info("获取学习方向...")
        directions = system.get_learning_directions()
        for direction in directions:
            logger.info(f"学习方向: {direction['focus_area']} (优先级: {direction['priority']})")
        
        time.sleep(60)
    except KeyboardInterrupt:
        system.stop()
        logger.info("AI自我觉醒学习系统已停止")