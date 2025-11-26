// 简化的登录脚本 - 修复版本
console.log('登录脚本已加载');

// 避免重复声明
if (typeof window.sessionTimeout === 'undefined') {
    window.sessionTimeout = 30 * 60 * 1000; // 30分钟
}

// 全局变量
let loginAttempts = 0;
const maxAttempts = 3;

// DOM元素
let loginForm, usernameInput, passwordInput, captchaInput, loginBtn, errorContainer;

// 初始化DOM元素
function initializeElements() {
    loginForm = document.getElementById('login-form');
    usernameInput = document.getElementById('username');
    passwordInput = document.getElementById('password');
    captchaInput = document.getElementById('captcha');
    loginBtn = document.getElementById('login-btn');
    errorContainer = document.getElementById('error-container');
    
    console.log('DOM元素初始化完成');
}

// 显示错误信息
function showError(message) {
    if (errorContainer) {
        errorContainer.innerHTML = `<div class="error-message">${message}</div>`;
        setTimeout(() => {
            errorContainer.innerHTML = '';
        }, 5000);
    }
}

// 显示成功信息
function showSuccess(message) {
    if (errorContainer) {
        errorContainer.innerHTML = `<div class="success-message">${message}</div>`;
    }
}

// 设置按钮状态
function setButtonState(loading = false) {
    if (loginBtn) {
        if (loading) {
            loginBtn.disabled = true;
            loginBtn.innerHTML = '<span class="spinner"></span> 登录中...';
        } else {
            loginBtn.disabled = false;
            loginBtn.innerHTML = '登录';
        }
    }
}

// 验证表单
function validateForm() {
    const username = usernameInput?.value?.trim();
    const password = passwordInput?.value;
    const captcha = captchaInput?.value?.trim();
    
    if (!username) {
        showError('请输入用户名');
        return false;
    }
    
    if (!password) {
        showError('请输入密码');
        return false;
    }
    
    if (!captcha) {
        showError('请输入验证码');
        return false;
    }
    
    return true;
}

// 处理登录
async function handleLogin(e) {
    e.preventDefault();
    
    if (!validateForm()) {
        return;
    }
    
    // 检查登录尝试次数
    if (loginAttempts >= maxAttempts) {
        showError('登录尝试次数过多，请稍后再试');
        return;
    }
    
    const username = usernameInput.value.trim();
    const password = passwordInput.value;
    const captcha = captchaInput.value.trim();
    
    setButtonState(true);
    
    try {
        // 模拟API调用
        const response = await mockLoginAPI(username, password, captcha);
        
        if (response.success) {
            showSuccess('登录成功！正在跳转...');
            loginAttempts = 0;
            
            // 保存登录状态
            localStorage.setItem('isLoggedIn', 'true');
            localStorage.setItem('username', username);
            
            // 跳转到主页
            setTimeout(() => {
                window.location.href = 'dashboard.html';
            }, 1500);
        } else {
            loginAttempts++;
            showError(response.message || '登录失败');
            refreshCaptcha();
        }
    } catch (error) {
        console.error('登录错误:', error);
        showError('网络错误，请检查连接后重试');
        loginAttempts++;
    } finally {
        setButtonState(false);
    }
}

// 模拟登录API
async function mockLoginAPI(username, password, captcha) {
    // 模拟网络延迟
    await new Promise(resolve => setTimeout(resolve, 1000));
    
    // 简单的验证逻辑
    if (username === 'admin' && password === 'admin123' && captcha.toUpperCase() === 'ABCD') {
        return {
            success: true,
            message: '登录成功',
            token: 'mock-jwt-token-' + Date.now()
        };
    } else {
        return {
            success: false,
            message: '用户名、密码或验证码错误'
        };
    }
}

// 刷新验证码
function refreshCaptcha() {
    const captchaImg = document.getElementById('captcha-img');
    if (captchaImg) {
        const chars = 'ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789';
        let result = '';
        for (let i = 0; i < 4; i++) {
            result += chars.charAt(Math.floor(Math.random() * chars.length));
        }
        captchaImg.textContent = result;
    }
}

// 检查登录状态
function checkLoginStatus() {
    const isLoggedIn = localStorage.getItem('isLoggedIn');
    if (isLoggedIn === 'true') {
        // 如果已经登录，直接跳转
        window.location.href = 'dashboard.html';
    }
}

// 初始化
function init() {
    console.log('初始化登录页面');
    
    initializeElements();
    checkLoginStatus();
    refreshCaptcha();
    
    // 绑定事件
    if (loginForm) {
        loginForm.addEventListener('submit', handleLogin);
    }
    
    // 验证码点击刷新
    const captchaImg = document.getElementById('captcha-img');
    if (captchaImg) {
        captchaImg.addEventListener('click', refreshCaptcha);
    }
    
    // 第三方登录按钮
    document.querySelectorAll('.login-btn').forEach(btn => {
        btn.addEventListener('click', function() {
            const provider = this.dataset.provider;
            console.log('第三方登录:', provider);
            showError(`${provider} 登录功能开发中`);
        });
    });
    

    
    console.log('登录页面初始化完成');
}

// 页面加载完成后初始化
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init);
} else {
    init();
}

// 暴露全局函数
window.refreshCaptcha = refreshCaptcha;
window.showLoginError = showError;
window.showLoginSuccess = showSuccess;