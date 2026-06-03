# -*- coding: utf-8 -*-
#!/usr/bin/env python3
"""
Arduino 官方API适配器服务
提供对Arduino CLI,Arduino Cloud,Arduino Create等官方服务的集成支持
"""

import os
import sys
import json
import uuid
import subprocess
import requests
import logging
import tempfile
from datetime import datetime
from typing import Dict, List, Optional, Any

# 设置日志
LOG_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'logs')
os.makedirs(LOG_DIR, exist_ok=True)
LOG_FILE = os.path.join(LOG_DIR, f'arduino_api_{datetime.now().strftime("%Y-%m-%d")}.log')

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(LOG_FILE, encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger('ArduinoAPIAdapter')

class ArduinoCLIAdapter:
    """Arduino CLI 命令行工具适配器"""
    
    def __init__(self, cli_path: str = 'arduino-cli'):
        self.cli_path = cli_path
        self.has_cli = self._check_cli()
    
    def _check_cli(self) -> bool:
        """检查 Arduino CLI 是否安装"""
        try:
            result = subprocess.run([self.cli_path, '--version'], 
                                  capture_output=True, text=True, timeout=30)
            return result.returncode == 0
        except (FileNotFoundError, subprocess.TimeoutExpired):
            return False
    
    def get_version(self) -> Dict[str, Any]:
        """获取 CLI 版本信息"""
        if not self.has_cli:
            return {'success': False, 'message': 'Arduino CLI 未安装'}
        
        try:
            result = subprocess.run([self.cli_path, '--version'], 
                                  capture_output=True, text=True, timeout=30)
            if result.returncode == 0:
                return {
                    'success': True,
                    'version': result.stdout.strip(),
                    'cli_path': self.cli_path
                }
            return {'success': False, 'error': result.stderr}
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def list_boards(self) -> Dict[str, Any]:
        """列出所有支持的开发板"""
        if not self.has_cli:
            return {'success': False, 'message': 'Arduino CLI 未安装'}
        
        try:
            result = subprocess.run([self.cli_path, 'board', 'listall'], 
                                  capture_output=True, text=True, timeout=60)
            if result.returncode == 0:
                boards = []
                lines = result.stdout.strip().split('\n')
                for line in lines[1:]:
                    if line.strip():
                        parts = line.split('\t')
                        if len(parts) >= 2:
                            boards.append({
                                'name': parts[0].strip(),
                                'fqbn': parts[1].strip()
                            })
                return {'success': True, 'boards': boards}
            return {'success': False, 'error': result.stderr}
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def compile_sketch(self, code: str, fqbn: str = 'arduino:avr:uno') -> Dict[str, Any]:
        """编译 Arduino 代码"""
        if not self.has_cli:
            return {'success': False, 'message': 'Arduino CLI 未安装'}
        
        try:
            with tempfile.TemporaryDirectory() as tmpdir:
                sketch_name = f'sketch_{uuid.uuid4()[:8]}'
                sketch_dir = os.path.join(tmpdir, sketch_name)
                os.makedirs(sketch_dir, exist_ok=True)
                
                ino_file = os.path.join(sketch_dir, f'{sketch_name}.ino')
                with open(ino_file, 'w', encoding='utf-8') as f:
                    f.write(code)
                
                cmd = [self.cli_path, 'compile', '--fqbn', fqbn, sketch_dir]
                result = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
                
                if result.returncode == 0:
                    return {
                        'success': True,
                        'message': '编译成功',
                        'fqbn': fqbn,
                        'output': result.stdout
                    }
                else:
                    return {
                        'success': False,
                        'message': '编译失败',
                        'fqbn': fqbn,
                        'error': result.stderr
                    }
        except subprocess.TimeoutExpired:
            return {'success': False, 'message': '编译超时'}
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def upload_sketch(self, code: str, fqbn: str, port: str) -> Dict[str, Any]:
        """上传代码到开发板"""
        compile_result = self.compile_sketch(code, fqbn)
        if not compile_result['success']:
            return compile_result
        
        if not self.has_cli:
            return {'success': False, 'message': 'Arduino CLI 未安装'}
        
        try:
            with tempfile.TemporaryDirectory() as tmpdir:
                sketch_name = f'sketch_{uuid.uuid4()[:8]}'
                sketch_dir = os.path.join(tmpdir, sketch_name)
                os.makedirs(sketch_dir, exist_ok=True)
                
                ino_file = os.path.join(sketch_dir, f'{sketch_name}.ino')
                with open(ino_file, 'w', encoding='utf-8') as f:
                    f.write(code)
                
                cmd = [self.cli_path, 'upload', '--fqbn', fqbn, '--port', port, sketch_dir]
                result = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
                
                if result.returncode == 0:
                    return {
                        'success': True,
                        'message': '上传成功',
                        'fqbn': fqbn,
                        'port': port,
                        'output': result.stdout
                    }
                else:
                    return {
                        'success': False,
                        'message': '上传失败',
                        'error': result.stderr
                    }
        except subprocess.TimeoutExpired:
            return {'success': False, 'message': '上传超时'}
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def list_installed_cores(self) -> Dict[str, Any]:
        """列出已安装的核心"""
        if not self.has_cli:
            return {'success': False, 'message': 'Arduino CLI 未安装'}
        
        try:
            result = subprocess.run([self.cli_path, 'core', 'list'], 
                                  capture_output=True, text=True, timeout=30)
            if result.returncode == 0:
                cores = []
                lines = result.stdout.strip().split('\n')
                for line in lines[1:]:
                    if line.strip():
                        parts = line.split('\t')
                        if len(parts) >= 3:
                            cores.append({
                                'platform': parts[0].strip(),
                                'version': parts[1].strip(),
                                'installed': parts[2].strip()
                            })
                return {'success': True, 'cores': cores}
            return {'success': False, 'error': result.stderr}
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def list_libraries(self) -> Dict[str, Any]:
        """列出已安装的库"""
        if not self.has_cli:
            return {'success': False, 'message': 'Arduino CLI 未安装'}
        
        try:
            result = subprocess.run([self.cli_path, 'lib', 'list'], 
                                  capture_output=True, text=True, timeout=30)
            if result.returncode == 0:
                libraries = []
                lines = result.stdout.strip().split('\n')
                for line in lines[1:]:
                    if line.strip():
                        parts = line.split('\t')
                        if len(parts) >= 3:
                            libraries.append({
                                'name': parts[0].strip(),
                                'version': parts[1].strip(),
                                'location': parts[2].strip()
                            })
                return {'success': True, 'libraries': libraries}
            return {'success': False, 'error': result.stderr}
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def install_library(self, library_name: str) -> Dict[str, Any]:
        """安装库"""
        if not self.has_cli:
            return {'success': False, 'message': 'Arduino CLI 未安装'}
        
        try:
            cmd = [self.cli_path, 'lib', 'install', library_name]
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
            
            if result.returncode == 0:
                return {'success': True, 'message': f'库 {library_name} 安装成功'}
            return {'success': False, 'error': result.stderr}
        except subprocess.TimeoutExpired:
            return {'success': False, 'message': '安装超时'}
        except Exception as e:
            return {'success': False, 'error': str(e)}

class ArduinoCloudAdapter:
    """Arduino Cloud API 适配器"""
    
    BASE_URL = "https://api2.arduino.cc/iot"
    
    def __init__(self, client_id: str = None, client_secret: str = None):
        self.client_id = client_id
        self.client_secret = client_secret
        self.access_token = None
        self.token_expires_at = 0
    
    def _get_access_token(self) -> bool:
        """获取访问令牌"""
        if self.access_token and datetime.now().timestamp() < self.token_expires_at:
            return True
        
        if not self.client_id or not self.client_secret:
            return False
        
        try:
            response = requests.post(
                "https://api2.arduino.cc/iot/v1/clients/token",
                data={
                    'grant_type': 'client_credentials',
                    'client_id': self.client_id,
                    'client_secret': self.client_secret,
                    'audience': 'https://api2.arduino.cc/iot'
                },
                timeout=30
            )
            
            if response.status_code == 200:
                data = response.json()
                self.access_token = data.get('access_token')
                self.token_expires_at = datetime.now().timestamp() + data.get('expires_in', 3600)
                return True
            return False
        except Exception as e:
            logger.error(f"获取访问令牌失败: {e}")
            return False
    
    def get_things(self) -> Dict[str, Any]:
        """获取设备列表"""
        if not self._get_access_token():
            return {'success': False, 'message': '无法获取访问令牌'}
        
        try:
            headers = {'Authorization': f'Bearer {self.access_token}'}
            response = requests.get(
                f"{self.BASE_URL}/v2/things",
                headers=headers,
                timeout=30
            )
            
            if response.status_code == 200:
                return {'success': True, 'things': response.json()}
            return {'success': False, 'error': response.text}
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def get_thing(self, thing_id: str) -> Dict[str, Any]:
        """获取单个设备信息"""
        if not self._get_access_token():
            return {'success': False, 'message': '无法获取访问令牌'}
        
        try:
            headers = {'Authorization': f'Bearer {self.access_token}'}
            response = requests.get(
                f"{self.BASE_URL}/v2/things/{thing_id}",
                headers=headers,
                timeout=30
            )
            
            if response.status_code == 200:
                return {'success': True, 'thing': response.json()}
            return {'success': False, 'error': response.text}
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def get_properties(self, thing_id: str) -> Dict[str, Any]:
        """获取设备属性"""
        if not self._get_access_token():
            return {'success': False, 'message': '无法获取访问令牌'}
        
        try:
            headers = {'Authorization': f'Bearer {self.access_token}'}
            response = requests.get(
                f"{self.BASE_URL}/v2/things/{thing_id}/properties",
                headers=headers,
                timeout=30
            )
            
            if response.status_code == 200:
                return {'success': True, 'properties': response.json()}
            return {'success': False, 'error': response.text}
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def update_property(self, thing_id: str, property_id: str, value: Any) -> Dict[str, Any]:
        """更新设备属性值"""
        if not self._get_access_token():
            return {'success': False, 'message': '无法获取访问令牌'}
        
        try:
            headers = {
                'Authorization': f'Bearer {self.access_token}',
                'Content-Type': 'application/json'
            }
            response = requests.put(
                f"{self.BASE_URL}/v2/things/{thing_id}/properties/{property_id}/publish",
                headers=headers,
                json={'value': value},
                timeout=30
            )
            
            if response.status_code == 200:
                return {'success': True, 'message': '属性更新成功'}
            return {'success': False, 'error': response.text}
        except Exception as e:
            return {'success': False, 'error': str(e)}

class ArduinoLibraryManager:
    """Arduino 库管理器"""
    
    LIBRARY_INDEX_URL = "https://downloads.arduino.cc/libraries/library_index.json"
    
    def __init__(self):
        self.library_index = None
        self.last_update = 0
    
    def _update_index(self) -> bool:
        """更新库索引"""
        if datetime.now().timestamp() - self.last_update < 3600:
            return True
        
        try:
            response = requests.get(self.LIBRARY_INDEX_URL, timeout=30)
            if response.status_code == 200:
                self.library_index = response.json()
                self.last_update = datetime.now().timestamp()
                return True
            return False
        except Exception as e:
            logger.error(f"更新库索引失败: {e}")
            return False
    
    def search_libraries(self, query: str) -> Dict[str, Any]:
        """搜索库"""
        if not self._update_index():
            return {'success': False, 'message': '无法更新库索引'}
        
        try:
            results = []
            for lib in self.library_index.get('libraries', []):
                name = lib.get('name', '').lower()
                author = lib.get('author', '').lower()
                sentence = lib.get('sentence', '').lower()
                
                if query.lower() in name or query.lower() in author or query.lower() in sentence:
                    results.append({
                        'name': lib.get('name'),
                        'version': lib.get('version'),
                        'author': lib.get('author'),
                        'sentence': lib.get('sentence'),
                        'paragraph': lib.get('paragraph'),
                        'category': lib.get('category'),
                        'url': lib.get('url')
                    })
            
            return {'success': True, 'results': results[:50]}
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def get_library_details(self, library_name: str) -> Dict[str, Any]:
        """获取库详情"""
        if not self._update_index():
            return {'success': False, 'message': '无法更新库索引'}
        
        try:
            for lib in self.library_index.get('libraries', []):
                if lib.get('name') == library_name:
                    return {'success': True, 'library': lib}
            
            return {'success': False, 'message': '库未找到'}
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def list_categories(self) -> Dict[str, Any]:
        """列出所有分类"""
        if not self._update_index():
            return {'success': False, 'message': '无法更新库索引'}
        
        try:
            categories = set()
            for lib in self.library_index.get('libraries', []):
                category = lib.get('category')
                if category:
                    categories.add(category)
            
            return {'success': True, 'categories': sorted(list(categories))}
        except Exception as e:
            return {'success': False, 'error': str(e)}

class ArduinoAPIAdapter:
    """Arduino API 综合适配器"""
    
    def __init__(self):
        self.cli = ArduinoCLIAdapter()
        self.cloud = ArduinoCloudAdapter()
        self.library_manager = ArduinoLibraryManager()
    
    def get_system_info(self) -> Dict[str, Any]:
        """获取系统信息"""
        cli_version = self.cli.get_version()
        
        return {
            'cli_available': self.cli.has_cli,
            'cli_version': cli_version.get('version'),
            'cloud_available': True,
            'library_index_available': True
        }
    
    def compile_and_upload(self, code: str, board: str, port: str) -> Dict[str, Any]:
        """编译并上传代码"""
        fqbn_map = {
            'uno': 'arduino:avr:uno',
            'nano': 'arduino:avr:nano',
            'mega': 'arduino:avr:mega',
            'esp8266': 'esp8266:esp8266:nodemcuv2',
            'esp32': 'esp32:esp32:esp32'
        }
        
        fqbn = fqbn_map.get(board, 'arduino:avr:uno')
        
        compile_result = self.cli.compile_sketch(code, fqbn)
        if not compile_result['success']:
            return compile_result
        
        if port:
            return self.cli.upload_sketch(code, fqbn, port)
        
        return compile_result

if __name__ == '__main__':
    adapter = ArduinoAPIAdapter()
    
    print("=== Arduino API 适配器测试 ===\n")
    
    print("1. 获取系统信息:")
    sys_info = adapter.get_system_info()
    print(f"   CLI可用: {sys_info['cli_available']}")
    print(f"   CLI版本: {sys_info.get('cli_version', 'N/A')}")
    
    print("\n2. 列出支持的开发板:")
    boards = adapter.cli.list_boards()
    if boards['success']:
        print(f"   支持 {len(boards['boards'])} 种开发板")
        for board in boards['boards'][:5]:
            print(f"   - {board['name']}: {board['fqbn']}")
    else:
        print(f"   错误: {boards.get('error', '未知错误')}")
    
    print("\n3. 列出已安装的核心:")
    cores = adapter.cli.list_installed_cores()
    if cores['success']:
        print(f"   已安装 {len(cores['cores'])} 个核心")
        for core in cores['cores'][:3]:
            print(f"   - {core['platform']}: {core['version']}")
    else:
        print(f"   错误: {cores.get('error', '未知错误')}")
    
    print("\n4. 搜索库:")
    libs = adapter.library_manager.search_libraries('DHT')
    if libs['success']:
        print(f"   找到 {len(libs['results'])} 个匹配的库")
        for lib in libs['results'][:3]:
            print(f"   - {lib['name']} ({lib['version']})")
    else:
        print(f"   错误: {libs.get('error', '未知错误')}")
    
    print("\n5. 获取库分类:")
    categories = adapter.library_manager.list_categories()
    if categories['success']:
        print(f"   共有 {len(categories['categories'])} 个分类")
        print(f"   分类: {', '.join(categories['categories'][:5])}...")
    else:
        print(f"   错误: {categories.get('error', '未知错误')}")
    
    print("\n == 测试完成 ===")
