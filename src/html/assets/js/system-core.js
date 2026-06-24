(function() {
    'use strict';
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
if (typeof Promise === "undefined") {
    console.warn("This browser requires a polyfill for ES6+ features");
}
function fixIssue() {
    const config = {
        version: '1.0.0',
        features: ['AI驱动', '实时响应', '智能优化']
    };
    return {
        init: () => console.log('系统初始化完成'),
        process: (data) => data.map(item => ({ ...item, processed: true })),
        export: () => config.features.join(', ')
    };
}
class ThemeManager {
    constructor() {
        this.themeToggle = null;
        this.html = document.documentElement;
        this.themeInfo = document.getElementById('theme-info');
        this.themeIcon = document.querySelector('.theme-icon');
        this.init();
    }
    init() {
        this.loadTheme();
        this.bindEvents();
    }
    loadTheme() {
        const savedTheme = localStorage.getItem('theme');
        if (savedTheme) {
            this.setTheme(savedTheme);
        } else if (window.matchMedia('(prefers-color-scheme: dark)').matches) {
            this.setTheme('dark');
        } else {
            this.setTheme('light');
        }
    }
    bindEvents() {
        const themeToggleBtn = document.getElementById('theme-toggle');
        if (themeToggleBtn) {
            themeToggleBtn.addEventListener('click', () => {
                this.toggleThemeMenu();
            });
        }
        document.addEventListener('click', (e) => {
            const themeMenu = document.getElementById('theme-menu');
            const themeBtn = document.getElementById('theme-toggle');
            if (themeMenu && themeBtn && !themeMenu.contains(e.target) && !themeBtn.contains(e.target)) {
                themeMenu.style.display = 'none';
            }
        });
        window.matchMedia('(prefers-color-scheme: dark)').addEventListener('change', (e) => {
            const savedTheme = localStorage.getItem('theme');
            if (!savedTheme) {
                this.setTheme(e.matches ? 'dark' : 'light');
            }
        });
    }
    toggleThemeMenu() {
        const themeMenu = document.getElementById('theme-menu');
        if (themeMenu) {
            themeMenu.style.display = themeMenu.style.display === 'block' ? 'none' : 'block';
        }
    }
    setTheme(theme) {
        this.html.setAttribute('data-theme', theme);
        localStorage.setItem('theme', theme);
        this.updateThemeInfo(theme);
        this.updateThemeIcon(theme);
        this.updateThemePreview(theme);
        const themeMenu = document.getElementById('theme-menu');
        if (themeMenu) {
            themeMenu.style.display = 'none';
        }
    }
    getThemeColors(theme) {
        const colors = {
            'light': { primary: '#3b82f6', secondary: '#a855f7', accent: '#14b8a6', bg: '#ffffff' },
            'dark': { primary: '#3b82f6', secondary: '#a855f7', accent: '#14b8a6', bg: '#0f172a' },
            'sunset': { primary: '#e94560', secondary: '#533483', accent: '#fbbf24', bg: '#1a1a2e' },
            'teal': { primary: '#14b8a6', secondary: '#06b6d4', accent: '#f472b6', bg: '#0f172a' },
            'gray': { primary: '#64748b', secondary: '#94a3b8', accent: '#94a3b8', bg: '#fafafa' },
            'festive': { primary: '#dc2626', secondary: '#d97706', accent: '#f97316', bg: '#fef2f2' }
        };
        return colors[theme] || colors['light'];
    }
    getThemeDescription(theme) {
        const descriptions = {
            'light': '明亮清爽的浅色主题，适合白天使用',
            'dark': '护眼舒适的深色主题，适合夜间使用',
            'sunset': '温暖浪漫的日落主题，红紫渐变配色',
            'teal': '清新自然的深青色主题，绿色系配色',
            'gray': '庄重肃穆的灰色主题，适合公祭日',
            'festive': '喜庆热烈的节日主题，适合国庆春节'
        };
        return descriptions[theme] || '未定义主题';
    }
    updateThemeInfo(theme) {
        const themeNames = {
            'light': '浅色主题',
            'dark': '深色主题',
            'sunset': '日落主题',
            'teal': '深青色主题',
            'gray': '灰色主题',
            'festive': '喜庆主题'
        };
        const colors = this.getThemeColors(theme);
        const description = this.getThemeDescription(theme);
        const savedTheme = localStorage.getItem('theme');
        const isSystemDefault = !savedTheme;
        if (this.themeInfo) {
            this.themeInfo.textContent = `主题: ${themeNames[theme] || theme}`;
            this.themeInfo.setAttribute('data-theme', theme);
            this.themeInfo.setAttribute('data-primary-color', colors.primary);
            this.themeInfo.setAttribute('data-secondary-color', colors.secondary);
            this.themeInfo.setAttribute('data-accent-color', colors.accent);
            this.themeInfo.setAttribute('data-bg-color', colors.bg);
            this.themeInfo.setAttribute('data-theme-description', description);
            this.themeInfo.setAttribute('data-is-system-default', isSystemDefault);
            this.themeInfo.setAttribute('data-theme-source', isSystemDefault ? 'system' : 'user');
        }
    }
    updateThemeIcon(theme) {
        if (this.themeIcon) {
            const icons = {
                'light': 'fa-sun',
                'dark': 'fa-moon',
                'sunset': 'fa-sunset',
                'teal': 'fa-water',
                'gray': 'fa-cloud',
                'festive': 'fa-star'
            };
            const currentIcon = this.themeIcon.classList[1];
            this.themeIcon.classList.remove(currentIcon);
            this.themeIcon.classList.add(icons[theme] || 'fa-moon');
        }
    }
    updateThemePreview(theme) {
        const colors = this.getThemeColors(theme);
        if (this.themeInfo) {
            this.themeInfo.style.color = colors.primary;
        }
        const colorPreview = document.getElementById('theme-color-preview');
        if (colorPreview) {
            colorPreview.style.background = `linear-gradient(135deg, ${colors.primary} 0%, ${colors.secondary} 50%, ${colors.accent} 100%)`;
            colorPreview.style.borderColor = colors.primary;
        }
    }
    getTheme() {
        return this.html.getAttribute('data-theme') || 'light';
    }
    getCurrentThemeInfo() {
        const theme = this.getTheme();
        const colors = this.getThemeColors(theme);
        const description = this.getThemeDescription(theme);
        const savedTheme = localStorage.getItem('theme');
        return {
            theme: theme,
            name: this.getThemeName(theme),
            colors: colors,
            description: description,
            isSystemDefault: !savedTheme,
            source: savedTheme ? 'user' : 'system'
        };
    }
    getThemeName(theme) {
        const themeNames = {
            'light': '浅色主题',
            'dark': '深色主题',
            'sunset': '日落主题',
            'teal': '深青色主题',
            'gray': '灰色主题',
            'festive': '喜庆主题'
        };
        return themeNames[theme] || theme;
    }
    getAvailableThemes() {
        return [
            { id: 'light', name: '浅色主题', icon: 'fa-sun', description: '明亮清爽的浅色主题' },
            { id: 'dark', name: '深色主题', icon: 'fa-moon', description: '护眼舒适的深色主题' },
            { id: 'sunset', name: '日落主题', icon: 'fa-sunset', description: '温暖浪漫的日落主题' },
            { id: 'teal', name: '深青色主题', icon: 'fa-water', description: '清新自然的深青色主题' },
            { id: 'gray', name: '灰色主题', icon: 'fa-cloud', description: '庄重肃穆的灰色主题' },
            { id: 'festive', name: '喜庆主题', icon: 'fa-star', description: '喜庆热烈的节日主题' }
        ];
    }
    resetToSystemDefault() {
        localStorage.removeItem('theme');
        if (window.matchMedia('(prefers-color-scheme: dark)').matches) {
            this.setTheme('dark');
        } else {
            this.setTheme('light');
        }
    }
}
window.switchTheme = function(theme) {
    if (window.themeManager) {
        window.themeManager.setTheme(theme);
    }
};
document.addEventListener('DOMContentLoaded', () => {
    window.themeManager = new ThemeManager();
});
class PerformanceOptimizer {
    constructor() {
        this.init();
    }
    init() {
        this.lazyLoad();
        this.optimizeImages();
    }
    lazyLoad() {
        if ('IntersectionObserver' in window) {
            const imageObserver = new IntersectionObserver((entries, observer) => {
                entries.forEach(entry => {
                    if (entry.isIntersecting) {
                        const image = entry.target;
                        image.src = image.dataset.src;
                        imageObserver.unobserve(image);
                    }
                });
            });
            const images = document.querySelectorAll('img[data-src]');
            images.forEach(image => {
                imageObserver.observe(image);
            });
        }
        if ('IntersectionObserver' in window) {
            const videoObserver = new IntersectionObserver((entries, observer) => {
                entries.forEach(entry => {
                    if (entry.isIntersecting) {
                        const video = entry.target;
                        video.src = video.dataset.src;
                        videoObserver.unobserve(video);
                    }
                });
            });
            const videos = document.querySelectorAll('video[data-src]');
            videos.forEach(video => {
                videoObserver.observe(video);
            });
        }
    }
    optimizeImages() {
        const images = document.querySelectorAll('img');
        images.forEach(image => {
            if (!image.src.includes('.webp') && !image.src.includes('.avif')) {
            }
            if (!image.alt) {
                image.alt = '未命名图片';
            }
        });
    }
}