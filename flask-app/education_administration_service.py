#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
MTSCOS 教育行政管理服务 (v15.26.0)
====================================
提供行政事务、人事、财务、资产、档案、会议、公文、后勤等综合管理服务。

核心能力：
1. 行政事务管理 - 日常行政事务处理与记录
2. 人事管理 - 教师、职工、干部管理与绩效考核
3. 财务管理 - 预算、经费、报销、收费管理
4. 资产管理 - 固定资产、设备、图书、采购管理
5. 档案管理 - 文书、学籍、人事、财务档案管理
6. 会议管理 - 会议组织、记录、纪要管理
7. 公文管理 - 通知、请示、批复、函件管理
8. 后勤管理 - 食堂、宿舍、水电、维修管理
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
            os.path.join(os.path.dirname(os.path.abspath(__file__)), 'education_administration_service.log'),
            encoding='utf-8'
        ),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger('EducationAdministration')


# ========== 行政配置 ==========

ADMIN_TYPES = {
    'daily': {'name': '日常行政', 'sub': ['值班安排', '公务接待', '办公用品', '印章管理']},
    'personnel': {'name': '人事管理', 'sub': ['招聘', '培训', '考核', '任免']},
    'finance': {'name': '财务管理', 'sub': ['预算', '报销', '工资', '审计']},
    'asset': {'name': '资产管理', 'sub': ['采购', '登记', '盘点', '处置']},
    'archive': {'name': '档案管理', 'sub': ['收集', '整理', '保管', '利用']},
    'meeting': {'name': '会议管理', 'sub': ['筹备', '组织', '记录', '纪要']},
    'document': {'name': '公文管理', 'sub': ['起草', '审核', '签发', '归档']},
    'logistics': {'name': '后勤管理', 'sub': ['维修', '安保', '保洁', '餐饮']}
}

PERSONNEL_TYPES = {
    'teacher': {'name': '教师管理', 'sub': ['教师招聘', '职称评定', '继续教育', '教学考核']},
    'staff': {'name': '职工管理', 'sub': ['岗位设置', '劳动合同', '考勤管理', '奖惩管理']},
    'cadre': {'name': '干部管理', 'sub': ['干部选拔', '任前公示', '任期考核', '轮岗交流']},
    'recruitment': {'name': '人才引进', 'sub': ['招聘计划', '面试考核', '录用审批', '入职手续']},
    'title': {'name': '职称评定', 'sub': ['申报审核', '评审组织', '公示备案', '证书发放']},
    'performance': {'name': '绩效考核', 'sub': ['考核方案', '指标设定', '结果评定', '绩效反馈']},
    'training': {'name': '培训管理', 'sub': ['培训计划', '课程安排', '考勤记录', '效果评估']},
    'retirement': {'name': '离退休管理', 'sub': ['退休审批', '待遇核定', '离退休活动', '慰问关怀']}
}

FINANCE_TYPES = {
    'budget': {'name': '预算管理', 'sub': ['预算编制', '预算审批', '预算执行', '预算调整']},
    'fund': {'name': '经费管理', 'sub': ['经费申请', '经费拨付', '经费使用', '经费结算']},
    'reimbursement': {'name': '报销管理', 'sub': ['报销申请', '票据审核', '费用报销', '报销归档']},
    'charge': {'name': '收费管理', 'sub': ['收费标准', '收费通知', '收费统计', '欠费追缴']},
    'salary': {'name': '工资管理', 'sub': ['工资核算', '工资发放', '工资调整', '工资报表']},
    'audit': {'name': '审计管理', 'sub': ['内部审计', '专项审计', '审计报告', '整改跟踪']},
    'report': {'name': '财务报表', 'sub': ['月报季报', '年报编制', '报表分析', '报表报送']},
    'analysis': {'name': '财务分析', 'sub': ['收支分析', '成本分析', '效益分析', '趋势预测']}
}

ASSET_TYPES = {
    'fixed': {'name': '固定资产', 'sub': ['房屋建筑', '机械设备', '交通运输', '电子设备']},
    'equipment': {'name': '设备设施', 'sub': ['教学设备', '实验设备', '办公设备', '体育设备']},
    'library': {'name': '图书资料', 'sub': ['图书采购', '图书编目', '借阅管理', '图书剔旧']},
    'supplies': {'name': '办公用品', 'sub': ['办公用品采购', '领用登记', '库存管理', '消耗统计']},
    'intangible': {'name': '无形资产', 'sub': ['专利技术', '软件著作', '商标品牌', '域名管理']},
    'property': {'name': '房产管理', 'sub': ['房产登记', '房产租赁', '房产维修', '房产处置']},
    'vehicle': {'name': '车辆管理', 'sub': ['车辆登记', '车辆调度', '维修保养', '油耗管理']},
    'procurement': {'name': '物资采购', 'sub': ['采购计划', '招标采购', '合同管理', '验收入库']}
}

ARCHIVE_TYPES = {
    'document': {'name': '文书档案', 'sub': ['红头文件', '会议材料', '工作总结', '请示批复']},
    'student': {'name': '学籍档案', 'sub': ['入学登记', '学籍变更', '成绩档案', '毕业档案']},
    'personnel': {'name': '人事档案', 'sub': ['入职材料', '考核记录', '奖惩材料', '离职档案']},
    'finance': {'name': '财务档案', 'sub': ['会计凭证', '财务报表', '审计报告', '合同票据']},
    'research': {'name': '科研档案', 'sub': ['课题申报', '研究成果', '学术论文', '结题材料']},
    'construction': {'name': '基建档案', 'sub': ['立项文件', '设计图纸', '施工记录', '竣工验收']},
    'equipment': {'name': '设备档案', 'sub': ['设备采购', '安装调试', '维修记录', '报废档案']},
    'audio_visual': {'name': '声像档案', 'sub': ['照片档案', '视频资料', '录音资料', '电子档案']}
}

MEETING_TYPES = {
    'administrative': {'name': '行政会议', 'frequency': 'weekly', 'attendance': 'mandatory'},
    'teaching': {'name': '教学会议', 'frequency': 'biweekly', 'attendance': 'required'},
    'research': {'name': '科研会议', 'frequency': 'monthly', 'attendance': 'optional'},
    'special': {'name': '专题会议', 'frequency': 'ad-hoc', 'attendance': 'invited'},
    'general': {'name': '全体会议', 'frequency': 'quarterly', 'attendance': 'mandatory'},
    'department': {'name': '部门会议', 'frequency': 'weekly', 'attendance': 'mandatory'},
    'video': {'name': '视频会议', 'frequency': 'ad-hoc', 'attendance': 'remote'},
    'onsite': {'name': '现场会议', 'frequency': 'ad-hoc', 'attendance': 'onsite'}
}

DOCUMENT_TYPES = {
    'notice': {'name': '通知公告', 'flow': '起草->审核->签发->发布', 'template': 'notice'},
    'request': {'name': '请示报告', 'flow': '起草->审核->审批->回复', 'template': 'request'},
    'approval': {'name': '批复决定', 'flow': '起草->审核->签发->送达', 'template': 'approval'},
    'letter': {'name': '函件', 'flow': '起草->审核->签发->发送', 'template': 'letter'},
    'minutes': {'name': '会议纪要', 'flow': '记录->整理->审核->印发', 'template': 'minutes'},
    'regulation': {'name': '规章制度', 'flow': '起草->征求意见->审议->发布', 'template': 'regulation'},
    'plan': {'name': '计划总结', 'flow': '编制->审核->审批->下达', 'template': 'plan'},
    'research': {'name': '调研报告', 'flow': '调研->撰写->审核->印发', 'template': 'research'}
}

LOGISTICS_TYPES = {
    'canteen': {'name': '食堂管理', 'sub': ['菜品供应', '食品安全', '成本核算', '满意度调查']},
    'dormitory': {'name': '宿舍管理', 'sub': ['住宿安排', '设施维护', '安全管理', '退宿办理']},
    'utilities': {'name': '水电管理', 'sub': ['水电计量', '费用收缴', '节能管理', '设备维护']},
    'maintenance': {'name': '维修服务', 'sub': ['维修报修', '维修派工', '维修验收', '费用核算']},
    'security': {'name': '安保服务', 'sub': ['门禁管理', '巡逻执勤', '监控管理', '应急处置']},
    'cleaning': {'name': '保洁服务', 'sub': ['卫生保洁', '垃圾清运', '消杀防疫', '绿化养护']},
    'landscaping': {'name': '绿化管理', 'sub': ['绿化种植', '养护管理', '景观维护', '花木采购']},
    'transport': {'name': '车辆服务', 'sub': ['校车调度', '用车申请', '安全管理', '费用核算']}
}


class EducationAdministrationService:
    """教育行政管理服务"""

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
                    CREATE TABLE IF NOT EXISTS admin_affairs (
                        affair_id TEXT PRIMARY KEY,
                        affair_type TEXT NOT NULL,
                        affair_title TEXT NOT NULL,
                        education_type TEXT,
                        priority TEXT DEFAULT 'normal',
                        status TEXT DEFAULT 'pending',
                        assignee_id INTEGER,
                        assignee_name TEXT,
                        description TEXT,
                        deadline TEXT,
                        created_at TEXT,
                        updated_at TEXT
                    )
                ''')
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS affair_records (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        affair_id TEXT NOT NULL,
                        action TEXT NOT NULL,
                        operator_id INTEGER,
                        operator_name TEXT,
                        remark TEXT,
                        created_at TEXT
                    )
                ''')
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS personnel_management (
                        personnel_id TEXT PRIMARY KEY,
                        personnel_type TEXT NOT NULL,
                        name TEXT NOT NULL,
                        education_type TEXT,
                        gender TEXT,
                        birth_date TEXT,
                        id_card TEXT UNIQUE,
                        position TEXT,
                        department TEXT,
                        status TEXT DEFAULT 'active',
                        hire_date TEXT,
                        salary REAL,
                        phone TEXT,
                        email TEXT,
                        address TEXT,
                        created_at TEXT,
                        updated_at TEXT
                    )
                ''')
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS personnel_records (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        personnel_id TEXT NOT NULL,
                        record_type TEXT NOT NULL,
                        record_title TEXT,
                        content TEXT,
                        operator_id INTEGER,
                        operator_name TEXT,
                        created_at TEXT
                    )
                ''')
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS financial_management (
                        finance_id TEXT PRIMARY KEY,
                        finance_type TEXT NOT NULL,
                        title TEXT NOT NULL,
                        education_type TEXT,
                        amount REAL DEFAULT 0,
                        currency TEXT DEFAULT 'CNY',
                        status TEXT DEFAULT 'pending',
                        applicant_id INTEGER,
                        applicant_name TEXT,
                        department TEXT,
                        description TEXT,
                        document_no TEXT,
                        created_at TEXT,
                        updated_at TEXT
                    )
                ''')
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS financial_records (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        finance_id TEXT NOT NULL,
                        action TEXT NOT NULL,
                        amount REAL,
                        operator_id INTEGER,
                        operator_name TEXT,
                        remark TEXT,
                        created_at TEXT
                    )
                ''')
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS asset_management (
                        asset_id TEXT PRIMARY KEY,
                        asset_type TEXT NOT NULL,
                        asset_name TEXT NOT NULL,
                        education_type TEXT,
                        category TEXT,
                        brand TEXT,
                        model TEXT,
                        serial_no TEXT,
                        purchase_date TEXT,
                        purchase_price REAL,
                        current_value REAL,
                        location TEXT,
                        responsible_id INTEGER,
                        responsible_name TEXT,
                        status TEXT DEFAULT 'in_use',
                        depreciation_year INTEGER,
                        created_at TEXT,
                        updated_at TEXT
                    )
                ''')
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS asset_records (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        asset_id TEXT NOT NULL,
                        action TEXT NOT NULL,
                        operator_id INTEGER,
                        operator_name TEXT,
                        location_from TEXT,
                        location_to TEXT,
                        remark TEXT,
                        created_at TEXT
                    )
                ''')
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS archive_management (
                        archive_id TEXT PRIMARY KEY,
                        archive_type TEXT NOT NULL,
                        archive_name TEXT NOT NULL,
                        education_type TEXT,
                        category TEXT,
                        file_path TEXT,
                        file_size INTEGER,
                        storage_location TEXT,
                        is_available INTEGER DEFAULT 1,
                        access_level TEXT DEFAULT 'public',
                        creator_id INTEGER,
                        creator_name TEXT,
                        created_at TEXT,
                        updated_at TEXT
                    )
                ''')
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS archive_records (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        archive_id TEXT NOT NULL,
                        action TEXT NOT NULL,
                        operator_id INTEGER,
                        operator_name TEXT,
                        borrow_days INTEGER,
                        return_date TEXT,
                        remark TEXT,
                        created_at TEXT
                    )
                ''')
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS meeting_management (
                        meeting_id TEXT PRIMARY KEY,
                        meeting_type TEXT NOT NULL,
                        meeting_title TEXT NOT NULL,
                        education_type TEXT,
                        location TEXT,
                        start_time TEXT,
                        end_time TEXT,
                        organizer_id INTEGER,
                        organizer_name TEXT,
                        attendees TEXT,
                        agenda TEXT,
                        minutes TEXT,
                        status TEXT DEFAULT 'scheduled',
                        created_at TEXT,
                        updated_at TEXT
                    )
                ''')
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS meeting_records (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        meeting_id TEXT NOT NULL,
                        action TEXT NOT NULL,
                        operator_id INTEGER,
                        operator_name TEXT,
                        content TEXT,
                        created_at TEXT
                    )
                ''')
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS document_management (
                        document_id TEXT PRIMARY KEY,
                        document_type TEXT NOT NULL,
                        document_title TEXT NOT NULL,
                        education_type TEXT,
                        content TEXT,
                        sender_id INTEGER,
                        sender_name TEXT,
                        receiver TEXT,
                        status TEXT DEFAULT 'draft',
                        priority TEXT DEFAULT 'normal',
                        document_no TEXT,
                        signed_at TEXT,
                        created_at TEXT,
                        updated_at TEXT
                    )
                ''')
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS document_records (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        document_id TEXT NOT NULL,
                        action TEXT NOT NULL,
                        operator_id INTEGER,
                        operator_name TEXT,
                        status_before TEXT,
                        status_after TEXT,
                        remark TEXT,
                        created_at TEXT
                    )
                ''')
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS logistics_management (
                        logistics_id TEXT PRIMARY KEY,
                        logistics_type TEXT NOT NULL,
                        title TEXT NOT NULL,
                        education_type TEXT,
                        location TEXT,
                        status TEXT DEFAULT 'pending',
                        requester_id INTEGER,
                        requester_name TEXT,
                        assignee_id INTEGER,
                        assignee_name TEXT,
                        description TEXT,
                        priority TEXT DEFAULT 'normal',
                        cost REAL DEFAULT 0,
                        created_at TEXT,
                        updated_at TEXT
                    )
                ''')
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS logistics_records (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        logistics_id TEXT NOT NULL,
                        action TEXT NOT NULL,
                        operator_id INTEGER,
                        operator_name TEXT,
                        remark TEXT,
                        created_at TEXT
                    )
                ''')
                conn.commit()
                logger.info('教育行政管理服务数据库初始化完成')
        except Exception as e:
            logger.error(f'数据库初始化失败: {e}')

    # ========== 行政事务管理 ==========

    def create_admin_affair(self, affair_type: str, affair_title: str,
                            **kwargs) -> Dict[str, Any]:
        try:
            affair_id = f"adm_{uuid.uuid4().hex[:12]}"
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('''
                        INSERT INTO admin_affairs (
                            affair_id, affair_type, affair_title,
                            education_type, priority, status,
                            assignee_id, assignee_name, description,
                            deadline, created_at, updated_at
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    ''', (affair_id, affair_type, affair_title,
                          kwargs.get('education_type'),
                          kwargs.get('priority', 'normal'), 'pending',
                          kwargs.get('assignee_id'), kwargs.get('assignee_name'),
                          kwargs.get('description'), kwargs.get('deadline'),
                          now, now))
                    conn.commit()
                    logger.info(f'创建行政事务: {affair_title} ({affair_id})')
                    return {'success': True, 'affair_id': affair_id}
        except Exception as e:
            logger.error(f'创建行政事务失败: {e}')
            return {'success': False, 'error': str(e)}

    def process_admin_affair(self, affair_id: str, action: str,
                             operator_id: int, operator_name: str,
                             **kwargs) -> Dict[str, Any]:
        try:
            now = datetime.now().isoformat()
            status_map = {'approve': 'approved', 'reject': 'rejected', 'complete': 'completed'}
            new_status = status_map.get(action, 'processing')
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('UPDATE admin_affairs SET status = ?, updated_at = ? WHERE affair_id = ?',
                                 (new_status, now, affair_id))
                    cursor.execute('INSERT INTO affair_records (affair_id, action, operator_id, operator_name, remark, created_at) VALUES (?, ?, ?, ?, ?, ?)',
                                 (affair_id, action, operator_id, operator_name, kwargs.get('remark'), now))
                    conn.commit()
                    return {'success': True, 'status': new_status}
        except Exception as e:
            logger.error(f'处理行政事务失败: {e}')
            return {'success': False, 'error': str(e)}

    def assign_admin_affair(self, affair_id: str, assignee_id: int,
                            assignee_name: str) -> Dict[str, Any]:
        try:
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('UPDATE admin_affairs SET assignee_id = ?, assignee_name = ?, status = ?, updated_at = ? WHERE affair_id = ?',
                                 (assignee_id, assignee_name, 'assigned', now, affair_id))
                    cursor.execute('INSERT INTO affair_records (affair_id, action, operator_id, operator_name, remark, created_at) VALUES (?, ?, ?, ?, ?, ?)',
                                 (affair_id, 'assign', assignee_id, assignee_name, '事务已分配', now))
                    conn.commit()
                    return {'success': True}
        except Exception as e:
            logger.error(f'分配行政事务失败: {e}')
            return {'success': False, 'error': str(e)}

    def list_admin_affairs(self, affair_type: str = None, status: str = None,
                           education_type: str = None, page: int = 1,
                           page_size: int = 20) -> Dict[str, Any]:
        try:
            with self._get_connection() as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                query = 'SELECT * FROM admin_affairs WHERE 1=1'
                params = []
                if affair_type:
                    query += ' AND affair_type = ?'
                    params.append(affair_type)
                if status:
                    query += ' AND status = ?'
                    params.append(status)
                if education_type:
                    query += ' AND education_type = ?'
                    params.append(education_type)
                cursor.execute(f'SELECT COUNT(*) as cnt FROM ({query})', params)
                total = cursor.fetchone()['cnt']
                query += ' ORDER BY created_at DESC LIMIT ? OFFSET ?'
                params.extend([page_size, (page - 1) * page_size])
                cursor.execute(query, params)
                affairs = [dict(a) for a in cursor.fetchall()]
                return {'success': True, 'affairs': affairs, 'total': total, 'page': page, 'page_size': page_size}
        except Exception as e:
            logger.error(f'获取行政事务列表失败: {e}')
            return {'success': False, 'error': str(e)}

    # ========== 人事管理 ==========

    def add_personnel(self, personnel_type: str, name: str,
                      **kwargs) -> Dict[str, Any]:
        try:
            personnel_id = f"prs_{uuid.uuid4().hex[:12]}"
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('''
                        INSERT INTO personnel_management (
                            personnel_id, personnel_type, name, education_type,
                            gender, birth_date, id_card, position, department,
                            status, hire_date, salary, phone, email, address,
                            created_at, updated_at
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    ''', (personnel_id, personnel_type, name,
                          kwargs.get('education_type'), kwargs.get('gender'),
                          kwargs.get('birth_date'), kwargs.get('id_card'),
                          kwargs.get('position'), kwargs.get('department'),
                          'active', kwargs.get('hire_date', now[:10]),
                          kwargs.get('salary', 0), kwargs.get('phone'),
                          kwargs.get('email'), kwargs.get('address'), now, now))
                    cursor.execute('INSERT INTO personnel_records (personnel_id, record_type, record_title, content, operator_id, operator_name, created_at) VALUES (?, ?, ?, ?, ?, ?, ?)',
                                 (personnel_id, 'hire', '入职登记', f'{name}入职{kwargs.get("department", "")}',
                                  kwargs.get('operator_id'), kwargs.get('operator_name', 'system'), now))
                    conn.commit()
                    logger.info(f'添加人员: {name} ({personnel_id})')
                    return {'success': True, 'personnel_id': personnel_id}
        except Exception as e:
            logger.error(f'添加人员失败: {e}')
            return {'success': False, 'error': str(e)}

    def update_personnel(self, personnel_id: str, **kwargs) -> Dict[str, Any]:
        try:
            now = datetime.now().isoformat()
            updates = []
            params = []
            for key, value in kwargs.items():
                if key in ['name', 'gender', 'birth_date', 'position', 'department',
                           'salary', 'phone', 'email', 'address', 'status']:
                    updates.append(f'{key} = ?')
                    params.append(value)
            if not updates:
                return {'success': False, 'error': '没有更新字段'}
            params.append(personnel_id)
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute(f'UPDATE personnel_management SET {", ".join(updates)}, updated_at = ? WHERE personnel_id = ?',
                                 params + [now])
                    cursor.execute('INSERT INTO personnel_records (personnel_id, record_type, record_title, content, operator_id, operator_name, created_at) VALUES (?, ?, ?, ?, ?, ?, ?)',
                                 (personnel_id, 'update', '信息更新', json.dumps(kwargs, ensure_ascii=False),
                                  kwargs.get('operator_id'), kwargs.get('operator_name', 'system'), now))
                    conn.commit()
                    return {'success': True}
        except Exception as e:
            logger.error(f'更新人员信息失败: {e}')
            return {'success': False, 'error': str(e)}

    def record_performance(self, personnel_id: str, record_type: str,
                           record_title: str, content: str,
                           **kwargs) -> Dict[str, Any]:
        try:
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('INSERT INTO personnel_records (personnel_id, record_type, record_title, content, operator_id, operator_name, created_at) VALUES (?, ?, ?, ?, ?, ?, ?)',
                                 (personnel_id, record_type, record_title, content,
                                  kwargs.get('operator_id'), kwargs.get('operator_name', 'system'), now))
                    conn.commit()
                    return {'success': True}
        except Exception as e:
            logger.error(f'记录人事档案失败: {e}')
            return {'success': False, 'error': str(e)}

    def list_personnel(self, personnel_type: str = None, department: str = None,
                       education_type: str = None, page: int = 1,
                       page_size: int = 20) -> Dict[str, Any]:
        try:
            with self._get_connection() as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                query = 'SELECT * FROM personnel_management WHERE 1=1'
                params = []
                if personnel_type:
                    query += ' AND personnel_type = ?'
                    params.append(personnel_type)
                if department:
                    query += ' AND department = ?'
                    params.append(department)
                if education_type:
                    query += ' AND education_type = ?'
                    params.append(education_type)
                cursor.execute(f'SELECT COUNT(*) as cnt FROM ({query})', params)
                total = cursor.fetchone()['cnt']
                query += ' ORDER BY created_at DESC LIMIT ? OFFSET ?'
                params.extend([page_size, (page - 1) * page_size])
                cursor.execute(query, params)
                personnel = [dict(p) for p in cursor.fetchall()]
                return {'success': True, 'personnel': personnel, 'total': total, 'page': page, 'page_size': page_size}
        except Exception as e:
            logger.error(f'获取人员列表失败: {e}')
            return {'success': False, 'error': str(e)}

    # ========== 财务管理 ==========

    def create_financial_item(self, finance_type: str, title: str,
                              **kwargs) -> Dict[str, Any]:
        try:
            finance_id = f"fin_{uuid.uuid4().hex[:12]}"
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('''
                        INSERT INTO financial_management (
                            finance_id, finance_type, title, education_type,
                            amount, currency, status, applicant_id,
                            applicant_name, department, description,
                            document_no, created_at, updated_at
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    ''', (finance_id, finance_type, title,
                          kwargs.get('education_type'), kwargs.get('amount', 0),
                          kwargs.get('currency', 'CNY'), 'pending',
                          kwargs.get('applicant_id'), kwargs.get('applicant_name'),
                          kwargs.get('department'), kwargs.get('description'),
                          kwargs.get('document_no'), now, now))
                    conn.commit()
                    logger.info(f'创建财务事项: {title} ({finance_id})')
                    return {'success': True, 'finance_id': finance_id}
        except Exception as e:
            logger.error(f'创建财务事项失败: {e}')
            return {'success': False, 'error': str(e)}

    def approve_financial_item(self, finance_id: str, approved: bool,
                               operator_id: int, operator_name: str,
                               **kwargs) -> Dict[str, Any]:
        try:
            now = datetime.now().isoformat()
            status = 'approved' if approved else 'rejected'
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('UPDATE financial_management SET status = ?, updated_at = ? WHERE finance_id = ?',
                                 (status, now, finance_id))
                    cursor.execute('INSERT INTO financial_records (finance_id, action, amount, operator_id, operator_name, remark, created_at) VALUES (?, ?, ?, ?, ?, ?, ?)',
                                 (finance_id, status, kwargs.get('amount'), operator_id, operator_name, kwargs.get('remark'), now))
                    conn.commit()
                    return {'success': True, 'status': status}
        except Exception as e:
            logger.error(f'审核财务事项失败: {e}')
            return {'success': False, 'error': str(e)}

    def record_financial_transaction(self, finance_id: str, action: str,
                                     amount: float, operator_id: int,
                                     operator_name: str, **kwargs) -> Dict[str, Any]:
        try:
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('INSERT INTO financial_records (finance_id, action, amount, operator_id, operator_name, remark, created_at) VALUES (?, ?, ?, ?, ?, ?, ?)',
                                 (finance_id, action, amount, operator_id, operator_name, kwargs.get('remark'), now))
                    conn.commit()
                    return {'success': True}
        except Exception as e:
            logger.error(f'记录财务交易失败: {e}')
            return {'success': False, 'error': str(e)}

    def get_financial_summary(self, finance_type: str = None,
                              education_type: str = None,
                              start_date: str = None,
                              end_date: str = None) -> Dict[str, Any]:
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                query = 'SELECT SUM(amount) as total FROM financial_management WHERE 1=1'
                params = []
                if finance_type:
                    query += ' AND finance_type = ?'
                    params.append(finance_type)
                if education_type:
                    query += ' AND education_type = ?'
                    params.append(education_type)
                if start_date:
                    query += ' AND created_at >= ?'
                    params.append(start_date)
                if end_date:
                    query += ' AND created_at <= ?'
                    params.append(end_date + ' 23:59:59')
                cursor.execute(query, params)
                total = cursor.fetchone()[0] or 0
                return {'success': True, 'total_amount': round(total, 2)}
        except Exception as e:
            logger.error(f'获取财务汇总失败: {e}')
            return {'success': False, 'error': str(e)}

    # ========== 资产管理 ==========

    def add_asset(self, asset_type: str, asset_name: str,
                  **kwargs) -> Dict[str, Any]:
        try:
            asset_id = f"ast_{uuid.uuid4().hex[:12]}"
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('''
                        INSERT INTO asset_management (
                            asset_id, asset_type, asset_name, education_type,
                            category, brand, model, serial_no,
                            purchase_date, purchase_price, current_value,
                            location, responsible_id, responsible_name,
                            status, depreciation_year, created_at, updated_at
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    ''', (asset_id, asset_type, asset_name,
                          kwargs.get('education_type'), kwargs.get('category'),
                          kwargs.get('brand'), kwargs.get('model'),
                          kwargs.get('serial_no'), kwargs.get('purchase_date', now[:10]),
                          kwargs.get('purchase_price', 0), kwargs.get('current_value', kwargs.get('purchase_price', 0)),
                          kwargs.get('location'), kwargs.get('responsible_id'),
                          kwargs.get('responsible_name'), 'in_use',
                          kwargs.get('depreciation_year', 5), now, now))
                    conn.commit()
                    logger.info(f'添加资产: {asset_name} ({asset_id})')
                    return {'success': True, 'asset_id': asset_id}
        except Exception as e:
            logger.error(f'添加资产失败: {e}')
            return {'success': False, 'error': str(e)}

    def transfer_asset(self, asset_id: str, new_location: str,
                       new_responsible_id: int = None,
                       new_responsible_name: str = None,
                       **kwargs) -> Dict[str, Any]:
        try:
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('SELECT location, responsible_name FROM asset_management WHERE asset_id = ?', (asset_id,))
                    asset = cursor.fetchone()
                    if not asset:
                        return {'success': False, 'error': '资产不存在'}
                    updates = ['location = ?', 'updated_at = ?']
                    params = [new_location, now]
                    if new_responsible_id:
                        updates.append('responsible_id = ?')
                        params.append(new_responsible_id)
                    if new_responsible_name:
                        updates.append('responsible_name = ?')
                        params.append(new_responsible_name)
                    params.append(asset_id)
                    cursor.execute(f'UPDATE asset_management SET {", ".join(updates)} WHERE asset_id = ?', params)
                    cursor.execute('INSERT INTO asset_records (asset_id, action, operator_id, operator_name, location_from, location_to, remark, created_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?)',
                                 (asset_id, 'transfer', kwargs.get('operator_id'), kwargs.get('operator_name', 'system'),
                                  asset[0], new_location, kwargs.get('remark'), now))
                    conn.commit()
                    return {'success': True}
        except Exception as e:
            logger.error(f'资产调拨失败: {e}')
            return {'success': False, 'error': str(e)}

    def maintain_asset(self, asset_id: str, action: str,
                       operator_id: int, operator_name: str,
                       **kwargs) -> Dict[str, Any]:
        try:
            now = datetime.now().isoformat()
            status_map = {'repair': 'repairing', 'maintain': 'maintaining', 'complete': 'in_use'}
            new_status = status_map.get(action, 'in_use')
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('UPDATE asset_management SET status = ?, updated_at = ? WHERE asset_id = ?',
                                 (new_status, now, asset_id))
                    cursor.execute('INSERT INTO asset_records (asset_id, action, operator_id, operator_name, remark, created_at) VALUES (?, ?, ?, ?, ?, ?)',
                                 (asset_id, action, operator_id, operator_name, kwargs.get('remark'), now))
                    conn.commit()
                    return {'success': True, 'status': new_status}
        except Exception as e:
            logger.error(f'资产维护失败: {e}')
            return {'success': False, 'error': str(e)}

    def dispose_asset(self, asset_id: str, reason: str,
                      operator_id: int, operator_name: str) -> Dict[str, Any]:
        try:
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('UPDATE asset_management SET status = ?, updated_at = ? WHERE asset_id = ?',
                                 ('disposed', now, asset_id))
                    cursor.execute('INSERT INTO asset_records (asset_id, action, operator_id, operator_name, remark, created_at) VALUES (?, ?, ?, ?, ?, ?)',
                                 (asset_id, 'dispose', operator_id, operator_name, reason, now))
                    conn.commit()
                    return {'success': True}
        except Exception as e:
            logger.error(f'资产处置失败: {e}')
            return {'success': False, 'error': str(e)}

    def list_assets(self, asset_type: str = None, status: str = None,
                    education_type: str = None, page: int = 1,
                    page_size: int = 20) -> Dict[str, Any]:
        try:
            with self._get_connection() as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                query = 'SELECT * FROM asset_management WHERE 1=1'
                params = []
                if asset_type:
                    query += ' AND asset_type = ?'
                    params.append(asset_type)
                if status:
                    query += ' AND status = ?'
                    params.append(status)
                if education_type:
                    query += ' AND education_type = ?'
                    params.append(education_type)
                cursor.execute(f'SELECT COUNT(*) as cnt FROM ({query})', params)
                total = cursor.fetchone()['cnt']
                query += ' ORDER BY created_at DESC LIMIT ? OFFSET ?'
                params.extend([page_size, (page - 1) * page_size])
                cursor.execute(query, params)
                assets = [dict(a) for a in cursor.fetchall()]
                return {'success': True, 'assets': assets, 'total': total, 'page': page, 'page_size': page_size}
        except Exception as e:
            logger.error(f'获取资产列表失败: {e}')
            return {'success': False, 'error': str(e)}

    # ========== 档案管理 ==========

    def create_archive(self, archive_type: str, archive_name: str,
                       **kwargs) -> Dict[str, Any]:
        try:
            archive_id = f"arc_{uuid.uuid4().hex[:12]}"
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('''
                        INSERT INTO archive_management (
                            archive_id, archive_type, archive_name, education_type,
                            category, file_path, file_size, storage_location,
                            is_available, access_level, creator_id, creator_name,
                            created_at, updated_at
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    ''', (archive_id, archive_type, archive_name,
                          kwargs.get('education_type'), kwargs.get('category'),
                          kwargs.get('file_path'), kwargs.get('file_size', 0),
                          kwargs.get('storage_location'), kwargs.get('is_available', 1),
                          kwargs.get('access_level', 'public'), kwargs.get('creator_id'),
                          kwargs.get('creator_name'), now, now))
                    conn.commit()
                    logger.info(f'创建档案: {archive_name} ({archive_id})')
                    return {'success': True, 'archive_id': archive_id}
        except Exception as e:
            logger.error(f'创建档案失败: {e}')
            return {'success': False, 'error': str(e)}

    def borrow_archive(self, archive_id: str, operator_id: int,
                       operator_name: str, borrow_days: int = 7) -> Dict[str, Any]:
        try:
            now = datetime.now().isoformat()
            return_date = (datetime.now() + timedelta(days=borrow_days)).strftime('%Y-%m-%d')
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('SELECT is_available FROM archive_management WHERE archive_id = ?', (archive_id,))
                    archive = cursor.fetchone()
                    if not archive or archive[0] != 1:
                        return {'success': False, 'error': '档案不可借'}
                    cursor.execute('UPDATE archive_management SET is_available = 0, updated_at = ? WHERE archive_id = ?',
                                 (now, archive_id))
                    cursor.execute('INSERT INTO archive_records (archive_id, action, operator_id, operator_name, borrow_days, return_date, remark, created_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?)',
                                 (archive_id, 'borrow', operator_id, operator_name, borrow_days, return_date, '借阅', now))
                    conn.commit()
                    return {'success': True, 'return_date': return_date}
        except Exception as e:
            logger.error(f'借阅档案失败: {e}')
            return {'success': False, 'error': str(e)}

    def return_archive(self, archive_id: str, operator_id: int,
                       operator_name: str) -> Dict[str, Any]:
        try:
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('UPDATE archive_management SET is_available = 1, updated_at = ? WHERE archive_id = ?',
                                 (now, archive_id))
                    cursor.execute('INSERT INTO archive_records (archive_id, action, operator_id, operator_name, return_date, remark, created_at) VALUES (?, ?, ?, ?, ?, ?, ?)',
                                 (archive_id, 'return', operator_id, operator_name, now[:10], '归还', now))
                    conn.commit()
                    return {'success': True}
        except Exception as e:
            logger.error(f'归还档案失败: {e}')
            return {'success': False, 'error': str(e)}

    def list_archives(self, archive_type: str = None, is_available: bool = None,
                      education_type: str = None, page: int = 1,
                      page_size: int = 20) -> Dict[str, Any]:
        try:
            with self._get_connection() as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                query = 'SELECT * FROM archive_management WHERE 1=1'
                params = []
                if archive_type:
                    query += ' AND archive_type = ?'
                    params.append(archive_type)
                if is_available is not None:
                    query += ' AND is_available = ?'
                    params.append(1 if is_available else 0)
                if education_type:
                    query += ' AND education_type = ?'
                    params.append(education_type)
                cursor.execute(f'SELECT COUNT(*) as cnt FROM ({query})', params)
                total = cursor.fetchone()['cnt']
                query += ' ORDER BY created_at DESC LIMIT ? OFFSET ?'
                params.extend([page_size, (page - 1) * page_size])
                cursor.execute(query, params)
                archives = [dict(a) for a in cursor.fetchall()]
                return {'success': True, 'archives': archives, 'total': total, 'page': page, 'page_size': page_size}
        except Exception as e:
            logger.error(f'获取档案列表失败: {e}')
            return {'success': False, 'error': str(e)}

    # ========== 会议管理 ==========

    def create_meeting(self, meeting_type: str, meeting_title: str,
                       start_time: str, **kwargs) -> Dict[str, Any]:
        try:
            meeting_id = f"mtg_{uuid.uuid4().hex[:12]}"
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('''
                        INSERT INTO meeting_management (
                            meeting_id, meeting_type, meeting_title, education_type,
                            location, start_time, end_time, organizer_id,
                            organizer_name, attendees, agenda, minutes,
                            status, created_at, updated_at
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    ''', (meeting_id, meeting_type, meeting_title,
                          kwargs.get('education_type'), kwargs.get('location'),
                          start_time, kwargs.get('end_time'),
                          kwargs.get('organizer_id'), kwargs.get('organizer_name'),
                          kwargs.get('attendees'), kwargs.get('agenda'),
                          None, 'scheduled', now, now))
                    conn.commit()
                    logger.info(f'创建会议: {meeting_title} ({meeting_id})')
                    return {'success': True, 'meeting_id': meeting_id}
        except Exception as e:
            logger.error(f'创建会议失败: {e}')
            return {'success': False, 'error': str(e)}

    def update_meeting(self, meeting_id: str, **kwargs) -> Dict[str, Any]:
        try:
            now = datetime.now().isoformat()
            updates = []
            params = []
            for key, value in kwargs.items():
                if key in ['meeting_title', 'location', 'start_time', 'end_time',
                           'attendees', 'agenda', 'status', 'minutes']:
                    updates.append(f'{key} = ?')
                    params.append(value)
            if not updates:
                return {'success': False, 'error': '没有更新字段'}
            params.append(meeting_id)
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute(f'UPDATE meeting_management SET {", ".join(updates)}, updated_at = ? WHERE meeting_id = ?',
                                 params + [now])
                    cursor.execute('INSERT INTO meeting_records (meeting_id, action, operator_id, operator_name, content, created_at) VALUES (?, ?, ?, ?, ?, ?)',
                                 (meeting_id, 'update', kwargs.get('operator_id'), kwargs.get('operator_name', 'system'), json.dumps(kwargs, ensure_ascii=False), now))
                    conn.commit()
                    return {'success': True}
        except Exception as e:
            logger.error(f'更新会议失败: {e}')
            return {'success': False, 'error': str(e)}

    def record_meeting_minutes(self, meeting_id: str, minutes: str,
                               operator_id: int, operator_name: str) -> Dict[str, Any]:
        try:
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('UPDATE meeting_management SET minutes = ?, status = ?, updated_at = ? WHERE meeting_id = ?',
                                 (minutes, 'completed', now, meeting_id))
                    cursor.execute('INSERT INTO meeting_records (meeting_id, action, operator_id, operator_name, content, created_at) VALUES (?, ?, ?, ?, ?, ?)',
                                 (meeting_id, 'minutes', operator_id, operator_name, '会议纪要已记录', now))
                    conn.commit()
                    return {'success': True}
        except Exception as e:
            logger.error(f'记录会议纪要失败: {e}')
            return {'success': False, 'error': str(e)}

    def list_meetings(self, meeting_type: str = None, status: str = None,
                      education_type: str = None, page: int = 1,
                      page_size: int = 20) -> Dict[str, Any]:
        try:
            with self._get_connection() as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                query = 'SELECT * FROM meeting_management WHERE 1=1'
                params = []
                if meeting_type:
                    query += ' AND meeting_type = ?'
                    params.append(meeting_type)
                if status:
                    query += ' AND status = ?'
                    params.append(status)
                if education_type:
                    query += ' AND education_type = ?'
                    params.append(education_type)
                cursor.execute(f'SELECT COUNT(*) as cnt FROM ({query})', params)
                total = cursor.fetchone()['cnt']
                query += ' ORDER BY start_time DESC LIMIT ? OFFSET ?'
                params.extend([page_size, (page - 1) * page_size])
                cursor.execute(query, params)
                meetings = [dict(m) for m in cursor.fetchall()]
                return {'success': True, 'meetings': meetings, 'total': total, 'page': page, 'page_size': page_size}
        except Exception as e:
            logger.error(f'获取会议列表失败: {e}')
            return {'success': False, 'error': str(e)}

    # ========== 公文管理 ==========

    def create_document(self, document_type: str, document_title: str,
                        **kwargs) -> Dict[str, Any]:
        try:
            document_id = f"doc_{uuid.uuid4().hex[:12]}"
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('''
                        INSERT INTO document_management (
                            document_id, document_type, document_title, education_type,
                            content, sender_id, sender_name, receiver,
                            status, priority, document_no, signed_at,
                            created_at, updated_at
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    ''', (document_id, document_type, document_title,
                          kwargs.get('education_type'), kwargs.get('content'),
                          kwargs.get('sender_id'), kwargs.get('sender_name'),
                          kwargs.get('receiver'), 'draft',
                          kwargs.get('priority', 'normal'), kwargs.get('document_no'),
                          None, now, now))
                    conn.commit()
                    logger.info(f'创建公文: {document_title} ({document_id})')
                    return {'success': True, 'document_id': document_id}
        except Exception as e:
            logger.error(f'创建公文失败: {e}')
            return {'success': False, 'error': str(e)}

    def process_document(self, document_id: str, action: str,
                         operator_id: int, operator_name: str,
                         **kwargs) -> Dict[str, Any]:
        try:
            now = datetime.now().isoformat()
            status_map = {'submit': 'submitted', 'approve': 'approved', 'reject': 'rejected', 'sign': 'signed', 'publish': 'published'}
            new_status = status_map.get(action, 'draft')
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('SELECT status FROM document_management WHERE document_id = ?', (document_id,))
                    old_status = cursor.fetchone()[0] if cursor.fetchone() else 'draft'
                    updates = ['status = ?', 'updated_at = ?']
                    params = [new_status, now]
                    if action == 'sign':
                        updates.append('signed_at = ?')
                        params.append(now)
                    params.append(document_id)
                    cursor.execute(f'UPDATE document_management SET {", ".join(updates)} WHERE document_id = ?', params)
                    cursor.execute('INSERT INTO document_records (document_id, action, operator_id, operator_name, status_before, status_after, remark, created_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?)',
                                 (document_id, action, operator_id, operator_name, old_status, new_status, kwargs.get('remark'), now))
                    conn.commit()
                    return {'success': True, 'status': new_status}
        except Exception as e:
            logger.error(f'处理公文失败: {e}')
            return {'success': False, 'error': str(e)}

    def distribute_document(self, document_id: str, receiver: str,
                            operator_id: int, operator_name: str) -> Dict[str, Any]:
        try:
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('UPDATE document_management SET receiver = ?, status = ?, updated_at = ? WHERE document_id = ?',
                                 (receiver, 'distributed', now, document_id))
                    cursor.execute('INSERT INTO document_records (document_id, action, operator_id, operator_name, status_before, status_after, remark, created_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?)',
                                 (document_id, 'distribute', operator_id, operator_name, 'published', 'distributed', f'已分发至: {receiver}', now))
                    conn.commit()
                    return {'success': True}
        except Exception as e:
            logger.error(f'分发公文失败: {e}')
            return {'success': False, 'error': str(e)}

    def list_documents(self, document_type: str = None, status: str = None,
                       education_type: str = None, page: int = 1,
                       page_size: int = 20) -> Dict[str, Any]:
        try:
            with self._get_connection() as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                query = 'SELECT * FROM document_management WHERE 1=1'
                params = []
                if document_type:
                    query += ' AND document_type = ?'
                    params.append(document_type)
                if status:
                    query += ' AND status = ?'
                    params.append(status)
                if education_type:
                    query += ' AND education_type = ?'
                    params.append(education_type)
                cursor.execute(f'SELECT COUNT(*) as cnt FROM ({query})', params)
                total = cursor.fetchone()['cnt']
                query += ' ORDER BY created_at DESC LIMIT ? OFFSET ?'
                params.extend([page_size, (page - 1) * page_size])
                cursor.execute(query, params)
                documents = [dict(d) for d in cursor.fetchall()]
                return {'success': True, 'documents': documents, 'total': total, 'page': page, 'page_size': page_size}
        except Exception as e:
            logger.error(f'获取公文列表失败: {e}')
            return {'success': False, 'error': str(e)}

    # ========== 后勤管理 ==========

    def create_logistics_request(self, logistics_type: str, title: str,
                                 **kwargs) -> Dict[str, Any]:
        try:
            logistics_id = f"log_{uuid.uuid4().hex[:12]}"
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('''
                        INSERT INTO logistics_management (
                            logistics_id, logistics_type, title, education_type,
                            location, status, requester_id, requester_name,
                            assignee_id, assignee_name, description,
                            priority, cost, created_at, updated_at
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    ''', (logistics_id, logistics_type, title,
                          kwargs.get('education_type'), kwargs.get('location'),
                          'pending', kwargs.get('requester_id'), kwargs.get('requester_name'),
                          kwargs.get('assignee_id'), kwargs.get('assignee_name'),
                          kwargs.get('description'), kwargs.get('priority', 'normal'),
                          kwargs.get('cost', 0), now, now))
                    conn.commit()
                    logger.info(f'创建后勤请求: {title} ({logistics_id})')
                    return {'success': True, 'logistics_id': logistics_id}
        except Exception as e:
            logger.error(f'创建后勤请求失败: {e}')
            return {'success': False, 'error': str(e)}

    def assign_logistics(self, logistics_id: str, assignee_id: int,
                         assignee_name: str) -> Dict[str, Any]:
        try:
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('UPDATE logistics_management SET assignee_id = ?, assignee_name = ?, status = ?, updated_at = ? WHERE logistics_id = ?',
                                 (assignee_id, assignee_name, 'assigned', now, logistics_id))
                    cursor.execute('INSERT INTO logistics_records (logistics_id, action, operator_id, operator_name, remark, created_at) VALUES (?, ?, ?, ?, ?, ?)',
                                 (logistics_id, 'assign', assignee_id, assignee_name, '任务已分配', now))
                    conn.commit()
                    return {'success': True}
        except Exception as e:
            logger.error(f'分配后勤任务失败: {e}')
            return {'success': False, 'error': str(e)}

    def complete_logistics(self, logistics_id: str, operator_id: int,
                           operator_name: str, **kwargs) -> Dict[str, Any]:
        try:
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    updates = ['status = ?', 'updated_at = ?']
                    params = ['completed', now]
                    if 'cost' in kwargs:
                        updates.append('cost = ?')
                        params.append(kwargs['cost'])
                    params.append(logistics_id)
                    cursor.execute(f'UPDATE logistics_management SET {", ".join(updates)} WHERE logistics_id = ?', params)
                    cursor.execute('INSERT INTO logistics_records (logistics_id, action, operator_id, operator_name, remark, created_at) VALUES (?, ?, ?, ?, ?, ?)',
                                 (logistics_id, 'complete', operator_id, operator_name, kwargs.get('remark', '任务已完成'), now))
                    conn.commit()
                    return {'success': True}
        except Exception as e:
            logger.error(f'完成后勤任务失败: {e}')
            return {'success': False, 'error': str(e)}

    def list_logistics(self, logistics_type: str = None, status: str = None,
                       education_type: str = None, page: int = 1,
                       page_size: int = 20) -> Dict[str, Any]:
        try:
            with self._get_connection() as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                query = 'SELECT * FROM logistics_management WHERE 1=1'
                params = []
                if logistics_type:
                    query += ' AND logistics_type = ?'
                    params.append(logistics_type)
                if status:
                    query += ' AND status = ?'
                    params.append(status)
                if education_type:
                    query += ' AND education_type = ?'
                    params.append(education_type)
                cursor.execute(f'SELECT COUNT(*) as cnt FROM ({query})', params)
                total = cursor.fetchone()['cnt']
                query += ' ORDER BY created_at DESC LIMIT ? OFFSET ?'
                params.extend([page_size, (page - 1) * page_size])
                cursor.execute(query, params)
                logistics = [dict(l) for l in cursor.fetchall()]
                return {'success': True, 'logistics': logistics, 'total': total, 'page': page, 'page_size': page_size}
        except Exception as e:
            logger.error(f'获取后勤列表失败: {e}')
            return {'success': False, 'error': str(e)}

    # ========== 统计汇总 ==========

    def get_management_summary(self, education_type: str = None) -> Dict[str, Any]:
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                where_clause = 'WHERE education_type = ?' if education_type else ''
                params = [education_type] if education_type else []

                cursor.execute(f'SELECT COUNT(*) FROM admin_affairs {where_clause}', params)
                admin_count = cursor.fetchone()[0] or 0

                cursor.execute(f'SELECT COUNT(*) FROM personnel_management {where_clause}', params)
                personnel_count = cursor.fetchone()[0] or 0

                cursor.execute(f'SELECT SUM(amount) FROM financial_management {where_clause}', params)
                financial_total = cursor.fetchone()[0] or 0

                cursor.execute(f'SELECT COUNT(*) FROM asset_management {where_clause}', params)
                asset_count = cursor.fetchone()[0] or 0

                cursor.execute(f'SELECT COUNT(*) FROM archive_management {where_clause}', params)
                archive_count = cursor.fetchone()[0] or 0

                cursor.execute(f'SELECT COUNT(*) FROM meeting_management {where_clause}', params)
                meeting_count = cursor.fetchone()[0] or 0

                cursor.execute(f'SELECT COUNT(*) FROM document_management {where_clause}', params)
                document_count = cursor.fetchone()[0] or 0

                cursor.execute(f'SELECT COUNT(*) FROM logistics_management {where_clause}', params)
                logistics_count = cursor.fetchone()[0] or 0

                return {
                    'success': True,
                    'summary': {
                        'admin_affairs': admin_count,
                        'personnel': personnel_count,
                        'financial_total': round(financial_total, 2),
                        'assets': asset_count,
                        'archives': archive_count,
                        'meetings': meeting_count,
                        'documents': document_count,
                        'logistics': logistics_count
                    },
                    'education_type': education_type or 'all'
                }
        except Exception as e:
            logger.error(f'获取管理汇总失败: {e}')
            return {'success': False, 'error': str(e)}