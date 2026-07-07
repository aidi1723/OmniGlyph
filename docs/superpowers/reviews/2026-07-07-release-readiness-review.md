# Release Readiness Review - 2026-07-07

## Scope

Reviewed the July 7 readiness hardening changes before pushing to the remote repository.
The local branch history was unrelated to `origin/main`, so the final integration was applied on top of the remote v0.8 `main` baseline instead of force-pushing the older local `main`.

- CLI additions in `src/omniglyph/cli.py` for v0.8-missing local evidence commands.
- CLI regression coverage in `tests/test_cli_product_tools.py`.
- Release/readiness records in `docs/quickstart.md` and this review note.

## Findings

No blocking issues found.

## Review Notes

- Kept the remote v0.8 `enforce-output` and Policy Pack `enforce-intent` CLI behavior intact.
- Added local CLI wrappers for `validate-output`, `scan-language-input`, `scan-output-dlp`, and `audit-explain`.
- The new CLI commands call existing runtime helpers rather than duplicating guardrail, DLP, or audit logic.
- CLI tests exercise output validation, output enforcement, language-security scanning, DLP redaction, Policy Pack intent handling, and audit explanation output.
- v0.7 artifact notes remain in the local pre-integration record, but the remote-bound branch keeps v0.8 release/readiness documentation as the source of truth.

## Verification Evidence

- Focused CLI/Policy Pack tests: `17 passed`.
- Full project pytest: `189 passed`.
- `scripts/release_check.sh`: passed on the remote-based v0.8 branch.
- Release check covered Ruff, mypy, whitespace/conflict-marker check, MCP smoke, package build, Twine metadata check, artifact audit, wheel smoke, and demo output.

## Remaining Release Gates

- Final PyPI upload requires explicit approval.
- MCP Registry package metadata submission requires explicit approval.
- Do not force-push over `origin/main`; only push a fast-forward commit based on the remote v0.8 baseline.
