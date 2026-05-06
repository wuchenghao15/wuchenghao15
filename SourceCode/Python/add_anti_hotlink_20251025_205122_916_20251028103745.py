# -*- coding: utf-8 -*-
# 上次更新: 2025-10-26 16:53:16
#!/usr/bin/env python3
"""
为所有HTML页面添加防盗链脚本引用
"""
import os
import re
import logging
from datetime import datetime

# 设置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(f"Logs/anti_hotlink_update_{datetime.now().strftime('%Y-%m-%d_%H-%M-%S')}.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# 要添加的防盗链脚本引用
ANTI_HOTLINK_SCRIPT = '<script src="../MyScript/anti_hotlink.js"></script>'

# 查找的模式（在<head>标签内，最后一个</head>标签前插入）
HEAD_PATTERN = re.compile(r'(</head>)', re.IGNORECASE)

# 需要处理的HTML文件列表
HTML_FILES = [
    # MyPages目录下的HTML文件
    'MyPages/403.html',
    'MyPages/404.html',
    'MyPages/Arduino·.html',
    'MyPages/PasswordReset.html',
    'MyPages/UpdateInfo.html',
    'MyPages/dashboard.html',
    'MyPages/index.html',
    'MyPages/register.html',
    'MyPages/server.html',
    'MyPages/settings.html',
    'MyPages/test_verification.html',
    # deploy_site/MyPages目录下的HTML文件
    'deploy_site/MyPages/403.html',
    'deploy_site/MyPages/404.html',
    'deploy_site/MyPages/PasswordReset.html',
    'deploy_site/MyPages/UpdateInfo.html',
    'deploy_site/MyPages/dashboard.html',
    'deploy_site/MyPages/index.html',
    'deploy_site/MyPages/register.html',
    'deploy_site/MyPages/server.html',
    'deploy_site/MyPages/test_verification.html',
    'deploy_site/index.html'
]

    """
    """
        # 读取文件内容
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()

        # 检查是否已经添加了防盗链脚本
        if ANTI_HOTLINK_SCRIPT in content:
            logger.info(f'文件 {file_path} 已经包含防盗链脚本引用，跳过')
            return False

        # 替换</head>标签，在其前插入防盗链脚本
        modified_content = HEAD_PATTERN.sub(f'{ANTI_HOTLINK_SCRIPT}\n\1', content)

        # 写入修改后的内容
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(modified_content)

        logger.info(f'成功为文件 {file_path} 添加防盗链脚本引用')
        return True
    except Exception as e:
        logger.error(f'处理文件 {file_path} 时出错: {str(e)}')
        return False

def main():
    """
    """
    success_count = 0
    skip_count = 0
    error_count = 0

    for html_file in HTML_FILES:
        full_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), html_file)
        if os.path.exists(full_path):
            if add_anti_hotlink_to_html(full_path):
                success_count += 1
            else:
                skip_count += 1
        else:
            logger.warning(f'文件 {html_file} 不存在，跳过')
            error_count += 1

    logger.info(f'防盗链脚本引用添加完成')
    logger.info(f'成功: {success_count}, 跳过: {skip_count}, 错误: {error_count}')

if __name__ == '__main__':
