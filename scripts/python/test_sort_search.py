#!/usr/bin/env python3
import sys
sys.path.insert(0, '/Users/wuchenghao/Library/CloudStorage/OneDrive-个人/文档/MTSCOS_AI_Project')

from ai_engines.db_sort_search_agent import AIDatabaseSortSearchAgent

print('=' * 60)
print('AI数据库排序检索Agent - 功能测试')
print('=' * 60)

agent = AIDatabaseSortSearchAgent('db_sort_001', '数据库排序检索AI Agent', 9)
agent.start()
print('Agent启动成功')

print()
print('1. 智能排序查询(users表):')
result = agent.smart_sort_query('users', sort_by='created_at', sort_order='DESC', page=1, page_size=5)
print('  成功:', result['success'])
if result['success']:
    print('  总记录:', result['total'])
    print('  页码:', result['page'], '/', result['total_pages'])
    print('  排序:', result['sort_by'], result['sort_order'])
    print('  结果:')
    for row in result['data'][:3]:
        print('    -', row['username'], '-', row['role'], '-', row['created_at'])

print()
print('2. 带条件的排序查询(管理员):')
result = agent.smart_sort_query('users', conditions={'role': 'admin'}, sort_by='id', sort_order='ASC')
print('  成功:', result['success'])
if result['success']:
    print('  总记录:', result['total'])
    print('  结果:')
    for row in result['data']:
        print('    -', row['username'], '-', row['role'])

print()
print('3. 全文检索(搜索admin):')
result = agent.full_text_search('users', 'admin')
print('  成功:', result['success'])
if result['success']:
    print('  总记录:', result['total'])
    print('  搜索字段:', result['search_fields'])
    print('  结果:')
    for row in result['data'][:3]:
        print('    -', row['username'], '-', row['email'])

print()
print('4. 高级查询(带复杂条件):')
query_spec = {
    'columns': ['username', 'email', 'role', 'created_at'],
    'conditions': {'role': {'op': 'IN', 'value': ['admin', 'teacher']}},
    'sort_by': 'created_at',
    'sort_order': 'DESC',
    'page': 1,
    'page_size': 10
}
result = agent.advanced_query('users', query_spec)
print('  成功:', result['success'])
if result['success']:
    print('  总记录:', result['total'])
    print('  结果数量:', len(result['data']))

print()
print('5. 自然语言搜索("搜索管理员"):')
result = agent.natural_language_search('搜索管理员')
print('  成功:', result['success'])
if result['success']:
    print('  总记录:', result['total'])
    print('  结果:')
    for row in result['data'][:3]:
        print('    -', row['username'], '-', row['role'])

print()
print('6. 搜索建议("adm"前缀):')
suggestions = agent.get_search_suggestions('users', 'adm')
print('  建议数量:', len(suggestions))
print('  建议:', suggestions)

print()
print('7. 查询缓存测试(重复查询):')
result1 = agent.smart_sort_query('users', sort_by='id', sort_order='ASC', page=1, page_size=3)
print('  第一次查询 - 成功:', result1['success'], ', 来自缓存:', result1.get('from_cache', False))
result2 = agent.smart_sort_query('users', sort_by='id', sort_order='ASC', page=1, page_size=3)
print('  第二次查询 - 成功:', result2['success'], ', 来自缓存:', result2.get('from_cache', False))

print()
print('8. 分页测试:')
result = agent.smart_sort_query('users', page=2, page_size=3)
print('  成功:', result['success'])
if result['success']:
    print('  当前页:', result['page'], '/', result['total_pages'])
    print('  结果数量:', len(result['data']))

print()
print('9. 缓存统计:')
cache_stats = agent.get_cache_stats()
print('  缓存大小:', cache_stats['cache_size'])
print('  最大大小:', cache_stats['max_size'])
print('  总命中次数:', cache_stats['total_hits'])

agent.stop()
print()
print('=' * 60)
print('测试完成')
print('=' * 60)
