# -*- coding: utf-8 -*-
#!/usr/bin/env python3
"""
防作弊增强服务模块
提供答题行为监控、切屏检测、时间异常检测等高级防作弊功能
"""

import json
import time
import math
from datetime import datetime, timezone
from typing import Dict, List, Optional, Any, Tuple
from collections import defaultdict
from dataclasses import dataclass, field
import logging
import sqlite3

logger = logging.getLogger(__name__)


@dataclass
class BehaviorEvent:
    """行为事件数据结构"""
    event_type: str  # 事件类型: answer, switch_tab, focus_loss, mouse_leave, etc.
    timestamp: datetime  # 事件时间
    question_id: Optional[str] = None  # 相关题目ID
    details: Dict[str, Any] = field(default_factory=dict)  # 事件详情
    suspicion_level: float = 0.0  # 可疑程度 (0-1)


@dataclass
class CheatingDetectionResult:
    """作弊检测结果"""
    is_cheating: bool = False
    cheating_type: str = ""  # 作弊类型
    confidence: float = 0.0  # 确信度 (0-1)
    evidence: List[Dict] = field(default_factory=list)  # 证据列表
    risk_level: str = "low"  # 风险等级: low, medium, high, critical
    recommendation: str = ""  # 处理建议


class AntiCheatingService:
    """防作弊增强服务"""
    
    # 可疑行为阈值配置
    THRESHOLDS = {
        'switch_tab_count': 3,  # 切屏次数阈值
        'switch_tab_time_threshold': 2.0,  # 切屏时间阈值(秒)
        'focus_loss_count': 5,  # 失焦次数阈值
        'mouse_leave_count': 10,  # 鼠标离开次数阈值
        'answer_time_abnormal_ratio': 0.5,  # 答题时间异常比例阈值
        'rapid_answer_threshold': 3,  # 快速答题阈值(秒)
        'pattern_similarity_threshold': 0.8,  # 答题模式相似度阈值
        'idle_time_threshold': 60,  # 空闲时间阈值(秒)
        'total_suspicion_threshold': 0.7,  # 总可疑度阈值
    }
    
    # 风险等级映射
    RISK_LEVELS = {
        'low': {'min': 0.0, 'max': 0.3, 'label': '低风险'},
        'medium': {'min': 0.3, 'max': 0.6, 'label': '中风险'},
        'high': {'min': 0.6, 'max': 0.85, 'label': '高风险'},
        'critical': {'min': 0.85, 'max': 1.0, 'label': '严重风险'}
    }
    
    def __init__(self, db_path="app.db"):
        """初始化防作弊服务"""
        self.db_path = db_path
        self._init_tables()
        logger.info("防作弊增强服务初始化完成")
    
    def _connect(self):
        """获取数据库连接"""
        return sqlite3.connect(self.db_path)
    
    def _init_tables(self):
        """初始化防作弊相关表"""
        try:
            with self._connect() as conn:
                cursor = conn.cursor()
                
                # 答题行为记录表
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS exam_behavior_logs (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        session_id TEXT NOT NULL,
                        user_id TEXT NOT NULL,
                        exam_id TEXT NOT NULL,
                        event_type TEXT NOT NULL,
                        event_time TIMESTAMP NOT NULL,
                        question_id TEXT,
                        details TEXT,
                        suspicion_level REAL DEFAULT 0.0,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        FOREIGN KEY (session_id) REFERENCES exam_sessions(id)
                    )
                ''')
                
                # 切屏检测记录表
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS screen_switch_logs (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        session_id TEXT NOT NULL,
                        user_id TEXT NOT NULL,
                        switch_type TEXT NOT NULL,
                        switch_time TIMESTAMP NOT NULL,
                        return_time TIMESTAMP,
                        duration REAL DEFAULT 0.0,
                        details TEXT,
                        suspicion_score REAL DEFAULT 0.0,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                ''')
                
                # 时间异常检测记录表
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS time_anomaly_logs (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        session_id TEXT NOT NULL,
                        user_id TEXT NOT NULL,
                        anomaly_type TEXT NOT NULL,
                        detected_time TIMESTAMP NOT NULL,
                        expected_value REAL,
                        actual_value REAL,
                        deviation REAL,
                        details TEXT,
                        severity REAL DEFAULT 0.0,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                ''')
                
                # 作弊检测结果汇总表
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS cheating_detection_results (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        session_id TEXT NOT NULL,
                        user_id TEXT NOT NULL,
                        exam_id TEXT NOT NULL,
                        is_cheating BOOLEAN DEFAULT FALSE,
                        cheating_type TEXT,
                        confidence REAL DEFAULT 0.0,
                        risk_level TEXT DEFAULT 'low',
                        evidence TEXT,
                        recommendation TEXT,
                        detected_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        reviewed BOOLEAN DEFAULT FALSE,
                        reviewer_id TEXT,
                        review_result TEXT,
                        reviewed_at TIMESTAMP
                    )
                ''')
                
                # 答题模式分析表
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS answer_pattern_analysis (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        session_id TEXT NOT NULL,
                        user_id TEXT NOT NULL,
                        pattern_type TEXT NOT NULL,
                        pattern_data TEXT,
                        similarity_score REAL DEFAULT 0.0,
                        baseline_pattern TEXT,
                        deviation_score REAL DEFAULT 0.0,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                ''')
                
                conn.commit()
                logger.info("防作弊数据表初始化完成")
        except Exception as e:
            logger.error(f"初始化防作弊数据表失败: {str(e)}")
    
    def record_behavior_event(
        self,
        session_id: str,
        user_id: str,
        exam_id: str,
        event_type: str,
        question_id: Optional[str] = None,
        details: Optional[Dict] = None
    ) -> Dict:
        """
        记录答题行为事件
        
        Args:
            session_id: 考试会话ID
            user_id: 用户ID
            exam_id: 考试ID
            event_type: 事件类型 (answer, view_question, switch_tab, focus_loss, etc.)
            question_id: 相关题目ID
            details: 事件详情
        
        Returns:
            记录结果
        """
        try:
            # 计算可疑程度
            suspicion_level = self._calculate_event_suspicion(event_type, details)
            
            event_time = datetime.now(timezone.utc)
            
            with self._connect() as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    INSERT INTO exam_behavior_logs 
                    (session_id, user_id, exam_id, event_type, event_time, question_id, details, suspicion_level)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    session_id, user_id, exam_id, event_type, event_time.isoformat(),
                    question_id, json.dumps(details or {}), suspicion_level
                ))
                
                log_id = cursor.lastrowid
                conn.commit()
            
            logger.info(f"记录行为事件: {event_type}, 可疑度: {suspicion_level}")
            
            return {
                'success': True,
                'log_id': log_id,
                'suspicion_level': suspicion_level,
                'event_type': event_type
            }
            
        except Exception as e:
            logger.error(f"记录行为事件失败: {str(e)}")
            return {'success': False, 'error': str(e)}
    
    def _calculate_event_suspicion(self, event_type: str, details: Optional[Dict]) -> float:
        """计算事件可疑程度"""
        suspicion_map = {
            'answer': 0.0,  # 正常答题
            'view_question': 0.0,  # 查看题目
            'switch_tab': 0.7,  # 切屏 - 高可疑
            'focus_loss': 0.5,  # 失焦 - 中可疑
            'mouse_leave': 0.3,  # 鼠标离开 - 低可疑
            'keyboard_special': 0.6,  # 特殊键盘操作
            'copy_attempt': 0.9,  # 尝试复制 - 高可疑
            'paste_attempt': 0.9,  # 尝试粘贴 - 高可疑
            'devtools_open': 0.95,  # 打开开发者工具 - 极高可疑
            'print_attempt': 0.8,  # 尝试打印
            'idle_timeout': 0.4,  # 空闲超时
        }
        
        base_suspicion = suspicion_map.get(event_type, 0.0)
        
        # 根据详情调整可疑程度
        if details:
            # 如果切屏时间过长，增加可疑度
            if event_type == 'switch_tab' and 'duration' in details:
                duration = details['duration']
                if duration > self.THRESHOLDS['switch_tab_time_threshold']:
                    base_suspicion += 0.1 * min(duration / 10, 0.3)
            
            # 如果快速答题，增加可疑度
            if event_type == 'answer' and 'time_spent' in details:
                time_spent = details['time_spent']
                if time_spent < self.THRESHOLDS['rapid_answer_threshold']:
                    base_suspicion = 0.5
        
        return min(1.0, base_suspicion)
    
    def detect_screen_switch(
        self,
        session_id: str,
        user_id: str,
        switch_type: str = "tab_switch",
        return_time: Optional[datetime] = None
    ) -> Dict:
        """
        检测切屏行为
        
        Args:
            session_id: 会话ID
            user_id: 用户ID
            switch_type: 切屏类型 (tab_switch, window_switch, app_switch)
            return_time: 返回时间
        
        Returns:
            检测结果
        """
        try:
            switch_time = datetime.now(timezone.utc)
            duration = 0.0
            
            if return_time:
                duration = (return_time - switch_time).total_seconds()
            
            # 计算可疑分数
            suspicion_score = self._calculate_switch_suspicion(session_id, switch_type, duration)
            
            with self._connect() as conn:
                cursor = conn.cursor()
                
                # 记录切屏事件
                cursor.execute('''
                    INSERT INTO screen_switch_logs 
                    (session_id, user_id, switch_type, switch_time, return_time, duration, suspicion_score)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                ''', (
                    session_id, user_id, switch_type, switch_time.isoformat(),
                    return_time.isoformat() if return_time else None,
                    duration, suspicion_score
                ))
                
                log_id = cursor.lastrowid
                
                # 统计切屏次数
                cursor.execute('''
                    SELECT COUNT(*), AVG(suspicion_score) FROM screen_switch_logs 
                    WHERE session_id = ?
                ''', (session_id,))
                
                count, avg_suspicion = cursor.fetchone()
                
                conn.commit()
            
            # 判断是否超过阈值
            is_suspicious = count >= self.THRESHOLDS['switch_tab_count'] or \
                           avg_suspicion > self.THRESHOLDS['total_suspicion_threshold']
            
            result = {
                'success': True,
                'log_id': log_id,
                'switch_count': count,
                'avg_suspicion': avg_suspicion or 0.0,
                'is_suspicious': is_suspicious,
                'suspicion_score': suspicion_score,
                'duration': duration
            }
            
            # 如果可疑，记录行为事件
            if is_suspicious:
                self.record_behavior_event(
                    session_id, user_id, '', 'switch_tab',
                    details={'count': count, 'avg_suspicion': avg_suspicion}
                )
            
            logger.info(f"切屏检测: 次数 {count}, 可疑度 {suspicion_score}")
            
            return result
            
        except Exception as e:
            logger.error(f"切屏检测失败: {str(e)}")
            return {'success': False, 'error': str(e)}
    
    def _calculate_switch_suspicion(self, session_id: str, switch_type: str, duration: float) -> float:
        """计算切屏可疑分数"""
        # 基础可疑分数
        base_scores = {
            'tab_switch': 0.3,
            'window_switch': 0.4,
            'app_switch': 0.5,
            'browser_close': 0.8
        }
        
        score = base_scores.get(switch_type, 0.3)
        
        # 根据时长调整
        if duration > self.THRESHOLDS['switch_tab_time_threshold']:
            score += 0.1 * min(duration / 5, 0.4)
        
        # 查询历史切屏次数
        try:
            with self._connect() as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    SELECT COUNT(*) FROM screen_switch_logs WHERE session_id = ?
                ''', (session_id,))
                count = cursor.fetchone()[0]
                
                # 次数越多，可疑度越高
                if count > 0:
                    score += 0.1 * min(count, 0.4)
        except Exception:
            pass
        
        return min(1.0, score)
    
    def detect_time_anomaly(
        self,
        session_id: str,
        user_id: str,
        anomaly_type: str,
        expected_value: float,
        actual_value: float
    ) -> Dict:
        """
        检测时间异常
        
        Args:
            session_id: 会话ID
            user_id: 用户ID
            anomaly_type: 异常类型 (answer_time, total_time, idle_time, etc.)
            expected_value: 期望值
            actual_value: 实际值
        
        Returns:
            检测结果
        """
        try:
            # 计算偏差
            if expected_value > 0:
                deviation = abs(actual_value - expected_value) / expected_value
            else:
                deviation = abs(actual_value - expected_value)
            
            # 计算严重程度
            severity = self._calculate_anomaly_severity(anomaly_type, deviation)
            
            detected_time = datetime.now(timezone.utc)
            
            details = {
                'expected': expected_value,
                'actual': actual_value,
                'deviation_percent': deviation * 100
            }
            
            with self._connect() as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    INSERT INTO time_anomaly_logs 
                    (session_id, user_id, anomaly_type, detected_time, expected_value, actual_value, 
                     deviation, details, severity)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    session_id, user_id, anomaly_type, detected_time.isoformat(),
                    expected_value, actual_value, deviation, json.dumps(details), severity
                ))
                
                log_id = cursor.lastrowid
                conn.commit()
            
            result = {
                'success': True,
                'log_id': log_id,
                'anomaly_type': anomaly_type,
                'deviation': deviation,
                'severity': severity,
                'is_anomaly': severity > 0.5
            }
            
            logger.info(f"时间异常检测: {anomaly_type}, 偏差 {deviation:.2%}, 严重度 {severity}")
            
            return result
            
        except Exception as e:
            logger.error(f"时间异常检测失败: {str(e)}")
            return {'success': False, 'error': str(e)}
    
    def _calculate_anomaly_severity(self, anomaly_type: str, deviation: float) -> float:
        """计算异常严重程度"""
        # 不同异常类型的严重程度计算
        severity_config = {
            'answer_time': {
                'too_fast': 0.8,  # 答题太快
                'too_slow': 0.3,  # 答题太慢
                'threshold': 0.5
            },
            'total_time': {
                'threshold': 0.3
            },
            'idle_time': {
                'threshold': 0.6
            },
            'submission_time': {
                'threshold': 0.4
            }
        }
        
        config = severity_config.get(anomaly_type, {'threshold': 0.5})
        threshold = config.get('threshold', 0.5)
        
        if anomaly_type == 'answer_time':
            # 如果是答题时间，检查是太快还是太慢
            if deviation > config.get('too_fast', 0.8):
                return 0.9  # 极可疑
            elif deviation > threshold:
                return deviation
        
        # 一般情况：偏差越大，严重程度越高
        if deviation > threshold:
            return min(1.0, deviation)
        else:
            return deviation * 0.5
    
    def analyze_answer_pattern(
        self,
        session_id: str,
        user_id: str,
        answers: Dict[str, Any]
    ) -> Dict:
        """
        分析答题模式
        
        Args:
            session_id: 会话ID
            user_id: 用户ID
            answers: 答题数据
        
        Returns:
            分析结果
        """
        try:
            # 分析答题模式特征
            pattern_features = self._extract_pattern_features(answers)
            
            # 获取用户历史答题模式作为基准
            baseline_pattern = self._get_user_baseline_pattern(user_id)
            
            # 计算相似度和偏差
            similarity = self._calculate_pattern_similarity(pattern_features, baseline_pattern)
            deviation = 1.0 - similarity
            
            pattern_type = self._classify_pattern_type(pattern_features)
            
            with self._connect() as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    INSERT INTO answer_pattern_analysis 
                    (session_id, user_id, pattern_type, pattern_data, similarity_score, 
                     baseline_pattern, deviation_score)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                ''', (
                    session_id, user_id, pattern_type, json.dumps(pattern_features),
                    similarity, json.dumps(baseline_pattern), deviation
                ))
                
                analysis_id = cursor.lastrowid
                conn.commit()
            
            # 判断是否可疑
            is_suspicious = similarity < self.THRESHOLDS['pattern_similarity_threshold']
            
            result = {
                'success': True,
                'analysis_id': analysis_id,
                'pattern_type': pattern_type,
                'similarity': similarity,
                'deviation': deviation,
                'is_suspicious': is_suspicious,
                'pattern_features': pattern_features
            }
            
            logger.info(f"答题模式分析: 类型 {pattern_type}, 相似度 {similarity:.2f}")
            
            return result
            
        except Exception as e:
            logger.error(f"答题模式分析失败: {str(e)}")
            return {'success': False, 'error': str(e)}
    
    def _extract_pattern_features(self, answers: Dict[str, Any]) -> Dict:
        """提取答题模式特征"""
        features = {
            'total_questions': len(answers),
            'answer_times': [],
            'answer_sequence': [],
            'option_distribution': defaultdict(int),
            'difficulty_correlation': [],
            'time_distribution': []
        }
        
        for q_id, answer_data in answers.items():
            if isinstance(answer_data, dict):
                # 答题时间
                time_spent = answer_data.get('time_spent', 0)
                features['answer_times'].append(time_spent)
                
                # 答题顺序
                features['answer_sequence'].append(q_id)
                
                # 选项分布（选择题）
                answer = answer_data.get('answer', '')
                if isinstance(answer, str) and len(answer) == 1:
                    features['option_distribution'][answer] += 1
                
                # 题目难度与答题时间关联
                difficulty = answer_data.get('difficulty', 3)
                features['difficulty_correlation'].append({
                    'difficulty': difficulty,
                    'time': time_spent
                })
        
        # 计算统计特征
        if features['answer_times']:
            features['avg_answer_time'] = sum(features['answer_times']) / len(features['answer_times'])
            features['std_answer_time'] = math.sqrt(
                sum((t - features['avg_answer_time'])**2 for t in features['answer_times']) / 
                len(features['answer_times'])
            )
        
        features['option_distribution'] = dict(features['option_distribution'])
        
        return features
    
    def _get_user_baseline_pattern(self, user_id: str) -> Dict:
        """获取用户历史答题模式基准"""
        try:
            with self._connect() as conn:
                cursor = conn.cursor()
                # 获取用户最近的答题模式分析
                cursor.execute('''
                    SELECT pattern_data FROM answer_pattern_analysis 
                    WHERE user_id = ? AND similarity_score > 0.7
                    ORDER BY created_at DESC LIMIT 5
                ''', (user_id,))
                
                patterns = cursor.fetchall()
                
                if patterns:
                    # 合并历史模式
                    baseline = {}
                    for pattern_json in patterns:
                        pattern = json.loads(pattern_json[0])
                        for key, value in pattern.items():
                            if key not in baseline:
                                baseline[key] = []
                            if isinstance(value, list):
                                baseline[key].extend(value)
                            elif isinstance(value, (int, float)):
                                baseline[key].append(value)
                    
                    return baseline
                
                return {}
        except Exception:
            return {}
    
    def _calculate_pattern_similarity(self, current: Dict, baseline: Dict) -> float:
        """计算模式相似度"""
        if not baseline:
            return 1.0  # 没有基准数据时，不判断可疑
        
        similarity_scores = []
        
        # 比较平均答题时间
        if 'avg_answer_time' in current and 'avg_answer_time' in baseline:
            current_avg = current['avg_answer_time']
            baseline_avg = sum(baseline['avg_answer_time']) / len(baseline['avg_answer_time'])
            time_similarity = 1.0 - abs(current_avg - baseline_avg) / max(current_avg, baseline_avg, 1)
            similarity_scores.append(time_similarity)
        
        # 比较选项分布
        if 'option_distribution' in current and baseline.get('option_distribution'):
            current_dist = current['option_distribution']
            baseline_dist = baseline['option_distribution']
            
            # 计算选项分布相似度
            common_options = set(current_dist.keys()) & set(baseline_dist.keys())
            if common_options:
                option_similarity = sum(
                    min(current_dist.get(o, 0), baseline_dist.get(o, 0)) /
                    max(current_dist.get(o, 0), baseline_dist.get(o, 0), 1)
                    for o in common_options
                ) / len(common_options)
                similarity_scores.append(option_similarity)
        
        # 计算综合相似度
        if similarity_scores:
            return sum(similarity_scores) / len(similarity_scores)
        return 0.8
    
    def _classify_pattern_type(self, features: Dict) -> str:
        """分类答题模式类型"""
        avg_time = features.get('avg_answer_time', 0)
        std_time = features.get('std_answer_time', 0)
        
        if avg_time < 5:
            return 'rapid_answer'  # 快速答题
        elif std_time < 2:
            return 'consistent'  # 答题时间一致
        elif avg_time > 60:
            return 'slow_answer'  # 慢速答题
        else:
            return 'normal'  # 正常模式
    
    def perform_comprehensive_detection(
        self,
        session_id: str,
        user_id: str,
        exam_id: str
    ) -> CheatingDetectionResult:
        """
        执行综合作弊检测
        
        Args:
            session_id: 会话ID
            user_id: 用户ID
            exam_id: 考试ID
        
        Returns:
            作弊检测结果
        """
        try:
            result = CheatingDetectionResult()
            
            # 收集所有可疑证据
            evidence = []
            total_suspicion = 0.0
            
            # 1. 检查行为日志
            with self._connect() as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    SELECT event_type, COUNT(*), AVG(suspicion_level) 
                    FROM exam_behavior_logs 
                    WHERE session_id = ? AND suspicion_level > 0.3
                    GROUP BY event_type
                ''', (session_id,))
                
                behavior_evidence = cursor.fetchall()
                for event_type, count, avg_suspicion in behavior_evidence:
                    evidence.append({
                        'type': 'behavior',
                        'event_type': event_type,
                        'count': count,
                        'avg_suspicion': avg_suspicion
                    })
                    total_suspicion += avg_suspicion * count
            
            # 2. 检查切屏记录
            cursor.execute('''
                SELECT COUNT(*), AVG(suspicion_score), MAX(duration) 
                FROM screen_switch_logs WHERE session_id = ?
            ''', (session_id,))
            
            switch_data = cursor.fetchone()
            if switch_data and switch_data[0] > 0:
                switch_count, avg_suspicion, max_duration = switch_data
                if switch_count >= self.THRESHOLDS['switch_tab_count']:
                    evidence.append({
                        'type': 'screen_switch',
                        'count': switch_count,
                        'avg_suspicion': avg_suspicion or 0,
                        'max_duration': max_duration or 0
                    })
                    total_suspicion += (avg_suspicion or 0) * switch_count
            
            # 3. 检查时间异常
            cursor.execute('''
                SELECT anomaly_type, COUNT(*), AVG(severity) 
                FROM time_anomaly_logs WHERE session_id = ? AND severity > 0.5
                GROUP BY anomaly_type
            ''', (session_id,))
            
            time_evidence = cursor.fetchall()
            for anomaly_type, count, avg_severity in time_evidence:
                evidence.append({
                    'type': 'time_anomaly',
                    'anomaly_type': anomaly_type,
                    'count': count,
                    'avg_severity': avg_severity
                })
                total_suspicion += avg_severity * count
            
            # 4. 检查答题模式
            cursor.execute('''
                SELECT similarity_score, deviation_score 
                FROM answer_pattern_analysis WHERE session_id = ?
                ORDER BY created_at DESC LIMIT 1
            ''', (session_id,))
            
            pattern_data = cursor.fetchone()
            if pattern_data:
                similarity, deviation = pattern_data
                if similarity < self.THRESHOLDS['pattern_similarity_threshold']:
                    evidence.append({
                        'type': 'pattern_anomaly',
                        'similarity': similarity,
                        'deviation': deviation
                    })
                    total_suspicion += deviation
            
            # 计算综合可疑度
            if evidence:
                result.confidence = total_suspicion / len(evidence)
            else:
                result.confidence = 0.0
            
            # 确定作弊类型
            if result.confidence > self.THRESHOLDS['total_suspicion_threshold']:
                result.is_cheating = True
                
                # 根据主要证据判断作弊类型
                cheating_types = []
                for ev in evidence:
                    if ev['type'] == 'screen_switch':
                        cheating_types.append('screen_switch_cheating')
                    elif ev['type'] == 'behavior' and ev['event_type'] in ['copy_attempt', 'paste_attempt']:
                        cheating_types.append('copy_paste_cheating')
                    elif ev['type'] == 'pattern_anomaly':
                        cheating_types.append('answer_pattern_abnormal')
                    elif ev['type'] == 'time_anomaly':
                        cheating_types.append('time_anomaly')
                
                result.cheating_type = ', '.join(cheating_types) if cheating_types else 'unknown'
            
            # 确定风险等级
            for level, config in self.RISK_LEVELS.items():
                if config['min'] <= result.confidence <= config['max']:
                    result.risk_level = level
                    break
            
            # 生成处理建议
            result.recommendation = self._generate_recommendation(result)
            result.evidence = evidence
            
            # 保存检测结果
            self._save_detection_result(session_id, user_id, exam_id, result)
            
            logger.info(f"综合作弊检测: 可疑度 {result.confidence:.2f}, 风险等级 {result.risk_level}")
            
            return result
            
        except Exception as e:
            logger.error(f"综合作弊检测失败: {str(e)}")
            return CheatingDetectionResult(
                is_cheating=False,
                confidence=0.0,
                recommendation="检测失败，需要人工审核"
            )
    
    def _generate_recommendation(self, result: CheatingDetectionResult) -> str:
        """生成处理建议"""
        recommendations = {
            'low': '建议记录存档，暂不处理',
            'medium': '建议人工复核，关注后续行为',
            'high': '建议暂停考试，要求人工审核',
            'critical': '建议立即终止考试，标记作弊行为'
        }
        
        base_recommendation = recommendations.get(result.risk_level, '需要人工审核')
        
        # 根据作弊类型添加具体建议
        if 'screen_switch_cheating' in result.cheating_type:
            base_recommendation += '。注意切屏行为频繁，可能查看外部资料。'
        
        if 'answer_pattern_abnormal' in result.cheating_type:
            base_recommendation += '。答题模式异常，可能与历史行为不符。'
        
        if 'time_anomaly' in result.cheating_type:
            base_recommendation += '。答题时间异常，可能存在外部帮助。'
        
        return base_recommendation
    
    def _save_detection_result(
        self,
        session_id: str,
        user_id: str,
        exam_id: str,
        result: CheatingDetectionResult
    ):
        """保存检测结果"""
        try:
            with self._connect() as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    INSERT INTO cheating_detection_results 
                    (session_id, user_id, exam_id, is_cheating, cheating_type, confidence, 
                     risk_level, evidence, recommendation)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    session_id, user_id, exam_id, result.is_cheating, result.cheating_type,
                    result.confidence, result.risk_level, json.dumps(result.evidence),
                    result.recommendation
                ))
                conn.commit()
        except Exception as e:
            logger.error(f"保存检测结果失败: {str(e)}")
    
    def get_session_cheating_report(self, session_id: str) -> Dict:
        """获取会话作弊报告"""
        try:
            with self._connect() as conn:
                cursor = conn.cursor()
                
                # 获取检测结果
                cursor.execute('''
                    SELECT * FROM cheating_detection_results WHERE session_id = ?
                    ORDER BY detected_at DESC LIMIT 1
                ''', (session_id,))
                
                detection_result = cursor.fetchone()
                
                # 获取行为日志统计
                cursor.execute('''
                    SELECT event_type, COUNT(*), AVG(suspicion_level) 
                    FROM exam_behavior_logs WHERE session_id = ?
                    GROUP BY event_type
                ''', (session_id,))
                
                behavior_stats = cursor.fetchall()
                
                # 获取切屏统计
                cursor.execute('''
                    SELECT COUNT(*), AVG(duration), MAX(duration) 
                    FROM screen_switch_logs WHERE session_id = ?
                ''', (session_id,))
                
                switch_stats = cursor.fetchone()
                
                # 获取时间异常统计
                cursor.execute('''
                    SELECT anomaly_type, COUNT(*) FROM time_anomaly_logs 
                    WHERE session_id = ? GROUP BY anomaly_type
                ''', (session_id,))
                
                time_stats = cursor.fetchall()
                
                report = {
                    'session_id': session_id,
                    'detection_result': None,
                    'behavior_statistics': {},
                    'switch_statistics': {},
                    'time_anomaly_statistics': {}
                }
                
                if detection_result:
                    report['detection_result'] = {
                        'is_cheating': detection_result[3],
                        'cheating_type': detection_result[4],
                        'confidence': detection_result[5],
                        'risk_level': detection_result[6],
                        'recommendation': detection_result[8]
                    }
                
                for event_type, count, avg_suspicion in behavior_stats:
                    report['behavior_statistics'][event_type] = {
                        'count': count,
                        'avg_suspicion': avg_suspicion
                    }
                
                if switch_stats:
                    report['switch_statistics'] = {
                        'count': switch_stats[0],
                        'avg_duration': switch_stats[1],
                        'max_duration': switch_stats[2]
                    }
                
                for anomaly_type, count in time_stats:
                    report['time_anomaly_statistics'][anomaly_type] = count
                
                return report
                
        except Exception as e:
            logger.error(f"获取作弊报告失败: {str(e)}")
            return {'session_id': session_id, 'error': str(e)}
    
    def get_user_cheating_history(self, user_id: str, limit: int = 20) -> List[Dict]:
        """获取用户作弊历史"""
        try:
            with self._connect() as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    SELECT session_id, exam_id, is_cheating, cheating_type, confidence, 
                           risk_level, detected_at
                    FROM cheating_detection_results 
                    WHERE user_id = ?
                    ORDER BY detected_at DESC LIMIT ?
                ''', (user_id, limit))
                
                history = []
                for row in cursor.fetchall():
                    history.append({
                        'session_id': row[0],
                        'exam_id': row[1],
                        'is_cheating': row[2],
                        'cheating_type': row[3],
                        'confidence': row[4],
                        'risk_level': row[5],
                        'detected_at': row[6]
                    })
                
                return history
                
        except Exception as e:
            logger.error(f"获取作弊历史失败: {str(e)}")
            return []


# 全局实例
_anti_cheating_service = None

def get_anti_cheating_service(db_path="app.db") -> AntiCheatingService:
    """获取防作弊服务实例"""
    global _anti_cheating_service
    if _anti_cheating_service is None:
        _anti_cheating_service = AntiCheatingService(db_path)
    return _anti_cheating_service


if __name__ == "__main__":
    # 测试防作弊服务
    service = get_anti_cheating_service()
    
    print("=" * 60)
    print("防作弊增强服务测试")
    print("=" * 60)
    
    # 测试记录行为事件
    result = service.record_behavior_event(
        session_id="TEST_SESSION_001",
        user_id="USER_001",
        exam_id="EXAM_001",
        event_type="switch_tab",
        details={"duration": 5.0}
    )
    print(f"✓ 记录行为事件: {result}")
    
    # 测试切屏检测
    result = service.detect_screen_switch(
        session_id="TEST_SESSION_001",
        user_id="USER_001",
        switch_type="tab_switch"
    )
    print(f"✓ 切屏检测: {result}")
    
    # 测试时间异常检测
    result = service.detect_time_anomaly(
        session_id="TEST_SESSION_001",
        user_id="USER_001",
        anomaly_type="answer_time",
        expected_value=30.0,
        actual_value=2.0
    )
    print(f"✓ 时间异常检测: {result}")
    
    # 测试答题模式分析
    answers = {
        "Q1": {"answer": "A", "time_spent": 2},
        "Q2": {"answer": "A", "time_spent": 2},
        "Q3": {"answer": "A", "time_spent": 2}
    }
    result = service.analyze_answer_pattern(
        session_id="TEST_SESSION_001",
        user_id="USER_001",
        answers=answers
    )
    print(f"✓ 答题模式分析: {result}")
    
    # 测试综合作弊检测
    detection = service.perform_comprehensive_detection(
        session_id="TEST_SESSION_001",
        user_id="USER_001",
        exam_id="EXAM_001"
    )
    print(f"\n✓ 综合作弊检测:")
    print(f"  是否作弊: {detection.is_cheating}")
    print(f"  作弊类型: {detection.cheating_type}")
    print(f"  确信度: {detection.confidence:.2f}")
    print(f"  风险等级: {detection.risk_level}")
    print(f"  处理建议: {detection.recommendation}")
    
    # 获取作弊报告
    report = service.get_session_cheating_report("TEST_SESSION_001")
    print(f"\n✓ 作弊报告: {json.dumps(report, indent=2, ensure_ascii=False)}")
    
    logger.info("防作弊增强服务测试完成")