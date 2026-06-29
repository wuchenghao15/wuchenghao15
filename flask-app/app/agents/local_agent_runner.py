# -*- coding: utf-8 -*-
"""
本地Agent运行器
作为独立进程启动Agent
"""

import os
import sys
import time
import json
import logging
from datetime import datetime

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))


def run_agent(agent_code, port):
    """运行Agent"""
    try:
        logger.info(f"启动Agent: {agent_code}, 端口: {port}")
        
        from app.agents.agent_executor import AgentExecutor
        
        executor = AgentExecutor(agent_code)
        executor.start()
        
        logger.info(f"Agent {agent_code} 执行器已启动")
        
        while True:
            time.sleep(1)
            
    except KeyboardInterrupt:
        logger.info(f"Agent {agent_code} 收到中断信号，正在停止...")
    except Exception as e:
        logger.error(f"Agent {agent_code} 运行出错: {e}")
        sys.exit(1)


if __name__ == '__main__':
    if len(sys.argv) < 3:
        logger.error("用法: python -m app.agents.local_agent_runner <agent_code> <port>")
        sys.exit(1)
    
    agent_code = sys.argv[1]
    port = int(sys.argv[2])
    
    run_agent(agent_code, port)