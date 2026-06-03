# -*- coding: utf-8 -*-
#!/usr/bin/env python3
"""
用户注册器工具
只有通过此工具和首页前端注册的用户才视为合法用户
其他方式注册的用户将被标记为非法用户

import logging
logger = logging.getLogger(__name__)
import requests
import argparse
import sys
import json
import os

# 注册器的合法token
REGISTER_TOOL_TOKEN = "register_tool_legit_token"

# 注册API地址
REGISTER_API_URL = "http://localhost:8888/auth/register"

def register_user(username, password, email=None, role=None):
    使用注册器注册用户

    Args:
        username: 用户名
        password: 密码
        email: 邮箱(可选,自动生成如果不提供)
        role: 角色(可选,默认为user)

    Returns:
        dict: 注册结果
    # 如果没有提供邮箱,自动生成
    if not email:
        email = f"{username}@example.com"

    # 准备注册数据
    data = {
        "username": username,
        "password": password,
        "confirm_password": password,  # 注册器工具中密码和确认密码相同
        "email": email,
        "registration_token": REGISTER_TOOL_TOKEN
    }

    # 发送注册请求
    try:
        response = requests.post(REGISTER_API_URL, data=data)
        response.raise_for_status()  # 如果响应状态码不是200,抛出异常
        return response.json()
    except requests.exceptions.RequestException as e:
        return {"error": f"注册失败: {str(e)}"}

def main():
    主函数,处理命令行参数
    parser = argparse.ArgumentParser(description="用户注册器工具")
    parser.add_argument("username", help="用户名")
    parser.add_argument("password", help="密码")
    parser.add_argument("--email", help="邮箱(可选,自动生成如果不提供)")
    parser.add_argument("--role", help="角色(可选,默认为user)")

    args = parser.parse_args()

    # 调用注册函数
    result = register_user(args.username, args.password, args.email, args.role)

    # 打印注册结果
    print("注册结果:")
    for key, value in result.items():
        print(f"{key}: {value}")

    # 根据结果设置退出码
    if "error" in result:
        sys.exit(1)
    else:
        sys.exit(0)

if __name__ == "__main__":
    main()

"""