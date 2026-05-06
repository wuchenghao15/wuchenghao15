
// 兼容性检查和回退方案
(function() {
    'use strict';
    
    // 检查Array.includes支持
    if (!Array.prototype.includes) {
        Array.prototype.includes = function(searchElement, fromIndex) {
            fromIndex = parseInt(fromIndex) || 0;
            for (let i = fromIndex; i < this.length; i++) {
                if (this[i] === searchElement) {
                    return true;
                }
            }
            return false;
        };
    }
})();

// 兼容性检查和回退方案
(function() {
    'use strict';
    
    // 检查Array.includes支持
    if (!Array.prototype.includes) {
        Array.prototype.includes = function(searchElement, fromIndex) {
            fromIndex = parseInt(fromIndex) || 0;
            for (let i = fromIndex; i < this.length; i++) {
                if (this[i] === searchElement) {
                    return true;
                }
            }
            return false;
        };
    }
})();

// 兼容性检查和回退方案
(function() {
    'use strict';
    
    // 检查Array.includes支持
    if (!Array.prototype.includes) {
        Array.prototype.includes = function(searchElement, fromIndex) {
            fromIndex = parseInt(fromIndex) || 0;
            for (let i = fromIndex; i < this.length; i++) {
                if (this[i] === searchElement) {
                    return true;
                }
            }
            return false;
        };
    }
})();
// 添加ES6+兼容性支持
if (typeof Promise === "undefined") {
    // 这里可以添加具体的polyfill代码
    console.warn("This browser requires a polyfill for ES6+ features");
}

const el_unlock_password = document.getElementById('unlock-password');
// 切换密码可见性
function togglePassword() {
    const passwordInput = document.getElementById('unlock-password');
    const toggleBtn = passwordInput.nextElementSibling;
    const icon = toggleBtn.querySelector('i');
    
    if (passwordInput.type === 'password') {
        passwordInput.type = 'text';
        icon.classList.remove('fa-eye');
        icon.classList.add('fa-eye-slash');
    } else {
        passwordInput.type = 'password';
        icon.classList.remove('fa-eye-slash');
        icon.classList.add('fa-eye');
    }
}

// 获取URL参数
function getUrlParam(name) {
    const urlParams = new URLSearchParams(window.location.search);
    return urlParams.get(name);
}

// 显示错误信息
function showError(message) {
    const errorElement = document.getElementById('unlock-error');
    errorElement.textContent = message;
}

// 记录锁定事件
function recordLockEvent(eventType, details = {}) {
    try {
        const eventData = {
            eventType: eventType,
            details: {
                ...details,
                returnUrl: getUrlParam('returnUrl'),
                timestamp: new Date().toISOString(),
                userAgent: navigator.userAgent,
                url: window.location.href
            }
        };
        
        console.log(`[锁定事件] ${eventType}:`, eventData);
        
        // 发送事件到服务器
        fetch('/api/security/event', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(eventData)
        })
        .then(response => response.json())
        .then(data => {
            console.log('事件记录成功:', data);
        })
        .catch(error => {
            console.error('事件记录失败:', error);
        });
    } catch (error) {
        console.error('记录锁定事件失败:', error);
    }
}

// 显示加载中
function showLoading() {
    const loadingOverlay = document.createElement('div');
    loadingOverlay.className = 'loading-overlay';
    loadingOverlay.id = 'loading-overlay';
    loadingOverlay.innerHTML = `
        <div class="loading-spinner">
            <div class="spinner"></div>
            <div class="loading-text">验证中...</div>
        </div>
    `;
    document.body.appendChild(loadingOverlay);
}

// 隐藏加载中
function hideLoading() {
    const loadingOverlay = document.getElementById('loading-overlay');
    if (loadingOverlay) {
        document.body.removeChild(loadingOverlay);
    }
}

// 解锁系统
function unlockSystem(password) {
    showLoading();
    
    // 获取当前用户信息
    const userInfo = JSON.parse(localStorage.getItem('mtscos_user_info'));
    const token = localStorage.getItem('mtscos_auth_token');
    
    // 构建解锁请求数据
    const unlockData = {
        password: password,
        userInfo: userInfo,
        token: token
    };
    
    // 发送解锁请求
    fetch('/api/auth/unlock', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify(unlockData)
    })
    .then(response => response.json())
    .then(data => {
        hideLoading();
        
        if (data.success) {
            // 记录解锁成功事件
            recordLockEvent('unlock_success', {
                action: 'unlock_system',
                userId: userInfo?.username,
                userRole: userInfo?.role
            });
            
            // 解锁成功，重定向回原页面
            const returnUrl = getUrlParam('returnUrl') || '/html/dashboard.html';
            window.location.href = returnUrl;
        } else {
            // 记录解锁失败事件
            recordLockEvent('unlock_failure', {
                action: 'unlock_failed',
                userId: userInfo?.username,
                errorMessage: data.message || '解锁失败，请检查密码'
            });
            
            showError(data.message || '解锁失败，请检查密码');
        }
    })
    .catch(error => {
        hideLoading();
        
        // 记录解锁错误事件
        recordLockEvent('unlock_error', {
            action: 'unlock_error',
            errorMessage: error.message || '网络错误'
        });
        
        showError('网络错误，请稍后重试');
        console.error('解锁请求失败:', error);
    });
}

// 初始化表单
document.addEventListener('DOMContentLoaded', function() {
    // 记录锁定页面访问事件
    recordLockEvent('lock_page_access', {
        reason: 'session_timeout',
        action: 'access_lock_page'
    });
    
    const unlockForm = document.getElementById('unlockForm');
    
    unlockForm.addEventListener('submit', function(e) {
        e.preventDefault();
        
        const password = document.getElementById('unlock-password').value;
        
        if (!password) {
            showError('请输入密码');
            return;
        }
        
        // 记录解锁尝试事件
        recordLockEvent('unlock_attempt', {
            action: 'submit_unlock_form',
            passwordLength: password.length
        });
        
        unlockSystem(password);
    });
});

// 防止刷新绕过锁定
window.onbeforeunload = function(e) {
    const confirmationMessage = '警告：刷新页面将保持系统锁定状态！';
    e.returnValue = confirmationMessage;
    return confirmationMessage;
};

// 监控开发者工具
document.addEventListener('keydown', function(e) {
    // 禁止 F5 刷新
    if (e.key === 'F5') {
        e.preventDefault();
        showError('禁止使用F5刷新页面！');
    }
    
    // 禁止 Ctrl+R 刷新
    if ((e.ctrlKey || e.metaKey) && e.key === 'r') {
        e.preventDefault();
        showError('禁止使用快捷键刷新页面！');
    }
    
    // 禁止 Ctrl+Shift+I 打开开发者工具
    if ((e.ctrlKey || e.metaKey) && e.shiftKey && e.key === 'I') {
        e.preventDefault();
        showError('禁止打开开发者工具！');
    }
});

// 禁止右键菜单
document.addEventListener('contextmenu', function(e) {
    e.preventDefault();
});