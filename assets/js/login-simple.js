/**
 * 简化版登录页面JavaScript - 用于调试
 */

console.log('[SIMPLE LOGIN] Script loaded');

// 简单的初始化函数
function simpleInit() {
    console.log('[SIMPLE LOGIN] Initializing...');
    
    // 检查基本DOM元素
    const loginForm = document.getElementById('loginForm');
    console.log('[SIMPLE LOGIN] Login form found:', !!loginForm);
    
    if (loginForm) {
        // 简单的表单提交处理
        loginForm.addEventListener('submit', function(e) {
            e.preventDefault().catch(error => console.error(`[login-simple.js] e.preventDefault failed:`, error));
            console.log('[SIMPLE LOGIN] Form submitted');
        });
    }
}

// 页面加载完成后初始化
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', simpleInit);
} else {
    simpleInit();
}