#!/usr/bin/env python3
"""
验证配置是否已成功上传到数据库

import sqlite3
import os
# JSON import removed - using database
# 直接指定数据库路径
DB_PATH = os.path.join(os.path.dirname(__file__), 'instance', 'mtscos_ai.db')


def verify_config():
    """验证数据库中的配置"""
    print(f"连接数据库: {DB_PATH}")
    print("=" * 60)

    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()

        # 1. 查询所有配置
        cursor.execute("SELECT config_key, config_value, config_type FROM system_config ORDER BY config_key")
        configs = cursor.fetchall()

        print(f"✅ 找到 {len(configs)} 个配置项")

        # 2. 打印部分配置
        print(f"\n📋 配置列表:")
        for config_key, config_value, config_type in configs[:10]:
            # 对于长值，只显示前50个字符
            display_value = config_value
            if len(config_value) > 50:
                display_value = config_value[:50] + "..."
            print(f"   {config_key:25} ({config_type:8}): {display_value}")

        if len(configs) > 10:
            print(f"   ... 还有 {len(configs) - 10} 个配置项")

        # 3. 验证关键配置是否存在
        key_configs = ['APP_NAME', 'PORT', 'SECRET_KEY', 'AI_CONFIG', 'SECURITY_CONFIG']
        print(f"\n🔍 关键配置验证:")

        for key in key_configs:
            cursor.execute("SELECT id FROM system_config WHERE config_key = ?", (key,))
            if cursor.fetchone():
                print(f"   ✅ {key} 存在")
            else:
                print(f"   ❌ {key} 不存在")

        conn.close()

        print(f"\n🎉 配置验证完成！")
        return True

    except Exception as e:
        print(f"❌ 验证失败: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    verify_config()
