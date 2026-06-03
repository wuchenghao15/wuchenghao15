# -*- coding: utf-8 -*-
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
AI自动修复服务示例和使用说明
"""

from app.services.ai_auto_fix_service import (
    ai_auto_fix_service,
    AIAutoFixService,
    ErrorPattern,
    FixStrategy,
    ErrorAnalysis,
    FixSolution,
    BrainKnowledge
)
from app.services.error_report_service import (
    error_report_service,
    ErrorLevel,
    ErrorCategory
)


def example_analyze_and_fix():
    """分析和修复示例"""
    print("=" * 60)
    print("AI自动修复服务 - 分析和修复")
    print("=" * 60)
    
    test_errors = [
        ("导入错误", ModuleNotFoundError("No module named 'nonexistent_module'")),
        ("名称错误", NameError("name 'undefined_var' is not defined")),
        ("索引错误", IndexError("list index out of range")),
        ("键错误", KeyError("'missing_key'")),
    ]
    
    for name, error in test_errors:
        print(f"\n测试: {name}")
        print(f"错误: {error}")
        
        analysis, solution = ai_auto_fix_service.auto_fix_and_learn(error)
        
        print(f"分析ID: {analysis.error_id}")
        print(f"错误类型: {analysis.error_type}")
        print(f"错误模式: {analysis.pattern.value}")
        print(f"文件位置: {analysis.file_path}:{analysis.line_number}")
        print(f"代码片段: {analysis.code_snippet}")
        print(f"\n建议:")
        for i, suggestion in enumerate(analysis.suggestions, 1):
            print(f"  {i}. {suggestion}")
        print(f"\n修复方案:")
        print(f"  策略: {solution.strategy.value}")
        print(f"  置信度: {solution.confidence:.2f}")
        print(f"  解释: {solution.explanation}")
        print(f"  修复代码:")
        print(f"  {solution.fixed_code}")


def example_capture_and_auto_fix():
    """捕获错误并自动修复示例"""
    print("\n" + "=" * 60)
    print("错误上报服务 - 捕获并自动修复")
    print("=" * 60)
    
    try:
        result = 1 / 0
    except Exception as e:
        report = error_report_service.capture_error(
            e,
            level=ErrorLevel.ERROR,
            category=ErrorCategory.SYSTEM,
            context={'operation': 'division'}
        )
        
        print(f"错误报告: {report.error_id}")
        print(f"错误类型: {report.error_type}")
        print(f"错误消息: {report.message}")
        
        if 'ai_fix' in report.context:
            ai_fix = report.context['ai_fix']
            print(f"\nAI自动修复信息:")
            print(f"  已应用: {ai_fix['applied']}")
            print(f"  策略: {ai_fix['strategy']}")
            print(f"  置信度: {ai_fix['confidence']:.2f}")
            print(f"  解释: {ai_fix['explanation']}")


def example_brain_knowledge():
    """脑库知识示例"""
    print("\n" + "=" * 60)
    print("脑库知识 - 查看和管理")
    print("=" * 60)
    
    stats = ai_auto_fix_service.get_knowledge_base_stats()
    print(f"脑库统计:")
    print(f"  总知识数: {stats['total_knowledge']}")
    print(f"  平均成功率: {stats['avg_success_rate']:.2f}")
    print(f"  总使用次数: {stats['total_usage']}")
    print(f"\n模式分布:")
    for pattern, count in stats['patterns'].items():
        print(f"  {pattern}: {count}")
    
    all_knowledge = ai_auto_fix_service.get_all_knowledge()
    print(f"\n脑库知识列表 (共 {len(all_knowledge)} 条):")
    for kb in all_knowledge[:5]:
        print(f"  - {kb.knowledge_id}: {kb.error_type}")
        print(f"    解决方案: {kb.solution_approach}")
        print(f"    成功率: {kb.success_rate:.2f}, 使用次数: {kb.usage_count}")


def example_search_knowledge():
    """搜索脑库示例"""
    print("\n" + "=" * 60)
    print("脑库知识 - 搜索")
    print("=" * 60)
    
    search_results = ai_auto_fix_service.search_knowledge("import")
    print(f"搜索'import'结果: {len(search_results)} 条")
    for kb in search_results[:3]:
        print(f"  - {kb.knowledge_id}: {kb.root_cause[:50]}...")


def example_enable_disable_ai_fix():
    """启用/禁用AI自动修复示例"""
    print("\n" + "=" * 60)
    print("错误上报服务 - 启用/禁用AI自动修复")
    print("=" * 60)
    
    print("当前状态: AI自动修复已启用")
    error_report_service.enable_ai_auto_fix(False)
    print("已禁用AI自动修复")
    
    try:
        result = undefined_variable / 10
    except Exception as e:
        report = error_report_service.capture_error(e)
        has_ai_fix = 'ai_fix' in report.context
        print(f"错误 {report.error_id} 的AI修复状态: {has_ai_fix}")
    
    error_report_service.enable_ai_auto_fix(True)
    print("已重新启用AI自动修复")


def example_update_knowledge():
    """更新脑库知识示例"""
    print("\n" + "=" * 60)
    print("脑库知识 - 更新")
    print("=" * 60)
    
    all_knowledge = ai_auto_fix_service.get_all_knowledge()
    if all_knowledge:
        kb_id = all_knowledge[0].knowledge_id
        print(f"更新知识: {kb_id}")
        
        success = ai_auto_fix_service.update_knowledge(
            kb_id,
            {'success_rate': 0.95, 'tags': ['updated', 'test']}
        )
        print(f"更新结果: {'成功' if success else '失败'}")


def example_fix_unknown_error():
    """修复未知错误示例"""
    print("\n" + "=" * 60)
    print("AI自动修复服务 - 未知错误处理")
    print("=" * 60)
    
    custom_error = ValueError("Some custom error occurred")
    analysis, solution = ai_auto_fix_service.auto_fix_and_learn(custom_error)
    
    print(f"错误: {custom_error}")
    print(f"分析结果:")
    print(f"  错误模式: {analysis.pattern.value}")
    print(f"  建议: {analysis.suggestions}")
    print(f"修复方案:")
    print(f"  策略: {solution.strategy.value}")
    print(f"  置信度: {solution.confidence:.2f}")
    print(f"  修复代码: {solution.fixed_code}")


def run_all_examples():
    """运行所有示例"""
    example_analyze_and_fix()
    example_capture_and_auto_fix()
    example_brain_knowledge()
    example_search_knowledge()
    example_enable_disable_ai_fix()
    example_update_knowledge()
    example_fix_unknown_error()
    
    print("\n" + "=" * 60)
    print("所有示例执行完成")
    print("=" * 60)


if __name__ == "__main__":
    run_all_examples()
