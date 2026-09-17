# Contributing to Axon

Thanks for your interest in contributing. This guide covers the workflow we expect from all contributors.

## Golden Rule: Issue First, Code Second

> **Do not write code until a maintainer has approved your issue.**
>
> PRs without a linked, approved issue will be closed immediately — no exceptions for size or quality.

### The Contribution Workflow

```
1. Open an issue          →  Describe the problem/feature and your proposed approach
2. Discussion             →  Maintainer may ask questions or suggest a different direction
3. Issue gets `approved`  →  You now have the green light to write code
4. Open a PR              →  Reference the issue with "Closes #<number>"
5. Review                 →  Expect feedback, iterate
6. Merge                  →  🎉
```

**Why this matters:** We've had contributors spend days building features we didn't want, or submitting 13 PRs in a row without ever talking to us. The issue step takes 5 minutes and saves everyone time.

**Only exception:** Typo fixes, broken links, and documentation corrections under 5 changed lines.

## What We're Looking For

- Bug fixes with a clear reproduction path
- Performance improvements backed by benchmarks
- New language parser support (discuss scope in an issue first)
- Test coverage for uncovered edge cases
- Documentation improvements that fix actual confusion

## What We'll Close Without Review

- **PRs without a linked approved issue** — this is the #1 reason PRs get closed
- PRs that bundle unrelated changes to inflate diff size
- Stacked PR chains where each PR is a superset of the previous one (open one PR, not thirteen)
- PRs that add project-config files (CLAUDE.md, .cursorrules, etc.) — these are developer-local
- Bulk AI-generated submissions from contributors with zero prior engagement
- PRs where the contributor cannot explain the changes when asked

## Development Setup

```bash
# Clone and install
git clone https://github.com/harshkedia177/axon.git
cd axon
pip install -e ".[dev]"

# Run tests
pytest

# Lint
ruff check src/ tests/
ruff format --check src/ tests/
```

Requires Python 3.11+.

## PR Requirements

1. **One logical change per PR.** Don't mix a bug fix with a new feature with test refactoring.

2. **Tests are mandatory.** Every bug fix needs a regression test. Every new feature needs coverage. Run the full suite before opening:
   ```bash
   pytest --tb=short
   ```

3. **Pass linting.** We use ruff. Fix all issues before opening:
   ```bash
   ruff check src/ tests/ --fix
   ruff format src/ tests/
   ```

4. **Write a real PR description.** Use the PR template. Explain *what* changed and *why*. Link the issue.

5. **Keep diffs focused.** Don't reformat files you didn't change. Don't add docstrings to unrelated functions. Don't rename variables in code you didn't touch.

## On AI-Assisted Contributions

We don't ban AI tools — but we hold AI-assisted PRs to a higher bar, not a lower one.

- You must understand every line of code in your PR. We will ask questions.
- "Claude/Copilot wrote it" is not an answer to "why did you choose this approach?"
- AI-generated commit messages like "Generated with Claude Code" are a signal that the contributor didn't review their own work. Clean up your commits.
- Bulk-generating PRs against a repo you've never interacted with is not contributing — it's noise.

## Code Style

- Follow existing patterns in the codebase. If parsers use `_extract_*` methods, yours should too.
- No unnecessary abstractions. Three similar lines > a premature helper function.
- Type hints on public APIs. Skip them on obvious locals.
- Comments only where the logic isn't self-evident.

## Adding a New Language Parser

This is a common contribution. The expected process:

1. **Open an issue** with the language name and scope (what constructs you'll extract)
2. Create `src/axon/core/ingestion/languages/<lang>.py` following the pattern in `python.py` or `typescript.py`
3. Register the language in `src/axon/core/ingestion/languages/__init__.py`
4. Add tree-sitter grammar dependency to `pyproject.toml`
5. Write tests in `tests/core/test_parser_<lang>.py`
6. Verify integration: `axon analyze <test-repo>` should index the new language

## Commit Messages

```
<type>: <short description>

<optional body explaining why>
```

Types: `fix`, `feat`, `test`, `refactor`, `docs`, `chore`

Keep the subject under 72 characters. Explain the "why" in the body, not the "what."

## Review Process

- Maintainers will review within a few days
- Expect questions and change requests — this is normal
- If your PR goes stale (no response for 2 weeks), it may be closed
- Engage with feedback. PRs where the contributor disappears get closed.

## License

By contributing, you agree that your contributions are licensed under the MIT License.
