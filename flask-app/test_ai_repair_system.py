#!/usr/bin/env python3
"""
测试AI修复系统功能
"""

from ai_employee_system import RepairAIEmployee

# 创建修复AI实例
repair_ai = RepairAIEmployee('repair_001', '修复AI')

print('=== 测试修复AI功能 ===')

# 测试问题检测
print('1. 测试问题检测:')
detect_result = repair_ai.detect_issues({})
print('   结果:', detect_result['message'])
for issue in detect_result['issues']:
    print(f'   - {issue["title"]} ({issue["severity"]}): {issue["description"]}')

# 测试问题分析
print('\n2. 测试问题分析:')
analyze_result = repair_ai.analyze_issue({'issue_type': 'database_connection'})
print('   结果:', analyze_result['message'])
if 'recommended_solution' in analyze_result:
    print('   推荐解决方案:', analyze_result['recommended_solution']['title'])

print('\n=== 测试完成 ===')
