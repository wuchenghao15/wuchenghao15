#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
数据库版本初始化和记录脚本
自动记录数据库版本历史和初始配置
"""

import sys
import os
import json
from datetime import datetime

# 添加项目根目录到路径
script_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(script_dir)  # scripts -> flask-app
sys.path.insert(0, project_root)
sys.path.insert(0, os.path.join(project_root, 'app'))

try:
    from app.models.database_version_manager import db_version_manager
except ImportError:
    # 备用导入方式
    import importlib.util
    db_manager_path = os.path.join(project_root, 'app', 'models', 'database_version_manager.py')
    spec = importlib.util.spec_from_file_location('database_version_manager', db_manager_path)
    db_version_module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(db_version_module)
    db_version_manager = db_version_module.db_version_manager


def initialize_database_versions():
    """初始化数据库版本记录"""
    
    # 预定义的版本历史
    versions = [
        {
            'version': '1.0.0',
            'description': 'MTSCOS 9年教育系统初始版本',
            'changes': [
                '创建用户管理系统（User, UserProfile）',
                '创建题库管理系统（Question, QuestionBank）',
                '创建考试系统（Exam, ExamRecord）',
                '创建学习系统（LearningSystem, Course, Progress）',
                '创建教学内容管理系统（TeachingSyllabus, TeachingPreparation, TeachingPlan）',
                '创建系统配置管理（SystemConfig, ConfigCategory）',
                '创建日志系统（SystemLog, OperationLog）',
                '创建安全监控（SecurityEvent, AccessLog）',
                '创建本地存储（LocalStorage, StorageCategory）',
                '创建规则引擎（Rule, RuleCategory）'
            ]
        },
        {
            'version': '1.1.0',
            'description': '数据库性能优化版本',
            'changes': [
                '添加数据库索引优化',
                '优化查询性能',
                '添加表关系优化',
                '改进数据完整性约束',
                '添加索引使用统计'
            ]
        },
        {
            'version': '1.2.0',
            'description': '通讯协议集成版本',
            'changes': [
                '集成HTTP协议支持',
                '集成WebSocket实时通信',
                '集成MQTT消息队列',
                '集成gRPC远程调用',
                '添加协议管理器',
                '添加消息路由系统'
            ]
        },
        {
            'version': '1.3.0',
            'description': '安全增强版本',
            'changes': [
                '添加私有数据交互协议',
                '实现端到端加密',
                '添加RSA签名验证',
                '实现数据压缩传输',
                '添加安全通道封装'
            ]
        },
        {
            'version': '1.4.0',
            'description': '版本管理系统',
            'changes': [
                '创建数据库版本管理器',
                '添加版本历史记录',
                '实现变更追踪',
                '添加数据库优化功能',
                '创建索引分析系统',
                '添加版本报告生成'
            ]
        }
    ]
    
    print("=" * 60)
    print("MTSCOS 数据库版本初始化")
    print("=" * 60)
    print()
    
    # 记录所有版本
    for version_info in versions:
        version = version_info['version']
        description = version_info['description']
        changes = version_info['changes']
        
        # 检查版本是否已存在
        existing = db_version_manager.get_version_info(version)
        if existing:
            print(f"版本 {version} 已存在，跳过...")
            continue
        
        # 创建版本记录
        success = db_version_manager.create_version(
            version=version,
            description=description,
            changes=changes,
            created_by='system'
        )
        
        if success:
            print(f"✓ 版本 {version} 记录成功")
        else:
            print(f"✗ 版本 {version} 记录失败")
    
    print()
    print("=" * 60)
    print("数据库版本初始化完成")
    print("=" * 60)


def generate_database_report():
    """生成数据库报告"""
    print()
    print("=" * 60)
    print("数据库统计报告")
    print("=" * 60)
    print()
    
    stats = db_version_manager.get_database_stats()
    
    print(f"总表数量: {stats['total_tables']}")
    print(f"总索引数量: {stats['total_indexes']}")
    print(f"数据库大小: {stats['total_size_mb']} MB")
    print(f"版本数量: {stats['version_count']}")
    
    print()
    print("表统计:")
    print("-" * 60)
    for table_stat in stats['table_stats']:
        print(f"  - {table_stat['table_name']}: {table_stat['row_count']} 行, {table_stat['column_count']} 列")
    
    print()
    print("版本历史:")
    print("-" * 60)
    versions = db_version_manager.get_all_versions()
    for version in versions:
        print(f"  v{version['version']} - {version['description']}")
        print(f"    创建时间: {version['created_at']}")
        if version.get('changes'):
            changes = json.loads(version['changes'])
            for change in changes[:3]:  # 只显示前3个变更
                print(f"    • {change}")
            if len(changes) > 3:
                print(f"    ... 还有 {len(changes) - 3} 项变更")
        print()


def optimize_database():
    """执行数据库优化"""
    print()
    print("=" * 60)
    print("数据库优化")
    print("=" * 60)
    print()
    
    # VACUUM优化
    print("执行 VACUUM 优化...")
    result = db_version_manager.optimize_database('vacuum')
    if result['success']:
        print(f"  ✓ 优化成功，节省空间: {result['space_saved']} bytes")
    else:
        print(f"  ✗ 优化失败: {result.get('error', '未知错误')}")
    
    print()
    
    # ANALYZE优化
    print("执行 ANALYZE 优化...")
    result = db_version_manager.optimize_database('analyze')
    if result['success']:
        print(f"  ✓ 分析完成")
    else:
        print(f"  ✗ 分析失败: {result.get('error', '未知错误')}")
    
    print()
    
    # REINDEX优化
    print("执行 REINDEX 优化...")
    result = db_version_manager.optimize_database('reindex')
    if result['success']:
        print(f"  ✓ 索引重建完成")
        if result['tables_affected']:
            print(f"  受影响的索引: {', '.join(result['tables_affected'][:5])}")
            if len(result['tables_affected']) > 5:
                print(f"  ... 还有 {len(result['tables_affected']) - 5} 个索引")
    else:
        print(f"  ✗ 索引重建失败: {result.get('error', '未知错误')}")
    
    print()


def analyze_indexes():
    """分析数据库索引"""
    print()
    print("=" * 60)
    print("索引分析")
    print("=" * 60)
    print()
    
    indexes = db_version_manager.analyze_indexes()
    
    if not indexes:
        print("未发现用户索引")
        return
    
    print(f"发现 {len(indexes)} 个索引:")
    print("-" * 60)
    
    for idx in indexes:
        unique_str = "唯一" if idx['is_unique'] else "非唯一"
        print(f"  • {idx['index_name']}")
        print(f"    表: {idx['table_name']}")
        print(f"    类型: {unique_str}")
        print()


def export_version_history():
    """导出版本历史"""
    print()
    print("=" * 60)
    print("导出版本历史")
    print("=" * 60)
    print()
    
    # 确定导出路径
    base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    export_path = os.path.join(base_dir, 'database_version_report.json')
    
    success = db_version_manager.export_version_history(export_path, 'json')
    
    if success:
        print(f"✓ 版本历史已导出到: {export_path}")
    else:
        print(f"✗ 导出失败")


def main():
    """主函数"""
    print()
    print("=" * 60)
    print("MTSCOS 数据库版本管理系统")
    print("=" * 60)
    print()
    
    print("1. 初始化数据库版本记录")
    print("2. 生成数据库统计报告")
    print("3. 执行数据库优化")
    print("4. 分析数据库索引")
    print("5. 导出版本历史")
    print("6. 执行所有操作")
    print()
    
    choice = input("请选择操作 (1-6): ").strip()
    
    if choice == '1':
        initialize_database_versions()
    elif choice == '2':
        generate_database_report()
    elif choice == '3':
        optimize_database()
    elif choice == '4':
        analyze_indexes()
    elif choice == '5':
        export_version_history()
    elif choice == '6':
        initialize_database_versions()
        generate_database_report()
        optimize_database()
        analyze_indexes()
        export_version_history()
    else:
        print("无效的选择")
    
    print()
    print("操作完成!")


if __name__ == '__main__':
    main()
