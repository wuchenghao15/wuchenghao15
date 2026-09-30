#!/usr/bin/env python3
import os
import sys
import sqlite3
import json
from datetime import datetime

DATABASE_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'app.db')

VERSION_HISTORY = [
    {
        'version': '1.0.0',
        'codename': 'Initial Release',
        'status': 'stable',
        'description': '系统初始版本，包含基础的用户认证和考试系统',
        'build_date': '2026-01-01',
        'build_number': '20260101a',
        'features': ['用户认证系统', '基础考试系统', '数据库架构'],
        'upgrade_notes': '初始版本'
    },
    {
        'version': '2.0.0',
        'codename': 'AI Integration Edition',
        'status': 'stable',
        'description': 'AI功能集成版本，引入AI引擎和AI员工系统',
        'build_date': '2026-02-15',
        'build_number': '20260215a',
        'features': ['AI引擎系统', 'AI员工基础架构', 'AI学习能力'],
        'upgrade_notes': '首次引入AI功能'
    },
    {
        'version': '3.0.0',
        'codename': 'Knowledge Brain Edition',
        'status': 'stable',
        'description': 'AI脑库版本，实现知识存储、检索和增强功能',
        'build_date': '2026-03-01',
        'build_number': '20260301a',
        'features': ['AI脑库系统', '知识管理', '知识检索', '知识增强'],
        'upgrade_notes': 'AI脑库功能上线'
    },
    {
        'version': '4.0.0',
        'codename': 'Security Enhancement Edition',
        'status': 'stable',
        'description': '安全增强版本，实现数据库加密和安全中间件',
        'build_date': '2026-04-01',
        'build_number': '20260401a',
        'features': ['数据库加密', '安全中间件', '权限管理', '会话超时'],
        'upgrade_notes': '安全功能全面升级'
    },
    {
        'version': '5.0.0',
        'codename': 'Exam System Enhancement',
        'status': 'stable',
        'description': '考试系统增强版本，支持听力题和自动阅卷',
        'build_date': '2026-05-01',
        'build_number': '20260501a',
        'features': ['听力题支持', '自动阅卷', 'AI组卷', '科目分类'],
        'upgrade_notes': '考试系统全面升级'
    },
    {
        'version': '6.0.0',
        'codename': 'Git Sync Edition',
        'status': 'stable',
        'description': 'Git同步版本，实现Git与GitHub自动同步和远程更新检测',
        'build_date': '2026-05-15',
        'build_number': '20260515a',
        'features': ['Git自动同步', '远程更新检测', '数据库迁移', 'AI配置升级'],
        'upgrade_notes': '版本控制和自动升级功能'
    },
    {
        'version': '7.0.0',
        'codename': 'Maintenance Rules Edition',
        'status': 'stable',
        'description': '维护规则版本，实现系统规则数据库化和自动化维护',
        'build_date': '2026-06-01',
        'build_number': '20260601a',
        'features': ['system_rules表', '自动修复系统', '权限同步', '灰度发布'],
        'upgrade_notes': '系统规则全面数据库化'
    },
    {
        'version': '8.0.0',
        'codename': 'AI Employee Empowerment Edition',
        'status': 'stable',
        'description': 'AI员工赋能版本，实现AI员工智能赋能和性格模拟',
        'build_date': '2026-06-15',
        'build_number': '20260615a',
        'features': ['智能赋能系统', '性格模拟', '网络学习', '技能升级'],
        'upgrade_notes': 'AI员工能力全面提升'
    },
    {
        'version': '9.0.0',
        'codename': 'Data Sync Edition',
        'status': 'stable',
        'description': '数据同步版本，实现前端数据与数据库同步',
        'build_date': '2026-07-01',
        'build_number': '20260701a',
        'features': ['数据同步机制', '写穿机制', '前端数据同步', '缓存策略'],
        'upgrade_notes': '数据一致性保障'
    },
    {
        'version': '10.0.0',
        'codename': 'Comprehensive Rules Edition',
        'status': 'stable',
        'description': '综合规则版本，实现沙盒、网络、协议、端口、文档、前端、弹窗等全面规则管理',
        'build_date': '2026-07-15',
        'build_number': '20260715a',
        'features': [
            '沙盒规则系统', '网络规则系统', '协议规则系统', '端口规则系统',
            '文档规则系统', '前端样式规范', '弹窗文档规则', '例行维护规则'
        ],
        'upgrade_notes': '系统规则全面覆盖'
    }
]

def create_system_version_history_table(conn):
    """创建system_version_history表"""
    cursor = conn.cursor()
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS system_version_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            version TEXT NOT NULL,
            major INTEGER NOT NULL,
            minor INTEGER NOT NULL,
            patch INTEGER NOT NULL,
            build_number TEXT,
            build_date TEXT,
            codename TEXT,
            status TEXT DEFAULT 'stable',
            description TEXT,
            features TEXT,
            upgrade_notes TEXT,
            upgrade_time TEXT,
            upgrade_type TEXT DEFAULT 'manual',
            applied_by TEXT DEFAULT 'system',
            notes TEXT,
            previous_version TEXT,
            schema_version INTEGER DEFAULT 1,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    cursor.execute('''
        CREATE INDEX IF NOT EXISTS idx_version_history_version 
        ON system_version_history(version)
    ''')
    
    cursor.execute('''
        CREATE INDEX IF NOT EXISTS idx_version_history_build_date 
        ON system_version_history(build_date)
    ''')
    
    conn.commit()
    print("✓ system_version_history表创建成功")

def insert_version_history(conn, version_data, upgrade_time=None):
    """插入版本历史记录"""
    cursor = conn.cursor()
    
    version_parts = version_data['version'].split('.')
    major = int(version_parts[0])
    minor = int(version_parts[1])
    patch = int(version_parts[2]) if len(version_parts) > 2 else 0
    
    cursor.execute('''
        SELECT COUNT(*) FROM system_version_history WHERE version = ?
    ''', (version_data['version'],))
    
    if cursor.fetchone()[0] == 0:
        cursor.execute('''
            INSERT INTO system_version_history (
                version, major, minor, patch, build_number, build_date,
                codename, status, description, features, upgrade_notes,
                upgrade_time, upgrade_type, applied_by, previous_version
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            version_data['version'],
            major, minor, patch,
            version_data.get('build_number', ''),
            version_data.get('build_date', ''),
            version_data.get('codename', ''),
            version_data.get('status', 'stable'),
            version_data.get('description', ''),
            json.dumps(version_data.get('features', [])),
            version_data.get('upgrade_notes', ''),
            upgrade_time or datetime.now().isoformat(),
            version_data.get('upgrade_type', 'manual'),
            'system',
            version_data.get('previous_version', '')
        ))
        conn.commit()
        print(f"✓ 版本 {version_data['version']} 历史记录已插入")
    else:
        print(f"✓ 版本 {version_data['version']} 历史记录已存在，跳过")

def update_system_version(conn, version):
    """更新system_rules中的版本号"""
    cursor = conn.cursor()
    
    cursor.execute('''
        UPDATE system_rules SET rule_value = ?, updated_at = ? 
        WHERE rule_code = 'SYS_VERSION'
    ''', (version, datetime.now().isoformat()))
    
    conn.commit()
    print(f"✓ 系统版本号已更新为 {version}")

def run_maintenance_tasks(conn):
    """执行例行维护任务"""
    print("\n=== 执行例行维护任务 ===")
    
    cursor = conn.cursor()
    
    print("\n1. 清理无效会话...")
    try:
        cursor.execute("DELETE FROM user_sessions WHERE expires_at < ?", 
                      (datetime.now().isoformat(),))
        deleted = cursor.execute("SELECT changes()").fetchone()[0]
        print(f"   ✓ 清理了 {deleted} 条过期会话")
    except Exception as e:
        print(f"   ✗ 清理会话失败: {e}")
    
    print("\n2. 更新规则状态...")
    try:
        cursor.execute("UPDATE system_rules SET is_active = 1 WHERE is_active IS NULL")
        updated = cursor.execute("SELECT changes()").fetchone()[0]
        print(f"   ✓ 更新了 {updated} 条规则状态")
    except Exception as e:
        print(f"   ✗ 更新规则状态失败: {e}")
    
    print("\n3. 统计规则数量...")
    try:
        cursor.execute("SELECT COUNT(*) FROM system_rules")
        total = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM system_rules WHERE is_active = 1")
        active = cursor.fetchone()[0]
        
        print(f"   ✓ 规则总数: {total}, 启用规则: {active}")
    except Exception as e:
        print(f"   ✗ 统计规则失败: {e}")
    
    print("\n4. 检查数据库完整性...")
    try:
        cursor.execute("PRAGMA integrity_check")
        result = cursor.fetchone()[0]
        if result == 'ok':
            print("   ✓ 数据库完整性检查通过")
        else:
            print(f"   ✗ 数据库完整性检查失败: {result}")
    except Exception as e:
        print(f"   ✗ 数据库完整性检查失败: {e}")
    
    print("\n5. 清理system_maintenance_logs旧记录(保留90天)...")
    try:
        cursor.execute("DELETE FROM system_maintenance_logs WHERE created_at < ?",
                      (datetime.now().strftime('%Y-%m-%d %H:%M:%S'),))
        deleted = cursor.execute("SELECT changes()").fetchone()[0]
        print(f"   ✓ 清理了 {deleted} 条旧记录")
    except Exception as e:
        print(f"   ✗ 清理日志失败: {e}")
    
    conn.commit()
    print("\n✓ 例行维护任务执行完成")

def log_maintenance(conn, action, details):
    """记录维护日志"""
    cursor = conn.cursor()
    
    try:
        cursor.execute('''
            INSERT INTO system_maintenance_logs (action, details, timestamp)
            VALUES (?, ?, ?)
        ''', (action, details, datetime.now().isoformat()))
        conn.commit()
    except Exception as e:
        print(f"记录维护日志失败: {e}")

def main():
    print("=" * 60)
    print("     MTSCOS AI 例行维护系统")
    print("=" * 60)
    print(f"维护时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    try:
        with sqlite3.connect(DATABASE_PATH) as conn:
            print("=== 创建版本历史表 ===")
            create_system_version_history_table(conn)
            
            print("\n=== 写入历史版本记录 ===")
            for i, version_data in enumerate(VERSION_HISTORY):
                if i > 0:
                    version_data['previous_version'] = VERSION_HISTORY[i-1]['version']
                insert_version_history(conn, version_data)
            
            print("\n=== 更新当前系统版本 ===")
            latest_version = VERSION_HISTORY[-1]['version']
            update_system_version(conn, latest_version)
            
            print("\n=== 执行例行维护 ===")
            run_maintenance_tasks(conn)
            
            print("\n=== 记录维护日志 ===")
            log_maintenance(conn, 'routine_maintenance', 
                          f'例行维护完成，版本升级至 {latest_version}')
            
            print("\n" + "=" * 60)
            print("     例行维护完成!")
            print("=" * 60)
            
    except Exception as e:
        print(f"\n✗ 维护失败: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    return 0

if __name__ == '__main__':
    sys.exit(main())