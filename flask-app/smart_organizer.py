# -*- coding: utf-8 -*-
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
智能项目整理系统 V2.0
基于AI分析动态优化项目结构
"""

import os
import sys
import json
import shutil
import logging
from pathlib import Path
from collections import defaultdict
from datetime import datetime
import hashlib

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('SmartOrganizer')

class SmartProjectOrganizer:
    """智能项目整理器"""
    
    def __init__(self, base_path: str):
        self.base_path = Path(base_path)
        self.analysis = {
            'files': [],
            'categories': defaultdict(list),
            'duplicates': [],
            'orphans': [],
            'recommendations': []
        }
        self.stats = {
            'analyzed': 0,
            'organized': 0,
            'moved': 0,
            'cleaned': 0,
            'merged': 0
        }
    
    def analyze_project(self) -> dict:
        """AI分析项目结构"""
        logger.info("开始分析项目结构...")
        
        for root, dirs, files in os.walk(self.base_path):
            dirs[:] = [d for d in dirs if d not in ['__pycache__', 'node_modules', '.git', 'venv', '.venv']]
            
            for file in files:
                if file.startswith('.'):
                    continue
                
                file_path = Path(root) / file
                rel_path = file_path.relative_to(self.base_path)
                
                file_info = {
                    'path': str(rel_path),
                    'name': file,
                    'size': file_path.stat().st_size,
                    'ext': file_path.suffix,
                    'modified': datetime.fromtimestamp(file_path.stat().st_mtime),
                    'type': self._classify_file(file, rel_path)
                }
                
                self.analysis['files'].append(file_info)
                self.analysis['categories'][file_info['type']].append(file_info)
                
                self.stats['analyzed'] += 1
        
        self._find_duplicates()
        self._find_orphans()
        self._generate_recommendations()
        
        logger.info(f"分析完成: {self.stats['analyzed']} 个文件")
        return self.analysis
    
    def _classify_file(self, filename: str, path: Path) -> str:
        """AI分类文件"""
        name_lower = filename.lower()
        path_str = str(path).lower()
        
        # 核心文件
        if filename in ['main.py', 'app.py', 'config.py', '__init__.py']:
            return 'core'
        
        # AI相关
        if name_lower.startswith('ai_') or 'ai' in path_str:
            if 'engine' in path_str:
                return 'ai_engine'
            elif 'brain' in path_str:
                return 'ai_brain'
            elif 'employee' in path_str:
                return 'ai_employee'
            elif 'learning' in path_str:
                return 'ai_learning'
            elif 'system' in path_str or 'v2' in name_lower:
                return 'ai_system'
            return 'ai_misc'
        
        # V2系统
        if 'v2' in name_lower or '_v2' in name_lower:
            return 'v2_system'
        
        # API相关
        if filename.endswith('_api.py') or filename.endswith('_routes.py'):
            if 'ai' in path_str:
                return 'ai_api'
            elif 'admin' in path_str:
                return 'admin_api'
            return 'api'
        
        # 服务层
        if filename.endswith('_service.py'):
            return 'service'
        
        # 模型层
        if filename.endswith('_model.py'):
            return 'model'
        
        # 工具类
        if filename.endswith('_util.py') or filename.endswith('_helper.py'):
            return 'util'
        
        # 测试文件
        if filename.startswith('test_') or filename.endswith('_test.py'):
            return 'test'
        
        # 配置和数据
        if filename.endswith('.json') or filename.endswith('.yaml') or filename.endswith('.yml'):
            if 'config' in path_str:
                return 'config'
            elif 'data' in path_str:
                return 'data'
            return 'config'
        
        # 数据库
        if filename.endswith('.db') or filename.endswith('.sqlite'):
            return 'database'
        
        # 日志
        if filename.endswith('.log'):
            return 'log'
        
        # 备份
        if '.backup' in filename or filename.endswith('.bak'):
            return 'backup'
        
        # 文档
        if filename.endswith('.md') or filename.endswith('.txt'):
            if 'readme' in name_lower:
                return 'docs'
            elif 'changelog' in name_lower:
                return 'docs'
            return 'docs'
        
        # Docker
        if 'docker' in name_lower or 'dockerfile' in name_lower:
            return 'deploy'
        
        # 临时文件
        if filename.endswith('.tmp') or filename.endswith('.cache') or filename.endswith('.pyc'):
            return 'temp'
        
        return 'misc'
    
    def _find_duplicates(self):
        """查找重复文件"""
        seen = defaultdict(list)
        
        for file_info in self.analysis['files']:
            key = hashlib.md5(f"{file_info['name']}{file_info['size']}".encode()).hexdigest()
            seen[key].append(file_info)
        
        for key, files in seen.items():
            if len(files) > 1:
                self.analysis['duplicates'].append({
                    'files': files,
                    'size': files[0]['size']
                })
    
    def _find_orphans(self):
        """查找孤立文件"""
        # 查找没有任何关联的文件
        pass
    
    def _generate_recommendations(self):
        """AI生成整理建议"""
        recommendations = []
        
        # 建议1: 整理V2系统
        v2_count = len(self.analysis['categories']['v2_system'])
        if v2_count > 0:
            recommendations.append({
                'type': 'move',
                'target': 'v2_systems/',
                'files': [f for f in self.analysis['categories']['v2_system']],
                'reason': f'整理{v2_count}个V2系统文件'
            })
        
        # 建议2: 整理AI文件
        ai_files = (
            self.analysis['categories']['ai_engine'] +
            self.analysis['categories']['ai_brain'] +
            self.analysis['categories']['ai_employee'] +
            self.analysis['categories']['ai_learning'] +
            self.analysis['categories']['ai_system'] +
            self.analysis['categories']['ai_misc']
        )
        if ai_files:
            recommendations.append({
                'type': 'move',
                'target': 'ai_engines/',
                'files': ai_files,
                'reason': f'整理{len(ai_files)}个AI相关文件'
            })
        
        # 建议3: 清理备份
        backup_count = len(self.analysis['categories']['backup'])
        if backup_count > 5:
            recommendations.append({
                'type': 'cleanup',
                'target': 'backups/',
                'files': self.analysis['categories']['backup'],
                'reason': f'清理{backup_count}个旧备份文件'
            })
        
        # 建议4: 清理日志
        log_count = len(self.analysis['categories']['log'])
        if log_count > 10:
            recommendations.append({
                'type': 'cleanup',
                'target': 'logs/',
                'files': self.analysis['categories']['log'],
                'reason': f'整理{log_count}个日志文件'
            })
        
        # 建议5: 清理临时文件
        temp_count = len(self.analysis['categories']['temp'])
        if temp_count > 0:
            recommendations.append({
                'type': 'cleanup',
                'target': 'temp/',
                'files': self.analysis['categories']['temp'],
                'reason': f'清理{temp_count}个临时文件'
            })
        
        # 建议6: 合并重复文件
        if self.analysis['duplicates']:
            recommendations.append({
                'type': 'merge',
                'duplicates': self.analysis['duplicates'],
                'reason': f'发现{len(self.analysis["duplicates"])}组重复文件'
            })
        
        self.analysis['recommendations'] = recommendations
    
    def execute_recommendations(self, dry_run: bool = True):
        """执行整理建议"""
        logger.info("执行整理建议...")
        
        directories = ['ai_engines', 'v2_systems', 'backups', 'logs', 'temp', 'docs']
        
        for dir_name in directories:
            dir_path = self.base_path / dir_name
            if not dir_path.exists():
                dir_path.mkdir(parents=True, exist_ok=True)
                logger.info(f"创建目录: {dir_name}/")
        
        for rec in self.analysis['recommendations']:
            if rec['type'] == 'move':
                for file_info in rec['files']:
                    self._move_file(file_info, rec['target'], dry_run)
            
            elif rec['type'] == 'cleanup':
                for file_info in rec['files']:
                    self._cleanup_file(file_info, rec['target'], dry_run)
            
            elif rec['type'] == 'merge':
                self._merge_duplicates(rec['duplicates'], dry_run)
        
        if not dry_run:
            self._cleanup_pycache()
        
        return self.stats
    
    def _move_file(self, file_info: dict, target_dir: str, dry_run: bool):
        """移动文件"""
        source = self.base_path / file_info['path']
        target = self.base_path / target_dir / file_info['name']
        
        if not source.exists() or source == target:
            return
        
        if dry_run:
            logger.info(f"计划移动: {file_info['path']} -> {target_dir}/{file_info['name']}")
        else:
            try:
                shutil.move(str(source), str(target))
                logger.info(f"移动: {file_info['path']} -> {target_dir}/")
                self.stats['moved'] += 1
            except Exception as e:
                logger.error(f"移动失败: {e}")
    
    def _cleanup_file(self, file_info: dict, target_dir: str, dry_run: bool):
        """清理文件"""
        source = self.base_path / file_info['path']
        
        if dry_run:
            logger.info(f"计划清理: {file_info['path']}")
        else:
            if file_info['type'] == 'backup':
                target = self.base_path / target_dir / file_info['name']
                if not target.exists():
                    shutil.move(str(source), str(target))
                    logger.info(f"归档备份: {file_info['path']} -> {target_dir}/")
                    self.stats['moved'] += 1
            else:
                try:
                    source.unlink()
                    logger.info(f"删除: {file_info['path']}")
                    self.stats['cleaned'] += 1
                except Exception as e:
                    logger.error(f"删除失败: {e}")
    
    def _merge_duplicates(self, duplicates: list, dry_run: bool):
        """合并重复文件"""
        for group in duplicates:
            if dry_run:
                logger.info(f"计划合并: {len(group['files'])} 个重复文件")
            else:
                primary = group['files'][0]
                for dup in group['files'][1:]:
                    dup_path = self.base_path / dup['path']
                    try:
                        dup_path.unlink()
                        logger.info(f"删除重复: {dup['path']}")
                        self.stats['merged'] += 1
                    except Exception:
                        pass
    
    def _cleanup_pycache(self):
        """清理Python缓存"""
        for root, dirs, files in os.walk(self.base_path):
            for d in dirs[:]:
                if d == '__pycache__':
                    shutil.rmtree(os.path.join(root, d))
                    logger.info(f"清理: {root}/__pycache__")
                    self.stats['cleaned'] += 1
    
    def generate_report(self) -> dict:
        """生成整理报告"""
        report = {
            'timestamp': datetime.now().isoformat(),
            'base_path': str(self.base_path),
            'statistics': self.stats,
            'analysis': {
                'total_files': len(self.analysis['files']),
                'categories': {k: len(v) for k, v in self.analysis['categories'].items()},
                'duplicates': len(self.analysis['duplicates'])
            },
            'recommendations': [
                {
                    'type': r['type'],
                    'target': r.get('target', ''),
                    'file_count': len(r.get('files', [])),
                    'reason': r['reason']
                }
                for r in self.analysis['recommendations']
            ]
        }
        
        return report
    
    def run(self, dry_run: bool = True):
        """运行整理流程"""
        print("\n" + "=" * 70)
        print("智能项目整理系统 V2.0 - AI动态优化")
        print("=" * 70 + "\n")
        
        self.analyze_project()
        
        print("\n📊 项目分析结果:")
        print(f"   总文件数: {self.stats['analyzed']}")
        print("\n📁 文件分类统计:")
        for cat, files in sorted(self.analysis['categories'].items(), key=lambda x: -len(x[1])):
            print(f"   {cat:15s}: {len(files):3d} 个文件")
        
        if self.analysis['duplicates']:
            print(f"\n🔍 发现重复文件: {len(self.analysis['duplicates'])} 组")
        
        print("\n💡 AI整理建议:")
        for i, rec in enumerate(self.analysis['recommendations'], 1):
            print(f"   {i}. {rec['reason']}")
        
        print("\n" + "-" * 70 + "\n")
        
        if dry_run:
            print("🔍 预览模式 - 不执行任何操作\n")
            response = input("是否执行整理? (y/N): ").strip().lower()
        else:
            print("⚡ 执行模式 - 开始整理...\n")
            response = 'y'
        
        if response == 'y':
            self.execute_recommendations(dry_run=False)
            
            print("\n" + "=" * 70)
            print("✅ 整理完成!")
            print("=" * 70)
            print(f"\n📈 整理统计:")
            print(f"   移动文件: {self.stats['moved']}")
            print(f"   清理文件: {self.stats['cleaned']}")
            print(f"   合并重复: {self.stats['merged']}")
            
            report = self.generate_report()
            report_file = self.base_path / "smart_organize_report.json"
            with open(report_file, 'w', encoding='utf-8') as f:
                json.dump(report, f, ensure_ascii=False, indent=2)
            print(f"\n📄 报告已保存: {report_file}")
        else:
            print("\n⏭️  已取消整理")
        
        print()
        return self.stats


def main():
    """主函数"""
    base_path = "/Users/wuchenghao/Library/CloudStorage/OneDrive-个人/文档/MTSCOS_AI_Project/flask-app"
    
    organizer = SmartProjectOrganizer(base_path)
    organizer.run(dry_run=True)


if __name__ == "__main__":
    main()