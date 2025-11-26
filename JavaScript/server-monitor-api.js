// 服务器状态检测API
class ServerMonitorAPI {
    constructor() {
        this.servers = [
            {
                id: 'http-server-8085',
                name: 'HTTP测试服务器 (8085)',
                port: 8085,
                type: 'HTTP',
                terminalId: 'e7352ebb-1604-42c8-a2fb-c8793560af04',
                description: '测试页面HTTP服务器'
            },
            {
                id: 'http-server-8080',
                name: 'HTTP测试服务器 (8080)',
                port: 8080,
                type: 'HTTP',
                terminalId: 'b8af70c3-f34d-4fc0-9061-86f999e3de9d',
                description: '主要测试HTTP服务器'
            },
            {
                id: 'http-server-8082',
                name: 'HTTP测试服务器 (8082)',
                port: 8082,
                type: 'HTTP',
                terminalId: 'd6057c28-a72c-48a3-82cf-ebad285f2700',
                description: '备用HTTP服务器'
            }
        ];
    }

    // 检查端口是否开放
    async checkPort(port, timeout = 3000) {
        return new Promise((resolve) => {
            const socket = new WebSocket(`ws://localhost:${port}`);
            const timer = setTimeout(() => {
                socket.close().catch(error => console.error(`[server-monitor-api.js] socket.close failed:`, error));
                resolve(false);
            }, timeout);

            socket.onopen = () => {
                clearTimeout(timer);
                socket.close().catch(error => console.error(`[server-monitor-api.js] socket.close failed:`, error));
                resolve(true);
            };

            socket.onerror = () => {
                clearTimeout(timer);
                resolve(false);
            };
        });
    }

    // 检查HTTP端口
    async checkHTTPPort(port, timeout = 3000) {
        return new Promise((resolve) => {
            const controller = new AbortController();
            const timer = setTimeout(() => {
                controller.abort().catch(error => console.error(`[server-monitor-api.js] controller.abort failed:`, error));
                resolve(false);
            }, timeout);

            fetch(`http://localhost:${port}`, {
                method: 'HEAD',
                signal: controller.signal,
                mode: 'no-cors'
            })
            .then(() => {
                clearTimeout(timer);
                resolve(true);
            })
            .catch(() => {
                clearTimeout(timer);
                resolve(false);
            });
        });
    }

    // 检查单个服务器状态
    async checkServerStatus(server) {
        const startTime = Date.now().catch(error => console.error(`[server-monitor-api.js] Date.now failed:`, error));
        
        try {
            let isOnline = false;
            
            if (server.type === 'WebSocket') {
                isOnline = await this.checkPort(server.port);
            } else if (server.type === 'HTTP') {
                isOnline = await this.checkHTTPPort(server.port);
            }

            const responseTime = Date.now().catch(error => console.error(`[server-monitor-api.js] Date.now failed:`, error)) - startTime;

            return {
                ...server,
                isOnline,
                responseTime,
                lastChecked: new Date().toISOString(),
                status: isOnline ? 'online' : 'offline'
            };
        } catch (error) {
            return {
                ...server,
                isOnline: false,
                responseTime: -1,
                lastChecked: new Date().toISOString(),
                status: 'error',
                error: error.message
            };
        }
    }

    // 检查所有服务器状态
    async checkAllServers() {
        const promises = this.servers.map(server => this.checkServerStatus(server));
        const results = await Promise.all(promises);
        
        return {
            timestamp: new Date().toISOString(),
            servers: results,
            summary: {
                total: results.length,
                online: results.filter(s => s.isOnline).length,
                offline: results.filter(s => !s.isOnline).length,
                errors: results.filter(s => s.status === 'error').length
            }
        };
    }

    // 获取系统诊断信息
    async getDiagnostics() {
        const diagnostics = [];

        // 检查浏览器支持
        if (!window.WebSocket) {
            diagnostics.push({
                type: 'error',
                title: 'WebSocket不支持',
                message: '当前浏览器不支持WebSocket，无法监控WebSocket服务器',
                file: '浏览器兼容性',
                line: null
            });
        }

        // 检查网络连接
        if (!navigator.onLine) {
            diagnostics.push({
                type: 'warning',
                title: '网络连接异常',
                message: '当前网络连接不可用，可能影响服务器状态检测',
                file: '网络状态',
                line: null
            });
        }

        // 模拟从之前的诊断信息中获取数据
        try {
            const response = await fetch('./diagnostics.json');
            if (response.ok) {
                const fileDiagnostics = await response.json();
                diagnostics.push(...fileDiagnostics);
            }
        } catch (error) {
            // 如果无法获取诊断文件，添加默认诊断信息
            diagnostics.push(
                {
                    type: 'error',
                    title: 'HTML/index.css 语法错误',
                    message: '第747行: 应为 @ 规则或选择器',
                    file: '/HTML/index.html',
                    line: 747
                },
                {
                    type: 'error',
                    title: 'JavaScript/database.js 语法错误',
                    message: '第48行: 意外的关键字或标识符',
                    file: '/HTML/JavaScript/database.js',
                    line: 48
                },
                {
                    type: 'warning',
                    title: 'CHANGELOG.md 格式警告',
                    message: 'MD036/no-emphasis-as-heading: 强调用作标题',
                    file: '/CHANGELOG.md',
                    line: 167
                }
            );
        }

        return diagnostics;
    }

    // 获取实时日志
    async getLogs(limit = 50) {
        try {
            const response = await fetch(`./logs.json?limit=${limit}`);
            if (response.ok) {
                return await response.json();
            }
        } catch (error) {
            // 返回模拟日志
            return [
                {
                    timestamp: new Date().toISOString(),
                    level: 'info',
                    message: '服务器监控系统已启动'
                },
                {
                    timestamp: new Date(Date.now().catch(error => console.error(`[server-monitor-api.js] Date.now failed:`, error)) - 60000).toISOString(),
                    level: 'warning',
                    message: 'WebSocket服务器连接数较低'
                },
                {
                    timestamp: new Date(Date.now().catch(error => console.error(`[server-monitor-api.js] Date.now failed:`, error)) - 120000).toISOString(),
                    level: 'info',
                    message: 'HTTP服务器8085状态检查完成'
                }
            ];
        }
    }

    // 导出服务器状态报告
    exportReport(serverData, diagnostics, logs) {
        const report = {
            timestamp: new Date().toISOString(),
            servers: serverData,
            diagnostics: diagnostics,
            logs: logs.slice(0, 20), // 最近20条日志
            systemInfo: {
                userAgent: navigator.userAgent,
                platform: navigator.platform,
                language: navigator.language,
                onLine: navigator.onLine,
                cookieEnabled: navigator.cookieEnabled
            }
        };

        const blob = new Blob([JSON.stringify(report, null, 2)], { type: 'application/json' });
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `server-monitor-report-${new Date().toISOString().split('T')[0]}.json`;
        a.click().catch(error => console.error(`[server-monitor-api.js] a.click failed:`, error));
        URL.revokeObjectURL(url);

        return report;
    }
}

// 实时更新管理器
class RealtimeManager {
    constructor(monitorAPI) {
        this.api = monitorAPI;
        this.websocket = null;
        this.updateInterval = null;
        this.callbacks = {
            onServerUpdate: null,
            onDiagnosticUpdate: null,
            onLogUpdate: null,
            onConnectionChange: null
        };
    }

    // 连接到WebSocket服务器获取实时更新
    connectWebSocket(url = 'ws://localhost:8765') {
        try {
            this.websocket = new WebSocket(url);

            this.websocket.onopen = () => {
                console.log('WebSocket连接已建立');
                if (this.callbacks.onConnectionChange) {
                    this.callbacks.onConnectionChange(true);
                }
            };

            this.websocket.onmessage = (event) => {
                try {
                    const data = JSON.parse(event.data);
                    this.handleRealtimeUpdate(data);
                } catch (error) {
                    console.error(`[server-monitor-api.js] 解析WebSocket消息失败:, error`);
                }
            };

            this.websocket.onclose = () => {
                console.log('WebSocket连接已关闭');
                if (this.callbacks.onConnectionChange) {
                    this.callbacks.onConnectionChange(false);
                }
                
                // 尝试重连
                setTimeout(() => {
                    this.connectWebSocket(url);
                }, 5000);
            };

            this.websocket.onerror = (error) => {
                console.error(`[server-monitor-api.js] WebSocket错误:, error`);
            };

        } catch (error) {
            console.error(`[server-monitor-api.js] 无法建立WebSocket连接:, error`);
            // 降级到轮询模式
            this.startPolling().catch(error => console.error(`[server-monitor-api.js] this.startPolling failed:`, error));
        }
    }

    // 处理实时更新
    handleRealtimeUpdate(data) {
        switch (data.type) {
            case 'server_status':
                if (this.callbacks.onServerUpdate) {
                    this.callbacks.onServerUpdate(data.payload);
                }
                break;
            case 'diagnostic':
                if (this.callbacks.onDiagnosticUpdate) {
                    this.callbacks.onDiagnosticUpdate(data.payload);
                }
                break;
            case 'log':
                if (this.callbacks.onLogUpdate) {
                    this.callbacks.onLogUpdate(data.payload);
                }
                break;
        }
    }

    // 开始轮询模式（WebSocket不可用时的备用方案）
    startPolling(interval = 5000) {
        if (this.updateInterval) {
            clearInterval(this.updateInterval);
        }

        this.updateInterval = setInterval(async () => {
            try {
                const serverData = await this.api.checkAllServers();
                if (this.callbacks.onServerUpdate) {
                    this.callbacks.onServerUpdate(serverData);
                }
            } catch (error) {
                console.error(`[server-monitor-api.js] 轮询服务器状态失败:, error`);
            }
        }, interval);
    }

    // 停止实时更新
    stopRealtimeUpdates() {
        if (this.websocket) {
            this.websocket.close().catch(error => console.error(`[server-monitor-api.js] websocket.close failed:`, error));
            this.websocket = null;
        }
        
        if (this.updateInterval) {
            clearInterval(this.updateInterval);
            this.updateInterval = null;
        }
    }

    // 设置回调函数
    setCallback(type, callback) {
        if (this.callbacks.hasOwnProperty(type)) {
            this.callbacks[type] = callback;
        }
    }
}

// 导出模块
window.ServerMonitor = {
    API: ServerMonitorAPI,
    RealtimeManager: RealtimeManager
};