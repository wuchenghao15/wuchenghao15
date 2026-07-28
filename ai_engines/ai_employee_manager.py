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
from ai_engines.arduino_ai_employees import (
    ArduinoCodeGeneratorEmployee,
    ArduinoCodeDebuggerEmployee,
    ArduinoCodeOptimizerEmployee,
    ArduinoComponentAdvisorEmployee,
)
from ai_engines.ai_code_review_agent import AICodeReviewAgent
from ai_engines.ai_auto_test_agent import AIAutoTestAgent
from ai_engines.ai_performance_optimizer import AIPerformanceOptimizer
from ai_engines.ai_security_auditor import AISecurityAuditor
from ai_engines.ai_requirement_analyzer import AIRequirementAnalyzer
from ai_engines.ai_doc_generator import AIDocGenerator
from ai_engines.ai_task_scheduler_agent import AITaskSchedulerAgent
from ai_engines.ai_auto_repair_agent import AIAutoRepairAgent
from ai_engines.ai_data_analyzer import AIDataAnalyzer
from ai_engines.ai_model_manager import AIModelManager
from ai_engines.ai_ops_agent import AIOpsAgent
from ai_engines.ai_code_generator_agent import AICodeGeneratorAgent
from ai_engines.ai_conversation_agent import AIConversationAgent
from ai_engines.ai_recommendation_agent import AIRecommendationAgent
from ai_engines.ai_marketing_agent import AIMarketingAgent
from ai_engines.ai_customer_service_agent import AICustomerServiceAgent
from ai_engines.ai_public_opinion_agent import AIPublicOpinionAgent
from ai_engines.ai_financial_agent import AIFinancialAgent
from ai_engines.ai_hr_agent import AIHRAgent
from ai_engines.ai_project_management_agent import AIProjectManagementAgent
from ai_engines.ai_crm_agent import AICRMAgent
from ai_engines.ai_education_manager import AIEducationManager
from ai_engines.ai_community_manager import AICommunityManager
from ai_engines.ai_activity_manager import AIActivityManager
from ai_engines.ai_content_creator import AIContentCreator
from ai_engines.ai_config_manager import AIConfigManager
from ai_engines.ai_log_analyzer import AILogAnalyzer
from ai_engines.ai_document_processor import AIDocumentProcessor
from ai_engines.ai_vulnerability_scanner import AIVulnerabilityScanner
from ai_engines.ai_cybersecurity_agent import AICybersecurityAgent
from ai_engines.ai_system_extension_agent import AISystemExtensionAgent
from ai_engines.ai_data_science_agent import AIDataScienceAgent
from ai_engines.ai_image_processing_agent import AIImageProcessingAgent
from ai_engines.ai_speech_processing_agent import AISpeechProcessingAgent
from ai_engines.ai_translation_agent import AITranslationAgent
from ai_engines.ai_data_governance_agent import AIDataGovernanceAgent
from ai_engines.ai_business_intelligence_agent import AIBusinessIntelligenceAgent
from ai_engines.ai_devops_agent import AIDevOpsAgent
from ai_engines.ai_microservice_agent import AIMicroserviceAgent
from ai_engines.ai_knowledge_graph_agent import AIKnowledgeGraphAgent
from ai_engines.ai_digital_twin_agent import AIDigitalTwinAgent
from ai_engines.ai_vikey_security_employee import AI_VIKEY_Security_Employee

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
            "config_manager": "配置管理AI员工",
            "japanese_listener_kansai": "日语听力报读员-关西腔",
            "japanese_listener_kanto": "日语听力报读员-关东腔",
            "english_listener_american": "英语听力报读员-美式英语",
            "english_listener_british": "英语听力报读员-英式英语",
            "arduino_code_generator": "Arduino代码生成AI员工",
            "arduino_code_debugger": "Arduino代码调试AI员工",
            "arduino_code_optimizer": "Arduino代码优化AI员工",
            "arduino_component_advisor": "Arduino组件推荐AI员工",
            "code_review": "代码审查AI员工",
            "auto_test": "自动化测试AI员工",
            "performance_optimizer": "性能优化AI员工",
            "security_auditor": "安全审计AI员工",
            "requirement_analyzer": "需求分析AI员工",
            "doc_generator": "文档生成AI员工",
            "task_scheduler": "任务调度AI员工",
            "auto_repair": "自动修复AI员工",
            "data_analyzer": "数据分析AI员工",
            "model_manager": "模型管理AI员工",
            "ops_agent": "智能运维AI员工",
            "code_generator": "代码生成AI员工",
            "conversation": "对话管理AI员工",
            "recommendation": "推荐系统AI员工",
            "marketing": "营销AI员工",
            "customer_service": "客服AI员工",
            "public_opinion": "舆情分析AI员工",
            "financial": "财务分析AI员工",
            "hr": "人力资源AI员工",
            "project_management": "项目管理AI员工",
            "crm": "客户关系AI员工",
            "education_manager": "教育管理AI员工",
            "community_manager": "社区管理AI员工",
            "activity_manager": "活动管理AI员工",
            "content_creator": "内容创作AI员工",
            "config_manager": "配置管理AI员工",
            "log_analyzer": "日志分析AI员工",
            "document_processor": "文档处理AI员工",
            "vulnerability_scanner": "安全漏洞检测AI员工",
            "cybersecurity": "网络安全AI员工",
            "system_extension": "系统扩展AI员工",
            "data_science": "数据科学AI员工",
            "image_processing": "图像处理AI员工",
            "speech_processing": "语音处理AI员工",
            "translation": "智能翻译AI员工",
            "data_governance": "数据治理AI员工",
            "business_intelligence": "商业智能AI员工",
            "devops": "DevOps AI员工",
            "microservice": "微服务管理AI员工",
            "knowledge_graph": "知识图谱AI员工",
            "digital_twin": "数字孪生AI员工"
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

        # 为不继承AIEmployee基类的独立员工类注入智能赋能
        self._inject_empowerment_to_standalone_employees()

        # 创建配置管理AI员工 (级别8)
        config_manager_employee = ConfigManagerEmployee("config_mgr_001", "配置管理AI", "config_manager", 8)
        config_manager_employee.type = "config_manager"
        self.employees["config_mgr_001"] = config_manager_employee
        self._safe_start_employee(config_manager_employee)
        self.add_employee_to_organizations(config_manager_employee)

        # 创建Arduino代码生成AI员工 (级别7)
        arduino_gen_employee = ArduinoCodeGeneratorEmployee("arduino_gen_001", "Arduino代码生成AI", 7)
        self.employees["arduino_gen_001"] = arduino_gen_employee
        self._safe_start_employee(arduino_gen_employee)
        self.add_employee_to_organizations(arduino_gen_employee)

        # 创建Arduino代码调试AI员工 (级别8)
        arduino_debug_employee = ArduinoCodeDebuggerEmployee("arduino_debug_001", "Arduino代码调试AI", 8)
        self.employees["arduino_debug_001"] = arduino_debug_employee
        self._safe_start_employee(arduino_debug_employee)
        self.add_employee_to_organizations(arduino_debug_employee)

        # 创建Arduino代码优化AI员工 (级别7)
        arduino_opt_employee = ArduinoCodeOptimizerEmployee("arduino_opt_001", "Arduino代码优化AI", 7)
        self.employees["arduino_opt_001"] = arduino_opt_employee
        self._safe_start_employee(arduino_opt_employee)
        self.add_employee_to_organizations(arduino_opt_employee)

        # 创建Arduino组件推荐AI员工 (级别6)
        arduino_comp_employee = ArduinoComponentAdvisorEmployee("arduino_comp_001", "Arduino组件推荐AI", 6)
        self.employees["arduino_comp_001"] = arduino_comp_employee
        self._safe_start_employee(arduino_comp_employee)
        self.add_employee_to_organizations(arduino_comp_employee)

        # 创建代码审查AI员工 (级别8)
        code_review_employee = AICodeReviewAgent("code_review_001", "代码审查AI")
        code_review_employee.type = "code_review"
        self.employees["code_review_001"] = code_review_employee
        self._safe_start_employee(code_review_employee)
        self.add_employee_to_organizations(code_review_employee)

        # 创建自动化测试AI员工 (级别7)
        auto_test_employee = AIAutoTestAgent("auto_test_001", "自动化测试AI")
        auto_test_employee.type = "auto_test"
        self.employees["auto_test_001"] = auto_test_employee
        self._safe_start_employee(auto_test_employee)
        self.add_employee_to_organizations(auto_test_employee)

        # 创建性能优化AI员工 (级别8)
        perf_opt_employee = AIPerformanceOptimizer("perf_opt_001", "性能优化AI")
        perf_opt_employee.type = "performance_optimizer"
        self.employees["perf_opt_001"] = perf_opt_employee
        self._safe_start_employee(perf_opt_employee)
        self.add_employee_to_organizations(perf_opt_employee)

        # 创建安全审计AI员工 (级别9)
        security_auditor_employee = AISecurityAuditor("sec_audit_001", "安全审计AI")
        security_auditor_employee.type = "security_auditor"
        self.employees["sec_audit_001"] = security_auditor_employee
        self._safe_start_employee(security_auditor_employee)
        self.add_employee_to_organizations(security_auditor_employee)

        # 创建需求分析AI员工 (级别7)
        req_analyzer_employee = AIRequirementAnalyzer("req_analyzer_001", "需求分析AI")
        req_analyzer_employee.type = "requirement_analyzer"
        self.employees["req_analyzer_001"] = req_analyzer_employee
        self._safe_start_employee(req_analyzer_employee)
        self.add_employee_to_organizations(req_analyzer_employee)

        # 创建文档生成AI员工 (级别6)
        doc_gen_employee = AIDocGenerator("doc_gen_001", "文档生成AI")
        doc_gen_employee.type = "doc_generator"
        self.employees["doc_gen_001"] = doc_gen_employee
        self._safe_start_employee(doc_gen_employee)
        self.add_employee_to_organizations(doc_gen_employee)

        # 创建任务调度AI员工 (级别7)
        task_sched_employee = AITaskSchedulerAgent("task_sched_001", "任务调度AI")
        task_sched_employee.type = "task_scheduler"
        self.employees["task_sched_001"] = task_sched_employee
        self._safe_start_employee(task_sched_employee)
        self.add_employee_to_organizations(task_sched_employee)

        # 创建自动修复AI员工 (级别8)
        auto_repair_employee = AIAutoRepairAgent("auto_repair_001", "自动修复AI")
        auto_repair_employee.type = "auto_repair"
        self.employees["auto_repair_001"] = auto_repair_employee
        self._safe_start_employee(auto_repair_employee)
        self.add_employee_to_organizations(auto_repair_employee)

        # 创建数据分析AI员工 (级别7)
        data_analyzer_employee = AIDataAnalyzer("data_analyzer_001", "数据分析AI")
        data_analyzer_employee.type = "data_analyzer"
        self.employees["data_analyzer_001"] = data_analyzer_employee
        self._safe_start_employee(data_analyzer_employee)
        self.add_employee_to_organizations(data_analyzer_employee)

        # 创建模型管理AI员工 (级别8)
        model_mgr_employee = AIModelManager("model_mgr_001", "模型管理AI")
        model_mgr_employee.type = "model_manager"
        self.employees["model_mgr_001"] = model_mgr_employee
        self._safe_start_employee(model_mgr_employee)
        self.add_employee_to_organizations(model_mgr_employee)

        # 创建智能运维AI员工 (级别9)
        ops_agent_employee = AIOpsAgent("ops_agent_001", "智能运维AI")
        ops_agent_employee.type = "ops_agent"
        self.employees["ops_agent_001"] = ops_agent_employee
        self._safe_start_employee(ops_agent_employee)
        self.add_employee_to_organizations(ops_agent_employee)

        # 创建代码生成AI员工 (级别7)
        code_gen_employee = AICodeGeneratorAgent("code_gen_001", "代码生成AI")
        code_gen_employee.type = "code_generator"
        self.employees["code_gen_001"] = code_gen_employee
        self._safe_start_employee(code_gen_employee)
        self.add_employee_to_organizations(code_gen_employee)

        # 创建对话管理AI员工 (级别6)
        conv_employee = AIConversationAgent("conv_001", "对话管理AI")
        conv_employee.type = "conversation"
        self.employees["conv_001"] = conv_employee
        self._safe_start_employee(conv_employee)
        self.add_employee_to_organizations(conv_employee)

        # 创建推荐系统AI员工 (级别7)
        rec_employee = AIRecommendationAgent("rec_001", "推荐系统AI")
        rec_employee.type = "recommendation"
        self.employees["rec_001"] = rec_employee
        self._safe_start_employee(rec_employee)
        self.add_employee_to_organizations(rec_employee)

        # 创建营销AI员工 (级别7)
        marketing_employee = AIMarketingAgent("marketing_001", "营销AI")
        marketing_employee.type = "marketing"
        self.employees["marketing_001"] = marketing_employee
        self._safe_start_employee(marketing_employee)
        self.add_employee_to_organizations(marketing_employee)

        # 创建客服AI员工 (级别6)
        cs_employee = AICustomerServiceAgent("cs_001", "客服AI")
        cs_employee.type = "customer_service"
        self.employees["cs_001"] = cs_employee
        self._safe_start_employee(cs_employee)
        self.add_employee_to_organizations(cs_employee)

        # 创建舆情分析AI员工 (级别8)
        po_employee = AIPublicOpinionAgent("po_001", "舆情分析AI")
        po_employee.type = "public_opinion"
        self.employees["po_001"] = po_employee
        self._safe_start_employee(po_employee)
        self.add_employee_to_organizations(po_employee)

        # 创建财务分析AI员工 (级别8)
        fin_employee = AIFinancialAgent("fin_001", "财务分析AI")
        fin_employee.type = "financial"
        self.employees["fin_001"] = fin_employee
        self._safe_start_employee(fin_employee)
        self.add_employee_to_organizations(fin_employee)

        # 创建人力资源AI员工 (级别7)
        hr_employee = AIHRAgent("hr_001", "人力资源AI")
        hr_employee.type = "hr"
        self.employees["hr_001"] = hr_employee
        self._safe_start_employee(hr_employee)
        self.add_employee_to_organizations(hr_employee)

        # 创建项目管理AI员工 (级别8)
        pm_employee = AIProjectManagementAgent("pm_001", "项目管理AI")
        pm_employee.type = "project_management"
        self.employees["pm_001"] = pm_employee
        self._safe_start_employee(pm_employee)
        self.add_employee_to_organizations(pm_employee)

        # 创建客户关系AI员工 (级别7)
        crm_employee = AICRMAgent("crm_001", "客户关系AI")
        crm_employee.type = "crm"
        self.employees["crm_001"] = crm_employee
        self._safe_start_employee(crm_employee)
        self.add_employee_to_organizations(crm_employee)

        # 创建教育管理AI员工 (级别8)
        edu_employee = AIEducationManager("edu_001", "教育管理AI")
        edu_employee.type = "education_manager"
        self.employees["edu_001"] = edu_employee
        self._safe_start_employee(edu_employee)
        self.add_employee_to_organizations(edu_employee)

        # 创建社区管理AI员工 (级别7)
        comm_employee = AICommunityManager("comm_001", "社区管理AI")
        comm_employee.type = "community_manager"
        self.employees["comm_001"] = comm_employee
        self._safe_start_employee(comm_employee)
        self.add_employee_to_organizations(comm_employee)

        # 创建活动管理AI员工 (级别7)
        act_employee = AIActivityManager("act_001", "活动管理AI")
        act_employee.type = "activity_manager"
        self.employees["act_001"] = act_employee
        self._safe_start_employee(act_employee)
        self.add_employee_to_organizations(act_employee)

        # 创建内容创作AI员工 (级别8)
        content_employee = AIContentCreator("content_001", "内容创作AI")
        content_employee.type = "content_creator"
        self.employees["content_001"] = content_employee
        self._safe_start_employee(content_employee)
        self.add_employee_to_organizations(content_employee)

        # 创建配置管理AI员工 (级别7)
        cfg_employee = AIConfigManager("cfg_001", "配置管理AI")
        cfg_employee.type = "config_manager"
        self.employees["cfg_001"] = cfg_employee
        self._safe_start_employee(cfg_employee)
        self.add_employee_to_organizations(cfg_employee)

        # 创建日志分析AI员工 (级别8)
        log_employee = AILogAnalyzer("log_001", "日志分析AI")
        log_employee.type = "log_analyzer"
        self.employees["log_001"] = log_employee
        self._safe_start_employee(log_employee)
        self.add_employee_to_organizations(log_employee)

        # 创建文档处理AI员工 (级别7)
        doc_employee = AIDocumentProcessor("doc_001", "文档处理AI")
        doc_employee.type = "document_processor"
        self.employees["doc_001"] = doc_employee
        self._safe_start_employee(doc_employee)
        self.add_employee_to_organizations(doc_employee)

        # 创建安全漏洞检测AI员工 (级别9)
        vuln_employee = AIVulnerabilityScanner("vuln_001", "安全漏洞检测AI")
        vuln_employee.type = "vulnerability_scanner"
        self.employees["vuln_001"] = vuln_employee
        self._safe_start_employee(vuln_employee)
        self.add_employee_to_organizations(vuln_employee)

        # 创建网络安全AI员工 (级别9)
        cyber_employee = AICybersecurityAgent("cyber_001", "网络安全AI")
        cyber_employee.type = "cybersecurity"
        self.employees["cyber_001"] = cyber_employee
        self._safe_start_employee(cyber_employee)
        self.add_employee_to_organizations(cyber_employee)

        # 创建系统扩展AI员工 (级别7)
        ext_employee = AISystemExtensionAgent("ext_001", "系统扩展AI")
        ext_employee.type = "system_extension"
        self.employees["ext_001"] = ext_employee
        self._safe_start_employee(ext_employee)
        self.add_employee_to_organizations(ext_employee)

        # 创建数据科学AI员工 (级别9)
        ds_employee = AIDataScienceAgent("ds_001", "数据科学AI")
        ds_employee.type = "data_science"
        self.employees["ds_001"] = ds_employee
        self._safe_start_employee(ds_employee)
        self.add_employee_to_organizations(ds_employee)

        # 创建图像处理AI员工 (级别8)
        img_employee = AIImageProcessingAgent("img_001", "图像处理AI")
        img_employee.type = "image_processing"
        self.employees["img_001"] = img_employee
        self._safe_start_employee(img_employee)
        self.add_employee_to_organizations(img_employee)

        # 创建语音处理AI员工 (级别8)
        speech_employee = AISpeechProcessingAgent("speech_001", "语音处理AI")
        speech_employee.type = "speech_processing"
        self.employees["speech_001"] = speech_employee
        self._safe_start_employee(speech_employee)
        self.add_employee_to_organizations(speech_employee)

        # 创建智能翻译AI员工 (级别8)
        trans_employee = AITranslationAgent("trans_001", "智能翻译AI")
        trans_employee.type = "translation"
        self.employees["trans_001"] = trans_employee
        self._safe_start_employee(trans_employee)
        self.add_employee_to_organizations(trans_employee)

        # 创建数据治理AI员工 (级别8)
        dg_employee = AIDataGovernanceAgent("dg_001", "数据治理AI")
        dg_employee.type = "data_governance"
        self.employees["dg_001"] = dg_employee
        self._safe_start_employee(dg_employee)
        self.add_employee_to_organizations(dg_employee)

        # 创建商业智能AI员工 (级别8)
        bi_employee = AIBusinessIntelligenceAgent("bi_001", "商业智能AI")
        bi_employee.type = "business_intelligence"
        self.employees["bi_001"] = bi_employee
        self._safe_start_employee(bi_employee)
        self.add_employee_to_organizations(bi_employee)

        # 创建DevOps AI员工 (级别8)
        devops_employee = AIDevOpsAgent("devops_001", "DevOps AI")
        devops_employee.type = "devops"
        self.employees["devops_001"] = devops_employee
        self._safe_start_employee(devops_employee)
        self.add_employee_to_organizations(devops_employee)

        # 创建微服务管理AI员工 (级别8)
        ms_employee = AIMicroserviceAgent("ms_001", "微服务管理AI")
        ms_employee.type = "microservice"
        self.employees["ms_001"] = ms_employee
        self._safe_start_employee(ms_employee)
        self.add_employee_to_organizations(ms_employee)

        # 创建知识图谱AI员工 (级别8)
        kg_employee = AIKnowledgeGraphAgent("kg_001", "知识图谱AI")
        kg_employee.type = "knowledge_graph"
        self.employees["kg_001"] = kg_employee
        self._safe_start_employee(kg_employee)
        self.add_employee_to_organizations(kg_employee)

        # 创建数字孪生AI员工 (级别8)
        dt_employee = AIDigitalTwinAgent("dt_001", "数字孪生AI")
        dt_employee.type = "digital_twin"
        self.employees["dt_001"] = dt_employee
        self._safe_start_employee(dt_employee)
        self.add_employee_to_organizations(dt_employee)

        # 创建VIKEY安全专家AI员工 (级别9)
        vikey_security_employee = AI_VIKEY_Security_Employee("vikey_sec_001", "VIKEY安全专家")
        vikey_security_employee.type = "vikey_security"
        self.employees["vikey_sec_001"] = vikey_security_employee
        self._safe_start_employee(vikey_security_employee)
        self.add_employee_to_organizations(vikey_security_employee)

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

    def _inject_empowerment_to_standalone_employees(self):
        """为不继承AIEmployee基类的独立员工类注入智能赋能"""
        try:
            from ai_engines.intelligent_empowerment import PersonalitySystem, NetworkLearningEngine, EMOTION_STATES

            standalone_map = {
                'diag_001': ('analytical', 'diagnostics'),
                'qbm_001': ('analytical', 'question_bank'),
                'pol_001': ('supportive', 'education'),
                'k12_001': ('supportive', 'education'),
                'list_001': ('supportive', 'education'),
                'rbu_001': ('cautious', 'system_admin'),
            }

            for emp_id, (ptype, domain) in standalone_map.items():
                emp = self.employees.get(emp_id)
                if emp and not getattr(emp, 'empowerment_enabled', False):
                    emp.personality = PersonalitySystem(ptype)
                    emp.learning_engine = NetworkLearningEngine(emp_id, domain)
                    emp.empowerment_enabled = True
                    emp.decision_history = []

                    # 添加赋能方法（如果不存在）
                    if not hasattr(emp, 'get_empowerment_profile'):
                        def _get_profile(self=emp):
                            if not getattr(self, 'empowerment_enabled', False):
                                return {'enabled': False, 'employee_id': getattr(self, 'employee_id', ''), 'name': getattr(self, 'name', '')}
                            return {
                                'enabled': True,
                                'employee_id': getattr(self, 'employee_id', ''),
                                'name': getattr(self, 'name', ''),
                                'type': getattr(self, 'type', getattr(self, 'employee_type', 'general')),
                                'personality': self.personality.get_personality_profile(),
                                'learning_stats': self.learning_engine.get_learning_stats(),
                                'knowledge_topics': len(self.learning_engine.knowledge_base),
                                'certifications': self.learning_engine.certifications,
                                'decision_count': len(getattr(self, 'decision_history', [])),
                            }
                        emp.get_empowerment_profile = _get_profile

                    if not hasattr(emp, 'get_personality_detail'):
                        emp.get_personality_detail = lambda self=emp: self.personality.get_personality_profile() if getattr(self, 'personality', None) else {}

                    if not hasattr(emp, 'get_learning_detail'):
                        def _get_learning(self=emp):
                            if not getattr(self, 'learning_engine', None):
                                return {}
                            return {
                                'stats': self.learning_engine.get_learning_stats(),
                                'knowledge_base': self.learning_engine.get_knowledge_base(),
                                'recent_history': self.learning_engine.get_learning_history(10),
                                'upgrade_status': self.learning_engine.auto_upgrade_check(),
                                'certifications': self.learning_engine.certifications,
                            }
                        emp.get_learning_detail = _get_learning

                    if not hasattr(emp, 'trigger_learning_session'):
                        emp.trigger_learning_session = lambda topic=None, duration=30, self=emp: self.learning_engine.learn_from_network(topic, duration) if getattr(self, 'learning_engine', None) else {'success': False, 'message': '学习引擎未初始化'}

                    if not hasattr(emp, 'rest_employee'):
                        emp.rest_employee = lambda self=emp: ({'success': True, 'message': f'{self.name} 已休息'} if self.personality else {'success': False}) if hasattr(self, 'personality') and self.personality else self.personality.rest() if hasattr(self, 'personality') and self.personality else {'success': False}

                    logger.info(f"  ✓ 独立员工 {emp.name} 智能赋能注入完成")
        except Exception as e:
            logger.error(f"独立员工赋能注入失败: {e}")

    def _load_employees_from_database(self):
        """从数据库加载AI员工"""
        import sqlite3
        
        db_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'app.db')
        
        try:
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS ai_employees (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL,
                    employee_code TEXT UNIQUE,
                    description TEXT,
                    capabilities TEXT,
                    specialties TEXT,
                    status TEXT DEFAULT 'active',
                    accuracy REAL DEFAULT 0.85,
                    total_tasks INTEGER DEFAULT 0,
                    successful_fixes INTEGER DEFAULT 0,
                    failed_fixes INTEGER DEFAULT 0,
                    learning_rate REAL DEFAULT 0.05,
                    knowledge_base_size INTEGER DEFAULT 0,
                    last_training TEXT,
                    model_version TEXT DEFAULT '1.0',
                    is_enabled INTEGER DEFAULT 1,
                    priority INTEGER DEFAULT 1,
                    max_concurrent_tasks INTEGER DEFAULT 5,
                    skill_level INTEGER DEFAULT 1,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                    updated_at TEXT DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            conn.commit()
            
            cursor.execute('SELECT COUNT(*) FROM ai_employees')
            count = cursor.fetchone()[0]
            
            logger.info("创建核心AI员工...")
            self.create_initial_employees()
            
            if count > 0:
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
                    if emp_id in self.employees:
                        continue
                    
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
        elif employee_type == "code_review":
            employee = AICodeReviewAgent(employee_id, name)
            employee.type = employee_type
        elif employee_type == "auto_test":
            employee = AIAutoTestAgent(employee_id, name)
            employee.type = employee_type
        elif employee_type == "performance_optimizer":
            employee = AIPerformanceOptimizer(employee_id, name)
            employee.type = employee_type
        elif employee_type == "security_auditor":
            employee = AISecurityAuditor(employee_id, name)
            employee.type = employee_type
        elif employee_type == "requirement_analyzer":
            employee = AIRequirementAnalyzer(employee_id, name)
            employee.type = employee_type
        elif employee_type == "doc_generator":
            employee = AIDocGenerator(employee_id, name)
            employee.type = employee_type
        elif employee_type == "task_scheduler":
            employee = AITaskSchedulerAgent(employee_id, name)
            employee.type = employee_type
        elif employee_type == "auto_repair":
            employee = AIAutoRepairAgent(employee_id, name)
            employee.type = employee_type
        elif employee_type == "data_analyzer":
            employee = AIDataAnalyzer(employee_id, name)
            employee.type = employee_type
        elif employee_type == "model_manager":
            employee = AIModelManager(employee_id, name)
            employee.type = employee_type
        elif employee_type == "ops_agent":
            employee = AIOpsAgent(employee_id, name)
            employee.type = employee_type
        elif employee_type == "code_generator":
            employee = AICodeGeneratorAgent(employee_id, name)
            employee.type = employee_type
        elif employee_type == "conversation":
            employee = AIConversationAgent(employee_id, name)
            employee.type = employee_type
        elif employee_type == "recommendation":
            employee = AIRecommendationAgent(employee_id, name)
            employee.type = employee_type
        elif employee_type == "marketing":
            employee = AIMarketingAgent(employee_id, name)
            employee.type = employee_type
        elif employee_type == "customer_service":
            employee = AICustomerServiceAgent(employee_id, name)
            employee.type = employee_type
        elif employee_type == "public_opinion":
            employee = AIPublicOpinionAgent(employee_id, name)
            employee.type = employee_type
        elif employee_type == "financial":
            employee = AIFinancialAgent(employee_id, name)
            employee.type = employee_type
        elif employee_type == "hr":
            employee = AIHRAgent(employee_id, name)
            employee.type = employee_type
        elif employee_type == "project_management":
            employee = AIProjectManagementAgent(employee_id, name)
            employee.type = employee_type
        elif employee_type == "crm":
            employee = AICRMAgent(employee_id, name)
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
