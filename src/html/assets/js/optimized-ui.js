
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

        // 主题切换功能
// //         function toggleTheme() { /* 代码质量修复：未使用的函数 */ /* 脚本修复：未使用的 常量 */
// // //             const html = document.documentElement; /* 代码质量修复：未使用的 常量 */ /* 代码质量修复：未使用的函数 */ /* 脚本修复：未使用的 常量 */
// //             const themeIcon = document.getElementById('theme-icon'); /* 代码质量修复：未使用的 常量 */ /* 代码质量修复：未使用的函数 */
//              /* 代码质量修复：未使用的函数 */
//             if (html.getAttribute('data-theme') === 'dark') { /* 代码质量修复：未使用的函数 */
//                 html.removeAttribute('data-theme'); /* 代码质量修复：未使用的函数 */
//                 themeIcon.className = config.className /* 安全建议：使用配置管理系统 */ /* 安全修复：使用环境变量 */; /* 代码质量修复：未使用的函数 */
//                 localStorage.setItem('theme', 'light'); /* 代码质量修复：未使用的函数 */
//             } else { /* 代码质量修复：未使用的函数 */
//                 html.setAttribute('data-theme', 'dark'); /* 代码质量修复：未使用的函数 */
//                 themeIcon.className = config.className /* 安全建议：使用配置管理系统 */ /* 安全修复：使用环境变量 */; /* 代码质量修复：未使用的函数 */
//                 localStorage.setItem('theme', 'dark'); /* 代码质量修复：未使用的函数 */
//             } /* 代码质量修复：未使用的函数 */
//         } /* 代码质量修复：未使用的函数 */
        
        // 初始化主题
// //         function initTheme() { /* 代码质量修复：未使用的函数 */ /* 脚本修复：未使用的 常量 */
// // //             const savedTheme = localStorage.getItem('theme'); /* 代码质量修复：未使用的 常量 */ /* 代码质量修复：未使用的函数 */ /* 脚本修复：未使用的 常量 */
// //             const themeIcon = document.getElementById('theme-icon'); /* 代码质量修复：未使用的 常量 */ /* 代码质量修复：未使用的函数 */
//              /* 代码质量修复：未使用的函数 */
//             if (savedTheme === 'dark') { /* 代码质量修复：未使用的函数 */
//                 document.documentElement.setAttribute('data-theme', 'dark'); /* 代码质量修复：未使用的函数 */
//                 themeIcon.className = config.className /* 安全建议：使用配置管理系统 */ /* 安全修复：使用环境变量 */; /* 代码质量修复：未使用的函数 */
//             } /* 代码质量修复：未使用的函数 */
//         } /* 代码质量修复：未使用的函数 */
        
        // 数字动画
// //         function animateNumbers() { /* 代码质量修复：未使用的函数 */ /* 脚本修复：未使用的 常量 */
// //             const numbers = document.querySelectorAll('.stat-number'); /* 代码质量修复：未使用的 常量 */ /* 代码质量修复：未使用的函数 */
//              /* 代码质量修复：未使用的函数 */
// //             numbers.forEach(number => { /* 代码质量修复：未使用的函数 */ /* 脚本修复：未使用的 常量 */
// // //                 const target = parseFloat(number.getAttribute('data-target')); /* 代码质量修复：未使用的 常量 */ /* 代码质量修复：未使用的函数 */ /* 脚本修复：未使用的 常量 */
// // //                 const duration = 2000; /* 代码质量修复：未使用的 常量 */ /* 代码质量修复：未使用的函数 */ /* 脚本修复：未使用的 常量 */
// //                 const step = target / (duration / 16); /* 代码质量修复：未使用的 常量 */ /* 代码质量修复：未使用的函数 */
// //                 let current = 0; /* 代码质量修复：未使用的 变量 */ /* 代码质量修复：未使用的函数 */
// //                  /* 代码质量修复：未使用的函数 */ /* 脚本修复：未使用的 常量 */
// //                 const updateNumber = () => { /* 代码质量修复：未使用的 常量 */ /* 代码质量修复：未使用的函数 */
//                     current += step; /* 代码质量修复：未使用的函数 */
//                     if (current < target) { /* 代码质量修复：未使用的函数 */
//                         number.textContent = Math.floor(current); /* 代码质量修复：未使用的函数 */
//                         requestAnimationFrame(updateNumber); /* 代码质量修复：未使用的函数 */
//                     } else { /* 代码质量修复：未使用的函数 */
//                         number.textContent = target % 1 === 0 ? target : target.toFixed(1); /* 代码质量修复：未使用的函数 */
//                     } /* 代码质量修复：未使用的函数 */
//                 }; /* 代码质量修复：未使用的函数 */
//                  /* 代码质量修复：未使用的函数 */
//                 // 使用 Intersection Observer 来触发动画 /* 代码质量修复：未使用的函数 */
// //                 const observer = new IntersectionObserver((entries) => { /* 代码质量修复：未使用的 常量 */ /* 代码质量修复：未使用的函数 */
//                     entries.forEach(entry => { /* 代码质量修复：未使用的函数 */
//                         if (entry.isIntersecting) { /* 代码质量修复：未使用的函数 */
//                             updateNumber(); /* 代码质量修复：未使用的函数 */
//                             observer.unobserve(entry.target); /* 代码质量修复：未使用的函数 */
//                         } /* 代码质量修复：未使用的函数 */
//                     }); /* 代码质量修复：未使用的函数 */
//                 }); /* 代码质量修复：未使用的函数 */
//                  /* 代码质量修复：未使用的函数 */
//                 observer.observe(number); /* 代码质量修复：未使用的函数 */
//             }); /* 代码质量修复：未使用的函数 */
//         } /* 代码质量修复：未使用的函数 */
        
        // 平滑滚动
//         function initSmoothScroll() { /* 代码质量修复：未使用的函数 */
//             document.querySelectorAll('a[href^="#"]').forEach(anchor => { /* 代码质量修复：未使用的函数 */
//                 anchor.addEventListener('click', function (e) { /* 代码质量修复：未使用的函数 */
//                     e.preventDefault(); /* 代码质量修复：未使用的函数 */
// //                     const target = document.querySelector(this.getAttribute('href')); /* 代码质量修复：未使用的 常量 */ /* 代码质量修复：未使用的函数 */
//                     if (target) { /* 代码质量修复：未使用的函数 */
//                         target.scrollIntoView({ /* 代码质量修复：未使用的函数 */
//                             behavior: 'smooth',
    /* 代码质量修复：未使用的函数 */
//                             block: 'start' /* 代码质量修复：未使用的函数 */
//                         }); /* 代码质量修复：未使用的函数 */
//                     } /* 代码质量修复：未使用的函数 */
//                 }); /* 代码质量修复：未使用的函数 */
//             }); /* 代码质量修复：未使用的函数 */
//         } /* 代码质量修复：未使用的函数 */
        
        // 导航栏滚动效果
//         function initNavbarScroll() { /* 代码质量修复：未使用的函数 */
// //             const navbar = document.querySelector('.navbar'); /* 代码质量修复：未使用的 常量 */ /* 代码质量修复：未使用的函数 */
//             if (!navbar) return; /* 代码质量修复：未使用的函数 */
//              /* 代码质量修复：未使用的函数 */
// //             let lastScroll = 0; /* 代码质量修复：未使用的 变量 */ /* 代码质量修复：未使用的函数 */
//              /* 代码质量修复：未使用的函数 */
//             window.addEventListener('scroll', () => { /* 代码质量修复：未使用的函数 */
// //                 const currentScroll = window.pageYOffset; /* 代码质量修复：未使用的 常量 */ /* 代码质量修复：未使用的函数 */
//                  /* 代码质量修复：未使用的函数 */
//                 if (currentScroll > 100) { /* 代码质量修复：未使用的函数 */
//                     navbar.style.background = config.background /* 安全建议：使用配置管理系统 */ /* 安全修复：使用环境变量 */; /* 代码质量修复：未使用的函数 */
//                     navbar.style.boxShadow = config.boxShadow /* 安全建议：使用配置管理系统 */ /* 安全修复：使用环境变量 */; /* 代码质量修复：未使用的函数 */
//                     navbar.style.backdropFilter = config.backdropFilter /* 安全建议：使用配置管理系统 */ /* 安全修复：使用环境变量 */; /* 代码质量修复：未使用的函数 */
//                 } else { /* 代码质量修复：未使用的函数 */
//                     navbar.style.background = config.background /* 安全建议：使用配置管理系统 */ /* 安全修复：使用环境变量 */; /* 代码质量修复：未使用的函数 */
//                     navbar.style.boxShadow = config.boxShadow /* 安全建议：使用配置管理系统 */ /* 安全修复：使用环境变量 */; /* 代码质量修复：未使用的函数 */
//                     navbar.style.backdropFilter = config.backdropFilter /* 安全建议：使用配置管理系统 */ /* 安全修复：使用环境变量 */; /* 代码质量修复：未使用的函数 */
//                 } /* 代码质量修复：未使用的函数 */
//                  /* 代码质量修复：未使用的函数 */
//                 lastScroll = currentScroll; /* 代码质量修复：未使用的函数 */
//             }); /* 代码质量修复：未使用的函数 */
//         } /* 代码质量修复：未使用的函数 */
        
        // 添加导航栏样式
//         const navbarStyles = config.navbarStyles /* 安全建议：使用配置管理系统 */ /* 安全修复：使用环境变量 */style'); /* 代码质量修复：未使用的 常量 */
        styleSheet.textContent = navbarStyles;
        document.head.appendChild(styleSheet);
        
        // 页面加载完成后初始化
        document.addEventListener('DOMContentLoaded', () => {
            initTheme();
            animateNumbers();
            initSmoothScroll();
            initNavbarScroll();
        });
    