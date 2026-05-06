/**
 * Flask框架适配模块
 * 用于将现有Express项目适配到Flask框架
 */

const fs = require('fs');
const path = require('path');
const { exec } = require('child_process');
const util = require('util');
const winston = require('winston');

// 配置日志
const logger = winston.createLogger({
    level: process.env.LOG_LEVEL || 'info',
    format: winston.format.combine(
        winston.format.timestamp(),
        winston.format.json()
    ),
    transports: [
        new winston.transports.File({
            filename: `${process.env.LOG_DIR || './Logs'}/flask-adapter.log`,
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

// Flask适配类
class FlaskAdapter {
    constructor(projectRoot) {
        this.projectRoot = projectRoot;
        this.flaskRoot = path.join(projectRoot, 'flask-app');
        this.expressRoot = projectRoot;
        this.execPromise = util.promisify(exec);
    }
    
    /**
     * 初始化Flask项目结构
     */
    async initializeFlaskProject() {
        logger.info(`🚀 初始化Flask项目结构...`);
        
        try {
            // 创建Flask项目目录
            if (!fs.existsSync(this.flaskRoot)) {
                fs.mkdirSync(this.flaskRoot, { recursive: true });
            }
            
            // 创建基本的Flask项目文件结构
            const flaskStructure = {
                'app.py': this.createAppPy(),
                'requirements.txt': this.createRequirementsTxt(),
                'templates/index.html': this.createTemplateIndex(),
                'static/css/style.css': this.createStaticCss(),
                'static/js/script.js': this.createStaticJs(),
                'config.py': this.createConfigPy()
            };
            
            // 创建所有文件
            for (const [filePath, content] of Object.entries(flaskStructure)) {
                const fullPath = path.join(this.flaskRoot, filePath);
                const dir = path.dirname(fullPath);
                
                if (!fs.existsSync(dir)) {
                    fs.mkdirSync(dir, { recursive: true });
                }
                
                fs.writeFileSync(fullPath, content);
                logger.info(`✅ 创建Flask文件: ${filePath}`);
            }
            
            logger.info(`✅ Flask项目结构初始化完成`);
            return true;
            
        } catch (error) {
            logger.error(`❌ 初始化Flask项目结构时发生错误: ${error.message}`);
            return false;
        }
    }
    
    /**
     * 创建app.py文件
     */
    createAppPy() {
        return `from flask import Flask, render_template, request, jsonify
import config

app = Flask(__name__)
app.config.from_object(config.Config)

# 首页路由
@app.route('/')
def index():
    return render_template('index.html')

# API路由示例
@app.route('/api/health', methods=['GET'])
def health_check():
    return jsonify({"status": "ok", "message": "Server is running"})

# 用户相关路由
@app.route('/api/users', methods=['GET'])
def get_users():
    # 这里可以替换为实际的数据库查询
    users = [
        {"id": 1, "username": "admin", "email": "admin@example.com"},
        {"id": 2, "username": "user", "email": "user@example.com"}
    ]
    return jsonify({"success": True, "users": users, "total": len(users)})

# 登录路由
@app.route('/api/auth/login', methods=['POST'])
def login():
    data = request.get_json()
    username = data.get('username')
    password = data.get('password')
    
    # 这里可以替换为实际的用户验证逻辑
    if username == 'admin' and password == 'admin123':
        return jsonify({
            "success": True,
            "message": "登录成功",
            "user": {"username": username, "role": "admin"}
        })
    
    return jsonify({"success": False, "message": "用户名或密码不正确"}), 401

# 注册路由
@app.route('/api/auth/register', methods=['POST'])
def register():
    data = request.get_json()
    username = data.get('username')
    email = data.get('email')
    password = data.get('password')
    
    # 这里可以替换为实际的用户注册逻辑
    return jsonify({
        "success": True,
        "message": "注册成功",
        "user": {"username": username, "email": email}
    })

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
`;
    }
    
    /**
     * 创建requirements.txt文件
     */
    createRequirementsTxt() {
        return `Flask==3.0.0
Flask-CORS==4.0.0
PyJWT==2.8.0
python-dotenv==1.0.0
`;
    }
    
    /**
     * 创建配置文件
     */
    createConfigPy() {
        return `import os

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev-secret-key'
    DEBUG = True
    
    # 数据库配置（示例）
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or 'sqlite:///app.db'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
`;
    }
    
    /**
     * 创建模板index.html
     */
    createTemplateIndex() {
        return `<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>MTSCOS AI 项目管理系统</title>
    <link rel="stylesheet" href="{{ url_for('static', filename='css/style.css') }}">
</head>
<body>
    <div class="auth-container">
        <div class="auth-card">
            <div class="auth-header">
                <h2>登录系统</h2>
                <p>MTSCOS AI 项目管理系统</p>
            </div>
            
            <div class="auth-tabs">
                <button class="auth-tab active" id="login-tab">登录</button>
                <button class="auth-tab" id="register-tab">注册</button>
            </div>
            
            <!-- 登录表单 -->
            <form class="auth-form active" id="login-form">
                <div class="form-group">
                    <label for="login-username">用户名</label>
                    <input type="text" id="login-username" name="username" required>
                </div>
                
                <div class="form-group">
                    <label for="login-password">密码</label>
                    <input type="password" id="login-password" name="password" required>
                </div>
                
                <button type="submit" class="btn btn-primary w-full">登录</button>
            </form>
            
            <!-- 注册表单 -->
            <form class="auth-form" id="register-form">
                <div class="form-group">
                    <label for="register-username">用户名</label>
                    <input type="text" id="register-username" name="username" required>
                </div>
                
                <div class="form-group">
                    <label for="register-email">邮箱</label>
                    <input type="email" id="register-email" name="email" required>
                </div>
                
                <div class="form-group">
                    <label for="register-password">密码</label>
                    <input type="password" id="register-password" name="password" required>
                </div>
                
                <button type="submit" class="btn btn-primary w-full">注册</button>
            </form>
        </div>
    </div>
    
    <script src="{{ url_for('static', filename='js/script.js') }}"></script>
</body>
</html>`;
    }
    
    /**
     * 创建静态CSS文件
     */
    createStaticCss() {
        return `/* 基础样式 */
* {
    margin: 0;
    padding: 0;
    box-sizing: border-box;
}

body {
    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    min-height: 100vh;
    display: flex;
    align-items: center;
    justify-content: center;
}

/* 认证容器 */
.auth-container {
    width: 100%;
    max-width: 450px;
    padding: 20px;
}

/* 认证卡片 */
.auth-card {
    background: white;
    border-radius: 12px;
    box-shadow: 0 20px 40px rgba(0, 0, 0, 0.1);
    overflow: hidden;
}

/* 认证头部 */
.auth-header {
    text-align: center;
    padding: 30px 20px;
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    color: white;
}

.auth-header h2 {
    font-size: 24px;
    margin-bottom: 8px;
    font-weight: 600;
}

.auth-header p {
    font-size: 14px;
    opacity: 0.9;
}

/* 标签页 */
.auth-tabs {
    display: flex;
    border-bottom: 1px solid #e0e0e0;
}

.auth-tab {
    flex: 1;
    padding: 15px;
    border: none;
    background: none;
    font-size: 16px;
    font-weight: 500;
    color: #666;
    cursor: pointer;
    transition: all 0.3s ease;
}

.auth-tab.active {
    color: #667eea;
    border-bottom: 2px solid #667eea;
}

.auth-tab:hover {
    color: #764ba2;
}

/* 表单样式 */
.auth-form {
    padding: 30px 20px;
    display: none;
}

.auth-form.active {
    display: block;
}

.form-group {
    margin-bottom: 20px;
}

.form-group label {
    display: block;
    margin-bottom: 8px;
    font-weight: 500;
    color: #333;
}

.form-group input {
    width: 100%;
    padding: 12px;
    border: 1px solid #ddd;
    border-radius: 8px;
    font-size: 16px;
    transition: border-color 0.3s ease;
}

.form-group input:focus {
    outline: none;
    border-color: #667eea;
    box-shadow: 0 0 0 2px rgba(102, 126, 234, 0.1);
}

/* 按钮样式 */
.btn {
    padding: 12px 20px;
    border: none;
    border-radius: 8px;
    font-size: 16px;
    font-weight: 500;
    cursor: pointer;
    transition: all 0.3s ease;
    text-decoration: none;
    display: inline-block;
    text-align: center;
}

.btn-primary {
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    color: white;
}

.btn-primary:hover {
    transform: translateY(-2px);
    box-shadow: 0 8px 16px rgba(102, 126, 234, 0.3);
}

/* 响应式设计 */
@media (max-width: 500px) {
    .auth-container {
        padding: 10px;
    }
    
    .auth-header {
        padding: 20px 15px;
    }
    
    .auth-form {
        padding: 20px 15px;
    }
}
`;
    }
    
    /**
     * 创建静态JS文件
     */
    createStaticJs() {
        return `// 表单切换功能
const loginTab = document.getElementById('login-tab');
const registerTab = document.getElementById('register-tab');
const loginForm = document.getElementById('login-form');
const registerForm = document.getElementById('register-form');

// 切换到登录表单
loginTab.addEventListener('click', () => {
    loginTab.classList.add('active');
    registerTab.classList.remove('active');
    loginForm.classList.add('active');
    registerForm.classList.remove('active');
});

// 切换到注册表单
registerTab.addEventListener('click', () => {
    registerTab.classList.add('active');
    loginTab.classList.remove('active');
    registerForm.classList.add('active');
    loginForm.classList.remove('active');
});

// 登录表单提交
loginForm.addEventListener('submit', async (e) => {
    e.preventDefault();
    
    const formData = new FormData(loginForm);
    const data = {
        username: formData.get('username'),
        password: formData.get('password')
    };
    
    try {
        const response = await fetch('/api/auth/login', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(data)
        });
        
        const result = await response.json();
        if (result.success) {
            alert('登录成功！');
            // 可以添加跳转到其他页面的逻辑
        } else {
            alert('登录失败：' + result.message);
        }
    } catch (error) {
        console.error('登录错误：', error);
        alert('登录过程中发生错误');
    }
});

// 注册表单提交
registerForm.addEventListener('submit', async (e) => {
    e.preventDefault();
    
    const formData = new FormData(registerForm);
    const data = {
        username: formData.get('username'),
        email: formData.get('email'),
        password: formData.get('password')
    };
    
    try {
        const response = await fetch('/api/auth/register', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(data)
        });
        
        const result = await response.json();
        if (result.success) {
            alert('注册成功！');
            // 可以添加跳转到登录页面的逻辑
            loginTab.click();
        } else {
            alert('注册失败：' + result.message);
        }
    } catch (error) {
        console.error('注册错误：', error);
        alert('注册过程中发生错误');
    }
});
`;
    }
    
    /**
     * 安装Flask依赖
     */
    async installFlaskDependencies() {
        logger.info(`📦 安装Flask依赖...`);
        
        try {
            await this.execPromise(
                `cd ${this.flaskRoot} && pip install -r requirements.txt`,
                { cwd: this.projectRoot }
            );
            
            logger.info(`✅ Flask依赖安装完成`);
            return true;
            
        } catch (error) {
            logger.error(`❌ 安装Flask依赖时发生错误: ${error.message}`);
            return false;
        }
    }
    
    /**
     * 启动Flask开发服务器
     */
    async startFlaskServer() {
        logger.info(`🔥 启动Flask开发服务器...`);
        
        try {
            // 在后台启动Flask服务器
            const flaskProcess = exec(
                `cd ${this.flaskRoot} && python app.py`,
                { cwd: this.projectRoot }
            );
            
            // 捕获输出
            flaskProcess.stdout.on('data', (data) => {
                logger.info(`[Flask] ${data}`);
            });
            
            flaskProcess.stderr.on('data', (data) => {
                logger.error(`[Flask Error] ${data}`);
            });
            
            // 等待服务器启动
            await new Promise(resolve => setTimeout(resolve, 3000));
            
            logger.info(`✅ Flask服务器已启动，访问地址: http://localhost:5000`);
            return flaskProcess;
            
        } catch (error) {
            logger.error(`❌ 启动Flask服务器时发生错误: ${error.message}`);
            return null;
        }
    }
    
    /**
     * 生成Flask适配报告
     */
    generateAdaptationReport() {
        return {
            projectRoot: this.projectRoot,
            flaskRoot: this.flaskRoot,
            expressRoot: this.expressRoot,
            timestamp: new Date().toISOString(),
            status: 'completed',
            flaskVersion: '3.0.0',
            features: [
                '基本Flask应用结构',
                '认证系统（登录/注册）',
                'API路由示例',
                '模板系统',
                '静态文件服务'
            ],
            instructions: {
                install: 'cd flask-app && pip install -r requirements.txt',
                run: 'cd flask-app && python app.py',
                access: 'http://localhost:5000'
            }
        };
    }
}

// 导出FlaskAdapter类
module.exports = FlaskAdapter;