#!/usr/bin/env python3
"""
上传项目到飞牛Nas，支持双重设备认证

import pexpect
import sys
import os

def upload_to_nas():
    """上传文件到飞牛Nas"""

    # 服务器信息
    host = "wuchenghao15.fnos.net"
    username = "wuchenghao15"
    password = "!+.4457KKZbchno"
    local_file = "MTSCOS_AI_Project.tar.gz"
    remote_path = "~/"

    print(f"开始上传文件到飞牛Nas: {host}")
    print(f"本地文件: {local_file}")
    print(f"远程路径: {remote_path}")

    # 构建 scp 命令
    cmd = f"scp -o StrictHostKeyChecking=no {local_file} {username}@{host}:{remote_path}"

    try:
        # 启动子进程
        child = pexpect.spawn(cmd, timeout=300)

        # 等待密码提示
        index = child.expect(["password:", "Password:", pexpect.EOF, pexpect.TIMEOUT], timeout=10)

        if index in [0, 1]:
            print("输入密码...")
            child.sendline(password)

            # 等待可能的二次认证提示
            index2 = child.expect([
                "Verification code:",  # 认证码提示
                "verification code:",
                "Two-factor",
                "two-factor",
                "success",  # 上传成功
                "100%",     # 上传进度完成
                pexpect.EOF,
                pexpect.TIMEOUT
            ], timeout=60)

            if index2 in [0, 1, 2, 3]:
                # 需要双重认证码
                print("\n" + "="*50)
                print("需要双重设备认证！")
                print("请检查您的认证设备（手机/邮箱）获取认证码")
                print("="*50)

                # 提示用户输入认证码
                auth_code = input("请输入认证码: ").strip()

                if auth_code:
                    child.sendline(auth_code)
                    print("已发送认证码，等待上传完成...")
                else:
                    print("未输入认证码，取消上传")
                    child.close()
                    return False

            # 等待上传完成
            child.expect(pexpect.EOF, timeout=300)

        # 获取输出
        output = child.before.decode('utf-8', errors='ignore') if child.before else ""

        # 检查是否成功
        if child.exitstatus == 0:
            print("\n" + "="*50)
            print(f"文件已上传到: {remote_path}{local_file}")
            print("="*50)
            return True
            print(f"\n✗ 上传失败，退出码: {child.exitstatus}")
            if output:
            return False

    except pexpect.exceptions.TIMEOUT:
        print("\n✗ 连接超时，请检查网络连接")
    except Exception as e:
        print(f"\n✗ 上传过程中出错: {str(e)}")
        import traceback
        return False

if __name__ == "__main__":
    success = upload_to_nas()
