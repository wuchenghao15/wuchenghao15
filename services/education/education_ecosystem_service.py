from core.db_path import get_db_path as _mtscos_get_db_path
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
""" MTSCOS 教育生态系统服务 (v15.22.0) ==================================== 提供生态合作伙伴管理、资源共享、服务集成、数据互通、标准规范、 价值共创、风险防控和可持续发展等综合管理服务。  核心能力： 1. 生态合作伙伴 - 合作伙伴管理、关系维护、准入审核、合作协议 2. 生态资源共享 - 资源注册、权限管理、共享记录、资源检索 3. 生态服务集成 - 服务注册、服务调用、服务监控、服务评价 4. 生态数据互通 - 数据交换、数据标准、数据映射、数据质量、数据安全 5. 生态标准规范 - 标准制定、标准发布、标准认证、合规检查 6. 生态价值共创 - 价值评估、贡献记录、收益分配、合作共赢 7. 生态风险防控 - 风险识别、风险评估、风险预警、风险处置 8. 生态可持续发展 - 可持续评估、指标监控、改进措施、报告生成 9. 生态监控预警 - 监控数据采集、预警规则、预警触发、历史记录 10. 生态统计分析 - 综合统计报表  差异化支持： - 成人教育 - K12教育 """
import os
import json
import uuid
import sqlite3
import logging
import threading
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Tuple

DATABASE_PATH = _mtscos_get_db_path('app.db')

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    handlers=[
        logging.FileHandler(
            os.path.join(os.path.dirname(os.path.abspath(__file__)), 'education_ecosystem_service.log'),
            encoding='utf-8'
        ),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger('EducationEcosystem')


# ========== 生态配置 ==========

PARTNER_TYPES = {
    'education': {'name': '教育机构', 'sub_types': ['高校', '职业院校', '培训机构', '幼儿园', '中小学']},
    'enterprise': {'name': '企业', 'sub_types': ['教育科技', '互联网', '金融', '制造业', '服务业']},
    'government': {'name': '政府', 'sub_types': ['教育局', '人社局', '发改委', '科技局']},
    'research': {'name': '科研机构', 'sub_types': ['研究院', '实验室', '智库', '研究所']},
    'social': {'name': '社会组织', 'sub_types': ['基金会', '协会', '公益组织', '社区']},
    'international': {'name': '国际组织', 'sub_types': ['联合国机构', '国际教育组织', '跨国企业']},
    'media': {'name': '媒体', 'sub_types': ['新闻媒体', '教育媒体', '自媒体']},
    'finance': {'name': '金融机构', 'sub_types': ['银行', '保险', '投资机构', '基金']}
}

RESOURCE_TYPES = {
    'course': {'name': '课程资源', 'formats': ['视频', '文档', 'PPT', 'MOOC']},
    'teaching': {'name': '教学资源', 'formats': ['教案', '课件', '题库', '教具']},
    'research': {'name': '科研资源', 'formats': ['论文', '专利', '数据', '设备']},
    'human': {'name': '人力资源', 'formats': ['教师', '专家', '顾问', '导师']},
    'equipment': {'name': '设备资源', 'formats': ['实验设备', '教学仪器', '硬件设施']},
    'data': {'name': '数据资源', 'formats': ['数据集', 'API', '数据库', '报表']},
    'funding': {'name': '资金资源', 'formats': ['项目资金', '奖学金', '投资', '赞助']},
    'brand': {'name': '品牌资源', 'formats': ['品牌授权', '认证标识', '知识产权']}
}

SERVICE_TYPES = {
    'teaching': {'name': '教学服务', 'features': ['在线授课', '辅导答疑', '作业批改']},
    'research': {'name': '科研服务', 'features': ['课题申报', '论文发表', '成果转化']},
    'management': {'name': '管理服务', 'features': ['教务管理', '学生管理', '财务管理']},
    'consulting': {'name': '咨询服务', 'features': ['教育规划', '职业指导', '企业培训']},
    'technology': {'name': '技术服务', 'features': ['平台开发', '系统集成', '运维支持']},
    'training': {'name': '培训服务', 'features': ['技能培训', '资格认证', '继续教育']},
    'assessment': {'name': '评估服务', 'features': ['教学评估', '质量认证', '绩效评价']},
    'certification': {'name': '认证服务', 'features': ['学历认证', '技能认证', '资质认证']}
}

DATA_TYPES = {
    'student': {'name': '学生数据', 'fields': ['学籍信息', '成绩', '行为数据', '画像']},
    'teacher': {'name': '教师数据', 'fields': ['资质信息', '教学记录', '评价数据']},
    'teaching': {'name': '教学数据', 'fields': ['课程数据', '课堂数据', '互动数据']},
    'research': {'name': '科研数据', 'fields': ['项目数据', '成果数据', '经费数据']},
    'management': {'name': '管理数据', 'fields': ['行政数据', '人事数据', '资产数据']},
    'financial': {'name': '财务数据', 'fields': ['收入数据', '支出数据', '预算数据']},
    'operation': {'name': '运营数据', 'fields': ['流量数据', '用户数据', '服务数据']},
    'external': {'name': '外部数据', 'fields': ['行业数据', '政策数据', '市场数据']}
}

STANDARD_TYPES = {
    'course': {'name': '课程标准', 'scope': ['课程设计', '内容要求', '考核标准']},
    'teaching': {'name': '教学标准', 'scope': ['教学方法', '教学流程', '教学质量']},
    'quality': {'name': '质量标准', 'scope': ['质量体系', '评估指标', '认证标准']},
    'data': {'name': '数据标准', 'scope': ['数据格式', '数据接口', '数据安全']},
    'technology': {'name': '技术标准', 'scope': ['技术架构', '开发规范', '运维标准']},
    'service': {'name': '服务标准', 'scope': ['服务流程', '服务质量', '服务承诺']},
    'security': {'name': '安全标准', 'scope': ['信息安全', '网络安全', '数据隐私']},
    'management': {'name': '管理标准', 'scope': ['管理制度', '工作流程', '绩效考核']}
}

VALUE_MODELS = {
    'knowledge': {'name': '知识创造', 'indicators': ['论文发表', '专利申请', '知识产出']},
    'ability': {'name': '能力培养', 'indicators': ['技能提升', '证书获取', '就业质量']},
    'innovation': {'name': '创新驱动', 'indicators': ['技术创新', '模式创新', '产品创新']},
    'social': {'name': '社会服务', 'indicators': ['公益活动', '社区服务', '扶贫助困']},
    'culture': {'name': '文化传承', 'indicators': ['文化保护', '非遗传承', '文化传播']},
    'international': {'name': '国际交流', 'indicators': ['海外合作', '留学项目', '国际认证']},
    'industry': {'name': '产业发展', 'indicators': ['产学研合作', '成果转化', '产业升级']},
    'talent': {'name': '人才输出', 'indicators': ['毕业生就业', '人才流动', '行业贡献']}
}

RISK_TYPES = {
    'policy': {'name': '政策风险', 'severity': ['低', '中', '高', '严重']},
    'market': {'name': '市场风险', 'severity': ['低', '中', '高', '严重']},
    'technology': {'name': '技术风险', 'severity': ['低', '中', '高', '严重']},
    'financial': {'name': '财务风险', 'severity': ['低', '中', '高', '严重']},
    'operation': {'name': '运营风险', 'severity': ['低', '中', '高', '严重']},
    'compliance': {'name': '合规风险', 'severity': ['低', '中', '高', '严重']},
    'security': {'name': '安全风险', 'severity': ['低', '中', '高', '严重']},
    'reputation': {'name': '声誉风险', 'severity': ['低', '中', '高', '严重']}
}

SUSTAINABILITY_FACTORS = {
    'resource': {'name': '资源节约', 'metrics': ['能耗', '水耗', '材料利用率']},
    'environment': {'name': '环境友好', 'metrics': ['碳排放', '废弃物处理', '绿色认证']},
    'social': {'name': '社会责任', 'metrics': ['公益投入', '就业贡献', '社区服务']},
    'economic': {'name': '经济可持续', 'metrics': ['盈利能力', '成本控制', '投资回报']},
    'innovation': {'name': '创新驱动', 'metrics': ['研发投入', '专利数量', '技术转化']},
    'talent': {'name': '人才培养', 'metrics': ['师资建设', '人才储备', '员工发展']},
    'culture': {'name': '文化传承', 'metrics': ['文化保护', '非遗传承', '文化传播']},
    'institution': {'name': '制度保障', 'metrics': ['治理结构', '合规体系', '风险管控']}
}


class EducationEcosystemService:
    """教育生态系统服务"""

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

                cursor.execute(''' CREATE TABLE IF NOT EXISTS ecosystem_partners ( partner_id TEXT PRIMARY KEY, partner_name TEXT NOT NULL, partner_type TEXT NOT NULL, sub_type TEXT, education_type TEXT, contact_person TEXT, contact_phone TEXT, contact_email TEXT, address TEXT, description TEXT, logo_url TEXT, status TEXT DEFAULT 'pending', join_date TEXT, expire_date TEXT, created_at TEXT, updated_at TEXT ) ''')

                cursor.execute(''' CREATE TABLE IF NOT EXISTS partner_relations ( relation_id TEXT PRIMARY KEY, partner_id TEXT NOT NULL, related_partner_id TEXT NOT NULL, relation_type TEXT, education_type TEXT, description TEXT, start_date TEXT, end_date TEXT, status TEXT DEFAULT 'active', created_at TEXT ) ''')

                cursor.execute(''' CREATE TABLE IF NOT EXISTS shared_resources ( resource_id TEXT PRIMARY KEY, resource_name TEXT NOT NULL, resource_type TEXT NOT NULL, format TEXT, education_type TEXT, owner_partner_id TEXT, owner_name TEXT, description TEXT, access_level TEXT DEFAULT 'public', tags TEXT, file_url TEXT, size INTEGER, download_count INTEGER DEFAULT 0, view_count INTEGER DEFAULT 0, status TEXT DEFAULT 'available', created_at TEXT, updated_at TEXT ) ''')

                cursor.execute(''' CREATE TABLE IF NOT EXISTS resource_access ( access_id TEXT PRIMARY KEY, resource_id TEXT NOT NULL, partner_id TEXT NOT NULL, access_type TEXT, granted_at TEXT, expires_at TEXT, status TEXT DEFAULT 'active', created_at TEXT ) ''')

                cursor.execute(''' CREATE TABLE IF NOT EXISTS integrated_services ( service_id TEXT PRIMARY KEY, service_name TEXT NOT NULL, service_type TEXT NOT NULL, education_type TEXT, provider_partner_id TEXT, provider_name TEXT, description TEXT, endpoint_url TEXT, api_key TEXT, status TEXT DEFAULT 'available', call_count INTEGER DEFAULT 0, avg_response_time REAL DEFAULT 0, created_at TEXT, updated_at TEXT ) ''')

                cursor.execute(''' CREATE TABLE IF NOT EXISTS service_registry ( registry_id TEXT PRIMARY KEY, service_id TEXT NOT NULL, partner_id TEXT NOT NULL, registered_at TEXT, status TEXT DEFAULT 'registered', created_at TEXT ) ''')

                cursor.execute(''' CREATE TABLE IF NOT EXISTS data_interchange ( interchange_id TEXT PRIMARY KEY, data_type TEXT NOT NULL, education_type TEXT, source_partner_id TEXT, target_partner_id TEXT, data_format TEXT, data_size INTEGER, transfer_status TEXT DEFAULT 'pending', transfer_time TEXT, created_at TEXT ) ''')

                cursor.execute(''' CREATE TABLE IF NOT EXISTS data_standards ( standard_id TEXT PRIMARY KEY, standard_name TEXT NOT NULL, data_type TEXT, education_type TEXT, format_spec TEXT, version TEXT DEFAULT '1.0', status TEXT DEFAULT 'active', created_at TEXT, updated_at TEXT ) ''')

                cursor.execute(''' CREATE TABLE IF NOT EXISTS ecosystem_standards ( standard_id TEXT PRIMARY KEY, standard_name TEXT NOT NULL, standard_type TEXT NOT NULL, education_type TEXT, description TEXT, scope TEXT, version TEXT DEFAULT '1.0', status TEXT DEFAULT 'draft', published_at TEXT, created_at TEXT, updated_at TEXT ) ''')

                cursor.execute(''' CREATE TABLE IF NOT EXISTS standard_compliance ( compliance_id TEXT PRIMARY KEY, standard_id TEXT NOT NULL, partner_id TEXT NOT NULL, education_type TEXT, compliance_status TEXT DEFAULT 'pending', audit_date TEXT, audit_result TEXT, created_at TEXT, updated_at TEXT ) ''')

                cursor.execute(''' CREATE TABLE IF NOT EXISTS value_co_creation ( project_id TEXT PRIMARY KEY, project_name TEXT NOT NULL, value_model TEXT NOT NULL, education_type TEXT, description TEXT, status TEXT DEFAULT 'active', created_at TEXT, updated_at TEXT ) ''')

                cursor.execute(''' CREATE TABLE IF NOT EXISTS value_contributions ( contribution_id TEXT PRIMARY KEY, project_id TEXT NOT NULL, partner_id TEXT NOT NULL, education_type TEXT, contribution_type TEXT, amount REAL, description TEXT, created_at TEXT ) ''')

                cursor.execute(''' CREATE TABLE IF NOT EXISTS risk_management ( risk_id TEXT PRIMARY KEY, risk_type TEXT NOT NULL, education_type TEXT, title TEXT NOT NULL, description TEXT, severity TEXT DEFAULT 'medium', probability REAL DEFAULT 0.5, impact REAL DEFAULT 0.5, status TEXT DEFAULT 'identified', created_at TEXT, updated_at TEXT ) ''')

                cursor.execute(''' CREATE TABLE IF NOT EXISTS risk_assessments ( assessment_id TEXT PRIMARY KEY, risk_id TEXT NOT NULL, assessor_id INTEGER, assessor_name TEXT, assessment_date TEXT, severity TEXT, probability REAL, impact REAL, risk_score REAL, recommendations TEXT, created_at TEXT ) ''')

                cursor.execute(''' CREATE TABLE IF NOT EXISTS sustainability ( sustainability_id TEXT PRIMARY KEY, partner_id TEXT NOT NULL, education_type TEXT, overall_score REAL DEFAULT 0, status TEXT DEFAULT 'evaluating', last_evaluation TEXT, created_at TEXT, updated_at TEXT ) ''')

                cursor.execute(''' CREATE TABLE IF NOT EXISTS sustainability_metrics ( metric_id TEXT PRIMARY KEY, sustainability_id TEXT NOT NULL, factor_type TEXT, metric_name TEXT, value REAL, target_value REAL, unit TEXT, created_at TEXT ) ''')

                cursor.execute(''' CREATE TABLE IF NOT EXISTS ecosystem_monitoring ( monitor_id TEXT PRIMARY KEY, partner_id TEXT, education_type TEXT, monitor_type TEXT, threshold REAL, status TEXT DEFAULT 'active', created_at TEXT, updated_at TEXT ) ''')

                cursor.execute(''' CREATE TABLE IF NOT EXISTS monitoring_data ( data_id TEXT PRIMARY KEY, monitor_id TEXT NOT NULL, value REAL, recorded_at TEXT, created_at TEXT ) ''')

                cursor.execute(''' CREATE TABLE IF NOT EXISTS ecosystem_alerts ( alert_id TEXT PRIMARY KEY, monitor_id TEXT NOT NULL, partner_id TEXT, education_type TEXT, alert_type TEXT, severity TEXT DEFAULT 'warning', message TEXT, status TEXT DEFAULT 'active', created_at TEXT, resolved_at TEXT ) ''')

                cursor.execute(''' CREATE TABLE IF NOT EXISTS alert_history ( history_id TEXT PRIMARY KEY, alert_id TEXT NOT NULL, action TEXT, actor_id INTEGER, actor_name TEXT, action_time TEXT, notes TEXT, created_at TEXT ) ''')

                conn.commit()
                logger.info('教育生态系统服务数据库初始化完成')
        except Exception as e:
            logger.error(f'数据库初始化失败: {e}')

    # ========== 生态合作伙伴 ==========

    def register_partner(self, partner_name: str, partner_type: str,
                         **kwargs) -> Dict[str, Any]:
        try:
            partner_id = f"ep_{uuid.uuid4().hex[:12]}"
            now = datetime.now().isoformat()
            config = PARTNER_TYPES.get(partner_type, {})
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute(''' INSERT INTO ecosystem_partners ( partner_id, partner_name, partner_type, sub_type, education_type, contact_person, contact_phone, contact_email, address, description, logo_url, status, join_date, created_at, updated_at ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'pending', ?, ?, ?) ''', (partner_id, partner_name, partner_type,
                          kwargs.get('sub_type', config.get('sub_types', [''])[0]),
                          kwargs.get('education_type'), kwargs.get('contact_person'),
                          kwargs.get('contact_phone'), kwargs.get('contact_email'),
                          kwargs.get('address'), kwargs.get('description'),
                          kwargs.get('logo_url'), now[:10], now, now))
                    conn.commit()
                    logger.info(f'注册合作伙伴: {partner_name} ({partner_id})')
                    return {'success': True, 'partner_id': partner_id}
        except Exception as e:
            logger.error(f'注册合作伙伴失败: {e}')
            return {'success': False, 'error': str(e)}

    def approve_partner(self, partner_id: str, approved: bool,
                        **kwargs) -> Dict[str, Any]:
        try:
            now = datetime.now().isoformat()
            status = 'approved' if approved else 'rejected'
            expire_date = (datetime.now() + timedelta(days=365)).isoformat()[:10] if approved else None
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute(''' UPDATE ecosystem_partners SET status = ?, expire_date = ?, updated_at = ? WHERE partner_id = ? AND status = 'pending' ''', (status, expire_date, now, partner_id))
                    if cursor.rowcount > 0:
                        conn.commit()
                        return {'success': True, 'status': status}
                    return {'success': False, 'error': '合作伙伴状态不允许审核'}
        except Exception as e:
            logger.error(f'审核合作伙伴失败: {e}')
            return {'success': False, 'error': str(e)}

    def establish_relation(self, partner_id: str, related_partner_id: str,
                           relation_type: str, **kwargs) -> Dict[str, Any]:
        try:
            relation_id = f"pr_{uuid.uuid4().hex[:12]}"
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute(''' INSERT INTO partner_relations ( relation_id, partner_id, related_partner_id, relation_type, education_type, description, start_date, end_date, status, created_at ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, 'active', ?) ''', (relation_id, partner_id, related_partner_id, relation_type,
                          kwargs.get('education_type'), kwargs.get('description'),
                          now[:10], kwargs.get('end_date'), now))
                    conn.commit()
                    logger.info(f'建立合作伙伴关系: {partner_id} <-> {related_partner_id}')
                    return {'success': True, 'relation_id': relation_id}
        except Exception as e:
            logger.error(f'建立合作伙伴关系失败: {e}')
            return {'success': False, 'error': str(e)}

    def list_partners(self, partner_type: str = None, education_type: str = None,
                      status: str = None, page: int = 1, page_size: int = 20) -> Dict[str, Any]:
        try:
            with self._get_connection() as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                query = 'SELECT * FROM ecosystem_partners WHERE 1=1'
                params = []
                if partner_type:
                    query += ' AND partner_type = ?'
                    params.append(partner_type)
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
                partners = [dict(p) for p in cursor.fetchall()]
                return {'success': True, 'partners': partners, 'total': total, 'page': page, 'page_size': page_size}
        except Exception as e:
            logger.error(f'获取合作伙伴列表失败: {e}')
            return {'success': False, 'error': str(e)}

    # ========== 资源共享 ==========

    def register_resource(self, resource_name: str, resource_type: str,
                          owner_partner_id: str, **kwargs) -> Dict[str, Any]:
        try:
            resource_id = f"sr_{uuid.uuid4().hex[:12]}"
            now = datetime.now().isoformat()
            config = RESOURCE_TYPES.get(resource_type, {})
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute(''' INSERT INTO shared_resources ( resource_id, resource_name, resource_type, format, education_type, owner_partner_id, owner_name, description, access_level, tags, file_url, size, download_count, view_count, status, created_at, updated_at ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 0, 0, 'available', ?, ?) ''', (resource_id, resource_name, resource_type,
                          kwargs.get('format', config.get('formats', [''])[0]),
                          kwargs.get('education_type'), owner_partner_id,
                          kwargs.get('owner_name'), kwargs.get('description'),
                          kwargs.get('access_level', 'public'), kwargs.get('tags'),
                          kwargs.get('file_url'), kwargs.get('size', 0), now, now))
                    conn.commit()
                    logger.info(f'注册共享资源: {resource_name} ({resource_id})')
                    return {'success': True, 'resource_id': resource_id}
        except Exception as e:
            logger.error(f'注册共享资源失败: {e}')
            return {'success': False, 'error': str(e)}

    def grant_resource_access(self, resource_id: str, partner_id: str,
                              access_type: str, **kwargs) -> Dict[str, Any]:
        try:
            access_id = f"ra_{uuid.uuid4().hex[:12]}"
            now = datetime.now().isoformat()
            expires_at = (datetime.now() + timedelta(days=kwargs.get('duration_days', 30))).isoformat()[:10]
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute(''' INSERT INTO resource_access ( access_id, resource_id, partner_id, access_type, granted_at, expires_at, status, created_at ) VALUES (?, ?, ?, ?, ?, ?, 'active', ?) ''', (access_id, resource_id, partner_id, access_type, now[:10], expires_at, now))
                    conn.commit()
                    return {'success': True, 'access_id': access_id}
        except Exception as e:
            logger.error(f'授权资源访问失败: {e}')
            return {'success': False, 'error': str(e)}

    def record_resource_usage(self, resource_id: str, usage_type: str = 'view') -> Dict[str, Any]:
        try:
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    if usage_type == 'download':
                        cursor.execute('UPDATE shared_resources SET download_count = download_count + 1, updated_at = ? WHERE resource_id = ?', (now, resource_id))
                    else:
                        cursor.execute('UPDATE shared_resources SET view_count = view_count + 1, updated_at = ? WHERE resource_id = ?', (now, resource_id))
                    if cursor.rowcount > 0:
                        conn.commit()
                        return {'success': True}
                    return {'success': False, 'error': '资源不存在'}
        except Exception as e:
            logger.error(f'记录资源使用失败: {e}')
            return {'success': False, 'error': str(e)}

    def search_resources(self, keyword: str = None, resource_type: str = None,
                         education_type: str = None, access_level: str = None,
                         page: int = 1, page_size: int = 20) -> Dict[str, Any]:
        try:
            with self._get_connection() as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                query = 'SELECT * FROM shared_resources WHERE status = "available"'
                params = []
                if keyword:
                    query += ' AND (resource_name LIKE ? OR description LIKE ?)'
                    params.extend([f'%{keyword}%', f'%{keyword}%'])
                if resource_type:
                    query += ' AND resource_type = ?'
                    params.append(resource_type)
                if education_type:
                    query += ' AND education_type = ?'
                    params.append(education_type)
                if access_level:
                    query += ' AND access_level = ?'
                    params.append(access_level)
                cursor.execute(f'SELECT COUNT(*) as cnt FROM ({query})', params)
                total = cursor.fetchone()['cnt']
                query += ' ORDER BY created_at DESC LIMIT ? OFFSET ?'
                params.extend([page_size, (page - 1) * page_size])
                cursor.execute(query, params)
                resources = [dict(r) for r in cursor.fetchall()]
                return {'success': True, 'resources': resources, 'total': total, 'page': page, 'page_size': page_size}
        except Exception as e:
            logger.error(f'搜索资源失败: {e}')
            return {'success': False, 'error': str(e)}

    # ========== 服务集成 ==========

    def register_service(self, service_name: str, service_type: str,
                         provider_partner_id: str, **kwargs) -> Dict[str, Any]:
        try:
            service_id = f"is_{uuid.uuid4().hex[:12]}"
            now = datetime.now().isoformat()
            config = SERVICE_TYPES.get(service_type, {})
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute(''' INSERT INTO integrated_services ( service_id, service_name, service_type, education_type, provider_partner_id, provider_name, description, endpoint_url, api_key, status, call_count, avg_response_time, created_at, updated_at ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, 'available', 0, 0, ?, ?) ''', (service_id, service_name, service_type, kwargs.get('education_type'),
                          provider_partner_id, kwargs.get('provider_name'),
                          kwargs.get('description'), kwargs.get('endpoint_url'),
                          kwargs.get('api_key'), now, now))
                    conn.commit()
                    logger.info(f'注册集成服务: {service_name} ({service_id})')
                    return {'success': True, 'service_id': service_id}
        except Exception as e:
            logger.error(f'注册集成服务失败: {e}')
            return {'success': False, 'error': str(e)}

    def subscribe_service(self, service_id: str, partner_id: str) -> Dict[str, Any]:
        try:
            registry_id = f"sr_{uuid.uuid4().hex[:12]}"
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('SELECT status FROM integrated_services WHERE service_id = ?', (service_id,))
                    service = cursor.fetchone()
                    if not service:
                        return {'success': False, 'error': '服务不存在'}
                    if service[0] != 'available':
                        return {'success': False, 'error': '服务不可用'}
                    cursor.execute('INSERT OR IGNORE INTO service_registry (registry_id, service_id, partner_id, registered_at, status, created_at) VALUES (?, ?, ?, ?, "registered", ?)',
                                 (registry_id, service_id, partner_id, now[:10], now))
                    if cursor.rowcount > 0:
                        conn.commit()
                        return {'success': True, 'registry_id': registry_id}
                    return {'success': False, 'error': '已订阅该服务'}
        except Exception as e:
            logger.error(f'订阅服务失败: {e}')
            return {'success': False, 'error': str(e)}

    def record_service_call(self, service_id: str, response_time: float = 0) -> Dict[str, Any]:
        try:
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('SELECT call_count, avg_response_time FROM integrated_services WHERE service_id = ?',
                    (service_id,))
                    service = cursor.fetchone()
                    if not service:
                        return {'success': False, 'error': '服务不存在'}
                    new_count = service[0] + 1
                    new_avg = ((
                    service[1] * service[0]) + response_time) / new_count if service[0] > 0 else response_time
                    cursor.execute('UPDATE integrated_services SET call_count = ?, avg_response_time = ?, updated_at = ? WHERE service_id = ?',
                                 (new_count, round(new_avg, 2), now, service_id))
                    conn.commit()
                    return {'success': True, 'call_count': new_count, 'avg_response_time': round(new_avg, 2)}
        except Exception as e:
            logger.error(f'记录服务调用失败: {e}')
            return {'success': False, 'error': str(e)}

    def get_service_stats(self, service_id: str = None, education_type: str = None) -> Dict[str, Any]:
        try:
            with self._get_connection() as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                query = 'SELECT service_id, service_name, service_type, call_count, avg_response_time FROM integrated_services WHERE 1=1'
                params = []
                if service_id:
                    query += ' AND service_id = ?'
                    params.append(service_id)
                if education_type:
                    query += ' AND education_type = ?'
                    params.append(education_type)
                cursor.execute(query, params)
                stats = [dict(s) for s in cursor.fetchall()]
                return {'success': True, 'stats': stats}
        except Exception as e:
            logger.error(f'获取服务统计失败: {e}')
            return {'success': False, 'error': str(e)}

    # ========== 数据互通 ==========

    def initiate_data_transfer(self, data_type: str, source_partner_id: str,
                               target_partner_id: str, **kwargs) -> Dict[str, Any]:
        try:
            interchange_id = f"dt_{uuid.uuid4().hex[:12]}"
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute(''' INSERT INTO data_interchange ( interchange_id, data_type, education_type, source_partner_id, target_partner_id, data_format, data_size, transfer_status, created_at ) VALUES (?, ?, ?, ?, ?, ?, ?, 'pending', ?) ''', (interchange_id, data_type, kwargs.get('education_type'),
                          source_partner_id, target_partner_id,
                          kwargs.get('data_format'), kwargs.get('data_size', 0), now))
                    conn.commit()
                    return {'success': True, 'interchange_id': interchange_id}
        except Exception as e:
            logger.error(f'发起数据传输失败: {e}')
            return {'success': False, 'error': str(e)}

    def update_transfer_status(self, interchange_id: str, status: str,
                               **kwargs) -> Dict[str, Any]:
        try:
            now = datetime.now().isoformat()
            transfer_time = now[:10] if status == 'completed' else None
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute(''' UPDATE data_interchange SET transfer_status = ?, transfer_time = ?, updated_at = ? WHERE interchange_id = ? ''', (status, transfer_time, now, interchange_id))
                    if cursor.rowcount > 0:
                        conn.commit()
                        return {'success': True, 'status': status}
                    return {'success': False, 'error': '传输记录不存在'}
        except Exception as e:
            logger.error(f'更新传输状态失败: {e}')
            return {'success': False, 'error': str(e)}

    def define_data_standard(self, standard_name: str, data_type: str,
                             **kwargs) -> Dict[str, Any]:
        try:
            standard_id = f"ds_{uuid.uuid4().hex[:12]}"
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute(''' INSERT INTO data_standards ( standard_id, standard_name, data_type, education_type, format_spec, version, status, created_at, updated_at ) VALUES (?, ?, ?, ?, ?, ?, 'active', ?, ?) ''', (standard_id, standard_name, data_type, kwargs.get('education_type'),
                          kwargs.get('format_spec'), kwargs.get('version', '1.0'), now, now))
                    conn.commit()
                    return {'success': True, 'standard_id': standard_id}
        except Exception as e:
            logger.error(f'定义数据标准失败: {e}')
            return {'success': False, 'error': str(e)}

    def validate_data_format(self, standard_id: str, data: Dict[str, Any]) -> Dict[str, Any]:
        try:
            with self._get_connection() as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                cursor.execute('SELECT format_spec FROM data_standards WHERE standard_id = ?', (standard_id,))
                standard = cursor.fetchone()
                if not standard:
                    return {'success': False, 'error': '数据标准不存在'}
                spec = json.loads(standard['format_spec']) if standard['format_spec'] else {}
                required_fields = spec.get('required', [])
                missing_fields = [f for f in required_fields if f not in data]
                if missing_fields:
                    return {'success': False, 'error': f'缺少必填字段: {", ".join(missing_fields)}'}
                return {'success': True, 'validated': True, 'message': '数据格式验证通过'}
        except Exception as e:
            logger.error(f'验证数据格式失败: {e}')
            return {'success': False, 'error': str(e)}

    def get_data_transfer_history(self, source_partner_id: str = None,
                                   target_partner_id: str = None,
                                   education_type: str = None,
                                   page: int = 1, page_size: int = 20) -> Dict[str, Any]:
        try:
            with self._get_connection() as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                query = 'SELECT * FROM data_interchange WHERE 1=1'
                params = []
                if source_partner_id:
                    query += ' AND source_partner_id = ?'
                    params.append(source_partner_id)
                if target_partner_id:
                    query += ' AND target_partner_id = ?'
                    params.append(target_partner_id)
                if education_type:
                    query += ' AND education_type = ?'
                    params.append(education_type)
                cursor.execute(f'SELECT COUNT(*) as cnt FROM ({query})', params)
                total = cursor.fetchone()['cnt']
                query += ' ORDER BY created_at DESC LIMIT ? OFFSET ?'
                params.extend([page_size, (page - 1) * page_size])
                cursor.execute(query, params)
                history = [dict(h) for h in cursor.fetchall()]
                return {'success': True, 'history': history, 'total': total, 'page': page, 'page_size': page_size}
        except Exception as e:
            logger.error(f'获取数据传输历史失败: {e}')
            return {'success': False, 'error': str(e)}

    # ========== 标准规范 ==========

    def create_standard(self, standard_name: str, standard_type: str,
                        **kwargs) -> Dict[str, Any]:
        try:
            standard_id = f"es_{uuid.uuid4().hex[:12]}"
            now = datetime.now().isoformat()
            config = STANDARD_TYPES.get(standard_type, {})
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute(''' INSERT INTO ecosystem_standards ( standard_id, standard_name, standard_type, education_type, description, scope, version, status, created_at, updated_at ) VALUES (?, ?, ?, ?, ?, ?, ?, 'draft', ?, ?) ''', (standard_id, standard_name, standard_type, kwargs.get('education_type'),
                          kwargs.get('description'), kwargs.get('scope', ','.join(config.get('scope', []))),
                          kwargs.get('version', '1.0'), now, now))
                    conn.commit()
                    logger.info(f'创建标准规范: {standard_name} ({standard_id})')
                    return {'success': True, 'standard_id': standard_id}
        except Exception as e:
            logger.error(f'创建标准规范失败: {e}')
            return {'success': False, 'error': str(e)}

    def publish_standard(self, standard_id: str) -> Dict[str, Any]:
        try:
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute(''' UPDATE ecosystem_standards SET status = 'published', published_at = ?, updated_at = ? WHERE standard_id = ? AND status = 'draft' ''', (now[:10], now, standard_id))
                    if cursor.rowcount > 0:
                        conn.commit()
                        return {'success': True, 'status': 'published'}
                    return {'success': False, 'error': '标准状态不允许发布'}
        except Exception as e:
            logger.error(f'发布标准失败: {e}')
            return {'success': False, 'error': str(e)}

    def assess_compliance(self, standard_id: str, partner_id: str,
                          **kwargs) -> Dict[str, Any]:
        try:
            compliance_id = f"sc_{uuid.uuid4().hex[:12]}"
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('SELECT status FROM ecosystem_standards WHERE standard_id = ?', (standard_id,))
                    standard = cursor.fetchone()
                    if not standard or standard[0] != 'published':
                        return {'success': False, 'error': '标准未发布'}
                    cursor.execute(''' INSERT INTO standard_compliance ( compliance_id, standard_id, partner_id, education_type, compliance_status, audit_date, audit_result, created_at, updated_at ) VALUES (?, ?, ?, ?, 'pending', ?, ?, ?, ?) ''', (compliance_id, standard_id, partner_id, kwargs.get('education_type'),
                          now[:10], kwargs.get('audit_result'), now, now))
                    conn.commit()
                    return {'success': True, 'compliance_id': compliance_id}
        except Exception as e:
            logger.error(f'评估合规性失败: {e}')
            return {'success': False, 'error': str(e)}

    def update_compliance_status(self, compliance_id: str, status: str,
                                  **kwargs) -> Dict[str, Any]:
        try:
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute(''' UPDATE standard_compliance SET compliance_status = ?, audit_result = ?, updated_at = ? WHERE compliance_id = ? ''', (status, kwargs.get('audit_result'), now, compliance_id))
                    if cursor.rowcount > 0:
                        conn.commit()
                        return {'success': True, 'status': status}
                    return {'success': False, 'error': '合规记录不存在'}
        except Exception as e:
            logger.error(f'更新合规状态失败: {e}')
            return {'success': False, 'error': str(e)}

    # ========== 价值共创 ==========

    def create_value_project(self, project_name: str, value_model: str,
                             **kwargs) -> Dict[str, Any]:
        try:
            project_id = f"vc_{uuid.uuid4().hex[:12]}"
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute(''' INSERT INTO value_co_creation ( project_id, project_name, value_model, education_type, description, status, created_at, updated_at ) VALUES (?, ?, ?, ?, ?, 'active', ?, ?) ''', (project_id, project_name, value_model, kwargs.get('education_type'),
                          kwargs.get('description'), now, now))
                    conn.commit()
                    logger.info(f'创建价值共创项目: {project_name} ({project_id})')
                    return {'success': True, 'project_id': project_id}
        except Exception as e:
            logger.error(f'创建价值共创项目失败: {e}')
            return {'success': False, 'error': str(e)}

    def record_contribution(self, project_id: str, partner_id: str,
                            contribution_type: str, **kwargs) -> Dict[str, Any]:
        try:
            contribution_id = f"vct_{uuid.uuid4().hex[:12]}"
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('SELECT status FROM value_co_creation WHERE project_id = ?', (project_id,))
                    project = cursor.fetchone()
                    if not project or project[0] != 'active':
                        return {'success': False, 'error': '项目不存在或已结束'}
                    cursor.execute(''' INSERT INTO value_contributions ( contribution_id, project_id, partner_id, education_type, contribution_type, amount, description, created_at ) VALUES (?, ?, ?, ?, ?, ?, ?, ?) ''', (contribution_id, project_id, partner_id, kwargs.get('education_type'),
                          contribution_type, kwargs.get('amount', 0), kwargs.get('description'), now))
                    conn.commit()
                    return {'success': True, 'contribution_id': contribution_id}
        except Exception as e:
            logger.error(f'记录贡献失败: {e}')
            return {'success': False, 'error': str(e)}

    def calculate_value(self, project_id: str) -> Dict[str, Any]:
        try:
            with self._get_connection() as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                cursor.execute('SELECT value_model FROM value_co_creation WHERE project_id = ?', (project_id,))
                project = cursor.fetchone()
                if not project:
                    return {'success': False, 'error': '项目不存在'}
                cursor.execute('SELECT SUM(amount) as total FROM value_contributions WHERE project_id = ?', (project_id,
                ))
                total = cursor.fetchone()['total'] or 0
                cursor.execute('SELECT COUNT( DISTINCT partner_id) as partners FROM value_contributions WHERE project_id = ?', (project_id,))
                partners = cursor.fetchone()['partners'] or 0
                return {'success': True, 'project_id': project_id, 'value_model': project['value_model'],
                        'total_contribution': total, 'participating_partners': partners}
        except Exception as e:
            logger.error(f'计算价值失败: {e}')
            return {'success': False, 'error': str(e)}

    def list_value_projects(self, value_model: str = None, education_type: str = None,
                            status: str = None, page: int = 1, page_size: int = 20) -> Dict[str, Any]:
        try:
            with self._get_connection() as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                query = 'SELECT * FROM value_co_creation WHERE 1=1'
                params = []
                if value_model:
                    query += ' AND value_model = ?'
                    params.append(value_model)
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
                projects = [dict(p) for p in cursor.fetchall()]
                return {'success': True, 'projects': projects, 'total': total, 'page': page, 'page_size': page_size}
        except Exception as e:
            logger.error(f'获取价值项目列表失败: {e}')
            return {'success': False, 'error': str(e)}

    # ========== 风险防控 ==========

    def identify_risk(self, risk_type: str, title: str, **kwargs) -> Dict[str, Any]:
        try:
            risk_id = f"rm_{uuid.uuid4().hex[:12]}"
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute(''' INSERT INTO risk_management ( risk_id, risk_type, education_type, title, description, severity, probability, impact, status, created_at, updated_at ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, 'identified', ?, ?) ''', (risk_id, risk_type, kwargs.get('education_type'), title,
                          kwargs.get('description'), kwargs.get('severity', 'medium'),
                          kwargs.get('probability', 0.5), kwargs.get('impact', 0.5), now, now))
                    conn.commit()
                    logger.info(f'识别风险: {title} ({risk_id})')
                    return {'success': True, 'risk_id': risk_id}
        except Exception as e:
            logger.error(f'识别风险失败: {e}')
            return {'success': False, 'error': str(e)}

    def assess_risk(self, risk_id: str, assessor_id: int, assessor_name: str,
                    **kwargs) -> Dict[str, Any]:
        try:
            assessment_id = f"ra_{uuid.uuid4().hex[:12]}"
            now = datetime.now().isoformat()
            severity = kwargs.get('severity', 'medium')
            probability = kwargs.get('probability', 0.5)
            impact = kwargs.get('impact', 0.5)
            risk_score = probability * impact
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute(''' INSERT INTO risk_assessments ( assessment_id, risk_id, assessor_id, assessor_name, assessment_date, severity, probability, impact, risk_score, recommendations, created_at ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?) ''', (assessment_id, risk_id, assessor_id, assessor_name, now[:10],
                          severity, probability, impact, round(risk_score, 2),
                          kwargs.get('recommendations'), now))
                    cursor.execute(''' UPDATE risk_management SET severity = ?, probability = ?, impact = ?, status = 'assessed', updated_at = ? WHERE risk_id = ? ''', (severity, probability, impact, now, risk_id))
                    conn.commit()
                    return {'success': True, 'assessment_id': assessment_id, 'risk_score': round(risk_score, 2)}
        except Exception as e:
            logger.error(f'评估风险失败: {e}')
            return {'success': False, 'error': str(e)}

    def mitigate_risk(self, risk_id: str, **kwargs) -> Dict[str, Any]:
        try:
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute(''' UPDATE risk_management SET status = 'mitigated', updated_at = ? WHERE risk_id = ? AND status = 'assessed' ''', (now, risk_id))
                    if cursor.rowcount > 0:
                        conn.commit()
                        return {'success': True, 'status': 'mitigated'}
                    return {'success': False, 'error': '风险状态不允许处置'}
        except Exception as e:
            logger.error(f'处置风险失败: {e}')
            return {'success': False, 'error': str(e)}

    def get_risk_dashboard(self, education_type: str = None, risk_type: str = None) -> Dict[str, Any]:
        try:
            with self._get_connection() as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                query = 'SELECT * FROM risk_management WHERE 1=1'
                params = []
                if education_type:
                    query += ' AND education_type = ?'
                    params.append(education_type)
                if risk_type:
                    query += ' AND risk_type = ?'
                    params.append(risk_type)
                cursor.execute(query, params)
                risks = [dict(r) for r in cursor.fetchall()]
                cursor.execute(''' SELECT status, COUNT(*) as count FROM risk_management WHERE 1=1 ''' + (' AND education_type = ?' if education_type else ''), params if education_type else [])
                summary = [{'status': r['status'], 'count': r['count']} for r in cursor.fetchall()]
                return {'success': True, 'risks': risks, 'summary': summary}
        except Exception as e:
            logger.error(f'获取风险面板失败: {e}')
            return {'success': False, 'error': str(e)}

    # ========== 可持续发展 ==========

    def evaluate_sustainability(self, partner_id: str, **kwargs) -> Dict[str, Any]:
        try:
            sustainability_id = f"su_{uuid.uuid4().hex[:12]}"
            now = datetime.now().isoformat()
            overall_score = kwargs.get('overall_score', 0)
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute(''' INSERT INTO sustainability ( sustainability_id, partner_id, education_type, overall_score, status, last_evaluation, created_at, updated_at ) VALUES (?, ?, ?, ?, 'evaluated', ?, ?, ?) ''', (sustainability_id, partner_id, kwargs.get('education_type'),
                          overall_score, now[:10], now, now))
                    metrics = kwargs.get('metrics', [])
                    for metric in metrics:
                        metric_id = f"sm_{uuid.uuid4().hex[:12]}"
                        cursor.execute(''' INSERT INTO sustainability_metrics ( metric_id, sustainability_id, factor_type, metric_name, value, target_value, unit, created_at ) VALUES (?, ?, ?, ?, ?, ?, ?, ?) ''', (metric_id, sustainability_id, metric.get('factor_type'),
                              metric.get('metric_name'), metric.get('value', 0),
                              metric.get('target_value', 0), metric.get('unit', ''), now))
                    conn.commit()
                    return {'success': True, 'sustainability_id': sustainability_id, 'overall_score': overall_score}
        except Exception as e:
            logger.error(f'评估可持续性失败: {e}')
            return {'success': False, 'error': str(e)}

    def update_sustainability_metrics(self, sustainability_id: str,
                                       metrics: List[Dict[str, Any]]) -> Dict[str, Any]:
        try:
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    for metric in metrics:
                        cursor.execute(''' UPDATE sustainability_metrics SET value = ?, target_value = ?, updated_at = ? WHERE sustainability_id = ? AND metric_name = ? ''', (metric.get('value'), metric.get('target_value'), now,
                              sustainability_id, metric.get('metric_name')))
                    conn.commit()
                    return {'success': True}
        except Exception as e:
            logger.error(f'更新可持续性指标失败: {e}')
            return {'success': False, 'error': str(e)}

    def generate_sustainability_report(self, partner_id: str,
                                       education_type: str = None) -> Dict[str, Any]:
        try:
            with self._get_connection() as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                cursor.execute(''' SELECT s.*, p.partner_name FROM sustainability s LEFT JOIN ecosystem_partners p ON s.partner_id = p.partner_id WHERE s.partner_id = ? ''' + (' AND s.education_type = ?' if education_type else ''),
                              (partner_id, education_type) if education_type else (partner_id,))
                sustainability = cursor.fetchone()
                if not sustainability:
                    return {'success': False, 'error': '未找到可持续性评估记录'}
                cursor.execute('SELECT * FROM sustainability_metrics WHERE sustainability_id = ?',
                              (sustainability['sustainability_id'],))
                metrics = [dict(m) for m in cursor.fetchall()]
                report = {
                    'partner_id': partner_id,
                    'partner_name': sustainability['partner_name'],
                    'education_type': sustainability['education_type'],
                    'overall_score': sustainability['overall_score'],
                    'last_evaluation': sustainability['last_evaluation'],
                    'metrics': metrics
                }
                return {'success': True, 'report': report}
        except Exception as e:
            logger.error(f'生成可持续性报告失败: {e}')
            return {'success': False, 'error': str(e)}

    def list_sustainability_records(self, education_type: str = None,
                                     page: int = 1, page_size: int = 20) -> Dict[str, Any]:
        try:
            with self._get_connection() as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                query = 'SELECT * FROM sustainability WHERE 1=1'
                params = []
                if education_type:
                    query += ' AND education_type = ?'
                    params.append(education_type)
                cursor.execute(f'SELECT COUNT(*) as cnt FROM ({query})', params)
                total = cursor.fetchone()['cnt']
                query += ' ORDER BY last_evaluation DESC LIMIT ? OFFSET ?'
                params.extend([page_size, (page - 1) * page_size])
                cursor.execute(query, params)
                records = [dict(r) for r in cursor.fetchall()]
                return {'success': True, 'records': records, 'total': total, 'page': page, 'page_size': page_size}
        except Exception as e:
            logger.error(f'获取可持续性记录失败: {e}')
            return {'success': False, 'error': str(e)}

    # ========== 监控预警 ==========

    def create_monitor(self, monitor_type: str, threshold: float,
                       **kwargs) -> Dict[str, Any]:
        try:
            monitor_id = f"em_{uuid.uuid4().hex[:12]}"
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute(''' INSERT INTO ecosystem_monitoring ( monitor_id, partner_id, education_type, monitor_type, threshold, status, created_at, updated_at ) VALUES (?, ?, ?, ?, ?, 'active', ?, ?) ''', (monitor_id, kwargs.get('partner_id'), kwargs.get('education_type'),
                          monitor_type, threshold, now, now))
                    conn.commit()
                    return {'success': True, 'monitor_id': monitor_id}
        except Exception as e:
            logger.error(f'创建监控失败: {e}')
            return {'success': False, 'error': str(e)}

    def record_monitor_data(self, monitor_id: str, value: float) -> Dict[str, Any]:
        try:
            data_id = f"md_{uuid.uuid4().hex[:12]}"
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('SELECT threshold, partner_id, education_type FROM ecosystem_monitoring WHERE monitor_id = ?', (monitor_id,))
                    monitor = cursor.fetchone()
                    if not monitor:
                        return {'success': False, 'error': '监控不存在'}
                    cursor.execute(''' INSERT INTO monitoring_data ( data_id, monitor_id, value, recorded_at, created_at ) VALUES (?, ?, ?, ?, ?) ''', (data_id, monitor_id, value, now[:10], now))
                    if value > monitor[0]:
                        alert_id = f"ea_{uuid.uuid4().hex[:12]}"
                        cursor.execute(''' INSERT INTO ecosystem_alerts ( alert_id, monitor_id, partner_id, education_type, alert_type, severity, message, status, created_at ) VALUES (?, ?, ?, ?, ?, ?, ?, 'active', ?) ''', (alert_id, monitor_id, monitor[1], monitor[2],
                              'threshold_exceeded', 'warning',
                              f'Monitor {monitor_id} exceeded threshold: {value} > {monitor[0]}', now))
                    conn.commit()
                    return {'success': True, 'data_id': data_id}
        except Exception as e:
            logger.error(f'记录监控数据失败: {e}')
            return {'success': False, 'error': str(e)}

    def resolve_alert(self, alert_id: str, actor_id: int, actor_name: str,
                      **kwargs) -> Dict[str, Any]:
        try:
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute(''' UPDATE ecosystem_alerts SET status = 'resolved', resolved_at = ?, updated_at = ? WHERE alert_id = ? AND status = 'active' ''', (now[:10], now, alert_id))
                    if cursor.rowcount > 0:
                        history_id = f"ah_{uuid.uuid4().hex[:12]}"
                        cursor.execute(''' INSERT INTO alert_history ( history_id, alert_id, action, actor_id, actor_name, action_time, notes, created_at ) VALUES (?, ?, ?, ?, ?, ?, ?, ?) ''', (history_id, alert_id, 'resolved', actor_id, actor_name, now[:10],
                              kwargs.get('notes'), now))
                        conn.commit()
                        return {'success': True, 'status': 'resolved'}
                    return {'success': False, 'error': '告警不存在或已解决'}
        except Exception as e:
            logger.error(f'解决告警失败: {e}')
            return {'success': False, 'error': str(e)}

    def get_alert_history(self, partner_id: str = None, education_type: str = None,
                          page: int = 1, page_size: int = 20) -> Dict[str, Any]:
        try:
            with self._get_connection() as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                query = 'SELECT * FROM ecosystem_alerts WHERE 1=1'
                params = []
                if partner_id:
                    query += ' AND partner_id = ?'
                    params.append(partner_id)
                if education_type:
                    query += ' AND education_type = ?'
                    params.append(education_type)
                cursor.execute(f'SELECT COUNT(*) as cnt FROM ({query})', params)
                total = cursor.fetchone()['cnt']
                query += ' ORDER BY created_at DESC LIMIT ? OFFSET ?'
                params.extend([page_size, (page - 1) * page_size])
                cursor.execute(query, params)
                alerts = [dict(a) for a in cursor.fetchall()]
                return {'success': True, 'alerts': alerts, 'total': total, 'page': page, 'page_size': page_size}
        except Exception as e:
            logger.error(f'获取告警历史失败: {e}')
            return {'success': False, 'error': str(e)}

    # ========== 统计分析 ==========

    def get_ecosystem_summary(self, education_type: str = None) -> Dict[str, Any]:
        try:
            with self._get_connection() as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                where_clause = f' AND education_type = "{education_type}"' if education_type else ''

                cursor.execute(f'SELECT COUNT( *) as count FROM ecosystem_partners WHERE status = "approved"{where_clause}')
                partners = cursor.fetchone()['count']

                cursor.execute(f'SELECT COUNT( *) as count FROM shared_resources WHERE status = "available"{where_clause}')
                resources = cursor.fetchone()['count']

                cursor.execute(f'SELECT COUNT( *) as count FROM integrated_services WHERE status = "available"{where_clause}')
                services = cursor.fetchone()['count']

                cursor.execute(f'SELECT COUNT( *) as count FROM data_interchange WHERE transfer_status = "completed"{where_clause}')
                data_transfers = cursor.fetchone()['count']

                cursor.execute(f'SELECT COUNT( *) as count FROM ecosystem_standards WHERE status = "published"{where_clause}')
                standards = cursor.fetchone()['count']

                cursor.execute(f'SELECT COUNT(*) as count FROM value_co_creation WHERE status = "active"{where_clause}')
                projects = cursor.fetchone()['count']

                cursor.execute(f'SELECT COUNT( *) as count FROM risk_management WHERE status = "identified"{where_clause}')
                active_risks = cursor.fetchone()['count']

                cursor.execute(f'SELECT COUNT(*) as count FROM ecosystem_alerts WHERE status = "active"{where_clause}')
                active_alerts = cursor.fetchone()['count']

                summary = {
                    'partner_count': partners,
                    'resource_count': resources,
                    'service_count': services,
                    'data_transfer_count': data_transfers,
                    'standard_count': standards,
                    'active_projects': projects,
                    'active_risks': active_risks,
                    'active_alerts': active_alerts,
                    'education_type': education_type or 'all'
                }
                return {'success': True, 'summary': summary}
        except Exception as e:
            logger.error(f'获取生态系统统计失败: {e}')
            return {'success': False, 'error': str(e)}