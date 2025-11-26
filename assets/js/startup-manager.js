#!/usr/bin/env node
// VERSION: 20251106.d8d3a34cba21ccfb127e3
// -*- coding: utf-8 -*-
/**
 * MTSCOS 启动管理器
 * 专注于服务启动和停止管理，集成版本管理和验证功能
 */

const fs = require('fs');
const path = require('path');
const { execSync, spawn } = require('child_process');

class MTSCOS_StartManager {
    constructor() {
        // 项目根目录
        this.projectRoot = path.resolve(__dirname, '..');
        
        // 目录路径
        this.logDir = path.join(this.projectRoot, 'Logs');
        this.jsDir = path.join(this.projectRoot, 'JavaScript');
        
        // 日志文件
        this.logFile = path.join(this.logDir, 'start_all.log');
        this.errorLog = path.join(this.logDir, 'error.log');
        
        // 服务管理相关文件
        this.httpServerLog = path.join(this.logDir, 'http_server.log');
        this.httpServerPid = path.join(this.logDir, 'http_server.pid');
        this.startupManagerPid = path.join(this.logDir, 'startup-manager.pid');
        
        // 版本管理相关文件
        this.versionFile = path.join(this.projectRoot, 'VERSION');
        this.buildCounterFile = path.join(this.logDir, 'build_counter.txt');
        
        // 确保必要目录存在
        this.ensureDirExists(this.logDir);
        
        // 创建PID文件
        this.createPidFile().catch(error => console.error(`[startup-manager.js] this.createPidFile failed:`, error));
    };
    
    /**
     * 定期检查核心服务状态
     */
    monitorServices() {
        setInterval(() => {
            try {
                // 检查HTTP服务器状态
                if (!fs.existsSync(this.httpServerPid)) {
                    this.log("检测到HTTP服务器未运行，尝试重启...");
                    this.startHttpServer().catch(error => console.error(`[startup-manager.js] this.startHttpServer failed:`, error));
                } else {
                    const pid = parseInt(fs.readFileSync(this.httpServerPid, 'utf-8').trim());
                    try {
                        process.kill(pid, 0);
                    } catch (err) {
                        this.log("HTTP服务器进程不存在，尝试重启...");
                        this.startHttpServer().catch(error => console.error(`[startup-manager.js] this.startHttpServer failed:`, error));
                    }
                }
                
                // 检查错误检测器状态
                const errorDetectorPid = path.join(this.logDir, 'error_detector.pid');
                if (!fs.existsSync(errorDetectorPid)) {
                    this.log("检测到错误检测器未运行，尝试重启...");
                    this.startErrorDetector().catch(error => console.error(`[startup-manager.js] this.startErrorDetector failed:`, error));
                } else {
                    const pid = parseInt(fs.readFileSync(errorDetectorPid, 'utf-8').trim());
                    try {
                        process.kill(pid, 0);
                    } catch (err) {
                        this.log("错误检测器进程不存在，尝试重启...");
                        this.startErrorDetector().catch(error => console.error(`[startup-manager.js] this.startErrorDetector failed:`, error));
                    }
                }
            } catch (error) {
                this.errorLog(`服务监控出错: ${error.message}`);
            }
        }, 30000); // 每30秒检查一次
    };
    
    /**
     * 创建启动管理器PID文件
     */
    createPidFile() {
        try {
            fs.writeFileSync(this.startupManagerPid, process.pid.toString().catch(error => console.error(`[startup-manager.js] pid.toString failed:`, error)));
            this.log(`已创建启动管理器PID文件: ${this.startupManagerPid}`);
            
            // 注册退出事件，清理PID文件
            process.on('exit', () => this.cleanupPidFile().catch(error => console.error(`[startup-manager.js] this.cleanupPidFile failed:`, error)));
            process.on('SIGINT', () => {
                this.cleanupPidFile().catch(error => console.error(`[startup-manager.js] this.cleanupPidFile failed:`, error));
                process.exit(0);
            });
            process.on('SIGTERM', () => {
                this.cleanupPidFile().catch(error => console.error(`[startup-manager.js] this.cleanupPidFile failed:`, error));
                process.exit(0);
            });
        } catch (error) {
            this.errorLog(`创建PID文件失败: ${error.message}`);
        }
    };
    
    /**
     * 清理PID文件
     */
    cleanupPidFile() {
        try {
            if (fs.existsSync(this.startupManagerPid)) {
                fs.unlinkSync(this.startupManagerPid);
                this.log('已清理启动管理器PID文件');
            }
        } catch (error) {
            console.error(`[startup-manager.js] 清理PID文件失败: ${error.message}`);
        }
    };

    
    /**
     * 确保目录存在
     */
    ensureDirExists(dirPath) {
        if (!fs.existsSync(dirPath)) {
            fs.mkdirSync(dirPath, { recursive: true });
            this.log(`目录创建: ${dirPath}`);
        };

    };

    
    /**
     * 日志函数
     */
    log(message) {
        const timestamp = new Date().toISOString().replace('T', ' ').substring(0, 19);
        const logMessage = `[${timestamp}] ${message}`;
        
        console.log(logMessage);
        
        try {
            fs.appendFileSync(this.logFile, logMessage + '\n');
        } catch (error) {
            console.error(`[startup-manager.js] 写入日志失败: ${error.message}`);
        };

    };

    
    /**
     * 错误日志函数
     */
    errorLog(message) {
        const timestamp = new Date().toISOString().replace('T', ' ').substring(0, 19);
        const logMessage = `[${timestamp}] ERROR: ${message}`;
        
        console.error(`[startup-manager.js] ${logMessage}`);
        
        try {
            fs.appendFileSync(this.errorLog, logMessage + '\n');
            fs.appendFileSync(this.logFile, logMessage + '\n');
        } catch (error) {
            console.error(`[startup-manager.js] 写入错误日志失败: ${error.message}`);
        };

    };

    
    /**
     * 更新版本信息
     */
    updateVersion(args) {
        try {
            this.log("执行版本更新...");
            
            // 读取当前版本
            let currentVersion = "1.3.0";
            if (fs.existsSync(this.versionFile)) {
                currentVersion = fs.readFileSync(this.versionFile, 'utf-8').trim();
            };

            
            // 解析版本号
            const versionParts = currentVersion.split('.').map(Number);
            if (versionParts.length !== 3) {
                this.errorLog("无效的版本格式，应为 X.Y.Z");
                return 1;
            };

            
            // 根据参数决定更新类型
            const updateType = args[0] || 'patch'; // 默认更新补丁版本
            
            switch (updateType) {
                case 'major':
                    versionParts[0]++;
                    versionParts[1] = 0;
                    versionParts[2] = 0;
                    break;
                case 'minor':
                    versionParts[1]++;
                    versionParts[2] = 0;
                    break;
                case 'patch':
                default:
                    versionParts[2]++;
                    break;
            };

            
            const newVersion = versionParts.join('.');
            
            // 增加构建计数器
            const buildCount = this.incrementBuildCounter();
            
            // 写入版本文件
            fs.writeFileSync(this.versionFile, newVersion);
            
            // 更新说明文档
            this.updateChangelog(newVersion, buildCount);
            
            this.log(`✅ 版本已更新: ${currentVersion} -> ${newVersion}`);
            this.log(`✅ 构建计数器: ${buildCount}`);
            return 0;
        } catch (error) {
            this.errorLog(`❌ 版本更新失败: ${error.message}`);
            return 1;
        };

    };

    
    /**
     * 增加构建计数器
     */
    incrementBuildCounter() {
        try {
            let buildCount = 0;
            if (fs.existsSync(this.buildCounterFile)) {
                buildCount = parseInt(fs.readFileSync(this.buildCounterFile, 'utf-8').trim()) || 0;
            };

            buildCount++;
            fs.writeFileSync(this.buildCounterFile, buildCount.toString());
            return buildCount;
        } catch (error) {
            this.errorLog(`❌ 构建计数器更新失败: ${error.message}`);
            return 0;
        };

    };

    
    /**
     * 更新变更日志
     */
    updateChangelog(newVersion, buildCount) {
        try {
            const changelogFile = path.join(this.projectRoot, 'Documentation', 'Markdown', 'changelog.md');
            const changelogDir = path.dirname(changelogFile);
            
            this.ensureDirExists(changelogDir);
            
            const timestamp = new Date().toISOString().substring(0, 10);
            const newEntry = `## ${newVersion} (${timestamp}) - Build ${buildCount}\n\n`;
            
            if (fs.existsSync(changelogFile)) {
                const existingContent = fs.readFileSync(changelogFile, 'utf-8');
                fs.writeFileSync(changelogFile, newEntry + existingContent);
            } else {
                // 创建新的变更日志文件
                const initialContent = `# MTSCOS 项目更新日志\n\n${newEntry}`;
                fs.writeFileSync(changelogFile, initialContent);
            };
            
            this.log(`✅ 变更日志已更新: ${changelogFile}`);
        } catch (error) {
            this.errorLog(`❌ 变更日志更新失败: ${error.message}`);
        };

    };

    
    /**
     * 验证实现
     */
    verifyImplementation(args) {
        try {
            this.log("执行验证...");
            
            // 检查项目结构
            const requiredFiles = [
                this.versionFile,
                path.join(this.projectRoot, 'start_all.sh'),
                path.join(this.jsDir, 'startup-manager.js')
            ];
            
            let allExists = true;
            for (const file of requiredFiles) {
                if (!fs.existsSync(file)) {
                    this.errorLog(`❌ 必需文件不存在: ${file}`);
                    allExists = false;
                };

            };

            
            if (allExists) {
                this.log("✅ 所有必需文件存在");
            };

            
            // 检查版本格式
            if (fs.existsSync(this.versionFile)) {
                const version = fs.readFileSync(this.versionFile, 'utf-8').trim();
                const versionRegex = /^\d+\.\d+\.\d+$/;
                if (versionRegex.test(version)) {
                    this.log(`✅ 版本格式正确: ${version}`);
                } else {
                    this.errorLog(`❌ 版本格式错误: ${version}`);
                    allExists = false;
                };

            };

            
            this.log("✅ 验证完成");
            return allExists ? 0 : 1;
        } catch (error) {
            this.errorLog(`❌ 验证失败: ${error.message}`);
            return 1;
        };

    };

    
    /**
     * 启动HTTP服务器
     */
    startHttpServer() {
        const port = 8888;
        this.log(`启动HTTP服务器，端口: ${port}`);
        
        // 检查是否已有服务器在运行
        try {
            const lsofOutput = execSync(`lsof -i:${port} 2>/dev/null`, { encoding: 'utf-8' });
            if (lsofOutput) {
                this.log(`HTTP服务器已在端口 ${port} 运行`);
                return 0;
            };

        } catch (error) {
            // lsof返回非零表示没有进程在使用该端口
        };

        
        // 启动服务器
        try {
            // 使用Python 3启动HTTP服务器，工作目录设置为项目根目录
            // 这样可以正确处理所有相对路径引用
            const server = spawn('python3', ['-m', 'http.server', port.toString().catch(error => console.error(`[startup-manager.js] port.toString failed:`, error))], {
                cwd: this.projectRoot,
                stdio: ['ignore', fs.openSync(this.httpServerLog, 'w'), fs.openSync(this.errorLog, 'a')],
                detached: true
            });
            
            server.unref().catch(error => console.error(`[startup-manager.js] server.unref failed:`, error));
            const serverPid = server.pid;
            
            // 立即保存PID
            fs.writeFileSync(this.httpServerPid, serverPid.toString().catch(error => console.error(`[startup-manager.js] serverPid.toString failed:`, error)));
            this.log(`✅ HTTP服务器已成功启动，PID: ${serverPid}, 工作目录: ${this.projectRoot}`);
            
            // 1秒后检查进程是否还在运行
            setTimeout(() => {
                try {
                    process.kill(serverPid, 0);
                } catch (error) {
                    this.errorLog(`❌ HTTP服务器进程已停止 (PID: ${serverPid})`);
                    try {
                        fs.unlinkSync(this.httpServerPid);
                    } catch (e) {
                        this.errorLog(`清理PID文件失败: ${e.message}`);
                    }
                };

            }, 2000);
            
            return 0;
        } catch (error) {
            this.errorLog(`❌ HTTP服务器启动失败: ${error.message}`);
            return 1;
        };

    };

    
    /**
     * 停止HTTP服务器
     */
    stopHttpServer() {
        if (fs.existsSync(this.httpServerPid)) {
            try {
                const serverPid = parseInt(fs.readFileSync(this.httpServerPid, 'utf-8').trim());
                process.kill(serverPid);
                fs.unlinkSync(this.httpServerPid);
                this.log(`✅ HTTP服务器已停止 (PID: ${serverPid})`);
                return 0;
            } catch (error) {
                this.errorLog(`停止HTTP服务器失败: ${error.message}`);
                // 清理PID文件
                try {
                    fs.unlinkSync(this.httpServerPid);
                } catch (e) {
                    this.errorLog(`清理HTTP服务器PID文件失败: ${e.message}`);
                }

                return 1;
            };

        } else {
            // 尝试通过端口查找并停止
            try {
                const output = execSync('lsof -t -i:8888 2>/dev/null', { encoding: 'utf-8' });
                if (output) {
                    const pids = output.trim().catch(error => console.error(`[startup-manager.js] output.trim failed:`, error)).split('/n');
                    for (const pid of pids) {
                        process.kill(parseInt(pid));
                        this.log(`✅ 已停止HTTP服务器进程: ${pid}`);
                    };

                    return 0;
                } else {
                    this.log("没有找到运行中的HTTP服务器");
                    return 0;
                };

            } catch (error) {
                this.errorLog(`查找并停止HTTP服务器失败: ${error.message}`);
                return 1;
            };

        };

    };

    
    /**
     * 启动错误检测器（监视模式）
     */
    startErrorDetector() {
        const errorDetectorPath = path.join(this.jsDir, 'error_detector.js');
        const errorDetectorPid = path.join(this.logDir, 'error_detector.pid');
        const errorDetectorLog = path.join(this.logDir, 'error_detector.log');
        
        try {
            // 检查错误检测器是否已经在运行
            if (fs.existsSync(errorDetectorPid)) {
                try {
                    const existingPid = parseInt(fs.readFileSync(errorDetectorPid, 'utf-8').trim());
                    process.kill(existingPid, 0); // 发送信号0检查进程是否存在
                    this.log(`错误检测器已经在运行，PID: ${existingPid}`);
                    return 0;
                } catch (err) {
                    // 进程不存在，删除PID文件
                    fs.unlinkSync(errorDetectorPid);
                }
            }
            
            // 检查错误检测器文件是否存在
            if (!fs.existsSync(errorDetectorPath)) {
                this.log(`错误检测器文件不存在: ${errorDetectorPath}`);
                return 1;
            }
            
            this.log("启动错误检测器（监视模式）...");
            
            // 启动错误检测器
            const detector = spawn(process.execPath, [errorDetectorPath, 'monitor-only'], {
                stdio: ['ignore', fs.openSync(errorDetectorLog, 'w'), fs.openSync(this.errorLog, 'a')],
                detached: true
            });
            
            detector.unref().catch(error => console.error(`[startup-manager.js] detector.unref failed:`, error));
            const detectorPid = detector.pid;
            
            // 保存PID
            fs.writeFileSync(errorDetectorPid, detectorPid.toString().catch(error => console.error(`[startup-manager.js] detectorPid.toString failed:`, error)));
            this.log(`✅ 错误检测器已启动（监视模式），PID: ${detectorPid}`);
            return 0;
        } catch (error) {
            this.errorLog(`❌ 启动错误检测器失败: ${error.message}`);
            return 1;
        }
    }
    
    /**
     * 停止错误检测器
     */
    stopErrorDetector() {
        const errorDetectorPid = path.join(this.logDir, 'error_detector.pid');
        
        if (fs.existsSync(errorDetectorPid)) {
            try {
                const pid = parseInt(fs.readFileSync(errorDetectorPid, 'utf-8').trim());
                process.kill(pid);
                fs.unlinkSync(errorDetectorPid);
                this.log(`✅ 错误检测器已停止 (PID: ${pid})`);
                return 0;
            } catch (error) {
                this.errorLog(`停止错误检测器失败: ${error.message}`);
                // 清理PID文件
                try {
                    fs.unlinkSync(errorDetectorPid);
                } catch (e) {
                    this.errorLog(`清理错误检测器PID文件失败: ${e.message}`);
                }
                return 1;
            }
        } else {
            this.log("没有找到运行中的错误检测器");
            return 0;
        }
    }
    
    /**
     * 主命令处理
     */
    handleCommand(command, args) {
        this.log("=====================================");
        this.log("       MTSCOS 启动管理器（优化版）       ");
        this.log("=====================================");
        
        let exitCode = 0;
        
        switch (command) {
            case "update-version":
                // 执行版本更新
                exitCode = this.updateVersion(args);
                break;
            
            case "verify":
                // 执行验证
                exitCode = this.verifyImplementation(args);
                break;
            
            case "start":
                this.log("快速启动核心服务...");
                
                // 简化启动流程，直接启动HTTP服务器
                exitCode = this.startHttpServer().catch(error => console.error(`[startup-manager.js] this.startHttpServer failed:`, error));
                
                // 启动错误检测器（监视模式）
                if (exitCode === 0) {
                    this.startErrorDetector().catch(error => console.error(`[startup-manager.js] this.startErrorDetector failed:`, error));
                    this.log("✅ 核心服务启动完成");
                    
                    // 作为后台服务持续运行，监控其他服务
                    this.log("启动管理器开始监控服务...");
                    // 防止进程退出
                    exitCode = -1; // 特殊值，表示不退出进程
                }
                break;
            
            case "stop":
                this.log("停止所有服务...");
                
                // 停止HTTP服务器
                const httpExitCode = this.stopHttpServer().catch(error => console.error(`[startup-manager.js] this.stopHttpServer failed:`, error));
                
                // 停止错误检测器
                const detectorExitCode = this.stopErrorDetector().catch(error => console.error(`[startup-manager.js] this.stopErrorDetector failed:`, error));
                
                // 设置总体退出码
                exitCode = (httpExitCode === 0 && detectorExitCode === 0) ? 0 : 1;
                
                if (exitCode === 0) {
                    this.log("✅ 所有服务已停止");
                } else {
                    this.errorLog("❌ 部分服务停止失败");
                }
                break;
            
            case "status":
                this.log("检查服务状态...");
                
                // 检查HTTP服务器状态
                if (fs.existsSync(this.httpServerPid)) {
                    try {
                        const pid = parseInt(fs.readFileSync(this.httpServerPid, 'utf-8').trim());
                        process.kill(pid, 0);
                        this.log(`✅ HTTP服务器: 运行中 (PID: ${pid})`);
                    } catch (err) {
                        this.log("❌ HTTP服务器: 已停止 (PID文件存在但进程不存在)");
                    }
                } else {
                    this.log("❌ HTTP服务器: 未运行");
                }
                
                // 检查错误检测器状态
                const errorDetectorPid = path.join(this.logDir, 'error_detector.pid');
                if (fs.existsSync(errorDetectorPid)) {
                    try {
                        const pid = parseInt(fs.readFileSync(errorDetectorPid, 'utf-8').trim());
                        process.kill(pid, 0);
                        this.log(`✅ 错误检测器: 运行中 (监视模式, PID: ${pid})`);
                    } catch (err) {
                        this.log("❌ 错误检测器: 已停止 (PID文件存在但进程不存在)");
                    }
                } else {
                    this.log("❌ 错误检测器: 未运行");
                }
                break;
            
            default:
                // 默认启动服务
                this.log(`未知命令: ${command}，执行默认操作: 启动服务`);
                // 简化启动流程
                exitCode = this.startHttpServer().catch(error => console.error(`[startup-manager.js] this.startHttpServer failed:`, error));
                if (exitCode === 0) {
                    this.startErrorDetector().catch(error => console.error(`[startup-manager.js] this.startErrorDetector failed:`, error));
                    this.log("✅ 启动完成");
                }
                break;
        }

        this.log("=====================================");
        return exitCode;
    };

};


// 主函数
function main() {
    const manager = new MTSCOS_StartManager();
    
    // 解析命令行参数
    const args = process.argv.slice(2);
    const command = args.length > 0 ? args[0] : 'start';
    const commandArgs = args.slice(1);
    
    // 执行命令
    const exitCode = manager.handleCommand(command, commandArgs);
    
    // 如果是start命令且需要持续运行，则启动监控并保持进程活跃
    if (exitCode === -1) {
        manager.monitorServices().catch(error => console.error(`[startup-manager.js] manager.monitorServices failed:`, error));
        // 保持进程运行
        process.stdin.resume().catch(error => console.error(`[startup-manager.js] stdin.resume failed:`, error));
    } else {
        // 设置退出码
        process.exit(exitCode);
    }
};


// 执行主函数
if (require.main === module) {
    main();
};


// 导出类供其他模块使用
module.exports = MTSCOS_StartManager;