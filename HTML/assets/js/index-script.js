// VERSION: 20251106.9fc34fccd7e47f8fe4035
// 用户验证管理器
class UserAuthenticationManager {
    constructor() {
        // 系统内置用户信息（实际项目中应加密存储或通过安全渠道获取）
        this.systemUsers = {
            'admin': {
                password: 'Admin123456',
                role: 'admin',
                source: 'system'
            },
            'test_user': {
                password: 'Test@123456',
                role: 'user',
                source: 'system'
            },
            'readonly': {
                password: 'Readonly@123',
                role: 'readonly',
                source: 'system'
            }
        };
    }

    // 验证用户凭证
    async authenticate(username, password) {
        // 1. 首先检查系统内置用户
        const systemUser = await this.checkSystemUsers(username, password);
        if (systemUser) {
            return {
                success: true,
                user: {
                    username: username,
                    role: systemUser.role,
                    source: 'system',
                    displayName: username
                }
            };
        }

        // 2. 检查远程数据库用户
        const dbUser = await this.checkRemoteDatabase(username, password);
        if (dbUser) {
            return {
                success: true,
                user: dbUser
            };
        }

        // 3. 检查第三方证人用户（模拟API调用）
        const thirdPartyUser = await this.checkThirdPartyWitness(username, password);
        if (thirdPartyUser) {
            return {
                success: true,
                user: thirdPartyUser
            };
        }

        // 所有验证方式都失败
        return {
            success: false,
            message: '用户名或密码错误，请重试'
        };
    }

    // 检查系统内置用户
    async checkSystemUsers(username, password) {
        return new Promise((resolve) => {
            // 模拟同步检查
            setTimeout(() => {
                const user = this.systemUsers[username];
                if (user && user.password === password) {
                    resolve(user);
                } else {
                    resolve(null);
                }
            }, 100);
        });
    }

    // 检查远程数据库用户
    async checkRemoteDatabase(username, password) {
        return new Promise((resolve) => {
            // 模拟API调用延迟
            setTimeout(() => {
                try {
                    // 模拟远程数据库查询
                    // 在实际项目中，这里应该是加密的API请求
                    console.log('查询远程数据库用户:', username);
                    
                    // 这里仅作为演示，实际项目中不应在前端硬编码数据库用户
                    // 假设特定模式的用户名通过远程数据库验证
                    if (username.startsWith('db_') && password.length >= 8) {
                        resolve({
                            username: username,
                            role: 'user',
                            source: 'database',
                            displayName: username.replace('db_', '')
                        });
                    } else {
                        resolve(null);
                    }
                } catch (error) {
                    console.error('远程数据库查询失败:', error);
                    resolve(null);
                }
            }, 300);
        });
    }

    // 检查第三方证人用户
    async checkThirdPartyWitness(username, password) {
        return new Promise((resolve) => {
            // 模拟API调用延迟
            setTimeout(() => {
                try {
                    // 模拟第三方证人验证
                    console.log('验证第三方证人用户:', username);
                    
                    // 这里仅作为演示，实际项目中应该调用官方API
                    if (username.startsWith('witness_') && password.endsWith('_witness')) {
                        resolve({
                            username: username,
                            role: 'witness',
                            source: 'third_party',
                            displayName: '第三方证人: ' + username.replace('witness_', '')
                        });
                    } else {
                        resolve(null);
                    }
                } catch (error) {
                    console.error('第三方证人验证失败:', error);
                    resolve(null);
                }
            }, 400);
        });
    }

    // 获取登录源的中文显示名
    getSourceDisplayName(source) {
        const sourceNames = {
            'system': '系统内置用户',
            'database': '远程数据库',
            'third_party': '第三方证人'
        };
        return sourceNames[source] || source;
    }
}

// DOM加载完成后执行
window.addEventListener('DOMContentLoaded', function() {
    // 初始化用户认证管理器
    const authManager = new UserAuthenticationManager();
    
    // 添加表单验证功能
    const loginForm = document.getElementById('login-form');
    if (loginForm) {
        loginForm.addEventListener('submit', async function(event) {
            // 阻止默认提交
            event.preventDefault();
            
            // 获取表单元素
            const username = document.getElementById('username').value.trim();
            const password = document.getElementById('password').value;
            const errorMessage = document.getElementById('error-message');
            const errorText = document.getElementById('error-text');
            const loginButton = document.getElementById('login-button');
            
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
            
            // 显示加载状态
            loginButton.disabled = true;
            const originalButtonText = loginButton.innerHTML;
            loginButton.innerHTML = '<i class="fas fa-spinner fa-spin"></i> <span>验证中...</span>';
            
            console.log('登录请求已提交，正在多源验证...');
            
            try {
                // 使用用户认证管理器进行多源验证
                const result = await authManager.authenticate(username, password);
                
                if (result.success) {
                    // 登录成功
                    authManager.handleLoginSuccess(result.user);
                } else {
                    // 登录失败
                    errorText.textContent = result.message || '登录失败，请检查用户名和密码';
                    errorMessage.style.display = 'flex';
                    
                    // 更新剩余尝试次数（如果有）
                    const attemptsLeftElement = document.getElementById('attempts-left');
                    if (attemptsLeftElement) {
                        let attempts = parseInt(attemptsLeftElement.textContent);
                        if (attempts > 0) {
                            attemptsLeftElement.textContent = attempts - 1;
                        }
                        
                        // 如果尝试次数用完，锁定表单
                        if (attempts <= 1) {
                            loginButton.disabled = true;
                            errorText.textContent += '（账户已临时锁定，请稍后再试）';
                        }
                    }
                }
            } catch (error) {
                console.error('登录过程中发生错误:', error);
                errorText.textContent = '登录过程中发生错误，请稍后重试';
                errorMessage.style.display = 'flex';
            } finally {
                // 恢复按钮状态
                loginButton.disabled = false;
                loginButton.innerHTML = originalButtonText;
            }
        });
    };

    
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
                };

            });
        });
    };

    
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
            };

        };

        return false;
    };

    
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
            };

            
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
                };

            }, 1000);
        };

    };

    
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
            };

            
            // 添加state参数防止CSRF攻击
            const state = Math.random().toString(36).substring(2, 15) + Math.random().toString(36).substring(2, 15);
            localStorage.setItem(`oauth_state_${provider}`, state);
            authUrl += `&state=${state}`;
            
            // 对于微信，特殊处理
            if (provider === 'wechat') {
                showWechatQrCode();
                loginButton.classList.remove('loading');
                return;
            };

            
            // 跳转到授权页面
            console.log(`跳转到${provider}授权页面:`, authUrl);
            window.location.href = authUrl;
        } else {
            console.error(`未配置${provider}的OAuth设置`);
            alert('该登录方式暂不可用，请稍后再试');
            loginButton.classList.remove('loading');
        };

    };

    
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
            };

            
            // 二维码过期
            if (remainingTime <= 0) {
                clearInterval(timerInterval);
                statusElement.textContent = '二维码已过期';
                timerElement.textContent = '有效期0分0秒';
                
                // 自动关闭
                setTimeout(() => {
                    document.body.removeChild(qrContainer);
                }, 2000);
            };

        }, 1000);
    };

    
    // 主题切换功能实现
function setupThemeToggle() {
    const themeButton = document.querySelector('.theme-btn');
    const body = document.body;
    
    if (!themeButton) return;
    
    // 检查是否为公祭日
    if (isMourningDay()) {
        // 公祭日自动使用公祭日主题
        applyTheme('mourning');
        // 禁用主题切换按钮
        themeButton.disabled = true;
        themeButton.title = '公祭日期间主题不可切换';
        themeButton.style.opacity = '0.5';
        return;
    }
    
    // 从localStorage加载保存的主题
    const savedTheme = localStorage.getItem('theme');
    if (savedTheme && savedTheme !== 'mourning') { // 不允许加载公祭日主题
        applyTheme(savedTheme);
    } else {
        // 默认检查系统偏好
        const prefersDark = window.matchMedia && window.matchMedia('(prefers-color-scheme: dark)').matches;
        applyTheme(prefersDark ? 'dark' : 'light');
    }
    
    // 添加点击事件监听
    themeButton.addEventListener('click', function() {
        const currentTheme = getCurrentTheme();
        let nextTheme;
        
        // 循环切换主题：light -> dark -> light
        // 移除公祭日主题的手动切换
        nextTheme = currentTheme === 'light' ? 'dark' : 'light';
        
        applyTheme(nextTheme);
        localStorage.setItem('theme', nextTheme);
    });
}

// 判断是否为公祭日
function isMourningDay() {
    const now = new Date();
    const month = now.getMonth() + 1;
    const day = now.getDate();
    
    // 公祭日列表（根据官方公告）
    const mourningDays = [
        { month: 9, day: 18 }, // 九一八事变纪念日
        { month: 12, day: 13 } // 南京大屠杀死难者国家公祭日
    ];
    
    // 检查当前日期是否在公祭日列表中
    return mourningDays.some(date => date.month === month && date.day === day);
}

// 获取当前主题
function getCurrentTheme() {
    const body = document.body;
    if (body.classList.contains('dark-theme')) {
        return 'dark';
    } else if (body.classList.contains('mourning-theme')) {
        return 'mourning';
    }
    return 'light';
}

// 应用主题
function applyTheme(theme) {
    const body = document.body;
    const themeIcon = document.querySelector('.theme-btn i');
    
    // 移除所有主题类
    body.classList.remove('dark-theme', 'mourning-theme');
    
    // 添加对应的主题类
    if (theme === 'dark') {
        body.classList.add('dark-theme');
        if (themeIcon) themeIcon.className = 'fas fa-sun'; // 切换到深色主题时显示太阳图标
    } else if (theme === 'mourning') {
        body.classList.add('mourning-theme');
        if (themeIcon) themeIcon.className = 'fas fa-star'; // 公祭日主题时显示星星图标
    } else {
        if (themeIcon) themeIcon.className = 'fas fa-moon'; // 浅色主题时显示月亮图标
    }
    
    console.log(`已切换到${theme}主题`);
}

// 更新IP和地理位置信息（使用默认值避免API调用错误）
function updateIPAndLocation() {
    // 直接使用默认值
    const ipElement = document.getElementById('user-ip');
    if (ipElement) {
        ipElement.textContent = 'IP: 192.168.1.100';
    };

    
    // 移除位置信息，不再添加或更新位置元素
    const locationElement = document.getElementById('user-location');
    if (locationElement) {
        const locationRow = locationElement.closest('tr');
        if (locationRow) {
            locationRow.remove();
        };

    };

};


// 初始化时检查OAuth回调
if (!checkOAuthCallback()) {
    console.log('不是OAuth回调，继续正常流程');
};

    
    // 获取IP和地理位置信息
updateIPAndLocation();

// 移除在线人数统计相关代码

// 初始化主题切换功能
setupThemeToggle();
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
    };

};


// 添加浮动动画
const floatStyle = document.createElement('style');
floatStyle.textContent = `
    @keyframes float {
        0% {
            transform: translateY(0) translateX(0);
        };

        25% {
            transform: translateY(-50px) translateX(20px);
        };

        50% {
            transform: translateY(-100px) translateX(0);
        };

        75% {
            transform: translateY(-50px) translateX(-20px);
        };

        100% {
            transform: translateY(0) translateX(0);
        };

    };

`;
document.head.appendChild(floatStyle);

// 初始化粒子
createParticles();

// 防盗链脚本
window.addEventListener('DOMContentLoaded', function() {
    // 防止iframe嵌套
    if (window.top !== window.self) {
        window.top.location = window.location;
    };

    
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
            };

        });
    });
};


// 农历转换功能
function solarToLunar(date) {
    // 简化版农历转换，实际应用中可以使用更精确的农历库
    const lunarMonths = ['正月', '二月', '三月', '四月', '五月', '六月', '七月', '八月', '九月', '十月', '冬月', '腊月'];
    const lunarDays = ['初一', '初二', '初三', '初四', '初五', '初六', '初七', '初八', '初九', '初十', 
                      '十一', '十二', '十三', '十四', '十五', '十六', '十七', '十八', '十九', '二十', 
                      '廿一', '廿二', '廿三', '廿四', '廿五', '廿六', '廿七', '廿八', '廿九', '三十'];
    
    // 使用简化的方法计算农历日期（实际应用建议使用完整的农历转换算法）
    // 这里仅作为演示，使用近似值
    const year = date.getFullYear();
    const month = date.getMonth();
    const day = date.getDate();
    
    // 简单的农历日期计算（非精确，仅供演示）
    const lunarMonth = (month + 1 + 2) % 12 || 12;
    const lunarDay = day - 1; // 初一对应公历1日-1
    
    return `${year}年${lunarMonths[lunarMonth - 1]}${lunarDays[lunarDay >= 0 ? lunarDay : 29]}`;
}

// 更新时间函数 - 使用new Date()实现，添加农历时间显示
function updateCurrentTime() {
    const now = new Date();
    const options = { year: 'numeric', month: 'long', day: 'numeric', hour: '2-digit', minute: '2-digit', second: '2-digit' };
    const formattedTime = now.toLocaleString('zh-CN', options);
    
    // 添加农历时间
    const lunarDate = solarToLunar(now);
    const fullTimeText = `${formattedTime} (农历：${lunarDate})`;
    
    // 查找time类元素而不是current-time ID
    const timeElement = document.querySelector('.time');
    
    // 直接更新时间文本
    if (timeElement) {
        timeElement.textContent = fullTimeText;
    }
}


// 初始化时间更新
setInterval(updateCurrentTime, 1000);
updateCurrentTime();