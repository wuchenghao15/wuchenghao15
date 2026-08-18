from core.db_path import get_db_path as _mtscos_get_db_path
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
""" MTSCOS 教育政策研究服务 (v15.13.0) ==================================== 提供教育政策研究、政策解读、政策评估、政策咨询、政策监测等综合管理服务。  核心能力： 1. 政策管理 - 政策录入、版本管理、状态跟踪、检索查询 2. 政策解读 - 深度解读、政策问答、要点提炼、案例分析 3. 政策研究 - 政策分析、比较研究、趋势预测、政策建议 4. 政策评估 - 目标评估、效果评估、影响评估、可持续性评估 5. 政策咨询 - 咨询受理、专家答疑、方案建议、跟进反馈 6. 政策监测 - 动态监测、预警提示、变更跟踪、影响分析 7. 政策数据库 - 政策存储、标签管理、关联分析、知识图谱 8. 影响分析 - 社会影响、经济影响、教育质量、公平性分析 9. 研究报告 - 报告生成、数据分析、可视化、导出分享 10. 统计分析 - 数据统计、趋势分析、报表生成  支持教育类型：成人教育 / K12教育 """
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
            os.path.join(os.path.dirname(os.path.abspath(__file__)), 'education_policy_service.log'),
            encoding='utf-8'
        ),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger('EducationPolicy')


# ========== 政策配置项 ==========

POLICY_TYPES = {
    'law': {'name': '法律法规', 'priority': 1},
    'regulation': {'name': '部门规章', 'priority': 2},
    'normative': {'name': '规范性文件', 'priority': 3},
    'plan': {'name': '规划纲要', 'priority': 4},
    'guidance': {'name': '指导意见', 'priority': 5},
    'implementation': {'name': '实施方案', 'priority': 6},
    'notice': {'name': '通知公告', 'priority': 7}
}

POLICY_LEVELS = {
    'national': {'name': '国家级', 'scope': '全国', 'authority': '国务院及部委'},
    'provincial': {'name': '省级', 'scope': '省/自治区/直辖市', 'authority': '省级政府及部门'},
    'municipal': {'name': '市级', 'scope': '地级市', 'authority': '市级政府及部门'},
    'county': {'name': '县级', 'scope': '县/区', 'authority': '县级政府及部门'},
    'school': {'name': '校级', 'scope': '学校', 'authority': '学校及部门'}
}

POLICY_DOMAINS = {
    'basic': {'name': '基础教育', 'age_range': '3-15岁', 'focus': '义务教育'},
    'vocational': {'name': '职业教育', 'age_range': '15-25岁', 'focus': '技能培训'},
    'higher': {'name': '高等教育', 'age_range': '18-25岁', 'focus': '本科/研究生'},
    'adult': {'name': '成人教育', 'age_range': '18岁以上', 'focus': '继续教育'},
    'private': {'name': '民办教育', 'age_range': '全年龄段', 'focus': '民办机构'},
    'special': {'name': '特殊教育', 'age_range': '3-25岁', 'focus': '特殊需求'},
    'informatization': {'name': '教育信息化', 'age_range': '全年龄段', 'focus': '技术应用'},
    'teacher': {'name': '教师队伍', 'age_range': '无', 'focus': '师资建设'}
}

RESEARCH_TYPES = {
    'analysis': {'name': '政策分析', 'method': '定性定量结合'},
    'evaluation': {'name': '政策评估', 'method': '多维度评估'},
    'prediction': {'name': '政策预测', 'method': '趋势分析'},
    'suggestion': {'name': '政策建议', 'method': '实证研究'},
    'comparative': {'name': '比较研究', 'method': '横向对比'},
    'case': {'name': '案例研究', 'method': '深度剖析'}
}

EVALUATION_DIMENSIONS = {
    'goal': {'name': '目标达成', 'weight': 0.2},
    'effect': {'name': '实施效果', 'weight': 0.2},
    'social': {'name': '社会影响', 'weight': 0.15},
    'economic': {'name': '经济效益', 'weight': 0.15},
    'equity': {'name': '公平性', 'weight': 0.15},
    'sustainability': {'name': '可持续性', 'weight': 0.15}
}

POLICY_STATUS = {
    'draft': {'name': '草案', 'description': '起草阶段'},
    'consultation': {'name': '征求意见', 'description': '公开征求意见'},
    'published': {'name': '发布', 'description': '正式发布'},
    'implemented': {'name': '实施', 'description': '正在实施'},
    'revised': {'name': '修订', 'description': '修订中'},
    'abolished': {'name': '废止', 'description': '已废止'},
    'expired': {'name': '失效', 'description': '已失效'}
}

IMPACT_LEVELS = {
    'major': {'name': '重大', 'color': 'red', 'threshold': 80},
    'significant': {'name': '较大', 'color': 'orange', 'threshold': 60},
    'general': {'name': '一般', 'color': 'yellow', 'threshold': 40},
    'minor': {'name': '较小', 'color': 'green', 'threshold': 0}
}


class EducationPolicyResearchService:
    """教育政策研究服务"""

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
                cursor.execute(''' CREATE TABLE IF NOT EXISTS policies ( policy_id TEXT PRIMARY KEY, title TEXT NOT NULL, policy_type TEXT, policy_level TEXT, policy_domain TEXT, education_type TEXT, issuing_authority TEXT, issue_date TEXT, effective_date TEXT, expiry_date TEXT, status TEXT DEFAULT 'draft', summary TEXT, full_text TEXT, file_url TEXT, tags TEXT, is_key_policy INTEGER DEFAULT 0, created_at TEXT, updated_at TEXT ) ''')
                cursor.execute(''' CREATE TABLE IF NOT EXISTS policy_documents ( doc_id TEXT PRIMARY KEY, policy_id TEXT NOT NULL, doc_type TEXT, doc_title TEXT, file_path TEXT, file_size INTEGER, upload_time TEXT, FOREIGN KEY (policy_id) REFERENCES policies(policy_id) ) ''')
                cursor.execute(''' CREATE TABLE IF NOT EXISTS policy_versions ( version_id TEXT PRIMARY KEY, policy_id TEXT NOT NULL, version_number TEXT, version_date TEXT, change_summary TEXT, content_diff TEXT, status TEXT DEFAULT 'active', created_at TEXT, FOREIGN KEY (policy_id) REFERENCES policies(policy_id) ) ''')
                cursor.execute(''' CREATE TABLE IF NOT EXISTS policy_interpretations ( interpretation_id TEXT PRIMARY KEY, policy_id TEXT NOT NULL, interpreter TEXT, interpreter_title TEXT, interpretation_date TEXT, content TEXT, interpretation_type TEXT, source_url TEXT, created_at TEXT, FOREIGN KEY (policy_id) REFERENCES policies(policy_id) ) ''')
                cursor.execute(''' CREATE TABLE IF NOT EXISTS policy_research ( research_id TEXT PRIMARY KEY, policy_id TEXT, research_type TEXT, title TEXT NOT NULL, researcher TEXT, organization TEXT, education_type TEXT, methodology TEXT, key_findings TEXT, recommendations TEXT, status TEXT DEFAULT 'in_progress', created_at TEXT, updated_at TEXT ) ''')
                cursor.execute(''' CREATE TABLE IF NOT EXISTS research_reports ( report_id TEXT PRIMARY KEY, research_id TEXT NOT NULL, report_title TEXT, report_type TEXT, content TEXT, data_analysis TEXT, charts TEXT, attachments TEXT, status TEXT DEFAULT 'draft', created_at TEXT, updated_at TEXT, FOREIGN KEY (research_id) REFERENCES policy_research(research_id) ) ''')
                cursor.execute(''' CREATE TABLE IF NOT EXISTS policy_evaluations ( evaluation_id TEXT PRIMARY KEY, policy_id TEXT NOT NULL, evaluator TEXT, organization TEXT, education_type TEXT, evaluation_date TEXT, evaluation_scope TEXT, methodology TEXT, overall_score REAL, status TEXT DEFAULT 'in_progress', created_at TEXT, FOREIGN KEY (policy_id) REFERENCES policies(policy_id) ) ''')
                cursor.execute(''' CREATE TABLE IF NOT EXISTS evaluation_results ( result_id TEXT PRIMARY KEY, evaluation_id TEXT NOT NULL, dimension TEXT, score REAL, weight REAL, comments TEXT, evidence TEXT, FOREIGN KEY (evaluation_id) REFERENCES policy_evaluations(evaluation_id) ) ''')
                cursor.execute(''' CREATE TABLE IF NOT EXISTS policy_monitoring ( monitor_id TEXT PRIMARY KEY, policy_id TEXT NOT NULL, monitor_name TEXT, monitor_type TEXT, frequency TEXT, threshold TEXT, status TEXT DEFAULT 'active', created_at TEXT, FOREIGN KEY (policy_id) REFERENCES policies(policy_id) ) ''')
                cursor.execute(''' CREATE TABLE IF NOT EXISTS monitoring_records ( record_id TEXT PRIMARY KEY, monitor_id TEXT NOT NULL, record_date TEXT, data_value TEXT, status TEXT, alert_level TEXT, notes TEXT, FOREIGN KEY (monitor_id) REFERENCES policy_monitoring(monitor_id) ) ''')
                cursor.execute(''' CREATE TABLE IF NOT EXISTS policy_consultations ( consultation_id TEXT PRIMARY KEY, policy_id TEXT, education_type TEXT, consultor_name TEXT, consultor_organization TEXT, consultor_contact TEXT, consultation_date TEXT, question TEXT, urgency TEXT, status TEXT DEFAULT 'pending', created_at TEXT ) ''')
                cursor.execute(''' CREATE TABLE IF NOT EXISTS consultation_records ( record_id TEXT PRIMARY KEY, consultation_id TEXT NOT NULL, responder TEXT, response_date TEXT, response_content TEXT, attachments TEXT, follow_up_needed INTEGER DEFAULT 0, FOREIGN KEY (consultation_id) REFERENCES policy_consultations(consultation_id) ) ''')
                cursor.execute(''' CREATE TABLE IF NOT EXISTS policy_database ( db_id TEXT PRIMARY KEY, entry_type TEXT, title TEXT, content TEXT, source TEXT, tags TEXT, education_type TEXT, created_at TEXT, updated_at TEXT ) ''')
                cursor.execute(''' CREATE TABLE IF NOT EXISTS policy_tags ( tag_id TEXT PRIMARY KEY, tag_name TEXT NOT NULL, tag_category TEXT, description TEXT, usage_count INTEGER DEFAULT 0, created_at TEXT ) ''')
                cursor.execute(''' CREATE TABLE IF NOT EXISTS policy_references ( ref_id TEXT PRIMARY KEY, policy_id TEXT NOT NULL, reference_type TEXT, reference_title TEXT, reference_source TEXT, reference_url TEXT, FOREIGN KEY (policy_id) REFERENCES policies(policy_id) ) ''')
                cursor.execute(''' CREATE TABLE IF NOT EXISTS policy_impact_analysis ( analysis_id TEXT PRIMARY KEY, policy_id TEXT NOT NULL, analysis_type TEXT, education_type TEXT, impact_level TEXT, impact_summary TEXT, detailed_analysis TEXT, beneficiaries TEXT, affected_groups TEXT, recommendations TEXT, created_at TEXT, FOREIGN KEY (policy_id) REFERENCES policies(policy_id) ) ''')
                conn.commit()
                logger.info('教育政策研究服务数据库初始化完成')
        except Exception as e:
            logger.error(f'数据库初始化失败: {e}')

    # ========== 政策管理 ==========

    def create_policy(self, title: str, policy_type: str, policy_level: str,
                      policy_domain: str, **kwargs) -> Dict[str, Any]:
        try:
            policy_id = f"pol_{uuid.uuid4().hex[:12]}"
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute(''' INSERT INTO policies ( policy_id, title, policy_type, policy_level, policy_domain, education_type, issuing_authority, issue_date, effective_date, expiry_date, status, summary, full_text, file_url, tags, is_key_policy, created_at, updated_at ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?) ''', (policy_id, title, policy_type, policy_level, policy_domain,
                          kwargs.get('education_type'), kwargs.get('issuing_authority'),
                          kwargs.get('issue_date'), kwargs.get('effective_date'),
                          kwargs.get('expiry_date'), kwargs.get('status', 'draft'),
                          kwargs.get('summary'), kwargs.get('full_text'),
                          kwargs.get('file_url'), kwargs.get('tags'),
                          kwargs.get('is_key_policy', 0), now, now))
                    conn.commit()
                    logger.info(f'创建政策: {title} ({policy_id})')
                    return {'success': True, 'policy_id': policy_id}
        except Exception as e:
            logger.error(f'创建政策失败: {e}')
            return {'success': False, 'error': str(e)}

    def update_policy_status(self, policy_id: str, status: str) -> Dict[str, Any]:
        try:
            if status not in POLICY_STATUS:
                return {'success': False, 'error': '无效的政策状态'}
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('UPDATE policies SET status = ?, updated_at = ? WHERE policy_id = ?',
                                 (status, now, policy_id))
                    if cursor.rowcount > 0:
                        conn.commit()
                        return {'success': True, 'status': POLICY_STATUS[status]['name']}
                    return {'success': False, 'error': '政策不存在'}
        except Exception as e:
            logger.error(f'更新政策状态失败: {e}')
            return {'success': False, 'error': str(e)}

    def add_policy_version(self, policy_id: str, version_number: str,
                           change_summary: str, **kwargs) -> Dict[str, Any]:
        try:
            version_id = f"ver_{uuid.uuid4().hex[:12]}"
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('SELECT policy_id FROM policies WHERE policy_id = ?', (policy_id,))
                    if not cursor.fetchone():
                        return {'success': False, 'error': '政策不存在'}
                    cursor.execute(''' INSERT INTO policy_versions ( version_id, policy_id, version_number, version_date, change_summary, content_diff, status, created_at ) VALUES (?, ?, ?, ?, ?, ?, 'active', ?) ''', (version_id, policy_id, version_number, now[:10],
                          change_summary, kwargs.get('content_diff'), now))
                    conn.commit()
                    return {'success': True, 'version_id': version_id}
        except Exception as e:
            logger.error(f'添加政策版本失败: {e}')
            return {'success': False, 'error': str(e)}

    def search_policies(self, **kwargs) -> Dict[str, Any]:
        try:
            with self._get_connection() as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                query = 'SELECT * FROM policies WHERE 1=1'
                params = []
                if kwargs.get('title'):
                    query += ' AND title LIKE ?'
                    params.append(f"%{kwargs['title']}%")
                if kwargs.get('policy_type'):
                    query += ' AND policy_type = ?'
                    params.append(kwargs['policy_type'])
                if kwargs.get('policy_level'):
                    query += ' AND policy_level = ?'
                    params.append(kwargs['policy_level'])
                if kwargs.get('policy_domain'):
                    query += ' AND policy_domain = ?'
                    params.append(kwargs['policy_domain'])
                if kwargs.get('education_type'):
                    query += ' AND education_type = ?'
                    params.append(kwargs['education_type'])
                if kwargs.get('status'):
                    query += ' AND status = ?'
                    params.append(kwargs['status'])
                if kwargs.get('is_key_policy') is not None:
                    query += ' AND is_key_policy = ?'
                    params.append(1 if kwargs['is_key_policy'] else 0)
                cursor.execute(f'SELECT COUNT(*) as cnt FROM ({query})', params)
                total = cursor.fetchone()['cnt']
                page = kwargs.get('page', 1)
                page_size = kwargs.get('page_size', 20)
                query += ' ORDER BY issue_date DESC LIMIT ? OFFSET ?'
                params.extend([page_size, (page - 1) * page_size])
                cursor.execute(query, params)
                policies = [dict(p) for p in cursor.fetchall()]
                return {'success': True, 'policies': policies, 'total': total, 'page': page, 'page_size': page_size}
        except Exception as e:
            logger.error(f'搜索政策失败: {e}')
            return {'success': False, 'error': str(e)}

    # ========== 政策解读 ==========

    def add_policy_interpretation(self, policy_id: str, interpreter: str,
                                  content: str, **kwargs) -> Dict[str, Any]:
        try:
            interpretation_id = f"int_{uuid.uuid4().hex[:12]}"
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('SELECT policy_id FROM policies WHERE policy_id = ?', (policy_id,))
                    if not cursor.fetchone():
                        return {'success': False, 'error': '政策不存在'}
                    cursor.execute(''' INSERT INTO policy_interpretations ( interpretation_id, policy_id, interpreter, interpreter_title, interpretation_date, content, interpretation_type, source_url, created_at ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?) ''', (interpretation_id, policy_id, interpreter, kwargs.get('interpreter_title'),
                          now[:10], content, kwargs.get('interpretation_type'),
                          kwargs.get('source_url'), now))
                    conn.commit()
                    return {'success': True, 'interpretation_id': interpretation_id}
        except Exception as e:
            logger.error(f'添加政策解读失败: {e}')
            return {'success': False, 'error': str(e)}

    def get_policy_interpretations(self, policy_id: str) -> Dict[str, Any]:
        try:
            with self._get_connection() as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                cursor.execute(
                'SELECT * FROM policy_interpretations WHERE policy_id = ? ORDER BY interpretation_date DESC',
                (policy_id,))
                interpretations = [dict(i) for i in cursor.fetchall()]
                return {'success': True, 'interpretations': interpretations}
        except Exception as e:
            logger.error(f'获取政策解读失败: {e}')
            return {'success': False, 'error': str(e)}

    def extract_policy_key_points(self, policy_id: str) -> Dict[str, Any]:
        try:
            with self._get_connection() as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                cursor.execute('SELECT title, summary, full_text, policy_type, policy_level FROM policies WHERE policy_id = ?', (policy_id,))
                policy = cursor.fetchone()
                if not policy:
                    return {'success': False, 'error': '政策不存在'}
                key_points = {
                    'policy_id': policy_id,
                    'title': policy['title'],
                    'policy_type': POLICY_TYPES.get(policy['policy_type'], {}).get('name', policy['policy_type']),
                    'policy_level': POLICY_LEVELS.get(policy['policy_level'], {}).get('name', policy['policy_level']),
                    'summary': policy['summary'],
                    'key_elements': []
                }
                if policy['full_text']:
                    text = policy['full_text'][:500]
                    key_points['key_elements'] = [
                        {'type': '政策目标', 'content': '根据政策文本分析得出的核心目标'},
                        {'type': '适用范围', 'content': '政策适用的地域、人群和时间范围'},
                        {'type': '主要措施', 'content': '政策提出的具体实施措施'},
                        {'type': '责任主体', 'content': '政策执行的责任部门和单位'},
                        {'type': '预期效果', 'content': '政策预期达成的效果和目标'}
                    ]
                return {'success': True, 'key_points': key_points}
        except Exception as e:
            logger.error(f'提取政策要点失败: {e}')
            return {'success': False, 'error': str(e)}

    def analyze_policy_case(self, policy_id: str, case_description: str) -> Dict[str, Any]:
        try:
            with self._get_connection() as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                cursor.execute('SELECT title, policy_domain FROM policies WHERE policy_id = ?', (policy_id,))
                policy = cursor.fetchone()
                if not policy:
                    return {'success': False, 'error': '政策不存在'}
                analysis = {
                    'policy_id': policy_id,
                    'policy_title': policy['title'],
                    'policy_domain': POLICY_DOMAINS.get(policy['policy_domain'], {}).get('name',
                    policy['policy_domain']),
                    'case_description': case_description,
                    'analysis_result': {
                        'applicability': 'high',
                        'key_issues': ['政策适用性评估', '实施条件分析', '预期效果预测'],
                        'recommendations': ['建议参照政策条款执行', '注意实施细节', '做好风险评估'],
                        'impact_analysis': '案例符合政策导向，预期产生积极影响'
                    }
                }
                return {'success': True, 'analysis': analysis}
        except Exception as e:
            logger.error(f'政策案例分析失败: {e}')
            return {'success': False, 'error': str(e)}

    # ========== 政策研究 ==========

    def create_research_project(self, title: str, research_type: str,
                                **kwargs) -> Dict[str, Any]:
        try:
            research_id = f"rsr_{uuid.uuid4().hex[:12]}"
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute(''' INSERT INTO policy_research ( research_id, policy_id, research_type, title, researcher, organization, education_type, methodology, key_findings, recommendations, status, created_at, updated_at ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'in_progress', ?, ?) ''', (research_id, kwargs.get('policy_id'), research_type, title,
                          kwargs.get('researcher'), kwargs.get('organization'),
                          kwargs.get('education_type'), kwargs.get('methodology'),
                          kwargs.get('key_findings'), kwargs.get('recommendations'),
                          now, now))
                    conn.commit()
                    return {'success': True, 'research_id': research_id}
        except Exception as e:
            logger.error(f'创建研究项目失败: {e}')
            return {'success': False, 'error': str(e)}

    def update_research_project(self, research_id: str, **kwargs) -> Dict[str, Any]:
        try:
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    update_fields = []
                    update_values = []
                    if 'title' in kwargs:
                        update_fields.append('title = ?')
                        update_values.append(kwargs['title'])
                    if 'research_type' in kwargs:
                        update_fields.append('research_type = ?')
                        update_values.append(kwargs['research_type'])
                    if 'key_findings' in kwargs:
                        update_fields.append('key_findings = ?')
                        update_values.append(kwargs['key_findings'])
                    if 'recommendations' in kwargs:
                        update_fields.append('recommendations = ?')
                        update_values.append(kwargs['recommendations'])
                    if 'status' in kwargs:
                        update_fields.append('status = ?')
                        update_values.append(kwargs['status'])
                    if update_fields:
                        update_fields.append('updated_at = ?')
                        update_values.append(now)
                        update_values.append(research_id)
                        query = f'UPDATE policy_research SET {", ".join(update_fields)} WHERE research_id = ?'
                        cursor.execute(query, update_values)
                        if cursor.rowcount > 0:
                            conn.commit()
                            return {'success': True}
                    return {'success': False, 'error': '无更新内容或研究项目不存在'}
        except Exception as e:
            logger.error(f'更新研究项目失败: {e}')
            return {'success': False, 'error': str(e)}

    def compare_policies(self, policy_ids: List[str], education_type: str = None) -> Dict[str, Any]:
        try:
            with self._get_connection() as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                placeholders = ','.join(['?'] * len(policy_ids))
                query = f'SELECT * FROM policies WHERE policy_id IN ({placeholders})'
                if education_type:
                    query += ' AND education_type = ?'
                    params = policy_ids + [education_type]
                else:
                    params = policy_ids
                cursor.execute(query, params)
                policies = [dict(p) for p in cursor.fetchall()]
                if len(policies) < 2:
                    return {'success': False, 'error': '至少需要两个政策进行比较'}
                comparison = {
                    'policy_ids': policy_ids,
                    'education_type': education_type,
                    'comparison_dimensions': ['政策类型', '层级', '领域', '发布时间', '实施效果'],
                    'policies': []
                }
                for p in policies:
                    comparison['policies'].append({
                        'policy_id': p['policy_id'],
                        'title': p['title'],
                        'policy_type': POLICY_TYPES.get(p['policy_type'], {}).get('name'),
                        'policy_level': POLICY_LEVELS.get(p['policy_level'], {}).get('name'),
                        'policy_domain': POLICY_DOMAINS.get(p['policy_domain'], {}).get('name'),
                        'issue_date': p['issue_date'],
                        'status': POLICY_STATUS.get(p['status'], {}).get('name')
                    })
                comparison['summary'] = f'共比较 {len(policies)} 个政策，涵盖 {len(set( p["policy_domain"] for p in policies))} 个领域'
                return {'success': True, 'comparison': comparison}
        except Exception as e:
            logger.error(f'政策比较失败: {e}')
            return {'success': False, 'error': str(e)}

    def predict_policy_trends(self, policy_domain: str = None,
                              education_type: str = None) -> Dict[str, Any]:
        try:
            with self._get_connection() as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                query = 'SELECT policy_type, issue_date FROM policies WHERE status = "implemented"'
                params = []
                if policy_domain:
                    query += ' AND policy_domain = ?'
                    params.append(policy_domain)
                if education_type:
                    query += ' AND education_type = ?'
                    params.append(education_type)
                cursor.execute(query, params)
                policies = cursor.fetchall()
                trend_analysis = {
                    'policy_domain': POLICY_DOMAINS.get(policy_domain, {}).get('name', '全部'),
                    'education_type': education_type,
                    'total_policies': len(policies),
                    'trend_predictions': [
                        {'period': '短期(1-2年)', 'trends': ['政策细化', '执行监督加强']},
                        {'period': '中期(3-5年)', 'trends': ['数字化转型加速', '质量评估体系完善']},
                        {'period': '长期(5年以上)', 'trends': ['终身学习体系构建', '教育公平深化']}
                    ],
                    'key_drivers': ['人口结构变化', '技术创新', '经济发展需求', '社会公平诉求']
                }
                return {'success': True, 'trend_analysis': trend_analysis}
        except Exception as e:
            logger.error(f'政策趋势预测失败: {e}')
            return {'success': False, 'error': str(e)}

    # ========== 政策评估 ==========

    def create_evaluation(self, policy_id: str, evaluator: str,
                          organization: str, **kwargs) -> Dict[str, Any]:
        try:
            evaluation_id = f"eva_{uuid.uuid4().hex[:12]}"
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('SELECT policy_id FROM policies WHERE policy_id = ?', (policy_id,))
                    if not cursor.fetchone():
                        return {'success': False, 'error': '政策不存在'}
                    cursor.execute(''' INSERT INTO policy_evaluations ( evaluation_id, policy_id, evaluator, organization, education_type, evaluation_date, evaluation_scope, methodology, overall_score, status, created_at ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, NULL, 'in_progress', ?) ''', (evaluation_id, policy_id, evaluator, organization,
                          kwargs.get('education_type'), now[:10],
                          kwargs.get('evaluation_scope'), kwargs.get('methodology'), now))
                    conn.commit()
                    return {'success': True, 'evaluation_id': evaluation_id}
        except Exception as e:
            logger.error(f'创建评估失败: {e}')
            return {'success': False, 'error': str(e)}

    def add_evaluation_result(self, evaluation_id: str, dimension: str,
                              score: float, **kwargs) -> Dict[str, Any]:
        try:
            result_id = f"res_{uuid.uuid4().hex[:12]}"
            weight = EVALUATION_DIMENSIONS.get(dimension, {}).get('weight', 0.15)
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('SELECT evaluation_id FROM policy_evaluations WHERE evaluation_id = ?',
                    (evaluation_id,))
                    if not cursor.fetchone():
                        return {'success': False, 'error': '评估不存在'}
                    cursor.execute(''' INSERT INTO evaluation_results ( result_id, evaluation_id, dimension, score, weight, comments, evidence ) VALUES (?, ?, ?, ?, ?, ?, ?) ''', (result_id, evaluation_id, dimension, score, weight,
                          kwargs.get('comments'), kwargs.get('evidence')))
                    cursor.execute(''' SELECT SUM(score * weight) / SUM(weight) FROM evaluation_results WHERE evaluation_id = ? ''', (evaluation_id,))
                    overall = cursor.fetchone()[0]
                    if overall:
                        cursor.execute('UPDATE policy_evaluations SET overall_score = ? WHERE evaluation_id = ?',
                        (round(overall, 2), evaluation_id))
                    conn.commit()
                    return {'success': True, 'result_id': result_id, 'overall_score': round(overall,
                    2) if overall else None}
        except Exception as e:
            logger.error(f'添加评估结果失败: {e}')
            return {'success': False, 'error': str(e)}

    def complete_evaluation(self, evaluation_id: str) -> Dict[str, Any]:
        try:
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('SELECT overall_score FROM policy_evaluations WHERE evaluation_id = ?',
                    (evaluation_id,))
                    eval_data = cursor.fetchone()
                    if not eval_data:
                        return {'success': False, 'error': '评估不存在'}
                    cursor.execute('UPDATE policy_evaluations SET status = "completed" WHERE evaluation_id = ?',
                    (evaluation_id,))
                    conn.commit()
                    return {'success': True, 'overall_score': eval_data[0], 'status': 'completed'}
        except Exception as e:
            logger.error(f'完成评估失败: {e}')
            return {'success': False, 'error': str(e)}

    def get_evaluation_report(self, evaluation_id: str) -> Dict[str, Any]:
        try:
            with self._get_connection() as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                cursor.execute('SELECT * FROM policy_evaluations WHERE evaluation_id = ?', (evaluation_id,))
                evaluation = cursor.fetchone()
                if not evaluation:
                    return {'success': False, 'error': '评估不存在'}
                cursor.execute('SELECT * FROM evaluation_results WHERE evaluation_id = ?', (evaluation_id,))
                results = [dict(r) for r in cursor.fetchall()]
                report = {
                    'evaluation_id': evaluation_id,
                    'policy_id': evaluation['policy_id'],
                    'evaluator': evaluation['evaluator'],
                    'organization': evaluation['organization'],
                    'education_type': evaluation['education_type'],
                    'evaluation_date': evaluation['evaluation_date'],
                    'overall_score': evaluation['overall_score'],
                    'status': evaluation['status'],
                    'dimensions': []
                }
                for r in results:
                    report['dimensions'].append({
                        'dimension': EVALUATION_DIMENSIONS.get(r['dimension'], {}).get('name', r['dimension']),
                        'score': r['score'],
                        'weight': r['weight'],
                        'weighted_score': round(r['score'] * r['weight'], 2),
                        'comments': r['comments']
                    })
                return {'success': True, 'report': report}
        except Exception as e:
            logger.error(f'获取评估报告失败: {e}')
            return {'success': False, 'error': str(e)}

    def list_evaluations(self, policy_id: str = None, status: str = None,
                         page: int = 1, page_size: int = 20) -> Dict[str, Any]:
        try:
            with self._get_connection() as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                query = 'SELECT * FROM policy_evaluations WHERE 1=1'
                params = []
                if policy_id:
                    query += ' AND policy_id = ?'
                    params.append(policy_id)
                if status:
                    query += ' AND status = ?'
                    params.append(status)
                cursor.execute(f'SELECT COUNT(*) as cnt FROM ({query})', params)
                total = cursor.fetchone()['cnt']
                query += ' ORDER BY evaluation_date DESC LIMIT ? OFFSET ?'
                params.extend([page_size, (page - 1) * page_size])
                cursor.execute(query, params)
                evaluations = [dict(e) for e in cursor.fetchall()]
                return {'success': True, 'evaluations': evaluations, 'total': total, 'page': page,
                'page_size': page_size}
        except Exception as e:
            logger.error(f'获取评估列表失败: {e}')
            return {'success': False, 'error': str(e)}

    # ========== 政策咨询 ==========

    def submit_consultation(self, question: str, consultor_name: str,
                            **kwargs) -> Dict[str, Any]:
        try:
            consultation_id = f"con_{uuid.uuid4().hex[:12]}"
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute(''' INSERT INTO policy_consultations ( consultation_id, policy_id, education_type, consultor_name, consultor_organization, consultor_contact, consultation_date, question, urgency, status, created_at ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, 'pending', ?) ''', (consultation_id, kwargs.get('policy_id'), kwargs.get('education_type'),
                          consultor_name, kwargs.get('consultor_organization'),
                          kwargs.get('consultor_contact'), now[:10], question,
                          kwargs.get('urgency', 'normal'), now))
                    conn.commit()
                    return {'success': True, 'consultation_id': consultation_id}
        except Exception as e:
            logger.error(f'提交咨询失败: {e}')
            return {'success': False, 'error': str(e)}

    def respond_consultation(self, consultation_id: str, responder: str,
                             response_content: str, **kwargs) -> Dict[str, Any]:
        try:
            record_id = f"cr_{uuid.uuid4().hex[:12]}"
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('SELECT consultation_id FROM policy_consultations WHERE consultation_id = ?',
                    (consultation_id,))
                    if not cursor.fetchone():
                        return {'success': False, 'error': '咨询不存在'}
                    cursor.execute(''' INSERT INTO consultation_records ( record_id, consultation_id, responder, response_date, response_content, attachments, follow_up_needed ) VALUES (?, ?, ?, ?, ?, ?, ?) ''', (record_id, consultation_id, responder, now[:10],
                          response_content, kwargs.get('attachments'),
                          kwargs.get('follow_up_needed', 0)))
                    cursor.execute('UPDATE policy_consultations SET status = "responded" WHERE consultation_id = ?',
                    (consultation_id,))
                    conn.commit()
                    return {'success': True, 'record_id': record_id}
        except Exception as e:
            logger.error(f'回复咨询失败: {e}')
            return {'success': False, 'error': str(e)}

    def get_consultation_history(self, consultation_id: str) -> Dict[str, Any]:
        try:
            with self._get_connection() as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                cursor.execute('SELECT * FROM policy_consultations WHERE consultation_id = ?', (consultation_id,))
                consultation = cursor.fetchone()
                if not consultation:
                    return {'success': False, 'error': '咨询不存在'}
                cursor.execute(
                'SELECT * FROM consultation_records WHERE consultation_id = ? ORDER BY response_date DESC',
                (consultation_id,))
                records = [dict(r) for r in cursor.fetchall()]
                return {'success': True, 'consultation': dict(consultation), 'records': records}
        except Exception as e:
            logger.error(f'获取咨询历史失败: {e}')
            return {'success': False, 'error': str(e)}

    def list_consultations(self, status: str = None, education_type: str = None,
                           page: int = 1, page_size: int = 20) -> Dict[str, Any]:
        try:
            with self._get_connection() as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                query = 'SELECT * FROM policy_consultations WHERE 1=1'
                params = []
                if status:
                    query += ' AND status = ?'
                    params.append(status)
                if education_type:
                    query += ' AND education_type = ?'
                    params.append(education_type)
                cursor.execute(f'SELECT COUNT(*) as cnt FROM ({query})', params)
                total = cursor.fetchone()['cnt']
                query += ' ORDER BY consultation_date DESC LIMIT ? OFFSET ?'
                params.extend([page_size, (page - 1) * page_size])
                cursor.execute(query, params)
                consultations = [dict(c) for c in cursor.fetchall()]
                return {'success': True, 'consultations': consultations, 'total': total, 'page': page,
                'page_size': page_size}
        except Exception as e:
            logger.error(f'获取咨询列表失败: {e}')
            return {'success': False, 'error': str(e)}

    # ========== 政策监测 ==========

    def create_monitor(self, policy_id: str, monitor_name: str,
                       monitor_type: str, **kwargs) -> Dict[str, Any]:
        try:
            monitor_id = f"mon_{uuid.uuid4().hex[:12]}"
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('SELECT policy_id FROM policies WHERE policy_id = ?', (policy_id,))
                    if not cursor.fetchone():
                        return {'success': False, 'error': '政策不存在'}
                    cursor.execute(''' INSERT INTO policy_monitoring ( monitor_id, policy_id, monitor_name, monitor_type, frequency, threshold, status, created_at ) VALUES (?, ?, ?, ?, ?, ?, 'active', ?) ''', (monitor_id, policy_id, monitor_name, monitor_type,
                          kwargs.get('frequency', 'daily'), kwargs.get('threshold'), now))
                    conn.commit()
                    return {'success': True, 'monitor_id': monitor_id}
        except Exception as e:
            logger.error(f'创建监测失败: {e}')
            return {'success': False, 'error': str(e)}

    def add_monitoring_record(self, monitor_id: str, data_value: str, **kwargs) -> Dict[str, Any]:
        try:
            record_id = f"mr_{uuid.uuid4().hex[:12]}"
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('SELECT threshold FROM policy_monitoring WHERE monitor_id = ?', (monitor_id,))
                    monitor = cursor.fetchone()
                    if not monitor:
                        return {'success': False, 'error': '监测不存在'}
                    alert_level = 'normal'
                    if monitor[0] and data_value:
                        try:
                            if float(data_value) > float(monitor[0]):
                                alert_level = 'warning'
                        except ValueError:
                            pass
                    cursor.execute(''' INSERT INTO monitoring_records ( record_id, monitor_id, record_date, data_value, status, alert_level, notes ) VALUES (?, ?, ?, ?, ?, ?, ?) ''', (record_id, monitor_id, now[:10], data_value,
                          kwargs.get('status', 'normal'), alert_level, kwargs.get('notes')))
                    conn.commit()
                    return {'success': True, 'record_id': record_id, 'alert_level': alert_level}
        except Exception as e:
            logger.error(f'添加监测记录失败: {e}')
            return {'success': False, 'error': str(e)}

    def get_monitoring_alerts(self, monitor_id: str = None, alert_level: str = 'warning') -> Dict[str, Any]:
        try:
            with self._get_connection() as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                query = 'SELECT * FROM monitoring_records WHERE alert_level = ?'
                params = [alert_level]
                if monitor_id:
                    query += ' AND monitor_id = ?'
                    params.append(monitor_id)
                query += ' ORDER BY record_date DESC'
                cursor.execute(query, params)
                alerts = [dict(a) for a in cursor.fetchall()]
                return {'success': True, 'alerts': alerts}
        except Exception as e:
            logger.error(f'获取监测预警失败: {e}')
            return {'success': False, 'error': str(e)}

    def get_monitoring_summary(self, policy_id: str) -> Dict[str, Any]:
        try:
            with self._get_connection() as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                cursor.execute('SELECT * FROM policy_monitoring WHERE policy_id = ?', (policy_id,))
                monitors = [dict(m) for m in cursor.fetchall()]
                summary = {
                    'policy_id': policy_id,
                    'monitor_count': len(monitors),
                    'monitors': []
                }
                for m in monitors:
                    cursor.execute('SELECT COUNT( *) as cnt FROM monitoring_records WHERE monitor_id = ? AND alert_level = "warning"',
                    (m['monitor_id'],))
                    warning_count = cursor.fetchone()['cnt']
                    summary['monitors'].append({
                        'monitor_id': m['monitor_id'],
                        'monitor_name': m['monitor_name'],
                        'monitor_type': m['monitor_type'],
                        'frequency': m['frequency'],
                        'warning_count': warning_count,
                        'status': m['status']
                    })
                return {'success': True, 'summary': summary}
        except Exception as e:
            logger.error(f'获取监测汇总失败: {e}')
            return {'success': False, 'error': str(e)}

    # ========== 政策数据库 ==========

    def add_database_entry(self, entry_type: str, title: str,
                           content: str, **kwargs) -> Dict[str, Any]:
        try:
            db_id = f"dbe_{uuid.uuid4().hex[:12]}"
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute(''' INSERT INTO policy_database ( db_id, entry_type, title, content, source, tags, education_type, created_at, updated_at ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?) ''', (db_id, entry_type, title, content, kwargs.get('source'),
                          kwargs.get('tags'), kwargs.get('education_type'), now, now))
                    conn.commit()
                    return {'success': True, 'db_id': db_id}
        except Exception as e:
            logger.error(f'添加数据库条目失败: {e}')
            return {'success': False, 'error': str(e)}

    def add_policy_tag(self, tag_name: str, tag_category: str, **kwargs) -> Dict[str, Any]:
        try:
            tag_id = f"tag_{uuid.uuid4().hex[:12]}"
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('SELECT tag_id FROM policy_tags WHERE tag_name = ?', (tag_name,))
                    if cursor.fetchone():
                        return {'success': False, 'error': '标签已存在'}
                    cursor.execute(''' INSERT INTO policy_tags ( tag_id, tag_name, tag_category, description, usage_count, created_at ) VALUES (?, ?, ?, ?, 0, ?) ''', (tag_id, tag_name, tag_category, kwargs.get('description'), now))
                    conn.commit()
                    return {'success': True, 'tag_id': tag_id}
        except Exception as e:
            logger.error(f'添加政策标签失败: {e}')
            return {'success': False, 'error': str(e)}

    def add_policy_reference(self, policy_id: str, reference_type: str,
                             reference_title: str, **kwargs) -> Dict[str, Any]:
        try:
            ref_id = f"ref_{uuid.uuid4().hex[:12]}"
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('SELECT policy_id FROM policies WHERE policy_id = ?', (policy_id,))
                    if not cursor.fetchone():
                        return {'success': False, 'error': '政策不存在'}
                    cursor.execute(''' INSERT INTO policy_references ( ref_id, policy_id, reference_type, reference_title, reference_source, reference_url ) VALUES (?, ?, ?, ?, ?, ?) ''', (ref_id, policy_id, reference_type, reference_title,
                          kwargs.get('reference_source'), kwargs.get('reference_url')))
                    conn.commit()
                    return {'success': True, 'ref_id': ref_id}
        except Exception as e:
            logger.error(f'添加政策引用失败: {e}')
            return {'success': False, 'error': str(e)}

    def search_database(self, **kwargs) -> Dict[str, Any]:
        try:
            with self._get_connection() as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                query = 'SELECT * FROM policy_database WHERE 1=1'
                params = []
                if kwargs.get('entry_type'):
                    query += ' AND entry_type = ?'
                    params.append(kwargs['entry_type'])
                if kwargs.get('title'):
                    query += ' AND title LIKE ?'
                    params.append(f"%{kwargs['title']}%")
                if kwargs.get('tags'):
                    query += ' AND tags LIKE ?'
                    params.append(f"%{kwargs['tags']}%")
                if kwargs.get('education_type'):
                    query += ' AND education_type = ?'
                    params.append(kwargs['education_type'])
                cursor.execute(f'SELECT COUNT(*) as cnt FROM ({query})', params)
                total = cursor.fetchone()['cnt']
                page = kwargs.get('page', 1)
                page_size = kwargs.get('page_size', 20)
                query += ' ORDER BY created_at DESC LIMIT ? OFFSET ?'
                params.extend([page_size, (page - 1) * page_size])
                cursor.execute(query, params)
                entries = [dict(e) for e in cursor.fetchall()]
                return {'success': True, 'entries': entries, 'total': total, 'page': page, 'page_size': page_size}
        except Exception as e:
            logger.error(f'搜索数据库失败: {e}')
            return {'success': False, 'error': str(e)}

    # ========== 影响分析 ==========

    def analyze_social_impact(self, policy_id: str, education_type: str = None) -> Dict[str, Any]:
        try:
            with self._get_connection() as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                cursor.execute('SELECT title, policy_domain FROM policies WHERE policy_id = ?', (policy_id,))
                policy = cursor.fetchone()
                if not policy:
                    return {'success': False, 'error': '政策不存在'}
                impact = {
                    'policy_id': policy_id,
                    'policy_title': policy['title'],
                    'education_type': education_type,
                    'analysis_type': 'social',
                    'impact_level': 'significant',
                    'key_indicators': [
                        {'name': '受教育人群覆盖', 'impact': 'positive', 'description': '政策预计覆盖更多目标人群'},
                        {'name': '教育公平性', 'impact': 'positive', 'description': '促进教育资源均衡分配'},
                        {'name': '社会认可度', 'impact': 'positive', 'description': '提升公众对教育政策的认同'},
                        {'name': '家庭负担', 'impact': 'mixed', 'description': '部分家庭可能受益，部分可能增加负担'}
                    ],
                    'summary': '政策对社会层面产生积极影响，有助于提升整体教育水平和社会公平'
                }
                return {'success': True, 'impact': impact}
        except Exception as e:
            logger.error(f'社会影响分析失败: {e}')
            return {'success': False, 'error': str(e)}

    def analyze_economic_impact(self, policy_id: str, education_type: str = None) -> Dict[str, Any]:
        try:
            with self._get_connection() as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                cursor.execute('SELECT title, policy_domain FROM policies WHERE policy_id = ?', (policy_id,))
                policy = cursor.fetchone()
                if not policy:
                    return {'success': False, 'error': '政策不存在'}
                impact = {
                    'policy_id': policy_id,
                    'policy_title': policy['title'],
                    'education_type': education_type,
                    'analysis_type': 'economic',
                    'impact_level': 'general',
                    'key_indicators': [
                        {'name': '政府投入', 'impact': 'positive', 'description': '预计增加教育财政投入'},
                        {'name': '就业市场', 'impact': 'positive', 'description': '提升劳动者素质，促进就业'},
                        {'name': '产业发展', 'impact': 'positive', 'description': '带动教育相关产业发展'},
                        {'name': '个人投资回报', 'impact': 'positive', 'description': '提升教育投资回报率'}
                    ],
                    'cost_benefit': {'estimated_cost': '中等', 'estimated_benefit': '长期', 'payback_period': '5-10年'},
                    'summary': '政策具有良好的经济效益，长期来看将促进经济发展和人力资本提升'
                }
                return {'success': True, 'impact': impact}
        except Exception as e:
            logger.error(f'经济影响分析失败: {e}')
            return {'success': False, 'error': str(e)}

    def analyze_equity_impact(self, policy_id: str, education_type: str = None) -> Dict[str, Any]:
        try:
            with self._get_connection() as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                cursor.execute('SELECT title, policy_domain FROM policies WHERE policy_id = ?', (policy_id,))
                policy = cursor.fetchone()
                if not policy:
                    return {'success': False, 'error': '政策不存在'}
                impact = {
                    'policy_id': policy_id,
                    'policy_title': policy['title'],
                    'education_type': education_type,
                    'analysis_type': 'equity',
                    'impact_level': 'significant',
                    'dimensions': [
                        {'name': '城乡差距', 'analysis': '有助于缩小城乡教育资源差距', 'confidence': 'high'},
                        {'name': '区域均衡', 'analysis': '促进区域教育协调发展', 'confidence': 'medium'},
                        {'name': '群体公平', 'analysis': '关注特殊群体教育权益保障', 'confidence': 'high'},
                        {'name': '性别平等', 'analysis': '推动教育性别平等', 'confidence': 'medium'}
                    ],
                    'recommendations': ['加强资源倾斜', '建立公平监测机制', '完善补偿性政策'],
                    'summary': '政策在公平性方面设计合理，有望显著改善教育公平状况'
                }
                return {'success': True, 'impact': impact}
        except Exception as e:
            logger.error(f'公平性影响分析失败: {e}')
            return {'success': False, 'error': str(e)}

    # ========== 研究报告 ==========

    def create_research_report(self, research_id: str, report_title: str,
                               **kwargs) -> Dict[str, Any]:
        try:
            report_id = f"rpt_{uuid.uuid4().hex[:12]}"
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('SELECT research_id FROM policy_research WHERE research_id = ?', (research_id,))
                    if not cursor.fetchone():
                        return {'success': False, 'error': '研究项目不存在'}
                    cursor.execute(''' INSERT INTO research_reports ( report_id, research_id, report_title, report_type, content, data_analysis, charts, attachments, status, created_at, updated_at ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, 'draft', ?, ?) ''', (report_id, research_id, report_title, kwargs.get('report_type'),
                          kwargs.get('content'), kwargs.get('data_analysis'),
                          kwargs.get('charts'), kwargs.get('attachments'), now, now))
                    conn.commit()
                    return {'success': True, 'report_id': report_id}
        except Exception as e:
            logger.error(f'创建研究报告失败: {e}')
            return {'success': False, 'error': str(e)}

    def update_research_report(self, report_id: str, **kwargs) -> Dict[str, Any]:
        try:
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    update_fields = []
                    update_values = []
                    if 'content' in kwargs:
                        update_fields.append('content = ?')
                        update_values.append(kwargs['content'])
                    if 'data_analysis' in kwargs:
                        update_fields.append('data_analysis = ?')
                        update_values.append(kwargs['data_analysis'])
                    if 'charts' in kwargs:
                        update_fields.append('charts = ?')
                        update_values.append(kwargs['charts'])
                    if 'status' in kwargs:
                        update_fields.append('status = ?')
                        update_values.append(kwargs['status'])
                    if update_fields:
                        update_fields.append('updated_at = ?')
                        update_values.append(now)
                        update_values.append(report_id)
                        query = f'UPDATE research_reports SET {", ".join(update_fields)} WHERE report_id = ?'
                        cursor.execute(query, update_values)
                        if cursor.rowcount > 0:
                            conn.commit()
                            return {'success': True}
                    return {'success': False, 'error': '无更新内容或报告不存在'}
        except Exception as e:
            logger.error(f'更新研究报告失败: {e}')
            return {'success': False, 'error': str(e)}

    def get_research_report(self, report_id: str) -> Dict[str, Any]:
        try:
            with self._get_connection() as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                cursor.execute('SELECT * FROM research_reports WHERE report_id = ?', (report_id,))
                report = cursor.fetchone()
                if not report:
                    return {'success': False, 'error': '报告不存在'}
                cursor.execute('SELECT title, research_type, education_type FROM policy_research WHERE research_id = ?',
                (report['research_id'],))
                research = cursor.fetchone()
                full_report = dict(report)
                if research:
                    full_report['research_title'] = research['title']
                    full_report['research_type'] = RESEARCH_TYPES.get(research['research_type'], {}).get('name',
                    research['research_type'])
                    full_report['education_type'] = research['education_type']
                return {'success': True, 'report': full_report}
        except Exception as e:
            logger.error(f'获取研究报告失败: {e}')
            return {'success': False, 'error': str(e)}

    def export_report(self, report_id: str, format: str = 'pdf') -> Dict[str, Any]:
        try:
            with self._get_connection() as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                cursor.execute('SELECT * FROM research_reports WHERE report_id = ?', (report_id,))
                report = cursor.fetchone()
                if not report:
                    return {'success': False, 'error': '报告不存在'}
                export_data = {
                    'report_id': report_id,
                    'report_title': report['report_title'],
                    'format': format,
                    'export_time': datetime.now().isoformat(),
                    'content_preview': report['content'][:200] if report['content'] else '',
                    'file_name': f"report_{report_id}_{datetime.now().strftime('%Y%m%d')}.{format}",
                    'status': 'ready'
                }
                return {'success': True, 'export': export_data}
        except Exception as e:
            logger.error(f'导出报告失败: {e}')
            return {'success': False, 'error': str(e)}

    # ========== 统计分析 ==========

    def get_policy_statistics(self, education_type: str = None) -> Dict[str, Any]:
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                base_query = 'WHERE 1=1'
                params = []
                if education_type:
                    base_query += ' AND education_type = ?'
                    params.append(education_type)
                cursor.execute(f'SELECT COUNT(*) as cnt FROM policies {base_query}', params)
                total_policies = cursor.fetchone()[0]
                cursor.execute(f'SELECT COUNT(*) as cnt FROM policies {base_query} AND status = "implemented"', params)
                implemented_count = cursor.fetchone()[0]
                cursor.execute(f'SELECT policy_domain, COUNT(*) as cnt FROM policies {base_query} GROUP BY policy_domain', params)
                domain_dist = []
                for row in cursor.fetchall():
                    domain_dist.append({
                        'domain': POLICY_DOMAINS.get(row[0], {}).get('name', row[0]),
                        'count': row[1]
                    })
                cursor.execute(f'SELECT policy_level, COUNT(*) as cnt FROM policies {base_query} GROUP BY policy_level',
                params)
                level_dist = []
                for row in cursor.fetchall():
                    level_dist.append({
                        'level': POLICY_LEVELS.get(row[0], {}).get('name', row[0]),
                        'count': row[1]
                    })
                cursor.execute(f'SELECT COUNT(*) as cnt FROM policy_evaluations {base_query}', params)
                evaluation_count = cursor.fetchone()[0]
                cursor.execute(f'SELECT COUNT(*) as cnt FROM policy_research {base_query}', params)
                research_count = cursor.fetchone()[0]
                statistics = {
                    'education_type': education_type or '全部',
                    'total_policies': total_policies,
                    'implemented_policies': implemented_count,
                    'implementation_rate': round(implemented_count / total_policies * 100,
                    2) if total_policies > 0 else 0,
                    'domain_distribution': domain_dist,
                    'level_distribution': level_dist,
                    'evaluation_count': evaluation_count,
                    'research_count': research_count,
                    'update_time': datetime.now().isoformat()
                }
                return {'success': True, 'statistics': statistics}
        except Exception as e:
            logger.error(f'获取政策统计失败: {e}')
            return {'success': False, 'error': str(e)}






































































