#!/usr/bin/env python3
"""
测试服务器状态并查看server.log文件
import requests
import time
import os

def main():
    print("正在测试服务器状态...")
    time.sleep(3)  # 等待服务器启动

    try:
        response = requests.get('http://localhost:8888')
        print('✅ 服务器已成功启动！')
        print(f'状态码: {response.status_code}')
        print(f'响应内容: {response.text[:200]}...')
    except Exception as e:
        print(f'❌ 服务器未启动或无法访问: {e}')
        print('\n查看server.log文件了解详情:')
        os.system('tail -20 server.log')

if __name__ == "__main__":
    main()

"""