# -*- coding: utf-8 -*-
#!/usr/bin/env python3
"""
容器管理器 - 负责协调所有容器的初始化和管理
"""

import time
import threading
from typing import Dict, Any
from app.utils.logging import logger
from app.containers.login_container import login_container
from app.containers.user_container import user_container
from app.containers.connector_container import connector_container
import logging


class ContainerManager:
    """容器管理器类 - 负责协调所有容器的初始化和管理"""

    def __init__(self):
        self.manager_id = f"container_manager_{id(self)}"
        self.name = "容器管理器"
        self.description = "负责协调所有容器的初始化和管理"

        self.config = {
            "enabled": True,
            "ai_monitoring_enabled": True,
            "health_check_interval": 60,
            "auto_heal_enabled": True
        }

        self.containers = {
            "login_container": login_container,
            "user_container": user_container,
            "connector_container": connector_container
        }

        self.stats = {
            "total_containers": len(self.containers),
            "active_containers": 0,
            "container_status": {},
            "last_health_check": 0,
            "health_check_results": {}
        }

        self.health_check_thread = None

        self._initialize_containers()
        self._start_health_check()

        logger.info(f"✓ 容器管理器初始化成功: {self.manager_id}")

    def _initialize_containers(self):
        """初始化所有容器"""
        try:
            logger.info(f"🔧 初始化容器...")

            active_count = 0
            for container_name, container in self.containers.items():
                try:
                    status = container.get_status()
                    if status["status"] == "running":
                        active_count += 1
                    self.stats["container_status"][container_name] = status["status"]
                except Exception as e:
                    logger.error(f"❌ 检查容器 {container_name} 状态出错: {str(e)}")
                    self.stats["container_status"][container_name] = "error"

            self.stats["active_containers"] = active_count
            self.stats["last_updated"] = time.time()

            logger.info(f"✓ 容器初始化完成: 共 {len(self.containers)} 个容器,活跃容器: {active_count}")
        except Exception as e:
            logger.error(f"❌ 初始化容器出错: {str(e)}")

    def _start_health_check(self):
        """启动健康检查线程"""
        if self.config["health_check_interval"] > 0:
            self.health_check_thread = threading.Thread(target=self._health_check_thread_func, daemon=True)
            self.health_check_thread.start()
            logger.info(f"✓ 健康检查线程已启动,检查间隔: {self.config['health_check_interval']}秒")

    def _health_check_thread_func(self):
        """健康检查线程函数"""
        while True:
            time.sleep(self.config["health_check_interval"])
            self._perform_health_check()

    def _perform_health_check(self):
        """执行健康检查"""
        try:
            logger.info("🔍 执行容器健康检查...")

            results = {}
            for container_name, container in self.containers.items():
                try:
                    status = container.get_status()
                    results[container_name] = {
                        "status": status["status"],
                        "last_checked": time.time()
                    }

                    if status["status"] != "running" and self.config["auto_heal_enabled"]:
                        logger.warning(f"⚠️  容器 {container_name} 状态异常, 尝试自动修复...")
                except Exception as e:
                    results[container_name] = {
                        "status": "error",
                        "last_checked": time.time(),
                        "error": str(e)
                    }
                    logger.error(f"❌ 检查容器 {container_name} 健康出错: {str(e)}")

            self.stats["health_check_results"] = results
            self.stats["active_containers"] = sum(1 for status in results.values() if status["status"] == "running")

        except Exception as e:
            logger.error(f"❌ 执行健康检查出错: {str(e)}")

    def get_container(self, container_name: str):
        """获取指定容器"""
        return self.containers.get(container_name)

    def get_status(self) -> Dict[str, Any]:
        """获取容器管理器状态"""
        return {
            "status": "running",
            "manager_id": self.manager_id,
            "name": self.name,
            "stats": self.stats
        }

    def _cleanup(self):
        """清理资源"""
        try:
            if self.health_check_thread and self.health_check_thread.is_alive():
                self.health_check_thread = None
        except Exception as e:
            logger.error(f"❌ 清理容器管理器资源出错: {str(e)}")

    def __del__(self):
        self._cleanup()


container_manager = ContainerManager()
