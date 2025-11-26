# HardwareKey Native API Integration

## 概述

本项目已成功集成基于官方HardwareKey库的Node.js原生扩展模块，提供真正的HardwareKey USB加密狗操作功能。

## 文件结构

```
JavaScript/
├── hardwareKey-native/                 # HardwareKey原生模块
│   ├── binding.gyp              # 构建配置文件
│   ├── package.json             # Node.js包配置
│   ├── index.js                 # JavaScript接口封装
│   ├── src/
│   │   └── hardwareKey_native.cpp     # C++原生实现
│   ├── test.js                  # 测试脚本
│   └── README.md                # 模块文档
├── hardwareKey-websocket-server.js    # 更新的WebSocket服务器
├── install-hardwareKey-native.sh      # Linux/macOS安装脚本
└── install-hardwareKey-native.bat     # Windows安装脚本
```

## 主要特性

### 1. 基于官方库的完整实现

- 使用官方 `hardwareKey.h`、`hardwareKey.lib` 和 `hardwareKey.dll`
- 支持所有官方API功能
- 完整的错误码支持

### 2. Node.js原生扩展

- 使用 `node-addon-api` 构建
- 高性能的C++实现
- 异步/同步API支持

### 3. 智能回退机制

- 自动检测原生模块可用性
- 不可用时回退到模拟模式
- 无缝切换，不影响前端使用

## API功能

### 基础设备操作

- `find()` / `findEx()` - 查找HardwareKey设备
- `getHID(index)` - 获取设备硬件ID
- `getType(index)` - 获取设备类型
- `getLevel(index)` - 获取权限级别
- `getSoftIDString(index)` - 获取软件ID

### 认证功能

- `userLogin(index, password)` - 用户登录
- `adminLogin(index, password)` - 管理员登录
- `logoff(index)` - 登出

### 数据操作

- `readData(index, address, length)` - 读取数据
- `writeData(index, address, data)` - 写入数据

### 设备控制

- `setLED(index, state)` - LED控制
- `random(index, length)` - 生成随机数

### 加密功能

- `encrypt3DES(index, data, key)` - 3DES加密
- `decrypt3DES(index, data, key)` - 3DES解密
- `encryptDES(index, data, key)` - DES加密
- `decryptDES(index, data, key)` - DES解密

## 安装步骤

### Windows环境（推荐）

1. **准备环境**

   ```cmd
   # 确保已安装：
   # - Node.js (v14+)
   # - Visual Studio Build Tools
   # - Python (2.7或3.x)
   ```

2. **放置官方库文件**

   ```
   将以下文件放置到项目根目录/HardwareKey/文件夹中：
   - hardwareKey.h
   - hardwareKey.lib  
   - hardwareKey.dll
   ```

3. **运行安装脚本**

   ```cmd
   cd JavaScript
   install-hardwareKey-native.bat
   ```

### Linux/macOS环境

1. **准备环境**

   ```bash
   # 确保已安装：
   # - Node.js (v14+)
   # - node-gyp
   # - 构建工具
   ```

2. **运行安装脚本**

   ```bash
   cd JavaScript
   ./install-hardwareKey-native.sh
   ```

   注意：HardwareKey库主要支持Windows，非Windows环境下可能无法完全工作。

## 使用方法

### 1. 直接使用原生模块

```javascript
const HardwareKeyAPI = require('./hardwareKey-native');

const hardwareKey = new HardwareKeyAPI();

// 查找设备
const result = await hardwareKey.findEx();
if (result.success) {
    console.log(`找到 ${result.count} 个设备`);
    
    // 获取第一个设备的HID
    const hidResult = await hardwareKey.getHID(0);
    if (hidResult.success) {
        console.log(`设备HID: ${hidResult.hid}`);
    }
}
```

### 2. 通过WebSocket服务器

WebSocket服务器会自动使用原生模块（如果可用）：

```javascript
// 连接到WebSocket服务器
const ws = new WebSocket('ws://localhost:8084');

// 查找设备
ws.send(JSON.stringify({
    type: 'HardwareKeyFind'
}));

// 处理响应
ws.onmessage = (event) => {
    const response = JSON.parse(event.data);
    if (response.type === 'HardwareKeyFind') {
        console.log('设备查找结果:', response.data);
    }
};
```

## WebSocket消息格式

### 请求格式

```json
{
    "type": "HardwareKeyFind",
    "index": 0,
    "password": "123456"
}
```

### 响应格式

```json
{
    "type": "HardwareKeyFind",
    "success": true,
    "data": {
        "count": 1,
        "devices": [{
            "index": 0,
            "hid": "VID_096E&PID_0801",
            "type": 1,
            "level": 0,
            "softId": "MTSCOS",
            "status": "connected"
        }]
    },
    "timestamp": 1703123456789
}
```

## 支持的消息类型

| 消息类型 | 描述 | 参数 |
|---------|------|------|
| `GetVersion` | 获取版本信息 | - |
| `CheckInstall` | 检查安装状态 | - |
| `HardwareKeyFind` | 查找设备 | - |
| `HardwareKeyGetHID` | 获取设备HID | `index` |
| `HardwareKeyGetType` | 获取设备类型 | `index` |
| `HardwareKeyGetLevel` | 获取权限级别 | `index` |
| `HardwareKeyGetPtroductName` | 获取产品名称 | `index` |
| `HardwareKeyUserLogin` | 用户登录 | `index`, `password` |
| `HardwareKeyAdminLogin` | 管理员登录 | `index`, `password` |

## 错误处理

### 错误码

所有HardwareKey API调用都会返回标准错误码：

- `0x00000000` - 成功
- `0x80000001` - 未找到HardwareKey设备
- `0x80000002` - 设备权限不足
- `0x80000003` - 密码错误
- 其他错误码请参考官方文档

### 错误响应格式

```json
{
    "type": "HardwareKeyUserLogin",
    "success": false,
    "error": "用户登录失败: 错误码 21474836487",
    "errorCode": 21474836487,
    "timestamp": 1703123456789
}
```

## 调试和故障排除

### 1. 检查原生模块状态

```javascript
// 在WebSocket服务器日志中查看
// ✓ HardwareKey Native API loaded successfully
// 或
// ✗ HardwareKey Native API not available, using simulation mode
```

### 2. 运行测试脚本

```bash
cd JavaScript/hardwareKey-native
node test.js
```

### 3. 检查构建日志

```bash
# 重新构建并显示详细日志
npx node-gyp rebuild --verbose
```

### 4. 常见问题

**问题**: 原生模块加载失败
**解决**:

- 确保在Windows环境下构建
- 检查Visual Studio Build Tools是否安装
- 验证HardwareKey库文件是否正确放置

**问题**: 设备查找失败
**解决**:

- 确保HardwareKey设备已连接
- 检查USB驱动是否正确安装
- 验证设备权限

**问题**: 登录失败
**解决**:

- 检查密码是否正确
- 确认设备索引是否有效
- 验证权限级别

## 性能优化

### 1. 异步操作

所有API都支持异步操作，避免阻塞主线程：

```javascript
// 好的做法
const result = await hardwareKey.findEx();

// 避免同步调用
const result = hardwareKey.findExSync(); // 不推荐
```

### 2. 批量操作

使用 `Promise.all` 进行并行操作：

```javascript
const [hidResult, typeResult, levelResult] = await Promise.all([
    hardwareKey.getHID(0),
    hardwareKey.getType(0),
    hardwareKey.getLevel(0)
]);
```

### 3. 连接复用

WebSocket服务器会维护HardwareKey实例，避免重复初始化。

## 安全注意事项

1. **密码保护**: 不要在代码中硬编码密码
2. **权限控制**: 使用最小权限原则
3. **数据加密**: 敏感数据使用加密功能
4. **日志安全**: 避免在日志中记录敏感信息

## 版本信息

- **当前版本**: v2.0.0
- **原生API版本**: 基于官方HardwareKey库
- **Node.js要求**: v14.0.0+
- **平台支持**: Windows (主要), Linux/macOS (部分)

## 更新日志

### v2.0.0 (2025-11-20)

- ✅ 集成官方HardwareKey库
- ✅ 实现Node.js原生扩展
- ✅ 添加智能回退机制
- ✅ 更新WebSocket服务器
- ✅ 完善错误处理
- ✅ 添加安装脚本

### v1.0.0 (之前版本)

- ✅ 基础WebSocket服务器
- ✅ 模拟HardwareKey功能
- ✅ 基础消息处理

## 技术支持

如遇到问题，请检查：

1. [官方HardwareKey文档](./HardwareKey/)
2. [Node.js原生扩展文档](https://nodejs.org/api/addons.html)
3. [node-addon-api文档](https://github.com/nodejs/node-addon-api)

---

**注意**: 本实现完全基于官方提供的 `hardwareKey.h`、`hardwareKey.lib` 和 `hardwareKey.dll` 文件，确保与官方标准的完全兼容性。
