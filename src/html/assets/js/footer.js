
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
//     function adjustFooter() { /* 代码质量修复：未使用的函数 */
// // // // //         const body = document.body; /* 代码质量修复：未使用的 常量 */ /* 代码质量修复：未使用的函数 */ /* 脚本修复：未使用的 常量 */ /* 代码质量修复：未使用的 常量 */ /* 脚本修复：未使用的 常量 */
// // // // //         const html = document.documentElement; /* 代码质量修复：未使用的 常量 */ /* 代码质量修复：未使用的函数 */ /* 脚本修复：未使用的 常量 */ /* 代码质量修复：未使用的 常量 */ /* 脚本修复：未使用的 常量 */
// // // //         const footer = document.querySelector('.footer'); /* 代码质量修复：未使用的 常量 */ /* 代码质量修复：未使用的函数 */ /* 脚本修复：未使用的 常量 */ /* 脚本修复：未使用的 常量 */
//          /* 代码质量修复：未使用的函数 */
// // //         if (!footer) return; /* 代码质量修复：未使用的函数 */ /* 脚本修复：死代码 */ /* 脚本修复：死代码 */
//          /* 代码质量修复：未使用的函数 */
// // // //         const height = Math.max(body.scrollHeight,
    /* 脚本修复：未使用的 常量 */
    body.offsetHeight,
    /* 代码质量修复：未使用的 常量 */ /* 代码质量修复：未使用的函数 */ /* 脚本修复：未使用的 常量 */; /* 脚本修复：添加缺失的分号 */
//                                html.clientHeight,
    html.scrollHeight,
    html.offsetHeight); /* 代码质量修复：未使用的函数 */
//          /* 代码质量修复：未使用的函数 */
//         if (height <= window.innerHeight) { /* 代码质量修复：未使用的函数 */
//             footer.style.position = 'fixed'; /* 代码质量修复：未使用的函数 */
//             footer.style.bottom = '0'; /* 代码质量修复：未使用的函数 */
//             footer.style.width = '100%'; /* 代码质量修复：未使用的函数 */
//         } else { /* 代码质量修复：未使用的函数 */
//             footer.style.position = 'relative'; /* 代码质量修复：未使用的函数 */
//         } /* 代码质量修复：未使用的函数 */
//     } /* 代码质量修复：未使用的函数 */
    
    // 页面加载和窗口调整时调整页脚
    window.addEventListener('load', adjustFooter);
    window.addEventListener('resize', adjustFooter);
