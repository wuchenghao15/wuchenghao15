# MTSCOS AI修复引擎

## 项目概述

MTSCOS AI修复引擎是一个基于AI的代码修复工具，能够自动检测和修复JavaScript代码中的各种问题，包括语法错误、逻辑错误、安全漏洞等。

## 核心功能

### 1. 代码问题检测

- 支持多种代码问题检测（语法错误、安全漏洞、性能问题等）
- 可扩展的检测器架构，支持自定义检测器

### 2. AI驱动修复

- 基于DeepSeek AI模型进行智能代码修复
- 支持本地模型和云端模型切换
- 修复结果可验证和回滚

### 3. 批量修复

- 支持单个文件修复
- 支持目录级批量修复
- 支持指定文件类型过滤

### 4. 配置管理

- 灵活的配置系统
- 支持环境变量替换
- 可扩展的配置项

## 快速开始

### 安装依赖

```bash
# 安装项目依赖
npm install
```

### 基本使用

```javascript
const RepairEngine = require('./repair-engine');

// 创建修复引擎配置
const config = {
    deepseek: {
        apiKey: 'your-api-key',
        model: 'deepseek-coder',
        temperature: 0.3
    }
};

// 初始化修复引擎
const repairEngine = new RepairEngine(config);
await repairEngine.initialize();

// 修复单个文件
const fileResult = await repairEngine.repairFile('path/to/file.js');
console.log('文件修复结果:', fileResult);

// 修复目录
const dirResult = await repairEngine.repairDirectory('path/to/directory', ['.js']);
console.log('目录修复结果:', dirResult);
```

## API参考

### RepairEngine 类

#### 构造函数

```javascript
new RepairEngine(config)
```

**参数：**

- `config` (Object): 修复引擎配置对象
  - `deepseek` (Object): DeepSeek AI配置
    - `apiKey` (String): API密钥
    - `model` (String): 模型名称
    - `temperature` (Number): 生成温度
  - `cache` (Object): 缓存配置
    - `enabled` (Boolean): 是否启用缓存
    - `maxSize` (Number): 缓存最大大小
    - `ttl` (Number): 缓存过期时间
  - `logger` (Object): 日志配置
    - `level` (String): 日志级别

#### 方法

##### initialize()

```javascript
await repairEngine.initialize()
```

初始化修复引擎，加载AI模型和组件。

**返回值：**

- `Object`: 初始化结果
  - `success` (Boolean): 是否成功
  - `error` (String): 错误信息（如果失败）
  - `errorType` (String): 错误类型（如果失败）

##### repairFile(filePath, issues)

```javascript
await repairEngine.repairFile(filePath, issues)
```

修复单个JavaScript文件。

**参数：**

- `filePath` (String): 文件路径
- `issues` (Array): 已知问题列表（可选，默认自动检测）

**返回值：**

- `Object`: 修复结果
  - `success` (Boolean): 是否成功
  - `issues` (Array): 检测到的问题
  - `fixedIssues` (Array): 已修复的问题
  - `fixedContent` (String): 修复后的代码内容

##### repairDirectory(directoryPath, fileExtensions)

```javascript
await repairEngine.repairDirectory(directoryPath, fileExtensions)
```

批量修复目录中的JavaScript文件。

**参数：**

- `directoryPath` (String): 目录路径
- `fileExtensions` (Array): 文件扩展名过滤（默认：['.js']）

**返回值：**

- `Object`: 修复结果
  - `success` (Boolean): 是否成功
  - `results` (Array): 每个文件的修复结果
  - `totalFiles` (Number): 处理的文件总数
  - `successfulRepairs` (Number): 成功修复的文件数

##### getStatus()

```javascript
repairEngine.getStatus()
```

获取修复引擎的当前状态。

**返回值：**

- `Object`: 引擎状态
  - `initialized` (Boolean): 是否已初始化
  - `models` (Object): AI模型状态
  - `detectors` (Array): 已加载的检测器
  - `strategies` (Array): 已加载的修复策略

## 配置示例

```javascript
const config = {
    deepseek: {
        apiKey: 'sk-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx',
        baseUrl: 'https://api.deepseek.com',
        model: 'deepseek-coder',
        maxTokens: 1024,
        temperature: 0.3,
        timeout: 30000
    },
    cache: {
        enabled: true,
        maxSize: 100,
        ttl: 3600000
    },
    logger: {
        level: 'info',
        format: 'json'
    }
};
```

## 测试

运行测试脚本：

```bash
node test-repair-engine.js
```

## 注意事项

1. 确保提供有效的DeepSeek API密钥
2. 首次使用时会初始化模型，可能需要一些时间
3. 修复结果建议进行人工验证
4. 支持Node.js v14.0.0及以上版本
