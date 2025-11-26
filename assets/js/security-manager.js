/**
 * 安全检查脚本
 * 用于检查用户登录状态和访问权限
 */
class SecurityManager {
    constructor() {
        this.sessionTimeout = 30 * 60 * 1000; // 30分钟超时
        this.init();
    }

    init() {
        // 首先检查局域网访问权限
        if (!this.checkLANAccess()) {
            return; // 如果不是局域网访问，停止后续初始化
        }
        
        // 检查当前页面是否为index页面
        const isIndexPage = window.location.pathname.endsWith('index.html') || 
                           window.location.pathname === '/' ||
                           window.location.pathname.endsWith('/');
        
        if (!isIndexPage) {
            this.checkAuthentication();
        }
        
        // 设置会话监控
        this.setupSessionMonitor();
    }

    /**
     * 检查用户认证状态
     */
    checkAuthentication() {
        const sessionId = this.getCookie('sessionId');
        const userInfo = this.getSessionData();
        
        if (!sessionId || !userInfo) {
            this.handleUnauthorizedAccess();
            return false;
        }

        // 检查会话是否过期
        if (this.isSessionExpired()) {
            this.handleSessionExpired();
            return false;
        }

        // 更新最后访问时间
        this.updateLastAccess();
        return true;
    }

    /**
     * 处理未授权访问
     */
    handleUnauthorizedAccess() {
        this.logSecurityEvent('unauthorized_access', {
            page: window.location.pathname,
            referrer: document.referrer,
            userAgent: navigator.userAgent,
            timestamp: new Date().toISOString()
        });

        // 显示提示信息
        this.showSecurityMessage('请先登录后再访问此页面', 'warning');
        
        // 延迟跳转到首页
        setTimeout(() => {
            window.location.href = '/index.html';
        }, 2000);
    }

    /**
     * 处理会话过期
     */
    handleSessionExpired() {
        this.logSecurityEvent('session_expired', {
            page: window.location.pathname,
            timestamp: new Date().toISOString()
        });

        // 清除过期的会话数据
        this.clearSession();
        
        // 记录到后台，不显示前台提示
        this.logToBackend('Session expired for user', {
            page: window.location.pathname,
            timestamp: new Date().toISOString()
        });

        // 直接跳转到首页，不显示过期信息
        window.location.href = '/index.html';
    }

    /**
     * 获取Cookie值
     */
    getCookie(name) {
        const value = `; ${document.cookie}`;
        const parts = value.split(`; ${name}=`);
        if (parts.length === 2) {
            return parts.pop().split(';').shift();
        }
        return null;
    }

    /**
     * 获取会话数据
     */
    getSessionData() {
        try {
            const sessionData = localStorage.getItem('userSession');
            return sessionData ? JSON.parse(sessionData) : null;
        } catch (e) {
            return null;
        }
    }

    /**
     * 检查会话是否过期
     */
    isSessionExpired() {
        const lastAccess = localStorage.getItem('lastAccess');
        if (!lastAccess) return true;
        
        const now = Date.now();
        const lastAccessTime = parseInt(lastAccess);
        return (now - lastAccessTime) > this.sessionTimeout;
    }

    /**
     * 更新最后访问时间
     */
    updateLastAccess() {
        localStorage.setItem('lastAccess', Date.now().toString());
    }

    /**
     * 清除会话
     */
    clearSession() {
        document.cookie = 'sessionId=; expires=Thu, 01 Jan 1970 00:00:00 UTC; path=/;';
        localStorage.removeItem('userSession');
        localStorage.removeItem('lastAccess');
    }

    /**
     * 设置会话监控
     */
    setupSessionMonitor() {
        // 每分钟检查一次会话状态
        setInterval(() => {
            if (this.isSessionExpired()) {
                this.handleSessionExpired();
            }
        }, 60000);

        // 监听页面活动
        ['mousedown', 'mousemove', 'keypress', 'scroll', 'touchstart'].forEach(event => {
            document.addEventListener(event, () => {
                this.updateLastAccess();
            }, true);
        });
    }

    /**
     * 记录安全事件
     */
    logSecurityEvent(eventType, data) {
        const logEntry = {
            type: eventType,
            data: data,
            timestamp: new Date().toISOString()
        };

        // 发送到后端记录
        this.logToBackend(`Security event: ${eventType}`, logEntry);
    }

    /**
     * 记录到后端
     */
    async logToBackend(message, data = {}) {
        try {
            await fetch('/api/logs', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    message: message,
                    data: data,
                    timestamp: new Date().toISOString()
                })
            });
        } catch (error) {
            console.error('Failed to log to backend:', error);
        }
    }

    /**
     * 显示安全消息
     */
    showSecurityMessage(message, type = 'info') {
        // 创建消息元素
        const messageDiv = document.createElement('div');
        messageDiv.style.cssText = `
            position: fixed;
            top: 20px;
            right: 20px;
            background: ${type === 'warning' ? '#ff6b6b' : '#4CAF50'};
            color: white;
            padding: 15px 20px;
            border-radius: 5px;
            z-index: 10000;
            font-family: Arial, sans-serif;
            box-shadow: 0 4px 8px rgba(0,0,0,0.2);
            max-width: 300px;
        `;
        messageDiv.textContent = message;
        
        document.body.appendChild(messageDiv);
        
        // 3秒后自动移除
        setTimeout(() => {
            if (messageDiv.parentNode) {
                messageDiv.parentNode.removeChild(messageDiv);
            }
        }, 3000);
    }

    // 检查局域网访问权限
    checkLANAccess() {
        const clientIP = this.getClientIP();
        
        // 如果是本地访问，允许
        if (this.isLocalAccess(clientIP)) {
            return true;
        }
        
        // 检查是否在局域网范围内
        if (this.isInLAN(clientIP)) {
            return true;
        }
        
        // 非局域网访问，显示404错误
        this.show404Error();
        return false;
    }

    // 获取客户端IP
    getClientIP() {
        // 尝试从多个来源获取IP
        return this.getIPFromStorage() || this.getIPFromHeaders() || 'unknown';
    }

    // 从存储获取IP
    getIPFromStorage() {
        return localStorage.getItem('client_ip') || sessionStorage.getItem('client_ip');
    }

    // 从请求头获取IP（需要服务器端支持）
    getIPFromHeaders() {
        // 这里可以通过API调用获取真实IP
        // 暂时返回空，由服务器端处理
        return null;
    }

    // 检查是否为本地访问
    isLocalAccess(ip) {
        if (!ip || ip === 'unknown') return false;
        
        const localPatterns = [
            /^127\./,           // 127.0.0.1
            /^::1$/,            // IPv6 localhost
            /^localhost$/i,     // localhost
            /^0\.0\.0\.0$/      // 0.0.0.0
        ];
        
        return localPatterns.some(pattern => pattern.test(ip));
    }

    // 检查是否在局域网内
    isInLAN(ip) {
        if (!ip || ip === 'unknown') return false;
        
        // 局域网IP段
        const lanPatterns = [
            /^10\./,                    // 10.0.0.0/8
            /^172\.(1[6-9]|2[0-9]|3[0-1])\./,  // 172.16.0.0/12
            /^192\.168\./,              // 192.168.0.0/16
            /^169\.254\./               // 169.254.0.0/16 (APIPA)
        ];
        
        return lanPatterns.some(pattern => pattern.test(ip));
    }

    // 显示404错误页面
    show404Error() {
        // 创建404错误页面
        const errorHTML = `
        <!DOCTYPE html>
        <html lang="zh-CN">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>404 - 页面未找到</title>
            <style>
                * {
                    margin: 0;
                    padding: 0;
                    box-sizing: border-box;
                }
                
                body {
                    font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                    min-height: 100vh;
                    display: flex;
                    align-items: center;
                    justify-content: center;
                    color: white;
                }
                
                .error-container {
                    text-align: center;
                    max-width: 600px;
                    padding: 40px;
                    background: rgba(255, 255, 255, 0.1);
                    border-radius: 20px;
                    backdrop-filter: blur(10px);
                    box-shadow: 0 20px 40px rgba(0, 0, 0, 0.3);
                }
                
                .error-code {
                    font-size: 120px;
                    font-weight: bold;
                    margin-bottom: 20px;
                    text-shadow: 2px 2px 4px rgba(0, 0, 0, 0.3);
                }
                
                .error-message {
                    font-size: 24px;
                    margin-bottom: 30px;
                    opacity: 0.9;
                }
                
                .error-description {
                    font-size: 16px;
                    line-height: 1.6;
                    margin-bottom: 40px;
                    opacity: 0.8;
                }
                
                .back-button {
                    display: inline-block;
                    padding: 15px 30px;
                    background: rgba(255, 255, 255, 0.2);
                    color: white;
                    text-decoration: none;
                    border-radius: 30px;
                    border: 2px solid rgba(255, 255, 255, 0.3);
                    transition: all 0.3s ease;
                    font-weight: bold;
                }
                
                .back-button:hover {
                    background: rgba(255, 255, 255, 0.3);
                    transform: translateY(-2px);
                    box-shadow: 0 10px 20px rgba(0, 0, 0, 0.2);
                }
                
                .time-display {
                    margin-top: 30px;
                    font-size: 14px;
                    opacity: 0.7;
                    font-style: italic;
                }
            </style>
        </head>
        <body>
            <div class="error-container">
                <div class="error-code">404</div>
                <div class="error-message">页面未找到</div>
                <div class="error-description">
                    抱歉，您访问的页面不存在或您没有权限访问。<br>
                    请检查URL是否正确，或联系管理员获取访问权限。
                </div>
                <a href="/" class="back-button">返回首页</a>
                <div class="time-display" id="timeDisplay"></div>
            </div>
            
            <script>
                // 显示当前时间（局域网外用户无法看到准确时间）
                function updateTime() {
                    const now = new Date();
                    const timeString = now.toLocaleString('zh-CN');
                    document.getElementById('timeDisplay').textContent = '访问时间: ' + timeString;
                }
                
                updateTime();
                setInterval(updateTime, 1000);
                
                // 记录非法访问尝试
                const accessAttempt = {
                    type: 'unauthorized_access',
                    timestamp: Date.now(),
                    userAgent: navigator.userAgent,
                    page: window.location.pathname,
                    referrer: document.referrer
                };
                
                // 保存访问记录
                try {
                    const logs = JSON.parse(localStorage.getItem('security_access_logs') || '[]');
                    logs.push(accessAttempt);
                    localStorage.setItem('security_access_logs', JSON.stringify(logs));
                } catch (e) {
                    console.log('无法保存访问记录');
                }
            </script>
        </body>
        </html>
        `;
        
        // 替换当前页面内容
        document.open();
        document.write(errorHTML);
        document.close();
        
        // 记录非法访问尝试
        this.logUnauthorizedAccess();
    }

    // 记录非法访问
    logUnauthorizedAccess() {
        const accessLog = {
            type: 'lan_access_denied',
            timestamp: Date.now(),
            ip: this.getClientIP(),
            userAgent: navigator.userAgent,
            page: window.location.pathname,
            referrer: document.referrer
        };
        
        console.log('[安全管理] 非法局域网访问已记录:', accessLog);
        
        // 保存到安全日志
        try {
            const logs = JSON.parse(localStorage.getItem('security_access_logs') || '[]');
            logs.push(accessLog);
            
            // 保持最近100条记录
            if (logs.length > 100) {
                logs.splice(0, logs.length - 100);
            }
            
            localStorage.setItem('security_access_logs', JSON.stringify(logs));
        } catch (e) {
            console.error('[安全管理] 保存访问日志失败:', e);
        }
    }

    // 设置客户端IP（由服务器端调用）
    setClientIP(ip) {
        localStorage.setItem('client_ip', ip);
        sessionStorage.setItem('client_ip', ip);
    }
}

// 初始化安全管理器
document.addEventListener('DOMContentLoaded', function() {
    window.securityManager = new SecurityManager();
    
    // 检查IP访问权限
    if (!window.securityManager.checkIPAccess()) {
        window.location.href = '/404.html';
    }
});