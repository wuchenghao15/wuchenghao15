#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
项目版本控制系统
功能：记录核心文件变化、操作日志、版本回滚、历史存档

import os
import shutil
import datetime
# JSON import removed - using database
import hashlib
import logging
from pathlib import Path

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('project_history.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger('ProjectVersionControl')

class ProjectVersionControl:
    def __init__(self, project_root=None):
        self.project_root = project_root or os.getcwd()
        self.history_dir = os.path.join(self.project_root, '.project_history')
        self.core_files = self._get_core_files()
        self.backup_dirs = ['templates', 'app', 'static', 'config']

        # 创建必要目录
        os.makedirs(self.history_dir, exist_ok=True)
        os.makedirs(os.path.join(self.history_dir, 'versions'), exist_ok=True)
        os.makedirs(os.path.join(self.history_dir, 'backups'), exist_ok=True)

        # 初始化历史记录文件
        self.history_file = os.path.join(self.history_dir, 'history.json')
        if not os.path.exists(self.history_file):
            with open(self.history_file, 'w', encoding='utf-8') as f:
                json.dump({'versions': [], 'operations': []}, f, ensure_ascii=False, indent=2)

    def _get_core_files(self):
        """获取核心文件列表"""
        core_files = [
            'app.py',
            'VERSION',
            'requirements.txt',
            'simple_version_upgrade.py',
            'standalone_ai_brain_map.py',
            'ai_employee_distributed_upgrade.py'
        ]

    def _get_file_hash(self, file_path):
        """计算文件哈希值"""
        if not os.path.exists(file_path):
            return None
        with open(file_path, 'rb') as f:
            return hashlib.md5(f.read()).hexdigest()

    def create_snapshot(self, version_name, description):
        """创建项目快照"""
        timestamp = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
        snapshot_dir = os.path.join(self.history_dir, 'versions', f'{version_name}_{timestamp}')
        os.makedirs(snapshot_dir, exist_ok=True)

        # 保存核心文件
        core_snapshot = {}
        for file in self.core_files:
            file_path = os.path.join(self.project_root, file)
            if os.path.exists(file_path):
                dest_path = os.path.join(snapshot_dir, file)
                try:
                    # 添加超时处理，使用基本的文件复制
                    with open(file_path, 'rb') as src_file:
                        with open(dest_path, 'wb') as dst_file:
                            dst_file.write(src_file.read())
                    core_snapshot[file] = self._get_file_hash(file_path)
                    logger.info(f'已保存核心文件: {file}')
                except Exception as e:
                    logger.warning(f'保存核心文件失败: {file} - {str(e)}')
                    core_snapshot[file] = f'ERROR: {str(e)}'

        # 保存目录
        for dir_name in self.backup_dirs:
            dir_path = os.path.join(self.project_root, dir_name)
            if os.path.exists(dir_path):
                dest_path = os.path.join(snapshot_dir, dir_name)
                try:
                    # 使用shutil.copytree并忽略错误
                        dir_path, dest_path,
                        dirs_exist_ok=True,
                        ignore=shutil.ignore_patterns('*.pyc', '__pycache__')
                    )
                    logger.info(f'已保存目录: {dir_name}')
                    logger.warning(f'保存目录失败: {dir_name} - {str(e)}')

        # 记录版本信息
            'version_name': version_name,
            'timestamp': timestamp,
            'description': description,
            'core_files': core_snapshot,
            'directories': self.backup_dirs
        }

        # 更新历史记录
        with open(self.history_file, 'r+', encoding='utf-8') as f:
            history = json.load(f)
            history['versions'].append(version_info)
            f.seek(0)
            json.dump(history, f, ensure_ascii=False, indent=2)

        logger.info(f'已创建版本快照: {version_name} ({timestamp}) - {description}')
        return version_info

    def record_operation(self, operation_type, description, file_path=None):
        """记录操作日志"""
        operation = {
            'timestamp': datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'operation_type': operation_type,
            'description': description,
            'file_path': file_path
        }

        with open(self.history_file, 'r+', encoding='utf-8') as f:
            history['operations'].append(operation)
            f.seek(0)

        logger.info(f'已记录操作: {operation_type} - {description}')

        """列出所有版本"""
        with open(self.history_file, 'r', encoding='utf-8') as f:
        return history['versions']
    def list_operations(self, limit=10):
        """列出操作日志"""
        with open(self.history_file, 'r', encoding='utf-8') as f:
            history = json.load(f)
        return history['operations'][-limit:]
    def rollback_to_version(self, version_index):
        """回滚到指定版本"""
        with open(self.history_file, 'r', encoding='utf-8') as f:
            history = json.load(f)

            logger.error(f'无效的版本索引: {version_index}')
            return False

        version_dir = os.path.join(self.history_dir, 'versions', f'{version["version_name"]}_{version["timestamp"]}')
        if not os.path.exists(version_dir):
            logger.error(f'版本目录不存在: {version_dir}')
            return False

        for file in self.core_files:
            src_path = os.path.join(version_dir, file)
            dest_path = os.path.join(self.project_root, file)
                shutil.copy2(src_path, dest_path)
                logger.info(f'已回滚文件: {file}')

        # 回滚目录
        for dir_name in self.backup_dirs:
            src_path = os.path.join(version_dir, dir_name)
            dest_path = os.path.join(self.project_root, dir_name)
            if os.path.exists(src_path):
                # 删除现有目录
                if os.path.exists(dest_path):
                logger.info(f'已回滚目录: {dir_name}')

        logger.info(f'已回滚到版本: {version["version_name"]} ({version["timestamp"]})')
        return True

    def create_backup(self, backup_name=None):
        """创建完整备份"""
        timestamp = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
        backup_name = backup_name or f'backup_{timestamp}'
        backup_path = os.path.join(self.history_dir, 'backups', f'{backup_name}.zip')
        # 创建完整备份
        shutil.make_archive(
            os.path.join(self.history_dir, 'backups', backup_name),
            'zip',
            ignore=lambda src, names: ['.git', '.project_history', '__pycache__', '*.pyc']
        )

        return backup_path

    def export_history(self):
        """导出历史记录"""
        history_path = os.path.join(self.history_dir, 'exported_history.json')
        with open(self.history_file, 'r', encoding='utf-8') as f:
            history = json.load(f)

        # 添加导出信息
        history['export_info'] = {
            'export_time': datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'project_root': self.project_root,
            'total_versions': len(history['versions']),
            'total_operations': len(history['operations'])
        }

        with open(history_path, 'w', encoding='utf-8') as f:
            json.dump(history, f, ensure_ascii=False, indent=2)
        logger.info(f'已导出历史记录: {history_path}')
        return history_path

    def get_current_state(self):
        """获取当前项目状态"""
            'core_files': {},
            'directories': []
        }

        # 检查核心文件
        for file in self.core_files:
            file_path = os.path.join(self.project_root, file)
            current_state['core_files'][file] = {
                'exists': os.path.exists(file_path),
                'hash': self._get_file_hash(file_path),

            dir_path = os.path.join(self.project_root, dir_name)
            if os.path.exists(dir_path):
                current_state['directories'].append(dir_name)

        return current_state

    def generate_version_summary(self, start_version=None, end_version=None):
        生成项目历史版本总结报告
            end_version: 结束版本索引（可选）
        Returns:
        logger.info("生成项目历史版本总结报告")

        with open(self.history_file, 'r', encoding='utf-8') as f:
            history = json.load(f)

        versions = history['versions']
        operations = history['operations']

        # 应用版本范围过滤
        if start_version is not None or end_version is not None:
            start = start_version if start_version is not None else 0
            end = end_version + 1 if end_version is not None else len(versions)
            versions = versions[start:end]

        if not versions:
            logger.warning("没有找到版本记录")
            return None

        # 计算版本统计信息
        total_versions = len(versions)
        total_operations = len(operations)

        version_dates = []
        for version in versions:
            version_date = datetime.datetime.strptime(version['timestamp'], '%Y%m%d_%H%M%S')

        # 计算版本间隔
        version_intervals = []
        for i in range(1, len(version_dates)):
            interval = (version_dates[i] - version_dates[i-1]).total_seconds() / 3600  # 转换为小时
            version_intervals.append(interval)

        avg_version_interval = sum(version_intervals) / len(version_intervals) if version_intervals else 0
        # 统计核心文件变更
        file_changes = {}
        for file in self.core_files:
            file_changes[file] = {
                'total_changes': 0,
                'versions_changed': []
            }

        # 比较相邻版本的文件哈希值，统计变更
        for i in range(1, len(versions)):
            curr_version = versions[i]

            for file in self.core_files:
                prev_hash = prev_version['core_files'].get(file)
                curr_hash = curr_version['core_files'].get(file)

                if prev_hash and curr_hash and prev_hash != curr_hash:
                    file_changes[file]['total_changes'] += 1
                    file_changes[file]['versions_changed'].append(curr_version['version_name'])

        operation_types = {}
        for op in operations:
            op_type = op['operation_type']
            operation_types[op_type] = operation_types.get(op_type, 0) + 1
        # 生成总结报告
        summary = {
            'report_generated_at': datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'report_period': {
                'start_version': start_version if start_version is not None else 0,
                'end_version': end_version if end_version is not None else len(history['versions']) - 1,
                'total_versions_in_report': total_versions,
                'time_range': {
                    'start': version_dates[0].strftime('%Y-%m-%d %H:%M:%S') if version_dates else '',
                    'end': version_dates[-1].strftime('%Y-%m-%d %H:%M:%S') if version_dates else ''
                }
            },
            'version_statistics': {
                'total_versions': total_versions,
                'total_operations': total_operations,
                'average_version_interval_hours': round(avg_version_interval, 2),
                'shortest_version_interval_hours': round(min(version_intervals), 2) if version_intervals else 0,
                'longest_version_interval_hours': round(max(version_intervals), 2) if version_intervals else 0
            },
            'file_change_statistics': file_changes,
            'operation_type_distribution': operation_types,
            'versions_summary': [],
            'change_trend': self._analyze_change_trend(versions, file_changes)
        }

        # 添加版本详细摘要
        for i, version in enumerate(versions):
            version_summary = {
                'version_index': i + (start_version if start_version is not None else 0),
                'version_name': version['version_name'],
                'description': version['description'],
                'core_files_count': len(version['core_files']),
                'directories': version['directories']
            }

            # 计算该版本的文件变更数
            if i > 0:
                prev_version = versions[i-1]
                change_count = 0
                for file in self.core_files:
                    prev_hash = prev_version['core_files'].get(file)
                    curr_hash = version['core_files'].get(file)
                        change_count += 1
                version_summary['files_changed'] = change_count
            else:
                version_summary['files_changed'] = len(version['core_files'])  # 第一个版本，所有文件都是新增
            summary['versions_summary'].append(version_summary)

        logger.info(f"生成项目历史版本总结报告成功，包含 {total_versions} 个版本")
        return summary

    def _analyze_change_trend(self, versions, file_changes):

        Args:
            versions: 版本列表
            file_changes: 文件变更统计

        Returns:
            变更趋势分析结果
        # 计算每个版本的文件变更数
        for i in range(1, len(versions)):
            prev_version = versions[i-1]
            curr_version = versions[i]

            change_count = 0
            for file in self.core_files:
                prev_hash = prev_version['core_files'].get(file)
                curr_hash = curr_version['core_files'].get(file)
                if prev_hash and curr_hash and prev_hash != curr_hash:
                    change_count += 1

            version_changes.append({
                'version_name': curr_version['version_name'],
                'timestamp': curr_version['timestamp'],
                'changes_count': change_count

        # 分析变更趋势
        if not version_changes:
            return {
                'average_changes_per_version': 0,
                'most_changes_version': None,
                'least_changes_version': None

        # 计算平均变更数

        # 找出变更最多和最少的版本
        most_changes = max(version_changes, key=lambda x: x['changes_count'])
        least_changes = min(version_changes, key=lambda x: x['changes_count'])

        # 分析趋势
        # 简单的趋势分析：比较最近3个版本与之前版本的平均变更数
        if len(version_changes) >= 3:
            recent_avg = sum(vc['changes_count'] for vc in version_changes[-3:]) / 3
            previous_avg = sum(vc['changes_count'] for vc in version_changes[:-3]) / (len(version_changes) - 3) if len(version_changes) > 3 else avg_changes

            if recent_avg > previous_avg * 1.5:
            elif recent_avg < previous_avg * 0.5:
                trend = 'decreasing'
            else:
                trend = 'stable'
            trend = 'stable'

            'trend': trend,
            'average_changes_per_version': round(avg_changes, 2),
            'most_changes_version': most_changes,
            'version_changes': version_changes

    def export_version_summary(self, summary=None, start_version=None, end_version=None):

        Args:
            summary: 版本总结报告（可选，如不提供则生成新的）
            start_version: 起始版本索引（可选）

        if not summary:
            if not summary:
                logger.error("生成版本总结报告失败")
                return None

        summary_path = os.path.join(self.history_dir, f'version_summary_{datetime.datetime.now().strftime("%Y%m%d_%H%M%S")}.json')

        with open(summary_path, 'w', encoding='utf-8') as f:
            json.dump(summary, f, ensure_ascii=False, indent=2)

        return summary_path
    def generate_version_summary_markdown(self, start_version=None, end_version=None):
        生成版本总结报告的Markdown格式

        Args:
            start_version: 起始版本索引（可选）
            end_version: 结束版本索引（可选）

        Returns:
            Markdown格式的版本总结报告
        summary = self.generate_version_summary(start_version, end_version)
        if not summary:
            logger.error("生成版本总结报告失败")
            return None

        # 生成Markdown报告
        markdown = f"""# 项目历史版本总结报告

## 报告基本信息

- **报告生成时间**: {summary['report_generated_at']}
- **报告涵盖版本范围**: 第 {summary['report_period']['start_version']} 至 {summary['report_period']['end_version']} 版本
- **总版本数**: {summary['report_period']['total_versions_in_report']}
- **时间范围**: {summary['report_period']['time_range']['start']} 至 {summary['report_period']['time_range']['end']}


| 统计项 | 数值 |
|--------|------|
| 总版本数 | {summary['version_statistics']['total_versions']} |
| 总操作数 | {summary['version_statistics']['total_operations']} |
| 平均版本间隔 (小时) | {summary['version_statistics']['average_version_interval_hours']} |
| 最短版本间隔 (小时) | {summary['version_statistics']['shortest_version_interval_hours']} |
## 变更趋势分析
- **平均每个版本变更文件数**: {summary['change_trend']['average_changes_per_version']}
### 变更最多的版本
- **版本名称**: {summary['change_trend']['most_changes_version']['version_name']}
- **时间**: {summary['change_trend']['most_changes_version']['timestamp']}

### 变更最少的版本
- **版本名称**: {summary['change_trend']['least_changes_version']['version_name']}
- **变更文件数**: {summary['change_trend']['least_changes_version']['changes_count']}
- **时间**: {summary['change_trend']['least_changes_version']['timestamp']}

## 核心文件变更统计

| 文件名称 | 变更次数 | 变更版本 |
|----------|----------|----------|

        # 添加文件变更统计
        for file, stats in summary['file_change_statistics'].items():
            versions_list = ', '.join(stats['versions_changed']) if stats['versions_changed'] else '无'
            markdown += f"| {file} | {stats['total_changes']} | {versions_list} |\n"

        markdown += "\n## 操作类型分布\n\n| 操作类型 | 次数 |\n|----------|------|\n"
        for op_type, count in summary['operation_type_distribution'].items():
            markdown += f"| {op_type} | {count} |\n"
        markdown += "\n## 版本详细信息\n\n| 版本索引 | 版本名称 | 时间戳 | 描述 | 变更文件数 |\n|----------|----------|--------|------|------------|\n"
            markdown += f"| {version['version_index']} | {version['version_name']} | {version['timestamp']} | {version['description']} | {version['files_changed']} |\n"

        return markdown
    def save_version_summary_markdown(self, start_version=None, end_version=None):
        保存版本总结报告的Markdown格式到文件

        Args:
            start_version: 起始版本索引（可选）
            end_version: 结束版本索引（可选）

        Returns:
            保存的Markdown文件路径
        markdown = self.generate_version_summary_markdown(start_version, end_version)
        if not markdown:
            logger.error("生成Markdown版本总结报告失败")
            return None

        # 保存为Markdown文件
        md_path = os.path.join(self.history_dir, f'version_summary_{datetime.datetime.now().strftime("%Y%m%d_%H%M%S")}.md')

        with open(md_path, 'w', encoding='utf-8') as f:
            f.write(markdown)


    def get_version_difference(self, version1_index, version2_index):

        Args:
            version2_index: 版本2索引

        Returns:
            版本差异信息
        with open(self.history_file, 'r', encoding='utf-8') as f:
            history = json.load(f)

        versions = history['versions']

        if version1_index < 0 or version1_index >= len(versions) or
           version2_index < 0 or version2_index >= len(versions):
            logger.error(f'无效的版本索引: {version1_index} 或 {version2_index}')
            return None

        # 确保version1是较早的版本
        if version1_index > version2_index:
            version1_index, version2_index = version2_index, version1_index

        version1 = versions[version1_index]
        version2 = versions[version2_index]

        # 比较两个版本的文件差异
        file_differences = {
            'added': [],
            'modified': [],
            'removed': []
        }

        # 比较核心文件
        version2_files = set(version2['core_files'].keys())

        # 新增文件
        added_files = version2_files - version1_files
        for file in added_files:
            file_differences['added'].append(file)
        # 删除文件
        removed_files = version1_files - version2_files
        for file in removed_files:
            file_differences['removed'].append(file)
        # 修改文件
        common_files = version1_files.intersection(version2_files)
        for file in common_files:
                file_differences['modified'].append(file)

        # 生成差异报告
        difference = {
                'index': version1_index,
                'name': version1['version_name'],
                'description': version1['description']
            },
            'version2': {
                'index': version2_index,
                'name': version2['version_name'],
                'timestamp': version2['timestamp'],
                'description': version2['description']
            },
                'added': len(file_differences['added']),
                'modified': len(file_differences['modified']),
                'removed': len(file_differences['removed'])
            }
        }

        logger.info(f"获取版本 {version1_index} 和 {version2_index} 之间的差异成功")
        return difference

def main():
    """主函数"""
    pvc = ProjectVersionControl()

    print("=" * 60)
    print("=" * 60)
    print("1. 创建版本快照")
    print("2. 记录操作日志")
    print("3. 列出所有版本")
    print("4. 列出操作日志")
    print("5. 回滚到指定版本")
    print("6. 创建完整备份")
    print("7. 导出历史记录")
    print("8. 获取当前状态")
    print("9. 生成版本总结报告")
    print("11. 生成Markdown版本总结")
    print("12. 获取版本差异")
    print("0. 退出")
    print("=" * 60)

    while True:
        choice = input("请输入操作编号: ").strip()

        if choice == '0':
            break
        elif choice == '1':
            version_name = input("请输入版本名称: ").strip()
            description = input("请输入版本描述: ").strip()
            pvc.create_snapshot(version_name, description)
            description = input("请输入操作描述: ").strip()
            file_path = input("请输入相关文件路径 (可选): ").strip()
            file_path = file_path if file_path else None
            pvc.record_operation(operation_type, description, file_path)
        elif choice == '3':
            versions = pvc.list_versions()
            print(f"\n共 {len(versions)} 个版本:")
            for i, version in enumerate(versions):
                print(f"{i}. {version['version_name']} - {version['timestamp']}")
                print(f"   描述: {version['description']}")
                print(f"   文件数: {len(version['core_files'])}")
                print()
        elif choice == '4':
            limit = input("请输入显示条数 (默认10): ").strip()
            limit = int(limit) if limit else 10
            operations = pvc.list_operations(limit)
            print(f"\n最近 {len(operations)} 条操作:")
            for op in operations:
                print(f"{op['timestamp']} - {op['operation_type']}: {op['description']}")
                if op['file_path']:
                    print(f"   文件: {op['file_path']}")
            print()
        elif choice == '5':
            versions = pvc.list_versions()
            print(f"\n共 {len(versions)} 个版本:")
            for i, version in enumerate(versions):
                print(f"{i}. {version['version_name']} - {version['timestamp']} - {version['description']}")

            index = input("请输入要回滚的版本索引: ").strip()
            if index.isdigit():
                index = int(index)
                if pvc.rollback_to_version(index):
                    print("回滚成功!")
                else:
                    print("回滚失败!")
        elif choice == '6':
            backup_name = input("请输入备份名称 (可选): ").strip()
            backup_name = backup_name if backup_name else None
            backup_path = pvc.create_backup(backup_name)
            print(f"备份已创建: {backup_path}")
        elif choice == '7':
            history_path = pvc.export_history()
            print(f"历史记录已导出: {history_path}")
            state = pvc.get_current_state()
            print(f"\n当前项目状态 ({state['timestamp']}):")
            print("核心文件:")
            for file, info in state['core_files'].items():
                status = "存在" if info['exists'] else "不存在"
            print(f"已备份目录: {', '.join(state['directories'])}")
        elif choice == '9':
            # 生成版本总结报告
            start_ver = input("请输入起始版本索引 (可选): ").strip()
            end_ver = input("请输入结束版本索引 (可选): ").strip()

            start_ver = int(start_ver) if start_ver.isdigit() else None
            end_ver = int(end_ver) if end_ver.isdigit() else None

            summary = pvc.generate_version_summary(start_ver, end_ver)
            if summary:
                print(f"\n版本总结报告生成成功:")
                print(f"- 报告涵盖 {summary['report_period']['total_versions_in_report']} 个版本")
                print(f"- 平均版本间隔: {summary['version_statistics']['average_version_interval_hours']} 小时")
                print(f"- 总体变更趋势: {summary['change_trend']['trend']}")
        elif choice == '10':
            # 导出版本总结报告
            start_ver = input("请输入起始版本索引 (可选): ").strip()
            end_ver = input("请输入结束版本索引 (可选): ").strip()

            start_ver = int(start_ver) if start_ver.isdigit() else None
            end_ver = int(end_ver) if end_ver.isdigit() else None

            summary_path = pvc.export_version_summary(None, start_ver, end_ver)
            if summary_path:
                print(f"\n版本总结报告导出成功: {summary_path}")
        elif choice == '11':
            # 生成Markdown版本总结
            start_ver = input("请输入起始版本索引 (可选): ").strip()
            end_ver = input("请输入结束版本索引 (可选): ").strip()

            start_ver = int(start_ver) if start_ver.isdigit() else None
            end_ver = int(end_ver) if end_ver.isdigit() else None

            md_path = pvc.save_version_summary_markdown(start_ver, end_ver)
            if md_path:
                print(f"\nMarkdown版本总结报告生成成功: {md_path}")
        elif choice == '12':
            # 获取版本差异
            ver1 = input("请输入第一个版本索引: ").strip()
            ver2 = input("请输入第二个版本索引: ").strip()

            if ver1.isdigit() and ver2.isdigit():
                ver1 = int(ver1)
                ver2 = int(ver2)

                diff = pvc.get_version_difference(ver1, ver2)
                if diff:
                    print(f"\n版本 {ver1} 和 {ver2} 之间的差异:")
                    print(f"- 新增文件: {', '.join(diff['file_differences']['added']) if diff['file_differences']['added'] else '无'}")
                    print(f"- 修改文件: {', '.join(diff['file_differences']['modified']) if diff['file_differences']['modified'] else '无'}")
                    print(f"- 删除文件: {', '.join(diff['file_differences']['removed']) if diff['file_differences']['removed'] else '无'}")
                    print(f"- 总差异数: {diff['total_differences']}")
            else:
                print("无效的版本索引!")
        else:
            print("无效的操作编号!")

        print("=" * 60)

if __name__ == '__main__':
    main()
