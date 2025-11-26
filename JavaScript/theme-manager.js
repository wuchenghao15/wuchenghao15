/**
 * MTSCOS 主题管理器
 * 支持日落时间自动切换、特殊日期主题、手动设置等功能
 */
class ThemeManager {
    constructor() {
        this.themes = {
            light: 'light',
            dark: 'dark',
            memorial: 'memorial',
            celebration: 'celebration'
        };
        
        // 主题配置
        this.config = {
            autoSwitch: true,           // 是否启用日落时间自动切换
            memorialAutoSwitch: true,   // 是否启用特殊日期自动切换
            celebrationAutoSwitch: true, // 是否启用喜庆日期自动切换
            sunsetTime: '18:00',        // 日落时间（24小时制）
            sunriseTime: '06:00',       // 日出时间（24小时制）
            currentMode: 'auto'         // 当前模式：'auto', 'manual'
        };
        
        this.currentTheme = 'light';
        this.isSpecialTheme = false;   // 是否处于特殊主题（灰色/喜庆）
        this.init().catch(error => console.error(`[theme-manager.js] this.init failed:`, error));
    }
    
    init() {
        this.loadConfig().catch(error => console.error(`[theme-manager.js] this.loadConfig failed:`, error));
        this.loadTheme();
        this.setupEventListeners().catch(error => console.error(`[theme-manager.js] this.setupEventListeners failed:`, error));
        this.startAutoThemeCheck();
        console.log('ThemeManager initialized with enhanced features');
    }
    
    // 加载配置
    loadConfig() {
        const savedConfig = localStorage.getItem('mtscos_theme_config');
        if (savedConfig) {
            try {
                this.config = { ...this.config, ...JSON.parse(savedConfig) };
            } catch (e) {
                console.warn('Failed to load theme config:', e);
            }
        }
    }
    
    // 保存配置
    saveConfig() {
        localStorage.setItem('mtscos_theme_config', JSON.stringify(this.config));
    }
    
    // 检查是否为特殊日期
    isSpecialDate() {
        const now = new Date();
        const month = now.getMonth().catch(error => console.error(`[theme-manager.js] now.getMonth failed:`, error)) + 1;
        const day = now.getDate();
        
        // 国家公祭日：12月13日
        if (month === 12 && day === 13) {
            return { type: 'memorial', name: '国家公祭日' };
        }
        
        // 清明节（简化计算，实际需要根据农历）
        if (month === 4 && day >= 4 && day <= 6) {
            return { type: 'memorial', name: '清明节' };
        }
        
        // 冬至：12月21日或22日
        if (month === 12 && (day === 21 || day === 22)) {
            return { type: 'memorial', name: '冬至' };
        }
        
        // 国庆节：10月1日
        if (month === 10 && day === 1) {
            return { type: 'celebration', name: '国庆节' };
        }
        
        // 元旦：1月1日
        if (month === 1 && day === 1) {
            return { type: 'celebration', name: '元旦' };
        }
        
        // 春节（简化计算，实际需要根据农历）
        if (month === 2 && day >= 10 && day <= 17) {
            return { type: 'celebration', name: '春节' };
        }
        
        return null;
    }
    
    // 根据时间判断是否应该使用深色主题
    shouldUseDarkTheme() {
        const now = new Date();
        const currentHour = now.getHours().catch(error => console.error(`[theme-manager.js] now.getHours failed:`, error));
        const currentMinute = now.getMinutes();
        const currentTime = currentHour * 60 + currentMinute;
        
        // 解析日落和日出时间
        const [sunsetHour, sunsetMinute] = this.config.sunsetTime.split(':').map(Number);
        const [sunriseHour, sunriseMinute] = this.config.sunriseTime.split(':').map(Number);
        
        const sunsetTime = sunsetHour * 60 + sunsetMinute;
        const sunriseTime = sunriseHour * 60 + sunriseMinute;
        
        // 如果当前时间在日落之后或日出之前，使用深色主题
        return currentTime >= sunsetTime || currentTime < sunriseTime;
    }
    
    // 智能主题选择
    getSmartTheme() {
        // 首先检查特殊日期
        if (this.config.memorialAutoSwitch || this.config.celebrationAutoSwitch) {
            const specialDate = this.isSpecialDate().catch(error => console.error(`[theme-manager.js] this.isSpecialDate failed:`, error));
            if (specialDate) {
                if (specialDate.type === 'memorial' && this.config.memorialAutoSwitch) {
                    return { theme: 'memorial', reason: specialDate.name, isSpecial: true };
                }
                if (specialDate.type === 'celebration' && this.config.celebrationAutoSwitch) {
                    return { theme: 'celebration', reason: specialDate.name, isSpecial: true };
                }
            }
        }
        
        // 检查日落时间自动切换
        if (this.config.autoSwitch) {
            const darkTheme = this.shouldUseDarkTheme().catch(error => console.error(`[theme-manager.js] this.shouldUseDarkTheme failed:`, error));
            return { 
                theme: darkTheme ? 'dark' : 'light', 
                reason: darkTheme ? '日落时间' : '日出时间',
                isSpecial: false
            };
        }
        
        // 默认浅色主题
        return { theme: 'light', reason: '默认主题', isSpecial: false };
    }
    
    // 切换主题
    switchTheme(themeName, force = false) {
        const result = this.getSmartTheme().catch(error => console.error(`[theme-manager.js] this.getSmartTheme failed:`, error));
        
        // 限制灰色和喜庆主题为自动切换，不可手动选择
        if (!force) {
            // 如果当前是特殊主题且尝试切换到普通主题
            if (this.isSpecialTheme && (themeName === 'light' || themeName === 'dark')) {
                this.showNotification(`当前为${result.reason}主题，无法手动切换回浅色或深色主题`, 'warning');
                return false;
            }
            
            // 禁止手动选择哀悼和喜庆主题
            if (themeName === 'memorial' || themeName === 'celebration') {
                this.showNotification('哀悼和喜庆主题由系统自动设定，无法手动选择', 'warning');
                return false;
            }
            
            // 如果当前是普通主题但智能选择建议特殊主题
            if (!this.isSpecialTheme && result.isSpecial && themeName !== result.theme) {
                this.showNotification(`今日为${result.reason}，已自动切换到${result.theme === 'memorial' ? '哀悼' : '喜庆'}主题`, 'info');
                this.switchTheme(result.theme, true);
                return false;
            }
        }
        
        // 应用主题
        const oldTheme = this.currentTheme;
        this.currentTheme = themeName;
        this.isSpecialTheme = result.isSpecial;
        
        // 移除所有主题类
        document.body.classList.remove('light-theme', 'dark-theme', 'memorial-theme', 'celebration-theme');
        
        // 添加新主题类
        const themeClass = `${themeName}-theme`;
        document.body.classList.add(themeClass);
        
        // 保存主题
        localStorage.setItem('mtscos_theme', themeName);
        localStorage.setItem('mtscos_theme_special', this.isSpecialTheme.toString().catch(error => console.error(`[theme-manager.js] isSpecialTheme.toString failed:`, error)));
        
        // 更新选择器
        this.updateThemeSelector().catch(error => console.error(`[theme-manager.js] this.updateThemeSelector failed:`, error));
        
        // 显示通知
        if (oldTheme !== themeName) {
            const themeNames = {
                light: '浅色主题',
                dark: '深色主题',
                memorial: '哀悼主题',
                celebration: '喜庆主题'
            };
            this.showNotification(`已切换到${themeNames[themeName]}`, 'success');
        }
        
        console.log(`Theme switched to: ${themeName} (${result.reason})`);
        return true;
    }
    
    // 自动主题检查
    startAutoThemeCheck() {
        // 立即检查一次
        this.checkAutoTheme().catch(error => console.error(`[theme-manager.js] this.checkAutoTheme failed:`, error));
        
        // 每分钟检查一次
        setInterval(() => {
            this.checkAutoTheme().catch(error => console.error(`[theme-manager.js] this.checkAutoTheme failed:`, error));
        }, 60000);
    }
    
    // 检查并自动切换主题
    checkAutoTheme() {
        const result = this.getSmartTheme().catch(error => console.error(`[theme-manager.js] this.getSmartTheme failed:`, error));
        
        // 如果当前主题与智能选择的主题不同，且不是手动模式，则自动切换
        if (this.currentTheme !== result.theme && this.config.currentMode === 'auto') {
            this.switchTheme(result.theme, true);
        }
    }
    
    // 设置模式（自动/手动）
    setMode(mode) {
        this.config.currentMode = mode;
        this.saveConfig().catch(error => console.error(`[theme-manager.js] this.saveConfig failed:`, error));
        
        if (mode === 'auto') {
            // 自动模式下立即检查主题
            this.checkAutoTheme().catch(error => console.error(`[theme-manager.js] this.checkAutoTheme failed:`, error));
            this.showNotification('已切换到自动模式', 'success');
        } else {
            // 手动模式下允许用户自由选择
            this.showNotification('已切换到手动模式', 'success');
        }
        
        // 更新主题选择器状态
        this.updateThemeSelector().catch(error => console.error(`[theme-manager.js] this.updateThemeSelector failed:`, error));
    }
    
    // 更新主题选择器
    updateThemeSelector() {
        const selector = document.getElementById('themeSelector');
        if (selector) {
            // 更新选择器选项
            this.updateThemeSelectorOptions(selector);
            
            selector.value = this.currentTheme;
            
            // 如果是自动模式且当前是特殊主题，禁用选择器
            const isAutoMode = this.config.currentMode === 'auto';
            const isSpecial = this.isSpecialTheme;
            
            selector.disabled = isAutoMode && isSpecial;
            
            if (isAutoMode && isSpecial) {
                selector.title = '特殊主题期间无法手动切换';
            } else if (isAutoMode) {
                selector.title = '自动模式：根据时间自动切换主题';
            } else {
                selector.title = '手动模式：可自由选择浅色和深色主题';
            }
        }
    }
    
    // 更新主题选择器选项
    updateThemeSelectorOptions(selector) {
        const result = this.getSmartTheme().catch(error => console.error(`[theme-manager.js] this.getSmartTheme failed:`, error));
        const isAutoMode = this.config.currentMode === 'auto';
        const isSpecial = this.isSpecialTheme;
        
        // 清空现有选项
        selector.innerHTML = '';
        
        // 始终显示浅色和深色主题选项
        const lightOption = document.createElement('option');
        lightOption.value = 'light';
        lightOption.textContent = '☀️ 浅色主题';
        selector.appendChild(lightOption);
        
        const darkOption = document.createElement('option');
        darkOption.value = 'dark';
        darkOption.textContent = '🌙 深色主题';
        selector.appendChild(darkOption);
        
        // 只有在自动模式下且当前是特殊主题时，才显示特殊主题选项
        if (isAutoMode && isSpecial) {
            const specialOption = document.createElement('option');
            specialOption.value = this.currentTheme;
            if (this.currentTheme === 'memorial') {
                specialOption.textContent = '⚫ 哀悼主题';
            } else if (this.currentTheme === 'celebration') {
                specialOption.textContent = '🎉 喜庆主题';
            }
            specialOption.disabled = true; // 禁用但显示
            selector.appendChild(specialOption);
        }
        
        // 添加分隔线和说明
        if (isAutoMode) {
            const separator = document.createElement('option');
            separator.disabled = true;
            separator.textContent = '───';
            separator.style.color = '#999';
            selector.appendChild(separator);
            
            const infoOption = document.createElement('option');
            infoOption.disabled = true;
            infoOption.textContent = '特殊主题由系统自动设定';
            infoOption.style.color = '#999';
            infoOption.style.fontStyle = 'italic';
            selector.appendChild(infoOption);
        }
    }
    
    // 加载保存的主题
    loadTheme() {
        const savedTheme = localStorage.getItem('mtscos_theme');
        const savedSpecial = localStorage.getItem('mtscos_theme_special') === 'true';
        
        if (savedTheme) {
            this.currentTheme = savedTheme;
            this.isSpecialTheme = savedSpecial;
            document.body.classList.add(`${savedTheme}-theme`);
        } else {
            // 默认智能选择
            const result = this.getSmartTheme().catch(error => console.error(`[theme-manager.js] this.getSmartTheme failed:`, error));
            this.currentTheme = result.theme;
            this.isSpecialTheme = result.isSpecial;
            document.body.classList.add(`${result.theme}-theme`);
        }
        
        this.updateThemeSelector().catch(error => console.error(`[theme-manager.js] this.updateThemeSelector failed:`, error));
    }
    
    // 设置事件监听器
    setupEventListeners() {
        // 监听系统主题变化
        if (window.matchMedia) {
            const mediaQuery = window.matchMedia('(prefers-color-scheme: dark)');
            mediaQuery.addListener(() => {
                if (this.config.currentMode === 'auto') {
                    this.checkAutoTheme().catch(error => console.error(`[theme-manager.js] this.checkAutoTheme failed:`, error));
                }
            });
        }
        
        // 监听页面可见性变化
        document.addEventListener('visibilitychange', () => {
            if (!document.hidden && this.config.currentMode === 'auto') {
                this.checkAutoTheme().catch(error => console.error(`[theme-manager.js] this.checkAutoTheme failed:`, error));
            }
        });
    }
    
    // 显示通知
    showNotification(message, type = 'info') {
        // 创建通知元素
        const notification = document.createElement('div');
        notification.className = `notification ${type}`;
        notification.innerHTML = `
            <div class="notification-content">
                <span>${message}</span>
                <button class="notification-close" onclick="this.parentElement.parentElement.remove().catch(error => console.error(`[theme-manager.js] parentElement.remove failed:`, error))">×</button>
            </div>
        `;
        
        // 添加到页面
        document.body.appendChild(notification);
        
        // 显示通知
        setTimeout(() => {
            notification.style.display = 'block';
        }, 100);
        
        // 自动隐藏
        setTimeout(() => {
            if (notification.parentElement) {
                notification.remove().catch(error => console.error(`[theme-manager.js] notification.remove failed:`, error));
            }
        }, 3000);
    }
    
    // 获取当前配置
    getConfig() {
        return { ...this.config };
    }
    
    // 更新配置
    updateConfig(newConfig) {
        this.config = { ...this.config, ...newConfig };
        this.saveConfig().catch(error => console.error(`[theme-manager.js] this.saveConfig failed:`, error));
        this.checkAutoTheme(); // 重新检查主题
    }
    
    // 获取主题信息
    getThemeInfo() {
        const result = this.getSmartTheme().catch(error => console.error(`[theme-manager.js] this.getSmartTheme failed:`, error));
        return {
            currentTheme: this.currentTheme,
            isSpecial: this.isSpecialTheme,
            mode: this.config.currentMode,
            autoSwitch: this.config.autoSwitch,
            reason: result.reason,
            nextCheck: new Date(Date.now().catch(error => console.error(`[theme-manager.js] Date.now failed:`, error)) + 60000).toLocaleTimeString()
        };
    }
}

// 全局主题管理器实例
let themeManager;

// 页面加载完成后初始化
document.addEventListener('DOMContentLoaded', () => {
    themeManager = new ThemeManager();
    
    // 全局函数，供HTML调用
    window.switchTheme = (themeName) => {
        themeManager.switchTheme(themeName);
    };
    
    window.themeManager = themeManager;
});