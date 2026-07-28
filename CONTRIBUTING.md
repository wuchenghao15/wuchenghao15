# 贡献指南

首先感谢你花时间为 MTSCOS AI 做贡献！🎉

## 行为准则

请阅读并遵守我们的 [行为准则](CODE_OF_CONDUCT.md)。

## 我该如何贡献？

### 🐛 报告 Bug

如果你发现了 bug，请提交 Issue。在提交 Issue 时，请包含以下信息：

- **清晰的标题** - 简要描述问题
- **复现步骤** - 详细说明如何复现问题
- **预期行为** - 你期望发生什么
- **实际行为** - 实际发生了什么
- **环境信息** - 操作系统、Python版本、浏览器等
- **截图/日志** - 如果有的话

### 💡 提出新功能

有好的想法？欢迎提交 Feature Request！

- 描述功能的详细说明
- 说明为什么这个功能对大多数用户有用
- 如果可能，提供一些使用场景的例子

### 🔧 提交代码

我们欢迎 Pull Request！

#### 提交 PR 前的检查清单

- [ ] 代码遵循项目的代码风格
- [ ] 新功能有对应的测试
- [ ] 文档已更新（如果需要）
- [ ] 所有测试都通过
- [ ] 提交信息清晰规范

#### PR 提交流程

1. Fork 本仓库
2. 创建你的功能分支 (`git checkout -b feature/AmazingFeature`)
3. 提交你的更改 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 发起 Pull Request

### 📝 完善文档

文档也是项目的重要部分！如果你发现：
- 文档有错误或过时
- 某些功能缺少说明
- 示例代码可以改进

欢迎提交 PR 来完善文档！

## 开发指南

### 环境搭建

```bash
# 克隆仓库
git clone https://github.com/wuchenghao15/MTSCOS.git
cd MTSCOS

# 安装依赖
pip install flask

# 启动开发服务器
python server_real_db.py
```

### 运行测试

```bash
cd flask-app
python scripts/tools/mtscos_system_test_engine.py
```

### 代码风格

- 遵循 PEP 8 Python 代码风格
- 使用有意义的变量名和函数名
- 添加必要的注释
- 保持代码简洁易读

### 提交信息规范

我们使用约定式提交（Conventional Commits）：

```
<类型>[可选范围]: <描述>

[可选正文]

[可选页脚]
```

**类型：**
- `feat` - 新功能
- `fix` - Bug 修复
- `docs` - 文档更新
- `style` - 代码格式（不影响功能）
- `refactor` - 重构
- `perf` - 性能优化
- `test` - 添加测试
- `chore` - 构建/工具链等

**示例：**
```
feat(ai): 添加AI员工自动调度功能

- 实现智能调度算法
- 添加调度日志记录
- 优化任务分配策略

Closes #123
```

## 有问题？

如果你有任何问题，欢迎：
- 提交 Issue
- 在 Discussions 中提问
- 查看现有文档

## 致谢

感谢所有为这个项目做出贡献的人！

---

再次感谢你的贡献！❤️
