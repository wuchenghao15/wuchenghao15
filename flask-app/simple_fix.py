#!/usr/bin/env python3
"""
简化版修复脚本，直接修改learning.py文件，解决MODEL_PATH KeyError问题
"""
import os

# 获取learning.py文件的完整路径
file_path = os.path.join(os.path.dirname(__file__), 'app', 'ai', 'learning.py')

def main():
    print(f"正在修复文件: {file_path}")
    
    # 创建一个简单的替换脚本
    fix_script = """
import sys
import os

# 读取文件
with open(sys.argv[1], 'r') as f:
    content = f.read()

# 全局替换所有的['MODEL_PATH']为.get('MODEL_PATH', os.environ.get('MODEL_PATH', 'models/'))
fixed_content = content.replace("['MODEL_PATH']", ".get('MODEL_PATH', os.environ.get('MODEL_PATH', 'models/'))")

# 写入文件
with open(sys.argv[1], 'w') as f:
    f.write(fixed_content)

print("修复完成！")
"""
    
    # 写入临时脚本
    temp_script = "fix_temp.py"
    with open(temp_script, 'w') as f:
        f.write(fix_script)
    
    # 运行临时脚本
    os.system(f"python3 {temp_script} {file_path}")
    
    # 清理临时脚本
    os.remove(temp_script)
    
    print("修复完成！")
    
    # 重启服务器
    print("正在重启服务器...")
    os.system("pkill -f 'python3 start_server.py'")
    os.system("nohup python3 start_server.py > server.log 2>&1 &")
    print("服务器已重启，请查看server.log获取更多信息")

if __name__ == "__main__":
    main()
