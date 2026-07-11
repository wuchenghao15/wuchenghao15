#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
9年制学生升级管理系统
包含完整的升级逻辑、考试管理、权限控制
版本: 1.1 - 从小学1年级开始的完整9年制体系
"""

import sqlite3
import json
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple
from enum import Enum
import uuid


class GradeLevel(Enum):
    """年级级别 - 完整9年制体系（小学1年级至初中3年级）"""
    GRADE_1 = "grade1"   # 小学1年级
    GRADE_2 = "grade2"   # 小学2年级
    GRADE_3 = "grade3"   # 小学3年级
    GRADE_4 = "grade4"   # 小学4年级
    GRADE_5 = "grade5"   # 小学5年级
    GRADE_6 = "grade6"   # 小学6年级
    GRADE_7 = "grade7"   # 初中1年级
    GRADE_8 = "grade8"   # 初中2年级
    GRADE_9 = "grade9"   # 初中3年级


class Subject(Enum):
    """科目"""
    CHINESE = "语文"
    MATH = "数学"
    ENGLISH = "英语"
    PHYSICS = "物理"
    CHEMISTRY = "化学"
    BIOLOGY = "生物"
    HISTORY = "历史"
    GEOGRAPHY = "地理"
    POLITICS = "政治"


class SubjectMaxScore:
    """科目最大分值配置"""
    @staticmethod
    def get_max_score(subject: Subject, grade: GradeLevel) -> int:
        """根据年级和科目获取最大分值"""
        # 小学1-6年级: 所有科目满分100分
        if grade in [GradeLevel.GRADE_1, GradeLevel.GRADE_2, GradeLevel.GRADE_3, 
                    GradeLevel.GRADE_4, GradeLevel.GRADE_5, GradeLevel.GRADE_6]:
            return 100
        
        # 初中7-9年级: 根据科目不同
        else:
            if subject in [Subject.CHINESE, Subject.MATH, Subject.ENGLISH]:
                return 150
            elif subject in [Subject.PHYSICS, Subject.CHEMISTRY]:
                return 100
            else:
                return 100


class GradeStatus(Enum):
    """年级状态枚举"""
    NORMAL = "normal"                    # 正常状态
    CONDITIONAL = "conditional"          # 条件升级（补考通过）
    RESTRICTED = "restricted"            # 受限状态（补考不及格）
    SUSPENDED = "suspended"              # 暂停状态
    GRADUATED = "graduated"              # 已毕业（初中3年级）
    REPEATING = "repeating"              # 留级状态


class ExamStatus(Enum):
    """考试状态枚举"""
    NOT_STARTED = "not_started"          # 未开始
    IN_PROGRESS = "in_progress"          # 进行中
    PAUSED = "paused"                    # 已暂停
    COMPLETED = "completed"              # 已完成
    FAILED = "failed"                    # 不及格
    PASSED = "passed"                    # 及格
    EXPIRED = "expired"                  # 已过期


class UpgradeType(Enum):
    """升级类型枚举"""
    NORMAL = "normal"                    # 正常升级
    MAKEUP_PASSED = "makeup_passed"      # 补考通过升级
    FORCE_UPGRADE = "force_upgrade"      # 强制升级（管理员）
    CONDITIONAL = "conditional"          # 条件升级


class PermissionLevel(Enum):
    """权限等级枚举"""
    SUPER_ADMIN = 100                    # 超级管理员
    ADMIN = 80                           # 管理员
    TEACHER = 60                         # 教师
    SUPERVISOR = 40                      # 学习监督
    STUDENT_FULL = 20                    # 完整权限学生
    STUDENT_LIMITED = 10                 # 受限权限学生
    STUDENT_RESTRICTED = 0               # 严格受限学生


class StudentGrade:
    """学生年级信息"""
    
    def __init__(self, user_id: str):
        self.user_id = user_id
        self.current_grade: Optional[GradeLevel] = None
        self.is_grade_confirmed = False
        self.grade_confirmed_at: Optional[datetime] = None
        self.grade_status: GradeStatus = GradeStatus.NORMAL
        self.permission_level: PermissionLevel = PermissionLevel.STUDENT_FULL
        self.can_change_grade = True
        self.grade_change_applications: List[Dict[str, Any]] = []
    
    def select_grade(self, grade: GradeLevel) -> bool:
        """选择年级"""
        if not self.can_change_grade:
            return False
        
        if self.current_grade and self.is_grade_confirmed:
            return False
        
        self.current_grade = grade
        return True
    
    def confirm_grade(self) -> bool:
        """确认年级"""
        if not self.current_grade:
            return False
        
        self.is_grade_confirmed = True
        self.grade_confirmed_at = datetime.now()
        self.can_change_grade = False
        return True
    
    def apply_grade_change(self, new_grade: GradeLevel, reason: str) -> str:
        """申请年级变更"""
        application = {
            "application_id": str(uuid.uuid4()),
            "user_id": self.user_id,
            "current_grade": self.current_grade.value if self.current_grade else None,
            "new_grade": new_grade.value,
            "reason": reason,
            "status": "pending",
            "created_at": datetime.now().isoformat(),
            "approved_by": None,
            "approved_at": None
        }
        self.grade_change_applications.append(application)
        return application["application_id"]
    
    def approve_grade_change(self, application_id: str, approved_by: str) -> bool:
        """审批年级变更"""
        for app in self.grade_change_applications:
            if app["application_id"] == application_id and app["status"] == "pending":
                app["status"] = "approved"
                app["approved_by"] = approved_by
                app["approved_at"] = datetime.now().isoformat()
                self.can_change_grade = True
                self.is_grade_confirmed = False
                return True
        return False
    
    def auto_upgrade(self) -> bool:
        """自动升级"""
        if not self.current_grade:
            return False
        
        if not self.is_grade_confirmed:
            return False
        
        grade_order = list(GradeLevel)
        current_index = grade_order.index(self.current_grade)
        
        if current_index >= len(grade_order) - 1:
            # 已经是最高年级（初中3年级）
            self.grade_status = GradeStatus.GRADUATED
            return False
        
        self.current_grade = grade_order[current_index + 1]
        self.grade_status = GradeStatus.NORMAL
        return True


class Exam:
    """考试"""
    
    def __init__(self, user_id: str, subject: Subject, exam_type: str, grade: GradeLevel):
        self.exam_id = str(uuid.uuid4())
        self.user_id = user_id
        self.subject = subject
        self.exam_type = exam_type
        self.grade = grade
        self.status = ExamStatus.NOT_STARTED
        self.score: Optional[float] = None
        self.max_score = SubjectMaxScore.get_max_score(subject, grade)
        self.created_at = datetime.now()
        self.started_at: Optional[datetime] = None
        self.completed_at: Optional[datetime] = None
        self.paused_at: Optional[datetime] = None
        self.can_pause = True
        self.has_paused = False
        self.deadline: Optional[datetime] = None
        self.calculate_deadline()
    
    def calculate_deadline(self):
        """计算考试截止时间"""
        now = datetime.now()
        
        if self.exam_type == "midterm":
            # 期中考试: 4月30日前完成
            self.deadline = datetime(now.year, 4, 30, 23, 59, 59)
        elif self.exam_type == "final":
            # 期末考试: 7月31日前完成
            if now.month < 6:
                self.deadline = datetime(now.year, 7, 31, 23, 59, 59)
            else:
                self.deadline = datetime(now.year, 7, 31, 23, 59, 59)
        elif self.exam_type == "makeup":
            # 补考: 8月20日前完成
            self.deadline = datetime(now.year, 8, 20, 23, 59, 59)
    
    def start_exam(self) -> bool:
        """开始考试"""
        if self.status != ExamStatus.NOT_STARTED:
            return False
        
        self.status = ExamStatus.IN_PROGRESS
        self.started_at = datetime.now()
        return True
    
    def pause_exam(self, approved_by_teacher: bool = False) -> bool:
        """暂停考试"""
        if not approved_by_teacher:
            return False
        
        if self.status != ExamStatus.IN_PROGRESS:
            return False
        
        if not self.can_pause:
            return False
        
        if self.has_paused:
            return False
        
        self.status = ExamStatus.PAUSED
        self.paused_at = datetime.now()
        self.can_pause = False
        self.has_paused = True
        return True
    
    def resume_exam(self) -> bool:
        """继续考试"""
        if self.status != ExamStatus.PAUSED:
            return False
        
        self.status = ExamStatus.IN_PROGRESS
        return True
    
    def complete_exam(self, score: float) -> bool:
        """完成考试"""
        if self.status not in [ExamStatus.IN_PROGRESS, ExamStatus.PAUSED]:
            return False
        
        self.status = ExamStatus.COMPLETED
        self.completed_at = datetime.now()
        self.score = score
        
        if self.score >= self.max_score * 0.6:
            self.status = ExamStatus.PASSED
        else:
            self.status = ExamStatus.FAILED
        
        return True
    
    def is_deadline_passed(self) -> bool:
        """检查是否超过截止时间"""
        if not self.deadline:
            return False
        return datetime.now() > self.deadline
    
    def auto_fail_if_paused(self) -> bool:
        """暂停考试未完成视为不及格"""
        if self.status == ExamStatus.PAUSED and self.is_deadline_passed():
            self.status = ExamStatus.FAILED
            self.score = 0
            self.completed_at = datetime.now()
            return True
        return False


class NineYearUpgradeSystem:
    """9年制学生升级管理系统"""
    
    def __init__(self, db_path: str = 'mtcos_system.db'):
        self.db_path = db_path
        self.conn = None
        self.cursor = None
    
    def connect(self):
        """连接数据库"""
        self.conn = sqlite3.connect(self.db_path)
        self.conn.row_factory = sqlite3.Row
        self.cursor = self.conn.cursor()
    
    def close(self):
        """关闭数据库连接"""
        if self.cursor:
            self.cursor.close()
        if self.conn:
            self.conn.close()
    
    def init_database(self):
        """初始化数据库表"""
        self.connect()
        
        # 学生年级表
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS nine_year_grades (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id TEXT NOT NULL UNIQUE,
                current_grade VARCHAR(20) NOT NULL,
                grade_status VARCHAR(20) DEFAULT 'normal',
                permission_level INTEGER DEFAULT 20,
                is_confirmed BOOLEAN DEFAULT FALSE,
                confirmed_at TIMESTAMP,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # 考试记录表
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS nine_year_exams (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id TEXT NOT NULL,
                exam_type VARCHAR(20) NOT NULL,
                subject VARCHAR(20) NOT NULL,
                grade VARCHAR(20) NOT NULL,
                score DECIMAL(5,2),
                max_score DECIMAL(5,2) DEFAULT 100,
                status VARCHAR(20) DEFAULT 'not_started',
                is_paused BOOLEAN DEFAULT FALSE,
                pause_reason TEXT,
                pause_approved BOOLEAN DEFAULT FALSE,
                pause_approved_by TEXT,
                pause_approved_at TIMESTAMP,
                pause_deadline TIMESTAMP,
                deadline TIMESTAMP,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                started_at TIMESTAMP,
                completed_at TIMESTAMP,
                UNIQUE(user_id, exam_type, subject, grade)
            )
        ''')
        
        # 升级历史表
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS nine_year_upgrade_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id TEXT NOT NULL,
                from_grade VARCHAR(20),
                to_grade VARCHAR(20) NOT NULL,
                upgrade_type VARCHAR(20) NOT NULL,
                status VARCHAR(20) DEFAULT 'completed',
                reason TEXT,
                approved_by TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # 暂停申请表
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS nine_year_pause_requests (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id TEXT NOT NULL,
                exam_id INTEGER NOT NULL,
                reason TEXT NOT NULL,
                status VARCHAR(20) DEFAULT 'pending',
                approved_by TEXT,
                approved_at TIMESTAMP,
                rejection_reason TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (exam_id) REFERENCES nine_year_exams(id)
            )
        ''')
        
        # 权限记录表
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS nine_year_permission_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id TEXT NOT NULL,
                action VARCHAR(50) NOT NULL,
                resource VARCHAR(50) NOT NULL,
                old_permission INTEGER,
                new_permission INTEGER,
                reason TEXT,
                operator_id TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        self.conn.commit()
        self.close()
        print("✅ 9年制升级系统数据库初始化完成")
    
    def get_passing_score(self, max_score: float) -> float:
        """计算及格分数（60%）"""
        return max_score * 0.6
    
    def get_student_grade_info(self, user_id: str) -> Optional[Dict]:
        """获取学生年级信息"""
        self.connect()
        self.cursor.execute('''
            SELECT * FROM nine_year_grades WHERE user_id = ?
        ''', (user_id,))
        row = self.cursor.fetchone()
        self.close()
        
        if row:
            return dict(row)
        return None
    
    def register_student_grade(self, user_id: str, grade: GradeLevel) -> bool:
        """注册学生年级"""
        self.connect()
        try:
            self.cursor.execute('''
                INSERT INTO nine_year_grades (user_id, current_grade, grade_status, permission_level)
                VALUES (?, ?, 'normal', 20)
            ''', (user_id, grade.value))
            self.conn.commit()
            self.close()
            return True
        except sqlite3.IntegrityError:
            self.close()
            return False
    
    def confirm_grade(self, user_id: str) -> bool:
        """确认年级"""
        self.connect()
        self.cursor.execute('''
            UPDATE nine_year_grades 
            SET is_confirmed = TRUE, confirmed_at = CURRENT_TIMESTAMP
            WHERE user_id = ?
        ''', (user_id,))
        self.conn.commit()
        affected = self.cursor.rowcount
        self.close()
        return affected > 0
    
    def create_exam_record(self, user_id: str, exam_type: str, subject: Subject, grade: GradeLevel) -> Optional[int]:
        """创建考试记录"""
        self.connect()
        try:
            max_score = SubjectMaxScore.get_max_score(subject, grade)
            self.cursor.execute('''
                INSERT INTO nine_year_exams (user_id, exam_type, subject, grade, max_score, status, deadline)
                VALUES (?, ?, ?, ?, ?, 'not_started', ?)
            ''', (user_id, exam_type, subject.value, grade.value, max_score, self._calculate_deadline(exam_type)))
            
            exam_id = self.cursor.lastrowid
            self.conn.commit()
            self.close()
            return exam_id
        except sqlite3.IntegrityError:
            self.close()
            return None
    
    def _calculate_deadline(self, exam_type: str) -> str:
        """计算截止时间"""
        now = datetime.now()
        if exam_type == "midterm":
            return datetime(now.year, 4, 30, 23, 59, 59).isoformat()
        elif exam_type == "final":
            return datetime(now.year, 7, 31, 23, 59, 59).isoformat()
        elif exam_type == "makeup":
            return datetime(now.year, 8, 20, 23, 59, 59).isoformat()
        else:
            return datetime(now.year, 12, 31, 23, 59, 59).isoformat()
    
    def start_exam(self, exam_id: int) -> Tuple[bool, str]:
        """开始考试"""
        self.connect()
        
        # 检查考试状态
        self.cursor.execute('''
            SELECT * FROM nine_year_exams WHERE id = ?
        ''', (exam_id,))
        exam = self.cursor.fetchone()
        
        if not exam:
            self.close()
            return False, "考试不存在"
        
        if exam['status'] != 'not_started':
            self.close()
            return False, "考试已无法开始"
        
        # 检查权限
        if exam['status'] == 'paused':
            self.close()
            return False, "考试已暂停，请等待恢复"
        
        # 更新考试状态
        self.cursor.execute('''
            UPDATE nine_year_exams 
            SET status = 'in_progress', started_at = CURRENT_TIMESTAMP
            WHERE id = ?
        ''', (exam_id,))
        
        self.conn.commit()
        self.close()
        return True, "考试已开始"
    
    def pause_exam_request(self, exam_id: int, user_id: str, reason: str) -> Tuple[bool, str, Optional[int]]:
        """申请暂停考试"""
        self.connect()
        
        # 检查考试状态
        self.cursor.execute('''
            SELECT * FROM nine_year_exams WHERE id = ? AND user_id = ?
        ''', (exam_id, user_id))
        exam = self.cursor.fetchone()
        
        if not exam:
            self.close()
            return False, "考试不存在或无权操作", None
        
        if exam['status'] != 'in_progress':
            self.close()
            return False, "只有进行中的考试可以暂停", None
        
        if exam['is_paused']:
            self.close()
            return False, "考试已经暂停过", None
        
        # 创建暂停申请
        self.cursor.execute('''
            INSERT INTO nine_year_pause_requests (user_id, exam_id, reason)
            VALUES (?, ?, ?)
        ''', (user_id, exam_id, reason))
        
        request_id = self.cursor.lastrowid
        self.conn.commit()
        self.close()
        
        return True, "暂停申请已提交", request_id
    
    def approve_pause_request(self, request_id: int, teacher_id: str, approved: bool, comment: str = "") -> Tuple[bool, str]:
        """审批暂停申请"""
        self.connect()
        
        # 获取申请信息
        self.cursor.execute('''
            SELECT * FROM nine_year_pause_requests WHERE id = ?
        ''', (request_id,))
        request = self.cursor.fetchone()
        
        if not request:
            self.close()
            return False, "申请不存在"
        
        if request['status'] != 'pending':
            self.close()
            return False, "申请已处理"
        
        if approved:
            # 批准: 更新申请状态和考试状态
            self.cursor.execute('''
                UPDATE nine_year_pause_requests 
                SET status = 'approved', approved_by = ?, approved_at = CURRENT_TIMESTAMP
                WHERE id = ?
            ''', (teacher_id, request_id))
            
            pause_deadline = (datetime.now() + timedelta(days=7)).strftime('%Y-%m-%d %H:%M:%S')
            self.cursor.execute('''
                UPDATE nine_year_exams 
                SET status = 'paused', is_paused = TRUE, pause_reason = ?, 
                    pause_approved = TRUE, pause_approved_by = ?, 
                    pause_approved_at = CURRENT_TIMESTAMP, pause_deadline = ?
                WHERE id = ?
            ''', (request['reason'], teacher_id, pause_deadline, request['exam_id']))
            
            # 更新学生权限
            self._update_student_permission(request['user_id'], PermissionLevel.STUDENT_LIMITED.value,
                                           f"考试暂停: {request['reason']}", teacher_id)
        else:
            # 拒绝: 记录拒绝原因
            self.cursor.execute('''
                UPDATE nine_year_pause_requests 
                SET status = 'rejected', approved_by = ?, approved_at = CURRENT_TIMESTAMP,
                    rejection_reason = ?
                WHERE id = ?
            ''', (teacher_id, comment, request_id))
            
            # 记录权限日志
            self._log_permission_change(request['user_id'], 'pause_request_denied',
                                       'in_progress', 'in_progress', comment, teacher_id)
        
        self.conn.commit()
        self.close()
        
        return True, "审批完成"
    
    def submit_exam(self, exam_id: int, score: float) -> Tuple[bool, str]:
        """提交考试成绩"""
        self.connect()
        
        # 获取考试信息
        self.cursor.execute('''
            SELECT * FROM nine_year_exams WHERE id = ?
        ''', (exam_id,))
        exam = self.cursor.fetchone()
        
        if not exam:
            self.close()
            return False, "考试不存在"
        
        if exam['status'] not in ['in_progress', 'paused']:
            self.close()
            return False, "考试状态不允许提交"
        
        # 判断是否及格
        passing_score = self.get_passing_score(exam['max_score'])
        status = 'passed' if score >= passing_score else 'failed'
        
        # 更新考试记录
        self.cursor.execute('''
            UPDATE nine_year_exams 
            SET score = ?, status = ?, completed_at = CURRENT_TIMESTAMP
            WHERE id = ?
        ''', (score, status, exam_id))
        
        self.conn.commit()
        self.close()
        
        return True, f"成绩: {score}, 状态: {'及格' if status == 'passed' else '不及格'}"
    
    def check_upgrade_eligibility(self, user_id: str) -> Dict[str, Any]:
        """检查学生升级资格"""
        self.connect()
        
        # 获取学生年级信息
        self.cursor.execute('''
            SELECT * FROM nine_year_grades WHERE user_id = ?
        ''', (user_id,))
        grade_info = self.cursor.fetchone()
        
        if not grade_info:
            self.close()
            return {
                'eligible': False,
                'reason': '学生信息不存在',
                'current_grade': None
            }
        
        current_grade = grade_info['current_grade']
        
        # 检查是否有待完成的考试
        self.cursor.execute('''
            SELECT * FROM nine_year_exams 
            WHERE user_id = ? AND grade = ? AND status NOT IN ('passed', 'failed')
        ''', (user_id, current_grade))
        pending_exams = self.cursor.fetchall()
        
        if pending_exams:
            self.close()
            return {
                'eligible': False,
                'reason': '还有未完成的考试',
                'pending_exams': [dict(e) for e in pending_exams],
                'current_grade': current_grade
            }
        
        # 检查期中和期末成绩
        self.cursor.execute('''
            SELECT * FROM nine_year_exams 
            WHERE user_id = ? AND grade = ? AND exam_type IN ('midterm', 'final')
        ''', (user_id, current_grade))
        exams = self.cursor.fetchall()
        
        midterm_passed = False
        final_passed = False
        midterm_failed = False
        final_failed = False
        
        for exam in exams:
            if exam['exam_type'] == 'midterm':
                midterm_passed = exam['status'] == 'passed'
                midterm_failed = exam['status'] == 'failed'
            elif exam['exam_type'] == 'final':
                final_passed = exam['status'] == 'passed'
                final_failed = exam['status'] == 'failed'
        
        # 判断升级资格
        if midterm_passed and final_passed:
            # 情况1: 都及格 - 正常升级
            self.close()
            return {
                'eligible': True,
                'upgrade_type': 'normal',
                'reason': '期中和期末考试都及格',
                'current_grade': current_grade,
                'next_grade': self._get_next_grade(current_grade)
            }
        
        elif midterm_failed or final_failed:
            # 情况2: 需要检查补考
            self.cursor.execute('''
                SELECT * FROM nine_year_exams 
                WHERE user_id = ? AND grade = ? AND exam_type = 'makeup'
            ''', (user_id, current_grade))
            makeup = self.cursor.fetchone()
            
            if makeup:
                if makeup['status'] == 'passed':
                    # 补考及格 - 条件升级
                    self.close()
                    return {
                        'eligible': True,
                        'upgrade_type': 'conditional',
                        'reason': '补考及格，条件升级',
                        'current_grade': current_grade,
                        'next_grade': self._get_next_grade(current_grade),
                        'restrictions': ['基础难度考试', '需完成补修课程']
                    }
                else:
                    # 补考不及格 - 不能升级
                    self.close()
                    return {
                        'eligible': False,
                        'upgrade_type': 'failed',
                        'reason': '补考不及格，需留级',
                        'current_grade': current_grade,
                        'next_grade': None,
                        'action_required': '请联系教师或管理员'
                    }
            else:
                # 有不及格但还没有补考
                self.close()
                return {
                    'eligible': False,
                    'upgrade_type': 'pending_makeup',
                    'reason': '存在不及格考试，需要参加补考',
                    'current_grade': current_grade,
                    'failed_exams': [dict(e) for e in exams if e['status'] == 'failed']
                }
        
        else:
            self.close()
            return {
                'eligible': False,
                'reason': '考试未完成',
                'current_grade': current_grade
            }
    
    def _get_next_grade(self, current: str) -> Optional[str]:
        """获取下一个年级"""
        grade_order = ['grade1', 'grade2', 'grade3', 'grade4', 'grade5', 'grade6',
                      'grade7', 'grade8', 'grade9']
        try:
            current_index = grade_order.index(current)
            if current_index < len(grade_order) - 1:
                return grade_order[current_index + 1]
        except ValueError:
            pass
        return None
    
    def perform_upgrade(self, user_id: str, upgrade_type: str, operator_id: str = "system", reason: str = "") -> Tuple[bool, str]:
        """执行升级操作"""
        self.connect()
        
        # 检查升级资格
        eligibility = self.check_upgrade_eligibility(user_id)
        
        if not eligibility['eligible']:
            self.close()
            return False, eligibility['reason']
        
        current_grade = eligibility['current_grade']
        next_grade = eligibility.get('next_grade')
        
        if not next_grade:
            self.close()
            return False, "已达到最高年级"
        
        # 更新学生年级
        new_status = 'normal'
        new_permission = 20
        
        if upgrade_type == 'conditional':
            new_status = 'conditional'
            new_permission = 10
        
        self.cursor.execute('''
            UPDATE nine_year_grades 
            SET current_grade = ?, grade_status = ?, permission_level = ?, 
                updated_at = CURRENT_TIMESTAMP
            WHERE user_id = ?
        ''', (next_grade, new_status, new_permission, user_id))
        
        # 记录升级历史
        self.cursor.execute('''
            INSERT INTO nine_year_upgrade_history 
            (user_id, from_grade, to_grade, upgrade_type, status, reason, approved_by)
            VALUES (?, ?, ?, ?, 'completed', ?, ?)
        ''', (user_id, current_grade, next_grade, upgrade_type, reason, operator_id))
        
        # 记录权限变更
        self._log_permission_change(user_id, 'upgrade',
                                   str(10 if upgrade_type == 'conditional' else 20),
                                   str(new_permission),
                                   f"升级类型: {upgrade_type}", operator_id)
        
        self.conn.commit()
        self.close()
        
        return True, f"成功升级到{next_grade}"
    
    def force_repeat(self, user_id: str, operator_id: str, reason: str = "") -> Tuple[bool, str]:
        """强制留级（管理员操作）"""
        self.connect()
        
        # 获取当前年级信息
        self.cursor.execute('''
            SELECT * FROM nine_year_grades WHERE user_id = ?
        ''', (user_id,))
        grade_info = self.cursor.fetchone()
        
        if not grade_info:
            self.close()
            return False, "学生信息不存在"
        
        # 更新年级状态为留级
        self.cursor.execute('''
            UPDATE nine_year_grades 
            SET grade_status = 'repeating', permission_level = ?,
                updated_at = CURRENT_TIMESTAMP
            WHERE user_id = ?
        ''', (PermissionLevel.STUDENT_RESTRICTED.value, user_id))
        
        # 记录升级历史
        self.cursor.execute('''
            INSERT INTO nine_year_upgrade_history 
            (user_id, from_grade, to_grade, upgrade_type, status, reason, approved_by)
            VALUES (?, ?, ?, 'force_repeat', 'completed', ?, ?)
        ''', (user_id, grade_info['current_grade'], grade_info['current_grade'], reason, operator_id))
        
        # 记录权限变更
        self._log_permission_change(user_id, 'force_repeat',
                                   str(grade_info['permission_level']),
                                   str(PermissionLevel.STUDENT_RESTRICTED.value),
                                   reason, operator_id)
        
        self.conn.commit()
        self.close()
        
        return True, f"学生已留级: {reason}"
    
    def _update_student_permission(self, user_id: str, new_permission: int, reason: str, operator_id: str):
        """更新学生权限"""
        self.cursor.execute('''
            SELECT permission_level FROM nine_year_grades WHERE user_id = ?
        ''', (user_id,))
        row = self.cursor.fetchone()
        old_permission = row['permission_level'] if row else 0
        
        self.cursor.execute('''
            UPDATE nine_year_grades 
            SET permission_level = ?, updated_at = CURRENT_TIMESTAMP
            WHERE user_id = ?
        ''', (new_permission, user_id))
        
        self._log_permission_change(user_id, 'permission_update',
                                   str(old_permission), str(new_permission),
                                   reason, operator_id)
    
    def _log_permission_change(self, user_id: str, action: str, old_perm: str, 
                              new_perm: str, reason: str, operator_id: str):
        """记录权限变更日志"""
        self.cursor.execute('''
            INSERT INTO nine_year_permission_logs 
            (user_id, action, resource, old_permission, new_permission, reason, operator_id)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (user_id, action, 'grade', old_perm, new_perm, reason, operator_id))
    
    def get_student_status(self, user_id: str) -> Dict[str, Any]:
        """获取学生完整状态"""
        self.connect()
        
        # 获取年级信息
        self.cursor.execute('''
            SELECT * FROM nine_year_grades WHERE user_id = ?
        ''', (user_id,))
        grade_info = self.cursor.fetchone()
        
        # 获取考试记录
        self.cursor.execute('''
            SELECT * FROM nine_year_exams WHERE user_id = ? ORDER BY created_at DESC
        ''', (user_id,))
        exams = self.cursor.fetchall()
        
        # 获取升级历史
        self.cursor.execute('''
            SELECT * FROM nine_year_upgrade_history WHERE user_id = ? ORDER BY created_at DESC
        ''', (user_id,))
        upgrades = self.cursor.fetchall()
        
        # 获取权限日志
        self.cursor.execute('''
            SELECT * FROM nine_year_permission_logs WHERE user_id = ? ORDER BY created_at DESC LIMIT 10
        ''', (user_id,))
        permission_logs = self.cursor.fetchall()
        
        self.close()
        
        return {
            'grade_info': dict(grade_info) if grade_info else None,
            'exams': [dict(e) for e in exams],
            'upgrades': [dict(u) for u in upgrades],
            'permission_logs': [dict(l) for l in permission_logs],
            'eligibility': self.check_upgrade_eligibility(user_id)
        }
    
    def get_pending_pause_requests(self, teacher_id: str) -> List[Dict]:
        """获取待审批的暂停申请（教师）"""
        self.connect()
        self.cursor.execute('''
            SELECT pr.*, e.exam_type, e.subject, e.grade
            FROM nine_year_pause_requests pr
            JOIN nine_year_exams e ON pr.exam_id = e.id
            WHERE pr.status = 'pending'
            ORDER BY pr.created_at DESC
        ''')
        requests = self.cursor.fetchall()
        self.close()
        
        return [dict(r) for r in requests]
    
    def get_upgrade_report(self) -> Dict[str, Any]:
        """获取升级报告"""
        self.connect()
        
        # 统计各状态学生数
        self.cursor.execute('''
            SELECT grade_status, COUNT(*) as count 
            FROM nine_year_grades 
            GROUP BY grade_status
        ''')
        status_counts = {row['grade_status']: row['count'] for row in self.cursor.fetchall()}
        
        # 统计本月升级人数
        self.cursor.execute('''
            SELECT COUNT(*) as count 
            FROM nine_year_upgrade_history 
            WHERE strftime('%Y-%m', created_at) = strftime('%Y-%m', 'now')
        ''')
        monthly_upgrades = self.cursor.fetchone()['count']
        
        # 统计补考人数
        self.cursor.execute('''
            SELECT COUNT(DISTINCT user_id) as count 
            FROM nine_year_exams 
            WHERE exam_type = 'makeup'
        ''')
        makeup_count = self.cursor.fetchone()['count']
        
        # 待审批暂停申请
        self.cursor.execute('''
            SELECT COUNT(*) as count 
            FROM nine_year_pause_requests 
            WHERE status = 'pending'
        ''')
        pending_pauses = self.cursor.fetchone()['count']
        
        self.close()
        
        return {
            'status_distribution': status_counts,
            'monthly_upgrades': monthly_upgrades,
            'makeup_students': makeup_count,
            'pending_pauses': pending_pauses,
            'generated_at': datetime.now().isoformat()
        }


def main():
    """主函数 - 测试升级系统"""
    system = NineYearUpgradeSystem()
    
    print("=" * 80)
    print("MTSCOS 9年制学生升级管理系统 (v1.1)")
    print("=" * 80)
    print("📚 完整9年制体系: 小学1年级至初中3年级")
    print("=" * 80)
    
    # 初始化数据库
    system.init_database()
    
    # 测试用例
    test_user_id = "test_student_001"
    
    # 1. 注册学生 - 小学1年级
    print("\n📝 测试: 注册学生")
    if system.register_student_grade(test_user_id, GradeLevel.GRADE_1):
        print("✅ 学生注册成功 - 小学1年级")
    
    # 2. 确认年级
    print("\n📝 测试: 确认年级")
    if system.confirm_grade(test_user_id):
        print("✅ 年级确认成功")
    
    # 3. 创建考试 - 期中数学
    print("\n📝 测试: 创建考试")
    exam_id = system.create_exam_record(test_user_id, "midterm", Subject.MATH, GradeLevel.GRADE_1)
    if exam_id:
        print(f"✅ 期中考试创建成功 (ID: {exam_id})")
    
    # 4. 提交成绩（及格）
    print("\n📝 测试: 提交成绩（及格）")
    result = system.submit_exam(exam_id, 85)
    if result[0]:
        print(f"✅ 成绩提交成功: {result[1]}")
    
    # 5. 检查升级资格
    print("\n📝 测试: 检查升级资格")
    eligibility = system.check_upgrade_eligibility(test_user_id)
    print(f"升级资格: {json.dumps(eligibility, ensure_ascii=False, indent=2)}")
    
    # 6. 获取学生状态
    print("\n📝 测试: 获取学生完整状态")
    status = system.get_student_status(test_user_id)
    print(f"学生状态: {json.dumps(status, ensure_ascii=False, indent=2)}")
    
    print("\n" + "=" * 80)
    print("✅ 测试完成！")
    print("=" * 80)


if __name__ == '__main__':
    main()
