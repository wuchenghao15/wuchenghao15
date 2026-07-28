#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
MTSCOS 成人教育API接口
=====================
提供成人教育相关的REST API接口，包括：
- 职业导向学习推荐
- 碎片化学习计划
- 学分证书管理
- 企业培训
- 在线考试认证
- 学习社群
"""

from flask import Blueprint, request, jsonify
from ..middlewares.access_control import require_admin
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from adult_education_service import (
    AdultEducationService,
    CorporateTrainingService,
    OnlineExamService,
    LearningCommunityService,
    CAREER_PATHS,
    ADULT_SUBJECTS,
    STUDY_TIME_SLOTS,
    CREDIT_TYPES,
    CERTIFICATE_TYPES,
    CORPORATE_TRAINING_TYPES,
    EXAM_TYPES
)

adult_api = Bluelogger.info('adult_api', __name__)

adult_service = AdultEducationService()
corporate_service = CorporateTrainingService()
exam_service = OnlineExamService()
community_service = LearningCommunityService()


# ========== 职业导向学习 ==========

@adult_api.route('/api/adult/career/path', methods=['POST'])
@require_admin
def set_career_path():
    """设置职业方向"""
    data = request.get_json()
    user_id = data.get('user_id')
    career_path = data.get('career_path')
    target_level = data.get('target_level')

    if not user_id or not career_path:
        return jsonify({'success': False, 'error': '缺少必要参数'}), 400

    result = adult_service.set_career_path(user_id, career_path, target_level)
    return jsonify(result)


@adult_api.route('/api/adult/career/recommendation/<int:user_id>', methods=['GET'])
@require_admin
def get_career_recommendation(user_id):
    """获取职业方向推荐"""
    result = adult_service.get_career_recommendation(user_id)
    return jsonify(result)


# ========== 碎片化学习计划 ==========

@adult_api.route('/api/adult/study/plan', methods=['POST'])
@require_admin
def create_study_plan():
    """创建学习计划"""
    data = request.get_json()
    user_id = data.get('user_id')
    subject = data.get('subject')
    target_level = data.get('target_level')
    weekly_hours = data.get('weekly_hours', 5)
    time_slots = data.get('time_slots', [])
    plan_name = data.get('plan_name')

    if not user_id or not subject or not target_level:
        return jsonify({'success': False, 'error': '缺少必要参数'}), 400

    result = adult_service.create_study_plan(user_id, subject, target_level, weekly_hours, time_slots, plan_name)
    return jsonify(result)


@adult_api.route('/api/adult/study/schedule/<int:user_id>', methods=['GET'])
@require_admin
def get_study_schedule(user_id):
    """获取学习时间表"""
    plan_id = request.args.get('plan_id')
    result = adult_service.get_study_schedule(user_id, plan_id)
    return jsonify(result)


@adult_api.route('/api/adult/study/plan/progress', methods=['PUT'])
@require_admin
def update_plan_progress():
    """更新学习计划进度"""
    data = request.get_json()
    plan_id = data.get('plan_id')
    progress = data.get('progress')

    if not plan_id or progress is None:
        return jsonify({'success': False, 'error': '缺少必要参数'}), 400

    result = adult_service.update_plan_progress(plan_id, progress)
    return jsonify(result)


# ========== 学分管理 ==========

@adult_api.route('/api/adult/credits', methods=['POST'])
@require_admin
def add_credits():
    """增加学分"""
    data = request.get_json()
    user_id = data.get('user_id')
    credit_type = data.get('credit_type')
    credits = data.get('credits')
    subject = data.get('subject')
    activity_id = data.get('activity_id')
    duration_minutes = data.get('duration_minutes', 0)

    if not user_id or not credit_type or credits is None:
        return jsonify({'success': False, 'error': '缺少必要参数'}), 400

    result = adult_service.add_credits(user_id, credit_type, credits, subject, activity_id, duration_minutes)
    return jsonify(result)


@adult_api.route('/api/adult/credits/summary/<int:user_id>', methods=['GET'])
@require_admin
def get_credit_summary(user_id):
    """获取学分汇总"""
    result = adult_service.get_credit_summary(user_id)
    return jsonify(result)


# ========== 证书管理 ==========

@adult_api.route('/api/adult/certificate/issue', methods=['POST'])
@require_admin
def issue_certificate():
    """发放证书"""
    data = request.get_json()
    user_id = data.get('user_id')
    certificate_type = data.get('certificate_type')
    subject = data.get('subject')
    level = data.get('level')
    accuracy = data.get('accuracy', 0.0)

    if not user_id or not certificate_type:
        return jsonify({'success': False, 'error': '缺少必要参数'}), 400

    result = adult_service.issue_certificate(user_id, certificate_type, subject, level, accuracy)
    return jsonify(result)


@adult_api.route('/api/adult/certificate/list/<int:user_id>', methods=['GET'])
@require_admin
def list_certificates(user_id):
    """列出用户证书"""
    result = adult_service.list_certificates(user_id)
    return jsonify(result)


# ========== 学习目标管理 ==========

@adult_api.route('/api/adult/goal', methods=['POST'])
@require_admin
def set_study_goal():
    """设置学习目标"""
    data = request.get_json()
    user_id = data.get('user_id')
    goal_type = data.get('goal_type')
    title = data.get('title')
    target_value = data.get('target_value')
    deadline = data.get('deadline')
    description = data.get('description', '')

    if not user_id or not goal_type or not title or target_value is None or not deadline:
        return jsonify({'success': False, 'error': '缺少必要参数'}), 400

    result = adult_service.set_study_goal(user_id, goal_type, title, target_value, deadline, description)
    return jsonify(result)


@adult_api.route('/api/adult/goal/progress', methods=['PUT'])
@require_admin
def update_goal_progress():
    """更新目标进度"""
    data = request.get_json()
    goal_id = data.get('goal_id')
    current_value = data.get('current_value')

    if not goal_id or current_value is None:
        return jsonify({'success': False, 'error': '缺少必要参数'}), 400

    result = adult_service.update_goal_progress(goal_id, current_value)
    return jsonify(result)


# ========== 班级社群 ==========

@adult_api.route('/api/adult/group', methods=['POST'])
@require_admin
def create_study_group():
    """创建学习班级"""
    data = request.get_json()
    group_name = data.get('group_name')
    career_path = data.get('career_path')
    leader_id = data.get('leader_id')
    subject = data.get('subject')
    description = data.get('description', '')
    max_members = data.get('max_members', 30)

    if not group_name or not career_path or not leader_id:
        return jsonify({'success': False, 'error': '缺少必要参数'}), 400

    result = adult_service.create_study_group(group_name, career_path, leader_id, subject, description, max_members)
    return jsonify(result)


@adult_api.route('/api/adult/group/join', methods=['POST'])
@require_admin
def join_study_group():
    """加入班级"""
    data = request.get_json()
    group_id = data.get('group_id')
    user_id = data.get('user_id')

    if not group_id or not user_id:
        return jsonify({'success': False, 'error': '缺少必要参数'}), 400

    result = adult_service.join_study_group(group_id, user_id)
    return jsonify(result)


# ========== 企业培训 ==========

@adult_api.route('/api/adult/corporate/company', methods=['POST'])
@require_admin
def create_company():
    """创建企业"""
    data = request.get_json()
    company_id = data.get('company_id')
    company_name = data.get('company_name')
    industry = data.get('industry')
    employee_count = data.get('employee_count', 0)
    contact_email = data.get('contact_email', '')

    if not company_id or not company_name:
        return jsonify({'success': False, 'error': '缺少必要参数'}), 400

    result = corporate_service.create_company(company_id, company_name, industry, employee_count, contact_email)
    return jsonify(result)


@adult_api.route('/api/adult/corporate/program', methods=['POST'])
@require_admin
def create_training_program():
    """创建培训项目"""
    data = request.get_json()
    company_id = data.get('company_id')
    program_name = data.get('program_name')
    training_type = data.get('training_type')
    target_role = data.get('target_role')
    duration_hours = data.get('duration_hours')
    required_credits = data.get('required_credits', 0)
    description = data.get('description', '')
    created_by = data.get('created_by')

    if not company_id or not program_name or not training_type or not target_role or duration_hours is None:
        return jsonify({'success': False, 'error': '缺少必要参数'}), 400

    result = corporate_service.create_training_program(company_id, program_name, training_type, target_role,
                                                       duration_hours, required_credits, description, created_by)
    return jsonify(result)


@adult_api.route('/api/adult/corporate/module', methods=['POST'])
@require_admin
def add_training_module():
    """添加培训模块"""
    data = request.get_json()
    program_id = data.get('program_id')
    module_name = data.get('module_name')
    module_order = data.get('module_order')
    duration_hours = data.get('duration_hours')
    description = data.get('description', '')
    required_score = data.get('required_score', 0.8)

    if not program_id or not module_name or module_order is None or duration_hours is None:
        return jsonify({'success': False, 'error': '缺少必要参数'}), 400

    result = corporate_service.add_training_module(program_id, module_name, module_order, duration_hours,
                                                  description, required_score)
    return jsonify(result)


@adult_api.route('/api/adult/corporate/enroll', methods=['POST'])
@require_admin
def enroll_employee():
    """员工报名培训"""
    data = request.get_json()
    user_id = data.get('user_id')
    program_id = data.get('program_id')
    company_id = data.get('company_id')
    employee_role = data.get('employee_role', 'employee')

    if not user_id or not program_id or not company_id:
        return jsonify({'success': False, 'error': '缺少必要参数'}), 400

    result = corporate_service.enroll_employee(user_id, program_id, company_id, employee_role)
    return jsonify(result)


@adult_api.route('/api/adult/corporate/complete', methods=['POST'])
@require_admin
def complete_module():
    """完成培训模块"""
    data = request.get_json()
    user_id = data.get('user_id')
    program_id = data.get('program_id')
    module_id = data.get('module_id')
    score = data.get('score')

    if not user_id or not program_id or not module_id or score is None:
        return jsonify({'success': False, 'error': '缺少必要参数'}), 400

    result = corporate_service.complete_module(user_id, program_id, module_id, score)
    return jsonify(result)


@adult_api.route('/api/adult/corporate/status/<int:user_id>', methods=['GET'])
@require_admin
def get_employee_training_status(user_id):
    """获取员工培训状态"""
    result = corporate_service.get_employee_training_status(user_id)
    return jsonify(result)


# ========== 在线考试认证 ==========

@adult_api.route('/api/adult/exam', methods=['POST'])
@require_admin
def create_exam():
    """创建考试"""
    data = request.get_json()
    exam_name = data.get('exam_name')
    exam_type = data.get('exam_type')
    subject = data.get('subject')
    duration_minutes = data.get('duration_minutes')
    total_score = data.get('total_score')
    passing_score = data.get('passing_score')
    question_count = data.get('question_count')
    created_by = data.get('created_by')

    if not exam_name or not exam_type or not subject or duration_minutes is None or \
            total_score is None or passing_score is None or question_count is None:
        return jsonify({'success': False, 'error': '缺少必要参数'}), 400

    result = exam_service.create_exam(exam_name, exam_type, subject, duration_minutes,
                                      total_score, passing_score, question_count, created_by)
    return jsonify(result)


@adult_api.route('/api/adult/exam/question', methods=['POST'])
@require_admin
def add_exam_question():
    """添加考试题"""
    data = request.get_json()
    exam_id = data.get('exam_id')
    question_text = data.get('question_text')
    question_type = data.get('question_type')
    options = data.get('options', [])
    correct_answer = data.get('correct_answer')
    score = data.get('score')
    question_order = data.get('question_order')

    if not exam_id or not question_text or not question_type or not correct_answer or score is None:
        return jsonify({'success': False, 'error': '缺少必要参数'}), 400

    result = exam_service.add_exam_question(exam_id, question_text, question_type, options,
                                             correct_answer, score, question_order)
    return jsonify(result)


@adult_api.route('/api/adult/exam/start', methods=['POST'])
@require_admin
def start_exam():
    """开始考试"""
    data = request.get_json()
    user_id = data.get('user_id')
    exam_id = data.get('exam_id')

    if not user_id or not exam_id:
        return jsonify({'success': False, 'error': '缺少必要参数'}), 400

    result = exam_service.start_exam(user_id, exam_id)
    return jsonify(result)


@adult_api.route('/api/adult/exam/submit', methods=['POST'])
@require_admin
def submit_exam():
    """提交考试"""
    data = request.get_json()
    record_id = data.get('record_id')
    answers = data.get('answers', {})

    if not record_id:
        return jsonify({'success': False, 'error': '缺少必要参数'}), 400

    result = exam_service.submit_exam(record_id, answers)
    return jsonify(result)


@adult_api.route('/api/adult/exam/certifications/<int:user_id>', methods=['GET'])
@require_admin
def get_user_certifications(user_id):
    """获取用户证书"""
    result = exam_service.get_user_certifications(user_id)
    return jsonify(result)


# ========== 学习社群 ==========

@adult_api.route('/api/adult/community', methods=['POST'])
@require_admin
def create_community():
    """创建社群"""
    data = request.get_json()
    group_name = data.get('group_name')
    category = data.get('category')
    description = data.get('description', '')
    max_members = data.get('max_members', 500)
    privacy = data.get('privacy', 'public')
    created_by = data.get('created_by')

    if not group_name or not category:
        return jsonify({'success': False, 'error': '缺少必要参数'}), 400

    result = community_service.create_community(group_name, category, description, max_members, privacy, created_by)
    return jsonify(result)


@adult_api.route('/api/adult/community/join', methods=['POST'])
@require_admin
def join_community():
    """加入社群"""
    data = request.get_json()
    group_id = data.get('group_id')
    user_id = data.get('user_id')

    if not group_id or not user_id:
        return jsonify({'success': False, 'error': '缺少必要参数'}), 400

    result = community_service.join_community(group_id, user_id)
    return jsonify(result)


# ========== 统计和配置 ==========

@adult_api.route('/api/adult/stats', methods=['GET'])
@require_admin
def get_adult_stats():
    """获取成人教育统计"""
    result = adult_service.get_statistics()
    return jsonify(result)


@adult_api.route('/api/adult/config/career_paths', methods=['GET'])
@require_admin
def get_career_paths_config():
    """获取职业方向配置"""
    return jsonify({'success': True, 'career_paths': CAREER_PATHS})


@adult_api.route('/api/adult/config/subjects', methods=['GET'])
@require_admin
def get_subjects_config():
    """获取科目配置"""
    return jsonify({'success': True, 'subjects': ADULT_SUBJECTS})


@adult_api.route('/api/adult/config/time_slots', methods=['GET'])
@require_admin
def get_time_slots_config():
    """获取时段配置"""
    return jsonify({'success': True, 'time_slots': STUDY_TIME_SLOTS})


@adult_api.route('/api/adult/config/credit_types', methods=['GET'])
@require_admin
def get_credit_types_config():
    """获取学分类型配置"""
    return jsonify({'success': True, 'credit_types': CREDIT_TYPES})


@adult_api.route('/api/adult/config/certificate_types', methods=['GET'])
@require_admin
def get_certificate_types_config():
    """获取证书类型配置"""
    return jsonify({'success': True, 'certificate_types': CERTIFICATE_TYPES})


@adult_api.route('/api/adult/config/training_types', methods=['GET'])
@require_admin
def get_training_types_config():
    """获取培训类型配置"""
    return jsonify({'success': True, 'training_types': CORPORATE_TRAINING_TYPES})


@adult_api.route('/api/adult/config/exam_types', methods=['GET'])
@require_admin
def get_exam_types_config():
    """获取考试类型配置"""
    return jsonify({'success': True, 'exam_types': EXAM_TYPES})