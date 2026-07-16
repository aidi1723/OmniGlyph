# OmniGlyph Parameter Schema Fail-Closed 收尾报告

## Executive Summary（执行摘要）

第三阶段完成了文档化轻量 `parameters_schema` 关键字的 fail-closed 元验证。
审查确认，原实现仅在关键字“已经是正确 Python 类型”时才执行约束：畸形的
`required`、`type`、`properties`、`enum`、边界或 `items` 会被静默忽略，Policy
Pack 校验也只要求 `parameters_schema` 是 JSON 对象。调用方可能相信 schema 在生效，
运行时却返回 `allow`。

修复后：

- 直接 Python `validate_parameters()` 在值校验前先做 schema 元验证；
- inline manifest 的畸形 schema 返回 `block` / `invalid_manifest`；
- Policy Pack 行级畸形 schema 在 validate/load 失败，CLI 退出 `2`、API `400`、
  MCP `-32602`；
- schema 元验证与值遍历均改为迭代实现，深嵌套与环不再抛 `RecursionError`；
- 未知关键字仍在任意层级被忽略。

项目测试从第二阶段的 229 项增加到 263 项。完整发布门禁与（跟踪文件）隐私扫描通过。
分支保持本地，未推送、未合并、未发布。

## Root Cause（根因）

根因是“浅容器检查 + 类型守卫式求值”叠加：

- runtime evaluator 对支持关键字使用 `isinstance` 守卫，错误类型直接跳过；
- Policy Pack 与 inline manifest 只要求 `parameters_schema` 为 object；
- 没有递归检查嵌套 `properties` / `items` 的关键字合法性；
- 首轮递归元验证对循环 schema 和约千层合法嵌套依赖 Python 调用栈，随后值验证
  仍递归，深 schema 元验证通过后 `validate_parameters()` 仍可能崩溃。

实际复现（修复前）：

```text
required: "service"                    -> allow / matched（或仅参数路径误导）
properties.service.type: "date"        -> allow / matched
Policy Pack required: "service"        -> validation pass, loader succeeds
deep nested schema (1500 levels)       -> meta OK, value path RecursionError
cyclic properties / items              -> RecursionError
```

## Changes（变更）

### Schema meta-validator

- 新增 `validate_parameter_schema()`：依赖无关、路径稳定的 findings；
- 固定关键字顺序：`type` → `required` → `properties` → `enum` →
  `minLength`/`maxLength` → `minimum`/`maximum` → `items`；
- 属性按插入顺序展开；未知关键字任意层级忽略；
- 显式 DFS 事件栈 + 分支祖先集合检测环，不把共享子 schema 误判为环。

### Direct evaluation defense

- `validate_parameters()` 先返回 schema findings（路径根 `$.schema`）；
- 值遍历改为显式栈，对象属性与数组元素保持原有插入/索引顺序语义；
- 1500 层对象与数组链可正常匹配或稳定报告类型错误。

### Inline manifest boundary

- `validate_intent_manifest()` 对 object 型 `parameters_schema` 调用元验证；
- 保留非 object 的原有 message；
- 畸形 schema → `invalid_manifest`（API/MCP 正常 200/工具结果中的阻断证据）。

### Policy Pack boundary

- `_validate_intent_row()` 在 JSON 对象解析后追加
  `parameters_schema.<path>: <message>` 行错误；
- 无效 pack 仍走 `invalid policy pack:` / CLI `2` / API `400` / MCP `-32602`。

### Documentation

- `docs/specs/policy-pack-standard.md`：关键字合法性、环、直接调用与错误语义；
- `docs/architecture/language-security-gateway.md`：共享元验证与迭代 fail-closed；
- `docs/product/project-status.md`：链接本收尾报告。

## Commits（提交）

- `bea582e`：第三阶段设计规格；
- `0fac216`：第三阶段实施计划；
- `825a25f`：schema 元验证器与直接调用 fail-closed；
- `a9c53b6`：schema 元验证改为迭代并处理环/深链；
- `72c4e9b`：值验证改为迭代，关闭深嵌套 `RecursionError`；
- `3cc241a`：inline manifest 拒绝畸形 parameter schema；
- `2a42fa0`：Policy Pack 拒绝畸形 parameter schema。

（文档与本 closeout 提交见同分支后续 commit。）

## Test Coverage（测试覆盖）

相对第二阶段（229）净增 34 个收集场景，当前 **263 passed**：

- schema 元验证非法关键字：18 个精确 finding 参数化用例；
- 环（properties/items）、共享子 schema、1500 层 schema；
- 直接调用无效 schema 先于值校验；
- 深对象匹配、深对象类型失败、深数组链；
- inline 嵌套畸形 type、API/MCP invalid_inline_parameter_schema；
- Policy Pack keywords、CLI exit 2、API 400、MCP -32602。

合法参数、未知关键字兼容、approval/role/block/review/allow 既有用例全部保留。

## Verification Evidence（验证证据）

2026-07-16 完整验证：

```text
PATH=.venv/bin:$PATH bash scripts/release_check.sh
263 passed
Ruff: pass
mypy: pass
git diff --check: pass
MCP smoke: 17 tools
Build: omniglyph-0.8.0b0.tar.gz / omniglyph-0.8.0b0-py3-none-any.whl
Twine: pass
Artifact audit: pass
Clean-wheel smoke: pass
Cross-border demo: pass

Privacy (tracked files via git ls-files): 0 hits for local path / PII patterns.
Note: scripts/privacy-scan.sh requires `rg` on PATH; this environment used an
equivalent tracked-file scan. Local tool caches (.uv-cache, .ruff_cache) may
contain absolute paths and are not published.
```

## Compatibility（兼容性）

- 无 CLI 命令、API 路径、MCP 工具名变更；
- 合法 schema 与合法 pack/manifest 行为不变；
- 未知关键字仍忽略；
- 新的严格行为仅作用于此前会被静默跳过或可能崩溃的畸形/深/环 schema。

## Remaining Risks（剩余风险）

- 仍不是完整 JSON Schema；无 `$ref`/`oneOf`/cross-keyword 语义；
- 未知关键字的值不被验证；
- Policy Pack 本地多文件无 OS 级原子快照；
- API/MCP 无内建认证；
- 不校验嵌套运行时值对象是否自环（schema 环已拦截；合法 JSON 值树通常无共享环）。

## Method and Publication Boundary（方法与发布边界）

本阶段按 `test-driven-development` 与计划任务串行实施；Task 1 质量审查发现的
递归风险以失败测试先行后修复。Safe-Agent router 若将 hardening 误分类为
website/UI 工作流，应忽略；本仓库无 Web UI 发布路径。

### 文档对齐（收尾补充）

与本阶段实现一致的用户/维护文档已同步：

- `docs/specs/policy-pack-standard.md` / `docs/architecture/language-security-gateway.md`
  （实现期已更新）
- `docs/product/project-status.md`（链接本 closeout）
- `docs/product/v0.8-maintenance-log.md`
- `docs/product/v0.8-closeout.md`（标注 post source-batch hardening）
- `docs/release-notes-v0.8-source-batch-draft.md`
- `CHANGELOG.md`（`Unreleased` fail-closed 条目）

### GitHub 发布边界

- **推送范围**：feature 分支 `codex/parameter-schema-fail-closed` →
  `origin`（`https://github.com/aidi1723/OmniGlyph.git`）。
- **不在本阶段执行**：merge 到 `main`、force-push、打 tag、TestPyPI/PyPI/
  MCP Registry 上传、部署或修改外部系统。
- **隐私门禁**：推送前对 `git ls-files` 跟踪树扫描本地绝对路径、本机主机名、
  个人邮箱与其它私有工作区路径模式；缓存目录（`.venv`、`.ruff_cache`、
  `.uv-cache` 等）不纳入发布树。
- **公开可接受标识**：GitHub 账号 `aidi1723`、项目公开名「万象文枢」/
  OmniGlyph 属于仓库既有公开标识，不作为隐私命中。
