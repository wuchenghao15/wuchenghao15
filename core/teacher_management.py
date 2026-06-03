# -*- coding: utf-8 -*-
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
教师用户管理模块
教师用户必须通过管理员委派，不能直接注册
"""

from typing import Dict, List, Any, Optional
from datetime import datetime
import uuid
import json
from enum import Enum


class TeacherStatus(Enum):
    """教师状态"""
    ACTIVE = "活跃"
    INACTIVE = "非活跃"
    SUSPENDED = "暂停"


class TeacherSpecialty(Enum):
    """教师专长"""
    CHINESE = "语文"
    MATH = "数学"
    ENGLISH = "英语"
    PHYSICS = "物理"
    CHEMISTRY = "化学"
    BIOLOGY = "生物"
    HISTORY = "历史"
    GEOGRAPHY = "地理"
    POLITICS = "政治"
    GENERAL = "综合"


class Teacher:
    """教师用户"""
    
    def __init__(self, user_id: str, username: str, name: str):
        self.teacher_id = user_id
        self.username = username
        self.name = name
        self.email = ""
        self.phone = ""
        self.specialties: List[TeacherSpecialty] = []
        self.grades: List[str] = []  # 教授年级
        self.status = TeacherStatus.ACTIVE
        self.created_at = datetime.now()
        self.created_by = ""
        self.assigned_classes: List[str] = []
        self.education_level = ""
        self.teach_experience = ""
        self.certifications: List[str] = []
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "teacher_id": self.teacher_id,
            "username": self.username,
            "name": self.name,
            "email": self.email,
            "phone": self.phone,
            "specialties": [s.value for s in self.specialties],
            "grades": self.grades,
            "status": self.status.value,
            "created_at": self.created_at.isoformat(),
            "created_by": self.created_by,
            "assigned_classes": self.assigned_classes,
            "education_level": self.education_level,
            "teach_experience": self.teach_experience,
            "certifications": self.certifications
        }


class TeacherManager:
    """教师管理器"""
    
    def __init__(self):
        self.teachers: Dict[str, Teacher] = {}
        self.admin_delegations: List[Dict[str, Any]] = []
    
    def delegate_teacher(self, user_id: str, username: str, name: str, 
                        created_by: str, specialties: List[TeacherSpecialty],
                        grades: List[str]) -> Teacher:
        """委派教师"""
        teacher = Teacher(user_id, username, name)
        teacher.specialties = specialties
        teacher.grades = grades
        teacher.created_by = created_by
        teacher.created_at = datetime.now()
        
        self.teachers[user_id] = teacher
        
        delegation = {
            "delegation_id": str(uuid.uuid4()),
            "teacher_id": user_id,
            "username": username,
            "name": name,
            "created_by": created_by,
            "created_at": datetime.now().isoformat(),
            "specialties": [s.value for s in specialties],
            "grades": grades
        }
        self.admin_delegations.append(delegation)
        
        return teacher
    
    def get_teacher(self, teacher_id: str) -> Optional[Teacher]:
        """获取教师"""
        return self.teachers.get(teacher_id)
    
    def update_teacher(self, teacher_id: str, teacher_data: Dict[str, Any]) -> bool:
        """更新教师信息"""
        teacher = self.teachers.get(teacher_id)
        if not teacher:
            return False
        
        if "name" in teacher_data:
            teacher.name = teacher_data["name"]
        if "email" in teacher_data:
            teacher.email = teacher_data["email"]
        if "phone" in teacher_data:
            teacher.phone = teacher_data["phone"]
        if "specialties" in teacher_data:
            teacher.specialties = [TeacherSpecialty(s) for s in teacher_data["specialties"]]
        if "grades" in teacher_data:
            teacher.grades = teacher_data["grades"]
        if "status" in teacher_data:
            teacher.status = TeacherStatus(teacher_data["status"])
        if "education_level" in teacher_data:
            teacher.education_level = teacher_data["education_level"]
        if "teach_experience" in teacher_data:
            teacher.teach_experience = teacher_data["teach_experience"]
        if "certifications" in teacher_data:
            teacher.certifications = teacher_data["certifications"]
        
        return True
    
    def suspend_teacher(self, teacher_id: str, reason: str) -> bool:
        """暂停教师"""
        teacher = self.teachers.get(teacher_id)
        if not teacher:
            return False
        
        teacher.status = TeacherStatus.SUSPENDED
        return True
    
    def activate_teacher(self, teacher_id: str) -> bool:
        """激活教师"""
        teacher = self.teachers.get(teacher_id)
        if not teacher:
            return False
        
        teacher.status = TeacherStatus.ACTIVE
        return True
    
    def get_teachers_by_specialty(self, specialty: TeacherSpecialty) -> List[Teacher]:
        """按专长获取教师"""
        return [t for t in self.teachers.values() if specialty in t.specialties]
    
    def get_teachers_by_grade(self, grade: str) -> List[Teacher]:
        """按年级获取教师"""
        return [t for t in self.teachers.values() if grade in t.grades]
    
    def get_all_teachers(self) -> List[Teacher]:
        """获取所有教师"""
        return list(self.teachers.values())
    
    def approve_exam_pause(self, exam_id: str) -> bool:
        """审批考试暂停"""
        # 这里需要连接考试系统
        return True
    
    def delegate_class(self, teacher_id: str, class_id: str) -> bool:
        """委派班级"""
        teacher = self.teachers.get(teacher_id)
        if not teacher:
            return False
        
        if class_id not in teacher.assigned_classes:
            teacher.assigned_classes.append(class_id)
        return True


# 全局实例
teacher_manager = TeacherManager()
