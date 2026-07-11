// 移动端交互优化 - v2.0 增强版
class MobileInteractions {
    constructor() {
        this.init();
        this.touchStartX = 0;
        this.touchStartY = 0;
        this.touchEndX = 0;
        this.touchEndY = 0;
        this.isDragging = false;
        this.startTime = 0;
        this.endTime = 0;
        this.menuOpen = false;
        this.swipeThreshold = 50;
        this.longPressThreshold = 500;
    }
    
    init() {
        this.setupTouchEvents();
        this.setupGestureEvents();
        this.setupMobileOptimizations();
        this.setupDrawerMenu();
        this.setupBottomNav();
        this.setupTouchFeedback();
    }
    
    setupTouchEvents() {
        // 添加触摸事件监听器
        document.addEventListener('touchstart', (e) => this.handleTouchStart(e), { passive: true });
        document.addEventListener('touchend', (e) => this.handleTouchEnd(e), { passive: true });
        document.addEventListener('touchmove', (e) => this.handleTouchMove(e), { passive: true });
        document.addEventListener('touchcancel', (e) => this.handleTouchCancel(e), { passive: true });
    }
    
    setupGestureEvents() {
        // 添加手势事件监听器
        document.addEventListener('gesturestart', (e) => this.handleGestureStart(e), { passive: true });
        document.addEventListener('gesturechange', (e) => this.handleGestureChange(e), { passive: true });
        document.addEventListener('gestureend', (e) => this.handleGestureEnd(e), { passive: true });
    }
    
    setupMobileOptimizations() {
        // 禁止双击缩放
        document.addEventListener('dblclick', (e) => {
            if (this.isMobile()) {
                e.preventDefault();
            }
        });
        
        // 优化移动端滚动
        this.optimizeScroll();
        
        // 优化表单输入
        this.optimizeFormInputs();
    }
    
    handleTouchStart(e) {
        // 记录触摸开始位置和时间
        this.touchStartX = e.touches[0].clientX;
        this.touchStartY = e.touches[0].clientY;
        this.startTime = Date.now();
        this.isDragging = false;
    }
    
    handleTouchEnd(e) {
        // 记录触摸结束位置和时间
        this.touchEndX = e.changedTouches[0].clientX;
        this.touchEndY = e.changedTouches[0].clientY;
        this.endTime = Date.now();
        
        // 计算触摸持续时间
        const touchDuration = this.endTime - this.startTime;
        
        // 检测手势类型
        this.detectGesture(touchDuration);
        
        this.isDragging = false;
    }
    
    handleTouchMove(e) {
        // 检测是否正在拖动
        this.isDragging = true;
    }
    
    handleTouchCancel(e) {
        // 触摸取消事件处理
        this.isDragging = false;
    }
    
    handleGestureStart(e) {
        // 手势开始事件处理
        e.preventDefault();
    }
    
    handleGestureChange(e) {
        // 手势变化事件处理
        e.preventDefault();
    }
    
    handleGestureEnd(e) {
        // 手势结束事件处理
        e.preventDefault();
    }
    
    detectGesture(duration) {
        // 计算水平和垂直移动距离
        const deltaX = this.touchEndX - this.touchStartX;
        const deltaY = this.touchEndY - this.touchStartY;
        
        // 计算移动距离的绝对值
        const absDeltaX = Math.abs(deltaX);
        const absDeltaY = Math.abs(deltaY);
        
        // 检测点击事件（短时间、小距离移动）
        if (duration < 200 && absDeltaX < 10 && absDeltaY < 10) {
            this.handleTap();
            return;
        }
        
        // 检测长按事件（长时间、小距离移动）
        if (duration > 500 && absDeltaX < 10 && absDeltaY < 10) {
            this.handleLongPress();
            return;
        }
        
        // 检测滑动事件（大距离移动）
        if (absDeltaX > 50 || absDeltaY > 50) {
            // 检测滑动方向
            if (absDeltaX > absDeltaY) {
                // 水平滑动
                if (deltaX > 0) {
                    this.handleSwipeRight();
                } else {
                    this.handleSwipeLeft();
                }
            } else {
                // 垂直滑动
                if (deltaY > 0) {
                    this.handleSwipeDown();
                } else {
                    this.handleSwipeUp();
                }
            }
        }
    }
    
    handleTap() {
        // 点击事件处理
        console.log('Tap detected');
    }
    
    handleLongPress() {
        // 长按事件处理
        console.log('Long press detected');
    }
    
    handleSwipeLeft() {
        // 向左滑动事件处理
        console.log('Swipe left detected');
        // 可以用于导航到下一页或显示侧边菜单
    }
    
    handleSwipeRight() {
        // 向右滑动事件处理
        console.log('Swipe right detected');
        // 可以用于导航到上一页或隐藏侧边菜单
    }
    
    handleSwipeUp() {
        // 向上滑动事件处理
        console.log('Swipe up detected');
        // 可以用于显示更多内容或隐藏底部菜单
    }
    
    handleSwipeDown() {
        // 向下滑动事件处理
        console.log('Swipe down detected');
        // 可以用于刷新页面或显示顶部菜单
    }
    
    optimizeScroll() {
        // 优化移动端滚动性能
        document.addEventListener('touchmove', (e) => {
            // 可以添加滚动优化逻辑
        }, { passive: true });
    }
    
    optimizeFormInputs() {
        // 优化移动端表单输入
        const inputs = document.querySelectorAll('input, select, textarea');
        inputs.forEach(input => {
            // 优化输入焦点
            input.addEventListener('focus', () => {
                // 可以添加输入焦点优化逻辑
            });
            
            // 优化输入模糊
            input.addEventListener('blur', () => {
                // 可以添加输入模糊优化逻辑
            });
        });
    }
    
    isMobile() {
        // 检测是否为移动设备
        return /Android|webOS|iPhone|iPad|iPod|BlackBerry|IEMobile|Opera Mini/i.test(navigator.userAgent);
    }
    
    isTouchDevice() {
        return 'ontouchstart' in window || navigator.maxTouchPoints > 0 || navigator.msMaxTouchPoints > 0;
    }
    
    setupDrawerMenu() {
        const hamburger = document.querySelector('.mobile-hamburger');
        const overlay = document.querySelector('.mobile-menu-overlay');
        const drawer = document.querySelector('.mobile-drawer');
        const closeBtn = document.querySelector('.mobile-drawer-close');
        
        if (hamburger) {
            hamburger.addEventListener('click', () => {
                this.toggleDrawerMenu();
            });
        }
        
        if (overlay) {
            overlay.addEventListener('click', () => {
                this.closeDrawerMenu();
            });
        }
        
        if (closeBtn) {
            closeBtn.addEventListener('click', () => {
                this.closeDrawerMenu();
            });
        }
    }
    
    toggleDrawerMenu() {
        const overlay = document.querySelector('.mobile-menu-overlay');
        const drawer = document.querySelector('.mobile-drawer');
        const hamburger = document.querySelector('.mobile-hamburger');
        
        if (this.menuOpen) {
            this.closeDrawerMenu();
        } else {
            this.openDrawerMenu();
        }
    }
    
    openDrawerMenu() {
        const overlay = document.querySelector('.mobile-menu-overlay');
        const drawer = document.querySelector('.mobile-drawer');
        const hamburger = document.querySelector('.mobile-hamburger');
        
        if (overlay) overlay.classList.add('active');
        if (drawer) drawer.classList.add('open');
        if (hamburger) hamburger.classList.add('active');
        
        this.menuOpen = true;
    }
    
    closeDrawerMenu() {
        const overlay = document.querySelector('.mobile-menu-overlay');
        const drawer = document.querySelector('.mobile-drawer');
        const hamburger = document.querySelector('.mobile-hamburger');
        
        if (overlay) overlay.classList.remove('active');
        if (drawer) drawer.classList.remove('open');
        if (hamburger) hamburger.classList.remove('active');
        
        this.menuOpen = false;
    }
    
    setupBottomNav() {
        const navItems = document.querySelectorAll('.mobile-bottom-nav li');
        
        navItems.forEach(item => {
            item.addEventListener('click', (e) => {
                navItems.forEach(i => i.classList.remove('active'));
                item.classList.add('active');
            });
        });
    }
    
    setupTouchFeedback() {
        const touchElements = document.querySelectorAll('.btn, .feature-card, .stat-card, .role-card, .mobile-card');
        
        touchElements.forEach(element => {
            element.addEventListener('touchstart', () => {
                element.style.transform = 'scale(0.95)';
            }, { passive: true });
            
            element.addEventListener('touchend', () => {
                element.style.transform = 'scale(1)';
            }, { passive: true });
            
            element.addEventListener('touchcancel', () => {
                element.style.transform = 'scale(1)';
            }, { passive: true });
        });
    }
    
    handleSwipeLeft() {
        console.log('Swipe left detected');
        if (this.menuOpen) {
            this.closeDrawerMenu();
        }
    }
    
    handleSwipeRight() {
        console.log('Swipe right detected');
        if (!this.menuOpen && this.isMobile()) {
            this.openDrawerMenu();
        }
    }
    
    getTouchStartX() {
        return this.touchStartX;
    }
    
    getTouchStartY() {
        return this.touchStartY;
    }
    
    getTouchEndX() {
        return this.touchEndX;
    }
    
    getTouchEndY() {
        return this.touchEndY;
    }
    
    isDragging() {
        return this.isDragging;
    }
    
    isMenuOpen() {
        return this.menuOpen;
    }
}

// 初始化移动端交互
let mobileInteractions;
if (typeof window !== 'undefined') {
    window.addEventListener('DOMContentLoaded', () => {
        mobileInteractions = new MobileInteractions();
        // 将实例暴露到全局，方便其他脚本访问
        window.mobileInteractions = mobileInteractions;
    });
}