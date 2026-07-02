// AI主题管理器 - 统一所有页面配色和布局方案
window.ThemeManager = {
    // 当前主题
    currentTheme: 'dark',
    
    // 主题配置
    themes: {
        dark: {
            name: '科技暗黑',
            primary: '#667eea',
            secondary: '#764ba2',
            accent: '#3b82f6',
            background: 'linear-gradient(135deg, #1a1a2e 0%, #16213e 50%, #0f3460 100%)',
            textColor: '#ffffff',
            textMuted: 'rgba(255, 255, 255, 0.8)',
            cardBg: 'rgba(255, 255, 255, 0.1)',
            borderColor: 'rgba(255, 255, 255, 0.2)'
        },
        light: {
            name: '清爽浅色',
            primary: '#667eea',
            secondary: '#764ba2',
            accent: '#3b82f6',
            background: 'linear-gradient(135deg, #f8fafc 0%, #f1f5f9 100%)',
            textColor: '#1f2937',
            textMuted: '#4b5563',
            cardBg: 'rgba(255, 255, 255, 0.95)',
            borderColor: '#e5e7eb'
        },
        sunset: {
            name: '日落橙红',
            primary: '#f97316',
            secondary: '#ef4444',
            accent: '#f59e0b',
            background: 'linear-gradient(135deg, #fbbf24 0%, #f97316 50%, #ef4444 100%)',
            textColor: '#ffffff',
            textMuted: 'rgba(255, 255, 255, 0.9)',
            cardBg: 'rgba(255, 255, 255, 0.15)',
            borderColor: 'rgba(255, 255, 255, 0.25)'
        },
        ocean: {
            name: '海洋深蓝',
            primary: '#06b6d4',
            secondary: '#3b82f6',
            accent: '#0ea5e9',
            background: 'linear-gradient(135deg, #0c4a6e 0%, #164e63 50%, #0891b2 100%)',
            textColor: '#ffffff',
            textMuted: 'rgba(255, 255, 255, 0.85)',
            cardBg: 'rgba(255, 255, 255, 0.1)',
            borderColor: 'rgba(255, 255, 255, 0.2)'
        },
        forest: {
            name: '森林绿意',
            primary: '#22c55e',
            secondary: '#16a34a',
            accent: '#84cc16',
            background: 'linear-gradient(135deg, #14532d 0%, #15803d 50%, #22c55e 100%)',
            textColor: '#ffffff',
            textMuted: 'rgba(255, 255, 255, 0.85)',
            cardBg: 'rgba(255, 255, 255, 0.1)',
            borderColor: 'rgba(255, 255, 255, 0.2)'
        }
    },
    
    // 初始化主题管理器
    init: function() {
        this.loadTheme();
        this.applyTheme();
        this.createThemeSwitcher();
        this.log('AI主题管理器已启动');
    },
    
    // 加载保存的主题
    loadTheme: function() {
        const saved = localStorage.getItem('mtscos_theme');
        if (saved && this.themes[saved]) {
            this.currentTheme = saved;
        } else {
            this.currentTheme = this.detectSystemTheme();
        }
    },
    
    // 检测系统主题偏好
    detectSystemTheme: function() {
        if (window.matchMedia && window.matchMedia('(prefers-color-scheme: dark)').matches) {
            return 'dark';
        }
        return 'light';
    },
    
    // 应用主题
    applyTheme: function() {
        const theme = this.themes[this.currentTheme];
        if (!theme) return;
        
        // 设置CSS变量
        const root = document.documentElement;
        root.style.setProperty('--theme-primary', theme.primary);
        root.style.setProperty('--theme-secondary', theme.secondary);
        root.style.setProperty('--theme-accent', theme.accent);
        root.style.setProperty('--theme-bg', theme.background);
        root.style.setProperty('--theme-text', theme.textColor);
        root.style.setProperty('--theme-text-muted', theme.textMuted);
        root.style.setProperty('--theme-card-bg', theme.cardBg);
        root.style.setProperty('--theme-border', theme.borderColor);
        
        // 设置body背景
        document.body.style.background = theme.background;
        document.body.style.color = theme.textColor;
        
        // 更新meta主题色
        const metaTheme = document.querySelector('meta[name="theme-color"]');
        if (metaTheme) {
            metaTheme.content = theme.primary;
        }
        
        // 更新所有按钮
        this.updateButtons();
        
        // 更新所有卡片
        this.updateCards();
        
        // 更新所有输入框
        this.updateInputs();
        
        // 更新主题切换器显示
        this.updateThemeSwitcher();
        
        // 保存到localStorage
        localStorage.setItem('mtscos_theme', this.currentTheme);
        
        this.log(`已应用主题: ${theme.name}`);
    },
    
    // 更新按钮样式
    updateButtons: function() {
        const theme = this.themes[this.currentTheme];
        const buttons = document.querySelectorAll('button');
        
        buttons.forEach(btn => {
            if (btn.classList.contains('btn-primary')) {
                btn.style.background = `linear-gradient(135deg, ${theme.primary} 0%, ${theme.secondary} 100%)`;
            } else if (btn.classList.contains('btn-secondary')) {
                btn.style.borderColor = theme.primary;
                btn.style.color = theme.primary;
            }
        });
    },
    
    // 更新卡片样式
    updateCards: function() {
        const theme = this.themes[this.currentTheme];
        const cards = document.querySelectorAll('.glass-card, .glass-card-light');
        
        cards.forEach(card => {
            card.style.background = theme.cardBg;
            card.style.borderColor = theme.borderColor;
        });
    },
    
    // 更新输入框样式
    updateInputs: function() {
        const theme = this.themes[this.currentTheme];
        const inputs = document.querySelectorAll('input, textarea, select');
        
        inputs.forEach(input => {
            if (!input.classList.contains('no-theme')) {
                input.style.borderColor = theme.borderColor;
                input.style.color = theme.textColor;
                input.style.background = theme.cardBg;
            }
        });
    },
    
    // 切换主题
    switchTheme: function(themeName) {
        if (this.themes[themeName]) {
            this.currentTheme = themeName;
            this.applyTheme();
            this.notifyThemeChange();
        }
    },
    
    // 创建主题切换器
    createThemeSwitcher: function() {
        // 如果已存在则跳过
        if (document.getElementById('theme-switcher')) return;
        
        const switcher = document.createElement('div');
        switcher.id = 'theme-switcher';
        switcher.style.cssText = `
            position: fixed;
            top: 20px;
            right: 20px;
            z-index: 9999;
        `;
        
        const btn = document.createElement('button');
        btn.id = 'theme-btn';
        btn.title = '切换主题';
        btn.style.cssText = `
            background: rgba(102, 126, 234, 0.8);
            border: none;
            border-radius: 50%;
            width: 44px;
            height: 44px;
            display: flex;
            align-items: center;
            justify-content: center;
            cursor: pointer;
            transition: all 0.3s ease;
            box-shadow: 0 4px 15px rgba(102, 126, 234, 0.4);
        `;
        
        btn.innerHTML = `<svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="white" stroke-width="2"><circle cx="12" cy="12" r="5"/><line x1="12" y1="1" x2="12" y2="3"/><line x1="12" y1="21" x2="12" y2="23"/><line x1="4.22" y1="4.22" x2="5.64" y2="5.64"/><line x1="18.36" y1="18.36" x2="19.78" y2="19.78"/><line x1="1" y1="12" x2="3" y2="12"/><line x1="21" y1="12" x2="23" y2="12"/><line x1="4.22" y1="19.78" x2="5.64" y2="18.36"/><line x1="18.36" y1="5.64" x2="19.78" y2="4.22"/></svg>`;
        
        btn.onclick = () => this.toggleThemeMenu();
        
        // 主题菜单
        const menu = document.createElement('div');
        menu.id = 'theme-menu';
        menu.style.cssText = `
            position: absolute;
            top: 50px;
            right: 0;
            background: rgba(30, 30, 50, 0.95);
            backdrop-filter: blur(20px);
            border-radius: 12px;
            padding: 10px;
            display: none;
            flex-direction: column;
            gap: 8px;
            min-width: 160px;
            border: 1px solid rgba(255, 255, 255, 0.1);
            box-shadow: 0 10px 40px rgba(0, 0, 0, 0.3);
        `;
        
        // 添加主题选项
        Object.keys(this.themes).forEach(key => {
            const theme = this.themes[key];
            const option = document.createElement('button');
            option.style.cssText = `
                display: flex;
                align-items: center;
                gap: 10px;
                padding: 10px 15px;
                border: none;
                border-radius: 8px;
                background: transparent;
                color: ${key === this.currentTheme ? theme.primary : 'rgba(255,255,255,0.8)'};
                cursor: pointer;
                transition: all 0.2s;
                font-size: 14px;
                width: 100%;
                text-align: left;
            `;
            
            option.innerHTML = `
                <span style="width: 20px; height: 20px; border-radius: 50%; background: ${theme.primary};"></span>
                ${theme.name}
                ${key === this.currentTheme ? '<span style="margin-left: auto;">✓</span>' : ''}
            `;
            
            option.onclick = () => {
                this.switchTheme(key);
                this.toggleThemeMenu();
            };
            
            option.onmouseenter = () => {
                option.style.background = 'rgba(255, 255, 255, 0.1)';
            };
            
            option.onmouseleave = () => {
                option.style.background = 'transparent';
            };
            
            menu.appendChild(option);
        });
        
        switcher.appendChild(btn);
        switcher.appendChild(menu);
        document.body.appendChild(switcher);
        
        // 点击外部关闭菜单
        document.addEventListener('click', (e) => {
            if (!switcher.contains(e.target)) {
                menu.style.display = 'none';
            }
        });
        
        this.log('主题切换器已创建');
    },
    
    // 切换主题菜单显示
    toggleThemeMenu: function() {
        const menu = document.getElementById('theme-menu');
        if (menu) {
            menu.style.display = menu.style.display === 'flex' ? 'none' : 'flex';
        }
    },
    
    // 更新主题切换器显示
    updateThemeSwitcher: function() {
        const theme = this.themes[this.currentTheme];
        const btn = document.getElementById('theme-btn');
        const menu = document.getElementById('theme-menu');
        
        if (btn) {
            btn.style.background = theme.primary;
        }
        
        if (menu) {
            const options = menu.querySelectorAll('button');
            options.forEach((opt, index) => {
                const keys = Object.keys(this.themes);
                const key = keys[index];
                const optTheme = this.themes[key];
                opt.style.color = key === this.currentTheme ? optTheme.primary : 'rgba(255,255,255,0.8)';
                opt.innerHTML = `
                    <span style="width: 20px; height: 20px; border-radius: 50%; background: ${optTheme.primary};"></span>
                    ${optTheme.name}
                    ${key === this.currentTheme ? '<span style="margin-left: auto;">✓</span>' : ''}
                `;
            });
        }
    },
    
    // 通知主题变更
    notifyThemeChange: function() {
        const event = new CustomEvent('themeChange', {
            detail: {
                theme: this.currentTheme,
                config: this.themes[this.currentTheme]
            }
        });
        window.dispatchEvent(event);
        
        this.log(`主题已切换为: ${this.themes[this.currentTheme].name}`);
    },
    
    // 获取当前主题配置
    getCurrentTheme: function() {
        return this.themes[this.currentTheme];
    },
    
    // 获取所有主题列表
    getThemes: function() {
        return this.themes;
    },
    
    // AI智能推荐主题
    recommendTheme: function() {
        const hour = new Date().getHours();
        
        if (hour >= 6 && hour < 12) {
            return 'ocean';
        } else if (hour >= 12 && hour < 18) {
            return 'light';
        } else if (hour >= 18 && hour < 21) {
            return 'sunset';
        } else {
            return 'dark';
        }
    },
    
    // 应用AI推荐主题
    applyRecommendedTheme: function() {
        const recommended = this.recommendTheme();
        if (recommended !== this.currentTheme) {
            this.switchTheme(recommended);
            this.log(`AI推荐主题: ${this.themes[recommended].name}`);
        }
    },
    
    // 日志记录
    log: function(msg) {
        console.log('[AI-Theme] ' + msg);
    }
};

// 页面加载时初始化
document.addEventListener('DOMContentLoaded', function() {
    window.ThemeManager.init();
});

// 如果页面已加载，立即初始化
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', function() {
        window.ThemeManager.init();
    });
} else {
    window.ThemeManager.init();
}