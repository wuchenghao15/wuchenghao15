// Vikey硬件密钥检测功能
let isVikeyDetected = false;

// 模拟Vikey硬件密钥检测
function detectVikey() {
    // 这里应该是实际的Vikey硬件检测代码
    // 为了演示，我们使用一个模拟的检测
    console.log('正在检测Vikey硬件密钥...');
    
    // 模拟检测过程，随机返回是否检测到Vikey
    // 在实际应用中，这里应该调用Vikey SDK的检测方法
    const randomDetection = Math.random() > 0.3; // 70%的概率检测到Vikey
    isVikeyDetected = randomDetection;
    
    if (isVikeyDetected) {
        console.log('检测到Vikey硬件密钥！');
        updateLoginButton();
    } else {
        console.log('未检测到Vikey硬件密钥');
    }
    
    return isVikeyDetected;
}

// 更新登录按钮状态
function updateLoginButton() {
    const loginButton = document.querySelector('#login-form button[type="submit"]');
    if (loginButton) {
        if (isVikeyDetected) {
            loginButton.innerHTML = '<svg class="svg-icon" viewBox="0 0 512 512" width="16" height="16"><path d="M336 144c0-26.5 21.5-48 48-48s48 21.5 48 48-21.5 48-48 48-48-21.5-48-48zm176 48c0-79.5-64.5-144-144-144s-144 64.5-144 144c0 19.3 3.8 37.7 10.7 54.6L144 352 48 256 0 304l96 96 48 48 48-48 16.4-16.4c15.5 5.6 32.1 8.8 49.6 8.8 79.5 0 144-64.5 144-144z"/></svg>免密登录';
            loginButton.title = '检测到Vikey硬件密钥，点击即可免密登录';
        } else {
            loginButton.innerHTML = '<i class="fas fa-sign-in-alt mr-2"></i>登录';
            loginButton.title = '请输入用户名和密码登录';
        }
    }
}

// 处理免密登录
function handleVikeyLogin(event) {
    if (isVikeyDetected) {
        event.preventDefault();
        console.log('执行Vikey免密登录...');
        
        // 这里应该是实际的Vikey免密登录代码
        // 为了演示，我们模拟一个登录过程
        const loginButton = event.target;
        const originalText = loginButton.innerHTML;
        
        loginButton.innerHTML = '<i class="fas fa-spinner fa-spin mr-2"></i>登录中...';
        loginButton.disabled = true;
        
        // 模拟登录请求
        setTimeout(() => {
            // 模拟登录成功
            alert('Vikey免密登录成功！');
            // 这里可以添加实际的登录成功处理逻辑，比如跳转到首页
            window.location.href = '/dashboard';
        }, 1500);
    }
}

// 页面加载完成后初始化Vikey检测
document.addEventListener('DOMContentLoaded', function() {
    // 检测Vikey硬件密钥
    detectVikey();
    
    // 为登录按钮添加点击事件监听
    const loginButton = document.querySelector('#login-form button[type="submit"]');
    if (loginButton) {
        loginButton.addEventListener('click', handleVikeyLogin);
    }
    
    // 定期检测Vikey状态（每5秒）
    setInterval(detectVikey, 5000);
});
