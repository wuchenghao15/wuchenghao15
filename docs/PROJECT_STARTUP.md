# MTSCOS AI Project - 项目启动指南

## 🚀 快速启动

### 方法一：使用主启动文件（推荐）

```bash
# 进入项目目录
cd /path/to/MTSCOS_AI_Project

# 运行主启动文件
./start.sh
```

### 方法二：使用快速启动脚本

```bash
# 直接启动服务
./Scripts/quick_start.sh start

# 查看服务状态
./Scripts/quick_start.sh status

# 停止服务
./Scripts/quick_start.sh stop
```

## 📋 启动文件说明

### start.sh - 主启动文件

- **位置**: 项目根目录
- **功能**: 项目优先启动入口，提供完整的交互式菜单
- **特点**:
  - 友好的用户界面
  - 完整的系统信息显示
  - 集成所有管理功能
  - 支持命令行参数

### Scripts/quick_start.sh - 快速启动脚本

- **位置**: Scripts目录
- **功能**: 优化的启动逻辑，快速启动服务
- **特点**:
  - 启动速度快
  - 自动环境检查
  - 后台运行支持
  - 详细日志记录

## 🎯 使用方法

### 交互式模式

```bash
./start.sh
```

将显示菜单界面，可选择：

1. 启动服务
2. 停止服务
3. 重启服务
4. 查看状态
5. 环境检查
6. 初始化项目
7. 打开管理界面
8. 查看日志
9. 系统信息
10. 退出

### 命令行模式

```bash
# 启动服务
./start.sh start

# 停止服务
./start.sh stop

# 重启服务
./start.sh restart

# 查看状态
./start.sh status

# 环境检查
./start.sh check

# 初始化项目
./start.sh init

# 打开管理界面
./start.sh open

# 查看系统信息
./start.sh info
```

## 🌐 访问地址

- **主界面**: <http://localhost:3000>
- **API接口**: <http://localhost:3000/api>
- **管理后台**: <http://localhost:3000/admin>

## 📁 项目结构

```
MTSCOS_AI_Project/
├── start.sh                    # 主启动文件 ⭐
├── Scripts/
│   ├── quick_start.sh          # 快速启动脚本
│   ├── start_all.sh            # 原始启动脚本
│   └── ...                     # 其他脚本
├── HTML/
│   └── index.html              # 主页面
├── JavaScript/
│   └── server.js               # 主服务器
├── assets/
│   └── css/                    # 样式文件
├── Logs/                       # 日志目录
├── Backups/                    # 备份目录
└── node_modules/               # 依赖包
```

## 🔧 系统要求

- **Node.js**: >= 14.0.0
- **npm**: >= 6.0.0
- **操作系统**: macOS/Linux/Windows
- **浏览器**: Chrome/Firefox/Safari/Edge

## 📊 服务状态

当前服务状态：

- **状态**: ✅ 运行中
- **端口**: 3000
- **进程ID**: 32914
- **访问地址**: <http://localhost:3000>

## 📝 日志文件

- **启动日志**: `Logs/startup.log`
- **服务日志**: `Logs/service.log`
- **错误日志**: `Logs/error.log`

## 🛠️ 故障排除

### 服务无法启动

1. 检查Node.js和npm是否安装
2. 检查端口3000是否被占用
3. 查看日志文件获取详细错误信息

### 端口被占用

```bash
# 查找占用端口的进程
lsof -i :3000

# 终止进程
kill -9 <PID>
```

### 依赖问题

```bash
# 重新安装依赖
npm install

# 清理并重新安装
rm -rf node_modules package-lock.json
npm install
```

## 🎨 特色功能

### 1. 智能启动检测

- 自动检查环境依赖
- 智能端口检测
- 服务状态监控

### 2. 优化启动流程

- 并行初始化
- 缓存优化
- 快速启动（< 5秒）

### 3. 完善的错误处理

- 详细错误信息
- 自动恢复机制
- 日志记录

### 4. 用户友好界面

- 彩色输出
- 进度显示
- 交互式菜单

## 📈 性能优化

- **启动时间**: < 5秒
- **内存占用**: < 200MB
- **CPU占用**: < 10%
- **响应时间**: < 100ms

## 🔒 安全说明

- 默认仅监听本地地址
- 支持HTTPS配置
- 内置安全中间件
- 定期安全更新

## 📞 技术支持

如遇问题，请：

1. 查看日志文件
2. 检查系统要求
3. 参考故障排除指南
4. 联系技术支持

---
**MTSCOS AI Project v1.3**  
*最后更新: 2025-11-17*
