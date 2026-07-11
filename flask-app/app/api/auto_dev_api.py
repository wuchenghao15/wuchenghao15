# -*- coding: utf-8 -*-
"""
综合API蓝图 - 统一API接口
整合审批系统、测试框架、Git操作、依赖扫描、迭代引擎、运维报告的API
"""
import json
import logging
from datetime import datetime
from flask import Blueprint, request, jsonify

from app.agents.approval_manager import get_approval_manager, OperationLevel, ApprovalStatus
from app.agents.auto_test_runner import get_test_runner, TestType
from app.agents.git_auto_ops import get_git_auto_ops
from app.agents.dependency_scanner import get_dependency_scanner
from app.agents.iteration_engine import get_iteration_engine
from app.agents.ops_report_generator import get_report_generator

logger = logging.getLogger(__name__)

auto_dev_api = Blueprint('auto_dev_api', __name__, url_prefix='/api/auto-dev')


@auto_dev_api.route('/health', methods=['GET'])
def health_check():
    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.now().isoformat()
    })


@auto_dev_api.route('/approval/create', methods=['POST'])
def create_approval():
    try:
        data = request.get_json()
        operation_type = data.get('operation_type', '')
        operation_level = data.get('operation_level', 'normal')
        description = data.get('description', '')
        details = data.get('details', {})
        
        approval_manager = get_approval_manager()
        approval_id = approval_manager.create_approval(
            operation_type, operation_level, description, details
        )
        
        return jsonify({
            'success': True,
            'approval_id': approval_id
        })
    
    except Exception as e:
        logger.error(f"[API] 创建审批失败: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@auto_dev_api.route('/approval/list', methods=['GET'])
def list_approvals():
    try:
        status = request.args.get('status', '')
        approval_manager = get_approval_manager()
        
        approvals = approval_manager.get_approvals()
        if status:
            approvals = [a for a in approvals if a['status'] == status]
        
        return jsonify({'success': True, 'approvals': approvals})
    
    except Exception as e:
        logger.error(f"[API] 获取审批列表失败: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@auto_dev_api.route('/approval/<approval_id>/approve', methods=['POST'])
def approve_approval(approval_id):
    try:
        data = request.get_json()
        approver = data.get('approver', 'admin')
        comment = data.get('comment', '')
        
        approval_manager = get_approval_manager()
        success = approval_manager.approve(approval_id, approver, comment)
        
        return jsonify({'success': success})
    
    except Exception as e:
        logger.error(f"[API] 审批通过失败: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@auto_dev_api.route('/approval/<approval_id>/reject', methods=['POST'])
def reject_approval(approval_id):
    try:
        data = request.get_json()
        approver = data.get('approver', 'admin')
        reason = data.get('reason', '')
        
        approval_manager = get_approval_manager()
        success = approval_manager.reject(approval_id, approver, reason)
        
        return jsonify({'success': success})
    
    except Exception as e:
        logger.error(f"[API] 审批拒绝失败: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@auto_dev_api.route('/test/unit', methods=['POST'])
def run_unit_tests():
    try:
        test_runner = get_test_runner()
        result = test_runner.run_unit_tests()
        
        return jsonify({'success': True, 'result': result})
    
    except Exception as e:
        logger.error(f"[API] 运行单元测试失败: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@auto_dev_api.route('/test/api', methods=['POST'])
def run_api_tests():
    try:
        test_runner = get_test_runner()
        result = test_runner.run_api_tests()
        
        return jsonify({'success': True, 'result': result})
    
    except Exception as e:
        logger.error(f"[API] 运行API测试失败: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@auto_dev_api.route('/test/page', methods=['POST'])
def run_page_tests():
    try:
        test_runner = get_test_runner()
        result = test_runner.run_page_tests()
        
        return jsonify({'success': True, 'result': result})
    
    except Exception as e:
        logger.error(f"[API] 运行页面测试失败: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@auto_dev_api.route('/test/stress', methods=['POST'])
def run_stress_test():
    try:
        data = request.get_json()
        duration = data.get('duration', 30)
        concurrency = data.get('concurrency', 10)
        
        test_runner = get_test_runner()
        result = test_runner.run_stress_test(duration, concurrency)
        
        return jsonify({'success': True, 'result': result})
    
    except Exception as e:
        logger.error(f"[API] 运行压力测试失败: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@auto_dev_api.route('/test/all', methods=['POST'])
def run_all_tests():
    try:
        test_runner = get_test_runner()
        result = test_runner.run_all_tests()
        
        return jsonify({'success': True, 'result': result})
    
    except Exception as e:
        logger.error(f"[API] 运行全部测试失败: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@auto_dev_api.route('/git/branch/list', methods=['GET'])
def list_git_branches():
    try:
        git_ops = get_git_auto_ops()
        branches = git_ops.list_branches()
        
        return jsonify({'success': True, 'branches': branches})
    
    except Exception as e:
        logger.error(f"[API] 获取分支列表失败: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@auto_dev_api.route('/git/branch/checkout', methods=['POST'])
def checkout_git_branch():
    try:
        data = request.get_json()
        branch_name = data.get('branch_name', '')
        
        git_ops = get_git_auto_ops()
        result = git_ops.checkout_branch(branch_name)
        
        return jsonify({'success': True, 'result': result})
    
    except Exception as e:
        logger.error(f"[API] 切换分支失败: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@auto_dev_api.route('/git/pull', methods=['POST'])
def git_pull():
    try:
        data = request.get_json()
        branch_name = data.get('branch_name', '')
        
        git_ops = get_git_auto_ops()
        result = git_ops.pull(branch_name)
        
        return jsonify({'success': True, 'result': result})
    
    except Exception as e:
        logger.error(f"[API] 拉取代码失败: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@auto_dev_api.route('/git/modify', methods=['POST'])
def modify_git_file():
    try:
        data = request.get_json()
        file_path = data.get('file_path', '')
        changes = data.get('changes', {})
        
        git_ops = get_git_auto_ops()
        result = git_ops.modify_file(file_path, changes)
        
        return jsonify({'success': result['status'] == 'completed', 'result': result})
    
    except Exception as e:
        logger.error(f"[API] 修改文件失败: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@auto_dev_api.route('/git/commit', methods=['POST'])
def git_commit():
    try:
        data = request.get_json()
        message = data.get('message', '')
        files = data.get('files', [])
        
        git_ops = get_git_auto_ops()
        result = git_ops.commit(message, files)
        
        return jsonify({'success': result['status'] == 'completed', 'result': result})
    
    except Exception as e:
        logger.error(f"[API] 提交代码失败: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@auto_dev_api.route('/git/push', methods=['POST'])
def git_push():
    try:
        data = request.get_json()
        branch_name = data.get('branch_name', '')
        
        git_ops = get_git_auto_ops()
        result = git_ops.push(branch_name)
        
        return jsonify({'success': result['status'] == 'completed', 'result': result})
    
    except Exception as e:
        logger.error(f"[API] 推送代码失败: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@auto_dev_api.route('/dependency/scan', methods=['POST'])
def scan_dependencies():
    try:
        scanner = get_dependency_scanner()
        result = scanner.scan_vulnerabilities()
        
        return jsonify({'success': True, 'result': result})
    
    except Exception as e:
        logger.error(f"[API] 扫描依赖失败: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@auto_dev_api.route('/dependency/scans', methods=['GET'])
def list_scan_results():
    try:
        scanner = get_dependency_scanner()
        results = scanner.get_scan_results()
        
        return jsonify({'success': True, 'results': results})
    
    except Exception as e:
        logger.error(f"[API] 获取扫描结果失败: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@auto_dev_api.route('/dependency/upgrade', methods=['POST'])
def execute_upgrade():
    try:
        data = request.get_json()
        task_id = data.get('task_id', '')
        
        scanner = get_dependency_scanner()
        result = scanner.execute_upgrade(task_id)
        
        return jsonify(result)
    
    except Exception as e:
        logger.error(f"[API] 执行升级失败: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@auto_dev_api.route('/dependency/upgrade-tasks', methods=['GET'])
def list_upgrade_tasks():
    try:
        scanner = get_dependency_scanner()
        tasks = scanner.get_upgrade_tasks()
        
        return jsonify({'success': True, 'tasks': tasks})
    
    except Exception as e:
        logger.error(f"[API] 获取升级任务失败: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@auto_dev_api.route('/iteration/run', methods=['POST'])
def run_iteration():
    try:
        engine = get_iteration_engine()
        result = engine.run_iteration()
        
        return jsonify({'success': True, 'result': result})
    
    except Exception as e:
        logger.error(f"[API] 运行迭代失败: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@auto_dev_api.route('/iteration/plans', methods=['GET'])
def list_iteration_plans():
    try:
        engine = get_iteration_engine()
        plans = engine.get_iteration_plans()
        
        return jsonify({'success': True, 'plans': plans})
    
    except Exception as e:
        logger.error(f"[API] 获取迭代计划失败: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@auto_dev_api.route('/report/generate', methods=['POST'])
def generate_report():
    try:
        generator = get_report_generator()
        result = generator.generate_daily_report()
        
        return jsonify({'success': True, 'result': result})
    
    except Exception as e:
        logger.error(f"[API] 生成报告失败: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@auto_dev_api.route('/report/list', methods=['GET'])
def list_reports():
    try:
        generator = get_report_generator()
        reports = generator.get_all_reports()
        
        return jsonify({'success': True, 'reports': reports})
    
    except Exception as e:
        logger.error(f"[API] 获取报告列表失败: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@auto_dev_api.route('/report/<report_id>', methods=['GET'])
def get_report_detail(report_id):
    try:
        generator = get_report_generator()
        report = generator.get_report(report_id)
        
        if report:
            return jsonify({'success': True, 'report': report})
        else:
            return jsonify({'success': False, 'error': '报告不存在'}), 404
    
    except Exception as e:
        logger.error(f"[API] 获取报告详情失败: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500