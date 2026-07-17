#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
MTSCOS 教育脑机接口服务 (v15.19.0)
====================================
提供脑机接口基础、EEG采集、脑信号分析、思维控制、神经反馈、BCI应用、脑机交互和教育应用等综合管理服务。

核心能力：
1. 脑机接口 - 接口管理、连接控制、设备配置、信号校准
2. EEG采集 - 信号采集、数据存储、质量检测、实时传输
3. 脑信号分析 - 时频分析、特征提取、模式识别、智能诊断
4. 思维控制 - 思维解码、意图识别、动作控制、状态监测
5. 神经反馈 - 实时反馈、训练计划、效果评估、自适应调节
6. BCI应用 - 应用管理、场景配置、个性化设置、数据同步
7. 设备管理 - 设备注册、状态监控、维护记录、固件升级
8. 教育应用 - 课程管理、学习分析、认知训练、能力评估
9. 研究管理 - 项目管理、数据采集、实验设计、成果追踪
10. 统计分析 - 综合统计、趋势分析、对比报告、数据可视化
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
            os.path.join(os.path.dirname(os.path.abspath(__file__)), 'education_bci_service.log'),
            encoding='utf-8'
        ),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger('EducationBCI')


# ========== BCI配置项 ==========

BCI_TYPES = {
    'non_invasive': {'name': '非侵入式BCI', 'description': '无需手术植入，通过头皮电极采集脑电信号', 'safety_level': 'high', 'precision': 'medium'},
    'invasive': {'name': '侵入式BCI', 'description': '通过手术将电极植入大脑皮层', 'safety_level': 'low', 'precision': 'high'},
    'semi_invasive': {'name': '半侵入式BCI', 'description': '电极植入颅骨与大脑皮层之间', 'safety_level': 'medium', 'precision': 'high'},
    'neural_prosthesis': {'name': '神经假体', 'description': '替代或增强神经功能的植入设备', 'safety_level': 'medium', 'precision': 'high'},
    'brain_network': {'name': '脑网络接口', 'description': '连接多个大脑形成脑联网', 'safety_level': 'low', 'precision': 'medium'}
}

SIGNAL_TYPES = {
    'eeg': {'name': '脑电图', 'description': '头皮电极采集的脑电信号', 'frequency_range': '0.5-100Hz', 'spatial_resolution': 'low'},
    'meg': {'name': '脑磁图', 'description': '测量大脑神经元活动产生的磁场', 'frequency_range': '0.1-1000Hz', 'spatial_resolution': 'medium'},
    'fmri': {'name': '功能磁共振', 'description': '基于血氧水平依赖的脑成像技术', 'frequency_range': '0.01-1Hz', 'spatial_resolution': 'high'},
    'ecog': {'name': '皮层脑电图', 'description': '放置在大脑皮层表面的电极记录', 'frequency_range': '0.5-1000Hz', 'spatial_resolution': 'high'},
    'ieeg': {'name': '颅内脑电图', 'description': '植入大脑内部的电极记录', 'frequency_range': '0.5-1000Hz', 'spatial_resolution': 'very_high'},
    'nir': {'name': '近红外光谱', 'description': '通过近红外光测量脑血氧变化', 'frequency_range': '0.01-10Hz', 'spatial_resolution': 'medium'}
}

ANALYSIS_METHODS = {
    'time_frequency': {'name': '时频分析', 'description': '分析信号在时间和频率域的特征', 'applications': ['事件相关电位', '脑电波节律']},
    'spatial_filtering': {'name': '空间滤波', 'description': '从多通道信号中提取感兴趣成分', 'applications': ['源定位', '伪迹去除']},
    'machine_learning': {'name': '机器学习', 'description': '使用传统ML算法进行模式识别', 'applications': ['分类', '回归', '聚类']},
    'deep_learning': {'name': '深度学习', 'description': '使用神经网络进行特征学习', 'applications': ['深度学习解码', '脑信号建模']},
    'pattern_recognition': {'name': '模式识别', 'description': '识别脑信号中的特定模式', 'applications': ['运动想象', '视觉想象']},
    'feature_extraction': {'name': '特征提取', 'description': '从原始信号中提取有用特征', 'applications': ['频域特征', '时域特征', '非线性特征']}
}

CONTROL_MODES = {
    'thought_control': {'name': '思维控制', 'description': '通过思维直接控制外部设备', 'training_required': True, 'difficulty': 'high'},
    'motor_imagery': {'name': '运动想象', 'description': '想象运动动作来控制设备', 'training_required': True, 'difficulty': 'medium'},
    'visual_imagery': {'name': '视觉想象', 'description': '通过想象视觉图像进行控制', 'training_required': True, 'difficulty': 'medium'},
    'emotion_control': {'name': '情绪控制', 'description': '通过情绪状态控制设备', 'training_required': False, 'difficulty': 'low'},
    'attention_control': {'name': '注意力控制', 'description': '通过注意力水平控制设备', 'training_required': False, 'difficulty': 'low'},
    'mental_typing': {'name': '意念打字', 'description': '通过思维进行文字输入', 'training_required': True, 'difficulty': 'high'}
}

FEEDBACK_TYPES = {
    'visual': {'name': '视觉反馈', 'description': '通过视觉形式提供反馈信息', 'medium': '屏幕', 'delay': 'low'},
    'auditory': {'name': '听觉反馈', 'description': '通过声音提供反馈信息', 'medium': '耳机', 'delay': 'low'},
    'haptic': {'name': '触觉反馈', 'description': '通过触觉刺激提供反馈', 'medium': '振动器', 'delay': 'medium'},
    'neural': {'name': '神经反馈', 'description': '直接作用于神经系统的反馈', 'medium': '电刺激', 'delay': 'low'},
    'real_time': {'name': '实时反馈', 'description': '即时的反馈信息', 'latency': '<100ms', 'applications': ['训练']},
    'delayed': {'name': '延迟反馈', 'description': '延迟的反馈信息', 'latency': '>100ms', 'applications': ['评估']}
}

BCI_APPLICATIONS = {
    'assistive_education': {'name': '辅助教育', 'description': '帮助特殊教育学生学习', 'target_users': ['特殊教育学生', '学习障碍者']},
    'rehabilitation': {'name': '康复训练', 'description': '帮助运动功能障碍者康复', 'target_users': ['中风患者', '脊髓损伤者']},
    'cognitive_enhancement': {'name': '认知增强', 'description': '提升认知能力', 'target_users': ['学生', '专业人士']},
    'emotion_regulation': {'name': '情绪调节', 'description': '帮助情绪管理', 'target_users': ['焦虑症患者', '压力较大者']},
    'attention_training': {'name': '注意力训练', 'description': '提升注意力水平', 'target_users': ['儿童', '注意力缺陷者']},
    'learning_optimization': {'name': '学习优化', 'description': '优化学习过程', 'target_users': ['学生', '终身学习者']}
}

HARDWARE_DEVICES = {
    'eeg_headset': {'name': 'EEG头戴设备', 'description': '轻便的脑电采集头戴', 'channels': '4-32', 'wireless': True},
    'eeg_cap': {'name': '脑电帽', 'description': '高密度脑电采集帽子', 'channels': '32-256', 'wireless': False},
    'dry_electrode': {'name': '干电极设备', 'description': '无需导电膏的电极', 'comfort': 'high', 'signal_quality': 'medium'},
    'wet_electrode': {'name': '湿电极设备', 'description': '需要导电膏的传统电极', 'comfort': 'medium', 'signal_quality': 'high'},
    'wireless_device': {'name': '无线设备', 'description': '无线传输的脑电设备', 'range': '5-30m', 'battery_life': '4-8h'},
    'portable_device': {'name': '便携式设备', 'description': '便于携带的脑电设备', 'weight': '<500g', 'applications': ['移动监测']}
}

EDUCATION_SCENARIOS = {
    'classroom': {'name': '课堂学习', 'description': '在传统课堂环境中使用BCI', 'group_size': '10-50', 'focus': '注意力监测'},
    'personalized': {'name': '个性化学习', 'description': '基于脑信号的个性化学习方案', 'group_size': '1', 'focus': '学习优化'},
    'special_education': {'name': '特殊教育', 'description': '为特殊需求学生提供支持', 'group_size': '1-5', 'focus': '辅助沟通'},
    'vocational_training': {'name': '职业培训', 'description': '专业技能的BCI辅助培训', 'group_size': '5-20', 'focus': '技能提升'},
    'cognitive_rehabilitation': {'name': '认知康复', 'description': '认知功能损伤的康复训练', 'group_size': '1-3', 'focus': '康复治疗'},
    'neuroscience_education': {'name': '神经科学教育', 'description': '神经科学知识的实践教学', 'group_size': '5-30', 'focus': '科学探究'}
}


class EducationBCIService:
    """教育脑机接口服务"""

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
                    CREATE TABLE IF NOT EXISTS bci_devices (
                        device_id TEXT PRIMARY KEY,
                        device_name TEXT NOT NULL,
                        device_type TEXT,
                        hardware_category TEXT,
                        manufacturer TEXT,
                        model TEXT,
                        channel_count INTEGER DEFAULT 8,
                        signal_type TEXT,
                        sampling_rate INTEGER DEFAULT 250,
                        wireless INTEGER DEFAULT 1,
                        battery_life INTEGER DEFAULT 4,
                        firmware_version TEXT,
                        status TEXT DEFAULT 'available',
                        location TEXT,
                        education_type TEXT,
                        created_at TEXT,
                        updated_at TEXT
                    )
                ''')
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS device_registry (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        device_id TEXT NOT NULL,
                        user_id INTEGER,
                        user_name TEXT,
                        register_date TEXT,
                        unregister_date TEXT,
                        usage_count INTEGER DEFAULT 0,
                        total_usage_hours REAL DEFAULT 0,
                        last_used_date TEXT,
                        FOREIGN KEY (device_id) REFERENCES bci_devices(device_id)
                    )
                ''')
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS signal_recording (
                        recording_id TEXT PRIMARY KEY,
                        device_id TEXT NOT NULL,
                        user_id INTEGER,
                        user_name TEXT,
                        signal_type TEXT,
                        education_type TEXT,
                        start_time TEXT,
                        end_time TEXT,
                        duration REAL,
                        sample_count INTEGER,
                        channel_data TEXT,
                        file_path TEXT,
                        signal_quality REAL DEFAULT 0,
                        status TEXT DEFAULT 'recording',
                        created_at TEXT,
                        FOREIGN KEY (device_id) REFERENCES bci_devices(device_id)
                    )
                ''')
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS recording_sessions (
                        session_id TEXT PRIMARY KEY,
                        user_id INTEGER,
                        user_name TEXT,
                        education_type TEXT,
                        session_type TEXT,
                        start_time TEXT,
                        end_time TEXT,
                        duration REAL,
                        recording_count INTEGER DEFAULT 0,
                        device_ids TEXT,
                        notes TEXT,
                        status TEXT DEFAULT 'active',
                        created_at TEXT,
                        updated_at TEXT
                    )
                ''')
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS brain_signal_analysis (
                        analysis_id TEXT PRIMARY KEY,
                        recording_id TEXT NOT NULL,
                        user_id INTEGER,
                        user_name TEXT,
                        education_type TEXT,
                        analysis_method TEXT,
                        parameters TEXT,
                        status TEXT DEFAULT 'pending',
                        started_at TEXT,
                        completed_at TEXT,
                        FOREIGN KEY (recording_id) REFERENCES signal_recording(recording_id)
                    )
                ''')
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS analysis_results (
                        result_id TEXT PRIMARY KEY,
                        analysis_id TEXT NOT NULL,
                        user_id INTEGER,
                        user_name TEXT,
                        education_type TEXT,
                        result_type TEXT,
                        result_data TEXT,
                        metrics TEXT,
                        accuracy REAL DEFAULT 0,
                        confidence REAL DEFAULT 0,
                        interpretation TEXT,
                        created_at TEXT,
                        FOREIGN KEY (analysis_id) REFERENCES brain_signal_analysis(analysis_id)
                    )
                ''')
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS bci_control (
                        control_id TEXT PRIMARY KEY,
                        user_id INTEGER,
                        user_name TEXT,
                        education_type TEXT,
                        control_mode TEXT,
                        target_device TEXT,
                        calibration_status TEXT DEFAULT 'calibrating',
                        accuracy REAL DEFAULT 0,
                        last_used TEXT,
                        status TEXT DEFAULT 'active',
                        created_at TEXT,
                        updated_at TEXT
                    )
                ''')
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS control_sessions (
                        session_id TEXT PRIMARY KEY,
                        control_id TEXT NOT NULL,
                        user_id INTEGER,
                        user_name TEXT,
                        education_type TEXT,
                        control_mode TEXT,
                        start_time TEXT,
                        end_time TEXT,
                        duration REAL,
                        success_count INTEGER DEFAULT 0,
                        total_attempts INTEGER DEFAULT 0,
                        average_response_time REAL DEFAULT 0,
                        notes TEXT,
                        created_at TEXT,
                        FOREIGN KEY (control_id) REFERENCES bci_control(control_id)
                    )
                ''')
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS neuro_feedback (
                        feedback_id TEXT PRIMARY KEY,
                        user_id INTEGER,
                        user_name TEXT,
                        education_type TEXT,
                        feedback_type TEXT,
                        target_parameter TEXT,
                        threshold_low REAL,
                        threshold_high REAL,
                        training_goal TEXT,
                        session_count INTEGER DEFAULT 0,
                        progress REAL DEFAULT 0,
                        status TEXT DEFAULT 'active',
                        created_at TEXT,
                        updated_at TEXT
                    )
                ''')
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS feedback_sessions (
                        session_id TEXT PRIMARY KEY,
                        feedback_id TEXT NOT NULL,
                        user_id INTEGER,
                        user_name TEXT,
                        education_type TEXT,
                        start_time TEXT,
                        end_time TEXT,
                        duration REAL,
                        target_value REAL,
                        achieved_value REAL,
                        success_rate REAL DEFAULT 0,
                        notes TEXT,
                        created_at TEXT,
                        FOREIGN KEY (feedback_id) REFERENCES neuro_feedback(feedback_id)
                    )
                ''')
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS bci_applications (
                        app_id TEXT PRIMARY KEY,
                        app_name TEXT NOT NULL,
                        application_type TEXT,
                        education_type TEXT,
                        description TEXT,
                        target_users TEXT,
                        required_devices TEXT,
                        complexity TEXT DEFAULT 'medium',
                        status TEXT DEFAULT 'active',
                        created_at TEXT,
                        updated_at TEXT
                    )
                ''')
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS application_data (
                        data_id TEXT PRIMARY KEY,
                        app_id TEXT NOT NULL,
                        user_id INTEGER,
                        user_name TEXT,
                        education_type TEXT,
                        session_id TEXT,
                        data_type TEXT,
                        data_content TEXT,
                        timestamp TEXT,
                        created_at TEXT,
                        FOREIGN KEY (app_id) REFERENCES bci_applications(app_id)
                    )
                ''')
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS brain_computer_interface (
                        interface_id TEXT PRIMARY KEY,
                        interface_name TEXT NOT NULL,
                        bci_type TEXT,
                        education_type TEXT,
                        description TEXT,
                        protocol TEXT,
                        connection_status TEXT DEFAULT 'disconnected',
                        last_connected TEXT,
                        created_at TEXT,
                        updated_at TEXT
                    )
                ''')
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS interface_logs (
                        log_id TEXT PRIMARY KEY,
                        interface_id TEXT NOT NULL,
                        log_type TEXT,
                        message TEXT,
                        timestamp TEXT,
                        level TEXT DEFAULT 'info',
                        FOREIGN KEY (interface_id) REFERENCES brain_computer_interface(interface_id)
                    )
                ''')
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS cognitive_enhancement (
                        enhancement_id TEXT PRIMARY KEY,
                        user_id INTEGER,
                        user_name TEXT,
                        education_type TEXT,
                        target_ability TEXT,
                        program_name TEXT,
                        duration_weeks INTEGER DEFAULT 4,
                        current_week INTEGER DEFAULT 1,
                        baseline_score REAL,
                        current_score REAL,
                        progress REAL DEFAULT 0,
                        status TEXT DEFAULT 'active',
                        created_at TEXT,
                        updated_at TEXT
                    )
                ''')
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS enhancement_records (
                        record_id TEXT PRIMARY KEY,
                        enhancement_id TEXT NOT NULL,
                        user_id INTEGER,
                        user_name TEXT,
                        education_type TEXT,
                        week INTEGER,
                        training_date TEXT,
                        score REAL,
                        improvement REAL DEFAULT 0,
                        notes TEXT,
                        created_at TEXT,
                        FOREIGN KEY (enhancement_id) REFERENCES cognitive_enhancement(enhancement_id)
                    )
                ''')
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS bci_education (
                        course_id TEXT PRIMARY KEY,
                        course_name TEXT NOT NULL,
                        education_type TEXT,
                        scenario TEXT,
                        description TEXT,
                        target_age_group TEXT,
                        duration_hours REAL DEFAULT 10,
                        required_devices TEXT,
                        instructor_id INTEGER,
                        instructor_name TEXT,
                        max_students INTEGER DEFAULT 10,
                        enrolled_count INTEGER DEFAULT 0,
                        status TEXT DEFAULT 'active',
                        created_at TEXT,
                        updated_at TEXT
                    )
                ''')
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS education_sessions (
                        session_id TEXT PRIMARY KEY,
                        course_id TEXT NOT NULL,
                        user_id INTEGER,
                        user_name TEXT,
                        education_type TEXT,
                        session_date TEXT,
                        session_number INTEGER,
                        duration REAL,
                        activity_type TEXT,
                        performance_data TEXT,
                        progress REAL DEFAULT 0,
                        created_at TEXT,
                        FOREIGN KEY (course_id) REFERENCES bci_education(course_id)
                    )
                ''')
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS bci_research (
                        project_id TEXT PRIMARY KEY,
                        project_name TEXT NOT NULL,
                        education_type TEXT,
                        description TEXT,
                        research_type TEXT,
                        principal_investigator TEXT,
                        start_date TEXT,
                        end_date TEXT,
                        status TEXT DEFAULT 'active',
                        participant_count INTEGER DEFAULT 0,
                        data_points INTEGER DEFAULT 0,
                        created_at TEXT,
                        updated_at TEXT
                    )
                ''')
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS research_projects (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        project_id TEXT NOT NULL,
                        participant_id INTEGER,
                        participant_name TEXT,
                        education_type TEXT,
                        group_type TEXT DEFAULT 'control',
                        data_collected INTEGER DEFAULT 0,
                        consent_status TEXT DEFAULT 'pending',
                        joined_at TEXT,
                        FOREIGN KEY (project_id) REFERENCES bci_research(project_id)
                    )
                ''')
                conn.commit()
                logger.info('教育脑机接口服务数据库初始化完成')
        except Exception as e:
            logger.error(f'数据库初始化失败: {e}')

    # ========== 脑机接口基础 ==========

    def create_interface(self, interface_name: str, bci_type: str,
                          education_type: str = 'adult', **kwargs) -> Dict[str, Any]:
        try:
            interface_id = f"bci_{uuid.uuid4().hex[:12]}"
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('''
                        INSERT INTO brain_computer_interface (
                            interface_id, interface_name, bci_type,
                            education_type, description, protocol,
                            connection_status, created_at, updated_at
                        ) VALUES (?, ?, ?, ?, ?, ?, 'disconnected', ?, ?)
                    ''', (interface_id, interface_name, bci_type,
                          education_type, kwargs.get('description'),
                          kwargs.get('protocol', 'BCI2000'), now, now))
                    conn.commit()
                    logger.info(f'创建脑机接口: {interface_name} ({interface_id})')
                    return {'success': True, 'interface_id': interface_id}
        except Exception as e:
            logger.error(f'创建脑机接口失败: {e}')
            return {'success': False, 'error': str(e)}

    def connect_interface(self, interface_id: str) -> Dict[str, Any]:
        try:
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('UPDATE brain_computer_interface SET connection_status = ?, last_connected = ?, updated_at = ? WHERE interface_id = ?',
                                 ('connected', now, now, interface_id))
                    if cursor.rowcount > 0:
                        self._log_interface(interface_id, 'connection', f'接口已连接')
                        conn.commit()
                        return {'success': True, 'status': 'connected'}
                    return {'success': False, 'error': '接口不存在'}
        except Exception as e:
            logger.error(f'连接脑机接口失败: {e}')
            return {'success': False, 'error': str(e)}

    def disconnect_interface(self, interface_id: str) -> Dict[str, Any]:
        try:
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('UPDATE brain_computer_interface SET connection_status = ?, updated_at = ? WHERE interface_id = ?',
                                 ('disconnected', now, interface_id))
                    if cursor.rowcount > 0:
                        self._log_interface(interface_id, 'disconnection', f'接口已断开')
                        conn.commit()
                        return {'success': True, 'status': 'disconnected'}
                    return {'success': False, 'error': '接口不存在'}
        except Exception as e:
            logger.error(f'断开脑机接口失败: {e}')
            return {'success': False, 'error': str(e)}

    def _log_interface(self, interface_id: str, log_type: str, message: str):
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    INSERT INTO interface_logs (log_id, interface_id, log_type, message, timestamp)
                    VALUES (?, ?, ?, ?, ?)
                ''', (f"log_{uuid.uuid4().hex[:12]}", interface_id, log_type, message, datetime.now().isoformat()))
                conn.commit()
        except Exception as e:
            logger.error(f'记录接口日志失败: {e}')

    def configure_interface(self, interface_id: str, **kwargs) -> Dict[str, Any]:
        try:
            now = datetime.now().isoformat()
            updates = []
            params = []
            for key, value in kwargs.items():
                if key in ['protocol', 'description']:
                    updates.append(f"{key} = ?")
                    params.append(value)
            if updates:
                params.extend([now, interface_id])
                with self._lock:
                    with self._get_connection() as conn:
                        cursor = conn.cursor()
                        cursor.execute(f'UPDATE brain_computer_interface SET {", ".join(updates)}, updated_at = ? WHERE interface_id = ?', params)
                        if cursor.rowcount > 0:
                            conn.commit()
                            return {'success': True}
                        return {'success': False, 'error': '接口不存在'}
            return {'success': False, 'error': '无有效配置参数'}
        except Exception as e:
            logger.error(f'配置脑机接口失败: {e}')
            return {'success': False, 'error': str(e)}

    # ========== EEG采集 ==========

    def start_recording(self, device_id: str, user_id: int,
                         user_name: str = None, education_type: str = 'adult',
                         signal_type: str = 'eeg') -> Dict[str, Any]:
        try:
            recording_id = f"rec_{uuid.uuid4().hex[:12]}"
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('SELECT status FROM bci_devices WHERE device_id = ?', (device_id,))
                    device = cursor.fetchone()
                    if not device:
                        return {'success': False, 'error': '设备不存在'}
                    if device[0] != 'available':
                        return {'success': False, 'error': '设备不可用'}
                    cursor.execute('''
                        INSERT INTO signal_recording (
                            recording_id, device_id, user_id, user_name,
                            signal_type, education_type, start_time, status, created_at
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, 'recording', ?)
                    ''', (recording_id, device_id, user_id, user_name, signal_type, education_type, now, now))
                    cursor.execute('UPDATE bci_devices SET status = ? WHERE device_id = ?', ('recording', device_id))
                    conn.commit()
                    logger.info(f'开始信号采集: {recording_id}')
                    return {'success': True, 'recording_id': recording_id}
        except Exception as e:
            logger.error(f'开始采集失败: {e}')
            return {'success': False, 'error': str(e)}

    def stop_recording(self, recording_id: str) -> Dict[str, Any]:
        try:
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('SELECT device_id, start_time FROM signal_recording WHERE recording_id = ? AND status = ?', (recording_id, 'recording'))
                    recording = cursor.fetchone()
                    if not recording:
                        return {'success': False, 'error': '采集不存在或已停止'}
                    start_time = datetime.fromisoformat(recording[1])
                    end_time = datetime.fromisoformat(now)
                    duration = (end_time - start_time).total_seconds()
                    cursor.execute('UPDATE signal_recording SET end_time = ?, duration = ?, status = ? WHERE recording_id = ?',
                                 (now, duration, 'completed', recording_id))
                    cursor.execute('UPDATE bci_devices SET status = ? WHERE device_id = ?', ('available', recording[0]))
                    conn.commit()
                    return {'success': True, 'duration': round(duration, 2)}
        except Exception as e:
            logger.error(f'停止采集失败: {e}')
            return {'success': False, 'error': str(e)}

    def save_recording_data(self, recording_id: str, channel_data: str,
                             **kwargs) -> Dict[str, Any]:
        try:
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('UPDATE signal_recording SET channel_data = ?, file_path = ?, signal_quality = ?, sample_count = ?, updated_at = ? WHERE recording_id = ?',
                                 (channel_data, kwargs.get('file_path'), kwargs.get('signal_quality', 0), kwargs.get('sample_count', 0), now, recording_id))
                    if cursor.rowcount > 0:
                        conn.commit()
                        return {'success': True}
                    return {'success': False, 'error': '采集记录不存在'}
        except Exception as e:
            logger.error(f'保存采集数据失败: {e}')
            return {'success': False, 'error': str(e)}

    def get_recording_status(self, recording_id: str) -> Dict[str, Any]:
        try:
            with self._get_connection() as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                cursor.execute('SELECT * FROM signal_recording WHERE recording_id = ?', (recording_id,))
                recording = cursor.fetchone()
                if recording:
                    return {'success': True, 'recording': dict(recording)}
                return {'success': False, 'error': '采集不存在'}
        except Exception as e:
            logger.error(f'获取采集状态失败: {e}')
            return {'success': False, 'error': str(e)}

    # ========== 脑信号分析 ==========

    def create_analysis(self, recording_id: str, analysis_method: str,
                         user_id: int, user_name: str = None,
                         education_type: str = 'adult', **kwargs) -> Dict[str, Any]:
        try:
            analysis_id = f"ana_{uuid.uuid4().hex[:12]}"
            now = datetime.now().isoformat()
            params = json.dumps(kwargs) if kwargs else '{}'
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('SELECT user_id, education_type FROM signal_recording WHERE recording_id = ?', (recording_id,))
                    recording = cursor.fetchone()
                    if not recording:
                        return {'success': False, 'error': '采集记录不存在'}
                    cursor.execute('''
                        INSERT INTO brain_signal_analysis (
                            analysis_id, recording_id, user_id, user_name,
                            education_type, analysis_method, parameters,
                            status, started_at
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, 'running', ?)
                    ''', (analysis_id, recording_id, user_id or recording[0], user_name, education_type or recording[1], analysis_method, params, now))
                    conn.commit()
                    return {'success': True, 'analysis_id': analysis_id}
        except Exception as e:
            logger.error(f'创建分析任务失败: {e}')
            return {'success': False, 'error': str(e)}

    def complete_analysis(self, analysis_id: str, result_type: str,
                           result_data: str, **kwargs) -> Dict[str, Any]:
        try:
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('UPDATE brain_signal_analysis SET status = ?, completed_at = ? WHERE analysis_id = ?',
                                 ('completed', now, analysis_id))
                    if cursor.rowcount == 0:
                        return {'success': False, 'error': '分析任务不存在'}
                    result_id = f"res_{uuid.uuid4().hex[:12]}"
                    cursor.execute('''
                        INSERT INTO analysis_results (
                            result_id, analysis_id, user_id, user_name,
                            education_type, result_type, result_data,
                            metrics, accuracy, confidence, interpretation,
                            created_at
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    ''', (result_id, analysis_id, kwargs.get('user_id'), kwargs.get('user_name'),
                          kwargs.get('education_type', 'adult'), result_type, result_data,
                          kwargs.get('metrics', '{}'), kwargs.get('accuracy', 0),
                          kwargs.get('confidence', 0), kwargs.get('interpretation'), now))
                    conn.commit()
                    return {'success': True, 'result_id': result_id}
        except Exception as e:
            logger.error(f'完成分析任务失败: {e}')
            return {'success': False, 'error': str(e)}

    def get_analysis_result(self, result_id: str) -> Dict[str, Any]:
        try:
            with self._get_connection() as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                cursor.execute('SELECT * FROM analysis_results WHERE result_id = ?', (result_id,))
                result = cursor.fetchone()
                if result:
                    return {'success': True, 'result': dict(result)}
                return {'success': False, 'error': '分析结果不存在'}
        except Exception as e:
            logger.error(f'获取分析结果失败: {e}')
            return {'success': False, 'error': str(e)}

    def list_analysis_results(self, user_id: int = None, education_type: str = None,
                               page: int = 1, page_size: int = 20) -> Dict[str, Any]:
        try:
            with self._get_connection() as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                query = 'SELECT * FROM analysis_results WHERE 1=1'
                params = []
                if user_id:
                    query += ' AND user_id = ?'
                    params.append(user_id)
                if education_type:
                    query += ' AND education_type = ?'
                    params.append(education_type)
                cursor.execute(f'SELECT COUNT(*) as cnt FROM ({query})', params)
                total = cursor.fetchone()['cnt']
                query += ' ORDER BY created_at DESC LIMIT ? OFFSET ?'
                params.extend([page_size, (page - 1) * page_size])
                cursor.execute(query, params)
                results = [dict(r) for r in cursor.fetchall()]
                return {'success': True, 'results': results, 'total': total, 'page': page, 'page_size': page_size}
        except Exception as e:
            logger.error(f'获取分析结果列表失败: {e}')
            return {'success': False, 'error': str(e)}

    # ========== 思维控制 ==========

    def create_control(self, user_id: int, control_mode: str,
                        education_type: str = 'adult', **kwargs) -> Dict[str, Any]:
        try:
            control_id = f"ctl_{uuid.uuid4().hex[:12]}"
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('''
                        INSERT INTO bci_control (
                            control_id, user_id, user_name, education_type,
                            control_mode, target_device, calibration_status,
                            accuracy, status, created_at, updated_at
                        ) VALUES (?, ?, ?, ?, ?, ?, 'calibrating', 0, 'active', ?, ?)
                    ''', (control_id, user_id, kwargs.get('user_name'), education_type,
                          control_mode, kwargs.get('target_device'), now, now))
                    conn.commit()
                    logger.info(f'创建思维控制: {control_id}')
                    return {'success': True, 'control_id': control_id}
        except Exception as e:
            logger.error(f'创建思维控制失败: {e}')
            return {'success': False, 'error': str(e)}

    def calibrate_control(self, control_id: str, accuracy: float) -> Dict[str, Any]:
        try:
            now = datetime.now().isoformat()
            status = 'calibrated' if accuracy >= 70 else 'calibrating'
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('UPDATE bci_control SET calibration_status = ?, accuracy = ?, updated_at = ? WHERE control_id = ?',
                                 (status, accuracy, now, control_id))
                    if cursor.rowcount > 0:
                        conn.commit()
                        return {'success': True, 'calibration_status': status, 'accuracy': accuracy}
                    return {'success': False, 'error': '控制不存在'}
        except Exception as e:
            logger.error(f'校准思维控制失败: {e}')
            return {'success': False, 'error': str(e)}

    def start_control_session(self, control_id: str, user_id: int,
                               education_type: str = 'adult', **kwargs) -> Dict[str, Any]:
        try:
            session_id = f"csn_{uuid.uuid4().hex[:12]}"
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('SELECT control_mode, calibration_status FROM bci_control WHERE control_id = ?', (control_id,))
                    control = cursor.fetchone()
                    if not control:
                        return {'success': False, 'error': '控制不存在'}
                    if control[1] != 'calibrated':
                        return {'success': False, 'error': '控制未校准'}
                    cursor.execute('''
                        INSERT INTO control_sessions (
                            session_id, control_id, user_id, user_name,
                            education_type, control_mode, start_time, status
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, 'active')
                    ''', (session_id, control_id, user_id, kwargs.get('user_name'), education_type, control[0], now))
                    conn.commit()
                    return {'success': True, 'session_id': session_id}
        except Exception as e:
            logger.error(f'开始控制会话失败: {e}')
            return {'success': False, 'error': str(e)}

    def end_control_session(self, session_id: str, **kwargs) -> Dict[str, Any]:
        try:
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('SELECT start_time FROM control_sessions WHERE session_id = ?', (session_id,))
                    session = cursor.fetchone()
                    if not session:
                        return {'success': False, 'error': '会话不存在'}
                    duration = (datetime.fromisoformat(now) - datetime.fromisoformat(session[0])).total_seconds()
                    cursor.execute('UPDATE control_sessions SET end_time = ?, duration = ?, success_count = ?, total_attempts = ?, average_response_time = ? WHERE session_id = ?',
                                 (now, duration, kwargs.get('success_count', 0), kwargs.get('total_attempts', 0), kwargs.get('average_response_time', 0), session_id))
                    cursor.execute('UPDATE bci_control SET last_used = ?, updated_at = ? WHERE control_id = (SELECT control_id FROM control_sessions WHERE session_id = ?)',
                                 (now, now, session_id))
                    conn.commit()
                    return {'success': True, 'duration': round(duration, 2)}
        except Exception as e:
            logger.error(f'结束控制会话失败: {e}')
            return {'success': False, 'error': str(e)}

    # ========== 神经反馈 ==========

    def create_feedback_program(self, user_id: int, feedback_type: str,
                                 education_type: str = 'adult', **kwargs) -> Dict[str, Any]:
        try:
            feedback_id = f"fbk_{uuid.uuid4().hex[:12]}"
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('''
                        INSERT INTO neuro_feedback (
                            feedback_id, user_id, user_name, education_type,
                            feedback_type, target_parameter, threshold_low,
                            threshold_high, training_goal, status, created_at, updated_at
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, 'active', ?, ?)
                    ''', (feedback_id, user_id, kwargs.get('user_name'), education_type,
                          feedback_type, kwargs.get('target_parameter'),
                          kwargs.get('threshold_low', 0), kwargs.get('threshold_high', 100),
                          kwargs.get('training_goal'), now, now))
                    conn.commit()
                    logger.info(f'创建神经反馈: {feedback_id}')
                    return {'success': True, 'feedback_id': feedback_id}
        except Exception as e:
            logger.error(f'创建神经反馈失败: {e}')
            return {'success': False, 'error': str(e)}

    def start_feedback_session(self, feedback_id: str, user_id: int,
                                education_type: str = 'adult') -> Dict[str, Any]:
        try:
            session_id = f"fbs_{uuid.uuid4().hex[:12]}"
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('SELECT user_name FROM neuro_feedback WHERE feedback_id = ?', (feedback_id,))
                    feedback = cursor.fetchone()
                    if not feedback:
                        return {'success': False, 'error': '反馈程序不存在'}
                    cursor.execute('''
                        INSERT INTO feedback_sessions (
                            session_id, feedback_id, user_id, user_name,
                            education_type, start_time
                        ) VALUES (?, ?, ?, ?, ?, ?)
                    ''', (session_id, feedback_id, user_id, feedback[0], education_type, now))
                    conn.commit()
                    return {'success': True, 'session_id': session_id}
        except Exception as e:
            logger.error(f'开始反馈会话失败: {e}')
            return {'success': False, 'error': str(e)}

    def end_feedback_session(self, session_id: str, **kwargs) -> Dict[str, Any]:
        try:
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('SELECT start_time, feedback_id FROM feedback_sessions WHERE session_id = ?', (session_id,))
                    session = cursor.fetchone()
                    if not session:
                        return {'success': False, 'error': '会话不存在'}
                    duration = (datetime.fromisoformat(now) - datetime.fromisoformat(session[0])).total_seconds()
                    cursor.execute('UPDATE feedback_sessions SET end_time = ?, duration = ?, target_value = ?, achieved_value = ?, success_rate = ?, notes = ? WHERE session_id = ?',
                                 (now, duration, kwargs.get('target_value', 0), kwargs.get('achieved_value', 0), kwargs.get('success_rate', 0), kwargs.get('notes'), session_id))
                    cursor.execute('UPDATE neuro_feedback SET session_count = session_count + 1, updated_at = ? WHERE feedback_id = ?', (now, session[1]))
                    conn.commit()
                    return {'success': True, 'duration': round(duration, 2)}
        except Exception as e:
            logger.error(f'结束反馈会话失败: {e}')
            return {'success': False, 'error': str(e)}

    def update_feedback_progress(self, feedback_id: str, progress: float) -> Dict[str, Any]:
        try:
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('UPDATE neuro_feedback SET progress = ?, updated_at = ? WHERE feedback_id = ?',
                                 (progress, now, feedback_id))
                    if cursor.rowcount > 0:
                        conn.commit()
                        return {'success': True, 'progress': progress}
                    return {'success': False, 'error': '反馈程序不存在'}
        except Exception as e:
            logger.error(f'更新反馈进度失败: {e}')
            return {'success': False, 'error': str(e)}

    def get_feedback_stats(self, feedback_id: str) -> Dict[str, Any]:
        try:
            with self._get_connection() as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                cursor.execute('SELECT * FROM neuro_feedback WHERE feedback_id = ?', (feedback_id,))
                feedback = cursor.fetchone()
                if not feedback:
                    return {'success': False, 'error': '反馈程序不存在'}
                cursor.execute('SELECT AVG(success_rate), AVG(duration), COUNT(*) FROM feedback_sessions WHERE feedback_id = ?', (feedback_id,))
                stats = cursor.fetchone()
                return {
                    'success': True,
                    'feedback': dict(feedback),
                    'avg_success_rate': round(stats[0], 2) if stats[0] else 0,
                    'avg_duration': round(stats[1], 2) if stats[1] else 0,
                    'total_sessions': stats[2] or 0
                }
        except Exception as e:
            logger.error(f'获取反馈统计失败: {e}')
            return {'success': False, 'error': str(e)}

    # ========== BCI应用 ==========

    def create_application(self, app_name: str, application_type: str,
                            education_type: str = 'adult', **kwargs) -> Dict[str, Any]:
        try:
            app_id = f"app_{uuid.uuid4().hex[:12]}"
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('''
                        INSERT INTO bci_applications (
                            app_id, app_name, application_type, education_type,
                            description, target_users, required_devices,
                            complexity, status, created_at, updated_at
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, 'active', ?, ?)
                    ''', (app_id, app_name, application_type, education_type,
                          kwargs.get('description'), kwargs.get('target_users'),
                          kwargs.get('required_devices'), kwargs.get('complexity', 'medium'), now, now))
                    conn.commit()
                    logger.info(f'创建BCI应用: {app_name} ({app_id})')
                    return {'success': True, 'app_id': app_id}
        except Exception as e:
            logger.error(f'创建BCI应用失败: {e}')
            return {'success': False, 'error': str(e)}

    def configure_application(self, app_id: str, **kwargs) -> Dict[str, Any]:
        try:
            now = datetime.now().isoformat()
            updates = []
            params = []
            for key, value in kwargs.items():
                if key in ['description', 'target_users', 'required_devices', 'complexity']:
                    updates.append(f"{key} = ?")
                    params.append(value)
            if updates:
                params.extend([now, app_id])
                with self._lock:
                    with self._get_connection() as conn:
                        cursor = conn.cursor()
                        cursor.execute(f'UPDATE bci_applications SET {", ".join(updates)}, updated_at = ? WHERE app_id = ?', params)
                        if cursor.rowcount > 0:
                            conn.commit()
                            return {'success': True}
                        return {'success': False, 'error': '应用不存在'}
            return {'success': False, 'error': '无有效配置参数'}
        except Exception as e:
            logger.error(f'配置BCI应用失败: {e}')
            return {'success': False, 'error': str(e)}

    def log_application_data(self, app_id: str, user_id: int,
                              data_type: str, data_content: str,
                              education_type: str = 'adult', **kwargs) -> Dict[str, Any]:
        try:
            data_id = f"dat_{uuid.uuid4().hex[:12]}"
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('''
                        INSERT INTO application_data (
                            data_id, app_id, user_id, user_name,
                            education_type, session_id, data_type,
                            data_content, timestamp, created_at
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    ''', (data_id, app_id, user_id, kwargs.get('user_name'),
                          education_type, kwargs.get('session_id'),
                          data_type, data_content, now, now))
                    conn.commit()
                    return {'success': True, 'data_id': data_id}
        except Exception as e:
            logger.error(f'记录应用数据失败: {e}')
            return {'success': False, 'error': str(e)}

    def list_applications(self, education_type: str = None, status: str = 'active',
                           page: int = 1, page_size: int = 20) -> Dict[str, Any]:
        try:
            with self._get_connection() as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                query = 'SELECT * FROM bci_applications WHERE 1=1'
                params = []
                if education_type:
                    query += ' AND education_type = ?'
                    params.append(education_type)
                if status:
                    query += ' AND status = ?'
                    params.append(status)
                cursor.execute(f'SELECT COUNT(*) as cnt FROM ({query})', params)
                total = cursor.fetchone()['cnt']
                query += ' ORDER BY created_at DESC LIMIT ? OFFSET ?'
                params.extend([page_size, (page - 1) * page_size])
                cursor.execute(query, params)
                apps = [dict(a) for a in cursor.fetchall()]
                return {'success': True, 'applications': apps, 'total': total, 'page': page, 'page_size': page_size}
        except Exception as e:
            logger.error(f'获取应用列表失败: {e}')
            return {'success': False, 'error': str(e)}

    # ========== 设备管理 ==========

    def register_device(self, device_name: str, device_type: str,
                         hardware_category: str, education_type: str = 'adult',
                         **kwargs) -> Dict[str, Any]:
        try:
            device_id = f"dev_{uuid.uuid4().hex[:12]}"
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('''
                        INSERT INTO bci_devices (
                            device_id, device_name, device_type, hardware_category,
                            manufacturer, model, channel_count, signal_type,
                            sampling_rate, wireless, battery_life,
                            firmware_version, status, location,
                            education_type, created_at, updated_at
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'available', ?, ?, ?, ?)
                    ''', (device_id, device_name, device_type, hardware_category,
                          kwargs.get('manufacturer'), kwargs.get('model'),
                          kwargs.get('channel_count', 8), kwargs.get('signal_type', 'eeg'),
                          kwargs.get('sampling_rate', 250), kwargs.get('wireless', 1),
                          kwargs.get('battery_life', 4), kwargs.get('firmware_version'),
                          kwargs.get('location'), education_type, now, now))
                    conn.commit()
                    logger.info(f'注册设备: {device_name} ({device_id})')
                    return {'success': True, 'device_id': device_id}
        except Exception as e:
            logger.error(f'注册设备失败: {e}')
            return {'success': False, 'error': str(e)}

    def assign_device(self, device_id: str, user_id: int, user_name: str = None) -> Dict[str, Any]:
        try:
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('SELECT status FROM bci_devices WHERE device_id = ?', (device_id,))
                    device = cursor.fetchone()
                    if not device:
                        return {'success': False, 'error': '设备不存在'}
                    if device[0] != 'available':
                        return {'success': False, 'error': '设备不可分配'}
                    cursor.execute('INSERT OR REPLACE INTO device_registry (device_id, user_id, user_name, register_date) VALUES (?, ?, ?, ?)',
                                 (device_id, user_id, user_name, now[:10]))
                    cursor.execute('UPDATE bci_devices SET status = ? WHERE device_id = ?', ('assigned', device_id))
                    conn.commit()
                    return {'success': True}
        except Exception as e:
            logger.error(f'分配设备失败: {e}')
            return {'success': False, 'error': str(e)}

    def unassign_device(self, device_id: str) -> Dict[str, Any]:
        try:
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('UPDATE device_registry SET unregister_date = ? WHERE device_id = ? AND unregister_date IS NULL', (now[:10], device_id))
                    cursor.execute('UPDATE bci_devices SET status = ? WHERE device_id = ?', ('available', device_id))
                    conn.commit()
                    return {'success': True}
        except Exception as e:
            logger.error(f'取消设备分配失败: {e}')
            return {'success': False, 'error': str(e)}

    def update_device_firmware(self, device_id: str, firmware_version: str) -> Dict[str, Any]:
        try:
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('UPDATE bci_devices SET firmware_version = ?, updated_at = ? WHERE device_id = ?',
                                 (firmware_version, now, device_id))
                    if cursor.rowcount > 0:
                        conn.commit()
                        return {'success': True, 'firmware_version': firmware_version}
                    return {'success': False, 'error': '设备不存在'}
        except Exception as e:
            logger.error(f'更新设备固件失败: {e}')
            return {'success': False, 'error': str(e)}

    # ========== 教育应用 ==========

    def create_education_course(self, course_name: str, education_type: str,
                                 scenario: str, **kwargs) -> Dict[str, Any]:
        try:
            course_id = f"edu_{uuid.uuid4().hex[:12]}"
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('''
                        INSERT INTO bci_education (
                            course_id, course_name, education_type, scenario,
                            description, target_age_group, duration_hours,
                            required_devices, instructor_id, instructor_name,
                            max_students, enrolled_count, status,
                            created_at, updated_at
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 0, 'active', ?, ?)
                    ''', (course_id, course_name, education_type, scenario,
                          kwargs.get('description'), kwargs.get('target_age_group'),
                          kwargs.get('duration_hours', 10), kwargs.get('required_devices'),
                          kwargs.get('instructor_id'), kwargs.get('instructor_name'),
                          kwargs.get('max_students', 10), now, now))
                    conn.commit()
                    logger.info(f'创建BCI教育课程: {course_name} ({course_id})')
                    return {'success': True, 'course_id': course_id}
        except Exception as e:
            logger.error(f'创建教育课程失败: {e}')
            return {'success': False, 'error': str(e)}

    def enroll_course(self, course_id: str, user_id: int, user_name: str = None) -> Dict[str, Any]:
        try:
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('SELECT max_students, enrolled_count, status FROM bci_education WHERE course_id = ?', (course_id,))
                    course = cursor.fetchone()
                    if not course:
                        return {'success': False, 'error': '课程不存在'}
                    if course[2] != 'active':
                        return {'success': False, 'error': '课程不开放'}
                    if course[0] and course[1] >= course[0]:
                        return {'success': False, 'error': '名额已满'}
                    cursor.execute('UPDATE bci_education SET enrolled_count = enrolled_count + 1, updated_at = ? WHERE course_id = ?', (now, course_id))
                    conn.commit()
                    return {'success': True}
        except Exception as e:
            logger.error(f'选课失败: {e}')
            return {'success': False, 'error': str(e)}

    def create_education_session(self, course_id: str, user_id: int,
                                  session_date: str, session_number: int,
                                  education_type: str = 'adult', **kwargs) -> Dict[str, Any]:
        try:
            session_id = f"eds_{uuid.uuid4().hex[:12]}"
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('''
                        INSERT INTO education_sessions (
                            session_id, course_id, user_id, user_name,
                            education_type, session_date, session_number,
                            duration, activity_type, performance_data,
                            progress, created_at
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    ''', (session_id, course_id, user_id, kwargs.get('user_name'),
                          education_type, session_date, session_number,
                          kwargs.get('duration', 0), kwargs.get('activity_type'),
                          kwargs.get('performance_data', '{}'), kwargs.get('progress', 0), now))
                    conn.commit()
                    return {'success': True, 'session_id': session_id}
        except Exception as e:
            logger.error(f'创建教育会话失败: {e}')
            return {'success': False, 'error': str(e)}

    def update_session_progress(self, session_id: str, progress: float,
                                 **kwargs) -> Dict[str, Any]:
        try:
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('UPDATE education_sessions SET progress = ?, duration = ?, performance_data = ?, updated_at = ? WHERE session_id = ?',
                                 (progress, kwargs.get('duration', 0), kwargs.get('performance_data', '{}'), now, session_id))
                    if cursor.rowcount > 0:
                        conn.commit()
                        return {'success': True, 'progress': progress}
                    return {'success': False, 'error': '会话不存在'}
        except Exception as e:
            logger.error(f'更新会话进度失败: {e}')
            return {'success': False, 'error': str(e)}

    # ========== 研究管理 ==========

    def create_research_project(self, project_name: str, research_type: str,
                                 education_type: str = 'adult', **kwargs) -> Dict[str, Any]:
        try:
            project_id = f"rsp_{uuid.uuid4().hex[:12]}"
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('''
                        INSERT INTO bci_research (
                            project_id, project_name, education_type,
                            description, research_type, principal_investigator,
                            start_date, end_date, status, created_at, updated_at
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, 'active', ?, ?)
                    ''', (project_id, project_name, education_type,
                          kwargs.get('description'), research_type,
                          kwargs.get('principal_investigator'),
                          kwargs.get('start_date', now[:10]), kwargs.get('end_date'), now, now))
                    conn.commit()
                    logger.info(f'创建研究项目: {project_name} ({project_id})')
                    return {'success': True, 'project_id': project_id}
        except Exception as e:
            logger.error(f'创建研究项目失败: {e}')
            return {'success': False, 'error': str(e)}

    def add_participant(self, project_id: str, participant_id: int,
                         participant_name: str = None, education_type: str = 'adult',
                         group_type: str = 'control') -> Dict[str, Any]:
        try:
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('INSERT OR IGNORE INTO research_projects (project_id, participant_id, participant_name, education_type, group_type, consent_status, joined_at) VALUES (?, ?, ?, ?, ?, ?, ?)',
                                 (project_id, participant_id, participant_name, education_type, group_type, 'pending', now))
                    if cursor.rowcount > 0:
                        cursor.execute('UPDATE bci_research SET participant_count = participant_count + 1, updated_at = ? WHERE project_id = ?', (now, project_id))
                        conn.commit()
                        return {'success': True}
                    return {'success': False, 'error': '参与者已加入'}
        except Exception as e:
            logger.error(f'添加参与者失败: {e}')
            return {'success': False, 'error': str(e)}

    def record_research_data(self, project_id: str, participant_id: int,
                              data_points: int, education_type: str = 'adult') -> Dict[str, Any]:
        try:
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('UPDATE research_projects SET data_collected = data_collected + ? WHERE project_id = ? AND participant_id = ?',
                                 (data_points, project_id, participant_id))
                    cursor.execute('UPDATE bci_research SET data_points = data_points + ?, updated_at = ? WHERE project_id = ?',
                                 (data_points, now, project_id))
                    conn.commit()
                    return {'success': True}
        except Exception as e:
            logger.error(f'记录研究数据失败: {e}')
            return {'success': False, 'error': str(e)}

    # ========== 认知增强 ==========

    def create_enhancement_program(self, user_id: int, target_ability: str,
                                    program_name: str, education_type: str = 'adult',
                                    **kwargs) -> Dict[str, Any]:
        try:
            enhancement_id = f"enh_{uuid.uuid4().hex[:12]}"
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('''
                        INSERT INTO cognitive_enhancement (
                            enhancement_id, user_id, user_name, education_type,
                            target_ability, program_name, duration_weeks,
                            current_week, baseline_score, status,
                            created_at, updated_at
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, 1, ?, 'active', ?, ?)
                    ''', (enhancement_id, user_id, kwargs.get('user_name'), education_type,
                          target_ability, program_name, kwargs.get('duration_weeks', 4),
                          kwargs.get('baseline_score', 0), now, now))
                    conn.commit()
                    return {'success': True, 'enhancement_id': enhancement_id}
        except Exception as e:
            logger.error(f'创建认知增强项目失败: {e}')
            return {'success': False, 'error': str(e)}

    def record_enhancement_score(self, enhancement_id: str, week: int,
                                  score: float, education_type: str = 'adult',
                                  **kwargs) -> Dict[str, Any]:
        try:
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('SELECT baseline_score, current_score FROM cognitive_enhancement WHERE enhancement_id = ?', (enhancement_id,))
                    enhancement = cursor.fetchone()
                    if not enhancement:
                        return {'success': False, 'error': '增强项目不存在'}
                    improvement = score - enhancement[0] if enhancement[0] else 0
                    record_id = f"rec_{uuid.uuid4().hex[:12]}"
                    cursor.execute('''
                        INSERT INTO enhancement_records (
                            record_id, enhancement_id, user_id, user_name,
                            education_type, week, training_date, score,
                            improvement, notes, created_at
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    ''', (record_id, enhancement_id, kwargs.get('user_id'), kwargs.get('user_name'),
                          education_type, week, now[:10], score, improvement, kwargs.get('notes'), now))
                    progress = min(100, (score / (enhancement[0] * 1.5)) * 100) if enhancement[0] > 0 else 0
                    cursor.execute('UPDATE cognitive_enhancement SET current_week = ?, current_score = ?, progress = ?, updated_at = ? WHERE enhancement_id = ?',
                                 (week, score, progress, now, enhancement_id))
                    conn.commit()
                    return {'success': True, 'improvement': improvement, 'progress': round(progress, 2)}
        except Exception as e:
            logger.error(f'记录增强分数失败: {e}')
            return {'success': False, 'error': str(e)}

    # ========== 统计分析 ==========

    def get_bci_statistics(self, education_type: str = None) -> Dict[str, Any]:
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                filters = ''
                params = []
                if education_type:
                    filters = 'WHERE education_type = ?'
                    params.append(education_type)
                cursor.execute(f'SELECT COUNT(*) FROM bci_devices {filters}', params)
                device_count = cursor.fetchone()[0]
                cursor.execute(f'SELECT COUNT(*) FROM signal_recording {filters}', params)
                recording_count = cursor.fetchone()[0]
                cursor.execute(f'SELECT COUNT(*) FROM analysis_results {filters}', params)
                analysis_count = cursor.fetchone()[0]
                cursor.execute(f'SELECT COUNT(*) FROM bci_education {filters}', params)
                course_count = cursor.fetchone()[0]
                cursor.execute(f'SELECT COUNT(*) FROM bci_applications {filters}', params)
                app_count = cursor.fetchone()[0]
                cursor.execute('SELECT AVG(accuracy) FROM analysis_results WHERE accuracy > 0')
                avg_accuracy = cursor.fetchone()[0] or 0
                cursor.execute('SELECT AVG(duration) FROM signal_recording WHERE duration > 0')
                avg_duration = cursor.fetchone()[0] or 0
                return {
                    'success': True,
                    'statistics': {
                        'total_devices': device_count,
                        'total_recordings': recording_count,
                        'total_analyses': analysis_count,
                        'total_courses': course_count,
                        'total_applications': app_count,
                        'avg_analysis_accuracy': round(avg_accuracy, 2),
                        'avg_recording_duration': round(avg_duration, 2),
                        'education_type': education_type or 'all'
                    }
                }
        except Exception as e:
            logger.error(f'获取统计数据失败: {e}')
            return {'success': False, 'error': str(e)}