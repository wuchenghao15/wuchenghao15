# -*- coding: utf-8 -*-
"""
AI员工自动衍生系统 v1.0.0
自动分析系统功能，智能创建适配的AI员工，实现自我扩展和进化
"""

import logging
import threading
import time
import json
import os
import uuid
import sqlite3
from contextlib import contextmanager
from datetime import datetime
from typing import Dict, List, Any, Optional, Callable
from enum import Enum
from collections import defaultdict

logger = logging.getLogger(__name__)


class EmployeeRole(Enum):
    """AI员工角色类型"""
    SYSTEM_ADMIN = "system_admin"
    SECURITY_OFFICER = "security_officer"
    DATA_ANALYST = "data_analyst"
    PERFORMANCE_OPTIMIZER = "performance_optimizer"
    CONTENT_MANAGER = "content_manager"
    USER_SUPPORT = "user_support"
    TEST_ENGINEER = "test_engineer"
    DEPLOYMENT_MANAGER = "deployment_manager"
    BACKUP_ADMIN = "backup_admin"
    SYNC_MANAGER = "sync_manager"
    EXAM_MANAGER = "exam_manager"
    LEARNING_ADVISOR = "learning_advisor"
    CACHE_MANAGER = "cache_manager"
    API_GATEWAY = "api_gateway"
    WORKFLOW_ENGINEER = "workflow_engineer"
    ALERT_HANDLER = "alert_handler"
    REPORT_GENERATOR = "report_generator"
    KNOWLEDGE_CURATOR = "knowledge_curator"
    PREDICTION_SPECIALIST = "prediction_specialist"
    ERROR_RECOVERY = "error_recovery"
    DIAGNOSTICS_REPAIR = "diagnostics_repair"


class EmployeeStatus(Enum):
    """AI员工状态"""
    IDLE = "idle"
    WORKING = "working"
    LEARNING = "learning"
    ADAPTING = "adapting"
    PAUSED = "paused"
    ERROR = "error"


class EmployeeSkill:
    """AI员工技能"""
    
    def __init__(self, name: str, level: int = 1, experience: float = 0.0):
        self.name = name
        self.level = level
        self.experience = experience
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "level": self.level,
            "experience": self.experience
        }


class AIEmployee:
    """AI员工实体"""
    
    def __init__(self, employee_id: str, name: str, role: EmployeeRole, 
                 skills: List[EmployeeSkill] = None, capabilities: List[str] = None):
        self.employee_id = employee_id
        self.name = name
        self.role = role
        self.skills = skills or []
        self.capabilities = capabilities or []
        self.status = EmployeeStatus.IDLE
        self.created_at = datetime.now()
        self.last_updated = datetime.now()
        self.last_active = datetime.now()
        self.performance_metrics = {
            "tasks_completed": 0,
            "success_rate": 1.0,
            "efficiency_score": 1.0,
            "learning_progress": 0.0
        }
        self.adaptation_history = []
        self.assigned_features = []
        
        logger.info(f"创建AI员工: {self.name} ({self.role.value})")
    
    def add_skill(self, skill: EmployeeSkill):
        """添加技能"""
        existing = next((s for s in self.skills if s.name == skill.name), None)
        if existing:
            existing.level = max(existing.level, skill.level)
            existing.experience += skill.experience
        else:
            self.skills.append(skill)
    
    def assign_feature(self, feature_name: str):
        """分配功能"""
        if feature_name not in self.assigned_features:
            self.assigned_features.append(feature_name)
            self.last_updated = datetime.now()
            logger.info(f"AI员工 {self.name} 分配功能: {feature_name}")
    
    def update_status(self, status: EmployeeStatus):
        """更新状态"""
        self.status = status
        self.last_active = datetime.now()
    
    def record_adaptation(self, feature: str, success: bool, details: str):
        """记录适配历史"""
        record = {
            "feature": feature,
            "success": success,
            "details": details,
            "timestamp": datetime.now().isoformat()
        }
        self.adaptation_history.append(record)
        if len(self.adaptation_history) > 100:
            self.adaptation_history = self.adaptation_history[-100:]
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "employee_id": self.employee_id,
            "name": self.name,
            "role": self.role.value,
            "skills": [s.to_dict() for s in self.skills],
            "capabilities": self.capabilities,
            "status": self.status.value,
            "created_at": self.created_at.isoformat(),
            "last_updated": self.last_updated.isoformat(),
            "last_active": self.last_active.isoformat(),
            "performance_metrics": self.performance_metrics,
            "assigned_features": self.assigned_features,
            "adaptation_count": len(self.adaptation_history)
        }


class FeatureAnalyzer:
    """功能分析器 - 分析系统功能并确定需要的AI员工"""
    
    SYSTEM_FEATURES = {
        "security": {
            "description": "系统安全功能",
            "required_roles": [EmployeeRole.SECURITY_OFFICER],
            "required_skills": ["security_scanning", "threat_detection", "access_control", "audit_logging"]
        },
        "authentication": {
            "description": "用户认证功能",
            "required_roles": [EmployeeRole.SECURITY_OFFICER],
            "required_skills": ["token_validation", "session_management", "password_encryption"]
        },
        "authorization": {
            "description": "权限管理功能",
            "required_roles": [EmployeeRole.SYSTEM_ADMIN],
            "required_skills": ["role_based_access", "permission_checking", "access_control"]
        },
        "exam_system": {
            "description": "考试系统功能",
            "required_roles": [EmployeeRole.EXAM_MANAGER],
            "required_skills": ["exam_administration", "timeout_management", "lock_system", "grading"]
        },
        "learning_system": {
            "description": "学习系统功能",
            "required_roles": [EmployeeRole.LEARNING_ADVISOR],
            "required_skills": ["learning_analysis", "personalized_recommendation", "progress_tracking"]
        },
        "database": {
            "description": "数据库管理功能",
            "required_roles": [EmployeeRole.DATA_ANALYST],
            "required_skills": ["data_query", "data_optimization", "data_backup", "schema_design"]
        },
        "monitoring": {
            "description": "系统监控功能",
            "required_roles": [EmployeeRole.PERFORMANCE_OPTIMIZER, EmployeeRole.ALERT_HANDLER],
            "required_skills": ["system_monitoring", "alert_detection", "performance_analysis", "log_analysis"]
        },
        "performance": {
            "description": "性能优化功能",
            "required_roles": [EmployeeRole.PERFORMANCE_OPTIMIZER],
            "required_skills": ["system_optimization", "resource_allocation", "caching", "load_balancing"]
        },
        "backup": {
            "description": "备份管理功能",
            "required_roles": [EmployeeRole.BACKUP_ADMIN],
            "required_skills": ["backup_creation", "restore_management", "disaster_recovery"]
        },
        "sync": {
            "description": "同步管理功能",
            "required_roles": [EmployeeRole.SYNC_MANAGER],
            "required_skills": ["git_sync", "remote_replication", "version_control"]
        },
        "sandbox": {
            "description": "沙盒环境功能",
            "required_roles": [EmployeeRole.DEPLOYMENT_MANAGER],
            "required_skills": ["environment_isolation", "safe_deployment", "rollback"]
        },
        "api": {
            "description": "API管理功能",
            "required_roles": [EmployeeRole.API_GATEWAY],
            "required_skills": ["api_management", "api_monitoring", "api_security"]
        },
        "cache": {
            "description": "缓存管理功能",
            "required_roles": [EmployeeRole.CACHE_MANAGER],
            "required_skills": ["cache_strategy", "cache_invalidation", "performance_tuning"]
        },
        "workflow": {
            "description": "工作流管理功能",
            "required_roles": [EmployeeRole.WORKFLOW_ENGINEER],
            "required_skills": ["task_scheduling", "process_automation", "dependency_management"]
        },
        "reporting": {
            "description": "报表生成功能",
            "required_roles": [EmployeeRole.REPORT_GENERATOR],
            "required_skills": ["data_visualization", "report_generation", "trend_analysis"]
        },
        "knowledge": {
            "description": "知识管理功能",
            "required_roles": [EmployeeRole.KNOWLEDGE_CURATOR],
            "required_skills": ["knowledge_graph", "information_retrieval", "content_management"]
        },
        "prediction": {
            "description": "预测分析功能",
            "required_roles": [EmployeeRole.PREDICTION_SPECIALIST],
            "required_skills": ["predictive_analytics", "machine_learning", "trend_forecasting"]
        },
        "testing": {
            "description": "测试功能",
            "required_roles": [EmployeeRole.TEST_ENGINEER],
            "required_skills": ["automated_testing", "quality_assurance", "bug_detection"]
        },
        "recovery": {
            "description": "错误恢复功能",
            "required_roles": [EmployeeRole.ERROR_RECOVERY],
            "required_skills": ["error_detection", "auto_healing", "fault_tolerance"]
        },
        "diagnostics": {
            "description": "问题诊断与修复功能",
            "required_roles": [EmployeeRole.DIAGNOSTICS_REPAIR],
            "required_skills": ["system_diagnostics", "problem_detection", "auto_repair", "health_monitoring", "report_generation", "root_cause_analysis"]
        },
        "user_support": {
            "description": "用户支持功能",
            "required_roles": [EmployeeRole.USER_SUPPORT],
            "required_skills": ["user_assistance", "issue_resolution", "feedback_management"]
        },
        "content": {
            "description": "内容管理功能",
            "required_roles": [EmployeeRole.CONTENT_MANAGER],
            "required_skills": ["content_creation", "content_organization", "content_publishing"]
        },
        "deployment": {
            "description": "部署管理功能",
            "required_roles": [EmployeeRole.DEPLOYMENT_MANAGER],
            "required_skills": ["system_deployment", "version_management", "configuration_management"]
        }
    }
    
    def __init__(self):
        self.analyzed_features = set()
        self.role_requirements = defaultdict(list)
    
    def analyze_feature(self, feature_name: str) -> Dict[str, Any]:
        """分析单个功能"""
        if feature_name not in self.SYSTEM_FEATURES:
            return {
                "feature": feature_name,
                "found": False,
                "description": "未知功能",
                "required_roles": [],
                "required_skills": []
            }
        
        feature = self.SYSTEM_FEATURES[feature_name]
        self.analyzed_features.add(feature_name)
        
        for role in feature["required_roles"]:
            self.role_requirements[role].append(feature_name)
        
        return {
            "feature": feature_name,
            "found": True,
            "description": feature["description"],
            "required_roles": [r.value for r in feature["required_roles"]],
            "required_skills": feature["required_skills"]
        }
    
    def analyze_all_features(self) -> List[Dict[str, Any]]:
        """分析所有已知功能"""
        results = []
        for feature_name in self.SYSTEM_FEATURES:
            results.append(self.analyze_feature(feature_name))
        return results
    
    def get_role_requirements(self) -> Dict[str, List[str]]:
        """获取角色需求"""
        return {role.value: features for role, features in self.role_requirements.items()}


class AIEmployeeAutoGenerator:
    """AI员工自动衍生器"""
    
    def __init__(self):
        self.employees: Dict[str, AIEmployee] = {}
        self.employees_by_role: Dict[str, List[AIEmployee]] = defaultdict(list)
        self.employees_by_feature: Dict[str, List[AIEmployee]] = defaultdict(list)
        self.feature_analyzer = FeatureAnalyzer()
        self.is_running = False
        self.monitor_thread: Optional[threading.Thread] = None
        self.adaptation_lock = threading.Lock()
        
        self._load_config()
        self._load_employees_from_database()
    
    @contextmanager
    def _get_db_connection(self):
        """获取数据库连接"""
        db_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'app.db')
        conn = sqlite3.connect(db_path, timeout=10.0)
        conn.row_factory = sqlite3.Row
        try:
            yield conn
        finally:
            conn.close()
    
    def _load_config(self):
        """加载配置"""
        config_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "employee_config.json")
        if os.path.exists(config_path):
            try:
                with open(config_path, 'r', encoding='utf-8') as f:
                    self.config = json.load(f)
                logger.info("AI员工配置加载成功")
            except Exception as e:
                logger.error(f"加载配置失败: {e}")
                self.config = {}
        else:
            self.config = {}
    
    def _save_config(self):
        """保存配置"""
        config_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "employee_config.json")
        try:
            with open(config_path, 'w', encoding='utf-8') as f:
                json.dump(self.config, f, ensure_ascii=False, indent=2)
        except Exception as e:
            logger.error(f"保存配置失败: {e}")
    
    def _load_employees_from_database(self):
        """从数据库加载所有AI员工"""
        logger.info("开始从数据库加载AI员工...")

        try:
            with self._get_db_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT id, name, employee_code, description, capabilities, specialties,
                           status, accuracy, is_enabled, priority, skill_level,
                           created_at, updated_at
                    FROM ai_employees
                    ORDER BY id ASC
                    LIMIT 100
                """)
                
                rows = cursor.fetchall()
                employee_code_to_role = {
                    'AI_FIXER_001': 'error_recovery',
                    'AI_MATH_FIXER_001': 'error_recovery',
                    'AI_EXC_FIXER_001': 'error_recovery',
                    'AI_CDN_ICON_FIXER_001': 'performance_optimizer',
                    'AI_CODE_FIXER_001': 'error_recovery',
                    'AI_NOTIFICATION_EXTENDER_001': 'content_manager',
                    'AI_BUTTON_EXTENDER_001': 'content_manager',
                    'AI_GAOKAO_EXPANSION_001': 'content_manager',
                    'AI_GAOKAO_HISTORY_001': 'content_manager',
                    'AI_GAOKAO_HISTORY_AUTO_001': 'content_manager',
                    'AI_ZHONGKAO_HISTORY_AUTO_001': 'content_manager',
                    'AI_JAPANESE_READING_AUTO_001': 'content_manager',
                    'AI_NCE_HISTORY_AUTO_001': 'content_manager',
                    'AI_NEWORIENTAL_AUTO_001': 'content_manager',
                    'AI_INDEPENDENT_ADMISSION_AUTO_001': 'content_manager',
                    'AI_JUNIOR_COLLEGE_AUTO_001': 'content_manager',
                    'AI_SYS_ADMIN_001': 'system_admin',
                    'AI_HARDWARE_MGR_001': 'system_admin',
                    'AI_EXAM_MGR_001': 'exam_manager',
                    'AI_REPORT_GEN_001': 'report_generator',
                    'AI_SECURITY_MGR_001': 'security_officer',
                    'AI_DB_MGR_001': 'data_analyst',
                    'AI_BACKUP_MGR_001': 'backup_admin',
                    'AI_MONITOR_001': 'alert_handler',
                    'AI_QUESTION_GENERATOR_001': 'content_manager',
                    'AI_PRACTICE_QUESTION_001': 'content_manager',
                    'AI_CHOICE_OPTION_OPTIMIZER_001': 'content_manager',
                    'AI_LANGUAGE_CHOICE_OPTIMIZER_001': 'content_manager',
                    'AI_MCQ_CLEANER_001': 'content_manager',
                    'AI_JAPANESE_EXAM_COLLECTOR_001': 'content_manager',
                    'AI_SINGAPORE_EXAM_COLLECTOR_001': 'content_manager',
                    'AI_CODE_OPTIMIZER_001': 'performance_optimizer',
                    'AI_FRONTEND_OPTIMIZER_001': 'performance_optimizer',
                    'AI_DATA_SECURITY_001': 'security_officer',
                    'AI_PLACEMENT_OPTIMIZER_001': 'exam_manager',
                    'AI_AUDIO_FIXER_001': 'error_recovery',
                    'AI_MCQ_FIXER_001': 'error_recovery',
                    'AI-EXPLAIN-001': 'learning_advisor',
                    'AI-AUDIO-MATCH-001': 'error_recovery',
                    'AI-AUDIO-TEST-001': 'test_engineer',
                    'EDU_NINE_YEAR': 'learning_advisor',
                    'EDU_ADULT': 'learning_advisor',
                    'EXAM_NINE_YEAR': 'exam_manager',
                    'EXAM_ADULT': 'exam_manager'
                }
                
                for row in rows:
                    try:
                        capabilities = []
                        if row['capabilities']:
                            try:
                                capabilities = json.loads(row['capabilities'])
                            except Exception:
                                capabilities = [row['capabilities']]
                        
                        specialties = []
                        if row['specialties']:
                            try:
                                specialties = json.loads(row['specialties'])
                            except Exception:
                                specialties = []
                        
                        code = row['employee_code']
                        role_name = employee_code_to_role.get(code, 'system_admin')
                        
                        try:
                            role = EmployeeRole(role_name)
                        except ValueError:
                            role = EmployeeRole.SYSTEM_ADMIN
                        
                        skills = []
                        for cap in capabilities[:10]:
                            if isinstance(cap, str):
                                skill_name = cap[:50].replace(' ', '_').lower()
                                skills.append(skill_name)
                        
                        employee_id = f"db_{row['id']}_{code}"
                        
                        employee_skills = [EmployeeSkill(s, level=row['skill_level'] or 1, 
                                                          experience=row['accuracy'] or 0.0) 
                                           for s in skills]
                        
                        employee = AIEmployee(employee_id, row['name'], role, 
                                             employee_skills, capabilities)
                        
                        employee.performance_metrics = {
                            "tasks_completed": row['accuracy'] or 0,
                            "success_rate": row['accuracy'] / 100 if row['accuracy'] else 1.0,
                            "efficiency_score": row['accuracy'] / 100 if row['accuracy'] else 1.0,
                            "learning_progress": 0.0
                        }
                        
                        if row['is_enabled']:
                            employee.status = EmployeeStatus.IDLE
                        else:
                            employee.status = EmployeeStatus.PAUSED
                        
                        self.employees[employee_id] = employee
                        self.employees_by_role[role.value].append(employee)
                        
                    except Exception as e:
                        logger.error(f"加载员工失败 ({row['name']}): {e}")
            
            logger.info(f"从数据库加载完成，共 {len(self.employees)} 名AI员工")
        
        except Exception as e:
            logger.error(f"从数据库加载员工失败: {e}")
            self._init_core_employees()
    
    def _init_core_employees(self):
        """初始化核心AI员工（数据库加载失败时使用）"""
        logger.info("使用核心员工初始化...")
        
        core_employees = [
            {
                "role": EmployeeRole.SYSTEM_ADMIN,
                "name": "系统管理员",
                "skills": ["system_management", "resource_allocation", "configuration", "user_management"],
                "capabilities": ["system_overview", "admin_tasks", "resource_monitoring"]
            },
            {
                "role": EmployeeRole.SECURITY_OFFICER,
                "name": "安全专员",
                "skills": ["security_scanning", "threat_detection", "access_control", "audit_logging"],
                "capabilities": ["security_audit", "threat_response", "access_management"]
            },
            {
                "role": EmployeeRole.PERFORMANCE_OPTIMIZER,
                "name": "性能优化师",
                "skills": ["system_optimization", "resource_allocation", "caching", "load_balancing"],
                "capabilities": ["performance_monitoring", "optimization_recommendations", "capacity_planning"]
            },
            {
                "role": EmployeeRole.DATA_ANALYST,
                "name": "数据分析师",
                "skills": ["data_query", "data_optimization", "data_backup", "schema_design"],
                "capabilities": ["data_analysis", "reporting", "database_management"]
            }
        ]
        
        for emp_config in core_employees:
            self.create_employee(emp_config["role"], emp_config["name"],
                                emp_config["skills"], emp_config["capabilities"])
    
    def create_employee(self, role: EmployeeRole, name: str, 
                        skills: List[str] = None, capabilities: List[str] = None) -> AIEmployee:
        """创建AI员工"""
        employee_id = f"ai_{role.value}_{uuid.uuid4().hex[:8]}"
        
        employee_skills = [EmployeeSkill(s, level=1, experience=0.0) for s in (skills or [])]
        employee = AIEmployee(employee_id, name, role, employee_skills, capabilities or [])
        
        self.employees[employee_id] = employee
        self.employees_by_role[role.value].append(employee)
        
        logger.info(f"创建AI员工成功: {employee_id} - {name} ({role.value})")
        return employee
    
    def get_employee(self, employee_id: str) -> Optional[AIEmployee]:
        """获取AI员工"""
        return self.employees.get(employee_id)
    
    def get_employees_by_role(self, role: str) -> List[AIEmployee]:
        """按角色获取AI员工"""
        return self.employees_by_role.get(role, [])
    
    def list_employees(self) -> List[Dict[str, Any]]:
        """列出所有AI员工"""
        return [emp.to_dict() for emp in self.employees.values()]
    
    def auto_generate_employees(self) -> Dict[str, Any]:
        """自动衍生AI员工"""
        logger.info("开始自动衍生AI员工...")
        
        results = {
            "total_features_analyzed": 0,
            "new_employees_created": 0,
            "existing_employees_adapted": 0,
            "features_assigned": 0,
            "new_employees": [],
            "adapted_employees": []
        }
        
        feature_analysis = self.feature_analyzer.analyze_all_features()
        results["total_features_analyzed"] = len(feature_analysis)
        
        for feature_info in feature_analysis:
            if not feature_info["found"]:
                continue
            
            feature_name = feature_info["feature"]
            
            for role_name in feature_info["required_roles"]:
                role = EmployeeRole(role_name)
                existing_employees = self.get_employees_by_role(role_name)
                
                if existing_employees:
                    employee = existing_employees[0]
                    self._adapt_employee_to_feature(employee, feature_info)
                    results["existing_employees_adapted"] += 1
                    results["adapted_employees"].append(employee.employee_id)
                else:
                    new_employee = self._create_employee_for_feature(role, feature_info)
                    if new_employee:
                        results["new_employees_created"] += 1
                        results["new_employees"].append(new_employee.employee_id)
                
                results["features_assigned"] += 1
        
        logger.info(f"自动衍生完成: 新增 {results['new_employees_created']} 名员工, "
                    f"适配 {results['existing_employees_adapted']} 名员工")
        
        return results
    
    def _adapt_employee_to_feature(self, employee: AIEmployee, feature_info: Dict[str, Any]):
        """适配员工到功能"""
        with self.adaptation_lock:
            feature_name = feature_info["feature"]
            
            if feature_name in employee.assigned_features:
                return
            
            employee.assign_feature(feature_name)
            
            for skill_name in feature_info["required_skills"]:
                employee.add_skill(EmployeeSkill(skill_name, level=2, experience=10.0))
            
            employee.record_adaptation(feature_name, True, 
                                       f"成功适配到功能: {feature_info['description']}")
            
            logger.info(f"AI员工 {employee.name} 已适配到功能: {feature_name}")
    
    def _create_employee_for_feature(self, role: EmployeeRole, 
                                     feature_info: Dict[str, Any]) -> Optional[AIEmployee]:
        """为功能创建新员工"""
        role_display_names = {
            EmployeeRole.SYSTEM_ADMIN: "系统管理员",
            EmployeeRole.SECURITY_OFFICER: "安全专员",
            EmployeeRole.DATA_ANALYST: "数据分析师",
            EmployeeRole.PERFORMANCE_OPTIMIZER: "性能优化师",
            EmployeeRole.CONTENT_MANAGER: "内容管理员",
            EmployeeRole.USER_SUPPORT: "用户支持专员",
            EmployeeRole.TEST_ENGINEER: "测试工程师",
            EmployeeRole.DEPLOYMENT_MANAGER: "部署管理员",
            EmployeeRole.BACKUP_ADMIN: "备份管理员",
            EmployeeRole.SYNC_MANAGER: "同步管理员",
            EmployeeRole.EXAM_MANAGER: "考试管理员",
            EmployeeRole.LEARNING_ADVISOR: "学习顾问",
            EmployeeRole.CACHE_MANAGER: "缓存管理员",
            EmployeeRole.API_GATEWAY: "API网关管理员",
            EmployeeRole.WORKFLOW_ENGINEER: "工作流工程师",
            EmployeeRole.ALERT_HANDLER: "告警处理员",
            EmployeeRole.REPORT_GENERATOR: "报告生成员",
            EmployeeRole.KNOWLEDGE_CURATOR: "知识管理员",
            EmployeeRole.PREDICTION_SPECIALIST: "预测专家",
            EmployeeRole.ERROR_RECOVERY: "错误恢复员",
            EmployeeRole.DIAGNOSTICS_REPAIR: "诊断修复员"
        }
        
        name = role_display_names.get(role, f"{role.value}_employee")
        name += f"_{len(self.get_employees_by_role(role.value)) + 1}"
        
        new_employee = self.create_employee(
            role=role,
            name=name,
            skills=feature_info["required_skills"],
            capabilities=[feature_info["description"]]
        )
        
        new_employee.assign_feature(feature_info["feature"])
        new_employee.record_adaptation(feature_info["feature"], True, 
                                       f"新员工已适配到功能: {feature_info['description']}")
        
        return new_employee
    
    def adapt_to_new_feature(self, feature_name: str, 
                            feature_description: str = "",
                            required_skills: List[str] = None) -> Dict[str, Any]:
        """适配到新功能"""
        logger.info(f"开始适配新功能: {feature_name}")
        
        result = {
            "feature": feature_name,
            "description": feature_description,
            "action": "",
            "employee_id": None,
            "employee_name": None,
            "skills_added": []
        }
        
        analysis = self.feature_analyzer.analyze_feature(feature_name)
        
        if analysis["found"]:
            required_roles = analysis["required_roles"]
            required_skills = analysis["required_skills"]
        else:
            required_roles = []
            required_skills = required_skills or []
        
        if required_roles:
            for role_name in required_roles:
                existing_employees = self.get_employees_by_role(role_name)
                if existing_employees:
                    employee = existing_employees[0]
                    self._adapt_employee_to_feature(employee, {
                        "feature": feature_name,
                        "description": feature_description,
                        "required_skills": required_skills
                    })
                    result["action"] = "adapted_existing"
                    result["employee_id"] = employee.employee_id
                    result["employee_name"] = employee.name
                    result["skills_added"] = required_skills
                    break
                else:
                    role = EmployeeRole(role_name)
                    new_employee = self._create_employee_for_feature(role, {
                        "feature": feature_name,
                        "description": feature_description,
                        "required_skills": required_skills
                    })
                    result["action"] = "created_new"
                    result["employee_id"] = new_employee.employee_id
                    result["employee_name"] = new_employee.name
                    result["skills_added"] = required_skills
        else:
            new_employee = self.create_employee(
                role=EmployeeRole.SYSTEM_ADMIN,
                name=f"通用功能员工_{len(self.employees) + 1}",
                skills=required_skills or [],
                capabilities=[feature_description]
            )
            new_employee.assign_feature(feature_name)
            result["action"] = "created_generic"
            result["employee_id"] = new_employee.employee_id
            result["employee_name"] = new_employee.name
            result["skills_added"] = required_skills or []
        
        logger.info(f"适配完成: {result['action']} - {result['employee_name']}")
        return result
    
    def start(self):
        """启动自动衍生系统"""
        if self.is_running:
            return
        
        self.is_running = True
        self.monitor_thread = threading.Thread(target=self._monitor_loop, daemon=True)
        self.monitor_thread.start()
        
        logger.info("AI员工自动衍生系统已启动")
    
    def stop(self):
        """停止自动衍生系统"""
        self.is_running = False
        if self.monitor_thread:
            self.monitor_thread.join(timeout=5)
        logger.info("AI员工自动衍生系统已停止")
    
    def _monitor_loop(self):
        """监控循环 - 定期检查并自动衍生"""
        while self.is_running:
            try:
                self._check_and_adapt()
                time.sleep(300)
            except Exception as e:
                logger.error(f"监控循环出错: {e}")
    
    def _check_and_adapt(self):
        """检查并适配"""
        logger.debug("执行定期检查...")
        self.auto_generate_employees()
    
    def get_system_status(self) -> Dict[str, Any]:
        """获取系统状态"""
        role_counts = {role: len(emps) for role, emps in self.employees_by_role.items()}
        feature_assignments = {feature: len(emps) for feature, emps in self.employees_by_feature.items()}
        
        return {
            "total_employees": len(self.employees),
            "employee_types": role_counts,
            "feature_assignments": feature_assignments,
            "is_running": self.is_running,
            "last_checked": datetime.now().isoformat()
        }
    
    def get_employee_stats(self) -> Dict[str, Any]:
        """获取员工统计"""
        stats = {
            "total": len(self.employees),
            "by_role": {},
            "by_status": {status.value: 0 for status in EmployeeStatus},
            "total_skills": 0,
            "total_features_assigned": 0
        }
        
        for role, emps in self.employees_by_role.items():
            stats["by_role"][role] = len(emps)
        
        for emp in self.employees.values():
            stats["by_status"][emp.status.value] += 1
            stats["total_skills"] += len(emp.skills)
            stats["total_features_assigned"] += len(emp.assigned_features)
        
        return stats


# 全局单例
_employee_generator: Optional[AIEmployeeAutoGenerator] = None


def get_employee_generator() -> AIEmployeeAutoGenerator:
    """获取AI员工自动衍生器单例"""
    global _employee_generator
    if _employee_generator is None:
        _employee_generator = AIEmployeeAutoGenerator()
    return _employee_generator


if __name__ == "__main__":
    generator = AIEmployeeAutoGenerator()
    
    print("=" * 60)
    print("AI员工自动衍生系统测试")
    print("=" * 60)
    
    print("\n1. 初始员工列表:")
    initial_employees = generator.list_employees()
    for emp in initial_employees:
        print(f"  ID: {emp['employee_id']}")
        print(f"  名称: {emp['name']}")
        print(f"  角色: {emp['role']}")
        print(f"  技能: {', '.join(s['name'] for s in emp['skills'])}")
        print()
    
    print("2. 自动衍生AI员工...")
    result = generator.auto_generate_employees()
    print(f"   - 分析功能数: {result['total_features_analyzed']}")
    print(f"   - 新增员工数: {result['new_employees_created']}")
    print(f"   - 适配员工数: {result['existing_employees_adapted']}")
    print(f"   - 分配功能数: {result['features_assigned']}")
    
    print("\n3. 衍生后员工列表:")
    all_employees = generator.list_employees()
    for emp in all_employees:
        print(f"  {emp['name']} ({emp['role']}) - 功能: {', '.join(emp['assigned_features'])}")
    
    print("\n4. 系统状态:")
    status = generator.get_system_status()
    print(f"   - 总员工数: {status['total_employees']}")
    print(f"   - 员工类型: {status['employee_types']}")
    
    print("\n5. 适配新功能...")
    adapt_result = generator.adapt_to_new_feature(
        "new_feature",
        "新功能描述",
        ["new_skill_1", "new_skill_2"]
    )
    print(f"   - 操作: {adapt_result['action']}")
    print(f"   - 员工: {adapt_result['employee_name']}")
    print(f"   - 技能: {adapt_result['skills_added']}")
    
    print("\n" + "=" * 60)
    print("测试完成")
    print("=" * 60)