#!/usr/bin/env python3
import os
import ast

failed_files = [
    'ai_engine.py', 'ai_decision_engine.py', 'all_ai_employees_loader.py',
    'resource_recommendation_engine.py', 'ai_service.py', 'ai_supervision_upgrade.py',
    'mechanism_ai.py', 'intelligent_warning_engine.py', 'ai_question_maintenance.py',
    'arduino_ai_employees.py', 'system_auto_processor.py', 'intelligence_manager.py',
    'ai_log_analyzer.py', 'frontend_backend_sync_ai.py', 'home_school_communication_engine.py',
    'feature_library_manager.py', 'smart_proctoring_engine.py', 'ai_system_upgrader.py',
    'ai_self_learning_empowered.py', 'learning_analytics_engine.py', 'ai_system_monitor.py',
    'gamification_engine.py', 'ai_management.py', 'ai_monitor_server.py',
    'learning_visualization_engine.py', 'ai_brain_search_enhancer.py', 'ai_engine_v3.py',
    'multi_code_repair_ai.py', 'ai_agent_auto_config.py', 'question_bank_maintainer.py',
    'ai_anomaly_detector.py', 'ai_performance_monitor.py', 'layout_adjustment_ai.py',
    'ai_training_monitor.py', 'config_manager_employee.py', 'code_analyzer.py',
    'auto_ai_enhancement.py', 'frontend_fixer_ai.py', 'ai_rule_enhancer.py',
    'standalone_ai_brain_map.py', 'ai_auto_fix_service.py', 'math_solver_engine.py',
    'rule_base_maintenance_employee.py', 'ai_brain_library.py', 'listening_question_employee.py',
    'smart_schedule_engine.py', 'math_questions_perfect_ai.py', 'knowledge_base_engine.py',
    'auto_sync_upgrade_service.py', 'ai_tutor_engine.py', 'exam_generator.py'
]

for filename in failed_files[:5]:
    filepath = os.path.join('/Users/wuchenghao/Library/CloudStorage/OneDrive-个人/文档/MTSCOS_AI_Project/ai_engines', filename)
    if not os.path.exists(filepath):
        filepath = os.path.join('/Users/wuchenghao/Library/CloudStorage/OneDrive-个人/文档/MTSCOS_AI_Project', filename)
    
    if not os.path.exists(filepath):
        continue
    
    print('\n' + '=' * 80)
    print('文件: ' + filename)
    
    with open(filepath, 'r', encoding='utf-8') as f:
        lines = f.readlines()
    
    for i, line in enumerate(lines[:60], 1):
        stripped = line.strip()
        if '=' in stripped and '"' in stripped and len(stripped) > 50:
            print(f'{i}: {stripped[:100]}')
    
    try:
        ast.parse(''.join(lines))
    except SyntaxError as e:
        print(f'\n语法错误: {e}')
        print(f'错误行号: {e.lineno}')
        if e.lineno <= len(lines):
            print(f'错误行内容: {lines[e.lineno - 1].strip()[:150]}')
