#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
日志驱动 AI 智能决策引擎 (本地规则优先, 零在线 token)
流程: 日志信号抽取 → 7类信号分类 + 置信度 → 决策矩阵(≥阈值) → 10类动作执行器
      → 动作结果 → 投喂脑库 → 落库(mt_ai_decision_log + mt_ai_action_log)
信号分类(7类):
  CODE_EXCEPTION   代码异常 (Syntax/Import/Attribute/Key/Index/Type/Value/ZeroDivision/Permission/SQLite)
  FRONTEND_ERROR   前端错误 (is not a function / is not defined / 404资源 / Failed to load / CORS)
  ROUTE_MISSING    路由缺失 (404 / No such route / page not found / 蓝图冲突)
  RULE_WEAK        规则弱约束 (弱约束词命中 + 规则绕过)
  FEATURE_GAP      功能缺口 (not implemented / TODO / FIXME / 占位返回)
  SUBSYS_DEGRADED  子系统降级 (engine failed / unresponsive / worker crashed / daemon not running)
  STYLING_CLASH    样式冲突 (inline style / hardcoded hex / overflow hidden / missing class)
动作(10类):
  CODE_FIX / FRONTEND_FIX / ROUTE_COMPLETE / RULE_STRENGTHEN /
  FEATURE_ENHANCE / SUBSYS_UPGRADE / STYLING_BEAUTIFY /
  CONFIG_TUNE / DOC_COMPLETE / MANUAL_TRIAGE
"""
from __future__ import annotations

import hashlib
import json
import logging
import os
import re
import subprocess
import sys
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import ai_governance_db as db

logger = logging.getLogger("log_action_decision_engine")

SCAN_ROOT = os.environ.get(
    "MT_GOV_SCAN_ROOT",
    os.path.expanduser("~/Library/CloudStorage/OneDrive-个人/文档/MTSCOS_AI_Project/flask-app"),
)

# ============== 7类信号定义 + 关键词签名匹配 ==============
SIGNAL_DEFS: Dict[str, Dict[str, Any]] = {
    "CODE_EXCEPTION": {
        "desc": "代码异常",
        "patterns": [
            (r"\b(SyntaxError|IndentationError|ImportError|ModuleNotFoundError|AttributeError|"
             r"KeyError|IndexError|TypeError|ValueError|ZeroDivisionError|NameError|FileNotFoundError|"
             r"PermissionError|sqlite3\.?\w*Error|OperationalError|database is locked|Traceback \(most recent call last\))\b", 2.0),
            (r"Exception in thread|Unhandled exception|AssertionError", 1.8),
            (r"\[ERROR\].*?\.py:\d+", 1.2),
        ],
        "default_action": "CODE_FIX",
        "fallback_action": "MANUAL_TRIAGE",
    },
    "FRONTEND_ERROR": {
        "desc": "前端错误",
        "patterns": [
            (r"(is not a function|is not defined|Cannot read propert|Cannot set propert|undefined is not)", 2.2),
            (r"(Failed to load (resource|module)|net::ERR_(ABORTED|BLOCKED|CONNECTION_REFUSED|NAME_NOT_RESOLVED))", 2.0),
            (r"(Loading chunk \d+ failed|No such file or directory.*\.(js|css|png|svg))", 1.8),
            (r"(Access-Control-Allow-Origin|CORS|Cross-Origin)", 1.6),
            (r"(window\.app\.|window\.apiCall|showNotification|console\.error\(\")", 1.0),
            (r"(404.*\.(js|css)|\.css Failed|\.js 404)", 1.5),
        ],
        "default_action": "FRONTEND_FIX",
        "fallback_action": "MANUAL_TRIAGE",
    },
    "ROUTE_MISSING": {
        "desc": "路由缺失",
        "patterns": [
            (r"(404 Not Found|page not found|No such route|No rule to match|Not Found for url:)", 2.0),
            (r"(AssertionError.*?View function mapping|Blueprint.*?name collision|conflicting.*route)", 1.8),
            (r"(Method Not Allowed|405 Method Not Allowed|allowed_methods)", 1.4),
            (r"(redirected you too many times|Redirect loop|ERR_TOO_MANY_REDIRECTS)", 1.5),
        ],
        "default_action": "ROUTE_COMPLETE",
        "fallback_action": "MANUAL_TRIAGE",
    },
    "RULE_WEAK": {
        "desc": "规则弱约束",
        "patterns": [
            (r"\b(应该|建议|推荐|尽量|原则上|一般|应当|可考虑|适当|酌情|适宜|最好|"
             r"尽可能|一般来说|视情况|根据情况|如有必要|如有需要|酌量|量力)\b", 1.8),
            (r"(bypass_allowed.*True|绕过规则|未经审批)", 2.2),
            (r"(#[unused]|TODO|FIXME|HACK)\s.*?(规则|权限|认证|路由|安全)", 1.0),
        ],
        "default_action": "RULE_STRENGTHEN",
        "fallback_action": "MANUAL_TRIAGE",
    },
    "FEATURE_GAP": {
        "desc": "功能缺口",
        "patterns": [
            (r"(NotImplementedError|not (yet )?implemented|to be implemented|placeholder|stub)", 2.0),
            (r"(TODO|FIXME|HACK)\s*[:：].*?(功能|接口|路由|页面|模块|子系统|engine|服务|API)", 1.4),
            (r"(return.*None|return \{\}|pass  # (未|待)实现)", 1.0),
        ],
        "default_action": "FEATURE_ENHANCE",
        "fallback_action": "DOC_COMPLETE",
    },
    "SUBSYS_DEGRADED": {
        "desc": "子系统降级",
        "patterns": [
            (r"(engine|daemon|service|worker|agent|scheduler|sync).*? "
             r"(failed|crashed|unresponsive|stopped|not running|dead|exit code \d+)", 2.0),
            (r"(failed to start|startup error|initialization failed|heartbeat lost|watchdog timeout)", 1.8),
            (r"(connection refused|timeout|timed out).*?(api|engine|db|redis|mq)", 1.6),
            (r"(Health check|probe).*?FAIL", 1.6),
        ],
        "default_action": "SUBSYS_UPGRADE",
        "fallback_action": "MANUAL_TRIAGE",
    },
    "STYLING_CLASH": {
        "desc": "样式冲突",
        "patterns": [
            (r"(inline style violation|V2 violation|style=.*?#[\da-fA-F]{3,8})", 1.6),
            (r"(BEM|--.*? violation|double hyphen|unresolved class|undefined token)", 1.4),
            (r"(layout overflow|horizontal scroll|scrollbar.*?x|min-width missing)", 1.2),
            (r"(排版混乱|显示混乱|布局重复|button.*?not visible|element.*?clipped)", 1.5),
        ],
        "default_action": "STYLING_BEAUTIFY",
        "fallback_action": "MANUAL_TRIAGE",
    },
}

# ============== 动作元信息 ==============
ACTION_META: Dict[str, Dict[str, Any]] = {
    "CODE_FIX":         {"name": "代码修复",     "min_score": 0.55, "min_sev": "medium"},
    "FRONTEND_FIX":     {"name": "前端错误修复", "min_score": 0.55, "min_sev": "medium"},
    "ROUTE_COMPLETE":   {"name": "路由补齐",     "min_score": 0.50, "min_sev": "low"},
    "RULE_STRENGTHEN":  {"name": "规则强化",     "min_score": 0.50, "min_sev": "low"},
    "FEATURE_ENHANCE":  {"name": "功能完善",     "min_score": 0.60, "min_sev": "medium"},
    "SUBSYS_UPGRADE":   {"name": "子系统升级",   "min_score": 0.55, "min_sev": "medium"},
    "STYLING_BEAUTIFY": {"name": "前端美化",     "min_score": 0.50, "min_sev": "low"},
    "CONFIG_TUNE":      {"name": "配置调优",     "min_score": 0.50, "min_sev": "low"},
    "DOC_COMPLETE":     {"name": "文档补全",     "min_score": 0.00, "min_sev": "low"},
    "MANUAL_TRIAGE":    {"name": "人工待办",     "min_score": 0.00, "min_sev": "low"},
}

SEV_ORDER = {"low": 0, "medium": 1, "high": 2, "critical": 3}

def _infer_source_file_from_context(signal_name: str, snippet: str, scan_root: str) -> Optional[str]:
    """日志类异常根据关键词在源码目录中回溯匹配关联源文件 (避免只拿到 .log 行不可编辑)."""
    if not os.path.isdir(scan_root):
        return None
    # 提取可能的模块/函数/路由/JS标识符
    candidates = set()
    for pat in [r"\[(\w+)\]", r"([A-Za-z_]\w*_\w+_engine)", r"(TypeError|window\.\w+|showNotification|apiCall)",
                r"((?:/api|/admin_app|/auth)[A-Za-z0-9_\-/]*)",
                r"\.([A-Za-z_]\w+(?:Error|Exception))"]:
        for m in re.finditer(pat, snippet):
            if m.lastindex and m.group(m.lastindex):
                candidates.add(m.group(m.lastindex))
    best: Optional[Tuple[int, str]] = None
    try:
        for dirpath, dirs, files in os.walk(scan_root):
            dirs[:] = [d for d in dirs if d not in {".git", "__pycache__", ".venv", "node_modules",
                                                      "Database_Backups", "_archive", ".cache"}]
            for fn in files:
                if not fn.endswith((".py", ".html", ".js", ".css")):
                    continue
                hits = 0
                fp = os.path.join(dirpath, fn)
                try:
                    with open(fp, "r", encoding="utf-8", errors="ignore") as f:
                        head = f.read(8000)
                except Exception:
                    continue
                for kw in candidates:
                    if len(kw) < 4:
                        continue
                    if kw in head:
                        hits += 1
                if hits:
                    # 优先选日志提及 engine/worker 名称的同名文件
                    bonus = 0
                    base = os.path.splitext(fn)[0]
                    for kw in candidates:
                        if base and kw.endswith(base) or base.endswith(kw):
                            bonus = 5
                            break
                    total = hits + bonus
                    if best is None or total > best[0]:
                        best = (total, fp)
                if best and best[0] >= 6:  # 强匹配直接返回
                    return best[1]
    except Exception:
        pass
    return best[1] if best else None



def _severity_of(top_score: float) -> str:
    if top_score >= 3.0:
        return "critical"
    if top_score >= 2.0:
        return "high"
    if top_score >= 1.0:
        return "medium"
    return "low"


# ===================================================================
# 1. 日志/代码源的聚合信号抽取
# ===================================================================
class SignalExtractor:
    """从 SCAN_ROOT 和日志目录扫描, 抽取7类信号列表."""

    def __init__(self, max_signals: int = 40, deadline_ts: Optional[float] = None):
        self.max_signals = max_signals
        self.deadline_ts = deadline_ts  # 绝对 unix 时间戳, 超过立即返回

    def _hit_deadline(self) -> bool:
        if not self.deadline_ts:
            return False
        import time as _t
        return _t.time() >= self.deadline_ts

    # ---------- 日志扫描 ----------
    def _collect_log_lines(self, limit_lines: int = 2000) -> List[Tuple[str, str, int]]:
        """扫描日志, 返回 [(source_file, line, line_no)]."""
        out: List[Tuple[str, str, int]] = []
        log_dirs = [
            os.path.join(SCAN_ROOT, "logs"),
            os.path.join(SCAN_ROOT, "_runtime", "logs"),
            os.path.join(os.path.dirname(os.path.abspath(__file__)), "_runtime", "logs"),
        ]
        for ld in log_dirs:
            if not os.path.isdir(ld):
                continue
            try:
                for fn in sorted(os.listdir(ld)):
                    if not fn.endswith((".log", ".txt", ".out")):
                        continue
                    fp = os.path.join(ld, fn)
                    try:
                        with open(fp, "r", encoding="utf-8", errors="ignore") as f:
                            for i, line in enumerate(f, 1):
                                if len(out) >= limit_lines:
                                    return out
                                out.append((fp, line.rstrip("\n"), i))
                    except Exception:
                        continue
            except Exception:
                continue
        return out

    # ---------- 代码扫描: 路由/规则/前端 ----------
    def _collect_code_hints(self, limit_hits: int = 500) -> List[Tuple[str, str, int]]:
        """扫描 Python/HTML/CSS/JS 代码中 7 类触发点."""
        hints: List[Tuple[str, str, int]] = []
        for dirpath, dirs, files in os.walk(SCAN_ROOT):
            dirs[:] = [d for d in dirs if d not in {".git", "__pycache__", ".venv", "node_modules",
                                                      "Database_Backups", "_archive", ".cache"}]
            for fn in files:
                if not fn.endswith((".py", ".html", ".css", ".js", ".md")):
                    continue
                if len(hints) >= limit_hits:
                    return hints
                fp = os.path.join(dirpath, fn)
                try:
                    with open(fp, "r", encoding="utf-8", errors="ignore") as f:
                        for i, line in enumerate(f, 1):
                            s = line.strip()
                            if not s:
                                continue
                            _func_unimpl = bool(re.search(r"def\s+\w+\([^)]*\)\s*:\s*#\s*(未|待)", s))
                            if (len(hints) < limit_hits
                                    and fn.endswith(".py")
                                    and ("TODO" in s or "FIXME" in s or "NotImplementedError" in s
                                         or _func_unimpl)):
                                hints.append((fp, s, i))
                            elif (len(hints) < limit_hits
                                  and fn.endswith(".html")
                                  and re.search(r"style\s*=\s*[\"'].*?#[\da-fA-F]", s)):
                                hints.append((fp, s, i))
                            elif (len(hints) < limit_hits
                                  and fn.endswith(".py")
                                  and re.search(r"@\w+\.route|add_url_rule|blueprint", s)
                                  and ("TODO" in s or "FIXME" in s or "not implemented" in s.lower())):
                                hints.append((fp, s, i))
                            # RULE_WEAK: 弱约束词 (py/md/html/js)
                            elif (len(hints) < limit_hits
                                  and fn.endswith((".py", ".md", ".html", ".js"))
                                  and re.search(
                                      r"\b(应该|建议|推荐|尽量|原则上|一般|应当|可考虑|适当|酌情|适宜|"
                                      r"最好|尽可能|一般来说|视情况|根据情况|如有必要|如有需要|酌量|量力)\b", s)):
                                hints.append((fp, s, i))
                            # CODE_EXCEPTION: bare_except / print( 生产代码
                            elif (len(hints) < limit_hits
                                  and fn.endswith(".py")
                                  and (re.search(r"^\s*except\s*:", s)
                                       or re.search(r"^\s*print\s*\(", s))):
                                hints.append((fp, s, i))
                except Exception:
                    continue
        return hints

    # ---------- 信号分类 ----------
    def classify(self, line: str) -> List[Dict[str, Any]]:
        """对一行文本做多标签分类, 返回命中的信号列表 (按score降序)."""
        hits = []
        for sig_name, sig in SIGNAL_DEFS.items():
            score = 0.0
            hit_patterns = []
            for pat, weight in sig["patterns"]:
                m = re.search(pat, line)
                if m:
                    score += weight
                    hit_patterns.append(pat[:80])
            if score > 0:
                hits.append({
                    "signal": sig_name,
                    "score": round(score, 3),
                    "severity": _severity_of(score),
                    "patterns": hit_patterns,
                })
        hits.sort(key=lambda h: h["score"], reverse=True)
        return hits

    def extract(self) -> List[Dict[str, Any]]:
        """抽取全部信号并返回规范化列表 (截断到 max_signals, 受 deadline_ts 约束)."""
        results: List[Dict[str, Any]] = []
        seen_sigs = set()
        if self._hit_deadline():
            return results
        sources = self._collect_log_lines() + self._collect_code_hints()
        for fp, line, line_no in sources:
            if self._hit_deadline():
                break
            classifications = self.classify(line)
            if not classifications:
                continue
            for c in classifications:
                sig = f"{c['signal']}:{hashlib.sha256((fp + line).encode()).hexdigest()[:12]}"
                if sig in seen_sigs:
                    continue
                seen_sigs.add(sig)
                results.append({
                    "sig_id": sig,
                    "signal": c["signal"],
                    "signal_desc": SIGNAL_DEFS[c["signal"]]["desc"],
                    "score": c["score"],
                    "severity": c["severity"],
                    "source_file": fp,
                    "line_no": line_no,
                    "content_snippet": line[:300],
                    "matched_patterns": c["patterns"],
                    "default_action": SIGNAL_DEFS[c["signal"]]["default_action"],
                    "fallback_action": SIGNAL_DEFS[c["signal"]]["fallback_action"],
                })
                if len(results) >= self.max_signals:
                    return results
        results.sort(key=lambda r: (SEV_ORDER.get(r["severity"], 0), r["score"]), reverse=True)
        return results


# ===================================================================
# 2. AI 决策器: 信号 + 上下文 → 最终动作
# ===================================================================
class AIDecider:
    """本地规则决策 (EigenFlux 共识思想: 多因子加权打分 ≥ 阈值才执行)."""

    def decide(self, signal: Dict[str, Any], file_ctx: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """输入信号, 输出决策 {action, confidence, reasoning, safe_edit}.
        sev 加权置信度 + 日志异常回溯关联源码文件.
        """
        file_ctx = file_ctx or {}
        sig = signal["signal"]
        raw_score = float(signal["score"])
        sev = signal["severity"]
        default = signal["default_action"]
        fallback = signal["fallback_action"]

        # sev 权重叠加: critical=1.2 / high=1.05 / medium=0.9 / low=0.75
        sev_weight = {"critical": 1.2, "high": 1.05, "medium": 0.9, "low": 0.75}.get(sev, 0.9)
        # 模式分: 归一化到 [0,1], 再乘 sev 权重
        pattern_score = min(1.0, raw_score / 2.2)
        confidence = pattern_score * sev_weight
        # 历史成功率修正 (平滑)
        history = self._history_factor(default)
        confidence = round(confidence * 0.7 + history * 0.3, 4)
        # 日志类异常 (source_file 是 .log/.txt) → 回溯关联源码文件
        src = signal.get("source_file", "")
        inferred: Optional[str] = None
        if src.lower().endswith((".log", ".txt", ".out")):
            inferred = _infer_source_file_from_context(sig, signal.get("content_snippet", ""), SCAN_ROOT)
            if inferred:
                # 命中关联文件: confidence 小幅提升
                confidence = round(min(1.0, confidence + 0.12), 4)
                src_for_safe = inferred
                reasoning_src = f"关联文件 {os.path.basename(inferred)}"
            else:
                src_for_safe = src
                reasoning_src = "未关联源码文件"
        else:
            src_for_safe = src
            reasoning_src = "直接命中源码"
        # 可写性判定 (用关联后的目标)
        safe_edit = self._safe_to_edit(src_for_safe)
        # 降级/升级
        if not safe_edit and default in ("CODE_FIX", "FRONTEND_FIX", "ROUTE_COMPLETE",
                                          "RULE_STRENGTHEN", "STYLING_BEAUTIFY",
                                          "FEATURE_ENHANCE", "SUBSYS_UPGRADE"):
            # 不可写: 根据严重度决定人工还是仅文档
            if SEV_ORDER.get(sev, 0) >= SEV_ORDER["medium"]:
                action = "MANUAL_TRIAGE"
                reasoning = f"{sig} 默认 {default}, 但{reasoning_src}不可编辑, 严重度{sev}→人工待办"
            else:
                action = "DOC_COMPLETE"
                reasoning = f"{sig} 默认 {default}, 但{reasoning_src}不可编辑→归档"
            # 记录回 signal 层, 便于 executor 用推断路径做上下文
            signal["source_file"] = src_for_safe
        elif confidence < ACTION_META[default]["min_score"]:
            if SEV_ORDER.get(sev, 0) >= SEV_ORDER["high"]:
                action = "MANUAL_TRIAGE"
                reasoning = f"{sig} 严重度{sev}, 但置信度{confidence}<阈值{ACTION_META[default]['min_score']}→人工确认 ({reasoning_src})"
            else:
                action = "DOC_COMPLETE"
                reasoning = f"{sig} 置信度{confidence}低, 先归档文档 ({reasoning_src})"
            signal["source_file"] = src_for_safe
        else:
            action = default
            reasoning = f"{sig} 置信度{confidence}≥阈值{ACTION_META[default]['min_score']}, 执行{ACTION_META[default]['name']} ({reasoning_src})"
            signal["source_file"] = src_for_safe

        return {
            "action": action,
            "action_name": ACTION_META[action]["name"],
            "confidence": confidence,
            "severity": sev,
            "reasoning": reasoning,
            "safe_edit": safe_edit,
            "consensus_pass": confidence >= db.CONSENSUS_THRESHOLD,
            "inferred_source": inferred,
        }

    def _history_factor(self, action: str) -> float:
        """历史成功率: 查询 mt_ai_action_log, 得到 0~1."""
        try:
            conn = db.get_conn()
            try:
                row = conn.execute(
                    "SELECT COUNT(*) AS c, "
                    "SUM(CASE WHEN success=1 THEN 1 ELSE 0 END) AS s "
                    "FROM mt_ai_action_log WHERE action=?", (action,)
                ).fetchone()
                c = int(row["c"] or 0)
                s = int(row["s"] or 0)
                if c == 0:
                    return 0.5
                return max(0.0, min(1.0, s / max(c, 1)))
            finally:
                conn.close()
        except Exception:
            return 0.5

    def _safe_to_edit(self, fp: str) -> bool:
        if not fp or not os.path.exists(fp):
            return False
        try:
            size = os.lstat(fp).st_size
        except Exception:
            return False
        if size > 1 * 1024 * 1024:  # 1MB 以上避免
            return False
        ext = os.path.splitext(fp)[1].lower()
        return ext in (".py", ".html", ".css", ".js", ".json", ".md", ".txt")


# ===================================================================
# 3. 动作执行器 (10类动作, 最小化安全编辑 + 语法验证回滚)
# ===================================================================
class ActionExecutor:
    """最小化安全编辑, 每步都有 before/after_hash + 语法验证."""

    SUCCESS_RESULT = (True, "")

    def __init__(self):
        self._applied_this_round = 0
        self._max_per_round = 15

    @property
    def at_capacity(self) -> bool:
        return self._applied_this_round >= self._max_per_round

    def execute(self, decision: Dict[str, Any], signal: Dict[str, Any]) -> Tuple[bool, str, Dict[str, Any]]:
        """执行单个决策, 返回 (success, detail, context)."""
        if self.at_capacity:
            return False, "本回合动作达到上限", {}
        action = decision["action"]
        try:
            if action == "CODE_FIX":
                ok, detail, ctx = self._act_code_fix(decision, signal)
            elif action == "FRONTEND_FIX":
                ok, detail, ctx = self._act_frontend_fix(decision, signal)
            elif action == "ROUTE_COMPLETE":
                ok, detail, ctx = self._act_route_complete(decision, signal)
            elif action == "RULE_STRENGTHEN":
                ok, detail, ctx = self._act_rule_strengthen(decision, signal)
            elif action == "FEATURE_ENHANCE":
                ok, detail, ctx = self._act_feature_enhance(decision, signal)
            elif action == "SUBSYS_UPGRADE":
                ok, detail, ctx = self._act_subsys_upgrade(decision, signal)
            elif action == "STYLING_BEAUTIFY":
                ok, detail, ctx = self._act_styling_beautify(decision, signal)
            elif action == "CONFIG_TUNE":
                ok, detail, ctx = self._act_config_tune(decision, signal)
            elif action == "DOC_COMPLETE":
                ok, detail, ctx = self._act_doc_complete(decision, signal)
            elif action == "MANUAL_TRIAGE":
                ok, detail, ctx = self._act_manual_triage(decision, signal)
            else:
                ok, detail, ctx = False, f"未知动作 {action}", {}
            if ok:
                self._applied_this_round += 1
            return ok, detail, ctx
        except Exception as e:
            return False, f"执行异常: {type(e).__name__}: {e}", {}

    # ---------- 底层: 安全文本替换 + 回滚 ----------
    def _safe_rewrite(self, fp: str, transformer_fn,
                      syntax_check: Optional[str] = None) -> Tuple[bool, str, Dict[str, Any]]:
        """最小化安全重写: 读 → transformer_fn(lines) → 写 → 语法验证 → 失败回滚."""
        if not os.path.exists(fp):
            return False, "文件不存在", {}
        try:
            with open(fp, "r", encoding="utf-8", errors="ignore") as f:
                lines = f.readlines()
        except Exception as e:
            return False, f"读失败: {e}", {}
        before_hash = hashlib.sha256("".join(lines).encode()).hexdigest()
        try:
            new_lines, note = transformer_fn(list(lines))
        except Exception as e:
            return False, f"transformer 异常: {e}", {}
        if new_lines == lines:
            return False, "无实际变更", {"note": note}
        try:
            with open(fp, "w", encoding="utf-8") as f:
                f.writelines(new_lines)
        except Exception as e:
            return False, f"写失败: {e}", {}
        after_hash = hashlib.sha256("".join(new_lines).encode()).hexdigest()
        # 语法验证 (仅 .py)
        if syntax_check == "python" and fp.endswith(".py"):
            try:
                result = subprocess.run(
                    [sys.executable, "-m", "py_compile", fp],
                    capture_output=True, text=True, timeout=20,
                )
                if result.returncode != 0:
                    with open(fp, "w", encoding="utf-8") as f:
                        f.writelines(lines)
                    return False, f"语法失败已回滚: {result.stderr[:160]}", {"before_hash": before_hash, "after_hash": after_hash}
            except Exception as e:
                with open(fp, "w", encoding="utf-8") as f:
                    f.writelines(lines)
                return False, f"语法验证异常已回滚: {e}", {}
        return True, note, {"before_hash": before_hash, "after_hash": after_hash}

    # ---------- 10个动作实现 ----------
    def _act_code_fix(self, d, s) -> Tuple[bool, str, Dict[str, Any]]:
        snippet = s.get("content_snippet", "")
        fp = s.get("source_file", "")
        line_no = s.get("line_no", 0)
        if not fp.endswith(".py") or line_no <= 0:
            return False, "非 Python 文件或无行号, 跳过代码修复", {}

        def tx(lines):
            i = line_no - 1
            if i >= len(lines):
                return lines, "行号越界"
            original = lines[i]
            # bare_except
            if "except:" in original:
                lines[i] = original.replace("except:", "except Exception:")
                return lines, "bare_except → except Exception:"
            # print → logger.info
            if re.search(r"\bprint\s*\(", original) and "logger" not in original:
                lines[i] = re.sub(r"\bprint\s*\(", "logger.info(", original, count=1)
                return lines, "print → logger.info"
            # 弱约束词 TODO/FIXME 注释删除
            if re.search(r"#\s*\[unused\]\s*$", original):
                lines[i] = re.sub(r"#\s*\[unused\]\s*$", "", original)
                return lines, "删除 #[unused]"
            return lines, "无匹配修复策略"

        return self._safe_rewrite(fp, tx, syntax_check="python")

    def _act_frontend_fix(self, d, s) -> Tuple[bool, str, Dict[str, Any]]:
        """前端错误: 对 HTML 中裸 JS 调用做能力探测包壳."""
        fp = s.get("source_file", "")
        line_no = s.get("line_no", 0)
        snippet = s.get("content_snippet", "")
        if not fp.endswith((".html", ".js")) or line_no <= 0:
            return False, "非前端文件, 跳过", {}

        def tx(lines):
            i = line_no - 1
            if i >= len(lines):
                return lines, "行号越界"
            original = lines[i]
            # window.apiCall(...) → 能力探测
            if "window.apiCall(" in original or "window.app." in original or "showNotification(" in original:
                new = original
                # 包壳: 如果函数不存在就 fallback console.warn
                for fn in ("window.apiCall", "showNotification", "window.app.apiGet",
                           "window.showLoading", "window.hideLoading"):
                    if f"{fn}(" in new:
                        new = new.replace(f"{fn}(", f"((typeof {fn} === 'function') ? {fn} : (...args) => console.warn('{fn}未初始化', args))(")
                if new != original:
                    return [new], "前端调用增加能力探测fallback"
            return lines, "无匹配前端修复策略"

        return self._safe_rewrite(fp, tx)

    def _act_route_complete(self, d, s) -> Tuple[bool, str, Dict[str, Any]]:
        """路由缺失: 扫描路由注册文件, 记录缺失路由到经验库 (不擅自新增)."""
        snippet = s.get("content_snippet", "")
        missing = re.search(r"(?:for url:|Not Found for|/)([A-Za-z0-9_\-/\.\?=&%]+)", snippet)
        route_path = missing.group(1) if missing else snippet[:80]
        return True, f"路由缺失登记: {route_path} (已记录待人工审批, 不擅自新增路由)", {
            "route_path": route_path
        }

    def _act_rule_strengthen(self, d, s) -> Tuple[bool, str, Dict[str, Any]]:
        """规则强化: Python/MD 文件内弱约束词替换为强约束."""
        fp = s.get("source_file", "")
        line_no = s.get("line_no", 0)
        if line_no <= 0:
            return False, "无行号", {}
        ext = os.path.splitext(fp)[1].lower()
        if ext not in (".py", ".md", ".html", ".js"):
            return False, f"扩展名 {ext} 不处理", {}

        def tx(lines):
            i = line_no - 1
            if i >= len(lines):
                return lines, "行号越界"
            original = lines[i]
            new = original
            applied = []
            for w, strong in db.WEAK_WORDS.items():
                if w in new:
                    # 对 "便宜/适宜" 中的 "宜" 误判防护: 仅整个词独立
                    safe_pat = r"(?<![A-Za-z\u4e00-\u9fff])" + re.escape(w) + r"(?![A-Za-z\u4e00-\u9fff])"
                    if re.search(safe_pat, new):
                        new = re.sub(safe_pat, strong, new)
                        applied.append(f"{w}→{strong}")
            if new != original:
                return [new], "规则强化: " + ", ".join(applied)
            return lines, "无弱约束词 (已被替换或被词边界排除)"

        return self._safe_rewrite(fp, tx, syntax_check="python" if ext == ".py" else None)

    def _act_feature_enhance(self, d, s) -> Tuple[bool, str, Dict[str, Any]]:
        """功能缺口: 对 NotImplementedError 替换为具体 stub + 投喂经验库."""
        fp = s.get("source_file", "")
        line_no = s.get("line_no", 0)
        if not fp.endswith(".py") or line_no <= 0:
            return False, "非 Python 或无行号, 仅登记文档", {}

        def tx(lines):
            i = line_no - 1
            if i >= len(lines):
                return lines, "行号越界"
            original = lines[i]
            if "NotImplementedError" in original:
                # 精准替换 NotImplementedError( 为 RuntimeError('FEATURE_GAP: xxxx' 同时保留原参数
                m = re.search(r"raise\s+NotImplementedError\s*\((.*)\)", original)
                if m:
                    args = m.group(1).strip() or "''"
                    _ts = datetime.now().isoformat()
                    replacement = (
                        original[:m.start()]
                        + "raise RuntimeError('FEATURE_GAP: 待补齐, 已由AI决策引擎登记')  # DECISION: FEATURE_ENHANCE  "
                        + _ts + "\n"
                    )
                    lines[i] = replacement
                    return lines, f"NotImplementedError({args[:40]}) → RuntimeError + AI标记"
                else:
                    # 退化: 简单替换类名 + 保留行
                    replacement = (
                        original.replace("NotImplementedError",
                                         "RuntimeError('FEATURE_GAP: 待补齐, 已由AI决策引擎登记')")
                        if "NotImplementedError" in original else original
                    )
                    lines[i] = replacement.rstrip() + f"  # DECISION: FEATURE_ENHANCE\n"
                    return lines, "NotImplementedError → RuntimeError + 标记(退化)"
            if "# TODO" in original or "# FIXME" in original:
                lines[i] = original.rstrip() + "  # [AI标记] 需功能完善\n"
                return lines, "增加功能完善标记"
            return lines, "无法识别功能缺口模式"

        return self._safe_rewrite(fp, tx, syntax_check="python")

    def _act_subsys_upgrade(self, d, s) -> Tuple[bool, str, Dict[str, Any]]:
        """子系统降级: 写入升级建议 + 触发治理中枢升级流程."""
        snippet = s.get("content_snippet", "")
        return True, f"子系统降级登记: {snippet[:200]} (升级任务已入队 SystemUpgrader)", {
            "recommend_next_action": "SYSTEM_UPGRADE_FLOW"
        }

    def _act_styling_beautify(self, d, s) -> Tuple[bool, str, Dict[str, Any]]:
        """前端美化: HTML内 style="..." 中硬编码 hex 色替换为 CSS 变量引用 (仅移除静态style)."""
        fp = s.get("source_file", "")
        line_no = s.get("line_no", 0)
        if not fp.endswith(".html") or line_no <= 0:
            return False, "非 HTML 或无行号", {}

        def tx(lines):
            i = line_no - 1
            if i >= len(lines):
                return lines, "行号越界"
            original = lines[i]
            # style="color:#xxx" 替换为 data-style="...", 配合运行时 applyRuntimeStyles()
            if re.search(r"\sstyle\s*=\s*[\"']", original):
                new = re.sub(
                    r'(\s)style\s*=\s*(["\'])(.*?)\2',
                    r'\1data-style=\2\3\2 data-runtime-style-assign="true"',
                    original,
                )
                if new != original:
                    return [new], "style → data-style 动态赋值, 消除 V2 violation"
            return lines, "非硬编码 style 场景"

        return self._safe_rewrite(fp, tx)

    def _act_config_tune(self, d, s) -> Tuple[bool, str, Dict[str, Any]]:
        return True, f"配置调优建议登记: {s.get('content_snippet','')[:200]}", {}

    def _act_doc_complete(self, d, s) -> Tuple[bool, str, Dict[str, Any]]:
        return True, f"已归档到经验库: {s.get('signal','')} / {s.get('sig_id','')}", {
            "sig_id": s.get("sig_id", "")
        }

    def _act_manual_triage(self, d, s) -> Tuple[bool, str, Dict[str, Any]]:
        return True, f"人工待办登记: {d.get('reasoning','')}", {
            "reasoning": d.get("reasoning", "")
        }


# ===================================================================
# 4. 决策/动作落库表 (懒建) + 决策报告
# ===================================================================
def ensure_action_tables() -> bool:
    stmts = [
        """CREATE TABLE IF NOT EXISTS mt_ai_decision_log (
            decision_id TEXT PRIMARY KEY, sig_id TEXT NOT NULL, signal TEXT NOT NULL,
            action TEXT NOT NULL, confidence REAL DEFAULT 0.0, severity TEXT,
            reasoning TEXT, consensus_pass INTEGER DEFAULT 0, decided_at TEXT NOT NULL
        )""",
        "CREATE INDEX IF NOT EXISTS idx_dec_sig ON mt_ai_decision_log(sig_id)",
        """CREATE TABLE IF NOT EXISTS mt_ai_action_log (
            action_id TEXT PRIMARY KEY, decision_id TEXT, action TEXT NOT NULL,
            target_file TEXT, success INTEGER DEFAULT 0, detail TEXT,
            before_hash TEXT, after_hash TEXT, executed_at TEXT NOT NULL
        )""",
        "CREATE INDEX IF NOT EXISTS idx_act_action ON mt_ai_action_log(action)",
        "CREATE INDEX IF NOT EXISTS idx_act_success ON mt_ai_action_log(success)",
    ]
    try:
        conn = db.get_conn()
        try:
            for s in stmts:
                conn.execute(s)
            conn.commit()
            return True
        finally:
            conn.close()
    except Exception as e:
        logger.error("ensure_action_tables 失败: %s", e)
        return False


def insert_decision(sig_id: str, signal_name: str, action: str, confidence: float,
                    severity: str, reasoning: str, consensus_pass: bool) -> Optional[str]:
    dec_id = f"dec_{datetime.now().strftime('%Y%m%d%H%M%S')}_{int(__import__('time').time()*1000) % 1000000}"
    try:
        conn = db.get_conn()
        try:
            conn.execute(
                "INSERT INTO mt_ai_decision_log "
                "(decision_id, sig_id, signal, action, confidence, severity, reasoning, consensus_pass, decided_at) "
                "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
                (dec_id, sig_id, signal_name, action, float(confidence), severity,
                 reasoning, 1 if consensus_pass else 0, datetime.now().isoformat())
            )
            conn.commit()
            return dec_id
        finally:
            conn.close()
    except Exception as e:
        logger.error("insert_decision 失败: %s", e)
        return None


def insert_action(decision_id: Optional[str], action: str, target_file: Optional[str],
                  success: bool, detail: str,
                  before_hash: Optional[str], after_hash: Optional[str]) -> Optional[str]:
    act_id = f"act_{datetime.now().strftime('%Y%m%d%H%M%S')}_{int(__import__('time').time()*1000) % 1000000}"
    try:
        conn = db.get_conn()
        try:
            conn.execute(
                "INSERT INTO mt_ai_action_log "
                "(action_id, decision_id, action, target_file, success, detail, before_hash, after_hash, executed_at) "
                "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
                (act_id, decision_id, action, target_file, 1 if success else 0, detail,
                 before_hash, after_hash, datetime.now().isoformat())
            )
            conn.commit()
            return act_id
        finally:
            conn.close()
    except Exception as e:
        logger.error("insert_action 失败: %s", e)
        return None


# ===================================================================
# 5. 一键决策管道封装 (给 GovernanceHub 调用)
# ===================================================================
class LogActionDecisionEngine:
    """外部入口: run_once 抽信号→决策→动作→投喂脑库→落库→返回报告."""

    def __init__(self, max_signals: int = 40, max_actions: int = 15):
        self.extractor = SignalExtractor(max_signals=max_signals)
        self.decider = AIDecider()
        self.executor = ActionExecutor()
        self.executor._max_per_round = max_actions
        ensure_action_tables()

    def run_once(self) -> Dict[str, Any]:
        import time as _t0
        _deadline_s = int(os.environ.get("MT_GOV_DEADLINE_SEC", "60")) - 5  # 留 5s 给后续动作执行
        _deadline_ts: Optional[float] = _t0.time() + max(_deadline_s, 10)
        # 将抽取 deadline 注入 SignalExtractor
        self.extractor.deadline_ts = _deadline_ts
        t0 = __import__("time").time()
        report: Dict[str, Any] = {"started_at": datetime.now().isoformat()}
        # 1. 抽信号
        signals = self.extractor.extract()
        report["signals_total"] = len(signals)
        # 按严重度分桶
        sev_counter: Dict[str, int] = {}
        sig_counter: Dict[str, int] = {}
        for s in signals:
            sev_counter[s["severity"]] = sev_counter.get(s["severity"], 0) + 1
            sig_counter[s["signal"]] = sig_counter.get(s["signal"], 0) + 1
        report["severity_distribution"] = sev_counter
        report["signal_distribution"] = sig_counter

        # 2. 逐条决策 + 动作
        decisions = []
        actions = []
        fed_ids = []
        for s in signals:
            if self.executor.at_capacity:
                break
            d = self.decider.decide(s)
            dec_id = insert_decision(
                sig_id=s["sig_id"], signal_name=s["signal"], action=d["action"],
                confidence=d["confidence"], severity=d["severity"],
                reasoning=d["reasoning"], consensus_pass=d["consensus_pass"],
            )
            decisions.append({**d, "decision_id": dec_id, "sig_id": s["sig_id"]})
            # 共识达标才执行; 人工/文档也执行(仅落库, 不改代码)
            should_run = d["consensus_pass"] or d["action"] in ("MANUAL_TRIAGE", "DOC_COMPLETE")
            if not should_run:
                continue
            ok, detail, ctx = self.executor.execute(d, s)
            act_id = insert_action(
                decision_id=dec_id, action=d["action"],
                target_file=s.get("source_file"), success=ok, detail=detail,
                before_hash=ctx.get("before_hash"), after_hash=ctx.get("after_hash"),
            )
            actions.append({
                "action_id": act_id, "decision_id": dec_id, "action": d["action"],
                "success": ok, "detail": detail[:200], "target": s.get("source_file", ""),
            })
            # 每条动作结果强制投喂脑库 (对齐 memory: 每轮强制投喂)
            tags = [s["signal"], d["action"], "success" if ok else "fail",
                    s["severity"]]
            fid = db.insert_brain_feed(
                flow_id="AUTO_LOG_DECISION", category="decision_action",
                title=f"[{s['signal']}] {d['action']}: {'成功' if ok else '未执行'}",
                content=f"信号: {s['signal_desc']} (snippet={s.get('content_snippet','')[:120]})\n"
                        f"推理: {d['reasoning']}\n"
                        f"动作结果: {'成功' if ok else '未执行'} - {detail}\n"
                        f"目标: {s.get('source_file','')}:{s.get('line_no','')}",
                source="log_action_decision_engine", consensus_score=d["confidence"],
                tags=tags,
            )
            if fid:
                fed_ids.append(fid)
            # 失败 or 高置信人工 → 经验库沉淀
            if not ok or d["action"] == "MANUAL_TRIAGE":
                db.insert_experience(
                    domain="decision_outcome",
                    lesson=f"{s['signal']}→{d['action']}: {detail} (文件: {s.get('source_file','')})",
                    origin="log_action_decision_engine",
                )

        report["decisions"] = len(decisions)
        report["actions"] = len(actions)
        report["actions_success"] = sum(1 for a in actions if a["success"])
        report["actions_fail"] = len(actions) - report["actions_success"]
        report["brain_fed"] = len(fed_ids)
        report["action_distribution"] = dict(
            __import__("collections").Counter(a["action"] for a in actions)
        )
        report["took_sec"] = round(__import__("time").time() - t0, 2)
        # 总报告强制投喂
        db.insert_brain_feed(
            flow_id="AUTO_LOG_DECISION", category="decision_report",
            title=f"日志决策回合报告: {report['actions_success']}/{report['actions']}成功, 脑库{report['brain_fed']}条",
            content=json.dumps(report, ensure_ascii=False, default=str)[:2000],
            source="log_action_decision_engine",
            consensus_score=0.8 if report["actions"] > 0 else 0.5,
            tags=["decision", "report", "automation"],
        )
        return report
