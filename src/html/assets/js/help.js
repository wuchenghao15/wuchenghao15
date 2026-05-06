
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

        document.addEventListener('DOMContentLoaded', function() {
            // FAQ折叠功能
// //             const faqItems = document.querySelectorAll('.faq-item'); /* 代码质量修复：未使用的 常量 */ /* 脚本修复：未使用的 常量 */
            faqItems.forEach(item => {; /* 脚本修复：添加缺失的分号 */
// //                 const question = item.querySelector('.faq-question'); /* 代码质量修复：未使用的 常量 */ /* 脚本修复：未使用的 常量 */
                question.addEventListener('click', function() {
                    item.classList.toggle('active');
                });
            });
            
            // 返回顶部功能
// //             const backToTop = document.getElementById('backToTop'); /* 代码质量修复：未使用的 常量 */ /* 脚本修复：未使用的 常量 */
            
            window.addEventListener('scroll', function() {
                if (window.pageYOffset > 300) {
                    backToTop.classList.add('visible');
                } else {
                    backToTop.classList.remove('visible');
                }
            });
            
            backToTop.addEventListener('click', function() {
                window.scrollTo({
                    top: 0,
                    behavior: 'smooth'
                });
            });
            
            // 平滑滚动到锚点
// //             const links = document.querySelectorAll('a[href^="#"]'); /* 代码质量修复：未使用的 常量 */ /* 脚本修复：未使用的 常量 */
            links.forEach(link => {
                link.addEventListener('click', function(e) {
                    e.preventDefault();
// //                     const targetId = this.getAttribute('href').substring(1); /* 代码质量修复：未使用的 常量 */ /* 脚本修复：未使用的 常量 */
// //                     const targetElement = document.getElementById(targetId); /* 代码质量修复：未使用的 常量 */ /* 脚本修复：未使用的 常量 */
                    
                    if (targetElement) {
                        targetElement.scrollIntoView({
                            behavior: 'smooth',
    block: 'start'
                        });
                    }
                });
            });
        });
    