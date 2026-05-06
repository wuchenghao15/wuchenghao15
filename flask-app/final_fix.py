#!/usr/bin/env python3
"""
最终修复脚本，直接修改learning.py文件，解决MODEL_PATH KeyError问题
import os
import tempfile

# 获取learning.py文件的完整路径
file_path = os.path.join(os.path.dirname(__file__), 'app', 'ai', 'learning.py')
temp_file_path = file_path + '.tmp'

print(f"正在修复文件: {file_path}")

try:
    # 读取文件内容
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    print("文件读取成功")

    # 查找第16行
    lines = content.split('\n')
    if len(lines) >= 16:
        print(f"第16行内容: {lines[15]}")

        # 将config['MODEL_PATH']替换为安全访问方式
        if "config['MODEL_PATH']" in lines[15]:
            lines[15] = lines[15].replace("config['MODEL_PATH']", "config.get('MODEL_PATH', os.environ.get('MODEL_PATH', 'models/'))")
            print(f"修复后的第16行: {lines[15]}")
        elif "config["'MODEL_PATH'""]" in lines[15]:
            lines[15] = lines[15].replace("config["'MODEL_PATH'""]", "config.get('MODEL_PATH', os.environ.get('MODEL_PATH', 'models/'))")
            print(f"修复后的第16行: {lines[15]}")
            print("未找到直接的MODEL_PATH访问，尝试全局替换")
            for i, line in enumerate(lines):
                if "['MODEL_PATH']" in line:
                    lines[i] = line.replace("['MODEL_PATH']", ".get('MODEL_PATH', os.environ.get('MODEL_PATH', 'models/'))")
                    print(f"修复了第{i+1}行: {lines[i]}")

    # 添加必要的导入
    if "import os" not in lines[0:10]:
        # 在文件开头添加import os
        lines.insert(0, "import os")
        print("已添加import os")

    # 写入临时文件
    with open(temp_file_path, 'w', encoding='utf-8') as f:
        f.write('\n'.join(lines))
    print(f"临时文件写入成功: {temp_file_path}")

    # 替换原文件
    os.replace(temp_file_path, file_path)
    print("原文件已替换")

    print("修复完成！")

    # 重启服务器
    print("正在重启服务器...")
    os.system("pkill -f 'python3 start_server.py'")
    os.system("nohup python3 start_server.py > server.log 2>&1 &")
    print("服务器已重启，请查看server.log获取更多信息")

except Exception as e:
    print(f"修复失败: {e}")
    import traceback
    traceback.print_exc()
    # 清理临时文件
    if os.path.exists(temp_file_path):
        os.remove(temp_file_path)
    exit(1)

"""