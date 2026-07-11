"""学习路径API路由 - MTSCOS AI项目"""

from flask import Blueprint, request, session
from app.services.learning_path_service import LearningPathService
from app.utils.api_response import APIResponse
from app.utils.permission import require_login
from app.exceptions import (
    ValidationException,
    ResourceNotFoundException,
    AuthorizationException,
    BusinessException
)

learning_path_api = Blueprint('learning_path_api', __name__)


@learning_path_api.route('/api/learning_paths', methods=['GET'])
@require_login
def get_user_paths():
    """获取用户学习路径列表"""
    user_id = session.get('user_id')
    status = request.args.get('status')
    
    paths = LearningPathService.get_user_paths(user_id, status)
    result = []
    for path in paths:
        progress = LearningPathService.calculate_progress(path.id)
        path_dict = path.to_dict()
        path_dict['progress'] = round(progress, 2)
        result.append(path_dict)
    
    return APIResponse.success(result)


@learning_path_api.route('/api/learning_paths/<int:path_id>', methods=['GET'])
@require_login
def get_path_detail(path_id):
    """获取学习路径详情"""
    user_id = session.get('user_id')
    path = LearningPathService.get_path(path_id, user_id)
    
    if not path:
        return APIResponse.not_found("学习路径不存在")
    
    nodes = LearningPathService.get_path_nodes(path_id)
    progress = LearningPathService.calculate_progress(path_id)
    
    result = path.to_dict()
    result['nodes'] = [node.to_dict() for node in nodes]
    result['progress'] = round(progress, 2)
    
    return APIResponse.success(result)


@learning_path_api.route('/api/learning_paths', methods=['POST'])
@require_login
def create_path():
    """创建学习路径"""
    try:
        data = request.json
        user_id = session.get('user_id')
        
        path = LearningPathService.create_path(user_id, data.get('name'), data.get('description'))
        return APIResponse.success(path.to_dict(), message="学习路径创建成功")
    
    except ValidationException as e:
        return APIResponse.validation_error(e.message, details=e.details)
    except BusinessException as e:
        return APIResponse.error(e.message, error_type=e.error_type, suggestion=e.suggestion)
    except Exception as e:
        return APIResponse.server_error(str(e))


@learning_path_api.route('/api/learning_paths/<int:path_id>/nodes', methods=['POST'])
@require_login
def add_node(path_id):
    """添加路径节点"""
    try:
        data = request.json
        
        node = LearningPathService.add_node(
            path_id=path_id,
            title=data.get('title'),
            order=data.get('order', 0),
            description=data.get('description'),
            node_type=data.get('type', 'lesson'),
            content_url=data.get('content_url'),
            estimated_time=data.get('estimated_time')
        )
        
        return APIResponse.success(node.to_dict(), message="节点添加成功")
    
    except ValidationException as e:
        return APIResponse.validation_error(e.message, details=e.details)
    except ResourceNotFoundException as e:
        return APIResponse.not_found(e.message)
    except BusinessException as e:
        return APIResponse.error(e.message, error_type=e.error_type, suggestion=e.suggestion)
    except Exception as e:
        return APIResponse.server_error(str(e))


@learning_path_api.route('/api/learning_paths/nodes/<int:node_id>/complete', methods=['PUT'])
@require_login
def mark_node_completed(node_id):
    """标记节点完成"""
    try:
        node = LearningPathService.mark_node_completed(node_id)
        return APIResponse.success(node.to_dict(), message="节点标记完成")
    
    except ResourceNotFoundException as e:
        return APIResponse.not_found(e.message)
    except BusinessException as e:
        return APIResponse.error(e.message, error_type=e.error_type, suggestion=e.suggestion)
    except Exception as e:
        return APIResponse.server_error(str(e))


@learning_path_api.route('/api/learning_paths/recommendation', methods=['GET'])
@require_login
def get_recommendation():
    """获取学习推荐"""
    try:
        user_id = session.get('user_id')
        subject = request.args.get('subject')
        
        recommendation = LearningPathService.generate_recommendation(user_id, subject)
        return APIResponse.success(recommendation)
    
    except Exception as e:
        return APIResponse.server_error(str(e))


@learning_path_api.route('/api/learning_paths/<int:path_id>/pause', methods=['POST'])
@require_login
def pause_path(path_id):
    """暂停学习路径"""
    try:
        user_id = session.get('user_id')
        
        path = LearningPathService.pause_path(path_id, user_id)
        return APIResponse.success(path.to_dict(), message="学习路径已暂停")
    
    except ResourceNotFoundException as e:
        return APIResponse.not_found(e.message)
    except AuthorizationException as e:
        return APIResponse.forbidden(e.message)
    except BusinessException as e:
        return APIResponse.error(e.message, error_type=e.error_type, suggestion=e.suggestion)
    except Exception as e:
        return APIResponse.server_error(str(e))


@learning_path_api.route('/api/learning_paths/<int:path_id>/resume', methods=['POST'])
@require_login
def resume_path(path_id):
    """恢复学习路径"""
    try:
        user_id = session.get('user_id')
        
        path = LearningPathService.resume_path(path_id, user_id)
        return APIResponse.success(path.to_dict(), message="学习路径已恢复")
    
    except ResourceNotFoundException as e:
        return APIResponse.not_found(e.message)
    except AuthorizationException as e:
        return APIResponse.forbidden(e.message)
    except BusinessException as e:
        return APIResponse.error(e.message, error_type=e.error_type, suggestion=e.suggestion)
    except Exception as e:
        return APIResponse.server_error(str(e))


@learning_path_api.route('/api/learning_paths/<int:path_id>', methods=['DELETE'])
@require_login
def delete_path(path_id):
    """删除学习路径"""
    try:
        user_id = session.get('user_id')
        
        LearningPathService.delete_path(path_id, user_id)
        return APIResponse.success(message="学习路径已删除")
    
    except ResourceNotFoundException as e:
        return APIResponse.not_found(e.message)
    except AuthorizationException as e:
        return APIResponse.forbidden(e.message)
    except BusinessException as e:
        return APIResponse.error(e.message, error_type=e.error_type, suggestion=e.suggestion)
    except Exception as e:
        return APIResponse.server_error(str(e))


@learning_path_api.route('/api/learning_paths/statistics', methods=['GET'])
@require_login
def get_learning_statistics():
    """获取学习统计"""
    try:
        user_id = session.get('user_id')
        
        stats = LearningPathService.get_learning_statistics(user_id)
        return APIResponse.success(stats)
    
    except Exception as e:
        return APIResponse.server_error(str(e))


@learning_path_api.route('/api/learning_paths/trend', methods=['GET'])
@require_login
def get_learning_trend():
    """获取学习趋势"""
    try:
        user_id = session.get('user_id')
        days = int(request.args.get('days', 7))
        
        trend = LearningPathService.get_learning_trend(user_id, days)
        return APIResponse.success(trend)
    
    except ValidationException as e:
        return APIResponse.validation_error(e.message, details=e.details)
    except Exception as e:
        return APIResponse.server_error(str(e))


@learning_path_api.route('/api/learning_paths/<int:path_id>/next_node', methods=['GET'])
@require_login
def get_next_node(path_id):
    """获取下一个待完成节点"""
    try:
        user_id = session.get('user_id')
        
        LearningPathService.get_path(path_id, user_id)
        node = LearningPathService.get_next_node(path_id)
        
        if node:
            return APIResponse.success(node.to_dict())
        else:
            return APIResponse.success(None, message="学习路径已全部完成")
    
    except ResourceNotFoundException as e:
        return APIResponse.not_found(e.message)
    except AuthorizationException as e:
        return APIResponse.forbidden(e.message)
    except Exception as e:
        return APIResponse.server_error(str(e))