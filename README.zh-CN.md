# OmniGlyph（万象文枢）

> AI Agent 的本地符号真值层。  
> 面向 Codex、OpenClaw、Claude Desktop 和自定义 Agent 的字符事实查询与术语标准化基础设施。

OmniGlyph 不是传统字典。传统字典主要给人类阅读；OmniGlyph 给 Agent 调用。它将 Unicode 字符、Unihan 属性、私有领域词典和来源快照组织成可追溯、可查询、可通过 API/MCP 调用的结构化事实层。


## 为什么说它是 Agent 基础设施

OmniGlyph 不只是一个字典 API，而是 Agent 系统的底层基础设施组件。

### 1. Agent 的物理感知层

大模型并不是像人一样直接“看见”字符，它看到的是 token。当 OpenClaw 这类工作流收到一封混杂缩写、OCR 噪声、小语种、乱码、生僻符号的外贸邮件时，幻觉可能在复杂推理之前就已经发生：它可能从感知和分词阶段就开始偏移。

OmniGlyph 像是 Agent 的高精度符号显微镜。在 LLM 进行意图分析、报价逻辑、风险判断之前，先把不确定字符和领域术语标准化为确定的 Unicode 事实和 canonical ID。

如果感知层不稳定，后端业务逻辑再精妙也会不稳定。OmniGlyph 先稳定第一层。

### 2. Agent 的外部真值记忆

LLM 的知识压缩在概率模型权重里，这让它强大，但也容易被上下文诱导并自信编造。

OmniGlyph 把字符、符号、行业术语的解释权从模型内部记忆中剥离出来，放进一个外部、只读、来源可追溯的本地服务。部署在 N100 等边缘节点后，它就是 Agent 可通过 API 或 MCP 调用的本地 Ground-Truth Memory。

它为 Agent 世界提供了一套局部“度量衡”：符号是什么、术语是什么、来源是什么、缺失就是什么都没有。

### 3. 原子化基础设施

真正好的基础设施不会写死具体业务流程。OmniGlyph 不负责“怎么回复客户”、“怎么算运费”、“怎么给玻璃报价”。它只做一件原子化的事：

```text
输入符号或术语 → 输出来源可追溯的标准属性 / canonical ID
```

正因为它足够原子化和高内聚，才可以被复用到很多场景：

- 外贸询盘清洗
- OCR 后处理
- 多语言商品标题标准化
- RAG 预处理
- 建材术语归一
- Codex / OpenClaw 类 Agent 的 MCP 工具调用

从这个角度看，OmniGlyph 是一次开源尝试：为 Agent 时代定义一个数据清洗与事实确权的底层原语。

## OmniGlyph 填补了什么空白？

目前很多 Agent 系统仍然是“模型优先”的架构：不稳定就换更大的模型、加更长的 Prompt、再叠一层 RAG。这些方法有价值，但不能完全解决符号和术语层面的确定性问题。概率模型应该负责推理，而不应该被迫自己发明底层事实。

OmniGlyph 填补的是三个容易被忽视的基础设施空白：

### 1. 把“感知”和“推理”分离

很多 Agent 工作流把基础识别和高级推理混在同一次 LLM 调用里。对工业自动化来说，这很脆弱。识别一个生僻字符、OCR 噪声片段、当地缩写、材料简称或类似 HS code 的字符串，首先是感知问题，然后才是推理问题。

OmniGlyph 在这一层为 Agent 提供本地事实字典：推理交给模型，认字、认术语、认标准属性交给确定性服务。

### 2. 提供轻量级本地真值源

大型知识图谱和远程 API 很强，但在边缘 Agent 工作流中，可能太重、太慢、太贵，或者过度依赖网络。

OmniGlyph 的目标是作为小型本地服务运行在 Intel N100/N97 等边缘节点上。这样 Agent 可以在消耗大模型 token 之前，先做低延迟、本地化的词法校验；同时也减少敏感业务文本发送到外部服务的需求。

### 3. 把符号转成可计算输入

传统字典主要服务“阅读”，而 Agent 系统需要的是可计算的结构化输入。

OmniGlyph 把字符、别名、缩写和领域术语转换为 canonical ID、JSON facts、来源元数据，并在未来扩展为 computable traits。这相当于把现实世界中混乱的文本，变成报价逻辑、RAG 检索、OCR 校对、合规检查和下游自动化可以稳定使用的输入。

一句话：OmniGlyph 是符号与术语层面的实用防幻觉滤网。它不声称消灭所有模型幻觉，而是通过本地、可追溯的事实层，在推理前后降低一类关键底层错误。

## 当前能力

- UnicodeData 导入与字符查询。
- Unihan 属性导入，支持汉字读音等字段。
- 私有领域词典 CSV 导入。
- `GET /api/v1/glyph` 字符查询。
- `GET /api/v1/term` 术语查询。
- `POST /api/v1/normalize` 批量标准化。
- `omniglyph scan-code` 代码符号审查器。
- MCP 工具：`lookup_glyph`、`lookup_term`、`normalize_tokens`、`validate_output_terms`、`scan_code_symbols`。
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
- `validate_output_terms`
- `scan_code_symbols`

Codex 接入说明见：`docs/integrations/codex-mcp.md`。Claude Desktop / Claude Code 接入见 `docs/integrations/claude-desktop-mcp.md` 和 `docs/integrations/claude-code-mcp.md`。MCP 安全说明见 `docs/security/mcp-safety.md`。

## 许可证

万象文枢（OmniGlyph）源代码采用 Apache License 2.0。

导入的数据集、Unicode/Unihan/CLDR 原始数据以及私有领域词库遵循各自的授权条款，本项目不会对其重新授权。



## 开发者场景：代码符号审查器

OmniGlyph 现在把自己的符号事实层用于编码 Agent 场景。`scan-code` 命令可以检测隐形 Unicode 控制符、Bidi 控制符、跨文字系统同形字符等问题，这类问题会让源码看起来正确，但实际行为异常。

```bash
python examples/poisoned-code/generate_poison.py
omniglyph scan-code examples/poisoned-code/test_bug.py
```

该能力适合接入 pre-commit、CI，以及支持 MCP 的编码 Agent，让 Agent 在修改或解释代码之前，先看见源码的物理 Unicode 真相。详见 `docs/use-cases/code-linter.md`。

## Agent 三明治防线架构

OmniGlyph 可以挂载在 Agent/RAG 工作流的两端：

```text
原始输入
  → OmniGlyph 前置标准化器
  → RAG / LLM / Agent 推理
  → OmniGlyph 输出守门员
  → 客户回复 / 报价 / ERP / 工厂指令
```

作为 **Input Normalizer（前置标准化器）**，OmniGlyph 在检索和推理之前，把客户邮件、OCR 片段、行业缩写、多语言别名和贸易术语映射成 canonical ID。

作为 **Output Guardrail（输出守门员）**，OmniGlyph 在模型生成内容发给客户或下游系统之前进行校验。如果模型编造了不存在的 HS code、材料名或型材型号，工作流可以标记、阻断或转人工复核。

当前版本已经实现输入标准化侧的基础能力：`POST /api/v1/normalize` 和 MCP `normalize_tokens`，并新增最小输出 guardrail，用于已知/未知术语检查。完整的策略阻断、重写、ERP/邮件系统集成仍属于后续工作。

详见：`docs/architecture/sandwich-architecture.md`。

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
