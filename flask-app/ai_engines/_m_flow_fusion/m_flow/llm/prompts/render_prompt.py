"""
Jinja2 prompt template renderer.

Renders prompt templates with context data.
"""

from __future__ import annotations

from jinja2 import Environment, FileSystemLoader, select_autoescape

from m_flow.root_dir import get_absolute_path

_DEFAULT_DIR = "./llm/prompts"


def render_prompt(
    filename: str,
    context: dict,
    base_directory: str | None = None,
) -> str:
    """
    Render Jinja2 template with context.

    Args:
        filename: Template filename.
        context: Variables for template rendering.
        base_directory: Template directory (defaults to llm/prompts).

    Returns:
        Rendered template string.
    """
    base = base_directory or get_absolute_path(_DEFAULT_DIR)

    env = Environment(
        loader=FileSystemLoader(base),
        autoescape=select_autoescape(["html", "xml", "txt"]),
    )

    template = env.get_template(filename)
    return template.render(context)
