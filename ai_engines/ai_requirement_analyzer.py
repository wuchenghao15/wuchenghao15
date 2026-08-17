#!/usr/bin/env python3
"""AI需求分析Agent"""

import os
import re
import logging
import json
from datetime import datetime
from typing import Dict, List, Any
from ai_engines.ai_employee_system import AIEmployee

logger = logging.getLogger(__name__)

class AIRequirementAnalyzer(AIEmployee):
    """AI需求分析Agent"""
    
    def __init__(self, employee_id: str, name: str = "AI需求分析专家"):
        super().__init__(employee_id, name, 'requirement_analyzer', 7)
        self.skills = [
            '需求分析', '需求提取', '需求分类',
            '需求优先级评估', '需求冲突检测', '需求文档生成',
            '用例分析', '功能点识别', '需求追溯'
        ]
        self.analysis_history = []
        self.total_analyses = 0
        self.total_requirements = 0
    
    def analyze_requirement(self, requirement_text: str) -> Dict[str, Any]:
        """分析需求文本"""
        requirements = []
        
        requirements.extend(self._extract_functional_requirements(requirement_text))
        requirements.extend(self._extract_non_functional_requirements(requirement_text))
        requirements.extend(self._extract_technical_requirements(requirement_text))
        
        self.total_analyses += 1
        self.total_requirements += len(requirements)
        
        analysis_result = {
            'original_text': requirement_text,
            'total_requirements': len(requirements),
            'requirements': requirements,
            'summary': self._generate_summary(requirements),
            'conflicts': self._detect_conflicts(requirements),
            'timestamp': datetime.now().isoformat()
        }
        
        self.analysis_history.append(analysis_result)
        return analysis_result
    
    def _extract_functional_requirements(self, text: str) -> List[Dict]:
        """提取功能需求"""
        requirements = []
        
        functional_keywords = [
            '需要', '应该', '必须', '可以', '能够', '支持', '实现',
            '提供', '允许', '确保', '包含', '包括', '显示', '生成',
            '创建', '更新', '删除', '查询', '导入', '导出', '发送',
            '接收', '处理', '计算', '分析', '管理', '配置', '监控',
            '通知', '提醒', '验证', '授权', '登录', '注册', '认证'
        ]
        
        sentences = re.split(r'[。！？;；]', text)
        for sentence in sentences:
            for keyword in functional_keywords:
                if keyword in sentence:
                    requirements.append({
                        'type': 'functional',
                        'priority': self._determine_priority(sentence),
                        'content': sentence.strip(),
                        'keyword': keyword
                    })
                    break
        
        return requirements
    
    def _extract_non_functional_requirements(self, text: str) -> List[Dict]:
        """提取非功能需求"""
        requirements = []
        
        nfr_patterns = [
            (r'响应时间|性能|速度|延迟', 'performance', '性能要求'),
            (r'安全|加密|权限|认证', 'security', '安全要求'),
            (r'可靠|稳定|可用性', 'reliability', '可靠性要求'),
            (r'可扩展|可维护|可移植', 'maintainability', '可维护性要求'),
            (r'兼容|适配|支持.*设备', 'compatibility', '兼容性要求'),
            (r'易用|友好|简单|便捷', 'usability', '易用性要求'),
            (r'并发|负载|吞吐量', 'scalability', '可扩展性要求'),
            (r'存储|容量|资源', 'resource', '资源要求'),
        ]
        
        for pattern, category, description in nfr_patterns:
            if re.search(pattern, text):
                requirements.append({
                    'type': 'non_functional',
                    'category': category,
                    'priority': 'high',
                    'content': description,
                    'keyword': pattern
                })
        
        return requirements
    
    def _extract_technical_requirements(self, text: str) -> List[Dict]:
        """提取技术需求"""
        requirements = []
        
        tech_keywords = [
            ('Python', 'python', '编程语言'),
            ('Flask', 'flask', 'Web框架'),
            ('SQLite', 'sqlite', '数据库'),
            ('MySQL', 'mysql', '数据库'),
            ('Redis', 'redis', '缓存'),
            ('Docker', 'docker', '容器化'),
            ('API', 'api', '接口'),
            ('RESTful', 'restful', '接口风格'),
            ('WebSocket', 'websocket', '实时通信'),
            ('SSL', 'ssl', '安全'),
            ('HTTPS', 'https', '安全'),
            ('OAuth', 'oauth', '认证'),
            ('JWT', 'jwt', '认证'),
            ('WebSocket', 'websocket', '通信'),
            ('WebSocket', 'websocket', '协议'),
        ]
        
        for keyword, category, description in tech_keywords:
            if keyword in text:
                requirements.append({
                    'type': 'technical',
                    'category': category,
                    'priority': 'medium',
                    'content': f'使用{description}: {keyword}',
                    'keyword': keyword
                })
        
        return requirements
    
    def _determine_priority(self, sentence: str) -> str:
        """确定需求优先级"""
        priority_keywords = {
            '必须': 'high',
            '务必': 'high',
            '一定': 'high',
            '紧急': 'high',
            '重要': 'high',
            '应该': 'medium',
            '建议': 'medium',
            '可以': 'low',
            '可选': 'low',
            '希望': 'low',
        }
        
        for keyword, priority in priority_keywords.items():
            if keyword in sentence:
                return priority
        
        return 'medium'
    
    def _generate_summary(self, requirements: List[Dict]) -> Dict:
        """生成分析摘要"""
        summary = {
            'functional': 0,
            'non_functional': 0,
            'technical': 0,
            'high': 0,
            'medium': 0,
            'low': 0
        }
        
        for req in requirements:
            req_type = req.get('type', 'functional')
            priority = req.get('priority', 'medium')
            
            if req_type in summary:
                summary[req_type] += 1
            if priority in summary:
                summary[priority] += 1
        
        return summary
    
    def _detect_conflicts(self, requirements: List[Dict]) -> List[Dict]:
        """检测需求冲突"""
        conflicts = []
        
        functional_reqs = [r for r in requirements if r['type'] == 'functional']
        for i, req1 in enumerate(functional_reqs):
            for j, req2 in enumerate(functional_reqs[i+1:], i+1):
                if self._is_conflicting(req1, req2):
                    conflicts.append({
                        'req1': req1['content'],
                        'req2': req2['content'],
                        'type': 'conflict',
                        'severity': 'high'
                    })
        
        return conflicts
    
    def _is_conflicting(self, req1: Dict, req2: Dict) -> bool:
        """判断两个需求是否冲突"""
        negation_words = ['不', '非', '否', '禁止', '不能', '无需']
        
        for word in negation_words:
            if word in req1['content'] and word not in req2['content']:
                if req1['keyword'] in req2['content']:
                    return True
            if word in req2['content'] and word not in req1['content']:
                if req2['keyword'] in req1['content']:
                    return True
        
        return False
    
    def generate_requirement_document(self, requirements: List[Dict]) -> str:
        """生成需求文档"""
        doc_lines = []
        doc_lines.append("# 需求分析文档")
        doc_lines.append(f"生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        doc_lines.append("")
        
        doc_lines.append("## 功能需求")
        for req in requirements:
            if req['type'] == 'functional':
                priority = {'high': '高', 'medium': '中', 'low': '低'}[req['priority']]
                doc_lines.append(f"- [{priority}] {req['content']}")
        doc_lines.append("")
        
        doc_lines.append("## 非功能需求")
        for req in requirements:
            if req['type'] == 'non_functional':
                doc_lines.append(f"- {req['content']}")
        doc_lines.append("")
        
        doc_lines.append("## 技术需求")
        for req in requirements:
            if req['type'] == 'technical':
                doc_lines.append(f"- {req['content']}")
        
        return '\n'.join(doc_lines)
    
    def get_stats(self) -> Dict:
        """获取分析统计"""
        return {
            'total_analyses': self.total_analyses,
            'total_requirements': self.total_requirements,
            'avg_requirements_per_analysis': self.total_requirements / max(1, self.total_analyses),
            'recent_analyses': self.analysis_history[-5:]
        }

requirement_analyzer = AIRequirementAnalyzer('ai_requirement_001')
