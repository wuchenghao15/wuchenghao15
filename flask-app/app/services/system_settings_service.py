import logging
logger = logging.getLogger(__name__)

# -*- coding: utf-8 -*-
#!/usr/bin/env python3
"""
系统设置服务
提供版本管理、历史记录、自动升级和文档生成功能
"""

import os
import sys
import json
import uuid
import shutil
from datetime import datetime
from typing import Dict, List, Optional, Any

# 设置配置目录
CONFIG_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'config')
os.makedirs(CONFIG_DIR, exist_ok=True)

class SystemSettingsService:
    """系统设置服务核心类"""
    
    def __init__(self):
        self.settings = {}
        self.version_history = []
        self.current_version = "1.0.0"
        self._load_settings()
        self._load_version_history()
    
    def _load_settings(self) -> None:
        """加载系统设置"""
        settings_file = os.path.join(CONFIG_DIR, 'system_settings.json')
        if os.path.exists(settings_file):
            try:
                with open(settings_file, 'r', encoding='utf-8') as f:
                    self.settings = json.load(f)
                    self.current_version = self.settings.get('version', '1.0.0')
            except Exception as e:
                print(f"加载设置失败: {e}")
    
    def _save_settings(self) -> None:
        """保存系统设置"""
        settings_file = os.path.join(CONFIG_DIR, 'system_settings.json')
        with open(settings_file, 'w', encoding='utf-8') as f:
            json.dump(self.settings, f, indent=2, ensure_ascii=False)
    
    def _load_version_history(self) -> None:
        """加载版本历史"""
        history_file = os.path.join(CONFIG_DIR, 'version_history.json')
        if os.path.exists(history_file):
            try:
                with open(history_file, 'r', encoding='utf-8') as f:
                    self.version_history = json.load(f)
            except Exception as e:
                print(f"加载版本历史失败: {e}")
    
    def _save_version_history(self) -> None:
        """保存版本历史"""
        history_file = os.path.join(CONFIG_DIR, 'version_history.json')
        with open(history_file, 'w', encoding='utf-8') as f:
            json.dump(self.version_history, f, indent=2)
    
    def get_settings(self) -> Dict[str, Any]:
        """获取当前系统设置"""
        return {
            'success': True,
            'settings': self.settings,
            'version': self.current_version,
            'last_updated': self.settings.get('last_updated')
        }
    
    def update_settings(self, new_settings: Dict) -> Dict[str, Any]:
        """更新系统设置"""
        try:
            self.settings.update(new_settings)
            self.settings['last_updated'] = datetime.now().isoformat()
            self._save_settings()
            
            return {
                'success': True,
                'message': '设置更新成功',
                'settings': self.settings
            }
        except Exception as e:
            return {'success': False, 'message': f'更新设置失败: {str(e)}'}
    
    def set_setting(self, key: str, value: Any) -> Dict[str, Any]:
        """设置单个配置项"""
        try:
            self.settings[key] = value
            self.settings['last_updated'] = datetime.now().isoformat()
            self._save_settings()
            
            return {
                'success': True,
                'message': f'设置 {key} 成功',
                'key': key,
                'value': value
            }
        except Exception as e:
            return {'success': False, 'message': f'设置失败: {str(e)}'}
    
    def get_setting(self, key: str, default: Any = None) -> Dict[str, Any]:
        """获取单个配置项"""
        return {
            'success': True,
            'key': key,
            'value': self.settings.get(key, default)
        }
    
    def upgrade_version(self, new_version: str, description: str = "", 
                       changes: List[str] = None, author: str = "System") -> Dict[str, Any]:
        """升级系统版本"""
        try:
            # 验证版本格式
            if not self._validate_version(new_version):
                return {'success': False, 'message': '无效的版本格式'}
            
            # 检查版本号是否大于当前版本
            if not self._is_version_greater(new_version, self.current_version):
                return {'success': False, 'message': '新版本必须大于当前版本'}
            
            # 创建版本记录
            version_record = {
                'version': new_version,
                'previous_version': self.current_version,
                'description': description,
                'changes': changes or [],
                'author': author,
                'upgrade_date': datetime.now().isoformat(),
                'status': 'completed',
                'upgrade_id': str(uuid.uuid4())[:8]
            }
            
            # 添加到历史记录
            self.version_history.insert(0, version_record)
            
            # 限制历史记录数量
            if len(self.version_history) > 100:
                self.version_history = self.version_history[:100]
            
            # 更新当前版本
            self.current_version = new_version
            self.settings['version'] = new_version
            self.settings['last_updated'] = datetime.now().isoformat()
            
            # 保存
            self._save_settings()
            self._save_version_history()
            
            # 生成更新说明文档
            self.generate_update_documentation()
            
            return {
                'success': True,
                'message': f'版本升级成功: {self.current_version}',
                'version': new_version,
                'previous_version': version_record['previous_version'],
                'changes': changes,
                'upgrade_id': version_record['upgrade_id']
            }
        except Exception as e:
            return {'success': False, 'message': f'升级失败: {str(e)}'}
    
    def _validate_version(self, version: str) -> bool:
        """验证版本号格式"""
        import re
        pattern = r'^\d+\.\d+\.\d+(-(dev|plc|beta|alpha|rc\d+))?$'
        return bool(re.match(pattern, version))
    
    def _is_version_greater(self, new_version: str, old_version: str) -> bool:
        """比较版本号大小"""
        new_parts = self._parse_version(new_version)
        new_suffix = self._get_version_suffix(new_version)
        
        old_parts = self._parse_version(old_version)
        old_suffix = self._get_version_suffix(old_version)
        
        for n, o in zip(new_parts, old_parts):
            if n > o:
                return True
            elif n < o:
                return False
        
        return self._compare_suffix(new_suffix, old_suffix)
    
    def _parse_version(self, version: str) -> List[int]:
        """解析版本号"""
        import re
        parts = re.match(r'^(\d+)\.(\d+)\.(\d+)', version)
        if parts:
            return [int(parts.group(1)), int(parts.group(2)), int(parts.group(3))]
        return [0, 0, 0]
    
    def _get_version_suffix(self, version: str) -> str:
        """获取版本号后缀"""
        import re
        match = re.search(r'-(\w+)$', version)
        return match.group(1) if match else ''
    
    def _compare_suffix(self, new_suffix: str, old_suffix: str) -> bool:
        """比较版本后缀优先级"""
        suffix_priority = {'': 0, 'dev': 1, 'alpha': 2, 'beta': 3, 'rc': 4, 'plc': 5}
        
        def get_priority(suffix):
            if suffix.startswith('rc'):
                return (suffix_priority['rc'], int(suffix[2:]) if suffix[2:].isdigit() else 0)
            return (suffix_priority.get(suffix, 99), 0)
        
        new_prio = get_priority(new_suffix)
        old_prio = get_priority(old_suffix)
        
        return new_prio > old_prio
    
    def get_version_history(self, limit: int = 20) -> Dict[str, Any]:
        """获取版本历史记录"""
        return {
            'success': True,
            'current_version': self.current_version,
            'history': self.version_history[:limit],
            'total_count': len(self.version_history)
        }
    
    def get_version_info(self, version: str) -> Dict[str, Any]:
        """获取特定版本信息"""
        for record in self.version_history:
            if record['version'] == version:
                return {'success': True, 'version_info': record}
        return {'success': False, 'message': '版本未找到'}
    
    def generate_update_documentation(self) -> Dict[str, Any]:
        """生成更新说明文档"""
        try:
            doc_content = f"""# 系统更新说明文档

## 当前版本: {self.current_version}

### 生成时间
{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

---

## 版本历史

"""
            
            for i, record in enumerate(self.version_history[:20], 1):
                doc_content += f"""### {i}. v{record['version']} ({record['upgrade_date'][:10]})

**描述:** {record['description']}

**作者:** {record['author']}

**变更列表:**
"""
                if record['changes']:
                    for change in record['changes']:
                        doc_content += f"- {change}\n"
                else:
                    doc_content += "- 暂无详细变更\n"
                
                doc_content += "\n"
            
            doc_content += """---

## 系统信息

- **系统名称:** MTSCOS AI Project
- **当前版本:** {self.current_version}
- **版本总数:** {len(self.version_history)}
- **文档生成时间:** {datetime.now().isoformat()}

---

*此文档由系统自动生成*
"""
            
            doc_file = os.path.join(CONFIG_DIR, 'update_documentation.md')
            with open(doc_file, 'w', encoding='utf-8') as f:
                f.write(doc_content)
            
            return {
                'success': True,
                'message': '更新说明文档生成成功',
                'file_path': doc_file,
                'version': self.current_version
            }
        except Exception as e:
            return {'success': False, 'message': f'生成文档失败: {str(e)}'}
    
    def auto_upgrade(self) -> Dict[str, Any]:
        """自动检查并升级版本"""
        try:
            # 获取下一个版本号
            next_version = self._generate_next_version()
            
            # 创建更新说明
            changes = [
                '系统自动升级',
                '性能优化',
                '安全更新',
                'Bug修复'
            ]
            
            # 执行升级
            result = self.upgrade_version(
                next_version,
                '系统自动升级',
                changes,
                'Auto Upgrade'
            )
            
            if result['success']:
                # 生成文档
                self.generate_update_documentation()
            
            return result
        except Exception as e:
            return {'success': False, 'message': f'自动升级失败: {str(e)}'}
    
    def _generate_next_version(self) -> str:
        """生成下一个版本号"""
        parts = self._parse_version(self.current_version)
        parts[-1] += 1  # 增加修订号
        return f"{parts[0]}.{parts[1]}.{parts[2]}"
    
    def rollback_version(self, target_version: str) -> Dict[str, Any]:
        """回滚到指定版本"""
        try:
            # 找到目标版本记录
            target_record = None
            for record in self.version_history:
                if record['version'] == target_version:
                    target_record = record
                    break
            
            if not target_record:
                return {'success': False, 'message': '目标版本不存在'}
            
            # 创建回滚记录
            rollback_record = {
                'version': target_version,
                'previous_version': self.current_version,
                'description': f'回滚到 v{target_version}',
                'changes': [f'从 v{self.current_version} 回滚'],
                'author': 'System',
                'upgrade_date': datetime.now().isoformat(),
                'status': 'rollback',
                'upgrade_id': str(uuid.uuid4())[:8]
            }
            
            # 添加到历史记录
            self.version_history.insert(0, rollback_record)
            
            # 更新当前版本
            self.current_version = target_version
            self.settings['version'] = target_version
            self.settings['last_updated'] = datetime.now().isoformat()
            
            # 保存
            self._save_settings()
            self._save_version_history()
            
            # 生成文档
            self.generate_update_documentation()
            
            return {
                'success': True,
                'message': f'回滚成功: v{target_version}',
                'version': target_version,
                'from_version': rollback_record['previous_version']
            }
        except Exception as e:
            return {'success': False, 'message': f'回滚失败: {str(e)}'}
    
    def export_settings(self) -> Dict[str, Any]:
        """导出系统设置"""
        try:
            export_data = {
                'settings': self.settings,
                'current_version': self.current_version,
                'version_history': self.version_history,
                'export_time': datetime.now().isoformat()
            }
            
            export_file = os.path.join(CONFIG_DIR, f'settings_export_{datetime.now().strftime("%Y%m%d_%H%M%S")}.json')
            with open(export_file, 'w', encoding='utf-8') as f:
                json.dump(export_data, f, indent=2, ensure_ascii=False)
            
            return {
                'success': True,
                'message': '设置导出成功',
                'file_path': export_file
            }
        except Exception as e:
            return {'success': False, 'message': f'导出失败: {str(e)}'}
    
    def import_settings(self, file_path: str) -> Dict[str, Any]:
        """导入系统设置"""
        try:
            if not os.path.exists(file_path):
                return {'success': False, 'message': '文件不存在'}
            
            with open(file_path, 'r', encoding='utf-8') as f:
                import_data = json.load(f)
            
            self.settings = import_data.get('settings', {})
            self.current_version = import_data.get('current_version', '1.0.0')
            self.version_history = import_data.get('version_history', [])
            
            self._save_settings()
            self._save_version_history()
            
            return {
                'success': True,
                'message': '设置导入成功',
                'version': self.current_version,
                'history_count': len(self.version_history)
            }
        except Exception as e:
            return {'success': False, 'message': f'导入失败: {str(e)}'}

class VersionDashboard:
    """版本管理仪表盘"""
    
    def __init__(self):
        self.settings_service = SystemSettingsService()
    
    def get_dashboard_data(self) -> Dict[str, Any]:
        """获取仪表盘数据"""
        history = self.settings_service.get_version_history()
        
        recent_versions = history['history'][:5]
        version_stats = {
            'current_version': history['current_version'],
            'total_versions': history['total_count'],
            'recent_upgrades': len([v for v in recent_versions if v['status'] == 'completed']),
            'rollbacks': len([v for v in history['history'] if v['status'] == 'rollback'])
        }
        
        return {
            'success': True,
            'stats': version_stats,
            'recent_versions': recent_versions,
            'settings': self.settings_service.get_settings()['settings']
        }
    
    def get_changelog(self, version: str = None) -> Dict[str, Any]:
        """获取更新日志"""
        if version:
            return self.settings_service.get_version_info(version)
        
        history = self.settings_service.get_version_history()
        changelog = []
        
        for record in history['history']:
            changelog.append({
                'version': record['version'],
                'date': record['upgrade_date'],
                'description': record['description'],
                'changes': record['changes'],
                'author': record['author']
            })
        
        return {
            'success': True,
            'current_version': history['current_version'],
            'changelog': changelog
        }

if __name__ == '__main__':
    service = SystemSettingsService()
    dashboard = VersionDashboard()
    
    print("=== 系统设置服务测试 ===\n")
    
    print("1. 当前版本:")
    print(f"   v{service.current_version}")
    
    print("\n2. 升级版本到 2.0.0:")
    upgrade_result = service.upgrade_version(
        '2.0.0',
        '重大版本升级',
        [
            '新增OTA升级功能',
            '完善Arduino设计系统',
            '添加版本管理功能',
            '性能优化',
            '安全更新'
        ],
        'Admin'
    )
    print(f"   结果: {'成功' if upgrade_result['success'] else '失败'}")
    if upgrade_result['success']:
        print(f"   新版本: {upgrade_result['version']}")
    
    print("\n3. 自动升级:")
    auto_result = service.auto_upgrade()
    print(f"   结果: {'成功' if auto_result['success'] else '失败'}")
    if auto_result['success']:
        print(f"   当前版本: {auto_result['version']}")
    
    print("\n4. 获取版本历史:")
    history = service.get_version_history()
    print(f"   版本总数: {history['total_count']}")
    print(f"   当前版本: {history['current_version']}")
    print("   历史记录:")
    for i, record in enumerate(history['history'][:3], 1):
        status = "升级" if record['status'] == 'completed' else "回滚"
        print(f"     {i}. v{record['version']} ({status}) - {record['description']}")
    
    print("\n5. 生成更新文档:")
    doc_result = service.generate_update_documentation()
    print(f"   结果: {'成功' if doc_result['success'] else '失败'}")
    if doc_result['success']:
        print(f"   文件: {doc_result['file_path']}")
    
    print("\n6. 获取仪表盘数据:")
    dashboard_data = dashboard.get_dashboard_data()
    print(f"   当前版本: {dashboard_data['stats']['current_version']}")
    print(f"   版本总数: {dashboard_data['stats']['total_versions']}")
    
    logger.info("\n == 测试完成 ===")
