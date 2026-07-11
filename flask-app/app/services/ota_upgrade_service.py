import logging
logger = logging.getLogger(__name__)

# -*- coding: utf-8 -*-
#!/usr/bin/env python3
"""
OTA升级服务
为系统各子服务器提供远程固件升级功能
"""

import os
import sys
import json
import uuid
import hashlib
import shutil
from datetime import datetime
from typing import Dict, List, Optional, Any

# 设置固件存储目录
FIRMWARE_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'firmware')
os.makedirs(FIRMWARE_DIR, exist_ok=True)

class OTAUpgradeService:
    """OTA升级服务核心类"""
    
    def __init__(self):
        self.firmwares = {}
        self.devices = {}
        self.upgrade_tasks = {}
        self._load_firmwares()
        self._load_devices()
    
    def _load_firmwares(self) -> None:
        """加载已存储的固件信息"""
        firmware_info_file = os.path.join(FIRMWARE_DIR, 'firmwares.json')
        if os.path.exists(firmware_info_file):
            try:
                with open(firmware_info_file, 'r', encoding='utf-8') as f:
                    self.firmwares = json.load(f)
            except Exception as e:
                print(f"加载固件信息失败: {e}")
    
    def _save_firmwares(self) -> None:
        """保存固件信息"""
        firmware_info_file = os.path.join(FIRMWARE_DIR, 'firmwares.json')
        with open(firmware_info_file, 'w', encoding='utf-8') as f:
            json.dump(self.firmwares, f, indent=2)
    
    def _load_devices(self) -> None:
        """加载设备信息"""
        devices_file = os.path.join(FIRMWARE_DIR, 'devices.json')
        if os.path.exists(devices_file):
            try:
                with open(devices_file, 'r', encoding='utf-8') as f:
                    self.devices = json.load(f)
            except Exception as e:
                print(f"加载设备信息失败: {e}")
    
    def _save_devices(self) -> None:
        """保存设备信息"""
        devices_file = os.path.join(FIRMWARE_DIR, 'devices.json')
        with open(devices_file, 'w', encoding='utf-8') as f:
            json.dump(self.devices, f, indent=2)
    
    def calculate_hash(self, file_path: str) -> str:
        """计算文件SHA256哈希值"""
        sha256_hash = hashlib.sha256()
        with open(file_path, 'rb') as f:
            for chunk in iter(lambda: f.read(4096), b""):
                sha256_hash.update(chunk)
        return sha256_hash.hexdigest()
    
    def upload_firmware(self, file_path: str, device_type: str, version: str, 
                       description: str = "", release_notes: str = "") -> Dict[str, Any]:
        """上传固件"""
        try:
            if not os.path.exists(file_path):
                return {'success': False, 'message': '固件文件不存在'}
            
            file_name = os.path.basename(file_path)
            firmware_id = str(uuid.uuid4())[:8]
            
            # 创建版本目录
            version_dir = os.path.join(FIRMWARE_DIR, device_type, version)
            os.makedirs(version_dir, exist_ok=True)
            
            # 复制固件文件
            dest_path = os.path.join(version_dir, file_name)
            shutil.copy(file_path, dest_path)
            
            # 计算哈希值
            file_hash = self.calculate_hash(dest_path)
            file_size = os.path.getsize(dest_path)
            
            # 保存固件信息
            firmware_info = {
                'firmware_id': firmware_id,
                'device_type': device_type,
                'version': version,
                'file_name': file_name,
                'file_path': dest_path,
                'file_hash': file_hash,
                'file_size': file_size,
                'description': description,
                'release_notes': release_notes,
                'uploaded_at': datetime.now().isoformat(),
                'status': 'active',
                'download_count': 0
            }
            
            if device_type not in self.firmwares:
                self.firmwares[device_type] = {}
            self.firmwares[device_type][version] = firmware_info
            
            self._save_firmwares()
            
            return {
                'success': True,
                'message': '固件上传成功',
                'firmware_id': firmware_id,
                'device_type': device_type,
                'version': version,
                'file_hash': file_hash,
                'file_size': file_size
            }
        except Exception as e:
            return {'success': False, 'message': f'上传失败: {str(e)}'}
    
    def get_firmware_list(self, device_type: str = None) -> Dict[str, Any]:
        """获取固件列表"""
        try:
            if device_type:
                if device_type in self.firmwares:
                    return {
                        'success': True,
                        'device_type': device_type,
                        'firmwares': list(self.firmwares[device_type].values())
                    }
                return {'success': False, 'message': '设备类型不存在'}
            
            all_firmwares = []
            for device_type, versions in self.firmwares.items():
                all_firmwares.extend(list(versions.values()))
            
            return {
                'success': True,
                'firmwares': all_firmwares,
                'count': len(all_firmwares)
            }
        except Exception as e:
            return {'success': False, 'message': f'获取固件列表失败: {str(e)}'}
    
    def get_firmware_info(self, device_type: str, version: str) -> Dict[str, Any]:
        """获取固件详细信息"""
        try:
            if device_type in self.firmwares and version in self.firmwares[device_type]:
                return {
                    'success': True,
                    'firmware': self.firmwares[device_type][version]
                }
            return {'success': False, 'message': '固件不存在'}
        except Exception as e:
            return {'success': False, 'message': f'获取固件信息失败: {str(e)}'}
    
    def delete_firmware(self, device_type: str, version: str) -> Dict[str, Any]:
        """删除固件"""
        try:
            if device_type in self.firmwares and version in self.firmwares[device_type]:
                firmware = self.firmwares[device_type][version]
                
                # 删除文件
                if os.path.exists(firmware['file_path']):
                    os.remove(firmware['file_path'])
                
                # 删除目录(如果为空)
                version_dir = os.path.dirname(firmware['file_path'])
                if os.path.exists(version_dir) and len(os.listdir(version_dir)) == 0:
                    os.rmdir(version_dir)
                
                # 删除记录
                del self.firmwares[device_type][version]
                if not self.firmwares[device_type]:
                    del self.firmwares[device_type]
                
                self._save_firmwares()
                
                return {'success': True, 'message': '固件删除成功'}
            
            return {'success': False, 'message': '固件不存在'}
        except Exception as e:
            return {'success': False, 'message': f'删除固件失败: {str(e)}'}
    
    def register_device(self, device_id: str, device_type: str, current_version: str,
                       device_name: str = "", metadata: Dict = None) -> Dict[str, Any]:
        """注册设备"""
        try:
            device_info = {
                'device_id': device_id,
                'device_type': device_type,
                'device_name': device_name or device_id,
                'current_version': current_version,
                'metadata': metadata or {},
                'registered_at': datetime.now().isoformat(),
                'last_seen': datetime.now().isoformat(),
                'status': 'online',
                'upgrade_status': 'idle'
            }
            
            self.devices[device_id] = device_info
            self._save_devices()
            
            return {
                'success': True,
                'message': '设备注册成功',
                'device_id': device_id
            }
        except Exception as e:
            return {'success': False, 'message': f'注册设备失败: {str(e)}'}
    
    def get_device_info(self, device_id: str) -> Dict[str, Any]:
        """获取设备信息"""
        try:
            if device_id in self.devices:
                return {
                    'success': True,
                    'device': self.devices[device_id]
                }
            return {'success': False, 'message': '设备不存在'}
        except Exception as e:
            return {'success': False, 'message': f'获取设备信息失败: {str(e)}'}
    
    def get_device_list(self, device_type: str = None) -> Dict[str, Any]:
        """获取设备列表"""
        try:
            if device_type:
                devices = [d for d in self.devices.values() if d['device_type'] == device_type]
                return {
                    'success': True,
                    'device_type': device_type,
                    'devices': devices,
                    'count': len(devices)
                }
            
            return {
                'success': True,
                'devices': list(self.devices.values()),
                'count': len(self.devices)
            }
        except Exception as e:
            return {'success': False, 'message': f'获取设备列表失败: {str(e)}'}
    
    def update_device_status(self, device_id: str, status: str = None, 
                            current_version: str = None) -> Dict[str, Any]:
        """更新设备状态"""
        try:
            if device_id not in self.devices:
                return {'success': False, 'message': '设备不存在'}
            
            device = self.devices[device_id]
            
            if status:
                device['status'] = status
            if current_version:
                device['current_version'] = current_version
            device['last_seen'] = datetime.now().isoformat()
            
            self._save_devices()
            
            return {'success': True, 'message': '设备状态更新成功'}
        except Exception as e:
            return {'success': False, 'message': f'更新设备状态失败: {str(e)}'}
    
    def _parse_version(self, version: str) -> list:
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
    
    def _compare_versions(self, new_version: str, old_version: str) -> bool:
        """比较版本号大小,支持dev/plc/beta等后缀"""
        suffix_priority = {'': 0, 'dev': 1, 'alpha': 2, 'beta': 3, 'rc': 4, 'plc': 5}
        
        def get_priority(suffix):
            if suffix.startswith('rc'):
                return (suffix_priority['rc'], int(suffix[2:]) if suffix[2:].isdigit() else 0)
            return (suffix_priority.get(suffix, 99), 0)
        
        new_parts = self._parse_version(new_version)
        new_suffix = self._get_version_suffix(new_version)
        
        old_parts = self._parse_version(old_version)
        old_suffix = self._get_version_suffix(old_version)
        
        for n, o in zip(new_parts, old_parts):
            if n > o:
                return True
            elif n < o:
                return False
        
        new_prio = get_priority(new_suffix)
        old_prio = get_priority(old_suffix)
        
        return new_prio > old_prio
    
    def check_update(self, device_id: str) -> Dict[str, Any]:
        """检查设备是否有可用更新"""
        try:
            if device_id not in self.devices:
                return {'success': False, 'message': '设备不存在'}
            
            device = self.devices[device_id]
            device_type = device['device_type']
            current_version = device['current_version']
            
            if device_type not in self.firmwares:
                return {'success': True, 'message': '暂无可用固件', 'has_update': False}
            
            versions = list(self.firmwares[device_type].keys())
            if not versions:
                return {'success': True, 'message': '暂无可用固件', 'has_update': False}
            
            latest_version = versions[0]
            for version in versions[1:]:
                if self._compare_versions(version, latest_version):
                    latest_version = version
            
            has_update = self._compare_versions(latest_version, current_version)
            
            if has_update:
                firmware = self.firmwares[device_type][latest_version]
                return {
                    'success': True,
                    'has_update': True,
                    'current_version': current_version,
                    'latest_version': latest_version,
                    'firmware': {
                        'firmware_id': firmware['firmware_id'],
                        'version': firmware['version'],
                        'file_size': firmware['file_size'],
                        'file_hash': firmware['file_hash'],
                        'description': firmware['description'],
                        'release_notes': firmware['release_notes']
                    }
                }
            
            return {
                'success': True,
                'has_update': False,
                'current_version': current_version,
                'latest_version': latest_version,
                'message': '当前已是最新版本'
            }
        except Exception as e:
            return {'success': False, 'message': f'检查更新失败: {str(e)}'}
    
    def start_upgrade(self, device_id: str, version: str = None) -> Dict[str, Any]:
        """开始升级任务"""
        try:
            if device_id not in self.devices:
                return {'success': False, 'message': '设备不存在'}
            
            device = self.devices[device_id]
            device_type = device['device_type']
            
            if device_type not in self.firmwares:
                return {'success': False, 'message': '该设备类型暂无固件'}
            
            # 确定目标版本
            if version:
                if version not in self.firmwares[device_type]:
                    return {'success': False, 'message': '指定版本不存在'}
                target_version = version
            else:
                target_version = max(self.firmwares[device_type].keys())
            
            firmware = self.firmwares[device_type][target_version]
            
            task_id = str(uuid.uuid4())[:8]
            upgrade_task = {
                'task_id': task_id,
                'device_id': device_id,
                'device_type': device_type,
                'target_version': target_version,
                'firmware_id': firmware['firmware_id'],
                'status': 'pending',
                'progress': 0,
                'started_at': datetime.now().isoformat(),
                'updated_at': datetime.now().isoformat(),
                'error_message': None
            }
            
            self.upgrade_tasks[task_id] = upgrade_task
            
            # 更新设备升级状态
            device['upgrade_status'] = 'upgrading'
            self._save_devices()
            
            return {
                'success': True,
                'message': '升级任务已创建',
                'task_id': task_id,
                'target_version': target_version
            }
        except Exception as e:
            return {'success': False, 'message': f'创建升级任务失败: {str(e)}'}
    
    def get_upgrade_task(self, task_id: str) -> Dict[str, Any]:
        """获取升级任务状态"""
        try:
            if task_id in self.upgrade_tasks:
                return {
                    'success': True,
                    'task': self.upgrade_tasks[task_id]
                }
            return {'success': False, 'message': '任务不存在'}
        except Exception as e:
            return {'success': False, 'message': f'获取任务状态失败: {str(e)}'}
    
    def update_upgrade_progress(self, task_id: str, progress: int, status: str = None) -> Dict[str, Any]:
        """更新升级进度"""
        try:
            if task_id not in self.upgrade_tasks:
                return {'success': False, 'message': '任务不存在'}
            
            task = self.upgrade_tasks[task_id]
            task['progress'] = min(max(0, progress), 100)
            
            if status:
                task['status'] = status
            
            task['updated_at'] = datetime.now().isoformat()
            
            # 更新设备状态
            if status == 'completed':
                device = self.devices.get(task['device_id'])
                if device:
                    device['current_version'] = task['target_version']
                    device['upgrade_status'] = 'idle'
                    self._save_devices()
            
            return {'success': True, 'message': '进度更新成功'}
        except Exception as e:
            return {'success': False, 'message': f'更新进度失败: {str(e)}'}
    
    def get_upgrade_history(self, device_id: str = None) -> Dict[str, Any]:
        """获取升级历史"""
        try:
            if device_id:
                history = [t for t in self.upgrade_tasks.values() if t['device_id'] == device_id]
            else:
                history = list(self.upgrade_tasks.values())
            
            history.sort(key=lambda x: x['started_at'], reverse=True)
            
            return {
                'success': True,
                'history': history[:50],
                'count': len(history)
            }
        except Exception as e:
            return {'success': False, 'message': f'获取升级历史失败: {str(e)}'}

class OTAServerAdapter:
    """OTA服务器适配器 - 支持多种子服务器类型"""
    
    SUPPORTED_SERVERS = [
        'main_server',
        'exam_server',
        'arduino_server',
        'monitoring_server',
        'api_server',
        'database_server',
        'ai_server',
        'file_server'
    ]
    
    def __init__(self):
        self.ota_service = OTAUpgradeService()
    
    def prepare_server_firmware(self, server_type: str, version: str, 
                               description: str = "", release_notes: str = "") -> Dict[str, Any]:
        """准备服务器固件(模拟生成)"""
        if server_type not in self.SUPPORTED_SERVERS:
            return {'success': False, 'message': f'不支持的服务器类型: {server_type}'}
        
        try:
            # 创建模拟固件文件
            firmware_content = f"""#!/usr/bin/env python3
# {server_type} firmware v{version}
# Generated: {datetime.now().isoformat()}
# Description: {description}
# Release Notes: {release_notes}

FIRMWARE_VERSION = "{version}"
SERVER_TYPE = "{server_type}"
"""
            
            # 创建临时固件文件
            temp_dir = os.path.join(FIRMWARE_DIR, 'temp')
            os.makedirs(temp_dir, exist_ok=True)
            temp_file = os.path.join(temp_dir, f'{server_type}_v{version}.fw')
            
            with open(temp_file, 'w', encoding='utf-8') as f:
                f.write(firmware_content)
            
            # 上传固件
            result = self.ota_service.upload_firmware(
                temp_file,
                server_type,
                version,
                description,
                release_notes
            )
            
            # 清理临时文件
            os.remove(temp_file)
            
            return result
        except Exception as e:
            return {'success': False, 'message': f'准备固件失败: {str(e)}'}
    
    def register_all_servers(self) -> Dict[str, Any]:
        """注册所有支持的服务器"""
        results = []
        for server_type in self.SUPPORTED_SERVERS:
            device_id = f'{server_type}_001'
            result = self.ota_service.register_device(
                device_id,
                server_type,
                '1.0.0',
                f'{server_type} primary'
            )
            results.append({
                'server_type': server_type,
                'device_id': device_id,
                'success': result['success'],
                'message': result['message']
            })
        
        return {
            'success': True,
            'results': results,
            'total': len(self.SUPPORTED_SERVERS)
        }
    
    def check_all_updates(self) -> Dict[str, Any]:
        """检查所有服务器的更新"""
        results = []
        for server_type in self.SUPPORTED_SERVERS:
            device_id = f'{server_type}_001'
            result = self.ota_service.check_update(device_id)
            results.append({
                'server_type': server_type,
                'device_id': device_id,
                'has_update': result.get('has_update', False),
                'current_version': result.get('current_version'),
                'latest_version': result.get('latest_version')
            })
        
        return {
            'success': True,
            'results': results,
            'total_servers': len(self.SUPPORTED_SERVERS),
            'servers_with_update': sum(1 for r in results if r['has_update'])
        }
    
    def upgrade_all_servers(self) -> Dict[str, Any]:
        """升级所有服务器"""
        results = []
        for server_type in self.SUPPORTED_SERVERS:
            device_id = f'{server_type}_001'
            result = self.ota_service.start_upgrade(device_id)
            results.append({
                'server_type': server_type,
                'device_id': device_id,
                'success': result['success'],
                'task_id': result.get('task_id'),
                'message': result.get('message')
            })
        
        return {
            'success': True,
            'results': results,
            'total': len(self.SUPPORTED_SERVERS),
            'success_count': sum(1 for r in results if r['success'])
        }

if __name__ == '__main__':
    ota_adapter = OTAServerAdapter()
    
    print("=== OTA升级服务测试 ===\n")
    
    print("1. 注册所有服务器:")
    reg_result = ota_adapter.register_all_servers()
    print(f"   注册服务器数量: {reg_result['total']}")
    
    print("\n2. 为所有服务器准备固件(支持多版本类型):")
    server_firmwares = {
        'main_server': ('2.0.0', '主服务器正式版', '- 修复安全漏洞\n- 性能优化\n- 新增OTA功能'),
        'exam_server': ('2.0.0-beta', '考试服务器Beta版', '- 新增考试功能\n- 优化答题体验\n- 修复成绩计算bug'),
        'arduino_server': ('2.0.0-dev', 'Arduino服务器开发版', '- 新增COM口监听\n- 支持官方API\n- 代码编译优化'),
        'monitoring_server': ('2.0.0-plc', '监控服务器PLC版', '- 实时监控增强\n- 告警系统优化\n- 性能指标扩展'),
        'api_server': ('2.0.1', 'API服务器正式版', '- RESTful API优化\n- 接口文档更新\n- 性能提升'),
        'database_server': ('2.0.1-beta', '数据库服务器Beta版', '- 加密功能增强\n- 查询优化\n- 备份机制完善'),
        'ai_server': ('2.0.1-dev', 'AI服务器开发版', '- 模型优化\n- 推理速度提升\n- 多引擎支持'),
        'file_server': ('2.0.1-plc', '文件服务器PLC版', '- 存储优化\n- 上传速度提升\n- 安全性增强')
    }
    
    for server_type, (version, desc, notes) in server_firmwares.items():
        fw_result = ota_adapter.prepare_server_firmware(server_type, version, desc, notes)
        if fw_result['success']:
            print(f"   ✓ {server_type}: v{version}")
        else:
            print(f"   ✗ {server_type}: {fw_result.get('message', '失败')}")
    
    print("\n3. 检查所有服务器更新:")
    update_result = ota_adapter.check_all_updates()
    print(f"   服务器总数: {update_result['total_servers']}")
    print(f"   需要更新: {update_result['servers_with_update']}")
    for server in update_result['results']:
        status = "✓ 有更新" if server['has_update'] else "✗ 已是最新"
        print(f"   - {server['server_type']}: {server['current_version']} → {server['latest_version']} [{status}]")
    
    print("\n4. 获取设备列表:")
    devices = ota_adapter.ota_service.get_device_list()
    print(f"   设备数量: {devices['count']}")
    
    print("\n5. 获取固件列表:")
    firmwares = ota_adapter.ota_service.get_firmware_list()
    print(f"   固件数量: {firmwares['count']}")
    
    logger.info("\n == 测试完成 ===")
