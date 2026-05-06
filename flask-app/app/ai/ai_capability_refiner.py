#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
AI能力细化模块
自动向下细化AI功能及专业能力，为不同领域的AI分配专业任务

import os
# JSON import removed - using database
import logging
import threading
from datetime import datetime
from typing import Dict, List, Any, Optional

# 配置日志
logger = logging.getLogger('ai_capability_refiner')

class AICapabilityRefiner:
    """AI能力细化类"""

    def __init__(self):
        """初始化AI能力细化器"""
        self.capabilities = {
            'general': {
                'name': '通用AI',
                'description': '具备基本的AI能力，可处理多种任务',
                'skills': ['natural_language_processing', 'basic_reasoning', 'general_knowledge']
            },
            'engineering': {
                'name': '工程AI',
                'description': '专注于软件工程和系统维护',
                'skills': ['code_analysis', 'performance_monitoring', 'security_scanning', 'network_knowledge']
            },
                'name': '前端工程AI',
                'description': '专注于前端开发和用户界面',
                'skills': ['frontend_code_analysis', 'frontend_performance_monitoring', 'frontend_security_scanning', 'frontend_frameworks']
            },
                'name': '后端工程AI',
                'description': '专注于后端开发和服务器架构',
                'skills': ['backend_code_analysis', 'backend_performance_monitoring', 'backend_security_scanning', 'database_management']
            },
                'name': '移动应用工程AI',
                'description': '专注于移动应用开发',
                'skills': ['mobile_code_analysis', 'mobile_performance_monitoring', 'mobile_security_scanning', 'mobile_frameworks']
            },
                'name': 'DevOps工程AI',
                'description': '专注于开发运维和自动化',
                'skills': ['devops_code_analysis', 'devops_performance_monitoring', 'devops_security_scanning', 'automation_tools']
            },
                'name': '教育AI',
                'description': '专注于教育和学习领域',
                'skills': ['question_generation', 'student_assessment', 'learning_analysis', 'content_curation']
            },
                'name': '数学教师AI',
                'description': '专注于数学教育领域',
                'skills': ['math_question_generation', 'math_student_assessment', 'math_learning_analysis', 'math_content_curation']
            },
                'name': '语言教师AI',
                'description': '专注于语言教育领域',
                'skills': ['language_question_generation', 'language_student_assessment', 'language_learning_analysis', 'language_content_curation']
            },
                'name': '科学教师AI',
                'description': '专注于科学教育领域',
                'skills': ['science_question_generation', 'science_student_assessment', 'science_learning_analysis', 'science_content_curation']
            },
                'name': '历史教师AI',
                'description': '专注于历史教育领域',
                'skills': ['history_question_generation', 'history_student_assessment', 'history_learning_analysis', 'history_content_curation']
            },
                'name': '艺术教师AI',
                'description': '专注于艺术教育领域',
                'skills': ['art_question_generation', 'art_student_assessment', 'art_learning_analysis', 'art_content_curation']
            },
                'name': '网络AI',
                'description': '专注于网络管理和安全',
                'skills': ['network_monitoring', 'security_analysis', 'traffic_optimization', 'threat_detection']
            },
                'name': '网络安全AI',
                'description': '专注于网络安全和防护',
                'skills': ['network_security_monitoring', 'security_threat_analysis', 'security_incident_response', 'security_policies']
            },
                'name': '网络运维AI',
                'description': '专注于网络运维和管理',
                'skills': ['network_operations_monitoring', 'network_troubleshooting', 'network_performance_optimization', 'network_documentation']
            },
                'name': '网络架构AI',
                'description': '专注于网络架构设计和规划',
                'skills': ['network_architecture_design', 'network_scalability_planning', 'network_security_architecture', 'network_technology_evaluation']
            },
                'name': '考试AI',
                'description': '专注于考试和评估',
                'skills': ['exam_generation', 'answer_analysis', 'performance_evaluation', 'adaptive_testing']
            },
                'name': '设计AI',
                'description': '专注于UI/UX设计',
                'skills': ['ui_design', 'ux_analysis', 'visualization', 'design_recommendation']
            },
                'name': 'UI设计AI',
                'description': '专注于用户界面设计',
                'skills': ['ui_visual_design', 'ui_component_design', 'ui_responsive_design', 'ui_style_guide']
            },
                'name': 'UX设计AI',
                'description': '专注于用户体验设计',
                'skills': ['ux_user_research', 'ux_journey_mapping', 'ux_prototyping', 'ux_usability_testing']
            },
                'name': '平面设计AI',
                'description': '专注于平面设计和视觉传达',
                'skills': ['graphic_layout_design', 'graphic_color_theory', 'graphic_typography', 'graphic_branding']
            },
                'name': '产品设计AI',
                'description': '专注于产品设计和创新',
                'skills': ['product_requirements_analysis', 'product_user_story', 'product_feature_design', 'product_iteration']
            },
                'name': '用户行为AI',
                'description': '专注于用户行为分析',
                'skills': ['behavior_analysis', 'preference_learning', 'recommendation', 'user_segmentation']
            },
                'name': '用户行为分析AI',
                'description': '专注于用户行为数据分析',
                'skills': ['behavior_data_analysis', 'behavior_pattern_recognition', 'behavior_metrics_tracking', 'behavior_reporting']
            },
                'name': '用户画像AI',
                'description': '专注于用户画像和细分',
                'skills': ['user_profiling', 'user_segmentation_advanced', 'user_persona_creation', 'user_demographic_analysis']
            },
                'name': '推荐系统AI',
                'description': '专注于推荐系统和个性化',
                'skills': ['recommendation_system_design', 'recommendation_algorithm_optimization', 'recommendation_evaluation', 'recommendation_personalization']
            },
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
                'description': '监控系统性能',
                'required_knowledge': ['system_metrics', 'performance_benchmarks', 'optimization_techniques']
            },
                'description': '扫描系统安全漏洞',
                'required_knowledge': ['security_vulnerabilities', 'penetration_testing', 'secure_coding']
            },
                'description': '网络知识和管理',
                'required_knowledge': ['network_protocols', 'network_topology', 'network_security']
            },
                'description': '生成教育题目',
                'required_knowledge': ['curriculum_standards', 'question_types', 'difficulty_levels']
            },
                'description': '评估学生表现',
                'required_knowledge': ['assessment_methods', 'learning_objectives', 'grading_scales']
            },
                'description': '分析学习数据',
                'required_knowledge': ['learning_analytics', 'data_mining', 'educational_statistics']
            },
                'description': '内容管理和推荐',
            },
                'description': '生成数学题目',
                'required_knowledge': ['mathematics_curriculum', 'math_question_types', 'math_difficulty_levels']
            },
                'description': '评估学生数学表现',
                'required_knowledge': ['math_assessment_methods', 'math_learning_objectives', 'math_grading_scales']
            },
                'description': '分析数学学习数据',
                'required_knowledge': ['math_learning_analytics', 'math_data_mining', 'math_educational_statistics']
            },
                'description': '数学内容管理和推荐',
                'required_knowledge': ['math_content_standards', 'math_recommendation_algorithms', 'math_content_organization']
            },
                'description': '生成语言题目',
                'required_knowledge': ['language_curriculum', 'language_question_types', 'language_difficulty_levels']
            },
                'description': '评估学生语言表现',
                'required_knowledge': ['language_assessment_methods', 'language_learning_objectives', 'language_grading_scales']
            },
                'description': '分析语言学习数据',
                'required_knowledge': ['language_learning_analytics', 'language_data_mining', 'language_educational_statistics']
            },
                'description': '语言内容管理和推荐',
                'required_knowledge': ['language_content_standards', 'language_recommendation_algorithms', 'language_content_organization']
            },
                'description': '生成科学题目',
                'required_knowledge': ['science_curriculum', 'science_question_types', 'science_difficulty_levels']
            },
                'description': '评估学生科学表现',
                'required_knowledge': ['science_assessment_methods', 'science_learning_objectives', 'science_grading_scales']
            },
                'description': '分析科学学习数据',
                'required_knowledge': ['science_learning_analytics', 'science_data_mining', 'science_educational_statistics']
            },
                'description': '科学内容管理和推荐',
                'required_knowledge': ['science_content_standards', 'science_recommendation_algorithms', 'science_content_organization']
            },
                'description': '生成历史题目',
                'required_knowledge': ['history_curriculum', 'history_question_types', 'history_difficulty_levels']
            },
                'description': '评估学生历史表现',
                'required_knowledge': ['history_assessment_methods', 'history_learning_objectives', 'history_grading_scales']
            },
                'description': '分析历史学习数据',
                'required_knowledge': ['history_learning_analytics', 'history_data_mining', 'history_educational_statistics']
            },
                'description': '历史内容管理和推荐',
                'required_knowledge': ['history_content_standards', 'history_recommendation_algorithms', 'history_content_organization']
            },
                'description': '生成艺术题目',
                'required_knowledge': ['art_curriculum', 'art_question_types', 'art_difficulty_levels']
            },
                'description': '评估学生艺术表现',
                'required_knowledge': ['art_assessment_methods', 'art_learning_objectives', 'art_grading_scales']
            },
                'description': '分析艺术学习数据',
                'required_knowledge': ['art_learning_analytics', 'art_data_mining', 'art_educational_statistics']
            },
                'description': '艺术内容管理和推荐',
                'required_knowledge': ['art_content_standards', 'art_recommendation_algorithms', 'art_content_organization']
            },
                'description': '监控网络状态',
                'required_knowledge': ['network_monitoring_tools', 'alerting_systems', 'network_performance']
            },
                'description': '分析安全威胁',
                'required_knowledge': ['threat_intelligence', 'security_analytics', 'incident_response']
            },
                'description': '优化网络流量',
                'required_knowledge': ['traffic_analysis', 'load_balancing', 'network_optimization']
            },
                'description': '检测安全威胁',
                'required_knowledge': ['threat_models', 'anomaly_detection', 'security_monitoring']
            },
                'description': '生成考试试卷',
                'required_knowledge': ['exam_standards', 'question_banking', 'test_construction']
            },
                'description': '分析答案质量',
                'required_knowledge': ['answer_grading', 'rubrics', 'feedback_generation']
            },
                'description': '评估考试表现',
                'required_knowledge': ['performance_metrics', 'statistical_analysis', 'reporting']
            },
                'description': '自适应测试',
                'required_knowledge': ['item_response_theory', 'adaptive_algorithms', 'personalization']
            },
                'description': '用户界面设计',
                'required_knowledge': ['design_principles', 'visual_hierarchy', 'user_interface_patterns']
            },
                'description': '用户体验分析',
                'required_knowledge': ['user_research', 'usability_testing', 'ux_metrics']
            },
                'description': '数据可视化',
                'required_knowledge': ['data_visualization', 'information_design', 'visual_perception']
            },
                'description': '设计推荐',
                'required_knowledge': ['design_trends', 'best_practices', 'user_preferences']
            },
                'description': '分析用户行为',
                'required_knowledge': ['behavioral_science', 'user_journeys', 'interaction_analysis']
            },
                'description': '学习用户偏好',
                'required_knowledge': ['preference_modeling', 'collaborative_filtering', 'personalization']
            },
                'description': '推荐内容',
                'required_knowledge': ['recommendation_systems', 'content_based_filtering', 'hybrid_methods']
            },
                'description': '用户细分',
                'required_knowledge': ['clustering_algorithms', 'demographic_analysis', 'behavioral_segmentation']
            },
                'description': '自然语言处理',
                'required_knowledge': ['nlp_techniques', 'language_models', 'text_analysis']
            },
                'description': '基本推理能力',
                'required_knowledge': ['logic', 'problem_solving', 'critical_thinking']
            },
                'description': '通用知识',
                'required_knowledge': ['world_knowledge', 'common_sense', 'current_events']
            },
            'frontend_code_analysis': {
                'description': '分析前端代码质量和安全性',
                'required_knowledge': ['frontend_languages', 'frontend_frameworks', 'frontend_code_patterns', 'frontend_security']
            },
                'description': '监控前端性能',
                'required_knowledge': ['frontend_metrics', 'frontend_performance_benchmarks', 'frontend_optimization']
            },
                'description': '扫描前端安全漏洞',
                'required_knowledge': ['frontend_security_vulnerabilities', 'frontend_secure_coding', 'frontend_security_tools']
            },
                'description': '前端框架和库',
                'required_knowledge': ['react', 'vue', 'angular', 'frontend_build_tools']
            },
                'description': '分析后端代码质量和安全性',
                'required_knowledge': ['backend_languages', 'backend_frameworks', 'backend_code_patterns', 'backend_security']
            },
                'description': '监控后端性能',
                'required_knowledge': ['backend_metrics', 'backend_performance_benchmarks', 'backend_optimization']
            },
                'description': '扫描后端安全漏洞',
                'required_knowledge': ['backend_security_vulnerabilities', 'backend_secure_coding', 'backend_security_tools']
            },
                'description': '数据库管理和优化',
                'required_knowledge': ['database_systems', 'sql', 'database_optimization', 'database_security']
            },
                'description': '分析移动应用代码质量和安全性',
                'required_knowledge': ['mobile_languages', 'mobile_frameworks', 'mobile_code_patterns', 'mobile_security']
            },
                'description': '监控移动应用性能',
                'required_knowledge': ['mobile_metrics', 'mobile_performance_benchmarks', 'mobile_optimization']
            },
                'description': '扫描移动应用安全漏洞',
                'required_knowledge': ['mobile_security_vulnerabilities', 'mobile_secure_coding', 'mobile_security_tools']
            },
                'description': '移动应用框架',
                'required_knowledge': ['ios_development', 'android_development', 'cross_platform_frameworks', 'mobile_ui_frameworks']
            },
                'description': '分析DevOps代码质量和安全性',
                'required_knowledge': ['devops_languages', 'devops_tools', 'devops_code_patterns', 'devops_security']
            },
                'description': '监控DevOps性能',
                'required_knowledge': ['devops_metrics', 'devops_performance_benchmarks', 'devops_optimization']
            },
                'description': '扫描DevOps安全漏洞',
                'required_knowledge': ['devops_security_vulnerabilities', 'devops_secure_coding', 'devops_security_tools']
            },
                'description': '自动化工具和脚本',
                'required_knowledge': ['ci_cd_tools', 'infrastructure_as_code', 'configuration_management', 'automation_scripting']
            },
            'network_security_monitoring': {
                'description': '监控网络安全状态',
                'required_knowledge': ['network_security_monitoring_tools', 'security_alerting', 'security_incident_detection']
            },
                'description': '分析安全威胁',
                'required_knowledge': ['threat_intelligence', 'security_analytics', 'threat_modeling']
            },
                'description': '处理安全事件响应',
                'required_knowledge': ['incident_response_protocols', 'forensic_analysis', 'security_containment']
            },
                'description': '安全策略和合规',
                'required_knowledge': ['security_policies_framework', 'compliance_requirements', 'security_auditing']
            },
                'description': '监控网络运维状态',
                'required_knowledge': ['network_operations_tools', 'network_alerting', 'network_performance_monitoring']
            },
                'description': '网络故障排查',
                'required_knowledge': ['network_diagnostic_tools', 'troubleshooting_methodologies', 'network_protocols']
            },
                'description': '优化网络性能',
                'required_knowledge': ['network_optimization_techniques', 'traffic_engineering', 'quality_of_service']
            },
                'description': '网络文档管理',
                'required_knowledge': ['network_documentation_standards', 'diagramming_tools', 'configuration_management']
            },
                'description': '设计网络架构',
                'required_knowledge': ['network_design_principles', 'scalability', 'redundancy', 'disaster_recovery']
            },
                'description': '规划网络可扩展性',
                'required_knowledge': ['scalability_strategies', 'capacity_planning', 'load_balancing']
            },
                'description': '设计网络安全架构',
                'required_knowledge': ['security_architecture_principles', 'defense_in_depth', 'zero_trust']
            },
                'description': '评估网络技术',
                'required_knowledge': ['technology_assessment_criteria', 'vendor_evaluation', 'cost_benefit_analysis']
            },
            'ui_visual_design': {
                'description': '用户界面视觉设计',
                'required_knowledge': ['color_theory', 'typography', 'visual_hierarchy', 'composition']
            },
                'description': 'UI组件设计',
                'required_knowledge': ['component_library', 'design_system', 'interaction_design', 'accessibility']
            },
                'description': '响应式UI设计',
                'required_knowledge': ['responsive_design_principles', 'media_queries', 'fluid_layouts', 'device_breakpoints']
            },
                'description': 'UI风格指南',
                'required_knowledge': ['style_guide_creation', 'brand_guidelines', 'consistency', 'design_tokens']
            },
                'description': '用户研究',
                'required_knowledge': ['user_research_methods', 'interview_techniques', 'survey_design', 'persona_development']
            },
                'description': '用户旅程映射',
                'required_knowledge': ['journey_mapping_methods', 'touchpoint_analysis', 'emotional_design', 'pain_point_identification']
            },
                'description': 'UX原型设计',
                'required_knowledge': ['prototyping_tools', 'wireframing', 'interactive_prototypes', 'user_flow']
            },
                'description': '可用性测试',
                'required_knowledge': ['usability_testing_methods', 'test_plan_design', 'metrics_collection', 'insights_synthesis']
            },
                'description': '平面布局设计',
                'required_knowledge': ['grid_systems', 'space_management', 'visual_balance', 'composition_rules']
            },
                'description': '色彩理论应用',
                'required_knowledge': ['color_palettes', 'color_harmony', 'color_psychology', 'color_accessibility']
            },
                'description': '排版设计',
                'required_knowledge': ['font_hierarchy', 'typeface_selection', 'typographic_rules', 'readability']
            },
                'description': '品牌设计',
                'required_knowledge': ['brand_strategy', 'logo_design', 'brand_identity', 'brand_guidelines']
            },
                'description': '产品需求分析',
                'required_knowledge': ['requirements_gathering', 'stakeholder_management', 'scope_definition', 'prioritization']
            },
                'description': '用户故事开发',
                'required_knowledge': ['user_story_format', 'acceptance_criteria', 'story_mapping', 'epic_decomposition']
            },
                'description': '产品功能设计',
                'required_knowledge': ['feature_specification', 'user_experience_design', 'technical_feasibility', 'competitive_analysis']
            },
                'description': '产品迭代管理',
                'required_knowledge': ['agile_methodologies', 'sprint_planning', 'feedback_integration', 'release_management']
            },
            'behavior_data_analysis': {
                'description': '用户行为数据分析',
                'required_knowledge': ['data_analysis_techniques', 'statistical_methods', 'data_visualization', 'sql']
            },
                'description': '行为模式识别',
                'required_knowledge': ['pattern_recognition_algorithms', 'machine_learning', 'sequence_analysis', 'anomaly_detection']
            },
                'description': '行为指标跟踪',
                'required_knowledge': ['event_tracking', 'funnel_analysis', 'retention_analysis', 'cohort_analysis']
                'description': '行为报告生成',
                'required_knowledge': ['reporting_tools', 'dashboard_design', 'data_storytelling', 'insights_presentation']
            },
                'description': '用户画像构建',
                'required_knowledge': ['user_data_collection', 'profile_creation', 'demographic_analysis', 'psychographic_analysis']
            },
                'description': '高级用户细分',
                'required_knowledge': ['segmentation_algorithms', 'clustering_techniques', 'predictive_segmentation', 'segment_validation']
            },
                'description': '用户角色创建',
                'required_knowledge': ['persona_development', 'user_research', 'needs_analysis', 'behavioral_patterns']
            },
                'description': '人口统计分析',
                'required_knowledge': ['demographic_data_sources', 'population_analysis', 'trend_identification', 'segmentation_based_on_demographics']
            },
                'description': '推荐系统设计',
                'required_knowledge': ['recommendation_algorithms', 'system_architecture', 'data_requirements', 'scalability']
            },
                'description': '推荐算法优化',
                'required_knowledge': ['algorithm_tuning', 'performance_evaluation', 'A/B_testing', 'feedback_loops']
            },
                'description': '推荐系统评估',
                'required_knowledge': ['evaluation_metrics', 'offline_evaluation', 'online_evaluation', 'bias_detection']
            },
                'description': '个性化推荐',
                'required_knowledge': ['user_preference_modeling', 'context_awareness', 'real_time_personalization', 'long_term_vs_short_term_preferences']
            },
                'description': '行为预测建模',
                'required_knowledge': ['predictive_modeling', 'machine_learning_algorithms', 'feature_engineering', 'model_evaluation']
            },
                'description': '行为预测',
                'required_knowledge': ['time_series_analysis', 'forecasting_methods', 'trend_analysis', 'seasonality_detection']
            },
                'description': '异常行为检测',
                'required_knowledge': ['anomaly_detection_algorithms', 'threshold_setting', 'false_positive_reduction', 'alerting']
            },
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

    def get_skill(self, skill_id: str) -> Optional[Dict[str, Any]]:
        """获取技能信息"""
        return self.skill_mapping.get(skill_id)

    def get_all_skills(self) -> Dict[str, Dict[str, Any]]:
        """获取所有技能"""
        return self.skill_mapping

    def refine_capability(self, ai_instance: Any, target_capability: str) -> bool:
        """细化AI能力"""
        try:
            # 检查目标能力是否存在
            if target_capability not in self.capabilities:
                logger.error(f"目标能力不存在: {target_capability}")
                return False

            # 获取目标能力的技能
            target_skills = self.capabilities[target_capability]['skills']

            # 为AI实例分配技能
            with self.lock:
                # 假设AI实例有一个skills属性
                ai_instance.skills = target_skills
                ai_instance.capability = target_capability
                ai_instance.capability_name = self.capabilities[target_capability]['name']
                ai_instance.capability_description = self.capabilities[target_capability]['description']

                # 初始化refinement_history属性
                if not hasattr(ai_instance, 'refinement_history'):
                    ai_instance.refinement_history = []

                # 记录细化过程
                ai_instance.refinement_history.append({
                    'timestamp': datetime.now().isoformat(),
                    'capability': target_capability,
                    'skills': target_skills
                })

            logger.info(f"AI实例 {ai_instance.instance_id} 能力细化成功，目标能力: {target_capability}")
            return True
        except Exception as e:
            logger.error(f"细化AI能力失败: {str(e)}")
            return False

    def recommend_capability(self, task_description: str) -> List[str]:
        """根据任务描述推荐能力"""
        try:
            # 简单的关键词匹配
            task_lower = task_description.lower()
            recommendations = []

            # 匹配能力
            for capability_id, capability in self.capabilities.items():
                # 检查能力名称和描述
                if (capability['name'].lower() in task_lower or
                    capability['description'].lower() in task_lower):
                    recommendations.append(capability_id)

                # 检查技能
                for skill in capability['skills']:
                    skill_info = self.skill_mapping.get(skill)
                    if skill_info and skill_info['description'].lower() in task_lower:
                        if capability_id not in recommendations:
                            recommendations.append(capability_id)

            # 如果没有匹配，返回通用能力
            if not recommendations:
                recommendations.append('general')

            return recommendations
        except Exception as e:
            logger.error(f"推荐能力失败: {str(e)}")
            return ['general']

    def get_skill_requirements(self, skill_id: str) -> List[str]:
        """获取技能所需的知识"""
        skill = self.skill_mapping.get(skill_id)
        if skill:
            return skill.get('required_knowledge', [])
        return []

    def validate_capability(self, ai_instance: Any) -> bool:
        """验证AI实例的能力"""
        try:
            # 检查AI实例是否有能力属性
            if not hasattr(ai_instance, 'capability') or not ai_instance.capability:
                logger.warning(f"AI实例 {ai_instance.instance_id} 没有能力属性")
                return False

            # 检查能力是否存在
            if ai_instance.capability not in self.capabilities:
                logger.warning(f"AI实例 {ai_instance.instance_id} 的能力不存在: {ai_instance.capability}")
                return False

            # 检查技能是否匹配
            if hasattr(ai_instance, 'skills'):
                expected_skills = self.capabilities[ai_instance.capability]['skills']
                for skill in expected_skills:
                    if skill not in ai_instance.skills:
                        logger.warning(f"AI实例 {ai_instance.instance_id} 缺少技能: {skill}")
                        return False

            logger.info(f"AI实例 {ai_instance.instance_id} 能力验证通过")
            return True
        except Exception as e:
            logger.error(f"验证AI能力失败: {str(e)}")
            return False

    def update_capability(self, capability_id: str, updates: Dict[str, Any]) -> bool:
        """更新能力信息"""
        try:
            with self.lock:
                if capability_id in self.capabilities:
                    self.capabilities[capability_id].update(updates)
                    logger.info(f"能力 {capability_id} 更新成功")
                    return True
                else:
                    logger.error(f"能力不存在: {capability_id}")
            logger.error(f"更新能力失败: {str(e)}")
            return False

    def add_skill(self, skill_id: str, skill_info: Dict[str, Any]) -> bool:
        """添加新技能"""
        try:
            with self.lock:
                if skill_id not in self.skill_mapping:
                    self.skill_mapping[skill_id] = skill_info
                    logger.info(f"技能 {skill_id} 添加成功")
                    return True
                else:
                    logger.warning(f"技能已存在: {skill_id}")
                    return False
        except Exception as e:
            logger.error(f"添加技能失败: {str(e)}")
            return False

# 创建全局AI能力细化器实例
ai_capability_refiner = AICapabilityRefiner()

if __name__ == '__main__':
    print("AI能力细化器初始化成功")
    print(f"能力数量: {len(ai_capability_refiner.get_all_capabilities())}")
    print(f"技能数量: {len(ai_capability_refiner.get_all_skills())}")

    # 测试推荐能力
    test_task = "分析代码性能问题"
    recommendations = ai_capability_refiner.recommend_capability(test_task)
    print(f"\n任务: {test_task}")
    print(f"推荐能力: {recommendations}")

    # 测试技能要求
    test_skill = "code_analysis"
    requirements = ai_capability_refiner.get_skill_requirements(test_skill)
    print(f"\n技能: {test_skill}")
    print(f"所需知识: {requirements}")
