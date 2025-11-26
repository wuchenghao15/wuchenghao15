const http = require('http');
const fs = require('fs');
const path = require('path');

// 端口
const PORT = 3000;

// MIME类型映射
const mimeTypes = {
  '.html': 'text/html',
  '.css': 'text/css',
  '.js': 'text/javascript',
  '.json': 'application/json',
  '.png': 'image/png',
  '.jpg': 'image/jpeg',
  '.gif': 'image/gif',
  '.svg': 'image/svg+xml',
  '.ico': 'image/x-icon'
};

// 创建服务器
const server = http.createServer((req, res) => {
  console.log(`[${new Date().toISOString()}] 请求路径: ${req.url}`);
  
  // 处理路径
  let filePath = req.url === '/' ? '/index.html' : req.url;
  
  // 特殊处理页面路由
  if (filePath.startsWith('/news.html')) {
    filePath = '/HTML/about/news.html';
  } else if (filePath.startsWith('/team.html')) {
    filePath = '/HTML/about/team.html';
  } else if (filePath.startsWith('/history.html')) {
    filePath = '/HTML/about/history.html';
  } else if (filePath.startsWith('/company.html')) {
    filePath = '/HTML/about/company.html';
  } else if (filePath.startsWith('/about.html')) {
    filePath = '/HTML/about.html';
  } else if (filePath.startsWith('/index.html')) {
    filePath = '/HTML/index.html';
  }
  
  // 静态文件路径处理
  if (!filePath.includes('/HTML/') && !filePath.includes('/CSS/') && 
      !filePath.includes('/JavaScript/') && !filePath.includes('/Encrypted_JS/')) {
    // 检查是否是常见静态文件类型
    const ext = path.extname(filePath);
    if (mimeTypes[ext]) {
      // 尝试不同的目录
      const possiblePaths = [
        `/HTML${filePath}`,
        `/CSS${filePath}`,
        `/JavaScript${filePath}`,
        `/Encrypted_JS${filePath}`
      ];
      
      for (const possiblePath of possiblePaths) {
        const fullPath = path.join(__dirname, possiblePath);
        if (fs.existsSync(fullPath)) {
          filePath = possiblePath;
          break;
        }
      }
    }
  }
  
  // 构建完整文件路径
  const fullPath = path.join(__dirname, filePath);
  console.log(`[${new Date().toISOString()}] 尝试读取文件: ${fullPath}`);
  
  // 检查文件是否存在
  fs.exists(fullPath, (exists) => {
    if (!exists) {
      console.log(`[${new Date().toISOString()}] 文件不存在: ${fullPath}`);
      res.writeHead(404, { 'Content-Type': 'text/html' });
      res.end(`<h1>404 页面未找到</h1><p>请求的路径: ${req.url}</p><p>尝试的文件路径: ${fullPath}</p>`);
      return;
    }
    
    // 读取文件
    fs.readFile(fullPath, (err, content) => {
      if (err) {
        console.error(`[${new Date().toISOString()}] 读取文件错误: ${err.message}`);
        res.writeHead(500, { 'Content-Type': 'text/html' });
        res.end(`<h1>500 服务器错误</h1><p>错误信息: ${err.message}</p>`);
        return;
      }
      
      // 设置MIME类型
      const ext = path.extname(fullPath);
      const contentType = mimeTypes[ext] || 'application/octet-stream';
      
      console.log(`[${new Date().toISOString()}] 成功读取文件: ${fullPath}, 内容类型: ${contentType}`);
      
      // 返回文件内容
      res.writeHead(200, { 'Content-Type': contentType });
      res.end(content);
    });
  });
});

// 启动服务器
server.listen(PORT, '0.0.0.0', () => {
  console.log(`[${new Date().toISOString()}] 调试服务器启动在 http://0.0.0.0:${PORT}`);
  console.log(`[${new Date().toISOString()}] 支持的页面:`);
  console.log(`[${new Date().toISOString()}] - http://localhost:${PORT}/index.html`);
  console.log(`[${new Date().toISOString()}] - http://localhost:${PORT}/about.html`);
  console.log(`[${new Date().toISOString()}] - http://localhost:${PORT}/news.html`);
  console.log(`[${new Date().toISOString()}] - http://localhost:${PORT}/team.html`);
  console.log(`[${new Date().toISOString()}] - http://localhost:${PORT}/history.html`);
  console.log(`[${new Date().toISOString()}] - http://localhost:${PORT}/company.html`);
});

// 监听错误
server.on('error', (err) => {
  console.error(`[${new Date().toISOString()}] 服务器错误: ${err.message}`);
});

console.log(`[${new Date().toISOString()}] 服务器初始化中...`);