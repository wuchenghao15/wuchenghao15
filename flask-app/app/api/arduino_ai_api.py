# -*- coding: utf-8 -*-
"""
Arduino AI增强API
提供AI代码生成、项目管理、教程系统等接口
"""

from flask import Blueprint, request, jsonify, session
from app.services.arduino_ai_enhanced_service import arduino_ai_enhanced_service
from app.services.arduino_service import ArduinoService
import logging

logger = logging.getLogger(__name__)

arduino_ai_api = Blueprint('arduino_ai_api', __name__)

arduino_service = ArduinoService()


def get_current_user():
    """获取当前用户"""
    user_id = session.get('user_id')
    if not user_id:
        user_id = session.get('admin_user_id')
    return user_id


@arduino_ai_api.route('/api/arduino/ai/generate', methods=['POST'])
def generate_code():
    """
    AI生成Arduino代码
    
    Request Body:
        description: 功能描述
        board: 板型（默认uno）
        feature: 功能类型
        language: 编程语言
    """
    try:
        data = request.get_json()
        description = data.get('description', '')
        board = data.get('board', 'uno')
        feature = data.get('feature', '自定义功能')
        language = data.get('language', 'C++')
        
        if not description:
            return jsonify({'success': False, 'error': '功能描述不能为空'}), 400
        
        result = arduino_ai_enhanced_service.generate_code(
            description=description,
            board=board,
            feature=feature,
            language=language
        )
        
        return jsonify(result)
    except Exception as e:
        logger.error(f"生成代码失败: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@arduino_ai_api.route('/api/arduino/ai/explain', methods=['POST'])
def explain_code():
    """
    解释Arduino代码
    
    Request Body:
        code: 代码内容
    """
    try:
        data = request.get_json()
        code = data.get('code', '')
        
        if not code:
            return jsonify({'success': False, 'error': '代码不能为空'}), 400
        
        result = arduino_ai_enhanced_service.explain_code(code)
        
        return jsonify(result)
    except Exception as e:
        logger.error(f"解释代码失败: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@arduino_ai_api.route('/api/arduino/compile', methods=['POST'])
def compile_code():
    """
    编译Arduino代码
    
    Request Body:
        code: 代码内容
        board: 板型（默认uno）
    """
    try:
        data = request.get_json()
        code = data.get('code', '')
        board = data.get('board', 'uno')
        
        if not code:
            return jsonify({'success': False, 'error': '代码不能为空'}), 400
        
        result = arduino_service.compile_code(code, board)
        
        return jsonify(result)
    except Exception as e:
        logger.error(f"编译失败: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@arduino_ai_api.route('/api/arduino/upload', methods=['POST'])
def upload_code():
    """
    上传代码到Arduino
    
    Request Body:
        code: 代码内容
        board: 板型
        port: 串口号
    """
    try:
        data = request.get_json()
        code = data.get('code', '')
        board = data.get('board', 'uno')
        port = data.get('port', '')
        
        if not code:
            return jsonify({'success': False, 'error': '代码不能为空'}), 400
        
        result = arduino_service.upload_code(code, board, port)
        
        return jsonify(result)
    except Exception as e:
        logger.error(f"上传失败: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@arduino_ai_api.route('/api/arduino/verify', methods=['POST'])
def verify_code():
    """
    验证代码语法
    
    Request Body:
        code: 代码内容
    """
    try:
        data = request.get_json()
        code = data.get('code', '')
        
        if not code:
            return jsonify({'success': False, 'error': '代码不能为空'}), 400
        
        result = arduino_service.verify_code(code)
        
        return jsonify(result)
    except Exception as e:
        logger.error(f"验证代码失败: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@arduino_ai_api.route('/api/arduino/boards', methods=['GET'])
def get_boards():
    """获取支持的板型列表"""
    try:
        result = arduino_service.get_boards()
        return jsonify(result)
    except Exception as e:
        logger.error(f"获取板型列表失败: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@arduino_ai_api.route('/api/arduino/templates', methods=['GET'])
def get_templates():
    """获取代码模板列表"""
    try:
        result = arduino_service.get_templates()
        return jsonify(result)
    except Exception as e:
        logger.error(f"获取模板列表失败: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@arduino_ai_api.route('/api/arduino/sensors', methods=['GET'])
def get_sensors():
    """获取传感器列表"""
    try:
        result = arduino_service.get_sensors()
        return jsonify(result)
    except Exception as e:
        logger.error(f"获取传感器列表失败: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@arduino_ai_api.route('/api/arduino/ports', methods=['GET'])
def get_serial_ports():
    """获取可用串口列表"""
    try:
        result = arduino_service.list_serial_ports()
        return jsonify(result)
    except Exception as e:
        logger.error(f"获取串口列表失败: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@arduino_ai_api.route('/api/arduino/components', methods=['GET'])
def get_components():
    """获取元件库"""
    try:
        result = arduino_ai_enhanced_service.get_component_library()
        return jsonify(result)
    except Exception as e:
        logger.error(f"获取元件库失败: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@arduino_ai_api.route('/api/arduino/circuit-templates', methods=['GET'])
def get_circuit_templates():
    """获取电路模板"""
    try:
        result = arduino_ai_enhanced_service.get_circuit_templates()
        return jsonify(result)
    except Exception as e:
        logger.error(f"获取电路模板失败: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@arduino_ai_api.route('/api/arduino/tutorials', methods=['GET'])
def get_tutorials():
    """
    获取教程列表
    
    Query Parameters:
        category: 分类
        difficulty: 难度
        page: 页码
        page_size: 每页数量
    """
    try:
        category = request.args.get('category')
        difficulty = request.args.get('difficulty')
        page = int(request.args.get('page', 1))
        page_size = int(request.args.get('page_size', 20))
        
        result = arduino_ai_enhanced_service.get_tutorials(
            category=category,
            difficulty=difficulty,
            page=page,
            page_size=page_size
        )
        
        return jsonify(result)
    except Exception as e:
        logger.error(f"获取教程列表失败: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@arduino_ai_api.route('/api/arduino/tutorials/<int:tutorial_id>', methods=['GET'])
def get_tutorial(tutorial_id):
    """
    获取教程详情
    
    Path Parameters:
        tutorial_id: 教程ID
    """
    try:
        result = arduino_ai_enhanced_service.get_tutorial_detail(tutorial_id)
        return jsonify(result)
    except Exception as e:
        logger.error(f"获取教程详情失败: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@arduino_ai_api.route('/api/arduino/projects', methods=['GET'])
def get_projects():
    """
    获取用户项目列表
    
    Query Parameters:
        page: 页码
        page_size: 每页数量
    """
    try:
        user_id = get_current_user()
        if not user_id:
            return jsonify({'success': False, 'error': '请先登录'}), 401
        
        page = int(request.args.get('page', 1))
        page_size = int(request.args.get('page_size', 20))
        
        result = arduino_ai_enhanced_service.get_user_projects(
            user_id=user_id,
            page=page,
            page_size=page_size
        )
        
        return jsonify(result)
    except Exception as e:
        logger.error(f"获取项目列表失败: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@arduino_ai_api.route('/api/arduino/projects/<int:project_id>', methods=['GET'])
def get_project(project_id):
    """
    获取项目详情
    
    Path Parameters:
        project_id: 项目ID
    """
    try:
        result = arduino_ai_enhanced_service.get_project_detail(project_id)
        return jsonify(result)
    except Exception as e:
        logger.error(f"获取项目详情失败: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@arduino_ai_api.route('/api/arduino/projects', methods=['POST'])
def save_project():
    """
    保存项目
    
    Request Body:
        project_name: 项目名称
        code: 代码
        board_type: 板型
        description: 描述
        circuit_data: 电路数据
        tags: 标签列表
        project_id: 项目ID（更新时使用）
    """
    try:
        user_id = get_current_user()
        if not user_id:
            return jsonify({'success': False, 'error': '请先登录'}), 401
        
        data = request.get_json()
        project_name = data.get('project_name', '未命名项目')
        code = data.get('code', '')
        board_type = data.get('board_type', 'uno')
        description = data.get('description', '')
        circuit_data = data.get('circuit_data')
        tags = data.get('tags')
        project_id = data.get('project_id')
        
        result = arduino_ai_enhanced_service.save_project(
            user_id=user_id,
            project_name=project_name,
            code=code,
            board_type=board_type,
            description=description,
            circuit_data=circuit_data,
            tags=tags,
            project_id=project_id
        )
        
        return jsonify(result)
    except Exception as e:
        logger.error(f"保存项目失败: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@arduino_ai_api.route('/api/arduino/projects/<int:project_id>', methods=['DELETE'])
def delete_project(project_id):
    """
    删除项目
    
    Path Parameters:
        project_id: 项目ID
    """
    try:
        user_id = get_current_user()
        if not user_id:
            return jsonify({'success': False, 'error': '请先登录'}), 401
        
        result = arduino_ai_enhanced_service.delete_project(user_id, project_id)
        
        return jsonify(result)
    except Exception as e:
        logger.error(f"删除项目失败: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@arduino_ai_api.route('/api/arduino/generate-project', methods=['POST'])
def generate_project():
    """
    生成完整Arduino项目
    
    Request Body:
        project_name: 项目名称
        code: 代码
        board: 板型
    """
    try:
        data = request.get_json()
        project_name = data.get('project_name', 'arduino_project')
        code = data.get('code', '')
        board = data.get('board', 'uno')
        
        if not code:
            return jsonify({'success': False, 'error': '代码不能为空'}), 400
        
        result = arduino_service.generate_project(project_name, code, board)
        
        return jsonify(result)
    except Exception as e:
        logger.error(f"生成项目失败: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500