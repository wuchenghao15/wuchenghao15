# -*- coding: utf-8 -*-
"""
考试系统规则模板
支持考试系统自动规则创建、更新迭代，方便AI员工自动触发规则执行操作
"""

class ExamRuleTemplate:
    """考试系统规则模板"""
    
    EXAM_MANAGEMENT_RULES = [
        {
            'name': '考试未开始提醒',
            'template_key': 'exam_reminder_not_started',
            'category': 'exam_management',
            'conditions': [
                {'field': 'exam_status', 'operator': 'equals', 'value': 'active'},
                {'field': 'minutes_before_start', 'operator': 'equals', 'value': 30}
            ],
            'actions': [
                {'action_type': 'notify_admin', 'params': {'message': '考试即将开始，请确保系统准备就绪', 'level': 'info'}},
                {'action_type': 'send_message', 'params': {'message_type': 'exam_reminder', 'content': {'action': 'broadcast'}}}
            ],
            'priority': 8,
            'description': '考试开始前30分钟发送提醒通知'
        },
        {
            'name': '考试进行中超时检测',
            'template_key': 'exam_timeout_detection',
            'category': 'exam_management',
            'conditions': [
                {'field': 'exam_status', 'operator': 'equals', 'value': 'in_progress'},
                {'field': 'time_remaining', 'operator': 'less_than', 'value': 300}
            ],
            'actions': [
                {'action_type': 'send_message', 'params': {'message_type': 'timeout_warning', 'content': {'message': '考试剩余时间不足5分钟'}}},
                {'action_type': 'update_status', 'params': {'status': 'timeout_alert'}}
            ],
            'priority': 10,
            'description': '考试进行中剩余时间不足5分钟时发送警告'
        },
        {
            'name': '考试结束自动批改',
            'template_key': 'exam_auto_correct',
            'category': 'exam_management',
            'conditions': [
                {'field': 'exam_status', 'operator': 'equals', 'value': 'completed'},
                {'field': 'auto_correct', 'operator': 'equals', 'value': True}
            ],
            'actions': [
                {'action_type': 'dispatch_task', 'params': {'task_type': 'exam_correct', 'employee_template': 'exam_grader'}},
                {'action_type': 'call_api', 'params': {'url': '/api/exam/correct', 'method': 'POST'}}
            ],
            'priority': 12,
            'description': '考试结束后自动触发AI批改任务'
        },
        {
            'name': '考试成绩异常检测',
            'template_key': 'exam_score_anomaly',
            'category': 'exam_management',
            'conditions': [
                {'field': 'score_deviation', 'operator': 'greater_than', 'value': 0.3}
            ],
            'actions': [
                {'action_type': 'notify_admin', 'params': {'message': '检测到考试成绩异常，可能存在作弊行为', 'level': 'warning'}},
                {'action_type': 'dispatch_task', 'params': {'task_type': 'cheat_detection', 'employee_template': 'security_analyzer'}}
            ],
            'priority': 15,
            'description': '成绩偏离正常范围超过30%时触发作弊检测'
        },
        {
            'name': '考试数据统计分析',
            'template_key': 'exam_statistics_analysis',
            'category': 'exam_management',
            'conditions': [
                {'field': 'exam_count_today', 'operator': 'greater_than', 'value': 10}
            ],
            'actions': [
                {'action_type': 'dispatch_task', 'params': {'task_type': 'exam_analytics', 'employee_template': 'data_analyzer'}},
                {'action_type': 'call_api', 'params': {'url': '/api/exam/statistics', 'method': 'GET'}}
            ],
            'priority': 5,
            'description': '当日考试数量超过10场时触发统计分析'
        }
    ]
    
    QUESTION_MANAGEMENT_RULES = [
        {
            'name': '题目难度调整',
            'template_key': 'question_difficulty_adjust',
            'category': 'question_management',
            'conditions': [
                {'field': 'question_accuracy', 'operator': 'less_than', 'value': 0.4}
            ],
            'actions': [
                {'action_type': 'dispatch_task', 'params': {'task_type': 'question_update', 'employee_template': 'content_manager'}},
                {'action_type': 'call_api', 'params': {'url': '/api/exam/question/adjust', 'method': 'POST'}}
            ],
            'priority': 8,
            'description': '题目正确率低于40%时自动调整难度'
        },
        {
            'name': '题目过期提醒',
            'template_key': 'question_expiry_reminder',
            'category': 'question_management',
            'conditions': [
                {'field': 'days_since_update', 'operator': 'greater_than', 'value': 90}
            ],
            'actions': [
                {'action_type': 'notify_admin', 'params': {'message': '题目超过90天未更新，建议审核', 'level': 'info'}},
                {'action_type': 'dispatch_task', 'params': {'task_type': 'question_review', 'employee_template': 'content_manager'}}
            ],
            'priority': 4,
            'description': '题目长时间未更新时触发审核提醒'
        },
        {
            'name': '题库数量不足告警',
            'template_key': 'question_bank_low',
            'category': 'question_management',
            'conditions': [
                {'field': 'question_bank_count', 'operator': 'less_than', 'value': 50}
            ],
            'actions': [
                {'action_type': 'notify_admin', 'params': {'message': '题库数量不足50道，需要补充', 'level': 'warning'}},
                {'action_type': 'dispatch_task', 'params': {'task_type': 'question_generate', 'employee_template': 'ai_writer'}}
            ],
            'priority': 10,
            'description': '题库数量不足时自动触发AI生成题目'
        },
        {
            'name': '题目重复检测',
            'template_key': 'question_duplicate_detection',
            'category': 'question_management',
            'conditions': [
                {'field': 'similarity_score', 'operator': 'greater_than', 'value': 0.8}
            ],
            'actions': [
                {'action_type': 'notify_admin', 'params': {'message': '检测到重复题目，请审核处理', 'level': 'warning'}},
                {'action_type': 'update_status', 'params': {'status': 'duplicate_alert'}}
            ],
            'priority': 7,
            'description': '题目相似度超过80%时触发重复检测'
        }
    ]
    
    STUDENT_BEHAVIOR_RULES = [
        {
            'name': '学生考试行为异常',
            'template_key': 'student_behavior_anomaly',
            'category': 'student_behavior',
            'conditions': [
                {'field': 'answer_changes', 'operator': 'greater_than', 'value': 10},
                {'field': 'time_between_answers', 'operator': 'less_than', 'value': 5}
            ],
            'actions': [
                {'action_type': 'notify_admin', 'params': {'message': '学生答题行为异常，可能存在作弊', 'level': 'warning'}},
                {'action_type': 'dispatch_task', 'params': {'task_type': 'behavior_analysis', 'employee_template': 'security_analyzer'}}
            ],
            'priority': 12,
            'description': '学生频繁修改答案且答题速度异常时触发分析'
        },
        {
            'name': '学生连续考试失败',
            'template_key': 'student_consecutive_failure',
            'category': 'student_behavior',
            'conditions': [
                {'field': 'consecutive_failures', 'operator': 'greater_than', 'value': 3}
            ],
            'actions': [
                {'action_type': 'notify_admin', 'params': {'message': '学生连续3次考试未通过，建议提供辅导', 'level': 'info'}},
                {'action_type': 'dispatch_task', 'params': {'task_type': 'student_analysis', 'employee_template': 'tutor_analyzer'}}
            ],
            'priority': 6,
            'description': '学生连续考试失败时触发学习分析'
        },
        {
            'name': '学生考试进度提醒',
            'template_key': 'student_progress_reminder',
            'category': 'student_behavior',
            'conditions': [
                {'field': 'exam_progress', 'operator': 'less_than', 'value': 0.5},
                {'field': 'time_remaining_ratio', 'operator': 'less_than', 'value': 0.3}
            ],
            'actions': [
                {'action_type': 'send_message', 'params': {'message_type': 'progress_warning', 'content': {'message': '答题进度较慢，请加快速度'}}}
            ],
            'priority': 5,
            'description': '学生考试进度落后时发送提醒'
        },
        {
            'name': '学生成绩提升奖励',
            'template_key': 'student_improvement_reward',
            'category': 'student_behavior',
            'conditions': [
                {'field': 'score_improvement', 'operator': 'greater_than', 'value': 15}
            ],
            'actions': [
                {'action_type': 'send_message', 'params': {'message_type': 'achievement', 'content': {'message': '成绩提升超过15分，继续加油！'}}},
                {'action_type': 'update_status', 'params': {'status': 'achievement_unlocked'}}
            ],
            'priority': 3,
            'description': '学生成绩显著提升时发送奖励通知'
        }
    ]
    
    SECURITY_RULES = [
        {
            'name': '考试作弊检测',
            'template_key': 'exam_cheat_detection',
            'category': 'exam_security',
            'conditions': [
                {'field': 'cheat_score', 'operator': 'greater_than', 'value': 0.7}
            ],
            'actions': [
                {'action_type': 'notify_admin', 'params': {'message': '检测到高作弊嫌疑，建议人工审核', 'level': 'critical'}},
                {'action_type': 'dispatch_task', 'params': {'task_type': 'deep_analysis', 'employee_template': 'security_analyzer'}},
                {'action_type': 'update_status', 'params': {'status': 'cheat_suspected'}}
            ],
            'priority': 20,
            'description': '作弊嫌疑分数超过70%时触发深度分析'
        },
        {
            'name': '异常登录检测',
            'template_key': 'exam_abnormal_login',
            'category': 'exam_security',
            'conditions': [
                {'field': 'login_from_different_ip', 'operator': 'equals', 'value': True},
                {'field': 'login_attempts', 'operator': 'greater_than', 'value': 3}
            ],
            'actions': [
                {'action_type': 'notify_admin', 'params': {'message': '检测到异常登录行为，考试账号可能被盗', 'level': 'warning'}},
                {'action_type': 'update_status', 'params': {'status': 'security_lock'}}
            ],
            'priority': 15,
            'description': '从不同IP频繁登录时触发安全告警'
        },
        {
            'name': '考试数据篡改检测',
            'template_key': 'exam_data_tampering',
            'category': 'exam_security',
            'conditions': [
                {'field': 'data_hash_mismatch', 'operator': 'equals', 'value': True}
            ],
            'actions': [
                {'action_type': 'notify_admin', 'params': {'message': '检测到考试数据篡改，数据完整性受损', 'level': 'critical'}},
                {'action_type': 'execute_shell', 'params': {'command': 'sqlite3 app.db "PRAGMA integrity_check;"'}}
            ],
            'priority': 25,
            'description': '考试数据哈希校验失败时触发紧急告警'
        }
    ]
    
    PERFORMANCE_RULES = [
        {
            'name': '考试系统性能监控',
            'template_key': 'exam_performance_monitor',
            'category': 'exam_performance',
            'conditions': [
                {'field': 'exam_response_time', 'operator': 'greater_than', 'value': 3000}
            ],
            'actions': [
                {'action_type': 'notify_admin', 'params': {'message': '考试系统响应时间超过3秒', 'level': 'warning'}},
                {'action_type': 'dispatch_task', 'params': {'task_type': 'performance_analysis', 'employee_template': 'system_optimizer'}}
            ],
            'priority': 10,
            'description': '考试系统响应时间过长时触发性能分析'
        },
        {
            'name': '并发考试人数预警',
            'template_key': 'exam_concurrent_warning',
            'category': 'exam_performance',
            'conditions': [
                {'field': 'concurrent_exams', 'operator': 'greater_than', 'value': 50}
            ],
            'actions': [
                {'action_type': 'notify_admin', 'params': {'message': '并发考试人数超过50人，注意系统负载', 'level': 'warning'}},
                {'action_type': 'call_api', 'params': {'url': '/api/system/health', 'method': 'GET'}}
            ],
            'priority': 8,
            'description': '并发考试人数超过阈值时发送预警'
        },
        {
            'name': '考试数据备份',
            'template_key': 'exam_data_backup',
            'category': 'exam_performance',
            'conditions': [
                {'field': 'days_since_last_backup', 'operator': 'greater_than', 'value': 7}
            ],
            'actions': [
                {'action_type': 'execute_shell', 'params': {'command': 'cp app.db app_backup_$(date +%Y%m%d).db'}},
                {'action_type': 'notify_admin', 'params': {'message': '考试数据已自动备份', 'level': 'info'}}
            ],
            'priority': 6,
            'description': '超过7天未备份时自动执行备份'
        }
    ]
    
    ALL_TEMPLATES = (
        EXAM_MANAGEMENT_RULES + 
        QUESTION_MANAGEMENT_RULES + 
        STUDENT_BEHAVIOR_RULES + 
        SECURITY_RULES + 
        PERFORMANCE_RULES
    )
    
    CATEGORIES = ['exam_management', 'question_management', 'student_behavior', 'exam_security', 'exam_performance']