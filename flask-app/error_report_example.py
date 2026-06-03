#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
错误上报服务示例和使用说明
"""

from app.services.error_report_service import (
    error_report_service,
    ErrorLevel,
    ErrorCategory,
    ErrorReportService,
    create_error_report_decorator
)


def example_basic_usage():
    """基本使用示例"""
    print("=" * 60)
    print("错误上报服务 - 基本使用")
    print("=" * 60)
    
    # 捕获异常
    try:
        result = 1 / 0
    except Exception as e:
        report = error_report_service.capture_error(
            e,
            level=ErrorLevel.ERROR,
            category=ErrorCategory.BUSINESS,
            context={'operation': 'division', 'dividend': 1, 'divisor': 0}
        )
        print(f"错误已捕获: {report.error_id}")
        print(f"错误类型: {report.error_type}")
        print(f"错误消息: {report.message}")
        print(f"文件位置: {report.file_path}:{report.line_number}")
        print()

    # 手动上报错误
    report = error_report_service.report_error(
        message="数据库连接失败",
        error_type="DatabaseConnectionError",
        level=ErrorLevel.CRITICAL,
        category=ErrorCategory.DATABASE,
        context={'host': 'localhost', 'port': 5432}
    )
    print(f"手动上报成功: {report.error_id}")
    print()


def example_list_and_search():
    """列表和搜索示例"""
    print("=" * 60)
    print("错误上报服务 - 列表和搜索")
    print("=" * 60)
    
    # 列出所有错误
    all_errors = error_report_service.list_errors(limit=5)
    print(f"最近5条错误: {len(all_errors)}")
    for err in all_errors:
        print(f"  - {err.error_id}: {err.message[:50]}...")
    print()
    
    # 按级别筛选
    errors = error_report_service.list_errors(level=ErrorLevel.ERROR)
    print(f"ERROR级别错误: {len(errors)}")
    print()
    
    # 按类别筛选
    db_errors = error_report_service.list_errors(category=ErrorCategory.DATABASE)
    print(f"DATABASE类别错误: {len(db_errors)}")
    print()
    
    # 搜索错误
    search_results = error_report_service.search_errors("database")
    print(f"搜索'database'结果: {len(search_results)}")
    print()


def example_statistics():
    """统计分析示例"""
    print("=" * 60)
    print("错误上报服务 - 统计分析")
    print("=" * 60)
    
    # 获取统计信息
    stats = error_report_service.get_statistics()
    print(f"总错误数: {stats.total_errors}")
    print(f"已解决: {stats.resolved_count}")
    print(f"未解决: {stats.unresolved_count}")
    print()
    
    # 按级别统计
    print("按级别统计:")
    for level, count in stats.errors_by_level.items():
        print(f"  {level}: {count}")
    print()
    
    # 按类别统计
    print("按类别统计:")
    for category, count in stats.errors_by_category.items():
        print(f"  {category}: {count}")
    print()
    
    # 获取最常见的错误
    top_errors = error_report_service.get_top_errors(limit=5)
    print("最常见的错误:")
    for i, err in enumerate(top_errors, 1):
        print(f"  {i}. [{err['count']}次] {err['error_type']}: {err['message']}")
    print()


def example_resolve_and_delete():
    """解决和删除示例"""
    print("=" * 60)
    print("错误上报服务 - 解决和删除")
    print("=" * 60)
    
    # 获取一个未解决的错误
    unresolved = error_report_service.list_errors(resolved=False, limit=1)
    if unresolved:
        error_id = unresolved[0].error_id
        print(f"解决错误: {error_id}")
        success = error_report_service.resolve_error(error_id, resolved_by="admin")
        print(f"解决结果: {'成功' if success else '失败'}")
    print()


def example_decorator_usage():
    """装饰器使用示例"""
    print("=" * 60)
    print("错误上报服务 - 装饰器使用")
    print("=" * 60)
    
    # 创建装饰器
    error_decorator = create_error_report_decorator(error_report_service)
    
    @error_decorator
    def risky_operation(data):
        """可能失败的操作"""
        result = data['value'] / data['divisor']
        return result
    
    # 调用可能失败的操作
    try:
        risky_operation({'value': 10, 'divisor': 0})
    except Exception as e:
        print(f"捕获到装饰器报告的错误: {e}")
    print()


def example_export():
    """导出示例"""
    print("=" * 60)
    print("错误上报服务 - 导出功能")
    print("=" * 60)
    
    # 导出为JSON
    json_data = error_report_service.export_errors(format_type="json")
    print(f"JSON导出长度: {len(json_data)} 字符")
    
    # 导出为CSV
    csv_data = error_report_service.export_errors(format_type="csv")
    print(f"CSV导出长度: {len(csv_data)} 字符")
    print()


def example_time_range():
    """时间范围查询示例"""
    print("=" * 60)
    print("错误上报服务 - 时间范围查询")
    print("=" * 60)
    
    import time
    
    # 获取最近1小时的错误
    one_hour_ago = time.time() - 3600
    recent_errors = error_report_service.get_errors_by_time_range(
        start_time=one_hour_ago,
        end_time=time.time()
    )
    print(f"最近1小时错误: {len(recent_errors)}")
    print()


def example_handler_registration():
    """错误处理器注册示例"""
    print("=" * 60)
    print("错误上报服务 - 错误处理器注册")
    print("=" * 60)
    
    def my_error_handler(error_report):
        """自定义错误处理器"""
        print(f"[处理器] 收到错误报告: {error_report.error_id}")
        print(f"[处理器] 错误级别: {error_report.level.value}")
        print(f"[处理器] 错误消息: {error_report.message}")
    
    # 注册处理器
    error_report_service.register_error_handler(my_error_handler)
    print("自定义错误处理器已注册")
    
    # 触发一个错误来测试处理器
    try:
        raise ValueError("测试错误")
    except Exception as e:
        error_report_service.capture_error(e)
    print()


def run_all_examples():
    """运行所有示例"""
    example_basic_usage()
    example_list_and_search()
    example_statistics()
    example_resolve_and_delete()
    example_decorator_usage()
    example_export()
    example_time_range()
    example_handler_registration()
    
    print("=" * 60)
    print("所有示例执行完成")
    print("=" * 60)


if __name__ == "__main__":
    run_all_examples()
