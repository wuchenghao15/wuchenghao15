# -*- coding: utf-8 -*-
"""
AI员工主动运作系统API
"""

from flask import Blueprint, request, jsonify, session
import logging
from collections import defaultdict
from app.ai.proactive_ai_system import (
    proactive_ai_center,
    InitiativeLevel,
    TaskStatus,
    DiscoverySource
)
from app.utils.logging import logger

proactive_ai_api = Blueprint('proactive_ai_api', __name__)


@proactive_ai_api.route('/proactive-ai/status', methods=['GET'])
def get_system_status():
    """获取主动运作系统状态"""
    try:
        status = proactive_ai_center.get_system_status()
        return jsonify({
            'success': True,
            'data': status
        })
    except Exception as e:
        logger.error(f"获取主动AI系统状态失败: {e}")
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500


@proactive_ai_api.route('/proactive-ai/start', methods=['POST'])
def start_system():
    """启动主动运作系统"""
    try:
        data = request.get_json() or {}
        num_workers = data.get('num_workers', 3)
        
        proactive_ai_center.start(num_workers=num_workers)
        
        return jsonify({
            'success': True,
            'message': 'AI员工主动运作系统已启动',
            'data': {
                'num_workers': num_workers
            }
        })
    except Exception as e:
        logger.error(f"启动主动AI系统失败: {e}")
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500


@proactive_ai_api.route('/proactive-ai/stop', methods=['POST'])
def stop_system():
    """停止主动运作系统"""
    try:
        proactive_ai_center.stop()
        
        return jsonify({
            'success': True,
            'message': 'AI员工主动运作系统已停止'
        })
    except Exception as e:
        logger.error(f"停止主动AI系统失败: {e}")
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500


@proactive_ai_api.route('/proactive-ai/initiative-level', methods=['GET'])
def get_initiative_level():
    """获取主动性等级"""
    try:
        levels = [
            {'level': 'passive', 'name': '被动', 'description': '只在触发时工作'},
            {'level': 'reactive', 'name': '反应', 'description': '对问题快速响应'},
            {'level': 'proactive', 'name': '主动', 'description': '主动发现问题'},
            {'level': 'self_driven', 'name': '自驱', 'description': '自主规划和执行'},
            {'level': 'autonomous', 'name': '自主', 'description': '完全自主决策'}
        ]
        
        current_level = proactive_ai_center._initiative_level.value
        
        return jsonify({
            'success': True,
            'data': {
                'current_level': current_level,
                'available_levels': levels
            }
        })
    except Exception as e:
        logger.error(f"获取主动性等级失败: {e}")
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500


@proactive_ai_api.route('/proactive-ai/initiative-level', methods=['PUT'])
def set_initiative_level():
    """设置主动性等级"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({
                'success': False,
                'message': '缺少数据'
            }), 400
        
        level_str = data.get('level', 'proactive')
        
        level_map = {
            'passive': InitiativeLevel.PASSIVE,
            'reactive': InitiativeLevel.REACTIVE,
            'proactive': InitiativeLevel.PROACTIVE,
            'self_driven': InitiativeLevel.SELF_DRIVEN,
            'autonomous': InitiativeLevel.AUTONOMOUS
        }
        
        level = level_map.get(level_str)
        if not level:
            return jsonify({
                'success': False,
                'message': f'无效的主动性等级: {level_str}'
            }), 400
        
        proactive_ai_center.set_initiative_level(level)
        
        return jsonify({
            'success': True,
            'message': f'主动性等级已设置为: {level_str}',
            'data': {
                'level': level_str
            }
        })
    except Exception as e:
        logger.error(f"设置主动性等级失败: {e}")
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500


@proactive_ai_api.route('/proactive-ai/discovery/trigger', methods=['POST'])
def trigger_discovery():
    """触发手动发现"""
    try:
        tasks = proactive_ai_center.trigger_manual_discovery()
        
        return jsonify({
            'success': True,
            'message': f'发现 {len(tasks)} 个新任务',
            'data': {
                'tasks_count': len(tasks),
                'tasks': tasks[:10]
            }
        })
    except Exception as e:
        logger.error(f"触发发现失败: {e}")
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500


@proactive_ai_api.route('/proactive-ai/discovery/modules', methods=['GET'])
def get_discovery_modules():
    """获取发现模块列表"""
    try:
        discovery_stats = proactive_ai_center.discovery_engine.get_discovery_stats()
        
        modules_info = [
            {'name': 'error_pattern_analysis', 'description': '错误模式分析', 'source': 'error_log'},
            {'name': 'performance_anomaly', 'description': '性能异常检测', 'source': 'performance'},
            {'name': 'user_behavior_pattern', 'description': '用户行为模式', 'source': 'user_behavior'},
            {'name': 'system_health_monitor', 'description': '系统健康监控', 'source': 'system_health'},
            {'name': 'data_integrity_check', 'description': '数据完整性检查', 'source': 'data_anomaly'},
            {'name': 'optimization_opportunity', 'description': '优化机会发现', 'source': 'optimization'},
            {'name': 'knowledge_gap_detector', 'description': '知识缺口检测', 'source': 'knowledge_gap'},
            {'name': 'predictive_maintenance', 'description': '预测性维护', 'source': 'predictive'}
        ]
        
        return jsonify({
            'success': True,
            'data': {
                'modules': modules_info,
                'total': len(modules_info),
                'discovery_stats': discovery_stats
            }
        })
    except Exception as e:
        logger.error(f"获取发现模块失败: {e}")
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500


@proactive_ai_api.route('/proactive-ai/tasks', methods=['GET'])
def get_task_list():
    """获取任务列表"""
    try:
        status = request.args.get('status')
        limit = int(request.args.get('limit', 50))
        
        tasks = proactive_ai_center.get_task_list(status, limit)
        
        return jsonify({
            'success': True,
            'data': {
                'tasks': tasks,
                'total': len(tasks)
            }
        })
    except Exception as e:
        logger.error(f"获取任务列表失败: {e}")
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500


@proactive_ai_api.route('/proactive-ai/tasks', methods=['POST'])
def create_task():
    """创建自定义任务"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({
                'success': False,
                'message': '缺少数据'
            }), 400
        
        title = data.get('title')
        description = data.get('description', '')
        priority = data.get('priority', 'medium')
        category = data.get('category', 'custom')
        required_skills = data.get('required_skills', [])
        
        if not title:
            return jsonify({
                'success': False,
                'message': '任务标题不能为空'
            }), 400
        
        task = proactive_ai_center.create_custom_task(
            title=title,
            description=description,
            priority=priority,
            category=category,
            required_skills=required_skills
        )
        
        return jsonify({
            'success': True,
            'message': '任务已创建',
            'data': task
        })
    except Exception as e:
        logger.error(f"创建任务失败: {e}")
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500


@proactive_ai_api.route('/proactive-ai/tasks/<task_id>', methods=['GET'])
def get_task_detail(task_id):
    """获取任务详情"""
    try:
        tasks = proactive_ai_center.get_task_list(limit=500)
        task = next((t for t in tasks if t.get('task_id') == task_id), None)
        
        if not task:
            return jsonify({
                'success': False,
                'message': '任务不存在'
            }), 404
        
        return jsonify({
            'success': True,
            'data': task
        })
    except Exception as e:
        logger.error(f"获取任务详情失败: {e}")
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500


@proactive_ai_api.route('/proactive-ai/scheduler/stats', methods=['GET'])
def get_scheduler_stats():
    """获取调度器统计"""
    try:
        stats = proactive_ai_center.task_scheduler.get_queue_stats()
        
        return jsonify({
            'success': True,
            'data': stats
        })
    except Exception as e:
        logger.error(f"获取调度器统计失败: {e}")
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500


@proactive_ai_api.route('/proactive-ai/learning/stats', methods=['GET'])
def get_learning_stats():
    """获取学习统计"""
    try:
        stats = proactive_ai_center.learning_engine.get_knowledge_stats()
        suggestions = proactive_ai_center.learning_engine.generate_improvement_suggestions()
        
        return jsonify({
            'success': True,
            'data': {
                'stats': stats,
                'improvement_suggestions': suggestions
            }
        })
    except Exception as e:
        logger.error(f"获取学习统计失败: {e}")
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500


@proactive_ai_api.route('/proactive-ai/learning/skills', methods=['GET'])
def get_skill_levels():
    """获取技能水平"""
    try:
        skills = proactive_ai_center.learning_engine.get_all_skills()
        
        # 排序
        sorted_skills = sorted(skills.items(), key=lambda x: x[1], reverse=True)
        
        return jsonify({
            'success': True,
            'data': {
                'skills': dict(sorted_skills),
                'total_categories': len(skills),
                'average_level': sum(skills.values()) / len(skills) if skills else 0
            }
        })
    except Exception as e:
        logger.error(f"获取技能水平失败: {e}")
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500


@proactive_ai_api.route('/proactive-ai/learning/rate', methods=['PUT'])
def set_learning_rate():
    """设置学习率"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({
                'success': False,
                'message': '缺少数据'
            }), 400
        
        rate = data.get('rate', 0.1)
        
        if not isinstance(rate, (int, float)) or rate <= 0 or rate > 1:
            return jsonify({
                'success': False,
                'message': '学习率必须在0到1之间'
            }), 400
        
        proactive_ai_center.learning_engine.set_learning_rate(rate)
        
        return jsonify({
            'success': True,
            'message': f'学习率已设置为: {rate}',
            'data': {
                'learning_rate': rate
            }
        })
    except Exception as e:
        logger.error(f"设置学习率失败: {e}")
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500


@proactive_ai_api.route('/proactive-ai/sources', methods=['GET'])
def get_discovery_sources():
    """获取发现来源列表"""
    try:
        sources = [
            {'source': 'error_log', 'name': '错误日志', 'description': '从错误日志中发现问题'},
            {'source': 'performance', 'name': '性能指标', 'description': '从性能指标中发现异常'},
            {'source': 'user_behavior', 'name': '用户行为', 'description': '分析用户行为模式'},
            {'source': 'system_health', 'name': '系统健康', 'description': '监控系统健康状态'},
            {'source': 'data_anomaly', 'name': '数据异常', 'description': '检测数据异常情况'},
            {'source': 'security_alert', 'name': '安全告警', 'description': '安全事件分析'},
            {'source': 'pattern_analysis', 'name': '模式分析', 'description': '深度模式分析'},
            {'source': 'predictive', 'name': '预测性', 'description': '预测性发现'},
            {'source': 'knowledge_gap', 'name': '知识缺口', 'description': '发现知识和能力缺口'},
            {'source': 'optimization', 'name': '优化机会', 'description': '发现优化机会'}
        ]
        
        return jsonify({
            'success': True,
            'data': {
                'sources': sources,
                'total': len(sources)
            }
        })
    except Exception as e:
        logger.error(f"获取发现来源失败: {e}")
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500


@proactive_ai_api.route('/proactive-ai/test', methods=['GET'])
def test_proactive_system():
    """测试主动AI系统"""
    try:
        # 系统状态
        status = proactive_ai_center.get_system_status()
        
        # 触发一次发现
        discovered = proactive_ai_center.trigger_manual_discovery()
        
        # 技能水平
        skills = proactive_ai_center.learning_engine.get_all_skills()
        
        return jsonify({
            'success': True,
            'data': {
                'system_running': status['running'],
                'initiative_level': status['initiative_level'],
                'discovered_tasks': len(discovered),
                'skill_categories': len(skills),
                'discovery_modules': len(status['discovery'].get('modules', [])),
                'queue_stats': status['scheduler']
            }
        })
    except Exception as e:
        logger.error(f"测试主动AI系统失败: {e}")
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500


@proactive_ai_api.route('/proactive-ai/dashboard', methods=['GET'])
def get_dashboard_data():
    """获取仪表盘数据"""
    try:
        status = proactive_ai_center.get_system_status()
        tasks = proactive_ai_center.get_task_list(limit=20)
        
        # 统计任务状态分布
        status_counts = defaultdict(int)
        for task in tasks:
            status_counts[task.get('status', 'unknown')] += 1
        
        return jsonify({
            'success': True,
            'data': {
                'system': {
                    'running': status['running'],
                    'initiative_level': status['initiative_level'],
                    'uptime_seconds': status.get('uptime_seconds')
                },
                'tasks': {
                    'queued': status['scheduler'].get('queued', 0),
                    'active': status['scheduler'].get('active', 0),
                    'completed_today': status['scheduler'].get('completed_today', 0),
                    'failed_today': status['scheduler'].get('failed_today', 0),
                    'status_distribution': dict(status_counts)
                },
                'discovery': {
                    'modules_count': status['discovery'].get('modules_count', 0),
                    'history_count': status['discovery'].get('history_count', 0)
                },
                'learning': {
                    'knowledge_entries': status['learning'].get('knowledge_entries', 0),
                    'skill_categories': len(status['learning'].get('skills', {})),
                    'suggestions': status.get('improvement_suggestions', [])
                },
                'recent_tasks': tasks[:10]
            }
        })
    except Exception as e:
        logger.error(f"获取仪表盘数据失败: {e}")
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500
