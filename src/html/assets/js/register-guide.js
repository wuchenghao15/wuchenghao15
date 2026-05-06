
// 兼容性检查和回退方案
(function() {
    'use strict';
    
    // 检查Array.includes支持
    if (!Array.prototype.includes) {
        Array.prototype.includes = function(searchElement, fromIndex) {
            fromIndex = parseInt(fromIndex) || 0;
            for (let i = fromIndex; i < this.length; i++) {
                if (this[i] === searchElement) {
                    return true;
                }
            }
            return false;
        };
    }
})();

        // 滚动检测功能
        window.addEventListener('scroll', function() {
            const scrollHeight = document.documentElement.scrollHeight;
            const scrollTop = document.documentElement.scrollTop || document.body.scrollTop;
            const clientHeight = document.documentElement.clientHeight;
            
            // 当滚动到页面底部时显示阅读完成标记
            if (scrollTop + clientHeight >= scrollHeight - 100) {
                document.getElementById('read-complete').style.display = 'block';
            }
        });
        
        // 标记为已阅读
        function markAsRead() {
            // 存储阅读完成状态到sessionStorage
            sessionStorage.setItem('registerGuideRead', 'true');
            alert('感谢您阅读完注册手册！现在您可以返回注册页面并勾选同意条款。');
            // 关闭当前窗口（如果是在新窗口打开的）
            if (window.opener) {
                // 通知父窗口阅读已完成
                window.opener.postMessage({ type: 'REGISTER_GUIDE_READ' }, '*');
                // 关闭当前窗口
                window.close();
            } else {
                // 如果不是新窗口打开的，返回登录页
                window.location.href = '/';
            }
        }
    