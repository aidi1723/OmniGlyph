# OmniGlyph v0.8.0 Beta 中文更新说明草稿

当前源码版本：`0.8.0b0`。

v0.8.0 beta 新增 World Protocol Pack v0.1，这是 OmniGlyph “世界大词典 / 文明根证书”方向的第一步工程化实现。它把协议规则变成可版本化、可溯源、可确定性检查的规则包，让 Agent host 可以在允许目标、动作、intent 或输出继续之前，先调用 OmniGlyph 做协议检查。

## 新增内容

- 新增 `src/omniglyph/protocol_pack.py`，支持协议包验证、加载、匹配和决策聚合。
- 新增 `examples/protocol-packs/root_starter/protocol.json` 作为 starter root protocol 示例。
- 新增 CLI 命令：
  - `omniglyph init-protocol-pack`
  - `omniglyph validate-protocol-pack`
  - `omniglyph check-protocol`
- 新增 API：
  - `POST /api/v1/protocol/validate-pack`
  - `POST /api/v1/protocol/check`
- 新增 MCP 工具：
  - `validate_protocol_pack`
  - `check_protocol`
- 新增文档：
  - `docs/specs/world-protocol-pack-standard.md`
  - `docs/architecture/world-protocol-layer.md`

## 运行行为

`check_protocol` 返回四类确定性决策：

- `block`：命中了至少一条阻断规则。
- `warn`：未命中阻断规则，但命中了警告规则。
- `allow`：命中的规则均为允许规则。
- `unknown`：没有命中任何已配置规则。

`unknown` 不是放行许可。Host runtime 仍然需要决定是转人工复核、阻断、降级 fallback，还是走其他策略。

## MCP 工具数

当前源码 MCP server 暴露 18 个工具：

- `lookup_glyph`
- `lookup_term`
- `explain_glyph`
- `explain_term`
- `explain_code_security`
- `normalize_tokens`
- `list_namespaces`
- `validate_lexicon_pack`
- `validate_protocol_pack`
- `check_protocol`
- `validate_output_terms`
- `enforce_grounded_output`
- `scan_code_symbols`
- `scan_unicode_security`
- `scan_language_input`
- `scan_output_dlp`
- `enforce_intent`
- `audit_explain`

## 边界说明

World Protocol Pack v0.1 不是全球伦理裁判，也不证明 Agent 已经完成全局对齐。它是一个针对已配置规则的确定性协议检查层，返回匹配规则、来源、置信度、limits 和决策证据。

换句话说，它把“世界大词典”的宏大方向先落成一个可运行、可验证、可审计的最小协议层。
