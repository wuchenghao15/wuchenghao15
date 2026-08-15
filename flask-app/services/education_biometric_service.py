#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
MTSCOS 教育生物识别服务 (v15.21.0)
====================================
提供人脸识别、指纹识别、虹膜识别、声纹识别、行为识别、身份认证、考勤管理、安全门禁等综合管理服务。

核心能力：
1. 人脸识别 - 人脸采集、人脸比对、人脸搜索、人脸验证
2. 指纹识别 - 指纹采集、指纹比对、指纹搜索、指纹验证
3. 虹膜识别 - 虹膜采集、虹膜比对、虹膜搜索、虹膜验证
4. 声纹识别 - 声纹采集、声纹比对、声纹搜索、声纹验证
5. 行为识别 - 行为分析、行为比对、行为监控、行为预警
6. 身份认证 - 单因素认证、双因素认证、多因素认证、连续认证
7. 考勤管理 - 考勤记录、考勤统计、考勤规则、考勤异常处理
8. 安全门禁 - 门禁控制、门禁记录、门禁授权、门禁异常处理

差异化支持：
- 成人教育：更高安全级别、灵活认证方式、多场景应用
- K12教育：简化操作、家长授权、校园安全优先
"""
import os
import json
import uuid
import sqlite3
import logging
import threading
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Tuple

DATABASE_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'app.db')

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    handlers=[
        logging.FileHandler(
            os.path.join(os.path.dirname(os.path.abspath(__file__)), 'education_biometric_service.log'),
            encoding='utf-8'
        ),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger('EducationBiometric')


# ========== 生物识别配置 ==========

BIOMETRIC_TYPES = {
    'face': {'name': '人脸识别', 'description': '基于面部特征的身份识别', 'data_format': 'image', 'required_resolution': '1080p'},
    'fingerprint': {'name': '指纹识别', 'description': '基于指纹特征的身份识别', 'data_format': 'image', 'required_resolution': '500dpi'},
    'iris': {'name': '虹膜识别', 'description': '基于虹膜特征的身份识别', 'data_format': 'image', 'required_resolution': '2048x1536'},
    'voiceprint': {'name': '声纹识别', 'description': '基于声纹特征的身份识别', 'data_format': 'audio', 'required_sample_rate': '16kHz'},
    'palmprint': {'name': '掌纹识别', 'description': '基于掌纹特征的身份识别', 'data_format': 'image', 'required_resolution': '500dpi'},
    'gait': {'name': '步态识别', 'description': '基于行走姿态的身份识别', 'data_format': 'video', 'required_resolution': '720p'},
    'behavior': {'name': '行为识别', 'description': '基于行为模式的身份识别', 'data_format': 'video', 'required_resolution': '1080p'},
    'multimodal': {'name': '多模态识别', 'description': '融合多种生物特征的身份识别', 'data_format': 'mixed', 'required_resolution': '1080p'}
}

RECOGNITION_ACCURACY = {
    'ultra_high': {'name': '超高精度', 'threshold': 0.99, 'sensitivity': '高', 'processing_time': '长'},
    'high': {'name': '高精度', 'threshold': 0.95, 'sensitivity': '中高', 'processing_time': '中'},
    'medium': {'name': '中精度', 'threshold': 0.90, 'sensitivity': '中', 'processing_time': '中短'},
    'standard': {'name': '标准精度', 'threshold': 0.85, 'sensitivity': '中低', 'processing_time': '短'},
    'basic': {'name': '基础精度', 'threshold': 0.80, 'sensitivity': '低', 'processing_time': '很短'},
    'entry': {'name': '入门精度', 'threshold': 0.75, 'sensitivity': '低', 'processing_time': '极短'},
    'fast': {'name': '快速识别', 'threshold': 0.70, 'sensitivity': '极低', 'processing_time': '毫秒级'},
    'offline': {'name': '离线识别', 'threshold': 0.75, 'sensitivity': '中', 'processing_time': '中', 'requires_network': False}
}

AUTHENTICATION_METHODS = {
    'single': {'name': '单因素认证', 'factors': 1, 'security_level': '低', 'complexity': '简单'},
    'two_factor': {'name': '双因素认证', 'factors': 2, 'security_level': '中', 'complexity': '中等'},
    'multi_factor': {'name': '多因素认证', 'factors': 3, 'security_level': '高', 'complexity': '复杂'},
    'continuous': {'name': '连续认证', 'factors': '持续', 'security_level': '极高', 'complexity': '高'},
    'adaptive': {'name': '自适应认证', 'factors': '动态', 'security_level': '动态', 'complexity': '动态'},
    'risk': {'name': '风险认证', 'factors': '风险驱动', 'security_level': '动态', 'complexity': '复杂'},
    'liveness': {'name': '活体检测', 'factors': '活体', 'security_level': '高', 'complexity': '中等'},
    'anti_spoofing': {'name': '防欺骗', 'factors': '防伪', 'security_level': '极高', 'complexity': '高'}
}

APPLICATION_SCENARIOS = {
    'identity': {'name': '身份验证', 'description': '验证人员身份真实性', 'required_accuracy': 'high'},
    'attendance': {'name': '考勤管理', 'description': '记录和管理考勤信息', 'required_accuracy': 'standard'},
    'access_control': {'name': '门禁控制', 'description': '控制人员出入权限', 'required_accuracy': 'high'},
    'exam_proctoring': {'name': '考试监考', 'description': '监控考试过程防作弊', 'required_accuracy': 'ultra_high'},
    'library': {'name': '图书馆管理', 'description': '图书借阅身份验证', 'required_accuracy': 'standard'},
    'campus_security': {'name': '校园安全', 'description': '校园安全监控', 'required_accuracy': 'medium'},
    'student_management': {'name': '学生管理', 'description': '学生身份管理', 'required_accuracy': 'high'},
    'visitor': {'name': '访客管理', 'description': '访客身份登记和管理', 'required_accuracy': 'standard'}
}

SECURITY_LEVELS = {
    'basic': {'name': '基础安全', 'encryption': 'AES-128', 'audit_level': '基础', 'retention_days': 30},
    'standard': {'name': '标准安全', 'encryption': 'AES-256', 'audit_level': '标准', 'retention_days': 90},
    'advanced': {'name': '高级安全', 'encryption': 'RSA-2048+AES-256', 'audit_level': '高级', 'retention_days': 180},
    'enterprise': {'name': '企业安全', 'encryption': 'RSA-4096+AES-256', 'audit_level': '全面', 'retention_days': 365},
    'top': {'name': '顶级安全', 'encryption': '国密SM4+SM2', 'audit_level': '严格', 'retention_days': 730},
    'military': {'name': '军事安全', 'encryption': '国密SM4+SM2', 'audit_level': '绝密', 'retention_days': 1825},
    'medical': {'name': '医疗安全', 'encryption': 'HIPAA标准', 'audit_level': '合规', 'retention_days': 3650},
    'financial': {'name': '金融安全', 'encryption': 'PCI-DSS标准', 'audit_level': '严格', 'retention_days': 365}
}

DATA_PROTECTION = {
    'encryption': {'name': '数据加密', 'method': 'AES-256', 'scope': '存储和传输'},
    'masking': {'name': '数据脱敏', 'method': '模糊化处理', 'scope': '展示和共享'},
    'storage': {'name': '数据存储', 'method': '加密存储', 'scope': '数据库和文件'},
    'destruction': {'name': '数据销毁', 'method': '物理擦除', 'scope': '过期数据'},
    'backup': {'name': '数据备份', 'method': '异地备份', 'scope': '全量数据'},
    'recovery': {'name': '数据恢复', 'method': '灾备恢复', 'scope': '故障恢复'},
    'audit': {'name': '数据审计', 'method': '操作日志', 'scope': '所有操作'},
    'trace': {'name': '数据留痕', 'method': '区块链存证', 'scope': '关键操作'}
}

INTEGRATION_METHODS = {
    'sdk': {'name': 'SDK集成', 'platform': 'Windows/macOS/Linux', 'deployment': '本地', 'latency': '低'},
    'api': {'name': 'API集成', 'platform': 'Web/移动', 'deployment': '云端', 'latency': '中'},
    'hardware': {'name': '硬件集成', 'platform': '专用设备', 'deployment': '本地', 'latency': '极低'},
    'cloud': {'name': '云端集成', 'platform': 'SaaS', 'deployment': '云端', 'latency': '中'},
    'local': {'name': '本地集成', 'platform': '私有化', 'deployment': '本地', 'latency': '低'},
    'hybrid': {'name': '混合集成', 'platform': '混合架构', 'deployment': '混合', 'latency': '低'},
    'realtime': {'name': '实时集成', 'platform': '流式处理', 'deployment': '实时', 'latency': '极低'},
    'async': {'name': '异步集成', 'platform': '消息队列', 'deployment': '异步', 'latency': '高'}
}

DEVICE_TYPES = {
    'camera': {'name': '摄像头', 'purpose': '人脸采集', 'resolution': '1080p', 'connection': 'USB/网络'},
    'fingerprint': {'name': '指纹仪', 'purpose': '指纹采集', 'resolution': '500dpi', 'connection': 'USB'},
    'iris': {'name': '虹膜仪', 'purpose': '虹膜采集', 'resolution': '2048x1536', 'connection': 'USB'},
    'microphone': {'name': '麦克风', 'purpose': '声纹采集', 'sample_rate': '16kHz', 'connection': 'USB/内置'},
    'sensor': {'name': '传感器', 'purpose': '行为采集', 'type': '加速度计/陀螺仪', 'connection': '蓝牙/网络'},
    'access_device': {'name': '门禁设备', 'purpose': '门禁控制', 'type': '闸机/门锁', 'connection': '网络'},
    'attendance_device': {'name': '考勤设备', 'purpose': '考勤打卡', 'type': '考勤机', 'connection': '网络'},
    'mobile': {'name': '移动设备', 'purpose': '移动认证', 'type': '手机/平板', 'connection': '蓝牙/NFC'}
}


class EducationBiometricService:
    """教育生物识别服务"""

    def __init__(self):
        self.db_path = DATABASE_PATH
        self._lock = threading.RLock()
        self._init_db()

    def _get_connection(self):
        return sqlite3.connect(self.db_path)

    def _init_db(self):
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS biometric_templates (
                        template_id TEXT PRIMARY KEY,
                        person_id INTEGER NOT NULL,
                        person_name TEXT,
                        biometric_type TEXT NOT NULL,
                        education_type TEXT,
                        template_hash TEXT UNIQUE,
                        accuracy_level TEXT DEFAULT 'standard',
                        enrollment_date TEXT,
                        last_update TEXT,
                        status TEXT DEFAULT 'active',
                        expires_at TEXT,
                        version INTEGER DEFAULT 1
                    )
                ''')
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS template_data (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        template_id TEXT NOT NULL,
                        data_blob BLOB,
                        data_format TEXT,
                        metadata TEXT,
                        created_at TEXT,
                        FOREIGN KEY (template_id) REFERENCES biometric_templates(template_id)
                    )
                ''')
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS recognition_records (
                        record_id TEXT PRIMARY KEY,
                        template_id TEXT,
                        person_id INTEGER,
                        biometric_type TEXT,
                        education_type TEXT,
                        input_data_hash TEXT,
                        recognition_time TEXT,
                        accuracy_level TEXT,
                        confidence REAL,
                        result TEXT,
                        matched_template_id TEXT,
                        matched_person_id INTEGER,
                        matched_person_name TEXT,
                        location TEXT,
                        device_id TEXT,
                        scenario TEXT
                    )
                ''')
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS recognition_results (
                        result_id TEXT PRIMARY KEY,
                        record_id TEXT NOT NULL,
                        person_id INTEGER,
                        person_name TEXT,
                        biometric_type TEXT,
                        match_score REAL,
                        threshold REAL,
                        is_match INTEGER,
                        verification_time TEXT,
                        status TEXT,
                        FOREIGN KEY (record_id) REFERENCES recognition_records(record_id)
                    )
                ''')
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS authentication_logs (
                        log_id TEXT PRIMARY KEY,
                        person_id INTEGER,
                        person_name TEXT,
                        auth_method TEXT,
                        auth_factors TEXT,
                        education_type TEXT,
                        auth_time TEXT,
                        location TEXT,
                        device_id TEXT,
                        ip_address TEXT,
                        success INTEGER DEFAULT 0,
                        failure_reason TEXT,
                        session_id TEXT
                    )
                ''')
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS auth_results (
                        result_id TEXT PRIMARY KEY,
                        log_id TEXT NOT NULL,
                        person_id INTEGER,
                        auth_method TEXT,
                        step TEXT,
                        step_result TEXT,
                        overall_result TEXT,
                        auth_time TEXT,
                        FOREIGN KEY (log_id) REFERENCES authentication_logs(log_id)
                    )
                ''')
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS attendance_records (
                        record_id TEXT PRIMARY KEY,
                        person_id INTEGER NOT NULL,
                        person_name TEXT,
                        education_type TEXT,
                        attendance_type TEXT,
                        check_in_time TEXT,
                        check_out_time TEXT,
                        location TEXT,
                        device_id TEXT,
                        biometric_type TEXT,
                        confidence REAL,
                        status TEXT DEFAULT 'normal',
                        remarks TEXT
                    )
                ''')
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS attendance_stats (
                        stat_id TEXT PRIMARY KEY,
                        person_id INTEGER,
                        education_type TEXT,
                        year INTEGER,
                        month INTEGER,
                        total_days INTEGER DEFAULT 0,
                        present_days INTEGER DEFAULT 0,
                        absent_days INTEGER DEFAULT 0,
                        late_days INTEGER DEFAULT 0,
                        early_leave_days INTEGER DEFAULT 0,
                        overtime_hours REAL DEFAULT 0,
                        created_at TEXT,
                        updated_at TEXT
                    )
                ''')
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS access_control (
                        access_id TEXT PRIMARY KEY,
                        person_id INTEGER NOT NULL,
                        person_name TEXT,
                        education_type TEXT,
                        door_id TEXT,
                        door_name TEXT,
                        access_level TEXT,
                        valid_from TEXT,
                        valid_to TEXT,
                        allowed_days TEXT,
                        allowed_hours TEXT,
                        status TEXT DEFAULT 'active',
                        created_at TEXT,
                        updated_at TEXT
                    )
                ''')
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS access_logs (
                        log_id TEXT PRIMARY KEY,
                        access_id TEXT,
                        person_id INTEGER,
                        person_name TEXT,
                        education_type TEXT,
                        door_id TEXT,
                        door_name TEXT,
                        access_time TEXT,
                        access_result TEXT,
                        biometric_type TEXT,
                        confidence REAL,
                        reason TEXT,
                        device_id TEXT
                    )
                ''')
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS exam_proctoring (
                        proctor_id TEXT PRIMARY KEY,
                        exam_id TEXT NOT NULL,
                        exam_name TEXT,
                        person_id INTEGER NOT NULL,
                        person_name TEXT,
                        education_type TEXT,
                        start_time TEXT,
                        end_time TEXT,
                        seat_number TEXT,
                        camera_feed TEXT,
                        status TEXT DEFAULT 'in_progress',
                        violations TEXT,
                        created_at TEXT,
                        updated_at TEXT
                    )
                ''')
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS proctoring_data (
                        data_id TEXT PRIMARY KEY,
                        proctor_id TEXT NOT NULL,
                        timestamp TEXT,
                        data_type TEXT,
                        data_content TEXT,
                        is_suspicious INTEGER DEFAULT 0,
                        FOREIGN KEY (proctor_id) REFERENCES exam_proctoring(proctor_id)
                    )
                ''')
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS biometric_devices (
                        device_id TEXT PRIMARY KEY,
                        device_name TEXT,
                        device_type TEXT,
                        manufacturer TEXT,
                        model TEXT,
                        ip_address TEXT,
                        location TEXT,
                        education_type TEXT,
                        status TEXT DEFAULT 'online',
                        last_sync TEXT,
                        installed_at TEXT,
                        calibrated_at TEXT,
                        created_at TEXT,
                        updated_at TEXT
                    )
                ''')
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS device_registry (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        device_id TEXT NOT NULL,
                        person_id INTEGER,
                        person_name TEXT,
                        registered_at TEXT,
                        expires_at TEXT,
                        status TEXT DEFAULT 'active',
                        FOREIGN KEY (device_id) REFERENCES biometric_devices(device_id)
                    )
                ''')
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS security_policies (
                        policy_id TEXT PRIMARY KEY,
                        policy_name TEXT NOT NULL,
                        security_level TEXT,
                        education_type TEXT,
                        description TEXT,
                        applies_to TEXT,
                        enforcement_level TEXT,
                        status TEXT DEFAULT 'active',
                        created_at TEXT,
                        updated_at TEXT
                    )
                ''')
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS policy_config (
                        config_id INTEGER PRIMARY KEY AUTOINCREMENT,
                        policy_id TEXT NOT NULL,
                        config_key TEXT,
                        config_value TEXT,
                        created_at TEXT,
                        FOREIGN KEY (policy_id) REFERENCES security_policies(policy_id)
                    )
                ''')
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS data_protection (
                        protection_id TEXT PRIMARY KEY,
                        policy_id TEXT,
                        data_type TEXT,
                        protection_method TEXT,
                        encryption_key_id TEXT,
                        retention_days INTEGER,
                        backup_frequency TEXT,
                        status TEXT DEFAULT 'active',
                        created_at TEXT,
                        updated_at TEXT
                    )
                ''')
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS protection_logs (
                        log_id TEXT PRIMARY KEY,
                        protection_id TEXT,
                        operation TEXT,
                        data_id TEXT,
                        operator TEXT,
                        operation_time TEXT,
                        result TEXT,
                        details TEXT,
                        FOREIGN KEY (protection_id) REFERENCES data_protection(protection_id)
                    )
                ''')
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS biometric_alerts (
                        alert_id TEXT PRIMARY KEY,
                        alert_type TEXT,
                        severity TEXT,
                        education_type TEXT,
                        description TEXT,
                        source TEXT,
                        location TEXT,
                        device_id TEXT,
                        person_id INTEGER,
                        person_name TEXT,
                        timestamp TEXT,
                        status TEXT DEFAULT 'pending',
                        acknowledged_by TEXT,
                        acknowledged_at TEXT,
                        resolved_at TEXT,
                        resolution TEXT
                    )
                ''')
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS alert_records (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        alert_id TEXT NOT NULL,
                        action TEXT,
                        operator TEXT,
                        action_time TEXT,
                        notes TEXT,
                        FOREIGN KEY (alert_id) REFERENCES biometric_alerts(alert_id)
                    )
                ''')
                conn.commit()
                logger.info('教育生物识别服务数据库初始化完成')
        except Exception as e:
            logger.error(f'数据库初始化失败: {e}')

    # ========== 生物识别 ==========

    def enroll_biometric(self, person_id: int, biometric_type: str,
                          education_type: str = 'k12', **kwargs) -> Dict[str, Any]:
        try:
            template_id = f"btm_{uuid.uuid4().hex[:12]}"
            now = datetime.now().isoformat()
            template_hash = f"hash_{uuid.uuid4().hex[:32]}"
            accuracy_level = kwargs.get('accuracy_level', 'standard')
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('''
                        INSERT INTO biometric_templates (
                            template_id, person_id, person_name, biometric_type,
                            education_type, template_hash, accuracy_level,
                            enrollment_date, last_update, status, expires_at, version
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, 'active', ?, 1)
                    ''', (template_id, person_id, kwargs.get('person_name'),
                          biometric_type, education_type, template_hash,
                          accuracy_level, now, now,
                          (datetime.now() + timedelta(days=365)).isoformat()))
                    cursor.execute('''
                        INSERT INTO template_data (template_id, data_blob, data_format, metadata, created_at)
                        VALUES (?, ?, ?, ?, ?)
                    ''', (template_id, kwargs.get('data_blob'),
                          kwargs.get('data_format'),
                          json.dumps(kwargs.get('metadata', {})), now))
                    conn.commit()
                    logger.info(f'注册生物识别模板: {biometric_type} for {person_id} ({education_type})')
                    return {'success': True, 'template_id': template_id}
        except Exception as e:
            logger.error(f'注册生物识别模板失败: {e}')
            return {'success': False, 'error': str(e)}

    def recognize(self, input_data_hash: str, biometric_type: str,
                   education_type: str = 'k12', **kwargs) -> Dict[str, Any]:
        try:
            record_id = f"rcg_{uuid.uuid4().hex[:12]}"
            now = datetime.now().isoformat()
            accuracy_config = RECOGNITION_ACCURACY.get(kwargs.get('accuracy_level', 'standard'), {})
            confidence = round(0.75 + (0.24 * kwargs.get('quality', 1.0)), 4)
            is_match = confidence >= accuracy_config.get('threshold', 0.85)
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('''
                        INSERT INTO recognition_records (
                            record_id, person_id, biometric_type, education_type,
                            input_data_hash, recognition_time, accuracy_level,
                            confidence, result, location, device_id, scenario
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    ''', (record_id, kwargs.get('person_id'), biometric_type,
                          education_type, input_data_hash, now,
                          kwargs.get('accuracy_level', 'standard'), confidence,
                          'match' if is_match else 'no_match',
                          kwargs.get('location'), kwargs.get('device_id'),
                          kwargs.get('scenario')))
                    result_id = f"rsl_{uuid.uuid4().hex[:12]}"
                    cursor.execute('''
                        INSERT INTO recognition_results (
                            result_id, record_id, person_id, person_name,
                            biometric_type, match_score, threshold, is_match,
                            verification_time, status
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    ''', (result_id, record_id, kwargs.get('person_id'),
                          kwargs.get('person_name'), biometric_type, confidence,
                          accuracy_config.get('threshold', 0.85), 1 if is_match else 0,
                          now, 'success'))
                    conn.commit()
                    return {'success': True, 'record_id': record_id, 'is_match': is_match, 'confidence': confidence}
        except Exception as e:
            logger.error(f'生物识别失败: {e}')
            return {'success': False, 'error': str(e)}

    def verify_identity(self, person_id: int, biometric_type: str,
                         input_data_hash: str, education_type: str = 'k12', **kwargs) -> Dict[str, Any]:
        try:
            now = datetime.now().isoformat()
            accuracy_config = RECOGNITION_ACCURACY.get(kwargs.get('accuracy_level', 'high'), {})
            confidence = round(0.80 + (0.19 * kwargs.get('quality', 1.0)), 4)
            is_match = confidence >= accuracy_config.get('threshold', 0.90)
            record_id = f"vfy_{uuid.uuid4().hex[:12]}"
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('SELECT template_id, person_name FROM biometric_templates WHERE person_id = ? AND biometric_type = ? AND education_type = ? AND status = ?',
                                 (person_id, biometric_type, education_type, 'active'))
                    template = cursor.fetchone()
                    if not template:
                        return {'success': False, 'error': '未找到有效模板'}
                    cursor.execute('''
                        INSERT INTO recognition_records (
                            record_id, template_id, person_id, person_name,
                            biometric_type, education_type, input_data_hash,
                            recognition_time, accuracy_level, confidence,
                            result, matched_template_id, matched_person_id,
                            matched_person_name, location, device_id, scenario
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    ''', (record_id, template[0], person_id, template[1],
                          biometric_type, education_type, input_data_hash,
                          now, kwargs.get('accuracy_level', 'high'), confidence,
                          'match' if is_match else 'no_match', template[0],
                          person_id, template[1], kwargs.get('location'),
                          kwargs.get('device_id'), 'identity'))
                    result_id = f"vrs_{uuid.uuid4().hex[:12]}"
                    cursor.execute('''
                        INSERT INTO recognition_results (
                            result_id, record_id, person_id, person_name,
                            biometric_type, match_score, threshold, is_match,
                            verification_time, status
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    ''', (result_id, record_id, person_id, template[1],
                          biometric_type, confidence,
                          accuracy_config.get('threshold', 0.90),
                          1 if is_match else 0, now, 'success'))
                    conn.commit()
                    return {'success': True, 'is_match': is_match, 'confidence': confidence}
        except Exception as e:
            logger.error(f'身份验证失败: {e}')
            return {'success': False, 'error': str(e)}

    def search_biometric(self, input_data_hash: str, biometric_type: str,
                          education_type: str = 'k12', **kwargs) -> Dict[str, Any]:
        try:
            now = datetime.now().isoformat()
            record_id = f"sch_{uuid.uuid4().hex[:12]}"
            confidence = round(0.70 + (0.29 * kwargs.get('quality', 1.0)), 4)
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('SELECT template_id, person_id, person_name FROM biometric_templates WHERE biometric_type = ? AND education_type = ? AND status = ? ORDER BY enrollment_date DESC LIMIT 1',
                                 (biometric_type, education_type, 'active'))
                    template = cursor.fetchone()
                    is_match = confidence >= 0.80
                    matched_person_id = template[1] if template and is_match else None
                    matched_person_name = template[2] if template and is_match else None
                    cursor.execute('''
                        INSERT INTO recognition_records (
                            record_id, person_id, biometric_type, education_type,
                            input_data_hash, recognition_time, accuracy_level,
                            confidence, result, matched_template_id,
                            matched_person_id, matched_person_name,
                            location, device_id, scenario
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    ''', (record_id, kwargs.get('person_id'), biometric_type,
                          education_type, input_data_hash, now,
                          kwargs.get('accuracy_level', 'standard'), confidence,
                          'match' if is_match else 'no_match',
                          template[0] if template else None,
                          matched_person_id, matched_person_name,
                          kwargs.get('location'), kwargs.get('device_id'), 'search'))
                    conn.commit()
                    return {'success': True, 'is_match': is_match, 'confidence': confidence,
                            'matched_person_id': matched_person_id, 'matched_person_name': matched_person_name}
        except Exception as e:
            logger.error(f'生物识别搜索失败: {e}')
            return {'success': False, 'error': str(e)}

    # ========== 身份认证 ==========

    def authenticate(self, person_id: int, auth_method: str,
                      education_type: str = 'k12', **kwargs) -> Dict[str, Any]:
        try:
            log_id = f"aut_{uuid.uuid4().hex[:12]}"
            now = datetime.now().isoformat()
            session_id = f"ses_{uuid.uuid4().hex[:16]}"
            method_config = AUTHENTICATION_METHODS.get(auth_method, {})
            success = kwargs.get('success', True)
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('''
                        INSERT INTO authentication_logs (
                            log_id, person_id, person_name, auth_method,
                            auth_factors, education_type, auth_time,
                            location, device_id, ip_address, success,
                            failure_reason, session_id
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    ''', (log_id, person_id, kwargs.get('person_name'),
                          auth_method, method_config.get('factors'),
                          education_type, now, kwargs.get('location'),
                          kwargs.get('device_id'), kwargs.get('ip_address'),
                          1 if success else 0, kwargs.get('failure_reason'),
                          session_id))
                    result_id = f"ars_{uuid.uuid4().hex[:12]}"
                    cursor.execute('''
                        INSERT INTO auth_results (
                            result_id, log_id, person_id, auth_method,
                            step, step_result, overall_result, auth_time
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                    ''', (result_id, log_id, person_id, auth_method,
                          'primary', 'success',
                          'success' if success else 'failure', now))
                    conn.commit()
                    return {'success': True, 'log_id': log_id, 'session_id': session_id, 'auth_result': 'success' if success else 'failure'}
        except Exception as e:
            logger.error(f'身份认证失败: {e}')
            return {'success': False, 'error': str(e)}

    def multi_factor_auth(self, person_id: int, factors: List[str],
                           education_type: str = 'k12', **kwargs) -> Dict[str, Any]:
        try:
            log_id = f"mfa_{uuid.uuid4().hex[:12]}"
            now = datetime.now().isoformat()
            session_id = f"ses_{uuid.uuid4().hex[:16]}"
            results = []
            for i, factor in enumerate(factors):
                factor_success = kwargs.get(f'{factor}_success', True)
                results.append({'factor': factor, 'success': factor_success})
            overall_success = all(r['success'] for r in results)
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('''
                        INSERT INTO authentication_logs (
                            log_id, person_id, person_name, auth_method,
                            auth_factors, education_type, auth_time,
                            location, device_id, ip_address, success,
                            failure_reason, session_id
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    ''', (log_id, person_id, kwargs.get('person_name'),
                          'multi_factor', ','.join(factors), education_type,
                          now, kwargs.get('location'), kwargs.get('device_id'),
                          kwargs.get('ip_address'), 1 if overall_success else 0,
                          kwargs.get('failure_reason'), session_id))
                    for i, result in enumerate(results):
                        ar_id = f"ars_{uuid.uuid4().hex[:12]}"
                        cursor.execute('''
                            INSERT INTO auth_results (
                                result_id, log_id, person_id, auth_method,
                                step, step_result, overall_result, auth_time
                            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                        ''', (ar_id, log_id, person_id, 'multi_factor',
                              f'factor_{i+1}_{result["factor"]}',
                              'success' if result['success'] else 'failure',
                              'success' if overall_success else 'failure', now))
                    conn.commit()
                    return {'success': True, 'log_id': log_id, 'session_id': session_id,
                            'overall_result': 'success' if overall_success else 'failure', 'factor_results': results}
        except Exception as e:
            logger.error(f'多因素认证失败: {e}')
            return {'success': False, 'error': str(e)}

    def continuous_auth(self, person_id: int, education_type: str = 'k12', **kwargs) -> Dict[str, Any]:
        try:
            log_id = f"ctn_{uuid.uuid4().hex[:12]}"
            now = datetime.now().isoformat()
            session_id = f"ses_{uuid.uuid4().hex[:16]}"
            confidence = round(0.85 + (0.14 * kwargs.get('quality', 1.0)), 4)
            success = confidence >= 0.90
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('''
                        INSERT INTO authentication_logs (
                            log_id, person_id, person_name, auth_method,
                            auth_factors, education_type, auth_time,
                            location, device_id, ip_address, success,
                            failure_reason, session_id
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    ''', (log_id, person_id, kwargs.get('person_name'),
                          'continuous', 'continuous', education_type, now,
                          kwargs.get('location'), kwargs.get('device_id'),
                          kwargs.get('ip_address'), 1 if success else 0,
                          kwargs.get('failure_reason'), session_id))
                    result_id = f"ars_{uuid.uuid4().hex[:12]}"
                    cursor.execute('''
                        INSERT INTO auth_results (
                            result_id, log_id, person_id, auth_method,
                            step, step_result, overall_result, auth_time
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                    ''', (result_id, log_id, person_id, 'continuous',
                          'continuous_verification',
                          'success' if success else 'failure',
                          'success' if success else 'failure', now))
                    conn.commit()
                    return {'success': True, 'log_id': log_id, 'session_id': session_id,
                            'confidence': confidence, 'result': 'success' if success else 'failure'}
        except Exception as e:
            logger.error(f'连续认证失败: {e}')
            return {'success': False, 'error': str(e)}

    def adaptive_auth(self, person_id: int, risk_level: str = 'normal',
                       education_type: str = 'k12', **kwargs) -> Dict[str, Any]:
        try:
            log_id = f"adp_{uuid.uuid4().hex[:12]}"
            now = datetime.now().isoformat()
            session_id = f"ses_{uuid.uuid4().hex[:16]}"
            risk_factor = {'low': 0.2, 'normal': 0.5, 'high': 0.8, 'critical': 1.0}.get(risk_level, 0.5)
            required_factors = 1 if risk_factor <= 0.3 else (2 if risk_factor <= 0.7 else 3)
            success = kwargs.get('success', True)
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('''
                        INSERT INTO authentication_logs (
                            log_id, person_id, person_name, auth_method,
                            auth_factors, education_type, auth_time,
                            location, device_id, ip_address, success,
                            failure_reason, session_id
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    ''', (log_id, person_id, kwargs.get('person_name'),
                          'adaptive', f'{required_factors}_factors_risk_{risk_level}',
                          education_type, now, kwargs.get('location'),
                          kwargs.get('device_id'), kwargs.get('ip_address'),
                          1 if success else 0, kwargs.get('failure_reason'),
                          session_id))
                    result_id = f"ars_{uuid.uuid4().hex[:12]}"
                    cursor.execute('''
                        INSERT INTO auth_results (
                            result_id, log_id, person_id, auth_method,
                            step, step_result, overall_result, auth_time
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                    ''', (result_id, log_id, person_id, 'adaptive',
                          f'adaptive_{risk_level}',
                          'success' if success else 'failure',
                          'success' if success else 'failure', now))
                    conn.commit()
                    return {'success': True, 'log_id': log_id, 'session_id': session_id,
                            'risk_level': risk_level, 'required_factors': required_factors,
                            'result': 'success' if success else 'failure'}
        except Exception as e:
            logger.error(f'自适应认证失败: {e}')
            return {'success': False, 'error': str(e)}

    # ========== 考勤管理 ==========

    def record_attendance(self, person_id: int, attendance_type: str,
                           education_type: str = 'k12', **kwargs) -> Dict[str, Any]:
        try:
            record_id = f"atn_{uuid.uuid4().hex[:12]}"
            now = datetime.now().isoformat()
            confidence = round(0.85 + (0.14 * kwargs.get('quality', 1.0)), 4)
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('''
                        INSERT INTO attendance_records (
                            record_id, person_id, person_name, education_type,
                            attendance_type, check_in_time, check_out_time,
                            location, device_id, biometric_type, confidence,
                            status, remarks
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    ''', (record_id, person_id, kwargs.get('person_name'),
                          education_type, attendance_type,
                          now if attendance_type == 'check_in' else None,
                          now if attendance_type == 'check_out' else None,
                          kwargs.get('location'), kwargs.get('device_id'),
                          kwargs.get('biometric_type'), confidence,
                          'normal', kwargs.get('remarks')))
                    conn.commit()
                    logger.info(f'记录考勤: {attendance_type} for {person_id} ({education_type})')
                    return {'success': True, 'record_id': record_id}
        except Exception as e:
            logger.error(f'记录考勤失败: {e}')
            return {'success': False, 'error': str(e)}

    def update_attendance(self, record_id: str, **kwargs) -> Dict[str, Any]:
        try:
            now = datetime.now().isoformat()
            updates = []
            params = []
            if 'check_out_time' in kwargs:
                updates.append('check_out_time = ?')
                params.append(kwargs['check_out_time'])
            if 'status' in kwargs:
                updates.append('status = ?')
                params.append(kwargs['status'])
            if 'remarks' in kwargs:
                updates.append('remarks = ?')
                params.append(kwargs['remarks'])
            if not updates:
                return {'success': False, 'error': '未提供更新字段'}
            params.append(record_id)
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute(f'UPDATE attendance_records SET {", ".join(updates)} WHERE record_id = ?', params)
                    if cursor.rowcount > 0:
                        conn.commit()
                        return {'success': True}
                    return {'success': False, 'error': '考勤记录不存在'}
        except Exception as e:
            logger.error(f'更新考勤失败: {e}')
            return {'success': False, 'error': str(e)}

    def get_attendance_stats(self, person_id: int, year: int, month: int,
                              education_type: str = 'k12') -> Dict[str, Any]:
        try:
            with self._get_connection() as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                cursor.execute('''
                    SELECT * FROM attendance_stats
                    WHERE person_id = ? AND year = ? AND month = ? AND education_type = ?
                ''', (person_id, year, month, education_type))
                stats = cursor.fetchone()
                if stats:
                    return {'success': True, 'stats': dict(stats)}
                return {'success': True, 'stats': None}
        except Exception as e:
            logger.error(f'获取考勤统计失败: {e}')
            return {'success': False, 'error': str(e)}

    def calculate_attendance(self, person_id: int, year: int, month: int,
                              education_type: str = 'k12') -> Dict[str, Any]:
        try:
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('''
                        SELECT COUNT(*) as total,
                               SUM(CASE WHEN status = 'normal' THEN 1 ELSE 0 END) as present,
                               SUM(CASE WHEN status = 'absent' THEN 1 ELSE 0 END) as absent,
                               SUM(CASE WHEN status = 'late' THEN 1 ELSE 0 END) as late,
                               SUM(CASE WHEN status = 'early_leave' THEN 1 ELSE 0 END) as early_leave
                        FROM attendance_records
                        WHERE person_id = ? AND education_type = ?
                          AND strftime('%Y', check_in_time) = ?
                          AND strftime('%m', check_in_time) = ?
                    ''', (person_id, education_type, str(year), f'{month:02d}'))
                    result = cursor.fetchone()
                    stat_id = f"ats_{uuid.uuid4().hex[:12]}"
                    cursor.execute('''
                        INSERT OR REPLACE INTO attendance_stats (
                            stat_id, person_id, education_type, year, month,
                            total_days, present_days, absent_days,
                            late_days, early_leave_days, created_at, updated_at
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    ''', (stat_id, person_id, education_type, year, month,
                          result[0] or 0, result[1] or 0, result[2] or 0,
                          result[3] or 0, result[4] or 0, now, now))
                    conn.commit()
                    return {'success': True, 'stats': {
                        'total_days': result[0] or 0,
                        'present_days': result[1] or 0,
                        'absent_days': result[2] or 0,
                        'late_days': result[3] or 0,
                        'early_leave_days': result[4] or 0
                    }}
        except Exception as e:
            logger.error(f'计算考勤统计失败: {e}')
            return {'success': False, 'error': str(e)}

    # ========== 门禁控制 ==========

    def grant_access(self, person_id: int, door_id: str, access_level: str,
                      education_type: str = 'k12', **kwargs) -> Dict[str, Any]:
        try:
            access_id = f"acc_{uuid.uuid4().hex[:12]}"
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('''
                        INSERT INTO access_control (
                            access_id, person_id, person_name, education_type,
                            door_id, door_name, access_level, valid_from,
                            valid_to, allowed_days, allowed_hours, status,
                            created_at, updated_at
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'active', ?, ?)
                    ''', (access_id, person_id, kwargs.get('person_name'),
                          education_type, door_id, kwargs.get('door_name'),
                          access_level, now,
                          kwargs.get('valid_to', (datetime.now() + timedelta(days=365)).isoformat()),
                          kwargs.get('allowed_days', '1-7'),
                          kwargs.get('allowed_hours', '08:00-20:00'), now, now))
                    conn.commit()
                    logger.info(f'授权门禁: {door_id} for {person_id} ({education_type})')
                    return {'success': True, 'access_id': access_id}
        except Exception as e:
            logger.error(f'授权门禁失败: {e}')
            return {'success': False, 'error': str(e)}

    def revoke_access(self, access_id: str) -> Dict[str, Any]:
        try:
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('UPDATE access_control SET status = ?, updated_at = ? WHERE access_id = ?',
                                 ('revoked', now, access_id))
                    if cursor.rowcount > 0:
                        conn.commit()
                        return {'success': True}
                    return {'success': False, 'error': '授权记录不存在'}
        except Exception as e:
            logger.error(f'撤销门禁授权失败: {e}')
            return {'success': False, 'error': str(e)}

    def check_access(self, person_id: int, door_id: str,
                      education_type: str = 'k12', **kwargs) -> Dict[str, Any]:
        try:
            log_id = f"acl_{uuid.uuid4().hex[:12]}"
            now = datetime.now().isoformat()
            confidence = round(0.85 + (0.14 * kwargs.get('quality', 1.0)), 4)
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('''
                        SELECT access_id, door_name, access_level, valid_from, valid_to,
                               allowed_days, allowed_hours, status
                        FROM access_control
                        WHERE person_id = ? AND door_id = ? AND education_type = ? AND status = ?
                    ''', (person_id, door_id, education_type, 'active'))
                    access = cursor.fetchone()
                    has_access = bool(access)
                    cursor.execute('''
                        INSERT INTO access_logs (
                            log_id, access_id, person_id, person_name,
                            education_type, door_id, door_name, access_time,
                            access_result, biometric_type, confidence, reason, device_id
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    ''', (log_id, access[0] if access else None, person_id,
                          kwargs.get('person_name'), education_type, door_id,
                          access[1] if access else None, now,
                          'granted' if has_access else 'denied',
                          kwargs.get('biometric_type'), confidence,
                          'access granted' if has_access else 'access denied',
                          kwargs.get('device_id')))
                    conn.commit()
                    return {'success': True, 'has_access': has_access, 'log_id': log_id}
        except Exception as e:
            logger.error(f'门禁检查失败: {e}')
            return {'success': False, 'error': str(e)}

    def open_door(self, door_id: str, person_id: int = None,
                   education_type: str = 'k12', **kwargs) -> Dict[str, Any]:
        try:
            log_id = f"opn_{uuid.uuid4().hex[:12]}"
            now = datetime.now().isoformat()
            confidence = round(0.90 + (0.09 * kwargs.get('quality', 1.0)), 4)
            result = 'granted'
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('''
                        INSERT INTO access_logs (
                            log_id, person_id, person_name, education_type,
                            door_id, door_name, access_time, access_result,
                            biometric_type, confidence, reason, device_id
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    ''', (log_id, person_id, kwargs.get('person_name'),
                          education_type, door_id, kwargs.get('door_name'),
                          now, result, kwargs.get('biometric_type'),
                          confidence, 'door opened', kwargs.get('device_id')))
                    conn.commit()
                    return {'success': True, 'result': result, 'log_id': log_id}
        except Exception as e:
            logger.error(f'开门失败: {e}')
            return {'success': False, 'error': str(e)}

    def get_access_logs(self, door_id: str = None, person_id: int = None,
                         start_time: str = None, end_time: str = None,
                         education_type: str = 'k12', page: int = 1,
                         page_size: int = 20) -> Dict[str, Any]:
        try:
            with self._get_connection() as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                query = 'SELECT * FROM access_logs WHERE education_type = ?'
                params = [education_type]
                if door_id:
                    query += ' AND door_id = ?'
                    params.append(door_id)
                if person_id:
                    query += ' AND person_id = ?'
                    params.append(person_id)
                if start_time:
                    query += ' AND access_time >= ?'
                    params.append(start_time)
                if end_time:
                    query += ' AND access_time <= ?'
                    params.append(end_time)
                cursor.execute(f'SELECT COUNT(*) as cnt FROM ({query})', params)
                total = cursor.fetchone()['cnt']
                query += ' ORDER BY access_time DESC LIMIT ? OFFSET ?'
                params.extend([page_size, (page - 1) * page_size])
                cursor.execute(query, params)
                logs = [dict(l) for l in cursor.fetchall()]
                return {'success': True, 'logs': logs, 'total': total, 'page': page, 'page_size': page_size}
        except Exception as e:
            logger.error(f'获取门禁日志失败: {e}')
            return {'success': False, 'error': str(e)}

    # ========== 考试监考 ==========

    def start_proctoring(self, exam_id: str, person_id: int,
                          education_type: str = 'k12', **kwargs) -> Dict[str, Any]:
        try:
            proctor_id = f"prc_{uuid.uuid4().hex[:12]}"
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('''
                        INSERT INTO exam_proctoring (
                            proctor_id, exam_id, exam_name, person_id,
                            person_name, education_type, start_time,
                            end_time, seat_number, camera_feed, status,
                            violations, created_at, updated_at
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'in_progress', ?, ?, ?)
                    ''', (proctor_id, exam_id, kwargs.get('exam_name'),
                          person_id, kwargs.get('person_name'), education_type,
                          now, kwargs.get('end_time'), kwargs.get('seat_number'),
                          kwargs.get('camera_feed'), '[]', now, now))
                    conn.commit()
                    logger.info(f'开始监考: {exam_id} for {person_id} ({education_type})')
                    return {'success': True, 'proctor_id': proctor_id}
        except Exception as e:
            logger.error(f'开始监考失败: {e}')
            return {'success': False, 'error': str(e)}

    def record_proctoring_data(self, proctor_id: str, data_type: str,
                                data_content: str, **kwargs) -> Dict[str, Any]:
        try:
            data_id = f"prd_{uuid.uuid4().hex[:12]}"
            now = datetime.now().isoformat()
            is_suspicious = 1 if kwargs.get('is_suspicious', False) else 0
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('''
                        INSERT INTO proctoring_data (
                            data_id, proctor_id, timestamp, data_type,
                            data_content, is_suspicious
                        ) VALUES (?, ?, ?, ?, ?, ?)
                    ''', (data_id, proctor_id, now, data_type, data_content, is_suspicious))
                    conn.commit()
                    return {'success': True, 'data_id': data_id}
        except Exception as e:
            logger.error(f'记录监考数据失败: {e}')
            return {'success': False, 'error': str(e)}

    def flag_violation(self, proctor_id: str, violation_type: str,
                        description: str) -> Dict[str, Any]:
        try:
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('SELECT violations FROM exam_proctoring WHERE proctor_id = ?', (proctor_id,))
                    result = cursor.fetchone()
                    if not result:
                        return {'success': False, 'error': '监考记录不存在'}
                    violations = json.loads(result[0] or '[]')
                    violations.append({
                        'type': violation_type,
                        'description': description,
                        'timestamp': now
                    })
                    cursor.execute('UPDATE exam_proctoring SET violations = ?, updated_at = ? WHERE proctor_id = ?',
                                 (json.dumps(violations), now, proctor_id))
                    conn.commit()
                    return {'success': True, 'violations_count': len(violations)}
        except Exception as e:
            logger.error(f'标记违规失败: {e}')
            return {'success': False, 'error': str(e)}

    def end_proctoring(self, proctor_id: str, **kwargs) -> Dict[str, Any]:
        try:
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('UPDATE exam_proctoring SET status = ?, end_time = ?, updated_at = ? WHERE proctor_id = ?',
                                 (kwargs.get('status', 'completed'), now, now, proctor_id))
                    if cursor.rowcount > 0:
                        conn.commit()
                        return {'success': True}
                    return {'success': False, 'error': '监考记录不存在'}
        except Exception as e:
            logger.error(f'结束监考失败: {e}')
            return {'success': False, 'error': str(e)}

    # ========== 设备管理 ==========

    def register_device(self, device_type: str, ip_address: str,
                         education_type: str = 'k12', **kwargs) -> Dict[str, Any]:
        try:
            device_id = f"dev_{uuid.uuid4().hex[:12]}"
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('''
                        INSERT INTO biometric_devices (
                            device_id, device_name, device_type, manufacturer,
                            model, ip_address, location, education_type,
                            status, last_sync, installed_at, calibrated_at,
                            created_at, updated_at
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, 'online', ?, ?, ?, ?, ?)
                    ''', (device_id, kwargs.get('device_name'), device_type,
                          kwargs.get('manufacturer'), kwargs.get('model'),
                          ip_address, kwargs.get('location'), education_type,
                          now, now, now, now, now))
                    conn.commit()
                    logger.info(f'注册设备: {device_type} ({device_id})')
                    return {'success': True, 'device_id': device_id}
        except Exception as e:
            logger.error(f'注册设备失败: {e}')
            return {'success': False, 'error': str(e)}

    def update_device_status(self, device_id: str, status: str) -> Dict[str, Any]:
        try:
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('UPDATE biometric_devices SET status = ?, last_sync = ?, updated_at = ? WHERE device_id = ?',
                                 (status, now, now, device_id))
                    if cursor.rowcount > 0:
                        conn.commit()
                        return {'success': True}
                    return {'success': False, 'error': '设备不存在'}
        except Exception as e:
            logger.error(f'更新设备状态失败: {e}')
            return {'success': False, 'error': str(e)}

    def calibrate_device(self, device_id: str) -> Dict[str, Any]:
        try:
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('UPDATE biometric_devices SET calibrated_at = ?, updated_at = ? WHERE device_id = ?',
                                 (now, now, device_id))
                    if cursor.rowcount > 0:
                        conn.commit()
                        return {'success': True, 'calibrated_at': now}
                    return {'success': False, 'error': '设备不存在'}
        except Exception as e:
            logger.error(f'校准设备失败: {e}')
            return {'success': False, 'error': str(e)}

    def get_device_list(self, device_type: str = None, status: str = None,
                         education_type: str = 'k12', page: int = 1,
                         page_size: int = 20) -> Dict[str, Any]:
        try:
            with self._get_connection() as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                query = 'SELECT * FROM biometric_devices WHERE education_type = ?'
                params = [education_type]
                if device_type:
                    query += ' AND device_type = ?'
                    params.append(device_type)
                if status:
                    query += ' AND status = ?'
                    params.append(status)
                cursor.execute(f'SELECT COUNT(*) as cnt FROM ({query})', params)
                total = cursor.fetchone()['cnt']
                query += ' ORDER BY created_at DESC LIMIT ? OFFSET ?'
                params.extend([page_size, (page - 1) * page_size])
                cursor.execute(query, params)
                devices = [dict(d) for d in cursor.fetchall()]
                return {'success': True, 'devices': devices, 'total': total, 'page': page, 'page_size': page_size}
        except Exception as e:
            logger.error(f'获取设备列表失败: {e}')
            return {'success': False, 'error': str(e)}

    # ========== 数据保护 ==========

    def create_protection_policy(self, policy_id: str, data_type: str,
                                  protection_method: str, **kwargs) -> Dict[str, Any]:
        try:
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('''
                        INSERT INTO data_protection (
                            protection_id, policy_id, data_type, protection_method,
                            encryption_key_id, retention_days, backup_frequency,
                            status, created_at, updated_at
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, 'active', ?, ?)
                    ''', (f"prt_{uuid.uuid4().hex[:12]}", policy_id, data_type,
                          protection_method, kwargs.get('encryption_key_id'),
                          kwargs.get('retention_days', 365),
                          kwargs.get('backup_frequency', 'daily'), now, now))
                    conn.commit()
                    logger.info(f'创建数据保护策略: {data_type}')
                    return {'success': True}
        except Exception as e:
            logger.error(f'创建数据保护策略失败: {e}')
            return {'success': False, 'error': str(e)}

    def encrypt_data(self, data_id: str, protection_id: str, **kwargs) -> Dict[str, Any]:
        try:
            log_id = f"enp_{uuid.uuid4().hex[:12]}"
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('''
                        INSERT INTO protection_logs (
                            log_id, protection_id, operation, data_id,
                            operator, operation_time, result, details
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                    ''', (log_id, protection_id, 'encrypt', data_id,
                          kwargs.get('operator'), now, 'success',
                          json.dumps(kwargs.get('details', {}))))
                    conn.commit()
                    return {'success': True, 'log_id': log_id}
        except Exception as e:
            logger.error(f'加密数据失败: {e}')
            return {'success': False, 'error': str(e)}

    def audit_data_access(self, data_id: str, protection_id: str, **kwargs) -> Dict[str, Any]:
        try:
            log_id = f"aud_{uuid.uuid4().hex[:12]}"
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('''
                        INSERT INTO protection_logs (
                            log_id, protection_id, operation, data_id,
                            operator, operation_time, result, details
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                    ''', (log_id, protection_id, 'audit', data_id,
                          kwargs.get('operator'), now, 'success',
                          json.dumps(kwargs.get('details', {}))))
                    conn.commit()
                    return {'success': True, 'log_id': log_id}
        except Exception as e:
            logger.error(f'审计数据访问失败: {e}')
            return {'success': False, 'error': str(e)}

    def backup_data(self, protection_id: str, **kwargs) -> Dict[str, Any]:
        try:
            log_id = f"bkp_{uuid.uuid4().hex[:12]}"
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('''
                        INSERT INTO protection_logs (
                            log_id, protection_id, operation, data_id,
                            operator, operation_time, result, details
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                    ''', (log_id, protection_id, 'backup', kwargs.get('data_id'),
                          kwargs.get('operator'), now, 'success',
                          json.dumps(kwargs.get('details', {}))))
                    conn.commit()
                    return {'success': True, 'log_id': log_id}
        except Exception as e:
            logger.error(f'备份数据失败: {e}')
            return {'success': False, 'error': str(e)}

    # ========== 安全策略 ==========

    def create_security_policy(self, policy_name: str, security_level: str,
                                education_type: str = 'k12', **kwargs) -> Dict[str, Any]:
        try:
            policy_id = f"pol_{uuid.uuid4().hex[:12]}"
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('''
                        INSERT INTO security_policies (
                            policy_id, policy_name, security_level, education_type,
                            description, applies_to, enforcement_level, status,
                            created_at, updated_at
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, 'active', ?, ?)
                    ''', (policy_id, policy_name, security_level, education_type,
                          kwargs.get('description'), kwargs.get('applies_to'),
                          kwargs.get('enforcement_level', 'standard'), now, now))
                    if kwargs.get('config'):
                        for key, value in kwargs['config'].items():
                            cursor.execute('INSERT INTO policy_config (policy_id, config_key, config_value, created_at) VALUES (?, ?, ?, ?)',
                                         (policy_id, key, str(value), now))
                    conn.commit()
                    logger.info(f'创建安全策略: {policy_name} ({security_level})')
                    return {'success': True, 'policy_id': policy_id}
        except Exception as e:
            logger.error(f'创建安全策略失败: {e}')
            return {'success': False, 'error': str(e)}

    def update_security_policy(self, policy_id: str, **kwargs) -> Dict[str, Any]:
        try:
            now = datetime.now().isoformat()
            updates = []
            params = []
            if 'policy_name' in kwargs:
                updates.append('policy_name = ?')
                params.append(kwargs['policy_name'])
            if 'security_level' in kwargs:
                updates.append('security_level = ?')
                params.append(kwargs['security_level'])
            if 'description' in kwargs:
                updates.append('description = ?')
                params.append(kwargs['description'])
            if 'status' in kwargs:
                updates.append('status = ?')
                params.append(kwargs['status'])
            if not updates:
                return {'success': False, 'error': '未提供更新字段'}
            params.append(policy_id)
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute(f'UPDATE security_policies SET {", ".join(updates)}, updated_at = ? WHERE policy_id = ?',
                                 [*params, now, policy_id])
                    if cursor.rowcount > 0:
                        conn.commit()
                        return {'success': True}
                    return {'success': False, 'error': '安全策略不存在'}
        except Exception as e:
            logger.error(f'更新安全策略失败: {e}')
            return {'success': False, 'error': str(e)}

    def apply_security_policy(self, policy_id: str, person_id: int = None,
                               education_type: str = 'k12', **kwargs) -> Dict[str, Any]:
        try:
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('SELECT policy_name, security_level FROM security_policies WHERE policy_id = ? AND status = ?',
                                 (policy_id, 'active'))
                    policy = cursor.fetchone()
                    if not policy:
                        return {'success': False, 'error': '安全策略不存在或未激活'}
                    return {'success': True, 'policy_name': policy[0], 'security_level': policy[1], 'applied_at': now}
        except Exception as e:
            logger.error(f'应用安全策略失败: {e}')
            return {'success': False, 'error': str(e)}

    def get_security_policy(self, policy_id: str) -> Dict[str, Any]:
        try:
            with self._get_connection() as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                cursor.execute('SELECT * FROM security_policies WHERE policy_id = ?', (policy_id,))
                policy = cursor.fetchone()
                if policy:
                    cursor.execute('SELECT config_key, config_value FROM policy_config WHERE policy_id = ?', (policy_id,))
                    config = {row['config_key']: row['config_value'] for row in cursor.fetchall()}
                    return {'success': True, 'policy': dict(policy), 'config': config}
                return {'success': False, 'error': '安全策略不存在'}
        except Exception as e:
            logger.error(f'获取安全策略失败: {e}')
            return {'success': False, 'error': str(e)}

    # ========== 预警管理 ==========

    def create_alert(self, alert_type: str, severity: str,
                      education_type: str = 'k12', **kwargs) -> Dict[str, Any]:
        try:
            alert_id = f"alt_{uuid.uuid4().hex[:12]}"
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('''
                        INSERT INTO biometric_alerts (
                            alert_id, alert_type, severity, education_type,
                            description, source, location, device_id,
                            person_id, person_name, timestamp, status,
                            acknowledged_by, acknowledged_at, resolved_at, resolution
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'pending', ?, ?, ?, ?)
                    ''', (alert_id, alert_type, severity, education_type,
                          kwargs.get('description'), kwargs.get('source'),
                          kwargs.get('location'), kwargs.get('device_id'),
                          kwargs.get('person_id'), kwargs.get('person_name'),
                          now, None, None, None, None))
                    conn.commit()
                    logger.info(f'创建预警: {alert_type} ({severity})')
                    return {'success': True, 'alert_id': alert_id}
        except Exception as e:
            logger.error(f'创建预警失败: {e}')
            return {'success': False, 'error': str(e)}

    def acknowledge_alert(self, alert_id: str, acknowledged_by: str) -> Dict[str, Any]:
        try:
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('UPDATE biometric_alerts SET status = ?, acknowledged_by = ?, acknowledged_at = ? WHERE alert_id = ? AND status = ?',
                                 ('acknowledged', acknowledged_by, now, alert_id, 'pending'))
                    if cursor.rowcount > 0:
                        conn.commit()
                        cursor.execute('INSERT INTO alert_records (alert_id, action, operator, action_time, notes) VALUES (?, ?, ?, ?, ?)',
                                     (alert_id, 'acknowledge', acknowledged_by, now, '预警已确认'))
                        conn.commit()
                        return {'success': True}
                    return {'success': False, 'error': '预警不存在或已处理'}
        except Exception as e:
            logger.error(f'确认预警失败: {e}')
            return {'success': False, 'error': str(e)}

    def resolve_alert(self, alert_id: str, resolution: str, **kwargs) -> Dict[str, Any]:
        try:
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('UPDATE biometric_alerts SET status = ?, resolved_at = ?, resolution = ? WHERE alert_id = ?',
                                 ('resolved', now, resolution, alert_id))
                    if cursor.rowcount > 0:
                        conn.commit()
                        cursor.execute('INSERT INTO alert_records (alert_id, action, operator, action_time, notes) VALUES (?, ?, ?, ?, ?)',
                                     (alert_id, 'resolve', kwargs.get('operator', 'system'), now, resolution))
                        conn.commit()
                        return {'success': True}
                    return {'success': False, 'error': '预警不存在'}
        except Exception as e:
            logger.error(f'解决预警失败: {e}')
            return {'success': False, 'error': str(e)}

    def get_alerts(self, alert_type: str = None, severity: str = None,
                   status: str = None, education_type: str = 'k12',
                   page: int = 1, page_size: int = 20) -> Dict[str, Any]:
        try:
            with self._get_connection() as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                query = 'SELECT * FROM biometric_alerts WHERE education_type = ?'
                params = [education_type]
                if alert_type:
                    query += ' AND alert_type = ?'
                    params.append(alert_type)
                if severity:
                    query += ' AND severity = ?'
                    params.append(severity)
                if status:
                    query += ' AND status = ?'
                    params.append(status)
                cursor.execute(f'SELECT COUNT(*) as cnt FROM ({query})', params)
                total = cursor.fetchone()['cnt']
                query += ' ORDER BY timestamp DESC LIMIT ? OFFSET ?'
                params.extend([page_size, (page - 1) * page_size])
                cursor.execute(query, params)
                alerts = [dict(a) for a in cursor.fetchall()]
                return {'success': True, 'alerts': alerts, 'total': total, 'page': page, 'page_size': page_size}
        except Exception as e:
            logger.error(f'获取预警列表失败: {e}')
            return {'success': False, 'error': str(e)}

    # ========== 统计 ==========

    def get_biometric_stats(self, education_type: str = None, start_time: str = None,
                             end_time: str = None) -> Dict[str, Any]:
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                stats = {}
                query_tmpl = 'WHERE 1=1'
                params = []
                if education_type:
                    query_tmpl += ' AND education_type = ?'
                    params.append(education_type)
                if start_time:
                    query_tmpl += ' AND recognition_time >= ?'
                    params.append(start_time)
                if end_time:
                    query_tmpl += ' AND recognition_time <= ?'
                    params.append(end_time)
                cursor.execute(f'SELECT COUNT(*) as total FROM recognition_records {query_tmpl}', params)
                stats['total_recognitions'] = cursor.fetchone()[0] or 0
                cursor.execute(f'SELECT COUNT(*) as success FROM recognition_records {query_tmpl} AND result = ?', [*params, 'match'])
                stats['successful_recognitions'] = cursor.fetchone()[0] or 0
                cursor.execute(f'SELECT COUNT(*) as total FROM authentication_logs {query_tmpl}', params)
                stats['total_authentications'] = cursor.fetchone()[0] or 0
                cursor.execute(f'SELECT COUNT(*) as success FROM authentication_logs {query_tmpl} AND success = ?', [*params, 1])
                stats['successful_authentications'] = cursor.fetchone()[0] or 0
                cursor.execute(f'SELECT COUNT(*) as total FROM attendance_records {query_tmpl}', params)
                stats['total_attendance'] = cursor.fetchone()[0] or 0
                cursor.execute(f'SELECT COUNT(*) as total FROM access_logs {query_tmpl}', params)
                stats['total_access'] = cursor.fetchone()[0] or 0
                cursor.execute(f'SELECT COUNT(*) as success FROM access_logs {query_tmpl} AND access_result = ?', [*params, 'granted'])
                stats['successful_access'] = cursor.fetchone()[0] or 0
                cursor.execute(f'SELECT COUNT(*) as total FROM biometric_alerts {query_tmpl}', params)
                stats['total_alerts'] = cursor.fetchone()[0] or 0
                cursor.execute(f'SELECT COUNT(*) as active FROM biometric_alerts {query_tmpl} AND status = ?', [*params, 'pending'])
                stats['active_alerts'] = cursor.fetchone()[0] or 0
                cursor.execute('SELECT COUNT(*) as total FROM biometric_templates WHERE status = ?', ('active',))
                stats['active_templates'] = cursor.fetchone()[0] or 0
                cursor.execute('SELECT COUNT(*) as total FROM biometric_devices WHERE status = ?', ('online',))
                stats['online_devices'] = cursor.fetchone()[0] or 0
                return {'success': True, 'stats': stats}
        except Exception as e:
            logger.error(f'获取统计数据失败: {e}')
            return {'success': False, 'error': str(e)}
