# -*- coding: utf-8 -*-
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
JSON数据上传服务示例和使用说明
"""

import json
import os
from app.services.json_data_upload_service import (
    json_data_upload_service,
    UploadMode,
    UploadResult
)


def example_create_table_and_upload():
    """创建表并上传数据示例"""
    print("=" * 60)
    print("JSON数据上传 - 创建表并上传")
    print("=" * 60)
    
    # 准备测试数据
    test_data = [
        {'id': 1, 'name': '张三', 'email': 'zhangsan@example.com', 'age': 25},
        {'id': 2, 'name': '李四', 'email': 'lisi@example.com', 'age': 30},
        {'id': 3, 'name': '王五', 'email': 'wangwu@example.com', 'age': 35}
    ]
    
    # 创建表
    print("创建测试表...")
    success = json_data_upload_service.create_table_from_json(
        table_name='test_users',
        json_data=test_data,
        primary_key='id'
    )
    print(f"表创建结果: {'成功' if success else '失败'}")
    
    # 上传数据(INSERT模式)
    print("\n上传数据(INSERT模式)...")
    result = json_data_upload_service.upload_from_string(
        json_string=json.dumps(test_data),
        table_name='test_users',
        mode=UploadMode.INSERT
    )
    print(f"上传结果: {result.success}")
    print(f"消息: {result.message}")
    print(f"总数: {result.total_records}, 成功: {result.success_count}, 失败: {result.failed_count}")
    
    # 尝试再次上传(测试UPSERT模式)
    print("\n上传更新数据(UPSERT模式)...")
    update_data = [
        {'id': 2, 'name': '李四更新', 'email': 'lisi_updated@example.com', 'age': 31},
        {'id': 4, 'name': '赵六', 'email': 'zhaoliu@example.com', 'age': 28}
    ]
    result = json_data_upload_service.upload_from_string(
        json_string=json.dumps(update_data),
        table_name='test_users',
        mode=UploadMode.UPSERT,
        primary_key='id'
    )
    print(f"上传结果: {result.success}")
    print(f"消息: {result.message}")


def example_upload_from_file():
    """从文件上传示例"""
    print("\n" + "=" * 60)
    print("JSON数据上传 - 从文件上传")
    print("=" * 60)
    
    # 创建临时JSON文件
    temp_file = '/tmp/test_data.json'
    test_data = [
        {'product_id': 'P001', 'name': '笔记本电脑', 'price': 5999.0, 'stock': 100},
        {'product_id': 'P002', 'name': '智能手机', 'price': 3999.0, 'stock': 200}
    ]
    
    with open(temp_file, 'w', encoding='utf-8') as f:
        json.dump(test_data, f, ensure_ascii=False, indent=2)
    
    # 创建表
    success = json_data_upload_service.create_table_from_json(
        table_name='products',
        json_data=test_data,
        primary_key='product_id'
    )
    print(f"表创建结果: {'成功' if success else '失败'}")
    
    # 从文件上传
    print("\n从文件上传数据...")
    result = json_data_upload_service.upload_from_file(
        file_path=temp_file,
        table_name='products',
        mode=UploadMode.INSERT
    )
    print(f"上传结果: {result.success}")
    print(f"消息: {result.message}")
    
    # 清理临时文件
    os.remove(temp_file)


def example_export_table():
    """导出表数据示例"""
    print("\n" + "=" * 60)
    print("JSON数据上传 - 导出表数据")
    print("=" * 60)
    
    # 导出表
    print("导出test_users表...")
    result = json_data_upload_service.export_table_to_json('test_users')
    print(f"导出成功,共 {result.get('count', 0)} 条记录")
    
    # 打印部分数据
    if 'data' in result:
        print("\n数据预览:")
        for record in result['data'][:3]:
            print(f"  {record}")


def example_task_management():
    """任务管理示例"""
    print("\n" + "=" * 60)
    print("JSON数据上传 - 任务管理")
    print("=" * 60)
    
    # 获取任务列表
    tasks = json_data_upload_service.list_tasks(limit=5)
    print(f"最近任务数: {len(tasks)}")
    
    # 获取上传摘要
    summary = json_data_upload_service.get_upload_summary()
    print("\n上传摘要:")
    print(f"  总任务数: {summary['total_tasks']}")
    print(f"  已完成: {summary['completed_tasks']}")
    print(f"  失败: {summary['failed_tasks']}")
    print(f"  运行中: {summary['running_tasks']}")
    print(f"  总记录数: {summary['total_records']}")
    print(f"  成功记录: {summary['success_records']}")
    print(f"  失败记录: {summary['failed_records']}")


def example_upload_from_string():
    """从字符串上传示例"""
    print("\n" + "=" * 60)
    print("JSON数据上传 - 从字符串上传")
    print("=" * 60)
    
    json_string = '''{
        "data": [
            {"order_id": "ORD001", "customer_id": "CUS001", "amount": 100.0, "status": "pending"},
            {"order_id": "ORD002", "customer_id": "CUS002", "amount": 200.0, "status": "completed"}
        ]
    }'''
    
    # 创建表
    data = json.loads(json_string)
    success = json_data_upload_service.create_table_from_json(
        table_name='orders',
        json_data=data,
        primary_key='order_id'
    )
    print(f"表创建结果: {'成功' if success else '失败'}")
    
    # 上传数据
    result = json_data_upload_service.upload_from_string(
        json_string=json_string,
        table_name='orders',
        mode=UploadMode.INSERT
    )
    print(f"\n上传结果: {result.success}")
    print(f"消息: {result.message}")


def run_all_examples():
    """运行所有示例"""
    example_create_table_and_upload()
    example_upload_from_file()
    example_export_table()
    example_task_management()
    example_upload_from_string()
    
    print("\n" + "=" * 60)
    print("所有示例执行完成")
    print("=" * 60)


if __name__ == "__main__":
    run_all_examples()
