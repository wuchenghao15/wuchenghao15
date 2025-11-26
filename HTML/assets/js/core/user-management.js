/**
 * 用户智能管理系统
 * 实现用户信息管理、权限分级、智能账户管理等功能
 */

class UserManagementSystem {
    constructor() {
        this.currentUser = null;
        this.userDatabase = null;
        this.permissionLevels = {
            GUEST: 0,           // 访客
            USER: 1,            // 普通用户
            ADMIN: 2,           // 管理员
            SUPER_ADMIN: 3,      // 超级管理员
            VIKEY_ADMIN: 4       // Vikey管理员
        };
        
        this.sessionTimeout = 30 * 60 * 1000; // 30分钟会话超时
        this.maxLoginAttempts = 5;
        this.lockoutDuration = 15 * 60 * 1000; // 15分钟锁定
        
        this.init();
    }

    /**
     * 初始化用户管理系统
     */
    async init() {
        try {
            // 初始化用户数据库
            await this.initializeUserDatabase();
            
            // 检查当前会话
            await this.checkCurrentSession();
            
            // 设置会话监控
            this.setupSessionMonitoring();
            
            console.log('用户管理系统初始化完成');
        } catch (error) {
            console.error('用户管理系统初始化失败:', error);
            throw error;
        }
    }

    /**
     * 初始化用户数据库
     */
    async initializeUserDatabase() {
        this.userDatabase = new UserDatabase();
        await this.userDatabase.init();
        
        // 确保默认管理员存在
        await this.ensureDefaultAdmin();
    }

    /**
     * 确保默认管理员存在
     */
    async ensureDefaultAdmin() {
        try {
            const adminExists = await this.userDatabase.userExists('wuchenghao15');
            
            if (!adminExists) {
                // 创建默认管理员账户
                const adminUser = {
                    username: 'wuchenghao15',
                    email: 'admin@mtscos.com',
                    permissionLevel: this.permissionLevels.SUPER_ADMIN,
                    isActive: true,
                    isVikeyUser: false,
                    createdAt: new Date().toISOString(),
                    lastLogin: null,
                    loginAttempts: 0,
                    isLocked: false,
                    lockUntil: null,
                    passwordChanged: false,
                    profile: {
                        displayName: '系统管理员',
                        department: '系统管理',
                        phone: '',
                        avatar: ''
                    }
                };
                
                await this.userDatabase.createUser(adminUser);
                console.log('默认管理员账户已创建');
            }
        } catch (error) {
            console.error('创建默认管理员失败:', error);
        }
    }

    /**
     * 检查当前会话
     */
    async checkCurrentSession() {
        const sessionId = localStorage.getItem('userSessionId');
        if (!sessionId) return null;
        
        try {
            const session = await this.userDatabase.getSession(sessionId);
            if (!session || session.expiresAt < new Date()) {
                localStorage.removeItem('userSessionId');
                return null;
            }
            
            const user = await this.userDatabase.getUserById(session.userId);
            if (!user || !user.isActive) {
                localStorage.removeItem('userSessionId');
                return null;
            }
            
            this.currentUser = user;
            await this.updateSessionActivity(sessionId);
            return user;
        } catch (error) {
            console.error('检查会话失败:', error);
            localStorage.removeItem('userSessionId');
            return null;
        }
    }

    /**
     * 更新会话活动时间
     */
    async updateSessionActivity(sessionId) {
        try {
            const newExpiresAt = new Date(Date.now() + this.sessionTimeout);
            await this.userDatabase.updateSession(sessionId, {
                lastActivity: new Date().toISOString(),
                expiresAt: newExpiresAt.toISOString()
            });
        } catch (error) {
            console.error('更新会话活动失败:', error);
        }
    }

    /**
     * 设置会话监控
     */
    setupSessionMonitoring() {
        // 每分钟检查会话状态
        setInterval(async () => {
            if (this.currentUser) {
                const sessionId = localStorage.getItem('userSessionId');
                if (sessionId) {
                    const session = await this.userDatabase.getSession(sessionId);
                    if (!session || session.expiresAt < new Date()) {
                        this.logout();
                        this.showSessionExpiredMessage();
                    }
                }
            }
        }, 60000);

        // 监听页面活动
        ['mousedown', 'keydown', 'scroll', 'touchstart'].forEach(event => {
            document.addEventListener(event, () => {
                if (this.currentUser) {
                    const sessionId = localStorage.getItem('userSessionId');
                    if (sessionId) {
                        this.updateSessionActivity(sessionId);
                    }
                }
            }, true);
        });
    }

    /**
     * 用户登录
     */
    async login(username, password, vikeyInfo = null) {
        try {
            // 检查用户是否被锁定
            const user = await this.userDatabase.getUser(username);
            if (!user) {
                throw new Error('用户名或密码错误');
            }

            if (user.isLocked && user.lockUntil && user.lockUntil > new Date()) {
                const remainingTime = Math.ceil((user.lockUntil - new Date()) / 60000);
                throw new Error(`账户已被锁定，请${remainingTime}分钟后重试`);
            }

            // 验证密码
            const isPasswordValid = await this.verifyPassword(password, user.password);
            if (!isPasswordValid) {
                await this.handleFailedLogin(user);
                throw new Error('用户名或密码错误');
            }

            // 检查Vikey验证（如果需要）
            if (user.isVikeyUser && !vikeyInfo) {
                throw new Error('Vikey用户需要插入Vikey设备');
            }

            if (user.isVikeyUser && vikeyInfo) {
                const isVikeyValid = await this.verifyVikey(user, vikeyInfo);
                if (!isVikeyValid) {
                    throw new Error('Vikey验证失败');
                }
            }

            // 检查密码是否需要更改
            if (!user.passwordChanged && user.permissionLevel > this.permissionLevels.USER) {
                return {
                    requirePasswordChange: true,
                    user: user
                };
            }

            // 登录成功
            await this.handleSuccessfulLogin(user);
            
            return {
                success: true,
                user: user,
                sessionId: localStorage.getItem('userSessionId')
            };

        } catch (error) {
            console.error('登录失败:', error);
            throw error;
        }
    }

    /**
     * Vikey登录
     */
    async vikeyLogin(vikeyInfo) {
        try {
            // 通过Vikey ID查找用户
            const user = await this.userDatabase.getUserByVikeyId(vikeyInfo.vikeyId);
            if (!user) {
                throw new Error('未找到关联的Vikey用户');
            }

            if (!user.isActive) {
                throw new Error('用户账户已被禁用');
            }

            // 验证Vikey信息
            const isVikeyValid = await this.verifyVikey(user, vikeyInfo);
            if (!isVikeyValid) {
                throw new Error('Vikey验证失败');
            }

            // Vikey登录成功
            await this.handleSuccessfulLogin(user);
            
            return {
                success: true,
                user: user,
                sessionId: localStorage.getItem('userSessionId')
            };

        } catch (error) {
            console.error('Vikey登录失败:', error);
            throw error;
        }
    }

    /**
     * 处理成功登录
     */
    async handleSuccessfulLogin(user) {
        try {
            // 重置登录失败次数
            await this.userDatabase.updateUser(user.id, {
                loginAttempts: 0,
                isLocked: false,
                lockUntil: null,
                lastLogin: new Date().toISOString()
            });

            // 创建会话
            const sessionId = await this.createUserSession(user.id);
            localStorage.setItem('userSessionId', sessionId);

            this.currentUser = user;

            // 记录登录日志
            await this.logUserActivity('LOGIN', {
                userId: user.id,
                username: user.username,
                loginTime: new Date().toISOString(),
                ipAddress: this.getClientIP(),
                userAgent: navigator.userAgent
            });

        } catch (error) {
            console.error('处理登录成功失败:', error);
            throw error;
        }
    }

    /**
     * 处理登录失败
     */
    async handleFailedLogin(user) {
        try {
            const newAttempts = (user.loginAttempts || 0) + 1;
            const updateData = {
                loginAttempts: newAttempts
            };

            // 检查是否需要锁定账户
            if (newAttempts >= this.maxLoginAttempts) {
                updateData.isLocked = true;
                updateData.lockUntil = new Date(Date.now() + this.lockoutDuration).toISOString();
            }

            await this.userDatabase.updateUser(user.id, updateData);

            // 记录登录失败日志
            await this.logUserActivity('LOGIN_FAILED', {
                userId: user.id,
                username: user.username,
                attempts: newAttempts,
                isLocked: updateData.isLocked,
                timestamp: new Date().toISOString(),
                ipAddress: this.getClientIP()
            });

        } catch (error) {
            console.error('处理登录失败失败:', error);
        }
    }

    /**
     * 创建用户会话
     */
    async createUserSession(userId) {
        const sessionId = this.generateSessionId();
        const session = {
            id: sessionId,
            userId: userId,
            createdAt: new Date().toISOString(),
            lastActivity: new Date().toISOString(),
            expiresAt: new Date(Date.now() + this.sessionTimeout).toISOString(),
            ipAddress: this.getClientIP(),
            userAgent: navigator.userAgent
        };

        await this.userDatabase.createSession(session);
        return sessionId;
    }

    /**
     * 用户登出
     */
    async logout() {
        try {
            const sessionId = localStorage.getItem('userSessionId');
            if (sessionId) {
                await this.userDatabase.deleteSession(sessionId);
                localStorage.removeItem('userSessionId');
            }

            if (this.currentUser) {
                // 记录登出日志
                await this.logUserActivity('LOGOUT', {
                    userId: this.currentUser.id,
                    username: this.currentUser.username,
                    logoutTime: new Date().toISOString()
                });
            }

            this.currentUser = null;

        } catch (error) {
            console.error('登出失败:', error);
        }
    }

    /**
     * 获取当前用户
     */
    getCurrentUser() {
        return this.currentUser;
    }

    /**
     * 检查用户权限
     */
    hasPermission(requiredLevel) {
        if (!this.currentUser) return false;
        return this.currentUser.permissionLevel >= requiredLevel;
    }

    /**
     * 检查是否为管理员
     */
    isAdmin() {
        return this.hasPermission(this.permissionLevels.ADMIN);
    }

    /**
     * 检查是否为超级管理员
     */
    isSuperAdmin() {
        return this.hasPermission(this.permissionLevels.SUPER_ADMIN);
    }

    /**
     * 检查是否为Vikey管理员
     */
    isVikeyAdmin() {
        return this.hasPermission(this.permissionLevels.VIKEY_ADMIN);
    }

    /**
     * 创建用户
     */
    async createUser(userData, createdBy) {
        try {
            // 检查权限
            if (!this.hasPermission(this.permissionLevels.ADMIN)) {
                throw new Error('权限不足');
            }

            // 检查是否可以创建该权限级别的用户
            if (userData.permissionLevel >= this.permissionLevels.SUPER_ADMIN && !this.isSuperAdmin()) {
                throw new Error('只有超级管理员可以创建超级管理员用户');
            }

            // 验证用户数据
            await this.validateUserData(userData);

            // 检查用户名是否已存在
            const existingUser = await this.userDatabase.getUser(userData.username);
            if (existingUser) {
                throw new Error('用户名已存在');
            }

            // 创建用户对象
            const newUser = {
                username: userData.username,
                email: userData.email,
                password: await this.hashPassword(userData.password),
                permissionLevel: userData.permissionLevel,
                isActive: true,
                isVikeyUser: userData.isVikeyUser || false,
                vikeyId: userData.vikeyId || null,
                createdAt: new Date().toISOString(),
                createdBy: createdBy.id,
                lastLogin: null,
                loginAttempts: 0,
                isLocked: false,
                lockUntil: null,
                passwordChanged: false,
                profile: userData.profile || {}
            };

            const userId = await this.userDatabase.createUser(newUser);

            // 记录创建用户日志
            await this.logUserActivity('USER_CREATED', {
                newUserId: userId,
                newUsername: userData.username,
                createdBy: createdBy.id,
                createdByName: createdBy.username,
                timestamp: new Date().toISOString()
            });

            return { success: true, userId: userId };

        } catch (error) {
            console.error('创建用户失败:', error);
            throw error;
        }
    }

    /**
     * 更新用户信息
     */
    async updateUser(userId, updateData, updatedBy) {
        try {
            // 检查权限
            const targetUser = await this.userDatabase.getUserById(userId);
            if (!targetUser) {
                throw new Error('用户不存在');
            }

            // 用户只能更新自己的基本信息，管理员可以更新更多信息
            if (this.currentUser.id !== userId && !this.isAdmin()) {
                throw new Error('权限不足');
            }

            // 非管理员不能修改权限级别
            if (updateData.permissionLevel && !this.isSuperAdmin()) {
                throw new Error('只有超级管理员可以修改权限级别');
            }

            // 验证更新数据
            await this.validateUpdateData(updateData, targetUser);

            // 如果更新密码，需要重新哈希
            if (updateData.password) {
                updateData.password = await this.hashPassword(updateData.password);
                updateData.passwordChanged = true;
            }

            updateData.updatedAt = new Date().toISOString();
            updateData.updatedBy = updatedBy.id;

            await this.userDatabase.updateUser(userId, updateData);

            // 记录更新日志
            await this.logUserActivity('USER_UPDATED', {
                userId: userId,
                username: targetUser.username,
                updatedBy: updatedBy.id,
                updatedByName: updatedBy.username,
                updateFields: Object.keys(updateData),
                timestamp: new Date().toISOString()
            });

            return { success: true };

        } catch (error) {
            console.error('更新用户失败:', error);
            throw error;
        }
    }

    /**
     * 删除用户
     */
    async deleteUser(userId, deletedBy) {
        try {
            // 检查权限
            if (!this.isSuperAdmin()) {
                throw new Error('只有超级管理员可以删除用户');
            }

            const targetUser = await this.userDatabase.getUserById(userId);
            if (!targetUser) {
                throw new Error('用户不存在');
            }

            // 不能删除自己
            if (userId === this.currentUser.id) {
                throw new Error('不能删除当前登录用户');
            }

            // 需要多人批准机制（简化版本，实际需要更复杂的审批流程）
            const approvalRequired = targetUser.permissionLevel >= this.permissionLevels.ADMIN;
            if (approvalRequired) {
                // 这里应该触发审批流程
                throw new Error('删除管理员用户需要审批流程');
            }

            await this.userDatabase.deleteUser(userId);

            // 记录删除日志
            await this.logUserActivity('USER_DELETED', {
                deletedUserId: userId,
                deletedUsername: targetUser.username,
                deletedBy: deletedBy.id,
                deletedByName: deletedBy.username,
                timestamp: new Date().toISOString()
            });

            return { success: true };

        } catch (error) {
            console.error('删除用户失败:', error);
            throw error;
        }
    }

    /**
     * 获取用户列表
     */
    async getUsers(filters = {}, pagination = {}) {
        try {
            // 检查权限
            if (!this.isAdmin()) {
                throw new Error('权限不足');
            }

            return await this.userDatabase.getUsers(filters, pagination);

        } catch (error) {
            console.error('获取用户列表失败:', error);
            throw error;
        }
    }

    /**
     * 验证用户数据
     */
    async validateUserData(userData) {
        if (!userData.username || userData.username.length < 3) {
            throw new Error('用户名至少需要3个字符');
        }

        if (!userData.email || !this.isValidEmail(userData.email)) {
            throw new Error('请输入有效的邮箱地址');
        }

        if (!userData.password || userData.password.length < 6) {
            throw new Error('密码至少需要6个字符');
        }

        if (userData.permissionLevel === undefined) {
            throw new Error('必须指定用户权限级别');
        }

        if (userData.permissionLevel < 0 || userData.permissionLevel > 4) {
            throw new Error('无效的权限级别');
        }
    }

    /**
     * 验证更新数据
     */
    async validateUpdateData(updateData, targetUser) {
        if (updateData.username && updateData.username !== targetUser.username) {
            if (updateData.username.length < 3) {
                throw new Error('用户名至少需要3个字符');
            }
        }

        if (updateData.email && !this.isValidEmail(updateData.email)) {
            throw new Error('请输入有效的邮箱地址');
        }

        if (updateData.password && updateData.password.length < 6) {
            throw new Error('密码至少需要6个字符');
        }
    }

    /**
     * 验证密码
     */
    async verifyPassword(password, hashedPassword) {
        // 简化版本，实际应该使用bcrypt等安全哈希算法
        return await this.hashPassword(password) === hashedPassword;
    }

    /**
     * 哈希密码
     */
    async hashPassword(password) {
        // 简化版本，实际应该使用bcrypt等安全哈希算法
        return btoa(password + 'salt'); // 仅用于演示
    }

    /**
     * 验证Vikey
     */
    async verifyVikey(user, vikeyInfo) {
        if (!user.isVikeyUser || !user.vikeyId) {
            return false;
        }

        // 检查Vikey ID是否匹配
        if (user.vikeyId !== vikeyInfo.vikeyId) {
            return false;
        }

        // 检查Vikey是否有效
        if (vikeyInfo.state !== 2) { // 2 = AUTHENTICATED
            return false;
        }

        // 检查Vikey权限级别是否匹配
        if (vikeyInfo.permissionLevel !== user.permissionLevel) {
            return false;
        }

        // 检查Vikey是否过期
        if (vikeyInfo.validTo && new Date(vikeyInfo.validTo) < new Date()) {
            return false;
        }

        return true;
    }

    /**
     * 生成会话ID
     */
    generateSessionId() {
        return 'session_' + Date.now() + '_' + Math.random().toString(36).substr(2, 9);
    }

    /**
     * 获取客户端IP
     */
    getClientIP() {
        // 简化版本，实际应该从服务器获取
        return '127.0.0.1';
    }

    /**
     * 验证邮箱格式
     */
    isValidEmail(email) {
        const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
        return emailRegex.test(email);
    }

    /**
     * 记录用户活动日志
     */
    async logUserActivity(activity, details) {
        try {
            const logEntry = {
                activity: activity,
                details: details,
                timestamp: new Date().toISOString(),
                sessionId: localStorage.getItem('userSessionId')
            };

            await this.userDatabase.logActivity(logEntry);
        } catch (error) {
            console.error('记录用户活动日志失败:', error);
        }
    }

    /**
     * 显示会话过期消息
     */
    showSessionExpiredMessage() {
        if (typeof window.showAlert === 'function') {
            window.showAlert('会话已过期，请重新登录', 'warning');
        } else {
            alert('会话已过期，请重新登录');
        }
    }

    /**
     * 获取用户统计信息
     */
    async getUserStatistics() {
        try {
            if (!this.isAdmin()) {
                throw new Error('权限不足');
            }

            return await this.userDatabase.getUserStatistics();
        } catch (error) {
            console.error('获取用户统计失败:', error);
            throw error;
        }
    }
}

/**
 * 用户数据库操作类
 */
class UserDatabase {
    constructor() {
        this.dbName = 'UserManagementDB';
        this.dbVersion = 1;
        this.db = null;
    }

    async init() {
        return new Promise((resolve, reject) => {
            const request = indexedDB.open(this.dbName, this.dbVersion);

            request.onerror = () => reject(request.error);
            request.onsuccess = () => {
                this.db = request.result;
                resolve();
            };

            request.onupgradeneeded = (event) => {
                const db = event.target.result;

                // 用户表
                if (!db.objectStoreNames.contains('users')) {
                    const userStore = db.createObjectStore('users', { keyPath: 'id', autoIncrement: true });
                    userStore.createIndex('username', 'username', { unique: true });
                    userStore.createIndex('email', 'email', { unique: true });
                    userStore.createIndex('vikeyId', 'vikeyId', { unique: true, sparse: true });
                    userStore.createIndex('permissionLevel', 'permissionLevel');
                    userStore.createIndex('isActive', 'isActive');
                }

                // 会话表
                if (!db.objectStoreNames.contains('sessions')) {
                    const sessionStore = db.createObjectStore('sessions', { keyPath: 'id' });
                    sessionStore.createIndex('userId', 'userId');
                    sessionStore.createIndex('expiresAt', 'expiresAt');
                }

                // 活动日志表
                if (!db.objectStoreNames.contains('activity_logs')) {
                    const logStore = db.createObjectStore('activity_logs', { keyPath: 'id', autoIncrement: true });
                    logStore.createIndex('activity', 'activity');
                    logStore.createIndex('timestamp', 'timestamp');
                    logStore.createIndex('userId', 'userId');
                }
            };
        });
    }

    async createUser(userData) {
        return new Promise((resolve, reject) => {
            const transaction = this.db.transaction(['users'], 'readwrite');
            const store = transaction.objectStore('users');
            const request = store.add(userData);

            request.onsuccess = () => resolve(request.result);
            request.onerror = () => reject(request.error);
        });
    }

    async getUser(username) {
        return new Promise((resolve, reject) => {
            const transaction = this.db.transaction(['users'], 'readonly');
            const store = transaction.objectStore('users');
            const index = store.index('username');
            const request = index.get(username);

            request.onsuccess = () => resolve(request.result);
            request.onerror = () => reject(request.error);
        });
    }

    async getUserByVikeyId(vikeyId) {
        return new Promise((resolve, reject) => {
            const transaction = this.db.transaction(['users'], 'readonly');
            const store = transaction.objectStore('users');
            const index = store.index('vikeyId');
            const request = index.get(vikeyId);

            request.onsuccess = () => resolve(request.result);
            request.onerror = () => reject(request.error);
        });
    }

    async getUserById(userId) {
        return new Promise((resolve, reject) => {
            const transaction = this.db.transaction(['users'], 'readonly');
            const store = transaction.objectStore('users');
            const request = store.get(userId);

            request.onsuccess = () => resolve(request.result);
            request.onerror = () => reject(request.error);
        });
    }

    async updateUser(userId, updateData) {
        return new Promise((resolve, reject) => {
            const transaction = this.db.transaction(['users'], 'readwrite');
            const store = transaction.objectStore('users');
            
            const getRequest = store.get(userId);
            getRequest.onsuccess = () => {
                const user = getRequest.result;
                if (!user) {
                    reject(new Error('用户不存在'));
                    return;
                }

                Object.assign(user, updateData);
                const updateRequest = store.put(user);
                
                updateRequest.onsuccess = () => resolve(updateRequest.result);
                updateRequest.onerror = () => reject(updateRequest.error);
            };
            getRequest.onerror = () => reject(getRequest.error);
        });
    }

    async deleteUser(userId) {
        return new Promise((resolve, reject) => {
            const transaction = this.db.transaction(['users'], 'readwrite');
            const store = transaction.objectStore('users');
            const request = store.delete(userId);

            request.onsuccess = () => resolve(request.result);
            request.onerror = () => reject(request.error);
        });
    }

    async userExists(username) {
        const user = await this.getUser(username);
        return !!user;
    }

    async createSession(sessionData) {
        return new Promise((resolve, reject) => {
            const transaction = this.db.transaction(['sessions'], 'readwrite');
            const store = transaction.objectStore('sessions');
            const request = store.add(sessionData);

            request.onsuccess = () => resolve(request.result);
            request.onerror = () => reject(request.error);
        });
    }

    async getSession(sessionId) {
        return new Promise((resolve, reject) => {
            const transaction = this.db.transaction(['sessions'], 'readonly');
            const store = transaction.objectStore('sessions');
            const request = store.get(sessionId);

            request.onsuccess = () => resolve(request.result);
            request.onerror = () => reject(request.error);
        });
    }

    async updateSession(sessionId, updateData) {
        return new Promise((resolve, reject) => {
            const transaction = this.db.transaction(['sessions'], 'readwrite');
            const store = transaction.objectStore('sessions');
            
            const getRequest = store.get(sessionId);
            getRequest.onsuccess = () => {
                const session = getRequest.result;
                if (!session) {
                    reject(new Error('会话不存在'));
                    return;
                }

                Object.assign(session, updateData);
                const updateRequest = store.put(session);
                
                updateRequest.onsuccess = () => resolve(updateRequest.result);
                updateRequest.onerror = () => reject(updateRequest.error);
            };
            getRequest.onerror = () => reject(getRequest.error);
        });
    }

    async deleteSession(sessionId) {
        return new Promise((resolve, reject) => {
            const transaction = this.db.transaction(['sessions'], 'readwrite');
            const store = transaction.objectStore('sessions');
            const request = store.delete(sessionId);

            request.onsuccess = () => resolve(request.result);
            request.onerror = () => reject(request.error);
        });
    }

    async logActivity(logEntry) {
        return new Promise((resolve, reject) => {
            const transaction = this.db.transaction(['activity_logs'], 'readwrite');
            const store = transaction.objectStore('activity_logs');
            const request = store.add(logEntry);

            request.onsuccess = () => resolve(request.result);
            request.onerror = () => reject(request.error);
        });
    }

    async getUsers(filters = {}, pagination = {}) {
        return new Promise((resolve, reject) => {
            const transaction = this.db.transaction(['users'], 'readonly');
            const store = transaction.objectStore('users');
            const request = store.getAll();

            request.onsuccess = () => {
                let users = request.result || [];

                // 应用过滤器
                if (filters.permissionLevel !== undefined) {
                    users = users.filter(user => user.permissionLevel === filters.permissionLevel);
                }
                if (filters.isActive !== undefined) {
                    users = users.filter(user => user.isActive === filters.isActive);
                }
                if (filters.isVikeyUser !== undefined) {
                    users = users.filter(user => user.isVikeyUser === filters.isVikeyUser);
                }

                // 应用分页
                const { page = 1, limit = 10 } = pagination;
                const startIndex = (page - 1) * limit;
                const endIndex = startIndex + limit;
                const paginatedUsers = users.slice(startIndex, endIndex);

                resolve({
                    users: paginatedUsers,
                    total: users.length,
                    page: page,
                    limit: limit
                });
            };
            request.onerror = () => reject(request.error);
        });
    }

    async getUserStatistics() {
        return new Promise((resolve, reject) => {
            const transaction = this.db.transaction(['users'], 'readonly');
            const store = transaction.objectStore('users');
            const request = store.getAll();

            request.onsuccess = () => {
                const users = request.result || [];
                
                const stats = {
                    total: users.length,
                    active: users.filter(u => u.isActive).length,
                    inactive: users.filter(u => !u.isActive).length,
                    vikeyUsers: users.filter(u => u.isVikeyUser).length,
                    byPermissionLevel: {},
                    locked: users.filter(u => u.isLocked).length
                };

                // 按权限级别统计
                for (let i = 0; i <= 4; i++) {
                    stats.byPermissionLevel[i] = users.filter(u => u.permissionLevel === i).length;
                }

                resolve(stats);
            };
            request.onerror = () => reject(request.error);
        });
    }
}

// 导出类供其他模块使用
if (typeof module !== 'undefined' && module.exports) {
    module.exports = { UserManagementSystem, UserDatabase };
} else {
    window.UserManagementSystem = UserManagementSystem;
    window.UserDatabase = UserDatabase;
}