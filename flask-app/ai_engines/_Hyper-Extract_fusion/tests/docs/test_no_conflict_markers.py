"""Regression: published docs must not contain leftover git conflict markers."""

from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
DOCS_ROOT = REPO_ROOT / "docs"


def test_docs_have_no_git_conflict_markers():
    offenders: list[str] = []
    for path in sorted(DOCS_ROOT.rglob("*.md")):
        text = path.read_text(encoding="utf-8")
        for lineno, line in enumerate(text.splitlines(), start=1):
            if line.startswith("<<<<<<<") or line.startswith(">>>>>>>"):
                offenders.append(f"{path.relative_to(REPO_ROOT)}:{lineno}:{line}")
            elif line == "=======":
                offenders.append(f"{path.relative_to(REPO_ROOT)}:{lineno}:{line}")
    assert not offenders, "leftover git conflict markers:\n" + "\n".join(offenders)
