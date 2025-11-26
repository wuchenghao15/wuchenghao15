/**
 * 登录页面JavaScript
 * 实现表单验证、密码显示切换、登录功能以及佛教时间显示
 */

// 立即检查document和querySelector状态
(function() {
    console.log('[IMMEDIATE CHECK] Document exists:', !!document);
    console.log('[IMMEDIATE CHECK] Document readyState:', document.readyState);
    console.log('[IMMEDIATE CHECK] QuerySelector available:', typeof document.querySelector);
    
    if (document && typeof document.querySelector === 'function') {
        try {
            const testElement = document.querySelector('body');
            console.log('[IMMEDIATE CHECK] Test querySelector result:', !!testElement);
        } catch (e) {
            console.error('[IMMEDIATE CHECK] QuerySelector test failed:', e);
        }
    }
})();

// 添加全局错误处理器来捕获真正的错误
window.addEventListener('error', function(e) {
    console.error('[GLOBAL ERROR]', {
        message: e.message,
        filename: e.filename,
        lineno: e.lineno,
        colno: e.colno,
        stack: e.error?.stack
    });
});

// 调试：检查document和querySelector是否可用
console.log('[DEBUG] Document ready:', !!document);
console.log('[DEBUG] QuerySelector available:', typeof document.querySelector);

// DOM元素缓存 - 将在init函数中初始化
let loginForm, usernameInput, passwordInput, rememberCheckbox, loginButton, versionElement, usernameHelp, passwordHelp, btnText, btnLoading, passwordToggleBtn, errorMessage, errorText, loginContainer, currentTimeElement, lunarDateElement, buddhistYearElement, eventsList, toggleEventsBtn;

/**
 * 佛教时间工具函数
 */
class BuddhistDateUtils {
    /**
     * 格式化当前时间
     * @returns {string} 格式化的时间字符串
     */
    static formatCurrentTime() {
        const now = new Date();
        const year = now.getFullYear();
        const month = String(now.getMonth() + 1).padStart(2, '0');
        const day = String(now.getDate()).padStart(2, '0');
        const hours = String(now.getHours()).padStart(2, '0');
        const minutes = String(now.getMinutes()).padStart(2, '0');
        const seconds = String(now.getSeconds()).padStart(2, '0');
        
        return `${year}-${month}-${day} ${hours}:${minutes}:${seconds}`;
    }
    
    /**
     * 计算农历日期（简化版算法）
     * @param {Date} date - 公历日期
     * @returns {string} 农历日期
     */
    static getLunarDate(date) {
        // 农历月份名称
        const lunarMonths = ['', '正月', '二月', '三月', '四月', '五月', '六月', '七月', '八月', '九月', '十月', '冬月', '腊月'];
        // 农历日期名称
        const lunarDays = ['', '初一', '初二', '初三', '初四', '初五', '初六', '初七', '初八', '初九', '初十',
                          '十一', '十二', '十三', '十四', '十五', '十六', '十七', '十八', '十九', '二十',
                          '廿一', '廿二', '廿三', '廿四', '廿五', '廿六', '廿七', '廿八', '廿九', '三十'];
        
        // 这里使用简化的农历计算，实际项目中应使用更精确的农历算法
        // 此方法使用1900-2100年的农历数据表（简化版）
        const year = date.getFullYear();
        const month = date.getMonth() + 1;
        const day = date.getDate();
        
        // 简化的农历计算逻辑
        const lunarData = this.lunarCalendarData(year);
        const lunarMonth = lunarData[month] || month;
        const lunarDay = lunarData[day] || day;
        
        return `${year}年${lunarMonths[lunarMonth]}${lunarDays[lunarDay]}`;
    }
    
    /**
     * 获取佛历年份
     * 佛历 = 公历 + 543（佛陀涅槃年份）
     * @returns {string} 佛历年份
     */
    static getBuddhistYear() {
        const currentYear = new Date().getFullYear();
        const buddhistYear = currentYear + 543;
        return `${buddhistYear}年`;
    }
    
    /**
     * 简化的农历数据（仅作示例）
     * 在实际应用中应使用完整的农历数据表
     */
    static lunarCalendarData(year) {
        // 这里只是简化示例，实际应用中应使用完整的农历计算库
        // 返回一个对象，包含月份和日期的映射
        return {
            // 月份映射
            1: 1, 2: 2, 3: 3, 4: 4, 5: 5, 6: 6,
            7: 7, 8: 8, 9: 9, 10: 10, 11: 11, 12: 12,
            // 日期映射（简化）
            1: 1, 2: 2, 3: 3, 4: 4, 5: 5, 6: 6, 7: 7, 8: 8, 9: 9, 10: 10,
            11: 11, 12: 12, 13: 13, 14: 14, 15: 15, 16: 16, 17: 17, 18: 18, 19: 19, 20: 20,
            21: 21, 22: 22, 23: 23, 24: 24, 25: 25, 26: 26, 27: 27, 28: 28, 29: 29, 30: 30, 31: 1
        };
    }
}

// 佛教事件数据 - 汉传、藏传、东传佛教重要日期
const buddhistEvents = {
    // 汉传佛教重要事件
    han: [
        // 1月
        { month: 1, day: 1, name: '弥勒佛诞辰', type: '诞辰' },
        // 2月
        { month: 2, day: 8, name: '释迦牟尼佛出家日', type: '出家' },
        { month: 2, day: 15, name: '释迦牟尼佛涅槃日', type: '涅槃' },
        // 3月
        { month: 3, day: 16, name: '准提菩萨诞辰', type: '诞辰' },
        // 4月
        { month: 4, day: 1, name: '文殊菩萨诞辰', type: '诞辰' },
        { month: 4, day: 8, name: '释迦牟尼佛诞辰', type: '诞辰' },
        // 5月
        { month: 5, day: 13, name: '伽蓝菩萨诞辰', type: '诞辰' },
        { month: 5, day: 19, name: '观世音菩萨成道日', type: '成道' },
        // 6月
        { month: 6, day: 3, name: '韦陀菩萨诞辰', type: '诞辰' },
        { month: 6, day: 19, name: '观世音菩萨诞辰', type: '诞辰' },
        { month: 6, day: 24, name: '关圣帝君诞辰', type: '诞辰' },
        // 7月
        { month: 7, day: 13, name: '大势至菩萨诞辰', type: '诞辰' },
        { month: 7, day: 15, name: '佛欢喜日/盂兰盆节', type: '节日' },
        { month: 7, day: 24, name: '龙树菩萨诞辰', type: '诞辰' },
        // 8月
        { month: 8, day: 22, name: '燃灯佛诞辰', type: '诞辰' },
        { month: 8, day: 24, name: '大势至菩萨成道日', type: '成道' },
        // 9月
        { month: 9, day: 19, name: '观世音菩萨出家日', type: '出家' },
        { month: 9, day: 30, name: '药师佛诞辰', type: '诞辰' },
        // 10月
        { month: 10, day: 5, name: '达摩祖师诞辰', type: '诞辰' },
        // 11月
        { month: 11, day: 17, name: '阿弥陀佛诞辰', type: '诞辰' },
        // 12月
        { month: 12, day: 8, name: '释迦牟尼佛成道日', type: '成道' }
    ],
    
    // 藏传佛教重要事件
    tibetan: [
        { month: 1, day: 1, name: '藏历新年', type: '节日' },
        { month: 1, day: 15, name: '酥油灯节', type: '节日' },
        { month: 3, day: 15, name: '大昭寺展佛节', type: '节日' },
        { month: 4, day: 15, name: '萨噶达瓦节（佛陀诞辰、成道、涅槃）', type: '节日' },
        { month: 6, day: 4, name: '转山节', type: '节日' },
        { month: 6, day: 30, name: '雪顿节', type: '节日' },
        { month: 9, day: 22, name: '燃灯节', type: '节日' },
        { month: 12, day: 29, name: '驱鬼节', type: '节日' }
    ],
    
    // 东传佛教重要事件
    east: [
        { month: 1, day: 24, name: '天照大神祭', type: '节日' },
        { month: 2, day: 11, name: '弥勒菩萨圣诞', type: '诞辰' },
        { month: 3, day: 18, name: '普贤菩萨圣诞', type: '诞辰' },
        { month: 4, day: 8, name: '佛诞日/浴佛节', type: '节日' },
        { month: 5, day: 5, name: '端午节法会', type: '法会' },
        { month: 7, day: 15, name: '盂兰盆节', type: '节日' },
        { month: 9, day: 9, name: '重阳节法会', type: '法会' },
        { month: 12, day: 8, name: '腊八节/成道会', type: '节日' }
    ]
};

/**
 * 更新佛教时间显示
 */
function updateBuddhistTime() {
    try {
        // 确保DOM元素已初始化
        if (!currentTimeElement || !lunarDateElement || !buddhistYearElement) {
            console.warn('时间显示元素未初始化');
            return;
        }
        
        const now = new Date();
        
        // 更新当前时间
        currentTimeElement.textContent = BuddhistDateUtils.formatCurrentTime();
        
        // 每分钟更新一次农历和佛历（不需要每秒更新）
        const minutes = now.getMinutes();
        if (typeof updateBuddhistTime.lastMinute === 'undefined' || updateBuddhistTime.lastMinute !== minutes) {
            updateBuddhistTime.lastMinute = minutes;
            
            // 更新农历日期
            lunarDateElement.textContent = BuddhistDateUtils.getLunarDate(new Date());
            
            // 更新佛历年份
            buddhistYearElement.textContent = BuddhistDateUtils.getBuddhistYear();
            
            // 每天更新一次佛教事件
            const dateKey = `${now.getMonth() + 1}-${now.getDate()}`;
            if (typeof updateBuddhistTime.lastDate === 'undefined' || updateBuddhistTime.lastDate !== dateKey) {
                updateBuddhistTime.lastDate = dateKey;
                updateBuddhistEvents();
            }
        }
    } catch (error) {
        console.error('更新佛教时间失败:', error);
    }
}

/**
 * 初始化佛教时间显示
 */
function initBuddhistTime() {
    // 立即更新一次
    updateBuddhistTime();
    
    // 设置每秒更新当前时间
    setInterval(() => {
        try {
            updateBuddhistTime();
        } catch (error) {
            console.error('更新佛教时间失败:', error);
        }
    }, 1000);
}

// 更新佛教事件显示
function updateBuddhistEvents() {
    try {
        // 确保DOM元素已初始化
        if (!eventsList) {
            console.warn('事件列表元素未初始化');
            return;
        }
        
        const now = new Date();
        const currentMonth = now.getMonth() + 1;
        const currentDay = now.getDate();
        
        // 获取今日事件
        const todayEvents = getTodayBuddhistEvents(currentMonth, currentDay);
        
        // 清空事件列表
        eventsList.innerHTML = '';
        
        if (todayEvents.length === 0) {
            // 如果今日没有事件，显示近期事件
            const upcomingEvents = getUpcomingBuddhistEvents(currentMonth, currentDay, 7);
            
            if (upcomingEvents.length === 0) {
                const noEventItem = document.createElement('div');
                noEventItem.className = 'event-item';
                noEventItem.innerHTML = '近期无重要佛教事件';
                eventsList.appendChild(noEventItem);
            } else {
                upcomingEvents.forEach(event => {
                    const eventItem = createEventElement(event, true);
                    eventsList.appendChild(eventItem);
                });
            }
        } else {
            // 显示今日事件
            todayEvents.forEach(event => {
                const eventItem = createEventElement(event, false);
                eventsList.appendChild(eventItem);
            });
            
            // 添加近期事件预览
            const upcomingEvents = getUpcomingBuddhistEvents(currentMonth, currentDay, 3);
            if (upcomingEvents.length > 0) {
                const separator = document.createElement('div');
                separator.className = 'event-item';
                separator.style.textAlign = 'center';
                separator.style.borderLeft = 'none';
                separator.style.fontStyle = 'italic';
                separator.style.padding = '4px';
                separator.textContent = '近期重要事件';
                eventsList.appendChild(separator);
                
                upcomingEvents.forEach(event => {
                    const eventItem = createEventElement(event, true);
                    eventsList.appendChild(eventItem);
                });
            }
        }
    } catch (error) {
        console.error('更新佛教事件失败:', error);
    }
}

// 获取今日佛教事件
function getTodayBuddhistEvents(month, day) {
    const events = [];
    
    // 检查所有佛教传统的今日事件
    Object.keys(buddhistEvents).forEach(tradition => {
        const traditionEvents = buddhistEvents[tradition];
        traditionEvents.forEach(event => {
            if (event.month === month && event.day === day) {
                events.push({
                    ...event,
                    tradition: getTraditionName(tradition)
                });
            }
        });
    });
    
    return events;
}

// 获取近期佛教事件
function getUpcomingBuddhistEvents(currentMonth, currentDay, daysToLookAhead) {
    const events = [];
    const today = new Date();
    
    // 检查未来几天的事件
    for (let i = 1; i <= daysToLookAhead; i++) {
        const futureDate = new Date(today);
        futureDate.setDate(today.getDate() + i);
        
        const month = futureDate.getMonth() + 1;
        const day = futureDate.getDate();
        const dayEvents = getTodayBuddhistEvents(month, day);
        
        if (dayEvents.length > 0) {
            dayEvents.forEach(event => {
                events.push({
                    ...event,
                    daysUntil: i
                });
            });
        }
    }
    
    // 限制返回事件数量
    return events.slice(0, 5);
}

// 创建事件元素
function createEventElement(event, isUpcoming) {
    const eventItem = document.createElement('div');
    eventItem.className = 'event-item';
    
    // 根据事件类型设置不同的左侧边框颜色
    let borderColor = 'var(--primary-color)'; // 默认朱红色
    if (event.type === '诞辰') {
        borderColor = 'var(--secondary-color)'; // 金黄色
    } else if (event.type === '涅槃') {
        borderColor = 'var(--accent-color)'; // 深绿色
    } else if (event.type === '成道') {
        borderColor = 'var(--text-color)'; // 深褐色
    }
    
    eventItem.style.borderLeftColor = borderColor;
    
    // 构建事件内容
    let eventText = `${event.name} (${event.type})`;
    if (event.tradition) {
        eventText += ` - ${event.tradition}`;
    }
    
    // 构建日期显示
    let dateText = `${event.month}月${event.day}日`;
    if (isUpcoming && event.daysUntil) {
        dateText += ` (${event.daysUntil}天后)`;
    }
    
    // 设置事件内容
    eventItem.innerHTML = `
        <span class="event-name">${eventText}</span>
        <span class="event-date">${dateText}</span>
    `;
    
    return eventItem;
}

// 获取佛教传统名称
function getTraditionName(traditionKey) {
    const traditionNames = {
        han: '汉传佛教',
        tibetan: '藏传佛教',
        east: '东传佛教'
    };
    
    return traditionNames[traditionKey] || traditionKey;
}

// 添加事件切换功能
function initEventsToggle() {
    // 确保DOM元素已初始化
    if (!toggleEventsBtn || !eventsList) {
        console.warn('事件切换元素未初始化');
        return;
    }
    
    toggleEventsBtn.addEventListener('click', () => {
        eventsList.classList.toggle('collapsed');
        toggleEventsBtn.classList.toggle('collapsed');
    });
}

/**
 * 切换密码可见性 - 增强版
 */
function togglePasswordVisibility() {
    // 确保DOM元素已初始化且是有效的DOM元素
    if (!passwordInput || !passwordToggleBtn || 
        typeof passwordToggleBtn.querySelector !== 'function') {
        console.warn('密码切换功能未初始化');
        return;
    }
    
    const type = passwordInput.getAttribute('type') === 'password' ? 'text' : 'password';
    passwordInput.setAttribute('type', type);
    
    // 更新图标和aria-label
    const icon = passwordToggleBtn.querySelector('i');
    if (icon && typeof icon.classList !== 'undefined') {
        if (type === 'text') {
            icon.classList.remove('fa-eye');
            icon.classList.add('fa-eye-slash');
            passwordToggleBtn.setAttribute('aria-label', '隐藏密码');
        } else {
            icon.classList.remove('fa-eye-slash');
            icon.classList.add('fa-eye');
            passwordToggleBtn.setAttribute('aria-label', '显示密码');
        }
    }
    
    // 添加微小的动画效果
    passwordToggleBtn.style.transform = 'scale(1.1)';
    setTimeout(() => {
        passwordToggleBtn.style.transform = 'scale(1)';
    }, 100);
}

/**
 * 显示错误消息 - 增强版，支持不同类型的消息显示
 * @param {string} message - 错误消息内容
 * @param {string} type - 消息类型: 'error' | 'info' | 'success'
 */
function showError(message, type = 'error') {
    // 确保DOM元素已初始化
    if (!errorText || !errorMessage) {
        console.warn('错误消息功能未初始化:', message);
        return;
    }
    
    // 设置错误消息内容
    errorText.textContent = message;
    
    // 显示错误消息容器
    errorMessage.style.display = 'flex';
    
    // 移除所有类型类
    errorMessage.classList.remove('error-type', 'info-type', 'success-type');
    
    // 根据类型添加相应的类
    if (type === 'info') {
        errorMessage.classList.add('info-type');
    } else if (type === 'success') {
        errorMessage.classList.add('success-type');
    } else {
        errorMessage.classList.add('error-type');
    }
    
    // 添加动画效果
    errorMessage.style.opacity = '0';
    errorMessage.style.transform = 'translateY(-10px)';
    
    setTimeout(() => {
        errorMessage.style.opacity = '1';
        errorMessage.style.transform = 'translateY(0)';
        errorMessage.style.transition = 'opacity 0.3s ease, transform 0.3s ease';
    }, 50);
    
    // 根据消息类型设置不同的自动隐藏时间
    let hideDelay = 5000;
    if (type === 'info') {
        hideDelay = 2000;
    } else if (type === 'success') {
        hideDelay = 3500;
    }
    
    // 设置自动隐藏错误消息
    setTimeout(() => {
        hideError();
    }, hideDelay);
}

/**
 * 隐藏错误消息 - 增强版
 */
function hideError() {
    // 确保DOM元素已初始化
    if (!errorMessage) {
        console.warn('错误消息隐藏功能未初始化');
        return;
    }
    
    // 添加淡出动画
    errorMessage.style.opacity = '0';
    errorMessage.style.transform = 'translateY(-10px)';
    
    setTimeout(() => {
        errorMessage.style.display = 'none';
        errorMessage.style.opacity = '1';
        errorMessage.style.transform = 'translateY(0)';
    }, 300);
}

/**
 * 表单验证 - 增强版，适配新的UI结构
 * @returns {boolean} - 是否通过验证
 */
function validateForm() {
    let isValid = true;
    
    // 重置错误提示
    usernameHelp.textContent = '';
    passwordHelp.textContent = '';
    
    // 验证用户名
    const username = usernameInput.value.trim();
    if (!username) {
        usernameHelp.textContent = '请输入用户名或邮箱';
        usernameInput.parentElement.classList.add('input-error');
        isValid = false;
    } else {
        usernameInput.parentElement.classList.remove('input-error');
    }
    
    // 验证密码
    const password = passwordInput.value;
    if (!password) {
        passwordHelp.textContent = '请输入密码';
        passwordInput.parentElement.classList.add('input-error');
        isValid = false;
    } else if (password.length < 6) {
        passwordHelp.textContent = '请输入密码';
        passwordInput.parentElement.classList.add('input-error');
        isValid = false;
    } else {
        passwordInput.parentElement.classList.remove('input-error');
    }
    
    return isValid;
}

/**
 * 设置按钮加载状态 - 适配新的按钮结构
 * @param {boolean} isLoading - 是否显示加载状态
 */
function setButtonLoading(isLoading) {
    // 确保DOM元素已初始化
    if (!loginButton) {
        console.warn('登录按钮未初始化');
        return;
    }
    
    // 动态获取按钮元素
    const btnText = loginButton.querySelector('.btn-text');
    const btnLoading = loginButton.querySelector('.btn-loader');
    
    if (isLoading) {
        loginButton.disabled = true;
        if (btnText) btnText.style.display = 'none';
        if (btnLoading) btnLoading.style.display = 'block';
        // 添加微小的缩放动画
        loginButton.style.transform = 'scale(0.98)';
    } else {
        loginButton.disabled = false;
        if (btnText) btnText.style.display = 'block';
        if (btnLoading) btnLoading.style.display = 'none';
        // 恢复按钮状态
        loginButton.style.transform = 'scale(1)';
    }
}

/**
 * 处理登录提交 - 增强版，支持动画效果和更好的错误处理
 * @param {Event} event - 提交事件
 */
// 登录提交处理
async function handleLogin(e) {
    e.preventDefault();
    
    // 验证表单
    if (!validateForm()) {
        return;
    }
    
    // 确保DOM元素已初始化
    if (!usernameInput || !passwordInput) {
        console.warn('登录功能未初始化');
        showError('系统初始化中，请稍后再试');
        return;
    }
    
    const username = usernameInput.value;
    const password = passwordInput.value;
    const captchaInput = document.getElementById('captcha-input');
    const captcha = captchaInput ? captchaInput.value : '';
    
    // 设置加载状态
    setButtonLoading(true, '登录中...');
    
    try {
        console.log('[LOGIN] 尝试登录用户:', username);
        
        // 调用真实登录API
        const response = await loginApiClient.login(username, password, captcha);
        
        if (response.success) {
            console.log('[LOGIN] 登录成功');
            await handleLoginSuccess(response);
        } else {
            console.warn('[LOGIN] 登录失败:', response.message);
            showError(response.message || '登录失败，请检查用户名和密码');
            
            // 登录失败后刷新验证码
            await refreshCaptcha();
            
            // 添加抖动效果
            if (loginForm) {
                loginForm.classList.add('shake');
                setTimeout(() => {
                    loginForm.classList.remove('shake');
                }, 500);
            }
        }
        
    } catch (error) {
        console.error('[LOGIN] 登录异常:', error);
        showError('网络错误，请稍后重试');
        
        // 异常后刷新验证码
        await refreshCaptcha();
    } finally {
        setButtonLoading(false);
    }
}

/**
 * 记录登录事件
 */
async function logLoginEvent(status, username, loginType, errorMessage = null) {
    try {
        const logData = {
            status,
            username,
            loginType,
            timestamp: new Date().toISOString(),
            userAgent: navigator.userAgent,
            sessionId: loginApiClient.sessionId
        };
        
        if (errorMessage) {
            logData.errorMessage = errorMessage;
        }
        
        console.log('[LOGIN] 记录登录事件:', logData);
        
        // 发送到服务器（可选）
        // await loginApiClient.sendLog(logData);
        
    } catch (error) {
        console.error('[LOGIN] 记录登录事件失败:', error);
    }
}

/**
 * 验证登录表单
 */
function validateLoginForm(username, password, captcha) {
    // 验证用户名
    if (!username) {
        showErrorMessage('请输入用户名');
        return false;
    }
    
    if (username.length < 3 || username.length > 50) {
        showErrorMessage('用户名长度应在3-50个字符之间');
        return false;
    }
    
    // 验证密码
    if (!password) {
        showErrorMessage('请输入密码');
        return false;
    }
    
    if (password.length < 6) {
        showErrorMessage('密码长度不能少于6位');
        return false;
    }
    
    // 验证验证码（如果显示）
    const captchaInput = document.getElementById('captcha');
    if (captchaInput && captchaInput.style.display !== 'none' && !captcha) {
        showErrorMessage('请输入验证码');
        return false;
    }
    
    return true;
}

/**
 * 设置登录按钮加载状态
 */
function setLoginButtonLoading(loading) {
    // 确保DOM元素已初始化
    if (!loginBtn) {
        console.warn('登录按钮未初始化');
        return;
    }
    
    const btnText = loginBtn.querySelector('.btn-text');
    const btnLoader = loginBtn.querySelector('.btn-loader');
    
    if (loading) {
        loginBtn.disabled = true;
        if (btnText) btnText.style.display = 'none';
        if (!btnLoader) {
            const loader = document.createElement('div');
            loader.className = 'btn-loader';
            loader.innerHTML = '<div class="spinner"></div>';
            loginBtn.appendChild(loader);
        } else {
            btnLoader.style.display = 'block';
        }
    } else {
        loginBtn.disabled = false;
        if (btnText) btnText.style.display = 'inline';
        const loader = loginBtn.querySelector('.btn-loader');
        if (loader) {
            loader.style.display = 'none';
        }
    }
}

/**
 * 显示登录成功动画
 */
function showLoginSuccess() {
    // 确保DOM元素已初始化
    if (!loginForm) {
        console.warn('登录表单未初始化');
        return;
    }
    
    const successMessage = document.createElement('div');
    successMessage.className = 'login-success-message';
    successMessage.innerHTML = `
        <div class="success-icon">✓</div>
        <div class="success-text">登录成功！</div>
        <div class="success-subtitle">正在跳转...</div>
    `;
    
    loginForm.appendChild(successMessage);
    
    // 添加成功动画类
    loginForm.classList.add('login-success');
    
    // 3秒后移除成功消息
    setTimeout(() => {
        if (successMessage.parentNode) {
            successMessage.parentNode.removeChild(successMessage);
        }
        loginForm.classList.remove('login-success');
    }, 3000);
}

/**
 * 添加错误动画
 */
function addErrorAnimation() {
    // 确保DOM元素已初始化
    if (!loginForm) {
        console.warn('登录表单未初始化');
        return;
    }
    
    loginForm.classList.add('error-shake');
    
    setTimeout(() => {
        loginForm.classList.remove('error-shake');
    }, 500);
}

/**
 * 刷新验证码
 */
async function refreshCaptcha() {
    try {
        const captchaData = await loginApiClient.getCaptcha('image');
        
        // 确保DOM元素已初始化
        const captchaImage = document.getElementById('captcha-image');
        if (captchaImage && captchaData.image) {
            captchaImage.src = captchaData.image;
            captchaImage.setAttribute('data-captcha-id', captchaData.captchaId);
        }
        
        // 清空验证码输入
        const captchaInput = document.getElementById('captcha');
        if (captchaInput) {
            captchaInput.value = '';
        }
        
        console.log('[LOGIN] 验证码已刷新');
    } catch (error) {
        console.error('[LOGIN] 刷新验证码失败:', error);
    }
}

/**
 * 处理第三方登录
 */
async function handleThirdPartyLogin(provider) {
    try {
        console.log(`[LOGIN] 开始${provider}第三方登录`);
        
        // 获取授权URL
        const authUrl = loginApiClient.getThirdPartyAuthUrl(provider);
        
        // 打开授权窗口
        const popup = window.open(
            authUrl,
            `${provider}_login`,
            'width=500,height=600,scrollbars=yes,resizable=yes'
        );
        
        // 监听授权回调
        const checkClosed = setInterval(() => {
            if (popup.closed) {
                clearInterval(checkClosed);
                console.log(`[LOGIN] ${provider}授权窗口已关闭`);
            }
        }, 1000);
        
        // 监听消息（用于获取授权码）
        window.addEventListener('message', async (event) => {
            if (event.origin !== window.location.origin) {
                return;
            }
            
            if (event.data.type === 'oauth_callback') {
                const { code, state, provider: callbackProvider } = event.data;
                
                if (callbackProvider === provider) {
                    try {
                        setLoginButtonLoading(true);
                        
                        // 处理OAuth回调
                        const result = await loginApiClient.loginWithThirdParty(provider, code, state);
                        
                        if (result.success) {
                            await logLoginEvent('success', result.data.user.username, provider);
                            showLoginSuccess();
                            
                            setTimeout(() => {
                                window.location.href = 'index.html';
                            }, 1500);
                        } else {
                            throw new Error(result.message || `${provider}登录失败`);
                        }
                        
                    } catch (error) {
                        console.error(`[LOGIN] ${provider}登录失败:`, error);
                        await logLoginEvent('failed', null, provider, error.message);
                        showErrorMessage(`${provider}登录失败: ${error.message}`);
                    } finally {
                        setLoginButtonLoading(false);
                        popup.close();
                    }
                }
            }
        });
        
    } catch (error) {
        console.error(`[LOGIN] ${provider}登录初始化失败:`, error);
        showErrorMessage(`${provider}登录初始化失败: ${error.message}`);
    }
}

/**
 * 获取提供商中文名称
 */
function getProviderName(provider) {
    const providerNames = {
        qq: 'QQ',
        wechat: '微信',
        google: 'Google',
        github: 'GitHub',
        hotmail: 'Hotmail'
    };
    
    return providerNames[provider] || provider;
}

/**
 * 添加第三方登录事件监听器
 */
function addThirdPartyLoginListeners() {
    const socialButtons = document.querySelectorAll('.social-button');
    socialButtons.forEach(button => {
        button.addEventListener('click', () => {
            const provider = button.dataset.provider;
            handleThirdPartyLogin(provider);
        });
    });
}

/**
 * 添加表单输入事件监听器 - 增强版
 */
function addInputEventListeners() {
    // 为输入框添加聚焦效果
    const inputs = document.querySelectorAll('input[type="text"], input[type="password"]');
    inputs.forEach(input => {
        input.addEventListener('focus', function() {
            this.parentElement.classList.add('input-focused');
        });
        input.addEventListener('blur', function() {
            this.parentElement.classList.remove('input-focused');
        });
    });
    
    // 用户名输入事件
    usernameInput.addEventListener('input', () => {
        if (usernameInput.value.trim()) {
            usernameInput.parentElement.classList.remove('input-error');
            usernameHelp.textContent = '';
            hideError();
        }
    });
    
    // 密码输入事件
    passwordInput.addEventListener('input', () => {
        if (passwordInput.value) {
            passwordInput.parentElement.classList.remove('input-error');
            passwordHelp.textContent = '';
            hideError();
        }
    });
    
    // 添加键盘导航支持
    usernameInput.addEventListener('keydown', (e) => {
        if (e.key === 'Enter') {
            passwordInput.focus();
            e.preventDefault();
        }
    });
    
    // 密码输入键盘事件
    passwordInput.addEventListener('keypress', (e) => {
        if (e.key === 'Enter') {
            handleLogin(e);
        }
    });
    
    // 密码切换按钮事件
    if (passwordToggleBtn) {
        passwordToggleBtn.addEventListener('click', togglePasswordVisibility);
    }
    
    // 添加第三方登录事件监听
    addThirdPartyLoginListeners();
}

/**
 * 加载版本信息
 */
function loadVersionInfo() {
    try {
        const versionElement = document.getElementById('version');
        if (versionElement) {
            versionElement.textContent = 'v1.0.0';
        }
    } catch (error) {
        console.error('[ERROR] Failed to load version info:', error);
    }
}

/**
 * 加载记住的用户名
 */
function loadRememberedUsername() {
    try {
        const rememberedUsername = localStorage.getItem('rememberedUsername');
        const usernameInput = document.getElementById('username');
        const rememberCheckbox = document.getElementById('remember');
        
        if (rememberedUsername && usernameInput && rememberCheckbox) {
            usernameInput.value = rememberedUsername;
            rememberCheckbox.checked = true;
        }
    } catch (error) {
        console.error('[ERROR] Failed to load remembered username:', error);
    }
}

/**
 * 页面初始化 - 增强版，添加更多动画效果
 */
function init() {
    console.log('[DEBUG] init() function called');
    
    // 初始化DOM元素缓存
    console.log('[DEBUG] Initializing DOM elements...');
    loginForm = document.getElementById('loginForm');
    console.log('[DEBUG] loginForm:', loginForm);
    
    usernameInput = document.getElementById('username');
    passwordInput = document.getElementById('password');
    rememberCheckbox = document.getElementById('remember');
    
    // 安全地获取登录按钮
    if (loginForm && typeof loginForm.querySelector === 'function') {
        loginButton = loginForm.querySelector('.login-button');
    } else {
        loginButton = document.querySelector('.login-button');
    }
    
    versionElement = document.getElementById('version');
    usernameHelp = document.getElementById('usernameHelp');
    passwordHelp = document.getElementById('passwordHelp');
    btnText = loginButton ? loginButton.querySelector('.btn-text') : null;
    btnLoading = loginButton ? loginButton.querySelector('.btn-loading') : null;
    passwordToggleBtn = document.getElementById('togglePassword');
    console.log('[DEBUG] passwordToggleBtn:', passwordToggleBtn);
    errorMessage = document.getElementById('errorMessage');
    errorText = document.getElementById('errorText');
    loginContainer = document.querySelector('.login-container');
    console.log('[DEBUG] loginContainer:', loginContainer);
    currentTimeElement = document.getElementById('current-time');
    lunarDateElement = document.getElementById('lunar-date');
    buddhistYearElement = document.getElementById('buddhist-year');
    eventsList = document.getElementById('events-list');
    toggleEventsBtn = document.getElementById('toggle-events-btn');
    
    // 加载版本信息
    loadVersionInfo();
    
    // 加载记住的用户名
    loadRememberedUsername();
    
    // 初始化佛教时间显示
    initBuddhistTime();
    
    // 初始化佛教事件切换功能
    initEventsToggle();
    
    // 添加表单事件监听器
    addInputEventListeners();
    
    // 添加页面入场动画 - 添加null检查
    if (loginContainer) {
        loginContainer.style.opacity = '0';
        loginContainer.style.transform = 'translateY(20px)';
        loginContainer.style.transition = 'all 0.6s ease-out';
        
        // 触发入场动画
        setTimeout(() => {
            if (loginContainer) {
                loginContainer.style.opacity = '1';
                loginContainer.style.transform = 'translateY(0)';
                
                // 动画完成后聚焦到用户名输入框
                setTimeout(() => {
                    if (usernameInput) {
                        usernameInput.focus();
                    }
                }, 300);
            }
        }, 100);
    }
    
    // 为装饰元素添加动画
    const decorativeElements = document.querySelectorAll('.decorative-element');
    decorativeElements.forEach((el, index) => {
        setTimeout(() => {
            el.style.opacity = '0.8';
            el.style.transition = 'opacity 1s ease-in';
        }, index * 300);
    });
    
    // 添加表单提交事件监听器
    if (loginForm) {
        loginForm.addEventListener('submit', handleLogin);
    }
}

// 页面加载完成后初始化
window.addEventListener('load', init);

// 暴露一些方法供全局使用（如果需要）
window.togglePasswordVisibility = togglePasswordVisibility;
window.handleLogin = handleLogin;

// 登录成功处理
async function handleLoginSuccess(response) {
    console.log('[LOGIN] 登录成功:', response);
    
    // 创建会话
    const sessionCreated = await sessionManager.createSession(response);
    if (!sessionCreated) {
        console.error('[LOGIN] 会话创建失败');
        showError('登录成功但会话创建失败，请重试');
        return;
    }
    
    // 显示成功动画
    showSuccessAnimation();
    
    // 更新按钮状态
    const loginBtn = document.getElementById('login-btn');
    loginBtn.classList.add('success');
    loginBtn.innerHTML = '<i class="fas fa-check"></i> 登录成功';
    
    // 保存用户名（如果勾选了记住我）
    const rememberMe = document.getElementById('remember-me').checked;
    if (rememberMe) {
        localStorage.setItem('rememberedUsername', document.getElementById('username').value);
    }
    
    // 延迟跳转
    setTimeout(() => {
        window.location.href = '../index.html';
    }, 1500);
}