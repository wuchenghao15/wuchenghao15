# APP构建指南

## 问题分析

当前生成的 `app-release.apk` 是一个模拟文件，无法安装到手机上。要构建可安装的APK文件，需要使用 Expo Application Services (EAS) Build 进行真实构建。

## 构建环境准备

### 1. 安装必要工具

```bash
# 安装Expo CLI
npm install -g expo-cli

# 安装EAS CLI
npm install -g eas-cli
```

### 2. 配置EAS

```bash
# 登录EAS账号
eas login

# 初始化EAS配置
eas init
```

### 3. 配置app.json

确保 `app.json` 文件包含正确的配置：

```json
{
  "expo": {
    "name": "考试系统APP",
    "slug": "exam-system-app",
    "version": "1.0.0",
    "orientation": "portrait",
    "icon": "./assets/icon.png",
    "userInterfaceStyle": "light",
    "splash": {
      "image": "./assets/splash.png",
      "resizeMode": "contain",
      "backgroundColor": "#ffffff"
    },
    "assetBundlePatterns": [
      "**/*"
    ],
    "ios": {
      "supportsTablet": true,
      "bundleIdentifier": "com.mtscos.examsystem"
    },
    "android": {
      "adaptiveIcon": {
        "foregroundImage": "./assets/adaptive-icon.png",
        "backgroundColor": "#ffffff"
      },
      "package": "com.mtscos.examsystem"
    },
    "web": {
      "favicon": "./assets/favicon.png"
    },
    "extra": {
      "eas": {
        "projectId": "你的项目ID"
      }
    }
  }
}
```

## 构建步骤

### 构建安卓APK

```bash
# 构建预览版本（适合测试）
eas build -p android --profile preview

# 构建生产版本（适合发布）
eas build -p android --profile production
```

### 构建iOS IPA

```bash
# 构建预览版本
eas build -p ios --profile preview

# 构建生产版本
eas build -p ios --profile production
```

## 构建配置文件

创建 `eas.json` 文件来配置构建选项：

```json
{
  "cli": {
    "version": ">= 7.8.1"
  },
  "build": {
    "preview": {
      "android": {
        "buildType": "apk"
      }
    },
    "production": {
      "android": {
        "buildType": "app-bundle"
      }
    }
  },
  "submit": {
    "production": {}
  }
}
```

## 安装APK到手机

### 方法1：使用EAS Build下载链接

1. 构建完成后，EAS会提供一个下载链接
2. 在手机浏览器中打开该链接
3. 点击下载APK文件
4. 打开下载的APK文件进行安装

### 方法2：使用ADB安装

```bash
# 确保手机已连接并启用USB调试
adb devices

# 安装APK
adb install path/to/app-release.apk
```

### 方法3：使用文件传输

1. 将APK文件复制到手机存储
2. 在手机上使用文件管理器找到APK文件
3. 点击APK文件进行安装

## 故障排除

### 常见安装问题

1. **安装被阻止**
   - 解决方法：在手机设置中允许安装来自"未知来源"的应用

2. **解析包错误**
   - 解决方法：重新下载APK文件，确保文件完整

3. **应用未安装**
   - 解决方法：检查是否已安装旧版本，需要先卸载旧版本

4. **权限问题**
   - 解决方法：在安装过程中授予必要的权限

### 构建问题

1. **依赖冲突**
   - 解决方法：运行 `npx expo install --fix -- --legacy-peer-deps`

2. **构建失败**
   - 解决方法：检查EAS控制台的构建日志，根据错误信息进行修复

3. **资源缺失**
   - 解决方法：确保所有资源文件（图标、启动图等）都存在

## 测试建议

1. **在多个设备上测试**：确保APP在不同型号的手机上都能正常运行
2. **测试各种网络条件**：在WiFi和移动数据下都进行测试
3. **测试核心功能**：登录、考试、数据库同步等核心功能
4. **性能测试**：检查APP的启动速度和响应速度

## 真实构建流程

1. 确保所有依赖都已正确安装
2. 运行 `npx expo install --fix` 修复依赖
3. 执行 `eas build -p android --profile preview` 构建APK
4. 下载生成的APK文件
5. 安装到手机并进行测试
6. 如有问题，根据错误信息进行修复后重新构建

## 注意事项

- 构建过程需要网络连接
- 首次构建可能需要较长时间（15-30分钟）
- 确保 `app.json` 中的包名和版本号正确
- 测试版本可以使用预览构建，发布版本需要使用生产构建

## 紧急解决方案

如果需要立即测试APP，可以使用Expo Go应用：

```bash
# 启动Expo开发服务器
npx expo start

# 使用Expo Go应用扫描二维码进行测试
```

这种方法不需要构建APK，可以直接在手机上测试APP功能。
