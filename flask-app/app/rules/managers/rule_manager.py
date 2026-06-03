# -*- coding: utf-8 -*-
# MTSCOS AI Project 规则管理器 - 升级版本
"""
规则管理器负责规则的存储,检索,添加,更新和删除.
支持规则优先级、规则冲突检测、规则版本管理.
"""

from typing import Dict, Any, List, Optional
import uuid
import json
from threading import Lock

try:
    from app.utils.logging import logger
except ImportError:
    import logging
    logger = logging.getLogger(__name__)
    logging.basicConfig(level=logging.INFO)

try:
    from app.rules import RULE_STATUS, RULE_TYPES
except ImportError:
    RULE_STATUS = {"ACTIVE": "active", "INACTIVE": "inactive", "DISABLED": "disabled"}
    RULE_TYPES = {"VALIDATION": "validation", "DECISION": "decision", "FILTER": "filter"}

class RuleManager:
    """规则管理器 - 升级版本"""

    def __init__(self):
        self._rules: Dict[str, Dict[str, Any]] = {}
        self._rules_by_type: Dict[str, Dict[str, str]] = {}
        self._rules_by_priority: Dict[int, List[str]] = {}
        self._sources = []
        self._lock = Lock()
        self._rule_versions: Dict[str, List[Dict]] = {}

    def load_all_rules(self):
        """从所有规则源加载规则"""
        logger.info("从所有规则源加载规则...")

        try:
            from app.rules.sources.file_source import FileRuleSource
            from app.rules.sources.database_source import DatabaseRuleSource

            file_source = FileRuleSource()
            self.load_rules_from_source(file_source)

            db_source = DatabaseRuleSource()
            self.load_rules_from_source(db_source)

        except ImportError:
            logger.warning("规则源模块未找到,跳过外部加载")

        logger.info(f"共加载 {len(self._rules)} 个规则")

    def load_rules_from_source(self, source):
        """从指定规则源加载规则"""
        try:
            rules = source.load_rules()
            for rule in rules:
                self.add_rule(rule)
            logger.info(f"从 {source.__class__.__name__} 加载了 {len(rules)} 个规则")
        except Exception as e:
            logger.error(f"从 {source.__class__.__name__} 加载规则失败: {str(e)}")

    def add_rule(self, rule: Dict[str, Any]) -> str:
        """添加新规则"""
        if not self._validate_rule(rule):
            logger.error("规则验证失败")
            raise ValueError("规则验证失败")

        rule_id = rule.get("id", str(uuid.uuid4()))
        rule["id"] = rule_id

        if "status" not in rule:
            rule["status"] = RULE_STATUS["ACTIVE"]

        if "priority" not in rule:
            rule["priority"] = 5

        if "created_at" not in rule:
            rule["created_at"] = self._get_timestamp()

        if "updated_at" not in rule:
            rule["updated_at"] = rule["created_at"]

        rule["version"] = rule.get("version", "1.0.0")

        with self._lock:
            # 保存旧版本
            if rule_id in self._rules:
                self._save_version(rule_id, self._rules[rule_id])

            self._rules[rule_id] = rule

            rule_type = rule.get("type", "unknown")
            if rule_type not in self._rules_by_type:
                self._rules_by_type[rule_type] = {}
            self._rules_by_type[rule_type][rule_id] = rule_id

            priority = rule["priority"]
            if priority not in self._rules_by_priority:
                self._rules_by_priority[priority] = []
            if rule_id not in self._rules_by_priority[priority]:
                self._rules_by_priority[priority].append(rule_id)

        logger.info(f"添加规则: {rule_id} (类型: {rule_type}, 名称: {rule.get('name', '未命名')}, 优先级: {priority})")

        self._persist_rule(rule)

        return rule_id

    def update_rule(self, rule_id: str, rule: Dict[str, Any]) -> bool:
        """更新规则"""
        if rule_id not in self._rules:
            logger.error(f"规则不存在: {rule_id}")
            return False

        if not self._validate_rule(rule):
            logger.error("规则验证失败")
            return False

        with self._lock:
            old_rule = self._rules[rule_id]
            self._save_version(rule_id, old_rule)

            rule["id"] = rule_id
            rule["updated_at"] = self._get_timestamp()
            
            old_version = old_rule.get("version", "1.0.0")
            rule["version"] = self._bump_version(old_version)

            old_type = old_rule.get("type", "unknown")
            new_type = rule.get("type", "unknown")

            self._rules[rule_id] = rule

            if old_type != new_type:
                if old_type in self._rules_by_type and rule_id in self._rules_by_type[old_type]:
                    del self._rules_by_type[old_type][rule_id]
                
                if new_type not in self._rules_by_type:
                    self._rules_by_type[new_type] = {}
                self._rules_by_type[new_type][rule_id] = rule_id

            old_priority = old_rule.get("priority", 5)
            new_priority = rule.get("priority", 5)
            
            if old_priority != new_priority:
                if old_priority in self._rules_by_priority and rule_id in self._rules_by_priority[old_priority]:
                    self._rules_by_priority[old_priority].remove(rule_id)
                
                if new_priority not in self._rules_by_priority:
                    self._rules_by_priority[new_priority] = []
                if rule_id not in self._rules_by_priority[new_priority]:
                    self._rules_by_priority[new_priority].append(rule_id)

        logger.info(f"更新规则: {rule_id} (类型: {new_type}, 名称: {rule.get('name', '未命名')}, 优先级: {new_priority})")

        self._persist_rule(rule)

        return True

    def delete_rule(self, rule_id: str) -> bool:
        """删除规则"""
        if rule_id not in self._rules:
            logger.error(f"规则不存在: {rule_id}")
            return False

        with self._lock:
            rule = self._rules[rule_id]
            rule_type = rule.get("type", "unknown")
            priority = rule.get("priority", 5)

            del self._rules[rule_id]

            if rule_type in self._rules_by_type and rule_id in self._rules_by_type[rule_type]:
                del self._rules_by_type[rule_type][rule_id]

            if priority in self._rules_by_priority and rule_id in self._rules_by_priority[priority]:
                self._rules_by_priority[priority].remove(rule_id)

            if rule_id in self._rule_versions:
                del self._rule_versions[rule_id]

        logger.info(f"删除规则: {rule_id} (类型: {rule_type}, 名称: {rule.get('name', '未命名')})")

        self._delete_persisted_rule(rule_id)

        return True

    def get_rule(self, rule_id: str) -> Optional[Dict[str, Any]]:
        """获取规则"""
        return self._rules.get(rule_id)

    def get_rules(self, rule_type: Optional[str] = None) -> List[Dict[str, Any]]:
        """获取规则列表"""
        with self._lock:
            if rule_type:
                rule_ids = self._rules_by_type.get(rule_type, {})
                rules = [self._rules[rule_id] for rule_id in rule_ids if rule_id in self._rules]
            else:
                rules = list(self._rules.values())
            
            return sorted(rules, key=lambda r: r.get("priority", 1), reverse=True)

    def get_rules_by_status(self, status: str) -> List[Dict[str, Any]]:
        """按状态获取规则"""
        return [rule for rule in self._rules.values() if rule.get("status") == status]

    def get_rules_by_priority(self, min_priority: int = None, max_priority: int = None) -> List[Dict[str, Any]]:
        """按优先级范围获取规则"""
        rules = []
        with self._lock:
            for priority, rule_ids in self._rules_by_priority.items():
                if (min_priority is None or priority >= min_priority) and \
                   (max_priority is None or priority <= max_priority):
                    rules.extend([self._rules[rule_id] for rule_id in rule_ids if rule_id in self._rules])
        
        return sorted(rules, key=lambda r: r.get("priority", 1), reverse=True)

    def enable_rule(self, rule_id: str) -> bool:
        """启用规则"""
        if rule_id not in self._rules:
            return False
        
        with self._lock:
            self._rules[rule_id]["status"] = RULE_STATUS["ACTIVE"]
        
        logger.info(f"启用规则: {rule_id}")
        self._persist_rule(self._rules[rule_id])
        return True

    def disable_rule(self, rule_id: str) -> bool:
        """禁用规则"""
        if rule_id not in self._rules:
            return False
        
        with self._lock:
            self._rules[rule_id]["status"] = RULE_STATUS["DISABLED"]
        
        logger.info(f"禁用规则: {rule_id}")
        self._persist_rule(self._rules[rule_id])
        return True

    def find_conflicts(self) -> List[Dict[str, Any]]:
        """检测规则冲突"""
        conflicts = []
        rules = self.get_rules()

        for i, rule1 in enumerate(rules):
            for j, rule2 in enumerate(rules[i+1:], start=i+1):
                conflict = self._detect_conflict(rule1, rule2)
                if conflict:
                    conflicts.append(conflict)

        return conflicts

    def _detect_conflict(self, rule1: Dict, rule2: Dict) -> Optional[Dict]:
        """检测两个规则之间的冲突"""
        actions1 = rule1.get("actions", [])
        actions2 = rule2.get("actions", [])

        for action1 in actions1:
            for action2 in actions2:
                if action1.get("type") == "update_system_config" and action2.get("type") == "update_system_config":
                    key1 = action1.get("parameters", {}).get("config_key")
                    key2 = action2.get("parameters", {}).get("config_key")
                    if key1 and key2 and key1 == key2:
                        return {
                            "type": "config_conflict",
                            "rule1_id": rule1["id"],
                            "rule1_name": rule1.get("name", "未命名"),
                            "rule2_id": rule2["id"],
                            "rule2_name": rule2.get("name", "未命名"),
                            "key": key1
                        }

                elif action1.get("type") == "grant_permission" and action2.get("type") == "revoke_permission":
                    user1 = action1.get("parameters", {}).get("user_id")
                    perm1 = action1.get("parameters", {}).get("permission")
                    user2 = action2.get("parameters", {}).get("user_id")
                    perm2 = action2.get("parameters", {}).get("permission")
                    if user1 == user2 and perm1 == perm2:
                        return {
                            "type": "permission_conflict",
                            "rule1_id": rule1["id"],
                            "rule1_name": rule1.get("name", "未命名"),
                            "rule2_id": rule2["id"],
                            "rule2_name": rule2.get("name", "未命名"),
                            "user_id": user1,
                            "permission": perm1
                        }

        return None

    def resolve_conflicts(self, conflicts: List[Dict]) -> Dict[str, Any]:
        """解决规则冲突"""
        resolved = {}
        
        for conflict in conflicts:
            rule1 = self.get_rule(conflict["rule1_id"])
            rule2 = self.get_rule(conflict["rule2_id"])
            
            if not rule1 or not rule2:
                continue

            priority1 = rule1.get("priority", 1)
            priority2 = rule2.get("priority", 1)

            if priority1 > priority2:
                winner = rule1
                loser = rule2
            else:
                winner = rule2
                loser = rule1

            self.disable_rule(loser["id"])
            
            resolved[conflict["rule1_id"] + "_" + conflict["rule2_id"]] = {
                "conflict_type": conflict["type"],
                "winner": winner["id"],
                "winner_name": winner.get("name", "未命名"),
                "loser": loser["id"],
                "loser_name": loser.get("name", "未命名"),
                "resolved_by": "priority"
            }

            logger.info(f"规则冲突已解决: {winner['id']} 优先于 {loser['id']}")

        return resolved

    def get_rule_versions(self, rule_id: str) -> List[Dict]:
        """获取规则版本历史"""
        return self._rule_versions.get(rule_id, [])

    def restore_rule_version(self, rule_id: str, version: str) -> bool:
        """恢复规则到指定版本"""
        versions = self._rule_versions.get(rule_id, [])
        
        for v in versions:
            if v.get("version") == version:
                restored_rule = v.copy()
                restored_rule["version"] = self._bump_version(version)
                self.add_rule(restored_rule)
                logger.info(f"规则 {rule_id} 已恢复到版本 {version}")
                return True

        logger.error(f"规则 {rule_id} 不存在版本 {version}")
        return False

    def _save_version(self, rule_id: str, rule: Dict):
        """保存规则版本"""
        if rule_id not in self._rule_versions:
            self._rule_versions[rule_id] = []
        
        version_copy = rule.copy()
        self._rule_versions[rule_id].append(version_copy)
        
        if len(self._rule_versions[rule_id]) > 10:
            self._rule_versions[rule_id].pop(0)

    def _bump_version(self, version: str) -> str:
        """升级版本号"""
        parts = version.split(".")
        if len(parts) == 3:
            return f"{parts[0]}.{parts[1]}.{int(parts[2]) + 1}"
        return f"{version}.1"

    def _validate_rule(self, rule: Dict[str, Any]) -> bool:
        """验证规则定义"""
        required_fields = ["name", "type", "description", "conditions", "actions"]
        for field in required_fields:
            if field not in rule:
                logger.error(f"规则缺少必要字段: {field}")
                return False

        if not isinstance(rule["conditions"], list):
            logger.error("规则条件必须是列表")
            return False

        for i, condition in enumerate(rule["conditions"]):
            if not isinstance(condition, dict):
                logger.error(f"规则条件 {i} 必须是字典")
                return False

            if "type" not in condition:
                logger.error(f"规则条件 {i} 缺少必要字段 type")
                return False

        if not isinstance(rule["actions"], list):
            logger.error("规则动作必须是列表")
            return False

        for i, action in enumerate(rule["actions"]):
            if not isinstance(action, dict):
                logger.error(f"规则动作 {i} 必须是字典")
                return False

            if "type" not in action:
                logger.error(f"规则动作 {i} 缺少必要字段 type")
                return False

        if "priority" in rule:
            if not isinstance(rule["priority"], int) or not (1 <= rule["priority"] <= 15):
                logger.error(f"规则优先级必须是1-15之间的整数: {rule['priority']}")
                return False

        return True

    def _get_timestamp(self) -> str:
        """获取当前时间戳"""
        from datetime import datetime
        return datetime.now().isoformat()

    def _persist_rule(self, rule: Dict[str, Any]):
        """持久化规则"""
        try:
            from app.rules.sources.database_source import DatabaseRuleSource
            from app.rules.sources.file_source import FileRuleSource

            db_source = DatabaseRuleSource()
            db_source.save_rule(rule)

            file_source = FileRuleSource()
            file_source.save_rule(rule)

        except ImportError:
            logger.warning("持久化模块未找到")
        except Exception as e:
            logger.error(f"持久化规则失败: {str(e)}")

    def _delete_persisted_rule(self, rule_id: str):
        """从持久化存储中删除规则"""
        try:
            from app.rules.sources.database_source import DatabaseRuleSource
            from app.rules.sources.file_source import FileRuleSource

            db_source = DatabaseRuleSource()
            db_source.delete_rule(rule_id)

            file_source = FileRuleSource()
            file_source.delete_rule(rule_id)

        except ImportError:
            logger.warning("持久化模块未找到")
        except Exception as e:
            logger.error(f"删除持久化规则失败: {str(e)}")

    def clear_all_rules(self):
        """清除所有规则"""
        with self._lock:
            self._rules.clear()
            self._rules_by_type.clear()
            self._rules_by_priority.clear()
            self._rule_versions.clear()
        
        logger.info("已清除所有规则")

    def get_rule_count(self) -> int:
        """获取规则数量"""
        return len(self._rules)

    def get_rule_types(self) -> List[str]:
        """获取所有规则类型"""
        return list(self._rules_by_type.keys())

    def get_stats(self) -> Dict[str, Any]:
        """获取规则统计"""
        stats = {
            "total_rules": len(self._rules),
            "rules_by_type": {},
            "rules_by_status": {},
            "rules_by_priority": {},
            "total_versions": sum(len(v) for v in self._rule_versions.values())
        }

        for rule_type, rule_ids in self._rules_by_type.items():
            stats["rules_by_type"][rule_type] = len(rule_ids)

        for rule in self._rules.values():
            status = rule.get("status", "unknown")
            stats["rules_by_status"][status] = stats["rules_by_status"].get(status, 0) + 1

        for priority, rule_ids in self._rules_by_priority.items():
            stats["rules_by_priority"][priority] = len(rule_ids)

        return stats