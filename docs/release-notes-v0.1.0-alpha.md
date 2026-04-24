# OmniGlyph v0.1.0-alpha 发布说明

> AI Agent 的本地符号真值层：减少 token 消耗，降低字符级幻觉，约束 Agent 在符号事实上的“发飘”。

OmniGlyph（万象文枢）不是给人类浏览的传统字典，而是给 Agent 调用的本地符号事实基础设施。它把 Unicode 字符、Unihan 属性、来源快照和私有领域属性组织成可追溯、可查询、可通过 API/MCP 调用的结构化事实层。

当前版本定位为 **v0.1.0-alpha**：适合本地评估、Agent 集成实验、OpenClaw/AgentCore 原型接入，不建议直接作为生产稳定版使用。

## 一句话价值

OmniGlyph 让 Agent 在遇到字符、符号、汉字、emoji、CJK 字符时，不再依赖大模型猜测，而是先查询本地确定性事实库。

```text
未知符号 → 本地 OmniGlyph 查询 → 来源可追溯 JSON → Agent 再执行任务
```

这使 OmniGlyph 成为 Agent 系统中的：

- **符号真值层**：给字符和符号提供确定性来源。
- **上下文压缩器**：用短 JSON / MCP 工具调用替代网页字典和长上下文。
- **防幻觉护栏**：缺失字段返回 `null`，不让模型编造。
- **本地知识心脏**：可部署在 N100 等边缘节点，离线、私有、低延迟。

## 已实现能力

### 1. Unicode 字符事实层

已支持导入并查询 `UnicodeData.txt`。

可返回：

- 字符本体
- Unicode code point
- Unicode name
- source snapshot
- SHA-256
- license note
- raw properties

真实数据验证：

- `UnicodeData.txt` 下载成功。
- SHA-256：`2e1efc1dcb59c575eedf5ccae60f95229f706ee6d031835247d843c11d96470c`
- 导入 `40,569` 条 glyph records。
- 修复并测试了 surrogate code point 跳过逻辑，避免真实 UnicodeData 导入崩溃。

### 2. Unihan 汉字属性增强

已支持导入 Unihan tab-separated 数据文件。

真实数据验证：

- `Unihan_Readings.txt` 导入 `291,227` 条 properties。
- `Unihan_DictionaryLikeData.txt` 导入 `156,251` 条 properties。
- 查询 `铝` 可返回：
  - `unicode.hex = U+94DD`
  - `lexical.pinyin = lǚ`
  - `basic_meaning = null`

其中 `basic_meaning = null` 是一个重要设计：当前验证过的 Unihan 文件没有给 `U+94DD` 提供 `kDefinition`，系统不会让模型或程序擅自补写“aluminum”。

### 3. FastAPI 查询接口

提供本地 HTTP 查询：

```text
GET /api/v1/glyph?char=铝
```

返回结构包含：

- `unicode`
- `lexical`
- `domain_traits`
- raw `properties`
- `sources`

示例：

```json
{
  "glyph": "铝",
  "unicode": {
    "hex": "U+94DD",
    "name": "CJK UNIFIED IDEOGRAPH-94DD",
    "block": null
  },
  "lexical": {
    "pinyin": "lǚ",
    "basic_meaning": null,
    "sources": {
      "pinyin": "Unihan Database"
    }
  },
  "domain_traits": {},
  "properties": [],
  "sources": []
}
```

### 4. MCP Agent 工具接口

提供最小 stdio MCP server，暴露工具：

```text
lookup_glyph
```

支持：

- `initialize`
- `tools/list`
- `tools/call`

这使 OmniGlyph 可以作为 OpenClaw、Claude Desktop、自定义 Agent、RAG pipeline 的本地工具源。

### 5. Source-backed append-only 数据模型

核心表：

- `source_snapshot`
- `glyph_node`
- `glyph_property`

特点：

- 每条事实都能追踪来源。
- 多源属性 append-only 存储，不覆盖旧事实。
- 不同来源冲突时保留所有来源，API 层再决定如何展示。
- 私有领域属性通过 `private_*` namespace 隔离。

### 6. Docker / N100 验证

已在 N100 服务器验证：

- 主机：`yami-n100`
- Python：`3.12.3`
- Docker：`28.2.2`
- 测试：`21 passed in 2.06s`
- Docker image：`omniglyph:0.1.0-alpha` 构建成功。
- 容器启动成功。
- 空数据库查询返回 `404`，不是 `500`。
- 容器内导入 fixture 后，`/api/v1/glyph?char=铝` 返回 `U+94DD`。

## 对 Token 节省的价值

### 当前已能节省的部分

OmniGlyph 当前主要节省 **字符/符号事实查询** 的 token。

传统 Agent 遇到不确定符号时，常见流程是：

```text
搜索网页 → 读取 HTML/字典页 → 塞进上下文 → 让模型总结
```

这可能消耗数千 token，并引入网页噪声和幻觉风险。

OmniGlyph 的流程是：

```text
调用 lookup_glyph → 返回短 JSON → Agent 使用确定字段
```

例如 `铝` 的必要事实可以压缩为：

```json
{
  "glyph": "铝",
  "unicode": {"hex": "U+94DD"},
  "lexical": {"pinyin": "lǚ", "basic_meaning": null}
}
```

### Token 节省估计

以下为工程估计，不是当前版本的正式 benchmark 指标：

| 场景 | 当前节省预估 | 说明 |
| --- | ---: | --- |
| 单字符 Unicode 查证 | 70%–95% | 用本地 JSON 取代网页/搜索上下文。 |
| CJK 字符读音确认 | 60%–90% | 用 Unihan 字段取代模型推测和解释。 |
| emoji / 符号识别 | 50%–85% | Unicode name 直接返回。 |
| 整段询盘解析 | 5%–15% | 当前尚未实现 batch normalize 和词典层。 |

下一阶段加入 Private Domain Pack、Batch Normalize、Compact Mode、MCP `normalize_tokens` 后，跨境询盘/商品标题类场景预计可节省：

| 场景 | 后续目标节省预估 |
| --- | ---: |
| 跨境询盘解析 | 30%–70% |
| 商品标题标准化 | 40%–80% |
| 多语言术语归一 | 50%–85% |
| Agent 多轮事实复用 | 50%+ |

## 防幻觉能力

### 当前能防止的幻觉

OmniGlyph 当前能显著降低 **字符级 / 符号级幻觉**：

- Unicode 编码乱猜。
- 生僻字符认错。
- 汉字读音乱猜。
- emoji / 数学符号 / 专业符号解释发散。
- 把不存在的字段说成存在。
- 把来源不明的解释混进标准事实。

关键机制：

```text
有来源 → 返回事实
没来源 → 返回 null
没记录 → 返回 404
```

例如，真实数据中 `铝` 有 `kMandarin = lǚ`，但当前验证源没有 `kDefinition`。OmniGlyph 返回：

```json
{
  "pinyin": "lǚ",
  "basic_meaning": null
}
```

这比让模型直接回答“铝就是 aluminum”更严格，因为它区分了“常识可能知道”和“当前事实库有来源证明”。

### 当前不能防止的幻觉

v0.1.0-alpha 还不能防止所有业务语义幻觉，例如：

- 复杂询盘理解。
- 供应链风险判断。
- 保险建议。
- 英文/泰语/阿语整词释义。
- `风暴 + 海运 + 玻璃` 这种语义计算。

这些需要后续的：

- Private Domain Pack
- term API
- batch normalize
- concept graph
- computable traits
- rule engine

## 防止 Agent “发飘”的能力

Agent 发飘常常源于最小事实不稳定：

```text
字符识别错 → 词义猜错 → 概念归一错 → 业务判断发散
```

OmniGlyph 当前先约束第一层：

```text
字符/符号事实必须先查本地真值层
```

这可以让 Agent 形成更稳定的工作模式：

1. 遇到不确定字符，不直接解释。
2. 调用 `lookup_glyph`。
3. 只使用返回的 source-backed 字段。
4. 缺失字段明确标记为 `null`。
5. 后续回答中区分“已验证事实”和“未覆盖信息”。

这不是完整的 Agent 行为控制系统，但已经是 Agent 基础设施中的第一层护栏。

## 为什么这是 Agent 基础设施

OmniGlyph 不只是一个 API 或字典，而是 Agent 系统的底层组件。

它提供：

- **确定性事实层**：弥补 LLM 概率生成的不稳定。
- **本地查询层**：避免每次把网页/字典塞进 prompt。
- **来源追踪层**：让 Agent 回答时能知道事实从哪里来。
- **空值纪律**：缺失即缺失，不编造。
- **MCP 工具层**：让 Agent 以标准工具协议调用。
- **边缘部署能力**：可在 N100 等低功耗节点运行。
- **私有扩展入口**：可挂载建材外贸、HS code、贸易术语等私有词库。

类比：

```text
操作系统需要文件系统
搜索引擎需要索引
数据库需要 schema
Agent 系统需要符号真值层
```

OmniGlyph 的定位正是：

> Symbol Ground Truth Layer for AI Agents.

## 性能数据

已验证：

- 本地 macOS 测试：`21 passed in 1.22s`。
- N100 Linux 测试：`21 passed in 2.06s`。
- 真实 UnicodeData 导入：`40,569` glyph records。
- 真实 Unihan_Readings 导入：`291,227` properties。
- 真实 Unihan_DictionaryLikeData 导入：`156,251` properties。
- SQLite 查询 `铝` 1000 次：P95 约 `0.17ms`。

说明：

- 当前性能数据基于本地 SQLite 和单机测试。
- 未做多 Agent 并发压测。
- 未做 PostgreSQL/pgvector 测试。

## 当前限制

v0.1.0-alpha 仍有明确边界：

- 不是通用多语言词典。
- 尚未导入 Wiktionary 或 CLDR。
- 尚未实现 `term` API。
- 尚未实现 batch normalize。
- 尚未实现私有领域词典导入器。
- 尚未实现语义图谱和语义计算。
- MCP server 是最小 stdio 实现，尚未做完整客户端兼容矩阵。
- 私有 namespace 不是权限系统。

## 下一步路线

建议 v0.2.0 优先实现：

1. `omniglyph lookup` CLI。
2. `POST /api/normalize/batch`。
3. MCP `normalize_tokens` 工具。
4. Private Domain Pack CSV/JSONL 导入。
5. `GET /api/v1/term?text=...`。
6. 跨境建材询盘 normalization demo。
7. CLDR ingestion。

这样 OmniGlyph 将从“字符级防幻觉”升级为“行业术语级防幻觉 + Agent 上下文压缩器”。

## 发布结论

OmniGlyph v0.1.0-alpha 已达到 alpha 发布标准：

- 有明确许可证。
- 有数据源合规说明。
- 有发布清单。
- 有完整测试。
- 有真实 Unicode/Unihan 数据验证。
- 有 Docker/N100 验证。
- 有 API 和 MCP 工具接口。

适合发布为：

```text
v0.1.0-alpha: Local symbol ground truth layer for AI agent evaluation.
```

不建议标记为 production/stable。
