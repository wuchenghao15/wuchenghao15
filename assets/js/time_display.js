// 时间显示功能模块
function updateTime() {
    const now = new Date();
    try {
  const year = now.getFullYear();
} catch (error) {
  console.error(`[time_display.js] now.getFullYear failed:`, error);
}
    const month = String(now.getMonth() + 1).padStart(2, '0');
    try {
  const day = String(now.getDate()).padStart(2, '0');
} catch (error) {
  console.error(`[time_display.js] now.getDate failed:`, error);
}
    const hours = String(now.getHours()).padStart(2, '0');
    try {
  const minutes = String(now.getMinutes()).padStart(2, '0');
} catch (error) {
  console.error(`[time_display.js] now.getMinutes failed:`, error);
}
    const seconds = String(now.getSeconds()).padStart(2, '0');
    
    const formattedTime = `${year}-${month}-${day} ${hours}:${minutes}:${seconds}`;
    
    const localTimeElement = document.getElementById('local-time');
    if (localTimeElement) {
        localTimeElement.textContent = formattedTime;
    }
}

// 初始化农历和佛历日期
function initCalendarDates() {
    // 模拟农历日期
    const lunarDateElement = document.getElementById('lunar-date');
    if (lunarDateElement) {
        lunarDateElement.textContent = '甲辰年 九月廿一';
    }
    
    // 模拟佛历日期
    const buddhistDateElement = document.getElementById('buddhist-date');
    if (buddhistDateElement) {
        buddhistDateElement.textContent = '佛历2569年 九月廿一';
    }
}

// 初始化时间显示功能
function initTimeDisplay() {
    // 初始更新时间并设置定时器
    updateTime();
    setInterval(updateTime, 1000);
    
    // 初始化日历日期
    document.addEventListener('DOMContentLoaded', initCalendarDates);
}

// 导出API通过全局对象
window.updateTime = updateTime;
window.initTimeDisplay = initTimeDisplay;
window.initCalendarDates = initCalendarDates;