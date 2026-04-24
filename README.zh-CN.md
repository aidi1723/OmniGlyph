# OmniGlyph（万象文枢）

> AI Agent 的本地符号真值层。  
> 面向 Codex、OpenClaw、Claude Desktop 和自定义 Agent 的字符事实查询与术语标准化基础设施。

OmniGlyph 不是传统字典。传统字典主要给人类阅读；OmniGlyph 给 Agent 调用。它将 Unicode 字符、Unihan 属性、私有领域词典和来源快照组织成可追溯、可查询、可通过 API/MCP 调用的结构化事实层。

## 当前能力

- UnicodeData 导入与字符查询。
- Unihan 属性导入，支持汉字读音等字段。
- 私有领域词典 CSV 导入。
- `GET /api/v1/glyph` 字符查询。
- `GET /api/v1/term` 术语查询。
- `POST /api/v1/normalize` 批量标准化。
- MCP 工具：`lookup_glyph`、`lookup_term`、`normalize_tokens`。
- 建材外贸 demo pack 与跨境询盘 demo。
- Docker、CI、release check、N100 验证记录。

## 快速开始

```bash
UV_CACHE_DIR=.uv-cache uv venv .venv --python 3.11
UV_CACHE_DIR=.uv-cache uv pip install -e '.[dev]'
.venv/bin/python -m pytest -v
```

导入示例数据：

```bash
.venv/bin/omniglyph ingest-unicode --source tests/fixtures/UnicodeData.sample.txt --source-version fixture
.venv/bin/omniglyph ingest-domain-pack --source examples/domain-packs/building_materials.csv --namespace private_building_materials --source-version example
```

启动 API：

```bash
.venv/bin/uvicorn omniglyph.api:app --reload
```

查询字符：

```bash
curl 'http://127.0.0.1:8000/api/v1/glyph?char=%E9%93%9D'
```

批量标准化：

```bash
curl -X POST 'http://127.0.0.1:8000/api/v1/normalize?mode=compact' \
  -H 'Content-Type: application/json' \
  -d '{"tokens":["铝","FOB","tempered glass","unknown"]}'
```

预期结果：

```json
{
  "known": {
    "铝": "glyph:U+94DD",
    "FOB": "trade:fob",
    "tempered glass": "material:tempered_glass"
  },
  "unknown": ["unknown"]
}
```

## 运行 Demo

```bash
PYTHONPATH=src .venv/bin/python examples/scripts/run_cross_border_demo.py
```

该 demo 会把：

```text
Need aluminum profile and tempered glass, FOB Bangkok, MOQ 500 sets.
```

标准化为：

```json
{
  "known": {
    "aluminum profile": "material:aluminum_profile",
    "tempered glass": "material:tempered_glass",
    "FOB": "trade:fob",
    "MOQ": "trade:moq"
  },
  "unknown": ["Bangkok", "500 sets"]
}
```

## MCP 使用

启动 MCP server：

```bash
.venv/bin/omniglyph-mcp
```

可用工具：

- `lookup_glyph`
- `lookup_term`
- `normalize_tokens`

Codex 接入说明见：`docs/integrations/codex-mcp.md`。

## 许可证

万象文枢（OmniGlyph）源代码采用 Apache License 2.0。

导入的数据集、Unicode/Unihan/CLDR 原始数据以及私有领域词库遵循各自的授权条款，本项目不会对其重新授权。

## 当前阶段

当前版本适合作为 `v0.2.0-beta` 开源发布候选：

- 可用于本地评估。
- 可用于 Agent 工具集成实验。
- 可用于建材外贸术语标准化 demo。
- 不建议直接作为生产稳定版使用。
