#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
MTSCOS AI Project - 系统升级维护脚本
用于执行系统优化、版本升级和维护任务

import os
import sys
import time
import subprocess
import logging
from datetime import datetime

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('system_maintenance.log'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger('system_maintenance')

class SystemMaintenance:
    """系统维护类"""

    def __init__(self):
        """初始化维护类"""
        self.project_dir = os.path.dirname(os.path.abspath(__file__))
        self.flask_app_dir = os.path.join(self.project_dir, 'flask-app')
        self.logs_dir = os.path.join(self.project_dir, 'logs')
        self.backups_dir = os.path.join(self.project_dir, 'backups')

        # 创建必要目录
        os.makedirs(self.logs_dir, exist_ok=True)
        os.makedirs(self.backups_dir, exist_ok=True)

        logger.info("系统维护脚本初始化完成")

    def run_command(self, command, cwd=None):
        """运行命令

        Args:
            command: 命令字符串
            cwd: 工作目录

        Returns:
            tuple: (return_code, stdout, stderr)
        logger.info(f"执行命令: {command}")

        try:
            result = subprocess.run(
                command,
                shell=True,
                cwd=cwd,
                capture_output=True,
                text=True,
                timeout=300
            )

                logger.info(f"命令输出:\n{result.stdout}")
            if result.stderr:
                logger.warning(f"命令错误输出:\n{result.stderr}")

            return (result.returncode, result.stdout, result.stderr)
        except subprocess.TimeoutExpired:
            logger.error(f"命令执行超时: {command}")
            return (-1, "", "命令执行超时")
        except Exception as e:
            logger.error(f"命令执行失败: {str(e)}")
            return (-1, "", str(e))

    def clean_logs(self):
        """清理旧日志文件"""
        logger.info("开始清理日志文件...")

        try:
            # 清理flask-app目录下的日志文件
            log_files = []
                for filename in filenames:
                    if filename.endswith('.log') or filename.startswith('system_size.log'):
                        log_files.append(os.path.join(dirpath, filename))

            logger.info(f"找到 {len(log_files)} 个日志文件")

            # 删除超过7天的日志文件
            current_time = time.time()
            deleted_count = 0

            for log_file in log_files:
                try:
                    file_age = current_time - os.path.getmtime(log_file)
                    if file_age > 7 * 24 * 60 * 60:  # 7天
                        logger.info(f"删除旧日志文件: {log_file}")
                        deleted_count += 1
                except Exception as e:
                    logger.warning(f"删除日志文件失败 {log_file}: {str(e)}")

            logger.info(f"已清理 {deleted_count} 个旧日志文件")
            return True
            logger.error(f"清理日志失败: {str(e)}")
            return False

    def backup_database(self):
        logger.info("开始备份数据库...")

        try:
            db_path = os.path.join(self.flask_app_dir, 'app.db')

                # 创建备份文件名
                backup_name = f"app_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.db"
                backup_path = os.path.join(self.backups_dir, backup_name)

                # 复制数据库文件
                import shutil
                shutil.copy2(db_path, backup_path)

                logger.info(f"数据库备份完成: {backup_path}")
                return True
            else:
                logger.warning("数据库文件不存在，跳过备份")
                return False
        except Exception as e:
            logger.error(f"备份数据库失败: {str(e)}")
            return False

        """优化数据库"""

        try:

                # 使用VACUUM命令优化SQLite数据库
                conn = sqlite3.connect(db_path)
                cursor = conn.cursor()
                cursor.execute('VACUUM')
                conn.commit()
                conn.close()

                logger.info("数据库优化完成")
                return True
                logger.warning("数据库文件不存在，跳过优化")
                return False
            logger.error(f"优化数据库失败: {str(e)}")
            return False

    def update_dependencies(self):
        """更新依赖"""
        try:
            # 更新pip
            self.run_command('pip3 install --upgrade pip')
            # 更新核心依赖
                'flask',
                'requests',
                'numpy',
                'python-dotenv',
                'sqlalchemy'
            ]

                self.run_command(f'pip3 install --upgrade {dep}')

            logger.info("依赖更新完成")
            return True
        except Exception as e:
            logger.error(f"更新依赖失败: {str(e)}")
            return False

    def clean_pycache(self):
        """清理Python缓存文件"""
        logger.info("开始清理Python缓存...")

        try:

            for dirpath, dirnames, filenames in os.walk(self.project_dir):
                if '.git' in dirpath.split(os.sep):

                for filename in filenames:
                    if filename.endswith('.pyc') or filename.endswith('.pyo'):
                        try:
                            os.remove(os.path.join(dirpath, filename))
                        except Exception as e:

                # 删除__pycache__目录
                if '__pycache__' in dirnames:
                    pycache_dir = os.path.join(dirpath, '__pycache__')
                        import shutil
                        shutil.rmtree(pycache_dir)
                        pycache_count += 1
                        pass
            logger.info(f"已清理 {pycache_count} 个缓存文件/目录")
        except Exception as e:
            logger.error(f"清理缓存失败: {str(e)}")
            return False

    def run_database_migrations(self):
        """运行数据库迁移"""
        logger.info("开始运行数据库迁移...")
        try:
            # 检查并创建必要的表
            migrate_scripts = [
                'create_exam_tables.py',
            ]

                script_path = os.path.join(self.flask_app_dir, script)
                if os.path.exists(script_path):
                    logger.info(f"运行迁移脚本: {script}")
                    self.run_command(f'python3 {script}', cwd=self.flask_app_dir)

            logger.info("数据库迁移完成")
        except Exception as e:
            logger.error(f"运行数据库迁移失败: {str(e)}")
            return False
    def validate_system(self):
        """验证系统完整性"""
        checks = [
            ('VERSION文件', os.path.exists(os.path.join(self.project_dir, 'VERSION'))),
            ('app/__init__.py', os.path.exists(os.path.join(self.flask_app_dir, 'app', '__init__.py'))),
            ('clean_start.py', os.path.exists(os.path.join(self.flask_app_dir, 'clean_start.py'))),
        ]
        for check_name, passed in checks:
            status = "✅" if passed else "❌"
            logger.info(f"{status} {check_name}")
            if not passed:
                all_passed = False

        if all_passed:
            logger.info("系统完整性验证通过")
        else:

        return all_passed

    def generate_maintenance_report(self, results):
        """生成维护报告"""
        logger.info("生成维护报告...")

            'timestamp': datetime.now().isoformat(),
            'version': self.get_version(),
            'results': results,
            'summary': {
                'total_tasks': len(results),
                'successful_tasks': sum(1 for r in results.values() if r),
                'failed_tasks': sum(1 for r in results.values() if not r)
            }
        }

        # 打印报告
        print("\n" + "="*60)
        print("          系统维护报告")
        print("="*60)
        print(f"时间: {report['timestamp']}")
        print(f"版本: {report['version']}")
        print("\n任务执行结果:")
        print("-"*40)

        for task, success in results.items():
            status = "✅ 成功" if success else "❌ 失败"
            print(f"{task}: {status}")

        print("\n" + "-"*40)
        print(f"总计: {report['summary']['total_tasks']} 个任务")
        print(f"成功: {report['summary']['successful_tasks']} 个")
        print(f"失败: {report['summary']['failed_tasks']} 个")
        print("="*60)

        # 保存报告
        report_path = os.path.join(self.logs_dir, f"maintenance_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json")
        # JSON import removed - using database
with open(report_path, 'w', encoding='utf-8') as f:
            json.dump(report, f, ensure_ascii=False, indent=2)

        logger.info(f"维护报告已保存: {report_path}")
        return report

    def get_version(self):
        """获取当前版本号"""
        version_path = os.path.join(self.project_dir, 'VERSION')
        if os.path.exists(version_path):
            with open(version_path, 'r') as f:
                return f.read().strip()
        return "unknown"

    def run_full_maintenance(self):
        """运行完整维护流程"""
        logger.info("="*60)
        logger.info("开始执行系统维护")
        logger.info("="*60)
        results = {}

        # 1. 备份数据库
        results['数据库备份'] = self.backup_database()

        # 2. 清理日志
        results['清理日志'] = self.clean_logs()

        # 3. 清理缓存
        results['清理缓存'] = self.clean_pycache()

        # 4. 优化数据库
        results['优化数据库'] = self.optimize_database()

        # 5. 更新依赖
        results['更新依赖'] = self.update_dependencies()

        # 6. 运行数据库迁移
        results['数据库迁移'] = self.run_database_migrations()
        # 7. 验证系统完整性
        results['系统验证'] = self.validate_system()

        # 生成报告
        self.generate_maintenance_report(results)

        logger.info("="*60)
        logger.info("系统维护完成")
        logger.info("="*60)

        return results

def main():
    """主函数"""
    maintenance = SystemMaintenance()

    print("""
╔══════════════════════════════════════════════════════════════╗
║              MTSCOS AI Project 系统维护工具                   ║
╚══════════════════════════════════════════════════════════════╝
""")

    print("请选择维护操作:")
    print("2. 仅清理日志")
    print("3. 仅备份数据库")
    print("4. 仅优化数据库")
    print("5. 仅更新依赖")
    print("6. 验证系统完整性")
    print("0. 退出")

    try:
        choice = int(input("\n请输入选择: "))

        if choice == 1:
            maintenance.run_full_maintenance()
        elif choice == 2:
            print("\n日志清理完成")
        elif choice == 3:
            maintenance.backup_database()
            print("\n数据库备份完成")
        elif choice == 4:
            maintenance.optimize_database()
            print("\n数据库优化完成")
        elif choice == 5:
            maintenance.update_dependencies()
            print("\n依赖更新完成")
        elif choice == 6:
            maintenance.validate_system()
            print("\n系统验证完成")
        elif choice == 0:
            return
            print("无效选择")

    except ValueError:
        print("请输入有效数字")
    except KeyboardInterrupt:
        print("\n维护操作已取消")

if __name__ == "__main__":
    main()
