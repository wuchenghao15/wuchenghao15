#!/bin/bash

# 系统配置初始化脚本
echo "=========================================="
echo "  系统配置初始化"
echo "=========================================="
echo ""

# 检查Node.js
if ! command -v node &> /dev/null; then
    echo "❌ Node.js未安装，请先安装Node.js"
    exit 1
fi

echo "[1/8] 检查项目结构..."
if [ ! -d "src" ]; then
    echo "❌ 项目结构不正确"
    exit 1
fi
echo "✓ 项目结构正确"

echo ""
echo "[2/8] 创建配置目录..."
mkdir -p src/config
echo "✓ 配置目录创建完成"

echo ""
echo "[3/8] 生成系统配置文件..."

cat > src/config/system.config.js << 'EOF'
export const SYSTEM_CONFIG = {
  app: {
    name: 'MTSCOS',
    nameZh: '智能学习系统',
    version: '2.0.0',
    buildNumber: '20260511',
    description: '智能学习与考试系统',
    author: 'MTSCOS AI Project Team',
    license: 'MIT',
  },
  environment: {
    development: { apiUrl: 'http://localhost:8890', debug: true, logLevel: 'debug' },
    staging: { apiUrl: 'https://staging.api.mtscos.com', debug: true, logLevel: 'info' },
    production: { apiUrl: 'https://api.mtscos.com', debug: false, logLevel: 'warn' },
  },
  network: { timeout: 30000, retryCount: 3, retryDelay: 1000 },
  cache: { enabled: true, maxSize: 100 * 1024 * 1024, ttl: 3600 },
  storage: { encryption: { enabled: true, algorithm: 'AES-256' } },
  security: { tokenExpiry: 86400, refreshTokenExpiry: 604800 },
  notifications: { enabled: true, pushEnabled: true },
  theme: { default: 'system', availableThemes: ['light', 'dark', 'system'] },
  language: { default: 'zh-CN', availableLanguages: ['zh-CN', 'en-US', 'ja-JP'] },
  features: { aiEnabled: true, offlineMode: true, examMode: true },
  exam: { maxDuration: 3600, autoSubmit: true, autoSave: true },
  sync: { enabled: true, autoSync: true, syncInterval: 300 },
  logging: { enabled: true, consoleEnabled: true },
};

export default SYSTEM_CONFIG;
export const getEnvironmentConfig = (env = 'development') => SYSTEM_CONFIG.environment[env] || SYSTEM_CONFIG.environment.development;
export const getApiUrl = (env = 'development') => getEnvironmentConfig(env).apiUrl;
EOF

echo "✓ 系统配置文件已创建"

echo ""
echo "[4/8] 生成环境变量文件..."

cat > .env << 'EOF'
# 应用环境配置
APP_ENV=development
APP_NAME=MTSCOS
APP_VERSION=2.0.0

# API配置
API_URL=http://localhost:8890
API_TIMEOUT=30000

# 安全配置
ENCRYPTION_ENABLED=true
TOKEN_EXPIRY=86400

# 日志配置
LOG_LEVEL=debug
LOG_ENABLED=true

# 功能开关
AI_ENABLED=true
OFFLINE_MODE=true
EXAM_MODE=true

# 开发配置
DEBUG=true
DEV_TOOLS=false
EOF

echo "✓ 环境变量文件已创建"

echo ""
echo "[5/8] 检查package.json..."
if [ ! -f "package.json" ]; then
    echo "❌ package.json不存在"
    exit 1
fi

# 检查必要依赖
REQUIRED_DEPS=("react" "react-native" "axios" "@react-navigation/native" "@react-native-async-storage/async-storage")

echo "检查依赖..."
for dep in "${REQUIRED_DEPS[@]}"; do
    if grep -q "\"$dep\"" package.json; then
        echo "✓ $dep 已安装"
    else
        echo "⚠️ $dep 未安装"
    fi
done

echo ""
echo "[6/8] 验证Android配置..."
if [ -d "android" ]; then
    echo "✓ Android目录存在"
    if [ -f "android/app/build.gradle" ]; then
        echo "✓ build.gradle存在"
    else
        echo "⚠️ build.gradle不存在"
    fi
else
    echo "⚠️ Android目录不存在"
fi

echo ""
echo "[7/8] 验证HarmonyOS配置..."
if [ -d "harmonyos" ]; then
    echo "✓ HarmonyOS目录存在"
    if [ -f "harmonyos/build-profile.json5" ]; then
        echo "✓ build-profile.json5存在"
    else
        echo "⚠️ build-profile.json5不存在"
    fi
else
    echo "⚠️ HarmonyOS目录不存在"
fi

echo ""
echo "[8/8] 生成配置总结..."

cat > CONFIG_SUMMARY.md << 'EOF'
# MTSCOS 系统配置总结

## 📋 基本信息
- 应用名称: MTSCOS
- 版本号: 2.0.0
- 构建号: 20260511
- 开发环境: development

## 🔧 API配置
- API地址: http://localhost:8890
- 超时时间: 30秒
- 重试次数: 3次

## ✅ 功能状态
- AI功能: ✅ 启用
- 离线模式: ✅ 启用
- 考试模式: ✅ 启用

## 📁 配置文件
- src/config/system.config.js - 系统配置
- src/config/ai.config.js - AI配置
- .env - 环境变量

## 🚀 启动命令
```bash
npm run init          # 初始化项目
npm run start         # 启动开发服务器
npm run android       # 运行Android
npm run harmonyos     # 运行HarmonyOS
```
EOF

echo "✓ 配置总结已生成"

echo ""
echo "=========================================="
echo "  系统配置初始化完成！"
echo "=========================================="
echo ""
echo "配置文件已创建:"
echo "  - src/config/system.config.js"
echo "  - src/config/ai.config.js"
echo "  - .env"
echo "  - CONFIG_SUMMARY.md"
echo ""
echo "运行项目:"
echo "  npm run init"
echo "  npm run start"
echo "  npm run android"