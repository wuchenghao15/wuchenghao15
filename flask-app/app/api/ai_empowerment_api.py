# -*- coding: utf-8 -*-
"""
统一AI赋能API蓝图
功能：
1. AI系统状态 - 获取所有AI子系统的状态概览
2. 自学习系统API - 系统自学习和优化相关接口
3. 技能进化API - AI员工技能进化相关接口
4. AI能力评估 - 综合评估AI系统能力
5. AI任务编排 - 编排多个AI服务完成复杂任务
6. AI洞察中心 - 汇总所有AI系统生成的洞察
"""

from flask import Blueprint, jsonify, request, session
from app.middlewares.permission_decorators import require_login, require_admin
from app.ai.self_learning_system import self_learning_system
from app.ai.ai_skill_evolution import ai_skill_evolution_system
from app.ai.student_learning_optimizer import student_learning_optimizer
from app.ai.question_bank_ai import QuestionBankAIAssistant
from app.ai.maintenance_ai import maintenance_ai
from app.utils.api_response import APIResponse
import sqlite3
import logging
import os
import json
from datetime import datetime

logger = logging.getLogger(__name__)

ai_empowerment_api = Blueprint('ai_empowerment_api', __name__, url_prefix='/api/ai/empowerment')

DB_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), 'app.db')

@ai_empowerment_api.route('/status', methods=['GET'])
def get_ai_system_status():
    """获取AI系统状态概览"""
    try:
        status = {
            'self_learning': {
                'name': '自学习系统',
                'status': self_learning_system._is_learning,
                'patterns_detected': len(self_learning_system.patterns),
                'insights_generated': len(self_learning_system.insights),
                'learning_cycles': len(self_learning_system.learning_history)
            },
            'skill_evolution': {
                'name': '技能进化系统',
                'status': ai_skill_evolution_system._is_evolving,
                'total_employees': len(ai_skill_evolution_system.employees),
                'evolution_stats': ai_skill_evolution_system.get_evolution_stats()
            },
            'learning_optimizer': {
                'name': '学习优化器',
                'status': 'running',
                'features': ['学情诊断', '学习推荐', '智能出题', '作业批改', '效果预测']
            },
            'question_bank_ai': {
                'name': '题库AI',
                'status': 'running',
                'features': ['题目优化', '难度分析', '标签分类', '自动出题']
            },
            'maintenance_ai': {
                'name': '维护AI',
                'status': 'running',
                'features': ['系统维护', '数据库清理', '日志管理', '健康检查']
            },
            'proactive_ai': {
                'name': '主动AI系统',
                'status': 'running',
                'features': ['主动监控', '智能预警', '自动修复']
            }
        }

        return jsonify({
            'success': True,
            'data': status,
            'message': 'AI系统状态获取成功'
        })
    except Exception as e:
        logger.error(f"[AI赋能API] 获取AI系统状态失败: {str(e)}")
        return jsonify({
            'success': False,
            'message': f'获取AI系统状态失败: {str(e)}'
        }), 500

@ai_empowerment_api.route('/self_learning/start', methods=['POST'])
def start_self_learning():
    """启动自学习系统"""
    try:
        self_learning_system.start_learning()
        return jsonify({
            'success': True,
            'message': '自学习系统已启动'
        })
    except Exception as e:
        logger.error(f"[AI赋能API] 启动自学习系统失败: {str(e)}")
        return jsonify({
            'success': False,
            'message': f'启动自学习系统失败: {str(e)}'
        }), 500

@ai_empowerment_api.route('/self_learning/stop', methods=['POST'])
def stop_self_learning():
    """停止自学习系统"""
    try:
        self_learning_system.stop_learning()
        return jsonify({
            'success': True,
            'message': '自学习系统已停止'
        })
    except Exception as e:
        logger.error(f"[AI赋能API] 停止自学习系统失败: {str(e)}")
        return jsonify({
            'success': False,
            'message': f'停止自学习系统失败: {str(e)}'
        }), 500

@ai_empowerment_api.route('/self_learning/analyze', methods=['GET'])
def analyze_system():
    """分析系统状态"""
    try:
        analysis = self_learning_system.analyze_system()
        return jsonify({
            'success': True,
            'data': analysis,
            'message': '系统分析完成'
        })
    except Exception as e:
        logger.error(f"[AI赋能API] 系统分析失败: {str(e)}")
        return jsonify({
            'success': False,
            'message': f'系统分析失败: {str(e)}'
        }), 500

@ai_empowerment_api.route('/self_learning/insights', methods=['GET'])
def get_insights():
    """获取系统洞察"""
    try:
        limit = int(request.args.get('limit', 10))
        level = request.args.get('level')
        
        insights = self_learning_system.get_insights(limit=limit, level=level)
        return jsonify({
            'success': True,
            'data': insights,
            'count': len(insights),
            'message': '洞察获取成功'
        })
    except Exception as e:
        logger.error(f"[AI赋能API] 获取洞察失败: {str(e)}")
        return jsonify({
            'success': False,
            'message': f'获取洞察失败: {str(e)}'
        }), 500

@ai_empowerment_api.route('/self_learning/patterns', methods=['GET'])

def get_patterns():
    """获取检测到的模式"""
    try:
        limit = int(request.args.get('limit', 10))
        
        patterns = self_learning_system.get_patterns(limit=limit)
        return jsonify({
            'success': True,
            'data': patterns,
            'count': len(patterns),
            'message': '模式获取成功'
        })
    except Exception as e:
        logger.error(f"[AI赋能API] 获取模式失败: {str(e)}")
        return jsonify({
            'success': False,
            'message': f'获取模式失败: {str(e)}'
        }), 500

@ai_empowerment_api.route('/self_learning/apply_insight', methods=['POST'])

def apply_insight():
    """应用洞察建议"""
    try:
        data = request.get_json() or {}
        insight_id = data.get('insight_id')
        
        if not insight_id:
            return jsonify({'success': False, 'message': '洞察ID不能为空'}), 400
        
        result = self_learning_system.apply_insight(insight_id)
        
        if result:
            return jsonify({
                'success': True,
                'message': '洞察已应用'
            })
        else:
            return jsonify({
                'success': False,
                'message': '应用洞察失败，洞察不存在'
            }), 404
    except Exception as e:
        logger.error(f"[AI赋能API] 应用洞察失败: {str(e)}")
        return jsonify({
            'success': False,
            'message': f'应用洞察失败: {str(e)}'
        }), 500

@ai_empowerment_api.route('/self_learning/learn', methods=['POST'])

def learn_from_data():
    """从外部数据学习"""
    try:
        data = request.get_json() or {}
        
        if not data:
            return jsonify({'success': False, 'message': '学习数据不能为空'}), 400
        
        self_learning_system.learn_from_data(data)
        
        return jsonify({
            'success': True,
            'message': '学习完成'
        })
    except Exception as e:
        logger.error(f"[AI赋能API] 学习失败: {str(e)}")
        return jsonify({
            'success': False,
            'message': f'学习失败: {str(e)}'
        }), 500

@ai_empowerment_api.route('/skill_evolution/start', methods=['POST'])

def start_skill_evolution():
    """启动技能进化系统"""
    try:
        ai_skill_evolution_system.start_evolution()
        return jsonify({
            'success': True,
            'message': '技能进化系统已启动'
        })
    except Exception as e:
        logger.error(f"[AI赋能API] 启动技能进化系统失败: {str(e)}")
        return jsonify({
            'success': False,
            'message': f'启动技能进化系统失败: {str(e)}'
        }), 500

@ai_empowerment_api.route('/skill_evolution/stop', methods=['POST'])

def stop_skill_evolution():
    """停止技能进化系统"""
    try:
        ai_skill_evolution_system.stop_evolution()
        return jsonify({
            'success': True,
            'message': '技能进化系统已停止'
        })
    except Exception as e:
        logger.error(f"[AI赋能API] 停止技能进化系统失败: {str(e)}")
        return jsonify({
            'success': False,
            'message': f'停止技能进化系统失败: {str(e)}'
        }), 500

@ai_empowerment_api.route('/skill_evolution/employees', methods=['GET'])

def get_employees_evolution():
    """获取所有员工进化信息"""
    try:
        employees = ai_skill_evolution_system.get_all_employees_evolution()
        return jsonify({
            'success': True,
            'data': employees,
            'count': len(employees),
            'message': '员工进化信息获取成功'
        })
    except Exception as e:
        logger.error(f"[AI赋能API] 获取员工进化信息失败: {str(e)}")
        return jsonify({
            'success': False,
            'message': f'获取员工进化信息失败: {str(e)}'
        }), 500

@ai_empowerment_api.route('/skill_evolution/employees/<employee_id>', methods=['GET'])

def get_employee_evolution(employee_id):
    """获取单个员工进化信息"""
    try:
        employee = ai_skill_evolution_system.get_employee_evolution(employee_id)
        
        if not employee:
            return jsonify({'success': False, 'message': '员工不存在'}), 404
        
        return jsonify({
            'success': True,
            'data': employee,
            'message': '员工进化信息获取成功'
        })
    except Exception as e:
        logger.error(f"[AI赋能API] 获取员工进化信息失败: {str(e)}")
        return jsonify({
            'success': False,
            'message': f'获取员工进化信息失败: {str(e)}'
        }), 500

@ai_empowerment_api.route('/skill_evolution/employees/<employee_id>/suggestions', methods=['GET'])

def get_employee_suggestions(employee_id):
    """获取员工改进建议"""
    try:
        suggestions = ai_skill_evolution_system.get_improvement_suggestions(employee_id)
        return jsonify({
            'success': True,
            'data': suggestions,
            'count': len(suggestions),
            'message': '改进建议获取成功'
        })
    except Exception as e:
        logger.error(f"[AI赋能API] 获取员工改进建议失败: {str(e)}")
        return jsonify({
            'success': False,
            'message': f'获取员工改进建议失败: {str(e)}'
        }), 500

@ai_empowerment_api.route('/skill_evolution/top_employees', methods=['GET'])

def get_top_employees():
    """获取顶尖员工"""
    try:
        limit = int(request.args.get('limit', 5))
        by = request.args.get('by', 'experience')
        
        top_employees = ai_skill_evolution_system.get_top_employees(limit=limit, by=by)
        return jsonify({
            'success': True,
            'data': top_employees,
            'count': len(top_employees),
            'message': '顶尖员工获取成功'
        })
    except Exception as e:
        logger.error(f"[AI赋能API] 获取顶尖员工失败: {str(e)}")
        return jsonify({
            'success': False,
            'message': f'获取顶尖员工失败: {str(e)}'
        }), 500

@ai_empowerment_api.route('/skill_evolution/record_task', methods=['POST'])

def record_employee_task():
    """记录员工任务结果"""
    try:
        data = request.get_json() or {}
        
        employee_id = data.get('employee_id')
        task_result = data.get('task_result')
        
        if not employee_id or not task_result:
            return jsonify({'success': False, 'message': '员工ID和任务结果不能为空'}), 400
        
        ai_skill_evolution_system.record_employee_task(employee_id, task_result)
        
        return jsonify({
            'success': True,
            'message': '任务记录成功'
        })
    except Exception as e:
        logger.error(f"[AI赋能API] 记录员工任务失败: {str(e)}")
        return jsonify({
            'success': False,
            'message': f'记录员工任务失败: {str(e)}'
        }), 500

@ai_empowerment_api.route('/skill_evolution/simulate_training', methods=['POST'])

def simulate_training():
    """模拟技能训练"""
    try:
        data = request.get_json() or {}
        
        employee_id = data.get('employee_id')
        skill_name = data.get('skill_name')
        intensity = float(data.get('intensity', 1.0))
        
        if not employee_id or not skill_name:
            return jsonify({'success': False, 'message': '员工ID和技能名称不能为空'}), 400
        
        result = ai_skill_evolution_system.simulate_training(employee_id, skill_name, intensity)
        
        if result['success']:
            return jsonify({
                'success': True,
                'data': result,
                'message': '训练完成'
            })
        else:
            return jsonify({
                'success': False,
                'message': result.get('message', '训练失败')
            }), 404
    except Exception as e:
        logger.error(f"[AI赋能API] 模拟训练失败: {str(e)}")
        return jsonify({
            'success': False,
            'message': f'模拟训练失败: {str(e)}'
        }), 500

@ai_empowerment_api.route('/skill_evolution/stats', methods=['GET'])

def get_evolution_stats():
    """获取进化统计"""
    try:
        stats = ai_skill_evolution_system.get_evolution_stats()
        return jsonify({
            'success': True,
            'data': stats,
            'message': '进化统计获取成功'
        })
    except Exception as e:
        logger.error(f"[AI赋能API] 获取进化统计失败: {str(e)}")
        return jsonify({
            'success': False,
            'message': f'获取进化统计失败: {str(e)}'
        }), 500

@ai_empowerment_api.route('/assessment', methods=['GET'])

def ai_capability_assessment():
    """AI能力综合评估"""
    try:
        assessment = {
            'overall_score': 0,
            'sub_systems': [],
            'recommendations': []
        }
        
        scores = []
        
        sl_status = self_learning_system.analyze_system()
        sl_score = 80 if sl_status['status'] == 'running' else 40
        scores.append(sl_score)
        assessment['sub_systems'].append({
            'name': '自学习系统',
            'score': sl_score,
            'status': sl_status['status'],
            'details': {
                'patterns_detected': sl_status['patterns_detected'],
                'insights_generated': sl_status['insights_generated']
            }
        })
        
        se_stats = ai_skill_evolution_system.get_evolution_stats()
        se_score = min(100, se_stats['total_employees'] * 5 + se_stats.get('avg_success_rate', 0) * 0.5)
        scores.append(se_score)
        assessment['sub_systems'].append({
            'name': '技能进化系统',
            'score': round(se_score, 1),
            'status': 'running' if ai_skill_evolution_system._is_evolving else 'stopped',
            'details': {
                'total_employees': se_stats['total_employees'],
                'avg_success_rate': se_stats.get('avg_success_rate', 0),
                'top_stage': se_stats.get('top_stage', 0)
            }
        })
        
        assessment['overall_score'] = round(sum(scores) / len(scores), 1)
        
        if assessment['overall_score'] >= 80:
            assessment['level'] = '优秀'
            assessment['recommendations'] = ['系统AI能力优秀，建议继续扩展新功能', '考虑增加AI员工数量和类型']
        elif assessment['overall_score'] >= 60:
            assessment['level'] = '良好'
            assessment['recommendations'] = ['系统AI能力良好，建议优化薄弱环节', '增加自学习系统的运行频率']
        else:
            assessment['level'] = '需要改进'
            assessment['recommendations'] = ['建议检查各AI子系统状态', '启动自学习和技能进化系统']
        
        return jsonify({
            'success': True,
            'data': assessment,
            'message': 'AI能力评估完成'
        })
    except Exception as e:
        logger.error(f"[AI赋能API] AI能力评估失败: {str(e)}")
        return jsonify({
            'success': False,
            'message': f'AI能力评估失败: {str(e)}'
        }), 500

@ai_empowerment_api.route('/insights_center', methods=['GET'])

def insights_center():
    """AI洞察中心 - 汇总所有AI系统生成的洞察"""
    try:
        insights = []
        
        sl_insights = self_learning_system.get_insights(limit=5)
        for insight in sl_insights:
            insights.append({
                'source': '自学习系统',
                **insight
            })
        
        se_stats = ai_skill_evolution_system.get_evolution_stats()
        if se_stats.get('avg_success_rate', 0) < 70:
            insights.append({
                'source': '技能进化系统',
                'insight_type': 'ai_empowerment',
                'message': f'AI员工平均成功率 {se_stats["avg_success_rate"]}%，低于70%阈值',
                'level': 'high',
                'recommendation': '建议优化AI员工配置，增加训练任务'
            })
        
        insights.sort(key=lambda x: x.get('created_at', ''), reverse=True)
        
        return jsonify({
            'success': True,
            'data': insights[:10],
            'count': len(insights),
            'message': '洞察中心数据获取成功'
        })
    except Exception as e:
        logger.error(f"[AI赋能API] 洞察中心获取失败: {str(e)}")
        return jsonify({
            'success': False,
            'message': f'洞察中心获取失败: {str(e)}'
        }), 500

@ai_empowerment_api.route('/task_orchestration', methods=['POST'])

def task_orchestration():
    """AI任务编排 - 编排多个AI服务完成复杂任务"""
    try:
        data = request.get_json() or {}
        tasks = data.get('tasks', [])
        
        if not tasks:
            return jsonify({'success': False, 'message': '任务列表不能为空'}), 400
        
        results = []
        
        for task in tasks:
            task_type = task.get('type')
            task_data = task.get('data', {})
            
            result = {
                'task_type': task_type,
                'status': 'processing',
                'result': None
            }
            
            try:
                if task_type == 'learning_analysis':
                    student_id = task_data.get('student_id')
                    if student_id:
                        analysis = student_learning_optimizer.analyze_student_performance(student_id)
                        result['status'] = 'success'
                        result['result'] = analysis
                
                elif task_type == 'question_generation':
                    count = task_data.get('count', 5)
                    difficulty = task_data.get('difficulty', 'medium')
                    questions = QuestionBankAIAssistant.generate_questions(count, difficulty)
                    result['status'] = 'success'
                    result['result'] = {'generated_count': len(questions), 'difficulty': difficulty}
                
                elif task_type == 'system_maintenance':
                    maintenance_result = maintenance_ai.run_maintenance()
                    result['status'] = 'success'
                    result['result'] = maintenance_result
                
                elif task_type == 'health_check':
                    health = maintenance_ai.check_health()
                    result['status'] = 'success'
                    result['result'] = health
                
                elif task_type == 'skill_training':
                    employee_id = task_data.get('employee_id')
                    skill_name = task_data.get('skill_name')
                    training_result = ai_skill_evolution_system.simulate_training(employee_id, skill_name)
                    result['status'] = 'success' if training_result['success'] else 'failed'
                    result['result'] = training_result
                
                elif task_type == 'pattern_detection':
                    self_learning_system.detect_patterns()
                    patterns = self_learning_system.get_patterns(limit=5)
                    result['status'] = 'success'
                    result['result'] = {'patterns_found': len(patterns)}
                
                else:
                    result['status'] = 'failed'
                    result['result'] = {'error': f'未知任务类型: {task_type}'}
                
            except Exception as e:
                result['status'] = 'failed'
                result['result'] = {'error': str(e)}
            
            results.append(result)
        
        success_count = sum(1 for r in results if r['status'] == 'success')
        
        return jsonify({
            'success': True,
            'data': results,
            'summary': {
                'total_tasks': len(tasks),
                'success_count': success_count,
                'fail_count': len(tasks) - success_count,
                'success_rate': round(success_count / len(tasks) * 100, 1)
            },
            'message': '任务编排执行完成'
        })
    except Exception as e:
        logger.error(f"[AI赋能API] 任务编排失败: {str(e)}")
        return jsonify({
            'success': False,
            'message': f'任务编排失败: {str(e)}'
        }), 500

@ai_empowerment_api.route('/knowledge_summary', methods=['GET'])

def knowledge_summary():
    """获取知识库摘要"""
    try:
        summary = {
            'self_learning': self_learning_system.get_knowledge_summary(),
            'skill_evolution': {
                'skill_levels': {k: v for k, v in ai_skill_evolution_system.__class__.__dict__.get('SKILL_LEVELS', {}).items() if isinstance(k, int)},
                'thinking_focus_types': {k: v for k, v in ai_skill_evolution_system.__class__.__dict__.get('THINKING_FOCUS_TYPES', {}).items()}
            },
            'timestamp': datetime.now().isoformat()
        }
        
        return jsonify({
            'success': True,
            'data': summary,
            'message': '知识库摘要获取成功'
        })
    except Exception as e:
        logger.error(f"[AI赋能API] 获取知识库摘要失败: {str(e)}")
        return jsonify({
            'success': False,
            'message': f'获取知识库摘要失败: {str(e)}'
        }), 500

@ai_empowerment_api.route('/proactive_monitoring', methods=['GET'])

def proactive_monitoring():
    """主动AI监控"""
    try:
        monitoring_data = {
            'system_health': {},
            'alerts': [],
            'recommendations': []
        }
        
        try:
            health = maintenance_ai.check_health()
            monitoring_data['system_health'] = health
        except Exception:
            pass
        
        try:
            insights = self_learning_system.get_insights(limit=5, level='high')
            monitoring_data['alerts'] = insights
        except Exception:
            pass
        
        try:
            assessment = ai_capability_assessment().json
            if assessment.get('success'):
                monitoring_data['recommendations'] = assessment['data'].get('recommendations', [])
        except Exception:
            pass
        
        return jsonify({
            'success': True,
            'data': monitoring_data,
            'message': '主动监控完成'
        })
    except Exception as e:
        logger.error(f"[AI赋能API] 主动监控失败: {str(e)}")
        return jsonify({
            'success': False,
            'message': f'主动监控失败: {str(e)}'
        }), 500