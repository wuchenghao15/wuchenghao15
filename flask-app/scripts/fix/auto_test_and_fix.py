#!/usr/bin/env python3
import os
import sys
import sqlite3
import datetime
import json

DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'app.db')
DATA_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'data')
FIX_RECORDS = []

def log_fix(fix_id, category, description, status, details=''):
    fix_record = {
        'fix_id': fix_id,
        'category': category,
        'description': description,
        'status': status,
        'details': details,
        'fixed_at': datetime.datetime.now().isoformat()
    }
    FIX_RECORDS.append(fix_record)
    status_icon = '✓' if status == 'success' else '✗'
    print(f'  [{status_icon}] [{category}] {description}')

def fix_database_files():
    print('[修复1/4] 数据库文件修复...')

    os.makedirs(DATA_DIR, exist_ok=True)
    example_db = os.path.join(DATA_DIR, 'example_db.sqlite')

    if not os.path.exists(example_db):
        try:
            conn = sqlite3.connect(example_db)
            cursor = conn.cursor()
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS system_rules (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    rule_code TEXT UNIQUE NOT NULL,
                    rule_name TEXT,
                    rule_value TEXT,
                    rule_type TEXT DEFAULT 'maintenance',
                    description TEXT,
                    is_active INTEGER DEFAULT 1,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                    updated_at TEXT DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS ai_brain_knowledge (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    knowledge_id TEXT UNIQUE NOT NULL,
                    title TEXT NOT NULL,
                    content TEXT NOT NULL,
                    category TEXT,
                    domain TEXT,
                    tags TEXT,
                    confidence REAL DEFAULT 0.0,
                    source TEXT,
                    source_url TEXT,
                    status TEXT DEFAULT 'active',
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                    updated_at TEXT DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            conn.commit()
            conn.close()
            log_fix('FIX-001', 'database', '创建example_db.sqlite数据库', 'success',
                   f'创建路径: {example_db}')
        except Exception as e:
            log_fix('FIX-001', 'database', '创建example_db.sqlite数据库', 'failed', str(e))
    else:
        log_fix('FIX-001', 'database', 'example_db.sqlite已存在', 'success', '文件已存在')

def fix_brain_activity_log_table():
    print('[修复2/4] 脑库活动日志表修复...')

    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()

        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='brain_activity_log'")
        if not cursor.fetchone():
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS brain_activity_log (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    activity_type TEXT NOT NULL,
                    activity_details TEXT,
                    knowledge_count INTEGER DEFAULT 0,
                    source TEXT,
                    status TEXT DEFAULT 'success',
                    error_message TEXT,
                    duration_ms INTEGER DEFAULT 0,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_brain_activity_type ON brain_activity_log(activity_type)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_brain_activity_created ON brain_activity_log(created_at)')
            conn.commit()
            log_fix('FIX-002', 'table', '创建brain_activity_log表', 'success',
                   '添加了脑库活动记录表，含索引优化')
        else:
            log_fix('FIX-002', 'table', 'brain_activity_log表已存在', 'success')

        conn.close()
    except Exception as e:
        log_fix('FIX-002', 'table', '创建brain_activity_log表', 'failed', str(e))

def fix_missing_system_rules():
    print('[修复3/4] 系统规则修复...')

    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()

        missing_rules = [
            ('AUTO_FIX_ENABLED', '自动修复启用', '1', 'maintenance', '是否启用自动修复功能', 1),
            ('AUTO_TEST_ENABLED', '自动测试启用', '1', 'maintenance', '是否启用自动测试功能', 1),
            ('AUTO_REPAIR_ENABLED', '自动修复系统', '1', 'maintenance', '是否启用系统自动修复', 1),
            ('FIX_VERIFY_RETRY_COUNT', '修复验证重试次数', '3', 'maintenance', '修复后验证的最大重试次数', 1),
            ('BRAIN_ACTIVITY_LOG_RETENTION', '脑库日志保留天数', '30', 'maintenance', '脑库活动日志保留天数', 1),
        ]

        fixed_count = 0
        for rule_code, rule_name, rule_value, rule_type, description, is_active in missing_rules:
            cursor.execute("SELECT rule_code FROM system_rules WHERE rule_code = ?", (rule_code,))
            if not cursor.fetchone():
                cursor.execute('''
                    INSERT INTO system_rules
                    (rule_code, rule_name, rule_value, rule_type, description, is_active, created_at, updated_at)
                    VALUES (?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
                ''', (rule_code, rule_name, rule_value, rule_type, description, is_active))
                fixed_count += 1
                log_fix(f'FIX-003-{rule_code}', 'rule', f'添加规则 {rule_code}', 'success',
                       f'{rule_name} = {rule_value}')
            else:
                log_fix(f'FIX-003-{rule_code}', 'rule', f'规则 {rule_code} 已存在', 'success')

        conn.commit()
        conn.close()
    except Exception as e:
        log_fix('FIX-003', 'rule', '添加系统规则', 'failed', str(e))

def fix_feed_to_brain():
    print('[修复4/4] 修复方案投喂到AI脑库...')

    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()

        fix_knowledge_items = [
            {
                'knowledge_id': 'FIX-DB-001',
                'title': '数据库文件缺失自动修复方案',
                'content': '当检测到data/example_db.sqlite数据库文件缺失时，自动创建该数据库并初始化必要的表结构，包括system_rules和ai_brain_knowledge表，确保系统能够正常运行。',
                'category': '数据库修复',
                'domain': 'Database',
                'tags': 'database,fix,auto_repair',
                'confidence': 0.95,
                'source': 'auto_fix_engine'
            },
            {
                'knowledge_id': 'FIX-TABLE-001',
                'title': 'brain_activity_log表结构规范',
                'content': '脑库活动记录表(brain_activity_log)用于记录所有脑库操作活动，包括知识投喂、学习周期、规则执行等。包含字段：activity_type, activity_details, knowledge_count, source, status, error_message, duration_ms, created_at。',
                'category': '表结构修复',
                'domain': 'Database',
                'tags': 'table_schema,brain,log',
                'confidence': 0.90,
                'source': 'auto_fix_engine'
            },
            {
                'knowledge_id': 'FIX-RULE-001',
                'title': '系统规则完整性自动检查与修复',
                'content': '系统启动时自动检查关键系统规则是否存在，包括AUTO_FIX_ENABLED、AUTO_TEST_ENABLED、AUTO_REPAIR_ENABLED等核心规则。缺失的规则自动添加默认值，确保系统功能正常运行。',
                'category': '规则修复',
                'domain': 'Configuration',
                'tags': 'rules,system_config,auto_fix',
                'confidence': 0.92,
                'source': 'auto_fix_engine'
            },
            {
                'knowledge_id': 'FIX-TEST-001',
                'title': '自动化测试与修复流水线',
                'content': '完整的自动测试与修复流程：1) 数据库文件检查 2) Python语法检查 3) 表结构完整性检查 4) 系统规则检查 5) 代码导入检查。发现问题后自动执行对应修复方案，并将修复记录保存到修复历史表。',
                'category': '测试修复',
                'domain': 'DevOps',
                'tags': 'testing,auto_fix,pipeline,ci_cd',
                'confidence': 0.88,
                'source': 'auto_fix_engine'
            },
            {
                'knowledge_id': 'FIX-VERIFY-001',
                'title': '修复验证机制',
                'content': '每次自动修复后执行验证步骤，确认修复是否成功。验证包括：重新运行检查项、检查表是否存在、验证规则是否生效、测试核心功能是否正常。失败的修复会记录错误信息并触发重试机制。',
                'category': '修复验证',
                'domain': 'Quality',
                'tags': 'verification,qa,testing,fix',
                'confidence': 0.85,
                'source': 'auto_fix_engine'
            }
        ]

        fed_count = 0
        for item in fix_knowledge_items:
            cursor.execute("SELECT knowledge_id FROM ai_brain_knowledge WHERE knowledge_id = ?",
                         (item['knowledge_id'],))
            if not cursor.fetchone():
                cursor.execute('''
                    INSERT INTO ai_brain_knowledge
                    (knowledge_id, title, content, knowledge_type, source, tags, priority, status, created_at, updated_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, 'active', CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
                ''', (item['knowledge_id'], item['title'], item['content'],
                      item['category'], item['source'], item['tags'], 1))
                fed_count += 1

        conn.commit()
        conn.close()

        log_fix('FIX-004', 'brain_feeding', '投喂修复方案到脑库', 'success',
               f'成功投喂 {fed_count} 条修复方案知识')
    except Exception as e:
        log_fix('FIX-004', 'brain_feeding', '投喂修复方案到脑库', 'failed', str(e))

def save_fix_records_to_db():
    print()
    print('保存修复记录到数据库...')

    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()

        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='auto_fix_records'")
        if not cursor.fetchone():
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS auto_fix_records (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    fix_id TEXT NOT NULL,
                    category TEXT,
                    description TEXT,
                    status TEXT,
                    details TEXT,
                    fixed_at TEXT DEFAULT CURRENT_TIMESTAMP
                )
            ''')

        for record in FIX_RECORDS:
            cursor.execute('''
                INSERT INTO auto_fix_records
                (fix_id, category, description, status, details, fixed_at)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (record['fix_id'], record['category'], record['description'],
                  record['status'], record['details'], record['fixed_at']))

        conn.commit()
        conn.close()
        print(f'  ✓ 已保存 {len(FIX_RECORDS)} 条修复记录')
    except Exception as e:
        print(f'  ✗ 保存失败: {e}')

def generate_fix_report():
    print()
    print('=' * 70)
    print('  自动修复报告')
    print('=' * 70)
    print()

    success_count = sum(1 for r in FIX_RECORDS if r['status'] == 'success')
    fail_count = sum(1 for r in FIX_RECORDS if r['status'] == 'failed')

    print(f'  总修复项: {len(FIX_RECORDS)}')
    print(f'  成功: {success_count}')
    print(f'  失败: {fail_count}')
    print()

    print('  修复详情:')
    for r in FIX_RECORDS:
        icon = '✓' if r['status'] == 'success' else '✗'
        print(f'    [{icon}] {r["fix_id"]} - {r["description"]}')

    print()
    print('=' * 70)

    report_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'auto_fix_report.json')
    with open(report_file, 'w', encoding='utf-8') as f:
        json.dump({
            'generated_at': datetime.datetime.now().isoformat(),
            'total_fixes': len(FIX_RECORDS),
            'success_count': success_count,
            'fail_count': fail_count,
            'fix_records': FIX_RECORDS
        }, f, ensure_ascii=False, indent=2)
    print(f'  报告已保存: {report_file}')
    print()

def main():
    print()
    print('=' * 70)
    print('  MTSCOS AI Project - 自动测试与修复引擎')
    print('=' * 70)
    print()

    fix_database_files()
    print()
    fix_brain_activity_log_table()
    print()
    fix_missing_system_rules()
    print()
    fix_feed_to_brain()

    save_fix_records_to_db()
    generate_fix_report()

    success_count = sum(1 for r in FIX_RECORDS if r['status'] == 'success')
    return 0 if success_count == len(FIX_RECORDS) else 1

if __name__ == '__main__':
    sys.exit(main())
