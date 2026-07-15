# OmniGlyph 全项目发布安全加固收尾报告

## Executive Summary（执行摘要）

本轮对 OmniGlyph `0.8.0b0` 源码候选进行了全项目审查和发布安全加固。
项目原有发布基线健康，审查开始时已有 189 项测试通过，Ruff、mypy、隐私扫描、
构建、产物审计、独立 wheel 验证和演示流程均正常。本轮没有扩展产品功能，重点修复
了测试未覆盖的数据一致性、事务原子性、来源文件完整性、策略歧义、DLP 输出稳定性
和 MCP JSON-RPC 边界问题。

最终结果：新增 15 个回归测试，共 204 项测试通过；完整发布门禁通过；公开 API、
CLI 命令、17 个 MCP 工具、数据库表结构和产品定位保持不变。当前分支已达到新的
源码发布候选质量门槛，但本轮没有执行 TestPyPI、PyPI、MCP Registry、标签、推送或
生产部署。

## Scope and Baseline（范围与基线）

审查范围包括：

- `src/omniglyph/` 下 22 个 Python 源文件；
- API、CLI、MCP、SQLite repository、Unicode/Unihan/领域词库导入；
- Policy Pack、参数模式、输出 guardrail、Language Security Gateway；
- 测试、发布脚本、隐私扫描、构建配置、产物审计和维护文档；
- 当前 `0.8.0b0` wheel、sdist、MCP smoke 和跨境业务演示路径。

基线证据：

- Python 测试：189 项通过；
- Ruff：通过；
- mypy：22 个源文件通过；
- 隐私扫描：通过；
- 完整 `scripts/release_check.sh`：通过；
- MCP 工具数：17；
- 工作区：审查开始时干净。

项目不存在 Web 前端或其他 UI 表面，因此本轮没有引入 UI 框架或视觉改动。

方法说明：任务先经过 `safe-agent-router`。路由器选择了可信的
`data-analysis-report` 场景包及 `data-quality-audit`、`research-source-check`、
`execution-file-batch` 等方法指导；该结果对代码项目的分类并不精确，因此仅采用其
来源盘点、工作区边界、证据记录和质量审计要求。设计与实施使用
`design-md-ui`（确认无 UI 范围）、`brainstorming`、`writing-plans`、
`executing-plans` 和 `test-driven-development` 工作流。

## Findings Resolved（已解决问题）

| 严重度 | 问题 | 影响 | 处理结果 |
| --- | --- | --- | --- |
| 高 | `--replace-namespace` 先提交删除，再单独写入新数据 | 新数据序列化或数据库写入失败时，已验证的旧命名空间可能丢失 | 删除、来源登记、条目和别名写入改为一个 SQLite 事务；异常时完整回滚 |
| 高 | 下载直接写入正式目标文件，完成后才校验 SHA-256 | 哈希不匹配或下载中断会覆盖已验证文件，留下不可信或不完整内容 | 改为同目录临时文件，校验成功后原子替换；失败时保留旧文件并清理临时文件 |
| 中 | `glyph_property` 唯一约束包含可空 `language` | SQLite 对 `NULL` 的唯一性语义允许完全相同的属性重复导入 | 属性 ID 改为基于完整来源身份的 UUID5，重复导入保持幂等 |
| 中 | 先导入 Unihan、后导入 UnicodeData 时只更新时间 | glyph 的 Unicode 名称可能长期保持空值，结果取决于导入顺序 | upsert 仅在现有名称为空时补入 Unicode 名称 |
| 中 | Policy Pack 允许重复 `intent_id` | 首条匹配使有效策略依赖 CSV 行顺序，存在策略歧义 | 校验器拒绝重复 ID，并报告首次定义行和重复行 |
| 中 | 参数枚举直接使用 Python 相等语义 | `True == 1` 可让布尔值错误通过数字枚举 | 改为 JSON 类型感知的递归比较；布尔与数字分离，`1` 与 `1.0` 保持数值等价 |
| 中 | MCP 对非法顶层 JSON、版本和容器缺少统一校验 | 可能抛出属性异常、返回错误码不一致，并向客户端泄漏内部异常文本 | 增加 JSON-RPC 信封、`params`、`arguments` 校验；内部错误保留请求 ID 且隐藏异常细节 |
| 低 | DLP 部分重叠或相邻命中分别渲染占位符 | 同一敏感区间可能输出多个 `[REDACTED]`，降低结果稳定性 | 渲染前合并重叠和相邻区间，原始 finding 偏移与哈希保持不变 |

## Implementation（实施摘要）

- `e748dff`：确定性属性 ID 和与导入顺序无关的 Unicode 名称补全；
- `25bc1c8`：命名空间替换的单事务 repository 路径；
- `b740843`：临时下载、哈希校验和原子目标替换；
- `1807830`：重复 Policy Pack intent 拒绝和 JSON 枚举类型比较；
- `6ea81b9`：DLP 区间合并；
- `70a4250`：MCP JSON-RPC 边界校验与通用内部错误；
- `b646d00`、`22f0a73`：确认后的设计规格和实施计划。

所有行为修复均先添加回归测试并观察预期失败，再做最小实现并复测。新增测试分布：

- repository：3 项；
- source download：2 项；
- Policy Pack：1 项；
- parameter schema：1 项；
- DLP：2 个参数化场景；
- MCP：6 项。

## Verification Evidence（验证证据）

2026-07-16 最终验证：

```text
.venv/bin/python -m pytest -q
204 passed in 1.95s

.venv/bin/python -m ruff check .
All checks passed!

.venv/bin/python -m mypy src
Success: no issues found in 22 source files

bash scripts/privacy-scan.sh
exit 0, no findings
```

完整发布门禁：

```text
PATH=.venv/bin:$PATH bash scripts/release_check.sh
204 passed in 1.81s
Ruff: pass
mypy: pass
git diff --check: pass
MCP smoke: 17 tools available
Build: omniglyph-0.8.0b0.tar.gz and omniglyph-0.8.0b0-py3-none-any.whl
Twine metadata check: pass
Artifact audit: pass
Clean-wheel CLI/MCP smoke: pass
Cross-border demo: pass
```

测试和产物只在获准工作区及临时目录内生成，没有上传私有数据，也没有使用生产凭据。

## Compatibility（兼容性）

- API 路径、请求模型和主要响应结构未改变；
- CLI 命令和参数未改变；`--replace-namespace` 只增强失败回滚语义；
- MCP 工具名称与数量保持 17 个，合法请求行为不变；
- SQLite 表和索引结构未改变，无破坏性迁移；
- 现有数据不被自动重写或删除；
- 新下载成功后的 `SourceArtifact` 字段保持不变；
- DLP finding 数量、偏移和哈希不变，仅合并最终脱敏文本中的连续占位符。

MCP 对缺失或错误 `jsonrpc`、非字符串 method、非对象 `params`/`arguments` 的处理
更严格。这属于协议正确性修复，依赖非法请求被宽松接受的调用方需要修正请求格式。

## Remaining Risks（剩余风险）

- 现有数据库中已经产生的重复 glyph 属性不会自动去重；本轮只保证后续相同导入幂等。
- 原子下载使用同文件系统 `replace`，但未增加文件和目录 `fsync`；极端掉电持久性不在本轮范围。
- 下载入口没有新增域名 allowlist；调用者仍需控制 URL 和预期 SHA-256。
- MCP 仍不支持 JSON-RPC batch，也没有认证和授权；应继续只在受信本地环境运行。
- API 没有新增请求体大小限制；面向不受信网络前仍需由反向代理或宿主设置限制。
- Policy Pack 的 `parameters_schema` 仍是明确记录的 JSON Schema 子集，未知关键字继续忽略。
- DLP 自定义 secret term 仍为大小写敏感的字面匹配，完整 DLP 产品能力不在当前 beta 范围。
- Unicode confusables 仍使用最小规则包，完整 Unicode confusables 数据导入仍是后续工作。
- 本轮使用 fixture、示例和构建产物验证，没有重新下载和全量导入上游 Unicode/Unihan 数据集。
- 社区采用度、生产级多租户安全和外部审批工作流仍未解决。

## Publication Boundary（发布边界）

本轮完成的是本地源码分支的审查、修复、测试、构建和收尾记录。以下操作均未执行：

- 未推送当前提交到远程；
- 未创建或推送 Git 标签；
- 未上传 TestPyPI 或 PyPI；
- 未更新 MCP Registry；
- 未部署 API、MCP server 或数据库；
- 未修改任何生产数据、凭据或外部系统。

后续如进入发布流程，应继续按照 `docs/ecosystem/pypi-publish.md` 先发布到
TestPyPI，验证独立安装和 CLI/MCP 行为后，再在明确批准下进入 PyPI 和 MCP Registry。
