#!/usr/bin/env python3
"""
使用自定义的 Git 管理器初始化仓库

import os
import sys
import logging

# 添加项目根目录到 Python 路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def main():
    """主函数"""
    try:
        # 导入 Git 管理器
        import sys
        from app.services.git_manager import git_manager

        # 初始化仓库
        logger.info("初始化 Git 仓库...")
        result = git_manager.init_repo()
        logger.info(f"初始化结果: {result}")

        # 查看仓库状态
        logger.info("查看仓库状态...")
        status = git_manager.status()
        logger.info(f"仓库状态: {status}")

        # 添加文件到暂存区
        logger.info("添加文件到暂存区...")
        add_result = git_manager.add()
        logger.info(f"添加结果: {add_result}")

        # 提交更改
        logger.info("提交更改...")
        commit_result = git_manager.commit("Initial commit")
        logger.info(f"提交结果: {commit_result}")

        # 查看提交日志
        logger.info("查看提交日志...")
        log_result = git_manager.log(5)
        logger.info(f"提交日志: {log_result}")

        logger.info("Git 仓库初始化完成！")

    except Exception as e:
        logger.error(f"初始化 Git 仓库失败: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
