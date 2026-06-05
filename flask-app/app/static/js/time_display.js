// 系统时间显示功能
function updateCurrentTime() {
    const now = new Date();
    
    // 格式化时间：HH:MM:SS
    const hours = now.getHours().toString().padStart(2, '0');
    const minutes = now.getMinutes().toString().padStart(2, '0');
    const seconds = now.getSeconds().toString().padStart(2, '0');
    
    // 格式化日期：YYYY-MM-DD
    const year = now.getFullYear();
    const month = (now.getMonth() + 1).toString().padStart(2, '0');
    const day = now.getDate().toString().padStart(2, '0');
    
    const formattedTime = `${year}-${month}-${day} ${hours}:${minutes}:${seconds}`;
    
    // 更新DOM
    const timeElement = document.getElementById('current-time');
    if (timeElement) {
        timeElement.textContent = formattedTime;
    }
}

// 获取并显示IP地址
function getAndDisplayIP() {
    // 使用ipify API获取IP地址
    fetch('https://api.ipify.org?format=json')
        .then(response => response.json())
        .then(data => {
            const ip = data.ip;
            // 更新DOM
            const ipElement = document.getElementById('user-ip');
            if (ipElement) {
                ipElement.textContent = `IP: ${ip}`;
            }
        })
        .catch(error => {
            console.error('获取IP地址失败:', error);
        });
}

// 页面加载完成后更新时间和IP
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', function() {
        updateCurrentTime();
        getAndDisplayIP();
        // 每秒更新一次时间
        setInterval(updateCurrentTime, 1000);
    });
} else {
    updateCurrentTime();
    getAndDisplayIP();
    // 每秒更新一次时间
    setInterval(updateCurrentTime, 1000);
}
