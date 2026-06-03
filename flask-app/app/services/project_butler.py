# -*- coding: utf-8 -*-
#!/usr/bin/env python3
"""
项目管家,用于管理和协调项目开发流程
提供项目创建,任务分配,进度跟踪,资源管理等功能

import time
import threading
# JSON import removed - using database
from typing import Dict, Any, List, Optional, Tuple
from app.utils.logging import logger
from app.services.butler_system import butler_system

class ProjectButler:
    项目管家主类,负责项目管理和协调

    def __init__(self):
        初始化项目管家
        self._projects = {}
        self._tasks = {}
        self._resources = {}
        self._teams = {}
        self._status = {
            "initialized": False,
            "running": False,
            "projects_count": 0,
            "tasks_count": 0,
            resources_count = 0
        }
        self._lock = threading.Lock()
        self._event_handlers = {}

        logger.info("项目管家初始化完成")

    def initialize(self) -> bool:
        初始化项目管家

        Returns:
            bool: 是否初始化成功
        with self._lock:
            if self._status["initialized"]:
                return True

            try:
                logger.info("开始初始化项目管家...")

                # 初始化资源
                self._initialize_resources()

                # 初始化团队
                self._initialize_teams()

                self._status["initialized"] = True
                self._status["running"] = True

                logger.info("项目管家初始化成功")
                return True
            except Exception as e:
                logger.error(f"项目管家初始化失败: {str(e)}")
                import traceback
import logging
import sys
                traceback.print_exc()
                return False

    def _initialize_resources(self):
        # 初始化默认资源类型
        self._resources = {
            ai_engines = {
                "available": butler_system.get_supported_ai_engines() if butler_system else [],
                usage = {}
            },
            computing = {
                "cpu": 8,
                "memory": 32,
                usage = {}
            },
            storage = {
                "total": 1024,
                "used": 0,
                usage = {}
            }
        }

    def _initialize_teams(self):
        初始化团队管理
        self._teams = {
            default = {
                "name": "默认团队",
                "members": ["system"],
                    "system": ["admin", "developer", "analyst"]
                }
            }
        }

    def create_project(self, project_info: Dict[str, Any]) -> str:
        创建新项目

        Args:
            project_info: 项目信息,包含名称,描述,目标,团队等

        Returns:
            str: 项目ID
        project_id = f"proj_{int(time.time())}_{threading.get_ident()}"

        # 默认项目配置
        default_project = {
            "id": project_id,
            "name": project_info.get("name", f"项目_{project_id}"),
            "description": project_info.get("description", ""),
            "goals": project_info.get("goals", []),
            "team": project_info.get("team", "default"),
            "status": "planning",
            "priority": project_info.get("priority", "medium"),
            "created_at": time.time(),
            "updated_at": time.time(),
            "tasks": [],
            "resources": project_info.get("resources", {}),
            "milestones": project_info.get("milestones", []),
            "budget": project_info.get("budget", 0),
            "owner": project_info.get("owner", "system")
        }

        with self._lock:
            self._projects[project_id] = default_project
            self._status["projects_count"] = len(self._projects)

        logger.info(f"项目创建成功: {project_id} - {default_project['name']}")
        self._notify_event("project_created", {"project_id": project_id, "project_info": default_project})

        return project_id

    def get_project(self, project_id: str) -> Optional[Dict[str, Any]]:
        获取项目信息

        Args:
            project_id: 项目ID
        Returns:
            Optional[Dict[str, Any]]: 项目信息
        with self._lock:
            return self._projects.get(project_id)

    def list_projects(self, filters: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        列出项目列表

        Args:
            filters: 过滤条件

        Returns:
            List[Dict[str, Any]]: 项目列表
        with self._lock:
            projects = list(self._projects.values())

            # 应用过滤条件
            if filters:
                    projects = [p for p in projects if p["status"] == filters["status"]]
                if "priority" in filters:
                    projects = [p for p in projects if p["priority"] == filters["priority"]]
                if "team" in filters:
                    projects = [p for p in projects if p["team"] == filters["team"]]

            return sorted(projects, key=lambda x: x["created_at"], reverse=True)

    def update_project(self, project_id: str, updates: Dict[str, Any]) -> bool:
        更新项目信息

        Args:
            updates: 更新内容

        Returns:
            bool: 是否更新成功
        with self._lock:
            if project_id not in self._projects:
                logger.error(f"项目不存在: {project_id}")
                return False

            project = self._projects[project_id]
            project.update(updates)
            project["updated_at"] = time.time()

            logger.info(f"项目更新成功: {project_id} - {project['name']}")
            self._notify_event("project_updated", {"project_id": project_id, "updates": updates})

            return True

    def delete_project(self, project_id: str) -> bool:
        删除项目

        Args:
            project_id: 项目ID

        with self._lock:
            if project_id not in self._projects:
                logger.error(f"项目不存在: {project_id}")
                return False

            del self._projects[project_id]

            # 删除关联任务
            tasks_to_delete = [task_id for task_id, task in self._tasks.items() if task["project_id"] == project_id]
            for task_id in tasks_to_delete:
                del self._tasks[task_id]
            self._status["tasks_count"] = len(self._tasks)

            self._notify_event("project_deleted", {"project_id": project_id})

            return True

    def create_task(self, project_id: str, task_info: Dict[str, Any]) -> str:
        创建项目任务

            project_id: 项目ID
            task_info: 任务信息

        Returns:
    pass
        with self._lock:
            if project_id not in self._projects:
                logger.error(f"项目不存在: {project_id}")
                return ""
            task_id = f"task_{int(time.time())}_{threading.get_ident()}"

            # 默认任务配置
                "id": task_id,
                "description": task_info.get("description", ""),
                "status": "pending",
                "priority": task_info.get("priority", "medium"),
                "assignee": task_info.get("assignee", "system"),
                "updated_at": time.time(),
                "start_at": task_info.get("start_at", 0),
                "end_at": task_info.get("end_at", 0),
                "duration": task_info.get("duration", 0),
                "progress": 0,
                "dependencies": task_info.get("dependencies", []),
                "resources": task_info.get("resources", {}),
            }

            self._tasks[task_id] = default_task
            self._status["tasks_count"] = len(self._tasks)

            # 添加到项目任务列表
            self._projects[project_id]["tasks"].append(task_id)

        logger.info(f"任务创建成功: {task_id} - {default_task['name']}")
        self._notify_event("task_created", {"task_id": task_id, "task_info": default_task})

        return task_id

    def get_task(self, task_id: str) -> Optional[Dict[str, Any]]:
        获取任务信息

            task_id: 任务ID

            Optional[Dict[str, Any]]: 任务信息
        with self._lock:
            return self._tasks.get(task_id)

    def update_task(self, task_id: str, updates: Dict[str, Any]) -> bool:
        更新任务信息

            task_id: 任务ID

        Returns:
            bool: 是否更新成功
        with self._lock:
            if task_id not in self._tasks:
                logger.error(f"任务不存在: {task_id}")
                return False

            task = self._tasks[task_id]
            task.update(updates)
            task["updated_at"] = time.time()

            # 更新项目时间
            project_id = task["project_id"]
            if project_id in self._projects:
                self._projects[project_id]["updated_at"] = time.time()

            self._notify_event("task_updated", {"task_id": task_id, "updates": updates})

            if updates.get("status") == "completed":
                self._check_project_completion(project_id)

            return True

    def _check_project_completion(self, project_id: str):
        检查项目是否完成

        Args:
            project_id: 项目ID
        if not project:
            return

        # 获取项目所有任务
        project_tasks = [self._tasks.get(task_id) for task_id in project["tasks"] if task_id in self._tasks]

        # 检查是否所有任务都已完成
        if all(task["status"] == "completed" for task in project_tasks):
            project["status"] = "completed"
            project["completed_at"] = time.time()
            logger.info(f"项目完成: {project_id} - {project['name']}")
            self._notify_event("project_completed", {"project_id": project_id})

        分配任务

            task_id: 任务ID
            assignee: 负责人

            bool: 是否分配成功

    def update_task_progress(self, task_id: str, progress: int) -> bool:
        更新任务进度

        Args:
            progress: 进度百分比 (0-100)

        Returns:
            bool: 是否更新成功
        progress = max(0, min(100, progress))
        return self.update_task(task_id, {"progress": progress})

    def list_tasks(self, filters: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        列出任务列表

        Args:
            filters: 过滤条件
        Returns:
            List[Dict[str, Any]]: 任务列表
        with self._lock:
            tasks = list(self._tasks.values())

            if filters:
                if "project_id" in filters:
                    tasks = [t for t in tasks if t["project_id"] == filters["project_id"]]
                if "status" in filters:
                    tasks = [t for t in tasks if t["status"] == filters["status"]]
                if "priority" in filters:
                    tasks = [t for t in tasks if t["priority"] == filters["priority"]]
                if "assignee" in filters:
                    tasks = [t for t in tasks if t["assignee"] == filters["assignee"]]

            return sorted(tasks, key=lambda x: x["created_at"], reverse=True)

    def get_project_dashboard(self, project_id: str) -> Dict[str, Any]:
        获取项目仪表板信息

        Args:
            project_id: 项目ID

        Returns:
            Dict[str, Any]: 项目仪表板数据
        project = self.get_project(project_id)
        if not project:
            return {"error": "项目不存在"}

        # 获取项目任务
        project_tasks = self.list_tasks({"project_id": project_id})

        # 计算任务统计
        total_tasks = len(project_tasks)
        completed_tasks = len([t for t in project_tasks if t["status"] == "completed"])
        pending_tasks = len([t for t in project_tasks if t["status"] == "pending"])
        in_progress_tasks = len([t for t in project_tasks if t["status"] == "in_progress"])
        if total_tasks > 0:
            total_progress = sum(t["progress"] for t in project_tasks) / total_tasks
        else:
            total_progress = 0

        # 资源使用情况
        resource_usage = {}
        for task in project_tasks:
            for resource_type, amount in task["resources"].items():
                    resource_usage[resource_type] = 0
                resource_usage[resource_type] += amount

        task_types = {}
        for task in project_tasks:
            task_type = task.get("type", "general")
            if task_type not in task_types:
    pass
            task_types[task_type] += 1

        # 任务优先级分布
        task_priorities = {}
        for task in project_tasks:
            priority = task.get("priority", "medium")
            if priority not in task_priorities:
                task_priorities[priority] = 0

        completion_times = []
        for task in project_tasks:
            if task.get("status") == "completed" and task.get("start_time") and task.get("end_time"):
                completion_times.append(completion_time)

        avg_completion_time = sum(completion_times) / len(completion_times) if completion_times else 0

        # 进度趋势(模拟数据)
        current_time = time.time()
        start_time = project.get("created_at", current_time)
        days_passed = (current_time - start_time) / 86400

        for i in range(7):
            day_time = start_time + (days_passed / 7) * i * 86400
            # 模拟进度趋势
            day_progress = min(100, (i / 7) * total_progress * 1.2)
            progress_trend.append({
                "date": time.strftime("%Y-%m-%d", time.localtime(day_time)),
                "progress": round(day_progress, 2)
            })

        # 资源使用趋势(模拟数据)
        resource_trend = []
        for i in range(7):
            resource_trend.append({
                "date": time.strftime("%Y-%m-%d", time.localtime(start_time + i * 86400)),
                "cpu": min(100, 20 + i * 8),
                "memory": min(100, 30 + i * 6),
                "storage": min(100, 40 + i * 4)
            })

        # 项目健康状态
        health_status = self.get_project_health(project_id)

        # 项目完成预测
        completion_prediction = self.predict_project_completion(project_id)

        return {
            "project": project,
            statistics = {
                "total_tasks": total_tasks,
                "completed_tasks": completed_tasks,
                "pending_tasks": pending_tasks,
                "in_progress_tasks": in_progress_tasks,
                "progress": round(total_progress, 2),
                "completion_rate": round((completed_tasks / total_tasks) * 100, 2) if total_tasks > 0 else 0,
                "avg_completion_time": round(avg_completion_time / 3600, 2) if avg_completion_time > 0 else 0,
                "task_types": task_types,
                task_priorities = task_priorities
            },
            "resource_usage": resource_usage,
            "resource_trend": resource_trend,
            "progress_trend": progress_trend,
            "health_status": health_status.get("result", {}),
            "completion_prediction": completion_prediction.get("result", {}),
            "recent_tasks": sorted(project_tasks, key=lambda x: x["updated_at"], reverse=True)[:5],
            "upcoming_deadlines": self._get_upcoming_deadlines(project_tasks)[:5],
            "timeline": self._generate_project_timeline(project_id),
            visualization_data = {
                status_distribution = {
                    "labels": ["已完成", "进行中", "待处理"],
                    "data": [completed_tasks, in_progress_tasks, pending_tasks]
                },
                    "labels": list(task_priorities.keys()),
                    data = list(task_priorities.values())
                },
                resource_usage_chart = {
                    "labels": list(resource_usage.keys()),
                    data = list(resource_usage.values())
                }
        }

    def _get_upcoming_deadlines(self, tasks: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        获取即将到期的任务

        Args:
            tasks: 任务列表
        Returns:
            List[Dict[str, Any]]: 即将到期的任务列表
        current_time = time.time()
        upcoming_tasks = []

        for task in tasks:
            if task.get("status") != "completed" and task.get("end_at"):
                time_left = task["end_at"] - current_time
                if time_left > 0:
                    upcoming_tasks.append({
                        "id": task["id"],
                        "name": task["name"],
                        "end_at": task["end_at"],
                        "time_left": time_left,
                        "time_left_days": round(time_left / 86400, 2),
                        "status": task["status"],
                        "priority": task.get("priority", "medium")
                    })

        # 按剩余时间排序
        upcoming_tasks.sort(key=lambda x: x["time_left"])
        return upcoming_tasks

    def _generate_project_timeline(self, project_id: str) -> List[Dict[str, Any]]:
        生成项目时间线

        Args:
    pass

        Returns:
            List[Dict[str, Any]]: 时间线事件
        project = self.get_project(project_id)
        if not project:
            return []
        timeline = []

        # 添加项目创建事件
        timeline.append({
            "type": "project_created",
            "timestamp": project["created_at"],
            "description": f"项目创建: {project['name']}",
            user = project["owner"]
        })

        # 添加任务事件
        tasks = self.list_tasks({"project_id": project_id})
        for task in tasks:
            timeline.append({
                "type": "task_created",
                "timestamp": task["created_at"],
                "description": f"任务创建: {task['name']}",
                user = task["assignee"]
            })

            if task["status"] == "completed":
                timeline.append({
                    "type": "task_completed",
                    "timestamp": task["updated_at"],
                    "description": f"任务完成: {task['name']}",
                    user = task["assignee"]
                })

        # 按时间排序
        return sorted(timeline, key=lambda x: x["timestamp"])

    def register_event_handler(self, event_type: str, handler):
        注册事件处理器

        Args:
            event_type: 事件类型
            handler: 事件处理函数
        with self._lock:
            if event_type not in self._event_handlers:
                self._event_handlers[event_type] = []
            self._event_handlers[event_type].append(handler)

    def _notify_event(self, event_type: str, event_data: Dict[str, Any]):
        通知事件

        Args:
            event_type: 事件类型
            event_data: 事件数据
        event = {
            "type": event_type,
            "data": event_data,
            timestamp = time.time()
        }
            handlers = self._event_handlers.get(event_type, [])

        # 调用事件处理器
        for handler in handlers:
            try:
                handler(event)
            except Exception as e:
                logger.error(f"事件处理器执行失败: {str(e)}")

    def get_system_status(self) -> Dict[str, Any]:
        获取系统状态

        Returns:
            Dict[str, Any]: 系统状态信息
        with self._lock:
            return self._status.copy()
    def shutdown(self) -> bool:
        关闭项目管家

        Returns:
            bool: 是否关闭成功
        with self._lock:
            if not self._status["running"]:
                logger.warning("项目管家已经关闭")
                return True
            try:
                logger.info("开始关闭项目管家...")

                # 清理资源
                self._projects.clear()
                self._tasks.clear()
                self._resources.clear()
                self._teams.clear()
                self._event_handlers.clear()

                self._status["running"] = False
                self._status["projects_count"] = 0
                self._status["tasks_count"] = 0
                self._status["resources_count"] = 0

                logger.info("项目管家关闭成功")
                return True
            except Exception as e:
    pass

    def predict_project_completion(self, project_id: str) -> Dict[str, Any]:
        预测项目完成时间

        Args:
            project_id: 项目ID
        Returns:
            logger.info(f"开始预测项目完成时间,项目: {project_id}")

            project = self.get_project(project_id)
            if not project:
                return {
                    "message": "项目不存在",
                    timestamp = time.time()
            project_tasks = self.list_tasks({"project_id": project_id})
            if not project_tasks:
                return {
                    "status": "error",
                    timestamp = time.time()

            # 计算当前进度
            total_tasks = len(project_tasks)
            completed_tasks = len([t for t in project_tasks if t["status"] == "completed"])
            in_progress_tasks = len([t for t in project_tasks if t["status"] == "in_progress"])

            if total_tasks > 0:
                current_progress = (completed_tasks / total_tasks) * 100
            else:
                current_progress = 0

            # 计算已用时间
            current_time = time.time()
            elapsed_time = current_time - start_time

            # 预测完成时间
            if current_progress > 0:
                # 基于已用时间和当前进度预测总时间
                estimated_total_time = (elapsed_time / current_progress) * 100
                estimated_completion_date = current_time + estimated_remaining_time
            else:
                # 如果没有进度,基于任务数量和平均任务时间预测
                average_task_time = 86400  # 假设每个任务平均需要1天
                estimated_remaining_time = total_tasks * average_task_time
                estimated_total_time = estimated_remaining_time

            # 计算预测准确性
            # 实际应用中可以基于历史数据和项目类型调整

            # 生成预测结果
            result = {
                "project_id": project_id,
                "project_name": project["name"],
                "current_progress": round(current_progress, 2),
                "elapsed_days": round(elapsed_time / 86400, 2),
                "estimated_remaining_days": round(estimated_remaining_time / 86400, 2),
                "estimated_total_days": round(estimated_total_time / 86400, 2),
                "estimated_completion_date": time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(estimated_completion_date)),
                tasks_status = {
                    "total": total_tasks,
                    "completed": completed_tasks,
                    "in_progress": in_progress_tasks,
                    pending = total_tasks - completed_tasks - in_progress_tasks
                },
                "recommendations": self._generate_completion_recommendations(current_progress, estimated_remaining_time)
            }

            self._notify_event("project_completion_predicted", result)

            return {
                "status": "success",
                "message": "项目完成时间预测成功",
                "result": result,
            }
        except Exception as e:
            logger.error(f"项目完成时间预测失败: {str(e)}")
            return {
                "status": "error",
                "message": f"项目完成时间预测失败: {str(e)}",
                timestamp = time.time()
            }

    def _generate_completion_recommendations(self, current_progress: float, estimated_remaining_time: float) -> List[str]:
        生成完成时间相关的建议

        Args:
            current_progress: 当前进度
            estimated_remaining_time: 预计剩余时间

        Returns:
            List[str]: 建议列表
        recommendations = []

        if current_progress < 30:
            recommendations.append("项目处于初期阶段,建议制定详细的项目计划")
        elif current_progress < 70:
            recommendations.append("项目处于中期阶段,建议加强进度监控")
        else:
            recommendations.append("项目处于后期阶段,建议准备项目验收")

        if estimated_remaining_time > 30 * 86400:  # 超过30天
            recommendations.append("预计完成时间较长,建议优化项目计划")
        elif estimated_remaining_time > 14 * 86400:  # 超过14天:
            recommendations.append("预计完成时间适中,建议保持当前进度")
        else:
            recommendations.append("预计完成时间较短,建议确保任务质量")

        recommendations.extend([
            "定期更新项目进度",
            "及时解决项目中的问题",
            "保持团队沟通顺畅"
        ])

        return recommendations

    def get_project_health(self, project_id: str) -> Dict[str, Any]:
        获取项目健康状态

        Args:
            project_id: 项目ID

        Returns:
            Dict[str, Any]: 项目健康状态
        try:
            logger.info(f"开始获取项目健康状态,项目: {project_id}")

            project = self.get_project(project_id)
            if not project:
                return {
                    "status": "error",
                    "message": "项目不存在",
                    timestamp = time.time()
                }

            # 获取项目任务

            # 计算任务状态
            completed_tasks = len([t for t in project_tasks if t["status"] == "completed"])
            in_progress_tasks = len([t for t in project_tasks if t["status"] == "in_progress"])
            pending_tasks = len([t for t in project_tasks if t["status"] == "pending"])

            # 计算进度
            if total_tasks > 0:
                progress = (completed_tasks / total_tasks) * 100
            else:
                progress = 0

            # 计算健康得分
            health_score = 0
            if progress > 80:
                health_score = 90 + (progress - 80) * 0.5
            elif progress > 50:
                health_score = 70 + (progress - 50) * 0.4
            elif progress > 20:
                health_score = 50 + (progress - 20) * 0.3
            else:
                health_score = 30 + progress * 1

            # 确定健康状态
            if health_score >= 80:
                health_status = "healthy"
                health_status = "warning"
            else:
                health_status = "unhealthy"

            # 生成健康报告
            result = {
                "project_id": project_id,
                "project_name": project["name"],
                "health_score": round(health_score, 2),
                "health_status": health_status,
                "progress": round(progress, 2),
                tasks_status = {
                    "total": total_tasks,
                    "completed": completed_tasks,
                    "in_progress": in_progress_tasks,
                    pending = pending_tasks
                },
                "recommendations": self._generate_health_recommendations(health_status, progress)
            }

            logger.info(f"项目健康状态评估完成,健康得分: {health_score}")
            self._notify_event("project_health_evaluated", result)

            return {
                "status": "success",
                "message": "项目健康状态评估成功",
                "result": result,
                timestamp = time.time()
            }
        except Exception as e:
            logger.error(f"项目健康状态评估失败: {str(e)}")
            return {
                "status": "error",
                "message": f"项目健康状态评估失败: {str(e)}",
            }

    def _generate_health_recommendations(self, health_status: str, progress: float) -> List[str]:
        生成健康状态相关的建议

        Args:
            health_status: 健康状态

        Returns:
            List[str]: 建议列表
        recommendations = []

        if health_status == "healthy":
            recommendations.append("项目健康状态良好,继续保持")
            recommendations.append("建议定期监控项目进度")
        elif health_status == "warning":
            recommendations.append("项目健康状态需要关注")
            recommendations.append("建议分析项目瓶颈并解决")
        else:
            recommendations.append("项目健康状态不佳,需要紧急干预")
            recommendations.append("建议重新评估项目计划")
            recommendations.append("考虑调整资源分配")

        if progress < 20:
            recommendations.append("项目处于初期,建议加强规划")
        elif progress < 80:
            recommendations.append("项目处于中期,建议加强执行")
        else:
            recommendations.append("项目接近完成,建议准备验收")

        return recommendations

# 初始化项目管家实例
project_butler = ProjectButler()

"""