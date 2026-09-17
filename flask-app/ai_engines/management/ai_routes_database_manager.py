# routes/readonly_inventory_routes.py
"""
只读库存信息 API
"""

from flask import Blueprint, jsonify, request, abort
from system_container import system_container
from utils.auth import _get_current_user, _check_permission

bp = Blueprint('readonly_inventory', __name__)

@bp.route('/api/readonly_inventory', methods=['GET'])
@system_container(require_auth='login', allowed_roles=['admin', 'super_admin', 'teacher', 'student'])
def get_readonly_inventory():
    """
    获取只读库存列表
    需要 view_readonly_inventory 权限
    """
    user = _get_current_user(request)
    if not _check_permission(user, 'view_readonly_inventory'):
        abort(403, description='无权访问库存信息')

    # 这里示例返回空列表，实际可根据业务需求从数据库读取
    inventory_list = []

    return jsonify({
        'code': 0,
        'message': '成功',
        'data': inventory_list,
        'timestamp': int(time.time())
    })
