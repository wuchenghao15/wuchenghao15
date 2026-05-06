# -*- coding: utf-8 -*-
# 上次更新: 2025-10-26 16:53:21
#!/usr/bin/env python3
"""
MSSQL数据库环境设置脚本
用于测试数据库连接和配置连接字符串

import os
import sys
import time
from datetime import datetime

# 设置日志函数
def log(message, level="INFO"):
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{timestamp}] [{level}] {message}")

    # 写入日志文件
    log_dir = "Logs"
    os.makedirs(log_dir, exist_ok=True)
    log_file = os.path.join(log_dir, "mssql_setup.log")
    with open(log_file, "a", encoding="utf-8") as f:
        f.write(f"[{timestamp}] [{level}] {message}\n")

def check_pyodbc():
    """检查pyodbc模块是否已安装"""
    try:
        import pyodbc
        log("pyodbc模块已安装")
        return True
    except ImportError:
        log("pyodbc模块未安装，请安装pyodbc: pip install pyodbc", "WARNING")
        return False

def test_connection(conn_str):
    """测试数据库连接"""
    if not check_pyodbc():
        return False
    import pyodbc
        conn = pyodbc.connect(conn_str)
        cursor = conn.cursor()
        cursor.execute("SELECT @@VERSION")
        row = cursor.fetchone()
        log(f"成功连接到数据库！SQL Server版本: {row[0][:100]}...")
        cursor.close()
        conn.close()
        return True
    except Exception as e:
        log(f"数据库连接失败: {str(e)}", "ERROR")

def update_connection_string(local=True):
    """更新数据库连接字符串配置文件"""

    if local:
        # 本地数据库连接信息
        server = "localhost"
        port = "33693"
        log("使用本地MSSQL数据库配置")
    else:
        # 远程数据库连接信息
        server = "wuchenghao15.xicp.net"
        port = "33693"
        log("使用远程MSSQL数据库配置")

    # 连接参数
    username = "sa"
    password = "LoginMe15"

    # 创建连接字符串
    connection_strings = {
        "sqlserver": f"Server={server},{port};Database={database};User Id={username};Password={password};Encrypt=False;TrustServerCertificate=True;",
        "odbc": f"DRIVER={{ODBC Driver 17 for SQL Server}};SERVER={server},{port};DATABASE={database};UID={username};PWD={password};",
        "jdbc": f"jdbc:sqlserver://{server}:{port};databaseName={database};user={username};password={password};encrypt=false;trustServerCertificate=true;",
        "adonet": f"Server={server},{port};Database={database};User ID={username};Password={password};Trusted_Connection=False;Encrypt=False;"
    }

    # 写入配置文件
    try:
        with open(config_file, "w", encoding="utf-8") as f:
            f.write(f"# MTSCOS 数据库连接配置\n")
            f.write(f"# 生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")

            f.write("# SQLSERVER 连接字符串\n")
            f.write(f"{connection_strings['sqlserver']}\n\n")

            f.write("# ODBC 连接字符串\n")
            f.write(f"{connection_strings['odbc']}\n\n")

            f.write("# JDBC 连接字符串\n")
            f.write(f"{connection_strings['jdbc']}\n\n")

            f.write("# ADONET 连接字符串\n")
            f.write(f"{connection_strings['adonet']}\n")

        log(f"数据库连接配置已更新: {config_file}")
        return connection_strings
    except Exception as e:
        log(f"更新数据库配置文件失败: {str(e)}", "ERROR")
        return None

def display_setup_instructions():
    """显示MSSQL数据库安装指南"""
    log("\n===== MSSQL数据库环境设置指南 =====", "INFO")
    log("", "INFO")
    log("方法1: 使用Docker部署本地MSSQL（推荐）", "INFO")
    log("1. 安装Docker Desktop: https://www.docker.com/products/docker-desktop", "INFO")
    log("2. 启动Docker Desktop", "INFO")
    log("3. 运行: docker-compose up -d", "INFO")
    log("4. 检查服务状态: docker-compose ps", "INFO")
    log("", "INFO")
    log("方法2: 使用已配置的远程MSSQL服务器", "INFO")
    log("- 服务器: wuchenghao15.xicp.net", "INFO")
    log("- 端口: 33693", "INFO")
    log("- 用户名: sa", "INFO")
    log("- 密码: LoginMe15", "INFO")
    log("- 数据库: MyData, MyCode", "INFO")
    log("", "INFO")
    log("1. 下载SQL Server: https://www.microsoft.com/en-us/sql-server/sql-server-downloads", "INFO")
    log("2. 安装时设置密码为: LoginMe15", "INFO")
    log("3. 启用TCP/IP协议并设置端口为33693", "INFO")
    log("4. 运行此脚本更新连接配置", "INFO")
    log("\n====================================\n", "INFO")

    """主函数"""
    log("开始MSSQL数据库环境设置...")

    # 显示设置指南
    display_setup_instructions()

    # 检查Docker是否可用
    try:
        result = subprocess.run(["docker", "--version"], capture_output=True, text=True)
        if result.returncode == 0:
            log(f"Docker已安装: {result.stdout.strip()}")
            log("可以使用docker-compose部署MSSQL数据库")
            log("运行: docker-compose up -d 来启动数据库服务")
        else:
            log("Docker未安装，请按照指南安装Docker或使用其他方法", "WARNING")
    except Exception as e:
        log(f"检查Docker时出错: {str(e)}", "WARNING")

    # 提示用户选择配置类型
    print("\n请选择数据库配置类型:")
    print("1. 本地MSSQL数据库（Docker部署）")
    print("2. 远程MSSQL数据库（wuchenghao15.xicp.net）")
    try:
        use_local = choice == "1"

        # 更新连接配置
        conn_strings = update_connection_string(use_local)
        if conn_strings:
            # 测试连接
            test_connection(conn_strings['odbc'])

            log("数据库环境设置完成！")
            log("请确保数据库服务已启动并可访问")
    except KeyboardInterrupt:
        log("用户取消了操作", "INFO")
    except Exception as e:
        log(f"设置过程中发生错误: {str(e)}", "ERROR")

if __name__ == "__main__":
    main()
