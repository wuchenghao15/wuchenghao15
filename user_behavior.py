#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
用户行为法则 - User Behavior Framework
MTSCOS AI Project v3.1
用户行为监控、异常检测和风险评估
"""

import os
import sys
import json
import sqlite3
import logging
import hashlib
import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field
from enum import Enum
import statistics

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('user_behavior.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger('user_behavior')

class BehaviorType(Enum):
    """行为类型"""
    LOGIN = "login"                      # 登录
    LOGOUT = "logout"                    # 登出
    DATA_ACCESS = "data_access"          # 数据访问
    FILE_DOWNLOAD = "file_download"      # 文件下载
    FILE_UPLOAD = "file_upload"         # 文件上传
    DATA_MODIFY = "data_modify"         # 数据修改
    DATA_DELETE = "data_delete"          # 数据删除
    SYSTEM_CONFIG = "system_config"      # 系统配置
    USER_MANAGEMENT = "user_management"  # 用户管理
    PERMISSION_CHANGE = "permission_change"  # 权限变更
    API_CALL = "api_call"              # API调用
    QUERY = "query"                    # 查询
    REPORT_GENERATION = "report_generation"  # 报告生成
    DATA_EXPORT = "data_export"         # 数据导出

class RiskLevel(Enum):
    """风险等级"""
    CRITICAL = "critical"    # 极高风险
    HIGH = "high"          # 高风险
    MEDIUM = "medium"      # 中等风险
    LOW = "low"            # 低风险
    NORMAL = "normal"     # 正常

class AnomalyType(Enum):
    """异常类型"""
    FREQUENCY_ANOMALY = "frequency_anomaly"        # 频率异常
    TIME_ANOMALY = "time_anomaly"                # 时间异常
    LOCATION_ANOMALY = "location_anomaly"        # 位置异常
    PATTERN_ANOMALY = "pattern_anomaly"          # 模式异常
    VOLUME_ANOMALY = "volume_anomaly"            # 数量异常
    SEQUENCE_ANOMALY = "sequence_anomaly"        # 顺序异常
    DATA_ANOMALY = "data_anomaly"              # 数据异常

class ActionType(Enum):
    """动作类型"""
    ALLOW = "allow"              # 允许
    BLOCK = "block"             # 阻止
    WARN = "warn"               # 警告
    MONITOR = "monitor"         # 监控
    INVESTIGATE = "investigate"  # 调查
    LOCK = "lock"               # 锁定
    NOTIFY = "notify"           # 通知

@dataclass
class UserProfile:
    """用户画像"""
    user_id: str
    username: str
    department: str = ""
    role: str = ""
    access_level: int = 1
    first_activity: str = None
    last_activity: str = None
    total_sessions: int = 0
    avg_session_duration: float = 0.0
    avg_activity_per_day: float = 0.0
    common_access_times: List[str] = field(default_factory=list)
    common_locations: List[str] = field(default_factory=list)
    common_resources: List[str] = field(default_factory=list)
    behavior_patterns: Dict[str, Any] = field(default_factory=dict)
    risk_score: float = 0.0
    risk_level: RiskLevel = RiskLevel.NORMAL
    last_evaluated: str = None

@dataclass
class BehaviorEvent:
    """行为事件"""
    event_id: str
    user_id: str
    username: str
    behavior_type: BehaviorType
    timestamp: str
    ip_address: str
    location: str = ""
    resource: str = ""
    action: str = ""
    result: str = "success"
    duration: float = 0.0
    metadata: Dict[str, Any] = field(default_factory=dict)
    risk_score: float = 0.0
    risk_factors: List[str] = field(default_factory=list)

@dataclass
class Anomaly:
    """异常记录"""
    anomaly_id: str
    user_id: str
    anomaly_type: AnomalyType
    severity: RiskLevel
    description: str
    evidence: List[str]
    detected_at: str
    status: str = "detected"
    action_taken: str = "none"
    resolved_at: str = None

class BehaviorAnalyzer:
    """行为分析器"""
    
    def __init__(self):
        self.baseline_profiles: Dict[str, UserProfile] = {}
        self.current_events: List[BehaviorEvent] = []
        self.anomalies: List[Anomaly] = []
        self.analysis_window = 30  # 天
        self.anomaly_threshold = 0.7  # 异常阈值
    
    def calculate_frequency_score(self, user_id: str, event_type: BehaviorType, 
                                 time_window: int = 3600) -> Tuple[float, str]:
        """计算频率异常得分"""
        cutoff_time = datetime.now() - timedelta(seconds=time_window)
        recent_events = [
            e for e in self.current_events
            if e.user_id == user_id 
            and e.behavior_type == event_type
            and datetime.fromisoformat(e.timestamp) > cutoff_time
        ]
        
        count = len(recent_events)
        
        if count == 0:
            return 0.0, "normal"
        elif count <= 3:
            return 0.2, "low"
        elif count <= 10:
            return 0.5, "medium"
        elif count <= 30:
            return 0.8, "high"
        else:
            return 1.0, "critical"
    
    def calculate_time_score(self, user_id: str, current_time: datetime) -> Tuple[float, str]:
        """计算时间异常得分"""
        profile = self.baseline_profiles.get(user_id)
        if not profile or not profile.common_access_times:
            return 0.5, "unknown"
        
        hour = current_time.hour
        is_common_time = any(
            hour >= int(t.split(':')[0]) and hour < int(t.split(':')[1])
            for t in profile.common_access_times
        )
        
        if is_common_time:
            return 0.0, "normal"
        elif 22 <= hour or hour < 6:
            return 0.9, "critical"
        else:
            return 0.6, "unusual"
    
    def calculate_location_score(self, user_id: str, location: str) -> Tuple[float, str]:
        """计算位置异常得分"""
        profile = self.baseline_profiles.get(user_id)
        if not profile or not profile.common_locations:
            return 0.5, "unknown"
        
        if location in profile.common_locations:
            return 0.0, "normal"
        else:
            location_parts = location.split(',')
            for common_loc in profile.common_locations:
                if any(part in common_loc for part in location_parts):
                    return 0.3, "similar"
            return 0.8, "new_location"
    
    def calculate_volume_score(self, user_id: str, resource: str, 
                              time_window: int = 3600) -> Tuple[float, str]:
        """计算数量异常得分"""
        cutoff_time = datetime.now() - timedelta(seconds=time_window)
        recent_access = [
            e for e in self.current_events
            if e.user_id == user_id
            and e.resource == resource
            and datetime.fromisoformat(e.timestamp) > cutoff_time
        ]
        
        count = len(recent_access)
        
        if count == 0:
            return 0.0, "normal"
        elif count <= 5:
            return 0.1, "low"
        elif count <= 20:
            return 0.5, "medium"
        elif count <= 50:
            return 0.8, "high"
        else:
            return 1.0, "critical"
    
    def calculate_pattern_score(self, user_id: str, 
                              behavior_sequence: List[BehaviorType]) -> Tuple[float, str]:
        """计算模式异常得分"""
        profile = self.baseline_profiles.get(user_id)
        if not profile or not profile.behavior_patterns:
            return 0.5, "unknown"
        
        expected_pattern = profile.behavior_patterns.get('sequence', [])
        if not expected_pattern:
            return 0.5, "unknown"
        
        if len(behavior_sequence) < len(expected_pattern):
            return 0.3, "partial_match"
        
        matches = sum(
            1 for i, behavior in enumerate(behavior_sequence[-len(expected_pattern):])
            if behavior.value in expected_pattern[i:i+1]
        )
        
        match_ratio = matches / len(expected_pattern) if expected_pattern else 0
        
        if match_ratio >= 0.9:
            return 0.0, "normal"
        elif match_ratio >= 0.7:
            return 0.4, "slight_deviation"
        elif match_ratio >= 0.5:
            return 0.7, "significant_deviation"
        else:
            return 1.0, "completely_unusual"
    
    def analyze_behavior(self, event: BehaviorEvent) -> Dict[str, Any]:
        """分析行为异常"""
        risk_factors = []
        total_risk_score = 0.0
        factors_count = 0
        
        freq_score, freq_status = self.calculate_frequency_score(
            event.user_id, event.behavior_type
        )
        if freq_score > 0.3:
            risk_factors.append(f"频率异常: {freq_status}")
        total_risk_score += freq_score
        factors_count += 1
        
        time_score, time_status = self.calculate_time_score(
            event.user_id, datetime.fromisoformat(event.timestamp)
        )
        if time_score > 0.3:
            risk_factors.append(f"时间异常: {time_status}")
        total_risk_score += time_score
        factors_count += 1
        
        loc_score, loc_status = self.calculate_location_score(
            event.user_id, event.location
        )
        if loc_score > 0.3:
            risk_factors.append(f"位置异常: {loc_status}")
        total_risk_score += loc_score
        factors_count += 1
        
        vol_score, vol_status = self.calculate_volume_score(
            event.user_id, event.resource
        )
        if vol_score > 0.3:
            risk_factors.append(f"数量异常: {vol_status}")
        total_risk_score += vol_score
        factors_count += 1
        
        recent_behaviors = [
            e.behavior_type for e in self.current_events[-10:]
            if e.user_id == event.user_id
        ]
        pattern_score, pattern_status = self.calculate_pattern_score(
            event.user_id, recent_behaviors
        )
        if pattern_score > 0.3:
            risk_factors.append(f"模式异常: {pattern_status}")
        total_risk_score += pattern_score
        factors_count += 1
        
        avg_risk_score = total_risk_score / factors_count if factors_count > 0 else 0.0
        
        risk_level = RiskLevel.NORMAL
        if avg_risk_score >= 0.8:
            risk_level = RiskLevel.CRITICAL
        elif avg_risk_score >= 0.6:
            risk_level = RiskLevel.HIGH
        elif avg_risk_score >= 0.4:
            risk_level = RiskLevel.MEDIUM
        elif avg_risk_score >= 0.2:
            risk_level = RiskLevel.LOW
        
        return {
            'risk_score': avg_risk_score,
            'risk_level': risk_level,
            'risk_factors': risk_factors,
            'anomaly_detected': avg_risk_score > self.anomaly_threshold
        }

class UserBehaviorManager:
    """用户行为管理器"""
    
    def __init__(self, db_path: str = "user_behavior.db"):
        self.db_path = db_path
        self.analyzer = BehaviorAnalyzer()
        self._init_database()
        self._load_profiles()
    
    def _init_database(self):
        """初始化数据库"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS user_profiles (
                user_id TEXT PRIMARY KEY,
                username TEXT NOT NULL,
                department TEXT,
                role TEXT,
                access_level INTEGER DEFAULT 1,
                first_activity TEXT,
                last_activity TEXT,
                total_sessions INTEGER DEFAULT 0,
                avg_session_duration REAL DEFAULT 0.0,
                avg_activity_per_day REAL DEFAULT 0.0,
                common_access_times TEXT,
                common_locations TEXT,
                common_resources TEXT,
                behavior_patterns TEXT,
                risk_score REAL DEFAULT 0.0,
                risk_level TEXT DEFAULT 'normal',
                last_evaluated TEXT
            )
        """)
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS behavior_events (
                event_id TEXT PRIMARY KEY,
                user_id TEXT NOT NULL,
                username TEXT,
                behavior_type TEXT NOT NULL,
                timestamp TEXT NOT NULL,
                ip_address TEXT,
                location TEXT,
                resource TEXT,
                action TEXT,
                result TEXT DEFAULT 'success',
                duration REAL DEFAULT 0.0,
                metadata TEXT,
                risk_score REAL DEFAULT 0.0,
                risk_factors TEXT,
                FOREIGN KEY (user_id) REFERENCES user_profiles(user_id)
            )
        """)
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS anomalies (
                anomaly_id TEXT PRIMARY KEY,
                user_id TEXT,
                anomaly_type TEXT NOT NULL,
                severity TEXT,
                description TEXT,
                evidence TEXT,
                detected_at TEXT,
                status TEXT DEFAULT 'detected',
                action_taken TEXT DEFAULT 'none',
                resolved_at TEXT,
                FOREIGN KEY (user_id) REFERENCES user_profiles(user_id)
            )
        """)
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS risk_alerts (
                alert_id TEXT PRIMARY KEY,
                user_id TEXT,
                risk_level TEXT,
                alert_type TEXT,
                message TEXT,
                created_at TEXT,
                acknowledged INTEGER DEFAULT 0,
                acknowledged_by TEXT,
                acknowledged_at TEXT
            )
        """)
        
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_events_user_time 
            ON behavior_events(user_id, timestamp)
        """)
        
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_anomalies_user 
            ON anomalies(user_id, detected_at)
        """)
        
        conn.commit()
        conn.close()
        logger.info(f"用户行为数据库初始化完成: {self.db_path}")
    
    def _load_profiles(self):
        """加载用户画像"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM user_profiles")
        rows = cursor.fetchall()
        conn.close()
        
        columns = ['user_id', 'username', 'department', 'role', 'access_level',
                  'first_activity', 'last_activity', 'total_sessions', 
                  'avg_session_duration', 'avg_activity_per_day', 'common_access_times',
                  'common_locations', 'common_resources', 'behavior_patterns',
                  'risk_score', 'risk_level', 'last_evaluated']
        
        for row in rows:
            data = dict(zip(columns, row))
            data['common_access_times'] = json.loads(data['common_access_times']) if data['common_access_times'] else []
            data['common_locations'] = json.loads(data['common_locations']) if data['common_locations'] else []
            data['common_resources'] = json.loads(data['common_resources']) if data['common_resources'] else []
            data['behavior_patterns'] = json.loads(data['behavior_patterns']) if data['behavior_patterns'] else {}
            data['risk_level'] = RiskLevel(data['risk_level'])
            
            profile = UserProfile(**data)
            self.analyzer.baseline_profiles[profile.user_id] = profile
    
    def record_behavior(self, user_id: str, username: str, behavior_type: BehaviorType,
                       ip_address: str, location: str = "", resource: str = "",
                       action: str = "", result: str = "success", 
                       duration: float = 0.0, metadata: Dict = None) -> Tuple[str, Dict]:
        """记录用户行为"""
        event_id = f"EVT-{int(time.time())}-{hashlib.md5(f'{user_id}{time.time()}'.encode()).hexdigest()[:8]}"
        
        event = BehaviorEvent(
            event_id=event_id,
            user_id=user_id,
            username=username,
            behavior_type=behavior_type,
            timestamp=datetime.now().isoformat(),
            ip_address=ip_address,
            location=location,
            resource=resource,
            action=action,
            result=result,
            duration=duration,
            metadata=metadata or {}
        )
        
        analysis_result = self.analyzer.analyze_behavior(event)
        event.risk_score = analysis_result['risk_score']
        event.risk_factors = analysis_result['risk_factors']
        
        self._save_event(event)
        self._update_profile(event)
        self.analyzer.current_events.append(event)
        
        if len(self.analyzer.current_events) > 1000:
            self.analyzer.current_events = self.analyzer.current_events[-500:]
        
        if analysis_result['anomaly_detected']:
            self._create_anomaly(event, analysis_result)
        
        return event_id, analysis_result
    
    def _save_event(self, event: BehaviorEvent):
        """保存事件到数据库"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO behavior_events 
            (event_id, user_id, username, behavior_type, timestamp, ip_address,
             location, resource, action, result, duration, metadata, risk_score, risk_factors)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            event.event_id, event.user_id, event.username, event.behavior_type.value,
            event.timestamp, event.ip_address, event.location, event.resource,
            event.action, event.result, event.duration,
            json.dumps(event.metadata), event.risk_score,
            json.dumps(event.risk_factors)
        ))
        conn.commit()
        conn.close()
    
    def _update_profile(self, event: BehaviorEvent):
        """更新用户画像"""
        if event.user_id not in self.analyzer.baseline_profiles:
            profile = UserProfile(
                user_id=event.user_id,
                username=event.username,
                first_activity=event.timestamp
            )
            self.analyzer.baseline_profiles[event.user_id] = profile
        
        profile = self.analyzer.baseline_profiles[event.user_id]
        profile.last_activity = event.timestamp
        profile.total_sessions += 1
        
        if event.location and event.location not in profile.common_locations:
            profile.common_locations.append(event.location)
            if len(profile.common_locations) > 10:
                profile.common_locations = profile.common_locations[-10:]
        
        if event.resource and event.resource not in profile.common_resources:
            profile.common_resources.append(event.resource)
            if len(profile.common_resources) > 20:
                profile.common_resources = profile.common_resources[-20:]
        
        self._save_profile(profile)
    
    def _save_profile(self, profile: UserProfile):
        """保存用户画像"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("""
            INSERT OR REPLACE INTO user_profiles 
            (user_id, username, department, role, access_level, first_activity,
             last_activity, total_sessions, avg_session_duration, avg_activity_per_day,
             common_access_times, common_locations, common_resources, behavior_patterns,
             risk_score, risk_level, last_evaluated)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            profile.user_id, profile.username, profile.department, profile.role,
            profile.access_level, profile.first_activity, profile.last_activity,
            profile.total_sessions, profile.avg_session_duration,
            profile.avg_activity_per_day, json.dumps(profile.common_access_times),
            json.dumps(profile.common_locations), json.dumps(profile.common_resources),
            json.dumps(profile.behavior_patterns), profile.risk_score,
            profile.risk_level.value, datetime.now().isoformat()
        ))
        conn.commit()
        conn.close()
    
    def _create_anomaly(self, event: BehaviorEvent, analysis_result: Dict):
        """创建异常记录"""
        anomaly_id = f"ANM-{int(time.time())}-{hashlib.md5(event.event_id.encode()).hexdigest()[:8]}"
        
        anomaly = Anomaly(
            anomaly_id=anomaly_id,
            user_id=event.user_id,
            anomaly_type=AnomalyType.PATTERN_ANOMALY,
            severity=analysis_result['risk_level'],
            description=f"检测到异常行为: {', '.join(analysis_result['risk_factors'])}",
            evidence=[
                f"行为类型: {event.behavior_type.value}",
                f"IP: {event.ip_address}",
                f"位置: {event.location}",
                f"资源: {event.resource}",
                f"风险得分: {event.risk_score:.2f}"
            ],
            detected_at=datetime.now().isoformat()
        )
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO anomalies 
            (anomaly_id, user_id, anomaly_type, severity, description, evidence,
             detected_at, status, action_taken)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            anomaly.anomaly_id, anomaly.user_id, anomaly.anomaly_type.value,
            anomaly.severity.value, anomaly.description, json.dumps(anomaly.evidence),
            anomaly.detected_at, anomaly.status, anomaly.action_taken
        ))
        conn.commit()
        conn.close()
        
        self.analyzer.anomalies.append(anomaly)
        
        self._create_risk_alert(event.user_id, analysis_result['risk_level'], 
                               "anomaly_detected", anomaly.description)
        
        logger.warning(f"⚠️ 异常行为检测: 用户 {event.username} - {anomaly.description}")
    
    def _create_risk_alert(self, user_id: str, risk_level: RiskLevel,
                          alert_type: str, message: str):
        """创建风险告警"""
        alert_id = f"ALT-{int(time.time())}-{hashlib.md5(user_id.encode()).hexdigest()[:8]}"
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO risk_alerts 
            (alert_id, user_id, risk_level, alert_type, message, created_at)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (alert_id, user_id, risk_level.value, alert_type, message,
              datetime.now().isoformat()))
        conn.commit()
        conn.close()
        
        if risk_level == RiskLevel.CRITICAL:
            logger.critical(f"🚨 极高风险告警: {message}")
        elif risk_level == RiskLevel.HIGH:
            logger.error(f"⚠️ 高风险告警: {message}")
    
    def get_user_risk_score(self, user_id: str) -> Dict[str, Any]:
        """获取用户风险评分"""
        profile = self.analyzer.baseline_profiles.get(user_id)
        if not profile:
            return {'risk_score': 0.0, 'risk_level': 'normal', 'message': '无历史数据'}
        
        recent_events = [
            e for e in self.analyzer.current_events
            if e.user_id == user_id
            and datetime.fromisoformat(e.timestamp) > datetime.now() - timedelta(days=7)
        ]
        
        avg_risk = statistics.mean([e.risk_score for e in recent_events]) if recent_events else 0.0
        
        return {
            'user_id': user_id,
            'username': profile.username,
            'risk_score': avg_risk,
            'risk_level': profile.risk_level.value,
            'total_sessions': profile.total_sessions,
            'recent_events': len(recent_events),
            'last_activity': profile.last_activity
        }
    
    def get_user_behavior_timeline(self, user_id: str, days: int = 7) -> List[Dict]:
        """获取用户行为时间线"""
        cutoff_time = datetime.now() - timedelta(days=days)
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("""
            SELECT event_id, behavior_type, timestamp, ip_address, location,
                   resource, result, risk_score, risk_factors
            FROM behavior_events
            WHERE user_id = ? AND timestamp > ?
            ORDER BY timestamp DESC
        """, (user_id, cutoff_time.isoformat()))
        
        rows = cursor.fetchall()
        conn.close()
        
        events = []
        for row in rows:
            events.append({
                'event_id': row[0],
                'behavior_type': row[1],
                'timestamp': row[2],
                'ip_address': row[3],
                'location': row[4],
                'resource': row[5],
                'result': row[6],
                'risk_score': row[7],
                'risk_factors': json.loads(row[8]) if row[8] else []
            })
        
        return events
    
    def get_active_anomalies(self, limit: int = 50) -> List[Dict]:
        """获取活跃异常"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("""
            SELECT anomaly_id, user_id, anomaly_type, severity, description,
                   evidence, detected_at, status
            FROM anomalies
            WHERE status = 'detected'
            ORDER BY detected_at DESC
            LIMIT ?
        """, (limit,))
        
        rows = cursor.fetchall()
        conn.close()
        
        anomalies = []
        for row in rows:
            anomalies.append({
                'anomaly_id': row[0],
                'user_id': row[1],
                'anomaly_type': row[2],
                'severity': row[3],
                'description': row[4],
                'evidence': json.loads(row[5]) if row[5] else [],
                'detected_at': row[6],
                'status': row[7]
            })
        
        return anomalies
    
    def resolve_anomaly(self, anomaly_id: str, action: str = "resolved") -> bool:
        """解决异常"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute("""
                UPDATE anomalies 
                SET status = ?, resolved_at = ?
                WHERE anomaly_id = ?
            """, (action, datetime.now().isoformat(), anomaly_id))
            conn.commit()
            conn.close()
            return True
        except Exception as e:
            logger.error(f"解决异常失败: {e}")
            return False
    
    def get_behavior_statistics(self, days: int = 30) -> Dict[str, Any]:
        """获取行为统计"""
        cutoff_time = datetime.now() - timedelta(days=days)
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT COUNT(*) FROM behavior_events WHERE timestamp > ?
        """, (cutoff_time.isoformat(),))
        total_events = cursor.fetchone()[0]
        
        cursor.execute("""
            SELECT behavior_type, COUNT(*) 
            FROM behavior_events 
            WHERE timestamp > ?
            GROUP BY behavior_type
        """, (cutoff_time.isoformat(),))
        behavior_counts = dict(cursor.fetchall())
        
        cursor.execute("""
            SELECT COUNT(*) FROM anomalies 
            WHERE detected_at > ? AND status = 'detected'
        """, (cutoff_time.isoformat(),))
        active_anomalies = cursor.fetchone()[0]
        
        cursor.execute("""
            SELECT COUNT(DISTINCT user_id) FROM behavior_events 
            WHERE timestamp > ?
        """, (cutoff_time.isoformat(),))
        active_users = cursor.fetchone()[0]
        
        cursor.execute("""
            SELECT AVG(risk_score) FROM behavior_events 
            WHERE timestamp > ? AND risk_score > 0
        """, (cutoff_time.isoformat(),))
        avg_risk = cursor.fetchone()[0] or 0.0
        
        conn.close()
        
        return {
            'total_events': total_events,
            'behavior_counts': behavior_counts,
            'active_anomalies': active_anomalies,
            'active_users': active_users,
            'avg_risk_score': avg_risk,
            'period_days': days
        }

def main():
    """测试主函数"""
    print("\n👥 用户行为法则测试")
    print("=" * 60)
    
    manager = UserBehaviorManager()
    
    print("\n📊 行为统计:")
    stats = manager.get_behavior_statistics()
    for key, value in stats.items():
        print(f"  {key}: {value}")
    
    print("\n🧪 测试正常登录行为:")
    event_id, result = manager.record_behavior(
        user_id="test_user",
        username="测试用户",
        behavior_type=BehaviorType.LOGIN,
        ip_address="192.168.1.100",
        location="北京",
        action="login"
    )
    print(f"  事件ID: {event_id}")
    print(f"  风险评分: {result['risk_score']:.2f}")
    print(f"  风险等级: {result['risk_level'].value}")
    print(f"  异常检测: {'是' if result['anomaly_detected'] else '否'}")
    
    print("\n🧪 测试异常快速访问:")
    for i in range(10):
        event_id, result = manager.record_behavior(
            user_id="test_user",
            username="测试用户",
            behavior_type=BehaviorType.DATA_ACCESS,
            ip_address="192.168.1.100",
            location="北京",
            resource="/api/sensitive_data",
            action="read"
        )
        print(f"  第{i+1}次访问 - 风险评分: {result['risk_score']:.2f}")
    
    print("\n🧪 测试不同位置访问:")
    event_id, result = manager.record_behavior(
        user_id="test_user",
        username="测试用户",
        behavior_type=BehaviorType.LOGIN,
        ip_address="10.0.0.50",
        location="东京",
        action="login"
    )
    print(f"  事件ID: {event_id}")
    print(f"  风险评分: {result['risk_score']:.2f}")
    print(f"  风险因素: {', '.join(result['risk_factors'])}")
    
    print("\n📋 活跃异常:")
    anomalies = manager.get_active_anomalies()
    print(f"  当前活跃异常: {len(anomalies)} 个")
    for anomaly in anomalies[:3]:
        print(f"  - [{anomaly['severity']}] {anomaly['description'][:50]}...")
    
    print("\n📊 用户风险评分:")
    risk_info = manager.get_user_risk_score("test_user")
    for key, value in risk_info.items():
        print(f"  {key}: {value}")
    
    print("\n📈 最终行为统计:")
    stats = manager.get_behavior_statistics()
    for key, value in stats.items():
        print(f"  {key}: {value}")
    
    print("\n" + "=" * 60)
    print("✅ 用户行为法则测试完成")

if __name__ == '__main__':
    main()
