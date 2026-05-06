# -*- coding: utf-8 -*-
import sqlite3

def update_database_table(db_name):
    """修改指定数据库中的user_japanese_levels表结构"""
    print(f"\n=== 修改数据库: {db_name} ===")

    try:
        conn = sqlite3.connect(db_name)
        cursor = conn.cursor()

        # 1. 创建新表
        print("1. 创建新表 user_japanese_levels_new")
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS user_japanese_levels_new (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT NOT NULL,
                level TEXT,
                highest_level TEXT,
                progress REAL NOT NULL DEFAULT 0,
                last_test_date TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                updated_at TEXT DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (username) REFERENCES users(username)
            );
        ''')

        # 2. 检查旧表是否存在
            SELECT name FROM sqlite_master WHERE type='table' AND name='user_japanese_levels';
        ''')

        if old_table_exists:
            # 3. 复制数据
            print("2. 从旧表复制数据到新表")
                INSERT INTO user_japanese_levels_new
                (id, username, level, highest_level, progress, last_test_date, created_at, updated_at)
                SELECT id, username, level, highest_level, progress, last_test_date, created_at, updated_at
                FROM user_japanese_levels;
            ''')

            print("3. 删除旧表 user_japanese_levels")
            cursor.execute('DROP TABLE user_japanese_levels;')

        # 5. 重命名新表
        print("4. 重命名新表为 user_japanese_levels")
        cursor.execute('ALTER TABLE user_japanese_levels_new RENAME TO user_japanese_levels;')

        # 6. 验证修改结果
        print("5. 验证修改结果")
        cursor.execute('PRAGMA table_info(user_japanese_levels);')
        columns = cursor.fetchall()
        print("修改后的表结构:")
        for col in columns:
            print(f"   - {col[1]}: {col[2]}{' (NOT NULL)' if col[3] else ''}")

        conn.commit()
        conn.close()
        print(f"✅ 数据库 {db_name} 修改成功!")
        return True

    except Exception as e:
        print(f"❌ 数据库 {db_name} 修改失败: {e}")
        return False

# 主函数
if __name__ == "__main__":
    print("=== 更新日语等级表结构 ===")

    # 修改主数据库
    update_database_table('primary.db')

    # 修改备份数据库
    update_database_table('backup.db')

    print("\n=== 表结构修改完成 ===")
    print("现在可以允许新用户的日语等级为空，需要通过等级测试来确定。")
