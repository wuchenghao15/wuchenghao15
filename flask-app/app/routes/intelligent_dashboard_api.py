"""
智慧仪表盘 API v4.0.0
提供AI智能系统的完整监控和控制接口
"""

from flask import Blueprint, jsonify, request
from datetime import datetime
import logging

from app.services import (
    get_decision_engine,
    get_knowledge_graph,
    get_predictor,
    get_orchestrator,
    initialize_all_ai_services
)

logger = logging.getLogger(__name__)

intelligent_dashboard_bp = Blueprint('intelligent_dashboard', __name__)


@intelligent_dashboard_bp.route('/api/intelligent/overview', methods=['GET'])
def get_overview():
    """获取系统整体概览"""
    try:
        de = get_decision_engine()
        kg = get_knowledge_graph()
        pr = get_predictor()
        orc = get_orchestrator()
        
        decision_stats = de.get_performance_report()
        kg_stats = kg.get_statistics()
        prediction_stats = pr.get_prediction_statistics()
        orchestrator_stats = orc.get_statistics()
        
        overview = {
            'timestamp': datetime.now().isoformat(),
            'decision_engine': {
                'total_decisions': decision_stats.get('total_decisions', 0),
                'success_rate': decision_stats.get('success_rate', 0),
                'pending_decisions': decision_stats.get('pending', 0),
                'knowledge_base_size': decision_stats.get('knowledge_base_size', 0)
            },
            'knowledge_graph': {
                'total_nodes': kg_stats.get('total_nodes', 0),
                'total_edges': kg_stats.get('total_edges', 0),
                'node_types': kg_stats.get('node_types', {}),
                'total_tags': kg_stats.get('total_tags', 0)
            },
            'predictor': {
                'total_predictions': prediction_stats.get('total_predictions', 0),
                'active_series': prediction_stats.get('active_series', 0),
                'tracking_targets': prediction_stats.get('tracking_targets', 0)
            },
            'orchestrator': {
                'total_tasks': orchestrator_stats.get('tasks', {}).get('total', 0),
                'completed_tasks': orchestrator_stats.get('tasks', {}).get('completed', 0),
                'active_alerts': orchestrator_stats.get('alerts', {}).get('active', 0),
                'busy_workers': orchestrator_stats.get('workers', {}).get('busy', 0),
                'learning_records': orchestrator_stats.get('learning', {}).get('total_records', 0)
            }
        }
        
        return jsonify({
            'success': True,
            'data': overview
        })
    except Exception as e:
        logger.error(f"获取概览失败: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@intelligent_dashboard_bp.route('/api/intelligent/decisions', methods=['GET'])
def get_decisions():
    """获取决策记录"""
    try:
        de = get_decision_engine()
        pending = de.get_pending_decisions()
        
        return jsonify({
            'success': True,
            'data': {
                'pending_decisions': pending
            }
        })
    except Exception as e:
        logger.error(f"获取决策记录失败: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@intelligent_dashboard_bp.route('/api/intelligent/decisions/<decision_id>/execute', methods=['POST'])
def execute_decision(decision_id):
    """执行决策"""
    try:
        de = get_decision_engine()
        result = de.execute_decision(decision_id)
        
        return jsonify({
            'success': True,
            'data': result
        })
    except Exception as e:
        logger.error(f"执行决策失败: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@intelligent_dashboard_bp.route('/api/intelligent/knowledge/search', methods=['GET'])
def search_knowledge():
    """搜索知识图谱"""
    try:
        query = request.args.get('q', '')
        kg = get_knowledge_graph()
        
        results = kg.search(query)
        
        return jsonify({
            'success': True,
            'data': {
                'query': query,
                'results': [
                    {
                        'node': r.node.to_dict() if hasattr(r, 'node') else None,
                        'score': r.score,
                        'explanation': r.explanation
                    }
                    for r in results
                ]
            }
        })
    except Exception as e:
        logger.error(f"搜索知识失败: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@intelligent_dashboard_bp.route('/api/intelligent/knowledge/stats', methods=['GET'])
def get_knowledge_stats():
    """获取知识图谱统计"""
    try:
        kg = get_knowledge_graph()
        stats = kg.get_statistics()
        
        return jsonify({
            'success': True,
            'data': stats
        })
    except Exception as e:
        logger.error(f"获取知识统计失败: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@intelligent_dashboard_bp.route('/api/intelligent/predictions', methods=['GET'])
def get_predictions():
    """获取预测数据"""
    try:
        target = request.args.get('target', 'system')
        pr = get_predictor()
        
        predictions = pr.get_prediction_history(target, limit=20)
        
        return jsonify({
            'success': True,
            'data': {
                'target': target,
                'predictions': [
                    {
                        'type': p.prediction_type.value,
                        'value': p.predicted_value,
                        'confidence': p.confidence,
                        'trend': p.trend,
                        'recommendations': p.recommendations,
                        'created_at': p.created_at.isoformat()
                    }
                    for p in predictions
                ]
            }
        })
    except Exception as e:
        logger.error(f"获取预测数据失败: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@intelligent_dashboard_bp.route('/api/intelligent/alerts', methods=['GET'])
def get_alerts():
    """获取预警信息"""
    try:
        orc = get_orchestrator()
        alerts = orc.get_active_alerts()
        
        return jsonify({
            'success': True,
            'data': {
                'alerts': alerts
            }
        })
    except Exception as e:
        logger.error(f"获取预警信息失败: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@intelligent_dashboard_bp.route('/api/intelligent/alerts/<alert_id>/acknowledge', methods=['POST'])
def acknowledge_alert(alert_id):
    """确认预警"""
    try:
        orc = get_orchestrator()
        orc.acknowledge_alert(alert_id)
        
        return jsonify({
            'success': True,
            'message': '预警已确认'
        })
    except Exception as e:
        logger.error(f"确认预警失败: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@intelligent_dashboard_bp.route('/api/intelligent/alerts/<alert_id>/resolve', methods=['POST'])
def resolve_alert(alert_id):
    """解决预警"""
    try:
        orc = get_orchestrator()
        orc.resolve_alert(alert_id)
        
        return jsonify({
            'success': True,
            'message': '预警已解决'
        })
    except Exception as e:
        logger.error(f"解决预警失败: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@intelligent_dashboard_bp.route('/api/intelligent/tasks', methods=['GET'])
def get_tasks():
    """获取任务列表"""
    try:
        orc = get_orchestrator()
        stats = orc.get_statistics()
        
        return jsonify({
            'success': True,
            'data': stats.get('tasks', {})
        })
    except Exception as e:
        logger.error(f"获取任务列表失败: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@intelligent_dashboard_bp.route('/api/intelligent/tasks', methods=['POST'])
def submit_task():
    """提交新任务"""
    try:
        data = request.get_json()
        task_type = data.get('type', 'system_optimization')
        description = data.get('description', '通用任务')
        priority = data.get('priority', 5)
        
        orc = get_orchestrator()
        task = orc.submit_task(task_type, description, priority)
        
        return jsonify({
            'success': True,
            'data': {
                'task_id': task.task_id,
                'type': task.task_type,
                'description': task.description,
                'priority': task.priority,
                'status': task.status.value
            }
        })
    except Exception as e:
        logger.error(f"提交任务失败: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@intelligent_dashboard_bp.route('/api/intelligent/tasks/<task_id>', methods=['GET'])
def get_task_status(task_id):
    """获取任务状态"""
    try:
        orc = get_orchestrator()
        status = orc.get_task_status(task_id)
        
        if not status:
            return jsonify({'success': False, 'error': '任务不存在'}), 404
        
        return jsonify({
            'success': True,
            'data': status
        })
    except Exception as e:
        logger.error(f"获取任务状态失败: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@intelligent_dashboard_bp.route('/api/intelligent/insights', methods=['GET'])
def get_insights():
    """获取系统洞察"""
    try:
        de = get_decision_engine()
        insights = de.get_insights(limit=10)
        
        return jsonify({
            'success': True,
            'data': {
                'insights': insights
            }
        })
    except Exception as e:
        logger.error(f"获取洞察失败: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@intelligent_dashboard_bp.route('/api/intelligent/workers', methods=['GET'])
def get_workers():
    """获取AI员工状态"""
    try:
        orc = get_orchestrator()
        stats = orc.get_statistics()
        
        return jsonify({
            'success': True,
            'data': stats.get('workers', {})
        })
    except Exception as e:
        logger.error(f"获取AI员工状态失败: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@intelligent_dashboard_bp.route('/api/intelligent/initialize', methods=['POST'])
def initialize_services():
    """初始化所有AI服务"""
    try:
        data = request.get_json() or {}
        start_orchestrator = data.get('start_orchestrator', True)
        
        services = initialize_all_ai_services(start_orchestrator=start_orchestrator)
        
        return jsonify({
            'success': True,
            'message': 'AI智能服务初始化完成',
            'data': {
                'services_initialized': list(services.keys())
            }
        })
    except Exception as e:
        logger.error(f"初始化服务失败: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500
