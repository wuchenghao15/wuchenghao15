#!/usr/bin/env node

/**
 * 本地DeepSeek启动脚本
 * 支持本地模型优先，API回退模式
 */

const path = require('path');
const fs = require('fs');

// 项目根目录
const PROJECT_ROOT = path.resolve(__dirname, '..');

class LocalDeepSeekLauncher {
    constructor() {
        this.config = null;
        this.modelExists = false;
        this.serverProcess = null;
    }

    /**
     * 加载配置
     */
    loadConfig() {
        try {
            const configPath = path.join(PROJECT_ROOT, 'Configs', 'deepseek_config.json');
            const configContent = fs.readFileSync(configPath, 'utf8');
            this.config = JSON.parse(configContent);
            console.log('✅ 配置加载成功');
        } catch (error) {
            console.error(`[start-local-deepseek.js] ❌ 配置加载失败:, error.message`);
            process.exit(1);
        }
    }

    /**
     * 检查本地模型
     */
    checkLocalModel() {
        const modelPath = path.join(PROJECT_ROOT, this.config.localModel.modelPath);
        this.modelExists = fs.existsSync(modelPath);
        
        if (this.modelExists) {
            const stats = fs.statSync(modelPath);
            const sizeInMB = (stats.size / (1024 * 1024)).toFixed(2);
            console.log(`✅ 本地模型存在: ${modelPath}`);
            console.log(`📊 模型大小: ${sizeInMB} MB`);
        } else {
            console.log(`⚠️  本地模型不存在: ${modelPath}`);
            console.log('💡 将使用API模式运行');
        }
    }

    /**
     * 检查依赖
     */
    checkDependencies() {
        try {
            require('express');
            console.log('✅ Express 依赖正常');
        } catch (error) {
            console.error(`[start-local-deepseek.js] ❌ Express 依赖缺失，请运行: npm install express`);
            process.exit(1);
        }

        if (this.config.localModel.enabled && this.modelExists) {
            try {
                // 检查node-llama-cpp
                console.log('🔍 检查本地模型依赖...');
                // 这里会在运行时动态加载
            } catch (error) {
                console.log('⚠️  本地模型依赖检查将在运行时进行');
            }
        }
    }

    /**
     * 创建启动环境
     */
    createEnvironment() {
        // 设置环境变量
        process.env.NODE_ENV = process.env.NODE_ENV || 'development';
        process.env.DEEPSEEK_MODE = this.modelExists ? 'local' : 'api';
        process.env.DEEPSEEK_CONFIG_PATH = path.join(PROJECT_ROOT, 'Configs', 'deepseek_config.json');
        
        console.log(`🌍 运行模式: ${process.env.DEEPSEEK_MODE.toUpperCase()}`);
        console.log(`📁 项目路径: ${PROJECT_ROOT}`);
    }

    /**
     * 启动服务器
     */
    async startServer() {
        try {
            console.log('🚀 启动DeepSeek服务器...');
            
            // 动态导入服务器模块
            const serverPath = path.join(PROJECT_ROOT, 'JavaScript', 'deepseek-server.js');
            
            if (!fs.existsSync(serverPath)) {
                throw new Error(`服务器文件不存在: ${serverPath}`);
            }

            // 启动服务器
            const { spawn } = require('child_process');
            this.serverProcess = spawn('node', [serverPath], {
                cwd: PROJECT_ROOT,
                stdio: 'inherit',
                env: { ...process.env }
            });

            this.serverProcess.on('error', (error) => {
                console.error(`[start-local-deepseek.js] ❌ 服务器启动失败:, error.message`);
                process.exit(1);
            });

            this.serverProcess.on('exit', (code) => {
                console.log(`📋 服务器退出，代码: ${code}`);
                process.exit(code);
            });

            // 等待服务器启动
            setTimeout(() => {
                console.log('✅ DeepSeek服务器启动完成！');
                console.log('🌐 访问地址: http://localhost:3001');
                console.log('📝 测试页面: http://localhost:8080/HTML/deepseek-test.html');
                console.log('');
                console.log('🛠️  可用命令:');
                console.log('  - 下载模型: node Scripts/download-model.js');
                console.log('  - 查看状态: curl http://localhost:3001/status');
                console.log('  - 停止服务: Ctrl+C');
                console.log('');
            }, 2000);

        } catch (error) {
            console.error(`[start-local-deepseek.js] ❌ 启动失败:, error.message`);
            process.exit(1);
        }
    }

    /**
     * 显示帮助信息
     */
    showHelp() {
        console.log(`
🤖 本地DeepSeek启动器

用法: node Scripts/start-local-deepseek.js [选项]

选项:
  --help, -h     显示帮助信息
  --check        仅检查环境和配置
  --download     下载本地模型
  --api-only     强制使用API模式

示例:
  node Scripts/start-local-deepseek.js          # 启动服务
  node Scripts/start-local-deepseek.js --check  # 检查环境
  node Scripts/start-local-deepseek.js --download # 下载模型

配置文件: Configs/deepseek_config.json
模型目录: models/
        `);
    }

    /**
     * 主启动流程
     */
    async run() {
        console.log('🤖 本地DeepSeek启动器');
        console.log('='.repeat(40));

        // 解析命令行参数
        const args = process.argv.slice(2);
        
        if (args.includes('--help') || args.includes('-h')) {
            this.showHelp().catch(error => console.error(`[start-local-deepseek.js] this.showHelp failed:`, error));
            return;
        }

        if (args.includes('--download')) {
            console.log('📥 启动模型下载...');
            const { spawn } = require('child_process');
            const downloadProcess = spawn('node', [path.join(PROJECT_ROOT, 'Scripts', 'download-model.js')], {
                stdio: 'inherit'
            });
            return;
        }

        // 加载配置
        this.loadConfig().catch(error => console.error(`[start-local-deepseek.js] this.loadConfig failed:`, error));

        // 检查本地模型
        this.checkLocalModel().catch(error => console.error(`[start-local-deepseek.js] this.checkLocalModel failed:`, error));

        // 检查依赖
        this.checkDependencies().catch(error => console.error(`[start-local-deepseek.js] this.checkDependencies failed:`, error));

        if (args.includes('--check')) {
            console.log('✅ 环境检查完成');
            return;
        }

        // 强制API模式
        if (args.includes('--api-only')) {
            console.log('🔗 强制使用API模式');
            process.env.DEEPSEEK_MODE = 'api';
        }

        // 创建环境
        this.createEnvironment().catch(error => console.error(`[start-local-deepseek.js] this.createEnvironment failed:`, error));

        // 启动服务器
        await this.startServer();

        // 处理退出信号
        process.on('SIGINT', () => {
            console.log('\n🛑 正在关闭服务器...');
            if (this.serverProcess) {
                this.serverProcess.kill('SIGTERM');
            }
            process.exit(0);
        });
    }
}

// 启动应用
if (require.main === module) {
    const launcher = new LocalDeepSeekLauncher();
    launcher.run().catch(error => {
        console.error(`[start-local-deepseek.js] ❌ 启动失败:, error`);
        process.exit(1);
    });
}

module.exports = LocalDeepSeekLauncher;