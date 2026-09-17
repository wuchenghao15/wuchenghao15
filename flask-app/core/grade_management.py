# -*- coding: utf-8 -*-
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
年级管理模块
支持9年制义务教育系统，包含年级选择、自动升级、考试管理
"""

from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
import uuid
import json
from enum import Enum


class GradeLevel(Enum):
    """年级级别"""
    GRADE_1 = "一年级"
    GRADE_2 = "二年级"
    GRADE_3 = "三年级"
    GRADE_4 = "四年级"
    GRADE_5 = "五年级"
    GRADE_6 = "六年级"
    GRADE_7 = "七年级"
    GRADE_8 = "八年级"
    GRADE_9 = "九年级"


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
    """科目最大分值"""
    @staticmethod
    def get_max_score(subject: Subject, grade: GradeLevel) -> int:
        """根据年级和科目获取最大分值"""
        if grade in [GradeLevel.GRADE_1, GradeLevel.GRADE_2, GradeLevel.GRADE_3, 
                     GradeLevel.GRADE_4, GradeLevel.GRADE_5, GradeLevel.GRADE_6]:
            # 小学科目分值
            if subject in [Subject.CHINESE, Subject.MATH]:
                return 100
            elif subject == Subject.ENGLISH:
                return 100
            else:
                return 100
        else:
            # 初中科目分值
            if subject in [Subject.CHINESE, Subject.MATH, Subject.ENGLISH]:
                return 150
            elif subject in [Subject.PHYSICS, Subject.CHEMISTRY]:
                return 100
            else:
                return 100


class StudentGrade:
    """学生年级信息"""
    
    def __init__(self, user_id: str):
        self.user_id = user_id
        self.current_grade: Optional[GradeLevel] = None
        self.is_grade_confirmed = False
        self.grade_confirmed_at: Optional[datetime] = None
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
            # 已经是最高年级（初三）
            return False
        
        self.current_grade = grade_order[current_index + 1]
        return True


class ExamStatus(Enum):
    """考试状态"""
    NOT_STARTED = "未开始"
    IN_PROGRESS = "进行中"
    PAUSED = "已暂停"
    COMPLETED = "已完成"
    FAILED = "不及格"
    PASSED = "及格"


class ExamType(Enum):
    """考试类型"""
    MIDTERM_EXAM = "期中考试"
    FINAL_EXAM = "期末考试"
    MAKEUP_EXAM = "补考"
    PRACTICE_TEST = "平时测试"


class Exam:
    """考试"""
    
    def __init__(self, user_id: str, subject: Subject, exam_type: ExamType, grade: GradeLevel):
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
        
        if self.exam_type == ExamType.MIDTERM_EXAM:
            # 期中考试必须在4月30日前完成
            self.deadline = datetime(now.year, 4, 30, 23, 59, 59)
        elif self.exam_type == ExamType.FINAL_EXAM:
            # 期末考试必须在7月31日前完成
            if now.month < 6:
                self.deadline = datetime(now.year, 7, 31, 23, 59, 59)
            else:
                self.deadline = datetime(now.year, 7, 31, 23, 59, 59)
        elif self.exam_type == ExamType.MAKEUP_EXAM:
            # 补考必须在8月20日前完成
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


class ExamManager:
    """考试管理器"""
    
    def __init__(self):
        self.exams: Dict[str, List[Exam]] = {}
        self.student_grades: Dict[str, StudentGrade] = {}
    
    def create_exam(self, user_id: str, subject: Subject, exam_type: ExamType, grade: GradeLevel) -> Exam:
        """创建考试"""
        if user_id not in self.exams:
            self.exams[user_id] = []
        
        exam = Exam(user_id, subject, exam_type, grade)
        self.exams[user_id].append(exam)
        return exam
    
    def get_student_grade(self, user_id: str) -> Optional[StudentGrade]:
        """获取学生年级"""
        return self.student_grades.get(user_id)
    
    def create_student_grade(self, user_id: str) -> StudentGrade:
        """创建学生年级"""
        if user_id not in self.student_grades:
            self.student_grades[user_id] = StudentGrade(user_id)
        return self.student_grades[user_id]
    
    def should_auto_load_final_exam(self) -> bool:
        """6月20日自动加载期末考试"""
        now = datetime.now()
        return now.month == 6 and now.day >= 20
    
    def should_auto_load_midterm_exam(self) -> bool:
        """3月20日自动加载期中考试"""
        now = datetime.now()
        return now.month == 3 and now.day >= 20
    
    def has_failed_midterm_exams(self, user_id: str, grade: GradeLevel) -> bool:
        """检查是否有不及格的期中考试"""
        if user_id not in self.exams:
            return False
        
        for exam in self.exams[user_id]:
            if exam.grade == grade and exam.exam_type == ExamType.MIDTERM_EXAM:
                if exam.status == ExamStatus.FAILED:
                    return True
        
        return False
    
    def auto_upgrade_students(self) -> int:
        """9月1日自动升级学生年级"""
        now = datetime.now()
        if not (now.month == 9 and now.day == 1):
            return 0
        
        upgraded_count = 0
        
        for user_id, student_grade in self.student_grades.items():
            if not student_grade.current_grade or not student_grade.is_grade_confirmed:
                continue
            
            # 检查期中考试和期末考试是否都及格
            if self.has_failed_midterm_exams(user_id, student_grade.current_grade):
                continue
            if self.has_failed_final_exams(user_id, student_grade.current_grade):
                continue
            
            if student_grade.auto_upgrade():
                upgraded_count += 1
        
        return upgraded_count
    
    def has_failed_final_exams(self, user_id: str, grade: GradeLevel) -> bool:
        """检查是否有不及格的期末考试"""
        if user_id not in self.exams:
            return False
        
        for exam in self.exams[user_id]:
            if exam.grade == grade and exam.exam_type == ExamType.FINAL_EXAM:
                if exam.status == ExamStatus.FAILED:
                    return True
        
        return False
    
    def get_student_exams(self, user_id: str) -> List[Exam]:
        """获取学生考试"""
        return self.exams.get(user_id, [])
    
    def calculate_exam_difficulty(self, user_id: str, subject: Subject, grade: GradeLevel) -> float:
        """根据平时测试平衡试卷难度"""
        if user_id not in self.exams:
            return 0.5
        
        practice_scores = []
        for exam in self.exams[user_id]:
            if exam.grade == grade and exam.exam_type == ExamType.PRACTICE_TEST and exam.score:
                practice_scores.append(exam.score)
        
        if not practice_scores:
            return 0.5
        
        avg_score = sum(practice_scores) / len(practice_scores)
        max_score = SubjectMaxScore.get_max_score(subject, grade)
        
        # 平均分越高，难度越大
        difficulty = avg_score / max_score
        return min(1.0, max(0.1, difficulty))


# 全局实例
exam_manager = ExamManager()
