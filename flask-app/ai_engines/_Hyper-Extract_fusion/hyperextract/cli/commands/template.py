"""Template authoring commands for Hyper-Extract CLI."""

import json
from pathlib import Path

import typer
from rich.console import Console

from hyperextract.utils.logging import get_logger
from hyperextract.utils.template_engine import (
    ValidationResult,
    validate_template,
    validate_template_dir,
)
from hyperextract.utils.template_engine.validator import iter_template_files

logger = get_logger("he.template")
console = Console()

app = typer.Typer(
    name="template",
    help="Template authoring tools",
    no_args_is_help=True,
)


def _print_human(result: ValidationResult) -> None:
    if result.ok and not result.diagnostics:
        console.print(f"[bold green]OK[/bold green]  {result.file}")
        return
    if result.ok:
        console.print(
            f"[bold yellow]OK[/bold yellow]  {result.file}  "
            f"({result.warning_count} warning"
            f"{'s' if result.warning_count != 1 else ''})"
        )
    else:
        console.print(
            f"[bold red]FAILED[/bold red]  {result.file}  "
            f"({result.error_count} error"
            f"{'s' if result.error_count != 1 else ''}, "
            f"{result.warning_count} warning"
            f"{'s' if result.warning_count != 1 else ''})"
        )
    for diagnostic in result.diagnostics:
        color = "red" if diagnostic.severity == "error" else "yellow"
        location = diagnostic.path or "-"
        console.print(
            f"  [{color}]{diagnostic.severity:7}[/{color}] "
            f"{diagnostic.code}  {location}  {diagnostic.message}"
        )


def _emit_json(payload: dict) -> None:
    print(json.dumps(payload, ensure_ascii=False, indent=2))


@app.command("validate")
def validate(
    path: str = typer.Argument(
        ...,
        help="Template YAML file, or a directory when using --all",
    ),
    json_output: bool = typer.Option(
        False,
        "--json",
        help="Print machine-readable JSON diagnostics",
    ),
    all_files: bool = typer.Option(
        False,
        "--all",
        help="Validate every YAML file under a directory",
    ),
):
    """Validate a template YAML file (or a directory of templates)."""
    logger.info(
        "command=template-validate path=%s json=%s all=%s",
        path,
        json_output,
        all_files,
    )
    target = Path(path)

    if not target.exists():
        result = validate_template(target)
        if json_output:
            _emit_json(result.to_dict())
        else:
            console.print(f"[red]Error:[/red] {result.diagnostics[0].message}")
        raise typer.Exit(1)

    if target.is_dir() and not all_files:
        console.print(
            "[red]Error:[/red] PATH is a directory. Re-run with --all to validate "
            "every YAML file under it."
        )
        raise typer.Exit(1)

    if target.is_file() and all_files:
        console.print(
            "[red]Error:[/red] --all is for directories. Pass a directory path."
        )
        raise typer.Exit(1)

    if target.is_dir():
        files = iter_template_files(target)
        if not files:
            console.print(f"[red]Error:[/red] No YAML templates found in {target}")
            raise typer.Exit(1)
        results = validate_template_dir(target)
        ok = all(item.ok for item in results)
        if json_output:
            _emit_json(
                {
                    "results": [item.to_dict() for item in results],
                    "ok": ok,
                }
            )
        else:
            for item in results:
                _print_human(item)
            errors = sum(item.error_count for item in results)
            warnings = sum(item.warning_count for item in results)
            console.print()
            console.print(
                f"[dim]Validated {len(results)} template(s): "
                f"{errors} error(s), {warnings} warning(s)[/dim]"
            )
        raise typer.Exit(0 if ok else 1)

    result = validate_template(target)
    if json_output:
        _emit_json(result.to_dict())
    else:
        _print_human(result)
    raise typer.Exit(0 if result.ok else 1)
