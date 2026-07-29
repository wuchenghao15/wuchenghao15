# MTSCOS AI Contributing Guide

> Version: v17.22.0
> Updated: 2026-07-26
>
> [中文版本 / Chinese Version](CONTRIBUTING.md)

---

## 📋 Table of Contents

- [1. Ways to Contribute](#1-ways-to-contribute)
- [2. Code Standards](#2-code-standards)
- [3. Branch Management](#3-branch-management)
- [4. Commit Standards](#4-commit-standards)
- [5. PR Process](#5-pr-process)
- [6. Issue Guidelines](#6-issue-guidelines)
- [7. Development Environment](#7-development-environment)
- [8. Testing Standards](#8-testing-standards)
- [9. Documentation Contributions](#9-documentation-contributions)
- [10. Community Code of Conduct](#10-community-code-of-conduct)

---

## 1. Ways to Contribute

Welcome to contribute in any way! Here are some common ways:

| Contribution Type | Description | Suitable For |
|-------------------|-------------|-------------|
| Code Contributions | Fix bugs, add new features | Developers |
| Documentation | Improve docs, translate | Technical Writers |
| Bug Reports | Report discovered bugs | All Users |
| Feature Requests | Propose new feature ideas | All Users |
| Testing | Write test cases | Test Engineers |
| Design | UI design, icon design | Designers |

---

## 2. Code Standards

### Python Code Standards

The project follows [PEP 8](https://peps.python.org/pep-0008/) with the following additional rules:

| Rule | Description | Example |
|------|-------------|---------|
| Indentation | Use 4 spaces | `def func():` |
| Line Length | Max 127 characters | Reasonable line breaks when exceeded |
| Naming | Variables/functions: snake_case | `user_name`, `get_user()` |
| Class Names | Use PascalCase | `class UserManager:` |
| Constants | Use UPPER_SNAKE_CASE | `MAX_RETRY = 3` |
| Import Order | Stdlib → Third-party → Local | Sort alphabetically |
| Type Hints | Type hints recommended | `def get_user(id: int) -> User:` |

### HTML / CSS Code Standards

| Rule | Description |
|------|-------------|
| Tag Naming | Use kebab-case | `<user-profile>` |
| CSS Naming | Use BEM convention | `.block__element--modifier` |
| Attribute Order | class → id → name → others | Be consistent |
| Indentation | Use 2 spaces | Keep code clean |

### JavaScript Code Standards

| Rule | Description |
|------|-------------|
| Variable Declaration | Use const / let | Avoid var |
| Arrow Functions | Use arrow functions for concise functions | `items.map(item => item.id)` |
| Strings | Use backticks | Support template strings |
| Import/Export | Use ES6 modules | `import`, `export` |

---

## 3. Branch Management

### Branch Strategy

| Branch | Purpose | Protection |
|--------|---------|------------|
| `main` | Main branch, production code | ✅ Protected |
| `develop` | Development branch, integrate all features | ✅ Protected |
| `feature/xxx` | Feature branch for new features | - |
| `bugfix/xxx` | Bug fix branch | - |
| `hotfix/xxx` | Emergency fix branch | - |
| `release/xxx` | Release branch | - |

### Branch Naming Convention

```text
<type>/<description>
```

| Type | Description | Example |
|------|-------------|---------|
| feature | New feature | `feature/ai-question-generator` |
| bugfix | Bug fix | `bugfix/login-redirect` |
| hotfix | Emergency fix | `hotfix/security-patch` |
| release | Release preparation | `release/v17.22.0` |
| docs | Documentation update | `docs/readme-update` |
| refactor | Code refactoring | `refactor/api-blueprints` |

---

## 4. Commit Standards

### Commit Message Format

```text
<type>(<scope>): <description>

<detailed description>

<related references>
```

### Type Description

| Type | Description | Example |
|------|-------------|---------|
| `feat` | New feature | `feat(ai): Add AI question generator` |
| `fix` | Bug fix | `fix(auth): Fix login redirect issue` |
| `docs` | Documentation update | `docs(readme): Update deployment guide` |
| `style` | Style modification | `style(css): Optimize responsive layout` |
| `refactor` | Code refactoring | `refactor(api): Refactor API module` |
| `test` | Test code | `test(auth): Add login test cases` |
| `chore` | Build/tool update | `chore(deps): Update dependencies` |
| `perf` | Performance optimization | `perf(db): Optimize database queries` |
| `security` | Security fix | `security(firewall): Fix SQL injection vulnerability` |

### Scope Description

| Scope | Description |
|-------|-------------|
| `app` | Application core |
| `api` | API interfaces |
| `auth` | Authentication system |
| `ai` | AI engine |
| `db` | Database |
| `admin` | Admin backend |
| `exam` | Exam system |
| `question` | Question bank system |
| `learning` | Learning system |
| `security` | Security module |
| `docs` | Documentation |
| `config` | Configuration |

### Example

```text
feat(ai): Add AI learning path recommendation

- Analyze student incorrect answer data
- Identify weak areas
- Generate personalized learning path
- Track learning progress

Closes #123
```

---

## 5. PR Process

### Steps to Submit a PR

1. **Fork the Repository**
   - Fork this repository on GitHub to your own account

2. **Clone the Repository**
   ```bash
   git clone https://github.com/your-username/MTSCOS-AI-Project.git
   cd MTSCOS-AI-Project
   ```

3. **Add Upstream Remote**
   ```bash
   git remote add upstream https://github.com/wuchenghao15/MTSCOS-AI-Project.git
   ```

4. **Create a Branch**
   ```bash
   git checkout -b feature/your-feature-name
   ```

5. **Develop the Feature**
   - Implement the feature or fix the bug
   - Write test cases
   - Update related documentation

6. **Commit the Code**
   ```bash
   git add .
   git commit -m "feat(xxx): description"
   ```

7. **Sync with Upstream**
   ```bash
   git fetch upstream
   git rebase upstream/develop
   ```

8. **Push the Branch**
   ```bash
   git push origin feature/your-feature-name
   ```

9. **Create a PR**
   - Create a Pull Request on GitHub to the `develop` branch
   - Fill in the PR description explaining the changes
   - Add relevant labels

10. **Code Review**
    - Wait for project maintainers to review
    - Modify code based on feedback
    - Keep the PR updated

11. **Merge the Branch**
    - Merge into `develop` after PR passes review
    - Delete the feature branch

### PR Template

```markdown
## Summary

<Brief description of the PR content>

## Changes

- [ ] Feature A
- [ ] Feature B
- [ ] Bug Fix

## Test Plan

- [ ] Unit Tests
- [ ] Integration Tests
- [ ] Manual Tests

## Related Issues

Closes #123
Related #456
```

---

## 6. Issue Guidelines

### Issue Types

| Type | Description | Label |
|------|-------------|-------|
| Bug | Report a bug | `bug` |
| Feature | New feature request | `feature` |
| Enhancement | Feature enhancement | `enhancement` |
| Documentation | Documentation issue | `documentation` |
| Question | Inquiry | `question` |
| Help Wanted | Need help | `help wanted` |

### Bug Report Template

```markdown
## Bug Description

<Detailed description of the bug behavior>

## Steps to Reproduce

1. <Step 1>
2. <Step 2>
3. <Step 3>

## Expected Result

<Expected behavior>

## Actual Result

<Actual behavior>

## Environment Information

- Version: <version>
- Operating System: <OS>
- Browser: <browser>
```

### Feature Request Template

```markdown
## Feature Description

<Detailed description of the desired feature>

## Use Cases

<Describe the use cases for this feature>

## Implementation Suggestions

<If you have suggestions, describe them>

## Priority

- [ ] High
- [ ] Medium
- [ ] Low
```

---

## 7. Development Environment

### Environment Requirements

- Python 3.9+
- SQLite 3.30+
- Redis 7.0+ (optional)
- Git
- pip 20.0+

### Environment Setup

1. **Clone the Repository**
```bash
git clone https://github.com/wuchenghao15/MTSCOS-AI-Project.git
cd MTSCOS-AI-Project
```

2. **Create Virtual Environment**
```bash
python3 -m venv venv
source venv/bin/activate
```

3. **Install Dependencies**
```bash
pip install -r flask-app/requirements.txt
```

4. **Start Development Server**
```bash
python3 server_preview.py --port 8888 --debug
```

5. **Run Tests**
```bash
python -m pytest
```

### Development Tools

| Tool | Purpose |
|------|---------|
| flake8 | Python code linting |
| pylint | Python code analysis |
| pytest | Testing framework |
| black | Code formatting |
| isort | Import sorting |

---

## 8. Testing Standards

### Test Types

| Test Type | Description | Tool |
|-----------|-------------|------|
| Unit Tests | Test individual functions/methods | pytest |
| Integration Tests | Test inter-module interactions | pytest |
| End-to-End Tests | Test complete flows | pytest |

### Test Coverage Requirements

- New features must have unit tests
- Core modules test coverage ≥ 80%
- Key paths must have integration tests

### Test File Naming

```text
tests/test_<module_name>.py
```

### Test Case Naming

```python
def test_<feature>_<scenario>_<expected_result>():
    pass
```

---

## 9. Documentation Contributions

### Documentation Types

| Document | File | Description |
|----------|------|-------------|
| Project Intro | README.md | Project overview and quick start |
| Chinese Docs | README.zh-CN.md | Chinese project documentation |
| Deployment Guide | DEPLOYMENT_GUIDE.md | Detailed deployment instructions |
| System Docs | SYSTEM_DOC.md | Detailed system description |
| Security Docs | SECURITY.md | Security-related documentation |
| Contributing | CONTRIBUTING.md | Contribution guidelines |
| Changelog | CHANGELOG.md | Version change records |

### Documentation Standards

- Use Markdown format
- Chinese documents use Chinese punctuation
- English documents use English punctuation
- Keep documentation synchronized with code
- Add necessary code examples

### Documentation Translation

- When translating Chinese to English, maintain professionalism and accuracy
- Unified English terminology:
  - 登录 → Login
  - 注册 → Register
  - 管理员 → Admin
  - 学生 → Student
  - 教师 → Teacher
  - 题库 → Question Bank
  - 考试 → Exam
  - 学习 → Learning

---

## 10. Community Code of Conduct

### Behavior Standards

1. **Respect Others**: Respect all contributors and users
2. **Friendly Communication**: Use friendly, professional language
3. **Active Collaboration**: Be willing to help others and share knowledge
4. **Follow Rules**: Follow project rules and code standards
5. **Honesty**: Do not submit false information or malicious code

### Prohibited Behavior

1. **Harassment**: No personal attacks or harassment
2. **Discrimination**: No discrimination based on gender, race, religion, etc.
3. **Abuse**: Do not abuse Issue or PR features
4. **Malicious Code**: Do not submit malicious code or vulnerabilities
5. **Disclosure**: Do not disclose sensitive information

### Dispute Resolution

1. **Communicate First**: Resolve disputes through communication first
2. **Seek Help**: Contact project maintainers for assistance
3. **Community Arbitration**: If unresolved, community members arbitrate together

---

## 🤝 Join Us

Welcome to join the MTSCOS AI community!

- GitHub: https://github.com/wuchenghao15/MTSCOS-AI-Project
- Discussions: https://github.com/wuchenghao15/MTSCOS-AI-Project/discussions
- Issues: https://github.com/wuchenghao15/MTSCOS-AI-Project/issues

**Thank you for your contribution!** 🚀