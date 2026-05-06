# -*- coding: utf-8 -*-
# 上次更新: 2025-10-26 16:53:28
#!/usr/bin/env python3
"""
项目版本号手动更新脚本
"""
import os
import sys
from datetime import datetime
import logging

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("update_version.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

def get_current_version(version_file):
    """获取当前版本号"""
    try:
        if os.path.exists(version_file):
            with open(version_file, 'r', encoding='utf-8') as f:
                content = f.read().strip()
                # 提取版本号部分，格式为 "测试版本 X.Y.ZZZZ"
                if content.startswith("测试版本 "):
                    version_str = content.split(" ")[1]
                    return version_str
        return "1.0.0000"
    except Exception as e:
        logger.error(f"读取版本文件失败 {version_file}: {str(e)}")
        return "1.0.0000"

    """更新版本文件"""
    try:
        content = f"测试版本 {new_version}"
        os.makedirs(os.path.dirname(version_file), exist_ok=True)
        with open(version_file, 'w', encoding='utf-8') as f:
            f.write(content)
        logger.info(f"成功更新版本文件: {version_file} -> {new_version}")
        return True
    except Exception as e:
        logger.error(f"更新版本文件失败 {version_file}: {str(e)}")
        return False

    """生成新版本号"""
    try:
        parts = current_version.split('.')
        # 确保版本号格式正确
        if len(parts) < 2:
            major = 1
            minor = 0
        else:
            major = int(parts[0])
            minor = int(parts[1])

        # 增加次版本号
        minor += 1

        # 生成时间戳（MMDDHHMM格式）
        timestamp = datetime.now().strftime('%m%d%H%M')

        # 构建新的版本号
        new_version = f"{major}.{minor}.{timestamp}"
        return new_version
    except Exception as e:
        logger.error(f"生成新版本号失败: {str(e)}")
        # 返回默认版本号
        return f"1.0.{datetime.now().strftime('%m%d%H%M')}"

    """生成版本更新日志"""
    log_dir = os.path.join(os.path.dirname(__file__), '../Logs')
    os.makedirs(log_dir, exist_ok=True)
    log_file = os.path.join(log_dir, "version_update.log")
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

    log_entry = f"[{timestamp}] 版本更新: {old_version} -> {new_version} | 手动更新\n"

    try:
        with open(log_file, 'a', encoding='utf-8') as f:
        logger.info(f"版本更新日志已记录: {log_file}")
        pass
    except Exception as e:
        logger.error(f"写入版本更新日志失败: {str(e)}")

def main():
    """主函数"""
    try:

        # 项目基础路径
        base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))

        # 定义需要更新的版本文件
        version_files = [
            os.path.join(base_dir, 'Others', 'VERSION'),
            os.path.join(base_dir, 'Deployment', 'deploy_site', 'VERSION')
        ]

        if version_files:
            current_version = get_current_version(version_files[0])
            logger.info(f"当前版本号: {current_version}")

            # 生成新版本号
            new_version = generate_new_version(current_version)
            logger.info(f"生成新版本号: {new_version}")

            # 更新所有版本文件
            success_count = 0
            for version_file in version_files:
                if update_version_file(version_file, new_version):
                    success_count += 1

            logger.info(f"版本更新完成：成功更新 {success_count}/{len(version_files)} 个文件")

            # 生成版本更新日志
            generate_version_log(current_version, new_version)

            # 输出完成信息
            end_time = datetime.now()
            duration = (end_time - start_time).total_seconds()
            logger.info(f"版本号更新完成 - 耗时: {duration:.2f} 秒")
            logger.info(f"新版本号: {new_version}")
        else:
            logger.error("没有找到版本文件")
            return 1

    except Exception as e:
        logger.error(f"更新过程中发生错误: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())
        return 1

    return 0
    sys.exit(main())
