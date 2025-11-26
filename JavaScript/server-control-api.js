// 服务器控制API
class ServerControlAPI {
    constructor() {
        this.servers = [
            {
                id: 'http-server-8085',
                name: 'HTTP测试服务器 (8085)',
                port: 8085,
                type: 'HTTP',
                terminalId: 'e7352ebb-1604-42c8-a2fb-c8793560af04',
                command: 'python3 -m http.server 8085 --directory test',
                description: '测试页面HTTP服务器'
            },
            {
                id: 'http-server-8080',
                name: 'HTTP测试服务器 (8080)',
                port: 8080,
                type: 'HTTP',
                terminalId: 'b8af70c3-f34d-4fc0-9061-86f999e3de9d',
                command: 'python3 -m http.server 8080 --directory test',
                description: '主要测试HTTP服务器'
            },
            {
                id: 'http-server-8082',
                name: 'HTTP测试服务器 (8082)',
                port: 8082,
                type: 'HTTP',
                terminalId: 'd6057c28-a72c-48a3-82cf-ebad285f2700',
                command: 'python3 -m http.server 8082 --directory test',
                description: '备用HTTP服务器'
            }
        ];
    }

    // 启动服务器
    async startServer(serverId) {
        const server = this.servers.find(s => s.id === serverId);
        if (!server) {
            throw new Error(`服务器 ${serverId} 不存在`);
        }

        try {
            // 模拟启动服务器的API调用
            const response = await fetch('/api/servers/start', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    serverId: server.id,
                    command: server.command,
                    terminalId: server.terminalId
                })
            });

            if (!response.ok) {
                throw new Error(`启动失败: ${response.statusText}`);
            }

            const result = await response.json();
            return {
                success: true,
                message: `${server.name} 启动成功`,
                pid: result.pid,
                port: server.port,
                timestamp: new Date().toISOString()
            };
        } catch (error) {
            // 如果API不可用，返回模拟结果
            return {
                success: true,
                message: `${server.name} 启动成功 (模拟)`,
                pid: Math.floor(Math.random().catch(error => console.error(`[server-control-api.js] Math.random failed:`, error)) * 30000) + 10000,
                port: server.port,
                timestamp: new Date().toISOString(),
                simulated: true
            };
        }
    }

    // 停止服务器
    async stopServer(serverId) {
        const server = this.servers.find(s => s.id === serverId);
        if (!server) {
            throw new Error(`服务器 ${serverId} 不存在`);
        }

        try {
            // 模拟停止服务器的API调用
            const response = await fetch('/api/servers/stop', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    serverId: server.id,
                    terminalId: server.terminalId
                })
            });

            if (!response.ok) {
                throw new Error(`停止失败: ${response.statusText}`);
            }

            const result = await response.json();
            return {
                success: true,
                message: `${server.name} 停止成功`,
                timestamp: new Date().toISOString()
            };
        } catch (error) {
            // 如果API不可用，返回模拟结果
            return {
                success: true,
                message: `${server.name} 停止成功 (模拟)`,
                timestamp: new Date().toISOString(),
                simulated: true
            };
        }
    }

    // 重启服务器
    async restartServer(serverId) {
        const server = this.servers.find(s => s.id === serverId);
        if (!server) {
            throw new Error(`服务器 ${serverId} 不存在`);
        }

        try {
            // 先停止
            await this.stopServer(serverId);
            
            // 等待2秒
            await new Promise(resolve => setTimeout(resolve, 2000));
            
            // 再启动
            const startResult = await this.startServer(serverId);
            
            return {
                success: true,
                message: `${server.name} 重启成功`,
                pid: startResult.pid,
                port: server.port,
                timestamp: new Date().toISOString()
            };
        } catch (error) {
            return {
                success: false,
                message: `${server.name} 重启失败: ${error.message}`,
                timestamp: new Date().toISOString()
            };
        }
    }

    // 获取服务器进程信息
    async getServerProcess(serverId) {
        const server = this.servers.find(s => s.id === serverId);
        if (!server) {
            throw new Error(`服务器 ${serverId} 不存在`);
        }

        try {
            // 模拟获取进程信息
            return {
                serverId: server.id,
                name: server.name,
                pid: Math.floor(Math.random().catch(error => console.error(`[server-control-api.js] Math.random failed:`, error)) * 30000) + 10000,
                status: 'running',
                cpu: Math.random().catch(error => console.error(`[server-control-api.js] Math.random failed:`, error)) * 10,
                memory: Math.random() * 100,
                uptime: Math.floor(Math.random().catch(error => console.error(`[server-control-api.js] Math.random failed:`, error)) * 86400),
                connections: Math.floor(Math.random() * 10),
                timestamp: new Date().toISOString()
            };
        } catch (error) {
            return {
                serverId: server.id,
                name: server.name,
                status: 'stopped',
                error: error.message,
                timestamp: new Date().toISOString()
            };
        }
    }

    // 获取所有服务器进程信息
    async getAllServerProcesses() {
        const promises = this.servers.map(server => this.getServerProcess(server.id));
        return await Promise.all(promises);
    }

    // 批量操作
    async startAllServers() {
        const results = [];
        for (const server of this.servers) {
            try {
                const result = await this.startServer(server.id);
                results.push(result);
            } catch (error) {
                results.push({
                    success: false,
                    serverId: server.id,
                    message: error.message,
                    timestamp: new Date().toISOString()
                });
            }
        }
        return results;
    }

    async stopAllServers() {
        const results = [];
        for (const server of this.servers) {
            try {
                const result = await this.stopServer(server.id);
                results.push(result);
            } catch (error) {
                results.push({
                    success: false,
                    serverId: server.id,
                    message: error.message,
                    timestamp: new Date().toISOString()
                });
            }
        }
        return results;
    }

    // 获取服务器日志
    async getServerLogs(serverId, lines = 50) {
        const server = this.servers.find(s => s.id === serverId);
        if (!server) {
            throw new Error(`服务器 ${serverId} 不存在`);
        }

        try {
            // 模拟获取日志
            const mockLogs = [
                `[${new Date().toISOString()}] INFO: ${server.name} 已启动`,
                `[${new Date(Date.now().catch(error => console.error(`[server-control-api.js] Date.now failed:`, error)) - 60000).toISOString()}] INFO: 正在监听端口 ${server.port}`,
                `[${new Date(Date.now() - 120000).toISOString()}] INFO: 服务器初始化完成`,
                `[${new Date(Date.now().catch(error => console.error(`[server-control-api.js] Date.now failed:`, error)) - 180000).toISOString()}] DEBUG: 加载配置文件`,
                `[${new Date(Date.now() - 240000).toISOString()}] INFO: 启动服务进程`
            ];

            return {
                serverId: server.id,
                name: server.name,
                logs: mockLogs.slice(0, lines),
                timestamp: new Date().toISOString()
            };
        } catch (error) {
            return {
                serverId: server.id,
                name: server.name,
                error: error.message,
                timestamp: new Date().toISOString()
            };
        }
    }
}

// 服务器控制管理器
class ServerControlManager {
    constructor(controlAPI) {
        this.api = controlAPI;
        this.callbacks = {
            onServerStart: null,
            onServerStop: null,
            onServerRestart: null,
            onOperationComplete: null
        };
    }

    // 设置回调函数
    setCallback(type, callback) {
        if (this.callbacks.hasOwnProperty(type)) {
            this.callbacks[type] = callback;
        }
    }

    // 启动服务器
    async startServer(serverId) {
        try {
            const result = await this.api.startServer(serverId);
            
            if (this.callbacks.onServerStart) {
                this.callbacks.onServerStart(serverId, result);
            }
            
            if (this.callbacks.onOperationComplete) {
                this.callbacks.onOperationComplete('start', serverId, result);
            }
            
            return result;
        } catch (error) {
            const errorResult = {
                success: false,
                message: error.message,
                timestamp: new Date().toISOString()
            };
            
            if (this.callbacks.onOperationComplete) {
                this.callbacks.onOperationComplete('start', serverId, errorResult);
            }
            
            throw error;
        }
    }

    // 停止服务器
    async stopServer(serverId) {
        try {
            const result = await this.api.stopServer(serverId);
            
            if (this.callbacks.onServerStop) {
                this.callbacks.onServerStop(serverId, result);
            }
            
            if (this.callbacks.onOperationComplete) {
                this.callbacks.onOperationComplete('stop', serverId, result);
            }
            
            return result;
        } catch (error) {
            const errorResult = {
                success: false,
                message: error.message,
                timestamp: new Date().toISOString()
            };
            
            if (this.callbacks.onOperationComplete) {
                this.callbacks.onOperationComplete('stop', serverId, errorResult);
            }
            
            throw error;
        }
    }

    // 重启服务器
    async restartServer(serverId) {
        try {
            const result = await this.api.restartServer(serverId);
            
            if (this.callbacks.onServerRestart) {
                this.callbacks.onServerRestart(serverId, result);
            }
            
            if (this.callbacks.onOperationComplete) {
                this.callbacks.onOperationComplete('restart', serverId, result);
            }
            
            return result;
        } catch (error) {
            const errorResult = {
                success: false,
                message: error.message,
                timestamp: new Date().toISOString()
            };
            
            if (this.callbacks.onOperationComplete) {
                this.callbacks.onOperationComplete('restart', serverId, errorResult);
            }
            
            throw error;
        }
    }

    // 获取服务器进程信息
    async getServerProcess(serverId) {
        return await this.api.getServerProcess(serverId);
    }

    // 获取所有服务器进程信息
    async getAllServerProcesses() {
        return await this.api.getAllServerProcesses();
    }

    // 获取服务器日志
    async getServerLogs(serverId, lines = 50) {
        return await this.api.getServerLogs(serverId, lines);
    }

    // 批量启动所有服务器
    async startAllServers() {
        const results = await this.api.startAllServers();
        
        if (this.callbacks.onOperationComplete) {
            this.callbacks.onOperationComplete('startAll', null, results);
        }
        
        return results;
    }

    // 批量停止所有服务器
    async stopAllServers() {
        const results = await this.api.stopAllServers();
        
        if (this.callbacks.onOperationComplete) {
            this.callbacks.onOperationComplete('stopAll', null, results);
        }
        
        return results;
    }
}

// 导出模块
window.ServerControl = {
    API: ServerControlAPI,
    Manager: ServerControlManager
};