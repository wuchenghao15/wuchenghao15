#!/bin/bash

# MTSCOS AI 项目自包含部署脚本
# 目标服务器: 172.16.0.196
# 功能: 创建部署包并通过HTTP上传

set -e

echo "🚀 开始创建MTSCOS AI项目部署包..."

# 1. 清理和优化项目
echo "🧹 清理和优化项目..."
npm run clean || true

# 2. 创建部署目录
echo "📁 创建部署目录..."
mkdir -p deploy-package

# 3. 复制必要的文件
echo "📋 复制项目文件..."
cp -r package.json package-lock.json src config data models deploy.sh deploy-package/
cp -r docs README.md ARCHITECTURE_DESIGN.md deploy-package/

# 4. 创建启动脚本
echo "🔧 创建启动脚本..."
cat > deploy-package/start.sh << 'EOF'
#!/bin/bash

# MTSCOS AI 项目启动脚本
set -e

echo "🚀 启动MTSCOS AI项目..."

# 安装依赖
echo "📦 安装项目依赖..."
npm install --production

# 创建必要的目录
echo "📁 创建必要的目录..."
mkdir -p Logs storage data

# 修复权限
echo "🔒 修复文件权限..."
chmod -R 755 .

# 启动项目
echo "🚀 启动服务器..."
npm start
EOF

chmod +x deploy-package/start.sh

# 5. 创建README部署说明
echo "📄 创建部署说明..."
cat > deploy-package/DEPLOYMENT.md << 'EOF'
# MTSCOS AI 项目部署说明

## 目标服务器
- IP地址: 172.16.0.196
- 端口: 80 (HTTP), 8081 (应用)
- 服务器类型: Microsoft-IIS/10.0

## 部署步骤

### 方法1: 通过WebDAV上传
1. 打开Windows资源管理器
2. 输入地址: `\\172.16.0.196\web`
3. 输入认证凭据
4. 将部署包复制到服务器
5. 运行 `start.sh` 脚本

### 方法2: 通过远程桌面
1. 使用远程桌面连接到 172.16.0.196
2. 复制部署包到服务器
3. 打开命令提示符
4. 运行 `start.sh` 脚本

### 方法3: 通过PowerShell
1. 打开PowerShell
2. 使用 `Copy-Item` 命令复制文件
3. 使用 `Invoke-Command` 运行启动脚本

## 访问地址
- 应用主页: http://172.16.0.196:8081
- 健康检查: http://172.16.0.196:8081/api/health
- API文档: http://172.16.0.196:8081/api

## 故障排除
1. 检查端口8081是否已开放
2. 检查防火墙设置
3. 查看 Logs 目录中的日志文件
4. 确保Node.js已安装在服务器上

## 项目特性
- 双重密码加密 (bcrypt + HMAC-SHA256)
- 反逆向工程保护
- AI引擎集成 (7个本地AI引擎)
- 实时监控和自动优化
- 数据安全和完整性检查
EOF

# 6. 压缩部署包
echo "📦 压缩部署包..."
cd deploy-package
zip -r mtscos-ai-project-deploy.zip ./*
cd ..

# 7. 检查部署包
echo "📋 检查部署包..."
ls -la deploy-package/

# 8. 尝试通过HTTP上传
echo "🌐 尝试上传部署包..."
curl -v -X PUT -u "username:password" --data-binary @deploy-package/mtscos-ai-project-deploy.zip http://172.16.0.196/mtscos-ai-project-deploy.zip || {
    echo "⚠️ HTTP上传失败，需要认证凭据"
    echo "📁 部署包已创建: deploy-package/mtscos-ai-project-deploy.zip"
    echo "📄 请使用服务器认证凭据手动上传部署包"
}

echo "🎉 部署包创建完成！"
echo "📦 部署包位置: deploy-package/mtscos-ai-project-deploy.zip"
echo "📄 部署说明: deploy-package/DEPLOYMENT.md"
echo "🚀 请按照部署说明完成项目发布"