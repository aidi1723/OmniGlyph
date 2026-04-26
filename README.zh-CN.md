# OmniGlyph（万象文枢）

[![PyPI](https://img.shields.io/pypi/v/omniglyph?label=PyPI)](https://pypi.org/project/omniglyph/)
[![MCP Registry](https://img.shields.io/badge/MCP%20Registry-io.github.aidi1723%2Fomniglyph-blue)](https://registry.modelcontextprotocol.io/)
[![License](https://img.shields.io/badge/license-Apache--2.0-green)](LICENSE)

> AI Agent 的本地符号真值层。  
> 面向 Codex、OpenClaw、Claude Desktop 和自定义 Agent 的字符事实查询与术语标准化基础设施。

OmniGlyph 不是传统字典。传统字典主要给人类阅读；OmniGlyph 给 Agent 调用。它将 Unicode 字符、Unihan 属性、私有领域词典和来源快照组织成可追溯、可查询、可通过 API/MCP 调用的结构化事实层。

## 产品主线

OmniGlyph 现在围绕三层能力建设，但三层都共享同一个确定性符号真值底座。

### 1. 全球符号真知层

OmniGlyph 为 Agent 提供本地、可追溯、确定性的符号与术语事实层。它帮助 Agent 在推理前识别 Unicode 码点、同形字符、零宽字符、Bidi 控制符、全角/半角异常和私有业务术语。

这不是“消灭所有幻觉”的承诺，而是降低一类非常具体的字符、符号、术语层错误：让底层文本基座可检查、可追溯、可被机器稳定调用。

### 2. 企业级确定性护栏

基于符号真值层，OmniGlyph 可以作为企业工作流里的确定性 MCP 护栏。用户可以挂载私有 Lexicon Pack，把业务术语、SKU、材料名、供应商词汇、敏感词和 approved alias 接入本地真值库。

Agent 输出前可通过 `validate_output_terms` 和 `enforce_grounded_output` 检查。未知、未审核或无来源支持的词条可以被阻断或转人工复核，避免进入客户回复、报价、ERP 或下游工具。

### 3. Language-as-Code 安全网关

OmniGlyph 也把自然语言当作运行时攻击面处理。`scan_language_input` 检查不可信输入中的 prompt-injection 指令和隐藏 Unicode 攻击；`scan_output_dlp` 对出境文本做脱敏；`enforce_intent` 用 intent manifest 校验 Agent 动作请求。

这一层不执行 shell 命令，也不承诺彻底解决所有 prompt injection。它提供机器可读的 `allow`、`review`、`block` 证据，让执行和交付决策发生在模型外部。

一句话：

> OmniGlyph 是面向 AI Agent 的本地符号真值层、确定性企业护栏与语言安全网关。

## 已发布到 PyPI + MCP Registry

OmniGlyph 已准备为 Python 包和 MCP Registry server。

- 当前源码包版本：`omniglyph==0.7.0b0`
- 最新已发布 PyPI 包：`omniglyph==0.6.0b0`
- MCP Registry server：`io.github.aidi1723/omniglyph`
- 传输方式：本地 stdio MCP server

安装最新已发布的 PyPI 包：

```bash
pip install omniglyph==0.6.0b0
```

启动 MCP server：

```bash
omniglyph-mcp
```

快速验证 MCP tools：

```bash
printf '{"jsonrpc":"2.0","id":1,"method":"tools/list"}\n' | omniglyph-mcp
```

当前源码分支版本为 `0.7.0b0`，已经提供 v0.7 MCP 工具集。`0.7.0b0` 的 PyPI 发布属于单独 release 步骤。

当前源码 MCP 工具：`lookup_glyph`、`lookup_term`、`explain_glyph`、`explain_term`、`explain_code_security`、`normalize_tokens`、`list_namespaces`、`validate_lexicon_pack`、`validate_output_terms`、`enforce_grounded_output`、`scan_code_symbols`、`scan_unicode_security`、`scan_language_input`、`scan_output_dlp`、`enforce_intent`、`audit_explain`。

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


## 范围与边界

当前 beta 阶段的 OmniGlyph 故意保持克制：

- 它分析的是 Unicode 文本/码点，不直接识别原始图片。OCR 或视觉字形识别应在 OmniGlyph 之前完成。
- 它返回来源可追溯的事实和规则检测结果，不生成式猜测解释。
- 它可以降低符号/术语层面的幻觉，但不声称消灭所有大模型幻觉。
- 它把全球 Unicode 事实、Unihan 事实和私有领域词典分层处理，避免业务私有词汇污染公共真值层。

详细定位与非目标见 `docs/product/positioning.md`。

## 项目成熟度说明

当前项目仍处于 beta 阶段，适合本地 Agent 增强、RAG 预处理、代码符号审查和 OCR/文本清洗原型。它不是通用大模型，也不是完整生产级语义计算引擎。详细状态见 `docs/product/project-status.md`，路线图见 `ROADMAP.md`。

## 当前能力

- UnicodeData 导入与字符查询。
- Unihan 属性导入，支持汉字读音等字段。
- 私有领域词典 CSV 导入。
- `GET /api/v1/glyph` 字符查询。
- `GET /api/v1/term` 术语查询。
- `POST /api/v1/normalize` 批量标准化。
- `omniglyph scan-code` 代码符号审查器。
- OES v0.1 解释协议：`explain_glyph`、`explain_term`、`explain_code_security`。
- Unicode Security Pack：带 `source_id`、`why_it_matters`、`suggested_action` 的开发者友好扫描结果。
- 软件开发领域词库 starter pack：`examples/domain-packs/software_development.csv`。
- Audit Workflow：记录谁查询了什么、来源是什么、哪里未知。
- Language Security Gateway：输入 prompt-injection 扫描、输出 DLP 脱敏、intent manifest 沙盒决策。
- MCP 工具：`lookup_glyph`、`lookup_term`、`explain_glyph`、`explain_term`、`explain_code_security`、`normalize_tokens`、`validate_output_terms`、`enforce_grounded_output`、`scan_code_symbols`、`scan_unicode_security`、`scan_language_input`、`scan_output_dlp`、`enforce_intent`、`audit_explain`。
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
.venv/bin/omniglyph ingest-domain-pack --source examples/domain-packs/software_development.csv --namespace public_software_development --source-version 0.1.0
```

创建和导入自己的企业/个人词库：

```bash
.venv/bin/omniglyph init-lexicon-pack my-pack --namespace private_acme --pack-id company.acme.trade_terms --name "ACME Trade Terms"
.venv/bin/omniglyph validate-domain-pack my-pack
.venv/bin/omniglyph ingest-domain-pack --source my-pack --dry-run
.venv/bin/omniglyph ingest-domain-pack --source my-pack --replace-namespace
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
- `explain_glyph`
- `explain_term`
- `explain_code_security`
- `normalize_tokens`
- `validate_output_terms`
- `enforce_grounded_output`
- `scan_code_symbols`
- `scan_unicode_security`
- `scan_language_input`
- `scan_output_dlp`
- `enforce_intent`
- `audit_explain`

Codex 接入说明见：`docs/integrations/codex-mcp.md`。Claude Desktop / Claude Code 接入见 `docs/integrations/claude-desktop-mcp.md` 和 `docs/integrations/claude-code-mcp.md`。MCP 安全说明见 `docs/security/mcp-safety.md`。

## 许可证

万象文枢（OmniGlyph）源代码采用 Apache License 2.0。

导入的数据集、Unicode/Unihan/CLDR 原始数据以及私有领域词库遵循各自的授权条款，本项目不会对其重新授权。



## 开发者场景：代码符号审查器

OmniGlyph 现在把自己的符号事实层用于编码 Agent 场景。`scan-code` 命令可以检测隐形 Unicode 控制符、Bidi 控制符、来源可追溯的 confusable、跨文字系统同形字符、全角/半角字符和 NFKC 归一化变化，这类问题会让源码看起来正确，但实际行为异常。

```bash
python examples/poisoned-code/generate_poison.py
omniglyph scan-code examples/poisoned-code/test_bug.py
```

该能力适合接入 pre-commit、CI，以及支持 MCP 的编码 Agent，让 Agent 在修改或解释代码之前，先看见源码的物理 Unicode 真相。企业流程需要留痕时，可以用 `audit_explain` 记录操作者、输入、来源和未知项。详见 `docs/use-cases/code-linter.md` 与 `docs/use-cases/security-dictionary-audit.md`。

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

当前版本已经实现输入标准化侧的基础能力：`POST /api/v1/normalize` 和 MCP `normalize_tokens`，并新增输出 guardrail，用于已知/未知术语检查和严格溯源的 `allow/block` 决策。重写、ERP/邮件系统集成、完整人工复核流仍属于后续工作。

详见：`docs/architecture/sandwich-architecture.md`。

## 确定性 MCP 护栏

护栏能力是 OmniGlyph 的一个商业化部署模式。它不改变项目主线，而是把符号真值层、领域词库、OES 和审计事件用于一个更直接的问题：

```text
这个 Agent 的输出，哪些可以放行，哪些必须拦截？
```

当前严格溯源策略会返回：

- 所有候选术语都存在于本地事实库时，`decision: "allow"`。
- 任何候选术语未知时，`decision: "block"`。
- 已知事实对应的 `source_ids`。
- 传入 `actor_id` 时返回审计证据。

## Language Security Gateway（语言安全网关）

语言安全网关是 OmniGlyph 的安全分支能力，不替代原本的全球符号与语言基础设施。

```text
外部输入
  → scan_language_input
  → 拦截 prompt injection 或隐藏 Unicode 攻击
  → 模型推理
  → scan_output_dlp
  → 脱敏密钥、邮箱、商业机密词
  → enforce_intent
  → 对 Agent 动作请求返回 allow / review / block
```

当前已实现：

- `scan_language_input`：在输入进入模型前扫描 prompt-injection 指令和高风险隐藏 Unicode。
- `scan_output_dlp`：在输出出境前扫描 API key、AWS key、邮箱和调用方传入的机密词，并返回 `[REDACTED]` 文本。
- `enforce_intent`：根据 intent manifest 校验 Agent 动作请求，只返回决策，不执行 shell 命令。

这不是“彻底消灭 prompt injection”的承诺，而是给 AgentCore / MCP 工作流增加确定性安全检查点，让模型即使被诱导也不能直接越过边界。

## 实测数据与预期效果

OmniGlyph 的目标是用本地、可追溯、结构化查询，替代 Agent 临时读网页或让模型直接猜，从而减少 token 浪费和字符/术语级幻觉风险。

### 已验证数据

当前 `v0.7.0-beta` 源码候选版本已在本地验证：

| 指标 | 结果 |
| --- | ---: |
| UnicodeData 导入 | `40,569` 条 glyph records |
| Unihan_Readings 导入 | `291,227` 条 properties |
| Unihan_DictionaryLikeData 导入 | `156,251` 条 properties |
| 已验证 Unihan 属性总量 | `447,478` 条 properties |
| 本地测试 | `112 passed` |
| N100 Linux 测试 | beta 分支曾验证通过 |
| Docker build/run/healthcheck | N100 曾验证通过 |
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

当前源码版本适合作为 `v0.7.0-beta` 开源发布候选：

- 可用于本地评估。
- 可用于 Agent 工具集成实验。
- 可用于建材外贸术语标准化 demo。
- 不建议直接作为生产稳定版使用。
