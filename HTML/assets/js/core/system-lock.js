/**
 * 系统锁定管理器
 * 实现系统锁定、超时机制和管理员Vikey例外处理
 */
class SystemLockManager {
    constructor() {
        this.isLocked = false;
        this.lockTimer = null;
        this.lockTimeout = 30 * 60 * 1000; // 默认30分钟超时
        this.warningTimer = null;
        this.warningTime = 5 * 60 * 1000; // 超时前5分钟警告
        this.userActivity = new Map();
        this.lockReason = null;
        this.lockedBy = null;
        this.lockTime = null;
        this.vikeyMonitor = null;
        this.userManagement = null;
        this.database = null;
        this.settings = {
            autoLockEnabled: true,
            lockTimeout: 30 * 60 * 1000,
            warningEnabled: true,
            warningTime: 5 * 60 * 1000,
            adminVikeyBypass: true,
            lockOnVikeyRemove: true,
            lockOnTabClose: false
        };

        // 事件监听器
        this.eventListeners = new Map();
    }

    /**
     * 初始化锁定管理器
     */
    async init() {
        try {
            console.log('初始化系统锁定管理器...');
            
            // 加载设置
            await this.loadSettings();
            
            // 初始化依赖模块
            await this.initializeDependencies();
            
            // 设置活动监听器
            this.setupActivityListeners();
            
            // 检查Vikey状态
            await this.checkVikeyStatus();
            
            // 恢复锁定状态
            await this.restoreLockState();
            
            console.log('系统锁定管理器初始化完成');
            
        } catch (error) {
            console.error('初始化锁定管理器失败:', error);
            throw error;
        }
    }

    /**
     * 初始化依赖模块
     */
    async initializeDependencies() {
        try {
            // 初始化Vikey监控
            if (typeof VikeyActiveXMonitor !== 'undefined') {
                this.vikeyMonitor = new VikeyActiveXMonitor();
                await this.vikeyMonitor.init();
                
                // 监听Vikey事件
                this.vikeyMonitor.addEventListener('deviceRemoved', (event) => {
                    this.handleVikeyRemoved(event);
                });
                
                this.vikeyMonitor.addEventListener('deviceInserted', (event) => {
                    this.handleVikeyInserted(event);
                });
            }

            // 初始化用户管理
            if (typeof UserManagementSystem !== 'undefined') {
                this.userManagement = new UserManagementSystem();
                await this.userManagement.init();
            }

            // 初始化数据库
            if (typeof VikeyDatabase !== 'undefined') {
                this.database = new VikeyDatabase();
                await this.database.init();
            }

        } catch (error) {
            console.error('初始化依赖模块失败:', error);
        }
    }

    /**
     * 设置活动监听器
     */
    setupActivityListeners() {
        // 鼠标移动
        document.addEventListener('mousemove', () => {
            this.recordUserActivity();
        });

        // 键盘输入
        document.addEventListener('keydown', () => {
            this.recordUserActivity();
        });

        // 鼠标点击
        document.addEventListener('click', () => {
            this.recordUserActivity();
        });

        // 滚动
        document.addEventListener('scroll', () => {
            this.recordUserActivity();
        });

        // 页面可见性变化
        document.addEventListener('visibilitychange', () => {
            if (document.hidden) {
                this.handlePageHidden();
            } else {
                this.handlePageVisible();
            }
        });

        // 窗口焦点变化
        window.addEventListener('blur', () => {
            this.handleWindowBlur();
        });

        window.addEventListener('focus', () => {
            this.handleWindowFocus();
        });
    }

    /**
     * 记录用户活动
     */
    recordUserActivity() {
        if (this.isLocked) return;

        const now = Date.now();
        this.userActivity.set('lastActivity', now);

        // 重置锁定计时器
        this.resetLockTimer();

        // 记录活动到数据库
        this.logActivity('USER_ACTIVITY', {
            timestamp: now,
            page: window.location.pathname
        });
    }

    /**
     * 重置锁定计时器
     */
    resetLockTimer() {
        if (!this.settings.autoLockEnabled) return;

        // 清除现有计时器
        if (this.lockTimer) {
            clearTimeout(this.lockTimer);
        }
        if (this.warningTimer) {
            clearTimeout(this.warningTimer);
        }

        // 设置新的锁定计时器
        this.lockTimer = setTimeout(() => {
            this.lockSystem('INACTIVITY_TIMEOUT');
        }, this.settings.lockTimeout);

        // 设置警告计时器
        if (this.settings.warningEnabled && this.settings.warningTime < this.settings.lockTimeout) {
            this.warningTimer = setTimeout(() => {
                this.showTimeoutWarning();
            }, this.settings.warningTime);
        }
    }

    /**
     * 锁定系统
     */
    async lockSystem(reason = 'MANUAL', options = {}) {
        try {
            // 检查管理员Vikey例外
            if (await this.checkAdminVikeyBypass()) {
                console.log('管理员Vikey插入，跳过锁定');
                return false;
            }

            if (this.isLocked) {
                console.log('系统已锁定');
                return false;
            }

            const currentUser = this.getCurrentUser();
            
            this.isLocked = true;
            this.lockReason = reason;
            this.lockedBy = currentUser?.id || null;
            this.lockTime = new Date().toISOString();

            // 清除计时器
            if (this.lockTimer) {
                clearTimeout(this.lockTimer);
                this.lockTimer = null;
            }
            if (this.warningTimer) {
                clearTimeout(this.warningTimer);
                this.warningTimer = null;
            }

            // 保存锁定状态
            await this.saveLockState();

            // 显示锁定页面
            this.showLockScreen();

            // 记录锁定事件
            await this.logActivity('SYSTEM_LOCKED', {
                reason: reason,
                lockedBy: this.lockedBy,
                lockTime: this.lockTime,
                options: options
            });

            // 触发锁定事件
            this.dispatchEvent('systemLocked', {
                reason: reason,
                lockedBy: this.lockedBy,
                lockTime: this.lockTime
            });

            console.log('系统已锁定:', reason);
            return true;

        } catch (error) {
            console.error('锁定系统失败:', error);
            return false;
        }
    }

    /**
     * 解锁系统
     */
    async unlockSystem(credentials = null) {
        try {
            if (!this.isLocked) {
                console.log('系统未锁定');
                return false;
            }

            // 验证解锁凭据
            if (!await this.validateUnlockCredentials(credentials)) {
                this.showUnlockError('凭据验证失败');
                return false;
            }

            this.isLocked = false;
            this.lockReason = null;
            this.lockedBy = null;
            this.lockTime = null;

            // 清除锁定状态
            await this.clearLockState();

            // 隐藏锁定页面
            this.hideLockScreen();

            // 重置活动计时器
            this.resetLockTimer();

            // 记录解锁事件
            await this.logActivity('SYSTEM_UNLOCKED', {
                unlockedBy: this.getCurrentUser()?.id || null,
                unlockTime: new Date().toISOString()
            });

            // 触发解锁事件
            this.dispatchEvent('systemUnlocked', {
                unlockedBy: this.getCurrentUser()?.id || null,
                unlockTime: new Date().toISOString()
            });

            console.log('系统已解锁');
            return true;

        } catch (error) {
            console.error('解锁系统失败:', error);
            return false;
        }
    }

    /**
     * 检查管理员Vikey例外
     */
    async checkAdminVikeyBypass() {
        if (!this.settings.adminVikeyBypass) {
            return false;
        }

        try {
            // 检查是否有管理员Vikey插入
            if (this.vikeyMonitor) {
                const devices = await this.vikeyMonitor.getConnectedDevices();
                
                for (const device of devices) {
                    // 检查设备是否属于管理员用户
                    const isAdminDevice = await this.checkDeviceAdminStatus(device);
                    if (isAdminDevice) {
                        return true;
                    }
                }
            }

            return false;

        } catch (error) {
            console.error('检查管理员Vikey例外失败:', error);
            return false;
        }
    }

    /**
     * 检查设备管理员状态
     */
    async checkDeviceAdminStatus(device) {
        try {
            if (!this.database) return false;

            // 查询设备对应的用户
            const vikeyInfo = await this.database.getVikeyInfo(device.deviceId);
            if (!vikeyInfo) return false;

            // 查询用户权限
            const user = await this.database.getUser(vikeyInfo.userId);
            if (!user) return false;

            // 检查是否为管理员级别
            return user.permissionLevel >= 2; // 管理员及以上

        } catch (error) {
            console.error('检查设备管理员状态失败:', error);
            return false;
        }
    }

    /**
     * 验证解锁凭据
     */
    async validateUnlockCredentials(credentials) {
        try {
            if (!credentials) {
                return false;
            }

            // 支持多种解锁方式
            if (credentials.type === 'password') {
                return await this.validatePasswordUnlock(credentials);
            } else if (credentials.type === 'vikey') {
                return await this.validateVikeyUnlock(credentials);
            } else if (credentials.type === 'biometric') {
                return await this.validateBiometricUnlock(credentials);
            }

            return false;

        } catch (error) {
            console.error('验证解锁凭据失败:', error);
            return false;
        }
    }

    /**
     * 验证密码解锁
     */
    async validatePasswordUnlock(credentials) {
        try {
            if (!this.userManagement) return false;

            const currentUser = this.getCurrentUser();
            if (!currentUser) return false;

            // 验证密码
            const isValid = await this.userManagement.validatePassword(
                currentUser.username,
                credentials.password
            );

            if (isValid) {
                // 记录成功登录
                await this.userManagement.recordLogin(currentUser.username, true);
            } else {
                // 记录失败登录
                await this.userManagement.recordLogin(currentUser.username, false);
            }

            return isValid;

        } catch (error) {
            console.error('密码验证失败:', error);
            return false;
        }
    }

    /**
     * 验证Vikey解锁
     */
    async validateVikeyUnlock(credentials) {
        try {
            if (!this.vikeyMonitor) return false;

            // 检查Vikey设备
            const devices = await this.vikeyMonitor.getConnectedDevices();
            if (devices.length === 0) {
                return false;
            }

            // 验证设备
            for (const device of devices) {
                const isValid = await this.vikeyMonitor.verifyDevice(device.deviceId);
                if (isValid) {
                    // 检查设备权限
                    const hasPermission = await this.checkDeviceUnlockPermission(device);
                    if (hasPermission) {
                        return true;
                    }
                }
            }

            return false;

        } catch (error) {
            console.error('Vikey验证失败:', error);
            return false;
        }
    }

    /**
     * 检查设备解锁权限
     */
    async checkDeviceUnlockPermission(device) {
        try {
            if (!this.database) return false;

            const vikeyInfo = await this.database.getVikeyInfo(device.deviceId);
            if (!vikeyInfo) return false;

            const user = await this.database.getUser(vikeyInfo.userId);
            if (!user) return false;

            // 检查用户状态
            if (!user.isActive || user.isLocked) {
                return false;
            }

            return true;

        } catch (error) {
            console.error('检查设备解锁权限失败:', error);
            return false;
        }
    }

    /**
     * 显示锁定屏幕
     */
    showLockScreen() {
        // 创建锁定屏幕覆盖层
        const lockOverlay = document.createElement('div');
        lockOverlay.id = 'system-lock-overlay';
        lockOverlay.style.cssText = `
            position: fixed;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            z-index: 9999;
            display: flex;
            align-items: center;
            justify-content: center;
            font-family: 'Microsoft YaHei', Arial, sans-serif;
        `;

        lockOverlay.innerHTML = `
            <div class="lock-container" style="
                background: white;
                border-radius: 20px;
                padding: 40px;
                box-shadow: 0 20px 60px rgba(0, 0, 0, 0.3);
                text-align: center;
                max-width: 400px;
                width: 90%;
            ">
                <div class="lock-icon" style="
                    font-size: 64px;
                    margin-bottom: 20px;
                ">🔒</div>
                
                <h2 class="lock-title" style="
                    color: #333;
                    margin-bottom: 10px;
                    font-size: 24px;
                ">系统已锁定</h2>
                
                <p class="lock-reason" style="
                    color: #666;
                    margin-bottom: 30px;
                    font-size: 14px;
                ">${this.getLockReasonText()}</p>
                
                <div class="unlock-methods">
                    <div class="password-unlock" style="margin-bottom: 20px;">
                        <input type="password" id="unlock-password" placeholder="输入密码解锁" style="
                            width: 100%;
                            padding: 12px;
                            border: 1px solid #ddd;
                            border-radius: 8px;
                            margin-bottom: 10px;
                            font-size: 14px;
                        ">
                        <button onclick="attemptPasswordUnlock()" style="
                            width: 100%;
                            padding: 12px;
                            background: #667eea;
                            color: white;
                            border: none;
                            border-radius: 8px;
                            cursor: pointer;
                            font-size: 14px;
                        ">密码解锁</button>
                    </div>
                    
                    <div class="vikey-unlock" style="margin-bottom: 20px;">
                        <button onclick="attemptVikeyUnlock()" style="
                            width: 100%;
                            padding: 12px;
                            background: #28a745;
                            color: white;
                            border: none;
                            border-radius: 8px;
                            cursor: pointer;
                            font-size: 14px;
                        ">🔑 Vikey解锁</button>
                    </div>
                </div>
                
                <div class="unlock-status" id="unlock-status" style="
                    margin-top: 20px;
                    font-size: 12px;
                    color: #666;
                    min-height: 20px;
                "></div>
            </div>
        `;

        document.body.appendChild(lockOverlay);

        // 聚焦密码输入框
        setTimeout(() => {
            const passwordInput = document.getElementById('unlock-password');
            if (passwordInput) {
                passwordInput.focus();
            }
        }, 100);
    }

    /**
     * 隐藏锁定屏幕
     */
    hideLockScreen() {
        const lockOverlay = document.getElementById('system-lock-overlay');
        if (lockOverlay) {
            lockOverlay.remove();
        }
    }

    /**
     * 获取锁定原因文本
     */
    getLockReasonText() {
        const reasons = {
            'MANUAL': '手动锁定',
            'INACTIVITY_TIMEOUT': '长时间无操作自动锁定',
            'VIKEY_REMOVED': 'Vikey设备被移除',
            'TAB_CLOSED': '标签页关闭',
            'SECURITY_POLICY': '安全策略触发',
            'ADMIN_ACTION': '管理员操作'
        };

        return reasons[this.lockReason] || '未知原因';
    }

    /**
     * 显示超时警告
     */
    showTimeoutWarning() {
        const warningDiv = document.createElement('div');
        warningDiv.id = 'timeout-warning';
        warningDiv.style.cssText = `
            position: fixed;
            top: 20px;
            right: 20px;
            background: #fff3cd;
            border: 1px solid #ffeaa7;
            color: #856404;
            padding: 15px 20px;
            border-radius: 8px;
            box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
            z-index: 1000;
            font-family: 'Microsoft YaHei', Arial, sans-serif;
            font-size: 14px;
            max-width: 300px;
        `;

        warningDiv.innerHTML = `
            <div style="display: flex; align-items: center; gap: 10px;">
                <span style="font-size: 20px;">⚠️</span>
                <div>
                    <strong>系统即将锁定</strong>
                    <div style="font-size: 12px; margin-top: 5px;">
                        由于长时间无操作，系统将在5分钟后自动锁定
                    </div>
                </div>
            </div>
            <button onclick="dismissTimeoutWarning()" style="
                margin-top: 10px;
                width: 100%;
                padding: 8px;
                background: #856404;
                color: white;
                border: none;
                border-radius: 4px;
                cursor: pointer;
                font-size: 12px;
            ">我知道了</button>
        `;

        document.body.appendChild(warningDiv);

        // 自动移除警告
        setTimeout(() => {
            dismissTimeoutWarning();
        }, 30000); // 30秒后自动移除
    }

    /**
     * 处理Vikey移除
     */
    async handleVikeyRemoved(event) {
        try {
            console.log('Vikey设备被移除:', event.detail);

            if (this.settings.lockOnVikeyRemove) {
                await this.lockSystem('VIKEY_REMOVED', {
                    deviceId: event.detail.deviceId
                });
            }

        } catch (error) {
            console.error('处理Vikey移除失败:', error);
        }
    }

    /**
     * 处理Vikey插入
     */
    async handleVikeyInserted(event) {
        try {
            console.log('Vikey设备插入:', event.detail);

            // 检查是否为管理员设备，如果是则自动解锁
            if (this.isLocked) {
                const isAdminDevice = await this.checkDeviceAdminStatus(event.detail);
                if (isAdminDevice) {
                    await this.unlockSystem({
                        type: 'vikey',
                        deviceId: event.detail.deviceId
                    });
                }
            }

        } catch (error) {
            console.error('处理Vikey插入失败:', error);
        }
    }

    /**
     * 处理页面隐藏
     */
    handlePageHidden() {
        if (this.settings.lockOnTabClose && !this.isLocked) {
            // 延迟锁定，避免快速切换标签页误触发
            setTimeout(() => {
                if (document.hidden && !this.isLocked) {
                    this.lockSystem('TAB_CLOSED');
                }
            }, 5000); // 5秒延迟
        }
    }

    /**
     * 处理页面可见
     */
    handlePageVisible() {
        // 页面重新可见时记录活动
        this.recordUserActivity();
    }

    /**
     * 处理窗口失焦
     */
    handleWindowBlur() {
        // 可以添加窗口失焦的处理逻辑
    }

    /**
     * 处理窗口聚焦
     */
    handleWindowFocus() {
        // 窗口重新聚焦时记录活动
        this.recordUserActivity();
    }

    /**
     * 检查Vikey状态
     */
    async checkVikeyStatus() {
        try {
            if (!this.vikeyMonitor) return;

            const devices = await this.vikeyMonitor.getConnectedDevices();
            console.log('当前连接的Vikey设备:', devices.length);

            // 检查是否有管理员设备插入
            for (const device of devices) {
                const isAdminDevice = await this.checkDeviceAdminStatus(device);
                if (isAdminDevice) {
                    console.log('检测到管理员Vikey设备:', device.deviceId);
                    break;
                }
            }

        } catch (error) {
            console.error('检查Vikey状态失败:', error);
        }
    }

    /**
     * 加载设置
     */
    async loadSettings() {
        try {
            if (!this.database) return;

            const config = await this.database.getConfig('system-lock');
            if (config) {
                this.settings = { ...this.settings, ...config.value };
            }

        } catch (error) {
            console.error('加载锁定设置失败:', error);
        }
    }

    /**
     * 保存锁定状态
     */
    async saveLockState() {
        try {
            if (!this.database) return;

            const lockState = {
                isLocked: this.isLocked,
                lockReason: this.lockReason,
                lockedBy: this.lockedBy,
                lockTime: this.lockTime
            };

            await this.database.setConfig('system-lock-state', lockState);

        } catch (error) {
            console.error('保存锁定状态失败:', error);
        }
    }

    /**
     * 恢复锁定状态
     */
    async restoreLockState() {
        try {
            if (!this.database) return;

            const lockState = await this.database.getConfig('system-lock-state');
            if (lockState && lockState.value.isLocked) {
                this.isLocked = lockState.value.isLocked;
                this.lockReason = lockState.value.lockReason;
                this.lockedBy = lockState.value.lockedBy;
                this.lockTime = lockState.value.lockTime;

                // 显示锁定屏幕
                this.showLockScreen();
            }

        } catch (error) {
            console.error('恢复锁定状态失败:', error);
        }
    }

    /**
     * 清除锁定状态
     */
    async clearLockState() {
        try {
            if (!this.database) return;

            await this.database.deleteConfig('system-lock-state');

        } catch (error) {
            console.error('清除锁定状态失败:', error);
        }
    }

    /**
     * 记录活动
     */
    async logActivity(activityType, data) {
        try {
            if (!this.database) return;

            await this.database.addActivityLog({
                type: activityType,
                data: data,
                timestamp: new Date().toISOString(),
                userId: this.getCurrentUser()?.id || null,
                sessionId: this.getSessionId()
            });

        } catch (error) {
            console.error('记录活动失败:', error);
        }
    }

    /**
     * 获取当前用户
     */
    getCurrentUser() {
        if (this.userManagement) {
            return this.userManagement.getCurrentUser();
        }
        return null;
    }

    /**
     * 获取会话ID
     */
    getSessionId() {
        // 从sessionStorage或localStorage获取会话ID
        return sessionStorage.getItem('sessionId') || 'anonymous';
    }

    /**
     * 添加事件监听器
     */
    addEventListener(event, callback) {
        if (!this.eventListeners.has(event)) {
            this.eventListeners.set(event, []);
        }
        this.eventListeners.get(event).push(callback);
    }

    /**
     * 移除事件监听器
     */
    removeEventListener(event, callback) {
        if (this.eventListeners.has(event)) {
            const listeners = this.eventListeners.get(event);
            const index = listeners.indexOf(callback);
            if (index > -1) {
                listeners.splice(index, 1);
            }
        }
    }

    /**
     * 触发事件
     */
    dispatchEvent(event, data) {
        if (this.eventListeners.has(event)) {
            this.eventListeners.get(event).forEach(callback => {
                try {
                    callback(data);
                } catch (error) {
                    console.error('事件回调执行失败:', error);
                }
            });
        }
    }

    /**
     * 更新设置
     */
    async updateSettings(newSettings) {
        try {
            this.settings = { ...this.settings, ...newSettings };

            if (this.database) {
                await this.database.setConfig('system-lock', this.settings);
            }

            // 重新设置计时器
            this.resetLockTimer();

            console.log('锁定设置已更新:', this.settings);

        } catch (error) {
            console.error('更新锁定设置失败:', error);
        }
    }

    /**
     * 获取锁定状态
     */
    getLockStatus() {
        return {
            isLocked: this.isLocked,
            lockReason: this.lockReason,
            lockedBy: this.lockedBy,
            lockTime: this.lockTime,
            settings: this.settings
        };
    }

    /**
     * 强制锁定（用于管理员操作）
     */
    async forceLock(reason = 'ADMIN_ACTION') {
        return await this.lockSystem(reason, { force: true });
    }

    /**
     * 强制解锁（用于管理员操作）
     */
    async forceUnlock() {
        return await this.unlockSystem({ type: 'admin' });
    }
}

// 全局函数，供HTML调用
let systemLockManager = null;

// 密码解锁
async function attemptPasswordUnlock() {
    const passwordInput = document.getElementById('unlock-password');
    const statusDiv = document.getElementById('unlock-status');
    
    if (!passwordInput || !systemLockManager) return;

    const password = passwordInput.value.trim();
    if (!password) {
        statusDiv.textContent = '请输入密码';
        statusDiv.style.color = '#dc3545';
        return;
    }

    statusDiv.textContent = '正在验证...';
    statusDiv.style.color = '#667eea';

    try {
        const success = await systemLockManager.unlockSystem({
            type: 'password',
            password: password
        });

        if (success) {
            statusDiv.textContent = '解锁成功';
            statusDiv.style.color = '#28a745';
        } else {
            statusDiv.textContent = '密码错误';
            statusDiv.style.color = '#dc3545';
            passwordInput.value = '';
            passwordInput.focus();
        }

    } catch (error) {
        statusDiv.textContent = '解锁失败: ' + error.message;
        statusDiv.style.color = '#dc3545';
    }
}

// Vikey解锁
async function attemptVikeyUnlock() {
    const statusDiv = document.getElementById('unlock-status');
    
    if (!systemLockManager) return;

    statusDiv.textContent = '正在检查Vikey设备...';
    statusDiv.style.color = '#667eea';

    try {
        const success = await systemLockManager.unlockSystem({
            type: 'vikey'
        });

        if (success) {
            statusDiv.textContent = 'Vikey验证成功';
            statusDiv.style.color = '#28a745';
        } else {
            statusDiv.textContent = '未找到有效的Vikey设备';
            statusDiv.style.color = '#dc3545';
        }

    } catch (error) {
        statusDiv.textContent = 'Vikey验证失败: ' + error.message;
        statusDiv.style.color = '#dc3545';
    }
}

// 关闭超时警告
function dismissTimeoutWarning() {
    const warningDiv = document.getElementById('timeout-warning');
    if (warningDiv) {
        warningDiv.remove();
    }
}

// 初始化系统锁定管理器
document.addEventListener('DOMContentLoaded', async function() {
    try {
        systemLockManager = new SystemLockManager();
        await systemLockManager.init();
        
        // 添加回车键支持
        document.addEventListener('keydown', function(event) {
            if (event.key === 'Enter' && systemLockManager.isLocked) {
                const passwordInput = document.getElementById('unlock-password');
                if (passwordInput && document.activeElement === passwordInput) {
                    attemptPasswordUnlock();
                }
            }
        });

        console.log('系统锁定管理器已启动');
        
    } catch (error) {
        console.error('启动系统锁定管理器失败:', error);
    }
});

// 导出类供其他模块使用
if (typeof module !== 'undefined' && module.exports) {
    module.exports = SystemLockManager;
}