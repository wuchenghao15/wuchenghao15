"""
Node.js runtime environment setup utilities.

Provides functions to detect, install, and configure Node.js and npm
using nvm (Node Version Manager) on Unix-like systems.
"""

from __future__ import annotations

import os
import platform
import subprocess
import tempfile
from pathlib import Path
from typing import Optional, Tuple

import requests

from m_flow.shared.logging_utils import get_logger

_log = get_logger()

# nvm installation script URL
_NVM_INSTALL_URL = "https://raw.githubusercontent.com/nvm-sh/nvm/v0.40.3/install.sh"

# Timeout settings (seconds)
_CMD_TIMEOUT = 10
_INSTALL_TIMEOUT = 120
_NODE_INSTALL_TIMEOUT = 300


def _resolve_nvm_directory() -> Path:
    """
    Determine nvm installation directory.

    Follows XDG Base Directory specification: uses XDG_CONFIG_HOME/nvm
    if XDG_CONFIG_HOME is set, otherwise defaults to ~/.nvm.
    """
    xdg_config = os.environ.get("XDG_CONFIG_HOME")
    if xdg_config:
        return Path(xdg_config) / "nvm"
    return Path.home() / ".nvm"


def _resolve_nvm_script() -> Path:
    """Get path to nvm.sh initialization script."""
    return _resolve_nvm_directory() / "nvm.sh"


def _is_windows() -> bool:
    """Check if running on Windows."""
    return platform.system() == "Windows"


def _execute_cmd(
    cmd: list[str],
    timeout: int = _CMD_TIMEOUT,
    shell: bool = False,
) -> subprocess.CompletedProcess:
    """
    Execute command with timeout and capture output.

    Args:
        cmd: Command and arguments
        timeout: Timeout in seconds
        shell: Use shell execution
    """
    return subprocess.run(
        cmd,
        capture_output=True,
        text=True,
        timeout=timeout,
        shell=shell,
    )


def _execute_bash_cmd(script: str, timeout: int = _CMD_TIMEOUT) -> subprocess.CompletedProcess:
    """Execute bash script with timeout."""
    return subprocess.run(
        ["bash", "-c", script],
        capture_output=True,
        text=True,
        timeout=timeout,
    )


def _source_nvm_and_run(command: str, timeout: int = _CMD_TIMEOUT) -> subprocess.CompletedProcess:
    """Source nvm and execute a command."""
    nvm_script = _resolve_nvm_script()
    full_script = f"source {nvm_script} && {command}"
    return _execute_bash_cmd(full_script, timeout=timeout)


# Compatibility aliases
def get_nvm_dir() -> Path:
    """Alias for _resolve_nvm_directory."""
    return _resolve_nvm_directory()


def get_nvm_sh_path() -> Path:
    """Alias for _resolve_nvm_script."""
    return _resolve_nvm_script()


def check_nvm_installed() -> bool:
    """
    Check if nvm is properly installed and functional.

    Returns:
        True if nvm is available, False otherwise
    """
    try:
        if _is_windows():
            # Windows uses nvm-windows (different implementation)
            result = _execute_cmd(["nvm", "version"], shell=True)
            return result.returncode == 0

        # Unix: nvm is a shell function, must source nvm.sh first
        nvm_script = _resolve_nvm_script()

        if not nvm_script.exists():
            _log.debug(f"nvm script not found: {nvm_script}")
            return False

        result = _source_nvm_and_run("nvm --version")

        if result.returncode != 0:
            if result.stderr:
                _log.debug(f"nvm verification failed: {result.stderr.strip()}")
            return False

        return True

    except Exception as err:
        _log.debug(f"nvm check exception: {err}")
        return False


def install_nvm() -> bool:
    """
    Install nvm on Unix-like systems.

    Note: Windows requires manual nvm-windows installation.

    Returns:
        True if installation succeeded, False otherwise
    """
    if _is_windows():
        _log.error("Windows requires nvm-windows for nvm functionality.")
        _log.error("Download from: https://github.com/coreybutler/nvm-windows")
        return False

    _log.info("Installing nvm (Node Version Manager)...")

    try:
        # Fetch installer script
        _log.info(f"Fetching nvm installer: {_NVM_INSTALL_URL}")
        response = requests.get(_NVM_INSTALL_URL, timeout=60)
        response.raise_for_status()

        # Write to temporary file
        with tempfile.NamedTemporaryFile(mode="w", suffix=".sh", delete=False) as tf:
            tf.write(response.text)
            script_path = tf.name

        try:
            # Execute installer
            os.chmod(script_path, 0o755)
            result = _execute_bash_cmd(script_path, timeout=_INSTALL_TIMEOUT)

            if result.returncode != 0:
                _log.error(f"nvm install failed: {result.stderr}")
                return False

            _log.info("✓ nvm installation completed")

            # Verify installation directory exists
            nvm_dir = _resolve_nvm_directory()
            if not nvm_dir.exists():
                _log.warning(f"nvm directory missing after install: {nvm_dir}")
                return False

            return True

        finally:
            # Cleanup temp script
            try:
                os.unlink(script_path)
            except OSError:
                pass

    except requests.RequestException as err:
        _log.error(f"Failed to fetch nvm installer: {err}")
        return False
    except Exception as err:
        _log.error(f"nvm installation error: {err}")
        return False


def install_node_with_nvm() -> bool:
    """
    Install latest Node.js using nvm.

    Returns:
        True if installation succeeded, False otherwise
    """
    if _is_windows():
        _log.error("Use nvm-windows for Node.js installation on Windows.")
        _log.error("Or install directly from: https://nodejs.org/")
        return False

    _log.info("Installing Node.js via nvm...")

    try:
        nvm_script = _resolve_nvm_script()

        if not nvm_script.exists():
            _log.error(f"nvm script not found: {nvm_script}")
            return False

        # Install latest Node.js
        result = _source_nvm_and_run("nvm install node", timeout=_NODE_INSTALL_TIMEOUT)

        if result.returncode != 0:
            _log.error(f"Node.js install failed: {result.stderr}")
            return False

        _log.info("✓ Node.js installed via nvm")

        # Set as default
        _source_nvm_and_run("nvm alias default node", timeout=30)

        # Update PATH for current process
        _update_path_with_node()

        return True

    except subprocess.TimeoutExpired:
        _log.error("Node.js installation timed out (may take several minutes)")
        return False
    except Exception as err:
        _log.error(f"Node.js installation error: {err}")
        return False


def _update_path_with_node() -> None:
    """Add nvm-managed Node.js to current process PATH."""
    nvm_dir = _resolve_nvm_directory()

    if not nvm_dir.exists():
        return

    versions_dir = nvm_dir / "versions" / "node"

    if not versions_dir.exists():
        return

    # Find latest installed version
    installed = sorted(versions_dir.iterdir(), reverse=True)

    if not installed:
        return

    latest_bin = installed[0] / "bin"

    if latest_bin.exists():
        current = os.environ.get("PATH", "")
        os.environ["PATH"] = f"{latest_bin}:{current}"


def _check_node_available() -> Optional[str]:
    """
    Check if node command is available.

    Returns:
        Version string if available, None otherwise
    """
    try:
        result = _execute_cmd(["node", "--version"])
        if result.returncode == 0:
            return result.stdout.strip()
    except (subprocess.TimeoutExpired, FileNotFoundError):
        pass

    # Try with nvm sourced
    nvm_script = _resolve_nvm_script()
    if nvm_script.exists():
        try:
            result = _source_nvm_and_run("node --version")
            if result.returncode == 0:
                return result.stdout.strip()
            if result.stderr:
                _log.debug(f"node check via nvm failed: {result.stderr.strip()}")
        except subprocess.TimeoutExpired:
            pass

    return None


def _check_npm_available() -> Optional[str]:
    """
    Check if npm command is available.

    Returns:
        Version string if available, None otherwise
    """
    try:
        if _is_windows():
            result = _execute_cmd(["npm", "--version"], shell=True)
        else:
            result = _execute_cmd(["npm", "--version"])

        if result.returncode == 0:
            return result.stdout.strip()
    except (subprocess.TimeoutExpired, FileNotFoundError):
        pass

    # Try with nvm sourced (Unix only)
    if not _is_windows():
        nvm_script = _resolve_nvm_script()
        if nvm_script.exists():
            try:
                result = _source_nvm_and_run("npm --version")
                if result.returncode == 0:
                    return result.stdout.strip()
                if result.stderr:
                    _log.debug(f"npm check via nvm failed: {result.stderr.strip()}")
            except subprocess.TimeoutExpired:
                pass

    return None


def _attempt_auto_install() -> Tuple[bool, str]:
    """
    Attempt automatic nvm and Node.js installation.

    Returns:
        (success, message) tuple
    """
    _log.info("Node.js not found. Attempting automatic installation...")

    # Step 1: Ensure nvm is installed
    if not check_nvm_installed():
        _log.info("nvm not found. Installing nvm first...")
        if not install_nvm():
            return (
                False,
                "nvm installation failed. Please install Node.js manually: https://nodejs.org/",
            )

    # Step 2: Install Node.js via nvm
    if not install_node_with_nvm():
        return (
            False,
            "Node.js installation failed. Please install manually: https://nodejs.org/",
        )

    # Step 3: Verify installation
    node_ver = _check_node_available()
    if not node_ver:
        nvm_script = _resolve_nvm_script()
        return (
            False,
            f"Node.js installed but not accessible. Restart terminal or source {nvm_script}",
        )

    npm_ver = _check_npm_available()
    if not npm_ver:
        return (
            False,
            "Node.js installed but npm not accessible. Please verify installation.",
        )

    return (True, f"Node.js {node_ver}, npm {npm_ver}")


def check_node_npm() -> Tuple[bool, str]:
    """
    Verify Node.js and npm availability, installing if needed.

    This function checks if Node.js and npm are available in the system.
    If not found, it attempts automatic installation via nvm.

    Returns:
        Tuple of (is_available, message)
        - is_available: True if both node and npm are functional
        - message: Version info on success, error description on failure
    """
    try:
        # Quick check: node available?
        node_ver = _check_node_available()

        if not node_ver:
            # Not found - try auto-install
            return _attempt_auto_install()

        _log.debug(f"Node.js version: {node_ver}")

        # Check npm
        npm_ver = _check_npm_available()

        if not npm_ver:
            return (False, "npm not found or not accessible")

        _log.debug(f"npm version: {npm_ver}")

        return (True, f"Node.js {node_ver}, npm {npm_ver}")

    except subprocess.TimeoutExpired:
        return (False, "Timeout checking Node.js/npm")

    except FileNotFoundError:
        # Explicit FileNotFoundError - attempt install
        return _attempt_auto_install()

    except Exception as err:
        return (False, f"Error checking Node.js/npm: {err}")
