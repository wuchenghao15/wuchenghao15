<!--
⚠️  READ BEFORE OPENING ⚠️

PRs without a linked, maintainer-approved issue WILL be closed.

Workflow:
1. Open an issue → describe the problem/feature
2. Wait for the `approved` label from a maintainer
3. Then open this PR linking that issue

Only exception: typo/broken-link fixes under 5 changed lines.

See CONTRIBUTING.md for full details.
-->

## Linked Issue

**Issue:** #<!-- Replace with the approved issue number -->

## What Changed and Why

<!-- 2-4 sentences. Explain the problem and how your change solves it. -->
<!-- Don't list files. Explain intent. -->

## How to Test

<!-- Exact steps a reviewer can follow to verify. -->

```bash
# Example:
pytest tests/core/test_parser_php.py -v
```

## Checklist

- [ ] This PR is linked to a maintainer-approved issue (or is a trivial typo/link fix under 5 lines)
- [ ] I have read CONTRIBUTING.md
- [ ] One logical change only — no bundled/unrelated work
- [ ] Tests added or updated for this change
- [ ] `pytest` passes locally
- [ ] `ruff check src/ tests/` passes
- [ ] I can explain every line of this PR when asked
- [ ] No generated project-config files (CLAUDE.md, .cursorrules, etc.)
