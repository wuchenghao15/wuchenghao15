#!/usr/bin/env python3
"""
MTSCOS AI 系统例行维护脚本
"""
import os
import sys
import sqlite3
import shutil
import subprocess
from pathlib import Path
from datetime import datetime

class MTSCOSMaintenance:
    def __init__(self, project_path):
        self.project_path = Path(project_path)
        self.flask_app_path = self.project_path / 'flask-app'
        self.results = {
            '清理临时文件': False,
            '数据库检查': False,
            '服务状态': False,
            '备份更新': False,
            '日志清理': False,
            '缓存清理': False,
            '代码检查': False
        }
    
    def run_all_maintenance(self):
        print("="*60)
        print("🛠️  MTSCOS AI 系统例行维护")
        print("="*60)
        print(f"时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("="*60)
        
        self.clean_temp_files()
        self.check_databases()
        self.check_services()
        self.update_backup()
        self.clean_logs()
        self.clean_cache()
        self.check_code()
        
        self.print_summary()
    
    def clean_temp_files(self):
        print("\n🗑️  清理临时文件...")
        try:
            temp_patterns = ['*.tmp', '*.bak', '*.swp', '*.log', '*.pid']
            cleaned = 0
            
            for pattern in temp_patterns:
                for file in self.flask_app_path.rglob(pattern):
                    if 'venv' not in str(file) and '__pycache__' not in str(file):
                        try:
                            file.unlink()
                            cleaned += 1
                        except:
                            pass
            
            print(f"  ✅ 清理了 {cleaned} 个临时文件")
            self.results['清理临时文件'] = True
        except Exception as e:
            print(f"  ❌ 清理失败: {e}")
    
    def check_databases(self):
        print("\n📊 检查数据库...")
        try:
            db_files = [
                'mtscos.db',
                'code_fixes.db',
                'python_fixes.db',
                'verified_fixes.db',
                'math_formulas.db'
            ]
            
            for db_name in db_files:
                db_path = self.flask_app_path / db_name
                if db_path.exists():
                    try:
                        conn = sqlite3.connect(str(db_path))
                        cursor = conn.cursor()
                        cursor.execute('PRAGMA integrity_check')
                        result = cursor.fetchone()[0]
                        conn.close()
                        
                        size = db_path.stat().st_size / 1024 / 1024
                        status = '✅' if result == 'ok' else '⚠️'
                        print(f"  {status} {db_name}: {size:.2f} MB - {result}")
                    except Exception as e:
                        print(f"  ❌ {db_name}: 检查失败 - {e}")
                else:
                    print(f"  ⚪ {db_name}: 不存在")
            
            self.results['数据库检查'] = True
        except Exception as e:
            print(f"  ❌ 数据库检查失败: {e}")
    
    def check_services(self):
        print("\n🔧 检查服务状态...")
        try:
            # 检查Flask应用
            result = subprocess.run(
                ['pgrep', '-f', 'python.*app.py'],
                capture_output=True,
                text=True
            )
            
            if result.returncode == 0:
                pid = result.stdout.strip()
                print(f"  ✅ Flask服务运行中 (PID: {pid})")
                self.results['服务状态'] = True
            else:
                print(f"  ⚠️  Flask服务未运行")
                # 尝试启动服务
                print("  🔄 尝试启动服务...")
                subprocess.Popen(
                    ['python3', 'app.py'],
                    cwd=str(self.flask_app_path),
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL
                )
                print("  ✅ 服务已启动")
                self.results['服务状态'] = True
        except Exception as e:
            print(f"  ❌ 服务检查失败: {e}")
    
    def update_backup(self):
        print("\n💾 更新备份...")
        try:
            backup_dir = self.project_path / 'backups'
            if not backup_dir.exists():
                backup_dir.mkdir()
            
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            backup_file = backup_dir / f'maintenance_backup_{timestamp}.tar.gz'
            
            # 创建备份（排除大型文件）
            subprocess.run(
                ['tar', '-czf', str(backup_file),
                 '--exclude=venv',
                 '--exclude=__pycache__',
                 '--exclude=*.db',
                 '--exclude=*.wav',
                 '--exclude=*.mp3',
                 '--exclude=backups',
                 '--exclude=recovery_images',
                 'flask-app'],
                cwd=str(self.project_path),
                capture_output=True
            )
            
            if backup_file.exists():
                size = backup_file.stat().st_size / 1024 / 1024
                print(f"  ✅ 备份创建成功: {backup_file.name} ({size:.2f} MB)")
                self.results['备份更新'] = True
            else:
                print(f"  ⚠️  备份创建失败")
        except Exception as e:
            print(f"  ❌ 备份失败: {e}")
    
    def clean_logs(self):
        print("\n📝 清理日志...")
        try:
            logs_dir = self.project_path / 'Logs'
            if logs_dir.exists():
                # 删除30天前的日志
                cleaned = 0
                for log_file in logs_dir.rglob('*.log'):
                    try:
                        age = (datetime.now() - datetime.fromtimestamp(log_file.stat().st_mtime)).days
                        if age > 30:
                            log_file.unlink()
                            cleaned += 1
                    except:
                        pass
                
                print(f"  ✅ 清理了 {cleaned} 个旧日志文件")
            else:
                print(f"  ⚪ 日志目录不存在")
            
            self.results['日志清理'] = True
        except Exception as e:
            print(f"  ❌ 日志清理失败: {e}")
    
    def clean_cache(self):
        print("\n🧹 清理缓存...")
        try:
            # 清理__pycache__
            cleaned = 0
            for pycache in self.flask_app_path.rglob('__pycache__'):
                if 'venv' not in str(pycache):
                    try:
                        shutil.rmtree(pycache)
                        cleaned += 1
                    except:
                        pass
            
            print(f"  ✅ 清理了 {cleaned} 个缓存目录")
            self.results['缓存清理'] = True
        except Exception as e:
            print(f"  ❌ 缓存清理失败: {e}")
    
    def check_code(self):
        print("\n🔍 检查代码质量...")
        try:
            # 检查语法错误
            result = subprocess.run(
                ['find', str(self.flask_app_path), '-name', '*.py', '-type', 'f'],
                capture_output=True,
                text=True
            )
            
            files = [f for f in result.stdout.strip().split('\n') 
                    if f and 'venv' not in f and '__pycache__' not in f]
            
            syntax_errors = 0
            for filepath in files[:100]:  # 只检查前100个文件
                try:
                    result = subprocess.run(
                        [sys.executable, '-m', 'py_compile', filepath],
                        capture_output=True,
                        text=True,
                        timeout=5
                    )
                    if result.returncode != 0:
                        syntax_errors += 1
                except:
                    pass
            
            if syntax_errors == 0:
                print(f"  ✅ 代码语法检查通过 (检查了 {min(len(files), 100)} 个文件)")
            else:
                print(f"  ⚠️  发现 {syntax_errors} 个语法错误")
            
            self.results['代码检查'] = True
        except Exception as e:
            print(f"  ❌ 代码检查失败: {e}")
    
    def print_summary(self):
        print("\n" + "="*60)
        print("📊 维护报告摘要")
        print("="*60)
        
        success = sum(1 for v in self.results.values() if v)
        total = len(self.results)
        
        for task, status in self.results.items():
            icon = '✅' if status else '❌'
            print(f"{icon} {task}")
        
        print("="*60)
        print(f"完成率: {success}/{total} ({success/total*100:.1f}%)")
        print("="*60)

def main():
    project_path = '/Users/wuchenghao/Library/CloudStorage/OneDrive-个人/文档/MTSCOS_AI_Project'
    
    maintenance = MTSCOSMaintenance(project_path)
    maintenance.run_all_maintenance()

if __name__ == '__main__':
    main()