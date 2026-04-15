# MTSCOS AI Project 文件系统 API
"""
文件系统API，提供RESTful接口用于文件系统操作
"""

from flask import Blueprint, request, jsonify
from app.filesystem import file_system

# 创建文件系统API蓝图
filesystem_bp = Blueprint('filesystem', __name__, url_prefix='/api/filesystem')


@filesystem_bp.route('/files', methods=['POST'])
def create_file():
    """
    创建文件
    
    Request Body:
    {
        "path": "文件路径",
        "content": "文件内容",
        "overwrite": false
    }
    
    Response:
    {
        "success": true,
        "message": "文件创建成功",
        "data": {
            "path": "文件路径"
        }
    }
    """
    try:
        data = request.get_json()
        path = data.get('path')
        content = data.get('content')
        overwrite = data.get('overwrite', False)
        
        if not path:
            return jsonify({
                'success': False,
                'message': '路径不能为空'
            }), 400
        
        result = file_system.create_file(path, content, overwrite)
        
        if result:
            return jsonify({
                'success': True,
                'message': '文件创建成功',
                'data': {
                    'path': path
                }
            }), 201
        else:
            return jsonify({
                'success': False,
                'message': '文件创建失败'
            }), 400
    except Exception as e:
        logger.error(f"创建文件API失败: {str(e)}")
        return jsonify({
            'success': False,
            'message': f'服务器错误: {str(e)}'
        }), 500


@filesystem_bp.route('/files/<path:path>', methods=['GET'])
def read_file(path):
    """
    读取文件
    
    Response:
    {
        "success": true,
        "message": "文件读取成功",
        "data": {
            "path": "文件路径",
            "content": "文件内容"
        }
    }
    """
    try:
        content = file_system.read_file(path)
        
        if content is not None:
            return jsonify({
                'success': True,
                'message': '文件读取成功',
                'data': {
                    'path': path,
                    'content': content
                }
            }), 200
        else:
            return jsonify({
                'success': False,
                'message': '文件不存在或读取失败'
            }), 404
    except Exception as e:
        logger.error(f"读取文件API失败: {str(e)}")
        return jsonify({
            'success': False,
            'message': f'服务器错误: {str(e)}'
        }), 500


@filesystem_bp.route('/files/<path:path>', methods=['PUT'])
def update_file(path):
    """
    更新文件
    
    Request Body:
    {
        "content": "文件内容"
    }
    
    Response:
    {
        "success": true,
        "message": "文件更新成功",
        "data": {
            "path": "文件路径"
        }
    }
    """
    try:
        data = request.get_json()
        content = data.get('content')
        
        result = file_system.update_file(path, content)
        
        if result:
            return jsonify({
                'success': True,
                'message': '文件更新成功',
                'data': {
                    'path': path
                }
            }), 200
        else:
            return jsonify({
                'success': False,
                'message': '文件更新失败'
            }), 400
    except Exception as e:
        logger.error(f"更新文件API失败: {str(e)}")
        return jsonify({
            'success': False,
            'message': f'服务器错误: {str(e)}'
        }), 500


@filesystem_bp.route('/files/<path:path>', methods=['DELETE'])
def delete_file(path):
    """
    删除文件
    
    Response:
    {
        "success": true,
        "message": "文件删除成功"
    }
    """
    try:
        result = file_system.delete_file(path)
        
        if result:
            return jsonify({
                'success': True,
                'message': '文件删除成功'
            }), 200
        else:
            return jsonify({
                'success': False,
                'message': '文件删除失败'
            }), 400
    except Exception as e:
        logger.error(f"删除文件API失败: {str(e)}")
        return jsonify({
            'success': False,
            'message': f'服务器错误: {str(e)}'
        }), 500


@filesystem_bp.route('/files/<path:path>/info', methods=['GET'])
def get_file_info(path):
    """
    获取文件信息
    
    Response:
    {
        "success": true,
        "message": "文件信息获取成功",
        "data": {
            "path": "文件路径",
            "type": "file",
            "size": 1024,
            "created_at": 1234567890,
            "modified_at": 1234567890,
            "extension": ".txt"
        }
    }
    """
    try:
        info = file_system.get_file_info(path)
        
        if info.get('exists'):
            return jsonify({
                'success': True,
                'message': '文件信息获取成功',
                'data': info
            }), 200
        else:
            return jsonify({
                'success': False,
                'message': '文件不存在'
            }), 404
    except Exception as e:
        logger.error(f"获取文件信息API失败: {str(e)}")
        return jsonify({
            'success': False,
            'message': f'服务器错误: {str(e)}'
        }), 500


@filesystem_bp.route('/directories', methods=['POST'])
def create_directory():
    """
    创建目录
    
    Request Body:
    {
        "path": "目录路径"
    }
    
    Response:
    {
        "success": true,
        "message": "目录创建成功",
        "data": {
            "path": "目录路径"
        }
    }
    """
    try:
        data = request.get_json()
        path = data.get('path')
        
        if not path:
            return jsonify({
                'success': False,
                'message': '路径不能为空'
            }), 400
        
        result = file_system.create_directory(path)
        
        if result:
            return jsonify({
                'success': True,
                'message': '目录创建成功',
                'data': {
                    'path': path
                }
            }), 201
        else:
            return jsonify({
                'success': False,
                'message': '目录创建失败'
            }), 400
    except Exception as e:
        logger.error(f"创建目录API失败: {str(e)}")
        return jsonify({
            'success': False,
            'message': f'服务器错误: {str(e)}'
        }), 500


@filesystem_bp.route('/directories/<path:path>', methods=['GET'])
def list_directory(path):
    """
    列出目录内容
    
    Response:
    {
        "success": true,
        "message": "目录内容获取成功",
        "data": {
            "path": "目录路径",
            "contents": [
                {
                    "name": "文件或目录名",
                    "type": "file"或"directory",
                    "size": 1024,
                    "modified_at": 1234567890
                }
            ]
        }
    }
    """
    try:
        contents = file_system.list_directory(path)
        
        return jsonify({
            'success': True,
            'message': '目录内容获取成功',
            'data': {
                'path': path,
                'contents': contents
            }
        }), 200
    except Exception as e:
        logger.error(f"列出目录API失败: {str(e)}")
        return jsonify({
            'success': False,
            'message': f'服务器错误: {str(e)}'
        }), 500


@filesystem_bp.route('/directories/<path:path>', methods=['DELETE'])
def delete_directory(path):
    """
    删除目录
    
    Query Parameters:
    - recursive: 是否递归删除，默认为false
    
    Response:
    {
        "success": true,
        "message": "目录删除成功"
    }
    """
    try:
        recursive = request.args.get('recursive', 'false').lower() == 'true'
        result = file_system.delete_directory(path, recursive)
        
        if result:
            return jsonify({
                'success': True,
                'message': '目录删除成功'
            }), 200
        else:
            return jsonify({
                'success': False,
                'message': '目录删除失败'
            }), 400
    except Exception as e:
        logger.error(f"删除目录API失败: {str(e)}")
        return jsonify({
            'success': False,
            'message': f'服务器错误: {str(e)}'
        }), 500


@filesystem_bp.route('/directories/<path:path>/info', methods=['GET'])
def get_directory_info(path):
    """
    获取目录信息
    
    Response:
    {
        "success": true,
        "message": "目录信息获取成功",
        "data": {
            "path": "目录路径",
            "type": "directory",
            "size": 1024,
            "created_at": 1234567890,
            "modified_at": 1234567890,
            "contents": {
                "file_count": 10,
                "directory_count": 5,
                "total_size": 10240
            }
        }
    }
    """
    try:
        info = file_system.get_directory_info(path)
        
        if info.get('exists'):
            return jsonify({
                'success': True,
                'message': '目录信息获取成功',
                'data': info
            }), 200
        else:
            return jsonify({
                'success': False,
                'message': '目录不存在'
            }), 404
    except Exception as e:
        logger.error(f"获取目录信息API失败: {str(e)}")
        return jsonify({
            'success': False,
            'message': f'服务器错误: {str(e)}'
        }), 500


@filesystem_bp.route('/paths/<path:path>', methods=['GET'])
def check_path(path):
    """
    检查路径是否存在
    
    Response:
    {
        "success": true,
        "message": "路径检查成功",
        "data": {
            "path": "路径",
            "exists": true,
            "type": "file"或"directory"或"not_exists"
        }
    }
    """
    try:
        exists = file_system.exists(path)
        path_type = file_system.get_path_type(path)
        
        return jsonify({
            'success': True,
            'message': '路径检查成功',
            'data': {
                'path': path,
                'exists': exists,
                'type': path_type
            }
        }), 200
    except Exception as e:
        logger.error(f"检查路径API失败: {str(e)}")
        return jsonify({
            'success': False,
            'message': f'服务器错误: {str(e)}'
        }), 500


@filesystem_bp.route('/paths/<path:path>/full', methods=['GET'])
def get_full_path(path):
    """
    获取完整路径
    
    Response:
    {
        "success": true,
        "message": "完整路径获取成功",
        "data": {
            "path": "原始路径",
            "full_path": "完整路径"
        }
    }
    """
    try:
        full_path = file_system.get_full_path(path)
        
        return jsonify({
            'success': True,
            'message': '完整路径获取成功',
            'data': {
                'path': path,
                'full_path': full_path
            }
        }), 200
    except Exception as e:
        logger.error(f"获取完整路径API失败: {str(e)}")
        return jsonify({
            'success': False,
            'message': f'服务器错误: {str(e)}'
        }), 500


@filesystem_bp.route('/copy', methods=['POST'])
def copy_path():
    """
    复制文件或目录
    
    Request Body:
    {
        "src_path": "源路径",
        "dest_path": "目标路径",
        "overwrite": false
    }
    
    Response:
    {
        "success": true,
        "message": "复制成功",
        "data": {
            "src_path": "源路径",
            "dest_path": "目标路径"
        }
    }
    """
    try:
        data = request.get_json()
        src_path = data.get('src_path')
        dest_path = data.get('dest_path')
        overwrite = data.get('overwrite', False)
        
        if not src_path or not dest_path:
            return jsonify({
                'success': False,
                'message': '源路径和目标路径不能为空'
            }), 400
        
        # 检查源路径类型，调用相应的复制方法
        src_type = file_system.get_path_type(src_path)
        if src_type == 'file':
            result = file_system.get_file_manager().copy_file(src_path, dest_path, overwrite)
        elif src_type == 'directory':
            result = file_system.get_directory_manager().copy_directory(src_path, dest_path, overwrite)
        else:
            return jsonify({
                'success': False,
                'message': '源路径不存在或类型不支持'
            }), 400
        
        if result:
            return jsonify({
                'success': True,
                'message': '复制成功',
                'data': {
                    'src_path': src_path,
                    'dest_path': dest_path
                }
            }), 200
        else:
            return jsonify({
                'success': False,
                'message': '复制失败'
            }), 400
    except Exception as e:
        logger.error(f"复制API失败: {str(e)}")
        return jsonify({
            'success': False,
            'message': f'服务器错误: {str(e)}'
        }), 500


@filesystem_bp.route('/move', methods=['POST'])
def move_path():
    """
    移动文件或目录
    
    Request Body:
    {
        "src_path": "源路径",
        "dest_path": "目标路径",
        "overwrite": false
    }
    
    Response:
    {
        "success": true,
        "message": "移动成功",
        "data": {
            "src_path": "源路径",
            "dest_path": "目标路径"
        }
    }
    """
    try:
        data = request.get_json()
        src_path = data.get('src_path')
        dest_path = data.get('dest_path')
        overwrite = data.get('overwrite', False)
        
        if not src_path or not dest_path:
            return jsonify({
                'success': False,
                'message': '源路径和目标路径不能为空'
            }), 400
        
        # 检查源路径类型，调用相应的移动方法
        src_type = file_system.get_path_type(src_path)
        if src_type == 'file':
            result = file_system.get_file_manager().move_file(src_path, dest_path, overwrite)
        elif src_type == 'directory':
            result = file_system.get_directory_manager().move_directory(src_path, dest_path, overwrite)
        else:
            return jsonify({
                'success': False,
                'message': '源路径不存在或类型不支持'
            }), 400
        
        if result:
            return jsonify({
                'success': True,
                'message': '移动成功',
                'data': {
                    'src_path': src_path,
                    'dest_path': dest_path
                }
            }), 200
        else:
            return jsonify({
                'success': False,
                'message': '移动失败'
            }), 400
    except Exception as e:
        logger.error(f"移动API失败: {str(e)}")
        return jsonify({
            'success': False,
            'message': f'服务器错误: {str(e)}'
        }), 500


@filesystem_bp.route('/storage/usage', methods=['GET'])
def get_storage_usage():
    """
    获取存储使用情况
    
    Response:
    {
        "success": true,
        "message": "存储使用情况获取成功",
        "data": {
            "total": 1073741824,
            "used": 536870912,
            "free": 536870912,
            "available": 536870912,
            "usage_percentage": 50
        }
    }
    """
    try:
        usage = file_system.get_storage_manager().get_disk_usage()
        
        return jsonify({
            'success': True,
            'message': '存储使用情况获取成功',
            'data': usage
        }), 200
    except Exception as e:
        logger.error(f"获取存储使用情况API失败: {str(e)}")
        return jsonify({
            'success': False,
            'message': f'服务器错误: {str(e)}'
        }), 500


@filesystem_bp.route('/permissions', methods=['POST'])
def set_permission():
    """
    设置权限
    
    Request Body:
    {
        "path": "路径",
        "user_id": "用户ID",
        "permissions": {
            "read": true,
            "write": false,
            "execute": false,
            "admin": false
        }
    }
    
    Response:
    {
        "success": true,
        "message": "权限设置成功",
        "data": {
            "path": "路径",
            "user_id": "用户ID"
        }
    }
    """
    try:
        data = request.get_json()
        path = data.get('path')
        user_id = data.get('user_id')
        permissions = data.get('permissions', {})
        
        if not path or not user_id:
            return jsonify({
                'success': False,
                'message': '路径和用户ID不能为空'
            }), 400
        
        result = file_system.get_permission_manager().set_permission(path, user_id, permissions)
        
        if result:
            return jsonify({
                'success': True,
                'message': '权限设置成功',
                'data': {
                    'path': path,
                    'user_id': user_id
                }
            }), 200
        else:
            return jsonify({
                'success': False,
                'message': '权限设置失败'
            }), 400
    except Exception as e:
        logger.error(f"设置权限API失败: {str(e)}")
        return jsonify({
            'success': False,
            'message': f'服务器错误: {str(e)}'
        }), 500


@filesystem_bp.route('/permissions/<path:path>/<user_id>', methods=['GET'])
def get_permission(path, user_id):
    """
    获取权限
    
    Response:
    {
        "success": true,
        "message": "权限获取成功",
        "data": {
            "path": "路径",
            "user_id": "用户ID",
            "permissions": {
                "read": true,
                "write": false,
                "execute": false,
                "admin": false
            }
        }
    }
    """
    try:
        permissions = file_system.get_permission_manager().get_permission(path, user_id)
        
        return jsonify({
            'success': True,
            'message': '权限获取成功',
            'data': {
                'path': path,
                'user_id': user_id,
                'permissions': permissions
            }
        }), 200
    except Exception as e:
        logger.error(f"获取权限API失败: {str(e)}")
        return jsonify({
            'success': False,
            'message': f'服务器错误: {str(e)}'
        }), 500


@filesystem_bp.route('/permissions/<path:path>/<user_id>', methods=['DELETE'])
def remove_permission(path, user_id):
    """
    移除权限
    
    Response:
    {
        "success": true,
        "message": "权限移除成功",
        "data": {
            "path": "路径",
            "user_id": "用户ID"
        }
    }
    """
    try:
        result = file_system.get_permission_manager().remove_permission(path, user_id)
        
        if result:
            return jsonify({
                'success': True,
                'message': '权限移除成功',
                'data': {
                    'path': path,
                    'user_id': user_id
                }
            }), 200
        else:
            return jsonify({
                'success': False,
                'message': '权限移除失败'
            }), 400
    except Exception as e:
        logger.error(f"移除权限API失败: {str(e)}")
        return jsonify({
            'success': False,
            'message': f'服务器错误: {str(e)}'
        }), 500


@filesystem_bp.route('/search', methods=['GET'])
def search_files():
    """
    搜索文件
    
    Query Parameters:
    - directory: 搜索目录
    - pattern: 搜索模式（如*.txt）
    - recursive: 是否递归搜索，默认为false
    
    Response:
    {
        "success": true,
        "message": "搜索成功",
        "data": {
            "results": [
                {
                    "path": "文件路径",
                    "type": "file",
                    "size": 1024,
                    "modified_at": 1234567890
                }
            ]
        }
    }
    """
    try:
        directory = request.args.get('directory', '.')
        pattern = request.args.get('pattern', '*')
        recursive = request.args.get('recursive', 'false').lower() == 'true'
        
        results = file_system.get_directory_manager().find_in_directory(directory, pattern, recursive)
        
        return jsonify({
            'success': True,
            'message': '搜索成功',
            'data': {
                'results': results
            }
        }), 200
    except Exception as e:
        logger.error(f"搜索文件API失败: {str(e)}")
        return jsonify({
            'success': False,
            'message': f'服务器错误: {str(e)}'
        }), 500


# 缓存管理API
@filesystem_bp.route('/cache/system/upgrades', methods=['POST'])
def set_system_upgrade_cache_api():
    """
    设置系统升级包缓存
    
    Request Body:
    {
        "version": "1.0.0",
        "upgrade_data": {
            "files": ["file1.txt", "file2.txt"],
            "size": 1024
        },
        "expiry": 3600
    }
    
    Response:
    {
        "success": true,
        "message": "系统升级包缓存设置成功"
    }
    """
    try:
        data = request.get_json()
        version = data.get('version')
        upgrade_data = data.get('upgrade_data')
        expiry = data.get('expiry')
        
        if not version or not upgrade_data:
            return jsonify({
                'success': False,
                'message': '版本号和升级包数据不能为空'
            }), 400
        
        result = file_system.set_system_upgrade_cache(version, upgrade_data, expiry)
        
        if result:
            return jsonify({
                'success': True,
                'message': '系统升级包缓存设置成功'
            }), 200
        else:
            return jsonify({
                'success': False,
                'message': '系统升级包缓存设置失败'
            }), 400
    except Exception as e:
        logger.error(f"设置系统升级包缓存API失败: {str(e)}")
        return jsonify({
            'success': False,
            'message': f'服务器错误: {str(e)}'
        }), 500


@filesystem_bp.route('/cache/system/upgrades/<version>', methods=['GET'])
def get_system_upgrade_cache_api(version):
    """
    获取系统升级包缓存
    
    Response:
    {
        "success": true,
        "message": "系统升级包缓存获取成功",
        "data": {
            "version": "1.0.0",
            "upgrade_data": {
                "files": ["file1.txt", "file2.txt"],
                "size": 1024
            }
        }
    }
    """
    try:
        upgrade_data = file_system.get_system_upgrade_cache(version)
        
        if upgrade_data:
            return jsonify({
                'success': True,
                'message': '系统升级包缓存获取成功',
                'data': {
                    'version': version,
                    'upgrade_data': upgrade_data
                }
            }), 200
        else:
            return jsonify({
                'success': False,
                'message': '系统升级包缓存不存在或已过期'
            }), 404
    except Exception as e:
        logger.error(f"获取系统升级包缓存API失败: {str(e)}")
        return jsonify({
            'success': False,
            'message': f'服务器错误: {str(e)}'
        }), 500


@filesystem_bp.route('/cache/system/upgrades/<version>', methods=['DELETE'])
def delete_system_upgrade_cache_api(version):
    """
    删除系统升级包缓存
    
    Response:
    {
        "success": true,
        "message": "系统升级包缓存删除成功"
    }
    """
    try:
        result = file_system.delete_system_upgrade_cache(version)
        
        if result:
            return jsonify({
                'success': True,
                'message': '系统升级包缓存删除成功'
            }), 200
        else:
            return jsonify({
                'success': False,
                'message': '系统升级包缓存删除失败'
            }), 400
    except Exception as e:
        logger.error(f"删除系统升级包缓存API失败: {str(e)}")
        return jsonify({
            'success': False,
            'message': f'服务器错误: {str(e)}'
        }), 500


@filesystem_bp.route('/cache/system/upgrades', methods=['GET'])
def list_system_upgrade_caches_api():
    """
    列出所有系统升级包缓存
    
    Response:
    {
        "success": true,
        "message": "系统升级包缓存列表获取成功",
        "data": {
            "upgrades": [
                {
                    "version": "1.0.0",
                    "created_at": 1234567890,
                    "expiry": 604800,
                    "size": 1024
                }
            ]
        }
    }
    """
    try:
        upgrades = file_system.list_system_upgrade_caches()
        
        return jsonify({
            'success': True,
            'message': '系统升级包缓存列表获取成功',
            'data': {
                'upgrades': upgrades
            }
        }), 200
    except Exception as e:
        logger.error(f"列出系统升级包缓存API失败: {str(e)}")
        return jsonify({
            'success': False,
            'message': f'服务器错误: {str(e)}'
        }), 500


@filesystem_bp.route('/cache/users/<user_id>/files', methods=['POST'])
def set_user_file_cache_api(user_id):
    """
    设置用户文件缓存
    
    Request Body:
    {
        "file_id": "file_123",
        "file_data": {
            "name": "test.txt",
            "content": "test content",
            "size": 100
        },
        "expiry": 259200
    }
    
    Response:
    {
        "success": true,
        "message": "用户文件缓存设置成功"
    }
    """
    try:
        data = request.get_json()
        file_id = data.get('file_id')
        file_data = data.get('file_data')
        expiry = data.get('expiry')
        
        if not file_id or not file_data:
            return jsonify({
                'success': False,
                'message': '文件ID和文件数据不能为空'
            }), 400
        
        result = file_system.set_user_file_cache(user_id, file_id, file_data, expiry)
        
        if result:
            return jsonify({
                'success': True,
                'message': '用户文件缓存设置成功'
            }), 200
        else:
            return jsonify({
                'success': False,
                'message': '用户文件缓存设置失败'
            }), 400
    except Exception as e:
        logger.error(f"设置用户文件缓存API失败: {str(e)}")
        return jsonify({
            'success': False,
            'message': f'服务器错误: {str(e)}'
        }), 500


@filesystem_bp.route('/cache/users/<user_id>/files/<file_id>', methods=['GET'])
def get_user_file_cache_api(user_id, file_id):
    """
    获取用户文件缓存
    
    Response:
    {
        "success": true,
        "message": "用户文件缓存获取成功",
        "data": {
            "file_id": "file_123",
            "file_data": {
                "name": "test.txt",
                "content": "test content",
                "size": 100
            }
        }
    }
    """
    try:
        file_data = file_system.get_user_file_cache(user_id, file_id)
        
        if file_data:
            return jsonify({
                'success': True,
                'message': '用户文件缓存获取成功',
                'data': {
                    'file_id': file_id,
                    'file_data': file_data
                }
            }), 200
        else:
            return jsonify({
                'success': False,
                'message': '用户文件缓存不存在或已过期'
            }), 404
    except Exception as e:
        logger.error(f"获取用户文件缓存API失败: {str(e)}")
        return jsonify({
            'success': False,
            'message': f'服务器错误: {str(e)}'
        }), 500


@filesystem_bp.route('/cache/users/<user_id>/files/<file_id>', methods=['DELETE'])
def delete_user_file_cache_api(user_id, file_id):
    """
    删除用户文件缓存
    
    Response:
    {
        "success": true,
        "message": "用户文件缓存删除成功"
    }
    """
    try:
        result = file_system.delete_user_file_cache(user_id, file_id)
        
        if result:
            return jsonify({
                'success': True,
                'message': '用户文件缓存删除成功'
            }), 200
        else:
            return jsonify({
                'success': False,
                'message': '用户文件缓存删除失败'
            }), 400
    except Exception as e:
        logger.error(f"删除用户文件缓存API失败: {str(e)}")
        return jsonify({
            'success': False,
            'message': f'服务器错误: {str(e)}'
        }), 500


@filesystem_bp.route('/cache/users/<user_id>/files', methods=['GET'])
def list_user_file_caches_api(user_id):
    """
    列出用户文件缓存
    
    Response:
    {
        "success": true,
        "message": "用户文件缓存列表获取成功",
        "data": {
            "files": [
                {
                    "file_id": "file_123",
                    "created_at": 1234567890,
                    "expiry": 259200,
                    "size": 1024
                }
            ]
        }
    }
    """
    try:
        files = file_system.list_user_file_caches(user_id)
        
        return jsonify({
            'success': True,
            'message': '用户文件缓存列表获取成功',
            'data': {
                'files': files
            }
        }), 200
    except Exception as e:
        logger.error(f"列出用户文件缓存API失败: {str(e)}")
        return jsonify({
            'success': False,
            'message': f'服务器错误: {str(e)}'
        }), 500


@filesystem_bp.route('/cache/stats', methods=['GET'])
def get_cache_stats_api():
    """
    获取缓存统计信息
    
    Response:
    {
        "success": true,
        "message": "缓存统计信息获取成功",
        "data": {
            "system_cache": {
                "file_count": 10,
                "total_size": 1024000
            },
            "user_cache": {
                "file_count": 50,
                "total_size": 5120000,
                "user_count": 5
            },
            "total_cache_size": 6144000
        }
    }
    """
    try:
        stats = file_system.get_cache_stats()
        
        return jsonify({
            'success': True,
            'message': '缓存统计信息获取成功',
            'data': stats
        }), 200
    except Exception as e:
        logger.error(f"获取缓存统计信息API失败: {str(e)}")
        return jsonify({
            'success': False,
            'message': f'服务器错误: {str(e)}'
        }), 500


@filesystem_bp.route('/cache/<cache_type>', methods=['DELETE'])
def clear_cache_api(cache_type):
    """
    清空缓存
    
    Args:
        cache_type: 缓存类型，'system' 或 'user'
    
    Response:
    {
        "success": true,
        "message": "缓存清空成功"
    }
    """
    try:
        if cache_type not in ['system', 'user']:
            return jsonify({
                'success': False,
                'message': '无效的缓存类型，只能是system或user'
            }), 400
        
        result = file_system.clear_cache(cache_type)
        
        if result:
            return jsonify({
                'success': True,
                'message': f'{cache_type}缓存清空成功'
            }), 200
        else:
            return jsonify({
                'success': False,
                'message': f'{cache_type}缓存清空失败'
            }), 400
    except Exception as e:
        logger.error(f"清空缓存API失败: {str(e)}")
        return jsonify({
            'success': False,
            'message': f'服务器错误: {str(e)}'
        }), 500


@filesystem_bp.route('/cache/users/<user_id>', methods=['DELETE'])
def clear_user_cache_api(user_id):
    """
    清空特定用户的缓存
    
    Response:
    {
        "success": true,
        "message": "用户缓存清空成功"
    }
    """
    try:
        result = file_system.clear_cache('user', user_id)
        
        if result:
            return jsonify({
                'success': True,
                'message': f'用户 {user_id} 缓存清空成功'
            }), 200
        else:
            return jsonify({
                'success': False,
                'message': f'用户 {user_id} 缓存清空失败'
            }), 400
    except Exception as e:
        logger.error(f"清空用户缓存API失败: {str(e)}")
        return jsonify({
            'success': False,
            'message': f'服务器错误: {str(e)}'
        }), 500