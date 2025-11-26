// 强制应用浅色主题脚本
console.log('正在强制应用浅色主题...');

// 清除可能存在的深色主题偏好
if (typeof localStorage !== 'undefined') {
    localStorage.setItem('theme', 'light');
    console.log('已将本地存储主题设置为: light');
}

// 移除body上的dark-theme类
if (document && document.body) {
    document.body.classList.remove('dark-theme');
    console.log('已移除dark-theme类');
}

console.log('浅色主题已强制应用完成！');