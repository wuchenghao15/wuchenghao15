// MTSCOS AI Project - 主入口文件
const express = require('express');
const bodyParser = require('body-parser');
const cors = require('cors');
const winston = require('winston');

// 创建日志记录器
const logger = winston.createLogger({
  level: 'info',
  format: winston.format.combine(
    winston.format.timestamp(),
    winston.format.json()
  ),
  defaultMeta: { service: 'mtscos-server' },
  transports: [
    new winston.transports.File({ filename: '../Logs/error.log', level: 'error' }),
    new winston.transports.File({ filename: '../Logs/combined.log' }),
  ],
});

// 如果不是生产环境，添加控制台输出
if (process.env.NODE_ENV !== 'production') {
  logger.add(new winston.transports.Console({
    format: winston.format.simple(),
  }));
}

const app = express();
const PORT = 3000;

// 中间件
app.use(cors());
app.use(bodyParser.json());
app.use(express.static('../HTML'));
app.use(express.static('../CSS'));

// 基本路由
app.get('/', (req, res) => {
  res.sendFile('../HTML/index.html', { root: __dirname });
});

// API路由
app.get('/api/status', (req, res) => {
  res.json({ status: 'ok', message: 'MTSCOS AI Project is running' });
});

// 启动服务器
app.listen(PORT, () => {
  console.log();
  logger.info();
});

// 错误处理
app.use((err, req, res, next) => {
  console.error(err.stack);
  logger.error(err.message);
  res.status(500).send('Something broke!');
});
