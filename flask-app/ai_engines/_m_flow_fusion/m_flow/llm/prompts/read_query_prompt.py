"""
Prompt file reader.

Loads prompt templates from the filesystem.
"""

from __future__ import annotations

from os import path

from m_flow.root_dir import get_absolute_path
from m_flow.shared.logging_utils import ERROR, get_logger

_log = get_logger(level=ERROR)
_DEFAULT_DIR = "./llm/prompts"


def read_query_prompt(
    prompt_file_name: str,
    base_directory: str | None = None,
) -> str | None:
    """
    Read prompt content from file.

    Args:
        prompt_file_name: Prompt filename.
        base_directory: Directory path (defaults to llm/prompts).

    Returns:
        File content or None on error.
    """
    base = base_directory or get_absolute_path(_DEFAULT_DIR)
    target = path.join(base, prompt_file_name)

    try:
        with open(target, "r", encoding="utf-8") as f:
            return f.read()
    except FileNotFoundError:
        _log.error(f"Prompt not found: {target}")
        return None
    except Exception as e:
        _log.error(f"Failed to read prompt: {e}")
        return None
