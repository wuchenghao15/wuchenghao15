#!/usr/bin/env python3
"""
后台自动挂载 API
暴露任务调度、进程管理、事件Hook、AI Agent管理功能
"""
from flask import Blueprint, jsonify, request
from app.middlewares.access_control import require_login, require_admin

auto_mount_api = Blueprint('auto_mount_api', __name__)


def _get_svc():
    from app.services.auto_mount_service import auto_mount_service
    return auto_mount_service


# ============ 挂载控制 ============

@auto_mount_api.route('/api/auto-mount/mount', methods=['POST'])
@require_admin
def mount_all():
    """挂载所有后台组件"""
    svc = _get_svc()
    result = svc.mount_all()
    return jsonify(result)


@auto_mount_api.route('/api/auto-mount/unmount', methods=['POST'])
@require_admin
def unmount_all():
    """卸载所有后台组件"""
    svc = _get_svc()
    svc.unmount_all()
    return jsonify({'success': True})


@auto_mount_api.route('/api/auto-mount/status', methods=['GET'])
@require_login
def mount_status():
    """获取挂载状态"""
    svc = _get_svc()
    status = svc.get_status()
    return jsonify({'success': True, 'data': status})


# ============ 任务管理 ============

@auto_mount_api.route('/api/auto-mount/tasks', methods=['POST'])
@require_admin
def register_task():
    """注册后台任务"""
    data = request.get_json() or {}
    svc = _get_svc()
    result = svc.register_task(
        task_id=data.get('task_id', ''),
        module_path=data.get('module_path', ''),
        func_name=data.get('func_name', ''),
        name=data.get('name', ''),
        interval=float(data.get('interval', 60)),
        priority=int(data.get('priority', 5)),
        config=data.get('config', {})
    )
    return jsonify(result)


@auto_mount_api.route('/api/auto-mount/tasks', methods=['GET'])
@require_login
def list_tasks():
    """列出所有任务"""
    svc = _get_svc()
    tasks = svc.list_tasks()
    return jsonify({'success': True, 'count': len(tasks), 'data': tasks})


@auto_mount_api.route('/api/auto-mount/tasks/<task_id>/run', methods=['POST'])
@require_admin
def run_task_now(task_id):
    """立即运行任务"""
    svc = _get_svc()
    result = svc.run_task_now(task_id)
    return jsonify(result)


# ============ 进程管理 ============

@auto_mount_api.route('/api/auto-mount/processes', methods=['POST'])
@require_admin
def start_process():
    """启动后台进程"""
    data = request.get_json() or {}
    svc = _get_svc()
    import importlib
    module = importlib.import_module(data.get('module_path', ''))
    func = getattr(module, data.get('func_name', ''))

    def target():
        try:
            func()
        except Exception as e:
            pass

    result = svc.start_background_process(
        pid=data.get('pid', ''),
        target=target,
        name=data.get('name', '')
    )
    return jsonify(result)


@auto_mount_api.route('/api/auto-mount/processes/<pid>', methods=['DELETE'])
@require_admin
def stop_process(pid):
    """停止后台进程"""
    svc = _get_svc()
    result = svc.stop_background_process(pid)
    return jsonify(result)


@auto_mount_api.route('/api/auto-mount/processes', methods=['GET'])
@require_login
def list_processes():
    """列出所有进程"""
    svc = _get_svc()
    processes = svc.list_background_processes()
    return jsonify({'success': True, 'count': len(processes), 'data': processes})


# ============ 事件Hook ============

@auto_mount_api.route('/api/auto-mount/events/subscribe', methods=['POST'])
@require_admin
def subscribe_event():
    """订阅事件"""
    data = request.get_json() or {}
    svc = _get_svc()
    # 注意：handler需要通过函数名引用
    sub_id = svc.subscribe_event(
        event=data.get('event', ''),
        priority=int(data.get('priority', 10))
    )
    return jsonify({'success': True, 'sub_id': sub_id})


@auto_mount_api.route('/api/auto-mount/events/emit', methods=['POST'])
@require_login
def emit_event():
    """发射事件"""
    data = request.get_json() or {}
    svc = _get_svc()
    event = data.get('event', '')
    payload = data.get('payload', {})
    results = svc.emit_event(event, **payload)
    return jsonify({'success': True, 'results': results})


@auto_mount_api.route('/api/auto-mount/events', methods=['GET'])
@require_login
def list_events():
    """列出事件类型"""
    svc = _get_svc()
    events = svc.list_events()
    return jsonify({'success': True, 'events': events})


@auto_mount_api.route('/api/auto-mount/events/history', methods=['GET'])
@require_login
def event_history():
    """获取事件历史"""
    event = request.args.get('event', '')
    limit = min(int(request.args.get('limit', 50)), 200)
    svc = _get_svc()
    history = svc.get_event_history(event, limit)
    return jsonify({'success': True, 'count': len(history), 'data': history})


# ============ AI Agent 管理 ============

@auto_mount_api.route('/api/auto-mount/agents/register', methods=['POST'])
@require_admin
def register_agent():
    """注册AI Agent"""
    data = request.get_json() or {}
    svc = _get_svc()
    result = svc.register_and_load_agent(
        agent_id=data.get('agent_id', ''),
        agent_name=data.get('agent_name', ''),
        module_path=data.get('module_path', ''),
        class_name=data.get('class_name', ''),
        agent_type=data.get('agent_type', 'employee'),
        auto_load=data.get('auto_load', True)
    )
    return jsonify(result)


@auto_mount_api.route('/api/auto-mount/agents', methods=['GET'])
@require_login
def list_agents():
    """列出所有AI Agent"""
    svc = _get_svc()
    agents = svc.list_agents()
    return jsonify({'success': True, 'count': len(agents), 'data': agents})


@auto_mount_api.route('/api/auto-mount/agents/<agent_id>', methods=['GET'])
@require_login
def get_agent(agent_id):
    """获取单个Agent"""
    svc = _get_svc()
    agent = svc.get_agent(agent_id)
    if agent:
        return jsonify({'success': True, 'data': str(agent)})
    return jsonify({'success': False, 'error': 'Agent not found'}), 404


# ============ 健康检查 ============

@auto_mount_api.route('/api/auto-mount/health', methods=['GET'])
def health_check():
    """健康检查"""
    svc = _get_svc()
    status = svc.get_status()
    return jsonify({
        'status': 'healthy',
        'mounted': status['mounted'],
        'tasks_count': status['tasks']['total'],
        'agents_count': status['agents']['total'],
        'processes_count': len(status['processes']),
        'events_types': len(status['events']['types'])
    })
