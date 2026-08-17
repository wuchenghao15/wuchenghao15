#!/usr/bin/env python3
from flask import Blueprint, jsonify, request
from app.middlewares.access_control import require_login, require_admin

ai_dashboard_api = Bluelogger.info('ai_dashboard_api', __name__)

@ai_dashboard_api.route('/api/ai/dashboard/overview', methods=['GET'])
@require_admin
def get_dashboard_overview():
    try:
        from app.ai.ai_professional_role import ai_professional_role_system
        from app.ai.ai_orchestrator import ai_orchestrator
        from app.ai.ai_skill_evolution import ai_skill_evolution_system
        from app.ai.ai_self_learning import self_learning_system
        
        overview = {
            'total_employees': 0,
            'active_employees': 0,
            'roles': {},
            'skill_distribution': {},
            'growth_cycles': 0,
            'knowledge_base_size': 0,
            'learning_hours': 0,
            'thinking_sessions': 0
        }

        summary = ai_professional_role_system.get_professional_summary()
        overview['total_employees'] = len(summary)
        
        for emp in summary:
            role_name = emp.get('role_name', '未分配')
            overview['roles'][role_name] = overview['roles'].get(role_name, 0) + 1
            overview['thinking_sessions'] += emp.get('total_thinking_sessions', 0)
            overview['learning_hours'] += emp.get('total_learning_hours', 0)
            overview['knowledge_base_size'] += emp.get('knowledge_base_size', 0)

        try:
            skill_stats = ai_skill_evolution_system.get_skill_distribution()
            overview['skill_distribution'] = skill_stats
        except:
            pass

        try:
            cycles = ai_orchestrator.get_growth_history('emp_001')
            overview['growth_cycles'] = len(cycles)
        except:
            pass

        try:
            self_learning_status = self_learning_system.get_status()
            overview['self_learning'] = {
                'is_running': self_learning_status.get('is_running', False),
                'learning_cycles': self_learning_status.get('learning_cycles', 0)
            }
        except:
            pass

        return jsonify({'success': True, 'data': overview})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@ai_dashboard_api.route('/api/ai/dashboard/employees', methods=['GET'])
@require_admin
def get_employees_list():
    try:
        from app.ai.ai_professional_role import ai_professional_role_system
        from app.ai.ai_orchestrator import ai_orchestrator
        
        employees = []
        summary = ai_professional_role_system.get_professional_summary()
        
        for emp in summary:
            emp_data = {
                'employee_id': emp.get('employee_id', ''),
                'employee_name': emp.get('employee_name', ''),
                'role_name': emp.get('role_name', ''),
                'total_thinking_sessions': emp.get('total_thinking_sessions', 0),
                'total_learning_hours': emp.get('total_learning_hours', 0),
                'knowledge_base_size': emp.get('knowledge_base_size', 0),
                'current_plan_progress': emp.get('current_plan_progress', 0),
                'last_activity': emp.get('last_activity', '')
            }
            
            try:
                cycles = ai_orchestrator.get_growth_history(emp['employee_id'])
                emp_data['growth_cycles'] = len(cycles)
            except:
                emp_data['growth_cycles'] = 0
            
            employees.append(emp_data)
        
        return jsonify({'success': True, 'data': employees})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@ai_dashboard_api.route('/api/ai/dashboard/employee/<employee_id>', methods=['GET'])
@require_admin
def get_employee_detail(employee_id):
    try:
        from app.ai.ai_professional_role import ai_professional_role_system
        from app.ai.ai_orchestrator import ai_orchestrator
        from app.ai.ai_skill_evolution import ai_skill_evolution_system
        
        detail = {}
        
        role_data = ai_professional_role_system.get_role(employee_id)
        if role_data['success']:
            detail['role'] = role_data
        else:
            return jsonify({'success': False, 'error': '员工不存在'}), 404
        
        growth_history = ai_orchestrator.get_growth_history(employee_id)
        detail['growth_history'] = growth_history
        
        try:
            skills = ai_skill_evolution_system.get_employee_skills(employee_id)
            detail['skills'] = skills
        except:
            detail['skills'] = []
        
        kb_result = ai_professional_role_system.get_knowledge_base(employee_id)
        detail['knowledge_base'] = kb_result
        
        plan_result = ai_professional_role_system.get_learning_plan(employee_id)
        detail['learning_plan'] = plan_result
        
        thinking_history = ai_professional_role_system.thinking_engine.get_thinking_history(employee_id)
        detail['thinking_history'] = thinking_history
        
        return jsonify({'success': True, 'data': detail})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@ai_dashboard_api.route('/api/ai/dashboard/growth/trigger', methods=['POST'])
@require_admin
def trigger_growth_cycle():
    try:
        from app.ai.ai_orchestrator import ai_orchestrator
        
        data = request.get_json() or {}
        employee_id = data.get('employee_id')
        employee_name = data.get('employee_name', '')
        current_skills = data.get('current_skills', {})
        
        if not employee_id:
            return jsonify({'success': False, 'error': '员工ID不能为空'}), 400
        
        result = ai_orchestrator.trigger_full_growth_cycle(employee_id, employee_name or f"员工{employee_id}",
        current_skills)
        return jsonify(result)
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@ai_dashboard_api.route('/api/ai/dashboard/growth/batch', methods=['POST'])
@require_admin
def trigger_batch_growth():
    try:
        from app.ai.ai_orchestrator import ai_orchestrator
        
        data = request.get_json() or {}
        employee_ids = data.get('employee_ids', [])
        
        if not employee_ids:
            return jsonify({'success': False, 'error': '员工ID列表不能为空'}), 400
        
        results = ai_orchestrator.trigger_batch_growth(employee_ids)
        return jsonify({'success': True, 'data': results})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@ai_dashboard_api.route('/api/ai/dashboard/stats', methods=['GET'])
@require_login
def get_stats():
    try:
        from app.ai.ai_professional_role import ai_professional_role_system
        
        summary = ai_professional_role_system.get_professional_summary()
        
        stats = {
            'total_employees': len(summary),
            'total_thinking_sessions': sum(e.get('total_thinking_sessions', 0) for e in summary),
            'total_learning_hours': sum(e.get('total_learning_hours', 0) for e in summary),
            'total_knowledge': sum(e.get('knowledge_base_size', 0) for e in summary),
            'avg_plan_progress': sum(e.get('current_plan_progress', 0) for e in summary) / max(len(summary), 1)
        }
        
        return jsonify({'success': True, 'data': stats})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@ai_dashboard_api.route('/api/ai/dashboard/roles', methods=['GET'])
@require_login
def get_role_stats():
    try:
        from app.ai.ai_professional_role import ai_professional_role_system
        
        roles = ai_professional_role_system.list_all_roles()
        summary = ai_professional_role_system.get_professional_summary()
        
        role_stats = {}
        for emp in summary:
            role_name = emp.get('role_name', '未分配')
            if role_name not in role_stats:
                role_stats[role_name] = {'count': 0, 'avg_progress': 0, 'thinking_sessions': 0}
            role_stats[role_name]['count'] += 1
            role_stats[role_name]['avg_progress'] += emp.get('current_plan_progress', 0)
            role_stats[role_name]['thinking_sessions'] += emp.get('total_thinking_sessions', 0)
        
        for role_name, stats in role_stats.items():
            stats['avg_progress'] = stats['avg_progress'] / stats['count']
        
        return jsonify({'success': True, 'data': {'roles_count': len(roles), 'role_stats': role_stats}})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500