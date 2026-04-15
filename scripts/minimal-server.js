/**
 * 极简服务器 - 用于排查启动问题
 */

const express = require('express');
const app = express();
const PORT = 8080;

// 静态文件服务
app.use('/html', express.static(__dirname + '/../src/html'));

// 根路径
app.get('/', (req, res) => {
    res.redirect('/html/index.html');
});

// 健康检查
app.get('/api/health', (req, res) => {
    res.json({
        status: 'ok',
        message: 'Server is running'
    });
});

// 启动服务器
console.log('Starting minimal server...');
app.listen(PORT, () => {
    console.log('Server running on http://localhost:8080');
    console.log('Static files: http://localhost:8080/html');
});