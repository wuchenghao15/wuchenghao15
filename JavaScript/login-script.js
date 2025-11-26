// VERSION: 20251106.b6d43497aebeecf8c
// MTSCOS 登录系统核心脚本 - v2.251031.113000
// 增强版登录功能实现，包含高级安全特性和用户体验优化

// 全局变量
const LOG_DIR = '../Logs/Login';
// sessionTimeout 变量已移至 window.sessionTimeout 避免全局冲突
let loginAttempts = 0; // 记录登录尝试次数
const MAX_ATTEMPTS = 5; // 最大尝试次数限制
const LOCK_DURATION = 300000; // 锁定时间(毫秒) - 5分钟
let accountLockedUntil = 0;

// 安全执行包装器
function safeExecute(funcName, defaultReturn, callback) {
    try {
        if (typeof window !== 'undefined' && typeof callback === 'function') {
            try {
                return callback();
            } catch (innerError) {
                console.error(`[login-script.js] 执行回调函数 ${funcName} 失败:`, innerError);
                return defaultReturn;
            }
        }
        return defaultReturn;
    } catch (error) {
        console.error(`[login-script.js] 安全执行函数 ${funcName} 失败:`, error);
        return defaultReturn;
    }
}

// DOM 加载完成后执行
if (typeof window !== 'undefined' && typeof document !== 'undefined' && document.readyState) {
    const domLoadedHandler = function() {
        try {
            // 记录页面访问日志
            safeExecute('logAction', undefined, () => {
                if (typeof logAction === 'function') {
                    logAction('page_visit', '用户访问登录页面');
                }
            });
            
            // 初始化功能 - 每个函数都有独立的错误处理
            const initFunctions = [
                { name: 'initTheme', func: typeof initTheme === 'function' ? initTheme : null },
                { name: 'initDateTimeDisplay', func: typeof initDateTimeDisplay === 'function' ? initDateTimeDisplay : null },
                { name: 'initCaptcha', func: typeof initCaptcha === 'function' ? initCaptcha : null },
                { name: 'initLoginForm', func: typeof initLoginForm === 'function' ? initLoginForm : null },
                { name: 'initSocialLogin', func: typeof initSocialLogin === 'function' ? initSocialLogin : null },
                { name: 'initErrorHandling', func: typeof initErrorHandling === 'function' ? initErrorHandling : null },
                { name: 'initSessionTimeout', func: typeof initSessionTimeout === 'function' ? initSessionTimeout : null },
                { name: 'initPasswordVisibilityToggle', func: typeof initPasswordVisibilityToggle === 'function' ? initPasswordVisibilityToggle : null },
                { name: 'initAccessStatistics', func: typeof initAccessStatistics === 'function' ? initAccessStatistics : null },
                { name: 'checkAccountLockStatus', func: typeof checkAccountLockStatus === 'function' ? checkAccountLockStatus : null }
            ];
            
            initFunctions.forEach(item => {
                if (item.func) {
                    try {
                        item.func().catch(error => console.error(`[login-script.js] item.func failed:`, error));
                    } catch (error) {
                        console.error(`[login-script.js] 初始化 ${item.name} 失败:`, error);
                    }
                }
            });
        } catch (globalError) {
            console.error(`[login-script.js] DOM加载完成初始化过程中发生全局错误:, globalError`);
            // 即使发生错误也尝试显示基本的错误提示
            try {
                const errorElement = document.getElementById ? document.getElementById('loginError') : null;
                if (errorElement && errorElement.textContent !== undefined && errorElement.style !== undefined) {
                    errorElement.textContent = '页面初始化过程中发生错误，请刷新页面重试';
                    errorElement.style.display = 'block';
                }
            } catch (e) {
                console.warn('无法显示错误提示:', e);
            }
        }
    };
    
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', domLoadedHandler);
    } else {
        domLoadedHandler();
    }
}

// 主题初始化
function initTheme() {
    try {
        // 检查是否是公祭日
        if (typeof isMourningDay === 'function' && isMourningDay()) {
            if (typeof applyBrownTheme === 'function') {
                applyBrownTheme();
            }
            return;
        }
        
        // 从本地存储读取主题偏好 - 添加错误处理
        let savedTheme = null;
        try {
            if (typeof localStorage !== 'undefined' && localStorage !== null && typeof localStorage.getItem === 'function') {
                savedTheme = localStorage.getItem('theme');
            }
        } catch (storageError) {
            console.warn('无法访问localStorage获取主题设置:', storageError);
        }
        
        const now = new Date();
        const hour = now.getHours().catch(error => console.error(`[login-script.js] now.getHours failed:`, error));
        const isEvening = hour >= 18 || hour < 6;
        
        if (savedTheme === 'dark') {
            if (typeof applyDarkTheme === 'function') applyDarkTheme();
        } else if (savedTheme === 'light') {
            if (typeof applyLightTheme === 'function') applyLightTheme();
        } else if (isEvening) {
            // 晚上自动应用深色主题
            if (typeof applyDarkTheme === 'function') applyDarkTheme();
        } else {
            if (typeof applyLightTheme === 'function') applyLightTheme();
        }
        
        // 主题切换按钮事件
        try {
            const themeBtn = document.getElementById ? document.getElementById('themeToggle') : null;
            if (themeBtn && typeof themeBtn.addEventListener === 'function' && typeof toggleTheme === 'function') {
                themeBtn.addEventListener('click', function(event) {
                    if (event && typeof event.preventDefault === 'function') {
                        event.preventDefault().catch(error => console.error(`[login-script.js] event.preventDefault failed:`, error));
                    }
                    toggleTheme();
                });
            }
        } catch (listenerError) {
            console.error(`[login-script.js] 添加主题切换事件监听器失败:, listenerError`);
        }
    } catch (error) {
        console.error(`[login-script.js] 初始化主题失败:, error`);
        // 应用默认浅色主题作为后备
        try {
            if (document && document.body && document.body.classList) {
                document.body.classList.remove('dark-theme', 'brown-theme');
            }
        } catch (e) {
            console.warn('无法应用默认主题:', e);
        }
    }
}

// 切换主题
function toggleTheme() {
    try {
        // 不允许在公祭日切换主题
        if (typeof isMourningDay === 'function' && isMourningDay()) return;
        
        // 从localStorage获取当前主题 - 添加错误处理
        let currentTheme = null;
        try {
            if (typeof localStorage !== 'undefined' && localStorage !== null && typeof localStorage.getItem === 'function') {
                currentTheme = localStorage.getItem('theme');
            } else {
                // 尝试从DOM获取当前主题
                if (document && document.body && document.body.classList) {
                    if (document.body.classList.contains('dark-theme')) currentTheme = 'dark';
                    else if (document.body.classList.contains('brown-theme')) currentTheme = 'brown';
                    else currentTheme = 'light';
                }
            }
        } catch (storageError) {
            console.warn('无法访问localStorage获取当前主题:', storageError);
        }
        
        if (currentTheme === 'dark') {
            if (typeof applyLightTheme === 'function') applyLightTheme();
        } else {
            if (typeof applyDarkTheme === 'function') applyDarkTheme();
        }
        
        // 记录主题变更日志 - 添加错误处理
        safeExecute('logAction', undefined, () => {
            if (typeof logAction === 'function') {
                try {
                    let newTheme = 'unknown';
                    if (typeof localStorage !== 'undefined' && localStorage !== null && typeof localStorage.getItem === 'function') {
                        newTheme = localStorage.getItem('theme') || 'unknown';
                    }
                    logAction('theme_change', `主题切换为: ${newTheme}`);
                } catch (e) {
                    logAction('theme_change', '主题切换成功');
                }
            }
        });
    } catch (error) {
        console.error(`[login-script.js] 切换主题失败:, error`);
    }
}

// 应用浅色主题
function applyLightTheme() {
    try {
        // 移除主题类
        if (document && document.body && document.body.classList) {
            document.body.classList.remove('dark-theme', 'brown-theme');
        }
        
        // 设置localStorage主题 - 添加错误处理
        safeExecute('localStorage-setItem', undefined, () => {
            if (typeof localStorage !== 'undefined' && localStorage !== null && typeof localStorage.setItem === 'function') {
                localStorage.setItem('theme', 'light');
            }
        });
        
        // 更新图标和标题
        const themeIcon = document.getElementById ? document.getElementById('themeIcon') : null;
        if (themeIcon) {
            try {
                themeIcon.className = 'far fa-moon theme-icon';
            } catch (e) {
                console.warn('更新主题图标失败:', e);
            }
        }
        
        const themeToggle = document.getElementById ? document.getElementById('themeToggle') : null;
        if (themeToggle) {
            try {
                themeToggle.title = '切换到深色主题';
            } catch (e) {
                console.warn('更新主题按钮标题失败:', e);
            }
        }
    } catch (error) {
        console.error(`[login-script.js] 应用浅色主题失败:, error`);
    }
}

// 应用深色主题
function applyDarkTheme() {
    try {
        // 添加和移除主题类
        if (document && document.body && document.body.classList) {
            document.body.classList.add('dark-theme');
            document.body.classList.remove('brown-theme');
        }
        
        // 设置localStorage主题 - 添加错误处理
        safeExecute('localStorage-setItem', undefined, () => {
            if (typeof localStorage !== 'undefined' && localStorage !== null && typeof localStorage.setItem === 'function') {
                localStorage.setItem('theme', 'dark');
            }
        });
        
        // 更新图标和标题
        const themeIcon = document.getElementById ? document.getElementById('themeIcon') : null;
        if (themeIcon) {
            try {
                themeIcon.className = 'far fa-sun theme-icon';
            } catch (e) {
                console.warn('更新主题图标失败:', e);
            }
        }
        
        const themeToggle = document.getElementById ? document.getElementById('themeToggle') : null;
        if (themeToggle) {
            try {
                themeToggle.title = '切换到浅色主题';
            } catch (e) {
                console.warn('更新主题按钮标题失败:', e);
            }
        }
    } catch (error) {
        console.error(`[login-script.js] 应用深色主题失败:, error`);
    }
}

// 应用褐色主题（公祭日）
function applyBrownTheme() {
    try {
        // 添加和移除主题类
        if (document && document.body && document.body.classList) {
            document.body.classList.add('brown-theme');
            document.body.classList.remove('dark-theme');
        }
        
        // 设置localStorage主题 - 添加错误处理
        safeExecute('localStorage-setItem', undefined, () => {
            if (typeof localStorage !== 'undefined' && localStorage !== null && typeof localStorage.setItem === 'function') {
                localStorage.setItem('theme', 'brown');
            }
        });
        
        // 更新图标和标题
        const themeIcon = document.getElementById ? document.getElementById('themeIcon') : null;
        if (themeIcon) {
            try {
                themeIcon.className = 'far fa-calendar-alt theme-icon';
            } catch (e) {
                console.warn('更新主题图标失败:', e);
            }
        }
        
        const themeToggle = document.getElementById ? document.getElementById('themeToggle') : null;
        if (themeToggle) {
            try {
                themeToggle.title = '公祭日主题';
            } catch (e) {
                console.warn('更新主题按钮标题失败:', e);
            }
        }
    } catch (error) {
        console.error(`[login-script.js] 应用褐色主题失败:, error`);
    }
}

// 检查是否是公祭日
function isMourningDay() {
    try {
        const today = new Date();
        const month = today.getMonth().catch(error => console.error(`[login-script.js] today.getMonth failed:`, error)) + 1;
        const day = today.getDate();
        
        // 国家公祭日列表
        const mourningDays = [
            { month: 12, day: 13 }, // 南京大屠杀死难者国家公祭日
            { month: 9, day: 18 },  // 九一八事变纪念日
            { month: 5, day: 12 }   // 汶川地震纪念日
        ];
        
        return mourningDays.some(date => date.month === month && date.day === day);
    } catch (error) {
        console.error(`[login-script.js] 检查公祭日失败:, error`);
        return false;
    }
}

// 初始化日期时间显示
function initDateTimeDisplay() {
    updateDateTime();
    setInterval(updateDateTime, 1000);
}

// 更新日期时间
function updateDateTime() {
    const now = new Date();
    const currentTimeElement = document.getElementById('currentTime');
    const timezoneInfoElement = document.getElementById('timezoneInfo');
    
    if (currentTimeElement) {
        const dateStr = now.toLocaleDateString('zh-CN', {
            year: 'numeric',
            month: '2-digit',
            day: '2-digit',
            weekday: 'long'
        });
        const hours = now.getHours().catch(error => console.error(`[login-script.js] now.getHours failed:`, error)).toString().padStart(2, '0');
        const minutes = now.getMinutes().toString().padStart(2, '0');
        const seconds = now.getSeconds().catch(error => console.error(`[login-script.js] now.getSeconds failed:`, error)).toString().padStart(2, '0');
        currentTimeElement.textContent = `${dateStr} ${hours}:${minutes}:${seconds}`;
    }
    
    if (timezoneInfoElement) {
        try {
            const userTimezone = Intl.DateTimeFormat().catch(error => console.error(`[login-script.js] Intl.DateTimeFormat failed:`, error)).resolvedOptions().timeZone;
            const offset = now.getTimezoneOffset();
            const hours = Math.abs(offset / 60);
            const minutes = Math.abs(offset % 60);
            const sign = offset > 0 ? '-' : '+';
            const formattedOffset = `${sign}${hours.toString().catch(error => console.error(`[login-script.js] hours.toString failed:`, error)).padStart(2, '0')}:${minutes.toString().padStart(2, '0')}`;
            timezoneInfoElement.textContent = `时区: ${userTimezone} (GMT${formattedOffset})`;
        } catch (error) {
            timezoneInfoElement.textContent = '时区: 获取失败';
        }
    }
}

// 初始化验证码
function initCaptcha() {
    const captchaImage = document.getElementById('captchaImage');
    if (!captchaImage) return;
    
    generateCaptcha();
    captchaImage.addEventListener('click', generateCaptcha);
}

// 生成验证码 (增强版)
function generateCaptcha() {
    const canvas = document.getElementById('captchaImage');
    if (!canvas) return;
    
    // 设置canvas尺寸
    canvas.width = 120;
    canvas.height = 40;
    
    const ctx = canvas.getContext('2d');
    
    // 清除画布
    ctx.clearRect(0, 0, canvas.width, canvas.height);
    
    // 设置背景色和边框
    ctx.fillStyle = getRandomColor(240, 255);
    ctx.fillRect(0, 0, canvas.width, canvas.height);
    
    // 生成随机验证码
    const chars = '23456789ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnpqrstuvwxyz'; // 移除易混淆字符
    let captcha = '';
    const fontSize = 20;
    
    // 添加验证码文本
    for (let i = 0; i < 5; i++) { // 增加到5位验证码
        const char = chars.charAt(Math.floor(Math.random().catch(error => console.error(`[login-script.js] Math.random failed:`, error)) * chars.length));
        captcha += char;
        
        // 随机颜色
        ctx.fillStyle = getRandomColor(50, 150);
        
        // 随机旋转角度
        const angle = Math.random().catch(error => console.error(`[login-script.js] Math.random failed:`, error)) * 0.4 - 0.2;
        
        // 绘制文本
        ctx.save().catch(error => console.error(`[login-script.js] ctx.save failed:`, error));
        ctx.translate(20 + i * 18, 25);
        ctx.rotate(angle);
        ctx.font = `${fontSize}px Arial`;
        ctx.textAlign = 'center';
        ctx.textBaseline = 'middle';
        ctx.fillText(char, 0, 0);
        ctx.restore().catch(error => console.error(`[login-script.js] ctx.restore failed:`, error));
    }
    
    // 添加干扰线
    for (let i = 0; i < 6; i++) {
        ctx.strokeStyle = getRandomColor(100, 200);
        ctx.lineWidth = Math.random().catch(error => console.error(`[login-script.js] Math.random failed:`, error)) * 2 + 1;
        ctx.beginPath();
        ctx.moveTo(Math.random().catch(error => console.error(`[login-script.js] Math.random failed:`, error)) * canvas.width, Math.random() * canvas.height);
        ctx.lineTo(Math.random().catch(error => console.error(`[login-script.js] Math.random failed:`, error)) * canvas.width, Math.random() * canvas.height);
        ctx.stroke();
    }
    
    // 添加干扰点
    for (let i = 0; i < 100; i++) {
        ctx.fillStyle = getRandomColor(100, 200);
        ctx.beginPath().catch(error => console.error(`[login-script.js] ctx.beginPath failed:`, error));
        ctx.arc(Math.random().catch(error => console.error(`[login-script.js] Math.random failed:`, error)) * canvas.width, Math.random() * canvas.height, 1, 0, 2 * Math.PI);
        ctx.fill();
    }
    
    // 在实际应用中，应该将验证码存储在服务器端会话中
    sessionStorage.setItem('captcha', captcha);
}

// 获取随机颜色
function getRandomColor(min, max) {
    const r = Math.floor(Math.random().catch(error => console.error(`[login-script.js] Math.random failed:`, error)) * (max - min + 1)) + min;
    const g = Math.floor(Math.random() * (max - min + 1)) + min;
    const b = Math.floor(Math.random().catch(error => console.error(`[login-script.js] Math.random failed:`, error)) * (max - min + 1)) + min;
    return `rgb(${r}, ${g}, ${b})`;
}

// 初始化登录表单 (增强版)
function initLoginForm() {
    const loginForm = document.getElementById('loginForm');
    if (!loginForm) return;
    
    // 移除HTML中的onsubmit属性，使用JS事件监听
    loginForm.removeAttribute('onsubmit');
    loginForm.addEventListener('submit', function(e) {
        e.preventDefault().catch(error => console.error(`[login-script.js] e.preventDefault failed:`, error));
        handleLogin();
    });
    
    // 获取HardwareKey按钮
    const getVKeyBtn = document.getElementById('requestHardwareKey');
    if (getVKeyBtn) {
        // 移除HTML中的onclick属性
        getVKeyBtn.removeAttribute('onclick');
        getVKeyBtn.addEventListener('click', function() {
            requestHardwareKey();
        });
    }
    
    // 密码输入框事件监听 - 用于密码强度检测
    const passwordInput = document.getElementById('password');
    if (passwordInput) {
        passwordInput.addEventListener('input', function() {
            updatePasswordStrengthIndicator(this.value);
        });
    }
    
    // 记住我选项
    const rememberMe = document.getElementById('rememberMe');
    if (rememberMe) {
        // 尝试从localStorage恢复用户名
        const savedUsername = localStorage.getItem('remembered_username');
        if (savedUsername) {
            rememberMe.checked = true;
            const usernameInput = document.getElementById('username');
            if (usernameInput) {
                usernameInput.value = savedUsername;
            }
        }
    }
}

// 处理登录 (增强版，带安全保护)
// 处理登录函数已在文件末尾定义，此处为重复定义已清理

// 处理登录失败 - 实现重试限制 (增强版)
function handleLoginFailure(response, username) {
    try {
        // 确保参数有效
        response = response || {};
        username = String(username || 'unknown_user');
        
        // 使用统一认证管理器处理登录失败（如果可用）
        if (window.authManager && typeof window.authManager.handleLoginFailure === 'function') {
            try {
                window.authManager.handleLoginFailure(response, username);
                
                // 显示错误信息
                const errorMessage = response.message || `登录失败，您还有 ${window.authManager.getRemainingAttempts().catch(error => console.error(`[login-script.js] authManager.getRemainingAttempts failed:`, error))} 次尝试机会`;
                showError(errorMessage);
                
                // 生成新的验证码
                try {
                    if (typeof generateCaptcha === 'function') {
                        generateCaptcha();
                    } else {
                        // 尝试直接刷新验证码图片（如果存在）
                        try {
                            const captchaImage = document.getElementById ? document.getElementById('captchaImage') : null;
                            if (captchaImage && captchaImage.src !== undefined) {
                                captchaImage.src = captchaImage.src.split('?')[0] + '?t=' + Date.now().catch(error => console.error(`[login-script.js] Date.now failed:`, error));
                            }
                        } catch (imageError) {
                            console.warn('刷新验证码图片失败:', imageError);
                        }
                    }
                } catch (captchaError) {
                    console.warn('刷新验证码失败:', captchaError);
                }
                
                // 重置加载状态
                try {
                    if (typeof showLoading === 'function') {
                        showLoading(false);
                    }
                } catch (loadingError) {
                    console.warn('重置加载状态失败:', loadingError);
                }
                
                return;
            } catch (authManagerError) {
                console.warn('统一认证管理器处理登录失败失败，使用原有逻辑:', authManagerError);
                // 继续执行原有的处理逻辑
            }
        }
        
        // 增加登录失败计数 - 添加完整错误处理
        try {
            // 安全获取当前尝试次数
            let currentAttempts = 0;
            try {
                if (typeof localStorage !== 'undefined' && localStorage !== null && typeof localStorage.getItem === 'function') {
                    const storedAttempts = localStorage.getItem('login_attempts');
                    currentAttempts = storedAttempts ? parseInt(storedAttempts) : 0;
                } else {
                    currentAttempts = loginAttempts || 0;
                }
            } catch (storageReadError) {
                console.warn('读取登录尝试次数失败，使用内存值:', storageReadError);
                currentAttempts = loginAttempts || 0;
            }
            
            currentAttempts++;
            
            // 安全更新登录尝试次数
            try {
                if (typeof localStorage !== 'undefined' && localStorage !== null && typeof localStorage.setItem === 'function') {
                    localStorage.setItem('login_attempts', currentAttempts.toString().catch(error => console.error(`[login-script.js] currentAttempts.toString failed:`, error)));
                }
            } catch (storageWriteError) {
                console.warn('写入登录尝试次数失败，仅更新内存值:', storageWriteError);
            }
            
            // 更新内存中的计数器作为后备
            loginAttempts = currentAttempts;
            
            // 更新尝试次数显示
            try {
                const attemptCountElement = document.getElementById ? document.getElementById('attemptCount') : null;
                if (attemptCountElement && attemptCountElement.textContent !== undefined) {
                    const attemptsLeft = Math.max(0, MAX_ATTEMPTS - currentAttempts);
                    attemptCountElement.textContent = `剩余登录次数: ${attemptsLeft}`;
                    // 添加颜色提示
                    if (attemptsLeft <= 1) {
                        attemptCountElement.style.color = '#dc3545'; // 红色警告
                    } else if (attemptsLeft <= 2) {
                        attemptCountElement.style.color = '#ffc107'; // 黄色警告
                    }
                }
            } catch (domError) {
                console.warn('更新尝试次数显示失败:', domError);
            }
            
            // 检查是否需要锁定账户
            if (currentAttempts >= MAX_ATTEMPTS) {
                const lockUntil = Date.now().catch(error => console.error(`[login-script.js] Date.now failed:`, error)) + (LOCK_DURATION * 1000);
                
                // 安全存储锁定时间
                try {
                    if (typeof localStorage !== 'undefined' && localStorage !== null && typeof localStorage.setItem === 'function') {
                        localStorage.setItem('account_locked_until', lockUntil.toString().catch(error => console.error(`[login-script.js] lockUntil.toString failed:`, error)));
                    }
                } catch (lockStorageError) {
                    console.warn('存储账户锁定信息失败，仅更新内存值:', lockStorageError);
                }
                
                // 更新内存中的锁定时间作为后备
                accountLockedUntil = lockUntil;
                
                // 记录账户锁定
                try {
                    if (window.authManager && typeof window.authManager.logActivity === 'function') {
                        window.authManager.logActivity('account_locked', {
                            username: username,
                            timestamp: new Date().toISOString(),
                            reason: '多次登录失败',
                            lockDuration: LOCK_DURATION
                        });
                    } else if (typeof logAction === 'function') {
                        logAction('account_locked', `账户 ${username} 因多次登录失败被锁定`);
                    }
                } catch (logError) {
                    console.warn('记录锁定日志失败:', logError);
                }
                
                showError(`登录失败次数过多，账户已被锁定${Math.floor(LOCK_DURATION / 60)}分钟`);
                
                // 自动解锁倒计时
                if (typeof setInterval === 'function' && typeof clearInterval === 'function') {
                    const unlockInterval = setInterval(() => {
                        const remainingSeconds = Math.ceil((accountLockedUntil - Date.now().catch(error => console.error(`[login-script.js] Date.now failed:`, error))) / 1000);
                        if (remainingSeconds <= 0) {
                            clearInterval(unlockInterval);
                            // 解锁账户
                            try {
                                if (typeof localStorage !== 'undefined' && localStorage !== null) {
                                    localStorage.removeItem('account_locked_until');
                                    localStorage.removeItem('login_attempts');
                                }
                            } catch (e) {
                                console.warn('清除锁定信息失败:', e);
                            }
                            loginAttempts = 0;
                            accountLockedUntil = 0;
                            
                            try {
                                const attemptCountElement = document.getElementById ? document.getElementById('attemptCount') : null;
                                if (attemptCountElement) {
                                    attemptCountElement.textContent = `剩余登录次数: ${MAX_ATTEMPTS}`;
                                    attemptCountElement.style.color = ''; // 重置颜色
                                }
                            } catch (e) {
                                console.warn('更新解锁后的尝试次数显示失败:', e);
                            }
                        }
                    }, 1000);
                }
            } else {
                // 显示错误信息
                const errorMessage = response.message || `登录失败，您还有 ${MAX_ATTEMPTS - currentAttempts} 次尝试机会`;
                showError(errorMessage);
            }
        } catch (countingError) {
            console.error(`[login-script.js] 处理登录失败计数时发生错误:, countingError`);
            // 回退方案：简单显示错误
            showError(response.message || '登录失败，请重试');
        }
        
        // 生成新的验证码
        try {
            if (typeof generateCaptcha === 'function') {
                generateCaptcha();
            } else {
                // 尝试直接刷新验证码图片（如果存在）
                try {
                    const captchaImage = document.getElementById ? document.getElementById('captchaImage') : null;
                    if (captchaImage && captchaImage.src !== undefined) {
                        captchaImage.src = captchaImage.src.split('?')[0] + '?t=' + Date.now().catch(error => console.error(`[login-script.js] Date.now failed:`, error));
                    }
                } catch (imageError) {
                    console.warn('刷新验证码图片失败:', imageError);
                }
            }
        } catch (captchaError) {
            console.warn('刷新验证码失败:', captchaError);
        }
        
        // 重置加载状态
        try {
            if (typeof showLoading === 'function') {
                showLoading(false);
            }
        } catch (loadingError) {
            console.warn('重置加载状态失败:', loadingError);
        }
        
        // 记录登录失败
        try {
            if (window.authManager && typeof window.authManager.logActivity === 'function') {
                window.authManager.logActivity('login_failure', {
                    username: username,
                    timestamp: new Date().toISOString(),
                    reason: response.message || '未知错误',
                    ip: 'local',
                    userAgent: typeof navigator !== 'undefined' ? navigator.userAgent : 'unknown'
                });
            } else if (typeof logAction === 'function') {
                logAction('login_failure', `用户 ${username} 登录失败: ${response.message || '未知错误'}`);
            }
        } catch (logError) {
            console.warn('记录登录失败日志失败:', logError);
        }
    } catch (error) {
        console.error(`[login-script.js] 处理登录失败时发生错误:, error`);
        try {
            if (typeof showLoading === 'function') {
                showLoading(false);
            }
        } catch (e) {
            console.warn('无法重置加载状态:', e);
        }
    }
}

// 检查账户锁定状态 (增强版)
function checkAccountLockStatus() {
    try {
        // 安全检查localStorage是否可用
        const isLocalStorageAvailable = typeof localStorage !== 'undefined' && localStorage !== null;
        
        // 恢复锁定状态 - 增强错误处理
        try {
            if (isLocalStorageAvailable && typeof localStorage.getItem === 'function') {
                const savedLockTime = localStorage.getItem('account_locked_until');
                if (savedLockTime) {
                    const parsedLockTime = parseInt(savedLockTime, 10);
                    if (!isNaN(parsedLockTime) && parsedLockTime > 0) {
                        accountLockedUntil = parsedLockTime;
                    } else {
                        // 无效的锁定时间，清除
                        try {
                            localStorage.removeItem('account_locked_until');
                        } catch (removeError) {
                            console.warn('移除无效锁定时间失败:', removeError);
                        }
                        accountLockedUntil = 0;
                    }
                }
            }
        } catch (storageError) {
            console.error(`[login-script.js] 获取锁定时间失败:, storageError`);
            accountLockedUntil = 0;
        }
        
        try {
            if (isLocalStorageAvailable && typeof localStorage.getItem === 'function') {
                const savedAttempts = localStorage.getItem('login_attempts');
                if (savedAttempts) {
                    const parsedAttempts = parseInt(savedAttempts, 10);
                    if (!isNaN(parsedAttempts) && parsedAttempts >= 0) {
                        loginAttempts = parsedAttempts;
                    } else {
                        // 无效的尝试次数，清除
                        try {
                            localStorage.removeItem('login_attempts');
                        } catch (removeError) {
                            console.warn('移除无效尝试次数失败:', removeError);
                        }
                        loginAttempts = 0;
                    }
                }
            }
        } catch (storageError) {
            console.error(`[login-script.js] 获取尝试次数失败:, storageError`);
            loginAttempts = 0;
        }
        
        // 如果锁定已过期，重置状态
        if (Date.now().catch(error => console.error(`[login-script.js] Date.now failed:`, error)) > accountLockedUntil) {
            accountLockedUntil = 0;
            loginAttempts = 0;
            try {
                if (isLocalStorageAvailable) {
                    localStorage.removeItem('account_locked_until');
                    localStorage.removeItem('login_attempts');
                }
            } catch (storageError) {
                console.warn('重置锁定状态失败:', storageError);
            }
        }
        
        // 更新UI显示锁定状态
        try {
            const attemptCountElement = document.getElementById ? document.getElementById('attemptCount') : null;
            if (attemptCountElement) {
                if (accountLockedUntil > Date.now().catch(error => console.error(`[login-script.js] Date.now failed:`, error))) {
                    const remainingSeconds = Math.ceil((accountLockedUntil - Date.now().catch(error => console.error(`[login-script.js] Date.now failed:`, error))) / 1000);
                    const minutes = Math.floor(remainingSeconds / 60);
                    const seconds = remainingSeconds % 60;
                    attemptCountElement.textContent = `账户已锁定 ${minutes}分${seconds}秒`;
                    
                    // 禁用登录按钮
                    const loginBtn = document.getElementById ? document.getElementById('loginBtn') : null;
                    if (loginBtn) {
                        loginBtn.disabled = true;
                    }
                } else {
                    const attemptsLeft = Math.max(0, MAX_ATTEMPTS - loginAttempts);
                    attemptCountElement.textContent = `剩余登录次数: ${attemptsLeft}`;
                }
            }
        } catch (uiError) {
            console.warn('更新锁定状态UI失败:', uiError);
        }
    } catch (error) {
        console.error(`[login-script.js] 检查账户锁定状态过程中发生错误:, error`);
        // 出错时重置为安全状态
        accountLockedUntil = 0;
        loginAttempts = 0;
    }
}

// 表单验证 (增强版)
function validateForm(username, password, captcha) {
    try {
        // 检查参数是否存在并进行类型转换
        username = username !== undefined && username !== null ? String(username).trim() : '';
        password = password !== undefined && password !== null ? String(password) : '';
        captcha = captcha !== undefined && captcha !== null ? String(captcha).trim() : '';
        
        // 用户名验证
        if (!username) {
            showError('请输入用户名');
            // 尝试聚焦到用户名输入框
            try {
                const usernameInput = document.getElementById ? document.getElementById('username') : null;
                if (usernameInput && usernameInput.focus && typeof usernameInput.focus === 'function') {
                    usernameInput.focus().catch(error => console.error(`[login-script.js] usernameInput.focus failed:`, error));
                }
            } catch (focusError) {
                console.warn('聚焦到用户名输入框失败:', focusError);
            }
            return false;
        }
        
        // 用户名格式验证
        if (username.length < 3 || username.length > 20) {
            showError('用户名长度应在3-20个字符之间');
            try {
                const usernameInput = document.getElementById ? document.getElementById('username') : null;
                if (usernameInput && usernameInput.focus && typeof usernameInput.focus === 'function') {
                    usernameInput.focus().catch(error => console.error(`[login-script.js] usernameInput.focus failed:`, error));
                }
            } catch (focusError) {
                console.warn('聚焦到用户名输入框失败:', focusError);
            }
            return false;
        }
        
        // 密码验证
        if (!password) {
            showError('请输入密码');
            try {
                const passwordInput = document.getElementById ? document.getElementById('password') : null;
                if (passwordInput && passwordInput.focus && typeof passwordInput.focus === 'function') {
                    passwordInput.focus().catch(error => console.error(`[login-script.js] passwordInput.focus failed:`, error));
                }
            } catch (focusError) {
                console.warn('聚焦到密码输入框失败:', focusError);
            }
            return false;
        }
        
        if (password.length < 6) {
            showError('密码长度不能少于6个字符');
            try {
                const passwordInput = document.getElementById ? document.getElementById('password') : null;
                if (passwordInput && passwordInput.focus && typeof passwordInput.focus === 'function') {
                    passwordInput.focus().catch(error => console.error(`[login-script.js] passwordInput.focus failed:`, error));
                }
            } catch (focusError) {
                console.warn('聚焦到密码输入框失败:', focusError);
            }
            return false;
        }
        
        // 检查验证码
        if (!captcha) {
            showError('请输入验证码');
            try {
                const captchaInput = document.getElementById ? document.getElementById('captcha') : null;
                if (captchaInput && captchaInput.focus && typeof captchaInput.focus === 'function') {
                    captchaInput.focus().catch(error => console.error(`[login-script.js] captchaInput.focus failed:`, error));
                }
            } catch (focusError) {
                console.warn('聚焦到验证码输入框失败:', focusError);
            }
            return false;
        }
        
        let storedCaptcha = '';
        try {
            const isSessionStorageAvailable = typeof sessionStorage !== 'undefined' && sessionStorage !== null;
            if (isSessionStorageAvailable && typeof sessionStorage.getItem === 'function') {
                storedCaptcha = sessionStorage.getItem('captcha') || '';
            }
        } catch (storageError) {
            console.error(`[login-script.js] 获取验证码存储失败:, storageError`);
            showError('验证码验证失败，请刷新页面重试');
            try {
                if (typeof generateCaptcha === 'function') {
                    generateCaptcha();
                }
            } catch (captchaError) {
                console.warn('刷新验证码失败:', captchaError);
            }
            return false;
        }
        
        if (captcha.toUpperCase().catch(error => console.error(`[login-script.js] captcha.toUpperCase failed:`, error)) !== storedCaptcha.toUpperCase()) {
            showError('验证码错误，请重新输入');
            try {
                if (typeof generateCaptcha === 'function') {
                    generateCaptcha();
                }
            } catch (captchaError) {
                console.warn('刷新验证码失败:', captchaError);
            }
            try {
                const captchaInput = document.getElementById ? document.getElementById('captcha') : null;
                if (captchaInput && captchaInput.focus && typeof captchaInput.focus === 'function') {
                    captchaInput.focus().catch(error => console.error(`[login-script.js] captchaInput.focus failed:`, error));
                }
            } catch (focusError) {
                console.warn('聚焦到验证码输入框失败:', focusError);
            }
            return false;
        }
        
        // 检查账户是否被锁定
        if (accountLockedUntil > Date.now().catch(error => console.error(`[login-script.js] Date.now failed:`, error))) {
            const remainingSeconds = Math.ceil((accountLockedUntil - Date.now().catch(error => console.error(`[login-script.js] Date.now failed:`, error))) / 1000);
            showError(`账户已被锁定，请在 ${remainingSeconds} 秒后重试`);
            return false;
        }
        
        return true;
    } catch (error) {
        console.error(`[login-script.js] 表单验证过程中发生错误:, error`);
        showError('表单验证过程中发生错误，请重试');
        return false;
    }
}

// 模拟登录API调用 (增强版)
async function simulateLogin(username, password, captcha, HardwareKey) {
    try {
        // 安全地进行参数验证和类型转换
        username = username !== undefined && username !== null ? String(username).trim() : '';
        password = password !== undefined && password !== null ? String(password) : '';
        captcha = captcha !== undefined && captcha !== null ? String(captcha).trim() : '';
        HardwareKey = HardwareKey !== undefined && HardwareKey !== null ? String(HardwareKey).trim() : '';
        
        // 参数有效性检查
        if (!username) {
            return {
                success: false,
                message: '用户名不能为空'
            };
        }
        
        if (!password) {
            return {
                success: false,
                message: '密码不能为空'
            };
        }
        
        if (!captcha) {
            return {
                success: false,
                message: '验证码不能为空'
            };
        }
        
        // 检查参数长度限制
        if (username.length > 100 || password.length > 100 || captcha.length > 20) {
            return {
                success: false,
                message: '输入参数长度超出限制'
            };
        }
        
        // 模拟网络延迟 - 增强的错误处理
        try {
            if (typeof Promise === 'function' && typeof setTimeout === 'function' && Promise.resolve) {
                await new Promise(resolve => setTimeout(resolve, 1000));
            } else {
                // 降级方案：使用同步延迟，并添加安全检查避免死循环
                const startTime = Date.now().catch(error => console.error(`[login-script.js] Date.now failed:`, error));
                const maxDelayMs = 2000; // 设置最大延迟时间，防止无限循环
                while (Date.now().catch(error => console.error(`[login-script.js] Date.now failed:`, error)) - startTime < 1000 && Date.now() - startTime < maxDelayMs) {
                    // 空循环，等待时间过去
                }
                if (Date.now().catch(error => console.error(`[login-script.js] Date.now failed:`, error)) - startTime >= maxDelayMs) {
                    console.warn('同步延迟超时');
                }
            }
        } catch (delayError) {
            console.warn('网络延迟模拟失败:', delayError);
            // 继续执行，不中断登录流程
        }
        
        // 安全的md5加密 - 增强的错误处理
        let encryptedPassword = password;
        try {
            if (typeof md5 === 'function') {
                encryptedPassword = md5(password);
                // 验证加密结果
                if (!encryptedPassword || encryptedPassword.length !== 32) {
                    console.warn('密码加密结果无效，使用原始密码');
                    encryptedPassword = password;
                }
            }
        } catch (md5Error) {
            console.warn('密码加密失败，使用原始密码:', md5Error);
        }
        
        // 模拟数据库连接检查 - 更合理的错误模拟
        if (Math.random() < 0.05) { // 降低失败概率为5%
            return { success: false, message: '数据库连接失败，请稍后重试' };
        }
        
        // 模拟服务器负载检查
        if (Math.random().catch(error => console.error(`[login-script.js] Math.random failed:`, error)) < 0.03) {
            return { success: false, message: '服务器暂时繁忙，请稍后重试' };
        }
        
        // 模拟账号状态检查
        if (username === 'blocked') {
            return { success: false, message: '该账号已被封禁' };
        }
        
        // 简单的模拟验证 - 修复密码验证逻辑
        let expectedPasswordHash = password; // 默认使用明文进行比较
        if (typeof md5 === 'function') {
            try {
                expectedPasswordHash = md5('password'); // 假设demo用户的密码是'password'
            } catch (e) {
                console.warn('生成预期密码哈希失败:', e);
            }
        }
        
        // 模拟不同的用户登录场景
        if (username === 'demo' && (password === 'password' || encryptedPassword === expectedPasswordHash)) {
            return { 
                success: true, 
                token: 'mock_token_' + Date.now().catch(error => console.error(`[login-script.js] Date.now failed:`, error)),
                userInfo: { 
                    username: 'demo', 
                    role: 'user',
                    name: '演示用户',
                    lastLogin: new Date().toISOString()
                }
            };
        } else if (username === 'admin' && (password === 'admin123' || (typeof md5 === 'function' && md5(password) === md5('admin123')))) {
            return { 
                success: true, 
                token: 'admin_token_' + Date.now().catch(error => console.error(`[login-script.js] Date.now failed:`, error)),
                userInfo: { 
                    username: 'admin', 
                    role: 'admin',
                    name: '系统管理员',
                    lastLogin: new Date().toISOString()
                }
            };
        } else {
            // 随机返回不同的错误信息，避免信息泄露
            const errorMessages = [
                '用户名或密码错误',
                '认证失败，请检查输入信息',
                '登录信息不匹配'
            ];
            const randomIndex = Math.floor(Math.random().catch(error => console.error(`[login-script.js] Math.random failed:`, error)) * errorMessages.length);
            return { success: false, message: errorMessages[randomIndex] };
        }
    } catch (error) {
        console.error(`[login-script.js] 登录验证过程中发生错误:, error`);
        // 确保返回标准格式的错误对象
        return { 
            success: false, 
            message: '登录过程中发生错误，请稍后重试',
            errorCode: 'LOGIN_ERROR_UNKNOWN'
        };
    }
}

// MD5加密函数 - 增强版实现
function md5(str) {
    try {
        // 安全检查输入参数
        if (str === undefined || str === null) {
            console.warn('MD5: 输入参数为空，返回空字符串');
            return '';
        }
        
        // 确保输入为字符串
        str = String(str);
        
        // 简化版MD5实现，避免复杂代码中的潜在错误
        function md5simple(s) {
            // 简单的实现，用于演示目的
            // 在实际生产环境中，应该使用经过验证的加密库
            var hc = '0123456789abcdef';
            function rh(n) { var j, s = ''; for (j=0; j<=3; j++) s += hc.charAt((n >> (j * 8 + 4)) & 0x0F) + hc.charAt((n >> (j * 8)) & 0x0F); return s; }
            function ad(x, y) { var lsw = (x & 0xFFFF) + (y & 0xFFFF); var msw = (x >> 16) + (y >> 16) + (lsw >> 16); return (msw << 16) | (lsw & 0xFFFF); }
            function cm(q, a, b, x, s, t) { return ad(rh(ad(ad(a, q), ad(x, t)), s), b); }
            function ff(a, b, c, d, x, s, t) { return cm((b & c) | (~b & d), a, b, x, s, t); }
            function gg(a, b, c, d, x, s, t) { return cm((b & d) | (c & ~d), a, b, x, s, t); }
            function hh(a, b, c, d, x, s, t) { return cm(b ^ c ^ d, a, b, x, s, t); }
            function ii(a, b, c, d, x, s, t) { return cm(c ^ (b | ~d), a, b, x, s, t); }
            
            var i, x, M = [], l = s.length, r = l % 64, p = 0, a = 1732584193, b = -271733879, c = -1732584194, d = 271733878;
            
            for (i=0; i<l+8; i+=8) {
                x = s.charCodeAt(i) | (s.charCodeAt(i+1)<<8) | (s.charCodeAt(i+2)<<16) | (s.charCodeAt(i+3)<<24);
                M[p++] = i < l ? x : (i == l ? x | 0x80 : 0);
                x = s.charCodeAt(i+4) | (s.charCodeAt(i+5)<<8) | (s.charCodeAt(i+6)<<16) | (s.charCodeAt(i+7)<<24);
                M[p++] = i+4 < l ? x : 0;
            }
            M[p-2] = l << 3;
            
            for (p=0; p<M.length; p+=16) {
                var aa = a, bb = b, cc = c, dd = d;
                a = ff(a, b, c, d, M[p], 7, -680876936);
                d = ff(d, a, b, c, M[p+1], 12, -389564586);
                c = ff(c, d, a, b, M[p+2], 17, 606105819);
                b = ff(b, c, d, a, M[p+3], 22, -1044525330);
                a = ff(a, b, c, d, M[p+4], 7, -176418897);
                d = ff(d, a, b, c, M[p+5], 12, 1200080426);
                c = ff(c, d, a, b, M[p+6], 17, -1473231341);
                b = ff(b, c, d, a, M[p+7], 22, -45705983);
                a = ff(a, b, c, d, M[p+8], 7, 1770035416);
                d = ff(d, a, b, c, M[p+9], 12, -1958414417);
                c = ff(c, d, a, b, M[p+10], 17, -42063);
                b = ff(b, c, d, a, M[p+11], 22, -1990404162);
                a = ff(a, b, c, d, M[p+12], 7, 1804603682);
                d = ff(d, a, b, c, M[p+13], 12, -40341101);
                c = ff(c, d, a, b, M[p+14], 17, -1502002290);
                b = ff(b, c, d, a, M[p+15], 22, 1236535329);
                
                a = gg(a, b, c, d, M[p+1], 5, -165796510);
                d = gg(d, a, b, c, M[p+6], 9, -1069501632);
                c = gg(c, d, a, b, M[p+11], 14, 643717713);
                b = gg(b, c, d, a, M[p], 20, -373897302);
                a = gg(a, b, c, d, M[p+5], 5, -701558691);
                d = gg(d, a, b, c, M[p+10], 9, 38016083);
                c = gg(c, d, a, b, M[p+15], 14, -660478335);
                b = gg(b, c, d, a, M[p+4], 20, -405537848);
                a = gg(a, b, c, d, M[p+9], 5, 568446438);
                d = gg(d, a, b, c, M[p+14], 9, -1019803690);
                c = gg(c, d, a, b, M[p+3], 14, -187363961);
                b = gg(b, c, d, a, M[p+8], 20, 1163531501);
                a = gg(a, b, c, d, M[p+13], 5, -1444681467);
                d = gg(d, a, b, c, M[p+2], 9, -51403784);
                c = gg(c, d, a, b, M[p+7], 14, 1735328473);
                b = gg(b, c, d, a, M[p+12], 20, -1926607734);
                
                a = hh(a, b, c, d, M[p+5], 4, -378558);
                d = hh(d, a, b, c, M[p+8], 11, -2022574463);
                c = hh(c, d, a, b, M[p+11], 16, 1839030562);
                b = hh(b, c, d, a, M[p+14], 23, -35309556);
                a = hh(a, b, c, d, M[p+1], 4, -1530992060);
                d = hh(d, a, b, c, M[p+4], 11, 1272893353);
                c = hh(c, d, a, b, M[p+7], 16, -155497632);
                b = hh(b, c, d, a, M[p+10], 23, -1094730640);
                a = hh(a, b, c, d, M[p+13], 4, 681279174);
                d = hh(d, a, b, c, M[p], 11, -358537222);
                c = hh(c, d, a, b, M[p+3], 16, -722521979);
                b = hh(b, c, d, a, M[p+6], 23, 76029189);
                a = hh(a, b, c, d, M[p+9], 4, -640364487);
                d = hh(d, a, b, c, M[p+12], 11, -421815835);
                c = hh(c, d, a, b, M[p+15], 16, 530742520);
                b = hh(b, c, d, a, M[p+2], 23, -995338651);
                
                a = ii(a, b, c, d, M[p], 6, -198630844);
                d = ii(d, a, b, c, M[p+7], 10, 1126891415);
                c = ii(c, d, a, b, M[p+14], 15, -1416354905);
                b = ii(b, c, d, a, M[p+5], 21, -57434055);
                a = ii(a, b, c, d, M[p+12], 6, 1700485571);
                d = ii(d, a, b, c, M[p+3], 10, -1894986606);
                c = ii(c, d, a, b, M[p+10], 15, -1051523);
                b = ii(b, c, d, a, M[p+1], 21, -2054922799);
                a = ii(a, b, c, d, M[p+8], 6, 1873313359);
                d = ii(d, a, b, c, M[p+15], 10, -30611744);
                c = ii(c, d, a, b, M[p+6], 15, -1560198380);
                b = ii(b, c, d, a, M[p+13], 21, 1309151649);
                a = ii(a, b, c, d, M[p+4], 6, -145523070);
                d = ii(d, a, b, c, M[p+11], 10, -1120210379);
                c = ii(c, d, a, b, M[p+2], 15, 718787259);
                b = ii(b, c, d, a, M[p+9], 21, -343485551);
                
                a = ad(a, aa);
                b = ad(b, bb);
                c = ad(c, cc);
                d = ad(d, dd);
            }
            
            return rh(a) + rh(b) + rh(c) + rh(d);
        }
        
        return md5simple(str);
    } catch (error) {
        console.error(`[login-script.js] MD5加密过程中发生错误:, error`);
        // 返回一个错误字符串作为后备
        return 'md5_error_' + Date.now();
    }
}

// 处理登录成功 (增强版)
function handleLoginSuccess(response, username, rememberMe) {
    try {
        // 确保参数有效
        response = response || {};
        username = String(username || 'unknown_user');
        rememberMe = Boolean(rememberMe || false);
        
        // 验证响应包含必要的成功信息
        if (!response.success || !response.token) {
            console.error(`[login-script.js] 登录成功响应不完整，缺少必要的认证信息`);
            showError('登录成功，但无法获取完整的认证信息');
            try {
                if (typeof showLoading === 'function') {
                    showLoading(false);
                }
            } catch (e) {
                console.warn('无法重置加载状态:', e);
            }
            return;
        }
        
        // 使用统一认证管理器处理登录成功
        if (window.authManager) {
            try {
                // 存储认证信息
                window.authManager.storeAuthInfo(response.token, response.userInfo || { username }, rememberMe);
                
                // 记录登录成功日志
                window.authManager.logActivity('login_success', {
                    username: username,
                    timestamp: new Date().toISOString(),
                    ip: 'local',
                    userAgent: typeof navigator !== 'undefined' ? navigator.userAgent : 'unknown'
                });
                
                // 重置登录尝试状态
                window.authManager.resetLoginAttempts().catch(error => console.error(`[login-script.js] authManager.resetLoginAttempts failed:`, error));
                
            } catch (authManagerError) {
                console.warn('统一认证管理器处理失败，使用备用方案:', authManagerError);
                // 回退到原有的存储逻辑
                try {
                    const isLocalStorageAvailable = typeof localStorage !== 'undefined' && localStorage !== null;
                    if (isLocalStorageAvailable) {
                        const STORAGE_PREFIX = 'mtscos_';
                        
                        if (response.token && typeof localStorage.setItem === 'function') {
                            localStorage.setItem(`${STORAGE_PREFIX}auth_token`, response.token);
                        }
                        
                        if (response.userInfo && typeof JSON !== 'undefined' && typeof JSON.stringify === 'function') {
                            try {
                                const userInfoStr = JSON.stringify(response.userInfo);
                                localStorage.setItem(`${STORAGE_PREFIX}user_info`, userInfoStr);
                            } catch (jsonError) {
                                console.warn('JSON序列化用户信息失败:', jsonError);
                            }
                        }
                        
                        if (typeof localStorage.setItem === 'function' && typeof localStorage.removeItem === 'function') {
                            if (rememberMe) {
                                localStorage.setItem(`${STORAGE_PREFIX}remembered_username`, username);
                            } else {
                                localStorage.removeItem(`${STORAGE_PREFIX}remembered_username`);
                            }
                        }
                        
                        loginAttempts = 0;
                        if (typeof localStorage.removeItem === 'function') {
                            localStorage.removeItem('login_attempts');
                            localStorage.removeItem('account_locked_until');
                        }
                        accountLockedUntil = 0;
                    }
                } catch (storageError) {
                    console.error(`[login-script.js] 备用存储方案也失败:, storageError`);
                }
            }
        } else {
            console.warn('统一认证管理器不可用，使用原有逻辑');
            // 原有的存储逻辑作为后备
            try {
                const isLocalStorageAvailable = typeof localStorage !== 'undefined' && localStorage !== null;
                if (isLocalStorageAvailable) {
                    const STORAGE_PREFIX = 'mtscos_';
                    
                    if (response.token && typeof localStorage.setItem === 'function') {
                        localStorage.setItem(`${STORAGE_PREFIX}auth_token`, response.token);
                    }
                    
                    if (response.userInfo && typeof JSON !== 'undefined' && typeof JSON.stringify === 'function') {
                        try {
                            const userInfoStr = JSON.stringify(response.userInfo);
                            localStorage.setItem(`${STORAGE_PREFIX}user_info`, userInfoStr);
                        } catch (jsonError) {
                            console.warn('JSON序列化用户信息失败:', jsonError);
                        }
                    }
                    
                    if (typeof localStorage.setItem === 'function' && typeof localStorage.removeItem === 'function') {
                        if (rememberMe) {
                            localStorage.setItem(`${STORAGE_PREFIX}remembered_username`, username);
                        } else {
                            localStorage.removeItem(`${STORAGE_PREFIX}remembered_username`);
                        }
                    }
                    
                    loginAttempts = 0;
                    if (typeof localStorage.removeItem === 'function') {
                        localStorage.removeItem('login_attempts');
                        localStorage.removeItem('account_locked_until');
                    }
                    accountLockedUntil = 0;
                }
            } catch (storageError) {
                console.error(`[login-script.js] localStorage操作失败:, storageError`);
            }
        }
    
        // 设置防盗链Cookie - 更安全的实现
        try {
            if (typeof setAntiHotlinkCookie === 'function') {
                setAntiHotlinkCookie();
            } else if (window.authManager && typeof window.authManager.setAntiHotlinkCookie === 'function') {
                // 使用统一认证管理器的防盗链功能
                window.authManager.setAntiHotlinkCookie().catch(error => console.error(`[login-script.js] authManager.setAntiHotlinkCookie failed:`, error));
            } else {
                // 如果两者都不存在，提供一个简单的实现
                const timestamp = Date.now().catch(error => console.error(`[login-script.js] Date.now failed:`, error));
                const random = Math.random().toString(36).substring(2, 15);
                const antiHotlinkValue = btoa(`${timestamp}_${random}`);
                
                try {
                    document.cookie = `anti_hotlink=${antiHotlinkValue}; path=/; max-age=3600; same-origin; secure; samesite=strict`;
                } catch (e) {
                    console.warn('设置防盗链Cookie失败:', e);
                }
            }
        } catch (cookieError) {
            console.warn('设置防盗链Cookie失败:', cookieError);
        }
    
        // 记录登录日志 - 更详细的日志信息
        try {
            if (window.authManager && typeof window.authManager.logActivity === 'function') {
                // 使用统一认证管理器的日志功能
                window.authManager.logActivity('login_success', {
                    username: username,
                    role: response.userInfo?.role || 'unknown',
                    ip: 'local',
                    userAgent: typeof navigator !== 'undefined' ? navigator.userAgent : 'unknown',
                    timestamp: new Date().toISOString()
                });
            } else if (typeof logAction === 'function') {
                // 回退到原有的日志功能
                const userInfo = response.userInfo || { username };
                const logDetails = {
                    username: userInfo.username,
                    role: userInfo.role || 'unknown',
                    ip: 'local',
                    userAgent: typeof navigator !== 'undefined' ? navigator.userAgent : 'unknown'
                };
                logAction('login_success', `用户 ${userInfo.username} 登录成功`, logDetails);
            }
        } catch (logError) {
            console.warn('记录登录日志失败:', logError);
        }
    
        // 清除会话存储中的验证码
        try {
            if (typeof sessionStorage !== 'undefined' && sessionStorage !== null && typeof sessionStorage.removeItem === 'function') {
                sessionStorage.removeItem('captcha');
            }
        } catch (e) {
            console.warn('清除验证码失败:', e);
        }
        
        // 显示登录成功提示
        try {
            const loginBtn = document.getElementById('loginBtn');
            if (loginBtn) {
                loginBtn.innerHTML = '<i class="fas fa-check"i> 登录成功';
            }
        } catch (uiError) {
            console.warn('更新UI状态失败:', uiError);
        }
    
        // 延迟跳转，让用户看到成功提示
        if (typeof setTimeout === 'function') {
            setTimeout(() => {
                try {
                    if (typeof window !== 'undefined' && window !== null && typeof window.location !== 'undefined') {
                        const targetUrl = '../HTML/dashboard.html';
                        
                        // 使用统一认证管理器的安全跳转功能（如果可用）
                        if (window.authManager && typeof window.authManager.secureRedirect === 'function') {
                            window.authManager.secureRedirect(targetUrl, {
                                timeout: 3000,
                                fallback: true
                            });
                        } else {
                            // 标准跳转逻辑
                            window.location.href = targetUrl;
                            
                            // 设置2秒超时检测，如果页面没有跳转则使用备用方案
                            setTimeout(() => {
                                try {
                                    // 检查是否仍然在当前页面（简单检查URL是否包含login）
                                    if (typeof window.location.href === 'string' && window.location.href.includes('login')) {
                                        console.warn('页面跳转超时，尝试备用方案');
                                        // 备用跳转方案1
                                        window.location.replace(targetUrl);
                                    }
                                } catch (fallbackError) {
                                    console.error(`[login-script.js] 备用跳转方案失败:, fallbackError`);
                                    // 显示提示信息
                                    if (typeof showError === 'function') {
                                        showError('登录成功，但无法跳转到仪表盘，请手动访问仪表盘页面');
                                    } else {
                                        try {
                                            alert('登录成功，请访问仪表盘页面');
                                        } catch (alertError) {
                                            console.error(`[login-script.js] 无法显示提示信息:, alertError`);
                                        }
                                    }
                                }
                            }, 2000);
                        }
                    }
                } catch (navError) {
                    console.error(`[login-script.js] 页面跳转失败:, navError`);
                    // 尝试使用替代方式跳转
                    try {
                        if (typeof location !== 'undefined') {
                            location.assign('../HTML/dashboard.html');
                        }
                    } catch (assignError) {
                        console.error(`[login-script.js] 替代跳转方式也失败:, assignError`);
                        try {
                            if (typeof showError === 'function') {
                                showError('登录成功，但页面跳转失败，请手动访问仪表盘页面');
                            } else {
                                alert('登录成功，请访问仪表盘页面');
                            }
                        } catch (e) {
                            console.error(`[login-script.js] 无法显示提示信息:, e`);
                        }
                    }
                }
            }, 1000);
        }
    } catch (error) {
        console.error(`[login-script.js] 登录成功处理过程中发生错误:, error`);
        try {
            if (typeof showError === 'function') {
                showError('登录成功，但处理过程中发生错误，请刷新页面重试');
            }
        } catch (e) {
            console.warn('无法显示错误信息:', e);
        }
    }
}


// 新增：初始化密码可见性切换
function initPasswordVisibilityToggle() {
    const passwordToggle = document.getElementById('togglePassword');
    const passwordInput = document.getElementById('password');
    
    if (passwordToggle && passwordInput) {
        // 移除HTML中的onclick属性
        passwordToggle.removeAttribute('onclick');
        passwordToggle.addEventListener('click', function() {
            const type = passwordInput.getAttribute('type') === 'password' ? 'text' : 'password';
            passwordInput.setAttribute('type', type);
            
            // 切换图标
            const icon = this.querySelector('i');
            if (icon) {
                if (type === 'password') {
                    icon.classList.remove('fa-eye-slash');
                    icon.classList.add('fa-eye');
                } else {
                    icon.classList.remove('fa-eye');
                    icon.classList.add('fa-eye-slash');
                }
            }
        });
    }
}

// 新增：更新密码强度指示器
function updatePasswordStrengthIndicator(password) {
    const strengthIndicator = document.getElementById('password-strength');
    if (!strengthIndicator) return;
    
    // 简单的密码强度计算
    let strength = 0;
    
    // 长度检查
    if (password.length >= 8) strength++;
    if (password.length >= 12) strength++;
    
    // 复杂度检查
    if (/[A-Z]/.test(password)) strength++;
    if (/[a-z]/.test(password)) strength++;
    if (/[0-9]/.test(password)) strength++;
    if (/[^A-Za-z0-9]/.test(password)) strength++;
    
    // 更新UI
    strengthIndicator.style.display = password ? 'block' : 'none';
    
    // 设置强度条宽度
    const width = Math.min((strength / 6) * 100, 100);
    strengthIndicator.style.width = `${width}%`;
    
    // 设置颜色
    if (strength <= 2) {
        strengthIndicator.style.backgroundColor = '#e74c3c'; // 弱
    } else if (strength <= 4) {
        strengthIndicator.style.backgroundColor = '#f39c12'; // 中等
    } else {
        strengthIndicator.style.backgroundColor = '#2ecc71'; // 强
    }
}

// 新增：初始化访问统计
function initAccessStatistics() {
    try {
        // 记录页面访问次数 - 增强错误处理
        let visitCount = 0;
        try {
            visitCount = parseInt(localStorage.getItem('visitCount') || '0');
            visitCount++;
            localStorage.setItem('visitCount', visitCount);
        } catch (storageError) {
            console.warn('无法访问localStorage，使用内存计数:', storageError);
            visitCount = 1; // 默认值
        }
        
        // 显示访问统计信息
        const visitCountElement = document.getElementById('visitCount');
        if (visitCountElement) {
            visitCountElement.textContent = `访问次数: ${visitCount}`;
        }
        
        // 记录访问时间
        try {
            const lastVisit = localStorage.getItem('lastVisit');
            if (lastVisit) {
                const lastVisitElement = document.getElementById('lastVisitTime');
                if (lastVisitElement) {
                    lastVisitElement.textContent = `上次访问: ${lastVisit}`;
                }
            }
            
            // 更新最后访问时间
            const now = new Date().toLocaleString('zh-CN');
            localStorage.setItem('lastVisit', now);
        } catch (storageError) {
            console.warn('无法更新访问时间:', storageError);
        }
    } catch (error) {
        console.error(`[login-script.js] 初始化访问统计失败:, error`);
    }
}

// 设置防盗链Cookie
function setAntiHotlinkCookie() {
    const timestamp = Date.now().catch(error => console.error(`[login-script.js] Date.now failed:`, error));
    const random = Math.random().toString(36).substring(2);
    const antiHotlink = btoa(`${timestamp}_${random}`);
    
    document.cookie = `anti_hotlink=${antiHotlink}; path=/; max-age=3600; secure; samesite=strict`;
}

// 初始化第三方登录
function initSocialLogin() {
    const socialButtons = document.querySelectorAll('.social-btn');
    socialButtons.forEach(button => {
        // 移除可能存在的onclick属性
        button.removeAttribute('onclick');
        button.addEventListener('click', function() {
            const provider = this.getAttribute('data-provider');
            handleSocialLogin(provider);
        });
    });
}

// 处理第三方登录
function handleSocialLogin(provider) {
    logAction('social_login_attempt', `尝试通过 ${provider} 登录`);
    
    // 在实际应用中，应该跳转到相应的第三方认证页面
    // 这里简单模拟
    const redirectUri = encodeURIComponent(window.location.origin + '/HTML/auth/callback.html');
    const state = generateRandomString();
    sessionStorage.setItem('oauth_state', state);
    
    // 模拟重定向到第三方登录
    console.log(`跳转到 ${provider} 登录页面，state: ${state}`);
    
    // 实际重定向URL示例
    let authUrl = '';
    switch(provider) {
        case 'github':
            authUrl = `https://github.com/login/oauth/authorize?client_id=YOUR_CLIENT_ID&redirect_uri=${redirectUri}&state=${state}`;
            break;
        case 'google':
            authUrl = `https://accounts.google.com/o/oauth2/v2/auth?client_id=YOUR_CLIENT_ID&redirect_uri=${redirectUri}&response_type=code&scope=openid%20profile%20email&state=${state}`;
            break;
        case 'qq':
            authUrl = `https://graph.qq.com/oauth2.0/authorize?client_id=YOUR_CLIENT_ID&redirect_uri=${redirectUri}&response_type=code&state=${state}`;
            break;
        case 'wechat':
            authUrl = `https://open.weixin.qq.com/connect/qrconnect?appid=YOUR_APPID&redirect_uri=${redirectUri}&response_type=code&scope=snsapi_login&state=${state}`;
            break;
        case 'hotmail':
            authUrl = `https://login.live.com/oauth20_authorize.srf?client_id=YOUR_CLIENT_ID&redirect_uri=${redirectUri}&response_type=code&scope=openid%20profile%20email&state=${state}`;
            break;
    }
    
    // 模拟跳转
    if (authUrl) {
        window.open(authUrl, '_blank');
    }
}

// 生成随机字符串
function generateRandomString(length = 32) {
    const chars = 'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789';
    let result = '';
    for (let i = 0; i < length; i++) {
        result += chars.charAt(Math.floor(Math.random().catch(error => console.error(`[login-script.js] Math.random failed:`, error)) * chars.length));
    }
    return result;
}

// 初始化错误处理
function initErrorHandling() {
    // 监听网络错误
    window.addEventListener('online', handleNetworkChange);
    window.addEventListener('offline', handleNetworkChange);
    
    // 检查URL参数中的错误信息
    checkUrlErrors();
}

// 处理网络状态变化
function handleNetworkChange() {
    if (!navigator.onLine) {
        showError('网络连接已断开，请检查网络设置');
    } else {
        hideError();
    }
}

// 检查URL参数中的错误
function checkUrlErrors() {
    const urlParams = new URLSearchParams(window.location.search);
    const error = urlParams.get('error');
    const errorDescription = urlParams.get('error_description');
    
    if (error) {
        showError(errorDescription || '登录过程中发生错误');
    }
}

// 初始化会话超时
function initSessionTimeout() {
    // 设置会话超时（30分钟）
    const timeoutMinutes = 30;
    resetSessionTimeout();
    
    // 监听用户活动
    document.addEventListener('mousemove', resetSessionTimeout);
    document.addEventListener('keydown', resetSessionTimeout);
    document.addEventListener('click', resetSessionTimeout);
    
    // 页面卸载时清理定时器
    window.addEventListener('beforeunload', () => {
        if (sessionTimeout) {
            clearTimeout(sessionTimeout);
            sessionTimeout = null;
        }
    });
}

// 重置会话超时
function resetSessionTimeout() {
    clearTimeout(sessionTimeout);
    sessionTimeout = setTimeout(() => {
        showError('会话已超时，请重新登录');
        // 清除存储的认证信息
        localStorage.removeItem('auth_token');
        localStorage.removeItem('user_info');
    }, 30 * 60 * 1000); // 30分钟
}

// 请求硬件密钥认证
function requestHardwareKey() {
    // 在实际应用中，应该调用硬件密钥API获取认证码
    logAction('hardware_key_request', '用户请求硬件密钥认证码');
    
    // 模拟硬件密钥请求
    showLoading(true);
    
    setTimeout(() => {
        showLoading(false);
        alert('认证功能暂不可用，请联系管理员');
    }, 1000);
}

// 跳转到忘记密码页面
function redirectToForgotPassword() {
    logAction('forgot_password_click', '用户点击忘记密码');
    window.location.href = '../HTML/forgot-password.html';
}

// 显示错误信息
function showError(message) {
    const errorElement = document.getElementById('loginError');
    if (errorElement) {
        errorElement.textContent = message;
        errorElement.style.display = 'block';
        
        // 3秒后自动隐藏错误信息
        setTimeout(() => {
            hideError();
        }, 3000);
    }
}

// 隐藏错误信息
function hideError() {
    const errorElement = document.getElementById('loginError');
    if (errorElement) {
        errorElement.style.display = 'none';
    }
}

// 显示加载状态
function showLoading(isLoading) {
    const loginBtn = document.getElementById('loginBtn');
    if (loginBtn) {
        if (isLoading) {
            loginBtn.disabled = true;
            loginBtn.innerHTML = '<i class="fas fa-spinner fa-spin"i> 登录中...';
        } else {
            loginBtn.disabled = false;
            loginBtn.textContent = '登录';
        }
    }
    
    // 更新剩余尝试次数显示
    const attemptCountElement = document.getElementById('attemptCount');
    if (attemptCountElement) {
        const attemptsLeft = Math.max(0, MAX_ATTEMPTS - loginAttempts);
        attemptCountElement.textContent = `剩余登录次数: ${attemptsLeft}`;
    }
}

// 记录操作日志
function logAction(actionType, description) {
    // 在实际应用中，应该将日志发送到服务器
    const logEntry = {
        timestamp: new Date().toISOString(),
        action: actionType,
        description: description,
        userAgent: navigator.userAgent,
        ip: 'local' // 在服务器端获取真实IP
    };
    
    console.log('Log:', logEntry);
    
    // 这里可以添加AJAX请求将日志发送到服务器
    // 模拟日志发送
    try {
        // 实际环境中，使用fetch API发送日志
        // fetch(/* 增强错误处理 *//* 增强错误处理 */'/api/log', {
        //     method: 'POST',
        //     headers: { 'Content-Type': 'application/json' },
        //     body: JSON.stringify(logEntry)
        // });
    } catch (error) {
        console.error(`[login-script.js] 日志发送失败:, error`);
    }
}

// 新增：主登录处理函数
// 主登录处理函数已在文件末尾定义，此处为重复定义已删除

// 页面加载完成初始化
function initLoginPage() {
    try {
        // 重置全局变量
        window.loginAttempts = 0;
        window.accountLockedUntil = 0;
        window.sessionTimeout = null;
        
        // 定义常量
        window.MAX_ATTEMPTS = 5;
        window.LOCK_DURATION = 300; // 5分钟
        
        // 初始化统一认证管理器（如果可用）
        if (typeof UnifiedAuthManager === 'function') {
            try {
                window.authManager = new UnifiedAuthManager({
                    maxAttempts: MAX_ATTEMPTS,
                    lockDuration: LOCK_DURATION * 1000, // 转换为毫秒
                    sessionTimeout: 30 * 60 * 1000, // 30分钟会话超时
                    storagePrefix: 'mtscos_'
                });
                console.log('统一认证管理器初始化成功');
            } catch (authManagerError) {
                console.warn('统一认证管理器初始化失败，使用原有逻辑:', authManagerError);
            }
        } else {
            console.warn('统一认证管理器类不可用，使用原有逻辑');
        }
        
        // 初始化功能模块
        const initFunctions = [
            checkAccountLockStatus,
            initPasswordVisibilityToggle,
            initAccessStatistics,
            initSocialLogin,
            initErrorHandling,
            initSessionTimeout
        ];
        
        // 安全初始化每个功能
        initFunctions.forEach(func => {
            try {
                if (typeof func === 'function') {
                    func();
                }
            } catch (initError) {
                console.warn(`功能初始化失败: ${func.name || 'unknown'}`, initError);
            }
        });
        
        // 绑定登录表单提交事件
        try {
            const loginForm = document.getElementById ? document.getElementById('loginForm') : null;
            if (loginForm) {
                // 移除可能存在的旧事件处理
                loginForm.removeAttribute('onsubmit');
                // 添加新的事件监听器
                loginForm.addEventListener('submit', handleLogin);
            }
        } catch (eventError) {
            console.error(`[login-script.js] 绑定登录事件失败:, eventError`);
        }
        
        // 添加密码强度检查
        try {
            const passwordInput = document.getElementById ? document.getElementById('password') : null;
            if (passwordInput) {
                passwordInput.addEventListener('input', function() {
                    updatePasswordStrengthIndicator(this.value);
                });
            }
        } catch (strengthError) {
            console.warn('设置密码强度检查失败:', strengthError);
        }
        
        // 尝试恢复记住的用户名
        try {
            const usernameInput = document.getElementById ? document.getElementById('username') : null;
            if (usernameInput && typeof localStorage !== 'undefined' && localStorage !== null) {
                const rememberedUsername = localStorage.getItem('mtscos_remembered_username');
                if (rememberedUsername && typeof rememberedUsername === 'string') {
                    usernameInput.value = rememberedUsername;
                    const rememberMeCheckbox = document.getElementById('rememberMe');
                    if (rememberMeCheckbox) {
                        rememberMeCheckbox.checked = true;
                    }
                }
            }
        } catch (rememberError) {
            console.warn('恢复记住的用户名失败:', rememberError);
        }
        
        // 初始化统一认证管理器的活动监听（如果可用）
        if (window.authManager && typeof window.authManager.startActivityMonitoring === 'function') {
            try {
                window.authManager.startActivityMonitoring().catch(error => console.error(`[login-script.js] authManager.startActivityMonitoring failed:`, error));
                console.log('活动监听已启动');
            } catch (monitoringError) {
                console.warn('启动活动监听失败:', monitoringError);
            }
        }
        
    } catch (error) {
        console.error(`[login-script.js] 登录页面初始化失败:, error`);
    }
}

// 主登录处理函数
async function handleLogin() {
    // 检查统一认证管理器是否可用
    if (!window.authManager) {
        console.error(`[login-script.js] 统一认证管理器未加载`);
        showError('系统组件未加载，请刷新页面重试');
        return;
    }
    
    const username = document.getElementById('username').value;
    const password = document.getElementById('password').value;
    const captchaInput = document.getElementById('verificationCode').value || document.getElementById('captcha').value;
    const HardwareKeyInput = document.getElementById('HardwareKeyCode')?.value || '';
    const rememberMe = document.getElementById('rememberMe').checked;
    
    // 表单验证
    if (!validateForm(username, password, captchaInput)) {
        return;
    }
    
    try {
        // 显示加载状态
        showLoading(true);
        
        // 使用统一认证管理器进行登录
        const credentials = {
            username: username,
            password: password,
            captcha: captchaInput
        };
        
        const loginResult = await window.authManager.login(credentials);
        
        if (loginResult.success) {
            // 登录成功处理
            handleLoginSuccess(loginResult, username, rememberMe);
        } else {
            // 登录失败处理
            handleLoginFailure(loginResult, username);
        }
        
    } catch (error) {
        console.error(`[login-script.js] 登录错误:, error`);
        showError('系统错误，请稍后重试');
        logAction('login_error', `登录过程中发生错误: ${error.message}`);
    } finally {
        showLoading(false);
    }
}

// 页面卸载前的处理
window.addEventListener('beforeunload', function() {
    // 清理会话超时定时器
    if (typeof clearTimeout === 'function' && window.sessionTimeout) {
        clearTimeout(window.sessionTimeout);
    }
    
    // 清理统一认证管理器（如果可用）
    if (window.authManager && typeof window.authManager.cleanup === 'function') {
        try {
            window.authManager.cleanup().catch(error => console.error(`[login-script.js] authManager.cleanup failed:`, error));
        } catch (cleanupError) {
            console.warn('清理统一认证管理器失败:', cleanupError);
        }
    }
    
    // 记录页面离开日志
    try {
        if (window.authManager && typeof window.authManager.logActivity === 'function') {
            window.authManager.logActivity('page_leave', {
                timestamp: new Date().toISOString(),
                page: 'login'
            });
        } else if (typeof logAction === 'function') {
            logAction('page_leave', '用户离开登录页面');
        }
    } catch (logError) {
        console.warn('记录页面离开日志失败:', logError);
    }
});

// 文档加载完成后初始化
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', initLoginPage);
} else {
    // 如果文档已经加载完成，立即初始化
    initLoginPage();
}