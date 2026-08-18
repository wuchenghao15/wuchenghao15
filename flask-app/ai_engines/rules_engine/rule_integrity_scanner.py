"""
规则完整性自检 CLI
================================

扫描 .trae/rules/ 9篇规则文件, 输出:
- RULE_META 完整性 (9/9 必须 ACTIVE)
- 弱约束词剩余数 (应该/建议/推荐/尽量/原则上, 必须=0)
- 违反触发块覆盖率 (每条强制条款必须含违反触发)
- 9篇规则执行覆盖率报告

调用方式:
    python flask-app/ai_engines/rules_engine/rule_integrity_scanner.py
    python flask-app/ai_engines/rules_engine/rule_integrity_scanner.py --json
    python flask-app/ai_engines/rules_engine/rule_integrity_scanner.py --strict
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
from typing import Dict, List

# 兼容直接作为脚本运行和作为模块导入两种情况
if __package__ in (None, ""):
    _SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
    _FLASK_APP_DIR = os.path.abspath(os.path.join(_SCRIPT_DIR, "..", ".."))
    if _FLASK_APP_DIR not in sys.path:
        sys.path.insert(0, _FLASK_APP_DIR)
    from ai_engines.rules_engine.rule_db import RuleDB
    from ai_engines.rules_engine.rule_meta import (
        DEFAULT_RULES_DIR,
        RuleMeta,
        parse_all_rules,
        parse_rule_meta,
        validate_rule_meta,
    )
else:
    from .rule_db import RuleDB
    from .rule_meta import (
        DEFAULT_RULES_DIR,
        RuleMeta,
        parse_all_rules,
        parse_rule_meta,
        validate_rule_meta,
    )


# 弱约束词清单 (禁止在强制条款中使用)
# v2.0: 从6个扩充到20个, 覆盖所有弱约束表达变体
_WEAK_WORDS = [
    "应该",       # → 必须
    "应当",       # → 必须 (v2.0新增, 之前误归为强约束)
    "建议",       # → 必须
    "推荐",       # → 必须
    "尽量",       # → 必须
    "原则上",     # → 必须 (无例外)
    "一般",       # → 必须 (无例外)
    "可考虑",     # → 必须 (v2.0新增)
    "适当",       # → 必须 (v2.0新增, 消除模糊性)
    "酌情",       # → 必须 (v2.0新增, 消除自由裁量)
    "适宜",       # → 必须 (v2.0新增, 不用单字"宜"避免"便宜"误判)
    "最好",       # → 必须 (v2.0新增)
    "尽可能",     # → 必须 (v2.0新增, 消除尽力而为)
    "一般来说",   # → 必须 (v2.0新增, 消除一般性例外)
    "视情况",     # → 必须 (v2.0新增, 消除条件性)
    "根据情况",   # → 必须 (v2.0新增)
    "如有必要",   # → 必须 (v2.0新增, 消除条件性)
    "如有需要",   # → 必须 (v2.0新增)
    "酌量",       # → 必须 (v2.0新增)
    "量力",       # → 必须 (v2.0新增, 消除尽力而为)
]

# 强约束词清单 (允许使用)
_STRONG_WORDS = ["必须", "禁止", "不得", "不允许", "强制"]

# 违反触发块标记
_VIOLATION_TRIGGER_MARKERS = [
    "违反触发",
    "VIOLATION",
    "拦截层",
    "落库",
    "告警",
]


def _count_weak_words(file_path: str) -> int:
    """统计单篇规则文件中弱约束词数量"""
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()
    except OSError:
        return 0
    # 排除 RULE_META 块 + frontmatter
    content_no_meta = re.sub(
        r"<!--\s*RULE_META_START.*?RULE_META_END\s*-->", "", content, flags=re.DOTALL
    )
    content_no_meta = re.sub(r"^---\n.*?\n---", "", content_no_meta, flags=re.DOTALL)
    count = 0
    for word in _WEAK_WORDS:
        count += content_no_meta.count(word)
    return count


def _count_violation_triggers(file_path: str) -> int:
    """统计单篇规则文件中违反触发块数量"""
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()
    except OSError:
        return 0
    count = 0
    for marker in _VIOLATION_TRIGGER_MARKERS:
        count += content.count(marker)
    return count


def _scan_single_rule(file_path: str) -> Dict:
    """扫描单个规则文件"""
    meta = parse_rule_meta(file_path)
    fname = os.path.basename(file_path)

    if meta is None:
        return {
            "file": fname,
            "rule_id": "",
            "rule_version": "",
            "meta_present": False,
            "meta_valid": False,
            "weak_words_count": _count_weak_words(file_path),
            "violation_trigger_count": 0,
            "violations": ["RULE_META 缺失"],
            "status": "FAIL",
        }

    violations = validate_rule_meta(meta)
    weak_count = _count_weak_words(file_path)
    trigger_count = _count_violation_triggers(file_path)

    status = "PASS"
    if violations:
        status = "FAIL"
    if weak_count > 0:
        status = "FAIL"
        violations.append(f"弱约束词剩余 {weak_count} 处 (应=0)")

    return {
        "file": fname,
        "rule_id": meta.rule_id,
        "rule_version": meta.rule_version,
        "meta_present": True,
        "meta_valid": meta.is_valid(),
        "weak_words_count": weak_count,
        "violation_trigger_count": trigger_count,
        "violations": violations,
        "status": status,
    }


def run_integrity_scan(
    rules_dir: str = DEFAULT_RULES_DIR,
    output_json: bool = False,
    strict: bool = False,
) -> int:
    """执行9篇规则完整性自检, 返回 0=PASS, 1=FAIL"""
    if not os.path.isdir(rules_dir):
        print(f"[ERROR] rules 目录不存在: {rules_dir}")
        return 1

    rule_files = [
        os.path.join(rules_dir, f)
        for f in sorted(os.listdir(rules_dir))
        if f.endswith(".md") and not f.startswith("00-")
    ]

    total_rules = 9
    scanned_rules = len(rule_files)
    results: List[Dict] = []

    print(f"[INFO] 扫描 {scanned_rules} 个规则文件 ({rules_dir})")

    for file_path in rule_files:
        result = _scan_single_rule(file_path)
        results.append(result)
        if result["status"] == "PASS":
            print(
                f"[PASS] {result['file']} - META complete, "
                f"{result['weak_words_count']} weak words, "
                f"{result['violation_trigger_count']} triggers"
            )
        else:
            print(
                f"[FAIL] {result['file']} - {result['weak_words_count']} weak words, "
                f"{result['violation_trigger_count']} triggers"
            )
            for v in result["violations"]:
                print(f"       └─ {v}")

    passed_rules = sum(1 for r in results if r["status"] == "PASS")
    failed_rules = scanned_rules - passed_rules
    weak_words_total = sum(r["weak_words_count"] for r in results)
    missing_meta_count = sum(1 for r in results if not r["meta_present"])
    missing_trigger_count = sum(1 for r in results if r["violation_trigger_count"] == 0)

    scan_status = "PASS" if failed_rules == 0 else "FAIL"

    print(f"\n[REPORT] Total: {scanned_rules}/{total_rules}")
    print(f"[REPORT] Pass: {passed_rules}/{scanned_rules}")
    print(f"[REPORT] Fail: {failed_rules}/{scanned_rules}")
    print(f"[REPORT] Weak words remaining: {weak_words_total}")
    print(f"[REPORT] Missing META: {missing_meta_count}")
    print(f"[REPORT] Missing triggers: {missing_trigger_count}")
    print(f"[STATUS] {scan_status}")

    # 落库自检报告
    try:
        rule_db = RuleDB()
        rule_db.insert_integrity_scan(
            total_rules=total_rules,
            scanned_rules=scanned_rules,
            passed_rules=passed_rules,
            failed_rules=failed_rules,
            weak_words_count=weak_words_total,
            missing_meta_count=missing_meta_count,
            missing_trigger_count=missing_trigger_count,
            scan_report_json=json.dumps(
                {"results": results, "rules_dir": rules_dir},
                ensure_ascii=False,
            ),
            scan_status=scan_status,
        )
    except Exception as exc:  # noqa: BLE001
        print(f"[WARN] 落库自检报告失败 (不影响退出码): {exc}")

    if output_json:
        print(
            json.dumps(
                {
                    "total_rules": total_rules,
                    "scanned_rules": scanned_rules,
                    "passed_rules": passed_rules,
                    "failed_rules": failed_rules,
                    "weak_words_total": weak_words_total,
                    "missing_meta_count": missing_meta_count,
                    "missing_trigger_count": missing_trigger_count,
                    "scan_status": scan_status,
                    "results": results,
                },
                ensure_ascii=False,
                indent=2,
            )
        )

    if strict and scan_status != "PASS":
        return 1
    return 0 if scan_status == "PASS" else 1


def main(argv: List[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="MTSCOS rules_engine 完整性自检 CLI")
    parser.add_argument("--rules-dir", default=DEFAULT_RULES_DIR, help="规则目录路径")
    parser.add_argument("--json", action="store_true", help="输出 JSON 格式")
    parser.add_argument("--strict", action="store_true", help="严格模式 (有失败项则退出码=1)")
    args = parser.parse_args(argv)

    return run_integrity_scan(
        rules_dir=args.rules_dir,
        output_json=args.json,
        strict=args.strict,
    )


if __name__ == "__main__":
    sys.exit(main())
