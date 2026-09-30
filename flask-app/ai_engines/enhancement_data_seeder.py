#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
增强管理器深度数据填充脚本
填充: 权限规则矩阵 / AI模型库 / 集群节点 / 题库分类 / 端口分配 / 前端布局
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from ai_engines.system_enhancement_manager import system_enhancement_manager as mgr


def seed_permission_rules():
    """填充完整权限规则矩阵 (40+规则)"""
    rules = [
        # 超级管理员 - 全权限
        {'rule_id': 'rule_super_admin_full', 'role': 'super_admin', 'resource': '*', 'action_name': '*', 'allowed': 1, 'priority': 200},
        # 硬件管理员 - 全权限
        {'rule_id': 'rule_hw_admin_full', 'role': 'hardware_admin', 'resource': '*', 'action_name': '*', 'allowed': 1, 'priority': 200},
        {'rule_id': 'rule_hw_vikey_full', 'role': 'hardware_vikey_admin', 'resource': '*', 'action_name': '*', 'allowed': 1, 'priority': 200},
        # 管理员 - 管理+只读敏感数据
        {'rule_id': 'rule_admin_manage', 'role': 'admin', 'resource': '/admin_app', 'action_name': 'GET', 'allowed': 1, 'priority': 100},
        {'rule_id': 'rule_admin_settings', 'role': 'admin', 'resource': '/settings', 'action_name': 'GET', 'allowed': 1, 'priority': 100},
        {'rule_id': 'rule_admin_dashboard', 'role': 'admin', 'resource': '/dashboard', 'action_name': 'GET', 'allowed': 1, 'priority': 100},
        {'rule_id': 'rule_admin_enhancement', 'role': 'admin', 'resource': '/enhancement', 'action_name': 'GET', 'allowed': 1, 'priority': 100},
        {'rule_id': 'rule_admin_api_enh', 'role': 'admin', 'resource': '/api/enhancement/*', 'action_name': '*', 'allowed': 1, 'priority': 100},
        {'rule_id': 'rule_admin_users_view', 'role': 'admin', 'resource': '/api/users', 'action_name': 'GET', 'allowed': 1, 'priority': 90},
        {'rule_id': 'rule_admin_sensitive_edit', 'role': 'admin', 'resource': '/api/sensitive/*', 'action_name': 'POST', 'allowed': 0, 'priority': 50},
        # 教师权限
        {'rule_id': 'rule_teacher_home', 'role': 'teacher', 'resource': '/teacher', 'action_name': 'GET', 'allowed': 1, 'priority': 60},
        {'rule_id': 'rule_teacher_exam', 'role': 'teacher', 'resource': '/api/exams', 'action_name': 'GET', 'allowed': 1, 'priority': 60},
        {'rule_id': 'rule_teacher_exam_create', 'role': 'teacher', 'resource': '/api/exams', 'action_name': 'POST', 'allowed': 1, 'priority': 60},
        {'rule_id': 'rule_teacher_questions', 'role': 'teacher', 'resource': '/api/questions', 'action_name': 'GET', 'allowed': 1, 'priority': 60},
        {'rule_id': 'rule_teacher_questions_create', 'role': 'teacher', 'resource': '/api/questions', 'action_name': 'POST', 'allowed': 1, 'priority': 60},
        {'rule_id': 'rule_teacher_students', 'role': 'teacher', 'resource': '/api/students', 'action_name': 'GET', 'allowed': 1, 'priority': 60},
        {'rule_id': 'rule_teacher_reports', 'role': 'teacher', 'resource': '/api/reports', 'action_name': 'GET', 'allowed': 1, 'priority': 60},
        {'rule_id': 'rule_teacher_grade', 'role': 'teacher', 'resource': '/api/grading', 'action_name': 'POST', 'allowed': 1, 'priority': 60},
        # 学生权限
        {'rule_id': 'rule_student_exam', 'role': 'student', 'resource': '/exam_system', 'action_name': 'GET', 'allowed': 1, 'priority': 50},
        {'rule_id': 'rule_student_exam_api', 'role': 'student', 'resource': '/api/exams', 'action_name': 'GET', 'allowed': 1, 'priority': 50},
        {'rule_id': 'rule_student_tests', 'role': 'student', 'resource': '/exam_system/tests', 'action_name': 'GET', 'allowed': 1, 'priority': 50},
        {'rule_id': 'rule_student_practice', 'role': 'student', 'resource': '/exam_system/practice', 'action_name': 'GET', 'allowed': 1, 'priority': 50},
        {'rule_id': 'rule_student_results', 'role': 'student', 'resource': '/api/my_results', 'action_name': 'GET', 'allowed': 1, 'priority': 50},
        {'rule_id': 'rule_student_wrong_book', 'role': 'student', 'resource': '/api/wrong_book', 'action_name': 'GET', 'allowed': 1, 'priority': 50},
        {'rule_id': 'rule_student_ai_chat', 'role': 'student', 'resource': '/ai-chat', 'action_name': 'GET', 'allowed': 1, 'priority': 50},
        {'rule_id': 'rule_student_k12', 'role': 'student', 'resource': '/k12', 'action_name': 'GET', 'allowed': 1, 'priority': 50},
        {'rule_id': 'rule_student_settings', 'role': 'student', 'resource': '/settings', 'action_name': 'GET', 'allowed': 0, 'priority': 10},
        {'rule_id': 'rule_student_admin', 'role': 'student', 'resource': '/admin_app', 'action_name': 'GET', 'allowed': 0, 'priority': 10},
        # VIP学生额外权限
        {'rule_id': 'rule_student_vip_exam', 'role': 'student_vip', 'resource': '/exam_system', 'action_name': 'GET', 'allowed': 1, 'priority': 55},
        {'rule_id': 'rule_student_vip_practice', 'role': 'student_vip', 'resource': '/exam_system/practice', 'action_name': 'GET', 'allowed': 1, 'priority': 55},
        {'rule_id': 'rule_student_vip_ai', 'role': 'student_vip', 'resource': '/ai-chat', 'action_name': 'GET', 'allowed': 1, 'priority': 55},
        # 设计师权限
        {'rule_id': 'rule_designer_arduino', 'role': 'designer', 'resource': '/arduino', 'action_name': 'GET', 'allowed': 1, 'priority': 55},
        {'rule_id': 'rule_designer_upload', 'role': 'designer', 'resource': '/api/upload', 'action_name': 'POST', 'allowed': 1, 'priority': 55},
        # 访客权限
        {'rule_id': 'rule_guest_login', 'role': 'guest', 'resource': '/login', 'action_name': 'GET', 'allowed': 1, 'priority': 10},
        {'rule_id': 'rule_guest_register', 'role': 'guest', 'resource': '/register', 'action_name': 'GET', 'allowed': 1, 'priority': 10},
        {'rule_id': 'rule_guest_k12', 'role': 'guest', 'resource': '/k12', 'action_name': 'GET', 'allowed': 1, 'priority': 10},
        {'rule_id': 'rule_guest_status', 'role': 'guest', 'resource': '/api/k12/status', 'action_name': 'GET', 'allowed': 1, 'priority': 10},
        # 研究员权限
        {'rule_id': 'rule_researcher_data', 'role': 'researcher', 'resource': '/api/analytics', 'action_name': 'GET', 'allowed': 1, 'priority': 55},
        {'rule_id': 'rule_researcher_reports', 'role': 'researcher', 'resource': '/api/reports', 'action_name': 'GET', 'allowed': 1, 'priority': 55},
    ]
    count = 0
    for rule in rules:
        r = mgr.manage_permission_rules('upsert', rule)
        if r.get('success'):
            count += 1
    print(f'✓ 权限规则填充完成: {count}/{len(rules)} 条')
    return count


def seed_ai_models():
    """填充AI模型库 (15+模型)"""
    models = [
        # 大语言模型
        {'model_id': 'model_gpt4', 'model_name': 'GPT-4', 'version': '1.0.0', 'status': 'registered', 'performance_score': 95.0, 'config': {'provider': 'openai', 'type': 'llm', 'context': '8k'}},
        {'model_id': 'model_gpt4_turbo', 'model_name': 'GPT-4-Turbo', 'version': '1.0.0', 'status': 'registered', 'performance_score': 96.0, 'config': {'provider': 'openai', 'type': 'llm', 'context': '128k'}},
        {'model_id': 'model_gpt35', 'model_name': 'GPT-3.5-Turbo', 'version': '1.0.0', 'status': 'registered', 'performance_score': 88.0, 'config': {'provider': 'openai', 'type': 'llm', 'context': '16k'}},
        {'model_id': 'model_claude3_opus', 'model_name': 'Claude-3-Opus', 'version': '1.0.0', 'status': 'registered', 'performance_score': 94.0, 'config': {'provider': 'anthropic', 'type': 'llm', 'context': '200k'}},
        {'model_id': 'model_claude3_sonnet', 'model_name': 'Claude-3-Sonnet', 'version': '1.0.0', 'status': 'registered', 'performance_score': 91.0, 'config': {'provider': 'anthropic', 'type': 'llm', 'context': '200k'}},
        {'model_id': 'model_claude3_haiku', 'model_name': 'Claude-3-Haiku', 'version': '1.0.0', 'status': 'registered', 'performance_score': 85.0, 'config': {'provider': 'anthropic', 'type': 'llm', 'context': '200k'}},
        {'model_id': 'model_qwen72b', 'model_name': 'Qwen-72B', 'version': '1.0.0', 'status': 'registered', 'performance_score': 87.0, 'config': {'provider': 'alibaba', 'type': 'llm', 'context': '32k'}},
        {'model_id': 'model_qwen14b', 'model_name': 'Qwen-14B', 'version': '1.0.0', 'status': 'registered', 'performance_score': 82.0, 'config': {'provider': 'alibaba', 'type': 'llm', 'context': '8k'}},
        {'model_id': 'model_deepseek', 'model_name': 'DeepSeek-Coder', 'version': '1.0.0', 'status': 'registered', 'performance_score': 89.0, 'config': {'provider': 'deepseek', 'type': 'llm', 'context': '64k'}},
        {'model_id': 'model_chatglm', 'model_name': 'ChatGLM3', 'version': '1.0.0', 'status': 'registered', 'performance_score': 83.0, 'config': {'provider': 'zhipu', 'type': 'llm', 'context': '32k'}},
        # 嵌入模型
        {'model_id': 'model_ada002', 'model_name': 'text-embedding-ada-002', 'version': '1.0.0', 'status': 'registered', 'performance_score': 90.0, 'config': {'provider': 'openai', 'type': 'embedding', 'dim': 1536}},
        {'model_id': 'model_bge_large', 'model_name': 'bge-large-zh', 'version': '1.0.0', 'status': 'registered', 'performance_score': 88.0, 'config': {'provider': 'baidu', 'type': 'embedding', 'dim': 1024}},
        # 多模态模型
        {'model_id': 'model_whisper', 'model_name': 'Whisper-Large', 'version': '1.0.0', 'status': 'registered', 'performance_score': 87.0, 'config': {'provider': 'openai', 'type': 'audio', 'languages': 99}},
        {'model_id': 'model_dalle3', 'model_name': 'DALL-E-3', 'version': '1.0.0', 'status': 'registered', 'performance_score': 86.0, 'config': {'provider': 'openai', 'type': 'image'}},
        {'model_id': 'model_qwen_vl', 'model_name': 'Qwen-VL', 'version': '1.0.0', 'status': 'registered', 'performance_score': 84.0, 'config': {'provider': 'alibaba', 'type': 'multimodal'}},
        # 本地模型
        {'model_id': 'model_local_mtscos', 'model_name': 'MTSCOS-Local-LLM', 'version': '1.0.0', 'status': 'registered', 'performance_score': 78.0, 'config': {'provider': 'local', 'type': 'llm', 'context': '4k'}},
    ]
    count = 0
    for model in models:
        r = mgr.register_model(model)
        if r.get('success'):
            count += 1
    print(f'✓ AI模型填充完成: {count}/{len(models)} 个')
    return count


def seed_cluster_nodes():
    """填充集群节点 (master/worker/backup)"""
    nodes = [
        {'node_id': 'node_master_01', 'node_type': 'master', 'address': '127.0.0.1:8888', 'status': 'online', 'load': 0.0},
        {'node_id': 'node_worker_01', 'node_type': 'worker', 'address': '127.0.0.1:8889', 'status': 'online', 'load': 15.5},
        {'node_id': 'node_worker_02', 'node_type': 'worker', 'address': '127.0.0.1:8890', 'status': 'online', 'load': 22.3},
        {'node_id': 'node_worker_03', 'node_type': 'worker', 'address': '127.0.0.1:8891', 'status': 'online', 'load': 8.7},
        {'node_id': 'node_backup_01', 'node_type': 'backup', 'address': '127.0.0.1:8892', 'status': 'standby', 'load': 0.0},
    ]
    count = 0
    for node in nodes:
        r = mgr.manage_db_cluster('add', node)
        if r.get('success'):
            count += 1
    print(f'✓ 集群节点填充完成: {count}/{len(nodes)} 个')
    return count


def seed_ai_nodes():
    """填充AI节点"""
    nodes = [
        {'node_id': 'ai_node_01', 'node_name': '本地AI节点-主', 'model': 'GPT-4', 'status': 'idle', 'load': 0.0, 'capacity': 10},
        {'node_id': 'ai_node_02', 'node_name': '本地AI节点-副', 'model': 'Claude-3-Opus', 'status': 'idle', 'load': 0.0, 'capacity': 8},
        {'node_id': 'ai_node_03', 'node_name': '推理节点-1', 'model': 'Qwen-72B', 'status': 'idle', 'load': 0.0, 'capacity': 15},
        {'node_id': 'ai_node_04', 'node_name': '嵌入节点', 'model': 'text-embedding-ada-002', 'status': 'idle', 'load': 0.0, 'capacity': 50},
        {'node_id': 'ai_node_05', 'node_name': '语音节点', 'model': 'Whisper-Large', 'status': 'idle', 'load': 0.0, 'capacity': 5},
    ]
    count = 0
    for node in nodes:
        r = mgr.manage_ai_nodes('upsert', node)
        if r.get('success'):
            count += 1
    print(f'✓ AI节点填充完成: {count}/{len(nodes)} 个')
    return count


def seed_question_categories():
    """填充题库分类体系 (K12+成人教育)"""
    categories = [
        # 九年制义务教育 - 小学
        {'category_id': 'cat_primary_chinese', 'name': '小学语文', 'parent_id': 'cat_k9', 'description': '小学1-6年级语文', 'question_count': 0},
        {'category_id': 'cat_primary_math', 'name': '小学数学', 'parent_id': 'cat_k9', 'description': '小学1-6年级数学', 'question_count': 0},
        {'category_id': 'cat_primary_english', 'name': '小学英语', 'parent_id': 'cat_k9', 'description': '小学3-6年级英语', 'question_count': 0},
        {'category_id': 'cat_primary_science', 'name': '小学科学', 'parent_id': 'cat_k9', 'description': '小学科学课程', 'question_count': 0},
        # 九年制义务教育 - 初中
        {'category_id': 'cat_junior_chinese', 'name': '初中语文', 'parent_id': 'cat_k9', 'description': '初中1-3年级语文', 'question_count': 0},
        {'category_id': 'cat_junior_math', 'name': '初中数学', 'parent_id': 'cat_k9', 'description': '初中1-3年级数学', 'question_count': 0},
        {'category_id': 'cat_junior_english', 'name': '初中英语', 'parent_id': 'cat_k9', 'description': '初中1-3年级英语', 'question_count': 0},
        {'category_id': 'cat_junior_physics', 'name': '初中物理', 'parent_id': 'cat_k9', 'description': '初中物理', 'question_count': 0},
        {'category_id': 'cat_junior_chemistry', 'name': '初中化学', 'parent_id': 'cat_k9', 'description': '初中化学', 'question_count': 0},
        {'category_id': 'cat_junior_biology', 'name': '初中生物', 'parent_id': 'cat_k9', 'description': '初中生物', 'question_count': 0},
        {'category_id': 'cat_junior_history', 'name': '初中历史', 'parent_id': 'cat_k9', 'description': '初中历史', 'question_count': 0},
        {'category_id': 'cat_junior_geography', 'name': '初中地理', 'parent_id': 'cat_k9', 'description': '初中地理', 'question_count': 0},
        {'category_id': 'cat_junior_politics', 'name': '初中政治', 'parent_id': 'cat_k9', 'description': '初中道德与法治', 'question_count': 0},
        # 九年制义务教育 - 高中
        {'category_id': 'cat_senior_chinese', 'name': '高中语文', 'parent_id': 'cat_k12', 'description': '高中1-3年级语文', 'question_count': 0},
        {'category_id': 'cat_senior_math', 'name': '高中数学', 'parent_id': 'cat_k12', 'description': '高中1-3年级数学', 'question_count': 0},
        {'category_id': 'cat_senior_english', 'name': '高中英语', 'parent_id': 'cat_k12', 'description': '高中1-3年级英语', 'question_count': 0},
        {'category_id': 'cat_senior_physics', 'name': '高中物理', 'parent_id': 'cat_k12', 'description': '高中物理', 'question_count': 0},
        {'category_id': 'cat_senior_chemistry', 'name': '高中化学', 'parent_id': 'cat_k12', 'description': '高中化学', 'question_count': 0},
        {'category_id': 'cat_senior_biology', 'name': '高中生物', 'parent_id': 'cat_k12', 'description': '高中生物', 'question_count': 0},
        {'category_id': 'cat_senior_japanese', 'name': '高中日语', 'parent_id': 'cat_k12', 'description': '高中日语（听力题）', 'question_count': 0},
        # 成人教育
        {'category_id': 'cat_adult_language', 'name': '成人-语言考试', 'parent_id': 'cat_adult', 'description': '英语四六级/雅思/托福/日语能力考', 'question_count': 0},
        {'category_id': 'cat_adult_career', 'name': '成人-职业资格', 'parent_id': 'cat_adult', 'description': '各类职业资格考试', 'question_count': 0},
        {'category_id': 'cat_adult_degree', 'name': '成人-学历提升', 'parent_id': 'cat_adult', 'description': '成人高考/自考', 'question_count': 0},
        {'category_id': 'cat_adult_skill', 'name': '成人-专业技能', 'parent_id': 'cat_adult', 'description': 'IT/财务/管理等专业技能', 'question_count': 0},
    ]
    count = 0
    for cat in categories:
        r = mgr.manage_question_categories('upsert', cat)
        if r.get('success'):
            count += 1
    print(f'✓ 题库分类填充完成: {count}/{len(categories)} 个')
    return count


def seed_ports():
    """填充端口分配"""
    ports = [
        {'service': 'mtscos_web', 'preferred': 8888},
        {'service': 'mtscos_api', 'preferred': 8889},
        {'service': 'mtscos_ai_engine', 'preferred': 8890},
        {'service': 'mtscos_monitor', 'preferred': 8891},
        {'service': 'mtscos_backup', 'preferred': 8892},
        {'service': 'mtscos_websocket', 'preferred': 8893},
    ]
    count = 0
    for p in ports:
        r = mgr.allocate_port(p['service'], p['preferred'])
        if r.get('success'):
            count += 1
    print(f'✓ 端口分配填充完成: {count}/{len(ports)} 个')
    return count


def seed_frontend_layouts():
    """填充前端布局配置"""
    layouts = [
        {'layout_id': 'layout_default', 'layout_name': '默认布局', 'config': {'sidebar': True, 'header': True, 'footer': False, 'sidebar_collapsed': False}, 'theme': 'blue', 'is_active': 1},
        {'layout_id': 'layout_dark', 'layout_name': '暗色主题', 'config': {'sidebar': True, 'header': True, 'footer': True, 'sidebar_collapsed': False}, 'theme': 'dark', 'is_active': 0},
        {'layout_id': 'layout_compact', 'layout_name': '紧凑布局', 'config': {'sidebar': True, 'header': True, 'footer': False, 'sidebar_collapsed': True}, 'theme': 'green', 'is_active': 0},
        {'layout_id': 'layout_fullscreen', 'layout_name': '全屏布局', 'config': {'sidebar': False, 'header': False, 'footer': False, 'sidebar_collapsed': True}, 'theme': 'purple', 'is_active': 0},
        {'layout_id': 'layout_minimal', 'layout_name': '极简布局', 'config': {'sidebar': False, 'header': True, 'footer': False, 'sidebar_collapsed': True}, 'theme': 'orange', 'is_active': 0},
    ]
    count = 0
    for layout in layouts:
        r = mgr.manage_layout_config('upsert', layout)
        if r.get('success'):
            count += 1
    print(f'✓ 前端布局填充完成: {count}/{len(layouts)} 个')
    return count


def run_all_seeds():
    """运行所有数据填充"""
    print('=' * 60)
    print('  增强管理器深度数据填充')
    print('=' * 60)
    total = 0
    total += seed_permission_rules()
    total += seed_ai_models()
    total += seed_cluster_nodes()
    total += seed_ai_nodes()
    total += seed_question_categories()
    total += seed_ports()
    total += seed_frontend_layouts()
    print('-' * 60)
    print(f'  总计填充: {total} 条数据')
    print('=' * 60)
    # 验证
    status = mgr.get_enhancement_status()
    print(f'  模块数量: {status.get("module_count", 0)}')
    db_health = mgr.db_health_check()
    print(f'  数据库健康: {db_health.get("healthy")}/{db_health.get("total")}')
    perf = mgr.analyze_performance()
    print(f'  性能评分: {perf.get("performance_score")} ({perf.get("grade")})')


if __name__ == '__main__':
    run_all_seeds()
