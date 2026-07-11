/**
 * AI员工管理系统
 * 功能：加载、展示和管理AI员工信息
 */

class AIEmployeeManager {
    constructor() {
        this.employees = [];
        this.stats = null;
        this.container = null;
        this.init();
    }
    
    async init() {
        this.container = document.getElementById('ai-employees-container');
        if (!this.container) {
            console.warn('AI员工容器未找到');
            return;
        }
        
        await this.loadEmployees();
        this.renderEmployees();
        this.setupInteractions();
    }
    
    async loadEmployees() {
        try {
            const response = await fetch('config/ai-employees.json');
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            const data = await response.json();
            this.employees = data.ai_employees;
            this.stats = data.team_stats;
            console.log('AI员工数据加载成功:', this.employees);
        } catch (error) {
            console.error('加载AI员工数据失败:', error);
            this.employees = this.getDefaultEmployees();
            this.stats = this.getDefaultStats();
        }
    }
    
    getDefaultEmployees() {
        return [
            {
                id: 'art-designer',
                name: '艺术设计师',
                icon: 'fa-palette',
                color: '#ec4899',
                gradient: 'linear-gradient(135deg, #ec4899 0%, #f472b6 100%)',
                role: '视觉创意专家',
                description: '专注于UI/UX设计、视觉创意、品牌形象和用户体验优化',
                abilities: ['界面设计', '配色方案', '动效设计', '品牌视觉'],
                status: 'active',
                workload: 75,
                efficiency: 92
            },
            {
                id: 'code-developer',
                name: '代码开发师',
                icon: 'fa-code',
                color: '#3b82f6',
                gradient: 'linear-gradient(135deg, #3b82f6 0%, #2563eb 100%)',
                role: '全栈开发专家',
                description: '精通前端、后端、数据库和系统架构的全能开发者',
                abilities: ['前端开发', '后端开发', 'API设计', '性能优化'],
                status: 'active',
                workload: 60,
                efficiency: 95
            }
        ];
    }
    
    getDefaultStats() {
        return {
            total_members: 2,
            active_count: 2,
            average_efficiency: 93.5,
            average_workload: 67.5
        };
    }
    
    renderEmployees() {
        if (!this.container) return;
        
        // 渲染团队统计
        this.renderStats();
        
        // 渲染员工卡片
        const grid = this.container.querySelector('.ai-employees-grid');
        if (!grid) return;
        
        grid.innerHTML = '';
        
        this.employees.forEach((employee, index) => {
            const card = this.createEmployeeCard(employee);
            grid.appendChild(card);
            
            // 添加延迟动画
            setTimeout(() => {
                card.classList.add('visible');
            }, index * 100);
        });
    }
    
    renderStats() {
        if (!this.stats) return;
        
        const statsContainer = this.container.querySelector('.team-stats');
        if (!statsContainer) return;
        
        statsContainer.innerHTML = `
            <div class="stat-item">
                <i class="fas fa-users"></i>
                <span class="stat-value">${this.stats.total_members}</span>
                <span class="stat-label">总人数</span>
            </div>
            <div class="stat-item">
                <i class="fas fa-check-circle"></i>
                <span class="stat-value">${this.stats.active_count}</span>
                <span class="stat-label">在线</span>
            </div>
            <div class="stat-item">
                <i class="fas fa-chart-line"></i>
                <span class="stat-value">${this.stats.average_efficiency}%</span>
                <span class="stat-label">平均效率</span>
            </div>
            <div class="stat-item">
                <i class="fas fa-tasks"></i>
                <span class="stat-value">${this.stats.average_workload}%</span>
                <span class="stat-label">平均负载</span>
            </div>
        `;
    }
    
    createEmployeeCard(employee) {
        const card = document.createElement('div');
        card.className = 'ai-employee-card';
        card.dataset.employeeId = employee.id;
        
        // 技能标签HTML
        const abilitiesHtml = employee.abilities.map(ability => 
            `<span class="ability-tag">${ability}</span>`
        ).join('');
        
        card.innerHTML = `
            <div class="card-header">
                <div class="avatar-wrapper">
                    <div class="avatar" style="background: ${employee.gradient}">
                        <i class="fas ${employee.icon}"></i>
                    </div>
                    <div class="status-indicator ${employee.status}"></div>
                </div>
                <div class="employee-info">
                    <h3 class="employee-name">${employee.name}</h3>
                    <p class="employee-role">${employee.role}</p>
                </div>
            </div>
            <div class="card-body">
                <p class="employee-description">${employee.description}</p>
                <div class="abilities">
                    ${abilitiesHtml}
                </div>
            </div>
            <div class="card-footer">
                <div class="metric">
                    <div class="metric-header">
                        <span>工作效率</span>
                        <span>${employee.efficiency}%</span>
                    </div>
                    <div class="progress-bar">
                        <div class="progress-fill" style="width: ${employee.efficiency}%; background: ${employee.gradient}"></div>
                    </div>
                </div>
                <div class="metric">
                    <div class="metric-header">
                        <span>工作负载</span>
                        <span>${employee.workload}%</span>
                    </div>
                    <div class="progress-bar">
                        <div class="progress-fill" style="width: ${employee.workload}%; background: ${employee.gradient}"></div>
                    </div>
                </div>
            </div>
        `;
        
        return card;
    }
    
    setupInteractions() {
        // 卡片悬停效果
        document.querySelectorAll('.ai-employee-card').forEach(card => {
            card.addEventListener('mouseenter', function() {
                this.classList.add('hover');
            });
            
            card.addEventListener('mouseleave', function() {
                this.classList.remove('hover');
            });
            
            // 点击展开详情
            card.addEventListener('click', function() {
                const employeeId = this.dataset.employeeId;
                this.showEmployeeDetail(employeeId);
            });
        });
    }
    
    showEmployeeDetail(employeeId) {
        const employee = this.employees.find(e => e.id === employeeId);
        if (!employee) return;
        
        console.log('查看AI员工详情:', employee);
        
        // 可以在这里添加模态框或其他详情展示逻辑
        alert(`AI员工详情\n\n姓名: ${employee.name}\n角色: ${employee.role}\n效率: ${employee.efficiency}%\n负载: ${employee.workload}%`);
    }
    
    getEmployees() {
        return this.employees;
    }
    
    getEmployeeById(id) {
        return this.employees.find(e => e.id === id);
    }
    
    getStats() {
        return this.stats;
    }
    
    getActiveEmployees() {
        return this.employees.filter(e => e.status === 'active');
    }
    
    getAverageEfficiency() {
        if (this.employees.length === 0) return 0;
        const total = this.employees.reduce((sum, e) => sum + e.efficiency, 0);
        return Math.round(total / this.employees.length);
    }
}

// 页面加载完成后初始化
document.addEventListener('DOMContentLoaded', () => {
    // 延迟初始化，确保DOM已完全加载
    setTimeout(() => {
        window.aiEmployeeManager = new AIEmployeeManager();
    }, 500);
});

// 导出模块
if (typeof module !== 'undefined' && module.exports) {
    module.exports = AIEmployeeManager;
}