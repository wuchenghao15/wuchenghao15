#!/usr/bin/env python3
"""
auto_sniff_engine.py — 仙女座 · 自动嗅探引擎
==============================================
扫描 flask-app/ 下所有路由/引擎/中间件的 Python 源码，
检测代码味道并产出结构化建议（进 mt_ai_suggestion_pool）。

嗅探类型:
  1. endpoint_duplicate    — 同函数多装饰 @_bp.route → endpoint 冲突
  2. missing_import        — 用了 functools.wraps 但没 import 等
  3. decorator_order       — @bp.route 在 @system_container 上面（正确顺序是 route 在上）
  4. hardcoded_i18n        — 中文硬编码字符串 → 建议冰山 store_content_4lang
  5. legacy_kwargs         — @system_container(page_name=...) 过时调用
  6. bare_except           — except: 没有指定异常类型
  7. todo_fixme            — 源码里 TODO/FIXME/HACK 标记

产出:
  mt_ai_suggestion_pool (source_name='auto_sniff_engine', flow_id='auto_sniff_v1')

用法:
  python3 auto_sniff_engine.py run          # 完整一轮嗅探 + 入库
  python3 auto_sniff_engine.py scan         # 只扫描不入库（dry-run）
  python3 auto_sniff_engine.py summary      # 上一轮嗅探结果
  python3 auto_sniff_engine.py routes       # 只扫 routes/ 目录
  python3 auto_sniff_engine.py --target=x   # 只扫指定文件/目录
"""
import argparse, json, os, re, sqlite3, sys, time
from pathlib import Path

# ── 路径常量 ──
BASE = Path(__file__).resolve().parent.parent
DB = BASE / "database" / "app.db"
ROUTES_DIR = BASE / "routes"
ENGINES_DIR = BASE / "engines"
MIDDLEWARES_DIR = BASE / "app" / "middlewares"

# ── 嗅探规则 ──
SNIFF_RULES = [
    {
        "id": "endpoint_duplicate",
        "name": "Flask Endpoint 重复",
        "desc": "同一个函数被 @_bp.route 装饰多次且未显式指定唯一 endpoint",
        "severity": "HIGH",
        # 匹配: 同函数体附近出现多次 @_bp.route 且装饰同一个 def
    },
    {
        "id": "missing_import",
        "name": "Missing Import",
        "desc": "使用了模块但文件顶部没 import（如 @wraps 缺 from functools import wraps）",
        "severity": "MEDIUM",
    },
    {
        "id": "decorator_order",
        "name": "装饰器顺序错误",
        "desc": "@bp.route 应该在 @system_container 之上（route 先注册蓝图）",
        "severity": "LOW",
    },
    {
        "id": "hardcoded_i18n",
        "name": "硬编码中文",
        "desc": "Python 字符串中的中文字面量 → 建议走冰山 store_content_4lang",
        "severity": "INFO",
    },
    {
        "id": "legacy_kwargs",
        "name": "过时 @system_container 调用",
        "desc": "使用 page_name= 等已废弃参数",
        "severity": "MEDIUM",
    },
    {
        "id": "bare_except",
        "name": "裸 except",
        "desc": "except: 未指定异常类型 → 会吞掉 KeyboardInterrupt",
        "severity": "LOW",
    },
    {
        "id": "todo_fixme",
        "name": "TODO/FIXME 标记",
        "desc": "源码中有待办标记 — 可能需要优先处理",
        "severity": "INFO",
    },
]


# ═══════════════════════════════════════════════════════════════════
# 嗅探器: 每个 sniff_* 函数返回 list[dict]
# ═══════════════════════════════════════════════════════════════════

def _read_lines(path: Path) -> list[str]:
    try:
        return path.read_text(encoding='utf-8', errors='replace').splitlines()
    except Exception:
        return []


def _s(line) -> str:
    """防御性 .strip() — 确保 line 是 str 再 strip()"""
    if not isinstance(line, str):
        try: line = str(line)
        except: return ''
    return line.strip()


def _iter_py_files(root: Path) -> list[Path]:
    if not root.exists():
        return []
    return sorted(root.rglob('*.py'))


def sniff_endpoint_duplicate(file_path: Path, lines: list[str]) -> list[dict]:
    """检测: 同函数体被多次 @_bp.route 装饰且未显式 endpoint="""
    findings = []
    route_stack = []  # 待配对的装饰器
    current_func = None
    func_line = -1

    for i, line in enumerate(lines):
        ln = i + 1
        stripped = line.strip()

        # function def
        m = re.match(r'^def\s+(\w+)\s*\(', line)
        if m:
            # 结算上一个函数
            if current_func and len(route_stack) >= 2:
                # 检查这些 route 有没有都带 endpoint=
                no_endpoint = [ln_ for ln_ in route_stack if 'endpoint=' not in lines[ln_-1]]
                if len(no_endpoint) >= 2:
                    findings.append({
                        "file": str(file_path.relative_to(BASE)),
                        "line": func_line,
                        "rule_id": "endpoint_duplicate",
                        "severity": "HIGH",
                        "detail": f"函数 '{current_func}' 被 {len(route_stack)} 个 route 装饰，其中 {len(no_endpoint)} 个未显式指定 endpoint=（Flask 会用函数名自动生成，导致冲突）",
                        "suggestion": f"给 @{file_path.parent.name}_bp.route 的非主路径加 endpoint='xxx_slash' 或 endpoint='xxx_alias'",
                        "func_name": current_func,
                        "route_lines": route_stack,
                    })
            current_func = m.group(1)
            func_line = ln
            route_stack = []
            continue

        # route decorator — 任何 @xxx_bp.route 或 @_bp.route
        if re.match(r'@[\w_]*bp\.route\(', stripped, re.IGNORECASE) or re.match(r'@_bp\.route\(', stripped):
            route_stack.append(ln)

    # 文件末尾结算最后一个
    if current_func and len(route_stack) >= 2:
        no_endpoint = [ln_ for ln_ in route_stack if 'endpoint=' not in lines[ln_-1]]
        if len(no_endpoint) >= 2:
            findings.append({
                "file": str(file_path.relative_to(BASE)),
                "line": func_line,
                "rule_id": "endpoint_duplicate",
                "severity": "HIGH",
                "detail": f"函数 '{current_func}' 被 {len(route_stack)} 个 route 装饰，其中 {len(no_endpoint)} 个未显式指定 endpoint=",
                "suggestion": "给非主路径加 endpoint='xxx_slash' / endpoint='xxx_alias'",
            })

    return findings


def sniff_missing_import(file_path: Path, lines: list[str]) -> list[dict]:
    """检测: 使用了 functools / typing / datetime 等但文件顶部没 import"""
    findings = []
    file_text = '\n'.join(lines)

    # 收集已有 imports
    imported = set()
    for line in lines[:60]:  # 顶部 60 行
        m1 = re.match(r'^import\s+(\w+)', line)
        if m1: imported.add(m1.group(1))
        m2 = re.match(r'^from\s+([\w\.]+)\s+import', line)
        if m2: imported.add(m2.group(1).split('.')[0])

    # 检查可疑使用模式
    suspicious_patterns = [
        ('wraps', 'functools', 'from functools import wraps'),
        ('partial', 'functools', 'from functools import partial'),
        ('lru_cache', 'functools', 'from functools import lru_cache'),
        ('TypeVar', 'typing', 'from typing import TypeVar'),
        ('datetime', 'datetime', 'from datetime import datetime, timedelta'),
        ('timedelta', 'datetime', 'from datetime import timedelta'),
        ('Optional', 'typing', 'from typing import Optional'),
        ('sqlite3', 'sqlite3', 'import sqlite3'),
        ('uuid', 'uuid', 'import uuid'),
    ]

    for symbol, module, import_stmt in suspicious_patterns:
        if module in imported:
            continue
        # 跳过符号本身就是模块名的情况
        if symbol == module:
            continue
        # 找使用（跳过注释和 docstring）
        for i, line in enumerate(lines):
            if line.strip().startswith('#'):
                continue
            # 跳过顶部 import 区域
            if i < 10 and ('import' in line or 'from ' in line):
                continue
            # 检查 symbol 作为函数调用或类型使用
            if re.search(rf'\b{symbol}\s*\(', line) or re.search(rf'\b{symbol}\[', line):
                findings.append({
                    "file": str(file_path.relative_to(BASE)),
                    "line": i + 1,
                    "rule_id": "missing_import",
                    "severity": "MEDIUM",
                    "detail": f"使用了 '{symbol}()' 但文件顶部未 import '{module}'",
                    "suggestion": f"加一行: {import_stmt}",
                    "symbol": symbol,
                    "missing_module": module,
                })
                break  # 每文件每 symbol 只报一次

    return findings


def sniff_decorator_order(file_path: Path, lines: list[str]) -> list[dict]:
    """检测: 单个 route 和 sc 紧邻且顺序反了（多 route 同函数场景跳过）"""
    findings = []
    rel = str(file_path.relative_to(BASE))
    if not rel.startswith('routes/'):
        return findings

    window = []

    for i, line in enumerate(lines):
        stripped = line.strip()
        if stripped.startswith('@'):
            window.append((stripped, i + 1))
        elif window and (stripped.startswith('def ') or stripped.startswith('class ')):
            window_text = [w[0] for w in window]
            route_positions = [j for j, d in enumerate(window_text) if '.route(' in d]
            sc_positions = [j for j, d in enumerate(window_text) if 'system_container' in d]
            # 只在恰好 1 个 route + 恰好 1 个 sc 时才查顺序
            if len(route_positions) == 1 and len(sc_positions) == 1:
                r_idx = route_positions[0]
                s_idx = sc_positions[0]
                # Flask 装饰器: 最下面（最靠近 def）的先应用 → route 应该最靠近 def
                if r_idx < s_idx and (s_idx - r_idx) == 1:
                    findings.append({
                        "file": rel,
                        "line": window[r_idx][1],
                        "rule_id": "decorator_order",
                        "severity": "LOW",
                        "detail": "@system_container 紧邻写在 @bp.route 下方 — Flask 装饰器从下往上应用，route 会覆盖 sc",
                        "suggestion": "交换两者顺序: @bp.route 在最下（最靠近 def），@system_container 在其上方",
                    })
            window = []

    return findings


def sniff_hardcoded_i18n(file_path: Path, lines: list[str]) -> list[dict]:
    """检测: Python 字符串中包含中文字面量 → 建议走冰山"""
    findings = []
    # 跳过的目录/文件
    skip_dirs = {'test', 'tests', '__pycache__'}
    rel = str(file_path.relative_to(BASE))
    if any(d in rel for d in skip_dirs):
        return findings
    # 跳过 i18n_engine.py / iceberg 引擎（本身就是处理 i18n 的）
    if 'i18n' in file_path.name or 'iceberg' in file_path.name:
        return findings

    for i, line in enumerate(lines):
        # 跳过 import 行、注释行、docstring 行
        stripped = line.strip()
        if stripped.startswith('#'):
            continue
        if stripped.startswith(('import ', 'from ')):
            continue
        # 跳过明显的日志模块配置
        if stripped.startswith('logger') or stripped.startswith('LOG'):
            continue
        # 匹配字符串中的中文（至少 2 个中文字符）
        m = re.search(r'[\u4e00-\u9fff]{2,}', line)
        if m:
            # 进一步过滤：只认字符串字面量
            in_string = re.search(r'["\'].*[\u4e00-\u9fff].*["\']', line)
            if in_string:
                findings.append({
                    "file": str(file_path.relative_to(BASE)),
                    "line": i + 1,
                    "rule_id": "hardcoded_i18n",
                    "severity": "INFO",
                    "detail": f"硬编码中文: {m.group()}",
                    "suggestion": "考虑用冰山 store_content_4lang() 管理多语言",
                    "snippet": in_string.group()[:80],
                })
    return findings


def sniff_legacy_kwargs(file_path: Path, lines: list[str]) -> list[dict]:
    """检测: @system_container(page_name=...) 过时参数"""
    findings = []
    for i, line in enumerate(lines):
        if re.search(r'@system_container\(.*page_name\s*=', line):
            findings.append({
                "file": str(file_path.relative_to(BASE)),
                "line": i + 1,
                "rule_id": "legacy_kwargs",
                "severity": "MEDIUM",
                "detail": "@system_container 仍在使用 page_name= 过时参数（已由 **kwargs 吸收）",
                "suggestion": "可以移除 page_name 参数了，system_container 已加 **kwargs",
            })
    return findings


def sniff_bare_except(file_path: Path, lines: list[str]) -> list[dict]:
    """检测: except: 未指定类型（会吞 KeyboardInterrupt/SystemExit）"""
    findings = []
    for i, line in enumerate(lines):
        stripped = line.strip()
        if stripped == 'except:' or stripped == 'except Exception:':
            if stripped == 'except:':
                findings.append({
                    "file": str(file_path.relative_to(BASE)),
                    "line": i + 1,
                    "rule_id": "bare_except",
                    "severity": "LOW",
                    "detail": "裸 except: 会吞掉 KeyboardInterrupt/SystemExit",
                    "suggestion": "改成 except Exception: 或指定具体异常类型",
                })
    return findings


def sniff_todo_fixme(file_path: Path, lines: list[str]) -> list[dict]:
    """检测: TODO / FIXME / HACK 标记"""
    findings = []
    patterns = [
        (r'TODO[:\s]', 'TODO'),
        (r'FIXME[:\s]', 'FIXME'),
        (r'HACK[:\s]', 'HACK'),
        (r'XXX[:\s]', 'XXX'),
    ]
    for i, line in enumerate(lines):
        for pat, tag in patterns:
            if re.search(pat, line, re.IGNORECASE):
                findings.append({
                    "file": str(file_path.relative_to(BASE)),
                    "line": i + 1,
                    "rule_id": "todo_fixme",
                    "severity": "INFO",
                    "detail": f"[{tag}] {line.strip()[:100]}",
                    "suggestion": "TODO/FIXME — 仙女座嗅探标记，可能需要优先处理",
                    "tag": tag,
                })
                break  # 每行只记一次
    return findings


# ═══════════════════════════════════════════════════════════════════
# 主流程
# ═══════════════════════════════════════════════════════════════════

def _safe_call(name: str, fn, file_path, lines) -> list[dict]:
    """每个 sniff_* 调用的安全 wrapper — 任何异常都不中断整个嗅探"""
    try:
        return list(fn(file_path, lines))
    except AttributeError as e:
        print(f"  ⚠️ [{name}] AttributeError in {file_path.name}: {e}")
        return []
    except Exception as e:
        print(f"  ⚠️ [{name}] {type(e).__name__} in {file_path.name}: {e}")
        return []


def run_sniff(target_dirs: list[Path] | None = None, include_info: bool = False) -> list[dict]:
    """对指定目录（默认 routes + engines + middlewares）跑一轮完整嗅探"""
    if target_dirs is None:
        target_dirs = [ROUTES_DIR, ENGINES_DIR, MIDDLEWARES_DIR]

    all_findings = []
    files_scanned = 0

    for root in target_dirs:
        for f in _iter_py_files(root):
            # 跳过 auto_gen_ 目录（自动生成的，下次会重写）
            fp_str = str(f)
            if 'auto_gen_' in fp_str:
                continue
            # 跳过超大噪音文件（本身就是文档/模板驱动的）
            if f.name in ('server_real_db.py', 'modular_start.py'):
                continue

            lines = _read_lines(f)
            if not lines:
                continue
            files_scanned += 1

            all_findings += _safe_call('endpoint_duplicate', sniff_endpoint_duplicate, f, lines)
            all_findings += _safe_call('missing_import', sniff_missing_import, f, lines)
            all_findings += _safe_call('decorator_order', sniff_decorator_order, f, lines)
            if include_info:
                all_findings += _safe_call('hardcoded_i18n', sniff_hardcoded_i18n, f, lines)
            all_findings += _safe_call('legacy_kwargs', sniff_legacy_kwargs, f, lines)
            all_findings += _safe_call('bare_except', sniff_bare_except, f, lines)
            if include_info:
                all_findings += _safe_call('todo_fixme', sniff_todo_fixme, f, lines)

    # 严重度排序
    sev_rank = {"HIGH": 0, "MEDIUM": 1, "LOW": 2, "INFO": 3}
    all_findings.sort(key=lambda x: sev_rank.get(x["severity"], 99))

    print(f"\n🔍 auto_sniff_engine: 扫描 {files_scanned} 文件 → 发现 {len(all_findings)} 项")
    by_sev = {}
    for f in all_findings:
        by_sev[f["severity"]] = by_sev.get(f["severity"], 0) + 1
    print(f"  严重度分布: {by_sev}")

    return all_findings


def write_suggestions(findings: list[dict]) -> int:
    """把嗅探结果写入 mt_ai_suggestion_pool"""
    conn = sqlite3.connect(str(DB), timeout=15)
    conn.execute('PRAGMA busy_timeout=15000')
    ts = time.strftime('%Y-%m-%d %H:%M:%S')
    inserted = 0

    for f in findings:
        rule = next((r for r in SNIFF_RULES if r["id"] == f["rule_id"]), None)
        rule_name = rule["name"] if rule else f["rule_id"]

        # 建议标题: [severity] rule_name — file:line
        title = f"[{f['severity']}] {rule_name} — {f['file']}:{f.get('line','?')}"
        # 建议正文
        body = f"## {rule_name}\n\n**详情**: {f['detail']}\n\n**建议**: {f['suggestion']}\n\n**文件**: {f['file']}\n**行号**: {f.get('line','?')}"
        meta = json.dumps({
            "rule_id": f["rule_id"],
            "severity": f["severity"],
            "file": f["file"],
            "line": f.get("line"),
            "func_name": f.get("func_name"),
            "source": "auto_sniff_engine",
            "discovered_at": ts,
        }, ensure_ascii=False)

        try:
            conn.execute("""
                INSERT INTO mt_ai_suggestion_pool
                (source_type, source_name, suggestion_text, priority,
                 feasibility_score, value_score, cost_score, risk_score,
                 status, flow_id, meta_json, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, 'EVALUATED', ?, ?, ?)
            """, (
                "CODE_SNIFF",
                "auto_sniff_engine",
                body,
                {"HIGH": 9, "MEDIUM": 7, "LOW": 5, "INFO": 3}.get(f["severity"], 5),
                0.90,  # feasibility: sniffer 输出的都是可验证的
                {"HIGH": 0.90, "MEDIUM": 0.75, "LOW": 0.50, "INFO": 0.30}.get(f["severity"], 0.50),
                0.10,  # cost: 修复通常一行代码
                0.05,  # risk: 自动嗅探建议风险极低
                f"auto_sniff_{f['rule_id']}",
                meta,
                ts,
            ))
            inserted += 1
        except sqlite3.IntegrityError:
            pass  # 重复 flow_id 跳过
        except Exception as e:
            print(f"  ⚠️ write err: {e}")

    conn.commit()
    conn.close()
    print(f"  ✅ 入库: {inserted} / {len(findings)}")
    return inserted


def run_sniff_cycle(target_dirs: list[Path] | None = None) -> dict:
    """完整一轮嗅探 + 入库 — andromeda_core Loop 7 调用入口"""
    t0 = time.time()
    findings = run_sniff(target_dirs)
    inserted = write_suggestions(findings)

    elapsed = round(time.time() - t0, 2)
    result = {
        "status": "DONE",
        "total_findings": len(findings),
        "inserted_to_pool": inserted,
        "elapsed_seconds": elapsed,
        "top_issues": [
            {"severity": f["severity"], "rule": f["rule_id"], "file": f["file"], "line": f.get("line"), "detail": f["detail"][:60]}
            for f in findings[:5]
        ],
        "rule_counts": {
            r["id"]: sum(1 for f in findings if f["rule_id"] == r["id"])
            for r in SNIFF_RULES
        },
    }
    print(f"  ⏱️ 耗时: {elapsed}s")
    return result


def sniff_summary() -> dict:
    """查上一轮嗅探结果"""
    conn = sqlite3.connect(str(DB), timeout=15)
    conn.row_factory = sqlite3.Row

    total = conn.execute("SELECT COUNT(*) FROM mt_ai_suggestion_pool WHERE source_name='auto_sniff_engine'").fetchone()[0]
    by_sev = conn.execute("""
        SELECT json_extract(meta_json, '$.severity') as sev, COUNT(*) as cnt
        FROM mt_ai_suggestion_pool WHERE source_name='auto_sniff_engine'
        GROUP BY sev
    """).fetchall()
    by_rule = conn.execute("""
        SELECT json_extract(meta_json, '$.rule_id') as rule_id, COUNT(*) as cnt
        FROM mt_ai_suggestion_pool WHERE source_name='auto_sniff_engine'
        GROUP BY rule_id ORDER BY cnt DESC
    """).fetchall()
    recent = conn.execute("""
        SELECT suggestion_id, substr(suggestion_text, 1, 80) as text,
               json_extract(meta_json, '$.severity') as sev,
               created_at
        FROM mt_ai_suggestion_pool
        WHERE source_name='auto_sniff_engine'
        ORDER BY created_at DESC LIMIT 10
    """).fetchall()

    conn.close()
    return {
        "total_sniffed": total,
        "by_severity": {r["sev"] or "NONE": r["cnt"] for r in by_sev},
        "by_rule": {r["rule_id"] or "NONE": r["cnt"] for r in by_rule},
        "recent": [dict(r) for r in recent],
    }


# ═══════════════════════════════════════════════════════════════════
# CLI
# ═══════════════════════════════════════════════════════════════════

def main():
    p = argparse.ArgumentParser(description="仙女座自动嗅探引擎")
    p.add_argument("cmd", choices=["run", "scan", "summary", "routes", "engines"], default="run")
    p.add_argument("--target", default=None, help="只扫描指定目录/文件")
    args = p.parse_args()

    targets = None
    if args.target:
        t = Path(args.target)
        targets = [t] if t.exists() else None

    if args.cmd == "run":
        result = run_sniff_cycle(targets)
        print(f"\n{'='*50}")
        print(f"  嗅探完成: {result['total_findings']} 项 / 入库 {result['inserted_to_pool']} / 耗时 {result['elapsed_seconds']}s")
        print(f"  规则分布: {result['rule_counts']}")
        print(f"{'='*50}")

    elif args.cmd == "scan":
        findings = run_sniff(targets)
        for f in findings[:20]:
            print(f"  [{f['severity']}] {f['rule_id']:20s} {f['file']}:{f.get('line','?')}  — {f['detail'][:60]}")

    elif args.cmd == "summary":
        s = sniff_summary()
        print(json.dumps(s, ensure_ascii=False, indent=2, default=str))

    elif args.cmd == "routes":
        run_sniff_cycle([ROUTES_DIR])

    elif args.cmd == "engines":
        run_sniff_cycle([ENGINES_DIR])


if __name__ == "__main__":
    main()
