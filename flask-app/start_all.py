#!/usr/bin/env python3
"""
MTSCOS AI系统主启动脚本
用于启动所有服务并实现后台常驻
"""

import os
import sys
import logging
import time
import daemon
from daemon import pidfile

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# 设置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('start_all.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# 导入服务管理器
from app.services.service_manager import service_manager

def main():
    """主函数"""
    logger.info("开始启动MTSCOS AI系统...")
    
    try:
        # 启动服务管理器
        service_manager.start()
        logger.info("服务管理器启动成功")
        
        # 等待服务启动
        logger.info("等待服务启动...")
        time.sleep(10)
        
        # 检查服务状态
        status = service_manager.get_all_service_status()
        logger.info("服务启动状态:")
        for service_name, service_info in status.items():
            logger.info(f"  - {service_info['name']}: {service_info['status']}")
        
        # 保持运行
        logger.info("MTSCOS AI系统启动完成，进入后台运行状态...")
        while True:
            time.sleep(60)
            # 定期检查服务状态
            status = service_manager.get_all_service_status()
            running_count = sum(1 for s in status.values() if s['status'] == 'running')
            logger.debug(f"当前运行的服务数量: {running_count}/{len(status)}")
            
    except KeyboardInterrupt:
        logger.info("接收到中断信号，正在停止服务...")
    except Exception as e:
        logger.error(f"启动过程中发生错误: {str(e)}")
    finally:
        # 停止服务管理器
        try:
            service_manager.stop()
            logger.info("服务管理器已停止")
        except Exception as e:
            logger.error(f"停止服务管理器时发生错误: {str(e)}")

if __name__ == '__main__':
    # 检查是否以守护进程方式运行
    if len(sys.argv) > 1 and sys.argv[1] == '--daemon':
        # 以守护进程方式运行
        logger.info("以守护进程方式启动MTSCOS AI系统...")
        
        # 守护进程配置
        pid_file = pidfile.TimeoutPIDLockFile('start_all.pid')
        
        with daemon.DaemonContext(
            working_directory=os.path.dirname(os.path.abspath(__file__)),
            pidfile=pid_file,
            stdout=open('start_all.stdout', 'w+'),
            stderr=open('start_all.stderr', 'w+'),
        ):
            main()
    else:
        # 直接运行
        main()
