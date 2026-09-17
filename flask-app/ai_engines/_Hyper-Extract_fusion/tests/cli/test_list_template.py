"""CLI tests for `he list template` language / method inclusion."""

from typer.testing import CliRunner

from hyperextract.cli.cli import app

runner = CliRunner()


def test_list_template_lang_zh_includes_methods():
    result = runner.invoke(app, ["list", "template", "--lang", "zh"])
    assert result.exit_code == 0, result.output
    assert "method/" in result.output
    assert "chunk_rag" in result.output


def test_list_template_lang_zh_no_methods_hides_methods():
    result = runner.invoke(app, ["list", "template", "--lang", "zh", "--no-methods"])
    assert result.exit_code == 0, result.output
    assert "method/" not in result.output
    assert "chunk_rag" not in result.output
