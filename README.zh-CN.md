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


## 实测数据与预期效果

OmniGlyph 的目标是用本地、可追溯、结构化查询，替代 Agent 临时读网页或让模型直接猜，从而减少 token 浪费和字符/术语级幻觉风险。

### 已验证数据

当前 `v0.2.0-beta` 候选版本已验证：

| 指标 | 结果 |
| --- | ---: |
| UnicodeData 导入 | `40,569` 条 glyph records |
| Unihan_Readings 导入 | `291,227` 条 properties |
| Unihan_DictionaryLikeData 导入 | `156,251` 条 properties |
| 已验证 Unihan 属性总量 | `447,478` 条 properties |
| 本地测试 | `34 passed` |
| N100 Linux 测试 | `34 passed` |
| Docker build/run/healthcheck | N100 验证通过 |
| `铝` 的 SQLite 查询 benchmark | 1000 次查询 P95 约 `0.17ms` |

示例询盘：

```text
Need aluminum profile and tempered glass, FOB Bangkok, MOQ 500 sets.
```

Compact 标准化结果：

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

### Token 节省潜力

以下是工程预估，不是大规模 benchmark 结论：

| 场景 | 预计 token 节省 | 原因 |
| --- | ---: | --- |
| 单个 Unicode 字符查证 | `70%–95%` | 用本地 JSON 替代网页搜索、HTML 和长解释。 |
| CJK 读音查询 | `60%–90%` | 用 Unihan 字段替代模型猜测和解释。 |
| emoji / 符号识别 | `50%–85%` | 直接返回 Unicode 名称和来源属性。 |
| 跨境询盘标准化 | 目标 `30%–70%` | 依赖 domain pack + batch normalize；当前 beta 已具备雏形。 |

### 防幻觉护栏

OmniGlyph 当前通过以下规则降低字符、符号和术语级幻觉：

```text
有来源事实 → 返回事实
上游缺失值 → 返回 null
未知 token → 返回 unknown / 404
```

例如，真实验证的 Unihan 数据为 `铝` 提供了 `kMandarin = lǚ`，但验证过的 Unihan 文件没有给该码点提供 `kDefinition`。因此 OmniGlyph 返回 `basic_meaning: null`，不会为了“看起来完整”而编造解释。

这不能消灭所有 Agent 幻觉，但能提供第一层基础设施：模型推理前，先用确定性的符号和术语事实打底。

## 当前阶段

当前版本适合作为 `v0.2.0-beta` 开源发布候选：

- 可用于本地评估。
- 可用于 Agent 工具集成实验。
- 可用于建材外贸术语标准化 demo。
- 不建议直接作为生产稳定版使用。
