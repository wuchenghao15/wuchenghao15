/**
 * MTSCOS AI System - 脑库可视化组件
 * 版本: 1.0.0
 * 描述: 脑库可视化展示和交互界面
 */

class BrainVisualizer {
    constructor(brainManager) {
        this.brain = brainManager;
        this.container = null;
        this.currentView = 'dashboard';
        this.init();
    }
    
    async init() {
        await this.brain.waitForReady ? await this.brain.waitForReady() : Promise.resolve();
        console.log('✅ 脑库可视化组件初始化成功');
    }
    
    // 创建脑库面板
    createPanel() {
        const panel = document.createElement('div');
        panel.id = 'brain-panel';
        panel.className = 'brain-panel';
        panel.innerHTML = this.getPanelTemplate();
        
        // 添加样式
        this.addStyles();
        
        // 绑定事件
        this.bindEvents(panel);
        
        return panel;
    }
    
    getPanelTemplate() {
        return `
            <div class="brain-header">
                <h2><i class="fas fa-brain"></i> 脑库数据库</h2>
                <button class="btn-close" id="brain-close">
                    <i class="fas fa-times"></i>
                </button>
            </div>
            
            <div class="brain-nav">
                <button class="nav-btn active" data-view="dashboard">
                    <i class="fas fa-chart-pie"></i> 概览
                </button>
                <button class="nav-btn" data-view="fix-cases">
                    <i class="fas fa-bug"></i> 修复案例
                </button>
                <button class="nav-btn" data-view="best-practices">
                    <i class="fas fa-star"></i> 最佳实践
                </button>
                <button class="nav-btn" data-view="patterns">
                    <i class="fas fa-puzzle-piece"></i> 技术模式
                </button>
                <button class="nav-btn" data-view="errors">
                    <i class="fas fa-exclamation-triangle"></i> 错误方案
                </button>
                <button class="nav-btn" data-view="search">
                    <i class="fas fa-search"></i> 智能搜索
                </button>
            </div>
            
            <div class="brain-content" id="brain-content">
                <!-- 动态内容 -->
            </div>
            
            <div class="brain-footer">
                <button id="brain-export" class="btn btn-sm btn-secondary">
                    <i class="fas fa-download"></i> 导出知识库
                </button>
            </div>
        `;
    }
    
    addStyles() {
        const styles = document.createElement('style');
        styles.textContent = `
            .brain-panel {
                position: fixed;
                top: 20px;
                right: 20px;
                width: 480px;
                max-height: 80vh;
                background: var(--bg-card);
                backdrop-filter: blur(20px);
                border: 1px solid var(--border-color);
                border-radius: var(--radius-xl);
                box-shadow: var(--shadow-xl);
                z-index: 9999;
                display: flex;
                flex-direction: column;
                overflow: hidden;
            }
            
            .brain-header {
                display: flex;
                justify-content: space-between;
                align-items: center;
                padding: 16px 20px;
                border-bottom: 1px solid var(--border-color);
                background: var(--primary-gradient);
                color: white;
            }
            
            .brain-header h2 {
                margin: 0;
                font-size: 16px;
                font-weight: 600;
            }
            
            .btn-close {
                background: none;
                border: none;
                color: white;
                cursor: pointer;
                padding: 4px 8px;
                border-radius: 4px;
                transition: background 0.2s;
            }
            
            .btn-close:hover {
                background: rgba(255,255,255,0.2);
            }
            
            .brain-nav {
                display: flex;
                flex-wrap: wrap;
                gap: 8px;
                padding: 12px 16px;
                border-bottom: 1px solid var(--border-color);
                background: var(--bg-secondary);
            }
            
            .nav-btn {
                flex: 1 1 auto;
                min-width: 70px;
                padding: 8px 12px;
                font-size: 12px;
                border: 1px solid var(--border-color);
                background: var(--bg-card);
                color: var(--text-primary);
                border-radius: var(--radius-md);
                cursor: pointer;
                transition: all 0.2s;
                display: flex;
                align-items: center;
                justify-content: center;
                gap: 4px;
            }
            
            .nav-btn:hover {
                background: var(--primary-500);
                color: white;
                border-color: var(--primary-500);
            }
            
            .nav-btn.active {
                background: var(--primary-500);
                color: white;
                border-color: var(--primary-500);
            }
            
            .brain-content {
                flex: 1;
                overflow-y: auto;
                padding: 16px;
            }
            
            .brain-footer {
                padding: 12px 16px;
                border-top: 1px solid var(--border-color);
                background: var(--bg-secondary);
                display: flex;
                justify-content: flex-end;
                gap: 8px;
            }
            
            /* 内容样式 */
            .content-section {
                animation: fadeIn 0.3s ease;
            }
            
            .stats-grid {
                display: grid;
                grid-template-columns: repeat(2, 1fr);
                gap: 12px;
                margin-bottom: 20px;
            }
            
            .stat-card {
                padding: 16px;
                background: var(--bg-secondary);
                border-radius: var(--radius-lg);
                text-align: center;
            }
            
            .stat-card .number {
                font-size: 28px;
                font-weight: 700;
                background: var(--primary-gradient);
                -webkit-background-clip: text;
                -webkit-text-fill-color: transparent;
            }
            
            .stat-card .label {
                font-size: 12px;
                color: var(--text-muted);
                margin-top: 4px;
            }
            
            .case-card, .practice-card, .pattern-card, .error-card {
                padding: 16px;
                background: var(--bg-secondary);
                border-radius: var(--radius-lg);
                margin-bottom: 12px;
                border-left: 4px solid var(--primary-500);
            }
            
            .case-card h4, .practice-card h4, .pattern-card h4, .error-card h4 {
                margin: 0 0 8px 0;
                font-size: 14px;
                color: var(--text-primary);
            }
            
            .case-card .meta, .practice-card .meta, .pattern-card .meta, .error-card .meta {
                display: flex;
                gap: 8px;
                margin-bottom: 8px;
                flex-wrap: wrap;
            }
            
            .badge {
                padding: 2px 8px;
                font-size: 10px;
                border-radius: var(--radius-full);
                background: var(--primary-500);
                color: white;
            }
            
            .badge.severity-high { background: var(--error-500); }
            .badge.severity-medium { background: var(--warning-500); }
            .badge.severity-critical { background: var(--error-600); }
            
            .case-card p, .practice-card p, .pattern-card p, .error-card p {
                font-size: 12px;
                color: var(--text-secondary);
                margin: 8px 0;
                line-height: 1.5;
            }
            
            .code-block {
                background: var(--gray-900);
                color: var(--gray-100);
                padding: 12px;
                border-radius: var(--radius-md);
                font-family: var(--font-mono);
                font-size: 11px;
                overflow-x: auto;
                margin-top: 8px;
            }
            
            .search-box {
                display: flex;
                gap: 8px;
                margin-bottom: 16px;
            }
            
            .search-box input {
                flex: 1;
                padding: 12px 16px;
                border: 1px solid var(--border-color);
                border-radius: var(--radius-lg);
                font-size: 14px;
                background: var(--bg-input);
                color: var(--text-primary);
            }
            
            .search-box input:focus {
                outline: none;
                border-color: var(--primary-500);
                box-shadow: 0 0 0 3px rgba(59, 130, 246, 0.1);
            }
            
            .search-result {
                padding: 12px;
                background: var(--bg-secondary);
                border-radius: var(--radius-lg);
                margin-bottom: 8px;
                cursor: pointer;
                transition: all 0.2s;
            }
            
            .search-result:hover {
                background: var(--bg-hover);
                transform: translateX(4px);
            }
            
            .search-result .title {
                font-weight: 600;
                font-size: 13px;
                color: var(--text-primary);
                margin-bottom: 4px;
            }
            
            .search-result .excerpt {
                font-size: 11px;
                color: var(--text-muted);
            }
            
            .search-result .source {
                font-size: 10px;
                color: var(--primary-500);
                margin-top: 4px;
            }
            
            @keyframes fadeIn {
                from { opacity: 0; transform: translateY(10px); }
                to { opacity: 1; transform: translateY(0); }
            }
        `;
        
        document.head.appendChild(styles);
    }
    
    bindEvents(panel) {
        // 导航切换
        panel.querySelectorAll('.nav-btn').forEach(btn => {
            btn.addEventListener('click', () => {
                panel.querySelectorAll('.nav-btn').forEach(b => b.classList.remove('active'));
                btn.classList.add('active');
                this.switchView(btn.dataset.view);
            });
        });
        
        // 关闭按钮
        panel.querySelector('#brain-close').addEventListener('click', () => {
            this.hide();
        });
        
        // 导出按钮
        panel.querySelector('#brain-export').addEventListener('click', async () => {
            await this.exportKnowledge();
        });
    }
    
    async switchView(view) {
        this.currentView = view;
        const content = document.getElementById('brain-content');
        
        switch (view) {
            case 'dashboard':
                content.innerHTML = await this.renderDashboard();
                break;
            case 'fix-cases':
                content.innerHTML = await this.renderFixCases();
                break;
            case 'best-practices':
                content.innerHTML = await this.renderBestPractices();
                break;
            case 'patterns':
                content.innerHTML = await this.renderPatterns();
                break;
            case 'errors':
                content.innerHTML = await this.renderErrors();
                break;
            case 'search':
                content.innerHTML = await this.renderSearch();
                break;
        }
    }
    
    async renderDashboard() {
        const stats = await this.brain.getStats();
        
        return `
            <div class="content-section">
                <h3 style="margin-bottom: 16px; font-size: 16px;">📊 脑库统计</h3>
                <div class="stats-grid">
                    <div class="stat-card">
                        <div class="number">${stats.totalItems.fixCases}</div>
                        <div class="label">修复案例</div>
                    </div>
                    <div class="stat-card">
                        <div class="number">${stats.totalItems.bestPractices}</div>
                        <div class="label">最佳实践</div>
                    </div>
                    <div class="stat-card">
                        <div class="number">${stats.totalItems.techPatterns}</div>
                        <div class="label">技术模式</div>
                    </div>
                    <div class="stat-card">
                        <div class="number">${stats.totalItems.errorSolutions}</div>
                        <div class="label">错误方案</div>
                    </div>
                </div>
                
                <h3 style="margin: 20px 0 16px; font-size: 16px;">🔥 最近修复案例</h3>
                ${await this.renderRecentCases()}
            </div>
        `;
    }
    
    async renderRecentCases() {
        const cases = await this.brain.getAllFixCases();
        const recent = cases.slice(0, 3);
        
        return recent.map(c => `
            <div class="case-card">
                <h4>${c.id}: ${c.title}</h4>
                <div class="meta">
                    <span class="badge severity-${c.severity}">${c.severity}</span>
                    <span class="badge">${c.category}</span>
                </div>
                <p>${c.description}</p>
            </div>
        `).join('');
    }
    
    async renderFixCases() {
        const cases = await this.brain.getAllFixCases();
        
        return `
            <div class="content-section">
                <h3 style="margin-bottom: 16px; font-size: 16px;">🐛 修复案例库</h3>
                ${cases.map(c => `
                    <div class="case-card">
                        <h4>${c.id}: ${c.title}</h4>
                        <div class="meta">
                            <span class="badge severity-${c.severity}">${c.severity}</span>
                            <span class="badge">${c.category}</span>
                            ${(c.tags || []).slice(0, 3).map(t => `<span class="badge">${t}</span>`).join('')}
                        </div>
                        <p><strong>根因：</strong>${c.rootCause}</p>
                        <details>
                            <summary style="cursor:pointer;color:var(--primary-500);font-size:12px;">查看解决方案</summary>
                            <div class="code-block">
${(c.solution?.steps || []).map((s, i) => `${i + 1}. ${s}`).join('\n')}
                            </div>
                        </details>
                    </div>
                `).join('')}
            </div>
        `;
    }
    
    async renderBestPractices() {
        const practices = await this.brain.getAllBestPractices();
        
        return `
            <div class="content-section">
                <h3 style="margin-bottom: 16px; font-size: 16px;">⭐ 最佳实践</h3>
                ${practices.map(p => `
                    <div class="practice-card">
                        <h4>${p.id}: ${p.title}</h4>
                        <div class="meta">
                            <span class="badge">${p.category}</span>
                        </div>
                        <p>${p.description}</p>
                        ${(p.practices || []).slice(0, 2).map(pr => `
                            <details style="margin-top:8px;">
                                <summary style="cursor:pointer;color:var(--primary-500);font-size:12px;">${pr.title}</summary>
                                <p style="font-size:11px;margin-top:4px;">${pr.content}</p>
                            </details>
                        `).join('')}
                    </div>
                `).join('')}
            </div>
        `;
    }
    
    async renderPatterns() {
        const patterns = await this.brain.getAllTechPatterns();
        
        return `
            <div class="content-section">
                <h3 style="margin-bottom: 16px; font-size: 16px;">🧩 技术模式</h3>
                ${patterns.map(p => `
                    <div class="pattern-card">
                        <h4>${p.id}: ${p.title}</h4>
                        <div class="meta">
                            <span class="badge">${p.category}</span>
                        </div>
                        <p>${p.description}</p>
                        ${p.example ? `
                            <details>
                                <summary style="cursor:pointer;color:var(--primary-500);font-size:12px;">查看代码示例</summary>
                                <div class="code-block">${p.example.substring(0, 200)}...</div>
                            </details>
                        ` : ''}
                    </div>
                `).join('')}
            </div>
        `;
    }
    
    async renderErrors() {
        const errors = await this.brain.getAllErrorSolutions();
        
        return `
            <div class="content-section">
                <h3 style="margin-bottom: 16px; font-size: 16px;">⚠️ 错误解决方案</h3>
                ${errors.map(e => `
                    <div class="error-card">
                        <h4>${e.id}: ${e.error.substring(0, 50)}...</h4>
                        <div class="meta">
                            <span class="badge">${e.category}</span>
                        </div>
                        <p><strong>原因：</strong>${e.cause}</p>
                        <details>
                            <summary style="cursor:pointer;color:var(--primary-500);font-size:12px;">查看解决方案</summary>
                            <div class="code-block">
${(e.steps || []).map((s, i) => `${i + 1}. ${s}`).join('\n')}
                            </div>
                        </details>
                    </div>
                `).join('')}
            </div>
        `;
    }
    
    async renderSearch() {
        return `
            <div class="content-section">
                <h3 style="margin-bottom: 16px; font-size: 16px;">🔍 智能搜索</h3>
                <div class="search-box">
                    <input type="text" id="brain-search-input" placeholder="输入关键词搜索...">
                    <button class="btn btn-primary" id="brain-search-btn">
                        <i class="fas fa-search"></i>
                    </button>
                </div>
                <div id="brain-search-results">
                    <p style="color:var(--text-muted);font-size:12px;text-align:center;">输入关键词开始搜索...</p>
                </div>
            </div>
        `;
    }
    
    bindSearchEvents() {
        const input = document.getElementById('brain-search-input');
        const btn = document.getElementById('brain-search-btn');
        const results = document.getElementById('brain-search-results');
        
        const performSearch = async () => {
            const query = input.value.trim();
            if (!query) return;
            
            results.innerHTML = '<p style="color:var(--text-muted);">搜索中...</p>';
            
            const searchResults = await this.brain.search(query);
            
            if (searchResults.length === 0) {
                results.innerHTML = '<p style="color:var(--text-muted);">未找到相关结果</p>';
                return;
            }
            
            results.innerHTML = searchResults.slice(0, 10).map(r => `
                <div class="search-result">
                    <div class="title">${r.title || r.id}</div>
                    <div class="excerpt">${(r.description || r.error || '').substring(0, 100)}...</div>
                    <div class="source">来源: ${r.collection}</div>
                </div>
            `).join('');
        };
        
        btn.addEventListener('click', performSearch);
        input.addEventListener('keypress', (e) => {
            if (e.key === 'Enter') performSearch();
        });
    }
    
    async exportKnowledge() {
        try {
            const data = await this.brain.exportKnowledge();
            alert('✅ 脑库已导出到本地存储');
            console.log('📤 脑库导出数据:', data);
        } catch (error) {
            console.error('❌ 导出失败:', error);
            alert('❌ 导出失败');
        }
    }
    
    show() {
        if (!this.container) {
            this.container = this.createPanel();
            document.body.appendChild(this.container);
            
            // 绑定搜索事件
            setTimeout(() => this.bindSearchEvents(), 100);
        }
        
        this.container.style.display = 'flex';
        this.switchView(this.currentView);
    }
    
    hide() {
        if (this.container) {
            this.container.style.display = 'none';
        }
    }
    
    toggle() {
        if (this.container && this.container.style.display !== 'none') {
            this.hide();
        } else {
            this.show();
        }
    }
}

// 导出模块
if (typeof module !== 'undefined' && module.exports) {
    module.exports = BrainVisualizer;
}
