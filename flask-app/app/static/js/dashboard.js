// 仪表盘功能初始化
function initDashboard() {
    // 初始化过渡动画
    initTransitionAnimation();
    
    // 添加页面元素依次显示动画
    initElementRevealAnimations();
    
    // 添加菜单交互效果
    initMenuInteractions();
    
    // 添加统计卡片动画
    initStatCardAnimations();
    
    // 添加功能卡片交互
    initFeatureCardInteractions();
    
    // 添加平滑滚动效果
    initSmoothScroll();
    
    // 添加页面加载完成动画
    initPageLoadComplete();
}

// 初始化过渡动画 - 增强版
function initTransitionAnimation() {
    const overlay = document.getElementById('transition-overlay');
    const spinner = overlay?.querySelector('.spinner-ring');
    const text = overlay?.querySelector('.transition-text');
    
    if (overlay) {
        // 初始显示过渡动画
        overlay.classList.add('active');
        
        // 增强加载动画
        if (spinner) {
            spinner.style.animation = 'spin 1s linear infinite, pulse 2s ease-in-out infinite';
        }
        
        if (text) {
            // 加载文本淡入淡出效果
            text.style.animation = 'fadeInOut 2s ease-in-out infinite';
        }
        
        // 模拟页面加载过程
        const loadingSteps = [
            { text: '正在初始化系统...', delay: 500 },
            { text: '加载用户数据...', delay: 1000 },
            { text: '初始化AI模型...', delay: 1500 },
            { text: '准备就绪！', delay: 2000 }
        ];
        
        // 依次显示加载步骤
        loadingSteps.forEach((step, index) => {
            setTimeout(() => {
                if (text) {
                    text.textContent = step.text;
                }
            }, step.delay);
        });
        
        // 页面加载完成后隐藏过渡动画
        setTimeout(() => {
            overlay.style.transition = 'opacity 0.8s ease, visibility 0.8s ease, transform 0.8s ease';
            overlay.style.opacity = '0';
            overlay.style.visibility = 'hidden';
            overlay.style.transform = 'scale(1.1)';
        }, 2500);
    }
}

// 添加页面元素依次显示动画
function initElementRevealAnimations() {
    const elementsToAnimate = [
        '.dashboard-header',
        '.sidebar',
        '.content-header',
        '.dashboard-stats',
        '.dashboard-section'
    ];
    
    // 为每个元素添加延迟显示动画
    elementsToAnimate.forEach((selector, index) => {
        const element = document.querySelector(selector);
        if (element) {
            element.style.opacity = '0';
            element.style.transform = 'translateY(20px)';
            
            // 延迟执行动画，营造依次显示效果
            setTimeout(() => {
                element.style.transition = 'opacity 0.6s ease, transform 0.6s ease';
                element.style.opacity = '1';
                element.style.transform = 'translateY(0)';
            }, 2800 + (index * 200));
        }
    });
}

// 添加菜单交互效果 - 增强版
function initMenuInteractions() {
    const menuItems = document.querySelectorAll('.menu-item a');
    
    menuItems.forEach(item => {
        // 初始状态
        item.style.opacity = '0';
        item.style.transform = 'translateX(-20px)';
        
        // 依次显示菜单项
        setTimeout(() => {
            item.style.transition = 'all 0.4s ease';
            item.style.opacity = '1';
            item.style.transform = 'translateX(0)';
        }, 3500 + Array.from(menuItems).indexOf(item) * 100);
        
        // 点击效果
        item.addEventListener('click', function(e) {
            // 波纹效果
            createRippleEffect(e, this);
            
            // 点击位移效果
            this.style.transform = 'translateX(15px) scale(1.05)';
            setTimeout(() => {
                this.style.transform = 'translateX(0) scale(1)';
            }, 200);
        });
        
        // 悬停效果增强
        item.addEventListener('mouseenter', function() {
            this.style.transform = 'translateX(8px)';
            this.style.boxShadow = '0 2px 8px rgba(102, 126, 234, 0.2)';
        });
        
        item.addEventListener('mouseleave', function() {
            this.style.transform = 'translateX(0)';
            this.style.boxShadow = 'none';
        });
    });
}

// 添加统计卡片动画 - 增强版
function initStatCardAnimations() {
    const statCards = document.querySelectorAll('.stat-card');
    
    // 为每个统计卡片添加动画
    statCards.forEach((card, index) => {
        card.style.opacity = '0';
        card.style.transform = 'translateY(30px) scale(0.95)';
        card.style.transition = `opacity 0.6s cubic-bezier(0.34, 1.56, 0.64, 1) ${index * 0.15}s, 
                                 transform 0.6s cubic-bezier(0.34, 1.56, 0.64, 1) ${index * 0.15}s, 
                                 box-shadow 0.3s ease ${index * 0.15}s`;
        
        // 当卡片进入视口时触发动画
        const observer = new IntersectionObserver((entries) => {
            entries.forEach(entry => {
                if (entry.isIntersecting) {
                    card.style.opacity = '1';
                    card.style.transform = 'translateY(0) scale(1)';
                    
                    // 数值增长动画
                    animateStatValues(card);
                    
                    observer.unobserve(card);
                }
            });
        }, {
            threshold: 0.1,
            rootMargin: '0px 0px -50px 0px'
        });
        
        observer.observe(card);
    });
}

// 数值增长动画
function animateStatValues(card) {
    const statValue = card.querySelector('.stat-value');
    if (statValue && !isNaN(statValue.textContent)) {
        const targetValue = parseInt(statValue.textContent);
        let currentValue = 0;
        const increment = targetValue / 50;
        const duration = 2000;
        const startTime = performance.now();
        
        function updateValue(timestamp) {
            const elapsed = timestamp - startTime;
            const progress = Math.min(elapsed / duration, 1);
            
            // 使用缓动函数
            const easedProgress = 1 - Math.pow(1 - progress, 3);
            currentValue = Math.floor(easedProgress * targetValue);
            
            statValue.textContent = currentValue;
            
            if (progress < 1) {
                requestAnimationFrame(updateValue);
            } else {
                statValue.textContent = targetValue;
            }
        }
        
        requestAnimationFrame(updateValue);
    }
}

// 添加功能卡片交互 - 增强版
function initFeatureCardInteractions() {
    const featureCards = document.querySelectorAll('.feature-card');
    
    featureCards.forEach((card, index) => {
        // 初始状态
        card.style.opacity = '0';
        card.style.transform = 'translateY(20px) scale(0.98)';
        
        // 依次显示卡片
        setTimeout(() => {
            card.style.transition = 'all 0.5s cubic-bezier(0.34, 1.56, 0.64, 1)';
            card.style.opacity = '1';
            card.style.transform = 'translateY(0) scale(1)';
        }, 4000 + (index * 100));
        
        card.addEventListener('mouseenter', function() {
            // 鼠标进入时的效果 - 增强版
            this.style.transform = 'translateY(-10px) scale(1.03)';
            this.style.boxShadow = '0 12px 30px rgba(102, 126, 234, 0.25)';
            this.style.borderColor = '#667eea';
            
            // 添加发光效果
            this.style.boxShadow = '0 12px 30px rgba(102, 126, 234, 0.25), 0 0 20px rgba(102, 126, 234, 0.1)';
        });
        
        card.addEventListener('mouseleave', function() {
            // 鼠标离开时的效果
            this.style.transform = 'translateY(0) scale(1)';
            this.style.boxShadow = '0 4px 15px rgba(0, 0, 0, 0.05)';
            this.style.borderColor = '#f0f0f0';
        });
        
        // 点击效果
        card.addEventListener('click', function(e) {
            createRippleEffect(e, this);
        });
    });
}

// 添加平滑滚动效果
function initSmoothScroll() {
    // 平滑滚动到锚点
    document.querySelectorAll('a[href^="#"]').forEach(anchor => {
        anchor.addEventListener('click', function (e) {
            e.preventDefault();
            const target = document.querySelector(this.getAttribute('href'));
            if (target) {
                target.scrollIntoView({
                    behavior: 'smooth',
                    block: 'start'
                });
            }
        });
    });
}

// 添加页面加载完成动画
function initPageLoadComplete() {
    setTimeout(() => {
        // 添加页面加载完成的庆祝效果
        createConfettiEffect();
        
        // 更新页面标题，添加通知
        const originalTitle = document.title;
        document.title = '🎉 系统已准备就绪！';
        
        setTimeout(() => {
            document.title = originalTitle;
        }, 2000);
    }, 5000);
}

// 创建波纹效果
function createRippleEffect(e, element) {
    const ripple = document.createElement('span');
    const rect = element.getBoundingClientRect();
    const size = Math.max(rect.width, rect.height);
    const x = e.clientX - rect.left - size / 2;
    const y = e.clientY - rect.top - size / 2;
    
    ripple.style.cssText = `
        position: absolute;
        width: ${size}px;
        height: ${size}px;
        left: ${x}px;
        top: ${y}px;
        background: rgba(102, 126, 234, 0.3);
        border-radius: 50%;
        transform: scale(0);
        animation: ripple 0.6s ease-out;
        pointer-events: none;
        z-index: 1000;
    `;
    
    element.style.position = 'relative';
    element.style.overflow = 'hidden';
    element.appendChild(ripple);
    
    setTimeout(() => {
        ripple.remove();
    }, 600);
}

// 创建庆祝效果（简单版）
function createConfettiEffect() {
    const colors = ['#667eea', '#764ba2', '#f093fb', '#f5576c', '#4facfe', '#00f2fe'];
    const container = document.createElement('div');
    container.style.cssText = `
        position: fixed;
        top: 0;
        left: 0;
        width: 100%;
        height: 100%;
        pointer-events: none;
        z-index: 9999;
        overflow: hidden;
    `;
    document.body.appendChild(container);
    
    // 创建50个庆祝粒子
    for (let i = 0; i < 50; i++) {
        setTimeout(() => {
            const particle = document.createElement('div');
            const size = Math.random() * 10 + 5;
            const color = colors[Math.floor(Math.random() * colors.length)];
            const left = Math.random() * 100;
            
            particle.style.cssText = `
                position: absolute;
                width: ${size}px;
                height: ${size}px;
                background: ${color};
                border-radius: ${Math.random() > 0.5 ? '50%' : '0'};
                left: ${left}%;
                top: -20px;
                opacity: 0.8;
                transform: scale(0);
                animation: confettiFall ${Math.random() * 3 + 2}s ease-in forwards;
            `;
            
            container.appendChild(particle);
            
            // 移除粒子
            setTimeout(() => {
                particle.remove();
            }, 5000);
        }, i * 50);
    }
    
    // 移除容器
    setTimeout(() => {
        container.remove();
    }, 6000);
}

// 添加CSS动画关键帧
function addAnimationKeyframes() {
    const style = document.createElement('style');
    style.textContent = `
        /* 增强的动画关键帧 */
        @keyframes spin {
            to {
                transform: rotate(360deg);
            }
        }
        
        @keyframes pulse {
            0%, 100% {
                opacity: 1;
                transform: scale(1);
            }
            50% {
                opacity: 0.7;
                transform: scale(1.1);
            }
        }
        
        @keyframes fadeInOut {
            0%, 100% {
                opacity: 0.6;
            }
            50% {
                opacity: 1;
            }
        }
        
        @keyframes ripple {
            to {
                transform: scale(4);
                opacity: 0;
            }
        }
        
        @keyframes confettiFall {
            0% {
                transform: translateY(-20px) rotate(0deg) scale(0);
                opacity: 0;
            }
            10% {
                transform: translateY(0) rotate(180deg) scale(1);
                opacity: 1;
            }
            100% {
                transform: translateY(100vh) rotate(720deg) scale(1);
                opacity: 0;
            }
        }
    `;
    document.head.appendChild(style);
}

// 添加动画样式
addAnimationKeyframes();

// 页面加载完成后初始化仪表盘功能
document.addEventListener('DOMContentLoaded', initDashboard);