#!/usr/bin/env python3
"""
修复instances.py文件中的死锁问题，避免在get_ai_instance方法中直接访问sandbox_manager
"""
import os

# 获取instances.py文件的完整路径
file_path = os.path.join(os.path.dirname(__file__), 'app', 'ai', 'instances.py')

print(f"正在修复文件: {file_path}")

# 读取文件内容
try:
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    print("文件读取成功")
except Exception as e:
    print(f"文件读取失败: {e}")
    exit(1)

# 替换get_ai_instance方法中的问题代码
old_code = '''    def get_ai_instance(self, instance_id):
        """获取AI实例"""
        with self.instance_lock:
            instance = self.ai_instances.get(instance_id)
            if instance:
                # 更新最后使用时间
                instance['last_used'] = time.time()
                
                # 如果沙盒功能已启用，更新沙盒信息
                if sandbox_manager.is_sandbox_enabled() and 'sandbox' in instance:
                    sandbox = sandbox_manager.get_sandbox(instance_id)
                    instance['sandbox'] = sandbox
            return instance'''

new_code = '''    def get_ai_instance(self, instance_id):
        """获取AI实例"""
        with self.instance_lock:
            instance = self.ai_instances.get(instance_id)
            if instance:
                # 更新最后使用时间
                instance['last_used'] = time.time()
                
                # 移除直接的sandbox_manager依赖，避免死锁
                # 沙盒信息将在需要时由调用者更新
            return instance'''

# 替换代码
fixed_content = content.replace(old_code, new_code)

# 写入修改后的内容
try:
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(fixed_content)
    print("文件写入成功")
except Exception as e:
    print(f"文件写入失败: {e}")
    exit(1)

print("修复完成！")

# 重启服务器
print("正在重启服务器...")
os.system("pkill -f 'python3 start_server.py'")
os.system("nohup python3 start_server.py > server.log 2>&1 &")
print("服务器已重启，请查看server.log获取更多信息")
