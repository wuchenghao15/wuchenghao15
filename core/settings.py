# -*- coding: utf-8 -*-
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
User Settings Manager - 用户设置管理系统
支持基于权限和规则的动态功能显示
"""

from typing import Dict, List, Any, Optional, Tuple, Set
from datetime import datetime
import json
import sys

class UserRole:
    """用户角色"""
    
    def __init__(self, role_id: str, name: str, description: str = ""):
        self.id = role_id
        self.name = name
        self.description = description
        self.permissions: Set[str] = set()
        self.allowed_features: Set[str] = set()
        self.priority = 0
    
    def add_permission(self, permission: str):
        self.permissions.add(permission)
    
    def add_feature(self, feature: str):
        self.allowed_features.add(feature)
    
    def has_permission(self, permission: str) -> bool:
        return permission in self.permissions
    
    def has_feature(self, feature: str) -> bool:
        return feature in self.allowed_features
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "role_id": self.id,
            "name": self.name,
            "description": self.description,
            "permissions": list(self.permissions),
            "allowed_features": list(self.allowed_features),
            "priority": self.priority
        }


class User:
    """用户"""
    
    def __init__(self, user_id: str, username: str, email: str = ""):
        self.id = user_id
        self.username = username
        self.email = email
        self.roles: List[UserRole] = []
        self.settings: Dict[str, Any] = {}
        self.created_at = datetime.now()
        self.last_login_at = None
    
    def add_role(self, role: UserRole):
        if role not in self.roles:
            self.roles.append(role)
    
    def remove_role(self, role: UserRole):
        if role in self.roles:
            self.roles.remove(role)
    
    def has_permission(self, permission: str) -> bool:
        return any(role.has_permission(permission) for role in self.roles)
    
    def has_feature(self, feature: str) -> bool:
        return any(role.has_feature(feature) for role in self.roles)
    
    def get_effective_permissions(self) -> Set[str]:
        permissions = set()
        for role in self.roles:
            permissions.update(role.permissions)
        return permissions
    
    def get_effective_features(self) -> Set[str]:
        features = set()
        for role in self.roles:
            features.update(role.allowed_features)
        return features
    
    def set_setting(self, key: str, value: Any):
        self.settings[key] = value
    
    def get_setting(self, key: str, default: Any = None) -> Any:
        return self.settings.get(key, default)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "user_id": self.id,
            "username": self.username,
            "email": self.email,
            "roles": [role.to_dict() for role in self.roles],
            "permissions": list(self.get_effective_permissions()),
            "features": list(self.get_effective_features()),
            "settings": self.settings,
            "created_at": self.created_at.isoformat(),
            "last_login_at": self.last_login_at.isoformat() if self.last_login_at else None
        }


class SettingGroup:
    """设置分组"""
    
    def __init__(self, group_id: str, name: str, icon: str = "", order: int = 0):
        self.id = group_id
        self.name = name
        self.icon = icon
        self.order = order
        self.settings: List["SettingItem"] = []
    
    def add_setting(self, setting: "SettingItem"):
        self.settings.append(setting)
        self.settings.sort(key=lambda x: x.order)
    
    def to_dict(self, user: Optional[User] = None) -> Dict[str, Any]:
        visible_settings = []
        for setting in self.settings:
            if setting.is_visible(user):
                visible_settings.append(setting.to_dict())
        
        if not visible_settings:
            return None
        
        return {
            "group_id": self.id,
            "name": self.name,
            "icon": self.icon,
            "order": self.order,
            "settings": visible_settings
        }


class SettingItem:
    """设置项"""
    
    def __init__(self, setting_id: str, name: str, setting_type: str, 
                 description: str = "", default_value: Any = None, order: int = 0):
        self.id = setting_id
        self.name = name
        self.type = setting_type
        self.description = description
        self.default_value = default_value
        self.order = order
        self.permissions: Set[str] = set()
        self.conditions: List[callable] = []
        self.options: List[Dict[str, Any]] = []
    
    def add_permission(self, permission: str):
        self.permissions.add(permission)
    
    def add_condition(self, condition: callable):
        self.conditions.append(condition)
    
    def add_option(self, value: Any, label: str):
        self.options.append({"value": value, "label": label})
    
    def is_visible(self, user: Optional[User] = None) -> bool:
        if not user:
            return False
        
        for permission in self.permissions:
            if not user.has_permission(permission):
                return False
        
        for condition in self.conditions:
            if not condition(user):
                return False
        
        return True
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "setting_id": self.id,
            "name": self.name,
            "type": self.type,
            "description": self.description,
            "default_value": self.default_value,
            "order": self.order,
            "options": self.options
        }


class FeatureRule:
    """功能规则"""
    
    def __init__(self, rule_id: str, feature_id: str, conditions: List[dict], 
                 action: str = "show", priority: int = 100):
        self.id = rule_id
        self.feature_id = feature_id
        self.conditions = conditions
        self.action = action
        self.priority = priority
    
    def evaluate(self, user: User) -> bool:
        """评估规则是否匹配"""
        for condition in self.conditions:
            if not self._evaluate_condition(condition, user):
                return False
        return True
    
    def _evaluate_condition(self, condition: dict, user: User) -> bool:
        """评估单个条件"""
        field = condition.get("field")
        operator = condition.get("operator")
        value = condition.get("value")
        
        if field == "role":
            return any(role.id == value for role in user.roles)
        elif field == "permission":
            return user.has_permission(value)
        elif field == "feature":
            return user.has_feature(value)
        elif field == "setting":
            user_value = user.get_setting(field.split(".")[1])
            return self._compare_values(user_value, operator, value)
        elif field == "user_id":
            return user.id == value
        elif field == "has_role":
            return any(role.id == value for role in user.roles)
        
        return True
    
    def _compare_values(self, left: Any, operator: str, right: Any) -> bool:
        """比较两个值"""
        try:
            if operator == "==":
                return left == right
            elif operator == "!=":
                return left != right
            elif operator == ">":
                return left > right
            elif operator == "<":
                return left < right
            elif operator == ">=":
                return left >= right
            elif operator == "<=":
                return left <= right
            elif operator == "contains":
                return str(value) in str(left)
        except Exception:
            return False
        return False


class SettingsManager:
    """设置管理器"""
    
    def __init__(self):
        self.roles: Dict[str, UserRole] = {}
        self.users: Dict[str, User] = {}
        self.setting_groups: Dict[str, SettingGroup] = {}
        self.features: Dict[str, Dict[str, Any]] = {}
        self.feature_rules: List[FeatureRule] = []
        
        self._init_default_roles()
        self._init_default_settings()
        self._init_default_features()
    
    def _init_default_roles(self):
        """初始化默认角色"""
        roles = [
            {"id": "admin", "name": "管理员", "description": "系统管理员", "priority": 100},
            {"id": "teacher", "name": "教师", "description": "任课教师", "priority": 50},
            {"id": "student", "name": "学生", "description": "学生用户", "priority": 10},
            {"id": "parent", "name": "家长", "description": "学生家长", "priority": 20},
            {"id": "researcher", "name": "教研员", "description": "教研人员", "priority": 60}
        ]
        
        for role_data in roles:
            role = UserRole(role_data["id"], role_data["name"], role_data["description"])
            role.priority = role_data["priority"]
            self.roles[role.id] = role
        
        self.roles["admin"].add_permission("manage_users")
        self.roles["admin"].add_permission("manage_settings")
        self.roles["admin"].add_permission("manage_features")
        self.roles["admin"].add_permission("view_logs")
        
        self.roles["teacher"].add_permission("manage_classes")
        self.roles["teacher"].add_permission("manage_students")
        self.roles["teacher"].add_permission("create_quizzes")
        self.roles["teacher"].add_permission("view_reports")
        
        self.roles["student"].add_permission("view_courses")
        self.roles["student"].add_permission("submit_homework")
        self.roles["student"].add_permission("view_grades")
        
        self.roles["parent"].add_permission("view_child_progress")
        self.roles["parent"].add_permission("view_child_grades")
        
        self.roles["researcher"].add_permission("analyze_curriculum")
        self.roles["researcher"].add_permission("design_courses")
        self.roles["researcher"].add_permission("view_statistics")
        
        self.roles["admin"].add_feature("user_management")
        self.roles["admin"].add_feature("system_settings")
        self.roles["admin"].add_feature("audit_logs")
        
        self.roles["teacher"].add_feature("class_management")
        self.roles["teacher"].add_feature("quiz_management")
        self.roles["teacher"].add_feature("grade_management")
        
        self.roles["student"].add_feature("course_view")
        self.roles["student"].add_feature("homework_submit")
        self.roles["student"].add_feature("grade_view")
        
        self.roles["parent"].add_feature("child_progress")
        self.roles["parent"].add_feature("notification_settings")
        
        self.roles["researcher"].add_feature("curriculum_analysis")
        self.roles["researcher"].add_feature("course_design")
    
    def _init_default_settings(self):
        """初始化默认设置"""
        groups = [
            {
                "group_id": "account",
                "name": "账号设置",
                "icon": "user",
                "order": 1
            },
            {
                "group_id": "learning",
                "name": "学习设置",
                "icon": "book",
                "order": 2
            },
            {
                "group_id": "notification",
                "name": "通知设置",
                "icon": "bell",
                "order": 3
            },
            {
                "group_id": "system",
                "name": "系统设置",
                "icon": "settings",
                "order": 10
            }
        ]
        
        for group_data in groups:
            self.setting_groups[group_data["group_id"]] = SettingGroup(
                group_data["group_id"],
                group_data["name"],
                group_data["icon"],
                group_data["order"]
            )
        
        account_settings = [
            SettingItem("username", "用户名", "text", "您的显示名称", order=1),
            SettingItem("email", "邮箱", "email", "联系邮箱", order=2),
            SettingItem("password", "密码", "password", "修改密码", order=3),
            SettingItem("avatar", "头像", "image", "个人头像", order=4)
        ]
        
        learning_settings = [
            SettingItem("daily_goal", "每日学习目标", "number", "每天计划学习分钟数", 60, order=1),
            SettingItem("difficulty", "难度偏好", "select", "学习内容难度", "medium", order=2),
            SettingItem("notification_enabled", "学习提醒", "boolean", "启用学习提醒", True, order=3),
            SettingItem("study_mode", "学习模式", "select", "专注模式或自由模式", "focus", order=4)
        ]
        learning_settings[1].add_option("easy", "简单")
        learning_settings[1].add_option("medium", "中等")
        learning_settings[1].add_option("hard", "困难")
        learning_settings[3].add_option("focus", "专注模式")
        learning_settings[3].add_option("free", "自由模式")
        
        notification_settings = [
            SettingItem("email_notifications", "邮件通知", "boolean", "接收邮件通知", True, order=1),
            SettingItem("push_notifications", "推送通知", "boolean", "接收推送通知", True, order=2),
            SettingItem("daily_digest", "每日汇总", "boolean", "接收每日学习汇总", True, order=3),
            SettingItem("weekly_report", "周报", "boolean", "接收周报", True, order=4)
        ]
        
        system_settings = [
            SettingItem("language", "语言", "select", "界面语言", "zh-CN", order=1),
            SettingItem("theme", "主题", "select", "界面主题", "light", order=2),
            SettingItem("timezone", "时区", "select", "时区设置", "Asia/Shanghai", order=3),
            SettingItem("data_export", "数据导出", "action", "导出个人数据", order=10)
        ]
        system_settings[0].add_option("zh-CN", "简体中文")
        system_settings[0].add_option("en-US", "English")
        system_settings[1].add_option("light", "浅色")
        system_settings[1].add_option("dark", "深色")
        system_settings[1].add_option("auto", "跟随系统")
        
        for setting in account_settings:
            self.setting_groups["account"].add_setting(setting)
        
        for setting in learning_settings:
            self.setting_groups["learning"].add_setting(setting)
        
        for setting in notification_settings:
            self.setting_groups["notification"].add_setting(setting)
        
        for setting in system_settings:
            setting.add_permission("manage_settings")
            self.setting_groups["system"].add_setting(setting)
    
    def _init_default_features(self):
        """初始化默认功能"""
        features = [
            {"id": "user_management", "name": "用户管理", "description": "管理系统用户", "icon": "users"},
            {"id": "class_management", "name": "班级管理", "description": "管理班级和学生", "icon": "school"},
            {"id": "quiz_management", "name": "测验管理", "description": "创建和管理测验", "icon": "clipboard"},
            {"id": "grade_management", "name": "成绩管理", "description": "录入和查看成绩", "icon": "chart"},
            {"id": "course_view", "name": "课程学习", "description": "浏览和学习课程", "icon": "book-open"},
            {"id": "homework_submit", "name": "作业提交", "description": "提交和查看作业", "icon": "file"},
            {"id": "grade_view", "name": "成绩查询", "description": "查看个人成绩", "icon": "award"},
            {"id": "child_progress", "name": "孩子进度", "description": "查看孩子学习进度", "icon": "trending-up"},
            {"id": "notification_settings", "name": "通知设置", "description": "管理通知偏好", "icon": "bell"},
            {"id": "curriculum_analysis", "name": "课程分析", "description": "分析教学大纲", "icon": "bar-chart"},
            {"id": "course_design", "name": "课程设计", "description": "设计课程方案", "icon": "pencil"},
            {"id": "system_settings", "name": "系统设置", "description": "系统配置管理", "icon": "settings"},
            {"id": "audit_logs", "name": "审计日志", "description": "查看系统日志", "icon": "file-text"},
            {"id": "statistics", "name": "数据统计", "description": "查看数据统计", "icon": "pie-chart"}
        ]
        
        for feature in features:
            self.features[feature["id"]] = feature
    
    def create_user(self, user_id: str, username: str, email: str = "") -> User:
        """创建用户"""
        user = User(user_id, username, email)
        self.users[user_id] = user
        return user
    
    def get_user(self, user_id: str) -> Optional[User]:
        """获取用户"""
        return self.users.get(user_id)
    
    def assign_role(self, user_id: str, role_id: str) -> bool:
        """分配角色"""
        user = self.get_user(user_id)
        role = self.roles.get(role_id)
        
        if user and role:
            user.add_role(role)
            return True
        return False
    
    def get_visible_settings(self, user: User) -> List[Dict[str, Any]]:
        """获取用户可见的设置"""
        visible_groups = []
        
        for group_id in sorted(self.setting_groups.keys(), key=lambda x: self.setting_groups[x].order):
            group = self.setting_groups[group_id]
            group_dict = group.to_dict(user)
            if group_dict:
                visible_groups.append(group_dict)
        
        return visible_groups
    
    def get_visible_features(self, user: User) -> List[Dict[str, Any]]:
        """获取用户可见的功能"""
        visible_features = []
        effective_features = user.get_effective_features()
        
        for feature_id in effective_features:
            if feature_id in self.features:
                feature = self.features[feature_id]
                
                matches = [rule for rule in self.feature_rules 
                          if rule.feature_id == feature_id]
                
                visible = True
                for rule in sorted(matches, key=lambda x: x.priority):
                    if rule.evaluate(user):
                        if rule.action == "hide":
                            visible = False
                        elif rule.action == "show":
                            visible = True
                
                if visible:
                    visible_features.append(feature)
        
        visible_features.sort(key=lambda x: x.get("name", ""))
        return visible_features
    
    def add_feature_rule(self, rule: FeatureRule):
        """添加功能规则"""
        self.feature_rules.append(rule)
    
    def evaluate_feature_access(self, user: User, feature_id: str) -> bool:
        """评估用户是否有权访问功能"""
        if not user.has_feature(feature_id):
            return False
        
        matches = [rule for rule in self.feature_rules 
                  if rule.feature_id == feature_id]
        
        for rule in sorted(matches, key=lambda x: x.priority):
            if rule.evaluate(user):
                if rule.action == "hide":
                    return False
        
        return True
    
    def update_user_settings(self, user_id: str, settings: Dict[str, Any]) -> bool:
        """更新用户设置"""
        user = self.get_user(user_id)
        if not user:
            return False
        
        for key, value in settings.items():
            user.set_setting(key, value)
        
        return True
    
    def get_user_settings(self, user_id: str) -> Dict[str, Any]:
        """获取用户设置"""
        user = self.get_user(user_id)
        if not user:
            return {}
        
        return user.settings


# 全局实例
settings_manager = SettingsManager()
