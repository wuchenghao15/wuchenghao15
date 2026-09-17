# Installation

Hyper-Extract requires **Python 3.11+**.

---

## Install as CLI Tool

If you want to use the `he` command from anywhere:

=== "uv (recommended)"

    Install [uv](https://docs.astral.sh/uv/) first (if you haven't):

    ```bash
    curl -LsSf https://astral.sh/uv/install.sh | sh
    ```

    Then install Hyper-Extract:

    ```bash
    uv tool install hyperextract
    ```

=== "pipx"

    ```bash
    pipx install hyperextract
    ```

    > Don't have pipx? Install it with `pip install pipx`.

---

## Install as Python Library

If you want to use Hyper-Extract in your Python code:

=== "uv (recommended)"

    ```bash
    uv pip install hyperextract
    ```

=== "pip"

    ```bash
    pip install hyperextract
    ```

---

## Verify Installation

=== "CLI"

    ```bash
    he --version
    ```

    You should see something like:

    ```
    Hyper-Extract CLI version 0.4.0
    ```

=== "Python"

    ```python
    import hyperextract
    print(hyperextract.__version__)
    ```

---

## Development Installation

If you want to contribute or modify the source code:

```bash
git clone https://github.com/yifanfeng97/hyper-extract.git
cd hyper-extract

# Install with uv (recommended) — includes the `dev` dependency group
uv sync

# Or with pip (pip 25.1+)
pip install -e . --group dev
```

---

## What's Next?

- [:octicons-arrow-right-24: CLI Quickstart](cli-quickstart.md) — Your first extraction from the terminal
- [:octicons-arrow-right-24: Python Quickstart](python-quickstart.md) — Your first extraction with Python
