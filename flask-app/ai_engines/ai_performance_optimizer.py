#!/usr/bin/env python3
"""AI性能优化Agent"""

import os
import re
import logging
import time
import psutil
import json
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any
from ai_engines.ai_employee_system import AIEmployee

logger = logging.getLogger(__name__)

class AIPerformanceOptimizer(AIEmployee):
    """AI性能优化Agent"""

    def __init__(self, employee_id: str, name: str = "AI性能优化专家"):
        super().__init__(employee_id, name, 'performance_optimizer', 8)
        self.skills = [
            '性能监控', '性能分析', '代码优化',
            '数据库优化', '缓存策略', '负载均衡',
            '资源管理', '性能测试', '性能报告'
        ]
        self.optimization_history = []
        self.total_optimizations = 0
        self.total_savings = 0
        # 加载rules文件夹下所有规则约束，本地优化全程遵守规范
        self.project_rules = self._load_all_rules_from_rules_folder()

    def _load_all_rules_from_rules_folder(self) -> List[Dict[str, Any]]:
        """加载rules目录下所有规则规范约束"""
        rules = []
        rules_dir = Path("rules")
        if not rules_dir.exists() or not rules_dir.is_dir():
            logger.warning("rules文件夹不存在，将使用默认性能优化规则")
            return rules
        for rule_file in rules_dir.rglob("*.json"):
            try:
                with open(rule_file, "r", encoding="utf-8") as f:
                    rule_content = json.load(f)
                    if isinstance(rule_content, list):
                        rules.extend(rule_content)
                    elif isinstance(rule_content, dict):
                        rules.append(rule_content)
                logger.info(f"成功加载规则文件: {rule_file.name}")
            except Exception as e:
                logger.error(f"加载规则文件{rule_file.name}失败: {str(e)}")
        return rules

    def _check_code_compliance_with_rules(self, code: str) -> tuple[bool, List[str]]:
        """校验代码是否符合rules文件夹下所有约束规范"""
        violation_messages = []
        for rule in self.project_rules:
            # 规则类型：禁止模式校验
            if rule.get("type") == "forbidden_pattern" and "pattern" in rule:
                if re.search(rule["pattern"], code, flags=re.MULTILINE | re.DOTALL):
                    violation_messages.append(f"违反规则[{rule.get('name', '未命名规则')}]: {rule.get('description', '未描述违规')}")
            # 规则类型：必须存在模式校验
            if rule.get("type") == "required_pattern" and "pattern" in rule:
                if not re.search(rule["pattern"], code, flags=re.MULTILINE | re.DOTALL):
                    violation_messages.append(f"违反规则[{rule.get('name', '未命名规则')}]: 缺少必需内容 {rule.get('description', '未描述要求')}")
        return len(violation_messages) == 0, violation_messages

    def monitor_system(self) -> Dict[str, Any]:
        """监控系统性能"""
        cpu_percent = psutil.cpu_percent(interval=1)
        memory = psutil.virtual_memory()
        disk = psutil.disk_usage('/')
        network = psutil.net_io_counters()

        return {
            'cpu': {
                'percent': cpu_percent,
                'cores': psutil.cpu_count(),
                'frequency': psutil.cpu_freq().current if psutil.cpu_freq() else 0
            },
            'memory': {
                'total': round(memory.total / 1024 / 1024 / 1024, 2),
                'used': round(memory.used / 1024 / 1024 / 1024, 2),
                'available': round(memory.available / 1024 / 1024 / 1024, 2),
                'percent': memory.percent
            },
            'disk': {
                'total': round(disk.total / 1024 / 1024 / 1024, 2),
                'used': round(disk.used / 1024 / 1024 / 1024, 2),
                'free': round(disk.free / 1024 / 1024 / 1024, 2),
                'percent': disk.percent
            },
            'network': {
                'bytes_sent': round(network.bytes_sent / 1024 / 1024, 2),
                'bytes_recv': round(network.bytes_recv / 1024 / 1024, 2),
                'packets_sent': network.packets_sent,
                'packets_recv': network.packets_recv
            },
            'processes': len(psutil.pids()),
            'timestamp': datetime.now().isoformat()
        }

    def analyze_performance(self, code: str) -> Dict[str, Any]:
        """分析代码性能问题，同时校验符合rules文件夹规范"""
        issues = []
        # 先校验规则合规性
        is_compliant, violations = self._check_code_compliance_with_rules(code)
        for v in violations:
            issues.append({
                'category': 'rule_compliance',
                'severity': 'critical',
                'description': v,
                'suggestion': '修改代码满足rules文件夹下对应规范要求'
            })

        perf_patterns = [
            (r'\b(list|dict|set)\(\)', '使用空构造函数', 'memory', 'low', '使用字面量[] {} set()'),
            (r'\bstr\(\)', '使用str()转换', 'cpu', 'low', '考虑直接字符串操作'),
            (r'\bint\(\)', '使用int()转换', 'cpu', 'low', '考虑直接数值操作'),
            (r'\bfloat\(\)', '使用float()转换', 'cpu', 'low', '考虑直接浮点操作'),
            (r'\bmap\(|filter\(|reduce\(', '使用高阶函数', 'cpu', 'medium', '考虑列表推导式'),
            (r'\bsorted\(', '使用sorted()', 'cpu', 'medium', '考虑原地排序'),
            (r'\breversed\(', '使用reversed()', 'memory', 'low', '考虑索引访问'),
            (r'\benumerate\(', '使用enumerate()', 'memory', 'low', '考虑直接range'),
            (r'\bzip\(', '使用zip()', 'memory', 'medium', '注意内存使用'),
            (r'\bslice\(', '使用slice()', 'memory', 'low', '考虑直接切片'),
        ]

        for pattern, description, category, severity, suggestion in perf_patterns:
            if re.search(pattern, code):
                issues.append({
                    'category': category,
                    'severity': severity,
                    'description': description,
                    'suggestion': suggestion
                })

        return {
            'total_issues': len(issues),
            'issues': issues,
            'optimization_score': max(0, 100 - len(issues) * 5),
            'rule_compliant': is_compliant,
            'timestamp': datetime.now().isoformat()
        }

    def optimize_code(self, code: str) -> Dict[str, Any]:
        """优化代码，全程遵守rules文件夹下所有规则约束"""
        optimizations = []
        original_code = code
        optimized_code = code

        # 先做规则合规性校验，原始代码违规的话优先修复规则要求
        is_original_compliant, original_violations = self._check_code_compliance_with_rules(original_code)
        if not is_original_compliant:
            logger.info("原始代码存在rules规范违规项，优化过程优先保证符合规则要求")

        # 执行性能优化，每步优化后校验规则合规性
        temp_code = re.sub(r'\b(list)\(\)', '[]', optimized_code)
        if self._check_code_compliance_with_rules(temp_code)[0]:
            optimized_code = temp_code
            optimizations.append('将list()替换为[]')

        temp_code = re.sub(r'\b(dict)\(\)', '{}', optimized_code)
        if self._check_code_compliance_with_rules(temp_code)[0]:
            optimized_code = temp_code
            optimizations.append('将dict()替换为{}')

        # 注: set() 无空字面量等价写法 ({} 是 dict), 不做替换

        return {
            'total_optimizations': len(optimizations),
            'optimizations': optimizations,
            'optimized_code': optimized_code,
            'timestamp': datetime.now().isoformat()
        }
