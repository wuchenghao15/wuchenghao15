# -*- coding: utf-8 -*-
"""
Trae 调用本地AI组件示例代码 (flow_TRAE_EXAMPLE_CODE_20260904_001)
================================================================
覆盖四个场景:
  1. Python 导入调用示例  (直接 import 组件函数)
  2. Shell CLI 调用示例   (命令行调网关)
  3. MCP 工具集成示例     (封装为 MCP 工具供 Trae 调用)
  4. Skill 集成示例       (封装为 Trae Skill)

目标组件:
  - local_ai_unified_gateway  (本地AI统一网关)
  - code_analyzer_offline     (离线代码分析器)
  - thinking_assistant        (思考助理)

路由优先级: 本地 Ollama (qwen2.5:7b, 零token) > 火山引擎兜底
"""
from __future__ import annotations

import os
import sys

# ===== 路径初始化 (Trae 运行时需把 ai_engines 目录加入 sys.path) =====
_AI_ENGINES_DIR = os.path.dirname(os.path.abspath(__file__))
if _AI_ENGINES_DIR not in sys.path:
    sys.path.insert(0, _AI_ENGINES_DIR)


# ============================================================
# 1. Python 导入调用示例
# ============================================================

def example_python_chat():
    """示例1: 通过统一网关对话 (本地Ollama优先, 零token)"""
    from local_ai_unified_gateway import chat, health

    # 先看网关健康状态
    status = health()
    print(f"[网关状态] local_ollama={status['local_ollama'].get('available')}, "
          f"cloud={status['cloud_volcengine'].get('available')}")

    # 对话 — 优先走本地 Ollama, 不可用才走云端
    result = chat(
        prompt="解释 Python 装饰器的执行顺序",
        system="你是MTSCOS本地AI助手,简洁回答",
        flow_id="flow_TRAE_EXAMPLE_CODE_20260904_001"
    )
    if result["success"]:
        print(f"[路由] {result['route']} | [模型] {result['model']}")
        print(f"[节省tokens] {result.get('tokens_saved', 0)}")
        print(f"[回复] {result['response']}")
    else:
        print(f"[错误] {result.get('error')}")
    return result


def example_python_think():
    """示例2: 思考助理 — 深度推理 / 方案设计 / Bug定位"""
    from thinking_assistant import deep_think, design_plan, locate_bug, architecture_think

    # 深度推理
    r1 = deep_think(
        question="如何降低 OneDrive 占位符导致的 git 操作超时?",
        context="本地 pack 文件被回收为 0B, git status 挂起",
        flow_id="flow_TRAE_EXAMPLE_CODE_20260904_001"
    )
    print(f"[深度推理 route={r1['route']}] {r1.get('response', '')[:200]}")

    # 方案设计
    r2 = design_plan(
        requirement="为 Trae 实现本地代码离线分析",
        constraints="零token, 优先本地 Ollama, 纯离线运行",
        flow_id="flow_TRAE_EXAMPLE_CODE_20260904_001"
    )
    print(f"[方案设计 route={r2['route']}] {r2.get('response', '')[:200]}")

    # Bug定位
    r3 = locate_bug(
        error_desc="sqlite3.OperationalError: database is locked",
        code="conn = sqlite3.connect(db, timeout=5)",
        flow_id="flow_TRAE_EXAMPLE_CODE_20260904_001"
    )
    print(f"[Bug定位 route={r3['route']}] {r3.get('response', '')[:200]}")

    # 架构思考
    r4 = architecture_think(
        requirement="设计 Trae 本地AI双轨路由(本地优先+云兜底)",
        flow_id="flow_TRAE_EXAMPLE_CODE_20260904_001"
    )
    print(f"[架构思考 route={r4['route']}] {r4.get('response', '')[:200]}")
    return r1


def example_python_analyze():
    """示例3: 离线代码分析器 — 语法/编译/质量/AI建议"""
    from code_analyzer_offline import analyze_file, compile_check_file, health

    print(f"[分析器能力] {health()}")

    # 选一个真实文件分析 (这里用自身做示例)
    sample = os.path.join(_AI_ENGINES_DIR, "local_ai_unified_gateway.py")

    # 完整分析 (语法+编译+质量+AI建议)
    r1 = analyze_file(sample, flow_id="flow_TRAE_EXAMPLE_CODE_20260904_001")
    print(f"[分析] syntax_ok={r1['syntax']['syntax_ok']}, "
          f"issues={r1['quality']['issue_count']}, route={r1['route']}")
    if r1.get("ai_suggestion"):
        print(f"[AI建议] {r1['ai_suggestion'][:200]}")

    # 纯编译检查
    r2 = compile_check_file(sample, flow_id="flow_TRAE_EXAMPLE_CODE_20260904_001")
    print(f"[编译] compile_ok={r2['compile']['compile_ok']}, route={r2['route']}")
    return r1


def example_python_gateway_dispatch():
    """示例4: 通过统一网关分发各类场景"""
    from local_ai_unified_gateway import think, review, classify

    # think — 思考助理入口
    r_think = think("评估本地7B模型能否胜任代码审查",
                    context="qwen2.5:7b, 8GB内存",
                    flow_id="flow_TRAE_EXAMPLE_CODE_20260904_001")
    print(f"[gateway.think] {r_think.get('route')} → {r_think.get('response', '')[:150]}")

    # review — 代码审查
    r_review = review("def foo(x):\n    return x",
                      flow_id="flow_TRAE_EXAMPLE_CODE_20260904_001")
    print(f"[gateway.review] {r_review.get('route')} → {r_review.get('response', '')[:150]}")

    # classify — 代码分类
    r_classify = classify("@app.route('/api/health')\ndef health(): pass",
                          categories=["api_route", "function_def", "sql"],
                          flow_id="flow_TRAE_EXAMPLE_CODE_20260904_001")
    print(f"[gateway.classify] {r_classify.get('route')} → {r_classify.get('response', '')[:150]}")
    return r_think


# ============================================================
# 2. Shell CLI 调用示例
# ============================================================
#
# 网关已内置 argparse CLI, 直接在终端调用:
#
#   # 健康检查
#   python3 flask-app/ai_engines/local_ai_unified_gateway.py health
#
#   # 对话 (本地Ollama优先, 零token)
#   python3 flask-app/ai_engines/local_ai_unified_gateway.py chat "解释Python装饰器" \
#       --system "你是MTSCOS本地AI助手"
#
#   # 思考助理
#   python3 flask-app/ai_engines/local_ai_unified_gateway.py think "如何优化这个函数"
#
#   # 代码分析 (语法/编译/质量/AI建议)
#   python3 flask-app/ai_engines/local_ai_unified_gateway.py analyze \
#       flask-app/ai_engines/local_ai_unified_gateway.py
#
#   # 离线编译检查
#   python3 flask-app/ai_engines/local_ai_unified_gateway.py compile \
#       flask-app/ai_engines/local_ai_unified_gateway.py
#
#   # 代码审查
#   python3 flask-app/ai_engines/local_ai_unified_gateway.py review "def foo(x): return x"
#
#   # 代码分类
#   python3 flask-app/ai_engines/local_ai_unified_gateway.py classify \
#       "@app.route('/api/health')"
#
#   # 带 flow_id (关联12步骤工作流)
#   python3 flask-app/ai_engines/local_ai_unified_gateway.py chat "分析这段代码" \
#       --flow-id flow_TRAE_EXAMPLE_CODE_20260904_001
#
# Trae Shell 工具调用示例 (在 Trae 的 Shell 工具里执行):
#   cwd = "/Users/wuchenghao/Library/CloudStorage/OneDrive-个人/文档/MTSCOS_AI_Project"
#   command = "python3 flask-app/ai_engines/local_ai_unified_gateway.py health"
# ============================================================


# ============================================================
# 3. MCP 工具集成示例
# ============================================================
# 将本地AI组件封装为 MCP 工具, Trae 通过 run_mcp 调用。
# 需在 Trae MCP 配置中注册本服务 (mcp_file_system_servers)。

# ---- 3.1 MCP 工具函数实现 (供 MCP server 暴露) ----

def mcp_tool_local_chat(prompt: str, system: str = "", flow_id: str = "") -> dict:
    """MCP工具: 本地AI对话 (本地Ollama优先, 零token)
    参数:
      prompt  : 用户问题
      system  : 系统提示(可选)
      flow_id : 12步骤工作流ID(可选)
    返回: {success, response, route, model, tokens_saved}
    """
    from local_ai_unified_gateway import chat
    result = chat(prompt, system, flow_id or None)
    return {
        "success": result["success"],
        "response": result.get("response", ""),
        "route": result.get("route", "none"),
        "model": result.get("model", ""),
        "tokens_saved": result.get("tokens_saved", 0),
    }


def mcp_tool_code_analyze(file_path: str, flow_id: str = "") -> dict:
    """MCP工具: 离线代码分析 (语法/编译/质量/AI建议)
    参数:
      file_path : 待分析的 Python 文件绝对路径
      flow_id   : 12步骤工作流ID(可选)
    返回: {success, syntax, quality, ai_suggestion, route}
    """
    from code_analyzer_offline import analyze_file
    result = analyze_file(file_path, flow_id or None)
    return {
        "success": result["success"],
        "syntax_ok": result.get("syntax", {}).get("syntax_ok"),
        "issue_count": result.get("quality", {}).get("issue_count", 0),
        "ai_suggestion": result.get("ai_suggestion", ""),
        "route": result.get("route", "offline_static"),
    }


def mcp_tool_deep_think(question: str, context: str = "", flow_id: str = "") -> dict:
    """MCP工具: 深度思考助理 (推理/决策/方案/Bug定位)
    参数:
      question : 思考的问题
      context  : 上下文(可选)
      flow_id  : 12步骤工作流ID(可选)
    返回: {success, response, route}
    """
    from thinking_assistant import deep_think
    result = deep_think(question, context, flow_id or None)
    return {
        "success": result["success"],
        "response": result.get("response", ""),
        "route": result.get("route", "none"),
    }


def mcp_tool_locate_bug(error_desc: str, code: str = "", flow_id: str = "") -> dict:
    """MCP工具: Bug根因定位
    参数:
      error_desc : 错误描述/堆栈
      code       : 相关代码片段(可选)
      flow_id    : 12步骤工作流ID(可选)
    返回: {success, response, route}
    """
    from thinking_assistant import locate_bug
    result = locate_bug(error_desc, code, flow_id or None)
    return {
        "success": result["success"],
        "response": result.get("response", ""),
        "route": result.get("route", "none"),
    }


def mcp_tool_ai_health() -> dict:
    """MCP工具: 本地AI网关健康检查"""
    from local_ai_unified_gateway import health
    return health()


# ---- 3.2 Trae 通过 run_mcp 调用示例 (伪代码, 需 MCP server 注册) ----
#
#   # Trae 调用本地AI对话
#   run_mcp(server_name="local_ai", tool_name="local_chat",
#           args={"prompt": "解释Python装饰器", "flow_id": "flow_xxx"})
#
#   # Trae 调用代码分析
#   run_mcp(server_name="local_ai", tool_name="code_analyze",
#           args={"file_path": "/abs/path/to/file.py"})
#
#   # Trae 调用深度思考
#   run_mcp(server_name="local_ai", tool_name="deep_think",
#           args={"question": "如何优化函数", "context": "..."})
#
#   # Trae 调用Bug定位
#   run_mcp(server_name="local_ai", tool_name="locate_bug",
#           args={"error_desc": "database is locked", "code": "..."})
# ============================================================


# ============================================================
# 4. Skill 集成示例
# ============================================================
# 将本地AI组件封装为 Trae Skill, 通过 Skill 工具调用。
# Skill 名称: local-ai-toolkit
# 触发条件: 用户要求"本地分析代码/本地思考/零token推理/Bug定位"时触发

def skill_local_ai_toolkit(action: str, **kwargs) -> dict:
    """Trae Skill: 本地AI工具包
    action 取值:
      - chat       : 本地对话
      - think      : 深度思考
      - analyze     : 代码分析
      - locate_bug : Bug定位
      - health     : 健康检查
    """
    flow_id = kwargs.get("flow_id", "flow_TRAE_EXAMPLE_CODE_20260904_001")

    if action == "chat":
        from local_ai_unified_gateway import chat
        return chat(kwargs["prompt"], kwargs.get("system", ""), flow_id)

    if action == "think":
        from thinking_assistant import deep_think
        return deep_think(kwargs["question"], kwargs.get("context", ""), flow_id)

    if action == "analyze":
        from code_analyzer_offline import analyze_file
        return analyze_file(kwargs["file_path"], flow_id)

    if action == "locate_bug":
        from thinking_assistant import locate_bug
        return locate_bug(kwargs["error_desc"], kwargs.get("code", ""), flow_id)

    if action == "health":
        from local_ai_unified_gateway import health
        return health()

    return {"success": False, "error": f"未知 action: {action}"}


# ---- 4.1 Trae 调用 Skill 示例 ----
#
#   # Trae 通过 Skill 工具调用本地AI对话
#   Skill(name="local-ai-toolkit",
#         args="chat|prompt=解释Python装饰器|system=简洁回答")
#
#   # Trae 调用代码分析
#   Skill(name="local-ai-toolkit",
#         args="analyze|file_path=/abs/path/to/file.py")
#
#   # Trae 调用深度思考
#   Skill(name="local-ai-toolkit",
#         args="think|question=如何优化函数|context=...")
#
#   # Trae 调用Bug定位
#   Skill(name="local-ai-toolkit",
#         args="locate_bug|error_desc=database is locked|code=conn=...")
# ============================================================


# ============================================================
# 主入口: 运行所有 Python 示例
# ============================================================
if __name__ == "__main__":
    print("=" * 60)
    print("Trae 调用本地AI组件示例 (flow_TRAE_EXAMPLE_CODE_20260904_001)")
    print("=" * 60)

    print("\n--- 示例1: Python 对话 ---")
    example_python_chat()

    print("\n--- 示例2: Python 思考助理 ---")
    example_python_think()

    print("\n--- 示例3: Python 代码分析 ---")
    example_python_analyze()

    print("\n--- 示例4: Python 网关分发 ---")
    example_python_gateway_dispatch()

    print("\n--- 示例5: MCP 工具调用 (本地对话) ---")
    r = mcp_tool_local_chat("解释 SQLite 锁的成因",
                            system="你是MTSCOS本地AI助手",
                            flow_id="flow_TRAE_EXAMPLE_CODE_20260904_001")
    print(f"[MCP local_chat] route={r['route']}, saved={r['tokens_saved']}")
    print(f"  response: {r['response'][:200]}")

    print("\n--- 示例6: MCP 工具调用 (代码分析) ---")
    r = mcp_tool_code_analyze(
        os.path.join(_AI_ENGINES_DIR, "local_ai_unified_gateway.py"),
        flow_id="flow_TRAE_EXAMPLE_CODE_20260904_001"
    )
    print(f"[MCP code_analyze] syntax_ok={r['syntax_ok']}, "
          f"issues={r['issue_count']}, route={r['route']}")

    print("\n--- 示例7: MCP 工具调用 (深度思考) ---")
    r = mcp_tool_deep_think(
        "如何让 Trae 优先走本地推理?",
        context="本地Ollama qwen2.5:7b可用, 8GB内存",
        flow_id="flow_TRAE_EXAMPLE_CODE_20260904_001"
    )
    print(f"[MCP deep_think] route={r['route']}")
    print(f"  response: {r['response'][:200]}")

    print("\n--- 示例8: MCP 工具调用 (Bug定位) ---")
    r = mcp_tool_locate_bug(
        "sqlite3.OperationalError: database is locked",
        code="conn = sqlite3.connect(db, timeout=5)\ncur = conn.execute(...)",
        flow_id="flow_TRAE_EXAMPLE_CODE_20260904_001"
    )
    print(f"[MCP locate_bug] route={r['route']}")
    print(f"  response: {r['response'][:200]}")

    print("\n--- 示例9: Skill 调用 ---")
    r = skill_local_ai_toolkit("health")
    print(f"[Skill health] {r}")

    print("\n" + "=" * 60)
    print("所有示例执行完毕")
    print("Shell CLI / MCP / Skill 调用方式见文件内注释")
    print("=" * 60)
