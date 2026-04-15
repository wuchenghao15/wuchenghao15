#!/usr/bin/env python3
"""
系统测试脚本
"""

import time
import logging
import sys
from app.utils.db import db_manager
from app.utils.cache import cache_manager
from app.utils.performance import performance_monitor
from app.ai.enhanced_ai_engine import enhanced_ai_engine
from app.models.enhanced_exam import enhanced_exam_system
from app.services.system_logic_manager import system_logic_manager
from app.services.version_manager import version_manager
from app.utils.logging import logger

class SystemTester:
    """系统测试器"""
    
    def __init__(self):
        """初始化系统测试器"""
        self.test_results = []
        self.start_time = None
        self.end_time = None
        logger.info("系统测试器初始化完成")
    
    def start_test(self):
        """
        开始测试
        """
        self.start_time = time.time()
        self.test_results = []
        logger.info("开始系统测试")
    
    def end_test(self):
        """
        结束测试
        """
        self.end_time = time.time()
        self._print_test_results()
        logger.info("系统测试完成")
    
    def test_database(self):
        """
        测试数据库功能
        """
        test_name = "数据库功能测试"
        start_time = time.time()
        
        try:
            # 测试数据库连接
            conn = db_manager.get_connection()
            if conn:
                # 测试查询
                cursor = conn.cursor()
                cursor.execute("SELECT 1")
                result = cursor.fetchone()
                
                if result:
                    self._add_test_result(test_name, True, time.time() - start_time)
                else:
                    self._add_test_result(test_name, False, time.time() - start_time, "查询失败")
            else:
                self._add_test_result(test_name, False, time.time() - start_time, "连接失败")
                
        except Exception as e:
            self._add_test_result(test_name, False, time.time() - start_time, str(e))
    
    def test_cache(self):
        """
        测试缓存功能
        """
        test_name = "缓存功能测试"
        start_time = time.time()
        
        try:
            # 测试缓存设置和获取
            cache_manager.set("test_key", "test_value", 10)
            cached_value = cache_manager.get("test_key")
            
            if cached_value == "test_value":
                self._add_test_result(test_name, True, time.time() - start_time)
            else:
                self._add_test_result(test_name, False, time.time() - start_time, "缓存获取失败")
                
        except Exception as e:
            self._add_test_result(test_name, False, time.time() - start_time, str(e))
    
    def test_ai_engine(self):
        """
        测试AI引擎功能
        """
        test_name = "AI引擎功能测试"
        start_time = time.time()
        
        try:
            # 测试用户行为分析
            analysis = enhanced_ai_engine.analyze_user_behavior(1, [{
                'type': 'login',
                'timestamp': time.time(),
                'ip': '127.0.0.1',
                'user_agent': 'Mozilla/5.0'
            }])
            
            if 'user_id' in analysis:
                self._add_test_result(test_name, True, time.time() - start_time)
            else:
                self._add_test_result(test_name, False, time.time() - start_time, "分析失败")
                
        except Exception as e:
            self._add_test_result(test_name, False, time.time() - start_time, str(e))
    
    def test_exam_system(self):
        """
        测试考试系统功能
        """
        test_name = "考试系统功能测试"
        start_time = time.time()
        
        try:
            # 测试创建考试
            exam_id = enhanced_exam_system.create_exam(
                "测试考试",
                "这是一个测试考试",
                60,
                5,
                60.0
            )
            
            if exam_id > 0:
                # 测试添加题目
                question_id = enhanced_exam_system.add_question(
                    exam_id,
                    "multiple_choice",
                    "1+1=?",
                    ["1", "2", "3", "4"],
                    "2",
                    1,
                    1.0
                )
                
                if question_id > 0:
                    self._add_test_result(test_name, True, time.time() - start_time)
                else:
                    self._add_test_result(test_name, False, time.time() - start_time, "添加题目失败")
            else:
                self._add_test_result(test_name, False, time.time() - start_time, "创建考试失败")
                
        except Exception as e:
            self._add_test_result(test_name, False, time.time() - start_time, str(e))
    
    def test_system_logic(self):
        """
        测试系统逻辑功能
        """
        test_name = "系统逻辑功能测试"
        start_time = time.time()
        
        try:
            # 测试获取系统状态
            status = system_logic_manager.get_system_status()
            
            if status['status'] == 'success':
                self._add_test_result(test_name, True, time.time() - start_time)
            else:
                self._add_test_result(test_name, False, time.time() - start_time, "获取系统状态失败")
                
        except Exception as e:
            self._add_test_result(test_name, False, time.time() - start_time, str(e))
    
    def test_version_manager(self):
        """
        测试版本管理功能
        """
        test_name = "版本管理功能测试"
        start_time = time.time()
        
        try:
            # 测试获取当前版本
            current_version = version_manager.get_current_version()
            
            if current_version:
                # 测试检查更新
                update_info = version_manager.check_for_updates()
                
                if update_info['status'] == 'success':
                    self._add_test_result(test_name, True, time.time() - start_time)
                else:
                    self._add_test_result(test_name, False, time.time() - start_time, "检查更新失败")
            else:
                self._add_test_result(test_name, False, time.time() - start_time, "获取版本失败")
                
        except Exception as e:
            self._add_test_result(test_name, False, time.time() - start_time, str(e))
    
    def test_performance(self):
        """
        测试系统性能
        """
        test_name = "系统性能测试"
        start_time = time.time()
        
        try:
            # 测试数据库查询性能
            @performance_monitor.measure_time
            def test_query():
                for i in range(100):
                    db_manager.fetch_one("SELECT 1")
            
            test_query()
            
            # 测试缓存性能
            @performance_monitor.measure_time
            def test_cache_perf():
                for i in range(100):
                    cache_manager.set(f"test_key_{i}", f"test_value_{i}")
                    cache_manager.get(f"test_key_{i}")
            
            test_cache_perf()
            
            # 打印性能指标
            performance_monitor.print_metrics()
            
            self._add_test_result(test_name, True, time.time() - start_time)
            
        except Exception as e:
            self._add_test_result(test_name, False, time.time() - start_time, str(e))
    
    def _add_test_result(self, test_name, success, duration, error_message=None):
        """
        添加测试结果
        
        Args:
            test_name: 测试名称
            success: 是否成功
            duration: 测试时长
            error_message: 错误信息
        """
        result = {
            'test_name': test_name,
            'success': success,
            'duration': duration,
            'error_message': error_message
        }
        self.test_results.append(result)
        
        status = "✅" if success else "❌"
        logger.info(f"{status} {test_name} - 时长: {duration:.4f}s" + (f" - 错误: {error_message}" if not success else ""))
    
    def _print_test_results(self):
        """
        打印测试结果
        """
        print("\n" + "=" * 60)
        print("🚀 系统测试结果")
        print("=" * 60)
        
        total_tests = len(self.test_results)
        passed_tests = sum(1 for result in self.test_results if result['success'])
        failed_tests = total_tests - passed_tests
        total_duration = sum(result['duration'] for result in self.test_results)
        
        print(f"总测试数: {total_tests}")
        print(f"通过测试: {passed_tests}")
        print(f"失败测试: {failed_tests}")
        print(f"总耗时: {total_duration:.4f}s")
        print(f"成功率: {(passed_tests / total_tests * 100):.2f}%")
        
        if failed_tests > 0:
            print("\n❌ 失败测试详情:")
            for result in self.test_results:
                if not result['success']:
                    print(f"- {result['test_name']}: {result['error_message']}")
        
        print("\n✅ 通过测试详情:")
        for result in self.test_results:
            if result['success']:
                print(f"- {result['test_name']}: {result['duration']:.4f}s")
        
        print("\n" + "=" * 60)
        
        if failed_tests == 0:
            print("🎉 所有测试通过！系统运行正常")
        else:
            print(f"⚠️  有 {failed_tests} 个测试失败，需要检查")
        
        print("=" * 60)

def main():
    """
    主函数
    """
    print("🚀 系统测试工具")
    print("=" * 60)
    print("开始测试系统功能和性能...")
    
    tester = SystemTester()
    tester.start_test()
    
    # 运行所有测试
    tester.test_database()
    tester.test_cache()
    tester.test_ai_engine()
    tester.test_exam_system()
    tester.test_system_logic()
    tester.test_version_manager()
    tester.test_performance()
    
    tester.end_test()
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
