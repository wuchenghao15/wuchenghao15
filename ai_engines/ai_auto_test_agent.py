#!/usr/bin/env python3
"""AI自动化测试Agent"""

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
    """AI自动化测试Agent"""
    
    def __init__(self, employee_id: str, name: str = "AI自动化测试专家"):
        super().__init__(employee_id, name, 'auto_test', 7)
        self.skills = [
            '单元测试生成', '集成测试', 'API测试',
            '性能测试', '回归测试', '测试报告生成',
            '测试用例设计', '测试覆盖率分析'
        ]
        self.test_history = []
        self.total_tests = 0
        self.passed_tests = 0
        self.failed_tests = 0
    
    def generate_unit_test(self, function_code: str, function_name: str = "") -> str:
        """生成单元测试代码"""
        test_cases = []
        
        if 'def ' in function_code:
            func_match = re.search(r'def (\w+)\s*\(([^)]*)\)', function_code)
            if func_match:
                func_name = func_match.group(1)
                params = [p.strip() for p in func_match.group(2).split(',') if p.strip()]
                
                test_cases.append(f"def test_{func_name}_basic():")
                args = ', '.join(f"{p}=None" for p in params)
                test_cases.append(f"    result = {func_name}({args})")
                test_cases.append(f"    assert result is not None")
                test_cases.append("")
                
                test_cases.append(f"def test_{func_name}_empty_params():")
                test_cases.append(f"    result = {func_name}()")
                test_cases.append(f"    assert result is not None")
                test_cases.append("")
        
        return '\n'.join(test_cases)
    
    def run_test(self, test_file: str) -> Dict[str, Any]:
        """运行测试文件"""
        try:
            result = subprocess.run(
                ['python', '-m', 'pytest', test_file, '-v', '--tb=short'],
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
                'test_file': test_file,
                'passed': passed,
                'failed': failed,
                'total': passed + failed,
                'success_rate': (passed / (passed + failed)) * 100 if (passed + failed) > 0 else 0,
                'output': result.stdout[:2000],
                'timestamp': datetime.now().isoformat()
            }
            
            self.test_history.append(test_result)
            return test_result
            
        except Exception as e:
            return {
                'test_file': test_file,
                'passed': 0,
                'failed': 0,
                'total': 0,
                'success_rate': 0,
                'error': str(e),
                'timestamp': datetime.now().isoformat()
            }
    
    def run_api_tests(self, api_endpoints: List[str], base_url: str = "http://localhost:8888") -> Dict[str, Any]:
        """运行API测试"""
        results = []
        
        for endpoint in api_endpoints:
            try:
                import urllib.request
                url = f"{base_url}{endpoint}"
                response = urllib.request.urlopen(url, timeout=10)
                status_code = response.getcode()
                
                results.append({
                    'endpoint': endpoint,
                    'status_code': status_code,
                    'success': status_code == 200,
                    'response_length': len(response.read())
                })
            except Exception as e:
                results.append({
                    'endpoint': endpoint,
                    'status_code': 0,
                    'success': False,
                    'error': str(e)
                })
        
        success_count = sum(1 for r in results if r['success'])
        
        return {
            'total_endpoints': len(api_endpoints),
            'passed': success_count,
            'failed': len(api_endpoints) - success_count,
            'success_rate': (success_count / len(api_endpoints)) * 100 if api_endpoints else 0,
            'results': results,
            'timestamp': datetime.now().isoformat()
        }
    
    def analyze_coverage(self, source_dir: str) -> Dict[str, Any]:
        """分析测试覆盖率"""
        try:
            result = subprocess.run(
                ['python', '-m', 'pytest', '--cov=' + source_dir, '--cov-report=json'],
                capture_output=True,
                text=True,
                timeout=120
            )
            
            import json
            with open('.coverage') as f:
                coverage_data = json.load(f)
            
            return {
                'source_dir': source_dir,
                'total_lines': coverage_data.get('lines', {}),
                'covered_lines': coverage_data.get('covered_lines', {}),
                'timestamp': datetime.now().isoformat()
            }
        except Exception as e:
            return {
                'source_dir': source_dir,
                'error': str(e),
                'timestamp': datetime.now().isoformat()
            }
    
    def get_stats(self) -> Dict:
        """获取测试统计"""
        return {
            'total_tests': self.total_tests,
            'passed_tests': self.passed_tests,
            'failed_tests': self.failed_tests,
            'success_rate': (self.passed_tests / self.total_tests) * 100 if self.total_tests > 0 else 0,
            'recent_tests': self.test_history[-5:]
        }

auto_test_agent = AIAutoTestAgent('ai_auto_test_001')
