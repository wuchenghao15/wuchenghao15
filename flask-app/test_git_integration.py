#!/usr/bin/env python3
"""
测试 Git 集成功能

import time
import logging
from app.services.git_manager import git_manager
from app.services.distributed_server import distributed_server_manager

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_git_manager():
    """测试 Git 管理器"""
    logger.info("=== 测试 Git 管理器 ===")

    # 测试获取仓库信息
    start_time = time.time()
    try:
        repo_info = git_manager.get_repo_info()
        logger.info(f"仓库信息: {repo_info}")
        info_time = time.time() - start_time
        logger.info(f"获取仓库信息测试：耗时: {info_time:.4f}秒")
    except Exception as e:
        logger.error(f"获取仓库信息测试失败: {str(e)}")

    # 测试查看仓库状态
    start_time = time.time()
        status = git_manager.status()
        status_time = time.time() - start_time
        logger.info(f"查看仓库状态测试：耗时: {status_time:.4f}秒")
    except Exception as e:
        logger.error(f"查看仓库状态测试失败: {str(e)}")

    # 测试查看提交日志
    start_time = time.time()
        log = git_manager.log(5)
        logger.info(f"提交日志: {log}")
        logger.info(f"查看提交日志测试：耗时: {log_time:.4f}秒")
    except Exception as e:
        logger.error(f"查看提交日志测试失败: {str(e)}")

    # 测试查看分支
    start_time = time.time()
        branches = git_manager.branch()
        logger.info(f"分支: {branches}")
        branch_time = time.time() - start_time
    except Exception as e:
        logger.error(f"查看分支测试失败: {str(e)}")

    # 测试查看远程仓库
    start_time = time.time()
        remotes = git_manager.remote()
        logger.info(f"远程仓库: {remotes}")
        remote_time = time.time() - start_time
        logger.info(f"查看远程仓库测试：耗时: {remote_time:.4f}秒")
        logger.error(f"查看远程仓库测试失败: {str(e)}")

def test_distributed_server_git():
    """测试分布式服务器管理器的 Git 功能"""
    logger.info("=== 测试分布式服务器管理器的 Git 功能 ===")

    # 测试获取仓库信息
    try:
        logger.info(f"仓库信息: {repo_info}")
        info_time = time.time() - start_time
        logger.info(f"获取仓库信息测试：耗时: {info_time:.4f}秒")
    except Exception as e:
        logger.error(f"获取仓库信息测试失败: {str(e)}")
    # 测试查看仓库状态
    start_time = time.time()
    try:
        logger.info(f"仓库状态: {status}")
        status_time = time.time() - start_time
        logger.info(f"查看仓库状态测试：耗时: {status_time:.4f}秒")
        logger.error(f"查看仓库状态测试失败: {str(e)}")
    start_time = time.time()
        logger.info(f"提交日志: {log}")
        log_time = time.time() - start_time
    except Exception as e:
        logger.error(f"查看提交日志测试失败: {str(e)}")
    # 测试查看分支
    try:
        logger.info(f"分支: {branches}")
        branch_time = time.time() - start_time
    except Exception as e:

    """主测试函数"""

        test_git_manager()
        test_distributed_server_git()
    except Exception as e:
        logger.error(f"测试失败: {str(e)}")
        import traceback
        traceback.print_exc()
if __name__ == "__main__":
