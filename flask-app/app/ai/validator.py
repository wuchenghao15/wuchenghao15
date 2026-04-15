import re
import logging
from app.utils.logging import logger

class ValidatorAI:
    """数据验证AI，负责数据验证和格式检查"""
    
    def __init__(self):
        self.instance_id = f"validator_ai_{id(self)}"
        self.name = "数据验证AI"
        self.description = "负责数据验证和格式检查"
        self.logger = logger
        self.logger.info(f"初始化数据验证AI: {self.instance_id}")
    
    def validate_data(self, data, schema):
        """根据schema验证数据"""
        try:
            self.logger.info(f"{self.instance_id} 正在验证数据")
            
            errors = []
            
            # 遍历schema中的每个字段
            for field, field_schema in schema.items():
                # 检查必填字段
                if field_schema.get("required", False) and field not in data:
                    errors.append(f"字段 '{field}' 是必填项")
                    continue
                
                # 如果字段存在，验证类型和其他约束
                if field in data:
                    field_value = data[field]
                    
                    # 验证类型
                    expected_type = field_schema.get("type")
                    if expected_type:
                        if not self._validate_type(field_value, expected_type):
                            errors.append(f"字段 '{field}' 类型错误，期望 '{expected_type}'")
                            continue
                    
                    # 验证最小值
                    if "min" in field_schema and isinstance(field_value, (int, float)):
                        if field_value < field_schema["min"]:
                            errors.append(f"字段 '{field}' 必须大于等于 {field_schema['min']}")
                    
                    # 验证最大值
                    if "max" in field_schema and isinstance(field_value, (int, float)):
                        if field_value > field_schema["max"]:
                            errors.append(f"字段 '{field}' 必须小于等于 {field_schema['max']}")
                    
                    # 验证最小长度
                    if "min_length" in field_schema and isinstance(field_value, str):
                        if len(field_value) < field_schema["min_length"]:
                            errors.append(f"字段 '{field}' 长度必须大于等于 {field_schema['min_length']}")
                    
                    # 验证最大长度
                    if "max_length" in field_schema and isinstance(field_value, str):
                        if len(field_value) > field_schema["max_length"]:
                            errors.append(f"字段 '{field}' 长度必须小于等于 {field_schema['max_length']}")
                    
                    # 验证正则表达式
                    if "pattern" in field_schema and isinstance(field_value, str):
                        if not re.match(field_schema["pattern"], field_value):
                            errors.append(f"字段 '{field}' 格式错误")
                    
                    # 验证枚举值
                    if "enum" in field_schema:
                        if field_value not in field_schema["enum"]:
                            errors.append(f"字段 '{field}' 必须是以下值之一: {', '.join(map(str, field_schema['enum']))}")
            
            if errors:
                self.logger.warning(f"{self.instance_id} 数据验证失败: {', '.join(errors)}")
                return {
                    "success": False,
                    "errors": errors
                }
            
            self.logger.info(f"{self.instance_id} 数据验证成功")
            return {
                "success": True,
                "errors": []
            }
        except Exception as e:
            self.logger.error(f"{self.instance_id} 数据验证失败: {str(e)}")
            return {
                "success": False,
                "errors": [f"验证过程中发生错误: {str(e)}"]
            }
    
    def check_format(self, value, format_type):
        """检查值的格式"""
        try:
            self.logger.info(f"{self.instance_id} 正在检查格式: {format_type}")
            
            format_checks = {
                "email": self._is_valid_email,
                "password": self._is_valid_password,
                "username": self._is_valid_username,
                "url": self._is_valid_url,
                "phone": self._is_valid_phone,
                "date": self._is_valid_date
            }
            
            if format_type not in format_checks:
                self.logger.warning(f"{self.instance_id} 未知的格式类型: {format_type}")
                return False
            
            result = format_checks[format_type](value)
            self.logger.info(f"{self.instance_id} 格式检查{'通过' if result else '失败'}: {format_type}")
            return result
        except Exception as e:
            self.logger.error(f"{self.instance_id} 格式检查失败: {str(e)}")
            return False
    
    def sanitize_input(self, input_data, sanitize_rules=None):
        """净化输入数据"""
        try:
            self.logger.info(f"{self.instance_id} 正在净化输入数据")
            
            if isinstance(input_data, str):
                return self._sanitize_string(input_data)
            elif isinstance(input_data, dict):
                sanitized_dict = {}
                for key, value in input_data.items():
                    sanitized_dict[key] = self.sanitize_input(value)
                return sanitized_dict
            elif isinstance(input_data, list):
                return [self.sanitize_input(item) for item in input_data]
            else:
                return input_data
        except Exception as e:
            self.logger.error(f"{self.instance_id} 输入净化失败: {str(e)}")
            return input_data
    
    def _validate_type(self, value, expected_type):
        """验证值的类型"""
        if expected_type == "string":
            return isinstance(value, str)
        elif expected_type == "int":
            return isinstance(value, int)
        elif expected_type == "float":
            return isinstance(value, float)
        elif expected_type == "bool":
            return isinstance(value, bool)
        elif expected_type == "list":
            return isinstance(value, list)
        elif expected_type == "dict":
            return isinstance(value, dict)
        elif expected_type == "null":
            return value is None
        return True
    
    def _is_valid_email(self, email):
        """验证邮箱格式"""
        email_pattern = r"^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$"
        return re.match(email_pattern, email) is not None
    
    def _is_valid_password(self, password):
        """验证密码强度"""
        # 至少8个字符，包含大小写字母和数字
        password_pattern = r"^(?=.*[a-z])(?=.*[A-Z])(?=.*\d).{8,}$"
        return re.match(password_pattern, password) is not None
    
    def _is_valid_username(self, username):
        """验证用户名格式"""
        # 3-20个字符，只能包含字母、数字和下划线
        username_pattern = r"^[a-zA-Z0-9_]{3,20}$"
        return re.match(username_pattern, username) is not None
    
    def _is_valid_url(self, url):
        """验证URL格式"""
        url_pattern = r"^(https?:\/\/)?([\da-z.-]+)\.([a-z.]{2,6})([\/\w .-]*)*\/?$"
        return re.match(url_pattern, url) is not None
    
    def _is_valid_phone(self, phone):
        """验证手机号码格式"""
        # 简单的手机号码验证，支持国际格式
        phone_pattern = r"^\+?[1-9]\d{1,14}$"
        return re.match(phone_pattern, phone) is not None
    
    def _is_valid_date(self, date):
        """验证日期格式"""
        # 支持YYYY-MM-DD格式
        date_pattern = r"^\d{4}-\d{2}-\d{2}$"
        return re.match(date_pattern, date) is not None
    
    def _sanitize_string(self, string):
        """净化字符串，防止XSS攻击"""
        # 替换危险字符
        replacements = {
            "<": "&lt;",
            ">": "&gt;",
            "&": "&amp;",
            "\"": "&quot;",
            "'": "&#x27;",
            "/": "&#x2F;"
        }
        
        sanitized = string
        for char, replacement in replacements.items():
            sanitized = sanitized.replace(char, replacement)
        
        return sanitized
    
    def __str__(self):
        return f"ValidatorAI(instance_id={self.instance_id}, name={self.name})"
    
    def __repr__(self):
        return self.__str__()

# 创建全局数据验证AI实例
validator_ai = ValidatorAI()