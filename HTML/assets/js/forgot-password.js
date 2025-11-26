// VERSION: 20251106.aad2ec92b5a8553cf8c0aad
// 忘记密码页面脚本

// DOM 加载完成后执行
window.addEventListener('DOMContentLoaded', function() {
    // 初始化主题和时间显示
    initTheme();
    initDateTimeDisplay();
    
    // 初始化表单步骤
    initResetSteps();
    
    // 记录页面访问日志
    logAction('forgot_password_visit', '用户访问重设密码页面');
});

// 初始化重置步骤
function initResetSteps() {
    // 步骤1按钮
    document.getElementById('step1-next').addEventListener('click', function() {
        validateUsername();
    });
    
    // 步骤2按钮
    document.getElementById('step2-back').addEventListener('click', function() {
        goToStep(1);
    });
    document.getElementById('step2-next').addEventListener('click', function() {
        validateVerification();
    });
    
    // 步骤3按钮
    document.getElementById('step3-back').addEventListener('click', function() {
        goToStep(2);
    });
    
    // 表单提交
    document.getElementById('reset-form').addEventListener('submit', function(e) {
        e.preventDefault();
        submitNewPassword();
    });
    
    // 验证码刷新
    const verifyImage = document.getElementById('verify-image');
    if (verifyImage) {
        generateVerifyCode();
        verifyImage.addEventListener('click', generateVerifyCode);
    }
}

// 验证用户名
function validateUsername() {
    const username = document.getElementById('username').value.trim();
    
    if (!username) {
        showResetError('请输入用户名');
        return;
    }
    
    // 模拟用户名验证
    showLoading(true);
    
    setTimeout(() => {
        showLoading(false);
        // 在实际应用中，这里应该调用API验证用户名是否存在
        if (username === 'demo') {
            goToStep(2);
            logAction('username_validated', `用户名 ${username} 验证通过`);
        } else {
            showResetError('用户名不存在');
        }
    }, 800);
}

// 验证身份
function validateVerification() {
    const verifyCode = document.getElementById('verify-code').value.trim();
    const securityQuestion = document.getElementById('security-question').value;
    const securityAnswer = document.getElementById('security-answer').value.trim();
    
    // 验证验证码
    const storedCode = sessionStorage.getItem('verify_code');
    if (!verifyCode || verifyCode.toUpperCase() !== storedCode.toUpperCase()) {
        showResetError('验证码错误');
        generateVerifyCode();
        return;
    }
    
    if (!securityQuestion) {
        showResetError('请选择安全问题');
        return;
    }
    
    if (!securityAnswer) {
        showResetError('请输入安全问题答案');
        return;
    }
    
    // 模拟安全验证
    showLoading(true);
    
    setTimeout(() => {
        showLoading(false);
        // 在实际应用中，这里应该调用API验证安全问题答案
        if (securityAnswer.toLowerCase() === 'demo') {
            goToStep(3);
            logAction('identity_verified', '用户身份验证通过');
        } else {
            showResetError('安全问题答案错误');
        }
    }, 800);
}

// 提交新密码
function submitNewPassword() {
    const newPassword = document.getElementById('new-password').value;
    const confirmPassword = document.getElementById('confirm-password').value;
    const username = document.getElementById('username').value;
    
    if (!newPassword) {
        showResetError('请输入新密码');
        return;
    }
    
    if (newPassword.length < 6) {
        showResetError('密码长度至少为6位');
        return;
    }
    
    if (newPassword !== confirmPassword) {
        showResetError('两次输入的密码不一致');
        return;
    }
    
    // 模拟密码重置
    showLoading(true);
    
    setTimeout(async () => {
        // 密码MD5加密
        const encryptedPassword = await md5(newPassword);
        
        // 在实际应用中，这里应该调用API重置密码
        showLoading(false);
        
        goToStep(4);
        logAction('password_reset', `用户 ${username} 密码重置成功`);
    }, 1000);
}

// 生成验证码
function generateVerifyCode() {
    const chars = '0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ';
    let code = '';
    for (let i = 0; i < 4; i++) {
        code += chars.charAt(Math.floor(Math.random() * chars.length));
    }
    
    sessionStorage.setItem('verify_code', code);
    
    // 创建验证码图片（简化版）
    const canvas = document.createElement('canvas');
    canvas.width = 120;
    canvas.height = 45;
    const ctx = canvas.getContext('2d');
    
    // 设置背景
    const bgColors = ['#f0f0f0', '#e0e0e0', '#f5f5f5'];
    ctx.fillStyle = bgColors[Math.floor(Math.random() * bgColors.length)];
    ctx.fillRect(0, 0, canvas.width, canvas.height);
    
    // 添加干扰线
    ctx.strokeStyle = '#ccc';
    ctx.lineWidth = 1;
    for (let i = 0; i < 5; i++) {
        ctx.beginPath();
        ctx.moveTo(Math.random() * canvas.width, Math.random() * canvas.height);
        ctx.lineTo(Math.random() * canvas.width, Math.random() * canvas.height);
        ctx.stroke();
    }
    
    // 添加文字
    ctx.font = 'bold 24px Arial';
    ctx.textAlign = 'center';
    ctx.textBaseline = 'middle';
    
    // 每个字符使用不同颜色
    const textColors = ['#333', '#666', '#999'];
    for (let i = 0; i < code.length; i++) {
        ctx.fillStyle = textColors[Math.floor(Math.random() * textColors.length)];
        const x = 25 + i * 20;
        const y = 22 + (Math.random() - 0.5) * 10;
        const rotation = (Math.random() - 0.5) * 0.3;
        
        ctx.save();
        ctx.translate(x, y);
        ctx.rotate(rotation);
        ctx.fillText(code[i], 0, 0);
        ctx.restore();
    }
    
    // 设置验证码图片
    const verifyImage = document.getElementById('verify-image');
    verifyImage.src = canvas.toDataURL();
}

// 切换到指定步骤
function goToStep(step) {
    // 隐藏所有步骤
    const steps = document.querySelectorAll('.reset-step');
    steps.forEach(s => s.style.display = 'none');
    
    // 显示当前步骤
    if (step === 1) {
        document.getElementById('step-username').style.display = 'block';
    } else if (step === 2) {
        document.getElementById('step-verify').style.display = 'block';
    } else if (step === 3) {
        document.getElementById('step-new-password').style.display = 'block';
    } else if (step === 4) {
        document.getElementById('reset-success').style.display = 'block';
    }
    
    // 隐藏错误信息
    hideResetError();
}

// 显示错误信息
function showResetError(message) {
    const errorElement = document.getElementById('reset-error');
    if (errorElement) {
        errorElement.textContent = message;
        errorElement.style.display = 'block';
        
        setTimeout(hideResetError, 3000);
    }
}

// 隐藏错误信息
function hideResetError() {
    const errorElement = document.getElementById('reset-error');
    if (errorElement) {
        errorElement.style.display = 'none';
    }
}

// 显示加载状态
function showLoading(isLoading) {
    // 禁用或启用所有按钮
    const buttons = document.querySelectorAll('button, input[type="submit"]');
    buttons.forEach(btn => {
        btn.disabled = isLoading;
        if (isLoading && btn.id === 'reset-submit') {
            btn.innerHTML = '<i class="fas fa-spinner fa-spin"i> 处理中...';
        } else if (btn.id === 'reset-submit') {
            btn.textContent = '重设密码';
        }
    });
}

// 主题初始化（从login-script.js复制的功能）
function initTheme() {
    // 检查系统主题偏好
    const prefersDark = window.matchMedia && window.matchMedia('(prefers-color-scheme: dark)').matches;
    
    // 检查是否是公祭日
    if (isMourningDay()) {
        document.body.classList.add('mourning-theme');
        localStorage.setItem('theme', 'mourning');
        return;
    }
    
    // 从本地存储读取主题偏好或使用系统偏好
    const savedTheme = localStorage.getItem('theme');
    if (savedTheme) {
        document.body.classList.add(savedTheme + '-theme');
    } else if (prefersDark) {
        document.body.classList.add('dark-theme');
        localStorage.setItem('theme', 'dark');
    }
    
    // 主题切换按钮事件
    const themeBtn = document.getElementById('theme-toggle');
    if (themeBtn) {
        themeBtn.addEventListener('click', toggleTheme);
    }
}

// 切换主题
function toggleTheme() {
    if (isMourningDay()) return;
    
    const currentTheme = localStorage.getItem('theme');
    const body = document.body;
    
    body.classList.remove('light-theme', 'dark-theme');
    
    if (currentTheme === 'dark') {
        localStorage.setItem('theme', 'light');
    } else {
        body.classList.add('dark-theme');
        localStorage.setItem('theme', 'dark');
    }
}

// 检查是否是公祭日
function isMourningDay() {
    const today = new Date();
    const month = today.getMonth() + 1;
    const day = today.getDate();
    
    const mourningDays = [
        { month: 12, day: 13 },
        { month: 9, day: 18 },
        { month: 5, day: 12 }
    ];
    
    return mourningDays.some(date => date.month === month && date.day === day);
}

// 初始化日期时间显示
function initDateTimeDisplay() {
    const dateTimeElement = document.getElementById('datetime-display');
    if (!dateTimeElement) return;
    
    updateDateTime();
    setInterval(updateDateTime, 1000);
}

// 更新日期时间
function updateDateTime() {
    const dateTimeElement = document.getElementById('datetime-display');
    if (!dateTimeElement) return;
    
    const userTimezone = Intl.DateTimeFormat().resolvedOptions().timeZone;
    const now = new Date();
    
    const options = {
        year: 'numeric',
        month: '2-digit',
        day: '2-digit',
        hour: '2-digit',
        minute: '2-digit',
        second: '2-digit',
        hour12: false,
        timeZoneName: 'short'
    };
    
    const formattedDateTime = now.toLocaleString('zh-CN', options);
    dateTimeElement.textContent = `${formattedDateTime} | ${userTimezone}`;
}

// MD5加密函数
async function md5(str) {
    const encoder = new TextEncoder();
    const data = encoder.encode(str);
    const hashBuffer = await crypto.subtle.digest('SHA-1', data);
    const hashArray = Array.from(new Uint8Array(hashBuffer));
    return hashArray.map(b => b.toString(16).padStart(2, '0')).join('');
}

// 记录操作日志
function logAction(actionType, description) {
    const logEntry = {
        timestamp: new Date().toISOString(),
        action: actionType,
        description: description,
        userAgent: navigator.userAgent
    };
    
    console.log('Forgot Password Log:', logEntry);
    
    // 实际环境中，这里应该发送日志到服务器
}