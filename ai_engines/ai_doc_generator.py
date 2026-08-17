#!/usr/bin/env python3
"""AI文档生成Agent"""

import os
import re
import logging
import json
from datetime import datetime
from typing import Dict, List, Any
from ai_engines.ai_employee_system import AIEmployee

logger = logging.getLogger(__name__)

class AIDocGenerator(AIEmployee):
    """AI文档生成Agent"""
    
    def __init__(self, employee_id: str, name: str = "AI文档生成专家"):
        super().__init__(employee_id, name, 'doc_generator', 6)
        self.skills = [
            'API文档生成', '代码注释生成', '技术文档编写',
            '用户手册生成', 'README生成', '变更日志生成',
            '架构文档生成', '接口文档生成', '文档翻译'
        ]
        self.doc_history = []
        self.total_docs = 0
    
    def generate_api_doc(self, api_endpoints: List[Dict]) -> str:
        """生成API文档"""
        doc_lines = []
        doc_lines.append("# API文档")
        doc_lines.append(f"生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        doc_lines.append("")
        
        for endpoint in api_endpoints:
            doc_lines.append(f"## {endpoint.get('method', 'GET')} {endpoint.get('path', '')}")
            doc_lines.append(f"**描述**: {endpoint.get('description', '')}")
            doc_lines.append("")
            
            if 'parameters' in endpoint and endpoint['parameters']:
                doc_lines.append("### 参数")
                for param in endpoint['parameters']:
                    doc_lines.append(f"- `{param.get('name')}` ({param.get('type', 'string')}): {param.get('description', '')}")
                doc_lines.append("")
            
            if 'response' in endpoint:
                doc_lines.append("### 响应示例")
                doc_lines.append("```json")
                doc_lines.append(json.dumps(endpoint['response'], indent=2, ensure_ascii=False))
                doc_lines.append("```")
                doc_lines.append("")
        
        self.total_docs += 1
        self.doc_history.append({'type': 'api', 'content': doc_lines[0]})
        return '\n'.join(doc_lines)
    
    def generate_code_documentation(self, code: str, file_path: str = "") -> str:
        """生成代码文档"""
        doc_lines = []
        doc_lines.append(f"# {os.path.basename(file_path) if file_path else '代码文档'}")
        doc_lines.append(f"生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        doc_lines.append("")
        
        classes = re.findall(r'class (\w+)\s*\(', code)
        functions = re.findall(r'def (\w+)\s*\(', code)
        
        if classes:
            doc_lines.append("## 类")
            for cls in classes:
                doc_lines.append(f"- `{cls}`")
                cls_match = re.search(r'class ' + cls + r'\s*\([^)]*\):\s*([^}]*)', code, re.DOTALL)
                if cls_match:
                    doc_lines.append(f"  {cls_match.group(1).strip()[:100]}...")
            doc_lines.append("")
        
        if functions:
            doc_lines.append("## 函数")
            for func in functions:
                func_match = re.search(r'def ' + func + r'\s*\(([^)]*)\):', code)
                if func_match:
                    params = func_match.group(1)
                    doc_lines.append(f"- `{func}({params})`")
            doc_lines.append("")
        
        doc_lines.append("## 代码内容")
        doc_lines.append("```python")
        doc_lines.append(code)
        doc_lines.append("```")
        
        self.total_docs += 1
        self.doc_history.append({'type': 'code', 'content': doc_lines[0]})
        return '\n'.join(doc_lines)
    
    def generate_readme(self, project_info: Dict) -> str:
        """生成README文档"""
        doc_lines = []
        doc_lines.append(f"# {project_info.get('name', 'Project Name')}")
        doc_lines.append("")
        
        if 'description' in project_info:
            doc_lines.append(project_info['description'])
            doc_lines.append("")
        
        if 'features' in project_info:
            doc_lines.append("## 功能特性")
            for feature in project_info['features']:
                doc_lines.append(f"- {feature}")
            doc_lines.append("")
        
        if 'installation' in project_info:
            doc_lines.append("## 安装")
            doc_lines.append(project_info['installation'])
            doc_lines.append("")
        
        if 'usage' in project_info:
            doc_lines.append("## 使用方法")
            doc_lines.append(project_info['usage'])
            doc_lines.append("")
        
        if 'contributing' in project_info:
            doc_lines.append("## 贡献")
            doc_lines.append(project_info['contributing'])
            doc_lines.append("")
        
        doc_lines.append(f"*最后更新: {datetime.now().strftime('%Y-%m-%d')}*")
        
        self.total_docs += 1
        self.doc_history.append({'type': 'readme', 'content': doc_lines[0]})
        return '\n'.join(doc_lines)
    
    def generate_changelog(self, changes: List[Dict]) -> str:
        """生成变更日志"""
        doc_lines = []
        doc_lines.append("# 变更日志")
        doc_lines.append("")
        
        for change in changes:
            doc_lines.append(f"## [{change.get('version', '')}] - {change.get('date', '')}")
            doc_lines.append(f"**标题**: {change.get('title', '')}")
            doc_lines.append("")
            
            if 'changes' in change:
                doc_lines.append("### 变更内容")
                for item in change['changes']:
                    doc_lines.append(f"- {item}")
                doc_lines.append("")
            
            if 'highlights' in change:
                doc_lines.append("### 亮点")
                for highlight in change['highlights']:
                    doc_lines.append(f"- {highlight}")
                doc_lines.append("")
        
        self.total_docs += 1
        self.doc_history.append({'type': 'changelog', 'content': doc_lines[0]})
        return '\n'.join(doc_lines)
    
    def translate_document(self, content: str, target_language: str = "zh") -> str:
        """翻译文档"""
        doc_lines = []
        doc_lines.append(f"# 文档翻译 ({target_language})")
        doc_lines.append(f"生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        doc_lines.append("")
        doc_lines.append(content)
        
        self.total_docs += 1
        self.doc_history.append({'type': 'translation', 'content': doc_lines[0]})
        return '\n'.join(doc_lines)
    
    def get_stats(self) -> Dict:
        """获取文档统计"""
        return {
            'total_docs': self.total_docs,
            'recent_docs': self.doc_history[-5:]
        }

doc_generator = AIDocGenerator('ai_doc_generator_001')
