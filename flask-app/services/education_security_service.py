#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
MTSCOS 教育安全保障服务 (v15.26.0)
====================================
提供校园安全、网络安全、食品安全、消防安全、交通安全、应急管理、安全培训和安全评估等综合管理服务。

核心能力：
1. 校园安全管理 - 门禁管理、巡逻管理、监控管理、访客管理、安保人员、安全设施、安全事件、安全预警
2. 网络安全管理 - 防火墙、入侵检测、病毒防护、数据加密、访问控制、安全审计、网络监控、漏洞管理
3. 食品安全管理 - 食材采购、食品加工、食品储存、卫生检查、从业人员、食品留样、营养配餐、食品安全事件
4. 消防安全管理 - 消防设施、消防检查、消防演练、火灾隐患、消防培训、消防安全档案、消防预案、火灾事故
5. 交通安全管理 - 车辆管理、停车管理、交通设施、交通安全宣传、交通事故、交通应急预案、校车管理、步行安全
6. 应急管理 - 应急预案、应急演练、应急物资、应急队伍、应急响应、应急指挥、应急评估、应急改进
7. 安全培训 - 安全教育、安全演练、安全讲座、安全手册、安全考核、安全证书、安全宣传、安全咨询
8. 安全评估 - 风险评估、安全检查、隐患排查、安全等级、安全报告、安全整改、安全复查、安全统计

差异化支持：成人教育 / K12教育
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
            os.path.join(os.path.dirname(os.path.abspath(__file__)), 'education_security_service.log'),
            encoding='utf-8'
        ),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger('EducationSecurity')


# ========== 安全配置 ==========

CAMPUS_SECURITY = {
    'access_control': {'name': '门禁管理', 'features': ['刷卡门禁', '人脸识别', '访客登记', '权限管理']},
    'patrol': {'name': '巡逻管理', 'features': ['巡逻路线', '巡逻签到', '异常上报', '巡逻记录']},
    'monitoring': {'name': '监控管理', 'features': ['视频监控', '录像回放', '异常检测', '监控覆盖']},
    'visitor': {'name': '访客管理', 'features': ['访客预约', '身份验证', '访问记录', '离开登记']},
    'security_staff': {'name': '安保人员', 'features': ['人员档案', '排班管理', '培训记录', '绩效评估']},
    'facilities': {'name': '安全设施', 'features': ['设施登记', '维护保养', '检查记录', '更换记录']},
    'incidents': {'name': '安全事件', 'features': ['事件上报', '事件处理', '事件跟踪', '事件分析']},
    'warning': {'name': '安全预警', 'features': ['风险预警', '预警通知', '预警处置', '预警统计']}
}

NETWORK_SECURITY = {
    'firewall': {'name': '防火墙', 'features': ['规则配置', '流量监控', '入侵拦截', '日志审计']},
    'ids': {'name': '入侵检测', 'features': ['实时检测', '威胁告警', '攻击溯源', '行为分析']},
    'antivirus': {'name': '病毒防护', 'features': ['病毒查杀', '实时监控', '病毒库更新', '隔离处理']},
    'encryption': {'name': '数据加密', 'features': ['传输加密', '存储加密', '密钥管理', '加密审计']},
    'access_control': {'name': '访问控制', 'features': ['用户认证', '权限管理', '访问日志', '异常行为']},
    'audit': {'name': '安全审计', 'features': ['日志收集', '行为分析', '合规检查', '审计报告']},
    'monitoring': {'name': '网络监控', 'features': ['流量分析', '设备监控', '性能告警', '拓扑管理']},
    'vulnerability': {'name': '漏洞管理', 'features': ['漏洞扫描', '漏洞评估', '补丁管理', '修复跟踪']}
}

FOOD_SECURITY = {
    'procurement': {'name': '食材采购', 'features': ['供应商管理', '采购验收', '索证索票', '质量检测']},
    'processing': {'name': '食品加工', 'features': ['加工流程', '卫生规范', '操作记录', '温度控制']},
    'storage': {'name': '食品储存', 'features': ['仓储管理', '保质期管理', '温湿度监控', '库存盘点']},
    'sanitation': {'name': '卫生检查', 'features': ['卫生标准', '检查记录', '问题整改', '卫生评级']},
    'staff': {'name': '从业人员', 'features': ['健康证明', '培训考核', '资质管理', '卫生习惯']},
    'sample': {'name': '食品留样', 'features': ['留样管理', '留样记录', '留样期限', '异常检测']},
    'nutrition': {'name': '营养配餐', 'features': ['营养均衡', '食谱制定', '特殊饮食', '营养分析']},
    'incidents': {'name': '食品安全事件', 'features': ['事件上报', '调查处理', '原因分析', '整改措施']}
}

FIRE_SECURITY = {
    'facilities': {'name': '消防设施', 'features': ['设施登记', '定期检查', '维护保养', '检测报告']},
    'inspection': {'name': '消防检查', 'features': ['日常检查', '专项检查', '问题整改', '检查记录']},
    'drill': {'name': '消防演练', 'features': ['演练计划', '演练实施', '演练评估', '改进措施']},
    'hazard': {'name': '火灾隐患', 'features': ['隐患排查', '隐患分级', '隐患整改', '隐患跟踪']},
    'training': {'name': '消防培训', 'features': ['培训课程', '培训记录', '考核认证', '技能提升']},
    'archives': {'name': '消防安全档案', 'features': ['档案管理', '资料归档', '查阅检索', '档案更新']},
    'plan': {'name': '消防预案', 'features': ['预案制定', '预案演练', '预案修订', '预案执行']},
    'accident': {'name': '火灾事故', 'features': ['事故上报', '事故调查', '原因分析', '责任认定']}
}

TRAFFIC_SECURITY = {
    'vehicle': {'name': '车辆管理', 'features': ['车辆登记', '出入管理', '违规处理', '车辆年检']},
    'parking': {'name': '停车管理', 'features': ['车位管理', '停车收费', '违停处理', '停车统计']},
    'facilities': {'name': '交通设施', 'features': ['设施维护', '标志标线', '照明设施', '道路养护']},
    'promotion': {'name': '交通安全宣传', 'features': ['宣传活动', '宣传资料', '宣传效果', '宣传统计']},
    'accident': {'name': '交通事故', 'features': ['事故上报', '事故处理', '责任认定', '事故分析']},
    'emergency': {'name': '交通应急预案', 'features': ['预案制定', '预案演练', '应急响应', '预案评估']},
    'school_bus': {'name': '校车管理', 'features': ['校车登记', '司机资质', '运行路线', '安全检查']},
    'pedestrian': {'name': '步行安全', 'features': ['步行路线', '安全指引', '护导管理', '安全提醒']}
}

EMERGENCY_MANAGEMENT = {
    'plan': {'name': '应急预案', 'features': ['预案编制', '预案审核', '预案发布', '预案修订']},
    'drill': {'name': '应急演练', 'features': ['演练计划', '演练组织', '演练评估', '演练复盘']},
    'materials': {'name': '应急物资', 'features': ['物资储备', '物资管理', '物资调拨', '物资补充']},
    'team': {'name': '应急队伍', 'features': ['队伍组建', '人员培训', '装备配置', '演练考核']},
    'response': {'name': '应急响应', 'features': ['响应启动', '指挥协调', '资源调度', '现场处置']},
    'command': {'name': '应急指挥', 'features': ['指挥体系', '信息报送', '决策支持', '指挥记录']},
    'evaluation': {'name': '应急评估', 'features': ['评估标准', '评估实施', '评估报告', '改进建议']},
    'improvement': {'name': '应急改进', 'features': ['问题分析', '整改措施', '跟踪落实', '效果评估']}
}

SAFETY_TRAINING = {
    'education': {'name': '安全教育', 'features': ['课程设置', '教学计划', '授课记录', '学习反馈']},
    'drill': {'name': '安全演练', 'features': ['演练项目', '演练组织', '演练记录', '演练评估']},
    'lecture': {'name': '安全讲座', 'features': ['讲座安排', '讲座内容', '参与记录', '效果评估']},
    'manual': {'name': '安全手册', 'features': ['手册编制', '手册发放', '手册更新', '学习考核']},
    'assessment': {'name': '安全考核', 'features': ['考核题库', '考核安排', '成绩管理', '考核分析']},
    'certificate': {'name': '安全证书', 'features': ['证书颁发', '证书管理', '证书查询', '证书失效']},
    'promotion': {'name': '安全宣传', 'features': ['宣传活动', '宣传材料', '宣传渠道', '宣传效果']},
    'consultation': {'name': '安全咨询', 'features': ['咨询服务', '咨询记录', '问题解答', '咨询统计']}
}

SECURITY_ASSESSMENT = {
    'risk': {'name': '风险评估', 'features': ['风险识别', '风险分析', '风险评价', '风险控制']},
    'inspection': {'name': '安全检查', 'features': ['检查计划', '检查实施', '问题记录', '检查报告']},
    'hazard': {'name': '隐患排查', 'features': ['隐患发现', '隐患分级', '隐患整改', '整改验收']},
    'level': {'name': '安全等级', 'features': ['等级评定', '等级公示', '等级调整', '等级管理']},
    'report': {'name': '安全报告', 'features': ['报告编制', '报告审核', '报告发布', '报告归档']},
    'rectification': {'name': '安全整改', 'features': ['整改方案', '整改实施', '整改跟踪', '整改验收']},
    'review': {'name': '安全复查', 'features': ['复查计划', '复查实施', '复查记录', '复查结论']},
    'statistics': {'name': '安全统计', 'features': ['数据统计', '趋势分析', '报表生成', '统计报告']}
}


class EducationSecurityService:
    """教育安全保障服务"""

    def __init__(self):
        self.db_path = DATABASE_PATH
        self._lock = threading.RLock()
        self._init_db()

    def _get_connection(self):
        return sqlite3.connect(self.db_path)

    def _init_db(self):
        try:
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()

                    cursor.execute('''
                        CREATE TABLE IF NOT EXISTS campus_security (
                            security_id TEXT PRIMARY KEY,
                            security_type TEXT NOT NULL,
                            name TEXT NOT NULL,
                            education_type TEXT,
                            location TEXT,
                            description TEXT,
                            status TEXT DEFAULT 'active',
                            created_at TEXT,
                            updated_at TEXT
                        )
                    ''')

                    cursor.execute('''
                        CREATE TABLE IF NOT EXISTS security_records (
                            record_id TEXT PRIMARY KEY,
                            security_id TEXT NOT NULL,
                            record_type TEXT NOT NULL,
                            content TEXT,
                            operator TEXT,
                            operator_id INTEGER,
                            record_time TEXT,
                            education_type TEXT,
                            FOREIGN KEY (security_id) REFERENCES campus_security(security_id)
                        )
                    ''')

                    cursor.execute('''
                        CREATE TABLE IF NOT EXISTS network_security (
                            security_id TEXT PRIMARY KEY,
                            security_type TEXT NOT NULL,
                            name TEXT NOT NULL,
                            education_type TEXT,
                            device_name TEXT,
                            ip_address TEXT,
                            status TEXT DEFAULT 'active',
                            last_scan TEXT,
                            created_at TEXT,
                            updated_at TEXT
                        )
                    ''')

                    cursor.execute('''
                        CREATE TABLE IF NOT EXISTS network_records (
                            record_id TEXT PRIMARY KEY,
                            security_id TEXT NOT NULL,
                            record_type TEXT NOT NULL,
                            content TEXT,
                            severity TEXT,
                            operator TEXT,
                            record_time TEXT,
                            education_type TEXT,
                            FOREIGN KEY (security_id) REFERENCES network_security(security_id)
                        )
                    ''')

                    cursor.execute('''
                        CREATE TABLE IF NOT EXISTS food_security (
                            security_id TEXT PRIMARY KEY,
                            security_type TEXT NOT NULL,
                            name TEXT NOT NULL,
                            education_type TEXT,
                            supplier TEXT,
                            location TEXT,
                            status TEXT DEFAULT 'active',
                            last_inspection TEXT,
                            created_at TEXT,
                            updated_at TEXT
                        )
                    ''')

                    cursor.execute('''
                        CREATE TABLE IF NOT EXISTS food_records (
                            record_id TEXT PRIMARY KEY,
                            security_id TEXT NOT NULL,
                            record_type TEXT NOT NULL,
                            content TEXT,
                            inspector TEXT,
                            result TEXT,
                            record_time TEXT,
                            education_type TEXT,
                            FOREIGN KEY (security_id) REFERENCES food_security(security_id)
                        )
                    ''')

                    cursor.execute('''
                        CREATE TABLE IF NOT EXISTS fire_security (
                            security_id TEXT PRIMARY KEY,
                            security_type TEXT NOT NULL,
                            name TEXT NOT NULL,
                            education_type TEXT,
                            location TEXT,
                            equipment_type TEXT,
                            status TEXT DEFAULT 'active',
                            last_check TEXT,
                            next_check TEXT,
                            created_at TEXT,
                            updated_at TEXT
                        )
                    ''')

                    cursor.execute('''
                        CREATE TABLE IF NOT EXISTS fire_records (
                            record_id TEXT PRIMARY KEY,
                            security_id TEXT NOT NULL,
                            record_type TEXT NOT NULL,
                            content TEXT,
                            operator TEXT,
                            result TEXT,
                            record_time TEXT,
                            education_type TEXT,
                            FOREIGN KEY (security_id) REFERENCES fire_security(security_id)
                        )
                    ''')

                    cursor.execute('''
                        CREATE TABLE IF NOT EXISTS traffic_security (
                            security_id TEXT PRIMARY KEY,
                            security_type TEXT NOT NULL,
                            name TEXT NOT NULL,
                            education_type TEXT,
                            location TEXT,
                            vehicle_type TEXT,
                            status TEXT DEFAULT 'active',
                            last_audit TEXT,
                            created_at TEXT,
                            updated_at TEXT
                        )
                    ''')

                    cursor.execute('''
                        CREATE TABLE IF NOT EXISTS traffic_records (
                            record_id TEXT PRIMARY KEY,
                            security_id TEXT NOT NULL,
                            record_type TEXT NOT NULL,
                            content TEXT,
                            operator TEXT,
                            result TEXT,
                            record_time TEXT,
                            education_type TEXT,
                            FOREIGN KEY (security_id) REFERENCES traffic_security(security_id)
                        )
                    ''')

                    cursor.execute('''
                        CREATE TABLE IF NOT EXISTS emergency_management (
                            emergency_id TEXT PRIMARY KEY,
                            emergency_type TEXT NOT NULL,
                            name TEXT NOT NULL,
                            education_type TEXT,
                            description TEXT,
                            scope TEXT,
                            status TEXT DEFAULT 'draft',
                            created_at TEXT,
                            updated_at TEXT
                        )
                    ''')

                    cursor.execute('''
                        CREATE TABLE IF NOT EXISTS emergency_records (
                            record_id TEXT PRIMARY KEY,
                            emergency_id TEXT NOT NULL,
                            record_type TEXT NOT NULL,
                            content TEXT,
                            operator TEXT,
                            result TEXT,
                            record_time TEXT,
                            education_type TEXT,
                            FOREIGN KEY (emergency_id) REFERENCES emergency_management(emergency_id)
                        )
                    ''')

                    cursor.execute('''
                        CREATE TABLE IF NOT EXISTS safety_training (
                            training_id TEXT PRIMARY KEY,
                            training_type TEXT NOT NULL,
                            name TEXT NOT NULL,
                            education_type TEXT,
                            description TEXT,
                            target_audience TEXT,
                            status TEXT DEFAULT 'planned',
                            start_date TEXT,
                            end_date TEXT,
                            created_at TEXT,
                            updated_at TEXT
                        )
                    ''')

                    cursor.execute('''
                        CREATE TABLE IF NOT EXISTS training_records (
                            record_id TEXT PRIMARY KEY,
                            training_id TEXT NOT NULL,
                            record_type TEXT NOT NULL,
                            content TEXT,
                            participant_id INTEGER,
                            participant_name TEXT,
                            result TEXT,
                            record_time TEXT,
                            education_type TEXT,
                            FOREIGN KEY (training_id) REFERENCES safety_training(training_id)
                        )
                    ''')

                    cursor.execute('''
                        CREATE TABLE IF NOT EXISTS security_assessment (
                            assessment_id TEXT PRIMARY KEY,
                            assessment_type TEXT NOT NULL,
                            name TEXT NOT NULL,
                            education_type TEXT,
                            description TEXT,
                            scope TEXT,
                            status TEXT DEFAULT 'in_progress',
                            start_date TEXT,
                            end_date TEXT,
                            created_at TEXT,
                            updated_at TEXT
                        )
                    ''')

                    cursor.execute('''
                        CREATE TABLE IF NOT EXISTS assessment_records (
                            record_id TEXT PRIMARY KEY,
                            assessment_id TEXT NOT NULL,
                            record_type TEXT NOT NULL,
                            content TEXT,
                            assessor TEXT,
                            result TEXT,
                            score REAL,
                            record_time TEXT,
                            education_type TEXT,
                            FOREIGN KEY (assessment_id) REFERENCES security_assessment(assessment_id)
                        )
                    ''')

                    conn.commit()
                    logger.info('教育安全保障服务数据库初始化完成')
        except Exception as e:
            logger.error(f'数据库初始化失败: {e}')

    # ========== 校园安全管理 ==========

    def create_campus_security(self, security_type: str, name: str,
                               education_type: str, **kwargs) -> Dict[str, Any]:
        try:
            security_id = f"csm_{uuid.uuid4().hex[:12]}"
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('''
                        INSERT INTO campus_security (
                            security_id, security_type, name, education_type,
                            location, description, status, created_at, updated_at
                        ) VALUES (?, ?, ?, ?, ?, ?, 'active', ?, ?)
                    ''', (security_id, security_type, name, education_type,
                          kwargs.get('location'), kwargs.get('description'), now, now))
                    conn.commit()
                    logger.info(f'创建校园安全记录: {name} ({security_id})')
                    return {'success': True, 'security_id': security_id}
        except Exception as e:
            logger.error(f'创建校园安全记录失败: {e}')
            return {'success': False, 'error': str(e)}

    def record_security_event(self, security_id: str, record_type: str,
                              content: str, **kwargs) -> Dict[str, Any]:
        try:
            record_id = f"csr_{uuid.uuid4().hex[:12]}"
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('''
                        INSERT INTO security_records (
                            record_id, security_id, record_type, content,
                            operator, operator_id, record_time, education_type
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                    ''', (record_id, security_id, record_type, content,
                          kwargs.get('operator'), kwargs.get('operator_id'),
                          now, kwargs.get('education_type')))
                    conn.commit()
                    return {'success': True, 'record_id': record_id}
        except Exception as e:
            logger.error(f'记录安全事件失败: {e}')
            return {'success': False, 'error': str(e)}

    def update_campus_security(self, security_id: str, **kwargs) -> Dict[str, Any]:
        try:
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    update_fields = []
                    params = []
                    if 'name' in kwargs:
                        update_fields.append('name = ?')
                        params.append(kwargs['name'])
                    if 'location' in kwargs:
                        update_fields.append('location = ?')
                        params.append(kwargs['location'])
                    if 'description' in kwargs:
                        update_fields.append('description = ?')
                        params.append(kwargs['description'])
                    if 'status' in kwargs:
                        update_fields.append('status = ?')
                        params.append(kwargs['status'])
                    if update_fields:
                        update_fields.append('updated_at = ?')
                        params.append(now)
                        params.append(security_id)
                        cursor.execute(f'UPDATE campus_security SET {", ".join(update_fields)} WHERE security_id = ?', params)
                        if cursor.rowcount > 0:
                            conn.commit()
                            return {'success': True}
                    return {'success': False, 'error': '未找到记录或无更新内容'}
        except Exception as e:
            logger.error(f'更新校园安全记录失败: {e}')
            return {'success': False, 'error': str(e)}

    def list_campus_security(self, security_type: str = None,
                             education_type: str = None,
                             status: str = None, page: int = 1,
                             page_size: int = 20) -> Dict[str, Any]:
        try:
            with self._get_connection() as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                query = 'SELECT * FROM campus_security WHERE 1=1'
                params = []
                if security_type:
                    query += ' AND security_type = ?'
                    params.append(security_type)
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
            logger.error(f'获取校园安全列表失败: {e}')
            return {'success': False, 'error': str(e)}

    # ========== 网络安全管理 ==========

    def create_network_security(self, security_type: str, name: str,
                                education_type: str, **kwargs) -> Dict[str, Any]:
        try:
            security_id = f"nwm_{uuid.uuid4().hex[:12]}"
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('''
                        INSERT INTO network_security (
                            security_id, security_type, name, education_type,
                            device_name, ip_address, status, last_scan,
                            created_at, updated_at
                        ) VALUES (?, ?, ?, ?, ?, ?, 'active', NULL, ?, ?)
                    ''', (security_id, security_type, name, education_type,
                          kwargs.get('device_name'), kwargs.get('ip_address'), now, now))
                    conn.commit()
                    logger.info(f'创建网络安全记录: {name} ({security_id})')
                    return {'success': True, 'security_id': security_id}
        except Exception as e:
            logger.error(f'创建网络安全记录失败: {e}')
            return {'success': False, 'error': str(e)}

    def record_network_event(self, security_id: str, record_type: str,
                             content: str, **kwargs) -> Dict[str, Any]:
        try:
            record_id = f"nwr_{uuid.uuid4().hex[:12]}"
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('''
                        INSERT INTO network_records (
                            record_id, security_id, record_type, content,
                            severity, operator, record_time, education_type
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                    ''', (record_id, security_id, record_type, content,
                          kwargs.get('severity', 'medium'), kwargs.get('operator'),
                          now, kwargs.get('education_type')))
                    if kwargs.get('severity') == 'critical':
                        cursor.execute('UPDATE network_security SET status = ?, updated_at = ? WHERE security_id = ?', ('warning', now, security_id))
                    conn.commit()
                    return {'success': True, 'record_id': record_id}
        except Exception as e:
            logger.error(f'记录网络安全事件失败: {e}')
            return {'success': False, 'error': str(e)}

    def update_network_security(self, security_id: str, **kwargs) -> Dict[str, Any]:
        try:
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    update_fields = []
                    params = []
                    if 'name' in kwargs:
                        update_fields.append('name = ?')
                        params.append(kwargs['name'])
                    if 'device_name' in kwargs:
                        update_fields.append('device_name = ?')
                        params.append(kwargs['device_name'])
                    if 'ip_address' in kwargs:
                        update_fields.append('ip_address = ?')
                        params.append(kwargs['ip_address'])
                    if 'status' in kwargs:
                        update_fields.append('status = ?')
                        params.append(kwargs['status'])
                    if 'last_scan' in kwargs:
                        update_fields.append('last_scan = ?')
                        params.append(kwargs['last_scan'])
                    if update_fields:
                        update_fields.append('updated_at = ?')
                        params.append(now)
                        params.append(security_id)
                        cursor.execute(f'UPDATE network_security SET {", ".join(update_fields)} WHERE security_id = ?', params)
                        if cursor.rowcount > 0:
                            conn.commit()
                            return {'success': True}
                    return {'success': False, 'error': '未找到记录或无更新内容'}
        except Exception as e:
            logger.error(f'更新网络安全记录失败: {e}')
            return {'success': False, 'error': str(e)}

    def list_network_security(self, security_type: str = None,
                              education_type: str = None,
                              status: str = None, page: int = 1,
                              page_size: int = 20) -> Dict[str, Any]:
        try:
            with self._get_connection() as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                query = 'SELECT * FROM network_security WHERE 1=1'
                params = []
                if security_type:
                    query += ' AND security_type = ?'
                    params.append(security_type)
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
            logger.error(f'获取网络安全列表失败: {e}')
            return {'success': False, 'error': str(e)}

    # ========== 食品安全管理 ==========

    def create_food_security(self, security_type: str, name: str,
                             education_type: str, **kwargs) -> Dict[str, Any]:
        try:
            security_id = f"fdm_{uuid.uuid4().hex[:12]}"
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('''
                        INSERT INTO food_security (
                            security_id, security_type, name, education_type,
                            supplier, location, status, last_inspection,
                            created_at, updated_at
                        ) VALUES (?, ?, ?, ?, ?, ?, 'active', NULL, ?, ?)
                    ''', (security_id, security_type, name, education_type,
                          kwargs.get('supplier'), kwargs.get('location'), now, now))
                    conn.commit()
                    logger.info(f'创建食品安全记录: {name} ({security_id})')
                    return {'success': True, 'security_id': security_id}
        except Exception as e:
            logger.error(f'创建食品安全记录失败: {e}')
            return {'success': False, 'error': str(e)}

    def record_food_inspection(self, security_id: str, record_type: str,
                               content: str, **kwargs) -> Dict[str, Any]:
        try:
            record_id = f"fdr_{uuid.uuid4().hex[:12]}"
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('''
                        INSERT INTO food_records (
                            record_id, security_id, record_type, content,
                            inspector, result, record_time, education_type
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                    ''', (record_id, security_id, record_type, content,
                          kwargs.get('inspector'), kwargs.get('result', 'pass'),
                          now, kwargs.get('education_type')))
                    if kwargs.get('record_type') == 'inspection':
                        cursor.execute('UPDATE food_security SET last_inspection = ?, updated_at = ? WHERE security_id = ?', (now[:10], now, security_id))
                    conn.commit()
                    return {'success': True, 'record_id': record_id}
        except Exception as e:
            logger.error(f'记录食品安全检查失败: {e}')
            return {'success': False, 'error': str(e)}

    def update_food_security(self, security_id: str, **kwargs) -> Dict[str, Any]:
        try:
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    update_fields = []
                    params = []
                    if 'name' in kwargs:
                        update_fields.append('name = ?')
                        params.append(kwargs['name'])
                    if 'supplier' in kwargs:
                        update_fields.append('supplier = ?')
                        params.append(kwargs['supplier'])
                    if 'location' in kwargs:
                        update_fields.append('location = ?')
                        params.append(kwargs['location'])
                    if 'status' in kwargs:
                        update_fields.append('status = ?')
                        params.append(kwargs['status'])
                    if 'last_inspection' in kwargs:
                        update_fields.append('last_inspection = ?')
                        params.append(kwargs['last_inspection'])
                    if update_fields:
                        update_fields.append('updated_at = ?')
                        params.append(now)
                        params.append(security_id)
                        cursor.execute(f'UPDATE food_security SET {", ".join(update_fields)} WHERE security_id = ?', params)
                        if cursor.rowcount > 0:
                            conn.commit()
                            return {'success': True}
                    return {'success': False, 'error': '未找到记录或无更新内容'}
        except Exception as e:
            logger.error(f'更新食品安全记录失败: {e}')
            return {'success': False, 'error': str(e)}

    def list_food_security(self, security_type: str = None,
                           education_type: str = None,
                           status: str = None, page: int = 1,
                           page_size: int = 20) -> Dict[str, Any]:
        try:
            with self._get_connection() as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                query = 'SELECT * FROM food_security WHERE 1=1'
                params = []
                if security_type:
                    query += ' AND security_type = ?'
                    params.append(security_type)
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
            logger.error(f'获取食品安全列表失败: {e}')
            return {'success': False, 'error': str(e)}

    # ========== 消防安全管理 ==========

    def create_fire_security(self, security_type: str, name: str,
                             education_type: str, **kwargs) -> Dict[str, Any]:
        try:
            security_id = f"frm_{uuid.uuid4().hex[:12]}"
            now = datetime.now().isoformat()
            next_check = (datetime.now() + timedelta(days=30)).strftime('%Y-%m-%d')
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('''
                        INSERT INTO fire_security (
                            security_id, security_type, name, education_type,
                            location, equipment_type, status, last_check,
                            next_check, created_at, updated_at
                        ) VALUES (?, ?, ?, ?, ?, ?, 'active', NULL, ?, ?, ?)
                    ''', (security_id, security_type, name, education_type,
                          kwargs.get('location'), kwargs.get('equipment_type'),
                          next_check, now, now))
                    conn.commit()
                    logger.info(f'创建消防安全记录: {name} ({security_id})')
                    return {'success': True, 'security_id': security_id}
        except Exception as e:
            logger.error(f'创建消防安全记录失败: {e}')
            return {'success': False, 'error': str(e)}

    def record_fire_check(self, security_id: str, record_type: str,
                          content: str, **kwargs) -> Dict[str, Any]:
        try:
            record_id = f"frr_{uuid.uuid4().hex[:12]}"
            now = datetime.now().isoformat()
            next_check = (datetime.now() + timedelta(days=30)).strftime('%Y-%m-%d')
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('''
                        INSERT INTO fire_records (
                            record_id, security_id, record_type, content,
                            operator, result, record_time, education_type
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                    ''', (record_id, security_id, record_type, content,
                          kwargs.get('operator'), kwargs.get('result', 'pass'),
                          now, kwargs.get('education_type')))
                    if record_type == 'inspection' or record_type == 'check':
                        cursor.execute('UPDATE fire_security SET last_check = ?, next_check = ?, updated_at = ? WHERE security_id = ?', (now[:10], next_check, now, security_id))
                    conn.commit()
                    return {'success': True, 'record_id': record_id}
        except Exception as e:
            logger.error(f'记录消防安全检查失败: {e}')
            return {'success': False, 'error': str(e)}

    def update_fire_security(self, security_id: str, **kwargs) -> Dict[str, Any]:
        try:
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    update_fields = []
                    params = []
                    if 'name' in kwargs:
                        update_fields.append('name = ?')
                        params.append(kwargs['name'])
                    if 'location' in kwargs:
                        update_fields.append('location = ?')
                        params.append(kwargs['location'])
                    if 'equipment_type' in kwargs:
                        update_fields.append('equipment_type = ?')
                        params.append(kwargs['equipment_type'])
                    if 'status' in kwargs:
                        update_fields.append('status = ?')
                        params.append(kwargs['status'])
                    if 'last_check' in kwargs:
                        update_fields.append('last_check = ?')
                        params.append(kwargs['last_check'])
                    if 'next_check' in kwargs:
                        update_fields.append('next_check = ?')
                        params.append(kwargs['next_check'])
                    if update_fields:
                        update_fields.append('updated_at = ?')
                        params.append(now)
                        params.append(security_id)
                        cursor.execute(f'UPDATE fire_security SET {", ".join(update_fields)} WHERE security_id = ?', params)
                        if cursor.rowcount > 0:
                            conn.commit()
                            return {'success': True}
                    return {'success': False, 'error': '未找到记录或无更新内容'}
        except Exception as e:
            logger.error(f'更新消防安全记录失败: {e}')
            return {'success': False, 'error': str(e)}

    def list_fire_security(self, security_type: str = None,
                           education_type: str = None,
                           status: str = None, page: int = 1,
                           page_size: int = 20) -> Dict[str, Any]:
        try:
            with self._get_connection() as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                query = 'SELECT * FROM fire_security WHERE 1=1'
                params = []
                if security_type:
                    query += ' AND security_type = ?'
                    params.append(security_type)
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
            logger.error(f'获取消防安全列表失败: {e}')
            return {'success': False, 'error': str(e)}

    def schedule_fire_drill(self, education_type: str, drill_date: str,
                            **kwargs) -> Dict[str, Any]:
        try:
            drill_id = f"fdr_{uuid.uuid4().hex[:12]}"
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('''
                        INSERT INTO fire_records (
                            record_id, security_id, record_type, content,
                            operator, result, record_time, education_type
                        ) VALUES (?, 'drill_scheduled', 'drill', ?, ?, 'scheduled', ?, ?)
                    ''', (drill_id, kwargs.get('description', f'{education_type}消防演练计划于{drill_date}'),
                          kwargs.get('operator'), now, education_type))
                    conn.commit()
                    return {'success': True, 'drill_id': drill_id}
        except Exception as e:
            logger.error(f'调度消防演练失败: {e}')
            return {'success': False, 'error': str(e)}

    # ========== 交通安全管理 ==========

    def create_traffic_security(self, security_type: str, name: str,
                                education_type: str, **kwargs) -> Dict[str, Any]:
        try:
            security_id = f"trm_{uuid.uuid4().hex[:12]}"
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('''
                        INSERT INTO traffic_security (
                            security_id, security_type, name, education_type,
                            location, vehicle_type, status, last_audit,
                            created_at, updated_at
                        ) VALUES (?, ?, ?, ?, ?, ?, 'active', NULL, ?, ?)
                    ''', (security_id, security_type, name, education_type,
                          kwargs.get('location'), kwargs.get('vehicle_type'), now, now))
                    conn.commit()
                    logger.info(f'创建交通安全记录: {name} ({security_id})')
                    return {'success': True, 'security_id': security_id}
        except Exception as e:
            logger.error(f'创建交通安全记录失败: {e}')
            return {'success': False, 'error': str(e)}

    def record_traffic_event(self, security_id: str, record_type: str,
                             content: str, **kwargs) -> Dict[str, Any]:
        try:
            record_id = f"trr_{uuid.uuid4().hex[:12]}"
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('''
                        INSERT INTO traffic_records (
                            record_id, security_id, record_type, content,
                            operator, result, record_time, education_type
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                    ''', (record_id, security_id, record_type, content,
                          kwargs.get('operator'), kwargs.get('result'),
                          now, kwargs.get('education_type')))
                    if record_type == 'accident':
                        cursor.execute('UPDATE traffic_security SET status = ?, updated_at = ? WHERE security_id = ?', ('incident', now, security_id))
                    conn.commit()
                    return {'success': True, 'record_id': record_id}
        except Exception as e:
            logger.error(f'记录交通安全事件失败: {e}')
            return {'success': False, 'error': str(e)}

    def update_traffic_security(self, security_id: str, **kwargs) -> Dict[str, Any]:
        try:
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    update_fields = []
                    params = []
                    if 'name' in kwargs:
                        update_fields.append('name = ?')
                        params.append(kwargs['name'])
                    if 'location' in kwargs:
                        update_fields.append('location = ?')
                        params.append(kwargs['location'])
                    if 'vehicle_type' in kwargs:
                        update_fields.append('vehicle_type = ?')
                        params.append(kwargs['vehicle_type'])
                    if 'status' in kwargs:
                        update_fields.append('status = ?')
                        params.append(kwargs['status'])
                    if 'last_audit' in kwargs:
                        update_fields.append('last_audit = ?')
                        params.append(kwargs['last_audit'])
                    if update_fields:
                        update_fields.append('updated_at = ?')
                        params.append(now)
                        params.append(security_id)
                        cursor.execute(f'UPDATE traffic_security SET {", ".join(update_fields)} WHERE security_id = ?', params)
                        if cursor.rowcount > 0:
                            conn.commit()
                            return {'success': True}
                    return {'success': False, 'error': '未找到记录或无更新内容'}
        except Exception as e:
            logger.error(f'更新交通安全记录失败: {e}')
            return {'success': False, 'error': str(e)}

    def list_traffic_security(self, security_type: str = None,
                              education_type: str = None,
                              status: str = None, page: int = 1,
                              page_size: int = 20) -> Dict[str, Any]:
        try:
            with self._get_connection() as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                query = 'SELECT * FROM traffic_security WHERE 1=1'
                params = []
                if security_type:
                    query += ' AND security_type = ?'
                    params.append(security_type)
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
            logger.error(f'获取交通安全列表失败: {e}')
            return {'success': False, 'error': str(e)}

    # ========== 应急管理 ==========

    def create_emergency_plan(self, emergency_type: str, name: str,
                              education_type: str, **kwargs) -> Dict[str, Any]:
        try:
            emergency_id = f"emg_{uuid.uuid4().hex[:12]}"
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('''
                        INSERT INTO emergency_management (
                            emergency_id, emergency_type, name, education_type,
                            description, scope, status, created_at, updated_at
                        ) VALUES (?, ?, ?, ?, ?, ?, 'draft', ?, ?)
                    ''', (emergency_id, emergency_type, name, education_type,
                          kwargs.get('description'), kwargs.get('scope'), now, now))
                    conn.commit()
                    logger.info(f'创建应急预案: {name} ({emergency_id})')
                    return {'success': True, 'emergency_id': emergency_id}
        except Exception as e:
            logger.error(f'创建应急预案失败: {e}')
            return {'success': False, 'error': str(e)}

    def record_emergency_event(self, emergency_id: str, record_type: str,
                               content: str, **kwargs) -> Dict[str, Any]:
        try:
            record_id = f"emr_{uuid.uuid4().hex[:12]}"
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('''
                        INSERT INTO emergency_records (
                            record_id, emergency_id, record_type, content,
                            operator, result, record_time, education_type
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                    ''', (record_id, emergency_id, record_type, content,
                          kwargs.get('operator'), kwargs.get('result'),
                          now, kwargs.get('education_type')))
                    if record_type == 'drill':
                        cursor.execute('UPDATE emergency_management SET status = ?, updated_at = ? WHERE emergency_id = ?', ('tested', now, emergency_id))
                    conn.commit()
                    return {'success': True, 'record_id': record_id}
        except Exception as e:
            logger.error(f'记录应急事件失败: {e}')
            return {'success': False, 'error': str(e)}

    def update_emergency_plan(self, emergency_id: str, **kwargs) -> Dict[str, Any]:
        try:
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    update_fields = []
                    params = []
                    if 'name' in kwargs:
                        update_fields.append('name = ?')
                        params.append(kwargs['name'])
                    if 'description' in kwargs:
                        update_fields.append('description = ?')
                        params.append(kwargs['description'])
                    if 'scope' in kwargs:
                        update_fields.append('scope = ?')
                        params.append(kwargs['scope'])
                    if 'status' in kwargs:
                        update_fields.append('status = ?')
                        params.append(kwargs['status'])
                    if update_fields:
                        update_fields.append('updated_at = ?')
                        params.append(now)
                        params.append(emergency_id)
                        cursor.execute(f'UPDATE emergency_management SET {", ".join(update_fields)} WHERE emergency_id = ?', params)
                        if cursor.rowcount > 0:
                            conn.commit()
                            return {'success': True}
                    return {'success': False, 'error': '未找到记录或无更新内容'}
        except Exception as e:
            logger.error(f'更新应急预案失败: {e}')
            return {'success': False, 'error': str(e)}

    def list_emergency_plans(self, emergency_type: str = None,
                             education_type: str = None,
                             status: str = None, page: int = 1,
                             page_size: int = 20) -> Dict[str, Any]:
        try:
            with self._get_connection() as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                query = 'SELECT * FROM emergency_management WHERE 1=1'
                params = []
                if emergency_type:
                    query += ' AND emergency_type = ?'
                    params.append(emergency_type)
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
            logger.error(f'获取应急预案列表失败: {e}')
            return {'success': False, 'error': str(e)}

    # ========== 安全培训 ==========

    def create_safety_training(self, training_type: str, name: str,
                               education_type: str, **kwargs) -> Dict[str, Any]:
        try:
            training_id = f"stm_{uuid.uuid4().hex[:12]}"
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('''
                        INSERT INTO safety_training (
                            training_id, training_type, name, education_type,
                            description, target_audience, status, start_date,
                            end_date, created_at, updated_at
                        ) VALUES (?, ?, ?, ?, ?, ?, 'planned', ?, ?, ?, ?)
                    ''', (training_id, training_type, name, education_type,
                          kwargs.get('description'), kwargs.get('target_audience'),
                          kwargs.get('start_date'), kwargs.get('end_date'), now, now))
                    conn.commit()
                    logger.info(f'创建安全培训: {name} ({training_id})')
                    return {'success': True, 'training_id': training_id}
        except Exception as e:
            logger.error(f'创建安全培训失败: {e}')
            return {'success': False, 'error': str(e)}

    def record_training_participation(self, training_id: str, participant_id: int,
                                      participant_name: str, **kwargs) -> Dict[str, Any]:
        try:
            record_id = f"str_{uuid.uuid4().hex[:12]}"
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('''
                        INSERT INTO training_records (
                            record_id, training_id, record_type, content,
                            participant_id, participant_name, result,
                            record_time, education_type
                        ) VALUES (?, ?, 'participation', ?, ?, ?, ?, ?, ?)
                    ''', (record_id, training_id, kwargs.get('content', '参训'),
                          participant_id, participant_name,
                          kwargs.get('result', 'completed'), now,
                          kwargs.get('education_type')))
                    conn.commit()
                    return {'success': True, 'record_id': record_id}
        except Exception as e:
            logger.error(f'记录培训参与失败: {e}')
            return {'success': False, 'error': str(e)}

    def update_safety_training(self, training_id: str, **kwargs) -> Dict[str, Any]:
        try:
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    update_fields = []
                    params = []
                    if 'name' in kwargs:
                        update_fields.append('name = ?')
                        params.append(kwargs['name'])
                    if 'description' in kwargs:
                        update_fields.append('description = ?')
                        params.append(kwargs['description'])
                    if 'target_audience' in kwargs:
                        update_fields.append('target_audience = ?')
                        params.append(kwargs['target_audience'])
                    if 'status' in kwargs:
                        update_fields.append('status = ?')
                        params.append(kwargs['status'])
                    if 'start_date' in kwargs:
                        update_fields.append('start_date = ?')
                        params.append(kwargs['start_date'])
                    if 'end_date' in kwargs:
                        update_fields.append('end_date = ?')
                        params.append(kwargs['end_date'])
                    if update_fields:
                        update_fields.append('updated_at = ?')
                        params.append(now)
                        params.append(training_id)
                        cursor.execute(f'UPDATE safety_training SET {", ".join(update_fields)} WHERE training_id = ?', params)
                        if cursor.rowcount > 0:
                            conn.commit()
                            return {'success': True}
                    return {'success': False, 'error': '未找到记录或无更新内容'}
        except Exception as e:
            logger.error(f'更新安全培训失败: {e}')
            return {'success': False, 'error': str(e)}

    def list_safety_training(self, training_type: str = None,
                             education_type: str = None,
                             status: str = None, page: int = 1,
                             page_size: int = 20) -> Dict[str, Any]:
        try:
            with self._get_connection() as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                query = 'SELECT * FROM safety_training WHERE 1=1'
                params = []
                if training_type:
                    query += ' AND training_type = ?'
                    params.append(training_type)
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
            logger.error(f'获取安全培训列表失败: {e}')
            return {'success': False, 'error': str(e)}

    # ========== 安全评估 ==========

    def create_security_assessment(self, assessment_type: str, name: str,
                                   education_type: str, **kwargs) -> Dict[str, Any]:
        try:
            assessment_id = f"asm_{uuid.uuid4().hex[:12]}"
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('''
                        INSERT INTO security_assessment (
                            assessment_id, assessment_type, name, education_type,
                            description, scope, status, start_date,
                            end_date, created_at, updated_at
                        ) VALUES (?, ?, ?, ?, ?, ?, 'in_progress', ?, ?, ?, ?)
                    ''', (assessment_id, assessment_type, name, education_type,
                          kwargs.get('description'), kwargs.get('scope'),
                          kwargs.get('start_date', now[:10]), kwargs.get('end_date'),
                          now, now))
                    conn.commit()
                    logger.info(f'创建安全评估: {name} ({assessment_id})')
                    return {'success': True, 'assessment_id': assessment_id}
        except Exception as e:
            logger.error(f'创建安全评估失败: {e}')
            return {'success': False, 'error': str(e)}

    def record_assessment_result(self, assessment_id: str, record_type: str,
                                 content: str, **kwargs) -> Dict[str, Any]:
        try:
            record_id = f"asr_{uuid.uuid4().hex[:12]}"
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('''
                        INSERT INTO assessment_records (
                            record_id, assessment_id, record_type, content,
                            assessor, result, score, record_time, education_type
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                    ''', (record_id, assessment_id, record_type, content,
                          kwargs.get('assessor'), kwargs.get('result'),
                          kwargs.get('score'), now, kwargs.get('education_type')))
                    if record_type == 'final' and kwargs.get('result'):
                        cursor.execute('UPDATE security_assessment SET status = ?, end_date = ?, updated_at = ? WHERE assessment_id = ?', ('completed', now[:10], now, assessment_id))
                    conn.commit()
                    return {'success': True, 'record_id': record_id}
        except Exception as e:
            logger.error(f'记录评估结果失败: {e}')
            return {'success': False, 'error': str(e)}

    def update_security_assessment(self, assessment_id: str, **kwargs) -> Dict[str, Any]:
        try:
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    update_fields = []
                    params = []
                    if 'name' in kwargs:
                        update_fields.append('name = ?')
                        params.append(kwargs['name'])
                    if 'description' in kwargs:
                        update_fields.append('description = ?')
                        params.append(kwargs['description'])
                    if 'scope' in kwargs:
                        update_fields.append('scope = ?')
                        params.append(kwargs['scope'])
                    if 'status' in kwargs:
                        update_fields.append('status = ?')
                        params.append(kwargs['status'])
                    if 'start_date' in kwargs:
                        update_fields.append('start_date = ?')
                        params.append(kwargs['start_date'])
                    if 'end_date' in kwargs:
                        update_fields.append('end_date = ?')
                        params.append(kwargs['end_date'])
                    if update_fields:
                        update_fields.append('updated_at = ?')
                        params.append(now)
                        params.append(assessment_id)
                        cursor.execute(f'UPDATE security_assessment SET {", ".join(update_fields)} WHERE assessment_id = ?', params)
                        if cursor.rowcount > 0:
                            conn.commit()
                            return {'success': True}
                    return {'success': False, 'error': '未找到记录或无更新内容'}
        except Exception as e:
            logger.error(f'更新安全评估失败: {e}')
            return {'success': False, 'error': str(e)}

    def list_security_assessment(self, assessment_type: str = None,
                                  education_type: str = None,
                                  status: str = None, page: int = 1,
                                  page_size: int = 20) -> Dict[str, Any]:
        try:
            with self._get_connection() as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                query = 'SELECT * FROM security_assessment WHERE 1=1'
                params = []
                if assessment_type:
                    query += ' AND assessment_type = ?'
                    params.append(assessment_type)
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
            logger.error(f'获取安全评估列表失败: {e}')
            return {'success': False, 'error': str(e)}

    # ========== 安全统计 ==========

    def get_security_statistics(self, education_type: str = None,
                                start_date: str = None, end_date: str = None) -> Dict[str, Any]:
        try:
            with self._get_connection() as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                stats = {}

                date_filter = ''
                params = []
                if education_type:
                    date_filter += ' AND education_type = ?'
                    params.append(education_type)
                if start_date:
                    date_filter += ' AND created_at >= ?'
                    params.append(start_date)
                if end_date:
                    date_filter += ' AND created_at <= ?'
                    params.append(end_date)

                cursor.execute(f'SELECT COUNT(*) as cnt FROM campus_security WHERE 1=1{date_filter}', params)
                stats['campus_security_count'] = cursor.fetchone()['cnt']

                cursor.execute(f'SELECT COUNT(*) as cnt FROM network_security WHERE 1=1{date_filter}', params)
                stats['network_security_count'] = cursor.fetchone()['cnt']

                cursor.execute(f'SELECT COUNT(*) as cnt FROM food_security WHERE 1=1{date_filter}', params)
                stats['food_security_count'] = cursor.fetchone()['cnt']

                cursor.execute(f'SELECT COUNT(*) as cnt FROM fire_security WHERE 1=1{date_filter}', params)
                stats['fire_security_count'] = cursor.fetchone()['cnt']

                cursor.execute(f'SELECT COUNT(*) as cnt FROM traffic_security WHERE 1=1{date_filter}', params)
                stats['traffic_security_count'] = cursor.fetchone()['cnt']

                cursor.execute(f'SELECT COUNT(*) as cnt FROM emergency_management WHERE 1=1{date_filter}', params)
                stats['emergency_plan_count'] = cursor.fetchone()['cnt']

                cursor.execute(f'SELECT COUNT(*) as cnt FROM safety_training WHERE 1=1{date_filter}', params)
                stats['training_count'] = cursor.fetchone()['cnt']

                cursor.execute(f'SELECT COUNT(*) as cnt FROM security_assessment WHERE 1=1{date_filter}', params)
                stats['assessment_count'] = cursor.fetchone()['cnt']

                event_params = params.copy()
                cursor.execute(f'SELECT COUNT(*) as cnt FROM security_records WHERE 1=1{date_filter}', event_params)
                stats['campus_events'] = cursor.fetchone()['cnt']

                cursor.execute(f'SELECT COUNT(*) as cnt FROM network_records WHERE 1=1{date_filter}', event_params)
                stats['network_events'] = cursor.fetchone()['cnt']

                cursor.execute(f'SELECT COUNT(*) as cnt FROM fire_records WHERE record_type = "accident"{date_filter}', event_params)
                stats['fire_accidents'] = cursor.fetchone()['cnt']

                cursor.execute(f'SELECT COUNT(*) as cnt FROM traffic_records WHERE record_type = "accident"{date_filter}', event_params)
                stats['traffic_accidents'] = cursor.fetchone()['cnt']

                if education_type:
                    cursor.execute('SELECT COUNT(*) as cnt FROM campus_security WHERE education_type = "adult"', [])
                    stats['adult_campus_security'] = cursor.fetchone()['cnt']
                    cursor.execute('SELECT COUNT(*) as cnt FROM campus_security WHERE education_type = "k12"', [])
                    stats['k12_campus_security'] = cursor.fetchone()['cnt']

                stats['education_type'] = education_type if education_type else 'all'
                stats['start_date'] = start_date
                stats['end_date'] = end_date
                stats['generated_at'] = datetime.now().isoformat()

                return {'success': True, 'statistics': stats}
        except Exception as e:
            logger.error(f'获取安全统计失败: {e}')
            return {'success': False, 'error': str(e)}