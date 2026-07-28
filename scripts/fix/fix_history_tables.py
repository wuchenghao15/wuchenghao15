#!/usr/bin/env python3
"""修复历史馆相关数据库表：system_versions, upgrade_history, ai_brain_bank, ai_learning_tasks"""

import os
import sys
import json
import sqlite3

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from core.db_path import get_db_path


def main():
    db_path = get_db_path('app.db')
    print(f"数据库路径: {db_path}")
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # ============================================
    # 1. 创建 system_versions 表并填充数据
    # ============================================
    print("\n=== 1. 修复 system_versions 表 ===")
    
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='system_versions'")
    if cursor.fetchone():
        print("  system_versions 表已存在，跳过创建")
    else:
        cursor.execute('''
            CREATE TABLE system_versions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                version TEXT NOT NULL,
                major INTEGER,
                minor INTEGER,
                patch INTEGER,
                build_number TEXT,
                build_date TEXT,
                codename TEXT,
                status TEXT DEFAULT 'stable',
                description TEXT,
                features TEXT,
                upgrade_notes TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                updated_at TEXT
            )
        ''')
        print("  system_versions 表创建成功")
    
    # 检查是否有数据
    cursor.execute('SELECT COUNT(*) FROM system_versions')
    count = cursor.fetchone()[0]
    if count > 0:
        print(f"  system_versions 已有 {count} 条数据，跳过填充")
    else:
        # 先从 system_version_history 迁移数据
        cursor.execute('SELECT version, build_date, codename, description, features, status, upgrade_notes, created_at FROM system_version_history ORDER BY build_date DESC')
        old_versions = cursor.fetchall()
        
        inserted = 0
        for row in old_versions:
            version = row[0]
            parts = version.split('.')
            major = int(parts[0]) if len(parts) > 0 else 0
            minor = int(parts[1]) if len(parts) > 1 else 0
            patch = int(parts[2]) if len(parts) > 2 else 0
            
            cursor.execute('''
                INSERT INTO system_versions 
                (version, major, minor, patch, build_date, codename, description, features, status, upgrade_notes, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                version, major, minor, patch,
                row[1],  # build_date
                row[2],  # codename
                row[3],  # description
                row[4],  # features
                row[5] or 'stable',  # status
                row[6],  # upgrade_notes
                row[7],  # created_at
            ))
            inserted += 1
        
        print(f"  从 system_version_history 迁移了 {inserted} 条版本记录")
        
        # 从 version_manager.py 的 VERSION_DATA 补充新版本（v17.x.x）
        try:
            from core.services.version_manager import VERSION_DATA
            
            new_count = 0
            for version, data in sorted(VERSION_DATA.items(), key=lambda x: x[1].get('build_date', ''), reverse=True):
                cursor.execute('SELECT id FROM system_versions WHERE version = ?', (version,))
                if cursor.fetchone():
                    continue
                
                parts = version.split('.')
                major = int(parts[0]) if len(parts) > 0 else 0
                minor = int(parts[1]) if len(parts) > 1 else 0
                patch = int(parts[2]) if len(parts) > 2 else 0
                
                features_json = json.dumps(data.get('features', []), ensure_ascii=False)
                
                cursor.execute('''
                    INSERT INTO system_versions 
                    (version, major, minor, patch, build_number, build_date, codename, status, description, features, upgrade_notes, created_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    version, major, minor, patch,
                    data.get('build_number', ''),
                    data.get('build_date', ''),
                    data.get('codename', ''),
                    data.get('status', 'stable'),
                    data.get('description', ''),
                    features_json,
                    data.get('upgrade_notes', ''),
                    data.get('build_date', '') + 'T00:00:00',
                ))
                new_count += 1
            
            print(f"  从 version_manager.VERSION_DATA 补充了 {new_count} 条新版本记录")
        except Exception as e:
            print(f"  从 version_manager 导入失败: {e}")
    
    conn.commit()
    
    # ============================================
    # 2. 修复 upgrade_history 表列名
    # ============================================
    print("\n=== 2. 修复 upgrade_history 表列名 ===")
    
    cursor.execute('PRAGMA table_info(upgrade_history)')
    columns = {row[1]: row[2] for row in cursor.fetchall()}
    
    if 'ai_employees_count' in columns and 'features_count' in columns:
        print("  upgrade_history 表列名已正确，跳过")
    else:
        # 需要重命名列或添加列
        if 'ai_count' in columns and 'ai_employees_count' not in columns:
            cursor.execute('ALTER TABLE upgrade_history ADD COLUMN ai_employees_count INTEGER DEFAULT 0')
            cursor.execute('UPDATE upgrade_history SET ai_employees_count = ai_count')
            print("  添加 ai_employees_count 列并同步数据")
        
        if 'feature_count' in columns and 'features_count' not in columns:
            cursor.execute('ALTER TABLE upgrade_history ADD COLUMN features_count INTEGER DEFAULT 0')
            cursor.execute('UPDATE upgrade_history SET features_count = feature_count')
            print("  添加 features_count 列并同步数据")
    
    conn.commit()
    
    # ============================================
    # 3. 创建 ai_brain_bank 表并迁移数据
    # ============================================
    print("\n=== 3. 修复 ai_brain_bank 表 ===")
    
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='ai_brain_bank'")
    if cursor.fetchone():
        cursor.execute('SELECT COUNT(*) FROM ai_brain_bank')
        count = cursor.fetchone()[0]
        print(f"  ai_brain_bank 表已存在，有 {count} 条数据")
    else:
        cursor.execute('''
            CREATE TABLE ai_brain_bank (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                category TEXT,
                title TEXT,
                content TEXT,
                tags TEXT,
                version TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        print("  ai_brain_bank 表创建成功")
        
        # 从 ai_brain_knowledge 迁移数据
        cursor.execute('SELECT knowledge_type, title, content, tags, created_at FROM ai_brain_knowledge ORDER BY created_at DESC LIMIT 200')
        rows = cursor.fetchall()
        
        for row in rows:
            cursor.execute('''
                INSERT INTO ai_brain_bank (category, title, content, tags, version, created_at)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (
                row[0] or 'general',  # category
                row[1],  # title
                row[2],  # content
                row[3],  # tags
                '17.22.0',  # version
                row[4],  # created_at
            ))
        
        print(f"  从 ai_brain_knowledge 迁移了 {len(rows)} 条知识记录")
    
    conn.commit()
    
    # ============================================
    # 4. 创建 ai_learning_tasks 表并初始化数据
    # ============================================
    print("\n=== 4. 修复 ai_learning_tasks 表 ===")
    
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='ai_learning_tasks'")
    if cursor.fetchone():
        cursor.execute('SELECT COUNT(*) FROM ai_learning_tasks')
        count = cursor.fetchone()[0]
        print(f"  ai_learning_tasks 表已存在，有 {count} 条数据")
    else:
        cursor.execute('''
            CREATE TABLE ai_learning_tasks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                task_name TEXT NOT NULL,
                task_desc TEXT,
                task_type TEXT,
                version TEXT,
                status TEXT DEFAULT 'completed',
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        print("  ai_learning_tasks 表创建成功")
        
        # 初始化学习任务数据
        tasks = [
            ('AI自学习引擎初始化', '启动AI自学习引擎，建立基础学习框架', 'system_init', '17.0.0', 'completed'),
            ('知识脑库构建', '构建AI知识脑库，整合多源知识资源', 'knowledge_base', '17.0.0', 'completed'),
            ('AI员工技能培训', '培训AI员工掌握核心技能', 'skill_training', '17.5.0', 'completed'),
            ('协作模式优化', '优化多AI员工协作模式', 'collaboration', '17.10.0', 'completed'),
            ('代码质量提升', 'AI学习代码最佳实践', 'code_quality', '17.15.0', 'completed'),
            ('安全协议学习', 'AI学习网络安全和数据保护协议', 'security', '17.16.0', 'completed'),
            ('Arduino知识学习', 'AI学习Arduino硬件编程知识', 'hardware', '17.20.0', 'completed'),
            ('动态题目生成学习', 'AI学习动态题目生成策略', 'education', '17.20.0', 'completed'),
            ('版本管理学习', 'AI学习版本管理和升级流程', 'devops', '17.22.0', 'in_progress'),
            ('用户体验优化学习', 'AI学习用户体验优化方法', 'ux', '17.22.0', 'pending'),
        ]
        
        for task in tasks:
            cursor.execute('''
                INSERT INTO ai_learning_tasks (task_name, task_desc, task_type, version, status)
                VALUES (?, ?, ?, ?, ?)
            ''', task)
        
        print(f"  初始化了 {len(tasks)} 条学习任务")
    
    conn.commit()
    
    # ============================================
    # 5. 验证结果
    # ============================================
    print("\n=== 5. 验证结果 ===")
    
    tables_to_check = [
        ('system_versions', '版本记录'),
        ('upgrade_history', '升级记录'),
        ('ai_brain_bank', '知识脑库'),
        ('ai_learning_tasks', '学习任务'),
    ]
    
    for table, desc in tables_to_check:
        try:
            cursor.execute(f'SELECT COUNT(*) FROM "{table}"')
            count = cursor.fetchone()[0]
            print(f"  {desc}: {count} 条")
        except Exception as e:
            print(f"  {desc}: 查询失败 - {e}")
    
    # 验证 history_api 所需的查询
    print("\n=== 6. 验证历史馆API查询 ===")
    
    # 测试 stats 查询
    try:
        cursor.execute('SELECT COUNT(*) FROM system_versions')
        versions = cursor.fetchone()[0]
        cursor.execute('SELECT COUNT(*) FROM upgrade_history')
        upgrades = cursor.fetchone()[0]
        cursor.execute('SELECT COUNT(*) FROM ai_brain_bank')
        knowledge = cursor.fetchone()[0]
        cursor.execute('SELECT COUNT(*) FROM ai_learning_tasks')
        learning = cursor.fetchone()[0]
        print(f"  stats: versions={versions}, upgrades={upgrades}, knowledge={knowledge}, learning={learning}")
    except Exception as e:
        print(f"  stats 查询失败: {e}")
    
    # 测试 timeline 查询
    try:
        cursor.execute('SELECT version, build_date, codename, description, features, status FROM system_versions ORDER BY build_date DESC LIMIT 3')
        rows = cursor.fetchall()
        print(f"  timeline: 最新3个版本")
        for row in rows:
            print(f"    {row[0]} - {row[2]}")
    except Exception as e:
        print(f"  timeline 查询失败: {e}")
    
    conn.close()
    print("\n✅ 修复完成！")


if __name__ == '__main__':
    main()
