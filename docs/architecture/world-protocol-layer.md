# World Protocol Layer

The World Protocol Layer is a higher-level OmniGlyph capability for checking Agent goals, actions, intents, and outputs against versioned protocol packs.

It extends OmniGlyph's existing foundation:

```text
Global Symbol Ground Truth Layer
  -> Lexicon Pack and OES evidence
  -> World Protocol Pack rules
  -> API / MCP / CLI protocol checks
  -> Host allow, review, block, or fallback decision
```

## Why This Exists

Agent systems need more than prompts that say "be safe" or "do not hallucinate." They need deterministic checkpoints that return source-backed evidence outside the model.

World Protocol Packs make that boundary explicit. A host runtime can force an Agent to call `check_protocol` before it sends an answer, executes an action, or treats a goal as acceptable.

## Current Scope

v0.1 is intentionally small:

- protocol pack validation
- keyword and exact-intent matchers
- deterministic `allow`, `warn`, `block`, or `unknown`
- source, confidence, and limits fields
- API, MCP, and CLI exposure

It does not claim to be a final global ethics authority. It is a checked protocol layer that the host runtime can compose with retrieval, permissions, human review, and existing safety systems.

## Relationship to Other Layers

- Lexicon Packs define trusted vocabulary.
- OES defines how explanations carry sources and limits.
- Language Security Gateway scans prompt-injection and DLP risks.
- Intent Sandbox validates manifest-defined actions.
- World Protocol Layer checks broader protocol rules configured by a pack maintainer.

These layers are complementary. None of them executes shell commands or replaces host-level permissioning.
