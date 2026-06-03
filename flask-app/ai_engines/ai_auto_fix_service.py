# -*- coding: utf-8 -*-
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
AI自动修复服务 - 自动检测、修复错误并学习升级
"""

import os
import re
import ast
import json
import time
import traceback
import threading
import subprocess
from typing import Dict, List, Optional, Any, Tuple, Callable
from enum import Enum
from dataclasses import dataclass, field
from datetime import datetime

from app.utils.logging import logger
import logging


class ErrorPattern(Enum):
    """错误模式"""
    SYNTAX_ERROR = "syntax_error"
    IMPORT_ERROR = "import_error"
    NAME_ERROR = "name_error"
    TYPE_ERROR = "type_error"
    VALUE_ERROR = "value_error"
    ATTRIBUTE_ERROR = "attribute_error"
    INDEX_ERROR = "index_error"
    KEY_ERROR = "key_error"
    RUNTIME_ERROR = "runtime_error"
    UNKNOWN_ERROR = "unknown_error"


class FixStrategy(Enum):
    """修复策略"""
    ADD_IMPORT = "add_import"
    FIX_VARIABLE = "fix_variable"
    ADD_PARAMETER = "add_parameter"
    FIX_TYPE = "fix_type"
    ADD_DEFAULT = "add_default"
    WRAP_TRY = "wrap_try"
    ADD_CHECK = "add_check"
    FIX_INDENT = "fix_indent"
    FIX_SYTAX = "fix_syntax"
    UNKNOWN = "unknown"


@dataclass
class ErrorAnalysis:
    """错误分析"""
    error_id: str
    error_type: str
    error_message: str
    file_path: str
    line_number: int
    column: int
    code_snippet: str
    pattern: ErrorPattern
    suggestions: List[str] = field(default_factory=list)


@dataclass
class FixSolution:
    """修复方案"""
    solution_id: str
    error_pattern: ErrorPattern
    strategy: FixStrategy
    original_code: str
    fixed_code: str
    explanation: str
    confidence: float = 0.0
    examples: List[str] = field(default_factory=list)


@dataclass
class BrainKnowledge:
    """脑库知识"""
    knowledge_id: str
    error_type: str
    error_pattern: ErrorPattern
    root_cause: str
    solution_approach: str
    fix_code: str
    explanation: str
    success_rate: float = 0.0
    usage_count: int = 0
    last_used: Optional[float] = None
    created_at: float = field(default_factory=lambda: time.time())
    updated_at: float = field(default_factory=lambda: time.time())
    tags: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict:
        return {
            'knowledge_id': self.knowledge_id,
            'error_type': self.error_type,
            'error_pattern': self.pattern.value if self.error_pattern else None,
            'root_cause': self.root_cause,
            'solution_approach': self.solution_approach,
            'fix_code': self.fix_code,
            'explanation': self.explanation,
            'success_rate': self.success_rate,
            'usage_count': self.usage_count,
            'last_used': self.last_used,
            'created_at': self.created_at,
            'updated_at': self.updated_at,
            'tags': self.tags
        }


class AIAutoFixService:
    """AI自动修复服务"""

    def __init__(self):
        self._knowledge_base: Dict[str, BrainKnowledge] = {}
        self._fix_strategies: Dict[ErrorPattern, Callable] = {}
        self._lock = threading.RLock()
        self._db_path = os.path.join(os.path.dirname(__file__), '..', '..', 'data', 'brain_knowledge.json')
        
        os.makedirs(os.path.dirname(self._db_path), exist_ok=True)
        
        self._load_knowledge_base()
        self._register_fix_strategies()
        
        logger.info("AI自动修复服务初始化完成")

    def _load_knowledge_base(self):
        """加载脑库知识"""
        if os.path.exists(self._db_path):
            try:
                with open(self._db_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    for kb_data in data.get('knowledge', []):
                        kb = BrainKnowledge(
                            knowledge_id=kb_data['knowledge_id'],
                            error_type=kb_data['error_type'],
                            error_pattern=ErrorPattern(kb_data['error_pattern']),
                            root_cause=kb_data['root_cause'],
                            solution_approach=kb_data['solution_approach'],
                            fix_code=kb_data['fix_code'],
                            explanation=kb_data['explanation'],
                            success_rate=kb_data.get('success_rate', 0.0),
                            usage_count=kb_data.get('usage_count', 0),
                            last_used=kb_data.get('last_used'),
                            created_at=kb_data.get('created_at', time.time()),
                            updated_at=kb_data.get('updated_at', time.time()),
                            tags=kb_data.get('tags', [])
                        )
                        self._knowledge_base[kb.knowledge_id] = kb
                logger.info(f"已加载 {len(self._knowledge_base)} 条脑库知识")
            except Exception as e:
                logger.error(f"加载脑库知识失败: {str(e)}")

    def _save_knowledge_base(self):
        """保存脑库知识"""
        try:
            data = {
                'last_updated': time.time(),
                'knowledge': [kb.to_dict() for kb in self._knowledge_base.values()]
            }
            with open(self._db_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
        except Exception as e:
            logger.error(f"保存脑库知识失败: {str(e)}")

    def _register_fix_strategies(self):
        """注册修复策略"""
        self._fix_strategies = {
            ErrorPattern.SYNTAX_ERROR: self._fix_syntax_error,
            ErrorPattern.IMPORT_ERROR: self._fix_import_error,
            ErrorPattern.NAME_ERROR: self._fix_name_error,
            ErrorPattern.TYPE_ERROR: self._fix_type_error,
            ErrorPattern.ATTRIBUTE_ERROR: self._fix_attribute_error,
            ErrorPattern.INDEX_ERROR: self._fix_index_error,
            ErrorPattern.KEY_ERROR: self._fix_key_error,
        }

    def analyze_error(self, error: Exception, file_path: str = "", context: Optional[Dict] = None) -> ErrorAnalysis:
        """分析错误"""
        error_type = type(error).__name__
        error_message = str(error)
        tb = traceback.extract_tb(error.__traceback__)
        
        line_number = 0
        column = 0
        code_snippet = ""
        
        if tb:
            frame = tb[-1]
            line_number = frame.lineno or 0
            file_path = frame.filename or file_path
            code_snippet = frame.line or ""
        
        pattern = self._classify_error(error_type, error_message)
        
        suggestions = self._generate_suggestions(pattern, error_message)
        
        error_id = f"ERR-ANALYSIS-{datetime.now().strftime('%Y%m%d%H%M%S')}-{len(self._knowledge_base)}"
        
        return ErrorAnalysis(
            error_id=error_id,
            error_type=error_type,
            error_message=error_message,
            file_path=file_path,
            line_number=line_number,
            column=column,
            code_snippet=code_snippet,
            pattern=pattern,
            suggestions=suggestions
        )

    def _classify_error(self, error_type: str, error_message: str) -> ErrorPattern:
        """分类错误"""
        error_type_lower = error_type.lower()
        msg_lower = error_message.lower()
        
        if error_type_lower == 'keyerror':
            return ErrorPattern.KEY_ERROR
        elif error_type_lower == 'indexerror':
            return ErrorPattern.INDEX_ERROR
        elif error_type_lower == 'typeerror':
            return ErrorPattern.TYPE_ERROR
        elif error_type_lower == 'nameerror':
            return ErrorPattern.NAME_ERROR
        elif error_type_lower == 'attributeerror':
            return ErrorPattern.ATTRIBUTE_ERROR
        elif error_type_lower == 'importerror' or error_type_lower == 'modulenotfounderror':
            return ErrorPattern.IMPORT_ERROR
        elif error_type_lower == 'valueerror':
            return ErrorPattern.VALUE_ERROR
        elif error_type_lower == 'syntaxerror' or 'syntax' in msg_lower or 'invalid syntax' in msg_lower:
            return ErrorPattern.SYNTAX_ERROR
        elif 'import' in msg_lower or 'modulenotfound' in msg_lower:
            return ErrorPattern.IMPORT_ERROR
        elif 'name' in msg_lower:
            return ErrorPattern.NAME_ERROR
        elif 'type' in msg_lower:
            return ErrorPattern.TYPE_ERROR
        elif 'attribute' in msg_lower:
            return ErrorPattern.ATTRIBUTE_ERROR
        elif 'index' in msg_lower:
            return ErrorPattern.INDEX_ERROR
        elif 'key' in msg_lower:
            return ErrorPattern.KEY_ERROR
        elif 'value' in msg_lower:
            return ErrorPattern.VALUE_ERROR
        else:
            return ErrorPattern.UNKNOWN_ERROR

    def _generate_suggestions(self, pattern: ErrorPattern, error_message: str) -> List[str]:
        """生成修复建议"""
        suggestions = {
            ErrorPattern.SYNTAX_ERROR: [
                "检查代码缩进是否正确",
                "检查括号是否匹配",
                "检查是否有缺少的冒号",
                "检查字符串引号是否匹配"
            ],
            ErrorPattern.IMPORT_ERROR: [
                "确认模块已安装",
                "检查模块名称拼写",
                "尝试使用完整的模块路径",
                "检查Python路径设置"
            ],
            ErrorPattern.NAME_ERROR: [
                "检查变量名拼写",
                "确认变量已定义",
                "检查变量作用域",
                "确认导入语句正确"
            ],
            ErrorPattern.TYPE_ERROR: [
                "检查数据类型",
                "添加类型转换",
                "检查函数参数类型",
                "使用默认值"
            ],
            ErrorPattern.ATTRIBUTE_ERROR: [
                "检查属性名拼写",
                "确认对象有该属性",
                "检查导入的模块",
                "使用hasattr检查"
            ],
            ErrorPattern.INDEX_ERROR: [
                "检查索引范围",
                "使用len()检查长度",
                "确保列表不为空",
                "使用try-except包装"
            ],
            ErrorPattern.KEY_ERROR: [
                "检查字典键名",
                "使用get()方法",
                "检查键是否存在",
                "使用setdefault"
            ],
            ErrorPattern.UNKNOWN_ERROR: [
                "查看完整错误信息",
                "使用try-except捕获",
                "添加日志调试",
                "检查输入参数"
            ]
        }
        return suggestions.get(pattern, suggestions[ErrorPattern.UNKNOWN_ERROR])

    def _fix_syntax_error(self, analysis: ErrorAnalysis) -> FixSolution:
        """修复语法错误"""
        fixed_code = analysis.code_snippet
        
        if "'" in analysis.code_snippet and '"' not in analysis.code_snippet:
            pass
        
        return FixSolution(
            solution_id=self._generate_solution_id(),
            error_pattern=analysis.pattern,
            strategy=FixStrategy.FIX_SYTAX,
            original_code=analysis.code_snippet,
            fixed_code=fixed_code,
            explanation="检查并修复语法错误",
            confidence=0.8
        )

    def _fix_import_error(self, analysis: ErrorAnalysis) -> FixSolution:
        """修复导入错误"""
        match = re.search(r"ModuleNotFoundError: No module named '(\w+)'", analysis.error_message)
        module_name = match.group(1) if match else "unknown"
        
        fixed_code = f"# 尝试导入模块\ntry:\n    import {module_name}\nexcept ImportError:\n    import subprocess\n    subprocess.run(['pip', 'install', '{module_name}'])\n    import {module_name}"
        
        return FixSolution(
            solution_id=self._generate_solution_id(),
            error_pattern=analysis.pattern,
            strategy=FixStrategy.ADD_IMPORT,
            original_code=analysis.code_snippet,
            fixed_code=fixed_code,
            explanation=f"安装并导入缺失的模块 {module_name}",
            confidence=0.9
        )

    def _fix_name_error(self, analysis: ErrorAnalysis) -> FixSolution:
        """修复名称错误"""
        match = re.search(r"name '(\w+)' is not defined", analysis.error_message)
        var_name = match.group(1) if match else "unknown"
        
        fixed_code = f"# 定义缺失的变量\n{var_name} = None  # TODO: 根据上下文设置合适的默认值"
        
        return FixSolution(
            solution_id=self._generate_solution_id(),
            error_pattern=analysis.pattern,
            strategy=FixStrategy.FIX_VARIABLE,
            original_code=analysis.code_snippet,
            fixed_code=fixed_code,
            explanation=f"定义缺失的变量 {var_name}",
            confidence=0.85
        )

    def _fix_type_error(self, analysis: ErrorAnalysis) -> FixSolution:
        """修复类型错误"""
        fixed_code = f"# 类型转换\n# 原始代码: {analysis.code_snippet}\n# 请添加适当的类型转换"
        
        return FixSolution(
            solution_id=self._generate_solution_id(),
            error_pattern=analysis.pattern,
            strategy=FixStrategy.FIX_TYPE,
            original_code=analysis.code_snippet,
            fixed_code=fixed_code,
            explanation="添加适当的类型转换或检查类型",
            confidence=0.7
        )

    def _fix_attribute_error(self, analysis: ErrorAnalysis) -> FixSolution:
        """修复属性错误"""
        match = re.search(r"module '(\w+)' has no attribute '(\w+)'", analysis.error_message)
        if match:
            module_name, attr_name = match.groups()
            fixed_code = f"# 检查模块属性\nif hasattr({module_name}, '{attr_name}'):\n    result = {module_name}.{attr_name}\nelse:\n    # 处理属性不存在的情况\n    pass"
        else:
            fixed_code = "# 使用hasattr检查属性\nif hasattr(obj, 'attribute'):\n    result = obj.attribute"
        
        return FixSolution(
            solution_id=self._generate_solution_id(),
            error_pattern=analysis.pattern,
            strategy=FixStrategy.ADD_CHECK,
            original_code=analysis.code_snippet,
            fixed_code=fixed_code,
            explanation="添加属性存在性检查",
            confidence=0.85
        )

    def _fix_index_error(self, analysis: ErrorAnalysis) -> FixSolution:
        """修复索引错误"""
        fixed_code = f"# 安全索引访问\ntry:\n    # 原始代码: {analysis.code_snippet}\n    result = items[index]\nexcept IndexError:\n    # 处理索引越界\n    result = None"
        
        return FixSolution(
            solution_id=self._generate_solution_id(),
            error_pattern=analysis.pattern,
            strategy=FixStrategy.WRAP_TRY,
            original_code=analysis.code_snippet,
            fixed_code=fixed_code,
            explanation="使用try-except包装并添加索引检查",
            confidence=0.9
        )

    def _fix_key_error(self, analysis: ErrorAnalysis) -> FixSolution:
        """修复键错误"""
        match = re.search(r"KeyError: (.+)", analysis.error_message)
        key_name = match.group(1) if match else "unknown"
        
        fixed_code = f"# 安全字典访问\nvalue = data.get({key_name})  # 使用get方法避免KeyError"
        
        return FixSolution(
            solution_id=self._generate_solution_id(),
            error_pattern=analysis.pattern,
            strategy=FixStrategy.ADD_CHECK,
            original_code=analysis.code_snippet,
            fixed_code=fixed_code,
            explanation=f"使用dict.get()方法安全访问键 {key_name}",
            confidence=0.95
        )

    def _generate_solution_id(self) -> str:
        """生成方案ID"""
        return f"SOL-{datetime.now().strftime('%Y%m%d%H%M%S')}-{len(self._knowledge_base)}"

    def find_solution_in_knowledge(self, pattern: ErrorPattern, error_message: str) -> Optional[BrainKnowledge]:
        """从脑库中查找解决方案"""
        with self._lock:
            for kb in self._knowledge_base.values():
                if kb.error_pattern == pattern:
                    if any(tag in error_message.lower() for tag in kb.tags):
                        kb.usage_count += 1
                        kb.last_used = time.time()
                        return kb
                    if kb.success_rate > 0.8:
                        return kb
        return None

    def apply_fix(self, analysis: ErrorAnalysis) -> FixSolution:
        """应用修复"""
        kb_solution = self.find_solution_in_knowledge(analysis.pattern, analysis.error_message)
        
        if kb_solution:
            logger.info(f"从脑库找到解决方案: {kb_solution.knowledge_id}")
            return FixSolution(
                solution_id=self._generate_solution_id(),
                error_pattern=analysis.pattern,
                strategy=FixStrategy.UNKNOWN,
                original_code=analysis.code_snippet,
                fixed_code=kb_solution.fix_code,
                explanation=f"应用脑库方案: {kb_solution.solution_approach}",
                confidence=kb_solution.success_rate
            )
        
        fix_func = self._fix_strategies.get(analysis.pattern)
        if fix_func:
            return fix_func(analysis)
        
        return FixSolution(
            solution_id=self._generate_solution_id(),
            error_pattern=analysis.pattern,
            strategy=FixStrategy.UNKNOWN,
            original_code=analysis.code_snippet,
            fixed_code=analysis.code_snippet,
            explanation="未知错误,请手动检查",
            confidence=0.0
        )

    def learn_from_fix(self, analysis: ErrorAnalysis, solution: FixSolution, success: bool):
        """从修复中学习"""
        if not success:
            return
        
        knowledge_id = f"KB-{analysis.pattern.value}-{len(self._knowledge_base)}"
        
        kb = BrainKnowledge(
            knowledge_id=knowledge_id,
            error_type=analysis.error_type,
            error_pattern=analysis.pattern,
            root_cause=analysis.error_message,
            solution_approach=solution.explanation,
            fix_code=solution.fixed_code,
            explanation=f"成功修复 {analysis.error_type}: {solution.explanation}",
            success_rate=1.0 if success else 0.0,
            usage_count=1,
            last_used=time.time(),
            tags=self._extract_tags(analysis.error_message)
        )
        
        with self._lock:
            self._knowledge_base[knowledge_id] = kb
        
        self._save_knowledge_base()
        logger.info(f"脑库知识已更新: {knowledge_id}")

    def _extract_tags(self, error_message: str) -> List[str]:
        """提取标签"""
        tags = []
        keywords = ['import', 'module', 'name', 'type', 'attribute', 'index', 'key', 'value', 'syntax']
        
        msg_lower = error_message.lower()
        for keyword in keywords:
            if keyword in msg_lower:
                tags.append(keyword)
        
        return tags[:5]

    def auto_fix_and_learn(self, error: Exception, file_path: str = "", context: Optional[Dict] = None) -> Tuple[ErrorAnalysis, FixSolution]:
        """自动修复并学习"""
        analysis = self.analyze_error(error, file_path, context)
        solution = self.apply_fix(analysis)
        
        self.learn_from_fix(analysis, solution, success=solution.confidence > 0.7)
        
        return analysis, solution

    def get_knowledge_base_stats(self) -> Dict:
        """获取脑库统计"""
        with self._lock:
            total = len(self._knowledge_base)
            patterns = {}
            for kb in self._knowledge_base.values():
                pattern_name = kb.error_pattern.value
                patterns[pattern_name] = patterns.get(pattern_name, 0) + 1
            
            avg_success = sum(kb.success_rate for kb in self._knowledge_base.values()) / total if total > 0 else 0
            
            return {
                'total_knowledge': total,
                'patterns': patterns,
                'avg_success_rate': round(avg_success, 2),
                'total_usage': sum(kb.usage_count for kb in self._knowledge_base.values())
            }

    def search_knowledge(self, query: str) -> List[BrainKnowledge]:
        """搜索脑库知识"""
        results = []
        query_lower = query.lower()
        
        with self._lock:
            for kb in self._knowledge_base.values():
                if (query_lower in kb.error_type.lower() or
                    query_lower in kb.root_cause.lower() or
                    query_lower in kb.solution_approach.lower() or
                    any(query_lower in tag for tag in kb.tags)):
                    results.append(kb)
        
        return sorted(results, key=lambda x: x.usage_count, reverse=True)

    def get_all_knowledge(self) -> List[BrainKnowledge]:
        """获取所有脑库知识"""
        with self._lock:
            return list(self._knowledge_base.values())

    def update_knowledge(self, knowledge_id: str, updates: Dict) -> bool:
        """更新脑库知识"""
        with self._lock:
            if knowledge_id in self._knowledge_base:
                kb = self._knowledge_base[knowledge_id]
                for key, value in updates.items():
                    if hasattr(kb, key):
                        setattr(kb, key, value)
                kb.updated_at = time.time()
                self._save_knowledge_base()
                return True
        return False

    def delete_knowledge(self, knowledge_id: str) -> bool:
        """删除脑库知识"""
        with self._lock:
            if knowledge_id in self._knowledge_base:
                del self._knowledge_base[knowledge_id]
                self._save_knowledge_base()
                return True
        return False


# 创建全局实例
ai_auto_fix_service = AIAutoFixService()
