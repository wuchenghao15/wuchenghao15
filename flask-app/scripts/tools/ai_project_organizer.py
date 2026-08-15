#!/usr/bin/env python3
"""
AI项目整理Agent - 智能整理项目目录结构
功能：自动分析项目结构，分类整理文件，保持兼容性
"""

import os
import sys
import shutil
import sqlite3
import datetime
import json
from pathlib import Path

class AIProjectOrganizer:
    def __init__(self, project_root):
        self.project_root = Path(project_root).resolve()
        self.backup_dir = self.project_root / 'organization_backup'
        self.move_log = []
        self.skipped_files = []

    def analyze_structure(self):
        """分析当前项目结构"""
        print('=' * 70)
        print('  📊 AI项目整理Agent - 结构分析')
        print('=' * 70)
        print()

        root_items = list(self.project_root.iterdir())
        dirs = [item for item in root_items if item.is_dir() and not item.name.startswith('.')]
        files = [item for item in root_items if item.is_file() and not item.name.startswith('.')]

        print(f'项目根目录: {self.project_root}')
        print(f'目录数量: {len(dirs)}')
        print(f'文件数量: {len(files)}')
        print()

        # 分类文件
        categories = {
            '数据库文件': [],
            '日志文件': [],
            '测试文件': [],
            'Python脚本': [],
            '配置文件': [],
            '音频文件': [],
            'SQL文件': [],
            '备份文件': [],
            '其他文件': []
        }

        for f in files:
            name = f.name.lower()
            if name.startswith('test_') and name.endswith('.py'):
                categories['测试文件'].append(f)
            elif name.endswith('.db') or name.endswith('.sqlite') or name.endswith('.db-shm') or name.endswith('.db-wal'):
                categories['数据库文件'].append(f)
            elif name.endswith('.log'):
                categories['日志文件'].append(f)
            elif name.endswith('.py'):
                categories['Python脚本'].append(f)
            elif name.endswith('.json') or name.endswith('.yaml') or name.endswith('.yml') or name.endswith('.env'):
                categories['配置文件'].append(f)
            elif name.endswith('.wav') or name.endswith('.mp3') or name.endswith('.m4a'):
                categories['音频文件'].append(f)
            elif name.endswith('.sql'):
                categories['SQL文件'].append(f)
            elif '.bak' in name or 'backup' in name or name.endswith('.disabled'):
                categories['备份文件'].append(f)
            else:
                categories['其他文件'].append(f)

        for cat, cat_files in categories.items():
            if cat_files:
                total_size = sum(f.stat().st_size for f in cat_files)
                size_str = f'{total_size/1024:.1f}KB' if total_size < 1024*1024 else f'{total_size/1024/1024:.1f}MB'
                print(f'  {cat}: {len(cat_files)} 个 ({size_str})')

        print()
        return categories

    def plan_organization(self):
        """制定整理计划"""
        print('=' * 70)
        print('  📋 整理计划')
        print('=' * 70)
        print()

        plan = [
            {
                'step': 1,
                'name': '创建目标目录',
                'dirs': [
                    'data/databases',
                    'logs/ai_engines',
                    'logs/system',
                    'tests/unit',
                    'scripts/upgrade',
                    'scripts/fix',
                    'scripts/tools',
                    'config',
                    'data/audio',
                    'data/sql',
                    'archive/backup_files',
                ]
            },
            {
                'step': 2,
                'name': '移动数据库文件',
                'source_pattern': '*.db',
                'target_dir': 'data/databases',
                'exclude': ['app.db']
            },
            {
                'step': 3,
                'name': '移动日志文件',
                'source_pattern': '*.log',
                'target_dir': 'logs/system'
            },
            {
                'step': 4,
                'name': '移动测试文件',
                'source_pattern': 'test_*.py',
                'target_dir': 'tests/unit'
            },
            {
                'step': 5,
                'name': '移动Python脚本',
                'files': [
                    ('upgrade_question_bank.py', 'scripts/upgrade/'),
                    ('upgrade_v6.py', 'scripts/upgrade/'),
                    ('auto_test_and_fix.py', 'scripts/fix/'),
                    ('fix_*.py', 'scripts/fix/'),
                    ('init_*.py', 'scripts/tools/'),
                ]
            },
            {
                'step': 6,
                'name': '移动配置文件',
                'source_pattern': '*.json',
                'target_dir': 'config',
                'exclude': ['package.json']
            },
            {
                'step': 7,
                'name': '移动音频文件',
                'source_pattern': '*.wav',
                'target_dir': 'data/audio'
            },
            {
                'step': 8,
                'name': '移动SQL文件',
                'source_pattern': '*.sql',
                'target_dir': 'data/sql'
            },
            {
                'step': 9,
                'name': '移动备份文件',
                'source_pattern': '*.bak',
                'target_dir': 'archive/backup_files'
            },
        ]

        for p in plan:
            print(f'  步骤{p["step"]}: {p["name"]}')

        print()
        print('  ⚠️  保留在根目录的核心文件:')
        print('    - app.py (主入口)')
        print('    - app.db (主数据库)')
        print('    - auto_scheduler.py (调度引擎)')
        print('    - ai_self_learning_engine.py (自我学习引擎)')
        print('    - brain_feeding_engine.py (脑库投喂引擎)')
        print('    - .env, .gitignore, .dockerignore')
        print('    - README.md, requirements.txt')
        print()

        return plan

    def create_directories(self, dirs):
        """创建目标目录"""
        print('[1/9] 创建目标目录...')
        for d in dirs:
            dir_path = self.project_root / d
            dir_path.mkdir(parents=True, exist_ok=True)
            print(f'  ✓ {d}/')
        print()

    def safe_move(self, src_path, target_dir):
        """安全移动文件，保留备份"""
        src = Path(src_path)
        dst_dir = Path(target_dir)

        if not src.exists():
            return False

        dst = dst_dir / src.name
        if dst.exists():
            # 目标已存在，重命名源文件
            timestamp = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
            dst = dst_dir / f'{src.stem}_{timestamp}{src.suffix}'

        try:
            shutil.move(str(src), str(dst))
            self.move_log.append({
                'source': str(src.relative_to(self.project_root)),
                'target': str(dst.relative_to(self.project_root)),
                'timestamp': datetime.datetime.now().isoformat()
            })
            return True
        except Exception as e:
            print(f'  ✗ 移动失败 {src.name}: {e}')
            self.skipped_files.append((str(src), str(e)))
            return False

    def move_by_pattern(self, pattern, target_dir, exclude=None):
        """按模式移动文件"""
        if exclude is None:
            exclude = []

        target_path = self.project_root / target_dir
        moved_count = 0

        for f in self.project_root.glob(pattern):
            if f.is_file() and f.name not in exclude:
                if self.safe_move(f, target_path):
                    moved_count += 1

        return moved_count

    def execute_organization(self):
        """执行整理"""
        print('=' * 70)
        print('  🚀 开始执行项目整理')
        print('=' * 70)
        print()

        # 1. 创建目录
        dirs_to_create = [
            'data/databases',
            'logs/ai_engines',
            'logs/system',
            'tests/unit',
            'scripts/upgrade',
            'scripts/fix',
            'scripts/tools',
            'config',
            'data/audio',
            'data/sql',
            'archive/backup_files',
            'organization_backup',
        ]
        self.create_directories(dirs_to_create)

        # 2. 移动数据库文件
        print('[2/9] 移动数据库文件...')
        count = self.move_by_pattern('*.db', 'data/databases', exclude=['app.db'])
        count += self.move_by_pattern('*.db-shm', 'data/databases')
        count += self.move_by_pattern('*.db-wal', 'data/databases')
        count += self.move_by_pattern('*.sqlite', 'data/databases')
        print(f'  ✓ 移动了 {count} 个数据库文件')
        print()

        # 3. 移动日志文件
        print('[3/9] 移动日志文件...')
        count = self.move_by_pattern('*.log', 'logs/system')
        print(f'  ✓ 移动了 {count} 个日志文件')
        print()

        # 4. 移动测试文件
        print('[4/9] 移动测试文件...')
        count = self.move_by_pattern('test_*.py', 'tests/unit')
        print(f'  ✓ 移动了 {count} 个测试文件')
        print()

        # 5. 移动升级脚本
        print('[5/9] 移动脚本文件...')
        count = 0
        for f in ['upgrade_question_bank.py', 'upgrade_v6.py']:
            src = self.project_root / f
            if src.exists():
                if self.safe_move(src, self.project_root / 'scripts/upgrade'):
                    count += 1

        for f in self.project_root.glob('fix_*.py'):
            if f.is_file():
                if self.safe_move(f, self.project_root / 'scripts/fix'):
                    count += 1

        for f in self.project_root.glob('init_*.py'):
            if f.is_file() and 'init_db' not in f.name:
                if self.safe_move(f, self.project_root / 'scripts/tools'):
                    count += 1

        auto_test_fix = self.project_root / 'auto_test_and_fix.py'
        if auto_test_fix.exists():
            if self.safe_move(auto_test_fix, self.project_root / 'scripts/fix'):
                count += 1

        print(f'  ✓ 移动了 {count} 个脚本文件')
        print()

        # 6. 移动配置文件
        print('[6/9] 移动配置文件...')
        count = 0
        for f in self.project_root.glob('*.json'):
            if f.is_file() and f.name != 'package.json':
                if self.safe_move(f, self.project_root / 'config'):
                    count += 1
        print(f'  ✓ 移动了 {count} 个配置文件')
        print()

        # 7. 移动音频文件
        print('[7/9] 移动音频文件...')
        count = 0
        for f in self.project_root.glob('*.wav'):
            if f.is_file():
                if self.safe_move(f, self.project_root / 'data/audio'):
                    count += 1
        print(f'  ✓ 移动了 {count} 个音频文件')
        print()

        # 8. 移动SQL文件
        print('[8/9] 移动SQL文件...')
        count = self.move_by_pattern('*.sql', 'data/sql')
        print(f'  ✓ 移动了 {count} 个SQL文件')
        print()

        # 9. 移动备份/禁用文件
        print('[9/9] 移动备份文件...')
        count = 0
        for f in self.project_root.iterdir():
            if f.is_file():
                name = f.name.lower()
                if '.bak' in name or 'backup' in name or name.endswith('.disabled'):
                    if self.safe_move(f, self.project_root / 'archive/backup_files'):
                        count += 1
        print(f'  ✓ 移动了 {count} 个备份文件')
        print()

        # 保存移动日志
        self.save_move_log()

        # 输出总结
        self.print_summary()

    def save_move_log(self):
        """保存移动日志"""
        log_file = self.project_root / 'organization_backup' / 'move_log.json'
        with open(log_file, 'w', encoding='utf-8') as f:
            json.dump({
                'organized_at': datetime.datetime.now().isoformat(),
                'total_moved': len(self.move_log),
                'moved_files': self.move_log,
                'skipped_files': self.skipped_files
            }, f, ensure_ascii=False, indent=2)

    def print_summary(self):
        """打印整理总结"""
        print('=' * 70)
        print('  📊 整理完成总结')
        print('=' * 70)
        print()

        # 统计根目录文件
        root_files = [f for f in self.project_root.iterdir() if f.is_file() and not f.name.startswith('.')]
        root_dirs = [d for d in self.project_root.iterdir() if d.is_dir() and not d.name.startswith('.')]

        print(f'  移动文件总数: {len(self.move_log)} 个')
        print(f'  根目录剩余文件: {len(root_files)} 个')
        print(f'  根目录剩余目录: {len(root_dirs)} 个')
        print()

        print('  根目录文件列表:')
        for f in sorted(root_files, key=lambda x: x.name.lower()):
            size = f.stat().st_size
            size_str = f'{size/1024:.1f}KB' if size < 1024*1024 else f'{size/1024/1024:.1f}MB'
            print(f'    📄 {f.name} ({size_str})')

        print()
        print('  根目录列表:')
        for d in sorted(root_dirs, key=lambda x: x.name.lower()):
            try:
                count = len(list(d.iterdir()))
            except Exception:
                count = '?'
            print(f'    📁 {d.name}/ ({count} 项)')

        print()
        print('  移动日志已保存: organization_backup/move_log.json')
        print()
        print('=' * 70)

def main():
    if len(sys.argv) > 1 and sys.argv[1] == 'analyze':
        organizer = AIProjectOrganizer('.')
        organizer.analyze_structure()
        organizer.plan_organization()
    elif len(sys.argv) > 1 and sys.argv[1] == 'execute':
        organizer = AIProjectOrganizer('.')
        organizer.analyze_structure()
        organizer.execute_organization()
    else:
        print('用法:')
        print('  python ai_project_organizer.py analyze   # 分析结构，制定计划')
        print('  python ai_project_organizer.py execute   # 执行整理')
        print()
        print('⚠️  建议先运行 analyze 查看计划，确认后再执行 execute')

if __name__ == '__main__':
    main()
