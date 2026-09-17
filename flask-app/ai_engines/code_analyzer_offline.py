# -*- coding: utf-8 -*-
"""
离线代码分析器 (Offline Code Analyzer)
======================================
Trae 优先离线编译代码的核心组件

功能:
  1. 语法检查 (py_compile / ast 解析)
  2. 编译错误定位 (行号/列号/错误类型)
  3. AI 辅助分析 (本地 Ollama 解释错误+修复建议)
  4. 代码质量检查 (复杂度/重复/未使用变量)
  5. 优化建议 (本地 Ollama 生成)

特点:
  - 纯离线运行,零token消耗
  - 语法检查用 Python 内置 ast 模块(无需安装)
  - AI辅助分析走本地Ollama(qwen2.5:7b)
"""
from __future__ import annotations

import ast
import os
import py_compile
import sys
import tempfile
from typing import Any, Dict, List, Optional

# 确保 ai_engines 目录在 sys.path
_AI_ENGINES_DIR = os.path.dirname(os.path.abspath(__file__))
if _AI_ENGINES_DIR not in sys.path:
    sys.path.insert(0, _AI_ENGINES_DIR)


def _syntax_check(file_path: str) -> Dict[str, Any]:
    """语法检查 (ast 解析)"""
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            source = f.read()
        ast.parse(source, filename=file_path)
        return {"syntax_ok": True, "errors": [], "line_count": source.count("\n") + 1}
    except SyntaxError as e:
        return {
            "syntax_ok": False,
            "errors": [{
                "line": e.lineno,
                "col": e.offset,
                "type": "SyntaxError",
                "msg": e.msg,
                "text": e.text.strip() if e.text else "",
            }],
            "line_count": 0,
        }
    except Exception as e:
        return {"syntax_ok": False, "errors": [{"line": 0, "type": "IOError", "msg": str(e)}], "line_count": 0}


def _compile_check(file_path: str) -> Dict[str, Any]:
    """编译检查 (py_compile)"""
    try:
        py_compile.compile(file_path, doraise=True)
        return {"compile_ok": True, "errors": []}
    except py_compile.PyCompileError as e:
        return {
            "compile_ok": False,
            "errors": [{"line": e.lineno or 0, "type": "CompileError", "msg": str(e)}],
        }
    except Exception as e:
        return {"compile_ok": False, "errors": [{"line": 0, "type": "Error", "msg": str(e)}]}


def _quality_check(file_path: str) -> Dict[str, Any]:
    """代码质量检查 (复杂度/未使用变量/导入检查)"""
    issues: List[Dict] = []
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            source = f.read()
        tree = ast.parse(source, filename=file_path)

        # 检查未使用的导入
        imports = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    imports.add(alias.asname or alias.name.split(".")[0])
            elif isinstance(node, ast.ImportFrom):
                for alias in node.names:
                    imports.add(alias.asname or alias.name)

        # 检查导入是否在源码中使用
        for imp in imports:
            if imp not in source.replace(f"import {imp}", ""):
                # 粗略检查: 如果只出现在import行,视为未使用
                import_count = source.count(imp)
                if import_count <= 2:  # import行出现1-2次
                    issues.append({"type": "unused_import", "name": imp, "severity": "LOW"})

        # 函数复杂度检查(嵌套深度)
        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                # 计算嵌套深度
                depth = _max_nesting_depth(node)
                if depth > 5:
                    issues.append({
                        "type": "high_complexity",
                        "function": node.name,
                        "nesting_depth": depth,
                        "severity": "MEDIUM",
                    })

        # 检查 bare except
        for node in ast.walk(tree):
            if isinstance(node, ast.ExceptHandler) and node.type is None:
                issues.append({"type": "bare_except", "line": node.lineno, "severity": "MEDIUM"})

    except Exception as e:
        issues.append({"type": "analyze_error", "msg": str(e), "severity": "LOW"})

    return {"quality_issues": issues, "issue_count": len(issues)}


def _max_nesting_depth(node, current=0):
    """计算最大嵌套深度"""
    if not hasattr(node, "body"):
        return current
    max_depth = current
    for child in ast.walk(node):
        if isinstance(child, (ast.If, ast.For, ast.While, ast.With, ast.Try)):
            depth = current + 1
            if depth > max_depth:
                max_depth = depth
    return max_depth


def _ai_analyze_errors(file_path: str, errors: List[Dict], flow_id: Optional[str] = None) -> str:
    """用本地 Ollama 分析错误并给出修复建议"""
    try:
        from ai_ollama_engine import chat as ollama_chat, is_available
        if not is_available():
            return "Ollama不可用,无法提供AI分析建议"

        with open(file_path, "r", encoding="utf-8") as f:
            source = f.read()[:2000]  # 截取前2000字符

        error_desc = "\n".join([f"  行{e.get('line', '?')}: {e.get('type', '?')} - {e.get('msg', '?')}"
                                for e in errors])
        prompt = f"""分析以下Python代码的错误并给出修复建议:

文件: {file_path}
错误:
{error_desc}

代码(前2000字符):
```
{source}
```

请给出: 1.错误根因 2.修复方案 3.修复后的代码片段"""
        result = ollama_chat(prompt, system="你是Python代码分析专家", flow_id=flow_id, prefer_7b=True)
        return result.get("response", "AI分析失败") if result["success"] else "AI分析失败"
    except Exception as e:
        return f"AI分析异常: {e}"


def analyze_file(file_path: str, flow_id: Optional[str] = None) -> Dict[str, Any]:
    """
    代码分析入口 (语法+编译+质量+AI建议)
    """
    if not os.path.exists(file_path):
        return {"success": False, "error": f"文件不存在: {file_path}"}

    syntax = _syntax_check(file_path)
    quality = _quality_check(file_path)
    ai_suggestion = ""

    if not syntax["syntax_ok"] or quality["issue_count"] > 0:
        # 有问题才调AI分析(节省推理资源)
        ai_suggestion = _ai_analyze_errors(file_path, syntax["errors"] + quality["quality_issues"], flow_id)

    return {
        "success": True,
        "file": file_path,
        "syntax": syntax,
        "quality": quality,
        "ai_suggestion": ai_suggestion,
        "route": "local_ollama" if ai_suggestion else "offline_static",
        "gateway": "local_ai_unified_gateway",
    }


def compile_check_file(file_path: str, flow_id: Optional[str] = None) -> Dict[str, Any]:
    """
    离线编译检查入口 (py_compile + AI错误解释)
    """
    if not os.path.exists(file_path):
        return {"success": False, "error": f"文件不存在: {file_path}"}

    compile_result = _compile_check(file_path)
    ai_suggestion = ""

    if not compile_result["compile_ok"]:
        ai_suggestion = _ai_analyze_errors(file_path, compile_result["errors"], flow_id)

    return {
        "success": True,
        "file": file_path,
        "compile": compile_result,
        "ai_suggestion": ai_suggestion,
        "route": "local_ollama" if ai_suggestion else "offline_static",
        "gateway": "local_ai_unified_gateway",
    }


def health() -> Dict[str, Any]:
    return {
        "engine": "code_analyzer_offline",
        "features": ["syntax_check", "compile_check", "quality_check", "ai_analyze"],
        "ai_backend": "ollama_qwen2.5_7b",
        "offline_capable": True,
    }
