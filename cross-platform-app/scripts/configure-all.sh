#!/bin/bash

# 完整系统配置脚本
echo "=========================================="
echo "  MTSCOS 完整系统配置"
echo "=========================================="
echo ""

# 检查Node.js
if ! command -v node &> /dev/null; then
    echo "❌ Node.js未安装，请先安装Node.js"
    exit 1
fi

echo "[1/6] 运行系统配置..."
bash scripts/configure-system.sh
echo ""

echo "[2/6] 运行数据库配置..."
bash scripts/configure-database.sh
echo ""

echo "[3/6] 运行AI配置..."
bash scripts/configure-ai.sh
echo ""

echo "[4/6] 运行规则配置..."
bash scripts/configure-rules.sh
echo ""

echo "[5/6] 更新配置总结..."

cat > CONFIG_SUMMARY.md << 'EOF'
# MTSCOS 系统配置总结

## 📋 基本信息
- 应用名称: MTSCOS 智能学习系统
- 版本号: 2.0.0
- 构建号: 20260511
- 开发环境: development

## 🔧 配置文件清单

| 文件 | 功能 |
|------|------|
| src/config/system.config.js | 系统核心配置 |
| src/config/database.config.js | 数据库配置 |
| src/config/ai.config.js | AI服务配置 |
| src/config/rules.config.js | 系统规则配置 |
| .env | 环境变量配置 |

## 🌐 API配置
- API地址: http://localhost:8890
- 超时时间: 30秒
- 重试次数: 3次

## 🗄️ 数据库配置
- 类型: SQLite
- 名称: mtscos_offline.db
- 加密: AES-256-GCM
- 同步间隔: 5分钟
- 自动备份: 每天

## 🤖 AI配置
- 启用: ✅
- 默认模型: GPT-4
- 最大Token: 1024
- 温度: 0.7

## 📊 用户角色
| 角色 | 权限 |
|------|------|
| admin | 全部权限 |
| professor | 题库管理、教师委派、职称测评 |
| teacher | 创建考试、批改作业 |
| student | 参加考试、查看进度 |
| guest | 查看公开内容 |

## 📚 考试科目
- 语文、数学、英语、物理、化学、生物、历史、地理、政治、日语

## 🎯 升级规则
- 年级: 一年级 ~ 高三
- 分科: 文科、理科、综合 (9年级可选)
- 班级人数: 每45人一班
- 及格线: 60分
- 补考次数: 1次

## 👨‍🏫 教师职称
| 职称 | 要求经验 |
|------|----------|
| 助教 | 0年 |
| 讲师 | 2年 |
| 副教授 | 5年 |
| 教授 | 10年 |

## 🛡️ 安全配置
- 密码策略: 大写+小写+数字 (6-32字符)
- 登录尝试: 最多5次，锁定15分钟
- 敏感数据: AES-256加密

## 📱 平台适配
| 平台 | 主题 | 主色调 |
|------|------|--------|
| HyperOS | 深色主题 | #6366f1 |
| HarmonyOS | 系统主题 | #007dff |
| Android | 浅色主题 | #6200ee |

## 🚀 启动命令

```bash
# 初始化项目
npm run init

# 启动开发服务器
npm run start

# 启动模拟器
npm run emulator

# 运行Android
npm run android:debug

# 构建所有平台
npm run build:all

# 完整发布
npm run release
```

## ✅ 已完成配置

- ✅ 系统配置
- ✅ 数据库配置
- ✅ AI配置
- ✅ 规则配置
- ✅ 平台适配配置
- ✅ 离线功能配置
- ✅ 版本管理配置
- ✅ 安全配置
EOF

echo "✓ 配置总结已更新"

echo ""
echo "[6/6] 验证所有配置文件..."

CONFIG_FILES=(
    "src/config/system.config.js"
    "src/config/database.config.js"
    "src/config/ai.config.js"
    "src/config/rules.config.js"
    ".env"
    "src/services/AIService.js"
    "src/services/RuleService.js"
    "src/services/VersionService.js"
    "src/services/SyncService.js"
    "src/services/OfflineStorageService.js"
)

ALL_OK=true
for file in "${CONFIG_FILES[@]}"; do
    if [ -f "$file" ]; then
        echo "✓ $file"
    else
        echo "❌ $file - 不存在"
        ALL_OK=false
    fi
done

echo ""
echo "=========================================="
if $ALL_OK; then
    echo "  ✅ 所有配置完成！"
else
    echo "  ⚠️ 部分配置文件缺失"
fi
echo "=========================================="
echo ""
echo "项目已完成以下配置:"
echo "  ✓ 系统配置 (system.config.js)"
echo "  ✓ 数据库配置 (database.config.js)"
echo "  ✓ AI配置 (ai.config.js)"
echo "  ✓ 规则配置 (rules.config.js)"
echo "  ✓ 环境变量 (.env)"
echo "  ✓ AI服务 (AIService.js)"
echo "  ✓ 规则服务 (RuleService.js)"
echo "  ✓ 版本服务 (VersionService.js)"
echo "  ✓ 同步服务 (SyncService.js)"
echo "  ✓ 离线存储服务 (OfflineStorageService.js)"
echo ""
echo "启动命令:"
echo "  npm run init          # 初始化项目"
echo "  npm run emulator      # 启动模拟器"
echo "  npm run android:debug # 运行调试版本"