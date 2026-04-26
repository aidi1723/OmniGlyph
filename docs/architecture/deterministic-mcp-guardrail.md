# Deterministic MCP Guardrail

The Deterministic MCP Guardrail is a deployment mode of OmniGlyph, not a replacement for the core language and symbol foundation.

OmniGlyph remains the Symbol Ground Truth Layer for AI agents. The guardrail branch uses that same source-backed base to control what an agent is allowed to claim in enterprise workflows.

## Positioning

Primary project line:

```text
Global symbol, lexical, and semantic infrastructure for AI agents.
```

Guardrail branch:

```text
Deterministic MCP Guardrail for source-grounded agents.
```

The first line explains what OmniGlyph is building over the long term. The second line explains one concrete commercial use case: stopping agents from asserting unsupported terms, symbols, specifications, or security-sensitive facts.

## Boundary Principle

Do not ask a probabilistic model to promise that it will never hallucinate.

Instead, give the model a deterministic boundary:

```text
Known in OmniGlyph → can be used with source evidence
Unknown in OmniGlyph → must be blocked, reviewed, or rewritten
```

This turns "please do not make things up" from a prompt instruction into a runtime policy.

## Runtime Flow

```text
1. Candidate text or output is produced.
2. Terms, symbols, or identifiers are extracted by the host workflow.
3. The host calls OmniGlyph through API or MCP.
4. OmniGlyph checks each candidate against the local fact base.
5. OmniGlyph returns allow/block evidence.
6. The host sends, blocks, rewrites, or routes to human review.
```

The model may still reason, summarize, and write. The factual boundary is enforced outside the model.

## Current Implementation

The current strict-source-grounding policy is intentionally small:

- Input: a list of candidate output terms.
- Known term: term exists in the local lexical/domain fact base.
- Unknown term: term does not exist in the local fact base.
- Decision: `allow` if all terms are known, otherwise `block`.
- Evidence: known canonical IDs, unknown terms, source IDs, limits, and optional audit event.

API:

```text
POST /api/v1/guardrail/enforce-output
```

MCP:

```text
enforce_grounded_output
```

## Response Shape

```json
{
  "schema": "omniglyph.guardrail:0.1",
  "mode": "strict_source_grounding",
  "decision": "block",
  "status": "warn",
  "known": {
    "FOB": "trade:fob"
  },
  "unknown": ["HS 7604.99X"],
  "source_ids": ["..."],
  "limits": [
    "Unknown terms must be reviewed or removed before model output is trusted."
  ]
}
```

When `actor_id` is provided, OmniGlyph also returns audit evidence showing who requested the enforcement decision.

## What This Does Not Claim

This mode does not prove that an entire agent is globally hallucination-free.

It establishes a zero-hallucination boundary for the checked layer:

- checked terms
- checked symbols
- checked Unicode security findings
- checked source-backed facts

Anything outside the checked layer remains the responsibility of the host workflow, model policy, retrieval system, and human review design.

## Why It Fits the Main Mission

The guardrail branch depends on the original OmniGlyph foundation:

- Unicode facts define the physical symbol layer.
- Domain packs define approved private vocabulary.
- OES explanations define evidence shape.
- Audit events define who checked what and what remained unknown.

Without the symbol and lexical foundation, the guardrail would be only a shallow allowlist. With OmniGlyph underneath, it becomes a source-backed boundary controller for agent systems.
