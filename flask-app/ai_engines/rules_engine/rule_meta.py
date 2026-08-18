"""
RULE_META 元数据解析与校验
================================

解析 .trae/rules/ 9篇规则文件头部的 <!-- RULE_META_START ... RULE_META_END --> 块,
校验元数据完整性, 供 rules_engine 各组件统一引用。
"""

from __future__ import annotations

import os
import re
from dataclasses import dataclass, field
from typing import Dict, List, Optional

# 默认规则目录 (相对项目根)
DEFAULT_RULES_DIR = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "..", "..", ".trae", "rules")
)

# RULE_META 块正则 (非贪婪匹配)
_META_PATTERN = re.compile(
    r"<!--\s*RULE_META_START\s*(.*?)\s*RULE_META_END\s*-->",
    re.DOTALL,
)

# 单行 KEY: VALUE 解析正则
_KV_PATTERN = re.compile(r"^([A-Z_]+)\s*:\s*(.+?)\s*$", re.MULTILINE)


@dataclass
class RuleMeta:
    """单篇规则的元数据"""

    rule_id: str = ""
    rule_name: str = ""
    rule_level: str = ""
    rule_version: str = ""
    effective_date: str = ""
    status: str = ""
    violation_code: str = ""
    intercept_layers: List[str] = field(default_factory=list)
    responsible_role: str = ""
    depends_on: List[str] = field(default_factory=list)
    modify_approval_flow: str = ""
    bypass_allowed: bool = True
    last_changed: str = ""
    source_file: str = ""
    raw_meta_text: str = ""

    def is_valid(self) -> bool:
        """校验必填字段"""
        required = [
            self.rule_id,
            self.rule_name,
            self.rule_level,
            self.rule_version,
            self.effective_date,
            self.status,
            self.violation_code,
            self.responsible_role,
            self.modify_approval_flow,
        ]
        return all(required) and self.status == "ACTIVE"

    def to_dict(self) -> Dict:
        return {
            "rule_id": self.rule_id,
            "rule_name": self.rule_name,
            "rule_level": self.rule_level,
            "rule_version": self.rule_version,
            "effective_date": self.effective_date,
            "status": self.status,
            "violation_code": self.violation_code,
            "intercept_layers": self.intercept_layers,
            "responsible_role": self.responsible_role,
            "depends_on": self.depends_on,
            "modify_approval_flow": self.modify_approval_flow,
            "bypass_allowed": self.bypass_allowed,
            "last_changed": self.last_changed,
            "source_file": self.source_file,
        }


def _parse_intercept_layers(value: str) -> List[str]:
    """解析 INTERCEPT_LAYERS: [a, b, c] 格式"""
    if not value:
        return []
    cleaned = value.strip().lstrip("[").rstrip("]")
    return [item.strip() for item in cleaned.split(",") if item.strip()]


def _parse_depends_on(value: str) -> List[str]:
    """解析 DEPENDS_ON: [a, b] 格式"""
    if not value:
        return []
    cleaned = value.strip().lstrip("[").rstrip("]")
    if not cleaned:
        return []
    return [item.strip() for item in cleaned.split(",") if item.strip()]


def _parse_bypass_allowed(value: str) -> bool:
    """解析 BYPASS_ALLOWED: false/true"""
    return value.strip().lower() in ("true", "1", "yes")


def parse_rule_meta(file_path: str) -> Optional[RuleMeta]:
    """解析单个规则文件的 RULE_META 块"""
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()
    except (OSError, IOError) as exc:
        print(f"[ERROR] 读取规则文件失败 {file_path}: {exc}")
        return None

    match = _META_PATTERN.search(content)
    if not match:
        return None

    meta_text = match.group(1)
    meta = RuleMeta(source_file=os.path.basename(file_path), raw_meta_text=meta_text)

    for kv_match in _KV_PATTERN.finditer(meta_text):
        key, value = kv_match.group(1), kv_match.group(2)
        if key == "RULE_ID":
            meta.rule_id = value
        elif key == "RULE_NAME":
            meta.rule_name = value
        elif key == "RULE_LEVEL":
            meta.rule_level = value
        elif key == "RULE_VERSION":
            meta.rule_version = value
        elif key == "EFFECTIVE_DATE":
            meta.effective_date = value
        elif key == "STATUS":
            meta.status = value
        elif key == "VIOLATION_CODE":
            meta.violation_code = value
        elif key == "INTERCEPT_LAYERS":
            meta.intercept_layers = _parse_intercept_layers(value)
        elif key == "RESPONSIBLE_ROLE":
            meta.responsible_role = value
        elif key == "DEPENDS_ON":
            meta.depends_on = _parse_depends_on(value)
        elif key == "MODIFY_APPROVAL_FLOW":
            meta.modify_approval_flow = value
        elif key == "BYPASS_ALLOWED":
            meta.bypass_allowed = _parse_bypass_allowed(value)
        elif key == "LAST_CHANGED":
            meta.last_changed = value

    return meta


def parse_all_rules(rules_dir: str = DEFAULT_RULES_DIR) -> List[RuleMeta]:
    """扫描 rules 目录, 解析所有 .md 文件的 RULE_META"""
    results: List[RuleMeta] = []
    if not os.path.isdir(rules_dir):
        print(f"[WARN] rules 目录不存在: {rules_dir}")
        return results

    for fname in sorted(os.listdir(rules_dir)):
        if not fname.endswith(".md"):
            continue
        if fname.startswith("00-"):
            # 总索引文件本身不需要 RULE_META
            continue
        file_path = os.path.join(rules_dir, fname)
        meta = parse_rule_meta(file_path)
        if meta is None:
            print(f"[WARN] 缺失 RULE_META: {fname}")
            continue
        results.append(meta)

    return results


def validate_rule_meta(meta: RuleMeta) -> List[str]:
    """校验元数据完整性, 返回违规项列表 (空表示通过)"""
    violations: List[str] = []
    if not meta.is_valid():
        violations.append(f"{meta.source_file}: 必填字段缺失或 STATUS≠ACTIVE")
    if meta.bypass_allowed:
        violations.append(
            f"{meta.source_file}: BYPASS_ALLOWED=true 违反铁律 (必须 false)"
        )
    if not meta.intercept_layers:
        violations.append(f"{meta.source_file}: INTERCEPT_LAYERS 为空")
    if not meta.violation_code:
        violations.append(f"{meta.source_file}: VIOLATION_CODE 为空")
    return violations
