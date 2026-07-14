# 🤝 贡献指南

欢迎您为 MTSCOS AI 智能考试系统做出贡献！无论是修复 bug、添加新功能还是改进文档，我们都非常欢迎。

## 📋 贡献流程

### 1. Fork 仓库

首先，点击 GitHub 页面右上角的 "Fork" 按钮，将仓库 fork 到您自己的账户。

### 2. 克隆仓库

```bash
git clone https://github.com/your-username/wuchenghao15.git
cd wuchenghao15/flask-app
```

### 3. 创建分支

创建一个新的分支来开发您的功能或修复：

```bash
git checkout -b feature/your-feature-name
# 或
git checkout -b fix/your-bug-fix
```

### 4. 开发

在分支上进行开发，确保：

- 代码风格符合项目规范
- 添加适当的测试
- 更新相关文档

### 5. 提交更改

```bash
git add .
git commit -m "feat: 添加你的功能描述"
```

提交信息格式：
- `feat:` 添加新功能
- `fix:` 修复 bug
- `docs:` 更新文档
- `refactor:` 重构代码
- `test:` 添加测试
- `perf:` 性能优化

### 6. 推送到远程

```bash
git push origin feature/your-feature-name
```

### 7. 创建 Pull Request

在 GitHub 上打开一个 Pull Request，描述您的更改。

## 📝 代码规范

### Python 代码规范

- 遵循 PEP 8 规范
- 使用 4 个空格缩进
- 文件名使用 snake_case
- 类名使用 PascalCase
- 函数名和变量名使用 snake_case
- 添加适当的类型提示

### 前端代码规范

- 使用语义化 HTML
- CSS 使用 BEM 命名规范
- JavaScript 遵循 ES6+ 标准
- 添加适当的注释

### 提交信息规范

提交信息应简洁明了，使用英文或中文均可：

```
feat: 添加AI试卷自动组卷功能
- 实现智能选题算法
- 添加知识覆盖率分析
- 支持试卷预览和保存
```

## 🧪 测试

运行测试以确保您的更改没有破坏现有功能：

```bash
# 安装测试依赖
pip install pytest

# 运行测试
pytest tests/
```

## 📋 Issue 模板

在创建 issue 时，请使用以下模板：

- **Bug Report**: 使用 `.github/ISSUE_TEMPLATE/bug_report.md`
- **Feature Request**: 使用 `.github/ISSUE_TEMPLATE/feature_request.md`
- **Question**: 使用 `.github/ISSUE_TEMPLATE/question.md`

## 📦 开发环境

### 设置开发环境

```bash
# 创建虚拟环境
python3 -m venv venv
source venv/bin/activate

# 安装依赖
pip install -r requirements.txt

# 初始化数据库
python -c "from app.utils.db import init_all_databases; init_all_databases()"

# 启动开发服务器
python app.py --port 8888
```

### 代码检查

```bash
# 安装 lint 工具
pip install flake8

# 运行 lint 检查
flake8 app/
```

## 📄 许可证

通过贡献代码，您同意您的贡献将在 MIT 许可证下发布。

## 💬 联系方式

如果您有任何问题或建议，可以通过以下方式联系我们：

- 创建 Issue
- 发送邮件
- 加入讨论

感谢您的贡献！🎉