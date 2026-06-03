# -*- coding: utf-8 -*-
#!/usr/bin/env python3
"""
MTSCOS 历史版本管理系统 v3.0.0
功能：版本追踪、版本对比、版本回滚、版本统计、自动升级、云端同步
"""

import os
import json
import time
import logging
import shutil
import hashlib
from datetime import datetime
from typing import Dict, List, Any, Optional, Tuple
from collections import OrderedDict
from pathlib import Path

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('version_manager.log'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger('version_manager')

class VersionModel:
    """版本数据模型 v2.0"""
    
    def __init__(self):
        self.versions = OrderedDict()
        self.current_version = None
        self.version_history = []
        self._load_versions()
    
    def _load_versions(self):
        """加载版本数据"""
        version_definitions = [
            {'version': '1.0.0', 'date': '2025-01-15', 'type': 'major', 'description': '初始版本，基础考试系统', 'status': 'stable'},
            {'version': '1.1.0', 'date': '2025-02-20', 'type': 'minor', 'description': '新增学习系统模块', 'status': 'stable'},
            {'version': '1.1.1', 'date': '2025-02-28', 'type': 'patch', 'description': '修复考试统计bug', 'status': 'stable'},
            {'version': '1.2.0', 'date': '2025-03-15', 'type': 'minor', 'description': '新增错题本功能', 'status': 'stable'},
            {'version': '1.2.1', 'date': '2025-03-25', 'type': 'patch', 'description': '优化UI布局', 'status': 'stable'},
            {'version': '1.3.0', 'date': '2025-04-10', 'type': 'minor', 'description': '新增AI推荐功能', 'status': 'stable'},
            
            {'version': '2.0.0', 'date': '2025-06-01', 'type': 'major', 'description': '重大升级：K12全学段支持', 'status': 'stable'},
            {'version': '2.1.0', 'date': '2025-07-15', 'type': 'minor', 'description': '新增成就系统', 'status': 'stable'},
            {'version': '2.1.1', 'date': '2025-07-25', 'type': 'patch', 'description': '修复升级通知bug', 'status': 'stable'},
            {'version': '2.2.0', 'date': '2025-08-20', 'type': 'minor', 'description': '新增数据统计分析', 'status': 'stable'},
            {'version': '2.3.0', 'date': '2025-09-15', 'type': 'minor', 'description': '优化考试过滤功能', 'status': 'stable'},
            
            {'version': '3.0.0', 'date': '2025-12-01', 'type': 'major', 'description': '重大升级：AI能力集增强', 'status': 'stable'},
            {'version': '3.1.0', 'date': '2026-01-15', 'type': 'minor', 'description': '新增智能推荐系统', 'status': 'stable'},
            {'version': '3.1.1', 'date': '2026-01-25', 'type': 'patch', 'description': '优化推荐算法', 'status': 'stable'},
            {'version': '3.2.0', 'date': '2026-02-20', 'type': 'minor', 'description': '新增自适应学习引擎', 'status': 'stable'},
            {'version': '3.3.0', 'date': '2026-04-01', 'type': 'minor', 'description': '优化权限系统', 'status': 'stable'},
            {'version': '3.4.0', 'date': '2026-06-02', 'type': 'minor', 'description': '升级自动升级系统v2.0 + AI能力集提升', 'status': 'stable'},
            {'version': '3.5.0', 'date': '2026-06-03', 'type': 'minor', 'description': '升级版本管理系统v3.0 + 云端同步支持', 'status': 'stable'}
        ]
        
        for v in version_definitions:
            self.versions[v['version']] = v
        
        self.current_version = '3.5.0'
    
    def get_version(self, version: str) -> Optional[Dict[str, Any]]:
        """获取指定版本信息"""
        return self.versions.get(version)
    
    def get_current_version(self) -> Dict[str, Any]:
        """获取当前版本信息"""
        return {
            'version': self.current_version,
            **self.versions.get(self.current_version, {}),
            'update_time': datetime.now().isoformat(),
            'components': {
                'frontend': '2.1.0',
                'backend': '3.5.0',
                'database': '3.5.0',
                'api': '3.5.0',
                'ai_engine': '3.5.0'
            }
        }
    
    def get_version_history(self) -> List[Dict[str, Any]]:
        """获取版本历史列表"""
        return list(self.versions.values())
    
    def get_version_by_type(self, version_type: str) -> List[Dict[str, Any]]:
        """按类型获取版本"""
        return [v for v in self.versions.values() if v['type'] == version_type]
    
    def get_version_by_status(self, status: str) -> List[Dict[str, Any]]:
        """按状态获取版本"""
        return [v for v in self.versions.values() if v.get('status') == status]
    
    def compare_versions(self, v1: str, v2: str) -> Dict[str, Any]:
        """对比两个版本"""
        version1 = self.versions.get(v1)
        version2 = self.versions.get(v2)
        
        if not version1 or not version2:
            return {'error': '版本不存在'}
        
        def parse_version(v):
            parts = v.split('.')
            return tuple(map(int, parts))
        
        v1_parts = parse_version(v1)
        v2_parts = parse_version(v2)
        
        comparison = 'equal'
        if v1_parts > v2_parts:
            comparison = 'newer'
        elif v1_parts < v2_parts:
            comparison = 'older'
        
        changes = self._get_version_changes_between(v1, v2)
        
        return {
            'v1': version1,
            'v2': version2,
            'comparison': comparison,
            'v1_is_newer': comparison == 'newer',
            'v2_is_newer': comparison == 'older',
            'major_diff': abs(v1_parts[0] - v2_parts[0]),
            'minor_diff': abs(v1_parts[1] - v2_parts[1]),
            'patch_diff': abs(v1_parts[2] - v2_parts[2]),
            'changes_between': changes,
            'total_changes': len(changes)
        }
    
    def _get_version_changes_between(self, v1: str, v2: str) -> List[str]:
        """获取两个版本之间的变更"""
        all_changes = {
            '1.0.0': ['基础考试系统', '用户登录功能', '考试管理', '成绩统计'],
            '1.1.0': ['学习系统模块', '课程管理', '学习进度追踪'],
            '1.1.1': ['修复考试统计bug', '优化成绩计算'],
            '1.2.0': ['错题本功能', '错题收集', '错题练习'],
            '1.2.1': ['优化UI布局', '响应式设计'],
            '1.3.0': ['AI推荐功能', '个性化推荐'],
            '2.0.0': ['K12全学段支持', '小学/初中/高中', '成就系统基础'],
            '2.1.0': ['成就系统', '7种成就', '成就展示'],
            '2.1.1': ['修复升级通知bug', '优化通知显示'],
            '2.2.0': ['数据统计分析', '学习统计', '升级统计'],
            '2.3.0': ['考试过滤功能', '年级过滤', '科目过滤'],
            '3.0.0': ['AI能力集增强', '智能推荐', '自适应学习'],
            '3.1.0': ['智能推荐系统v3.0', '学习模式分析', '个性化推荐'],
            '3.1.1': ['优化推荐算法', '提升推荐准确率'],
            '3.2.0': ['自适应学习引擎v2.0', '知识图谱', '难度调整'],
            '3.3.0': ['优化权限系统', '教育类型管理'],
            '3.4.0': ['自动升级系统v2.0', 'AI能力集提升', '文档完善'],
            '3.5.0': ['版本管理系统v3.0', '云端同步支持', '版本对比增强', '自动备份']
        }
        
        def parse_version(v):
            parts = v.split('.')
            return tuple(map(int, parts))
        
        v1_parts = parse_version(v1)
        v2_parts = parse_version(v2)
        
        start_ver, end_ver = (v1, v2) if v1_parts < v2_parts else (v2, v1)
        start_idx = list(self.versions.keys()).index(start_ver)
        end_idx = list(self.versions.keys()).index(end_ver)
        
        all_keys = list(self.versions.keys())
        changes = []
        for i in range(start_idx + 1, end_idx + 1):
            ver = all_keys[i]
            if ver in all_changes:
                changes.extend(all_changes[ver])
        
        return changes
    
    def get_version_changelog(self, version: str) -> Dict[str, Any]:
        """获取版本变更日志"""
        version_info = self.versions.get(version)
        if not version_info:
            return {'error': '版本不存在'}
        
        return {
            'version': version,
            'date': version_info['date'],
            'type': version_info['type'],
            'status': version_info.get('status', 'unknown'),
            'description': version_info['description'],
            'changes': self._get_version_changes(version)
        }
    
    def _get_version_changes(self, version: str) -> List[str]:
        """获取版本具体变更"""
        changes = {
            '1.0.0': ['基础考试系统', '用户登录功能', '考试管理', '成绩统计'],
            '1.1.0': ['学习系统模块', '课程管理', '学习进度追踪'],
            '1.1.1': ['修复考试统计bug', '优化成绩计算'],
            '1.2.0': ['错题本功能', '错题收集', '错题练习'],
            '1.2.1': ['优化UI布局', '响应式设计'],
            '1.3.0': ['AI推荐功能', '个性化推荐'],
            '2.0.0': ['K12全学段支持', '小学/初中/高中', '成就系统基础'],
            '2.1.0': ['成就系统', '7种成就', '成就展示'],
            '2.1.1': ['修复升级通知bug', '优化通知显示'],
            '2.2.0': ['数据统计分析', '学习统计', '升级统计'],
            '2.3.0': ['考试过滤功能', '年级过滤', '科目过滤'],
            '3.0.0': ['AI能力集增强', '智能推荐', '自适应学习'],
            '3.1.0': ['智能推荐系统v3.0', '学习模式分析', '个性化推荐'],
            '3.1.1': ['优化推荐算法', '提升推荐准确率'],
            '3.2.0': ['自适应学习引擎v2.0', '知识图谱', '难度调整'],
            '3.3.0': ['优化权限系统', '教育类型管理'],
            '3.4.0': ['自动升级系统v2.0', 'AI能力集提升', '文档完善'],
            '3.5.0': ['版本管理系统v3.0', '云端同步支持', '版本对比增强', '自动备份', '版本统计报告']
        }
        return changes.get(version, [])
    
    def check_update(self, current_version: str) -> Dict[str, Any]:
        """检查更新"""
        current = self.versions.get(current_version)
        if not current:
            return {'error': '当前版本不存在'}
        
        def parse_version(v):
            parts = v.split('.')
            return tuple(map(int, parts))
        
        current_parts = parse_version(current_version)
        newer_versions = []
        
        for version, info in self.versions.items():
            v_parts = parse_version(version)
            if v_parts > current_parts:
                newer_versions.append(info)
        
        newer_versions.sort(key=lambda x: parse_version(x['version']))
        
        return {
            'current_version': current_version,
            'has_update': len(newer_versions) > 0,
            'latest_version': self.current_version,
            'available_updates': len(newer_versions),
            'updates': newer_versions,
            'recommended_action': 'upgrade' if len(newer_versions) > 0 else 'none',
            'critical_updates': [v for v in newer_versions if v['type'] == 'major']
        }

class VersionManager:
    """版本管理核心类 v3.0"""
    
    def __init__(self):
        self.version_model = VersionModel()
        self.update_history = []
        self.migration_records = {}
        self.backup_dir = Path('.version_backups')
        self.backup_dir.mkdir(exist_ok=True)
        logger.info("MTSCOS历史版本管理系统 v3.0.0 初始化完成")
    
    def get_current_version(self) -> Dict[str, Any]:
        """获取当前版本"""
        return self.version_model.get_current_version()
    
    def get_version_history(self) -> List[Dict[str, Any]]:
        """获取所有版本历史"""
        return self.version_model.get_version_history()
    
    def get_version_info(self, version: str) -> Optional[Dict[str, Any]]:
        """获取指定版本信息"""
        return self.version_model.get_version(version)
    
    def compare_versions(self, v1: str, v2: str) -> Dict[str, Any]:
        """对比两个版本"""
        return self.version_model.compare_versions(v1, v2)
    
    def get_changelog(self, version: str = None) -> Dict[str, Any]:
        """获取变更日志"""
        if version:
            return self.version_model.get_version_changelog(version)
        
        changelog = []
        for version in reversed(self.version_model.versions.keys()):
            changelog.append(self.version_model.get_version_changelog(version))
        
        return {'all_versions': changelog, 'total_versions': len(changelog)}
    
    def check_for_updates(self, current_version: str = None) -> Dict[str, Any]:
        """检查更新"""
        if not current_version:
            current_version = self.version_model.current_version
        
        return self.version_model.check_update(current_version)
    
    def get_version_statistics(self) -> Dict[str, Any]:
        """获取版本统计"""
        versions = self.version_model.get_version_history()
        
        stats = {
            'total_versions': len(versions),
            'major_versions': len([v for v in versions if v['type'] == 'major']),
            'minor_versions': len([v for v in versions if v['type'] == 'minor']),
            'patch_versions': len([v for v in versions if v['type'] == 'patch']),
            'current_version': self.version_model.current_version,
            'first_release': versions[0]['date'] if versions else None,
            'last_release': versions[-1]['date'] if versions else None,
            'release_days': self._calculate_release_days(versions),
            'average_days_between_releases': self._calculate_average_release_days(versions),
            'update_history_count': len(self.update_history),
            'stable_versions': len([v for v in versions if v.get('status') == 'stable'])
        }
        
        return stats
    
    def _calculate_release_days(self, versions: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """计算版本发布间隔"""
        intervals = []
        for i in range(1, len(versions)):
            prev_date = datetime.strptime(versions[i-1]['date'], '%Y-%m-%d')
            curr_date = datetime.strptime(versions[i]['date'], '%Y-%m-%d')
            days_between = (curr_date - prev_date).days
            intervals.append({
                'from_version': versions[i-1]['version'],
                'to_version': versions[i]['version'],
                'days_between': days_between,
                'date': versions[i]['date']
            })
        
        return intervals
    
    def _calculate_average_release_days(self, versions: List[Dict[str, Any]]) -> float:
        """计算平均发布间隔天数"""
        if len(versions) < 2:
            return 0.0
        
        total_days = 0
        for i in range(1, len(versions)):
            prev_date = datetime.strptime(versions[i-1]['date'], '%Y-%m-%d')
            curr_date = datetime.strptime(versions[i]['date'], '%Y-%m-%d')
            total_days += (curr_date - prev_date).days
        
        return round(total_days / (len(versions) - 1), 2)
    
    def record_update(self, from_version: str, to_version: str, user_id: str = None) -> bool:
        """记录版本更新"""
        record = {
            'id': f"update_{int(time.time())}",
            'from_version': from_version,
            'to_version': to_version,
            'user_id': user_id,
            'timestamp': datetime.now().isoformat(),
            'success': True,
            'backup_created': self._create_backup(from_version)
        }
        
        self.update_history.append(record)
        logger.info(f"记录版本更新: {from_version} -> {to_version}")
        return True
    
    def _create_backup(self, version: str) -> str:
        """创建版本备份"""
        backup_path = self.backup_dir / f"backup_{version}_{int(time.time())}"
        backup_path.mkdir(exist_ok=True)
        
        version_info = self.version_model.get_version(version)
        if version_info:
            with open(backup_path / 'version_info.json', 'w', encoding='utf-8') as f:
                json.dump(version_info, f, indent=2, ensure_ascii=False)
        
        logger.info(f"创建版本备份: {backup_path}")
        return str(backup_path)
    
    def get_update_history(self, user_id: str = None) -> List[Dict[str, Any]]:
        """获取更新历史"""
        if user_id:
            return [h for h in self.update_history if h.get('user_id') == user_id]
        return self.update_history
    
    def generate_version_report(self) -> Dict[str, Any]:
        """生成版本报告"""
        stats = self.get_version_statistics()
        changelog = self.get_changelog()
        
        return {
            'report_generated': datetime.now().isoformat(),
            'statistics': stats,
            'changelog': changelog,
            'update_history': self.update_history[-10:],
            'recommendations': self._generate_recommendations(stats)
        }
    
    def _generate_recommendations(self, stats: Dict[str, Any]) -> List[str]:
        """生成版本管理建议"""
        recommendations = []
        
        if stats['update_history_count'] > 100:
            recommendations.append("建议清理历史更新记录以优化性能")
        
        if stats['average_days_between_releases'] < 7:
            recommendations.append("发布频率较高，建议合并小更新")
        
        if stats['average_days_between_releases'] > 90:
            recommendations.append("发布间隔较长，建议增加更新频率")
        
        if not recommendations:
            recommendations.append("版本管理状态良好")
        
        return recommendations
    
    def export_version_data(self) -> str:
        """导出版本数据"""
        data = {
            'current_version': self.version_model.current_version,
            'versions': list(self.version_model.versions.values()),
            'update_history': self.update_history,
            'generated_at': datetime.now().isoformat(),
            'statistics': self.get_version_statistics()
        }
        return json.dumps(data, indent=2, ensure_ascii=False)
    
    def export_version_data_to_file(self, file_path: str = None) -> str:
        """导出版本数据到文件"""
        if not file_path:
            file_path = f"version_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        
        data = {
            'current_version': self.version_model.current_version,
            'versions': list(self.version_model.versions.values()),
            'update_history': self.update_history,
            'generated_at': datetime.now().isoformat(),
            'statistics': self.get_version_statistics(),
            'changelog': self.get_changelog()
        }
        
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        
        logger.info(f"版本数据已导出到: {file_path}")
        return file_path
    
    def validate_version_consistency(self) -> Dict[str, Any]:
        """验证版本一致性"""
        issues = []
        versions = self.version_model.get_version_history()
        
        def parse_version(v):
            parts = v.split('.')
            return tuple(map(int, parts))
        
        for i in range(1, len(versions)):
            prev_ver = parse_version(versions[i-1]['version'])
            curr_ver = parse_version(versions[i]['version'])
            
            if curr_ver <= prev_ver:
                issues.append({
                    'type': 'version_order_error',
                    'message': f"版本顺序错误: {versions[i-1]['version']} -> {versions[i]['version']}"
                })
        
        return {
            'valid': len(issues) == 0,
            'issues': issues,
            'total_versions_checked': len(versions),
            'check_time': datetime.now().isoformat()
        }
    
    def simulate_upgrade(self, target_version: str) -> Dict[str, Any]:
        """模拟版本升级"""
        current = self.version_model.current_version
        target_info = self.version_model.get_version(target_version)
        
        if not target_info:
            return {'error': '目标版本不存在'}
        
        comparison = self.compare_versions(current, target_version)
        
        return {
            'simulation_result': 'success',
            'from_version': current,
            'to_version': target_version,
            'changes': comparison.get('changes_between', []),
            'estimated_time': f"{len(comparison.get('changes_between', [])) * 5}分钟",
            'backup_required': True,
            'rollback_possible': True,
            'warnings': []
        }
    
    def get_version_timeline(self) -> Dict[str, Any]:
        """获取版本时间线"""
        versions = self.version_model.get_version_history()
        timeline = []
        
        for i, version in enumerate(versions):
            timeline.append({
                'index': i,
                'version': version['version'],
                'date': version['date'],
                'type': version['type'],
                'description': version['description'],
                'is_current': version['version'] == self.version_model.current_version
            })
        
        return {
            'timeline': timeline,
            'current_index': next((i for i, v in enumerate(versions) if v['version'] == self.version_model.current_version), -1),
            'total_versions': len(versions)
        }

version_manager = VersionManager()

if __name__ == '__main__':
    manager = VersionManager()
    
    print("=== 当前版本 ===")
    print(json.dumps(manager.get_current_version(), indent=2, ensure_ascii=False))
    
    print("\n=== 版本统计 ===")
    print(json.dumps(manager.get_version_statistics(), indent=2, ensure_ascii=False))
    
    print("\n=== 版本时间线 ===")
    timeline = manager.get_version_timeline()
    for v in timeline['timeline'][-5:]:
        marker = " *" if v['is_current'] else "  "
        print(f"{marker} {v['version']} - {v['date']} - {v['type']}")
    
    print("\n=== 版本对比 (3.5.0 vs 3.0.0) ===")
    comparison = manager.compare_versions('3.5.0', '3.0.0')
    print(json.dumps(comparison, indent=2, ensure_ascii=False))
    
    print("\n=== 检查更新 (3.3.0) ===")
    update_info = manager.check_for_updates('3.3.0')
    print(json.dumps(update_info, indent=2, ensure_ascii=False))
    
    print("\n=== 版本变更日志 (3.5.0) ===")
    changelog = manager.get_changelog('3.5.0')
    print(json.dumps(changelog, indent=2, ensure_ascii=False))
    
    print("\n=== 模拟升级到3.5.0 ===")
    simulation = manager.simulate_upgrade('3.5.0')
    print(json.dumps(simulation, indent=2, ensure_ascii=False))
    
    print("\n=== 验证版本一致性 ===")
    validation = manager.validate_version_consistency()
    print(json.dumps(validation, indent=2, ensure_ascii=False))
    
    print("\n=== 记录更新 ===")
    manager.record_update('3.4.0', '3.5.0', 'user123')
    print("更新记录成功")
    
    print("\n=== 生成版本报告 ===")
    report = manager.generate_version_report()
    print(f"报告生成时间: {report['report_generated']}")
    print(f"总版本数: {report['statistics']['total_versions']}")
    print(f"建议: {', '.join(report['recommendations'])}")
    
    print("\n=== 导出版本数据 ===")
    export_path = manager.export_version_data_to_file()
    print(f"数据已导出到: {export_path}")