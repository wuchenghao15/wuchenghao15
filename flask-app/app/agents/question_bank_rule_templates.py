# -*- coding: utf-8 -*-
"""
题库系统规则模板
支持题库系统自动规则创建、更新迭代，方便AI员工自动触发规则执行操作
"""

class QuestionBankRuleTemplate:
    """题库系统规则模板"""
    
    QUESTION_MANAGEMENT_RULES = [
        {
            'name': '题目过期自动审核',
            'template_key': 'question_expiry_review',
            'category': 'question_management',
            'conditions': [
                {'field': 'question_age_days', 'operator': 'greater_than', 'value': 180}
            ],
            'actions': [
                {'action_type': 'notify_admin', 'params': {'message': '题目超过180天未更新，需人工审核', 'level': 'info'}},
                {'action_type': 'dispatch_task', 'params': {'task_type': 'question_review', 'employee_template': 'content_reviewer'}},
                {'action_type': 'call_api', 'params': {'url': '/api/question-bank-ai/ai/analyze', 'method': 'POST'}}
            ],
            'priority': 6,
            'description': '题目长时间未更新时触发自动审核'
        },
        {
            'name': '题目质量评分过低',
            'template_key': 'question_quality_low',
            'category': 'question_management',
            'conditions': [
                {'field': 'quality_score', 'operator': 'less_than', 'value': 60}
            ],
            'actions': [
                {'action_type': 'notify_admin', 'params': {'message': '题目质量评分低于60分，需要优化', 'level': 'warning'}},
                {'action_type': 'dispatch_task', 'params': {'task_type': 'question_optimize', 'employee_template': 'question_optimizer'}},
                {'action_type': 'call_api', 'params': {'url': '/api/question-bank-ai/ai/optimize', 'method': 'POST'}}
            ],
            'priority': 8,
            'description': '题目质量评分过低时触发AI优化'
        },
        {
            'name': '题目难度异常检测',
            'template_key': 'question_difficulty_anomaly',
            'category': 'question_management',
            'conditions': [
                {'field': 'difficulty_match_rate', 'operator': 'less_than', 'value': 0.5}
            ],
            'actions': [
                {'action_type': 'notify_admin', 'params': {'message': '题目难度与标签不匹配，需要调整', 'level': 'warning'}},
                {'action_type': 'dispatch_task', 'params': {'task_type': 'difficulty_adjust', 'employee_template': 'difficulty_analyzer'}},
                {'action_type': 'update_status', 'params': {'status': 'difficulty_review'}}
            ],
            'priority': 7,
            'description': '题目难度设置异常时触发调整'
        },
        {
            'name': '题目使用频率过低',
            'template_key': 'question_usage_low',
            'category': 'question_management',
            'conditions': [
                {'field': 'usage_count', 'operator': 'less_than', 'value': 5},
                {'field': 'question_age_days', 'operator': 'greater_than', 'value': 30}
            ],
            'actions': [
                {'action_type': 'notify_admin', 'params': {'message': '题目使用频率过低，可能需要优化或删除', 'level': 'info'}},
                {'action_type': 'dispatch_task', 'params': {'task_type': 'usage_analysis', 'employee_template': 'content_analyzer'}}
            ],
            'priority': 5,
            'description': '题目使用频率过低时触发分析'
        },
        {
            'name': '题目重复检测',
            'template_key': 'question_duplicate_check',
            'category': 'question_management',
            'conditions': [
                {'field': 'duplicate_similarity', 'operator': 'greater_than', 'value': 0.85}
            ],
            'actions': [
                {'action_type': 'notify_admin', 'params': {'message': '检测到重复题目，请审核处理', 'level': 'warning'}},
                {'action_type': 'update_status', 'params': {'status': 'duplicate_flagged'}},
                {'action_type': 'dispatch_task', 'params': {'task_type': 'duplicate_resolve', 'employee_template': 'content_reviewer'}}
            ],
            'priority': 10,
            'description': '检测到重复题目时触发处理'
        }
    ]
    
    BANK_EXPANSION_RULES = [
        {
            'name': '题库数量不足告警',
            'template_key': 'bank_count_low',
            'category': 'bank_expansion',
            'conditions': [
                {'field': 'question_bank_count', 'operator': 'less_than', 'value': 1000}
            ],
            'actions': [
                {'action_type': 'notify_admin', 'params': {'message': '题库数量不足1000道，需要扩充', 'level': 'warning'}},
                {'action_type': 'dispatch_task', 'params': {'task_type': 'bank_expand', 'employee_template': 'question_generator'}},
                {'action_type': 'call_api', 'params': {'url': '/api/question-bank-ai/ai/batch-optimize', 'method': 'POST'}}
            ],
            'priority': 12,
            'description': '题库数量不足时自动触发扩充'
        },
        {
            'name': '特定科目题目不足',
            'template_key': 'subject_questions_low',
            'category': 'bank_expansion',
            'conditions': [
                {'field': 'subject_question_count', 'operator': 'less_than', 'value': 200}
            ],
            'actions': [
                {'action_type': 'notify_admin', 'params': {'message': '特定科目题目不足200道，需要针对性扩充', 'level': 'warning'}},
                {'action_type': 'dispatch_task', 'params': {'task_type': 'subject_expand', 'employee_template': 'subject_generator'}},
                {'action_type': 'call_api', 'params': {'url': '/api/questions/generate', 'method': 'POST'}}
            ],
            'priority': 10,
            'description': '特定科目题目不足时触发扩充'
        },
        {
            'name': '题目类型分布不均',
            'template_key': 'question_type_unbalanced',
            'category': 'bank_expansion',
            'conditions': [
                {'field': 'type_distribution_ratio', 'operator': 'less_than', 'value': 0.1}
            ],
            'actions': [
                {'action_type': 'notify_admin', 'params': {'message': '题目类型分布不均衡，需要补充稀缺类型', 'level': 'info'}},
                {'action_type': 'dispatch_task', 'params': {'task_type': 'type_balance', 'employee_template': 'question_generator'}}
            ],
            'priority': 6,
            'description': '题目类型分布不均时触发平衡'
        },
        {
            'name': '自动爬取补充题库',
            'template_key': 'auto_crawl_supplement',
            'category': 'bank_expansion',
            'conditions': [
                {'field': 'bank_growth_rate', 'operator': 'less_than', 'value': 0.05},
                {'field': 'days_since_last_crawl', 'operator': 'greater_than', 'value': 7}
            ],
            'actions': [
                {'action_type': 'dispatch_task', 'params': {'task_type': 'crawl_questions', 'employee_template': 'question_crawler'}},
                {'action_type': 'notify_admin', 'params': {'message': '已自动触发题目爬取补充题库', 'level': 'info'}}
            ],
            'priority': 5,
            'description': '题库增长缓慢时自动爬取补充'
        },
        {
            'name': '热门题目自动复制',
            'template_key': 'hot_question_reproduce',
            'category': 'bank_expansion',
            'conditions': [
                {'field': 'question_hit_rate', 'operator': 'greater_than', 'value': 0.8},
                {'field': 'similar_question_count', 'operator': 'less_than', 'value': 3}
            ],
            'actions': [
                {'action_type': 'dispatch_task', 'params': {'task_type': 'question_reproduce', 'employee_template': 'question_generator'}},
                {'action_type': 'notify_admin', 'params': {'message': '热门题目已自动生成相似题目', 'level': 'info'}}
            ],
            'priority': 4,
            'description': '热门题目自动生成相似题目扩充题库'
        }
    ]
    
    QUALITY_ASSURANCE_RULES = [
        {
            'name': '题目内容安全审核',
            'template_key': 'question_content_security',
            'category': 'quality_assurance',
            'conditions': [
                {'field': 'sensitive_word_detected', 'operator': 'equals', 'value': True}
            ],
            'actions': [
                {'action_type': 'notify_admin', 'params': {'message': '题目包含敏感内容，需要审核', 'level': 'critical'}},
                {'action_type': 'update_status', 'params': {'status': 'security_review'}},
                {'action_type': 'dispatch_task', 'params': {'task_type': 'content_audit', 'employee_template': 'security_checker'}}
            ],
            'priority': 20,
            'description': '题目包含敏感内容时触发安全审核'
        },
        {
            'name': '题目答案准确性检查',
            'template_key': 'answer_accuracy_check',
            'category': 'quality_assurance',
            'conditions': [
                {'field': 'answer_error_rate', 'operator': 'greater_than', 'value': 0.1}
            ],
            'actions': [
                {'action_type': 'notify_admin', 'params': {'message': '题目答案错误率超过10%，需要核查', 'level': 'warning'}},
                {'action_type': 'dispatch_task', 'params': {'task_type': 'answer_verify', 'employee_template': 'answer_checker'}},
                {'action_type': 'call_api', 'params': {'url': '/api/question-bank-ai/ai/analyze', 'method': 'POST'}}
            ],
            'priority': 15,
            'description': '题目答案错误率高时触发核查'
        },
        {
            'name': '题目解析完整性检查',
            'template_key': 'explanation_completeness',
            'category': 'quality_assurance',
            'conditions': [
                {'field': 'explanation_missing_rate', 'operator': 'greater_than', 'value': 0.2}
            ],
            'actions': [
                {'action_type': 'notify_admin', 'params': {'message': '题目解析缺失率超过20%，需要补充', 'level': 'warning'}},
                {'action_type': 'dispatch_task', 'params': {'task_type': 'explanation_generate', 'employee_template': 'ai_writer'}},
                {'action_type': 'call_api', 'params': {'url': '/api/question-bank-ai/ai/optimize', 'method': 'POST'}}
            ],
            'priority': 8,
            'description': '题目解析缺失率高时自动补充'
        },
        {
            'name': '题目标签准确性检测',
            'template_key': 'tag_accuracy_check',
            'category': 'quality_assurance',
            'conditions': [
                {'field': 'tag_match_rate', 'operator': 'less_than', 'value': 0.7}
            ],
            'actions': [
                {'action_type': 'notify_admin', 'params': {'message': '题目标签准确性低于70%，需要重新标注', 'level': 'info'}},
                {'action_type': 'dispatch_task', 'params': {'task_type': 'tag_relabel', 'employee_template': 'content_analyzer'}}
            ],
            'priority': 6,
            'description': '题目标签不准确时触发重新标注'
        },
        {
            'name': '题目格式标准化检查',
            'template_key': 'format_standardization',
            'category': 'quality_assurance',
            'conditions': [
                {'field': 'format_error_count', 'operator': 'greater_than', 'value': 5}
            ],
            'actions': [
                {'action_type': 'notify_admin', 'params': {'message': '题目格式错误超过5处，需要标准化', 'level': 'info'}},
                {'action_type': 'dispatch_task', 'params': {'task_type': 'format_fix', 'employee_template': 'format_fixer'}},
                {'action_type': 'call_api', 'params': {'url': '/api/question-bank-ai/ai/optimize', 'method': 'POST'}}
            ],
            'priority': 5,
            'description': '题目格式不规范时触发标准化'
        }
    ]
    
    STATISTICS_RULES = [
        {
            'name': '题库统计分析定时执行',
            'template_key': 'statistics_schedule',
            'category': 'statistics',
            'conditions': [
                {'field': 'hours_since_last_stats', 'operator': 'greater_than', 'value': 24}
            ],
            'actions': [
                {'action_type': 'dispatch_task', 'params': {'task_type': 'stats_analysis', 'employee_template': 'data_analyzer'}},
                {'action_type': 'call_api', 'params': {'url': '/api/question-bank-ai/ai/statistics', 'method': 'GET'}}
            ],
            'priority': 4,
            'description': '定期执行题库统计分析'
        },
        {
            'name': '题目使用热度分析',
            'template_key': 'usage_heat_analysis',
            'category': 'statistics',
            'conditions': [
                {'field': 'total_usage_events', 'operator': 'greater_than', 'value': 1000}
            ],
            'actions': [
                {'action_type': 'dispatch_task', 'params': {'task_type': 'heat_analysis', 'employee_template': 'data_analyzer'}},
                {'action_type': 'notify_admin', 'params': {'message': '已触发题目使用热度分析', 'level': 'info'}}
            ],
            'priority': 3,
            'description': '题目使用次数达到阈值时触发热度分析'
        },
        {
            'name': '题库质量报告生成',
            'template_key': 'quality_report_generate',
            'category': 'statistics',
            'conditions': [
                {'field': 'days_since_last_report', 'operator': 'greater_than', 'value': 7}
            ],
            'actions': [
                {'action_type': 'dispatch_task', 'params': {'task_type': 'report_generate', 'employee_template': 'report_generator'}},
                {'action_type': 'call_api', 'params': {'url': '/api/question-bank-ai/ai/summary', 'method': 'GET'}},
                {'action_type': 'notify_admin', 'params': {'message': '题库质量周报已生成', 'level': 'info'}}
            ],
            'priority': 5,
            'description': '定期生成题库质量报告'
        },
        {
            'name': '错题统计分析',
            'template_key': 'error_stats_analysis',
            'category': 'statistics',
            'conditions': [
                {'field': 'error_rate_threshold', 'operator': 'greater_than', 'value': 0.3},
                {'field': 'sample_size', 'operator': 'greater_than', 'value': 100}
            ],
            'actions': [
                {'action_type': 'dispatch_task', 'params': {'task_type': 'error_analysis', 'employee_template': 'data_analyzer'}},
                {'action_type': 'notify_admin', 'params': {'message': '题目错误率高，已触发错题分析', 'level': 'warning'}}
            ],
            'priority': 7,
            'description': '题目错误率高时触发错题统计分析'
        }
    ]
    
    AI_OPTIMIZATION_RULES = [
        {
            'name': 'AI题目自动优化',
            'template_key': 'ai_auto_optimize',
            'category': 'ai_optimization',
            'conditions': [
                {'field': 'pending_optimize_count', 'operator': 'greater_than', 'value': 50}
            ],
            'actions': [
                {'action_type': 'dispatch_task', 'params': {'task_type': 'batch_optimize', 'employee_template': 'question_optimizer'}},
                {'action_type': 'call_api', 'params': {'url': '/api/question-bank-ai/ai/batch-optimize', 'method': 'POST'}}
            ],
            'priority': 8,
            'description': '待优化题目过多时触发AI批量优化'
        },
        {
            'name': 'AI题目自动生成',
            'template_key': 'ai_auto_generate',
            'category': 'ai_optimization',
            'conditions': [
                {'field': 'auto_generate_enabled', 'operator': 'equals', 'value': True},
                {'field': 'generation_interval_hours', 'operator': 'greater_than', 'value': 12}
            ],
            'actions': [
                {'action_type': 'dispatch_task', 'params': {'task_type': 'auto_generate', 'employee_template': 'ai_question_generator'}},
                {'action_type': 'call_api', 'params': {'url': '/api/questions/generate', 'method': 'POST'}}
            ],
            'priority': 6,
            'description': '定时触发AI题目自动生成'
        },
        {
            'name': 'AI智能建议生成',
            'template_key': 'ai_suggestions',
            'category': 'ai_optimization',
            'conditions': [
                {'field': 'request_suggestions', 'operator': 'equals', 'value': True}
            ],
            'actions': [
                {'action_type': 'call_api', 'params': {'url': '/api/question-bank-ai/ai/suggestions', 'method': 'GET'}},
                {'action_type': 'notify_admin', 'params': {'message': 'AI优化建议已生成', 'level': 'info'}}
            ],
            'priority': 4,
            'description': '触发AI智能建议生成'
        },
        {
            'name': 'AI能力评估',
            'template_key': 'ai_capability_check',
            'category': 'ai_optimization',
            'conditions': [
                {'field': 'days_since_capability_check', 'operator': 'greater_than', 'value': 30}
            ],
            'actions': [
                {'action_type': 'call_api', 'params': {'url': '/api/question-bank-ai/ai/capabilities', 'method': 'GET'}},
                {'action_type': 'dispatch_task', 'params': {'task_type': 'capability_update', 'employee_template': 'system_optimizer'}}
            ],
            'priority': 3,
            'description': '定期评估AI题库优化能力'
        }
    ]
    
    ALL_TEMPLATES = (
        QUESTION_MANAGEMENT_RULES + 
        BANK_EXPANSION_RULES + 
        QUALITY_ASSURANCE_RULES + 
        STATISTICS_RULES + 
        AI_OPTIMIZATION_RULES
    )
    
    CATEGORIES = ['question_management', 'bank_expansion', 'quality_assurance', 'statistics', 'ai_optimization']