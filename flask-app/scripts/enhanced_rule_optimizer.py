# -*- coding: utf-8 -*-
#!/usr/bin/env python3
"""
增强版智能规则优化系统 - 直接插入优化规则到数据库
"""

import os
import sys
import sqlite3
import hashlib
import base64
import json
import uuid
from datetime import datetime
from typing import Dict, List

# 配置
DATABASE_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'app.db')


def log(message: str, symbol: str = '📋'):
    """日志记录"""
    print(f"[{datetime.now().strftime('%H:%M:%S')}] {symbol} {message}")


def backup_current_rules():
    """备份当前规则"""
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()
    
    # 备份system_rules
    cursor.execute('SELECT * FROM system_rules')
    rules = cursor.fetchall()
    
    for rule in rules:
        backup_id = str(uuid.uuid4())
        try:
            cursor.execute('''
                INSERT INTO system_rules_backup 
                (id, rule_category, rule_name, rule_value, backup_time)
                VALUES (?, ?, ?, ?, ?)
            ''', (
                backup_id,
                rule[1] if len(rule) > 1 else 'unknown',
                rule[2] if len(rule) > 2 else 'unknown',
                json.dumps(rule),
                datetime.now().isoformat()
            ))
        except Exception:
            pass
    
    conn.commit()
    conn.close()
    
    log(f'已备份 {len(rules)} 条规则')
    return len(rules)


def insert_rule(code: str, name: str, description: str, rule_type: str, value, priority: int = 100):
    """插入或更新规则"""
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()
    
    value_json = json.dumps(value, ensure_ascii=False)
    
    # 检查是否已存在
    cursor.execute('SELECT id FROM system_rules WHERE rule_code = ?', (code,))
    existing = cursor.fetchone()
    
    if existing:
        # 更新
        cursor.execute('''
            UPDATE system_rules 
            SET rule_name = ?, rule_description = ?, rule_type = ?, 
                rule_value = ?, is_active = 1, updated_at = ?
            WHERE rule_code = ?
        ''', (name, description, rule_type, value_json, datetime.now().isoformat(), code))
    else:
        # 插入
        try:
            cursor.execute('''
                INSERT INTO system_rules 
                (rule_code, rule_name, rule_description, rule_type, rule_value, is_active, priority, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', (code, name, description, rule_type, value_json, 1, priority, datetime.now().isoformat()))
        except Exception as e:
            log(f'插入规则失败 {code}: {str(e)}', '❌')
    
    conn.commit()
    conn.close()


def optimize_base_rules():
    """优化系统基本规则"""
    log('优化系统基本规则...', '📋')
    
    rules = [
        ('session_timeout', '会话超时时间', '用户会话超时时间(秒)', 'number', 1800, 100),
        ('max_login_attempts', '最大登录尝试', '登录失败最大次数', 'number', 5, 100),
        ('lockout_duration', '锁定时长', '账户锁定时长(秒)', 'number', 300, 100),
        ('password_min_length', '密码最小长度', '用户密码最小长度', 'number', 6, 100),
        ('password_expiry_days', '密码过期天数', '密码过期天数', 'number', 90, 100),
        ('require_email_verification', '需要邮箱验证', '注册时需要邮箱验证', 'boolean', True, 90),
        ('require_phone_verification', '需要手机验证', '注册时需要手机验证', 'boolean', False, 90),
    ]
    
    for code, name, desc, rtype, value, priority in rules:
        insert_rule(code, name, desc, rtype, value, priority)
        log(f'  ✅ {name}: {value}', '✅')
    
    log(f'系统基本规则优化完成: {len(rules)} 条规则', '✅')


def optimize_user_rules():
    """优化用户规则"""
    log('优化用户规则...', '📋')
    
    user_rules = [
        ('user_registration_min_length', '用户注册-最小长度', '用户名最小长度', 'number', 3, 100),
        ('user_registration_max_length', '用户注册-最大长度', '用户名最大长度', 'number', 20, 100),
        ('user_password_hash', '密码哈希算法', '密码加密算法', 'text', 'pbkdf2_sha256', 100),
        ('user_default_role', '默认用户角色', '新用户默认角色', 'text', 'student', 100),
        ('user_session_duration', '会话持续时间', '会话有效时长(秒)', 'number', 86400, 90),
    ]
    
    for code, name, desc, rtype, value, priority in user_rules:
        insert_rule(code, name, desc, rtype, value, priority)
        log(f'  ✅ {name}: {value}', '✅')
    
    log(f'用户规则优化完成: {len(user_rules)} 条规则', '✅')


def optimize_permission_rules():
    """优化权限规则"""
    log('优化权限规则...', '📋')
    
    permission_rules = [
        ('page_access_student', '学生页面访问', '学生可访问的页面列表', 'json', {
            'allowed': ['/', '/exam', '/dashboard', '/profile'],
            'denied': ['/admin', '/settings']
        }, 100),
        ('page_access_teacher', '教师页面访问', '教师可访问的页面列表', 'json', {
            'allowed': ['/', '/exam', '/dashboard', '/profile', '/exam/manage', '/results'],
            'denied': ['/admin', '/settings/system']
        }, 100),
        ('page_access_admin', '管理员页面访问', '管理员可访问的页面列表', 'json', {
            'allowed': ['*'],
            'denied': []
        }, 100),
        ('feature_permission_student', '学生功能权限', '学生可用功能', 'json', {
            'can_take_exam': True,
            'can_view_results': True,
            'can_create_exam': False,
            'can_manage_users': False
        }, 100),
        ('feature_permission_teacher', '教师功能权限', '教师可用功能', 'json', {
            'can_take_exam': True,
            'can_view_results': True,
            'can_create_exam': True,
            'can_manage_questions': True,
            'can_view_students': True,
            'can_manage_users': False
        }, 100),
    ]
    
    for code, name, desc, rtype, value, priority in permission_rules:
        insert_rule(code, name, desc, rtype, value, priority)
        log(f'  ✅ {name}', '✅')
    
    log(f'权限规则优化完成: {len(permission_rules)} 条规则', '✅')


def optimize_strategy_rules():
    """优化策略规则"""
    log('优化策略规则...', '📋')
    
    strategy_rules = [
        ('exam_question_selection', '题目选择策略', '考试题目选择方式', 'text', 'random_difficulty_balanced', 100),
        ('exam_randomize_options', '随机化选项', '考试选项随机化', 'boolean', True, 100),
        ('exam_prevent_duplicate', '防止重复', '防止出现重复题目', 'boolean', True, 100),
        ('exam_auto_save', '自动保存', '考试答案自动保存', 'boolean', True, 90),
        ('exam_time_allocation', '时间分配', '考试时间分配策略', 'text', 'auto_per_question', 90),
        ('grading_partial_credit', '部分得分', '允许部分得分', 'boolean', True, 100),
        ('grading_ai_assist', 'AI辅助评分', 'AI辅助评分功能', 'boolean', True, 90),
        ('proctor_prevent_refresh', '防止刷新', '考试中防止页面刷新', 'boolean', True, 100),
        ('proctor_monitor_tab', '监控标签页', '监控标签页切换', 'boolean', True, 100),
        ('proctor_require_proctor_approval', '需要监考审批', '暂停需要监考审批', 'boolean', True, 100),
    ]
    
    for code, name, desc, rtype, value, priority in strategy_rules:
        insert_rule(code, name, desc, rtype, value, priority)
        log(f'  ✅ {name}: {value}', '✅')
    
    log(f'策略规则优化完成: {len(strategy_rules)} 条规则', '✅')


def optimize_student_rules():
    """优化学生规则"""
    log('优化学生规则...', '📋')
    
    student_rules = [
        ('student_max_exams_per_day', '每日最大考试数', '学生每天最多参加的考试数', 'number', 5, 100),
        ('student_exam_time_multiplier', '考试时间倍数', '学生考试时间乘数', 'number', 1.0, 100),
        ('student_can_review_answers', '可查看答案', '考试后可查看答案', 'boolean', True, 90),
        ('student_can_download_cert', '可下载证书', '可下载成绩证书', 'boolean', True, 90),
        ('student_adaptive_difficulty', '自适应难度', '根据表现自动调整难度', 'boolean', True, 90),
        ('student_max_retakes', '最大重考次数', '考试最大重考次数', 'number', 3, 100),
        ('student_requires_placement', '需要摸底测试', '参加正式考试前需要摸底测试', 'boolean', True, 100),
    ]
    
    for code, name, desc, rtype, value, priority in student_rules:
        insert_rule(code, name, desc, rtype, value, priority)
        log(f'  ✅ {name}: {value}', '✅')
    
    log(f'学生规则优化完成: {len(student_rules)} 条规则', '✅')


def optimize_teacher_rules():
    """优化教师规则"""
    log('优化教师规则...', '📋')
    
    teacher_rules = [
        ('teacher_can_create_exam', '可创建考试', '教师可创建考试', 'boolean', True, 100),
        ('teacher_can_edit_own_questions', '可编辑自己的题目', '教师可编辑自己创建的题目', 'boolean', True, 100),
        ('teacher_can_view_student_results', '可查看学生成绩', '教师可查看学生成绩', 'boolean', True, 100),
        ('teacher_can_grade_manually', '可手动评分', '教师可手动评分', 'boolean', True, 90),
        ('teacher_can_generate_reports', '可生成报告', '教师可生成分析报告', 'boolean', True, 90),
        ('teacher_max_questions_per_exam', '最大题目数', '考试最大题目数', 'number', 100, 90),
        ('teacher_cannot_delete_system', '不能删除系统题', '不能删除系统级题目', 'boolean', True, 100),
    ]
    
    for code, name, desc, rtype, value, priority in teacher_rules:
        insert_rule(code, name, desc, rtype, value, priority)
        log(f'  ✅ {name}: {value}', '✅')
    
    log(f'教师规则优化完成: {len(teacher_rules)} 条规则', '✅')


def optimize_route_rules():
    """优化路由规则"""
    log('优化路由规则...', '📋')
    
    route_rules = [
        ('route_login_required', '需要登录的路由', '需要登录才能访问的路由', 'json', [
            '/exam', '/dashboard', '/profile', '/results'
        ], 100),
        ('route_admin_required', '需要管理员权限', '需要管理员权限的路由', 'json', [
            '/admin', '/settings/system', '/users/manage'
        ], 100),
        ('route_public', '公开路由', '公开访问的路由', 'json', [
            '/', '/login', '/test', '/api/health'
        ], 100),
        ('route_redirect_login', '登录重定向', '未登录时重定向到登录页', 'boolean', True, 100),
    ]
    
    for code, name, desc, rtype, value, priority in route_rules:
        insert_rule(code, name, desc, rtype, value, priority)
        log(f'  ✅ {name}', '✅')
    
    log(f'路由规则优化完成: {len(route_rules)} 条规则', '✅')


def optimize_data_rules():
    """优化数据规则"""
    log('优化数据规则...', '📋')
    
    data_rules = [
        ('data_encryption', '数据加密', '敏感数据加密存储', 'boolean', True, 100),
        ('data_backup_enabled', '启用备份', '启用数据自动备份', 'boolean', True, 100),
        ('data_backup_frequency', '备份频率', '数据备份频率(小时)', 'number', 24, 90),
        ('data_retention_days', '数据保留天数', '日志数据保留天数', 'number', 90, 90),
        ('data_anonymization', '数据匿名化', '分析时使用匿名化数据', 'boolean', True, 90),
    ]
    
    for code, name, desc, rtype, value, priority in data_rules:
        insert_rule(code, name, desc, rtype, value, priority)
        log(f'  ✅ {name}: {value}', '✅')
    
    log(f'数据规则优化完成: {len(data_rules)} 条规则', '✅')


def optimize_subject_rules():
    """优化学科规则"""
    log('优化学科维护规则...', '📋')
    
    subject_rules = [
        ('subject_auto_update', '自动更新题库', '自动更新题库内容', 'boolean', True, 100),
        ('subject_difficulty_calibration', '难度校准', '定期校准题目难度', 'boolean', True, 90),
        ('subject_quality_check', '质量检查', '自动检查题目质量', 'boolean', True, 100),
        ('subject_ai_enhancement', 'AI增强', '使用AI增强题目质量', 'boolean', True, 90),
        ('subject_localization', '本地化', '支持本地化内容', 'boolean', True, 90),
    ]
    
    for code, name, desc, rtype, value, priority in subject_rules:
        insert_rule(code, name, desc, rtype, value, priority)
        log(f'  ✅ {name}: {value}', '✅')
    
    log(f'学科规则优化完成: {len(subject_rules)} 条规则', '✅')


def optimize_cluster_rules():
    """优化集群规则"""
    log('优化集群规则...', '📋')
    
    cluster_rules = [
        ('cluster_load_balancing', '负载均衡', '启用负载均衡', 'boolean', True, 100),
        ('cluster_failover', '故障转移', '启用故障转移', 'boolean', True, 100),
        ('cluster_sync_interval', '同步间隔', '集群同步间隔(秒)', 'number', 30, 90),
        ('cluster_heartbeat_timeout', '心跳超时', '节点心跳超时(秒)', 'number', 60, 90),
    ]
    
    for code, name, desc, rtype, value, priority in cluster_rules:
        insert_rule(code, name, desc, rtype, value, priority)
        log(f'  ✅ {name}: {value}', '✅')
    
    log(f'集群规则优化完成: {len(cluster_rules)} 条规则', '✅')


def main():
    """主函数"""
    print('\n' + '='*60)
    print('🎯 智能规则优化系统 - 增强版')
    print('='*60 + '\n')
    
    # 备份现有规则
    log('开始备份现有规则...', '📋')
    backup_count = backup_current_rules()
    log(f'已备份 {backup_count} 条规则\n', '📋')
    
    # 优化各类规则
    optimize_base_rules()
    optimize_user_rules()
    optimize_permission_rules()
    optimize_strategy_rules()
    optimize_student_rules()
    optimize_teacher_rules()
    optimize_route_rules()
    optimize_data_rules()
    optimize_subject_rules()
    optimize_cluster_rules()
    
    # 总结
    print('\n' + '='*60)
    log('规则优化总结', '📊')
    print('='*60)
    log(f'已备份规则: {backup_count} 条', '📋')
    log('所有系统规则已优化完成', '✅')
    print('='*60 + '\n')


if __name__ == '__main__':
    main()
