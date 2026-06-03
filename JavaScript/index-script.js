// DOM加载完成后执行
window.addEventListener('DOMContentLoaded', function() {
    // 添加表单验证功能
    const loginForm = document.getElementById('loginForm');
    if (loginForm) {
        loginForm.addEventListener('submit', function(event) {
            // 阻止默认提交
            event.preventDefault();
            
            // 获取表单元素
            const username = document.getElementById('username').value.trim();
            const password = document.getElementById('password').value;
            const errorMessage = document.getElementById('error-message');
            const errorText = document.getElementById('error-text');
            
            // 重置错误信息
            errorMessage.style.display = 'none';
            
            // 验证用户名
            if (!username) {
                errorText.textContent = '请输入用户名';
                errorMessage.style.display = 'flex';
                return;
            }
            
            // 验证密码
            if (!password) {
                errorText.textContent = '请输入密码';
                errorMessage.style.display = 'flex';
                return;
            }
            
            // 密码强度验证
            if (password.length < 6) {
                errorText.textContent = '密码长度至少为6位';
                errorMessage.style.display = 'flex';
                return;
            }
            
            // 模拟登录请求
            console.log('登录请求已提交，正在验证...');
            
            // 这里应该是实际的登录逻辑
            // 为了演示，我们延迟后显示成功消息
            setTimeout(function() {
                alert('登录验证成功！');
                // 实际项目中这里会重定向或执行其他操作
            }, 1000);
        });
    }
    
    // Vikey设备自动检测功能
    let detectionInterval;
    let lastDeviceState = false;
    
    // 获取UI元素
    const vkeyStatusLabel = document.getElementById('vkey-status');
    const hiddenVkeyInput = document.getElementById('vkey');
    let vkeyText = null;
    if (vkeyStatusLabel) {
        vkeyText = vkeyStatusLabel.querySelector('.vkey-text');
    }
    
    // 开始定期检测Vikey设备（仅当vkey-status元素存在时）
    function startVikeyDetection() {
        if (!vkeyStatusLabel || !vkeyText) {
            console.log('Vikey状态元素不存在，跳过设备检测');
            return;
        }
        
        // 立即执行一次检测
        detectVikeyDevice();
        
        // 设置定期检测（每2秒）
        detectionInterval = setInterval(detectVikeyDevice, 2000);
    }
    
    // 检测Vikey设备
    async function detectVikeyDevice() {
        try {
            // 检查window.vikeyAPI是否已加载
            if (!window.vikeyAPI) {
                console.warn('VikeyAPI尚未加载');
                return;
            }
            
            // 使用增强版VikeyAPI查找设备
            const findResult = await window.vikeyAPI.VikeyFind();
            
            if (findResult.code === window.vikeyAPI.VIKEY_SUCCESS && findResult.count > 0) {
                // 设备已检测到
                if (!lastDeviceState) {
                    lastDeviceState = true;
                    updateVikeyStatus(true, findResult.devices[0]);
                    
                    // 生成模拟的vkey认证码（实际应用中应从设备获取）
                    const mockVkey = `VIKEY-${Date.now()}-${Math.random().toString(36).substr(2, 9).toUpperCase()}`;
                    hiddenVkeyInput.value = mockVkey;
                    
                    console.log('已检测到Vikey设备:', findResult.devices[0]);
                    
                    // 使用模拟的vkey进行自动验证
                    try {
                        const verifyResult = await window.vikeyAPI.VikeyVerifyAuthCode(mockVkey);
                        if (verifyResult.valid) {
                            console.log('Vikey设备验证成功，令牌:', verifyResult.token);
                            localStorage.setItem('vikeyAuthToken', verifyResult.token);
                        }
                    } catch (verifyError) {
                        console.error('Vikey验证失败:', verifyError);
                    }
                }
            } else {
                // 设备未检测到
                if (lastDeviceState) {
                    lastDeviceState = false;
                    updateVikeyStatus(false);
                    hiddenVkeyInput.value = '';
                    localStorage.removeItem('vikeyAuthToken');
                }
            }
        } catch (error) {
            console.error('Vikey设备检测失败:', error);
            if (lastDeviceState) {
                lastDeviceState = false;
                updateVikeyStatus(false);
                hiddenVkeyInput.value = '';
            }
        }
    }
    
    // 更新Vikey状态显示
    function updateVikeyStatus(isDetected, device = null) {
        if (isDetected && device) {
            vkeyStatusLabel.classList.remove('status-error');
            vkeyStatusLabel.classList.add('status-detected');
            
            // 根据设备类型显示不同信息
            let deviceTypeText = '加密狗';
            if (device.type === window.vikeyAPI.VikeyType.ViKeySecure) {
                deviceTypeText = '高安全性加密狗';
            } else if (device.type === window.vikeyAPI.VikeyType.ViKeyCloud) {
                deviceTypeText = '云验证型加密狗';
            } else if (device.type === window.vikeyAPI.VikeyType.ViKeyMobile) {
                deviceTypeText = '移动设备验证器';
            }
            
            vkeyText.textContent = `已检测到Vikey ${deviceTypeText}（ID: ${device.id.substring(0, 4)}****）`;
        } else {
            vkeyStatusLabel.classList.remove('status-detected');
            vkeyStatusLabel.classList.add('status-error');
            vkeyText.textContent = '未检测到Vikey设备';
        }
    }
    
    // 实现第三方登录功能
    function initThirdPartyLogin() {
        const socialButtons = document.querySelectorAll('.social-btn');
        
        socialButtons.forEach(button => {
            button.addEventListener('click', function() {
                const provider = this.classList.contains('github') ? 'github' :
                                this.classList.contains('google') ? 'google' :
                                this.classList.contains('qq') ? 'qq' :
                                this.classList.contains('wechat') ? 'wechat' :
                                this.classList.contains('hotmail') ? 'microsoft' : null;
                
                if (provider) {
                    initiateOAuthLogin(provider);
                }
            });
        });
    }
    
    // 官方OAuth登录配置
    const oauthConfig = {
        github: {
            clientId: 'YOUR_GITHUB_CLIENT_ID',
            redirectUri: 'http://localhost:8888/auth/github/callback',
            authEndpoint: 'https://github.com/login/oauth/authorize',
            scope: 'user:email'
        },
        google: {
            clientId: 'YOUR_GOOGLE_CLIENT_ID',
            redirectUri: 'http://localhost:8888/auth/google/callback',
            authEndpoint: 'https://accounts.google.com/o/oauth2/v2/auth',
            scope: 'profile email'
        },
        qq: {
            clientId: 'YOUR_QQ_APP_ID',
            redirectUri: 'http://localhost:8888/auth/qq/callback',
            authEndpoint: 'https://graph.qq.com/oauth2.0/authorize'
        },
        microsoft: {
            clientId: 'YOUR_MICROSOFT_CLIENT_ID',
            redirectUri: 'http://localhost:8888/auth/microsoft/callback',
            authEndpoint: 'https://login.microsoftonline.com/common/oauth2/v2.0/authorize',
            scope: 'openid profile email'
        }
    };
    
    // 检查OAuth回调
    function checkOAuthCallback() {
        const urlParams = new URLSearchParams(window.location.search);
        const code = urlParams.get('code');
        const state = urlParams.get('state');
        const pathname = window.location.pathname;
        
        // 检查是否是回调路径
        if (pathname.includes('/auth/')) {
            const providerMatch = pathname.match(/\/auth\/(\w+)\/callback/);
            if (providerMatch && code) {
                const provider = providerMatch[1];
                handleOAuthCallback(provider, code, state);
                return true;
            }
        }
        return false;
    }
    
    // 处理OAuth回调
    function handleOAuthCallback(provider, code, state) {
        // 验证state参数防止CSRF攻击
        const savedState = localStorage.getItem(`oauth_state_${provider}`);
        if (savedState && savedState === state) {
            localStorage.removeItem(`oauth_state_${provider}`);
            console.log(`${provider}授权码:`, code);
            
            // 显示加载状态
            const loginButton = document.getElementById('login-button');
            if (loginButton) {
                loginButton.classList.add('loading');
            }
            
            // 模拟后端验证过程
            setTimeout(() => {
                const mockToken = `OAUTH_${provider.toUpperCase()}_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
                
                // 存储token
                localStorage.setItem(`oauth_token_${provider}`, mockToken);
                localStorage.setItem('last_login_method', provider);
                
                // 显示成功消息
                const providerNames = {
                    github: 'GitHub',
                    google: 'Google',
                    qq: 'QQ',
                    wechat: '微信',
                    microsoft: 'Microsoft'
                };
                
                alert(`通过${providerNames[provider]}登录成功！即将跳转到系统`);
                console.log(`${provider}登录成功，令牌:`, mockToken);
                
                // 移除URL中的code参数
                window.history.replaceState({}, document.title, window.location.pathname);
                
                if (loginButton) {
                    loginButton.classList.remove('loading');
                }
            }, 1000);
        }
    }
    
    // 发起OAuth登录 - 接入官方API
    function initiateOAuthLogin(provider) {
        console.log(`开始${provider}登录流程`);
        
        // 显示加载状态
        const loginButton = document.getElementById('login-button');
        loginButton.classList.add('loading');
        
        if (oauthConfig[provider]) {
            const config = oauthConfig[provider];
            let authUrl = `${config.authEndpoint}?client_id=${config.clientId}&redirect_uri=${encodeURIComponent(config.redirectUri)}&response_type=code`;
            
            // 添加scope参数（如果有）
            if (config.scope) {
                authUrl += `&scope=${encodeURIComponent(config.scope)}`;
            }
            
            // 添加state参数防止CSRF攻击
            const state = Math.random().toString(36).substring(2, 15) + Math.random().toString(36).substring(2, 15);
            localStorage.setItem(`oauth_state_${provider}`, state);
            authUrl += `&state=${state}`;
            
            // 对于微信，特殊处理
            if (provider === 'wechat') {
                showWechatQrCode();
                loginButton.classList.remove('loading');
                return;
            }
            
            // 跳转到授权页面
            console.log(`跳转到${provider}授权页面:`, authUrl);
            window.location.href = authUrl;
        } else {
            console.error(`未配置${provider}的OAuth设置`);
            alert('该登录方式暂不可用，请稍后再试');
            loginButton.classList.remove('loading');
        }
    }
    
    // 微信二维码登录 - 接入官方API
    function showWechatQrCode() {
        // 创建二维码容器
        const qrContainer = document.createElement('div');
        qrContainer.className = 'wechat-qr-container';
        
        // 生成微信扫码登录状态标识
        const loginState = 'wechat_login_' + Date.now();
        
        // 使用微信开放平台的官方二维码生成（这里使用公共二维码API作为示例）
        const qrCodeUrl = `https://api.qrserver.com/v1/create-qr-code/?size=150x150&data=WECHAT_OAUTH_${loginState}`;
        
        qrContainer.innerHTML = `
            <div class="qr-overlay"></div>
            <div class="qr-content">
                <div class="qr-header">
                    <h3>微信扫码登录</h3>
                    <button class="qr-close">&times;</button>
                </div>
                <div class="qr-body">
                    <div class="qr-code-container">
                        <img src="${qrCodeUrl}" alt="微信登录二维码" class="wechat-qr-image">
                    </div>
                    <p class="qr-instruction">请使用微信扫描二维码</p>
                    <div class="qr-status">正在等待扫码...</div>
                    <div class="qr-timer">有效期5分钟</div>
                </div>
            </div>
        `;
        
        // 添加到页面
        document.body.appendChild(qrContainer);
        
        // 添加关闭功能
        const closeButton = qrContainer.querySelector('.qr-close');
        closeButton.addEventListener('click', function() {
            document.body.removeChild(qrContainer);
        });
        
        // 模拟扫码检测
        let remainingTime = 300; // 5分钟 = 300秒
        const timerElement = qrContainer.querySelector('.qr-timer');
        const statusElement = qrContainer.querySelector('.qr-status');
        
        const timerInterval = setInterval(() => {
            remainingTime--;
            const minutes = Math.floor(remainingTime / 60);
            const seconds = remainingTime % 60;
            timerElement.textContent = `有效期${minutes}分${seconds}秒`;
            
            // 模拟随机扫码成功（实际应用中应通过后端API检查）
            if (remainingTime % 5 === 0 && Math.random() > 0.8) {
                statusElement.textContent = '扫码成功，正在登录...';
                
                // 模拟登录成功延迟
                setTimeout(() => {
                    const mockToken = `WECHAT_OAUTH_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
                    localStorage.setItem('oauth_token_wechat', mockToken);
                    localStorage.setItem('last_login_method', 'wechat');
                    
                    alert('通过微信登录成功！即将跳转到系统');
                    console.log('微信登录成功，令牌:', mockToken);
                    
                    // 清理
                    clearInterval(timerInterval);
                    document.body.removeChild(qrContainer);
                }, 1500);
            }
            
            // 二维码过期
            if (remainingTime <= 0) {
                clearInterval(timerInterval);
                statusElement.textContent = '二维码已过期';
                timerElement.textContent = '有效期0分0秒';
                
                // 自动关闭
                setTimeout(() => {
                    document.body.removeChild(qrContainer);
                }, 2000);
            }
        }, 1000);
    }
    
    // 更新IP和地理位置信息（使用默认值避免API调用错误）
    function updateIPAndLocation() {
        // 直接使用默认值
        const ipElement = document.getElementById('user-ip');
        if (ipElement) {
            ipElement.textContent = 'IP: 192.168.1.100';
        }
        
        // 移除位置信息，不再添加或更新位置元素
        const locationElement = document.getElementById('user-location');
        if (locationElement) {
            const locationRow = locationElement.closest('tr');
            if (locationRow) {
                locationRow.remove();
            }
        }
    }
    
    // 初始化时检查OAuth回调
    if (!checkOAuthCallback()) {
        console.log('不是OAuth回调，继续正常流程');
    }
    
    // 获取IP和地理位置信息
    updateIPAndLocation();
    
    // 移除在线人数统计相关代码
});

// 粒子背景效果模拟
function createParticles() {
    const particlesContainer = document.getElementById('particles-js');
    const particleCount = 50;
    
    for (let i = 0; i < particleCount; i++) {
        const particle = document.createElement('div');
        particle.style.position = 'absolute';
        particle.style.width = `${Math.random() * 5 + 1}px`;
        particle.style.height = `${Math.random() * 5 + 1}px`;
        particle.style.backgroundColor = `rgba(22, 93, 255, ${Math.random() * 0.3 + 0.1})`;
        particle.style.borderRadius = '50%';
        particle.style.left = `${Math.random() * 100}%`;
        particle.style.top = `${Math.random() * 100}%`;
        particle.style.opacity = Math.random() * 0.7 + 0.3;
        particle.style.animation = `float ${Math.random() * 10 + 10}s linear infinite`;
        particle.style.animationDelay = `${Math.random() * 5}s`;
        
        particlesContainer.appendChild(particle);
    }
}

// 添加浮动动画
const floatStyle = document.createElement('style');
floatStyle.textContent = `
    @keyframes float {
        0% {
            transform: translateY(0) translateX(0);
        }
        25% {
            transform: translateY(-50px) translateX(20px);
        }
        50% {
            transform: translateY(-100px) translateX(0);
        }
        75% {
            transform: translateY(-50px) translateX(-20px);
        }
        100% {
            transform: translateY(0) translateX(0);
        }
    }
`;
document.head.appendChild(floatStyle);

// 初始化粒子
createParticles();

// 防盗链脚本
window.addEventListener('DOMContentLoaded', function() {
    // 防止iframe嵌套
    if (window.top !== window.self) {
        window.top.location = window.location;
    }
    
    // 禁用右键菜单
    document.addEventListener('contextmenu', function(e) {
        e.preventDefault();
    });
    
    // 禁用复制粘贴（可选）
    document.addEventListener('copy', function(e) {
        e.preventDefault();
        return false;
    });
});

// 删除按钮功能实现
function setupDeleteButtons() {
    const deleteButtons = document.querySelectorAll('.delete-btn');
    deleteButtons.forEach(button => {
        button.addEventListener('click', function() {
            // 直接删除对应的行
            const row = this.closest('tr');
            if (row) {
                row.remove();
            }
        });
    });
}

// 更新时间函数 - 使用new Date()实现
function updateCurrentTime() {
    const now = new Date();
    const options = { year: 'numeric', month: 'long', day: 'numeric', hour: '2-digit', minute: '2-digit', second: '2-digit' };
    const formattedTime = now.toLocaleString('zh-CN', options);
    
    const timeElement = document.getElementById('current-time');
    
    // 直接更新时间文本，移除删除按钮相关代码
    if (timeElement) {
        timeElement.textContent = formattedTime;
    }
}

// 初始化时间更新
setInterval(updateCurrentTime, 1000);
updateCurrentTime();