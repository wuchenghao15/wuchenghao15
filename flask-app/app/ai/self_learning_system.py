# -*- coding: utf-8 -*-
"""
AI自学习系统模块 - 系统自学习和优化
功能：
1. 系统模式分析 - 从历史数据中识别模式和趋势
2. 性能跟踪 - 监控系统性能指标
3. 洞察生成 - 基于分析生成改进建议
4. 知识积累 - 持续学习和积累系统知识
5. 自适应优化 - 根据学习结果自动调整系统配置
"""

import os
import json
import logging
import sqlite3
import time
import threading
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple
from collections import defaultdict, Counter

logger = logging.getLogger(__name__)

DATABASE_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))), 'app.db')

class LearningPattern:
    """学习模式类"""
    
    PATTERN_TYPES = {
        'performance_degradation': '性能下降模式',
        'high_load_period': '高负载时段模式',
        'user_activity_pattern': '用户活动模式',
        'error_frequency': '错误频率模式',
        'resource_usage': '资源使用模式',
        'task_completion': '任务完成模式',
        'ai_employee_efficiency': 'AI员工效率模式',
        'learning_effectiveness': '学习效果模式'
    }
    
    def __init__(self, pattern_type: str, data: Dict[str, Any], confidence: float = 0.0):
        self.pattern_type = pattern_type
        self.data = data
        self.confidence = confidence
        self.detected_at = datetime.now()
        self.insights = []
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'pattern_type': self.pattern_type,
            'pattern_name': self.PATTERN_TYPES.get(self.pattern_type, self.pattern_type),
            'data': self.data,
            'confidence': self.confidence,
            'detected_at': self.detected_at.isoformat(),
            'insights': self.insights
        }

class SystemInsight:
    """系统洞察类"""
    
    INSIGHT_LEVELS = {
        'critical': '关键',
        'high': '高',
        'medium': '中',
        'low': '低'
    }
    
    INSIGHT_TYPES = {
        'performance': '性能优化',
        'security': '安全建议',
        'resource': '资源管理',
        'user_experience': '用户体验',
        'system_health': '系统健康',
        'ai_empowerment': 'AI赋能',
        'scalability': '可扩展性',
        'maintenance': '维护建议'
    }
    
    def __init__(self, insight_type: str, message: str, level: str = 'medium', 
                 recommendation: str = '', evidence: Dict[str, Any] = None):
        self.insight_type = insight_type
        self.message = message
        self.level = level
        self.recommendation = recommendation
        self.evidence = evidence or {}
        self.created_at = datetime.now()
        self.applied = False
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'insight_type': self.insight_type,
            'insight_name': self.INSIGHT_TYPES.get(self.insight_type, self.insight_type),
            'level': self.level,
            'level_name': self.INSIGHT_LEVELS.get(self.level, self.level),
            'message': self.message,
            'recommendation': self.recommendation,
            'evidence': self.evidence,
            'created_at': self.created_at.isoformat(),
            'applied': self.applied
        }

class SelfLearningSystem:
    """AI自学习系统"""
    
    def __init__(self):
        self.enabled = True
        self.learning_data = {}
        self.patterns = []
        self.insights = []
        self.performance_metrics = {}
        self.learning_history = []
        self.knowledge_base = {}
        self.analysis_cache = {}
        self._lock = threading.RLock()
        self._learning_thread = None
        self._is_learning = False
        
        self._init_knowledge_base()
        self._create_tables()
    
    def _create_tables(self):
        """创建学习相关数据表"""
        try:
            with sqlite3.connect(DATABASE_PATH) as conn:
                cursor = conn.cursor()
                
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS learning_patterns (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        pattern_type TEXT NOT NULL,
                        pattern_data TEXT NOT NULL,
                        confidence REAL DEFAULT 0.0,
                        detected_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        insights TEXT DEFAULT '[]'
                    )
                ''')
                
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS system_insights (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        insight_type TEXT NOT NULL,
                        message TEXT NOT NULL,
                        level TEXT DEFAULT 'medium',
                        recommendation TEXT DEFAULT '',
                        evidence TEXT DEFAULT '{}',
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        applied INTEGER DEFAULT 0
                    )
                ''')
                
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS performance_metrics (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        metric_name TEXT NOT NULL,
                        metric_value REAL NOT NULL,
                        timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                ''')
                
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS learning_history (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        learning_type TEXT NOT NULL,
                        data TEXT NOT NULL,
                        result TEXT DEFAULT '',
                        timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                ''')
                
                conn.commit()
                logger.info("[自学习系统] 数据表创建完成")
        except Exception as e:
            logger.error(f"[自学习系统] 创建数据表失败: {str(e)}")
    
    def _init_knowledge_base(self):
        """初始化知识库"""
        self.knowledge_base = {
            'performance_thresholds': {
                'cpu_warning': 80,
                'cpu_critical': 95,
                'memory_warning': 75,
                'memory_critical': 90,
                'response_time_warning': 2.0,
                'response_time_critical': 5.0,
                'error_rate_warning': 5,
                'error_rate_critical': 15
            },
            'patterns': {
                'morning_peak': {'start': 8, 'end': 10, 'description': '早间用户高峰'},
                'afternoon_peak': {'start': 14, 'end': 16, 'description': '下午用户高峰'},
                'evening_peak': {'start': 19, 'end': 21, 'description': '晚间用户高峰'}
            },
            'optimization_rules': {
                'reduce_batch_size': '当内存使用率超过80%时，减少批处理大小',
                'increase_cache': '当数据库查询响应时间超过2秒时，增加缓存策略',
                'schedule_maintenance': '在低峰期（凌晨2-6点）安排系统维护',
                'scale_up': '当CPU持续超过90%达10分钟时，考虑扩容'
            }
        }
    
    def start_learning(self):
        """启动自学习线程"""
        if self._is_learning:
            return
        
        self._is_learning = True
        self._learning_thread = threading.Thread(
            target=self._learning_loop,
            daemon=True,
            name='SelfLearningThread'
        )
        self._learning_thread.start()
        logger.info("[自学习系统] 自学习线程已启动")
    
    def stop_learning(self):
        """停止自学习线程"""
        self._is_learning = False
        if self._learning_thread:
            self._learning_thread.join(timeout=5)
        logger.info("[自学习系统] 自学习线程已停止")
    
    def _learning_loop(self):
        """自学习主循环"""
        while self._is_learning:
            try:
                self.learn_from_system()
                self.detect_patterns()
                self.generate_insights()
                self.persist_learning()
            except Exception as e:
                logger.error(f"[自学习系统] 学习循环错误: {str(e)}")
            
            time.sleep(300)
    
    def learn_from_system(self):
        """从系统数据中学习"""
        with self._lock:
            now = datetime.now()
            
            learning_result = {
                'timestamp': now.isoformat(),
                'sources': [],
                'patterns_detected': 0,
                'insights_generated': 0
            }
            
            system_data = self._collect_system_data()
            if system_data:
                learning_result['sources'].append('system_data')
                self.learning_data['system'] = system_data
            
            user_activity = self._collect_user_activity()
            if user_activity:
                learning_result['sources'].append('user_activity')
                self.learning_data['user_activity'] = user_activity
            
            ai_performance = self._collect_ai_performance()
            if ai_performance:
                learning_result['sources'].append('ai_performance')
                self.learning_data['ai_performance'] = ai_performance
            
            learning_result['patterns_detected'] = len(self.patterns)
            learning_result['insights_generated'] = len(self.insights)
            
            self.learning_history.append(learning_result)
            if len(self.learning_history) > 100:
                self.learning_history = self.learning_history[-100:]
            
            logger.info(f"[自学习系统] 完成一次学习，数据源: {learning_result['sources']}")
    
    def _collect_system_data(self) -> Dict[str, Any]:
        """收集系统数据"""
        try:
            import psutil
            
            cpu_percent = psutil.cpu_percent(interval=1)
            memory = psutil.virtual_memory()
            disk = psutil.disk_usage('/')
            network = psutil.net_io_counters()
            
            return {
                'cpu_percent': cpu_percent,
                'memory_percent': memory.percent,
                'memory_available': memory.available // (1024 * 1024),
                'disk_percent': disk.percent,
                'disk_used': disk.used // (1024 * 1024 * 1024),
                'network_sent': network.bytes_sent // (1024 * 1024),
                'network_recv': network.bytes_recv // (1024 * 1024),
                'timestamp': datetime.now().isoformat()
            }
        except ImportError:
            return {
                'cpu_percent': 0,
                'memory_percent': 0,
                'memory_available': 0,
                'disk_percent': 0,
                'disk_used': 0,
                'network_sent': 0,
                'network_recv': 0,
                'timestamp': datetime.now().isoformat(),
                'warning': 'psutil not available'
            }
        except Exception as e:
            logger.error(f"[自学习系统] 收集系统数据失败: {str(e)}")
            return {}
    
    def _collect_user_activity(self) -> Dict[str, Any]:
        """收集用户活动数据"""
        try:
            with sqlite3.connect(DATABASE_PATH) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                
                now = datetime.now()
                last_hour = now - timedelta(hours=1)
                last_day = now - timedelta(days=1)
                
                cursor.execute('''
                    SELECT COUNT(*) as count FROM user_sessions 
                    WHERE last_activity >= ?
                ''', (last_hour.isoformat(),))
                active_users = cursor.fetchone()['count']
                
                cursor.execute('''
                    SELECT COUNT(*) as count FROM exam_records 
                    WHERE created_at >= ?
                ''', (last_day.isoformat(),))
                exam_count = cursor.fetchone()['count']
                
                cursor.execute('''
                    SELECT COUNT(*) as count FROM learning_records 
                    WHERE created_at >= ?
                ''', (last_day.isoformat(),))
                learning_count = cursor.fetchone()['count']
                
                cursor.execute('''
                    SELECT role, COUNT(*) as count FROM users 
                    GROUP BY role
                ''')
                role_distribution = {row['role']: row['count'] for row in cursor.fetchall()}
                
                return {
                    'active_users': active_users,
                    'exam_count_today': exam_count,
                    'learning_count_today': learning_count,
                    'role_distribution': role_distribution,
                    'timestamp': datetime.now().isoformat()
                }
        except Exception as e:
            logger.error(f"[自学习系统] 收集用户活动数据失败: {str(e)}")
            return {}
    
    def _collect_ai_performance(self) -> Dict[str, Any]:
        """收集AI员工性能数据"""
        try:
            with sqlite3.connect(DATABASE_PATH) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                
                cursor.execute('''
                    SELECT ai_type, COUNT(*) as task_count, 
                           AVG(execution_time) as avg_time,
                           SUM(CASE WHEN success = 1 THEN 1 ELSE 0 END) as success_count
                    FROM ai_task_logs 
                    WHERE created_at >= ?
                    GROUP BY ai_type
                ''', ((datetime.now() - timedelta(days=1)).isoformat(),))
                
                ai_performance = {}
                for row in cursor.fetchall():
                    ai_type = row['ai_type']
                    task_count = row['task_count']
                    success_count = row['success_count']
                    avg_time = row['avg_time'] or 0
                    
                    ai_performance[ai_type] = {
                        'task_count': task_count,
                        'success_count': success_count,
                        'success_rate': round(success_count / task_count * 100, 2) if task_count > 0 else 0,
                        'avg_execution_time': round(avg_time, 2)
                    }
                
                cursor.execute('''
                    SELECT COUNT(*) as total FROM ai_employees
                ''')
                ai_count = cursor.fetchone()['total']
                
                return {
                    'ai_count': ai_count,
                    'performance_by_type': ai_performance,
                    'timestamp': datetime.now().isoformat()
                }
        except Exception as e:
            logger.error(f"[自学习系统] 收集AI性能数据失败: {str(e)}")
            return {}
    
    def detect_patterns(self):
        """检测系统模式"""
        with self._lock:
            new_patterns = []
            
            perf_data = self.learning_data.get('system', {})
            if perf_data:
                cpu_pattern = self._detect_cpu_pattern(perf_data)
                if cpu_pattern:
                    new_patterns.append(cpu_pattern)
                
                memory_pattern = self._detect_memory_pattern(perf_data)
                if memory_pattern:
                    new_patterns.append(memory_pattern)
            
            user_data = self.learning_data.get('user_activity', {})
            if user_data:
                activity_pattern = self._detect_activity_pattern(user_data)
                if activity_pattern:
                    new_patterns.append(activity_pattern)
            
            ai_data = self.learning_data.get('ai_performance', {})
            if ai_data:
                ai_pattern = self._detect_ai_efficiency_pattern(ai_data)
                if ai_pattern:
                    new_patterns.append(ai_pattern)
            
            self.patterns.extend(new_patterns)
            if len(self.patterns) > 50:
                self.patterns = self.patterns[-50:]
            
            if new_patterns:
                logger.info(f"[自学习系统] 检测到 {len(new_patterns)} 个新模式")
    
    def _detect_cpu_pattern(self, perf_data: Dict[str, Any]) -> Optional[LearningPattern]:
        """检测CPU使用模式"""
        cpu = perf_data.get('cpu_percent', 0)
        thresholds = self.knowledge_base['performance_thresholds']
        
        if cpu >= thresholds['cpu_critical']:
            return LearningPattern(
                pattern_type='performance_degradation',
                data={'metric': 'cpu', 'value': cpu, 'threshold': thresholds['cpu_critical']},
                confidence=0.95
            )
        elif cpu >= thresholds['cpu_warning']:
            return LearningPattern(
                pattern_type='performance_degradation',
                data={'metric': 'cpu', 'value': cpu, 'threshold': thresholds['cpu_warning']},
                confidence=0.75
            )
        return None
    
    def _detect_memory_pattern(self, perf_data: Dict[str, Any]) -> Optional[LearningPattern]:
        """检测内存使用模式"""
        memory = perf_data.get('memory_percent', 0)
        thresholds = self.knowledge_base['performance_thresholds']
        
        if memory >= thresholds['memory_critical']:
            return LearningPattern(
                pattern_type='resource_usage',
                data={'metric': 'memory', 'value': memory, 'threshold': thresholds['memory_critical']},
                confidence=0.95
            )
        elif memory >= thresholds['memory_warning']:
            return LearningPattern(
                pattern_type='resource_usage',
                data={'metric': 'memory', 'value': memory, 'threshold': thresholds['memory_warning']},
                confidence=0.75
            )
        return None
    
    def _detect_activity_pattern(self, user_data: Dict[str, Any]) -> Optional[LearningPattern]:
        """检测用户活动模式"""
        hour = datetime.now().hour
        
        for peak_name, peak_info in self.knowledge_base['patterns'].items():
            if peak_info['start'] <= hour < peak_info['end']:
                return LearningPattern(
                    pattern_type='high_load_period',
                    data={'period': peak_name, 'description': peak_info['description'], 'hour': hour},
                    confidence=0.85
                )
        
        if user_data.get('active_users', 0) > 100:
            return LearningPattern(
                pattern_type='user_activity_pattern',
                data={'active_users': user_data['active_users'], 'description': '高并发用户访问'},
                confidence=0.80
            )
        
        return None
    
    def _detect_ai_efficiency_pattern(self, ai_data: Dict[str, Any]) -> Optional[LearningPattern]:
        """检测AI员工效率模式"""
        perf_by_type = ai_data.get('performance_by_type', {})
        
        for ai_type, metrics in perf_by_type.items():
            if metrics['success_rate'] < 70:
                return LearningPattern(
                    pattern_type='ai_employee_efficiency',
                    data={'ai_type': ai_type, 'success_rate': metrics['success_rate'], 
                          'task_count': metrics['task_count']},
                    confidence=0.80
                )
        
        return None
    
    def generate_insights(self):
        """生成系统洞察"""
        with self._lock:
            new_insights = []
            
            for pattern in self.patterns:
                insights = self._generate_insights_from_pattern(pattern)
                new_insights.extend(insights)
            
            system_insights = self._generate_system_health_insights()
            new_insights.extend(system_insights)
            
            ai_insights = self._generate_ai_empowerment_insights()
            new_insights.extend(ai_insights)
            
            self.insights.extend(new_insights)
            if len(self.insights) > 100:
                self.insights = self.insights[-100:]
            
            if new_insights:
                logger.info(f"[自学习系统] 生成 {len(new_insights)} 条新洞察")
    
    def _generate_insights_from_pattern(self, pattern: LearningPattern) -> List[SystemInsight]:
        """从模式生成洞察"""
        insights = []
        
        if pattern.pattern_type == 'performance_degradation':
            metric = pattern.data.get('metric', '')
            value = pattern.data.get('value', 0)
            
            if value >= self.knowledge_base['performance_thresholds'][f'{metric}_critical']:
                insights.append(SystemInsight(
                    insight_type='performance',
                    message=f"{metric.upper()}使用率达到临界值 {value}%",
                    level='critical',
                    recommendation=self.knowledge_base['optimization_rules']['scale_up'],
                    evidence=pattern.data
                ))
            else:
                insights.append(SystemInsight(
                    insight_type='performance',
                    message=f"{metric.upper()}使用率接近警戒线 {value}%",
                    level='high',
                    recommendation=self.knowledge_base['optimization_rules']['reduce_batch_size'],
                    evidence=pattern.data
                ))
        
        elif pattern.pattern_type == 'resource_usage':
            insights.append(SystemInsight(
                insight_type='resource',
                message=f"内存使用率 {pattern.data.get('value', 0)}%",
                level='medium',
                recommendation=self.knowledge_base['optimization_rules']['increase_cache'],
                evidence=pattern.data
            ))
        
        elif pattern.pattern_type == 'high_load_period':
            insights.append(SystemInsight(
                insight_type='user_experience',
                message=f"当前处于{pattern.data.get('description', '')}",
                level='low',
                recommendation='建议准备扩容资源或启用缓存策略',
                evidence=pattern.data
            ))
        
        elif pattern.pattern_type == 'ai_employee_efficiency':
            insights.append(SystemInsight(
                insight_type='ai_empowerment',
                message=f"AI员工类型 {pattern.data.get('ai_type', '')} 成功率低于70%",
                level='high',
                recommendation='建议检查该类型AI员工配置，考虑增加培训或调整参数',
                evidence=pattern.data
            ))
        
        return insights
    
    def _generate_system_health_insights(self) -> List[SystemInsight]:
        """生成系统健康洞察"""
        insights = []
        
        try:
            with sqlite3.connect(DATABASE_PATH) as conn:
                cursor = conn.cursor()
                
                cursor.execute('''
                    SELECT COUNT(*) as count FROM error_logs 
                    WHERE created_at >= ?
                ''', ((datetime.now() - timedelta(hours=1)).isoformat(),))
                recent_errors = cursor.fetchone()[0]
                
                if recent_errors > 10:
                    insights.append(SystemInsight(
                        insight_type='system_health',
                        message=f"最近1小时出现 {recent_errors} 个错误",
                        level='high',
                        recommendation='建议检查系统日志，排查错误原因',
                        evidence={'error_count': recent_errors}
                    ))
                
                cursor.execute('''
                    SELECT COUNT(*) as count FROM maintenance_tasks 
                    WHERE status = 'pending'
                ''')
                pending_tasks = cursor.fetchone()[0]
                
                if pending_tasks > 5:
                    insights.append(SystemInsight(
                        insight_type='maintenance',
                        message=f"有 {pending_tasks} 个待处理的维护任务",
                        level='medium',
                        recommendation='建议及时处理待维护任务',
                        evidence={'pending_tasks': pending_tasks}
                    ))
        except Exception as e:
            logger.error(f"[自学习系统] 生成系统健康洞察失败: {str(e)}")
        
        return insights
    
    def _generate_ai_empowerment_insights(self) -> List[SystemInsight]:
        """生成AI赋能洞察"""
        insights = []
        
        ai_data = self.learning_data.get('ai_performance', {})
        perf_by_type = ai_data.get('performance_by_type', {})
        
        if perf_by_type:
            avg_success_rate = sum(m['success_rate'] for m in perf_by_type.values()) / len(perf_by_type)
            
            if avg_success_rate > 90:
                insights.append(SystemInsight(
                    insight_type='ai_empowerment',
                    message=f"AI员工整体成功率 {round(avg_success_rate, 1)}%，表现优秀",
                    level='low',
                    recommendation='考虑扩展AI员工能力范围或增加新类型AI员工',
                    evidence={'avg_success_rate': round(avg_success_rate, 1), 'ai_count': ai_data.get('ai_count', 0)}
                ))
            elif avg_success_rate < 70:
                insights.append(SystemInsight(
                    insight_type='ai_empowerment',
                    message=f"AI员工整体成功率 {round(avg_success_rate, 1)}%，需要改进",
                    level='high',
                    recommendation='建议优化AI员工配置，增加训练数据，或调整模型参数',
                    evidence={'avg_success_rate': round(avg_success_rate, 1), 'ai_count': ai_data.get('ai_count', 0)}
                ))
        
        return insights
    
    def persist_learning(self):
        """持久化学习数据"""
        try:
            with sqlite3.connect(DATABASE_PATH) as conn:
                cursor = conn.cursor()
                
                for pattern in self.patterns[-5:]:
                    cursor.execute('''
                        INSERT OR IGNORE INTO learning_patterns 
                        (pattern_type, pattern_data, confidence, detected_at, insights)
                        VALUES (?, ?, ?, ?, ?)
                    ''', (
                        pattern.pattern_type,
                        json.dumps(pattern.data),
                        pattern.confidence,
                        pattern.detected_at.isoformat(),
                        json.dumps(pattern.insights)
                    ))
                
                for insight in self.insights[-5:]:
                    cursor.execute('''
                        INSERT OR IGNORE INTO system_insights 
                        (insight_type, message, level, recommendation, evidence, created_at, applied)
                        VALUES (?, ?, ?, ?, ?, ?, ?)
                    ''', (
                        insight.insight_type,
                        insight.message,
                        insight.level,
                        insight.recommendation,
                        json.dumps(insight.evidence),
                        insight.created_at.isoformat(),
                        1 if insight.applied else 0
                    ))
                
                conn.commit()
        except Exception as e:
            logger.error(f"[自学习系统] 持久化学习数据失败: {str(e)}")
    
    def apply_insight(self, insight_id: int) -> bool:
        """应用洞察建议"""
        try:
            with sqlite3.connect(DATABASE_PATH) as conn:
                cursor = conn.cursor()
                
                cursor.execute('''
                    SELECT * FROM system_insights WHERE id = ?
                ''', (insight_id,))
                insight = cursor.fetchone()
                
                if not insight:
                    return False
                
                cursor.execute('''
                    UPDATE system_insights SET applied = 1 WHERE id = ?
                ''', (insight_id,))
                conn.commit()
                
                logger.info(f"[自学习系统] 已应用洞察: {insight['message']}")
                return True
        except Exception as e:
            logger.error(f"[自学习系统] 应用洞察失败: {str(e)}")
            return False
    
    def analyze_system(self) -> Dict[str, Any]:
        """分析系统状态"""
        return {
            'status': 'running' if self._is_learning else 'stopped',
            'analysis': self._perform_comprehensive_analysis(),
            'patterns_detected': len(self.patterns),
            'insights_generated': len(self.insights),
            'learning_history_length': len(self.learning_history),
            'last_learning_time': self.learning_history[-1]['timestamp'] if self.learning_history else None
        }
    
    def _perform_comprehensive_analysis(self) -> Dict[str, Any]:
        """执行综合分析"""
        analysis = {
            'performance': self._analyze_performance(),
            'resource_usage': self._analyze_resource_usage(),
            'user_activity': self._analyze_user_activity(),
            'ai_performance': self._analyze_ai_performance(),
            'recommendations': self._generate_recommendations()
        }
        return analysis
    
    def _analyze_performance(self) -> Dict[str, Any]:
        """分析性能"""
        perf_data = self.learning_data.get('system', {})
        thresholds = self.knowledge_base['performance_thresholds']
        
        status = 'healthy'
        if perf_data.get('cpu_percent', 0) >= thresholds['cpu_warning']:
            status = 'warning'
        if perf_data.get('cpu_percent', 0) >= thresholds['cpu_critical']:
            status = 'critical'
        
        return {
            'status': status,
            'cpu_percent': perf_data.get('cpu_percent', 0),
            'memory_percent': perf_data.get('memory_percent', 0),
            'disk_percent': perf_data.get('disk_percent', 0)
        }
    
    def _analyze_resource_usage(self) -> Dict[str, Any]:
        """分析资源使用"""
        perf_data = self.learning_data.get('system', {})
        
        memory_status = 'optimal'
        if perf_data.get('memory_percent', 0) > 70:
            memory_status = 'high'
        if perf_data.get('memory_percent', 0) > 85:
            memory_status = 'critical'
        
        return {
            'memory_status': memory_status,
            'memory_available_mb': perf_data.get('memory_available', 0),
            'disk_used_gb': perf_data.get('disk_used', 0),
            'network_traffic_mb': {
                'sent': perf_data.get('network_sent', 0),
                'received': perf_data.get('network_recv', 0)
            }
        }
    
    def _analyze_user_activity(self) -> Dict[str, Any]:
        """分析用户活动"""
        user_data = self.learning_data.get('user_activity', {})
        
        activity_level = 'low'
        active_users = user_data.get('active_users', 0)
        if active_users > 50:
            activity_level = 'medium'
        if active_users > 100:
            activity_level = 'high'
        
        return {
            'activity_level': activity_level,
            'active_users': active_users,
            'exam_count_today': user_data.get('exam_count_today', 0),
            'learning_count_today': user_data.get('learning_count_today', 0),
            'role_distribution': user_data.get('role_distribution', {})
        }
    
    def _analyze_ai_performance(self) -> Dict[str, Any]:
        """分析AI性能"""
        ai_data = self.learning_data.get('ai_performance', {})
        perf_by_type = ai_data.get('performance_by_type', {})
        
        if not perf_by_type:
            return {'status': 'no_data', 'ai_count': ai_data.get('ai_count', 0)}
        
        avg_success = sum(m['success_rate'] for m in perf_by_type.values()) / len(perf_by_type)
        
        status = 'excellent' if avg_success >= 90 else 'good' if avg_success >= 70 else 'needs_improvement'
        
        return {
            'status': status,
            'ai_count': ai_data.get('ai_count', 0),
            'avg_success_rate': round(avg_success, 1),
            'performance_by_type': perf_by_type
        }
    
    def _generate_recommendations(self) -> List[str]:
        """生成综合建议"""
        recommendations = []
        
        perf = self.learning_data.get('system', {})
        if perf.get('memory_percent', 0) > 80:
            recommendations.append('考虑增加系统内存或优化内存使用')
        
        ai_data = self.learning_data.get('ai_performance', {})
        perf_by_type = ai_data.get('performance_by_type', {})
        if perf_by_type:
            avg_success = sum(m['success_rate'] for m in perf_by_type.values()) / len(perf_by_type)
            if avg_success < 70:
                recommendations.append('建议优化AI员工配置以提高成功率')
        
        if not recommendations:
            recommendations.append('系统运行正常，暂无特殊建议')
        
        return recommendations
    
    def get_insights(self, limit: int = 10, level: str = None) -> List[Dict[str, Any]]:
        """获取系统洞察"""
        try:
            with sqlite3.connect(DATABASE_PATH) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                
                query = 'SELECT * FROM system_insights'
                params = []
                
                if level:
                    query += ' WHERE level = ?'
                    params.append(level)
                
                query += ' ORDER BY created_at DESC LIMIT ?'
                params.append(limit)
                
                cursor.execute(query, params)
                insights = []
                
                for row in cursor.fetchall():
                    insights.append({
                        'id': row['id'],
                        'insight_type': row['insight_type'],
                        'message': row['message'],
                        'level': row['level'],
                        'recommendation': row['recommendation'],
                        'evidence': json.loads(row['evidence']),
                        'created_at': row['created_at'],
                        'applied': bool(row['applied'])
                    })
                
                return insights
        except Exception as e:
            logger.error(f"[自学习系统] 获取洞察失败: {str(e)}")
            return [i.to_dict() for i in self.insights[-limit:]]
    
    def get_patterns(self, limit: int = 10) -> List[Dict[str, Any]]:
        """获取检测到的模式"""
        try:
            with sqlite3.connect(DATABASE_PATH) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                
                cursor.execute('''
                    SELECT * FROM learning_patterns 
                    ORDER BY detected_at DESC LIMIT ?
                ''', (limit,))
                
                patterns = []
                for row in cursor.fetchall():
                    patterns.append({
                        'id': row['id'],
                        'pattern_type': row['pattern_type'],
                        'pattern_data': json.loads(row['pattern_data']),
                        'confidence': row['confidence'],
                        'detected_at': row['detected_at'],
                        'insights': json.loads(row['insights'])
                    })
                
                return patterns
        except Exception as e:
            logger.error(f"[自学习系统] 获取模式失败: {str(e)}")
            return [p.to_dict() for p in self.patterns[-limit:]]
    
    def learn_from_data(self, data: Dict[str, Any]):
        """从外部数据学习"""
        with self._lock:
            learning_type = data.get('type', 'custom')
            
            if learning_type == 'user_feedback':
                self._learn_from_feedback(data)
            elif learning_type == 'system_event':
                self._learn_from_event(data)
            elif learning_type == 'performance_data':
                self._learn_from_performance(data)
            
            self.learning_history.append({
                'timestamp': datetime.now().isoformat(),
                'learning_type': learning_type,
                'data': data
            })
    
    def _learn_from_feedback(self, data: Dict[str, Any]):
        """从用户反馈学习"""
        feedback_type = data.get('feedback_type', '')
        score = data.get('score', 0)
        
        if feedback_type == 'feature_rating' and score < 3:
            insight = SystemInsight(
                insight_type='user_experience',
                message=f"功能评分较低: {data.get('feature_name', '')} - {score}/5",
                level='medium',
                recommendation='建议改进该功能的用户体验',
                evidence=data
            )
            self.insights.append(insight)
    
    def _learn_from_event(self, data: Dict[str, Any]):
        """从系统事件学习"""
        event_type = data.get('event_type', '')
        
        if event_type == 'error':
            insight = SystemInsight(
                insight_type='system_health',
                message=f"系统错误: {data.get('error_message', '')}",
                level='high',
                recommendation='建议排查错误原因',
                evidence=data
            )
            self.insights.append(insight)
    
    def _learn_from_performance(self, data: Dict[str, Any]):
        """从性能数据学习"""
        metric = data.get('metric', '')
        value = data.get('value', 0)
        threshold = data.get('threshold', 0)
        
        if value > threshold:
            insight = SystemInsight(
                insight_type='performance',
                message=f"{metric}超过阈值: {value} > {threshold}",
                level='high',
                recommendation='建议优化该性能指标',
                evidence=data
            )
            self.insights.append(insight)
    
    def get_performance_metrics(self) -> Dict[str, Any]:
        """获取性能指标"""
        try:
            with sqlite3.connect(DATABASE_PATH) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                
                cursor.execute('''
                    SELECT metric_name, AVG(metric_value) as avg_value, 
                           MAX(metric_value) as max_value, MIN(metric_value) as min_value
                    FROM performance_metrics 
                    WHERE timestamp >= ?
                    GROUP BY metric_name
                ''', ((datetime.now() - timedelta(hours=24)).isoformat(),))
                
                metrics = {}
                for row in cursor.fetchall():
                    metrics[row['metric_name']] = {
                        'avg': round(row['avg_value'], 2),
                        'max': round(row['max_value'], 2),
                        'min': round(row['min_value'], 2)
                    }
                
                return metrics
        except Exception as e:
            logger.error(f"[自学习系统] 获取性能指标失败: {str(e)}")
            return {
                'cpu_usage': self.learning_data.get('system', {}).get('cpu_percent', 0),
                'memory_usage': self.learning_data.get('system', {}).get('memory_percent', 0),
                'response_time': 0
            }
    
    def get_knowledge_summary(self) -> Dict[str, Any]:
        """获取知识库摘要"""
        return {
            'performance_thresholds': self.knowledge_base['performance_thresholds'],
            'known_patterns': list(self.knowledge_base['patterns'].keys()),
            'optimization_rules': list(self.knowledge_base['optimization_rules'].keys()),
            'patterns_detected': len(self.patterns),
            'insights_generated': len(self.insights),
            'learning_cycles': len(self.learning_history)
        }

self_learning_system = SelfLearningSystem()