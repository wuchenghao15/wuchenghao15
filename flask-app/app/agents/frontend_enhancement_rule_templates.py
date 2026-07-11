# -*- coding: utf-8 -*-
"""
系统前端增强规则模板
支持前端系统自动规则创建、更新迭代，方便AI员工自动触发规则执行操作
"""

class FrontendEnhancementRuleTemplate:
    """系统前端增强规则模板"""
    
    # UI性能监控规则
    UI_PERFORMANCE_RULES = [
        {
            'name': '首屏加载超时告警',
            'template_key': 'first_screen_timeout',
            'category': 'ui_performance',
            'conditions': [
                {'field': 'first_contentful_paint', 'operator': 'greater_than', 'value': 3000}
            ],
            'actions': [
                {'action_type': 'notify_admin', 'params': {'message': '首屏加载超过3秒，影响用户体验', 'level': 'warning'}},
                {'action_type': 'dispatch_task', 'params': {'task_type': 'performance_optimization', 'employee_template': 'frontend_performance_engineer'}},
                {'action_type': 'call_api', 'params': {'url': '/api/frontend/optimize', 'method': 'POST'}}
            ],
            'priority': 12,
            'description': '首屏加载超时时触发性能优化'
        },
        {
            'name': '页面渲染卡顿检测',
            'template_key': 'page_render_jank',
            'category': 'ui_performance',
            'conditions': [
                {'field': 'long_task_count', 'operator': 'greater_than', 'value': 3},
                {'field': 'time_window_seconds', 'operator': 'less_than', 'value': 60}
            ],
            'actions': [
                {'action_type': 'notify_admin', 'params': {'message': '页面存在长任务阻塞，导致渲染卡顿', 'level': 'warning'}},
                {'action_type': 'dispatch_task', 'params': {'task_type': 'jank_investigation', 'employee_template': 'frontend_engineer'}},
                {'action_type': 'update_status', 'params': {'status': 'render_alert'}}
            ],
            'priority': 15,
            'description': '页面渲染卡顿时触发分析'
        },
        {
            'name': '内存泄漏检测',
            'template_key': 'memory_leak_detected',
            'category': 'ui_performance',
            'conditions': [
                {'field': 'memory_growth_percent', 'operator': 'greater_than', 'value': 50},
                {'field': 'navigation_count', 'operator': 'greater_than', 'value': 10}
            ],
            'actions': [
                {'action_type': 'notify_admin', 'params': {'message': '检测到内存泄漏，内存增长超过50%', 'level': 'critical'}},
                {'action_type': 'dispatch_task', 'params': {'task_type': 'memory_leak_fix', 'employee_template': 'frontend_engineer'}},
                {'action_type': 'update_status', 'params': {'status': 'memory_leak'}}
            ],
            'priority': 20,
            'description': '内存泄漏时触发紧急修复'
        },
        {
            'name': 'JS执行时间过长',
            'template_key': 'js_execution_timeout',
            'category': 'ui_performance',
            'conditions': [
                {'field': 'js_execution_time_ms', 'operator': 'greater_than', 'value': 500}
            ],
            'actions': [
                {'action_type': 'notify_admin', 'params': {'message': 'JavaScript执行时间超过500ms', 'level': 'warning'}},
                {'action_type': 'dispatch_task', 'params': {'task_type': 'js_optimization', 'employee_template': 'frontend_engineer'}}
            ],
            'priority': 10,
            'description': 'JS执行时间过长时触发优化'
        },
        {
            'name': 'CPU使用率过高',
            'template_key': 'cpu_usage_high',
            'category': 'ui_performance',
            'conditions': [
                {'field': 'cpu_usage_percent', 'operator': 'greater_than', 'value': 80},
                {'field': 'duration_seconds', 'operator': 'greater_than', 'value': 5}
            ],
            'actions': [
                {'action_type': 'notify_admin', 'params': {'message': '前端CPU使用率持续超过80%', 'level': 'warning'}},
                {'action_type': 'dispatch_task', 'params': {'task_type': 'cpu_profiling', 'employee_template': 'frontend_performance_engineer'}}
            ],
            'priority': 12,
            'description': 'CPU使用率过高时触发分析'
        }
    ]
    
    # 用户交互分析规则
    USER_INTERACTION_RULES = [
        {
            'name': '页面跳出率过高',
            'template_key': 'high_bounce_rate',
            'category': 'user_interaction',
            'conditions': [
                {'field': 'bounce_rate_percent', 'operator': 'greater_than', 'value': 70}
            ],
            'actions': [
                {'action_type': 'notify_admin', 'params': {'message': '页面跳出率超过70%，需要优化', 'level': 'warning'}},
                {'action_type': 'dispatch_task', 'params': {'task_type': 'bounce_rate_analysis', 'employee_template': 'ux_analyst'}},
                {'action_type': 'call_api', 'params': {'url': '/api/frontend/analytics', 'method': 'GET'}}
            ],
            'priority': 10,
            'description': '跳出率过高时触发分析优化'
        },
        {
            'name': '用户操作异常',
            'template_key': 'user_behavior_anomaly',
            'category': 'user_interaction',
            'conditions': [
                {'field': 'rage_click_count', 'operator': 'greater_than', 'value': 10},
                {'field': 'time_window_seconds', 'operator': 'less_than', 'value': 30}
            ],
            'actions': [
                {'action_type': 'notify_admin', 'params': {'message': '检测到用户狂点行为，可能存在交互问题', 'level': 'warning'}},
                {'action_type': 'dispatch_task', 'params': {'task_type': 'interaction_analysis', 'employee_template': 'ux_analyst'}}
            ],
            'priority': 8,
            'description': '用户操作异常时触发分析'
        },
        {
            'name': '表单提交失败率高',
            'template_key': 'form_submit_failure',
            'category': 'user_interaction',
            'conditions': [
                {'field': 'form_submit_failure_rate', 'operator': 'greater_than', 'value': 0.3}
            ],
            'actions': [
                {'action_type': 'notify_admin', 'params': {'message': '表单提交失败率超过30%', 'level': 'warning'}},
                {'action_type': 'dispatch_task', 'params': {'task_type': 'form_optimization', 'employee_template': 'frontend_engineer'}},
                {'action_type': 'update_status', 'params': {'status': 'form_error'}}
            ],
            'priority': 12,
            'description': '表单提交失败率高时触发优化'
        },
        {
            'name': '页面停留时间异常',
            'template_key': 'page_stay_time_anomaly',
            'category': 'user_interaction',
            'conditions': [
                {'field': 'avg_stay_time_seconds', 'operator': 'less_than', 'value': 10},
                {'field': 'page_views', 'operator': 'greater_than', 'value': 100}
            ],
            'actions': [
                {'action_type': 'notify_admin', 'params': {'message': '用户平均停留时间不足10秒', 'level': 'info'}},
                {'action_type': 'dispatch_task', 'params': {'task_type': 'content_optimization', 'employee_template': 'ux_analyst'}}
            ],
            'priority': 6,
            'description': '停留时间异常时触发内容优化'
        },
        {
            'name': '功能未使用检测',
            'template_key': 'feature_not_used',
            'category': 'user_interaction',
            'conditions': [
                {'field': 'feature_usage_rate', 'operator': 'less_than', 'value': 0.05},
                {'field': 'days_since_release', 'operator': 'greater_than', 'value': 30}
            ],
            'actions': [
                {'action_type': 'notify_admin', 'params': {'message': '功能发布30天后使用率低于5%', 'level': 'info'}},
                {'action_type': 'dispatch_task', 'params': {'task_type': 'feature_review', 'employee_template': 'product_manager'}}
            ],
            'priority': 5,
            'description': '功能使用率低时触发评估'
        }
    ]
    
    # 前端错误监控规则
    FRONTEND_ERROR_RULES = [
        {
            'name': 'JS错误率过高',
            'template_key': 'js_error_rate_high',
            'category': 'frontend_error',
            'conditions': [
                {'field': 'js_error_rate', 'operator': 'greater_than', 'value': 0.01}
            ],
            'actions': [
                {'action_type': 'notify_admin', 'params': {'message': 'JavaScript错误率超过1%', 'level': 'warning'}},
                {'action_type': 'dispatch_task', 'params': {'task_type': 'error_investigation', 'employee_template': 'frontend_engineer'}},
                {'action_type': 'call_api', 'params': {'url': '/api/frontend/errors', 'method': 'GET'}}
            ],
            'priority': 18,
            'description': 'JS错误率过高时触发调查'
        },
        {
            'name': '资源加载失败',
            'template_key': 'resource_load_failure',
            'category': 'frontend_error',
            'conditions': [
                {'field': 'resource_failure_count', 'operator': 'greater_than', 'value': 10},
                {'field': 'time_window_minutes', 'operator': 'less_than', 'value': 10}
            ],
            'actions': [
                {'action_type': 'notify_admin', 'params': {'message': '前端资源加载失败次数过多', 'level': 'warning'}},
                {'action_type': 'dispatch_task', 'params': {'task_type': 'resource_fix', 'employee_template': 'frontend_engineer'}},
                {'action_type': 'update_status', 'params': {'status': 'resource_error'}}
            ],
            'priority': 15,
            'description': '资源加载失败时触发修复'
        },
        {
            'name': '网络请求失败',
            'template_key': 'network_request_failure',
            'category': 'frontend_error',
            'conditions': [
                {'field': 'network_error_rate', 'operator': 'greater_than', 'value': 0.05}
            ],
            'actions': [
                {'action_type': 'notify_admin', 'params': {'message': '前端网络请求失败率超过5%', 'level': 'warning'}},
                {'action_type': 'dispatch_task', 'params': {'task_type': 'network_optimization', 'employee_template': 'frontend_engineer'}}
            ],
            'priority': 12,
            'description': '网络请求失败时触发优化'
        },
        {
            'name': 'DOM异常检测',
            'template_key': 'dom_exception_detected',
            'category': 'frontend_error',
            'conditions': [
                {'field': 'dom_exception_count', 'operator': 'greater_than', 'value': 5},
                {'field': 'time_window_minutes', 'operator': 'less_than', 'value': 5}
            ],
            'actions': [
                {'action_type': 'notify_admin', 'params': {'message': '检测到DOM异常', 'level': 'warning'}},
                {'action_type': 'dispatch_task', 'params': {'task_type': 'dom_debug', 'employee_template': 'frontend_engineer'}}
            ],
            'priority': 10,
            'description': 'DOM异常时触发调试'
        },
        {
            'name': '兼容性错误检测',
            'template_key': 'compatibility_error',
            'category': 'frontend_error',
            'conditions': [
                {'field': 'browser_specific_errors', 'operator': 'greater_than', 'value': 0}
            ],
            'actions': [
                {'action_type': 'notify_admin', 'params': {'message': '检测到浏览器兼容性错误', 'level': 'warning'}},
                {'action_type': 'dispatch_task', 'params': {'task_type': 'browser_compatibility', 'employee_template': 'frontend_engineer'}}
            ],
            'priority': 10,
            'description': '兼容性错误时触发修复'
        }
    ]
    
    # 页面加载优化规则
    PAGE_LOAD_RULES = [
        {
            'name': 'LCP性能指标不达标',
            'template_key': 'lcp_performance_failure',
            'category': 'page_load',
            'conditions': [
                {'field': 'largest_contentful_paint', 'operator': 'greater_than', 'value': 2500}
            ],
            'actions': [
                {'action_type': 'notify_admin', 'params': {'message': 'LCP性能指标不达标（>2.5s）', 'level': 'warning'}},
                {'action_type': 'dispatch_task', 'params': {'task_type': 'lcp_optimization', 'employee_template': 'frontend_performance_engineer'}},
                {'action_type': 'call_api', 'params': {'url': '/api/frontend/optimize/lcp', 'method': 'POST'}}
            ],
            'priority': 15,
            'description': 'LCP不达标时触发优化'
        },
        {
            'name': 'FID响应时间过长',
            'template_key': 'fid_response_slow',
            'category': 'page_load',
            'conditions': [
                {'field': 'first_input_delay', 'operator': 'greater_than', 'value': 200}
            ],
            'actions': [
                {'action_type': 'notify_admin', 'params': {'message': 'FID超过200ms，影响交互体验', 'level': 'warning'}},
                {'action_type': 'dispatch_task', 'params': {'task_type': 'fid_optimization', 'employee_template': 'frontend_performance_engineer'}}
            ],
            'priority': 12,
            'description': 'FID过长时触发优化'
        },
        {
            'name': 'CLS布局偏移过大',
            'template_key': 'cls_layout_shift',
            'category': 'page_load',
            'conditions': [
                {'field': 'cumulative_layout_shift', 'operator': 'greater_than', 'value': 0.25}
            ],
            'actions': [
                {'action_type': 'notify_admin', 'params': {'message': 'CLS超过0.25，布局偏移过大', 'level': 'warning'}},
                {'action_type': 'dispatch_task', 'params': {'task_type': 'layout_stability', 'employee_template': 'frontend_engineer'}}
            ],
            'priority': 10,
            'description': 'CLS过大时触发优化'
        },
        {
            'name': '资源体积过大',
            'template_key': 'resource_size_excessive',
            'category': 'page_load',
            'conditions': [
                {'field': 'total_resource_size_mb', 'operator': 'greater_than', 'value': 2}
            ],
            'actions': [
                {'action_type': 'notify_admin', 'params': {'message': '页面总资源超过2MB，需要压缩', 'level': 'warning'}},
                {'action_type': 'dispatch_task', 'params': {'task_type': 'asset_compression', 'employee_template': 'frontend_engineer'}},
                {'action_type': 'call_api', 'params': {'url': '/api/frontend/optimize/compress', 'method': 'POST'}}
            ],
            'priority': 12,
            'description': '资源体积过大时触发压缩'
        },
        {
            'name': '未使用CSS检测',
            'template_key': 'unused_css_detected',
            'category': 'page_load',
            'conditions': [
                {'field': 'unused_css_percent', 'operator': 'greater_than', 'value': 50}
            ],
            'actions': [
                {'action_type': 'notify_admin', 'params': {'message': '未使用CSS超过50%', 'level': 'info'}},
                {'action_type': 'dispatch_task', 'params': {'task_type': 'css_cleanup', 'employee_template': 'frontend_engineer'}}
            ],
            'priority': 8,
            'description': '未使用CSS过多时触发清理'
        }
    ]
    
    # 响应式设计规则
    RESPONSIVE_DESIGN_RULES = [
        {
            'name': '移动端适配问题',
            'template_key': 'mobile_adaptation_issue',
            'category': 'responsive_design',
            'conditions': [
                {'field': 'mobile_viewport_errors', 'operator': 'greater_than', 'value': 0}
            ],
            'actions': [
                {'action_type': 'notify_admin', 'params': {'message': '检测到移动端适配问题', 'level': 'warning'}},
                {'action_type': 'dispatch_task', 'params': {'task_type': 'mobile_fix', 'employee_template': 'frontend_engineer'}},
                {'action_type': 'update_status', 'params': {'status': 'mobile_issue'}}
            ],
            'priority': 10,
            'description': '移动端适配问题时触发修复'
        },
        {
            'name': '平板端布局异常',
            'template_key': 'tablet_layout_anomaly',
            'category': 'responsive_design',
            'conditions': [
                {'field': 'tablet_layout_issues', 'operator': 'greater_than', 'value': 0}
            ],
            'actions': [
                {'action_type': 'notify_admin', 'params': {'message': '检测到平板端布局异常', 'level': 'info'}},
                {'action_type': 'dispatch_task', 'params': {'task_type': 'tablet_fix', 'employee_template': 'frontend_engineer'}}
            ],
            'priority': 6,
            'description': '平板端布局异常时触发修复'
        },
        {
            'name': '断点设置不合理',
            'template_key': 'breakpoint_misconfiguration',
            'category': 'responsive_design',
            'conditions': [
                {'field': 'breakpoint_overlap', 'operator': 'equals', 'value': True}
            ],
            'actions': [
                {'action_type': 'notify_admin', 'params': {'message': '响应式断点设置存在重叠', 'level': 'info'}},
                {'action_type': 'dispatch_task', 'params': {'task_type': 'breakpoint_optimization', 'employee_template': 'frontend_engineer'}}
            ],
            'priority': 5,
            'description': '断点设置不合理时触发优化'
        },
        {
            'name': '字体大小适配问题',
            'template_key': 'font_size_adaptation',
            'category': 'responsive_design',
            'conditions': [
                {'field': 'font_size_issues', 'operator': 'greater_than', 'value': 0}
            ],
            'actions': [
                {'action_type': 'notify_admin', 'params': {'message': '检测到字体大小适配问题', 'level': 'info'}},
                {'action_type': 'dispatch_task', 'params': {'task_type': 'font_adaptation', 'employee_template': 'frontend_engineer'}}
            ],
            'priority': 5,
            'description': '字体大小适配问题时触发修复'
        }
    ]
    
    # 前端安全规则
    FRONTEND_SECURITY_RULES = [
        {
            'name': 'XSS攻击检测',
            'template_key': 'xss_attack_detected',
            'category': 'frontend_security',
            'conditions': [
                {'field': 'xss_pattern_detected', 'operator': 'equals', 'value': True}
            ],
            'actions': [
                {'action_type': 'notify_admin', 'params': {'message': '检测到XSS攻击尝试', 'level': 'critical'}},
                {'action_type': 'dispatch_task', 'params': {'task_type': 'xss_investigation', 'employee_template': 'security_engineer'}},
                {'action_type': 'update_status', 'params': {'status': 'xss_alert'}}
            ],
            'priority': 25,
            'description': 'XSS攻击时触发紧急响应'
        },
        {
            'name': 'CSRF防护缺失',
            'template_key': 'csrf_protection_missing',
            'category': 'frontend_security',
            'conditions': [
                {'field': 'csrf_token_missing', 'operator': 'equals', 'value': True}
            ],
            'actions': [
                {'action_type': 'notify_admin', 'params': {'message': '检测到CSRF防护缺失', 'level': 'critical'}},
                {'action_type': 'dispatch_task', 'params': {'task_type': 'csrf_implementation', 'employee_template': 'security_engineer'}}
            ],
            'priority': 22,
            'description': 'CSRF防护缺失时触发修复'
        },
        {
            'name': '敏感信息泄露',
            'template_key': 'sensitive_info_leak',
            'category': 'frontend_security',
            'conditions': [
                {'field': 'sensitive_data_in_frontend', 'operator': 'equals', 'value': True}
            ],
            'actions': [
                {'action_type': 'notify_admin', 'params': {'message': '检测到敏感信息在前端泄露', 'level': 'critical'}},
                {'action_type': 'dispatch_task', 'params': {'task_type': 'data_hide', 'employee_template': 'security_engineer'}},
                {'action_type': 'update_status', 'params': {'status': 'data_leak'}}
            ],
            'priority': 25,
            'description': '敏感信息泄露时触发紧急处理'
        },
        {
            'name': 'iframe安全风险',
            'template_key': 'iframe_security_risk',
            'category': 'frontend_security',
            'conditions': [
                {'field': 'untrusted_iframe', 'operator': 'equals', 'value': True}
            ],
            'actions': [
                {'action_type': 'notify_admin', 'params': {'message': '检测到不受信任的iframe', 'level': 'warning'}},
                {'action_type': 'dispatch_task', 'params': {'task_type': 'iframe_security', 'employee_template': 'security_engineer'}}
            ],
            'priority': 15,
            'description': 'iframe安全风险时触发处理'
        },
        {
            'name': 'CSP策略违规',
            'template_key': 'csp_policy_violation',
            'category': 'frontend_security',
            'conditions': [
                {'field': 'csp_violation_count', 'operator': 'greater_than', 'value': 10}
            ],
            'actions': [
                {'action_type': 'notify_admin', 'params': {'message': 'CSP策略违规次数过多', 'level': 'warning'}},
                {'action_type': 'dispatch_task', 'params': {'task_type': 'csp_fix', 'employee_template': 'security_engineer'}}
            ],
            'priority': 12,
            'description': 'CSP违规时触发修复'
        }
    ]
    
    # 用户体验优化规则
    USER_EXPERIENCE_RULES = [
        {
            'name': '加载状态缺失',
            'template_key': 'loading_state_missing',
            'category': 'user_experience',
            'conditions': [
                {'field': 'loading_indicator_missing', 'operator': 'equals', 'value': True},
                {'field': 'api_response_time_ms', 'operator': 'greater_than', 'value': 1000}
            ],
            'actions': [
                {'action_type': 'notify_admin', 'params': {'message': '长时间请求缺少加载状态提示', 'level': 'info'}},
                {'action_type': 'dispatch_task', 'params': {'task_type': 'loading_implementation', 'employee_template': 'ux_engineer'}}
            ],
            'priority': 6,
            'description': '加载状态缺失时触发添加'
        },
        {
            'name': '错误提示不友好',
            'template_key': 'error_message_unfriendly',
            'category': 'user_experience',
            'conditions': [
                {'field': 'error_message_technical', 'operator': 'equals', 'value': True}
            ],
            'actions': [
                {'action_type': 'notify_admin', 'params': {'message': '错误提示过于技术化，用户难以理解', 'level': 'info'}},
                {'action_type': 'dispatch_task', 'params': {'task_type': 'error_message_improve', 'employee_template': 'ux_engineer'}}
            ],
            'priority': 5,
            'description': '错误提示不友好时触发优化'
        },
        {
            'name': '导航体验不佳',
            'template_key': 'navigation_experience_poor',
            'category': 'user_experience',
            'conditions': [
                {'field': 'navigation_clicks', 'operator': 'greater_than', 'value': 5},
                {'field': 'goal_page_reached', 'operator': 'equals', 'value': False}
            ],
            'actions': [
                {'action_type': 'notify_admin', 'params': {'message': '用户需要多次点击才能到达目标页面', 'level': 'info'}},
                {'action_type': 'dispatch_task', 'params': {'task_type': 'navigation_optimization', 'employee_template': 'ux_engineer'}}
            ],
            'priority': 5,
            'description': '导航体验不佳时触发优化'
        },
        {
            'name': '按钮可点击性问题',
            'template_key': 'button_clickability_issue',
            'category': 'user_experience',
            'conditions': [
                {'field': 'button_hover_area', 'operator': 'less_than', 'value': 48}
            ],
            'actions': [
                {'action_type': 'notify_admin', 'params': {'message': '按钮点击区域过小', 'level': 'info'}},
                {'action_type': 'dispatch_task', 'params': {'task_type': 'button_improve', 'employee_template': 'ux_engineer'}}
            ],
            'priority': 4,
            'description': '按钮可点击性问题时触发优化'
        },
        {
            'name': '颜色对比度不足',
            'template_key': 'color_contrast_insufficient',
            'category': 'user_experience',
            'conditions': [
                {'field': 'color_contrast_ratio', 'operator': 'less_than', 'value': 4.5}
            ],
            'actions': [
                {'action_type': 'notify_admin', 'params': {'message': '颜色对比度不足，影响可访问性', 'level': 'info'}},
                {'action_type': 'dispatch_task', 'params': {'task_type': 'contrast_improve', 'employee_template': 'ux_engineer'}}
            ],
            'priority': 5,
            'description': '颜色对比度不足时触发优化'
        }
    ]
    
    # 前端资源管理规则
    RESOURCE_MANAGEMENT_RULES = [
        {
            'name': '缓存策略不合理',
            'template_key': 'cache_strategy_inefficient',
            'category': 'resource_management',
            'conditions': [
                {'field': 'cache_hit_rate', 'operator': 'less_than', 'value': 0.7}
            ],
            'actions': [
                {'action_type': 'notify_admin', 'params': {'message': '缓存命中率低于70%', 'level': 'warning'}},
                {'action_type': 'dispatch_task', 'params': {'task_type': 'cache_optimization', 'employee_template': 'frontend_engineer'}},
                {'action_type': 'call_api', 'params': {'url': '/api/frontend/cache-config', 'method': 'POST'}}
            ],
            'priority': 10,
            'description': '缓存策略不合理时触发优化'
        },
        {
            'name': '图片格式不优化',
            'template_key': 'image_format_not_optimized',
            'category': 'resource_management',
            'conditions': [
                {'field': 'unoptimized_image_count', 'operator': 'greater_than', 'value': 5}
            ],
            'actions': [
                {'action_type': 'notify_admin', 'params': {'message': '存在未优化的图片', 'level': 'info'}},
                {'action_type': 'dispatch_task', 'params': {'task_type': 'image_optimization', 'employee_template': 'frontend_engineer'}}
            ],
            'priority': 6,
            'description': '图片格式不优化时触发处理'
        },
        {
            'name': 'JS依赖过多',
            'template_key': 'js_dependencies_excessive',
            'category': 'resource_management',
            'conditions': [
                {'field': 'js_bundle_count', 'operator': 'greater_than', 'value': 20}
            ],
            'actions': [
                {'action_type': 'notify_admin', 'params': {'message': 'JS依赖包过多，需要优化', 'level': 'info'}},
                {'action_type': 'dispatch_task', 'params': {'task_type': 'dependency_review', 'employee_template': 'frontend_engineer'}}
            ],
            'priority': 6,
            'description': 'JS依赖过多时触发优化'
        },
        {
            'name': '静态资源版本管理缺失',
            'template_key': 'asset_versioning_missing',
            'category': 'resource_management',
            'conditions': [
                {'field': 'asset_versioning_enabled', 'operator': 'equals', 'value': False}
            ],
            'actions': [
                {'action_type': 'notify_admin', 'params': {'message': '静态资源缺少版本管理', 'level': 'info'}},
                {'action_type': 'dispatch_task', 'params': {'task_type': 'versioning_implementation', 'employee_template': 'frontend_engineer'}}
            ],
            'priority': 5,
            'description': '版本管理缺失时触发添加'
        },
        {
            'name': 'CDN配置异常',
            'template_key': 'cdn_configuration_anomaly',
            'category': 'resource_management',
            'conditions': [
                {'field': 'cdn_availability', 'operator': 'equals', 'value': False}
            ],
            'actions': [
                {'action_type': 'notify_admin', 'params': {'message': 'CDN不可用', 'level': 'warning'}},
                {'action_type': 'dispatch_task', 'params': {'task_type': 'cdn_fix', 'employee_template': 'devops_engineer'}}
            ],
            'priority': 15,
            'description': 'CDN配置异常时触发修复'
        }
    ]
    
    ALL_TEMPLATES = (
        UI_PERFORMANCE_RULES + 
        USER_INTERACTION_RULES + 
        FRONTEND_ERROR_RULES + 
        PAGE_LOAD_RULES + 
        RESPONSIVE_DESIGN_RULES +
        FRONTEND_SECURITY_RULES +
        USER_EXPERIENCE_RULES +
        RESOURCE_MANAGEMENT_RULES
    )
    
    CATEGORIES = [
        'ui_performance',
        'user_interaction',
        'frontend_error',
        'page_load',
        'responsive_design',
        'frontend_security',
        'user_experience',
        'resource_management'
    ]