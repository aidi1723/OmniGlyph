# Sandwich Architecture for Agents

OmniGlyph is designed to sit on both sides of an Agent/RAG workflow:

```text
Raw input
  → OmniGlyph Input Normalizer
  → RAG / LLM / Agent reasoning
  → OmniGlyph Output Guardrail
  → customer reply / quote / ERP / factory instruction
```

## 1. Input Normalizer

The input normalizer handles noisy physical-world text before it enters the model.

Examples:

```text
alu prof → material:aluminum_profile
temp glass → material:tempered_glass
FOB → trade:fob
MOQ → trade:moq
```

This helps prevent garbage-in/garbage-out failures:

- non-standard abbreviations become canonical IDs
- multilingual aliases become standard domain terms
- RAG receives cleaner search keys
- prompts carry compact identifiers instead of long explanations

Implemented today:

- `POST /api/v1/normalize`
- MCP `normalize_tokens`
- private domain pack ingestion
- compact mode canonical IDs

## 2. Output Guardrail

The output guardrail checks generated model output before it reaches customers or downstream systems.

The goal is to catch terms, material names, HS codes, model numbers, or domain-specific strings that are not present in the local fact base.

Examples:

```text
Known: FOB, tempered glass, aluminum profile
Unknown: HS 7604.99X, imaginary profile model, misspelled material name
```

Possible actions:

- pass
- warn
- block
- route to human review
- ask the LLM to rewrite with verified terms only

Implemented today:

- minimal text guardrail API for exact known-term detection
- unknown-token reporting for reviewed candidate outputs

Not implemented yet:

- automatic natural-language term extraction
- policy-based block/rewrite/review workflows
- ERP/email/factory-system integration
- severity scoring beyond known/unknown status

## Why This Matters

Many Agent failures begin at the smallest layer:

```text
character mistaken → term guessed → concept normalized incorrectly → business decision drifts
```

OmniGlyph stabilizes both ends:

- before reasoning: normalize inputs
- after reasoning: verify outputs

This makes it a symbol and term certainty layer for practical Agent systems.
