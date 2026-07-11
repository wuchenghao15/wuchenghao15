# 🎬 MTSCOS AI 系统功能演示指南 | Demo Guide

## 📸 功能演示GIF制作说明

本目录用于存放系统功能演示的GIF图片和录制说明。

---

## 🎯 核心功能演示清单

### 1. 🔐 用户登录流程 | Login Flow

**演示内容**:
1. 打开浏览器访问 http://localhost:8888
2. 输入用户名和密码
3. 系统验证并跳转对应角色页面

**录制命令** (使用ffmpeg):
```bash
ffmpeg -f avfoundation -framerate 30 -i "0" -t 10 -vf "scale=1280:720" login_demo.mp4
```

### 2. 📊 超级管理员仪表盘 | Super Admin Dashboard

**演示内容**:
1. 使用 hardware_admin 账号登录
2. 自动跳转到 /super_admin_dashboard
3. 展示9大功能区域
4. 点击各个管理入口

**关键页面**:
- 系统监控台
- 用户管理
- 考试系统后台
- 学习系统后台

### 3. 🤖 AI员工批量修复 | AI Employee Batch Fix

**演示内容**:
1. 调用 `/api/ai/batch_fix` API
2. AI员工自动检测问题
3. 查看修复报告 `/api/ai/fix_report`

**API调用示例**:
```bash
# 调用批量修复
curl -X POST http://localhost:8888/api/ai/batch_fix \
  -H "Content-Type: application/json" \
  -d '{"fix_types":["template","route"]}'

# 查看修复报告
curl http://localhost:8888/api/ai/fix_report
```

### 4. 🛠️ Git管理AI员工 | Git Manager AI

**演示内容**:
1. 查看Git状态
2. 自动提交更改
3. 推送到远程仓库
4. 创建备份分支

**API调用示例**:
```bash
# 查看Git状态
curl http://localhost:8888/api/git/status

# 同步备份
curl -X POST http://localhost:8888/api/git/sync

# 查看操作历史
curl http://localhost:8888/api/git/history
```

### 5. 🔧 异常页面展示 | Error Pages

**演示内容**:
1. 访问不存在的页面 → 404页面
2. 未登录访问受保护页面 → 401页面
3. 无权限访问 → 403页面
4. 服务器错误 → 500页面

**测试命令**:
```bash
# 测试404
curl http://localhost:8888/nonexistent_page

# 测试401
curl http://localhost:8888/exam_system

# 测试403 (需要非admin角色)
```

---

## 🎥 GIF录制工具

### macOS录制工具

1. **QuickTime Player**
   - 文件 → 新建屏幕录制
   - 选择要录制的区域
   - 点击录制按钮

2. **LICEcap** (推荐)
   - 开源免费的GIF录制工具
   - 下载地址: https://licecap.en.softonic.com/

### 在线GIF制作

1. **EZGIF**
   - https://ezgif.com/video-to-gif
   - 支持视频转GIF

2. **CloudApp**
   - https://cloudapp.ai/
   - 屏幕录制+云端托管

---

## 📁 GIF存放位置

建议将录制的GIF文件存放在以下位置:

```
📂 docs/
├── 📸 gifs/
│   ├── login_demo.gif
│   ├── dashboard_demo.gif
│   ├── ai_fix_demo.gif
│   ├── git_manager_demo.gif
│   └── error_pages_demo.gif
│
└── GIF制作指南.md
```

---

## 🎬 快速演示脚本

创建自动化演示脚本 `demo.sh`:

```bash
#!/bin/bash

echo "🎬 MTSCOS AI 系统功能演示"
echo "================================"

echo ""
echo "📡 1. 检查系统状态..."
curl -s http://localhost:8888/api/health | python3 -m json.tool

echo ""
echo "🔐 2. 检查Git状态..."
curl -s http://localhost:8888/api/git/status | python3 -m json.tool

echo ""
echo "🤖 3. 运行AI员工批量修复..."
curl -s -X POST http://localhost:8888/api/ai/batch_fix \
  -H "Content-Type: application/json" \
  -d '{"fix_types":["template","route"]}' | python3 -m json.tool

echo ""
echo "📊 4. 查看AI员工列表..."
curl -s http://localhost:8888/api/ai/employees | python3 -m json.tool

echo ""
echo "✅ 演示完成！"
```

赋予执行权限并运行:
```bash
chmod +x demo.sh
./demo.sh
```

---

## 🎨 美化建议

### GIF优化建议

1. **分辨率**: 1280x720 或 1920x1080
2. **帧率**: 10-15 FPS (GIF文件更小)
3. **时长**: 每个GIF控制在5-10秒
4. **文件大小**: 单个GIF不超过2MB

### README中引用GIF

在README.md中添加GIF引用:

```markdown
## 功能演示

### 用户登录
![Login Demo](../docs/gifs/login_demo.gif)

### 超级管理员仪表盘
![Dashboard Demo](../docs/gifs/dashboard_demo.gif)
```

---

## 📝 演示场景设计

### 场景1: 新用户首次体验 (2分钟)

1. 登录系统 (5秒GIF)
2. 查看角色对应页面 (10秒GIF)
3. 体验一个核心功能 (15秒GIF)

### 场景2: AI员工能力展示 (3分钟)

1. 系统出现问题 (5秒GIF)
2. AI员工自动检测 (10秒GIF)
3. AI员工自动修复 (15秒GIF)
4. 验证修复结果 (10秒GIF)

### 场景3: 权限管理演示 (2分钟)

1. 学生账号登录 (5秒GIF)
2. 尝试访问管理员页面 (10秒GIF)
3. 使用硬件管理员登录 (5秒GIF)
4. 访问所有页面 (15秒GIF)

---

## 🎯 最佳实践

1. **提前准备**: 测试所有演示流程确保无错误
2. **简洁明了**: 每个GIF聚焦一个功能点
3. **标注说明**: GIF下方添加简短说明
4. **控制时长**: 避免过长的GIF影响加载速度
5. **提供备选**: 同时提供视频版本作为备选

---

## 📞 技术支持

如果GIF录制过程中遇到问题，请参考:

- QuickTime使用指南: macOS内置帮助
- ffmpeg官方文档: https://ffmpeg.org/documentation.html
- LICEcap使用教程: 官方README文件

---

**创建时间**: 2026-06-27
**最后更新**: 2026-06-27
**维护者**: MTSCOS AI Team