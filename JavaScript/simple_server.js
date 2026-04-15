const http = require('http');
const fs = require('fs');
const path = require('path');

const PORT = 8080;
const BASE_DIR = path.join(__dirname, 'HTML');

// MIME类型映射
const mimeTypes = {
  '.html': 'text/html',
  '.css': 'text/css',
  '.js': 'text/javascript',
  '.svg': 'image/svg+xml',
  '.png': 'image/png',
  '.jpg': 'image/jpeg',
  '.json': 'application/json'
};

// 创建简单的HTTP服务器
const server = http.createServer((req, res) => {
  console.log(`请求: ${req.url}`);
  
  // 处理根路径
  let filePath = req.url === '/' ? '/index.html' : req.url;
  
  // 特殊处理about文件夹中的文件
  if (['/news.html', '/team.html', '/history.html', '/company.html'].includes(filePath)) {
    filePath = `/about${filePath}`;
  }
  
  // 处理CSS请求
  if (filePath.startsWith('/CSS/')) {
    filePath = path.join(__dirname, filePath);
  } 
  // 处理JavaScript请求
  else if (filePath.startsWith('/JavaScript/')) {
    filePath = path.join(__dirname, filePath);
  }
  // 处理Encrypted_JS请求
  else if (filePath.startsWith('/Encrypted_JS/')) {
    filePath = path.join(__dirname, filePath);
  }
  // 处理其他静态文件
  else {
    filePath = path.join(BASE_DIR, filePath);
  }
  
  // 获取文件扩展名以确定MIME类型
  const extname = String(path.extname(filePath)).toLowerCase();
  const contentType = mimeTypes[extname] || 'application/octet-stream';
  
  // 读取并发送文件
  fs.readFile(filePath, (error, content) => {
    if (error) {
      console.error(`错误: ${error.message}`);
      
      if (error.code === 'ENOENT') {
        // 文件不存在
        res.writeHead(404);
        res.end('404 页面未找到');
      } else {
        // 服务器错误
        res.writeHead(500);
        res.end('500 服务器错误');
      }
    } else {
      // 成功发送文件
      res.writeHead(200, { 'Content-Type': contentType });
      res.end(content, 'utf-8');
      console.log(`成功发送: ${filePath}`);
    }
  });
});

// 启动服务器
server.listen(PORT, '0.0.0.0', () => {
  console.log(`简单服务器启动在 http://0.0.0.0:${PORT}`);
  console.log('支持的路径:');
  console.log('- http://localhost:3000/ (主页)');
  console.log('- http://localhost:3000/about.html');
  console.log('- http://localhost:3000/news.html');
  console.log('- http://localhost:3000/team.html');
  console.log('- http://localhost:3000/history.html');
  console.log('- http://localhost:3000/company.html');
});