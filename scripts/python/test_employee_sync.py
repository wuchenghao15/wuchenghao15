#!/usr/bin/env python3
"""
测试AI员工同步功能
"""

import sys
sys.path.insert(0, '/Users/wuchenghao/Library/CloudStorage/OneDrive-个人/文档/MTSCOS_AI_Project')

from ai_engines.ai_employee_sync import AIEmployeeSync, ensure_employee_table

class MockEmployee:
    """模拟员工对象"""
    def __init__(self, employee_id, name, emp_type='general', level=1, status='active'):
        self.employee_id = employee_id
        self.name = name
        self.type = emp_type
        self.level = level
        self.status = status
        self.description = ''
        self.capabilities = []
        self.efficiency = 0
        self.workload = 0
        self.knowledge_domain = ''
        self.personality_type = ''
        self.total_tasks = 0
        self.successful_tasks = 0
        self.failed_tasks = 0
        self.performance_score = 80.0

print('=' * 60)
print('AI员工同步功能测试')
print('=' * 60)

ensure_employee_table()
print('1. 数据库表初始化完成')

sync_manager = AIEmployeeSync()

print()
print('2. 创建模拟员工数据:')
mock_employees = {
    'val_001': MockEmployee('val_001', '验证AI员工', 'validation', 5, 'active'),
    'rout_001': MockEmployee('rout_001', '路由AI员工', 'routing', 7, 'active'),
    'test_001': MockEmployee('test_001', '测试AI员工', 'test_system', 3, 'active'),
    'diag_001': MockEmployee('diag_001', '诊断修复AI员工', 'diagnostics_repair', 8, 'active'),
    'qbm_001': MockEmployee('qbm_001', '题库维护AI员工', 'question_bank_maintenance', 6, 'active'),
    'prj_rep_001': MockEmployee('prj_rep_001', '项目修复AI Agent', 'project_repair', 9, 'active'),
    'db_qry_001': MockEmployee('db_qry_001', '数据库查询AI Agent', 'db_query', 9, 'active'),
    'db_sort_001': MockEmployee('db_sort_001', '数据库排序检索AI Agent', 'db_sort_search', 9, 'active'),
}

print(f'   共创建 {len(mock_employees)} 个模拟员工')

print()
print('3. 同步员工到数据库:')
sync_result = sync_manager.sync_all_employees(mock_employees)
print(f'   总数: {sync_result["total"]}')
print(f'   新增: {sync_result["created"]}')
print(f'   更新: {sync_result["updated"]}')
print(f'   失败: {sync_result["failed"]}')
if sync_result['errors']:
    print('   错误详情:')
    for error in sync_result['errors'][:3]:
        print(f'     {error["employee_id"]}: {error["error"]}')

print()
print('4. 获取同步统计信息:')
stats = sync_manager.get_employee_stats(mock_employees)
print(f'   数据库总数: {stats.get("db_total", 0)}')
print(f'   内存总数: {stats.get("memory_total", 0)}')
print()
print('   数据库按类型统计:')
for emp_type, count in stats.get('db_by_type', {}).items():
    print(f'     {emp_type}: {count}')
print()
print('   内存按类型统计:')
for emp_type, count in stats.get('memory_by_type', {}).items():
    print(f'     {emp_type}: {count}')

print()
print('5. 导出员工数据:')
export_result = sync_manager.export_employees(mock_employees, '/tmp/mock_employees.json')
print(f'   导出员工数: {export_result["total_employees"]}')
print(f'   输出文件: {export_result["output_file"]}')

print()
print('6. 再次同步(测试更新):')
mock_employees['val_001'].level = 6
mock_employees['val_001'].performance_score = 85.0
sync_result2 = sync_manager.sync_all_employees(mock_employees)
print(f'   新增: {sync_result2["created"]}')
print(f'   更新: {sync_result2["updated"]}')

print()
print('=' * 60)
print('测试完成')
print('=' * 60)
