#!/usr/bin/env python3
"""
系统优化脚本
用于优化系统功能，保证系统运行流畅
"""

import os
import json
import sqlite3
import logging
import shutil
import time
import threading
import psutil
from datetime import datetime, timedelta

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('system_optimization.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class SystemOptimizer:
    """系统优化器"""
    
    def __init__(self):
        self.db_path = 'app.db'
        self.backup_dir = 'backups/system_optimization'
        os.makedirs(self.backup_dir, exist_ok=True)
    
    def optimize_database(self):
        """优化数据库"""
        logger.info("开始优化数据库...")
        
        try:
            # 连接数据库
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # 执行数据库优化
            cursor.execute('VACUUM;')
            cursor.execute('ANALYZE;')
            
            # 优化数据库索引
            tables = ['users', 'questions', 'question_options', 'test_scores', 'system_configs']
            for table in tables:
                try:
                    cursor.execute(f'REINDEX {table};')
                    logger.info(f"已优化表 {table} 的索引")
                except Exception as idx_e:
                    logger.warning(f"优化表 {table} 索引失败: {str(idx_e)}")
            
            # 清理旧的测试记录（保留最近30天的记录）
            cursor.execute('''
                DELETE FROM test_scores WHERE assessment_date < datetime('now', '-30 days');
            ''')
            
            # 清理旧的系统更新报告（保留最近30天的记录）
            cursor.execute('''
                DELETE FROM system_upgrade_reports WHERE created_at < datetime('now', '-30 days');
            ''')
            
            # 清理旧的JSON文件记录（保留最近60天的记录）
            cursor.execute('''
                DELETE FROM json_files WHERE uploaded_at < datetime('now', '-60 days');
            ''')
            
            conn.commit()
            conn.close()
            
            logger.info("数据库优化完成")
            return True
            
        except Exception as e:
            logger.error(f"数据库优化失败: {str(e)}")
            return False
    
    def monitor_system_resources(self):
        """监控系统资源使用情况"""
        logger.info("开始监控系统资源...")
        
        try:
            # 获取CPU使用率
            cpu_percent = psutil.cpu_percent(interval=1)
            
            # 获取内存使用情况
            mem = psutil.virtual_memory()
            mem_percent = mem.percent
            mem_used = mem.used / (1024 * 1024 * 1024)  # GB
            mem_total = mem.total / (1024 * 1024 * 1024)  # GB
            
            # 获取磁盘使用情况
            disk = psutil.disk_usage('/')
            disk_percent = disk.percent
            disk_used = disk.used / (1024 * 1024 * 1024)  # GB
            disk_total = disk.total / (1024 * 1024 * 1024)  # GB
            
            # 获取Python进程数量
            python_processes = [p for p in psutil.process_iter(['name']) if 'python' in p.info['name'].lower()]
            python_process_count = len(python_processes)
            
            logger.info(f"系统资源监控结果:")
            logger.info(f"  CPU使用率: {cpu_percent}%")
            logger.info(f"  内存使用: {mem_used:.2f}GB / {mem_total:.2f}GB ({mem_percent}%)")
            logger.info(f"  磁盘使用: {disk_used:.2f}GB / {disk_total:.2f}GB ({disk_percent}%)")
            logger.info(f"  Python进程数: {python_process_count}")
            
            # 保存监控结果到数据库
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT INTO system_health_logs (timestamp, cpu_usage, memory_usage, disk_usage, python_process_count)
                VALUES (?, ?, ?, ?, ?)
            ''', (datetime.now().strftime("%Y-%m-%d %H:%M:%S"), cpu_percent, mem_percent, disk_percent, python_process_count))
            
            conn.commit()
            conn.close()
            
            return {
                'cpu_percent': cpu_percent,
                'memory_percent': mem_percent,
                'disk_percent': disk_percent,
                'python_process_count': python_process_count
            }
            
        except Exception as e:
            logger.error(f"监控系统资源失败: {str(e)}")
            return None
    
    def clean_log_files(self):
        """清理旧的日志文件"""
        logger.info("开始清理日志文件...")
        
        try:
            # 清理旧的系统日志
            log_files = [
                'system_time.log.*',
                'ai_brain.log.*',
                'system_health.log.*'
            ]
            
            for pattern in log_files:
                import glob
                for file in glob.glob(pattern):
                    try:
                        os.remove(file)
                        logger.info(f"已删除旧日志文件: {file}")
                    except Exception as e:
                        logger.error(f"删除日志文件失败 {file}: {str(e)}")
            
            logger.info("日志文件清理完成")
            return True
            
        except Exception as e:
            logger.error(f"清理日志文件失败: {str(e)}")
            return False
    
    def clean_temporary_files(self):
        """清理临时文件"""
        logger.info("开始清理临时文件...")
        
        try:
            # 清理测试生成的临时文件
            temp_files = [
                'test_sync.json',
                'test_*.json',
                '*.pyc',
                '__pycache__/*'
            ]
            
            for pattern in temp_files:
                import glob
                for file in glob.glob(pattern, recursive=True):
                    try:
                        if os.path.isfile(file):
                            os.remove(file)
                            logger.info(f"已删除临时文件: {file}")
                        elif os.path.isdir(file):
                            shutil.rmtree(file)
                            logger.info(f"已删除临时目录: {file}")
                    except Exception as e:
                        logger.error(f"删除临时文件失败 {file}: {str(e)}")
            
            logger.info("临时文件清理完成")
            return True
            
        except Exception as e:
            logger.error(f"清理临时文件失败: {str(e)}")
            return False
    
    def optimize_system_config(self):
        """优化系统配置"""
        logger.info("开始优化系统配置...")
        
        try:
            # 优化Flask应用配置
            config_updates = {
                'DEBUG': False,  # 生产环境禁用DEBUG模式
                'MAX_CONTENT_LENGTH': 16 * 1024 * 1024,  # 限制上传文件大小为16MB
                'JSON_SORT_KEYS': False,  # 禁用JSON排序，提高性能
                'TEMPLATES_AUTO_RELOAD': False,  # 生产环境禁用模板自动重载
            }
            
            logger.info(f"建议的系统配置优化: {config_updates}")
            
            # 更新系统配置表
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            for key, value in config_updates.items():
                # 将Python类型转换为JSON字符串
                value_str = json.dumps(value)
                cursor.execute('''
                    INSERT OR REPLACE INTO system_configs (key, value, description)
                    VALUES (?, ?, ?)
                ''', (key, value_str, f"系统优化配置: {key}"))
            
            conn.commit()
            conn.close()
            
            logger.info("系统配置优化完成")
            return True
            
        except Exception as e:
            logger.error(f"优化系统配置失败: {str(e)}")
            return False
    
    def backup_system(self):
        """备份系统关键数据"""
        logger.info("开始备份系统关键数据...")
        
        try:
            # 备份数据库
            backup_file = os.path.join(self.backup_dir, f'app.db.backup_{datetime.now().strftime("%Y%m%d%H%M%S")}')
            shutil.copy2(self.db_path, backup_file)
            logger.info(f"已备份数据库到: {backup_file}")
            
            # 备份关键配置文件
            config_files = ['config.json', 'system_config.json', 'feature_library.json']
            for file in config_files:
                if os.path.exists(file):
                    backup_config_file = os.path.join(self.backup_dir, f'{file}.backup_{datetime.now().strftime("%Y%m%d%H%M%S")}')
                    shutil.copy2(file, backup_config_file)
                    logger.info(f"已备份配置文件到: {backup_config_file}")
            
            logger.info("系统备份完成")
            return True
            
        except Exception as e:
            logger.error(f"系统备份失败: {str(e)}")
            return False
    
    def run_full_optimization(self):
        """运行完整的系统优化"""
        logger.info("开始运行完整的系统优化...")
        
        # 先进行资源监控
        resource_stats = self.monitor_system_resources()
        
        results = {
            'backup': self.backup_system(),
            'database': self.optimize_database(),
            'logs': self.clean_log_files(),
            'temp_files': self.clean_temporary_files(),
            'config': self.optimize_system_config()
        }
        
        logger.info(f"系统优化结果: {results}")
        
        # 生成优化报告
        report = {
            'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            'resource_stats': resource_stats,
            'results': results,
            'success': all(results.values())
        }
        
        # 保存优化报告
        report_file = os.path.join(self.backup_dir, f'optimization_report_{datetime.now().strftime("%Y%m%d%H%M%S")}.json')
        with open(report_file, 'w', encoding='utf-8') as f:
            json.dump(report, f, ensure_ascii=False, indent=2)
        
        logger.info(f"系统优化报告已保存到: {report_file}")
        
        if all(results.values()):
            logger.info("系统优化成功完成")
        else:
            logger.warning("系统优化部分项目失败，请查看日志")
        
        return all(results.values())
    
    def start_scheduled_optimization(self, interval_hours=24):
        """启动定时优化任务"""
        logger.info(f"启动定时优化任务，每 {interval_hours} 小时执行一次")
        
        def scheduled_task():
            while True:
                try:
                    self.run_full_optimization()
                    # 等待指定时间后再次执行
                    time.sleep(interval_hours * 3600)
                except Exception as e:
                    logger.error(f"定时优化任务执行失败: {str(e)}")
                    time.sleep(3600)  # 出错后等待1小时重试
        
        # 创建并启动线程
        self.scheduled_thread = threading.Thread(target=scheduled_task, daemon=True)
        self.scheduled_thread.start()
        logger.info("定时优化任务已启动")
        
        return self.scheduled_thread
    
    def stop_scheduled_optimization(self):
        """停止定时优化任务"""
        if hasattr(self, 'scheduled_thread') and self.scheduled_thread.is_alive():
            # 由于线程是守护线程，会随主进程结束而结束
            logger.info("定时优化任务已停止")
            return True
        return False

# 命令行使用示例
if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='系统优化脚本')
    parser.add_argument('--run', action='store_true', help='运行一次完整优化')
    parser.add_argument('--start-schedule', action='store_true', help='启动定时优化任务')
    parser.add_argument('--stop-schedule', action='store_true', help='停止定时优化任务')
    parser.add_argument('--interval', type=int, default=24, help='定时优化间隔（小时），默认24小时')
    
    args = parser.parse_args()
    
    optimizer = SystemOptimizer()
    
    if args.run:
        optimizer.run_full_optimization()
    elif args.start_schedule:
        optimizer.start_scheduled_optimization(args.interval)
        print(f"定时优化任务已启动，每 {args.interval} 小时执行一次")
        try:
            # 保持主进程运行
            while True:
                time.sleep(3600)
        except KeyboardInterrupt:
            print("定时优化任务已停止")
    elif args.stop_schedule:
        optimizer.stop_scheduled_optimization()
        print("定时优化任务已停止")
    else:
        parser.print_help()
