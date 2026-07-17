#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
MTSCOS 教育信息化治理服务 (v15.20.0)
====================================
提供IT治理、信息系统管理、技术架构、数据治理、安全治理、IT服务管理、
IT投资管理、IT绩效评估等综合管理服务。

核心能力：
1. IT治理 - 治理框架、战略对齐、价值交付、治理委员会
2. 信息系统 - 系统管理、目录管理、集成管理、运行监控
3. 技术架构 - 架构规划、组件管理、技术选型、演进管理
4. 数据治理 - 数据标准、数据质量、元数据管理、数据安全
5. 安全治理 - 安全策略、身份认证、访问控制、安全审计、合规管理
6. IT服务管理 - 服务目录、服务级别、变更管理、问题管理
7. IT投资管理 - 预算管理、投资评估、采购管理、供应商管理
8. IT绩效评估 - 效率评估、效果评估、满意度、价值分析
9. 项目管理 - 项目规划、执行跟踪、状态管理、资源分配
10. 统计分析 - 综合统计、报表生成

支持教育类型：成人教育、K12教育
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
            os.path.join(os.path.dirname(os.path.abspath(__file__)), 'education_it_governance_service.log'),
            encoding='utf-8'
        ),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger('EducationITGovernance')


# ========== IT治理配置 ==========

IT_GOVERNANCE_FRAMEWORKS = {
    'cobit': {'name': 'COBIT', 'focus': 'IT治理与管理', 'version': 'COBIT 2019'},
    'itil': {'name': 'ITIL', 'focus': 'IT服务管理', 'version': 'ITIL 4'},
    'iso27001': {'name': 'ISO 27001', 'focus': '信息安全管理', 'version': 'ISO/IEC 27001:2022'},
    'nist': {'name': 'NIST', 'focus': '网络安全框架', 'version': 'NIST CSF v1.1'},
    'governance_committee': {'name': 'IT治理委员会', 'focus': '决策监督', 'version': '企业级'},
    'enterprise_architecture': {'name': '企业架构', 'focus': '架构治理', 'version': 'TOGAF 9.2'},
    'strategic_alignment': {'name': '战略对齐', 'focus': '业务-IT对齐', 'version': '企业级'},
    'value_delivery': {'name': '价值交付', 'focus': 'IT价值实现', 'version': '企业级'}
}

INFORMATION_SYSTEMS = {
    'academic': {'name': '教务系统', 'modules': ['选课管理', '课程管理', '成绩管理', '排课系统']},
    'student': {'name': '学工系统', 'modules': ['学籍管理', '学生事务', '资助管理', '就业管理']},
    'finance': {'name': '财务系统', 'modules': ['预算管理', '收费管理', '报销管理', '账务核算']},
    'hr': {'name': '人事系统', 'modules': ['人员管理', '薪酬管理', '考勤管理', '绩效评估']},
    'research': {'name': '科研系统', 'modules': ['项目管理', '成果管理', '经费管理', '学术交流']},
    'library': {'name': '图书馆系统', 'modules': ['馆藏管理', '借阅管理', '数字资源', '读者服务']},
    'campus_card': {'name': '校园卡系统', 'modules': ['身份认证', '消费管理', '门禁管理', '充值管理']},
    'portal': {'name': '门户系统', 'modules': ['统一登录', '信息发布', '应用集成', '个性化服务']}
}

TECHNOLOGY_ARCHITECTURE = {
    'cloud': {'name': '云计算', 'components': ['IaaS', 'PaaS', 'SaaS', '混合云']},
    'bigdata': {'name': '大数据', 'components': ['数据采集', '存储', '分析', '可视化']},
    'ai': {'name': '人工智能', 'components': ['机器学习', '深度学习', 'NLP', '知识图谱']},
    'iot': {'name': '物联网', 'components': ['传感器', '网关', '平台', '应用']},
    'blockchain': {'name': '区块链', 'components': ['分布式账本', '智能合约', '共识机制']},
    'edge': {'name': '边缘计算', 'components': ['边缘节点', '边缘网关', '边缘存储']},
    'microservices': {'name': '微服务', 'components': ['服务注册', 'API网关', '服务编排']},
    'container': {'name': '容器化', 'components': ['Docker', 'Kubernetes', 'DevOps']}
}

DATA_GOVERNANCE = {
    'standards': {'name': '数据标准', 'elements': ['数据定义', '编码规范', '格式标准', '命名规则']},
    'quality': {'name': '数据质量', 'elements': ['准确性', '完整性', '一致性', '时效性']},
    'security': {'name': '数据安全', 'elements': ['数据分类', '加密', '脱敏', '访问控制']},
    'lifecycle': {'name': '数据生命周期', 'elements': ['创建', '存储', '使用', '归档', '销毁']},
    'metadata': {'name': '元数据管理', 'elements': ['技术元数据', '业务元数据', '管理元数据']},
    'catalog': {'name': '数据目录', 'elements': ['数据资产', '数据地图', '数据说明']},
    'lineage': {'name': '数据血缘', 'elements': ['来源追溯', '流向追踪', '影响分析']},
    'committee': {'name': '数据治理委员会', 'elements': ['决策机制', '职责分工', '工作流程']}
}

SECURITY_GOVERNANCE = {
    'network': {'name': '网络安全', 'controls': ['防火墙', '入侵检测', 'VPN', '网络分段']},
    'data': {'name': '数据安全', 'controls': ['加密', '脱敏', '备份', '灾备']},
    'application': {'name': '应用安全', 'controls': ['代码审计', '渗透测试', 'WAF', '安全编码']},
    'infrastructure': {'name': '基础设施安全', 'controls': ['服务器安全', '操作系统加固', '补丁管理']},
    'identity': {'name': '身份认证', 'controls': ['SSO', 'MFA', '身份生命周期', '权限管理']},
    'access': {'name': '访问控制', 'controls': ['RBAC', 'ABAC', '最小权限', '权限审计']},
    'audit': {'name': '安全审计', 'controls': ['日志审计', '行为分析', '合规检查', '报告生成']},
    'compliance': {'name': '合规管理', 'controls': ['等级保护', 'GDPR', 'ISO 27001', '安全评估']}
}

IT_SERVICE_MANAGEMENT = {
    'service_catalog': {'name': '服务目录', 'items': ['服务定义', '服务描述', '服务等级', '服务定价']},
    'slm': {'name': '服务级别管理', 'items': ['SLA定义', 'SLA监控', 'SLA报告', 'SLA改进']},
    'change': {'name': '变更管理', 'items': ['变更请求', '变更评估', '变更实施', '变更回滚']},
    'configuration': {'name': '配置管理', 'items': ['CMDB', '配置项管理', '配置审计', '配置变更']},
    'problem': {'name': '问题管理', 'items': ['问题识别', '根本原因分析', '问题解决', '预防措施']},
    'incident': {'name': '事件管理', 'items': ['事件记录', '事件分类', '事件解决', '事件报告']},
    'release': {'name': '发布管理', 'items': ['发布规划', '测试验证', '部署实施', '发布回顾']},
    'continuity': {'name': '连续性管理', 'items': ['BCP', 'DRP', '灾备演练', '恢复测试']}
}

IT_INVESTMENT = {
    'budget': {'name': '预算管理', 'activities': ['预算编制', '预算审批', '预算执行', '预算调整']},
    'evaluation': {'name': '投资评估', 'activities': ['可行性分析', '风险评估', '收益预测', '方案比选']},
    'roi': {'name': 'ROI分析', 'activities': ['成本测算', '效益分析', '回收期计算', '敏感性分析']},
    'cost_benefit': {'name': '成本效益分析', 'activities': ['成本归集', '效益识别', '效益量化', '对比分析']},
    'project': {'name': '项目评估', 'activities': ['项目筛选', '优先级排序', '资源配置', '绩效跟踪']},
    'procurement': {'name': '采购管理', 'activities': ['需求分析', '招标采购', '合同签订', '验收交付']},
    'supplier': {'name': '供应商管理', 'activities': ['供应商评估', '供应商选择', '绩效评价', '关系管理']},
    'contract': {'name': '合同管理', 'activities': ['合同起草', '合同审批', '合同执行', '合同终止']}
}

IT_PERFORMANCE = {
    'efficiency': {'name': 'IT效率', 'metrics': ['资源利用率', '响应时间', '处理能力', '自动化程度']},
    'effectiveness': {'name': 'IT效果', 'metrics': ['目标达成率', '质量合格率', '交付及时率', '客户满意度']},
    'satisfaction': {'name': '用户满意度', 'metrics': ['满意度评分', '投诉率', '建议采纳率', '忠诚度']},
    'availability': {'name': '系统可用性', 'metrics': ['可用性百分比', '故障时间', '恢复时间', 'MTBF']},
    'response': {'name': '响应时间', 'metrics': ['平均响应时间', '峰值响应时间', '超时率', '吞吐量']},
    'cost_effectiveness': {'name': '成本效益', 'metrics': ['单位成本', '成本节约率', '投资回报率', '价值创造']},
    'innovation': {'name': '创新能力', 'metrics': ['新技术应用', '专利数量', '流程改进', '数字化转型']},
    'business_value': {'name': '业务价值', 'metrics': ['业务提升度', '效率提升率', '竞争优势', '战略贡献']}
}


class EducationITGovernanceService:
    """教育信息化治理服务"""

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
                    CREATE TABLE IF NOT EXISTS it_governance (
                        governance_id TEXT PRIMARY KEY,
                        framework_type TEXT NOT NULL,
                        education_type TEXT,
                        name TEXT NOT NULL,
                        description TEXT,
                        scope TEXT,
                        status TEXT DEFAULT 'active',
                        established_date TEXT,
                        review_frequency TEXT,
                        created_at TEXT,
                        updated_at TEXT
                    )
                ''')
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS governance_framework (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        governance_id TEXT NOT NULL,
                        framework_code TEXT NOT NULL,
                        framework_name TEXT,
                        adoption_level TEXT,
                        implementation_status TEXT,
                        last_review_date TEXT,
                        next_review_date TEXT,
                        FOREIGN KEY (governance_id) REFERENCES it_governance(governance_id)
                    )
                ''')
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS information_systems (
                        system_id TEXT PRIMARY KEY,
                        system_code TEXT NOT NULL,
                        system_name TEXT NOT NULL,
                        education_type TEXT,
                        description TEXT,
                        vendor TEXT,
                        version TEXT,
                        deployment_status TEXT DEFAULT 'deployed',
                        critical_level TEXT DEFAULT 'medium',
                        created_at TEXT,
                        updated_at TEXT
                    )
                ''')
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS system_catalog (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        system_id TEXT NOT NULL,
                        module_name TEXT NOT NULL,
                        module_code TEXT,
                        description TEXT,
                        access_level TEXT,
                        FOREIGN KEY (system_id) REFERENCES information_systems(system_id)
                    )
                ''')
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS technology_architecture (
                        architecture_id TEXT PRIMARY KEY,
                        architecture_name TEXT NOT NULL,
                        education_type TEXT,
                        description TEXT,
                        status TEXT DEFAULT 'active',
                        created_at TEXT,
                        updated_at TEXT
                    )
                ''')
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS architecture_components (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        architecture_id TEXT NOT NULL,
                        component_name TEXT NOT NULL,
                        component_type TEXT,
                        vendor TEXT,
                        version TEXT,
                        status TEXT DEFAULT 'active',
                        FOREIGN KEY (architecture_id) REFERENCES technology_architecture(architecture_id)
                    )
                ''')
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS data_governance (
                        governance_id TEXT PRIMARY KEY,
                        governance_name TEXT NOT NULL,
                        education_type TEXT,
                        description TEXT,
                        status TEXT DEFAULT 'active',
                        created_at TEXT,
                        updated_at TEXT
                    )
                ''')
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS data_standards (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        governance_id TEXT NOT NULL,
                        standard_name TEXT NOT NULL,
                        standard_code TEXT,
                        description TEXT,
                        status TEXT DEFAULT 'active',
                        FOREIGN KEY (governance_id) REFERENCES data_governance(governance_id)
                    )
                ''')
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS security_governance (
                        security_id TEXT PRIMARY KEY,
                        security_name TEXT NOT NULL,
                        education_type TEXT,
                        description TEXT,
                        status TEXT DEFAULT 'active',
                        created_at TEXT,
                        updated_at TEXT
                    )
                ''')
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS security_policies (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        security_id TEXT NOT NULL,
                        policy_name TEXT NOT NULL,
                        policy_code TEXT,
                        policy_type TEXT,
                        description TEXT,
                        status TEXT DEFAULT 'active',
                        effective_date TEXT,
                        FOREIGN KEY (security_id) REFERENCES security_governance(security_id)
                    )
                ''')
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS it_service_management (
                        service_id TEXT PRIMARY KEY,
                        service_name TEXT NOT NULL,
                        education_type TEXT,
                        description TEXT,
                        status TEXT DEFAULT 'active',
                        created_at TEXT,
                        updated_at TEXT
                    )
                ''')
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS service_levels (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        service_id TEXT NOT NULL,
                        sla_name TEXT NOT NULL,
                        sla_code TEXT,
                        target_value TEXT,
                        actual_value TEXT,
                        status TEXT DEFAULT 'active',
                        FOREIGN KEY (service_id) REFERENCES it_service_management(service_id)
                    )
                ''')
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS it_investment (
                        investment_id TEXT PRIMARY KEY,
                        investment_name TEXT NOT NULL,
                        education_type TEXT,
                        budget_amount REAL DEFAULT 0,
                        actual_amount REAL DEFAULT 0,
                        status TEXT DEFAULT 'planning',
                        created_at TEXT,
                        updated_at TEXT
                    )
                ''')
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS investment_projects (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        investment_id TEXT NOT NULL,
                        project_name TEXT NOT NULL,
                        project_code TEXT,
                        budget REAL DEFAULT 0,
                        actual_cost REAL DEFAULT 0,
                        status TEXT DEFAULT 'pending',
                        FOREIGN KEY (investment_id) REFERENCES it_investment(investment_id)
                    )
                ''')
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS it_performance (
                        performance_id TEXT PRIMARY KEY,
                        performance_name TEXT NOT NULL,
                        education_type TEXT,
                        description TEXT,
                        period TEXT,
                        status TEXT DEFAULT 'active',
                        created_at TEXT,
                        updated_at TEXT
                    )
                ''')
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS performance_metrics (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        performance_id TEXT NOT NULL,
                        metric_name TEXT NOT NULL,
                        metric_code TEXT,
                        target_value TEXT,
                        actual_value TEXT,
                        unit TEXT,
                        FOREIGN KEY (performance_id) REFERENCES it_performance(performance_id)
                    )
                ''')
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS it_projects (
                        project_id TEXT PRIMARY KEY,
                        project_name TEXT NOT NULL,
                        education_type TEXT,
                        description TEXT,
                        status TEXT DEFAULT 'planning',
                        priority TEXT DEFAULT 'medium',
                        budget REAL DEFAULT 0,
                        progress REAL DEFAULT 0,
                        start_date TEXT,
                        end_date TEXT,
                        created_at TEXT,
                        updated_at TEXT
                    )
                ''')
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS project_status (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        project_id TEXT NOT NULL,
                        status TEXT NOT NULL,
                        status_date TEXT,
                        comment TEXT,
                        FOREIGN KEY (project_id) REFERENCES it_projects(project_id)
                    )
                ''')
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS it_assets (
                        asset_id TEXT PRIMARY KEY,
                        asset_name TEXT NOT NULL,
                        asset_type TEXT,
                        education_type TEXT,
                        location TEXT,
                        status TEXT DEFAULT 'active',
                        purchase_date TEXT,
                        value REAL DEFAULT 0,
                        created_at TEXT,
                        updated_at TEXT
                    )
                ''')
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS asset_management (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        asset_id TEXT NOT NULL,
                        action_type TEXT NOT NULL,
                        action_date TEXT,
                        responsible TEXT,
                        comment TEXT,
                        FOREIGN KEY (asset_id) REFERENCES it_assets(asset_id)
                    )
                ''')
                conn.commit()
                logger.info('教育信息化治理服务数据库初始化完成')
        except Exception as e:
            logger.error(f'数据库初始化失败: {e}')

    # ========== IT治理 ==========

    def create_it_governance(self, framework_type: str, name: str, **kwargs) -> Dict[str, Any]:
        try:
            governance_id = f"gov_{uuid.uuid4().hex[:12]}"
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('''
                        INSERT INTO it_governance (
                            governance_id, framework_type, education_type, name,
                            description, scope, status, established_date,
                            review_frequency, created_at, updated_at
                        ) VALUES (?, ?, ?, ?, ?, ?, 'active', ?, ?, ?, ?)
                    ''', (governance_id, framework_type, kwargs.get('education_type'), name,
                          kwargs.get('description'), kwargs.get('scope'),
                          kwargs.get('established_date', now[:10]),
                          kwargs.get('review_frequency', 'yearly'), now, now))
                    conn.commit()
                    logger.info(f'创建IT治理: {name} ({governance_id})')
                    return {'success': True, 'governance_id': governance_id}
        except Exception as e:
            logger.error(f'创建IT治理失败: {e}')
            return {'success': False, 'error': str(e)}

    def add_governance_framework(self, governance_id: str, framework_code: str, **kwargs) -> Dict[str, Any]:
        try:
            config = IT_GOVERNANCE_FRAMEWORKS.get(framework_code, {})
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('''
                        INSERT INTO governance_framework (
                            governance_id, framework_code, framework_name,
                            adoption_level, implementation_status, last_review_date, next_review_date
                        ) VALUES (?, ?, ?, ?, ?, ?, ?)
                    ''', (governance_id, framework_code,
                          kwargs.get('framework_name', config.get('name')),
                          kwargs.get('adoption_level', 'partial'),
                          kwargs.get('implementation_status', 'in_progress'),
                          kwargs.get('last_review_date'), kwargs.get('next_review_date')))
                    conn.commit()
                    return {'success': True}
        except Exception as e:
            logger.error(f'添加治理框架失败: {e}')
            return {'success': False, 'error': str(e)}

    def update_governance_status(self, governance_id: str, status: str) -> Dict[str, Any]:
        try:
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('UPDATE it_governance SET status = ?, updated_at = ? WHERE governance_id = ?',
                                 (status, now, governance_id))
                    if cursor.rowcount > 0:
                        conn.commit()
                        return {'success': True, 'status': status}
                    return {'success': False, 'error': 'IT治理记录不存在'}
        except Exception as e:
            logger.error(f'更新IT治理状态失败: {e}')
            return {'success': False, 'error': str(e)}

    def list_it_governance(self, education_type: str = None, status: str = None,
                           page: int = 1, page_size: int = 20) -> Dict[str, Any]:
        try:
            with self._get_connection() as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                query = 'SELECT * FROM it_governance WHERE 1=1'
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
                records = [dict(r) for r in cursor.fetchall()]
                return {'success': True, 'records': records, 'total': total, 'page': page, 'page_size': page_size}
        except Exception as e:
            logger.error(f'获取IT治理列表失败: {e}')
            return {'success': False, 'error': str(e)}

    # ========== 信息系统 ==========

    def register_information_system(self, system_code: str, system_name: str, **kwargs) -> Dict[str, Any]:
        try:
            system_id = f"sys_{uuid.uuid4().hex[:12]}"
            now = datetime.now().isoformat()
            config = INFORMATION_SYSTEMS.get(system_code, {})
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('''
                        INSERT INTO information_systems (
                            system_id, system_code, system_name, education_type,
                            description, vendor, version, deployment_status,
                            critical_level, created_at, updated_at
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    ''', (system_id, system_code, system_name,
                          kwargs.get('education_type'), kwargs.get('description'),
                          kwargs.get('vendor'), kwargs.get('version'),
                          kwargs.get('deployment_status', 'deployed'),
                          kwargs.get('critical_level', 'medium'), now, now))
                    if config.get('modules'):
                        for module in config['modules']:
                            cursor.execute('INSERT INTO system_catalog (system_id, module_name) VALUES (?, ?)',
                                         (system_id, module))
                    conn.commit()
                    logger.info(f'注册信息系统: {system_name} ({system_id})')
                    return {'success': True, 'system_id': system_id}
        except Exception as e:
            logger.error(f'注册信息系统失败: {e}')
            return {'success': False, 'error': str(e)}

    def add_system_module(self, system_id: str, module_name: str, **kwargs) -> Dict[str, Any]:
        try:
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('INSERT INTO system_catalog (system_id, module_name, module_code, description, access_level) VALUES (?, ?, ?, ?, ?)',
                                 (system_id, module_name, kwargs.get('module_code'),
                                  kwargs.get('description'), kwargs.get('access_level', 'internal')))
                    conn.commit()
                    return {'success': True}
        except Exception as e:
            logger.error(f'添加系统模块失败: {e}')
            return {'success': False, 'error': str(e)}

    def update_system_status(self, system_id: str, deployment_status: str) -> Dict[str, Any]:
        try:
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('UPDATE information_systems SET deployment_status = ?, updated_at = ? WHERE system_id = ?',
                                 (deployment_status, now, system_id))
                    if cursor.rowcount > 0:
                        conn.commit()
                        return {'success': True, 'status': deployment_status}
                    return {'success': False, 'error': '信息系统不存在'}
        except Exception as e:
            logger.error(f'更新系统状态失败: {e}')
            return {'success': False, 'error': str(e)}

    def list_information_systems(self, education_type: str = None, status: str = None,
                                 page: int = 1, page_size: int = 20) -> Dict[str, Any]:
        try:
            with self._get_connection() as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                query = 'SELECT * FROM information_systems WHERE 1=1'
                params = []
                if education_type:
                    query += ' AND education_type = ?'
                    params.append(education_type)
                if status:
                    query += ' AND deployment_status = ?'
                    params.append(status)
                cursor.execute(f'SELECT COUNT(*) as cnt FROM ({query})', params)
                total = cursor.fetchone()['cnt']
                query += ' ORDER BY created_at DESC LIMIT ? OFFSET ?'
                params.extend([page_size, (page - 1) * page_size])
                cursor.execute(query, params)
                systems = [dict(s) for s in cursor.fetchall()]
                return {'success': True, 'systems': systems, 'total': total, 'page': page, 'page_size': page_size}
        except Exception as e:
            logger.error(f'获取信息系统列表失败: {e}')
            return {'success': False, 'error': str(e)}

    # ========== 技术架构 ==========

    def create_technology_architecture(self, architecture_name: str, **kwargs) -> Dict[str, Any]:
        try:
            architecture_id = f"arc_{uuid.uuid4().hex[:12]}"
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('''
                        INSERT INTO technology_architecture (
                            architecture_id, architecture_name, education_type,
                            description, status, created_at, updated_at
                        ) VALUES (?, ?, ?, ?, 'active', ?, ?)
                    ''', (architecture_id, architecture_name, kwargs.get('education_type'),
                          kwargs.get('description'), now, now))
                    conn.commit()
                    logger.info(f'创建技术架构: {architecture_name} ({architecture_id})')
                    return {'success': True, 'architecture_id': architecture_id}
        except Exception as e:
            logger.error(f'创建技术架构失败: {e}')
            return {'success': False, 'error': str(e)}

    def add_architecture_component(self, architecture_id: str, component_name: str, **kwargs) -> Dict[str, Any]:
        try:
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('INSERT INTO architecture_components (architecture_id, component_name, component_type, vendor, version, status) VALUES (?, ?, ?, ?, ?, ?)',
                                 (architecture_id, component_name, kwargs.get('component_type'),
                                  kwargs.get('vendor'), kwargs.get('version'),
                                  kwargs.get('status', 'active')))
                    conn.commit()
                    return {'success': True}
        except Exception as e:
            logger.error(f'添加架构组件失败: {e}')
            return {'success': False, 'error': str(e)}

    def update_architecture_status(self, architecture_id: str, status: str) -> Dict[str, Any]:
        try:
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('UPDATE technology_architecture SET status = ?, updated_at = ? WHERE architecture_id = ?',
                                 (status, now, architecture_id))
                    if cursor.rowcount > 0:
                        conn.commit()
                        return {'success': True, 'status': status}
                    return {'success': False, 'error': '技术架构不存在'}
        except Exception as e:
            logger.error(f'更新架构状态失败: {e}')
            return {'success': False, 'error': str(e)}

    def list_technology_architectures(self, education_type: str = None, status: str = None,
                                      page: int = 1, page_size: int = 20) -> Dict[str, Any]:
        try:
            with self._get_connection() as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                query = 'SELECT * FROM technology_architecture WHERE 1=1'
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
                architectures = [dict(a) for a in cursor.fetchall()]
                return {'success': True, 'architectures': architectures, 'total': total, 'page': page, 'page_size': page_size}
        except Exception as e:
            logger.error(f'获取技术架构列表失败: {e}')
            return {'success': False, 'error': str(e)}

    # ========== 数据治理 ==========

    def create_data_governance(self, governance_name: str, **kwargs) -> Dict[str, Any]:
        try:
            governance_id = f"dgo_{uuid.uuid4().hex[:12]}"
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('''
                        INSERT INTO data_governance (
                            governance_id, governance_name, education_type,
                            description, status, created_at, updated_at
                        ) VALUES (?, ?, ?, ?, 'active', ?, ?)
                    ''', (governance_id, governance_name, kwargs.get('education_type'),
                          kwargs.get('description'), now, now))
                    conn.commit()
                    logger.info(f'创建数据治理: {governance_name} ({governance_id})')
                    return {'success': True, 'governance_id': governance_id}
        except Exception as e:
            logger.error(f'创建数据治理失败: {e}')
            return {'success': False, 'error': str(e)}

    def add_data_standard(self, governance_id: str, standard_name: str, **kwargs) -> Dict[str, Any]:
        try:
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('INSERT INTO data_standards (governance_id, standard_name, standard_code, description, status) VALUES (?, ?, ?, ?, ?)',
                                 (governance_id, standard_name, kwargs.get('standard_code'),
                                  kwargs.get('description'), kwargs.get('status', 'active')))
                    conn.commit()
                    return {'success': True}
        except Exception as e:
            logger.error(f'添加数据标准失败: {e}')
            return {'success': False, 'error': str(e)}

    def update_data_governance_status(self, governance_id: str, status: str) -> Dict[str, Any]:
        try:
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('UPDATE data_governance SET status = ?, updated_at = ? WHERE governance_id = ?',
                                 (status, now, governance_id))
                    if cursor.rowcount > 0:
                        conn.commit()
                        return {'success': True, 'status': status}
                    return {'success': False, 'error': '数据治理不存在'}
        except Exception as e:
            logger.error(f'更新数据治理状态失败: {e}')
            return {'success': False, 'error': str(e)}

    def list_data_governance(self, education_type: str = None, status: str = None,
                             page: int = 1, page_size: int = 20) -> Dict[str, Any]:
        try:
            with self._get_connection() as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                query = 'SELECT * FROM data_governance WHERE 1=1'
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
                records = [dict(r) for r in cursor.fetchall()]
                return {'success': True, 'records': records, 'total': total, 'page': page, 'page_size': page_size}
        except Exception as e:
            logger.error(f'获取数据治理列表失败: {e}')
            return {'success': False, 'error': str(e)}

    # ========== 安全治理 ==========

    def create_security_governance(self, security_name: str, **kwargs) -> Dict[str, Any]:
        try:
            security_id = f"sec_{uuid.uuid4().hex[:12]}"
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('''
                        INSERT INTO security_governance (
                            security_id, security_name, education_type,
                            description, status, created_at, updated_at
                        ) VALUES (?, ?, ?, ?, 'active', ?, ?)
                    ''', (security_id, security_name, kwargs.get('education_type'),
                          kwargs.get('description'), now, now))
                    conn.commit()
                    logger.info(f'创建安全治理: {security_name} ({security_id})')
                    return {'success': True, 'security_id': security_id}
        except Exception as e:
            logger.error(f'创建安全治理失败: {e}')
            return {'success': False, 'error': str(e)}

    def add_security_policy(self, security_id: str, policy_name: str, **kwargs) -> Dict[str, Any]:
        try:
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('''
                        INSERT INTO security_policies (
                            security_id, policy_name, policy_code, policy_type,
                            description, status, effective_date
                        ) VALUES (?, ?, ?, ?, ?, ?, ?)
                    ''', (security_id, policy_name, kwargs.get('policy_code'),
                          kwargs.get('policy_type'), kwargs.get('description'),
                          kwargs.get('status', 'active'), kwargs.get('effective_date')))
                    conn.commit()
                    return {'success': True}
        except Exception as e:
            logger.error(f'添加安全策略失败: {e}')
            return {'success': False, 'error': str(e)}

    def update_security_policy_status(self, policy_id: int, status: str) -> Dict[str, Any]:
        try:
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('UPDATE security_policies SET status = ? WHERE id = ?',
                                 (status, policy_id))
                    if cursor.rowcount > 0:
                        conn.commit()
                        return {'success': True, 'status': status}
                    return {'success': False, 'error': '安全策略不存在'}
        except Exception as e:
            logger.error(f'更新安全策略状态失败: {e}')
            return {'success': False, 'error': str(e)}

    def update_security_governance_status(self, security_id: str, status: str) -> Dict[str, Any]:
        try:
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('UPDATE security_governance SET status = ?, updated_at = ? WHERE security_id = ?',
                                 (status, now, security_id))
                    if cursor.rowcount > 0:
                        conn.commit()
                        return {'success': True, 'status': status}
                    return {'success': False, 'error': '安全治理不存在'}
        except Exception as e:
            logger.error(f'更新安全治理状态失败: {e}')
            return {'success': False, 'error': str(e)}

    def list_security_governance(self, education_type: str = None, status: str = None,
                                 page: int = 1, page_size: int = 20) -> Dict[str, Any]:
        try:
            with self._get_connection() as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                query = 'SELECT * FROM security_governance WHERE 1=1'
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
                records = [dict(r) for r in cursor.fetchall()]
                return {'success': True, 'records': records, 'total': total, 'page': page, 'page_size': page_size}
        except Exception as e:
            logger.error(f'获取安全治理列表失败: {e}')
            return {'success': False, 'error': str(e)}

    # ========== IT服务管理 ==========

    def create_it_service(self, service_name: str, **kwargs) -> Dict[str, Any]:
        try:
            service_id = f"svc_{uuid.uuid4().hex[:12]}"
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('''
                        INSERT INTO it_service_management (
                            service_id, service_name, education_type,
                            description, status, created_at, updated_at
                        ) VALUES (?, ?, ?, ?, 'active', ?, ?)
                    ''', (service_id, service_name, kwargs.get('education_type'),
                          kwargs.get('description'), now, now))
                    conn.commit()
                    logger.info(f'创建IT服务: {service_name} ({service_id})')
                    return {'success': True, 'service_id': service_id}
        except Exception as e:
            logger.error(f'创建IT服务失败: {e}')
            return {'success': False, 'error': str(e)}

    def add_service_level(self, service_id: str, sla_name: str, **kwargs) -> Dict[str, Any]:
        try:
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('INSERT INTO service_levels (service_id, sla_name, sla_code, target_value, actual_value, status) VALUES (?, ?, ?, ?, ?, ?)',
                                 (service_id, sla_name, kwargs.get('sla_code'),
                                  kwargs.get('target_value'), kwargs.get('actual_value'),
                                  kwargs.get('status', 'active')))
                    conn.commit()
                    return {'success': True}
        except Exception as e:
            logger.error(f'添加服务级别失败: {e}')
            return {'success': False, 'error': str(e)}

    def update_service_status(self, service_id: str, status: str) -> Dict[str, Any]:
        try:
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('UPDATE it_service_management SET status = ?, updated_at = ? WHERE service_id = ?',
                                 (status, now, service_id))
                    if cursor.rowcount > 0:
                        conn.commit()
                        return {'success': True, 'status': status}
                    return {'success': False, 'error': 'IT服务不存在'}
        except Exception as e:
            logger.error(f'更新服务状态失败: {e}')
            return {'success': False, 'error': str(e)}

    def list_it_services(self, education_type: str = None, status: str = None,
                         page: int = 1, page_size: int = 20) -> Dict[str, Any]:
        try:
            with self._get_connection() as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                query = 'SELECT * FROM it_service_management WHERE 1=1'
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
                services = [dict(s) for s in cursor.fetchall()]
                return {'success': True, 'services': services, 'total': total, 'page': page, 'page_size': page_size}
        except Exception as e:
            logger.error(f'获取IT服务列表失败: {e}')
            return {'success': False, 'error': str(e)}

    # ========== IT投资管理 ==========

    def create_it_investment(self, investment_name: str, **kwargs) -> Dict[str, Any]:
        try:
            investment_id = f"inv_{uuid.uuid4().hex[:12]}"
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('''
                        INSERT INTO it_investment (
                            investment_id, investment_name, education_type,
                            budget_amount, actual_amount, status, created_at, updated_at
                        ) VALUES (?, ?, ?, ?, 0, ?, ?, ?)
                    ''', (investment_id, investment_name, kwargs.get('education_type'),
                          kwargs.get('budget_amount', 0), kwargs.get('status', 'planning'),
                          now, now))
                    conn.commit()
                    logger.info(f'创建IT投资: {investment_name} ({investment_id})')
                    return {'success': True, 'investment_id': investment_id}
        except Exception as e:
            logger.error(f'创建IT投资失败: {e}')
            return {'success': False, 'error': str(e)}

    def add_investment_project(self, investment_id: str, project_name: str, **kwargs) -> Dict[str, Any]:
        try:
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('INSERT INTO investment_projects (investment_id, project_name, project_code, budget, actual_cost, status) VALUES (?, ?, ?, ?, 0, ?)',
                                 (investment_id, project_name, kwargs.get('project_code'),
                                  kwargs.get('budget', 0), kwargs.get('status', 'pending')))
                    conn.commit()
                    return {'success': True}
        except Exception as e:
            logger.error(f'添加投资项目失败: {e}')
            return {'success': False, 'error': str(e)}

    def update_investment_status(self, investment_id: str, status: str) -> Dict[str, Any]:
        try:
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('UPDATE it_investment SET status = ?, updated_at = ? WHERE investment_id = ?',
                                 (status, now, investment_id))
                    if cursor.rowcount > 0:
                        conn.commit()
                        return {'success': True, 'status': status}
                    return {'success': False, 'error': 'IT投资不存在'}
        except Exception as e:
            logger.error(f'更新投资状态失败: {e}')
            return {'success': False, 'error': str(e)}

    def list_it_investments(self, education_type: str = None, status: str = None,
                            page: int = 1, page_size: int = 20) -> Dict[str, Any]:
        try:
            with self._get_connection() as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                query = 'SELECT * FROM it_investment WHERE 1=1'
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
                investments = [dict(i) for i in cursor.fetchall()]
                return {'success': True, 'investments': investments, 'total': total, 'page': page, 'page_size': page_size}
        except Exception as e:
            logger.error(f'获取IT投资列表失败: {e}')
            return {'success': False, 'error': str(e)}

    # ========== IT绩效评估 ==========

    def create_it_performance(self, performance_name: str, **kwargs) -> Dict[str, Any]:
        try:
            performance_id = f"prf_{uuid.uuid4().hex[:12]}"
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('''
                        INSERT INTO it_performance (
                            performance_id, performance_name, education_type,
                            description, period, status, created_at, updated_at
                        ) VALUES (?, ?, ?, ?, ?, 'active', ?, ?)
                    ''', (performance_id, performance_name, kwargs.get('education_type'),
                          kwargs.get('description'), kwargs.get('period', 'yearly'),
                          now, now))
                    conn.commit()
                    logger.info(f'创建IT绩效: {performance_name} ({performance_id})')
                    return {'success': True, 'performance_id': performance_id}
        except Exception as e:
            logger.error(f'创建IT绩效失败: {e}')
            return {'success': False, 'error': str(e)}

    def add_performance_metric(self, performance_id: str, metric_name: str, **kwargs) -> Dict[str, Any]:
        try:
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('INSERT INTO performance_metrics (performance_id, metric_name, metric_code, target_value, actual_value, unit) VALUES (?, ?, ?, ?, ?, ?)',
                                 (performance_id, metric_name, kwargs.get('metric_code'),
                                  kwargs.get('target_value'), kwargs.get('actual_value'),
                                  kwargs.get('unit')))
                    conn.commit()
                    return {'success': True}
        except Exception as e:
            logger.error(f'添加绩效指标失败: {e}')
            return {'success': False, 'error': str(e)}

    def update_performance_metric(self, metric_id: int, **kwargs) -> Dict[str, Any]:
        try:
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    updates = []
                    params = []
                    if 'actual_value' in kwargs:
                        updates.append('actual_value = ?')
                        params.append(kwargs['actual_value'])
                    if 'target_value' in kwargs:
                        updates.append('target_value = ?')
                        params.append(kwargs['target_value'])
                    if not updates:
                        return {'success': False, 'error': '未提供更新字段'}
                    params.append(metric_id)
                    cursor.execute(f'UPDATE performance_metrics SET {", ".join(updates)} WHERE id = ?', params)
                    if cursor.rowcount > 0:
                        conn.commit()
                        return {'success': True}
                    return {'success': False, 'error': '绩效指标不存在'}
        except Exception as e:
            logger.error(f'更新绩效指标失败: {e}')
            return {'success': False, 'error': str(e)}

    def list_it_performance(self, education_type: str = None, status: str = None,
                            page: int = 1, page_size: int = 20) -> Dict[str, Any]:
        try:
            with self._get_connection() as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                query = 'SELECT * FROM it_performance WHERE 1=1'
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
                records = [dict(r) for r in cursor.fetchall()]
                return {'success': True, 'records': records, 'total': total, 'page': page, 'page_size': page_size}
        except Exception as e:
            logger.error(f'获取IT绩效列表失败: {e}')
            return {'success': False, 'error': str(e)}

    # ========== 项目管理 ==========

    def create_it_project(self, project_name: str, **kwargs) -> Dict[str, Any]:
        try:
            project_id = f"prj_{uuid.uuid4().hex[:12]}"
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('''
                        INSERT INTO it_projects (
                            project_id, project_name, education_type,
                            description, status, priority, budget, progress,
                            start_date, end_date, created_at, updated_at
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, 0, ?, ?, ?, ?)
                    ''', (project_id, project_name, kwargs.get('education_type'),
                          kwargs.get('description'), kwargs.get('status', 'planning'),
                          kwargs.get('priority', 'medium'), kwargs.get('budget', 0),
                          kwargs.get('start_date'), kwargs.get('end_date'), now, now))
                    conn.commit()
                    logger.info(f'创建IT项目: {project_name} ({project_id})')
                    return {'success': True, 'project_id': project_id}
        except Exception as e:
            logger.error(f'创建IT项目失败: {e}')
            return {'success': False, 'error': str(e)}

    def update_project_status(self, project_id: str, status: str, **kwargs) -> Dict[str, Any]:
        try:
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('UPDATE it_projects SET status = ?, updated_at = ? WHERE project_id = ?',
                                 (status, now, project_id))
                    if cursor.rowcount > 0:
                        cursor.execute('INSERT INTO project_status (project_id, status, status_date, comment) VALUES (?, ?, ?, ?)',
                                     (project_id, status, now[:10], kwargs.get('comment')))
                        conn.commit()
                        return {'success': True, 'status': status}
                    return {'success': False, 'error': 'IT项目不存在'}
        except Exception as e:
            logger.error(f'更新项目状态失败: {e}')
            return {'success': False, 'error': str(e)}

    def update_project_progress(self, project_id: str, progress: float) -> Dict[str, Any]:
        try:
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('UPDATE it_projects SET progress = ?, updated_at = ? WHERE project_id = ?',
                                 (progress, now, project_id))
                    if cursor.rowcount > 0:
                        conn.commit()
                        return {'success': True, 'progress': progress}
                    return {'success': False, 'error': 'IT项目不存在'}
        except Exception as e:
            logger.error(f'更新项目进度失败: {e}')
            return {'success': False, 'error': str(e)}

    def list_it_projects(self, education_type: str = None, status: str = None,
                         page: int = 1, page_size: int = 20) -> Dict[str, Any]:
        try:
            with self._get_connection() as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                query = 'SELECT * FROM it_projects WHERE 1=1'
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
                projects = [dict(p) for p in cursor.fetchall()]
                return {'success': True, 'projects': projects, 'total': total, 'page': page, 'page_size': page_size}
        except Exception as e:
            logger.error(f'获取IT项目列表失败: {e}')
            return {'success': False, 'error': str(e)}

    # ========== 统计 ==========

    def get_statistics(self, education_type: str = None) -> Dict[str, Any]:
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                stats = {}
                tables = [
                    ('it_governance', 'governance_count'),
                    ('information_systems', 'system_count'),
                    ('technology_architecture', 'architecture_count'),
                    ('data_governance', 'data_governance_count'),
                    ('security_governance', 'security_governance_count'),
                    ('it_service_management', 'service_count'),
                    ('it_investment', 'investment_count'),
                    ('it_performance', 'performance_count'),
                    ('it_projects', 'project_count'),
                    ('it_assets', 'asset_count')
                ]
                for table, key in tables:
                    if education_type:
                        cursor.execute(f'SELECT COUNT(*) FROM {table} WHERE education_type = ?', (education_type,))
                    else:
                        cursor.execute(f'SELECT COUNT(*) FROM {table}')
                    stats[key] = cursor.fetchone()[0]
                cursor.execute('SELECT status, COUNT(*) FROM it_projects GROUP BY status')
                project_status = cursor.fetchall()
                stats['project_status_distribution'] = {status: count for status, count in project_status}
                if education_type:
                    cursor.execute('SELECT SUM(budget_amount), SUM(actual_amount) FROM it_investment WHERE education_type = ?', (education_type,))
                else:
                    cursor.execute('SELECT SUM(budget_amount), SUM(actual_amount) FROM it_investment')
                investment_data = cursor.fetchone()
                stats['total_budget'] = investment_data[0] or 0
                stats['total_actual'] = investment_data[1] or 0
                return {'success': True, 'statistics': stats}
        except Exception as e:
            logger.error(f'获取统计数据失败: {e}')
            return {'success': False, 'error': str(e)}