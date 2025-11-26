const http = require('http');
const httpProxy = require('http-proxy');
const fs = require('fs');
const path = require('path');

// 创建代理服务器
const proxy = httpProxy.createProxyServer({});

// MIME类型映射
const mimeTypes = {
    '.html': 'text/html',
    '.css': 'text/css',
    '.js': 'application/javascript',
    '.json': 'application/json',
    '.png': 'image/png',
    '.jpg': 'image/jpeg',
    '.gif': 'image/gif',
    '.svg': 'image/svg+xml'
};

// 创建HTTP服务器
const server = http.createServer((req, res) => {
    console.log(`[${new Date().toISOString()}] ${req.method} ${req.url}`);
    
    // 处理API请求 - 代理到端口3001
    if (req.url.startsWith('/api/')) {
        proxy.web(req, res, { target: 'http://localhost:3001' });
    } else {
        // 静态文件服务
        let filePath = req.url === '/' ? '/index.html' : req.url;
        filePath = path.join(__dirname, filePath);
        
        const ext = path.extname(filePath);
        const contentType = mimeTypes[ext] || 'text/plain';
        
        fs.readFile(filePath, (err, content) => {
            if (err) {
                if (err.code === 'ENOENT') {
                    res.writeHead(404, { 'Content-Type': 'text/plain' });
                    res.end('文件未找到');
                } else {
                    res.writeHead(500, { 'Content-Type': 'text/plain' });
                    res.end('服务器内部错误');
                }
            } else {
                res.writeHead(200, { 'Content-Type': contentType });
                res.end(content);
            }
        });
    }
});

// 代理错误处理
proxy.on('error', (err, req, res) => {
    console.error(`[proxy-server.js] Proxy error:, err`);
    res.writeHead(500, { 'Content-Type': 'text/plain' });
    res.end('API服务器连接失败');
});

// 启动服务器
const PORT = 8085;
server.listen(PORT, () => {
    console.log(`代理服务器运行在 http://localhost:${PORT}`);
    console.log('API请求将被代理到 http://localhost:3001');
    console.log('静态文件服务已启用');
});