#!/usr/bin/env python3
import sys
sys.path.insert(0, '/Users/wuchenghao/Library/CloudStorage/OneDrive-个人/文档/MTSCOS_AI_Project')

from ai_engines.db_query_agent import AIDatabaseQueryAgent

print('=' * 60)
print('AI数据库查询Agent - 功能测试')
print('=' * 60)

agent = AIDatabaseQueryAgent('db_qry_001', '数据库查询AI Agent', 9)
agent.start()
print('Agent启动成功')

print()
print('1. 获取数据库统计信息:')
stats = agent.get_database_stats()
for db_name, db_info in list(stats.items())[:5]:
    if 'error' not in db_info:
        print('  {}: {}个表'.format(db_name, db_info['total_tables']))
        if db_info['tables']:
            print('    表列表:', db_info['tables'][:3])
print('  共{}个数据库'.format(len(stats)))

print()
print('2. 获取表结构信息:')
schema = agent.get_table_schema('users')
if schema:
    print('  表名:', schema['table'])
    print('  数据库:', schema['database'])
    print('  字段:')
    for col in schema['columns'][:5]:
        print('    - {} ({})'.format(col['name'], col['type']))
else:
    print('  未找到users表')

print()
print('3. 执行SQL查询(auth.db):')
result = agent.execute_query('SELECT * FROM users LIMIT 5')
print('  成功:', result['success'])
if result['success']:
    print('  执行时间:', result['execution_time'], '秒')
    print('  结果数量:', len(result.get('data', [])))
    for row in result['data'][:2]:
        print('    -', dict(row))
else:
    print('  错误:', result.get('error', '未知错误'))

print()
print('4. 查询缓存测试:')
result2 = agent.execute_query('SELECT * FROM users LIMIT 5')
print('  成功:', result2['success'])
if result2['success']:
    print('  来自缓存:', result2.get('from_cache', False))
    print('  执行时间:', result2['execution_time'], '秒')

print()
print('5. 查询ai.db中的表:')
result = agent.execute_query('SELECT * FROM ai_agents LIMIT 5')
print('  成功:', result['success'])
if result['success']:
    print('  执行时间:', result['execution_time'], '秒')
    print('  结果数量:', len(result.get('data', [])))

print()
print('6. 自然语言转SQL:')
natural_queries = [
    '-- 用户数量',
    '-- 所有用户',
    '-- 管理员',
    '-- 错误日志',
    '-- 修复记录'
]
for query in natural_queries:
    sql = agent.natural_to_sql(query[2:].strip())
    print('  "{}" -> {}'.format(query[2:].strip(), sql))

print()
print('7. 智能查询（自然语言）:')
result = agent.smart_query('-- 用户数量')
print('  成功:', result['success'])
if result['success']:
    print('  结果:', result['data'])

print()
print('8. 聚合查询:')
result = agent.aggregate_query('users', 'role', {'count': 'id'})
print('  成功:', result['success'])
if result['success']:
    print('  聚合结果:', len(result['data']), '条')
    for row in result['data'][:3]:
        print('    - {}: {}个'.format(row.get('role', 'N/A'), row.get('count_id', 0)))

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
