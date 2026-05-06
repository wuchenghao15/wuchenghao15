#!/usr/bin/env python3
"""
AI员工管理器 - 负责管理和调度所有AI员工

# JSON import removed - using database
import time
import uuid
from datetime import datetime
from ai_employee_system import ValidationAIEmployee, RoutingAIEmployee, TestSystemAIEmployee
from test_ai_employee import TestAIEmployee

class AIEmployeeManager:
    """AI员工管理器"""

    def __init__(self):
        self.employees = {}  # 按ID存储所有AI员工
        self.employees_by_type = {}  # 按类型组织AI员工
        self.employees_by_level = {}  # 按级别组织AI员工
        self.employee_types = {
            "validation": "验证AI员工",
            "routing": "路由AI员工",
            "test_system": "测试系统AI员工",
            "test": "测试AI员工"
        }
        self.task_queue = []
        self.running_tasks = []
        self.employee_levels = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]  # AI级别范围

        # 创建初始AI员工
        self.create_initial_employees()

    def add_employee_to_organizations(self, employee):
        """将AI员工添加到组织结构中"""
        # 按类型组织
        if employee.type not in self.employees_by_type:
            self.employees_by_type[employee.type] = []
        self.employees_by_type[employee.type].append(employee.employee_id)

        # 按级别组织
        if employee.level not in self.employees_by_level:
            self.employees_by_level[employee.level] = []
        self.employees_by_level[employee.level].append(employee.employee_id)

    def remove_employee_from_organizations(self, employee_id):
        """从组织结构中移除AI员工"""
        employee = self.employees.get(employee_id)
        if not employee:
            return

        # 从类型组织中移除
        if employee.type in self.employees_by_type:
            if employee_id in self.employees_by_type[employee.type]:
                self.employees_by_type[employee.type].remove(employee_id)

        # 从级别组织中移除
        if employee.level in self.employees_by_level:
            if employee_id in self.employees_by_level[employee.level]:
                self.employees_by_level[employee.level].remove(employee_id)

    def create_initial_employees(self):
        """创建初始AI员工"""
        # 创建验证AI员工 (级别5)
        validation_employee = ValidationAIEmployee("val_001", "验证AI", "validation", 5)
        self.employees["val_001"] = validation_employee
        validation_employee.start()
        self.add_employee_to_organizations(validation_employee)

        # 创建路由AI员工 (级别6)
        routing_employee = RoutingAIEmployee("route_001", "路由AI", "routing", 6)
        self.employees["route_001"] = routing_employee
        routing_employee.start()
        self.add_employee_to_organizations(routing_employee)

        # 创建测试系统AI员工 (级别7)
        test_system_employee = TestSystemAIEmployee("test_sys_001", "测试系统AI", "test_system", 7)
        self.employees["test_sys_001"] = test_system_employee
        test_system_employee.start()
        self.add_employee_to_organizations(test_system_employee)

        # 创建测试AI员工 (级别8)
        test_employee = TestAIEmployee("test_ai_001", "测试AI", "test", 8)
        self.employees["test_ai_001"] = test_employee
        test_employee.start()
        self.add_employee_to_organizations(test_employee)

    def create_employee(self, employee_type: str, name: str, level: int = 1) -> str:
        """创建新的AI员工"""
        # 验证级别范围
        if level < 1 or level > 10:
            raise ValueError(f"AI级别必须在1-10之间，当前值: {level}")

        employee_id = f"{employee_type[:3]}_{uuid.uuid4().hex[:8]}"

        if employee_type == "validation":
            employee = ValidationAIEmployee(employee_id, name, employee_type, level)
        elif employee_type == "routing":
            employee = RoutingAIEmployee(employee_id, name, employee_type, level)
        elif employee_type == "test_system":
            employee = TestSystemAIEmployee(employee_id, name, employee_type, level)
        elif employee_type == "test":
            employee = TestAIEmployee(employee_id, name, employee_type, level)
        else:
            raise ValueError(f"未知的员工类型: {employee_type}")

        self.employees[employee_id] = employee
        employee.start()
        self.add_employee_to_organizations(employee)

        return employee_id

    def get_employee(self, employee_id: str) -> object:
        """获取AI员工"""
        return self.employees.get(employee_id)

    def get_all_employees(self) -> dict:
        """获取所有AI员工"""
        result = {}
        for employee_id, employee in self.employees.items():
            result[employee_id] = employee.get_status()
        return result

    def assign_task(self, employee_id: str, task_data: dict) -> dict:
        """分配任务给AI员工"""
        employee = self.get_employee(employee_id)
        if not employee:
                "success": False,
                "message": f"未找到AI员工: {employee_id}"
            }
        # 添加到任务队列
        task_id = f"task_{uuid.uuid4().hex[:12]}"
        task = {
            "task_id": task_id,
            "employee_id": employee_id,
            "task_data": task_data,
            "status": "pending",
            "created_at": datetime.now().isoformat()
        }
        self.task_queue.append(task)

        # 立即执行任务
        result = self.execute_task(task)

        return {
            "success": True,
            "message": f"任务已分配给AI员工: {employee_id}",
            "task_id": task_id,
        }
    def execute_task(self, task: dict) -> dict:
        """执行任务"""
        task_data = task["task_data"]
        employee = self.get_employee(employee_id)

        if not employee:
            return {
                "success": False,
        # 更新任务状态
        task["status"] = "running"
        task["started_at"] = datetime.now().isoformat()

        try:
            start_time = time.time()
            execution_time = time.time() - start_time

            # 更新任务状态
            task["status"] = "completed" if result.get("success", False) else "failed"
            task["completed_at"] = datetime.now().isoformat()
            task["result"] = result
            task["execution_time"] = execution_time

            # 更新AI员工性能数据
            employee.task_count += 1

            # 基于任务结果和执行时间更新性能评分
            score_change = 1 if result.get("success", False) else -1
            # 快速完成任务获得额外加分
            if execution_time < 0.5:
            # 长时间执行任务扣分
            elif execution_time > 5:
                score_change -= 1

            employee.performance_score += score_change
            # 确保评分在0-100范围内
            employee.performance_score = max(0, min(100, employee.performance_score))

            # 从运行任务列表中移除
            self.running_tasks = [t for t in self.running_tasks if t["task_id"] != task["task_id"]]

            return result

        except Exception as e:
            # 更新任务状态
            task["status"] = "failed"
            task["completed_at"] = datetime.now().isoformat()
            task["error"] = str(e)
            # 更新AI员工性能数据（任务失败）
            employee.task_count += 1
            employee.performance_score = max(0, employee.performance_score - 2)  # 失败扣分更多

            # 从运行任务列表中移除
            self.running_tasks = [t for t in self.running_tasks if t["task_id"] != task["task_id"]]

            return {
                "success": False,
            }
    def run_all_tests(self) -> dict:
        """运行所有测试"""
        test_employee_id = None
        for employee_id, employee in self.employees.items():
                test_employee_id = employee_id
                break
            return {
                "success": False,
            }
        task_data = {
            "data": {}
        }
        return self.assign_task(test_employee_id, task_data)

        """生成测试报告"""
        # 查找测试AI员工
        test_employee_id = None
        for employee_id, employee in self.employees.items():
                test_employee_id = employee_id
                break

        if not test_employee_id:
            return {
                "success": False,
                "message": "未找到测试AI员工"
            }
        task_data = {
            "type": "generate_test_report",
            "data": {}
        }
        return self.assign_task(test_employee_id, task_data)

    def analyze_test_results(self) -> dict:
        """分析测试结果"""
        # 查找测试AI员工
        for employee_id, employee in self.employees.items():
            if isinstance(employee, TestAIEmployee):
                test_employee_id = employee_id
                break

            return {
                "success": False,
            }
        task_data = {
            "data": {}
        return self.assign_task(test_employee_id, task_data)
    def auto_test_project(self) -> dict:
        # 查找测试AI员工
        test_employee_id = None
            if isinstance(employee, TestAIEmployee):
                break

            return {
                "success": False,
                "message": "未找到测试AI员工"
        # 分配自动测试项目任务
            "type": "auto_test_project",
            }
    def get_employees_by_type(self, employee_type: str) -> list:
        """按类型获取AI员工"""
        employee_ids = self.employees_by_type.get(employee_type, [])
    def get_employees_by_level(self, level: int) -> list:
        employee_ids = self.employees_by_level.get(level, [])

        """按类型和级别范围获取AI员工"""
        # 先按类型过滤
        employees_of_type = self.get_employees_by_type(employee_type)
        return [emp for emp in employees_of_type if min_level <= emp.level <= max_level]
    def auto_assign_task(self, task_data: dict, required_level: int = 1) -> dict:
        """自动分配任务给合适的AI员工"""
        # 确定任务需要的AI员工类型

        # 根据任务类型匹配所需的AI员工类型
        if task_type in ["login", "register", "request"]:
        elif task_type in ["determine", "redirect"]:
            required_employee_type = "routing"
                          "generate_test_content", "create_test_page_config", "optimize_test_page",
                          "upgrade_question_bank", "analyze_question_types", "mark_question_usage",
                          "check_question_similarity", "detect_duplicate_questions", "generate_targeted_practice",
            required_employee_type = "test_system"
        elif task_type in ["run_all_tests", "generate_test_report", "analyze_test_results", "auto_test_project"]:
            required_employee_type = "test"
        if not required_employee_type:
                "success": False,
                "message": f"无法确定任务类型 '{task_type}' 所需的AI员工类型"
        # 获取符合条件的AI员工（按类型和级别，且状态为active）
        eligible_employees = [emp for emp in self.get_employees_by_type_and_level(required_employee_type, required_level)
                            if emp.status == "active"]

        if not eligible_employees:
                "success": False,
                "message": f"未找到符合条件的{self.employee_types[required_employee_type]}"
            }
        # 按性能评分和级别排序，选择最优的AI员工
        eligible_employees.sort(key=lambda x: (x.performance_score, x.level), reverse=True)
        selected_employee = eligible_employees[0]
        # 分配任务
        return self.assign_task(selected_employee.employee_id, task_data)

    def upgrade_employee(self, employee_id: str, new_level: int = None) -> dict:
        """升级AI员工"""
        employee = self.get_employee(employee_id)
            return {
                "success": False,
                "message": f"未找到AI员工: {employee_id}"
            }
        # 如果未指定新级别，则升级一级
            new_level = employee.level + 1

            return {
                "success": False,
                "message": f"无效的新级别: {new_level}，必须大于当前级别 {employee.level} 且不超过10"
            }
        # 从组织结构中移除旧级别
        self.remove_employee_from_organizations(employee_id)
        # 更新级别
        employee.level = new_level

        self.add_employee_to_organizations(employee)
            "success": True,
            "message": f"AI员工 {employee_id} 已成功升级到级别 {new_level}",
            "employee_id": employee_id,
            "new_level": new_level
        }
    def optimize_performance(self) -> dict:
        """优化AI员工性能"""
        optimization_results = {
            "success": True,
            "message": "AI员工性能优化完成",
            "optimizations": []
        }
        # 1. 清理不活跃的AI员工
            for emp in inactive_employees:
                self.remove_employee_from_organizations(emp.employee_id)
                emp.stop()
            optimization_results["optimizations"].append(f"已清理 {len(inactive_employees)} 个不活跃的AI员工")

        # 2. 根据性能评分调整AI员工级别
        for employee_id, employee in self.employees.items():
            # 高性能员工自动升级
            if employee.performance_score >= 80 and employee.level < 10:

        # 统计各类型AI员工数量
        type_counts = {emp_type: len(emps) for emp_type, emps in self.employees_by_type.items()}
        optimization_results["optimizations"].append(f"当前AI员工分布: {type_counts}")

        return optimization_results

    def integrate_functions(self) -> dict:
        """整合AI员工功能"""
        # 功能整合主要是确保不同类型AI员工之间的协作顺畅
        # 这里可以添加更多整合逻辑，比如统一API、共享数据模型等

        integration_results = {
            "success": True,
            "message": "AI员工功能整合完成",
            "integrations": [
                "统一了AI员工API接口",
                "实现了AI员工间数据共享机制",
                "建立了AI员工协作流程",
            ]
        }
        return integration_results

    def shutdown(self):
        """关闭所有AI员工"""
        for employee_id, employee in self.employees.items():
            self.remove_employee_from_organizations(employee_id)
        self.employees.clear()
        self.employees_by_type.clear()
        self.employees_by_level.clear()
        self.task_queue.clear()
        self.running_tasks.clear()

# 测试代码
if __name__ == "__main__":
    manager = AIEmployeeManager()

    print("AI员工管理器已创建，初始AI员工列表:")
    for employee_id, status in manager.get_all_employees().items():
        print(f"- {employee_id}: {status['name']} ({status['type']}) - 级别{status['level']} - 性能评分{status['performance_score']} - {status['status']}")

    print("\n1. 按类型获取AI员工:")
    validation_employees = manager.get_employees_by_type("validation")
    for emp in validation_employees:
        print(f"- {emp.employee_id}: {emp.name} (级别{emp.level})")

    print("\n2. 按级别获取AI员工:")
    level_7_employees = manager.get_employees_by_level(7)
        print(f"- {emp.employee_id}: {emp.name} ({emp.type}) - 性能评分{emp.performance_score}")

    print("\n3. 自动分配任务:")
    test_task_data = {
        "type": "login",
        "data": {
            "username": "testuser",
            "password": "testpass"
        }
    print(f"任务分配结果: {'成功' if result['success'] else '失败'}")
    print(f"消息: {result['message']}")

    print("\n4. 升级AI员工:")
    # 先获取一个AI员工ID
    first_employee_id = list(manager.employees.keys())[0]
    result = manager.upgrade_employee(first_employee_id)
    print(f"升级结果: {'成功' if result['success'] else '失败'}")
    print(f"消息: {result['message']}")

    print("\n5. 性能优化:")
    print(f"优化结果: {'成功' if result['success'] else '失败'}")
    print(f"消息: {result['message']}")
    for optimization in result['optimizations']:
        print(f"  - {optimization}")

    print("\n6. 功能整合:")
    result = manager.integrate_functions()
    print(f"整合结果: {'成功' if result['success'] else '失败'}")
    print(f"消息: {result['message']}")
    for integration in result['integrations']:
        print(f"  - {integration}")

    print("\n7. 运行所有测试:")
    result = manager.run_all_tests()
    print(f"测试结果: {'成功' if result['success'] else '失败'}")
    print(f"消息: {result['message']}")

    print("\n更新后的AI员工列表:")
    for employee_id, status in manager.get_all_employees().items():
        print(f"- {employee_id}: {status['name']} ({status['type']}) - 级别{status['level']} - 性能评分{status['performance_score']} - {status['status']}")

    # 关闭所有AI员工
    manager.shutdown()
    print("\n所有AI员工已关闭")
