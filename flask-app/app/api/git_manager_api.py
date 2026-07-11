# -*- coding: utf-8 -*-
"""
Git管理AI员工API
提供GitHub和本地Git仓库的自动化管理接口
"""

from flask import Blueprint, jsonify, request
import logging

logger = logging.getLogger(__name__)

git_manager_api = Blueprint('git_manager_api', __name__)


@git_manager_api.route('/api/git/status', methods=['GET'])
def git_status():
    """获取Git状态"""
    try:
        from ai_engines.git_manager_ai import get_git_manager_ai
        git_manager = get_git_manager_ai()
        status = git_manager.check_git_status()
        return jsonify(status)
    
    except Exception as e:
        logger.error(f"获取Git状态失败: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@git_manager_api.route('/api/git/commit', methods=['POST'])
def git_commit():
    """自动提交更改"""
    try:
        data = request.get_json()
        commit_message = data.get('message')
        
        from ai_engines.git_manager_ai import get_git_manager_ai
        git_manager = get_git_manager_ai()
        result = git_manager.auto_commit_changes(commit_message)
        
        return jsonify(result)
    
    except Exception as e:
        logger.error(f"提交失败: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@git_manager_api.route('/api/git/push', methods=['POST'])
def git_push():
    """推送到远程"""
    try:
        data = request.get_json()
        remote = data.get('remote', 'origin')
        branch = data.get('branch')
        
        from ai_engines.git_manager_ai import get_git_manager_ai
        git_manager = get_git_manager_ai()
        result = git_manager.auto_push_to_remote(remote, branch)
        
        return jsonify(result)
    
    except Exception as e:
        logger.error(f"推送失败: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@git_manager_api.route('/api/git/pull', methods=['POST'])
def git_pull():
    """从远程拉取"""
    try:
        data = request.get_json()
        remote = data.get('remote', 'origin')
        branch = data.get('branch')
        
        from ai_engines.git_manager_ai import get_git_manager_ai
        git_manager = get_git_manager_ai()
        result = git_manager.pull_from_remote(remote, branch)
        
        return jsonify(result)
    
    except Exception as e:
        logger.error(f"拉取失败: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@git_manager_api.route('/api/git/backup', methods=['POST'])
def git_backup():
    """创建备份分支"""
    try:
        data = request.get_json()
        branch_name = data.get('branch_name')
        
        from ai_engines.git_manager_ai import get_git_manager_ai
        git_manager = get_git_manager_ai()
        result = git_manager.create_backup_branch(branch_name)
        
        return jsonify(result)
    
    except Exception as e:
        logger.error(f"备份失败: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@git_manager_api.route('/api/git/sync', methods=['POST'])
def git_sync():
    """同步并备份"""
    try:
        from ai_engines.git_manager_ai import get_git_manager_ai
        git_manager = get_git_manager_ai()
        result = git_manager.sync_and_backup()
        
        return jsonify(result)
    
    except Exception as e:
        logger.error(f"同步备份失败: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@git_manager_api.route('/api/git/history', methods=['GET'])
def git_history():
    """获取操作历史"""
    try:
        limit = request.args.get('limit', 50, type=int)
        
        from ai_engines.git_manager_ai import get_git_manager_ai
        git_manager = get_git_manager_ai()
        history = git_manager.get_operation_history(limit)
        
        return jsonify({
            'success': True,
            'history': history,
            'total': len(history)
        })
    
    except Exception as e:
        logger.error(f"获取历史失败: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500