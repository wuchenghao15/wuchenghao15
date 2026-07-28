#!/usr/bin/env python3
"""AI企业级Agent统一管理API"""

from flask import Blueprint, request, jsonify
from ai_engines.ai_employee_manager import AIEmployeeManager

ai_enterprise_api = Blueprint('ai_enterprise_api', __name__, url_prefix='/api/ai/enterprise')

employee_manager = AIEmployeeManager()

@ai_enterprise_api.route('/employees/list', methods=['GET'])
def list_employees():
    """获取所有企业级AI员工列表"""
    try:
        result = employee_manager.list_employees()
        enterprise_types = [
            'education_manager', 'community_manager', 'activity_manager',
            'content_creator', 'config_manager', 'log_analyzer',
            'document_processor', 'vulnerability_scanner', 'cybersecurity',
            'system_extension'
        ]
        enterprise_employees = [
            emp for emp in result.get('employees', []) 
            if emp.get('type') in enterprise_types
        ]
        return jsonify({
            'success': True,
            'data': enterprise_employees,
            'total': len(enterprise_employees)
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@ai_enterprise_api.route('/employee/<employee_id>', methods=['GET'])
def get_employee(employee_id):
    """获取单个AI员工详情"""
    try:
        employee = employee_manager.employees.get(employee_id)
        if not employee:
            return jsonify({'success': False, 'error': '员工不存在'}), 404
        
        return jsonify({
            'success': True,
            'data': {
                'employee_id': employee.employee_id,
                'name': employee.name,
                'type': getattr(employee, 'type', employee.employee_type),
                'level': employee.level,
                'skills': getattr(employee, 'skills', []),
                'status': getattr(employee, 'status', 'active')
            }
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@ai_enterprise_api.route('/education/courses', methods=['POST'])
def manage_courses():
    """课程管理"""
    try:
        data = request.get_json()
        action = data.get('action', 'list')
        employee = employee_manager.employees.get('edu_001')
        
        if not employee:
            return jsonify({'success': False, 'error': '教育管理AI员工不存在'}), 500
        
        result = employee.manage_courses(action, **data)
        return jsonify(result)
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@ai_enterprise_api.route('/education/performance', methods=['POST'])
def analyze_performance():
    """分析学生表现"""
    try:
        data = request.get_json()
        employee = employee_manager.employees.get('edu_001')
        
        if not employee:
            return jsonify({'success': False, 'error': '教育管理AI员工不存在'}), 500
        
        result = employee.analyze_performance(data)
        return jsonify(result)
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@ai_enterprise_api.route('/community/users', methods=['POST'])
def manage_users():
    """用户管理"""
    try:
        data = request.get_json()
        action = data.get('action', 'list')
        employee = employee_manager.employees.get('comm_001')
        
        if not employee:
            return jsonify({'success': False, 'error': '社区管理AI员工不存在'}), 500
        
        result = employee.manage_users(action, **data)
        return jsonify(result)
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@ai_enterprise_api.route('/community/posts', methods=['POST'])
def manage_posts():
    """帖子管理"""
    try:
        data = request.get_json()
        action = data.get('action', 'list')
        employee = employee_manager.employees.get('comm_001')
        
        if not employee:
            return jsonify({'success': False, 'error': '社区管理AI员工不存在'}), 500
        
        result = employee.manage_posts(action, **data)
        return jsonify(result)
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@ai_enterprise_api.route('/activity/manage', methods=['POST'])
def manage_activities():
    """活动管理"""
    try:
        data = request.get_json()
        action = data.get('action', 'list')
        employee = employee_manager.employees.get('act_001')
        
        if not employee:
            return jsonify({'success': False, 'error': '活动管理AI员工不存在'}), 500
        
        result = employee.manage_activities(action, **data)
        return jsonify(result)
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@ai_enterprise_api.route('/activity/analyze', methods=['POST'])
def analyze_activity():
    """分析活动效果"""
    try:
        data = request.get_json()
        activity_id = data.get('activity_id', '')
        employee = employee_manager.employees.get('act_001')
        
        if not employee:
            return jsonify({'success': False, 'error': '活动管理AI员工不存在'}), 500
        
        result = employee.analyze_activity(activity_id)
        return jsonify(result)
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@ai_enterprise_api.route('/content/create', methods=['POST'])
def create_content():
    """创建内容"""
    try:
        data = request.get_json()
        content_type = data.get('type', 'article')
        employee = employee_manager.employees.get('content_001')
        
        if not employee:
            return jsonify({'success': False, 'error': '内容创作AI员工不存在'}), 500
        
        result = employee.create_content(content_type, **data)
        return jsonify(result)
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@ai_enterprise_api.route('/content/seo', methods=['POST'])
def optimize_seo():
    """SEO优化"""
    try:
        data = request.get_json()
        content = data.get('content', '')
        keywords = data.get('keywords', [])
        employee = employee_manager.employees.get('content_001')
        
        if not employee:
            return jsonify({'success': False, 'error': '内容创作AI员工不存在'}), 500
        
        result = employee.optimize_seo(content, keywords)
        return jsonify(result)
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@ai_enterprise_api.route('/config/get', methods=['GET'])
def get_config():
    """获取配置"""
    try:
        config_name = request.args.get('name', '')
        employee = employee_manager.employees.get('cfg_001')
        
        if not employee:
            return jsonify({'success': False, 'error': '配置管理AI员工不存在'}), 500
        
        result = employee.get_config(config_name)
        return jsonify(result)
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@ai_enterprise_api.route('/config/set', methods=['POST'])
def set_config():
    """设置配置"""
    try:
        data = request.get_json()
        config_name = data.get('name', '')
        value = data.get('value', '')
        description = data.get('description', '')
        employee = employee_manager.employees.get('cfg_001')
        
        if not employee:
            return jsonify({'success': False, 'error': '配置管理AI员工不存在'}), 500
        
        result = employee.set_config(config_name, value, description)
        return jsonify(result)
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@ai_enterprise_api.route('/log/collect', methods=['POST'])
def collect_logs():
    """收集日志"""
    try:
        data = request.get_json()
        log_source = data.get('source', '')
        logs = data.get('logs', [])
        employee = employee_manager.employees.get('log_001')
        
        if not employee:
            return jsonify({'success': False, 'error': '日志分析AI员工不存在'}), 500
        
        result = employee.collect_logs(log_source, logs)
        return jsonify(result)
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@ai_enterprise_api.route('/log/analyze', methods=['GET'])
def analyze_logs():
    """分析日志"""
    try:
        employee = employee_manager.employees.get('log_001')
        
        if not employee:
            return jsonify({'success': False, 'error': '日志分析AI员工不存在'}), 500
        
        anomalies = employee.detect_anomalies()
        performance = employee.analyze_performance()
        report = employee.generate_report()
        
        return jsonify({
            'success': True,
            'anomalies': anomalies,
            'performance': performance,
            'report': report
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@ai_enterprise_api.route('/document/upload', methods=['POST'])
def upload_document():
    """上传文档"""
    try:
        data = request.get_json()
        employee = employee_manager.employees.get('doc_001')
        
        if not employee:
            return jsonify({'success': False, 'error': '文档处理AI员工不存在'}), 500
        
        result = employee.upload_document(data)
        return jsonify(result)
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@ai_enterprise_api.route('/document/summary', methods=['POST'])
def summarize_document():
    """文档摘要"""
    try:
        data = request.get_json()
        document_id = data.get('document_id', '')
        employee = employee_manager.employees.get('doc_001')
        
        if not employee:
            return jsonify({'success': False, 'error': '文档处理AI员工不存在'}), 500
        
        result = employee.summarize_document(document_id)
        return jsonify(result)
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@ai_enterprise_api.route('/security/scan/code', methods=['POST'])
def scan_code():
    """扫描代码漏洞"""
    try:
        data = request.get_json()
        code = data.get('code', '')
        file_path = data.get('file_path', '')
        employee = employee_manager.employees.get('vuln_001')
        
        if not employee:
            return jsonify({'success': False, 'error': '安全漏洞检测AI员工不存在'}), 500
        
        result = employee.scan_code(code, file_path)
        return jsonify(result)
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@ai_enterprise_api.route('/security/scan/dependencies', methods=['POST'])
def scan_dependencies():
    """扫描依赖漏洞"""
    try:
        data = request.get_json()
        dependencies = data.get('dependencies', [])
        employee = employee_manager.employees.get('vuln_001')
        
        if not employee:
            return jsonify({'success': False, 'error': '安全漏洞检测AI员工不存在'}), 500
        
        result = employee.scan_dependencies(dependencies)
        return jsonify(result)
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@ai_enterprise_api.route('/cybersecurity/detect', methods=['POST'])
def detect_intrusion():
    """检测入侵"""
    try:
        data = request.get_json()
        employee = employee_manager.employees.get('cyber_001')
        
        if not employee:
            return jsonify({'success': False, 'error': '网络安全AI员工不存在'}), 500
        
        result = employee.detect_intrusion(data)
        return jsonify(result)
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@ai_enterprise_api.route('/cybersecurity/firewall', methods=['POST'])
def manage_firewall():
    """防火墙管理"""
    try:
        data = request.get_json()
        action = data.get('action', '')
        employee = employee_manager.employees.get('cyber_001')
        
        if not employee:
            return jsonify({'success': False, 'error': '网络安全AI员工不存在'}), 500
        
        result = employee.manage_firewall(action, **data)
        return jsonify(result)
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@ai_enterprise_api.route('/extension/install', methods=['POST'])
def install_extension():
    """安装扩展"""
    try:
        data = request.get_json()
        employee = employee_manager.employees.get('ext_001')
        
        if not employee:
            return jsonify({'success': False, 'error': '系统扩展AI员工不存在'}), 500
        
        result = employee.install_extension(data)
        return jsonify(result)
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@ai_enterprise_api.route('/extension/list', methods=['GET'])
def list_extensions():
    """列出扩展"""
    try:
        employee = employee_manager.employees.get('ext_001')
        
        if not employee:
            return jsonify({'success': False, 'error': '系统扩展AI员工不存在'}), 500
        
        result = employee.list_extensions()
        return jsonify(result)
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500