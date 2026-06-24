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
    // 确保页脚始终在页面底部
    function adjustFooter() {
        const body = document.body;
        const html = document.documentElement;
        const footer = document.querySelector('.footer');
        if (!footer) return;
        const height = Math.max(body.scrollHeight, body.offsetHeight, html.clientHeight, html.scrollHeight, html.offsetHeight);
        if (height <= window.innerHeight) {
            footer.style.position = 'fixed';
            footer.style.bottom = '0';
            footer.style.width = '100%';
        } else {
            footer.style.position = 'relative';
        }
    }
    window.addEventListener('load', adjustFooter);
    window.addEventListener('resize', adjustFooter);