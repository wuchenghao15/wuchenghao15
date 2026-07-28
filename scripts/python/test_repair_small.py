#!/usr/bin/env python3
import sys
import time
sys.path.insert(0, '/Users/wuchenghao/Library/CloudStorage/OneDrive-个人/文档/MTSCOS_AI_Project')

logger.info('测试修复脚本开始', flush=True)

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

code_smells = [e for e in agent.scan_results if e['error_type'] == 'code_smell']
logger.info('代码异味总数: {}'.format(len(code_smells)), flush=True)

by_file = {}
for e in code_smells:
    f = e['file']
    if f not in by_file:
        by_file[f] = []
    by_file[f].append(e)

logger.info('涉及文件数: {}'.format(len(by_file)), flush=True)

files_list = list(by_file.items())[:10]
logger.info('只处理前10个文件:', flush=True)
for f, errs in files_list:
    logger.info('  {}: {}个问题'.format(f.split('/')[-1], len(errs)), flush=True)

logger.info('开始修复...', flush=True)
start_time = time.time()

success = 0
failed = 0

for file_path, errors in files_list:
    logger.info('  修复 {}...'.format(file_path.split('/')[-1]), flush=True)
    result = agent._fix_file_code_smells(file_path, errors)
    if result['success']:
        success += result.get('fixed_count', len(errors))
        logger.info('    ✓ 成功: {}'.format(result['message']), flush=True)
    else:
        failed += len(errors)
        logger.info('    ✗ 失败: {}'.format(result['message']), flush=True)

fix_time = time.time() - start_time
logger.info('修复完成: 成功{} | 失败{} (耗时{}秒)'.format(success, failed, int(fix_time)), flush=True)

agent.stop()
logger.info('测试完成', flush=True)
