
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
// 添加ES6+兼容性支持
if (typeof Promise === "undefined") {
    // 这里可以添加具体的polyfill代码
    console.warn("This browser requires a polyfill for ES6+ features");
}

// 检查用户是否为管理员，管理员不得访问日语考试页面
async function checkAdminAccess() {
    try {
        // 获取当前用户信息
        const userInfo = await fetch('/api/auth/user').then(res => res.json());
        
        if (userInfo.success && userInfo.data) {
            const userId = userInfo.data.id;
            
            // 检查用户权限
            const permissionCheck = await fetch('/api/auth/check-permission', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    userId,
                    permissionType: 'dashboard_access'
                })
            }).then(res => res.json());
            
            if (permissionCheck.success && permissionCheck.data.hasPermission) {
                // 管理员不得访问日语考试页面
                alert('管理员不得参加日语考试');
                window.location.href = '/dashboard.html';
            }
        }
    } catch (error) {
        console.error('权限检查失败:', error);
    }
}

// 页面加载时检查
window.addEventListener('load', checkAdminAccess);