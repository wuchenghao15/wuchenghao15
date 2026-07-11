/**
 * MTSCOS AI System - 交互动效师AI员工
 * 版本: 4.4.0
 * 描述: 专注于动画效果、过渡效果、用户交互反馈和微交互设计
 */

class AnimationExpert {
    constructor() {
        this.id = 'animation-expert';
        this.name = '交互动效师';
        this.icon = 'fa-magic';
        this.color = '#a855f7';
        this.gradient = 'linear-gradient(135deg, #a855f7 0%, #9333ea 100%)';
        this.role = '交互动效专家';
        this.description = '专注于动画效果、过渡效果、用户交互反馈和微交互设计';
        this.abilities = [
            '动画设计',
            '过渡效果',
            '交互反馈',
            '微交互',
            '性能优化',
            '动画编排'
        ];
        this.status = 'active';
        this.workload = 20;
        this.efficiency = 96;
        this.presetAnimations = this.initPresetAnimations();
        this.easingFunctions = this.initEasingFunctions();
    }

    // ==================== 预设动画 ====================

    initPresetAnimations() {
        return {
            fade: {
                name: '淡入淡出',
                keyframes: `@keyframes fade {
  from { opacity: 0; }
  to { opacity: 1; }
}`,
                duration: 300,
                timing: 'ease'
            },
            slideUp: {
                name: '上滑进入',
                keyframes: `@keyframes slideUp {
  from { transform: translateY(20px); opacity: 0; }
  to { transform: translateY(0); opacity: 1; }
}`,
                duration: 400,
                timing: 'ease-out'
            },
            slideDown: {
                name: '下滑进入',
                keyframes: `@keyframes slideDown {
  from { transform: translateY(-20px); opacity: 0; }
  to { transform: translateY(0); opacity: 1; }
}`,
                duration: 400,
                timing: 'ease-out'
            },
            bounce: {
                name: '弹跳效果',
                keyframes: `@keyframes bounce {
  0%, 100% { transform: translateY(0); }
  50% { transform: translateY(-10px); }
}`,
                duration: 600,
                timing: 'ease-in-out'
            },
            pulse: {
                name: '脉冲效果',
                keyframes: `@keyframes pulse {
  0%, 100% { transform: scale(1); }
  50% { transform: scale(1.05); }
}`,
                duration: 1000,
                timing: 'ease-in-out'
            },
            spin: {
                name: '旋转加载',
                keyframes: `@keyframes spin {
  from { transform: rotate(0deg); }
  to { transform: rotate(360deg); }
}`,
                duration: 1000,
                timing: 'linear'
            },
            shake: {
                name: '摇晃提示',
                keyframes: `@keyframes shake {
  0%, 100% { transform: translateX(0); }
  10%, 30%, 50%, 70%, 90% { transform: translateX(-5px); }
  20%, 40%, 60%, 80% { transform: translateX(5px); }
}`,
                duration: 500,
                timing: 'ease-in-out'
            },
            float: {
                name: '漂浮效果',
                keyframes: `@keyframes float {
  0%, 100% { transform: translateY(0); }
  50% { transform: translateY(-8px); }
}`,
                duration: 2000,
                timing: 'ease-in-out'
            }
        };
    }

    // ==================== 缓动函数 ====================

    initEasingFunctions() {
        return {
            'ease': 'ease',
            'ease-in': 'ease-in',
            'ease-out': 'ease-out',
            'ease-in-out': 'ease-in-out',
            'linear': 'linear',
            'easeInQuad': 'cubic-bezier(0.55, 0.085, 0.68, 0.53)',
            'easeInCubic': 'cubic-bezier(0.550, 0.055, 0.675, 0.19)',
            'easeInQuart': 'cubic-bezier(0.895, 0.03, 0.685, 0.22)',
            'easeInQuint': 'cubic-bezier(0.755, 0.05, 0.855, 0.06)',
            'easeOutQuad': 'cubic-bezier(0.25, 0.46, 0.45, 0.94)',
            'easeOutCubic': 'cubic-bezier(0.215, 0.61, 0.355, 1)',
            'easeOutQuart': 'cubic-bezier(0.165, 0.84, 0.44, 1)',
            'easeOutQuint': 'cubic-bezier(0.23, 1, 0.32, 1)',
            'easeInOutQuad': 'cubic-bezier(0.455, 0.03, 0.515, 0.955)',
            'easeInOutCubic': 'cubic-bezier(0.645, 0.045, 0.355, 1)',
            'easeInOutQuart': 'cubic-bezier(0.77, 0, 0.175, 1)',
            'easeInOutQuint': 'cubic-bezier(0.86, 0, 0.07, 1)',
            'spring': 'cubic-bezier(0.175, 0.885, 0.32, 1.275)'
        };
    }

    // ==================== 动画生成 ====================

    // 生成动画CSS
    generateAnimationCSS(config = {}) {
        const name = config.name || 'customAnimation';
        const keyframes = config.keyframes || this.presetAnimations.fade.keyframes;
        const duration = config.duration || 300;
        const timing = config.timing || 'ease';
        const delay = config.delay || 0;
        const iteration = config.iteration || 1;
        const direction = config.direction || 'normal';
        const fill = config.fill || 'none';

        return {
            css: `@keyframes ${name} ${keyframes.replace('@keyframes ' + Object.keys(this.presetAnimations).find(k => this.presetAnimations[k].keyframes === keyframes) || 'fade', '')}`,
            class: `.${name} {
  animation: ${name} ${duration}ms ${this.easingFunctions[timing] || timing} ${delay}ms ${iteration} ${direction} ${fill};
}`
        };
    }

    // 创建微交互
    createMicroInteraction(config = {}) {
        const type = config.type || 'hover'; // hover, click, focus, active

        const interactions = {
            hover: {
                name: '悬停效果',
                css: `.${config.selector || 'element'}:hover {
  transform: ${config.transform || 'scale(1.05)'};
  transition: ${config.duration || 200}ms ${config.easing || 'ease'};
}`
            },
            click: {
                name: '点击效果',
                css: `.${config.selector || 'element'}:active {
  transform: ${config.activeTransform || 'scale(0.95)'};
  transition: 100ms ease;
}`
            },
            focus: {
                name: '焦点效果',
                css: `.${config.selector || 'element'}:focus {
  outline: ${config.outline || '2px solid #3b82f6'};
  outline-offset: ${config.offset || '2px'};
  transition: outline 150ms ease;
}`
            }
        };

        return interactions[type];
    }

    // ==================== 过渡效果 ====================

    // 生成过渡
    generateTransition(config = {}) {
        const properties = config.properties || ['all'];
        const duration = config.duration || 300;
        const timing = config.timing || 'ease';
        const delay = config.delay || 0;

        const transitions = properties.map(prop => {
            return `${prop} ${duration}ms ${this.easingFunctions[timing] || timing} ${delay}ms`;
        }).join(', ');

        return {
            css: `transition: ${transitions};`,
            shorthand: `transition: ${duration}ms ${timing};`
        };
    }

    // 生成卡片悬停效果
    generateCardHoverEffect(config = {}) {
        const lift = config.lift || 4;
        const shadow = config.shadow || 20;

        return {
            css: `.card-hover {
  transition: transform 200ms ease, box-shadow 200ms ease;
}
.card-hover:hover {
  transform: translateY(-${lift}px);
  box-shadow: 0 ${shadow}px ${shadow * 2}px rgba(0, 0, 0, 0.1);
}`
        };
    }

    // ==================== 动画编排 ====================

    // 创建动画序列
    createAnimationSequence(config = {}) {
        const steps = config.steps || [];
        const totalDuration = steps.reduce((sum, step) => sum + (step.duration || 300), 0);

        const sequence = {
            name: config.name || '动画序列',
            steps: [],
            totalDuration,
            css: ''
        };

        let currentDelay = 0;
        steps.forEach((step, index) => {
            const duration = step.duration || 300;
            const delay = step.delay !== undefined ? step.delay : currentDelay;

            sequence.steps.push({
                ...step,
                index,
                delay,
                endTime: delay + duration
            });

            currentDelay += duration;
        });

        // 生成CSS
        sequence.css = steps.map((step, i) => {
            return `.step-${i} {
  animation: ${step.animation || 'fade'} ${step.duration || 300}ms ${step.easing || 'ease'} ${step.delay || 0}ms forwards;
  opacity: 0;
}`;
        }).join('\n');

        return sequence;
    }

    // ==================== 页面过渡 ====================

    // 生成页面过渡
    generatePageTransition(config = {}) {
        const type = config.type || 'fade'; // fade, slide, flip, zoom

        const transitions = {
            fade: {
                css: `.page-enter {
  opacity: 0;
}
.page-enter-active {
  opacity: 1;
  transition: opacity 300ms ease;
}
.page-exit {
  opacity: 1;
}
.page-exit-active {
  opacity: 0;
  transition: opacity 300ms ease;
}`
            },
            slide: {
                css: `.page-enter {
  transform: translateX(20px);
  opacity: 0;
}
.page-enter-active {
  transform: translateX(0);
  opacity: 1;
  transition: transform 300ms ease, opacity 300ms ease;
}
.page-exit {
  transform: translateX(0);
  opacity: 1;
}
.page-exit-active {
  transform: translateX(-20px);
  opacity: 0;
  transition: transform 300ms ease, opacity 300ms ease;
}`
            },
            zoom: {
                css: `.page-enter {
  transform: scale(0.95);
  opacity: 0;
}
.page-enter-active {
  transform: scale(1);
  opacity: 1;
  transition: transform 300ms ease, opacity 300ms ease;
}
.page-exit {
  transform: scale(1);
  opacity: 1;
}
.page-exit-active {
  transform: scale(1.05);
  opacity: 0;
  transition: transform 300ms ease, opacity 300ms ease;
}`
            }
        };

        return transitions[type];
    }

    // ==================== 加载动画 ====================

    // 生成加载动画
    generateLoader(type = 'spinner') {
        const loaders = {
            spinner: {
                html: '<div class="loader-spinner"></div>',
                css: `.loader-spinner {
  width: 40px;
  height: 40px;
  border: 4px solid #f3f3f3;
  border-top: 4px solid #3b82f6;
  border-radius: 50%;
  animation: spin 1s linear infinite;
}
@keyframes spin {
  0% { transform: rotate(0deg); }
  100% { transform: rotate(360deg); }
}`
            },
            dots: {
                html: '<div class="loader-dots"><span></span><span></span><span></span></div>',
                css: `.loader-dots {
  display: flex;
  gap: 4px;
}
.loader-dots span {
  width: 10px;
  height: 10px;
  background: #3b82f6;
  border-radius: 50%;
  animation: dotPulse 1.4s ease-in-out infinite;
}
.loader-dots span:nth-child(2) { animation-delay: 0.2s; }
.loader-dots span:nth-child(3) { animation-delay: 0.4s; }
@keyframes dotPulse {
  0%, 80%, 100% { transform: scale(0.6); opacity: 0.5; }
  40% { transform: scale(1); opacity: 1; }
}`
            },
            bars: {
                html: '<div class="loader-bars"><span></span><span></span><span></span><span></span></div>',
                css: `.loader-bars {
  display: flex;
  gap: 4px;
  align-items: flex-end;
  height: 40px;
}
.loader-bars span {
  width: 8px;
  background: #3b82f6;
  animation: barLoad 1.2s ease-in-out infinite;
}
.loader-bars span:nth-child(1) { animation-delay: 0s; }
.loader-bars span:nth-child(2) { animation-delay: 0.1s; }
.loader-bars span:nth-child(3) { animation-delay: 0.2s; }
.loader-bars span:nth-child(4) { animation-delay: 0.3s; }
@keyframes barLoad {
  0%, 100% { height: 20%; }
  50% { height: 100%; }
}`
            }
        };

        return loaders[type] || loaders.spinner;
    }

    // ==================== 动画性能 ====================

    // 检查动画性能
    checkAnimationPerformance(element) {
        const element_obj = typeof element === 'string' ? document.querySelector(element) : element;
        if (!element_obj) return null;

        const styles = window.getComputedStyle(element_obj);
        const properties = [];

        // 检测可能触发重排的属性
        const layoutProps = ['width', 'height', 'padding', 'margin', 'top', 'left', 'right', 'bottom', 'border-width'];
        const paintProps = ['color', 'background', 'border-color', 'opacity', 'visibility'];
        const compositeProps = ['transform', 'opacity', 'filter'];

        layoutProps.forEach(prop => {
            const value = styles.getPropertyValue(prop);
            if (value && value !== 'auto') {
                properties.push({ property: prop, type: 'layout', impact: 'high' });
            }
        });

        return {
            element: element_obj.tagName.toLowerCase() + (element_obj.id ? `#${element_obj.id}` : '') + (element_obj.className ? `.${element_obj.className.split(' ').join('.')}` : ''),
            properties,
            recommendation: properties.some(p => p.impact === 'high')
                ? '建议使用 transform 和 opacity 替代 width/height 等属性以提升性能'
                : '动画性能良好'
        };
    }

    // 优化动画
    optimizeAnimation(css) {
        let optimized = css;

        // 替换 layout 属性为 transform
        const replacements = [
            { from: /translateX\((-?\d+)px\)/g, to: (match, p1) => `translateX(${p1}px)` },
            { from: /translateY\((-?\d+)px\)/g, to: (match, p1) => `translateY(${p1}px)` }
        ];

        // 添加 will-change 提示
        if (!optimized.includes('will-change')) {
            optimized = optimized.replace(/\.(\w+)\s*\{/, '.$1 {\n  will-change: transform, opacity;');
        }

        return optimized;
    }

    // ==================== 辅助方法 ====================

    getStatus() {
        return {
            id: this.id,
            name: this.name,
            status: this.status,
            workload: this.workload,
            efficiency: this.efficiency,
            presetCount: Object.keys(this.presetAnimations).length,
            easingCount: Object.keys(this.easingFunctions).length
        };
    }

    // 获取所有预设动画
    getPresetAnimations() {
        return this.presetAnimations;
    }

    // 获取所有缓动函数
    getEasingFunctions() {
        return this.easingFunctions;
    }
}

// 创建全局实例
window.animationExpert = new AnimationExpert();

// 导出
window.MTSCOS_AnimationExpert = AnimationExpert;
