#!/usr/bin/env python3
import sys
import time
sys.path.insert(0, '/Users/wuchenghao/Library/CloudStorage/OneDrive-个人/文档/MTSCOS_AI_Project')

logger.info('完整修复脚本开始', flush=True)

from ai_engines.project_repair_agent import ProjectRepairAgent
logger.info('导入成功', flush=True)

agent = ProjectRepairAgent('prj_rep_001', '项目修复AI Agent', 9)
logger.info('创建Agent成功', flush=True)

agent.start()
logger.info('Agent启动成功', flush=True)

logger.info('开始扫描...', flush=True)
start_time = time.time()
scan_result = agent.scan_project()
scan_time = time.time() - start_time
logger.info('扫描完成: {} (耗时{}秒)'.format(scan_result['message'], int(scan_time)), flush=True)

logger.info('开始修复...', flush=True)
start_time = time.time()
fix_result = agent.fix_issues()
fix_time = time.time() - start_time
logger.info('修复结果: {} (耗时{}秒)'.format(fix_result['message'], int(fix_time)), flush=True)

logger.info('开始上报数据库...', flush=True)
report_result = agent.report_to_database()
logger.info('上报结果: {}'.format(report_result['message']), flush=True)

agent.stop()
logger.info('修复完成', flush=True)
