# -*- coding: utf-8 -*-
"""
本地AI MCP Server (零依赖, stdio 传输)
======================================
将本地AI引擎封装为 MCP (Model Context Protocol) Server, 供 Trae 直接调用。

路由策略: 本地 Ollama (qwen2.5:7b, 零token) 优先 → 火山引擎兜底

提供的 MCP Tools:
  - local_ai_chat        : 本地AI对话 (零token优先)
  - local_ai_think       : 深度思考/方案设计
  - local_ai_code_review : 代码审查
  - local_ai_bug_locate  : Bug根因定位
  - local_ai_health      : 引擎健康状态

启动方式 (Trae MCP 配置):
  command: python3
  args: ["/绝对路径/flask-app/ai_engines/local_ai_mcp_server.py"]

零外部依赖: 仅使用 Python 3.9+ 标准库
"""
from __future__ import annotations

import json
import os
import sys
import traceback
from typing import Any, Dict

# 确保 ai_engines 目录在 sys.path
_AI_ENGINES_DIR = os.path.dirname(os.path.abspath(__file__))
if _AI_ENGINES_DIR not in sys.path:
    sys.path.insert(0, _AI_ENGINES_DIR)


# ============================================================
# MCP 工具实现
# ============================================================

def tool_local_ai_chat(prompt: str, system: str = "", flow_id: str = "") -> Dict[str, Any]:
    """本地AI对话 — 优先走本地Ollama(零token), 不可用时火山引擎兜底"""
    from local_ai_unified_gateway import chat
    result = chat(prompt, system, flow_id or "mcp_local_ai_chat")
    return {
        "content": [{"type": "text", "text": result.get("response", "")}],
        "meta": {
            "route": result.get("route", ""),
            "model": result.get("model", ""),
            "tokens_saved": result.get("tokens_saved", 0),
            "duration_ms": result.get("duration_ms", 0),
            "success": result.get("success", False),
        }
    }


def tool_local_ai_code(prompt: str, system: str = "", flow_id: str = "") -> Dict[str, Any]:
    """本地AI编码 — 代码生成/补全/重构, 优先使用编码专用模型(零token)"""
    from local_ai_unified_gateway import code
    result = code(prompt, system, flow_id or "mcp_local_ai_code")
    return {
        "content": [{"type": "text", "text": result.get("response", "")}],
        "meta": {
            "route": result.get("route", ""),
            "model": result.get("model", ""),
            "tokens_saved": result.get("tokens_saved", 0),
            "duration_ms": result.get("duration_ms", 0),
            "success": result.get("success", False),
        }
    }


def tool_local_ai_think(question: str, context: str = "", flow_id: str = "") -> Dict[str, Any]:
    """深度思考助理 — 推理/决策/方案设计/Bug定位"""
    from local_ai_unified_gateway import think
    result = think(question, context, flow_id or "mcp_local_ai_think")
    return {
        "content": [{"type": "text", "text": result.get("response", "")}],
        "meta": {
            "route": result.get("route", ""),
            "model": result.get("model", ""),
            "tokens_saved": result.get("tokens_saved", 0),
            "duration_ms": result.get("duration_ms", 0),
            "success": result.get("success", False),
        }
    }


def tool_local_ai_code_review(code: str, flow_id: str = "") -> Dict[str, Any]:
    """代码审查 — 检查代码质量、安全、性能问题"""
    from local_ai_unified_gateway import review
    result = review(code, flow_id or "mcp_local_ai_code_review")
    return {
        "content": [{"type": "text", "text": result.get("response", "")}],
        "meta": {
            "route": result.get("route", ""),
            "model": result.get("model", ""),
            "tokens_saved": result.get("tokens_saved", 0),
            "duration_ms": result.get("duration_ms", 0),
            "success": result.get("success", False),
        }
    }


def tool_local_ai_bug_locate(error_desc: str, code: str = "", flow_id: str = "") -> Dict[str, Any]:
    """Bug根因定位 — 分析错误描述和相关代码, 给出修复方案"""
    from thinking_assistant import locate_bug
    result = locate_bug(error_desc, code, flow_id or "mcp_local_ai_bug_locate")
    return {
        "content": [{"type": "text", "text": result.get("response", "")}],
        "meta": {
            "route": result.get("route", ""),
            "model": result.get("model", ""),
            "tokens_saved": result.get("tokens_saved", 0),
            "duration_ms": result.get("duration_ms", 0),
            "success": result.get("success", False),
        }
    }


def tool_local_ai_health() -> Dict[str, Any]:
    """本地AI引擎健康状态 — 查看本地Ollama和火山引擎可用性"""
    from local_ai_unified_gateway import health
    result = health()
    return {
        "content": [{"type": "text", "text": json.dumps(result, ensure_ascii=False, indent=2)}],
        "meta": {"success": True}
    }


# ============================================================
# MCP 工具注册表
# ============================================================

_TOOLS = {
    "local_ai_chat": {
        "handler": tool_local_ai_chat,
        "schema": {
            "name": "local_ai_chat",
            "description": "本地AI对话 - 优先走本地Ollama(零token消耗), 不可用时火山引擎兜底。适合日常问答、文案生成、知识咨询等场景。",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "prompt": {"type": "string", "description": "用户提问内容"},
                    "system": {"type": "string", "description": "系统提示词(可选), 用于设定AI角色"},
                    "flow_id": {"type": "string", "description": "流程ID(可选), 用于日志追踪"},
                },
                "required": ["prompt"]
            }
        }
    },
    "local_ai_code": {
        "handler": tool_local_ai_code,
        "schema": {
            "name": "local_ai_code",
            "description": "本地AI编码 - 代码生成/补全/重构, 优先使用编码专用模型(qwen2.5-coder), 零token消耗。【只输出代码, 不执行指令】: 仅返回代码文本, 不会也不应输出任何shell/终端命令(如pip/python/git/npm)、安装或运行步骤; 需要执行命令的任务(跑测试/装依赖/git操作)不要交给本工具。适合写函数、修Bug、代码转换等场景。",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "prompt": {"type": "string", "description": "编码需求描述"},
                    "system": {"type": "string", "description": "系统提示词(可选)"},
                    "flow_id": {"type": "string", "description": "流程ID(可选)"},
                },
                "required": ["prompt"]
            }
        }
    },
    "local_ai_think": {
        "handler": tool_local_ai_think,
        "schema": {
            "name": "local_ai_think",
            "description": "深度思考助理 - 擅长深度推理、方案设计、Bug定位。输出结构化分析。",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "question": {"type": "string", "description": "需要思考的问题"},
                    "context": {"type": "string", "description": "上下文信息(可选)"},
                    "flow_id": {"type": "string", "description": "流程ID(可选)"},
                },
                "required": ["question"]
            }
        }
    },
    "local_ai_code_review": {
        "handler": tool_local_ai_code_review,
        "schema": {
            "name": "local_ai_code_review",
            "description": "代码审查 - 检查代码质量、安全漏洞、性能问题, 给出改进建议。",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "code": {"type": "string", "description": "需要审查的代码"},
                    "flow_id": {"type": "string", "description": "流程ID(可选)"},
                },
                "required": ["code"]
            }
        }
    },
    "local_ai_bug_locate": {
        "handler": tool_local_ai_bug_locate,
        "schema": {
            "name": "local_ai_bug_locate",
            "description": "Bug根因定位 - 根据错误描述和相关代码, 定位问题根因并给出修复方案。修复方案只给代码修改(代码块), 不输出任何shell/终端命令或安装、运行指令。",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "error_desc": {"type": "string", "description": "错误描述或异常信息"},
                    "code": {"type": "string", "description": "相关代码(可选)"},
                    "flow_id": {"type": "string", "description": "流程ID(可选)"},
                },
                "required": ["error_desc"]
            }
        }
    },
    "local_ai_health": {
        "handler": tool_local_ai_health,
        "schema": {
            "name": "local_ai_health",
            "description": "本地AI引擎健康状态 - 查看本地Ollama和火山引擎的可用性、模型列表、路由策略。",
            "inputSchema": {
                "type": "object",
                "properties": {},
            }
        }
    },
}


# ============================================================
# MCP stdio 协议实现 (JSON-RPC 2.0)
# ============================================================

def _send(msg: Dict[str, Any]) -> None:
    """发送 JSON-RPC 消息到 stdout"""
    sys.stdout.write(json.dumps(msg, ensure_ascii=False) + "\n")
    sys.stdout.flush()


def _handle_request(msg: Dict[str, Any]) -> None:
    """处理 MCP 请求"""
    method = msg.get("method", "")
    msg_id = msg.get("id")
    params = msg.get("params", {})

    try:
        if method == "initialize":
            _send({
                "jsonrpc": "2.0",
                "id": msg_id,
                "result": {
                    "protocolVersion": "2024-11-05",
                    "serverInfo": {"name": "local-ai-mcp", "version": "1.0.0"},
                    "capabilities": {
                        "tools": {"listChanged": False},
                    }
                }
            })

        elif method == "tools/list":
            tools = [t["schema"] for t in _TOOLS.values()]
            _send({
                "jsonrpc": "2.0",
                "id": msg_id,
                "result": {"tools": tools}
            })

        elif method == "tools/call":
            tool_name = params.get("name", "")
            arguments = params.get("arguments", {})
            tool = _TOOLS.get(tool_name)
            if not tool:
                _send({
                    "jsonrpc": "2.0",
                    "id": msg_id,
                    "result": {
                        "content": [{"type": "text", "text": f"未知工具: {tool_name}"}],
                        "isError": True
                    }
                })
                return
            try:
                result = tool["handler"](**arguments)
                _send({
                    "jsonrpc": "2.0",
                    "id": msg_id,
                    "result": result
                })
            except Exception as e:
                _send({
                    "jsonrpc": "2.0",
                    "id": msg_id,
                    "result": {
                        "content": [{"type": "text", "text": f"工具执行错误: {e}\n{traceback.format_exc()}"}],
                        "isError": True
                    }
                })

        else:
            _send({
                "jsonrpc": "2.0",
                "id": msg_id,
                "error": {"code": -32601, "message": f"Method not found: {method}"}
            })

    except Exception as e:
        _send({
            "jsonrpc": "2.0",
            "id": msg_id,
            "error": {"code": -32603, "message": f"Internal error: {e}"}
        })


def main() -> None:
    """MCP Server 主循环 (stdio)"""
    for line in sys.stdin:
        line = line.strip()
        if not line:
            continue
        try:
            msg = json.loads(line)
        except json.JSONDecodeError:
            continue

        # 通知 (无 id) 不回复
        if "id" not in msg:
            continue

        _handle_request(msg)


if __name__ == "__main__":
    main()
