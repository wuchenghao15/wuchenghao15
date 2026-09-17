"""
NPM command execution utilities.

Cross-platform npm runner with nvm support for Unix systems.
"""

from __future__ import annotations

import platform
import subprocess
from pathlib import Path
from typing import List

from m_flow.shared.logging_utils import get_logger
from .node_setup import get_nvm_sh_path

_log = get_logger()


def run_npm_command(
    cmd: List[str],
    cwd: Path,
    timeout: int = 300,
) -> subprocess.CompletedProcess:
    """
    Execute npm command with platform-specific handling.

    On Windows: Runs with shell=True.
    On Unix: Tries direct execution first, falls back to nvm if available.

    Args:
        cmd: Command parts (e.g., ["npm", "install"]).
        cwd: Working directory.
        timeout: Max execution time in seconds.

    Returns:
        CompletedProcess with stdout/stderr.
    """
    if platform.system() == "Windows":
        return _run_windows(cmd, cwd, timeout)

    return _run_unix(cmd, cwd, timeout)


def _run_windows(
    cmd: List[str],
    cwd: Path,
    timeout: int,
) -> subprocess.CompletedProcess:
    """Windows npm execution with shell."""
    return subprocess.run(
        cmd,
        cwd=cwd,
        capture_output=True,
        text=True,
        timeout=timeout,
        shell=True,
    )


def _run_unix(
    cmd: List[str],
    cwd: Path,
    timeout: int,
) -> subprocess.CompletedProcess:
    """Unix npm execution with nvm fallback."""
    # Try direct execution first
    result = subprocess.run(
        cmd,
        cwd=cwd,
        capture_output=True,
        text=True,
        timeout=timeout,
    )

    if result.returncode == 0:
        return result

    # Try with nvm sourced
    nvm_path = get_nvm_sh_path()
    if not nvm_path.exists():
        return result

    cmd_str = " ".join(cmd)
    nvm_cmd = f"source {nvm_path} && {cmd_str}"

    result = subprocess.run(
        ["bash", "-c", nvm_cmd],
        cwd=cwd,
        capture_output=True,
        text=True,
        timeout=timeout,
    )

    if result.returncode != 0 and result.stderr:
        _log.debug(f"npm via nvm failed: {result.stderr.strip()}")

    return result
