"""课程API路由 - MTSCOS AI项目"""

from flask import Blueprint, request, session
from app.services.course_service import CourseService
from app.utils.permission import require_login, require_admin
from app.utils.response import (
    success_response, created_response, bad_request, 
    forbidden, not_found, server_error
)
from app.exceptions import (
    ValidationException,
    ResourceNotFoundException,
    AuthorizationException,
    BusinessException
)

course_api = Blueprint('course_api', __name__)


@course_api.route('/api/courses', methods=['GET'])
def get_courses():
    """获取课程列表"""
    status = request.args.get('status')
    subject = request.args.get('subject')
    grade = request.args.get('grade')
    page = int(request.args.get('page', 1))
    limit = int(request.args.get('limit', 20))
    
    courses = CourseService.get_courses(status=status, subject=subject, 
                                        grade=grade, page=page, limit=limit)
    return success_response([c.to_dict() for c in courses])


@course_api.route('/api/courses/<int:course_id>', methods=['GET'])
def get_course(course_id):
    """获取课程详情"""
    course = CourseService.get_course(course_id)
    if course:
        return success_response(course.to_dict())
    return not_found('课程不存在')


@course_api.route('/api/courses', methods=['POST'])
@require_login
def create_course():
    """创建课程"""
    try:
        data = request.json
        user_id = session.get('user_id')
        
        course = CourseService.create_course(
            user_id=user_id,
            title=data.get('title'),
            description=data.get('description'),
            course_type=data.get('course_type', 'video'),
            subject=data.get('subject'),
            grade=data.get('grade'),
            duration=data.get('duration', 0),
            cover_image=data.get('cover_image')
        )
        
        return created_response(course.to_dict(), '课程创建成功')
    
    except ValidationException as e:
        return bad_request(e.message, e.error_type, e.suggestion, e.details)
    except AuthorizationException as e:
        return forbidden(e.message, e.error_type, e.suggestion)
    except BusinessException as e:
        return bad_request(e.message, e.error_type, e.suggestion, e.details)
    except Exception as e:
        return server_error(str(e))


@course_api.route('/api/courses/<int:course_id>', methods=['PUT'])
@require_login
def update_course(course_id):
    """更新课程"""
    try:
        data = request.json
        user_id = session.get('user_id')
        
        course = CourseService.update_course(course_id, user_id, **data)
        return success_response(course.to_dict(), '课程更新成功')
    
    except ValidationException as e:
        return bad_request(e.message, e.error_type, e.suggestion, e.details)
    except ResourceNotFoundException as e:
        return not_found(e.message, e.error_type, e.suggestion)
    except AuthorizationException as e:
        return forbidden(e.message, e.error_type, e.suggestion)
    except BusinessException as e:
        return bad_request(e.message, e.error_type, e.suggestion, e.details)
    except Exception as e:
        return server_error(str(e))


@course_api.route('/api/courses/<int:course_id>', methods=['DELETE'])
@require_login
def delete_course(course_id):
    """删除课程"""
    try:
        user_id = session.get('user_id')
        
        CourseService.delete_course(course_id, user_id)
        return success_response(message='课程删除成功')
    
    except ResourceNotFoundException as e:
        return not_found(e.message, e.error_type, e.suggestion)
    except AuthorizationException as e:
        return forbidden(e.message, e.error_type, e.suggestion)
    except BusinessException as e:
        return bad_request(e.message, e.error_type, e.suggestion, e.details)
    except Exception as e:
        return server_error(str(e))


@course_api.route('/api/courses/<int:course_id>/publish', methods=['POST'])
@require_login
def publish_course(course_id):
    """发布课程"""
    try:
        user_id = session.get('user_id')
        
        course = CourseService.publish_course(course_id, user_id)
        return success_response(course.to_dict(), '课程发布成功')
    
    except ResourceNotFoundException as e:
        return not_found(e.message, e.error_type, e.suggestion)
    except AuthorizationException as e:
        return forbidden(e.message, e.error_type, e.suggestion)
    except BusinessException as e:
        return bad_request(e.message, e.error_type, e.suggestion, e.details)
    except Exception as e:
        return server_error(str(e))


@course_api.route('/api/courses/<int:course_id>/archive', methods=['POST'])
@require_login
def archive_course(course_id):
    """归档课程"""
    try:
        user_id = session.get('user_id')
        
        course = CourseService.archive_course(course_id, user_id)
        return success_response(course.to_dict(), '课程归档成功')
    
    except ResourceNotFoundException as e:
        return not_found(e.message, e.error_type, e.suggestion)
    except AuthorizationException as e:
        return forbidden(e.message, e.error_type, e.suggestion)
    except BusinessException as e:
        return bad_request(e.message, e.error_type, e.suggestion, e.details)
    except Exception as e:
        return server_error(str(e))


@course_api.route('/api/courses/search', methods=['GET'])
def search_courses():
    """搜索课程"""
    keyword = request.args.get('keyword', '')
    page = int(request.args.get('page', 1))
    limit = int(request.args.get('limit', 20))
    
    courses = CourseService.search_courses(keyword, page=page, limit=limit)
    return success_response([c.to_dict() for c in courses])


@course_api.route('/api/courses/statistics', methods=['GET'])
@require_admin
def get_course_statistics():
    """获取课程统计"""
    stats = CourseService.get_course_statistics()
    return success_response(stats)


@course_api.route('/api/courses/types', methods=['GET'])
def get_course_types():
    """获取课程类型"""
    types = CourseService.get_course_types()
    return success_response(types)


@course_api.route('/api/courses/statuses', methods=['GET'])
def get_course_statuses():
    """获取课程状态"""
    statuses = CourseService.get_course_statuses()
    return success_response(statuses)