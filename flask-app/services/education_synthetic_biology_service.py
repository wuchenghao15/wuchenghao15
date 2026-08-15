#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
MTSCOS 教育合成生物学服务 (v15.19.0)
====================================
提供合成生物学课程、基因编辑实验、DNA合成、生物电路设计等综合教育服务。

核心能力：
1. 合成生物学课程 - 课程管理、选课、实验安排、成绩记录
2. 基因编辑 - CRISPR实验设计、编辑记录、结果分析
3. DNA合成 - 序列设计、合成订单、质量检测
4. 电路设计 - 生物电路建模、模拟仿真、实验验证
5. 生物信息学 - 序列分析、结构预测、功能注释
6. 实验室安全 - 安全规范、风险评估、检查记录
7. 生物教育 - 教学计划、课程安排、学习评估
8. 创新项目 - 项目立项、进度跟踪、成果提交
9. 设备管理 - 设备登记、使用记录、维护保养
10. 统计分析 - 综合数据统计与报告
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
            os.path.join(os.path.dirname(os.path.abspath(__file__)), 'education_synthetic_biology_service.log'),
            encoding='utf-8'
        ),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger('SyntheticBiology')


# ========== 合成生物学配置 ==========

SYNTHETIC_CONCEPTS = {
    'gene_editing': {'name': '基因编辑', 'description': '精准修饰生物体基因组'},
    'dna_synthesis': {'name': 'DNA合成', 'description': '人工合成基因片段'},
    'bio_circuit': {'name': '生物电路', 'description': '设计基因调控网络'},
    'metabolic_engineering': {'name': '代谢工程', 'description': '优化细胞代谢途径'},
    'cell_engineering': {'name': '细胞工程', 'description': '改造细胞功能特性'},
    'protein_engineering': {'name': '蛋白质工程', 'description': '设计新型蛋白质'},
    'genomics': {'name': '基因组学', 'description': '研究完整基因组信息'},
    'bioinformatics': {'name': '生物信息学', 'description': '计算分析生物数据'}
}

EDITING_TOOLS = {
    'crispr_cas9': {'name': 'CRISPR-Cas9', 'accuracy': 'high', 'target_type': 'DNA'},
    'crispr_cas12': {'name': 'CRISPR-Cas12', 'accuracy': 'medium', 'target_type': 'DNA'},
    'crispr_cas13': {'name': 'CRISPR-Cas13', 'accuracy': 'medium', 'target_type': 'RNA'},
    'talen': {'name': 'TALEN', 'accuracy': 'high', 'target_type': 'DNA'},
    'zfn': {'name': 'ZFN', 'accuracy': 'high', 'target_type': 'DNA'},
    'base_editing': {'name': '碱基编辑', 'accuracy': 'very_high', 'target_type': 'DNA'},
    'prime_editing': {'name': '先导编辑', 'accuracy': 'very_high', 'target_type': 'DNA'}
}

DNA_SYNTHESIS = {
    'oligo_synthesis': {'name': '寡核苷酸合成', 'max_length': 200, 'accuracy': 'high'},
    'gene_synthesis': {'name': '基因合成', 'max_length': 5000, 'accuracy': 'high'},
    'fragment_synthesis': {'name': '片段合成', 'max_length': 10000, 'accuracy': 'medium'},
    'full_gene_synthesis': {'name': '全基因合成', 'max_length': 50000, 'accuracy': 'medium'},
    'de_novo_synthesis': {'name': '从头合成', 'max_length': 100000, 'accuracy': 'low'},
    'directed_evolution': {'name': '定向进化', 'max_length': 1000, 'accuracy': 'high'}
}

CIRCUIT_DESIGN = {
    'logic_gate': {'name': '逻辑门', 'types': ['AND', 'OR', 'NOT', 'NAND', 'NOR', 'XOR']},
    'oscillator': {'name': '振荡器', 'types': ['repression', 'activation', 'toggle']},
    'switch': {'name': '开关', 'types': ['inducible', 'repressible', 'light', 'temperature']},
    'sensor': {'name': '传感器', 'types': ['chemical', 'light', 'pH', 'oxygen', 'pressure']},
    'memory': {'name': '记忆元件', 'types': ['toggle', 'counter', 'latch']},
    'signaling': {'name': '信号通路', 'types': ['MAPK', 'Wnt', 'Notch', 'Hedgehog']},
    'feedback': {'name': '反馈回路', 'types': ['positive', 'negative', 'feedforward']},
    'population': {'name': '细胞群体', 'types': ['quorum_sensing', 'pattern_formation']}
}

BIOINFORMATICS = {
    'sequence_analysis': {'name': '序列分析', 'tools': ['BLAST', 'ClustalW', 'MAFFT']},
    'structure_prediction': {'name': '结构预测', 'tools': ['AlphaFold', 'Rosetta', 'I-TASSER']},
    'functional_annotation': {'name': '功能注释', 'tools': ['GO', 'KEGG', 'InterPro']},
    'evolutionary_analysis': {'name': '进化分析', 'tools': ['MEGA', 'RAxML', 'BEAST']},
    'gene_expression': {'name': '基因表达', 'tools': ['RNA-seq', 'Microarray', 'qPCR']},
    'proteomics': {'name': '蛋白质组学', 'tools': ['LC-MS', '2D-PAGE', 'iTRAQ']},
    'metabolomics': {'name': '代谢组学', 'tools': ['GC-MS', 'LC-MS', 'NMR']}
}

SAFETY_PROTOCOLS = {
    'bio_safety_level': {'name': '生物安全等级', 'levels': ['BSL-1', 'BSL-2', 'BSL-3', 'BSL-4']},
    'lab_standards': {'name': '实验室规范', 'standards': ['ISO 15189', 'GLP', 'GMP']},
    'risk_assessment': {'name': '风险评估', 'types': ['biological', 'chemical', 'physical']},
    'ethics_review': {'name': '伦理审查', 'requirements': ['IRB', '知情同意', '隐私保护']},
    'bio_security': {'name': '生物安保', 'measures': ['access_control', 'inventory', 'transport']},
    'waste_disposal': {'name': '废物处理', 'categories': ['biological', 'chemical', 'radioactive']}
}

EDUCATION_LEVELS = {
    'intro': {'name': '入门', 'duration': '4周', 'age_range': '10+', 'prerequisites': []},
    'basic': {'name': '基础', 'duration': '8周', 'age_range': '12+', 'prerequisites': ['intro']},
    'intermediate': {'name': '中级', 'duration': '12周', 'age_range': '14+', 'prerequisites': ['basic']},
    'advanced': {'name': '高级', 'duration': '16周', 'age_range': '16+', 'prerequisites': ['intermediate']},
    'research': {'name': '研究', 'duration': '24周', 'age_range': '18+', 'prerequisites': ['advanced']},
    'innovation': {'name': '创新', 'duration': '可变', 'age_range': '16+', 'prerequisites': ['intermediate']}
}

APPLICATION_AREAS = {
    'healthcare': {'name': '医药健康', 'applications': ['药物研发', '诊断', '基因治疗']},
    'agriculture': {'name': '农业环保', 'applications': ['抗虫作物', '生物肥料', '生物修复']},
    'industry': {'name': '工业制造', 'applications': ['生物燃料', '生物塑料', '酶制剂']},
    'energy': {'name': '能源材料', 'applications': ['太阳能生物', '储能材料', '燃料电池']},
    'biocomputing': {'name': '生物计算', 'applications': ['DNA计算', '细胞计算', '生物传感器']},
    'biosensing': {'name': '生物传感', 'applications': ['环境监测', '食品安全', '医疗诊断']},
    'gene_therapy': {'name': '基因治疗', 'applications': ['遗传病', '癌症', '免疫疾病']},
    'synthetic_ecology': {'name': '合成生态', 'applications': ['共生系统', '生态修复', '生物多样性']}
}


class SyntheticBiologyService:
    """教育合成生物学服务"""

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
                    CREATE TABLE IF NOT EXISTS synthetic_courses (
                        course_id TEXT PRIMARY KEY,
                        course_name TEXT NOT NULL,
                        concept TEXT,
                        education_level TEXT,
                        education_type TEXT,
                        grade_level INTEGER,
                        teacher_id INTEGER,
                        teacher_name TEXT,
                        semester TEXT,
                        weekly_hours INTEGER DEFAULT 3,
                        location TEXT,
                        max_students INTEGER DEFAULT 20,
                        enrolled_count INTEGER DEFAULT 0,
                        description TEXT,
                        prerequisites TEXT,
                        status TEXT DEFAULT 'active',
                        created_at TEXT,
                        updated_at TEXT
                    )
                ''')
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS course_labs (
                        lab_id TEXT PRIMARY KEY,
                        course_id TEXT NOT NULL,
                        lab_name TEXT NOT NULL,
                        lab_type TEXT,
                        safety_level TEXT DEFAULT 'BSL-1',
                        duration_hours INTEGER DEFAULT 3,
                        equipment_required TEXT,
                        materials TEXT,
                        procedure TEXT,
                        expected_outcome TEXT,
                        education_type TEXT,
                        status TEXT DEFAULT 'planned',
                        created_at TEXT,
                        updated_at TEXT
                    )
                ''')
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS gene_editing (
                        editing_id TEXT PRIMARY KEY,
                        target_gene TEXT NOT NULL,
                        organism TEXT NOT NULL,
                        tool TEXT,
                        guide_rna TEXT,
                        editing_type TEXT,
                        education_type TEXT,
                        education_level TEXT,
                        status TEXT DEFAULT 'design',
                        created_at TEXT,
                        updated_at TEXT
                    )
                ''')
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS editing_experiments (
                        experiment_id TEXT PRIMARY KEY,
                        editing_id TEXT NOT NULL,
                        experiment_name TEXT,
                        student_id INTEGER,
                        student_name TEXT,
                        experiment_date TEXT,
                        cell_line TEXT,
                        transfection_method TEXT,
                        efficiency REAL,
                        off_target_count INTEGER DEFAULT 0,
                        result TEXT,
                        notes TEXT,
                        education_type TEXT,
                        created_at TEXT
                    )
                ''')
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS dna_synthesis (
                        synthesis_id TEXT PRIMARY KEY,
                        sequence_name TEXT NOT NULL,
                        sequence TEXT,
                        length INTEGER,
                        synthesis_type TEXT,
                        organism TEXT,
                        gc_content REAL,
                        purification_method TEXT,
                        quality_score REAL,
                        education_type TEXT,
                        status TEXT DEFAULT 'pending',
                        created_at TEXT,
                        updated_at TEXT
                    )
                ''')
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS synthesis_orders (
                        order_id TEXT PRIMARY KEY,
                        synthesis_id TEXT NOT NULL,
                        quantity INTEGER DEFAULT 1,
                        delivery_date TEXT,
                        price REAL DEFAULT 0,
                        payment_status TEXT DEFAULT 'unpaid',
                        tracking_number TEXT,
                        education_type TEXT,
                        created_at TEXT,
                        updated_at TEXT
                    )
                ''')
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS circuit_design (
                        design_id TEXT PRIMARY KEY,
                        design_name TEXT NOT NULL,
                        circuit_type TEXT,
                        components TEXT,
                        logic_description TEXT,
                        simulation_results TEXT,
                        organism TEXT,
                        promoter TEXT,
                        ribosome_binding TEXT,
                        terminator TEXT,
                        education_type TEXT,
                        education_level TEXT,
                        status TEXT DEFAULT 'design',
                        created_at TEXT,
                        updated_at TEXT
                    )
                ''')
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS design_projects (
                        project_id TEXT PRIMARY KEY,
                        design_id TEXT NOT NULL,
                        project_name TEXT,
                        student_id INTEGER,
                        student_name TEXT,
                        phase TEXT DEFAULT 'planning',
                        progress REAL DEFAULT 0,
                        milestone TEXT,
                        deadline TEXT,
                        education_type TEXT,
                        created_at TEXT,
                        updated_at TEXT
                    )
                ''')
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS bioinformatics (
                        analysis_id TEXT PRIMARY KEY,
                        analysis_name TEXT NOT NULL,
                        analysis_type TEXT,
                        input_data TEXT,
                        tools_used TEXT,
                        parameters TEXT,
                        output_data TEXT,
                        results_summary TEXT,
                        education_type TEXT,
                        education_level TEXT,
                        status TEXT DEFAULT 'running',
                        created_at TEXT,
                        updated_at TEXT
                    )
                ''')
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS analysis_tasks (
                        task_id TEXT PRIMARY KEY,
                        analysis_id TEXT NOT NULL,
                        task_name TEXT,
                        task_type TEXT,
                        input_file TEXT,
                        output_file TEXT,
                        status TEXT DEFAULT 'pending',
                        execution_time REAL,
                        error_message TEXT,
                        education_type TEXT,
                        created_at TEXT,
                        updated_at TEXT
                    )
                ''')
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS lab_safety (
                        safety_id TEXT PRIMARY KEY,
                        protocol_name TEXT NOT NULL,
                        safety_level TEXT,
                        category TEXT,
                        description TEXT,
                        procedures TEXT,
                        required_training TEXT,
                        documentation TEXT,
                        education_type TEXT,
                        is_active INTEGER DEFAULT 1,
                        created_at TEXT,
                        updated_at TEXT
                    )
                ''')
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS safety_checks (
                        check_id TEXT PRIMARY KEY,
                        safety_id TEXT NOT NULL,
                        check_date TEXT,
                        checker_id INTEGER,
                        checker_name TEXT,
                        check_items TEXT,
                        results TEXT,
                        issues_found INTEGER DEFAULT 0,
                        corrective_actions TEXT,
                        education_type TEXT,
                        created_at TEXT
                    )
                ''')
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS biology_education (
                        education_id TEXT PRIMARY KEY,
                        program_name TEXT NOT NULL,
                        education_type TEXT,
                        education_level TEXT,
                        target_age TEXT,
                        duration TEXT,
                        curriculum TEXT,
                        objectives TEXT,
                        assessment_method TEXT,
                        instructor_id INTEGER,
                        instructor_name TEXT,
                        max_participants INTEGER DEFAULT 30,
                        enrolled_count INTEGER DEFAULT 0,
                        status TEXT DEFAULT 'open',
                        created_at TEXT,
                        updated_at TEXT
                    )
                ''')
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS education_sessions (
                        session_id TEXT PRIMARY KEY,
                        education_id TEXT NOT NULL,
                        session_date TEXT,
                        session_time TEXT,
                        topic TEXT,
                        materials TEXT,
                        attendance_count INTEGER DEFAULT 0,
                        session_notes TEXT,
                        education_type TEXT,
                        created_at TEXT
                    )
                ''')
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS innovation_projects (
                        project_id TEXT PRIMARY KEY,
                        project_name TEXT NOT NULL,
                        project_type TEXT,
                        application_area TEXT,
                        description TEXT,
                        objectives TEXT,
                        team_members TEXT,
                        mentor_id INTEGER,
                        mentor_name TEXT,
                        budget REAL DEFAULT 0,
                        start_date TEXT,
                        end_date TEXT,
                        status TEXT DEFAULT 'proposed',
                        education_type TEXT,
                        created_at TEXT,
                        updated_at TEXT
                    )
                ''')
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS project_submissions (
                        submission_id TEXT PRIMARY KEY,
                        project_id TEXT NOT NULL,
                        submission_date TEXT,
                        submission_type TEXT,
                        content TEXT,
                        documents TEXT,
                        reviewer_id INTEGER,
                        reviewer_name TEXT,
                        review_status TEXT DEFAULT 'pending',
                        review_comments TEXT,
                        score REAL,
                        education_type TEXT,
                        created_at TEXT
                    )
                ''')
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS lab_equipment (
                        equipment_id TEXT PRIMARY KEY,
                        equipment_name TEXT NOT NULL,
                        equipment_type TEXT,
                        model TEXT,
                        manufacturer TEXT,
                        purchase_date TEXT,
                        location TEXT,
                        status TEXT DEFAULT 'available',
                        last_maintenance TEXT,
                        maintenance_interval TEXT,
                        safety_requirements TEXT,
                        education_type TEXT,
                        created_at TEXT,
                        updated_at TEXT
                    )
                ''')
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS equipment_usage (
                        usage_id TEXT PRIMARY KEY,
                        equipment_id TEXT NOT NULL,
                        user_id INTEGER,
                        user_name TEXT,
                        usage_date TEXT,
                        start_time TEXT,
                        end_time TEXT,
                        purpose TEXT,
                        education_type TEXT,
                        created_at TEXT
                    )
                ''')
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS biology_research (
                        research_id TEXT PRIMARY KEY,
                        research_title TEXT NOT NULL,
                        research_type TEXT,
                        hypothesis TEXT,
                        methodology TEXT,
                        participants TEXT,
                        duration TEXT,
                        funding_source TEXT,
                        status TEXT DEFAULT 'planning',
                        education_type TEXT,
                        created_at TEXT,
                        updated_at TEXT
                    )
                ''')
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS research_records (
                        record_id TEXT PRIMARY KEY,
                        research_id TEXT NOT NULL,
                        record_date TEXT,
                        record_type TEXT,
                        data TEXT,
                        observations TEXT,
                        conclusions TEXT,
                        researcher_id INTEGER,
                        researcher_name TEXT,
                        education_type TEXT,
                        created_at TEXT
                    )
                ''')
                conn.commit()
                logger.info('教育合成生物学服务数据库初始化完成')
        except Exception as e:
            logger.error(f'数据库初始化失败: {e}')

    # ========== 合成生物学课程 ==========

    def create_synthetic_course(self, course_name: str, concept: str,
                                 education_level: str, education_type: str,
                                 **kwargs) -> Dict[str, Any]:
        try:
            course_id = f"syn_{uuid.uuid4().hex[:12]}"
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('''
                        INSERT INTO synthetic_courses (
                            course_id, course_name, concept, education_level,
                            education_type, grade_level, teacher_id, teacher_name,
                            semester, weekly_hours, location, max_students,
                            enrolled_count, description, prerequisites, status,
                            created_at, updated_at
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 0, ?, ?, 'active', ?, ?)
                    ''', (course_id, course_name, concept, education_level,
                          education_type, kwargs.get('grade_level'),
                          kwargs.get('teacher_id'), kwargs.get('teacher_name'),
                          kwargs.get('semester'), kwargs.get('weekly_hours', 3),
                          kwargs.get('location'), kwargs.get('max_students', 20),
                          kwargs.get('description'), kwargs.get('prerequisites'),
                          now, now))
                    conn.commit()
                    logger.info(f'创建合成生物学课程: {course_name} ({course_id})')
                    return {'success': True, 'course_id': course_id}
        except Exception as e:
            logger.error(f'创建合成生物学课程失败: {e}')
            return {'success': False, 'error': str(e)}

    def enroll_synthetic_course(self, course_id: str, student_id: int,
                                 student_name: str = None) -> Dict[str, Any]:
        try:
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('SELECT max_students, enrolled_count, status FROM synthetic_courses WHERE course_id = ?', (course_id,))
                    course = cursor.fetchone()
                    if not course:
                        return {'success': False, 'error': '课程不存在'}
                    if course[2] != 'active':
                        return {'success': False, 'error': '课程状态不允许选课'}
                    if course[0] and course[1] >= course[0]:
                        return {'success': False, 'error': '课程名额已满'}
                    cursor.execute('''
                        INSERT OR IGNORE INTO art_enrollments (course_id, student_id, student_name, enroll_date)
                        VALUES (?, ?, ?, ?)
                    ''', (course_id, student_id, student_name, now[:10]))
                    if cursor.rowcount > 0:
                        cursor.execute('UPDATE synthetic_courses SET enrolled_count = enrolled_count + 1, updated_at = ? WHERE course_id = ?', (now, course_id))
                        conn.commit()
                        return {'success': True}
                    return {'success': False, 'error': '已选该课程'}
        except Exception as e:
            logger.error(f'合成生物学选课失败: {e}')
            return {'success': False, 'error': str(e)}

    def create_course_lab(self, course_id: str, lab_name: str,
                           **kwargs) -> Dict[str, Any]:
        try:
            lab_id = f"lab_{uuid.uuid4().hex[:12]}"
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('''
                        INSERT INTO course_labs (
                            lab_id, course_id, lab_name, lab_type, safety_level,
                            duration_hours, equipment_required, materials,
                            procedure, expected_outcome, education_type, status,
                            created_at, updated_at
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'planned', ?, ?)
                    ''', (lab_id, course_id, lab_name, kwargs.get('lab_type'),
                          kwargs.get('safety_level', 'BSL-1'),
                          kwargs.get('duration_hours', 3),
                          kwargs.get('equipment_required'),
                          kwargs.get('materials'), kwargs.get('procedure'),
                          kwargs.get('expected_outcome'),
                          kwargs.get('education_type'), now, now))
                    conn.commit()
                    logger.info(f'创建课程实验: {lab_name} ({lab_id})')
                    return {'success': True, 'lab_id': lab_id}
        except Exception as e:
            logger.error(f'创建课程实验失败: {e}')
            return {'success': False, 'error': str(e)}

    def get_course_labs(self, course_id: str, **kwargs) -> Dict[str, Any]:
        try:
            with self._get_connection() as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                query = 'SELECT * FROM course_labs WHERE course_id = ?'
                params = [course_id]
                if kwargs.get('status'):
                    query += ' AND status = ?'
                    params.append(kwargs.get('status'))
                cursor.execute(query, params)
                labs = [dict(l) for l in cursor.fetchall()]
                return {'success': True, 'labs': labs}
        except Exception as e:
            logger.error(f'获取课程实验失败: {e}')
            return {'success': False, 'error': str(e)}

    # ========== 基因编辑 ==========

    def create_gene_editing(self, target_gene: str, organism: str,
                             education_type: str, education_level: str,
                             **kwargs) -> Dict[str, Any]:
        try:
            editing_id = f"ged_{uuid.uuid4().hex[:12]}"
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('''
                        INSERT INTO gene_editing (
                            editing_id, target_gene, organism, tool, guide_rna,
                            editing_type, education_type, education_level, status,
                            created_at, updated_at
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, 'design', ?, ?)
                    ''', (editing_id, target_gene, organism, kwargs.get('tool'),
                          kwargs.get('guide_rna'), kwargs.get('editing_type'),
                          education_type, education_level, now, now))
                    conn.commit()
                    logger.info(f'创建基因编辑项目: {target_gene} ({editing_id})')
                    return {'success': True, 'editing_id': editing_id}
        except Exception as e:
            logger.error(f'创建基因编辑项目失败: {e}')
            return {'success': False, 'error': str(e)}

    def run_editing_experiment(self, editing_id: str, experiment_name: str,
                                student_id: int, **kwargs) -> Dict[str, Any]:
        try:
            experiment_id = f"eex_{uuid.uuid4().hex[:12]}"
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('''
                        INSERT INTO editing_experiments (
                            experiment_id, editing_id, experiment_name, student_id,
                            student_name, experiment_date, cell_line,
                            transfection_method, education_type
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                    ''', (experiment_id, editing_id, experiment_name, student_id,
                          kwargs.get('student_name'), now[:10],
                          kwargs.get('cell_line'), kwargs.get('transfection_method'),
                          kwargs.get('education_type')))
                    cursor.execute('UPDATE gene_editing SET status = ?, updated_at = ? WHERE editing_id = ?', ('in_progress', now, editing_id))
                    conn.commit()
                    return {'success': True, 'experiment_id': experiment_id}
        except Exception as e:
            logger.error(f'运行基因编辑实验失败: {e}')
            return {'success': False, 'error': str(e)}

    def record_editing_result(self, experiment_id: str, efficiency: float,
                               result: str, **kwargs) -> Dict[str, Any]:
        try:
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('''
                        UPDATE editing_experiments SET
                            efficiency = ?, result = ?, off_target_count = ?, notes = ?
                        WHERE experiment_id = ?
                    ''', (efficiency, result, kwargs.get('off_target_count', 0),
                          kwargs.get('notes'), experiment_id))
                    cursor.execute('SELECT editing_id FROM editing_experiments WHERE experiment_id = ?', (experiment_id,))
                    row = cursor.fetchone()
                    if row:
                        cursor.execute('UPDATE gene_editing SET status = ?, updated_at = ? WHERE editing_id = ?', (result, now, row[0]))
                    conn.commit()
                    return {'success': True}
        except Exception as e:
            logger.error(f'记录基因编辑结果失败: {e}')
            return {'success': False, 'error': str(e)}

    def get_gene_editing_history(self, student_id: int = None, **kwargs) -> Dict[str, Any]:
        try:
            with self._get_connection() as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                query = 'SELECT * FROM gene_editing WHERE 1=1'
                params = []
                if student_id:
                    query += ' AND editing_id IN (SELECT editing_id FROM editing_experiments WHERE student_id = ?)'
                    params.append(student_id)
                if kwargs.get('education_type'):
                    query += ' AND education_type = ?'
                    params.append(kwargs.get('education_type'))
                if kwargs.get('status'):
                    query += ' AND status = ?'
                    params.append(kwargs.get('status'))
                query += ' ORDER BY created_at DESC'
                cursor.execute(query, params)
                editings = [dict(e) for e in cursor.fetchall()]
                return {'success': True, 'editings': editings}
        except Exception as e:
            logger.error(f'获取基因编辑历史失败: {e}')
            return {'success': False, 'error': str(e)}

    # ========== DNA合成 ==========

    def create_dna_synthesis(self, sequence_name: str, sequence: str,
                              synthesis_type: str, education_type: str,
                              **kwargs) -> Dict[str, Any]:
        try:
            synthesis_id = f"dns_{uuid.uuid4().hex[:12]}"
            now = datetime.now().isoformat()
            gc_content = (sequence.count('G') + sequence.count('C')) / len(sequence) * 100 if sequence else 0
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('''
                        INSERT INTO dna_synthesis (
                            synthesis_id, sequence_name, sequence, length,
                            synthesis_type, organism, gc_content,
                            purification_method, education_type, status,
                            created_at, updated_at
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, 'pending', ?, ?)
                    ''', (synthesis_id, sequence_name, sequence, len(sequence),
                          synthesis_type, kwargs.get('organism'), gc_content,
                          kwargs.get('purification_method'), education_type,
                          now, now))
                    conn.commit()
                    logger.info(f'创建DNA合成: {sequence_name} ({synthesis_id})')
                    return {'success': True, 'synthesis_id': synthesis_id}
        except Exception as e:
            logger.error(f'创建DNA合成失败: {e}')
            return {'success': False, 'error': str(e)}

    def place_synthesis_order(self, synthesis_id: str, **kwargs) -> Dict[str, Any]:
        try:
            order_id = f"spo_{uuid.uuid4().hex[:12]}"
            now = datetime.now().isoformat()
            delivery_date = (datetime.now() + timedelta(days=kwargs.get('delivery_days', 14))).isoformat()[:10]
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('''
                        INSERT INTO synthesis_orders (
                            order_id, synthesis_id, quantity, delivery_date,
                            price, payment_status, education_type,
                            created_at, updated_at
                        ) VALUES (?, ?, ?, ?, ?, 'unpaid', ?, ?, ?)
                    ''', (order_id, synthesis_id, kwargs.get('quantity', 1),
                          delivery_date, kwargs.get('price', 0),
                          kwargs.get('education_type'), now, now))
                    cursor.execute('UPDATE dna_synthesis SET status = ?, updated_at = ? WHERE synthesis_id = ?', ('ordered', now, synthesis_id))
                    conn.commit()
                    return {'success': True, 'order_id': order_id, 'delivery_date': delivery_date}
        except Exception as e:
            logger.error(f'提交合成订单失败: {e}')
            return {'success': False, 'error': str(e)}

    def update_synthesis_quality(self, synthesis_id: str, quality_score: float,
                                 **kwargs) -> Dict[str, Any]:
        try:
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('''
                        UPDATE dna_synthesis SET
                            quality_score = ?, purification_method = ?, status = ?
                        WHERE synthesis_id = ?
                    ''', (quality_score, kwargs.get('purification_method'),
                          'completed', synthesis_id))
                    if cursor.rowcount > 0:
                        conn.commit()
                        return {'success': True, 'quality_score': quality_score}
                    return {'success': False, 'error': '合成记录不存在'}
        except Exception as e:
            logger.error(f'更新合成质量失败: {e}')
            return {'success': False, 'error': str(e)}

    def get_dna_synthesis_records(self, **kwargs) -> Dict[str, Any]:
        try:
            with self._get_connection() as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                query = 'SELECT * FROM dna_synthesis WHERE 1=1'
                params = []
                if kwargs.get('education_type'):
                    query += ' AND education_type = ?'
                    params.append(kwargs.get('education_type'))
                if kwargs.get('status'):
                    query += ' AND status = ?'
                    params.append(kwargs.get('status'))
                if kwargs.get('synthesis_type'):
                    query += ' AND synthesis_type = ?'
                    params.append(kwargs.get('synthesis_type'))
                query += ' ORDER BY created_at DESC'
                cursor.execute(query, params)
                syntheses = [dict(s) for s in cursor.fetchall()]
                return {'success': True, 'syntheses': syntheses}
        except Exception as e:
            logger.error(f'获取DNA合成记录失败: {e}')
            return {'success': False, 'error': str(e)}

    # ========== 电路设计 ==========

    def create_circuit_design(self, design_name: str, circuit_type: str,
                               education_type: str, education_level: str,
                               **kwargs) -> Dict[str, Any]:
        try:
            design_id = f"crd_{uuid.uuid4().hex[:12]}"
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('''
                        INSERT INTO circuit_design (
                            design_id, design_name, circuit_type, components,
                            logic_description, organism, promoter,
                            ribosome_binding, terminator, education_type,
                            education_level, status, created_at, updated_at
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'design', ?, ?)
                    ''', (design_id, design_name, circuit_type,
                          kwargs.get('components'), kwargs.get('logic_description'),
                          kwargs.get('organism'), kwargs.get('promoter'),
                          kwargs.get('ribosome_binding'), kwargs.get('terminator'),
                          education_type, education_level, now, now))
                    conn.commit()
                    logger.info(f'创建电路设计: {design_name} ({design_id})')
                    return {'success': True, 'design_id': design_id}
        except Exception as e:
            logger.error(f'创建电路设计失败: {e}')
            return {'success': False, 'error': str(e)}

    def simulate_circuit(self, design_id: str, **kwargs) -> Dict[str, Any]:
        try:
            now = datetime.now().isoformat()
            simulation_results = json.dumps({'simulation': 'completed', 'timestamp': now})
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('UPDATE circuit_design SET simulation_results = ?, status = ?, updated_at = ? WHERE design_id = ?',
                                 (simulation_results, 'simulated', now, design_id))
                    if cursor.rowcount > 0:
                        conn.commit()
                        return {'success': True, 'simulation_results': simulation_results}
                    return {'success': False, 'error': '设计不存在'}
        except Exception as e:
            logger.error(f'电路模拟失败: {e}')
            return {'success': False, 'error': str(e)}

    def create_design_project(self, design_id: str, project_name: str,
                               student_id: int, **kwargs) -> Dict[str, Any]:
        try:
            project_id = f"dpj_{uuid.uuid4().hex[:12]}"
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('''
                        INSERT INTO design_projects (
                            project_id, design_id, project_name, student_id,
                            student_name, phase, progress, milestone,
                            deadline, education_type, created_at, updated_at
                        ) VALUES (?, ?, ?, ?, ?, 'planning', 0, ?, ?, ?, ?, ?)
                    ''', (project_id, design_id, project_name, student_id,
                          kwargs.get('student_name'), kwargs.get('milestone'),
                          kwargs.get('deadline'), kwargs.get('education_type'),
                          now, now))
                    conn.commit()
                    return {'success': True, 'project_id': project_id}
        except Exception as e:
            logger.error(f'创建设计项目失败: {e}')
            return {'success': False, 'error': str(e)}

    def update_project_progress(self, project_id: str, progress: float,
                                 **kwargs) -> Dict[str, Any]:
        try:
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('''
                        UPDATE design_projects SET
                            progress = ?, phase = ?, milestone = ?, updated_at = ?
                        WHERE project_id = ?
                    ''', (progress, kwargs.get('phase'), kwargs.get('milestone'),
                          now, project_id))
                    if cursor.rowcount > 0:
                        conn.commit()
                        return {'success': True, 'progress': progress}
                    return {'success': False, 'error': '项目不存在'}
        except Exception as e:
            logger.error(f'更新项目进度失败: {e}')
            return {'success': False, 'error': str(e)}

    # ========== 生物信息学 ==========

    def create_bioinformatics_analysis(self, analysis_name: str, analysis_type: str,
                                        education_type: str, education_level: str,
                                        **kwargs) -> Dict[str, Any]:
        try:
            analysis_id = f"bif_{uuid.uuid4().hex[:12]}"
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('''
                        INSERT INTO bioinformatics (
                            analysis_id, analysis_name, analysis_type, input_data,
                            tools_used, parameters, education_type, education_level,
                            status, created_at, updated_at
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, 'running', ?, ?)
                    ''', (analysis_id, analysis_name, analysis_type,
                          kwargs.get('input_data'), kwargs.get('tools_used'),
                          kwargs.get('parameters'), education_type, education_level,
                          now, now))
                    conn.commit()
                    logger.info(f'创建生物信息学分析: {analysis_name} ({analysis_id})')
                    return {'success': True, 'analysis_id': analysis_id}
        except Exception as e:
            logger.error(f'创建生物信息学分析失败: {e}')
            return {'success': False, 'error': str(e)}

    def add_analysis_task(self, analysis_id: str, task_name: str,
                           task_type: str, **kwargs) -> Dict[str, Any]:
        try:
            task_id = f"ant_{uuid.uuid4().hex[:12]}"
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('''
                        INSERT INTO analysis_tasks (
                            task_id, analysis_id, task_name, task_type,
                            input_file, education_type, created_at, updated_at
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                    ''', (task_id, analysis_id, task_name, task_type,
                          kwargs.get('input_file'), kwargs.get('education_type'),
                          now, now))
                    conn.commit()
                    return {'success': True, 'task_id': task_id}
        except Exception as e:
            logger.error(f'添加分析任务失败: {e}')
            return {'success': False, 'error': str(e)}

    def complete_analysis_task(self, task_id: str, output_file: str,
                                **kwargs) -> Dict[str, Any]:
        try:
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('''
                        UPDATE analysis_tasks SET
                            output_file = ?, status = 'completed',
                            execution_time = ?, error_message = ?, updated_at = ?
                        WHERE task_id = ?
                    ''', (output_file, kwargs.get('execution_time'),
                          kwargs.get('error_message'), now, task_id))
                    if cursor.rowcount > 0:
                        conn.commit()
                        return {'success': True}
                    return {'success': False, 'error': '任务不存在'}
        except Exception as e:
            logger.error(f'完成分析任务失败: {e}')
            return {'success': False, 'error': str(e)}

    def finalize_analysis(self, analysis_id: str, results_summary: str,
                           **kwargs) -> Dict[str, Any]:
        try:
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('''
                        UPDATE bioinformatics SET
                            results_summary = ?, output_data = ?, status = 'completed',
                            updated_at = ?
                        WHERE analysis_id = ?
                    ''', (results_summary, kwargs.get('output_data'), now, analysis_id))
                    if cursor.rowcount > 0:
                        conn.commit()
                        return {'success': True}
                    return {'success': False, 'error': '分析不存在'}
        except Exception as e:
            logger.error(f'完成分析失败: {e}')
            return {'success': False, 'error': str(e)}

    def get_analysis_history(self, **kwargs) -> Dict[str, Any]:
        try:
            with self._get_connection() as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                query = 'SELECT * FROM bioinformatics WHERE 1=1'
                params = []
                if kwargs.get('education_type'):
                    query += ' AND education_type = ?'
                    params.append(kwargs.get('education_type'))
                if kwargs.get('education_level'):
                    query += ' AND education_level = ?'
                    params.append(kwargs.get('education_level'))
                if kwargs.get('status'):
                    query += ' AND status = ?'
                    params.append(kwargs.get('status'))
                query += ' ORDER BY created_at DESC'
                cursor.execute(query, params)
                analyses = [dict(a) for a in cursor.fetchall()]
                return {'success': True, 'analyses': analyses}
        except Exception as e:
            logger.error(f'获取分析历史失败: {e}')
            return {'success': False, 'error': str(e)}

    # ========== 实验室安全 ==========

    def create_safety_protocol(self, protocol_name: str, safety_level: str,
                                category: str, education_type: str,
                                **kwargs) -> Dict[str, Any]:
        try:
            safety_id = f"sft_{uuid.uuid4().hex[:12]}"
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('''
                        INSERT INTO lab_safety (
                            safety_id, protocol_name, safety_level, category,
                            description, procedures, required_training,
                            documentation, education_type, is_active,
                            created_at, updated_at
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, 1, ?, ?)
                    ''', (safety_id, protocol_name, safety_level, category,
                          kwargs.get('description'), kwargs.get('procedures'),
                          kwargs.get('required_training'), kwargs.get('documentation'),
                          education_type, now, now))
                    conn.commit()
                    logger.info(f'创建安全协议: {protocol_name} ({safety_id})')
                    return {'success': True, 'safety_id': safety_id}
        except Exception as e:
            logger.error(f'创建安全协议失败: {e}')
            return {'success': False, 'error': str(e)}

    def perform_safety_check(self, safety_id: str, checker_id: int,
                              **kwargs) -> Dict[str, Any]:
        try:
            check_id = f"chk_{uuid.uuid4().hex[:12]}"
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('''
                        INSERT INTO safety_checks (
                            check_id, safety_id, check_date, checker_id,
                            checker_name, check_items, results, issues_found,
                            corrective_actions, education_type, created_at
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    ''', (check_id, safety_id, now[:10], checker_id,
                          kwargs.get('checker_name'), kwargs.get('check_items'),
                          kwargs.get('results', 'passed'), kwargs.get('issues_found', 0),
                          kwargs.get('corrective_actions'), kwargs.get('education_type'),
                          now))
                    conn.commit()
                    return {'success': True, 'check_id': check_id}
        except Exception as e:
            logger.error(f'执行安全检查失败: {e}')
            return {'success': False, 'error': str(e)}

    def get_safety_protocols(self, **kwargs) -> Dict[str, Any]:
        try:
            with self._get_connection() as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                query = 'SELECT * FROM lab_safety WHERE 1=1'
                params = []
                if kwargs.get('education_type'):
                    query += ' AND education_type = ?'
                    params.append(kwargs.get('education_type'))
                if kwargs.get('safety_level'):
                    query += ' AND safety_level = ?'
                    params.append(kwargs.get('safety_level'))
                if kwargs.get('is_active') is not None:
                    query += ' AND is_active = ?'
                    params.append(1 if kwargs.get('is_active') else 0)
                query += ' ORDER BY created_at DESC'
                cursor.execute(query, params)
                protocols = [dict(p) for p in cursor.fetchall()]
                return {'success': True, 'protocols': protocols}
        except Exception as e:
            logger.error(f'获取安全协议失败: {e}')
            return {'success': False, 'error': str(e)}

    def get_safety_check_history(self, safety_id: str = None, **kwargs) -> Dict[str, Any]:
        try:
            with self._get_connection() as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                query = 'SELECT * FROM safety_checks WHERE 1=1'
                params = []
                if safety_id:
                    query += ' AND safety_id = ?'
                    params.append(safety_id)
                if kwargs.get('education_type'):
                    query += ' AND education_type = ?'
                    params.append(kwargs.get('education_type'))
                query += ' ORDER BY check_date DESC'
                cursor.execute(query, params)
                checks = [dict(c) for c in cursor.fetchall()]
                return {'success': True, 'checks': checks}
        except Exception as e:
            logger.error(f'获取安全检查历史失败: {e}')
            return {'success': False, 'error': str(e)}

    # ========== 生物教育 ==========

    def create_education_program(self, program_name: str, education_type: str,
                                  education_level: str, **kwargs) -> Dict[str, Any]:
        try:
            education_id = f"edu_{uuid.uuid4().hex[:12]}"
            now = datetime.now().isoformat()
            config = EDUCATION_LEVELS.get(education_level, {})
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('''
                        INSERT INTO biology_education (
                            education_id, program_name, education_type, education_level,
                            target_age, duration, curriculum, objectives,
                            assessment_method, instructor_id, instructor_name,
                            max_participants, enrolled_count, status,
                            created_at, updated_at
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 0, 'open', ?, ?)
                    ''', (education_id, program_name, education_type, education_level,
                          kwargs.get('target_age', config.get('age_range')),
                          kwargs.get('duration', config.get('duration')),
                          kwargs.get('curriculum'), kwargs.get('objectives'),
                          kwargs.get('assessment_method'), kwargs.get('instructor_id'),
                          kwargs.get('instructor_name'), kwargs.get('max_participants', 30),
                          now, now))
                    conn.commit()
                    logger.info(f'创建生物教育项目: {program_name} ({education_id})')
                    return {'success': True, 'education_id': education_id}
        except Exception as e:
            logger.error(f'创建生物教育项目失败: {e}')
            return {'success': False, 'error': str(e)}

    def create_education_session(self, education_id: str, session_date: str,
                                  topic: str, **kwargs) -> Dict[str, Any]:
        try:
            session_id = f"ses_{uuid.uuid4().hex[:12]}"
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('''
                        INSERT INTO education_sessions (
                            session_id, education_id, session_date, session_time,
                            topic, materials, education_type, created_at
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                    ''', (session_id, education_id, session_date,
                          kwargs.get('session_time', '09:00'), topic,
                          kwargs.get('materials'), kwargs.get('education_type'),
                          now))
                    conn.commit()
                    return {'success': True, 'session_id': session_id}
        except Exception as e:
            logger.error(f'创建教育课时失败: {e}')
            return {'success': False, 'error': str(e)}

    def enroll_education_program(self, education_id: str, student_id: int,
                                  student_name: str = None) -> Dict[str, Any]:
        try:
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('SELECT max_participants, enrolled_count, status FROM biology_education WHERE education_id = ?', (education_id,))
                    program = cursor.fetchone()
                    if not program:
                        return {'success': False, 'error': '教育项目不存在'}
                    if program[2] != 'open':
                        return {'success': False, 'error': '教育项目状态不允许报名'}
                    if program[0] and program[1] >= program[0]:
                        return {'success': False, 'error': '名额已满'}
                    cursor.execute('''
                        INSERT OR IGNORE INTO art_enrollments (course_id, student_id, student_name, enroll_date)
                        VALUES (?, ?, ?, ?)
                    ''', (education_id, student_id, student_name, now[:10]))
                    if cursor.rowcount > 0:
                        cursor.execute('UPDATE biology_education SET enrolled_count = enrolled_count + 1, updated_at = ? WHERE education_id = ?', (now, education_id))
                        conn.commit()
                        return {'success': True}
                    return {'success': False, 'error': '已报名该项目'}
        except Exception as e:
            logger.error(f'报名教育项目失败: {e}')
            return {'success': False, 'error': str(e)}

    def get_education_programs(self, **kwargs) -> Dict[str, Any]:
        try:
            with self._get_connection() as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                query = 'SELECT * FROM biology_education WHERE 1=1'
                params = []
                if kwargs.get('education_type'):
                    query += ' AND education_type = ?'
                    params.append(kwargs.get('education_type'))
                if kwargs.get('education_level'):
                    query += ' AND education_level = ?'
                    params.append(kwargs.get('education_level'))
                if kwargs.get('status'):
                    query += ' AND status = ?'
                    params.append(kwargs.get('status'))
                query += ' ORDER BY created_at DESC'
                cursor.execute(query, params)
                programs = [dict(p) for p in cursor.fetchall()]
                return {'success': True, 'programs': programs}
        except Exception as e:
            logger.error(f'获取教育项目失败: {e}')
            return {'success': False, 'error': str(e)}

    # ========== 创新项目 ==========

    def create_innovation_project(self, project_name: str, project_type: str,
                                   application_area: str, education_type: str,
                                   **kwargs) -> Dict[str, Any]:
        try:
            project_id = f"inv_{uuid.uuid4().hex[:12]}"
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('''
                        INSERT INTO innovation_projects (
                            project_id, project_name, project_type, application_area,
                            description, objectives, team_members, mentor_id,
                            mentor_name, budget, start_date, end_date, status,
                            education_type, created_at, updated_at
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'proposed', ?, ?, ?)
                    ''', (project_id, project_name, project_type, application_area,
                          kwargs.get('description'), kwargs.get('objectives'),
                          kwargs.get('team_members'), kwargs.get('mentor_id'),
                          kwargs.get('mentor_name'), kwargs.get('budget', 0),
                          now[:10], kwargs.get('end_date'), education_type,
                          now, now))
                    conn.commit()
                    logger.info(f'创建创新项目: {project_name} ({project_id})')
                    return {'success': True, 'project_id': project_id}
        except Exception as e:
            logger.error(f'创建创新项目失败: {e}')
            return {'success': False, 'error': str(e)}

    def submit_project_deliverable(self, project_id: str, submission_type: str,
                                    content: str, **kwargs) -> Dict[str, Any]:
        try:
            submission_id = f"psb_{uuid.uuid4().hex[:12]}"
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('''
                        INSERT INTO project_submissions (
                            submission_id, project_id, submission_date, submission_type,
                            content, documents, reviewer_id, reviewer_name,
                            review_status, education_type, created_at
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, 'pending', ?, ?)
                    ''', (submission_id, project_id, now[:10], submission_type,
                          content, kwargs.get('documents'), kwargs.get('reviewer_id'),
                          kwargs.get('reviewer_name'), kwargs.get('education_type'),
                          now))
                    conn.commit()
                    return {'success': True, 'submission_id': submission_id}
        except Exception as e:
            logger.error(f'提交项目成果失败: {e}')
            return {'success': False, 'error': str(e)}

    def review_project_submission(self, submission_id: str, review_status: str,
                                   **kwargs) -> Dict[str, Any]:
        try:
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('''
                        UPDATE project_submissions SET
                            review_status = ?, review_comments = ?, score = ?, updated_at = ?
                        WHERE submission_id = ?
                    ''', (review_status, kwargs.get('review_comments'),
                          kwargs.get('score'), now, submission_id))
                    if cursor.rowcount > 0:
                        conn.commit()
                        return {'success': True, 'review_status': review_status}
                    return {'success': False, 'error': '提交记录不存在'}
        except Exception as e:
            logger.error(f'评审项目提交失败: {e}')
            return {'success': False, 'error': str(e)}

    def update_project_status(self, project_id: str, status: str,
                               **kwargs) -> Dict[str, Any]:
        try:
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('UPDATE innovation_projects SET status = ?, updated_at = ? WHERE project_id = ?',
                                 (status, now, project_id))
                    if cursor.rowcount > 0:
                        conn.commit()
                        return {'success': True, 'status': status}
                    return {'success': False, 'error': '项目不存在'}
        except Exception as e:
            logger.error(f'更新项目状态失败: {e}')
            return {'success': False, 'error': str(e)}

    # ========== 设备管理 ==========

    def register_equipment(self, equipment_name: str, equipment_type: str,
                            **kwargs) -> Dict[str, Any]:
        try:
            equipment_id = f"eqp_{uuid.uuid4().hex[:12]}"
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('''
                        INSERT INTO lab_equipment (
                            equipment_id, equipment_name, equipment_type, model,
                            manufacturer, purchase_date, location, status,
                            last_maintenance, maintenance_interval,
                            safety_requirements, education_type,
                            created_at, updated_at
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, 'available', ?, ?, ?, ?, ?, ?)
                    ''', (equipment_id, equipment_name, equipment_type,
                          kwargs.get('model'), kwargs.get('manufacturer'),
                          now[:10], kwargs.get('location'), kwargs.get('last_maintenance'),
                          kwargs.get('maintenance_interval'), kwargs.get('safety_requirements'),
                          kwargs.get('education_type'), now, now))
                    conn.commit()
                    logger.info(f'注册设备: {equipment_name} ({equipment_id})')
                    return {'success': True, 'equipment_id': equipment_id}
        except Exception as e:
            logger.error(f'注册设备失败: {e}')
            return {'success': False, 'error': str(e)}

    def record_equipment_usage(self, equipment_id: str, user_id: int,
                                user_name: str, **kwargs) -> Dict[str, Any]:
        try:
            usage_id = f"equ_{uuid.uuid4().hex[:12]}"
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('SELECT status FROM lab_equipment WHERE equipment_id = ?', (equipment_id,))
                    row = cursor.fetchone()
                    if not row:
                        return {'success': False, 'error': '设备不存在'}
                    if row[0] != 'available':
                        return {'success': False, 'error': '设备不可用'}
                    cursor.execute('''
                        INSERT INTO equipment_usage (
                            usage_id, equipment_id, user_id, user_name,
                            usage_date, start_time, end_time, purpose,
                            education_type, created_at
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    ''', (usage_id, equipment_id, user_id, user_name, now[:10],
                          kwargs.get('start_time', now[11:16]), kwargs.get('end_time'),
                          kwargs.get('purpose'), kwargs.get('education_type'), now))
                    cursor.execute('UPDATE lab_equipment SET status = ?, updated_at = ? WHERE equipment_id = ?', ('in_use', now, equipment_id))
                    conn.commit()
                    return {'success': True, 'usage_id': usage_id}
        except Exception as e:
            logger.error(f'记录设备使用失败: {e}')
            return {'success': False, 'error': str(e)}

    def update_equipment_maintenance(self, equipment_id: str, **kwargs) -> Dict[str, Any]:
        try:
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('''
                        UPDATE lab_equipment SET
                            last_maintenance = ?, status = ?, updated_at = ?
                        WHERE equipment_id = ?
                    ''', (now[:10], kwargs.get('status', 'available'), now, equipment_id))
                    if cursor.rowcount > 0:
                        conn.commit()
                        return {'success': True}
                    return {'success': False, 'error': '设备不存在'}
        except Exception as e:
            logger.error(f'更新设备维护失败: {e}')
            return {'success': False, 'error': str(e)}

    def get_equipment_status(self, **kwargs) -> Dict[str, Any]:
        try:
            with self._get_connection() as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                query = 'SELECT * FROM lab_equipment WHERE 1=1'
                params = []
                if kwargs.get('education_type'):
                    query += ' AND education_type = ?'
                    params.append(kwargs.get('education_type'))
                if kwargs.get('status'):
                    query += ' AND status = ?'
                    params.append(kwargs.get('status'))
                if kwargs.get('equipment_type'):
                    query += ' AND equipment_type = ?'
                    params.append(kwargs.get('equipment_type'))
                query += ' ORDER BY equipment_name'
                cursor.execute(query, params)
                equipments = [dict(e) for e in cursor.fetchall()]
                return {'success': True, 'equipments': equipments}
        except Exception as e:
            logger.error(f'获取设备状态失败: {e}')
            return {'success': False, 'error': str(e)}

    # ========== 统计分析 ==========

    def get_service_statistics(self, education_type: str = None) -> Dict[str, Any]:
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                stats = {}
                tables = [
                    ('synthetic_courses', 'courses'),
                    ('gene_editing', 'gene_editings'),
                    ('dna_synthesis', 'dna_syntheses'),
                    ('circuit_design', 'circuit_designs'),
                    ('bioinformatics', 'bioinformatics_analyses'),
                    ('lab_safety', 'safety_protocols'),
                    ('biology_education', 'education_programs'),
                    ('innovation_projects', 'innovation_projects'),
                    ('lab_equipment', 'equipment')
                ]
                for table, name in tables:
                    if education_type:
                        cursor.execute(f'SELECT COUNT(*) FROM {table} WHERE education_type = ?', (education_type,))
                    else:
                        cursor.execute(f'SELECT COUNT(*) FROM {table}')
                    stats[name] = cursor.fetchone()[0]
                cursor.execute('SELECT COUNT(*) FROM editing_experiments' + (' WHERE education_type = ?' if education_type else ''), ([education_type] if education_type else []))
                stats['editing_experiments'] = cursor.fetchone()[0]
                cursor.execute('SELECT COUNT(*) FROM synthesis_orders' + (' WHERE education_type = ?' if education_type else ''), ([education_type] if education_type else []))
                stats['synthesis_orders'] = cursor.fetchone()[0]
                cursor.execute('SELECT COUNT(*) FROM safety_checks' + (' WHERE education_type = ?' if education_type else ''), ([education_type] if education_type else []))
                stats['safety_checks'] = cursor.fetchone()[0]
                return {'success': True, 'statistics': stats, 'education_type': education_type}
        except Exception as e:
            logger.error(f'获取统计数据失败: {e}')
            return {'success': False, 'error': str(e)}