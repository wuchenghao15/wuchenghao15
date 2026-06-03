#!/usr/bin/env python3
"""
使用专用实例化AI自动修复网站问题的脚本
"""

import sys
import os

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.ai.auto_completion import ai_auto_completion_service
from app.utils.logging import logger

def main():
    """主函数,使用AI自动修复网站问题"""
    logger.info("开始使用专用实例化AI自动修复网站问题")

    try:
        # 1. 自动补充项目功能
        logger.info("第一步:分析项目并补充缺失功能")
        completion_report = ai_auto_completion_service.auto_complete_project()

        logger.info(f"自动补充完成,应用了 {len(completion_report['applied_files'])} 个文件")
        logger.info(f"缺失功能:{len(completion_report['missing_features'])}")
        for feature in completion_report['missing_features']:
            logger.info(f"  - {feature['description']} ({feature['type']}, {feature['priority']})")

        # 2. 应用优化建议
        logger.info("\n第二步:应用优化建议")
        optimization_suggestions = completion_report['optimization_suggestions']
        applied_suggestions = ai_auto_completion_service.apply_optimization_suggestions(optimization_suggestions)
        logger.info(f"应用了 {len(applied_suggestions)} 个优化建议")

        # 3. 验证修复效果
        logger.info("\n第三步:验证修复效果")
        logger.info("请手动访问以下URL验证修复效果:")
        logger.info("  - http://localhost:8888 (主页)")
        logger.info("  - http://localhost:8888/dashboard (仪表盘)")
        logger.info("  - http://localhost:8888/japanese_test (日语测试)")
        logger.info("  - http://localhost:8888/english_test (英语测试)")
        logger.info("  - http://localhost:8888/combined_test (结合测试)")

        logger.info("\n专用实例化AI自动修复网站问题完成!")
        return 0

    except Exception as e:
        logger.error(f"修复过程中发生错误:{str(e)}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    sys.exit(main())
