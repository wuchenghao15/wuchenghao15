# MTSCOS AI Project - 项目启动指南

## 🚀 快速启动

### 方法一：使用主启动文件（推荐）

```bash
# 进入项目目录
cd /path/to/MTSCOS_AI_Project

# 运行主启动文件
./start.sh
```

### 方法二：使用纯净启动脚本

```bash
# 进入flask-app目录
cd flask-app

# 运行纯净启动脚本
python3 clean_start.py
```

### 方法三：使用系统初始化脚本

```bash
# 初始化并启动系统
python3 system_init.py
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

### flask-app/clean_start.py - 纯净启动脚本

- **位置**: flask-app目录
- **功能**: 创建纯净的Flask应用，跳过复杂初始化
- **特点**:
  - 启动速度快
  - 最小依赖
  - 适合开发和测试环境

### flask-app/system_init.py - 系统初始化脚本

- **位置**: flask-app目录
- **功能**: 完整的系统初始化和配置
- **特点**:
  - 自动环境检测
  - 依赖安装
  - 数据库初始化

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

### 纯净启动

```bash
cd flask-app
python3 clean_start.py
```

## 🌐 访问地址

- **主界面**: <http://localhost:8888>
- **登录页面**: <http://localhost:8888/auth/login>
- **注册页面**: <http://localhost:8888/auth/register>
- **API接口**: <http://localhost:8888/api>
- **API健康检查**: <http://localhost:8888/api/health>
- **API文档**: <http://localhost:8888/api/docs>

## 📁 项目结构

```
MTSCOS_AI_Project/
├── VERSION                      # 版本号文件
├── start.sh                     # 主启动文件 ⭐
├── ai_auto_generator.py         # AI自动生成器
├── ai_brain_management.py       # AI脑库管理系统
├── anti_brute_force_ai.py       # 数据撞库防御AI
├── expand_question_bank.py      # 题库扩充脚本
├── rule_expansion_ai.py         # 规则扩充AI
├── flask-app/                   # Flask应用目录
│   ├── app/                     # 应用核心代码
│   │   ├── ai/                  # AI模块
│   │   ├── api/                 # API路由
│   │   ├── models/              # 数据模型
│   │   ├── services/            # 服务层
│   │   ├── utils/               # 工具函数
│   │   ├── views/               # 视图层
│   │   └── __init__.py          # 应用初始化
│   ├── templates/               # 模板文件
│   ├── static/                  # 静态资源
│   ├── clean_start.py           # 纯净启动脚本
│   ├── system_init.py           # 系统初始化脚本
│   └── app.py                   # 主应用入口
├── frontend/                    # 前端文件
├── docs/                        # 文档目录
├── data/                        # 数据目录
├── assets/                      # 资源文件
└── logs/                        # 日志目录
```

## 🔧 系统要求

- **Python**: >= 3.9.0
- **Flask**: >= 3.0.0
- **操作系统**: macOS/Linux/Windows
- **浏览器**: Chrome/Firefox/Safari/Edge

## 📊 服务状态

当前服务状态：

- **状态**: ✅ 运行中
- **端口**: 8888
- **访问地址**: <http://localhost:8888>

## 📝 日志文件

- **启动日志**: `logs/startup.log`
- **服务日志**: `logs/service.log`
- **错误日志**: `logs/error.log`
- **API日志**: `logs/api.log`

## 🛠️ 故障排除

### 服务无法启动

1. 检查Python版本是否 >= 3.9.0
2. 检查端口8888是否被占用
3. 查看日志文件获取详细错误信息

### 端口被占用

```bash
# 查找占用端口的进程
lsof -i :8888

# 终止进程
kill -9 <PID>
```

### 依赖问题

```bash
# 安装依赖
pip3 install flask requests cryptography numpy

# 更新依赖
pip3 install --upgrade flask requests
```

### 数据库连接问题

```bash
# 检查数据库文件
ls -la flask-app/app.db

# 重新初始化数据库
python3 flask-app/init_database.py
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

### 5. AI智能系统

- AI自动生成器
- AI脑库管理
- AI自我学习
- AI规则管理

### 6. 考试系统

- 智能出题AI
- 阅卷AI
- 题库管理
- 试卷生成

## 📈 性能优化

- **启动时间**: < 5秒
- **内存占用**: < 200MB
- **CPU占用**: < 10%
- **响应时间**: < 100ms

## 🔒 安全说明

- 默认仅监听本地地址
- 支持HTTPS配置
- 内置安全中间件
- 数据撞库防御AI
- 定期安全更新

## 📞 技术支持

如遇问题，请：

1. 查看日志文件
2. 检查系统要求
3. 参考故障排除指南
4. 联系技术支持

---
**MTSCOS AI Project v4.5.5**  
*最后更新: 2026-04-28*

---

## 📋 API接口说明

### 健康检查

```bash
GET /api/health
```

返回系统健康状态。

### 系统状态

```bash
GET /api/status
```

返回系统各服务状态。

### API文档

```bash
GET /api/docs
```

返回完整的API文档。

### 规则管理

```bash
GET /api/rules
GET /api/rules/<rule_type>
```

获取系统规则。

### 考试系统

```bash
GET /api/exam/questions
POST /api/exam/generate
```

考试题目管理和试卷生成。

### AI脑库

```bash
GET /api/ai-brain/status
```

获取AI脑库状态。

## 🧠 AI功能说明

### AI自动生成器

自动生成不同类型的AI实例，支持批量生成和能力评估。

### AI脑库管理

管理AI知识存储，支持知识上传、查询和更新。

### 数据撞库防御AI

检测和防御批量登录尝试，保护系统安全。

### 规则扩充AI

根据AI建议自动扩充系统规则和策略。

### 题库扩充AI

自动生成和扩充考试题库，支持多种题型和难度级别。

---

## 🔄 系统维护

### 定期维护任务

1. **日志清理**: 定期清理旧日志文件
2. **数据库备份**: 定期备份数据库
3. **系统更新**: 定期更新系统版本
4. **安全检查**: 定期检查安全漏洞

### 维护命令

```bash
# 清理日志
./start.sh clean

# 备份数据库
./start.sh backup

# 更新系统
./start.sh update

# 安全检查
./start.sh security
```

---

**版权所有 © 2026 MTSCOS AI Project**