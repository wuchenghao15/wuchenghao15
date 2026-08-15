#!/usr/bin/env python3
r"""AI自动化测试Agentr"""

import os
import re
import logging
import subprocess
import json
from datetime import datetime
from typing import Dict, List, Any
from ai_engines.ai_employee_system import AIEmployee

logger = logging.getLogger(__name__)

class AIAutoTestAgent(AIEmployee):
    r"""AI自动化测试Agentr"""

    def __init__(self, employee_id: str, name: str = r"AI自动化测试专家"):
        super().__init__(employee_id, name, r'auto_test', 7)
        self.skills = [
            r'单元测试生成', r'集成测试', r'API测试',
            r'性能测试', r'回归测试', r'测试报告生成',
            r'测试用例设计', r'测试覆盖率分析'
        ]
        self.test_history = []
        self.total_tests = 0
        self.passed_tests = 0
        self.failed_tests = 0

    def generate_unit_test(self, function_code: str, function_name: str = r"") -> str:
        r"""生成单元测试代码r"""
        test_cases = []

        if r'def ' in function_code:
            func_match = re.search(r'def (\w+)\s*\(([^)]*)\)', function_code)
            if func_match:
                func_name = func_match.group(1)
                params = [p.strip() for p in func_match.group(2).split(r',') if p.strip()]

                test_cases.append(fr"def test_{func_name}_basic():")
                args = r', '.join(fr"{p}=None" for p in params)
                test_cases.append(fr"    result = {func_name}({args})")
                test_cases.append(r"    assert result is not None")
                test_cases.append(r"")

                test_cases.append(fr"def test_{func_name}_empty_params():")
                test_cases.append(fr"    result = {func_name}()")
                test_cases.append(r"    assert result is not None")
                test_cases.append(r"")

        return r'\n'.join(test_cases)

    def run_test(self, test_file: str) -> Dict[str, Any]:
        r"""运行测试文件r"""
        try:
            result = subprocess.run(
                [r'python', r'-m', r'pytest', test_file, r'-v', r'--tb=short'],
                capture_output=True,
                text=True,
                timeout=120
            )

            passed = len(re.findall(r'PASSED', result.stdout))
            failed = len(re.findall(r'FAILED', result.stdout))

            self.total_tests += passed + failed
            self.passed_tests += passed
            self.failed_tests += failed

            test_result = {
                r'test_file': test_file,
                r'passed': passed,
                r'failed': failed,
                r'total': passed + failed,
                r'success_rate': (passed / (passed + failed)) * 100 if (passed + failed) > 0 else 0,
                r'output': result.stdout[:2000],
                r'timestamp': datetime.now().isoformat()
            }

            self.test_history.append(test_result)
            return test_result

        except Exception as e:
            return {
                r'test_file': test_file,
                r'passed': 0,
                r'failed': 0,
                r'total': 0,
                r'success_rate': 0,
                r'error': str(e),
                r'timestamp': datetime.now().isoformat()
            }

    def run_api_tests(self, api_endpoints: List[str], base_url: str = r"http://localhost:8888") -> Dict[str, Any]:
        r"""运行API测试r"""
        results = []

        for endpoint in api_endpoints:
            try:
                import urllib.request
                url = fr"{base_url}{endpoint}"
                response = urllib.request.urlopen(url, timeout=10)
                status_code = response.getcode()

                results.append({
                    r'endpoint': endpoint,
                    r'status_code': status_code,
                    r'success': status_code == 200,
                    r'response_length': len(response.read())
                })
            except Exception as e:
                results.append({
                    r'endpoint': endpoint,
                    r'status_code': 0,
                    r'success': False,
                    r'error': str(e)
                })

        success_count = sum(1 for r in results if r[r'success'])

        return {
            r'total_endpoints': len(api_endpoints),
            r'passed': success_count,
            r'failed': len(api_endpoints) - success_count,
            r'success_rate': (success_count / len(api_endpoints)) * 100 if api_endpoints else 0,
            r'results': results,
            r'timestamp': datetime.now().isoformat()
        }

    def analyze_coverage(self, source_dir: str) -> Dict[str, Any]:
        r"""分析测试覆盖率r"""
        try:
            result = subprocess.run(
                [r'python', r'-m', r'pytest', r'--cov=' + source_dir, r'--cov-report=json'],
                capture_output=True,
                text=True,
                timeout=120
            )

            import json
            with open(r'.coverage') as f:
                coverage_data = json.load(f)

            return {
                r'source_dir': source_dir,
                r'total_lines': coverage_data.get(r'lines', {}),
                r'covered_lines': coverage_data.get(r'covered_lines', {}),
                r'timestamp': datetime.now().isoformat()
            }
        except Exception as e:
            return {
                r'source_dir': source_dir,
                r'error': str(e),
                r'timestamp': datetime.now().isoformat()
            }

    def get_stats(self) -> Dict:
        r"""获取测试统计r"""
        return {
            r'total_tests': self.total_tests,
            r'passed_tests': self.passed_tests,
            r'failed_tests': self.failed_tests,
            r'success_rate': (self.passed_tests / self.total_tests) * 100 if self.total_tests > 0 else 0,
            r'recent_tests': self.test_history[-5:]
        }

auto_test_agent = AIAutoTestAgent(r'ai_auto_test_001')
