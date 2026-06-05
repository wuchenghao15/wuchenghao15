// 核心功能：表单处理和基本页面功能

// 确保DOM完全加载后再执行表单相关操作
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', initFormFunctions);
} else {
    initFormFunctions();
}

function initFormFunctions() {
    // 表单切换功能
    const loginTab = document.getElementById('login-tab');
    const registerTab = document.getElementById('register-tab');
    const loginForm = document.getElementById('login-form');
    const registerForm = document.getElementById('register-form');
    const backToLoginLink = document.getElementById('back-to-login');
    
    // 空值检查，确保DOM元素存在
    if (!loginTab || !registerTab || !loginForm || !registerForm) {
        console.warn('表单元素未找到，跳过表单功能初始化');
        return;
    }
    
    // 切换到登录表单
    function switchToLogin() {
        loginTab.classList.add('active');
        registerTab.classList.remove('active');
        loginForm.classList.add('active');
        registerForm.classList.remove('active');
    }
    
    // 切换到注册表单
    function switchToRegister() {
        registerTab.classList.add('active');
        loginTab.classList.remove('active');
        registerForm.classList.add('active');
        loginForm.classList.remove('active');
    }
    
    // 登录标签点击事件
    loginTab.addEventListener('click', switchToLogin);
    
    // 注册标签点击事件
    registerTab.addEventListener('click', switchToRegister);
    
    // "已有账号？立即登录"链接点击事件
    if (backToLoginLink) {
        backToLoginLink.addEventListener('click', (e) => {
            e.preventDefault();
            switchToLogin();
        });
    }
    
    // 添加回车键监听功能
    const loginUsername = document.getElementById('login-username');
    const loginPassword = document.getElementById('login-password');
    const registerUsername = document.getElementById('register-username');
    const registerEmail = document.getElementById('register-email');
    const registerPassword = document.getElementById('register-password');
    
    // 登录表单回车键监听
    if (loginUsername && loginPassword) {
        loginUsername.addEventListener('keydown', (e) => {
            if (e.key === 'Enter') {
                loginPassword.focus();
                e.preventDefault();
            }
        });
        
        // 密码输入框按回车提交表单
        loginPassword.addEventListener('keydown', (e) => {
            if (e.key === 'Enter') {
                loginForm.submit();
                e.preventDefault();
            }
        });
    }
    
    // 注册表单回车键监听
    if (registerUsername && registerEmail && registerPassword) {
        // 用户名输入框按回车跳转到邮箱输入框
        registerUsername.addEventListener('keydown', (e) => {
            if (e.key === 'Enter') {
                registerEmail.focus();
                e.preventDefault();
            }
        });
        
        // 邮箱输入框按回车跳转到密码输入框
        registerEmail.addEventListener('keydown', (e) => {
            if (e.key === 'Enter') {
                registerPassword.focus();
                e.preventDefault();
            }
        });
        
        // 密码输入框按回车提交表单
        registerPassword.addEventListener('keydown', (e) => {
            if (e.key === 'Enter') {
                registerForm.submit();
                e.preventDefault();
            }
        });
    }
}

// 显示AI提示信息
function showAITip(message) {
    // 创建提示元素
    const tipElement = document.createElement('div');
    tipElement.className = 'ai-tip';
    tipElement.innerHTML = `
        <div class="ai-tip-content">
            <span class="ai-tip-icon">🤖</span>
            <div class="ai-tip-message">${message}</div>
            <button class="ai-tip-close">×</button>
        </div>
    `;
    
    // 添加样式
    tipElement.style.cssText = `
        position: fixed;
        top: 20px;
        right: 20px;
        background-color: #f8f9fa;
        border: 1px solid #dee2e6;
        border-radius: 8px;
        box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
        z-index: 10000;
        max-width: 300px;
        padding: 15px;
        font-size: 14px;
    `;
    
    // 添加到DOM
    document.body.appendChild(tipElement);
    
    // 关闭按钮事件
    const closeButton = tipElement.querySelector('.ai-tip-close');
    if (closeButton) {
        closeButton.addEventListener('click', () => {
            tipElement.remove();
        });
    }
    
    // 3秒后自动关闭
    setTimeout(() => {
        if (tipElement.parentNode) {
            tipElement.remove();
        }
    }, 3000);
}

// 添加密码强度样式
const strengthStyle = document.createElement('style');
strengthStyle.textContent = `
    .password-strength {
        margin-top: 5px;
        padding: 5px 10px;
        border-radius: 4px;
        font-size: 12px;
        font-weight: bold;
    }
    
    .strength-very-weak {
        background-color: #ffcccc;
        color: #d32f2f;
    }
    
    .strength-weak {
        background-color: #ffe0b2;
        color: #f57c00;
    }
    
    .strength-medium {
        background-color: #fff3cd;
        color: #856404;
    }
    
    .strength-strong {
        background-color: #d4edda;
        color: #155724;
    }
`;
document.head.appendChild(strengthStyle);

// 简单的表单验证
function validateForm(form) {
    const inputs = form.querySelectorAll('input[required]');
    let isValid = true;
    
    inputs.forEach(input => {
        if (!input.value.trim()) {
            input.classList.add('is-invalid');
            isValid = false;
        } else {
            input.classList.remove('is-invalid');
            input.classList.add('is-valid');
        }
    });
    
    return isValid;
}

// 为所有表单添加基本验证
document.addEventListener('DOMContentLoaded', () => {
    const forms = document.querySelectorAll('form');
    forms.forEach(form => {
        form.addEventListener('submit', (e) => {
            if (!validateForm(form)) {
                e.preventDefault();
                showAITip('请填写所有必填字段');
            }
        });
    });
});

// 图片延迟加载
if ('IntersectionObserver' in window) {
    const observer = new IntersectionObserver((entries) => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                const img = entry.target;
                if (img.dataset.src) {
                    img.src = img.dataset.src;
                    observer.unobserve(img);
                }
            }
        });
    });
    
    document.querySelectorAll('img[data-src]').forEach(img => {
        observer.observe(img);
    });
}