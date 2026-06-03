# -*- coding: utf-8 -*-
#!/usr/bin/env python3
"""
AI员工基类 - 定义所有AI员工的基本接口和属性
"""

from abc import ABC, abstractmethod
from datetime import datetime
from typing import Dict, Any
from ai_brain_library import AIBrainLibrary

class AIEmployee(ABC):
    """AI员工基类"""

    def __init__(self, employee_id: str, name: str, employee_type: str, level: int = 1):
        self.employee_id = employee_id
        self.name = name
        self.type = employee_type
        self.level = level
        self.status = "inactive"
        self.created_at = datetime.now().isoformat()
        self.last_active = None
        self.performance_score = 0
        self.task_count = 0
        self.learning_enabled = True
        self.brain_library = AIBrainLibrary()
        self.id = employee_id

    def start(self):
        """启动AI员工"""
        self.status = "active"
        self.last_active = datetime.now().isoformat()
        print(f"[AI员工] 启动AI员工: {self.name} ({self.type})")

    def stop(self):
        """停止AI员工"""
        self.status = "inactive"
        print(f"[AI员工] 停止AI员工: {self.name} ({self.type})")

    @abstractmethod
    def process(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """处理数据"""
        pass

    def get_status(self) -> Dict[str, Any]:
        """获取AI员工状态"""
        return {
            "employee_id": self.employee_id,
            "name": self.name,
            "type": self.type,
            "level": self.level,
            "performance_score": self.performance_score,
            "task_count": self.task_count,
            "status": self.status,
            "created_at": self.created_at,
            "last_active": self.last_active,
            "learning_enabled": self.learning_enabled
        }

    def upgrade_self(self):
        """AI员工自我升级"""
        if self.status != "active":
            return {"success": False, "message": "AI员工未激活,无法升级"}

        try:
            upgrade_results = self.brain_library.upgrade_all_libraries()
            self.last_active = datetime.now().isoformat()

            return {
                "success": True,
                "message": f"AI员工 {self.employee_id} 自我升级完成",
                "upgrade_results": upgrade_results
            }
        except Exception as e:
            return {
                "success": False,
                "message": f"AI员工自我升级失败: {str(e)}"
            }

    def learn_from_data(self, data: Dict[str, Any]):
        """从数据中学习"""
        if not self.learning_enabled or self.status != "active":
            return {"success": False, "message": "学习功能未启用或AI员工未激活"}

        try:
            data_type = data.get("type", "unknown")
            learning_result = False
            if data_type in ["validation", "login", "register"]:
                learning_result = self.brain_library.learn_from_data(data, "knowledge")
            elif data_type in ["determine", "redirect"]:
                learning_result = self.brain_library.learn_from_data(data, "features")
            elif data_type in ["manage_parameters", "upload_data", "analyze_performance"]:
                learning_result = self.brain_library.learn_from_data(data, "capabilities")
            elif data_type in ["run_test", "run_all_tests", "generate_test_report"]:
                learning_result = self.brain_library.learn_from_data(data, "brain_map")
            else:
                learning_result = self.brain_library.learn_from_data(data, "knowledge")

            self.last_active = datetime.now().isoformat()

            return {
                "success": True,
                "message": f"AI员工 {self.employee_id} 从数据中学习完成"
            }
        except Exception as e:
            return {
                "success": False,
                "message": f"AI员工学习失败: {str(e)}"
            }

    def toggle_learning(self, enabled: bool):
        """切换学习功能"""
        self.learning_enabled = enabled
        self.last_active = datetime.now().isoformat()
        return {
            "success": True,
            "message": f"学习功能已{'启用' if enabled else '禁用'}"
        }
