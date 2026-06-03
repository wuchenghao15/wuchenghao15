# MTSCOS 测试与调试指南

## 📱 快速开始

### 前置条件

1. **Node.js 18.x 或更高版本**
   ```bash
   node -v
   ```

2. **Android Studio** (用于开发Android)
   - Android SDK
   - Android SDK Platform 34
   - Android SDK Build-Tools 34.0.0

3. **Java JDK 11 或更高版本**
   ```bash
   java -version
   ```

4. **可选：HarmonyOS DevEco Studio** (用于开发HarmonyOS)

---

## 🚀 首次启动

### 步骤 1: 初始化项目

```bash
# 进入项目目录
cd cross-platform-app

# 运行初始化脚本
npm run init
# 或者
bash scripts/init.sh
```

初始化脚本会：
- 检查Node.js版本
- 安装npm依赖
- 检查Android环境
- 创建必要目录
- 配置Android SDK

### 步骤 2: 启动Android模拟器

**方法一：通过Android Studio**
1. 打开Android Studio
2. 点击 AVD Manager
3. 创建虚拟设备（推荐：Pixel 6, API 33+）
4. 点击播放按钮启动模拟器

**方法二：通过命令行**
```bash
# 列出可用的模拟器
emulator -list-avds

# 启动模拟器
emulator -avd <你的模拟器名称>
```

### 步骤 3: 构建并运行应用

```bash
# 方法一：使用调试脚本
npm run android:debug
# 或
bash scripts/debug-android.sh

# 方法二：手动运行
npm start
# 在另一个终端
npm run android
```

---

## 🔧 调试技巧

### 1. 查看日志

```bash
# 只查看React Native日志
adb logcat -s ReactNativeJS:* ReactNative:*

# 查看所有错误
adb logcat *:E

# 查看完整日志
adb logcat
```

### 2. 开发者菜单

在模拟器中按以下键打开开发者菜单：
- **Android模拟器**: `Ctrl + M` (Windows) 或 `Cmd + M` (Mac)
- **真机**: 摇一摇手机

开发者菜单选项：
- Reload - 重新加载JS
- Debug - 打开调试器
- Show Inspector - 元素检查
- Show Performance Monitor - 性能监控

### 3. 使用Chrome调试

1. 在开发者菜单中选择 "Debug"
2. 在Chrome中打开 `http://localhost:8081/debugger-ui/`
3. 打开Chrome DevTools (F12)
4. 在Sources面板中调试代码

### 4. React DevTools

```bash
# 安装React DevTools
npm install -g react-devtools

# 启动DevTools
react-devtools
```

---

## 🎯 功能测试清单

### 基础功能

- [ ] 应用启动无崩溃
- [ ] 登录页面显示正常
- [ ] 注册页面显示正常
- [ ] 首页显示正常
- [ ] 底部导航栏工作正常

### 平台适配

- [ ] HyperOS深色主题正确应用
- [ ] HarmonyOS主题正确应用
- [ ] Android浅色主题正确应用
- [ ] 平台识别正确（显示"运行于XXX"）

### 核心功能

- [ ] 考试中心页面正常显示
- [ ] 个人中心页面正常显示
- [ ] 设置页面正常显示
- [ ] 离线考试页面正常显示
- [ ] 离线设置页面正常显示

### 离线功能

- [ ] 离线考试功能可用
- [ ] 本地存储正常工作
- [ ] 同步状态显示正确
- [ ] 网络状态检测正确

---

## 🛠️ 常见问题

### 问题1: Metro bundler 端口被占用

```bash
# 查找占用端口的进程
lsof -ti:8081

# 杀掉进程
kill -9 <pid>

# 或者
pkill -f 'react-native'
```

### 问题2: 构建失败

```bash
# 清理并重新构建
npm run clean
npm install
npm run android:debug
```

### 问题3: 找不到Android SDK

确保设置了 `ANDROID_HOME` 环境变量：
```bash
# macOS/Linux
export ANDROID_HOME=$HOME/Library/Android/sdk
export PATH=$PATH:$ANDROID_HOME/emulator
export PATH=$PATH:$ANDROID_HOME/tools
export PATH=$PATH:$ANDROID_HOME/tools/bin
export PATH=$PATH:$ANDROID_HOME/platform-tools

# Windows
set ANDROID_HOME=C:\Users\<用户名>\AppData\Local\Android\Sdk
```

### 问题4: Gradle同步失败

```bash
cd android
./gradlew clean
./gradlew build --stacktrace
```

---

## 📊 性能测试

### 使用性能监视器

1. 打开开发者菜单
2. 选择 "Show Performance Monitor"
3. 监控FPS、内存等指标

### 检查内存泄漏

```bash
# 使用Android Studio Profiler
# 或
adb shell dumpsys meminfo com.mtscos.app
```

---

## 🧪 自动化测试

### 基础测试

```bash
# 运行测试
npm test

# 监听模式
npm test -- --watch
```

### 端到端测试

（使用Detox或Appium，需要额外配置）

---

## 📦 构建发布版本

### Android

```bash
# 构建APK
npm run build:android

# 或使用完整构建脚本
npm run build:all
```

APK输出位置：
- `android/app/build/outputs/apk/android/release/app-android-release.apk`

### 签名配置

1. 生成密钥库（如果还没有）：
```bash
keytool -genkeypair -v -storetype PKCS12 -keystore mtscos-release-key.jks -keyalg RSA -keysize 2048 -validity 10000 -alias mtscos-key
```

2. 将密钥库放到 `android/keys/` 目录

3. 配置 `android/key.properties`（已创建）

---

## 🤝 提交前检查清单

- [ ] 代码通过 `npm run lint` 检查
- [ ] 所有测试通过 `npm test`
- [ ] 在模拟器上测试功能正常
- [ ] 在真机上测试功能正常
- [ ] 检查无内存泄漏
- [ ] 检查应用大小
- [ ] 更新CHANGELOG

---

## 📞 需要帮助？

- 查看 [React Native官方文档](https://reactnative.dev/)
- 查看项目 `README.md`
- 检查 `app.json` 配置
- 查看Android Studio的Logcat日志

---

**祝测试顺利！** 🎉
