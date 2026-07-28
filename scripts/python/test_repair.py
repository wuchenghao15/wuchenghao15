#!/usr/bin/env python3
import sys
sys.path.insert(0, '/Users/wuchenghao/Library/CloudStorage/OneDrive-个人/文档/MTSCOS_AI_Project')

logger.info('测试修复脚本开始')

from ai_engines.project_repair_agent import ProjectRepairAgent
logger.info('导入成功')

agent = ProjectRepairAgent('prj_rep_001', '项目修复AI Agent', 9)
logger.info('创建Agent成功')

agent.start()
logger.info('Agent启动成功')

scan_result = agent.scan_project()
logger.info('扫描完成:', scan_result['message'])

fix_result = agent.fix_issues()
logger.info('修复结果:', fix_result['message'])

report_result = agent.report_to_database()
logger.info('上报结果:', report_result['message'])

agent.stop()
logger.info('测试完成')
