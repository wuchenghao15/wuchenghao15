// 全局超时监控和锁定系统
class GlobalLockSystem {
    constructor() {
        this.lockTimeout = 15 * 60 * 1000; // 15分钟无操作锁定
        this.warningTimeout = 1 * 60 * 1000; // 锁定前1分钟警告
        this.warningShown = false;
        this.lastActivity = Date.now();
        this.lockTimer = null;
        this.warningTimer = null;
        this.isLocked = false;
        this.lockCheckInterval = null;
        this.activityEvents = [
            'mousedown', 'mousemove', 'keypress', 'scroll', 'touchstart', 'click',
            'keydown', 'keyup', 'focus', 'blur', 'touchmove', 'touchend'
        ];
        
        this.init();
    }

    // 初始化系统
    init() {
        console.log('初始化全局锁定系统');
        
        // 检查当前页面是否为锁定页面
        if (this.isLockPage()) {
            console.log('当前为锁定页面，不启动监控');
            return;
        }
        
        // 启动活动监控
        this.startActivityMonitoring();
        
        // 启动定时检查
        this.startLockCheck();
        
        // 恢复之前的锁定状态
        this.restoreLockState();
        
        console.log('全局锁定系统已启动');
    }

    // 检查是否为锁定页面
    isLockPage() {
        return window.location.pathname.includes('locked.html') || 
               window.location.pathname.endsWith('/locked');
    }

    // 启动活动监控
    startActivityMonitoring() {
        // 监听用户活动
        this.activityEvents.forEach(event => {
            document.addEventListener(event, () => {
                this.recordActivity();
            }, { passive: true });
        });

        // 监听页面可见性变化
        document.addEventListener('visibilitychange', () => {
            if (!document.hidden) {
                this.recordActivity();
            }
        });

        // 监听窗口焦点
        window.addEventListener('focus', () => {
            this.recordActivity();
        });
    }

    // 记录用户活动
    recordActivity() {
        const now = Date.now();
        
        // 如果距离上次活动超过5秒，才更新时间
        if (now - this.lastActivity > 5000) {
            console.log('检测到用户活动');
        }
        
        this.lastActivity = now;
        this.warningShown = false;
        
        // 重置定时器
        this.resetTimers();
    }

    // 重置定时器
    resetTimers() {
        // 清除现有定时器
        this.clearTimers();
        
        // 设置警告定时器
        this.warningTimer = setTimeout(() => {
            this.showWarning();
        }, this.lockTimeout - this.warningTimeout);
        
        // 设置锁定定时器
        this.lockTimer = setTimeout(() => {
            this.lockSystem();
        }, this.lockTimeout);
    }

    // 清除定时器
    clearTimers() {
        if (this.lockTimer) {
            clearTimeout(this.lockTimer);
            this.lockTimer = null;
        }
        
        if (this.warningTimer) {
            clearTimeout(this.warningTimer);
            this.warningTimer = null;
        }
    }

    // 启动锁定检查
    startLockCheck() {
        // 每30秒检查一次是否需要锁定
        this.lockCheckInterval = setInterval(() => {
            this.checkLockStatus();
        }, 30000);
    }

    // 检查锁定状态
    checkLockStatus() {
        if (this.isLocked || this.isLockPage()) {
            return;
        }
        
        const now = Date.now();
        const timeSinceLastActivity = now - this.lastActivity;
        
        if (timeSinceLastActivity >= this.lockTimeout) {
            console.log('检测到超时，锁定系统');
            this.lockSystem();
        } else if (timeSinceLastActivity >= this.lockTimeout - this.warningTimeout && !this.warningShown) {
            console.log('显示锁定警告');
            this.showWarning();
        }
    }

    // 显示锁定警告
    showWarning() {
        if (this.warningShown || this.isLocked) {
            return;
        }
        
        this.warningShown = true;
        
        // 创建警告提示
        const warning = this.createWarningDialog();
        document.body.appendChild(warning);
        
        // 显示警告
        setTimeout(() => {
            warning.classList.add('show');
        }, 100);
        
        // 10秒后自动隐藏
        setTimeout(() => {
            this.hideWarning();
        }, 10000);
        
        console.log('显示锁定警告：系统将在1分钟后锁定');
    }

    // 创建警告对话框
    createWarningDialog() {
        const warning = document.createElement('div');
        warning.id = 'lock-warning';
        warning.innerHTML = `
            <div class="warning-overlay">
                <div class="warning-dialog">
                    <div class="warning-icon">
                        <i class="fas fa-exclamation-triangle"></i>
                    </div>
                    <div class="warning-content">
                        <h3>系统即将锁定</h3>
                        <p>检测到长时间无操作，系统将在1分钟后自动锁定以保护安全。</p>
                        <div class="warning-countdown">
                            <span id="warning-countdown">60</span> 秒
                        </div>
                        <div class="warning-actions">
                            <button class="btn-continue" onclick="globalLockSystem.hideWarning()">
                                继续使用
                            </button>
                            <button class="btn-lock-now" onclick="globalLockSystem.lockSystem()">
                                立即锁定
                            </button>
                        </div>
                    </div>
                </div>
            </div>
        `;
        
        // 添加样式
        this.addWarningStyles();
        
        // 启动倒计时
        this.startWarningCountdown();
        
        return warning;
    }

    // 添加警告样式
    addWarningStyles() {
        if (document.getElementById('lock-warning-styles')) {
            return;
        }
        
        const style = document.createElement('style');
        style.id = 'lock-warning-styles';
        style.textContent = `
            #lock-warning {
                position: fixed;
                top: 0;
                left: 0;
                width: 100%;
                height: 100%;
                z-index: 99999;
                opacity: 0;
                visibility: hidden;
                transition: all 0.3s ease;
            }
            
            #lock-warning.show {
                opacity: 1;
                visibility: visible;
            }
            
            .warning-overlay {
                position: absolute;
                top: 0;
                left: 0;
                width: 100%;
                height: 100%;
                background: rgba(0, 0, 0, 0.7);
                backdrop-filter: blur(5px);
                display: flex;
                align-items: center;
                justify-content: center;
            }
            
            .warning-dialog {
                background: white;
                border-radius: 12px;
                padding: 30px;
                max-width: 400px;
                width: 90%;
                text-align: center;
                box-shadow: 0 20px 60px rgba(0, 0, 0, 0.3);
                animation: warningSlideIn 0.3s ease;
            }
            
            @keyframes warningSlideIn {
                from {
                    opacity: 0;
                    transform: translateY(-50px) scale(0.9);
                }
                to {
                    opacity: 1;
                    transform: translateY(0) scale(1);
                }
            }
            
            .warning-icon {
                font-size: 48px;
                color: #f59e0b;
                margin-bottom: 20px;
                animation: warningPulse 2s infinite;
            }
            
            @keyframes warningPulse {
                0%, 100% { transform: scale(1); }
                50% { transform: scale(1.1); }
            }
            
            .warning-content h3 {
                margin: 0 0 15px 0;
                color: #1f2937;
                font-size: 20px;
                font-weight: 600;
            }
            
            .warning-content p {
                margin: 0 0 20px 0;
                color: #6b7280;
                line-height: 1.5;
            }
            
            .warning-countdown {
                font-size: 36px;
                font-weight: 700;
                color: #dc2626;
                margin-bottom: 25px;
                font-variant-numeric: tabular-nums;
            }
            
            .warning-actions {
                display: flex;
                gap: 10px;
                justify-content: center;
            }
            
            .btn-continue, .btn-lock-now {
                padding: 10px 20px;
                border: none;
                border-radius: 6px;
                font-size: 14px;
                font-weight: 500;
                cursor: pointer;
                transition: all 0.2s ease;
            }
            
            .btn-continue {
                background: #2563eb;
                color: white;
            }
            
            .btn-continue:hover {
                background: #1d4ed8;
            }
            
            .btn-lock-now {
                background: #f3f4f6;
                color: #374151;
            }
            
            .btn-lock-now:hover {
                background: #e5e7eb;
            }
            
            @media (max-width: 480px) {
                .warning-dialog {
                    padding: 20px;
                    margin: 20px;
                }
                
                .warning-actions {
                    flex-direction: column;
                }
                
                .btn-continue, .btn-lock-now {
                    width: 100%;
                }
            }
        `;
        
        document.head.appendChild(style);
    }

    // 启动警告倒计时
    startWarningCountdown() {
        let countdown = 60;
        const countdownElement = document.getElementById('warning-countdown');
        
        const countdownInterval = setInterval(() => {
            countdown--;
            if (countdownElement) {
                countdownElement.textContent = countdown;
            }
            
            if (countdown <= 0) {
                clearInterval(countdownInterval);
                this.lockSystem();
            }
        }, 1000);
        
        // 保存倒计时ID以便清理
        this.warningCountdownInterval = countdownInterval;
    }

    // 隐藏警告
    hideWarning() {
        const warning = document.getElementById('lock-warning');
        if (warning) {
            warning.classList.remove('show');
            setTimeout(() => {
                if (warning.parentNode) {
                    warning.parentNode.removeChild(warning);
                }
            }, 300);
        }
        
        // 清除倒计时
        if (this.warningCountdownInterval) {
            clearInterval(this.warningCountdownInterval);
            this.warningCountdownInterval = null;
        }
        
        // 重置警告状态
        this.warningShown = false;
        
        // 记录活动，重置定时器
        this.recordActivity();
    }

    // 锁定系统
    lockSystem(reason = '检测到长时间无操作，系统已自动锁定') {
        if (this.isLocked || this.isLockPage()) {
            return;
        }
        
        console.log('系统锁定:', reason);
        this.isLocked = true;
        
        // 保存锁定状态
        this.saveLockState(reason);
        
        // 保存当前页面信息
        sessionStorage.setItem('lockedFrom', window.location.pathname);
        sessionStorage.setItem('lockReason', reason);
        
        // 跳转到锁定页面
        this.redirectToLockPage();
    }

    // 保存锁定状态
    saveLockState(reason) {
        const lockState = {
            isLocked: true,
            reason: reason,
            timestamp: Date.now(),
            lastPage: window.location.pathname
        };
        
        localStorage.setItem('systemLockState', JSON.stringify(lockState));
    }

    // 恢复锁定状态
    restoreLockState() {
        try {
            const lockStateStr = localStorage.getItem('systemLockState');
            if (!lockStateStr) {
                return;
            }
            
            const lockState = JSON.parse(lockStateStr);
            
            // 检查锁定状态是否仍然有效
            const lockAge = Date.now() - lockState.timestamp;
            const maxLockAge = 24 * 60 * 60 * 1000; // 24小时后自动清除锁定状态
            
            if (lockAge > maxLockAge) {
                // 锁定状态过期，清除
                localStorage.removeItem('systemLockState');
                return;
            }
            
            if (lockState.isLocked) {
                console.log('恢复锁定状态:', lockState.reason);
                sessionStorage.setItem('lockReason', lockState.reason);
                this.redirectToLockPage();
            }
        } catch (error) {
            console.error('恢复锁定状态失败:', error);
            localStorage.removeItem('systemLockState');
        }
    }

    // 跳转到锁定页面
    redirectToLockPage() {
        // 清除定时器
        this.clearTimers();
        
        // 停止活动监控
        this.stopMonitoring();
        
        // 跳转到锁定页面
        const lockPageUrl = '/HTML/locked.html';
        
        if (window.location.pathname !== lockPageUrl) {
            window.location.href = lockPageUrl;
        }
    }

    // 停止监控
    stopMonitoring() {
        // 清除定时器
        this.clearTimers();
        
        if (this.lockCheckInterval) {
            clearInterval(this.lockCheckInterval);
            this.lockCheckInterval = null;
        }
        
        if (this.warningCountdownInterval) {
            clearInterval(this.warningCountdownInterval);
            this.warningCountdownInterval = null;
        }
        
        // 移除事件监听器
        this.activityEvents.forEach(event => {
            document.removeEventListener(event, this.recordActivity);
        });
    }

    // 手动锁定
    manualLock(reason = '用户手动锁定系统') {
        this.lockSystem(reason);
    }

    // 解锁系统（由锁定页面调用）
    unlockSystem() {
        console.log('系统已解锁');
        this.isLocked = false;
        
        // 清除锁定状态
        localStorage.removeItem('systemLockState');
        sessionStorage.removeItem('lockedFrom');
        sessionStorage.removeItem('lockReason');
        
        // 重新启动监控
        this.recordActivity();
        this.startLockCheck();
    }

    // 获取剩余时间
    getRemainingTime() {
        const now = Date.now();
        const timeSinceLastActivity = now - this.lastActivity;
        const remaining = Math.max(0, this.lockTimeout - timeSinceLastActivity);
        
        return {
            total: remaining,
            minutes: Math.floor(remaining / 60000),
            seconds: Math.floor((remaining % 60000) / 1000),
            isWarning: remaining <= this.warningTimeout
        };
    }

    // 设置锁定超时时间
    setLockTimeout(minutes) {
        this.lockTimeout = minutes * 60 * 1000;
        this.warningTimeout = Math.min(1 * 60 * 1000, this.lockTimeout / 2);
        
        // 重置定时器
        this.recordActivity();
        
        console.log(`锁定超时时间已设置为 ${minutes} 分钟`);
    }

    // 检查系统状态
    getSystemStatus() {
        return {
            isLocked: this.isLocked,
            lastActivity: this.lastActivity,
            remainingTime: this.getRemainingTime(),
            warningShown: this.warningShown
        };
    }
}

// 创建全局实例
let globalLockSystem;

// 页面加载完成后初始化
document.addEventListener('DOMContentLoaded', function() {
    // 确保不在锁定页面创建实例
    if (!window.location.pathname.includes('locked.html')) {
        globalLockSystem = new GlobalLockSystem();
        
        // 暴露到全局作用域供其他脚本使用
        window.globalLockSystem = globalLockSystem;
        
        console.log('全局锁定系统已初始化');
    }
});

// 导出类供其他模块使用
if (typeof module !== 'undefined' && module.exports) {
    module.exports = GlobalLockSystem;
}