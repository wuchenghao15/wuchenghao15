# -*- coding: utf-8 -*-
"""
AI错误分析服务
集成ai_error_fixer提供动态错误分析和修复建议
"""

import logging
import traceback
from typing import Dict, List, Optional
from datetime import datetime

logger = logging.getLogger(__name__)


class AIErrorAnalysisService:
    """AI错误分析服务"""
    
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._init_service()
        return cls._instance
    
    def _init_service(self):
        """初始化服务"""
        try:
            from app.services.ai_error_fixer import ErrorFixer, fix_code
            self.error_fixer = ErrorFixer()
            self.fix_code_func = fix_code
            logger.info("✓ AI错误分析服务已初始化")
        except Exception as e:
            self.error_fixer = None
            self.fix_code_func = None
            logger.warning(f"✗ AI错误分析服务初始化失败: {e}")
    
    def analyze_error(self, error: Exception, error_code: int, error_message: str, 
                     request_info: Optional[Dict] = None) -> Dict:
        """
        分析错误并生成AI分析报告
        Args:
            error: 异常对象
            error_code: HTTP错误码
            error_message: 错误消息
            request_info: 请求信息
        Returns:
            分析报告字典
        """
        if self.error_fixer is None:
            return self._generate_fallback_analysis(error_code, error_message)
        
        analysis = {
            'analyzed': True,
            'timestamp': datetime.now().isoformat(),
            'items': []
        }
        
        try:
            error_traceback = traceback.format_exc()
            code_snippet = self._extract_code_from_traceback(error_traceback)
            
            if code_snippet:
                fix_result = self.fix_code_func(code_snippet)
                
                for error_item in fix_result.get('errors', []):
                    analysis_item = {
                        'type': error_item.get('type', 'unknown'),
                        'title': self._get_error_title(error_item.get('type', '')),
                        'description': error_item.get('message', ''),
                        'severity': error_item.get('severity', 'low'),
                        'suggestion': error_item.get('suggestion', ''),
                        'line': error_item.get('line', 0),
                        'column': error_item.get('column', 0),
                        'code_snippet': error_item.get('code_snippet', '')
                    }
                    analysis['items'].append(analysis_item)
            
            if not analysis['items']:
                analysis['items'] = self._generate_analysis_based_on_error_code(error_code, error_message)
            
        except Exception as e:
            logger.error(f"AI错误分析失败: {e}")
            analysis['analyzed'] = False
            analysis['items'] = self._generate_fallback_analysis(error_code, error_message)
        
        return analysis
    
    def _extract_code_from_traceback(self, traceback_str: str) -> str:
        """从traceback中提取代码片段"""
        lines = traceback_str.split('\n')
        code_lines = []
        
        for i, line in enumerate(lines):
            if line.strip().startswith('File "'):
                next_line = lines[i + 1] if i + 1 < len(lines) else ''
                if next_line.strip().startswith('    '):
                    code_lines.append(next_line.strip())
        
        return '\n'.join(code_lines[:20])
    
    def _get_error_title(self, error_type: str) -> str:
        """根据错误类型获取标题"""
        titles = {
            'division_by_zero': '除零错误',
            'negative_square_root': '负数平方根错误',
            'quadratic_negative_discriminant': '二次方程判别式错误',
            'numeric_overflow': '数值溢出',
            'null_pointer': '空指针引用',
            'potential_null_pointer': '潜在空指针引用',
            'unhandled_exception': '未处理异常',
            'potential_type_mismatch': '类型不匹配',
            'potential_infinite_loop': '潜在无限循环',
            'off_by_one': '边界错误',
            'dead_code': '死代码'
        }
        return titles.get(error_type, '未知错误类型')
    
    def _generate_analysis_based_on_error_code(self, error_code: int, error_message: str) -> List[Dict]:
        """根据错误码生成分析"""
        analysis_items = []
        
        if error_code >= 500:
            analysis_items.append({
                'type': 'system_error',
                'title': '系统内部错误',
                'description': f'系统遇到了未预期的错误: {error_message}',
                'severity': 'error',
                'suggestion': '请联系系统管理员提供错误编号以便排查问题'
            })
            analysis_items.append({
                'type': 'server_issue',
                'title': '服务器问题',
                'description': '服务器在处理请求时发生故障',
                'severity': 'error',
                'suggestion': '稍后重试，或检查相关服务状态'
            })
        elif error_code == 401:
            analysis_items.append({
                'type': 'authentication_error',
                'title': '认证失败',
                'description': '您的身份验证信息无效或已过期',
                'severity': 'warning',
                'suggestion': '请重新登录系统'
            })
        elif error_code == 403:
            analysis_items.append({
                'type': 'authorization_error',
                'title': '权限不足',
                'description': '您没有访问此资源的权限',
                'severity': 'warning',
                'suggestion': '请联系管理员获取相应权限'
            })
        elif error_code == 404:
            analysis_items.append({
                'type': 'resource_not_found',
                'title': '资源不存在',
                'description': '请求的资源不存在或已被删除',
                'severity': 'info',
                'suggestion': '检查URL是否正确，或返回首页浏览'
            })
        elif error_code == 429:
            analysis_items.append({
                'type': 'rate_limit',
                'title': '请求过于频繁',
                'description': '您的请求频率超过了系统限制',
                'severity': 'warning',
                'suggestion': '请稍后再试，或联系管理员调整限制'
            })
        else:
            analysis_items.append({
                'type': 'client_error',
                'title': '客户端错误',
                'description': f'请求参数或格式有误: {error_message}',
                'severity': 'warning',
                'suggestion': '检查请求参数是否正确'
            })
        
        return analysis_items
    
    def _generate_fallback_analysis(self, error_code: int, error_message: str) -> List[Dict]:
        """生成降级分析（当AI分析不可用时）"""
        return self._generate_analysis_based_on_error_code(error_code, error_message)


ai_error_analysis = AIErrorAnalysisService()


def analyze_error(error: Exception, error_code: int, error_message: str, 
                  request_info: Optional[Dict] = None) -> Dict:
    """分析错误并生成AI分析报告"""
    return ai_error_analysis.analyze_error(error, error_code, error_message, request_info)


__all__ = ['AIErrorAnalysisService', 'ai_error_analysis', 'analyze_error']