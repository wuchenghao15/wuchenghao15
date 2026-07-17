#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
异常处理案例收集器模块
自动抓取和学习存储系统相关的异常处理方法案例到脑库
"""

import os
import json
import logging
import traceback
import inspect
from datetime import datetime
from typing import Dict, List, Any, Optional, Callable

logger = logging.getLogger('error_case_collector')


class ErrorCaseCollector:
    """异常处理案例收集器"""

    def __init__(self, error_cases_file: str = None, knowledge_base: Any = None):
        """初始化异常处理案例收集器"""
        self.error_cases_file = error_cases_file or os.path.join(
            os.path.dirname(__file__), 'brain', 'error_cases.json'
        )
        self.knowledge_base = knowledge_base
        self.error_cases = []
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
        except Exception as e:
            logger.error(f"加载错误案例失败: {str(e)}")
            self.error_cases = []

    def _save_error_cases(self):
        """保存错误案例"""
        try:
            os.makedirs(os.path.dirname(self.error_cases_file), exist_ok=True)
            with open(self.error_cases_file, 'w', encoding='utf-8') as f:
                json.dump(self.error_cases, f, ensure_ascii=False, indent=2)
            logger.info(f"错误案例保存成功: {len(self.error_cases)} 条")
        except Exception as e:
            logger.error(f"保存错误案例失败: {str(e)}")

    def capture_exception(self, exception: Exception, context: Dict[str, Any] = None) -> Dict[str, Any]:
        """捕获异常并生成错误案例"""
        try:
            error_id = f"case-{datetime.now().strftime('%Y%m%d%H%M%S')}"
            exception_type = type(exception).__name__
            exception_message = str(exception)
            traceback_info = traceback.format_exc()
            caller_frame = inspect.currentframe().f_back
            caller_info = inspect.getframeinfo(caller_frame)

            error_case = {
                'id': error_id,
                'title': f"{exception_type}异常: {exception_message[:50]}",
                'description': f"{exception_type}: {exception_message}\n\n{traceback_info}",
                'solution': self._generate_solution(exception, context),
                'affected_files': [caller_info.filename] if caller_info.filename else [],
                'fix_date': datetime.now().isoformat(),
                'fixer': 'error-case-collector'
            }

            self.error_cases.append(error_case)
            self._save_error_cases()

            if self.knowledge_base:
                self._sync_to_knowledge_base(error_case)

            logger.info(f"异常捕获成功: {error_id}")
            return error_case
        except Exception as e:
            logger.error(f"捕获异常失败: {str(e)}")
            return None

    def _generate_solution(self, exception: Exception, context: Dict[str, Any] = None) -> str:
        """生成解决方案"""
        return f"建议检查: {type(exception).__name__} - {str(exception)}"

    def _sync_to_knowledge_base(self, error_case: Dict[str, Any]):
        """同步错误案例到知识库"""
        try:
            tags = ['exception', 'error', 'fix']
            if 'title' in error_case:
                exception_type = error_case['title'].split('异常:')[0]
                tags.append(exception_type.lower())

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


def capture_errors(func):
    """异常捕获装饰器"""
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except Exception as e:
            context = {
                'args': str(args),
                'kwargs': str(kwargs)
            }
            collector = ErrorCaseCollector()
            collector.capture_exception(e, context)
            raise
    return wrapper


def capture_method_errors(method):
    """方法异常捕获装饰器"""
    def wrapper(self_obj, *args, **kwargs):
        try:
            return method(self_obj, *args, **kwargs)
        except Exception as e:
            context = {
                'args': str(args),
                'kwargs': str(kwargs)
            }
            collector = ErrorCaseCollector()
            collector.capture_exception(e, context)
            raise
    return wrapper


if __name__ == '__main__':
    def test_function():
        raise ValueError("测试异常")

    try:
        test_function()
    except Exception as e:
        collector = ErrorCaseCollector()
        collector.capture_exception(e)
