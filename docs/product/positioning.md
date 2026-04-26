# OmniGlyph Positioning

OmniGlyph is a local Symbol Ground Truth Layer for AI agents. It sits below language-model reasoning and above raw Unicode text, giving agents deterministic facts about characters, terms, suspicious symbol patterns, and source-grounded output boundaries.

## Product Thesis

OmniGlyph should be described as:

```text
A local Symbol Ground Truth Layer, deterministic enterprise guardrail, and language security gateway for AI agents.
```

This framing preserves the original language and symbol infrastructure mission while making the near-term commercial and security branches explicit.

## Strategic Layers

### 1. Global Symbol Ground Truth Layer

This is the absolute foundation.

OmniGlyph gives agents deterministic visibility into the physical text substrate: Unicode code points, source-backed glyph facts, Unihan properties, zero-width characters, Bidi controls, cross-script homoglyph risks, fullwidth/halfwidth forms, and private domain terms.

Preferred claim:

```text
OmniGlyph reduces character-, symbol-, and terminology-layer hallucination by making the low-level text substrate inspectable and source-backed.
```

Avoid claiming that OmniGlyph eliminates every token or model hallucination.

### 2. Strict Enterprise Guardrails

This is the near-term commercial engine.

Private Lexicon Packs let users mount approved company vocabulary, aliases, SKUs, confidential terms, supplier names, material terms, and industry abbreviations. Guardrail tools can then block unknown or unapproved output terms before customer delivery or downstream system actions.

Preferred claim:

```text
OmniGlyph provides source-grounded allow/block evidence for checked business terms and approved vocabulary.
```

Avoid claiming that all enterprise AI output is globally hallucination-free.

### 3. Language-as-Code Security Gateway

This is the security branch.

OmniGlyph treats natural language as a runtime attack surface: inputs can carry prompt-injection directives, outputs can leak secrets, and action requests can attempt to exceed policy. The gateway tools return `allow`, `review`, or `block` evidence without executing commands.

Preferred claim:

```text
OmniGlyph creates deterministic checkpoints for untrusted language, outbound text, and requested agent intents.
```

Avoid claiming complete prompt-injection immunity or replacing OS sandboxing, IAM, approval workflows, or endpoint security.

## Complementary Positions

OmniGlyph can be understood through five lenses:

1. **Unicode fact infrastructure**
   - Looks up code points, names, source snapshots, and selected lexical properties.
   - Keeps missing facts as `null` instead of inventing definitions.
   - Treats source provenance as part of the data model.

2. **Agent grounding layer**
   - Gives MCP-enabled agents tools such as `lookup_glyph`, `normalize_tokens`, and `validate_output_terms`.
   - Helps agents check symbols and domain terms before spending tokens on reasoning.
   - Works as a pre-reasoning normalizer and post-reasoning guardrail.

3. **Unicode security and audit tool**
   - Detects invisible characters, Bidi controls, unexpected controls, and cross-script homoglyph risks.
   - Targets code-review agents, copied code snippets, logs, OCR output, social text, and security-sensitive identifiers.
   - Will expand toward Unicode confusables, domain spoofing, and username validation workflows.

4. **Deterministic MCP guardrail**
   - Applies the local truth base to generated output terms before customer or system delivery.
   - Returns `allow` or `block` decisions for checked terms with source IDs and unknowns.
   - Works as a commercial branch capability without narrowing the long-term language and symbol infrastructure mission.

5. **Language security gateway**
   - Treats untrusted natural language and model output as security-sensitive runtime surfaces.
   - Scans prompt-injection directives, hidden Unicode attacks, outbound secrets, and requested action intents.
   - Returns deterministic `allow`, `review`, or `block` decisions without executing commands.

## What OmniGlyph Is Not

OmniGlyph deliberately avoids several adjacent claims:

- It is not an OCR engine. It analyzes text/code points after OCR or text extraction has already happened.
- It is not a generative dictionary. It does not ask an LLM to guess unsupported definitions.
- It is not a full semantic-reasoning engine yet. Stage 3/4 semantic topology and computation remain roadmap tracks.
- It is not a replacement for ICU, Unicode tools, or security libraries. It composes with them and exposes agent-friendly APIs/MCP tools.
- It is not a guarantee that all hallucinations disappear. It can enforce zero-hallucination boundaries only for the checked symbol, term, and source-backed fact layer.
- It is not a complete prompt-injection or DLP product. The language-security branch creates deterministic checkpoints for checked patterns, secret terms, and manifests.

## Differentiation

Existing Unicode and homoglyph libraries are valuable, but most are designed for direct developer use. OmniGlyph focuses on making those symbol facts usable by agents:

- local-first runtime
- source-backed JSON responses
- MCP-native tools
- private domain pack mounting
- code-symbol audit workflow
- strict source-grounding guardrail workflow
- language-security gateway workflow
- explicit separation between global facts and private business vocabulary

The practical goal is not to make models “understand every symbol” by themselves. The goal is to stop agents from guessing when a deterministic local lookup or audit is possible.
