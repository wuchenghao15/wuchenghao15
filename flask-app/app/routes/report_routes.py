"""报表API路由 - MTSCOS AI项目"""

from flask import Blueprint, request, session
from app.services.report_service import ReportService
from app.utils.api_response import APIResponse
from app.utils.permission import require_login, require_admin

report_api = Blueprint('report_api', __name__)


@report_api.route('/api/reports/types', methods=['GET'])
@require_login
def get_report_types():
    """获取可用报表类型"""
    types = ReportService.get_report_types()
    return APIResponse.success(types)


@report_api.route('/api/reports/daily', methods=['GET'])
@require_admin
def get_daily_report():
    """获取日报"""
    user_id = request.args.get('user_id')
    report = ReportService.generate_daily_report(user_id)
    return APIResponse.success(report)


@report_api.route('/api/reports/weekly', methods=['GET'])
@require_admin
def get_weekly_report():
    """获取周报"""
    user_id = request.args.get('user_id')
    report = ReportService.generate_weekly_report(user_id)
    return APIResponse.success(report)


@report_api.route('/api/reports/user', methods=['GET'])
@require_login
def get_user_report():
    """获取用户学习报告"""
    user_id = session.get('user_id')
    report = ReportService.generate_user_report(user_id)
    return APIResponse.success(report)


@report_api.route('/api/reports/exam/<int:exam_id>', methods=['GET'])
@require_login
def get_exam_report(exam_id):
    """获取考试报告"""
    report = ReportService.generate_exam_report(exam_id)
    return APIResponse.success(report)