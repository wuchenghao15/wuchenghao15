
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
/**
 * MTSCOS AI 系统 - 前端路由系统
 * 用于单页应用的路由管理
 */

class Router {
    constructor() {
        this.routes = {};
        this.currentPath = '';
        this.init();
    }
    
    // 初始化路由
    init() {
        // 监听页面加载
        window.addEventListener('load', () => {
            this.handleRoute();
        });
        
        // 监听浏览器历史变化
        window.addEventListener('popstate', () => {
            this.handleRoute();
        });
        
        // 拦截所有链接点击
        document.addEventListener('click', (e) => {
            const target = e.target.closest('a');
            if (target && target.matches('[data-route]')) {
                e.preventDefault();
                const path = target.getAttribute('href');
                this.navigate(path);
            }
        });
    }
    
    // 注册路由
    register(path, callback) {
        this.routes[path] = callback;
    }
    
    // 导航到指定路径
    navigate(path) {
        window.history.pushState({}, '', path);
        this.handleRoute();
    }
    
    // 处理路由
    handleRoute() {
        const path = window.location.pathname || '/';
        this.currentPath = path;
        
        const callback = this.routes[path] || this.routes['*'];
        if (callback) {
            callback();
        }
    }
    
    // 获取当前路径
    getCurrentPath() {
        return this.currentPath;
    }
    
    // 刷新当前路由
    refresh() {
        this.handleRoute();
    }
}

// 导出路由实例
window.router = new Router();
