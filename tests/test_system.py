#!/usr/bin/env python3
"""
MTSCOS系统全面测试脚本
测试统一题库、动态题目引擎、数据库连接等功能模块
"""

import os
import sys
import json
import time
import traceback
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

TEST_RESULTS = []


def test_log(test_name, status, message="", error=None):
    """记录测试结果"""
    result = {
        'test_name': test_name,
        'status': status,
        'message': message,
        'error': str(error) if error else None,
        'timestamp': datetime.now().isoformat()
    }
    TEST_RESULTS.append(result)
    
    status_icon = '✅' if status == 'PASS' else '❌' if status == 'FAIL' else '⚠️'
    print(f"{status_icon} {test_name}: {message}")
    if error:
        print(f"   错误: {error}")


def test_unified_question_bank():
    """测试统一题库系统"""
    print("\n" + "="*60)
    print("测试统一题库系统")
    print("="*60)
    
    try:
        from ai_engines.unified_question_bank import unified_question_bank, SUBJECTS, QUESTION_TYPES
        
        # 测试1: 获取题库统计
        test_log("获取题库统计", "RUNNING", "正在获取统计数据...")
        stats = unified_question_bank.get_statistics()
        if stats.get('success'):
            test_log("获取题库统计", "PASS", f"总题目数: {stats['data']['total_questions']}")
        else:
            test_log("获取题库统计", "FAIL", "获取统计失败")
        
        # 测试2: 获取题目列表
        test_log("获取题目列表", "RUNNING", "正在获取题目列表...")
        questions = unified_question_bank.get_questions({'page': 1, 'page_size': 5})
        if questions.get('success'):
            test_log("获取题目列表", "PASS", f"获取到{len(questions['data'])}道题目")
        else:
            test_log("获取题目列表", "FAIL", "获取题目列表失败")
        
        # 测试3: 添加题目
        test_log("添加题目", "RUNNING", "正在添加测试题目...")
        test_question = {
            'subject': 'math',
            'question_type': 'single_choice',
            'difficulty': 'easy',
            'content': '测试题目: 2 + 2 = ?',
            'options': ['A. 3', 'B. 4', 'C. 5', 'D. 6'],
            'correct_answer': 'B',
            'analysis': '测试题目分析',
            'tags': ['测试', '基础题'],
            'knowledge_points': ['基本运算'],
            'grade': '小学'
        }
        result = unified_question_bank.add_question(test_question)
        if result.get('success'):
            test_log("添加题目", "PASS", f"题目UUID: {result['question_uuid']}")
            # 测试4: 获取单个题目
            test_log("获取单个题目", "RUNNING", "正在获取单个题目...")
            single_q = unified_question_bank.get_question_by_uuid(result['question_uuid'])
            if single_q.get('success'):
                test_log("获取单个题目", "PASS", f"获取成功: {single_q['data']['content'][:30]}...")
            else:
                test_log("获取单个题目", "FAIL", "获取单个题目失败")
            
            # 测试5: 更新题目
            test_log("更新题目", "RUNNING", "正在更新题目...")
            update_result = unified_question_bank.update_question(result['question_uuid'], {'content': '更新后的测试题目: 2 + 2 = ?'})
            if update_result.get('success'):
                test_log("更新题目", "PASS", "更新成功")
            else:
                test_log("更新题目", "FAIL", "更新失败")
            
            # 测试6: 删除题目
            test_log("删除题目", "RUNNING", "正在删除题目...")
            delete_result = unified_question_bank.delete_question(result['question_uuid'])
            if delete_result.get('success'):
                test_log("删除题目", "PASS", "删除成功")
            else:
                test_log("删除题目", "FAIL", "删除失败")
        else:
            test_log("添加题目", "FAIL", "添加题目失败")
        
        # 测试7: 验证科目配置
        test_log("验证科目配置", "RUNNING", "正在验证科目配置...")
        if len(SUBJECTS) == 10:
            test_log("验证科目配置", "PASS", f"科目数量: {len(SUBJECTS)}")
        else:
            test_log("验证科目配置", "FAIL", f"科目数量不正确: {len(SUBJECTS)}")
        
        # 测试8: 验证题型配置
        test_log("验证题型配置", "RUNNING", "正在验证题型配置...")
        if len(QUESTION_TYPES) >= 10:
            test_log("验证题型配置", "PASS", f"题型数量: {len(QUESTION_TYPES)}")
        else:
            test_log("验证题型配置", "FAIL", f"题型数量不足: {len(QUESTION_TYPES)}")
    
    except Exception as e:
        test_log("统一题库测试", "FAIL", "测试过程中发生异常", e)
        traceback.print_exc()


def test_dynamic_question_engine():
    """测试动态题目生成引擎"""
    print("\n" + "="*60)
    print("测试动态题目生成引擎")
    print("="*60)
    
    try:
        from ai_engines.dynamic_question_engine import dynamic_question_engine
        
        # 测试1: 获取动态生成配置
        test_log("获取动态生成配置", "RUNNING", "正在获取配置...")
        config = dynamic_question_engine.get_config('max_daily_generation')
        if config:
            test_log("获取动态生成配置", "PASS", f"每日最大生成量: {config}")
        else:
            test_log("获取动态生成配置", "FAIL", "获取配置失败")
        
        # 测试2: 动态生成单道题目
        test_log("动态生成单道题目", "RUNNING", "正在生成题目...")
        question = dynamic_question_engine.generate_question('math', 'single_choice', 'easy')
        if question:
            test_log("动态生成单道题目", "PASS", f"生成成功: {question['content'][:30]}...")
        else:
            test_log("动态生成单道题目", "FAIL", "生成失败")
        
        # 测试3: 批量生成题目
        test_log("批量生成题目", "RUNNING", "正在批量生成5道题目...")
        result = dynamic_question_engine.batch_generate(count=5)
        if result.get('success'):
            test_log("批量生成题目", "PASS", f"成功生成{result['success_count']}道题目")
        else:
            test_log("批量生成题目", "FAIL", "批量生成失败")
        
        # 测试4: 获取动态统计
        test_log("获取动态统计", "RUNNING", "正在获取统计数据...")
        stats = dynamic_question_engine.get_dynamic_stats()
        if stats.get('success'):
            test_log("获取动态统计", "PASS", f"AI生成总量: {stats['data']['ai_generated_total']}")
        else:
            test_log("获取动态统计", "FAIL", "获取统计失败")
        
        # 测试5: 获取爬取统计
        test_log("获取爬取统计", "RUNNING", "正在获取爬取统计...")
        crawl_stats = dynamic_question_engine.get_crawled_count()
        if crawl_stats.get('success'):
            test_log("获取爬取统计", "PASS", f"总爬取: {crawl_stats['data']['total_crawled']}")
        else:
            test_log("获取爬取统计", "FAIL", "获取爬取统计失败")
    
    except Exception as e:
        test_log("动态题目引擎测试", "FAIL", "测试过程中发生异常", e)
        traceback.print_exc()


def test_database_connection():
    """测试数据库连接"""
    print("\n" + "="*60)
    print("测试数据库连接")
    print("="*60)
    
    try:
        from ai_engines.unified_question_bank import get_db_path, execute_sql, fetch_one
        
        # 测试1: 数据库路径
        test_log("数据库路径", "RUNNING", "正在获取数据库路径...")
        db_path = get_db_path()
        if os.path.exists(db_path):
            test_log("数据库路径", "PASS", f"路径存在: {db_path}")
        else:
            test_log("数据库路径", "FAIL", f"路径不存在: {db_path}")
        
        # 测试2: SQL执行
        test_log("SQL执行", "RUNNING", "正在执行测试SQL...")
        execute_sql("SELECT 1")
        test_log("SQL执行", "PASS", "SQL执行成功")
        
        # 测试3: 表存在性检查
        test_log("表存在性检查", "RUNNING", "正在检查表是否存在...")
        tables = ['unified_questions', 'dynamic_generation_config', 'generation_history', 'crawled_questions']
        for table in tables:
            result = fetch_one(f"SELECT name FROM sqlite_master WHERE type='table' AND name='{table}'")
            if result:
                test_log(f"表 {table}", "PASS", "表存在")
            else:
                test_log(f"表 {table}", "FAIL", "表不存在")
    
    except Exception as e:
        test_log("数据库连接测试", "FAIL", "测试过程中发生异常", e)
        traceback.print_exc()


def test_api_imports():
    """测试API模块导入"""
    print("\n" + "="*60)
    print("测试API模块导入")
    print("="*60)
    
    api_modules = [
        ('统一题库API', 'app.api.unified_question_api'),
        ('动态题目API', 'app.api.dynamic_question_api'),
        ('语文听力API', 'app.api.chinese_listening_api'),
    ]
    
    for name, module_path in api_modules:
        test_log(f"导入{name}", "RUNNING", f"正在导入 {module_path}...")
        try:
            __import__(module_path)
            test_log(f"导入{name}", "PASS", "导入成功")
        except Exception as e:
            test_log(f"导入{name}", "FAIL", f"导入失败: {e}")


def test_ai_extension():
    """测试AI延展功能"""
    print("\n" + "="*60)
    print("测试AI延展功能")
    print("="*60)
    
    try:
        from ai_engines.unified_question_bank import unified_question_bank
        
        # 获取一道现有题目
        questions = unified_question_bank.get_questions({'page': 1, 'page_size': 1})
        if questions.get('success') and questions['data']:
            source_uuid = questions['data'][0]['question_uuid']
            test_log("AI延展题目", "RUNNING", f"正在延展题目: {source_uuid}...")
            result = unified_question_bank.ai_extend_question(source_uuid, count=3)
            if result.get('success'):
                test_log("AI延展题目", "PASS", f"成功延展{result['generated_count']}道题目")
            else:
                test_log("AI延展题目", "FAIL", "延展失败")
        else:
            test_log("AI延展题目", "SKIP", "没有可用的源题目")
    
    except Exception as e:
        test_log("AI延展测试", "FAIL", "测试过程中发生异常", e)
        traceback.print_exc()


def test_sync_functionality():
    """测试题库同步功能"""
    print("\n" + "="*60)
    print("测试题库同步功能")
    print("="*60)
    
    try:
        from ai_engines.unified_question_bank import unified_question_bank
        
        test_log("题库同步", "RUNNING", "正在测试同步功能...")
        result = unified_question_bank.sync_with_external('mock', 'math')
        if result.get('success'):
            test_log("题库同步", "PASS", f"同步完成，新增{result['success_count']}道题目")
        else:
            test_log("题库同步", "FAIL", f"同步失败: {result.get('error')}")
    
    except Exception as e:
        test_log("题库同步测试", "FAIL", "测试过程中发生异常", e)
        traceback.print_exc()


def test_blueprint_registration():
    """测试蓝图注册"""
    print("\n" + "="*60)
    print("测试蓝图注册")
    print("="*60)
    
    try:
        import inspect
        from app import _register_blueprints
        
        source = inspect.getsource(_register_blueprints)
        
        expected_blueprints = [
            'unified_question_api',
            'dynamic_question_api',
            'chinese_listening_api'
        ]
        
        for blueprint in expected_blueprints:
            if blueprint in source:
                test_log(f"蓝图 {blueprint}", "PASS", "已注册")
            else:
                test_log(f"蓝图 {blueprint}", "FAIL", "未注册")
    
    except Exception as e:
        test_log("蓝图注册测试", "FAIL", "测试过程中发生异常", e)
        traceback.print_exc()


def test_version_manager():
    """测试版本管理器"""
    print("\n" + "="*60)
    print("测试版本管理器")
    print("="*60)
    
    try:
        from core.services.version_manager import CURRENT_VERSION, VERSION_DATA
        
        test_log("当前版本", "RUNNING", "正在检查当前版本...")
        if CURRENT_VERSION == '17.20.0':
            test_log("当前版本", "PASS", f"版本号正确: {CURRENT_VERSION}")
        else:
            test_log("当前版本", "FAIL", f"版本号不正确: {CURRENT_VERSION}")
        
        test_log("版本数据", "RUNNING", "正在检查版本数据...")
        if '17.20.0' in VERSION_DATA:
            version_info = VERSION_DATA['17.20.0']
            test_log("版本数据", "PASS", f"版本名称: {version_info['codename']}")
        else:
            test_log("版本数据", "FAIL", "版本数据中没有17.20.0")
    
    except Exception as e:
        test_log("版本管理器测试", "FAIL", "测试过程中发生异常", e)
        traceback.print_exc()


def generate_test_report():
    """生成测试报告"""
    print("\n" + "="*60)
    print("测试报告")
    print("="*60)
    
    passed = sum(1 for r in TEST_RESULTS if r['status'] == 'PASS')
    failed = sum(1 for r in TEST_RESULTS if r['status'] == 'FAIL')
    skipped = sum(1 for r in TEST_RESULTS if r['status'] == 'SKIP')
    
    print(f"\n测试总数: {len(TEST_RESULTS)}")
    print(f"✅ 通过: {passed}")
    print(f"❌ 失败: {failed}")
    print(f"⚠️ 跳过: {skipped}")
    print(f"通过率: {passed/len(TEST_RESULTS)*100:.1f}%")
    
    if failed > 0:
        print("\n失败的测试:")
        for r in TEST_RESULTS:
            if r['status'] == 'FAIL':
                print(f"  - {r['test_name']}: {r['error']}")
    
    # 保存测试报告
    report_path = f"test_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(report_path, 'w', encoding='utf-8') as f:
        json.dump(TEST_RESULTS, f, ensure_ascii=False, indent=2)
    
    print(f"\n测试报告已保存到: {report_path}")
    
    return passed, failed, skipped


def main():
    """主测试函数"""
    print("="*60)
    print("MTSCOS系统全面测试")
    print("="*60)
    print(f"测试时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*60)
    
    start_time = time.time()
    
    test_database_connection()
    test_unified_question_bank()
    test_dynamic_question_engine()
    test_api_imports()
    test_ai_extension()
    test_sync_functionality()
    test_blueprint_registration()
    test_version_manager()
    
    end_time = time.time()
    
    passed, failed, skipped = generate_test_report()
    
    print(f"\n测试耗时: {end_time - start_time:.2f}秒")
    
    if failed > 0:
        sys.exit(1)


if __name__ == '__main__':
    main()