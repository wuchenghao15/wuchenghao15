#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
脚本自动升级系统
自动升级系统中的脚本文件
"""

import os
import sys
import logging
import subprocess
import json
import time
from datetime import datetime
import requests
import shutil
import signal
import threading
import hashlib

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('auto_script_upgrade.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class AutoScriptUpgrader:
    """脚本自动升级器"""
    
    def __init__(self):
        self.running = True
        self.script_config_file = 'script_config.json'
        self.scripts_dir = '.'  # 当前目录
        self.backups_dir = 'script_backups'
        
        # 初始化配置
        self.init_config()
    
    def init_config(self):
        """初始化脚本配置"""
        if not os.path.exists(self.script_config_file):
            default_config = {
                'current_version': '1.0.0',
                'last_upgraded': datetime.now().isoformat(),
                'upgrade_check_interval': 86400,  # 24小时
                'scripts_to_upgrade': [
                    'ai_color_scheme_scraper.py',
                    'auto_error_fix.py',
                    'auto_ai_upgrade.py',
                    'auto_db_upgrade.py',
                    'auto_script_upgrade.py'  # 支持自升级
                ],
                'auto_upgrade_enabled': True,
                'upgrade_history': []
            }
            with open(self.script_config_file, 'w') as f:
                json.dump(default_config, f, indent=2)
            logger.info(f"已创建默认脚本配置文件: {self.script_config_file}")
        
        # 创建备份目录
        if not os.path.exists(self.backups_dir):
            os.makedirs(self.backups_dir)
            logger.info(f"已创建备份目录: {self.backups_dir}")
    
    def load_config(self):
        """加载脚本配置"""
        try:
            with open(self.script_config_file, 'r') as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"加载脚本配置失败: {str(e)}")
            return {
                'current_version': '1.0.0',
                'last_upgraded': datetime.now().isoformat(),
                'upgrade_check_interval': 86400,
                'scripts_to_upgrade': [
                    'ai_color_scheme_scraper.py',
                    'auto_error_fix.py',
                    'auto_ai_upgrade.py',
                    'auto_db_upgrade.py',
                    'auto_script_upgrade.py'
                ],
                'auto_upgrade_enabled': True,
                'upgrade_history': []
            }
    
    def save_config(self, config):
        """保存脚本配置"""
        try:
            with open(self.script_config_file, 'w') as f:
                json.dump(config, f, indent=2)
            logger.info(f"已保存脚本配置到 {self.script_config_file}")
        except Exception as e:
            logger.error(f"保存脚本配置失败: {str(e)}")
    
    def start_upgrade_monitor(self, interval=86400):
        """开始升级监控"""
        logger.info("启动脚本自动升级监控...")
        
        while self.running:
            try:
                # 检查是否需要升级
                if self.should_upgrade():
                    logger.info("开始脚本自动升级...")
                    self.run_upgrade()
                else:
                    logger.info("脚本版本已是最新，无需升级")
                
                # 等待指定时间
                time.sleep(interval)
                
            except Exception as e:
                logger.error(f"升级监控发生错误: {str(e)}")
                import traceback
                traceback.print_exc()
        
        logger.info("脚本自动升级监控已停止")
    
    def stop(self, signum=None, frame=None):
        """停止监控系统"""
        logger.info("正在停止脚本自动升级监控...")
        self.running = False
    
    def should_upgrade(self):
        """检查是否需要升级"""
        config = self.load_config()
        
        if not config.get('auto_upgrade_enabled', True):
            logger.info("脚本自动升级已禁用")
            return False
        
        # 检查距离上次升级的时间
        last_upgraded = datetime.fromisoformat(config.get('last_upgraded', datetime.now().isoformat()))
        interval = config.get('upgrade_check_interval', 86400)
        
        if (datetime.now() - last_upgraded).total_seconds() < interval:
            logger.debug(f"距离上次升级时间不足 {interval} 秒，跳过升级检查")
            return False
        
        # 检查是否有新版本
        current_version = config.get('current_version', '1.0.0')
        latest_version = self.get_latest_version()
        
        if latest_version and self.is_newer_version(latest_version, current_version):
            logger.info(f"发现新版本: {latest_version} (当前版本: {current_version})")
            return True
        
        return False
    
    def get_latest_version(self):
        """获取最新版本信息"""
        logger.info("检查最新脚本版本...")
        
        # 这里可以从GitHub、PyPI或自定义API获取最新版本
        # 目前使用模拟数据
        try:
            # 模拟从API获取版本
            # response = requests.get('https://api.example.com/script/version', timeout=10)
            # response.raise_for_status()
            # return response.json().get('version')
            
            # 模拟返回最新版本
            return '2.0.0'
        except Exception as e:
            logger.error(f"获取最新版本失败: {str(e)}")
            return None
    
    def is_newer_version(self, latest, current):
        """检查是否是更新的版本"""
        try:
            latest_parts = list(map(int, latest.split('.')))
            current_parts = list(map(int, current.split('.')))
            
            for l, c in zip(latest_parts, current_parts):
                if l > c:
                    return True
                elif l < c:
                    return False
            
            # 如果前面的版本号相同，检查长度
            return len(latest_parts) > len(current_parts)
        except Exception as e:
            logger.error(f"版本比较失败: {str(e)}")
            return False
    
    def run_upgrade(self):
        """执行升级"""
        logger.info("开始执行脚本升级...")
        
        config = self.load_config()
        current_version = config.get('current_version', '1.0.0')
        latest_version = self.get_latest_version()
        
        if not latest_version:
            logger.error("无法获取最新版本，升级失败")
            return False
        
        try:
            # 1. 备份当前脚本
            backup_info = self.backup_scripts()
            
            # 2. 下载并安装最新脚本
            self.download_and_install_scripts(latest_version)
            
            # 3. 更新配置
            config['current_version'] = latest_version
            config['last_upgraded'] = datetime.now().isoformat()
            
            # 记录升级历史
            upgrade_record = {
                'from_version': current_version,
                'to_version': latest_version,
                'upgraded_at': datetime.now().isoformat(),
                'backup_info': backup_info,
                'status': 'success'
            }
            
            if 'upgrade_history' not in config:
                config['upgrade_history'] = []
            config['upgrade_history'].append(upgrade_record)
            
            self.save_config(config)
            
            # 4. 验证升级结果
            self.verify_upgrade(latest_version)
            
            logger.info(f"脚本升级成功，已从版本 {current_version} 升级到 {latest_version}")
            return True
            
        except Exception as e:
            logger.error(f"脚本升级失败: {str(e)}")
            import traceback
            traceback.print_exc()
            
            # 尝试恢复备份
            self.restore_from_backup(backup_info)
            return False
    
    def backup_scripts(self):
        """备份当前脚本"""
        logger.info("备份当前脚本...")
        
        config = self.load_config()
        scripts_to_backup = config.get('scripts_to_upgrade', [])
        backup_info = {}
        
        backup_dir = os.path.join(self.backups_dir, f"backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}")
        os.makedirs(backup_dir)
        
        for script_name in scripts_to_backup:
            script_path = os.path.join(self.scripts_dir, script_name)
            if os.path.exists(script_path):
                backup_path = os.path.join(backup_dir, script_name)
                shutil.copy2(script_path, backup_path)
                
                # 计算文件哈希值
                file_hash = self.calculate_file_hash(script_path)
                backup_info[script_name] = {
                    'original_path': script_path,
                    'backup_path': backup_path,
                    'file_hash': file_hash
                }
                
                logger.info(f"已备份脚本: {script_name} 到 {backup_path}")
            else:
                logger.warning(f"脚本文件不存在，跳过备份: {script_name}")
        
        logger.info(f"脚本已备份到目录: {backup_dir}")
        backup_info['backup_dir'] = backup_dir
        return backup_info
    
    def calculate_file_hash(self, file_path):
        """计算文件哈希值"""
        hash_sha256 = hashlib.sha256()
        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                hash_sha256.update(chunk)
        return hash_sha256.hexdigest()
    
    def restore_from_backup(self, backup_info):
        """从备份恢复脚本"""
        logger.info("尝试从备份恢复脚本...")
        
        if not backup_info or 'backup_dir' not in backup_info:
            logger.error("没有找到有效的备份信息")
            return False
        
        backup_dir = backup_info['backup_dir']
        
        if not os.path.exists(backup_dir):
            logger.error(f"备份目录不存在: {backup_dir}")
            return False
        
        # 恢复所有脚本
        for script_name, info in backup_info.items():
            if script_name != 'backup_dir':
                backup_path = info.get('backup_path')
                original_path = info.get('original_path')
                
                if backup_path and os.path.exists(backup_path):
                    try:
                        shutil.copy2(backup_path, original_path)
                        logger.info(f"已从备份恢复脚本: {script_name}")
                    except Exception as e:
                        logger.error(f"恢复脚本 {script_name} 失败: {str(e)}")
        
        logger.info("脚本恢复完成")
        return True
    
    def download_and_install_scripts(self, version):
        """下载并安装最新脚本"""
        logger.info(f"下载并安装脚本版本 {version}...")
        
        config = self.load_config()
        scripts_to_upgrade = config.get('scripts_to_upgrade', [])
        
        for script_name in scripts_to_upgrade:
            script_path = os.path.join(self.scripts_dir, script_name)
            
            try:
                # 模拟下载最新脚本
                # script_url = f'https://api.example.com/scripts/{version}/{script_name}'
                # response = requests.get(script_url, timeout=30)
                # response.raise_for_status()
                # 
                # with open(script_path, 'wb') as f:
                #     f.write(response.content)
                
                # 模拟更新脚本内容（添加版本信息）
                if os.path.exists(script_path):
                    with open(script_path, 'r') as f:
                        content = f.read()
                    
                    # 在文件开头添加或更新版本信息
                    version_comment = f'#!/usr/bin/env python3\n# -*- coding: utf-8 -*-\n"""\n{script_name}\n版本: {version}\n最后更新: {datetime.now().isoformat()}\n"""\n'
                    
                    # 替换现有的版本信息或添加到开头
                    if '# -*- coding: utf-8 -*-' in content:
                        lines = content.split('\n')
                        new_content = []
                        version_found = False
                        
                        for line in lines:
                            if '# -*- coding: utf-8 -*-' in line:
                                new_content.append(line)
                                new_content.append('')
                                new_content.append(f'"""')
                                new_content.append(f'{script_name}')
                                new_content.append(f'版本: {version}')
                                new_content.append(f'最后更新: {datetime.now().isoformat()}')
                                new_content.append(f'"""')
                                version_found = True
                            elif '"""' in line and not version_found:
                                continue
                            elif not line.strip() and not version_found:
                                continue
                            else:
                                new_content.append(line)
                        
                        content = '\n'.join(new_content)
                    else:
                        content = version_comment + content
                    
                    with open(script_path, 'w') as f:
                        f.write(content)
                    
                    logger.info(f"已更新脚本: {script_name} 到版本 {version}")
                else:
                    # 新建脚本文件
                    with open(script_path, 'w') as f:
                        f.write(f'#!/usr/bin/env python3\n# -*- coding: utf-8 -*-\n"""\n{script_name}\n版本: {version}\n最后更新: {datetime.now().isoformat()}\n"""\n\n')
                    logger.info(f"已创建新脚本: {script_path}")
                    
                    # 设置可执行权限
                    os.chmod(script_path, 0o755)
                    
            except Exception as e:
                logger.error(f"下载并安装脚本 {script_name} 失败: {str(e)}")
                raise
        
        logger.info(f"脚本版本 {version} 安装完成")
    
    def verify_upgrade(self, version):
        """验证升级结果"""
        logger.info(f"验证脚本升级结果，版本: {version}")
        
        config = self.load_config()
        scripts_to_verify = config.get('scripts_to_upgrade', [])
        
        for script_name in scripts_to_verify:
            script_path = os.path.join(self.scripts_dir, script_name)
            
            # 检查脚本文件是否存在
            if os.path.exists(script_path):
                logger.info(f"脚本 {script_name} 存在，验证通过")
                
                # 检查脚本是否可执行
                if os.access(script_path, os.X_OK):
                    logger.info(f"脚本 {script_name} 可执行，验证通过")
                else:
                    # 尝试设置可执行权限
                    try:
                        os.chmod(script_path, 0o755)
                        logger.info(f"已设置脚本 {script_name} 可执行权限")
                    except Exception as e:
                        logger.error(f"设置脚本 {script_name} 可执行权限失败: {str(e)}")
            else:
                logger.error(f"脚本 {script_name} 不存在，验证失败")
                raise FileNotFoundError(f"脚本 {script_name} 不存在")
        
        logger.info("脚本升级验证全部通过")
    
    def manual_upgrade(self):
        """手动触发升级"""
        logger.info("手动触发脚本升级...")
        return self.run_upgrade()


def main():
    """主函数"""
    upgrader = AutoScriptUpgrader()
    
    # 启动监控线程
    monitor_thread = threading.Thread(target=upgrader.start_upgrade_monitor, args=(86400,))
    monitor_thread.daemon = True
    monitor_thread.start()
    
    logger.info("脚本自动升级系统已启动，按Ctrl+C停止")
    
    try:
        # 主线程保持运行
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        logger.info("收到停止信号")
    finally:
        upgrader.stop()
        monitor_thread.join(timeout=5)


if __name__ == "__main__":
    main()
