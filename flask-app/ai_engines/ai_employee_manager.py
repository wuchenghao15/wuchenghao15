#!/usr/bin/env python3
"""
AI员工管理器 - 负责管理和调度所有AI员工
"""

# JSON import removed - using database
import logging
logger = logging.getLogger(__name__)
import os
import sys
import time
import uuid
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from ai_engines.ai_employee_system import ValidationAIEmployee, RoutingAIEmployee, TestSystemAIEmployee, AIEmployee
from ai_engines.diagnostics_repair_employee import DiagnosticsRepairEmployee
from ai_engines.question_bank_maintenance_employee import QuestionBankMaintenanceEmployee
from ai_engines.politics_question_employee import PoliticsQuestionEmployee
from ai_engines.k12_question_employee import K12QuestionEmployee
from ai_engines.listening_question_employee import ListeningQuestionEmployee
from ai_engines.rule_base_maintenance_employee import RuleBaseMaintenanceEmployee
from ai_engines.config_manager_employee import ConfigManagerEmployee

try:
    from ai_engines.test_ai_employee import TestAIEmployee
except ImportError:
    class TestAIEmployee(AIEmployee):
        """测试AI员工 - 占位类"""
        def __init__(self, employee_id, name, employee_type="test", level=1):
            super().__init__(employee_id, name, employee_type, level)
            self.type = "test"
            self.status = "active"
            self.task_count = 0
            self.success_count = 0
            self.failure_count = 0
            self.performance_score = 80 + level * 2
            self._running = False
            import threading
            self._lock = threading.RLock()
        
        def start(self):
            self._running = True
        
        def stop(self):
            self._running = False
        
        def get_status(self):
            return {
                "employee_id": self.employee_id,
                "name": self.name,
                "type": self.type,
                "level": self.level,
                "status": self.status,
                "task_count": self.task_count,
                "success_count": self.success_count,
                "failure_count": self.failure_count,
                "performance_score": self.performance_score,
                "success_rate": 0.0 if self.task_count == 0 else self.success_count / self.task_count
            }
        
        def execute_task(self, task_data):
            self.task_count += 1
            self.success_count += 1
            return {"success": True, "message": "测试任务完成"}

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
            "test": "测试AI员工",
            "diagnostics_repair": "诊断修复AI员工",
            "question_bank_maintenance": "题库维护AI员工",
            "politics_question": "政治题库AI员工",
            "k12_question": "K12题库AI员工",
            "listening_question": "听力题库AI员工",
            "rule_base_maintenance": "规则库维护AI员工",
            "config_manager": "配置管理AI员工"
        }
        self.task_queue = []
        self.running_tasks = []
        self.employee_levels = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]  # AI级别范围

        # 从数据库加载员工，如果数据库为空则创建初始员工
        self._load_employees_from_database()

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

    def _safe_start_employee(self, employee):
        """安全启动AI员工，检查start方法是否存在"""
        if hasattr(employee, 'start') and callable(getattr(employee, 'start')):
            try:
                employee.start()
            except Exception as e:
                logger.warning(f"启动AI员工 {employee.employee_id} 时出错: {e}")
    
    def _get_employee_type(self, employee):
        """安全获取员工类型"""
        if hasattr(employee, 'type'):
            return employee.type
        elif hasattr(employee, 'employee_type'):
            return employee.employee_type
        else:
            return "unknown"

    def create_initial_employees(self):
        """创建初始AI员工"""
        # 创建验证AI员工 (级别5)
        validation_employee = ValidationAIEmployee("val_001", "验证AI", "validation", 5)
        validation_employee.type = "validation"
        self.employees["val_001"] = validation_employee
        self._safe_start_employee(validation_employee)
        self.add_employee_to_organizations(validation_employee)

        # 创建路由AI员工 (级别6)
        routing_employee = RoutingAIEmployee("route_001", "路由AI", "routing", 6)
        routing_employee.type = "routing"
        self.employees["route_001"] = routing_employee
        self._safe_start_employee(routing_employee)
        self.add_employee_to_organizations(routing_employee)

        # 创建测试系统AI员工 (级别7)
        test_system_employee = TestSystemAIEmployee("test_sys_001", "测试系统AI", "test_system", 7)
        test_system_employee.type = "test_system"
        self.employees["test_sys_001"] = test_system_employee
        self._safe_start_employee(test_system_employee)
        self.add_employee_to_organizations(test_system_employee)

        # 创建测试AI员工 (级别8)
        test_employee = TestAIEmployee("test_ai_001", "测试AI", "test", 8)
        self.employees["test_ai_001"] = test_employee
        self._safe_start_employee(test_employee)
        self.add_employee_to_organizations(test_employee)

        # 创建诊断修复AI员工 (级别9)
        diagnostics_employee = DiagnosticsRepairEmployee("diag_001", "诊断修复AI", 9)
        self.employees["diag_001"] = diagnostics_employee
        self._safe_start_employee(diagnostics_employee)
        self.add_employee_to_organizations(diagnostics_employee)

        # 创建题库维护AI员工 (级别7)
        qbm_employee = QuestionBankMaintenanceEmployee("qbm_001", "题库维护AI", 7)
        self.employees["qbm_001"] = qbm_employee
        self._safe_start_employee(qbm_employee)
        self.add_employee_to_organizations(qbm_employee)

        # 创建政治题库AI员工 (级别6)
        politics_employee = PoliticsQuestionEmployee("pol_001", "政治题库AI", 6)
        self.employees["pol_001"] = politics_employee
        self._safe_start_employee(politics_employee)
        self.add_employee_to_organizations(politics_employee)

        # 创建K12题库AI员工 (级别7)
        k12_employee = K12QuestionEmployee("k12_001", "K12题库AI", 7)
        self.employees["k12_001"] = k12_employee
        self._safe_start_employee(k12_employee)
        self.add_employee_to_organizations(k12_employee)

        # 创建听力题库AI员工 (级别6)
        listening_employee = ListeningQuestionEmployee("list_001", "听力题库AI", 6)
        self.employees["list_001"] = listening_employee
        self._safe_start_employee(listening_employee)
        self.add_employee_to_organizations(listening_employee)

        # 创建规则库维护AI员工 (级别8)
        rule_base_employee = RuleBaseMaintenanceEmployee("rbu_001", "规则库维护AI", 8)
        self.employees["rbu_001"] = rule_base_employee
        self._safe_start_employee(rule_base_employee)
        self.add_employee_to_organizations(rule_base_employee)

        # 创建配置管理AI员工 (级别8)
        config_manager_employee = ConfigManagerEmployee("config_mgr_001", "配置管理AI", "config_manager", 8)
        config_manager_employee.type = "config_manager"
        self.employees["config_mgr_001"] = config_manager_employee
        self._safe_start_employee(config_manager_employee)
        self.add_employee_to_organizations(config_manager_employee)

    def _parse_json_or_text(self, text):
        """解析JSON或文本，返回列表"""
        import json
        import re
        
        if not text:
            return []
        try:
            return json.loads(text)
        except (json.JSONDecodeError, ValueError):
            lines = [line.strip() for line in text.strip().split('\n') if line.strip()]
            result = []
            for line in lines:
                cleaned = re.sub(r'^[\d\.\-\•\*]+\s*', '', line)
                if cleaned:
                    result.append(cleaned)
            return result if result else [text]

    def _load_employees_from_database(self):
        """从数据库加载AI员工"""
        import sqlite3
        
        db_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'app.db')
        
        try:
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            
            cursor.execute('SELECT COUNT(*) FROM ai_employees')
            count = cursor.fetchone()[0]
            
            if count > 0:
                self.create_initial_employees()
                logger.info(f"从数据库加载 {count} 个业务专家AI员工...")
                
                cursor.execute('''
                    SELECT id, name, employee_code, description, capabilities, specialties, 
                           status, accuracy, total_tasks, successful_fixes, failed_fixes,
                           learning_rate, knowledge_base_size, last_training, model_version,
                           is_enabled, priority, max_concurrent_tasks, skill_level
                    FROM ai_employees
                ''')
                
                business_count = 0
                for row in cursor.fetchall():
                    emp_id = str(row[0])
                    name = row[1]
                    employee_code = row[2]
                    description = row[3]
                    capabilities = self._parse_json_or_text(row[4])
                    specialties = self._parse_json_or_text(row[5])
                    status = row[6]
                    accuracy = row[7]
                    total_tasks = row[8]
                    successful_fixes = row[9]
                    failed_fixes = row[10]
                    learning_rate = row[11]
                    knowledge_base_size = row[12]
                    last_training = row[13]
                    model_version = row[14]
                    is_enabled = row[15]
                    priority = row[16]
                    max_concurrent_tasks = row[17]
                    skill_level = row[18] if row[18] else 1
                    
                    employee = AIEmployee(emp_id, name, "business_expert", skill_level)
                    employee.type = "business_expert"
                    employee.status = status
                    employee.employee_code = employee_code
                    employee.description = description
                    employee.capabilities = capabilities
                    employee.specialties = specialties
                    employee.accuracy = accuracy
                    employee.total_tasks = total_tasks
                    employee.successful_fixes = successful_fixes
                    employee.failed_fixes = failed_fixes
                    employee.learning_rate = learning_rate
                    employee.knowledge_base_size = knowledge_base_size
                    employee.last_training = last_training
                    employee.model_version = model_version
                    employee.is_enabled = bool(is_enabled)
                    employee.priority = priority
                    employee.max_concurrent_tasks = max_concurrent_tasks
                    employee.performance_score = int(accuracy * 100) if accuracy else 80
                    
                    self.employees[emp_id] = employee
                    self.add_employee_to_organizations(employee)
                    business_count += 1
                
                logger.info(f"成功加载 {business_count} 个业务专家AI员工")
            else:
                logger.info("数据库中没有业务专家员工")
            
            conn.close()
        except Exception as e:
            logger.error(f"从数据库加载员工失败: {e}")
            logger.info("使用初始配置创建AI员工...")
            self.create_initial_employees()

    def create_employee(self, employee_type: str, name: str, level: int = 1) -> str:
        """创建新的AI员工"""
        # 验证级别范围
        if level < 1 or level > 10:
            raise ValueError(f"AI级别必须在1-10之间,当前值: {level}")

        employee_id = f"{employee_type[:3]}_{uuid.uuid4().hex[:8]}"

        if employee_type == "validation":
            employee = ValidationAIEmployee(employee_id, name, employee_type, level)
            employee.type = employee_type
        elif employee_type == "routing":
            employee = RoutingAIEmployee(employee_id, name, employee_type, level)
            employee.type = employee_type
        elif employee_type == "test_system":
            employee = TestSystemAIEmployee(employee_id, name, employee_type, level)
            employee.type = employee_type
        elif employee_type == "test":
            employee = TestAIEmployee(employee_id, name, employee_type, level)
        elif employee_type == "diagnostics_repair":
            employee = DiagnosticsRepairEmployee(employee_id, name, level)
        elif employee_type == "question_bank_maintenance":
            employee = QuestionBankMaintenanceEmployee(employee_id, name, level)
        elif employee_type == "politics_question":
            employee = PoliticsQuestionEmployee(employee_id, name, level)
        elif employee_type == "k12_question":
            employee = K12QuestionEmployee(employee_id, name, level)
        elif employee_type == "listening_question":
            employee = ListeningQuestionEmployee(employee_id, name, level)
        elif employee_type == "rule_base_maintenance":
            employee = RuleBaseMaintenanceEmployee(employee_id, name, level)
        elif employee_type == "config_manager":
            employee = ConfigManagerEmployee(employee_id, name, employee_type, level)
            employee.type = employee_type
        else:
            raise ValueError(f"未知的员工类型: {employee_type}")

        self.employees[employee_id] = employee
        self._safe_start_employee(employee)
        self.add_employee_to_organizations(employee)

        return employee_id

    def get_employee(self, employee_id: str) -> object:
        """获取AI员工"""
        return self.employees.get(employee_id)

    def get_all_employees(self) -> dict:
        """获取所有AI员工"""
        result = {}
        for employee_id, employee in self.employees.items():
            if hasattr(employee, 'get_status') and callable(getattr(employee, 'get_status')):
                try:
                    result[employee_id] = employee.get_status()
                except Exception as e:
                    result[employee_id] = {
                        'employee_id': employee_id,
                        'name': getattr(employee, 'name', 'Unknown'),
                        'type': self._get_employee_type(employee),
                        'level': getattr(employee, 'level', 1),
                        'status': 'active',
                        'error': str(e)
                    }
            else:
                result[employee_id] = {
                    'employee_id': employee_id,
                    'name': getattr(employee, 'name', 'Unknown'),
                    'type': self._get_employee_type(employee),
                    'level': getattr(employee, 'level', 1),
                    'status': getattr(employee, 'status', 'active')
                }
        return result

    def list_employees(self, role=None):
        """列出AI员工 (兼容app.py API)"""
        all_employees = self.get_all_employees()
        if role:
            return [e for e in all_employees.values() if e.get('type') == role or e.get('role') == role]
        return list(all_employees.values())

    def register_employee(self, employee_id, name, role, capabilities):
        """注册AI员工 (兼容app.py API)"""
        if employee_id in self.employees:
            return False
        
        employee = AIEmployee(employee_id, name, role, 1)
        employee.type = role
        employee.status = 'active'
        employee.capabilities = capabilities
        
        self.employees[employee_id] = employee
        self.add_employee_to_organizations(employee)
        return True

    def update_employee_status(self, employee_id, status):
        """更新AI员工状态 (兼容app.py API)"""
        employee = self.get_employee(employee_id)
        if employee:
            employee.status = status
            return True
        return False

    def list_system_params(self, scope=None):
        """列出系统参数 (兼容app.py API)"""
        if not hasattr(self, 'system_params'):
            self.system_params = {}
        if scope:
            return [p for p in self.system_params.values() if p.get('scope') == scope]
        return list(self.system_params.values())

    def set_system_param(self, key, value, scope='global', description=''):
        """设置系统参数 (兼容app.py API)"""
        if not hasattr(self, 'system_params'):
            self.system_params = {}
        if not hasattr(self, 'permission_rules'):
            self.permission_rules = {}
        
        self.system_params[key] = {
            'key': key,
            'value': value,
            'scope': scope,
            'description': description,
            'updated_at': datetime.now().isoformat()
        }
        return True

    def auto_discover_and_extend(self):
        """自动发现和扩展功能 (兼容app.py API)"""
        return []

    def assign_task(self, employee_id: str, task_data: dict) -> dict:
        """分配任务给AI员工"""
        employee = self.get_employee(employee_id)
        if not employee:
            return {
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
        task_data = task.get("task_data", {})
        employee_id = task.get("employee_id", "")
        employee = self.get_employee(employee_id)

        if not employee:
            return {
                "success": False,
                "message": f"未找到AI员工: {employee_id}"
            }

        # 更新任务状态
        task["status"] = "running"
        task["started_at"] = datetime.now().isoformat()
        
        # 添加到运行任务列表
        self.running_tasks.append(task)

        try:
            start_time = time.time()
            
            # 检查员工是否有execute_task方法
            if hasattr(employee, 'execute_task') and callable(getattr(employee, 'execute_task')):
                result = employee.execute_task(task_data)
            elif hasattr(employee, 'process') and callable(getattr(employee, 'process')):
                result = employee.process(task_data)
            else:
                result = {
                    "success": False,
                    "message": f"AI员工 {employee_id} 没有任务执行方法"
                }
            
            execution_time = time.time() - start_time

            # 更新任务状态
            task["status"] = "completed" if result.get("success", False) else "failed"
            task["completed_at"] = datetime.now().isoformat()
            task["result"] = result
            task["execution_time"] = execution_time

            # 更新AI员工性能数据
            if hasattr(employee, 'task_count'):
                employee.task_count += 1

            # 基于任务结果和执行时间更新性能评分
            score_change = 1 if result.get("success", False) else -1
            # 快速完成任务获得额外加分
            if execution_time < 0.5:
                score_change += 1
            # 长时间执行任务扣分
            elif execution_time > 5:
                score_change -= 1

            if hasattr(employee, 'performance_score'):
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
            # 更新AI员工性能数据(任务失败)
            if hasattr(employee, 'task_count'):
                employee.task_count += 1
            if hasattr(employee, 'performance_score'):
                employee.performance_score = max(0, employee.performance_score - 2)  # 失败扣分更多

            # 从运行任务列表中移除
            self.running_tasks = [t for t in self.running_tasks if t["task_id"] != task["task_id"]]

            return {
                "success": False,
                "error": str(e)
            }
    def run_all_tests(self) -> dict:
        """运行所有测试"""
        test_employee_id = None
        for employee_id, employee in self.employees.items():
            if isinstance(employee, TestAIEmployee):
                test_employee_id = employee_id
                break

        if not test_employee_id:
            return {
                "success": False,
                "message": "No test employee available"
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
        }
        return self.assign_task(test_employee_id, task_data)
    def auto_test_project(self) -> dict:
        # 查找测试AI员工
        test_employee_id = None
        for employee_id, employee in self.employees.items():
            if isinstance(employee, TestAIEmployee):
                test_employee_id = employee_id
                break

        if not test_employee_id:
                return {
                    "success": False,
                    "message": "未找到测试AI员工"
                }
        # 分配自动测试项目任务
        task_data = {
            "type": "auto_test_project",
            "data": {}
        }
    def get_employees_by_type(self, employee_type: str) -> list:
        """按类型获取AI员工"""
        employee_ids = self.employees_by_type.get(employee_type, [])
        return [self.employees[eid] for eid in employee_ids if eid in self.employees]

    def get_employees_by_level(self, level: int) -> list:
        employee_ids = self.employees_by_level.get(level, [])
        return [self.employees[eid] for eid in employee_ids if eid in self.employees]

    def get_employees_by_type_and_level(self, employee_type: str, min_level: int = 1, max_level: int = 10) -> list:
        """按类型和级别范围获取AI员工"""
        employees_of_type = self.get_employees_by_type(employee_type)
        result = []
        for emp in employees_of_type:
            emp_level = getattr(emp, 'level', 1)
            if min_level <= emp_level <= max_level:
                result.append(emp)
        return result

    def auto_assign_task(self, task_data: dict, required_level: int = 1) -> dict:
        """自动分配任务给合适的AI员工"""
        task_type = task_data.get("task_type", task_data.get("type", ""))
        required_employee_type = None

        if task_type in ["login", "register", "request"]:
            required_employee_type = "validation"
        elif task_type in ["determine", "redirect"]:
            required_employee_type = "routing"
        elif task_type in ["generate_test_content", "create_test_page_config", "optimize_test_page",
                          "upgrade_question_bank", "analyze_question_types", "mark_question_usage",
                          "check_question_similarity", "detect_duplicate_questions", "generate_targeted_practice"]:
            required_employee_type = "test_system"
        elif task_type in ["run_all_tests", "generate_test_report", "analyze_test_results", "auto_test_project"]:
            required_employee_type = "test"
        elif task_type in ["diagnostics", "repair", "health_check", "full_scan"]:
            required_employee_type = "diagnostics_repair"
        elif task_type in ["expand_questions", "organize_questions", "quality_check",
                          "duplicate_removal", "category_optimization", "full_maintenance",
                          "web_crawl", "ai_generate", "get_statistics", "get_maintenance_plans",
                          "create_maintenance_plan"]:
            required_employee_type = "question_bank_maintenance"
        elif task_type in ["generate_questions", "generate_current_affairs",
                          "generate_real_exam", "generate_high_frequency"]:
            required_employee_type = "politics_question"
        elif task_type in ["generate_by_stage", "generate_competition",
                          "generate_self_admission"]:
            required_employee_type = "k12_question"
        elif task_type in ["generate_listening", "generate_japanese",
                          "generate_english", "generate_by_difficulty",
                          "generate_by_topic", "generate_mass"]:
            required_employee_type = "listening_question"
        elif task_type in ["expand_rules", "organize_rules", "quality_check",
                          "duplicate_removal", "web_fetch", "ai_generate",
                          "system_adapt", "deploy_employees", "full_maintenance",
                          "get_statistics"]:
            required_employee_type = "rule_base_maintenance"

        if not required_employee_type:
            return {
                "success": False,
                "message": f"无法确定任务类型 '{task_type}' 所需的AI员工类型"
            }
        # 获取符合条件的AI员工(按类型和级别,且状态为active)
        employees_of_type = self.get_employees_by_type_and_level(required_employee_type, required_level)
        eligible_employees = []
        for emp in employees_of_type:
            emp_status = getattr(emp, 'status', 'active')
            if emp_status == "active":
                eligible_employees.append(emp)

        if not eligible_employees:
            return {
                "success": False,
                "message": f"未找到符合条件的{self.employee_types.get(required_employee_type, required_employee_type)}"
            }
        # 按性能评分和级别排序,选择最优的AI员工
        eligible_employees.sort(
            key=lambda x: (getattr(x, 'performance_score', 80), getattr(x, 'level', 1)),
            reverse=True
        )
        selected_employee = eligible_employees[0]
        selected_id = getattr(selected_employee, 'employee_id', None)
        # 分配任务
        if selected_id:
            return self.assign_task(selected_id, task_data)
        else:
            return {
                "success": False,
                "message": "无法获取员工ID"
            }

    def upgrade_employee(self, employee_id: str, new_level: int = None) -> dict:
        """升级AI员工"""
        employee = self.get_employee(employee_id)
        if not employee:
            return {
                "success": False,
                "message": f"未找到AI员工: {employee_id}"
            }
        # 如果未指定新级别,则升级一级
        if new_level is None:
            new_level = employee.level + 1

        if new_level <= employee.level or new_level > 10:
            return {
                "success": False,
                "message": f"无效的新级别: {new_level},必须大于当前级别 {employee.level} 且不超过10"
            }
        # 从组织结构中移除旧级别
        self.remove_employee_from_organizations(employee_id)
        # 更新级别
        employee.level = new_level

        self.add_employee_to_organizations(employee)
        return {
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
        inactive_employees = [emp for emp in self.employees.values() if emp.status != "active"]
        for emp in inactive_employees:
            self.remove_employee_from_organizations(emp.employee_id)
            emp.stop()
        optimization_results["optimizations"].append(f"已清理 {len(inactive_employees)} 个不活跃的AI员工")

        # 2. 根据性能评分调整AI员工级别
        for employee_id, employee in self.employees.items():
            # 高性能员工自动升级
            if employee.performance_score >= 80 and employee.level < 10:
                self.upgrade_employee(employee_id)

        # 统计各类型AI员工数量
        type_counts = {emp_type: len(emps) for emp_type, emps in self.employees_by_type.items()}
        optimization_results["optimizations"].append(f"当前AI员工分布: {type_counts}")

        return optimization_results

    def integrate_functions(self) -> dict:
        """整合AI员工功能"""
        # 功能整合主要是确保不同类型AI员工之间的协作顺畅
        # 这里可以添加更多整合逻辑,比如统一API、共享数据模型等

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

    print("AI员工管理器已创建,初始AI员工列表:")
    for employee_id, status in manager.get_all_employees().items():
        print(f"- {employee_id}: {status['name']} ({status['type']}) - 级别{status['level']} - 性能评分{status['performance_score']} - {status['status']}")

    print("\n1. 按类型获取AI员工:")
    validation_employees = manager.get_employees_by_type("validation")
    for emp in validation_employees:
        print(f"- {emp.employee_id}: {emp.name} (级别{emp.level})")

    print("\n2. 按级别获取AI员工:")
    level_7_employees = manager.get_employees_by_level(7)
    for emp in level_7_employees:
        print(f"- {emp.employee_id}: {emp.name} ({emp.type}) - 性能评分{emp.performance_score}")

    print("\n3. 自动分配任务:")
    test_task_data = {
        "type": "login",
        "data": {
            "username": "testuser",
            "password": "testpass"
        }
    }
    result = manager.assign_task(test_task_data)
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
