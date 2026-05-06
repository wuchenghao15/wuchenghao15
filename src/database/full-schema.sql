-- 项目完整数据库结构
-- 存储所有参数、设置、用户信息和产生的数据

-- 用户表
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT UNIQUE NOT NULL,
    password TEXT NOT NULL,
    email TEXT UNIQUE,
    role TEXT DEFAULT 'user', -- admin, user
    status TEXT DEFAULT 'active',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 用户详细信息表
CREATE TABLE IF NOT EXISTS user_profiles (
    user_id INTEGER PRIMARY KEY,
    full_name TEXT,
    avatar TEXT,
    bio TEXT,
    learning_goal TEXT,
    last_login TIMESTAMP,
    login_count INTEGER DEFAULT 0,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);

-- 用户学习进度表
CREATE TABLE IF NOT EXISTS user_learning_progress (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    level TEXT NOT NULL, -- N1-N5
    type TEXT NOT NULL, -- listening, vocabulary, grammar, reading, writing
    progress REAL DEFAULT 0, -- 0-100
    last_practiced TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    total_questions INTEGER DEFAULT 0,
    correct_questions INTEGER DEFAULT 0,
    accuracy REAL DEFAULT 0,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    UNIQUE(user_id, level, type)
);

-- 用户答题记录表
CREATE TABLE IF NOT EXISTS user_answers (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    question_id INTEGER NOT NULL,
    answer TEXT,
    is_correct INTEGER DEFAULT 0,
    answered_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    time_spent INTEGER, -- 答题时间（秒）
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    FOREIGN KEY (question_id) REFERENCES questions(id) ON DELETE CASCADE
);

-- 系统设置表
CREATE TABLE IF NOT EXISTS system_settings (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    key TEXT UNIQUE NOT NULL,
    value TEXT NOT NULL,
    description TEXT,
    category TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 服务器配置表
CREATE TABLE IF NOT EXISTS server_config (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    config_key TEXT UNIQUE NOT NULL,
    config_value TEXT NOT NULL,
    description TEXT,
    is_active INTEGER DEFAULT 1,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 安全设置表
CREATE TABLE IF NOT EXISTS security_settings (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    setting_key TEXT UNIQUE NOT NULL,
    setting_value TEXT NOT NULL,
    description TEXT,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 生成的试卷表
CREATE TABLE IF NOT EXISTS generated_tests (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER,
    level TEXT NOT NULL,
    question_count INTEGER NOT NULL,
    questions TEXT NOT NULL, -- JSON格式存储题目ID列表
    generated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    completed_at TIMESTAMP,
    score INTEGER,
    status TEXT DEFAULT 'generated', -- generated, completed, expired
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE SET NULL
);

-- 音频数据表
CREATE TABLE IF NOT EXISTS audio_data (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    type TEXT NOT NULL, -- listening, system
    level TEXT, -- N1-N5
    data_url TEXT NOT NULL,
    duration INTEGER, -- 秒
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    usage_count INTEGER DEFAULT 0
);

-- 题目表
CREATE TABLE IF NOT EXISTS questions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    level TEXT NOT NULL, -- N1-N5
    type TEXT NOT NULL, -- listening, vocabulary, grammar, reading, writing
    question TEXT NOT NULL,
    options TEXT, -- JSON格式存储选项
    answer TEXT,
    explanation TEXT,
    audio_id INTEGER, -- 关联的音频ID
    scenario TEXT, -- 场景描述
    passage TEXT, -- 阅读文章
    difficulty INTEGER, -- 1-5
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (audio_id) REFERENCES audio_data(id) ON DELETE SET NULL
);

-- 分析报告表
CREATE TABLE IF NOT EXISTS analysis_reports (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER,
    report_type TEXT NOT NULL, -- user_analysis, system_analysis
    content TEXT NOT NULL, -- JSON格式存储报告内容
    generated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE SET NULL
);

-- 系统监控数据表
CREATE TABLE IF NOT EXISTS system_monitoring (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    metric_type TEXT NOT NULL, -- cpu, memory, disk, network
    metric_value REAL NOT NULL,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    status TEXT DEFAULT 'normal' -- normal, warning, critical
);

-- 安全事件表
CREATE TABLE IF NOT EXISTS security_events (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    event_type TEXT NOT NULL, -- login_attempt, access_denied, data_access
    severity TEXT DEFAULT 'info', -- info, warning, error, critical
    description TEXT NOT NULL,
    ip_address TEXT,
    user_agent TEXT,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    user_id INTEGER,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE SET NULL
);

-- 操作日志表
CREATE TABLE IF NOT EXISTS audit_logs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER,
    action TEXT NOT NULL,
    resource TEXT NOT NULL,
    description TEXT,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    ip_address TEXT,
    user_agent TEXT,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE SET NULL
);

-- 版本管理表
CREATE TABLE IF NOT EXISTS version_management (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    version TEXT UNIQUE NOT NULL,
    major INTEGER NOT NULL,
    minor INTEGER NOT NULL,
    patch INTEGER NOT NULL,
    build INTEGER DEFAULT 0,
    prerelease TEXT,
    is_current INTEGER DEFAULT 0,
    status TEXT DEFAULT 'released', -- development, testing, released, deprecated
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 版本历史表
CREATE TABLE IF NOT EXISTS version_history (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    version_id INTEGER NOT NULL,
    version TEXT NOT NULL,
    change_type TEXT NOT NULL, -- major, minor, patch, build, prerelease
    changes TEXT, -- JSON格式存储变更内容
    created_by INTEGER,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (version_id) REFERENCES version_management(id) ON DELETE CASCADE,
    FOREIGN KEY (created_by) REFERENCES users(id) ON DELETE SET NULL
);

-- 版本变更表
CREATE TABLE IF NOT EXISTS version_changes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    version_history_id INTEGER NOT NULL,
    change_type TEXT NOT NULL, -- feature, bugfix, improvement, security
    description TEXT NOT NULL,
    FOREIGN KEY (version_history_id) REFERENCES version_history(id) ON DELETE CASCADE
);

-- 逻辑结构树表
CREATE TABLE IF NOT EXISTS logic_structure_tree (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    node_id TEXT UNIQUE NOT NULL, -- 节点唯一标识
    node_name TEXT NOT NULL, -- 节点名称
    node_type TEXT NOT NULL, -- 节点类型（root, branch, leaf）
    level INTEGER NOT NULL, -- 层级深度
    parent_id INTEGER, -- 父节点ID
    path TEXT NOT NULL, -- 节点路径（如：1/2/3）
    status TEXT DEFAULT 'active', -- active, inactive, deleted
    description TEXT, -- 节点描述
    metadata TEXT, -- JSON格式存储附加信息
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (parent_id) REFERENCES logic_structure_tree(id) ON DELETE CASCADE
);

-- 逻辑信息表
CREATE TABLE IF NOT EXISTS logic_information (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    structure_id INTEGER NOT NULL, -- 关联的结构节点ID
    info_key TEXT NOT NULL, -- 信息键
    info_value TEXT NOT NULL, -- 信息值
    info_type TEXT DEFAULT 'string', -- string, number, boolean, json
    category TEXT, -- 信息分类
    description TEXT, -- 信息描述
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (structure_id) REFERENCES logic_structure_tree(id) ON DELETE CASCADE,
    UNIQUE(structure_id, info_key)
);

-- 逻辑结构关系表
CREATE TABLE IF NOT EXISTS logic_structure_relations (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    parent_id INTEGER NOT NULL, -- 父节点ID
    child_id INTEGER NOT NULL, -- 子节点ID
    relation_type TEXT DEFAULT 'hierarchy', -- hierarchy, reference, dependency
    order_index INTEGER DEFAULT 0, -- 子节点排序索引
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (parent_id) REFERENCES logic_structure_tree(id) ON DELETE CASCADE,
    FOREIGN KEY (child_id) REFERENCES logic_structure_tree(id) ON DELETE CASCADE,
    UNIQUE(parent_id, child_id)
);

-- 创建索引以优化查询性能
CREATE INDEX IF NOT EXISTS idx_users_username ON users(username);
CREATE INDEX IF NOT EXISTS idx_users_email ON users(email);
CREATE INDEX IF NOT EXISTS idx_user_learning_progress_user ON user_learning_progress(user_id);
CREATE INDEX IF NOT EXISTS idx_user_answers_user ON user_answers(user_id);
CREATE INDEX IF NOT EXISTS idx_user_answers_question ON user_answers(question_id);
CREATE INDEX IF NOT EXISTS idx_generated_tests_user ON generated_tests(user_id);
CREATE INDEX IF NOT EXISTS idx_generated_tests_status ON generated_tests(status);
CREATE INDEX IF NOT EXISTS idx_system_monitoring_type ON system_monitoring(metric_type);
CREATE INDEX IF NOT EXISTS idx_security_events_type ON security_events(event_type);
CREATE INDEX IF NOT EXISTS idx_audit_logs_user ON audit_logs(user_id);
CREATE INDEX IF NOT EXISTS idx_audit_logs_action ON audit_logs(action);
CREATE INDEX IF NOT EXISTS idx_version_management_version ON version_management(version);
CREATE INDEX IF NOT EXISTS idx_version_management_current ON version_management(is_current);
CREATE INDEX IF NOT EXISTS idx_version_history_version ON version_history(version);
CREATE INDEX IF NOT EXISTS idx_logic_structure_tree_parent ON logic_structure_tree(parent_id);
CREATE INDEX IF NOT EXISTS idx_logic_structure_tree_level ON logic_structure_tree(level);
CREATE INDEX IF NOT EXISTS idx_logic_structure_tree_path ON logic_structure_tree(path);
CREATE INDEX IF NOT EXISTS idx_logic_information_structure ON logic_information(structure_id);
CREATE INDEX IF NOT EXISTS idx_logic_structure_relations_parent ON logic_structure_relations(parent_id);
CREATE INDEX IF NOT EXISTS idx_logic_structure_relations_child ON logic_structure_relations(child_id);

-- 初始化系统设置
INSERT OR IGNORE INTO system_settings (key, value, description, category) VALUES
('system_name', 'MTSCOS AI Project', '系统名称', 'general'),
('system_version', '1.0.0', '系统版本', 'general'),
('max_users', '1000', '最大用户数', 'limits'),
('max_questions_per_test', '100', '每试卷最大题目数', 'limits'),
('auto_logout_time', '3600', '自动登出时间（秒）', 'security'),
('session_timeout', '7200', '会话超时时间（秒）', 'security'),
('enable_monitoring', '1', '启用监控', 'system'),
('enable_audit_log', '1', '启用审计日志', 'security');

-- 初始化服务器配置
INSERT OR IGNORE INTO server_config (config_key, config_value, description, is_active) VALUES
('port', '8080', '服务器端口', 1),
('host', 'localhost', '服务器主机', 1),
('max_request_size', '10mb', '最大请求大小', 1),
('enable_cors', '1', '启用CORS', 1),
('log_level', 'info', '日志级别', 1),
('workers', '1', '工作进程数', 1);

-- 初始化安全设置
INSERT OR IGNORE INTO security_settings (setting_key, setting_value, description) VALUES
('password_min_length', '8', '密码最小长度'),
('password_require_uppercase', '1', '密码要求大写字母'),
('password_require_lowercase', '1', '密码要求小写字母'),
('password_require_number', '1', '密码要求数字'),
('password_require_special', '1', '密码要求特殊字符'),
('login_attempt_limit', '5', '登录尝试限制'),
('lockout_duration', '300', '锁定持续时间（秒）'),
('enable_2fa', '0', '启用双因素认证');

-- 初始化版本管理
INSERT OR IGNORE INTO version_management (version, major, minor, patch, build, prerelease, is_current, status) VALUES
('1.0.0', 1, 0, 0, 0, NULL, 1, 'released');

-- 初始化逻辑结构树（创建根节点）
INSERT OR IGNORE INTO logic_structure_tree (node_id, node_name, node_type, level, parent_id, path, status, description) VALUES
('root', '系统根节点', 'root', 0, NULL, '0', 'active', '逻辑结构树的根节点');

-- 配色方案配置表
CREATE TABLE IF NOT EXISTS theme_config (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    theme_name TEXT UNIQUE NOT NULL, -- light, dark, gray, festive
    theme_type TEXT NOT NULL, -- system, custom
    config_data TEXT NOT NULL, -- JSON格式存储配色方案配置
    is_active INTEGER DEFAULT 1,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 国家公祭日表
CREATE TABLE IF NOT EXISTS national_mourning_days (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    date TEXT UNIQUE NOT NULL, -- 格式：YYYY-MM-DD
    name TEXT NOT NULL, -- 公祭日名称
    description TEXT,
    is_active INTEGER DEFAULT 1,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 用户权限扩展表
CREATE TABLE IF NOT EXISTS user_permissions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    permission_type TEXT NOT NULL, -- theme_management, system_config, etc.
    permission_level INTEGER DEFAULT 0, -- 0: 无权限, 1: 查看, 2: 修改, 3: 完全控制
    is_active INTEGER DEFAULT 1,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    UNIQUE(user_id, permission_type)
);

-- 日出日落时间表
CREATE TABLE IF NOT EXISTS sunrise_sunset_times (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    date TEXT UNIQUE NOT NULL, -- 格式：YYYY-MM-DD
    sunrise_time TEXT, -- 格式：HH:MM
    sunset_time TEXT, -- 格式：HH:MM
    location TEXT DEFAULT 'Beijing',
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 主题变更日志表
CREATE TABLE IF NOT EXISTS theme_change_logs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER,
    action TEXT NOT NULL, -- theme_switch, theme_update, etc.
    theme_name TEXT,
    old_config TEXT,
    new_config TEXT,
    ip_address TEXT,
    user_agent TEXT,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE SET NULL
);

-- 日志表
CREATE TABLE IF NOT EXISTS logs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp TEXT NOT NULL,
    level TEXT NOT NULL,
    module TEXT NOT NULL,
    message TEXT NOT NULL,
    metadata TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 创建新表的索引
CREATE INDEX IF NOT EXISTS idx_user_permissions_user ON user_permissions(user_id);
CREATE INDEX IF NOT EXISTS idx_national_mourning_days_date ON national_mourning_days(date);
CREATE INDEX IF NOT EXISTS idx_sunrise_sunset_times_date ON sunrise_sunset_times(date);
CREATE INDEX IF NOT EXISTS idx_theme_change_logs_user ON theme_change_logs(user_id);
CREATE INDEX IF NOT EXISTS idx_logs_timestamp ON logs(timestamp);
CREATE INDEX IF NOT EXISTS idx_logs_level ON logs(level);
CREATE INDEX IF NOT EXISTS idx_logs_module ON logs(module);
CREATE INDEX IF NOT EXISTS idx_logs_created_at ON logs(created_at);

-- 初始化配色方案配置
INSERT OR IGNORE INTO theme_config (theme_name, theme_type, config_data, is_active) VALUES
('light', 'system', '{"primary_color": "#2563eb", "primary_gradient": "linear-gradient(135deg, #2563eb 0%, #3b82f6 100%)", "primary_hover": "#1d4ed8", "primary_light": "#dbeafe", "bg_primary": "#ffffff", "bg_secondary": "#f8fafc", "text_primary": "#0f172a", "text_secondary": "#475569"}', 1),
('dark', 'system', '{"primary_color": "#3b82f6", "primary_gradient": "linear-gradient(135deg, #3b82f6 0%, #60a5fa 100%)", "primary_hover": "#2563eb", "primary_light": "#1e40af", "bg_primary": "#0f172a", "bg_secondary": "#1e293b", "text_primary": "#f8fafc", "text_secondary": "#cbd5e1"}', 1),
('gray', 'system', '{"primary_color": "#64748b", "primary_gradient": "linear-gradient(135deg, #64748b 0%, #94a3b8 100%)", "primary_hover": "#475569", "primary_light": "#f1f5f9", "bg_primary": "#fafafa", "bg_secondary": "#f5f5f5", "text_primary": "#374151", "text_secondary": "#6b7280"}', 1),
('festive', 'system', '{"primary_color": "#dc2626", "primary_gradient": "linear-gradient(135deg, #dc2626 0%, #ef4444 100%)", "primary_hover": "#b91c1c", "primary_light": "#fee2e2", "bg_primary": "#fef2f2", "bg_secondary": "#fef7f7", "text_primary": "#7f1d1d", "text_secondary": "#b91c1c"}', 1);

-- 初始化国家公祭日
INSERT OR IGNORE INTO national_mourning_days (date, name, description, is_active) VALUES
('09-18', '九一八事变纪念日', '纪念1931年9月18日九一八事变', 1),
('12-13', '南京大屠杀死难者国家公祭日', '纪念1937年12月13日南京大屠杀', 1),
('05-12', '汶川地震纪念日', '纪念2008年5月12日汶川地震', 1),
('04-04', '清明节', '传统祭祀节日', 1),
('12-22', '冬至', '传统祭祀节日', 1);

-- 更新系统设置，添加主题相关配置
INSERT OR IGNORE INTO system_settings (key, value, description, category) VALUES
('theme_auto_switch', '1', '启用主题自动切换', 'theme'),
('theme_default', 'light', '默认主题', 'theme'),
('theme_sunrise_sunset', '1', '启用日出日落主题切换', 'theme'),
('theme_national_mourning', '1', '启用国家公祭日主题', 'theme');

-- 本地化信息表
CREATE TABLE IF NOT EXISTS localization_configs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    config_key TEXT UNIQUE NOT NULL,
    config_type TEXT NOT NULL,
    config_data TEXT NOT NULL,
    description TEXT,
    category TEXT,
    is_active INTEGER DEFAULT 1,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 本地化功能表
CREATE TABLE IF NOT EXISTS localization_features (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    feature_name TEXT UNIQUE NOT NULL,
    feature_data TEXT NOT NULL,
    status TEXT DEFAULT 'inactive',
    description TEXT,
    dependencies TEXT,
    api_endpoints TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 本地化环境表
CREATE TABLE IF NOT EXISTS localization_environments (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    environment_name TEXT UNIQUE NOT NULL,
    environment_data TEXT NOT NULL,
    environment_type TEXT DEFAULT 'development',
    status TEXT DEFAULT 'inactive',
    description TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 本地化安全表
CREATE TABLE IF NOT EXISTS localization_security (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    security_key TEXT UNIQUE NOT NULL,
    security_data TEXT NOT NULL,
    security_type TEXT DEFAULT 'general',
    description TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 本地化资源表
CREATE TABLE IF NOT EXISTS localization_resources (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    resource_key TEXT UNIQUE NOT NULL,
    resource_data TEXT NOT NULL,
    resource_type TEXT DEFAULT 'general',
    description TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 用户会话表
CREATE TABLE IF NOT EXISTS user_sessions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    session_token TEXT UNIQUE NOT NULL,
    ip_address TEXT,
    user_agent TEXT,
    last_activity TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    expires_at TIMESTAMP NOT NULL,
    is_active INTEGER DEFAULT 1,
    remember_me INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);

-- 认证令牌表
CREATE TABLE IF NOT EXISTS auth_tokens (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    token TEXT UNIQUE NOT NULL,
    token_type TEXT DEFAULT 'access', -- access, refresh
    expires_at TIMESTAMP NOT NULL,
    is_revoked INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);

-- 登录尝试表
CREATE TABLE IF NOT EXISTS login_attempts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT NOT NULL,
    ip_address TEXT,
    user_agent TEXT,
    is_successful INTEGER DEFAULT 0,
    error_message TEXT,
    attempt_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 账户锁定表
CREATE TABLE IF NOT EXISTS account_locks (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT UNIQUE NOT NULL,
    locked_until TIMESTAMP NOT NULL,
    lock_reason TEXT,
    failed_attempts INTEGER DEFAULT 0,
    last_attempt TIMESTAMP,
    is_locked INTEGER DEFAULT 1,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 创建本地化信息表索引
CREATE INDEX IF NOT EXISTS idx_localization_configs_key ON localization_configs(config_key);
CREATE INDEX IF NOT EXISTS idx_localization_configs_type ON localization_configs(config_type);
CREATE INDEX IF NOT EXISTS idx_localization_configs_category ON localization_configs(category);
CREATE INDEX IF NOT EXISTS idx_localization_features_name ON localization_features(feature_name);
CREATE INDEX IF NOT EXISTS idx_localization_features_status ON localization_features(status);
CREATE INDEX IF NOT EXISTS idx_localization_environments_name ON localization_environments(environment_name);
CREATE INDEX IF NOT EXISTS idx_localization_environments_type ON localization_environments(environment_type);
CREATE INDEX IF NOT EXISTS idx_localization_security_key ON localization_security(security_key);
CREATE INDEX IF NOT EXISTS idx_localization_security_type ON localization_security(security_type);
CREATE INDEX IF NOT EXISTS idx_localization_resources_key ON localization_resources(resource_key);
CREATE INDEX IF NOT EXISTS idx_localization_resources_type ON localization_resources(resource_type);

-- 创建用户会话和认证相关索引
CREATE INDEX IF NOT EXISTS idx_user_sessions_user ON user_sessions(user_id);
CREATE INDEX IF NOT EXISTS idx_user_sessions_token ON user_sessions(session_token);
CREATE INDEX IF NOT EXISTS idx_user_sessions_expires ON user_sessions(expires_at);
CREATE INDEX IF NOT EXISTS idx_user_sessions_active ON user_sessions(is_active);
CREATE INDEX IF NOT EXISTS idx_auth_tokens_user ON auth_tokens(user_id);
CREATE INDEX IF NOT EXISTS idx_auth_tokens_token ON auth_tokens(token);
CREATE INDEX IF NOT EXISTS idx_auth_tokens_expires ON auth_tokens(expires_at);
CREATE INDEX IF NOT EXISTS idx_auth_tokens_revoked ON auth_tokens(is_revoked);
CREATE INDEX IF NOT EXISTS idx_login_attempts_username ON login_attempts(username);
CREATE INDEX IF NOT EXISTS idx_login_attempts_time ON login_attempts(attempt_time);
CREATE INDEX IF NOT EXISTS idx_account_locks_username ON account_locks(username);
CREATE INDEX IF NOT EXISTS idx_account_locks_locked_until ON account_locks(locked_until);
CREATE INDEX IF NOT EXISTS idx_account_locks_is_locked ON account_locks(is_locked);