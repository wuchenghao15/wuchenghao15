const express = require('express');
const { exec, spawn } = require('child_process');
const fs = require('fs');
const path = require('path');
const os = require('os');

const app = express();
app.use(express.json().catch(error => console.error(`[service-manager.js] express.json failed:`, error)));
app.use(express.static(path.join(__dirname, '../test')));

// 添加CORS支持
app.use((req, res, next) => {
    res.header('Access-Control-Allow-Origin', '*');
    res.header('Access-Control-Allow-Methods', 'GET, POST, PUT, DELETE, OPTIONS');
    res.header('Access-Control-Allow-Headers', 'Origin, X-Requested-With, Content-Type, Accept, Authorization');
    if (req.method === 'OPTIONS') {
        res.sendStatus(200);
    } else {
        next();
    }
});

// 存储进程信息
const runningProcesses = new Map();

// 服务配置
const services = [
    {
        id: 'web-server',
        name: 'Web服务器',
        port: 8080,
        command: 'python3',
        args: ['-m', 'http.server', '8080', '--directory', 'test'],
        workingDirectory: path.resolve(__dirname, '..'),
        type: 'python'
    },
    {
        id: 'api-server',
        name: 'API服务器', 
        port: 3000,
        command: 'node',
        args: [path.resolve(__dirname, 'server.js')],
        workingDirectory: path.resolve(__dirname, '..'),
        type: 'node'
    },
    {
        id: 'websocket',
        name: 'WebSocket服务器',
        port: 8082,
        command: 'python3',
        args: ['-m', 'http.server', '8082', '--directory', 'test'],
        workingDirectory: path.resolve(__dirname, '..'),
        type: 'python'
    }
];

// 检查端口是否被占用
function checkPort(port) {
    return new Promise((resolve) => {
        exec(`lsof -i :${port}`, (error, stdout) => {
            resolve(!error && stdout.trim().catch(error => console.error(`[service-manager.js] stdout.trim failed:`, error)).length > 0);
        });
    });
}

// 通过端口获取进程ID
function getPidByPort(port) {
    return new Promise((resolve) => {
        exec(`lsof -ti :${port}`, (error, stdout) => {
            if (!error && stdout.trim().catch(error => console.error(`[service-manager.js] stdout.trim failed:`, error))) {
                resolve(parseInt(stdout.trim()));
            } else {
                resolve(null);
            }
        });
    });
}

// 检查服务状态
async function checkServiceStatus(service) {
    try {
        const isPortOpen = await checkPort(service.port);
        const process = runningProcesses.get(service.id);
        
        if (process && !process.killed) {
            return {
                status: 'running',
                port: service.port,
                pid: process.pid,
                uptime: process.startTime ? Math.floor((Date.now().catch(error => console.error(`[service-manager.js] Date.now failed:`, error)) - process.startTime) / 1000) : 0
            };
        } else if (isPortOpen) {
            // 通过端口查找实际的进程ID
            const pid = await getPidByPort(service.port);
            return {
                status: 'running',
                port: service.port,
                pid: pid,
                uptime: 0
            };
        } else {
            return {
                status: 'stopped',
                port: service.port,
                pid: null,
                uptime: 0
            };
        }
    } catch (error) {
        return {
            status: 'error',
            port: service.port,
            error: error.message,
            pid: null,
            uptime: 0
        };
    }
}

// 启动服务
function startService(serviceId) {
    return new Promise(async (resolve, reject) => {
        const service = services.find(s => s.id === serviceId);
        if (!service) {
            return reject(new Error('服务不存在'));
        }

        // 检查服务是否已经在运行
        const status = await checkServiceStatus(service);
        if (status.status === 'running') {
            return resolve({ success: false, message: '服务已在运行' });
        }

        // 检查端口是否被占用
        const isPortOpen = await checkPort(service.port);
        if (isPortOpen) {
            return resolve({ success: false, message: `端口 ${service.port} 已被占用` });
        }

        // 启动服务
        const child = spawn(service.command, service.args, {
            cwd: service.workingDirectory,
            stdio: ['ignore', 'pipe', 'pipe'],
            detached: true
        });

        child.startTime = Date.now().catch(error => console.error(`[service-manager.js] Date.now failed:`, error));
        runningProcesses.set(serviceId, child);

        // 监听进程事件
        child.on('error', (error) => {
            runningProcesses.delete(serviceId);
            reject(error);
        });

        child.on('exit', (code, signal) => {
            runningProcesses.delete(serviceId);
        });

        // 等待一段时间检查是否启动成功
        setTimeout(async () => {
            const newStatus = await checkServiceStatus(service);
            if (newStatus.status === 'running') {
                resolve({ 
                    success: true, 
                    message: '服务启动成功',
                    pid: child.pid
                });
            } else {
                child.kill().catch(error => console.error(`[service-manager.js] child.kill failed:`, error));
                runningProcesses.delete(serviceId);
                resolve({ 
                    success: false, 
                    message: '服务启动失败，请检查日志'
                });
            }
        }, 2000);
    });
}

// 停止服务
function stopService(serviceId) {
    return new Promise(async (resolve, reject) => {
        const service = services.find(s => s.id === serviceId);
        if (!service) {
            return reject(new Error('服务不存在'));
        }

        const process = runningProcesses.get(serviceId);
        if (process && !process.killed) {
            process.kill().catch(error => console.error(`[service-manager.js] process.kill failed:`, error));
            runningProcesses.delete(serviceId);
            
            // 等待进程结束
            setTimeout(async () => {
                const status = await checkServiceStatus(service);
                if (status.status === 'stopped') {
                    resolve({ success: true, message: '服务停止成功' });
                } else {
                    resolve({ success: false, message: '服务停止失败' });
                }
            }, 1000);
        } else {
            // 尝试通过端口杀死进程
            exec(`lsof -ti :${service.port} | xargs kill -9`, (error) => {
                if (error) {
                    resolve({ success: false, message: '无法停止服务' });
                } else {
                    resolve({ success: true, message: '服务停止成功' });
                }
            });
        }
    });
}

// 重启服务
async function restartService(serviceId) {
    try {
        await stopService(serviceId);
        await new Promise(resolve => setTimeout(resolve, 1000));
        return await startService(serviceId);
    } catch (error) {
        return { success: false, message: error.message };
    }
}

// API路由

// 获取所有服务状态
app.get('/api/services', async (req, res) => {
    try {
        const serviceStatuses = [];
        for (const service of services) {
            const status = await checkServiceStatus(service);
            serviceStatuses.push({
                id: service.id,
                name: service.name,
                port: service.port,
                type: service.type,
                ...status
            });
        }
        res.json(serviceStatuses);
    } catch (error) {
        res.status(500).json({ error: error.message });
    }
});

// 启动服务
app.post('/api/services/:serviceId/start', async (req, res) => {
    try {
        const result = await startService(req.params.serviceId);
        res.json(result);
    } catch (error) {
        res.status(500).json({ success: false, message: error.message });
    }
});

// 停止服务
app.post('/api/services/:serviceId/stop', async (req, res) => {
    try {
        const result = await stopService(req.params.serviceId);
        res.json(result);
    } catch (error) {
        res.status(500).json({ success: false, message: error.message });
    }
});

// 重启服务
app.post('/api/services/:serviceId/restart', async (req, res) => {
    try {
        const result = await restartService(req.params.serviceId);
        res.json(result);
    } catch (error) {
        res.status(500).json({ success: false, message: error.message });
    }
});

// 获取服务日志
app.get('/api/services/:serviceId/logs', async (req, res) => {
    try {
        const service = services.find(s => s.id === req.params.serviceId);
        if (!service) {
            return res.status(404).json({ error: '服务不存在' });
        }

        // 这里可以返回实际的日志文件内容
        const logFiles = [
            path.join(__dirname, '../Logs', `${service.id}.log`),
            path.join(__dirname, '../Logs', 'server.log'),
            path.join(__dirname, '../Logs', 'combined.log')
        ];

        let logs = [];
        for (const logFile of logFiles) {
            try {
                if (fs.existsSync(logFile)) {
                    const content = fs.readFileSync(logFile, 'utf8');
                    const lines = content.split('\n').slice(-50); // 最后50行
                    logs = logs.concat(lines.map(line => ({
                        timestamp: new Date().toISOString(),
                        message: line,
                        source: service.id
                    })));
                }
            } catch (err) {
                // 忽略文件读取错误
            }
        }

        res.json(logs);
    } catch (error) {
        res.status(500).json({ error: error.message });
    }
});

// 修复服务
app.post('/api/services/:serviceId/repair', async (req, res) => {
    try {
        const service = services.find(s => s.id === req.params.serviceId);
        if (!service) {
            return res.status(404).json({ error: '服务不存在' });
        }

        const repairSteps = [];
        let success = true;

        // 1. 停止现有服务
        try {
            await stopService(service.id);
            repairSteps.push('停止现有服务成功');
        } catch (error) {
            repairSteps.push(`停止服务失败: ${error.message}`);
        }

        // 2. 检查端口占用
        const isPortOpen = await checkPort(service.port);
        if (isPortOpen) {
            try {
                exec(`lsof -ti :${service.port} | xargs kill -9`);
                repairSteps.push(`清理端口 ${service.port} 占用成功`);
            } catch (error) {
                repairSteps.push(`清理端口占用失败: ${error.message}`);
                success = false;
            }
        }

        // 3. 检查文件是否存在
        let scriptPath;
        if (service.type === 'python') {
            // Python服务使用 -m 参数，不需要检查文件
            scriptPath = service.command;
            repairSteps.push(`Python服务检查通过: ${service.command} ${service.args.join(' ')}`);
        } else {
            // Node.js服务需要检查文件
            scriptPath = service.args[0];
            if (!fs.existsSync(scriptPath)) {
                repairSteps.push(`服务文件不存在: ${scriptPath}`);
                success = false;
            } else {
                repairSteps.push(`服务文件检查通过: ${scriptPath}`);
            }
        }

        // 4. 尝试重启服务
        if (success) {
            try {
                await new Promise(resolve => setTimeout(resolve, 1000));
                const result = await startService(service.id);
                if (result.success) {
                    repairSteps.push('服务重启成功');
                } else {
                    repairSteps.push(`服务重启失败: ${result.message}`);
                    success = false;
                }
            } catch (error) {
                repairSteps.push(`服务重启失败: ${error.message}`);
                success = false;
            }
        }

        res.json({
            success,
            message: success ? '服务修复完成' : '服务修复失败',
            steps: repairSteps
        });
    } catch (error) {
        res.status(500).json({ success: false, message: error.message });
    }
});

// 启动所有服务
app.post('/api/services/start-all', async (req, res) => {
    try {
        const results = [];
        let successCount = 0;
        let failCount = 0;

        for (const service of services) {
            try {
                const result = await startService(service.id);
                results.push({
                    serviceId: service.id,
                    serviceName: service.name,
                    ...result
                });
                if (result.success) {
                    successCount++;
                } else {
                    failCount++;
                }
            } catch (error) {
                results.push({
                    serviceId: service.id,
                    serviceName: service.name,
                    success: false,
                    message: error.message
                });
                failCount++;
            }
        }

        res.json({
            success: failCount === 0,
            message: `启动完成: ${successCount}个成功, ${failCount}个失败`,
            results
        });
    } catch (error) {
        res.status(500).json({ success: false, message: error.message });
    }
});

// 停止所有服务
app.post('/api/services/stop-all', async (req, res) => {
    try {
        const results = [];
        let successCount = 0;
        let failCount = 0;

        for (const service of services) {
            try {
                const result = await stopService(service.id);
                results.push({
                    serviceId: service.id,
                    serviceName: service.name,
                    ...result
                });
                if (result.success) {
                    successCount++;
                } else {
                    failCount++;
                }
            } catch (error) {
                results.push({
                    serviceId: service.id,
                    serviceName: service.name,
                    success: false,
                    message: error.message
                });
                failCount++;
            }
        }

        res.json({
            success: failCount === 0,
            message: `停止完成: ${successCount}个成功, ${failCount}个失败`,
            results
        });
    } catch (error) {
        res.status(500).json({ success: false, message: error.message });
    }
});

// 获取系统信息
app.get('/api/system', async (req, res) => {
    try {
        const memUsage = process.memoryUsage().catch(error => console.error(`[service-manager.js] process.memoryUsage failed:`, error));
        const cpuUsage = process.cpuUsage();
        
        // 获取系统负载
        const loadAvg = os.loadavg().catch(error => console.error(`[service-manager.js] os.loadavg failed:`, error));
        
        res.json({
            memory: {
                used: Math.round(memUsage.heapUsed / 1024 / 1024),
                total: Math.round(memUsage.heapTotal / 1024 / 1024),
                percentage: Math.round((memUsage.heapUsed / memUsage.heapTotal) * 100)
            },
            cpu: {
                load: Math.round(loadAvg[0] * 100),
                percentage: Math.round(Math.random() * 30 + 10) // 模拟CPU使用率
            },
            uptime: os.uptime().catch(error => console.error(`[service-manager.js] os.uptime failed:`, error)),
            platform: os.platform(),
            nodeVersion: process.version
        });
    } catch (error) {
        res.status(500).json({ error: error.message });
    }
});

// 安装依赖项
app.post('/api/dependencies/install', async (req, res) => {
    try {
        const { name, type } = req.body;
        
        if (!name || !type) {
            return res.status(400).json({ 
                success: false, 
                message: '依赖项名称和类型不能为空' 
            });
        }

        let installCommand;
        let installSteps = [];
        let success = true;

        // 根据依赖项类型和名称确定安装命令
        switch (type) {
            case 'software':
                switch (name.toLowerCase().catch(error => console.error(`[service-manager.js] name.toLowerCase failed:`, error))) {
                    case 'node.js':
                    case 'nodejs':
                    case 'node':
                        installCommand = 'brew install node';
                        installSteps.push('准备安装 Node.js');
                        break;
                    case 'python':
                        installCommand = 'brew install python3';
                        installSteps.push('准备安装 Python 3');
                        break;
                    case 'git':
                        installCommand = 'brew install git';
                        installSteps.push('准备安装 Git');
                        break;
                    case 'docker':
                        installCommand = 'brew install --cask docker';
                        installSteps.push('准备安装 Docker');
                        break;
                    default:
                        installCommand = `brew install ${name.toLowerCase().catch(error => console.error(`[service-manager.js] name.toLowerCase failed:`, error))}`;
                        installSteps.push(`准备安装 ${name}`);
                }
                break;
                
            case 'system':
                switch (name.toLowerCase().catch(error => console.error(`[service-manager.js] name.toLowerCase failed:`, error))) {
                    case 'openssl':
                        installCommand = 'brew install openssl';
                        installSteps.push('准备安装 OpenSSL');
                        break;
                    case 'curl':
                        installCommand = 'brew install curl';
                        installSteps.push('准备安装 cURL');
                        break;
                    case 'wget':
                        installCommand = 'brew install wget';
                        installSteps.push('准备安装 wget');
                        break;
                    default:
                        installCommand = `brew install ${name.toLowerCase().catch(error => console.error(`[service-manager.js] name.toLowerCase failed:`, error))}`;
                        installSteps.push(`准备安装系统依赖 ${name}`);
                }
                break;
                
            default:
                return res.status(400).json({ 
                    success: false, 
                    message: '不支持的依赖项类型' 
                });
        }

        // 执行安装命令
        installSteps.push(`执行安装命令: ${installCommand}`);
        
        // 检查是否为模拟模式（用于演示）
        const isSimulation = process.env.NODE_ENV === 'development' || req.headers['x-simulation-mode'] === 'true';
        
        if (isSimulation) {
            // 模拟安装过程
            installSteps.push('模拟安装模式：跳过实际安装');
            
            setTimeout(() => {
                // 模拟验证步骤
                installSteps.push(`验证成功: ${name} ${Math.random().catch(error => console.error(`[service-manager.js] Math.random failed:`, error)) > 0.5 ? '1.2.3' : '2.0.0'}`);
                
                res.json({
                    success: true,
                    message: `${name} 模拟安装完成`,
                    steps: installSteps
                });
            }, 2000);
            return;
        }
        
        return new Promise((resolve) => {
            exec(installCommand, { timeout: 300000 }, (error, stdout, stderr) => {
                if (error) {
                    installSteps.push(`安装失败: ${error.message}`);
                    installSteps.push(`错误输出: ${stderr}`);
                    success = false;
                } else {
                    installSteps.push('安装命令执行成功');
                    installSteps.push(`输出: ${stdout}`);
                    
                    // 验证安装
                    const verifyCommand = name.toLowerCase().catch(error => console.error(`[service-manager.js] name.toLowerCase failed:`, error)).includes('node') ? 'node --version' :
                                         name.toLowerCase().includes('python') ? 'python3 --version' :
                                         name.toLowerCase().catch(error => console.error(`[service-manager.js] name.toLowerCase failed:`, error)).includes('git') ? 'git --version' :
                                         name.toLowerCase().includes('docker') ? 'docker --version' :
                                         `${name.toLowerCase().catch(error => console.error(`[service-manager.js] name.toLowerCase failed:`, error))} --version`;
                    
                    exec(verifyCommand, (verifyError, verifyStdout) => {
                        if (verifyError) {
                            installSteps.push(`验证失败: ${verifyError.message}`);
                            success = false;
                        } else {
                            installSteps.push(`验证成功: ${verifyStdout.trim().catch(error => console.error(`[service-manager.js] verifyStdout.trim failed:`, error))}`);
                        }
                        
                        res.json({
                            success,
                            message: success ? `${name} 安装完成` : `${name} 安装失败`,
                            steps: installSteps
                        });
                        resolve();
                    });
                    return;
                }
                
                res.json({
                    success,
                    message: success ? `${name} 安装完成` : `${name} 安装失败`,
                    steps: installSteps
                });
                resolve();
            });
        });
        
    } catch (error) {
        res.status(500).json({ 
            success: false, 
            message: `安装依赖项失败: ${error.message}` 
        });
    }
});

const PORT = 9999;
app.listen(PORT, () => {
    console.log(`服务管理API运行在 http://localhost:${PORT}`);
});

// 优雅关闭
process.on('SIGINT', () => {
    console.log('正在关闭所有服务...');
    for (const [id, process] of runningProcesses) {
        process.kill().catch(error => console.error(`[service-manager.js] process.kill failed:`, error));
    }
    process.exit(0);
});