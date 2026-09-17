# 安装

Hyper-Extract 需要 **Python 3.11+**。

---

## 安装为 CLI 工具

如果您想在任何地方使用 `he` 命令：

=== "uv (推荐)"

    首先安装 [uv](https://docs.astral.sh/uv/)（如果尚未安装）：

    ```bash
    curl -LsSf https://astral.sh/uv/install.sh | sh
    ```

    然后安装 Hyper-Extract：

    ```bash
    uv tool install hyperextract
    ```

=== "pipx"

    ```bash
    pipx install hyperextract
    ```

    > 没有安装 pipx？运行 `pip install pipx` 安装。

---

## 安装为 Python 库

如果您想在 Python 代码中使用 Hyper-Extract：

=== "uv (推荐)"

    ```bash
    uv pip install hyperextract
    ```

=== "pip"

    ```bash
    pip install hyperextract
    ```

---

## 验证安装

=== "CLI"

    ```bash
    he --version
    ```

    您应该看到类似输出：

    ```
    Hyper-Extract CLI version 0.4.0
    ```

=== "Python"

    ```python
    import hyperextract
    print(hyperextract.__version__)
    ```

---

## 开发安装

如果您想贡献或修改源代码：

```bash
git clone https://github.com/yifanfeng97/hyper-extract.git
cd hyper-extract

# 使用 uv 安装（推荐）——会安装 `dev` 依赖组
uv sync

# 或使用 pip（pip 25.1+）
pip install -e . --group dev
```

---

## 接下来做什么？

- [:octicons-arrow-right-24: CLI 快速入门](cli-quickstart.md) — 从终端进行首次提取
- [:octicons-arrow-right-24: Python 快速入门](python-quickstart.md) — 使用 Python 进行首次提取
