"""作业API路由 - MTSCOS AI项目"""

from flask import Blueprint, request, session
from app.services.assignment_service import AssignmentService
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

assignment_api = Blueprint('assignment_api', __name__)


@assignment_api.route('/api/assignments', methods=['GET'])
def get_assignments():
    """获取作业列表"""
    status = request.args.get('status')
    course_id = request.args.get('course_id')
    subject = request.args.get('subject')
    grade = request.args.get('grade')
    page = int(request.args.get('page', 1))
    limit = int(request.args.get('limit', 20))
    
    assignments = AssignmentService.get_assignments(
        status=status, course_id=course_id, subject=subject,
        grade=grade, page=page, limit=limit
    )
    return success_response([a.to_dict() for a in assignments])


@assignment_api.route('/api/assignments/<int:assignment_id>', methods=['GET'])
def get_assignment(assignment_id):
    """获取作业详情"""
    assignment = AssignmentService.get_assignment(assignment_id)
    if assignment:
        return success_response(assignment.to_dict())
    return not_found('作业不存在')


@assignment_api.route('/api/assignments', methods=['POST'])
@require_login
def create_assignment():
    """创建作业"""
    try:
        data = request.json
        user_id = session.get('user_id')
        
        assignment = AssignmentService.create_assignment(
            user_id=user_id,
            title=data.get('title'),
            description=data.get('description'),
            assignment_type=data.get('assignment_type', 'homework'),
            course_id=data.get('course_id'),
            subject=data.get('subject'),
            grade=data.get('grade'),
            total_score=data.get('total_score', 100),
            due_date=data.get('due_date'),
            max_attempts=data.get('max_attempts', 1),
            allow_late_submission=data.get('allow_late_submission', False)
        )
        
        return created_response(assignment.to_dict(), '作业创建成功')
    
    except ValidationException as e:
        return bad_request(e.message, e.error_type, e.suggestion, e.details)
    except AuthorizationException as e:
        return forbidden(e.message, e.error_type, e.suggestion)
    except BusinessException as e:
        return bad_request(e.message, e.error_type, e.suggestion, e.details)
    except Exception as e:
        return server_error(str(e))


@assignment_api.route('/api/assignments/<int:assignment_id>', methods=['PUT'])
@require_login
def update_assignment(assignment_id):
    """更新作业"""
    try:
        data = request.json
        user_id = session.get('user_id')
        
        assignment = AssignmentService.update_assignment(assignment_id, user_id, **data)
        return success_response(assignment.to_dict(), '作业更新成功')
    
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


@assignment_api.route('/api/assignments/<int:assignment_id>', methods=['DELETE'])
@require_login
def delete_assignment(assignment_id):
    """删除作业"""
    try:
        user_id = session.get('user_id')
        
        AssignmentService.delete_assignment(assignment_id, user_id)
        return success_response(message='作业删除成功')
    
    except ResourceNotFoundException as e:
        return not_found(e.message, e.error_type, e.suggestion)
    except AuthorizationException as e:
        return forbidden(e.message, e.error_type, e.suggestion)
    except BusinessException as e:
        return bad_request(e.message, e.error_type, e.suggestion, e.details)
    except Exception as e:
        return server_error(str(e))


@assignment_api.route('/api/assignments/<int:assignment_id>/publish', methods=['POST'])
@require_login
def publish_assignment(assignment_id):
    """发布作业"""
    try:
        user_id = session.get('user_id')
        
        assignment = AssignmentService.publish_assignment(assignment_id, user_id)
        return success_response(assignment.to_dict(), '作业发布成功')
    
    except ResourceNotFoundException as e:
        return not_found(e.message, e.error_type, e.suggestion)
    except AuthorizationException as e:
        return forbidden(e.message, e.error_type, e.suggestion)
    except BusinessException as e:
        return bad_request(e.message, e.error_type, e.suggestion, e.details)
    except Exception as e:
        return server_error(str(e))


@assignment_api.route('/api/assignments/<int:assignment_id>/close', methods=['POST'])
@require_login
def close_assignment(assignment_id):
    """关闭作业"""
    try:
        user_id = session.get('user_id')
        
        assignment = AssignmentService.close_assignment(assignment_id, user_id)
        return success_response(assignment.to_dict(), '作业关闭成功')
    
    except ResourceNotFoundException as e:
        return not_found(e.message, e.error_type, e.suggestion)
    except AuthorizationException as e:
        return forbidden(e.message, e.error_type, e.suggestion)
    except BusinessException as e:
        return bad_request(e.message, e.error_type, e.suggestion, e.details)
    except Exception as e:
        return server_error(str(e))


@assignment_api.route('/api/assignments/search', methods=['GET'])
def search_assignments():
    """搜索作业"""
    keyword = request.args.get('keyword', '')
    page = int(request.args.get('page', 1))
    limit = int(request.args.get('limit', 20))
    
    assignments = AssignmentService.search_assignments(keyword, page=page, limit=limit)
    return success_response([a.to_dict() for a in assignments])


@assignment_api.route('/api/assignments/statistics', methods=['GET'])
@require_admin
def get_assignment_statistics():
    """获取作业统计"""
    stats = AssignmentService.get_assignment_statistics()
    return success_response(stats)


@assignment_api.route('/api/assignments/types', methods=['GET'])
def get_assignment_types():
    """获取作业类型"""
    types = AssignmentService.get_assignment_types()
    return success_response(types)


@assignment_api.route('/api/assignments/statuses', methods=['GET'])
def get_assignment_statuses():
    """获取作业状态"""
    statuses = AssignmentService.get_assignment_statuses()
    return success_response(statuses)