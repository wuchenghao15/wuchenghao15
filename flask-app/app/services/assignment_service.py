"""作业服务 - MTSCOS AI项目"""

from typing import List, Optional
from datetime import datetime
from app.models.assignment import Assignment, AssignmentStatus, AssignmentType
from app.utils.logger import get_logger
from app.exceptions import (
    ValidationException,
    ResourceNotFoundException,
    AuthorizationException,
    BusinessException
)

logger = get_logger(__name__)


class AssignmentService:
    """作业服务"""
    
    @staticmethod
    def create_assignment(user_id: int, title: str, description: str = None,
                          assignment_type: str = 'homework', course_id: int = None,
                          subject: str = None, grade: str = None, total_score: int = 100,
                          due_date: str = None, max_attempts: int = 1,
                          allow_late_submission: bool = False) -> Optional[Assignment]:
        """创建作业"""
        if not title or not title.strip():
            raise ValidationException(
                message='作业标题不能为空',
                field_errors={'title': '作业标题不能为空'}
            )
        
        if assignment_type not in [AssignmentType.HOMEWORK, AssignmentType.QUIZ, AssignmentType.EXAM, AssignmentType.PROJECT, AssignmentType.ESSAY]:
            raise ValidationException(
                message='无效的作业类型',
                field_errors={'assignment_type': f'作业类型必须是: {", ".join([AssignmentType.HOMEWORK, AssignmentType.QUIZ, AssignmentType.EXAM, AssignmentType.PROJECT, AssignmentType.ESSAY])}'}
            )
        
        if total_score <= 0:
            raise ValidationException(
                message='总分必须大于0',
                field_errors={'total_score': '总分必须大于0'}
            )
        
        if max_attempts <= 0:
            raise ValidationException(
                message='最大尝试次数必须大于0',
                field_errors={'max_attempts': '最大尝试次数必须大于0'}
            )
        
        logger.info(f"创建作业: user_id={user_id}, title={title}")
        assignment = Assignment.create(
            title=title,
            description=description,
            assignment_type=assignment_type,
            course_id=course_id,
            subject=subject,
            grade=grade,
            total_score=total_score,
            due_date=due_date,
            max_attempts=max_attempts,
            allow_late_submission=allow_late_submission,
            created_by=user_id
        )
        
        if not assignment:
            raise BusinessException(
                message='作业创建失败',
                suggestion='请稍后重试或联系管理员'
            )
        
        return assignment
    
    @staticmethod
    def get_assignment(assignment_id: int, user_id: int = None) -> Optional[Assignment]:
        """获取作业详情"""
        assignment = Assignment.get_by_id(assignment_id)
        if not assignment:
            raise ResourceNotFoundException(
                message='作业不存在',
                resource_type='assignment'
            )
        
        if user_id and assignment.created_by != user_id:
            raise AuthorizationException(
                message='无权访问此作业',
                suggestion='请联系作业创建者获取访问权限'
            )
        
        return assignment
    
    @staticmethod
    def get_assignments(status: str = None, course_id: int = None, subject: str = None,
                        grade: str = None, page: int = 1, limit: int = 20) -> List[Assignment]:
        """获取作业列表"""
        return Assignment.get_all(status=status, course_id=course_id, subject=subject,
                                grade=grade, page=page, limit=limit)
    
    @staticmethod
    def get_user_assignments(user_id: int) -> List[Assignment]:
        """获取用户创建的作业"""
        return Assignment.get_by_user(user_id)
    
    @staticmethod
    def update_assignment(assignment_id: int, user_id: int, **kwargs) -> Optional[Assignment]:
        """更新作业"""
        assignment = Assignment.get_by_id(assignment_id)
        if not assignment:
            raise ResourceNotFoundException(
                message='作业不存在',
                resource_type='assignment'
            )
        
        if assignment.created_by != user_id:
            raise AuthorizationException(
                message='无权修改此作业',
                suggestion='只有作业创建者可以修改作业'
            )
        
        if 'title' in kwargs and (not kwargs['title'] or not kwargs['title'].strip()):
            raise ValidationException(
                message='作业标题不能为空',
                field_errors={'title': '作业标题不能为空'}
            )
        
        if 'total_score' in kwargs and kwargs['total_score'] <= 0:
            raise ValidationException(
                message='总分必须大于0',
                field_errors={'total_score': '总分必须大于0'}
            )
        
        logger.info(f"更新作业: assignment_id={assignment_id}, user_id={user_id}")
        if not assignment.update(**kwargs):
            raise BusinessException(
                message='作业更新失败',
                suggestion='请稍后重试或联系管理员'
            )
        
        return Assignment.get_by_id(assignment_id)
    
    @staticmethod
    def delete_assignment(assignment_id: int, user_id: int) -> bool:
        """删除作业"""
        assignment = Assignment.get_by_id(assignment_id)
        if not assignment:
            raise ResourceNotFoundException(
                message='作业不存在',
                resource_type='assignment'
            )
        
        if assignment.created_by != user_id:
            raise AuthorizationException(
                message='无权删除此作业',
                suggestion='只有作业创建者可以删除作业'
            )
        
        logger.info(f"删除作业: assignment_id={assignment_id}, user_id={user_id}")
        if not assignment.delete():
            raise BusinessException(
                message='作业删除失败',
                suggestion='请稍后重试或联系管理员'
            )
        
        return True
    
    @staticmethod
    def publish_assignment(assignment_id: int, user_id: int) -> Optional[Assignment]:
        """发布作业"""
        assignment = Assignment.get_by_id(assignment_id)
        if not assignment:
            raise ResourceNotFoundException(
                message='作业不存在',
                resource_type='assignment'
            )
        
        if assignment.created_by != user_id:
            raise AuthorizationException(
                message='无权发布此作业',
                suggestion='只有作业创建者可以发布作业'
            )
        
        if assignment.status == AssignmentStatus.PUBLISHED:
            raise BusinessException(
                message='作业已发布',
                suggestion='作业已经是发布状态，无需重复发布'
            )
        
        logger.info(f"发布作业: assignment_id={assignment_id}")
        if not assignment.publish():
            raise BusinessException(
                message='作业发布失败',
                suggestion='请稍后重试或联系管理员'
            )
        
        return Assignment.get_by_id(assignment_id)
    
    @staticmethod
    def close_assignment(assignment_id: int, user_id: int) -> Optional[Assignment]:
        """关闭作业"""
        assignment = Assignment.get_by_id(assignment_id)
        if not assignment:
            raise ResourceNotFoundException(
                message='作业不存在',
                resource_type='assignment'
            )
        
        if assignment.created_by != user_id:
            raise AuthorizationException(
                message='无权关闭此作业',
                suggestion='只有作业创建者可以关闭作业'
            )
        
        if assignment.status == AssignmentStatus.CLOSED:
            raise BusinessException(
                message='作业已关闭',
                suggestion='作业已经是关闭状态，无需重复关闭'
            )
        
        if assignment.status == AssignmentStatus.DRAFT:
            raise BusinessException(
                message='作业未发布',
                suggestion='只有已发布的作业才能关闭'
            )
        
        logger.info(f"关闭作业: assignment_id={assignment_id}")
        if not assignment.close():
            raise BusinessException(
                message='作业关闭失败',
                suggestion='请稍后重试或联系管理员'
            )
        
        return Assignment.get_by_id(assignment_id)
    
    @staticmethod
    def record_submission(assignment_id: int) -> bool:
        """记录提交"""
        assignment = Assignment.get_by_id(assignment_id)
        if assignment:
            return assignment.increment_submission_count()
        return False
    
    @staticmethod
    def record_completion(assignment_id: int) -> bool:
        """记录完成"""
        assignment = Assignment.get_by_id(assignment_id)
        if assignment:
            return assignment.increment_completed_count()
        return False
    
    @staticmethod
    def get_assignment_statistics() -> dict:
        """获取作业统计"""
        return Assignment.get_statistics()
    
    @staticmethod
    def search_assignments(keyword: str, page: int = 1, limit: int = 20) -> List[Assignment]:
        """搜索作业"""
        try:
            from app.utils.db import db_manager
            rows = db_manager.fetch_all("""
                SELECT * FROM assignments 
                WHERE (title LIKE ? OR description LIKE ?) AND status = 'published'
                ORDER BY created_at DESC LIMIT ? OFFSET ?
            """, (f"%{keyword}%", f"%{keyword}%", limit, (page - 1) * limit))
            return [Assignment._from_row(row) for row in rows]
        except Exception as e:
            logger.error(f"搜索作业失败: {str(e)}")
            return []
    
    @staticmethod
    def get_assignment_types() -> list:
        """获取作业类型列表"""
        return [
            {'value': AssignmentType.HOMEWORK, 'label': '家庭作业'},
            {'value': AssignmentType.QUIZ, 'label': '测验'},
            {'value': AssignmentType.EXAM, 'label': '考试'},
            {'value': AssignmentType.PROJECT, 'label': '项目作业'},
            {'value': AssignmentType.ESSAY, 'label': '论文'}
        ]
    
    @staticmethod
    def get_assignment_statuses() -> list:
        """获取作业状态列表"""
        return [
            {'value': AssignmentStatus.DRAFT, 'label': '草稿'},
            {'value': AssignmentStatus.PUBLISHED, 'label': '已发布'},
            {'value': AssignmentStatus.CLOSED, 'label': '已关闭'}
        ]