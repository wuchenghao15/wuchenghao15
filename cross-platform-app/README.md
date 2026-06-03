# MTSCOS AI Project - Cross-Platform Mobile App

一个高度适配 **HyperOS、Android 和 HarmonyOS** 的跨平台移动应用。

## 📱 功能特性

### 🚀 平台适配
- **HyperOS**: 深度适配小米HyperOS系统，享受流畅体验
- **HarmonyOS**: 完美适配鸿蒙系统，支持HarmonyOS特性
- **Android**: 原生Android优化，稳定可靠

### 🎨 界面设计
- 根据平台自动调整主题色彩
- 支持深色/浅色模式
- 流畅的动画效果

### 📱 核心功能
- 用户登录/注册
- 考试中心（支持多科目）
- 学习统计
- 个人中心
- 系统设置

## 🛠️ 技术栈

- React Native 0.74.3
- React 18.2.0
- React Navigation 6.x
- Axios
- AsyncStorage

## 📁 项目结构

```
cross-platform-app/
├── src/
│   ├── adapters/          # 平台适配器
│   │   └── PlatformAdapter.js
│   ├── context/           # React Context
│   │   ├── AuthContext.js
│   │   └── ThemeContext.js
│   ├── navigation/        # 导航配置
│   │   └── Navigation.js
│   └── screens/           # 屏幕组件
│       ├── LoginScreen.js
│       ├── RegisterScreen.js
│       ├── HomeScreen.js
│       ├── ExamScreen.js
│       ├── ProfileScreen.js
│       └── SettingsScreen.js
├── android/               # Android构建配置
├── harmonyos/             # HarmonyOS构建配置
├── scripts/               # 构建脚本
│   ├── build.sh           # 构建脚本
│   ├── package.sh         # 打包脚本
│   └── release.sh         # 完整发布脚本
├── App.js                 # 主应用入口
├── index.js              # React Native入口
├── app.json              # 应用配置
└── package.json          # 依赖配置
```

## 🚀 安装与运行

### 前置条件

- Node.js >= 18.0.0
- npm >= 9.0.0
- React Native CLI
- Android Studio (用于Android构建)
- DevEco Studio (用于HarmonyOS构建)
- JDK 11+

### 安装依赖

```bash
npm install
```

### 运行开发服务器

```bash
npm start
```

### 开发运行

```bash
# Android
npm run android

# HyperOS
npm run android -- --flavor hyperos

# HarmonyOS
npm run harmonyos
```

## 🔧 构建命令

### 基础构建

```bash
# 构建所有平台
npm run build:all

# 仅构建Android
npm run build:android

# 构建HyperOS版本
npm run build:hyperos

# 构建HarmonyOS
npm run build:harmonyos
```

### 打包命令

```bash
# 打包所有平台安装包
npm run package
```

### 完整发布流程

```bash
# 完整发布（环境检查 → 安装依赖 → 构建 → 打包 → 分发）
npm run release

# 仅检查环境
npm run release:env

# 仅安装依赖
npm run release:deps

# 仅构建
npm run release:build

# 仅打包
npm run release:package
```

## 📦 生成的安装包

运行发布脚本后，会在 `packages/` 目录生成以下文件：

| 文件 | 说明 |
|------|------|
| `MTSCOS_Android_v2.0.0.apk` | 通用Android版本 |
| `MTSCOS_HyperOS_v2.0.0.apk` | 小米HyperOS专用版 |
| `MTSCOS_HarmonyOS_Android_v2.0.0.apk` | HarmonyOS兼容版 |
| `MTSCOS_HarmonyOS_v2.0.0.hap` | HarmonyOS原生HAP包 |
| `checksums.md5` | MD5校验文件 |
| `checksums.sha256` | SHA256校验文件 |
| `RELEASE_NOTES.md` | 发布说明文档 |
| `MTSCOS_v2.0.0_all_platforms.zip` | 所有平台打包压缩包 |
| `MTSCOS_v2.0.0_all_platforms.tar.gz` | 所有平台打包压缩包 |

## 🔍 平台识别

应用启动时自动识别运行平台：

1. **HyperOS**: 通过检测品牌为Xiaomi且系统版本>=15识别
2. **HarmonyOS**: 通过检测系统名称包含"Harmony"识别
3. **Android**: 默认Android平台

## 🎨 主题适配

| 平台 | 主题 | 主色调 | 字体 |
|------|------|--------|------|
| HyperOS | 深色主题 | #6366f1 | MiSans |
| HarmonyOS | 跟随系统 | #007dff | HarmonyOS Sans SC |
| Android | 浅色主题 | #6200ee | Roboto |

## 📊 版本管理

```bash
# 升级版本
npm version major    # 主版本升级
npm version minor    # 次版本升级
npm version patch    # 补丁升级
```

## 🛡️ 安全

- 加密存储用户数据
- HTTPS通信加密
- Token安全管理
- APK签名验证

## 📝 许可证

MIT License

## 🤝 贡献

欢迎提交PR和Issue！

---

**MTSCOS AI Project** - 智能教育系统