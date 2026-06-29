# -*- coding: utf-8 -*-
"""
批量任务与自动规则API
提供批量任务委派和自动规则管理的RESTful接口
"""

from flask import Blueprint, request, jsonify
import logging

logger = logging.getLogger(__name__)

batch_auto_api = Blueprint('batch_auto_api', __name__)


def get_batch_manager():
    """获取批量任务管理器"""
    try:
        from app.agents.batch_task_manager import get_batch_manager
        return get_batch_manager()
    except Exception as e:
        logger.error(f"获取批量任务管理器失败: {e}")
        return None


def get_rule_engine():
    """获取规则引擎"""
    try:
        from app.agents.auto_rule_engine import get_rule_engine
        return get_rule_engine()
    except Exception as e:
        logger.error(f"获取规则引擎失败: {e}")
        return None


# ==================== 批量任务API ====================

@batch_auto_api.route('/api/batch/task', methods=['POST'])
def create_batch_task():
    """创建批量任务"""
    try:
        data = request.get_json() or {}
        agent_code = data.get('agent_code', 'batch_api')
        task_type = data.get('task_type', 'code_fix')
        tasks = data.get('tasks', [])
        employee_template = data.get('employee_template')
        
        if not tasks:
            return jsonify({'success': False, 'error': '任务列表不能为空'})
        
        manager = get_batch_manager()
        if not manager:
            return jsonify({'success': False, 'error': '批量任务管理器未初始化'})
        
        batch_id = manager.create_batch_task(agent_code, task_type, tasks)
        
        if not batch_id:
            return jsonify({'success': False, 'error': '创建批量任务失败'})
        
        if employee_template:
            dispatch_result = manager.dispatch_batch_task(batch_id, employee_template)
        else:
            dispatch_result = {'success': True, 'message': '批量任务已创建，等待分派'}
        
        return jsonify({
            'success': True,
            'batch_id': batch_id,
            'total_tasks': len(tasks),
            'dispatch_result': dispatch_result
        })
    
    except Exception as e:
        logger.error(f"创建批量任务失败: {e}")
        return jsonify({'success': False, 'error': str(e)})


@batch_auto_api.route('/api/batch/task/<batch_id>', methods=['GET'])
def get_batch_status(batch_id):
    """获取批量任务状态"""
    try:
        manager = get_batch_manager()
        if not manager:
            return jsonify({'success': False, 'error': '批量任务管理器未初始化'})
        
        result = manager.get_batch_status(batch_id)
        
        return jsonify(result)
    
    except Exception as e:
        logger.error(f"获取批量任务状态失败: {e}")
        return jsonify({'success': False, 'error': str(e)})


@batch_auto_api.route('/api/batch/task/<batch_id>/dispatch', methods=['POST'])
def dispatch_batch_task(batch_id):
    """分派批量任务"""
    try:
        data = request.get_json() or {}
        employee_template = data.get('employee_template')
        
        manager = get_batch_manager()
        if not manager:
            return jsonify({'success': False, 'error': '批量任务管理器未初始化'})
        
        result = manager.dispatch_batch_task(batch_id, employee_template)
        
        return jsonify(result)
    
    except Exception as e:
        logger.error(f"分派批量任务失败: {e}")
        return jsonify({'success': False, 'error': str(e)})


@batch_auto_api.route('/api/batch/tasks', methods=['GET'])
def get_all_batch_tasks():
    """获取所有批量任务"""
    try:
        status = request.args.get('status')
        
        manager = get_batch_manager()
        if not manager:
            return jsonify({'success': False, 'error': '批量任务管理器未初始化'})
        
        result = manager.get_all_batch_tasks(status)
        
        return jsonify(result)
    
    except Exception as e:
        logger.error(f"获取批量任务列表失败: {e}")
        return jsonify({'success': False, 'error': str(e)})


@batch_auto_api.route('/api/batch/task/<batch_id>/item/<item_id>', methods=['PUT'])
def update_batch_task_item(batch_id):
    """更新批量任务项结果"""
    try:
        data = request.get_json() or {}
        item_id = request.view_args.get('item_id')
        status = data.get('status')
        result = data.get('result')
        error = data.get('error')
        
        if not item_id or not status:
            return jsonify({'success': False, 'error': 'item_id和status不能为空'})
        
        manager = get_batch_manager()
        if not manager:
            return jsonify({'success': False, 'error': '批量任务管理器未初始化'})
        
        manager.update_task_item_result(item_id, status, result, error)
        
        return jsonify({'success': True, 'message': '任务项结果已更新'})
    
    except Exception as e:
        logger.error(f"更新任务项结果失败: {e}")
        return jsonify({'success': False, 'error': str(e)})


# ==================== 自动规则API ====================

@batch_auto_api.route('/api/rule', methods=['POST'])
def add_rule():
    """添加规则"""
    try:
        data = request.get_json() or {}
        name = data.get('name')
        conditions = data.get('conditions', [])
        actions = data.get('actions', [])
        priority = data.get('priority', 0)
        description = data.get('description', '')
        
        if not name:
            return jsonify({'success': False, 'error': '规则名称不能为空'})
        if not conditions:
            return jsonify({'success': False, 'error': '规则条件不能为空'})
        if not actions:
            return jsonify({'success': False, 'error': '规则动作不能为空'})
        
        engine = get_rule_engine()
        if not engine:
            return jsonify({'success': False, 'error': '规则引擎未初始化'})
        
        rule_id = engine.add_rule(name, conditions, actions, priority, description)
        
        if not rule_id:
            return jsonify({'success': False, 'error': '添加规则失败'})
        
        return jsonify({
            'success': True,
            'rule_id': rule_id,
            'message': '规则添加成功'
        })
    
    except Exception as e:
        logger.error(f"添加规则失败: {e}")
        return jsonify({'success': False, 'error': str(e)})


@batch_auto_api.route('/api/rule/<rule_id>', methods=['GET'])
def get_rule(rule_id):
    """获取规则"""
    try:
        engine = get_rule_engine()
        if not engine:
            return jsonify({'success': False, 'error': '规则引擎未初始化'})
        
        result = engine.get_rule(rule_id)
        
        return jsonify(result)
    
    except Exception as e:
        logger.error(f"获取规则失败: {e}")
        return jsonify({'success': False, 'error': str(e)})


@batch_auto_api.route('/api/rule/<rule_id>', methods=['PUT'])
def update_rule(rule_id):
    """更新规则"""
    try:
        data = request.get_json() or {}
        
        engine = get_rule_engine()
        if not engine:
            return jsonify({'success': False, 'error': '规则引擎未初始化'})
        
        result = engine.update_rule(rule_id, **data)
        
        return jsonify(result)
    
    except Exception as e:
        logger.error(f"更新规则失败: {e}")
        return jsonify({'success': False, 'error': str(e)})


@batch_auto_api.route('/api/rule/<rule_id>', methods=['DELETE'])
def delete_rule(rule_id):
    """删除规则"""
    try:
        engine = get_rule_engine()
        if not engine:
            return jsonify({'success': False, 'error': '规则引擎未初始化'})
        
        result = engine.delete_rule(rule_id)
        
        return jsonify(result)
    
    except Exception as e:
        logger.error(f"删除规则失败: {e}")
        return jsonify({'success': False, 'error': str(e)})


@batch_auto_api.route('/api/rules', methods=['GET'])
def get_all_rules():
    """获取所有规则"""
    try:
        engine = get_rule_engine()
        if not engine:
            return jsonify({'success': False, 'error': '规则引擎未初始化'})
        
        result = engine.get_all_rules()
        
        return jsonify(result)
    
    except Exception as e:
        logger.error(f"获取规则列表失败: {e}")
        return jsonify({'success': False, 'error': str(e)})


@batch_auto_api.route('/api/rule/trigger', methods=['POST'])
def trigger_rule():
    """手动触发规则评估"""
    try:
        data = request.get_json() or {}
        context = data.get('context', {})
        
        engine = get_rule_engine()
        if not engine:
            return jsonify({'success': False, 'error': '规则引擎未初始化'})
        
        results = engine.evaluate_and_trigger(context)
        
        return jsonify({
            'success': True,
            'triggered_rules': len(results),
            'results': results
        })
    
    except Exception as e:
        logger.error(f"触发规则评估失败: {e}")
        return jsonify({'success': False, 'error': str(e)})


@batch_auto_api.route('/api/rule/history', methods=['GET'])
def get_rule_history():
    """获取规则触发历史"""
    try:
        rule_id = request.args.get('rule_id')
        limit = int(request.args.get('limit', 50))
        
        engine = get_rule_engine()
        if not engine:
            return jsonify({'success': False, 'error': '规则引擎未初始化'})
        
        result = engine.get_trigger_history(rule_id, limit)
        
        return jsonify(result)
    
    except Exception as e:
        logger.error(f"获取规则触发历史失败: {e}")
        return jsonify({'success': False, 'error': str(e)})


@batch_auto_api.route('/api/rule/engine/status', methods=['GET'])
def get_rule_engine_status():
    """获取规则引擎状态"""
    try:
        engine = get_rule_engine()
        if not engine:
            return jsonify({'success': False, 'error': '规则引擎未初始化'})
        
        rules = engine.get_all_rules()
        
        return jsonify({
            'success': True,
            'status': {
                'total_rules': rules.get('total', 0),
                'rules': rules.get('data', []),
                'monitor_running': engine._running
            }
        })
    
    except Exception as e:
        logger.error(f"获取规则引擎状态失败: {e}")
        return jsonify({'success': False, 'error': str(e)})


# ==================== 代码修复批量任务API ====================

@batch_auto_api.route('/api/batch/code-fix', methods=['POST'])
def batch_code_fix():
    """批量代码修复任务"""
    try:
        data = request.get_json() or {}
        code_items = data.get('code_items', [])
        agent_code = data.get('agent_code', 'code_fix_batch')
        
        if not code_items:
            return jsonify({'success': False, 'error': '代码列表不能为空'})
        
        tasks = []
        for i, code_item in enumerate(code_items):
            tasks.append({
                'code': code_item.get('code', ''),
                'description': code_item.get('description', f'代码修复任务 {i+1}'),
                'language': code_item.get('language', 'python'),
                'code_id': code_item.get('code_id', f'code_{i:04d}')
            })
        
        manager = get_batch_manager()
        if not manager:
            return jsonify({'success': False, 'error': '批量任务管理器未初始化'})
        
        batch_id = manager.create_batch_task(agent_code, 'code_fix', tasks)
        
        if not batch_id:
            return jsonify({'success': False, 'error': '创建批量任务失败'})
        
        dispatch_result = manager.dispatch_batch_task(batch_id, 'code_fixer')
        
        return jsonify({
            'success': True,
            'batch_id': batch_id,
            'total_tasks': len(tasks),
            'message': '批量代码修复任务已创建并分派',
            'dispatch_result': dispatch_result
        })
    
    except Exception as e:
        logger.error(f"批量代码修复失败: {e}")
        return jsonify({'success': False, 'error': str(e)})


# ==================== 系统监控规则API ====================

@batch_auto_api.route('/api/rule/create-monitor-rules', methods=['POST'])
def create_monitor_rules():
    """创建系统监控规则"""
    try:
        engine = get_rule_engine()
        if not engine:
            return jsonify({'success': False, 'error': '规则引擎未初始化'})
        
        created_rules = []
        
        high_cpu_rule = engine.add_rule(
            name='CPU使用率过高告警',
            conditions=[
                {'field': 'cpu_usage', 'operator': 'greater_than', 'value': 80}
            ],
            actions=[
                {'action_type': 'notify_admin', 'params': {'message': 'CPU使用率超过80%'}},
                {'action_type': 'dispatch_task', 'params': {
                    'task_type': 'performance',
                    'task_data': {'action': 'analyze_cpu', 'threshold': 80},
                    'employee_template': 'performance_optimizer'
                }}
            ],
            priority=10,
            description='当CPU使用率超过80%时触发告警和性能分析'
        )
        if high_cpu_rule:
            created_rules.append({'rule_id': high_cpu_rule, 'name': 'CPU使用率过高告警'})
        
        high_memory_rule = engine.add_rule(
            name='内存使用率过高告警',
            conditions=[
                {'field': 'memory_usage', 'operator': 'greater_than', 'value': 85}
            ],
            actions=[
                {'action_type': 'notify_admin', 'params': {'message': '内存使用率超过85%'}}
            ],
            priority=10,
            description='当内存使用率超过85%时触发告警'
        )
        if high_memory_rule:
            created_rules.append({'rule_id': high_memory_rule, 'name': '内存使用率过高告警'})
        
        pending_tasks_rule = engine.add_rule(
            name='待处理任务过多',
            conditions=[
                {'field': 'pending_tasks', 'operator': 'greater_than', 'value': 10}
            ],
            actions=[
                {'action_type': 'create_employee', 'params': {'template_key': 'code_fixer', 'level': 'specialist'}},
                {'action_type': 'notify_admin', 'params': {'message': '待处理任务超过10个，已自动创建额外AI员工'}}
            ],
            priority=5,
            description='当待处理任务超过10个时自动创建AI员工'
        )
        if pending_tasks_rule:
            created_rules.append({'rule_id': pending_tasks_rule, 'name': '待处理任务过多'})
        
        return jsonify({
            'success': True,
            'created_rules': created_rules,
            'total_created': len(created_rules)
        })
    
    except Exception as e:
        logger.error(f"创建监控规则失败: {e}")
        return jsonify({'success': False, 'error': str(e)})


# ==================== 规则增强API ====================

def get_rule_generator():
    """获取规则生成器"""
    try:
        from app.agents.rule_auto_generator import get_rule_generator
        return get_rule_generator()
    except Exception as e:
        logger.error(f"获取规则生成器失败: {e}")
        return None


@batch_auto_api.route('/api/rule/templates', methods=['GET'])
def get_rule_templates():
    """获取可用规则模板列表"""
    try:
        category = request.args.get('category')
        
        generator = get_rule_generator()
        if not generator:
            return jsonify({'success': False, 'error': '规则生成器未初始化'})
        
        result = generator.get_available_templates(category)
        
        return jsonify(result)
    
    except Exception as e:
        logger.error(f"获取规则模板失败: {e}")
        return jsonify({'success': False, 'error': str(e)})


@batch_auto_api.route('/api/rule/generate', methods=['POST'])
def generate_rule_from_template():
    """根据模板生成规则"""
    try:
        data = request.get_json() or {}
        template_key = data.get('template_key')
        custom_params = data.get('custom_params')
        agent_code = data.get('agent_code', 'rule_generator_api')
        
        if not template_key:
            return jsonify({'success': False, 'error': 'template_key不能为空'})
        
        generator = get_rule_generator()
        if not generator:
            return jsonify({'success': False, 'error': '规则生成器未初始化'})
        
        result = generator.generate_rules_from_template(
            template_key, custom_params, agent_code
        )
        
        return jsonify(result)
    
    except Exception as e:
        logger.error(f"生成规则失败: {e}")
        return jsonify({'success': False, 'error': str(e)})


@batch_auto_api.route('/api/rule/batch-generate', methods=['POST'])
def batch_generate_rules():
    """批量生成规则"""
    try:
        data = request.get_json() or {}
        category = data.get('category')
        agent_code = data.get('agent_code', 'batch_rule_generator_api')
        auto_apply = data.get('auto_apply', True)
        
        generator = get_rule_generator()
        if not generator:
            return jsonify({'success': False, 'error': '规则生成器未初始化'})
        
        result = generator.batch_generate_rules(category, agent_code, auto_apply)
        
        return jsonify(result)
    
    except Exception as e:
        logger.error(f"批量生成规则失败: {e}")
        return jsonify({'success': False, 'error': str(e)})


@batch_auto_api.route('/api/batch/rule-enhancement', methods=['POST'])
def create_rule_enhancement_batch():
    """创建规则增强批量任务"""
    try:
        data = request.get_json() or {}
        rule_configs = data.get('rule_configs', [])
        agent_code = data.get('agent_code', 'rule_enhancement_batch')
        
        if not rule_configs:
            return jsonify({'success': False, 'error': '规则配置列表不能为空'})
        
        manager = get_batch_manager()
        if not manager:
            return jsonify({'success': False, 'error': '批量任务管理器未初始化'})
        
        result = manager.create_rule_enhancement_batch(agent_code, rule_configs)
        
        return jsonify(result)
    
    except Exception as e:
        logger.error(f"创建规则增强批量任务失败: {e}")
        return jsonify({'success': False, 'error': str(e)})


@batch_auto_api.route('/api/batch/auto-enhance-rules', methods=['POST'])
def auto_enhance_system_rules():
    """自动增强系统规则"""
    try:
        data = request.get_json() or {}
        categories = data.get('categories', ['performance', 'task_management', 'health'])
        agent_code = data.get('agent_code', 'auto_rule_enhancer_api')
        
        manager = get_batch_manager()
        if not manager:
            return jsonify({'success': False, 'error': '批量任务管理器未初始化'})
        
        result = manager.auto_enhance_system_rules(categories, agent_code)
        
        return jsonify(result)
    
    except Exception as e:
        logger.error(f"自动增强系统规则失败: {e}")
        return jsonify({'success': False, 'error': str(e)})


@batch_auto_api.route('/api/rule/generation-history', methods=['GET'])
def get_rule_generation_history():
    """获取规则生成历史"""
    try:
        limit = int(request.args.get('limit', 50))
        
        generator = get_rule_generator()
        if not generator:
            return jsonify({'success': False, 'error': '规则生成器未初始化'})
        
        result = generator.get_generation_history(limit)
        
        return jsonify(result)
    
    except Exception as e:
        logger.error(f"获取规则生成历史失败: {e}")
        return jsonify({'success': False, 'error': str(e)})


@batch_auto_api.route('/api/rule/update-from-feedback', methods=['POST'])
def update_rule_from_feedback():
    """根据反馈更新规则"""
    try:
        data = request.get_json() or {}
        rule_id = data.get('rule_id')
        feedback = data.get('feedback', {})
        agent_code = data.get('agent_code', 'rule_optimizer_api')
        
        if not rule_id:
            return jsonify({'success': False, 'error': 'rule_id不能为空'})
        
        generator = get_rule_generator()
        if not generator:
            return jsonify({'success': False, 'error': '规则生成器未初始化'})
        
        result = generator.update_rule_from_feedback(rule_id, feedback, agent_code)
        
        return jsonify(result)
    
    except Exception as e:
        logger.error(f"更新规则失败: {e}")
        return jsonify({'success': False, 'error': str(e)})


@batch_auto_api.route('/api/rule/quick-setup', methods=['POST'])
def quick_setup_system_rules():
    """快速设置系统规则 - 一键部署常用规则"""
    try:
        data = request.get_json() or {}
        setup_type = data.get('setup_type', 'full')  # full, performance, health, ai_collaboration
        agent_code = data.get('agent_code', 'quick_setup_api')
        
        generator = get_rule_generator()
        manager = get_batch_manager()
        
        if not generator or not manager:
            return jsonify({'success': False, 'error': '系统组件未初始化'})
        
        # 根据设置类型选择类别
        categories_map = {
            'full': ['performance', 'task_management', 'health', 'ai_collaboration', 'security', 'user_behavior'],
            'performance': ['performance'],
            'health': ['health'],
            'ai_collaboration': ['ai_collaboration'],
            'security': ['security'],
            'task_management': ['task_management']
        }
        
        categories = categories_map.get(setup_type, categories_map['full'])
        
        result = manager.auto_enhance_system_rules(categories, agent_code)
        
        return jsonify({
            'success': True,
            'setup_type': setup_type,
            'categories': categories,
            'result': result,
            'message': f'已快速部署 {result.get("total_generated", 0)} 条系统规则'
        })
    
    except Exception as e:
        logger.error(f"快速设置系统规则失败: {e}")
        return jsonify({'success': False, 'error': str(e)})


# ==================== 考试系统规则增强API ====================

@batch_auto_api.route('/api/exam/rules/templates', methods=['GET'])
def get_exam_rule_templates():
    """获取考试系统规则模板"""
    try:
        category = request.args.get('category')
        
        generator = get_rule_generator()
        if not generator:
            return jsonify({'success': False, 'error': '规则生成器未初始化'})
        
        result = generator.get_exam_templates(category)
        
        return jsonify(result)
    
    except Exception as e:
        logger.error(f"获取考试系统规则模板失败: {e}")
        return jsonify({'success': False, 'error': str(e)})


@batch_auto_api.route('/api/exam/rules/generate', methods=['POST'])
def generate_exam_rules():
    """生成考试系统规则"""
    try:
        data = request.get_json() or {}
        category = data.get('category')
        agent_code = data.get('agent_code', 'exam_rule_generator_api')
        
        generator = get_rule_generator()
        if not generator:
            return jsonify({'success': False, 'error': '规则生成器未初始化'})
        
        result = generator.generate_exam_rules(category, agent_code)
        
        return jsonify(result)
    
    except Exception as e:
        logger.error(f"生成考试系统规则失败: {e}")
        return jsonify({'success': False, 'error': str(e)})


@batch_auto_api.route('/api/exam/rules/batch-enhance', methods=['POST'])
def batch_enhance_exam_rules():
    """批量增强考试系统规则"""
    try:
        data = request.get_json() or {}
        categories = data.get('categories', ['exam_management', 'question_management', 'student_behavior', 'exam_security', 'exam_performance'])
        agent_code = data.get('agent_code', 'exam_rule_enhancer_api')
        
        generator = get_rule_generator()
        if not generator:
            return jsonify({'success': False, 'error': '规则生成器未初始化'})
        
        results = []
        total_generated = 0
        total_failed = 0
        
        for category in categories:
            result = generator.generate_exam_rules(category, agent_code)
            
            if result.get('success'):
                results.append({
                    'category': category,
                    'batch_id': result.get('batch_id'),
                    'generated': result.get('total_generated', 0),
                    'failed': result.get('total_failed', 0),
                    'rules': result.get('generated_rules', [])
                })
                total_generated += result.get('total_generated', 0)
                total_failed += result.get('total_failed', 0)
            else:
                results.append({
                    'category': category,
                    'error': result.get('error')
                })
                total_failed += 1
        
        return jsonify({
            'success': True,
            'results': results,
            'total_generated': total_generated,
            'total_failed': total_failed,
            'message': f'考试系统规则批量增强完成，共生成 {total_generated} 条规则'
        })
    
    except Exception as e:
        logger.error(f"批量增强考试系统规则失败: {e}")
        return jsonify({'success': False, 'error': str(e)})


@batch_auto_api.route('/api/exam/rules/quick-setup', methods=['POST'])
def quick_setup_exam_rules():
    """快速设置考试系统规则 - 一键部署考试相关规则"""
    try:
        data = request.get_json() or {}
        setup_type = data.get('setup_type', 'full')  # full, exam_management, question_management, security, performance
        agent_code = data.get('agent_code', 'exam_quick_setup_api')
        
        generator = get_rule_generator()
        if not generator:
            return jsonify({'success': False, 'error': '规则生成器未初始化'})
        
        categories_map = {
            'full': ['exam_management', 'question_management', 'student_behavior', 'exam_security', 'exam_performance'],
            'exam_management': ['exam_management'],
            'question_management': ['question_management'],
            'security': ['exam_security'],
            'performance': ['exam_performance'],
            'student': ['student_behavior']
        }
        
        categories = categories_map.get(setup_type, categories_map['full'])
        
        results = []
        total_generated = 0
        
        for category in categories:
            result = generator.generate_exam_rules(category, agent_code)
            if result.get('success'):
                results.append(result)
                total_generated += result.get('total_generated', 0)
        
        return jsonify({
            'success': True,
            'setup_type': setup_type,
            'categories': categories,
            'results': results,
            'total_generated': total_generated,
            'message': f'考试系统规则快速部署完成，共生成 {total_generated} 条规则'
        })
    
    except Exception as e:
        logger.error(f"快速设置考试系统规则失败: {e}")
        return jsonify({'success': False, 'error': str(e)})


@batch_auto_api.route('/api/exam/rules/sync', methods=['POST'])
def sync_exam_rules_to_db():
    """同步考试系统规则到数据库"""
    try:
        data = request.get_json() or {}
        category = data.get('category')
        agent_code = data.get('agent_code', 'exam_rule_sync_api')
        
        generator = get_rule_generator()
        if not generator:
            return jsonify({'success': False, 'error': '规则生成器未初始化'})
        
        result = generator.generate_exam_rules(category, agent_code)
        
        if result.get('success'):
            return jsonify({
                'success': True,
                'batch_id': result.get('batch_id'),
                'total_generated': result.get('total_generated'),
                'message': '考试系统规则已同步到数据库，AI员工可自动触发规则执行'
            })
        
        return jsonify(result)
    
    except Exception as e:
        logger.error(f"同步考试系统规则失败: {e}")
        return jsonify({'success': False, 'error': str(e)})


# ==================== 题库系统规则增强API ====================

@batch_auto_api.route('/api/question-bank/rules/templates', methods=['GET'])
def get_question_bank_rule_templates():
    """获取题库系统规则模板"""
    try:
        category = request.args.get('category')
        
        generator = get_rule_generator()
        if not generator:
            return jsonify({'success': False, 'error': '规则生成器未初始化'})
        
        result = generator.get_question_bank_templates(category)
        
        return jsonify(result)
    
    except Exception as e:
        logger.error(f"获取题库系统规则模板失败: {e}")
        return jsonify({'success': False, 'error': str(e)})


@batch_auto_api.route('/api/question-bank/rules/generate', methods=['POST'])
def generate_question_bank_rules():
    """生成题库系统规则"""
    try:
        data = request.get_json() or {}
        category = data.get('category')
        agent_code = data.get('agent_code', 'question_bank_rule_generator_api')
        
        generator = get_rule_generator()
        if not generator:
            return jsonify({'success': False, 'error': '规则生成器未初始化'})
        
        result = generator.generate_question_bank_rules(category, agent_code)
        
        return jsonify(result)
    
    except Exception as e:
        logger.error(f"生成题库系统规则失败: {e}")
        return jsonify({'success': False, 'error': str(e)})


@batch_auto_api.route('/api/question-bank/rules/batch-enhance', methods=['POST'])
def batch_enhance_question_bank_rules():
    """批量增强题库系统规则"""
    try:
        data = request.get_json() or {}
        categories = data.get('categories', ['question_management', 'bank_expansion', 'quality_assurance', 'statistics', 'ai_optimization'])
        agent_code = data.get('agent_code', 'question_bank_rule_enhancer_api')
        
        generator = get_rule_generator()
        if not generator:
            return jsonify({'success': False, 'error': '规则生成器未初始化'})
        
        results = []
        total_generated = 0
        total_failed = 0
        
        for category in categories:
            result = generator.generate_question_bank_rules(category, agent_code)
            
            if result.get('success'):
                results.append({
                    'category': category,
                    'batch_id': result.get('batch_id'),
                    'generated': result.get('total_generated', 0),
                    'failed': result.get('total_failed', 0),
                    'rules': result.get('generated_rules', [])
                })
                total_generated += result.get('total_generated', 0)
                total_failed += result.get('total_failed', 0)
            else:
                results.append({
                    'category': category,
                    'error': result.get('error')
                })
                total_failed += 1
        
        return jsonify({
            'success': True,
            'results': results,
            'total_generated': total_generated,
            'total_failed': total_failed,
            'message': f'题库系统规则批量增强完成，共生成 {total_generated} 条规则'
        })
    
    except Exception as e:
        logger.error(f"批量增强题库系统规则失败: {e}")
        return jsonify({'success': False, 'error': str(e)})


@batch_auto_api.route('/api/question-bank/rules/quick-setup', methods=['POST'])
def quick_setup_question_bank_rules():
    """快速设置题库系统规则 - 一键部署题库相关规则"""
    try:
        data = request.get_json() or {}
        setup_type = data.get('setup_type', 'full')  # full, question_management, bank_expansion, quality, statistics, ai_optimization
        agent_code = data.get('agent_code', 'question_bank_quick_setup_api')
        
        generator = get_rule_generator()
        if not generator:
            return jsonify({'success': False, 'error': '规则生成器未初始化'})
        
        categories_map = {
            'full': ['question_management', 'bank_expansion', 'quality_assurance', 'statistics', 'ai_optimization'],
            'question_management': ['question_management'],
            'bank_expansion': ['bank_expansion'],
            'quality': ['quality_assurance'],
            'statistics': ['statistics'],
            'ai_optimization': ['ai_optimization']
        }
        
        categories = categories_map.get(setup_type, categories_map['full'])
        
        results = []
        total_generated = 0
        
        for category in categories:
            result = generator.generate_question_bank_rules(category, agent_code)
            if result.get('success'):
                results.append(result)
                total_generated += result.get('total_generated', 0)
        
        return jsonify({
            'success': True,
            'setup_type': setup_type,
            'categories': categories,
            'results': results,
            'total_generated': total_generated,
            'message': f'题库系统规则快速部署完成，共生成 {total_generated} 条规则'
        })
    
    except Exception as e:
        logger.error(f"快速设置题库系统规则失败: {e}")
        return jsonify({'success': False, 'error': str(e)})


@batch_auto_api.route('/api/question-bank/rules/sync', methods=['POST'])
def sync_question_bank_rules_to_db():
    """同步题库系统规则到数据库"""
    try:
        data = request.get_json() or {}
        category = data.get('category')
        agent_code = data.get('agent_code', 'question_bank_rule_sync_api')
        
        generator = get_rule_generator()
        if not generator:
            return jsonify({'success': False, 'error': '规则生成器未初始化'})
        
        result = generator.generate_question_bank_rules(category, agent_code)
        
        if result.get('success'):
            return jsonify({
                'success': True,
                'batch_id': result.get('batch_id'),
                'total_generated': result.get('total_generated'),
                'message': '题库系统规则已同步到数据库，AI员工可自动触发规则执行'
            })
        
        return jsonify(result)
    
    except Exception as e:
        logger.error(f"同步题库系统规则失败: {e}")
        return jsonify({'success': False, 'error': str(e)})


# ==================== 数据安全系统规则增强API ====================

@batch_auto_api.route('/api/security/rules/templates', methods=['GET'])
def get_security_rule_templates():
    """获取数据安全系统规则模板"""
    try:
        category = request.args.get('category')
        
        generator = get_rule_generator()
        if not generator:
            return jsonify({'success': False, 'error': '规则生成器未初始化'})
        
        result = generator.get_security_templates(category)
        
        return jsonify(result)
    
    except Exception as e:
        logger.error(f"获取数据安全规则模板失败: {e}")
        return jsonify({'success': False, 'error': str(e)})


@batch_auto_api.route('/api/security/rules/generate', methods=['POST'])
def generate_security_rules():
    """生成数据安全系统规则"""
    try:
        data = request.get_json() or {}
        category = data.get('category')
        agent_code = data.get('agent_code', 'security_rule_generator_api')
        
        generator = get_rule_generator()
        if not generator:
            return jsonify({'success': False, 'error': '规则生成器未初始化'})
        
        result = generator.generate_security_rules(category, agent_code)
        
        return jsonify(result)
    
    except Exception as e:
        logger.error(f"生成数据安全规则失败: {e}")
        return jsonify({'success': False, 'error': str(e)})


@batch_auto_api.route('/api/security/rules/batch-enhance', methods=['POST'])
def batch_enhance_security_rules():
    """批量增强数据安全系统规则"""
    try:
        data = request.get_json() or {}
        categories = data.get('categories', ['access_security', 'encryption_security', 'integrity_security', 
                                            'privacy_protection', 'leakage_prevention', 'security_audit',
                                            'database_security', 'access_control'])
        agent_code = data.get('agent_code', 'security_rule_enhancer_api')
        
        generator = get_rule_generator()
        if not generator:
            return jsonify({'success': False, 'error': '规则生成器未初始化'})
        
        results = []
        total_generated = 0
        total_failed = 0
        
        for category in categories:
            result = generator.generate_security_rules(category, agent_code)
            
            if result.get('success'):
                results.append({
                    'category': category,
                    'batch_id': result.get('batch_id'),
                    'generated': result.get('total_generated', 0),
                    'failed': result.get('total_failed', 0),
                    'rules': result.get('generated_rules', [])
                })
                total_generated += result.get('total_generated', 0)
                total_failed += result.get('total_failed', 0)
            else:
                results.append({
                    'category': category,
                    'error': result.get('error')
                })
                total_failed += 1
        
        return jsonify({
            'success': True,
            'results': results,
            'total_generated': total_generated,
            'total_failed': total_failed,
            'message': f'数据安全系统规则批量增强完成，共生成 {total_generated} 条规则'
        })
    
    except Exception as e:
        logger.error(f"批量增强数据安全规则失败: {e}")
        return jsonify({'success': False, 'error': str(e)})


@batch_auto_api.route('/api/security/rules/quick-setup', methods=['POST'])
def quick_setup_security_rules():
    """快速设置数据安全规则 - 一键部署安全相关规则"""
    try:
        data = request.get_json() or {}
        setup_type = data.get('setup_type', 'full')  # full, access, encryption, integrity, privacy, leakage, audit, database, control
        agent_code = data.get('agent_code', 'security_quick_setup_api')
        
        generator = get_rule_generator()
        if not generator:
            return jsonify({'success': False, 'error': '规则生成器未初始化'})
        
        categories_map = {
            'full': ['access_security', 'encryption_security', 'integrity_security', 
                    'privacy_protection', 'leakage_prevention', 'security_audit',
                    'database_security', 'access_control'],
            'access': ['access_security'],
            'encryption': ['encryption_security'],
            'integrity': ['integrity_security'],
            'privacy': ['privacy_protection'],
            'leakage': ['leakage_prevention'],
            'audit': ['security_audit'],
            'database': ['database_security'],
            'control': ['access_control']
        }
        
        categories = categories_map.get(setup_type, categories_map['full'])
        
        results = []
        total_generated = 0
        
        for category in categories:
            result = generator.generate_security_rules(category, agent_code)
            if result.get('success'):
                results.append(result)
                total_generated += result.get('total_generated', 0)
        
        return jsonify({
            'success': True,
            'setup_type': setup_type,
            'categories': categories,
            'results': results,
            'total_generated': total_generated,
            'message': f'数据安全规则快速部署完成，共生成 {total_generated} 条规则'
        })
    
    except Exception as e:
        logger.error(f"快速设置数据安全规则失败: {e}")
        return jsonify({'success': False, 'error': str(e)})


@batch_auto_api.route('/api/security/rules/sync', methods=['POST'])
def sync_security_rules_to_db():
    """同步数据安全规则到数据库"""
    try:
        data = request.get_json() or {}
        category = data.get('category')
        agent_code = data.get('agent_code', 'security_rule_sync_api')
        
        generator = get_rule_generator()
        if not generator:
            return jsonify({'success': False, 'error': '规则生成器未初始化'})
        
        result = generator.generate_security_rules(category, agent_code)
        
        if result.get('success'):
            return jsonify({
                'success': True,
                'batch_id': result.get('batch_id'),
                'total_generated': result.get('total_generated'),
                'message': '数据安全规则已同步到数据库，AI员工可自动触发规则执行'
            })
        
        return jsonify(result)
    
    except Exception as e:
        logger.error(f"同步数据安全规则失败: {e}")
        return jsonify({'success': False, 'error': str(e)})


# ==================== 网络层安全系统规则增强API ====================

@batch_auto_api.route('/api/network-security/rules/templates', methods=['GET'])
def get_network_security_rule_templates():
    """获取网络层安全系统规则模板"""
    try:
        category = request.args.get('category')
        
        generator = get_rule_generator()
        if not generator:
            return jsonify({'success': False, 'error': '规则生成器未初始化'})
        
        result = generator.get_network_security_templates(category)
        
        return jsonify(result)
    
    except Exception as e:
        logger.error(f"获取网络层安全规则模板失败: {e}")
        return jsonify({'success': False, 'error': str(e)})


@batch_auto_api.route('/api/network-security/rules/generate', methods=['POST'])
def generate_network_security_rules():
    """生成网络层安全系统规则"""
    try:
        data = request.get_json() or {}
        category = data.get('category')
        agent_code = data.get('agent_code', 'network_security_rule_generator_api')
        
        generator = get_rule_generator()
        if not generator:
            return jsonify({'success': False, 'error': '规则生成器未初始化'})
        
        result = generator.generate_network_security_rules(category, agent_code)
        
        return jsonify(result)
    
    except Exception as e:
        logger.error(f"生成网络层安全规则失败: {e}")
        return jsonify({'success': False, 'error': str(e)})


@batch_auto_api.route('/api/network-security/rules/batch-enhance', methods=['POST'])
def batch_enhance_network_security_rules():
    """批量增强网络层安全系统规则"""
    try:
        data = request.get_json() or {}
        categories = data.get('categories', ['firewall_security', 'ddos_protection', 'intrusion_detection', 
                                           'ssl_tls_security', 'dns_security', 'vpn_tunnel_security',
                                           'network_isolation', 'network_traffic_monitoring'])
        agent_code = data.get('agent_code', 'network_security_rule_enhancer_api')
        
        generator = get_rule_generator()
        if not generator:
            return jsonify({'success': False, 'error': '规则生成器未初始化'})
        
        results = []
        total_generated = 0
        total_failed = 0
        
        for category in categories:
            result = generator.generate_network_security_rules(category, agent_code)
            
            if result.get('success'):
                results.append({
                    'category': category,
                    'batch_id': result.get('batch_id'),
                    'generated': result.get('total_generated', 0),
                    'failed': result.get('total_failed', 0),
                    'rules': result.get('generated_rules', [])
                })
                total_generated += result.get('total_generated', 0)
                total_failed += result.get('total_failed', 0)
            else:
                results.append({
                    'category': category,
                    'error': result.get('error')
                })
                total_failed += 1
        
        return jsonify({
            'success': True,
            'results': results,
            'total_generated': total_generated,
            'total_failed': total_failed,
            'message': f'网络层安全系统规则批量增强完成，共生成 {total_generated} 条规则'
        })
    
    except Exception as e:
        logger.error(f"批量增强网络层安全规则失败: {e}")
        return jsonify({'success': False, 'error': str(e)})


@batch_auto_api.route('/api/network-security/rules/quick-setup', methods=['POST'])
def quick_setup_network_security_rules():
    """快速设置网络层安全规则 - 一键部署网络安全相关规则"""
    try:
        data = request.get_json() or {}
        setup_type = data.get('setup_type', 'full')  # full, firewall, ddos, intrusion, ssl, dns, vpn, isolation, traffic
        agent_code = data.get('agent_code', 'network_security_quick_setup_api')
        
        generator = get_rule_generator()
        if not generator:
            return jsonify({'success': False, 'error': '规则生成器未初始化'})
        
        categories_map = {
            'full': ['firewall_security', 'ddos_protection', 'intrusion_detection', 
                    'ssl_tls_security', 'dns_security', 'vpn_tunnel_security',
                    'network_isolation', 'network_traffic_monitoring'],
            'firewall': ['firewall_security'],
            'ddos': ['ddos_protection'],
            'intrusion': ['intrusion_detection'],
            'ssl': ['ssl_tls_security'],
            'dns': ['dns_security'],
            'vpn': ['vpn_tunnel_security'],
            'isolation': ['network_isolation'],
            'traffic': ['network_traffic_monitoring']
        }
        
        categories = categories_map.get(setup_type, categories_map['full'])
        
        results = []
        total_generated = 0
        
        for category in categories:
            result = generator.generate_network_security_rules(category, agent_code)
            if result.get('success'):
                results.append(result)
                total_generated += result.get('total_generated', 0)
        
        return jsonify({
            'success': True,
            'setup_type': setup_type,
            'categories': categories,
            'results': results,
            'total_generated': total_generated,
            'message': f'网络层安全规则快速部署完成，共生成 {total_generated} 条规则'
        })
    
    except Exception as e:
        logger.error(f"快速设置网络层安全规则失败: {e}")
        return jsonify({'success': False, 'error': str(e)})


@batch_auto_api.route('/api/network-security/rules/sync', methods=['POST'])
def sync_network_security_rules_to_db():
    """同步网络层安全规则到数据库"""
    try:
        data = request.get_json() or {}
        category = data.get('category')
        agent_code = data.get('agent_code', 'network_security_rule_sync_api')
        
        generator = get_rule_generator()
        if not generator:
            return jsonify({'success': False, 'error': '规则生成器未初始化'})
        
        result = generator.generate_network_security_rules(category, agent_code)
        
        if result.get('success'):
            return jsonify({
                'success': True,
                'batch_id': result.get('batch_id'),
                'total_generated': result.get('total_generated'),
                'message': '网络层安全规则已同步到数据库，AI员工可自动触发规则执行'
            })
        
        return jsonify(result)
    
    except Exception as e:
        logger.error(f"同步网络层安全规则失败: {e}")
        return jsonify({'success': False, 'error': str(e)})


# ==================== 系统前端增强规则API ====================

@batch_auto_api.route('/api/frontend/rules/templates', methods=['GET'])
def get_frontend_rule_templates():
    """获取前端系统规则模板"""
    try:
        category = request.args.get('category')
        
        generator = get_rule_generator()
        if not generator:
            return jsonify({'success': False, 'error': '规则生成器未初始化'})
        
        result = generator.get_frontend_templates(category)
        
        return jsonify(result)
    
    except Exception as e:
        logger.error(f"获取前端规则模板失败: {e}")
        return jsonify({'success': False, 'error': str(e)})


@batch_auto_api.route('/api/frontend/rules/generate', methods=['POST'])
def generate_frontend_rules():
    """生成前端系统规则"""
    try:
        data = request.get_json() or {}
        category = data.get('category')
        agent_code = data.get('agent_code', 'frontend_rule_generator_api')
        
        generator = get_rule_generator()
        if not generator:
            return jsonify({'success': False, 'error': '规则生成器未初始化'})
        
        result = generator.generate_frontend_rules(category, agent_code)
        
        return jsonify(result)
    
    except Exception as e:
        logger.error(f"生成前端规则失败: {e}")
        return jsonify({'success': False, 'error': str(e)})


@batch_auto_api.route('/api/frontend/rules/batch-enhance', methods=['POST'])
def batch_enhance_frontend_rules():
    """批量增强前端系统规则"""
    try:
        data = request.get_json() or {}
        categories = data.get('categories', ['ui_performance', 'user_interaction', 'frontend_error', 
                                           'page_load', 'responsive_design', 'frontend_security',
                                           'user_experience', 'resource_management'])
        agent_code = data.get('agent_code', 'frontend_rule_enhancer_api')
        
        generator = get_rule_generator()
        if not generator:
            return jsonify({'success': False, 'error': '规则生成器未初始化'})
        
        results = []
        total_generated = 0
        total_failed = 0
        
        for category in categories:
            result = generator.generate_frontend_rules(category, agent_code)
            
            if result.get('success'):
                results.append({
                    'category': category,
                    'batch_id': result.get('batch_id'),
                    'generated': result.get('total_generated', 0),
                    'failed': result.get('total_failed', 0),
                    'rules': result.get('generated_rules', [])
                })
                total_generated += result.get('total_generated', 0)
                total_failed += result.get('total_failed', 0)
            else:
                results.append({
                    'category': category,
                    'error': result.get('error')
                })
                total_failed += 1
        
        return jsonify({
            'success': True,
            'results': results,
            'total_generated': total_generated,
            'total_failed': total_failed,
            'message': f'前端系统规则批量增强完成，共生成 {total_generated} 条规则'
        })
    
    except Exception as e:
        logger.error(f"批量增强前端规则失败: {e}")
        return jsonify({'success': False, 'error': str(e)})


@batch_auto_api.route('/api/frontend/rules/quick-setup', methods=['POST'])
def quick_setup_frontend_rules():
    """快速设置前端规则 - 一键部署前端相关规则"""
    try:
        data = request.get_json() or {}
        setup_type = data.get('setup_type', 'full')  # full, performance, interaction, error, page_load, responsive, security, ux, resource
        agent_code = data.get('agent_code', 'frontend_quick_setup_api')
        
        generator = get_rule_generator()
        if not generator:
            return jsonify({'success': False, 'error': '规则生成器未初始化'})
        
        categories_map = {
            'full': ['ui_performance', 'user_interaction', 'frontend_error', 
                    'page_load', 'responsive_design', 'frontend_security',
                    'user_experience', 'resource_management'],
            'performance': ['ui_performance'],
            'interaction': ['user_interaction'],
            'error': ['frontend_error'],
            'page_load': ['page_load'],
            'responsive': ['responsive_design'],
            'security': ['frontend_security'],
            'ux': ['user_experience'],
            'resource': ['resource_management']
        }
        
        categories = categories_map.get(setup_type, categories_map['full'])
        
        results = []
        total_generated = 0
        
        for category in categories:
            result = generator.generate_frontend_rules(category, agent_code)
            if result.get('success'):
                results.append(result)
                total_generated += result.get('total_generated', 0)
        
        return jsonify({
            'success': True,
            'setup_type': setup_type,
            'categories': categories,
            'results': results,
            'total_generated': total_generated,
            'message': f'前端规则快速部署完成，共生成 {total_generated} 条规则'
        })
    
    except Exception as e:
        logger.error(f"快速设置前端规则失败: {e}")
        return jsonify({'success': False, 'error': str(e)})


@batch_auto_api.route('/api/frontend/rules/sync', methods=['POST'])
def sync_frontend_rules_to_db():
    """同步前端规则到数据库"""
    try:
        data = request.get_json() or {}
        category = data.get('category')
        agent_code = data.get('agent_code', 'frontend_rule_sync_api')
        
        generator = get_rule_generator()
        if not generator:
            return jsonify({'success': False, 'error': '规则生成器未初始化'})
        
        result = generator.generate_frontend_rules(category, agent_code)
        
        if result.get('success'):
            return jsonify({
                'success': True,
                'batch_id': result.get('batch_id'),
                'total_generated': result.get('total_generated'),
                'message': '前端规则已同步到数据库，AI员工可自动触发规则执行'
            })
        
        return jsonify(result)
    
    except Exception as e:
        logger.error(f"同步前端规则失败: {e}")
        return jsonify({'success': False, 'error': str(e)})