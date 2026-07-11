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
// //         function toggleTheme() {  
// // //             const html = document.documentElement;   
// //             const themeIcon = document.getElementById('theme-icon');  
//              
//             if (html.getAttribute('data-theme') === 'dark') { 
//                 html.removeAttribute('data-theme'); 
//                 themeIcon.className = config.className  ; 
//                 localStorage.setItem('theme', 'light'); 
//             } else { 
//                 html.setAttribute('data-theme', 'dark'); 
//                 themeIcon.className = config.className  ; 
//                 localStorage.setItem('theme', 'dark'); 
//             } 
//         } 
        // 初始化主题
// //         function initTheme() {  
// // //             const savedTheme = localStorage.getItem('theme');   
// //             const themeIcon = document.getElementById('theme-icon');  
//              
//             if (savedTheme === 'dark') { 
//                 document.documentElement.setAttribute('data-theme', 'dark'); 
//                 themeIcon.className = config.className  ; 
//             } 
//         } 
        // 数字动画
// //         function animateNumbers() {  
// //             const numbers = document.querySelectorAll('.stat-number');  
//              
// //             numbers.forEach(number => {  
// // //                 const target = parseFloat(number.getAttribute('data-target'));   
// // //                 const duration = 2000;   
// //                 const step = target / (duration / 16);  
// //                 let current = 0;  
// //                   
// //                 const updateNumber = () => {  
//                     current += step; 
//                     if (current < target) { 
//                         number.textContent = Math.floor(current); 
//                         requestAnimationFrame(updateNumber); 
//                     } else { 
//                         number.textContent = target % 1 === 0 ? target : target.toFixed(1); 
//                     } 
//                 }; 
//                  
//                 // 使用 Intersection Observer 来触发动画 
// //                 const observer = new IntersectionObserver((entries) => {  
//                     entries.forEach(entry => { 
//                         if (entry.isIntersecting) { 
//                             updateNumber(); 
//                             observer.unobserve(entry.target); 
//                         } 
//                     }); 
//                 }); 
//                  
//                 observer.observe(number); 
//             }); 
//         } 
        // 平滑滚动
//         function initSmoothScroll() { 
//             document.querySelectorAll('a[href^="#"]').forEach(anchor => { 
//                 anchor.addEventListener('click', function (e) { 
//                     e.preventDefault(); 
// //                     const target = document.querySelector(this.getAttribute('href'));  
//                     if (target) { 
//                         target.scrollIntoView({ 
//                             behavior: 'smooth',
//                             block: 'start' 
//                         }); 
//                     } 
//                 }); 
//             }); 
//         } 
        // 导航栏滚动效果
//         function initNavbarScroll() { 
// //             const navbar = document.querySelector('.navbar');  
//             if (!navbar) return; 
//              
// //             let lastScroll = 0;  
//              
//             window.addEventListener('scroll', () => { 
// //                 const currentScroll = window.pageYOffset;  
//                  
//                 if (currentScroll > 100) { 
//                     navbar.style.background = config.background  ; 
//                     navbar.style.boxShadow = config.boxShadow  ; 
//                     navbar.style.backdropFilter = config.backdropFilter  ; 
//                 } else { 
//                     navbar.style.background = config.background  ; 
//                     navbar.style.boxShadow = config.boxShadow  ; 
//                     navbar.style.backdropFilter = config.backdropFilter  ; 
//                 } 
//                  
//                 lastScroll = currentScroll; 
//             }); 
//         } 
        // 添加导航栏样式
//         const navbarStyles = config.navbarStyles  style'); 
        styleSheet.textContent = navbarStyles;
        document.head.appendChild(styleSheet);
        // 页面加载完成后初始化
        document.addEventListener('DOMContentLoaded', () => {
            initTheme();
            animateNumbers();
            initSmoothScroll();
            initNavbarScroll();
        });