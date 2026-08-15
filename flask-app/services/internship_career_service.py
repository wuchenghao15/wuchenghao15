#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
MTSCOS 实习就业服务 (v15.6.0)
====================================
提供实习管理、就业指导、岗位推荐和职业发展等综合服务。

核心能力：
1. 实习管理 - 实习岗位、实习申请、实习考核
2. 就业指导 - 职业规划、简历指导、面试辅导
3. 岗位推荐 - 企业招聘、智能匹配、投递管理
4. 校企合作 - 企业合作、实习基地、联合培养
5. 就业统计 - 就业率统计、薪资分析、行业分布
6. 职业测评 - 职业兴趣、能力评估、性格测试
7. 成人就业 - 成人教育职业发展管理
8. K12职业启蒙 - 职业体验、兴趣探索
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
            os.path.join(os.path.dirname(os.path.abspath(__file__)), 'internship_career_service.log'),
            encoding='utf-8'
        ),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger('InternshipCareer')


# ========== 实习配置 ==========

# 实习类型
INTERNSHIP_TYPES = {
    'professional': {'name': '专业实习', 'duration_days': 90, 'required': True},
    'graduation': {'name': '毕业实习', 'duration_days': 120, 'required': True},
    'summer': {'name': '暑期实习', 'duration_days': 30, 'required': False},
    'winter': {'name': '寒假实习', 'duration_days': 21, 'required': False},
    'rotation': {'name': '轮岗实习', 'duration_days': 60, 'required': False},
    'apprentice': {'name': '学徒实习', 'duration_days': 180, 'required': False},
    'adult_practice': {'name': '成人实践', 'duration_days': 60, 'required': True},
    'k12_experience': {'name': 'K12职业体验', 'duration_days': 7, 'required': False}
}

# 实习状态
INTERNSHIP_STATUS = {
    'draft': {'name': '草稿', 'color': '#d9d9d9'},
    'open': {'name': '招募中', 'color': '#1890ff'},
    'applied': {'name': '已申请', 'color': '#faad14'},
    'accepted': {'name': '已录用', 'color': '#52c41a'},
    'rejected': {'name': '已拒绝', 'color': '#f5222d'},
    'ongoing': {'name': '实习中', 'color': '#1890ff'},
    'completed': {'name': '已完成', 'color': '#52c41a'},
    'terminated': {'name': '已终止', 'color': '#8c8c8c'},
    'cancelled': {'name': '已取消', 'color': '#f5222d'}
}

# 企业行业分类
INDUSTRY_CATEGORIES = {
    'it': {'name': '信息技术', 'sub': ['软件开发', '人工智能', '大数据', '云计算', '网络安全']},
    'finance': {'name': '金融行业', 'sub': ['银行', '保险', '证券', '投资', '金融科技']},
    'education': {'name': '教育培训', 'sub': ['K12教育', '高等教育', '职业教育', '在线教育', '语言培训']},
    'manufacturing': {'name': '制造业', 'sub': ['汽车', '电子', '机械', '化工', '纺织']},
    'service': {'name': '服务业', 'sub': ['餐饮', '零售', '物流', '旅游', '咨询']},
    'healthcare': {'name': '医疗健康', 'sub': ['医院', '制药', '医疗器械', '生物技术', '保健品']},
    'media': {'name': '传媒文化', 'sub': ['新闻', '出版', '影视', '广告', '游戏']},
    'trade': {'name': '贸易商业', 'sub': ['进出口', '电子商务', '批发', '零售', '供应链']}
}

# 企业规模
COMPANY_SIZE = {
    'startup': {'name': '初创企业', 'range': '1-50人'},
    'small': {'name': '小型企业', 'range': '50-200人'},
    'medium': {'name': '中型企业', 'range': '200-1000人'},
    'large': {'name': '大型企业', 'range': '1000-5000人'},
    'enterprise': {'name': '集团企业', 'range': '5000人以上'}
}

# 职业测评类型
CAREER_ASSESSMENT_TYPES = {
    'holland': {'name': '霍兰德职业兴趣测试', 'dimensions': 6, 'description': 'RIASEC六型职业兴趣'},
    'mbti': {'name': 'MBTI性格测试', 'dimensions': 4, 'description': '16型人格分析'},
    'big_five': {'name': '大五人格测试', 'dimensions': 5, 'description': 'OCEAN五维人格'},
    'career_maturity': {'name': '职业成熟度测试', 'dimensions': 4, 'description': '职业发展准备度'},
    'ability': {'name': '职业能力测评', 'dimensions': 8, 'description': '多维职业能力评估'},
    'value': {'name': '职业价值观测试', 'dimensions': 6, 'description': '工作价值观偏好'}
}

# 就业状态
EMPLOYMENT_STATUS = {
    'seeking': {'name': '求职中', 'color': '#faad14'},
    'employed': {'name': '已就业', 'color': '#52c41a'},
    'further_study': {'name': '继续深造', 'color': '#1890ff'},
    'entrepreneur': {'name': '自主创业', 'color': '#722ed1'},
    'gap_year': {'name': '间隔年', 'color': '#13c2c2'},
    'military': {'name': '参军入伍', 'color': '#eb2f96'},
    'abroad': {'name': '出国发展', 'color': '#fa8c16'},
    'unemployed': {'name': '待业', 'color': '#8c8c8c'}
}

# 合作类型
COOPERATION_TYPES = {
    'internship_base': {'name': '实习基地', 'description': '长期实习合作基地'},
    'joint_training': {'name': '联合培养', 'description': '校企联合人才培养'},
    'order_class': {'name': '订单班', 'description': '企业定向培养班级'},
    'research': {'name': '科研合作', 'description': '产学研合作项目'},
    'scholarship': {'name': '企业奖学金', 'description': '企业资助奖学金'},
    'campus_recruit': {'name': '校园招聘', 'description': '年度校园招聘合作'}
}


class InternshipCareerService:
    """实习就业服务"""

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
                    CREATE TABLE IF NOT EXISTS internship_positions (
                        position_id TEXT PRIMARY KEY,
                        company_id TEXT,
                        company_name TEXT NOT NULL,
                        position_title TEXT NOT NULL,
                        industry TEXT,
                        city TEXT,
                        salary_range TEXT,
                        internship_type TEXT NOT NULL,
                        duration_days INTEGER,
                        start_date TEXT,
                        headcount INTEGER DEFAULT 1,
                        applied_count INTEGER DEFAULT 0,
                        accepted_count INTEGER DEFAULT 0,
                        description TEXT,
                        requirements TEXT,
                        benefits TEXT,
                        mentor_assigned INTEGER DEFAULT 0,
                        status TEXT DEFAULT 'draft',
                        education_type TEXT,
                        created_by INTEGER,
                        created_at TEXT,
                        updated_at TEXT
                    )
                ''')
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS internship_applications (
                        application_id TEXT PRIMARY KEY,
                        position_id TEXT NOT NULL,
                        student_id INTEGER NOT NULL,
                        student_name TEXT,
                        education_type TEXT,
                        apply_date TEXT,
                        status TEXT DEFAULT 'applied',
                        resume_url TEXT,
                        cover_letter TEXT,
                        interview_date TEXT,
                        interview_result TEXT,
                        offer_date TEXT,
                        start_date TEXT,
                        end_date TEXT,
                        mentor_name TEXT,
                        weekly_report_count INTEGER DEFAULT 0,
                        final_score REAL,
                        evaluation TEXT,
                        certificate_url TEXT,
                        created_at TEXT,
                        updated_at TEXT
                    )
                ''')
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS companies (
                        company_id TEXT PRIMARY KEY,
                        company_name TEXT NOT NULL,
                        industry TEXT,
                        company_size TEXT,
                        city TEXT,
                        address TEXT,
                        contact_person TEXT,
                        contact_phone TEXT,
                        contact_email TEXT,
                        website TEXT,
                        description TEXT,
                        logo_url TEXT,
                        cooperation_type TEXT,
                        is_partner INTEGER DEFAULT 0,
                        total_positions INTEGER DEFAULT 0,
                        total_hired INTEGER DEFAULT 0,
                        rating REAL DEFAULT 0,
                        created_at TEXT,
                        updated_at TEXT
                    )
                ''')
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS career_assessments (
                        assessment_id TEXT PRIMARY KEY,
                        student_id INTEGER NOT NULL,
                        assessment_type TEXT NOT NULL,
                        answers TEXT,
                        result TEXT,
                        result_summary TEXT,
                        score REAL,
                        taken_at TEXT,
                        created_at TEXT
                    )
                ''')
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS employment_records (
                        record_id TEXT PRIMARY KEY,
                        student_id INTEGER NOT NULL,
                        student_name TEXT,
                        education_type TEXT,
                        graduation_year TEXT,
                        company_name TEXT,
                        position_title TEXT,
                        industry TEXT,
        city TEXT,
                        salary REAL,
                        employment_status TEXT,
                        employ_date TEXT,
                        is_related INTEGER DEFAULT 1,
                        source TEXT,
                        created_at TEXT,
                        updated_at TEXT
                    )
                ''')
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS weekly_reports (
                        report_id TEXT PRIMARY KEY,
                        application_id TEXT NOT NULL,
                        student_id INTEGER NOT NULL,
                        week_number INTEGER,
                        report_date TEXT,
                        content TEXT,
                        achievements TEXT,
                        challenges TEXT,
                        plan_next_week TEXT,
                        mentor_comment TEXT,
                        mentor_score INTEGER,
                        created_at TEXT
                    )
                ''')
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS career_guidance (
                        guidance_id TEXT PRIMARY KEY,
                        student_id INTEGER NOT NULL,
                        guidance_type TEXT,
                        topic TEXT,
                        content TEXT,
                        advisor_id INTEGER,
                        advisor_name TEXT,
                        session_date TEXT,
                        duration_minutes INTEGER,
                        rating INTEGER,
                        feedback TEXT,
                        created_at TEXT
                    )
                ''')
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS campus_recruitment (
                        recruit_id TEXT PRIMARY KEY,
                        company_id TEXT,
                        company_name TEXT NOT NULL,
                        event_name TEXT,
                        event_date TEXT,
                        location TEXT,
                        description TEXT,
                        positions TEXT,
                        target_majors TEXT,
                        registration_count INTEGER DEFAULT 0,
                        status TEXT DEFAULT 'scheduled',
                        created_at TEXT,
                        updated_at TEXT
                    )
                ''')
                conn.commit()
                logger.info('实习就业服务数据库初始化完成')
        except Exception as e:
            logger.error(f'数据库初始化失败: {e}')

    # ========== 企业管理 ==========

    def register_company(self, company_name: str, **kwargs) -> Dict[str, Any]:
        try:
            company_id = f"cpy_{uuid.uuid4().hex[:12]}"
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('''
                        INSERT INTO companies (
                            company_id, company_name, industry, company_size,
                            city, address, contact_person, contact_phone,
                            contact_email, website, description, logo_url,
                            cooperation_type, is_partner, created_at, updated_at
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    ''', (company_id, company_name, kwargs.get('industry'),
                          kwargs.get('company_size'), kwargs.get('city'),
                          kwargs.get('address'), kwargs.get('contact_person'),
                          kwargs.get('contact_phone'), kwargs.get('contact_email'),
                          kwargs.get('website'), kwargs.get('description'),
                          kwargs.get('logo_url'), kwargs.get('cooperation_type'),
                          kwargs.get('is_partner', 0), now, now))
                    conn.commit()
                    logger.info(f'注册企业: {company_name} ({company_id})')
                    return {'success': True, 'company_id': company_id}
        except Exception as e:
            logger.error(f'注册企业失败: {e}')
            return {'success': False, 'error': str(e)}

    def get_company(self, company_id: str) -> Optional[Dict[str, Any]]:
        try:
            with self._get_connection() as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                cursor.execute('SELECT * FROM companies WHERE company_id = ?', (company_id,))
                row = cursor.fetchone()
                return dict(row) if row else None
        except Exception as e:
            logger.error(f'获取企业信息失败: {e}')
            return None

    def list_companies(self, industry: str = None, is_partner: bool = None,
                        page: int = 1, page_size: int = 20) -> Dict[str, Any]:
        try:
            with self._get_connection() as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                query = 'SELECT * FROM companies WHERE 1=1'
                params = []
                if industry:
                    query += ' AND industry = ?'
                    params.append(industry)
                if is_partner is not None:
                    query += ' AND is_partner = ?'
                    params.append(1 if is_partner else 0)
                cursor.execute(f'SELECT COUNT(*) as cnt FROM ({query})', params)
                total = cursor.fetchone()['cnt']
                query += ' ORDER BY is_partner DESC, rating DESC LIMIT ? OFFSET ?'
                params.extend([page_size, (page - 1) * page_size])
                cursor.execute(query, params)
                companies = [dict(c) for c in cursor.fetchall()]
                return {'success': True, 'companies': companies, 'total': total, 'page': page, 'page_size': page_size}
        except Exception as e:
            logger.error(f'获取企业列表失败: {e}')
            return {'success': False, 'error': str(e)}

    # ========== 实习岗位 ==========

    def create_position(self, company_id: str, company_name: str,
                         position_title: str, internship_type: str,
                         **kwargs) -> Dict[str, Any]:
        try:
            position_id = f"pos_{uuid.uuid4().hex[:12]}"
            now = datetime.now().isoformat()
            config = INTERNSHIP_TYPES.get(internship_type, {})
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('''
                        INSERT INTO internship_positions (
                            position_id, company_id, company_name, position_title,
                            industry, city, salary_range, internship_type,
                            duration_days, start_date, headcount, description,
                            requirements, benefits, mentor_assigned, status,
                            education_type, created_by, created_at, updated_at
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'open', ?, ?, ?, ?)
                    ''', (position_id, company_id, company_name, position_title,
                          kwargs.get('industry'), kwargs.get('city'),
                          kwargs.get('salary_range'), internship_type,
                          kwargs.get('duration_days', config.get('duration_days', 30)),
                          kwargs.get('start_date'), kwargs.get('headcount', 1),
                          kwargs.get('description'), kwargs.get('requirements'),
                          kwargs.get('benefits'), kwargs.get('mentor_assigned', 0),
                          kwargs.get('education_type'), kwargs.get('created_by'),
                          now, now))
                    cursor.execute('UPDATE companies SET total_positions = total_positions + 1, updated_at = ? WHERE company_id = ?', (now, company_id))
                    conn.commit()
                    logger.info(f'创建实习岗位: {position_title} ({position_id})')
                    return {'success': True, 'position_id': position_id}
        except Exception as e:
            logger.error(f'创建实习岗位失败: {e}')
            return {'success': False, 'error': str(e)}

    def list_positions(self, internship_type: str = None, industry: str = None,
                        city: str = None, education_type: str = None,
                        status: str = 'open', page: int = 1,
                        page_size: int = 20) -> Dict[str, Any]:
        try:
            with self._get_connection() as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                query = 'SELECT * FROM internship_positions WHERE 1=1'
                params = []
                if internship_type:
                    query += ' AND internship_type = ?'
                    params.append(internship_type)
                if industry:
                    query += ' AND industry = ?'
                    params.append(industry)
                if city:
                    query += ' AND city LIKE ?'
                    params.append(f'%{city}%')
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
                positions = [dict(p) for p in cursor.fetchall()]
                return {'success': True, 'positions': positions, 'total': total, 'page': page, 'page_size': page_size}
        except Exception as e:
            logger.error(f'获取岗位列表失败: {e}')
            return {'success': False, 'error': str(e)}

    # ========== 实习申请 ==========

    def apply_internship(self, position_id: str, student_id: int,
                          **kwargs) -> Dict[str, Any]:
        try:
            application_id = f"app_{uuid.uuid4().hex[:12]}"
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('SELECT headcount, applied_count, status FROM internship_positions WHERE position_id = ?', (position_id,))
                    pos = cursor.fetchone()
                    if not pos:
                        return {'success': False, 'error': '岗位不存在'}
                    if pos[2] != 'open':
                        return {'success': False, 'error': f'岗位状态不允许申请: {pos[2]}'}
                    if pos[0] and pos[1] >= pos[0]:
                        return {'success': False, 'error': '岗位名额已满'}
                    cursor.execute('''
                        INSERT INTO internship_applications (
                            application_id, position_id, student_id, student_name,
                            education_type, apply_date, status, resume_url,
                            cover_letter, created_at, updated_at
                        ) VALUES (?, ?, ?, ?, ?, ?, 'applied', ?, ?, ?, ?)
                    ''', (application_id, position_id, student_id,
                          kwargs.get('student_name'), kwargs.get('education_type'),
                          now[:10], kwargs.get('resume_url'),
                          kwargs.get('cover_letter'), now, now))
                    cursor.execute('UPDATE internship_positions SET applied_count = applied_count + 1, updated_at = ? WHERE position_id = ?', (now, position_id))
                    conn.commit()
                    logger.info(f'实习申请: {application_id}')
                    return {'success': True, 'application_id': application_id}
        except Exception as e:
            logger.error(f'申请实习失败: {e}')
            return {'success': False, 'error': str(e)}

    def review_application(self, application_id: str, accepted: bool,
                            **kwargs) -> Dict[str, Any]:
        try:
            now = datetime.now().isoformat()
            status = 'accepted' if accepted else 'rejected'
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('SELECT position_id FROM internship_applications WHERE application_id = ?', (application_id,))
                    app = cursor.fetchone()
                    if not app:
                        return {'success': False, 'error': '申请不存在'}
                    update_fields = ['status = ?', 'interview_result = ?', 'updated_at = ?']
                    params = [status, kwargs.get('interview_result'), now]
                    if accepted:
                        update_fields.extend(['offer_date = ?', 'start_date = ?', 'mentor_name = ?'])
                        params.extend([kwargs.get('offer_date', now[:10]),
                                       kwargs.get('start_date'), kwargs.get('mentor_name')])
                    params.append(application_id)
                    cursor.execute(f'''
                        UPDATE internship_applications SET {", ".join(update_fields)}
                        WHERE application_id = ? AND status IN ('applied', 'ongoing')
                    ''', params)
                    if cursor.rowcount > 0:
                        if accepted:
                            cursor.execute('UPDATE internship_positions SET accepted_count = accepted_count + 1, updated_at = ? WHERE position_id = ?', (now, app[0]))
                        conn.commit()
                        return {'success': True, 'status': status}
                    return {'success': False, 'error': '申请状态不允许审核'}
        except Exception as e:
            logger.error(f'审核实习申请失败: {e}')
            return {'success': False, 'error': str(e)}

    def start_internship(self, application_id: str) -> Dict[str, Any]:
        try:
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('''
                        UPDATE internship_applications SET status = 'ongoing', start_date = ?, updated_at = ?
                        WHERE application_id = ? AND status = 'accepted'
                    ''', (now[:10], now, application_id))
                    if cursor.rowcount > 0:
                        conn.commit()
                        return {'success': True}
                    return {'success': False, 'error': '申请状态不允许开始实习'}
        except Exception as e:
            logger.error(f'开始实习失败: {e}')
            return {'success': False, 'error': str(e)}

    def complete_internship(self, application_id: str, **kwargs) -> Dict[str, Any]:
        try:
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('''
                        UPDATE internship_applications SET
                            status = 'completed', end_date = ?,
                            final_score = ?, evaluation = ?,
                            certificate_url = ?, updated_at = ?
                        WHERE application_id = ? AND status = 'ongoing'
                    ''', (kwargs.get('end_date', now[:10]),
                          kwargs.get('final_score', 0),
                          kwargs.get('evaluation'),
                          kwargs.get('certificate_url'),
                          now, application_id))
                    if cursor.rowcount > 0:
                        conn.commit()
                        logger.info(f'实习完成: {application_id}, 分数: {kwargs.get("final_score", 0)}')
                        return {'success': True}
                    return {'success': False, 'error': '申请状态不允许完成'}
        except Exception as e:
            logger.error(f'完成实习失败: {e}')
            return {'success': False, 'error': str(e)}

    def get_application(self, application_id: str) -> Optional[Dict[str, Any]]:
        try:
            with self._get_connection() as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                cursor.execute('SELECT * FROM internship_applications WHERE application_id = ?', (application_id,))
                row = cursor.fetchone()
                return dict(row) if row else None
        except Exception as e:
            logger.error(f'获取实习申请失败: {e}')
            return None

    def get_student_applications(self, student_id: int,
                                   status: str = None) -> Dict[str, Any]:
        try:
            with self._get_connection() as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                query = 'SELECT * FROM internship_applications WHERE student_id = ?'
                params = [student_id]
                if status:
                    query += ' AND status = ?'
                    params.append(status)
                query += ' ORDER BY created_at DESC'
                cursor.execute(query, params)
                applications = [dict(a) for a in cursor.fetchall()]
                return {'success': True, 'applications': applications}
        except Exception as e:
            logger.error(f'获取学生实习申请失败: {e}')
            return {'success': False, 'error': str(e)}

    # ========== 实习周报 ==========

    def submit_weekly_report(self, application_id: str, student_id: int,
                              **kwargs) -> Dict[str, Any]:
        try:
            report_id = f"rpt_{uuid.uuid4().hex[:12]}"
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('SELECT weekly_report_count FROM internship_applications WHERE application_id = ?', (application_id,))
                    app = cursor.fetchone()
                    if not app:
                        return {'success': False, 'error': '实习申请不存在'}
                    week_number = app[0] + 1
                    cursor.execute('''
                        INSERT INTO weekly_reports (
                            report_id, application_id, student_id, week_number,
                            report_date, content, achievements, challenges,
                            plan_next_week, created_at
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    ''', (report_id, application_id, student_id, week_number,
                          now[:10], kwargs.get('content'),
                          kwargs.get('achievements'), kwargs.get('challenges'),
                          kwargs.get('plan_next_week'), now))
                    cursor.execute('UPDATE internship_applications SET weekly_report_count = ?, updated_at = ? WHERE application_id = ?', (week_number, now, application_id))
                    conn.commit()
                    return {'success': True, 'report_id': report_id, 'week_number': week_number}
        except Exception as e:
            logger.error(f'提交周报失败: {e}')
            return {'success': False, 'error': str(e)}

    def review_weekly_report(self, report_id: str, mentor_comment: str,
                              mentor_score: int, **kwargs) -> Dict[str, Any]:
        try:
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('''
                        UPDATE weekly_reports SET mentor_comment = ?, mentor_score = ?
                        WHERE report_id = ?
                    ''', (mentor_comment, mentor_score, report_id))
                    if cursor.rowcount > 0:
                        conn.commit()
                        return {'success': True}
                    return {'success': False, 'error': '周报不存在'}
        except Exception as e:
            logger.error(f'审核周报失败: {e}')
            return {'success': False, 'error': str(e)}

    # ========== 职业测评 ==========

    def take_career_assessment(self, student_id: int, assessment_type: str,
                                answers: List[Any], **kwargs) -> Dict[str, Any]:
        try:
            assessment_id = f"cas_{uuid.uuid4().hex[:12]}"
            now = datetime.now().isoformat()
            config = CAREER_ASSESSMENT_TYPES.get(assessment_type)
            if not config:
                return {'success': False, 'error': '测评类型不存在'}
            result = self._calculate_assessment_result(assessment_type, answers)
            answers_json = json.dumps(answers, ensure_ascii=False)
            result_json = json.dumps(result, ensure_ascii=False)
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('''
                        INSERT INTO career_assessments (
                            assessment_id, student_id, assessment_type,
                            answers, result, result_summary, score, taken_at, created_at
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                    ''', (assessment_id, student_id, assessment_type,
                          answers_json, result_json,
                          result.get('summary', ''),
                          result.get('score', 0),
                          now, now))
                    conn.commit()
                    return {
                        'success': True,
                        'assessment_id': assessment_id,
                        'result': result
                    }
        except Exception as e:
            logger.error(f'职业测评失败: {e}')
            return {'success': False, 'error': str(e)}

    def _calculate_assessment_result(self, assessment_type: str, answers: List[Any]) -> Dict[str, Any]:
        if assessment_type == 'holland':
            types = {'R': 0, 'I': 0, 'A': 0, 'S': 0, 'E': 0, 'C': 0}
            for i, ans in enumerate(answers):
                key = list(types.keys())[i % 6]
                types[key] += int(ans) if ans else 0
            sorted_types = sorted(types.items(), key=lambda x: x[1], reverse=True)
            top3 = ''.join([t[0] for t in sorted_types[:3]])
            return {
                'type': 'holland',
                'scores': types,
                'top_code': top3,
                'summary': f'霍兰德代码: {top3}',
                'score': sum(types.values())
            }
        elif assessment_type == 'mbti':
            dimensions = {'E': 0, 'I': 0, 'S': 0, 'N': 0, 'T': 0, 'F': 0, 'J': 0, 'P': 0}
            for i, ans in enumerate(answers):
                keys = list(dimensions.keys())
                key = keys[i % len(keys)]
                dimensions[key] += int(ans) if ans else 0
            mbti_type = ''
            pairs = [('E', 'I'), ('S', 'N'), ('T', 'F'), ('J', 'P')]
            for a, b in pairs:
                mbti_type += a if dimensions[a] >= dimensions[b] else b
            return {
                'type': 'mbti',
                'scores': dimensions,
                'mbti_type': mbti_type,
                'summary': f'MBTI类型: {mbti_type}',
                'score': sum(dimensions.values())
            }
        else:
            total = sum(int(a) if a else 0 for a in answers)
            return {
                'type': assessment_type,
                'total_score': total,
                'summary': f'{CAREER_ASSESSMENT_TYPES.get(assessment_type, {}).get("name", "")}总分: {total}',
                'score': total
            }

    # ========== 就业指导 ==========

    def create_career_guidance(self, student_id: int, guidance_type: str,
                                topic: str, **kwargs) -> Dict[str, Any]:
        try:
            guidance_id = f"cgs_{uuid.uuid4().hex[:12]}"
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('''
                        INSERT INTO career_guidance (
                            guidance_id, student_id, guidance_type, topic,
                            content, advisor_id, advisor_name, session_date,
                            duration_minutes, created_at
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    ''', (guidance_id, student_id, guidance_type, topic,
                          kwargs.get('content'), kwargs.get('advisor_id'),
                          kwargs.get('advisor_name'),
                          kwargs.get('session_date', now[:10]),
                          kwargs.get('duration_minutes', 30), now))
                    conn.commit()
                    return {'success': True, 'guidance_id': guidance_id}
        except Exception as e:
            logger.error(f'创建就业指导失败: {e}')
            return {'success': False, 'error': str(e)}

    def get_student_guidance(self, student_id: int) -> Dict[str, Any]:
        try:
            with self._get_connection() as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                cursor.execute('SELECT * FROM career_guidance WHERE student_id = ? ORDER BY session_date DESC', (student_id,))
                records = [dict(r) for r in cursor.fetchall()]
                return {'success': True, 'guidance_records': records}
        except Exception as e:
            logger.error(f'获取就业指导记录失败: {e}')
            return {'success': False, 'error': str(e)}

    # ========== 就业记录 ==========

    def record_employment(self, student_id: int, **kwargs) -> Dict[str, Any]:
        try:
            record_id = f"emp_{uuid.uuid4().hex[:12]}"
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('''
                        INSERT INTO employment_records (
                            record_id, student_id, student_name, education_type,
                            graduation_year, company_name, position_title, industry,
                            city, salary, employment_status, employ_date,
                            is_related, source, created_at, updated_at
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    ''', (record_id, student_id, kwargs.get('student_name'),
                          kwargs.get('education_type'), kwargs.get('graduation_year'),
                          kwargs.get('company_name'), kwargs.get('position_title'),
                          kwargs.get('industry'), kwargs.get('city'),
                          kwargs.get('salary'), kwargs.get('employment_status', 'employed'),
                          kwargs.get('employ_date', now[:10]),
                          kwargs.get('is_related', 1), kwargs.get('source'),
                          now, now))
                    conn.commit()
                    logger.info(f'记录就业: {record_id}')
                    return {'success': True, 'record_id': record_id}
        except Exception as e:
            logger.error(f'记录就业失败: {e}')
            return {'success': False, 'error': str(e)}

    # ========== 就业统计 ==========

    def get_employment_statistics(self, graduation_year: str = None,
                                    education_type: str = None) -> Dict[str, Any]:
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                query = 'SELECT COUNT(*) FROM employment_records WHERE 1=1'
                params = []
                if graduation_year:
                    query += ' AND graduation_year = ?'
                    params.append(graduation_year)
                if education_type:
                    query += ' AND education_type = ?'
                    params.append(education_type)
                cursor.execute(query, params)
                total = cursor.fetchone()[0]
                cursor.execute(f'SELECT employment_status, COUNT(*) FROM ({query}) GROUP BY employment_status', params)
                by_status = {r[0]: r[1] for r in cursor.fetchall()}
                cursor.execute(f'SELECT industry, COUNT(*) FROM ({query}) GROUP BY industry ORDER BY COUNT(*) DESC', params)
                by_industry = {r[0]: r[1] for r in cursor.fetchall()}
                cursor.execute(f'SELECT AVG(salary), MAX(salary), MIN(salary) FROM ({query}) WHERE salary > 0', params)
                salary_row = cursor.fetchone()
                employed = by_status.get('employed', 0) + by_status.get('further_study', 0) + by_status.get('entrepreneur', 0)
                employment_rate = round(employed / total * 100, 2) if total > 0 else 0
                return {
                    'success': True,
                    'stats': {
                        'total_graduates': total,
                        'employment_rate': employment_rate,
                        'by_status': by_status,
                        'by_industry': by_industry,
                        'avg_salary': round(salary_row[0], 2) if salary_row[0] else 0,
                        'max_salary': salary_row[1] or 0,
                        'min_salary': salary_row[2] or 0
                    }
                }
        except Exception as e:
            logger.error(f'获取就业统计失败: {e}')
            return {'success': False, 'error': str(e)}

    # ========== 校园招聘 ==========

    def create_campus_recruitment(self, company_id: str, company_name: str,
                                    event_name: str, event_date: str,
                                    **kwargs) -> Dict[str, Any]:
        try:
            recruit_id = f"rec_{uuid.uuid4().hex[:12]}"
            now = datetime.now().isoformat()
            positions = json.dumps(kwargs.get('positions'), ensure_ascii=False) if kwargs.get('positions') else None
            target_majors = json.dumps(kwargs.get('target_majors'), ensure_ascii=False) if kwargs.get('target_majors') else None
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('''
                        INSERT INTO campus_recruitment (
                            recruit_id, company_id, company_name, event_name,
                            event_date, location, description, positions,
                            target_majors, registration_count, status, created_at, updated_at
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, 0, 'scheduled', ?, ?)
                    ''', (recruit_id, company_id, company_name, event_name,
                          event_date, kwargs.get('location'),
                          kwargs.get('description'), positions,
                          target_majors, now, now))
                    conn.commit()
                    logger.info(f'创建校园招聘: {event_name} ({recruit_id})')
                    return {'success': True, 'recruit_id': recruit_id}
        except Exception as e:
            logger.error(f'创建校园招聘失败: {e}')
            return {'success': False, 'error': str(e)}

    def list_campus_recruitments(self, status: str = 'scheduled',
                                   page: int = 1, page_size: int = 20) -> Dict[str, Any]:
        try:
            with self._get_connection() as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                query = 'SELECT * FROM campus_recruitment WHERE 1=1'
                params = []
                if status:
                    query += ' AND status = ?'
                    params.append(status)
                cursor.execute(f'SELECT COUNT(*) as cnt FROM ({query})', params)
                total = cursor.fetchone()['cnt']
                query += ' ORDER BY event_date DESC LIMIT ? OFFSET ?'
                params.extend([page_size, (page - 1) * page_size])
                cursor.execute(query, params)
                recruitments = [dict(r) for r in cursor.fetchall()]
                return {'success': True, 'recruitments': recruitments, 'total': total, 'page': page, 'page_size': page_size}
        except Exception as e:
            logger.error(f'获取校园招聘列表失败: {e}')
            return {'success': False, 'error': str(e)}
