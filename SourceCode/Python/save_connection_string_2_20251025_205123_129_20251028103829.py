# -*- coding: utf-8 -*-
# 上次更新: 2025-10-26 16:53:27
import os
import datetime
import re
import hashlib

# MD5加密函数
def md5_hash(string):
    """对字符串进行MD5加密"""
    return hashlib.md5(string.encode()).hexdigest()

# 检查字符串是否已被MD5加密
def is_md5_hash(string):
    """检查字符串是否为有效的MD5哈希值"""
    return bool(re.match(r'^[0-9a-f]{32}$', string.lower()))

def sanitize_connection_param(param, param_type):
    """清理连接字符串参数，防止SQL注入攻击"""
    if not param:
        return ''

    clean_param = str(param).strip()

    # 根据参数类型应用不同的清理规则
    if param_type == 'server_address':
        # 允许IP地址或域名格式
        ip_pattern = r'^([0-9]{1,3}\.){3}[0-9]{1,3}$'
        domain_pattern = r'^[a-zA-Z0-9][a-zA-Z0-9-]{0,61}[a-zA-Z0-9](?:\.[a-zA-Z]{2,})+$'
        if not re.match(ip_pattern, clean_param) and not re.match(domain_pattern, clean_param):
            print(f"安全警告: 无效的服务器地址格式: {param}")
            return ''
    elif param_type == 'server_port':
        # 验证端口号是有效的数字
        try:
            port_num = int(clean_param)
            if port_num < 1 or port_num > 65535:
                print(f"安全警告: 无效的端口号: {param}")
                return '3306'  # 默认端口
            clean_param = str(port_num)
        except ValueError:
            print(f"安全警告: 无效的端口号: {param}")
            return '3306'  # 默认端口
    elif param_type in ['db_username', 'database_name']:
        invalid_chars = r'[^a-zA-Z0-9_@#$%^&*()-+=. ]'
        clean_param = re.sub(invalid_chars, '', clean_param)

        # 检查是否包含SQL关键字
        sql_keywords = ['exec', 'execute', 'sp_', 'xp_', 'drop', 'alter', 'truncate']
        for keyword in sql_keywords:
            if keyword in clean_param.lower():
                print(f"安全警告: 检测到可能的SQL关键字: {keyword} 在参数中")
                # 替换关键字
                clean_param = clean_param.lower().replace(keyword, '*' * len(keyword))

        # 限制长度
        if len(clean_param) > 100:
            clean_param = clean_param[:100]

    elif param_type == 'db_password':
        # 密码通常不需要特别限制格式，但可以限制长度
        if len(clean_param) > 200:
            print("安全警告: 密码长度超过限制")
            clean_param = clean_param[:200]

        # 对密码进行MD5加密（如果尚未加密）
        if not is_md5_hash(clean_param):
            clean_param = md5_hash(clean_param)

    return clean_param

def validate_connection_params(config):
    """验证连接字符串参数"""
    if not config or not isinstance(config, dict):
        print("配置参数无效")
        return False

    required_params = ['server_address', 'database_name']
    for param in required_params:
        if param not in config or not config[param]:
            print(f"{param}是必需的参数")
            return False

    return True

db_config = {
    'server_address': 'wuchenghao15.xicp.net',
    'server_port': '33693',
    'db_username': 'sa',
    'db_password': '1e6e3e275c078986a9f5d77a0c5d452c',  # MD5加密后的'LoginMe15'
    'database_name': 'MyData',
    'db_charset': 'utf8mb4'
}

def generate_connection_strings(config):
    """生成不同类型的数据库连接字符串"""
    # 验证配置参数
    if not validate_connection_params(config):
        raise ValueError("无效的数据库配置参数")

    # 清理所有参数
    clean_config = {
        'server_address': sanitize_connection_param(config['server_address'], 'server_address'),
        'server_port': sanitize_connection_param(config.get('server_port', '3306'), 'server_port'),
        'db_username': sanitize_connection_param(config.get('db_username', ''), 'db_username'),
        'db_password': sanitize_connection_param(config.get('db_password', ''), 'db_password'),
        'database_name': sanitize_connection_param(config['database_name'], 'database_name'),
        'db_charset': config.get('db_charset', 'utf8mb4')
    }

    # 记录安全的连接字符串信息（不包含密码）
    print(f"生成连接字符串: Server={clean_config['server_address']},{clean_config['server_port']};Database={clean_config['database_name']};User Id={clean_config['db_username']};")

    connection_strings = {
        # SQL Server 连接字符串
        'sqlServer': f"Server={clean_config['server_address']},{clean_config['server_port']};Database={clean_config['database_name']};User Id={clean_config['db_username']};Password={clean_config['db_password']};Encrypt=False;TrustServerCertificate=True;",
        # ODBC 连接字符串
        'odbc': f"DRIVER={{ODBC Driver 17 for SQL Server}};SERVER={clean_config['server_address']},{clean_config['server_port']};DATABASE={clean_config['database_name']};UID={clean_config['db_username']};PWD={clean_config['db_password']};",
        # JDBC 连接字符串
        'jdbc': f"jdbc:sqlserver://{clean_config['server_address']}:{clean_config['server_port']};databaseName={clean_config['database_name']};user={clean_config['db_username']};password={clean_config['db_password']};encrypt=false;trustServerCertificate=true;",
        # ADO.NET 连接字符串
        'adoNet': f"Server={clean_config['server_address']},{clean_config['server_port']};Database={clean_config['database_name']};User ID={clean_config['db_username']};Password={clean_config['db_password']};Trusted_Connection=False;Encrypt=False;"
    }

    return connection_strings

def save_connection_string_to_file():
    try:
        connection_strings = generate_connection_strings(db_config)
        # 创建文件内容
        file_content = '# MTSCOS 数据库连接配置\n'
        file_content += f'# 生成时间: {datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")}\n\n'
        file_content += '# 安全提示：请妥善保管此文件，不要与他人共享\n'
        file_content += '# 此文件包含敏感信息，请确保权限设置正确\n\n'

        # 添加所有连接字符串类型
        for key, value in connection_strings.items():
            file_content += f'# {key.upper()} 连接字符串\n'
            file_content += f'{value}\n\n'

        # 确保MyData目录存在
        my_data_dir = os.path.join(os.path.dirname(__file__), '../MyData')
        if not os.path.exists(my_data_dir):
            os.makedirs(my_data_dir)

        # 写入文件
        file_path = os.path.join(my_data_dir, 'db_connection_string.txt')
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(file_content)

        print(f"连接字符串已成功保存到: {file_path}")
    except Exception as e:
        print(f"保存连接字符串失败: {str(e)}")

if __name__ == "__main__":
    save_connection_string_to_file()
