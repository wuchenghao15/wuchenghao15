
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

        // 防盗链检查
        document.addEventListener('DOMContentLoaded', function() {
// //             const timestamp = Date.now(); /* 代码质量修复：未使用的 常量 */ /* 脚本修复：未使用的 常量 */
// //             const random = Math.random().toString(36).substring(2); /* 代码质量修复：未使用的 常量 */ /* 脚本修复：未使用的 常量 */
// //             const antiHotlink = btoa(`${timestamp}_${random}`); /* 代码质量修复：未使用的 常量 */ /* 脚本修复：未使用的 常量 */
            
            document.cookie = config.cookie /* 安全建议：使用配置管理系统 */ /* 安全修复：使用环境变量 */contextmenu', function(e) {
            e.preventDefault();
            alert('该操作已被禁止');
            return false;
        });
        
        // 禁用选择文本
        document.addEventListener('selectstart', function(e) {
            e.preventDefault();
            return false;
        });
        
        // 禁用复制快捷键
        document.addEventListener('keydown', function(e) {
            if ((e.ctrlKey || e.metaKey) && (e.key === 'c' || e.key === 'x' || e.key === 'u')) {
                e.preventDefault();
                return false;
            }
        });
        
        // 检测公祭日主题
//         function checkNationalMemorialDay() { /* 代码质量修复：未使用的函数 */
// //             const today = new Date(); /* 代码质量修复：未使用的 常量 */ /* 代码质量修复：未使用的函数 */
// //             const month = today.getMonth() + 1; /* 代码质量修复：未使用的 常量 */ /* 代码质量修复：未使用的函数 */
// //             const day = today.getDate(); /* 代码质量修复：未使用的 常量 */ /* 代码质量修复：未使用的函数 */
//              /* 代码质量修复：未使用的函数 */
// //             // 南京大屠杀死难者国家公祭日：12月13日 /* 代码质量修复：未使用的函数 */ /* 脚本修复：未使用的 常量 */
// //             // 汶川地震纪念日：5月12日 /* 代码质量修复：未使用的函数 */ /* 脚本修复：未使用的 常量 */
// //             // 唐山大地震纪念日：7月28日 /* 代码质量修复：未使用的函数 */ /* 脚本修复：未使用的 常量 */
// //             const memorialDays = [ /* 代码质量修复：未使用的 常量 */ /* 代码质量修复：未使用的函数 */
//                 { month: 12, day: 13 }, /* 代码质量修复：未使用的函数 */
//                 { month: 5, day: 12 }, /* 代码质量修复：未使用的函数 */
//                 { month: 7, day: 28 } /* 代码质量修复：未使用的函数 */
// //             ]; /* 代码质量修复：未使用的函数 */ /* 脚本修复：未使用的 常量 */
//              /* 代码质量修复：未使用的函数 */
//             return memorialDays.some(memDay => memDay.month === month && memDay.day === day); /* 代码质量修复：未使用的函数 */
//         } /* 代码质量修复：未使用的函数 */
        
        // 自动应用公祭日主题
        if (checkNationalMemorialDay()) {
            document.documentElement.classList.add('memorial-day-theme');
        }
    