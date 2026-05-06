/**
 * MTSCOS AI 系统 - API入口文件
 * 优化后的API路由结构，提供健康检查和完整的文档支持
 */

const express = require("express");
const router = express.Router();

/**
 * @swagger
 * /api/health: 
 *   get:
 *     summary: 健康检查
 *     description: 检查API服务是否正常运行
 *     responses:
 *       200:
 *         description: 服务正常
 *         content:
 *           application/json:
 *             schema:
 *               type: object
 *               properties:
 *                 status:
 *                   type: string
 *                   example: ok
 *                 timestamp:
 *                   type: string
 *                   format: date-time
 *                 service:
 *                   type: string
 *                   example: MTSCOS AI API
 *                 version:
 *                   type: string
 *                   example: 1.0.0
 */
router.get("/health", (req, res) => {
    res.status(200).json({
        status: 'ok',
        timestamp: new Date().toISOString(),
        service: 'MTSCOS AI API',
        version: '1.0.0',
        uptime: process.uptime(),
        environment: process.env.NODE_ENV || 'development',
        memoryUsage: process.memoryUsage()
    });
});

/**
 * @swagger
 * /api/info: 
 *   get:
 *     summary: API信息
 *     description: 获取API的详细信息和可用端点
 *     responses:
 *       200:
 *         description: API信息
 *         content:
 *           application/json:
 *             schema:
 *               type: object
 *               properties:
 *                 name:
 *                   type: string
 *                   example: MTSCOS AI API
 *                 version:
 *                   type: string
 *                   example: 1.0.0
 *                 description:
 *                   type: string
 *                   example: MTSCOS AI系统API接口
 *                 endpoints:
 *                   type: object
 */
router.get("/info", (req, res) => {
    res.status(200).json({
        name: 'MTSCOS AI API',
        version: '1.0.0',
        description: 'MTSCOS AI系统API接口',
        documentation: 'https://your-api-docs-url.com',
        contact: {
            name: 'API Support',
            email: 'support@mtscos.com'
        },
        endpoints: {
            health: '/api/health',
            info: '/api/info',
            // 其他API端点将在此处动态生成
        },
        supportedMethods: ['GET', 'POST', 'PUT', 'DELETE'],
        rateLimits: {
            windowMs: 900000, // 15分钟
            max: 100 // 每个IP限制100个请求
        }
    });
});

/**
 * 路由组织示例
 * 建议按功能模块组织路由
 */
try {
    // 示例：用户管理路由
    // router.use("/users", require("./users"));
    
    // 示例：项目管理路由
    // router.use("/projects", require("./projects"));
    
    // 示例：AI功能路由
    // router.use("/ai", require("./ai"));
    
    // 示例：配置管理路由
    // router.use("/config", require("./config"));
    
    console.log("✅ API路由加载完成");
} catch (error) {
    console.error("❌ API路由加载失败:", error);
    // 记录错误，但不影响服务启动
}

/**
 * API错误处理中间件
 */
router.use((err, req, res, next) => {
    console.error("API错误:", err);
    
    const statusCode = err.statusCode || 500;
    const message = err.message || 'Internal Server Error';
    
    res.status(statusCode).json({
        success: false,
        error: {
            message: message,
            code: statusCode,
            timestamp: new Date().toISOString(),
            path: req.path,
            method: req.method,
            // 开发环境下显示详细错误
            stack: process.env.NODE_ENV === 'development' ? err.stack : undefined
        }
    });
});

module.exports = router;


// 初始化机制
const init = () => {
    console.log("Initializing module...");
    // 在这里添加初始化逻辑
    // 例如：加载配置、初始化依赖、设置事件监听等
    
    // 示例：加载配置
    // const config = loadConfig();
    
    // 示例：初始化依赖
    // initializeDependencies();
    
    // 示例：设置事件监听
    // setupEventListeners();
    
    console.log("Module initialized successfully!");
};

// 自动初始化
if (typeof window !== 'undefined') {
    // 浏览器环境：DOM加载完成后初始化
    if (document.readyState === 'loading') {
        document.addEventListener("DOMContentLoaded", init);
    } else {
        init();
    }
} else {
    // Node.js环境：导出初始化函数
    if (typeof module !== 'undefined' && module.exports) {
        module.exports.init = init;
    }
}
