# -*- coding: utf-8 -*-
#!/usr/bin/env python3
"""
考试系统优化 - 完善考试管理、监考策略和考试分析
"""

import os
import sys
import sqlite3
import json
import uuid
from datetime import datetime, timedelta
from typing import Dict, List, Tuple, Any

# 配置
DATABASE_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'app.db')


def log(message: str, symbol: str = '📋'):
    """日志记录"""
    print(f"[{datetime.now().strftime('%H:%M:%S')}] {symbol} {message}")


def optimize_exam_settings():
    """优化考试设置规则"""
    log('优化考试设置规则...', '📋')
    
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()
    
    exam_rules = [
        ('exam_default_duration', '默认考试时长', '默认考试时长(分钟)', 'number', 60, 100),
        ('exam_min_duration', '最短考试时长', '允许的最短考试时长(分钟)', 'number', 15, 100),
        ('exam_max_duration', '最长考试时长', '允许的最长考试时长(分钟)', 'number', 240, 100),
        ('exam_question_count', '默认题目数量', '默认考试题目数量', 'number', 50, 100),
        ('exam_min_question_count', '最小题目数量', '考试最少题目数量', 'number', 10, 100),
        ('exam_max_question_count', '最大题目数量', '考试最多题目数量', 'number', 200, 100),
        ('exam_pass_score', '及格分数', '默认及格分数', 'number', 60, 100),
        ('exam_auto_submit', '自动提交', '时间到自动提交', 'boolean', True, 100),
        ('exam_show_result', '显示成绩', '考后立即显示成绩', 'boolean', True, 90),
        ('exam_allow_review', '允许回顾', '考后允许回顾题目', 'boolean', True, 90),
        ('exam_random_order', '题目随机', '题目顺序随机', 'boolean', True, 100),
        ('exam_random_options', '选项随机', '选项顺序随机', 'boolean', True, 100),
    ]
    
    for code, name, desc, rtype, value, priority in exam_rules:
        try:
            cursor.execute('''
                UPDATE system_rules 
                SET rule_value = ?, rule_name = ?, rule_description = ?
                WHERE rule_code = ?
            ''', (str(value), name, desc, code))
            
            if cursor.rowcount == 0:
                cursor.execute('''
                    INSERT INTO system_rules 
                    (rule_code, rule_name, rule_description, rule_type, rule_value, is_active, priority)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                ''', (code, name, desc, rtype, str(value), 1, priority))
            
            log(f'  ✅ {name}: {value}', '✅')
        except Exception as e:
            log(f'  ❌ {name}: {str(e)}', '❌')
    
    conn.commit()
    conn.close()
    log(f'考试设置规则优化完成: {len(exam_rules)} 条规则', '✅')


def optimize_proctor_settings():
    """优化监考设置规则"""
    log('优化监考设置规则...', '📋')
    
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()
    
    proctor_rules = [
        ('proctor_prevent_refresh', '防止刷新', '考试中禁止页面刷新', 'boolean', True, 100),
        ('proctor_prevent_copy', '防止复制', '禁止复制题目内容', 'boolean', True, 100),
        ('proctor_monitor_tab', '监控标签页', '监控标签页切换', 'boolean', True, 100),
        ('proctor_max_tab_switches', '最大切换次数', '允许的最大标签页切换次数', 'number', 5, 100),
        ('proctor_require_proctor_approval', '需要监考审批', '暂停需要监考审批', 'boolean', True, 100),
        ('proctor_log_all_actions', '记录所有操作', '记录所有考生操作', 'boolean', True, 100),
        ('proctor_screenshot_interval', '截图间隔', '自动截图间隔(秒)', 'number', 60, 90),
        ('proctor_face_detection', '人脸检测', '启用人脸检测', 'boolean', False, 80),
        ('proctor_voice_detection', '声音检测', '启用声音检测', 'boolean', False, 80),
        ('proctor_ip_monitoring', 'IP监控', '监控IP地址变化', 'boolean', True, 90),
        ('proctor_device_monitoring', '设备监控', '监控设备变化', 'boolean', True, 90),
        ('proctor_fullscreen', '全屏模式', '要求全屏考试', 'boolean', False, 85),
        ('proctor_warning_count', '警告次数', '达到此次数强制交卷', 'number', 10, 100),
    ]
    
    for code, name, desc, rtype, value, priority in proctor_rules:
        try:
            cursor.execute('''
                UPDATE system_rules 
                SET rule_value = ?, rule_name = ?, rule_description = ?
                WHERE rule_code = ?
            ''', (str(value), name, desc, code))
            
            if cursor.rowcount == 0:
                cursor.execute('''
                    INSERT INTO system_rules 
                    (rule_code, rule_name, rule_description, rule_type, rule_value, is_active, priority)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                ''', (code, name, desc, rtype, str(value), 1, priority))
            
            log(f'  ✅ {name}: {value}', '✅')
        except Exception as e:
            log(f'  ❌ {name}: {str(e)}', '❌')
    
    conn.commit()
    conn.close()
    log(f'监考设置规则优化完成: {len(proctor_rules)} 条规则', '✅')


def optimize_grading_settings():
    """优化评分设置规则"""
    log('优化评分设置规则...', '📋')
    
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()
    
    grading_rules = [
        ('grading_partial_credit', '部分得分', '允许选择题部分得分', 'boolean', True, 100),
        ('grading_partial_ratio', '部分得分比例', '选对部分选项得分比例', 'number', 0.5, 100),
        ('grading_auto_grade', '自动评分', '客观题自动评分', 'boolean', True, 100),
        ('grading_ai_assist', 'AI辅助评分', '主观题AI辅助评分', 'boolean', True, 90),
        ('grading_teacher_review', '教师审核', '需要教师审核评分', 'boolean', False, 90),
        ('grading_allow_appeal', '允许申诉', '允许学生对成绩申诉', 'boolean', True, 90),
        ('grading_appeal_deadline', '申诉期限', '申诉截止天数', 'number', 7, 100),
        ('grading_curve_enabled', '启用曲线', '启用成绩曲线调整', 'boolean', False, 80),
        ('grading_curve_type', '曲线类型', '曲线调整类型', 'text', 'none', 80),
    ]
    
    for code, name, desc, rtype, value, priority in grading_rules:
        try:
            cursor.execute('''
                UPDATE system_rules 
                SET rule_value = ?, rule_name = ?, rule_description = ?
                WHERE rule_code = ?
            ''', (str(value), name, desc, code))
            
            if cursor.rowcount == 0:
                cursor.execute('''
                    INSERT INTO system_rules 
                    (rule_code, rule_name, rule_description, rule_type, rule_value, is_active, priority)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                ''', (code, name, desc, rtype, str(value), 1, priority))
            
            log(f'  ✅ {name}: {value}', '✅')
        except Exception as e:
            log(f'  ❌ {name}: {str(e)}', '❌')
    
    conn.commit()
    conn.close()
    log(f'评分设置规则优化完成: {len(grading_rules)} 条规则', '✅')


def optimize_question_selection():
    """优化题目选择策略"""
    log('优化题目选择策略...', '📋')
    
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()
    
    selection_rules = [
        ('question_selection_method', '选择方法', '题目选择方法', 'text', 'random_difficulty_balanced', 100),
        ('question_difficulty_distribution', '难度分布', '各难度题目比例', 'json', {
            'easy': 0.3,
            'medium': 0.5,
            'hard': 0.2
        }, 100),
        ('question_type_distribution', '题型分布', '各题型题目比例', 'json', {
            'single_choice': 0.4,
            'multiple_choice': 0.2,
            'true_false': 0.15,
            'fill_blank': 0.15,
            'essay': 0.1
        }, 100),
        ('question_prevent_duplicate', '防止重复', '防止出现重复题目', 'boolean', True, 100),
        ('question_tag_matching', '标签匹配', '根据知识点标签选择', 'boolean', True, 90),
        ('question_difficulty_auto', '自动难度', '根据考生水平调整难度', 'boolean', True, 90),
        ('question_similar_filter', '相似过滤', '过滤相似题目', 'boolean', True, 85),
        ('question_learning_weight', '学习权重', '优先选择未掌握知识点', 'boolean', True, 85),
    ]
    
    for code, name, desc, rtype, value, priority in selection_rules:
        try:
            value_json = json.dumps(value) if isinstance(value, dict) else str(value)
            cursor.execute('''
                UPDATE system_rules 
                SET rule_value = ?, rule_name = ?, rule_description = ?
                WHERE rule_code = ?
            ''', (value_json, name, desc, code))
            
            if cursor.rowcount == 0:
                cursor.execute('''
                    INSERT INTO system_rules 
                    (rule_code, rule_name, rule_description, rule_type, rule_value, is_active, priority)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                ''', (code, name, desc, rtype, value_json, 1, priority))
            
            log(f'  ✅ {name}', '✅')
        except Exception as e:
            log(f'  ❌ {name}: {str(e)}', '❌')
    
    conn.commit()
    conn.close()
    log(f'题目选择策略优化完成: {len(selection_rules)} 条规则', '✅')


def optimize_exam_time_settings():
    """优化考试时间设置"""
    log('优化考试时间设置...', '📋')
    
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()
    
    time_rules = [
        ('exam_early_start', '提前开始', '允许提前开始考试(分钟)', 'number', 5, 90),
        ('exam_late_submit', '延迟提交', '允许延迟提交(分钟)', 'number', 2, 90),
        ('exam_buffer_time', '缓冲时间', '题目加载缓冲时间(秒)', 'number', 3, 90),
        ('exam_auto_save_interval', '自动保存间隔', '自动保存答案间隔(秒)', 'number', 30, 100),
        ('exam_warning_time', '警告时间', '剩余时间警告(分钟)', 'number', 5, 100),
        ('exam_countdown_type', '倒计时方式', '倒计时显示方式', 'text', 'countdown', 80),
    ]
    
    for code, name, desc, rtype, value, priority in time_rules:
        try:
            cursor.execute('''
                UPDATE system_rules 
                SET rule_value = ?, rule_name = ?, rule_description = ?
                WHERE rule_code = ?
            ''', (str(value), name, desc, code))
            
            if cursor.rowcount == 0:
                cursor.execute('''
                    INSERT INTO system_rules 
                    (rule_code, rule_name, rule_description, rule_type, rule_value, is_active, priority)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                ''', (code, name, desc, rtype, str(value), 1, priority))
            
            log(f'  ✅ {name}: {value}', '✅')
        except Exception as e:
            log(f'  ❌ {name}: {str(e)}', '❌')
    
    conn.commit()
    conn.close()
    log(f'考试时间设置优化完成: {len(time_rules)} 条规则', '✅')


def optimize_exam_notification():
    """优化考试通知设置"""
    log('优化考试通知设置...', '📋')
    
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()
    
    notification_rules = [
        ('notification_exam_start', '考试开始通知', '考试开始前发送通知', 'boolean', True, 100),
        ('notification_exam_reminder', '考试提醒', '考试前提醒', 'boolean', True, 100),
        ('notification_reminder_interval', '提醒间隔', '提醒间隔(小时)', 'number', 24, 90),
        ('notification_result_release', '成绩发布通知', '成绩发布发送通知', 'boolean', True, 100),
        ('notification_cheating_detected', '作弊检测通知', '检测到作弊发送通知', 'boolean', True, 100),
        ('notification_email_enabled', '启用邮件通知', '发送邮件通知', 'boolean', False, 80),
        ('notification_sms_enabled', '启用短信通知', '发送短信通知', 'boolean', False, 80),
    ]
    
    for code, name, desc, rtype, value, priority in notification_rules:
        try:
            cursor.execute('''
                UPDATE system_rules 
                SET rule_value = ?, rule_name = ?, rule_description = ?
                WHERE rule_code = ?
            ''', (str(value), name, desc, code))
            
            if cursor.rowcount == 0:
                cursor.execute('''
                    INSERT INTO system_rules 
                    (rule_code, rule_name, rule_description, rule_type, rule_value, is_active, priority)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                ''', (code, name, desc, rtype, str(value), 1, priority))
            
            log(f'  ✅ {name}: {value}', '✅')
        except Exception as e:
            log(f'  ❌ {name}: {str(e)}', '❌')
    
    conn.commit()
    conn.close()
    log(f'考试通知设置优化完成: {len(notification_rules)} 条规则', '✅')


def create_exam_tables():
    """创建考试相关表"""
    log('创建考试相关表...', '📋')
    
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()
    
    tables = [
        '''CREATE TABLE IF NOT EXISTS exam_sessions (
            id TEXT PRIMARY KEY,
            user_id INTEGER,
            exam_id TEXT,
            start_time TEXT,
            end_time TEXT,
            duration INTEGER,
            score REAL,
            status TEXT,
            ip_address TEXT,
            device_info TEXT,
            proctor_log TEXT,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        )''',
        
        '''CREATE TABLE IF NOT EXISTS exam_attempts (
            id TEXT PRIMARY KEY,
            session_id TEXT,
            question_id TEXT,
            user_answer TEXT,
            score REAL,
            time_spent INTEGER,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        )''',
        
        '''CREATE TABLE IF NOT EXISTS exam_analytics (
            id TEXT PRIMARY KEY,
            exam_id TEXT,
            total_attempts INTEGER,
            avg_score REAL,
            pass_rate REAL,
            difficulty_analysis TEXT,
            time_analysis TEXT,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        )'''
    ]
    
    for sql in tables:
        try:
            cursor.execute(sql)
            log(f'  ✅ 表创建成功', '✅')
        except Exception as e:
            log(f'  ❌ 表创建失败: {str(e)}', '❌')
    
    conn.commit()
    conn.close()
    log(f'考试表创建完成', '✅')


def optimize_exam_analytics():
    """优化考试分析设置"""
    log('优化考试分析设置...', '📋')
    
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()
    
    analytics_rules = [
        ('analytics_difficulty', '难度分析', '启用题目难度分析', 'boolean', True, 100),
        ('analytics_time_spent', '用时分析', '启用答题用时分析', 'boolean', True, 100),
        ('analytics_pattern', '模式分析', '启用答题模式分析', 'boolean', True, 90),
        ('analytics_prediction', '成绩预测', '启用AI成绩预测', 'boolean', True, 85),
        ('analytics_recommendation', '推荐学习', '启用个性化学习推荐', 'boolean', True, 85),
        ('analytics_trend', '趋势分析', '启用成绩趋势分析', 'boolean', True, 90),
        ('analytics_comparison', '对比分析', '启用班级对比分析', 'boolean', True, 85),
    ]
    
    for code, name, desc, rtype, value, priority in analytics_rules:
        try:
            cursor.execute('''
                UPDATE system_rules 
                SET rule_value = ?, rule_name = ?, rule_description = ?
                WHERE rule_code = ?
            ''', (str(value), name, desc, code))
            
            if cursor.rowcount == 0:
                cursor.execute('''
                    INSERT INTO system_rules 
                    (rule_code, rule_name, rule_description, rule_type, rule_value, is_active, priority)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                ''', (code, name, desc, rtype, str(value), 1, priority))
            
            log(f'  ✅ {name}: {value}', '✅')
        except Exception as e:
            log(f'  ❌ {name}: {str(e)}', '❌')
    
    conn.commit()
    conn.close()
    log(f'考试分析设置优化完成: {len(analytics_rules)} 条规则', '✅')


def main():
    """主函数"""
    print('\n' + '='*60)
    print('📝 考试系统优化')
    print('='*60 + '\n')
    
    # 1. 创建考试相关表
    create_exam_tables()
    
    # 2. 优化考试设置规则
    optimize_exam_settings()
    
    # 3. 优化监考设置规则
    optimize_proctor_settings()
    
    # 4. 优化评分设置规则
    optimize_grading_settings()
    
    # 5. 优化题目选择策略
    optimize_question_selection()
    
    # 6. 优化考试时间设置
    optimize_exam_time_settings()
    
    # 7. 优化考试通知设置
    optimize_exam_notification()
    
    # 8. 优化考试分析设置
    optimize_exam_analytics()
    
    print('\n' + '='*60)
    log('考试系统优化完成!', '✅')
    print('='*60 + '\n')


if __name__ == '__main__':
    main()
