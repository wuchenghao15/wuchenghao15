#!/usr/bin/env python3
import os
import sys
import traceback
import json
import hashlib
import time
from datetime import datetime
from functools import wraps
from flask import request, jsonify, current_app

class AISelfRepairMiddleware:
    def __init__(self):
        self.error_history = {}
        self.fix_history = {}
        self.max_error_history = 100
        self.auto_repair_enabled = True
        self.repair_attempts = {}
        self.max_repair_attempts = 3
        
        self.error_patterns = {
            'TemplateNotFound': {
                'fix': self._fix_template_not_found,
                'description': '模板文件缺失'
            },
            'ImportError': {
                'fix': self._fix_import_error,
                'description': '模块导入错误'
            },
            'AttributeError': {
                'fix': self._fix_attribute_error,
                'description': '属性访问错误'
            },
            'KeyError': {
                'fix': self._fix_key_error,
                'description': '字典键不存在'
            },
            'TypeError': {
                'fix': self._fix_type_error,
                'description': '类型错误'
            },
            'sqlite3.OperationalError': {
                'fix': self._fix_sqlite_error,
                'description': '数据库操作错误'
            },
            'IndexError': {
                'fix': self._fix_index_error,
                'description': '索引越界'
            },
            'FileNotFoundError': {
                'fix': self._fix_file_not_found,
                'description': '文件不存在'
            },
        }
    
    def capture_exception(self, exception, context=None):
        exc_type = type(exception).__name__
        exc_traceback = traceback.format_exc()
        error_hash = hashlib.md5(f"{exc_type}:{str(exception)}".encode()).hexdigest()
        
        error_info = {
            'id': error_hash,
            'type': exc_type,
            'message': str(exception),
            'traceback': exc_traceback,
            'context': context or {},
            'timestamp': datetime.now().isoformat(),
            'count': self.error_history.get(error_hash, {}).get('count', 0) + 1,
            'last_occurrence': datetime.now().isoformat(),
            'path': request.path if request else '',
            'method': request.method if request else '',
            'user_id': None,
        }
        
        if request and hasattr(request, 'session'):
            error_info['user_id'] = request.session.get('user_id')
        
        self.error_history[error_hash] = error_info
        
        if len(self.error_history) > self.max_error_history:
            oldest_key = min(self.error_history.keys(), 
                           key=lambda k: self.error_history[k]['timestamp'])
            del self.error_history[oldest_key]
        
        self._log_error(error_info)
        
        if self.auto_repair_enabled:
            return self._attempt_auto_repair(error_info)
        
        return None
    
    def _log_error(self, error_info):
        log_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', 'logs')
        os.makedirs(log_dir, exist_ok=True)
        
        log_file = os.path.join(log_dir, f"errors_{datetime.now().strftime('%Y-%m-%d')}.log")
        with open(log_file, 'a', encoding='utf-8') as f:
            f.write(f"[{datetime.now().isoformat()}] {error_info['type']}: {error_info['message']}\n")
            f.write(f"Path: {error_info['path']}\n")
            f.write(f"Method: {error_info['method']}\n")
            f.write(f"Traceback:\n{error_info['traceback']}\n")
            f.write("="*80 + "\n")
    
    def _attempt_auto_repair(self, error_info):
        error_type = error_info['type']
        
        if error_type in self.error_patterns:
            if error_info['id'] in self.repair_attempts:
                if self.repair_attempts[error_info['id']] >= self.max_repair_attempts:
                    return {'success': False, 'message': '已达到最大修复尝试次数'}
            
            fix_func = self.error_patterns[error_type]['fix']
            
            try:
                result = fix_func(error_info)
                
                if result.get('success'):
                    self.repair_attempts[error_info['id']] = 0
                    self.fix_history[error_info['id']] = {
                        'timestamp': datetime.now().isoformat(),
                        'error_type': error_type,
                        'message': error_info['message'],
                        'fix_result': result
                    }
                    return result
                else:
                    self.repair_attempts[error_info['id']] = self.repair_attempts.get(error_info['id'], 0) + 1
                    return result
            except Exception as e:
                self.repair_attempts[error_info['id']] = self.repair_attempts.get(error_info['id'], 0) + 1
                return {'success': False, 'message': f'修复尝试失败: {str(e)}'}
        
        return {'success': False, 'message': '未找到匹配的修复模式'}
    
    def _fix_template_not_found(self, error_info):
        message = error_info['message']
        template_name = None
        
        if 'TemplateNotFound' in message:
            template_name = message.replace('TemplateNotFound: ', '').strip()
        
        if template_name:
            templates_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', 'templates')
            template_path = os.path.join(templates_dir, template_name)
            
            if not os.path.exists(template_path):
                os.makedirs(os.path.dirname(template_path), exist_ok=True)
                
                title = template_name.replace('.html', '').replace('_', ' ')
                base_template = '''{% extends "base.html" %}

{% block title %}''' + title + '''{% endblock %}

{% block content %}
<div style="text-align:center; padding:50px;">
    <div style="font-size:48px;margin-bottom:20px;">📄</div>
    <h1>''' + title + '''</h1>
    <p>页面开发中...</p>
</div>
{% endblock %}'''
                
                with open(template_path, 'w', encoding='utf-8') as f:
                    f.write(base_template)
                
                return {'success': True, 'message': f'已创建缺失模板: {template_name}'}
        
        return {'success': False, 'message': '无法确定模板名称'}
    
    def _fix_import_error(self, error_info):
        return {'success': False, 'message': '导入错误需要手动修复'}
    
    def _fix_attribute_error(self, error_info):
        return {'success': False, 'message': '属性错误需要手动修复'}
    
    def _fix_key_error(self, error_info):
        return {'success': False, 'message': '键错误需要手动修复'}
    
    def _fix_type_error(self, error_info):
        return {'success': False, 'message': '类型错误需要手动修复'}
    
    def _fix_sqlite_error(self, error_info):
        message = error_info['message']
        
        if 'no such table' in message.lower():
            table_name = message.split()[-1]
            return {'success': False, 'message': f'表 {table_name} 不存在，需要创建'}
        
        return {'success': False, 'message': '数据库错误需要手动修复'}
    
    def _fix_index_error(self, error_info):
        return {'success': False, 'message': '索引错误需要手动修复'}
    
    def _fix_file_not_found(self, error_info):
        message = error_info['message']
        file_path = None
        
        if 'FileNotFoundError' in message:
            parts = message.split(": ")
            if len(parts) > 1:
                file_path = parts[-1].strip().strip("'")
        
        if file_path:
            if '/assets/' in file_path:
                assets_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', 'src', 'html',
                'assets')
                full_path = os.path.join(assets_dir, file_path.split('/assets/')[-1])
                
                os.makedirs(os.path.dirname(full_path), exist_ok=True)
                
                if file_path.endswith('.css'):
                    with open(full_path, 'w', encoding='utf-8') as f:
                        f.write('/* Auto-generated */')
                    return {'success': True, 'message': f'已创建缺失CSS文件: {file_path}'}
                elif file_path.endswith('.js'):
                    with open(full_path, 'w', encoding='utf-8') as f:
                        f.write('// Auto-generated')
                    return {'success': True, 'message': f'已创建缺失JS文件: {file_path}'}
        
        return {'success': False, 'message': '无法确定文件路径'}
    
    def get_error_stats(self):
        stats = {
            'total_errors': len(self.error_history),
            'total_fixes': len(self.fix_history),
            'errors_by_type': {},
            'recent_errors': []
        }
        
        for error in self.error_history.values():
            error_type = error['type']
            stats['errors_by_type'][error_type] = stats['errors_by_type'].get(error_type, 0) + 1
        
        sorted_errors = sorted(self.error_history.values(), 
                              key=lambda x: x['timestamp'], reverse=True)[:10]
        stats['recent_errors'] = [{'id': e['id'], 'type': e['type'], 
                                   'message': e['message'], 'count': e['count'],
                                   'timestamp': e['timestamp']} for e in sorted_errors]
        
        return stats
    
    def get_fix_history(self):
        return list(self.fix_history.values())
    
    def reset_error_history(self):
        self.error_history = {}
        self.fix_history = {}
        self.repair_attempts = {}
        return {'success': True, 'message': '错误历史已重置'}

ai_self_repair = AISelfRepairMiddleware()

def ai_repair_decorator(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        try:
            return f(*args, **kwargs)
        except Exception as e:
            repair_result = ai_self_repair.capture_exception(e)
            if repair_result and repair_result.get('success'):
                try:
                    return f(*args, **kwargs)
                except Exception as retry_e:
                    ai_self_repair.capture_exception(retry_e)
            raise e
    return decorated_function

def install_repair_middleware(app):
    @app.errorhandler(Exception)
    def handle_exception(e):
        ai_self_repair.capture_exception(e)
        return jsonify({
            'success': False,
            'error': str(e),
            'type': type(e).__name__,
            'timestamp': datetime.now().isoformat()
        }), 500