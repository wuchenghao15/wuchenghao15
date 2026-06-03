# -*- coding: utf-8 -*-
from functools import wraps
from flask import request, jsonify, flash, redirect, url_for
from app.utils.logging import logger
from app.ai.learning import ai_learning
import re
import time
import logging
import json


class AIValidator:
    """AI驱动的数据验证器,由AI全权托管数据验证"""

    def __init__(self):
        self.validation_rules = {
            'email': {
                'pattern': r'^[^\s@]+@[^\s@]+\.[^\s@]+$',
                'message': '请输入有效的邮箱地址'
            },
            'password': {
                'min_length': 8,
                'requires_uppercase': True,
                'requires_lowercase': True,
                'requires_digit': True,
                'requires_special': True,
                'message': '密码至少需要8个字符,包含大小写字母,数字和特殊字符'
            },
            'username': {
                'min_length': 3,
                'max_length': 20,
                'pattern': r'^[a-zA-Z0-9_]+$',
                'message': '用户名只能包含字母,数字和下划线,长度在3-20个字符之间'
            },
            'question_content': {
                'min_length': 10,
                'max_length': 500,
                'message': '题目内容长度必须在10-500个字符之间'
            },
            'question_options': {
                'min_count': 2,
                'max_count': 10,
                'message': '题目选项数量必须在2-10个之间'
            }
        }

        self.validation_stats = {
            'successful_validations': 0,
            'failed_validations': 0,
            'error_types': {}
        }

        self.ai_optimization_enabled = True
        self.optimization_interval = 3600
        self.last_optimization_time = time.time()

    def validate_required_fields(self, fields):
        """验证必填字段"""
        def decorator(f):
            @wraps(f)
            def decorated_function(*args, **kwargs):
                if request.is_json:
                    data = request.get_json()
                else:
                    data = request.form.to_dict()

                missing_fields = [field for field in fields if field not in data or not data[field]]
                if missing_fields:
                    error_msg = f'缺少必填字段: {", ".join(missing_fields)}'
                    logger.warning(f"数据验证失败: {error_msg}")

                    self._record_validation_data('required_fields', data, missing_fields)

                    if request.is_json:
                        return jsonify({'error': error_msg}), 400
                    else:
                        flash(error_msg, 'error')
                        return redirect(url_for('index'))

                return f(*args, **kwargs)
            return decorated_function
        return decorator

    def validate_data(self, schema):
        """基于schema验证数据"""
        def decorator(f):
            @wraps(f)
            def decorated_function(*args, **kwargs):
                if request.is_json:
                    data = request.get_json()
                else:
                    data = request.form.to_dict()

                errors = self._validate_data_against_schema(data, schema)
                if errors:
                    error_msg = '; '.join(errors)
                    self._record_validation_data('schema', data, errors, schema)

                    if request.is_json:
                        return jsonify({'error': error_msg}), 400
                    else:
                        flash(error_msg, 'error')
                        return redirect(url_for('index'))

                return f(*args, **kwargs)
            return decorated_function
        return decorator

    def _validate_data_against_schema(self, data, schema):
        """根据schema验证数据"""
        errors = []

        for field, rules in schema.items():
            value = data.get(field)

            if rules.get('required', False) and not value:
                errors.append(f'{field}不能为空')

            if value:
                if 'min_length' in rules and len(value) < rules['min_length']:
                    errors.append(f'{field}长度不能少于{rules["min_length"]}个字符')
                if 'max_length' in rules and len(value) > rules['max_length']:
                    errors.append(f'{field}长度不能超过{rules["max_length"]}个字符')
                if 'pattern' in rules and not re.match(rules['pattern'], value):
                    errors.append(f'{field}格式不正确')

                if field == 'password':
                    password_errors = self._validate_password(value)
                    if password_errors:
                        errors.extend(password_errors)
                elif field == 'email':
                    if not self.validate_email(value):
                        errors.append(self.validation_rules['email']['message'])
                elif field == 'username':
                    username_errors = self._validate_username(value)
                    if username_errors:
                        errors.extend(username_errors)

        return errors

    def _validate_password(self, password):
        """验证密码强度"""
        errors = []

        if len(password) < self.validation_rules['password']['min_length']:
            errors.append(self.validation_rules['password']['message'])
            return errors

        if self.validation_rules['password']['requires_uppercase'] and not re.search(r'[A-Z]', password):
            errors.append('密码必须包含大写字母')
        if self.validation_rules['password']['requires_lowercase'] and not re.search(r'[a-z]', password):
            errors.append('密码必须包含小写字母')
        if self.validation_rules['password']['requires_digit'] and not re.search(r'\d', password):
            errors.append('密码必须包含数字')
        if self.validation_rules['password']['requires_special'] and not re.search(r'[!@#$%^&*(),.?":{}|<>]', password):
            errors.append('密码必须包含特殊字符')

        return errors

    def _validate_username(self, username):
        """验证用户名"""
        errors = []

        if len(username) < self.validation_rules['username']['min_length']:
            errors.append('用户名长度不能少于3个字符')
        if len(username) > self.validation_rules['username']['max_length']:
            errors.append('用户名长度不能超过20个字符')
        if not re.match(self.validation_rules['username']['pattern'], username):
            errors.append('用户名格式不正确')

        return errors

    def validate_email(self, email):
        """验证邮箱格式"""
        return re.match(self.validation_rules['email']['pattern'], email) is not None

    def validate_password_strength(self, password):
        """验证密码强度"""
        return len(self._validate_password(password)) == 0

    def _record_validation_data(self, validation_type, data, errors, schema=None):
        """记录验证数据到AI学习系统"""
        self.validation_stats['total_validations'] = self.validation_stats.get('total_validations', 0) + 1

        if errors:
            self.validation_stats['failed_validations'] += 1
            for error in errors:
                error_type = error.split(':')[0].strip() if ':' in error else 'general'
                self.validation_stats['error_types'][error_type] = self.validation_stats['error_types'].get(error_type, 0) + 1
        else:
            self.validation_stats['successful_validations'] += 1

        learning_data = {
            'type': 'validation',
            'validation_type': validation_type,
            'data': data,
            'errors': errors,
            'schema': schema,
            'timestamp': time.time(),
            'stats': self.validation_stats
        }

        ai_learning.add_learning_data(learning_data)
        self._check_ai_optimization()

    def _check_ai_optimization(self):
        """检查是否需要进行AI优化"""
        current_time = time.time()
        if self.ai_optimization_enabled and (current_time - self.last_optimization_time) > self.optimization_interval:
            self._perform_ai_optimization()

    def _perform_ai_optimization(self):
        """执行AI优化,调整验证规则"""
        try:
            logger.info("开始AI优化验证规则")

            optimization_data = {
                'validation_stats': self.validation_stats,
                'current_rules': self.validation_rules,
                'timestamp': time.time()
            }

            ai_learning.add_learning_data({
                'type': 'validation_optimization',
                'data': optimization_data
            })

            if self.validation_stats['error_types'].get('password', 0) > 100:
                self.validation_rules['password']['min_length'] = 6
                logger.info("AI优化:调整密码最小长度为6")

            self.last_optimization_time = time.time()
            logger.info("AI优化验证规则完成")
        except Exception as e:
            logger.error(f"AI优化验证规则失败: {str(e)}")

    def validate_question(self, question_data):
        """验证题目数据"""
        errors = []

        content = question_data.get('content')
        if content:
            if len(content) < self.validation_rules['question_content']['min_length']:
                errors.append(f"题目内容长度不能少于{self.validation_rules['question_content']['min_length']}个字符")
            if len(content) > self.validation_rules['question_content']['max_length']:
                errors.append(f"题目内容长度不能超过{self.validation_rules['question_content']['max_length']}个字符")
        else:
            errors.append("题目内容不能为空")

        options = question_data.get('options', [])
        if len(options) < self.validation_rules['question_options']['min_count']:
            errors.append(f"题目选项数量不能少于{self.validation_rules['question_options']['min_count']}个")
        if len(options) > self.validation_rules['question_options']['max_count']:
            errors.append(f"题目选项数量不能超过{self.validation_rules['question_options']['max_count']}个")

        correct_answer = question_data.get('correct_answer')
        if not correct_answer:
            errors.append("正确答案不能为空")
        elif correct_answer not in options:
            errors.append("正确答案必须在选项中")

        self._record_validation_data('question', question_data, errors)

        return errors

    def update_validation_rules(self, rules):
        """更新验证规则,由AI动态调整"""
        self.validation_rules.update(rules)
        logger.info(f"验证规则已更新: {rules}")

        ai_learning.add_learning_data({
            'type': 'validation_rules_update',
            'new_rules': rules,
            'timestamp': time.time()
        })


ai_validator = AIValidator()

ValidationUtils = AIValidator
