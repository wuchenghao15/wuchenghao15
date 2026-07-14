# -*- coding: utf-8 -*-
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
AI能力细化模块
自动向下细化AI功能及专业能力, 为不同领域的AI分配专业任务
"""

import os
import json
import logging
import threading
from datetime import datetime
from typing import Dict, List, Any, Optional
import sys

logger = logging.getLogger('ai_capability_refiner')


class AICapabilityRefiner:
    """AI能力细化类"""

    def __init__(self):
        """初始化AI能力细化器"""
        self.capabilities = {
            'general': {
                'name': '通用AI',
                'description': '具备基本的AI能力,可处理多种任务',
                'skills': ['natural_language_processing', 'basic_reasoning', 'general_knowledge']
            },
            'engineering': {
                'name': '工程AI',
                'description': '专注于软件工程和系统维护',
                'skills': ['code_analysis', 'performance_monitoring', 'security_scanning', 'network_knowledge']
            },
            'frontend_engineering': {
                'name': '前端工程AI',
                'description': '专注于前端开发和用户界面',
                'skills': ['frontend_code_analysis', 'frontend_performance_monitoring', 'frontend_security_scanning', 'frontend_frameworks']
            },
            'backend_engineering': {
                'name': '后端工程AI',
                'description': '专注于后端开发和服务器架构',
                'skills': ['backend_code_analysis', 'backend_performance_monitoring', 'backend_security_scanning', 'database_management']
            },
            'mobile_engineering': {
                'name': '移动应用工程AI',
                'description': '专注于移动应用开发',
                'skills': ['mobile_code_analysis', 'mobile_performance_monitoring', 'mobile_security_scanning', 'mobile_frameworks']
            },
            'devops_engineering': {
                'name': 'DevOps工程AI',
                'description': '专注于开发运维和自动化',
                'skills': ['devops_code_analysis', 'devops_performance_monitoring', 'devops_security_scanning', 'automation_tools']
            },
            'education': {
                'name': '教育AI',
                'description': '专注于教育和学习领域',
                'skills': ['question_generation', 'student_assessment', 'learning_analysis', 'content_curation']
            },
            'math_teacher': {
                'name': '数学教师AI',
                'description': '专注于数学教育领域',
                'skills': ['math_question_generation', 'math_student_assessment', 'math_learning_analysis', 'math_content_curation']
            },
            'language_teacher': {
                'name': '语言教师AI',
                'description': '专注于语言教育领域',
                'skills': ['language_question_generation', 'language_student_assessment', 'language_learning_analysis', 'language_content_curation']
            },
            'science_teacher': {
                'name': '科学教师AI',
                'description': '专注于科学教育领域',
                'skills': ['science_question_generation', 'science_student_assessment', 'science_learning_analysis', 'science_content_curation']
            },
            'history_teacher': {
                'name': '历史教师AI',
                'description': '专注于历史教育领域',
                'skills': ['history_question_generation', 'history_student_assessment', 'history_learning_analysis', 'history_content_curation']
            },
            'art_teacher': {
                'name': '艺术教师AI',
                'description': '专注于艺术教育领域',
                'skills': ['art_question_generation', 'art_student_assessment', 'art_learning_analysis', 'art_content_curation']
            },
            'network': {
                'name': '网络AI',
                'description': '专注于网络管理和安全',
                'skills': ['network_monitoring', 'security_analysis', 'traffic_optimization', 'threat_detection']
            },
            'network_security': {
                'name': '网络安全AI',
                'description': '专注于网络安全和防护',
                'skills': ['network_security_monitoring', 'security_threat_analysis', 'security_incident_response', 'security_policies']
            },
            'network_operations': {
                'name': '网络运维AI',
                'description': '专注于网络运维和管理',
                'skills': ['network_operations_monitoring', 'network_troubleshooting', 'network_performance_optimization', 'network_documentation']
            },
            'network_architecture': {
                'name': '网络架构AI',
                'description': '专注于网络架构设计和规划',
                'skills': ['network_architecture_design', 'network_scalability_planning', 'network_security_architecture', 'network_technology_evaluation']
            },
            'exam': {
                'name': '考试AI',
                'description': '专注于考试和评估',
                'skills': ['exam_generation', 'answer_analysis', 'performance_evaluation', 'adaptive_testing']
            },
            'design': {
                'name': '设计AI',
                'description': '专注于UI/UX设计',
                'skills': ['ui_design', 'ux_analysis', 'visualization', 'design_recommendation']
            },
            'ui_design': {
                'name': 'UI设计AI',
                'description': '专注于用户界面设计',
                'skills': ['ui_visual_design', 'ui_component_design', 'ui_responsive_design', 'ui_style_guide']
            },
            'ux_design': {
                'name': 'UX设计AI',
                'description': '专注于用户体验设计',
                'skills': ['ux_user_research', 'ux_journey_mapping', 'ux_prototyping', 'ux_usability_testing']
            },
            'graphic_design': {
                'name': '平面设计AI',
                'description': '专注于平面设计和视觉传达',
                'skills': ['graphic_layout_design', 'graphic_color_theory', 'graphic_typography', 'graphic_branding']
            },
            'product_design': {
                'name': '产品设计AI',
                'description': '专注于产品设计和创新',
                'skills': ['product_requirements_analysis', 'product_user_story', 'product_feature_design', 'product_iteration']
            },
            'user_behavior': {
                'name': '用户行为AI',
                'description': '专注于用户行为分析',
                'skills': ['behavior_analysis', 'preference_learning', 'recommendation', 'user_segmentation']
            },
            'user_behavior_analysis': {
                'name': '用户行为分析AI',
                'description': '专注于用户行为数据分析',
                'skills': ['behavior_data_analysis', 'behavior_pattern_recognition', 'behavior_metrics_tracking', 'behavior_reporting']
            },
            'user_profiling': {
                'name': '用户画像AI',
                'description': '专注于用户画像和细分',
                'skills': ['user_profiling', 'user_segmentation_advanced', 'user_persona_creation', 'user_demographic_analysis']
            },
            'recommendation_system': {
                'name': '推荐系统AI',
                'description': '专注于推荐系统和个性化',
                'skills': ['recommendation_system_design', 'recommendation_algorithm_optimization', 'recommendation_evaluation', 'recommendation_personalization']
            },
            'user_behavior_prediction': {
                'name': '用户行为预测AI',
                'description': '专注于用户行为预测和分析',
                'skills': ['behavior_prediction_modeling', 'behavior_forecasting', 'anomaly_detection', 'trend_analysis']
            }
        }

        self.skill_mapping = {
            'code_analysis': {
                'description': '分析代码质量和安全性',
                'required_knowledge': ['programming_languages', 'code_patterns', 'security_best_practices']
            },
            'performance_monitoring': {
                'description': '监控系统性能',
                'required_knowledge': ['system_metrics', 'performance_benchmarks', 'optimization_techniques']
            },
            'security_scanning': {
                'description': '扫描系统安全漏洞',
                'required_knowledge': ['security_vulnerabilities', 'penetration_testing', 'secure_coding']
            },
            'network_knowledge': {
                'description': '网络知识和管理',
                'required_knowledge': ['network_protocols', 'network_topology', 'network_security']
            },
            'question_generation': {
                'description': '生成教育题目',
                'required_knowledge': ['curriculum_standards', 'question_types', 'difficulty_levels']
            },
            'student_assessment': {
                'description': '评估学生表现',
                'required_knowledge': ['assessment_methods', 'learning_objectives', 'grading_scales']
            },
            'learning_analysis': {
                'description': '分析学习数据',
                'required_knowledge': ['learning_analytics', 'data_mining', 'educational_statistics']
            },
            'content_curation': {
                'description': '内容管理和推荐',
                'required_knowledge': ['content_standards', 'recommendation_algorithms', 'content_organization']
            },
            'math_question_generation': {
                'description': '生成数学题目',
                'required_knowledge': ['mathematics_curriculum', 'math_question_types', 'math_difficulty_levels']
            },
            'math_student_assessment': {
                'description': '评估学生数学表现',
                'required_knowledge': ['math_assessment_methods', 'math_learning_objectives', 'math_grading_scales']
            },
            'math_learning_analysis': {
                'description': '分析数学学习数据',
                'required_knowledge': ['math_learning_analytics', 'math_data_mining', 'math_educational_statistics']
            },
            'math_content_curation': {
                'description': '数学内容管理和推荐',
                'required_knowledge': ['math_content_standards', 'math_recommendation_algorithms', 'math_content_organization']
            },
            'language_question_generation': {
                'description': '生成语言题目',
                'required_knowledge': ['language_curriculum', 'language_question_types', 'language_difficulty_levels']
            },
            'language_student_assessment': {
                'description': '评估学生语言表现',
                'required_knowledge': ['language_assessment_methods', 'language_learning_objectives', 'language_grading_scales']
            },
            'language_learning_analysis': {
                'description': '分析语言学习数据',
                'required_knowledge': ['language_learning_analytics', 'language_data_mining', 'language_educational_statistics']
            },
            'language_content_curation': {
                'description': '语言内容管理和推荐',
                'required_knowledge': ['language_content_standards', 'language_recommendation_algorithms', 'language_content_organization']
            },
            'science_question_generation': {
                'description': '生成科学题目',
                'required_knowledge': ['science_curriculum', 'science_question_types', 'science_difficulty_levels']
            },
            'science_student_assessment': {
                'description': '评估学生科学表现',
                'required_knowledge': ['science_assessment_methods', 'science_learning_objectives', 'science_grading_scales']
            },
            'science_learning_analysis': {
                'description': '分析科学学习数据',
                'required_knowledge': ['science_learning_analytics', 'science_data_mining', 'science_educational_statistics']
            },
            'science_content_curation': {
                'description': '科学内容管理和推荐',
                'required_knowledge': ['science_content_standards', 'science_recommendation_algorithms', 'science_content_organization']
            },
            'history_question_generation': {
                'description': '生成历史题目',
                'required_knowledge': ['history_curriculum', 'history_question_types', 'history_difficulty_levels']
            },
            'history_student_assessment': {
                'description': '评估学生历史表现',
                'required_knowledge': ['history_assessment_methods', 'history_learning_objectives', 'history_grading_scales']
            },
            'history_learning_analysis': {
                'description': '分析历史学习数据',
                'required_knowledge': ['history_learning_analytics', 'history_data_mining', 'history_educational_statistics']
            },
            'history_content_curation': {
                'description': '历史内容管理和推荐',
                'required_knowledge': ['history_content_standards', 'history_recommendation_algorithms', 'history_content_organization']
            },
            'art_question_generation': {
                'description': '生成艺术题目',
                'required_knowledge': ['art_curriculum', 'art_question_types', 'art_difficulty_levels']
            },
            'art_student_assessment': {
                'description': '评估学生艺术表现',
                'required_knowledge': ['art_assessment_methods', 'art_learning_objectives', 'art_grading_scales']
            },
            'art_learning_analysis': {
                'description': '分析艺术学习数据',
                'required_knowledge': ['art_learning_analytics', 'art_data_mining', 'art_educational_statistics']
            },
            'art_content_curation': {
                'description': '艺术内容管理和推荐',
                'required_knowledge': ['art_content_standards', 'art_recommendation_algorithms', 'art_content_organization']
            },
            'network_monitoring': {
                'description': '监控网络状态',
                'required_knowledge': ['network_monitoring_tools', 'alerting_systems', 'network_performance']
            },
            'security_analysis': {
                'description': '分析安全威胁',
                'required_knowledge': ['threat_intelligence', 'security_analytics', 'incident_response']
            },
            'traffic_optimization': {
                'description': '优化网络流量',
                'required_knowledge': ['traffic_analysis', 'load_balancing', 'network_optimization']
            },
            'threat_detection': {
                'description': '检测安全威胁',
                'required_knowledge': ['threat_models', 'anomaly_detection', 'security_monitoring']
            },
            'exam_generation': {
                'description': '生成考试试卷',
                'required_knowledge': ['exam_standards', 'question_banking', 'test_construction']
            },
            'answer_analysis': {
                'description': '分析答案质量',
                'required_knowledge': ['answer_grading', 'rubrics', 'feedback_generation']
            },
            'performance_evaluation': {
                'description': '评估考试表现',
                'required_knowledge': ['performance_metrics', 'statistical_analysis', 'reporting']
            },
            'adaptive_testing': {
                'description': '自适应测试',
                'required_knowledge': ['item_response_theory', 'adaptive_algorithms', 'personalization']
            },
            'ui_design': {
                'description': '用户界面设计',
                'required_knowledge': ['design_principles', 'visual_hierarchy', 'user_interface_patterns']
            },
            'ux_analysis': {
                'description': '用户体验分析',
                'required_knowledge': ['user_research', 'usability_testing', 'ux_metrics']
            },
            'visualization': {
                'description': '数据可视化',
                'required_knowledge': ['data_visualization', 'information_design', 'visual_perception']
            },
            'design_recommendation': {
                'description': '设计推荐',
                'required_knowledge': ['design_trends', 'best_practices', 'user_preferences']
            },
            'behavior_analysis': {
                'description': '分析用户行为',
                'required_knowledge': ['behavioral_science', 'user_journeys', 'interaction_analysis']
            },
            'preference_learning': {
                'description': '学习用户偏好',
                'required_knowledge': ['preference_modeling', 'collaborative_filtering', 'personalization']
            },
            'recommendation': {
                'description': '推荐内容',
                'required_knowledge': ['recommendation_systems', 'content_based_filtering', 'hybrid_methods']
            },
            'user_segmentation': {
                'description': '用户细分',
                'required_knowledge': ['clustering_algorithms', 'demographic_analysis', 'behavioral_segmentation']
            },
            'natural_language_processing': {
                'description': '自然语言处理',
                'required_knowledge': ['nlp_techniques', 'language_models', 'text_analysis']
            },
            'basic_reasoning': {
                'description': '基本推理能力',
                'required_knowledge': ['logic', 'problem_solving', 'critical_thinking']
            },
            'general_knowledge': {
                'description': '通用知识',
                'required_knowledge': ['world_knowledge', 'common_sense', 'current_events']
            },
            'frontend_code_analysis': {
                'description': '分析前端代码质量和安全性',
                'required_knowledge': ['frontend_languages', 'frontend_frameworks', 'frontend_code_patterns', 'frontend_security']
            },
            'frontend_performance_monitoring': {
                'description': '监控前端性能',
                'required_knowledge': ['frontend_metrics', 'frontend_performance_benchmarks', 'frontend_optimization']
            },
            'frontend_security_scanning': {
                'description': '扫描前端安全漏洞',
                'required_knowledge': ['frontend_security_vulnerabilities', 'frontend_secure_coding', 'frontend_security_tools']
            },
            'frontend_frameworks': {
                'description': '前端框架和库',
                'required_knowledge': ['react', 'vue', 'angular', 'frontend_build_tools']
            },
            'backend_code_analysis': {
                'description': '分析后端代码质量和安全性',
                'required_knowledge': ['backend_languages', 'backend_frameworks', 'backend_code_patterns', 'backend_security']
            },
            'backend_performance_monitoring': {
                'description': '监控后端性能',
                'required_knowledge': ['backend_metrics', 'backend_performance_benchmarks', 'backend_optimization']
            },
            'backend_security_scanning': {
                'description': '扫描后端安全漏洞',
                'required_knowledge': ['backend_security_vulnerabilities', 'backend_secure_coding', 'backend_security_tools']
            },
            'database_management': {
                'description': '数据库管理和优化',
                'required_knowledge': ['database_systems', 'sql', 'database_optimization', 'database_security']
            },
            'mobile_code_analysis': {
                'description': '分析移动应用代码质量和安全性',
                'required_knowledge': ['mobile_languages', 'mobile_frameworks', 'mobile_code_patterns', 'mobile_security']
            },
            'mobile_performance_monitoring': {
                'description': '监控移动应用性能',
                'required_knowledge': ['mobile_metrics', 'mobile_performance_benchmarks', 'mobile_optimization']
            },
            'mobile_security_scanning': {
                'description': '扫描移动应用安全漏洞',
                'required_knowledge': ['mobile_security_vulnerabilities', 'mobile_secure_coding', 'mobile_security_tools']
            },
            'mobile_frameworks': {
                'description': '移动应用框架',
                'required_knowledge': ['ios_development', 'android_development', 'cross_platform_frameworks', 'mobile_ui_frameworks']
            },
            'devops_code_analysis': {
                'description': '分析DevOps代码质量和安全性',
                'required_knowledge': ['devops_languages', 'devops_tools', 'devops_code_patterns', 'devops_security']
            },
            'devops_performance_monitoring': {
                'description': '监控DevOps性能',
                'required_knowledge': ['devops_metrics', 'devops_performance_benchmarks', 'devops_optimization']
            },
            'devops_security_scanning': {
                'description': '扫描DevOps安全漏洞',
                'required_knowledge': ['devops_security_vulnerabilities', 'devops_secure_coding', 'devops_security_tools']
            },
            'automation_tools': {
                'description': '自动化工具和脚本',
                'required_knowledge': ['ci_cd_tools', 'infrastructure_as_code', 'configuration_management', 'automation_scripting']
            },
            'network_security_monitoring': {
                'description': '监控网络安全状态',
                'required_knowledge': ['network_security_monitoring_tools', 'security_alerting', 'security_incident_detection']
            },
            'security_threat_analysis': {
                'description': '分析安全威胁',
                'required_knowledge': ['threat_intelligence', 'security_analytics', 'threat_modeling']
            },
            'security_incident_response': {
                'description': '处理安全事件响应',
                'required_knowledge': ['incident_response_protocols', 'forensic_analysis', 'security_containment']
            },
            'security_policies': {
                'description': '安全策略和合规',
                'required_knowledge': ['security_policies_framework', 'compliance_requirements', 'security_auditing']
            },
            'network_operations_monitoring': {
                'description': '监控网络运维状态',
                'required_knowledge': ['network_operations_tools', 'network_alerting', 'network_performance_monitoring']
            },
            'network_troubleshooting': {
                'description': '网络故障排查',
                'required_knowledge': ['network_diagnostic_tools', 'troubleshooting_methodologies', 'network_protocols']
            },
            'network_performance_optimization': {
                'description': '优化网络性能',
                'required_knowledge': ['network_optimization_techniques', 'traffic_engineering', 'quality_of_service']
            },
            'network_documentation': {
                'description': '网络文档管理',
                'required_knowledge': ['network_documentation_standards', 'diagramming_tools', 'configuration_management']
            },
            'network_architecture_design': {
                'description': '设计网络架构',
                'required_knowledge': ['network_design_principles', 'scalability', 'redundancy', 'disaster_recovery']
            },
            'network_scalability_planning': {
                'description': '规划网络可扩展性',
                'required_knowledge': ['scalability_strategies', 'capacity_planning', 'load_balancing']
            },
            'network_security_architecture': {
                'description': '设计网络安全架构',
                'required_knowledge': ['security_architecture_principles', 'defense_in_depth', 'zero_trust']
            },
            'network_technology_evaluation': {
                'description': '评估网络技术',
                'required_knowledge': ['technology_assessment_criteria', 'vendor_evaluation', 'cost_benefit_analysis']
            },
            'ui_visual_design': {
                'description': '用户界面视觉设计',
                'required_knowledge': ['color_theory', 'typography', 'visual_hierarchy', 'composition']
            },
            'ui_component_design': {
                'description': 'UI组件设计',
                'required_knowledge': ['component_library', 'design_system', 'interaction_design', 'accessibility']
            },
            'ui_responsive_design': {
                'description': '响应式UI设计',
                'required_knowledge': ['responsive_design_principles', 'media_queries', 'fluid_layouts', 'device_breakpoints']
            },
            'ui_style_guide': {
                'description': 'UI风格指南',
                'required_knowledge': ['style_guide_creation', 'brand_guidelines', 'consistency', 'design_tokens']
            },
            'ux_user_research': {
                'description': '用户研究',
                'required_knowledge': ['user_research_methods', 'interview_techniques', 'survey_design', 'persona_development']
            },
            'ux_journey_mapping': {
                'description': '用户旅程映射',
                'required_knowledge': ['journey_mapping_methods', 'touchpoint_analysis', 'emotional_design', 'pain_point_identification']
            },
            'ux_prototyping': {
                'description': 'UX原型设计',
                'required_knowledge': ['prototyping_tools', 'wireframing', 'interactive_prototypes', 'user_flow']
            },
            'ux_usability_testing': {
                'description': '可用性测试',
                'required_knowledge': ['usability_testing_methods', 'test_plan_design', 'metrics_collection', 'insights_synthesis']
            },
            'graphic_layout_design': {
                'description': '平面布局设计',
                'required_knowledge': ['grid_systems', 'space_management', 'visual_balance', 'composition_rules']
            },
            'graphic_color_theory': {
                'description': '色彩理论应用',
                'required_knowledge': ['color_palettes', 'color_harmony', 'color_psychology', 'color_accessibility']
            },
            'graphic_typography': {
                'description': '排版设计',
                'required_knowledge': ['font_hierarchy', 'typeface_selection', 'typographic_rules', 'readability']
            },
            'graphic_branding': {
                'description': '品牌设计',
                'required_knowledge': ['brand_strategy', 'logo_design', 'brand_identity', 'brand_guidelines']
            },
            'product_requirements_analysis': {
                'description': '产品需求分析',
                'required_knowledge': ['requirements_gathering', 'stakeholder_management', 'scope_definition', 'prioritization']
            },
            'product_user_story': {
                'description': '用户故事开发',
                'required_knowledge': ['user_story_format', 'acceptance_criteria', 'story_mapping', 'epic_decomposition']
            },
            'product_feature_design': {
                'description': '产品功能设计',
                'required_knowledge': ['feature_specification', 'user_experience_design', 'technical_feasibility', 'competitive_analysis']
            },
            'product_iteration': {
                'description': '产品迭代管理',
                'required_knowledge': ['agile_methodologies', 'sprint_planning', 'feedback_integration', 'release_management']
            },
            'behavior_data_analysis': {
                'description': '用户行为数据分析',
                'required_knowledge': ['data_analysis_techniques', 'statistical_methods', 'data_visualization', 'sql']
            },
            'behavior_pattern_recognition': {
                'description': '行为模式识别',
                'required_knowledge': ['pattern_recognition_algorithms', 'machine_learning', 'sequence_analysis', 'anomaly_detection']
            },
            'behavior_metrics_tracking': {
                'description': '行为指标跟踪',
                'required_knowledge': ['event_tracking', 'funnel_analysis', 'retention_analysis', 'cohort_analysis']
            },
            'behavior_reporting': {
                'description': '行为报告生成',
                'required_knowledge': ['reporting_tools', 'dashboard_design', 'data_storytelling', 'insights_presentation']
            },
            'user_profiling': {
                'description': '用户画像构建',
                'required_knowledge': ['user_data_collection', 'profile_creation', 'demographic_analysis', 'psychographic_analysis']
            },
            'user_segmentation_advanced': {
                'description': '高级用户细分',
                'required_knowledge': ['segmentation_algorithms', 'clustering_techniques', 'predictive_segmentation', 'segment_validation']
            },
            'user_persona_creation': {
                'description': '用户角色创建',
                'required_knowledge': ['persona_development', 'user_research', 'needs_analysis', 'behavioral_patterns']
            },
            'user_demographic_analysis': {
                'description': '人口统计分析',
                'required_knowledge': ['demographic_data_sources', 'population_analysis', 'trend_identification', 'segmentation_based_on_demographics']
            },
            'recommendation_system_design': {
                'description': '推荐系统设计',
                'required_knowledge': ['recommendation_algorithms', 'system_architecture', 'data_requirements', 'scalability']
            },
            'recommendation_algorithm_optimization': {
                'description': '推荐算法优化',
                'required_knowledge': ['algorithm_tuning', 'performance_evaluation', 'A/B_testing', 'feedback_loops']
            },
            'recommendation_evaluation': {
                'description': '推荐系统评估',
                'required_knowledge': ['evaluation_metrics', 'offline_evaluation', 'online_evaluation', 'bias_detection']
            },
            'recommendation_personalization': {
                'description': '个性化推荐',
                'required_knowledge': ['user_preference_modeling', 'context_awareness', 'real_time_personalization', 'long_term_vs_short_term_preferences']
            },
            'behavior_prediction_modeling': {
                'description': '行为预测建模',
                'required_knowledge': ['predictive_modeling', 'machine_learning_algorithms', 'feature_engineering', 'model_evaluation']
            },
            'behavior_forecasting': {
                'description': '行为预测',
                'required_knowledge': ['time_series_analysis', 'forecasting_methods', 'trend_analysis', 'seasonality_detection']
            },
            'anomaly_detection': {
                'description': '异常行为检测',
                'required_knowledge': ['anomaly_detection_algorithms', 'threshold_setting', 'false_positive_reduction', 'alerting']
            },
            'trend_analysis': {
                'description': '趋势分析',
                'required_knowledge': ['trend_identification', 'data_visualization', 'statistical_significance', 'long_term_analysis']
            }
        }

        self.lock = threading.Lock()
        logger.info("AI能力细化器初始化完成")

    def get_capability(self, capability_id: str) -> Optional[Dict[str, Any]]:
        """获取能力信息"""
        return self.capabilities.get(capability_id)

    def get_all_capabilities(self) -> Dict[str, Dict[str, Any]]:
        """获取所有能力"""
        return self.capabilities

    def get_skill_info(self, skill_id: str) -> Optional[Dict[str, Any]]:
        """获取技能信息"""
        return self.skill_mapping.get(skill_id)

    def refine_capability(self, capability_id: str, context: Dict[str, Any] = None) -> Dict[str, Any]:
        """细化能力"""
        capability = self.capabilities.get(capability_id)
        if not capability:
            return None

        refined = {
            'capability_id': capability_id,
            'name': capability['name'],
            'description': capability['description'],
            'skills': [],
            'refined_at': datetime.now().isoformat()
        }

        for skill_id in capability['skills']:
            skill_info = self.skill_mapping.get(skill_id)
            if skill_info:
                refined['skills'].append({
                    'skill_id': skill_id,
                    'description': skill_info['description'],
                    'required_knowledge': skill_info['required_knowledge']
                })

        return refined


ai_capability_refiner = AICapabilityRefiner()
