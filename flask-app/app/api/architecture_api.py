# -*- coding: utf-8 -*-
"""
架构工程师AI员工 API
"""
import os
import sys
import logging
from flask import Blueprint, jsonify

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger('architecture_api')

architecture_api = Blueprint('architecture_api', __name__, url_prefix='/api/architecture')

BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, BASE_DIR)


@architecture_api.route('/analyze', methods=['GET'])
def analyze():
    """分析当前项目结构"""
    try:
        from architecture_engineer import ArchitectureEngineer
        engineer = ArchitectureEngineer()
        structure = engineer.analyze_structure()
        return jsonify({
            "success": True,
            "data": structure
        })
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@architecture_api.route('/optimize', methods=['POST'])
def optimize():
    """执行架构优化"""
    try:
        from architecture_engineer import ArchitectureEngineer
        engineer = ArchitectureEngineer()
        result = engineer.run_optimization()
        return jsonify({
            "success": True,
            "data": result
        })
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@architecture_api.route('/status', methods=['GET'])
def status():
    """获取架构工程师状态"""
    return jsonify({
        "success": True,
        "data": {
            "employee": "架构工程师 (ArchitectureEngineer)",
            "ai_id": "AI_ARCH_ENGINEER_001",
            "capabilities": [
                "项目结构分析",
                "目录自动整理",
                "文件分类归档",
                "架构优化建议",
                "架构报告生成"
            ],
            "status": "active",
            "base_dir": BASE_DIR
        }
    })
