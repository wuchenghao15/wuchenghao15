# 贡献指南 | Contributing Guidelines

首先感谢您对 MTSCOS AI 项目的关注！🙏

我们欢迎各种形式的贡献，包括但不限于：

- 🐛 报告 Bug 和问题
- 💡 提出新功能建议
- 🔧 提交代码修复和改进
- 📚 完善文档和翻译
- 🎨 优化UI/UX设计

---

## 📋 目录

- [行为准则](#行为准则)
- [如何贡献](#如何贡献)
- [开发环境搭建](#开发环境搭建)
- [代码规范](#代码规范)
- [提交规范](#提交规范)
- [Pull Request 流程](#pull-request-流程)
- [Issue 指南](#issue-指南)

---

## 行为准则

本项目采用 [Contributor Covenant](https://www.contributor-covenant.org/) 行为准则。参与本项目即表示您同意遵守其条款。

### 我们的承诺

- 🤝 营造友好、包容的环境
- 👥 尊重不同观点和经验
- 🤗 优雅地接受建设性批评
- 💚 关注对社区最有利的事情

---

## 如何贡献

### 1. 报告 Bug 🐛

如果您发现了bug，请通过 [GitHub Issues](https://github.com/wuchenghao15/MTSCOS-AI/issues) 提交。

**请包含以下信息：**
- 清晰的标题和描述
- 复现步骤
- 预期行为和实际行为
- 截图（如果适用）
- 环境信息（操作系统、Python版本、浏览器等）

### 2. 功能建议 💡

我们非常欢迎新功能建议！请在 Issue 中详细描述：

- 您想要的功能是什么？
- 为什么需要这个功能？
- 您期望的实现方式是怎样的？

### 3. 代码贡献 🔧

1. **Fork** 本仓库
2. 创建您的特性分支 (`git checkout -b feature/AmazingFeature`)
3. 提交您的更改 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 开启 **Pull Request**

---

## 开发环境搭建

### 前置要求

- Python 3.8+
- pip 21.0+
- Git

### 安装步骤

```bash
# 1. Fork 并克隆项目
git clone https://github.com/your-username/MTSCOS-AI.git
cd MTSCOS-AI

# 2. 创建虚拟环境
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 3. 安装依赖
cd flask-app
pip install -r requirements.txt

# 4. 初始化数据库
python init.py

# 5. 启动开发服务器
python app.py --port 8888
```

### 运行测试

```bash
# 运行测试套件
python -m pytest tests/

# 代码覆盖率检查
python -m pytest --cov=app tests/
```

---

## 代码规范

### Python 代码规范

- 遵循 [PEP 8](https://www.python.org/dev/peps/pep-0008/) 风格指南
- 使用 4 空格缩进
- 函数和变量使用 snake_case
- 类名使用 PascalCase
- 常量使用 UPPER_SNAKE_CASE
- 添加必要的注释和文档字符串

### JavaScript 代码规范

- 使用 ES6+ 语法
- 遵循 ESLint 推荐规则
- 2 空格缩进
- 变量和函数使用 camelCase

### CSS 代码规范

- 遵循 BEM 命名规范
- 优先使用 Flexbox 和 Grid 布局
- 响应式设计优先

---

## 提交规范

我们采用 [Conventional Commits](https://www.conventionalcommits.org/) 规范。

### 提交格式

```
<type>(<scope>): <subject>

<body>

<footer>
```

### 类型说明

| 类型 | 说明 |
|------|------|
| `feat` | 新功能 |
| `fix` | 修复bug |
| `docs` | 文档更新 |
| `style` | 格式调整（不影响代码运行） |
| `refactor` | 重构（既不是新增功能，也不是修复bug） |
| `perf` | 性能优化 |
| `test` | 测试相关 |
| `chore` | 构建/工具等辅助工具的变动 |

### 示例

```
feat(ai-brain): add knowledge search API

- 实现全文搜索功能
- 添加知识标签过滤
- 支持分页查询

Closes #123
```

---

## Pull Request 流程

### PR 要求

- [ ] 代码通过所有测试
- [ ] 代码符合项目规范
- [ ] 添加了必要的注释和文档
- [ ] 更新了相关的 README 和 CHANGELOG
- [ ] 标题清晰描述了更改内容

### PR 流程

1. 确保您的 PR 针对的是正确的分支（通常是 `main` 或 `MTSCOS`）
2. 填写 PR 模板，描述您做了什么以及为什么
3. 确保 CI 检查通过
4. 等待维护者审核
5. 根据审核意见进行修改
6. PR 被合并！🎉

---

## Issue 指南

### Issue 模板

我们提供了 Issue 模板，请选择合适的模板：

- 🐛 Bug 报告
- 💡 功能建议
- ❓ 问题提问

### 好的 Issue 应该

- ✅ 标题清晰具体
- ✅ 描述详细完整
- ✅ 提供复现步骤
- ✅ 包含环境信息
- ✅ 附上相关截图/代码

---

## 🏷️ 标签说明

| 标签 | 说明 |
|------|------|
| `bug` | Bug 相关 |
| `enhancement` | 功能增强 |
| `feature` | 新功能 |
| `documentation` | 文档相关 |
| `good first issue` | 适合新手 |
| `help wanted` | 需要帮助 |
| `question` | 问题咨询 |
| `duplicate` | 重复 |
| `wontfix` | 不会修复 |
| `invalid` | 无效 |

---

## 📞 联系方式

- **GitHub Issues**: [提交问题](https://github.com/wuchenghao15/MTSCOS-AI/issues)
- **邮箱**: caopinwen87@qq.com

---

再次感谢您的贡献！💖

**MTSCOS AI Team**
