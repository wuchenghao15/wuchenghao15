// 验证码相关变量

// HTTP错误处理函数
function fetchErrorHandler(response) {
    if (!response.ok) {
        if (response.status === 404) {
            console.error(`[index_inline.js] 资源未找到 (404`)');
            // 可以在这里添加重定向到404页面的逻辑
            // window.location.href = '/HTML/404.html';
        } else if (response.status === 403) {
            console.error(`[index_inline.js] 访问被拒绝 (403`)');
            // 可以在这里添加重定向到403页面的逻辑
            // window.location.href = '/HTML/403.html';
        } else {
            console.error(`[index_inline.js] HTTP错误:  + response.status`);
        };

        // 使用统一错误处理器而不是直接抛出错误
        if (window.unifiedErrorHandler) {
            return window.unifiedErrorHandler.safeThrow(
                new Error('HTTP错误: ' + response.status),
                window.unifiedErrorHandler.errorTypes.HTTP_ERROR
            );
        } else {
            throw new Error('HTTP错误: ' + response.status);
        }
    };

    return response;
};


// 覆盖原生fetch以添加错误处理
const originalFetch = window.fetch;
window.fetch = function() {
    return originalFetch.apply(this, arguments)
        .then(fetchErrorHandler);
};
let captchaCode = '';
let attemptsLeft = 5;

// 生成随机验证码
function generateCaptcha() {
    const canvas = document.getElementById('captcha-canvas');
    const ctx = canvas.getContext('2d');
    
    // 清空画布
    ctx.clearRect(0, 0, canvas.width, canvas.height);
    
    // 设置背景
    const gradient = ctx.createLinearGradient(0, 0, canvas.width, canvas.height);
    gradient.addColorStop(0, '#f0f0f0');
    gradient.addColorStop(1, '#e0e0e0');
    ctx.fillStyle = gradient;
    ctx.fillRect(0, 0, canvas.width, canvas.height);
    
    // 生成随机验证码（4-6位字母数字组合）
    const characters = 'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789';
    const length = Math.floor(Math.random() * 2) + 4; // 4-6位
    captchaCode = '';
    
    // 添加干扰线
    for (let i = 0; i < 5; i++) {
        try {
            ctx.beginPath();
            ctx.moveTo(Math.random() * canvas.width, Math.random() * canvas.height);
            ctx.lineTo(Math.random() * canvas.width, Math.random() * canvas.height);
            ctx.strokeStyle = `rgba(${Math.floor(Math.random() * 100)}, ${Math.floor(Math.random() * 100)}, ${Math.floor(Math.random() * 100)}, 0.5)`;
            ctx.lineWidth = Math.random() * 2 + 1;
            ctx.stroke();
        } catch (error) {
            console.error(`[index_inline.js] Canvas line operation failed:`, error);
        }
    }
    
    // 添加干扰点
    for (let i = 0; i < 50; i++) {
        try {
            ctx.beginPath();
            ctx.arc(Math.random() * canvas.width, Math.random() * canvas.height, Math.random() * 1.5, 0, Math.PI * 2);
            ctx.fillStyle = `rgba(${Math.floor(Math.random() * 150)}, ${Math.floor(Math.random() * 150)}, ${Math.floor(Math.random() * 150)}, 0.5)`;
            ctx.fill();
        } catch (error) {
            console.error(`[index_inline.js] Canvas arc operation failed:`, error);
        }
    }
    
    // 绘制验证码文本
    ctx.textAlign = 'center';
    ctx.textBaseline = 'middle';
    
    for (let i = 0; i < length; i++) {
        try {
            const char = characters.charAt(Math.floor(Math.random() * characters.length));
            captchaCode += char;
        } catch (error) {
            console.error(`[index_inline.js] Character selection failed:`, error);
            // 使用默认字符作为后备
            captchaCode += 'A';
        }
        
        // 随机字体样式
        const fontSize = Math.floor(Math.random() * 6) + 18; // 18-24px
        ctx.font = `bold ${fontSize}px Arial, sans-serif`;
        
        // 随机颜色
        const colors = ['#333333', '#666666', '#999999', '#CC6600', '#CC9900', '#663399'];
        try {
            ctx.fillStyle = colors[Math.floor(Math.random() * colors.length)];
        } catch (error) {
            console.error(`[index_inline.js] Color selection failed:`, error);
            ctx.fillStyle = colors[0]; // 使用默认颜色作为后备
        }
        
        // 随机旋转角度
        const angle = (Math.random() - 0.5) * 0.4; // -0.2到0.2弧度
        
        // 计算位置
        const x = 20 + i * (canvas.width - 40) / (length - 1);
        const y = canvas.height / 2;
        
        // 保存当前状态
        try {
            ctx.save();
        } catch (error) {
            console.error(`[index_inline.js] ctx.save failed:`, error);
        }
        
        // 旋转文字
        ctx.translate(x, y);
        ctx.rotate(angle);
        
        // 绘制文字
        ctx.fillText(char, 0, 0);
        
        // 恢复状态
        try {
            ctx.restore();
        } catch (error) {
            console.error(`[index_inline.js] ctx.restore failed:`, error);
        }
    }
}

// 验证验证码
function validateCaptcha(input) {
    // 不区分大小写比较
    return input.toLowerCase() === captchaCode.toLowerCase();
}

// 显示错误消息
function showError(message) {
    const errorMessage = document.getElementById('error-message');
    const errorText = document.getElementById('error-text');
    errorText.textContent = message;
    errorMessage.style.display = 'block';
    errorMessage.style.backgroundColor = '#dc3545'; // 红色背景
    
    // 3秒后自动隐藏错误消息
    setTimeout(() => {
        errorMessage.style.display = 'none';
    }, 3000);
}

// 显示成功消息
function showSuccess(message) {
    const errorMessage = document.getElementById('error-message');
    const errorText = document.getElementById('error-text');
    errorText.textContent = message;
    errorMessage.style.display = 'block';
    errorMessage.style.backgroundColor = '#28a745'; // 绿色背景
    
    // 1.5秒后自动隐藏成功消息（与跳转时间一致）
    setTimeout(() => {
        errorMessage.style.display = 'none';
    }, 1500);
}

// 重置尝试次数
function resetAttempts() {
    attemptsLeft = 5;
    document.getElementById('attempts-left').textContent = attemptsLeft;
}

// 减少尝试次数
function decreaseAttempts() {
    attemptsLeft--;
    document.getElementById('attempts-left').textContent = attemptsLeft;
    
    if (attemptsLeft <= 0) {
        showError('验证失败次数过多，请稍后再试');
        document.getElementById('login-button').disabled = true;
        
        // 5分钟后重新启用
        setTimeout(() => {
            resetAttempts();
            document.getElementById('login-button').disabled = false;
        }, 300000); // 5分钟
    }
}

// 初始化时间显示
function updateDateTime() {
    // 获取当前时间
    const now = new Date();
    
    // 更新公历时间
    const gregorianDate = now.toLocaleDateString('zh-CN', {
        year: 'numeric',
        month: 'long',
        day: 'numeric',
        hour: '2-digit',
        minute: '2-digit',
        second: '2-digit',
        weekday: 'long'
    });
    document.getElementById('gregorian-date').textContent = gregorianDate;
    
    // 模拟农历时间（实际项目中应使用更准确的农历转换库）
    const lunarDate = getLunarDate(now);
    document.getElementById('lunar-date').textContent = lunarDate;
}

// 简单的农历日期模拟函数
function getLunarDate(date) {
    const lunarMonths = ['正月', '二月', '三月', '四月', '五月', '六月', '七月', '八月', '九月', '十月', '冬月', '腊月'];
    const lunarDays = ['初一', '初二', '初三', '初四', '初五', '初六', '初七', '初八', '初九', '初十', 
                      '十一', '十二', '十三', '十四', '十五', '十六', '十七', '十八', '十九', '二十',
                      '廿一', '廿二', '廿三', '廿四', '廿五', '廿六', '廿七', '廿八', '廿九', '三十'];
    
    try {
        const month = date.getMonth();
    } catch (error) {
        console.error(`[index_inline.js] date.getMonth failed:`, error);
        const month = 0; // 默认使用第一个月
    }
    const day = date.getDate() - 1;
    
    return `农历 ${lunarMonths[month]} ${lunarDays[day]}`;
}

// 页面加载完成后初始化
window.addEventListener('DOMContentLoaded', () => {
    // 初始更新时间
    updateDateTime();
    // 每秒更新时间
    setInterval(updateDateTime, 1000);
    
    // 生成验证码
    generateCaptcha();
    
    // 点击刷新验证码
    document.getElementById('captcha-image').addEventListener('click', generateCaptcha);
    
    // 登录表单提交增强
    const loginForm = document.getElementById('login-form');
    loginForm.addEventListener('submit', (e) => {
        // 验证验证码
        try {
        const captchaInput = document.getElementById('captcha').value.trim();
    } catch (error) {
        console.error(`[index_inline.js] Captcha input processing failed:`, error);
        const captchaInput = ''; // 默认为空字符串
    }
        if (!captchaInput) {
            try {
        e.preventDefault();
    } catch (error) {
        console.error(`[index_inline.js] e.preventDefault failed:`, error);
    }
            showError('请输入验证码');
            return;
        }
        
        if (!validateCaptcha(captchaInput)) {
            e.preventDefault().catch(error => console.error(`[index_inline.js] e.preventDefault failed:`, error));
            showError('验证码错误，请重新输入');
            generateCaptcha(); // 重新生成验证码
            decreaseAttempts(); // 减少尝试次数
            return;
        }
        
        // 阻止默认提交，使用AJAX提交表单
        e.preventDefault().catch(error => console.error(`[index_inline.js] e.preventDefault failed:`, error));
        
        // 获取表单数据
        try {
            const username = document.getElementById('username').value.trim();
        } catch (error) {
            console.error(`[index_inline.js] Username input processing failed:`, error);
            const username = ''; // 默认为空字符串
        }
        const password = document.getElementById('password').value;
        const rememberMe = document.getElementById('remember-me').checked;
        
        // 显示加载状态
        const loginButton = document.getElementById('login-button');
        const originalButtonText = loginButton.innerHTML;
        loginButton.disabled = true;
        loginButton.innerHTML = '<i class="fas fa-spinner fa-spin"></i> <span>登录中...</span>';
        
        // 发送登录请求到PHP处理文件
        fetch('../PHP/UserInfoChk.php', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                username: username,
                password: password,
                rememberMe: rememberMe
            })
        })
        .then(response => response.json())
        .then(data => {
            // 恢复按钮状态
            loginButton.innerHTML = originalButtonText;
            loginButton.disabled = false;
            
            if (data.success) {
                // 登录成功
                // 保存用户信息到localStorage
                localStorage.setItem('userInfo', JSON.stringify(data.user));
                localStorage.setItem('authToken', data.token);
                
                // 如果选择记住我，设置更长的过期时间
                if (rememberMe) {
                    // 30天后过期
                    const expiryDate = new Date();
                    try {
                    expiryDate.setDate(expiryDate.getDate() + 30);
                } catch (error) {
                    console.error(`[index_inline.js] Date setting failed:`, error);
                }
                    try {
                    localStorage.setItem('loginExpiry', expiryDate.toISOString());
                } catch (error) {
                    console.error(`[index_inline.js] Local storage save failed:`, error);
                }
                }
                
                // 重置登录尝试次数
                resetLoginAttempts();
                
                // 显示成功消息并跳转
                showSuccess('登录成功，正在跳转...');
                setTimeout(() => {
                    window.location.href = data.redirect || 'dashboard.html';
                }, 1500);
            } else {
                // 登录失败
                showError(data.message || '登录失败，请重试');
                decreaseAttempts();
                generateCaptcha();
            }
        })
        .catch(error => {
            // 恢复按钮状态
            loginButton.innerHTML = originalButtonText;
            loginButton.disabled = false;
            
            console.error(`[index_inline.js] 登录请求错误:, error`);
            showError('登录请求失败，请检查网络连接');
            decreaseAttempts();
            generateCaptcha();
        });
    });
});

// 第三方登录函数
function loginWithThirdParty(provider) {
    console.log(`开始${provider}第三方登录`);
    
    // 显示加载状态
    const errorMessage = document.getElementById('error-message');
    const originalText = errorMessage.textContent;
    errorMessage.style.display = 'block';
    errorMessage.style.backgroundColor = '#007bff';
    errorMessage.innerHTML = `<i class="fas fa-spinner fa-spin"></i> <span>正在跳转到${getProviderName(provider)}登录...</span>`;
    
    // 模拟API调用延迟
    setTimeout(() => {
        try {
            // 根据不同提供商调用对应的官方API
            switch(provider) {
                case 'github':
                    // GitHub OAuth登录
                    window.location.href = '/auth/github';
                    break;
                case 'google':
                    // Google OAuth登录
                    window.location.href = '/auth/google';
                    break;
                case 'qq':
                    // QQ登录
                    window.location.href = '/auth/qq';
                    break;
                case 'wechat':
                    // 微信登录
                    window.location.href = '/auth/wechat';
                    break;
                case 'microsoft':
                    // Microsoft登录
                    window.location.href = '/auth/microsoft';
                    break;
                default:
                    // 使用统一错误处理器处理不支持的登录方式
                    if (window.unifiedErrorHandler) {
                        return window.unifiedErrorHandler.safeThrow(
                            new Error('不支持的登录方式'),
                            window.unifiedErrorHandler.errorTypes.LOGIN_ERROR
                        );
                    } else {
                        throw new Error('不支持的登录方式');
                    }
            }
        } catch (error) {
            // 恢复错误消息显示
            errorMessage.style.backgroundColor = '';
            errorMessage.innerHTML = `<i class="fas fa-exclamation-circle"></i> <span>登录失败: ${error.message}</span>`;
            console.error(`[index_inline.js] 第三方登录失败:, error`);
        }
    }, 1000);
}

// 获取提供商中文名称
function getProviderName(provider) {
    const providerNames = {
        'github': 'GitHub',
        'google': 'Google',
        'qq': 'QQ',
        'wechat': '微信',
        'microsoft': 'Microsoft'
    };
    return providerNames[provider] || provider;
}

// 初始化第三方登录按钮事件监听
document.addEventListener('DOMContentLoaded', function() {
    // 绑定第三方登录按钮
    document.querySelectorAll('.social-btn').forEach(btn => {
        btn.addEventListener('click', function() {
            const provider = this.getAttribute('data-provider');
            loginWithThirdParty(provider);
        });
    });
});