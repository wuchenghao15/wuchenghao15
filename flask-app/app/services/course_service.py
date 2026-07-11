"""课程服务 - MTSCOS AI项目"""

from typing import List, Optional
from datetime import datetime
from app.models.course import Course, CourseStatus, CourseType
from app.utils.logger import get_logger
from app.exceptions import (
    ValidationException,
    ResourceNotFoundException,
    AuthorizationException,
    BusinessException
)

logger = get_logger(__name__)


class CourseService:
    """课程服务"""
    
    @staticmethod
    def create_course(user_id: int, title: str, description: str = None, 
                      course_type: str = 'video', subject: str = None, 
                      grade: str = None, duration: int = 0, 
                      cover_image: str = None) -> Optional[Course]:
        """创建课程"""
        if not title or not title.strip():
            raise ValidationException(
                message='课程标题不能为空',
                field_errors={'title': '课程标题不能为空'}
            )
        
        if course_type not in [CourseType.VIDEO, CourseType.LIVE, CourseType.INTERACTIVE, CourseType.ASSESSMENT, CourseType.PRACTICE]:
            raise ValidationException(
                message='无效的课程类型',
                field_errors={'course_type': f'课程类型必须是: {", ".join([CourseType.VIDEO, CourseType.LIVE, CourseType.INTERACTIVE, CourseType.ASSESSMENT, CourseType.PRACTICE])}'}
            )
        
        logger.info(f"创建课程: user_id={user_id}, title={title}")
        course = Course.create(
            title=title,
            description=description,
            course_type=course_type,
            subject=subject,
            grade=grade,
            duration=duration,
            cover_image=cover_image,
            created_by=user_id
        )
        
        if not course:
            raise BusinessException(
                message='课程创建失败',
                suggestion='请稍后重试或联系管理员'
            )
        
        return course
    
    @staticmethod
    def get_course(course_id: int, user_id: int = None) -> Optional[Course]:
        """获取课程详情"""
        course = Course.get_by_id(course_id)
        if not course:
            raise ResourceNotFoundException(
                message='课程不存在',
                resource_type='course'
            )
        
        if user_id and course.created_by != user_id:
            raise AuthorizationException(
                message='无权访问此课程',
                suggestion='请联系课程创建者获取访问权限'
            )
        
        course.increment_view_count()
        return course
    
    @staticmethod
    def get_courses(status: str = None, subject: str = None, 
                    grade: str = None, page: int = 1, 
                    limit: int = 20) -> List[Course]:
        """获取课程列表"""
        return Course.get_all(status=status, subject=subject, grade=grade, 
                             page=page, limit=limit)
    
    @staticmethod
    def get_user_courses(user_id: int) -> List[Course]:
        """获取用户创建的课程"""
        return Course.get_by_user(user_id)
    
    @staticmethod
    def update_course(course_id: int, user_id: int, **kwargs) -> Optional[Course]:
        """更新课程"""
        course = Course.get_by_id(course_id)
        if not course:
            raise ResourceNotFoundException(
                message='课程不存在',
                resource_type='course'
            )
        
        if course.created_by != user_id:
            raise AuthorizationException(
                message='无权修改此课程',
                suggestion='只有课程创建者可以修改课程'
            )
        
        if 'title' in kwargs and (not kwargs['title'] or not kwargs['title'].strip()):
            raise ValidationException(
                message='课程标题不能为空',
                field_errors={'title': '课程标题不能为空'}
            )
        
        logger.info(f"更新课程: course_id={course_id}, user_id={user_id}")
        if not course.update(**kwargs):
            raise BusinessException(
                message='课程更新失败',
                suggestion='请稍后重试或联系管理员'
            )
        
        return Course.get_by_id(course_id)
    
    @staticmethod
    def delete_course(course_id: int, user_id: int) -> bool:
        """删除课程"""
        course = Course.get_by_id(course_id)
        if not course:
            raise ResourceNotFoundException(
                message='课程不存在',
                resource_type='course'
            )
        
        if course.created_by != user_id:
            raise AuthorizationException(
                message='无权删除此课程',
                suggestion='只有课程创建者可以删除课程'
            )
        
        logger.info(f"删除课程: course_id={course_id}, user_id={user_id}")
        if not course.delete():
            raise BusinessException(
                message='课程删除失败',
                suggestion='请稍后重试或联系管理员'
            )
        
        return True
    
    @staticmethod
    def publish_course(course_id: int, user_id: int) -> Optional[Course]:
        """发布课程"""
        course = Course.get_by_id(course_id)
        if not course:
            raise ResourceNotFoundException(
                message='课程不存在',
                resource_type='course'
            )
        
        if course.created_by != user_id:
            raise AuthorizationException(
                message='无权发布此课程',
                suggestion='只有课程创建者可以发布课程'
            )
        
        if course.status == CourseStatus.PUBLISHED:
            raise BusinessException(
                message='课程已发布',
                suggestion='课程已经是发布状态，无需重复发布'
            )
        
        logger.info(f"发布课程: course_id={course_id}")
        if not course.publish():
            raise BusinessException(
                message='课程发布失败',
                suggestion='请稍后重试或联系管理员'
            )
        
        return Course.get_by_id(course_id)
    
    @staticmethod
    def archive_course(course_id: int, user_id: int) -> Optional[Course]:
        """归档课程"""
        course = Course.get_by_id(course_id)
        if not course:
            raise ResourceNotFoundException(
                message='课程不存在',
                resource_type='course'
            )
        
        if course.created_by != user_id:
            raise AuthorizationException(
                message='无权归档此课程',
                suggestion='只有课程创建者可以归档课程'
            )
        
        if course.status == CourseStatus.ARCHIVED:
            raise BusinessException(
                message='课程已归档',
                suggestion='课程已经是归档状态，无需重复归档'
            )
        
        logger.info(f"归档课程: course_id={course_id}")
        if not course.archive():
            raise BusinessException(
                message='课程归档失败',
                suggestion='请稍后重试或联系管理员'
            )
        
        return Course.get_by_id(course_id)
    
    @staticmethod
    def get_course_statistics() -> dict:
        """获取课程统计"""
        return Course.get_statistics()
    
    @staticmethod
    def search_courses(keyword: str, page: int = 1, limit: int = 20) -> List[Course]:
        """搜索课程"""
        try:
            from app.utils.db import db_manager
            rows = db_manager.fetch_all("""
                SELECT * FROM courses 
                WHERE (title LIKE ? OR description LIKE ?) AND status = 'published'
                ORDER BY created_at DESC LIMIT ? OFFSET ?
            """, (f"%{keyword}%", f"%{keyword}%", limit, (page - 1) * limit))
            return [Course._from_row(row) for row in rows]
        except Exception as e:
            logger.error(f"搜索课程失败: {str(e)}")
            return []
    
    @staticmethod
    def get_course_types() -> list:
        """获取课程类型列表"""
        return [
            {'value': CourseType.VIDEO, 'label': '视频课程'},
            {'value': CourseType.LIVE, 'label': '直播课程'},
            {'value': CourseType.INTERACTIVE, 'label': '互动课程'},
            {'value': CourseType.ASSESSMENT, 'label': '评估课程'},
            {'value': CourseType.PRACTICE, 'label': '练习课程'}
        ]
    
    @staticmethod
    def get_course_statuses() -> list:
        """获取课程状态列表"""
        return [
            {'value': CourseStatus.DRAFT, 'label': '草稿'},
            {'value': CourseStatus.PUBLISHED, 'label': '已发布'},
            {'value': CourseStatus.ARCHIVED, 'label': '已归档'}
        ]