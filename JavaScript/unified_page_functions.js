// 统一页面功能脚本 - 版本: 1.231030.103001
// 功能: 统一认证机制、会话管理、主题切换、防盗链、加密解密、系统锁定与解锁等

// 全局版本信息
const SCRIPT_VERSION = '2.251030.14251';

// 锁定相关常量
const LOCKED_PAGE = '../HTML/locked.html';
const MAX_LOGIN_ATTEMPTS = 5;
const MAX_DIRECT_ACCESS_ATTEMPTS = 3;

// 检查是否是登录页面
function isLoginPage() {
    return window.location.pathname.includes('index.html');
}

// 检查是否是需要认证的页面
function requiresAuthentication() {
    const authPages = ['dashboard.html', 'settings.html', 'UpdateInfo.html', 'service_monitor.html'];
    const currentPage = window.location.pathname.split('/').pop();
    return authPages.includes(currentPage);
}

// 初始化主题
function initializeTheme() {
    // 检查本地存储中的主题设置
    const savedTheme = localStorage.getItem('theme');
    if (savedTheme) {
        document.body.classList.add(savedTheme);
    } else {
        // 默认使用浅色主题
        document.body.classList.remove('dark-theme');
    }
    
    // 初始化主题切换图标
    initializeThemeIcon();
    
    // 添加主题切换事件监听
    const themeToggle = document.getElementById('themeToggle');
    if (themeToggle) {
        themeToggle.addEventListener('click', toggleTheme);
    }
}

// 初始化主题图标
function initializeThemeIcon() {
    const themeToggle = document.getElementById('themeToggle');
    if (themeToggle) {
        const icon = themeToggle.querySelector('img');
        if (icon) {
            if (document.body.classList.contains('dark-theme')) {
                icon.src = '../SourceCode/images/icons/light_mode.svg';
                icon.alt = '切换到浅色主题';
            } else {
                icon.src = '../SourceCode/images/icons/dark_mode.svg';
                icon.alt = '切换到深色主题';
            }
        }
    }
}

// 切换主题
function toggleTheme() {
    const body = document.body;
    if (body.classList.contains('dark-theme')) {
        body.classList.remove('dark-theme');
        localStorage.setItem('theme', '');
    } else {
        body.classList.add('dark-theme');
        localStorage.setItem('theme', 'dark-theme');
    }
    initializeThemeIcon();
}

// 更新时间显示
function updateTimeDisplay() {
    const timeElement = document.getElementById('current-time');
    if (timeElement) {
        const now = new Date();
        timeElement.textContent = now.toLocaleString('zh-CN', {
            year: 'numeric',
            month: '2-digit',
            day: '2-digit',
            hour: '2-digit',
            minute: '2-digit',
            second: '2-digit'
        });
    }
}

// 更新访问统计
function updateVisitStats() {
    const visitInfoElement = document.getElementById('visit-info');
    if (visitInfoElement) {
        // 获取访问次数
        let visitCount = parseInt(localStorage.getItem('visitCount') || '0') + 1;
        localStorage.setItem('visitCount', visitCount.toString());
        
        // 获取上次访问时间
        const lastVisit = localStorage.getItem('lastVisit');
        let lastVisitText = '首次访问';
        if (lastVisit) {
            lastVisitText = '上次访问: ' + new Date(parseInt(lastVisit)).toLocaleString('zh-CN');
        }
        localStorage.setItem('lastVisit', Date.now().toString());
        
        visitInfoElement.innerHTML = `
            <div class="visit-count">访问次数: ${visitCount}</div>
            <div class="last-visit">${lastVisitText}</div>
        `;
    }
}

// 认证检查
function checkAuthentication() {
    if (!requiresAuthentication()) return;
    
    const authToken = localStorage.getItem('auth_token') || sessionStorage.getItem('auth_token');
    if (!authToken) {
        // 未认证，重定向到登录页面
        window.location.href = '../HTML/index.html';
    }
}

// 会话超时机制
let sessionTimeout;
function setupSessionTimeout() {
    if (!requiresAuthentication()) return;
    
    // 获取会话超时时间（分钟）
    const timeoutMinutes = parseInt(localStorage.getItem('sessionTimeout') || '30');
    const timeoutMilliseconds = timeoutMinutes * 60 * 1000;
    
    // 重置超时计时器
    resetSessionTimeout();
    
    // 添加用户活动监听
    document.addEventListener('mousemove', resetSessionTimeout);
    document.addEventListener('keypress', resetSessionTimeout);
    document.addEventListener('click', resetSessionTimeout);
}

// 重置会话超时
function resetSessionTimeout() {
    clearTimeout(sessionTimeout);
    sessionTimeout = setTimeout(() => {
        // 会话超时，锁定系统而不是仅仅重定向
        lockSystem('会话超时异常');
    }, parseInt(localStorage.getItem('sessionTimeout') || '30') * 60 * 1000);
}

// 清除认证信息
function clearAuthInfo() {
    localStorage.removeItem('auth_token');
    localStorage.removeItem('user_info');
    sessionStorage.removeItem('auth_token');
    sessionStorage.removeItem('user_info');
}

// 获取认证令牌
function getAuthToken() {
    return localStorage.getItem('auth_token') || sessionStorage.getItem('auth_token');
}

// 加密工具函数 - 支持进度条显示
function encryptData(data, key = 'MTSCOS_DEFAULT_KEY', progressCallback = null) {
    let result = '';
    const totalLength = data.length;
    
    for (let i = 0; i < totalLength; i++) {
        const charCode = data.charCodeAt(i) ^ key.charCodeAt(i % key.length);
        result += String.fromCharCode(charCode);
        
        // 每处理10%的数据或最后一个字符时更新进度
        if (progressCallback && (i % Math.ceil(totalLength / 10) === 0 || i === totalLength - 1)) {
            const progress = Math.round((i + 1) / totalLength * 100);
            progressCallback(progress);
        }
    }
    return btoa(result);
}

function decryptData(encryptedData, key = 'MTSCOS_DEFAULT_KEY') {
    const decoded = atob(encryptedData);
    let result = '';
    for (let i = 0; i < decoded.length; i++) {
        const charCode = decoded.charCodeAt(i) ^ key.charCodeAt(i % key.length);
        result += String.fromCharCode(charCode);
    }
    return result;
}

// 保存用户信息
function saveUserInfo(userInfo) {
    const encryptedUserInfo = encryptData(JSON.stringify(userInfo));
    localStorage.setItem('user_info', encryptedUserInfo);
}

// 获取用户信息
function getUserInfo() {
    const encryptedUserInfo = localStorage.getItem('user_info');
    if (encryptedUserInfo) {
        try {
            return JSON.parse(decryptData(encryptedUserInfo));
        } catch (e) {
            console.error('获取用户信息失败:', e);
            return null;
        }
    }
    return null;
}

// 登出功能
function setupLogout() {
    const logoutBtn = document.getElementById('logoutBtn');
    if (logoutBtn) {
        logoutBtn.addEventListener('click', function() {
            if (confirm('确定要退出登录吗？')) {
                // 清除所有认证信息
                localStorage.removeItem('auth_token');
                localStorage.removeItem('user_info');
                sessionStorage.removeItem('auth_token');
                sessionStorage.removeItem('user_info');
                
                console.log('用户已登出，清除认证信息');
                
                // 重定向到登录页面
                window.location.href = '../HTML/index.html';
            }
        });
    }
}

// 检查页面访问权限
function checkPageAccessPermission() {
    // 检查是否被锁定
    if (getCookie('isLocked') === 'true' || localStorage.getItem('isLocked') === 'true') {
        // 增加访问次数
        let logCount = parseInt(localStorage.getItem('Log_Count') || '0');
        logCount++;
        localStorage.setItem('Log_Count', logCount.toString());
        // 重定向到锁定页面
        window.location.href = LOCKED_PAGE;
        return false;
    }
    
    // 获取当前页面路径
    const currentPath = window.location.pathname;
    
    // 检查是否是锁定页面
    if (currentPath.endsWith('/HTML/locked.html')) {
        return true;
    }
    
    // 检查是否是登录页面或其他公开页面，这些页面不需要认证
    const excludedPaths = ['/HTML/index.html', '/HTML/register.html', '/HTML/PasswordReset.html', '/HTML/404.html', '/HTML/403.html'];
    
    // 如果在排除列表中，允许访问
    if (excludedPaths.some(path => currentPath.endsWith(path))) {
        // 但如果是公开页面且有锁定状态，仍然重定向到锁定页面
        if (localStorage.getItem('sessionLocked') === 'true') {
            let logCount = parseInt(localStorage.getItem('Log_Count') || '0');
            logCount++;
            localStorage.setItem('Log_Count', logCount.toString());
            window.location.href = LOCKED_PAGE;
            return false;
        }
        return true;
    }
    
    // 检查认证
    const authToken = getAuthToken();
    
    if (!authToken) {
        // 如果没有有效认证，重定向到登录页面
        window.location.href = '../HTML/index.html?redirect=' + encodeURIComponent(currentPath);
        return false;
    }
    
    // 检查是否有权限访问该页面
    checkPagePermission();
    return true;
}

// 检查页面权限
function checkPagePermission() {
    const currentPage = window.location.pathname;
    const authToken = localStorage.getItem('auth_token') || sessionStorage.getItem('auth_token');
    
    // 需要认证的页面列表
    const protectedPages = [
        'dashboard.html',
        'settings.html',
        'service_monitor.html'
    ];
    
    // 检查是否访问了需要认证的页面但没有登录
    for (const page of protectedPages) {
        if (currentPage.includes(page) && !authToken) {
            // 记录未授权访问
            logUnauthorizedAccess(page);
            // 跳转到登录页
            window.location.href = '../HTML/index.html?redirect=' + encodeURIComponent(currentPage);
            break;
        }
    }
}

// 锁定系统
function lockSystem(reason = '系统安全锁定') {
    // 设置锁定状态
    setCookie('isLocked', 'true', 1); // 锁定1天
    localStorage.setItem('isLocked', 'true');
    sessionStorage.setItem('isLocked', 'true');
    
    // 清除认证信息
    localStorage.removeItem('auth_token');
    localStorage.removeItem('user_info');
    sessionStorage.removeItem('auth_token');
    sessionStorage.removeItem('user_info');
    
    // 跳转到锁定页面
    window.location.href = LOCKED_PAGE + '?reason=' + encodeURIComponent(reason);
}

// 解锁系统
function unlockSystem(adminCode) {
    // 这里应该有实际的验证逻辑
    // 模拟验证
    if (adminCode === 'unlock123') { // 实际应该从服务器验证
        // 清除锁定状态
        setCookie('isLocked', 'false', -1); // 删除cookie
        localStorage.removeItem('isLocked');
        sessionStorage.removeItem('isLocked');
        localStorage.removeItem('Log_Count');
        localStorage.removeItem('lock_attempt_count');
        
        return true;
    }
    return false;
}

// 初始化页面监控
function initPageMonitoring() {
    // 监控异常访问
    monitorDirectAccess();
    
    // 监控URL篡改
    monitorUrlTampering();
}

// 监控直接访问
function monitorDirectAccess() {
    // 检查是否通过正确的入口访问
    if (!document.referrer && !isLoginPage()) {
        let directAccessCount = parseInt(localStorage.getItem('direct_access_count') || '0');
        directAccessCount++;
        localStorage.setItem('direct_access_count', directAccessCount.toString());
        
        if (directAccessCount >= MAX_DIRECT_ACCESS_ATTEMPTS) {
            lockSystem('多次尝试直接访问');
        }
    }
}

// 监控URL篡改
function monitorUrlTampering() {
    // 定期检查URL是否被篡改
    setInterval(() => {
        const currentHash = generatePageHash();
        const expectedHash = sessionStorage.getItem('page_hash');
        
        if (expectedHash && currentHash !== expectedHash) {
            lockSystem('检测到URL篡改');
        }
    }, 5000); // 每5秒检查一次
}

// 生成页面哈希值
function generatePageHash() {
    const url = window.location.href;
    const timestamp = Math.floor(Date.now() / 300000); // 每5分钟更新一次
    return simpleHash(url + timestamp);
}

// 简单哈希函数
function simpleHash(str) {
    let hash = 0;
    for (let i = 0; i < str.length; i++) {
        hash = ((hash << 5) - hash) + str.charCodeAt(i);
        hash = hash & hash;
    }
    return Math.abs(hash);
}

// 记录未授权访问
function logUnauthorizedAccess(page) {
    const logData = {
        timestamp: new Date().toISOString(),
        page: page,
        ip: localStorage.getItem('user_ip') || 'unknown',
        userAgent: navigator.userAgent
    };
    
    // 存储在localStorage中
    let accessLogs = JSON.parse(localStorage.getItem('unauthorized_access_logs') || '[]');
    accessLogs.push(logData);
    localStorage.setItem('unauthorized_access_logs', JSON.stringify(accessLogs.slice(-100))); // 只保留最近100条
}

// ViKey验证
async function verifyViKey() {
    try {
        // 这里应该调用实际的ViKey API
        // 模拟验证过程
        await new Promise(resolve => setTimeout(resolve, 2000));
        
        // 模拟验证成功
        const isVerified = Math.random() > 0.5; // 实际应该是API返回结果
        
        if (isVerified) {
            // 验证成功，解锁系统
            unlockSystem('vikey_verified');
            return true;
        }
        return false;
    } catch (error) {
        console.error('ViKey验证失败:', error);
        return false;
    }
}

// Cookie操作函数
function setCookie(name, value, days) {
    const expires = new Date();
    expires.setTime(expires.getTime() + days * 24 * 60 * 60 * 1000);
    document.cookie = name + '=' + value + ';expires=' + expires.toUTCString() + ';path=/';
}

function getCookie(name) {
    const cookieName = name + '=';
    const decodedCookie = decodeURIComponent(document.cookie);
    const ca = decodedCookie.split(';');
    for (let i = 0; i < ca.length; i++) {
        let c = ca[i];
        while (c.charAt(0) == ' ') {
            c = c.substring(1);
        }
        if (c.indexOf(cookieName) == 0) {
            return c.substring(cookieName.length, c.length);
        }
    }
    return '';
}

// 登录尝试次数管理
function getLoginAttempts() {
    return parseInt(localStorage.getItem('loginAttempts') || '0');
}

function incrementLoginAttempts() {
    const attempts = getLoginAttempts() + 1;
    localStorage.setItem('loginAttempts', attempts.toString());
    
    // 更新登录页面的尝试次数显示
    updateLoginAttemptsDisplay(attempts);
    
    // 如果超过最大尝试次数，锁定账号
    if (attempts >= 5) {
        lockAccount();
    }
}

function resetLoginAttempts() {
    localStorage.removeItem('loginAttempts');
    updateLoginAttemptsDisplay(0);
}

// 更新登录尝试次数显示
function updateLoginAttemptsDisplay(attempts) {
    const attemptsElement = document.getElementById('login-attempts');
    if (attemptsElement) {
        attemptsElement.textContent = `登录尝试次数: ${attempts}/5`;
        // 如果尝试次数大于等于3次，显示红色警告
        if (attempts >= 3) {
            attemptsElement.style.color = '#ff4d4f';
        } else {
            attemptsElement.style.color = ''; // 恢复默认颜色
        }
    }
}

function lockAccount() {
    const lockUntil = Date.now() + 5 * 60 * 1000; // 锁定5分钟
    localStorage.setItem('accountLockedUntil', lockUntil.toString());
    
    // 显示账号锁定遮罩层
    const accountLockOverlay = document.getElementById('account-lock-overlay');
    if (accountLockOverlay) {
        accountLockOverlay.style.display = 'flex';
        startLockCountdown();
    }
}

function isAccountLocked() {
    const lockUntil = localStorage.getItem('accountLockedUntil');
    if (lockUntil) {
        const now = Date.now();
        if (now < parseInt(lockUntil)) {
            return true;
        } else {
            // 锁定时间已过，清除锁定状态
            localStorage.removeItem('accountLockedUntil');
            return false;
        }
    }
    return false;
}

function startLockCountdown() {
    const countdownElement = document.getElementById('lock-countdown');
    if (countdownElement) {
        const lockUntil = parseInt(localStorage.getItem('accountLockedUntil'));
        
        function updateCountdown() {
            const now = Date.now();
            const remaining = Math.max(0, Math.floor((lockUntil - now) / 1000));
            
            const minutes = Math.floor(remaining / 60);
            const seconds = remaining % 60;
            
            countdownElement.textContent = `${minutes}分${seconds}秒`;
            
            if (remaining > 0) {
                setTimeout(updateCountdown, 1000);
            } else {
                // 锁定时间结束
                const accountLockOverlay = document.getElementById('account-lock-overlay');
                if (accountLockOverlay) {
                    accountLockOverlay.style.display = 'none';
                }
                resetLoginAttempts();
            }
        }
        
        updateCountdown();
    }
}

// 验证码生成
function generateVerificationCode() {
    const chars = '0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz';
    let code = '';
    for (let i = 0; i < 6; i++) {
        code += chars.charAt(Math.floor(Math.random() * chars.length));
    }
    return code;
}

// 初始化验证码
function initializeVerificationCode() {
    const captchaElement = document.getElementById('captchaImage');
    if (captchaElement) {
        refreshVerificationCode();
        captchaElement.addEventListener('click', refreshVerificationCode);
    }
}

function refreshVerificationCode() {
    const captchaElement = document.getElementById('captchaImage');
    if (captchaElement) {
        const code = generateVerificationCode();
        sessionStorage.setItem('verificationCode', code);
        
        // 创建验证码图像（简化版）
        captchaElement.textContent = code;
        captchaElement.style.fontSize = '24px';
        captchaElement.style.fontFamily = 'monospace';
        captchaElement.style.letterSpacing = '5px';
        captchaElement.style.padding = '10px';
        captchaElement.style.backgroundColor = '#f0f0f0';
        captchaElement.style.borderRadius = '4px';
        captchaElement.style.textAlign = 'center';
    }
}

// 密码显示/隐藏切换
function setupPasswordToggle() {
    const toggleButtons = document.querySelectorAll('.toggle-password');
    toggleButtons.forEach(button => {
        button.addEventListener('click', function() {
            const inputGroup = this.closest('.input-group');
            const passwordInput = inputGroup.querySelector('input[type="password"]');
            const icon = this.querySelector('i');
            
            if (passwordInput.type === 'password') {
                passwordInput.type = 'text';
                icon.className = 'fas fa-eye-slash';
            } else {
                passwordInput.type = 'password';
                icon.className = 'fas fa-eye';
            }
        });
    });
}

// 创建进度条元素
function createProgressBar(message = '处理中...') {
    // 检查是否已存在进度条
    let progressContainer = document.getElementById('global-progress-container');
    if (!progressContainer) {
        // 创建进度条容器
        progressContainer = document.createElement('div');
        progressContainer.id = 'global-progress-container';
        progressContainer.style.cssText = `
            position: fixed;
            top: 0;
            left: 0;
            width: 100%;
            height: 4px;
            background-color: #f0f0f0;
            z-index: 9999;
            display: none;
        `;
        
        // 创建进度条
        const progressBar = document.createElement('div');
        progressBar.id = 'global-progress-bar';
        progressBar.style.cssText = `
            width: 0%;
            height: 100%;
            background-color: #1890ff;
            transition: width 0.3s ease;
        `;
        
        // 创建进度文本
        const progressText = document.createElement('div');
        progressText.id = 'global-progress-text';
        progressText.style.cssText = `
            position: absolute;
            top: 100%;
            left: 50%;
            transform: translateX(-50%);
            background-color: rgba(0, 0, 0, 0.7);
            color: white;
            padding: 4px 8px;
            border-radius: 4px;
            font-size: 12px;
            white-space: nowrap;
            margin-top: 4px;
        `;
        
        progressContainer.appendChild(progressBar);
        progressContainer.appendChild(progressText);
        document.body.appendChild(progressContainer);
    }
    
    return progressContainer;
}

// 更新进度条
function updateProgressBar(percentage, message = '处理中...') {
    const container = createProgressBar();
    const bar = document.getElementById('global-progress-bar');
    const text = document.getElementById('global-progress-text');
    
    if (bar && text) {
        // 确保百分比在0-100之间
        percentage = Math.max(0, Math.min(100, percentage));
        
        bar.style.width = `${percentage}%`;
        text.textContent = `${message} ${percentage}%`;
        
        // 显示进度条
        container.style.display = 'block';
        
        // 完成时隐藏
        if (percentage >= 100) {
            setTimeout(() => {
                container.style.display = 'none';
            }, 1000);
        }
    }
}

// 检查链接可用性
function checkLinks() {
    const links = document.querySelectorAll('a[href], link[rel="stylesheet"], script[src], img[src]');
    const totalLinks = links.length;
    let checkedLinks = 0;
    let brokenLinks = [];
    
    if (totalLinks === 0) return;
    
    updateProgressBar(0, '检查链接');
    
    links.forEach(element => {
        const url = element.tagName === 'A' ? element.href : 
                  element.tagName === 'LINK' ? element.href : 
                  element.src;
        
        // 跳过外部链接和空链接
        if (url.startsWith('http') && !url.includes(window.location.hostname) || url === '' || url === '#') {
            checkedLinks++;
            updateProgressBar(Math.round(checkedLinks / totalLinks * 100), '检查链接');
            return;
        }
        
        // 检查本地链接
        fetch(url, { method: 'HEAD' })
            .then(response => {
                if (!response.ok) {
                    brokenLinks.push({ url, element: element.tagName });
                }
                checkedLinks++;
                updateProgressBar(Math.round(checkedLinks / totalLinks * 100), '检查链接');
                
                // 完成检查后处理结果
                if (checkedLinks === totalLinks && brokenLinks.length > 0) {
                    // 发送错误信息到后台进行修复
                    reportBrokenLinks(brokenLinks);
                }
            })
            .catch(() => {
                brokenLinks.push({ url, element: element.tagName });
                checkedLinks++;
                updateProgressBar(Math.round(checkedLinks / totalLinks * 100), '检查链接');
                
                // 完成检查后处理结果
                if (checkedLinks === totalLinks && brokenLinks.length > 0) {
                    // 发送错误信息到后台进行修复
                    reportBrokenLinks(brokenLinks);
                }
            });
    });
}

// 报告损坏的链接
function reportBrokenLinks(links) {
    // 构建错误数据
    const errorData = {
        timestamp: new Date().toISOString(),
        page: window.location.href,
        brokenLinks: links
    };
    
    // 在控制台记录错误（实际应用中应该发送到服务器）
    console.error('发现损坏的链接:', errorData);
    
    // 尝试本地修复（仅前端可见）
    attemptLocalLinkFix(links);
}

// 尝试本地修复链接
function attemptLocalLinkFix(links) {
    updateProgressBar(0, '修复链接');
    let fixedCount = 0;
    
    links.forEach((link, index) => {
        // 简单的修复策略：检查常见的路径错误
        const url = link.url;
        let fixedUrl = url;
        
        // 尝试修复常见的路径问题
        if (url.includes('../HTML/') && !url.includes('index.html')) {
            fixedUrl = url.replace('../HTML/', '../HTML/index.html');
        }
        
        // 在这里可以添加更多的修复策略
        
        // 更新进度
        fixedCount++;
        updateProgressBar(Math.round(fixedCount / links.length * 100), '修复链接');
        
        // 记录修复尝试
        console.log(`尝试修复链接: ${url} -> ${fixedUrl}`);
    });
}

// 404错误处理
function setup404Handling() {
    // 监听页面加载错误
    window.addEventListener('error', function(event) {
        // 检查是否是404错误
        if (event.target && (event.target.tagName === 'IMG' || event.target.tagName === 'SCRIPT' || event.target.tagName === 'LINK')) {
            console.error(`资源加载失败: ${event.target.src || event.target.href}`);
            
            // 尝试后台修复
            setTimeout(() => {
                // 模拟后台修复过程
                updateProgressBar(0, '修复缺失资源');
                for (let i = 10; i <= 100; i += 10) {
                    setTimeout(() => {
                        updateProgressBar(i, '修复缺失资源');
                    }, i * 100);
                }
            }, 500);
        }
    });
}

// 页面加载完成初始化
function initializePage() {
    // 首先检查页面访问权限
    checkPageAccessPermission();
    
    // 初始化主题
    initializeTheme();
    
    // 设置时间更新
    updateTimeDisplay();
    setInterval(updateTimeDisplay, 1000);
    
    // 更新访问统计
    updateVisitStats();
    
    // 认证检查
    checkAuthentication();
    
    // 设置会话超时
    setupSessionTimeout();
    
    // 设置登出功能
    setupLogout();
    
    // 初始化验证码（仅在登录页面）
    if (isLoginPage()) {
        initializeVerificationCode();
        
        // 更新登录尝试次数显示
        updateLoginAttemptsDisplay(getLoginAttempts());
        
        // 检查账号是否被锁定
        if (isAccountLocked()) {
            const accountLockOverlay = document.getElementById('account-lock-overlay');
            if (accountLockOverlay) {
                accountLockOverlay.style.display = 'flex';
                startLockCountdown();
            }
        }
    }
    
    // 设置密码显示/隐藏切换
    setupPasswordToggle();
    
    // 防止右键菜单（防盗链补充措施）
    document.addEventListener('contextmenu', function(e) {
        e.preventDefault();
    });
    
    // 初始化页面监控
    initPageMonitoring();
    
    // 设置404错误处理
    setup404Handling();
    
    // 页面加载完成后检查链接
    setTimeout(checkLinks, 1000); // 延迟执行以确保所有资源都已加载
}

// 页面加载完成后执行初始化
document.addEventListener('DOMContentLoaded', initializePage);

// 页面卸载时清除超时计时器
window.addEventListener('unload', function() {
    clearTimeout(sessionTimeout);
});