#!/usr/bin/env python3
import sys
sys.path.insert(0, '/Users/wuchenghao/Library/CloudStorage/OneDrive-个人/文档/MTSCOS_AI_Project')

from ai_engines.project_repair_agent import ProjectRepairAgent

def main():
    agent = ProjectRepairAgent('prj_rep_001', '项目修复AI Agent', 9)
    agent.start()
    
    logger.info('=' * 60)
    logger.info('项目修复AI Agent v3 - 批量修复模式')
    logger.info('=' * 60)
    
    scan_result = agent.scan_project()
    logger.info('扫描完成:', scan_result['message'])
    logger.info('严重级别分布:')
    logger.info('  高:', scan_result['errors_by_severity']['high'])
    logger.info('  中:', scan_result['errors_by_severity']['medium'])
    logger.info('  低:', scan_result['errors_by_severity']['low'])
    
    logger.info()
    logger.info('=' * 60)
    logger.info('开始批量修复问题')
    logger.info('=' * 60)
    
    fix_result = agent.fix_issues()
    logger.info('修复结果:', fix_result['message'])
    
    logger.info()
    logger.info('修复类型统计:')
    fix_types = {}
    for result in fix_result['results']:
        if result['success']:
            ft = result['message']
            fix_types[ft] = fix_types.get(ft, 0) + 1
    
    for ft, cnt in sorted(fix_types.items(), key=lambda x: -x[1]):
        logger.info('  {}次: {}'.format(cnt, ft))
    
    logger.info()
    logger.info('=' * 60)
    logger.info('上报修复记录到数据库')
    logger.info('=' * 60)
    
    report_result = agent.report_to_database()
    logger.info('上报结果:', report_result['message'])
    
    agent.stop()
    logger.info()
    logger.info('=' * 60)
    logger.info('项目修复AI Agent已完成任务')
    logger.info('=' * 60)

if __name__ == '__main__':
    main()
