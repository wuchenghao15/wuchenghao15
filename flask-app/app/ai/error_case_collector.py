#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
异常处理案例收集器模块
自动抓取和学习存储系统相关的异常处理方法案例到脑库

import os
# JSON import removed - using database
import logging
import traceback
import inspect
from datetime import datetime
from typing import Dict, List, Any, Optional, Callable

# 配置日志
logger = logging.getLogger('error_case_collector')

class ErrorCaseCollector:
    """异常处理案例收集器"""

    def __init__(self, error_cases_file: str = None, knowledge_base: Any = None):
        """初始化异常处理案例收集器"""
        # 错误案例文件路径
        self.error_cases_file = error_cases_file or os.path.join(
            os.path.dirname(__file__), 'brain', 'error_cases.json'
        )

        # 知识库实例
        self.knowledge_base = knowledge_base

        # 错误案例数据
        self.error_cases = []

        # 加载错误案例
        self._load_error_cases()

        logger.info("异常处理案例收集器初始化完成")

    def _load_error_cases(self):
        """加载错误案例"""
        try:
            if os.path.exists(self.error_cases_file):
                with open(self.error_cases_file, 'r', encoding='utf-8') as f:
                    self.error_cases = json.load(f)
                logger.info(f"错误案例加载成功: {len(self.error_cases)} 条")
            else:
                logger.warning(f"错误案例文件不存在: {self.error_cases_file}")
                self.error_cases = []
            logger.error(f"加载错误案例失败: {str(e)}")
            self.error_cases = []
    def _save_error_cases(self):
        """保存错误案例"""
        try:
            # 确保目录存在
            os.makedirs(os.path.dirname(self.error_cases_file), exist_ok=True)
            with open(self.error_cases_file, 'w', encoding='utf-8') as f:
                json.dump(self.error_cases, f, ensure_ascii=False, indent=2)
            logger.info(f"错误案例保存成功: {len(self.error_cases)} 条")
        except Exception as e:
            logger.error(f"保存错误案例失败: {str(e)}")

    def capture_exception(self, exception: Exception, context: Dict[str, Any] = None) -> Dict[str, Any]:
        """捕获异常并生成错误案例"""
        try:
            # 生成错误案例ID
            error_id = f"case-{datetime.now().strftime('%Y%m%d%H%M%S')}"
            # 获取异常信息
            exception_type = type(exception).__name__
            exception_message = str(exception)
            traceback_info = traceback.format_exc()

            # 获取调用上下文
            caller_frame = inspect.currentframe().f_back
            caller_info = inspect.getframeinfo(caller_frame)

            # 构建错误案例
            error_case = {
                'id': error_id,
                'title': f"{exception_type}异常: {exception_message[:50]}",
                'description': f"{exception_type}: {exception_message}\n\n{traceback_info}",
                'solution': self._generate_solution(exception, context),
                'affected_files': [caller_info.filename] if caller_info.filename else [],
                'fix_date': datetime.now().isoformat(),
                'fixer': 'error-case-collector'
            }

            # 添加到错误案例列表
            self.error_cases.append(error_case)
            self._save_error_cases()

            # 同步到知识库
            if self.knowledge_base:
                self._sync_to_knowledge_base(error_case)

            logger.info(f"异常捕获成功: {error_id}")
            return error_case
        except Exception as e:
            logger.error(f"捕获异常失败: {str(e)}")
            return {}

    def _generate_solution(self, exception: Exception, context: Dict[str, Any] = None) -> str:
        """生成解决方案"""
        exception_type = type(exception).__name__

        # 常见异常的解决方案
        solutions = {
            'FileNotFoundError': "检查文件路径是否正确，确保文件存在",
            'ConnectionError': "检查网络连接，确保服务可用",
            'ValueError': "检查输入值是否符合要求，确保数据类型正确",
            'TypeError': "检查参数类型是否正确，确保函数调用符合签名",
            'KeyError': "检查字典键是否存在，使用get()方法或设置默认值",
            'IndexError': "检查列表索引是否在有效范围内",
            'SQLiteError': "检查SQL语句语法，确保数据库连接正常",
            'ImportError': "确保所有依赖项已安装，检查导入路径是否正确",
            'ModuleNotFoundError': "确保模块已安装，检查模块名称是否正确"
        }

        return solutions.get(exception_type, "检查异常信息，根据具体情况进行修复")

    def _sync_to_knowledge_base(self, error_case: Dict[str, Any]):
        """同步错误案例到知识库"""
            # 提取关键词作为标签
            tags = ['exception', 'error', 'fix']
            # 从异常类型中提取标签
            if 'title' in error_case:
                exception_type = error_case['title'].split('异常:')[0]
                tags.append(exception_type.lower())

            # 添加到知识库
            self.knowledge_base.add_knowledge(
                category='engineering',
                title=error_case['title'],
                content=f"描述: {error_case['description']}\n\n解决方案: {error_case['solution']}",
                source='error_case_collector',
                tags=tags
            )
            logger.info(f"错误案例同步到知识库成功: {error_case['id']}")
        except Exception as e:
            logger.error(f"同步错误案例到知识库失败: {str(e)}")

    def get_error_cases(self, limit: int = None) -> List[Dict[str, Any]]:
        """获取错误案例"""
        if limit:
            return self.error_cases[-limit:]
        return self.error_cases

    def search_error_cases(self, query: str) -> List[Dict[str, Any]]:
        """搜索错误案例"""
        results = []

        for case in self.error_cases:
            if (query.lower() in case['title'].lower() or
                query.lower() in case['description'].lower() or
                query.lower() in case['solution'].lower()):
                results.append(case)

        return results

    def get_error_cases_by_type(self, error_type: str) -> List[Dict[str, Any]]:
        """按错误类型获取错误案例"""
        results = []

        for case in self.error_cases:
            if error_type.lower() in case['title'].lower():
                results.append(case)

        return results

    def monitor_function(self, func: Callable) -> Callable:
        def wrapper(*args, **kwargs):
            try:
            except Exception as e:
                # 捕获异常并生成错误案例
                    'args': str(args),
                    'kwargs': str(kwargs)
                self.capture_exception(e, context)
                # 重新抛出异常，不影响原有流程
                raise

        return wrapper

    def monitor_method(self, method: Callable) -> Callable:
        """监控方法执行，捕获异常"""
            try:
                return method(self_obj, *args, **kwargs)
            except Exception as e:
                # 捕获异常并生成错误案例
                    'class': self_obj.__class__.__name__,
                    'method': method.__name__,
                    'args': str(args),
                    'kwargs': str(kwargs)
                }
                self.capture_exception(e, context)
                # 重新抛出异常，不影响原有流程
                raise

        return wrapper

    def get_statistics(self) -> Dict[str, Any]:
        """获取错误案例统计信息"""
        try:
                'total_cases': len(self.error_cases),
                'cases_by_type': {},
                'last_updated': datetime.now().isoformat()
            }

            # 按错误类型统计
            for case in self.error_cases:
                if error_type not in stats['cases_by_type']:
                    stats['cases_by_type'][error_type] = 0
                stats['cases_by_type'][error_type] += 1

            return stats
        except Exception as e:
            return {}

# 创建全局异常处理案例收集器实例
try:
    from app.ai.ai_knowledge_base import ai_knowledge_base
    error_case_collector = ErrorCaseCollector(knowledge_base=ai_knowledge_base)
except ImportError:
# 异常捕获装饰器
def capture_errors(func):
    """异常捕获装饰器"""
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except Exception as e:
                'function': func.__name__,
                'args': str(args),
                'kwargs': str(kwargs)
            }
            error_case_collector.capture_exception(e, context)
            # 重新抛出异常，不影响原有流程
            raise

    return wrapper

# 方法异常捕获装饰器
def capture_method_errors(method):
    """方法异常捕获装饰器"""
    def wrapper(self_obj, *args, **kwargs):
        try:
            return method(self_obj, *args, **kwargs)
            # 捕获异常并生成错误案例
                'method': method.__name__,
                'args': str(args),
            }
            error_case_collector.capture_exception(e, context)
            # 重新抛出异常，不影响原有流程
            raise
    return wrapper

if __name__ == '__main__':
    print("异常处理案例收集器初始化成功")
    print(f"错误案例数量: {len(error_case_collector.error_cases)}")

    # 测试异常捕获
    @capture_errors
    def test_function():

    try:
        test_function()
    except Exception as e:
        pass
