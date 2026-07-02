class LayoutAdapter {
    constructor() {
        this.observers = [];
        this.resizeTimeout = null;
        this.layoutHistory = [];
        this.maxHistory = 10;
        this.isAdapting = false;
        
        this.init();
    }
    
    init() {
        this.setupResizeObserver();
        this.setupMutationObserver();
        this.setupLayoutWatcher();
        this.setupKeyboardShortcuts();
        this.setupOrientationChange();
        
        console.log('LayoutAdapter initialized - AI-powered responsive layout management');
    }
    
    setupResizeObserver() {
        window.addEventListener('resize', () => {
            if (this.resizeTimeout) {
                clearTimeout(this.resizeTimeout);
            }
            
            this.resizeTimeout = setTimeout(() => {
                this.handleResize();
            }, 100);
        });
    }
    
    setupMutationObserver() {
        const observer = new MutationObserver((mutations) => {
            mutations.forEach((mutation) => {
                if (mutation.type === 'childList' || mutation.type === 'attributes') {
                    this.checkAndFixLayout();
                }
            });
        });
        
        observer.observe(document.body, {
            childList: true,
            attributes: true,
            subtree: true,
            attributeFilter: ['style', 'class']
        });
        
        this.observers.push(observer);
    }
    
    setupLayoutWatcher() {
        this.layoutWatcher = setInterval(() => {
            if (!this.isAdapting) {
                this.checkAndFixLayout();
            }
        }, 2000);
    }
    
    setupKeyboardShortcuts() {
        window.addEventListener('keydown', (e) => {
            if ((e.metaKey || e.ctrlKey) && e.key === 'r') {
                e.preventDefault();
                this.resetLayout();
            }
            
            if (e.key === 'Escape') {
                this.closeOverlays();
            }
        });
    }
    
    setupOrientationChange() {
        window.addEventListener('orientationchange', () => {
            setTimeout(() => {
                this.handleResize();
                this.checkAndFixLayout();
            }, 500);
        });
    }
    
    handleResize() {
        const viewportWidth = window.innerWidth;
        const viewportHeight = window.innerHeight;
        
        this.updateLayoutState(viewportWidth, viewportHeight);
        this.adjustGridColumns(viewportWidth);
        this.adjustFontSizes(viewportWidth);
        this.adjustSpacing(viewportWidth);
        this.checkOverflow();
    }
    
    updateLayoutState(width, height) {
        const state = {
            width,
            height,
            ratio: width / height,
            orientation: width >= height ? 'landscape' : 'portrait',
            breakpoint: this.getBreakpoint(width),
            timestamp: Date.now()
        };
        
        this.layoutHistory.push(state);
        if (this.layoutHistory.length > this.maxHistory) {
            this.layoutHistory.shift();
        }
        
        document.documentElement.setAttribute('data-layout-width', width);
        document.documentElement.setAttribute('data-layout-height', height);
        document.documentElement.setAttribute('data-layout-orientation', state.orientation);
        document.documentElement.setAttribute('data-layout-breakpoint', state.breakpoint);
    }
    
    getBreakpoint(width) {
        if (width >= 1920) return 'xl';
        if (width >= 1600) return 'lg';
        if (width >= 1200) return 'md';
        if (width >= 992) return 'sm-lg';
        if (width >= 768) return 'sm';
        if (width >= 576) return 'xs';
        return 'xxs';
    }
    
    adjustGridColumns(width) {
        const grids = document.querySelectorAll('.grid-auto-adaptive, .grid-auto-responsive');
        
        grids.forEach((grid) => {
            let columns = 1;
            
            if (width >= 1920) columns = 4;
            else if (width >= 1600) columns = 4;
            else if (width >= 1200) columns = 3;
            else if (width >= 992) columns = 3;
            else if (width >= 768) columns = 2;
            else columns = 1;
            
            grid.style.gridTemplateColumns = `repeat(auto-fit, minmax(min(${Math.min(350, width / columns)}px, 100%), 1fr))`;
        });
    }
    
    adjustFontSizes(width) {
        const baseSize = Math.max(12, Math.min(22, width / 80));
        document.documentElement.style.fontSize = `${baseSize}px`;
        
        const titles = document.querySelectorAll('.title-adaptive');
        titles.forEach((title) => {
            const size = Math.max(24, Math.min(48, width / 30));
            title.style.fontSize = `${size}px`;
        });
        
        const subtitles = document.querySelectorAll('.subtitle-adaptive');
        subtitles.forEach((subtitle) => {
            const size = Math.max(18, Math.min(32, width / 45));
            subtitle.style.fontSize = `${size}px`;
        });
    }
    
    adjustSpacing(width) {
        const spacing = Math.max(8, Math.min(24, width / 50));
        
        const cards = document.querySelectorAll('.card-adaptive');
        cards.forEach((card) => {
            card.style.padding = `${spacing * 1.5}px`;
        });
        
        const buttons = document.querySelectorAll('.btn-adaptive');
        buttons.forEach((btn) => {
            btn.style.padding = `${spacing}px ${spacing * 1.5}px`;
        });
    }
    
    checkOverflow() {
        const overflowingElements = [];
        
        document.querySelectorAll('body *').forEach((el) => {
            const rect = el.getBoundingClientRect();
            const parentRect = el.parentElement?.getBoundingClientRect();
            
            if (parentRect) {
                if (rect.width > parentRect.width + 10 || rect.height > parentRect.height + 10) {
                    overflowingElements.push(el);
                }
            }
        });
        
        if (overflowingElements.length > 0) {
            this.fixOverflow(overflowingElements);
        }
    }
    
    fixOverflow(elements) {
        elements.forEach((el) => {
            const styles = window.getComputedStyle(el);
            
            if (styles.overflow !== 'hidden') {
                el.style.overflow = 'hidden';
                el.style.textOverflow = 'ellipsis';
                el.style.whiteSpace = 'nowrap';
            }
            
            if (styles.width === 'auto') {
                el.style.maxWidth = '100%';
            }
            
            const img = el.querySelector('img');
            if (img) {
                img.style.maxWidth = '100%';
                img.style.height = 'auto';
            }
        });
    }
    
    checkAndFixLayout() {
        this.isAdapting = true;
        
        try {
            this.checkGridLayouts();
            this.checkFlexLayouts();
            this.checkCardLayouts();
            this.checkModalLayouts();
            this.checkNavigationLayouts();
        } catch (error) {
            console.error('Layout check error:', error);
        }
        
        this.isAdapting = false;
    }
    
    checkGridLayouts() {
        const grids = document.querySelectorAll('.grid');
        
        grids.forEach((grid) => {
            const gridItems = grid.children;
            if (gridItems.length === 0) return;
            
            const itemWidth = gridItems[0].getBoundingClientRect().width;
            const gridWidth = grid.getBoundingClientRect().width;
            
            if (itemWidth > gridWidth) {
                grid.style.gridTemplateColumns = '1fr';
            }
        });
    }
    
    checkFlexLayouts() {
        const flexContainers = document.querySelectorAll('.flex');
        
        flexContainers.forEach((container) => {
            const containerWidth = container.getBoundingClientRect().width;
            let totalWidth = 0;
            
            Array.from(container.children).forEach((child) => {
                totalWidth += child.getBoundingClientRect().width;
            });
            
            if (totalWidth > containerWidth * 1.2) {
                container.style.flexWrap = 'wrap';
            }
        });
    }
    
    checkCardLayouts() {
        const cards = document.querySelectorAll('.glass-card, .card-adaptive');
        
        cards.forEach((card) => {
            const rect = card.getBoundingClientRect();
            
            if (rect.width < 200) {
                card.style.minWidth = '200px';
            }
            
            if (rect.height > window.innerHeight * 0.8) {
                card.style.maxHeight = `${window.innerHeight * 0.7}px`;
                card.style.overflowY = 'auto';
            }
        });
    }
    
    checkModalLayouts() {
        const modals = document.querySelectorAll('.modal, [role="dialog"]');
        
        modals.forEach((modal) => {
            const rect = modal.getBoundingClientRect();
            
            if (rect.width > window.innerWidth * 0.9) {
                modal.style.maxWidth = '90vw';
            }
            
            if (rect.height > window.innerHeight * 0.9) {
                modal.style.maxHeight = '90vh';
                modal.style.overflowY = 'auto';
            }
        });
    }
    
    checkNavigationLayouts() {
        const navs = document.querySelectorAll('nav, header');
        
        navs.forEach((nav) => {
            const rect = nav.getBoundingClientRect();
            
            if (rect.height > 100) {
                nav.style.flexWrap = 'wrap';
            }
        });
    }
    
    resetLayout() {
        document.documentElement.removeAttribute('style');
        
        document.querySelectorAll('.grid-auto-adaptive, .grid-auto-responsive').forEach((grid) => {
            grid.style.gridTemplateColumns = '';
        });
        
        document.querySelectorAll('.title-adaptive, .subtitle-adaptive').forEach((el) => {
            el.style.fontSize = '';
        });
        
        document.querySelectorAll('.card-adaptive').forEach((card) => {
            card.style.padding = '';
        });
        
        document.querySelectorAll('.btn-adaptive').forEach((btn) => {
            btn.style.padding = '';
        });
        
        this.handleResize();
        console.log('Layout reset to default');
    }
    
    closeOverlays() {
        document.querySelectorAll('.modal, .toast, .dropdown').forEach((el) => {
            el.style.display = 'none';
        });
    }
    
    getLayoutState() {
        return {
            current: this.layoutHistory[this.layoutHistory.length - 1],
            history: this.layoutHistory,
            adapting: this.isAdapting
        };
    }
    
    optimizePerformance() {
        const lazyImages = document.querySelectorAll('img[data-src]');
        
        const lazyLoadObserver = new IntersectionObserver((entries) => {
            entries.forEach((entry) => {
                if (entry.isIntersecting) {
                    const img = entry.target;
                    img.src = img.dataset.src;
                    img.removeAttribute('data-src');
                    lazyLoadObserver.unobserve(img);
                }
            });
        });
        
        lazyImages.forEach((img) => {
            lazyLoadObserver.observe(img);
        });
    }
    
    destroy() {
        this.observers.forEach((observer) => observer.disconnect());
        clearInterval(this.layoutWatcher);
        clearTimeout(this.resizeTimeout);
        window.removeEventListener('resize', this.handleResize);
        window.removeEventListener('keydown', this.setupKeyboardShortcuts);
        window.removeEventListener('orientationchange', this.setupOrientationChange);
        
        console.log('LayoutAdapter destroyed');
    }
}

document.addEventListener('DOMContentLoaded', () => {
    window.layoutAdapter = new LayoutAdapter();
    window.layoutAdapter.optimizePerformance();
});

if (typeof module !== 'undefined' && module.exports) {
    module.exports = LayoutAdapter;
}