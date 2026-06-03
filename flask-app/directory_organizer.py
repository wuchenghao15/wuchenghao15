# -*- coding: utf-8 -*-
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
项目目录整理工具 V2.0
整理和优化项目文件结构
"""

import os
import shutil
import json
import logging
from pathlib import Path
from collections import defaultdict
from datetime import datetime
import sys

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('DirectoryOrganizer')

class DirectoryOrganizer:
    """目录整理器"""
    
    def __init__(self, base_path: str):
        """初始化目录整理器"""
        self.base_path = Path(base_path)
        self.file_mappings = defaultdict(list)
        self.actions = []
        self.stats = {
            'moved': 0,
            'created': 0,
            'skipped': 0,
            'cleaned': 0
        }
        
        self._define_structure()
    
    def _define_structure(self):
        """定义目标目录结构"""
        self.target_structure = {
            'core/': [
                'ai_*.py',
                'system*.py',
                'engine*.py',
                '*_manager.py',
                '*_system.py'
            ],
            'ai_engines/': [
                'teacher*.py',
                'researcher*.py',
                'expert*.py',
                'student*.py',
                'engineer*.py',
                'artist*.py',
                'arduino*.py',
                'maintenance*.py',
                'butler*.py'
            ],
            'api/': [
                '*_api.py',
                '*_routes.py'
            ],
            'services/': [
                '*_service.py',
                '*_manager.py'
            ],
            'utils/': [
                '*_util.py',
                '*_helper.py',
                '*_tool.py',
                '*_utils.py'
            ],
            'models/': [
                'models/*.py'
            ],
            'data/': [
                '*.db',
                '*.json',
                '*.csv',
                'backups/*.db'
            ],
            'logs/': [
                '*.log',
                '*.log.*'
            ],
            'temp/': [
                '*.tmp',
                '*.cache',
                '__pycache__/',
                '*.pyc'
            ],
            'v2_systems/': [
                '*_v2.py',
                '*_manager_v2.py',
                '*_system_v2.py'
            ]
        }
        
        self.keep_in_root = [
            'main.py',
            'app.py',
            'config.py',
            'requirements.txt',
            'Dockerfile',
            '.env*',
            '__init__.py',
            'setup.py'
        ]
    
    def scan_files(self):
        """扫描所有文件"""
        logger.info(f"正在扫描目录: {self.base_path}")
        
        all_files = []
        for root, dirs, files in os.walk(self.base_path):
            dirs[:] = [d for d in dirs if not d.startswith('.') and d not in ['node_modules', 'venv', '__pycache__']]
            
            for file in files:
                if file.startswith('.'):
                    continue
                
                file_path = Path(root) / file
                rel_path = file_path.relative_to(self.base_path)
                
                all_files.append({
                    'path': file_path,
                    'name': file,
                    'relative': rel_path,
                    'size': file_path.stat().st_size if file_path.exists() else 0,
                    'ext': file_path.suffix,
                    'modified': datetime.fromtimestamp(file_path.stat().st_mtime)
                })
        
        logger.info(f"扫描完成: 发现 {len(all_files)} 个文件")
        return all_files
    
    def categorize_files(self, files: list) -> dict:
        """分类文件"""
        categories = defaultdict(list)
        
        v2_keywords = ['_v2', '_manager_v2', '_system_v2', 'thread_manager', 'process_manager', 
                      'permission_manager', 'audit_system', 'ai_system', 'distributed_deployment',
                      'sandbox_system', 'environment_manager', 'theme_system']
        
        for file_info in files:
            filename = file_info['name']
            path_str = str(file_info['relative'])
            
            if any(filename in path_str and kw in path_str for kw in v2_keywords):
                categories['v2_systems'].append(file_info)
            elif filename.startswith('ai_'):
                categories['ai_engines'].append(file_info)
            elif filename.endswith('_api.py') or filename.endswith('_routes.py'):
                categories['api'].append(file_info)
            elif filename.endswith('_service.py') or filename.endswith('_manager.py'):
                categories['services'].append(file_info)
            elif filename.endswith('_util.py') or filename.endswith('_helper.py') or filename.endswith('_tool.py'):
                categories['utils'].append(file_info)
            elif filename.endswith('_model.py'):
                categories['models'].append(file_info)
            elif filename.endswith('.log'):
                categories['logs'].append(file_info)
            elif filename.endswith('.db') or filename.endswith('.json'):
                categories['data'].append(file_info)
            else:
                categories['root'].append(file_info)
        
        return categories
    
    def create_directories(self):
        """创建必要的目录"""
        directories = [
            'core',
            'ai_engines',
            'api',
            'services',
            'utils',
            'models',
            'data',
            'logs',
            'temp',
            'v2_systems',
            'backups'
        ]
        
        for dir_name in directories:
            dir_path = self.base_path / dir_name
            if not dir_path.exists():
                dir_path.mkdir(parents=True, exist_ok=True)
                logger.info(f"创建目录: {dir_name}/")
                self.stats['created'] += 1
    
    def move_file(self, file_info: dict, target_dir: str):
        """移动文件到目标目录"""
        source = file_info['path']
        target = self.base_path / target_dir / file_info['name']
        
        if source == target:
            return False
        
        if target.exists():
            logger.warning(f"文件已存在: {target}, 跳过")
            self.stats['skipped'] += 1
            return False
        
        try:
            shutil.move(str(source), str(target))
            logger.info(f"移动: {source} -> {target_dir}/")
            self.stats['moved'] += 1
            
            self.actions.append({
                'type': 'move',
                'source': str(source.relative_to(self.base_path)),
                'target': f"{target_dir}/{file_info['name']}"
            })
            
            return True
        except Exception as e:
            logger.error(f"移动失败 {source}: {str(e)}")
            return False
    
    def clean_temp_files(self):
        """清理临时文件"""
        temp_patterns = ['*.pyc', '__pycache__', '*.tmp', '*.cache', '*.pyo']
        
        cleaned = 0
        for root, dirs, files in os.walk(self.base_path):
            dirs[:] = [d for d in dirs if d not in ['__pycache__', 'node_modules', 'venv']]
            
            for file in files:
                if file.endswith('.pyc') or file.endswith('.pyo') or file.endswith('.tmp'):
                    file_path = Path(root) / file
                    try:
                        file_path.unlink()
                        logger.debug(f"删除: {file_path}")
                        cleaned += 1
                    except Exception:
                        pass
        
        self.stats['cleaned'] += cleaned
        logger.info(f"清理临时文件: {cleaned} 个")
    
    def generate_tree(self, max_depth: int = 3) -> str:
        """生成项目树"""
        tree_lines = []
        
        def add_tree(path: Path, prefix: str = "", depth: int = 0):
            if depth >= max_depth:
                return
            
            try:
                items = sorted(path.iterdir(), key=lambda x: (not x.is_dir(), x.name))
                
                for i, item in enumerate(items):
                    is_last = i == len(items) - 1
                    current_prefix = "└── " if is_last else "├── "
                    tree_lines.append(f"{prefix}{current_prefix}{item.name}")
                    
                    if item.is_dir() and item.name not in ['node_modules', '__pycache__', '.git', 'venv']:
                        extension = "    " if is_last else "│   "
                        add_tree(item, prefix + extension, depth + 1)
            except PermissionError:
                pass
        
        tree_lines.append(str(self.base_path.name))
        add_tree(self.base_path)
        
        return "\n".join(tree_lines)
    
    def generate_report(self, categories: dict) -> dict:
        """生成整理报告"""
        report = {
            'timestamp': datetime.now().isoformat(),
            'base_path': str(self.base_path),
            'statistics': self.stats,
            'actions': self.actions,
            'categories': {
                cat: len(files) for cat, files in categories.items()
            },
            'tree': self.generate_tree()
        }
        
        return report
    
    def organize(self, dry_run: bool = True):
        """执行整理"""
        logger.info("开始整理项目目录...")
        
        self.create_directories()
        
        files = self.scan_files()
        categories = self.categorize_files(files)
        
        if dry_run:
            logger.info("\n == 预览整理计划 ===")
        
        for category, file_list in categories.items():
            if category == 'root':
                continue
            
            target_dir = category
            
            for file_info in file_list:
                source_path = str(file_info['relative'])
                
                if source_path.startswith(f"{target_dir}/"):
                    continue
                
                if dry_run:
                    logger.info(f"计划移动: {source_path} -> {target_dir}/")
                else:
                    self.move_file(file_info, target_dir)
        
        if not dry_run:
            self.clean_temp_files()
        
        report = self.generate_report(categories)
        
        logger.info("\n == 整理完成 ===")
        logger.info(f"移动文件: {self.stats['moved']}")
        logger.info(f"创建目录: {self.stats['created']}")
        logger.info(f"跳过文件: {self.stats['skipped']}")
        logger.info(f"清理临时: {self.stats['cleaned']}")
        
        return report


def main():
    """主函数"""
    base_path = "/Users/wuchenghao/Library/CloudStorage/OneDrive-个人/文档/MTSCOS_AI_Project/flask-app"
    
    print("\n" + "=" * 60)
    print("项目目录整理工具 V2.0")
    print("=" * 60)
    print(f"\n目标目录: {base_path}")
    print("\n功能:")
    print("  1. 创建规范化目录结构")
    print("  2. 按类型分类文件")
    print("  3. 移动文件到正确位置")
    print("  4. 清理临时文件")
    print("  5. 生成项目树和报告")
    print("\n" + "-" * 60 + "\n")
    
    organizer = DirectoryOrganizer(base_path)
    
    print("预览整理计划...")
    report = organizer.organize(dry_run=True)
    
    print("\n" + "=" * 60)
    print("分类统计:")
    for category, count in report['categories'].items():
        print(f"  {category}: {count} 个文件")
    print("=" * 60 + "\n")
    
    response = input("是否执行整理? (y/N): ").strip().lower()
    
    if response == 'y':
        print("\n执行整理...\n")
        report = organizer.organize(dry_run=False)
        
        print("\n" + "=" * 60)
        print("整理报告已生成")
        print("=" * 60)
        
        report_file = Path(base_path) / "directory_organize_report.json"
        with open(report_file, 'w', encoding='utf-8') as f:
            json.dump(report, f, ensure_ascii=False, indent=2)
        
        print(f"报告已保存: {report_file}")
    else:
        print("\n取消整理")


if __name__ == "__main__":
    main()