# Good First Issues

These are small, useful tasks for new contributors.

## Documentation

- Add a Claude Desktop screenshot-free walkthrough using `pip install omniglyph==0.3.2b0`.
- Add a `pipx install omniglyph` verification note once tested across macOS/Linux.
- Add more `scan_code_symbols` examples for JavaScript, Bash, and Markdown.
- Add a short FAQ explaining why OmniGlyph returns `null` instead of guessing.

## Tests

- Add tests for fullwidth Latin characters in `scan-code`.
- Add tests for variation selectors.
- Add tests for mixed Greek/Latin homoglyph risks.
- Add CLI tests for scanning a directory with multiple files.

## Code

- Add `omniglyph --version` output.
- Add `scripts/mcp_smoke_test.sh` for local and CI use.
- Add `--include` / `--exclude` patterns to `scan-code`.
- Add compact JSON output for `scan-code`.

## Data Sources

- Research Unicode `confusables.txt` ingestion and licensing notes.
- Document CLDR ingestion candidates.
- Add a small public-domain sample domain pack for OCR cleanup.

## Rules

Good first issues should stay deterministic and source-backed. Do not add generated definitions as canonical data.
