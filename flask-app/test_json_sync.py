#!/usr/bin/env python3
"""
测试JSON与数据库同步服务
"""

import os
import json
import time
import sqlite3

# 测试JSON文件路径
TEST_JSON_FILE = 'test_sync.json'
DB_PATH = 'app.db'

def test_json_sync():
    """测试JSON与数据库同步"""
    print("=== 测试JSON与数据库同步服务 ===")
    
    # 1. 创建测试JSON文件
    test_data = {
        "test_id": 1,
        "test_name": "JSON同步测试",
        "test_content": "这是一个JSON同步测试文件",
        "test_date": time.strftime("%Y-%m-%d %H:%M:%S"),
        "test_array": [1, 2, 3, 4, 5],
        "test_object": {
            "key1": "value1",
            "key2": "value2"
        }
    }
    
    print(f"1. 创建测试JSON文件: {TEST_JSON_FILE}")
    with open(TEST_JSON_FILE, 'w', encoding='utf-8') as f:
        json.dump(test_data, f, ensure_ascii=False, indent=2)
    
    # 2. 等待同步服务处理
    print("2. 等待同步服务处理...")
    time.sleep(10)  # 等待10秒，确保同步服务有足够时间处理
    
    # 3. 检查数据库中是否有对应的记录
    print("3. 检查数据库中是否有对应的记录...")
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # 查询json_files表
    cursor.execute('SELECT * FROM json_files WHERE file_name = ?', (TEST_JSON_FILE,))
    record = cursor.fetchone()
    
    if record:
        print(f"   ✓ 数据库中找到记录，ID: {record[0]}")
        print(f"   ✓ 文件路径: {record[1]}")
        print(f"   ✓ 文件名: {record[2]}")
        print(f"   ✓ 上传时间: {record[4]}")
        print(f"   ✓ 文件大小: {record[5]} 字节")
        print(f"   ✓ 文件哈希: {record[6]}")
        
        # 4. 验证JSON内容
        print("4. 验证JSON内容...")
        db_content = json.loads(record[3])
        if db_content == test_data:
            print("   ✓ JSON内容与数据库中存储的一致")
        else:
            print("   ✗ JSON内容与数据库中存储的不一致")
            print(f"   原数据: {test_data}")
            print(f"   数据库数据: {db_content}")
        
        # 5. 修改JSON文件，测试同步更新
        print("5. 修改JSON文件，测试同步更新...")
        test_data['test_content'] = "这是修改后的JSON同步测试文件"
        test_data['test_date'] = time.strftime("%Y-%m-%d %H:%M:%S")
        test_data['new_field'] = "新增字段"
        
        with open(TEST_JSON_FILE, 'w', encoding='utf-8') as f:
            json.dump(test_data, f, ensure_ascii=False, indent=2)
        
        # 等待同步更新
        time.sleep(10)
        
        # 检查更新后的记录
        cursor.execute('SELECT * FROM json_files WHERE file_name = ?', (TEST_JSON_FILE,))
        updated_record = cursor.fetchone()
        
        if updated_record:
            print(f"   ✓ 数据库记录已更新，ID: {updated_record[0]}")
            updated_content = json.loads(updated_record[3])
            if updated_content['test_content'] == "这是修改后的JSON同步测试文件":
                print("   ✓ JSON内容已成功更新")
            else:
                print("   ✗ JSON内容更新失败")
        else:
            print("   ✗ 未找到更新后的记录")
        
    else:
        print("   ✗ 数据库中未找到对应的记录")
    
    # 关闭数据库连接
    conn.close()
    
    # 6. 清理测试文件
    print(f"6. 清理测试文件: {TEST_JSON_FILE}")
    if os.path.exists(TEST_JSON_FILE):
        os.remove(TEST_JSON_FILE)
    
    # 等待同步服务处理删除操作
    time.sleep(10)
    
    # 7. 检查数据库中是否已删除记录
    print("7. 检查数据库中是否已删除记录...")
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM json_files WHERE file_name = ?', (TEST_JSON_FILE,))
    deleted_record = cursor.fetchone()
    conn.close()
    
    if not deleted_record:
        print("   ✓ 数据库记录已成功删除")
    else:
        print("   ✗ 数据库记录未删除")
    
    print("\n=== JSON同步测试完成 ===")

if __name__ == "__main__":
    test_json_sync()
