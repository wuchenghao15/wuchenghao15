# -*- coding: utf-8 -*-
# 上次更新: 2025-10-26 16:53:24
#!/usr/bin/env python3
# 简单日志监控脚本

import os
import shutil
import time
import logging
import datetime
from pathlib import Path
from collections import defaultdict

# 项目根目录
PROJECT_ROOT = Path('.')
LOG_DIR = PROJECT_ROOT / "Logs"

# 设置日志
LOG_DIR.mkdir(parents=True, exist_ok=True)
SERVICE_LOG_DIR = LOG_DIR / "日志监控"
SERVICE_LOG_DIR.mkdir(parents=True, exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(SERVICE_LOG_DIR / "monitor.log"),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger()

# 排除目录
EXCLUDE_DIRS = ['Logs', 'Build', 'Backups', '.git', 'node_modules', '__pycache__']

# 分类规则
CATEGORIES = {
    'backup': '备份工具',
    'error': '错误日志',
    'monitor': 'JavaScript监控',
    'log': '其他日志'
}

def scan_logs():
    logger.info("开始扫描日志文件...")
    stats = defaultdict(int)

    for root, dirs, files in os.walk(PROJECT_ROOT):
        # 过滤排除目录
        dirs[:] = [d for d in dirs if d not in EXCLUDE_DIRS]

        for file in files:
            # 识别日志文件
            if file.endswith(('.log', '.txt')) or any(key in file.lower() for key in ['log', '日志', 'error', 'backup']):
                file_path = Path(root) / file

                # 跳过Logs目录下的文件
                if 'Logs' in str(file_path):
                    continue

                # 确定分类
                category = '其他日志'
                for keyword, cat_name in CATEGORIES.items():
                    if keyword in file.lower():
                        category = cat_name
                        break

                # 创建目标目录
                target_dir = LOG_DIR / category
                target_dir.mkdir(parents=True, exist_ok=True)

                # 处理文件名冲突
                target_path = target_dir / file
                if target_path.exists():
                    base_name, ext = os.path.splitext(file)
                    timestamp = datetime.datetime.now().strftime('_%Y%m%d_%H%M%S')
                    target_path = target_dir / (base_name + timestamp + ext)

                # 移动文件
                try:
                    shutil.move(str(file_path), str(target_path))
                    logger.info(f"移动: {file_path} -> {target_path}")
                    stats[category] += 1
                except Exception as e:
                    logger.error(f"移动失败: {file_path} - {e}")

    # 输出统计
    logger.info("\n扫描完成！")
    logger.info("分类统计:")
    for cat, count in stats.items():
        logger.info(f"  {cat}: {count}个文件")

# 主函数
if __name__ == "__main__":
    print("日志监控脚本启动")
    print("按 Ctrl+C 停止")

        while True:
            scan_logs()
            print("\n等待5分钟后再次扫描...\n")
            time.sleep(300)
    except KeyboardInterrupt:
        print("\n脚本已停止")
    except Exception as e:
        print(f"错误: {e}")
