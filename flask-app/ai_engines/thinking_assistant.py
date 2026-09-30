# -*- coding: utf-8 -*-
"""
思考助理 (Thinking Assistant)
=============================
Trae 思考助理优先走本地 Ollama,零token消耗

功能:
  1. 深度推理 (问题分析→关键要素→推理过程→结论)
  2. 方案设计 (需求→约束→选项→推荐方案)
  3. 决策辅助 (选项对比→风险评估→推荐)
  4. Bug定位 (错误现象→假设→验证→根因)
  5. 架构思考 (需求→约束→方案→权衡)

特点:
  - 优先本地 Ollama (qwen2.5:7b), 零token
  - 火山引擎兜底
  - 结构化输出(问题分析/推理过程/结论)
"""
from __future__ import annotations

import os
import sys
from typing import Any, Dict, Optional

# 确保 ai_engines 目录在 sys.path
_AI_ENGINES_DIR = os.path.dirname(os.path.abspath(__file__))
if _AI_ENGINES_DIR not in sys.path:
    sys.path.insert(0, _AI_ENGINES_DIR)


def _think(prompt: str, system: str, flow_id: Optional[str] = None) -> Dict[str, Any]:
    """统一思考路由"""
    # 1. 本地 Ollama 优先
    try:
        from ai_ollama_engine import chat as ollama_chat, is_available
        if is_available():
            result = ollama_chat(prompt, system, flow_id, prefer_7b=True)
            if result["success"]:
                result["route"] = "local_ollama"
                result["engine"] = "thinking_assistant"
                return result
    except Exception:
        pass

    # 2. 火山引擎兜底
    try:
        from ai_volcengine_engine import chat as ark_chat, is_available as ark_available
        if ark_available():
            result = ark_chat(prompt, system, flow_id)
            if result["success"]:
                result["route"] = "cloud_volcengine"
                result["engine"] = "thinking_assistant"
                return result
    except Exception:
        pass

    return {
        "success": False, "response": "思考助理不可用(本地和云均离线)",
        "route": "none", "engine": "thinking_assistant", "error": "无可用引擎"
    }


def deep_think(question: str, context: str = "", flow_id: Optional[str] = None) -> Dict[str, Any]:
    """深度推理"""
    system = ("你是MTSCOS深度思考助理,擅长结构化推理。"
              "输出格式:\n## 问题分析\n## 关键要素\n## 推理过程\n## 结论")
    prompt = f"问题: {question}\n\n上下文:\n{context}\n\n请深度思考:"
    return _think(prompt, system, flow_id)


def design_plan(requirement: str, constraints: str = "", flow_id: Optional[str] = None) -> Dict[str, Any]:
    """方案设计"""
    system = ("你是MTSCOS方案设计助理,擅长架构设计。"
              "输出格式:\n## 需求分析\n## 约束条件\n## 方案选项\n## 推荐方案")
    prompt = f"需求: {requirement}\n\n约束:\n{constraints}\n\n请设计方案:"
    return _think(prompt, system, flow_id)


def make_decision(options: str, criteria: str = "", flow_id: Optional[str] = None) -> Dict[str, Any]:
    """决策辅助"""
    system = ("你是MTSCOS决策助理,擅长权衡分析。"
              "输出格式:\n## 选项对比\n## 风险评估\n## 推荐决策")
    prompt = f"选项:\n{options}\n\n决策标准:\n{criteria}\n\n请给出决策建议:"
    return _think(prompt, system, flow_id)


def locate_bug(error_desc: str, code: str = "", flow_id: Optional[str] = None):
    """Bug定位思考"""
    system = ("你是MTSCOS Bug定位助理,擅长根因分析。"
              "输出格式:\n## 错误现象\n## 假设列表\n## 验证过程\n## 根因结论\n## 修复方案(代码)\n"
              "铁律: 修复方案只能给出代码修改(用代码块给出改后的完整代码或关键片段), "
              "禁止输出任何shell/终端命令(如pip install/python/git/npm等), "
              "禁止要求或建议执行、运行、安装任何命令; 依赖问题只在代码注释中说明。")
    prompt = f"错误描述:\n{error_desc}\n\n相关代码:\n```\n{code}\n```\n\n请定位Bug根因:"
    return _think(prompt, system, flow_id)


def architecture_think(requirement: str, flow_id: Optional[str] = None) -> Dict[str, Any]:
    """架构思考"""
    system = ("你是MTSCOS架构思考助理,擅长系统设计。"
              "输出格式:\n## 需求解读\n## 架构约束\n## 方案设计\n## 权衡取舍")
    prompt = f"架构需求:\n{requirement}\n\n请进行架构思考:"
    return _think(prompt, system, flow_id)


def health() -> Dict[str, Any]:
    return {
        "engine": "thinking_assistant",
        "features": ["deep_think", "design_plan", "make_decision", "locate_bug", "architecture_think"],
        "ai_backend": "ollama_qwen2.5_7b_priority",
        "route_priority": "local_ollama > cloud_volcengine",
        "offline_capable": True,
    }
