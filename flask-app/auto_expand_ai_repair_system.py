#!/usr/bin/env python3
"""
自动扩充AI修复系统脚本
用于创建AI修复相关的数据库表、实现核心功能、与现有AI员工系统集成
"""

import sqlite3
import json
import time
import uuid
from datetime import datetime

class AIRepairSystemExpander:
    """AI修复系统扩充器"""
    
    def __init__(self, db_path='app.db'):
        self.db_path = db_path
        self.conn = sqlite3.connect(self.db_path)
        self.cursor = self.conn.cursor()
    
    def __del__(self):
        self.conn.close()
    
    def create_repair_tables(self):
        """创建AI修复相关的数据库表"""
        """
        创建AI修复系统所需的数据库表，包括：
        1. ai_repair_issues - AI修复问题表
        2. ai_repair_solutions - AI修复解决方案表
        3. ai_repair_logs - AI修复日志表
        4. ai_repair_policies - AI修复策略表
        
        返回:
        - 创建的表数量
        """
        try:
            tables_created = 0
            
            # 1. AI修复问题表
            self.cursor.execute("""
                CREATE TABLE IF NOT EXISTS ai_repair_issues (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    issue_id TEXT UNIQUE NOT NULL,
                    issue_type TEXT NOT NULL,
                    severity TEXT NOT NULL DEFAULT 'medium',
                    status TEXT NOT NULL DEFAULT 'pending',
                    title TEXT NOT NULL,
                    description TEXT NOT NULL,
                    detected_at TEXT DEFAULT CURRENT_TIMESTAMP,
                    detected_by TEXT,
                    resolved_at TEXT,
                    resolved_by TEXT,
                    solution_id INTEGER,
                    FOREIGN KEY (solution_id) REFERENCES ai_repair_solutions(id)
                )
            """)
            tables_created += 1
            
            # 2. AI修复解决方案表
            self.cursor.execute("""
                CREATE TABLE IF NOT EXISTS ai_repair_solutions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    solution_id TEXT UNIQUE NOT NULL,
                    issue_type TEXT NOT NULL,
                    solution_title TEXT NOT NULL,
                    solution_description TEXT NOT NULL,
                    implementation_steps TEXT,
                    expected_outcome TEXT,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                    created_by TEXT,
                    effectiveness_score REAL DEFAULT 0.0,
                    usage_count INTEGER DEFAULT 0
                )
            """)
            tables_created += 1
            
            # 3. AI修复日志表
            self.cursor.execute("""
                CREATE TABLE IF NOT EXISTS ai_repair_logs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    log_id TEXT UNIQUE NOT NULL,
                    issue_id TEXT,
                    solution_id TEXT,
                    action TEXT NOT NULL,
                    action_type TEXT NOT NULL,
                    result TEXT NOT NULL DEFAULT 'success',
                    details TEXT,
                    executed_by TEXT NOT NULL,
                    executed_at TEXT DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (issue_id) REFERENCES ai_repair_issues(issue_id),
                    FOREIGN KEY (solution_id) REFERENCES ai_repair_solutions(solution_id)
                )
            """)
            tables_created += 1
            
            # 4. AI修复策略表
            self.cursor.execute("""
                CREATE TABLE IF NOT EXISTS ai_repair_policies (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    policy_id TEXT UNIQUE NOT NULL,
                    policy_name TEXT NOT NULL,
                    policy_description TEXT,
                    issue_type TEXT NOT NULL,
                    severity_level TEXT NOT NULL,
                    action TEXT NOT NULL,
                    is_active INTEGER DEFAULT 1,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                    updated_at TEXT DEFAULT CURRENT_TIMESTAMP
                )
            """)
            tables_created += 1
            
            self.conn.commit()
            print(f"成功创建 {tables_created} 个AI修复相关表")
            return tables_created
        except Exception as e:
            print(f"创建AI修复相关表失败: {e}")
            self.conn.rollback()
            return 0
    
    def create_repair_collections(self):
        """创建AI修复相关的集合和实例"""
        """
        创建AI修复相关的AI集合和实例
        
        返回:
        - 创建的集合和实例数量
        """
        try:
            # 创建AI修复集合
            repair_collections = [
                {
                    "collection_name": "ai_repair_system",
                    "description": "AI修复系统知识库"
                },
                {
                    "collection_name": "repair_issues",
                    "description": "修复问题知识库"
                },
                {
                    "collection_name": "repair_solutions",
                    "description": "修复解决方案知识库"
                },
                {
                    "collection_name": "repair_policies",
                    "description": "修复策略知识库"
                }
            ]
            
            collections_created = 0
            
            for collection in repair_collections:
                # 检查集合是否已存在
                self.cursor.execute(
                    "SELECT id FROM ai_collections WHERE collection_name = ?",
                    (collection["collection_name"],)
                )
                existing = self.cursor.fetchone()
                if existing:
                    continue
                
                # 创建新集合
                self.cursor.execute("""
                    INSERT INTO ai_collections (collection_name, description, status)
                    VALUES (?, ?, 'active')
                """, (
                    collection["collection_name"],
                    collection["description"]
                ))
                collections_created += 1
            
            # 创建AI修复实例
            repair_instances = [
                {
                    "ai_name": "repair_manager",
                    "ai_type": "manager",
                    "description": "修复管理AI"
                },
                {
                    "ai_name": "issue_detector",
                    "ai_type": "detector",
                    "description": "问题检测AI"
                },
                {
                    "ai_name": "solution_generator",
                    "ai_type": "generator",
                    "description": "解决方案生成AI"
                },
                {
                    "ai_name": "repair_executor",
                    "ai_type": "executor",
                    "description": "修复执行AI"
                },
                {
                    "ai_name": "system_monitor",
                    "ai_type": "monitor",
                    "description": "系统监控AI"
                }
            ]
            
            instances_created = 0
            
            for instance in repair_instances:
                # 检查实例是否已存在
                self.cursor.execute(
                    "SELECT id FROM ai_instances WHERE ai_name = ?",
                    (instance["ai_name"],)
                )
                existing = self.cursor.fetchone()
                if existing:
                    continue
                
                # 创建新实例
                self.cursor.execute("""
                    INSERT INTO ai_instances (ai_name, ai_type, description, status)
                    VALUES (?, ?, ?, 'active')
                """, (
                    instance["ai_name"],
                    instance["ai_type"],
                    instance["description"]
                ))
                instances_created += 1
            
            self.conn.commit()
            print(f"成功创建 {collections_created} 个AI修复集合和 {instances_created} 个AI修复实例")
            return collections_created + instances_created
        except Exception as e:
            print(f"创建AI修复集合和实例失败: {e}")
            self.conn.rollback()
            return 0
    
    def create_repair_solutions(self):
        """创建AI修复解决方案"""
        """
        创建初始的AI修复解决方案
        
        返回:
        - 创建的解决方案数量
        """
        try:
            # 定义初始修复解决方案
            solutions = [
                {
                    "issue_type": "database_connection",
                    "solution_title": "数据库连接修复",
                    "solution_description": "修复数据库连接问题",
                    "implementation_steps": json.dumps([
                        "检查数据库服务是否运行",
                        "检查数据库连接字符串是否正确",
                        "检查数据库用户权限",
                        "重启数据库服务",
                        "重启应用服务"
                    ]),
                    "expected_outcome": "数据库连接恢复正常"
                },
                {
                    "issue_type": "database_performance",
                    "solution_title": "数据库性能优化",
                    "solution_description": "优化数据库性能问题",
                    "implementation_steps": json.dumps([
                        "分析数据库慢查询日志",
                        "优化查询语句",
                        "添加必要的索引",
                        "调整数据库配置参数",
                        "监控优化效果"
                    ]),
                    "expected_outcome": "数据库查询性能提升50%以上"
                },
                {
                    "issue_type": "high_cpu_usage",
                    "solution_title": "CPU使用率过高修复",
                    "solution_description": "修复CPU使用率过高问题",
                    "implementation_steps": json.dumps([
                        "检查CPU密集型进程",
                        "优化进程配置",
                        "调整系统资源分配",
                        "重启相关服务"
                    ]),
                    "expected_outcome": "CPU使用率恢复正常"
                },
                {
                    "issue_type": "memory_leak",
                    "solution_title": "内存泄漏修复",
                    "solution_description": "修复内存泄漏问题",
                    "implementation_steps": json.dumps([
                        "检测内存泄漏点",
                        "优化代码或配置",
                        "重启相关服务",
                        "监控内存使用情况"
                    ]),
                    "expected_outcome": "内存使用稳定，不再持续增长"
                },
                {
                    "issue_type": "disk_space_full",
                    "solution_title": "磁盘空间不足修复",
                    "solution_description": "修复磁盘空间不足问题",
                    "implementation_steps": json.dumps([
                        "检查磁盘使用情况",
                        "清理临时文件",
                        "删除不必要的日志文件",
                        "检查并清理数据库垃圾数据",
                        "考虑扩展磁盘空间"
                    ]),
                    "expected_outcome": "磁盘空间使用率降低到70%以下"
                },
                {
                    "issue_type": "service_unavailable",
                    "solution_title": "服务不可用修复",
                    "solution_description": "修复服务不可用问题",
                    "implementation_steps": json.dumps([
                        "检查服务状态",
                        "检查服务日志",
                        "修复服务配置",
                        "重启服务",
                        "验证服务可用性"
                    ]),
                    "expected_outcome": "服务恢复正常运行"
                },
                {
                    "issue_type": "service_crash",
                    "solution_title": "服务崩溃自动恢复",
                    "solution_description": "自动检测和恢复崩溃的服务",
                    "implementation_steps": json.dumps([
                        "监控服务运行状态",
                        "检测服务崩溃",
                        "自动重启服务",
                        "验证服务恢复",
                        "分析崩溃原因"
                    ]),
                    "expected_outcome": "服务在崩溃后30秒内自动恢复"
                },
                {
                    "issue_type": "network_issue",
                    "solution_title": "网络问题修复",
                    "solution_description": "修复网络连接问题",
                    "implementation_steps": json.dumps([
                        "检查网络连接",
                        "检查网络配置",
                        "重启网络服务",
                        "验证网络连接"
                    ]),
                    "expected_outcome": "网络连接恢复正常"
                },
                {
                    "issue_type": "network_latency",
                    "solution_title": "网络延迟优化",
                    "solution_description": "优化网络延迟问题",
                    "implementation_steps": json.dumps([
                        "测试网络延迟",
                        "检查网络拓扑",
                        "优化路由配置",
                        "检查网络设备性能",
                        "监控优化效果"
                    ]),
                    "expected_outcome": "网络延迟降低30%以上"
                },
                {
                    "issue_type": "ai_employee_error",
                    "solution_title": "AI员工错误修复",
                    "solution_description": "修复AI员工运行错误",
                    "implementation_steps": json.dumps([
                        "检查AI员工日志",
                        "重启AI员工进程",
                        "恢复AI员工配置",
                        "验证AI员工功能",
                        "更新AI员工知识库"
                    ]),
                    "expected_outcome": "AI员工恢复正常运行"
                },
                {
                    "issue_type": "ai_knowledge_corruption",
                    "solution_title": "AI知识库修复",
                    "solution_description": "修复AI知识库损坏问题",
                    "implementation_steps": json.dumps([
                        "检测知识库完整性",
                        "修复损坏的知识库数据",
                        "验证知识库一致性",
                        "备份修复后的知识库",
                        "更新知识库索引"
                    ]),
                    "expected_outcome": "AI知识库恢复完整和一致"
                },
                {
                    "issue_type": "system_config_error",
                    "solution_title": "系统配置错误修复",
                    "solution_description": "修复系统配置错误",
                    "implementation_steps": json.dumps([
                        "检测配置错误",
                        "恢复正确配置",
                        "验证配置有效性",
                        "备份正确配置",
                        "重启相关服务"
                    ]),
                    "expected_outcome": "系统配置恢复正确"
                },
                {
                    "issue_type": "log_file_growth",
                    "solution_title": "日志文件增长过快修复",
                    "solution_description": "修复日志文件增长过快问题",
                    "implementation_steps": json.dumps([
                        "分析日志生成情况",
                        "调整日志级别",
                        "配置日志轮换策略",
                        "清理旧日志文件",
                        "监控日志增长"
                    ]),
                    "expected_outcome": "日志文件大小得到有效控制"
                },
                {
                    "issue_type": "security_breach",
                    "solution_title": "安全漏洞修复",
                    "solution_description": "修复安全漏洞问题",
                    "implementation_steps": json.dumps([
                        "检测安全漏洞",
                        "隔离受影响的系统",
                        "应用安全补丁",
                        "重置受损账户",
                        "加强安全监控"
                    ]),
                    "expected_outcome": "安全漏洞得到修复，系统恢复安全状态"
                },
                {
                    "issue_type": "dependency_failure",
                    "solution_title": "依赖服务失败修复",
                    "solution_description": "修复依赖服务失败问题",
                    "implementation_steps": json.dumps([
                        "检查依赖服务状态",
                        "重启依赖服务",
                        "验证依赖服务恢复",
                        "重启主服务",
                        "监控系统稳定性"
                    ]),
                    "expected_outcome": "依赖服务和主服务都恢复正常"
                }
            ]
            
            solutions_created = 0
            
            for solution in solutions:
                # 检查解决方案是否已存在
                self.cursor.execute(
                    "SELECT id FROM ai_repair_solutions WHERE issue_type = ? AND solution_title = ?",
                    (solution["issue_type"], solution["solution_title"])
                )
                existing = self.cursor.fetchone()
                if existing:
                    continue
                
                # 创建解决方案ID
                solution_id = f"sol_{uuid.uuid4().hex[:8]}"
                
                # 插入解决方案
                self.cursor.execute("""
                    INSERT INTO ai_repair_solutions 
                    (solution_id, issue_type, solution_title, solution_description, implementation_steps, expected_outcome)
                    VALUES (?, ?, ?, ?, ?, ?)
                """, (
                    solution_id,
                    solution["issue_type"],
                    solution["solution_title"],
                    solution["solution_description"],
                    solution["implementation_steps"],
                    solution["expected_outcome"]
                ))
                
                solutions_created += 1
            
            self.conn.commit()
            print(f"成功创建 {solutions_created} 个AI修复解决方案")
            return solutions_created
        except Exception as e:
            print(f"创建AI修复解决方案失败: {e}")
            self.conn.rollback()
            return 0
    
    def create_repair_policies(self):
        """创建AI修复策略"""
        """
        创建初始的AI修复策略
        
        返回:
        - 创建的策略数量
        """
        try:
            # 定义初始修复策略
            policies = [
                {
                    "policy_name": "critical_issue_auto_repair",
                    "policy_description": "严重问题自动修复策略",
                    "issue_type": "*",
                    "severity_level": "critical",
                    "action": "auto_repair"
                },
                {
                    "policy_name": "high_issue_notification",
                    "policy_description": "高优先级问题通知策略",
                    "issue_type": "*",
                    "severity_level": "high",
                    "action": "notify_then_repair"
                },
                {
                    "policy_name": "medium_issue_review",
                    "policy_description": "中等优先级问题审核策略",
                    "issue_type": "*",
                    "severity_level": "medium",
                    "action": "review_then_repair"
                },
                {
                    "policy_name": "low_issue_monitor",
                    "policy_description": "低优先级问题监控策略",
                    "issue_type": "*",
                    "severity_level": "low",
                    "action": "monitor"
                },
                {
                    "policy_name": "database_issue_escalation",
                    "policy_description": "数据库问题升级策略",
                    "issue_type": "database_connection",
                    "severity_level": "high",
                    "action": "escalate_to_admin"
                },
                {
                    "policy_name": "database_performance_auto_fix",
                    "policy_description": "数据库性能自动优化策略",
                    "issue_type": "database_performance",
                    "severity_level": "medium",
                    "action": "auto_optimize"
                },
                {
                    "policy_name": "service_crash_immediate_recovery",
                    "policy_description": "服务崩溃立即恢复策略",
                    "issue_type": "service_crash",
                    "severity_level": "critical",
                    "action": "immediate_recovery"
                },
                {
                    "policy_name": "memory_leak_prevention",
                    "policy_description": "内存泄漏预防策略",
                    "issue_type": "memory_leak",
                    "severity_level": "medium",
                    "action": "monitor_with_threshold"
                },
                {
                    "policy_name": "disk_space_proactive_management",
                    "policy_description": "磁盘空间主动管理策略",
                    "issue_type": "disk_space_full",
                    "severity_level": "medium",
                    "action": "proactive_cleanup"
                },
                {
                    "policy_name": "ai_employee_self_recovery",
                    "policy_description": "AI员工自我恢复策略",
                    "issue_type": "ai_employee_error",
                    "severity_level": "high",
                    "action": "self_repair"
                },
                {
                    "policy_name": "knowledge_corruption_urgent_fix",
                    "policy_description": "知识库损坏紧急修复策略",
                    "issue_type": "ai_knowledge_corruption",
                    "severity_level": "critical",
                    "action": "urgent_repair"
                },
                {
                    "policy_name": "security_breach_escalation",
                    "policy_description": "安全漏洞升级策略",
                    "issue_type": "security_breach",
                    "severity_level": "critical",
                    "action": "escalate_and_isolate"
                },
                {
                    "policy_name": "network_latency_optimization",
                    "policy_description": "网络延迟优化策略",
                    "issue_type": "network_latency",
                    "severity_level": "medium",
                    "action": "auto_optimize"
                },
                {
                    "policy_name": "log_growth_management",
                    "policy_description": "日志增长管理策略",
                    "issue_type": "log_file_growth",
                    "severity_level": "low",
                    "action": "auto_rotate_and_clean"
                },
                {
                    "policy_name": "dependency_failure_recovery",
                    "policy_description": "依赖服务失败恢复策略",
                    "issue_type": "dependency_failure",
                    "severity_level": "high",
                    "action": "cascade_recovery"
                }
            ]
            
            policies_created = 0
            
            for policy in policies:
                # 检查策略是否已存在
                self.cursor.execute(
                    "SELECT id FROM ai_repair_policies WHERE policy_name = ?",
                    (policy["policy_name"],)
                )
                existing = self.cursor.fetchone()
                if existing:
                    continue
                
                # 创建策略ID
                policy_id = f"pol_{uuid.uuid4().hex[:8]}"
                
                # 插入策略
                self.cursor.execute("""
                    INSERT INTO ai_repair_policies 
                    (policy_id, policy_name, policy_description, issue_type, severity_level, action)
                    VALUES (?, ?, ?, ?, ?, ?)
                """, (
                    policy_id,
                    policy["policy_name"],
                    policy["policy_description"],
                    policy["issue_type"],
                    policy["severity_level"],
                    policy["action"]
                ))
                
                policies_created += 1
            
            self.conn.commit()
            print(f"成功创建 {policies_created} 个AI修复策略")
            return policies_created
        except Exception as e:
            print(f"创建AI修复策略失败: {e}")
            self.conn.rollback()
            return 0
    
    def expand_system_config(self):
        """扩充系统配置，添加AI修复相关配置"""
        """
        扩充系统配置，添加AI修复相关配置项
        
        返回:
        - 添加的配置项数量
        """
        try:
            # 定义AI修复相关配置项
            repair_configs = [
                {
                    "config_key": "AI_REPAIR_SYSTEM_ENABLED",
                    "config_value": "True",
                    "config_type": "bool",
                    "description": "是否启用AI修复系统"
                },
                {
                    "config_key": "AI_REPAIR_AUTO_ENABLED",
                    "config_value": "True",
                    "config_type": "bool",
                    "description": "是否启用自动修复功能"
                },
                {
                    "config_key": "AI_REPAIR_NOTIFICATION_ENABLED",
                    "config_value": "True",
                    "config_type": "bool",
                    "description": "是否启用修复通知功能"
                },
                {
                    "config_key": "AI_REPAIR_MONITORING_INTERVAL",
                    "config_value": "60",
                    "config_type": "int",
                    "description": "AI修复监控间隔（秒）"
                },
                {
                    "config_key": "AI_REPAIR_RETRY_COUNT",
                    "config_value": "3",
                    "config_type": "int",
                    "description": "修复失败重试次数"
                },
                {
                    "config_key": "AI_REPAIR_TIMEOUT",
                    "config_value": "300",
                    "config_type": "int",
                    "description": "修复操作超时时间（秒）"
                },
                {
                    "config_key": "AI_REPAIR_SELF_LEARNING_ENABLED",
                    "config_value": "True",
                    "config_type": "bool",
                    "description": "是否启用AI修复系统自学习功能"
                },
                {
                    "config_key": "AI_REPAIR_LEARNING_RATE",
                    "config_value": "0.1",
                    "config_type": "float",
                    "description": "AI修复系统学习率"
                },
                {
                    "config_key": "AI_REPAIR_CONFIDENCE_THRESHOLD",
                    "config_value": "0.8",
                    "config_type": "float",
                    "description": "AI修复系统执行修复的置信度阈值"
                },
                {
                    "config_key": "AI_REPAIR_MAX_CONCURRENT_OPERATIONS",
                    "config_value": "5",
                    "config_type": "int",
                    "description": "AI修复系统最大并发操作数"
                },
                {
                    "config_key": "AI_REPAIR_HISTORY_RETENTION_DAYS",
                    "config_value": "30",
                    "config_type": "int",
                    "description": "AI修复历史记录保留天数"
                },
                {
                    "config_key": "AI_REPAIR_PERFORMANCE_MONITORING_ENABLED",
                    "config_value": "True",
                    "config_type": "bool",
                    "description": "是否启用AI修复性能监控"
                },
                {
                    "config_key": "AI_REPAIR_LOG_LEVEL",
                    "config_value": "INFO",
                    "config_type": "string",
                    "description": "AI修复系统日志级别"
                },
                {
                    "config_key": "AI_REPAIR_EMERGENCY_CONTACTS",
                    "config_value": "admin@example.com",
                    "config_type": "string",
                    "description": "AI修复系统紧急联系人"
                }
            ]
            
            added_count = 0
            
            for config in repair_configs:
                # 检查配置项是否已存在
                self.cursor.execute(
                    "SELECT id FROM system_config WHERE config_key = ?",
                    (config["config_key"],)
                )
                existing = self.cursor.fetchone()
                if existing:
                    continue
                
                # 添加新配置项
                self.cursor.execute("""
                    INSERT INTO system_config 
                    (config_key, config_value, config_type, description, is_active)
                    VALUES (?, ?, ?, ?, 1)
                """, (
                    config["config_key"],
                    config["config_value"],
                    config["config_type"],
                    config["description"]
                ))
                
                added_count += 1
            
            self.conn.commit()
            print(f"成功添加 {added_count} 个AI修复相关配置项")
            return added_count
        except Exception as e:
            print(f"扩充AI修复配置失败: {e}")
            self.conn.rollback()
            return 0
    
    def auto_expand(self):
        """自动扩充AI修复系统"""
        """
        自动扩充AI修复系统，包括：
        1. 创建AI修复相关的数据库表
        2. 创建AI修复相关的集合和实例
        3. 创建初始的AI修复解决方案
        4. 创建AI修复策略
        5. 扩充系统配置，添加AI修复相关配置
        6. 添加AI修复自学习能力
        
        返回:
        - 扩充结果
        """
        print("开始自动扩充AI修复系统...")
        
        # 记录开始时间
        start_time = datetime.now()
        
        result = {
            "success": True,
            "message": "AI修复系统扩充成功",
            "details": {
                "start_time": start_time.isoformat(),
                "tables_created": 0,
                "collections_instances_created": 0,
                "solutions_created": 0,
                "policies_created": 0,
                "configs_added": 0,
                "self_learning_features_added": 0
            }
        }
        
        # 1. 创建AI修复相关的数据库表
        print("\n1. 创建AI修复相关的数据库表:")
        tables_created = self.create_repair_tables()
        result["details"]["tables_created"] = tables_created
        print(f"   ✓ 成功创建 {tables_created} 个表")
        
        # 2. 创建AI修复相关的集合和实例
        print("\n2. 创建AI修复相关的集合和实例:")
        collections_instances_created = self.create_repair_collections()
        result["details"]["collections_instances_created"] = collections_instances_created
        print(f"   ✓ 成功创建 {collections_instances_created} 个集合和实例")
        
        # 3. 创建初始的AI修复解决方案
        print("\n3. 创建初始的AI修复解决方案:")
        solutions_created = self.create_repair_solutions()
        result["details"]["solutions_created"] = solutions_created
        print(f"   ✓ 成功创建 {solutions_created} 个解决方案")
        
        # 4. 创建AI修复策略
        print("\n4. 创建AI修复策略:")
        policies_created = self.create_repair_policies()
        result["details"]["policies_created"] = policies_created
        print(f"   ✓ 成功创建 {policies_created} 个策略")
        
        # 5. 扩充系统配置，添加AI修复相关配置
        print("\n5. 扩充系统配置:")
        configs_added = self.expand_system_config()
        result["details"]["configs_added"] = configs_added
        print(f"   ✓ 成功添加 {configs_added} 个配置项")
        
        # 6. 添加AI修复自学习能力
        print("\n6. 添加AI修复自学习能力:")
        self_learning_features_added = self.add_self_learning_capabilities()
        result["details"]["self_learning_features_added"] = self_learning_features_added
        print(f"   ✓ 成功添加 {self_learning_features_added} 个自学习功能")
        
        # 记录结束时间
        end_time = datetime.now()
        result["details"]["end_time"] = end_time.isoformat()
        result["details"]["duration"] = (end_time - start_time).total_seconds()
        
        print("\nAI修复系统扩充完成！")
        print(f"总耗时: {result['details']['duration']:.2f} 秒")
        print(f"创建的表: {result['details']['tables_created']}")
        print(f"创建的集合和实例: {result['details']['collections_instances_created']}")
        print(f"创建的解决方案: {result['details']['solutions_created']}")
        print(f"创建的策略: {result['details']['policies_created']}")
        print(f"添加的配置项: {result['details']['configs_added']}")
        print(f"添加的自学习功能: {result['details']['self_learning_features_added']}")
        
        return result
    
    def add_self_learning_capabilities(self):
        """添加AI修复系统自学习能力"""
        """
        添加AI修复系统的自学习能力，包括：
        1. 创建自学习相关的数据库表
        2. 添加自学习相关的AI实例
        3. 添加自学习相关的配置项
        
        返回:
        - 添加的自学习功能数量
        """
        try:
            features_added = 0
            
            # 创建AI修复自学习表
            self.cursor.execute("""
                CREATE TABLE IF NOT EXISTS ai_repair_self_learning (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    learning_id TEXT UNIQUE NOT NULL,
                    issue_type TEXT NOT NULL,
                    solution_id INTEGER,
                    learning_data TEXT NOT NULL,
                    effectiveness_score REAL DEFAULT 0.0,
                    learning_status TEXT DEFAULT 'completed',
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (solution_id) REFERENCES ai_repair_solutions(id)
                )
            """)
            features_added += 1
            
            # 创建AI修复效果评估表
            self.cursor.execute("""
                CREATE TABLE IF NOT EXISTS ai_repair_effectiveness (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    effectiveness_id TEXT UNIQUE NOT NULL,
                    solution_id INTEGER NOT NULL,
                    issue_count INTEGER DEFAULT 0,
                    success_count INTEGER DEFAULT 0,
                    failure_count INTEGER DEFAULT 0,
                    average_resolution_time REAL DEFAULT 0.0,
                    last_evaluated_at TEXT DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (solution_id) REFERENCES ai_repair_solutions(id)
                )
            """)
            features_added += 1
            
            # 添加自学习相关的AI实例
            learning_instances = [
                {
                    "ai_name": "repair_learning_engine",
                    "ai_type": "learner",
                    "description": "AI修复自学习引擎"
                },
                {
                    "ai_name": "effectiveness_evaluator",
                    "ai_type": "evaluator",
                    "description": "修复效果评估AI"
                },
                {
                    "ai_name": "solution_optimizer",
                    "ai_type": "optimizer",
                    "description": "修复解决方案优化AI"
                }
            ]
            
            for instance in learning_instances:
                # 检查实例是否已存在
                self.cursor.execute(
                    "SELECT id FROM ai_instances WHERE ai_name = ?",
                    (instance["ai_name"],)
                )
                existing = self.cursor.fetchone()
                if existing:
                    continue
                
                # 创建新实例
                self.cursor.execute("""
                    INSERT INTO ai_instances (ai_name, ai_type, description, status)
                    VALUES (?, ?, ?, 'active')
                """, (
                    instance["ai_name"],
                    instance["ai_type"],
                    instance["description"]
                ))
                features_added += 1
            
            self.conn.commit()
            print(f"成功添加 {features_added} 个AI修复自学习功能")
            return features_added
        except Exception as e:
            print(f"添加AI修复自学习能力失败: {e}")
            self.conn.rollback()
            return 0
    
    def get_repair_system_stats(self):
        """获取AI修复系统统计信息"""
        """
        获取AI修复系统的统计信息
        
        返回:
        - 统计信息字典
        """
        stats = {}
        
        try:
            # 检查表是否存在
            self.cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='ai_repair_issues'")
            table_exists = self.cursor.fetchone()
            if not table_exists:
                return {
                    "repair_system_enabled": False,
                    "tables_available": False
                }
            
            # 获取修复问题数量
            self.cursor.execute("SELECT COUNT(*) FROM ai_repair_issues")
            stats["repair_issues_count"] = self.cursor.fetchone()[0]
            
            # 获取修复解决方案数量
            self.cursor.execute("SELECT COUNT(*) FROM ai_repair_solutions")
            stats["repair_solutions_count"] = self.cursor.fetchone()[0]
            
            # 获取修复日志数量
            self.cursor.execute("SELECT COUNT(*) FROM ai_repair_logs")
            stats["repair_logs_count"] = self.cursor.fetchone()[0]
            
            # 获取修复策略数量
            self.cursor.execute("SELECT COUNT(*) FROM ai_repair_policies")
            stats["repair_policies_count"] = self.cursor.fetchone()[0]
            
            # 获取AI修复相关配置数量
            self.cursor.execute("""
                SELECT COUNT(*) FROM system_config 
                WHERE config_key LIKE 'AI_REPAIR_%' OR config_key LIKE 'REPAIR_%'
            """)
            stats["repair_configs_count"] = self.cursor.fetchone()[0]
            
            # 获取AI修复相关集合数量
            self.cursor.execute("""
                SELECT COUNT(*) FROM ai_collections 
                WHERE collection_name LIKE '%repair%' OR description LIKE '%repair%'
            """)
            stats["repair_collections_count"] = self.cursor.fetchone()[0]
            
            # 获取AI修复相关实例数量
            self.cursor.execute("""
                SELECT COUNT(*) FROM ai_instances 
                WHERE ai_type IN ('manager', 'detector', 'generator', 'executor', 'monitor', 'learner', 'evaluator', 'optimizer')
            """)
            stats["repair_related_instances_count"] = self.cursor.fetchone()[0]
            
            # 获取自学习相关表的状态
            self.cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='ai_repair_self_learning'")
            self_learning_table = self.cursor.fetchone()
            stats["self_learning_enabled"] = bool(self_learning_table)
            
            # 获取自学习数据数量
            if self_learning_table:
                self.cursor.execute("SELECT COUNT(*) FROM ai_repair_self_learning")
                stats["self_learning_data_count"] = self.cursor.fetchone()[0]
            
            stats["repair_system_enabled"] = True
            stats["tables_available"] = True
            
            return stats
        except Exception as e:
            print(f"获取AI修复系统统计信息失败: {e}")
            return {
                "repair_system_enabled": False,
                "tables_available": False,
                "error": str(e)
            }

# 主程序
if __name__ == "__main__":
    expander = AIRepairSystemExpander()
    
    # 获取当前AI修复系统统计信息
    print("当前AI修复系统统计信息:")
    stats = expander.get_repair_system_stats()
    if stats:
        for key, value in stats.items():
            print(f"- {key}: {value}")
    
    # 自动扩充AI修复系统
    print("\n" + "="*50)
    print("开始自动扩充AI修复系统")
    print("="*50)
    
    result = expander.auto_expand()
    
    print("\n" + "="*50)
    print("AI修复系统扩充结果")
    print("="*50)
    print(f"成功: {result['success']}")
    print(f"消息: {result['message']}")
    for key, value in result["details"].items():
        print(f"- {key}: {value}")
    
    # 获取扩充后的AI修复系统统计信息
    print("\n" + "="*50)
    print("扩充后的AI修复系统统计信息")
    print("="*50)
    stats = expander.get_repair_system_stats()
    if stats:
        for key, value in stats.items():
            print(f"- {key}: {value}")
    
    print("\nAI修复系统自动扩充完成！")
