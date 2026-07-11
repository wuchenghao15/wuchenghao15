# -*- coding: utf-8 -*-
#!/usr/bin/env python3
"""
系统升级API
提供RESTful接口来管理系统升级和全面升级引擎
"""

from flask import Blueprint, request, jsonify
import logging
import json
import sys
import os

logger = logging.getLogger(__name__)

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, PROJECT_ROOT)

upgrade_api = Blueprint('upgrade_api', __name__, url_prefix='/api/upgrade')


def _get_comprehensive_upgrader():
    """获取全面系统升级引擎实例"""
    try:
        from ai_engines.comprehensive_system_upgrader import comprehensive_system_upgrader
        return comprehensive_system_upgrader
    except Exception as e:
        logger.error(f"获取全面系统升级引擎失败: {e}")
        return None


@upgrade_api.route('/status', methods=['GET'])
def get_upgrade_status():
    """获取升级状态"""
    try:
        upgrader = _get_comprehensive_upgrader()
        if not upgrader:
            return jsonify({
                'success': False,
                'message': '升级引擎不可用'
            }), 500
        
        status = upgrader.get_upgrade_status()
        return jsonify({
            'success': True,
            'data': status
        }), 200
    except Exception as e:
        logger.error(f"获取升级状态失败: {str(e)}")
        return jsonify({
            'success': False,
            'message': f'获取升级状态失败: {str(e)}'
        }), 500


@upgrade_api.route('/modules', methods=['GET'])
def get_upgrade_modules():
    """获取升级模块列表"""
    try:
        upgrader = _get_comprehensive_upgrader()
        if not upgrader:
            return jsonify({
                'success': False,
                'message': '升级引擎不可用'
            }), 500
        
        status = upgrader.get_upgrade_status()
        return jsonify({
            'success': True,
            'data': status.get('upgrade_modules', []),
            'total': status.get('total_modules', 0)
        }), 200
    except Exception as e:
        logger.error(f"获取升级模块失败: {str(e)}")
        return jsonify({
            'success': False,
            'message': f'获取升级模块失败: {str(e)}'
        }), 500


@upgrade_api.route('/modules/<module_id>', methods=['GET'])
def get_module_detail(module_id):
    """获取模块详情"""
    try:
        upgrader = _get_comprehensive_upgrader()
        if not upgrader:
            return jsonify({
                'success': False,
                'message': '升级引擎不可用'
            }), 500
        
        detail = upgrader.get_module_details(module_id)
        if detail:
            return jsonify({
                'success': True,
                'data': detail
            }), 200
        else:
            return jsonify({
                'success': False,
                'message': '模块不存在'
            }), 404
    except Exception as e:
        logger.error(f"获取模块详情失败: {str(e)}")
        return jsonify({
            'success': False,
            'message': f'获取模块详情失败: {str(e)}'
        }), 500


@upgrade_api.route('/start', methods=['POST'])
def start_upgrade():
    """启动全面系统升级"""
    try:
        upgrader = _get_comprehensive_upgrader()
        if not upgrader:
            return jsonify({
                'success': False,
                'message': '升级引擎不可用'
            }), 500
        
        data = request.get_json() or {}
        phases = data.get('phases')
        
        import threading
        
        def run_upgrade():
            try:
                upgrader.start_comprehensive_upgrade(phases)
            except Exception as e:
                logger.error(f"升级执行失败: {e}")
        
        thread = threading.Thread(target=run_upgrade, daemon=True)
        thread.start()
        
        return jsonify({
            'success': True,
            'message': '升级已启动',
            'data': {
                'phases': phases or 'all',
                'status': 'running'
            }
        }), 200
    except Exception as e:
        logger.error(f"启动升级失败: {str(e)}")
        return jsonify({
            'success': False,
            'message': f'启动升级失败: {str(e)}'
        }), 500


@upgrade_api.route('/start-module/<module_id>', methods=['POST'])
def start_module_upgrade(module_id):
    """启动指定模块升级"""
    try:
        upgrader = _get_comprehensive_upgrader()
        if not upgrader:
            return jsonify({
                'success': False,
                'message': '升级引擎不可用'
            }), 500
        
        import threading
        
        def run_upgrade():
            try:
                upgrader.start_comprehensive_upgrade([module_id])
            except Exception as e:
                logger.error(f"模块升级执行失败: {e}")
        
        thread = threading.Thread(target=run_upgrade, daemon=True)
        thread.start()
        
        return jsonify({
            'success': True,
            'message': f'模块 {module_id} 升级已启动',
            'data': {
                'module_id': module_id,
                'status': 'running'
            }
        }), 200
    except Exception as e:
        logger.error(f"启动模块升级失败: {str(e)}")
        return jsonify({
            'success': False,
            'message': f'启动模块升级失败: {str(e)}'
        }), 500


@upgrade_api.route('/history', methods=['GET'])
def get_upgrade_history():
    """获取升级历史"""
    try:
        upgrader = _get_comprehensive_upgrader()
        if not upgrader:
            return jsonify({
                'success': False,
                'message': '升级引擎不可用'
            }), 500
        
        limit = request.args.get('limit', 20, type=int)
        history = upgrader.get_upgrade_history(limit)
        
        return jsonify({
            'success': True,
            'data': history,
            'total': len(history)
        }), 200
    except Exception as e:
        logger.error(f"获取升级历史失败: {str(e)}")
        return jsonify({
            'success': False,
            'message': f'获取升级历史失败: {str(e)}'
        }), 500


@upgrade_api.route('/versions', methods=['GET'])
def get_version_history():
    """获取版本历史"""
    try:
        upgrader = _get_comprehensive_upgrader()
        if not upgrader:
            return jsonify({
                'success': False,
                'message': '升级引擎不可用'
            }), 500
        
        limit = request.args.get('limit', 10, type=int)
        versions = upgrader.get_version_history(limit)
        
        return jsonify({
            'success': True,
            'data': versions,
            'total': len(versions)
        }), 200
    except Exception as e:
        logger.error(f"获取版本历史失败: {str(e)}")
        return jsonify({
            'success': False,
            'message': f'获取版本历史失败: {str(e)}'
        }), 500


@upgrade_api.route('/models', methods=['GET'])
def get_model_library():
    """获取AI模型库"""
    try:
        upgrader = _get_comprehensive_upgrader()
        if not upgrader:
            return jsonify({
                'success': False,
                'message': '升级引擎不可用'
            }), 500
        
        models = upgrader.get_model_library()
        
        return jsonify({
            'success': True,
            'data': models,
            'total': len(models)
        }), 200
    except Exception as e:
        logger.error(f"获取模型库失败: {str(e)}")
        return jsonify({
            'success': False,
            'message': f'获取模型库失败: {str(e)}'
        }), 500


@upgrade_api.route('/permissions', methods=['GET'])
def get_permission_templates():
    """获取权限模板"""
    try:
        upgrader = _get_comprehensive_upgrader()
        if not upgrader:
            return jsonify({
                'success': False,
                'message': '升级引擎不可用'
            }), 500
        
        permissions = upgrader.get_permission_templates()
        
        return jsonify({
            'success': True,
            'data': permissions,
            'total': len(permissions)
        }), 200
    except Exception as e:
        logger.error(f"获取权限模板失败: {str(e)}")
        return jsonify({
            'success': False,
            'message': f'获取权限模板失败: {str(e)}'
        }), 500


@upgrade_api.route('/ports', methods=['GET'])
def get_port_management():
    """获取端口管理信息"""
    try:
        upgrader = _get_comprehensive_upgrader()
        if not upgrader:
            return jsonify({
                'success': False,
                'message': '升级引擎不可用'
            }), 500
        
        ports = upgrader.get_port_management()
        
        return jsonify({
            'success': True,
            'data': ports,
            'total': len(ports)
        }), 200
    except Exception as e:
        logger.error(f"获取端口管理失败: {str(e)}")
        return jsonify({
            'success': False,
            'message': f'获取端口管理失败: {str(e)}'
        }), 500


@upgrade_api.route('/version-info', methods=['GET'])
def get_version_info():
    """获取完整版本信息"""
    try:
        upgrader = _get_comprehensive_upgrader()
        if not upgrader:
            return jsonify({
                'success': False,
                'message': '升级引擎不可用'
            }), 500
        
        version_info = upgrader._get_version_info()
        
        return jsonify({
            'success': True,
            'data': version_info
        }), 200
    except Exception as e:
        logger.error(f"获取版本信息失败: {str(e)}")
        return jsonify({
            'success': False,
            'message': f'获取版本信息失败: {str(e)}'
        }), 500


@upgrade_api.route('/suggestions', methods=['GET'])
def get_smart_suggestions():
    """获取AI智能建议"""
    try:
        upgrader = _get_comprehensive_upgrader()
        if not upgrader:
            return jsonify({
                'success': False,
                'message': '升级引擎不可用'
            }), 500
        
        import sqlite3
        conn = sqlite3.connect(upgrader.db_path)
        cursor = conn.cursor()
        cursor.execute('''SELECT * FROM ai_smart_suggestions
            ORDER BY priority DESC, created_at DESC LIMIT 50''')
        columns = [desc[0] for desc in cursor.description]
        results = []
        for row in cursor.fetchall():
            record = dict(zip(columns, row))
            if record.get('implementation_steps'):
                record['implementation_steps'] = __import__('json').loads(record['implementation_steps'])
            results.append(record)
        conn.close()
        
        return jsonify({
            'success': True,
            'data': results,
            'total': len(results)
        }), 200
    except Exception as e:
        logger.error(f"获取智能建议失败: {str(e)}")
        return jsonify({
            'success': False,
            'message': f'获取智能建议失败: {str(e)}'
        }), 500


@upgrade_api.route('/knowledge-graph', methods=['GET'])
def get_knowledge_graph():
    """获取知识图谱数据"""
    try:
        upgrader = _get_comprehensive_upgrader()
        if not upgrader:
            return jsonify({
                'success': False,
                'message': '升级引擎不可用'
            }), 500
        
        import sqlite3
        conn = sqlite3.connect(upgrader.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''SELECT * FROM knowledge_graph_nodes WHERE is_active = 1''')
        columns = [desc[0] for desc in cursor.description]
        nodes = []
        for row in cursor.fetchall():
            node = dict(zip(columns, row))
            if node.get('metadata'):
                node['metadata'] = __import__('json').loads(node['metadata'])
            nodes.append(node)
        
        cursor.execute('''SELECT * FROM knowledge_graph_relations WHERE is_active = 1''')
        columns = [desc[0] for desc in cursor.description]
        relations = []
        for row in cursor.fetchall():
            relations.append(dict(zip(columns, row)))
        
        conn.close()
        
        return jsonify({
            'success': True,
            'data': {
                'nodes': nodes,
                'relations': relations,
                'nodes_count': len(nodes),
                'relations_count': len(relations)
            }
        }), 200
    except Exception as e:
        logger.error(f"获取知识图谱失败: {str(e)}")
        return jsonify({
            'success': False,
            'message': f'获取知识图谱失败: {str(e)}'
        }), 500


@upgrade_api.route('/diagnosis', methods=['GET'])
def get_diagnosis_records():
    """获取智能诊断记录"""
    try:
        upgrader = _get_comprehensive_upgrader()
        if not upgrader:
            return jsonify({
                'success': False,
                'message': '升级引擎不可用'
            }), 500
        
        import sqlite3
        conn = sqlite3.connect(upgrader.db_path)
        cursor = conn.cursor()
        cursor.execute('''SELECT * FROM intelligent_diagnosis_records
            ORDER BY created_at DESC LIMIT 30''')
        columns = [desc[0] for desc in cursor.description]
        results = []
        for row in cursor.fetchall():
            record = dict(zip(columns, row))
            if record.get('recommendations'):
                record['recommendations'] = __import__('json').loads(record['recommendations'])
            results.append(record)
        conn.close()
        
        return jsonify({
            'success': True,
            'data': results,
            'total': len(results)
        }), 200
    except Exception as e:
        logger.error(f"获取诊断记录失败: {str(e)}")
        return jsonify({
            'success': False,
            'message': f'获取诊断记录失败: {str(e)}'
        }), 500


@upgrade_api.route('/components', methods=['GET'])
def get_component_library():
    """获取前端组件库"""
    try:
        upgrader = _get_comprehensive_upgrader()
        if not upgrader:
            return jsonify({
                'success': False,
                'message': '升级引擎不可用'
            }), 500
        
        import sqlite3
        conn = sqlite3.connect(upgrader.db_path)
        cursor = conn.cursor()
        cursor.execute('''SELECT * FROM frontend_component_library
            WHERE is_active = 1 ORDER BY category, component_name''')
        columns = [desc[0] for desc in cursor.description]
        results = []
        for row in cursor.fetchall():
            record = dict(zip(columns, row))
            for key in ['props', 'events', 'slots']:
                if record.get(key):
                    record[key] = __import__('json').loads(record[key])
            results.append(record)
        conn.close()
        
        return jsonify({
            'success': True,
            'data': results,
            'total': len(results)
        }), 200
    except Exception as e:
        logger.error(f"获取组件库失败: {str(e)}")
        return jsonify({
            'success': False,
            'message': f'获取组件库失败: {str(e)}'
        }), 500
