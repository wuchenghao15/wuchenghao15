#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
自动错误修复系统
监控系统运行状态，自动检测和修复错误异常
"""

import os
import sys
import logging
import traceback
import subprocess
import time
from datetime import datetime
import signal
import threading

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('auto_error_fix.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class AutoErrorFixer:
    """自动错误修复器"""
    
    def __init__(self):
        self.error_history = []
        self.running = True
        self.fix_patterns = {
            'module_import_error': self.fix_module_import_error,
            'database_connection_error': self.fix_database_connection_error,
            'file_not_found_error': self.fix_file_not_found_error,
            'permission_error': self.fix_permission_error,
            'syntax_error': self.fix_syntax_error,
            'port_in_use_error': self.fix_port_in_use_error,
            'missing_config_error': self.fix_missing_config_error
        }
    
    def start_monitoring(self, interval=60):
        """开始监控系统状态"""
        logger.info("启动自动错误修复系统...")
        
        while self.running:
            try:
                # 检查系统状态
                self.check_system_status()
                # 检查日志文件中的错误
                self.check_log_files()
                # 检查进程状态
                self.check_process_status()
                
                # 等待指定时间
                time.sleep(interval)
                
            except Exception as e:
                logger.error(f"监控系统发生错误: {str(e)}")
                traceback.print_exc()
        
        logger.info("自动错误修复系统已停止")
    
    def stop(self, signum=None, frame=None):
        """停止监控系统"""
        logger.info("正在停止自动错误修复系统...")
        self.running = False
    
    def check_system_status(self):
        """检查系统状态"""
        logger.debug("检查系统状态...")
        
        # 检查Python版本
        python_version = sys.version_info
        if python_version < (3, 7):
            logger.warning(f"Python版本过低: {python_version.major}.{python_version.minor}.{python_version.micro}")
        
        # 检查依赖包
        self.check_dependencies()
    
    def check_dependencies(self):
        """检查依赖包是否安装"""
        required_packages = [
            'flask', 'requests', 'beautifulsoup4', 'sqlite3',
            'datetime', 'logging', 'json', 'os', 'sys'
        ]
        
        for package in required_packages:
            try:
                __import__(package)
                logger.debug(f"依赖包 {package} 已安装")
            except ImportError:
                logger.error(f"依赖包 {package} 未安装")
                self.fix_module_import_error(package)
    
    def check_log_files(self):
        """检查日志文件中的错误"""
        logger.debug("检查日志文件...")
        
        # 检查主要日志文件
        log_files = [
            'color_scheme.log',
            'auto_error_fix.log'
        ]
        
        for log_file in log_files:
            if os.path.exists(log_file):
                try:
                    with open(log_file, 'r') as f:
                        lines = f.readlines()
                        for line in lines[-100:]:  # 只检查最后100行
                            if 'ERROR' in line or 'Exception' in line:
                                self.analyze_error(line)
                except Exception as e:
                    logger.error(f"读取日志文件 {log_file} 失败: {str(e)}")
    
    def check_process_status(self):
        """检查进程状态"""
        logger.debug("检查进程状态...")
        
        try:
            # 检查Flask应用是否在运行
            result = subprocess.run(
                ['lsof', '-i', ':8888'],
                capture_output=True,
                text=True
            )
            
            if 'LISTEN' not in result.stdout:
                logger.warning("Flask应用未在端口8888上运行")
                self.restart_flask_app()
            else:
                logger.debug("Flask应用正在运行")
        except Exception as e:
            logger.error(f"检查进程状态失败: {str(e)}")
    
    def analyze_error(self, error_line):
        """分析错误信息"""
        logger.debug(f"分析错误: {error_line.strip()}")
        
        # 简单的错误类型识别
        if 'ModuleNotFoundError' in error_line:
            module_name = error_line.split("'").pop(-2) if "'" in error_line else "未知模块"
            self.handle_error('module_import_error', {'module_name': module_name})
        elif 'sqlite3.OperationalError' in error_line:
            self.handle_error('database_connection_error', {'error': error_line})
        elif 'FileNotFoundError' in error_line:
            self.handle_error('file_not_found_error', {'error': error_line})
        elif 'PermissionError' in error_line:
            self.handle_error('permission_error', {'error': error_line})
        elif 'SyntaxError' in error_line:
            self.handle_error('syntax_error', {'error': error_line})
        elif 'Address already in use' in error_line:
            self.handle_error('port_in_use_error', {'error': error_line})
        elif 'Config' in error_line and 'AttributeError' in error_line:
            self.handle_error('missing_config_error', {'error': error_line})
    
    def handle_error(self, error_type, error_info):
        """处理错误"""
        logger.info(f"处理错误: {error_type}, 详情: {error_info}")
        
        # 记录错误历史
        error_record = {
            'error_type': error_type,
            'error_info': error_info,
            'timestamp': datetime.now().isoformat(),
            'status': 'unfixed'
        }
        self.error_history.append(error_record)
        
        # 尝试修复错误
        if error_type in self.fix_patterns:
            try:
                success = self.fix_patterns[error_type](**error_info)
                error_record['status'] = 'fixed' if success else 'unfixable'
                error_record['fixed_at'] = datetime.now().isoformat()
                logger.info(f"错误修复 {'成功' if success else '失败'}: {error_type}")
            except Exception as e:
                error_record['status'] = 'fix_error'
                error_record['fix_error'] = str(e)
                logger.error(f"修复错误时发生异常: {str(e)}")
        else:
            error_record['status'] = 'unhandled'
            logger.warning(f"未处理的错误类型: {error_type}")
    
    def fix_module_import_error(self, module_name):
        """修复模块导入错误"""
        logger.info(f"尝试修复模块导入错误: {module_name}")
        
        try:
            # 尝试安装缺失的模块
            result = subprocess.run(
                [sys.executable, '-m', 'pip', 'install', module_name, '--break-system-packages'],
                capture_output=True,
                text=True,
                timeout=30
            )
            
            if result.returncode == 0:
                logger.info(f"成功安装模块: {module_name}")
                return True
            else:
                logger.error(f"安装模块失败: {module_name}, 错误: {result.stderr}")
                return False
        except Exception as e:
            logger.error(f"修复模块导入错误失败: {str(e)}")
            return False
    
    def fix_database_connection_error(self, error):
        """修复数据库连接错误"""
        logger.info(f"尝试修复数据库连接错误: {error}")
        
        try:
            # 检查数据库文件是否存在
            db_files = ['color_schemes.db']
            for db_file in db_files:
                if not os.path.exists(db_file):
                    logger.warning(f"数据库文件不存在: {db_file}")
                    # 尝试创建空数据库文件
                    with open(db_file, 'w') as f:
                        f.write('')
                    logger.info(f"已创建空数据库文件: {db_file}")
            
            # 检查数据库文件权限
            for db_file in db_files:
                if os.path.exists(db_file):
                    os.chmod(db_file, 0o644)
                    logger.info(f"已设置数据库文件权限: {db_file}")
            
            return True
        except Exception as e:
            logger.error(f"修复数据库连接错误失败: {str(e)}")
            return False
    
    def fix_file_not_found_error(self, error):
        """修复文件未找到错误"""
        logger.info(f"尝试修复文件未找到错误: {error}")
        
        try:
            # 从错误信息中提取文件名
            if 'No such file or directory' in error:
                file_path = error.split(':')[-1].strip()
                logger.warning(f"文件未找到: {file_path}")
                
                # 尝试创建目录
                dir_path = os.path.dirname(file_path)
                if dir_path and not os.path.exists(dir_path):
                    os.makedirs(dir_path, exist_ok=True)
                    logger.info(f"已创建目录: {dir_path}")
                    return True
            
            return False
        except Exception as e:
            logger.error(f"修复文件未找到错误失败: {str(e)}")
            return False
    
    def fix_permission_error(self, error):
        """修复权限错误"""
        logger.info(f"尝试修复权限错误: {error}")
        
        try:
            # 从错误信息中提取路径
            if 'Permission denied' in error:
                path = error.split(':')[-1].strip()
                logger.warning(f"权限错误: {path}")
                
                # 尝试更改权限
                if os.path.exists(path):
                    if os.path.isfile(path):
                        os.chmod(path, 0o644)
                    else:
                        os.chmod(path, 0o755)
                    logger.info(f"已更改权限: {path}")
                    return True
            
            return False
        except Exception as e:
            logger.error(f"修复权限错误失败: {str(e)}")
            return False
    
    def fix_syntax_error(self, error):
        """修复语法错误"""
        logger.info(f"尝试修复语法错误: {error}")
        
        try:
            # 语法错误通常需要人工修复，这里只记录详细信息
            logger.error("语法错误需要人工修复，无法自动修复")
            return False
        except Exception as e:
            logger.error(f"修复语法错误失败: {str(e)}")
            return False
    
    def fix_port_in_use_error(self, error):
        """修复端口被占用错误"""
        logger.info(f"尝试修复端口被占用错误: {error}")
        
        try:
            # 查找并杀死占用端口8888的进程
            result = subprocess.run(
                ['lsof', '-i', ':8888', '-t'],
                capture_output=True,
                text=True
            )
            
            if result.stdout:
                pids = result.stdout.strip().split('\n')
                for pid in pids:
                    try:
                        os.kill(int(pid), signal.SIGTERM)
                        logger.info(f"已杀死占用端口8888的进程: {pid}")
                    except Exception as e:
                        logger.error(f"杀死进程失败: {pid}, 错误: {str(e)}")
            
            return True
        except Exception as e:
            logger.error(f"修复端口被占用错误失败: {str(e)}")
            return False
    
    def fix_missing_config_error(self, error):
        """修复缺失配置错误"""
        logger.info(f"尝试修复缺失配置错误: {error}")
        
        try:
            # 检查app.py文件中的Config类
            app_file = '/Users/wuchenghao/Library/CloudStorage/OneDrive-个人/文档/MTSCOS_AI_Project/flask-app/app.py'
            if os.path.exists(app_file):
                with open(app_file, 'r') as f:
                    content = f.read()
                
                # 检查Config类是否存在
                if 'class Config' not in content:
                    logger.error("Config类不存在于app.py中")
                    return False
                
                # 检查是否缺少必要的配置项
                missing_attrs = []
                for attr in ['SECRET_KEY', 'DATABASE_URI', 'ENV', 'DEBUG']:
                    if f'{attr} =' not in content:
                        missing_attrs.append(attr)
                
                if missing_attrs:
                    logger.warning(f"缺少配置项: {missing_attrs}")
                    # 尝试添加缺失的配置项
                    new_content = content
                    for attr in missing_attrs:
                        if attr == 'SECRET_KEY':
                            new_content = new_content.replace('class Config:', f'class Config:\n    SECRET_KEY = \'your-secret-key\'\n')
                        elif attr == 'DATABASE_URI':
                            new_content = new_content.replace('class Config:', f'class Config:\n    DATABASE_URI = \'sqlite:///mtscos.db\'\n')
                        elif attr == 'ENV':
                            new_content = new_content.replace('class Config:', f'class Config:\n    ENV = \'development\'\n')
                        elif attr == 'DEBUG':
                            new_content = new_content.replace('class Config:', f'class Config:\n    DEBUG = True\n')
                    
                    with open(app_file, 'w') as f:
                        f.write(new_content)
                    logger.info(f"已添加缺失的配置项: {missing_attrs}")
                    return True
            
            return False
        except Exception as e:
            logger.error(f"修复缺失配置错误失败: {str(e)}")
            return False
    
    def restart_flask_app(self):
        """重启Flask应用"""
        logger.info("尝试重启Flask应用...")
        
        try:
            # 先杀死现有的Flask进程
            self.fix_port_in_use_error({'error': 'Address already in use'})
            
            # 启动Flask应用
            flask_app_path = '/Users/wuchenghao/Library/CloudStorage/OneDrive-个人/文档/MTSCOS_AI_Project/flask-app/app.py'
            subprocess.Popen(
                [sys.executable, flask_app_path],
                cwd='/Users/wuchenghao/Library/CloudStorage/OneDrive-个人/文档/MTSCOS_AI_Project',
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )
            
            logger.info("已启动Flask应用")
            return True
        except Exception as e:
            logger.error(f"重启Flask应用失败: {str(e)}")
            return False
    
    def run_fix(self, error_type, **error_info):
        """手动运行修复"""
        logger.info(f"手动运行修复: {error_type}, 详情: {error_info}")
        
        if error_type in self.fix_patterns:
            try:
                success = self.fix_patterns[error_type](**error_info)
                logger.info(f"手动修复 {'成功' if success else '失败'}: {error_type}")
                return success
            except Exception as e:
                logger.error(f"手动修复失败: {str(e)}")
                return False
        else:
            logger.error(f"未知的错误类型: {error_type}")
            return False


def main():
    """主函数"""
    fixer = AutoErrorFixer()
    
    # 启动监控线程
    monitor_thread = threading.Thread(target=fixer.start_monitoring, args=(60,))
    monitor_thread.daemon = True
    monitor_thread.start()
    
    logger.info("自动错误修复系统已启动，按Ctrl+C停止")
    
    try:
        # 主线程保持运行
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        logger.info("收到停止信号")
    finally:
        fixer.stop()
        monitor_thread.join(timeout=5)


if __name__ == "__main__":
    main()
