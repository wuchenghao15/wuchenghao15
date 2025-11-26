// VERSION: 20251106.7fdb8591d390780a088ce
// MTSCOS 系统重定向工具脚本
// 提供统一的重定向功能和路径管理

/**
 * 检查URL中是否包含vite相关的路径，并进行处理
 */
function handleViteRedirect() {
    const currentURL = window.location.href;
    
    // 如果检测到@vite/client相关请求，避免404错误
    if (currentURL.includes('@vite/client')) {
        console.log('检测到Vite客户端请求，已拦截以避免404错误');
        // 可以选择重定向到适当的页面或什么都不做
        return;
    }
}

/**
 * 统一的重定向函数
 * @param {string} targetURL - 目标URL
 * @param {number} delay - 延迟时间（毫秒）
 */
function redirectTo(targetURL, delay = 0) {
    if (delay > 0) {
        setTimeout(() => {
            window.location.href = targetURL;
        }, delay);
    } else {
        window.location.href = targetURL;
    }
}

/**
 * 获取正确的根路径
 * @returns {string} 根路径
 */
function getRootPath() {
    const currentPath = window.location.pathname;
    let rootPath = '';
    
    // 根据当前页面深度动态确定根路径
    if (currentPath.includes('/about/') || currentPath.includes('/help/') || currentPath.includes('/product/')) {
        // 在二级目录中
        rootPath = '../../';
    } else if (currentPath.includes('/auth/')) {
        // 在auth目录中
        rootPath = '../../';
    } else {
        // 在主HTML目录中
        rootPath = '../';
    }
    
    return rootPath;
}

/**
 * 页面加载时执行的初始化函数
 */
function initRedirect() {
    // 处理Vite相关请求
    handleViteRedirect();
    
    // 可以在这里添加其他重定向逻辑
}

// 页面加载时初始化
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', initRedirect);
} else {
    initRedirect();
}

// 暴露到全局作用域
window.RedirectModule = {
    redirectTo,
    getRootPath,
    handleRedirect
};