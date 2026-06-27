#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
MTSCOS系统自动适配器
自动检测、加载和配置新功能模块
"""
import os
import sys
import json
import importlib
import inspect
from datetime import datetime
from typing import Dict, List, Any, Optional
from pathlib import Path

class SystemAutoAdapter:
    """系统自动适配器"""

    def __init__(self, project_root: str = None):
        self.project_root = project_root or os.path.dirname(os.path.abspath(__file__))
        self.config_dir = os.path.join(self.project_root, 'config')
        self.modules_dir = os.path.join(self.project_root, 'app', 'modules')
        self.adapters_dir = os.path.join(self.project_root, 'adapters')
        self.system_config_path = os.path.join(self.project_root, 'system_config.json')

        os.makedirs(self.config_dir, exist_ok=True)
        os.makedirs(self.adapters_dir, exist_ok=True)

        self.loaded_modules = {}
        self.config_cache = {}
        self.module_registry = {}

    def detect_new_modules(self) -> List[Dict[str, Any]]:
        """检测新增模块"""
        detected = []

        # 检测json_auto_sync_system
        json_sync_path = os.path.join(self.project_root, 'json_auto_sync_system.py')
        if os.path.exists(json_sync_path):
            detected.append({
                'name': 'json_auto_sync',
                'type': 'sync_module',
                'path': json_sync_path,
                'version': '1.0.0',
                'description': 'JSON数据自动同步系统',
                'auto_start': True,
                'required': False
            })

        # 检测adapters目录下的适配器
        if os.path.exists(self.adapters_dir):
            for file in os.listdir(self.adapters_dir):
                if file.endswith('_adapter.py') and not file.startswith('__'):
                    adapter_name = file[:-3]
                    detected.append({
                        'name': adapter_name,
                        'type': 'adapter',
                        'path': os.path.join(self.adapters_dir, file),
                        'version': '1.0.0',
                        'description': f'{adapter_name}适配器',
                        'auto_start': True,
                        'required': False
                    })

        # 检测app/modules目录
        if os.path.exists(self.modules_dir):
            for root, dirs, files in os.walk(self.modules_dir):
                for file in files:
                    if file.endswith('.py') and not file.startswith('__') and not file.startswith('test_'):
                        module_name = file[:-3]
                        module_path = os.path.join(root, file)
                        relative_path = os.path.relpath(module_path, self.project_root)

                        detected.append({
                            'name': module_name,
                            'type': 'module',
                            'path': module_path,
                            'relative_path': relative_path,
                            'version': '1.0.0',
                            'description': f'{module_name}功能模块',
                            'auto_start': True,
                            'required': False
                        })

        print(f"✓ 检测到 {len(detected)} 个新模块")
        return detected

    def load_system_config(self) -> Dict[str, Any]:
        """加载系统配置"""
        try:
            if os.path.exists(self.system_config_path):
                with open(self.system_config_path, 'r', encoding='utf-8') as f:
                    config = json.load(f)
                print(f"✓ 已加载系统配置: {self.system_config_path}")
                return config
            else:
                print(f"⚠ 配置文件不存在，创建默认配置")
                return self.create_default_config()
        except Exception as e:
            print(f"✗ 加载配置失败: {e}")
            return {}

    def create_default_config(self) -> Dict[str, Any]:
        """创建默认系统配置"""
        default_config = {
            'version': '3.3.0',
            'last_updated': datetime.now().isoformat(),
            'auto_adapt': {
                'enabled': True,
                'scan_interval': 60,
                'auto_load_modules': True,
                'auto_update_config': True
            },
            'modules': {},
            'features': {},
            'json_sync': {
                'enabled': True,
                'sync_interval': 10,
                'watch_directories': [self.project_root],
                'auto_start': True
            },
            'loaded_adapters': [],
            'module_registry': {}
        }

        try:
            with open(self.system_config_path, 'w', encoding='utf-8') as f:
                json.dump(default_config, f, ensure_ascii=False, indent=2)
            print(f"✓ 已创建默认配置文件")
        except Exception as e:
            print(f"✗ 创建配置文件失败: {e}")

        return default_config

    def update_system_config(self, config: Dict[str, Any]):
        """更新系统配置"""
        try:
            config['last_updated'] = datetime.now().isoformat()

            # 确保auto_adapt字段存在
            if 'auto_adapt' not in config:
                config['auto_adapt'] = {}
            config['auto_adapt']['last_scan'] = datetime.now().isoformat()

            with open(self.system_config_path, 'w', encoding='utf-8') as f:
                json.dump(config, f, ensure_ascii=False, indent=2)

            print(f"✓ 系统配置已更新")
            self.config_cache = config
        except Exception as e:
            print(f"✗ 更新配置失败: {e}")

    def register_module(self, module_info: Dict[str, Any]) -> bool:
        """注册模块到系统"""
        try:
            module_name = module_info['name']
            self.module_registry[module_name] = {
                'registered_at': datetime.now().isoformat(),
                'status': 'active',
                **module_info
            }

            # 加载模块
            if module_info['type'] == 'sync_module':
                self.load_json_sync_module(module_info)
            elif module_info['type'] == 'adapter':
                self.load_adapter_module(module_info)
            elif module_info['type'] == 'module':
                self.load_python_module(module_info)

            print(f"✓ 模块已注册: {module_name}")
            return True
        except Exception as e:
            print(f"✗ 模块注册失败 {module_info['name']}: {e}")
            return False

    def load_json_sync_module(self, module_info: Dict[str, Any]):
        """加载JSON同步模块"""
        try:
            sys.path.insert(0, self.project_root)
            from json_auto_sync_system import EnhancedJSONSyncManager

            db_path = os.path.join(self.project_root, 'mtcos_json_sync.db')
            sync_manager = EnhancedJSONSyncManager(
                db_path=db_path,
                project_root=self.project_root
            )

            self.loaded_modules['json_auto_sync'] = {
                'manager': sync_manager,
                'status': 'ready'
            }

            print(f"✓ JSON同步模块已加载")
        except Exception as e:
            print(f"✗ 加载JSON同步模块失败: {e}")

    def load_adapter_module(self, module_info: Dict[str, Any]):
        """加载适配器模块"""
        try:
            module_path = module_info['path']
            module_name = module_info['name']

            spec = importlib.util.spec_from_file_location(module_name, module_path)
            if spec and spec.loader:
                module = importlib.util.module_from_spec(spec)
                sys.modules[module_name] = module
                spec.loader.exec_module(module)

                self.loaded_modules[module_name] = {
                    'module': module,
                    'status': 'ready'
                }

                print(f"✓ 适配器已加载: {module_name}")
        except Exception as e:
            print(f"✗ 加载适配器失败 {module_info['name']}: {e}")

    def load_python_module(self, module_info: Dict[str, Any]):
        """加载Python模块"""
        try:
            module_path = module_info['path']
            module_name = module_info['name']

            spec = importlib.util.spec_from_file_location(module_name, module_path)
            if spec and spec.loader:
                module = importlib.util.module_from_spec(spec)
                sys.modules[module_name] = module
                spec.loader.exec_module(module)

                self.loaded_modules[module_name] = {
                    'module': module,
                    'status': 'ready'
                }

                print(f"✓ 功能模块已加载: {module_name}")
        except Exception as e:
            print(f"✗ 加载模块失败 {module_info['name']}: {e}")

    def auto_adapt(self) -> Dict[str, Any]:
        """执行自动适配"""
        print("\n" + "=" * 60)
        print("MTSCOS 系统自动适配")
        print("=" * 60)

        # 加载系统配置
        print("\n[1/5] 加载系统配置...")
        config = self.load_system_config()

        # 检测新模块
        print("\n[2/5] 检测新模块...")
        detected_modules = self.detect_new_modules()

        # 注册模块
        print("\n[3/5] 注册模块...")
        registered_count = 0
        for module_info in detected_modules:
            if self.register_module(module_info):
                registered_count += 1

        # 更新配置
        print("\n[4/5] 更新系统配置...")
        config['modules'] = {name: info for name, info in self.module_registry.items()}
        config['loaded_adapters'] = list(self.loaded_modules.keys())
        config['module_registry'] = self.module_registry
        self.update_system_config(config)

        # 启动自动同步
        print("\n[5/5] 启动JSON同步服务...")
        if 'json_auto_sync' in self.loaded_modules:
            try:
                sync_manager = self.loaded_modules['json_auto_sync']['manager']
                sync_manager.start_file_monitoring()
                sync_manager.start_periodic_sync()
                print("✓ JSON同步服务已启动")
            except Exception as e:
                print(f"✗ 启动同步服务失败: {e}")

        print("\n" + "=" * 60)
        print("✓ 自动适配完成!")
        print(f"  - 检测模块: {len(detected_modules)}")
        print(f"  - 注册模块: {registered_count}")
        print(f"  - 加载模块: {len(self.loaded_modules)}")
        print("=" * 60)

        return {
            'detected': len(detected_modules),
            'registered': registered_count,
            'loaded': len(self.loaded_modules),
            'config': config
        }

    def get_module_status(self) -> Dict[str, Any]:
        """获取模块状态"""
        return {
            'loaded_modules': list(self.loaded_modules.keys()),
            'module_registry': self.module_registry,
            'config_cache': self.config_cache
        }

    def restart_module(self, module_name: str) -> bool:
        """重启指定模块"""
        try:
            if module_name in self.loaded_modules:
                # 停止模块
                if hasattr(self.loaded_modules[module_name]['manager'], 'stop'):
                    self.loaded_modules[module_name]['manager'].stop()

                # 重新加载
                if module_name == 'json_auto_sync':
                    self.load_json_sync_module({
                        'name': 'json_auto_sync',
                        'type': 'sync_module'
                    })

                    sync_manager = self.loaded_modules['json_auto_sync']['manager']
                    sync_manager.start_file_monitoring()
                    sync_manager.start_periodic_sync()

                print(f"✓ 模块已重启: {module_name}")
                return True
            else:
                print(f"✗ 模块不存在: {module_name}")
                return False
        except Exception as e:
            print(f"✗ 重启模块失败: {e}")
            return False

def main():
    """主函数"""
    print("=" * 60)
    print("MTSCOS 系统自动适配器")
    print("=" * 60)

    project_root = os.path.dirname(os.path.abspath(__file__))
    adapter = SystemAutoAdapter(project_root)

    result = adapter.auto_adapt()

    print("\n适配结果:")
    print(f"  检测模块: {result['detected']}")
    print(f"  注册模块: {result['registered']}")
    print(f"  加载模块: {result['loaded']}")

    return result

if __name__ == "__main__":
    main()
