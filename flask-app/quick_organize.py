# -*- coding: utf-8 -*-
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
项目结构优化脚本
直接执行目录整理，不询问
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
logger = logging.getLogger('ProjectOrganizer')

class ProjectOrganizer:
    """项目整理器"""
    
    def __init__(self, base_path: str):
        self.base_path = Path(base_path)
        self.stats = {
            'moved': 0,
            'created': 0,
            'cleaned': 0
        }
    
    def create_directories(self):
        """创建目录结构"""
        dirs = ['core', 'ai_engines', 'v2_systems', 'backups', 'logs']
        
        for d in dirs:
            path = self.base_path / d
            if not path.exists():
                path.mkdir(parents=True, exist_ok=True)
                logger.info(f"创建目录: {d}/")
                self.stats['created'] += 1
    
    def organize_v2_systems(self):
        """整理V2系统文件"""
        v2_files = [
            'thread_manager_v2.py',
            'process_manager_v2.py',
            'permission_manager_v2.py',
            'audit_system_v2.py',
            'ai_system_v2.py',
            'distributed_deployment_v2.py',
            'sandbox_system_v2.py',
            'environment_manager_v2.py',
            'theme_system_v2.py',
            'core_v2_adapter.py',
            'system_adapter.py',
            'shadow_system_v2.py'
        ]
        
        for filename in v2_files:
            source = self.base_path / filename
            if source.exists():
                target = self.base_path / 'v2_systems' / filename
                if source != target:
                    shutil.move(str(source), str(target))
                    logger.info(f"移动V2系统: {filename} -> v2_systems/")
                    self.stats['moved'] += 1
    
    def organize_ai_files(self):
        """整理AI文件"""
        ai_files = [f for f in os.listdir(self.base_path) 
                   if f.startswith('ai_') and f.endswith('.py')]
        
        for filename in ai_files:
            source = self.base_path / filename
            target = self.base_path / 'ai_engines' / filename
            if source != target:
                shutil.move(str(source), str(target))
                logger.info(f"移动AI文件: {filename} -> ai_engines/")
                self.stats['moved'] += 1
    
    def organize_backups(self):
        """整理备份文件"""
        backup_files = [f for f in os.listdir(self.base_path) 
                       if f.endswith('.backup') or '.backup_' in f]
        
        backups_dir = self.base_path / 'backups'
        if not backups_dir.exists():
            backups_dir.mkdir(parents=True, exist_ok=True)
        
        for filename in backup_files:
            source = self.base_path / filename
            target = backups_dir / filename
            shutil.move(str(source), str(target))
            logger.info(f"移动备份: {filename} -> backups/")
            self.stats['moved'] += 1
    
    def clean_temp_files(self):
        """清理临时文件"""
        for root, dirs, files in os.walk(self.base_path):
            for d in dirs[:]:
                if d == '__pycache__':
                    shutil.rmtree(os.path.join(root, d))
                    logger.info(f"清理: {root}/__pycache__")
                    self.stats['cleaned'] += 1
            
            for f in files:
                if f.endswith('.pyc') or f.endswith('.pyo'):
                    os.remove(os.path.join(root, f))
                    self.stats['cleaned'] += 1
    
    def generate_tree(self) -> str:
        """生成项目树"""
        lines = [str(self.base_path.name)]
        
        def walk(path: Path, prefix: str = "", max_depth: int = 2, depth: int = 0):
            if depth >= max_depth:
                return
            
            try:
                items = sorted(path.iterdir(), key=lambda x: (not x.is_dir(), x.name))
                for i, item in enumerate(items):
                    if item.name.startswith('.') or item.name in ['__pycache__', 'node_modules']:
                        continue
                    
                    is_last = i == len(items) - 1
                    connector = "└── " if is_last else "├── "
                    lines.append(f"{prefix}{connector}{item.name}")
                    
                    if item.is_dir():
                        ext = "    " if is_last else "│   "
                        walk(item, prefix + ext, max_depth, depth + 1)
            except PermissionError:
                pass
        
        walk(self.base_path)
        return "\n".join(lines)
    
    def organize(self):
        """执行整理"""
        logger.info("开始整理项目结构...")
        
        self.create_directories()
        self.organize_v2_systems()
        self.organize_ai_files()
        self.organize_backups()
        self.clean_temp_files()
        
        logger.info("\n整理完成!")
        logger.info(f"创建目录: {self.stats['created']}")
        logger.info(f"移动文件: {self.stats['moved']}")
        logger.info(f"清理文件: {self.stats['cleaned']}")
        
        tree = self.generate_tree()
        print("\n项目结构预览:\n")
        print(tree)
        
        return self.stats


def main():
    base_path = "/Users/wuchenghao/Library/CloudStorage/OneDrive-个人/文档/MTSCOS_AI_Project/flask-app"
    
    print("\n" + "=" * 60)
    print("项目结构优化")
    print("=" * 60 + "\n")
    
    organizer = ProjectOrganizer(base_path)
    stats = organizer.organize()
    
    print("\n" + "=" * 60)
    print("优化完成!")
    print("=" * 60)


if __name__ == "__main__":
    main()