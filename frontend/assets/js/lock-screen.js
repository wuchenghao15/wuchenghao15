// 锁定界面管理
class LockScreenManager {
    constructor() {
        this.lockTimeout = null;
        this.lockTime = 15 * 60 * 1000; // 15分钟
        this.failedAttempts = 0;
        this.maxAttempts = 5;
        this.lockoutTime = 5 * 60 * 1000; // 5分钟锁定
        this.lastActivityTime = Date.now();
        this.isLocked = false;
        this.isLockout = false;
        this.lockoutEndTime = 0;
        
        // 初始化DOM元素
        this.initializeElements();
        
        // 启动活动监控
        this.startActivityMonitoring();
        
        // 启动自动锁定计时器
        this.startLockTimer();
        
        console.log('锁定界面管理器已初始化');
    }
    
    // 初始化DOM元素
    initializeElements() {
        // 检查锁定界面是否已存在
        this.lockScreen = document.getElementById('lockScreen');
        if (!this.lockScreen) {
            this.createLockScreen();
        } else {
            this.lockScreen = document.getElementById('lockScreen');
        }
        
        this.lockUsername = document.getElementById('lockUsername');
        this.lockPassword = document.getElementById('lockPassword');
        this.lockVkey = document.getElementById('lockVkey');
        this.lockButton = document.getElementById('lockButton');
        this.lockError = document.getElementById('lockError');
        this.lockTimeLeft = document.getElementById('lockTimeLeft');
        
        // 添加事件监听器
        if (this.lockButton) {
            this.lockButton.addEventListener('click', () => this.unlock());
        }
        
        // 按Enter键解锁
        document.addEventListener('keydown', (e) => {
            if (this.isLocked && e.key === 'Enter') {
                this.unlock();
            }
        });
    }
    
    // 创建锁定界面
    createLockScreen() {
        const lockScreenHTML = `
        <div id="lockScreen" class="lock-screen">
            <div class="lock-container">
                <div class="lock-header">
                    <div class="lock-icon">🔒</div>
                    <h2 class="lock-title">系统已锁定</h2>
                    <p class="lock-subtitle">请验证您的身份以继续</p>
                </div>
                
                <div id="lockError" class="lock-error"></div>
                
                <form class="lock-form" onsubmit="event.preventDefault();">
                    <div class="lock-form-group">
                        <label for="lockUsername" class="lock-form-label">用户名</label>
                        <input type="text" id="lockUsername" class="lock-form-input" placeholder="请输入用户名" required>
                    </div>
                    
                    <div class="lock-form-group">
                        <label for="lockPassword" class="lock-form-label">密码</label>
                        <input type="password" id="lockPassword" class="lock-form-input" placeholder="请输入密码" required>
                    </div>
                    
                    <div class="lock-form-group">
                        <label for="lockVkey" class="lock-form-label">vKey认证码</label>
                        <input type="text" id="lockVkey" class="lock-form-input" placeholder="请输入vKey认证码" required>
                    </div>
                    
                    <button type="button" id="lockButton" class="lock-form-button">解锁系统</button>
                </form>
                
                <p class="lock-info">为了您的安全，系统在15分钟不活动后会自动锁定</p>
            </div>
        </div>
        `;
        
        const lockScreenContainer = document.createElement('div');
        lockScreenContainer.innerHTML = lockScreenHTML;
        document.body.appendChild(lockScreenContainer.firstElementChild);
    }
    
    // 启动活动监控
    startActivityMonitoring() {
        const activityEvents = ['mousemove', 'keydown', 'click', 'scroll', 'touchstart'];
        
        activityEvents.forEach(event => {
            document.addEventListener(event, () => this.resetActivity());
        });
    }
    
    // 重置活动时间
    resetActivity() {
        this.lastActivityTime = Date.now();
        
        // 如果处于锁定状态，不重置计时器
        if (this.isLocked) return;
        
        this.resetLockTimer();
    }
    
    // 启动锁定计时器
    startLockTimer() {
        this.lockTimeout = setTimeout(() => {
            this.lock();
        }, this.lockTime);
    }
    
    // 重置锁定计时器
    resetLockTimer() {
        if (this.lockTimeout) {
            clearTimeout(this.lockTimeout);
        }
        this.startLockTimer();
    }
    
    // 锁定系统
    lock() {
        if (this.isLocked || this.isLockout) return;
        
        this.isLocked = true;
        
        // 显示锁定界面
        if (this.lockScreen) {
            this.lockScreen.classList.add('active');
            
            // 尝试填充用户名
            const storedUsername = localStorage.getItem('lastUsername') || '';
            if (this.lockUsername && storedUsername) {
                this.lockUsername.value = storedUsername;
                this.lockPassword?.focus();
            } else if (this.lockUsername) {
                this.lockUsername.focus();
            }
        }
        
        // 记录锁定日志
        console.log('系统已锁定');
        this.logActivity('system_locked', { reason: 'inactivity_timeout' });
    }
    
    // 解锁系统
    unlock() {
        // 检查是否处于锁定状态
        if (!this.isLocked) return;
        
        // 检查是否被锁定在外面
        if (this.isLockout) {
            const remainingTime = Math.ceil((this.lockoutEndTime - Date.now()) / 1000);
            this.showError(`账户已被锁定，请在 ${Math.floor(remainingTime / 60)}:${(remainingTime % 60).toString().padStart(2, '0')} 后重试`);
            return;
        }
        
        // 获取用户输入
        const username = this.lockUsername?.value.trim() || '';
        const password = this.lockPassword?.value || '';
        const vkey = this.lockVkey?.value.trim() || '';
        
        // 验证输入
        if (!username || !password || !vkey) {
            this.showError('请输入所有必填字段');
            return;
        }
        
        // 模拟验证过程
        if (this.validateCredentials(username, password, vkey)) {
            this.unlockSuccess(username);
        } else {
            this.unlockFailed();
        }
    }
    
    // 验证凭证
    validateCredentials(username, password, vkey) {
        // 这里应该是与服务器验证的逻辑
        // 现在使用模拟验证
        const storedUsername = localStorage.getItem('validUsername') || 'admin';
        const storedPasswordHash = localStorage.getItem('validPasswordHash') || this.hashPassword('password123');
        const validVkey = localStorage.getItem('validVkey') || 'vkey123';
        
        // 基本验证逻辑
        return username === storedUsername && 
               this.hashPassword(password) === storedPasswordHash && 
               vkey === validVkey;
    }
    
    // 密码哈希函数
    hashPassword(password) {
        // 简单的哈希实现，实际应用中应该使用更安全的方法
        let hash = 0;
        for (let i = 0; i < password.length; i++) {
            const char = password.charCodeAt(i);
            hash = ((hash << 5) - hash) + char;
            hash = hash & hash;
        }
        return hash.toString(36);
    }
    
    // 解锁成功
    unlockSuccess(username) {
        // 重置失败尝试次数
        this.failedAttempts = 0;
        
        // 隐藏锁定界面
        if (this.lockScreen) {
            this.lockScreen.classList.remove('active');
        }
        
        // 重置表单
        this.resetForm();
        
        // 重置锁定状态
        this.isLocked = false;
        
        // 保存最后用户名
        localStorage.setItem('lastUsername', username);
        
        // 重启锁定计时器
        this.resetActivity();
        
        console.log('系统已成功解锁');
        this.logActivity('system_unlocked', { username });
    }
    
    // 解锁失败
    unlockFailed() {
        this.failedAttempts++;
        
        // 显示错误信息
        this.showError(`解锁失败，剩余尝试次数: ${this.maxAttempts - this.failedAttempts}`);
        
        // 记录失败尝试
        this.logActivity('unlock_failed', { attempts: this.failedAttempts });
        
        // 检查是否需要锁定账户
        if (this.failedAttempts >= this.maxAttempts) {
            this.lockoutAccount();
        }
    }
    
    // 锁定账户
    lockoutAccount() {
        this.isLockout = true;
        this.lockoutEndTime = Date.now() + this.lockoutTime;
        
        // 禁用解锁按钮
        if (this.lockButton) {
            this.lockButton.disabled = true;
        }
        
        // 显示锁定信息
        this.showError(`账户已被锁定5分钟，防止暴力破解`);
        
        // 开始倒计时
        this.startLockoutCountdown();
        
        // 记录锁定日志
        this.logActivity('account_locked', { reason: 'brute_force_attempt' });
        console.log('账户已被锁定5分钟');
    }
    
    // 锁定倒计时
    startLockoutCountdown() {
        const updateCountdown = () => {
            const remainingTime = this.lockoutEndTime - Date.now();
            
            if (remainingTime <= 0) {
                // 锁定时间结束
                this.isLockout = false;
                this.failedAttempts = 0;
                
                if (this.lockButton) {
                    this.lockButton.disabled = false;
                }
                
                this.hideError();
                return;
            }
            
            // 更新倒计时显示
            const minutes = Math.floor(remainingTime / 60000);
            const seconds = Math.floor((remainingTime % 60000) / 1000);
            
            this.showError(`账户已被锁定，请在 ${minutes}:${seconds.toString().padStart(2, '0')} 后重试`);
            
            // 继续倒计时
            setTimeout(updateCountdown, 1000);
        };
        
        updateCountdown();
    }
    
    // 显示错误信息
    showError(message) {
        if (this.lockError) {
            this.lockError.textContent = message;
            this.lockError.classList.add('active');
        }
    }
    
    // 隐藏错误信息
    hideError() {
        if (this.lockError) {
            this.lockError.classList.remove('active');
        }
    }
    
    // 重置表单
    resetForm() {
        if (this.lockPassword) this.lockPassword.value = '';
        if (this.lockVkey) this.lockVkey.value = '';
        this.hideError();
    }
    
    // 手动锁定系统
    manualLock() {
        this.lock();
    }
    
    // 记录活动日志
    logActivity(action, details = {}) {
        try {
            const logEntry = {
                timestamp: new Date().toISOString(),
                action,
                details,
                userAgent: navigator.userAgent
            };
            
            // 保存到localStorage或发送到服务器
            console.log('活动日志:', logEntry);
            
            // 可以添加发送到服务器的逻辑
        } catch (error) {
            console.error('记录日志失败:', error);
        }
    }
    
    // 销毁实例
    destroy() {
        if (this.lockTimeout) {
            clearTimeout(this.lockTimeout);
        }
        this.isLocked = false;
        this.isLockout = false;
        console.log('锁定界面管理器已销毁');
    }
}

// 页面加载完成后初始化
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', () => {
        // 检查是否已经初始化
        if (!window.lockScreenManager) {
            window.lockScreenManager = new LockScreenManager();
        }
    });
} else {
    if (!window.lockScreenManager) {
        window.lockScreenManager = new LockScreenManager();
    }
}

// 导出为模块（如果支持）
if (typeof module !== 'undefined' && module.exports) {
    module.exports = LockScreenManager;
}