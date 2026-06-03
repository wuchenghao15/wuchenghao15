/**
 * 主题配置
 */
module.exports = {
    // 默认主题
    defaultTheme: 'light',
    
    // 支持的主题列表
    themes: ['light', 'dark'],
    
    // 主题变量配置
    variables: {
        light: {
            primaryColor: '#165DFF',
            secondaryColor: '#F8FAFC',
            accentColor: '#36CFC9',
            textPrimary: '#1E293B',
            bgPrimary: '#FFFFFF',
            bgSecondary: '#F1F5F9'
        },
        dark: {
            primaryColor: '#14B8A6',
            secondaryColor: '#A755F7',
            accentColor: '#36CFC9',
            textPrimary: '#F1F5F9',
            bgPrimary: '#121212',
            bgSecondary: '#1E293B'
        }
    },
    
    // 主题切换按钮配置
    toggle: {
        position: 'header',
        iconSize: '1.125rem',
        color: 'var(--text-secondary)',
        hoverColor: 'var(--text-primary)',
        borderRadius: '50%',
        padding: '0.5rem'
    },
    
    // 响应式主题配置
    responsive: {
        mobile: {
            breakpoints: {
                sm: '576px',
                md: '768px',
                lg: '992px',
                xl: '1200px'
            }
        }
    },
    
    // 动画配置
    animations: {
        enable: true,
        duration: '0.3s',
        easing: 'ease'
    },
    
    // 可访问性配置
    accessibility: {
        highContrast: true,
        reducedMotion: false,
        keyboardNavigation: true
    },
    
    // 性能优化配置
    performance: {
        lazyLoad: true,
        minifyCSS: true,
        optimizeImages: true
    }
};
