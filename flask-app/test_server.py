#!/usr/bin/env python3
"""
测试服务器是否在端口8888上正常运行
"""

import requests
import time

def test_server():
    """测试服务器是否在端口8888上正常运行"""
    url = "http://localhost:8888"
    
    print(f"[测试] 正在检查服务器 {url}...")
    
    try:
        # 发送GET请求到根路径
        response = requests.get(url, timeout=5)
        
        # 检查响应状态码
        if response.status_code == 200:
            print(f"[成功] 服务器响应正常！状态码: {response.status_code}")
            print(f"[成功] 响应内容长度: {len(response.text)} 字节")
            print(f"[成功] 服务器正在端口8888上运行")
            return True
        else:
            print(f"[警告] 服务器响应状态码: {response.status_code}")
            print(f"[警告] 响应内容: {response.text[:100]}...")
            return False
    except requests.ConnectionError:
        print(f"[失败] 无法连接到服务器 {url}，服务器可能未启动或端口未开放")
        return False
    except requests.Timeout:
        print(f"[失败] 连接服务器 {url} 超时")
        return False
    except Exception as e:
        print(f"[失败] 测试服务器时发生错误: {str(e)}")
        return False

if __name__ == "__main__":
    print("=== 服务器测试脚本 ===")
    
    # 尝试3次连接
    for i in range(3):
        print(f"\n尝试第 {i+1}/3 次...")
        if test_server():
            break
        else:
            print(f"等待2秒后重试...")
            time.sleep(2)
    
    print("\n=== 测试完成 ===")
