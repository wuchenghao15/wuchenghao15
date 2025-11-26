#!/usr/bin/env node

/**
 * 项目更新机制
 * 自动检测资源变化并触发更新流程
 */

const fs = require('fs');
const path = require('path');
const { execSync } = require('child_process');

class ProjectUpdater {
    constructor() {
        this.projectRoot = process.cwd();
        this.assetsPath = path.join(this.projectRoot, 'assets');
        this.configPath = path.join(this.assetsPath, 'js', 'config', 'project-config.js');
        this.lastUpdateFile = path.join(this.assetsPath, '.last-update');
        this.watchedExtensions = ['.css', '.js', '.html', '.json'];
    }

    /**
     * 获取文件最后修改时间
     */
    getFileModTime(filePath) {
        try {
            const stats = fs.statSync(filePath);
            return stats.mtime.getTime();
        } catch (error) {
            return 0;
        }
    }

    /**
     * 获取目录下所有文件的最新修改时间
     */
    getLatestModTime(dirPath, extensions = this.watchedExtensions) {
        let latestTime = 0;
        
        try {
            const files = fs.readdirSync(dirPath, { withFileTypes: true });
            
            for (const file of files) {
                const fullPath = path.join(dirPath, file.name);
                
                if (file.isDirectory()) {
                    const dirTime = this.getLatestModTime(fullPath, extensions);
                    latestTime = Math.max(latestTime, dirTime);
                } else if (extensions.some(ext => file.name.endsWith(ext))) {
                    const fileTime = this.getFileModTime(fullPath);
                    latestTime = Math.max(latestTime, fileTime);
                }
            }
        } catch (error) {
            console.warn(`无法读取目录 ${dirPath}:`, error.message);
        }
        
        return latestTime;
    }

    /**
     * 获取上次更新时间
     */
    getLastUpdateTime() {
        try {
            const content = fs.readFileSync(this.lastUpdateFile, 'utf8');
            return parseInt(content.trim());
        } catch (error) {
            return 0;
        }
    }

    /**
     * 保存更新时间
     */
    saveUpdateTime() {
        const now = Date.now();
        try {
            fs.writeFileSync(this.lastUpdateFile, now.toString());
        } catch (error) {
            console.warn('无法保存更新时间:', error.message);
        }
    }

    /**
     * 检查是否有文件更新
     */
    hasUpdates() {
        const lastUpdate = this.getLastUpdateTime();
        const currentModTime = this.getLatestModTime(this.assetsPath);
        
        return currentModTime > lastUpdate;
    }

    /**
     * 生成资源映射表
     */
    generateAssetMap() {
        const assetMap = {
            css: {},
            js: {},
            img: {},
            fonts: {}
        };

        const scanDirectory = (dirPath, type) => {
            try {
                const files = fs.readdirSync(dirPath, { withFileTypes: true });
                
                for (const file of files) {
                    const fullPath = path.join(dirPath, file.name);
                    
                    if (file.isDirectory()) {
                        scanDirectory(fullPath, type);
                    } else if (file.name.endsWith(type === 'css' ? '.css' : '.js')) {
                        const relativePath = path.relative(this.projectRoot, fullPath);
                        const webPath = '/' + relativePath.replace(/\\/g, '/');
                        assetMap[type][file.name] = webPath;
                    }
                }
            } catch (error) {
                console.warn(`扫描目录 ${dirPath} 时出错:`, error.message);
            }
        };

        // 扫描各个资源目录
        const cssDir = path.join(this.assetsPath, 'css');
        const jsDir = path.join(this.assetsPath, 'js');
        
        if (fs.existsSync(cssDir)) scanDirectory(cssDir, 'css');
        if (fs.existsSync(jsDir)) scanDirectory(jsDir, 'js');

        return assetMap;
    }

    /**
     * 更新配置文件中的资源映射
     */
    updateConfig() {
        try {
            const assetMap = this.generateAssetMap();
            
            // 读取现有配置
            let configContent = '';
            if (fs.existsSync(this.configPath)) {
                configContent = fs.readFileSync(this.configPath, 'utf8');
            }

            // 更新资源映射部分
            const newAssetMap = `// 自动生成的资源映射 - ${new Date().toISOString()}
const ASSET_MAP = ${JSON.stringify(assetMap, null, 2)};`;

            // 替换或添加资源映射
            const assetMapRegex = /\/\/ 自动生成的资源映射[\s\S]*?const ASSET_MAP = [\s\S]*?;/;
            if (assetMapRegex.test(configContent)) {
                configContent = configContent.replace(assetMapRegex, newAssetMap);
            } else {
                configContent += '\n\n' + newAssetMap;
            }

            fs.writeFileSync(this.configPath, configContent);
            console.log('✅ 配置文件已更新');
            
        } catch (error) {
            console.error('❌ 更新配置文件失败:', error.message);
        }
    }

    /**
     * 运行路径修复
     */
    runPathFixer() {
        try {
            const pathFixerPath = path.join(this.assetsPath, 'js', 'utils', 'path-fixer.js');
            if (fs.existsSync(pathFixerPath)) {
                console.log('🔧 运行路径修复...');
                execSync(`node "${pathFixerPath}"`, { cwd: this.projectRoot, stdio: 'inherit' });
                console.log('✅ 路径修复完成');
            }
        } catch (error) {
            console.error('❌ 路径修复失败:', error.message);
        }
    }

    /**
     * 生成更新报告
     */
    generateReport() {
        const report = {
            timestamp: new Date().toISOString(),
            assetMap: this.generateAssetMap(),
            lastUpdate: this.getLastUpdateTime(),
            projectRoot: this.projectRoot
        };

        const reportPath = path.join(this.assetsPath, 'update-report.json');
        fs.writeFileSync(reportPath, JSON.stringify(report, null, 2));
        
        console.log(`📊 更新报告已生成: ${reportPath}`);
        return report;
    }

    /**
     * 执行完整更新流程
     */
    async performUpdate() {
        console.log('🚀 开始项目更新流程...\n');

        // 1. 检查是否有更新
        if (!this.hasUpdates()) {
            console.log('ℹ️  没有检测到文件更新');
            return false;
        }

        console.log('📦 检测到文件更新，开始处理...\n');

        // 2. 更新配置文件
        this.updateConfig();

        // 3. 运行路径修复
        this.runPathFixer();

        // 4. 生成更新报告
        this.generateReport();

        // 5. 保存更新时间
        this.saveUpdateTime();

        console.log('\n✨ 项目更新完成！');
        return true;
    }

    /**
     * 启动监控模式
     */
    startWatchMode(interval = 5000) {
        console.log(`👁️  启动文件监控模式 (检查间隔: ${interval}ms)`);
        
        const checkAndUpdate = async () => {
            try {
                const updated = await this.performUpdate();
                if (updated) {
                    console.log('🔄 项目已自动更新');
                }
            } catch (error) {
                console.error('❌ 自动更新失败:', error.message);
            }
        };

        // 立即检查一次
        checkAndUpdate();

        // 定期检查
        setInterval(checkAndUpdate, interval);
    }
}

// 命令行接口
async function main() {
    const updater = new ProjectUpdater();
    const args = process.argv.slice(2);

    if (args.includes('--watch') || args.includes('-w')) {
        const interval = parseInt(args.find(arg => arg.startsWith('--interval='))?.split('=')[1]) || 5000;
        updater.startWatchMode(interval);
    } else if (args.includes('--check')) {
        const hasUpdates = updater.hasUpdates();
        console.log(hasUpdates ? '📦 有待更新的文件' : 'ℹ️  没有更新');
        process.exit(hasUpdates ? 1 : 0);
    } else if (args.includes('--report')) {
        updater.generateReport();
    } else {
        await updater.performUpdate();
    }
}

// 导出类供其他模块使用
module.exports = ProjectUpdater;

// 如果直接运行此脚本
if (require.main === module) {
    main().catch(console.error);
}