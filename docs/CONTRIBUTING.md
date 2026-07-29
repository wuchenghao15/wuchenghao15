# MTSCOS AI 贡献指南 / Contributing Guide

> 版本: v17.22.0 | Version: v17.22.0
> 更新日期: 2026-07-26 | Updated: 2026-07-26
>
> [English Version / 英文版](CONTRIBUTING.en.md)

---

## 📋 目录

- [1. 贡献方式](#1-贡献方式)
- [2. 代码规范](#2-代码规范)
- [3. 分支管理](#3-分支管理)
- [4. 提交规范](#4-提交规范)
- [5. PR 流程](#5-pr流程)
- [6. Issue 规范](#6-issue规范)
- [7. 开发环境](#7-开发环境)
- [8. 测试规范](#8-测试规范)
- [9. 文档贡献](#9-文档贡献)
- [10. 社区行为准则](#10-社区行为准则)

---

## 1. 贡献方式

欢迎以任何方式贡献！以下是一些常见的贡献方式：

| 贡献类型 | 说明 | 适合人群 |
|----------|------|---------|
| 代码贡献 | 修复 Bug、添加新功能 | 开发者 |
| 文档贡献 | 完善文档、翻译文档 | 技术写作者 |
| Bug 报告 | 报告发现的 Bug | 所有用户 |
| 功能建议 | 提出新功能想法 | 所有用户 |
| 测试贡献 | 编写测试用例 | 测试工程师 |
| 设计贡献 | UI 设计、图标设计 | 设计师 |

---

## 2. 代码规范

### Python 代码规范

项目遵循 [PEP 8](https://peps.python.org/pep-0008/) 规范，同时遵循以下额外规则：

| 规则 | 说明 | 示例 |
|------|------|------|
| 缩进 | 使用 4 个空格 | `def func():` |
| 行长度 | 最大 127 字符 | 超过时合理换行 |
| 命名 | 变量 / 函数用 snake_case | `user_name`, `get_user()` |
| 类名 | 使用 PascalCase | `class UserManager:` |
| 常量 | 使用 UPPER_SNAKE_CASE | `MAX_RETRY = 3` |
| 导入顺序 | 标准库 → 第三方 → 本地 | 按字母排序 |
| 类型提示 | 建议添加类型提示 | `def get_user(id: int) -> User:` |

### HTML / CSS 代码规范

| 规则 | 说明 |
|------|------|
| 标签命名 | 使用 kebab-case | `<user-profile>` |
| CSS 命名 | 使用 BEM 规范 | `.block__element--modifier` |
| 属性顺序 | class → id → name → 其他 | 保持一致性 |
| 缩进 | 使用 2 个空格 | 保持代码整洁 |

### JavaScript 代码规范

| 规则 | 说明 |
|------|------|
| 变量声明 | 使用 const / let | 避免使用 var |
| 箭头函数 | 简洁函数使用箭头函数 | `items.map(item => item.id)` |
| 字符串 | 使用反引号 | 支持模板字符串 |
| 导入导出 | 使用 ES6 模块 | `import`, `export` |

---

## 3. 分支管理

### 分支策略

| 分支 | 用途 | 保护状态 |
|------|------|---------|
| `main` | 主分支，生产环境代码 | ✅ 受保护 |
| `develop` | 开发分支，集成所有功能 | ✅ 受保护 |
| `feature/xxx` | 功能分支，开发新功能 | - |
| `bugfix/xxx` | Bug 修复分支 | - |
| `hotfix/xxx` | 紧急修复分支 | - |
| `release/xxx` | 发布分支 | - |

### 分支命名规范

```text
<类型>/<描述>
```

| 类型 | 说明 | 示例 |
|------|------|------|
| feature | 新功能 | `feature/ai-question-generator` |
| bugfix | Bug 修复 | `bugfix/login-redirect` |
| hotfix | 紧急修复 | `hotfix/security-patch` |
| release | 发布准备 | `release/v17.22.0` |
| docs | 文档更新 | `docs/readme-update` |
| refactor | 代码重构 | `refactor/api-blueprints` |

---

## 4. 提交规范

### 提交信息格式

```text
<类型>(<范围>): <描述>

<详细说明>

<相关引用>
```

### 类型说明

| 类型 | 说明 | 示例 |
|------|------|------|
| `feat` | 新功能 | `feat(ai): 添加 AI 题目生成器` |
| `fix` | Bug 修复 | `fix(auth): 修复登录重定向问题` |
| `docs` | 文档更新 | `docs(readme): 更新部署指南` |
| `style` | 样式修改 | `style(css): 优化响应式布局` |
| `refactor` | 代码重构 | `refactor(api): 重构 API 模块` |
| `test` | 测试代码 | `test(auth): 添加登录测试用例` |
| `chore` | 构建 / 工具更新 | `chore(deps): 更新依赖包` |
| `perf` | 性能优化 | `perf(db): 优化数据库查询` |
| `security` | 安全修复 | `security(firewall): 修复 SQL 注入漏洞` |

### 范围说明

| 范围 | 说明 |
|------|------|
| `app` | 应用核心 |
| `api` | API 接口 |
| `auth` | 认证系统 |
| `ai` | AI 引擎 |
| `db` | 数据库 |
| `admin` | 管理后台 |
| `exam` | 考试系统 |
| `question` | 题库系统 |
| `learning` | 学习系统 |
| `security` | 安全模块 |
| `docs` | 文档 |
| `config` | 配置 |

### 示例

```text
feat(ai): 添加 AI 学习路径推荐功能

- 分析学生错题数据
- 识别薄弱环节
- 生成个性化学习路径
- 跟踪学习进度

Closes #123
```

---

## 5. PR 流程

### 提交 PR 步骤

1. **Fork 仓库**
   - 在 GitHub 上 Fork 本仓库到自己的账户

2. **克隆仓库**
   ```bash
   git clone https://github.com/your-username/MTSCOS-AI-Project.git
   cd MTSCOS-AI-Project
   ```

3. **添加上游仓库**
   ```bash
   git remote add upstream https://github.com/wuchenghao15/MTSCOS-AI-Project.git
   ```

4. **创建分支**
   ```bash
   git checkout -b feature/your-feature-name
   ```

5. **开发功能**
   - 实现功能或修复 Bug
   - 编写测试用例
   - 更新相关文档

6. **提交代码**
   ```bash
   git add .
   git commit -m "feat(xxx): 描述"
   ```

7. **同步上游**
   ```bash
   git fetch upstream
   git rebase upstream/develop
   ```

8. **推送分支**
   ```bash
   git push origin feature/your-feature-name
   ```

9. **创建 PR**
   - 在 GitHub 上创建 Pull Request 到 `develop` 分支
   - 填写 PR 描述，说明变更内容
   - 添加相关标签

10. **代码审查**
    - 等待项目维护者审查
    - 根据反馈修改代码
    - 保持 PR 更新

11. **合并分支**
    - PR 通过审查后合并到 `develop`
    - 删除功能分支

### PR 模板

```markdown
## 摘要

<简要描述 PR 的内容>

## 变更内容

- [ ] 功能 A
- [ ] 功能 B
- [ ] Bug 修复

## 测试计划

- [ ] 单元测试
- [ ] 集成测试
- [ ] 手动测试

## 相关 Issue

Closes #123
Related #456
```

---

## 6. Issue 规范

### Issue 类型

| 类型 | 说明 | 标签 |
|------|------|------|
| Bug | 报告 Bug | `bug` |
| Feature | 新功能请求 | `feature` |
| Enhancement | 功能增强 | `enhancement` |
| Documentation | 文档问题 | `documentation` |
| Question | 问题咨询 | `question` |
| Help Wanted | 需要帮助 | `help wanted` |

### Bug 报告模板

```markdown
## Bug 描述

<详细描述 Bug 的表现>

## 复现步骤

1. <步骤 1>
2. <步骤 2>
3. <步骤 3>

## 预期结果

<期望的行为>

## 实际结果

<实际发生的行为>

## 环境信息

- 版本: <版本号>
- 操作系统: <操作系统>
- 浏览器: <浏览器>
```

### 功能请求模板

```markdown
## 功能描述

<详细描述期望的功能>

## 使用场景

<描述该功能的使用场景>

## 实现建议

<如有建议，请描述>

## 优先级

- [ ] 高
- [ ] 中
- [ ] 低
```

---

## 7. 开发环境

### 环境要求

- Python 3.9+
- SQLite 3.30+
- Redis 7.0+（可选）
- Git
- pip 20.0+

### 环境搭建

1. **克隆仓库**
```bash
git clone https://github.com/wuchenghao15/MTSCOS-AI-Project.git
cd MTSCOS-AI-Project
```

2. **创建虚拟环境**
```bash
python3 -m venv venv
source venv/bin/activate
```

3. **安装依赖**
```bash
pip install -r flask-app/requirements.txt
```

4. **启动开发服务器**
```bash
python3 server_preview.py --port 8888 --debug
```

5. **运行测试**
```bash
python -m pytest
```

### 开发工具

| 工具 | 用途 |
|------|------|
| flake8 | Python 代码检查 |
| pylint | Python 代码分析 |
| pytest | 测试框架 |
| black | 代码格式化 |
| isort | 导入排序 |

---

## 8. 测试规范

### 测试类型

| 测试类型 | 说明 | 工具 |
|----------|------|------|
| 单元测试 | 测试单个函数 / 方法 | pytest |
| 集成测试 | 测试模块间交互 | pytest |
| 端到端测试 | 测试完整流程 | pytest |

### 测试覆盖要求

- 新增功能必须编写单元测试
- 核心模块测试覆盖率 ≥ 80%
- 关键路径必须有集成测试

### 测试文件命名

```text
tests/test_<模块名>.py
```

### 测试用例命名

```python
def test_<功能>_<场景>_<预期结果>():
    pass
```

---

## 9. 文档贡献

### 文档类型

| 文档 | 文件 | 说明 |
|------|------|------|
| 项目介绍 | README.md | 项目概述和快速开始 |
| 英文文档 | README.md | 英文项目介绍 |
| 中文文档 | README.zh-CN.md | 中文项目介绍 |
| 部署指南 | DEPLOYMENT_GUIDE.md | 详细部署说明 |
| 系统文档 | SYSTEM_DOC.md | 系统详细说明 |
| 安全文档 | SECURITY.md | 安全相关文档 |
| 贡献指南（中文） | CONTRIBUTING.md | 中文贡献说明 |
| 贡献指南（英文） | CONTRIBUTING.en.md | 英文贡献说明 |
| 变更日志 | CHANGELOG.md | 版本变更记录 |

### 文档规范

- 使用 Markdown 格式
- 中文文档使用中文标点
- 英文文档使用英文标点
- 保持文档与代码同步
- 添加必要的代码示例

### 文档翻译

- 中文文档翻译为英文时，保持专业性和准确性
- 英文术语统一：
  - 登录 → Login
  - 注册 → Register
  - 管理员 → Admin
  - 学生 → Student
  - 教师 → Teacher
  - 题库 → Question Bank
  - 考试 → Exam
  - 学习 → Learning

---

## 10. 社区行为准则

### 行为规范

1. **尊重他人**：尊重所有贡献者和用户
2. **友好沟通**：使用友好、专业的语言
3. **积极协作**：乐于帮助他人，分享知识
4. **遵守规则**：遵守项目规则和代码规范
5. **诚实守信**：不提交虚假信息或恶意代码

### 禁止行为

1. **骚扰**：不进行人身攻击或骚扰
2. **歧视**：不基于性别、种族、宗教等进行歧视
3. **滥用**：不滥用 Issue 或 PR 功能
4. **恶意代码**：不提交恶意代码或漏洞
5. **泄露**：不泄露敏感信息

### 争议解决

1. **沟通解决**：优先通过沟通解决争议
2. **寻求帮助**：可联系项目维护者寻求帮助
3. **社区仲裁**：如无法解决，由社区成员共同仲裁

---

## 🤝 加入我们

欢迎加入 MTSCOS AI 社区！

- GitHub: https://github.com/wuchenghao15/MTSCOS-AI-Project
- 讨论区: https://github.com/wuchenghao15/MTSCOS-AI-Project/discussions
- Issues: https://github.com/wuchenghao15/MTSCOS-AI-Project/issues

**感谢您的贡献！** 🚀
