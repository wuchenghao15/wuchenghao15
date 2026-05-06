// 验证码相关变量
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
        ctx.beginPath();
        ctx.moveTo(Math.random() * canvas.width, Math.random() * canvas.height);
        ctx.lineTo(Math.random() * canvas.width, Math.random() * canvas.height);
        ctx.strokeStyle = `rgba(${Math.floor(Math.random() * 100)}, ${Math.floor(Math.random() * 100)}, ${Math.floor(Math.random() * 100)}, 0.5)`;
        ctx.lineWidth = Math.random() * 2 + 1;
        ctx.stroke();
    }
    
    // 添加干扰点
    for (let i = 0; i < 50; i++) {
        ctx.beginPath();
        ctx.arc(Math.random() * canvas.width, Math.random() * canvas.height, Math.random() * 1.5, 0, Math.PI * 2);
        ctx.fillStyle = `rgba(${Math.floor(Math.random() * 150)}, ${Math.floor(Math.random() * 150)}, ${Math.floor(Math.random() * 150)}, 0.5)`;
        ctx.fill();
    }
    
    // 绘制验证码文本
    ctx.textAlign = 'center';
    ctx.textBaseline = 'middle';
    
    for (let i = 0; i < length; i++) {
        const char = characters.charAt(Math.floor(Math.random() * characters.length));
        captchaCode += char;
        
        // 随机字体样式
        const fontSize = Math.floor(Math.random() * 6) + 18; // 18-24px
        ctx.font = `bold ${fontSize}px Arial, sans-serif`;
        
        // 随机颜色
        const colors = ['#333333', '#666666', '#999999', '#CC6600', '#CC9900', '#663399'];
        ctx.fillStyle = colors[Math.floor(Math.random() * colors.length)];
        
        // 随机旋转角度
        const angle = (Math.random() - 0.5) * 0.4; // -0.2到0.2弧度
        
        // 计算位置
        const x = 20 + i * (canvas.width - 40) / (length - 1);
        const y = canvas.height / 2;
        
        // 保存当前状态
        ctx.save();
        
        // 旋转文字
        ctx.translate(x, y);
        ctx.rotate(angle);
        
        // 绘制文字
        ctx.fillText(char, 0, 0);
        
        // 恢复状态
        ctx.restore();
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
    
    // 3秒后自动隐藏错误消息
    setTimeout(() => {
        errorMessage.style.display = 'none';
    }, 3000);
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
    
    const month = date.getMonth();
    const day = date.getDate() - 1;
    
    return `农历 ${lunarMonths[month]} ${lunarDays[day]}`;
}

// 初始化ActiveX组件
function initActiveX() {
    try {
        // 模拟ActiveX组件挂载
        console.log('正在初始化Vikey ActiveX组件...');
        
        // 模拟组件就绪
        setTimeout(() => {
            document.getElementById('activex-status').innerHTML = 
                '<i class="fas fa-check-circle"></i> Vikey安全认证组件就绪';
            
            // 模拟认证状态检查
            checkVikeyAuthentication();
        }, 1000);
    } catch (e) {
        console.error('ActiveX组件初始化失败:', e);
        document.getElementById('activex-status').innerHTML = 
            '<i class="fas fa-exclamation-triangle"></i> Vikey组件初始化失败';
        document.getElementById('activex-status').style.backgroundColor = 'var(--danger-color)';
    }
}

// 检查Vikey认证状态
function checkVikeyAuthentication() {
    // 模拟认证检查
    const isAuthenticated = true; // 假设认证成功
    
    if (isAuthenticated) {
        document.getElementById('activex-status').innerHTML = 
            '<i class="fas fa-lock"></i> Vikey认证成功';
        document.getElementById('activex-status').style.backgroundColor = 'var(--success-color)';
    } else {
        document.getElementById('activex-status').innerHTML = 
            '<i class="fas fa-unlock"></i> Vikey认证失败';
        document.getElementById('activex-status').style.backgroundColor = 'var(--danger-color)';
    }
}

// 页面加载完成后初始化
window.addEventListener('DOMContentLoaded', () => {
    // 初始更新时间
    updateDateTime();
    // 每秒更新时间
    setInterval(updateDateTime, 1000);
    
    // 初始化ActiveX
    initActiveX();
    
    // 生成验证码
    generateCaptcha();
    
    // 点击刷新验证码
    document.getElementById('captcha-image').addEventListener('click', generateCaptcha);
    
    // 登录表单提交增强
    const loginForm = document.getElementById('login-form');
    loginForm.addEventListener('submit', (e) => {
        // 检查Vikey认证状态
        const isAuthenticated = document.getElementById('activex-status').textContent.includes('成功');
        if (!isAuthenticated) {
            e.preventDefault();
            showError('请确保Vikey认证成功后再登录');
            return;
        }
        
        // 验证验证码
        const captchaInput = document.getElementById('captcha').value.trim();
        if (!captchaInput) {
            e.preventDefault();
            showError('请输入验证码');
            return;
        }
        
        if (!validateCaptcha(captchaInput)) {
            e.preventDefault();
            showError('验证码错误，请重新输入');
            generateCaptcha(); // 重新生成验证码
            decreaseAttempts(); // 减少尝试次数
        }
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
                    throw new Error('不支持的登录方式');
            }
        } catch (error) {
            // 恢复错误消息显示
            errorMessage.style.backgroundColor = '';
            errorMessage.innerHTML = `<i class="fas fa-exclamation-circle"></i> <span>登录失败: ${error.message}</span>`;
            console.error('第三方登录失败:', error);
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