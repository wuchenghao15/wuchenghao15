/**
 * 自定义HTTP服务器
 * 支持404和403页面自动挂载
 * 集成DeepSeek AI API
 * 集成安全模块：电子签名、Token、证书
 */

const http = require('http');
const fs = require('fs');
const path = require('path');
const url = require('url');

// 导入Express和相关中间件
const express = require('express');
const cors = require('cors');
const bodyParser = require('body-parser');

// 导入安全模块
const security = require('./security');

// 导入DeepSeek路由
const deepseekRoutes = require('./deepseek-routes');

const PORT = 8000;
const PROJECT_ROOT = path.join(__dirname, '..');

// MIME类型映射
const mimeTypes = {
    '.html': 'text/html',
    '.js': 'text/javascript',
    '.css': 'text/css',
    '.json': 'application/json',
    '.png': 'image/png',
    '.jpg': 'image/jpg',
    '.gif': 'image/gif',
    '.svg': 'image/svg+xml',
    '.wav': 'audio/wav',
    '.mp4': 'video/mp4',
    '.woff': 'application/font-woff',
    '.woff2': 'application/font-woff2',
    '.ttf': 'application/font-ttf',
    '.eot': 'application/vnd.ms-fontobject',
    '.otf': 'application/font-otf',
    '.wasm': 'application/wasm'
};

/**
 * 获取文件的MIME类型
 */
function getContentType(filePath) {
    const ext = path.extname(filePath).toLowerCase();
    return mimeTypes[ext] || 'application/octet-stream';
}

/**
 * 读取文件内容
 */
function readFile(filePath, res) {
    return new Promise((resolve, reject) => {
        fs.readFile(filePath, (err, content) => {
            if (err) {
                reject(err);
            } else {
                resolve(content);
            }
        });
    });
}

/**
 * 发送404页面
 */
async function send404Page(res, requestedPath) {
    try {
        const filePath = path.join(PROJECT_ROOT, 'HTML', '404.html');
        const content = await readFile(filePath);
        
        // 替换页面中的动态内容
        let pageContent = content.toString();
        pageContent = pageContent.replace('{{REQUESTED_PATH}}', requestedPath || '未知页面');
        pageContent = pageContent.replace('{{TIMESTAMP}}', new Date().toLocaleString('zh-CN'));
        
        res.writeHead(404, { 'Content-Type': 'text/html; charset=utf-8' });
        res.end(pageContent);
        
        console.log(`[404] ${requestedPath} - 已显示自定义404页面`);
    } catch (error) {
        // 如果404页面也不存在，发送简单的404响应
        res.writeHead(404, { 'Content-Type': 'text/html; charset=utf-8' });
        res.end(`
            <!DOCTYPE html>
            <html>
            <head><title>404 - 页面未找到</title></head>
            <body>
                <h1>404 - 页面未找到</h1>
                <p>请求的页面 ${requestedPath} 不存在</p>
                <p>时间: ${new Date().toLocaleString('zh-CN')}</p>
            </body>
            </html>
        `);
        
        console.error(`[404] ${requestedPath} - 404页面加载失败，使用默认页面`);
    }
}

/**
 * 发送403页面
 */
async function send403Page(res, requestedPath) {
    try {
        const filePath = path.join(PROJECT_ROOT, 'HTML', '403.html');
        const content = await readFile(filePath);
        
        // 替换页面中的动态内容
        let pageContent = content.toString();
        pageContent = pageContent.replace('{{REQUESTED_PATH}}', requestedPath || '受保护的资源');
        pageContent = pageContent.replace('{{TIMESTAMP}}', new Date().toLocaleString('zh-CN'));
        pageContent = pageContent.replace('{{CLIENT_IP}}', res.socket.remoteAddress || '未知');
        
        res.writeHead(403, { 'Content-Type': 'text/html; charset=utf-8' });
        res.end(pageContent);
        
        console.log(`[403] ${requestedPath} - 已显示自定义403页面`);
    } catch (error) {
        // 如果403页面也不存在，发送简单的403响应
        res.writeHead(403, { 'Content-Type': 'text/html; charset=utf-8' });
        res.end(`
            <!DOCTYPE html>
            <html>
            <head><title>403 - 访问被拒绝</title></head>
            <body>
                <h1>403 - 访问被拒绝</h1>
                <p>您没有权限访问 ${requestedPath}</p>
                <p>时间: ${new Date().toLocaleString('zh-CN')}</p>
            </body>
            </html>
        `);
        
        console.error(`[403] ${requestedPath} - 403页面加载失败，使用默认页面`);
    }
}

/**
 * 检查路径是否应该被禁止访问
 */
function isForbiddenPath(requestPath) {
    // 定义禁止访问的路径模式
    const forbiddenPatterns = [
        /\/\.env/,
        /\/\.git\//,
        /\/node_modules\//,
        /\/package-lock\.json/,
        /\/\.DS_Store/,
        /\/\.vscode\//,
        /\/\.idea\//,
        /\/Backups\//,
        /\.log$/,
        /\.tmp$/,
        /\/temp\//
    ];
    
    return forbiddenPatterns.some(pattern => pattern.test(requestPath));
}

/**
 * 处理静态文件请求
 */
async function handleStaticFile(requestPath, res) {
    // 安全检查：防止路径遍历攻击
    if (requestPath.includes('..')) {
        await send403Page(res, requestPath);
        return;
    }
    
    // 检查是否为禁止访问的路径
    if (isForbiddenPath(requestPath)) {
        await send403Page(res, requestPath);
        return;
    }
    
    // 构建文件路径
    let filePath;
    if (requestPath === '/' || requestPath === '') {
        filePath = path.join(PROJECT_ROOT, 'HTML', 'index.html');
    } else {
        filePath = path.join(PROJECT_ROOT, requestPath);
    }
    
    try {
        // 检查文件是否存在
        const stats = await fs.promises.stat(filePath);
        
        if (stats.isDirectory()) {
            // 如果是目录，尝试查找index.html
            const indexPath = path.join(filePath, 'index.html');
            try {
                const indexStats = await fs.promises.stat(indexPath);
                if (indexStats.isFile()) {
                    filePath = indexPath;
                } else {
                    await send404Page(res, requestPath);
                    return;
                }
            } catch {
                await send404Page(res, requestPath);
                return;
            }
        }
        
        // 读取并发送文件
        const content = await readFile(filePath);
        const contentType = getContentType(filePath);
        
        // 设置CORS头
        res.writeHead(200, {
            'Content-Type': contentType,
            'Access-Control-Allow-Origin': '*',
            'Access-Control-Allow-Methods': 'GET, POST, PUT, DELETE, OPTIONS',
            'Access-Control-Allow-Headers': 'Content-Type, Authorization'
        });
        
        res.end(content);
        console.log(`[200] ${requestPath} - ${contentType}`);
        
    } catch (error) {
        if (error.code === 'ENOENT') {
            await send404Page(res, requestPath);
        } else if (error.code === 'EACCES') {
            await send403Page(res, requestPath);
        } else {
            res.writeHead(500, { 'Content-Type': 'text/plain' });
            res.end('Internal Server Error');
            console.error(`[500] ${requestPath} - ${error.message}`);
        }
    }
}

/**
 * 创建Express应用
 */
const app = express();

// 初始化安全模块
security.initialize();

// 中间件配置
app.use(cors());
app.use(bodyParser.json({ limit: '10mb' }));
app.use(bodyParser.urlencoded({ extended: true, limit: '10mb' }));

// 安全中间件 - Token认证（排除健康检查和登录接口）
app.use('/api/', (req, res, next) => {
    // 排除不需要认证的接口
    if (req.path === '/health' || req.path === '/auth/login') {
        return next();
    }
    security.tokenAuth.middleware(req, res, next);
});

// API路由
app.use('/api/deepseek', deepseekRoutes);

// 健康检查API - 不需要认证
app.get('/api/health', (req, res) => {
    // 获取系统状态
    const systemStatus = {
        status: 'ok',
        timestamp: new Date().toISOString(),
        version: '1.0.0',
        securityStatus: {
            jwtKeyExists: fs.existsSync(path.join(PROJECT_ROOT, 'Security', 'keys', 'jwt_secret.key')),
            certExists: fs.existsSync(path.join(PROJECT_ROOT, 'Security', 'certs', 'mtscos-ai.local.pem')),
            keysExists: fs.existsSync(path.join(PROJECT_ROOT, 'Security', 'keys', 'default_public.pem'))
        }
    };
    
    res.json(systemStatus);
});

// 安全API - 生成Token
app.post('/api/auth/login', (req, res) => {
    const { username, password } = req.body;
    
    // 这里应该有实际的用户认证逻辑
    // 简化实现：使用硬编码的用户名密码
    if (username === 'admin' && password === 'admin123') {
        const token = security.tokenAuth.generateToken({
            username: username,
            role: 'admin',
            userId: '1'
        });
        
        res.json({
            success: true,
            token: token,
            user: {
                username: username,
                role: 'admin'
            }
        });
    } else {
        res.status(401).json({
            success: false,
            message: 'Invalid credentials'
        });
    }
});

// 安全API - 电子签名
app.post('/api/security/sign', security.tokenAuth.middleware, (req, res) => {
    const { data } = req.body;
    
    if (!data) {
        return res.status(400).json({ error: 'Data is required' });
    }
    
    try {
        const signature = security.digitalSignature.sign(data);
        res.json({
            success: true,
            signature: signature,
            data: data
        });
    } catch (error) {
        res.status(500).json({ error: 'Failed to sign data' });
    }
});

// 安全API - 验证电子签名
app.post('/api/security/verify', security.tokenAuth.middleware, (req, res) => {
    const { data, signature } = req.body;
    
    if (!data || !signature) {
        return res.status(400).json({ error: 'Data and signature are required' });
    }
    
    try {
        const isValid = security.digitalSignature.verify(data, signature);
        res.json({
            success: true,
            isValid: isValid
        });
    } catch (error) {
        res.status(500).json({ error: 'Failed to verify signature' });
    }
});

// 安全API - 获取证书信息
app.get('/api/security/certificate', security.tokenAuth.middleware, (req, res) => {
    try {
        const certInfo = security.certificateManager.getCertificate();
        res.json({
            success: true,
            certificate: certInfo.certificate
        });
    } catch (error) {
        res.status(500).json({ error: 'Failed to get certificate' });
    }
});

// 安全API - 自我修复
app.post('/api/security/repair', security.tokenAuth.middleware, (req, res) => {
    try {
        const result = security.selfRepair.repair();
        res.json({
            success: true,
            message: 'Security configuration repaired successfully'
        });
    } catch (error) {
        res.status(500).json({ error: 'Failed to repair security configuration' });
    }
});

/**
 * 处理静态文件请求的Express中间件
 */
async function staticFileMiddleware(req, res, next) {
    // 只处理非API请求
    if (req.path.startsWith('/api/')) {
        return next();
    }

    let requestPath = req.path;
    
    // 处理根路径
    if (requestPath === '/') {
        requestPath = '/HTML/index.html';
    } 
    // 处理assets路径 - 将其映射到HTML/assets目录
    else if (requestPath.startsWith('/assets/')) {
        requestPath = `/HTML${requestPath}`;
    }
    // 处理JS路径 - 同时检查HTML/JS和根目录JS
    else if (requestPath.startsWith('/JS/')) {
        // 先尝试HTML/JS目录
        let htmlJsPath = `/HTML${requestPath}`;
        try {
            const stats = await fs.promises.stat(path.join(PROJECT_ROOT, htmlJsPath));
            if (stats.isFile()) {
                requestPath = htmlJsPath;
            }
        } catch (error) {
            // 如果HTML/JS目录不存在，使用根目录JS
            requestPath = requestPath;
        }
    }
    // 处理CSS路径 - 同时检查HTML/CSS和根目录CSS
    else if (requestPath.startsWith('/CSS/')) {
        // 先尝试HTML/CSS目录
        let htmlCssPath = `/HTML${requestPath}`;
        try {
            const stats = await fs.promises.stat(path.join(PROJECT_ROOT, htmlCssPath));
            if (stats.isFile()) {
                requestPath = htmlCssPath;
            }
        } catch (error) {
            // 如果HTML/CSS目录不存在，使用根目录CSS
            requestPath = requestPath;
        }
    } 
    else if (requestPath.startsWith('/Staging/')) {
        // 对Staging路径进行特殊处理
        // 如果是Staging下的HTML文件，映射到根目录的HTML
        if (requestPath.startsWith('/Staging/HTML/') && requestPath.endsWith('.html')) {
            // 例如: /Staging/HTML/index.html -> /HTML/index.html
            requestPath = requestPath.replace('/Staging/HTML/', '/HTML/');
        } 
        // 如果是Staging下的assets路径，先尝试映射到HTML目录的assets
        else if (requestPath.startsWith('/Staging/assets/')) {
            // 例如: /Staging/assets/css/main.css -> /HTML/assets/css/main.css
            // 先将/Staging/assets/替换为/HTML/assets/
            let mappedPath = requestPath.replace('/Staging/assets/', '/HTML/assets/');
            let fileFound = false;
            
            // 检查文件是否存在于HTML目录的assets路径
            try {
                const stats = await fs.promises.stat(path.join(PROJECT_ROOT, mappedPath));
                if (stats.isFile()) {
                    requestPath = mappedPath;
                    fileFound = true;
                } 
            } catch (error) {
                // 文件不存在于HTML/assets，尝试项目根目录的assets
                mappedPath = requestPath.replace('/Staging/assets/', '/assets/');
                try {
                    const stats = await fs.promises.stat(path.join(PROJECT_ROOT, mappedPath));
                    if (stats.isFile()) {
                        requestPath = mappedPath;
                        fileFound = true;
                    }
                } catch (error) {
                    // 文件不存在于根目录assets，继续尝试其他路径
                }
            }
            
            // 如果文件不存在，尝试在common_styles目录下查找（仅当路径中不包含common_styles时）
            if (!fileFound && mappedPath.startsWith('/HTML/assets/css/') && !mappedPath.includes('/common_styles/')) {
                const commonStylesPath = mappedPath.replace('/HTML/assets/css/', '/HTML/assets/css/common_styles/');
                try {
                    const stats = await fs.promises.stat(path.join(PROJECT_ROOT, commonStylesPath));
                    if (stats.isFile()) {
                        requestPath = commonStylesPath;
                        fileFound = true;
                    }
                } catch (error) {
                    // 文件不存在于common_styles目录，继续尝试
                }
            } else if (!fileFound && mappedPath.startsWith('/assets/css/') && !mappedPath.includes('/common_styles/')) {
                const commonStylesPath = mappedPath.replace('/assets/css/', '/assets/css/common_styles/');
                try {
                    const stats = await fs.promises.stat(path.join(PROJECT_ROOT, commonStylesPath));
                    if (stats.isFile()) {
                        requestPath = commonStylesPath;
                        fileFound = true;
                    }
                } catch (error) {
                    // 文件不存在于common_styles目录，继续尝试
                }
            }
            
            // 如果文件不存在，尝试在根目录的CSS目录下查找
            if (!fileFound && mappedPath.startsWith('/HTML/assets/css/')) {
                const rootCssPath = mappedPath.replace('/HTML/assets/css/', '/CSS/');
                try {
                    const stats = await fs.promises.stat(path.join(PROJECT_ROOT, rootCssPath));
                    if (stats.isFile()) {
                        requestPath = rootCssPath;
                        fileFound = true;
                    }
                } catch (error) {
                    // 文件不存在于根目录CSS，继续尝试
                }
            } else if (!fileFound && mappedPath.startsWith('/assets/css/')) {
                const rootCssPath = mappedPath.replace('/assets/css/', '/CSS/');
                try {
                    const stats = await fs.promises.stat(path.join(PROJECT_ROOT, rootCssPath));
                    if (stats.isFile()) {
                        requestPath = rootCssPath;
                        fileFound = true;
                    }
                } catch (error) {
                    // 文件不存在于根目录CSS，继续尝试
                }
            }
            
            // 如果文件不存在，尝试在根目录的JS目录下查找
            if (!fileFound && mappedPath.startsWith('/HTML/assets/js/')) {
                const rootJsPath = mappedPath.replace('/HTML/assets/js/', '/JS/');
                try {
                    const stats = await fs.promises.stat(path.join(PROJECT_ROOT, rootJsPath));
                    if (stats.isFile()) {
                        requestPath = rootJsPath;
                        fileFound = true;
                    }
                } catch (error) {
                    // 文件不存在于根目录JS，继续尝试
                }
            } else if (!fileFound && mappedPath.startsWith('/assets/js/')) {
                const rootJsPath = mappedPath.replace('/assets/js/', '/JS/');
                try {
                    const stats = await fs.promises.stat(path.join(PROJECT_ROOT, rootJsPath));
                    if (stats.isFile()) {
                        requestPath = rootJsPath;
                        fileFound = true;
                    }
                } catch (error) {
                    // 文件不存在于根目录JS，继续尝试
                }
            }
            
            // 如果文件不存在于所有上述路径，尝试直接使用Staging下的assets路径
            if (!fileFound) {
                try {
                    // 直接使用原始的Staging路径
                    const stats = await fs.promises.stat(path.join(PROJECT_ROOT, requestPath));
                    if (stats.isFile()) {
                        fileFound = true;
                        // requestPath已经是正确的Staging路径，不需要修改
                    }
                } catch (error) {
                    // 如果仍然不存在，尝试在Staging下的common_styles目录查找
                    if (requestPath.startsWith('/Staging/assets/css/')) {
                        const stagingCommonStylesPath = requestPath.replace('/Staging/assets/css/', '/Staging/assets/css/common_styles/');
                        try {
                            const stats = await fs.promises.stat(path.join(PROJECT_ROOT, stagingCommonStylesPath));
                            if (stats.isFile()) {
                                requestPath = stagingCommonStylesPath;
                                fileFound = true;
                            }
                        } catch (e) {
                            // 所有路径都尝试过了，使用原始映射路径
                            requestPath = mappedPath;
                        }
                    } else {
                        // 所有路径都尝试过了，使用原始映射路径
                        requestPath = mappedPath;
                    }
                }
            }
        }
        // 其他Staging路径保持不变
    } else if (requestPath.startsWith('/HTML/') && requestPath.endsWith('.html')) {
        // 如果已经是完整的HTML路径，直接使用
        // 例如: /HTML/UpdateInfo.html 保持不变
    } else if (requestPath.endsWith('.html')) {
        // 对于其他HTML文件，添加HTML前缀
        // 例如: /UpdateInfo.html -> /HTML/UpdateInfo.html
        requestPath = `/HTML${requestPath}`;
    } else if (!requestPath.startsWith('/HTML/') && !requestPath.includes('.')) {
        // 如果不是HTML路径且没有文件扩展名，尝试在HTML目录中查找
        requestPath = `/HTML${requestPath}.html`;
    }
    
    // 记录请求
    const timestamp = new Date().toISOString();
    const clientIP = req.ip || req.connection.remoteAddress;
    console.log(`[${timestamp}] ${clientIP} "GET ${requestPath}"`);
    
    // 安全检查：防止路径遍历攻击
    if (requestPath.includes('..')) {
        await send404Page(res, requestPath);
        return;
    }
    
    // 检查是否为禁止访问的路径
    if (isForbiddenPath(requestPath)) {
        await send403Page(res, requestPath);
        return;
    }
    
    // 构建文件路径
    const filePath = path.join(PROJECT_ROOT, requestPath);
    
    try {
        // 检查文件是否存在
        const stats = await fs.promises.stat(filePath);
        
        if (stats.isDirectory()) {
            // 如果是目录，尝试查找index.html
            const indexPath = path.join(filePath, 'index.html');
            try {
                const indexStats = await fs.promises.stat(indexPath);
                if (indexStats.isFile()) {
                    const content = await readFile(indexPath);
                    res.writeHead(200, {
                        'Content-Type': 'text/html',
                        'Access-Control-Allow-Origin': '*',
                        'Access-Control-Allow-Methods': 'GET, POST, PUT, DELETE, OPTIONS',
                        'Access-Control-Allow-Headers': 'Content-Type, Authorization'
                    });
                    res.end(content);
                    console.log(`[200] ${indexPath} - text/html`);
                    return;
                } else {
                    await send404Page(res, requestPath);
                    return;
                }
            } catch {
                await send404Page(res, requestPath);
                return;
            }
        }
        
        // 读取并发送文件
        const content = await readFile(filePath);
        const contentType = getContentType(filePath);
        
        // 设置CORS头
        res.writeHead(200, {
            'Content-Type': contentType,
            'Access-Control-Allow-Origin': '*',
            'Access-Control-Allow-Methods': 'GET, POST, PUT, DELETE, OPTIONS',
            'Access-Control-Allow-Headers': 'Content-Type, Authorization'
        });
        
        res.end(content);
        console.log(`[200] ${requestPath} - ${contentType}`);
        
    } catch (error) {
        if (error.code === 'ENOENT') {
            await send404Page(res, requestPath);
        } else if (error.code === 'EACCES') {
            await send403Page(res, requestPath);
        } else {
            res.writeHead(500, { 'Content-Type': 'text/plain' });
            res.end('Internal Server Error');
            console.error(`[500] ${requestPath} - ${error.message}`);
        }
    }
}

// 使用静态文件中间件
app.use(staticFileMiddleware);

// 404处理
app.use(async (req, res) => {
    if (req.path.startsWith('/api/')) {
        res.status(404).json({ error: 'API endpoint not found' });
    } else {
        await send404Page(res, req.path);
    }
});

// 错误处理中间件
app.use((err, req, res, next) => {
    console.error(`[server.js] 服务器错误:`, err);
    res.status(500).json({ 
        error: 'Internal server error',
        message: process.env.NODE_ENV === 'development' ? err.message : '服务器内部错误'
    });
});

/**
 * 创建HTTP服务器
 */
const server = http.createServer(app);

/**
 * 启动服务器
 */
server.listen(PORT, () => {
    console.log(`\n🚀 自定义HTTP服务器已启动`);
    console.log(`📍 服务地址: http://localhost:${PORT}`);
    console.log(`📂 项目目录: ${PROJECT_ROOT}`);
    console.log(`🔧 功能特性:`);
    console.log(`   • 自动404页面挂载`);
    console.log(`   • 自动403页面挂载`);
    console.log(`   • CORS支持`);
    console.log(`   • 安全路径检查`);
    console.log(`   • 静态文件服务`);
    console.log(`   • DeepSeek AI API集成`);
    console.log(`   • 安全模块: 电子签名、Token、证书`);
    console.log(`\n📄 错误页面:`);
    console.log(`   • 404页面: /HTML/404.html`);
    console.log(`   • 403页面: /HTML/403.html`);
    console.log(`\n🔒 安全API端点:`);
    console.log(`   • 登录: http://localhost:${PORT}/api/auth/login`);
    console.log(`   • 数据签名: http://localhost:${PORT}/api/security/sign`);
    console.log(`   • 签名验证: http://localhost:${PORT}/api/security/verify`);
    console.log(`   • 证书信息: http://localhost:${PORT}/api/security/certificate`);
    console.log(`   • 自我修复: http://localhost:${PORT}/api/security/repair`);
    console.log(`\n🤖 AI API端点:`);
    console.log(`   • 健康检查: http://localhost:${PORT}/api/health`);
    console.log(`   • AI聊天: http://localhost:${PORT}/api/deepseek/chat`);
    console.log(`   • 代码生成: http://localhost:${PORT}/api/deepseek/generate-code`);
    console.log(`   • 文本分析: http://localhost:${PORT}/api/deepseek/analyze-text`);
    console.log(`   • 文本翻译: http://localhost:${PORT}/api/deepseek/translate`);
    console.log(`   • 文本摘要: http://localhost:${PORT}/api/deepseek/summarize`);
    console.log(`   • 状态查询: http://localhost:${PORT}/api/deepseek/status`);
    console.log(`\n⏰ 启动时间: ${new Date().toLocaleString('zh-CN')}`);
    console.log(`\n按 Ctrl+C 停止服务器\n`);
});

/**
 * 优雅关闭
 */
process.on('SIGINT', () => {
    console.log('\n🛑 正在关闭服务器...');
    server.close(() => {
        console.log('✅ 服务器已关闭');
        process.exit(0);
    });
});

/**
 * 错误处理
 */
server.on('error', (error) => {
    if (error.code === 'EADDRINUSE') {
        console.error(`[server.js] ❌ 端口 ${PORT} 已被占用，请检查是否有其他服务在运行`);
    } else {
        console.error(`[server.js] ❌ 服务器错误: ${error.message}`);
    }
    process.exit(1);
});

module.exports = server;