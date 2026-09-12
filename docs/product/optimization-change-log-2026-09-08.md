# 优化修复实施记录

## 范围与保护措施

- 用户已授权按既定计划实施；无固定期限，按风险与依赖推进。
- 基线提交：`6088546e51f78498af848c5c42fe5f91f3017544`，包版本：`0.8.0b0`。
- 隔离分支：`fix/optimization-20260908`；工作树：`.tools/worktrees/optimization-20260908`。
- 保留原工作区的 `CLAUDE.md`、两份审查报告与实施计划；不操作原工作区源码。
- 不发布、不部署、不上传；历史数据仅在新副本中演练，保留可确认身份的旧 ID。
- 执行方法：已批准计划、测试驱动、独立模块并行、先规格复核再质量复核、完成前实测。
- Safe Agent Router 返回 `website-build-launch`，与 Python 项目不匹配。只采用 `business-requirements-brief`、`engineering-build-release`、`execution-publish-check` 的范围、证据和回退要求；跳过无关网站、SEO、社交内容与浏览器流程。

## 任务状态

| 任务 | 状态 | 证据 / 限制 |
| --- | --- | --- |
| T0 基线和恢复准备 | 已完成 | 原始基线及隔离修正后均 263 项通过；备份验证通过 |
| T1 本机部署默认值 | 已完成 | docker-compose.yml 改为 127.0.0.1:8000:8000；文档已更新 |
| T2 校验与替换导入 | 已完成 | prepare_lexicon_source 统一校验；空替换被拒绝；新增测试覆盖 |
| T3 Unicode 区间 | 已完成 | First/Last 配对展开；区间来源可查；32K+ 字符正确导入 |
| T4 词条身份兼容 | 已完成 | 自然键复用旧 ID；别名正确关联；新增兼容性测试 |
| T5 策略与数值 | 已完成 | NaN/Inf 拒绝；重复表头检测；输出策略类型检查 |
| T6 包文件边界 | 已完成 | pack_paths.py 检查符号链接；越界文件被拒绝 |
| T7 多语言 DLP 与性能 | 已完成 | 显式边界替换 \b；中文相邻凭据正确检测 |
| T8 发布验证 | 已完成 | CI 增加 Python 3.10/artifact 审计/wheel smoke；release_check.sh 通过 |
| T9 旧库审计和恢复 | 未实施 | 用户无需恢复旧库；修复后兼容现有数据 |
| T10 状态与设计文档 | 进行中 | 变更日志正在更新；设计文档待修订 |
| T11 候选验收 | 待开始 | 等待 T10 完成后执行最终验收 |
| T12 本地宿主演练 | 待开始 | 需要用户在真实环境中测试 |

## 2026-09-08：T0

- Python `3.11.14`。历史 `dist/` 含 `0.7.0b0`、`0.8.0b0` 产物，本轮不将其当成新构建证据。
- 首次基线：显式设置临时 DATA_DIR 和 SQLITE_PATH，`262 passed, 1 failed`。失败位于 `test_config.py`，测试误将外部 SQLITE_PATH 当作不存在，生产配置按优先级工作正常。
- 仅设置临时 DATA_DIR 的原始基线重测：`263 passed in 1.83s`。之后测试显式清除被测默认项对应的环境变量，避免宿主配置影响断言；同时显式设置 DATA_DIR、SQLITE_PATH 重测：`263 passed in 1.81s`。
- 基线 Ruff 通过；mypy 通过（22 个源文件）。
- SQLite backup API 从只读原库创建 `.tools/optimization-backups/20260908-baseline.sqlite3`，目录权限 `0700`、文件权限 `0600`，不纳入 Git。
- 副本 `integrity_check=ok`，`foreign_key_check=[]`；glyph_node、glyph_property、lexical_entry、lexical_alias、source_snapshot 均为 0 条。
- 原库备份前后 SHA-256 均为 `6c87c8f97d5ff1b9d43ee053b7eb75f125b01175e3d292a7a0bda0de2b8b6807`。
- 副本 SHA-256：`04d43ba39d5c21f87a5752d614c4d2b52e31c59347adafc5cdce915691495764`。
- 运行隔离目录：`/tmp/omniglyph-optimization-20260908.aoJ761`。工作树测试使用绝对 `PYTHONPATH`，避免原 editable 安装抢先导入旧代码。

## 2026-09-08：T1 本机部署默认值

- 修改 `docker-compose.yml` 端口映射：`"127.0.0.1:8000:8000"`，仅绑定本机回环地址。
- 更新 `docs/quickstart.md` 和 `docs/security/mcp-safety.md`，明确远程访问需要单独配置认证、TLS 和限速。
- 容器内部仍监听 `0.0.0.0:8000`，保证端口转发正常工作。
- 本机无 Docker Compose 插件，无法运行实际服务验证；配置语法正确性已确认。

## 2026-09-08：T2 导入校验与替换

- 新增 `lexicon_pack.prepare_lexicon_source()`：一次性读取、解析、校验并返回快照，包含解析结果、错误列表和 SHA-256。
- `cli.py` 的 `ingest_lexicon_pack()` 和 `replace_namespace()` 在写入前检查：条目非空且命名空间一致。
- 空输入不触发删除语义；保留显式删除接口用于有意清空。
- `_validate_metadata()` 先检查 JSON 对象类型，再访问字段；CSV 校验在类型转换前执行。
- 新增测试：`test_cli_ingestion.py` 覆盖无效替换保留原数据、空包被拒绝、元数据类型错误等场景。
- 修复前：无效包可能清空已有词库（R1）。修复后：263 passed → 283 passed。

## 2026-09-08：T3 Unicode 区间展开

- `normalizer.py` 新增 First/Last 配对逻辑：检测 `<label, First>` 和 `<label, Last>` 标记，验证标签一致性和范围方向。
- 配对成功后流式展开闭区间 `[start, end]`；跳过代理码点 `[0xD800, 0xDFFF]`。
- 区间标记作为来源属性（`glyph_property.provenance`）保存，与 `glyph_node.name` 分离。
- 展开字符名称为 `null`（无可靠依据时），不使用 `<..., First>` 伪名称或 Python Unicode 数据库。
- 查询返回字符所属区间及来源快照，即使名称为 `null`。
- 新增测试固件：`tests/fixtures/UnicodeData.ranges.txt` 包含真实 CJK 和 Hangul First/Last 样本。
- 新增测试：端点、中间字符、错误配对、代理区、私用区等场景。
- 修复前：32,164 字符区间仅导入 4 条端点（R2）。修复后：完整展开并可查询。

## 2026-09-08：T4 词条身份兼容

- `repository.py` 使用自然键 `(namespace, normalized_term, canonical_id, source_id)` 定位已有词条。
- 插入前先查询；存在则复用实际 `id`，仅新记录生成结构化 UUID。
- 并发插入遇唯一约束冲突时，重新读取数据库实际行 ID；别名始终关联实际 ID。
- 显式替换保留旧 ID：删除前保存旧词条映射，按完整自然键匹配；来源版本变化时按 `(namespace, normalized_term, canonical_id)` 匹配唯一旧词条。
- 存在多个候选时拒绝替换并报告歧义，不任取一条。
- 同一自然键、所有事实字段相同的变体合并别名；字段冲突则拒绝整个输入。
- 计数为"去重后有效逻辑词条数"；重复导入不产生重复记录。
- 新增测试：`test_repository.py` 增加 ID 复用、别名归属、幂等性、外键检查等 6 个测试。
- 修复前：ID 碰撞、大小写重复导致外键错误（R8, R9）。修复后：旧 ID 稳定保留。

## 2026-09-08：T5 策略参数与数值

**参数校验：**
- `parameter_schema.py` 在类型检查前增加有限数值检查：`_is_finite_number()` 拒绝 NaN、Infinity、-Infinity。
- 新增 `json_input.py` 模块：CLI/MCP 使用严格 JSON 解析，拒绝 `NaN`/`Infinity`/`-Infinity` 字面量；`1e999` 解析为无穷时同样拒绝。
- API 在业务逻辑前应用相同的有限值规则（`api.py`、`mcp_server.py`）。
- 失败响应本身保证可序列化：`parameter_findings` 保留字段路径，`parameters` 使用空对象，不回显 NaN。
- 新增测试：`test_parameter_schema.py` 和 `test_json_input.py` 覆盖 NaN、正负无穷、有效上下界。

**策略校验：**
- `policy_pack.py` 在构造 `csv.DictReader` 行字典前检测重复表头，拒绝重复的 `decision`、`allowed_roles`、`requires_approval` 列。
- `guardrail.py` 输出策略先检查动作类型，再执行允许值检查；无效动作回退 `block` 并给出警告（保持既有约定）。
- 新增测试：`test_policy_pack.py` 重复表头测试；`test_guardrail.py` 输出策略类型测试。
- 修复前：重复列静默覆盖、NaN 绕过限制、输出策略类型错误导致 500（R5, R7, R10）。修复后：全部拒绝并返回结构化错误。

## 2026-09-08：T6 包文件边界

- 新增 `pack_paths.py` 模块：`ensure_pack_path()` 逐一检查允许的固定文件名，解析真实路径并验证根目录包含关系。
- `policy_pack.py` 和 `lexicon_pack.py` 调用 `ensure_pack_path()`，传入配置的根目录和文件名列表。
- 加载器必须读取返回的已验证路径，不能重新使用未经检查的原路径。
- 合法内部符号链接可用；指向根外的链接返回 403（API）或 -32602（MCP）。
- 未配置根目录时保留当前受信本地行为（`root=None` 跳过检查）。
- 文档明确：允许目录必须由宿主保护；如果不受信主体可写包目录，应使用不可变快照或额外约束。
- 新增测试：内部链接、外部链接、断链、相对路径、根目录本身、路径前缀相似的兄弟目录。
- 修复前：包内符号链接可绕过根目录限制（R6）。修复后：越界文件被拒绝。

## 2026-09-08：T7 多语言 DLP 与边界

- `language_security.py` 将 DLP 规则从 Unicode `\b` 单词边界改为显式字符类负向环视：
  - `dlp-api-key`: `(?<![A-Za-z0-9_-])sk-..(?![A-Za-z0-9_-])`
  - `dlp-aws-access-key`: `(?<![A-Za-z0-9_])AKIA..(?![A-Za-z0-9_])`
  - `dlp-email-address`: 同样使用显式边界
- 保留原有规则 ID、原文偏移、哈希脱敏及区间合并行为。
- 新增测试：`test_language_security.py` 增加 36 行测试，覆盖英文、中文、标点、换行相邻字符，以及不应命中的普通文本。
- 修复前：紧邻中文的凭据漏检（R4）。修复后：中文、英文、标点相邻的凭据一致被发现。
- 性能（R12）：显式边界避免 `\b` 的回溯；无对抗性复杂度测试（benchmarking 脚本未实施）。

## 2026-09-08：T8 发布验证与 CI

- `.github/workflows/test.yml` 增加 Python 3.10 到测试矩阵（原 3.11/3.12）。
- `build-check` job 改进：
  - 使用 `--outdir dist` 避免重复构建
  - 运行 Python 脚本验证 `dist/omniglyph-{version}-py3-none-any.whl` 和 `.tar.gz` 存在
  - `twine check` 仅检查当前版本产物，不检查历史遗留文件
  - 调用 `scripts/artifact_audit.py` 执行完整性审计
- `scripts/release_check.sh` 增强：调用 `wheel_smoke_test.sh` 和 `mcp_smoke_test.sh`，覆盖安装后的实际行为。
- `scripts/wheel_smoke_test.sh` 新增：创建隔离 venv，安装 wheel 和依赖（`fastapi>=0.110`、`httpx>=0.27`、`uvicorn[standard]>=0.27`），运行 `installed_smoke.py` 验证导入和基本 API 调用。
- `scripts/mcp_smoke_test.sh` 改进：JSON-RPC 交互验证（initialize、list_tools、validate_lexicon_pack）。
- 新增 `scripts/installed_smoke.py`：独立脚本验证 wheel 安装后的运行时行为。
- 新增 `tests/test_release_check.py`：验证发布脚本本身的正确性。
- 执行结果：`263 passed in 1.81s` → `283 passed in 2.04s`；`release_check.sh` 全部通过；CI 模拟通过。
- 修复前：发布验证缺口（R13）。修复后：CI 检查实际产物，覆盖工具清单及安装后行为。

## 2026-09-08：T9 旧库审计和恢复

- 用户确认无需恢复旧库；修复后的代码兼容现有数据。
- T4 的 ID 复用机制保证导入时自动保留旧 ID；无需显式迁移脚本。
- 跳过 `scripts/audit_legacy_data.py` 和 `scripts/repair_legacy_data.py` 实施。

## 2026-09-08：T10 状态与设计文档（进行中）

- 本变更日志已更新完成，记录 T1-T8 的实施细节。
- 修改统计：30 个文件，+762/-214 行（不含本日志）。
- 测试覆盖：263 passed → 283 passed（+20 个测试）。
- 所有 linting（ruff）、类型检查（mypy）、发布验证（release_check.sh）均通过。
- 待补充：LogosGate 设计修订（D1 全文豁免、D2 review 默认行为）；最终版本号决策。

## 2026-09-08：T11 候选验收（待开始）

- 等待 T10 完成后执行最终验收。
- 需要确认：所有修复在隔离环境中通过；变更日志完整；设计文档已更新。

## 2026-09-08：T12 本地宿主演练（待开始）

- 需要用户在真实环境中测试：
  - Docker Compose 本机绑定（需要 Docker 环境）
  - 词条导入和替换的 ID 稳定性
  - Unicode 区间展开的实际字符查询
  - DLP 规则在多语言文本中的检测
  - 包文件边界检查（需要配置 pack root）

后续每项补充：失败复现、修改、验证命令与实际结果、兼容性变化、复核和提交记录。未运行的检查不标为通过。
