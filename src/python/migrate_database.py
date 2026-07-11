"""
数据库迁移脚本 - 从旧架构迁移到新架构
"""

import sqlite3
import json
import time
import os
from database_schema import SCHEMA
from database_schema_base import EnhancedDatabaseManager


def backup_old_database(old_path: str) -> str:
    """备份旧数据库"""
    if not os.path.exists(old_path):
        print("⚠️ 旧数据库不存在，跳过备份")
        return None
    
    backup_path = f"{old_path}.backup_{int(time.time())}"
    with open(old_path, 'rb') as f:
        data = f.read()
    with open(backup_path, 'wb') as f:
        f.write(data)
    print(f"✅ 已备份旧数据库到: {backup_path}")
    return backup_path


def migrate_data(old_conn: sqlite3.Connection, new_db: EnhancedDatabaseManager):
    """迁移数据"""
    print("\n📦 开始数据迁移...")
    
    # 获取旧数据库中的数据
    tables_to_migrate = [
        ('users', 'users'),
        ('ai_employees', 'ai_employees'),
    ]
    
    for old_table, new_table in tables_to_migrate:
        try:
            # 获取旧数据
            old_rows = old_conn.execute(f"SELECT * FROM {old_table}").fetchall()
            old_columns = [desc[0] for desc in old_conn.execute(f"PRAGMA table_info({old_table})").fetchall()]
            
            if old_rows:
                print(f"  📤 迁移 {old_table}: {len(old_rows)} 条记录")
                
                for row in old_rows:
                    data = dict(zip(old_columns, row))
                    try:
                        new_db.add(new_table, data)
                    except Exception as e:
                        print(f"    ⚠️ 跳过重复记录: {e}")
            else:
                print(f"  ⏭️ {old_table}: 无数据")
                
        except Exception as e:
            print(f"  ❌ 迁移 {old_table} 失败: {e}")
    
    print("✅ 数据迁移完成")


def create_initial_data(db: EnhancedDatabaseManager):
    """创建初始数据"""
    print("\n📝 创建初始数据...")
    
    # 创建默认管理员
    from main import Encryption
    password_hash = Encryption.hash_password('admin123')
    
    try:
        db.add('users', {
            'user_id': 'admin_001',
            'username': 'admin',
            'password_hash': password_hash,
            'email': 'admin@mtscos.com',
            'role': 'superadmin',
            'status': 'active',
            'created_at': int(time.time()),
            'updated_at': int(time.time())
        })
        print("  ✅ 创建默认管理员 (admin / admin123)")
    except Exception as e:
        print(f"  ⏭️ 管理员已存在: {e}")
    
    # 创建默认角色
    default_roles = [
        {'role_id': 'superadmin', 'name': '超级管理员', 'description': '系统最高权限', 'level': 100, 'is_system': 1},
        {'role_id': 'admin', 'name': '管理员', 'description': '系统管理员', 'level': 90, 'is_system': 1},
        {'role_id': 'vikey_admin', 'name': 'Vikey管理员', 'description': 'AI员工管理员', 'level': 80, 'is_system': 1},
        {'role_id': 'user', 'name': '普通用户', 'description': '普通用户', 'level': 10, 'is_system': 1},
        {'role_id': 'guest', 'name': '访客', 'description': '访客用户', 'level': 1, 'is_system': 1},
    ]
    
    for role in default_roles:
        role['permissions'] = json.dumps(role.get('permissions', []))
        role['created_at'] = int(time.time())
        role['updated_at'] = int(time.time())
        try:
            db.add('roles', role)
            print(f"  ✅ 创建角色: {role['name']}")
        except Exception as e:
            print(f"  ⏭️ 角色已存在: {role['name']}")
    
    # 创建默认主题
    default_themes = [
        {
            'theme_id': 'light', 'name': '明亮模式', 'type': 'light',
            'colors': json.dumps({
                'primary': '#3b82f6', 'background': '#ffffff', 'text': '#1f2937'
            }),
            'is_default': 1, 'created_at': int(time.time())
        },
        {
            'theme_id': 'dark', 'name': '深色模式', 'type': 'dark',
            'colors': json.dumps({
                'primary': '#60a5fa', 'background': '#1f2937', 'text': '#f9fafb'
            }),
            'is_default': 0, 'created_at': int(time.time())
        },
        {
            'theme_id': 'sunset', 'name': '日落模式', 'type': 'custom',
            'colors': json.dumps({
                'primary': '#f97316', 'background': '#fef3c7', 'text': '#78350f'
            }),
            'is_default': 0, 'created_at': int(time.time())
        },
    ]
    
    for theme in default_themes:
        try:
            db.add('themes', theme)
            print(f"  ✅ 创建主题: {theme['name']}")
        except Exception as e:
            print(f"  ⏭️ 主题已存在: {theme['name']}")
    
    # 创建默认AI员工分类
    default_categories = [
        {'category_id': 'core', 'name': '核心管理层', 'icon': 'fa-crown', 'sort_order': 1},
        {'category_id': 'technical', 'name': '技术执行层', 'icon': 'fa-code', 'sort_order': 2},
        {'category_id': 'design', 'name': '设计美化层', 'icon': 'fa-palette', 'sort_order': 3},
        {'category_id': 'education', 'name': '教育考试层', 'icon': 'fa-graduation-cap', 'sort_order': 4},
        {'category_id': 'security', 'name': '安全防护层', 'icon': 'fa-shield-alt', 'sort_order': 5},
        {'category_id': 'data', 'name': '数据管理层', 'icon': 'fa-database', 'sort_order': 6},
        {'category_id': 'operation', 'name': '运维支持层', 'icon': 'fa-server', 'sort_order': 7},
        {'category_id': 'cloud', 'name': '云端管理层', 'icon': 'fa-cloud', 'sort_order': 8},
        {'category_id': 'config', 'name': '配置管理层', 'icon': 'fa-cog', 'sort_order': 9},
    ]
    
    for cat in default_categories:
        cat['created_at'] = int(time.time())
        try:
            db.add('ai_employee_categories', cat)
            print(f"  ✅ 创建分类: {cat['name']}")
        except Exception as e:
            print(f"  ⏭️ 分类已存在: {cat['name']}")
    
    print("✅ 初始数据创建完成")


def main():
    """主函数"""
    print("""
╔══════════════════════════════════════════════════════════╗
║           数据库迁移工具 - 分表分项架构                     ║
╚══════════════════════════════════════════════════════════╝
    """)
    
    # 路径设置
    old_db_path = "data/mtscos.db"
    new_db_path = "data/mtscos_new.db"
    script_dir = os.path.dirname(os.path.abspath(__file__))
    old_full_path = os.path.join(script_dir, '..', old_db_path)
    new_full_path = os.path.join(script_dir, '..', new_db_path)
    
    # 备份旧数据库
    backup_path = backup_old_database(old_full_path)
    
    # 连接旧数据库
    old_conn = None
    if backup_path:
        old_full_backup = backup_path.replace('..' + os.sep, '').replace('..', '')
        old_full_backup_path = os.path.join(script_dir, backup_path)
        if os.path.exists(old_full_backup_path):
            old_conn = sqlite3.connect(old_full_backup_path)
            old_conn.row_factory = sqlite3.Row
    
    # 创建新数据库
    print(f"\n📦 创建新数据库: {new_db_path}")
    new_db = EnhancedDatabaseManager(new_full_path, SCHEMA)
    
    # 迁移数据
    if old_conn:
        migrate_data(old_conn, new_db)
        old_conn.close()
    
    # 创建初始数据
    create_initial_data(new_db)
    
    # 显示统计
    print("\n📊 新数据库统计:")
    stats = new_db.get_stats()
    for table, count in stats.items():
        print(f"  {table}: {count} 条记录")
    
    print(f"""
╔══════════════════════════════════════════════════════════╗
║                   迁移完成！                              ║
╠══════════════════════════════════════════════════════════╣
║  新数据库: {new_db_path:<47}  ║
║  表数量: {len(stats):<49}  ║
╚══════════════════════════════════════════════════════════╝

💡 下一步:
  1. 测试新数据库功能
  2. 确认无误后，可删除旧数据库备份
  3. 将新数据库重命名为正式名称
    """)


if __name__ == '__main__':
    main()
