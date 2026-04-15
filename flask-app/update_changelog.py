#!/usr/bin/env python3
"""
系统升级历史记录更新工具
用于自动更新CHANGELOG.md文件，记录系统升级信息
"""

import os
import json
import datetime
from typing import Dict, Any

class ChangelogUpdater:
    """系统升级历史记录更新器"""
    
    def __init__(self, changelog_path: str = "CHANGELOG.md"):
        self.changelog_path = changelog_path
    
    def read_changelog(self) -> str:
        """读取CHANGELOG.md文件内容"""
        if os.path.exists(self.changelog_path):
            with open(self.changelog_path, 'r', encoding='utf-8') as f:
                return f.read()
        return ""
    
    def write_changelog(self, content: str) -> None:
        """写入CHANGELOG.md文件内容"""
        with open(self.changelog_path, 'w', encoding='utf-8') as f:
            f.write(content)
    
    def add_version_entry(self, version: str, release_date: str, status: str = "当前运行版本", description: str = "", features: list = [], improvements: list = [], fixes: list = []) -> None:
        """添加新的版本条目"""
        # 读取当前CHANGELOG内容
        content = self.read_changelog()
        
        # 创建新的版本条目
        new_entry = f"## 版本 {version} ({status})\n\n"
        new_entry += f"**发布日期**: {release_date}\n"
        new_entry += f"**状态**: {status}\n\n"
        
        if description:
            new_entry += f"### 描述\n{description}\n\n"
        
        if features:
            new_entry += "### 新功能\n"
            for feature in features:
                new_entry += f"- {feature}\n"
            new_entry += "\n"
        
        if improvements:
            new_entry += "### 改进\n"
            for improvement in improvements:
                new_entry += f"- {improvement}\n"
            new_entry += "\n"
        
        if fixes:
            new_entry += "### 修复\n"
            for fix in fixes:
                new_entry += f"- {fix}\n"
            new_entry += "\n"
        
        # 如果CHANGELOG已经有内容，在现有内容前插入新条目
        if content:
            # 找到第一个##的位置
            first_section = content.find("##")
            if first_section > 0:
                # 保留标题
                header = content[:first_section]
                rest = content[first_section:]
                new_content = header + new_entry + rest
            else:
                new_content = new_entry + content
        else:
            # 创建全新的CHANGELOG
            new_content = "# 系统升级历史记录\n\n" + new_entry
        
        # 写入更新后的内容
        self.write_changelog(new_content)
        print(f"已成功添加版本 {version} 到CHANGELOG.md")
    
    def add_upgrade_attempt(self, version: str, upgrade_date: str, status: str, duration: str, current_version: str, description: str = "") -> None:
        """添加升级尝试记录"""
        # 读取当前CHANGELOG内容
        content = self.read_changelog()
        
        # 查找对应版本的位置
        version_section = f"## 版本 {version}"
        version_pos = content.find(version_section)
        
        if version_pos == -1:
            # 如果版本不存在，先添加版本条目
            self.add_version_entry(version, upgrade_date, "升级尝试", description)
            # 重新读取内容
            content = self.read_changelog()
            version_pos = content.find(version_section)
        
        # 找到升级记录表格的位置
        upgrade_table_start = content.find("### 升级记录", version_pos)
        if upgrade_table_start == -1:
            # 如果没有升级记录表格，添加一个
            upgrade_table = "### 升级记录\n"
            upgrade_table += "| 升级日期 | 状态 | 耗时 | 当前版本 | 说明 |\n"
            upgrade_table += "|---------|------|------|----------|------|\n"
            
            # 找到版本条目的结束位置
            next_version_pos = content.find("##", version_pos + len(version_section))
            if next_version_pos == -1:
                # 如果是最后一个版本
                new_content = content[:version_pos + len(version_section)] + "\n\n" + upgrade_table + "\n" + content[version_pos + len(version_section):]
            else:
                new_content = content[:next_version_pos] + upgrade_table + "\n" + content[next_version_pos:]
            
            self.write_changelog(new_content)
            content = self.read_changelog()
            upgrade_table_start = content.find("### 升级记录", version_pos)
        
        # 找到表格的结束位置
        table_end = content.find("\n##", upgrade_table_start)
        if table_end == -1:
            table_end = len(content)
        
        # 插入新的升级记录
        new_record = f"| {upgrade_date} | {status} | {duration} | {current_version} | {description} |\n"
        
        # 找到表格内容的结束位置（最后一个|行之后）
        lines = content[upgrade_table_start:table_end].split('\n')
        table_content_end = upgrade_table_start
        for line in lines:
            table_content_end += len(line) + 1
        
        # 插入新记录
        new_content = content[:table_content_end] + new_record + content[table_content_end:]
        self.write_changelog(new_content)
        print(f"已成功添加升级尝试记录到版本 {version}")
    
    def update_version_status(self, version: str, new_status: str) -> None:
        """更新版本状态"""
        content = self.read_changelog()
        old_status_pattern = f"## 版本 {version} \(.*\)"
        new_status_pattern = f"## 版本 {version} ({new_status})"
        
        # 使用字符串替换更新状态
        new_content = content.replace(old_status_pattern, new_status_pattern)
        self.write_changelog(new_content)
        print(f"已成功更新版本 {version} 的状态为 {new_status}")
    
    def get_latest_version(self) -> str:
        """获取最新版本号"""
        content = self.read_changelog()
        import re
        version_pattern = r"## 版本 ([0-9]+\.[0-9]+\.[0-9]+)"
        matches = re.findall(version_pattern, content)
        if matches:
            return matches[0]
        return "0.0.0"
    
    def generate_report(self) -> Dict[str, Any]:
        """生成升级报告"""
        content = self.read_changelog()
        
        # 提取所有版本
        import re
        version_pattern = r"## 版本 ([0-9]+\.[0-9]+\.[0-9]+) \((.*?)\)"
        versions = re.findall(version_pattern, content)
        
        report = {
            "total_versions": len(versions),
            "versions": [],
            "latest_version": versions[0][0] if versions else "0.0.0"
        }
        
        for version, status in versions:
            # 提取版本详细信息
            version_section = f"## 版本 {version} ({status})"
            section_start = content.find(version_section)
            next_version = content.find("##", section_start + len(version_section))
            if next_version == -1:
                section_end = len(content)
            else:
                section_end = next_version
            
            section_content = content[section_start:section_end]
            
            # 提取发布日期
            date_pattern = r"**发布日期**: (.*?)\n"
            date_match = re.search(date_pattern, section_content)
            release_date = date_match.group(1) if date_match else "未知"
            
            # 提取功能和改进
            feature_pattern = r"### 新功能\n((?:- .*?\n)*)"
            feature_match = re.search(feature_pattern, section_content, re.DOTALL)
            features = []
            if feature_match:
                features = [f.strip() for f in feature_match.group(1).split('\n') if f.strip()]
            
            improvement_pattern = r"### 改进\n((?:- .*?\n)*)"
            improvement_match = re.search(improvement_pattern, section_content, re.DOTALL)
            improvements = []
            if improvement_match:
                improvements = [i.strip() for i in improvement_match.group(1).split('\n') if i.strip()]
            
            # 提取修复
            fix_pattern = r"### 修复\n((?:- .*?\n)*)"
            fix_match = re.search(fix_pattern, section_content, re.DOTALL)
            fixes = []
            if fix_match:
                fixes = [f.strip() for f in fix_match.group(1).split('\n') if f.strip()]
            
            # 提取升级记录
            upgrade_pattern = r"### 升级记录\n.*?\n((?:\|.*?\|\n)*)"
            upgrade_match = re.search(upgrade_pattern, section_content, re.DOTALL)
            upgrades = []
            if upgrade_match:
                upgrade_lines = upgrade_match.group(1).split('\n')
                for line in upgrade_lines:
                    if line.strip() and '|' in line:
                        parts = [p.strip() for p in line.split('|')[1:-1]]
                        if len(parts) >= 5:
                            upgrade_record = {
                                "date": parts[0],
                                "status": parts[1],
                                "duration": parts[2],
                                "current_version": parts[3],
                                "description": parts[4]
                            }
                            upgrades.append(upgrade_record)
            
            version_info = {
                "version": version,
                "status": status,
                "release_date": release_date,
                "features": features,
                "improvements": improvements,
                "fixes": fixes,
                "upgrades": upgrades
            }
            
            report["versions"].append(version_info)
        
        return report

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="系统升级历史记录更新工具")
    parser.add_argument('--add-version', action='store_true', help='添加新的版本条目')
    parser.add_argument('--version', type=str, help='版本号')
    parser.add_argument('--date', type=str, default=datetime.datetime.now().strftime("%Y-%m-%d"), help='发布日期')
    parser.add_argument('--status', type=str, default="当前运行版本", help='版本状态')
    parser.add_argument('--description', type=str, default="", help='版本描述')
    parser.add_argument('--feature', type=str, action='append', default=[], help='新功能列表')
    parser.add_argument('--improvement', type=str, action='append', default=[], help='改进列表')
    parser.add_argument('--fix', type=str, action='append', default=[], help='修复列表')
    parser.add_argument('--add-upgrade', action='store_true', help='添加升级尝试记录')
    parser.add_argument('--current-version', type=str, default="3.0.0", help='当前版本')
    parser.add_argument('--duration', type=str, default="0.00秒", help='升级耗时')
    parser.add_argument('--upgrade-description', type=str, default="", help='升级说明')
    parser.add_argument('--update-status', action='store_true', help='更新版本状态')
    parser.add_argument('--new-status', type=str, help='新版本状态')
    parser.add_argument('--generate-report', action='store_true', help='生成升级报告')
    
    args = parser.parse_args()
    
    updater = ChangelogUpdater()
    
    if args.add_version:
        if not args.version:
            print("请提供版本号")
        else:
            updater.add_version_entry(
                args.version,
                args.date,
                args.status,
                args.description,
                args.feature,
                args.improvement,
                args.fix
            )
    elif args.add_upgrade:
        if not args.version:
            print("请提供目标版本号")
        else:
            updater.add_upgrade_attempt(
                args.version,
                args.date,
                args.status,
                args.duration,
                args.current_version,
                args.upgrade_description
            )
    elif args.update_status:
        if not args.version or not args.new_status:
            print("请提供版本号和新状态")
        else:
            updater.update_version_status(args.version, args.new_status)
    elif args.generate_report:
        report = updater.generate_report()
        print(json.dumps(report, indent=2, ensure_ascii=False))
    else:
        parser.print_help()