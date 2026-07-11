/**
 * MTSCOS AI System - 智能主题管理器
 * 版本: 4.4.0
 * 描述: 根据时间自动切换主题，支持用户手动切换和系统主题跟随
 */

class SmartThemeManager {
    constructor() {
        this.currentTheme = 'auto';
        this.userPreference = null;
        this.themeTimer = null;
        this.themes = this.initThemes();
        this.autoMode = true;
        
        this.init();
    }

    // ==================== 主题定义 ====================

    initThemes() {
        return {
            'light': {
                id: 'light',
                name: '明亮模式',
                description: '适合白天使用，清爽明亮',
                timeRange: { start: 6, end: 18 },
                colors: {
                    '--bg-primary': '#ffffff',
                    '--bg-secondary': '#f8fafc',
                    '--bg-tertiary': '#f1f5f9',
                    '--bg-card': '#ffffff',
                    '--bg-hover': '#e2e8f0',
                    '--bg-input': '#ffffff',
                    '--text-primary': '#0f172a',
                    '--text-secondary': '#475569',
                    '--text-tertiary': '#64748b',
                    '--border-color': '#e2e8f0',
                    '--border-color-focus': '#3b82f6',
                    '--shadow-sm': '0 1px 2px rgba(0, 0, 0, 0.05)',
                    '--shadow-md': '0 4px 6px rgba(0, 0, 0, 0.1)',
                    '--accent-glow': '0 0 20px rgba(59, 130, 246, 0.3)'
                },
                icon: 'fa-sun'
            },
            'dark': {
                id: 'dark',
                name: '深色模式',
                description: '适合夜晚使用，护眼舒适',
                timeRange: { start: 18, end: 6 },
                colors: {
                    '--bg-primary': '#0f172a',
                    '--bg-secondary': '#1e293b',
                    '--bg-tertiary': '#334155',
                    '--bg-card': '#1e293b',
                    '--bg-hover': '#334155',
                    '--bg-input': '#1e293b',
                    '--text-primary': '#f8fafc',
                    '--text-secondary': '#cbd5e1',
                    '--text-tertiary': '#94a3b8',
                    '--border-color': '#334155',
                    '--border-color-focus': '#60a5fa',
                    '--shadow-sm': '0 1px 2px rgba(0, 0, 0, 0.4)',
                    '--shadow-md': '0 4px 6px rgba(0, 0, 0, 0.4)',
                    '--accent-glow': '0 0 20px rgba(96, 165, 250, 0.3)'
                },
                icon: 'fa-moon'
            },
            'sunset': {
                id: 'sunset',
                name: '日落模式',
                description: '黄昏时分的温暖色调',
                timeRange: { start: 16, end: 20 },
                colors: {
                    '--bg-primary': '#fff7ed',
                    '--bg-secondary': '#ffedd5',
                    '--bg-tertiary': '#fed7aa',
                    '--bg-card': '#ffffff',
                    '--bg-hover': '#fed7aa',
                    '--bg-input': '#ffffff',
                    '--text-primary': '#7c2d12',
                    '--text-secondary': '#9a3412',
                    '--text-tertiary': '#c2410c',
                    '--border-color': '#fed7aa',
                    '--border-color-focus': '#f97316',
                    '--shadow-sm': '0 1px 2px rgba(249, 115, 22, 0.1)',
                    '--shadow-md': '0 4px 6px rgba(249, 115, 22, 0.15)',
                    '--accent-glow': '0 0 20px rgba(249, 115, 22, 0.3)'
                },
                icon: 'fa-sunset'
            },
            'ocean': {
                id: 'ocean',
                name: '海洋模式',
                description: '清凉的海洋色调，适合夏季',
                timeRange: { start: 10, end: 16 },
                colors: {
                    '--bg-primary': '#f0f9ff',
                    '--bg-secondary': '#e0f2fe',
                    '--bg-tertiary': '#bae6fd',
                    '--bg-card': '#ffffff',
                    '--bg-hover': '#bae6fd',
                    '--bg-input': '#ffffff',
                    '--text-primary': '#0c4a6e',
                    '--text-secondary': '#075985',
                    '--text-tertiary': '#0369a1',
                    '--border-color': '#bae6fd',
                    '--border-color-focus': '#0ea5e9',
                    '--shadow-sm': '0 1px 2px rgba(14, 165, 233, 0.1)',
                    '--shadow-md': '0 4px 6px rgba(14, 165, 233, 0.15)',
                    '--accent-glow': '0 0 20px rgba(14, 165, 233, 0.3)'
                },
                icon: 'fa-water'
            },
            'forest': {
                id: 'forest',
                name: '森林模式',
                description: '自然的绿色调，护眼舒适',
                timeRange: { start: 8, end: 18 },
                colors: {
                    '--bg-primary': '#f0fdf4',
                    '--bg-secondary': '#dcfce7',
                    '--bg-tertiary': '#bbf7d0',
                    '--bg-card': '#ffffff',
                    '--bg-hover': '#bbf7d0',
                    '--bg-input': '#ffffff',
                    '--text-primary': '#14532d',
                    '--text-secondary': '#166534',
                    '--text-tertiary': '#15803d',
                    '--border-color': '#bbf7d0',
                    '--border-color-focus': '#22c55e',
                    '--shadow-sm': '0 1px 2px rgba(34, 197, 94, 0.1)',
                    '--shadow-md': '0 4px 6px rgba(34, 197, 94, 0.15)',
                    '--accent-glow': '0 0 20px rgba(34, 197, 94, 0.3)'
                },
                icon: 'fa-tree'
            }
        };
    }

    // ==================== 初始化 ====================

    init() {
        this.loadUserPreference();
        
        if (this.userPreference === 'auto') {
            this.autoMode = true;
            this.switchToAuto();
        } else if (this.userPreference && this.themes[this.userPreference]) {
            this.autoMode = false;
            this.setTheme(this.userPreference);
        } else {
            this.autoMode = true;
            this.switchToAuto();
        }

        this.setupEventListeners();
    }

    loadUserPreference() {
        const stored = localStorage.getItem('mtscos_theme_preference');
        if (stored) {
            this.userPreference = stored;
        }
    }

    saveUserPreference(theme) {
        this.userPreference = theme;
        localStorage.setItem('mtscos_theme_preference', theme);
    }

    // ==================== 时间检测 ====================

    getCurrentHour() {
        return new Date().getHours();
    }

    getCurrentTimeOfDay() {
        const hour = this.getCurrentHour();
        
        if (hour >= 5 && hour < 8) return 'dawn';
        if (hour >= 8 && hour < 12) return 'morning';
        if (hour >= 12 && hour < 14) return 'noon';
        if (hour >= 14 && hour < 17) return 'afternoon';
        if (hour >= 17 && hour < 20) return 'sunset';
        if (hour >= 20 && hour < 23) return 'evening';
        return 'night';
    }

    getThemeByTime() {
        const timeOfDay = this.getCurrentTimeOfDay();
        
        switch (timeOfDay) {
            case 'dawn':
                return 'sunset';
            case 'morning':
                return 'forest';
            case 'noon':
                return 'ocean';
            case 'afternoon':
                return 'light';
            case 'sunset':
                return 'sunset';
            case 'evening':
                return 'dark';
            case 'night':
                return 'dark';
            default:
                return 'light';
        }
    }

    // ==================== 主题切换 ====================

    setTheme(themeId) {
        const theme = this.themes[themeId];
        if (!theme) return;

        this.currentTheme = themeId;
        this.applyTheme(theme);
        this.notifyThemeChange(theme);
    }

    applyTheme(theme) {
        const root = document.documentElement;
        
        Object.entries(theme.colors).forEach(([key, value]) => {
            root.style.setProperty(key, value);
        });

        document.body.setAttribute('data-theme', theme.id);
    }

    switchToAuto() {
        this.autoMode = true;
        this.saveUserPreference('auto');
        
        const themeId = this.getThemeByTime();
        this.setTheme(themeId);
        
        this.startTimer();
    }

    switchToManual(themeId) {
        this.autoMode = false;
        this.saveUserPreference(themeId);
        this.stopTimer();
        this.setTheme(themeId);
    }

    toggleTheme() {
        const themes = Object.keys(this.themes);
        const currentIndex = themes.indexOf(this.currentTheme);
        const nextIndex = (currentIndex + 1) % themes.length;
        this.switchToManual(themes[nextIndex]);
    }

    // ==================== 定时检测 ====================

    startTimer() {
        this.stopTimer();
        
        this.themeTimer = setInterval(() => {
            if (!this.autoMode) return;
            
            const newTheme = this.getThemeByTime();
            if (newTheme !== this.currentTheme) {
                this.setTheme(newTheme);
            }
        }, 60000);
    }

    stopTimer() {
        if (this.themeTimer) {
            clearInterval(this.themeTimer);
            this.themeTimer = null;
        }
    }

    // ==================== 事件监听 ====================

    setupEventListeners() {
        document.addEventListener('mtscos:theme:toggle', () => {
            this.toggleTheme();
        });

        document.addEventListener('mtscos:theme:set', (e) => {
            if (e.detail?.theme) {
                this.switchToManual(e.detail.theme);
            }
        });

        document.addEventListener('mtscos:theme:auto', () => {
            this.switchToAuto();
        });

        window.matchMedia('(prefers-color-scheme: dark)').addEventListener('change', (e) => {
            if (this.userPreference === 'auto') {
                if (e.matches) {
                    this.setTheme('dark');
                } else {
                    this.setTheme('light');
                }
            }
        });
    }

    notifyThemeChange(theme) {
        const event = new CustomEvent('mtscos:theme:changed', {
            detail: {
                theme: theme.id,
                name: theme.name,
                description: theme.description,
                timeOfDay: this.getCurrentTimeOfDay(),
                isAuto: this.autoMode
            }
        });
        document.dispatchEvent(event);
    }

    // ==================== 主题信息 ====================

    getCurrentThemeInfo() {
        return {
            id: this.currentTheme,
            name: this.themes[this.currentTheme]?.name || '未知',
            isAuto: this.autoMode,
            timeOfDay: this.getCurrentTimeOfDay(),
            hour: this.getCurrentHour()
        };
    }

    getAllThemes() {
        return Object.values(this.themes);
    }

    getThemeOptions() {
        return Object.entries(this.themes).map(([id, theme]) => ({
            value: id,
            label: theme.name,
            description: theme.description,
            icon: theme.icon
        }));
    }

    // ==================== 快捷方法 ====================

    isDark() {
        return this.currentTheme === 'dark';
    }

    isLight() {
        return this.currentTheme === 'light';
    }

    getStatus() {
        return {
            currentTheme: this.currentTheme,
            themeName: this.themes[this.currentTheme]?.name,
            autoMode: this.autoMode,
            timeOfDay: this.getCurrentTimeOfDay(),
            hour: this.getCurrentHour(),
            totalThemes: Object.keys(this.themes).length
        };
    }
}

// 创建全局实例
window.smartThemeManager = new SmartThemeManager();

// 导出
window.MTSCOS_SmartThemeManager = SmartThemeManager;
