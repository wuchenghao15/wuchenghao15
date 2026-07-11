# -*- coding: utf-8 -*-
"""
统一Auto API - 响应所有auto开头py文件功能
"""
import os
import sys
import importlib.util
import traceback
import re
from datetime import datetime
from flask import Blueprint, jsonify, request

auto_api = Blueprint('auto_api', __name__, url_prefix='/api/auto')

BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
AUTO_MODULES = {}
MODULE_RESULTS = {}
FAILURE_ANALYSIS = {}


def discover_auto_modules():
    """发现所有auto开头的python文件"""
    global AUTO_MODULES
    AUTO_MODULES = {}

    search_paths = [
        BASE_DIR,
        os.path.join(BASE_DIR, 'ai_engines'),
        os.path.join(BASE_DIR, 'app', 'api'),
    ]

    for search_path in search_paths:
        if not os.path.exists(search_path):
            continue
        for filename in os.listdir(search_path):
            if filename.startswith('auto') and filename.endswith('.py'):
                module_name = filename[:-3]
                file_path = os.path.join(search_path, filename)
                AUTO_MODULES[module_name] = file_path

    return AUTO_MODULES


def analyze_failure(error_message, _traceback_str=None):
    """分析模块加载失败原因并提供修复建议"""
    analysis = {
        "error_type": "Unknown",
        "missing_module": None,
        "fix_suggestion": None,
        "can_auto_fix": False
    }

    module_match = re.search(r"No module named '([^']+)'", error_message)
    import_match = re.search(r"cannot import name '([^']+)' from '([^']+)'", error_message)

    if module_match:
        missing = module_match.group(1)
        analysis["error_type"] = "ModuleNotFoundError"
        analysis["missing_module"] = missing

        if 'app.ai.' in missing:
            actual = missing.replace('app.ai.', '')
            analysis["fix_suggestion"] = f"尝试将 'app.ai.{actual}' 修改为 'ai_engines.{actual}'"
            analysis["can_auto_fix"] = True
        elif 'app.models.' in missing:
            analysis["fix_suggestion"] = f"检查模块路径 {missing} 是否正确"
        else:
            analysis["fix_suggestion"] = f"安装缺失模块: pip install {missing.split('.')[0]}"

    elif import_match:
        name = import_match.group(1)
        module = import_match.group(2)
        analysis["error_type"] = "ImportError"
        analysis["missing_module"] = f"{module}.{name}"
        analysis["fix_suggestion"] = f"检查 {module} 中是否存在 {name}"

    return analysis


def execute_module_function(module_name, function_name=None):
    """执行指定模块的函数"""
    result = {
        "module": module_name,
        "success": False,
        "timestamp": datetime.now().isoformat(),
        "data": None,
        "error": None,
        "error_analysis": None
    }

    try:
        if module_name not in AUTO_MODULES:
            result["error"] = f"模块 {module_name} 不存在"
            return result

        file_path = AUTO_MODULES[module_name]

        spec = importlib.util.spec_from_file_location(module_name, file_path)
        if not spec:
            result["error"] = "无法创建模块规范"
            return result

        module = importlib.util.module_from_spec(spec)
        sys.modules[module_name] = module
        spec.loader.exec_module(module)

        if function_name:
            if hasattr(module, function_name):
                func = getattr(module, function_name)
                if callable(func):
                    result["data"] = {"function": function_name, "exists": True}
                else:
                    result["data"] = {"function": function_name, "exists": False}
            else:
                result["data"] = {"function": function_name, "exists": False}
        else:
            classes = []
            functions = []
            for name in dir(module):
                if name.startswith('_'):
                    continue
                obj = getattr(module, name)
                if isinstance(obj, type) and obj.__module__ == module_name:
                    classes.append(name)
                elif callable(obj) and getattr(obj, '__module__', None) == module_name:
                    functions.append(name)
            result["data"] = {
                "classes": classes,
                "functions": functions,
                "file_path": file_path
            }

        result["success"] = True

    except Exception as e:
        result["error"] = f"{type(e).__name__}: {str(e)}"
        result["traceback"] = traceback.format_exc()
        result["error_analysis"] = analyze_failure(result["error"], result["traceback"])

    return result


@auto_api.route('/modules', methods=['GET'])
def list_auto_modules():
    """列出所有auto开头的python文件"""
    try:
        modules = discover_auto_modules()
        module_info = []
        for name, path in modules.items():
            module_info.append({
                "name": name,
                "file_path": path,
                "file_size": os.path.getsize(path) if os.path.exists(path) else 0,
                "modified_time": datetime.fromtimestamp(
                    os.path.getmtime(path)
                ).isoformat() if os.path.exists(path) else None
            })
        return jsonify({
            "success": True,
            "data": {
                "total": len(module_info),
                "modules": module_info
            }
        })
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@auto_api.route('/module/<module_name>', methods=['GET'])
def get_module_info(module_name):
    """获取指定auto模块的信息"""
    result = execute_module_function(module_name)
    return jsonify({
        "success": result["success"],
        "data": result["data"],
        "error": result["error"]
    })


@auto_api.route('/module/<module_name>/function/<function_name>', methods=['GET', 'POST'])
def get_module_function(module_name, function_name):
    """获取指定模块的指定函数信息"""
    result = execute_module_function(module_name, function_name)
    return jsonify({
        "success": result["success"],
        "data": result["data"],
        "error": result["error"]
    })


@auto_api.route('/module/<module_name>/execute', methods=['POST'])
def execute_module(module_name):
    """执行指定auto模块的主函数"""
    try:
        data = request.get_json() or {}
        function_name = data.get('function', 'main')

        result = execute_module_function(module_name)

        if not result["success"]:
            return jsonify({"success": False, "error": result["error"]}), 500

        return jsonify({
            "success": True,
            "data": {
                "module": module_name,
                "function": function_name,
                "info": result["data"],
                "timestamp": datetime.now().isoformat()
            }
        })
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@auto_api.route('/run-all', methods=['POST'])
def run_all_auto_modules():
    """运行所有auto模块的信息收集"""
    try:
        discover_auto_modules()
        results = {}
        failures = {}
        success_count = 0
        failed_count = 0

        for module_name in AUTO_MODULES.keys():
            result = execute_module_function(module_name)
            results[module_name] = {
                "success": result["success"],
                "error": result["error"] if not result["success"] else None,
                "summary": {
                    "classes_count": len(result["data"]["classes"]) if result["success"] and result["data"] else 0,
                    "functions_count": len(result["data"]["functions"]) if result["success"] and result["data"] else 0
                }
            }
            if result["success"]:
                success_count += 1
            else:
                failed_count += 1
                failures[module_name] = {
                    "error": result["error"],
                    "analysis": result["error_analysis"]
                }

        MODULE_RESULTS.clear()
        MODULE_RESULTS.update(results)
        FAILURE_ANALYSIS.clear()
        FAILURE_ANALYSIS.update(failures)

        return jsonify({
            "success": True,
            "data": {
                "total": len(AUTO_MODULES),
                "success": success_count,
                "failed": failed_count,
                "results": results,
                "failures": failures
            }
        })
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@auto_api.route('/failures', methods=['GET'])
def get_failures():
    """获取失败模块分析"""
    return jsonify({
        "success": True,
        "data": {
            "total": len(FAILURE_ANALYSIS),
            "failures": FAILURE_ANALYSIS
        }
    })


@auto_api.route('/results', methods=['GET'])
def get_results():
    """获取最近一次run-all的结果"""
    return jsonify({
        "success": True,
        "data": {
            "total": len(MODULE_RESULTS),
            "results": MODULE_RESULTS
        }
    })


@auto_api.route('/status', methods=['GET'])
def get_auto_api_status():
    """获取Auto API状态"""
    try:
        discover_auto_modules()
        return jsonify({
            "success": True,
            "data": {
                "api_name": "统一Auto API",
                "api_version": "1.0.0",
                "total_modules": len(AUTO_MODULES),
                "base_dir": BASE_DIR,
                "search_paths": [
                    BASE_DIR,
                    os.path.join(BASE_DIR, 'ai_engines'),
                    os.path.join(BASE_DIR, 'app', 'api')
                ],
                "status": "active",
                "timestamp": datetime.now().isoformat()
            }
        })
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@auto_api.route('/search', methods=['POST'])
def search_modules():
    """搜索auto模块"""
    try:
        data = request.get_json() or {}
        keyword = data.get('keyword', '').lower()

        discover_auto_modules()

        matched = []
        for name, path in AUTO_MODULES.items():
            if keyword in name.lower() or keyword in path.lower():
                matched.append({
                    "name": name,
                    "file_path": path
                })

        return jsonify({
            "success": True,
            "data": {
                "keyword": keyword,
                "matched_count": len(matched),
                "matched": matched
            }
        })
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


discover_auto_modules()
