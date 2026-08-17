#!/usr/bin/env python3
import sqlite3
import os
import shutil
import re

SOURCE_DB = '/tmp/app_local.db'
DEST_DIR = '/Users/wuchenghao/Library/CloudStorage/OneDrive-个人/文档/MTSCOS_AI_Project/flask-app/split_databases'

MODULE_MAPPING = {
    'auth': [
        'users', 'roles', 'permissions', 'role_permissions', 'auth_session_logs', 
        'auth_permission_logs', 'login_attempts', 'remember_me_tokens', 
        'user_roles', 'user_signin', 'user_locks', 'exception_login_logs',
        'user_login_logs', 'user_status', 'user_profile_info', 'user_profiles'
    ],
    'exam': [
        'exams', 'exam_account_locks', 'exam_activity_logs', 'exam_adaptation_rules',
        'exam_ai_analysis', 'exam_ai_conversations', 'exam_ai_sessions',
        'exam_ai_suggestions', 'exam_analysis', 'exam_analysis_cache', 'exam_analytics',
        'exam_answers', 'exam_appointments', 'exam_attempts', 'exam_behavior_logs',
        'exam_configs', 'exam_countdowns', 'exam_favorites', 'exam_generation_strategy',
        'exam_notes', 'exam_papers', 'exam_questions', 'exam_records', 'exam_results',
        'exam_rules', 'exam_score_comparisons', 'exam_session_timeout', 'exam_sessions',
        'exam_system_rules', 'exam_tags', 'exam_templates', 'gaokao_import_tasks',
        'gaokao_provinces', 'gaokao_questions', 'gaokao_sources', 'gaokao_subjects',
        'gaokao_years', 'japanese_exam_types', 'japanese_exams', 'japanese_import_tasks',
        'japanese_questions', 'japanese_years', 'junior_college_exam_types',
        'junior_college_import_tasks', 'junior_college_questions', 'junior_college_years',
        'nce_import_tasks', 'nce_levels', 'nce_questions', 'nce_years',
        'neworiental_course_types', 'neworiental_import_tasks', 'neworiental_questions',
        'neworiental_years', 'singapore_exams', 'singapore_questions',
        'zhongkao_import_tasks', 'zhongkao_provinces', 'zhongkao_questions',
        'zhongkao_subjects', 'zhongkao_years', 'independent_admission_questions',
        'independent_admission_tasks', 'independent_admission_types', 'independent_admission_years'
    ],
    'question': [
        'questions', 'question_analysis', 'question_bank_ai_stats', 'question_bank_maintenance',
        'question_bank_rules', 'question_bank_schedule_history', 'question_bank_schedule_plans',
        'question_banks', 'question_categories', 'question_content_hashes', 'question_fingerprints',
        'question_generation_logs', 'question_generation_stats', 'question_generation_strategies',
        'question_grading', 'question_knowledge_map', 'question_maintenance_logs',
        'question_maintenance_plans', 'question_maintenance_tasks', 'question_marks',
        'question_matrix_mapping', 'question_quality', 'question_quality_metrics',
        'question_statistics', 'question_tag_mapping', 'question_tags', 'question_templates',
        'knowledge_ability_mapping', 'knowledge_base_questions', 'knowledge_categories',
        'knowledge_consolidation_log', 'knowledge_entries', 'knowledge_explanations',
        'knowledge_index', 'knowledge_learning_log', 'knowledge_mastery', 'knowledge_nodes',
        'knowledge_point_statistics', 'knowledge_points', 'knowledge_relations',
        'knowledge_search_log', 'knowledge_shares', 'knowledge_user_paths', 'knowledge_version_history',
        'ai_generated_questions', 'ai_question_bank', 'ai_maintenance_questions',
        'problem_solutions', 'solutions', 'solution_methods', 'confusion_templates',
        'english_confusion_templates', 'japanese_confusion_templates', 'language_confusion_records',
        'duplicate_questions', 'bad_option_patterns', 'mcq_cleaning_records', 'wrong_questions',
        'wrong_analysis', 'wrong_question_reviews', 'wrong_review_plans', 'wrong_review_records'
    ],
    'learning': [
        'learning_events', 'learning_goals', 'learning_groups', 'learning_path_nodes',
        'learning_paths', 'learning_profiles', 'learning_progress', 'learning_recommendations',
        'learning_records', 'learning_reports', 'learning_resources', 'learning_statistics',
        'learning_style_profiles', 'learning_sync_records', 'learning_trends',
        'student_ability_profile', 'student_classification', 'student_exam_scores',
        'student_feedback', 'student_homework_submissions', 'student_mistakes',
        'student_type_rules', 'class_diagnosis', 'class_exam_records', 'class_students',
        'classroom_activities', 'classroom_groups', 'classroom_points', 'classroom_votes',
        'homework_submissions', 'homeworks', 'practice_plans', 'practice_question_bank',
        'daily_practice_records', 'user_learning_records', 'user_knowledge_mastery',
        'child_learning_stats', 'dropout_risk_assessments', 'intervention_plans',
        'diagnosis_reports', 'diagnosis_tests', 'grading_reports', 'grading_rules',
        'intelligent_evaluations', 'evaluation_dimension_details', 'evaluation_growth_trajectory',
        'evaluation_snapshots', 'subject_knowledge_points', 'subject_proficiency',
        'study_group_members', 'study_groups', 'study_schedules', 'study_time_recommendations'
    ],
    'system': [
        'system_config', 'system_documentation', 'system_events', 'system_health',
        'system_health_reports', 'system_logs', 'system_notices', 'system_operation_logs',
        'system_performance_log', 'system_problems', 'system_rules', 'system_rules_backup',
        'system_settings', 'system_status_log', 'system_system_notifications', 'system_test_logs',
        'system_version', 'system_version_history', 'current_system_info', 'db_version_history',
        'db_change_log', 'upgrade_tasks', 'maintenance_check_details', 'maintenance_check_reports',
        'maintenance_logs', 'maintenance_plans', 'backup_config', 'backup_history',
        'backup_records', 'backup_schedule', 'deployment_servers', 'deployment_tasks',
        'error_logs', 'error_types', 'error_diagnostics', 'error_feedbacks', 'error_fixes',
        'operation_logs', 'event_links', 'change_logs', 'security_audit_logs',
        'security_audit_reports', 'security_scan_results', 'vulnerability_scans',
        'monitor_alerts', 'monitor_error_plans', 'monitor_metrics', 'health_check_history',
        'health_check_results', 'distributed_locks', 'service_restarts', 'runtime_analysis',
        'capacity_metrics', 'capacity_planning_reports', 'matrix_data', 'matrix_types',
        'matrix_analysis_report', 'network_fix_cases', 'bug_records', 'release_history',
        'release_steps', 'resource_interactions', 'resource_reviews', 'share_votes',
        'group_activities', 'group_members', 'group_progress', 'collaborative_projects',
        'project_participants', 'collaborative_projects', 'batch_tasks', 'batch_task_items',
        'auto_rules', 'rule_constraints', 'rule_execution_logs', 'rule_groups',
        'rule_group_members', 'rule_templates', 'rule_trigger_history', 'rule_application_logs',
        'rule_maintenance_records', 'rule_maintenance_schedules', 'rule_optimization_sessions',
        'rule_optimizations', 'rule_expansion_sources', 'rule_generation_history',
        'candidate_rules', 'constraint_parameters', 'constraint_application_logs'
    ],
    'ai': [
        'ai_agents', 'ai_chat_conversations', 'ai_chat_messages', 'ai_chat_personalities',
        'ai_chat_settings', 'ai_cluster_config', 'ai_cluster_employee', 'ai_config_history',
        'ai_config_snapshot', 'ai_database_version', 'ai_employee_config',
        'ai_employee_fix_reports', 'ai_employee_module', 'ai_employee_stats',
        'ai_employee_task_history', 'ai_employee_tasks', 'ai_employees', 'ai_error_types',
        'ai_feedback', 'ai_learning_features', 'ai_learning_records', 'ai_plans',
        'ai_recommendations', 'ai_repair_logs', 'ai_rule_suggestions', 'ai_specialized_skills',
        'ai_task_assignments', 'ai_task_scheduler', 'agent_processes', 'agent_schedules',
        'agent_tasks', 'core_agent_tasks', 'prediction_alerts', 'prediction_models',
        'score_predictions', 'recommendations', 'recommendation_config',
        'knowledge_consolidation_log', 'knowledge_learning_log', 'knowledge_search_log',
        'learning_recommendations', 'adaptive_learning_paths'
    ],
    'physics': [
        'physics_categories', 'physics_constants', 'physics_forces', 'physics_formulas',
        'physics_objects', 'physics_simulation_steps', 'physics_simulations',
        'particle_interactions', 'particle_simulation_results', 'particle_systems',
        'particle_types', 'particles', 'force_fields'
    ],
    'math': [
        'math_concepts', 'math_formulas', 'math_functions', 'math_knowledge_graph',
        'math_model_categories', 'math_models', 'math_problems', 'formula_categories',
        'formula_tag_mapping', 'formula_tags', 'irt_parameters', 'ability_dimensions'
    ],
    'admin': [
        'admin_notifications', 'dashboard_widgets', 'dashboards', 'page_configurations',
        'page_navigation_logs', 'ui_components', 'access_control_rules', 'access_logs',
        'permission_bugs', 'permission_fixes', 'permission_test_results',
        'permission_test_sessions', 'navigation_anomalies', 'mtscos_extension_history',
        'mtscos_extension_status', 'mtscos_function_extensions', 'mtscos_modules',
        'super_admin_dashboard_fix_reports', 'frontend_fix_reports',
        'frontend_optimization_records', 'security_scan_results', 'sensitive_settings',
        'encryption_keys', 'data_masking_rules'
    ],
    'proctor': [
        'proctor_alerts', 'proctor_config', 'proctor_integrity_history', 'proctor_sessions',
        'proctor_teachers', 'proctor_violations', 'cheating_detection_results',
        'exam_behavior_logs', 'screen_switch_logs', 'time_anomaly_logs', 'pause_requests'
    ],
    'user': [
        'user_achievements', 'user_activity_hours', 'user_activity_logs',
        'user_audio_preferences', 'user_badges', 'user_behaviors', 'user_custom_practices',
        'user_exam_progress', 'user_listening_preferences', 'user_messages',
        'user_notification_preferences', 'user_notifications', 'user_points',
        'user_preferences', 'point_transactions', 'redeem_history', 'reward_config',
        'home_school_messages', 'home_school_relations', 'parent_alerts',
        'parent_child_relations', 'parent_meeting_registrations', 'parent_meetings',
        'parent_monitor_settings', 'parent_notifications', 'parent_permissions',
        'parent_student_bindings', 'teacher_classes', 'teacher_evaluations',
        'teacher_homeworks', 'teaching_evaluations', 'teaching_improvement_plans',
        'tutor_feedback', 'tutor_messages', 'tutor_sessions', 'leaderboards',
        'game_items', 'game_players', 'game_quests', 'player_inventory',
        'player_quest_progress', 'tournament_participants', 'tournament_records',
        'tournaments', 'audio_composition_rules', 'audio_matching_errors',
        'audio_matching_tests', 'audio_metadata', 'audio_synthesis_records',
        'audio_test_results', 'listening_audio_metadata', 'listening_questions',
        'listening_training_records', 'listening_training_stats', 'english_pronunciation',
        'japanese_pronunciation', 'visualizations', 'visualization_exports',
        'monitor_alerts', 'notification_channels', 'notification_logs',
        'notification_read', 'notification_routing_log', 'notification_settings',
        'notification_subscriptions', 'notifications', 'smart_notifications'
    ],
    'log': [
        'system_logs', 'system_operation_logs', 'error_logs', 'access_logs',
        'auth_session_logs', 'auth_permission_logs', 'session_logs', 'session_activities',
        'user_activity_logs', 'operation_logs', 'event_links', 'change_logs',
        'api_request_logs', 'api_response_logs', 'performance_logs', 'exception_logs',
        'security_audit_logs', 'backup_history', 'maintenance_logs', 'upgrade_tasks',
        'release_history', 'deployment_tasks', 'agent_task_history', 'ai_employee_task_history',
        'generation_logs', 'question_generation_logs', 'code_fix_logs', 'repair_records',
        'repair_reports', 'ai_repair_logs', 'fix_tasks', 'grade_bank_mapping',
        'knowledge_learning_log', 'knowledge_search_log', 'knowledge_consolidation_log',
        'learning_sync_records', 'search_metadata', 'search_cache', 'faq_cache',
        'route_config_cache', 'exam_analysis_cache', 'sync_metadata', 'index_metadata'
    ]
}

def get_module_for_table(table_name):
    for module, tables in MODULE_MAPPING.items():
        if table_name in tables:
            return module
    
    for module, tables in MODULE_MAPPING.items():
        if table_name.startswith(module + '_'):
            return module
    
    patterns = {
        'exam': r'^exam_|^test_|^gaokao_|^zhongkao_|^japanese_|^junior_college_|^nce_|^neworiental_|^singapore_',
        'question': r'^question_|^knowledge_|^ai_generated_|^ai_question_|^problem_|^solution_|^wrong_',
        'learning': r'^learning_|^student_|^class_|^homework_|^practice_|^user_learning_',
        'system': r'^system_|^settings_|^config_|^logs_|^notification_|^maintenance_|^backup_|^upgrade_',
        'ai': r'^ai_|^agent_|^intelligent_|^recommendation_|^prediction_',
        'physics': r'^physics_|^particle_|^force_',
        'math': r'^math_|^formula_|^irt_',
        'admin': r'^admin_|^dashboard_|^permission_|^access_',
        'proctor': r'^proctor_|^cheating_',
        'user': r'^user_|^teacher_|^parent_|^tutor_|^game_|^audio_|^listening_|^visualization_'
    }
    
    for module, pattern in patterns.items():
        if re.match(pattern, table_name):
            return module
    
    return 'other'

def split_database():
    os.makedirs(DEST_DIR, exist_ok=True)
    
    source_conn = sqlite3.connect(SOURCE_DB)
    source_cursor = source_conn.cursor()
    
    source_cursor.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")
    tables = [t[0] for t in source_cursor.fetchall()]
    
    module_tables = {}
    for table in tables:
        module = get_module_for_table(table)
        if module not in module_tables:
            module_tables[module] = []
        module_tables[module].append(table)
    
    logger.info(f"=== 数据库拆分计划 ===")
    logger.info(f"源数据库: {SOURCE_DB}")
    logger.info(f"源数据库大小: {os.path.getsize(SOURCE_DB) / (1024 * 1024):.2f} MB")
    logger.info(f"总表数: {len(tables)}")
    logger.info(f"目标目录: {DEST_DIR}")
    logger.info()
    
    for module, mod_tables in sorted(module_tables.items()):
        logger.info(f"  {module}: {len(mod_tables)} 个表")
    
    logger.info()
    logger.info(f"=== 开始拆分 ===")
    
    for module, mod_tables in sorted(module_tables.items()):
        if module == 'other' and len(mod_tables) == 0:
            continue
        
        dest_db = os.path.join(DEST_DIR, f'{module}.db')
        
        if os.path.exists(dest_db):
            os.remove(dest_db)
        
        dest_conn = sqlite3.connect(dest_db)
        dest_cursor = dest_conn.cursor()
        
        source_cursor.execute("ATTACH DATABASE ? AS dest", (dest_db,))
        
        for table in mod_tables:
            try:
                source_cursor.execute(f"CREATE TABLE dest.{table} AS SELECT * FROM {table}")
                
                source_cursor.execute(f"SELECT sql FROM sqlite_master WHERE type='index' AND tbl_name='{table}'")
                indexes = source_cursor.fetchall()
                for idx in indexes:
                    try:
                        dest_cursor.execute(idx[0])
                    except:
                        pass
                
                source_cursor.execute(f"SELECT sql FROM sqlite_master WHERE type='trigger' AND tbl_name='{table}'")
                triggers = source_cursor.fetchall()
                for trig in triggers:
                    try:
                        dest_cursor.execute(trig[0])
                    except:
                        pass
                
                logger.info(f"  [{module}] 迁移表: {table}")
                
            except Exception as e:
                logger.info(f"  [{module}] 迁移失败: {table} - {e}")
        
        source_cursor.execute("DETACH DATABASE dest")
        dest_conn.commit()
        dest_conn.close()
        
        db_size = os.path.getsize(dest_db) / (1024 * 1024)
        logger.info(f"  [{module}] 完成! 大小: {db_size:.2f} MB")
        logger.info()
    
    source_conn.close()
    
    logger.info(f"=== 拆分完成 ===")
    logger.info(f"生成的数据库文件:")
    for f in sorted(os.listdir(DEST_DIR)):
        if f.endswith('.db'):
            fpath = os.path.join(DEST_DIR, f)
            size = os.path.getsize(fpath) / (1024 * 1024)
            logger.info(f"  {f}: {size:.2f} MB")

if __name__ == '__main__':
    split_database()