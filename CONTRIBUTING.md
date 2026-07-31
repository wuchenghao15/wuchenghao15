# 贡献指南

首先，感谢你拨冗为 MTSCOS AI 项目做贡献。

## 行为准则

请阅读并遵守我们的 [行为准则](CODE_OF_CONDUCT.md)。

## 如何贡献

### 报告 Bug

若发现 Bug，请提交 Issue，并包含以下信息：

- **清晰的标题**：简要描述问题
- **复现步骤**：详细说明如何重现问题
- **预期行为**：期望发生什么
- **实际行为**：实际发生了什么
- **环境信息**：操作系统、Python 版本、浏览器等
- **截图 / 日志**：如有请附上

### 提出新功能

如有好的想法，欢迎提交 Feature Request：

- 详细描述功能需求
- 说明该功能对多数用户的价值
- 如可能，提供若干使用场景示例

### 提交代码

欢迎提交 Pull Request。

#### 提交 PR 前的检查清单

- [ ] 代码遵循项目代码风格（PEP 8）
- [ ] 新功能已编写对应测试
- [ ] 文档已更新（如需要）
- [ ] 所有测试通过
- [ ] 提交信息清晰且符合规范

#### PR 提交流程

1. Fork 本仓库
2. 创建功能分支：`git checkout -b feature/AmazingFeature`
3. 提交更改：`git commit -m 'Add some AmazingFeature'`
4. 推送至分支：`git push origin feature/AmazingFeature`
5. 发起 Pull Request

### 完善文档

文档同样是项目的重要组成部分。如发现以下情况，欢迎提交 PR 完善：

- 文档存在错误或已过时
- 某些功能缺少说明
- 示例代码可以改进

---

## 开发指南

### 环境搭建

```bash
# 克隆仓库
git clone https://github.com/wuchenghao15/MTSCOS-AI-Project.git
cd MTSCOS-AI-Project

# 创建虚拟环境并安装依赖（Python 3.9+）
python3 -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install -r requirements.txt

# 启动开发服务器（生产入口）
python3 server_real_db.py --port 8888 --debug
```

## 运行测试

```bash
python3 -m pytest tests/ -x
```

### 代码风格

- 遵循 [PEP 8](https://peps.python.org/pep-0008/) Python 代码风格
- 使用有意义的变量名和函数名
- 添加必要的注释，保持代码简洁易读
- 新增的公开函数应附带 docstring

### 提交信息规范

采用 [约定式提交（Conventional Commits）](https://www.conventionalcommits.org/) 1.0：

```text
<类型>[可选范围]: <描述>

[可选正文]

[可选页脚]
```

**类型：**

| 类型 | 说明 |
| :--- | :--- |
| `feat` | 新功能 |
| `fix` | Bug 修复 |
| `docs` | 文档更新 |
| `style` | 代码格式（不影响功能） |
| `refactor` | 重构 |
| `perf` | 性能优化 |
| `test` | 添加测试 |
| `chore` | 构建 / 工具链等 |

**示例：**

```text
feat(ai): 添加 AI 员工自动调度功能

- 实现智能调度算法
- 添加调度日志记录
- 优化任务分配策略

Closes #123
```

---

## 有问题？

如有任何疑问，欢迎：

- 提交 Issue
- 在 Discussions 中提问
- 查阅现有文档

## 致谢

感谢所有为本项目做出贡献的人。
