#!/usr/bin/env python3
import sys
import os
import time
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

employees = [
    ('ai_employee_system', 'ValidationAIEmployee', ['val_001', '验证AI', 'validation', 5]),
    ('ai_employee_system', 'RoutingAIEmployee', ['route_001', '路由AI', 'routing', 6]),
    ('ai_employee_system', 'TestSystemAIEmployee', ['test_sys_001', '测试系统AI', 'test_system', 7]),
    ('diagnostics_repair_employee', 'DiagnosticsRepairEmployee', ['diag_001', '诊断修复AI', 9]),
    ('question_bank_maintenance_employee', 'QuestionBankMaintenanceEmployee', ['qbm_001', '题库维护AI', 7]),
    ('rule_base_maintenance_employee', 'RuleBaseMaintenanceEmployee', ['rbm_001', '规则库维护AI', 8]),
    ('config_manager_employee', 'ConfigManagerEmployee', ['config_001', '配置管理AI', 6]),
]

for module_name, class_name, args in employees:
    print(f"Loading {class_name}... ", end='', flush=True)
    start = time.time()
    try:
        module = __import__(f'ai_engines.{module_name}', fromlist=[class_name])
        cls = getattr(module, class_name)
        emp = cls(*args)
        elapsed = time.time() - start
        print(f"OK ({elapsed:.2f}s)")
    except Exception as e:
        elapsed = time.time() - start
        print(f"FAILED ({elapsed:.2f}s): {e}")