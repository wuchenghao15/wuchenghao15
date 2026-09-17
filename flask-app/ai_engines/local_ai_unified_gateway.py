# -*- coding: utf-8 -*-
"""
本地AI统一网关 (Local AI Unified Gateway)
==========================================
Trae 优先离线编译代码、主力推理、思考助理的统一入口

路由优先级:
  1. 本地 Ollama (qwen2.5:7b) — 零token, 首选
  2. 火山引擎方舟ARK API — 云端兜底
  3. 本地模板匹配 — 最终兜底

支持场景:
  - chat      : 对话/思考助理
  - analyze   : 代码分析(语法/编译错误/优化建议)
  - think     : 思考助理(推理/决策/方案)
  - compile   : 离线编译辅助(代码检查/错误定位)
  - review    : 代码审查
  - classify  : 代码分类

CLI 用法:
  python3 local_ai_unified_gateway.py chat "你好"
  python3 local_ai_unified_gateway.py analyze path/to/file.py
  python3 local_ai_unified_gateway.py think "如何优化这个函数"
  python3 local_ai_unified_gateway.py compile path/to/file.py
  python3 local_ai_unified_gateway.py act "拉取代码后安装依赖并跑测试" [--dry-run]
  python3 local_ai_unified_gateway.py health

对接:
  - ai_ollama_engine.py (本地Ollama推理)
  - ai_volcengine_engine.py (火山引擎兜底)
  - ai_dual_route_engine.py (双轨路由)
  - code_analyzer_offline.py (离线代码分析)
  - thinking_assistant.py (思考助理)
"""
from __future__ import annotations

import json
import os
import re
import sys
import time
from typing import Any, Dict, Optional

# 确保 ai_engines 目录在 sys.path
_AI_ENGINES_DIR = os.path.dirname(os.path.abspath(__file__))
if _AI_ENGINES_DIR not in sys.path:
    sys.path.insert(0, _AI_ENGINES_DIR)

# 路由优先级配置 — Ollama 云端优先, 本地原生兜底
_ROUTE_PRIORITY = {
    "cloud_ollama": 1,       # 首选: Ollama Cloud (经 Cloud Proxy 11434, gpt-oss:20b)
    "native_ollama": 2,     # 兜底: 本地原生 Ollama (11435, qwen2.5:7b, 真正零云端token)
    "cloud_volcengine": 3,  # 最终兜底: 火山引擎方舟ARK(默认关闭, 见 _cloud_fallback_enabled)
}

# 云端瞬时失败重试: 吸收模型冷启动/换模型/网络抖动, 避免单次失败泄漏到本地原生
_LOCAL_MAX_ATTEMPTS = 3          # 云端最多尝试次数(含首次)
_LOCAL_RETRY_BACKOFF = (1.5, 4.0)  # 第1/2次失败后的退避秒数

# 路由决策计数(进程内, 供 health() 观测路由分布)
_ROUTE_STATS = {"cloud_ollama": 0, "cloud_retry": 0, "native": 0, "volcengine": 0, "blocked_cloud": 0, "none": 0}

# 本地原生 Ollama (11435, 真正本地推理, 零云端 token) — 作为 Ollama Cloud 不可用时的兜底
_NATIVE_OLLAMA_HOST = os.environ.get("OLLAMA_NATIVE_HOST", "http://localhost:11435")
_NATIVE_MODEL = os.environ.get("OLLAMA_NATIVE_MODEL", "qwen2.5:7b")


def _cloud_fallback_enabled() -> bool:
    """云端兜底开关: 默认关闭(极致本地优先, 零云端token)。

    仅当显式设置环境变量 MTSCOS_AI_ALLOW_CLOUD=1/true/yes/on 时才允许云端应急,
    从源头杜绝"本地打个盹就烧云端token"。
    """
    return os.environ.get("MTSCOS_AI_ALLOW_CLOUD", "0").strip().lower() in (
        "1", "true", "yes", "on")


def _get_ollama():
    """获取 Ollama 引擎 (任何导入/语法异常都降级为None, 不让网关崩溃)"""
    try:
        from ai_ollama_engine import chat as ollama_chat, classify as ollama_classify, \
            review as ollama_review, bug_analyze as ollama_bug, is_available, health
        return {"chat": ollama_chat, "classify": ollama_classify,
                "review": ollama_review, "bug_analyze": ollama_bug,
                "is_available": is_available, "health": health}
    except Exception as e:
        if os.environ.get("MTSCOS_AI_DEBUG"):
            sys.stderr.write(f"[gateway] ollama引擎加载失败: {e}\n")
        return None


def _get_volcengine():
    """获取火山引擎引擎 (异常降级)"""
    try:
        from ai_volcengine_engine import chat as ark_chat, is_available
        return {"chat": ark_chat, "is_available": is_available}
    except Exception:
        return None


def _native_ollama_available() -> bool:
    """本地原生 Ollama (11435) 是否在线且模型可用"""
    try:
        import urllib.request, json as _json
        with urllib.request.urlopen(_NATIVE_OLLAMA_HOST + "/api/tags", timeout=3) as r:
            data = _json.loads(r.read().decode("utf-8"))
            models = [m.get("name", "") for m in data.get("models", [])]
            return bool(models)
    except Exception:
        return False


def _native_ollama_chat(prompt: str, system: str = "", flow_id: Optional[str] = None) -> Dict[str, Any]:
    """本地原生 Ollama 推理 (11435, qwen2.5:7b, 真正零云端 token)"""
    import urllib.request, json as _json
    payload = {"model": _NATIVE_MODEL, "messages": [], "stream": False,
               "options": {"temperature": 0.7, "top_p": 0.9, "num_predict": 2048}}
    if system:
        payload["messages"].append({"role": "system", "content": system})
    payload["messages"].append({"role": "user", "content": prompt})
    start = time.time()
    try:
        req = urllib.request.Request(_NATIVE_OLLAMA_HOST + "/api/chat",
            data=_json.dumps(payload).encode("utf-8"),
            headers={"Content-Type": "application/json"}, method="POST")
        with urllib.request.urlopen(req, timeout=180) as resp:
            data = _json.loads(resp.read().decode("utf-8"))
        content = data.get("message", {}).get("content", "")
        pt = data.get("prompt_eval_count", 0)
        ct = data.get("eval_count", 0)
        return {"success": True, "response": content, "model": _NATIVE_MODEL,
                "route": "native_ollama", "gateway": "local_ai_unified_gateway",
                "duration_ms": int((time.time() - start) * 1000),
                "tokens_saved": pt + ct, "prompt_tokens": pt, "completion_tokens": ct}
    except Exception as e:
        return {"success": False, "response": "", "model": _NATIVE_MODEL,
                "route": "native_ollama", "error": f"本地原生推理失败: {e}",
                "duration_ms": int((time.time() - start) * 1000)}


def _route_chat(prompt: str, system: str = "", flow_id: Optional[str] = None,
                use_coder: bool = False) -> Dict[str, Any]:
    """统一路由聊天 — Ollama 云端优先, 本地原生兜底:

    1. Ollama Cloud (11434, gpt-oss:20b) 优先, 单次失败先重试(吸收抖动);
    2. 云端不可用 → 降级本地原生 Ollama (11435, qwen2.5:7b, 真正零云端 token);
    3. 本地原生也不可用 → 火山引擎最终兜底(门控, 默认关)。
    """
    ollama = _get_ollama()  # 连 11434 Cloud Proxy
    cloud_online = bool(ollama and ollama["is_available"]())
    cloud_error = "Ollama Cloud Proxy 未运行"

    # 1) Ollama Cloud 优先 + 瞬时失败重试
    if cloud_online:
        for attempt in range(1, _LOCAL_MAX_ATTEMPTS + 1):
            result = ollama["chat"](prompt, system, flow_id, prefer_7b=True, use_coder=use_coder)
            if result.get("success"):
                result["route"] = "cloud_ollama"
                result["gateway"] = "local_ai_unified_gateway"
                result["cloud_attempts"] = attempt
                _ROUTE_STATS["cloud_ollama"] += 1
                return result
            cloud_error = result.get("error", "云端推理失败") or "云端推理失败"
            if attempt < _LOCAL_MAX_ATTEMPTS:
                _ROUTE_STATS["cloud_retry"] += 1
                time.sleep(_LOCAL_RETRY_BACKOFF[min(attempt - 1, len(_LOCAL_RETRY_BACKOFF) - 1)])

    # 2) 本地原生 Ollama 兜底 (11435, qwen2.5:7b, 零云端 token)
    if _native_ollama_available():
        result = _native_ollama_chat(prompt, system, flow_id)
        if result.get("success"):
            result["native_reason"] = f"Cloud不可用({cloud_error[:40]}); 降级本地原生"
            _ROUTE_STATS["native"] += 1
            return result
        native_error = result.get("error", "本地原生推理失败")
    else:
        native_error = "本地原生 Ollama(11435)未运行"

    # 3) 火山引擎最终兜底(门控): 仅显式开启时才允许
    if _cloud_fallback_enabled():
        ark = _get_volcengine()
        if ark and ark["is_available"]():
            result = ark["chat"](prompt, system, flow_id)
            if result["success"]:
                result["route"] = "cloud_volcengine"
                result["gateway"] = "local_ai_unified_gateway"
                result["cloud_reason"] = f"Cloud+本地原生均不可用; 火山引擎兜底"
                _ROUTE_STATS["volcengine"] += 1
                return result
    else:
        _ROUTE_STATS["blocked_cloud"] += 1
        return {
            "success": False, "response": "", "model": "",
            "route": "all_unavailable", "gateway": "local_ai_unified_gateway",
            "duration_ms": 0, "tokens_saved": 0,
            "error": (f"Ollama Cloud({cloud_error[:60]}) 与本地原生({native_error[:40]}) 均不可用。"
                      f"已按策略禁用火山引擎兜底、不消耗云端token。"
                      f"紧急可设 MTSCOS_AI_ALLOW_CLOUD=1 启用火山引擎应急。"),
            "cloud_online": cloud_online, "cloud_blocked": True,
        }

    # 4) 火山引擎已开启但也不可用
    _ROUTE_STATS["none"] += 1
    return {
        "success": False, "response": "所有AI引擎不可用", "model": "",
        "route": "none", "gateway": "local_ai_unified_gateway",
        "duration_ms": 0, "tokens_saved": 0,
        "error": f"Cloud({cloud_error[:50]}); 本地原生({native_error[:40]}); 火山引擎不可用",
    }


def chat(prompt: str, system: str = "", flow_id: Optional[str] = None) -> Dict[str, Any]:
    """对话/思考助理入口 (Trae AI对话优先走本地)"""
    return _route_chat(prompt, system, flow_id)


# ===== 终端实时反馈 (仅CLI模式, 消除"假卡死") =====
_CLI = False
_SPIN_FRAMES = "⠋⠙⠹⠸⠼⠴⠦⠧⠇⠏"
_NODES = None          # 当前活跃节点清单跟踪器 (主节点渲染 / 嵌套时从属上抛)
_NODE_EST_CACHE = {}   # 节点组滚动ETA缓存 (已完成实际耗时 → 同组待执行节点预估)


def _prog_on():
    """启用CLI进度输出 (main()调用; MCP/程序导入时默认关闭)"""
    global _CLI
    _CLI = True


def _stage(msg: str):
    """打印一个阶段行 (换行, 带时间戳); 有节点清单时并入清单日志区"""
    if not _CLI:
        return
    if _NODES is not None:
        _NODES.log(f"▸ {msg}")
        return
    import datetime
    ts = datetime.datetime.now().strftime("%H:%M:%S")
    sys.stderr.write(f"  \033[36m▸\033[0m \033[2m{ts}\033[0m  {msg}\n")
    sys.stderr.flush()


def _banner(title: str, model: str = "", route: str = ""):
    if not _CLI:
        return
    if _NODES is not None:
        parts = [p for p in (title, model, route) if p]
        _NODES.log("🤖 " + " · ".join(parts))
        return
    sys.stderr.write("\n")
    sys.stderr.write("\033[1;35m┌──────────────────────────────────────────────┐\033[0m\n")
    sys.stderr.write(f"\033[1;35m│\033[0m  🤖  {title:<40}\033[1;35m│\033[0m\n")
    if model:
        sys.stderr.write(f"\033[1;35m│\033[0m  \033[2m模型: {model[:38]:<38}\033[0m\033[1;35m│\033[0m\n")
    if route:
        sys.stderr.write(f"\033[1;35m│\033[0m  \033[2m路由: {route[:38]:<38}\033[0m\033[1;35m│\033[0m\n")
    sys.stderr.write("\033[1;35m└──────────────────────────────────────────────┘\033[0m\n")
    sys.stderr.flush()


class _Spin:
    """长操作旋转动画 (后台线程, 显示已用秒数)"""
    def __init__(self, label: str):
        self.label = label
        self._t = None
        self._stop = False
        self.t0 = 0.0

    def __enter__(self):
        if not _CLI:
            return self
        import threading, time
        self.t0 = time.time()
        if _NODES is not None:
            # 节点清单模式: 抑制独立spinner线程(避免与多行重绘互相覆盖), 完成时仅记日志
            return self

        def run():
            i = 0
            while not self._stop:
                el = time.time() - self.t0
                frame = _SPIN_FRAMES[i % len(_SPIN_FRAMES)]
                sys.stderr.write(f"\r  \033[33m{frame}\033[0m {self.label} \033[2m({el:.0f}s)\033[0m   ")
                sys.stderr.flush()
                time.sleep(0.12)
                i += 1
        self._t = threading.Thread(target=run, daemon=True)
        self._t.start()
        return self

    def __exit__(self, *a):
        if not _CLI:
            return
        import time
        el = time.time() - self.t0
        if _NODES is not None:
            # 节点清单模式: 动画由节点行负责, 这里只记一条完成日志
            if self.label:
                _NODES.log(f"✓ {self.label} · {el:.1f}s")
            return
        self._stop = True
        time.sleep(0.15)
        sys.stderr.write(f"\r  \033[32m✓\033[0m {self.label} \033[2m({el:.1f}s)\033[0m" + " " * 20 + "\n")
        sys.stderr.flush()


def _fmt_eta(sec: float) -> str:
    """秒数 → 紧凑时长 (45s / 1m32s / 1h05m)"""
    sec = max(int(round(sec)), 0)
    if sec >= 3600:
        return f"{sec // 3600}h{sec % 3600 // 60:02d}m"
    if sec >= 60:
        return f"{sec // 60}m{sec % 60:02d}s"
    return f"{sec}s"


class _Nodes:
    """节点清单跟踪器 (CLI多行实时渲染, 仅stderr):

    📊 [████████░░░░░░░░░░░░] 3/8 · 待完成 5 · 预计剩余 ~1m32s · 预计完成 14:32:18
      ✓ 已完成节点 · 3.2s              (已完成检查: 绿色对勾+实际耗时)
      ⠙ 执行中节点 · 已用12s · 剩~28s   (节点执行倒计时)
      ○ 待执行节点 · 预计~40s          (待完成清单)
      ✗ 失败节点 · 失败 原因           / ⤳ 跳过节点 · 跳过 原因

    - 滚动ETA: 已完成节点实际耗时回写同组待执行节点的预估
    - 预计完成时刻 = 当前时间 + 剩余节点预估之和 (头部实时刷新)
    - 嵌套场景 (act→execute_task) 自动降级从属模式: 不重复渲染, 日志上抛父级
    - 非TTY(管道)模式: 不做动态刷新, close() 时一次性打印最终清单
    """
    BAR_W = 22

    def __init__(self, title: str, items=None, default_est: float = 30.0):
        import threading
        self.title = title
        self.default_est = default_est
        self.nodes = []      # {label, group, est, state, t0, dur, note}
        self.logs = []       # 清单下方附加日志 (stage/banner/命令输出)
        self._t = None
        self._stop = False
        self._last = 0
        self._lock = threading.Lock()
        self._slave = _NODES is not None
        for it in (items or []):
            self.add(*(it if isinstance(it, tuple) else (it,)))

    # -- 清单构建 --
    def add(self, label: str, est: float = None, group: str = "") -> int:
        """追加节点, 返回节点下标 (est=预估秒, group=同组共享滚动ETA)"""
        if est is None:
            est = _NODE_EST_CACHE.get(group, self.default_est)
        self.nodes.append({"label": label, "group": group, "est": float(est),
                           "state": "pending", "t0": 0.0, "dur": 0.0, "note": ""})
        return len(self.nodes) - 1

    # -- 状态推进 --
    def run(self, i: int):
        with self._lock:
            n = self.nodes[i]
            n["state"] = "run"
            n["t0"] = time.time()

    def ok(self, i: int, note: str = ""):
        with self._lock:
            n = self.nodes[i]
            n["state"] = "done"
            n["dur"] = max(time.time() - n["t0"], 0.05) if n["t0"] else 0.0
            if note:
                n["note"] = note
            g = n["group"]
            if g and n["dur"] > 0.5:
                _NODE_EST_CACHE[g] = round(n["dur"], 1)  # 滚动ETA学习
                for m in self.nodes:
                    if m["state"] == "pending" and m["group"] == g:
                        m["est"] = n["dur"]

    def err(self, i: int, note: str = ""):
        with self._lock:
            n = self.nodes[i]
            n["state"] = "fail"
            n["dur"] = time.time() - n["t0"] if n["t0"] else 0.0
            if note:
                n["note"] = note

    def skip(self, i: int, note: str = ""):
        with self._lock:
            self.nodes[i]["state"] = "skip"
            if note:
                self.nodes[i]["note"] = note

    def skip_pending(self, note: str = ""):
        """把所有未开始节点标记为跳过 (前序失败/dry-run后收尾)"""
        with self._lock:
            for m in self.nodes:
                if m["state"] == "pending":
                    m["state"] = "skip"
                    if note:
                        m["note"] = note

    def log(self, msg: str):
        """清单下方附加日志; 从属模式上抛父级"""
        if self._slave and _NODES is not self:
            _NODES.log(msg)
            return
        with self._lock:
            self.logs.append(msg)

    # -- 渲染 --
    def _render(self) -> list:
        import datetime
        now = time.time()
        with self._lock:
            total = len(self.nodes)
            done = sum(1 for n in self.nodes if n["state"] in ("done", "skip"))
            has_fail = any(n["state"] == "fail" for n in self.nodes)
            remain = 0.0
            for n in self.nodes:
                if n["state"] == "run":
                    remain += max(n["est"] - (now - n["t0"]), 2.0)
                elif n["state"] == "pending":
                    remain += n["est"]
            filled = int(round(self.BAR_W * done / total)) if total else 0
            bar = "█" * filled + "░" * (self.BAR_W - filled)
            head = (f"\033[1;35m📊\033[0m [\033[35m{bar}\033[0m] "
                    f"\033[1m{done}/{total}\033[0m · 待完成 \033[33m{total - done}\033[0m")
            if remain > 0:
                eta = (datetime.datetime.now()
                       + datetime.timedelta(seconds=remain)).strftime("%H:%M:%S")
                head += (f" · 预计剩余 \033[36m~{_fmt_eta(remain)}\033[0m"
                         f" · 预计完成 \033[36m{eta}\033[0m")
            else:
                head += (" · \033[32m清单已清空\033[0m" if not has_fail
                         else " · \033[31m存在失败节点\033[0m")
            lines = [head]
            frame = _SPIN_FRAMES[int(now * 8) % len(_SPIN_FRAMES)]
            for n in self.nodes:
                st = n["state"]
                if st == "done":
                    extra = f" \033[2m{n['note']}\033[0m" if n["note"] else ""
                    lines.append(f"  \033[32m✓\033[0m {n['label']}"
                                 f" \033[2m· {_fmt_eta(n['dur'])}{extra}\033[0m")
                elif st == "fail":
                    extra = f" \033[2m{n['note'][:70]}\033[0m" if n["note"] else ""
                    lines.append(f"  \033[31m✗\033[0m {n['label']}"
                                 f" \033[31m· 失败\033[0m{extra}")
                elif st == "skip":
                    lines.append(f"  \033[2m⤳ {n['label']} · 跳过 {n['note']}\033[0m")
                elif st == "run":
                    el = max(now - n["t0"], 0.0)
                    left = n["est"] - el
                    cd = f"剩~{_fmt_eta(left)}" if left > 0 else "即将完成"
                    lines.append(f"  \033[33m{frame}\033[0m \033[1m{n['label']}\033[0m"
                                 f" \033[2m· 已用{_fmt_eta(el)} · {cd}\033[0m")
                else:
                    lines.append(f"  \033[2m○ {n['label']} · 预计~{_fmt_eta(n['est'])}\033[0m")
            for m in self.logs[-10:]:
                lines.append(f"    \033[2m{m}\033[0m")
            return lines

    def _paint(self):
        lines = self._render()
        buf = []
        if self._last:
            buf.append(f"\x1b[{self._last}A\x1b[J")  # 光标上移并清空旧块
        buf.append("\n".join(lines))
        sys.stderr.write("".join(buf) + "\n")
        sys.stderr.flush()
        self._last = len(lines)

    def _loop(self):
        while not self._stop:
            self._paint()
            time.sleep(0.15)

    def start(self):
        """开始实时渲染 (从属/非TTY模式不启动)"""
        if not _CLI or self._slave or not self.nodes:
            return
        if not sys.stderr.isatty():
            return  # 管道输出: 不动态刷新, close()时打印最终清单
        global _NODES
        _NODES = self
        self._started = True
        sys.stderr.write(f"\n\033[1;35m📋 节点清单 · {self.title}\033[0m\n")
        sys.stderr.flush()
        import threading
        self._t = threading.Thread(target=self._loop, daemon=True)
        self._t.start()

    def close(self):
        """停止渲染并打印最终静态清单 (幂等)"""
        if self._slave or not _CLI or not self.nodes:
            return
        self._stop = True
        if self._t:
            self._t.join(timeout=0.5)
        lines = self._render()
        if not getattr(self, "_started", False):
            # 非TTY模式: 动态标题从未打印, 最终块自带标题保证自包含
            lines = [f"\033[1;35m📋 节点清单 · {self.title}\033[0m"] + lines
        for line in lines:
            sys.stderr.write(line + "\n")
        sys.stderr.write("\n")
        sys.stderr.flush()
        global _NODES
        if _NODES is self:
            _NODES = None

    def __enter__(self):
        self.start()
        return self

    def __exit__(self, *a):
        self.close()


def _ollama_stream(prompt: str, system: str = "", use_coder: bool = False) -> Optional[Dict[str, Any]]:
    """直连Ollama流式输出 (逐token打字机效果到stdout), 失败返回None回退"""
    import urllib.request
    import time
    model = "qwen2.5-coder:14b" if use_coder else "qwen2.5:7b"
    payload = {
        "model": model,
        "messages": [{"role": "system", "content": system or "你是MTSCOS本地AI助手。"},
                     {"role": "user", "content": prompt}],
        "stream": True,
    }
    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(_NATIVE_OLLAMA_HOST + "/api/chat", data=data,
                                 headers={"Content-Type": "application/json"})
    t0 = time.time()
    chunks = 0
    full = []
    try:
        with urllib.request.urlopen(req, timeout=600) as resp:
            for raw in resp:
                line = raw.decode("utf-8", "replace").strip()
                if not line:
                    continue
                try:
                    obj = json.loads(line)
                except json.JSONDecodeError:
                    continue
                tok = obj.get("message", {}).get("content", "")
                if tok:
                    full.append(tok)
                    chunks += 1
                    if _CLI:
                        sys.stdout.write(tok)
                        sys.stdout.flush()
                if obj.get("done"):
                    break
        if _CLI:
            sys.stdout.write("\n")
            sys.stdout.flush()
        text = "".join(full).strip()
        if not text:
            return None
        return {"success": True, "response": text, "model": model,
                "route": "local_ollama", "gateway": "local_ai_unified_gateway",
                "duration_ms": int((time.time() - t0) * 1000), "tokens_saved": chunks,
                "streamed": True}
    except Exception:
        return None


# ===== 编码铁律: 只输出代码, 禁止任何执行指令 =====
# 问题背景: 本地7B模型常把"执行命令"当答案(如 pip install / python xxx.py / git ...),
# 而非纯代码修改。此段对所有编码类请求强制追加, 即使调用方传了自定义 system 也不例外。
_CODE_RULES = (
    "\n\n【铁律 · 必须严格遵守】"
    "你只能输出代码文本, 没有任何执行能力:"
    "①禁止输出任何 shell/终端/命令行指令, 包括但不限于 pip/pip3 install、python/python3、"
    "bash/sh/zsh、git、npm/yarn/pnpm、brew、curl/wget、docker 等命令;"
    "②禁止要求、建议或描述让用户去'执行/运行/安装/重启'任何命令、脚本或步骤;"
    "③禁止输出操作步骤清单、命令清单或'请运行以下命令'之类内容, 所有需求一律通过给出"
    "修改后的代码来解决;"
    "④缺少依赖或需要环境配置时, 只能在代码注释中说明依赖名称与用途, 不得写出安装命令;"
    "⑤直接输出完整代码(用 ```代码块 包裹), 代码块外最多一两句简短说明; "
    "修改既有代码时保持未涉及部分原样不动, 不要输出 diff 标记(+/-行)。"
)

# 项目硬规则(对齐 .trae/rules 九篇规范 + 用户权限/设计规范/开发规则): 生成/修改代码时必须遵守, 无例外
_PROJECT_RULES = (
    "\n\n【MTSCOS 项目规范 · 必须严格遵守, 没有例外】"
    "①权限铁律: 所有 Flask 路由/API 必须有鉴权——页面/接口挂 @system_container 装饰器"
    "(require_auth='login'/'admin'/'super_admin', allowed_roles 限定角色) 或在函数体内"
    "调用 _check_login(user)/_check_admin(user) 助手; 禁止任何无鉴权的裸路由。"
    "②越权防护(IDOR): 凡是带 user_id 的端点(路径参数或请求体), 必须校验数据归属——"
    "学生/普通用户只能访问本人数据, 教师/管理员/超级管理员(wuchenghao15)可跨学生; "
    "写操作里的人工调整类型(如 manual_adjust)仅限教职; 越权返回 403 并写审计日志。"
    "③数据真源: SQLite 数据库是唯一权威数据源, 所有展示/统计必须查真实库表, "
    "禁止编造/硬编码模拟数据(假数字、假列表); 无数据时返回空或温和提示, 不得造假。"
    "④设计规范: 前端颜色/间距/字号一律用 Element Plus 设计 Token (var(--el-color-primary)、"
    "var(--el-bg-color-overlay)、var(--el-border-color) 等), 禁止硬编码十六进制颜色; "
    "模板先引 mtscos_design_tokens.css。"
    "⑤命名空间: /admin_app/* 是管理员后台(require_auth=admin), 学生/前台页面禁止链接到 /admin_app/* "
    "(学生会被重定向到管理员登录页); 学生功能页建在 /student/* 学生命名空间。"
    "⑥Ollama 云端优先路由: AI 推理优先走 Ollama Cloud(11434, gpt-oss:20b), 本地原生 Ollama(11435, qwen2.5:7b, 零token)兜底, "
    "火山引擎方舟ARK仅最终兜底(默认关, MTSCOS_AI_ALLOW_CLOUD=1 开启), 不得默认依赖火山付费云端。"
    "⑦代码规范: Python 4 空格缩进、行宽≤120 字符; 业务逻辑放 Service 层; API 统一响应格式 "
    "{code, message, data, timestamp}; 输入参数用白名单/类型校验(frozenset、_safe_int/_safe_str)。"
    "⑧规则文本强约束: 编写/修改规则文档时禁用弱约束词(应该/建议/推荐/尽量/原则上/一般/可考虑/"
    "适当/酌情/最好/尽可能/视情况 等), 一律改为强制表述(必须/禁止/不得/一律)。"
    "⑨开发流程: 大范围/新功能/高风险改动必须走 §14 强制开发12步骤(提案→会议→EigenFlux磋商→"
    "SA终审→实现→千轮测试), 不得跳过审批; 规则修改必须7步审批。"
    "不确定某规范细节时, 优先与现有同类文件的既有写法保持一致, 不要臆造新约定。"
)


def _with_rules(system: str, include_project: bool = True) -> str:
    """统一拼装 system prompt: 调用方角色说明 + 编码铁律 + 项目硬规则(不可豁免)。"""
    base = system or ""
    return base + _CODE_RULES + (_PROJECT_RULES if include_project else "")


def code(prompt: str, system: str = "", flow_id: Optional[str] = None) -> Dict[str, Any]:
    """编码任务入口 (代码生成/补全/重构, 优先使用编码专用模型)

    注意: 编码铁律(_CODE_RULES)始终追加到 system 末尾, 调用方传入的自定义
    system 只能补充角色/风格, 不能豁免'只输出代码、禁止执行指令'的约束。
    """
    if not system:
        system = ("你是资深全栈工程师,精通Python/JavaScript/TypeScript/HTML/CSS/SQL。"
                  "输出代码要求: 1.完整可运行 2.注释清晰 3.遵循PEP8/ESLint规范 "
                  "4.优先给出代码,简短说明即可。")
    system = _with_rules(system)  # 编码铁律 + MTSCOS项目硬规则, 不可豁免
    result = _route_chat(prompt, system, flow_id, use_coder=True)
    result["kind"] = "code"
    return result


def optimize_file(file_path: str, instruction: str = "", write_back: bool = False,
                  flow_id: Optional[str] = None) -> Dict[str, Any]:
    """
    优化文件入口 (读取文件→AI优化→可选写回)
    write_back=True  直接覆盖文件
    write_back=False 仅返回优化建议(diff),不修改文件
    """
    import os
    if not os.path.isfile(file_path):
        return {"success": False, "error": f"文件不存在: {file_path}"}

    with open(file_path, "r", encoding="utf-8") as f:
        original = f.read()

    ext = os.path.splitext(file_path)[1].lstrip(".")
    if not instruction:
        instruction = "优化代码质量: 修复潜在bug、提升可读性、遵循语言最佳实践,保持功能不变"

    system = (f"你是资深{ext}工程师。对以下代码进行优化。"
              "要求: 1.保持功能不变 2.修复潜在bug 3.提升可读性和性能 "
              "4.遵循语言规范 5.只输出优化后的完整代码,不要解释。")
    system = _with_rules(system)  # 编码铁律 + MTSCOS项目硬规则
    prompt = f"文件: {os.path.basename(file_path)}\n优化要求: {instruction}\n\n原始代码:\n```{ext}\n{original}\n```\n\n优化后的完整代码:"

    result = _route_chat(prompt, system, flow_id, use_coder=True)
    if not result["success"]:
        result["kind"] = "optimize"
        return result

    optimized = result.get("response", "")
    # 提取代码块内容
    import re
    code_match = re.search(r"```(?:\w+)?\n(.*?)```", optimized, re.DOTALL)
    if code_match:
        optimized_code = code_match.group(1)
    else:
        optimized_code = optimized

    result["kind"] = "optimize"
    result["original"] = original
    result["optimized"] = optimized_code
    result["file"] = file_path
    result["write_back"] = write_back

    if write_back:
        try:
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(optimized_code)
            result["written"] = True
        except Exception as e:
            result["written"] = False
            result["write_error"] = str(e)
    else:
        result["written"] = False

    return result


# ===== auto_fix 智能化: 写前验证 + 原子替换 + 失败回滚 + 静态安全审计 =====

def _verify_py_syntax(content):
    """用 ast 做语法校验(不执行/不导入, 避免触发重型应用初始化)。返回 (ok, errmsg)。"""
    try:
        import ast
        ast.parse(content)
        return True, ""
    except SyntaxError as e:
        return False, f"SyntaxError L{e.lineno}: {e.msg}"
    except Exception as e:  # noqa: BLE001
        return False, f"{type(e).__name__}: {e}"


def _has_markdown_fence(content):
    """检测AI残留的markdown代码围栏(```py / ``` 独立行), 这类内容写进源码必损坏。"""
    for ln in content.splitlines():
        s = ln.strip()
        if s.startswith("```"):
            return True
    return False


# 越权/鉴权特征: 出现任一即视为该函数已有归属或权限校验(保守, 宁可不报不误报)
_OWNERSHIP_MARKERS = (
    "_is_staff", "_check_admin", "_check_login", "system_container", "allowed_roles",
    "require_auth", "_uid_of", "user_id == ", "== user_id", "!= str(user_id)",
    "is_super_admin", "current_user", "g.current_user", "login_required", "abort(403",
)


def _audit_route_idor(content, rel_path):
    """路由文件IDOR预警(仅提示, 不阻断): 含 user_id 参数/路径的视图但函数体内无归属/权限校验。

    保守策略: 按函数切块, 只有"明显用到user_id且完全无任何鉴权标记"才报, 降低误报。
    """
    warnings_ = []
    if "/routes/" not in rel_path.replace("\\", "/") and not rel_path.startswith("routes/"):
        return warnings_
    import re
    # 按装饰器边界切块: 每个路由块 = @route装饰器(们) + def + 函数体(直到下一个装饰器)
    # 不能按 def 切, 否则会把装饰器行与函数体拆开导致误报
    blocks = re.split(r"\n(?=@)", content)
    for blk in blocks:
        if ".route(" not in blk:
            continue
        if "user_id" not in blk:
            continue
        uses_uid = ("<int:user_id>" in blk or "<user_id>" in blk
                    or "data.get('user_id')" in blk or 'data.get("user_id")' in blk
                    or re.search(r"\buser_id\s*=", blk) is not None)
        if not uses_uid:
            continue
        if not any(m in blk for m in _OWNERSHIP_MARKERS):
            m = re.search(r"def (\w+)\(", blk)
            fn = m.group(1) if m else "?"
            warnings_.append(f"路由 {fn}() 用到 user_id 但未见归属/权限校验, 疑似IDOR越权(请人工确认)")
    return warnings_


def _audit_template_links(content, rel_path):
    """模板预警: 学生/前台页面出现指向管理员命名空间 /admin_app/ 的活动链接(学生访问会被踢登录)。"""
    warnings_ = []
    if not rel_path.endswith((".html", ".jinja", ".jinja2")):
        return warnings_
    low = rel_path.lower()
    is_student_facing = ("student" in low) or ("portal" in low)
    if not is_student_facing:
        return warnings_
    import re
    for m in re.finditer(r'<a\s+[^>]*href=["\']([^"\']+)["\']', content):
        href = m.group(1)
        if "/admin_app/" in href:
            warnings_.append(f"学生模板出现管理员命名空间链接 {href} (学生访问会被重定向到管理员登录)")
    return warnings_


# 显式文件路径提取: 从用户请求中抓取明确的文件路径(含扩展名或路径分隔符), 优先命中,
# 避免AI定位/关键词降级误匹配到无关文件(历史问题: 改 ai_file_organizer 却命中 ai_performance_optimizer)。
_EXPLICIT_EXT = {".py", ".js", ".ts", ".html", ".css", ".sql", ".json", ".yml", ".yaml",
                 ".sh", ".jinja", ".jinja2", ".md", ".xml", ".ini", ".cfg", ".toml", ".txt"}


def _extract_explicit_file_paths(request: str, project_root: str, scanned_files: List[str]) -> List[str]:
    """从请求文本中提取显式文件路径, 返回相对 project_root 且真实存在的文件列表。

    匹配策略:
      1. 抓取含 '/' 或 '\\' 的路径片段(如 engines/ai_file_organizer.py / flask-app/engines/x.py)
      2. 抓取裸文件名(如 ai_file_organizer.py), 在 scanned_files 中精确匹配 basename
      3. 解析时兼容: 直接相对 project_root / 去掉前缀 flask-app/ 后相对 project_root
    """
    import os as _os
    import re as _re
    hits: List[str] = []
    seen = set()
    scanned_set = set(scanned_files)

    # 1) 路径片段: 允许字母数字 _ . - / \\ 组成, 必须含扩展名
    path_tokens = _re.findall(r"[\w./\\-]+\.(?:py|js|ts|html|css|sql|json|yml|yaml|sh|jinja|jinja2|md|xml|ini|cfg|toml|txt)",
                             request, _re.IGNORECASE)
    # 2) 裸文件名 (不含分隔符但有扩展名)
    bare_tokens = _re.findall(r"(?<![\w/\\])([\w-]+\.(?:py|js|ts|html|css|sql|json|yml|yaml|sh|jinja|jinja2|md|xml|ini|cfg|toml|txt))",
                             request, _re.IGNORECASE)

    for tok in path_tokens + bare_tokens:
        cand = tok.replace("\\", "/").rstrip(".,;:!?，。；：！？")
        if not cand:
            continue
        # 候选相对路径: 原样 / 去 flask-app/ 前缀
        cands = [cand]
        if cand.startswith("flask-app/"):
            cands.append(cand[len("flask-app/"):])
        # 也尝试只取 basename (用户可能写了绝对路径或多余前缀)
        base = _os.path.basename(cand)
        if base != cand:
            cands.append(base)

        for c in cands:
            if c in seen:
                continue
            full = _os.path.join(project_root, c)
            if _os.path.isfile(full):
                seen.add(c)
                hits.append(c)
                break
            # basename 精确匹配 scanned_files (用户只给了文件名)
            if "/" not in c:
                for rel in scanned_files:
                    if _os.path.basename(rel) == c and rel not in seen:
                        seen.add(rel)
                        hits.append(rel)
                        break
    return hits[:8]


def auto_fix(request: str, project_root: str = "", dry_run: bool = False,
             flow_id: Optional[str] = None) -> Dict[str, Any]:
    """
    自动修复入口 (分析需求→定位文件→AI修改→写回)
    request: 用户的自然语言需求
    project_root: 项目根目录(默认自动检测)
    dry_run: True=只输出计划不修改, False=自动修改(带备份)
    操作型指令(同步GitHub/拉取/测试等)自动分流到 execute_task 真实执行
    """
    import os
    import glob
    import shutil
    import re

    # auto_fix 是改码执行器(加强版ai act的code_fix意图内部路由到这里): 只有"真正的操作执行型"
    # 指令(git/测试/装依赖)才分流到 execute_task;
    # 只读分析类意图(dev_audit/feature_expand/日志/员工统计等)必须进入改码流程, 不能劫持成只读体检。
    # 设计原则: 用户要求"改代码", 语义就是"改代码", 任何把它偷偷降级为只读的行为都是错的。
    _EXEC_OP_INTENTS = {"git_sync", "git_pull", "git_status", "run_tests", "install_deps"}
    op_intent = _detect_operation_intent(request)
    if op_intent is None:
        _ai_intents = _ai_classify_intents(request, flow_id)
        op_intent = _ai_intents[0] if _ai_intents else None
    if op_intent in _EXEC_OP_INTENTS:
        root = project_root or os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        return execute_task(request, root, dry_run, flow_id)

    if not project_root:
        # 自动检测项目根目录
        project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

    if _CLI:
        _banner("AI 自动修复 · auto_fix", "qwen2.5-coder:14b", "local_ollama")
        _stage(f"需求: \033[1m{request[:50]}\033[0m")
        _stage(f"项目根: {project_root}")

    nd = _Nodes("AI 自动修复", [("扫描项目源码文件", 8, "scan"),
                                ("AI 分析需求 · 定位目标文件", 40, "locate")])
    nd.start()
    try:
        # 1. 扫描项目文件列表(限常见源码文件, 排除大目录; templates 必须纳入, 否则前端需求无法定位)
        exclude_dirs = {'.git', '__pycache__', 'node_modules', '.venv', 'venv',
                        'migrations', '_output', '_archive', '_runtime', 'static'}
        code_exts = {'.py', '.js', '.ts', '.html', '.css', '.sql', '.json', '.yml', '.yaml', '.sh', '.jinja', '.jinja2'}
        files = []
        with _Spin("扫描项目源码文件"):
            for r0, dirs, filenames in os.walk(project_root):
                dirs[:] = [d for d in dirs if d not in exclude_dirs and not d.startswith('.')]
                for fn in filenames:
                    ext = os.path.splitext(fn)[1]
                    if ext in code_exts:
                        files.append(os.path.relpath(os.path.join(r0, fn), project_root))
        files = sorted(files)[:400]  # 提高上限, 避免大项目关键文件被截断
        nd.ok(0, note=f"{len(files)}个源码文件")
        if _CLI:
            _stage(f"发现 \033[32m{len(files)}\033[0m 个源码文件")

        # 2.0 显式路径优先: 若用户请求中包含明确文件路径(如 engines/ai_file_organizer.py 或
        # flask-app/engines/ai_file_organizer.py), 直接命中, 跳过AI定位, 避免关键词误匹配改坏无关文件。
        plan_result = None  # 显式路径分支不经过AI定位, plan_result 保持 None
        target_files = _extract_explicit_file_paths(request, project_root, files)
        if target_files:
            if _CLI:
                _stage(f"从请求中提取到显式文件路径: {', '.join(target_files)}")
        else:
            # 2. 让AI分析需求并确定要修改的文件
            file_list_str = "\n".join(files[:200])  # 给AI看的上限提高到200
            system = ("你是项目维护助手。根据用户需求,从文件列表中选择需要修改的文件。"
                      "只返回需要修改的文件相对路径,每行一个,不要其他文字。")
            prompt = f"用户需求: {request}\n\n项目文件列表:\n{file_list_str}\n\n需要修改的文件:"

            with _Spin("AI 分析需求 · 定位目标文件"):
                plan_result = _route_chat(prompt, system, flow_id, use_coder=True)
            if not plan_result["success"]:
                nd.err(1, note=(plan_result.get("error") or "AI分析失败")[:50])
                return {"success": False, "error": "AI分析失败", "detail": plan_result}

            target_files = [l.strip() for l in plan_result["response"].split("\n")
                            if l.strip() and not l.startswith("```")]
            # 过滤出真实存在的文件, 上限8个(允许稍大范围改动但避免失控)
            target_files = [f for f in target_files if os.path.isfile(os.path.join(project_root, f))][:8]

            # AI定位失败降级: 用需求关键词在项目中检索真实文件, 避免直接失败
            if not target_files:
                try:
                    # 分词: 按标点/空格切, 中文长词再用2-3字滑窗拆(中文无空格分隔)
                    raw_tokens = [w for w in re.split(r"[\s'\"，。、/\\|（）()【】\[\]]+", request)
                                  if len(w) >= 1 and w not in ("ai", "fix", "的", "了", "和", "与", "及")]
                    kw = set()
                    for t in raw_tokens:
                        if len(t) <= 4:
                            kw.add(t.lower())
                        else:
                            # 中文长词: 2字+3字滑窗, 覆盖文件名常见片段
                            for n in (2, 3):
                                for i in range(len(t) - n + 1):
                                    kw.add(t[i:i+n].lower())
                    # 第一级: 文件名匹配
                    keyword_hits = []
                    for rel in files:
                        low = rel.lower()
                        score = sum(1 for w in kw if len(w) >= 2 and w in low)
                        if score > 0:
                            keyword_hits.append((score, rel))
                    keyword_hits.sort(key=lambda x: (-x[0], len(x[1])))
                    target_files = [r for _, r in keyword_hits[:3]]
                    # 第二级: 文件内容轻量匹配(只搜高相关目录前150文件前150行, 覆盖中文需求匹配英文文件名)
                    if not target_files:
                        content_hits = []
                        scan_files = [r for r in files if r.split("/")[0] in
                                      ("routes", "templates", "ai_engines", "services", "app", "core")][:150]
                        for rel in scan_files:
                            full = os.path.join(project_root, rel)
                            try:
                                with open(full, "r", encoding="utf-8", errors="ignore") as f:
                                    head = "".join(f.readlines()[:150]).lower()
                            except Exception:
                                continue
                            score = sum(1 for w in kw if len(w) >= 2 and w in head)
                            if score >= 2:  # 至少2个关键词命中才算相关
                                content_hits.append((score, rel))
                        content_hits.sort(key=lambda x: (-x[0], len(x[1])))
                        target_files = [r for _, r in content_hits[:3]]
                        if _CLI and target_files:
                            _stage(f"AI定位未命中, 已用内容关键词检索到候选文件: {', '.join(target_files)}")
                    elif _CLI:
                        _stage(f"AI定位未命中, 已用文件名关键词检索到候选文件: {', '.join(target_files)}")
                except Exception:
                    pass

        if not target_files:
            nd.err(1, note="未匹配到需要修改的文件")
            if _CLI:
                _stage("\033[31m未匹配到需要修改的文件\033[0m (需求过于模糊, 请指明具体模块/功能)")
            return {"success": False, "error": "未找到需要修改的文件",
                    "ai_plan": plan_result.get("response", "") if plan_result else "",
                    "hint": "需求过于模糊导致AI无法定位文件, 请指明具体模块/功能(如'完善学生端学习面板'/'修复k12路由IDOR')"}
        nd.ok(1, note=f"{len(target_files)}个目标文件")
        if _CLI:
            _stage(f"定位到 \033[33m{len(target_files)}\033[0m 个目标文件: {', '.join(target_files)}")

        # 3. 逐个修改文件 (动态加入节点清单)
        modified = []
        for idx, rel_path in enumerate(target_files, 1):
            full_path = os.path.join(project_root, rel_path)
            ext = os.path.splitext(rel_path)[1].lstrip(".")
            j = nd.add(f"AI 生成修改 · {rel_path}", est=60, group="gen")
            nd.run(j)
            if _CLI:
                _stage(f"[{idx}/{len(target_files)}] 生成修改 · \033[36m{rel_path}\033[0m")

            with open(full_path, "r", encoding="utf-8") as f:
                original = f.read()

            opt_system = (f"你是资深{ext}工程师, 严格遵守MTSCOS项目规范。根据用户需求修改以下代码。"
                          "要求: 1.只输出修改后的完整代码 2.不要解释 3.保持未涉及部分不变 "
                          "4.禁止输出任何shell/终端命令(如pip/python/git/npm)或让用户执行命令的步骤, "
                          "所有需求只通过代码修改解决, 依赖问题只写在代码注释里。")
            opt_system = _with_rules(opt_system)  # 编码铁律 + 项目硬规则(权限/IDOR/真数据/设计Token/命名空间等)
            opt_prompt = (f"用户需求: {request}\n文件: {rel_path}\n\n"
                          f"当前代码:\n```{ext}\n{original}\n```\n\n修改后的完整代码:")

            with _Spin(f"AI 生成代码 · {rel_path[:34]}"):
                opt_result = _route_chat(opt_prompt, opt_system, flow_id, use_coder=True)
            if not opt_result["success"]:
                nd.err(j, note=(opt_result.get("error") or "生成失败")[:50])
                modified.append({"file": rel_path, "success": False,
                                 "error": opt_result.get("error", "")})
                continue

            new_code = opt_result.get("response", "")
            code_match = re.search(r"```(?:\w+)?\n(.*?)```", new_code, re.DOTALL)
            if code_match:
                new_code = code_match.group(1)
            else:
                # 无条件剥离独立的首尾 markdown 围栏行 (防止无收尾围栏时污染文件)
                _lines = new_code.splitlines()
                while _lines and _lines[0].lstrip().startswith("```"):
                    _lines.pop(0)
                while _lines and _lines[-1].strip().startswith("```"):
                    _lines.pop()
                new_code = "\n".join(_lines)
            new_code = new_code.strip("\n") + "\n"

            if dry_run:
                nd.ok(j, note="dry-run 预览")
                # dry-run 也做静态校验, 提前暴露AI生成的坏代码
                _vwarn = []
                if ext == "py":
                    okv, errv = _verify_py_syntax(new_code)
                    if not okv:
                        _vwarn.append(f"语法校验未通过(未写盘): {errv}")
                elif _has_markdown_fence(new_code):
                    _vwarn.append("检测到markdown围栏残留(未写盘)")
                _vwarn += _audit_route_idor(new_code, rel_path) + _audit_template_links(new_code, rel_path)
                modified.append({"file": rel_path, "success": True,
                                 "dry_run": True, "new_code": new_code,
                                 "verify_ok": not any("未通过" in w or "残留" in w for w in _vwarn),
                                 "warnings": _vwarn})
            else:
                # 备份原文件
                backup_path = full_path + ".bak"
                shutil.copy2(full_path, backup_path)
                tmp_path = full_path + ".tmp"
                try:
                    # 1) 先写临时文件
                    with open(tmp_path, "w", encoding="utf-8") as f:
                        f.write(new_code)

                    # 2) 写前智能验证: .py 语法校验; 所有类型围栏污染检测
                    verify_err = ""
                    if ext == "py":
                        okv, errv = _verify_py_syntax(new_code)
                        if not okv:
                            verify_err = errv
                    if not verify_err and _has_markdown_fence(new_code):
                        verify_err = "检测到markdown围栏(```)残留, 拒绝写回"

                    if verify_err:
                        # 验证失败: 删除tmp, 保留原文件不动(回滚), 报告失败
                        try:
                            os.remove(tmp_path)
                        except OSError:
                            pass
                        nd.err(j, note=f"验证失败已回滚: {verify_err[:36]}")
                        if _CLI:
                            _stage(f"  \033[31m验证失败, 已回滚\033[0m {rel_path}: {verify_err}")
                        modified.append({"file": rel_path, "success": False,
                                         "rolled_back": True, "backup": backup_path,
                                         "error": f"写前验证失败, 原文件未改动: {verify_err}"})
                        continue

                    # 3) 验证通过: 原子替换 + 静态安全审计(提示级)
                    os.replace(tmp_path, full_path)
                    warns = _audit_route_idor(new_code, rel_path) + _audit_template_links(new_code, rel_path)
                    note = "已写回+验证通过" + (f" · {len(warns)}项审计提示" if warns else "")
                    nd.ok(j, note=note)
                    if _CLI:
                        _stage(f"  \033[32m已写回并验证通过\033[0m {rel_path} (备份: .bak)")
                        for w in warns:
                            _stage(f"  \033[33m⚠ 审计提示\033[0m {w}")
                    modified.append({"file": rel_path, "success": True,
                                     "backup": backup_path, "written": True,
                                     "verify_ok": True, "warnings": warns})
                except Exception as e:
                    # 写盘异常: 尽力回滚(原文件已在.bak, 且tmp未replace则原文件完好)
                    try:
                        if os.path.exists(tmp_path):
                            os.remove(tmp_path)
                    except OSError:
                        pass
                    nd.err(j, note=str(e)[:50])
                    modified.append({"file": rel_path, "success": False, "error": str(e)})
    finally:
        nd.close()

    # 智能化验证汇总
    written_files = [m["file"] for m in modified if m.get("written") and m.get("verify_ok")]
    rolled_back = [m["file"] for m in modified if m.get("rolled_back") or (m.get("success") is False and not m.get("dry_run"))]
    all_warnings = [w for m in modified for w in (m.get("warnings") or [])]
    dry_blocked = [m["file"] for m in modified if m.get("dry_run") and m.get("verify_ok") is False]

    # 真实改码证据: 只有确实 os.replace 成功写盘的才算 "已修改"
    actually_modified = written_files if not dry_run else []

    if _CLI:
        _stage(f"验证汇总: \033[32m写回并通过 {len(written_files)}\033[0m · "
               f"\033[31m回滚/失败 {len(rolled_back)}\033[0m · "
               f"\033[33m审计提示 {len(all_warnings)}\033[0m")
        if not dry_run and not actually_modified:
            _stage("\033[31m⚠ 本次代码修复未发生任何实际代码修改\033[0m (如需执行型操作请用 ai act)")

    _ok = len(actually_modified) > 0 or (dry_run and len(modified) > 0)
    return {
        "success": _ok,
        "kind": "auto_fix",
        "request": request,
        "target_files": target_files,
        "modified": modified,
        "dry_run": dry_run,
        "actually_modified_files": actually_modified,  # 真实落盘的文件清单(非dry_run才有值)
        "verification": {
            "written_verified": len(written_files),
            "rolled_back": len(rolled_back),
            "dry_run_blocked": len(dry_blocked),
            "warnings": len(all_warnings),
            "warning_items": all_warnings,
            "all_verified": len(rolled_back) == 0 and len(dry_blocked) == 0,
        },
        "model": plan_result.get("model", "") if plan_result else "",
        "route": plan_result.get("route", "") if plan_result else "",
    }


# ===== 操作型意图: 白名单真实执行 =====
# 安全原则: AI 永远不生成原始shell命令, 只做意图分类;
# 实际执行的命令全部来自下方固定模板, 参数仅允许白名单内注入。
# 结构: intent_id: (动作描述, 关键词列表, 规范指令串)
#   - 动作描述: 展示给AI分类器和用户看
#   - 关键词: 确定性匹配用(零推理)
#   - 规范指令串: 交给 execute_task 二次识别用, 必须内含某个关键词
OPERATION_INTENTS = {
    "git_sync":      ("同步GitHub/推送/上传代码",        ["同步", "sync", "推送", "push", "上传", "提交并推"], "同步GitHub"),
    "git_pull":      ("拉取远端最新代码",                ["拉取", "pull", "拉代码", "拉最新"], "拉取最新代码"),
    "git_status":    ("查看仓库状态/变更",               ["仓库状态", "git状态", "status", "查看变更", "什么改了", "改了啥", "改了什么"], "查看仓库状态"),
    "run_tests":     ("运行项目测试",                    ["跑测试", "运行测试", "执行测试", "pytest"], "运行测试"),
    "install_deps":  ("安装Python依赖(requirements.txt)", ["安装依赖", "装依赖", "依赖安装", "pip install",
                                                                     "install deps", "安装requirements", "安装依赖包"], "安装依赖"),
    "engine_health": ("本地AI引擎健康检查(只读)",         ["引擎健康", "健康检查", "引擎状态", "ai状态",
                                                                     "ai健康", "ollama状态"], "引擎健康检查"),
    # 系统性能诊断: 全程只读采集 + AI给建议, 绝不自动清理/改配置(副作用操作须用户另行明确指令)
    # 注意: 关键词都带"系统/电脑"等语境或专用词, 避免误匹配"优化这段代码/代码性能"
    "system_diagnose": ("系统性能诊断(只读:磁盘/负载/内存/进程/AI引擎, 并给优化建议)",
                        ["系统性能", "系统优化", "优化系统", "系统慢", "系统很慢", "系统有点慢",
                         "电脑慢", "电脑卡", "电脑卡顿", "电脑很卡", "电脑有点卡", "机器卡", "运行慢", "变慢",
                         "系统诊断", "系统体检", "系统提速", "diagnose", "performance"],
                        "系统性能诊断"),
    # 功能拓展分析: 全程只读盘点 + AI给拓展建议, 绝不自动改代码(代码修改须走 ai code/fix)
    "feature_expand": ("系统功能拓展分析(只读:盘点引擎/AI集/模型现状, AI生成功能扩充建议)",
                       ["拓展系统功能", "扩展系统功能", "系统功能拓展", "系统功能扩展",
                        "拓展功能", "扩展功能", "扩充功能", "功能拓展", "功能扩展", "功能扩充",
                        "拓展ai", "扩展ai", "功能进化", "新功能建议", "expand", "feature"],
                       "系统功能拓展分析"),
    # daemon状态: 只读检测PID文件+进程存活+daemon注册表, 绝不启停进程
    "daemon_status":  ("自动化daemon运行状态查看(只读:PID存活检测+daemon注册表)",
                       ["daemon状态", "守护进程", "后台进程", "自动进程",
                        "进程状态", "daemon跑", "daemon运行", "多少个daemon", "守护状态",
                        "daemon情况", "daemon列表", "daemon在不在", "守护进程在不在"],
                       "daemon运行状态查看"),
    # AI队伍统计: 只读查库(AI员工/EigenFlux/雇佣记录), 绝不新增/修改员工
    "ai_workforce":   ("AI员工/EigenFlux队伍统计(只读:员工数/注册数/雇佣记录)",
                       ["ai员工", "ai员工统计", "员工数量", "员工多少", "员工统计",
                        "ai队伍", "队伍统计", "eigenflux", "专家团队", "雇佣记录",
                        "多少员工", "员工情况", "ai人口", "员工在册"],
                       "AI员工队伍统计查看"),
    # 系统日志: 只读tail最新日志, 绝不删除/修改日志
    "view_logs":      ("系统最近日志查看(只读:tail最新运行日志)",
                       ["查看日志", "看日志", "最近日志", "系统日志", "错误日志",
                        "日志看看", "日志内容", "tail日志", "最新日志", "运行日志"],
                       "系统最近日志查看"),
    # 功能区体检(只读): 完善/补齐XX功能类需求, 只出缺口报告+任务清单, 不改代码; 落地走 ai act 代码修复
    "dev_audit":      ("功能区体检与缺口分析(只读:盘点某模块前端/路由/中间件, AI出任务清单, 不改代码)",
                       ["完善", "补齐", "补全", "功能体检", "功能审计", "缺口分析", "功能盘点",
                        "任务清单", "模块体检", "前端显示", "后端数据安全", "中间件功能",
                        "完善用户", "完善学生", "检查功能", "功能完善度", "dev_audit", "audit"],
                       "功能区体检与缺口分析"),
    # 代码修复(加强版ai act核心能力, v22.18.0 'ai fix'并入): 修复/修改代码类需求
    # → 内部路由 auto_fix(定位→AI改码→AST校验→原子写回+备份回滚), AI永不接触shell
    "code_fix":       ("代码修复/修改/重构(auto_fix:定位→AI改码→AST校验→原子写回+备份)",
                       ["修复", "修好", "修bug", "修 bug", "bug修复", "修复bug", "修复代码",
                        "代码修复", "修改代码", "改代码", "重构代码", "fix", "bugfix"],
                       "代码修复(auto_fix落盘)"),
    # 脑库投喂: 将知识/经验/异常/规则等同步到 mt_ai_brain_feed_log 表
    "brain_feed":     ("脑库投喂(将知识/经验/异常/规则等同步到AI脑库)",
                       ["投喂", "脑库", "同步到脑库", "知识投喂", "经验投喂", "异常投喂",
                        "规则投喂", "brain feed", "brain_feed", "喂给脑库", "写入脑库"],
                       "脑库投喂"),
}

# ===== ai act 递归分发: 支持 'ai act "ai fix ..."' / 'ai act "... ai chat ..."' 指令套指令 =====
# 可嵌套的 ai 子命令白名单 (AI 永不生成任意命令, 子命令固定; 参数文本交给对应网关函数)
_NESTED_SUBS = {"fix", "optimize", "code", "chat", "think", "act",
                "run", "sync", "analyze", "compile", "review", "classify"}
# 匹配 'ai <子命令>' 标记 (要求 ai 后有空白再跟英文子命令+词边界, 避免误伤 'ai员工/ai状态' 等中文词)
_NESTED_CMD_RE = re.compile(
    r"ai\s+(fix|optimize|code|chat|think|act|run|sync|analyze|compile|review|classify)\b",
    re.IGNORECASE)
# 匹配 'ai "XXX"' 或 'ai 'XXX'' 管道模式 (v22.19.0: 先执行 ai 'XXX' 得到结果, 再把结果传给 ai act)
_AI_PIPE_RE = re.compile(r'ai\s+[\'"]([^\'"]+)[\'"]', re.IGNORECASE)
# 嵌套 ai act 最大递归深度 (防止 'ai act "ai act "ai act ..."' 无限递归)
_MAX_ACT_DEPTH = 3


def _detect_operation_intents(request: str) -> list:
    """多意图关键词匹配 (确定性, 零推理): 按关键词在句中首次出现位置排序,
    支持链式指令(如'拉取代码后安装依赖再跑测试' → [git_pull, install_deps, run_tests])"""
    low = request.lower()
    found = []
    for intent, (_desc, kws, _canonical) in OPERATION_INTENTS.items():
        positions = [low.find(kw) for kw in kws if kw in low]
        if positions:
            found.append((min(positions), intent))
    found.sort(key=lambda x: x[0])
    return [intent for _pos, intent in found]


def _detect_operation_intent(request: str) -> Optional[str]:
    """单意图关键词分类 (向后兼容: auto_fix分流等旧调用方)"""
    intents = _detect_operation_intents(request)
    return intents[0] if intents else None


def _ai_classify_intents(request: str, flow_id: Optional[str] = None) -> list:
    """本地AI意图分类(零token): AI只从注册动作ID中选择, 永不生成shell命令。
    成功返回动作ID列表(可能为空), 任何异常/解析失败返回 []"""
    import re
    try:
        catalog = "\n".join(f"- {k}: {v[0]}" for k, v in OPERATION_INTENTS.items())
        system = ("你是操作意图分类器。根据用户指令, 从下列动作ID中选出需要真实执行的动作"
                  "(可多选, 按执行先后顺序排列)。只输出JSON数组, 例如 [\"git_pull\",\"run_tests\"], "
                  "不要输出任何其他文字、解释、markdown或命令。没有匹配动作时输出 []。\n"
                  "可用动作:\n" + catalog)
        r = chat(f"用户指令: {request}", system, flow_id or "act_ai_classify")
        if not r.get("success"):
            return []
        text = r.get("response", "")
        m = re.search(r"\[.*?\]", text, re.DOTALL)
        if not m:
            return []
        ids = json.loads(m.group(0))
        if not isinstance(ids, list):
            return []
        # 仅保留白名单内ID, 去重保序
        seen, out = set(), []
        for i in ids:
            if isinstance(i, str) and i in OPERATION_INTENTS and i not in seen:
                seen.add(i)
                out.append(i)
        return out
    except Exception:
        return []


def _cli_log(text: str):
    """CLI附属输出: 有节点清单时并入清单日志区, 否则直接打印"""
    if not _CLI:
        return
    if _NODES is not None:
        _NODES.log(text)
    else:
        sys.stderr.write(text + "\n")
        sys.stderr.flush()


def _run_cmd(cmd: list, cwd: str, timeout: int = 120) -> Dict[str, Any]:
    """执行单条白名单命令, 返回结构化结果 (CLI模式显示实时进度)"""
    import subprocess
    import os as _os
    env = dict(_os.environ)
    if cmd and cmd[0] == "git":
        env["GIT_OPTIONAL_LOCKS"] = "0"  # OneDrive大仓库避免索引写锁
    label = " ".join(cmd)
    try:
        with _Spin(f"执行 · {label[:44]}"):
            p = subprocess.run(cmd, cwd=cwd, capture_output=True, text=True,
                               timeout=timeout, shell=False, env=env)
        out = (p.stdout + p.stderr).strip()
        # 超长输出保留头部+尾部: 尾部通常是真正的错误行(如 pip 的 ERROR: No matching distribution)
        if len(out) > 3000:
            out = out[:1500] + "\n... [中间输出已截断] ...\n" + out[-1500:]
        if _CLI:
            # 成功打印头部进度行, 失败打印尾部错误行
            show = out.splitlines()
            show = show[:4] if p.returncode == 0 else show[-4:]
            for line in show:
                _cli_log(f"  {line[:70]}")
        return {"cmd": label, "ok": p.returncode == 0,
                "rc": p.returncode, "output": out[:3200]}
    except subprocess.TimeoutExpired:
        _cli_log(f"  \033[31m超时({timeout}s)\033[0m")
        return {"cmd": label, "ok": False, "rc": -1,
                "output": f"超时({timeout}s)"}
    except Exception as e:
        return {"cmd": label, "ok": False, "rc": -1, "output": str(e)}


def execute_task(request: str, repo_root: str = "", dry_run: bool = False,
                 flow_id: Optional[str] = None) -> Dict[str, Any]:
    """操作执行入口 (对外稳定接口): 保证任何失败都带 error 字段, 永不出空结果"""
    try:
        result = _execute_task_impl(request, repo_root, dry_run, flow_id)
    except Exception as e:
        return {"success": False, "kind": "execute", "request": request,
                "error": f"执行异常: {type(e).__name__}: {e}",
                "steps": []}

    if not result.get("success") and not result.get("error"):
        # 兜底: 从失败步骤提取输出
        for s in result.get("steps", []):
            if s.get("ok") is False:
                result["error"] = f"[{s.get('cmd','')}] {s.get('output','')}".strip()[:400]
                break
        result.setdefault("error", "未知失败 (无步骤输出)")

    # OneDrive 环境诊断提示
    err = result.get("error") or ""
    if err and ("mmap failed" in err or "Operation timed out" in err):
        result["hint"] = (
            "检测到 .git 位于 OneDrive 云端目录, git 内存映射超时。"
            "建议: 1) 在你自己的 Terminal(非Trae沙箱) 运行 2) 先执行 'brctl download <.git路径>' 落盘 "
            "3) 长期方案: 把仓库迁出 OneDrive 到 ~/Projects/ 后软链回来。")
    return result


def _execute_task_impl(request: str, repo_root: str = "", dry_run: bool = False,
                       flow_id: Optional[str] = None) -> Dict[str, Any]:
    """
    操作执行入口: 识别操作型指令并真实执行 (同步GitHub/拉取/状态/测试)
    - 意图识别: 关键词确定性匹配 (零推理)
    - 命令来源: 仅白名单模板, 禁止AI生成任意shell
    - git_sync: add → commit(AI生成中文提交信息) → push (永不force)
    """
    import os
    import subprocess
    import shlex
    import datetime

    if not repo_root:
        # 默认项目根 (gateway 位于 flask-app/ai_engines/, 向上3级)
        repo_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    repo_root = os.path.abspath(repo_root)

    intent = _detect_operation_intent(request)
    if intent is None:
        # 关键词未命中: 本地AI意图分类兜底(零token, 只从白名单动作选, 不生成命令)
        _ai_intents = _ai_classify_intents(request, flow_id)
        intent = _ai_intents[0] if _ai_intents else None
    if intent is None:
        return {"success": False, "kind": "execute", "error": "未识别的操作意图",
                "supported": {k: v[0] for k, v in OPERATION_INTENTS.items()},
                "hint": ("换个说法再试(如'daemon状态/AI员工多少/看日志/系统体检/拓展功能'); "
                         "咨询用 ai chat、方案用 ai think、代码修复用 ai act \"修复 xxx\"、"
                         "代码生成用 ai act \"ai code ...\"")}

    steps: list = []
    result = {"success": False, "kind": "execute", "intent": intent,
              "request": request, "repo": repo_root, "dry_run": dry_run, "steps": steps}

    def plan(*cmds):
        """dry-run 预览: 只登记计划命令, 不真实执行"""
        for c in cmds:
            steps.append({"cmd": c, "ok": None, "output": "(dry-run 预览)"})
        result["success"] = True

    # ===== 加强版ai act核心能力(v22.18.0 'ai fix'并入): 代码修复内部路由 auto_fix =====
    # auto_fix 自带: 显式路径提取优先 + AST写前校验 + 原子替换 + 自动备份回滚, AI永不接触shell
    if intent == "code_fix":
        _default_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        # 默认项目根时传 "" 让 auto_fix 自动定位 flask-app(显式路径相对 flask-app 解析, 兼容旧 ai fix 语义)
        fix_root = "" if os.path.abspath(repo_root) == os.path.abspath(_default_root) else repo_root
        r = auto_fix(request, fix_root, dry_run, flow_id)
        # 注入合成 step 供 act 看板展示与落库追溯(真实落盘结果, 非模拟)
        _files = r.get("actually_modified_files") or [
            m.get("file") for m in r.get("modified", []) if m.get("success")]
        _payload = (", ".join(f for f in _files if f) if _files
                    else str(r.get("error", "") or ("dry-run 预览通过" if dry_run else "无文件改动")))
        r.setdefault("steps", []).append({
            "cmd": f"auto_fix · {'📝 预览' if dry_run else '真实落盘'}: {_payload[:60]}",
            "ok": bool(r.get("success")), "rc": 0 if r.get("success") else 1,
            "output": (json.dumps(r.get("verification", {}), ensure_ascii=False)[:200]
                       if dry_run else _payload)[:400]})
        return r

    # ===== 脑库投喂: 将知识/经验/异常/规则等同步到 mt_ai_brain_feed_log 表 =====
    if intent == "brain_feed":
        if _CLI:
            _banner("🧠 脑库投喂", "将知识/经验/异常/规则等同步到AI脑库", "落库 mt_ai_brain_feed_log")
        nd = _Nodes("脑库投喂", [("解析投喂内容", 3, "parse"),
                               ("写入脑库表", 10, "insert")])
        nd.start()
        try:
            if dry_run:
                nd.skip_pending("dry-run 预览")
                plan(f"[AI] 解析投喂内容: {request[:60]}",
                     "[DB] INSERT INTO mt_ai_brain_feed_log (只读预览, 不真实写入)")
                return result

            # 1) AI 解析投喂内容(零token本地分类 + 内容摘要)
            nd.run(0)
            category = "general"
            for kw, cat in [("规则", "rule"), ("异常", "anomaly"), ("经验", "experience"),
                            ("知识", "knowledge"), ("投喂", "general")]:
                if kw in request:
                    category = cat
                    break
            title = request[:80]
            content = request
            nd.ok(0, note=f"分类: {category}")

            # 2) 写入脑库表
            nd.run(1)
            try:
                from schema_aligner import brain_insert
                feed_id = brain_insert(
                    flow_id=flow_id or "act_brain_feed",
                    category=category,
                    title=title,
                    content=content,
                    source="ai_act",
                    consensus_score=0.8,
                    tags=["ai_act", category]
                )
                if feed_id:
                    steps.append({"cmd": f"[脑库] INSERT feed_id={feed_id}", "ok": True, "rc": 0,
                                  "output": f"✅ 已写入 mt_ai_brain_feed_log (feed_id={feed_id}, category={category})"})
                    nd.ok(1, note=f"feed_id={feed_id}")
                else:
                    steps.append({"cmd": "[脑库] INSERT 失败", "ok": False, "rc": 1,
                                  "output": "brain_insert 返回 None (可能表不存在或写入异常)"})
                    nd.fail(1, "写入失败")
            except ImportError:
                steps.append({"cmd": "[脑库] schema_aligner 未找到", "ok": False, "rc": 1,
                              "output": "无法导入 schema_aligner.brain_insert"})
                nd.fail(1, "导入失败")
            except Exception as e:
                steps.append({"cmd": f"[脑库] 写入异常: {e}", "ok": False, "rc": 1,
                              "output": str(e)[:400]})
                nd.fail(1, f"异常: {e}")
            result["success"] = True
            return result
        finally:
            nd.close()

    # ===== 非git类动作: 不要求 .git 目录 =====
    if intent == "engine_health":
        if _CLI:
            _banner("⚡ 真实执行 · 引擎健康检查", "本地只读操作", "零token")
        nd = _Nodes("引擎健康检查", [("本地引擎健康采集", 6, "health")])
        nd.start()
        try:
            if dry_run:
                nd.skip_pending("dry-run 预览")
                plan("本地AI引擎健康检查(只读, 无副作用)")
                return result
            nd.run(0)
            h = health()
            local_ok = bool(h.get("local_ollama", {}).get("available"))
            cloud_gate = h.get("cloud_volcengine", {}).get("fallback_enabled", False)
            steps.append({"cmd": "local_ai_unified_gateway.health()", "ok": True, "rc": 0,
                          "output": json.dumps(h, ensure_ascii=False)[:2000]})
            gate_txt = "云端兜底已开(应急)" if cloud_gate else "云端兜底关闭(纯本地零token)"
            nd.ok(0, note=("本地在线 · " + gate_txt) if local_ok else ("本地离线 · " + gate_txt))
            result["success"] = True
            result["health"] = h
            return result
        finally:
            nd.close()

    if intent == "install_deps":
        import sys as _sys
        app_dir = os.path.join(repo_root, "flask-app")
        py_ver = f"{_sys.version_info.major}.{_sys.version_info.minor}"
        # 按解释器版本选择依赖清单: Python>=3.10 用完整版, 3.9及以下用兼容版(项目已自带)
        main_req = os.path.join(app_dir, "requirements.txt")
        py39_req = os.path.join(app_dir, "requirements-python39.txt")
        if _sys.version_info >= (3, 10):
            req_path, req_name = main_req, "requirements.txt"
        elif os.path.isfile(py39_req):
            req_path, req_name = py39_req, "requirements-python39.txt"
        else:
            req_path, req_name = main_req, "requirements.txt"
        if not os.path.isfile(req_path):
            return {"success": False, "kind": "execute", "intent": intent,
                    "error": f"未找到依赖文件: {req_path}", "steps": []}
        if _CLI:
            _banner("⚡ 真实执行 · 安装Python依赖", f"pip install -r {req_name}",
                    f"Python {py_ver} · 白名单")
            _stage(f"目录: {app_dir}")
        nd = _Nodes("安装Python依赖", [(f"pip install -r {req_name}", 120, "pip")])
        nd.start()
        try:
            cmd = ["python3", "-m", "pip", "install", "-r", req_name]
            if dry_run:
                nd.skip_pending("dry-run 预览")
                plan(f"python3 -m pip install -r {req_name}  (cwd: flask-app, Python {py_ver})")
                return result
            nd.run(0)
            steps.append(_run_cmd(cmd, app_dir, timeout=900))
            last = steps[-1]
            if last["ok"]:
                nd.ok(0)
            else:
                nd.err(0, note="依赖安装失败")
            result["success"] = last["ok"]
            result["python_version"] = py_ver
            result["requirements_file"] = req_name
            if not last["ok"]:
                # pip 真实错误在输出尾部(ERROR: ... 行), 头部多为进度/警告(如 user installation)
                out_lines = last["output"].splitlines()
                err_lines = [l for l in out_lines
                             if ("ERROR:" in l or "No matching distribution" in l
                                 or "Requires-Python" in l or "different python version" in l)]
                result["error"] = "\n".join(err_lines[-3:])[:400] if err_lines \
                    else "\n".join(out_lines[-5:])[:400]
                if "No matching distribution" in last["output"] or "different python version" in last["output"]:
                    result["hint"] = (f"当前 Python {py_ver} 与依赖版本不兼容"
                                      + ("(已自动选用 requirements-python39.txt 兼容清单)"
                                         if req_name == "requirements-python39.txt"
                                         else ", 升级到 Python 3.10+ 可安装完整安全修复版依赖"))
            return result
        finally:
            nd.close()

    if intent == "system_diagnose":
        # 系统性能诊断: 全程只读采集 + AI建议; 不做任何清理/改配置等副作用操作
        if _CLI:
            _banner("🔍 系统性能诊断", "全程只读采集(零副作用)", "AI给优化建议")
        nd = _Nodes("系统性能诊断", [("引擎健康 + 模型列表", 8, "diag"),
                                    ("系统指标只读采集 (5项)", 25, "diag"),
                                    ("AI 生成分层优化建议", 60, "diag_ai")])
        nd.start()
        try:
            diag_items = [
                ("磁盘空间",       ["df", "-h", "/"], repo_root, 60, 15),
                ("系统负载",       ["uptime"], repo_root, 30, 5),
                ("内存统计(macOS)", ["vm_stat"], repo_root, 30, 20),
                ("CPU占用Top进程",  ["ps", "-Ao", "pid,pcpu,pmem,comm", "-r"], repo_root, 30, 13),
                ("Ollama进程",     ["pgrep", "-fl", "ollama"], repo_root, 30, 10),
            ]
            if dry_run:
                nd.skip_pending("dry-run 预览")
                plan("[引擎健康检查 health()]", *[f"[只读采集] {name}: {' '.join(cmd)}"
                                                  for name, cmd, _d, _t, _n in diag_items],
                     "[AI] 基于采集数据生成分层优化建议(仅建议, 不执行)")
                return result

            # 1) 引擎健康 + Ollama模型 (Python内部, 只读)
            nd.run(0)
            try:
                h = health()
                steps.append({"cmd": "[引擎健康] local_ai_unified_gateway.health()", "ok": True, "rc": 0,
                              "output": json.dumps(h, ensure_ascii=False)[:1200]})
            except Exception as e:
                steps.append({"cmd": "[引擎健康] health()", "ok": False, "rc": -1,
                              "output": f"健康检查异常: {e}"})

            # 1b) Ollama 已装模型走 API(/api/tags), 不用 `ollama list` CLI(该命令在部分环境会卡死)
            try:
                from ai_ollama_engine import list_models as _ollama_list_models
                models = [m for m in _ollama_list_models() if not m.startswith("[FUSION_ENGINE]")]
                steps.append({"cmd": "[Ollama已装模型] GET /api/tags", "ok": bool(models), "rc": 0,
                              "output": "\n".join(models) if models else "(未获取到本地模型)"})
            except Exception as e:
                steps.append({"cmd": "[Ollama已装模型] GET /api/tags", "ok": False, "rc": -1,
                              "output": f"模型列表获取异常: {e}"})
            nd.ok(0)

            # 2) 系统指标采集(全部为只读白名单命令; 单项失败不中断, 失败本身也是诊断信息)
            nd.run(1)
            for name, cmd, cwd, timeout, max_lines in diag_items:
                try:
                    r = _run_cmd(cmd, cwd, timeout=timeout)
                    out_lines = (r.get("output") or "").splitlines()
                    r["output"] = "\n".join(out_lines[:max_lines])
                    if not r["ok"] and name == "Ollama进程" and r.get("rc") == 1:
                        # pgrep 无匹配返回1 = Ollama 未运行, 属正常诊断结论而非错误
                        r["ok"] = True
                        r["output"] = "(未检测到 ollama 进程, 本地引擎未启动)"
                    r["cmd"] = f"[{name}] {' '.join(cmd)}"
                    steps.append(r)
                except Exception as e:
                    steps.append({"cmd": f"[{name}] {' '.join(cmd)}", "ok": False, "rc": -1,
                                  "output": f"采集异常: {e}"})
            nd.ok(1, note=f"{len(diag_items)}项采集完成")

            # 3) AI 基于采集数据给分层优化建议(仅建议, 绝不执行; AI失败不影响诊断结论)
            nd.run(2)
            try:
                digest = "\n".join(f"$ {s['cmd']}\n{s.get('output','')[:600]}" for s in steps)
                adv = think("以下是对本机的只读性能诊断采集数据(磁盘/负载/内存/进程/AI引擎)。"
                            "请给出分层优化建议: ①紧急且零风险的操作 ②需要确认后执行的操作 "
                            "③长期建议。每条建议说明预期收益。注意: 你只输出建议文本, "
                            "不要输出任何shell命令让用户执行, 清理/改配置类操作必须由用户明确授权。\n"
                            f"诊断数据:\n{digest[:3500]}",
                            flow_id=flow_id or "act_diagnose_advice")
                advice = (adv.get("response") or "").strip() if adv.get("success") else ""
                if advice:
                    nd.ok(2, note="仅建议, 未执行变更")
                    result["advice"] = advice[:1800]
                    steps.append({"cmd": "[AI优化建议] 仅建议, 未执行任何变更", "ok": True, "rc": 0,
                                  "output": result["advice"]})
                else:
                    nd.skip(2, note="AI建议不可用(不影响诊断)")
            except Exception:
                nd.skip(2, note="AI建议异常(不影响诊断)")

            result["success"] = True  # 只读诊断: 采集完成即成功, 单项异常已在steps中体现
            return result
        finally:
            nd.close()

    if intent == "feature_expand":
        # 功能拓展分析: 全程只读盘点系统现状 + AI给拓展建议; 不做任何代码修改(须走 ai code/fix)
        if _CLI:
            _banner("🧭 系统功能拓展分析", "全程只读盘点(零副作用)", "AI给扩充建议")
        nd = _Nodes("功能拓展分析", [("系统现状只读盘点 (引擎/AI集/模型/员工)", 30, "feat_scan"),
                                    ("AI 生成功能拓展建议", 60, "feat_ai")])
        nd.start()
        try:
            if dry_run:
                nd.skip_pending("dry-run 预览")
                plan("[只读盘点] 统计 engines/ 与 ai_engines/ 引擎文件",
                     "[只读盘点] 网关健康 + Ollama本地模型 + 融合引擎",
                     "[只读盘点] app.db 关键表计数(AI员工/daemon/路由)",
                     "[AI] 基于现状生成功能拓展建议(仅建议, 不改代码)")
                return result

            # 1) 系统现状只读盘点
            nd.run(0)
            try:
                # 1a) 引擎文件计数(本地盘, 只读列举)
                _ae_dir = os.path.dirname(os.path.abspath(__file__))
                _en_dir = os.path.join(os.path.dirname(_ae_dir), "engines")
                ae_mods = sorted(f for f in os.listdir(_ae_dir)
                                 if f.endswith(".py") and "bak" not in f and not f.endswith(".tmp"))
                en_mods = sorted(f for f in os.listdir(_en_dir)
                                 if f.endswith(".py") and "bak" not in f and not f.endswith(".tmp")) \
                    if os.path.isdir(_en_dir) else []
                steps.append({"cmd": "[盘点] 引擎模块计数", "ok": True, "rc": 0,
                              "output": f"ai_engines/: {len(ae_mods)}个模块\nengines/: {len(en_mods)}个模块"})
            except Exception as e:
                steps.append({"cmd": "[盘点] 引擎模块计数", "ok": False, "rc": -1, "output": f"盘点异常: {e}"})
            try:
                h = health()
                models = (h.get("local_ollama") or {}).get("models", [])
                fusion = (h.get("local_ollama") or {}).get("fusion_engines", [])
                steps.append({"cmd": "[盘点] 本地模型/网关", "ok": True, "rc": 0,
                              "output": f"本地模型: {', '.join(models) or '(无)'}\n"
                                        f"融合引擎: {', '.join(fusion) or '(空, 未注册外部AI集)'}\n"
                                        f"云端兜底: {'开启(应急)' if h.get('cloud_volcengine', {}).get('fallback_enabled') else '关闭(纯本地零token)'}\n"
                                        f"本地命中率: {h.get('local_hit_rate', 1.0):.4%} (本进程)"})
            except Exception as e:
                steps.append({"cmd": "[盘点] 本地模型/网关", "ok": False, "rc": -1, "output": f"健康检查异常: {e}"})
            # 1b) 关键表计数(SQLite只读, 表不存在逐项跳过)
            try:
                import sqlite3
                _app_db = os.path.join(_ae_dir, "app.db")
                conn = sqlite3.connect(_app_db, timeout=5)
                counts = {}
                for label, table in [("AI员工", "ai_employees"),
                                     ("EigenFlux注册", "eigenflux_registrations"),
                                     ("daemon注册", "mt_daemon_registry"),
                                     ("本地推理日志", "mt_local_ai_inference_log")]:
                    try:
                        cur = conn.execute(f"SELECT COUNT(*) FROM {table}")
                        counts[label] = cur.fetchone()[0]
                    except Exception:
                        counts[label] = "N/A"
                conn.close()
                steps.append({"cmd": "[盘点] app.db 关键表计数(只读)", "ok": True, "rc": 0,
                              "output": "\n".join(f"{k}: {v}" for k, v in counts.items())})
            except Exception as e:
                steps.append({"cmd": "[盘点] app.db 关键表计数(只读)", "ok": False, "rc": -1,
                              "output": f"数据库盘点异常: {e}"})
            nd.ok(0)

            # 2) AI 基于现状给功能拓展建议(仅建议, 绝不改代码; AI失败不影响盘点结论)
            nd.run(1)
            try:
                digest = "\n".join(f"$ {s['cmd']}\n{s.get('output','')[:800]}" for s in steps)
                adv = think("以下是MTSCOS系统现状的只读盘点(引擎/本地模型/AI员工/daemon)。"
                            "请给出系统功能拓展建议: ①可优先本地落地的新AI功能/新daemon(本地推理优先, 零token) "
                            "②其他AI集/引擎与本地模型的集成方向 ③教育/运维/安全方向可新增的页面或自动化能力。"
                            "每条建议标注预期价值与依赖。注意: 你只输出建议文本, 不要输出代码或shell命令, "
                            "任何代码修改必须由用户另行明确授权(走 ai code/fix)。\n"
                            f"盘点数据:\n{digest[:4000]}",
                            flow_id=flow_id or "act_feature_expand_advice")
                advice = (adv.get("response") or "").strip() if adv.get("success") else ""
                if advice:
                    nd.ok(1, note="仅建议, 未修改代码")
                    result["advice"] = advice[:2000]
                    steps.append({"cmd": "[AI拓展建议] 仅建议, 未做任何代码修改", "ok": True, "rc": 0,
                                  "output": result["advice"]})
                else:
                    nd.skip(1, note="AI建议不可用(盘点结论已给出)")
            except Exception:
                nd.skip(1, note="AI建议异常(盘点结论已给出)")

            result["success"] = True  # 只读盘点: 盘点完成即成功
            return result
        finally:
            nd.close()

    if intent == "daemon_status":
        # daemon运行状态: 只读检测PID文件+进程存活+注册表; 绝不启停任何进程
        if _CLI:
            _banner("📡 自动化daemon状态", "全程只读(零副作用)", "不启停进程")
        nd = _Nodes("daemon状态查看", [("PID文件存活检测", 10, "daemon_pid"),
                                      ("daemon注册表(只读查库)", 12, "daemon_db")])
        nd.start()
        try:
            if dry_run:
                nd.skip_pending("dry-run 预览")
                plan("[只读] 扫描 _runtime/pids/*.pid 并 os.kill(pid,0) 存活检测",
                     "[只读] 查询 mt_daemon_registry 注册表状态")
                return result

            _ae_dir = os.path.dirname(os.path.abspath(__file__))
            runtime_dirs = [os.path.join(repo_root, "_runtime"),
                            os.path.join(repo_root, "flask-app", "_runtime"),
                            os.path.join(_ae_dir, "..", "_runtime")]
            nd.run(0)
            alive, dead, seen_pids = [], [], set()
            for rd in runtime_dirs:
                pid_dir = os.path.join(rd, "pids")
                if not os.path.isdir(pid_dir):
                    continue
                for pf in sorted(os.listdir(pid_dir)):
                    if not pf.endswith(".pid"):
                        continue
                    name = pf[:-4]
                    try:
                        with open(os.path.join(pid_dir, pf), "r") as f:
                            pid = int(f.read().strip())
                    except Exception:
                        dead.append(f"{name}(PID文件不可读)")
                        continue
                    if pid in seen_pids:
                        continue
                    seen_pids.add(pid)
                    try:
                        os.kill(pid, 0)
                        alive.append(f"{name}(pid={pid})")
                    except OSError:
                        dead.append(f"{name}(pid={pid},进程不存在)")
            steps.append({"cmd": "[只读] PID文件存活检测", "ok": True, "rc": 0,
                          "output": (f"存活 {len(alive)} 个:\n" + "\n".join(alive) +
                                     (f"\n\n已退出/残留PID {len(dead)} 个:\n" + "\n".join(dead) if dead else ""))
                          if alive or dead else "(未发现PID文件, daemon可能未通过PID机制启动)"})
            nd.ok(0, note=f"存活{len(alive)}/残留{len(dead)}")

            nd.run(1)
            try:
                import sqlite3
                _app_db = os.path.join(_ae_dir, "app.db")
                conn = sqlite3.connect(_app_db, timeout=5)
                cols = [r[1] for r in conn.execute("PRAGMA table_info(mt_daemon_registry)")]
                out_lines = [f"mt_daemon_registry 列: {', '.join(cols)[:200]}"]
                try:
                    total = conn.execute("SELECT COUNT(*) FROM mt_daemon_registry").fetchone()[0]
                    out_lines.append(f"注册daemon总数: {total}")
                except Exception as e:
                    out_lines.append(f"计数失败: {e}")
                # 状态列容错探测
                for st_col in ("current_state", "status", "state", "daemon_status"):
                    if st_col in cols:
                        try:
                            for row in conn.execute(f"SELECT {st_col}, COUNT(*) FROM mt_daemon_registry GROUP BY {st_col}"):
                                out_lines.append(f"  {st_col}={row[0]}: {row[1]}")
                        except Exception:
                            pass
                        break
                conn.close()
                steps.append({"cmd": "[只读] daemon注册表", "ok": True, "rc": 0,
                              "output": "\n".join(out_lines)})
            except Exception as e:
                steps.append({"cmd": "[只读] daemon注册表", "ok": False, "rc": -1,
                              "output": f"注册表查询异常: {e}"})
            nd.ok(1)
            result["success"] = True
            return result
        finally:
            nd.close()

    if intent == "ai_workforce":
        # AI队伍统计: 只读查库; 绝不新增/修改/删除员工
        if _CLI:
            _banner("👥 AI员工/EigenFlux 队伍统计", "全程只读查库(零副作用)", "零token")
        nd = _Nodes("AI队伍统计", [("关键表计数(只读)", 10, "workforce_db")])
        nd.start()
        try:
            if dry_run:
                nd.skip_pending("dry-run 预览")
                plan("[只读] 查询 ai_employees / eigenflux_registrations / mt_ai_auto_hire_log 等表计数")
                return result
            nd.run(0)
            import sqlite3
            _ae_dir = os.path.dirname(os.path.abspath(__file__))
            _flask_dir = os.path.dirname(_ae_dir)
            # 员工数据分散在多个库, 逐库如实计数(表/库不存在逐项跳过)
            db_targets = [
                (os.path.join(_ae_dir, "app.db"), "ai_engines/app.db",
                 [("AI员工", "ai_employees"), ("自动雇佣记录", "mt_ai_auto_hire_log"),
                  ("EigenFlux邀请", "mt_ai_eigenflux_invite_log"), ("本地推理日志", "mt_local_ai_inference_log")]),
                (os.path.join(_flask_dir, "engines", "app.db"), "engines/app.db",
                 [("AI员工", "ai_employees")]),
                (os.path.join(_flask_dir, "core", "app.db"), "core/app.db",
                 [("AI员工(mtscos)", "mtscos_ai_employees")]),
            ]
            lines = []
            for db_path, db_label, table_pairs in db_targets:
                if not os.path.isfile(db_path):
                    continue
                try:
                    conn = sqlite3.connect(db_path, timeout=5)
                    for label, table in table_pairs:
                        try:
                            n = conn.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]
                            lines.append(f"[{db_label}] {label}: {n}")
                        except Exception:
                            pass  # 表不存在即跳过, 不猜测不编造
                    conn.close()
                except Exception as e:
                    lines.append(f"[{db_label}] 读取异常: {str(e)[:60]}")
            steps.append({"cmd": "[只读] AI队伍关键表计数(跨库汇总)", "ok": True, "rc": 0,
                          "output": "\n".join(lines) if lines else "(候选库均未找到员工表)"})
            nd.ok(0)
            result["success"] = True
            return result
        finally:
            nd.close()

    if intent == "view_logs":
        # 系统日志: 只读tail最新日志; 绝不删除/修改/清空日志
        if _CLI:
            _banner("📄 系统最近日志", "全程只读tail(零副作用)", "不修改日志")
        nd = _Nodes("系统日志查看", [("定位最新日志文件", 6, "logs_find"),
                                    ("tail最新3个日志(各20行)", 15, "logs_tail")])
        nd.start()
        try:
            if dry_run:
                nd.skip_pending("dry-run 预览")
                plan("[只读] 定位 _runtime/logs 下最新3个 .log 文件",
                     "[只读] tail -n 20 读取末尾内容")
                return result
            nd.run(0)
            _ae_dir = os.path.dirname(os.path.abspath(__file__))
            log_dirs = [os.path.join(repo_root, "_runtime", "logs"),
                        os.path.join(repo_root, "flask-app", "_runtime", "logs"),
                        os.path.join(_ae_dir, "..", "_runtime", "logs")]
            log_files = []
            for ld in log_dirs:
                if os.path.isdir(ld):
                    try:
                        for fn in os.listdir(ld):
                            if fn.endswith(".log"):
                                fp = os.path.join(ld, fn)
                                log_files.append((os.path.getmtime(fp), fp))
                    except OSError:
                        continue
            log_files = sorted(set(log_files), reverse=True)[:3]
            nd.ok(0, note=f"{len(log_files)}个最新日志")
            nd.run(1)
            if not log_files:
                steps.append({"cmd": "[只读] 日志目录", "ok": True, "rc": 0,
                              "output": "(未找到 _runtime/logs/*.log)"})
            for _mt, fp in log_files:
                r = _run_cmd(["tail", "-n", "20", fp], repo_root, timeout=20)
                r["cmd"] = f"[只读] tail -n 20 {os.path.basename(fp)}"
                steps.append(r)
            nd.ok(1)
            result["success"] = True
            return result
        finally:
            nd.close()

    if intent == "dev_audit":
        # 功能区体检: 只读盘点某功能模块的前端/路由/中间件, AI出缺口报告+任务清单; 绝不改代码
        if _CLI:
            _banner("🩺 功能区体检 · 缺口分析", "全程只读盘点(零副作用)", "只出清单, 落地走 ai act 代码修复")
        nd = _Nodes("功能区体检", [("识别目标模块 + 只读盘点文件", 25, "audit_scan"),
                                  ("AI 生成缺口报告与任务清单", 60, "audit_ai")])
        nd.start()
        try:
            if dry_run:
                nd.skip_pending("dry-run 预览")
                plan("[只读] 识别目标模块关键词(学生/用户/考试/教育...)",
                     "[只读] 盘点 templates/ 前端页面 + routes/ 路由 + app/middlewares 中间件",
                     "[AI] 输出缺口报告与可落地任务清单(每项对应 ai act 修复指令, 不改代码)")
                return result

            # 1) 识别目标模块 (中文关键词 → 文件匹配词)
            nd.run(0)
            _ae_dir = os.path.dirname(os.path.abspath(__file__))
            _flask_dir = os.path.dirname(_ae_dir)
            _MODULE_MAP = [
                ("学生/学员", ["学生", "student"]),
                ("用户/账号", ["用户", "账号", "user", "account"]),
                ("管理员/后台", ["管理员", "后台", "admin"]),
                ("考试/题库", ["考试", "题库", "exam", "question"]),
                ("教育/教学", ["教育", "教学", "课程", "edu", "learn", "k12"]),
            ]
            targets = [name for name, kws in _MODULE_MAP
                       if any(kw.lower() in request.lower() for kw in kws)]
            target_label = "、".join(targets) if targets else "全局(未指定具体模块)"
            # 该模块对应的文件匹配词(用于过滤模板/路由)
            match_kws = []
            for name, kws in _MODULE_MAP:
                if not targets or name in targets:
                    match_kws += kws
            steps.append({"cmd": "[只读] 目标模块识别", "ok": True, "rc": 0,
                          "output": f"目标: {target_label}\n匹配关键词: {', '.join(match_kws)[:120]}"})

            # 2) 只读盘点 (逐类 try/except, 缺数据不编造)
            import re as _re
            def _count(pattern, text):
                return len(_re.findall(pattern, text))

            # 2a) 前端模板
            tpl_dir = os.path.join(_flask_dir, "templates")
            tpl_files = []
            try:
                for r0, _d, fns in os.walk(tpl_dir):
                    for fn in fns:
                        if fn.endswith((".html", ".jinja", ".jinja2")):
                            rel = os.path.relpath(os.path.join(r0, fn), tpl_dir)
                            low = (rel + " " + fn).lower()
                            if not targets or any(k.lower() in low for k in match_kws):
                                tpl_files.append(rel)
            except Exception as e:
                steps.append({"cmd": "[只读] 前端模板盘点", "ok": False, "rc": -1, "output": f"模板扫描异常: {e}"})
            steps.append({"cmd": "[只读] 前端模板 (templates/)", "ok": True, "rc": 0,
                          "output": (f"命中 {len(tpl_files)} 个:\n" + "\n".join(sorted(tpl_files)[:25]))
                          if tpl_files else "(未命中该模块模板)"})

            # 2b) 后端路由 + 路由数 + 权限装饰器覆盖
            routes_dir = os.path.join(_flask_dir, "routes")
            route_summary = []
            total_routes, total_protected = 0, 0
            try:
                for fn in sorted(os.listdir(routes_dir)):
                    if not fn.endswith(".py") or "bak" in fn:
                        continue
                    fp = os.path.join(routes_dir, fn)
                    try:
                        with open(fp, "r", encoding="utf-8", errors="replace") as f:
                            src = f.read()
                    except Exception:
                        continue
                    low_src = (fn + " " + src[:3000]).lower()
                    if targets and not any(k.lower() in low_src for k in match_kws):
                        continue
                    n_route = _count(r"@[\w_]+\.route\(", src)
                    n_prot = _count(r"@(system_container|require_auth|require_login|login_required|admin_required|permission_required)", src)
                    total_routes += n_route
                    total_protected += min(n_prot, n_route)
                    route_summary.append(f"{fn}: 路由{n_route} 权限装饰器{n_prot}")
            except Exception as e:
                steps.append({"cmd": "[只读] 后端路由盘点", "ok": False, "rc": -1, "output": f"路由扫描异常: {e}"})
            steps.append({"cmd": "[只读] 后端路由 (routes/)", "ok": True, "rc": 0,
                          "output": (f"相关文件 {len(route_summary)} 个, 路由合计 {total_routes}, "
                                     f"带权限装饰器 {total_protected}\n" + "\n".join(route_summary[:20]))
                          if route_summary else "(未命中该模块路由文件)"})

            # 2c) 中间件清单
            mw_dir = os.path.join(_flask_dir, "app", "middlewares")
            mw_files = []
            try:
                mw_files = sorted(f for f in os.listdir(mw_dir)
                                  if f.endswith(".py") and f != "__init__.py" and "bak" not in f)
            except Exception:
                pass
            steps.append({"cmd": "[只读] 中间件 (app/middlewares/)", "ok": bool(mw_files), "rc": 0,
                          "output": ("\n".join(mw_files) if mw_files else "(app/middlewares 不存在)")})
            nd.ok(0, note=f"模板{len(tpl_files)} 路由{total_routes} 中间件{len(mw_files)}")

            # 3) AI 缺口报告 + 任务清单 (仅建议, 不改代码)
            nd.run(1)
            try:
                digest = "\n".join(f"$ {s['cmd']}\n{s.get('output','')[:900]}" for s in steps)
                adv = think("你是MTSCOS系统架构审查员。以下是对功能模块的【只读盘点】(前端模板/后端路由/权限装饰器/中间件)。"
                            "用户想『完善该模块的功能任务、前端显示、后端数据安全与中间件』。请输出:\n"
                            "①缺口诊断(前端显示/后端接口/数据安全/中间件/权限 各维度, 基于盘点数据, 不要编造未看到的文件)\n"
                            "②按优先级排列的任务清单(P0安全/权限 → P1功能缺失 → P2前端体验), 每条注明涉及的文件类型与验收标准\n"
                            "③每条任务给出可直接执行的 ai act 修复指令文案(如: ai act \"修复 engines/x.py 的yyy\", 具体可落地)。\n"
                            "严格只输出报告文本, 不要输出代码/shell, 你本次不修改任何文件(代码落地由用户逐条 ai act 修复指令授权)。\n"
                            f"盘点数据:\n{digest[:4500]}",
                            flow_id=flow_id or "act_dev_audit")
                report = (adv.get("response") or "").strip() if adv.get("success") else ""
                if report:
                    nd.ok(1, note="仅报告, 未修改代码")
                    result["report"] = report[:3000]
                    steps.append({"cmd": "[AI] 缺口报告+任务清单(只读, 落地走 ai act 修复指令)", "ok": True, "rc": 0,
                                  "output": result["report"]})
                else:
                    nd.skip(1, note="AI报告不可用(盘点数据已给出)")
            except Exception:
                nd.skip(1, note="AI报告异常(盘点数据已给出)")

            result["success"] = True
            result["target_module"] = target_label
            return result
        finally:
            nd.close()

    # ===== 以下为 git 仓库类动作 =====
    if not os.path.isdir(os.path.join(repo_root, ".git")):
        return {"success": False, "kind": "execute", "error": f"不是git仓库: {repo_root}"}

    if _CLI:
        _intent_name = {"git_sync": "同步 GitHub", "git_pull": "拉取远端代码",
                        "git_status": "查看仓库状态", "run_tests": "运行测试"}.get(intent, intent)
        _banner(f"⚡ 真实执行 · {_intent_name}", "本地操作(白名单)", "零token")
        _stage(f"仓库: {repo_root}")
        _stage(f"模式: {'📝 dry-run 预览' if dry_run else '✅ 真实执行'}")

    # git 类动作节点清单: 每个意图一组节点, 倒计时+预计完成
    _git_node_spec = {
        "git_status": [("查看仓库状态 (git status)", 15, "git_status"),
                       ("最近提交记录 (git log)", 10, "git_status")],
        "git_pull":   [("拉取远端代码 (ff-only)", 60, "git_pull")],
        "run_tests":  [("运行 pytest 测试", 120, "pytest")],
        "git_sync":   [("检查仓库变更", 15, "sync_scan"),
                       ("AI 生成中文提交信息", 40, "sync_msg"),
                       ("暂存变更 (排除.bak)", 8, "sync_git"),
                       ("创建提交", 10, "sync_git"),
                       ("推送到 GitHub", 45, "sync_push")],
    }
    nd = _Nodes(f"真实执行 · {intent}", _git_node_spec.get(intent, [("执行白名单动作", 30, "")]))
    nd.start()
    try:
        if intent == "git_status":
            if dry_run:
                nd.skip_pending("dry-run 预览")
                plan("git status -sb")
                return result
            nd.run(0)
            steps.append(_run_cmd(["git", "status", "-sb"], repo_root, timeout=600))
            if steps[-1]["ok"]:
                nd.ok(0)
            else:
                nd.err(0)
                nd.skip_pending("前序步骤失败")
            nd.run(1)
            steps.append(_run_cmd(["git", "log", "--oneline", "-3"], repo_root))
            if steps[-1]["ok"]:
                nd.ok(1)
            else:
                nd.err(1)
            result["success"] = all(s["ok"] for s in steps)
            return result

        if intent == "git_pull":
            if dry_run:
                nd.skip_pending("dry-run 预览")
                plan("git pull --ff-only")
                return result
            nd.run(0)
            steps.append(_run_cmd(["git", "pull", "--ff-only"], repo_root, timeout=300))
            result["success"] = steps[-1]["ok"]
            if steps[-1]["ok"]:
                nd.ok(0)
            else:
                nd.err(0, note=(steps[-1]["output"] or "拉取失败")[:60])
            return result

        if intent == "run_tests":
            tests_dir = os.path.join(repo_root, "flask-app")
            cmd = ["python3", "-m", "pytest", "-x", "-q", "--co", "-q"] \
                  if dry_run else ["python3", "-m", "pytest", "-x", "-q"]
            if dry_run:
                nd.skip_pending("dry-run 预览")
                plan(" ".join(cmd) + "  (cwd: flask-app)")
                return result
            nd.run(0)
            steps.append(_run_cmd(cmd, tests_dir, timeout=600))
            result["success"] = steps[-1]["ok"]
            if steps[-1]["ok"]:
                nd.ok(0)
            else:
                nd.err(0, note="测试未全部通过")
            return result

        # intent == "git_sync"
        nd.run(0)
        st = _run_cmd(["git", "status", "--porcelain"], repo_root, timeout=600)
        if not st["ok"]:
            nd.err(0, note=(st["output"] or "状态检查失败")[:60])
            nd.skip_pending("前序步骤失败")
            steps.append(st)
            result["error"] = st["output"][:300]
            return result
        dirty_lines = [l for l in st["output"].splitlines() if l.strip()]
        dirty_lines = [l for l in dirty_lines if ".bak" not in l]  # 忽略AI备份文件
        if not dirty_lines:
            # 工作区干净 → 直接推送未推送提交
            nd.ok(0, note="工作区干净")
            steps.append({"cmd": "git status --porcelain", "ok": True, "rc": 0,
                          "output": "工作区干净, 无新变更"})
            ahead = _run_cmd(["git", "rev-list", "--count", "@{upstream}..HEAD"], repo_root)
            if ahead["ok"] and ahead["output"].strip() == "0":
                nd.skip(1, note="无需提交")
                nd.skip(2, note="无需提交")
                nd.skip(3, note="无需提交")
                nd.skip(4, note="远端已是最新")
                steps.append({"cmd": "git rev-list --count @{upstream}..HEAD", "ok": True,
                              "rc": 0, "output": "远端已是最新, 无需推送"})
                result["success"] = True
                return result
            nd.skip(1, note="无变更, 跳过")
            nd.skip(2, note="无变更, 跳过")
            nd.skip(3, note="无变更, 跳过")
            if dry_run:
                nd.skip(4, note="dry-run 预览")
                plan("git push -u MTSCOS HEAD")
                return result
            nd.run(4)
            steps.append(_run_cmd(["git", "push", "-u", "MTSCOS", "HEAD"], repo_root, timeout=300))
            result["success"] = steps[-1]["ok"]
            if steps[-1]["ok"]:
                nd.ok(4)
            else:
                nd.err(4, note=(steps[-1]["output"] or "推送失败")[:60])
            return result

        # 有变更: AI 生成中文提交信息 (本地, 零token)
        nd.ok(0, note=f"{len(dirty_lines)}个变更文件")
        summary = "\n".join(dirty_lines[:40])
        if _CLI:
            _stage(f"检测到 \033[33m{len(dirty_lines)}\033[0m 个变更文件, AI 生成提交信息...")
        nd.run(1)
        with _Spin("AI 生成中文提交信息"):
            msg_result = chat(
                f"根据以下git变更摘要, 生成一条简洁的中文git提交信息(50字内, 直接给内容, 不要引号和解释):\n{summary}",
                flow_id=flow_id)
        commit_msg = msg_result.get("response", "").strip().splitlines()[0][:60] \
            if msg_result.get("success") else ""
        commit_msg = commit_msg.strip("`\"' ") or \
            f"auto: 本地AI自动提交 {datetime.datetime.now().strftime('%Y-%m-%d %H:%M')}"
        result["commit_message"] = commit_msg
        nd.ok(1, note=commit_msg[:26])
        if _CLI:
            _stage(f"提交信息: \033[1;32m{commit_msg}\033[0m")

        if dry_run:
            nd.skip(2, note="dry-run 预览")
            nd.skip(3, note="dry-run 预览")
            nd.skip(4, note="dry-run 预览")
            plan("git add -A (不含 *.bak)",
                 f"git commit -m {shlex.quote(commit_msg)}",
                 "git push -u MTSCOS HEAD")
            steps.append({"cmd": f"待提交 {len(dirty_lines)} 个文件",
                          "ok": None, "output": summary[:800]})
            result["success"] = True
            return result

        # add: 显式加入非.bak变更文件, 避免把备份带进仓库
        nd.run(2)
        to_add = ["git", "add", "-A", "--", ":!*.bak"]
        steps.append(_run_cmd(to_add, repo_root))
        if not steps[-1]["ok"]:
            nd.err(2, note=(steps[-1]["output"] or "暂存失败")[:60])
            nd.skip_pending("前序步骤失败")
            result["error"] = steps[-1]["output"][:300]
            return result
        nd.ok(2)

        nd.run(3)
        steps.append(_run_cmd(["git", "commit", "-m", commit_msg], repo_root))
        if not steps[-1]["ok"]:
            nd.err(3, note=(steps[-1]["output"] or "提交失败")[:60])
            nd.skip_pending("前序步骤失败")
            result["error"] = steps[-1]["output"][:300]
            return result
        nd.ok(3)

        nd.run(4)
        steps.append(_run_cmd(["git", "push", "-u", "MTSCOS", "HEAD"], repo_root, timeout=300))
        result["success"] = steps[-1]["ok"]
        if steps[-1]["ok"]:
            nd.ok(4)
        else:
            nd.err(4, note=(steps[-1]["output"] or "推送失败")[:60])
            result["error"] = steps[-1]["output"][:300]
        return result
    finally:
        nd.close()


def _parse_nested_steps(request: str) -> list:
    """把 act 请求解析为有序步骤, 支持"指令里套指令"的递归写法。

    返回步骤元组列表:
      ("ai",  sub, sub_text)  — 显式 'ai <子命令> <内容>' 片段, 交给对应网关函数真实执行
      ("op",  intent, seg)    — 自由文本里的白名单运维动作(daemon状态/看日志/同步等)

    示例:
      '看下daemon状态, 然后 ai fix 完善 engines/x.py 的归档'
        → [("op","daemon_status",...), ("ai","fix","完善 engines/x.py 的归档")]
      'ai chat 你好'  → [("ai","chat","你好")]
      'ai fix A 然后 ai chat B' → [("ai","fix","A 然后"), ("ai","chat","B")]
    """
    markers = list(_NESTED_CMD_RE.finditer(request))
    if not markers:
        # 无嵌套指令: 退化为整段白名单动作识别
        return [("op", i, request) for i in _detect_operation_intents(request)]

    steps: list = []

    def _emit_ops(seg: str):
        for intent in _detect_operation_intents(seg):
            steps.append(("op", intent, seg))

    _emit_ops(request[:markers[0].start()])  # 首个嵌套指令前的自由文本
    for i, mk in enumerate(markers):
        sub = mk.group(1).lower()
        seg_end = markers[i + 1].start() if i + 1 < len(markers) else len(request)
        sub_text = request[mk.end():seg_end]
        sub_text = _clean_nested_text(sub_text)
        steps.append(("ai", sub, sub_text))
    return steps


def _clean_nested_text(text: str) -> str:
    """清理嵌套指令内容: 去首尾空白与连接词(然后/再/接着/逗号/冒号等)。"""
    text = text.strip().strip("，,、；;：:").strip()
    leads = ("然后", "接着", "之后", "最后", "再", "并")
    tails = ("然后", "接着", "之后", "最后", "再", "并", "，", ",", "、", "；", ";")
    changed = True
    while changed:
        changed = False
        for lead in leads:
            if text.startswith(lead):
                text = text[len(lead):].strip().strip("，,、；;：:").strip()
                changed = True
        for tail in tails:
            if text.endswith(tail):
                text = text[:-len(tail)].strip().strip("，,、；;：:").strip()
                changed = True
    return text


def _dispatch_nested(sub: str, text: str, repo_root: str, dry_run: bool,
                     flow_id: Optional[str], depth: int) -> Dict[str, Any]:
    """递归分发: 把 'ai <sub> <text>' 真实交给对应网关函数执行(非模拟)。

    - fix/optimize: 真实改代码并落盘(auto_fix 自带写前校验+原子替换+回滚), dry_run 时仅预览
    - code/chat/think: 真实走本地模型产出
    - act: 递归进入 act(), 深度 +1, 受 _MAX_ACT_DEPTH 护栏限制
    - run/sync: 真实执行白名单 shell
    - analyze/compile/review/classify: 真实离线分析
    """
    sub = (sub or "").lower()
    if sub == "fix":
        # project_root 传 "" 让 auto_fix 自动定位 flask-app, 显式路径相对 flask-app 解析
        return auto_fix(text, "", dry_run, flow_id)
    if sub == "optimize":
        return optimize_file(text, write_back=not dry_run, flow_id=flow_id)
    if sub == "code":
        return code(text, flow_id=flow_id)
    if sub == "chat":
        return chat(text, flow_id=flow_id)
    if sub == "think":
        return think(text, flow_id=flow_id)
    if sub == "act":
        if depth >= _MAX_ACT_DEPTH:
            return {"success": False, "kind": "act",
                    "error": f"递归深度超过上限({_MAX_ACT_DEPTH}), 已停止嵌套 'ai act' 以防无限递归"}
        return act(text, repo_root, dry_run, flow_id, _depth=depth + 1)
    if sub == "run":
        return execute_task(text, repo_root, dry_run, flow_id)
    if sub == "sync":
        return execute_task("同步GitHub", repo_root, dry_run, flow_id)
    if sub == "analyze":
        return analyze(text, flow_id)
    if sub == "compile":
        return compile_check(text, flow_id)
    if sub == "review":
        return review(text, flow_id)
    if sub == "classify":
        return classify(text, flow_id=flow_id)
    return {"success": False, "kind": "act",
            "error": f"不支持的嵌套子命令: ai {sub}",
            "hint": f"可用: ai {'/'.join(sorted(_NESTED_SUBS))}"}


def _inject_nested_step(r: Dict[str, Any], sub: str, sub_text: str, dry_run: bool):
    """把嵌套 ai 子命令的真实产出落为一条 step 记录(供看板展示/落库追溯, 非模拟)。"""
    ok = bool(r.get("success"))
    if sub in ("chat", "think", "code"):
        payload = str(r.get("response", "") or r.get("error", "")).strip()
    elif sub == "fix":
        if dry_run:
            payload = "(dry-run 预览, 未落盘) " + json.dumps(
                r.get("verification", {}), ensure_ascii=False)[:200]
        else:
            files = r.get("actually_modified_files") or [
                m.get("file") for m in r.get("modified", []) if m.get("success")]
            payload = "真实落盘文件: " + ", ".join(f for f in files if f) if files else \
                      (r.get("error") or "无文件改动")
    elif sub in ("analyze", "compile", "review", "classify"):
        payload = str(r.get("response", "") or r.get("summary", "") or
                      r.get("error", "")).strip()
    elif sub == "act":
        payload = f"递归完成, 执行: {', '.join(r.get('executed', []) or [])}"
    else:  # run / sync / optimize
        existing = r.get("steps") or []
        if existing:
            return  # 已有真实 shell 步骤, 不重复注入
        payload = str(r.get("error", "") or "已执行")
    steps = r.setdefault("steps", [])
    steps.append({"cmd": f"ai {sub} {sub_text[:40]}".strip(),
                  "ok": ok, "rc": 0 if ok else 1,
                  "output": payload[:500]})


def _run_nested_act(request: str, repo_root: str, dry_run: bool,
                    flow_id: Optional[str], depth: int) -> Dict[str, Any]:
    """递归执行路径: 请求中含 'ai <子命令>' 嵌套指令时, 按解析出的有序步骤真实执行。

    - ("ai", sub, text) → _dispatch_nested 真实调用对应网关函数(fix真落盘/chat真回答/git真执行)
    - ("op", intent, seg) → execute_task 白名单运维动作
    - 失败即停; dry_run=True 时所有副作用动作仅预览
    """
    steps = _parse_nested_steps(request)
    nested = [s for s in steps if s[0] == "ai"]
    if _CLI:
        chain = " → ".join(
            (f"ai {s[1]}" if s[0] == "ai" else s[1]) for s in steps)
        _stage(f"递归指令链: \033[33m{chain}\033[0m  (深度 {depth})")
        _stage(f"模式: {'📝 dry-run 预览' if dry_run else '✅ 真实执行(嵌套指令真实落实)'}")

    def _label(s):
        if s[0] == "ai":
            return f"ai {s[1]} {s[2][:18]}"
        return OPERATION_INTENTS[s[1]][2]

    nd = _Nodes("ai act 递归动作序列", [(_label(s), 45, f"s{i}") for i, s in enumerate(steps)])
    nd.start()
    sub_results = []
    try:
        for idx, step in enumerate(steps):
            nd.run(idx)
            kind = step[0]
            if kind == "ai":
                _, sub, sub_text = step
                # 空文本嵌套指令(常见于 'ai act ai act xxx' 叠写时外层 act 无内容): 跳过不报错
                if not sub_text.strip():
                    nd.ok(idx, note="空指令跳过")
                    continue
                if _CLI:
                    _stage(f"[{idx + 1}/{len(steps)}] 递归分发 \033[36mai {sub}\033[0m · {sub_text[:40]}")
                r = _dispatch_nested(sub, sub_text, repo_root, dry_run,
                                     flow_id or f"act_nested_{sub}", depth)
                r["intent"] = f"ai_{sub}"
                # 注入真实产出步骤: 嵌套 ai 子命令本身不带 shell steps, 这里把其真实结果
                # (chat回答/fix落盘文件/分析结论) 落为一条 step, 供看板展示与落库追溯(非模拟)
                _inject_nested_step(r, sub, sub_text, dry_run)
            else:
                _, intent, seg = step
                canonical = OPERATION_INTENTS[intent][2]
                if _CLI:
                    _stage(f"[{idx + 1}/{len(steps)}] 执行动作 \033[36m{intent}\033[0m · {canonical}")
                _exec_text = seg if intent in ("dev_audit", "code_fix") else canonical
                r = execute_task(_exec_text, repo_root, dry_run,
                                 flow_id or f"act_{intent}")
                r["intent"] = intent
            sub_results.append(r)
            if r.get("success"):
                nd.ok(idx)
            else:
                nd.err(idx, note=(r.get("error") or "执行失败")[:60])
                nd.skip_pending("前序动作失败")
                break  # 失败即停
    finally:
        nd.close()

    flat_steps: list = []
    for r in sub_results:
        flat_steps.extend(r.get("steps", []))

    out: Dict[str, Any] = {
        "success": all(r.get("success") for r in sub_results),
        "kind": "act",
        "request": request,
        "routed_by": "nested_recursive",
        "recursion_depth": depth,
        "nested_commands": [f"ai {s[1]}" for s in nested],
        "intents": [r.get("intent") for r in sub_results],
        "executed": [r.get("intent") for r in sub_results],
        "dry_run": dry_run,
        "steps": flat_steps,
        "results": sub_results,
    }
    if not out["success"]:
        for r in sub_results:
            if not r.get("success"):
                out["error"] = f"[{r.get('intent', '')}] {r.get('error', '执行失败')}"[:400]
                if r.get("hint"):
                    out["hint"] = r["hint"]
                if r.get("supported"):
                    out["supported"] = r["supported"]
                break
    return out


def act(request: str, repo_root: str = "", dry_run: bool = False,
        flow_id: Optional[str] = None, _depth: int = 0) -> Dict[str, Any]:
    """ai act 加强版统一入口(v22.18.0): 运维操作 + 代码修改一体化真实执行

    路由链 (对标ReAct闭环, 但AI永不接触shell):
      1. 关键词确定性多意图匹配(零推理, 支持链式指令, 含 code_fix 代码修复)
      2. 未命中 → 本地AI意图分类(零token, 只从注册动作ID里选, 不生成命令)
      3. 动作处理器顺序真实执行(白名单命令模板 / code_fix→auto_fix改码落盘), 失败即停
    代码修复类需求直接描述即可(如 "修复 engines/x.py 的yyy"), 内部路由 auto_fix
    (显式路径提取优先 + AST写前校验 + 原子替换 + 备份回滚)。
    递归: 请求中可嵌套 'ai fix/code/chat/think/act ...' 子指令, 本入口真实分发执行(非模拟),
          嵌套 ai act 受 _MAX_ACT_DEPTH 深度护栏保护('ai fix' 为并入前的旧写法, 仍兼容)。
    """
    try:
        # 0a. 管道模式: 'ai "XXX"' 或 'ai 'XXX'' → 先执行 ai 'XXX' 得到结果, 再把结果传给 ai act
        # v22.19.0: 两阶段执行, 阶段1 走本地模型产出, 阶段2 把产出当新 request 真实执行
        pipe_match = _AI_PIPE_RE.search(request)
        if pipe_match:
            pipe_text = pipe_match.group(1).strip()
            if _CLI:
                _banner("🔗 ai act · 管道模式", "阶段1: ai 产出 → 阶段2: act 真实执行", "两阶段串联")
                _stage(f"管道指令: \033[1mai '{pipe_text[:50]}'\033[0m")
            # 阶段1: 执行 ai 'XXX' 得到结果 (走 chat 本地模型, 用专门的 system prompt 让产出简洁)
            pipe_system = ("你是指令转换器。用户会给你一个任务描述, 你需要把它转换为一条简洁的操作指令。"
                          "要求: 1) 只输出指令文本, 不要解释 2) 用关键词而非完整句子 3) 控制在20字以内 "
                          "4) 如果是查看/统计类, 用'查看/统计/检查'等动词开头 5) 如果是修复类, 用'修复'开头 "
                          "示例: 输入'查看仓库状态' → 输出'查看仓库状态'; 输入'同步代码到GitHub' → 输出'同步GitHub'")
            stage1_result = chat(pipe_text, pipe_system, flow_id=flow_id or "act_pipe_stage1")
            if not stage1_result.get("success"):
                return {"success": False, "kind": "act", "request": request,
                        "error": f"管道阶段1失败: {stage1_result.get('error', 'ai 产出失败')}",
                        "stage": 1, "stage1_result": stage1_result}
            # 提取产出文本 (chat 返回 response 字段)
            stage1_output = (stage1_result.get("response") or "").strip()
            if not stage1_output:
                return {"success": False, "kind": "act", "request": request,
                        "error": "管道阶段1产出为空, 无法进入阶段2",
                        "stage": 1, "stage1_result": stage1_result}
            if _CLI:
                _stage(f"阶段1产出: \033[32m{stage1_output[:80]}...\033[0m")
                _stage(f"→ 进入阶段2: ai act \"{stage1_output[:50]}...\"")
            # 阶段2: 把产出当新 request 递归调用 act()
            stage2_result = act(stage1_output, repo_root, dry_run,
                                flow_id or "act_pipe_stage2", _depth=_depth)
            # 合并结果: 阶段1步骤 + 阶段2步骤
            stage1_steps = [{"cmd": f"[管道阶段1] ai '{pipe_text[:30]}'", "ok": True, "rc": 0,
                             "output": stage1_output[:500]}]
            stage2_steps = stage2_result.get("steps", [])
            stage2_result["steps"] = stage1_steps + stage2_steps
            stage2_result["pipe_mode"] = True
            stage2_result["pipe_stage1"] = {"input": pipe_text, "output": stage1_output}
            return stage2_result

        # 0b. 递归路径: 请求里含 'ai <子命令>' 嵌套指令 → 解析为有序步骤真实分发
        if _NESTED_CMD_RE.search(request):
            if _CLI:
                _banner("⚡ ai act · 递归指令真实执行", "白名单动作+嵌套ai子命令", "零token分类")
                _stage(f"指令: \033[1m{request[:60]}\033[0m")
            return _run_nested_act(request, repo_root, dry_run, flow_id, _depth)

        intents = _detect_operation_intents(request)
        routed_by = "keyword"
        if not intents:
            intents = _ai_classify_intents(request, flow_id)
            routed_by = "ai_classify"

        if not intents:
            return {"success": False, "kind": "act", "request": request,
                    "routed_by": routed_by, "intents": [], "steps": [],
                    "error": "未识别的操作意图(加强版 act 支持运维动作+代码修复, 见 supported)",
                    "supported": {k: v[0] for k, v in OPERATION_INTENTS.items()},
                    "hint": ("换个说法再试(如'daemon状态/AI员工多少/看日志/系统体检/拓展功能'), "
                             "或: 咨询问答用 ai chat、方案分析用 ai think、"
                             "代码修复直接说(如'修复 engines/x.py 的yyy')、"
                             "代码生成用 ai act \"ai code ...\"; 支持的操作见 supported")}

        if _CLI:
            _banner("⚡ ai act · 指令真实执行", "白名单动作(AI仅做分类)", "零token分类")
            _stage(f"指令: \033[1m{request[:60]}\033[0m")
            _stage(f"动作序列: \033[33m{' → '.join(intents)}\033[0m  (路由: {routed_by})")
            _stage(f"模式: {'📝 dry-run 预览' if dry_run else '✅ 真实执行'}")

        # 节点清单: 每个动作一个节点, 倒计时+预计完成 (execute_task内层自动从属上抛日志)
        nd = _Nodes("ai act 动作序列",
                    [(OPERATION_INTENTS[i][2], 45, i) for i in intents])
        nd.start()
        sub_results = []
        try:
            for idx, intent in enumerate(intents):
                canonical = OPERATION_INTENTS[intent][2]
                nd.run(idx)
                if _CLI:
                    _stage(f"[{idx + 1}/{len(intents)}] 执行动作 \033[36m{intent}\033[0m · {canonical}")
                # dev_audit/code_fix 需要解析用户原文识别目标模块/文件(规范指令串丢失"学生/考试/engines/x.py"等目标词)
                _exec_text = request if intent in ("dev_audit", "code_fix") else canonical
                r = execute_task(_exec_text, repo_root, dry_run,
                                 flow_id or f"act_{intent}")
                r["intent"] = intent
                sub_results.append(r)
                if r.get("success"):
                    nd.ok(idx)
                else:
                    nd.err(idx, note=(r.get("error") or "执行失败")[:60])
                    nd.skip_pending("前序动作失败")
                    break  # 失败即停, 不继续后续动作
        finally:
            nd.close()

        steps: list = []
        for r in sub_results:
            steps.extend(r.get("steps", []))

        out: Dict[str, Any] = {
            "success": all(r.get("success") for r in sub_results),
            "kind": "act",
            "request": request,
            "routed_by": routed_by,
            "intents": intents,
            "executed": [r.get("intent") for r in sub_results],
            "dry_run": dry_run,
            "steps": steps,
            "results": sub_results,
        }
        if not out["success"]:
            for r in sub_results:
                if not r.get("success"):
                    out["error"] = f"[{r.get('intent', '')}] {r.get('error', '执行失败')}"[:400]
                    if r.get("hint"):
                        out["hint"] = r["hint"]
                    if r.get("supported"):
                        out["supported"] = r["supported"]
                    break
        return out
    except Exception as e:
        return {"success": False, "kind": "act", "request": request,
                "error": f"act执行异常: {type(e).__name__}: {e}", "steps": []}


def think(question: str, context: str = "", flow_id: Optional[str] = None) -> Dict[str, Any]:
    """思考助理入口 (推理/决策/方案生成)"""
    system = ("你是MTSCOS思考助理,擅长深度推理和方案设计。"
              "请结构化输出: 1.问题分析 2.关键要素 3.推理过程 4.结论/方案")
    prompt = f"问题: {question}\n上下文: {context}\n\n请深度思考并给出方案:"
    result = _route_chat(prompt, system, flow_id)
    result["kind"] = "think"
    return result


def analyze(file_path: str, flow_id: Optional[str] = None) -> Dict[str, Any]:
    """代码分析入口 (语法/编译错误/优化建议)"""
    try:
        from code_analyzer_offline import analyze_file
        return analyze_file(file_path, flow_id)
    except ImportError as e:
        return {"success": False, "error": f"代码分析器未就绪: {e}"}


def compile_check(file_path: str, flow_id: Optional[str] = None) -> Dict[str, Any]:
    """离线编译辅助入口 (代码检查/错误定位)"""
    try:
        from code_analyzer_offline import compile_check_file
        return compile_check_file(file_path, flow_id)
    except ImportError as e:
        return {"success": False, "error": f"编译检查器未就绪: {e}"}


def review(code: str, flow_id: Optional[str] = None) -> Dict[str, Any]:
    """代码审查入口(按 MTSCOS 项目硬规则逐项审查)"""
    ollama = _get_ollama()
    if ollama and ollama["is_available"]():
        # 注入项目规则审查清单, 让本地模型对照规范找问题(权限/IDOR/真数据/设计Token/命名空间/本地推理)
        checklist = (
            "请对照以下 MTSCOS 项目硬规则审查代码并逐条指出违规(无违规也要说明):\n"
            "①路由/API 是否都有鉴权(@system_container 或 _check_login/_check_admin), 有无裸路由;\n"
            "②带 user_id 的端点是否做了归属校验(防 IDOR, 学生只能访问本人, 教职/SA 可跨查);\n"
            "③是否存在硬编码/模拟假数据, 数据是否来自真实 SQLite 库;\n"
            "④前端是否用 var(--el-*) 设计 Token, 有无硬编码颜色;\n"
            "⑤学生/前台页是否误链 /admin_app/* 管理员命名空间;\n"
            "⑥AI 推理路由是否 Ollama Cloud 优先 + 本地原生(11435)兜底;\n"
            "⑦输入是否做白名单/类型校验, 错误处理是否完整。\n"
            "待审查代码:\n"
        )
        result = ollama["review"](checklist + code, flow_id)
        result["route"] = "local_ollama"
        result["gateway"] = "local_ai_unified_gateway"
        result["rules_enforced"] = True
        return result
    return {"success": False, "error": "Ollama不可用"}


def classify(text: str, categories: list = None, flow_id: Optional[str] = None) -> Dict[str, Any]:
    """代码分类入口"""
    ollama = _get_ollama()
    if ollama and ollama["is_available"]():
        result = ollama["classify"](text, categories or ["code_type"], flow_id)
        result["route"] = "local_ollama"
        result["gateway"] = "local_ai_unified_gateway"
        return result
    return {"success": False, "error": "Ollama不可用"}


def health() -> Dict[str, Any]:
    """网关健康状态"""
    ollama = _get_ollama()
    ark = _get_volcengine()
    cloud_on = _cloud_fallback_enabled()
    # 本地命中率: 本地成功 / (本地成功 + 云端成功 + 被拦云端)
    # 防御式读取: _ROUTE_STATS 各版本键名有差异(local/native, cloud/cloud_ollama), 缺键按0计, 避免KeyError
    _rs_local = int(_ROUTE_STATS.get("local", 0) or 0) + int(_ROUTE_STATS.get("native", 0) or 0)
    _rs_cloud = int(_ROUTE_STATS.get("cloud", 0) or 0) + int(_ROUTE_STATS.get("cloud_ollama", 0) or 0) \
        + int(_ROUTE_STATS.get("volcengine", 0) or 0)
    _rs_blocked = int(_ROUTE_STATS.get("blocked_cloud", 0) or 0)
    decided = _rs_local + _rs_cloud + _rs_blocked
    local_hit_rate = round(_rs_local / decided, 6) if decided else 1.0
    return {
        "gateway": "local_ai_unified_gateway",
        "route_priority": _ROUTE_PRIORITY,
        "local_ollama": ollama["health"]() if ollama else {"available": False},
        "cloud_volcengine": {
            "available": ark["is_available"]() if ark else False,
            "fallback_enabled": cloud_on,  # 默认 False: 极致本地优先, 零云端token
            "enable_hint": "export MTSCOS_AI_ALLOW_CLOUD=1 可临时开启云端应急",
        },
        "routing_stats": dict(_ROUTE_STATS),
        "local_hit_rate": local_hit_rate,
        "local_retry_backoff": list(_LOCAL_RETRY_BACKOFF),
        "local_max_attempts": _LOCAL_MAX_ATTEMPTS,
        "supported_scenarios": ["chat", "code", "analyze", "think", "compile", "review", "classify"],
        "version": "v22.18.0",
    }


# ===== CLI 入口 =====
def _run_interactive(kind: str, prompt: str, system: str = ""):
    """交互式命令(chat/code/think): 流式打字机输出 + 美化头尾"""
    import time
    if not prompt:
        sys.stderr.write("❌ 请输入内容, 例如: ai \"你好\"\n")
        return
    use_coder = (kind == "code")
    model_name = "qwen2.5-coder:14b" if use_coder else "qwen2.5:7b"
    titles = {"chat": "💬 本地AI对话", "code": "💻 代码生成 (coder模型)", "think": "🧠 深度思考"}
    _banner(titles.get(kind, kind), model_name, "local_ollama · 零token")
    sys.stderr.write(f"\n\033[1;37m❓ 你:\033[0m {prompt}\n\n")
    sys.stderr.write(f"\033[1;32m🤖 AI:\033[0m  ")
    sys.stderr.flush()

    t0 = time.time()
    if kind == "code" and not system:
        system = ("你是资深全栈工程师,精通Python/JavaScript/TypeScript/HTML/CSS/SQL。"
                  "输出代码要求: 1.完整可运行 2.注释清晰 3.遵循规范 4.优先给代码,简短说明。")
    if kind == "code":
        # 编码铁律 + MTSCOS项目硬规则(与 code() 入口一致, 流式路径同样不可豁免)
        system = _with_rules(system)
    elif kind == "think" and not system:
        system = "你是深度思考助手。请有条理地分析问题,给出分步骤的推理和结论。"

    res = _ollama_stream(prompt, system, use_coder=use_coder)
    if res is None:
        # 流式失败 → 回退普通路由 (非流式), 直接打印结果
        sys.stderr.write("\033[2m(流式不可用, 改用普通模式...)\033[0m\n")
        with _Spin("AI 思考中"):
            res = _route_chat(prompt, system, use_coder=use_coder)
        if res.get("success"):
            sys.stdout.write(res.get("response", "") + "\n")
            sys.stdout.flush()
    el = time.time() - t0
    sys.stderr.write(f"\n\033[2m  ── {model_name} · 耗时 {el:.1f}s · 本地零云端积分 ──\033[0m\n\n")
    sys.stderr.flush()


def main():
    import argparse
    parser = argparse.ArgumentParser(description="MTSCOS 本地AI统一网关")
    parser.add_argument("command", choices=["chat", "code", "optimize", "fix", "act", "run", "sync", "analyze", "think", "compile", "review", "classify", "health"],
                        help="命令 (act=加强版一体化入口: 运维动作+代码修复, run=白名单操作, sync=同步GitHub; fix已废弃仅兼容自动路由act)")
    parser.add_argument("input", nargs="?", help="输入(文本或文件路径)")
    parser.add_argument("--system", default="", help="系统提示")
    parser.add_argument("--flow-id", default=None, help="flow_id")
    parser.add_argument("--write-back", action="store_true", help="optimize时直接写回文件")
    parser.add_argument("--instruction", default="", help="optimize时的优化指令")
    parser.add_argument("--dry-run", action="store_true", help="act/fix时只输出计划不修改/不落盘")
    parser.add_argument("--project-root", default="", help="act/fix时指定项目根目录")
    args = parser.parse_args()

    if args.command == "health":
        print(json.dumps(health(), ensure_ascii=False, indent=2))
        return

    # 启用终端实时反馈 (流式/进度/spinner)
    _prog_on()

    # 交互式对话/编码/思考: 流式打字机输出到 stdout, 不打印JSON
    if args.command in ("chat", "code", "think"):
        _run_interactive(args.command, args.input, args.system)
        return

    try:
        if args.command == "optimize":
            result = optimize_file(args.input, args.instruction, args.write_back, args.flow_id)
        elif args.command == "fix":
            # v22.18.0 'fix' 子命令已废除并合并进 ai act 加强版; 此处仅为旧脚本兼容自动路由
            _stage("\033[33m⚠ 'fix' 子命令已废除(v22.18.0, 合并进 ai act 加强版), 本次自动路由到 act\033[0m")
            result = act(args.input or "", args.project_root, args.dry_run, args.flow_id)
        elif args.command == "act":
            result = act(args.input or "", args.project_root, args.dry_run, args.flow_id)
        elif args.command == "run":
            result = execute_task(args.input or "", args.project_root, args.dry_run, args.flow_id)
        elif args.command == "sync":
            result = execute_task("同步GitHub", args.project_root, args.dry_run, args.flow_id)
        elif args.command == "analyze":
            result = analyze(args.input, args.flow_id)
        elif args.command == "compile":
            result = compile_check(args.input, args.flow_id)
        elif args.command == "review":
            result = review(args.input, args.flow_id)
        elif args.command == "classify":
            result = classify(args.input, flow_id=args.flow_id)
        else:
            result = {"success": False, "error": f"未知命令: {args.command}"}
    except Exception as e:
        result = {"success": False, "error": f"网关异常: {type(e).__name__}: {e}"}

    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()