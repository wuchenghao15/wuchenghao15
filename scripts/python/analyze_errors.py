#!/usr/bin/env python3
import sys
sys.path.insert(0, '/Users/wuchenghao/Library/CloudStorage/OneDrive-个人/文档/MTSCOS_AI_Project')

from ai_engines.project_repair_agent import ProjectRepairAgent

agent = ProjectRepairAgent('prj_rep_001', '项目修复AI Agent', 9)
scan_result = agent.scan_project()

code_smells = [e for e in scan_result['errors'] if e['error_type'] == 'code_smell']
logger.info('代码异味总数:', len(code_smells))

smell_types = {}
for smell in code_smells:
    msg = smell['message']
    smell_types[msg] = smell_types.get(msg, 0) + 1

logger.info('代码异味类型分布:')
for msg, cnt in sorted(smell_types.items(), key=lambda x: -x[1]):
    logger.info('  {}次: {}'.format(cnt, msg))

logger.info()
logger.info('前5个包含最多问题的文件:')
file_counts = {}
for smell in code_smells:
    f = smell['file']
    file_counts[f] = file_counts.get(f, 0) + 1

for f, cnt in sorted(file_counts.items(), key=lambda x: -x[1])[:5]:
    logger.info('  {}个问题: {}'.format(cnt, f.split('/')[-1]))

logger.info()
logger.info('使用全局变量的文件:')
global_files = set()
for smell in code_smells:
    if smell['message'] == '使用全局变量':
        global_files.add(smell['file'])
logger.info('  {}个文件使用全局变量'.format(len(global_files)))

logger.info()
logger.info('行长度超过120字符的文件统计:')
long_line_files = {}
for smell in code_smells:
    if smell['message'] == '行长度超过120字符':
        f = smell['file']
        long_line_files[f] = long_line_files.get(f, 0) + 1
logger.info('  {}个文件包含过长行'.format(len(long_line_files)))
