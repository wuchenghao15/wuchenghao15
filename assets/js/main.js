// 密码显示/隐藏切换
function setupPasswordToggle() {
    const togglePassword = document.getElementById('toggle-password');
    const password = document.getElementById('password');
    
    if (togglePassword && password) {
        togglePassword.addEventListener('click', function() {
            const type = password.getAttribute('type') === 'password' ? 'text' : 'password';
            password.setAttribute('type', type);
            this.textContent = type === 'password' ? '显示密码' : '隐藏密码';
        });
    }
}

// 验证码生成与刷新
function setupCaptcha() {
    const captchaImage = document.getElementById('captcha-image');
    
    if (captchaImage) {
        // 生成随机验证码
        function generateCaptcha() {
            const chars = '0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz';
            let captcha = '';
            for (let i = 0; i < 4; i++) {
                captcha += chars.charAt(Math.floor(Math.random() * chars.length));
            }
            return captcha;
        }
        
        // 刷新验证码
        function refreshCaptcha() {
            const captcha = generateCaptcha();
            captchaImage.textContent = captcha;
            
            // 随机生成验证码背景和文字颜色
            const colors = ['#FF6B6B', '#4ECDC4', '#45B7D1', '#FFA07A', '#98D8C8'];
            captchaImage.style.backgroundColor = colors[Math.floor(Math.random() * colors.length)];
            captchaImage.style.color = '#FFFFFF';
        }
        
        captchaImage.addEventListener('click', refreshCaptcha);
        // 初始化生成验证码
        refreshCaptcha();
    }
}

// 登录表单提交处理
function setupLoginForm() {
    const loginForm = document.getElementById('login-form');
    
    if (loginForm) {
        loginForm.addEventListener('submit', function(event) {
            event.preventDefault();
            
            // 获取表单数据
            const username = document.getElementById('username').value;
            const password = document.getElementById('password').value;
            const captcha = document.getElementById('captcha').value;
            
            // 表单验证
            if (!username || !password || !captcha) {
                alert('请填写所有必填字段');
                return;
            }
            
            console.log('登录信息:', { username, password, captcha });
            
            // 模拟登录过程
            const loginBtn = this.querySelector('button[type="submit"]');
            const originalText = loginBtn.textContent;
            
            loginBtn.disabled = true;
            loginBtn.textContent = '登录中...';
            
            // 模拟API调用，通过UrInfoChk.php处理登录
            setTimeout(() => {
                // 这里应该是实际的API调用
                // 例如：fetch('UrInfoChk.php', { method: 'POST', body: formData })
                
                // 模拟登录成功
                loginBtn.textContent = '登录成功';
                loginBtn.style.backgroundColor = '#4CAF50';
                
                // 设置会话超时（15分钟）
                setupSessionTimeout();
                
                // 跳转到首页
                setTimeout(() => {
                    window.location.href = 'dashboard.html';
                }, 1500);
            }, 2000);
        });
    }
}

// HardwareKey硬件密钥登录相关
function setupHardwareKeyLogin() {
    const findHardwareKeyBtn = document.getElementById('find-hardwareKey');
    const hardwareKeyLoginBtn = document.getElementById('hardwareKey-login');
    const hardwareKeyStatus = document.getElementById('hardwareKey-status');
    
    if (findHardwareKeyBtn && hardwareKeyLoginBtn && hardwareKeyStatus) {
        // 查找HardwareKey设备
        findHardwareKeyBtn.addEventListener('click', function() {
            hardwareKeyStatus.textContent = '正在查找HardwareKey设备...';
            this.disabled = true;
            
            // 模拟查找HardwareKey设备的过程
            setTimeout(() => {
                // 在实际应用中，这里应该调用HardwareKey API进行设备查找
                // 例如：HardwareKey.FindDevice();
                hardwareKeyStatus.textContent = '找到HardwareKey设备！';
                hardwareKeyLoginBtn.disabled = false;
                this.disabled = false;
            }, 2000);
        });
        
        // 使用HardwareKey登录
        hardwareKeyLoginBtn.addEventListener('click', function() {
            hardwareKeyStatus.textContent = '正在验证HardwareKey设备...';
            this.disabled = true;
            
            // 模拟HardwareKey验证过程
            setTimeout(() => {
                // 在实际应用中，这里应该调用HardwareKey API进行验证
                // 例如：HardwareKey.Verify();
                
                // 模拟验证成功
                hardwareKeyStatus.textContent = 'HardwareKey验证成功！';
                
                // 设置会话超时（15分钟）
                setupSessionTimeout();
                
                // 跳转到首页
                setTimeout(() => {
                    window.location.href = 'dashboard.html';
                }, 1500);
            }, 3000);
        });
    }
}

// 第三方登录按钮点击事件
function setupThirdPartyLogin() {
    // 登录方式配置
    const loginProviders = {
        'qq-login': { name: 'QQ', url: 'https://connect.qq.com/widget/qc_jssdk.js' },
        'wechat-login': { name: '微信', url: 'https://res.wx.qq.com/connect/zh_CN/htmledition/js/wxLogin.js' },
        'github-login': { name: 'GitHub', url: 'https://github.com/login/oauth/authorize' },
        'google-login': { name: 'Google', url: 'https://accounts.google.com/o/oauth2/v2/auth' },
        'hotmail-login': { name: 'Hotmail', url: 'https://login.live.com/oauth20_authorize.srf' },
        'email-login': { name: '邮箱', type: 'custom' },
        'phone-login': { name: '手机', type: 'custom' }
    };
    
    // 为每个登录按钮添加事件监听器
    Object.keys(loginProviders).forEach(buttonId => {
        const button = document.getElementById(buttonId);
        const provider = loginProviders[buttonId];
        
        if (button) {
            button.addEventListener('click', function() {
                console.log(`使用${provider.name}登录`);
                
                if (provider.type === 'custom') {
                    // 自定义登录流程（邮箱和手机）
                    if (buttonId === 'email-login') {
                        showEmailLoginDialog();
                    } else if (buttonId === 'phone-login') {
                        showPhoneLoginDialog();
                    }
                } else {
                    // 第三方OAuth登录
                    // 在实际应用中，这里应该重定向到第三方登录页面或打开授权弹窗
                    alert(`即将跳转到${provider.name}登录页面...`);
                    // 示例：window.location.href = `${provider.url}?client_id=YOUR_CLIENT_ID&redirect_uri=YOUR_REDIRECT_URI`;
                }
            });
        }
    });
}

// 邮箱登录对话框
// 创建自定义输入对话框
function createInputDialog(title, placeholder, callback) {
    // 创建对话框容器
    const dialog = document.createElement('div');
    dialog.style.cssText = `
        position: fixed;
        top: 0;
        left: 0;
        width: 100%;
        height: 100%;
        background-color: rgba(0, 0, 0, 0.5);
        display: flex;
        justify-content: center;
        align-items: center;
        z-index: 9999;
    `;
    
    // 创建对话框内容
    const dialogContent = document.createElement('div');
    dialogContent.style.cssText = `
        background-color: white;
        padding: 20px;
        border-radius: 8px;
        box-shadow: 0 4px 20px rgba(0, 0, 0, 0.3);
        width: 90%;
        max-width: 400px;
    `;
    
    // 添加标题
    const dialogTitle = document.createElement('h3');
    dialogTitle.textContent = title;
    dialogTitle.style.marginTop = '0';
    dialogContent.appendChild(dialogTitle);
    
    // 添加输入框
    const input = document.createElement('input');
    input.type = 'text';
    input.placeholder = placeholder;
    input.style.cssText = `
        width: 100%;
        padding: 10px;
        margin: 15px 0;
        border: 1px solid #ddd;
        border-radius: 4px;
        box-sizing: border-box;
        font-size: 16px;
    `;
    dialogContent.appendChild(input);
    
    // 创建按钮容器
    const buttonContainer = document.createElement('div');
    buttonContainer.style.cssText = `
        display: flex;
        justify-content: flex-end;
        gap: 10px;
    `;
    
    // 添加取消按钮
    const cancelButton = document.createElement('button');
    cancelButton.textContent = '取消';
    cancelButton.style.cssText = `
        padding: 8px 16px;
        background-color: #f1f1f1;
        border: none;
        border-radius: 4px;
        cursor: pointer;
        font-size: 14px;
    `;
    cancelButton.addEventListener('click', () => {
        document.body.removeChild(dialog);
        callback(null); // 用户取消
    });
    buttonContainer.appendChild(cancelButton);
    
    // 添加确定按钮
    const confirmButton = document.createElement('button');
    confirmButton.textContent = '确定';
    confirmButton.style.cssText = `
        padding: 8px 16px;
        background-color: #4CAF50;
        color: white;
        border: none;
        border-radius: 4px;
        cursor: pointer;
        font-size: 14px;
    `;
    confirmButton.addEventListener('click', () => {
        const value = input.value.trim();
        document.body.removeChild(dialog);
        callback(value);
    });
    buttonContainer.appendChild(confirmButton);
    
    // 添加按钮容器到对话框内容
    dialogContent.appendChild(buttonContainer);
    
    // 添加对话框到页面
    dialog.appendChild(dialogContent);
    document.body.appendChild(dialog);
    
    // 自动聚焦输入框
    input.focus();
}

// 邮箱登录对话框
function showEmailLoginDialog() {
    try {
        createInputDialog('邮箱登录', '请输入您的邮箱地址:', (email) => {
            if (!email) {
                return; // 用户取消输入
            }
            
            // 简单的邮箱格式验证
            const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
            if (!emailRegex.test(email)) {
                alert('请输入有效的邮箱地址');
                return;
            }
            
            alert(`验证码已发送至 ${email}，请查收并输入验证码完成登录。`);
            // 实际应用中，这里应该调用API发送验证码
            createInputDialog('输入验证码', '请输入邮箱验证码:', (verificationCode) => {
                if (verificationCode) {
                    // 验证验证码并登录
                    console.log('邮箱登录验证:', { email, verificationCode });
                    setupSessionTimeout();
                    alert('邮箱登录成功！');
                    window.location.href = 'dashboard.html';
                }
            });
        });
    } catch (error) {
        console.error('[main.js] 邮箱登录过程中发生错误:', error);
        alert('邮箱登录失败，请重试');
    }
}

// 手机登录对话框
function showPhoneLoginDialog() {
    try {
        createInputDialog('手机登录', '请输入您的手机号码:', (phone) => {
            if (!phone) {
                return; // 用户取消输入
            }
            
            // 简单的手机号格式验证
            const phoneRegex = /^1[3-9]\d{9}$/;
            if (!phoneRegex.test(phone)) {
                alert('请输入有效的手机号码');
                return;
            }
            
            alert(`验证码已发送至 ${phone}，请查收并输入验证码完成登录。`);
            // 实际应用中，这里应该调用API发送验证码
            createInputDialog('输入验证码', '请输入短信验证码:', (verificationCode) => {
                if (verificationCode) {
                    // 验证验证码并登录
                    console.log('手机登录验证:', { phone, verificationCode });
                    setupSessionTimeout();
                    alert('手机登录成功！');
                    window.location.href = 'dashboard.html';
                }
            });
        });
    } catch (error) {
        console.error('[main.js] 手机登录过程中发生错误:', error);
        alert('手机登录失败，请重试');
    }
}

// 初始化时间显示
function initTimeDisplay() {
    try {
        // 直接使用time_display.js中定义的函数
        if (typeof updateTimeDisplay === 'function') {
            updateTimeDisplay();
            setInterval(updateTimeDisplay, 1000);
        } else {
            console.error(`[main.js] 未找到updateTimeDisplay函数`);
            // 备用时间显示
            const updateTime = () => {
                const now = new Date();
                const timeElement = document.getElementById('current-time');
                if (timeElement) {
                    timeElement.textContent = now.toLocaleString('zh-CN');
                }
            };
            updateTime();
            setInterval(updateTime, 1000);
        }
    } catch (error) {
        console.error('[main.js] 初始化时间显示失败:', error);
    }
}

// 会话超时机制
function setupSessionTimeout() {
    const SESSION_TIMEOUT = 15 * 60 * 1000; // 15分钟
    let sessionTimer;
    let isSessionActive = true;
    
    // 清理会话计时器
    function clearSessionTimer() {
        if (sessionTimer) {
            clearTimeout(sessionTimer);
            sessionTimer = null;
        }
    }
    
    // 重置会话计时器
    function resetSessionTimer() {
        if (!isSessionActive) return; // 如果会话已失效，不再重置
        
        clearSessionTimer();
        sessionTimer = setTimeout(() => {
            // 会话超时，自动登出
            isSessionActive = false;
            console.warn('登录会话已超时');
            
            // 显示超时提示
            const timeoutMessage = document.createElement('div');
            timeoutMessage.style.cssText = `
                position: fixed;
                top: 50%;
                left: 50%;
                transform: translate(-50%, -50%);
                background: #ff4444;
                color: white;
                padding: 20px;
                border-radius: 8px;
                z-index: 10000;
                text-align: center;
            `;
            timeoutMessage.innerHTML = '登录会话已超时，正在跳转到登录页面...';
            document.body.appendChild(timeoutMessage);
            
            // 延迟跳转，让用户看到提示
            setTimeout(() => {
                window.location.href = 'index.html';
            }, 2000);
        }, SESSION_TIMEOUT);
    }
    
    // 初始启动计时器
    resetSessionTimer();
    
    // 监听用户活动，重置计时器
    const activityEvents = ['mousemove', 'keypress', 'click', 'scroll', 'touchstart'];
    activityEvents.forEach(eventType => {
        document.addEventListener(eventType, resetSessionTimer, { passive: true });
    });
    
    // 页面卸载时清理
    window.addEventListener('beforeunload', clearSessionTimer);
    
    console.log('会话超时机制已设置，15分钟无活动将自动登出');
    
    // 返回清理函数，用于手动清理
    return {
        clearSessionTimer,
        resetSessionTimer,
        isSessionActive: () => isSessionActive
    };
}

// 安全机制：XSS防护
function setupXSSProtection() {
    // 对用户输入进行编码
    window.encodeHTML = function(str) {
        return str
            .replace(/&/g, '&amp;')
            .replace(/</g, '&lt;')
            .replace(/>/g, '&gt;')
            .replace(/"/g, '&quot;')
            .replace(/'/g, '&#039;');
    };
    
    // 验证URL参数，防止XSS攻击
    window.validateUrlParams = function() {
        const params = new URLSearchParams(window.location.search);
        for (const [key, value] of params) {
            if (value.match(/<script|javascript:/i)) {
                console.warn('潜在的XSS攻击被阻止:', key, value);
                return false;
            }
        }
        return true;
    };
    
    // 验证URL参数
    validateUrlParams();
}

// 页面初始化
function initPage() {
    // 安全检查
    setupXSSProtection();
    
    // 初始化表单功能
    setupPasswordToggle();
    setupCaptcha();
    setupLoginForm();
    
    // 初始化登录方式
    setupThirdPartyLogin();
    
    // 初始化时间显示
    initTimeDisplay();
    
    console.log('页面初始化完成');
}

// 当DOM加载完成后初始化页面
document.addEventListener('DOMContentLoaded', initPage);