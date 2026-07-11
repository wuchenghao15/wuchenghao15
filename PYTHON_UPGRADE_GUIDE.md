# Python升级指南

## 概述

当前项目使用Python 3.9.6，存在4个GitHub安全漏洞无法修复：
- **aiohttp**: 2个高危漏洞
- **requests**: 1个中危漏洞
- **urllib3**: 2个中危漏洞
- **python-dotenv**: 1个中危漏洞

**根本解决方案**：升级Python到3.10+版本（建议3.11或3.12）。

## 升级步骤

### 方法一：使用pyenv（推荐）

```bash
# 1. 安装pyenv（如果尚未安装）
git clone https://github.com/pyenv/pyenv.git ~/.pyenv

# 2. 配置环境变量（添加到~/.zshrc或~/.bashrc）
echo 'export PATH="$HOME/.pyenv/bin:$PATH"' >> ~/.zshrc
echo 'eval "$(pyenv init -)"' >> ~/.zshrc
source ~/.zshrc

# 3. 安装Python 3.11或3.12
pyenv install 3.11.10

# 4. 设置全局Python版本
pyenv global 3.11.10

# 5. 验证版本
python --version  # 应显示 Python 3.11.10

# 6. 更新依赖
pip install --upgrade pip
pip install -r requirements.txt
```

### 方法二：使用官方安装包

1. 访问 https://www.python.org/downloads/macos/
2. 下载Python 3.11或3.12的.pkg安装包
3. 运行安装程序
4. 更新依赖：
   ```bash
   pip install --upgrade pip
   pip install -r requirements.txt
   ```

### 方法三：使用Homebrew（如果已安装）

```bash
brew install python@3.11
echo 'export PATH="/opt/homebrew/bin/python3:$PATH"' >> ~/.zshrc
source ~/.zshrc
python3 --version
pip3 install -r requirements.txt
```

## 验证升级结果

```bash
# 1. 检查Python版本
python --version

# 2. 安装依赖并验证
pip install -r requirements.txt

# 3. 运行漏洞扫描
pip install pip-audit
pip-audit

# 4. 启动应用验证
cd flask-app
python app.py
```

## 依赖兼容性检查

### 需要Python 3.10+的包

| 包名 | 旧版本 | 新版本 | 漏洞修复 |
|------|--------|--------|----------|
| aiohttp | 3.13.5 | 3.14.1 | 11个漏洞(2个高危) |
| requests | 3.32.5 | 2.33.0 | GHSA-gc5v-m9x4-r6x2 |
| urllib3 | 2.6.3 | 2.7.0 | PYSEC-2026-142, PYSEC-2026-141 |
| python-dotenv | 1.2.1 | 1.2.2 | GHSA-mf9w-mj56-hr94 |
| filelock | 3.19.1 | 3.20.3 | 2个漏洞 |
| pytest | 8.4.2 | 9.0.3 | 1个漏洞 |

### Python 3.9兼容方案

如果暂时无法升级Python，可使用兼容版本：

```bash
# 使用Python 3.9兼容依赖
pip install -r flask-app/requirements-python39.txt
```

**注意**：此方案无法修复安全漏洞，仅用于临时过渡。

## 升级后验证清单

- [ ] Python版本 >= 3.10
- [ ] 所有依赖安装成功
- [ ] `pip-audit`无高危漏洞
- [ ] Flask应用正常启动
- [ ] 数据库连接正常
- [ ] 所有页面功能正常

## 常见问题

### Q: 升级后pip命令找不到？
A: 使用`python -m pip`替代`pip`

### Q: 虚拟环境需要重新创建吗？
A: 是的，需要在新Python版本下重新创建虚拟环境：
```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### Q: 升级后某些包安装失败？
A: 检查是否需要安装系统依赖：
```bash
# macOS
xcode-select --install
brew install openssl readline sqlite3 xz zlib

# Ubuntu/Debian
sudo apt-get install build-essential libssl-dev zlib1g-dev \
    libbz2-dev libreadline-dev libsqlite3-dev wget curl llvm \
    libncursesw5-dev xz-utils tk-dev libxml2-dev libxmlsec1-dev \
    libffi-dev liblzma-dev
```

## 参考链接

- [Python官方下载](https://www.python.org/downloads/)
- [pyenv文档](https://github.com/pyenv/pyenv)
- [GitHub安全报告](https://github.com/wuchenghao15/wuchenghao15/security/dependabot)

## 更新日志

- 2026-07-11: 初始版本