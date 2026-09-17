# -*- coding: utf-8 -*-
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
申请审批系统
用于处理年级变更申请、考试暂停申请等
"""

from typing import Dict, List, Any, Optional
from datetime import datetime
import uuid
import json
from enum import Enum


class ApplicationType(Enum):
    """申请类型"""
    GRADE_CHANGE = "年级变更"
    EXAM_PAUSE = "考试暂停"
    OTHER = "其他"


class ApplicationStatus(Enum):
    """申请状态"""
    PENDING = "待审批"
    APPROVED = "已通过"
    REJECTED = "已拒绝"
    CANCELLED = "已取消"


class Application:
    """申请"""
    
    def __init__(self, user_id: str, application_type: ApplicationType, 
                 title: str, description: str = ""):
        self.application_id = str(uuid.uuid4())
        self.user_id = user_id
        self.type = application_type
        self.title = title
        self.description = description
        self.status = ApplicationStatus.PENDING
        self.created_at = datetime.now()
        self.updated_at = datetime.now()
        self.reviewed_by: Optional[str] = None
        self.reviewed_at: Optional[datetime] = None
        self.review_comment: Optional[str] = None
        self.data: Dict[str, Any] = {}
    
    def approve(self, reviewed_by: str, comment: str = "") -> bool:
        """审批通过"""
        if self.status != ApplicationStatus.PENDING:
            return False
        
        self.status = ApplicationStatus.APPROVED
        self.reviewed_by = reviewed_by
        self.reviewed_at = datetime.now()
        self.review_comment = comment
        self.updated_at = datetime.now()
        return True
    
    def reject(self, reviewed_by: str, comment: str = "") -> bool:
        """拒绝申请"""
        if self.status != ApplicationStatus.PENDING:
            return False
        
        self.status = ApplicationStatus.REJECTED
        self.reviewed_by = reviewed_by
        self.reviewed_at = datetime.now()
        self.review_comment = comment
        self.updated_at = datetime.now()
        return True
    
    def cancel(self) -> bool:
        """取消申请"""
        if self.status != ApplicationStatus.PENDING:
            return False
        
        self.status = ApplicationStatus.CANCELLED
        self.updated_at = datetime.now()
        return True
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "application_id": self.application_id,
            "user_id": self.user_id,
            "type": self.type.value,
            "title": self.title,
            "description": self.description,
            "status": self.status.value,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "reviewed_by": self.reviewed_by,
            "reviewed_at": self.reviewed_at.isoformat() if self.reviewed_at else None,
            "review_comment": self.review_comment,
            "data": self.data
        }


class ApplicationManager:
    """申请管理器"""
    
    def __init__(self):
        self.applications: Dict[str, Application] = {}
        self.user_applications: Dict[str, List[str]] = {}
    
    def create_grade_change_application(self, user_id: str, 
                                        current_grade: str, new_grade: str, 
                                        reason: str) -> Application:
        """创建年级变更申请"""
        application = Application(
            user_id=user_id,
            application_type=ApplicationType.GRADE_CHANGE,
            title=f"年级变更申请: {current_grade} -> {new_grade}",
            description=reason
        )
        application.data = {
            "current_grade": current_grade,
            "new_grade": new_grade,
            "reason": reason
        }
        
        self.applications[application.application_id] = application
        
        if user_id not in self.user_applications:
            self.user_applications[user_id] = []
        self.user_applications[user_id].append(application.application_id)
        
        return application
    
    def create_exam_pause_application(self, user_id: str, exam_id: str, 
                                     subject: str, reason: str) -> Application:
        """创建考试暂停申请"""
        application = Application(
            user_id=user_id,
            application_type=ApplicationType.EXAM_PAUSE,
            title=f"考试暂停申请: {subject}",
            description=reason
        )
        application.data = {
            "exam_id": exam_id,
            "subject": subject,
            "reason": reason
        }
        
        self.applications[application.application_id] = application
        
        if user_id not in self.user_applications:
            self.user_applications[user_id] = []
        self.user_applications[user_id].append(application.application_id)
        
        return application
    
    def get_application(self, application_id: str) -> Optional[Application]:
        """获取申请"""
        return self.applications.get(application_id)
    
    def get_user_applications(self, user_id: str) -> List[Application]:
        """获取用户申请"""
        if user_id not in self.user_applications:
            return []
        
        return [
            self.applications[app_id] 
            for app_id in self.user_applications[user_id] 
            if app_id in self.applications
        ]
    
    def get_pending_applications(self) -> List[Application]:
        """获取待审批申请"""
        return [
            app for app in self.applications.values()
            if app.status == ApplicationStatus.PENDING
        ]
    
    def approve_application(self, application_id: str, reviewed_by: str, 
                          comment: str = "") -> Optional[Application]:
        """审批通过申请"""
        application = self.applications.get(application_id)
        if not application:
            return None
        
        if application.approve(reviewed_by, comment):
            return application
        return None
    
    def reject_application(self, application_id: str, reviewed_by: str, 
                          comment: str = "") -> Optional[Application]:
        """拒绝申请"""
        application = self.applications.get(application_id)
        if not application:
            return None
        
        if application.reject(reviewed_by, comment):
            return application
        return None
    
    def cancel_application(self, application_id: str, user_id: str) -> Optional[Application]:
        """取消申请"""
        application = self.applications.get(application_id)
        if not application:
            return None
        
        if application.user_id != user_id:
            return None
        
        if application.cancel():
            return application
        return None
    
    def get_grade_change_applications(self) -> List[Application]:
        """获取年级变更申请"""
        return [
            app for app in self.applications.values()
            if app.type == ApplicationType.GRADE_CHANGE
        ]
    
    def get_exam_pause_applications(self) -> List[Application]:
        """获取考试暂停申请"""
        return [
            app for app in self.applications.values()
            if app.type == ApplicationType.EXAM_PAUSE
        ]


# 全局实例
application_manager = ApplicationManager()
