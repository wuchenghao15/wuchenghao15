#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
安全扫描器模块
负责扫描项目安全漏洞，检测潜在安全问题

import os
import re
import logging
import subprocess
from datetime import datetime
from typing import List, Dict, Any

# 配置日志
logger = logging.getLogger('security_scanner')

class SecurityScanner:
    """安全扫描器类"""

    def __init__(self):
        """初始化安全扫描器"""
        self.project_root = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
        self.python_extensions = ['.py']
        self.ignored_dirs = ['__pycache__', 'venv', 'env', '.git', 'static', 'templates']
        logger.info("安全扫描器初始化完成")

    def scan_project(self) -> List[Dict[str, Any]]:
        """扫描整个项目的安全问题"""
        issues = []
        try:
            # 遍历项目目录
            for root, dirs, files in os.walk(self.project_root):
                # 忽略指定目录
                dirs[:] = [d for d in dirs if d not in self.ignored_dirs]

                # 扫描Python文件
                for file in files:
                    if any(file.endswith(ext) for ext in self.python_extensions):
                        file_path = os.path.join(root, file)
                        file_issues = self.scan_file(file_path)
                        issues.extend(file_issues)

            logger.info(f"安全扫描完成，发现 {len(issues)} 个问题")
        except Exception as e:
            logger.error(f"扫描项目时出错: {str(e)}")

        return issues

    def scan_file(self, file_path: str) -> List[Dict[str, Any]]:
        """扫描单个文件的安全问题"""
        issues = []
            with open(file_path, 'r', encoding='utf-8') as f:

            # 扫描SQL注入漏洞
            sql_issues = self._scan_sql_injection(file_path, content)
            issues.extend(sql_issues)

            # 扫描XSS漏洞
            xss_issues = self._scan_xss(file_path, content)
            issues.extend(xss_issues)

            # 扫描CSRF漏洞
            csrf_issues = self._scan_csrf(file_path, content)
            issues.extend(csrf_issues)

            # 扫描敏感信息泄露
            sensitive_issues = self._scan_sensitive_info(file_path, content)
            issues.extend(sensitive_issues)

            # 扫描权限问题
            permission_issues = self._scan_permissions(file_path, content)
            issues.extend(permission_issues)

        except Exception as e:
            logger.error(f"扫描文件 {file_path} 时出错: {str(e)}")


    def _scan_sql_injection(self, file_path: str, content: str) -> List[Dict[str, Any]]:
        """扫描SQL注入漏洞"""
        # 检测直接拼接SQL语句
        sql_patterns = [
            r"execute\(['\"].*\{.*\}.*['\"],",
            r"execute\(['\"].*\+.*['\"],",
            r"cursor\.execute\(['\"].*\{.*\}.*['\"],",
            r"cursor\.execute\(['\"].*\+.*['\"],"
        ]

        lines = content.split('\n')
        for line_num, line in enumerate(lines, 1):
            for pattern in sql_patterns:
                if re.search(pattern, line):
                    issues.append({
                        'type': 'sql_injection',
                        'description': "可能存在SQL注入漏洞，避免直接拼接SQL语句",
                        'file': file_path,
                        'line': line_num,
                        'severity': 'high'
                    })
                    break

        return issues

    def _scan_xss(self, file_path: str, content: str) -> List[Dict[str, Any]]:
        """扫描XSS漏洞"""
        issues = []
        xss_patterns = [
            r"return render_template\(.*,.*=.*request\.",
            r"{{.*request\.",
            r"{{.*session\.",
            r"{{.*user\."
        ]

        lines = content.split('\n')
        for line_num, line in enumerate(lines, 1):
            for pattern in xss_patterns:
                if re.search(pattern, line):
                    issues.append({
                        'type': 'xss',
                        'file': file_path,
                        'line': line_num,
                    })

        return issues
    def _scan_csrf(self, file_path: str, content: str) -> List[Dict[str, Any]]:
        issues = []
        # 检测表单提交是否缺少CSRF保护
            r"<form.*method=['\"](?:post|PUT|DELETE)['\"].*>",
        ]
        csrf_protection_patterns = [
            r"csrf_token",
            r"csrf_protect"

        has_csrf_protection = any(re.search(pattern, content) for pattern in csrf_protection_patterns)

            lines = content.split('\n')
            for line_num, line in enumerate(lines, 1):
                for pattern in form_patterns:
                    if re.search(pattern, line):
                        issues.append({
                            'description': "可能存在CSRF漏洞，建议添加CSRF保护",
                            'file': file_path,
                            'line': line_num,
                            'severity': 'medium'
                        })
                        break


    def _scan_sensitive_info(self, file_path: str, content: str) -> List[Dict[str, Any]]:
        issues = []
        # 检测硬编码的敏感信息
        sensitive_patterns = [
            (r"secret['\"].*['\"]", "密钥"),
            (r"token['\"].*['\"]", "令牌"),
            (r"auth[_\s-]?key['\"].*['\"]", "认证密钥"),
            (r"database[_\s-]?url['\"].*['\"]", "数据库URL"),
            (r"connection[_\s-]?string['\"].*['\"]", "连接字符串")
        ]
        lines = content.split('\n')
        for line_num, line in enumerate(lines, 1):
                if re.search(pattern, line, re.IGNORECASE):
                    issues.append({
                        'type': 'sensitive_info',
                        'file': file_path,
                    break

        return issues

    def _scan_permissions(self, file_path: str, content: str) -> List[Dict[str, Any]]:
        issues = []
        # 检测缺少权限检查的路由
        route_patterns = [
        ]

        permission_decorators = [
            r"@login_required",
            r"@require_permission",
            r"@permission_required",
            r"@admin_required"

        lines = content.split('\n')
        for i, line in enumerate(lines, 1):
            for pattern in route_patterns:
                if re.search(pattern, line):
                    for j in range(max(0, i-5), i):
                        if j < len(lines):
                            for decorator in permission_decorators:
                                    has_permission_check = True
                                    break
                            break
                    if not has_permission_check:
                            'type': 'permission',
                            'description': "可能缺少权限检查，建议添加适当的权限装饰器",
                            'file': file_path,
                        })
                    break

        return issues

    def check_dependencies(self) -> List[Dict[str, Any]]:
        """检查依赖库的安全问题"""
        issues = []
            requirements_file = os.path.join(self.project_root, 'requirements.txt')
            if os.path.exists(requirements_file):
                with open(requirements_file, 'r', encoding='utf-8') as f:

                # 检测已知的有漏洞的依赖版本
                    ('Flask', '1.0.0', '2.0.0'),  # 示例，实际应使用最新的漏洞数据库
                    ('Django', '3.0.0', '3.2.0'),
                    ('requests', '2.20.0', '2.25.0')
                ]

                for dep, vulnerable_min, vulnerable_max in vulnerable_dependencies:
                    pattern = rf"{dep}==([0-9]+[0-9]+[0-9]+)"
                    match = re.search(pattern, requirements)
                    if match:
                        version = match.group(1)
                        if vulnerable_min <= version <= vulnerable_max:
                            issues.append({
                                'type': 'dependency_vulnerability',
                                'description': f"依赖库 {dep} {version} 可能存在安全漏洞，建议更新到最新版本",
                                'file': requirements_file,
                                'line': 1,
                            })
        except Exception as e:
        return issues
    def generate_security_report(self) -> Dict[str, Any]:
        """生成安全报告"""
        try:
            code_issues = self.scan_project()
            dependency_issues = self.check_dependencies()
            # 按严重程度分组
            high_severity = [issue for issue in all_issues if issue['severity'] == 'high']
            medium_severity = [issue for issue in all_issues if issue['severity'] == 'medium']
            report = {
                'total_issues': len(all_issues),
                'high_severity': len(high_severity),
                'medium_severity': len(medium_severity),
                'issues': all_issues,
                'recommendations': self._generate_recommendations(all_issues)
            }

            return report
        except Exception as e:
            logger.error(f"生成安全报告时出错: {str(e)}")

    def _generate_recommendations(self, issues: List[Dict[str, Any]]) -> List[str]:
        """生成安全建议"""
        recommendations = []

        # 基于问题类型生成建议
        issue_types = set(issue['type'] for issue in issues)

            recommendations.append('使用参数化查询或ORM框架避免SQL注入')
        if 'xss' in issue_types:
            recommendations.append('对用户输入进行适当的转义，使用安全的模板引擎')
        if 'csrf' in issue_types:
            recommendations.append('为所有表单提交添加CSRF保护')
        if 'sensitive_info' in issue_types:
            recommendations.append('使用环境变量或配置文件存储敏感信息，避免硬编码')
        if 'permission' in issue_types:
        if 'dependency_vulnerability' in issue_types:
            recommendations.append('定期更新依赖库到最新版本')
        # 通用建议
        recommendations.extend([
            '定期进行安全扫描，及时发现并修复漏洞',
            '使用安全的开发实践，遵循OWASP Top 10安全原则',
            '实施最小权限原则，只授予必要的权限',
            '加密敏感数据，特别是用户凭证和个人信息',
            '建立安全事件响应机制，及时处理安全问题'
        ])

        return recommendations

if __name__ == '__main__':
    # 测试安全扫描器
    scanner = SecurityScanner()
    issues = scanner.scan_project()
    print(f"发现 {len(issues)} 个安全问题:")
    for issue in issues:
        print(f"- {issue['type']}: {issue['description']} (文件: {issue['file']}:{issue['line']}, 严重程度: {issue['severity']})")

    # 测试依赖检查
    dependency_issues = scanner.check_dependencies()
    if dependency_issues:
        print("\n依赖库安全问题:")
        for issue in dependency_issues:
            print(f"- {issue['description']}")

    # 生成安全报告
    report = scanner.generate_security_report()
    print("\n安全报告:")
    print(f"总问题数: {report.get('total_issues', 0)}")
    print(f"高严重度: {report.get('high_severity', 0)}")
    print(f"中严重度: {report.get('medium_severity', 0)}")
    print(f"低严重度: {report.get('low_severity', 0)}")
    print("建议:")
    for recommendation in report.get('recommendations', []):
        print(f"- {recommendation}")
