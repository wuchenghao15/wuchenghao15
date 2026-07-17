#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
MTSCOS 教育量子计算服务 (v15.19.0)
====================================
提供量子计算课程、量子实验、量子编程和量子模拟等综合教育服务。

核心能力：
1. 量子计算基础 - 量子比特、叠加态、纠缠、量子门、量子测量、量子纠错
2. 量子算法 - 肖尔算法、格罗弗算法、量子傅里叶变换、量子相位估计
3. 量子编程 - Qiskit、Cirq、Q#、PennyLane、IBM Q Experience
4. 量子模拟 - 量子化学、材料科学、优化问题、金融建模
5. 量子机器学习 - 量子分类、量子回归、量子聚类、量子神经网络
6. 量子通信 - 量子密钥分发、量子隐形传态、量子网络
7. 量子实验 - 量子设备操作、实验设计、数据采集分析
8. 量子教育资源 - 课程资料、学习路径、评估体系
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
            os.path.join(os.path.dirname(os.path.abspath(__file__)), 'education_quantum_service.log'),
            encoding='utf-8'
        ),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger('EducationQuantum')


# ========== 量子配置 ==========

QUANTUM_CONCEPTS = {
    'qubit': {'name': '量子比特', 'description': '量子计算的基本信息单元，可处于0和1的叠加态', 'complexity': 1},
    'superposition': {'name': '叠加态', 'description': '量子系统同时处于多个状态的能力', 'complexity': 2},
    'entanglement': {'name': '纠缠', 'description': '两个或多个量子比特之间的强关联，测量一个会立即影响另一个', 'complexity': 3},
    'quantum_gate': {'name': '量子门', 'description': '量子电路的基本操作单元，用于变换量子态', 'complexity': 2},
    'measurement': {'name': '量子测量', 'description': '从量子态提取经典信息的过程，会使叠加态坍缩', 'complexity': 2},
    'error_correction': {'name': '量子纠错', 'description': '保护量子信息免受退相干和噪声影响的技术', 'complexity': 5},
    'parallelism': {'name': '量子并行', 'description': '量子计算同时处理多个计算路径的能力', 'complexity': 4},
    'interference': {'name': '量子干涉', 'description': '量子态之间的相互作用，可增强或抵消特定结果', 'complexity': 3}
}

QUANTUM_ALGORITHMS = {
    'shor': {'name': '肖尔算法', 'description': '多项式时间分解大数的量子算法', 'applications': ['密码破解', '数论']},
    'grover': {'name': '格罗弗算法', 'description': '平方根加速的无序搜索算法', 'applications': ['数据库搜索', '优化']},
    'qft': {'name': '量子傅里叶变换', 'description': '量子版本的傅里叶变换，是许多量子算法的基础', 'applications': ['信号处理', '量子相位估计']},
    'qpe': {'name': '量子相位估计', 'description': '估计幺正算子特征值的相位', 'applications': ['量子模拟', '算法设计']},
    'quantum_walk': {'name': '量子行走', 'description': '经典随机行走的量子推广', 'applications': ['搜索', '图论']},
    'qml': {'name': '量子机器学习', 'description': '利用量子计算加速机器学习任务', 'applications': ['分类', '回归', '聚类']}
}

QUANTUM_PROGRAMMING = {
    'qiskit': {'name': 'Qiskit', 'provider': 'IBM', 'type': 'SDK', 'language': 'Python', 'level': ['beginner', 'intermediate', 'advanced']},
    'cirq': {'name': 'Cirq', 'provider': 'Google', 'type': 'SDK', 'language': 'Python', 'level': ['intermediate', 'advanced']},
    'qsharp': {'name': 'Q#', 'provider': 'Microsoft', 'type': 'Language', 'language': 'Q#', 'level': ['beginner', 'intermediate', 'advanced']},
    'pennylane': {'name': 'PennyLane', 'provider': 'Xanadu', 'type': 'SDK', 'language': 'Python', 'level': ['beginner', 'intermediate', 'advanced']},
    'ibmq': {'name': 'IBM Q Experience', 'provider': 'IBM', 'type': 'Platform', 'language': 'Python/Qiskit', 'level': ['beginner', 'intermediate']},
    'google_cirq': {'name': 'Google Cirq', 'provider': 'Google', 'type': 'Platform', 'language': 'Python/Cirq', 'level': ['intermediate', 'advanced']}
}

QUANTUM_SIMULATIONS = {
    'quantum_chemistry': {'name': '量子化学', 'description': '模拟分子和材料的量子行为', 'applications': ['药物发现', '新材料']},
    'materials_science': {'name': '材料科学', 'description': '研究材料的量子特性', 'applications': ['超导材料', '半导体']},
    'optimization': {'name': '优化问题', 'description': '求解组合优化问题', 'applications': ['物流', '金融', '调度']},
    'finance': {'name': '金融建模', 'description': '量子计算在金融领域的应用', 'applications': ['投资组合优化', '风险评估']},
    'biological': {'name': '生物模拟', 'description': '模拟生物系统的量子过程', 'applications': ['蛋白质折叠', 'DNA分析']},
    'drug_discovery': {'name': '药物发现', 'description': '加速新药研发过程', 'applications': ['分子设计', '药效预测']}
}

QUANTUM_ML = {
    'classification': {'name': '量子分类', 'description': '用量子算法进行数据分类', 'complexity': 3},
    'regression': {'name': '量子回归', 'description': '用量子算法进行回归分析', 'complexity': 3},
    'clustering': {'name': '量子聚类', 'description': '用量子算法进行数据聚类', 'complexity': 4},
    'dimensionality_reduction': {'name': '量子降维', 'description': '用量子算法降低数据维度', 'complexity': 4},
    'quantum_nn': {'name': '量子神经网络', 'description': '量子版本的神经网络', 'complexity': 5},
    'quantum_rl': {'name': '量子强化学习', 'description': '量子计算与强化学习的结合', 'complexity': 5}
}

QUANTUM_COMMUNICATION = {
    'qkd': {'name': '量子密钥分发', 'description': '基于量子力学原理的安全密钥传输', 'security_level': 'provably secure'},
    'teleportation': {'name': '量子隐形传态', 'description': '利用纠缠实现量子态的远程传输', 'distance_limit': 'limited by decoherence'},
    'repeater': {'name': '量子中继器', 'description': '延长量子通信距离的设备', 'technology_readiness': 'developing'},
    'quantum_network': {'name': '量子网络', 'description': '连接多个量子节点的网络', 'scale': 'small scale'},
    'quantum_crypto': {'name': '量子加密', 'description': '基于量子原理的加密技术', 'applications': ['secure communication']}
}

QUANTUM_DEVICES = {
    'quantum_computer': {'name': '量子计算机', 'description': '基于量子力学原理的计算设备', 'qubit_count': 'increasing'},
    'quantum_simulator': {'name': '量子模拟器', 'description': '用经典或量子方法模拟量子系统', 'type': ['classical', 'quantum']},
    'quantum_sensor': {'name': '量子传感器', 'description': '利用量子效应进行高精度测量', 'applications': ['navigation', 'imaging']},
    'quantum_processor': {'name': '量子处理器', 'description': '执行量子计算的核心芯片', 'architecture': ['superconducting', 'ion trap']},
    'quantum_chip': {'name': '量子芯片', 'description': '集成量子比特的微型芯片', 'fabrication': ['CMOS', 'specialized']}
}

EDUCATION_LEVELS = {
    'intro': {'name': '入门', 'age_range': '8-14', 'duration_hours': 8, 'prerequisites': None, 'target_knowledge': ['basic physics']},
    'basic': {'name': '基础', 'age_range': '12-18', 'duration_hours': 20, 'prerequisites': ['intro'], 'target_knowledge': ['algebra', 'basic physics']},
    'intermediate': {'name': '中级', 'age_range': '16+', 'duration_hours': 40, 'prerequisites': ['basic'], 'target_knowledge': ['linear algebra', 'calculus', 'physics']},
    'advanced': {'name': '高级', 'age_range': '18+', 'duration_hours': 60, 'prerequisites': ['intermediate'], 'target_knowledge': ['quantum mechanics', 'linear algebra', 'complex analysis']},
    'expert': {'name': '专家', 'age_range': 'graduate', 'duration_hours': 100, 'prerequisites': ['advanced'], 'target_knowledge': ['quantum information', 'complexity theory']},
    'research': {'name': '研究', 'age_range': 'phd', 'duration_hours': 200, 'prerequisites': ['expert'], 'target_knowledge': ['advanced quantum computing', 'research methods']}
}


class EducationQuantumService:
    """教育量子计算服务"""

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
                    CREATE TABLE IF NOT EXISTS quantum_courses (
                        course_id TEXT PRIMARY KEY,
                        course_name TEXT NOT NULL,
                        education_level TEXT,
                        education_type TEXT,
                        description TEXT,
                        duration_hours INTEGER,
                        prerequisites TEXT,
                        target_knowledge TEXT,
                        difficulty TEXT,
                        max_students INTEGER DEFAULT 30,
                        enrolled_count INTEGER DEFAULT 0,
                        status TEXT DEFAULT 'active',
                        created_at TEXT,
                        updated_at TEXT
                    )
                ''')
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS course_modules (
                        module_id TEXT PRIMARY KEY,
                        course_id TEXT NOT NULL,
                        module_name TEXT NOT NULL,
                        module_order INTEGER,
                        duration_hours INTEGER,
                        content TEXT,
                        learning_objectives TEXT,
                        resources TEXT,
                        status TEXT DEFAULT 'active',
                        created_at TEXT,
                        FOREIGN KEY(course_id) REFERENCES quantum_courses(course_id)
                    )
                ''')
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS quantum_experiments (
                        experiment_id TEXT PRIMARY KEY,
                        experiment_name TEXT NOT NULL,
                        education_level TEXT,
                        education_type TEXT,
                        description TEXT,
                        required_devices TEXT,
                        estimated_duration TEXT,
                        safety_requirements TEXT,
                        learning_objectives TEXT,
                        status TEXT DEFAULT 'available',
                        created_at TEXT,
                        updated_at TEXT
                    )
                ''')
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS experiment_sessions (
                        session_id TEXT PRIMARY KEY,
                        experiment_id TEXT NOT NULL,
                        student_id INTEGER NOT NULL,
                        session_date TEXT,
                        start_time TEXT,
                        end_time TEXT,
                        status TEXT DEFAULT 'pending',
                        data_collected TEXT,
                        observations TEXT,
                        conclusion TEXT,
                        grade TEXT,
                        FOREIGN KEY(experiment_id) REFERENCES quantum_experiments(experiment_id)
                    )
                ''')
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS quantum_programs (
                        program_id TEXT PRIMARY KEY,
                        program_name TEXT NOT NULL,
                        programming_language TEXT,
                        education_level TEXT,
                        education_type TEXT,
                        description TEXT,
                        difficulty TEXT,
                        expected_output TEXT,
                        template_code TEXT,
                        status TEXT DEFAULT 'active',
                        created_at TEXT,
                        updated_at TEXT
                    )
                ''')
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS program_submissions (
                        submission_id TEXT PRIMARY KEY,
                        program_id TEXT NOT NULL,
                        student_id INTEGER NOT NULL,
                        submitted_code TEXT,
                        submission_time TEXT,
                        test_results TEXT,
                        grade TEXT,
                        feedback TEXT,
                        status TEXT DEFAULT 'submitted',
                        FOREIGN KEY(program_id) REFERENCES quantum_programs(program_id)
                    )
                ''')
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS quantum_simulation (
                        simulation_id TEXT PRIMARY KEY,
                        simulation_name TEXT NOT NULL,
                        simulation_type TEXT,
                        education_level TEXT,
                        education_type TEXT,
                        description TEXT,
                        parameters TEXT,
                        initial_state TEXT,
                        expected_results TEXT,
                        status TEXT DEFAULT 'configured',
                        created_at TEXT,
                        updated_at TEXT
                    )
                ''')
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS simulation_results (
                        result_id TEXT PRIMARY KEY,
                        simulation_id TEXT NOT NULL,
                        student_id INTEGER NOT NULL,
                        run_parameters TEXT,
                        raw_results TEXT,
                        analysis TEXT,
                        visualizations TEXT,
                        run_time TEXT,
                        status TEXT DEFAULT 'completed',
                        FOREIGN KEY(simulation_id) REFERENCES quantum_simulation(simulation_id)
                    )
                ''')
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS quantum_ml_models (
                        model_id TEXT PRIMARY KEY,
                        model_name TEXT NOT NULL,
                        model_type TEXT,
                        education_level TEXT,
                        education_type TEXT,
                        description TEXT,
                        architecture TEXT,
                        training_data TEXT,
                        hyperparameters TEXT,
                        status TEXT DEFAULT 'trained',
                        created_at TEXT,
                        updated_at TEXT
                    )
                ''')
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS model_training (
                        training_id TEXT PRIMARY KEY,
                        model_id TEXT NOT NULL,
                        student_id INTEGER NOT NULL,
                        training_data TEXT,
                        hyperparameters TEXT,
                        training_metrics TEXT,
                        accuracy REAL,
                        loss REAL,
                        training_time TEXT,
                        status TEXT DEFAULT 'completed',
                        FOREIGN KEY(model_id) REFERENCES quantum_ml_models(model_id)
                    )
                ''')
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS quantum_communication (
                        comm_id TEXT PRIMARY KEY,
                        comm_type TEXT NOT NULL,
                        education_level TEXT,
                        education_type TEXT,
                        description TEXT,
                        security_level TEXT,
                        distance_range TEXT,
                        equipment_required TEXT,
                        status TEXT DEFAULT 'available',
                        created_at TEXT,
                        updated_at TEXT
                    )
                ''')
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS communication_keys (
                        key_id TEXT PRIMARY KEY,
                        comm_id TEXT NOT NULL,
                        student_id INTEGER NOT NULL,
                        key_value TEXT,
                        key_type TEXT,
                        creation_time TEXT,
                        expiration_time TEXT,
                        is_active INTEGER DEFAULT 1,
                        FOREIGN KEY(comm_id) REFERENCES quantum_communication(comm_id)
                    )
                ''')
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS quantum_devices (
                        device_id TEXT PRIMARY KEY,
                        device_name TEXT NOT NULL,
                        device_type TEXT,
                        manufacturer TEXT,
                        qubit_count INTEGER,
                        status TEXT DEFAULT 'available',
                        location TEXT,
                        maintenance_schedule TEXT,
                        usage_count INTEGER DEFAULT 0,
                        created_at TEXT,
                        updated_at TEXT
                    )
                ''')
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS device_usage (
                        usage_id TEXT PRIMARY KEY,
                        device_id TEXT NOT NULL,
                        student_id INTEGER NOT NULL,
                        usage_date TEXT,
                        start_time TEXT,
                        end_time TEXT,
                        purpose TEXT,
                        session_type TEXT,
                        status TEXT DEFAULT 'completed',
                        FOREIGN KEY(device_id) REFERENCES quantum_devices(device_id)
                    )
                ''')
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS learning_progress (
                        progress_id TEXT PRIMARY KEY,
                        student_id INTEGER NOT NULL,
                        course_id TEXT,
                        education_level TEXT,
                        education_type TEXT,
                        total_modules INTEGER,
                        completed_modules INTEGER DEFAULT 0,
                        total_experiments INTEGER,
                        completed_experiments INTEGER DEFAULT 0,
                        total_programs INTEGER,
                        completed_programs INTEGER DEFAULT 0,
                        overall_score REAL DEFAULT 0,
                        status TEXT DEFAULT 'in_progress',
                        started_at TEXT,
                        completed_at TEXT,
                        FOREIGN KEY(course_id) REFERENCES quantum_courses(course_id)
                    )
                ''')
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS progress_records (
                        record_id TEXT PRIMARY KEY,
                        progress_id TEXT NOT NULL,
                        activity_type TEXT,
                        activity_id TEXT,
                        activity_name TEXT,
                        completed_at TEXT,
                        score REAL,
                        feedback TEXT,
                        FOREIGN KEY(progress_id) REFERENCES learning_progress(progress_id)
                    )
                ''')
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS quantum_resources (
                        resource_id TEXT PRIMARY KEY,
                        resource_name TEXT NOT NULL,
                        resource_type TEXT,
                        education_level TEXT,
                        education_type TEXT,
                        description TEXT,
                        file_url TEXT,
                        duration TEXT,
                        access_count INTEGER DEFAULT 0,
                        status TEXT DEFAULT 'available',
                        created_at TEXT,
                        updated_at TEXT
                    )
                ''')
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS resource_access (
                        access_id TEXT PRIMARY KEY,
                        resource_id TEXT NOT NULL,
                        student_id INTEGER NOT NULL,
                        access_time TEXT,
                        duration REAL,
                        completed INTEGER DEFAULT 0,
                        FOREIGN KEY(resource_id) REFERENCES quantum_resources(resource_id)
                    )
                ''')
                conn.commit()
                logger.info('教育量子计算服务数据库初始化完成')
        except Exception as e:
            logger.error(f'数据库初始化失败: {e}')

    # ========== 量子课程 ==========

    def create_quantum_course(self, course_name: str, education_level: str,
                               education_type: str, **kwargs) -> Dict[str, Any]:
        try:
            course_id = f"qnt_{uuid.uuid4().hex[:12]}"
            now = datetime.now().isoformat()
            level_config = EDUCATION_LEVELS.get(education_level, {})
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('''
                        INSERT INTO quantum_courses (
                            course_id, course_name, education_level, education_type,
                            description, duration_hours, prerequisites, target_knowledge,
                            difficulty, max_students, enrolled_count, status,
                            created_at, updated_at
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 0, 'active', ?, ?)
                    ''', (course_id, course_name, education_level, education_type,
                          kwargs.get('description'),
                          kwargs.get('duration_hours', level_config.get('duration_hours', 20)),
                          json.dumps(level_config.get('prerequisites', [])),
                          json.dumps(level_config.get('target_knowledge', [])),
                          kwargs.get('difficulty', education_level),
                          kwargs.get('max_students', 30), now, now))
                    conn.commit()
                    logger.info(f'创建量子课程: {course_name} ({course_id})')
                    return {'success': True, 'course_id': course_id}
        except Exception as e:
            logger.error(f'创建量子课程失败: {e}')
            return {'success': False, 'error': str(e)}

    def enroll_quantum_course(self, course_id: str, student_id: int,
                               student_name: str = None) -> Dict[str, Any]:
        try:
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('SELECT max_students, enrolled_count, status, education_level, education_type FROM quantum_courses WHERE course_id = ?', (course_id,))
                    course = cursor.fetchone()
                    if not course:
                        return {'success': False, 'error': '课程不存在'}
                    if course[2] != 'active':
                        return {'success': False, 'error': '课程状态不允许选课'}
                    if course[0] and course[1] >= course[0]:
                        return {'success': False, 'error': '课程名额已满'}
                    cursor.execute('INSERT OR IGNORE INTO learning_progress (progress_id, student_id, course_id, education_level, education_type, total_modules, completed_modules, total_experiments, completed_experiments, total_programs, completed_programs, overall_score, status, started_at) VALUES (?, ?, ?, ?, ?, ?, 0, ?, 0, ?, 0, 0, \'in_progress\', ?)',
                                 (f"prg_{uuid.uuid4().hex[:12]}", student_id, course_id,
                                  course[3], course[4], kwargs.get('total_modules', 0),
                                  kwargs.get('total_experiments', 0),
                                  kwargs.get('total_programs', 0), now))
                    cursor.execute('UPDATE quantum_courses SET enrolled_count = enrolled_count + 1, updated_at = ? WHERE course_id = ?', (now, course_id))
                    conn.commit()
                    return {'success': True}
        except Exception as e:
            logger.error(f'量子选课失败: {e}')
            return {'success': False, 'error': str(e)}

    def add_course_module(self, course_id: str, module_name: str,
                           module_order: int, **kwargs) -> Dict[str, Any]:
        try:
            module_id = f"mod_{uuid.uuid4().hex[:12]}"
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('INSERT INTO course_modules (module_id, course_id, module_name, module_order, duration_hours, content, learning_objectives, resources, status, created_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?, \'active\', ?)',
                                 (module_id, course_id, module_name, module_order,
                                  kwargs.get('duration_hours', 2), kwargs.get('content'),
                                  json.dumps(kwargs.get('learning_objectives', [])),
                                  json.dumps(kwargs.get('resources', [])), now))
                    conn.commit()
                    logger.info(f'添加课程模块: {module_name} ({module_id})')
                    return {'success': True, 'module_id': module_id}
        except Exception as e:
            logger.error(f'添加课程模块失败: {e}')
            return {'success': False, 'error': str(e)}

    def list_quantum_courses(self, education_level: str = None,
                              education_type: str = None, status: str = 'active',
                              page: int = 1, page_size: int = 20) -> Dict[str, Any]:
        try:
            with self._get_connection() as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                query = 'SELECT * FROM quantum_courses WHERE 1=1'
                params = []
                if education_level:
                    query += ' AND education_level = ?'
                    params.append(education_level)
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
                courses = [dict(c) for c in cursor.fetchall()]
                return {'success': True, 'courses': courses, 'total': total, 'page': page, 'page_size': page_size}
        except Exception as e:
            logger.error(f'获取量子课程列表失败: {e}')
            return {'success': False, 'error': str(e)}

    # ========== 量子实验 ==========

    def create_quantum_experiment(self, experiment_name: str, education_level: str,
                                   education_type: str, **kwargs) -> Dict[str, Any]:
        try:
            experiment_id = f"exp_{uuid.uuid4().hex[:12]}"
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('''
                        INSERT INTO quantum_experiments (
                            experiment_id, experiment_name, education_level, education_type,
                            description, required_devices, estimated_duration,
                            safety_requirements, learning_objectives, status,
                            created_at, updated_at
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, 'available', ?, ?)
                    ''', (experiment_id, experiment_name, education_level, education_type,
                          kwargs.get('description'),
                          json.dumps(kwargs.get('required_devices', [])),
                          kwargs.get('estimated_duration', '2h'),
                          kwargs.get('safety_requirements'),
                          json.dumps(kwargs.get('learning_objectives', [])), now, now))
                    conn.commit()
                    logger.info(f'创建量子实验: {experiment_name} ({experiment_id})')
                    return {'success': True, 'experiment_id': experiment_id}
        except Exception as e:
            logger.error(f'创建量子实验失败: {e}')
            return {'success': False, 'error': str(e)}

    def book_experiment_session(self, experiment_id: str, student_id: int,
                                 session_date: str, **kwargs) -> Dict[str, Any]:
        try:
            session_id = f"ses_{uuid.uuid4().hex[:12]}"
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('SELECT status FROM quantum_experiments WHERE experiment_id = ?', (experiment_id,))
                    exp = cursor.fetchone()
                    if not exp:
                        return {'success': False, 'error': '实验不存在'}
                    if exp[0] != 'available':
                        return {'success': False, 'error': '实验暂不可用'}
                    cursor.execute('INSERT INTO experiment_sessions (session_id, experiment_id, student_id, session_date, start_time, end_time, status) VALUES (?, ?, ?, ?, ?, ?, \'pending\')',
                                 (session_id, experiment_id, student_id, session_date,
                                  kwargs.get('start_time', '09:00'),
                                  kwargs.get('end_time', '11:00')))
                    conn.commit()
                    return {'success': True, 'session_id': session_id}
        except Exception as e:
            logger.error(f'预约实验失败: {e}')
            return {'success': False, 'error': str(e)}

    def record_experiment_result(self, session_id: str, **kwargs) -> Dict[str, Any]:
        try:
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('UPDATE experiment_sessions SET data_collected = ?, observations = ?, conclusion = ?, grade = ?, status = ? WHERE session_id = ?',
                                 (json.dumps(kwargs.get('data_collected', {})),
                                  kwargs.get('observations'), kwargs.get('conclusion'),
                                  kwargs.get('grade'), 'completed', session_id))
                    if cursor.rowcount > 0:
                        conn.commit()
                        return {'success': True}
                    return {'success': False, 'error': '实验记录不存在'}
        except Exception as e:
            logger.error(f'记录实验结果失败: {e}')
            return {'success': False, 'error': str(e)}

    def list_experiments(self, education_level: str = None,
                         education_type: str = None, status: str = 'available',
                         page: int = 1, page_size: int = 20) -> Dict[str, Any]:
        try:
            with self._get_connection() as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                query = 'SELECT * FROM quantum_experiments WHERE 1=1'
                params = []
                if education_level:
                    query += ' AND education_level = ?'
                    params.append(education_level)
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
                experiments = [dict(e) for e in cursor.fetchall()]
                return {'success': True, 'experiments': experiments, 'total': total, 'page': page, 'page_size': page_size}
        except Exception as e:
            logger.error(f'获取实验列表失败: {e}')
            return {'success': False, 'error': str(e)}

    # ========== 量子编程 ==========

    def create_quantum_program(self, program_name: str, programming_language: str,
                                education_level: str, education_type: str,
                                **kwargs) -> Dict[str, Any]:
        try:
            program_id = f"prg_{uuid.uuid4().hex[:12]}"
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('''
                        INSERT INTO quantum_programs (
                            program_id, program_name, programming_language,
                            education_level, education_type, description,
                            difficulty, expected_output, template_code, status,
                            created_at, updated_at
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, 'active', ?, ?)
                    ''', (program_id, program_name, programming_language,
                          education_level, education_type, kwargs.get('description'),
                          kwargs.get('difficulty', education_level),
                          kwargs.get('expected_output'), kwargs.get('template_code'),
                          now, now))
                    conn.commit()
                    logger.info(f'创建量子编程任务: {program_name} ({program_id})')
                    return {'success': True, 'program_id': program_id}
        except Exception as e:
            logger.error(f'创建量子编程任务失败: {e}')
            return {'success': False, 'error': str(e)}

    def submit_program(self, program_id: str, student_id: int,
                       submitted_code: str) -> Dict[str, Any]:
        try:
            submission_id = f"sub_{uuid.uuid4().hex[:12]}"
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('INSERT INTO program_submissions (submission_id, program_id, student_id, submitted_code, submission_time, status) VALUES (?, ?, ?, ?, ?, \'submitted\')',
                                 (submission_id, program_id, student_id, submitted_code, now))
                    conn.commit()
                    return {'success': True, 'submission_id': submission_id}
        except Exception as e:
            logger.error(f'提交编程任务失败: {e}')
            return {'success': False, 'error': str(e)}

    def grade_program(self, submission_id: str, grade: str, **kwargs) -> Dict[str, Any]:
        try:
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('UPDATE program_submissions SET test_results = ?, grade = ?, feedback = ?, status = ? WHERE submission_id = ?',
                                 (json.dumps(kwargs.get('test_results', {})), grade,
                                  kwargs.get('feedback'), 'graded', submission_id))
                    if cursor.rowcount > 0:
                        conn.commit()
                        return {'success': True}
                    return {'success': False, 'error': '提交记录不存在'}
        except Exception as e:
            logger.error(f'评分编程任务失败: {e}')
            return {'success': False, 'error': str(e)}

    def list_programs(self, programming_language: str = None,
                      education_level: str = None, education_type: str = None,
                      page: int = 1, page_size: int = 20) -> Dict[str, Any]:
        try:
            with self._get_connection() as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                query = 'SELECT * FROM quantum_programs WHERE 1=1'
                params = []
                if programming_language:
                    query += ' AND programming_language = ?'
                    params.append(programming_language)
                if education_level:
                    query += ' AND education_level = ?'
                    params.append(education_level)
                if education_type:
                    query += ' AND education_type = ?'
                    params.append(education_type)
                cursor.execute(f'SELECT COUNT(*) as cnt FROM ({query})', params)
                total = cursor.fetchone()['cnt']
                query += ' ORDER BY created_at DESC LIMIT ? OFFSET ?'
                params.extend([page_size, (page - 1) * page_size])
                cursor.execute(query, params)
                programs = [dict(p) for p in cursor.fetchall()]
                return {'success': True, 'programs': programs, 'total': total, 'page': page, 'page_size': page_size}
        except Exception as e:
            logger.error(f'获取编程任务列表失败: {e}')
            return {'success': False, 'error': str(e)}

    # ========== 量子模拟 ==========

    def create_simulation(self, simulation_name: str, simulation_type: str,
                           education_level: str, education_type: str,
                           **kwargs) -> Dict[str, Any]:
        try:
            simulation_id = f"sim_{uuid.uuid4().hex[:12]}"
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('''
                        INSERT INTO quantum_simulation (
                            simulation_id, simulation_name, simulation_type,
                            education_level, education_type, description,
                            parameters, initial_state, expected_results, status,
                            created_at, updated_at
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, 'configured', ?, ?)
                    ''', (simulation_id, simulation_name, simulation_type,
                          education_level, education_type, kwargs.get('description'),
                          json.dumps(kwargs.get('parameters', {})),
                          kwargs.get('initial_state'),
                          kwargs.get('expected_results'), now, now))
                    conn.commit()
                    logger.info(f'创建量子模拟: {simulation_name} ({simulation_id})')
                    return {'success': True, 'simulation_id': simulation_id}
        except Exception as e:
            logger.error(f'创建量子模拟失败: {e}')
            return {'success': False, 'error': str(e)}

    def run_simulation(self, simulation_id: str, student_id: int,
                       **kwargs) -> Dict[str, Any]:
        try:
            result_id = f"res_{uuid.uuid4().hex[:12]}"
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('INSERT INTO simulation_results (result_id, simulation_id, student_id, run_parameters, raw_results, analysis, visualizations, run_time, status) VALUES (?, ?, ?, ?, ?, ?, ?, ?, \'completed\')',
                                 (result_id, simulation_id, student_id,
                                  json.dumps(kwargs.get('run_parameters', {})),
                                  json.dumps(kwargs.get('raw_results', {})),
                                  kwargs.get('analysis'),
                                  json.dumps(kwargs.get('visualizations', [])), now))
                    conn.commit()
                    return {'success': True, 'result_id': result_id}
        except Exception as e:
            logger.error(f'运行量子模拟失败: {e}')
            return {'success': False, 'error': str(e)}

    def analyze_simulation(self, result_id: str, analysis: str,
                           **kwargs) -> Dict[str, Any]:
        try:
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('UPDATE simulation_results SET analysis = ?, visualizations = ? WHERE result_id = ?',
                                 (analysis, json.dumps(kwargs.get('visualizations', [])), result_id))
                    if cursor.rowcount > 0:
                        conn.commit()
                        return {'success': True}
                    return {'success': False, 'error': '模拟结果不存在'}
        except Exception as e:
            logger.error(f'分析模拟结果失败: {e}')
            return {'success': False, 'error': str(e)}

    def list_simulations(self, simulation_type: str = None,
                         education_level: str = None, education_type: str = None,
                         page: int = 1, page_size: int = 20) -> Dict[str, Any]:
        try:
            with self._get_connection() as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                query = 'SELECT * FROM quantum_simulation WHERE 1=1'
                params = []
                if simulation_type:
                    query += ' AND simulation_type = ?'
                    params.append(simulation_type)
                if education_level:
                    query += ' AND education_level = ?'
                    params.append(education_level)
                if education_type:
                    query += ' AND education_type = ?'
                    params.append(education_type)
                cursor.execute(f'SELECT COUNT(*) as cnt FROM ({query})', params)
                total = cursor.fetchone()['cnt']
                query += ' ORDER BY created_at DESC LIMIT ? OFFSET ?'
                params.extend([page_size, (page - 1) * page_size])
                cursor.execute(query, params)
                simulations = [dict(s) for s in cursor.fetchall()]
                return {'success': True, 'simulations': simulations, 'total': total, 'page': page, 'page_size': page_size}
        except Exception as e:
            logger.error(f'获取模拟列表失败: {e}')
            return {'success': False, 'error': str(e)}

    # ========== 量子机器学习 ==========

    def create_ml_model(self, model_name: str, model_type: str,
                         education_level: str, education_type: str,
                         **kwargs) -> Dict[str, Any]:
        try:
            model_id = f"mlm_{uuid.uuid4().hex[:12]}"
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('''
                        INSERT INTO quantum_ml_models (
                            model_id, model_name, model_type, education_level,
                            education_type, description, architecture,
                            training_data, hyperparameters, status,
                            created_at, updated_at
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, 'trained', ?, ?)
                    ''', (model_id, model_name, model_type, education_level,
                          education_type, kwargs.get('description'),
                          kwargs.get('architecture'), kwargs.get('training_data'),
                          json.dumps(kwargs.get('hyperparameters', {})), now, now))
                    conn.commit()
                    logger.info(f'创建量子ML模型: {model_name} ({model_id})')
                    return {'success': True, 'model_id': model_id}
        except Exception as e:
            logger.error(f'创建量子ML模型失败: {e}')
            return {'success': False, 'error': str(e)}

    def train_ml_model(self, model_id: str, student_id: int,
                        **kwargs) -> Dict[str, Any]:
        try:
            training_id = f"trn_{uuid.uuid4().hex[:12]}"
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('INSERT INTO model_training (training_id, model_id, student_id, training_data, hyperparameters, training_metrics, accuracy, loss, training_time, status) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, \'completed\')',
                                 (training_id, model_id, student_id,
                                  kwargs.get('training_data'),
                                  json.dumps(kwargs.get('hyperparameters', {})),
                                  json.dumps(kwargs.get('training_metrics', {})),
                                  kwargs.get('accuracy', 0), kwargs.get('loss', 0), now))
                    conn.commit()
                    return {'success': True, 'training_id': training_id}
        except Exception as e:
            logger.error(f'训练量子ML模型失败: {e}')
            return {'success': False, 'error': str(e)}

    def evaluate_ml_model(self, model_id: str, evaluation_data: str,
                          **kwargs) -> Dict[str, Any]:
        try:
            with self._get_connection() as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                cursor.execute('SELECT * FROM quantum_ml_models WHERE model_id = ?', (model_id,))
                model = cursor.fetchone()
                if not model:
                    return {'success': False, 'error': '模型不存在'}
                metrics = {
                    'accuracy': kwargs.get('accuracy', 0),
                    'precision': kwargs.get('precision', 0),
                    'recall': kwargs.get('recall', 0),
                    'f1_score': kwargs.get('f1_score', 0)
                }
                return {'success': True, 'model': dict(model), 'metrics': metrics}
        except Exception as e:
            logger.error(f'评估量子ML模型失败: {e}')
            return {'success': False, 'error': str(e)}

    def predict_ml_model(self, model_id: str, input_data: str) -> Dict[str, Any]:
        try:
            with self._get_connection() as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                cursor.execute('SELECT * FROM quantum_ml_models WHERE model_id = ?', (model_id,))
                model = cursor.fetchone()
                if not model:
                    return {'success': False, 'error': '模型不存在'}
                return {'success': True, 'model_name': model['model_name'], 'prediction': 'simulated_prediction'}
        except Exception as e:
            logger.error(f'量子ML模型预测失败: {e}')
            return {'success': False, 'error': str(e)}

    def list_ml_models(self, model_type: str = None,
                       education_level: str = None, education_type: str = None,
                       page: int = 1, page_size: int = 20) -> Dict[str, Any]:
        try:
            with self._get_connection() as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                query = 'SELECT * FROM quantum_ml_models WHERE 1=1'
                params = []
                if model_type:
                    query += ' AND model_type = ?'
                    params.append(model_type)
                if education_level:
                    query += ' AND education_level = ?'
                    params.append(education_level)
                if education_type:
                    query += ' AND education_type = ?'
                    params.append(education_type)
                cursor.execute(f'SELECT COUNT(*) as cnt FROM ({query})', params)
                total = cursor.fetchone()['cnt']
                query += ' ORDER BY created_at DESC LIMIT ? OFFSET ?'
                params.extend([page_size, (page - 1) * page_size])
                cursor.execute(query, params)
                models = [dict(m) for m in cursor.fetchall()]
                return {'success': True, 'models': models, 'total': total, 'page': page, 'page_size': page_size}
        except Exception as e:
            logger.error(f'获取ML模型列表失败: {e}')
            return {'success': False, 'error': str(e)}

    # ========== 量子通信 ==========

    def create_communication_task(self, comm_type: str, education_level: str,
                                   education_type: str, **kwargs) -> Dict[str, Any]:
        try:
            comm_id = f"com_{uuid.uuid4().hex[:12]}"
            now = datetime.now().isoformat()
            config = QUANTUM_COMMUNICATION.get(comm_type, {})
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('''
                        INSERT INTO quantum_communication (
                            comm_id, comm_type, education_level, education_type,
                            description, security_level, distance_range,
                            equipment_required, status, created_at, updated_at
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, 'available', ?, ?)
                    ''', (comm_id, comm_type, education_level, education_type,
                          kwargs.get('description'),
                          kwargs.get('security_level', config.get('security_level')),
                          kwargs.get('distance_range'),
                          json.dumps(kwargs.get('equipment_required', [])), now, now))
                    conn.commit()
                    logger.info(f'创建量子通信任务: {comm_type} ({comm_id})')
                    return {'success': True, 'comm_id': comm_id}
        except Exception as e:
            logger.error(f'创建量子通信任务失败: {e}')
            return {'success': False, 'error': str(e)}

    def generate_quantum_key(self, comm_id: str, student_id: int,
                             key_type: str = 'qkd') -> Dict[str, Any]:
        try:
            key_id = f"key_{uuid.uuid4().hex[:12]}"
            now = datetime.now().isoformat()
            key_value = f"QK{datetime.now().strftime('%Y%m%d')}{uuid.uuid4().hex[:32]}"
            expires = (datetime.now() + timedelta(days=30)).isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('INSERT INTO communication_keys (key_id, comm_id, student_id, key_value, key_type, creation_time, expiration_time, is_active) VALUES (?, ?, ?, ?, ?, ?, ?, 1)',
                                 (key_id, comm_id, student_id, key_value, key_type, now, expires))
                    conn.commit()
                    return {'success': True, 'key_id': key_id, 'key_value': key_value, 'expiration_time': expires}
        except Exception as e:
            logger.error(f'生成量子密钥失败: {e}')
            return {'success': False, 'error': str(e)}

    def use_quantum_key(self, key_id: str) -> Dict[str, Any]:
        try:
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('SELECT is_active, expiration_time FROM communication_keys WHERE key_id = ?', (key_id,))
                    key = cursor.fetchone()
                    if not key:
                        return {'success': False, 'error': '密钥不存在'}
                    if key[0] != 1:
                        return {'success': False, 'error': '密钥已失效'}
                    if datetime.now().isoformat() > key[1]:
                        cursor.execute('UPDATE communication_keys SET is_active = 0 WHERE key_id = ?', (key_id,))
                        conn.commit()
                        return {'success': False, 'error': '密钥已过期'}
                    return {'success': True, 'message': '密钥验证通过'}
        except Exception as e:
            logger.error(f'使用量子密钥失败: {e}')
            return {'success': False, 'error': str(e)}

    def list_communication_tasks(self, comm_type: str = None,
                                  education_level: str = None, education_type: str = None,
                                  page: int = 1, page_size: int = 20) -> Dict[str, Any]:
        try:
            with self._get_connection() as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                query = 'SELECT * FROM quantum_communication WHERE 1=1'
                params = []
                if comm_type:
                    query += ' AND comm_type = ?'
                    params.append(comm_type)
                if education_level:
                    query += ' AND education_level = ?'
                    params.append(education_level)
                if education_type:
                    query += ' AND education_type = ?'
                    params.append(education_type)
                cursor.execute(f'SELECT COUNT(*) as cnt FROM ({query})', params)
                total = cursor.fetchone()['cnt']
                query += ' ORDER BY created_at DESC LIMIT ? OFFSET ?'
                params.extend([page_size, (page - 1) * page_size])
                cursor.execute(query, params)
                tasks = [dict(t) for t in cursor.fetchall()]
                return {'success': True, 'tasks': tasks, 'total': total, 'page': page, 'page_size': page_size}
        except Exception as e:
            logger.error(f'获取通信任务列表失败: {e}')
            return {'success': False, 'error': str(e)}

    # ========== 量子设备 ==========

    def register_device(self, device_name: str, device_type: str,
                        **kwargs) -> Dict[str, Any]:
        try:
            device_id = f"dev_{uuid.uuid4().hex[:12]}"
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('''
                        INSERT INTO quantum_devices (
                            device_id, device_name, device_type, manufacturer,
                            qubit_count, status, location, maintenance_schedule,
                            usage_count, created_at, updated_at
                        ) VALUES (?, ?, ?, ?, ?, 'available', ?, ?, 0, ?, ?)
                    ''', (device_id, device_name, device_type, kwargs.get('manufacturer'),
                          kwargs.get('qubit_count', 0), kwargs.get('location'),
                          kwargs.get('maintenance_schedule'), now, now))
                    conn.commit()
                    logger.info(f'注册量子设备: {device_name} ({device_id})')
                    return {'success': True, 'device_id': device_id}
        except Exception as e:
            logger.error(f'注册量子设备失败: {e}')
            return {'success': False, 'error': str(e)}

    def reserve_device(self, device_id: str, student_id: int,
                       usage_date: str, **kwargs) -> Dict[str, Any]:
        try:
            usage_id = f"usg_{uuid.uuid4().hex[:12]}"
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('SELECT status FROM quantum_devices WHERE device_id = ?', (device_id,))
                    device = cursor.fetchone()
                    if not device:
                        return {'success': False, 'error': '设备不存在'}
                    if device[0] != 'available':
                        return {'success': False, 'error': '设备不可用'}
                    cursor.execute('INSERT INTO device_usage (usage_id, device_id, student_id, usage_date, start_time, end_time, purpose, session_type, status) VALUES (?, ?, ?, ?, ?, ?, ?, ?, \'scheduled\')',
                                 (usage_id, device_id, student_id, usage_date,
                                  kwargs.get('start_time', '09:00'),
                                  kwargs.get('end_time', '12:00'),
                                  kwargs.get('purpose', 'experiment'),
                                  kwargs.get('session_type', 'hands-on')))
                    cursor.execute('UPDATE quantum_devices SET status = \'reserved\', updated_at = ? WHERE device_id = ?', (now, device_id))
                    conn.commit()
                    return {'success': True, 'usage_id': usage_id}
        except Exception as e:
            logger.error(f'预约量子设备失败: {e}')
            return {'success': False, 'error': str(e)}

    def complete_device_usage(self, usage_id: str) -> Dict[str, Any]:
        try:
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('SELECT device_id FROM device_usage WHERE usage_id = ?', (usage_id,))
                    usage = cursor.fetchone()
                    if not usage:
                        return {'success': False, 'error': '使用记录不存在'}
                    cursor.execute('UPDATE device_usage SET status = \'completed\' WHERE usage_id = ?', (usage_id,))
                    cursor.execute('UPDATE quantum_devices SET status = \'available\', usage_count = usage_count + 1, updated_at = ? WHERE device_id = ?', (now, usage[0]))
                    conn.commit()
                    return {'success': True}
        except Exception as e:
            logger.error(f'完成设备使用失败: {e}')
            return {'success': False, 'error': str(e)}

    def list_devices(self, device_type: str = None, status: str = 'available',
                     page: int = 1, page_size: int = 20) -> Dict[str, Any]:
        try:
            with self._get_connection() as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                query = 'SELECT * FROM quantum_devices WHERE 1=1'
                params = []
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

    # ========== 学习进度 ==========

    def update_progress(self, progress_id: str, **kwargs) -> Dict[str, Any]:
        try:
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    updates = []
                    params = []
                    if 'completed_modules' in kwargs:
                        updates.append('completed_modules = ?')
                        params.append(kwargs['completed_modules'])
                    if 'completed_experiments' in kwargs:
                        updates.append('completed_experiments = ?')
                        params.append(kwargs['completed_experiments'])
                    if 'completed_programs' in kwargs:
                        updates.append('completed_programs = ?')
                        params.append(kwargs['completed_programs'])
                    if 'overall_score' in kwargs:
                        updates.append('overall_score = ?')
                        params.append(kwargs['overall_score'])
                    if updates:
                        updates.append('updated_at = ?')
                        params.extend([now, progress_id])
                        query = f'UPDATE learning_progress SET {", ".join(updates)} WHERE progress_id = ?'
                        cursor.execute(query, params)
                        conn.commit()
                    return {'success': True}
        except Exception as e:
            logger.error(f'更新学习进度失败: {e}')
            return {'success': False, 'error': str(e)}

    def add_progress_record(self, progress_id: str, activity_type: str,
                            activity_id: str, activity_name: str, **kwargs) -> Dict[str, Any]:
        try:
            record_id = f"rec_{uuid.uuid4().hex[:12]}"
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('INSERT INTO progress_records (record_id, progress_id, activity_type, activity_id, activity_name, completed_at, score, feedback) VALUES (?, ?, ?, ?, ?, ?, ?, ?)',
                                 (record_id, progress_id, activity_type, activity_id,
                                  activity_name, now, kwargs.get('score', 0),
                                  kwargs.get('feedback')))
                    conn.commit()
                    return {'success': True, 'record_id': record_id}
        except Exception as e:
            logger.error(f'添加进度记录失败: {e}')
            return {'success': False, 'error': str(e)}

    def get_student_progress(self, student_id: int, course_id: str = None) -> Dict[str, Any]:
        try:
            with self._get_connection() as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                query = 'SELECT * FROM learning_progress WHERE student_id = ?'
                params = [student_id]
                if course_id:
                    query += ' AND course_id = ?'
                    params.append(course_id)
                cursor.execute(query, params)
                progress = [dict(p) for p in cursor.fetchall()]
                return {'success': True, 'progress': progress}
        except Exception as e:
            logger.error(f'获取学生进度失败: {e}')
            return {'success': False, 'error': str(e)}

    def complete_course(self, progress_id: str) -> Dict[str, Any]:
        try:
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('UPDATE learning_progress SET status = \'completed\', completed_at = ? WHERE progress_id = ?', (now, progress_id))
                    if cursor.rowcount > 0:
                        conn.commit()
                        return {'success': True}
                    return {'success': False, 'error': '进度记录不存在'}
        except Exception as e:
            logger.error(f'完成课程失败: {e}')
            return {'success': False, 'error': str(e)}

    # ========== 资源管理 ==========

    def create_resource(self, resource_name: str, resource_type: str,
                        education_level: str, education_type: str,
                        **kwargs) -> Dict[str, Any]:
        try:
            resource_id = f"res_{uuid.uuid4().hex[:12]}"
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('''
                        INSERT INTO quantum_resources (
                            resource_id, resource_name, resource_type,
                            education_level, education_type, description,
                            file_url, duration, access_count, status,
                            created_at, updated_at
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, 0, 'available', ?, ?)
                    ''', (resource_id, resource_name, resource_type,
                          education_level, education_type, kwargs.get('description'),
                          kwargs.get('file_url'), kwargs.get('duration'), now, now))
                    conn.commit()
                    logger.info(f'创建量子资源: {resource_name} ({resource_id})')
                    return {'success': True, 'resource_id': resource_id}
        except Exception as e:
            logger.error(f'创建量子资源失败: {e}')
            return {'success': False, 'error': str(e)}

    def access_resource(self, resource_id: str, student_id: int,
                        **kwargs) -> Dict[str, Any]:
        try:
            access_id = f"acc_{uuid.uuid4().hex[:12]}"
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('INSERT INTO resource_access (access_id, resource_id, student_id, access_time, duration, completed) VALUES (?, ?, ?, ?, ?, ?)',
                                 (access_id, resource_id, student_id, now,
                                  kwargs.get('duration', 0), kwargs.get('completed', 0)))
                    cursor.execute('UPDATE quantum_resources SET access_count = access_count + 1, updated_at = ? WHERE resource_id = ?', (now, resource_id))
                    conn.commit()
                    return {'success': True, 'access_id': access_id}
        except Exception as e:
            logger.error(f'访问量子资源失败: {e}')
            return {'success': False, 'error': str(e)}

    def update_resource(self, resource_id: str, **kwargs) -> Dict[str, Any]:
        try:
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    updates = []
                    params = []
                    if 'resource_name' in kwargs:
                        updates.append('resource_name = ?')
                        params.append(kwargs['resource_name'])
                    if 'description' in kwargs:
                        updates.append('description = ?')
                        params.append(kwargs['description'])
                    if 'file_url' in kwargs:
                        updates.append('file_url = ?')
                        params.append(kwargs['file_url'])
                    if 'status' in kwargs:
                        updates.append('status = ?')
                        params.append(kwargs['status'])
                    if updates:
                        updates.append('updated_at = ?')
                        params.extend([now, resource_id])
                        query = f'UPDATE quantum_resources SET {", ".join(updates)} WHERE resource_id = ?'
                        cursor.execute(query, params)
                        conn.commit()
                    return {'success': True}
        except Exception as e:
            logger.error(f'更新量子资源失败: {e}')
            return {'success': False, 'error': str(e)}

    def list_resources(self, resource_type: str = None,
                       education_level: str = None, education_type: str = None,
                       page: int = 1, page_size: int = 20) -> Dict[str, Any]:
        try:
            with self._get_connection() as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                query = 'SELECT * FROM quantum_resources WHERE 1=1'
                params = []
                if resource_type:
                    query += ' AND resource_type = ?'
                    params.append(resource_type)
                if education_level:
                    query += ' AND education_level = ?'
                    params.append(education_level)
                if education_type:
                    query += ' AND education_type = ?'
                    params.append(education_type)
                cursor.execute(f'SELECT COUNT(*) as cnt FROM ({query})', params)
                total = cursor.fetchone()['cnt']
                query += ' ORDER BY created_at DESC LIMIT ? OFFSET ?'
                params.extend([page_size, (page - 1) * page_size])
                cursor.execute(query, params)
                resources = [dict(r) for r in cursor.fetchall()]
                return {'success': True, 'resources': resources, 'total': total, 'page': page, 'page_size': page_size}
        except Exception as e:
            logger.error(f'获取资源列表失败: {e}')
            return {'success': False, 'error': str(e)}

    # ========== 统计 ==========

    def get_quantum_education_stats(self, education_type: str = None) -> Dict[str, Any]:
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                stats = {}
                
                query_courses = 'SELECT COUNT(*) FROM quantum_courses WHERE 1=1'
                params_courses = []
                if education_type:
                    query_courses += ' AND education_type = ?'
                    params_courses.append(education_type)
                cursor.execute(query_courses, params_courses)
                stats['total_courses'] = cursor.fetchone()[0]

                query_students = 'SELECT COUNT(DISTINCT student_id) FROM learning_progress WHERE 1=1'
                params_students = []
                if education_type:
                    query_students += ' AND education_type = ?'
                    params_students.append(education_type)
                cursor.execute(query_students, params_students)
                stats['total_students'] = cursor.fetchone()[0]

                query_experiments = 'SELECT COUNT(*) FROM quantum_experiments WHERE 1=1'
                params_exp = []
                if education_type:
                    query_experiments += ' AND education_type = ?'
                    params_exp.append(education_type)
                cursor.execute(query_experiments, params_exp)
                stats['total_experiments'] = cursor.fetchone()[0]

                query_programs = 'SELECT COUNT(*) FROM quantum_programs WHERE 1=1'
                params_prog = []
                if education_type:
                    query_programs += ' AND education_type = ?'
                    params_prog.append(education_type)
                cursor.execute(query_programs, params_prog)
                stats['total_programs'] = cursor.fetchone()[0]

                query_simulations = 'SELECT COUNT(*) FROM quantum_simulation WHERE 1=1'
                params_sim = []
                if education_type:
                    query_simulations += ' AND education_type = ?'
                    params_sim.append(education_type)
                cursor.execute(query_simulations, params_sim)
                stats['total_simulations'] = cursor.fetchone()[0]

                query_ml_models = 'SELECT COUNT(*) FROM quantum_ml_models WHERE 1=1'
                params_ml = []
                if education_type:
                    query_ml_models += ' AND education_type = ?'
                    params_ml.append(education_type)
                cursor.execute(query_ml_models, params_ml)
                stats['total_ml_models'] = cursor.fetchone()[0]

                query_devices = 'SELECT COUNT(*) FROM quantum_devices'
                cursor.execute(query_devices)
                stats['total_devices'] = cursor.fetchone()[0]

                query_completed = 'SELECT COUNT(*) FROM learning_progress WHERE status = \'completed\''
                cursor.execute(query_completed)
                stats['completed_courses'] = cursor.fetchone()[0]

                return {'success': True, 'stats': stats}
        except Exception as e:
            logger.error(f'获取量子教育统计失败: {e}')
            return {'success': False, 'error': str(e)}