#!/usr/bin/env python3
"""AI安全审计Agent"""

import os
import re
import logging
import json
from datetime import datetime
from typing import Dict, List, Any
from ai_engines.ai_employee_system import AIEmployee

logger = logging.getLogger(__name__)

class AISecurityAuditor(AIEmployee):
    """AI安全审计Agent"""
    
    def __init__(self, employee_id: str, name: str = "AI安全审计专家"):
        super().__init__(employee_id, name, 'security_auditor', 9)
        self.skills = [
            '安全漏洞检测', '代码安全审计', '权限检查',
            '敏感信息扫描', 'SQL注入检测', 'XSS检测',
            '认证安全', '授权安全', '安全合规检查'
        ]
        self.audit_history = []
        self.total_audits = 0
        self.total_vulnerabilities = 0
        self.severity_levels = ['critical', 'high', 'medium', 'low', 'info']
    
    def audit_code(self, code: str, file_path: str = "") -> Dict[str, Any]:
        """审计代码安全"""
        vulnerabilities = []
        
        vulnerabilities.extend(self._detect_sql_injection(code))
        vulnerabilities.extend(self._detect_xss(code))
        vulnerabilities.extend(self._detect_sensitive_data(code))
        vulnerabilities.extend(self._detect_auth_issues(code))
        vulnerabilities.extend(self._detect_access_control(code))
        vulnerabilities.extend(self._detect_insecure_dependencies(code))
        
        self.total_audits += 1
        self.total_vulnerabilities += len(vulnerabilities)
        
        audit_result = {
            'file_path': file_path,
            'total_vulnerabilities': len(vulnerabilities),
            'vulnerabilities': vulnerabilities,
            'summary': self._generate_summary(vulnerabilities),
            'timestamp': datetime.now().isoformat()
        }
        
        self.audit_history.append(audit_result)
        return audit_result
    
    def _detect_sql_injection(self, code: str) -> List[Dict]:
        """检测SQL注入"""
        issues = []
        
        sql_patterns = [
            (r'sql\s*=\s*f?"', 'f-string SQL拼接', 'critical'),
            (r'sql\s*=\s*".*%\s*s', '字符串格式化SQL', 'critical'),
            (r'sql\s*=\s*".*\+\s*', '字符串拼接SQL', 'critical'),
            (r'execute\([^)]*\+', '动态SQL执行', 'critical'),
            (r'cursor\.execute\([^)]*%', '参数化查询缺失', 'high'),
        ]
        
        for pattern, description, severity in sql_patterns:
            if re.search(pattern, code):
                issues.append({
                    'type': 'sql_injection',
                    'severity': severity,
                    'description': description,
                    'suggestion': '使用参数化查询或ORM框架'
                })
        
        return issues
    
    def _detect_xss(self, code: str) -> List[Dict]:
        """检测XSS攻击"""
        issues = []
        
        xss_patterns = [
            (r'return\s*render_template\([^)]*\+', '模板渲染拼接', 'high'),
            (r'return\s*jsonify\([^)]*\+', 'JSON响应拼接', 'medium'),
            (r'<[^>]*\{\{.*\}\}', '未转义模板变量', 'high'),
            (r'innerHTML\s*=', '使用innerHTML', 'high'),
            (r'document\.write\(', '使用document.write', 'high'),
        ]
        
        for pattern, description, severity in xss_patterns:
            if re.search(pattern, code):
                issues.append({
                    'type': 'xss',
                    'severity': severity,
                    'description': description,
                    'suggestion': '使用模板转义或HTML转义函数'
                })
        
        return issues
    
    def _detect_sensitive_data(self, code: str) -> List[Dict]:
        """检测敏感信息泄露"""
        issues = []
        
        sensitive_patterns = [
            (r'password\s*=\s*["\'][^"\']+["\']', '硬编码密码', 'critical'),
            (r'secret\s*=\s*["\'][^"\']+["\']', '硬编码密钥', 'critical'),
            (r'token\s*=\s*["\'][^"\']+["\']', '硬编码Token', 'critical'),
            (r'api[_-]?key\s*=\s*["\'][^"\']+["\']', '硬编码API密钥', 'critical'),
            (r'access[_-]?key\s*=\s*["\'][^"\']+["\']', '硬编码访问密钥', 'critical'),
            (r'ssh[_-]?key\s*=\s*["\'][^"\']+["\']', '硬编码SSH密钥', 'critical'),
            (r'logging\.info\([^)]*password', '日志记录密码', 'high'),
            (r'print\([^)]*password', '打印密码', 'high'),
        ]
        
        for pattern, description, severity in sensitive_patterns:
            if re.search(pattern, code, re.IGNORECASE):
                issues.append({
                    'type': 'sensitive_data',
                    'severity': severity,
                    'description': description,
                    'suggestion': '使用环境变量或密钥管理服务'
                })
        
        return issues
    
    def _detect_auth_issues(self, code: str) -> List[Dict]:
        """检测认证问题"""
        issues = []
        
        auth_patterns = [
            (r'if\s+\w+\s*==\s*["\']admin["\']', '硬编码管理员检查', 'high'),
            (r'if\s+\w+\.password\s*==', '明文密码比较', 'critical'),
            (r'password\s*=\s*hashlib\.md5', '使用MD5哈希', 'critical'),
            (r'password\s*=\s*hashlib\.sha1', '使用SHA1哈希', 'high'),
            (r'session\[\w+\]\s*=', '直接设置会话', 'medium'),
            (r'cookie\[\w+\]\s*=', '直接设置Cookie', 'medium'),
        ]
        
        for pattern, description, severity in auth_patterns:
            if re.search(pattern, code):
                issues.append({
                    'type': 'authentication',
                    'severity': severity,
                    'description': description,
                    'suggestion': '使用安全的认证框架和密码哈希算法'
                })
        
        return issues
    
    def _detect_access_control(self, code: str) -> List[Dict]:
        """检测访问控制问题"""
        issues = []
        
        ac_patterns = [
            (r'@login_required', '缺少权限检查', 'medium'),
            (r'@admin_required', '缺少细粒度权限', 'medium'),
            (r'user\.role\s*==\s*["\']', '角色硬编码', 'medium'),
            (r'permission\s*=\s*True', '权限硬编码', 'high'),
        ]
        
        for pattern, description, severity in ac_patterns:
            if re.search(pattern, code):
                issues.append({
                    'type': 'access_control',
                    'severity': severity,
                    'description': description,
                    'suggestion': '实现细粒度的权限控制机制'
                })
        
        return issues
    
    def _detect_insecure_dependencies(self, code: str) -> List[Dict]:
        """检测不安全依赖"""
        issues = []
        
        insecure_patterns = [
            (r'import\s+pickle', '使用pickle', 'high'),
            (r'import\s+shelve', '使用shelve', 'medium'),
            (r'import\s+marshal', '使用marshal', 'high'),
            (r'import\s+subprocess', '使用subprocess', 'medium'),
            (r'import\s+os', '使用os模块', 'low'),
        ]
        
        for pattern, description, severity in insecure_patterns:
            if re.search(pattern, code):
                issues.append({
                    'type': 'insecure_dependency',
                    'severity': severity,
                    'description': description,
                    'suggestion': '评估依赖使用的安全性'
                })
        
        return issues
    
    def _generate_summary(self, vulnerabilities: List[Dict]) -> Dict:
        """生成审计摘要"""
        summary = {s: 0 for s in self.severity_levels}
        
        for v in vulnerabilities:
            severity = v.get('severity', 'low')
            if severity in summary:
                summary[severity] += 1
        
        total = sum(summary.values())
        if total > 0:
            risk_score = summary['critical'] * 10 + summary['high'] * 5 + summary['medium'] * 2
            summary['risk_score'] = risk_score
            summary['risk_level'] = self._get_risk_level(risk_score)
        else:
            summary['risk_score'] = 0
            summary['risk_level'] = 'low'
        
        return summary
    
    def _get_risk_level(self, score: int) -> str:
        """获取风险等级"""
        if score >= 50:
            return 'critical'
        elif score >= 30:
            return 'high'
        elif score >= 15:
            return 'medium'
        elif score >= 5:
            return 'low'
        else:
            return 'info'
    
    def get_stats(self) -> Dict:
        """获取审计统计"""
        return {
            'total_audits': self.total_audits,
            'total_vulnerabilities': self.total_vulnerabilities,
            'avg_vulnerabilities_per_audit': self.total_vulnerabilities / max(1, self.total_audits),
            'recent_audits': self.audit_history[-5:]
        }

security_auditor = AISecurityAuditor('ai_security_001')
