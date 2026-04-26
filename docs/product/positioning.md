# OmniGlyph Positioning

OmniGlyph is a local Symbol Ground Truth Layer for AI agents. It sits below language-model reasoning and above raw Unicode text, giving agents deterministic facts about characters, terms, suspicious symbol patterns, and source-grounded output boundaries.

## Three Complementary Positions

OmniGlyph can be understood through four lenses:

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

## What OmniGlyph Is Not

OmniGlyph deliberately avoids several adjacent claims:

- It is not an OCR engine. It analyzes text/code points after OCR or text extraction has already happened.
- It is not a generative dictionary. It does not ask an LLM to guess unsupported definitions.
- It is not a full semantic-reasoning engine yet. Stage 3/4 semantic topology and computation remain roadmap tracks.
- It is not a replacement for ICU, Unicode tools, or security libraries. It composes with them and exposes agent-friendly APIs/MCP tools.
- It is not a guarantee that all hallucinations disappear. It can enforce zero-hallucination boundaries only for the checked symbol, term, and source-backed fact layer.

## Differentiation

Existing Unicode and homoglyph libraries are valuable, but most are designed for direct developer use. OmniGlyph focuses on making those symbol facts usable by agents:

- local-first runtime
- source-backed JSON responses
- MCP-native tools
- private domain pack mounting
- code-symbol audit workflow
- strict source-grounding guardrail workflow
- explicit separation between global facts and private business vocabulary

The practical goal is not to make models “understand every symbol” by themselves. The goal is to stop agents from guessing when a deterministic local lookup or audit is possible.
