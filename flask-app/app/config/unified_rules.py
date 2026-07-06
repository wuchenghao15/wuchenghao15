# -*- coding: utf-8 -*-
"""
MTSCOS AI 统一规则配置中心
强化路由规则、系统规则、用户规则、数据安全规则、权限规则
"""

import logging
logger = logging.getLogger(__name__)

# ==========================================
# 一、路由规则配置
# ==========================================

SUPER_ADMIN_ROLES = ['hardware_admin', 'system_admin']

# 考试系统访问规则 - 只有学生可以参加考试，超级管理员除外
EXAM_SYSTEM_ROUTES = {
    '/exam_system': {
        'allowed_roles': ['student', 'hardware_admin', 'system_admin'],
        'description': '考试系统首页 - 学生和超级管理员',
        'require_login': True,
        'redirect_on_fail': '/auth/login'
    },
    '/exam/start/<exam_id>': {
        'allowed_roles': ['student', 'hardware_admin', 'system_admin'],
        'description': '开始考试 - 学生和超级管理员',
        'require_login': True,
        'redirect_on_fail': '/auth/login'
    },
    '/exam/placement_test': {
        'allowed_roles': ['student', 'student_vip', 'hardware_admin', 'system_admin'],
        'description': '摸底测试 - 学生和超级管理员',
        'require_login': True,
        'redirect_on_fail': '/auth/login'
    },
    '/api/exam/papers': {
        'allowed_roles': ['student', 'hardware_admin', 'system_admin'],
        'description': '考试试卷API - 学生和超级管理员',
        'require_login': True,
        'redirect_on_fail': None
    }
}

# 测试系统访问规则 - 只有学生可以参加测试，超级管理员除外
TEST_SYSTEM_ROUTES = {
    '/test_system': {
        'allowed_roles': ['student', 'student_vip', 'hardware_admin', 'system_admin'],
        'description': '测试系统首页 - 学生和超级管理员',
        'require_login': True,
        'redirect_on_fail': '/auth/login'
    }
}

# 学习系统访问规则 - 学生和教师，超级管理员除外
LEARNING_SYSTEM_ROUTES = {
    '/learning_system': {
        'allowed_roles': ['student', 'student_vip', 'teacher', 'researcher', 'hardware_admin', 'system_admin'],
        'description': '学习系统首页',
        'require_login': True,
        'redirect_on_fail': '/auth/login'
    },
    '/learning/history': {
        'allowed_roles': ['student', 'student_vip', 'teacher', 'researcher', 'hardware_admin', 'system_admin'],
        'description': '学习历史记录',
        'require_login': True
    },
    '/learning/wrong_questions': {
        'allowed_roles': ['student', 'student_vip', 'hardware_admin', 'system_admin'],
        'description': '错题本 - 学生和超级管理员',
        'require_login': True
    }
}

# 用户信息管理系统访问规则 - 所有已登录用户
USER_SYSTEM_ROUTES = {
    '/user_system': {
        'allowed_roles': ['student', 'student_vip', 'teacher', 'admin', 'super_admin', 
                          'hardware_admin', 'designer', 'researcher', 'exam_expert', 'system_admin'],
        'description': '用户信息管理系统 - 所有已登录用户',
        'require_login': True,
        'redirect_on_fail': '/auth/login'
    }
}

# 管理系统访问规则
ADMIN_SYSTEM_ROUTES = {
    '/admin_center': {
        'allowed_roles': ['admin', 'super_admin', 'hardware_admin', 'system_admin'],
        'description': '管理员中心',
        'require_login': True
    },
    '/super_admin_dashboard': {
        'allowed_roles': ['super_admin', 'hardware_admin', 'hardware_vikey_admin', 'system_admin'],
        'description': '超级管理员仪表盘',
        'require_login': True,
        'super_admin_only': True
    },
    '/admin_dashboard': {
        'allowed_roles': ['admin'],
        'description': '管理员控制台（只读权限）',
        'require_login': True,
        'readonly': True
    },
    '/admin_app/exams': {
        'allowed_roles': ['admin', 'super_admin', 'hardware_admin', 'system_admin'],
        'description': '考试管理',
        'require_login': True,
        'readonly_for_admin': True
    },
    '/admin_app/users': {
        'allowed_roles': ['admin', 'super_admin', 'hardware_admin', 'system_admin'],
        'description': '用户管理',
        'require_login': True,
        'readonly_for_admin': True
    },
    '/settings/security': {
        'allowed_roles': ['admin', 'super_admin', 'hardware_admin', 'system_admin'],
        'description': '安全配置',
        'require_login': True,
        'readonly_for_admin': True
    },
    '/settings/database-settings': {
        'allowed_roles': ['admin', 'super_admin', 'hardware_admin', 'system_admin'],
        'description': '数据库配置',
        'require_login': True,
        'readonly_for_admin': True
    },
    '/settings/rules': {
        'allowed_roles': ['admin', 'super_admin', 'hardware_admin', 'system_admin'],
        'description': '规则配置',
        'require_login': True,
        'readonly_for_admin': True
    },
    '/settings/hardware': {
        'allowed_roles': ['admin', 'super_admin', 'hardware_admin', 'system_admin'],
        'description': '硬件配置',
        'require_login': True,
        'readonly_for_admin': True
    }
}

# ==========================================
# 二、权限等级体系
# ==========================================

# 角色等级 - 从低到高
ROLE_HIERARCHY = {
    'guest': 0,
    'user': 1,
    'student': 2,
    'student_vip': 3,
    'designer': 4,
    'teacher': 5,
    'teacher_admin': 6,
    'exam_expert': 7,
    'researcher': 8,
    'admin': 9,
    'hardware_vikey_admin': 10,
    'super_admin': 11,
    'hardware_admin': 12,
    'system_admin': 13
}

# 角色描述
ROLE_DESCRIPTIONS = {
    'guest': '访客 - 未登录用户',
    'user': '普通用户 - 基础权限',
    'student': '学生 - 可参加考试和测试',
    'student_vip': 'VIP学生 - 扩展学习功能',
    'designer': '设计师 - 可设计题目但不能参加考试',
    'teacher': '教师 - 管理学生和作业',
    'teacher_admin': '教师管理员 - 教师管理权限',
    'exam_expert': '考试专家 - 考试相关权限',
    'researcher': '研究员 - 研究分析权限',
    'admin': '管理员 - 系统管理权限',
    'hardware_vikey_admin': '硬件ViKey管理员 - 硬件相关权限',
    'super_admin': '超级管理员 - 高级系统权限',
    'hardware_admin': '硬件管理员 - 最高权限，需硬件认证',
    'system_admin': '系统管理员 - 系统核心权限'
}

# ==========================================
# 三、系统核心规则
# ==========================================

SYSTEM_RULES = {
    # 登录安全规则
    'SEC_LOGIN_MAX_ATTEMPTS': {
        'value': 5,
        'description': '最大登录尝试次数',
        'type': 'security',
        'priority': 1
    },
    'SEC_LOCK_DURATION': {
        'value': 30,  # 强化为30分钟
        'description': '账户锁定时长(分钟)',
        'type': 'security',
        'priority': 1
    },
    'SEC_SESSION_TIMEOUT': {
        'value': 30,
        'description': '会话超时时间(分钟)',
        'type': 'security',
        'priority': 1
    },
    'SEC_PASSWORD_MIN_LENGTH': {
        'value': 8,
        'description': '密码最小长度',
        'type': 'security',
        'priority': 1
    },
    'SEC_PASSWORD_EXPIRY': {
        'value': 90,
        'description': '密码过期天数',
        'type': 'security',
        'priority': 1
    },
    'SEC_TWO_FACTOR_REQUIRED': {
        'value': False,
        'description': '是否强制双因素认证',
        'type': 'security',
        'priority': 2
    },
    
    # 系统运行规则
    'SYS_MAINTENANCE_MODE': {
        'value': False,
        'description': '维护模式',
        'type': 'system',
        'priority': 10
    },
    'SYS_ALLOW_REGISTRATION': {
        'value': True,
        'description': '允许用户注册',
        'type': 'system',
        'priority': 10
    },
    'SYS_MAX_USERS': {
        'value': 10000,  # 强化上限
        'description': '最大用户数',
        'type': 'system',
        'priority': 10
    },
    
    # 硬件认证规则
    'HW_AUTH_REQUIRED': {
        'value': True,
        'description': '硬件管理员需要硬件认证',
        'type': 'security',
        'priority': 1
    },
    'HW_SESSION_TIMEOUT': {
        'value': 8,
        'description': '硬件认证会话超时(小时)',
        'type': 'security',
        'priority': 1
    }
}

# ==========================================
# 四、数据安全规则
# ==========================================

DATA_SECURITY_RULES = {
    # 数据库安全
    'DB_BACKUP_INTERVAL': {
        'value': 300,  # 5分钟
        'description': '数据库备份间隔(秒)',
        'type': 'data_security',
        'priority': 1
    },
    'DB_MAX_BACKUPS': {
        'value': 10,
        'description': '最大备份文件数',
        'type': 'data_security',
        'priority': 1
    },
    'DB_ENCRYPTION_ENABLED': {
        'value': False,
        'description': '数据库加密',
        'type': 'data_security',
        'priority': 1
    },
    
    # SQL注入防护
    'SQL_INJECTION_PROTECTION': {
        'value': True,
        'description': 'SQL注入防护开关',
        'type': 'data_security',
        'priority': 1
    },
    'SQL_BLACKLIST_KEYWORDS': {
        'value': ['DROP', 'DELETE', 'TRUNCATE', 'ALTER', 'GRANT', 'REVOKE'],
        'description': 'SQL黑名单关键词',
        'type': 'data_security',
        'priority': 1
    },
    
    # 数据访问控制
    'DATA_ACCESS_LOG_ENABLED': {
        'value': True,
        'description': '数据访问日志',
        'type': 'data_security',
        'priority': 1
    },
    'SENSITIVE_DATA_MASK': {
        'value': True,
        'description': '敏感数据脱敏',
        'type': 'data_security',
        'priority': 1
    },
    
    # 用户数据保护
    'USER_DATA_RETENTION_DAYS': {
        'value': 365,
        'description': '用户数据保留天数',
        'type': 'data_security',
        'priority': 1
    },
    'USER_DATA_DELETE_ON_ACCOUNT_DELETE': {
        'value': True,
        'description': '账号删除时清除数据',
        'type': 'data_security',
        'priority': 1
    }
}

# ==========================================
# 五、权限规则配置
# ==========================================

PERMISSION_RULES = {
    # 仪表盘访问权限
    'PERM_VIEW_DASHBOARD': {
        'value': ['student', 'student_vip', 'designer', 'teacher', 'admin', 
                  'super_admin', 'hardware_admin', 'hardware_vikey_admin'],
        'description': '查看仪表盘权限',
        'type': 'permission',
        'priority': 20
    },
    
    # 设置页面访问权限
    'PERM_VIEW_SETTINGS': {
        'value': ['admin', 'super_admin', 'hardware_admin', 'hardware_vikey_admin'],
        'description': '查看设置权限',
        'type': 'permission',
        'priority': 20
    },
    
    # 用户管理权限
    'PERM_MANAGE_USERS': {
        'value': ['admin', 'super_admin', 'hardware_admin', 'hardware_vikey_admin'],
        'description': '管理用户权限',
        'type': 'permission',
        'priority': 20
    },
    
    # 删除用户权限
    'PERM_DELETE_USER': {
        'value': ['super_admin', 'hardware_admin', 'hardware_vikey_admin'],
        'description': '删除用户权限',
        'type': 'permission',
        'priority': 25
    },
    
    # 数据库管理权限
    'PERM_MANAGE_DATABASE': {
        'value': ['super_admin', 'hardware_admin', 'hardware_vikey_admin'],
        'description': '管理数据库权限',
        'type': 'permission',
        'priority': 25
    },
    
    # 查看日志权限
    'PERM_VIEW_LOGS': {
        'value': ['admin', 'super_admin', 'hardware_admin', 'hardware_vikey_admin'],
        'description': '查看日志权限',
        'type': 'permission',
        'priority': 20
    },
    
    # 考试系统权限 - 强化规则：只有学生可以参加考试
    'PERM_TAKE_EXAM': {
        'value': ['student', 'student_vip'],
        'description': '参加考试权限 - 仅限学生',
        'type': 'permission',
        'priority': 30
    },
    
    # 创建考试权限
    'PERM_CREATE_EXAM': {
        'value': ['admin', 'super_admin', 'hardware_admin', 'exam_expert'],
        'description': '创建考试权限',
        'type': 'permission',
        'priority': 20
    },
    
    # 管理考试权限
    'PERM_MANAGE_EXAMS': {
        'value': ['admin', 'super_admin', 'hardware_admin', 'exam_expert'],
        'description': '管理考试权限',
        'type': 'permission',
        'priority': 20
    },
    
    # 题库管理权限
    'PERM_MANAGE_QUESTION_BANK': {
        'value': ['admin', 'super_admin', 'hardware_admin', 'exam_expert', 'teacher'],
        'description': '题库管理权限',
        'type': 'permission',
        'priority': 20
    },
    
    # AI功能权限
    'PERM_USE_AI_CHAT': {
        'value': ['student', 'student_vip', 'designer', 'teacher', 'admin', 
                  'super_admin', 'hardware_admin', 'researcher'],
        'description': '使用AI聊天权限',
        'type': 'permission',
        'priority': 10
    },
    
    # 硬件管理权限 - 最高权限
    'PERM_HARDWARE_ADMIN': {
        'value': ['hardware_admin', 'hardware_vikey_admin'],
        'description': '硬件管理权限 - 最高权限',
        'type': 'permission',
        'priority': 100
    },
    
    # v5.3.0 新增权限规则
    
    # 学习诊断权限
    'PERM_USE_LEARNING_DIAGNOSIS': {
        'value': ['student', 'student_vip', 'teacher', 'researcher', 'admin', 
                  'super_admin', 'hardware_admin'],
        'description': '使用学习诊断功能权限',
        'type': 'permission',
        'priority': 15
    },
    
    # 智能评估权限
    'PERM_USE_INTELLIGENT_EVALUATION': {
        'value': ['student', 'student_vip', 'teacher', 'researcher', 'admin', 
                  'super_admin', 'hardware_admin'],
        'description': '使用智能评估分析功能权限',
        'type': 'permission',
        'priority': 15
    },
    
    # 个性化学习路径权限
    'PERM_USE_LEARNING_PATH': {
        'value': ['student', 'student_vip', 'teacher', 'researcher'],
        'description': '使用个性化学习路径功能权限',
        'type': 'permission',
        'priority': 15
    },
    
    # AI智能推荐权限
    'PERM_USE_AI_RECOMMENDATION': {
        'value': ['student', 'student_vip', 'teacher', 'researcher', 'admin', 
                  'super_admin', 'hardware_admin'],
        'description': '使用AI智能推荐功能权限',
        'type': 'permission',
        'priority': 15
    },
    
    # 知识库访问权限
    'PERM_ACCESS_KNOWLEDGE_BASE': {
        'value': ['student', 'student_vip', 'teacher', 'designer', 'researcher', 
                  'admin', 'super_admin', 'hardware_admin'],
        'description': '访问智能知识库权限',
        'type': 'permission',
        'priority': 10
    },
    
    # 课堂互动权限
    'PERM_USE_CLASSROOM_INTERACTION': {
        'value': ['student', 'student_vip', 'teacher', 'admin', 'super_admin', 'hardware_admin'],
        'description': '使用课堂互动功能权限',
        'type': 'permission',
        'priority': 15
    },
    
    # AI员工管理权限
    'PERM_MANAGE_AI_EMPLOYEES': {
        'value': ['admin', 'super_admin', 'hardware_admin'],
        'description': '管理AI员工权限',
        'type': 'permission',
        'priority': 25
    },
    
    # AI脑库管理权限
    'PERM_MANAGE_BRAIN_BANK': {
        'value': ['admin', 'super_admin', 'hardware_admin', 'researcher'],
        'description': '管理AI脑库权限',
        'type': 'permission',
        'priority': 25
    },
    
    # 数据完整性管理权限
    'PERM_MANAGE_DATA_INTEGRITY': {
        'value': ['super_admin', 'hardware_admin'],
        'description': '管理数据完整性权限',
        'type': 'permission',
        'priority': 30
    },
    
    # 主动AI管理权限
    'PERM_MANAGE_PROACTIVE_AI': {
        'value': ['admin', 'super_admin', 'hardware_admin', 'researcher'],
        'description': '管理主动AI系统权限',
        'type': 'permission',
        'priority': 25
    },
    
    # 路由管理权限
    'PERM_MANAGE_ROUTES': {
        'value': ['super_admin', 'hardware_admin'],
        'description': '管理系统路由权限',
        'type': 'permission',
        'priority': 30
    },
    
    # 系统监控权限
    'PERM_VIEW_MONITORING': {
        'value': ['admin', 'super_admin', 'hardware_admin'],
        'description': '查看系统监控权限',
        'type': 'permission',
        'priority': 20
    },
    
    # 备份管理权限
    'PERM_MANAGE_BACKUPS': {
        'value': ['super_admin', 'hardware_admin', 'admin'],
        'description': '管理系统备份权限',
        'type': 'permission',
        'priority': 25
    },
    
    # 报表生成权限
    'PERM_GENERATE_REPORTS': {
        'value': ['teacher', 'researcher', 'admin', 'super_admin', 'hardware_admin'],
        'description': '生成数据报表权限',
        'type': 'permission',
        'priority': 20
    },
    
    # 学习记录管理权限
    'PERM_MANAGE_LEARNING_RECORDS': {
        'value': ['teacher', 'researcher', 'admin', 'super_admin', 'hardware_admin'],
        'description': '管理学习记录权限',
        'type': 'permission',
        'priority': 20
    },
    
    # 错题本管理权限
    'PERM_MANAGE_WRONG_QUESTIONS': {
        'value': ['student', 'student_vip', 'teacher', 'admin', 'super_admin', 'hardware_admin'],
        'description': '管理错题本权限',
        'type': 'permission',
        'priority': 15
    },
    
    # 学习分析权限
    'PERM_VIEW_LEARNING_ANALYTICS': {
        'value': ['student', 'student_vip', 'teacher', 'researcher', 'admin', 
                  'super_admin', 'hardware_admin'],
        'description': '查看学习分析权限',
        'type': 'permission',
        'priority': 15
    },
    
    # 系统配置编辑权限
    'PERM_EDIT_SYSTEM_CONFIG': {
        'value': ['super_admin', 'hardware_admin'],
        'description': '编辑系统配置权限',
        'type': 'permission',
        'priority': 35
    },
    
    # 安全配置权限
    'PERM_MANAGE_SECURITY': {
        'value': ['super_admin', 'hardware_admin'],
        'description': '管理安全配置权限',
        'type': 'permission',
        'priority': 35
    },
    
    # 审计日志查看权限
    'PERM_VIEW_AUDIT_LOGS': {
        'value': ['super_admin', 'hardware_admin', 'admin'],
        'description': '查看审计日志权限',
        'type': 'permission',
        'priority': 25
    }
}

# ==========================================
# 六、统一权限检查函数
# ==========================================

def is_super_admin(user_role: str) -> bool:
    """判断是否为超级管理员"""
    return user_role in SUPER_ADMIN_ROLES


def check_route_permission(route_path: str, user_role: str) -> tuple:
    """
    检查路由访问权限
    返回: (allowed: bool, reason: str)
    """
    # 超级管理员拥有所有路由访问权限
    if is_super_admin(user_role):
        return True, f"超级管理员 {user_role} 拥有所有路由访问权限"
    
    # 合并所有路由规则
    all_routes = {}
    all_routes.update(EXAM_SYSTEM_ROUTES)
    all_routes.update(TEST_SYSTEM_ROUTES)
    all_routes.update(LEARNING_SYSTEM_ROUTES)
    all_routes.update(USER_SYSTEM_ROUTES)
    all_routes.update(ADMIN_SYSTEM_ROUTES)
    
    # 查找匹配的路由规则
    for route_pattern, route_config in all_routes.items():
        # 简单匹配（支持动态参数）
        if route_pattern.replace('<exam_id>', '').replace('<id>', '') in route_path:
            allowed_roles = route_config.get('allowed_roles', [])
            
            if user_role in allowed_roles:
                return True, f"角色 {user_role} 允许访问 {route_path}"
            else:
                return False, f"角色 {user_role} 无权限访问 {route_path}，允许的角色: {allowed_roles}"
    
    # 未找到明确规则，默认允许已登录用户
    return True, "未找到明确规则，默认允许"


def check_permission_by_rule(rule_code: str, user_role: str) -> tuple:
    """
    根据规则检查权限
    返回: (allowed: bool, reason: str)
    """
    # 超级管理员拥有所有权限
    if is_super_admin(user_role):
        return True, f"超级管理员 {user_role} 拥有所有权限"
    
    rule = PERMISSION_RULES.get(rule_code)
    
    if not rule:
        return False, f"规则 {rule_code} 不存在"
    
    allowed_roles = rule.get('value', [])
    
    if user_role in allowed_roles or '*' in allowed_roles:
        return True, f"角色 {user_role} 拥有 {rule_code} 权限"
    else:
        return False, f"角色 {user_role} 无 {rule_code} 权限，允许的角色: {allowed_roles}"


def get_role_level(role: str) -> int:
    """获取角色等级"""
    return ROLE_HIERARCHY.get(role, 0)


def is_role_higher_than(role1: str, role2: str) -> bool:
    """判断角色1是否高于角色2"""
    return get_role_level(role1) > get_role_level(role2)


def get_system_rule(rule_code: str):
    """获取系统规则值"""
    rule = SYSTEM_RULES.get(rule_code) or DATA_SECURITY_RULES.get(rule_code)
    return rule.get('value') if rule else None


# ==========================================
# 七、初始化函数
# ==========================================

def init_unified_rules(db_path: str):
    """
    初始化统一规则到数据库
    """
    import sqlite3
    import json
    
    try:
        with sqlite3.connect(db_path) as conn:
            cursor = conn.cursor()
            
            # 更新权限规则
            for rule_code, rule_config in PERMISSION_RULES.items():
                value_str = json.dumps(rule_config['value']) if isinstance(rule_config['value'], list) else str(rule_config['value'])
                cursor.execute('''
                    INSERT OR REPLACE INTO system_rules 
                    (rule_code, rule_name, rule_description, rule_type, rule_value, priority, is_active)
                    VALUES (?, ?, ?, ?, ?, ?, 1)
                ''', (rule_code, rule_config['description'], rule_config['description'], 
                      rule_config['type'], value_str, rule_config['priority']))
            
            # 更新系统规则
            for rule_code, rule_config in SYSTEM_RULES.items():
                value_str = json.dumps(rule_config['value']) if isinstance(rule_config['value'], list) else str(rule_config['value'])
                cursor.execute('''
                    INSERT OR REPLACE INTO system_rules 
                    (rule_code, rule_name, rule_description, rule_type, rule_value, priority, is_active)
                    VALUES (?, ?, ?, ?, ?, ?, 1)
                ''', (rule_code, rule_config['description'], rule_config['description'], 
                      rule_config['type'], value_str, rule_config['priority']))
            
            # 更新数据安全规则
            for rule_code, rule_config in DATA_SECURITY_RULES.items():
                value_str = json.dumps(rule_config['value']) if isinstance(rule_config['value'], list) else str(rule_config['value'])
                cursor.execute('''
                    INSERT OR REPLACE INTO system_rules 
                    (rule_code, rule_name, rule_description, rule_type, rule_value, priority, is_active)
                    VALUES (?, ?, ?, ?, ?, ?, 1)
                ''', (rule_code, rule_config['description'], rule_config['description'], 
                      rule_config['type'], value_str, rule_config['priority']))
            
            conn.commit()
            
        logger.info(f"[统一规则] 初始化完成，已更新 {len(PERMISSION_RULES) + len(SYSTEM_RULES) + len(DATA_SECURITY_RULES)} 条规则")
        return True
        
    except Exception as e:
        logger.error(f"[统一规则] 初始化失败: {e}")
        return False


# ==========================================
# 七、权限常量定义（v5.3.0新增）
# ==========================================

PERMISSION_CONSTANTS = {
    'VIEW_ONLY': ['PERM_VIEW_DASHBOARD', 'PERM_VIEW_SETTINGS', 'PERM_VIEW_LOGS', 
                  'PERM_VIEW_MONITORING', 'PERM_VIEW_LEARNING_ANALYTICS', 'PERM_VIEW_AUDIT_LOGS'],
    'USER_MANAGEMENT': ['PERM_MANAGE_USERS', 'PERM_DELETE_USER'],
    'SYSTEM_ADMIN': ['PERM_MANAGE_DATABASE', 'PERM_MANAGE_ROUTES', 'PERM_EDIT_SYSTEM_CONFIG', 
                     'PERM_MANAGE_SECURITY', 'PERM_MANAGE_DATA_INTEGRITY'],
    'AI_FEATURES': ['PERM_USE_AI_CHAT', 'PERM_USE_LEARNING_DIAGNOSIS', 'PERM_USE_INTELLIGENT_EVALUATION', 
                    'PERM_USE_LEARNING_PATH', 'PERM_USE_AI_RECOMMENDATION', 'PERM_ACCESS_KNOWLEDGE_BASE', 
                    'PERM_USE_CLASSROOM_INTERACTION'],
    'AI_ADMIN': ['PERM_MANAGE_AI_EMPLOYEES', 'PERM_MANAGE_BRAIN_BANK', 'PERM_MANAGE_PROACTIVE_AI'],
    'EXAM_FEATURES': ['PERM_TAKE_EXAM', 'PERM_CREATE_EXAM', 'PERM_MANAGE_EXAMS', 'PERM_MANAGE_QUESTION_BANK'],
    'LEARNING_FEATURES': ['PERM_MANAGE_LEARNING_RECORDS', 'PERM_MANAGE_WRONG_QUESTIONS', 'PERM_GENERATE_REPORTS']
}

# ==========================================
# 八、导出所有规则
# ==========================================

__all__ = [
    'EXAM_SYSTEM_ROUTES',
    'TEST_SYSTEM_ROUTES',
    'LEARNING_SYSTEM_ROUTES',
    'USER_SYSTEM_ROUTES',
    'ADMIN_SYSTEM_ROUTES',
    'ROLE_HIERARCHY',
    'ROLE_DESCRIPTIONS',
    'SYSTEM_RULES',
    'DATA_SECURITY_RULES',
    'PERMISSION_RULES',
    'PERMISSION_CONSTANTS',
    'check_route_permission',
    'check_permission_by_rule',
    'get_role_level',
    'is_role_higher_than',
    'get_system_rule',
    'init_unified_rules'
]