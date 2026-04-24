# OmniGlyph Code Linter

OmniGlyph Code Linter is the first dogfooding use case for OmniGlyph in developer workflows.

It does not replace syntax linters such as Ruff, ESLint, or ShellCheck. It scans the physical Unicode layer of source code so coding agents can see symbols that tokenizers, reviewers, and compilers may obscure.

## What It Detects

- invisible format characters such as `U+200B ZERO WIDTH SPACE`
- Bidi controls such as `U+202E RIGHT-TO-LEFT OVERRIDE`
- cross-script homoglyph risks such as `U+0430 CYRILLIC SMALL LETTER A`
- unexpected control characters in source text

## Generate a Poisoned Sample

```bash
python examples/poisoned-code/generate_poison.py
```

This creates `examples/poisoned-code/test_bug.py` with a Cyrillic `а`, a zero-width space, and a Bidi override.

## Scan with CLI

```bash
omniglyph scan-code examples/poisoned-code/test_bug.py
```

JSON output:

```bash
omniglyph scan-code examples/poisoned-code/test_bug.py --format json
```

Fail CI or pre-commit on warning:

```bash
omniglyph scan-code src/ --fail-on warning
```

## Use from MCP

Agents can call `scan_code_symbols` before editing or reviewing source code:

```json
{
  "text": "vаlue = 1\n",
  "source_name": "agent.py"
}
```

The tool returns a structured report with line, column, Unicode code point, official Unicode name, category, and rule ID.

## Agent Rule

Before an agent explains a mysterious compiler error, failed patch, copied code snippet, or suspicious diff, run OmniGlyph Code Linter. Treat findings as physical source facts, not model interpretations.
