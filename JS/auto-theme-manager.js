/**
 * 自动主题管理器
 * 负责根据日出日落、公祭日、喜庆日自动切换主题
 */
class AutoThemeManager {
    constructor() {
        this.currentTheme = 'light';
        this.isSpecialDay = false;
        this.specialDayType = null;
        this.sunTimes = null;
        this.checkInterval = null;
        this.logManager = null;
        this.updateManager = null;
        
        // 公祭日列表（月-日格式）
        this.memorialDays = [
            '04-04', // 清明节
            '09-18', // 九一八事变纪念日
            '12-13', // 南京大屠杀死难者国家公祭日
            '07-07', // 七七事变纪念日
            '09-30', // 烈士纪念日
        ];
        
        // 喜庆日列表（月-日格式）
        this.celebrationDays = [
            '01-01', // 元旦
            '02-14', // 情人节
            '03-08', // 妇女节
            '05-01', // 劳动节
            '06-01', // 儿童节
            '10-01', // 国庆节
            '12-25', // 圣诞节
        ];
        
        // 农历喜庆日（需要农历计算）
        this.lunarCelebrationDays = [
            { month: 1, day: 1, name: '春节' },   // 正月初一
            { month: 1, day: 15, name: '元宵节' }, // 正月十五
            { month: 5, day: 5, name: '端午节' },  // 五月初五
            { month: 8, day: 15, name: '中秋节' }, // 八月十五
            { month: 9, day: 9, name: '重阳节' }, // 九月初九
        ];
        
        this.init();
    }
    
    async init() {
        try {
            // 初始化日志管理器
            this.logManager = window.logManager || new LogManager();
            
            // 初始化更新管理器
            this.updateManager = window.updateManager || new UpdateManager();
            
            // 获取用户位置（用于计算日出日落）
            await this.getUserLocation();
            
            // 计算今日日出日落时间
            await this.calculateSunTimes();
            
            // 检查是否为特殊日子
            this.checkSpecialDay();
            
            // 应用初始主题
            this.applyAutoTheme();
            
            // 启动定时检查（每分钟检查一次）
            this.startPeriodicCheck();
            
            this.logManager.info('AutoThemeManager', '自动主题管理器初始化完成');
            
        } catch (error) {
            console.error('AutoThemeManager初始化失败:', error);
            this.logManager.error('AutoThemeManager', `初始化失败: ${error.message}`);
        }
    }
    
    async getUserLocation() {
        return new Promise((resolve, reject) => {
            if (navigator.geolocation) {
                navigator.geolocation.getCurrentPosition(
                    (position) => {
                        this.userLocation = {
                            lat: position.coords.latitude,
                            lng: position.coords.longitude
                        };
                        resolve(this.userLocation);
                    },
                    (error) => {
                        // 默认使用北京位置
                        this.userLocation = { lat: 39.9042, lng: 116.4074 };
                        console.warn('获取位置失败，使用默认位置（北京）:', error);
                        resolve(this.userLocation);
                    }
                );
            } else {
                // 不支持地理位置，使用默认位置
                this.userLocation = { lat: 39.9042, lng: 116.4074 };
                resolve(this.userLocation);
            }
        });
    }
    
    async calculateSunTimes() {
        try {
            // 使用简化的日出日落计算公式
            const today = new Date();
            const dayOfYear = Math.floor((today - new Date(today.getFullYear(), 0, 0)) / 86400000);
            
            // 简化计算（实际应用中应该使用更精确的算法或API）
            const lat = this.userLocation.lat;
            const sunriseBase = 6; // 基础日出时间（小时）
            const sunsetBase = 18; // 基础日落时间（小时）
            
            // 根据纬度和日期调整
            const latFactor = Math.sin((dayOfYear - 81) * 2 * Math.PI / 365) * Math.cos(lat * Math.PI / 180);
            const sunriseHour = sunriseBase - latFactor * 2;
            const sunsetHour = sunsetBase + latFactor * 2;
            
            this.sunTimes = {
                sunrise: new Date(today.setHours(Math.floor(sunriseHour), (sunriseHour % 1) * 60, 0, 0)),
                sunset: new Date(today.setHours(Math.floor(sunsetHour), (sunsetHour % 1) * 60, 0, 0))
            };
            
            this.logManager.info('AutoThemeManager', `日出时间: ${this.sunTimes.sunrise.toLocaleTimeString()}, 日落时间: ${this.sunTimes.sunset.toLocaleTimeString()}`);
            
        } catch (error) {
            console.error('计算日出日落时间失败:', error);
            // 使用默认时间
            const today = new Date();
            this.sunTimes = {
                sunrise: new Date(today.setHours(6, 0, 0, 0)),
                sunset: new Date(today.setHours(18, 0, 0, 0))
            };
        }
    }
    
    checkSpecialDay() {
        const today = new Date();
        const monthDay = `${String(today.getMonth() + 1).padStart(2, '0')}-${String(today.getDate()).padStart(2, '0')}`;
        
        // 检查公祭日
        if (this.memorialDays.includes(monthDay)) {
            this.isSpecialDay = true;
            this.specialDayType = 'memorial';
            this.logManager.info('AutoThemeManager', `今日为公祭日: ${monthDay}`);
            return;
        }
        
        // 检查喜庆日
        if (this.celebrationDays.includes(monthDay)) {
            this.isSpecialDay = true;
            this.specialDayType = 'celebration';
            this.logManager.info('AutoThemeManager', `今日为喜庆日: ${monthDay}`);
            return;
        }
        
        // 检查农历喜庆日（简化处理）
        const lunarDate = this.getLunarDate(today);
        const lunarCelebration = this.lunarCelebrationDays.find(
            day => day.month === lunarDate.month && day.day === lunarDate.day
        );
        
        if (lunarCelebration) {
            this.isSpecialDay = true;
            this.specialDayType = 'celebration';
            this.logManager.info('AutoThemeManager', `今日为农历喜庆日: ${lunarCelebration.name}`);
            return;
        }
        
        this.isSpecialDay = false;
        this.specialDayType = null;
    }
    
    getLunarDate(date) {
        // 简化的农历转换（实际应用中应该使用完整的农历算法）
        // 这里仅作为示例，返回公历日期
        return {
            year: date.getFullYear(),
            month: date.getMonth() + 1,
            day: date.getDate()
        };
    }
    
    applyAutoTheme() {
        let newTheme;
        let themeReason;
        
        if (this.isSpecialDay) {
            // 特殊日子优先
            if (this.specialDayType === 'memorial') {
                newTheme = 'memorial';
                themeReason = '公祭日主题';
            } else if (this.specialDayType === 'celebration') {
                newTheme = 'celebration';
                themeReason = '喜庆日主题';
            }
        } else {
            // 根据日出日落切换
            const now = new Date();
            if (now >= this.sunTimes.sunrise && now < this.sunTimes.sunset) {
                newTheme = 'light';
                themeReason = '日出日落自动切换（白天）';
            } else {
                newTheme = 'dark';
                themeReason = '日出日落自动切换（夜晚）';
            }
        }
        
        if (newTheme !== this.currentTheme) {
            this.setTheme(newTheme, themeReason);
        }
    }
    
    setTheme(theme, reason) {
        const oldTheme = this.currentTheme;
        this.currentTheme = theme;
        
        // 移除所有主题类
        document.body.classList.remove('light-theme', 'dark-theme', 'memorial-theme', 'celebration-theme');
        
        // 添加新主题类
        document.body.classList.add(`${theme}-theme`);
        
        // 保存到localStorage
        localStorage.setItem('auto-theme', theme);
        localStorage.setItem('theme-reason', reason);
        localStorage.setItem('theme-change-time', new Date().toISOString());
        
        // 记录日志
        this.logManager.info('AutoThemeManager', `主题切换: ${oldTheme} -> ${theme}, 原因: ${reason}`);
        
        // 触发更新机制
        this.updateManager.notifyThemeChange(theme, reason);
        
        // 触发自定义事件
        window.dispatchEvent(new CustomEvent('themeChanged', {
            detail: { theme, reason, oldTheme, timestamp: new Date() }
        }));
    }
    
    startPeriodicCheck() {
        // 每分钟检查一次
        this.checkInterval = setInterval(() => {
            this.checkAndApplyTheme();
        }, 60000);
        
        this.logManager.info('AutoThemeManager', '启动定时主题检查（每分钟）');
    }
    
    checkAndApplyTheme() {
        // 重新计算日出日落时间（考虑日期变化）
        this.calculateSunTimes().then(() => {
            // 重新检查特殊日子
            this.checkSpecialDay();
            // 应用主题
            this.applyAutoTheme();
        });
    }
    
    stopPeriodicCheck() {
        if (this.checkInterval) {
            clearInterval(this.checkInterval);
            this.checkInterval = null;
            this.logManager.info('AutoThemeManager', '停止定时主题检查');
        }
    }
    
    // 手动触发主题检查
    forceCheck() {
        this.checkAndApplyTheme();
    }
    
    // 获取当前主题信息
    getCurrentThemeInfo() {
        return {
            theme: this.currentTheme,
            isSpecialDay: this.isSpecialDay,
            specialDayType: this.specialDayType,
            sunTimes: this.sunTimes,
            reason: localStorage.getItem('theme-reason'),
            changeTime: localStorage.getItem('theme-change-time')
        };
    }
    
    // 销毁管理器
    destroy() {
        this.stopPeriodicCheck();
        this.logManager.info('AutoThemeManager', '自动主题管理器已销毁');
    }
}

// 日志管理器
class LogManager {
    constructor() {
        this.logs = [];
        this.maxLogs = 1000;
    }
    
    info(category, message) {
        this.addLog('INFO', category, message);
    }
    
    error(category, message) {
        this.addLog('ERROR', category, message);
    }
    
    warn(category, message) {
        this.addLog('WARN', category, message);
    }
    
    addLog(level, category, message) {
        const log = {
            timestamp: new Date().toISOString(),
            level,
            category,
            message
        };
        
        this.logs.push(log);
        
        // 限制日志数量
        if (this.logs.length > this.maxLogs) {
            this.logs.shift();
        }
        
        // 输出到控制台
        console.log(`[${level}] ${category}: ${message}`);
        
        // 触发日志事件
        window.dispatchEvent(new CustomEvent('logAdded', { detail: log }));
    }
    
    getLogs(category = null, level = null) {
        let filteredLogs = this.logs;
        
        if (category) {
            filteredLogs = filteredLogs.filter(log => log.category === category);
        }
        
        if (level) {
            filteredLogs = filteredLogs.filter(log => log.level === level);
        }
        
        return filteredLogs;
    }
    
    clearLogs() {
        this.logs = [];
    }
}

// 更新管理器
class UpdateManager {
    constructor() {
        this.listeners = [];
    }
    
    notifyThemeChange(theme, reason) {
        const update = {
            type: 'theme-change',
            theme,
            reason,
            timestamp: new Date().toISOString()
        };
        
        // 通知所有监听器
        this.listeners.forEach(listener => {
            try {
                listener(update);
            } catch (error) {
                console.error('更新监听器错误:', error);
            }
        });
        
        // 触发更新事件
        window.dispatchEvent(new CustomEvent('systemUpdate', { detail: update }));
    }
    
    addListener(listener) {
        this.listeners.push(listener);
    }
    
    removeListener(listener) {
        const index = this.listeners.indexOf(listener);
        if (index > -1) {
            this.listeners.splice(index, 1);
        }
    }
}

// 全局初始化
window.autoThemeManager = null;
window.logManager = null;
window.updateManager = null;

// 页面加载完成后自动初始化
document.addEventListener('DOMContentLoaded', () => {
    // 初始化管理器
    window.logManager = new LogManager();
    window.updateManager = new UpdateManager();
    window.autoThemeManager = new AutoThemeManager();
});

// 页面卸载时清理
window.addEventListener('beforeunload', () => {
    if (window.autoThemeManager) {
        window.autoThemeManager.destroy();
    }
});