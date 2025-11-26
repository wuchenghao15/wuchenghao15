/**
 * 管理员权限验证模块
 * 功能：处理用户认证、权限验证、会话管理等核心安全功能
 */

// 全局认证状态
const authState = {
    currentUser: null,
    isAuthenticated: false,
    sessionExpiresAt: null,
    requiredAdminCount: 3,  // 修改密码需要的管理员数量
    superAdminRole: 'vikey_admin', // 超级管理员角色
    activeApprovals: {},    // 活跃的多管理员审批列表
    permissionLevels: {
        user: 1,            // 普通用户
        password_admin: 2,  // 密码管理员
        administrator: 3,   // 管理员
        vikey_admin: 4      // Vikey管理员（最高权限）
    },
    permissionActions: {
        VIEW_RULES: 'view_rules',
        EDIT_RULES: 'edit_rules',
        MANAGE_USERS: 'manage_users',
        CHANGE_PASSWORD: 'change_password',
        MANAGE_SYSTEM: 'manage_system',
        REPAIR_SYSTEM: 'repair_system',
        APPROVE_CHANGES: 'approve_changes'
    }
};

// 模拟用户数据库（实际应用中应使用后端API）
const mockUserDatabase = [
    {
        username: 'vikey_admin',
        password: 'secure_password_vikey', // 实际应用中应使用加密存储
        role: 'vikey_admin',
        permissions: ['view_rules', 'edit_rules', 'manage_users', 'change_password', 'manage_system', 'repair_system', 'approve_changes'],
        fullName: '系统管理员',
        email: 'admin@example.com',
        lastLogin: null,
        isActive: true,
        createdAt: '2024-01-01T00:00:00Z'
    },
    {
        username: 'admin1',
        password: 'secure_password1',
        role: 'administrator',
        permissions: ['view_rules', 'edit_rules', 'manage_system', 'repair_system'],
        fullName: '管理员1',
        email: 'admin1@example.com',
        lastLogin: null,
        isActive: true,
        createdAt: '2024-01-05T00:00:00Z'
    },
    {
        username: 'admin2',
        password: 'secure_password2',
        role: 'administrator',
        permissions: ['view_rules', 'edit_rules', 'manage_system', 'repair_system'],
        fullName: '管理员2',
        email: 'admin2@example.com',
        lastLogin: null,
        isActive: true,
        createdAt: '2024-01-05T00:00:00Z'
    },
    {
        username: 'pass_admin',
        password: 'secure_password_pass',
        role: 'password_admin',
        permissions: ['view_rules', 'change_password', 'approve_changes'],
        fullName: '密码管理员',
        email: 'pass_admin@example.com',
        lastLogin: null,
        isActive: true,
        createdAt: '2024-01-10T00:00:00Z'
    },
    {
        username: 'regular_user',
        password: 'user_password',
        role: 'user',
        permissions: ['view_rules'],
        fullName: '普通用户',
        email: 'user@example.com',
        lastLogin: null,
        isActive: true,
        createdAt: '2024-01-15T00:00:00Z'
    }
];

// 模拟审批历史数据库
const mockApprovalHistory = [
    {
        id: 'APPROVAL-001',
        type: 'password_change',
        targetUser: 'admin1',
        requestedBy: 'admin2',
        requestedAt: '2024-01-18T10:30:00Z',
        approvals: [
            { username: 'vikey_admin', approvedAt: '2024-01-18T10:35:00Z' }
        ],
        status: 'approved',
        completedAt: '2024-01-18T10:35:00Z'
    },
    {
        id: 'APPROVAL-002',
        type: 'system_update',
        targetUser: null,
        requestedBy: 'admin1',
        requestedAt: '2024-01-19T14:20:00Z',
        approvals: [
            { username: 'admin2', approvedAt: '2024-01-19T14:30:00Z' },
            { username: 'pass_admin', approvedAt: '2024-01-19T14:45:00Z' }
        ],
        status: 'approved',
        completedAt: '2024-01-19T14:45:00Z'
    }
];

/**
 * 初始化认证模块
 */
function initializeAuth() {
    try {
        // 检查本地存储中的会话信息
        checkStoredSession();
        
        // 设置会话超时检查间隔
        setInterval(checkSessionTimeout, 60000); // 每分钟检查一次
        
        console.log('认证模块初始化完成');
    } catch (error) {
        console.error('认证模块初始化失败:', error);
    }
}

/**
 * 检查本地存储中的会话信息
 */
function checkStoredSession() {
    try {
        const storedSession = localStorage.getItem('auth_session');
        if (storedSession) {
            const sessionData = JSON.parse(storedSession);
            const now = new Date().getTime();
            
            // 验证会话是否有效
            if (sessionData.expiresAt && sessionData.expiresAt > now) {
                // 恢复会话状态
                authState.currentUser = sessionData.user;
                authState.isAuthenticated = true;
                authState.sessionExpiresAt = new Date(sessionData.expiresAt);
                
                console.log('已恢复存储的会话:', sessionData.user.username);
                return true;
            } else {
                // 会话已过期
                localStorage.removeItem('auth_session');
                console.log('存储的会话已过期');
            }
        }
        
        return false;
    } catch (error) {
        console.error('检查存储会话失败:', error);
        localStorage.removeItem('auth_session');
        return false;
    }
}

/**
 * 检查会话超时
 */
function checkSessionTimeout() {
    if (!authState.isAuthenticated || !authState.sessionExpiresAt) return;
    
    const now = new Date().getTime();
    const expiresAt = authState.sessionExpiresAt.getTime();
    
    // 提前5分钟提醒会话即将过期
    const warningThreshold = 5 * 60 * 1000;
    
    if (now > expiresAt) {
        // 会话已过期
        handleSessionExpired();
    } else if (expiresAt - now < warningThreshold) {
        // 会话即将过期，提醒用户
        notifySessionAboutToExpire(expiresAt - now);
    }
}

/**
 * 处理会话过期
 */
function handleSessionExpired() {
    console.log('会话已过期，需要重新登录');
    
    // 清除会话状态
    authState.currentUser = null;
    authState.isAuthenticated = false;
    authState.sessionExpiresAt = null;
    localStorage.removeItem('auth_session');
    
    // 显示会话过期提示
    if (window.addNotification) {
        window.addNotification('您的会话已过期，请重新登录', 'error');
    }
    
    // 如果在登录页面，则不进行重定向
    if (window.location.pathname !== '/login.html') {
        window.location.href = '/login.html';
    }
}

/**
 * 通知用户会话即将过期
 */
function notifySessionAboutToExpire(msRemaining) {
    const minutesRemaining = Math.ceil(msRemaining / (1000 * 60));
    
    if (window.addNotification) {
        window.addNotification(
            `您的会话将在 ${minutesRemaining} 分钟后过期，请及时操作或重新登录`, 
            'warning'
        );
    }
}

/**
 * 用户登录
 */
async function login(username, password) {
    try {
        // 模拟API调用延迟
        await new Promise(resolve => setTimeout(resolve, 800));
        
        // 查找用户
        const user = mockUserDatabase.find(u => u.username === username && u.password === password);
        
        if (!user) {
            throw new Error('用户名或密码错误');
        }
        
        if (!user.isActive) {
            throw new Error('用户账户已被禁用');
        }
        
        // 更新最后登录时间
        user.lastLogin = new Date().toISOString();
        
        // 设置认证状态
        authState.currentUser = { ...user };
        authState.isAuthenticated = true;
        
        // 设置会话过期时间（默认8小时）
        const expiresAt = new Date();
        expiresAt.setHours(expiresAt.getHours() + 8);
        authState.sessionExpiresAt = expiresAt;
        
        // 存储会话信息到本地存储
        const sessionData = {
            user: authState.currentUser,
            expiresAt: expiresAt.getTime(),
            createdAt: new Date().getTime()
        };
        localStorage.setItem('auth_session', JSON.stringify(sessionData));
        
        // 记录登录日志
        logAuthEvent('login', username, 'success');
        
        return {
            success: true,
            user: { ...user },
            message: '登录成功'
        };
        
    } catch (error) {
        // 记录失败的登录尝试
        logAuthEvent('login', username, 'failure', error.message);
        
        return {
            success: false,
            message: error.message || '登录失败，请重试'
        };
    }
}

/**
 * 用户登出
 */
function logout() {
    try {
        // 记录登出日志
        if (authState.currentUser) {
            logAuthEvent('logout', authState.currentUser.username, 'success');
        }
        
        // 清除认证状态
        authState.currentUser = null;
        authState.isAuthenticated = false;
        authState.sessionExpiresAt = null;
        
        // 清除本地存储中的会话信息
        localStorage.removeItem('auth_session');
        
        // 重定向到登录页面
        window.location.href = '/login.html';
        
        return true;
        
    } catch (error) {
        console.error('登出失败:', error);
        return false;
    }
}

/**
 * 检查用户是否已认证
 */
function isAuthenticated() {
    return authState.isAuthenticated && !!authState.currentUser;
}

/**
 * 获取当前登录用户
 */
function getCurrentUser() {
    return authState.currentUser;
}

/**
 * 检查用户是否具有特定角色
 */
function hasRole(role) {
    if (!isAuthenticated()) return false;
    
    // 超级管理员拥有所有角色的权限
    if (authState.currentUser.role === authState.superAdminRole) {
        return true;
    }
    
    return authState.currentUser.role === role;
}

/**
 * 检查用户是否拥有特定权限
 */
function hasPermission(permission) {
    if (!isAuthenticated()) return false;
    
    // 检查用户是否拥有该权限
    return authState.currentUser.permissions.includes(permission);
}

/**
 * 检查用户是否拥有足够的权限级别
 */
function hasPermissionLevel(level) {
    if (!isAuthenticated()) return false;
    
    const userLevel = authState.permissionLevels[authState.currentUser.role];
    const requiredLevel = authState.permissionLevels[level];
    
    return userLevel >= requiredLevel;
}

/**
 * 检查用户是否是管理员或Vikey管理员
 */
function isAdminOrVikeyAdmin() {
    return isAuthenticated() && 
           (authState.currentUser.role === 'administrator' || 
            authState.currentUser.role === 'vikey_admin');
}

/**
 * 检查用户是否是Vikey管理员
 */
function isVikeyAdmin() {
    return isAuthenticated() && authState.currentUser.role === 'vikey_admin';
}

/**
 * 记录认证事件日志
 */
function logAuthEvent(eventType, username, status, details = '') {
    const logEntry = {
        timestamp: new Date().toISOString(),
        type: eventType,
        username: username,
        status: status,
        ip: window.location.hostname, // 实际应用中应该获取真实IP
        userAgent: navigator.userAgent,
        details: details
    };
    
    console.log('认证事件:', logEntry);
    
    // 实际应用中应该发送到服务器保存
    // sendLogToServer(logEntry);
}

/**
 * 开始密码修改的多管理员授权流程
 */
async function startPasswordChangeApproval(targetUserId) {
    try {
        // 检查权限
        if (!isAdminOrVikeyAdmin()) {
            throw new Error('您没有权限发起密码修改请求');
        }
        
        // 检查目标用户是否存在
        const targetUser = mockUserDatabase.find(u => u.username === targetUserId);
        if (!targetUser) {
            throw new Error('目标用户不存在');
        }
        
        // 生成审批ID
        const approvalId = `APPROVAL-${Date.now()}`;
        
        // 创建审批请求
        const approvalRequest = {
            id: approvalId,
            type: 'password_change',
            targetUser: targetUserId,
            requestedBy: authState.currentUser.username,
            requestedAt: new Date().toISOString(),
            approvals: [],
            status: 'pending',
            expiresAt: new Date(Date.now() + 24 * 60 * 60 * 1000).toISOString() // 24小时内有效
        };
        
        // 保存到活跃审批列表
        authState.activeApprovals[approvalId] = approvalRequest;
        
        // 记录操作日志
        logAuthEvent('password_change_request', authState.currentUser.username, 'success', 
                    `请求修改用户 ${targetUserId} 的密码`);
        
        // 通知所有密码管理员和Vikey管理员
        notifyAdminsAboutApproval(approvalRequest);
        
        return {
            success: true,
            approvalId: approvalId,
            message: '密码修改请求已创建，请等待其他管理员批准'
        };
        
    } catch (error) {
        logAuthEvent('password_change_request', authState.currentUser.username, 'failure', error.message);
        
        return {
            success: false,
            message: error.message || '发起密码修改请求失败'
        };
    }
}

/**
 * 批准密码修改请求
 */
async function approvePasswordChange(approvalId) {
    try {
        // 检查认证
        if (!isAuthenticated()) {
            throw new Error('请先登录');
        }
        
        // 检查用户是否有批准权限
        if (!hasPermission('approve_changes') && !isVikeyAdmin()) {
            throw new Error('您没有权限批准密码修改');
        }
        
        // 检查审批请求是否存在
        const approval = authState.activeApprovals[approvalId];
        if (!approval) {
            throw new Error('审批请求不存在或已过期');
        }
        
        // 检查是否已批准
        const alreadyApproved = approval.approvals.some(a => a.username === authState.currentUser.username);
        if (alreadyApproved) {
            throw new Error('您已经批准过此请求');
        }
        
        // 检查请求是否已过期
        if (new Date(approval.expiresAt) < new Date()) {
            throw new Error('审批请求已过期');
        }
        
        // 添加批准记录
        approval.approvals.push({
            username: authState.currentUser.username,
            approvedAt: new Date().toISOString()
        });
        
        // 检查是否达到所需批准数量或超级管理员已批准
        const hasSuperAdminApproval = approval.approvals.some(a => {
            const approver = mockUserDatabase.find(u => u.username === a.username);
            return approver && approver.role === authState.superAdminRole;
        });
        
        const hasEnoughApprovals = approval.approvals.length >= authState.requiredAdminCount;
        
        if (hasSuperAdminApproval || hasEnoughApprovals) {
            // 满足条件，执行密码修改流程
            approval.status = 'approved';
            approval.completedAt = new Date().toISOString();
            
            // 执行密码修改（实际应用中应该有更复杂的密码重置逻辑）
            await executePasswordChange(approval.targetUser);
            
            // 保存到历史记录
            mockApprovalHistory.push({ ...approval });
            
            // 通知所有相关人员
            notifyPasswordChangeCompleted(approval);
            
            return {
                success: true,
                message: '密码修改已获批准并执行'
            };
        } else {
            // 还需更多批准
            const needed = authState.requiredAdminCount - approval.approvals.length;
            
            return {
                success: true,
                message: `批准成功，还需要 ${needed} 位管理员批准`
            };
        }
        
    } catch (error) {
        logAuthEvent('password_change_approval', authState.currentUser.username, 'failure', error.message);
        
        return {
            success: false,
            message: error.message || '批准密码修改失败'
        };
    }
}

/**
 * 拒绝密码修改请求
 */
async function rejectPasswordChange(approvalId, reason = '') {
    try {
        // 检查认证
        if (!isAuthenticated()) {
            throw new Error('请先登录');
        }
        
        // 检查用户是否有拒绝权限
        if (!hasPermission('approve_changes') && !isVikeyAdmin()) {
            throw new Error('您没有权限拒绝密码修改');
        }
        
        // 检查审批请求是否存在
        const approval = authState.activeApprovals[approvalId];
        if (!approval) {
            throw new Error('审批请求不存在或已过期');
        }
        
        // 更新审批状态
        approval.status = 'rejected';
        approval.rejectedBy = authState.currentUser.username;
        approval.rejectionReason = reason;
        approval.completedAt = new Date().toISOString();
        
        // 保存到历史记录
        mockApprovalHistory.push({ ...approval });
        
        // 通知相关人员
        notifyPasswordChangeRejected(approval);
        
        // 记录操作日志
        logAuthEvent('password_change_rejection', authState.currentUser.username, 'success', 
                    `拒绝了用户 ${approval.targetUser} 的密码修改请求`);
        
        return {
            success: true,
            message: '密码修改请求已拒绝'
        };
        
    } catch (error) {
        logAuthEvent('password_change_rejection', authState.currentUser.username, 'failure', error.message);
        
        return {
            success: false,
            message: error.message || '拒绝密码修改失败'
        };
    }
}

/**
 * 执行密码修改
 */
async function executePasswordChange(username) {
    // 模拟密码修改过程
    await new Promise(resolve => setTimeout(resolve, 1000));
    
    // 实际应用中应该：
    // 1. 生成临时密码
    // 2. 通过安全渠道通知用户
    // 3. 记录密码修改历史
    // 4. 强制用户下次登录时修改密码
    
    console.log(`执行用户 ${username} 的密码修改流程`);
    
    // 模拟发送新密码到用户邮箱
    notifyUserOfPasswordChange(username);
}

/**
 * 获取活跃的审批请求列表
 */
function getActiveApprovals() {
    // 过滤出未完成且未过期的审批
    const now = new Date();
    return Object.values(authState.activeApprovals).filter(approval => {
        return approval.status === 'pending' && new Date(approval.expiresAt) > now;
    });
}

/**
 * 获取审批历史
 */
function getApprovalHistory() {
    return [...mockApprovalHistory];
}

/**
 * 通知管理员关于审批请求
 */
function notifyAdminsAboutApproval(approval) {
    // 获取所有密码管理员和Vikey管理员
    const admins = mockUserDatabase.filter(u => 
        u.isActive && 
        (u.role === 'password_admin' || u.role === 'vikey_admin') &&
        u.username !== approval.requestedBy // 排除请求发起人
    );
    
    // 模拟发送通知
    console.log(`通知 ${admins.length} 位管理员关于新的审批请求`);
    
    // 实际应用中应该实现真实的通知机制（如邮件、消息推送等）
    admins.forEach(admin => {
        console.log(`通知管理员 ${admin.username} 关于 ${approval.type} 审批请求 ${approval.id}`);
    });
    
    // 如果有通知系统，可以在这里添加通知
    if (window.addNotification) {
        window.addNotification(`新的密码修改请求需要您的批准`, 'info');
    }
}

/**
 * 通知密码修改完成
 */
function notifyPasswordChangeCompleted(approval) {
    console.log(`密码修改请求 ${approval.id} 已完成，通知相关人员`);
    
    // 通知请求发起人和所有批准人
    const notifyUsers = new Set([approval.requestedBy, ...approval.approvals.map(a => a.username)]);
    
    notifyUsers.forEach(username => {
        console.log(`通知用户 ${username} 密码修改已完成`);
    });
    
    // 实际应用中应该实现真实的通知机制
    if (window.addNotification) {
        window.addNotification(`用户 ${approval.targetUser} 的密码已成功修改`, 'success');
    }
}

/**
 * 通知密码修改被拒绝
 */
function notifyPasswordChangeRejected(approval) {
    console.log(`密码修改请求 ${approval.id} 已被拒绝，通知相关人员`);
    
    // 通知请求发起人和所有已批准的用户
    const notifyUsers = new Set([approval.requestedBy, ...approval.approvals.map(a => a.username)]);
    
    notifyUsers.forEach(username => {
        console.log(`通知用户 ${username} 密码修改请求已被拒绝: ${approval.rejectionReason || '无理由'}`);
    });
    
    // 实际应用中应该实现真实的通知机制
    if (window.addNotification) {
        window.addNotification(`用户 ${approval.targetUser} 的密码修改请求已被拒绝`, 'warning');
    }
}

/**
 * 通知用户密码已修改
 */
function notifyUserOfPasswordChange(username) {
    // 实际应用中应该：
    // 1. 通过安全渠道（如邮件）发送新密码
    // 2. 要求用户首次登录时修改密码
    // 3. 提供密码修改的临时链接
    
    console.log(`通知用户 ${username} 密码已修改，请查收新密码`);
}

/**
 * 权限保护的页面访问控制
 */
function protectPage(minimumRole) {
    // 检查用户是否已认证
    if (!isAuthenticated()) {
        // 保存当前页面，以便登录后重定向
        localStorage.setItem('redirect_after_login', window.location.pathname);
        window.location.href = '/login.html';
        return false;
    }
    
    // 检查用户权限级别
    if (!hasPermissionLevel(minimumRole)) {
        window.location.href = '/access-denied.html';
        return false;
    }
    
    return true;
}

/**
 * 更新UI以反映当前用户权限
 */
function updateUIByPermissions() {
    if (!isAuthenticated()) return;
    
    // 更新用户信息显示（如果存在）
    const userInfoElement = document.getElementById('user-info');
    if (userInfoElement) {
        userInfoElement.textContent = `${authState.currentUser.fullName} (${authState.currentUser.role})`;
    }
    
    // 根据权限隐藏/显示UI元素
    const role = authState.currentUser.role;
    
    // 示例：根据不同角色显示/隐藏导航项
    const adminOnlyElements = document.querySelectorAll('.admin-only');
    adminOnlyElements.forEach(el => {
        el.style.display = isAdminOrVikeyAdmin() ? 'block' : 'none';
    });
    
    const vikeyAdminOnlyElements = document.querySelectorAll('.vikey-admin-only');
    vikeyAdminOnlyElements.forEach(el => {
        el.style.display = isVikeyAdmin() ? 'block' : 'none';
    });
    
    // 根据具体权限隐藏/显示操作按钮
    const permissionElements = document.querySelectorAll('[data-required-permission]');
    permissionElements.forEach(el => {
        const requiredPermission = el.getAttribute('data-required-permission');
        el.style.display = hasPermission(requiredPermission) ? 'block' : 'none';
    });
}

/**
 * 生成登录表单
 */
function generateLoginForm() {
    const loginFormHTML = `
        <div class="login-container">
            <div class="login-header">
                <h2>MTSCOS 管理员登录</h2>
                <p>请输入您的用户名和密码以登录系统</p>
            </div>
            
            <div class="login-form">
                <div class="form-group">
                    <label for="username">用户名</label>
                    <input type="text" id="username" placeholder="请输入用户名" required>
                </div>
                
                <div class="form-group">
                    <label for="password">密码</label>
                    <input type="password" id="password" placeholder="请输入密码" required>
                </div>
                
                <div class="form-actions">
                    <button id="login-button" class="btn primary">登录</button>
                </div>
                
                <div id="login-message" class="login-message"></div>
            </div>
        </div>
    `;
    
    return loginFormHTML;
}

/**
 * 初始化登录表单事件
 */
function initializeLoginForm() {
    const loginButton = document.getElementById('login-button');
    const usernameInput = document.getElementById('username');
    const passwordInput = document.getElementById('password');
    const messageElement = document.getElementById('login-message');
    
    if (loginButton) {
        loginButton.addEventListener('click', async () => {
            try {
                const username = usernameInput.value.trim();
                const password = passwordInput.value.trim();
                
                if (!username || !password) {
                    setLoginMessage('请输入用户名和密码', 'error');
                    return;
                }
                
                // 禁用登录按钮防止重复提交
                loginButton.disabled = true;
                setLoginMessage('正在登录...', 'info');
                
                // 执行登录
                const result = await login(username, password);
                
                if (result.success) {
                    setLoginMessage(result.message, 'success');
                    
                    // 检查是否有重定向URL
                    const redirectUrl = localStorage.getItem('redirect_after_login') || '/';
                    localStorage.removeItem('redirect_after_login');
                    
                    // 延迟跳转，让用户看到成功消息
                    setTimeout(() => {
                        window.location.href = redirectUrl;
                    }, 1500);
                    
                } else {
                    setLoginMessage(result.message, 'error');
                    loginButton.disabled = false;
                }
                
            } catch (error) {
                console.error('登录过程中发生错误:', error);
                setLoginMessage('登录失败，请重试', 'error');
                loginButton.disabled = false;
            }
        });
    }
    
    function setLoginMessage(message, type = 'info') {
        if (messageElement) {
            messageElement.textContent = message;
            messageElement.className = `login-message ${type}`;
        }
    }
    
    // 添加回车键登录功能
    [usernameInput, passwordInput].forEach(input => {
        if (input) {
            input.addEventListener('keypress', (e) => {
                if (e.key === 'Enter') {
                    loginButton.click();
                }
            });
        }
    });
}

// 暴露API
window.auth = {
    initialize: initializeAuth,
    login: login,
    logout: logout,
    isAuthenticated: isAuthenticated,
    getCurrentUser: getCurrentUser,
    hasRole: hasRole,
    hasPermission: hasPermission,
    hasPermissionLevel: hasPermissionLevel,
    isAdminOrVikeyAdmin: isAdminOrVikeyAdmin,
    isVikeyAdmin: isVikeyAdmin,
    startPasswordChangeApproval: startPasswordChangeApproval,
    approvePasswordChange: approvePasswordChange,
    rejectPasswordChange: rejectPasswordChange,
    getActiveApprovals: getActiveApprovals,
    getApprovalHistory: getApprovalHistory,
    protectPage: protectPage,
    updateUIByPermissions: updateUIByPermissions,
    generateLoginForm: generateLoginForm,
    initializeLoginForm: initializeLoginForm
};