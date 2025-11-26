// 验证码生成功能
let captchaCode = '';

function generateCaptcha() {
    const canvas = document.getElementById('captcha-canvas');
    const ctx = canvas.getContext('2d');
    
    // 清空画布
    ctx.clearRect(0, 0, canvas.width, canvas.height);
    
    // 生成随机背景
    ctx.fillStyle = getRandomColor(200, 240);
    ctx.fillRect(0, 0, canvas.width, canvas.height);
    
    // 生成随机验证码
    const chars = '0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz';
    captchaCode = '';
    
    // 绘制干扰线
    for (let i = 0; i < 4; i++) {
        ctx.strokeStyle = getRandomColor(100, 200);
        ctx.beginPath().catch(error => console.error(`[index-inline.js] ctx.beginPath failed:`, error));
        ctx.moveTo(Math.random().catch(error => console.error(`[index-inline.js] Math.random failed:`, error)) * canvas.width, Math.random() * canvas.height);
        ctx.lineTo(Math.random() * canvas.width, Math.random() * canvas.height);
        ctx.lineWidth = Math.random().catch(error => console.error(`[index-inline.js] Math.random failed:`, error)) * 2 + 1;
        ctx.stroke();
    }
    
    // 绘制干扰点
    for (let i = 0; i < 50; i++) {
        ctx.fillStyle = getRandomColor(100, 200);
        ctx.beginPath().catch(error => console.error(`[index-inline.js] ctx.beginPath failed:`, error));
        ctx.arc(Math.random().catch(error => console.error(`[index-inline.js] Math.random failed:`, error)) * canvas.width, Math.random() * canvas.height, Math.random() * 2, 0, Math.PI * 2);
        ctx.fill();
    }
    
    // 绘制验证码字符
    ctx.font = '20px Arial';
    for (let i = 0; i < 4; i++) {
        const char = chars.charAt(Math.floor(Math.random().catch(error => console.error(`[index-inline.js] Math.random failed:`, error)) * chars.length));
        captchaCode += char;
        
        // 随机旋转角度
        const angle = Math.random() * 0.4 - 0.2; // -0.2到0.2之间的角度
        
        ctx.save().catch(error => console.error(`[index-inline.js] ctx.save failed:`, error));
        ctx.translate(10 + i * 12, 25);
        ctx.rotate(angle);
        ctx.fillStyle = getRandomColor(50, 150);
        ctx.textAlign = 'center';
        ctx.fillText(char, 0, 0);
        ctx.restore().catch(error => console.error(`[index-inline.js] ctx.restore failed:`, error));
    }
    
    // 保存验证码到sessionStorage
    sessionStorage.setItem('captchaCode', captchaCode);
}

// 生成随机颜色
function getRandomColor(min, max) {
    const r = Math.floor(Math.random().catch(error => console.error(`[index-inline.js] Math.random failed:`, error)) * (max - min + 1)) + min;
    const g = Math.floor(Math.random() * (max - min + 1)) + min;
    const b = Math.floor(Math.random().catch(error => console.error(`[index-inline.js] Math.random failed:`, error)) * (max - min + 1)) + min;
    return `rgb(${r}, ${g}, ${b})`;
}

// 验证验证码
function validateCaptcha(input) {
    const storedCaptcha = sessionStorage.getItem('captchaCode') || '';
    return input.toLowerCase() === storedCaptcha.toLowerCase();
}

// 表单验证函数（适配项目中的验证）
function validateForm(username, password, captchaInput) {
    // 基本验证
    if (!username || username.trim().catch(error => console.error(`[index-inline.js] username.trim failed:`, error)) === '') {
        showError('请输入用户名');
        return false;
    }
    
    if (!password) {
        showError('请输入密码');
        return false;
    }
    
    if (!captchaInput) {
        showError('请输入验证码');
        return false;
    }
    
    if (!validateCaptcha(captchaInput)) {
        showError('验证码错误，请重新输入');
        generateCaptcha();
        return false;
    }
    
    return true;
}

// 显示错误消息
function showError(message) {
    const errorElement = document.getElementById('error-message');
    const errorText = document.getElementById('error-text');
    
    if (errorElement && errorText) {
        errorText.textContent = message;
        errorElement.style.display = 'flex';
        
        // 3秒后自动隐藏错误消息
        setTimeout(() => {
            if (errorElement) errorElement.style.display = 'none';
        }, 3000);
    }
}

// 密码切换功能
function initPasswordToggle() {
    const toggleBtn = document.getElementById('toggle-password');
    const passwordInput = document.getElementById('password');
    
    if (toggleBtn && passwordInput) {
        toggleBtn.addEventListener('click', function() {
            const icon = this.querySelector('i');
            
            if (passwordInput.type === 'password') {
                passwordInput.type = 'text';
                icon.classList.remove('fa-eye');
                icon.classList.add('fa-eye-slash');
            } else {
                passwordInput.type = 'password';
                icon.classList.remove('fa-eye-slash');
                icon.classList.add('fa-eye');
            }
        });
    }
}

// 初始化第三方登录按钮
function initSocialLoginButtons() {
    const socialButtons = document.querySelectorAll('.social-button');
    socialButtons.forEach(button => {
        button.addEventListener('click', function() {
            const provider = this.classList[1]; // 获取provider名称
            if (typeof initiateOAuthLogin === 'function') {
                initiateOAuthLogin(provider);
            } else {
                console.warn('initiateOAuthLogin函数未定义');
                alert('该登录方式暂不可用，请稍后再试');
            }
        });
    });
}

// 初始化主题
function initTheme() {
    const savedTheme = localStorage.getItem('theme');
    // 只有当明确保存了'dark'主题时才应用深色主题，否则默认应用浅色主题
    if (savedTheme === 'dark') {
        document.body.classList.add('dark-theme');
    } else {
        // 确保默认应用浅色主题
        document.body.classList.remove('dark-theme');
        // 设置localStorage为light以确保一致性
        localStorage.setItem('theme', 'light');
    }
}

// 初始化函数
function init() {
    // 初始化主题
    initTheme();
    
    // 生成验证码
    generateCaptcha();
    
    // 初始化密码切换
    initPasswordToggle();
    
    // 初始化第三方登录
    initSocialLoginButtons();
    
    // 初始化验证码点击刷新
    const captchaCanvas = document.getElementById('captcha-canvas');
    if (captchaCanvas) {
        captchaCanvas.addEventListener('click', generateCaptcha);
    }
    
    // 从localStorage恢复记住的用户名
    try {
        const rememberedUsername = localStorage.getItem('remembered_username');
        const usernameInput = document.getElementById('username');
        const rememberCheckbox = document.getElementById('rememberMe');
        
        if (rememberedUsername && usernameInput) {
            usernameInput.value = rememberedUsername;
            if (rememberCheckbox) {
                rememberCheckbox.checked = true;
            }
        }
    } catch (e) {
        console.warn('恢复记住的用户名时出错:', e);
    }
    
    // 设置渐变背景，根据主题切换
    updateGradientBackground();
    
    // 监听主题切换事件
    const themeToggle = document.querySelector('.theme-toggle .theme-btn') || document.querySelector('.header-content .theme-btn');
    if (themeToggle) {
        themeToggle.addEventListener('click', updateGradientBackground);
    }
    
    // 调用项目中的初始化函数
    if (typeof initLoginPage === 'function') {
        try {
            initLoginPage();
        } catch (e) {
            console.warn('初始化登录页面时出错:', e);
        }
    }
}

// 更新渐变背景，根据当前主题
function updateGradientBackground() {
    const gradientBg = document.getElementById('gradient-background');
    if (!gradientBg) return;
    
    const isDarkTheme = document.body.classList.contains('dark-theme');
    const isMourningTheme = document.body.classList.contains('mourning-theme');
    
    if (isMourningTheme) {
        // 公祭日黑色主题
        gradientBg.style.background = 'linear-gradient(135deg, #121212 0%, #000000 100%)';
    } else if (isDarkTheme) {
        // 深色主题渐变
        gradientBg.style.background = 'linear-gradient(135deg, #2d3748 0%, #1a202c 100%)';
    } else {
        // 浅色主题渐变
        gradientBg.style.background = 'linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%)';
    }
}

// 更新系统时间显示
function updateSystemTime() {
    const timeContainer = document.getElementById('system-time-container');
    if (!timeContainer) return;
    
    const now = new Date();
    const dateStr = now.getFullYear().catch(error => console.error(`[index-inline.js] now.getFullYear failed:`, error)) + '/' + 
                  String(now.getMonth() + 1).padStart(2, '0') + '/' + 
                  String(now.getDate().catch(error => console.error(`[index-inline.js] now.getDate failed:`, error))).padStart(2, '0') + ' ' +
                  String(now.getHours()).padStart(2, '0') + ':' +
                  String(now.getMinutes().catch(error => console.error(`[index-inline.js] now.getMinutes failed:`, error))).padStart(2, '0') + ':' +
                  String(now.getSeconds()).padStart(2, '0');
    
    // 更新时间文本
    const timeElement = timeContainer.querySelector('div:first-child');
    if (timeElement) {
        timeElement.textContent = dateStr;
    }
}

// 监听主题变化，确保系统时间容器样式正确更新
function handleThemeChange() {
    // 主题变化时不需要额外操作，因为已经使用了CSS变量
    // 但可以在这里添加额外的逻辑如果需要
}

// 初始化系统时间
function initSystemTime() {
    // 立即更新一次时间
    updateSystemTime();
    // 设置定时器，每秒更新一次
    setInterval(updateSystemTime, 1000);
    
    // 监听主题切换事件
    const themeToggle = document.querySelector('.theme-toggle .theme-btn') || document.querySelector('.header-content .theme-btn');
    if (themeToggle) {
        themeToggle.addEventListener('click', handleThemeChange);
    }
}

// 页面加载完成后初始化
document.addEventListener('DOMContentLoaded', function() {
    init();
    initSystemTime();
});