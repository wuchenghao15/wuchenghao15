/**
 * MTSCOS AI System - 动态Title管理器
 * 版本: 4.4.0
 * 描述: 提供多种动态Title效果，提升页面视觉效果
 */

class DynamicTitleManager {
    constructor() {
        this.defaultTitle = 'MTSCOS AI';
        this.isActive = false;
        this.currentIndex = 0;
        this.animationId = null;
        this.titles = [
            'MTSCOS AI - 智能管理系统',
            'MTSCOS AI - 登录',
            'MTSCOS AI - 欢迎回来',
            'MTSCOS AI - 科技赋能未来',
            'MTSCOS AI - 智能助手',
            'MTSCOS AI - 登录中...',
            'MTSCOS AI - 正在加载...'
        ];
        this.typewriterSpeed = 100;
        this.cycleInterval = 3000;
        this.cycleTimer = null;
    }

    // 初始化
    init(options = {}) {
        this.defaultTitle = options.defaultTitle || 'MTSCOS AI';
        this.titles = options.titles || this.titles;
        this.typewriterSpeed = options.typewriterSpeed || 100;
        this.cycleInterval = options.cycleInterval || 3000;
        
        // 监听页面状态变化
        this.setupEventListeners();
        
        return this;
    }

    // 事件监听
    setupEventListeners() {
        // 登录成功
        document.addEventListener('mtscos:login:success', () => {
            this.showMessage('登录成功，欢迎回来！');
        });
        
        // 登出
        document.addEventListener('mtscos:logout', () => {
            this.showMessage('已安全退出');
        });
        
        // 加载状态
        document.addEventListener('mtscos:loading:start', () => {
            this.showMessage('正在加载...');
        });
        
        document.addEventListener('mtscos:loading:end', () => {
            this.showMessage('加载完成');
            setTimeout(() => this.stopSpecial(), 2000);
        });
        
        // 错误状态
        document.addEventListener('mtscos:error', (e) => {
            this.showMessage(`错误: ${e.detail?.message || '未知错误'}`);
        });
        
        // 页面可见性变化
        document.addEventListener('visibilitychange', () => {
            if (document.hidden) {
                this.pauseCycle();
            } else {
                this.resumeCycle();
            }
        });
    }

    // ==================== 特效模式 ====================

    // 打字机效果
    startTypewriter(title = null) {
        this.stopAll();
        const text = title || this.defaultTitle;
        let index = 0;
        
        const animate = () => {
            document.title = text.substring(0, index);
            index++;
            
            if (index <= text.length) {
                this.animationId = setTimeout(animate, this.typewriterSpeed);
            } else {
                document.title = text;
            }
        };
        
        animate();
    }

    // 光标闪烁
    blinkCursor(text) {
        let showCursor = true;
        this.animationId = setInterval(() => {
            document.title = showCursor ? text + '▌' : text;
            showCursor = !showCursor;
        }, 500);
    }

    // 循环切换标题
    startCycle() {
        this.stopAll();
        this.isActive = true;
        
        const updateTitle = () => {
            this.currentIndex = (this.currentIndex + 1) % this.titles.length;
            const title = this.titles[this.currentIndex];
            
            // 淡入效果
            this.fadeInTitle(title);
        };
        
        this.cycleTimer = setInterval(updateTitle, this.cycleInterval);
        updateTitle();
    }

    // 淡入效果
    fadeInTitle(title) {
        let opacity = 0;
        const fadeIn = () => {
            opacity += 0.1;
            document.title = title;
            
            if (opacity < 1) {
                requestAnimationFrame(fadeIn);
            }
        };
        fadeIn();
    }

    // 闪烁效果
    startBlink(title = null) {
        this.stopAll();
        const text = title || this.defaultTitle;
        let show = true;
        
        this.animationId = setInterval(() => {
            document.title = show ? text : '● '.repeat(3) + text;
            show = !show;
        }, 800);
    }

    // 滚动字幕效果
    startMarquee(title = null) {
        this.stopAll();
        const text = (title || this.defaultTitle) + ' ★ ';
        let position = 0;
        
        const scroll = () => {
            position++;
            if (position >= text.length) position = 0;
            
            const display = text.substring(position) + text.substring(0, position);
            document.title = display;
            this.animationId = setTimeout(scroll, 200);
        };
        
        scroll();
    }

    // 渐变切换
    startGradientCycle() {
        this.stopAll();
        let hue = 0;
        
        const update = () => {
            hue = (hue + 1) % 360;
            const title = `MTSCOS AI \u2728 ${this.getGradientText(hue)}`;
            document.title = title;
            this.animationId = setTimeout(update, 100);
        };
        
        update();
    }

    getGradientText(hue) {
        return ['智能', '未来', '科技', '创新'][Math.floor(hue / 90) % 4];
    }

    // 特殊消息显示
    showMessage(message) {
        this.stopAll();
        let dots = '';
        
        const animate = () => {
            dots = dots.length < 3 ? dots + '.' : '';
            document.title = `${message}${dots}`;
            this.animationId = setTimeout(animate, 400);
        };
        
        animate();
    }

    // ==================== 控制方法 ====================

    // 停止所有动画
    stopAll() {
        if (this.animationId) {
            clearTimeout(this.animationId);
            clearInterval(this.animationId);
            this.animationId = null;
        }
        if (this.cycleTimer) {
            clearInterval(this.cycleTimer);
            this.cycleTimer = null;
        }
        this.isActive = false;
    }

    // 停止特殊效果，恢复默认
    stopSpecial() {
        this.stopAll();
        document.title = this.defaultTitle;
    }

    // 暂停循环
    pauseCycle() {
        if (this.cycleTimer) {
            clearInterval(this.cycleTimer);
            this.cycleTimer = null;
        }
    }

    // 恢复循环
    resumeCycle() {
        if (this.isActive && !this.cycleTimer) {
            this.startCycle();
        }
    }

    // 设置默认标题
    setDefault(title) {
        this.defaultTitle = title;
        document.title = title;
    }

    // 添加自定义标题
    addTitle(title) {
        if (!this.titles.includes(title)) {
            this.titles.push(title);
        }
    }

    // 移除标题
    removeTitle(title) {
        const index = this.titles.indexOf(title);
        if (index > -1) {
            this.titles.splice(index, 1);
        }
    }

    // ==================== 预设效果 ====================

    // 登录页效果
    loginMode() {
        this.init({
            titles: [
                'MTSCOS AI - 登录',
                'MTSCOS AI - 验证中...',
                'MTSCOS AI - 欢迎使用'
            ],
            cycleInterval: 2500
        });
        this.startCycle();
    }

    // 加载效果
    loadingMode() {
        this.startTypewriter('MTSCOS AI - 正在加载...');
    }

    // 成功效果
    successMode() {
        this.showMessage('操作成功 ✓');
        setTimeout(() => this.stopSpecial(), 3000);
    }

    // 错误效果
    errorMode(message = '发生错误') {
        this.stopAll();
        let flash = 0;
        const originalTitle = document.title;
        
        this.animationId = setInterval(() => {
            flash++;
            document.title = flash % 2 === 0 ? `⚠️ ${message}` : originalTitle;
            
            if (flash >= 6) {
                clearInterval(this.animationId);
                document.title = originalTitle;
            }
        }, 500);
    }

    // 通知效果
    notificationMode(message) {
        this.stopAll();
        
        // 先保存原标题
        const originalTitle = this.defaultTitle;
        
        // 显示通知
        this.showMessage(message);
        
        // 3秒后恢复
        setTimeout(() => {
            this.stopSpecial();
        }, 3000);
    }
}

// 创建全局实例
window.dynamicTitle = new DynamicTitleManager();

// 页面加载完成后自动初始化
document.addEventListener('DOMContentLoaded', () => {
    // 默认使用打字机效果
    setTimeout(() => {
        window.dynamicTitle.init();
        window.dynamicTitle.startTypewriter();
    }, 1000);
});
