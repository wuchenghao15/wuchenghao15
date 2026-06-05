class PageMonitor {
    constructor() {
        this.lastUrl = window.location.href;
        this.pageLoadTime = Date.now();
        this.navigationHistory = [];
        this.backCount = 0;
        this.backTimeWindow = 60000;
        this.backTimestamps = [];
        
        this.init();
    }
    
    init() {
        this.setupNavigationListeners();
        this.setupVisibilityListeners();
        this.setupErrorListeners();
        this.logPageLoad();
    }
    
    setupNavigationListeners() {
        const self = this;
        
        window.addEventListener('popstate', function(event) {
            const currentUrl = window.location.href;
            const navigationType = self.detectNavigationType(currentUrl);
            
            self.backTimestamps.push(Date.now());
            self.cleanupOldTimestamps();
            
            if (navigationType === 'back') {
                self.backCount++;
            }
            
            self.logNavigation(self.lastUrl, currentUrl, navigationType);
            self.lastUrl = currentUrl;
            
            self.detectBackAnomaly();
        });
        
        document.addEventListener('click', function(event) {
            const target = event.target;
            const link = target.closest('a');
            
            if (link && link.href) {
                const url = new URL(link.href);
                const currentUrl = new URL(window.location.href);
                
                if (url.pathname !== currentUrl.pathname) {
                    self.logNavigation(window.location.href, link.href, 'click');
                }
            }
        });
        
        const originalPushState = history.pushState;
        history.pushState = function(state, title, url) {
            originalPushState.apply(this, arguments);
            const newUrl = url || window.location.href;
            self.logNavigation(self.lastUrl, newUrl, 'push');
            self.lastUrl = newUrl;
        };
        
        const originalReplaceState = history.replaceState;
        history.replaceState = function(state, title, url) {
            originalReplaceState.apply(this, arguments);
            const newUrl = url || window.location.href;
            self.logNavigation(self.lastUrl, newUrl, 'replace');
            self.lastUrl = newUrl;
        };
    }
    
    detectNavigationType(currentUrl) {
        if (this.navigationHistory.length > 0) {
            const previousUrl = this.navigationHistory[this.navigationHistory.length - 1];
            if (previousUrl === currentUrl) {
                return 'back';
            }
        }
        return 'forward';
    }
    
    cleanupOldTimestamps() {
        const now = Date.now();
        this.backTimestamps = this.backTimestamps.filter(t => now - t <= this.backTimeWindow);
    }
    
    detectBackAnomaly() {
        if (this.backTimestamps.length >= 5) {
            this.reportAnomaly('excessive_back', {
                backCount: this.backTimestamps.length,
                timeWindow: this.backTimeWindow,
                timestamps: this.backTimestamps
            });
        }
    }
    
    setupVisibilityListeners() {
        document.addEventListener('visibilitychange', () => {
            if (document.hidden) {
                this.logVisibilityChange('hidden');
            } else {
                this.logVisibilityChange('visible');
            }
        });
        
        window.addEventListener('blur', () => {
            this.logVisibilityChange('blur');
        });
        
        window.addEventListener('focus', () => {
            this.logVisibilityChange('focus');
        });
    }
    
    setupErrorListeners() {
        window.addEventListener('error', (event) => {
            this.logError('javascript_error', {
                message: event.message,
                filename: event.filename,
                lineno: event.lineno,
                colno: event.colno,
                error: event.error ? event.error.stack : null
            });
        });
        
        window.addEventListener('unhandledrejection', (event) => {
            this.logError('promise_rejection', {
                reason: event.reason ? (typeof event.reason === 'string' ? event.reason : JSON.stringify(event.reason)) : null
            });
        });
    }
    
    logPageLoad() {
        const loadTime = Date.now() - this.pageLoadTime;
        
        this.sendLog({
            type: 'page_load',
            url: window.location.href,
            loadTime: loadTime,
            userAgent: navigator.userAgent,
            screenWidth: window.screen.width,
            screenHeight: window.screen.height,
            timestamp: Date.now()
        });
    }
    
    logNavigation(fromUrl, toUrl, type) {
        const navigationTime = Date.now() - this.pageLoadTime;
        
        this.navigationHistory.push(fromUrl);
        if (this.navigationHistory.length > 10) {
            this.navigationHistory.shift();
        }
        
        this.sendLog({
            type: 'page_navigation',
            from: fromUrl,
            to: toUrl,
            navigationType: type,
            navigationTime: navigationTime,
            timestamp: Date.now()
        });
    }
    
    logVisibilityChange(state) {
        this.sendLog({
            type: 'visibility_change',
            state: state,
            timestamp: Date.now()
        });
    }
    
    logError(errorType, details) {
        this.sendLog({
            type: 'error',
            errorType: errorType,
            details: details,
            url: window.location.href,
            timestamp: Date.now()
        });
    }
    
    reportAnomaly(anomalyType, details) {
        this.sendLog({
            type: 'anomaly',
            anomalyType: anomalyType,
            details: details,
            url: window.location.href,
            timestamp: Date.now()
        });
    }
    
    sendLog(data) {
        const sessionId = this.getSessionId();
        
        fetch('/api/monitor/log', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-Session-ID': sessionId
            },
            body: JSON.stringify(data),
            keepalive: true
        }).catch(() => {});
    }
    
    getSessionId() {
        const match = document.cookie.match(/session_id=([^;]+)/);
        return match ? match[1] : 'unknown';
    }
    
    getStats() {
        return {
            backCount: this.backCount,
            navigationHistory: this.navigationHistory,
            backTimestamps: this.backTimestamps,
            pageLoadTime: this.pageLoadTime
        };
    }
}

document.addEventListener('DOMContentLoaded', () => {
    window.pageMonitor = new PageMonitor();
});
