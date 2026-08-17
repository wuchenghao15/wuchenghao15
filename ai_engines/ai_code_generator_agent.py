#!/usr/bin/env python3
"""AI智能代码生成Agent"""

import os
import re
import logging
import json
from datetime import datetime
from typing import Dict, List, Any
from ai_engines.ai_employee_system import AIEmployee

logger = logging.getLogger(__name__)

class AICodeGeneratorAgent(AIEmployee):
    """AI代码生成Agent"""
    
    def __init__(self, employee_id: str, name: str = "AI代码生成专家"):
        super().__init__(employee_id, name, 'code_generator', 7)
        self.skills = [
            '代码生成', '代码优化', '代码重构',
            'API生成', '数据库操作', '单元测试',
            '代码注释', '文档生成', '代码审查'
        ]
        self.code_history = []
        self.total_generated = 0
    
    def generate_code(self, prompt: str, language: str = 'python') -> Dict[str, Any]:
        """生成代码"""
        code_snippets = {
            'python': {
                'hello': 'print("Hello, World!")',
                'function': 'def greet(name):\n    return f"Hello, {name}!"',
                'class': 'class Person:\n    def __init__(self, name):\n        self.name = name',
                'api': 'from flask import Flask, jsonify\napp = Flask(__name__)\n@app.route("/")\ndef home():\n    return jsonify({"message": "Hello"})',
                'database': 'import sqlite3\nconn = sqlite3.connect("example.db")',
                'test': 'import unittest\nclass TestExample(unittest.TestCase):\n    def test_example(self):\n        self.assertTrue(True)'
            },
            'javascript': {
                'hello': 'console.log("Hello, World!");',
                'function': 'function greet(name) {\n    return `Hello, ${name}!`;\n}',
                'class': 'class Person {\n    constructor(name) {\n        this.name = name;\n    }\n}',
                'api': 'const express = require("express");\nconst app = express();\napp.get("/", (req, res) => res.send("Hello"));',
                'database': 'const sqlite3 = require("sqlite3");\nconst db = new sqlite3.Database(":memory:");'
            },
            'java': {
                'hello': 'public class HelloWorld {\n    public static void main(String[] args) {\n        System.out.println("Hello, World!");\n    }\n}',
                'function': 'public class Utils {\n    public static String greet(String name) {\n        return "Hello, " + name + "!";\n    }\n}',
                'class': 'public class Person {\n    private String name;\n    public Person(String name) {\n        this.name = name;\n    }\n}'
            },
            'go': {
                'hello': 'package main\nimport "fmt"\nfunc main() {\n    fmt.Println("Hello, World!")\n}',
                'function': 'package main\nimport "fmt"\nfunc greet(name string) string {\n    return fmt.Sprintf("Hello, %s!", name)\n}',
                'class': 'package main\ntype Person struct {\n    Name string\n}'
            }
        }
        
        lang_code = code_snippets.get(language, code_snippets['python'])
        
        generated_code = ""
        if 'hello' in prompt.lower():
            generated_code = lang_code['hello']
        elif 'function' in prompt.lower():
            generated_code = lang_code['function']
        elif 'class' in prompt.lower():
            generated_code = lang_code['class']
        elif 'api' in prompt.lower():
            generated_code = lang_code['api']
        elif 'database' in prompt.lower():
            generated_code = lang_code['database']
        elif 'test' in prompt.lower():
            generated_code = lang_code.get('test', lang_code['function'])
        else:
            generated_code = lang_code['hello']
        
        self.total_generated += 1
        
        result = {
            'prompt': prompt,
            'language': language,
            'code': generated_code,
            'line_count': len(generated_code.split('\n')),
            'timestamp': datetime.now().isoformat()
        }
        
        self.code_history.append(result)
        return result
    
    def optimize_code(self, code: str) -> Dict[str, Any]:
        """优化代码"""
        optimizations = []
        
        if 'for i in range(' in code:
            optimizations.append('考虑使用列表推导式')
        
        if 'print(' in code:
            optimizations.append('考虑使用logging替代print')
        
        if len(code.split('\n')) > 50:
            optimizations.append('代码过长，考虑拆分')
        
        if 'if' in code and 'else' not in code:
            optimizations.append('考虑添加else分支')
        
        return {
            'original_code': code,
            'optimizations': optimizations,
            'optimized_code': code,
            'timestamp': datetime.now().isoformat()
        }
    
    def generate_api(self, endpoints: List[Dict]) -> str:
        """生成API代码"""
        code_lines = ['from flask import Flask, jsonify, request']
        code_lines.append('app = Flask(__name__)')
        code_lines.append('')
        
        for endpoint in endpoints:
            method = endpoint.get('method', 'GET').lower()
            path = endpoint.get('path', '/')
            description = endpoint.get('description', '')
            
            code_lines.append(f'@{method}("{path}")')
            code_lines.append(f'def {path.replace("/", "_").strip("_")}():')
            code_lines.append(f'    """{description}"""')
            code_lines.append('    return jsonify({"message": "Success"})')
            code_lines.append('')
        
        code_lines.append('if __name__ == "__main__":')
        code_lines.append('    app.run(debug=True)')
        
        return '\n'.join(code_lines)
    
    def get_stats(self) -> Dict:
        """获取统计"""
        return {
            'total_generated': self.total_generated,
            'recent_generations': self.code_history[-5:]
        }

code_generator_agent = AICodeGeneratorAgent('ai_code_generator_001')
