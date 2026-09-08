# Project Review: OmniGlyph and LogosGate

Review date: 2026-09-08. Source reviewed: local `main` at `6088546`, package version `0.8.0b0`.

## Findings

Three issues deserve immediate attention: invalid replacement imports can delete existing vocabulary, Unicode range records are not expanded, and the default Docker configuration exposes the unauthenticated API beyond localhost. Additional reproduced defects affect policy interpretation, DLP, and error handling. The existing tests and package checks pass, but do not cover these cases.

Severity reflects practical impact and prerequisites. P1 means high priority before affected production use; P2 means a concrete defect or verification gap to address in the next hardening work; P3 means maintenance debt. Configuration and draft-design findings are explicitly distinguished from reproduced runtime defects.

### R1. P1: Invalid replacement packs can erase existing vocabulary

References: [cli.py](src/omniglyph/cli.py), line 92; [domain_pack.py](src/omniglyph/domain_pack.py), line 33; [repository.py](src/omniglyph/repository.py), line 165.

`ingest_domain_pack` loads entries without running pack validation. The parser silently skips rows lacking mandatory fields, and namespace replacement deletes the existing entries before inserting the resulting list. A malformed pack can therefore become a successful empty replacement.

Reproduction: seed an approved `FOB` entry, then replace its namespace with a pack containing a row without `canonical_id`. The validator reports `fail`, but import returns `0` successfully and both the old entry and its alias disappear. The transaction commits because no exception occurs.

Recommendation: validate the replacement snapshot before any deletion, and make accidental empty replacements distinguishable from intentional clearing. Add a regression proving that rejected replacements preserve the previous namespace.

### R2. P1: UnicodeData range records lose most represented characters

Reference: [normalizer.py](src/omniglyph/normalizer.py), line 27.

The parser treats every UnicodeData row as one character. Upstream `First`/`Last` rows encode entire ranges, including CJK ideographs and Hangul syllables. The implementation imports only their endpoints and uses range-marker text as names.

Reproduction: the standard CJK `4E00..9FFF` and Hangul `AC00..D7A3` range rows produce 4 records instead of 32,164. U+94DD and U+AC01 are absent; U+4E00 is named `<CJK Ideograph, First>`. Unihan can backfill some Han nodes but does not repair this Unicode import or supply Hangul coverage. The test fixture uses individually expanded CJK rows, masking the upstream-format problem.

Recommendation: implement the documented range semantics, use appropriate source-backed naming rules, and test representative upstream range rows and resulting counts.

### R3. P1: Default Docker publishing exposes an unauthenticated private-data API

References: [docker-compose.yml](docker-compose.yml), line 5; [Dockerfile](Dockerfile), line 10; [api.py](src/omniglyph/api.py), line 104.

Compose publishes `8000:8000`, and Uvicorn listens on `0.0.0.0`. The API has no authentication and serves term details and namespace information. On a host reachable by other clients, the default deployment can expose imported private vocabulary. Exposure depends on host networking and firewall rules; no live exposure was attempted during this review.

Recommendation: bind the default host mapping to `127.0.0.1`. Document authenticated remote deployment as an explicit configuration with appropriate request limits.

### R4. P2: Chinese text can suppress supported DLP matches

Reference: [language_security.py](src/omniglyph/language_security.py), line 24.

ASCII credential patterns use Unicode-aware `\b` boundaries. Han characters are word characters under these regex semantics, so a supported key immediately after a Chinese label is missed.

Reproduction through the HTTP API: an artificial key after `Key: ` returns `block` and is redacted. The same key immediately after the Chinese word for key returns HTTP 200, `allow`, zero findings, and unchanged text. Equivalent Chinese-adjacent AWS access-key and email samples are also missed.

Recommendation: define boundaries appropriate to each credential format and add multilingual adjacency cases. This is a defect within advertised pattern coverage, independent of the documented limitation that DLP is incomplete.

### R5. P2: Duplicate CSV headers silently change policy decisions

Reference: [policy_pack.py](src/omniglyph/policy_pack.py), line 179.

Policy validation checks for missing columns and extra row values, but not duplicate column names. `csv.DictReader` discards an earlier value when a later column has the same name.

Reproduction: an `intents.csv` containing two `decision` columns, with `block` first and `allow` last, validates successfully and authorizes the intent. A malformed or misleading spreadsheet export can therefore disagree with the policy a reviewer thinks was approved.

Recommendation: reject duplicate header names before constructing row dictionaries, particularly for authorization fields.

### R6. P2: Child-file symlinks bypass configured pack-root containment

References: [policy_pack.py](src/omniglyph/policy_pack.py), line 141; [lexicon_pack.py](src/omniglyph/lexicon_pack.py), line 107.

Containment checks resolve the pack directory, but loaders subsequently follow `policy.json`, `intents.csv`, `pack.json`, and `terms.csv` without checking their resolved locations.

Reproduction: requesting an outside policy directly returns HTTP 403. A directory inside the allowed root containing child-file symlinks to that policy returns HTTP 200 and `allow`. Lexicon validation similarly accepts linked files outside its configured root.

This requires such symlinks to exist or to be creatable inside the allowed directory; it is not an arbitrary remote-write capability. Recommendation: enforce containment on every file actually opened and define the symlink policy explicitly.

### R7. P2: NaN satisfies bounded numeric intent parameters

Reference: [parameter_schema.py](src/omniglyph/parameter_schema.py), lines 204 and 238.

Schema bounds must be finite, but runtime numbers use a looser type check. Comparisons against NaN are false in both directions, so minimum and maximum checks report no violation.

Reproduction: for an amount bounded from 0 to 100, `101` returns `block / invalid_parameters`; `float("nan")` returns `allow / matched`. The MCP handler also allows a request decoded with Python's default permissive JSON parser containing NaN. Strict JSON clients cannot produce this literal, but direct Python callers and the current parser can.

Recommendation: reject non-finite runtime numeric values at the core boundary and reject nonstandard JSON constants at transport boundaries.

### R8. P2: Lexical identity encoding can merge different facts

Reference: [repository.py](src/omniglyph/repository.py), line 212.

Lexical IDs concatenate namespace, canonical ID, term, and source ID with unescaped colons. Different field boundaries can produce the same UUID input.

Reproduction within one source: `(canonical_id="permission:api", term="module:read")` and `(canonical_id="permission:api:module", term="read")` report two imported entries but persist one. The second entry's alias resolves to the first entry's canonical ID and definition.

Recommendation: encode the identity as a structured tuple, following the existing glyph-property implementation, and assess compatibility for stored IDs.

### R9. P2: A validated case-variant pack can fail during alias insertion

Reference: [repository.py](src/omniglyph/repository.py), lines 218 and 252.

`INSERT OR IGNORE` can skip a normalized-term uniqueness conflict. Alias insertion then uses the skipped row's newly calculated ID, which does not exist.

Reproduction: a pack with `FOB` and `fob`, the same canonical ID, and aliases passes validation but raises `IntegrityError: FOREIGN KEY constraint failed`. The transaction rolls back and imports no entries.

Recommendation: reject normalized duplicates during validation or resolve the persisted entry ID before merging aliases. Verify accurate import counts as well as transaction behavior.

### R10. P2: Container-valued output policies cause HTTP 500

Reference: [guardrail.py](src/omniglyph/guardrail.py), line 121.

Policy action validation performs set membership without checking that the value is a string. List and dictionary values are unhashable.

Reproduction: `{"unknown_action":"invalid"}` correctly falls back to `block`, but `{"unknown_action":[]}` and `{"unknown_action":{}}` both produce HTTP 500 with no guardrail decision. These objects pass the current API request model.

Recommendation: validate action value types before membership checks and apply the documented invalid-policy fallback consistently. This is an error-handling defect; it does not establish that a host executes an action after the error.

### R11. P2: Lexicon validation crashes on non-object JSON metadata

Reference: [lexicon_pack.py](src/omniglyph/lexicon_pack.py), line 150.

The metadata validator calls `.get()` before verifying the decoded JSON type. The loader and Policy Pack validator already perform the corresponding object check.

Reproduction: a pack with `pack.json` equal to `[]` returns HTTP 500 from the validation endpoint instead of a structured failed-validation report.

Recommendation: align metadata type validation across loaders and validators, with regression coverage for valid JSON values of the wrong type.

### R12. P2: Email scanning shows quadratic runtime on short adversarial text

Reference: [language_security.py](src/omniglyph/language_security.py), line 26.

For repeated `a.` text without an `@`, the email regex repeatedly retries overlapping candidate local parts. Local measurements for 4K, 8K, 16K, and 32K characters were approximately 0.010, 0.040, 0.159, and 0.641 seconds. Every case returned `allow`; doubling input approximately quadrupled runtime.

This can occupy a synchronous MCP process or API workers when scanning untrusted output. These measurements demonstrate the scaling pattern on this machine, not a production latency benchmark.

Recommendation: use a bounded or linear scanning approach and add an adversarial performance check with appropriate input limits.

### R13. P2: CI does not enforce the documented release checks

References: [test.yml](.github/workflows/test.yml), line 18; [release_check.sh](scripts/release_check.sh), line 18; [mcp_smoke_test.sh](scripts/mcp_smoke_test.sh), line 14.

CI runs source tests, a CLI version check, MCP tool listing, package build, and Twine metadata validation. It omits the local release script's Ruff, mypy, artifact-content audit, isolated wheel smoke, and business demo. Tests and artifacts are also produced in separate jobs, so tests that return early when `dist` is absent do not audit CI-built artifacts. Python 3.10 is advertised but the matrix covers only 3.11 and 3.12.

The shared MCP smoke script also omits `validate_policy_pack` from its expected set. It accepts the other 16 tool names even when that v0.8 tool is absent. Its successful output therefore does not establish completeness of the 17-tool inventory. The wheel smoke checks startup and tool listing, rather than an installed-wheel query or HTTP workflow.

Recommendation: run the intended release checks against the built artifacts in CI, align supported Python coverage, and test actual installed-wheel behavior in addition to tool inventory.

### Maintenance observation: current-state documentation has drifted

References: [v0.8-maintenance-log.md](docs/product/v0.8-maintenance-log.md), line 88; [README.zh-CN.md](README.zh-CN.md), line 430.

Some current-state text still describes work as unmerged or shows 184 passing tests, while the local `main` reviewed here contains the hardening and passes 263 tests. Historical closeouts remain useful, but current readiness should have a single dated entry tied to a source revision. No fresh remote publication status was checked, so this review makes no claim about today's PyPI, registry, or GitHub state.

## Project Inventory and Maturity

| Project | Evidence in the directory | Assessment |
| --- | --- | --- |
| OmniGlyph | Python package, SQLite repository, CLI, FastAPI API, 17 listed MCP tools, tests, examples, release tooling | Implemented infrastructure beta. Suitable for controlled local evaluation; the findings above should be addressed before relying on affected paths for production data or security enforcement. |
| LogosGate / Yanfa Jieshu | Concept documents in the nested directory and an unimplemented MVP plan under `docs/superpowers/plans` | Design-stage extension. No separate runnable package, implemented decorator, or corresponding tests were found. |

OmniGlyph's strongest current proposition is source-traceable Unicode and private terminology lookup exposed through useful developer interfaces. Its compact module structure and shared core logic make the implementation understandable. SQLite foreign keys, parameterized SQL, transactional replacement, source hashes, atomic download replacement, and regression tests show concrete attention to engineering reliability. The replacement defect above concerns validation before that transaction, not an absence of transaction support.

The project also documents important limits: minimal confusable coverage, a lightweight schema subset, no general semantic graph engine, and no replacement for IAM or OS sandboxing. These are product boundaries, not defects merely because broader features are possible. Runtime decisions are evidence for a host system; their effectiveness depends on the host controlling policy selection and honoring `block` and `review`.

No adoption data, buyer interviews, comparative detector evaluation, or production incident evidence was assessed. Commercial potential, competitive superiority, and reductions in real-world hallucination cannot be established from this repository review.

## LogosGate Design Concerns

These findings concern proposed code in a plan, not vulnerabilities in a deployed LogosGate implementation.

### D1. An allowed phrase suppresses a rule across the entire input

Reference: [LogosGate MVP plan](docs/superpowers/plans/2026-04-30-logosgate-mvp.md), line 612.

The proposed matcher returns no findings if any `allow_context` phrase appears anywhere in the text. A plan that quotes a prohibition and then requests the prohibited action can therefore suppress the rule. For example, the Chinese equivalent of "The rule says do not create fake orders; now create fake orders" contains both the allowed context and an affirmative instruction.

Before implementation, scope exceptions to the matched occurrence and bind decisions to structured actions. A global substring exception is insufficient for an action firewall.

### D2. The default decorator executes actions marked for review

References: [LogosGate MVP plan](docs/superpowers/plans/2026-04-30-logosgate-mvp.md), line 883; [concept document](言法界枢/项目思路.md), line 178.

The concept says `review` requires human confirmation, but the proposed decorator defaults to `block_on=("block",)` and its proposed test explicitly allows a review result to execute. Resolve this contradiction before implementing the wrapper: review should remain pending until a trusted approval is supplied.

Keep LogosGate incubated inside OmniGlyph until one concrete host integration proves that denied and pending actions do not execute. Existing intent manifests, roles, parameter checks, and Policy Packs provide a reuse opportunity; the plan should explain which responsibilities require new code.

## Verification Performed

| Check | Fresh result |
| --- | --- |
| Full test suite on local Python 3.11 | 263 passed in 2.02 seconds |
| Ruff | Passed |
| mypy | Passed for 22 source files |
| `git diff --check` | Passed |
| MCP smoke | Passed; actual output listed 17 tools, subject to R13's assertion gap |
| Fresh sdist and wheel build from `6088546` in a temporary source copy | Passed |
| Twine metadata check on both new artifacts | Passed |
| Artifact-content audit on both new artifacts | Passed |
| Isolated wheel CLI/MCP startup smoke | Passed |
| Cross-border example | Known terms normalized and unsupported terms remained unknown |
| Independent data and integration probes | Reproduced the runtime findings described above |

Verification used temporary databases and synthetic credentials. Application code, existing data, and existing release artifacts were not modified. The only project addition is this review report; the pre-existing untracked `CLAUDE.md` was preserved.

Limits: no live Docker deployment, external publication check, full upstream Unicode/Unihan import, production load test, dependency vulnerability audit, or full MCP client conformance test was performed. The fresh package build used the installed local build dependencies without isolation; wheel startup was checked in a separate environment. Passing these checks does not establish complete security coverage.

Method: independent data, security, and release/documentation reviews, followed by reproduction and fresh verification. The `safe-agent-router` selected the unrelated `website-build-launch` scenario; only applicable `engineering-build-release` and `execution-publish-check` guidance was used. Parallel review, systematic debugging, and verification-before-completion guidance supported the evidence gathering. There is no project frontend, so UI-design workflows were not applicable.

## Recommended Improvement Order

1. Protect existing data and private deployments: address replacement validation, Unicode ranges, and localhost defaults. Add regression cases that reproduce the failures before changing behavior.
2. Harden policy and security boundaries: reject ambiguous CSV headers, non-finite numbers, invalid action types, and escaping pack files; correct multilingual DLP boundaries and regex scaling.
3. Stabilize pack ingestion: use unambiguous identities, handle normalized duplicates consistently, and make validation reliably return actionable failures.
4. Make CI reflect release expectations: audit the artifacts actually built, verify all tools and installed behavior, and cover the advertised Python baseline.
5. Validate one narrow user workflow with realistic normal and adversarial inputs. Measure missed detections, false positives, and latency. Use that evidence to decide whether a LogosGate extension is justified, after resolving D1 and D2.

The next investment should be reliability and a demonstrated host workflow. Broader semantic-computation or general firewall claims require evidence beyond the implemented beta and its currently passing tests.
