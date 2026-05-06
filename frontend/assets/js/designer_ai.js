// 前端设计师AI核心功能

// 颜色方案生成器
const ColorGenerator = {
    // 生成单色方案
    monochromatic: (baseColor) => {
        const colors = [];
        for (let i = 0; i < 5; i++) {
            const shade = 1 - (i * 0.2);
            colors.push(this.adjustBrightness(baseColor, shade));
        }
        return colors;
    },
    
    // 生成类似色方案
    analogous: (baseColor) => {
        const colors = [baseColor];
        for (let i = 1; i <= 4; i++) {
            const hueOffset = i * 30;
            colors.push(this.adjustHue(baseColor, hueOffset));
        }
        return colors;
    },
    
    // 生成互补色方案
    complementary: (baseColor) => {
        const colors = [baseColor];
        colors.push(this.adjustHue(baseColor, 180));
        for (let i = 1; i <= 3; i++) {
            const shade = 1 - (i * 0.2);
            colors.push(this.adjustBrightness(baseColor, shade));
        }
        return colors;
    },
    
    // 生成三原色方案
    triadic: (baseColor) => {
        const colors = [baseColor];
        colors.push(this.adjustHue(baseColor, 120));
        colors.push(this.adjustHue(baseColor, 240));
        colors.push(this.adjustBrightness(baseColor, 0.8));
        colors.push(this.adjustBrightness(baseColor, 0.6));
        return colors;
    },
    
    // 生成四原色方案
    tetradic: (baseColor) => {
        const colors = [baseColor];
        colors.push(this.adjustHue(baseColor, 90));
        colors.push(this.adjustHue(baseColor, 180));
        colors.push(this.adjustHue(baseColor, 270));
        colors.push(this.adjustBrightness(baseColor, 0.7));
        return colors;
    },
    
    // 调整颜色亮度
    adjustBrightness: (color, factor) => {
        const hex = color.replace('#', '');
        const r = parseInt(hex.substring(0, 2), 16);
        const g = parseInt(hex.substring(2, 4), 16);
        const b = parseInt(hex.substring(4, 6), 16);
        
        const newR = Math.min(255, Math.round(r * factor));
        const newG = Math.min(255, Math.round(g * factor));
        const newB = Math.min(255, Math.round(b * factor));
        
        return `#${newR.toString(16).padStart(2, '0')}${newG.toString(16).padStart(2, '0')}${newB.toString(16).padStart(2, '0')}`;
    },
    
    // 调整颜色色相
    adjustHue: (color, degrees) => {
        const hex = color.replace('#', '');
        const r = parseInt(hex.substring(0, 2), 16) / 255;
        const g = parseInt(hex.substring(2, 4), 16) / 255;
        const b = parseInt(hex.substring(4, 6), 16) / 255;
        
        const max = Math.max(r, g, b);
        const min = Math.min(r, g, b);
        let h = 0;
        
        if (max === min) {
            h = 0;
        } else if (max === r) {
            h = ((g - b) / (max - min)) * 60;
        } else if (max === g) {
            h = (2 + (b - r) / (max - min)) * 60;
        } else {
            h = (4 + (r - g) / (max - min)) * 60;
        }
        
        h = (h + degrees) % 360;
        if (h < 0) h += 360;
        
        const c = max - min;
        const x = c * (1 - Math.abs((h / 60) % 2 - 1));
        const m = max - c;
        
        let newR, newG, newB;
        if (h >= 0 && h < 60) {
            newR = c; newG = x; newB = 0;
        } else if (h >= 60 && h < 120) {
            newR = x; newG = c; newB = 0;
        } else if (h >= 120 && h < 180) {
            newR = 0; newG = c; newB = x;
        } else if (h >= 180 && h < 240) {
            newR = 0; newG = x; newB = c;
        } else if (h >= 240 && h < 300) {
            newR = x; newG = 0; newB = c;
        } else {
            newR = c; newG = 0; newB = x;
        }
        
        const finalR = Math.round((newR + m) * 255);
        const finalG = Math.round((newG + m) * 255);
        const finalB = Math.round((newB + m) * 255);
        
        return `#${finalR.toString(16).padStart(2, '0')}${finalG.toString(16).padStart(2, '0')}${finalB.toString(16).padStart(2, '0')}`;
    }
};

// 设计建议生成器
const DesignSuggestions = {
    // 根据项目类型生成建议
    generateByProjectType: (projectType) => {
        const suggestions = {
            website: [
                "建议使用清晰的导航结构，便于用户快速找到所需信息",
                "优化首屏加载速度，确保用户体验流畅",
                "使用响应式设计，适配不同设备屏幕"
            ],
            webapp: [
                "设计简洁明了的界面，减少用户认知负担",
                "优化交互流程，提高用户操作效率",
                "使用一致的设计语言，增强品牌识别度"
            ],
            mobile: [
                "优先考虑触摸交互，确保按钮尺寸合适",
                "简化导航结构，适应小屏幕设备",
                "优化加载速度，减少移动数据消耗"
            ],
            dashboard: [
                "突出关键数据，使用可视化图表展示",
                "设计清晰的信息层级，便于用户快速理解",
                "提供自定义选项，满足不同用户需求"
            ],
            landing: [
                "突出核心价值主张，吸引用户注意力",
                "设计明确的行动召唤按钮，提高转化率",
                "使用高质量视觉元素，增强品牌形象"
            ]
        };
        return suggestions[projectType] || suggestions.website;
    },
    
    // 根据设计风格生成建议
    generateByDesignStyle: (designStyle) => {
        const suggestions = {
            modern: [
                "使用简洁的线条和几何形状",
                "采用大胆的排版和对比色",
                "融入微妙的动画效果"
            ],
            minimalist: [
                "使用大量留白，突出核心内容",
                "选择有限的色彩 palette",
                "注重排版和空间关系"
            ],
            corporate: [
                "使用专业的色彩方案，如蓝色和灰色",
                "设计清晰的信息层级",
                "保持一致的品牌元素"
            ],
            creative: [
                "大胆使用色彩和图形",
                "尝试非传统的布局",
                "融入独特的视觉元素"
            ],
            vintage: [
                "使用复古色彩 palette",
                "融入怀旧元素和纹理",
                "选择合适的复古字体"
            ],
            dark: [
                "确保文本与背景的对比度足够",
                "使用适当的强调色突出重要元素",
                "考虑不同设备的显示效果"
            ]
        };
        return suggestions[designStyle] || suggestions.modern;
    },
    
    // 生成综合建议
    generate: (projectType, designStyle) => {
        const projectSuggestions = this.generateByProjectType(projectType);
        const styleSuggestions = this.generateByDesignStyle(designStyle);
        return [...projectSuggestions, ...styleSuggestions];
    }
};

// 设计预览生成器
const DesignPreview = {
    // 生成设计预览
    generate: (projectType, designStyle, colors) => {
        const previewContent = document.getElementById('designPreview');
        const placeholder = document.querySelector('.preview-placeholder');
        
        placeholder.style.display = 'none';
        previewContent.style.display = 'block';
        
        // 清空预览内容
        previewContent.innerHTML = '';
        
        // 根据项目类型生成不同的预览
        let previewHTML = '';
        
        switch (projectType) {
            case 'website':
                previewHTML = this.generateWebsitePreview(designStyle, colors);
                break;
            case 'webapp':
                previewHTML = this.generateWebAppPreview(designStyle, colors);
                break;
            case 'mobile':
                previewHTML = this.generateMobilePreview(designStyle, colors);
                break;
            case 'dashboard':
                previewHTML = this.generateDashboardPreview(designStyle, colors);
                break;
            case 'landing':
                previewHTML = this.generateLandingPreview(designStyle, colors);
                break;
            default:
                previewHTML = this.generateWebsitePreview(designStyle, colors);
        }
        
        previewContent.innerHTML = previewHTML;
    },
    
    // 生成网站预览
    generateWebsitePreview: (designStyle, colors) => {
        return `
            <div style="height: 100%; display: flex; flex-direction: column; background: ${colors[0]};">
                <header style="background: ${colors[1]}; padding: 20px; color: white; display: flex; justify-content: space-between; align-items: center;">
                    <div style="font-weight: bold; font-size: 18px;">Brand</div>
                    <nav>
                        <ul style="display: flex; gap: 20px; list-style: none; margin: 0;">
                            <li><a href="#" style="color: white; text-decoration: none;">Home</a></li>
                            <li><a href="#" style="color: white; text-decoration: none;">About</a></li>
                            <li><a href="#" style="color: white; text-decoration: none;">Services</a></li>
                            <li><a href="#" style="color: white; text-decoration: none;">Contact</a></li>
                        </ul>
                    </nav>
                </header>
                <main style="flex: 1; background: white; padding: 40px;">
                    <section style="margin-bottom: 40px;">
                        <h1 style="color: ${colors[0]}; font-size: 32px; margin-bottom: 20px;">Welcome to Our Website</h1>
                        <p style="color: #333; line-height: 1.6;">This is a preview of your website design. The design follows a ${designStyle} style with a color palette based on ${colors[0]}.</p>
                        <button style="margin-top: 20px; padding: 12px 24px; background: ${colors[2]}; color: white; border: none; border-radius: 8px; cursor: pointer;">Learn More</button>
                    </section>
                    <section style="display: grid; grid-template-columns: repeat(3, 1fr); gap: 20px;">
                        ${Array(3).fill().map((_, i) => `
                            <div style="background: ${colors[i + 3]}; color: white; padding: 20px; border-radius: 8px;">
                                <h3>Feature ${i + 1}</h3>
                                <p>Description of feature ${i + 1}</p>
                            </div>
                        `).join('')}
                    </section>
                </main>
                <footer style="background: ${colors[1]}; padding: 20px; color: white; text-align: center;">
                    © 2025 Brand. All rights reserved.
                </footer>
            </div>
        `;
    },
    
    // 生成Web应用预览
    generateWebAppPreview: (designStyle, colors) => {
        return `
            <div style="height: 100%; display: flex; background: ${colors[0]};">
                <aside style="width: 200px; background: ${colors[1]}; color: white; padding: 20px;">
                    <div style="font-weight: bold; font-size: 18px; margin-bottom: 30px;">App Menu</div>
                    <ul style="list-style: none; padding: 0;">
                        ${['Dashboard', 'Projects', 'Tasks', 'Messages', 'Settings'].map(item => `
                            <li style="margin-bottom: 15px;"><a href="#" style="color: white; text-decoration: none; display: block; padding: 8px;">${item}</a></li>
                        `).join('')}
                    </ul>
                </aside>
                <main style="flex: 1; background: white; padding: 20px; overflow-y: auto;">
                    <header style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 30px;">
                        <h1 style="color: ${colors[0]}; font-size: 24px;">Dashboard</h1>
                        <div style="display: flex; gap: 10px;">
                            <button style="padding: 8px 16px; background: ${colors[2]}; color: white; border: none; border-radius: 6px; cursor: pointer;">Add</button>
                            <button style="padding: 8px 16px; background: ${colors[3]}; color: white; border: none; border-radius: 6px; cursor: pointer;">Settings</button>
                        </div>
                    </header>
                    <div style="display: grid; grid-template-columns: repeat(2, 1fr); gap: 20px;">
                        ${Array(4).fill().map((_, i) => `
                            <div style="background: ${colors[i + 2]}; color: white; padding: 20px; border-radius: 8px;">
                                <h3>Card ${i + 1}</h3>
                                <p>Content for card ${i + 1}</p>
                            </div>
                        `).join('')}
                    </div>
                </main>
            </div>
        `;
    },
    
    // 生成移动应用预览
    generateMobilePreview: (designStyle, colors) => {
        return `
            <div style="height: 100%; display: flex; justify-content: center; align-items: center; background: ${colors[0]};">
                <div style="width: 320px; height: 90%; background: white; border-radius: 20px; overflow: hidden; box-shadow: 0 10px 30px rgba(0,0,0,0.2);">
                    <header style="background: ${colors[1]}; padding: 20px; color: white; text-align: center;">
                        <h1 style="font-size: 18px; margin: 0;">Mobile App</h1>
                    </header>
                    <main style="padding: 20px; height: calc(100% - 120px); overflow-y: auto;">
                        <div style="margin-bottom: 30px;">
                            <h2 style="color: ${colors[0]}; font-size: 20px; margin-bottom: 15px;">Welcome</h2>
                            <p style="color: #333; line-height: 1.6;">This is a preview of your mobile app design. The design follows a ${designStyle} style with a color palette based on ${colors[0]}.</p>
                        </div>
                        <div style="display: flex; flex-direction: column; gap: 15px;">
                            ${Array(5).fill().map((_, i) => `
                                <div style="background: ${colors[i % 3 + 2]}; color: white; padding: 15px; border-radius: 8px; display: flex; align-items: center; gap: 10px;">
                                    <div style="width: 40px; height: 40px; background: rgba(255,255,255,0.2); border-radius: 50%; display: flex; align-items: center; justify-content: center;">${i + 1}</div>
                                    <span>Item ${i + 1}</span>
                                </div>
                            `).join('')}
                        </div>
                    </main>
                    <footer style="background: ${colors[1]}; padding: 15px; display: flex; justify-content: space-around; color: white;">
                        ${['Home', 'Search', 'Profile', 'Settings'].map(item => `
                            <div style="text-align: center; font-size: 12px;">
                                <div style="font-size: 18px; margin-bottom: 5px;">•</div>
                                ${item}
                            </div>
                        `).join('')}
                    </footer>
                </div>
            </div>
        `;
    },
    
    // 生成仪表盘预览
    generateDashboardPreview: (designStyle, colors) => {
        return `
            <div style="height: 100%; display: flex; flex-direction: column; background: ${colors[0]};">
                <header style="background: ${colors[1]}; padding: 15px; color: white; display: flex; justify-content: space-between; align-items: center;">
                    <div style="font-weight: bold; font-size: 16px;">Dashboard</div>
                    <div style="display: flex; gap: 10px;">
                        <button style="padding: 6px 12px; background: ${colors[2]}; color: white; border: none; border-radius: 4px; cursor: pointer; font-size: 12px;">Refresh</button>
                    </div>
                </header>
                <main style="flex: 1; background: white; padding: 20px; overflow-y: auto;">
                    <div style="display: grid; grid-template-columns: repeat(4, 1fr); gap: 15px; margin-bottom: 30px;">
                        ${Array(4).fill().map((_, i) => `
                            <div style="background: ${colors[i + 2]}; color: white; padding: 15px; border-radius: 8px;">
                                <div style="font-size: 12px; opacity: 0.8;">Metric ${i + 1}</div>
                                <div style="font-size: 24px; font-weight: bold;">${Math.floor(Math.random() * 1000)}</div>
                                <div style="font-size: 10px; margin-top: 5px;">${Math.random() > 0.5 ? '↑' : '↓'} ${Math.floor(Math.random() * 20)}%</div>
                            </div>
                        `).join('')}
                    </div>
                    <div style="display: grid; grid-template-columns: 2fr 1fr; gap: 20px;">
                        <div style="background: ${colors[3]}; color: white; padding: 20px; border-radius: 8px;">
                            <h3 style="margin-top: 0;">Performance Chart</h3>
                            <div style="height: 200px; background: rgba(255,255,255,0.1); border-radius: 4px; margin-top: 15px;"></div>
                        </div>
                        <div style="background: ${colors[4]}; color: white; padding: 20px; border-radius: 8px;">
                            <h3 style="margin-top: 0;">Recent Activity</h3>
                            <ul style="list-style: none; padding: 0; margin-top: 15px;">
                                ${Array(5).fill().map((_, i) => `
                                    <li style="margin-bottom: 10px; font-size: 12px;">Activity ${i + 1}</li>
                                `).join('')}
                            </ul>
                        </div>
                    </div>
                </main>
            </div>
        `;
    },
    
    // 生成落地页预览
    generateLandingPreview: (designStyle, colors) => {
        return `
            <div style="height: 100%; display: flex; flex-direction: column; background: ${colors[0]};">
                <main style="flex: 1; background: white; display: flex; align-items: center; justify-content: center; padding: 40px;">
                    <div style="max-width: 800px; text-align: center;">
                        <h1 style="color: ${colors[0]}; font-size: 48px; margin-bottom: 20px;">Welcome to Our Service</h1>
                        <p style="color: #333; font-size: 18px; margin-bottom: 40px; line-height: 1.6;">This is a preview of your landing page design. The design follows a ${designStyle} style with a color palette based on ${colors[0]}.</p>
                        <div style="display: flex; gap: 20px; justify-content: center;">
                            <button style="padding: 15px 30px; background: ${colors[1]}; color: white; border: none; border-radius: 8px; cursor: pointer; font-size: 16px;">Get Started</button>
                            <button style="padding: 15px 30px; background: ${colors[2]}; color: white; border: none; border-radius: 8px; cursor: pointer; font-size: 16px;">Learn More</button>
                        </div>
                    </div>
                </main>
                <section style="background: ${colors[1]}; color: white; padding: 40px;">
                    <div style="max-width: 1200px; margin: 0 auto; display: grid; grid-template-columns: repeat(3, 1fr); gap: 40px;">
                        ${Array(3).fill().map((_, i) => `
                            <div>
                                <div style="font-size: 32px; margin-bottom: 20px;">${['🚀', '💡', '🎯'][i]}</div>
                                <h3 style="font-size: 20px; margin-bottom: 15px;">Feature ${i + 1}</h3>
                                <p style="line-height: 1.6;">Description of feature ${i + 1} and its benefits.</p>
                            </div>
                        `).join('')}
                    </div>
                </section>
                <footer style="background: ${colors[0]}; padding: 20px; color: white; text-align: center;">
                    © 2025 Brand. All rights reserved.
                </footer>
            </div>
        `;
    }
};

// 初始化页面
document.addEventListener('DOMContentLoaded', function() {
    // 生成设计方案按钮
    const generateButton = document.getElementById('generateDesign');
    
    generateButton.addEventListener('click', function() {
        // 显示加载状态
        generateButton.innerHTML = '<i class="fas fa-spinner fa-spin"></i> 生成中...';
        generateButton.disabled = true;
        
        // 模拟生成过程
        setTimeout(() => {
            // 获取用户选择
            const projectType = document.getElementById('projectType').value;
            const designStyle = document.getElementById('designStyle').value;
            const colorScheme = document.getElementById('colorScheme').value;
            
            // 生成颜色方案
            const baseColor = '#165DFF'; // 默认基色
            let colors = [];
            
            switch (colorScheme) {
                case 'monochromatic':
                    colors = ColorGenerator.monochromatic(baseColor);
                    break;
                case 'analogous':
                    colors = ColorGenerator.analogous(baseColor);
                    break;
                case 'complementary':
                    colors = ColorGenerator.complementary(baseColor);
                    break;
                case 'triadic':
                    colors = ColorGenerator.triadic(baseColor);
                    break;
                case 'tetradic':
                    colors = ColorGenerator.tetradic(baseColor);
                    break;
                default:
                    colors = ColorGenerator.monochromatic(baseColor);
            }
            
            // 显示颜色方案
            const colorSchemePreview = document.getElementById('colorSchemePreview');
            colorSchemePreview.innerHTML = '';
            
            colors.forEach(color => {
                const swatch = document.createElement('div');
                swatch.className = 'color-swatch';
                swatch.style.backgroundColor = color;
                swatch.setAttribute('data-color', color);
                colorSchemePreview.appendChild(swatch);
            });
            
            // 生成设计预览
            DesignPreview.generate(projectType, designStyle, colors);
            
            // 生成设计建议
            const designSuggestions = document.getElementById('designSuggestions');
            designSuggestions.innerHTML = '';
            
            const suggestions = DesignSuggestions.generate(projectType, designStyle);
            
            suggestions.forEach((suggestion, index) => {
                const suggestionItem = document.createElement('div');
                suggestionItem.className = 'suggestion-item';
                suggestionItem.innerHTML = `
                    <h4>建议 ${index + 1}</h4>
                    <p>${suggestion}</p>
                `;
                designSuggestions.appendChild(suggestionItem);
            });
            
            // 恢复按钮状态
            generateButton.innerHTML = '<i class="fas fa-magic"></i> 生成设计方案';
            generateButton.disabled = false;
            
        }, 1500);
    });
    
    // 工具按钮点击事件
    const toolButtons = document.querySelectorAll('.tool-card .btn');
    toolButtons.forEach(button => {
        button.addEventListener('click', function() {
            const toolName = this.parentElement.querySelector('.tool-title').textContent;
            alert(`打开${toolName}工具`);
        });
    });
});

// 页面加载动画
window.addEventListener('load', function() {
    const cards = document.querySelectorAll('.card');
    cards.forEach((card, index) => {
        card.style.opacity = '0';
        card.style.transform = 'translateY(20px)';
        card.style.transition = 'opacity 0.5s ease, transform 0.5s ease';
        
        setTimeout(() => {
            card.style.opacity = '1';
            card.style.transform = 'translateY(0)';
        }, index * 100);
    });
});