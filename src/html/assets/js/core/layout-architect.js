/**
 * MTSCOS AI System - 布局架构师AI员工
 * 版本: 4.4.0
 * 描述: 专注于响应式布局、组件结构、间距系统、网格系统和布局模式
 */

class LayoutArchitect {
    constructor() {
        this.id = 'layout-architect';
        this.name = '布局架构师';
        this.icon = 'fa-th-large';
        this.color = '#f97316';
        this.gradient = 'linear-gradient(135deg, #f97316 0%, #ea580c 100%)';
        this.role = '布局设计专家';
        this.description = '专注于响应式布局、组件结构、间距系统和网格设计';
        this.abilities = [
            '响应式布局',
            '网格设计',
            '组件结构',
            '间距系统',
            '布局模式',
            '布局优化'
        ];
        this.status = 'active';
        this.workload = 15;
        this.efficiency = 98;
        this.gridSystems = this.initGridSystems();
        this.spacingScale = this.initSpacingScale();
    }

    // ==================== 网格系统 ====================

    initGridSystems() {
        return {
            '12-column': {
                name: '12列网格',
                columns: 12,
                gutter: 24,
                margin: 16,
                breakpoints: {
                    xs: { columns: 4, width: '100%' },
                    sm: { columns: 8, width: '100%' },
                    md: { columns: 12, width: '100%' },
                    lg: { columns: 12, width: '960px' },
                    xl: { columns: 12, width: '1200px' }
                }
            },
            '8-column': {
                name: '8列网格',
                columns: 8,
                gutter: 24,
                margin: 16,
                breakpoints: {
                    xs: { columns: 4, width: '100%' },
                    sm: { columns: 6, width: '100%' },
                    md: { columns: 8, width: '100%' },
                    lg: { columns: 8, width: '960px' },
                    xl: { columns: 8, width: '1200px' }
                }
            }
        };
    }

    initSpacingScale() {
        return {
            base: 4,
            scale: [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 12, 14, 16, 20, 24, 32, 40, 48, 56, 64],
            named: {
                none: 0,
                xs: 4,
                sm: 8,
                md: 16,
                lg: 24,
                xl: 32,
                '2xl': 40,
                '3xl': 48,
                '4xl': 64
            }
        };
    }

    // 生成网格CSS
    generateGridCSS(config = {}) {
        const system = config.system || '12-column';
        const gridConfig = this.gridSystems[system];
        const prefix = config.prefix || 'col';

        let css = '';
        const gutter = gridConfig.gutter;
        const margin = gridConfig.margin;

        // 容器
        css += `.container {\n`;
        css += `  width: 100%;\n`;
        css += `  max-width: ${gridConfig.breakpoints.xl.width};\n`;
        css += `  margin: 0 auto;\n`;
        css += `  padding: 0 ${margin}px;\n`;
        css += `}\n\n`;

        // 行
        css += `.row {\n`;
        css += `  display: flex;\n`;
        css += `  flex-wrap: wrap;\n`;
        css += `  margin: 0 -${gutter/2}px;\n`;
        css += `}\n\n`;

        // 列
        for (let i = 1; i <= gridConfig.columns; i++) {
            const width = (i / gridConfig.columns) * 100;
            css += `.${prefix}-${i} {\n`;
            css += `  flex: 0 0 ${width.toFixed(6)}%;\n`;
            css += `  max-width: ${width.toFixed(6)}%;\n`;
            css += `  padding: 0 ${gutter/2}px;\n`;
            css += `}\n\n`;
        }

        // 响应式
        Object.entries(gridConfig.breakpoints).forEach(([bp, config]) => {
            if (bp !== 'xl') {
                css += `@media (max-width: ${this.getBreakpointWidth(bp)}px) {\n`;
                for (let i = 1; i <= config.columns; i++) {
                    const width = (i / config.columns) * 100;
                    css += `  .${prefix}-${bp}-${i} {\n`;
                    css += `    flex: 0 0 ${width.toFixed(6)}%;\n`;
                    css += `    max-width: ${width.toFixed(6)}%;\n`;
                    css += `  }\n`;
                }
                css += `}\n\n`;
            }
        });

        return css;
    }

    getBreakpointWidth(bp) {
        const widths = { xs: 480, sm: 640, md: 768, lg: 1024, xl: 1280 };
        return widths[bp] || 1280;
    }

    // ==================== 响应式布局 ====================

    // 生成响应式断点
    generateResponsiveBreakpoints() {
        return {
            xs: { min: 0, max: 479, name: '超小屏' },
            sm: { min: 480, max: 767, name: '小屏' },
            md: { min: 768, max: 1023, name: '中屏' },
            lg: { min: 1024, max: 1279, name: '大屏' },
            xl: { min: 1280, max: 1535, name: '超大屏' },
            '2xl': { min: 1536, max: Infinity, name: '双倍大屏' }
        };
    }

    // 生成响应式工具类
    generateResponsiveUtilities() {
        const breakpoints = this.generateResponsiveBreakpoints();
        let css = '';

        // 显示/隐藏
        Object.entries(breakpoints).forEach(([bp, config]) => {
            css += `/* ${bp} - ${config.name} */\n`;
            css += `@media (min-width: ${config.min}px) {\n`;
            css += `  .show-${bp} { display: block !important; }\n`;
            css += `  .hide-${bp} { display: none !important; }\n`;
            css += `}\n\n`;
        });

        return css;
    }

    // ==================== 布局模式 ====================

    getLayoutPatterns() {
        return [
            {
                id: 'single-column',
                name: '单列布局',
                description: '适用于简单页面和移动端',
                structure: 'header → main → footer'
            },
            {
                id: 'sidebar-layout',
                name: '侧边栏布局',
                description: '适用于后台管理界面',
                structure: 'header → sidebar + main → footer'
            },
            {
                id: 'dashboard-layout',
                name: '仪表盘布局',
                description: '适用于数据展示类应用',
                structure: 'header → sidebar + content[widgets] → footer'
            },
            {
                id: 'magazine-layout',
                name: '杂志布局',
                description: '适用于内容展示网站',
                structure: 'header → hero → content[grid] → footer'
            },
            {
                id: 'holy-grail',
                name: '圣杯布局',
                description: '经典三栏布局',
                structure: 'header → nav + main + aside → footer'
            }
        ];
    }

    // 生成布局结构
    generateLayoutStructure(pattern, config = {}) {
        const structures = {
            'sidebar-layout': () => ({
                html: `<div class="layout layout-sidebar">
  <header class="layout-header">${config.header || 'Header'}</header>
  <div class="layout-body">
    <aside class="layout-sidebar">${config.sidebar || 'Sidebar'}</aside>
    <main class="layout-main">${config.main || 'Main Content'}</main>
  </div>
  <footer class="layout-footer">${config.footer || 'Footer'}</footer>
</div>`,
                css: `.layout { display: flex; flex-direction: column; min-height: 100vh; }
.layout-header { flex: 0 0 auto; }
.layout-body { flex: 1; display: flex; }
.layout-sidebar { flex: 0 0 250px; }
.layout-main { flex: 1; }
.layout-footer { flex: 0 0 auto; }`
            }),
            'dashboard-layout': () => ({
                html: `<div class="dashboard">
  <header class="dashboard-header"></header>
  <aside class="dashboard-sidebar"></aside>
  <main class="dashboard-content">
    <div class="widget-grid"></div>
  </main>
</div>`,
                css: `.dashboard { display: grid; grid-template-areas: "header header" "sidebar content"; grid-template-columns: 250px 1fr; grid-template-rows: 60px 1fr; min-height: 100vh; }`
            })
        };

        const generator = structures[pattern];
        return generator ? generator() : null;
    }

    // ==================== 间距系统 ====================

    // 生成间距CSS变量
    generateSpacingCSS() {
        let css = ':root {\n';
        const scale = this.spacingScale;

        scale.scale.forEach((value, index) => {
            const rem = (value * scale.base) / 16;
            css += `  --space-${index}: ${rem}rem;\n`;
        });

        // 命名间距
        Object.entries(scale.named).forEach(([name, value]) => {
            const rem = (value * scale.base) / 16;
            css += `  --space-${name}: ${rem}rem;\n`;
        });

        css += '}\n';
        return css;
    }

    // 计算间距
    calculateSpacing(base, multiplier, scale = 'linear') {
        if (scale === 'linear') {
            return base * multiplier;
        }
        // 几何级数
        return base * Math.pow(1.618, multiplier);
    }

    // ==================== 组件布局 ====================

    // 生成卡片布局
    generateCardGrid(config = {}) {
        const columns = config.columns || 3;
        const gap = config.gap || 24;
        const minWidth = config.minWidth || 300;

        return {
            css: `.card-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(${minWidth}px, 1fr));
  gap: ${gap}px;
}
.card-grid > * {
  break-inside: avoid;
}`,
            html: `<div class="card-grid">
  <!-- Cards here -->
</div>`
        };
    }

    // 生成Flex布局
    generateFlexUtilities() {
        return {
            css: `/* Flex utilities */
.flex { display: flex; }
.flex-col { flex-direction: column; }
.flex-row { flex-direction: row; }
.flex-wrap { flex-wrap: wrap; }
.flex-nowrap { flex-wrap: nowrap; }
.items-start { align-items: flex-start; }
.items-center { align-items: center; }
.items-end { align-items: flex-end; }
.justify-start { justify-content: flex-start; }
.justify-center { justify-content: center; }
.justify-end { justify-content: flex-end; }
.justify-between { justify-content: space-between; }
.justify-around { justify-content: space-around; }
.gap-1 { gap: 0.25rem; }
.gap-2 { gap: 0.5rem; }
.gap-3 { gap: 1rem; }
.gap-4 { gap: 1.5rem; }
.gap-6 { gap: 2rem; }
.flex-1 { flex: 1 1 0%; }
.flex-auto { flex: 1 1 auto; }
.flex-none { flex: none; }`
        };
    }

    // ==================== 布局分析 ====================

    // 分析页面布局
    analyzeLayout(element) {
        const element_obj = typeof element === 'string' ? document.querySelector(element) : element;
        if (!element_obj) return null;

        const rect = element_obj.getBoundingClientRect();
        const styles = window.getComputedStyle(element_obj);

        return {
            dimensions: {
                width: rect.width,
                height: rect.height,
                aspectRatio: rect.width / rect.height
            },
            position: {
                top: rect.top,
                left: rect.left,
                right: rect.right,
                bottom: rect.bottom
            },
            layout: {
                display: styles.display,
                flexDirection: styles.flexDirection,
                justifyContent: styles.justifyContent,
                alignItems: styles.alignItems,
                gap: styles.gap,
                gridTemplateColumns: styles.gridTemplateColumns,
                gridTemplateRows: styles.gridTemplateRows
            },
            spacing: {
                margin: {
                    top: parseFloat(styles.marginTop),
                    right: parseFloat(styles.marginRight),
                    bottom: parseFloat(styles.marginBottom),
                    left: parseFloat(styles.marginLeft)
                },
                padding: {
                    top: parseFloat(styles.paddingTop),
                    right: parseFloat(styles.paddingRight),
                    bottom: parseFloat(styles.paddingBottom),
                    left: parseFloat(styles.paddingLeft)
                }
            }
        };
    }

    // 优化布局建议
    getOptimizationSuggestions(element) {
        const analysis = this.analyzeLayout(element);
        if (!analysis) return [];

        const suggestions = [];

        // 检测固定高度
        if (analysis.dimensions.height === parseFloat(getComputedStyle(element).height)) {
            suggestions.push({
                type: 'height',
                level: 'warning',
                message: '考虑使用 min-height 代替固定 height 以提高灵活性'
            });
        }

        // 检测缺少gap
        if (analysis.layout.display === 'flex' && analysis.layout.gap === '0px') {
            suggestions.push({
                type: 'spacing',
                level: 'info',
                message: '建议添加 gap 属性以改善元素间距'
            });
        }

        return suggestions;
    }

    // ==================== 辅助方法 ====================

    getStatus() {
        return {
            id: this.id,
            name: this.name,
            status: this.status,
            workload: this.workload,
            efficiency: this.efficiency,
            gridSystems: Object.keys(this.gridSystems).length
        };
    }
}

// 创建全局实例
window.layoutArchitect = new LayoutArchitect();

// 导出
window.MTSCOS_LayoutArchitect = LayoutArchitect;
