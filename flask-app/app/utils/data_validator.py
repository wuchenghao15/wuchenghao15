# -*- coding: utf-8 -*-
#!/usr/bin/env python3
"""
Data Validator Module
数据验证模块 - 提供统一的数据验证功能
"""

import re
from typing import Dict, List, Optional, Tuple
import email_validator


def validate_user_data(user_data: Dict) -> Tuple[bool, List[str]]:
    """
    验证用户数据
    
    Args:
        user_data: 用户数据字典
        
    Returns:
        (is_valid, errors): 验证结果和错误列表
    """
    errors = []
    
    # 验证用户名
    username = user_data.get('username', '')
    if not username:
        errors.append('用户名不能为空')
    elif len(username) < 3:
        errors.append('用户名至少需要3个字符')
    elif len(username) > 50:
        errors.append('用户名不能超过50个字符')
    elif not re.match(r'^[a-zA-Z0-9_]+$', username):
        errors.append('用户名只能包含字母,数字和下划线')
    
    # 验证密码
    password = user_data.get('password', '')
    if not password:
        errors.append('密码不能为空')
    elif len(password) < 6:
        errors.append('密码至少需要6个字符')
    elif len(password) > 128:
        errors.append('密码不能超过128个字符')
    
    # 验证邮箱(使用简单正则验证,避免DNS查询)
    email = user_data.get('email', '')
    if email:
        email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        if not re.match(email_pattern, email):
            errors.append('邮箱格式不正确')
    
    # 验证角色
    role = user_data.get('role', '')
    valid_roles = ['student', 'teacher', 'admin', 'super_admin', 'hardware_admin', 'guest', 'designer']
    if role and role not in valid_roles:
        errors.append(f'无效的角色: {role}')
    
    return (len(errors) == 0, errors)


def validate_exam_data(exam_data: Dict) -> Tuple[bool, List[str]]:
    """
    验证考试数据
    
    Args:
        exam_data: 考试数据字典
        
    Returns:
        (is_valid, errors): 验证结果和错误列表
    """
    errors = []
    
    # 验证考试名称
    name = exam_data.get('name', '')
    if not name:
        errors.append('考试名称不能为空')
    elif len(name) > 200:
        errors.append('考试名称不能超过200个字符')
    
    # 验证考试描述
    description = exam_data.get('description', '')
    if description and len(description) > 2000:
        errors.append('考试描述不能超过2000个字符')
    
    # 验证考试时长
    duration = exam_data.get('duration', '')
    if duration:
        try:
            duration_int = int(duration)
            if duration_int <= 0:
                errors.append('考试时长必须大于0')
            elif duration_int > 1440:
                errors.append('考试时长不能超过1440分钟(24小时)')
        except ValueError:
            errors.append('考试时长必须是数字')
    
    # 验证题目数量
    question_count = exam_data.get('question_count', '')
    if question_count:
        try:
            qc_int = int(question_count)
            if qc_int <= 0:
                errors.append('题目数量必须大于0')
            elif qc_int > 1000:
                errors.append('题目数量不能超过1000')
        except ValueError:
            errors.append('题目数量必须是数字')
    
    # 验证总分
    total_score = exam_data.get('total_score', '')
    if total_score:
        try:
            ts_int = int(total_score)
            if ts_int <= 0:
                errors.append('总分必须大于0')
            elif ts_int > 10000:
                errors.append('总分不能超过10000')
        except ValueError:
            errors.append('总分必须是数字')
    
    return (len(errors) == 0, errors)


def validate_question_data(question_data: Dict) -> Tuple[bool, List[str]]:
    """
    验证题目数据
    
    Args:
        question_data: 题目数据字典
        
    Returns:
        (is_valid, errors): 验证结果和错误列表
    """
    errors = []
    
    # 验证题目内容
    content = question_data.get('content', '')
    if not content:
        errors.append('题目内容不能为空')
    elif len(content) > 5000:
        errors.append('题目内容不能超过5000个字符')
    
    # 验证题目类型
    question_type = question_data.get('type', '')
    valid_types = ['single', 'multiple', 'judge', 'fill', 'essay']
    if not question_type:
        errors.append('题目类型不能为空')
    elif question_type not in valid_types:
        errors.append(f'无效的题目类型: {question_type}')
    
    # 验证分值
    score = question_data.get('score', '')
    if score:
        try:
            score_float = float(score)
            if score_float <= 0:
                errors.append('分值必须大于0')
            elif score_float > 100:
                errors.append('分值不能超过100')
        except ValueError:
            errors.append('分值必须是数字')
    
    # 验证选项(选择题)
    options = question_data.get('options', [])
    if question_type in ['single', 'multiple']:
        if not options or len(options) < 2:
            errors.append('选择题至少需要2个选项')
        elif len(options) > 10:
            errors.append('选择题选项不能超过10个')
    
    # 验证答案
    answer = question_data.get('answer', '')
    if not answer:
        errors.append('答案不能为空')
    
    return (len(errors) == 0, errors)


def validate_email(email: str) -> bool:
    """
    验证邮箱格式
    
    Args:
        email: 邮箱地址
        
    Returns:
        True if valid, False otherwise
    """
    try:
        email_validator.validate_email(email)
        return True
    except email_validator.EmailNotValidError:
        return False


def validate_phone(phone: str) -> bool:
    """
    验证手机号格式
    
    Args:
        phone: 手机号码
        
    Returns:
        True if valid, False otherwise
    """
    if not phone:
        return False
    # 中国大陆手机号正则
    pattern = r'^1[3-9]\d{9}$'
    return bool(re.match(pattern, phone))


def validate_url(url: str) -> bool:
    """
    验证URL格式
    
    Args:
        url: URL地址
        
    Returns:
        True if valid, False otherwise
    """
    if not url:
        return False
    pattern = r'^(https?://)?([\da-z.-]+)\.([a-z.]{2,6})([/\w.-]*)*(/?)$'
    return bool(re.match(pattern, url))


def validate_password_strength(password: str) -> str:
    """
    验证密码强度
    
    Args:
        password: 密码
        
    Returns:
        密码强度等级: 'weak', 'medium', 'strong'
    """
    if not password:
        return 'weak'
    
    score = 0
    
    # 长度检查
    if len(password) >= 8:
        score += 1
    if len(password) >= 12:
        score += 1
    
    # 包含数字
    if re.search(r'\d', password):
        score += 1
    
    # 包含小写字母
    if re.search(r'[a-z]', password):
        score += 1
    
    # 包含大写字母
    if re.search(r'[A-Z]', password):
        score += 1
    
    # 包含特殊字符
    if re.search(r'[!@#$%^&*(),.?":{}|<>]', password):
        score += 1
    
    if score <= 2:
        return 'weak'
    elif score <= 4:
        return 'medium'
    else:
        return 'strong'


def sanitize_input(input_string: str) -> str:
    """
    清理用户输入,防止XSS攻击
    
    Args:
        input_string: 用户输入
        
    Returns:
        清理后的字符串
    """
    if not input_string:
        return ''
    
    # 移除危险标签
    sanitized = re.sub(r'<script[^>]*>.*?</script>', '', input_string, flags=re.IGNORECASE)
    sanitized = re.sub(r'<iframe[^>]*>.*?</iframe>', '', sanitized, flags=re.IGNORECASE)
    sanitized = re.sub(r'on\w+\s*=\s*["\'].*?["\']', '', sanitized, flags=re.IGNORECASE)
    
    return sanitized.strip()


def validate_file_name(filename: str) -> Tuple[bool, Optional[str]]:
    """
    验证文件名是否安全
    
    Args:
        filename: 文件名
        
    Returns:
        (is_valid, error_message)
    """
    if not filename:
        return False, '文件名不能为空'
    
    # 检查路径遍历攻击
    if '..' in filename or '/' in filename or '\\' in filename:
        return False, '文件名不能包含路径分隔符'
    
    # 检查特殊字符
    if re.search(r'[<>:\"|?*]', filename):
        return False, '文件名不能包含特殊字符'
    
    # 检查长度
    if len(filename) > 255:
        return False, '文件名不能超过255个字符'
    
    # 检查空文件名或只有空格
    if filename.strip() == '':
        return False, '文件名不能为空'
    
    return True, None


def validate_integer_range(value: int, min_val: int, max_val: int, field_name: str = '数值') -> Tuple[bool, List[str]]:
    """
    验证整数是否在指定范围内
    
    Args:
        value: 要验证的整数
        min_val: 最小值
        max_val: 最大值
        field_name: 字段名称(用于错误消息)
        
    Returns:
        (is_valid, errors)
    """
    errors = []
    
    try:
        int_value = int(value)
        if int_value < min_val:
            errors.append(f'{field_name}不能小于{min_val}')
        if int_value > max_val:
            errors.append(f'{field_name}不能大于{max_val}')
    except ValueError:
        errors.append(f'{field_name}必须是整数')
    
    return (len(errors) == 0, errors)


def validate_string_length(value: str, min_len: int, max_len: int, field_name: str = '字符串') -> Tuple[bool, List[str]]:
    """
    验证字符串长度
    
    Args:
        value: 字符串
        min_len: 最小长度
        max_len: 最大长度
        field_name: 字段名称
        
    Returns:
        (is_valid, errors)
    """
    errors = []
    
    if not value:
        if min_len > 0:
            errors.append(f'{field_name}不能为空')
        return (len(errors) == 0, errors)
    
    length = len(value)
    if length < min_len:
        errors.append(f'{field_name}至少需要{min_len}个字符')
    if length > max_len:
        errors.append(f'{field_name}不能超过{max_len}个字符')
    
    return (len(errors) == 0, errors)
