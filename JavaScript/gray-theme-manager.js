/**
 * 灰色主题机制和更新机制
 * 检测特殊日期并自动应用灰色主题，提供动态更新机制
 */

class GrayThemeManager {
    constructor(databaseManager) {
        this.dbManager = databaseManager;
        this.grayModeActive = false;
        this.grayDates = new Map(); // 灰色日期配置
        this.updateInterval = null;
        this.lastUpdateTime = null;
        this.observers = []; // 观察者模式监听器
        this.currentTheme = 'normal';
        
        this.initializeGrayDates();
        this.startUpdateMechanism();
        this.loadGrayModeSettings();
    }

    /**
     * 初始化灰色日期配置
     */
    async initializeGrayDates() {
        // 默认灰色日期配置
        const defaultGrayDates = [
            // 国家公祭日
            { date: '09-18', name: '九一八事变纪念日', type: 'national', duration: 1, priority: 'high' },
            { date: '07-07', name: '七七事变纪念日', type: 'national', duration: 1, priority: 'high' },
            { date: '12-13', name: '南京大屠杀死难者国家公祭日', type: 'national', duration: 1, priority: 'high' },
            { date: '04-04', name: '清明节', type: 'traditional', duration: 1, priority: 'medium' },
            
            // 其他重要纪念日
            { date: '05-12', name: '汶川地震纪念日', type: 'disaster', duration: 1, priority: 'medium' },
            { date: '08-15', name: '日本投降纪念日', type: 'historical', duration: 1, priority: 'medium' },
            { date: '09-09', name: '毛泽东逝世纪念日', type: 'historical', duration: 1, priority: 'medium' },
            
            // 国际纪念日
            { date: '01-27', name: '国际大屠杀纪念日', type: 'international', duration: 1, priority: 'low' },
            { date: '04-07', name: '卢旺达大屠杀纪念日', type: 'international', duration: 1, priority: 'low' }
        ];

        // 加载自定义灰色日期
        try {
            const customGrayDates = await this.dbManager.getSystemFactor('CustomGrayDates');
            if (customGrayDates) {
                const customDates = JSON.parse(customGrayDates);
                customDates.forEach(date => {
                    this.grayDates.set(date.date, date);
                });
            }
        } catch (error) {
            console.warn('⚠️ 加载自定义灰色日期失败:', error.message);
        }

        // 添加默认日期
        defaultGrayDates.forEach(date => {
            if (!this.grayDates.has(date.date)) {
                this.grayDates.set(date.date, date);
            }
        });

        console.log(`🕯️ 已加载 ${this.grayDates.size} 个灰色日期配置`);
    }

    /**
     * 加载灰色模式设置
     */
    async loadGrayModeSettings() {
        try {
            const settings = await this.dbManager.getSystemFactor('GrayModeSettings');
            if (settings) {
                const parsedSettings = JSON.parse(settings);
                this.applySettings(parsedSettings);
            }
        } catch (error) {
            console.warn('⚠️ 加载灰色模式设置失败:', error.message);
        }
    }

    /**
     * 启动更新机制
     */
    startUpdateMechanism() {
        // 立即检查一次
        this.checkAndUpdateGrayMode();
        
        // 每5分钟检查一次
        this.updateInterval = setInterval(() => {
            this.checkAndUpdateGrayMode();
        }, 300000);
        
        console.log('🔄 灰色主题更新机制已启动');
    }

    /**
     * 检查并更新灰色模式
     */
    async checkAndUpdateGrayMode() {
        try {
            const now = new Date();
            const shouldActivate = this.shouldActivateGrayMode(now);
            
            if (shouldActivate && !this.grayModeActive) {
                await this.activateGrayMode(now);
            } else if (!shouldActivate && this.grayModeActive) {
                await this.deactivateGrayMode();
            }
            
            this.lastUpdateTime = now;
            
            // 记录检查结果
            await this.logGrayModeCheck(now, shouldActivate);
            
        } catch (error) {
            console.error('❌ 灰色模式检查失败:', error);
            await this.dbManager.logSystemEvent('error', '灰色模式检查失败', 'GrayThemeManager', null, {
                error: error.message
            });
        }
    }

    /**
     * 判断是否应该激活灰色模式
     */
    shouldActivateGrayMode(currentDate) {
        const today = this.formatDate(currentDate);
        
        // 检查精确匹配
        if (this.grayDates.has(today)) {
            const grayDate = this.grayDates.get(today);
            return this.isDateWithinDuration(currentDate, grayDate);
        }
        
        // 检查动态日期（如清明节等农历节日）
        const dynamicGrayDates = this.getDynamicGrayDates(currentDate.getFullYear());
        for (const dynamicDate of dynamicGrayDates) {
            if (this.formatDate(dynamicDate.date) === today) {
                return this.isDateWithinDuration(currentDate, dynamicDate);
            }
        }
        
        // 检查临时灰色模式设置
        const tempGrayMode = this.getTemporaryGrayMode();
        if (tempGrayMode && this.isDateWithinDuration(currentDate, tempGrayMode)) {
            return true;
        }
        
        return false;
    }

    /**
     * 激活灰色模式
     */
    async activateGrayMode(currentDate) {
        console.log('🕯️ 激活灰色模式');
        
        this.grayModeActive = true;
        this.currentTheme = 'gray';
        
        // 应用灰色主题
        this.applyGrayTheme();
        
        // 更新系统因子
        await this.dbManager.updateSystemFactor('GrayModeActive', 'true');
        await this.dbManager.updateSystemFactor('GrayModeActivatedAt', currentDate.toISOString());
        
        // 获取当前灰色日期信息
        const grayDateInfo = this.getCurrentGrayDateInfo(currentDate);
        if (grayDateInfo) {
            await this.dbManager.updateSystemFactor('CurrentGrayDate', JSON.stringify(grayDateInfo));
        }
        
        // 通知观察者
        this.notifyObservers('grayModeActivated', {
            date: currentDate,
            reason: grayDateInfo ? grayDateInfo.name : '临时灰色模式'
        });
        
        // 记录事件
        await this.dbManager.logSystemEvent('info', '灰色模式已激活', 'GrayThemeManager', null, {
            date: currentDate.toISOString(),
            reason: grayDateInfo ? grayDateInfo.name : '临时灰色模式'
        });
    }

    /**
     * 停用灰色模式
     */
    async deactivateGrayMode() {
        console.log('🌈 停用灰色模式');
        
        this.grayModeActive = false;
        this.currentTheme = 'normal';
        
        // 移除灰色主题
        this.removeGrayTheme();
        
        // 更新系统因子
        await this.dbManager.updateSystemFactor('GrayModeActive', 'false');
        await this.dbManager.updateSystemFactor('GrayModeDeactivatedAt', new Date().toISOString());
        
        // 通知观察者
        this.notifyObservers('grayModeDeactivated', {
            date: new Date()
        });
        
        // 记录事件
        await this.dbManager.logSystemEvent('info', '灰色模式已停用', 'GrayThemeManager');
    }

    /**
     * 应用灰色主题
     */
    applyGrayTheme() {
        // 移除现有的灰色样式（如果有）
        this.removeGrayTheme();
        
        // 创建灰色主题样式
        const grayStyle = document.createElement('style');
        grayStyle.id = 'gray-theme-style';
        grayStyle.textContent = `
            /* 灰色主题样式 */
            html {
                filter: grayscale(100%) !important;
                -webkit-filter: grayscale(100%) !important;
                -moz-filter: grayscale(100%) !important;
                -ms-filter: grayscale(100%) !important;
                -o-filter: grayscale(100%) !important;
                filter: url("data:image/svg+xml;utf8,<svg xmlns='http://www.w3.org/2000/svg'><filter id='grayscale'><feColorMatrix type='matrix' values='0.3333 0.3333 0.3333 0 0 0.3333 0.3333 0.3333 0 0 0.3333 0.3333 0.3333 0 0 0 0 0 1 0'/></filter></svg>#grayscale") !important;
            }
            
            /* 确保所有元素都应用灰色滤镜 */
            body, div, span, p, a, img, video, canvas, svg {
                filter: inherit !important;
            }
            
            /* 特殊元素的灰色处理 */
            .colorful-element, .bright-element, .vibrant-element {
                filter: grayscale(100%) !important;
                opacity: 0.8 !important;
            }
            
            /* 背景图片的灰色处理 */
            body {
                background-blend-mode: luminosity !important;
            }
            
            /* 动画效果的调整 */
            @keyframes fadeInGray {
                from { opacity: 0.3; filter: grayscale(0%); }
                to { opacity: 1; filter: grayscale(100%); }
            }
            
            .gray-mode-transition {
                animation: fadeInGray 1s ease-in-out;
            }
            
            /* 灰色模式指示器 */
            .gray-mode-indicator {
                position: fixed !important;
                top: 10px !important;
                right: 10px !important;
                background: rgba(0, 0, 0, 0.8) !important;
                color: white !important;
                padding: 8px 16px !important;
                border-radius: 4px !important;
                font-size: 12px !important;
                z-index: 10000 !important;
                font-family: Arial, sans-serif !important;
                pointer-events: none !important;
            }
        `;
        
        document.head.appendChild(grayStyle);
        
        // 添加灰色模式指示器
        this.addGrayModeIndicator();
        
        // 添加过渡效果
        document.body.classList.add('gray-mode-transition');
        
        // 移除过渡效果
        setTimeout(() => {
            document.body.classList.remove('gray-mode-transition');
        }, 1000);
    }

    /**
     * 移除灰色主题
     */
    removeGrayTheme() {
        // 移除灰色样式
        const grayStyle = document.getElementById('gray-theme-style');
        if (grayStyle) {
            grayStyle.remove();
        }
        
        // 移除灰色模式指示器
        const indicator = document.getElementById('gray-mode-indicator');
        if (indicator) {
            indicator.remove();
        }
        
        // 移除过渡效果
        document.body.classList.remove('gray-mode-transition');
    }

    /**
     * 添加灰色模式指示器
     */
    addGrayModeIndicator() {
        const indicator = document.createElement('div');
        indicator.id = 'gray-mode-indicator';
        indicator.className = 'gray-mode-indicator';
        indicator.textContent = '🕯️ 灰色模式';
        document.body.appendChild(indicator);
        
        // 5秒后自动隐藏指示器
        setTimeout(() => {
            if (indicator.parentNode) {
                indicator.style.opacity = '0';
                indicator.style.transition = 'opacity 1s';
                setTimeout(() => {
                    if (indicator.parentNode) {
                        indicator.remove();
                    }
                }, 1000);
            }
        }, 5000);
    }

    /**
     * 获取动态灰色日期（如农历节日）
     */
    getDynamicGrayDates(year) {
        const dynamicDates = [];
        
        // 这里可以添加农历节日计算逻辑
        // 例如：清明节、端午节、中秋节等
        
        // 示例：计算清明节（通常在4月4日或5日）
        const qingmingDate = this.calculateQingmingDate(year);
        if (qingmingDate) {
            dynamicDates.push({
                date: qingmingDate,
                name: '清明节',
                type: 'traditional',
                duration: 1,
                priority: 'medium'
            });
        }
        
        return dynamicDates;
    }

    /**
     * 计算清明节日期
     */
    calculateQingmingDate(year) {
        // 简化的清明节计算（实际需要更精确的天文计算）
        // 这里使用4月4日或5日的简化逻辑
        const baseDate = new Date(year, 3, 4); // 4月4日
        const dayOfWeek = baseDate.getDay();
        
        // 如果4月4日是周日，则清明节在4月4日
        // 否则在4月4日或5日（这里简化为4月4日）
        return baseDate;
    }

    /**
     * 判断日期是否在持续时间内
     */
    isDateWithinDuration(currentDate, grayDate) {
        if (!grayDate.duration || grayDate.duration <= 1) {
            return this.formatDate(currentDate) === grayDate.date;
        }
        
        const startDate = new Date(currentDate.getFullYear() + '-' + grayDate.date);
        const endDate = new Date(startDate);
        endDate.setDate(startDate.getDate() + grayDate.duration - 1);
        
        return currentDate >= startDate && currentDate <= endDate;
    }

    /**
     * 获取当前灰色日期信息
     */
    getCurrentGrayDateInfo(currentDate) {
        const today = this.formatDate(currentDate);
        
        // 检查精确匹配
        if (this.grayDates.has(today)) {
            return this.grayDates.get(today);
        }
        
        // 检查动态日期
        const dynamicGrayDates = this.getDynamicGrayDates(currentDate.getFullYear());
        for (const dynamicDate of dynamicGrayDates) {
            if (this.formatDate(dynamicDate.date) === today) {
                return dynamicDate;
            }
        }
        
        // 检查临时灰色模式
        const tempGrayMode = this.getTemporaryGrayMode();
        if (tempGrayMode && this.isDateWithinDuration(currentDate, tempGrayMode)) {
            return tempGrayMode;
        }
        
        return null;
    }

    /**
     * 获取临时灰色模式设置
     */
    getTemporaryGrayMode() {
        // 这里可以从数据库或配置中获取临时灰色模式设置
        // 示例实现
        return null;
    }

    /**
     * 添加自定义灰色日期
     */
    async addCustomGrayDate(dateInfo) {
        const grayDate = {
            date: dateInfo.date,
            name: dateInfo.name,
            type: 'custom',
            duration: dateInfo.duration || 1,
            priority: dateInfo.priority || 'medium',
            createdBy: dateInfo.createdBy || 'system',
            createdAt: new Date().toISOString()
        };
        
        this.grayDates.set(grayDate.date, grayDate);
        
        // 保存到数据库
        const customDates = Array.from(this.grayDates.values()).filter(d => d.type === 'custom');
        await this.dbManager.updateSystemFactor('CustomGrayDates', JSON.stringify(customDates));
        
        // 立即检查是否需要激活灰色模式
        await this.checkAndUpdateGrayMode();
        
        console.log(`📅 已添加自定义灰色日期: ${grayDate.name} (${grayDate.date})`);
        
        return grayDate;
    }

    /**
     * 移除自定义灰色日期
     */
    async removeCustomGrayDate(date) {
        if (this.grayDates.has(date)) {
            const grayDate = this.grayDates.get(date);
            if (grayDate.type === 'custom') {
                this.grayDates.delete(date);
                
                // 更新数据库
                const customDates = Array.from(this.grayDates.values()).filter(d => d.type === 'custom');
                await this.dbManager.updateSystemFactor('CustomGrayDates', JSON.stringify(customDates));
                
                // 立即检查是否需要停用灰色模式
                await this.checkAndUpdateGrayMode();
                
                console.log(`🗑️ 已移除自定义灰色日期: ${grayDate.name} (${date})`);
                
                return true;
            }
        }
        
        return false;
    }

    /**
     * 手动激活灰色模式
     */
    async manualActivateGrayMode(reason, duration = 1) {
        const tempGrayMode = {
            date: this.formatDate(new Date()),
            name: reason || '手动激活',
            type: 'manual',
            duration: duration,
            priority: 'high'
        };
        
        // 保存临时灰色模式设置
        await this.dbManager.updateSystemFactor('TemporaryGrayMode', JSON.stringify(tempGrayMode));
        
        // 立即激活
        await this.checkAndUpdateGrayMode();
        
        console.log(`🖐️ 手动激活灰色模式: ${reason}`);
    }

    /**
     * 手动停用灰色模式
     */
    async manualDeactivateGrayMode() {
        // 移除临时灰色模式设置
        await this.dbManager.updateSystemFactor('TemporaryGrayMode', null);
        
        // 立即检查并更新
        await this.checkAndUpdateGrayMode();
        
        console.log('🖐️ 手动停用灰色模式');
    }

    /**
     * 添加观察者
     */
    addObserver(callback) {
        this.observers.push(callback);
    }

    /**
     * 移除观察者
     */
    removeObserver(callback) {
        const index = this.observers.indexOf(callback);
        if (index > -1) {
            this.observers.splice(index, 1);
        }
    }

    /**
     * 通知观察者
     */
    notifyObservers(event, data) {
        this.observers.forEach(callback => {
            try {
                callback(event, data);
            } catch (error) {
                console.error('❌ 观察者回调执行失败:', error);
            }
        });
    }

    /**
     * 应用设置
     */
    applySettings(settings) {
        if (settings.updateInterval) {
            // 重新设置更新间隔
            if (this.updateInterval) {
                clearInterval(this.updateInterval);
            }
            this.updateInterval = setInterval(() => {
                this.checkAndUpdateGrayMode();
            }, settings.updateInterval);
        }
    }

    /**
     * 记录灰色模式检查
     */
    async logGrayModeCheck(checkDate, shouldActivate) {
        await this.dbManager.logSystemEvent('debug', '灰色模式检查', 'GrayThemeManager', null, {
            checkDate: checkDate.toISOString(),
            shouldActivate: shouldActivate,
            currentStatus: this.grayModeActive,
            lastUpdateTime: this.lastUpdateTime ? this.lastUpdateTime.toISOString() : null
        });
    }

    /**
     * 格式化日期
     */
    formatDate(date) {
        const month = (date.getMonth() + 1).toString().padStart(2, '0');
        const day = date.getDate().toString().padStart(2, '0');
        return `${month}-${day}`;
    }

    /**
     * 获取灰色模式状态
     */
    getGrayModeStatus() {
        return {
            active: this.grayModeActive,
            currentTheme: this.currentTheme,
            lastUpdateTime: this.lastUpdateTime,
            grayDatesCount: this.grayDates.size,
            currentGrayDate: this.getCurrentGrayDateInfo(new Date()),
            nextGrayDate: this.getNextGrayDate()
        };
    }

    /**
     * 获取下一个灰色日期
     */
    getNextGrayDate() {
        const today = new Date();
        const currentYear = today.getFullYear();
        
        let nextDate = null;
        let minDaysDiff = Infinity;
        
        // 检查静态日期
        for (const [dateStr, grayDate] of this.grayDates) {
            const testDate = new Date(currentYear + '-' + dateStr);
            if (testDate > today) {
                const daysDiff = Math.ceil((testDate - today) / (1000 * 60 * 60 * 24));
                if (daysDiff < minDaysDiff) {
                    minDaysDiff = daysDiff;
                    nextDate = { ...grayDate, date: testDate };
                }
            }
        }
        
        // 检查动态日期
        const dynamicDates = this.getDynamicGrayDates(currentYear);
        for (const dynamicDate of dynamicDates) {
            if (dynamicDate.date > today) {
                const daysDiff = Math.ceil((dynamicDate.date - today) / (1000 * 60 * 60 * 24));
                if (daysDiff < minDaysDiff) {
                    minDaysDiff = daysDiff;
                    nextDate = dynamicDate;
                }
            }
        }
        
        return nextDate;
    }

    /**
     * 导出灰色模式配置
     */
    async exportGrayModeConfig() {
        const config = {
            timestamp: new Date().toISOString(),
            status: this.getGrayModeStatus(),
            grayDates: Array.from(this.grayDates.values()),
            settings: {
                updateInterval: 300000,
                autoActivate: true,
                showIndicator: true
            }
        };

        await this.dbManager.logSystemEvent('info', '导出灰色模式配置', 'GrayThemeManager', null, {
            grayDatesCount: config.grayDates.length,
            activeStatus: config.status.active
        });

        return config;
    }

    /**
     * 停止更新机制
     */
    stopUpdateMechanism() {
        if (this.updateInterval) {
            clearInterval(this.updateInterval);
            this.updateInterval = null;
            console.log('🛑 灰色主题更新机制已停止');
        }
    }

    /**
     * 销毁管理器
     */
    destroy() {
        this.stopUpdateMechanism();
        this.removeGrayTheme();
        this.observers = [];
        console.log('🗑️ 灰色主题管理器已销毁');
    }
}

// 导出类
if (typeof window !== 'undefined') {
    window.GrayThemeManager = GrayThemeManager;
} else if (typeof module !== 'undefined' && module.exports) {
    module.exports = GrayThemeManager;
}