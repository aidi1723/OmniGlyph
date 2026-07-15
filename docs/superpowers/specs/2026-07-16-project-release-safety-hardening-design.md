# OmniGlyph Project Release-Safety Hardening Design

## Status

- Date: 2026-07-16
- Scope: release-safe correctness, integrity, and boundary hardening
- Target: current `0.8.0b0` source candidate
- Compatibility: preserve public API routes, CLI commands, MCP tool names, database tables, and product positioning

## Context

The current source candidate passes its existing release gate: 189 tests, Ruff,
mypy, privacy scanning, package build, metadata checks, artifact audit, clean-wheel
smoke checks, MCP smoke checks, and the cross-border demo. The review nevertheless
identified correctness and safety edges that are not represented in the current
test suite. This batch closes those gaps without adding product features or
expanding the project's operational authority.

## Goals

1. Make repeated and differently ordered source ingestion deterministic.
2. Make namespace replacement atomic so a failed import cannot erase known-good data.
3. Prevent failed or unverified downloads from replacing an existing source artifact.
4. Return stable JSON-RPC errors for malformed MCP input.
5. Reject ambiguous duplicate intent definitions and type-confused enum values.
6. Produce stable DLP redaction for overlapping sensitive matches.
7. Record complete verification evidence and remaining limitations in a closeout report.

## Non-Goals

- No new API routes, CLI commands, MCP tools, authentication layer, or external integration.
- No database table redesign or destructive migration.
- No rewrite of the Unicode linter's detection policy.
- No package publication, registry update, release tag, or production deployment.
- No broad refactor whose value is unrelated to the confirmed findings.

## Design

### 1. Repository Ingestion Consistency

Glyph properties will use deterministic identifiers derived from their complete
source-backed identity. This makes exact duplicate property ingestion idempotent
even when nullable fields would otherwise bypass SQLite uniqueness semantics.

Unicode glyph upserts will fill missing canonical metadata, especially the Unicode
name, without overwriting an existing non-null value with a null value. This keeps
the result stable whether UnicodeData or Unihan is ingested first.

Lexical namespace replacement will execute deletion, source snapshot registration,
entry insertion, and alias insertion within one SQLite transaction. Any exception
will roll the entire replacement back. Existing non-replacement import behavior
will remain unchanged.

### 2. Source Download Integrity

Remote content will be written to a temporary file in the destination directory.
The temporary artifact will be closed and SHA-256 validated before an atomic
filesystem replacement. On network, write, or integrity failure, the temporary
file will be removed and an existing destination will remain untouched.

The function's return type and successful-path behavior remain unchanged.

### 3. MCP JSON-RPC Boundary

The stdio boundary will distinguish parse errors from invalid request envelopes.
Non-object JSON, an unsupported JSON-RPC version, a missing or invalid method, and
invalid `params` or `arguments` containers will return protocol errors rather than
uncaught attribute errors. Defensive internal errors will preserve the request ID
when it can be recovered and will not include raw exception details in the client
message.

Valid MCP requests and the existing seventeen-tool surface remain unchanged.

### 4. Policy and Parameter Validation

Policy Pack validation will reject duplicate non-empty `intent_id` values because
first-match evaluation would otherwise make the effective policy dependent on row
order. The validation report will identify the duplicate row and intent ID.

Enum validation will compare JSON primitive types as well as values, preventing
Python's `True == 1` behavior from satisfying a numeric enum. Existing supported
schema keywords and the documented fail-safe intent decision behavior remain intact.

### 5. DLP Redaction Stability

Redaction spans will be sorted and coalesced before output construction. Overlapping
or adjacent findings will produce one `[REDACTED]` marker for the combined sensitive
range. Finding offsets and hashes will continue to refer to the original input.

### 6. Documentation and Closeout

A dated closeout report will summarize:

- baseline state and review scope;
- confirmed findings and their severity;
- code and test changes;
- release-gate evidence;
- compatibility assessment;
- unresolved risks and deferred work;
- the publication boundary.

Existing product status and maintenance indexes will be updated only where needed
to link the new report and avoid stale verification counts.

## Error Handling

- Repository replacement failures roll back all replacement work.
- Download failures remove only the temporary file and re-raise the original error.
- MCP malformed input receives JSON-RPC error objects and does not terminate the loop.
- Invalid Policy Packs remain load-blocked by validation-aware callers.
- Parameter validation remains deterministic and dependency-free.

## Test Strategy

Each behavioral fix starts with a focused failing regression test:

1. Repeated property ingestion produces one stored property.
2. Unihan-first then UnicodeData ingestion fills the Unicode name.
3. A forced namespace replacement failure preserves prior entries and source state.
4. Hash mismatch and interrupted download preserve an existing destination.
5. Malformed JSON-RPC envelopes return the expected protocol errors and the loop continues.
6. Duplicate Policy Pack intent IDs fail validation.
7. Boolean values do not satisfy numeric enum members.
8. Overlapping and adjacent DLP findings produce one stable redaction marker.

After focused tests pass, run the full release gate and privacy scan. Compare the
working-tree diff to ensure only source, focused tests, and closeout documentation
changed.

## Acceptance Criteria

- All eight regression cases pass.
- Existing tests continue to pass.
- Ruff and mypy pass.
- Privacy scan passes.
- MCP smoke reports the same seventeen tools.
- Fresh `0.8.0b0` wheel and sdist pass metadata and artifact audits.
- Clean-wheel CLI/MCP smoke and the cross-border demo pass.
- The final report records evidence, compatibility, and remaining risks.
