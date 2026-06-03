#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
错误上报服务 - 实现错误捕获、上报和数据库记录
"""

import os
import sys
import json
import time
import traceback
import threading
from typing import Dict, List, Optional, Any, Callable
from enum import Enum
from dataclasses import dataclass, field
from datetime import datetime

from app.utils.logging import logger


class ErrorLevel(Enum):
    """错误级别"""
    DEBUG = "debug"
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


class ErrorCategory(Enum):
    """错误类别"""
    DATABASE = "database"
    NETWORK = "network"
    VALIDATION = "validation"
    PERMISSION = "permission"
    BUSINESS = "business"
    SYSTEM = "system"
    AI = "ai"
    UNKNOWN = "unknown"


@dataclass
class ErrorReport:
    """错误报告"""
    error_id: str
    level: ErrorLevel
    category: ErrorCategory
    message: str
    error_type: str
    stack_trace: str
    file_path: str
    line_number: int
    function_name: str
    timestamp: float = field(default_factory=lambda: time.time())
    context: Dict = field(default_factory=dict)
    user_id: Optional[str] = None
    session_id: Optional[str] = None
    request_id: Optional[str] = None
    resolved: bool = False
    resolved_at: Optional[float] = None
    resolved_by: Optional[str] = None

    def to_dict(self) -> Dict:
        return {
            'error_id': self.error_id,
            'level': self.level.value,
            'category': self.category.value,
            'message': self.message,
            'error_type': self.error_type,
            'stack_trace': self.stack_trace,
            'file_path': self.file_path,
            'line_number': self.line_number,
            'function_name': self.function_name,
            'timestamp': self.timestamp,
            'context': self.context,
            'user_id': self.user_id,
            'session_id': self.session_id,
            'request_id': self.request_id,
            'resolved': self.resolved,
            'resolved_at': self.resolved_at,
            'resolved_by': self.resolved_by
        }


@dataclass
class ErrorStatistics:
    """错误统计"""
    total_errors: int = 0
    errors_by_level: Dict[str, int] = field(default_factory=dict)
    errors_by_category: Dict[str, int] = field(default_factory=dict)
    recent_errors: List[ErrorReport] = field(default_factory=list)
    resolved_count: int = 0
    unresolved_count: int = 0
    avg_resolution_time: float = 0.0


class ErrorReportService:
    """错误上报服务"""

    def __init__(self):
        self._reports: Dict[str, ErrorReport] = {}
        self._error_handlers: List[Callable] = []
        self._lock = threading.RLock()
        self._report_count = 0
        self._max_reports = 10000
        self._db_path = os.path.join(os.path.dirname(__file__), '..', '..', 'data', 'error_reports.json')
        self._ai_auto_fix_enabled = True
        
        os.makedirs(os.path.dirname(self._db_path), exist_ok=True)
        
        self._load_reports()
        self._setup_global_exception_handler()
        
        logger.info("错误上报服务初始化完成")

    def enable_ai_auto_fix(self, enabled: bool = True):
        """启用/禁用AI自动修复"""
        self._ai_auto_fix_enabled = enabled
        logger.info(f"AI自动修复已{'启用' if enabled else '禁用'}")

    def auto_fix_error(self, error: Exception, file_path: str = "", context: Optional[Dict] = None) -> Optional[Dict]:
        """自动修复错误"""
        if not self._ai_auto_fix_enabled:
            return None
        
        try:
            from app.services.ai_auto_fix_service import ai_auto_fix_service
            analysis, solution = ai_auto_fix_service.auto_fix_and_learn(error, file_path, context)
            
            return {
                'analysis': {
                    'error_id': analysis.error_id,
                    'error_type': analysis.error_type,
                    'error_message': analysis.error_message,
                    'file_path': analysis.file_path,
                    'line_number': analysis.line_number,
                    'pattern': analysis.pattern.value,
                    'suggestions': analysis.suggestions
                },
                'solution': {
                    'solution_id': solution.solution_id,
                    'strategy': solution.strategy.value,
                    'original_code': solution.original_code,
                    'fixed_code': solution.fixed_code,
                    'explanation': solution.explanation,
                    'confidence': solution.confidence
                }
            }
        except Exception as e:
            logger.error(f"AI自动修复失败: {str(e)}")
            return None

    def _load_reports(self):
        """加载已保存的错误报告"""
        if os.path.exists(self._db_path):
            try:
                with open(self._db_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    for report_data in data.get('reports', []):
                        report = ErrorReport(
                            error_id=report_data['error_id'],
                            level=ErrorLevel(report_data['level']),
                            category=ErrorCategory(report_data['category']),
                            message=report_data['message'],
                            error_type=report_data['error_type'],
                            stack_trace=report_data['stack_trace'],
                            file_path=report_data['file_path'],
                            line_number=report_data['line_number'],
                            function_name=report_data['function_name'],
                            timestamp=report_data['timestamp'],
                            context=report_data.get('context', {}),
                            user_id=report_data.get('user_id'),
                            session_id=report_data.get('session_id'),
                            request_id=report_data.get('request_id'),
                            resolved=report_data.get('resolved', False),
                            resolved_at=report_data.get('resolved_at'),
                            resolved_by=report_data.get('resolved_by')
                        )
                        self._reports[report.error_id] = report
                    self._report_count = len(self._reports)
                logger.info(f"已加载 {len(self._reports)} 条错误报告")
            except Exception as e:
                logger.error(f"加载错误报告失败: {str(e)}")

    def _save_reports(self):
        """保存错误报告到文件"""
        try:
            data = {
                'last_updated': time.time(),
                'reports': [r.to_dict() for r in self._reports.values()]
            }
            with open(self._db_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
        except Exception as e:
            logger.error(f"保存错误报告失败: {str(e)}")

    def _setup_global_exception_handler(self):
        """设置全局异常处理器"""
        def global_exception_handler(exc_type, exc_value, exc_traceback):
            if issubclass(exc_type, KeyboardInterrupt):
                sys.__excepthook__(exc_type, exc_value, exc_traceback)
                return
            
            error_report = self.capture_error(
                exc_value,
                level=ErrorLevel.ERROR,
                category=ErrorCategory.SYSTEM,
                context={'exc_type': str(exc_type)}
            )
            
            logger.error(f"未捕获异常: {error_report.error_id} - {exc_value}")
            
            for handler in self._error_handlers:
                try:
                    handler(error_report)
                except Exception as e:
                    logger.error(f"错误处理器执行失败: {str(e)}")
        
        sys.excepthook = global_exception_handler

    def _generate_error_id(self) -> str:
        """生成错误ID"""
        import uuid
        return f"ERR-{datetime.now().strftime('%Y%m%d%H%M%S')}-{uuid.uuid4().hex[:8]}"

    def _classify_error(self, error: Exception) -> ErrorCategory:
        """分类错误"""
        error_str = str(error).lower()
        error_type = type(error).__name__.lower()
        
        if 'database' in error_str or 'sql' in error_str or 'sqlite' in error_type:
            return ErrorCategory.DATABASE
        elif 'network' in error_str or 'connection' in error_str or 'timeout' in error_str:
            return ErrorCategory.NETWORK
        elif 'validation' in error_str or 'invalid' in error_str:
            return ErrorCategory.VALIDATION
        elif 'permission' in error_str or 'denied' in error_str or 'unauthorized' in error_str:
            return ErrorCategory.PERMISSION
        elif 'ai' in error_str or 'openai' in error_str or 'anthropic' in error_str:
            return ErrorCategory.AI
        else:
            return ErrorCategory.UNKNOWN

    def capture_error(self, 
                     error: Exception,
                     level: ErrorLevel = ErrorLevel.ERROR,
                     category: Optional[ErrorCategory] = None,
                     context: Optional[Dict] = None,
                     user_id: Optional[str] = None,
                     session_id: Optional[str] = None,
                     request_id: Optional[str] = None) -> ErrorReport:
        """捕获错误"""
        import traceback
        
        tb = traceback.extract_tb(error.__traceback__)
        if tb:
            frame = tb[-1]
            file_path = frame.filename
            line_number = frame.lineno
            function_name = frame.name
        else:
            file_path = "unknown"
            line_number = 0
            function_name = "unknown"
        
        category = category or self._classify_error(error)
        
        ctx = context or {}
        
        if self._ai_auto_fix_enabled:
            fix_result = self.auto_fix_error(error, file_path, ctx)
            if fix_result:
                ctx['ai_fix'] = {
                    'applied': True,
                    'confidence': fix_result['solution']['confidence'],
                    'strategy': fix_result['solution']['strategy'],
                    'explanation': fix_result['solution']['explanation']
                }
                logger.info(f"AI自动修复已应用: {fix_result['solution']['strategy']} (置信度: {fix_result['solution']['confidence']:.2f})")
        
        report = ErrorReport(
            error_id=self._generate_error_id(),
            level=level,
            category=category,
            message=str(error),
            error_type=type(error).__name__,
            stack_trace=traceback.format_exc(),
            file_path=file_path,
            line_number=line_number,
            function_name=function_name,
            context=ctx,
            user_id=user_id,
            session_id=session_id,
            request_id=request_id
        )
        
        with self._lock:
            self._reports[report.error_id] = report
            self._report_count += 1
            
            if len(self._reports) > self._max_reports:
                oldest = min(self._reports.items(), key=lambda x: x[1].timestamp)
                del self._reports[oldest[0]]
        
        self._save_reports()
        
        return report

    def report_error(self,
                   message: str,
                   error_type: str,
                   level: ErrorLevel = ErrorLevel.ERROR,
                   category: ErrorCategory = ErrorCategory.UNKNOWN,
                   stack_trace: str = "",
                   context: Optional[Dict] = None,
                   user_id: Optional[str] = None,
                   session_id: Optional[str] = None,
                   request_id: Optional[str] = None) -> ErrorReport:
        """手动上报错误"""
        import traceback
        
        if not stack_trace:
            stack_trace = traceback.format_stack()
        
        report = ErrorReport(
            error_id=self._generate_error_id(),
            level=level,
            category=category,
            message=message,
            error_type=error_type,
            stack_trace=stack_trace,
            file_path="manual_report",
            line_number=0,
            function_name="manual_report",
            context=context or {},
            user_id=user_id,
            session_id=session_id,
            request_id=request_id
        )
        
        with self._lock:
            self._reports[report.error_id] = report
            self._report_count += 1
        
        self._save_reports()
        
        return report

    def get_error(self, error_id: str) -> Optional[ErrorReport]:
        """获取错误报告"""
        return self._reports.get(error_id)

    def list_errors(self,
                   level: Optional[ErrorLevel] = None,
                   category: Optional[ErrorCategory] = None,
                   resolved: Optional[bool] = None,
                   limit: int = 100,
                   offset: int = 0) -> List[ErrorReport]:
        """列出错误报告"""
        results = []
        
        with self._lock:
            for report in self._reports.values():
                if level and report.level != level:
                    continue
                if category and report.category != category:
                    continue
                if resolved is not None and report.resolved != resolved:
                    continue
                results.append(report)
        
        results.sort(key=lambda x: x.timestamp, reverse=True)
        return results[offset:offset+limit]

    def resolve_error(self, error_id: str, resolved_by: str = "system") -> bool:
        """标记错误为已解决"""
        with self._lock:
            report = self._reports.get(error_id)
            if report:
                report.resolved = True
                report.resolved_at = time.time()
                report.resolved_by = resolved_by
                self._save_reports()
                return True
        return False

    def delete_error(self, error_id: str) -> bool:
        """删除错误报告"""
        with self._lock:
            if error_id in self._reports:
                del self._reports[error_id]
                self._save_reports()
                return True
        return False

    def clear_resolved_errors(self) -> int:
        """清除已解决的错误"""
        with self._lock:
            resolved_ids = [eid for eid, r in self._reports.items() if r.resolved]
            for eid in resolved_ids:
                del self._reports[eid]
            
            self._save_reports()
            return len(resolved_ids)

    def get_statistics(self) -> ErrorStatistics:
        """获取错误统计"""
        stats = ErrorStatistics()
        
        with self._lock:
            stats.total_errors = len(self._reports)
            stats.errors_by_level = {}
            stats.errors_by_category = {}
            stats.recent_errors = []
            
            for report in self._reports.values():
                level_key = report.level.value
                category_key = report.category.value
                
                stats.errors_by_level[level_key] = stats.errors_by_level.get(level_key, 0) + 1
                stats.errors_by_category[category_key] = stats.errors_by_category.get(category_key, 0) + 1
                
                if report.resolved:
                    stats.resolved_count += 1
                else:
                    stats.unresolved_count += 1
            
            recent = sorted(self._reports.values(), key=lambda x: x.timestamp, reverse=True)
            stats.recent_errors = recent[:10]
        
        return stats

    def register_error_handler(self, handler: Callable):
        """注册错误处理器"""
        self._error_handlers.append(handler)

    def export_errors(self, format_type: str = "json") -> str:
        """导出错误报告"""
        with self._lock:
            reports = list(self._reports.values())
        
        if format_type == "json":
            return json.dumps([r.to_dict() for r in reports], ensure_ascii=False, indent=2)
        elif format_type == "csv":
            import csv
            import io
            
            output = io.StringIO()
            if reports:
                writer = csv.DictWriter(output, fieldnames=reports[0].to_dict().keys())
                writer.writeheader()
                for report in reports:
                    writer.writerow(report.to_dict())
            return output.getvalue()
        else:
            return str(reports)

    def get_errors_by_time_range(self, start_time: float, end_time: float) -> List[ErrorReport]:
        """获取时间范围内的错误"""
        results = []
        
        with self._lock:
            for report in self._reports.values():
                if start_time <= report.timestamp <= end_time:
                    results.append(report)
        
        return sorted(results, key=lambda x: x.timestamp, reverse=True)

    def get_top_errors(self, limit: int = 10) -> List[Dict]:
        """获取最常见的错误"""
        error_counts: Dict[str, Dict] = {}
        
        with self._lock:
            for report in self._reports.values():
                key = f"{report.error_type}:{report.message[:50]}"
                if key not in error_counts:
                    error_counts[key] = {
                        'error_type': report.error_type,
                        'message': report.message[:100],
                        'count': 0,
                        'last_occurrence': report.timestamp,
                        'level': report.level.value,
                        'category': report.category.value
                    }
                error_counts[key]['count'] += 1
                if report.timestamp > error_counts[key]['last_occurrence']:
                    error_counts[key]['last_occurrence'] = report.timestamp
        
        sorted_errors = sorted(error_counts.values(), key=lambda x: x['count'], reverse=True)
        return sorted_errors[:limit]

    def search_errors(self, keyword: str) -> List[ErrorReport]:
        """搜索错误"""
        results = []
        keyword_lower = keyword.lower()
        
        with self._lock:
            for report in self._reports.values():
                if (keyword_lower in report.message.lower() or
                    keyword_lower in report.error_type.lower() or
                    keyword_lower in report.stack_trace.lower()):
                    results.append(report)
        
        return sorted(results, key=lambda x: x.timestamp, reverse=True)


def create_error_report_decorator(error_service: 'ErrorReportService'):
    """创建错误上报装饰器"""
    def decorator(func):
        def wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except Exception as e:
                error_service.capture_error(
                    e,
                    context={'function': func.__name__, 'args': str(args), 'kwargs': str(kwargs)}
                )
                raise
        return wrapper
    return decorator


# 创建全局实例
error_report_service = ErrorReportService()
