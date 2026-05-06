# iOS APP构建与安装指南

## 问题分析

当前生成的 `app-release.ipa` 是一个模拟文件，无法安装到iPhone上。要构建可安装的IPA文件，需要使用 Expo Application Services (EAS) Build 进行真实构建，并且需要Apple开发者账号。

## iOS构建环境准备

### 1. 必要条件

- **Apple开发者账号**：需要付费的Apple Developer Program账号
- **Mac电脑**：iOS构建必须在Mac上进行
- **Xcode**：安装最新版本的Xcode
- **EAS CLI**：Expo的构建工具

### 2. 安装必要工具

```bash
# 安装Expo CLI
npm install -g expo-cli

# 安装EAS CLI
npm install -g eas-cli
```

### 3. 配置EAS

```bash
# 登录EAS账号
eas login

# 初始化EAS配置
eas init
```

### 4. 配置app.json

确保 `app.json` 文件包含正确的iOS配置：

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
      "bundleIdentifier": "com.mtscos.examsystem",
      "buildNumber": "1"
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

### 5. 配置eas.json

创建或更新 `eas.json` 文件：

```json
{
  "cli": {
    "version": ">= 7.8.1"
  },
  "build": {
    "preview": {
      "ios": {
        "simulator": false
      }
    },
    "production": {
      "ios": {
        "simulator": false
      }
    }
  },
  "submit": {
    "production": {}
  }
}
```

## iOS构建步骤

### 1. 构建IPA文件

```bash
# 构建预览版本（适合测试）
eas build -p ios --profile preview

# 构建生产版本（适合发布）
eas build -p ios --profile production
```

### 2. 构建过程

1. EAS会提示你选择构建类型（模拟器或真机）
2. 选择"真机"构建
3. EAS会自动处理证书和配置文件
4. 构建过程可能需要15-30分钟
5. 构建完成后，会提供下载链接

## 安装IPA到iPhone

### 方法1：使用TestFlight（推荐）

1. **上传到TestFlight**：
   ```bash
   eas submit -p ios --profile preview
   ```

2. **在iPhone上安装TestFlight应用**
3. **接收TestFlight邀请**：通过邮件或链接
4. **在TestFlight中安装APP**

### 方法2：使用Xcode安装

1. **下载IPA文件**：从EAS构建页面下载
2. **打开Xcode**：启动Xcode
3. **连接iPhone**：使用USB cable连接iPhone
4. **打开Devices and Simulators**：
   - 菜单：Window → Devices and Simulators
   - 或使用快捷键：⇧⌘2
5. **选择你的iPhone**：在左侧设备列表中
6. **安装APP**：
   - 点击"+"按钮
   - 选择下载的IPA文件
   - 等待安装完成

### 方法3：使用第三方工具

1. **Cydia Impactor**：
   - 下载并打开Cydia Impactor
   - 连接iPhone
   - 拖放IPA文件到Cydia Impactor
   - 输入Apple ID和密码
   - 等待安装完成

2. **AltStore**：
   - 在iPhone上安装AltStore
   - 通过AltStore安装IPA文件

## 证书和配置文件

### 自动证书管理

EAS Build可以自动管理证书：

```bash
# 配置自动证书管理
eas credentials
```

选择"Let EAS handle the process"选项，EAS会自动创建和管理证书。

### 手动证书管理

如果需要手动管理证书：

1. **创建证书**：在Apple Developer Portal中创建
2. **创建配置文件**：为你的APP创建配置文件
3. **上传证书**：
   ```bash
   eas credentials
   ```

## 故障排除

### 常见构建问题

1. **证书错误**
   - 解决方法：使用EAS自动证书管理或确保证书有效

2. **构建失败**
   - 解决方法：检查EAS控制台的构建日志，根据错误信息进行修复

3. **依赖冲突**
   - 解决方法：运行 `npx expo install --fix -- --legacy-peer-deps`

### 常见安装问题

1. **未受信任的开发者**
   - 解决方法：在设置 → 通用 → VPN与设备管理中信任开发者

2. **安装失败**
   - 解决方法：检查是否已安装旧版本，需要先卸载旧版本

3. **证书过期**
   - 解决方法：更新证书或重新构建APP

## 测试建议

1. **在多个设备上测试**：确保APP在不同型号的iPhone上都能正常运行
2. **测试各种网络条件**：在WiFi和移动数据下都进行测试
3. **测试核心功能**：登录、考试、数据库同步等核心功能
4. **性能测试**：检查APP的启动速度和响应速度

## 紧急解决方案

如果需要立即测试APP，可以使用Expo Go应用：

```bash
# 启动Expo开发服务器
npx expo start

# 使用Expo Go应用扫描二维码进行测试
```

这种方法不需要构建IPA，可以直接在iPhone上测试APP功能。

## 注意事项

- **Apple开发者账号**：必须有付费的Apple Developer Program账号
- **Mac电脑**：iOS构建必须在Mac上进行
- **证书有效期**：确保证书在有效期内
- **设备UDID**：如果使用开发证书，需要将测试设备的UDID添加到开发者账号
- **构建时间**：首次构建可能需要较长时间（15-30分钟）
- **TestFlight审核**：上传到TestFlight可能需要Apple审核（约1-2天）

## 真实构建流程

1. 确保所有依赖都已正确安装
2. 运行 `npx expo install --fix` 修复依赖
3. 执行 `eas build -p ios --profile preview` 构建IPA
4. 下载生成的IPA文件或通过TestFlight安装
5. 在iPhone上进行测试
6. 如有问题，根据错误信息进行修复后重新构建
