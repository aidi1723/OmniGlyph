# OmniGlyph 意图策略 Fail-Closed 加固收尾报告

## Executive Summary（执行摘要）

第二阶段完成了 Policy Pack 和 inline manifest 执行链的 fail-closed 加固。
审查确认，原实现的验证命令与实际加载路径相互独立：无效 Policy Pack 可以绕过
`validate_policy_pack()` 直接进入 CLI、API 或 MCP 执行；inline manifest 的未知
decision 和错误角色类型可以落入 allow 路径，畸形 intent 条目则会抛出运行时异常。

修复后，任何无效 Policy Pack 都无法加载，违反本阶段结构规则的 inline
manifest 返回 `decision: "block"` / `status: "invalid_manifest"`。合法 Python、
CLI、API 和 MCP 行为保持兼容。项目测试从第一阶段的 205 项增加到 229 项，
完整发布门禁通过。

## Root Cause（根因）

根因不是单个入口缺少 `try/except`，而是校验和执行使用了不同的数据路径：

- `validate_policy_pack()` 使用 `_validate_metadata()` 和 `_validate_intents()`；
- `load_policy_pack()` 直接使用 `_read_metadata()` 和 `_read_intents()`；
- CLI、API、MCP enforcement 都直接调用 loader；
- `enforce_intent_manifest()` 在 `_find_intent()` 前不验证 manifest 结构；
- 未识别的 decision 没有显式阻断分支，最终使用默认 `allow`；
- 字符串 `allowed_roles` 被 Python `in` 当作子串容器。

首轮实现后的独立审查又发现四个边界缺口：

- loader 在校验成功后重新打开文件，已加载内容可能不是已校验内容；
- 数组或对象 decision 会在 set membership 处抛出 `TypeError`；
- CSV 超出表头的值可能被忽略并让 pack 错误通过校验；
- API/MCP 会在核心校验前拒绝顶层非对象 manifest。

第二轮复审还发现，适配器无法区分 manifest 字段缺失与显式 JSON `null`，
导致 `null` 没有进入核心 fail-closed validator。

实际复现结果：

```text
decision="sometimes" -> decision="allow"
allowed_roles="admin", actor_role="min" -> decision="allow"
intents=[1] -> AttributeError: 'int' object has no attribute 'get'
duplicate Policy Pack intent_id -> load_policy_pack() succeeds
validated decision="review", replace file with "allow" -> loader returns "allow"
decision=[] -> TypeError: unhashable type: 'list'
valid row with an extra CSV value -> validation pass and enforcement continues
top-level manifest=[] -> API 422 / MCP -32602 instead of blocked evidence
manifest=null -> API 400 / MCP -32602 instead of blocked evidence
```

## Changes（变更）

### Core manifest boundary

- 新增依赖无关的 manifest validator；
- 校验顶层对象、policy、intents、intent 对象、非空 ID、唯一 ID、decision、
  requires_approval、allowed_roles 和 parameters_schema；
- decision 在枚举成员判断前先验证字符串类型；
- findings 使用稳定的 `path`、`rule`、`message` 结构；
- 任何 finding 在 intent 匹配前返回 block / invalid_manifest；
- 保留合法 inline manifest 省略 decision 的历史行为。

### Single-snapshot Policy Pack loader

- validator 和 loader 共用一次内部 inspection 的 metadata、intents 和 errors；
- loader 直接返回通过校验的解析对象，不再校验后重读文件；
- CSV 行超出表头的值统一视为校验错误；
- 非法字段、重复 ID、缺失列、错误 JSON 和无效 metadata 统一抛出带
  `invalid policy pack:` 前缀的 `ValueError`；
- 有效 `PolicyPack` 返回类型和 manifest 形状不变。

### Entry-point semantics

- CLI：argparse usage error，退出码 `2`，无 traceback；
- API policy path：HTTP `400`；
- MCP policy path：JSON-RPC `-32602`；
- API/MCP inline manifest：包括顶层非对象 JSON 值在内，调用正常返回阻断证据，
  不转成传输错误；
- API/MCP 使用字段存在性区分缺失与显式 `null`，后者进入核心阻断；
- MCP stdio 内部错误恢复测试改为显式 dispatcher 故障，不再依赖畸形 manifest。

## Commits（提交）

- `d225160`：第二阶段设计规格；
- `698c816`：第二阶段实施计划；
- `b5ba10e`：核心 inline manifest fail-closed 校验；
- `3885145`：严格 Policy Pack loader；
- `7133410`：CLI、API、MCP 错误语义与入口测试；
- `dcfc273`：补充独立审查后的设计约束；
- `7683b78`：补充独立审查后的实施计划；
- `15408f0`：拒绝非字符串 intent decision；
- `ad1878b`：加载同一已校验快照并拒绝 CSV 额外列；
- `120cbbc`：顶层非对象 inline manifest 进入核心校验；
- `1eb3508`：显式 `null` manifest 与字段缺失使用不同语义。

## Test Coverage（测试覆盖）

新增 24 个收集测试场景：

- 核心 manifest validator：13 个参数化非法结构场景；
- Policy Pack 已校验快照和 CSV 额外列：2 项；
- CLI 无效 Policy Pack：1 项；
- API 无效 pack、无效对象、顶层非对象和 `null` manifest：4 项；
- MCP 无效 pack、无效对象、顶层非对象和 `null` manifest：4 项。

现有合法 approval、role、parameter、explicit block、review、allow、unknown intent
和 Policy Pack manifest 测试全部保留并通过。

## Verification Evidence（验证证据）

2026-07-16 完整验证：

```text
PATH=.venv/bin:$PATH bash scripts/release_check.sh
229 passed in 2.09s
Ruff: pass
mypy: pass (22 source files)
git diff --check: pass
MCP smoke: 17 tools available
Build: omniglyph-0.8.0b0.tar.gz and omniglyph-0.8.0b0-py3-none-any.whl
Twine metadata check: pass
Artifact audit: pass
Clean-wheel CLI/MCP smoke: pass
Cross-border demo: pass

bash scripts/privacy-scan.sh
exit 0, no findings
```

## Compatibility（兼容性）

- 无 API 路径、CLI 命令或 MCP 工具名称变化；
- 合法 Policy Pack 的输出不变；
- 合法 inline manifest 可以继续省略 decision；
- 未知 intent 仍返回 block / unknown；
- 参数 schema 子集和未知关键字处理不变；
- 新的严格行为仅影响此前无效、歧义或会抛异常的策略输入。

## Remaining Risks（剩余风险）

- inline manifest 未知字段继续忽略，以保持兼容；
- `parameters_schema` 仍是记录在案的有限子集，未知关键字不会执行也不会报错；
- Policy Pack 仍是本地文件格式，不提供签名、版本锁定或外部审批服务；
- metadata 和 intents 各自只读取并验证一次，但本地多文件目录没有操作系统级
  原子快照；并发写入可能形成不同版本的 metadata/intents 组合，因此策略目录
  仍应受信并由宿主控制；
- API/MCP 仍无内建认证，应继续只在受信本地环境或受控宿主后运行；
- 本阶段没有添加请求体大小限制、JSON-RPC batch 或持久化审计存储。

## Method and Publication Boundary（方法与发布边界）

Safe-Agent router 将本阶段误分类为 `website-build-launch`。本项目没有 Web UI，
因此未采用 UI、SEO、social 或 browser 建议，只使用 `engineering-build-release`
和 `execution-publish-check` 的构建证据与发布隔离原则。根因分析使用
`systematic-debugging`，设计与实施使用 `brainstorming`、`writing-plans`、
`executing-plans`、`test-driven-development` 和 `verification-before-completion`。

本阶段仅在本地 `codex/intent-fail-closed` 分支完成。未推送、未合并、未创建标签、
未发布 TestPyPI/PyPI/MCP Registry，也未部署或修改任何外部系统。
