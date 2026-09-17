#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
规则弱约束词自动修复引擎 (Rule Strengthener Engine)
=====================================================
扫描 .trae/rules/ 9篇规则文件, 将弱约束词替换为强约束词
v2.0: 弱约束词从6个扩充到20个, 覆盖所有弱约束表达变体
弱约束词: 应该/应当/建议/推荐/尽量/原则上/一般/可考虑/适当/酌情/适宜/最好/尽可能/一般来说/视情况/根据情况/如有必要/如有需要/酌量/量力
强约束词: 必须/禁止/不得/不允许/强制

策略:
  1. 保护 RULE_META 块 和 YAML frontmatter (不替换)
  2. 表格行(|开头): 弱约束词→"标准"/"默认"/"强制"
  3. 普通行: 弱约束词→"必须"/"强制"/"不得"
  4. 代码块(```内部): 不替换
  5. 替换后重新扫描验证: 弱约束词=0
"""
import os
import re
import sys
from datetime import datetime

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RULES_DIR = os.path.join(ROOT, "..", ".trae", "rules")

# v2.0: 弱约束词 → 强约束词映射 (20个词)
# 表格行替换 (表格内用"标准"/"默认"更自然)
REPLACE_TABLE = {
    "建议": "标准",
    "推荐": "标准",
    "一般": "默认",
    "应该": "必须",
    "应当": "必须",
    "尽量": "必须",
    "原则上": "强制",
    "可考虑": "标准",
    "适当": "标准",
    "酌情": "标准",
    "适宜": "标准",
    "最好": "标准",
    "尽可能": "标准",
    "一般来说": "默认",
    "视情况": "默认",
    "根据情况": "默认",
    "如有必要": "强制",
    "如有需要": "强制",
    "酌量": "标准",
    "量力": "标准",
}

# 普通行替换 (强制条款用"必须"/"强制"/"不得")
REPLACE_NORMAL = {
    "原则上": "强制",
    "应该": "必须",
    "应当": "必须",
    "建议": "必须",
    "推荐": "强制",
    "尽量": "必须",
    "一般": "默认",
    "可考虑": "必须",
    "适当": "必须",
    "酌情": "必须",
    "适宜": "必须",
    "最好": "必须",
    "尽可能": "必须",
    "一般来说": "强制",
    "视情况": "必须",
    "根据情况": "必须",
    "如有必要": "必须",
    "如有需要": "必须",
    "酌量": "必须",
    "量力": "必须",
}

WEAK_WORDS = [
    "应该", "应当", "建议", "推荐", "尽量", "原则上", "一般",
    "可考虑", "适当", "酌情", "适宜", "最好", "尽可能",
    "一般来说", "视情况", "根据情况", "如有必要", "如有需要",
    "酌量", "量力",
]


def _is_table_row(line: str) -> bool:
    """是否为表格行"""
    stripped = line.strip()
    return stripped.startswith("|") or stripped.startswith("|")


def _is_code_fence(line: str) -> bool:
    """是否为代码块边界"""
    return line.strip().startswith("```")


def _is_meta_block(line: str) -> bool:
    """是否为RULE_META块边界"""
    return "RULE_META" in line


def _replace_weak_words_in_file(file_path: str) -> dict:
    """替换单个规则文件中的弱约束词
    返回: {file, total_replaced, details[], remaining_weak}"""
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()
    except OSError as e:
        return {"file": os.path.basename(file_path), "error": str(e),
                "total_replaced": 0, "remaining_weak": -1}

    lines = content.split("\n")
    in_meta = False
    in_code = False
    total_replaced = 0
    details = []

    new_lines = []
    for i, line in enumerate(lines, 1):
        # RULE_META 块检测
        if "RULE_META_START" in line:
            in_meta = True
            new_lines.append(line)
            continue
        if "RULE_META_END" in line:
            in_meta = False
            new_lines.append(line)
            continue
        if in_meta:
            new_lines.append(line)
            continue

        # 代码块检测
        if _is_code_fence(line):
            in_code = not in_code
            new_lines.append(line)
            continue
        if in_code:
            new_lines.append(line)
            continue

        # YAML frontmatter 跳过
        if i <= 3 and line.strip() == "---":
            new_lines.append(line)
            continue

        # 根据行类型选择替换映射
        if _is_table_row(line):
            replace_map = REPLACE_TABLE
        else:
            replace_map = REPLACE_NORMAL

        # 执行替换
        original_line = line
        for weak, strong in replace_map.items():
            if weak in line:
                count = line.count(weak)
                line = line.replace(weak, strong)
                total_replaced += count
                details.append({
                    "line": i,
                    "word": weak,
                    "to": strong,
                    "context": original_line.strip()[:80],
                })

        new_lines.append(line)

    # 写回文件
    new_content = "\n".join(new_lines)
    if total_replaced > 0:
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(new_content)

    # 统计剩余弱约束词
    content_no_meta = re.sub(
        r"<!--\s*RULE_META_START.*?RULE_META_END\s*-->", "",
        new_content, flags=re.DOTALL,
    )
    content_no_meta = re.sub(
        r"^---\n.*?\n---", "", content_no_meta, flags=re.DOTALL,
    )
    remaining = sum(content_no_meta.count(w) for w in WEAK_WORDS)

    return {
        "file": os.path.basename(file_path),
        "total_replaced": total_replaced,
        "remaining_weak": remaining,
        "details": details[:20],  # 最多展示20条
    }


def strengthen_all_rules() -> list:
    """扫描并修复所有规则文件"""
    rules_dir = os.path.abspath(RULES_DIR)
    if not os.path.isdir(rules_dir):
        print(f"[ERROR] rules目录不存在: {rules_dir}")
        return []

    md_files = sorted([
        f for f in os.listdir(rules_dir)
        if f.endswith(".md") and not f.startswith("00-")
    ])

    print(f"{'='*60}")
    print(f"  规则弱约束词自动修复引擎")
    print(f"{'='*60}")
    print(f"  扫描目录: {rules_dir}")
    print(f"  规则文件: {len(md_files)} 篇")
    print(f"  弱约束词: {', '.join(WEAK_WORDS)}")
    print(f"{'='*60}")

    results = []
    for md_file in md_files:
        file_path = os.path.join(rules_dir, md_file)
        print(f"\n--- 修复: {md_file} ---")
        r = _replace_weak_words_in_file(file_path)
        results.append(r)

        if r.get("error"):
            print(f"  ERROR: {r['error']}")
        else:
            print(f"  替换: {r['total_replaced']} 处")
            print(f"  剩余弱约束词: {r['remaining_weak']}")
            if r["total_replaced"] > 0:
                print(f"  替换明细 (最多20条):")
                for d in r["details"]:
                    print(f"    L{d['line']:4d} [{d['word']}→{d['to']}] {d['context'][:60]}...")

    # 汇总
    total_all = sum(r.get("total_replaced", 0) for r in results)
    remaining_all = sum(r.get("remaining_weak", 0) for r in results)
    print(f"\n{'='*60}")
    print(f"  汇总: 替换 {total_all} 处, 剩余弱约束词 {remaining_all} 处")
    if remaining_all == 0:
        print(f"  ✅ 弱约束词清零!")
    else:
        print(f"  ⚠️ 仍有 {remaining_all} 处弱约束词 (可能在代码块或表格头中)")
    print(f"{'='*60}")

    return results


def verify_zero_weak_words() -> bool:
    """验证所有规则文件弱约束词=0"""
    rules_dir = os.path.abspath(RULES_DIR)
    if not os.path.isdir(rules_dir):
        return False

    md_files = [
        f for f in os.listdir(rules_dir)
        if f.endswith(".md") and not f.startswith("00-")
    ]

    all_zero = True
    for md_file in md_files:
        file_path = os.path.join(rules_dir, md_file)
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()
        except OSError:
            continue

        # 排除 RULE_META 和 YAML
        content_no_meta = re.sub(
            r"<!--\s*RULE_META_START.*?RULE_META_END\s*-->", "",
            content, flags=re.DOTALL,
        )
        content_no_meta = re.sub(
            r"^---\n.*?\n---", "", content_no_meta, flags=re.DOTALL,
        )
        count = sum(content_no_meta.count(w) for w in WEAK_WORDS)

        status = "✅" if count == 0 else "❌"
        print(f"  {status} {md_file}: {count} weak words")
        if count > 0:
            all_zero = False

    return all_zero


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "verify":
        print("=== 弱约束词验证 ===")
        ok = verify_zero_weak_words()
        sys.exit(0 if ok else 1)
    else:
        strengthen_all_rules()
        print("\n=== 验证 ===")
        verify_zero_weak_words()
