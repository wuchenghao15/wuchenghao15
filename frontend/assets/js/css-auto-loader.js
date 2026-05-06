
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
        };

        throw new Error('HTTP错误: ' + response.status);
    };

    return response;
};


// 覆盖原生fetch以添加错误处理
const originalFetch = window.fetch;
window.fetch = function() {
    return originalFetch.apply(this, arguments)
        .then(fetchErrorHandler);
};
/**
 * MTSCOS CSS自动加载器 - 增强版
 * 作者: Chenghao Wu
 * 版本: 2.0.0
 * 功能: 自动检测主题、路径适配、响应式设计、深色模式支持
 */

class CssAutoLoader {
    constructor() {
        this.basePath = this.determineBasePath();
        this.pageStylesDir = `${this.basePath}CSS/page_styles/`;
        this.commonStylesDir = `${this.basePath}CSS/common_styles/`;
        this.componentStylesDir = `${this.basePath}CSS/component_styles/`;
        this.otherStylesDir = `${this.basePath}CSS/other_styles/`;
        this.defaultThemes = ['main.css', 'variables.css', 'responsive.css'];
        this.isDarkMode = this.detectDarkMode();
        this.loadedStyles = new Set();
        this.themeColors = this.getThemeColors();
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
        console.log(`检测到当前页面: ${pageName}`);
        
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
                primary: '#007bff',
                secondary: '#6c757d',
                success: '#28a745',
                warning: '#ffc107',
                danger: '#dc3545',
                info: '#17a2b8',
                background: '#f8f9fa',
                text: '#333',
                textLight: '#666',
                border: '#dee2e6'
            },
            dark: {
                primary: '#17a2b8',
                secondary: '#6c757d',
                success: '#28a745',
                warning: '#ffc107',
                danger: '#dc3545',
                info: '#0dcaf0',
                background: '#1a202c',
                text: '#e2e8f0',
                textLight: '#a0aec0',
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
     * 更新CSS变量
     */
    updateCSSVariables() {
        const colors = this.themeColors[this.isDarkMode ? 'dark' : 'light'];
        const root = document.documentElement;
        
        Object.entries(colors).forEach(([key, value]) => {
            root.style.setProperty(`--${key}-color`, value);
        });
    }

    /**
     * 获取当前页面文件名
     * @returns {string} 页面文件名（不含扩展名）
     */
    getCurrentPageName() {
        const pathname = window.location.pathname;
        const filename = pathname.substring(pathname.lastIndexOf('/') + 1);
        return filename.split('.')[0];
    }

    /**
     * 加载默认主题文件
     */
    loadDefaultThemes() {
        this.defaultThemes.forEach(cssFile => {
            const cssPath = `${this.commonStylesDir}${cssFile}`;
            this.loadCssIfExists(cssPath);
        });
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
        window.addEventListener('resize', this.debounce(() => {
            this.adjustForScreenSize();
        }, 250));
        
        // 初始调整
        this.adjustForScreenSize();
    }
    
    /**
     * 防抖函数
     */
    debounce(func, wait) {
        let timeout;
        return function executedFunction(...args) {
            const later = () => {
                clearTimeout(timeout);
                func(...args);
            };
            clearTimeout(timeout);
            timeout = setTimeout(later, wait);
        };
    }

    /**
     * 尝试加载页面特定的CSS文件
     * @param {string} pageName 页面名称
     */
    loadPageSpecificCss(pageName) {
        // 构建可能的CSS路径
        const possiblePaths = [
            `${this.pageStylesDir}${pageName}.css`,
            `${this.componentStylesDir}${pageName}-styles.css`,
            `${this.otherStylesDir}${pageName}.css`,
            `/HTML/css/${pageName}.css`
        ];

        possiblePaths.forEach(path => {
            this.loadCssIfExists(path);
        });
    }

    /**
     * 检查CSS文件是否存在并加载
     * @param {string} cssPath CSS文件路径
     */
    loadCssIfExists(cssPath) {
        // 检查是否已经加载过这个CSS
        if (this.loadedStyles.has(cssPath) || document.querySelector(`link[href="${cssPath}"]`)) {
            console.log(`CSS已加载: ${cssPath}`);
            return;
        }

        // 尝试加载CSS文件
        const link = document.createElement('link');
        link.rel = 'stylesheet';
        link.href = cssPath;
        link.media = 'all';
        
        link.onload = () => {
            this.loadedStyles.add(cssPath);
            console.log(`成功加载CSS: ${cssPath}`);
            // 触发CSS加载完成事件
            this.triggerCssLoadedEvent(cssPath);
        };
        
        link.onerror = () => {
            console.log(`CSS文件不存在或加载失败: ${cssPath}`);
            // 如果是页面特定CSS不存在，尝试应用通用样式
            if (cssPath.includes('/page_styles/')) {
                this.applyFallbackStyling();
            }
        };
        
        document.head.appendChild(link);
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
            toggleElement.addEventListener('click', () => {
                this.toggleTheme();
            });
            
            // 更新主题图标
            this.updateThemeIcon();
        }
    }
    
    /**
     * 设置系统主题监听器
     */
    setupSystemThemeListener() {
        if (window.matchMedia) {
            window.matchMedia('(prefers-color-scheme: dark)').addEventListener('change', (e) => {
                // 只有当主题设置为自动时才响应系统变化
                const savedTheme = localStorage.getItem('theme');
                if (!savedTheme || savedTheme === 'auto') {
                    this.isDarkMode = e.matches;
                    this.applyTheme();
                    this.updateThemeIcon();
                }
            });
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
     * 触发CSS加载完成事件
     * @param {string} cssPath 加载的CSS路径
     */
    triggerCssLoadedEvent(cssPath) {
        const event = new CustomEvent('cssLoaded', {
            detail: { cssPath: cssPath }
        });
        document.dispatchEvent(event);
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
        const links = document.querySelectorAll(`link[rel="stylesheet"][href="${url}"]`);
        links.forEach(link => {
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
        this.loadedStyles.forEach(url => {
            this.removeCSS(url);
        });
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
        
        return `${this.basePath}${relativePath}`;
    }
    
    /**
     * 刷新所有CSS（用于开发模式）
     */
    refreshAllCss() {
        const links = document.querySelectorAll('link[rel="stylesheet"]');
        links.forEach(link => {
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
document.addEventListener('DOMContentLoaded', () => {
    window.cssAutoLoader.init();
});