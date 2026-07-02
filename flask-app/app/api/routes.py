#!/usr/bin/env python3
"""API路由管理模块,实现统一的API路由管理系统"""

from flask import jsonify, request
from app.api import api_bp
from app.services.rule_management import rule_management_service
from app.services.exam_service import exam_service
from app.utils.logging import logger
from app.utils.ai_json_importer import ai_json_importer
from app.services.json_import_agent_service import json_import_agent_service
from app.utils.db_structure_analyzer import db_structure_analyzer
from app.utils.db_relationship_enhancer import db_relationship_enhancer
from app.utils.data_link_closure import data_link_closure
from app.utils.db_security_enhancer import db_security_enhancer

try:
    from app.services.ai_brain_service import ai_brain_service
except ImportError:
    class FakeAIBrainService:
        def get_status(self):
            return {'status': 'not_available', 'knowledge_count': 0}
    ai_brain_service = FakeAIBrainService()

API_VERSION = "v1"

@api_bp.route('/health', methods=['GET'])
def health_check():
    """API健康检查"""
    return jsonify({
        'success': True,
        'data': {
            'status': 'healthy',
            'api_version': API_VERSION,
            'service': 'MTSCOS API'
        }
    })

@api_bp.route('/status', methods=['GET'])
def get_system_status():
    """获取系统状态"""
    try:
        rule_status = rule_management_service.get_rules()
        brain_status = ai_brain_service.get_status()
        exam_status = exam_service.get_status()

        return jsonify({
            'success': True,
            'data': {
                'api_version': API_VERSION,
                'rule_management': {
                    'rules_count': sum(len(rules) for rules in rule_status.values())
                },
                'ai_brain': {
                    'status': brain_status.get('status', 'unknown'),
                    'knowledge_count': brain_status.get('knowledge_count', 0)
                },
                'exam_service': {
                    'status': exam_status.get('status', 'unknown'),
                    'questions_count': exam_status.get('questions_count', 0)
                }
            }
        })
    except Exception as e:
        logger.error(f"获取系统状态失败: {str(e)}")
        return jsonify({
            'success': False,
            'error': f'获取系统状态失败: {str(e)}'
        }), 500

@api_bp.route('/handshake', methods=['POST'])
def handshake():
    """API握手端点"""
    try:
        import uuid
        import time

        session_id = str(uuid.uuid4())
        api_key = str(uuid.uuid4())

        return jsonify({
            'success': True,
            'data': {
                'sessionId': session_id,
                'apiKey': api_key,
                'apiVersion': API_VERSION,
                'timestamp': int(time.time())
            }
        })
    except Exception as e:
        logger.error(f"握手失败: {str(e)}")
        return jsonify({
            'success': False,
            'error': f'握手失败: {str(e)}'
        }), 500

@api_bp.route('/heartbeat', methods=['POST'])
def heartbeat():
    """API心跳端点"""
    try:
        return jsonify({
            'success': True,
            'data': {
                'status': 'ok',
                'timestamp': int(time.time())
            }
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'心跳失败: {str(e)}'
        }), 500

@api_bp.route('/docs', methods=['GET'])
def get_api_docs():
    """获取API文档"""
    docs = {
        'api_version': API_VERSION,
        'endpoints': [
            {
                'path': '/api/health',
                'method': 'GET',
                'description': 'API健康检查'
            },
            {
                'path': '/api/status',
                'method': 'GET',
                'description': '获取系统状态'
            },
            {
                'path': '/api/handshake',
                'method': 'POST',
                'description': 'API握手'
            },
            {
                'path': '/api/heartbeat',
                'method': 'POST',
                'description': 'API心跳'
            },
            {
                'path': '/api/exam/list',
                'method': 'GET',
                'description': '获取考试列表'
            },
            {
                'path': '/api/exam/questions',
                'method': 'GET',
                'description': '获取考试题目'
            },
            {
                'path': '/api/exam/generate',
                'method': 'POST',
                'description': '生成试卷'
            },
            {
                'path': '/api/exam/<exam_id>',
                'method': 'GET',
                'description': '获取考试详情'
            }
        ],
        'rate_limit': {
            'enabled': True,
            'limit': '100 requests per minute'
        }
    }

    return jsonify({
        'success': True,
        'data': docs
    })

@api_bp.route('/rules', methods=['GET'])
def get_rules():
    """获取所有规则"""
    try:
        rules = rule_management_service.get_rules()
        return jsonify({
            'success': True,
            'data': rules
        })
    except Exception as e:
        logger.error(f"获取规则失败: {str(e)}")
        return jsonify({
            'success': False,
            'error': f'获取规则失败: {str(e)}'
        }), 500

@api_bp.route('/rules/<rule_type>', methods=['GET'])
def get_rules_by_type(rule_type):
    """根据类型获取规则"""
    try:
        rules = rule_management_service.get_rules(rule_type)
        return jsonify({
            'success': True,
            'data': rules
        })
    except Exception as e:
        logger.error(f"获取规则失败: {str(e)}")
        return jsonify({
            'success': False,
            'error': f'获取规则失败: {str(e)}'
        }), 500

@api_bp.route('/ai-brain/status', methods=['GET'])
def get_ai_brain_status():
    """获取AI脑库状态"""
    try:
        status = ai_brain_service.get_status()
        return jsonify({
            'success': True,
            'data': status
        })
    except Exception as e:
        logger.error(f"获取AI脑库状态失败: {str(e)}")
        return jsonify({
            'success': False,
            'error': f'获取AI脑库状态失败: {str(e)}'
        }), 500

@api_bp.route('/exam/list', methods=['GET'])
def get_exam_list():
    """获取考试列表"""
    try:
        exams = exam_service.get_exam_list()
        return jsonify({
            'success': True,
            'data': exams
        })
    except Exception as e:
        logger.error(f"获取考试列表失败: {str(e)}")
        return jsonify({
            'success': False,
            'error': f'获取考试列表失败: {str(e)}'
        }), 500

@api_bp.route('/exam/questions', methods=['GET'])
def get_exam_questions():
    """获取考试题目"""
    try:
        questions = exam_service.get_questions()
        return jsonify({
            'success': True,
            'data': questions
        })
    except Exception as e:
        logger.error(f"获取考试题目失败: {str(e)}")
        return jsonify({
            'success': False,
            'error': f'获取考试题目失败: {str(e)}'
        }), 500

@api_bp.route('/exam/generate', methods=['POST'])
def generate_exam():
    """生成试卷"""
    try:
        data = request.json or {}
        exam = exam_service.generate_exam(data)
        return jsonify({
            'success': True,
            'data': exam
        })
    except Exception as e:
        logger.error(f"生成试卷失败: {str(e)}")
        return jsonify({
            'success': False,
            'error': f'生成试卷失败: {str(e)}'
        }), 500

@api_bp.route('/exam/<exam_id>', methods=['GET'])
def get_exam_detail(exam_id):
    """获取考试详情"""
    try:
        exam = exam_service.get_exam(exam_id)
        return jsonify({
            'success': True,
            'data': exam
        })
    except Exception as e:
        logger.error(f"获取考试详情失败: {str(e)}")
        return jsonify({
            'success': False,
            'error': f'获取考试详情失败: {str(e)}'
        }), 500


@api_bp.route('/json-import/analyze', methods=['POST'])
def analyze_json_for_import():
    """分析JSON数据，提供导入建议"""
    try:
        json_data = request.json
        if not json_data:
            return jsonify({
                'success': False,
                'error': 'JSON数据为空'
            }), 400
        
        if isinstance(json_data, dict):
            json_data = [json_data]
        
        result = ai_json_importer.analyze_json_for_import(json_data)
        return jsonify(result)
    except Exception as e:
        logger.error(f"分析JSON数据失败: {str(e)}")
        return jsonify({
            'success': False,
            'error': f'分析JSON数据失败: {str(e)}'
        }), 500


@api_bp.route('/json-import/upload', methods=['POST'])
def upload_json_data():
    """上传JSON数据到数据库（自动匹配表）"""
    try:
        json_data = request.json
        if not json_data:
            return jsonify({
                'success': False,
                'error': 'JSON数据为空'
            }), 400
        
        if isinstance(json_data, dict):
            json_data = [json_data]
        
        table_name = request.args.get('table_name', None)
        auto_create = request.args.get('auto_create', 'true').lower() == 'true'
        
        result = ai_json_importer.import_json_data(json_data, table_name, auto_create)
        return jsonify(result)
    except Exception as e:
        logger.error(f"上传JSON数据失败: {str(e)}")
        return jsonify({
            'success': False,
            'error': f'上传JSON数据失败: {str(e)}'
        }), 500


@api_bp.route('/json-import/tables', methods=['GET'])
def get_import_tables():
    """获取可导入的表列表"""
    try:
        tables = ai_json_importer._get_all_table_names()
        return jsonify({
            'success': True,
            'data': {
                'tables': tables,
                'count': len(tables)
            }
        })
    except Exception as e:
        logger.error(f"获取表列表失败: {str(e)}")
        return jsonify({
            'success': False,
            'error': f'获取表列表失败: {str(e)}'
        }), 500


@api_bp.route('/json-import/history', methods=['GET'])
def get_import_history():
    """获取导入历史记录"""
    try:
        history = ai_json_importer.import_history[-20:]
        return jsonify({
            'success': True,
            'data': {
                'history': history,
                'total_count': len(ai_json_importer.import_history)
            }
        })
    except Exception as e:
        logger.error(f"获取导入历史失败: {str(e)}")
        return jsonify({
            'success': False,
            'error': f'获取导入历史失败: {str(e)}'
        }), 500


@api_bp.route('/json-import/agent/status', methods=['GET'])
def get_json_import_agent_status():
    """获取JSON数据导入Agent状态"""
    try:
        status = json_import_agent_service.get_status()
        return jsonify({
            'success': True,
            'data': status
        })
    except Exception as e:
        logger.error(f"获取Agent状态失败: {str(e)}")
        return jsonify({
            'success': False,
            'error': f'获取Agent状态失败: {str(e)}'
        }), 500


@api_bp.route('/json-import/agent/start', methods=['POST'])
def start_json_import_agent():
    """启动JSON数据导入Agent"""
    try:
        json_import_agent_service.start_agent()
        status = json_import_agent_service.get_status()
        return jsonify({
            'success': True,
            'message': 'JSON数据导入Agent已启动',
            'data': status
        })
    except Exception as e:
        logger.error(f"启动Agent失败: {str(e)}")
        return jsonify({
            'success': False,
            'error': f'启动Agent失败: {str(e)}'
        }), 500


@api_bp.route('/json-import/agent/stop', methods=['POST'])
def stop_json_import_agent():
    """停止JSON数据导入Agent"""
    try:
        json_import_agent_service.stop_agent()
        status = json_import_agent_service.get_status()
        return jsonify({
            'success': True,
            'message': 'JSON数据导入Agent已停止',
            'data': status
        })
    except Exception as e:
        logger.error(f"停止Agent失败: {str(e)}")
        return jsonify({
            'success': False,
            'error': f'停止Agent失败: {str(e)}'
        }), 500


@api_bp.route('/json-import/agent/task/create', methods=['POST'])
def create_json_import_task():
    """创建JSON数据导入任务"""
    try:
        json_data = request.json
        if not json_data:
            return jsonify({
                'success': False,
                'error': 'JSON数据为空'
            }), 400
        
        if isinstance(json_data, dict):
            json_data = [json_data]
        
        table_name = request.args.get('table_name', None)
        auto_create = request.args.get('auto_create', 'true').lower() == 'true'
        priority = int(request.args.get('priority', 0))
        
        task = json_import_agent_service.create_task(json_data, table_name, auto_create, priority)
        return jsonify({
            'success': True,
            'message': '任务创建成功',
            'data': task.to_dict()
        })
    except Exception as e:
        logger.error(f"创建任务失败: {str(e)}")
        return jsonify({
            'success': False,
            'error': f'创建任务失败: {str(e)}'
        }), 500


@api_bp.route('/json-import/agent/task/execute/<task_code>', methods=['POST'])
def execute_json_import_task(task_code):
    """执行指定的JSON数据导入任务"""
    try:
        task = json_import_agent_service.execute_task(task_code)
        return jsonify({
            'success': task.is_successful,
            'message': '任务执行完成',
            'data': task.to_dict()
        })
    except ValueError as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 400
    except Exception as e:
        logger.error(f"执行任务失败: {str(e)}")
        return jsonify({
            'success': False,
            'error': f'执行任务失败: {str(e)}'
        }), 500


@api_bp.route('/json-import/agent/task/execute-all', methods=['POST'])
def execute_all_json_import_tasks():
    """执行所有待处理的JSON数据导入任务"""
    try:
        results = json_import_agent_service.run_all_pending_tasks()
        return jsonify({
            'success': True,
            'message': f'已执行{len(results)}个任务',
            'data': [task.to_dict() for task in results]
        })
    except Exception as e:
        logger.error(f"执行所有任务失败: {str(e)}")
        return jsonify({
            'success': False,
            'error': f'执行所有任务失败: {str(e)}'
        }), 500


@api_bp.route('/json-import/agent/task/history', methods=['GET'])
def get_json_import_task_history():
    """获取JSON数据导入任务历史"""
    try:
        limit = int(request.args.get('limit', 20))
        tasks = json_import_agent_service.get_task_history(limit)
        return jsonify({
            'success': True,
            'data': {
                'tasks': [task.to_dict() for task in tasks],
                'count': len(tasks)
            }
        })
    except Exception as e:
        logger.error(f"获取任务历史失败: {str(e)}")
        return jsonify({
            'success': False,
            'error': f'获取任务历史失败: {str(e)}'
        }), 500


@api_bp.route('/json-import/agent/task/pending', methods=['GET'])
def get_json_import_pending_tasks():
    """获取待执行的JSON数据导入任务"""
    try:
        tasks = json_import_agent_service.get_pending_tasks()
        return jsonify({
            'success': True,
            'data': {
                'tasks': [task.to_dict() for task in tasks],
                'count': len(tasks)
            }
        })
    except Exception as e:
        logger.error(f"获取待执行任务失败: {str(e)}")
        return jsonify({
            'success': False,
            'error': f'获取待执行任务失败: {str(e)}'
        }), 500


@api_bp.route('/json-import/agent/execute', methods=['POST'])
def agent_execute_direct():
    """通过Agent直接执行JSON数据导入（不创建任务记录）"""
    try:
        json_data = request.json
        if not json_data:
            return jsonify({
                'success': False,
                'error': 'JSON数据为空'
            }), 400
        
        if isinstance(json_data, dict):
            json_data = [json_data]
        
        table_name = request.args.get('table_name', None)
        auto_create = request.args.get('auto_create', 'true').lower() == 'true'
        
        result = json_import_agent_service.execute_direct(json_data, table_name, auto_create)
        return jsonify(result)
    except Exception as e:
        logger.error(f"Agent执行失败: {str(e)}")
        return jsonify({
            'success': False,
            'error': f'Agent执行失败: {str(e)}'
        }), 500


@api_bp.route('/db/analyze/structure', methods=['GET'])
def analyze_db_structure():
    """分析数据库结构"""
    try:
        report = db_structure_analyzer.generate_structure_report()
        return jsonify({
            'success': True,
            'data': report
        })
    except Exception as e:
        logger.error(f"分析数据库结构失败: {str(e)}")
        return jsonify({
            'success': False,
            'error': f'分析数据库结构失败: {str(e)}'
        }), 500


@api_bp.route('/db/analyze/integrity', methods=['GET'])
def analyze_db_integrity():
    """分析数据库完整性"""
    try:
        integrity = db_structure_analyzer.analyze_data_integrity()
        return jsonify({
            'success': True,
            'data': integrity
        })
    except Exception as e:
        logger.error(f"分析数据库完整性失败: {str(e)}")
        return jsonify({
            'success': False,
            'error': f'分析数据库完整性失败: {str(e)}'
        }), 500


@api_bp.route('/db/analyze/relationships', methods=['GET'])
def analyze_db_relationships():
    """分析表间关系"""
    try:
        relationships = db_structure_analyzer.analyze_relationships()
        return jsonify({
            'success': True,
            'data': relationships
        })
    except Exception as e:
        logger.error(f"分析表间关系失败: {str(e)}")
        return jsonify({
            'success': False,
            'error': f'分析表间关系失败: {str(e)}'
        }), 500


@api_bp.route('/db/enhance/full', methods=['POST'])
def run_full_enhancement():
    """运行完整的数据库关系强化"""
    try:
        result = db_relationship_enhancer.run_full_enhancement()
        return jsonify({
            'success': True,
            'message': '数据库关系强化完成',
            'data': result
        })
    except Exception as e:
        logger.error(f"数据库关系强化失败: {str(e)}")
        return jsonify({
            'success': False,
            'error': f'数据库关系强化失败: {str(e)}'
        }), 500


@api_bp.route('/db/enhance/timestamps', methods=['POST'])
def add_missing_timestamps():
    """添加缺失的时间戳字段"""
    try:
        result = db_relationship_enhancer.add_missing_timestamps()
        return jsonify({
            'success': True,
            'message': '时间戳字段添加完成',
            'data': result
        })
    except Exception as e:
        logger.error(f"添加时间戳字段失败: {str(e)}")
        return jsonify({
            'success': False,
            'error': f'添加时间戳字段失败: {str(e)}'
        }), 500


@api_bp.route('/db/enhance/indexes', methods=['POST'])
def add_default_indexes():
    """添加默认索引"""
    try:
        result = db_relationship_enhancer.add_default_indexes()
        return jsonify({
            'success': True,
            'message': '索引添加完成',
            'data': result
        })
    except Exception as e:
        logger.error(f"添加索引失败: {str(e)}")
        return jsonify({
            'success': False,
            'error': f'添加索引失败: {str(e)}'
        }), 500


@api_bp.route('/db/enhance/relationships', methods=['POST'])
def enhance_relationships():
    """强化表间关系"""
    try:
        result = db_relationship_enhancer.enhance_all_relationships()
        return jsonify({
            'success': True,
            'message': '关系强化完成',
            'data': result
        })
    except Exception as e:
        logger.error(f"关系强化失败: {str(e)}")
        return jsonify({
            'success': False,
            'error': f'关系强化失败: {str(e)}'
        }), 500


@api_bp.route('/db/link/create', methods=['POST'])
def create_data_link():
    """创建数据链路"""
    try:
        data = request.json
        source_table = data.get('source_table')
        source_id = data.get('source_id')
        target_table = data.get('target_table')
        target_id = data.get('target_id')
        link_type = data.get('link_type', 'reference')
        
        if not source_table or not target_table:
            return jsonify({
                'success': False,
                'error': '缺少必要参数'
            }), 400
        
        link_id = data_link_closure.create_link(source_table, source_id, target_table, target_id, link_type)
        return jsonify({
            'success': True,
            'message': '数据链路创建成功',
            'data': {'link_id': link_id}
        })
    except Exception as e:
        logger.error(f"创建数据链路失败: {str(e)}")
        return jsonify({
            'success': False,
            'error': f'创建数据链路失败: {str(e)}'
        }), 500


@api_bp.route('/db/link/verify', methods=['POST'])
def verify_data_link():
    """验证数据链路闭环"""
    try:
        data = request.json
        link_id = data.get('link_id')
        
        if not link_id:
            return jsonify({
                'success': False,
                'error': '缺少链路ID'
            }), 400
        
        result = data_link_closure.verify_closure(link_id)
        return jsonify({
            'success': result['success'],
            'data': result
        })
    except Exception as e:
        logger.error(f"验证数据链路失败: {str(e)}")
        return jsonify({
            'success': False,
            'error': f'验证数据链路失败: {str(e)}'
        }), 500


@api_bp.route('/db/link/all', methods=['GET'])
def get_all_links():
    """获取所有数据链路"""
    try:
        links = data_link_closure.get_all_links()
        return jsonify({
            'success': True,
            'data': {'links': links, 'count': len(links)}
        })
    except Exception as e:
        logger.error(f"获取数据链路失败: {str(e)}")
        return jsonify({
            'success': False,
            'error': f'获取数据链路失败: {str(e)}'
        }), 500


@api_bp.route('/db/link/verify-all', methods=['POST'])
def verify_all_links():
    """验证所有数据链路闭环"""
    try:
        result = data_link_closure.run_closure_verification()
        return jsonify({
            'success': True,
            'data': result
        })
    except Exception as e:
        logger.error(f"验证所有链路失败: {str(e)}")
        return jsonify({
            'success': False,
            'error': f'验证所有链路失败: {str(e)}'
        }), 500


@api_bp.route('/db/security/status', methods=['GET'])
def get_security_status():
    """获取数据库安全状态"""
    try:
        status = db_security_enhancer.get_security_status()
        return jsonify({
            'success': True,
            'data': status
        })
    except Exception as e:
        logger.error(f"获取安全状态失败: {str(e)}")
        return jsonify({
            'success': False,
            'error': f'获取安全状态失败: {str(e)}'
        }), 500


@api_bp.route('/db/security/report', methods=['GET'])
def generate_security_report():
    """生成数据库安全报告"""
    try:
        report = db_security_enhancer.generate_security_report()
        return jsonify({
            'success': True,
            'data': report
        })
    except Exception as e:
        logger.error(f"生成安全报告失败: {str(e)}")
        return jsonify({
            'success': False,
            'error': f'生成安全报告失败: {str(e)}'
        }), 500


@api_bp.route('/db/security/scan', methods=['POST'])
def scan_sensitive_data():
    """扫描敏感数据"""
    try:
        result = db_security_enhancer.scan_sensitive_data()
        return jsonify({
            'success': True,
            'data': result
        })
    except Exception as e:
        logger.error(f"扫描敏感数据失败: {str(e)}")
        return jsonify({
            'success': False,
            'error': f'扫描敏感数据失败: {str(e)}'
        }), 500


@api_bp.route('/db/security/sensitive-table', methods=['POST'])
def add_sensitive_table():
    """添加敏感表"""
    try:
        data = request.json
        table_name = data.get('table_name')
        
        if not table_name:
            return jsonify({
                'success': False,
                'error': '缺少表名'
            }), 400
        
        db_security_enhancer.add_sensitive_table(table_name)
        return jsonify({
            'success': True,
            'message': f'敏感表 {table_name} 添加成功'
        })
    except Exception as e:
        logger.error(f"添加敏感表失败: {str(e)}")
        return jsonify({
            'success': False,
            'error': f'添加敏感表失败: {str(e)}'
        }), 500


@api_bp.route('/db/security/encrypt-field', methods=['POST'])
def add_encrypted_field():
    """添加加密字段"""
    try:
        data = request.json
        table_name = data.get('table_name')
        field_name = data.get('field_name')
        
        if not table_name or not field_name:
            return jsonify({
                'success': False,
                'error': '缺少表名或字段名'
            }), 400
        
        db_security_enhancer.add_encrypted_field(table_name, field_name)
        return jsonify({
            'success': True,
            'message': f'加密字段 {table_name}.{field_name} 添加成功'
        })
    except Exception as e:
        logger.error(f"添加加密字段失败: {str(e)}")
        return jsonify({
            'success': False,
            'error': f'添加加密字段失败: {str(e)}'
        }), 500


@api_bp.route('/db/security/detect-injection', methods=['POST'])
def detect_sql_injection():
    """检测SQL注入"""
    try:
        data = request.json
        query = data.get('query')
        
        if not query:
            return jsonify({
                'success': False,
                'error': '缺少查询语句'
            }), 400
        
        result = db_security_enhancer.detect_sql_injection(query)
        return jsonify({
            'success': True,
            'data': result
        })
    except Exception as e:
        logger.error(f"检测SQL注入失败: {str(e)}")
        return jsonify({
            'success': False,
            'error': f'检测SQL注入失败: {str(e)}'
        }), 500