# 万象文枢与言法界枢优化改进实施计划

> **供执行代理使用：** 实施时使用 `superpowers:subagent-driven-development` 或 `superpowers:executing-plans`，按任务逐项推进。以下复选框记录未来实施状态；编写本计划不代表修复已经完成。

**目标（Goal）：** 关闭审查报告中的 13 项工程发现，修正言法界枢的 2 项设计问题，形成保留现有数据与词条 ID、可验证且可恢复的改进版本。

**架构（Architecture）：** 沿用现有 Python、SQLite、CLI、FastAPI 和 MCP 架构。修复放在各自的核心模块，接口层负责输入及错误转换；校验、预览和导入共享同一份已解析数据。历史数据修复独立于日常服务启动，先在副本上演练。

**技术栈（Tech Stack）：** Python 3.10+、SQLite、FastAPI/Pydantic、stdio JSON-RPC、pytest、Ruff、mypy、setuptools/build、Twine、GitHub Actions。

---

## 1. 已确认的约束

- 用户没有固定期限：按照风险、依赖和验收结果推进，不以日期代替完成标准。
- 保留现有数据与旧词条 ID；恢复、重导入和兼容性检查先在数据库副本上进行。
- 依据：[2026-09-08 中文审查报告](../../../PROJECT_REVIEW_2026-09-08.zh-CN.md)，审查基线为 `6088546` / `0.8.0b0`。
- 此前基线为 263 项测试通过；这只是历史实测记录。实施前重新记录实际基线，新增回归测试后记录实际数量。
- 本次交付为计划文档。实施任务、数据库修复、提交、合并、包发布和部署均未执行。
- 本轮以现有接口和业务流程为基础；无效输入拒绝得更严格，属于需要记录的兼容性变化。

## 2. 路线选择与阶段

采用“分阶段加固 + 独立历史数据修复”的路线。仅修复三个高风险问题可以较快降低风险，但无法解决策略误判和发布检查缺口；整体重写则会扩大兼容与验证成本。现有模块已经具备事务、来源记录和测试基础，分批修复更适合当前代码规模。

| 阶段 | 交付内容 | 前置依赖 | 退出条件 |
| --- | --- | --- | --- |
| A：控制高风险 | T0 基线与恢复准备；T1 本地部署默认值；T2 导入校验；T3 Unicode 区间 | T0 为实施起点 | 无效替换不丢数据；32,164 字符样本完整；默认端口仅绑定本机 |
| B：核心行为加固 | T4 词条身份与重复项；T5 策略参数；T6 包文件边界；T7 DLP | T4、T6 依赖 T2；其余可在独立分支开展 | 审查复现样本全部有明确预期；有效输入兼容测试通过 |
| C：验证与旧库恢复 | T8 CI 与安装包验证；T9 历史数据审计及恢复演练 | T8 可提前准备，最终验证等待 A/B；T9 依赖 T2/T3/T4 | 新旧数据兼容、恢复演练、安装包实际调用均通过 |
| D：发布材料与设计收敛 | T10 状态文档与 LogosGate 设计修订；T11 候选版本验收 | 设计文档可提前修订；版本验收等待 A/B/C | 每条发现有修复、证据及剩余限制；候选产物与提交一致 |
| E：受控试点 | T12 一个宿主工作流的效果评估 | T11 验收通过 | 真实动作约束、误报漏报、延迟都有可追溯结果 |

**并行边界：** `lexicon_pack.py`、`repository.py` 的 T2/T4 由同一数据模块负责人顺序整合；T6 在 T2 的加载契约稳定后接入。R4/R12 同属 `language_security.py`，合并为 T7，避免两轮正则修改互相覆盖。T5 也涉及该文件，与 T7 顺序合入。T1 可独立完成，T8 的 CI 准备可并行。

## 3. 问题到任务的映射

| 审查项 | 对应任务 | 核心验收证据 |
| --- | --- | --- |
| R1 无效替换清空词库 | T2、T9 | 原词条、别名、来源记录在拒绝或失败后保持一致 |
| R2 Unicode 区间缺失 | T3、T9 | 区间数量、内部字符、名称与来源、旧端点伪名称修复 |
| R3 默认 API 暴露 | T1 | Compose 解析结果和本机监听检查 |
| R4 中文相邻 DLP 漏检 | T7 | 中文、英文、标点相邻的同一测试凭据一致被发现 |
| R5 重复策略表头 | T5 | 重复授权列被拒绝，不能以后一列覆盖前一列 |
| R6 包内符号链接越界 | T6 | 外部真实路径被拒绝；合法内部路径保持可用 |
| R7 NaN 绕过数值限制 | T5 | 核心、CLI、HTTP、MCP 均不产生允许决策 |
| R8 词条 ID 碰撞 | T4、T9 | 两条事实独立，别名正确，已存在 ID 保持稳定 |
| R9 大小写重复导致外键错误 | T4 | 等价项可合并，冲突项被拒绝，外键检查为空 |
| R10 输出策略类型导致 500 | T5 | 无效动作值按既有约定回退为 block 并给出警告 |
| R11 非对象元数据导致 500 | T2 | 错误 JSON 值类型返回结构化失败 |
| R12 DLP 平方级耗时 | T7 | 无 @ 和含 @ 的对抗样本均无平方级增长趋势 |
| R13 发布验证缺口 | T8、T11 | CI 检查本次实际产物，覆盖工具清单及安装后的行为 |
| 当前状态文档漂移 | T10、T11 | 日期、提交、版本、测试结果集中在同一入口 |
| D1 全文允许短语豁免 | T10、T12 | 文本中的允许短语不能取消结构化动作的拒绝决定 |
| D2 review 默认继续执行 | T10、T12 | 无可信审批时实际执行次数为 0 |

## 4. 文件与职责

| 文件 | 计划职责 |
| --- | --- |
| `src/omniglyph/domain_pack.py` | 共用 CSV 行解析与校验，保留可选列默认值 |
| `src/omniglyph/lexicon_pack.py` | 一次读取与校验产生导入快照；元数据类型与词条一致性 |
| `src/omniglyph/cli.py` | 校验、预览、导入共用结果；错误映射；禁止空替换 |
| `src/omniglyph/repository.py` | 事务边界、自然键定位、旧 ID 复用、正确关联别名、区间来源 |
| `src/omniglyph/normalizer.py` | Unicode First/Last 配对、区间展开、区分原始标记与字符名称 |
| `src/omniglyph/policy_pack.py` | 重复表头与策略数据校验 |
| `src/omniglyph/parameter_schema.py` | 有限数值校验，保持已声明的模式子集 |
| `src/omniglyph/guardrail.py` | 输出策略值类型及回退行为 |
| `src/omniglyph/language_security.py` | DLP 边界与扫描复杂度，非法参数失败响应 |
| `src/omniglyph/api.py`、`src/omniglyph/mcp_server.py` | 请求拒绝、错误码和已解析文件路径传递 |
| 新增 `src/omniglyph/pack_paths.py` | 两种数据包共用的文件真实路径解析与目录限制 |
| 新增 `src/omniglyph/json_input.py` | CLI/MCP 的严格 JSON 解析；API 对非有限值采用同等拒绝规则 |
| `docker-compose.yml`、`docs/quickstart.md`、`docs/security/mcp-safety.md` | 本地监听默认值与远程部署条件 |
| `scripts/release_check.sh`、`scripts/mcp_smoke_test.sh`、`scripts/wheel_smoke_test.sh` | 与 CI 共用的发布及安装验证 |
| 新增 `scripts/benchmark_dlp.py` | 有固定输入、预热及重复次数的扫描基准 |
| 新增 `scripts/audit_legacy_data.py`、`scripts/repair_legacy_data.py` | 显式旧库审计；根据可信原始来源修复数据库副本 |
| `.github/workflows/test.yml`、`pyproject.toml` | 测试版本矩阵、安装验证所需依赖与检查配置 |
| `tests/test_*.py` 与新增专项测试 | 各任务对应的失败复现、修复验证和兼容验证 |

新增模块仅用于共用文件边界与 JSON 解析；不在本轮拆分现有 API/MCP 架构或引入新的服务层。

## 5. 实施任务

### T0：记录基线，建立数据库恢复准备

负责：实施者与复核者。依赖：无。

- [ ] 记录当前提交、工作区差异、Python 版本、已有发布产物版本；保留用户现有文件。实施代码在隔离分支中进行，文档编写不要求迁移当前工作区。
- [ ] 将运行测试的 `OMNIGLYPH_DATA_DIR`、`OMNIGLYPH_SQLITE_PATH` 显式指向新临时目录，记录首次全量测试结果。
- [ ] 对需要演练的已有数据库，使用 SQLite backup API 创建一致副本；不直接复制仍在使用的 WAL 主文件。备份失败则终止演练。
- [ ] 在副本上执行 `PRAGMA integrity_check` 和 `PRAGMA foreign_key_check`，记录词条、别名、来源记录数量。备份和原始私有词包保存在受控本地位置，不进入 Git 或发行包。

基线命令，在配置好的临时数据库环境中执行：

```bash
git rev-parse HEAD
git status --short
.venv/bin/python --version
.venv/bin/python -m pytest -q
.venv/bin/python -m ruff check .
.venv/bin/python -m mypy src
```

退出标准：已知哪些结果来自当前基线；存在可读取的恢复副本；后续测试不会误用实际词库。

### T1：将默认部署限定在本机（R3）

修改：`docker-compose.yml`、`docs/quickstart.md`、`docs/security/mcp-safety.md`。

- [ ] 将宿主机映射改为如下内容；容器内部仍监听 `0.0.0.0:8000`，保证容器端口转发可用。

```yaml
ports:
  - "127.0.0.1:8000:8000"
```

- [ ] 在文档中明确：远程访问需要单独配置认证入口、TLS 和请求限制。不能把“绑定本机”描述为已经实现 API 身份认证。
- [ ] 执行 `docker compose config --format json`，检查 `services.api.ports` 的 `host_ip` 为 `127.0.0.1`；在隔离环境启动后检查监听地址，并访问健康接口。
- [ ] 验证现有本地 CLI/MCP 工作流不受影响，复核后单独提交部署默认值变更。

退出标准：默认配置不在宿主机全部接口发布服务。没有 Docker 环境时记录未完成运行验证，不将文档检查等同于部署验证。

### T2：统一词包校验并保护替换导入（R1、R11）

修改：`domain_pack.py`、`lexicon_pack.py`、`cli.py`、`repository.py`；测试：`tests/test_domain_pack.py`、`tests/test_lexicon_pack.py`、`tests/test_repository.py`、`tests/test_api.py`、`tests/test_mcp.py`；新增 `tests/test_cli_ingestion.py`。

- [ ] 增加失败用例：`pack.json` 为 `[]` 或 `null`；词条缺少必填字段；错误 traits；CSV 多列、重复表头；只有表头的空包；目标命名空间不一致；写入中途异常。
- [ ] 在已存 `FOB` 和别名的临时库中运行这些替换用例，断言拒绝后词条、别名、来源数量与内容均保持原样。
- [ ] 将读取、解析、校验收敛为一次准备操作：同一份原始内容生成解析结果、错误列表及 SHA-256。校验返回报告，加载与导入遇错抛出 `ValueError`；预览使用同一结果。不能先校验一次，再重新读取另一份文件用于导入。
- [ ] 在核心替换入口写入前，检查条目非空且命名空间一致。空输入不承担清空语义；保留已有显式删除方法用于有意删除。有效替换仍使用现有单事务操作。
- [ ] 元数据对象类型检查先于 `.get()`；CSV 校验先于转换。保留现有可选列默认值，在规格中明确前三列必填，避免无关格式升级。

替换入口的关键断言：

```python
entries = list(entries)
if not entries:
    raise ValueError("replacement entries must not be empty")
if any(entry.namespace != namespace for entry in entries):
    raise ValueError("replacement entries must match namespace")
```

验证命令：

```bash
.venv/bin/python -m pytest -q tests/test_cli_ingestion.py tests/test_domain_pack.py tests/test_lexicon_pack.py tests/test_repository.py tests/test_api.py tests/test_mcp.py
```

退出标准：校验、预览、导入接受或拒绝相同输入；校验失败返回结构化报告；导入失败非零退出；原数据不受影响。复核通过后提交这一组变更。

### T3：修复 Unicode 区间与来源表示（R2）

修改：`normalizer.py`、`repository.py`、`cli.py`；测试：`tests/test_normalizer.py`、`tests/test_repository.py`、`tests/test_cli_ingestion.py`；新增样本 `tests/fixtures/UnicodeData.ranges.txt`。

- [ ] 加入真实格式的 CJK 与 Hangul First/Last 片段，运行失败测试，记录当前只产生 4 条的结果。
- [ ] 解析时保存待配对的 First 行，检查标签、范围方向及相关字段一致性；配对成功后流式展开闭区间。代理码点不入库，码点越界及缺失 Last 不允许静默形成成功的完整导入。
- [ ] 原始区间标记作为来源属性保存，与 `glyph_node.name` 分离。普通显式名称继续保留；本轮没有可靠名称依据的展开字符使用 `null`，不把 `<..., First>` 当成名称，也不把宿主 Python 的 Unicode 名称版本冒充导入文件版本。
- [ ] 即使名称为 `null`，查询仍必须返回该字符所属区间及其来源快照。利用现有 `glyph_property` 保存区间来源，不需要为此替换数据库结构。
- [ ] 为端点、中间字符、扩展区、私用区、代理区、错误配对和普通单字符样本增加断言；保留已有有效名称及 Unihan 信息。

主数量样本 `tests/fixtures/UnicodeData.ranges.txt` 使用以下四行；异常与扩展区样本放入单独测试输入，避免改变该样本的数量断言：

```text
4E00;<CJK Ideograph, First>;Lo;0;L;;;;;N;;;;;
9FFF;<CJK Ideograph, Last>;Lo;0;L;;;;;N;;;;;
AC00;<Hangul Syllable, First>;Lo;0;L;;;;;N;;;;;
D7A3;<Hangul Syllable, Last>;Lo;0;L;;;;;N;;;;;
```

关键回归：

```python
from pathlib import Path
from omniglyph.normalizer import parse_unicode_data


def test_unicode_ranges_include_interior_characters():
    records = list(parse_unicode_data(Path("tests/fixtures/UnicodeData.ranges.txt")))
    by_codepoint = {record.unicode_hex: record for record in records}
    assert len(records) == 32164
    assert "U+94DD" in by_codepoint
    assert "U+AC01" in by_codepoint
    assert by_codepoint["U+4E00"].basic_definition != "<CJK Ideograph, First>"
```

验证命令：`.venv/bin/python -m pytest -q tests/test_normalizer.py tests/test_repository.py tests/test_cli_ingestion.py tests/test_unihan.py`。

退出标准：32,164 条样本完整，内部字符可查询，来源不丢失。标准字符名称的进一步补全列为后续独立数据源工作，使用同版本官方 `DerivedName.txt` 并记录版本、许可与哈希；不将该补全描述为本轮已完成。

### T4：稳定词条身份、旧 ID 与别名关系（R8、R9）

修改：`repository.py`、`domain_pack.py`、`lexicon_pack.py`；测试：`tests/test_repository.py`、`tests/test_lexicon_pack.py`；新增 `tests/test_legacy_data.py`。

- [ ] 为冒号字段边界碰撞、`FOB/fob`、重复重导入、旧算法 ID 与新增别名创建失败测试。
- [ ] 将现有规范化规则 `casefold + 首尾及重复空白处理` 共用于校验与存储，不引入新的语言归一化策略。
- [ ] 使用现有唯一约束对应的自然键：`namespace、normalized_term、canonical_id、source_id`。先按该键查询，存在则复用实际 `id`；仅新记录采用带版本标记的结构化 UUID 输入。

```python
identity = json.dumps(
    ["omniglyph:lexical:v2", entry.namespace, normalized_term, entry.canonical_id, source_id],
    ensure_ascii=False,
    separators=(",", ":"),
)
new_entry_id = str(uuid.uuid5(uuid.NAMESPACE_URL, identity))
```

- [ ] 如果并发插入遇到自然键冲突，重新读取数据库中的实际行 ID，别名始终关联实际 ID。不能只改 UUID 公式而保留“忽略插入后仍使用新 ID”的流程。
- [ ] 显式整包替换也需要保留旧 ID：在同一事务中删除旧数据前，保存旧词条映射。先按完整自然键匹配；来源版本改变时，按 `namespace、normalized_term、canonical_id` 匹配唯一旧词条，复用 ID 并登记新来源。存在多个候选时拒绝替换并报告歧义，不能按排序任取一条。新增词条才生成新 ID；有意移除的词条保留在恢复副本中。
- [ ] 对同一自然键，语言、定义、traits、敏感级别、审核状态和包元数据均相同的变体合并别名；事实字段冲突则拒绝整个输入，不能静默保留先到的数据。
- [ ] 明确计数为“去重后有效逻辑词条数”；重复导入可报告处理了该词条，但不能把同一逻辑项报成多条实际记录。
- [ ] 运行原 ID 保持、别名归属、幂等和外键检查；复核后单独提交身份兼容变更。

验证命令：`.venv/bin/python -m pytest -q tests/test_repository.py tests/test_lexicon_pack.py tests/test_legacy_data.py`。

退出标准：碰撞样本是两条独立事实；等价大小写变体合并成功；冲突明确失败；普通重导入和整包替换均不改变可确认的旧 ID；`PRAGMA foreign_key_check` 返回空结果。历史错误别名的修复交给 T9，不在服务启动时猜测修正。

### T5：统一策略与数值拒绝行为（R5、R7、R10）

修改：`policy_pack.py`、`parameter_schema.py`、`guardrail.py`、`language_security.py`、`cli.py`、`api.py`、`mcp_server.py`；新增 `json_input.py`；测试：`tests/test_policy_pack.py`、`tests/test_parameter_schema.py`、`tests/test_guardrail.py`、`tests/test_language_security.py`、`tests/test_api.py`、`tests/test_mcp.py`、`tests/test_cli_product_tools.py`。

- [ ] 添加重复 `decision`、`allowed_roles`、`requires_approval` 表头测试，要求在构造行字典前拒绝。
- [ ] 添加 NaN、正负无穷及有效上下界测试。数值校验使用已有 `_is_finite_number` 语义；不扩大轻量级 JSON Schema 的支持范围。
- [ ] 为 CLI/MCP 增加严格 JSON 解析：拒绝 `NaN`、`Infinity`、`-Infinity`，对 `1e999` 解析成无穷的情况同样拒绝。API 在进入业务逻辑前执行相同的有限值规则。
- [ ] 保证失败响应本身可严格序列化。核心拒绝非法数值时，`parameter_findings` 保留字段路径，响应的 `parameters` 使用空对象，不能再次回显 NaN 导致输出失败。
- [ ] 输出 guardrail 先检查动作类型，再执行允许值检查；维持既有“无效动作回退 block，并给出警告”的约定。

```python
if not isinstance(value, str) or value not in ALLOWED_ACTIONS:
    warnings.append(f"{key} must be one of allow, block, review; using block.")
    value = "block"
```

核心数值回归：

```python
import pytest
from omniglyph.parameter_schema import validate_parameters


@pytest.mark.parametrize("amount", [float("nan"), float("inf"), -float("inf")])
def test_nonfinite_amount_is_rejected(amount):
    schema = {
        "type": "object",
        "properties": {"amount": {"type": "number", "minimum": 0, "maximum": 100}},
        "required": ["amount"],
    }
    findings = validate_parameters({"amount": amount}, schema)
    assert findings
    assert any(item["path"] == "$.amount" for item in findings)
```

接口验收契约：

| 输入问题 | 核心行为 | CLI | HTTP API | MCP |
| --- | --- | --- | --- | --- |
| 重复策略表头 | 校验失败，加载抛 ValueError | 退出 2 | 加载策略时 400 | 调用参数错误 -32602 |
| 非标准 JSON 数值常量 | 解析拒绝 | 退出 2 | 400 | 解析错误 -32700 |
| 合法 JSON 数值溢出为无穷 | 数值拒绝，不返回 allow | 退出 2 | 422 | 参数错误 -32602 |
| Python 直接传入非有限参数 | block / invalid_parameters，响应可序列化 | 不适用 | 不适用 | 直接调用处理函数时返回拒绝证据 |
| 输出策略动作值为数组或对象 | 该类别动作回退 block，并附 policy_warnings | 输出策略报告 | 200，返回策略报告 | 正常工具响应，返回策略报告 |

最后一行的 `decision=block` 验收使用确实包含对应类别的输入，例如数组值 `unknown_action` 配合未知词条。全部词条均为已批准普通词条时，不因未使用类别的配置错误扩大拦截范围。

- [ ] 执行以下命令，验证正常角色、批准标志、嵌套参数、数值枚举与既有未知关键字行为保持一致。

```bash
.venv/bin/python -m pytest -q tests/test_policy_pack.py tests/test_parameter_schema.py tests/test_guardrail.py tests/test_language_security.py tests/test_api.py tests/test_mcp.py tests/test_cli_product_tools.py
```

- [ ] 审核错误码和文档后，将表头、数值及输出策略修复分别提交，便于独立回退。

### T6：将目录限制落实到实际打开的包文件（R6）

修改：新增 `pack_paths.py`；修改 `lexicon_pack.py`、`policy_pack.py`、`api.py`、`mcp_server.py`；测试：`tests/test_lexicon_pack.py`、`tests/test_policy_pack.py`、`tests/test_api.py`、`tests/test_mcp.py`。

- [ ] 先复现“外部目录直接被拒绝，但内部子文件链接可访问外部”的 HTTP/MCP 场景。
- [ ] 共用解析函数逐一处理允许的固定文件名；解析真实路径、检查根目录包含关系，并返回已经确认的文件路径。加载器必须读取返回路径，不能重新使用未经检查的原路径。
- [ ] 合法内部符号链接可用，指向根外的链接拒绝。缺失文件仍按校验失败处理，越界 API 返回 403，MCP 返回 -32602；未配置根目录时保留当前受信本地行为。
- [ ] 覆盖内部链接、外部链接、断链、相对路径、根目录本身和路径前缀相似的兄弟目录。
- [ ] 文档明确允许目录必须由宿主保护。普通路径解析不等价于抵御攻击者并发替换文件；如果部署允许不受信主体写包目录，应使用不可变快照或额外的文件描述符级约束。

验证命令：`.venv/bin/python -m pytest -q tests/test_lexicon_pack.py tests/test_policy_pack.py tests/test_api.py tests/test_mcp.py`。

退出标准：没有已复现的静态符号链接逃逸；有效本地包仍可加载；边界能力的描述不超过实际实现。

### T7：修复多语言 DLP 并控制扫描复杂度（R4、R12）

修改：`language_security.py`；新增 `scripts/benchmark_dlp.py`；测试：`tests/test_language_security.py`、`tests/test_api.py`、`tests/test_mcp.py`。

- [ ] 使用人工构造密钥、AWS 标识和 `example.com` 邮箱建立英文、中文、标点、换行及前后相邻字符测试；同时覆盖不应命中的普通文本。
- [ ] 使用符合各凭据字符集的显式边界替换泛化的 Unicode `\b`。保留现有规则 ID、原文偏移、哈希及合并脱敏区间行为。
- [ ] 邮箱扫描采用有界候选识别：ASCII 候选片段只扫描一次，对地址总长度最多 254 字符、本地部分最多 64 字符、域标签最多 63 字符的候选进行验证。超长无效候选整段跳过，不从每个内部字符重启无界匹配；处理句末标点并保留原文偏移。长度边界及现有 ASCII 邮箱覆盖范围写入检测规则文档。
- [ ] 对包含 @ 和不包含 @ 的长文本都做回归。仅加入“没有 @ 就提前返回”不能完成 R12 修复。

多语言关键回归：

```python
import pytest
from omniglyph.language_security import scan_output_dlp


@pytest.mark.parametrize("prefix", ["Key: ", "密钥", "密钥：", "\n"])
def test_key_is_detected_after_multilingual_labels(prefix):
    value = "sk-proj-abcdefghijklmnopqrstuvwxyz123456"
    report = scan_output_dlp(prefix + value)
    assert report["decision"] == "block"
    assert value not in report["redacted_text"]
    assert any(item["rule_id"] == "dlp-api-key" for item in report["findings"])
```

- [ ] 基准脚本接受 `--sizes 8192 16384 32768 65536 131072 --repeat 7`，预热后报告中位耗时、P95、Python/系统信息、输入长度及命中数。包括重复 `a.`、长域名、密集 @ 和正常中英文文本。
- [ ] 参考验收目标为相邻输入翻倍时，中位耗时比例不持续超过 3。对接近计时噪声的样本增加批量重复；采用相同环境前后比较，不把一次 CI 的绝对毫秒值当通用承诺。

验证命令：

```bash
.venv/bin/python -m pytest -q tests/test_language_security.py tests/test_api.py tests/test_mcp.py
.venv/bin/python scripts/benchmark_dlp.py --sizes 8192 16384 32768 65536 131072 --repeat 7
```

退出标准：原始漏检样本均发现并脱敏；有效既有样本不退化；对抗输入不再表现出原来的平方级增长，保留基准输出供复核。

### T8：让 CI 验证实际发布产物（R13）

修改：`.github/workflows/test.yml`、`scripts/release_check.sh`、`scripts/mcp_smoke_test.sh`、`scripts/wheel_smoke_test.sh`、`tests/test_release_check.py`、`tests/test_artifact_audit.py`；新增 `scripts/installed_smoke.py`、`tests/test_installed_package.py`。

- [ ] 源码测试矩阵覆盖 Python 3.10、3.11、3.12；Ruff/mypy 使用一个明确版本运行即可。项目继续声明更广泛版本支持前，应补充对应版本证据。
- [ ] 在同一发布任务中构建 sdist 和 wheel，再对本次生成的精确文件路径执行 Twine、artifact audit 和独立安装验证。产物路径从 `pyproject.toml` 版本解析，不能按文件名排序拿旧 wheel，也不能用历史 `dist/*` 混合结果证明本次构建。
- [ ] 保持本地和 CI 调用同一套检查脚本；构建所用工具版本记录在产物证据中。测试和构建的隔离目录通过路径参数传递。
- [ ] MCP 列表校验使用独立预期集合，包含全部 17 个工具及旧别名；检查名称唯一。用缺少 `validate_policy_pack` 的模拟响应证明脚本会失败，避免把运行时函数自己的输出同时当作期望值。
- [ ] 独立环境安装 wheel 及其运行依赖；源码目录外运行，移除测试进程的 `PYTHONPATH`。断言导入位置来自该环境，执行 CLI 导入/查询、MCP initialize/工具调用、HTTP 健康及术语查询。
- [ ] 为 HTTP smoke 安装所需测试客户端依赖，或使用临时本地服务与标准库 HTTP 客户端。由 smoke 管理进程退出，测试完成不留下服务。
- [ ] 将仅检查脚本文本的测试补充为实际成功和失败场景；本次产物缺失时发布任务必须失败。

退出标准：源码检查和安装产物检查各有独立证据；删除一个工具、缺少一个产物或破坏一个安装后调用都能触发检查失败。

### T9：审计并修复历史数据副本（R1、R2、R8、R9）

新增：`scripts/audit_legacy_data.py`、`scripts/repair_legacy_data.py`；修改：T4 已创建的 `tests/test_legacy_data.py` 及 `repository.py` 中可复用的事务与查询辅助方法。

- [ ] 用旧算法构造测试数据库，包含冒号碰撞后的缺失事实、错挂别名、旧区间端点伪名称，以及同命名空间不同来源的正常记录。
- [ ] 审计脚本接口为 `--database PATH --source PATH --source-kind {lexicon,unicode} --expected-sha256 SHA`，以只读连接生成 JSON 差异报告。裸 CSV 另需 `--namespace`；目录词包从元数据读取命名空间。输入、来源哈希、目标 source/namespace、受影响 ID、预计变更数量必须明确。
- [ ] 修复脚本使用同样的来源参数，并要求 `--output-database PATH`。输出必须是不存在的新路径，不提供默认原位覆盖；通过 SQLite backup API 从输入生成修复副本。
- [ ] 只根据哈希匹配的原始来源重建受影响的 source/namespace 数据。可确认身份的旧词条保留 ID，补回缺失事实，为其生成新 ID；根据原始包纠正该来源的别名关系，不删除同命名空间其他来源的数据。
- [ ] Unicode 修复只处理能确认由旧解析器产生的端点伪名称。先保留其原始区间来源，再设置有依据的名称或 null；不能依靠现有 `COALESCE` 自动纠正非空伪名称。普通名称、Unihan 和私有属性保持原样。
- [ ] 原始来源缺失、哈希不符或身份无法确认时，报告不可可靠恢复并停止该部分修复；不得猜测词义或别名归属。
- [ ] 验证修复后的完整性、外键、ID 稳定、查询结果及二次运行幂等。以旧副本恢复再验证，记录恢复步骤与结果。

验证命令：`.venv/bin/python -m pytest -q tests/test_legacy_data.py tests/test_repository.py tests/test_cli_ingestion.py`。

退出标准：既能展示修复后的数据，也能展示从备份恢复的结果。实际服务切换在维护窗口停止写入后进行；仅回退应用代码不能撤销已经修改的数据，版本与数据库副本需要成对管理。

### T10：修订当前状态文档及 LogosGate 设计（文档漂移、D1、D2）

修改：`docs/product/project-status.md`、`docs/product/v0.8-maintenance-log.md`、`README.md`、`README.zh-CN.md`、`docs/specs/lexicon-pack-standard.md`、`docs/specs/policy-pack-standard.md`、`docs/legal/data-sources.md`、`docs/superpowers/plans/2026-04-30-logosgate-mvp.md`、`言法界枢/项目思路.md`。

- [ ] 当前项目状态集中展示日期、提交、包版本、验证入口和限制；README 链接该入口。历史验收结果保留日期，不改写成新结果。
- [ ] 明确空替换拒绝、规范化重复合并、ID 兼容、区间名称为 null 的原因、严格数值输入及包文件边界。
- [ ] 删除拟议匹配器的“任何 allow_context 命中就让整条规则失效”逻辑。允许短语只作为对应文本片段的上下文证据，不能取消结构化动作策略的 block；无法可靠确定时进入 review。
- [ ] 拟议装饰器默认阻止 block 和 review。若未来实现人工审批，审批必须绑定实际意图、参数、策略版本及调用者，不能由模型提交 `approved=true` 自行获得放行。

设计中的默认值调整为：

```python
block_on: tuple[str, ...] = ("block", "review")
```

- [ ] 同步修订计划里的示例测试：引用“不要刷单”后再请求刷单不能获得 allow；未审批 review 时受保护函数的调用次数为 0。
- [ ] 明确当前没有实现 `omniglyph.logos`。本轮只修订设计，不将文档中的测试、装饰器和工具数量计入已实现能力。

退出标准：实施计划与产品说明对审批和执行的语义一致；当前状态有唯一入口；中文、英文主要说明无冲突。

### T11：完成候选版本验收与恢复说明

依赖：T1 至 T10 的对应修复与证据完整。新增 `docs/superpowers/reviews/2026-09-08-optimization-closeout.md`，该文件仅在实施完成时创建并记录实际日期。

- [ ] 在独立审查中逐条核对 R1-R13、D1-D2 与测试、配置或设计证据；不能只依据总测试数判断问题已关闭。
- [ ] 通过改进后的发布脚本一次完成全量测试、静态检查、构建和安装验收，不先单独重复运行脚本已经包含的同一组命令。完整检查通过后，只有新增代码、失败或未解疑点才触发相关复测。

```bash
bash scripts/release_check.sh
```

- [ ] 记录实际提交、版本、命令、产物 SHA-256、测试数量、旧库恢复证据及未验证项目。版本号在候选发布任务开始时按当时发布状态确定，不根据旧报告假定远程版本。
- [ ] 通过构建内容审计确认没有私有词包、数据库、备份或本地诊断文件进入发行包。
- [ ] 准备版本与数据库成对回退的操作说明。若恢复演练失败，不进入实际数据切换。
- [ ] 输出本地候选验收结果。包上传、远程部署与登记平台更新是后续发布动作，执行前依据届时明确的发布范围办理。

退出标准：所有高风险问题及本轮已确认的安全缺陷关闭，兼容与恢复检查通过；尚未覆盖的外部集成明确列出。达成该标准意味着本地候选合格，不代表通用安全产品认证。

### T12：通过一个真实宿主工作流验证产品价值

本任务是候选验收后的试点计划，实施范围在选定宿主时具体落定。优先复用现有 `enforce_intent_manifest` 和 Policy Pack，不先创建第二套独立策略引擎。

- [ ] 使用模拟报价交付动作作为首个本地演练：输入包含意图、角色、收件目标和结构化参数；宿主选择策略，模型仅提交动作请求。
- [ ] 记录实际执行计数：allow 时执行一次；block、review、解析失败和扫描异常时执行零次。请求中的执行参数必须与已检查参数一致。
- [ ] 建立固定评估集，至少覆盖正常报价、未知/未批准术语、秘密词、中文相邻凭据、权限不足、参数越界、引用禁令后要求违规及待审批动作。样本使用合成数据；实际业务样本另行脱敏和确认使用范围。
- [ ] 报告各类别样本量、误报数、漏报数、拒绝后实际执行数和端到端 P50/P95 延迟；标明模型、宿主、策略版本与硬件环境。已知绕过回归集要求漏过执行数为 0；不以小样本推导普遍安全率。
- [ ] 根据实测结果决定是继续增强现有 intent 能力，还是需要独立 LogosGate 执行适配器。独立产品化以真实宿主需求、稳定的执行约束和可测效果为依据。

## 6. 验收与发布检查清单

- [ ] 所有无效替换和中途异常都能保持原词库及来源记录。
- [ ] Unicode 区间数量、内部字符、原始来源及名称未知语义正确。
- [ ] 旧词条 ID 保持稳定，历史修复依据原始来源，数据库恢复演练成功。
- [ ] 默认本地部署不向全部宿主接口发布未认证服务。
- [ ] 重复表头、非有限数值、错误策略类型和包文件越界均不能产生不应有的 allow。
- [ ] 中文相邻凭据可以发现，DLP 对抗样本无原有平方级增长趋势。
- [ ] 全部 17 个 MCP 工具及安装后的 CLI/API/MCP 实际调用有检查证据。
- [ ] CI 覆盖明确支持的 Python 基线，并审计本次实际构建产物。
- [ ] LogosGate 文档中的 block/review 语义一致，未实现能力没有被计入当前版本。
- [ ] 收尾报告分别说明已通过、未通过和未执行的验证，不以旧结果代替新验收。

## 7. 执行管理

每个实现任务按“增加可复现测试 → 确认基线失败 → 最小修改 → 相关验证 → 独立复核 → 小范围提交”推进。纯文档和单行配置变更使用针对性的检查，不为凑测试数量增加重复测试。

同一模块的相关修复顺序合入；相互独立的模块可并行。未经验证的中间状态不跨任务扩散。任务完成后立即记录结果与提交，不能在最后一次性把全部复选框标成完成。

第一轮投入顺序为 T0、T1、T2、T3。T1 可独立完成，T2 是后续词库身份处理和历史恢复的基础。T8 的验证准备可以提前进行，但发布候选必须等待数据、安全与恢复验收通过。
