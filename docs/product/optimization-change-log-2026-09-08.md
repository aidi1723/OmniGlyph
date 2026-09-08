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
| T1 本机部署默认值 | 待开始 | 本机缺少 Compose 插件，运行验证不可用 |
| T2 校验与替换导入 | 待开始 | |
| T3 Unicode 区间 | 待开始 | |
| T4 词条身份兼容 | 待开始 | |
| T5 策略与数值 | 待开始 | |
| T6 包文件边界 | 待开始 | |
| T7 多语言 DLP 与性能 | 待开始 | |
| T8 发布验证 | 待开始 | |
| T9 旧库审计和恢复 | 待开始 | |
| T10 状态与设计文档 | 待开始 | |
| T11 候选验收 | 待开始 | |
| T12 本地宿主演练 | 待开始 | |

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

后续每项补充：失败复现、修改、验证命令与实际结果、兼容性变化、复核和提交记录。未运行的检查不标为通过。
