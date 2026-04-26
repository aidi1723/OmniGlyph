# Language Security Gateway

Language Security Gateway is a security branch capability of OmniGlyph. It does not replace the core symbol and language foundation.

The premise is simple:

```text
In agent systems, natural language can behave like executable code.
```

An email, web page, PDF chunk, or model output can contain instructions that try to hijack an agent, leak secrets, or trigger unsafe tool calls. OmniGlyph adds deterministic checkpoints around those language boundaries.

## Layers

### 1. Input Firewall

`scan_language_input` checks untrusted text before model ingestion.

It currently detects:

- prompt-injection directives such as attempts to ignore trusted instructions
- hidden Unicode format characters
- Bidi controls
- control characters
- cross-script homoglyph risks

Natural-language scanning intentionally filters out normal fullwidth punctuation so CJK text does not become noisy.

### 2. Output DLP

`scan_output_dlp` checks model output before external delivery.

It currently detects and redacts:

- OpenAI-style `sk-...` API keys
- AWS access key IDs
- email addresses
- caller-provided secret terms such as supplier names, floor prices, or customer identifiers

The API returns both findings and `redacted_text`. The host decides whether to block, review, or deliver the redacted output.

### 3. Intent Sandbox

`enforce_intent` validates a requested agent action against an intent manifest.

The model should not emit shell commands directly. It should emit a canonical intent such as:

```text
network.restart
```

OmniGlyph checks whether that intent exists, whether the actor role is allowed, and whether approval is required.

Example manifest:

```json
{
  "intents": [
    {
      "intent_id": "network.restart",
      "canonical_phrase": "restart network service",
      "allowed_commands": ["systemctl restart network"],
      "risk_level": "high",
      "requires_approval": true,
      "allowed_roles": ["admin"],
      "audit_required": true
    }
  ]
}
```

OmniGlyph never executes `allowed_commands`. They are evidence for a host gateway, policy engine, or human reviewer.

## Runtime Flow

```text
Untrusted language
  → scan_language_input
  → model
  → scan_output_dlp
  → intent extraction by host
  → enforce_intent
  → host allow / review / block
```

## Boundary

This does not prove that prompt injection is globally solved.

It creates deterministic safety checkpoints for the parts OmniGlyph can inspect:

- physical Unicode attacks
- known prompt-injection phrases
- obvious sensitive output patterns
- explicit secret terms
- manifest-defined intents

Anything outside those checked layers remains the responsibility of the host model policy, retrieval design, tool permissioning, and human review.
