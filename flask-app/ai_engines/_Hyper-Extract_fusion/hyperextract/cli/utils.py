"""Common utilities for Hyper-Extract CLI."""

import sys
from pathlib import Path

import typer
from rich.console import Console

from hyperextract.utils.readers import (
    INGESTABLE_SUFFIXES,
    TEXT_SUFFIXES,
    markitdown_available,
    read_document,
)

from .config import ConfigManager

console = Console()

_SKIPPED_FILE_PREVIEW_LIMIT = 10
_DS_STORE = ".DS_Store"

LOGO = r"""
                                                                                     
▄▄▄   ▄▄▄                                ▄▄▄▄▄▄▄                                     
███   ███                               ███▀▀▀▀▀        ██                      ██   
█████████ ██ ██ ████▄ ▄█▀█▄ ████▄       ███▄▄    ██ ██ ▀██▀▀ ████▄  ▀▀█▄ ▄████ ▀██▀▀ 
███▀▀▀███ ██▄██ ██ ██ ██▄█▀ ██ ▀▀ ▀▀▀▀▀ ███       ███   ██   ██ ▀▀ ▄█▀██ ██     ██   
███   ███  ▀██▀ ████▀ ▀█▄▄▄ ██          ▀███████ ██ ██  ██   ██    ▀█▄██ ▀████  ██   
            ██  ██                                                                   
          ▀▀▀   ▀▀                                                                   
"""


def _is_supported_text_suffix(path: Path) -> bool:
    """Return True when the CLI can read this file in the current environment.

    Plain text (``.txt``/``.md``) is always supported; document formats are
    supported when the optional markitdown backend is installed.
    """
    suffix = path.suffix.lower()
    if suffix in TEXT_SUFFIXES:
        return True
    return suffix in INGESTABLE_SUFFIXES and markitdown_available()


def require_supported_text_input(input_path: str) -> None:
    """Reject a single-file input the CLI cannot read.

    Stdin (``-``) is not suffix-checked. Directories are left to
    :func:`collect_directory_text_inputs`.
    """
    if input_path == "-":
        return
    path = Path(input_path)
    if path.is_dir():
        return
    if _is_supported_text_suffix(path):
        return
    suffix = path.suffix.lower()
    console.print(
        f"[red]Error:[/red] Unsupported input type: {path.name or input_path}"
    )
    if suffix in INGESTABLE_SUFFIXES:
        console.print(
            f"{INGESTABLE_SUFFIXES[suffix]} input is supported with the "
            "optional ingest extra: "
            'pip install "hyperextract\\[ingest]"'
        )
    else:
        console.print(
            "Supported inputs: .txt/.md always; PDF/DOCX/PPTX/XLSX/HTML and "
            'more via pip install "hyperextract\\[ingest]".'
        )
    raise typer.Exit(1)


def collect_directory_text_inputs(directory: Path) -> list[Path]:
    """Return non-recursive readable files in ``directory``.

    Raises:
        typer.Exit: If the directory contains no readable files.

    Other regular files at the same level produce a warning (up to 10 names
    plus a remaining count) and are skipped. ``.DS_Store`` is ignored.
    """
    text_files = sorted(
        (
            path
            for path in directory.glob("*")
            if path.is_file() and _is_supported_text_suffix(path)
        ),
        key=lambda path: path.name.lower(),
    )
    if not text_files:
        skipped_ingestable = [
            path
            for path in directory.iterdir()
            if path.is_file()
            and path.suffix.lower() in INGESTABLE_SUFFIXES
            and not markitdown_available()
        ]
        if skipped_ingestable:
            console.print(
                "[red]Error:[/red] No readable files found in "
                f"{directory}. Document files (e.g. "
                f"{skipped_ingestable[0].name}) need the ingest extra: "
                'pip install "hyperextract\\[ingest]"'
            )
        else:
            console.print(
                f"[red]Error:[/red] No .txt or .md files found in {directory}"
            )
        raise typer.Exit(1)

    skipped = sorted(
        (
            path
            for path in directory.iterdir()
            if path.is_file()
            and path.name != _DS_STORE
            and not _is_supported_text_suffix(path)
        ),
        key=lambda path: path.name.lower(),
    )
    if skipped:
        preview = skipped[:_SKIPPED_FILE_PREVIEW_LIMIT]
        listed = ", ".join(path.name for path in preview)
        remaining = len(skipped) - len(preview)
        extra = f" (+{remaining} more)" if remaining else ""
        hint = (
            " Install the ingest extra for documents: "
            'pip install "hyperextract\\[ingest]"'
            if any(p.suffix.lower() in INGESTABLE_SUFFIXES for p in skipped)
            and not markitdown_available()
            else ""
        )
        console.print(
            f"[yellow]Warning:[/yellow] skipped unsupported file(s): "
            f"{listed}{extra}.{hint}"
        )

    return text_files


def read_input(input_path: str) -> str:
    """Read input from file or stdin (document formats converted to text)."""
    if input_path == "-":
        return sys.stdin.read()
    path = Path(input_path)
    if not path.exists():
        raise FileNotFoundError(f"Input file not found: {input_path}")
    from hyperextract.utils.readers import ReaderError

    try:
        return read_document(path)
    except ReaderError as e:
        console.print(f"[red]Error:[/red] {e}")
        raise typer.Exit(1)


def validate_ka_path(ka_path: str) -> Path:
    """Validate Knowledge Abstract path.

    Args:
        ka_path: Knowledge Abstract directory path

    Returns:
        Path object

    Raises:
        typer.Exit: If path is invalid
    """
    path = Path(ka_path)

    if not path.exists():
        console.print(f"[red]Error:[/red] Knowledge Abstract not found: {ka_path}")
        raise typer.Exit(1)

    if not path.is_dir():
        console.print(f"[red]Error:[/red] Not a directory: {ka_path}")
        raise typer.Exit(1)

    return path


def validate_ka_with_data(ka_path: str) -> Path:
    """Validate Knowledge Abstract path with data.json.

    Args:
        ka_path: Knowledge Abstract directory path

    Returns:
        Path object

    Raises:
        typer.Exit: If path is invalid or missing data.json
    """
    path = validate_ka_path(ka_path)

    data_file = path / "data.json"
    if not data_file.exists():
        console.print(
            f"[red]Error:[/red] Not a valid Knowledge Abstract: {ka_path} (no data.json)"
        )
        raise typer.Exit(1)

    return path


def validate_ka_with_index(ka_path: str) -> Path:
    """Validate Knowledge Abstract path with index.

    Args:
        ka_path: Knowledge Abstract directory path

    Returns:
        Path object

    Raises:
        typer.Exit: If path is invalid or missing index
    """
    path = validate_ka_path(ka_path)

    index_dir = path / "index"
    if not index_dir.exists() or not any(index_dir.iterdir()):
        console.print(
            f"[red]Error:[/red] Index not found. Please run 'he build-index {ka_path}' first."
        )
        raise typer.Exit(1)

    return path


def get_template_from_ka(ka_path: Path) -> tuple[str, str]:
    """Get template path for Knowledge Abstract.

    Load priority:
    1. If template is a registered method (e.g., "method/chunk_rag") -> use it
    2. If template is in presets (e.g., "general/graph") -> use preset name
    3. If template not in presets -> try to find {template}.yaml in KA directory

    Raises:
        ValueError: If template not found and no local yaml file exists
    """
    from hyperextract.utils.template_engine import Gallery

    from .config import load_ka_metadata

    metadata = load_ka_metadata(ka_path)
    if metadata is None:
        raise ValueError(f"No metadata.json found in Knowledge Abstract: {ka_path}")

    template = metadata.get("template")
    lang = metadata.get("lang")

    if template:
        if template.startswith("method/"):
            # Method templates are code-registered, not gallery YAML files.
            from hyperextract.methods.registry import get_method

            if get_method(template[len("method/") :]) is not None:
                return template, lang
        elif Gallery.get(template) is not None:
            return template, lang
        else:
            local_yaml = ka_path / f"{template}.yaml"
            if local_yaml.exists():
                return str(local_yaml), lang
            raise ValueError(
                f"Template '{template}' not found in presets and local file "
                f"'{local_yaml}' does not exist."
            )

    raise ValueError("No template specified in metadata.json")


def validate_config() -> "ConfigManager":
    """Validate configuration.

    Returns:
        ConfigManager instance

    Raises:
        typer.Exit: If configuration is invalid
    """

    config = ConfigManager()
    valid, msg = config.validate()

    if not valid:
        console.print(f"[red]Error:[/red] {msg}")
        raise typer.Exit(1)

    return config
