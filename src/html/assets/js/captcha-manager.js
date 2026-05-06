
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
// 验证码管理器

/**
 * 生成验证码
 * @param {string} type - 验证码类型 ('login' 或 'register')
 * @returns {Promise<void>}
 */
async function generateCaptcha(type) {
    try {
        // 显示加载状态
        const captchaDisplay = document.getElementById(`${type}-captcha-display`);
        if (captchaDisplay) {
            captchaDisplay.innerHTML = '<i class="fas fa-spinner fa-spin"></i>';
        }
        
        // 调用Python后端API生成验证码
        const response = await fetch('http://localhost:8081/python/api/captcha/generate');
        const data = await response.json();
        
        if (data.success) {
            // 保存验证码令牌到sessionStorage
            sessionStorage.setItem(`${type}_captcha_token`, data.token);
            
            // 显示验证码
            if (captchaDisplay) {
                captchaDisplay.innerHTML = generateCaptchaHTML(data.captcha);
            }
        } else {
            console.error('生成验证码失败:', data.message);
            if (captchaDisplay) {
                captchaDisplay.innerHTML = '<span style="color: red;">验证码生成失败</span>';
            }
        }
    } catch (error) {
        console.error('生成验证码错误:', error);
        const captchaDisplay = document.getElementById(`${type}-captcha-display`);
        if (captchaDisplay) {
            captchaDisplay.innerHTML = '<span style="color: red;">网络错误</span>';
        }
    }
}

/**
 * 生成验证码HTML（添加干扰和样式）
 * @param {string} captcha - 验证码字符串
 * @returns {string} 验证码HTML
 */
function generateCaptchaHTML(captcha) {
    let html = '';
    const colors = ['#3498db', '#e74c3c', '#2ecc71', '#f39c12', '#9b59b6'];
    
    for (let i = 0; i < captcha.length; i++) {
        const char = captcha[i];
        const color = colors[Math.floor(Math.random() * colors.length)];
        const rotate = (Math.random() - 0.5) * 30; // -15 到 15 度的旋转
        
        html += `<span style="color: ${color}; transform: rotate(${rotate}deg); display: inline-block; margin: 0 2px;">${char}</span>`;
    }
    
    // 添加干扰线
    for (let i = 0; i < 3; i++) {
        const color = colors[Math.floor(Math.random() * colors.length)];
        const width = Math.random() * 2 + 1;
        const top = Math.random() * 30 + 5;
        const left = 0;
        const right = 100;
        
        html += `<div style="position: absolute; top: ${top}px; left: ${left}px; width: ${right}px; height: ${width}px; background-color: ${color}; opacity: 0.3; transform: rotate(${Math.random() * 360}deg);"></div>`;
    }
    
    return html;
}

/**
 * 验证验证码
 * @param {string} type - 验证码类型 ('login' 或 'register')
 * @param {string} userInput - 用户输入的验证码
 * @returns {Promise<boolean>} 验证结果
 */
async function validateCaptcha(type, userInput) {
    try {
        const token = sessionStorage.getItem(`${type}_captcha_token`);
        
        if (!token) {
            return false;
        }
        
        // 调用Python后端API验证验证码
        const response = await fetch('http://localhost:8081/python/api/captcha/verify', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ token, captcha: userInput.toUpperCase() })
        });
        
        const data = await response.json();
        return data.success;
    } catch (error) {
        console.error('验证验证码错误:', error);
        return false;
    }
}

/**
 * 初始化验证码
 */
async function initCaptcha() {
    // 初始化登录表单验证码
    await generateCaptcha('login');
    
    // 初始化注册表单验证码
    await generateCaptcha('register');
}

// 页面加载完成后初始化验证码
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', initCaptcha);
} else {
    initCaptcha();
}

// 绑定验证码刷新按钮
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', function() {
        const loginCaptchaBtn = document.getElementById('login-captcha-btn');
        if (loginCaptchaBtn) {
            loginCaptchaBtn.addEventListener('click', function() {
                generateCaptcha('login');
            });
        }
        
        const registerCaptchaBtn = document.getElementById('register-captcha-btn');
        if (registerCaptchaBtn) {
            registerCaptchaBtn.addEventListener('click', function() {
                generateCaptcha('register');
            });
        }
    });
} else {
    const loginCaptchaBtn = document.getElementById('login-captcha-btn');
    if (loginCaptchaBtn) {
        loginCaptchaBtn.addEventListener('click', function() {
            generateCaptcha('login');
        });
    }
    
    const registerCaptchaBtn = document.getElementById('register-captcha-btn');
    if (registerCaptchaBtn) {
        registerCaptchaBtn.addEventListener('click', function() {
            generateCaptcha('register');
        });
    }
}
