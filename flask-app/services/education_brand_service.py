#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
MTSCOS 教育品牌营销服务 (v15.29.0)
====================================
提供品牌定位、品牌形象、品牌传播、品牌推广、品牌维护、品牌评估、品牌创新和品牌国际化等综合管理服务。

核心能力：
1. 品牌定位 - 差异化定位、市场定位、消费者定位、竞争定位
2. 品牌形象 - 品牌名称、品牌标志、品牌色彩、品牌口号
3. 品牌传播 - 社交媒体、网络媒体、传统媒体、口碑传播
4. 品牌推广 - 广告宣传、促销活动、公共关系、品牌合作、口碑营销
5. 品牌维护 - 客户服务、危机管理、品牌监测、舆情管理
6. 品牌评估 - 品牌知名度、品牌美誉度、品牌忠诚度、品牌价值
7. 品牌创新 - 产品创新、服务创新、营销创新、管理创新
8. 品牌国际化 - 品牌输出、跨国合作、国际认证、海外扩张

支持教育类型：成人教育 / K12教育
"""
import os
import json
import uuid
import sqlite3
import logging
import threading
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple

DATABASE_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'app.db')

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    handlers=[
        logging.FileHandler(
            os.path.join(os.path.dirname(os.path.abspath(__file__)), 'education_brand_service.log'),
            encoding='utf-8'
        ),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger('EducationBrand')


# ========== 品牌配置 ==========

BRAND_TYPES = {
    'school': {'name': '学校品牌', 'description': '各类学校的整体品牌形象'},
    'institution': {'name': '教育机构', 'description': '培训机构、教育中心等'},
    'training': {'name': '培训品牌', 'description': '职业培训、技能培训品牌'},
    'online': {'name': '在线教育', 'description': '互联网教育平台与产品'},
    'product': {'name': '教育产品', 'description': '教材、教具、学习工具'},
    'service': {'name': '教育服务', 'description': '教育咨询、测评、托管等服务'},
    'tech': {'name': '教育科技', 'description': '教育科技公司、智能教育'},
    'platform': {'name': '教育平台', 'description': '综合性教育服务平台'}
}

POSITIONING_STRATEGIES = {
    'differentiation': {'name': '差异化定位', 'focus': '突出独特卖点和竞争优势'},
    'market': {'name': '市场定位', 'focus': '明确目标市场和细分领域'},
    'consumer': {'name': '消费者定位', 'focus': '精准把握目标用户需求'},
    'competitive': {'name': '竞争定位', 'focus': '分析竞争对手制定策略'},
    'value': {'name': '价值定位', 'focus': '传递品牌核心价值主张'},
    'emotional': {'name': '情感定位', 'focus': '建立情感连接和品牌认同'},
    'functional': {'name': '功能定位', 'focus': '强调产品功能和实用性'},
    'brand': {'name': '品牌定位', 'focus': '构建完整品牌形象体系'}
}

IMAGE_ELEMENTS = {
    'name': {'name': '品牌名称', 'importance': 'high', 'description': '品牌的核心标识'},
    'logo': {'name': '品牌标志', 'importance': 'high', 'description': '视觉识别核心'},
    'color': {'name': '品牌色彩', 'importance': 'medium', 'description': '品牌专属色彩系统'},
    'slogan': {'name': '品牌口号', 'importance': 'high', 'description': '品牌核心理念表达'},
    'story': {'name': '品牌故事', 'importance': 'medium', 'description': '品牌背景和价值观'},
    'tone': {'name': '品牌调性', 'importance': 'medium', 'description': '品牌风格和气质'},
    'visual': {'name': '品牌视觉', 'importance': 'medium', 'description': '整体视觉设计系统'},
    'voice': {'name': '品牌声音', 'importance': 'low', 'description': '音频识别和声音风格'}
}

COMMUNICATION_CHANNELS = {
    'social': {'name': '社交媒体', 'channels': ['微信', '微博', '抖音', '小红书', 'B站']},
    'online': {'name': '网络媒体', 'channels': ['门户网站', '教育媒体', '行业网站', '自媒体']},
    'traditional': {'name': '传统媒体', 'channels': ['电视', '报纸', '杂志', '广播']},
    'word_of_mouth': {'name': '口碑传播', 'channels': ['用户推荐', '家长社群', '校友网络']},
    'pr': {'name': '公关传播', 'channels': ['新闻发布会', '媒体采访', '行业论坛']},
    'event': {'name': '事件营销', 'channels': ['品牌活动', '公益活动', '热点事件']},
    'content': {'name': '内容营销', 'channels': ['公众号', '短视频', '直播', '博客']},
    'interactive': {'name': '互动营销', 'channels': ['线上互动', '用户UGC', '社群运营']}
}

PROMOTION_METHODS = {
    'advertising': {'name': '广告宣传', 'methods': ['线上广告', '线下广告', '户外广告', '精准投放']},
    'promotion': {'name': '促销活动', 'methods': ['折扣优惠', '限时活动', '团购活动', '赠品活动']},
    'public_relations': {'name': '公共关系', 'methods': ['媒体合作', '政府关系', '行业协会', '公益事业']},
    'cooperation': {'name': '品牌合作', 'methods': ['跨界合作', '联名活动', '渠道合作', '异业联盟']},
    'word_of_mouth': {'name': '口碑营销', 'methods': ['用户评价', '案例分享', '转介绍奖励', '社群运营']},
    'search_engine': {'name': '搜索引擎', 'methods': ['SEO优化', 'SEM投放', '问答营销', '百科建设']},
    'social_media': {'name': '社交媒体', 'methods': ['内容运营', '粉丝互动', '话题营销', '达人合作']},
    'offline': {'name': '线下活动', 'methods': ['展会展览', '讲座论坛', '体验活动', '校园推广']}
}

MAINTENANCE_ACTIVITIES = {
    'customer_service': {'name': '客户服务', 'tasks': ['咨询服务', '投诉处理', '满意度调查', '客户回访']},
    'crisis_management': {'name': '危机管理', 'tasks': ['危机预警', '危机应对', '危机公关', '危机复盘']},
    'brand_monitoring': {'name': '品牌监测', 'tasks': ['舆情监测', '口碑监测', '竞品监测', '市场监测']},
    'reputation_management': {'name': '舆情管理', 'tasks': ['正面引导', '负面处理', '信息发布', '媒体关系']},
    'customer_relationship': {'name': '客户关系', 'tasks': ['会员管理', '客户分层', '个性化服务', '忠诚度计划']},
    'brand_upgrade': {'name': '品牌升级', 'tasks': ['形象更新', '理念升级', '服务升级', '产品升级']},
    'brand_protection': {'name': '品牌保护', 'tasks': ['商标注册', '版权保护', '域名保护', '侵权维权']},
    'brand_repair': {'name': '品牌修复', 'tasks': ['负面消除', '信任重建', '形象重塑', '口碑恢复']}
}

ASSESSMENT_DIMENSIONS = {
    'awareness': {'name': '品牌知名度', 'metrics': ['认知度', '曝光量', '搜索量', '提及率']},
    'reputation': {'name': '品牌美誉度', 'metrics': ['好评率', '推荐度', '媒体评价', '行业认可']},
    'loyalty': {'name': '品牌忠诚度', 'metrics': ['复购率', '续费率', '转介绍率', '品牌依赖度']},
    'value': {'name': '品牌价值', 'metrics': ['市场估值', '品牌溢价', '用户价值', '资产价值']},
    'influence': {'name': '品牌影响力', 'metrics': ['行业地位', '媒体影响力', '社会影响力', '话语权']},
    'competitiveness': {'name': '品牌竞争力', 'metrics': ['市场份额', '竞争优势', '差异化程度', '创新能力']},
    'vitality': {'name': '品牌活力', 'metrics': ['用户活跃度', '内容更新频率', '创新速度', '年轻化程度']},
    'health': {'name': '品牌健康度', 'metrics': ['舆情健康度', '用户满意度', '财务状况', '发展潜力']}
}

INTERNATIONALIZATION_STRATEGIES = {
    'export': {'name': '品牌输出', 'approach': '将成熟品牌模式复制到海外市场'},
    'cooperation': {'name': '跨国合作', 'approach': '与海外机构建立战略合作关系'},
    'certification': {'name': '国际认证', 'approach': '获取国际权威机构认证和认可'},
    'expansion': {'name': '海外扩张', 'approach': '在海外建立分支机构和运营团队'},
    'localization': {'name': '本地化策略', 'approach': '根据当地市场特点调整品牌策略'},
    'cultural_integration': {'name': '文化融合', 'approach': '融合本地文化元素和品牌特色'},
    'global_marketing': {'name': '全球营销', 'approach': '实施统一的全球品牌营销计划'},
    'alliance': {'name': '品牌联盟', 'approach': '与国际品牌建立联盟合作关系'}
}


class EducationBrandService:
    """教育品牌营销服务"""

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
                    CREATE TABLE IF NOT EXISTS brand_positioning (
                        positioning_id TEXT PRIMARY KEY,
                        brand_name TEXT NOT NULL,
                        brand_type TEXT,
                        education_type TEXT NOT NULL,
                        strategy TEXT,
                        target_market TEXT,
                        target_users TEXT,
                        competitive_analysis TEXT,
                        value_proposition TEXT,
                        positioning_statement TEXT,
                        differentiators TEXT,
                        status TEXT DEFAULT 'draft',
                        created_at TEXT,
                        updated_at TEXT
                    )
                ''')
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS positioning_records (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        positioning_id TEXT NOT NULL,
                        action_type TEXT,
                        action_desc TEXT,
                        performed_by TEXT,
                        created_at TEXT
                    )
                ''')
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS brand_image (
                        image_id TEXT PRIMARY KEY,
                        brand_name TEXT NOT NULL,
                        education_type TEXT NOT NULL,
                        brand_name_en TEXT,
                        logo_url TEXT,
                        logo_description TEXT,
                        color_palette TEXT,
                        slogan TEXT,
                        brand_story TEXT,
                        brand_tone TEXT,
                        visual_guidelines TEXT,
                        voice_description TEXT,
                        status TEXT DEFAULT 'draft',
                        created_at TEXT,
                        updated_at TEXT
                    )
                ''')
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS image_records (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        image_id TEXT NOT NULL,
                        element_type TEXT,
                        change_desc TEXT,
                        performed_by TEXT,
                        created_at TEXT
                    )
                ''')
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS brand_communication (
                        communication_id TEXT PRIMARY KEY,
                        brand_name TEXT NOT NULL,
                        education_type TEXT NOT NULL,
                        channel TEXT,
                        platform TEXT,
                        content_type TEXT,
                        content_title TEXT,
                        content_body TEXT,
                        target_audience TEXT,
                        publish_date TEXT,
                        reach_count INTEGER DEFAULT 0,
                        engagement_count INTEGER DEFAULT 0,
                        conversion_count INTEGER DEFAULT 0,
                        status TEXT DEFAULT 'planned',
                        created_at TEXT,
                        updated_at TEXT
                    )
                ''')
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS communication_records (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        communication_id TEXT NOT NULL,
                        action_type TEXT,
                        action_desc TEXT,
                        metrics TEXT,
                        created_at TEXT
                    )
                ''')
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS brand_promotion (
                        promotion_id TEXT PRIMARY KEY,
                        brand_name TEXT NOT NULL,
                        education_type TEXT NOT NULL,
                        method TEXT,
                        promotion_name TEXT NOT NULL,
                        description TEXT,
                        start_date TEXT,
                        end_date TEXT,
                        budget REAL DEFAULT 0,
                        actual_cost REAL DEFAULT 0,
                        target_audience TEXT,
                        channels TEXT,
                        expected_reach INTEGER DEFAULT 0,
                        actual_reach INTEGER DEFAULT 0,
                        expected_conversion INTEGER DEFAULT 0,
                        actual_conversion INTEGER DEFAULT 0,
                        status TEXT DEFAULT 'planned',
                        created_at TEXT,
                        updated_at TEXT
                    )
                ''')
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS promotion_records (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        promotion_id TEXT NOT NULL,
                        action_type TEXT,
                        action_desc TEXT,
                        metrics TEXT,
                        created_at TEXT
                    )
                ''')
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS brand_maintenance (
                        maintenance_id TEXT PRIMARY KEY,
                        brand_name TEXT NOT NULL,
                        education_type TEXT NOT NULL,
                        activity_type TEXT,
                        activity_name TEXT NOT NULL,
                        description TEXT,
                        priority TEXT DEFAULT 'medium',
                        status TEXT DEFAULT 'pending',
                        assignee TEXT,
                        deadline TEXT,
                        completion_date TEXT,
                        created_at TEXT,
                        updated_at TEXT
                    )
                ''')
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS maintenance_records (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        maintenance_id TEXT NOT NULL,
                        action_type TEXT,
                        action_desc TEXT,
                        performed_by TEXT,
                        created_at TEXT
                    )
                ''')
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS brand_assessment (
                        assessment_id TEXT PRIMARY KEY,
                        brand_name TEXT NOT NULL,
                        education_type TEXT NOT NULL,
                        dimension TEXT,
                        assessment_period TEXT,
                        score REAL DEFAULT 0,
                        rating TEXT,
                        metrics_data TEXT,
                        analysis_report TEXT,
                        recommendations TEXT,
                        assessor TEXT,
                        status TEXT DEFAULT 'in_progress',
                        created_at TEXT,
                        updated_at TEXT
                    )
                ''')
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS assessment_records (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        assessment_id TEXT NOT NULL,
                        action_type TEXT,
                        action_desc TEXT,
                        performed_by TEXT,
                        created_at TEXT
                    )
                ''')
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS brand_innovation (
                        innovation_id TEXT PRIMARY KEY,
                        brand_name TEXT NOT NULL,
                        education_type TEXT NOT NULL,
                        innovation_type TEXT,
                        innovation_name TEXT NOT NULL,
                        description TEXT,
                        objectives TEXT,
                        status TEXT DEFAULT 'ideation',
                        implementation_date TEXT,
                        impact_analysis TEXT,
                        roi REAL DEFAULT 0,
                        created_at TEXT,
                        updated_at TEXT
                    )
                ''')
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS innovation_records (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        innovation_id TEXT NOT NULL,
                        action_type TEXT,
                        action_desc TEXT,
                        performed_by TEXT,
                        created_at TEXT
                    )
                ''')
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS brand_internationalization (
                        internationalization_id TEXT PRIMARY KEY,
                        brand_name TEXT NOT NULL,
                        education_type TEXT NOT NULL,
                        strategy TEXT,
                        target_market TEXT,
                        country_region TEXT,
                        partnership TEXT,
                        certification TEXT,
                        localization_plan TEXT,
                        timeline TEXT,
                        budget REAL DEFAULT 0,
                        status TEXT DEFAULT 'planning',
                        created_at TEXT,
                        updated_at TEXT
                    )
                ''')
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS internationalization_records (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        internationalization_id TEXT NOT NULL,
                        action_type TEXT,
                        action_desc TEXT,
                        performed_by TEXT,
                        created_at TEXT
                    )
                ''')
                conn.commit()
                logger.info('教育品牌营销服务数据库初始化完成')
        except Exception as e:
            logger.error(f'数据库初始化失败: {e}')

    # ========== 品牌定位 ==========

    def create_positioning(self, brand_name: str, education_type: str,
                           strategy: str, **kwargs) -> Dict[str, Any]:
        try:
            positioning_id = f"bpd_{uuid.uuid4().hex[:12]}"
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('''
                        INSERT INTO brand_positioning (
                            positioning_id, brand_name, brand_type,
                            education_type, strategy, target_market,
                            target_users, competitive_analysis,
                            value_proposition, positioning_statement,
                            differentiators, status, created_at, updated_at
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'draft', ?, ?)
                    ''', (positioning_id, brand_name,
                          kwargs.get('brand_type'), education_type, strategy,
                          kwargs.get('target_market'), kwargs.get('target_users'),
                          kwargs.get('competitive_analysis'),
                          kwargs.get('value_proposition'),
                          kwargs.get('positioning_statement'),
                          kwargs.get('differentiators'), now, now))
                    cursor.execute('INSERT INTO positioning_records (positioning_id, action_type, action_desc, performed_by, created_at) VALUES (?, ?, ?, ?, ?)',
                                 (positioning_id, 'create', '创建品牌定位方案', kwargs.get('performed_by'), now))
                    conn.commit()
                    logger.info(f'创建品牌定位: {brand_name} ({positioning_id})')
                    return {'success': True, 'positioning_id': positioning_id}
        except Exception as e:
            logger.error(f'创建品牌定位失败: {e}')
            return {'success': False, 'error': str(e)}

    def update_positioning(self, positioning_id: str, **kwargs) -> Dict[str, Any]:
        try:
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    update_fields = []
                    params = []
                    if 'brand_name' in kwargs:
                        update_fields.append('brand_name = ?')
                        params.append(kwargs['brand_name'])
                    if 'brand_type' in kwargs:
                        update_fields.append('brand_type = ?')
                        params.append(kwargs['brand_type'])
                    if 'strategy' in kwargs:
                        update_fields.append('strategy = ?')
                        params.append(kwargs['strategy'])
                    if 'target_market' in kwargs:
                        update_fields.append('target_market = ?')
                        params.append(kwargs['target_market'])
                    if 'target_users' in kwargs:
                        update_fields.append('target_users = ?')
                        params.append(kwargs['target_users'])
                    if 'competitive_analysis' in kwargs:
                        update_fields.append('competitive_analysis = ?')
                        params.append(kwargs['competitive_analysis'])
                    if 'value_proposition' in kwargs:
                        update_fields.append('value_proposition = ?')
                        params.append(kwargs['value_proposition'])
                    if 'positioning_statement' in kwargs:
                        update_fields.append('positioning_statement = ?')
                        params.append(kwargs['positioning_statement'])
                    if 'differentiators' in kwargs:
                        update_fields.append('differentiators = ?')
                        params.append(kwargs['differentiators'])
                    if 'status' in kwargs:
                        update_fields.append('status = ?')
                        params.append(kwargs['status'])
                    update_fields.append('updated_at = ?')
                    params.append(now)
                    params.append(positioning_id)
                    cursor.execute(f'UPDATE brand_positioning SET {", ".join(update_fields)} WHERE positioning_id = ?', params)
                    if cursor.rowcount > 0:
                        cursor.execute('INSERT INTO positioning_records (positioning_id, action_type, action_desc, performed_by, created_at) VALUES (?, ?, ?, ?, ?)',
                                     (positioning_id, 'update', '更新品牌定位方案', kwargs.get('performed_by'), now))
                        conn.commit()
                        return {'success': True}
                    return {'success': False, 'error': '定位方案不存在'}
        except Exception as e:
            logger.error(f'更新品牌定位失败: {e}')
            return {'success': False, 'error': str(e)}

    def get_positioning(self, positioning_id: str) -> Dict[str, Any]:
        try:
            with self._get_connection() as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                cursor.execute('SELECT * FROM brand_positioning WHERE positioning_id = ?', (positioning_id,))
                positioning = cursor.fetchone()
                if positioning:
                    return {'success': True, 'positioning': dict(positioning)}
                return {'success': False, 'error': '定位方案不存在'}
        except Exception as e:
            logger.error(f'获取品牌定位失败: {e}')
            return {'success': False, 'error': str(e)}

    def list_positioning(self, brand_name: str = None, education_type: str = None,
                         status: str = None, page: int = 1, page_size: int = 20) -> Dict[str, Any]:
        try:
            with self._get_connection() as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                query = 'SELECT * FROM brand_positioning WHERE 1=1'
                params = []
                if brand_name:
                    query += ' AND brand_name = ?'
                    params.append(brand_name)
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
                positionings = [dict(p) for p in cursor.fetchall()]
                return {'success': True, 'positionings': positionings, 'total': total, 'page': page, 'page_size': page_size}
        except Exception as e:
            logger.error(f'获取品牌定位列表失败: {e}')
            return {'success': False, 'error': str(e)}

    # ========== 品牌形象 ==========

    def create_brand_image(self, brand_name: str, education_type: str, **kwargs) -> Dict[str, Any]:
        try:
            image_id = f"bim_{uuid.uuid4().hex[:12]}"
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('''
                        INSERT INTO brand_image (
                            image_id, brand_name, education_type,
                            brand_name_en, logo_url, logo_description,
                            color_palette, slogan, brand_story,
                            brand_tone, visual_guidelines, voice_description,
                            status, created_at, updated_at
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'draft', ?, ?)
                    ''', (image_id, brand_name, education_type,
                          kwargs.get('brand_name_en'), kwargs.get('logo_url'),
                          kwargs.get('logo_description'), kwargs.get('color_palette'),
                          kwargs.get('slogan'), kwargs.get('brand_story'),
                          kwargs.get('brand_tone'), kwargs.get('visual_guidelines'),
                          kwargs.get('voice_description'), now, now))
                    cursor.execute('INSERT INTO image_records (image_id, element_type, change_desc, performed_by, created_at) VALUES (?, ?, ?, ?, ?)',
                                 (image_id, 'create', '创建品牌形象方案', kwargs.get('performed_by'), now))
                    conn.commit()
                    logger.info(f'创建品牌形象: {brand_name} ({image_id})')
                    return {'success': True, 'image_id': image_id}
        except Exception as e:
            logger.error(f'创建品牌形象失败: {e}')
            return {'success': False, 'error': str(e)}

    def update_image_element(self, image_id: str, element_type: str, value: str,
                             **kwargs) -> Dict[str, Any]:
        try:
            now = datetime.now().isoformat()
            element_mapping = {
                'name': 'brand_name',
                'logo': 'logo_url',
                'color': 'color_palette',
                'slogan': 'slogan',
                'story': 'brand_story',
                'tone': 'brand_tone',
                'visual': 'visual_guidelines',
                'voice': 'voice_description'
            }
            db_field = element_mapping.get(element_type)
            if not db_field:
                return {'success': False, 'error': '无效的形象元素类型'}
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute(f'UPDATE brand_image SET {db_field} = ?, updated_at = ? WHERE image_id = ?', (value, now, image_id))
                    if cursor.rowcount > 0:
                        cursor.execute('INSERT INTO image_records (image_id, element_type, change_desc, performed_by, created_at) VALUES (?, ?, ?, ?, ?)',
                                     (image_id, element_type, f'更新{IMAGE_ELEMENTS.get(element_type, {}).get("name", element_type)}', kwargs.get('performed_by'), now))
                        conn.commit()
                        return {'success': True}
                    return {'success': False, 'error': '品牌形象不存在'}
        except Exception as e:
            logger.error(f'更新品牌形象元素失败: {e}')
            return {'success': False, 'error': str(e)}

    def get_brand_image(self, image_id: str) -> Dict[str, Any]:
        try:
            with self._get_connection() as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                cursor.execute('SELECT * FROM brand_image WHERE image_id = ?', (image_id,))
                image = cursor.fetchone()
                if image:
                    return {'success': True, 'image': dict(image)}
                return {'success': False, 'error': '品牌形象不存在'}
        except Exception as e:
            logger.error(f'获取品牌形象失败: {e}')
            return {'success': False, 'error': str(e)}

    def list_brand_images(self, brand_name: str = None, education_type: str = None,
                          status: str = None, page: int = 1, page_size: int = 20) -> Dict[str, Any]:
        try:
            with self._get_connection() as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                query = 'SELECT * FROM brand_image WHERE 1=1'
                params = []
                if brand_name:
                    query += ' AND brand_name = ?'
                    params.append(brand_name)
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
                images = [dict(i) for i in cursor.fetchall()]
                return {'success': True, 'images': images, 'total': total, 'page': page, 'page_size': page_size}
        except Exception as e:
            logger.error(f'获取品牌形象列表失败: {e}')
            return {'success': False, 'error': str(e)}

    # ========== 品牌传播 ==========

    def create_communication(self, brand_name: str, education_type: str,
                             channel: str, content_title: str, **kwargs) -> Dict[str, Any]:
        try:
            communication_id = f"bcm_{uuid.uuid4().hex[:12]}"
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('''
                        INSERT INTO brand_communication (
                            communication_id, brand_name, education_type,
                            channel, platform, content_type,
                            content_title, content_body, target_audience,
                            publish_date, reach_count, engagement_count,
                            conversion_count, status, created_at, updated_at
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 0, 0, 0, 'planned', ?, ?)
                    ''', (communication_id, brand_name, education_type, channel,
                          kwargs.get('platform'), kwargs.get('content_type'),
                          content_title, kwargs.get('content_body'),
                          kwargs.get('target_audience'), kwargs.get('publish_date'),
                          now, now))
                    cursor.execute('INSERT INTO communication_records (communication_id, action_type, action_desc, metrics, created_at) VALUES (?, ?, ?, ?, ?)',
                                 (communication_id, 'create', '创建传播内容', '{}', now))
                    conn.commit()
                    logger.info(f'创建品牌传播: {content_title} ({communication_id})')
                    return {'success': True, 'communication_id': communication_id}
        except Exception as e:
            logger.error(f'创建品牌传播失败: {e}')
            return {'success': False, 'error': str(e)}

    def publish_communication(self, communication_id: str, **kwargs) -> Dict[str, Any]:
        try:
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('UPDATE brand_communication SET status = ?, publish_date = ?, updated_at = ? WHERE communication_id = ? AND status = ?',
                                 ('published', kwargs.get('publish_date', now[:10]), now, communication_id, 'planned'))
                    if cursor.rowcount > 0:
                        cursor.execute('INSERT INTO communication_records (communication_id, action_type, action_desc, metrics, created_at) VALUES (?, ?, ?, ?, ?)',
                                     (communication_id, 'publish', '发布传播内容', '{}', now))
                        conn.commit()
                        return {'success': True}
                    return {'success': False, 'error': '传播内容状态不允许发布'}
        except Exception as e:
            logger.error(f'发布品牌传播失败: {e}')
            return {'success': False, 'error': str(e)}

    def update_communication_metrics(self, communication_id: str, **kwargs) -> Dict[str, Any]:
        try:
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    update_fields = []
                    params = []
                    if 'reach_count' in kwargs:
                        update_fields.append('reach_count = ?')
                        params.append(kwargs['reach_count'])
                    if 'engagement_count' in kwargs:
                        update_fields.append('engagement_count = ?')
                        params.append(kwargs['engagement_count'])
                    if 'conversion_count' in kwargs:
                        update_fields.append('conversion_count = ?')
                        params.append(kwargs['conversion_count'])
                    update_fields.append('updated_at = ?')
                    params.append(now)
                    params.append(communication_id)
                    cursor.execute(f'UPDATE brand_communication SET {", ".join(update_fields)} WHERE communication_id = ?', params)
                    if cursor.rowcount > 0:
                        metrics = json.dumps({k: v for k, v in kwargs.items() if k in ['reach_count', 'engagement_count', 'conversion_count']})
                        cursor.execute('INSERT INTO communication_records (communication_id, action_type, action_desc, metrics, created_at) VALUES (?, ?, ?, ?, ?)',
                                     (communication_id, 'metrics', '更新传播数据', metrics, now))
                        conn.commit()
                        return {'success': True}
                    return {'success': False, 'error': '传播内容不存在'}
        except Exception as e:
            logger.error(f'更新传播数据失败: {e}')
            return {'success': False, 'error': str(e)}

    def list_communications(self, brand_name: str = None, education_type: str = None,
                            channel: str = None, status: str = None,
                            page: int = 1, page_size: int = 20) -> Dict[str, Any]:
        try:
            with self._get_connection() as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                query = 'SELECT * FROM brand_communication WHERE 1=1'
                params = []
                if brand_name:
                    query += ' AND brand_name = ?'
                    params.append(brand_name)
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
                communications = [dict(c) for c in cursor.fetchall()]
                return {'success': True, 'communications': communications, 'total': total, 'page': page, 'page_size': page_size}
        except Exception as e:
            logger.error(f'获取传播列表失败: {e}')
            return {'success': False, 'error': str(e)}

    # ========== 品牌推广 ==========

    def create_promotion(self, brand_name: str, education_type: str,
                         method: str, promotion_name: str, **kwargs) -> Dict[str, Any]:
        try:
            promotion_id = f"bpr_{uuid.uuid4().hex[:12]}"
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('''
                        INSERT INTO brand_promotion (
                            promotion_id, brand_name, education_type,
                            method, promotion_name, description,
                            start_date, end_date, budget, actual_cost,
                            target_audience, channels, expected_reach,
                            actual_reach, expected_conversion, actual_conversion,
                            status, created_at, updated_at
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, 0, ?, ?, ?, 0, ?, 0, 'planned', ?, ?)
                    ''', (promotion_id, brand_name, education_type, method,
                          promotion_name, kwargs.get('description'),
                          kwargs.get('start_date'), kwargs.get('end_date'),
                          kwargs.get('budget', 0), kwargs.get('target_audience'),
                          kwargs.get('channels'), kwargs.get('expected_reach', 0),
                          kwargs.get('expected_conversion', 0), now, now))
                    cursor.execute('INSERT INTO promotion_records (promotion_id, action_type, action_desc, metrics, created_at) VALUES (?, ?, ?, ?, ?)',
                                 (promotion_id, 'create', '创建推广活动', '{}', now))
                    conn.commit()
                    logger.info(f'创建品牌推广: {promotion_name} ({promotion_id})')
                    return {'success': True, 'promotion_id': promotion_id}
        except Exception as e:
            logger.error(f'创建品牌推广失败: {e}')
            return {'success': False, 'error': str(e)}

    def start_promotion(self, promotion_id: str) -> Dict[str, Any]:
        try:
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('UPDATE brand_promotion SET status = ?, updated_at = ? WHERE promotion_id = ? AND status = ?',
                                 ('active', now, promotion_id, 'planned'))
                    if cursor.rowcount > 0:
                        cursor.execute('INSERT INTO promotion_records (promotion_id, action_type, action_desc, metrics, created_at) VALUES (?, ?, ?, ?, ?)',
                                     (promotion_id, 'start', '启动推广活动', '{}', now))
                        conn.commit()
                        return {'success': True}
                    return {'success': False, 'error': '推广活动状态不允许启动'}
        except Exception as e:
            logger.error(f'启动品牌推广失败: {e}')
            return {'success': False, 'error': str(e)}

    def end_promotion(self, promotion_id: str, **kwargs) -> Dict[str, Any]:
        try:
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('UPDATE brand_promotion SET status = ?, actual_cost = ?, updated_at = ? WHERE promotion_id = ? AND status = ?',
                                 ('ended', kwargs.get('actual_cost', 0), now, promotion_id, 'active'))
                    if cursor.rowcount > 0:
                        metrics = json.dumps({k: v for k, v in kwargs.items() if k in ['actual_cost', 'actual_reach', 'actual_conversion']})
                        cursor.execute('INSERT INTO promotion_records (promotion_id, action_type, action_desc, metrics, created_at) VALUES (?, ?, ?, ?, ?)',
                                     (promotion_id, 'end', '结束推广活动', metrics, now))
                        conn.commit()
                        return {'success': True}
                    return {'success': False, 'error': '推广活动状态不允许结束'}
        except Exception as e:
            logger.error(f'结束品牌推广失败: {e}')
            return {'success': False, 'error': str(e)}

    def update_promotion_metrics(self, promotion_id: str, **kwargs) -> Dict[str, Any]:
        try:
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    update_fields = []
                    params = []
                    if 'actual_cost' in kwargs:
                        update_fields.append('actual_cost = ?')
                        params.append(kwargs['actual_cost'])
                    if 'actual_reach' in kwargs:
                        update_fields.append('actual_reach = ?')
                        params.append(kwargs['actual_reach'])
                    if 'actual_conversion' in kwargs:
                        update_fields.append('actual_conversion = ?')
                        params.append(kwargs['actual_conversion'])
                    update_fields.append('updated_at = ?')
                    params.append(now)
                    params.append(promotion_id)
                    cursor.execute(f'UPDATE brand_promotion SET {", ".join(update_fields)} WHERE promotion_id = ?', params)
                    if cursor.rowcount > 0:
                        metrics = json.dumps({k: v for k, v in kwargs.items() if k in ['actual_cost', 'actual_reach', 'actual_conversion']})
                        cursor.execute('INSERT INTO promotion_records (promotion_id, action_type, action_desc, metrics, created_at) VALUES (?, ?, ?, ?, ?)',
                                     (promotion_id, 'metrics', '更新推广数据', metrics, now))
                        conn.commit()
                        return {'success': True}
                    return {'success': False, 'error': '推广活动不存在'}
        except Exception as e:
            logger.error(f'更新推广数据失败: {e}')
            return {'success': False, 'error': str(e)}

    def list_promotions(self, brand_name: str = None, education_type: str = None,
                        method: str = None, status: str = None,
                        page: int = 1, page_size: int = 20) -> Dict[str, Any]:
        try:
            with self._get_connection() as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                query = 'SELECT * FROM brand_promotion WHERE 1=1'
                params = []
                if brand_name:
                    query += ' AND brand_name = ?'
                    params.append(brand_name)
                if education_type:
                    query += ' AND education_type = ?'
                    params.append(education_type)
                if method:
                    query += ' AND method = ?'
                    params.append(method)
                if status:
                    query += ' AND status = ?'
                    params.append(status)
                cursor.execute(f'SELECT COUNT(*) as cnt FROM ({query})', params)
                total = cursor.fetchone()['cnt']
                query += ' ORDER BY created_at DESC LIMIT ? OFFSET ?'
                params.extend([page_size, (page - 1) * page_size])
                cursor.execute(query, params)
                promotions = [dict(p) for p in cursor.fetchall()]
                return {'success': True, 'promotions': promotions, 'total': total, 'page': page, 'page_size': page_size}
        except Exception as e:
            logger.error(f'获取推广列表失败: {e}')
            return {'success': False, 'error': str(e)}

    # ========== 品牌维护 ==========

    def create_maintenance(self, brand_name: str, education_type: str,
                           activity_type: str, activity_name: str, **kwargs) -> Dict[str, Any]:
        try:
            maintenance_id = f"bmnt_{uuid.uuid4().hex[:12]}"
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('''
                        INSERT INTO brand_maintenance (
                            maintenance_id, brand_name, education_type,
                            activity_type, activity_name, description,
                            priority, status, assignee, deadline,
                            completion_date, created_at, updated_at
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, 'pending', ?, ?, NULL, ?, ?)
                    ''', (maintenance_id, brand_name, education_type, activity_type,
                          activity_name, kwargs.get('description'),
                          kwargs.get('priority', 'medium'), kwargs.get('assignee'),
                          kwargs.get('deadline'), now, now))
                    cursor.execute('INSERT INTO maintenance_records (maintenance_id, action_type, action_desc, performed_by, created_at) VALUES (?, ?, ?, ?, ?)',
                                 (maintenance_id, 'create', '创建维护任务', kwargs.get('performed_by'), now))
                    conn.commit()
                    logger.info(f'创建品牌维护: {activity_name} ({maintenance_id})')
                    return {'success': True, 'maintenance_id': maintenance_id}
        except Exception as e:
            logger.error(f'创建品牌维护失败: {e}')
            return {'success': False, 'error': str(e)}

    def update_maintenance_status(self, maintenance_id: str, status: str, **kwargs) -> Dict[str, Any]:
        try:
            now = datetime.now().isoformat()
            completion_date = now[:10] if status == 'completed' else None
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('UPDATE brand_maintenance SET status = ?, completion_date = ?, updated_at = ? WHERE maintenance_id = ?',
                                 (status, completion_date, now, maintenance_id))
                    if cursor.rowcount > 0:
                        cursor.execute('INSERT INTO maintenance_records (maintenance_id, action_type, action_desc, performed_by, created_at) VALUES (?, ?, ?, ?, ?)',
                                     (maintenance_id, 'status', f'状态变更为{status}', kwargs.get('performed_by'), now))
                        conn.commit()
                        return {'success': True}
                    return {'success': False, 'error': '维护任务不存在'}
        except Exception as e:
            logger.error(f'更新维护状态失败: {e}')
            return {'success': False, 'error': str(e)}

    def get_maintenance(self, maintenance_id: str) -> Dict[str, Any]:
        try:
            with self._get_connection() as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                cursor.execute('SELECT * FROM brand_maintenance WHERE maintenance_id = ?', (maintenance_id,))
                maintenance = cursor.fetchone()
                if maintenance:
                    return {'success': True, 'maintenance': dict(maintenance)}
                return {'success': False, 'error': '维护任务不存在'}
        except Exception as e:
            logger.error(f'获取品牌维护失败: {e}')
            return {'success': False, 'error': str(e)}

    def list_maintenance(self, brand_name: str = None, education_type: str = None,
                         activity_type: str = None, status: str = None,
                         page: int = 1, page_size: int = 20) -> Dict[str, Any]:
        try:
            with self._get_connection() as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                query = 'SELECT * FROM brand_maintenance WHERE 1=1'
                params = []
                if brand_name:
                    query += ' AND brand_name = ?'
                    params.append(brand_name)
                if education_type:
                    query += ' AND education_type = ?'
                    params.append(education_type)
                if activity_type:
                    query += ' AND activity_type = ?'
                    params.append(activity_type)
                if status:
                    query += ' AND status = ?'
                    params.append(status)
                cursor.execute(f'SELECT COUNT(*) as cnt FROM ({query})', params)
                total = cursor.fetchone()['cnt']
                query += ' ORDER BY created_at DESC LIMIT ? OFFSET ?'
                params.extend([page_size, (page - 1) * page_size])
                cursor.execute(query, params)
                maintenances = [dict(m) for m in cursor.fetchall()]
                return {'success': True, 'maintenances': maintenances, 'total': total, 'page': page, 'page_size': page_size}
        except Exception as e:
            logger.error(f'获取维护列表失败: {e}')
            return {'success': False, 'error': str(e)}

    # ========== 品牌评估 ==========

    def create_assessment(self, brand_name: str, education_type: str,
                          dimension: str, assessment_period: str, **kwargs) -> Dict[str, Any]:
        try:
            assessment_id = f"bass_{uuid.uuid4().hex[:12]}"
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('''
                        INSERT INTO brand_assessment (
                            assessment_id, brand_name, education_type,
                            dimension, assessment_period, score,
                            rating, metrics_data, analysis_report,
                            recommendations, assessor, status,
                            created_at, updated_at
                        ) VALUES (?, ?, ?, ?, ?, 0, NULL, ?, ?, ?, ?, 'in_progress', ?, ?)
                    ''', (assessment_id, brand_name, education_type, dimension,
                          assessment_period, kwargs.get('metrics_data', '{}'),
                          kwargs.get('analysis_report'), kwargs.get('recommendations'),
                          kwargs.get('assessor'), now, now))
                    cursor.execute('INSERT INTO assessment_records (assessment_id, action_type, action_desc, performed_by, created_at) VALUES (?, ?, ?, ?, ?)',
                                 (assessment_id, 'create', '创建品牌评估', kwargs.get('assessor'), now))
                    conn.commit()
                    logger.info(f'创建品牌评估: {brand_name} - {dimension} ({assessment_id})')
                    return {'success': True, 'assessment_id': assessment_id}
        except Exception as e:
            logger.error(f'创建品牌评估失败: {e}')
            return {'success': False, 'error': str(e)}

    def update_assessment_score(self, assessment_id: str, score: float, **kwargs) -> Dict[str, Any]:
        try:
            now = datetime.now().isoformat()
            rating = 'excellent' if score >= 90 else ('good' if score >= 80 else ('pass' if score >= 60 else 'fail'))
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('UPDATE brand_assessment SET score = ?, rating = ?, updated_at = ? WHERE assessment_id = ?',
                                 (score, rating, now, assessment_id))
                    if cursor.rowcount > 0:
                        cursor.execute('INSERT INTO assessment_records (assessment_id, action_type, action_desc, performed_by, created_at) VALUES (?, ?, ?, ?, ?)',
                                     (assessment_id, 'score', f'评分更新为{score}', kwargs.get('assessor'), now))
                        conn.commit()
                        return {'success': True, 'rating': rating}
                    return {'success': False, 'error': '评估记录不存在'}
        except Exception as e:
            logger.error(f'更新评估分数失败: {e}')
            return {'success': False, 'error': str(e)}

    def complete_assessment(self, assessment_id: str, **kwargs) -> Dict[str, Any]:
        try:
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    update_fields = ['status = ?']
                    params = ['completed']
                    if 'analysis_report' in kwargs:
                        update_fields.append('analysis_report = ?')
                        params.append(kwargs['analysis_report'])
                    if 'recommendations' in kwargs:
                        update_fields.append('recommendations = ?')
                        params.append(kwargs['recommendations'])
                    update_fields.append('updated_at = ?')
                    params.append(now)
                    params.append(assessment_id)
                    cursor.execute(f'UPDATE brand_assessment SET {", ".join(update_fields)} WHERE assessment_id = ?', params)
                    if cursor.rowcount > 0:
                        cursor.execute('INSERT INTO assessment_records (assessment_id, action_type, action_desc, performed_by, created_at) VALUES (?, ?, ?, ?, ?)',
                                     (assessment_id, 'complete', '完成品牌评估', kwargs.get('assessor'), now))
                        conn.commit()
                        return {'success': True}
                    return {'success': False, 'error': '评估记录不存在'}
        except Exception as e:
            logger.error(f'完成品牌评估失败: {e}')
            return {'success': False, 'error': str(e)}

    def list_assessments(self, brand_name: str = None, education_type: str = None,
                         dimension: str = None, status: str = None,
                         page: int = 1, page_size: int = 20) -> Dict[str, Any]:
        try:
            with self._get_connection() as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                query = 'SELECT * FROM brand_assessment WHERE 1=1'
                params = []
                if brand_name:
                    query += ' AND brand_name = ?'
                    params.append(brand_name)
                if education_type:
                    query += ' AND education_type = ?'
                    params.append(education_type)
                if dimension:
                    query += ' AND dimension = ?'
                    params.append(dimension)
                if status:
                    query += ' AND status = ?'
                    params.append(status)
                cursor.execute(f'SELECT COUNT(*) as cnt FROM ({query})', params)
                total = cursor.fetchone()['cnt']
                query += ' ORDER BY created_at DESC LIMIT ? OFFSET ?'
                params.extend([page_size, (page - 1) * page_size])
                cursor.execute(query, params)
                assessments = [dict(a) for a in cursor.fetchall()]
                return {'success': True, 'assessments': assessments, 'total': total, 'page': page, 'page_size': page_size}
        except Exception as e:
            logger.error(f'获取评估列表失败: {e}')
            return {'success': False, 'error': str(e)}

    # ========== 品牌创新 ==========

    def create_innovation(self, brand_name: str, education_type: str,
                          innovation_type: str, innovation_name: str, **kwargs) -> Dict[str, Any]:
        try:
            innovation_id = f"binn_{uuid.uuid4().hex[:12]}"
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('''
                        INSERT INTO brand_innovation (
                            innovation_id, brand_name, education_type,
                            innovation_type, innovation_name, description,
                            objectives, status, implementation_date,
                            impact_analysis, roi, created_at, updated_at
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, 'ideation', NULL, NULL, 0, ?, ?)
                    ''', (innovation_id, brand_name, education_type, innovation_type,
                          innovation_name, kwargs.get('description'),
                          kwargs.get('objectives'), now, now))
                    cursor.execute('INSERT INTO innovation_records (innovation_id, action_type, action_desc, performed_by, created_at) VALUES (?, ?, ?, ?, ?)',
                                 (innovation_id, 'create', '创建创新项目', kwargs.get('performed_by'), now))
                    conn.commit()
                    logger.info(f'创建品牌创新: {innovation_name} ({innovation_id})')
                    return {'success': True, 'innovation_id': innovation_id}
        except Exception as e:
            logger.error(f'创建品牌创新失败: {e}')
            return {'success': False, 'error': str(e)}

    def update_innovation_status(self, innovation_id: str, status: str, **kwargs) -> Dict[str, Any]:
        try:
            now = datetime.now().isoformat()
            implementation_date = now[:10] if status == 'implemented' else None
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('UPDATE brand_innovation SET status = ?, implementation_date = ?, updated_at = ? WHERE innovation_id = ?',
                                 (status, implementation_date, now, innovation_id))
                    if cursor.rowcount > 0:
                        cursor.execute('INSERT INTO innovation_records (innovation_id, action_type, action_desc, performed_by, created_at) VALUES (?, ?, ?, ?, ?)',
                                     (innovation_id, 'status', f'状态变更为{status}', kwargs.get('performed_by'), now))
                        conn.commit()
                        return {'success': True}
                    return {'success': False, 'error': '创新项目不存在'}
        except Exception as e:
            logger.error(f'更新创新状态失败: {e}')
            return {'success': False, 'error': str(e)}

    def record_innovation_impact(self, innovation_id: str, impact_analysis: str,
                                 roi: float = 0, **kwargs) -> Dict[str, Any]:
        try:
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('UPDATE brand_innovation SET impact_analysis = ?, roi = ?, updated_at = ? WHERE innovation_id = ?',
                                 (impact_analysis, roi, now, innovation_id))
                    if cursor.rowcount > 0:
                        cursor.execute('INSERT INTO innovation_records (innovation_id, action_type, action_desc, performed_by, created_at) VALUES (?, ?, ?, ?, ?)',
                                     (innovation_id, 'impact', f'记录创新影响 ROI:{roi}', kwargs.get('performed_by'), now))
                        conn.commit()
                        return {'success': True}
                    return {'success': False, 'error': '创新项目不存在'}
        except Exception as e:
            logger.error(f'记录创新影响失败: {e}')
            return {'success': False, 'error': str(e)}

    def list_innovations(self, brand_name: str = None, education_type: str = None,
                         innovation_type: str = None, status: str = None,
                         page: int = 1, page_size: int = 20) -> Dict[str, Any]:
        try:
            with self._get_connection() as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                query = 'SELECT * FROM brand_innovation WHERE 1=1'
                params = []
                if brand_name:
                    query += ' AND brand_name = ?'
                    params.append(brand_name)
                if education_type:
                    query += ' AND education_type = ?'
                    params.append(education_type)
                if innovation_type:
                    query += ' AND innovation_type = ?'
                    params.append(innovation_type)
                if status:
                    query += ' AND status = ?'
                    params.append(status)
                cursor.execute(f'SELECT COUNT(*) as cnt FROM ({query})', params)
                total = cursor.fetchone()['cnt']
                query += ' ORDER BY created_at DESC LIMIT ? OFFSET ?'
                params.extend([page_size, (page - 1) * page_size])
                cursor.execute(query, params)
                innovations = [dict(i) for i in cursor.fetchall()]
                return {'success': True, 'innovations': innovations, 'total': total, 'page': page, 'page_size': page_size}
        except Exception as e:
            logger.error(f'获取创新列表失败: {e}')
            return {'success': False, 'error': str(e)}

    # ========== 品牌国际化 ==========

    def create_internationalization(self, brand_name: str, education_type: str,
                                    strategy: str, target_market: str, **kwargs) -> Dict[str, Any]:
        try:
            internationalization_id = f"bint_{uuid.uuid4().hex[:12]}"
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('''
                        INSERT INTO brand_internationalization (
                            internationalization_id, brand_name, education_type,
                            strategy, target_market, country_region,
                            partnership, certification, localization_plan,
                            timeline, budget, status, created_at, updated_at
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'planning', ?, ?)
                    ''', (internationalization_id, brand_name, education_type, strategy,
                          target_market, kwargs.get('country_region'),
                          kwargs.get('partnership'), kwargs.get('certification'),
                          kwargs.get('localization_plan'), kwargs.get('timeline'),
                          kwargs.get('budget', 0), now, now))
                    cursor.execute('INSERT INTO internationalization_records (internationalization_id, action_type, action_desc, performed_by, created_at) VALUES (?, ?, ?, ?, ?)',
                                 (internationalization_id, 'create', '创建国际化计划', kwargs.get('performed_by'), now))
                    conn.commit()
                    logger.info(f'创建品牌国际化: {brand_name} - {target_market} ({internationalization_id})')
                    return {'success': True, 'internationalization_id': internationalization_id}
        except Exception as e:
            logger.error(f'创建品牌国际化失败: {e}')
            return {'success': False, 'error': str(e)}

    def update_internationalization(self, internationalization_id: str, **kwargs) -> Dict[str, Any]:
        try:
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    update_fields = []
                    params = []
                    if 'strategy' in kwargs:
                        update_fields.append('strategy = ?')
                        params.append(kwargs['strategy'])
                    if 'target_market' in kwargs:
                        update_fields.append('target_market = ?')
                        params.append(kwargs['target_market'])
                    if 'country_region' in kwargs:
                        update_fields.append('country_region = ?')
                        params.append(kwargs['country_region'])
                    if 'partnership' in kwargs:
                        update_fields.append('partnership = ?')
                        params.append(kwargs['partnership'])
                    if 'certification' in kwargs:
                        update_fields.append('certification = ?')
                        params.append(kwargs['certification'])
                    if 'localization_plan' in kwargs:
                        update_fields.append('localization_plan = ?')
                        params.append(kwargs['localization_plan'])
                    if 'timeline' in kwargs:
                        update_fields.append('timeline = ?')
                        params.append(kwargs['timeline'])
                    if 'budget' in kwargs:
                        update_fields.append('budget = ?')
                        params.append(kwargs['budget'])
                    if 'status' in kwargs:
                        update_fields.append('status = ?')
                        params.append(kwargs['status'])
                    update_fields.append('updated_at = ?')
                    params.append(now)
                    params.append(internationalization_id)
                    cursor.execute(f'UPDATE brand_internationalization SET {", ".join(update_fields)} WHERE internationalization_id = ?', params)
                    if cursor.rowcount > 0:
                        cursor.execute('INSERT INTO internationalization_records (internationalization_id, action_type, action_desc, performed_by, created_at) VALUES (?, ?, ?, ?, ?)',
                                     (internationalization_id, 'update', '更新国际化计划', kwargs.get('performed_by'), now))
                        conn.commit()
                        return {'success': True}
                    return {'success': False, 'error': '国际化计划不存在'}
        except Exception as e:
            logger.error(f'更新国际化计划失败: {e}')
            return {'success': False, 'error': str(e)}

    def get_internationalization(self, internationalization_id: str) -> Dict[str, Any]:
        try:
            with self._get_connection() as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                cursor.execute('SELECT * FROM brand_internationalization WHERE internationalization_id = ?', (internationalization_id,))
                internationalization = cursor.fetchone()
                if internationalization:
                    return {'success': True, 'internationalization': dict(internationalization)}
                return {'success': False, 'error': '国际化计划不存在'}
        except Exception as e:
            logger.error(f'获取国际化计划失败: {e}')
            return {'success': False, 'error': str(e)}

    def list_internationalizations(self, brand_name: str = None, education_type: str = None,
                                   strategy: str = None, status: str = None,
                                   page: int = 1, page_size: int = 20) -> Dict[str, Any]:
        try:
            with self._get_connection() as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                query = 'SELECT * FROM brand_internationalization WHERE 1=1'
                params = []
                if brand_name:
                    query += ' AND brand_name = ?'
                    params.append(brand_name)
                if education_type:
                    query += ' AND education_type = ?'
                    params.append(education_type)
                if strategy:
                    query += ' AND strategy = ?'
                    params.append(strategy)
                if status:
                    query += ' AND status = ?'
                    params.append(status)
                cursor.execute(f'SELECT COUNT(*) as cnt FROM ({query})', params)
                total = cursor.fetchone()['cnt']
                query += ' ORDER BY created_at DESC LIMIT ? OFFSET ?'
                params.extend([page_size, (page - 1) * page_size])
                cursor.execute(query, params)
                internationalizations = [dict(i) for i in cursor.fetchall()]
                return {'success': True, 'internationalizations': internationalizations, 'total': total, 'page': page, 'page_size': page_size}
        except Exception as e:
            logger.error(f'获取国际化列表失败: {e}')
            return {'success': False, 'error': str(e)}

    # ========== 统计 ==========

    def get_brand_statistics(self, brand_name: str = None, education_type: str = None) -> Dict[str, Any]:
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                stats = {}
                tables = [
                    ('brand_positioning', 'positioning_count'),
                    ('brand_image', 'image_count'),
                    ('brand_communication', 'communication_count'),
                    ('brand_promotion', 'promotion_count'),
                    ('brand_maintenance', 'maintenance_count'),
                    ('brand_assessment', 'assessment_count'),
                    ('brand_innovation', 'innovation_count'),
                    ('brand_internationalization', 'internationalization_count')
                ]
                for table, field in tables:
                    query = f'SELECT COUNT(*) FROM {table} WHERE 1=1'
                    params = []
                    if brand_name:
                        query += ' AND brand_name = ?'
                        params.append(brand_name)
                    if education_type:
                        query += ' AND education_type = ?'
                        params.append(education_type)
                    cursor.execute(query, params)
                    stats[field] = cursor.fetchone()[0]
                cursor.execute('''
                    SELECT AVG(score) as avg_score, MIN(score) as min_score, MAX(score) as max_score
                    FROM brand_assessment WHERE status = 'completed'
                    ''' + (' AND brand_name = ?' if brand_name else '') + (' AND education_type = ?' if education_type else ''),
                    tuple(filter(None, [brand_name, education_type])))
                score_stats = cursor.fetchone()
                stats['avg_assessment_score'] = round(score_stats[0], 2) if score_stats[0] else 0
                stats['min_assessment_score'] = score_stats[1] or 0
                stats['max_assessment_score'] = score_stats[2] or 0
                cursor.execute('''
                    SELECT SUM(budget) as total_budget, SUM(actual_cost) as total_cost,
                           SUM(expected_conversion) as total_expected_conversion,
                           SUM(actual_conversion) as total_actual_conversion
                    FROM brand_promotion WHERE status = 'ended'
                    ''' + (' AND brand_name = ?' if brand_name else '') + (' AND education_type = ?' if education_type else ''),
                    tuple(filter(None, [brand_name, education_type])))
                promotion_stats = cursor.fetchone()
                stats['total_promotion_budget'] = promotion_stats[0] or 0
                stats['total_promotion_cost'] = promotion_stats[1] or 0
                stats['total_expected_conversion'] = promotion_stats[2] or 0
                stats['total_actual_conversion'] = promotion_stats[3] or 0
                return {'success': True, 'statistics': stats}
        except Exception as e:
            logger.error(f'获取品牌统计失败: {e}')
            return {'success': False, 'error': str(e)}