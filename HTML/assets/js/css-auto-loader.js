
// HTTP错误处理函数
function fetchErrorHandler(response) {
    if (!response.ok) {
        if (response.status === 404) {
            console.error('资源未找到 (404)');
            // 可以在这里添加重定向到404页面的逻辑
            // window.location.href = '/HTML/404.html';
        } else if (response.status === 403) {
            console.error('访问被拒绝 (403)');
            // 可以在这里添加重定向到403页面的逻辑
            // window.location.href = '/HTML/403.html';
        } else {
            console.error('HTTP错误: ' + response.status);
        }
        
        // 使用统一错误处理器而不是直接抛出错误
        if (window.unifiedErrorHandler) {
            return window.unifiedErrorHandler.safeThrow(
                new Error('HTTP错误: ' + response.status),
                window.unifiedErrorHandler.errorTypes.HTTP_ERROR
            );
        } else {
            throw new Error('HTTP错误: ' + response.status);
        }
    }
    return response;
}

// 可选：不覆盖全局fetch，而是在需要时使用自定义fetch函数
function enhancedFetch(url, options) {
    return fetch(url, options)
        .then(fetchErrorHandler);
}
/**
 * MTSCOS CSS自动加载器 - 增强版
 * 作者: Chenghao Wu
 * 版本: 2.0.0
 * 功能: 自动检测主题、路径适配、响应式设计、深色模式支持
 */

class CssAutoLoader {
    constructor() {
        this.basePath = this.determineBasePath();
        this.pageStylesDir = this.basePath + '../CSS/page_styles/';
        this.commonStylesDir = this.basePath + '../CSS/common_styles/';
        this.componentStylesDir = this.basePath + '../CSS/component_styles/';
        this.otherStylesDir = this.basePath + '../CSS/other_styles/';
        // 根据实际文件位置调整默认主题列表
        this.defaultThemes = ['main.css', 'responsive.css'];
        this.isDarkMode = this.detectDarkMode();
        this.loadedStyles = new Set();
        this.themeColors = this.getThemeColors();
        
        // 性能优化：添加缓存和防抖
        this.loadCache = new Map();
        this.loadingPromises = new Map();
        this.performanceMetrics = {
            loadTimes: [],
            errorCount: 0,
            successCount: 0
        };
    }

    /**
     * 初始化CSS自动加载器
     */
    init() {
        console.log('CSS自动加载器初始化...');
        
        // 应用主题
        this.applyTheme();
        
        // 获取当前页面文件名
        const pageName = this.getCurrentPageName();
        console.log('检测到当前页面: ' + pageName);
        
        // 加载默认主题文件
        this.loadDefaultThemes();
        
        // 尝试加载页面特定CSS
        this.loadPageSpecificCss(pageName);
        
        // 监听主题切换
        this.setupThemeListener();
        
        // 监听系统主题变化
        this.setupSystemThemeListener();
        
        // 适配移动设备
        this.setupResponsiveListeners();
        
        console.log('CSS自动加载完成');
        console.log('当前主题:', this.isDarkMode ? '深色模式' : '浅色模式');
    }
    
    /**
     * 确定基础路径
     */
    determineBasePath() {
        const path = window.location.pathname;
        if (path.includes('/HTML/')) {
            return '../';
        }
        // 处理根目录或其他情况
        return '/';
    }
    
    /**
     * 检测深色模式偏好
     */
    detectDarkMode() {
        // 检查本地存储中的主题设置
        const savedTheme = localStorage.getItem('theme');
        if (savedTheme) {
            return savedTheme === 'dark';
        }
        
        // 检查系统偏好
        return window.matchMedia && window.matchMedia('(prefers-color-scheme: dark)').matches;
    }
    
    /**
     * 获取主题颜色变量
     */
    getThemeColors() {
        return {
            light: {
                // 优化亮色主题配色，使用更现代、和谐的颜色方案
                primary: '#165DFF',
                'primary-gradient': 'linear-gradient(135deg, #165DFF 0%, #0A4BFF 100%)',
                secondary: '#6B7280',
                success: '#34D399',
                warning: '#FBBF24',
                danger: '#F87171',
                info: '#60A5FA',
                background: '#FFFFFF',
                'bg-hover': '#F5F7FA',
                text: '#1D2129',
                'text-secondary': '#4E5969',
                'text-light': '#86909C',
                border: '#E4E7ED'
            },
            dark: {
                primary: '#17a2b8',
                'primary-gradient': 'linear-gradient(135deg, #17a2b8 0%, #117a8b 100%)',
                secondary: '#6c757d',
                success: '#28a745',
                warning: '#ffc107',
                danger: '#dc3545',
                info: '#0dcaf0',
                background: '#1a202c',
                'bg-hover': '#2d3748',
                text: '#e2e8f0',
                'text-secondary': '#a0aec0',
                'text-light': '#718096',
                border: '#4a5568'
            }
        };
    }
    
    /**
     * 应用主题
     */
    applyTheme() {
        if (this.isDarkMode) {
            document.body.classList.add('dark-theme');
        } else {
            document.body.classList.remove('dark-theme');
        }
        
        // 更新CSS变量
        this.updateCSSVariables();
    }
    
    /**
     * 更新CSS变量 - 统一变量命名机制
     */
    updateCSSVariables() {
        const colors = this.themeColors[this.isDarkMode ? 'dark' : 'light'];
        const root = document.documentElement;
        
        // 更新基础颜色变量（保持与variables.css一致的命名规范）
        root.style.setProperty('--primary-color', colors.primary);
        root.style.setProperty('--primary-gradient', colors['primary-gradient']);
        root.style.setProperty('--secondary-color', colors.secondary);
        root.style.setProperty('--success-color', colors.success);
        root.style.setProperty('--warning-color', colors.warning);
        root.style.setProperty('--danger-color', colors.danger);
        root.style.setProperty('--info-color', colors.info);
        root.style.setProperty('--bg-primary', colors.background);
        root.style.setProperty('--bg-hover', colors['bg-hover']);
        root.style.setProperty('--border-color', colors.border);
        root.style.setProperty('--text-primary', colors.text);
        root.style.setProperty('--text-secondary', colors['text-secondary']);
        root.style.setProperty('--text-muted', colors['text-light']);
        root.style.setProperty('--text-light', colors.text); // 白色文本在深色模式下使用
        
        // 向后兼容：保留旧的变量命名
        Object.entries(colors).forEach(function([key, value]) {
            root.style.setProperty('--' + key + '-color', value);
        });
    }

    /**
     * 获取当前页面文件名
     * @returns {string} 页面文件名（不含扩展名）
     */
    getCurrentPageName() {
        const pathname = window.location.pathname;
        const filename = pathname.substring(pathname.lastIndexOf('/') + 1);
        // 处理空文件名情况（如根目录）
        const pageName = filename.split('.')[0];
        return pageName || 'index';
    }

    /**
     * 加载默认主题文件
     */
    loadDefaultThemes() {
        // 加载common_styles目录中的文件
        this.defaultThemes.forEach(function(cssFile) {
            const cssPath = this.commonStylesDir + cssFile;
            this.loadCssIfExists(cssPath);
        }, this);
        
        // 单独加载variables.css，它在other_styles目录中
        const variablesPath = this.otherStylesDir + 'variables.css';
        this.loadCssIfExists(variablesPath);
    }
    
    /**
     * 调整屏幕大小
     */
    adjustForScreenSize() {
        const isMobile = window.innerWidth < 768;
        const isTablet = window.innerWidth < 1024 && window.innerWidth >= 768;
        
        document.body.classList.toggle('mobile-view', isMobile);
        document.body.classList.toggle('tablet-view', isTablet);
        document.body.classList.toggle('desktop-view', !isMobile && !isTablet);
    }
    
    /**
     * 设置响应式监听器
     */
    setupResponsiveListeners() {
        window.addEventListener('resize', this.debounce(function() {
            this.adjustForScreenSize();
        }, 250).bind(this));
        
        // 初始调整
        this.adjustForScreenSize();
    }
    
    /**
     * 防抖函数
     */
    debounce(func, wait) {
        let timeout;
        return function executedFunction(...args) {
            const later = function() {
                clearTimeout(timeout);
                func.apply(this, args);
            }.bind(this);
            clearTimeout(timeout);
            timeout = setTimeout(later, wait);
        };
    }

    /**
     * 尝试加载页面特定的CSS文件
     * @param {string} pageName 页面名称
     */
    loadPageSpecificCss(pageName) {
        if (!pageName) return;
        
        // 跳过无效的页面名称
        if (pageName === 'nonexistent-page' || pageName.includes('?') || pageName.includes('#')) {
            console.log('跳过无效页面CSS加载: ' + pageName);
            return;
        }
        
        // 构建可能的CSS路径，根据实际目录结构调整
        const possiblePaths = [];
        
        // 特殊页面名称映射 - 优先使用映射
        const pageMappings = {
            'index': 'index_inline.css',
            'login': 'login-styles.css'
        };
        
        // 如果有映射，优先使用映射的文件
        if (pageMappings[pageName]) {
            possiblePaths.push(this.pageStylesDir + pageMappings[pageName]);
        } else {
            // 否则尝试默认命名
            possiblePaths.push(this.pageStylesDir + pageName + '.css');
        }

        // 特殊处理HTML/css目录中的文件
        if (pageName === 'lock-screen') {
            possiblePaths.push(this.basePath + '../HTML/css/lock-screen.css');
        }

        possiblePaths.forEach(function(path) {
            // 确保路径有效
            if (path && !path.includes('/.css')) {
                this.loadCssIfExists(path);
            }
        }, this);
    }

    /**
     * 检查CSS文件是否存在并加载 - 性能优化版本
     * @param {string} cssPath CSS文件路径
     * @returns {Promise} 加载Promise
     */
    async loadCssIfExists(cssPath) {
        const startTime = performance.now();
        
        // 检查缓存
        if (this.loadCache.has(cssPath)) {
            const cached = this.loadCache.get(cssPath);
            if (cached.success) {
                console.log(`从缓存加载CSS: ${cssPath}`);
                return Promise.resolve(cached);
            }
        }

        // 检查是否已经加载过这个CSS
        if (this.loadedStyles.has(cssPath) || document.querySelector(`link[href="${cssPath}"]`)) {
            console.log(`CSS已加载: ${cssPath}`);
            return Promise.resolve({ success: true, fromCache: true });
        }

        // 防止重复加载
        if (this.loadingPromises.has(cssPath)) {
            console.log(`CSS正在加载中: ${cssPath}`);
            return this.loadingPromises.get(cssPath);
        }

        // 创建加载Promise
        const loadPromise = this.createCssLoadPromise(cssPath, startTime);
        this.loadingPromises.set(cssPath, loadPromise);

        try {
            const result = await loadPromise;
            this.loadingPromises.delete(cssPath);
            return result;
        } catch (error) {
            this.loadingPromises.delete(cssPath);
            throw error;
        }
    }

    /**
     * 创建CSS加载Promise
     * @param {string} cssPath CSS文件路径
     * @param {number} startTime 开始时间
     * @returns {Promise} 加载Promise
     */
    createCssLoadPromise(cssPath, startTime) {
        return new Promise((resolve, reject) => {
            // 预检查CSS文件是否存在
            this.checkCssExists(cssPath)
                .then(exists => {
                    if (!exists) {
                        const error = new Error(`CSS文件不存在: ${cssPath}`);
                        this.handleCssLoadError(cssPath, error);
                        reject(error);
                        return;
                    }

                    // 创建link元素
                    const link = document.createElement('link');
                    link.rel = 'stylesheet';
                    link.href = cssPath;
                    link.media = 'all';
                    link.crossOrigin = 'anonymous'; // 启用CORS缓存

                    link.onload = () => {
                        const loadTime = performance.now() - startTime;
                        this.loadedStyles.add(cssPath);
                        
                        // 更新缓存
                        this.loadCache.set(cssPath, {
                            success: true,
                            loadTime: loadTime,
                            timestamp: Date.now()
                        });

                        // 更新性能指标
                        this.performanceMetrics.loadTimes.push(loadTime);
                        this.performanceMetrics.successCount++;

                        console.log(`✅ 成功加载CSS: ${cssPath} (${loadTime.toFixed(2)}ms)`);
                        this.triggerCssLoadedEvent(cssPath, loadTime);
                        resolve({ success: true, loadTime });
                    };

                    link.onerror = () => {
                        const error = new Error(`CSS加载失败: ${cssPath}`);
                        this.handleCssLoadError(cssPath, error);
                        reject(error);
                    };

                    document.head.appendChild(link);
                })
                .catch(error => {
                    this.handleCssLoadError(cssPath, error);
                    reject(error);
                });
        });
    }

    /**
     * 检查CSS文件是否存在
     * @param {string} cssPath CSS文件路径
     * @returns {Promise<boolean>} 是否存在
     */
    async checkCssExists(cssPath) {
        try {
            const response = await fetch(cssPath, { 
                method: 'HEAD',
                cache: 'no-cache'
            });
            return response.ok;
        } catch (error) {
            return false;
        }
    }

    /**
     * 处理CSS加载错误
     * @param {string} cssPath CSS路径
     * @param {Error} error 错误对象
     */
    handleCssLoadError(cssPath, error) {
        this.performanceMetrics.errorCount++;
        
        // 更新缓存
        this.loadCache.set(cssPath, {
            success: false,
            error: error.message,
            timestamp: Date.now()
        });

        console.warn(`⚠️ ${error.message}`);

        // 只有在关键CSS文件缺失时才应用备用样式
        const isCriticalCss = cssPath.includes('variables.css') || 
                            cssPath.includes('main.css') || 
                            cssPath.includes('responsive.css');

        if (isCriticalCss) {
            console.warn(`🚨 关键CSS文件缺失，应用备用样式: ${cssPath}`);
            this.applyFallbackStyling();
        }
    }

    /**
     * 应用备用样式
     */
    applyFallbackStyling() {
        console.log('应用备用样式...');
        
        // 创建备用样式
        const style = document.createElement('style');
        style.textContent = `
            /* 备用通用样式 */
            body {
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
                line-height: 1.6;
                color: #333;
                background-color: #f8f9fa;
                margin: 0;
                padding: 0;
            }
            
            .container {
                max-width: 1200px;
                margin: 0 auto;
                padding: 0 20px;
            }
            
            header, footer {
                background-color: #007bff;
                color: white;
                padding: 1rem 0;
            }
            
            .btn {
                display: inline-block;
                padding: 0.5rem 1rem;
                background-color: #007bff;
                color: white;
                border: none;
                border-radius: 4px;
                cursor: pointer;
                text-decoration: none;
                transition: background-color 0.3s;
            }
            
            .btn:hover {
                background-color: #0056b3;
            }
        `;
        
        document.head.appendChild(style);
    }

    /**
     * 设置主题切换监听器
     */
    setupThemeListener() {
        // 检查是否有主题切换按钮
        const themeToggle = document.querySelector('.theme-toggle');
        const themeToggleById = document.getElementById('theme-toggle');
        const toggleElement = themeToggle || themeToggleById;
        
        if (toggleElement) {
            toggleElement.addEventListener('click', function() {
                this.toggleTheme();
            }.bind(this));
            
            // 更新主题图标
            this.updateThemeIcon();
        }
    }
    
    /**
     * 设置系统主题监听器
     */
    setupSystemThemeListener() {
        if (window.matchMedia) {
            window.matchMedia('(prefers-color-scheme: dark)').addEventListener('change', function(e) {
                // 只有当主题设置为自动时才响应系统变化
                const savedTheme = localStorage.getItem('theme');
                if (!savedTheme || savedTheme === 'auto') {
                    this.isDarkMode = e.matches;
                    this.applyTheme();
                    this.updateThemeIcon();
                }
            }.bind(this));
        }
    }

    /**
     * 切换主题
     */
    toggleTheme() {
        this.isDarkMode = !this.isDarkMode;
        localStorage.setItem('theme', this.isDarkMode ? 'dark' : 'light');
        this.applyTheme();
        this.updateThemeIcon();
    }
    
    /**
     * 更新主题图标
     */
    updateThemeIcon() {
        const themeIcon = document.querySelector('#theme-toggle i, .theme-toggle i');
        if (themeIcon) {
            if (this.isDarkMode) {
                themeIcon.classList.remove('fa-moon');
                themeIcon.classList.add('fa-sun');
            } else {
                themeIcon.classList.remove('fa-sun');
                themeIcon.classList.add('fa-moon');
            }
        }
    }

    /**
     * 触发CSS加载完成事件 - 性能优化版本
     * @param {string} cssPath CSS文件路径
     * @param {number} loadTime 加载时间（可选）
     */
    triggerCssLoadedEvent(cssPath, loadTime = null) {
        const event = new CustomEvent('cssLoaded', {
            detail: {
                cssPath: cssPath,
                loadTime: loadTime,
                totalLoaded: this.loadedStyles.size,
                timestamp: Date.now()
            }
        });
        document.dispatchEvent(event);
    }

    /**
     * 获取性能指标
     * @returns {Object} 性能数据
     */
    getPerformanceMetrics() {
        const loadTimes = this.performanceMetrics.loadTimes;
        const avgLoadTime = loadTimes.length > 0 ? 
            loadTimes.reduce((sum, time) => sum + time, 0) / loadTimes.length : 0;

        return {
            totalLoaded: this.loadedStyles.size,
            cacheSize: this.loadCache.size,
            successCount: this.performanceMetrics.successCount,
            errorCount: this.performanceMetrics.errorCount,
            averageLoadTime: avgLoadTime,
            minLoadTime: loadTimes.length > 0 ? Math.min(...loadTimes) : 0,
            maxLoadTime: loadTimes.length > 0 ? Math.max(...loadTimes) : 0,
            cacheHitRate: this.calculateCacheHitRate()
        };
    }

    /**
     * 计算缓存命中率
     * @returns {number} 命中率百分比
     */
    calculateCacheHitRate() {
        if (this.loadCache.size === 0) return 0;
        
        const successfulLoads = Array.from(this.loadCache.values())
            .filter(item => item.success).length;
        
        return (successfulLoads / this.loadCache.size) * 100;
    }

    /**
     * 清理过期缓存
     * @param {number} maxAge 最大缓存时间（毫秒）
     */
    clearExpiredCache(maxAge = 30 * 60 * 1000) { // 默认30分钟
        const now = Date.now();
        const expiredKeys = [];

        for (const [key, value] of this.loadCache.entries()) {
            if (now - value.timestamp > maxAge) {
                expiredKeys.push(key);
            }
        }

        expiredKeys.forEach(key => this.loadCache.delete(key));
        console.log(`清理了 ${expiredKeys.length} 个过期缓存项`);
    }

    /**
     * 动态添加样式
     */
    addDynamicStyles(css) {
        const style = document.createElement('style');
        style.textContent = css;
        document.head.appendChild(style);
        return style;
    }

    /**
     * 移除样式
     */
    removeCSS(url) {
        const links = document.querySelectorAll('link[rel="stylesheet"][href="' + url + '"]');
        links.forEach(function(link) {
            link.parentNode.removeChild(link);
        });
        this.loadedStyles.delete(url);
    }

    /**
     * 重新加载所有CSS
     */
    reloadAll() {
        // 保存当前主题
        const currentTheme = this.isDarkMode;
        
        // 清空已加载样式
        this.loadedStyles.forEach(function(url) {
            this.removeCSS(url);
        }, this);
        this.loadedStyles.clear();
        
        // 重新加载
        this.isDarkMode = currentTheme;
        this.loadDefaultThemes();
        const pageName = this.getCurrentPageName();
        this.loadPageSpecificCss(pageName);
        this.applyTheme();
    }
    
    /**
     * 获取当前主题信息
     */
    getCurrentThemeInfo() {
        return {
            mode: this.isDarkMode ? 'dark' : 'light',
            colors: this.themeColors[this.isDarkMode ? 'dark' : 'light'],
            loadedStyles: Array.from(this.loadedStyles)
        };
    }
    
    /**
     * 检查文件是否存在
     */
    async checkFileExists(url) {
        try {
            const response = await fetch(url, {
                method: 'HEAD',
                cache: 'no-cache'
            });
            return response.ok;
        } catch (error) {
            return false;
        }
    }
    
    /**
     * 自动适配路径
     */
    resolvePath(relativePath) {
        if (relativePath.startsWith('http://') || relativePath.startsWith('https://')) {
            return relativePath;
        }
        
        // 处理相对路径
        if (relativePath.startsWith('./')) {
            return relativePath.substring(2);
        }
        
        return this.basePath + relativePath;
    }
    
    /**
     * 刷新所有CSS（用于开发模式）
     */
    refreshAllCss() {
        const links = document.querySelectorAll('link[rel="stylesheet"]');
        links.forEach(function(link) {
            const href = link.getAttribute('href');
            const timestamp = new Date().getTime();
            link.setAttribute('href', href.includes('?') ? 
                href.split('?')[0] + '?' + timestamp : 
                href + '?' + timestamp);
        });
    }
}

// 导出实例
window.cssAutoLoader = new CssAutoLoader();

// 页面加载完成后初始化
document.addEventListener('DOMContentLoaded', function() {
    window.cssAutoLoader.init();
});