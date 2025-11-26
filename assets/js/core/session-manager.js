/**
 * 会话管理器 - 处理超时机制和会话管理
 * MTSCOS AI Security Module
 */

class SessionManager {
    constructor() {
        this.sessionTimeout = 30 * 60 * 1000; // 30分钟超时
        this.warningTime = 5 * 60 * 1000; // 5分钟警告
        this.checkInterval = 30 * 1000; // 30秒检查一次
        this.lastActivity = Date.now();
        this.sessionTimer = null;
        this.warningTimer = null;
        this.checkTimer = null;
        
        this.init();
    }

    init() {
        this.setupActivityListeners();
        this.startSessionMonitoring();
        this.loadSessionState();
        console.log('[会话管理] 会话管理器已初始化');
    }

    // 设置活动监听器
    setupActivityListeners() {
        const events = [
            'mousedown', 'mousemove', 'keypress', 'scroll', 
            'touchstart', 'click', 'keydown', 'keyup'
        ];

        events.forEach(event => {
            document.addEventListener(event, () => {
                this.updateLastActivity();
            }, true);
        });

        // 页面可见性变化
        document.addEventListener('visibilitychange', () => {
            if (document.hidden) {
                this.pauseMonitoring();
            } else {
                this.resumeMonitoring();
            }
        });

        // 页面获得/失去焦点
        window.addEventListener('focus', () => {
            this.updateLastActivity();
            this.resumeMonitoring();
        });

        window.addEventListener('blur', () => {
            this.pauseMonitoring();
        });
    }

    // 更新最后活动时间
    updateLastActivity() {
        this.lastActivity = Date.now();
        this.saveSessionState();
        
        // 重置定时器
        this.resetTimers();
    }

    // 开始会话监控
    startSessionMonitoring() {
        this.resetTimers();
        
        // 定期检查会话状态
        this.checkTimer = setInterval(() => {
            this.checkSessionStatus();
        }, this.checkInterval);
    }

    // 重置定时器
    resetTimers() {
        // 清除现有定时器
        if (this.sessionTimer) {
            clearTimeout(this.sessionTimer);
        }
        if (this.warningTimer) {
            clearTimeout(this.warningTimer);
        }

        // 设置警告定时器
        this.warningTimer = setTimeout(() => {
            this.showSessionWarning();
        }, this.sessionTimeout - this.warningTime);

        // 设置会话超时定时器
        this.sessionTimer = setTimeout(() => {
            this.handleSessionTimeout();
        }, this.sessionTimeout);
    }

    // 检查会话状态
    checkSessionStatus() {
        const now = Date.now();
        const inactiveTime = now - this.lastActivity;
        
        // 如果超过超时时间，立即处理
        if (inactiveTime >= this.sessionTimeout) {
            this.handleSessionTimeout();
            return;
        }

        // 如果接近警告时间，显示警告
        if (inactiveTime >= this.sessionTimeout - this.warningTime) {
            const remainingTime = this.sessionTimeout - inactiveTime;
            this.updateSessionWarning(remainingTime);
        }

        // 检查会话完整性
        this.validateSessionIntegrity();
    }

    // 显示会话警告
    showSessionWarning() {
        const remainingTime = this.sessionTimeout - (Date.now() - this.lastActivity);
        
        if (remainingTime <= 0) {
            this.handleSessionTimeout();
            return;
        }

        // 创建警告对话框
        this.createWarningDialog(remainingTime);
        
        console.log('[会话警告] 会话即将超时，剩余时间: ' + Math.floor(remainingTime / 1000) + '秒');
    }

    // 创建警告对话框
    createWarningDialog(remainingTime) {
        // 移除现有警告
        const existingWarning = document.getElementById('sessionWarning');
        if (existingWarning) {
            existingWarning.remove();
        }

        const warningDiv = document.createElement('div');
        warningDiv.id = 'sessionWarning';
        warningDiv.style.cssText = `
            position: fixed;
            top: 20px;
            right: 20px;
            background: linear-gradient(135deg, #ff6b6b, #ee5a24);
            color: white;
            padding: 20px;
            border-radius: 10px;
            box-shadow: 0 10px 30px rgba(0,0,0,0.3);
            z-index: 10001;
            max-width: 350px;
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            animation: slideIn 0.3s ease-out;
        `;

        warningDiv.innerHTML = `
            <div style="display: flex; align-items: center; margin-bottom: 10px;">
                <span style="font-size: 24px; margin-right: 10px;">⚠️</span>
                <h3 style="margin: 0; font-size: 16px;">会话即将超时</h3>
            </div>
            <p style="margin: 10px 0; font-size: 14px;">
                您的会话将在 <span id="countdown" style="font-weight: bold; font-size: 18px;">${Math.floor(remainingTime / 1000)}</span> 秒后超时
            </p>
            <div style="display: flex; gap: 10px; margin-top: 15px;">
                <button id="extendSession" style="
                    background: white;
                    color: #ee5a24;
                    border: none;
                    padding: 8px 16px;
                    border-radius: 5px;
                    cursor: pointer;
                    font-weight: bold;
                    flex: 1;
                ">延长会话</button>
                <button id="logoutNow" style="
                    background: transparent;
                    color: white;
                    border: 1px solid white;
                    padding: 8px 16px;
                    border-radius: 5px;
                    cursor: pointer;
                    flex: 1;
                ">立即退出</button>
            </div>
        `;

        // 添加动画样式
        const style = document.createElement('style');
        style.textContent = `
            @keyframes slideIn {
                from { transform: translateX(100%); opacity: 0; }
                to { transform: translateX(0); opacity: 1; }
            }
        `;
        document.head.appendChild(style);

        document.body.appendChild(warningDiv);

        // 设置倒计时更新
        const countdownInterval = setInterval(() => {
            const remaining = this.sessionTimeout - (Date.now() - this.lastActivity);
            const countdownEl = document.getElementById('countdown');
            
            if (countdownEl && remaining > 0) {
                countdownEl.textContent = Math.floor(remaining / 1000);
            } else {
                clearInterval(countdownInterval);
                this.removeWarningDialog();
                this.handleSessionTimeout();
            }
        }, 1000);

        // 绑定按钮事件
        document.getElementById('extendSession').addEventListener('click', () => {
            clearInterval(countdownInterval);
            this.extendSession();
            this.removeWarningDialog();
        });

        document.getElementById('logoutNow').addEventListener('click', () => {
            clearInterval(countdownInterval);
            this.removeWarningDialog();
            this.forceLogout();
        });
    }

    // 更新会话警告
    updateSessionWarning(remainingTime) {
        const countdownEl = document.getElementById('countdown');
        if (countdownEl) {
            countdownEl.textContent = Math.floor(remainingTime / 1000);
        }
    }

    // 移除警告对话框
    removeWarningDialog() {
        const warning = document.getElementById('sessionWarning');
        if (warning) {
            warning.remove();
        }
    }

    // 延长会话
    extendSession() {
        this.updateLastActivity();
        console.log('[会话管理] 会话已延长');
        
        // 显示延长成功提示
        this.showToast('会话已延长30分钟', 'success');
    }

    // 处理会话超时
    handleSessionTimeout() {
        console.log('[会话管理] 会话超时，执行安全锁定');
        
        // 清理定时器
        this.clearTimers();
        
        // 移除警告
        this.removeWarningDialog();
        
        // 记录超时事件到后台
        this.logTimeoutEvent();
        
        // 执行安全锁定
        this.executeSecurityLock();
        
        // 不再显示前台提示，改为后台记录
        // this.showToast('会话已超时，请重新验证身份', 'error');
    }

    // 执行安全锁定
    executeSecurityLock() {
        // 清除会话数据
        this.clearSessionData();
        
        // 重定向到锁定页面
        this.redirectToLockPage();
    }

    // 清除会话数据
    clearSessionData() {
        localStorage.removeItem('security_unlocked');
        localStorage.removeItem('session_token');
        localStorage.removeItem('unlock_time');
        sessionStorage.removeItem('temp_verification');
        
        console.log('[会话管理] 会话数据已清除');
    }

    // 重定向到锁定页面
    redirectToLockPage() {
        const currentPath = window.location.pathname;
        const lockPageUrl = '/HTML/locked.html?redirect=' + encodeURIComponent(currentPath);
        
        window.location.href = lockPageUrl;
    }

    // 强制退出
    forceLogout() {
        console.log('[会话管理] 用户主动退出');
        this.executeSecurityLock();
    }

    // 暂停监控
    pauseMonitoring() {
        if (this.checkTimer) {
            clearInterval(this.checkTimer);
            this.checkTimer = null;
        }
        console.log('[会话管理] 监控已暂停');
    }

    // 恢复监控
    resumeMonitoring() {
        if (!this.checkTimer) {
            this.checkTimer = setInterval(() => {
                this.checkSessionStatus();
            }, this.checkInterval);
        }
        console.log('[会话管理] 监控已恢复');
    }

    // 验证会话完整性
    validateSessionIntegrity() {
        const sessionToken = localStorage.getItem('session_token');
        const unlockTime = localStorage.getItem('unlock_time');
        
        if (!sessionToken || !unlockTime) {
            console.log('[会话管理] 会话数据不完整，执行锁定');
            this.handleSessionTimeout();
            return;
        }

        // 检查时间戳有效性
        const timeDiff = Date.now() - parseInt(unlockTime);
        if (timeDiff > this.sessionTimeout) {
            console.log('[会话管理] 会话时间戳无效，执行锁定');
            this.handleSessionTimeout();
            return;
        }

        // 检查令牌格式
        if (!this.isValidTokenFormat(sessionToken)) {
            console.log('[会话管理] 会话令牌格式无效，执行锁定');
            this.handleSessionTimeout();
            return;
        }
    }

    // 验证令牌格式
    isValidTokenFormat(token) {
        try {
            // 简单的格式验证
            return token && token.length > 20 && /^[A-Za-z0-9+/=]+$/.test(token);
        } catch (e) {
            return false;
        }
    }

    // 保存会话状态
    saveSessionState() {
        const sessionState = {
            lastActivity: this.lastActivity,
            sessionTimeout: this.sessionTimeout,
            timestamp: Date.now()
        };
        
        sessionStorage.setItem('session_state', JSON.stringify(sessionState));
    }

    // 加载会话状态
    loadSessionState() {
        try {
            const stateStr = sessionStorage.getItem('session_state');
            if (stateStr) {
                const state = JSON.parse(stateStr);
                
                // 检查状态是否过期
                if (Date.now() - state.timestamp < this.sessionTimeout) {
                    this.lastActivity = state.lastActivity;
                    console.log('[会话管理] 会话状态已恢复');
                } else {
                    console.log('[会话管理] 会话状态已过期');
                    sessionStorage.removeItem('session_state');
                }
            }
        } catch (e) {
            console.error('[会话管理] 加载会话状态失败:', e);
        }
    }

    // 记录超时事件到后台
    logTimeoutEvent() {
        const timeoutEvent = {
            type: 'session_timeout',
            timestamp: Date.now(),
            userAgent: navigator.userAgent,
            page: window.location.pathname,
            sessionDuration: Date.now() - this.lastActivity,
            ip: this.getClientIP()
        };

        // 保存到本地存储作为后台日志
        this.saveToBackendLog(timeoutEvent);
        
        // 发送到服务器（如果可用）
        this.sendToServer(timeoutEvent);
        
        console.log('[会话管理] 超时事件已记录到后台:', timeoutEvent);
    }

    // 获取客户端IP
    getClientIP() {
        // 尝试从已有数据中获取IP，或返回默认值
        return localStorage.getItem('client_ip') || 'unknown';
    }

    // 保存到后台日志
    saveToBackendLog(event) {
        try {
            const logs = JSON.parse(localStorage.getItem('backend_security_logs') || '[]');
            logs.push(event);
            
            // 保持最近100条记录
            if (logs.length > 100) {
                logs.splice(0, logs.length - 100);
            }
            
            localStorage.setItem('backend_security_logs', JSON.stringify(logs));
        } catch (e) {
            console.error('[会话管理] 保存后台日志失败:', e);
        }
    }

    // 发送到服务器
    sendToServer(event) {
        // 如果有可用的API端点，可以发送到服务器
        try {
            fetch('/api/security/log', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(event)
            }).catch(() => {
                // 静默处理网络错误
                console.log('[会话管理] 服务器日志记录失败，使用本地存储');
            });
        } catch (e) {
            // 静默处理错误
            console.log('[会话管理] 发送日志到服务器失败:', e.message);
        }
    }

    // 获取后台日志（供管理员查看）
    getBackendLogs() {
        try {
            return JSON.parse(localStorage.getItem('backend_security_logs') || '[]');
        } catch (e) {
            return [];
        }
    }

    // 清除后台日志
    clearBackendLogs() {
        localStorage.removeItem('backend_security_logs');
        console.log('[会话管理] 后台日志已清除');
    }

    // 清除定时器
    clearTimers() {
        if (this.sessionTimer) {
            clearTimeout(this.sessionTimer);
            this.sessionTimer = null;
        }
        if (this.warningTimer) {
            clearTimeout(this.warningTimer);
            this.warningTimer = null;
        }
        if (this.checkTimer) {
            clearInterval(this.checkTimer);
            this.checkTimer = null;
        }
    }

    // 显示提示消息
    showToast(message, type = 'info') {
        // 移除现有提示
        const existingToast = document.getElementById('sessionToast');
        if (existingToast) {
            existingToast.remove();
        }

        const toast = document.createElement('div');
        toast.id = 'sessionToast';
        
        const bgColor = type === 'success' ? '#27ae60' : 
                       type === 'error' ? '#e74c3c' : '#3498db';
        
        toast.style.cssText = `
            position: fixed;
            bottom: 20px;
            left: 50%;
            transform: translateX(-50%);
            background: ${bgColor};
            color: white;
            padding: 15px 25px;
            border-radius: 8px;
            box-shadow: 0 5px 15px rgba(0,0,0,0.3);
            z-index: 10002;
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            font-size: 14px;
            animation: fadeInUp 0.3s ease-out;
        `;

        toast.textContent = message;
        
        // 添加动画样式
        if (!document.getElementById('toastAnimation')) {
            const style = document.createElement('style');
            style.id = 'toastAnimation';
            style.textContent = `
                @keyframes fadeInUp {
                    from { transform: translate(-50%, 20px); opacity: 0; }
                    to { transform: translate(-50%, 0); opacity: 1; }
                }
            `;
            document.head.appendChild(style);
        }

        document.body.appendChild(toast);

        // 3秒后自动移除
        setTimeout(() => {
            if (toast.parentNode) {
                toast.remove();
            }
        }, 3000);
    }

    // 获取会话信息
    getSessionInfo() {
        const now = Date.now();
        const inactiveTime = now - this.lastActivity;
        const remainingTime = Math.max(0, this.sessionTimeout - inactiveTime);
        
        return {
            lastActivity: this.lastActivity,
            inactiveTime: inactiveTime,
            remainingTime: remainingTime,
            isActive: remainingTime > 0,
            sessionTimeout: this.sessionTimeout
        };
    }

    // 手动更新会话超时时间
    updateSessionTimeout(newTimeout) {
        this.sessionTimeout = newTimeout;
        this.warningTime = Math.min(5 * 60 * 1000, newTimeout / 6);
        this.resetTimers();
        console.log('[会话管理] 会话超时时间已更新为: ' + (newTimeout / 1000 / 60) + '分钟');
    }

    // 销毁会话管理器
    destroy() {
        this.clearTimers();
        this.removeWarningDialog();
        this.clearSessionData();
        console.log('[会话管理] 会话管理器已销毁');
    }
}

// 导出模块
if (typeof module !== 'undefined' && module.exports) {
    module.exports = SessionManager;
} else {
    window.SessionManager = SessionManager;
}