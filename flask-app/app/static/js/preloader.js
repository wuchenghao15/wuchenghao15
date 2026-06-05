/**
 * MTSCOS AI 预加载动画控制器
 * 负责管理页面加载时的预加载动画效果
 */

class Preloader {
    constructor(options = {}) {
        this.options = {
            minDuration: 2000,        // 最小显示时间（毫秒）
            fadeOutDuration: 500,     // 淡出动画时间
            progressUpdateInterval: 50, // 进度更新间隔
            autoStart: true,          // 是否自动启动
            ...options
        };
        
        this.progress = 0;
        this.isComplete = false;
        this.startTime = null;
        this.progressInterval = null;
        this.loadingStatus = [
            '初始化系统',
            '加载核心模块',
            '连接AI引擎',
            '同步数据',
            '准备界面',
            '即将完成'
        ];
        
        this.init();
    }
    
    init() {
        this.createPreloaderElement();
        this.createParticles();
        
        if (this.options.autoStart) {
            this.start();
        }
        
        // 监听页面加载事件
        window.addEventListener('load', () => this.onPageLoad());
        
        // 监听DOMContentLoaded事件
        if (document.readyState === 'loading') {
            document.addEventListener('DOMContentLoaded', () => this.onDOMReady());
        } else {
            this.onDOMReady();
        }
    }
    
    createPreloaderElement() {
        // 检查是否已存在预加载器
        if (document.getElementById('preloader')) {
            return;
        }
        
        const preloader = document.createElement('div');
        preloader.id = 'preloader';
        preloader.innerHTML = `
            <div class="preloader-particles"></div>
            <div class="preloader-ring"></div>
            <div class="preloader-logo">
                <svg viewBox="0 0 200 200" xmlns="http://www.w3.org/2000/svg">
                    <defs>
                        <linearGradient id="logoGradient" x1="0%" y1="0%" x2="100%" y2="100%">
                            <stop offset="0%" style="stop-color:#667eea;stop-opacity:1" />
                            <stop offset="50%" style="stop-color:#764ba2;stop-opacity:1" />
                            <stop offset="100%" style="stop-color:#f093fb;stop-opacity:1" />
                        </linearGradient>
                        <linearGradient id="brainGradient" x1="0%" y1="0%" x2="100%" y2="100%">
                            <stop offset="0%" style="stop-color:#4facfe;stop-opacity:1" />
                            <stop offset="100%" style="stop-color:#00f2fe;stop-opacity:1" />
                        </linearGradient>
                    </defs>
                    <circle cx="100" cy="100" r="90" fill="url(#logoGradient)" opacity="0.1"/>
                    <circle cx="100" cy="100" r="85" fill="none" stroke="url(#logoGradient)" stroke-width="2" opacity="0.3"/>
                    <g transform="translate(100, 100)">
                        <path d="M-35,-20 C-45,-30 -50,-10 -45,5 C-50,20 -40,35 -25,40 C-15,45 -5,40 0,35 L0,-25 C-10,-25 -25,-25 -35,-20 Z" 
                              fill="url(#brainGradient)" opacity="0.9"/>
                        <path d="M35,-20 C45,-30 50,-10 45,5 C50,20 40,35 25,40 C15,45 5,40 0,35 L0,-25 C10,-25 25,-25 35,-20 Z" 
                              fill="url(#brainGradient)" opacity="0.9"/>
                        <circle cx="-20" cy="-10" r="3" fill="#fff" opacity="0.8"/>
                        <circle cx="20" cy="-10" r="3" fill="#fff" opacity="0.8"/>
                        <circle cx="-15" cy="10" r="3" fill="#fff" opacity="0.8"/>
                        <circle cx="15" cy="10" r="3" fill="#fff" opacity="0.8"/>
                        <circle cx="0" cy="20" r="3" fill="#fff" opacity="0.8"/>
                        <line x1="-20" y1="-10" x2="20" y2="-10" stroke="#fff" stroke-width="1" opacity="0.5"/>
                        <line x1="-20" y1="-10" x2="-15" y2="10" stroke="#fff" stroke-width="1" opacity="0.5"/>
                        <line x1="20" y1="-10" x2="15" y2="10" stroke="#fff" stroke-width="1" opacity="0.5"/>
                        <line x1="-15" y1="10" x2="0" y2="20" stroke="#fff" stroke-width="1" opacity="0.5"/>
                        <line x1="15" y1="10" x2="0" y2="20" stroke="#fff" stroke-width="1" opacity="0.5"/>
                    </g>
                    <text x="100" y="145" font-family="Arial, sans-serif" font-size="28" font-weight="bold" 
                          text-anchor="middle" fill="url(#logoGradient)">MT</text>
                    <circle cx="100" cy="100" r="95" fill="none" stroke="url(#logoGradient)" stroke-width="1" opacity="0.2" stroke-dasharray="10,5"/>
                </svg>
            </div>
            <div class="preloader-text">
                <div class="preloader-title">MTSCOS AI</div>
                <div class="preloader-subtitle">智能考试系统</div>
            </div>
            <div class="preloader-progress-container">
                <div class="preloader-progress-bar" id="preloader-progress"></div>
            </div>
            <div class="preloader-percentage" id="preloader-percentage">0%</div>
            <div class="preloader-status" id="preloader-status">正在初始化</div>
        `;
        
        document.body.insertBefore(preloader, document.body.firstChild);
        
        // 添加样式
        this.addStyles();
    }
    
    addStyles() {
        if (document.getElementById('preloader-styles')) {
            return;
        }
        
        const link = document.createElement('link');
        link.id = 'preloader-styles';
        link.rel = 'stylesheet';
        link.href = '/static/css/preloader.css';
        document.head.appendChild(link);
    }
    
    createParticles() {
        const container = document.querySelector('.preloader-particles');
        if (!container) return;
        
        for (let i = 0; i < 20; i++) {
            const particle = document.createElement('div');
            particle.className = 'particle';
            particle.style.left = Math.random() * 100 + '%';
            particle.style.top = Math.random() * 100 + '%';
            particle.style.animationDelay = Math.random() * 3 + 's';
            particle.style.animationDuration = (2 + Math.random() * 2) + 's';
            container.appendChild(particle);
        }
    }
    
    start() {
        this.startTime = Date.now();
        this.progress = 0;
        this.isComplete = false;
        
        // 启动进度更新
        this.progressInterval = setInterval(() => {
            this.updateProgress();
        }, this.options.progressUpdateInterval);
    }
    
    updateProgress() {
        if (this.isComplete) return;
        
        const elapsed = Date.now() - this.startTime;
        const minDuration = this.options.minDuration;
        
        // 计算基础进度
        let targetProgress = Math.min((elapsed / minDuration) * 100, 95);
        
        // 添加一些随机波动，使进度看起来更自然
        if (this.progress < targetProgress) {
            const increment = Math.random() * 2 + 0.5;
            this.progress = Math.min(this.progress + increment, targetProgress);
        }
        
        // 更新UI
        this.updateUI();
        
        // 检查是否可以完成
        if (this.progress >= 95 && this.pageLoaded && elapsed >= minDuration) {
            this.complete();
        }
    }
    
    updateUI() {
        const progressBar = document.getElementById('preloader-progress');
        const percentage = document.getElementById('preloader-percentage');
        const status = document.getElementById('preloader-status');
        
        if (progressBar) {
            progressBar.style.width = this.progress + '%';
        }
        
        if (percentage) {
            percentage.textContent = Math.floor(this.progress) + '%';
        }
        
        if (status) {
            const statusIndex = Math.min(
                Math.floor((this.progress / 100) * this.loadingStatus.length),
                this.loadingStatus.length - 1
            );
            status.textContent = this.loadingStatus[statusIndex];
        }
    }
    
    onDOMReady() {
        this.domReady = true;
        this.checkComplete();
    }
    
    onPageLoad() {
        this.pageLoaded = true;
        this.checkComplete();
    }
    
    checkComplete() {
        if (this.domReady && this.pageLoaded) {
            const elapsed = Date.now() - this.startTime;
            const remainingTime = Math.max(0, this.options.minDuration - elapsed);
            
            // 如果已经达到最小显示时间，立即完成
            if (remainingTime <= 0) {
                this.complete();
            }
        }
    }
    
    complete() {
        if (this.isComplete) return;
        
        this.isComplete = true;
        this.progress = 100;
        this.updateUI();
        
        // 清除进度更新定时器
        if (this.progressInterval) {
            clearInterval(this.progressInterval);
            this.progressInterval = null;
        }
        
        // 添加完成动画
        const preloader = document.getElementById('preloader');
        if (preloader) {
            preloader.classList.add('preloader-complete');
        }
        
        // 延迟后隐藏预加载器
        setTimeout(() => {
            this.hide();
        }, 500);
    }
    
    hide() {
        const preloader = document.getElementById('preloader');
        if (preloader) {
            preloader.classList.add('hidden');
            
            // 动画结束后移除元素
            setTimeout(() => {
                if (preloader.parentNode) {
                    preloader.parentNode.removeChild(preloader);
                }
                
                // 触发自定义事件
                window.dispatchEvent(new CustomEvent('preloaderComplete'));
            }, this.options.fadeOutDuration);
        }
    }
    
    // 手动设置进度
    setProgress(value) {
        this.progress = Math.min(Math.max(value, 0), 100);
        this.updateUI();
    }
    
    // 手动设置状态文字
    setStatus(text) {
        const status = document.getElementById('preloader-status');
        if (status) {
            status.textContent = text;
        }
    }
}

// 自动初始化预加载器
document.addEventListener('DOMContentLoaded', () => {
    // 检查是否已经存在预加载器实例
    if (!window.preloader) {
        window.preloader = new Preloader();
    }
});

// 导出类，以便其他脚本可以使用
if (typeof module !== 'undefined' && module.exports) {
    module.exports = Preloader;
}