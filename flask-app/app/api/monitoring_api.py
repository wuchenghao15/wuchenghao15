# -*- coding: utf-8 -*-
"""
MonitoringAPI - 监控采集与Agent运行时API蓝图
提供监控采集、GitHub集成、Agent运行时管理等接口
"""
from flask import Blueprint, request, jsonify, Response
import logging

logger = logging.getLogger(__name__)

monitoring_api = Blueprint('monitoring_api', __name__, url_prefix='/api/monitoring')


@monitoring_api.route('/metrics', methods=['GET'])
def get_metrics():
    """获取Prometheus格式指标"""
    try:
        from app.agents.monitoring_collector import get_monitoring_collector
        
        collector = get_monitoring_collector()
        metrics = collector.get_prometheus_metrics()
        
        return Response(metrics, content_type='text/plain')
    
    except Exception as e:
        logger.error(f"获取指标失败: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@monitoring_api.route('/system', methods=['GET'])
def get_system_metrics():
    """获取系统指标"""
    try:
        from app.agents.monitoring_collector import get_monitoring_collector
        
        collector = get_monitoring_collector()
        metrics = collector.collect_system_metrics()
        
        return jsonify({
            'success': True,
            'metrics': metrics
        })
    
    except Exception as e:
        logger.error(f"获取系统指标失败: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@monitoring_api.route('/app', methods=['GET'])
def get_app_metrics():
    """获取应用指标"""
    try:
        from app.agents.monitoring_collector import get_monitoring_collector
        
        collector = get_monitoring_collector()
        metrics = collector.collect_app_metrics()
        
        return jsonify({
            'success': True,
            'metrics': metrics
        })
    
    except Exception as e:
        logger.error(f"获取应用指标失败: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@monitoring_api.route('/logs', methods=['GET'])
def get_logs():
    """获取日志"""
    try:
        from app.agents.monitoring_collector import get_monitoring_collector
        
        collector = get_monitoring_collector()
        lines = int(request.args.get('lines', 50))
        logs = collector.collect_logs(lines)
        
        return jsonify({
            'success': True,
            'logs': logs
        })
    
    except Exception as e:
        logger.error(f"获取日志失败: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@monitoring_api.route('/telegraf', methods=['GET'])
def get_telegraf_format():
    """获取Telegraf格式指标"""
    try:
        from app.agents.monitoring_collector import get_monitoring_collector
        
        collector = get_monitoring_collector()
        metrics = collector.collect_system_metrics()
        telegraf_data = collector.format_telegraf(metrics)
        
        return Response(telegraf_data, content_type='text/plain')
    
    except Exception as e:
        logger.error(f"获取Telegraf格式数据失败: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@monitoring_api.route('/loki', methods=['GET'])
def get_loki_format():
    """获取Loki格式指标"""
    try:
        from app.agents.monitoring_collector import get_monitoring_collector
        
        collector = get_monitoring_collector()
        metrics = collector.collect_system_metrics()
        loki_data = collector.format_loki(metrics)
        
        return jsonify(loki_data)
    
    except Exception as e:
        logger.error(f"获取Loki格式数据失败: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@monitoring_api.route('/push/loki', methods=['POST'])
def push_to_loki():
    """推送数据到Loki"""
    try:
        from app.agents.monitoring_collector import get_monitoring_collector
        
        collector = get_monitoring_collector()
        loki_url = request.args.get('url')
        
        metrics = collector.collect_system_metrics()
        success = collector.push_to_loki(metrics, loki_url)
        
        return jsonify({
            'success': success,
            'message': '推送成功' if success else '推送失败'
        })
    
    except Exception as e:
        logger.error(f"推送Loki失败: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@monitoring_api.route('/github/connect', methods=['POST'])
def github_connect():
    """连接GitHub"""
    try:
        from app.agents.github_integration import get_github_integration
        
        github = get_github_integration()
        
        return jsonify({
            'success': github.is_connected(),
            'connected': github.is_connected()
        })
    
    except Exception as e:
        logger.error(f"GitHub连接失败: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@monitoring_api.route('/github/repos', methods=['GET'])
def github_list_repos():
    """获取GitHub仓库列表"""
    try:
        from app.agents.github_integration import get_github_integration
        
        github = get_github_integration()
        repos = github.get_repositories()
        
        return jsonify({
            'success': True,
            'repos': repos
        })
    
    except Exception as e:
        logger.error(f"获取GitHub仓库失败: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@monitoring_api.route('/github/branches', methods=['GET'])
def github_list_branches():
    """获取分支列表"""
    try:
        from app.agents.github_integration import get_github_integration
        
        repo_name = request.args.get('repo_name')
        if not repo_name:
            return jsonify({'success': False, 'error': 'repo_name参数必填'}), 400
        
        github = get_github_integration()
        branches = github.get_branches(repo_name)
        
        return jsonify({
            'success': True,
            'branches': branches
        })
    
    except Exception as e:
        logger.error(f"获取分支列表失败: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@monitoring_api.route('/github/read-file', methods=['GET'])
def github_read_file():
    """读取仓库文件"""
    try:
        from app.agents.github_integration import get_github_integration
        
        repo_name = request.args.get('repo_name')
        file_path = request.args.get('file_path')
        branch = request.args.get('branch')
        
        if not repo_name or not file_path:
            return jsonify({'success': False, 'error': 'repo_name和file_path参数必填'}), 400
        
        github = get_github_integration()
        result = github.read_file(repo_name, file_path, branch)
        
        return jsonify(result)
    
    except Exception as e:
        logger.error(f"读取文件失败: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@monitoring_api.route('/github/write-file', methods=['POST'])
def github_write_file():
    """写入仓库文件"""
    try:
        from app.agents.github_integration import get_github_integration
        
        data = request.get_json() or {}
        
        repo_name = data.get('repo_name')
        file_path = data.get('file_path')
        content = data.get('content')
        message = data.get('message', 'Update file')
        branch = data.get('branch')
        
        if not repo_name or not file_path or content is None:
            return jsonify({'success': False, 'error': 'repo_name、file_path、content参数必填'}), 400
        
        github = get_github_integration()
        result = github.write_file(repo_name, file_path, content, message, branch)
        
        return jsonify(result)
    
    except Exception as e:
        logger.error(f"写入文件失败: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@monitoring_api.route('/github/create-branch', methods=['POST'])
def github_create_branch():
    """创建分支"""
    try:
        from app.agents.github_integration import get_github_integration
        
        data = request.get_json() or {}
        
        repo_name = data.get('repo_name')
        base_branch = data.get('base_branch', 'main')
        new_branch = data.get('new_branch')
        
        if not repo_name or not new_branch:
            return jsonify({'success': False, 'error': 'repo_name和new_branch参数必填'}), 400
        
        github = get_github_integration()
        result = github.create_branch(repo_name, base_branch, new_branch)
        
        return jsonify(result)
    
    except Exception as e:
        logger.error(f"创建分支失败: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@monitoring_api.route('/github/create-pr', methods=['POST'])
def github_create_pr():
    """创建Pull Request"""
    try:
        from app.agents.github_integration import get_github_integration
        
        data = request.get_json() or {}
        
        repo_name = data.get('repo_name')
        head_branch = data.get('head_branch')
        base_branch = data.get('base_branch', 'main')
        title = data.get('title')
        body = data.get('body', '')
        
        if not repo_name or not head_branch or not title:
            return jsonify({'success': False, 'error': 'repo_name、head_branch、title参数必填'}), 400
        
        github = get_github_integration()
        result = github.create_pull_request(repo_name, head_branch, base_branch, title, body)
        
        return jsonify(result)
    
    except Exception as e:
        logger.error(f"创建PR失败: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@monitoring_api.route('/github/auto-fix', methods=['POST'])
def github_auto_fix():
    """自动修复并推送"""
    try:
        from app.agents.github_integration import get_github_integration
        
        data = request.get_json() or {}
        
        repo_name = data.get('repo_name')
        file_path = data.get('file_path')
        original_content = data.get('original_content')
        fixed_content = data.get('fixed_content')
        fix_description = data.get('fix_description', 'Auto fix')
        
        if not repo_name or not file_path or not fixed_content:
            return jsonify({'success': False, 'error': 'repo_name、file_path、fixed_content参数必填'}), 400
        
        github = get_github_integration()
        result = github.auto_fix_and_push(repo_name, file_path, original_content, fixed_content, fix_description)
        
        return jsonify(result)
    
    except Exception as e:
        logger.error(f"自动修复失败: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@monitoring_api.route('/agent-runtime/runtimes', methods=['GET'])
def get_runtimes():
    """获取所有Agent运行时"""
    try:
        from app.agents.agent_runtime import get_runtime_manager
        
        manager = get_runtime_manager()
        runtimes = manager.get_all_runtimes()
        
        return jsonify({
            'success': True,
            'runtimes': runtimes
        })
    
    except Exception as e:
        logger.error(f"获取运行时失败: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@monitoring_api.route('/agent-runtime/<runtime_id>', methods=['GET'])
def get_runtime(runtime_id):
    """获取单个Agent运行时状态"""
    try:
        from app.agents.agent_runtime import get_runtime_manager
        
        manager = get_runtime_manager()
        runtime = manager.get_runtime(runtime_id)
        
        if not runtime:
            return jsonify({'success': False, 'error': '运行时不存在'}), 404
        
        return jsonify({
            'success': True,
            'runtime': runtime.get_status()
        })
    
    except Exception as e:
        logger.error(f"获取运行时失败: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@monitoring_api.route('/agent-runtime/<runtime_id>/execute', methods=['POST'])
def execute_runtime(runtime_id):
    """执行Agent运行时任务"""
    try:
        from app.agents.agent_runtime import get_runtime_manager
        
        manager = get_runtime_manager()
        task = request.get_json() or {}
        
        result = manager.execute_task(runtime_id, task)
        
        return jsonify(result)
    
    except Exception as e:
        logger.error(f"执行运行时任务失败: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@monitoring_api.route('/agent-runtime/local/register-tool', methods=['POST'])
def register_tool():
    """注册工具到本地Agent"""
    try:
        from app.agents.agent_runtime import get_runtime_manager
        
        manager = get_runtime_manager()
        data = request.get_json() or {}
        
        tool_name = data.get('tool_name')
        
        if not tool_name:
            return jsonify({'success': False, 'error': 'tool_name参数必填'}), 400
        
        def sample_tool(params):
            return {'tool_name': tool_name, 'params': params, 'result': '工具执行成功'}
        
        manager.register_tool(tool_name, sample_tool)
        
        return jsonify({
            'success': True,
            'message': f'工具 {tool_name} 已注册'
        })
    
    except Exception as e:
        logger.error(f"注册工具失败: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@monitoring_api.route('/health', methods=['GET'])
def health_check():
    """健康检查"""
    try:
        from app.agents.monitoring_collector import get_monitoring_collector
        from app.agents.github_integration import get_github_integration
        from app.agents.agent_runtime import get_runtime_manager
        
        collector = get_monitoring_collector()
        github = get_github_integration()
        runtime_manager = get_runtime_manager()
        
        return jsonify({
            'success': True,
            'monitoring': 'running',
            'github_connected': github.is_connected(),
            'runtimes_count': len(runtime_manager.get_all_runtimes())
        })
    
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500
