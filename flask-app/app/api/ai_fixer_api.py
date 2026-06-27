# -*- coding: utf-8 -*-
"""
AI员工批量修复API
提供统一的批量修复接口，调用各专业AI员工进行修复
"""

from flask import Blueprint, jsonify, request, current_app
import logging

logger = logging.getLogger(__name__)

ai_fixer_api = Blueprint('ai_fixer_api', __name__)


@ai_fixer_api.route('/api/ai/batch_fix', methods=['POST'])
def batch_fix():
    """AI员工批量修复接口"""
    try:
        data = request.get_json()
        fix_types = data.get('fix_types', ['template', 'route'])
        
        results = []
        
        # 模板修复
        if 'template' in fix_types:
            from ai_engines.template_fixer_ai import get_template_fixer_ai
            template_fixer = get_template_fixer_ai()
            template_dir = current_app.template_folder
            result = template_fixer.batch_fix_templates(template_dir)
            results.append(result)
        
        # 路由修复
        if 'route' in fix_types:
            from ai_engines.route_fixer_ai import get_route_fixer_ai
            route_fixer = get_route_fixer_ai(current_app)
            result = route_fixer.batch_fix_routes()
            results.append(result)
        
        return jsonify({
            'success': True,
            'message': 'AI员工批量修复完成',
            'results': results,
            'timestamp': datetime.now().isoformat()
        })
    
    except Exception as e:
        logger.error(f"AI员工批量修复失败: {e}")
        return jsonify({
            'success': False,
            'error': str(e),
            'message': '批量修复失败'
        }), 500


@ai_fixer_api.route('/api/ai/fix_report', methods=['GET'])
def get_fix_report():
    """获取AI员工修复报告"""
    try:
        import sqlite3
        db_path = '/Users/wuchenghao/Library/CloudStorage/OneDrive-个人/文档/MTSCOS_AI_Project/flask-app/app.db'
        
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # 查询最近的修复报告
        cursor.execute('''
        SELECT employee_name, specialty, issue_type, issue_description, fix_method, fixed, timestamp
        FROM ai_employee_fix_reports
        ORDER BY timestamp DESC
        LIMIT 100
        ''')
        
        reports = []
        for row in cursor.fetchall():
            reports.append({
                'employee_name': row[0],
                'specialty': row[1],
                'issue_type': row[2],
                'issue_description': row[3],
                'fix_method': row[4],
                'fixed': row[5],
                'timestamp': row[6]
            })
        
        conn.close()
        
        return jsonify({
            'success': True,
            'reports': reports,
            'total': len(reports)
        })
    
    except Exception as e:
        logger.error(f"获取修复报告失败: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@ai_fixer_api.route('/api/ai/employees', methods=['GET'])
def list_ai_employees():
    """列出所有AI员工"""
    employees = [
        {
            'employee_id': 'template_fixer_001',
            'employee_name': '模板修复专家',
            'specialty': '模板依赖修复、静态文件缺失检测、路径配置优化',
            'status': 'active',
            'fix_count': 0,
            'report_count': 0
        },
        {
            'employee_id': 'route_fixer_001',
            'employee_name': '路由修复专家',
            'specialty': '路由冲突检测、权限配置修复、404错误处理',
            'status': 'active',
            'fix_count': 0,
            'report_count': 0
        }
    ]
    
    return jsonify({
        'success': True,
        'employees': employees,
        'total': len(employees)
    })


# 导入datetime
from datetime import datetime