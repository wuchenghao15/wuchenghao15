#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
MTSCOS AI 系统配置 API 服务
"""

from flask import Flask, jsonify, request
import sys
import os

sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from system_config_manager import SystemConfigManager

app = Flask(__name__)
app.config['JSON_AS_ASCII'] = False

config_manager = None

def init_app():
    """初始化应用"""
    global config_manager
    config_manager = SystemConfigManager('system_config.db')
    print("✅ 系统配置管理器初始化完成")

@app.route('/api/config', methods=['GET'])
def get_config():
    """获取所有配置"""
    try:
        group = request.args.get('group')
        if group:
            configs = config_manager.get_all_configs(group)
        else:
            configs = config_manager.get_all_configs()
        return jsonify({
            'success': True,
            'data': configs,
            'groups': config_manager.get_config_groups()
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/config/<key>', methods=['GET'])
def get_config_by_key(key):
    """根据键获取单个配置"""
    try:
        value = config_manager.get_config(key)
        return jsonify({
            'success': True,
            'key': key,
            'value': value
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/config/<key>', methods=['POST', 'PUT'])
def update_config(key):
    """更新配置"""
    try:
        data = request.get_json()
        value = data.get('value')
        
        if value is None:
            return jsonify({
                'success': False,
                'error': '配置值不能为空'
            }), 400
            
        user_id = data.get('user_id', 'api')
        config_manager.set_config(key, value, user_id)
        
        return jsonify({
            'success': True,
            'message': f'配置 {key} 已更新',
            'value': value
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/config/groups', methods=['GET'])
def get_config_groups():
    """获取所有配置分组"""
    try:
        groups = config_manager.get_config_groups()
        return jsonify({
            'success': True,
            'data': groups
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/system/info', methods=['GET'])
def get_system_info():
    """获取系统信息"""
    try:
        return jsonify({
            'success': True,
            'data': {
                'name': config_manager.get_config('system.name'),
                'version': config_manager.get_config('system.version'),
                'port': config_manager.get_config('system.port', '8888'),
                'httpPort': config_manager.get_config('system.http_port', '8080'),
                'allowGuestAccess': config_manager.get_config('system.allow_guest_access'),
                'sessionTimeout': config_manager.get_config('system.session_timeout')
            }
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/exam/config', methods=['GET'])
def get_exam_config():
    """获取考试配置"""
    try:
        return jsonify({
            'success': True,
            'data': {
                'maxDuration': config_manager.get_config('exam.max_exam_duration'),
                'passingScore': config_manager.get_config('exam.passing_score'),
                'allowReview': config_manager.get_config('exam.allow_review')
            }
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/student/config', methods=['GET'])
def get_student_config():
    """获取学生配置"""
    try:
        return jsonify({
            'success': True,
            'data': {
                'nineYearEnabled': config_manager.get_config('student.nine_year.enabled'),
                'adultEnabled': config_manager.get_config('student.adult.enabled')
            }
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/ui/config', methods=['GET'])
def get_ui_config():
    """获取界面配置"""
    try:
        return jsonify({
            'success': True,
            'data': {
                'theme': config_manager.get_config('ui.theme'),
                'particlesEnabled': config_manager.get_config('ui.particles_enabled'),
                'language': config_manager.get_config('ui.language')
            }
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/permission/config', methods=['GET'])
def get_permission_config():
    """获取权限配置"""
    try:
        return jsonify({
            'success': True,
            'data': {
                'enableAutoDetect': config_manager.get_config('permission.enable_auto_detect'),
                'defaultGroup': config_manager.get_config('permission.default_group')
            }
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/export', methods=['GET'])
def export_config():
    """导出所有配置"""
    try:
        data = config_manager.export_config()
        return jsonify({
            'success': True,
            'data': data
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/import', methods=['POST'])
def import_config():
    """导入配置"""
    try:
        data = request.get_json()
        overwrite = data.get('overwrite', False)
        count = config_manager.import_config(data, overwrite)
        
        return jsonify({
            'success': True,
            'message': f'成功导入 {count} 个配置项',
            'count': count
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/health', methods=['GET'])
def health_check():
    """健康检查"""
    return jsonify({
        'status': 'healthy',
        'service': 'system-config-api',
        'version': '3.2.0'
    })

if __name__ == '__main__':
    init_app()
    print("\n🚀 启动系统配置 API 服务")
    print("=" * 60)
    print("📍 API 地址: http://localhost:5000/api")
    print("📍 健康检查: http://localhost:5000/health")
    print("=" * 60)
    app.run(host='0.0.0.0', port=5000, debug=True)
