#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
MTSCOS 教育出版服务 (v15.27.0)
=============================
提供教材出版、数字出版、版权管理、发行管理、营销管理、数据分析、合作管理和质量控制等综合服务。

核心能力：
1. 教材出版管理 - 教材策划、编辑、排版、印刷
2. 数字出版管理 - 电子书、有声书、互动书、在线课程
3. 版权管理 - 著作权、邻接权、许可权、维权
4. 出版发行管理 - 渠道管理、库存管理、发货管理
5. 出版营销管理 - 线上线下营销、社交媒体营销
6. 出版数据分析 - 销量分析、读者分析、市场分析
7. 出版合作管理 - 作者合作、出版社合作、国际合作
8. 出版质量控制 - 内容审核、编辑校对、印刷质检

支持成人教育与K12教育差异化管理。
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
            os.path.join(os.path.dirname(os.path.abspath(__file__)), 'education_publishing_service.log'),
            encoding='utf-8'
        ),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger('EducationPublishing')


# ========== 出版配置 ==========

TEXTBOOK_TYPES = {
    'textbook': {'name': '教科书', 'education_type': ['k12', 'adult']},
    'workbook': {'name': '教辅书', 'education_type': ['k12', 'adult']},
    'exercise': {'name': '练习册', 'education_type': ['k12']},
    'reference': {'name': '参考书', 'education_type': ['k12', 'adult']},
    'reference_book': {'name': '工具书', 'education_type': ['k12', 'adult']},
    'picture_book': {'name': '绘本', 'education_type': ['k12']},
    'supplementary': {'name': '教材配套', 'education_type': ['k12', 'adult']},
    'digital_textbook': {'name': '电子教材', 'education_type': ['k12', 'adult']}
}

DIGITAL_PUBLISHING = {
    'ebook': {'name': '电子书', 'formats': ['epub', 'pdf', 'mobi'], 'education_type': ['k12', 'adult']},
    'audiobook': {'name': '有声书', 'formats': ['mp3', 'wav'], 'education_type': ['k12', 'adult']},
    'interactive': {'name': '互动书', 'formats': ['html5', 'app'], 'education_type': ['k12']},
    'multimedia': {'name': '多媒体书', 'formats': ['pdf', 'video'], 'education_type': ['k12', 'adult']},
    'online_course': {'name': '在线课程', 'formats': ['video', 'scorm'], 'education_type': ['k12', 'adult']},
    'digital_magazine': {'name': '数字杂志', 'formats': ['pdf', 'html5'], 'education_type': ['adult']},
    'digital_newspaper': {'name': '数字报纸', 'formats': ['pdf', 'html5'], 'education_type': ['adult']},
    'digital_journal': {'name': '数字期刊', 'formats': ['pdf', 'html5'], 'education_type': ['adult']}
}

COPYRIGHT_TYPES = {
    'copyright': {'name': '著作权', 'protection_period': '作者终身+50年'},
    'neighboring': {'name': '邻接权', 'protection_period': '50年'},
    'trademark': {'name': '商标权', 'protection_period': '10年可续展'},
    'patent': {'name': '专利权', 'protection_period': '20年'},
    'usage': {'name': '使用权', 'protection_period': '合同约定'},
    'license': {'name': '许可权', 'protection_period': '合同约定'},
    'transfer': {'name': '转让权', 'protection_period': '合同约定'},
    'enforcement': {'name': '维权', 'protection_period': '有效期内'}
}

DISTRIBUTION_CHANNELS = {
    'bookstore': {'name': '书店', 'channel_type': 'offline', 'education_type': ['k12', 'adult']},
    'ecommerce': {'name': '电商平台', 'channel_type': 'online', 'education_type': ['k12', 'adult']},
    'direct_sale': {'name': '出版社直销', 'channel_type': 'direct', 'education_type': ['k12', 'adult']},
    'school_purchase': {'name': '学校采购', 'channel_type': 'b2b', 'education_type': ['k12']},
    'government_purchase': {'name': '政府采购', 'channel_type': 'b2b', 'education_type': ['k12', 'adult']},
    'international': {'name': '国际发行', 'channel_type': 'export', 'education_type': ['adult']},
    'library': {'name': '馆配', 'channel_type': 'b2b', 'education_type': ['k12', 'adult']},
    'group_buy': {'name': '团购', 'channel_type': 'b2b', 'education_type': ['k12', 'adult']}
}

MARKETING_METHODS = {
    'online': {'name': '线上营销', 'channels': ['官网', '电商平台', '直播']},
    'offline': {'name': '线下营销', 'channels': ['书店活动', '校园推广', '展会']},
    'social_media': {'name': '社交媒体营销', 'channels': ['微信', '微博', '抖音']},
    'content': {'name': '内容营销', 'channels': ['公众号', '短视频', '直播']},
    'event': {'name': '事件营销', 'channels': ['新书发布会', '作者见面会']},
    'cooperation': {'name': '合作营销', 'channels': ['跨界合作', '联合推广']},
    'word_of_mouth': {'name': '口碑营销', 'channels': ['用户评价', '推荐奖励']},
    'precision': {'name': '精准营销', 'channels': ['定向投放', '个性化推荐']}
}

ANALYSIS_DIMENSIONS = {
    'sales': {'name': '销量分析', 'metrics': ['销量', '销售额', '增长率']},
    'reader': {'name': '读者分析', 'metrics': ['年龄分布', '地域分布', '阅读偏好']},
    'market': {'name': '市场分析', 'metrics': ['市场份额', '需求趋势', '定价策略']},
    'competition': {'name': '竞争分析', 'metrics': ['竞品对比', '差异化优势']},
    'pricing': {'name': '定价分析', 'metrics': ['价格敏感度', '最优价格']},
    'channel': {'name': '渠道分析', 'metrics': ['渠道贡献', '库存周转']},
    'trend': {'name': '趋势分析', 'metrics': ['增长趋势', '季节性']},
    'benefit': {'name': '效益分析', 'metrics': ['利润率', 'ROI', '成本分析']}
}

COOPERATION_TYPES = {
    'author': {'name': '作者合作', 'model': ['签约', '买断', '分成']},
    'publisher': {'name': '出版社合作', 'model': ['联合出版', '版权贸易']},
    'distributor': {'name': '经销商合作', 'model': ['代理', '批发']},
    'education': {'name': '教育机构合作', 'model': ['定制开发', '联合推广']},
    'government': {'name': '政府合作', 'model': ['项目申报', '政府采购']},
    'international': {'name': '国际合作', 'model': ['版权输出', '合作出版']},
    'technology': {'name': '技术合作', 'model': ['平台合作', '技术开发']},
    'investment': {'name': '投资合作', 'model': ['股权投资', '项目投资']}
}

QUALITY_CONTROL = {
    'content_review': {'name': '内容审核', 'standards': ['政治正确', '学术规范', '适宜性']},
    'editing': {'name': '编辑校对', 'standards': ['文字规范', '格式统一', '错误率']},
    'layout': {'name': '排版设计', 'standards': ['视觉美观', '阅读体验', '版式规范']},
    'printing': {'name': '印刷质量', 'standards': ['纸张质量', '印刷精度', '装订质量']},
    'digital_quality': {'name': '数字质检', 'standards': ['格式规范', '兼容性', '加载速度']},
    'copyright_review': {'name': '版权审核', 'standards': ['授权完整', '侵权风险']},
    'compliance': {'name': '合规审查', 'standards': ['出版许可', 'ISBN规范']},
    'feedback': {'name': '用户反馈', 'standards': ['满意度', '问题响应']}
}


class EducationPublishingService:
    """教育出版服务"""

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
                    CREATE TABLE IF NOT EXISTS textbook_publishing (
                        textbook_id TEXT PRIMARY KEY,
                        textbook_name TEXT NOT NULL,
                        textbook_type TEXT NOT NULL,
                        education_type TEXT NOT NULL,
                        grade_level TEXT,
                        subject TEXT,
                        author TEXT,
                        editor TEXT,
                        publisher TEXT,
                        isbn TEXT,
                        pages INTEGER,
                        format TEXT,
                        price REAL,
                        cost REAL,
                        status TEXT DEFAULT 'planning',
                        publish_date TEXT,
                        description TEXT,
                        cover_image TEXT,
                        created_at TEXT,
                        updated_at TEXT
                    )
                ''')
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS publishing_records (
                        record_id INTEGER PRIMARY KEY AUTOINCREMENT,
                        textbook_id TEXT NOT NULL,
                        stage TEXT NOT NULL,
                        stage_name TEXT,
                        responsible_person TEXT,
                        start_date TEXT,
                        end_date TEXT,
                        status TEXT DEFAULT 'in_progress',
                        notes TEXT,
                        created_at TEXT
                    )
                ''')
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS digital_publishing (
                        digital_id TEXT PRIMARY KEY,
                        digital_name TEXT NOT NULL,
                        digital_type TEXT NOT NULL,
                        education_type TEXT NOT NULL,
                        textbook_id TEXT,
                        author TEXT,
                        editor TEXT,
                        publisher TEXT,
                        isbn TEXT,
                        file_format TEXT,
                        file_size REAL,
                        price REAL,
                        cost REAL,
                        status TEXT DEFAULT 'processing',
                        publish_date TEXT,
                        download_url TEXT,
                        preview_url TEXT,
                        description TEXT,
                        cover_image TEXT,
                        created_at TEXT,
                        updated_at TEXT
                    )
                ''')
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS digital_records (
                        record_id INTEGER PRIMARY KEY AUTOINCREMENT,
                        digital_id TEXT NOT NULL,
                        stage TEXT NOT NULL,
                        stage_name TEXT,
                        responsible_person TEXT,
                        start_date TEXT,
                        end_date TEXT,
                        status TEXT DEFAULT 'in_progress',
                        notes TEXT,
                        created_at TEXT
                    )
                ''')
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS copyright_management (
                        copyright_id TEXT PRIMARY KEY,
                        textbook_id TEXT,
                        digital_id TEXT,
                        copyright_type TEXT NOT NULL,
                        owner TEXT,
                        author TEXT,
                        registration_no TEXT,
                        registration_date TEXT,
                        protection_start TEXT,
                        protection_end TEXT,
                        status TEXT DEFAULT 'active',
                        description TEXT,
                        created_at TEXT,
                        updated_at TEXT
                    )
                ''')
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS copyright_records (
                        record_id INTEGER PRIMARY KEY AUTOINCREMENT,
                        copyright_id TEXT NOT NULL,
                        action TEXT NOT NULL,
                        action_name TEXT,
                        party TEXT,
                        amount REAL,
                        effective_date TEXT,
                        expiration_date TEXT,
                        contract_no TEXT,
                        status TEXT DEFAULT 'pending',
                        notes TEXT,
                        created_at TEXT
                    )
                ''')
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS publishing_distribution (
                        distribution_id TEXT PRIMARY KEY,
                        textbook_id TEXT,
                        digital_id TEXT,
                        channel TEXT NOT NULL,
                        channel_name TEXT,
                        education_type TEXT NOT NULL,
                        price REAL,
                        quantity INTEGER DEFAULT 0,
                        stock INTEGER DEFAULT 0,
                        sold INTEGER DEFAULT 0,
                        status TEXT DEFAULT 'active',
                        start_date TEXT,
                        end_date TEXT,
                        created_at TEXT,
                        updated_at TEXT
                    )
                ''')
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS distribution_records (
                        record_id INTEGER PRIMARY KEY AUTOINCREMENT,
                        distribution_id TEXT NOT NULL,
                        action TEXT NOT NULL,
                        action_name TEXT,
                        quantity INTEGER,
                        unit_price REAL,
                        total_amount REAL,
                        customer TEXT,
                        address TEXT,
                        tracking_no TEXT,
                        status TEXT DEFAULT 'pending',
                        notes TEXT,
                        created_at TEXT
                    )
                ''')
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS publishing_marketing (
                        marketing_id TEXT PRIMARY KEY,
                        textbook_id TEXT,
                        digital_id TEXT,
                        marketing_method TEXT NOT NULL,
                        method_name TEXT,
                        education_type TEXT NOT NULL,
                        budget REAL DEFAULT 0,
                        spent REAL DEFAULT 0,
                        target_audience TEXT,
                        campaign_name TEXT,
                        status TEXT DEFAULT 'planning',
                        start_date TEXT,
                        end_date TEXT,
                        description TEXT,
                        created_at TEXT,
                        updated_at TEXT
                    )
                ''')
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS marketing_records (
                        record_id INTEGER PRIMARY KEY AUTOINCREMENT,
                        marketing_id TEXT NOT NULL,
                        action TEXT NOT NULL,
                        action_name TEXT,
                        channel TEXT,
                        cost REAL,
                        impressions INTEGER DEFAULT 0,
                        clicks INTEGER DEFAULT 0,
                        conversions INTEGER DEFAULT 0,
                        notes TEXT,
                        created_at TEXT
                    )
                ''')
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS publishing_analysis (
                        analysis_id TEXT PRIMARY KEY,
                        textbook_id TEXT,
                        digital_id TEXT,
                        education_type TEXT NOT NULL,
                        analysis_type TEXT NOT NULL,
                        analysis_name TEXT,
                        period TEXT,
                        data_source TEXT,
                        status TEXT DEFAULT 'processing',
                        created_at TEXT,
                        updated_at TEXT
                    )
                ''')
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS analysis_data (
                        data_id INTEGER PRIMARY KEY AUTOINCREMENT,
                        analysis_id TEXT NOT NULL,
                        dimension TEXT,
                        metric TEXT,
                        value REAL,
                        value_text TEXT,
                        period TEXT,
                        created_at TEXT
                    )
                ''')
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS publishing_cooperation (
                        cooperation_id TEXT PRIMARY KEY,
                        cooperation_type TEXT NOT NULL,
                        type_name TEXT,
                        education_type TEXT NOT NULL,
                        partner_name TEXT,
                        partner_contact TEXT,
                        cooperation_model TEXT,
                        amount REAL,
                        status TEXT DEFAULT 'negotiating',
                        start_date TEXT,
                        end_date TEXT,
                        description TEXT,
                        contract_no TEXT,
                        created_at TEXT,
                        updated_at TEXT
                    )
                ''')
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS cooperation_records (
                        record_id INTEGER PRIMARY KEY AUTOINCREMENT,
                        cooperation_id TEXT NOT NULL,
                        action TEXT NOT NULL,
                        action_name TEXT,
                        responsible_person TEXT,
                        date TEXT,
                        outcome TEXT,
                        notes TEXT,
                        created_at TEXT
                    )
                ''')
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS publishing_quality (
                        quality_id TEXT PRIMARY KEY,
                        textbook_id TEXT,
                        digital_id TEXT,
                        education_type TEXT NOT NULL,
                        control_type TEXT NOT NULL,
                        control_name TEXT,
                        inspector TEXT,
                        status TEXT DEFAULT 'pending',
                        score REAL,
                        pass_threshold REAL DEFAULT 80,
                        is_pass INTEGER DEFAULT 0,
                        notes TEXT,
                        created_at TEXT,
                        updated_at TEXT
                    )
                ''')
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS quality_records (
                        record_id INTEGER PRIMARY KEY AUTOINCREMENT,
                        quality_id TEXT NOT NULL,
                        check_item TEXT,
                        check_result TEXT,
                        is_pass INTEGER,
                        notes TEXT,
                        created_at TEXT
                    )
                ''')
                conn.commit()
                logger.info('教育出版服务数据库初始化完成')
        except Exception as e:
            logger.error(f'数据库初始化失败: {e}')

    # ========== 教材出版管理 ==========

    def create_textbook(self, textbook_name: str, textbook_type: str,
                        education_type: str, **kwargs) -> Dict[str, Any]:
        try:
            textbook_id = f"tbk_{uuid.uuid4().hex[:12]}"
            now = datetime.now().isoformat()
            config = TEXTBOOK_TYPES.get(textbook_type, {})
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('''
                        INSERT INTO textbook_publishing (
                            textbook_id, textbook_name, textbook_type,
                            education_type, grade_level, subject,
                            author, editor, publisher, isbn,
                            pages, format, price, cost,
                            status, publish_date, description,
                            cover_image, created_at, updated_at
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'planning', ?, ?, ?, ?, ?)
                    ''', (textbook_id, textbook_name, textbook_type, education_type,
                          kwargs.get('grade_level'), kwargs.get('subject'),
                          kwargs.get('author'), kwargs.get('editor'),
                          kwargs.get('publisher'), kwargs.get('isbn'),
                          kwargs.get('pages'), kwargs.get('format'),
                          kwargs.get('price', 0), kwargs.get('cost', 0),
                          kwargs.get('publish_date'), kwargs.get('description'),
                          kwargs.get('cover_image'), now, now))
                    conn.commit()
                    logger.info(f'创建教材: {textbook_name} ({textbook_id})')
                    return {'success': True, 'textbook_id': textbook_id}
        except Exception as e:
            logger.error(f'创建教材失败: {e}')
            return {'success': False, 'error': str(e)}

    def update_textbook_stage(self, textbook_id: str, stage: str,
                              **kwargs) -> Dict[str, Any]:
        try:
            now = datetime.now().isoformat()
            stages = {'planning': '策划', 'writing': '编写', 'editing': '编辑',
                      'layout': '排版', 'printing': '印刷', 'published': '已出版'}
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('''
                        INSERT INTO publishing_records (
                            textbook_id, stage, stage_name,
                            responsible_person, start_date, end_date,
                            status, notes, created_at
                        ) VALUES (?, ?, ?, ?, ?, ?, 'in_progress', ?, ?)
                    ''', (textbook_id, stage, stages.get(stage, stage),
                          kwargs.get('responsible_person'), now[:10],
                          kwargs.get('end_date'), kwargs.get('notes'), now))
                    cursor.execute('UPDATE textbook_publishing SET status = ?, updated_at = ? WHERE textbook_id = ?',
                                 (stage, now, textbook_id))
                    conn.commit()
                    return {'success': True, 'stage': stage}
        except Exception as e:
            logger.error(f'更新教材阶段失败: {e}')
            return {'success': False, 'error': str(e)}

    def publish_textbook(self, textbook_id: str, **kwargs) -> Dict[str, Any]:
        try:
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('UPDATE textbook_publishing SET status = ?, publish_date = ?, updated_at = ? WHERE textbook_id = ?',
                                 ('published', now[:10], now, textbook_id))
                    if cursor.rowcount > 0:
                        conn.commit()
                        logger.info(f'教材出版完成: {textbook_id}')
                        return {'success': True, 'publish_date': now[:10]}
                    return {'success': False, 'error': '教材不存在'}
        except Exception as e:
            logger.error(f'教材出版失败: {e}')
            return {'success': False, 'error': str(e)}

    def list_textbooks(self, education_type: str = None, textbook_type: str = None,
                       status: str = None, page: int = 1, page_size: int = 20) -> Dict[str, Any]:
        try:
            with self._get_connection() as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                query = 'SELECT * FROM textbook_publishing WHERE 1=1'
                params = []
                if education_type:
                    query += ' AND education_type = ?'
                    params.append(education_type)
                if textbook_type:
                    query += ' AND textbook_type = ?'
                    params.append(textbook_type)
                if status:
                    query += ' AND status = ?'
                    params.append(status)
                cursor.execute(f'SELECT COUNT(*) as cnt FROM ({query})', params)
                total = cursor.fetchone()['cnt']
                query += ' ORDER BY created_at DESC LIMIT ? OFFSET ?'
                params.extend([page_size, (page - 1) * page_size])
                cursor.execute(query, params)
                textbooks = [dict(t) for t in cursor.fetchall()]
                return {'success': True, 'textbooks': textbooks, 'total': total, 'page': page, 'page_size': page_size}
        except Exception as e:
            logger.error(f'获取教材列表失败: {e}')
            return {'success': False, 'error': str(e)}

    # ========== 数字出版管理 ==========

    def create_digital_publishing(self, digital_name: str, digital_type: str,
                                  education_type: str, **kwargs) -> Dict[str, Any]:
        try:
            digital_id = f"dgt_{uuid.uuid4().hex[:12]}"
            now = datetime.now().isoformat()
            config = DIGITAL_PUBLISHING.get(digital_type, {})
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('''
                        INSERT INTO digital_publishing (
                            digital_id, digital_name, digital_type,
                            education_type, textbook_id, author,
                            editor, publisher, isbn, file_format,
                            file_size, price, cost, status,
                            publish_date, download_url, preview_url,
                            description, cover_image, created_at, updated_at
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'processing', ?, ?, ?, ?, ?, ?, ?)
                    ''', (digital_id, digital_name, digital_type, education_type,
                          kwargs.get('textbook_id'), kwargs.get('author'),
                          kwargs.get('editor'), kwargs.get('publisher'),
                          kwargs.get('isbn'), kwargs.get('file_format'),
                          kwargs.get('file_size', 0), kwargs.get('price', 0),
                          kwargs.get('cost', 0), kwargs.get('publish_date'),
                          kwargs.get('download_url'), kwargs.get('preview_url'),
                          kwargs.get('description'), kwargs.get('cover_image'),
                          now, now))
                    conn.commit()
                    logger.info(f'创建数字出版: {digital_name} ({digital_id})')
                    return {'success': True, 'digital_id': digital_id}
        except Exception as e:
            logger.error(f'创建数字出版失败: {e}')
            return {'success': False, 'error': str(e)}

    def update_digital_stage(self, digital_id: str, stage: str,
                             **kwargs) -> Dict[str, Any]:
        try:
            now = datetime.now().isoformat()
            stages = {'processing': '制作中', 'review': '审核中', 'testing': '测试中',
                      'ready': '待发布', 'published': '已发布'}
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('''
                        INSERT INTO digital_records (
                            digital_id, stage, stage_name,
                            responsible_person, start_date, end_date,
                            status, notes, created_at
                        ) VALUES (?, ?, ?, ?, ?, ?, 'in_progress', ?, ?)
                    ''', (digital_id, stage, stages.get(stage, stage),
                          kwargs.get('responsible_person'), now[:10],
                          kwargs.get('end_date'), kwargs.get('notes'), now))
                    cursor.execute('UPDATE digital_publishing SET status = ?, updated_at = ? WHERE digital_id = ?',
                                 (stage, now, digital_id))
                    conn.commit()
                    return {'success': True, 'stage': stage}
        except Exception as e:
            logger.error(f'更新数字出版阶段失败: {e}')
            return {'success': False, 'error': str(e)}

    def publish_digital(self, digital_id: str, **kwargs) -> Dict[str, Any]:
        try:
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('UPDATE digital_publishing SET status = ?, publish_date = ?, updated_at = ? WHERE digital_id = ?',
                                 ('published', now[:10], now, digital_id))
                    if cursor.rowcount > 0:
                        conn.commit()
                        logger.info(f'数字出版发布完成: {digital_id}')
                        return {'success': True, 'publish_date': now[:10]}
                    return {'success': False, 'error': '数字出版不存在'}
        except Exception as e:
            logger.error(f'数字出版发布失败: {e}')
            return {'success': False, 'error': str(e)}

    def list_digital_publishing(self, education_type: str = None, digital_type: str = None,
                                status: str = None, page: int = 1, page_size: int = 20) -> Dict[str, Any]:
        try:
            with self._get_connection() as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                query = 'SELECT * FROM digital_publishing WHERE 1=1'
                params = []
                if education_type:
                    query += ' AND education_type = ?'
                    params.append(education_type)
                if digital_type:
                    query += ' AND digital_type = ?'
                    params.append(digital_type)
                if status:
                    query += ' AND status = ?'
                    params.append(status)
                cursor.execute(f'SELECT COUNT(*) as cnt FROM ({query})', params)
                total = cursor.fetchone()['cnt']
                query += ' ORDER BY created_at DESC LIMIT ? OFFSET ?'
                params.extend([page_size, (page - 1) * page_size])
                cursor.execute(query, params)
                digitals = [dict(d) for d in cursor.fetchall()]
                return {'success': True, 'digitals': digitals, 'total': total, 'page': page, 'page_size': page_size}
        except Exception as e:
            logger.error(f'获取数字出版列表失败: {e}')
            return {'success': False, 'error': str(e)}

    # ========== 版权管理 ==========

    def register_copyright(self, copyright_type: str, **kwargs) -> Dict[str, Any]:
        try:
            copyright_id = f"cpy_{uuid.uuid4().hex[:12]}"
            now = datetime.now().isoformat()
            config = COPYRIGHT_TYPES.get(copyright_type, {})
            protection_end = None
            if config.get('protection_period'):
                if '终身' in config['protection_period']:
                    protection_end = (datetime.now() + timedelta(days=50*365)).isoformat()[:10]
                elif '50年' in config['protection_period']:
                    protection_end = (datetime.now() + timedelta(days=50*365)).isoformat()[:10]
                elif '20年' in config['protection_period']:
                    protection_end = (datetime.now() + timedelta(days=20*365)).isoformat()[:10]
                elif '10年' in config['protection_period']:
                    protection_end = (datetime.now() + timedelta(days=10*365)).isoformat()[:10]
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('''
                        INSERT INTO copyright_management (
                            copyright_id, textbook_id, digital_id,
                            copyright_type, owner, author,
                            registration_no, registration_date,
                            protection_start, protection_end,
                            status, description, created_at, updated_at
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'active', ?, ?, ?)
                    ''', (copyright_id, kwargs.get('textbook_id'), kwargs.get('digital_id'),
                          copyright_type, kwargs.get('owner'), kwargs.get('author'),
                          kwargs.get('registration_no'), now[:10], now[:10],
                          protection_end, kwargs.get('description'), now, now))
                    conn.commit()
                    logger.info(f'注册版权: {copyright_type} ({copyright_id})')
                    return {'success': True, 'copyright_id': copyright_id}
        except Exception as e:
            logger.error(f'注册版权失败: {e}')
            return {'success': False, 'error': str(e)}

    def license_copyright(self, copyright_id: str, **kwargs) -> Dict[str, Any]:
        try:
            now = datetime.now().isoformat()
            actions = {'license': '许可授权', 'transfer': '转让', 'enforce': '维权', 'renew': '续期'}
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('''
                        INSERT INTO copyright_records (
                            copyright_id, action, action_name,
                            party, amount, effective_date,
                            expiration_date, contract_no,
                            status, notes, created_at
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, 'pending', ?, ?)
                    ''', (copyright_id, 'license', actions['license'],
                          kwargs.get('party'), kwargs.get('amount', 0),
                          now[:10], kwargs.get('expiration_date'),
                          kwargs.get('contract_no'), kwargs.get('notes'), now))
                    conn.commit()
                    return {'success': True, 'action': 'license'}
        except Exception as e:
            logger.error(f'版权许可失败: {e}')
            return {'success': False, 'error': str(e)}

    def transfer_copyright(self, copyright_id: str, **kwargs) -> Dict[str, Any]:
        try:
            now = datetime.now().isoformat()
            actions = {'license': '许可授权', 'transfer': '转让', 'enforce': '维权', 'renew': '续期'}
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('''
                        INSERT INTO copyright_records (
                            copyright_id, action, action_name,
                            party, amount, effective_date,
                            expiration_date, contract_no,
                            status, notes, created_at
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, 'pending', ?, ?)
                    ''', (copyright_id, 'transfer', actions['transfer'],
                          kwargs.get('party'), kwargs.get('amount', 0),
                          now[:10], kwargs.get('expiration_date'),
                          kwargs.get('contract_no'), kwargs.get('notes'), now))
                    cursor.execute('UPDATE copyright_management SET owner = ?, updated_at = ? WHERE copyright_id = ?',
                                 (kwargs.get('party'), now, copyright_id))
                    conn.commit()
                    return {'success': True, 'action': 'transfer'}
        except Exception as e:
            logger.error(f'版权转让失败: {e}')
            return {'success': False, 'error': str(e)}

    def list_copyrights(self, copyright_type: str = None, status: str = None,
                        page: int = 1, page_size: int = 20) -> Dict[str, Any]:
        try:
            with self._get_connection() as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                query = 'SELECT * FROM copyright_management WHERE 1=1'
                params = []
                if copyright_type:
                    query += ' AND copyright_type = ?'
                    params.append(copyright_type)
                if status:
                    query += ' AND status = ?'
                    params.append(status)
                cursor.execute(f'SELECT COUNT(*) as cnt FROM ({query})', params)
                total = cursor.fetchone()['cnt']
                query += ' ORDER BY created_at DESC LIMIT ? OFFSET ?'
                params.extend([page_size, (page - 1) * page_size])
                cursor.execute(query, params)
                copyrights = [dict(c) for c in cursor.fetchall()]
                return {'success': True, 'copyrights': copyrights, 'total': total, 'page': page, 'page_size': page_size}
        except Exception as e:
            logger.error(f'获取版权列表失败: {e}')
            return {'success': False, 'error': str(e)}

    # ========== 出版发行管理 ==========

    def create_distribution(self, channel: str, education_type: str,
                            **kwargs) -> Dict[str, Any]:
        try:
            distribution_id = f"dis_{uuid.uuid4().hex[:12]}"
            now = datetime.now().isoformat()
            config = DISTRIBUTION_CHANNELS.get(channel, {})
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('''
                        INSERT INTO publishing_distribution (
                            distribution_id, textbook_id, digital_id,
                            channel, channel_name, education_type,
                            price, quantity, stock, sold,
                            status, start_date, end_date,
                            created_at, updated_at
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, 0, 'active', ?, ?, ?, ?)
                    ''', (distribution_id, kwargs.get('textbook_id'), kwargs.get('digital_id'),
                          channel, config.get('name', channel), education_type,
                          kwargs.get('price', 0), kwargs.get('quantity', 0),
                          kwargs.get('stock', 0), now[:10], kwargs.get('end_date'),
                          now, now))
                    conn.commit()
                    logger.info(f'创建发行渠道: {channel} ({distribution_id})')
                    return {'success': True, 'distribution_id': distribution_id}
        except Exception as e:
            logger.error(f'创建发行渠道失败: {e}')
            return {'success': False, 'error': str(e)}

    def update_stock(self, distribution_id: str, quantity: int,
                     operation: str = 'add') -> Dict[str, Any]:
        try:
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    if operation == 'add':
                        cursor.execute('UPDATE publishing_distribution SET stock = stock + ?, updated_at = ? WHERE distribution_id = ?',
                                     (quantity, now, distribution_id))
                    elif operation == 'subtract':
                        cursor.execute('UPDATE publishing_distribution SET stock = MAX(0, stock - ?), updated_at = ? WHERE distribution_id = ?',
                                     (quantity, now, distribution_id))
                    elif operation == 'set':
                        cursor.execute('UPDATE publishing_distribution SET stock = ?, updated_at = ? WHERE distribution_id = ?',
                                     (quantity, now, distribution_id))
                    if cursor.rowcount > 0:
                        cursor.execute('''
                            INSERT INTO distribution_records (
                                distribution_id, action, action_name,
                                quantity, status, notes, created_at
                            ) VALUES (?, ?, ?, ?, 'completed', ?, ?)
                        ''', (distribution_id, operation, '库存调整', quantity, f'{operation} {quantity}', now))
                        conn.commit()
                        return {'success': True}
                    return {'success': False, 'error': '发行记录不存在'}
        except Exception as e:
            logger.error(f'更新库存失败: {e}')
            return {'success': False, 'error': str(e)}

    def record_sale(self, distribution_id: str, quantity: int,
                    **kwargs) -> Dict[str, Any]:
        try:
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('SELECT stock, price FROM publishing_distribution WHERE distribution_id = ?', (distribution_id,))
                    dist = cursor.fetchone()
                    if not dist:
                        return {'success': False, 'error': '发行记录不存在'}
                    if dist[0] < quantity:
                        return {'success': False, 'error': '库存不足'}
                    unit_price = kwargs.get('unit_price', dist[1])
                    total_amount = unit_price * quantity
                    cursor.execute('UPDATE publishing_distribution SET stock = stock - ?, sold = sold + ?, updated_at = ? WHERE distribution_id = ?',
                                 (quantity, quantity, now, distribution_id))
                    cursor.execute('''
                        INSERT INTO distribution_records (
                            distribution_id, action, action_name,
                            quantity, unit_price, total_amount,
                            customer, address, tracking_no,
                            status, notes, created_at
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, 'completed', ?, ?)
                    ''', (distribution_id, 'sale', '销售', quantity, unit_price,
                          total_amount, kwargs.get('customer'), kwargs.get('address'),
                          kwargs.get('tracking_no'), kwargs.get('notes'), now))
                    conn.commit()
                    return {'success': True, 'total_amount': total_amount}
        except Exception as e:
            logger.error(f'记录销售失败: {e}')
            return {'success': False, 'error': str(e)}

    def list_distributions(self, education_type: str = None, channel: str = None,
                           status: str = None, page: int = 1, page_size: int = 20) -> Dict[str, Any]:
        try:
            with self._get_connection() as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                query = 'SELECT * FROM publishing_distribution WHERE 1=1'
                params = []
                if education_type:
                    query += ' AND education_type = ?'
                    params.append(education_type)
                if channel:
                    query += ' AND channel = ?'
                    params.append(channel)
                if status:
                    query += ' AND status = ?'
                    params.append(status)
                cursor.execute(f'SELECT COUNT(*) as cnt FROM ({query})', params)
                total = cursor.fetchone()['cnt']
                query += ' ORDER BY created_at DESC LIMIT ? OFFSET ?'
                params.extend([page_size, (page - 1) * page_size])
                cursor.execute(query, params)
                distributions = [dict(d) for d in cursor.fetchall()]
                return {'success': True, 'distributions': distributions, 'total': total, 'page': page, 'page_size': page_size}
        except Exception as e:
            logger.error(f'获取发行列表失败: {e}')
            return {'success': False, 'error': str(e)}

    def get_stock_summary(self, education_type: str = None) -> Dict[str, Any]:
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                query = 'SELECT SUM(stock) as total_stock, SUM(sold) as total_sold, SUM(quantity) as total_quantity FROM publishing_distribution WHERE 1=1'
                params = []
                if education_type:
                    query += ' AND education_type = ?'
                    params.append(education_type)
                cursor.execute(query, params)
                result = cursor.fetchone()
                return {'success': True, 'total_stock': result[0] or 0, 'total_sold': result[1] or 0, 'total_quantity': result[2] or 0}
        except Exception as e:
            logger.error(f'获取库存汇总失败: {e}')
            return {'success': False, 'error': str(e)}

    # ========== 出版营销管理 ==========

    def create_marketing_campaign(self, marketing_method: str, education_type: str,
                                  **kwargs) -> Dict[str, Any]:
        try:
            marketing_id = f"mkt_{uuid.uuid4().hex[:12]}"
            now = datetime.now().isoformat()
            config = MARKETING_METHODS.get(marketing_method, {})
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('''
                        INSERT INTO publishing_marketing (
                            marketing_id, textbook_id, digital_id,
                            marketing_method, method_name, education_type,
                            budget, spent, target_audience,
                            campaign_name, status, start_date,
                            end_date, description, created_at, updated_at
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, 0, ?, ?, 'planning', ?, ?, ?, ?, ?)
                    ''', (marketing_id, kwargs.get('textbook_id'), kwargs.get('digital_id'),
                          marketing_method, config.get('name', marketing_method),
                          education_type, kwargs.get('budget', 0),
                          kwargs.get('target_audience'), kwargs.get('campaign_name'),
                          kwargs.get('start_date'), kwargs.get('end_date'),
                          kwargs.get('description'), now, now))
                    conn.commit()
                    logger.info(f'创建营销活动: {marketing_method} ({marketing_id})')
                    return {'success': True, 'marketing_id': marketing_id}
        except Exception as e:
            logger.error(f'创建营销活动失败: {e}')
            return {'success': False, 'error': str(e)}

    def execute_marketing_action(self, marketing_id: str, action: str,
                                 **kwargs) -> Dict[str, Any]:
        try:
            now = datetime.now().isoformat()
            actions = {'launch': '启动', 'promote': '推广', 'analyze': '分析', 'optimize': '优化'}
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('''
                        INSERT INTO marketing_records (
                            marketing_id, action, action_name,
                            channel, cost, impressions, clicks,
                            conversions, notes, created_at
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    ''', (marketing_id, action, actions.get(action, action),
                          kwargs.get('channel'), kwargs.get('cost', 0),
                          kwargs.get('impressions', 0), kwargs.get('clicks', 0),
                          kwargs.get('conversions', 0), kwargs.get('notes'), now))
                    cursor.execute('UPDATE publishing_marketing SET spent = spent + ?, status = ?, updated_at = ? WHERE marketing_id = ?',
                                 (kwargs.get('cost', 0), 'active', now, marketing_id))
                    conn.commit()
                    return {'success': True, 'action': action}
        except Exception as e:
            logger.error(f'执行营销动作失败: {e}')
            return {'success': False, 'error': str(e)}

    def complete_marketing_campaign(self, marketing_id: str) -> Dict[str, Any]:
        try:
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('UPDATE publishing_marketing SET status = ?, updated_at = ? WHERE marketing_id = ?',
                                 ('completed', now, marketing_id))
                    if cursor.rowcount > 0:
                        conn.commit()
                        return {'success': True}
                    return {'success': False, 'error': '营销活动不存在'}
        except Exception as e:
            logger.error(f'完成营销活动失败: {e}')
            return {'success': False, 'error': str(e)}

    def list_marketing_campaigns(self, education_type: str = None,
                                 marketing_method: str = None, status: str = None,
                                 page: int = 1, page_size: int = 20) -> Dict[str, Any]:
        try:
            with self._get_connection() as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                query = 'SELECT * FROM publishing_marketing WHERE 1=1'
                params = []
                if education_type:
                    query += ' AND education_type = ?'
                    params.append(education_type)
                if marketing_method:
                    query += ' AND marketing_method = ?'
                    params.append(marketing_method)
                if status:
                    query += ' AND status = ?'
                    params.append(status)
                cursor.execute(f'SELECT COUNT(*) as cnt FROM ({query})', params)
                total = cursor.fetchone()['cnt']
                query += ' ORDER BY created_at DESC LIMIT ? OFFSET ?'
                params.extend([page_size, (page - 1) * page_size])
                cursor.execute(query, params)
                campaigns = [dict(c) for c in cursor.fetchall()]
                return {'success': True, 'campaigns': campaigns, 'total': total, 'page': page, 'page_size': page_size}
        except Exception as e:
            logger.error(f'获取营销活动列表失败: {e}')
            return {'success': False, 'error': str(e)}

    # ========== 出版数据分析 ==========

    def create_analysis(self, analysis_type: str, education_type: str,
                        **kwargs) -> Dict[str, Any]:
        try:
            analysis_id = f"ans_{uuid.uuid4().hex[:12]}"
            now = datetime.now().isoformat()
            config = ANALYSIS_DIMENSIONS.get(analysis_type, {})
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('''
                        INSERT INTO publishing_analysis (
                            analysis_id, textbook_id, digital_id,
                            education_type, analysis_type, analysis_name,
                            period, data_source, status,
                            created_at, updated_at
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, 'processing', ?, ?)
                    ''', (analysis_id, kwargs.get('textbook_id'), kwargs.get('digital_id'),
                          education_type, analysis_type, config.get('name', analysis_type),
                          kwargs.get('period'), kwargs.get('data_source'), now, now))
                    conn.commit()
                    logger.info(f'创建分析任务: {analysis_type} ({analysis_id})')
                    return {'success': True, 'analysis_id': analysis_id}
        except Exception as e:
            logger.error(f'创建分析任务失败: {e}')
            return {'success': False, 'error': str(e)}

    def add_analysis_data(self, analysis_id: str, dimension: str,
                          metric: str, value: float, **kwargs) -> Dict[str, Any]:
        try:
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('''
                        INSERT INTO analysis_data (
                            analysis_id, dimension, metric,
                            value, value_text, period, created_at
                        ) VALUES (?, ?, ?, ?, ?, ?, ?)
                    ''', (analysis_id, dimension, metric, value,
                          kwargs.get('value_text'), kwargs.get('period', now[:7]), now))
                    conn.commit()
                    return {'success': True}
        except Exception as e:
            logger.error(f'添加分析数据失败: {e}')
            return {'success': False, 'error': str(e)}

    def complete_analysis(self, analysis_id: str) -> Dict[str, Any]:
        try:
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('UPDATE publishing_analysis SET status = ?, updated_at = ? WHERE analysis_id = ?',
                                 ('completed', now, analysis_id))
                    if cursor.rowcount > 0:
                        conn.commit()
                        return {'success': True}
                    return {'success': False, 'error': '分析任务不存在'}
        except Exception as e:
            logger.error(f'完成分析任务失败: {e}')
            return {'success': False, 'error': str(e)}

    def get_analysis_data(self, analysis_id: str) -> Dict[str, Any]:
        try:
            with self._get_connection() as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                cursor.execute('SELECT * FROM analysis_data WHERE analysis_id = ?', (analysis_id,))
                data = [dict(d) for d in cursor.fetchall()]
                cursor.execute('SELECT * FROM publishing_analysis WHERE analysis_id = ?', (analysis_id,))
                analysis = cursor.fetchone()
                if analysis:
                    return {'success': True, 'analysis': dict(analysis), 'data': data}
                return {'success': False, 'error': '分析任务不存在'}
        except Exception as e:
            logger.error(f'获取分析数据失败: {e}')
            return {'success': False, 'error': str(e)}

    # ========== 出版合作管理 ==========

    def create_cooperation(self, cooperation_type: str, education_type: str,
                           partner_name: str, **kwargs) -> Dict[str, Any]:
        try:
            cooperation_id = f"coo_{uuid.uuid4().hex[:12]}"
            now = datetime.now().isoformat()
            config = COOPERATION_TYPES.get(cooperation_type, {})
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('''
                        INSERT INTO publishing_cooperation (
                            cooperation_id, cooperation_type, type_name,
                            education_type, partner_name, partner_contact,
                            cooperation_model, amount, status,
                            start_date, end_date, description,
                            contract_no, created_at, updated_at
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, 'negotiating', ?, ?, ?, ?, ?, ?)
                    ''', (cooperation_id, cooperation_type, config.get('name', cooperation_type),
                          education_type, partner_name, kwargs.get('partner_contact'),
                          kwargs.get('cooperation_model'), kwargs.get('amount', 0),
                          kwargs.get('start_date'), kwargs.get('end_date'),
                          kwargs.get('description'), kwargs.get('contract_no'),
                          now, now))
                    conn.commit()
                    logger.info(f'创建合作: {cooperation_type} ({cooperation_id})')
                    return {'success': True, 'cooperation_id': cooperation_id}
        except Exception as e:
            logger.error(f'创建合作失败: {e}')
            return {'success': False, 'error': str(e)}

    def update_cooperation_status(self, cooperation_id: str, status: str,
                                  **kwargs) -> Dict[str, Any]:
        try:
            now = datetime.now().isoformat()
            statuses = {'negotiating': '洽谈中', 'agreed': '已达成', 'active': '进行中',
                        'completed': '已完成', 'terminated': '已终止'}
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('''
                        INSERT INTO cooperation_records (
                            cooperation_id, action, action_name,
                            responsible_person, date, outcome,
                            notes, created_at
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                    ''', (cooperation_id, 'status_update', statuses.get(status, status),
                          kwargs.get('responsible_person'), now[:10],
                          kwargs.get('outcome'), kwargs.get('notes'), now))
                    cursor.execute('UPDATE publishing_cooperation SET status = ?, updated_at = ? WHERE cooperation_id = ?',
                                 (status, now, cooperation_id))
                    conn.commit()
                    return {'success': True, 'status': status}
        except Exception as e:
            logger.error(f'更新合作状态失败: {e}')
            return {'success': False, 'error': str(e)}

    def sign_cooperation_contract(self, cooperation_id: str, contract_no: str,
                                  **kwargs) -> Dict[str, Any]:
        try:
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('''
                        INSERT INTO cooperation_records (
                            cooperation_id, action, action_name,
                            responsible_person, date, outcome,
                            notes, created_at
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                    ''', (cooperation_id, 'sign', '签约', kwargs.get('responsible_person'),
                          now[:10], '合同已签署', kwargs.get('notes'), now))
                    cursor.execute('UPDATE publishing_cooperation SET status = ?, contract_no = ?, updated_at = ? WHERE cooperation_id = ?',
                                 ('active', contract_no, now, cooperation_id))
                    conn.commit()
                    return {'success': True, 'contract_no': contract_no}
        except Exception as e:
            logger.error(f'签署合作合同失败: {e}')
            return {'success': False, 'error': str(e)}

    def list_cooperations(self, education_type: str = None, cooperation_type: str = None,
                          status: str = None, page: int = 1, page_size: int = 20) -> Dict[str, Any]:
        try:
            with self._get_connection() as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                query = 'SELECT * FROM publishing_cooperation WHERE 1=1'
                params = []
                if education_type:
                    query += ' AND education_type = ?'
                    params.append(education_type)
                if cooperation_type:
                    query += ' AND cooperation_type = ?'
                    params.append(cooperation_type)
                if status:
                    query += ' AND status = ?'
                    params.append(status)
                cursor.execute(f'SELECT COUNT(*) as cnt FROM ({query})', params)
                total = cursor.fetchone()['cnt']
                query += ' ORDER BY created_at DESC LIMIT ? OFFSET ?'
                params.extend([page_size, (page - 1) * page_size])
                cursor.execute(query, params)
                cooperations = [dict(c) for c in cursor.fetchall()]
                return {'success': True, 'cooperations': cooperations, 'total': total, 'page': page, 'page_size': page_size}
        except Exception as e:
            logger.error(f'获取合作列表失败: {e}')
            return {'success': False, 'error': str(e)}

    # ========== 出版质量控制 ==========

    def create_quality_check(self, control_type: str, education_type: str,
                             **kwargs) -> Dict[str, Any]:
        try:
            quality_id = f"qlt_{uuid.uuid4().hex[:12]}"
            now = datetime.now().isoformat()
            config = QUALITY_CONTROL.get(control_type, {})
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('''
                        INSERT INTO publishing_quality (
                            quality_id, textbook_id, digital_id,
                            education_type, control_type, control_name,
                            inspector, status, score, pass_threshold,
                            is_pass, notes, created_at, updated_at
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, 'pending', 0, ?, 0, ?, ?, ?)
                    ''', (quality_id, kwargs.get('textbook_id'), kwargs.get('digital_id'),
                          education_type, control_type, config.get('name', control_type),
                          kwargs.get('inspector'), kwargs.get('pass_threshold', 80),
                          kwargs.get('notes'), now, now))
                    conn.commit()
                    logger.info(f'创建质量检查: {control_type} ({quality_id})')
                    return {'success': True, 'quality_id': quality_id}
        except Exception as e:
            logger.error(f'创建质量检查失败: {e}')
            return {'success': False, 'error': str(e)}

    def add_quality_check_item(self, quality_id: str, check_item: str,
                               check_result: str, is_pass: bool) -> Dict[str, Any]:
        try:
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('''
                        INSERT INTO quality_records (
                            quality_id, check_item, check_result,
                            is_pass, notes, created_at
                        ) VALUES (?, ?, ?, ?, ?, ?)
                    ''', (quality_id, check_item, check_result, 1 if is_pass else 0,
                          check_result, now))
                    conn.commit()
                    return {'success': True}
        except Exception as e:
            logger.error(f'添加质检项失败: {e}')
            return {'success': False, 'error': str(e)}

    def complete_quality_check(self, quality_id: str, score: float,
                               **kwargs) -> Dict[str, Any]:
        try:
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('SELECT pass_threshold FROM publishing_quality WHERE quality_id = ?', (quality_id,))
                    threshold = cursor.fetchone()
                    if not threshold:
                        return {'success': False, 'error': '质检记录不存在'}
                    is_pass = 1 if score >= threshold[0] else 0
                    cursor.execute('UPDATE publishing_quality SET status = ?, score = ?, is_pass = ?, notes = ?, updated_at = ? WHERE quality_id = ?',
                                 ('completed', score, is_pass, kwargs.get('notes'), now, quality_id))
                    conn.commit()
                    return {'success': True, 'is_pass': bool(is_pass), 'score': score}
        except Exception as e:
            logger.error(f'完成质检失败: {e}')
            return {'success': False, 'error': str(e)}

    def list_quality_checks(self, education_type: str = None, control_type: str = None,
                            status: str = None, page: int = 1, page_size: int = 20) -> Dict[str, Any]:
        try:
            with self._get_connection() as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                query = 'SELECT * FROM publishing_quality WHERE 1=1'
                params = []
                if education_type:
                    query += ' AND education_type = ?'
                    params.append(education_type)
                if control_type:
                    query += ' AND control_type = ?'
                    params.append(control_type)
                if status:
                    query += ' AND status = ?'
                    params.append(status)
                cursor.execute(f'SELECT COUNT(*) as cnt FROM ({query})', params)
                total = cursor.fetchone()['cnt']
                query += ' ORDER BY created_at DESC LIMIT ? OFFSET ?'
                params.extend([page_size, (page - 1) * page_size])
                cursor.execute(query, params)
                checks = [dict(c) for c in cursor.fetchall()]
                return {'success': True, 'checks': checks, 'total': total, 'page': page, 'page_size': page_size}
        except Exception as e:
            logger.error(f'获取质检列表失败: {e}')
            return {'success': False, 'error': str(e)}

    # ========== 统计汇总 ==========

    def get_publishing_summary(self, education_type: str = None) -> Dict[str, Any]:
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                result = {}
                query = 'SELECT COUNT(*) FROM textbook_publishing WHERE status = ?'
                params = ['published']
                if education_type:
                    query += ' AND education_type = ?'
                    params.append(education_type)
                cursor.execute(query, params)
                result['published_textbooks'] = cursor.fetchone()[0] or 0
                query = 'SELECT COUNT(*) FROM digital_publishing WHERE status = ?'
                params = ['published']
                if education_type:
                    query += ' AND education_type = ?'
                    params.append(education_type)
                cursor.execute(query, params)
                result['published_digital'] = cursor.fetchone()[0] or 0
                query = 'SELECT COUNT(*) FROM copyright_management WHERE status = ?'
                params = ['active']
                cursor.execute(query, params)
                result['active_copyrights'] = cursor.fetchone()[0] or 0
                query = 'SELECT SUM(sold) FROM publishing_distribution'
                params = []
                if education_type:
                    query += ' WHERE education_type = ?'
                    params.append(education_type)
                cursor.execute(query, params)
                result['total_sold'] = cursor.fetchone()[0] or 0
                query = 'SELECT COUNT(*) FROM publishing_marketing WHERE status = ?'
                params = ['completed']
                if education_type:
                    query += ' AND education_type = ?'
                    params.append(education_type)
                cursor.execute(query, params)
                result['completed_campaigns'] = cursor.fetchone()[0] or 0
                query = 'SELECT COUNT(*) FROM publishing_cooperation WHERE status = ?'
                params = ['active']
                if education_type:
                    query += ' AND education_type = ?'
                    params.append(education_type)
                cursor.execute(query, params)
                result['active_cooperations'] = cursor.fetchone()[0] or 0
                query = 'SELECT AVG(score) FROM publishing_quality WHERE status = ?'
                params = ['completed']
                if education_type:
                    query += ' AND education_type = ?'
                    params.append(education_type)
                cursor.execute(query, params)
                avg_score = cursor.fetchone()[0]
                result['avg_quality_score'] = round(avg_score, 1) if avg_score else 0
                query = 'SELECT COUNT(*) FROM publishing_quality WHERE status = ? AND is_pass = ?'
                params = ['completed', 1]
                if education_type:
                    query += ' AND education_type = ?'
                    params.append(education_type)
                cursor.execute(query, params)
                passed = cursor.fetchone()[0] or 0
                query = 'SELECT COUNT(*) FROM publishing_quality WHERE status = ?'
                params = ['completed']
                if education_type:
                    query += ' AND education_type = ?'
                    params.append(education_type)
                cursor.execute(query, params)
                total = cursor.fetchone()[0] or 0
                result['quality_pass_rate'] = round(passed / total * 100, 1) if total > 0 else 0
                result['education_type'] = education_type or 'all'
                return {'success': True, 'summary': result}
        except Exception as e:
            logger.error(f'获取出版汇总失败: {e}')
            return {'success': False, 'error': str(e)}