"""学习路径API路由 - MTSCOS AI项目"""

from flask import Blueprint, request, session
from app.services.learning_path_service import LearningPathService
from app.utils.api_response import APIResponse
from app.utils.permission import require_login

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
    data = request.json
    user_id = session.get('user_id')
    name = data.get('name')
    description = data.get('description')
    
    if not name:
        return APIResponse.validation_error("路径名称不能为空")
    
    path = LearningPathService.create_path(user_id, name, description)
    return APIResponse.success(path.to_dict(), message="学习路径创建成功")


@learning_path_api.route('/api/learning_paths/<int:path_id>/nodes', methods=['POST'])
@require_login
def add_node(path_id):
    """添加路径节点"""
    data = request.json
    title = data.get('title')
    order = data.get('order', 0)
    description = data.get('description')
    node_type = data.get('type', 'lesson')
    content_url = data.get('content_url')
    estimated_time = data.get('estimated_time')
    
    if not title:
        return APIResponse.validation_error("节点标题不能为空")
    
    node = LearningPathService.add_node(
        path_id=path_id,
        title=title,
        order=order,
        description=description,
        node_type=node_type,
        content_url=content_url,
        estimated_time=estimated_time
    )
    
    return APIResponse.success(node.to_dict(), message="节点添加成功")


@learning_path_api.route('/api/learning_paths/nodes/<int:node_id>/complete', methods=['PUT'])
@require_login
def mark_node_completed(node_id):
    """标记节点完成"""
    node = LearningPathService.mark_node_completed(node_id)
    
    if not node:
        return APIResponse.not_found("节点不存在")
    
    return APIResponse.success(node.to_dict(), message="节点标记完成")


@learning_path_api.route('/api/learning_paths/recommendation', methods=['GET'])
@require_login
def get_recommendation():
    """获取学习推荐"""
    user_id = session.get('user_id')
    subject = request.args.get('subject')
    
    recommendation = LearningPathService.generate_recommendation(user_id, subject)
    return APIResponse.success(recommendation)