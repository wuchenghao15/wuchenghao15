-- 插入硬件管理员用户
INSERT OR IGNORE INTO users (username, password, email, role, is_active, super_admin_approved, hardware_admin_approved) VALUES (
    'wuchenghao15',
    'LoginMe.1988',
    'wuchenghao_15@163.com',
    'hardware_admin',
    1,
    1,
    1
);

-- 插入超级管理员用户
INSERT OR IGNORE INTO users (username, password, email, role, is_active, super_admin_approved, hardware_admin_approved) VALUES (
    'wuchenghao16',
    'ppo900lik',
    '2@2.com',
    'super_admin',
    1,
    1,
    1
);

-- 插入普通用户
INSERT OR IGNORE INTO users (username, password, email, role, is_active, super_admin_approved, hardware_admin_approved) VALUES (
    'caopw',
    'xuxu2pipo',
    '1175061512@qq.com',
    'user',
    1,
    1,
    1
);

-- 查询插入结果
SELECT id, username, email, role, is_active, super_admin_approved, hardware_admin_approved FROM users;
