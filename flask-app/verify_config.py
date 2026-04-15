#!/usr/bin/env python3
"""
简单验证配置是否已保存到数据库
"""

import sqlite3
import json

print("验证配置是否已保存到数据库...")

try:
    # 连接数据库
    conn = sqlite3.connect('app.db')
    cursor = conn.cursor()
    
    # 检查system_config表是否存在
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='system_config'")
    if cursor.fetchone():
        print("✓ system_config表已存在")
        
        # 检查配置项数量
        cursor.execute("SELECT COUNT(*) FROM system_config")
        count = cursor.fetchone()[0]
        print(f"✓ 数据库中配置项数量: {count}")
        
        if count > 0:
            # 打印前5个配置项
            print("\n✓ 部分配置项示例:")
            cursor.execute("SELECT config_key, config_value FROM system_config LIMIT 5")
            for key, value in cursor.fetchall():
                try:
                    # 尝试解析为JSON
                    parsed = json.loads(value)
                    print(f"  {key}: {parsed} (JSON)")
                except:
                    # 普通值
                    print(f"  {key}: {value}")
            
            # 检查关键配置项
            key_to_check = 'SERVER_PORT'
            cursor.execute("SELECT config_value FROM system_config WHERE config_key = ?", (key_to_check,))
            result = cursor.fetchone()
            if result:
                print(f"\n✓ 关键配置项 {key_to_check} 已保存到数据库，值为: {result[0]}")
            
            print("\n✅ 配置已成功保存到数据库！")
        else:
            print("❌ 数据库中没有配置项")
    else:
        print("❌ system_config表不存在")
    
    # 关闭连接
    conn.close()
    
except Exception as e:
    print(f"❌ 验证失败: {