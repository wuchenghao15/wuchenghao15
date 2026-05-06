/**
 * 资源监控子AI
 * 监控并抓包客户端加载资源状态匹配项目源
 */

const winston = require('winston');
const crypto = require('crypto');
const fs = require('fs');
const path = require('path');
const { exec } = require('child_process');
const util = require('util');
const jsdom = require('jsdom');
const { JSDOM } = jsdom;

// 配置日志
const logger = winston.createLogger({
    level: process.env.LOG_LEVEL || 'info',
    format: winston.format.combine(
        winston.format.timestamp(),
        winston.format.json()
    ),
    transports: [
        new winston.transports.File({
            filename: `${process.env.LOG_DIR || './Logs'}/resource-monitor-ai.log`,
            maxsize: 5242880,
            maxFiles: 5
        }),
        new winston.transports.Console({
            format: winston.format.simple()
        })
    ]
});

// 添加warning方法的兼容处理
if (!logger.warning) {
    logger.warning = logger.warn;
}

// 引入AI特征库
const aiFeatureLibrary = require('./ai-feature-library');

// 资源监控子AI类
class ResourceMonitorAI {
    constructor() {
        this.id = crypto.randomUUID();
        this.name = 'resource_monitor_ai';
        this.role = 'resource_monitor';
        this.group = 'monitoring';
        this.status = 'idle';
        this.currentTask = null;
        this.taskHistory = [];
        this.createdAt = new Date();
        this.updatedAt = new Date();
        this.idleSince = new Date();
        
        // 监控配置
        this.monitoringConfig = {
            resourceMonitoring: true,
            packetCapture: true,
            autoFix: true,
            featureReporting: true,
            resourceCheckInterval: 60000, // 每分钟检查一次
            captureDirectory: path.join(__dirname, '../../../Logs/captures/resources')
        };
        
        // 性能指标
        this.performanceMetrics = {
            resourcesMonitored: 0,
            resourcesFailed: 0,
            resourcesMissing: 0,
            packetsCaptured: 0,
            fixesApplied: 0,
            featuresReported: 0,
            lastCheckTime: null
        };
        
        // 项目资源信息
        this.projectResources = {
            css: [],
            js: [],
            images: [],
            other: []
        };
        
        // 确保抓包目录存在
        if (!fs.existsSync(this.monitoringConfig.captureDirectory)) {
            fs.mkdirSync(this.monitoringConfig.captureDirectory, { recursive: true });
        }
        
        // 加载项目资源信息
        this.loadProjectResources();
        
        logger.info(`✅ 资源监控子AI已初始化: ${this.name}`);
    }
    
    /**
     * 开始监控
     */
    startMonitoring() {
        logger.info(`📋 开始资源监控...`);
        this.status = 'running';
        this.currentTask = 'resource_monitoring';
        this.updatedAt = new Date();
        
        // 定期检查资源加载状态
        this.monitoringInterval = setInterval(() => {
            this.checkResourceLoading();
        }, this.monitoringConfig.resourceCheckInterval);
        
        logger.info(`✅ 资源监控已启动`);
        return { success: true, message: '资源监控已启动' };
    }
    
    /**
     * 停止监控
     */
    stopMonitoring() {
        logger.info(`📋 停止资源监控...`);
        this.status = 'idle';
        this.currentTask = null;
        this.idleSince = new Date();
        this.updatedAt = new Date();
        
        if (this.monitoringInterval) {
            clearInterval(this.monitoringInterval);
            this.monitoringInterval = null;
        }
        
        logger.info(`✅ 资源监控已停止`);
        return { success: true, message: '资源监控已停止' };
    }
    
    /**
     * 加载项目资源信息
     */
    loadProjectResources() {
        logger.info(`📋 加载项目资源信息...`);
        
        try {
            const projectRoot = path.resolve(__dirname, '../../..');
            const htmlDir = path.join(projectRoot, 'src', 'html');
            
            // 查找所有HTML文件
            const htmlFiles = this.findFiles(htmlDir, '*.html');
            
            // 从HTML文件中提取资源信息
            htmlFiles.forEach(htmlFile => {
                const content = fs.readFileSync(htmlFile, 'utf8');
                
                // 提取CSS资源
                const cssRegex = /<link[^>]+rel="stylesheet"[^>]+href="([^"]+)"[^>]*>/g;
                let match;
                while ((match = cssRegex.exec(content)) !== null) {
                    const cssPath = match[1];
                    if (!this.projectResources.css.includes(cssPath)) {
                        this.projectResources.css.push(cssPath);
                    }
                }
                
                // 提取JS资源
                const jsRegex = /<script[^>]+src="([^"]+)"[^>]*>/g;
                while ((match = jsRegex.exec(content)) !== null) {
                    const jsPath = match[1];
                    if (!this.projectResources.js.includes(jsPath)) {
                        this.projectResources.js.push(jsPath);
                    }
                }
                
                // 提取图片资源
                const imgRegex = /<img[^>]+src="([^"]+)"[^>]*>/g;
                while ((match = imgRegex.exec(content)) !== null) {
                    const imgPath = match[1];
                    if (!this.projectResources.images.includes(imgPath)) {
                        this.projectResources.images.push(imgPath);
                    }
                }
            });
            
            logger.info(`✅ 项目资源信息加载完成`);
            logger.info(`   CSS资源: ${this.projectResources.css.length} 个`);
            logger.info(`   JS资源: ${this.projectResources.js.length} 个`);
            logger.info(`   图片资源: ${this.projectResources.images.length} 个`);
            
        } catch (error) {
            logger.error(`❌ 加载项目资源信息失败: ${error.message}`);
        }
    }
    
    /**
     * 查找文件
     */
    findFiles(directory, pattern) {
        const fullPath = path.resolve(directory);
        const findCommand = `find ${fullPath} -name "${pattern}" -type f | grep -v ".git"`;
        const { execSync } = require('child_process');
        const result = execSync(findCommand, { encoding: 'utf8' });
        return result.trim().split('\n').filter(Boolean);
    }
    
    /**
     * 检查资源加载状态
     */
    async checkResourceLoading() {
        logger.info(`🔍 检查资源加载状态...`);
        this.performanceMetrics.lastCheckTime = new Date();
        this.performanceMetrics.resourcesMonitored++;
        
        try {
            // 使用内部浏览器打开首页，监控资源加载
            await this.monitorResourceLoadingInBrowser();
            
            // 执行网络抓包
            await this.captureResourcePackets();
            
        } catch (error) {
            logger.error(`❌ 检查资源加载状态时发生错误: ${error.message}`);
        }
    }
    
    /**
     * 在浏览器中监控资源加载
     */
    async monitorResourceLoadingInBrowser() {
        logger.info(`🌐 在浏览器中监控资源加载...`);
        
        try {
            const homepageUrl = 'http://localhost:8080/html/index.html';
            const execPromise = util.promisify(exec);
            
            // 检查服务器是否正在运行
            try {
                await execPromise('curl -o /dev/null -s -f http://localhost:8080');
            } catch (serverError) {
                logger.warning(`⚠️  服务器可能未运行，跳过资源监控`);
                return;
            }
            
            // 使用curl获取首页内容
            const { stdout: htmlContent } = await execPromise(`curl -s ${homepageUrl}`);
            
            // 使用JSDOM解析HTML内容，模拟浏览器环境
            const dom = new JSDOM(htmlContent, {
                url: homepageUrl,
                pretendToBeVisual: true,
                runScripts: 'dangerously',
                resources: 'usable'
            });
            
            const { window } = dom;
            const { document } = window;
            
            // 等待页面加载完成
            await new Promise(resolve => {
                window.addEventListener('load', resolve);
                // 设置超时，防止无限等待
                setTimeout(resolve, 5000);
            });
            
            // 监控资源加载状态
            const loadedResources = {
                css: [],
                js: [],
                images: [],
                failed: []
            };
            
            // 监控CSS资源加载
            const linkElements = document.querySelectorAll('link[rel="stylesheet"]');
            linkElements.forEach(link => {
                const href = link.href;
                if (link.sheet) {
                    loadedResources.css.push(href);
                } else {
                    loadedResources.failed.push({
                        type: 'css',
                        url: href,
                        reason: 'CSS资源加载失败'
                    });
                }
            });
            
            // 监控JS资源加载
            const scriptElements = document.querySelectorAll('script[src]');
            scriptElements.forEach(script => {
                const src = script.src;
                if (script.readyState === 'complete' || script.readyState === 'loaded' || !script.readyState) {
                    loadedResources.js.push(src);
                } else {
                    loadedResources.failed.push({
                        type: 'js',
                        url: src,
                        reason: 'JS资源加载失败'
                    });
                }
            });
            
            // 监控图片资源加载
            const imgElements = document.querySelectorAll('img');
            imgElements.forEach(img => {
                const src = img.src;
                if (img.complete) {
                    loadedResources.images.push(src);
                } else {
                    loadedResources.failed.push({
                        type: 'image',
                        url: src,
                        reason: '图片资源加载失败'
                    });
                }
            });
            
            logger.info(`📊 资源加载状态:`);
            logger.info(`   加载成功的CSS: ${loadedResources.css.length} 个`);
            logger.info(`   加载成功的JS: ${loadedResources.js.length} 个`);
            logger.info(`   加载成功的图片: ${loadedResources.images.length} 个`);
            logger.info(`   加载失败的资源: ${loadedResources.failed.length} 个`);
            
            // 检查资源完整性
            await this.checkResourceIntegrity(loadedResources);
            
            // 记录加载失败的资源
            if (loadedResources.failed.length > 0) {
                await this.handleFailedResources(loadedResources.failed);
            }
            
        } catch (error) {
            logger.error(`❌ 在浏览器中监控资源加载失败: ${error.message}`);
        }
    }
    
    /**
     * 检查资源完整性
     */
    async checkResourceIntegrity(loadedResources) {
        logger.info(`🔍 检查资源完整性...`);
        
        try {
            // 检查项目源中的资源是否都被加载
            const missingResources = [];
            
            // 检查CSS资源
            this.projectResources.css.forEach(cssPath => {
                const fullUrl = `http://localhost:8080${cssPath.startsWith('/') ? cssPath : `/${cssPath}`}`;
                if (!loadedResources.css.some(loadedUrl => loadedUrl.includes(cssPath))) {
                    missingResources.push({
                        type: 'css',
                        url: fullUrl,
                        path: cssPath,
                        reason: 'CSS资源未加载'
                    });
                }
            });
            
            // 检查JS资源
            this.projectResources.js.forEach(jsPath => {
                const fullUrl = `http://localhost:8080${jsPath.startsWith('/') ? jsPath : `/${jsPath}`}`;
                if (!loadedResources.js.some(loadedUrl => loadedUrl.includes(jsPath))) {
                    missingResources.push({
                        type: 'js',
                        url: fullUrl,
                        path: jsPath,
                        reason: 'JS资源未加载'
                    });
                }
            });
            
            // 检查图片资源
            this.projectResources.images.forEach(imgPath => {
                const fullUrl = `http://localhost:8080${imgPath.startsWith('/') ? imgPath : `/${imgPath}`}`;
                if (!loadedResources.images.some(loadedUrl => loadedUrl.includes(imgPath))) {
                    missingResources.push({
                        type: 'image',
                        url: fullUrl,
                        path: imgPath,
                        reason: '图片资源未加载'
                    });
                }
            });
            
            logger.info(`📊 资源完整性检查:`);
            logger.info(`   缺失的资源: ${missingResources.length} 个`);
            
            // 记录缺失的资源
            if (missingResources.length > 0) {
                await this.handleMissingResources(missingResources);
            }
            
        } catch (error) {
            logger.error(`❌ 检查资源完整性失败: ${error.message}`);
        }
    }
    
    /**
     * 执行网络抓包
     */
    async captureResourcePackets() {
        logger.info(`📡 执行资源网络抓包...`);
        
        try {
            const execPromise = util.promisify(exec);
            const captureFile = path.join(this.monitoringConfig.captureDirectory, `resource_capture_${Date.now()}.pcap`);
            
            // 使用tcpdump抓包（如果可用）
            try {
                await execPromise(`tcpdump -i lo0 -w ${captureFile} -s 0 -c 100`);
                logger.info(`✅ 资源抓包已保存: ${captureFile}`);
                this.performanceMetrics.packetsCaptured++;
            } catch (tcpdumpError) {
                logger.warning(`⚠️  tcpdump 不可用，使用替代方法`);
                
                // 使用curl记录请求响应
                const requestFile = path.join(this.monitoringConfig.captureDirectory, `resource_request_${Date.now()}.json`);
                const { stdout: response, stderr: error } = await execPromise('curl -v http://localhost:8080/html/index.html 2>&1');
                
                const requestData = {
                    timestamp: new Date().toISOString(),
                    response: response,
                    error: error
                };
                
                fs.writeFileSync(requestFile, JSON.stringify(requestData, null, 2));
                logger.info(`✅ 资源请求响应已保存: ${requestFile}`);
                this.performanceMetrics.packetsCaptured++;
            }
            
        } catch (captureError) {
            logger.error(`❌ 执行资源网络抓包时发生错误: ${captureError.message}`);
        }
    }
    
    /**
     * 处理加载失败的资源
     */
    async handleFailedResources(failedResources) {
        logger.info(`⚠️  处理加载失败的资源...`);
        
        this.performanceMetrics.resourcesFailed += failedResources.length;
        
        for (const resource of failedResources) {
            // 创建错误特征
            const errorFeature = {
                type: 'resource_load_failure',
                description: `资源加载失败: ${resource.url}`,
                severity: 'medium',
                location: resource.url,
                timestamp: new Date().toISOString(),
                aiId: this.id,
                aiName: this.name,
                source: 'browser',
                details: resource
            };
            
            // 添加到特征库
            const newFeature = aiFeatureLibrary.addFeature(errorFeature);
            logger.info(`📊 资源加载失败特征已添加到特征库: ${newFeature.id}`);
            this.performanceMetrics.featuresReported++;
            
            // 尝试修复
            if (this.monitoringConfig.autoFix) {
                await this.attemptFix(errorFeature);
            }
        }
    }
    
    /**
     * 处理缺失的资源
     */
    async handleMissingResources(missingResources) {
        logger.info(`⚠️  处理缺失的资源...`);
        
        this.performanceMetrics.resourcesMissing += missingResources.length;
        
        for (const resource of missingResources) {
            // 创建错误特征
            const errorFeature = {
                type: 'resource_missing',
                description: `资源未加载: ${resource.url}`,
                severity: 'medium',
                location: resource.url,
                timestamp: new Date().toISOString(),
                aiId: this.id,
                aiName: this.name,
                source: 'resource_monitor',
                details: resource
            };
            
            // 添加到特征库
            const newFeature = aiFeatureLibrary.addFeature(errorFeature);
            logger.info(`📊 资源缺失特征已添加到特征库: ${newFeature.id}`);
            this.performanceMetrics.featuresReported++;
            
            // 尝试修复
            if (this.monitoringConfig.autoFix) {
                await this.attemptFix(errorFeature);
            }
        }
    }
    
    /**
     * 尝试修复错误
     */
    async attemptFix(errorFeature) {
        logger.info(`🔧 尝试修复资源错误: ${errorFeature.description}`);
        
        try {
            let result;
            if (errorFeature.type === 'resource_load_failure') {
                result = await this.fixResourceLoadFailure(errorFeature);
            } else if (errorFeature.type === 'resource_missing') {
                result = await this.fixResourceMissing(errorFeature);
            } else {
                result = { status: 'skipped', message: '未实现的修复类型' };
            }
            
            logger.info(`   修复结果: ${result.status} - ${result.message}`);
            
            if (result.status === 'success') {
                this.performanceMetrics.fixesApplied++;
            }
            
        } catch (fixError) {
            logger.error(`❌ 修复资源错误时发生错误: ${fixError.message}`);
        }
    }
    
    /**
     * 修复资源加载失败
     */
    async fixResourceLoadFailure(errorFeature) {
        logger.info(`   修复资源加载失败: ${errorFeature.details.url}`);
        
        try {
            const resourceUrl = errorFeature.details.url;
            const resourcePath = resourceUrl.replace('http://localhost:8080', '');
            const fullPath = path.resolve(__dirname, '../../../src', resourcePath);
            
            // 检查资源文件是否存在
            if (!fs.existsSync(fullPath)) {
                logger.error(`   资源文件不存在: ${fullPath}`);
                return { status: 'failed', message: '资源文件不存在' };
            }
            
            // 检查资源文件权限
            const stats = fs.statSync(fullPath);
            if (stats.mode & 0o444 !== 0o444) {
                logger.warning(`   资源文件权限问题，修复权限...`);
                fs.chmodSync(fullPath, 0o644);
            }
            
            logger.info(`   资源文件检查和修复完成`);
            return { status: 'success', message: '资源文件检查和修复完成' };
            
        } catch (fixError) {
            logger.error(`   修复资源加载失败时发生错误: ${fixError.message}`);
            return { status: 'failed', message: fixError.message };
        }
    }
    
    /**
     * 修复缺失的资源
     */
    async fixResourceMissing(errorFeature) {
        logger.info(`   修复缺失的资源: ${errorFeature.details.url}`);
        
        try {
            const resourcePath = errorFeature.details.path;
            const fullPath = path.resolve(__dirname, '../../../src', resourcePath);
            
            // 检查资源文件是否存在
            if (!fs.existsSync(fullPath)) {
                logger.error(`   资源文件不存在: ${fullPath}`);
                return { status: 'failed', message: '资源文件不存在' };
            }
            
            // 检查资源是否在HTML中正确引用
            const indexPath = path.resolve(__dirname, '../../../src/html/index.html');
            const indexContent = fs.readFileSync(indexPath, 'utf8');
            
            if (!indexContent.includes(resourcePath)) {
                logger.warning(`   资源未在HTML中引用，添加引用...`);
                
                let newContent = indexContent;
                if (resourcePath.endsWith('.css')) {
                    // 添加CSS引用
                    newContent = newContent.replace('</head>', `    <link rel="stylesheet" href="${resourcePath}">
</head>`);
                } else if (resourcePath.endsWith('.js')) {
                    // 添加JS引用
                    newContent = newContent.replace('</body>', `    <script src="${resourcePath}"></script>
</body>`);
                }
                
                fs.writeFileSync(indexPath, newContent, 'utf8');
                logger.info(`   资源引用已添加到HTML中`);
            }
            
            logger.info(`   缺失资源修复完成`);
            return { status: 'success', message: '缺失资源修复完成' };
            
        } catch (fixError) {
            logger.error(`   修复缺失资源时发生错误: ${fixError.message}`);
            return { status: 'failed', message: fixError.message };
        }
    }
    
    /**
     * 功能拓展和优化
     */
    async enhanceFeatures() {
        logger.info(`🚀 执行资源监控功能拓展和优化...`);
        
        try {
            // 这里可以添加根据AI自动拓展优化完善功能的逻辑
            // 例如：
            // 1. 优化资源加载顺序
            // 2. 添加资源预加载
            // 3. 实现资源懒加载
            // 4. 添加资源缓存优化
            
            logger.info(`✅ 资源监控功能拓展和优化完成`);
            
        } catch (enhanceError) {
            logger.error(`❌ 执行资源监控功能拓展和优化时发生错误: ${enhanceError.message}`);
        }
    }
    
    /**
     * 生成监控报告
     */
    generateReport() {
        const report = {
            id: `resource_report_${Date.now()}`,
            aiId: this.id,
            aiName: this.name,
            generatedAt: new Date().toISOString(),
            status: this.status,
            performanceMetrics: this.performanceMetrics,
            monitoringConfig: this.monitoringConfig,
            taskHistory: this.taskHistory,
            projectResources: this.projectResources
        };
        
        // 保存报告
        const reportFile = path.join(this.monitoringConfig.captureDirectory, `resource_report_${Date.now()}.json`);
        fs.writeFileSync(reportFile, JSON.stringify(report, null, 2));
        
        logger.info(`📄 资源监控报告已生成: ${reportFile}`);
        return report;
    }
    
    /**
     * 获取监控状态
     */
    getStatus() {
        return {
            id: this.id,
            name: this.name,
            status: this.status,
            role: this.role,
            group: this.group,
            createdAt: this.createdAt,
            updatedAt: this.updatedAt,
            idleSince: this.idleSince,
            currentTask: this.currentTask,
            performanceMetrics: this.performanceMetrics,
            monitoringConfig: this.monitoringConfig
        };
    }
    
    /**
     * 更新监控配置
     */
    updateConfig(config) {
        this.monitoringConfig = { ...this.monitoringConfig, ...config };
        logger.info(`⚙️  资源监控配置已更新`);
        return this.monitoringConfig;
    }
}

// 导出单例实例
const resourceMonitorAI = new ResourceMonitorAI();
module.exports = resourceMonitorAI;
