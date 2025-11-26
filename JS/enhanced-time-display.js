/**
 * 增强时间显示模块
 * 包含农历时间显示和事件显示
 */
class EnhancedTimeDisplay {
    constructor() {
        this.timeElement = null;
        this.lunarElement = null;
        this.eventElement = null;
        this.updateInterval = null;
        this.currentDate = new Date();
        
        // 农历数据（简化版本，实际应用中需要完整的农历算法）
        this.lunarInfo = [
            0x04bd8, 0x04ae0, 0x0a570, 0x054d5, 0x0d260, 0x0d950, 0x16554, 0x056a0, 0x09ad0, 0x055d2,
            0x04ae0, 0x0a5b6, 0x0a4d0, 0x0d250, 0x1d255, 0x0b540, 0x0d6a0, 0x0ada2, 0x095b0, 0x14977,
            0x04970, 0x0a4b0, 0x0b4b5, 0x06a50, 0x06d40, 0x1ab54, 0x02b60, 0x09570, 0x052f2, 0x04970,
            0x06566, 0x0d4a0, 0x0ea50, 0x06e95, 0x05ad0, 0x02b60, 0x186e3, 0x092e0, 0x1c8d7, 0x0c950,
            0x0d4a0, 0x1d8a6, 0x0b550, 0x056a0, 0x1a5b4, 0x025d0, 0x092d0, 0x0d2b2, 0x0a950, 0x0b557
        ];
        
        this.lunarMonths = ['正', '二', '三', '四', '五', '六', '七', '八', '九', '十', '冬', '腊'];
        this.lunarDays = ['初一', '初二', '初三', '初四', '初五', '初六', '初七', '初八', '初九', '初十',
                          '十一', '十二', '十三', '十四', '十五', '十六', '十七', '十八', '十九', '二十',
                          '廿一', '廿二', '廿三', '廿四', '廿五', '廿六', '廿七', '廿八', '廿九', '三十'];
        
        this.tianGan = ['甲', '乙', '丙', '丁', '戊', '己', '庚', '辛', '壬', '癸'];
        this.diZhi = ['子', '丑', '寅', '卯', '辰', '巳', '午', '未', '申', '酉', '戌', '亥'];
        
        this.init();
    }
    
    init() {
        this.createElements();
        this.startUpdate();
        this.bindEvents();
    }
    
    createElements() {
        // 查找或创建时间显示容器
        this.timeElement = document.querySelector('.current-time') || document.querySelector('#current-time');
        
        if (this.timeElement) {
            // 在现有时间元素后添加农历和事件显示
            const container = this.timeElement.parentElement;
            
            // 创建农历时间显示元素
            this.lunarElement = document.createElement('div');
            this.lunarElement.className = 'lunar-time';
            this.lunarElement.style.cssText = `
                font-size: 12px;
                color: var(--text-secondary);
                margin-top: 4px;
                font-weight: normal;
            `;
            
            // 创建事件显示元素
            this.eventElement = document.createElement('div');
            this.eventElement.className = 'time-events';
            this.eventElement.style.cssText = `
                font-size: 11px;
                color: var(--accent-color);
                margin-top: 2px;
                font-weight: normal;
                max-height: 40px;
                overflow: hidden;
            `;
            
            container.appendChild(this.lunarElement);
            container.appendChild(this.eventElement);
        }
    }
    
    startUpdate() {
        this.updateTime();
        this.updateInterval = setInterval(() => {
            this.updateTime();
        }, 1000);
    }
    
    updateTime() {
        this.currentDate = new Date();
        
        // 更新标准时间
        if (this.timeElement) {
            const timeString = this.formatDateTime(this.currentDate);
            this.timeElement.textContent = timeString;
        }
        
        // 更新农历时间
        if (this.lunarElement) {
            const lunarString = this.getLunarDateString(this.currentDate);
            this.lunarElement.textContent = lunarString;
        }
        
        // 更新事件显示
        if (this.eventElement) {
            const eventString = this.getEventString(this.currentDate);
            this.eventElement.textContent = eventString;
        }
    }
    
    formatDateTime(date) {
        const year = date.getFullYear();
        const month = String(date.getMonth() + 1).padStart(2, '0');
        const day = String(date.getDate()).padStart(2, '0');
        const hours = String(date.getHours()).padStart(2, '0');
        const minutes = String(date.getMinutes()).padStart(2, '0');
        const seconds = String(date.getSeconds()).padStart(2, '0');
        
        const weekdays = ['星期日', '星期一', '星期二', '星期三', '星期四', '星期五', '星期六'];
        const weekday = weekdays[date.getDay()];
        
        return `${year}-${month}-${day} ${hours}:${minutes}:${seconds} ${weekday}`;
    }
    
    getLunarDateString(date) {
        const lunar = this.getLunarDate(date);
        const lunarMonth = this.lunarMonths[lunar.month - 1];
        const lunarDay = this.lunarDays[lunar.day - 1];
        const yearGanZhi = this.getYearGanZhi(lunar.year);
        
        return `农历${yearGanZhi}年${lunarMonth}月${lunarDay}`;
    }
    
    getLunarDate(date) {
        // 简化的农历计算（实际应用中需要完整的农历算法）
        const year = date.getFullYear();
        const month = date.getMonth() + 1;
        const day = date.getDate();
        
        // 这里使用简化的映射，实际需要复杂的农历计算
        const baseDate = new Date(2024, 0, 1); // 2024年春节作为基准
        const diffDays = Math.floor((date - baseDate) / (1000 * 60 * 60 * 24));
        
        let lunarYear = year;
        let lunarMonth = 1;
        let lunarDay = 1;
        
        // 简化计算（仅作示例）
        if (diffDays >= 0) {
            lunarDay = Math.floor(diffDays % 30) + 1;
            lunarMonth = Math.floor(diffDays / 30) % 12 + 1;
            if (diffDays > 365) {
                lunarYear++;
            }
        }
        
        return {
            year: lunarYear,
            month: lunarMonth,
            day: lunarDay
        };
    }
    
    getYearGanZhi(year) {
        const ganIndex = (year - 4) % 10;
        const zhiIndex = (year - 4) % 12;
        return this.tianGan[ganIndex] + this.diZhi[zhiIndex];
    }
    
    getEventString(date) {
        const events = [];
        
        // 检查节气
        const solarTerm = this.getSolarTerm(date);
        if (solarTerm) {
            events.push(`今日${solarTerm}`);
        }
        
        // 检查节日
        const festival = this.getFestival(date);
        if (festival) {
            events.push(festival);
        }
        
        // 检查主题状态
        if (window.autoThemeManager) {
            const themeInfo = window.autoThemeManager.getCurrentThemeInfo();
            if (themeInfo.isSpecialDay) {
                if (themeInfo.specialDayType === 'memorial') {
                    events.push('公祭日');
                } else if (themeInfo.specialDayType === 'celebration') {
                    events.push('喜庆日');
                }
            } else {
                // 显示日出日落状态
                const now = date;
                if (themeInfo.sunTimes) {
                    if (now >= themeInfo.sunTimes.sunrise && now < themeInfo.sunTimes.sunset) {
                        events.push('☀️ 白天');
                    } else {
                        events.push('🌙 夜晚');
                    }
                }
            }
        }
        
        return events.join(' | ') || '平常日';
    }
    
    getSolarTerm(date) {
        // 简化的节气计算（实际应用中需要精确计算）
        const solarTerms = [
            { name: '立春', month: 2, day: 4 },
            { name: '雨水', month: 2, day: 19 },
            { name: '惊蛰', month: 3, day: 6 },
            { name: '春分', month: 3, day: 21 },
            { name: '清明', month: 4, day: 5 },
            { name: '谷雨', month: 4, day: 20 },
            { name: '立夏', month: 5, day: 6 },
            { name: '小满', month: 5, day: 21 },
            { name: '芒种', month: 6, day: 6 },
            { name: '夏至', month: 6, day: 21 },
            { name: '小暑', month: 7, day: 7 },
            { name: '大暑', month: 7, day: 23 },
            { name: '立秋', month: 8, day: 8 },
            { name: '处暑', month: 8, day: 23 },
            { name: '白露', month: 9, day: 8 },
            { name: '秋分', month: 9, day: 23 },
            { name: '寒露', month: 10, day: 8 },
            { name: '霜降', month: 10, day: 23 },
            { name: '立冬', month: 11, day: 8 },
            { name: '小雪', month: 11, day: 22 },
            { name: '大雪', month: 12, day: 7 },
            { name: '冬至', month: 12, day: 22 },
            { name: '小寒', month: 1, day: 6 },
            { name: '大寒', month: 1, day: 20 }
        ];
        
        const month = date.getMonth() + 1;
        const day = date.getDate();
        
        const term = solarTerms.find(t => t.month === month && Math.abs(t.day - day) <= 1);
        return term ? term.name : null;
    }
    
    getFestival(date) {
        const month = date.getMonth() + 1;
        const day = date.getDate();
        const monthDay = `${String(month).padStart(2, '0')}-${String(day).padStart(2, '0')}`;
        
        const festivals = {
            '01-01': '元旦',
            '02-14': '情人节',
            '03-08': '妇女节',
            '04-01': '愚人节',
            '05-01': '劳动节',
            '06-01': '儿童节',
            '07-01': '建党节',
            '08-01': '建军节',
            '09-10': '教师节',
            '10-01': '国庆节',
            '12-25': '圣诞节'
        };
        
        return festivals[monthDay] || null;
    }
    
    bindEvents() {
        // 监听主题变化事件
        window.addEventListener('themeChanged', (event) => {
            this.updateTime();
        });
        
        // 监听系统更新事件
        window.addEventListener('systemUpdate', (event) => {
            if (event.detail.type === 'theme-change') {
                this.updateTime();
            }
        });
    }
    
    // 手动更新时间
    forceUpdate() {
        this.updateTime();
    }
    
    // 销毁时间显示
    destroy() {
        if (this.updateInterval) {
            clearInterval(this.updateInterval);
            this.updateInterval = null;
        }
        
        // 移除创建的元素
        if (this.lunarElement && this.lunarElement.parentNode) {
            this.lunarElement.parentNode.removeChild(this.lunarElement);
        }
        
        if (this.eventElement && this.eventElement.parentNode) {
            this.eventElement.parentNode.removeChild(this.eventElement);
        }
    }
}

// 全局初始化
window.enhancedTimeDisplay = null;

// 页面加载完成后自动初始化
document.addEventListener('DOMContentLoaded', () => {
    // 等待DOM完全加载后初始化
    setTimeout(() => {
        window.enhancedTimeDisplay = new EnhancedTimeDisplay();
    }, 100);
});

// 页面卸载时清理
window.addEventListener('beforeunload', () => {
    if (window.enhancedTimeDisplay) {
        window.enhancedTimeDisplay.destroy();
    }
});