/**
 * MTSCOS AI System - 配色设计师AI员工
 * 版本: 4.4.0
 * 描述: 专注于颜色系统、色彩搭配、渐变设计、主题配色和视觉层次
 */

class ColorDesigner {
    constructor() {
        this.id = 'color-designer';
        this.name = '配色设计师';
        this.icon = 'fa-palette';
        this.color = '#ec4899';
        this.gradient = 'linear-gradient(135deg, #ec4899 0%, #db2777 100%)';
        this.role = '配色设计专家';
        this.description = '专注于颜色系统、色彩搭配、渐变设计和视觉层次优化';
        this.abilities = [
            '颜色设计',
            '配色方案',
            '渐变设计',
            '主题配色',
            '色彩心理学',
            '视觉层次'
        ];
        this.status = 'active';
        this.workload = 20;
        this.efficiency = 97;
        this.colorPalettes = this.initColorPalettes();
        this.colorSystems = this.initColorSystems();
    }

    // ==================== 色彩系统 ====================

    initColorSystems() {
        return {
            hsl: {
                name: 'HSL色彩空间',
                description: '基于色相、饱和度、亮度的色彩系统',
                functions: {
                    toHSL: (color) => this.rgbToHSL(this.hexToRGB(color)),
                    fromHSL: (h, s, l) => this.rgbToHex(this.hslToRGB(h, s, l)),
                    adjust: (color, adjustments) => this.adjustHSL(color, adjustments)
                }
            },
            css: {
                name: 'CSS颜色',
                description: '标准CSS颜色值转换',
                functions: {
                    toRGB: (color) => this.hexToRGB(color),
                    toHex: (rgb) => this.rgbToHex(rgb),
                    toHSL: (color) => this.rgbToHSL(this.hexToRGB(color))
                }
            }
        };
    }

    // ==================== 配色方案 ====================

    initColorPalettes() {
        return {
            default: {
                name: '默认主题',
                colors: {
                    primary: '#3b82f6',
                    secondary: '#6366f1',
                    success: '#22c55e',
                    warning: '#f59e0b',
                    danger: '#ef4444',
                    info: '#06b6d4',
                    light: '#f8fafc',
                    dark: '#0f172a'
                }
            },
            sunset: {
                name: '日落渐变',
                colors: {
                    primary: '#f97316',
                    secondary: '#ec4899',
                    success: '#10b981',
                    warning: '#fbbf24',
                    danger: '#dc2626'
                }
            },
            ocean: {
                name: '海洋主题',
                colors: {
                    primary: '#0ea5e9',
                    secondary: '#0284c7',
                    success: '#14b8a6',
                    warning: '#f59e0b',
                    danger: '#ef4444'
                }
            },
            forest: {
                name: '森林主题',
                colors: {
                    primary: '#22c55e',
                    secondary: '#16a34a',
                    success: '#10b981',
                    warning: '#eab308',
                    danger: '#dc2626'
                }
            }
        };
    }

    // 生成配色方案
    generatePalette(config = {}) {
        const baseColor = config.baseColor || '#3b82f6';
        const type = config.type || 'complementary'; // complementary, analogous, triadic, split, tetradic

        const palettes = {
            complementary: () => {
                const hsl = this.rgbToHSL(this.hexToRGB(baseColor));
                return {
                    primary: baseColor,
                    secondary: this.rgbToHex(this.hslToRGB((hsl.h + 180) % 360, hsl.s, hsl.l))
                };
            },
            analogous: () => {
                const hsl = this.rgbToHSL(this.hexToRGB(baseColor));
                return {
                    primary: baseColor,
                    secondary: this.rgbToHex(this.hslToRGB((hsl.h + 30) % 360, hsl.s, hsl.l)),
                    tertiary: this.rgbToHex(this.hslToRGB((hsl.h - 30 + 360) % 360, hsl.s, hsl.l))
                };
            },
            triadic: () => {
                const hsl = this.rgbToHSL(this.hexToRGB(baseColor));
                return {
                    primary: baseColor,
                    secondary: this.rgbToHex(this.hslToRGB((hsl.h + 120) % 360, hsl.s, hsl.l)),
                    tertiary: this.rgbToHex(this.hslToRGB((hsl.h + 240) % 360, hsl.s, hsl.l))
                };
            }
        };

        return palettes[type]();
    }

    // ==================== 渐变设计 ====================

    // 生成渐变
    generateGradient(config = {}) {
        const type = config.type || 'linear'; // linear, radial, conic, diamond
        const colors = config.colors || ['#3b82f6', '#8b5cf6'];
        const angle = config.angle || 135;
        const stops = config.stops || null;

        const gradient = {
            id: `grad_${Date.now()}`,
            type,
            colors,
            angle,
            stops,
            css: this.buildGradientCSS(type, colors, angle, stops)
        };

        return gradient;
    }

    // 构建CSS渐变
    buildGradientCSS(type, colors, angle, stops) {
        if (type === 'linear') {
            const stopStr = stops 
                ? stops.map((s, i) => `${colors[i % colors.length]} ${s}%`).join(', ')
                : colors.join(', ');
            return `linear-gradient(${angle}deg, ${stopStr})`;
        }
        if (type === 'radial') {
            return `radial-gradient(circle, ${colors.join(', ')})`;
        }
        if (type === 'conic') {
            return `conic-gradient(from ${angle}deg, ${colors.join(', ')})`;
        }
        return `linear-gradient(${angle}deg, ${colors.join(', ')})`;
    }

    // 预设渐变
    getPresetGradients() {
        return [
            { name: '科技蓝', colors: ['#00c6ff', '#0072ff'] },
            { name: '日落橙', colors: ['#ff9966', '#ff5e62'] },
            { name: '森林绿', colors: ['#11998e', '#38ef7d'] },
            { name: '梦幻紫', colors: ['#667eea', '#764ba2'] },
            { name: '玫瑰金', colors: ['#f5af19', '#f12711'] },
            { name: '冰川蓝', colors: ['#00d2ff', '#3a7bd5'] }
        ];
    }

    // ==================== 颜色工具 ====================

    hexToRGB(hex) {
        const result = /^#?([a-f\d]{2})([a-f\d]{2})([a-f\d]{2})$/i.exec(hex);
        return result ? {
            r: parseInt(result[1], 16),
            g: parseInt(result[2], 16),
            b: parseInt(result[3], 16)
        } : null;
    }

    rgbToHex(rgb) {
        return '#' + [rgb.r, rgb.g, rgb.b].map(x => {
            const hex = x.toString(16);
            return hex.length === 1 ? '0' + hex : hex;
        }).join('');
    }

    rgbToHSL(rgb) {
        rgb.r /= 255;
        rgb.g /= 255;
        rgb.b /= 255;
        const max = Math.max(rgb.r, rgb.g, rgb.b);
        const min = Math.min(rgb.r, rgb.g, rgb.b);
        let h, s, l = (max + min) / 2;

        if (max === min) {
            h = s = 0;
        } else {
            const d = max - min;
            s = l > 0.5 ? d / (2 - max - min) : d / (max + min);
            switch (max) {
                case rgb.r: h = ((rgb.g - rgb.b) / d + (rgb.g < rgb.b ? 6 : 0)) / 6; break;
                case rgb.g: h = ((rgb.b - rgb.r) / d + 2) / 6; break;
                case rgb.b: h = ((rgb.r - rgb.g) / d + 4) / 6; break;
            }
        }

        return { h: Math.round(h * 360), s: Math.round(s * 100), l: Math.round(l * 100) };
    }

    hslToRGB(h, s, l) {
        h /= 360; s /= 100; l /= 100;
        let r, g, b;

        if (s === 0) {
            r = g = b = l;
        } else {
            const hue2rgb = (p, q, t) => {
                if (t < 0) t += 1;
                if (t > 1) t -= 1;
                if (t < 1/6) return p + (q - p) * 6 * t;
                if (t < 1/2) return q;
                if (t < 2/3) return p + (q - p) * (2/3 - t) * 6;
                return p;
            };
            const q = l < 0.5 ? l * (1 + s) : l + s - l * s;
            const p = 2 * l - q;
            r = hue2rgb(p, q, h + 1/3);
            g = hue2rgb(p, q, h);
            b = hue2rgb(p, q, h - 1/3);
        }

        return { r: Math.round(r * 255), g: Math.round(g * 255), b: Math.round(b * 255) };
    }

    // 调整HSL
    adjustHSL(color, adjustments) {
        const rgb = this.hexToRGB(color);
        const hsl = this.rgbToHSL(rgb);
        const newHSL = { ...hsl, ...adjustments };
        return this.rgbToHex(this.hslToRGB(newHSL.h, newHSL.s, newHSL.l));
    }

    // ==================== 主题配色 ====================

    // 生成主题
    generateTheme(config = {}) {
        const baseColor = config.baseColor || '#3b82f6';
        const mode = config.mode || 'light'; // light, dark

        const theme = {
            id: `theme_${Date.now()}`,
            name: config.name || '自定义主题',
            mode,
            colors: {},
            shadows: this.generateShadows(baseColor, mode),
            borders: this.generateBorders(mode)
        };

        // 主色变体
        const hsl = this.rgbToHSL(this.hexToRGB(baseColor));
        theme.colors.primary = baseColor;
        theme.colors.primaryLight = this.rgbToHex(this.hslToRGB(hsl.h, hsl.s, Math.min(90, hsl.l + 20)));
        theme.colors.primaryDark = this.rgbToHex(this.hslToRGB(hsl.h, hsl.s, Math.max(30, hsl.l - 20)));

        // 背景色
        if (mode === 'dark') {
            theme.colors.background = '#0f172a';
            theme.colors.surface = '#1e293b';
            theme.colors.text = '#f8fafc';
            theme.colors.textSecondary = '#94a3b8';
        } else {
            theme.colors.background = '#ffffff';
            theme.colors.surface = '#f8fafc';
            theme.colors.text = '#0f172a';
            theme.colors.textSecondary = '#64748b';
        }

        return theme;
    }

    // 生成阴影
    generateShadows(baseColor, mode) {
        if (mode === 'dark') {
            return {
                sm: '0 1px 2px rgba(0, 0, 0, 0.4)',
                md: '0 4px 6px rgba(0, 0, 0, 0.4)',
                lg: '0 10px 15px rgba(0, 0, 0, 0.4)',
                xl: '0 20px 25px rgba(0, 0, 0, 0.4)'
            };
        }
        return {
            sm: '0 1px 2px rgba(0, 0, 0, 0.05)',
            md: '0 4px 6px rgba(0, 0, 0, 0.1)',
            lg: '0 10px 15px rgba(0, 0, 0, 0.1)',
            xl: '0 20px 25px rgba(0, 0, 0, 0.15)'
        };
    }

    // 生成边框
    generateBorders(mode) {
        if (mode === 'dark') {
            return { color: '#334155', radius: '8px' };
        }
        return { color: '#e2e8f0', radius: '8px' };
    }

    // 应用主题到DOM
    applyTheme(theme) {
        const root = document.documentElement;
        const style = [];

        Object.entries(theme.colors).forEach(([key, value]) => {
            root.style.setProperty(`--color-${key}`, value);
            style.push(`--color-${key}: ${value}`);
        });

        Object.entries(theme.shadows).forEach(([key, value]) => {
            root.style.setProperty(`--shadow-${key}`, value);
        });

        if (theme.borders) {
            root.style.setProperty(`--border-color`, theme.borders.color);
            root.style.setProperty(`--border-radius`, theme.borders.radius);
        }

        return { success: true, applied: style.length + ' variables' };
    }

    // ==================== 色彩心理学 ====================

    getColorPsychology(color) {
        const hsl = this.rgbToHSL(this.hexToRGB(color));
        const psychology = [];

        // 暖色系
        if (hsl.h >= 0 && hsl.h < 60) {
            psychology.push({ trait: '活力', description: '传达温暖、能量和热情' });
            if (hsl.h >= 0 && hsl.h < 30) psychology.push({ trait: '警示', description: '常用于警告和紧急信息' });
        }
        // 橙黄色
        if (hsl.h >= 30 && hsl.h < 60) {
            psychology.push({ trait: '创意', description: '激发创造力和快乐情绪' });
        }
        // 绿色
        if (hsl.h >= 60 && hsl.h < 180) {
            psychology.push({ trait: '自然', description: '传达平静、和谐和成长' });
        }
        // 蓝色
        if (hsl.h >= 180 && hsl.h < 270) {
            psychology.push({ trait: '信任', description: '建立信任感和专业感' });
            psychology.push({ trait: '稳定', description: '传达可靠和稳定' });
        }
        // 紫色
        if (hsl.h >= 270 && hsl.h < 330) {
            psychology.push({ trait: '神秘', description: '传达优雅和创造力' });
        }
        // 粉色
        if (hsl.h >= 330 || hsl.h < 15) {
            psychology.push({ trait: '浪漫', description: '传达温柔和关怀' });
        }

        return psychology;
    }

    // ==================== 辅助方法 ====================

    getStatus() {
        return {
            id: this.id,
            name: this.name,
            status: this.status,
            workload: this.workload,
            efficiency: this.efficiency,
            palettesCount: Object.keys(this.colorPalettes).length
        };
    }

    // 获取所有配色方案
    getAllPalettes() {
        return this.colorPalettes;
    }
}

// 创建全局实例
window.colorDesigner = new ColorDesigner();

// 导出
window.MTSCOS_ColorDesigner = ColorDesigner;
