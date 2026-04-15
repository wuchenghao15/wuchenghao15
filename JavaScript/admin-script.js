// MTSCOS 超级后台管理脚本
// 实现动态链接库管理、服务控制、终端功能等核心功能

class AdminManager {
    constructor() {
        this.llmModules = {};
        this.runningServices = {};
        this.terminalHistory = [];
        this.currentTerminalCommand = '';
        this.isProcessingTerminal = false;
    }

    // 初始化管理后台
    async initialize() {
        // 验证管理员权限
        if (!this.validateAdminAccess()) {
            window.location.href = '../HTML/index.html';
            return;
        }

        // 加载系统状态
        await this.loadSystemStatus();

        // 初始化动态链接库管理
        this.initLLMModules();

        // 初始化事件监听器
        this.initEventListeners();

        // 启动实时监控
        this.startRealTimeMonitoring();
    }

    // 验证管理员访问权限
    validateAdminAccess() {
        const authToken = localStorage.getItem('auth_token');
        if (!authToken) {
            return false;
        }

        // 这里应该有更复杂的token验证逻辑
        return this.verifyToken(authToken);
    }

    // 验证token（模拟）
    verifyToken(token) {
        // 模拟token验证
        const mockValidTokens = ['admin_token_123456', 'test_token_789012'];
        return mockValidTokens.includes(token);
    }

    // 加载系统状态
    async loadSystemStatus() {
        try {
            // 模拟API调用
            await this.sleep(500);

            // 模拟系统状态数据
            const systemStatus = {
                uptime: '32 天 4 小时 15 分钟',
                cpuUsage: 12.5,
                memoryUsage: 68.2,
                diskSpace: '2.5 GB / 50 GB',
                activeUsers: 12,
                services: [
                    { id: 'http', name: 'HTTP Server', status: 'running', cpu: 2.5, memory: 128 },
                    { id: 'db', name: 'Database Service', status: 'running', cpu: 5.8, memory: 256 },
                    { id: 'monitor', name: 'Monitoring Service', status: 'running', cpu: 1.2, memory: 64 }
                ]
            };

            this.updateSystemStatusUI(systemStatus);
            this.runningServices = systemStatus.services;
        } catch (error) {
            console.error('加载系统状态失败:', error);
            this.showNotification('系统状态加载失败', 'error');
        }
    }

    // 更新系统状态UI
    updateSystemStatusUI(status) {
        const uptimeElement = document.querySelector('.panel-title:contains("运行时间")')?.nextElementSibling;
        if (uptimeElement) {
            uptimeElement.textContent = status.uptime;
        }

        const usersElement = document.querySelector('.panel-title:contains("在线用户")')?.nextElementSibling;
        if (usersElement) {
            usersElement.textContent = status.activeUsers;
        }

        const dbElement = document.querySelector('.panel-title:contains("数据库大小")')?.nextElementSibling;
        if (dbElement) {
            dbElement.textContent = status.diskSpace.split('/')[0].trim();
        }
    }

    // 初始化动态链接库模块
    initLLMModules() {
        // 模拟动态链接库模块
        this.llmModules = {
            'text-generation': { name: '文本生成引擎', version: '1.0.3', status: 'active' },
            'image-processing': { name: '图像处理模块', version: '2.1.0', status: 'active' },
            'data-analytics': { name: '数据分析模块', version: '0.8.5', status: 'inactive' },
            'security-scanner': { name: '安全扫描模块', version: '3.2.1', status: 'active' }
        };
    }

    // 初始化事件监听器
    initEventListeners() {
        // 重启服务按钮
        document.getElementById('restart-services')?.addEventListener('click', async () => {
            await this.restartAllServices();
        });

        // 刷新数据按钮
        document.getElementById('refresh-data')?.addEventListener('click', async () => {
            await this.loadSystemStatus();
            this.showNotification('数据刷新成功', 'success');
        });

        // 退出登录
        document.getElementById('logout')?.addEventListener('click', () => {
            this.logout();
        });

        // 日志选择器
        document.getElementById('log-selector')?.addEventListener('change', (e) => {
            this.loadLogFile(e.target.value);
        });

        // 导航链接事件委托
        document.querySelector('.sidebar-nav')?.addEventListener('click', (e) => {
            const navLink = e.target.closest('.nav-link');
            if (navLink) {
                const href = navLink.getAttribute('href').substring(1);
                this.handleNavigation(href);
            }
        });
    }

    // 处理导航
    handleNavigation(route) {
        const pageTitle = document.getElementById('page-title');
        const titles = {
            'dashboard': '系统控制台',
            'system/services': '服务管理',
            'system/backups': '备份管理',
            'system/logs': '日志管理',
            'system/settings': '系统设置',
            'users/list': '用户列表',
            'users/permissions': '权限管理',
            'database/tables': '表管理',
            'database/backup': '数据备份',
            'database/sync': '数据同步',
            'scripts/javascript': 'JavaScript管理',
            'scripts/styles': '样式管理',
            'theme': '主题管理',
            'terminal': '终端'
        };

        if (titles[route]) {
            pageTitle.textContent = titles[route];
            
            // 如果是终端页面，初始化终端
            if (route === 'terminal') {
                this.initTerminal();
            }
            
            // 如果是动态链接库管理页面
            if (route.includes('modules')) {
                this.renderLLMModules();
            }
        }
    }

    // 重启所有服务
    async restartAllServices() {
        this.showNotification('服务重启开始...', 'info');
        
        try {
            // 模拟服务重启
            await this.sleep(4000);
            
            // 更新服务状态
            this.runningServices.forEach(service => {
                service.status = 'running';
            });
            
            this.updateServiceStatusUI();
            this.showNotification('所有服务重启成功', 'success');
        } catch (error) {
            console.error('服务重启失败:', error);
            this.showNotification('服务重启失败', 'error');
        }
    }

    // 更新服务状态UI
    updateServiceStatusUI() {
        const serviceRows = document.querySelectorAll('#system-services-view tbody tr');
        serviceRows.forEach((row, index) => {
            if (this.runningServices[index]) {
                const statusCell = row.querySelector('td:nth-child(2)');
                const statusIndicator = statusCell.querySelector('.status-indicator');
                const statusText = statusCell.textContent.trim();
                
                if (this.runningServices[index].status === 'running') {
                    statusIndicator.className = 'status-indicator status-online';
                    statusCell.innerHTML = '<span class="status-indicator status-online"></span> 运行中';
                } else {
                    statusIndicator.className = 'status-indicator status-offline';
                    statusCell.innerHTML = '<span class="status-indicator status-offline"></span> 已停止';
                }
                
                // 更新资源使用情况
                row.querySelector('td:nth-child(3)').textContent = `${this.runningServices[index].cpu}%`;
                row.querySelector('td:nth-child(4)').textContent = `${this.runningServices[index].memory} MB`;
            }
        });
    }

    // 加载日志文件
    async loadLogFile(filename) {
        const logContent = document.getElementById('log-content');
        logContent.textContent = '加载中...';
        
        try {
            // 模拟日志加载
            await this.sleep(800);
            
            let logs = '';
            const now = new Date();
            const dateStr = now.toISOString().slice(0, 10);
            const timeStr = now.toTimeString().slice(0, 8);
            
            switch(filename) {
                case 'error.log':
                    logs = `[${dateStr} ${timeStr}] <span class="log-error">ERROR</span> - 文件上传失败: 权限不足\n` +
                           `[${dateStr} ${timeStr}] <span class="log-error">ERROR</span> - 数据库连接超时\n` +
                           `[${dateStr} ${timeStr}] <span class="log-warning">WARNING</span> - 内存使用率过高`;
                    break;
                case 'access.log':
                    logs = `[${dateStr} ${timeStr}] <span class="log-info">INFO</span> - 192.168.1.100 访问 /admin\n` +
                           `[${dateStr} ${timeStr}] <span class="log-info">INFO</span> - 192.168.1.101 访问 /api/data\n` +
                           `[${dateStr} ${timeStr}] <span class="log-info">INFO</span> - 192.168.1.102 访问 /static/css/main.css`;
                    break;
                case 'system.log':
                    logs = `[${dateStr} ${timeStr}] <span class="log-info">INFO</span> - 系统启动成功\n` +
                           `[${dateStr} ${timeStr}] <span class="log-info">INFO</span> - 服务初始化完成\n` +
                           `[${dateStr} ${timeStr}] <span class="log-info">INFO</span> - 数据库连接成功`;
                    break;
                case 'database.log':
                    logs = `[${dateStr} ${timeStr}] <span class="log-info">INFO</span> - 数据库备份开始\n` +
                           `[${dateStr} ${timeStr}] <span class="log-info">INFO</span> - 数据库备份完成 (156 MB)\n` +
                           `[${dateStr} ${timeStr}] <span class="log-success">SUCCESS</span> - 索引优化完成`;
                    break;
            }
            
            logContent.innerHTML = logs;
        } catch (error) {
            console.error('加载日志失败:', error);
            logContent.textContent = '日志加载失败';
        }
    }

    // 渲染动态链接库模块
    renderLLMModules() {
        const modulesContainer = document.createElement('div');
        modulesContainer.className = 'card';
        modulesContainer.innerHTML = `
            <div class="card-header">
                <h3 class="card-title">动态链接库模块管理</h3>
                <button class="btn btn-primary" id="add-module">
                    <i class="fas fa-plus"></i> 添加模块
                </button>
            </div>
            <table class="table" id="modules-table">
                <thead>
                    <tr>
                        <th>模块名称</th>
                        <th>版本</th>
                        <th>状态</th>
                        <th>操作</th>
                    </tr>
                </thead>
                <tbody></tbody>
            </table>
        `;
        
        // 假设这里有一个容器来放置模块管理界面
        const container = document.getElementById('modules-container');
        if (container) {
            container.innerHTML = '';
            container.appendChild(modulesContainer);
        }
        
        const tbody = modulesContainer.querySelector('tbody');
        Object.entries(this.llmModules).forEach(([id, module]) => {
            const row = document.createElement('tr');
            row.innerHTML = `
                <td>${module.name}</td>
                <td>${module.version}</td>
                <td>
                    <span class="status-indicator ${module.status === 'active' ? 'status-online' : 'status-offline'}"></span>
                    ${module.status === 'active' ? '已启用' : '已禁用'}
                </td>
                <td>
                    <button class="btn ${module.status === 'active' ? 'btn-warning' : 'btn-success'} btn-sm toggle-module" data-id="${id}">
                        ${module.status === 'active' ? '禁用' : '启用'}
                    </button>
                    <button class="btn btn-primary btn-sm update-module" data-id="${id}">更新</button>
                    <button class="btn btn-danger btn-sm delete-module" data-id="${id}">删除</button>
                </td>
            `;
            tbody.appendChild(row);
        });
        
        // 添加事件监听器
        this.addModuleEventListeners();
    }

    // 添加模块操作事件监听器
    addModuleEventListeners() {
        document.querySelectorAll('.toggle-module').forEach(btn => {
            btn.addEventListener('click', (e) => {
                const moduleId = e.target.dataset.id;
                this.toggleModule(moduleId);
            });
        });
        
        document.querySelectorAll('.update-module').forEach(btn => {
            btn.addEventListener('click', (e) => {
                const moduleId = e.target.dataset.id;
                this.updateModule(moduleId);
            });
        });
        
        document.querySelectorAll('.delete-module').forEach(btn => {
            btn.addEventListener('click', (e) => {
                const moduleId = e.target.dataset.id;
                this.deleteModule(moduleId);
            });
        });
        
        document.getElementById('add-module')?.addEventListener('click', () => {
            this.addNewModule();
        });
    }

    // 切换模块状态
    toggleModule(moduleId) {
        if (this.llmModules[moduleId]) {
            this.llmModules[moduleId].status = 
                this.llmModules[moduleId].status === 'active' ? 'inactive' : 'active';
            
            this.renderLLMModules();
            this.showNotification(
                `模块 ${this.llmModules[moduleId].name} ${this.llmModules[moduleId].status === 'active' ? '已启用' : '已禁用'}`, 
                'success'
            );
        }
    }

    // 更新模块
    async updateModule(moduleId) {
        this.showNotification(`正在更新模块 ${this.llmModules[moduleId].name}...`, 'info');
        
        try {
            await this.sleep(2000);
            
            // 模拟版本更新
            const versionParts = this.llmModules[moduleId].version.split('.');
            const patch = parseInt(versionParts[2]) + 1;
            this.llmModules[moduleId].version = `${versionParts[0]}.${versionParts[1]}.${patch}`;
            
            this.renderLLMModules();
            this.showNotification(`模块 ${this.llmModules[moduleId].name} 更新成功`, 'success');
        } catch (error) {
            this.showNotification(`模块更新失败`, 'error');
        }
    }

    // 删除模块
    deleteModule(moduleId) {
        if (confirm(`确定要删除模块 ${this.llmModules[moduleId].name} 吗？`)) {
            delete this.llmModules[moduleId];
            this.renderLLMModules();
            this.showNotification('模块已删除', 'success');
        }
    }

    // 添加新模块
    addNewModule() {
        const moduleName = prompt('请输入模块名称:');
        if (moduleName) {
            const moduleId = moduleName.toLowerCase().replace(/\s+/g, '-');
            this.llmModules[moduleId] = {
                name: moduleName,
                version: '1.0.0',
                status: 'inactive'
            };
            
            this.renderLLMModules();
            this.showNotification('新模块已添加', 'success');
        }
    }

    // 初始化终端
    initTerminal() {
        const terminalContainer = document.createElement('div');
        terminalContainer.className = 'card';
        terminalContainer.innerHTML = `
            <div class="card-header">
                <h3 class="card-title">系统终端</h3>
                <button class="btn btn-warning" id="clear-terminal">清空</button>
            </div>
            <div class="terminal" id="terminal-output">
                <div class="terminal-welcome">Welcome to MTSCOS Admin Terminal</div>
                <div class="terminal-prompt">
                    <span class="prompt-user">admin@mtscos</span>
                    <span class="prompt-separator">:</span>
                    <span class="prompt-path">~</span>
                    <span class="prompt-symbol">$</span>
                    <input type="text" class="terminal-input" id="terminal-input"
                           autocomplete="off" autofocus spellcheck="false">
                </div>
            </div>
        `;
        
        // 添加终端样式
        const style = document.createElement('style');
        style.textContent = `
            .terminal {
                background-color: #1e1e1e;
                color: #d4d4d4;
                font-family: 'Courier New', monospace;
                font-size: 14px;
                padding: 15px;
                border-radius: 6px;
                max-height: 500px;
                overflow-y: auto;
            }
            .terminal-welcome {
                margin-bottom: 10px;
                color: #569cd6;
            }
            .terminal-prompt {
                display: flex;
                align-items: center;
                margin-bottom: 5px;
            }
            .prompt-user {
                color: #6a9955;
            }
            .prompt-path {
                color: #569cd6;
            }
            .prompt-separator, .prompt-symbol {
                color: #d4d4d4;
                margin: 0 5px;
            }
            .terminal-input {
                background: transparent;
                border: none;
                color: #d4d4d4;
                flex: 1;
                outline: none;
                font-family: 'Courier New', monospace;
                font-size: 14px;
            }
            .terminal-output-line {
                margin-bottom: 5px;
                white-space: pre-wrap;
            }
        `;
        document.head.appendChild(style);
        
        const container = document.getElementById('terminal-view');
        if (container) {
            container.innerHTML = '';
            container.appendChild(terminalContainer);
        }
        
        // 终端输入处理
        const terminalInput = document.getElementById('terminal-input');
        const terminalOutput = document.getElementById('terminal-output');
        
        terminalInput.addEventListener('keydown', async (e) => {
            if (e.key === 'Enter' && !this.isProcessingTerminal) {
                const command = terminalInput.value.trim();
                if (command) {
                    // 保存到历史记录
                    this.terminalHistory.push(command);
                    this.currentTerminalCommand = '';
                    
                    // 显示输入的命令
                    const commandLine = document.createElement('div');
                    commandLine.className = 'terminal-output-line';
                    commandLine.innerHTML = `
                        <span class="prompt-user">admin@mtscos</span>
                        <span class="prompt-separator">:</span>
                        <span class="prompt-path">~</span>
                        <span class="prompt-symbol">$</span>
                        <span>${command}</span>
                    `;
                    terminalOutput.appendChild(commandLine);
                    
                    // 清空输入框
                    terminalInput.value = '';
                    
                    // 执行命令
                    await this.executeTerminalCommand(command, terminalOutput);
                    
                    // 滚动到底部
                    terminalOutput.scrollTop = terminalOutput.scrollHeight;
                }
            } else if (e.key === 'ArrowUp') {
                e.preventDefault();
                // 历史记录导航
                const currentIndex = this.terminalHistory.indexOf(this.currentTerminalCommand);
                if (currentIndex === -1 && this.terminalHistory.length > 0) {
                    this.currentTerminalCommand = this.terminalHistory[this.terminalHistory.length - 1];
                } else if (currentIndex > 0) {
                    this.currentTerminalCommand = this.terminalHistory[currentIndex - 1];
                }
                terminalInput.value = this.currentTerminalCommand;
            } else if (e.key === 'ArrowDown') {
                e.preventDefault();
                // 历史记录导航
                const currentIndex = this.terminalHistory.indexOf(this.currentTerminalCommand);
                if (currentIndex !== -1 && currentIndex < this.terminalHistory.length - 1) {
                    this.currentTerminalCommand = this.terminalHistory[currentIndex + 1];
                } else {
                    this.currentTerminalCommand = '';
                }
                terminalInput.value = this.currentTerminalCommand;
            }
        });
        
        // 清空终端按钮
        document.getElementById('clear-terminal')?.addEventListener('click', () => {
            const promptContainer = terminalOutput.querySelector('.terminal-prompt');
            terminalOutput.innerHTML = '';
            terminalOutput.appendChild(promptContainer);
            terminalInput.focus();
        });
    }

    // 执行终端命令
    async executeTerminalCommand(command, outputElement) {
        this.isProcessingTerminal = true;
        
        try {
            const response = document.createElement('div');
            response.className = 'terminal-output-line';
            
            // 模拟命令执行
            await this.sleep(1000);
            
            switch(command) {
                case 'help':
                case '?':
                    response.innerHTML = 
                        '可用命令:\n' +
                        '  help, ?          - 显示帮助信息\n' +
                        '  status           - 显示系统状态\n' +
                        '  services         - 列出所有服务\n' +
                        '  restart [service] - 重启指定服务或所有服务\n' +
                        '  backup           - 创建数据库备份\n' +
                        '  modules          - 列出已安装模块\n' +
                        '  clear, cls       - 清空终端\n' +
                        '  exit, quit       - 退出终端';
                    break;
                case 'status':
                    response.textContent = `系统运行时间: 32 天 4 小时 15 分钟\n` +
                                          `CPU 使用率: 12.5%\n` +
                                          `内存使用率: 68.2%\n` +
                                          `磁盘空间: 2.5 GB / 50 GB\n` +
                                          `在线用户: 12`;
                    break;
                case 'services':
                    response.innerHTML = '服务状态:\n';
                    this.runningServices.forEach(service => {
                        response.innerHTML += `  ${service.name}: ${service.status === 'running' ? '\u001b[32m运行中\u001b[0m' : '\u001b[31m已停止\u001b[0m'}\n`;
                    });
                    break;
                case 'restart':
                    await this.restartAllServices();
                    response.textContent = '所有服务已重启';
                    break;
                case 'backup':
                    response.textContent = '正在创建数据库备份...\n备份完成: backup_20251106.sql (156 MB)';
                    break;
                case 'modules':
                    response.innerHTML = '已安装模块:\n';
                    Object.values(this.llmModules).forEach(module => {
                        response.innerHTML += `  ${module.name} (v${module.version}): ${module.status === 'active' ? '\u001b[32m已启用\u001b[0m' : '\u001b[33m已禁用\u001b[0m'}\n`;
                    });
                    break;
                case 'clear':
                case 'cls':
                    outputElement.innerHTML = '';
                    const promptContainer = document.createElement('div');
                    promptContainer.className = 'terminal-prompt';
                    promptContainer.innerHTML = `
                        <span class="prompt-user">admin@mtscos</span>
                        <span class="prompt-separator">:</span>
                        <span class="prompt-path">~</span>
                        <span class="prompt-symbol">$</span>
                        <input type="text" class="terminal-input" id="terminal-input"
                               autocomplete="off" spellcheck="false">
                    `;
                    outputElement.appendChild(promptContainer);
                    
                    // 重新绑定事件
                    const newInput = document.getElementById('terminal-input');
                    newInput.addEventListener('keydown', (e) => {
                        // 重新绑定事件监听器
                        if (e.key === 'Enter' && !this.isProcessingTerminal) {
                            // 简化版的事件处理
                            const cmd = newInput.value.trim();
                            if (cmd) {
                                this.terminalHistory.push(cmd);
                                this.executeTerminalCommand(cmd, outputElement);
                                newInput.value = '';
                            }
                        }
                    });
                    newInput.focus();
                    break;
                case 'exit':
                case 'quit':
                    response.textContent = '退出终端模式';
                    break;
                default:
                    response.textContent = `命令未找到: ${command}\n输入 'help' 获取可用命令列表`;
            }
            
            if (command !== 'clear' && command !== 'cls') {
                outputElement.appendChild(response);
            }
        } catch (error) {
            console.error('执行终端命令失败:', error);
            const errorLine = document.createElement('div');
            errorLine.className = 'terminal-output-line';
            errorLine.textContent = `错误: ${error.message}`;
            outputElement.appendChild(errorLine);
        } finally {
            this.isProcessingTerminal = false;
        }
    }

    // 退出登录
    logout() {
        localStorage.removeItem('auth_token');
        localStorage.removeItem('user_info');
        window.location.href = '../HTML/index.html';
    }

    // 显示通知
    showNotification(message, type = 'info') {
        // 创建通知元素
        const notification = document.createElement('div');
        notification.className = `notification notification-${type}`;
        notification.textContent = message;
        
        // 添加样式
        notification.style.position = 'fixed';
        notification.style.top = '20px';
        notification.style.right = '20px';
        notification.style.padding = '12px 20px';
        notification.style.borderRadius = '6px';
        notification.style.color = 'white';
        notification.style.fontWeight = '500';
        notification.style.zIndex = '9999';
        notification.style.boxShadow = '0 4px 12px rgba(0, 0, 0, 0.15)';
        notification.style.transition = 'opacity 0.3s ease, transform 0.3s ease';
        notification.style.opacity = '0';
        notification.style.transform = 'translateY(-20px)';
        
        // 根据类型设置颜色
        switch(type) {
            case 'success':
                notification.style.backgroundColor = '#28a745';
                break;
            case 'error':
                notification.style.backgroundColor = '#dc3545';
                break;
            case 'warning':
                notification.style.backgroundColor = '#ffc107';
                notification.style.color = '#212529';
                break;
            default:
                notification.style.backgroundColor = '#007bff';
        }
        
        // 添加到文档
        document.body.appendChild(notification);
        
        // 显示动画
        setTimeout(() => {
            notification.style.opacity = '1';
            notification.style.transform = 'translateY(0)';
        }, 10);
        
        // 3秒后隐藏
        setTimeout(() => {
            notification.style.opacity = '0';
            notification.style.transform = 'translateY(-20px)';
            setTimeout(() => {
                document.body.removeChild(notification);
            }, 300);
        }, 3000);
    }

    // 启动实时监控
    startRealTimeMonitoring() {
        // 每30秒更新一次系统状态
        setInterval(async () => {
            await this.loadSystemStatus();
        }, 30000);
    }

    // 辅助函数：延迟
    sleep(ms) {
        return new Promise(resolve => setTimeout(resolve, ms));
    }
}

// 页面加载完成后初始化
window.addEventListener('DOMContentLoaded', () => {
    const adminManager = new AdminManager();
    adminManager.initialize();
    
    // 暴露给全局，方便调试
    window.admin = adminManager;
});