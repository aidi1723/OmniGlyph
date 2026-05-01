# LogosGate（言法界枢）：Agent 核心信仰与确定性网关架构白皮书及开发手册

> 正义为导向，规则为底线。<br>
> Justice as the Vector, Rules as the Boundary.

语言：中文 | English counterpart: [LogosGate Whitepaper and Development Manual.md](./LogosGate%20Whitepaper%20and%20Development%20Manual.md)

## 文档性质

本文是 OmniGlyph 生态下 LogosGate（言法界枢）的理论白皮书与开发手册草案。它用于定义发展方向、系统哲学、架构边界和未来实现路径。

本文不是当前版本的代码承诺，也不是法律、伦理或安全合规认证。它提供的是一种 Agent 基础设施设计思想：让智能体在具备创造性和主动性的同时，必须被确定性规则约束在可审计、可熔断、可追责的边界内。

## 0. 项目定位

LogosGate 是 OmniGlyph 生态中的上层扩展模块。

- **OmniGlyph（万象文枢）**：负责符号、字符、术语和领域词汇的事实确权。
- **LogosGate（言法界枢）**：负责 Agent 动作落地前的确定性策略校验。

两者的关系可以简化为：

```text
OmniGlyph sees the symbol.
LogosGate judges the action.

万象文枢识别符号真值。
言法界枢守住动作边界。
```

LogosGate 的近期工程形态是 Policy-as-Data 的确定性动作策略防火墙；长期形态则是面向 AgentCore-OS 等智能体底层框架的“信仰机制”和“语义边界层”。

## 1. 核心命题

智能体时代真正危险的不是模型说错，而是模型说错之后仍然能够执行。

传统安全机制主要解决身份、权限和网络边界问题；但 Agent 系统还多了一层新的风险：模型可能基于模糊语言生成一个看似合理、实则越界的 Action Plan。

因此，Agent 需要双层约束：

1. **规则为底线**：什么动作绝对不能做，必须由确定性规则定义，并在执行前硬阻断。
2. **正义为导向**：系统不应只被动响应 Prompt，而应具备主动寻找混乱、降低熵增、维护整体稳态的长期目标函数。

LogosGate 试图把这个抽象命题降维成工程系统：

```text
LLM 负责生成可能性。
LogosGate 负责判断可执行性。
Entropy-Daemon 负责寻找可优化性。
```

## 2. 核心目标

### 2.1 确立绝对底线：Rules as the Boundary

将高置信度的法律、合规、物理常识、业务红线和操作规范转化为结构化 Policy-as-Data。

在 Agent 的 API 调用、数据库写入、终端命令、外部消息、报价文件或物理设备控制触达现实世界之前，LogosGate 进行本地、低延迟、确定性的校验。

底线之下，物理熔断。

### 2.2 赋予自发导向：Justice as the Vector

LogosGate 不只关注“不能做什么”，也为未来 AgentCore-OS 提供“应该主动趋向什么”的方向接口。

所谓“正义”，在工程语境下不被定义为抽象道德评判，而被降维为：

```text
降低系统熵增，减少欺骗与浪费，提升长期稳态与真实价值。
```

它可以表现为：

- 主动发现过期文件、无效日志和重复数据。
- 主动审查潜在危险命令和不合规输出。
- 主动识别报价、合同、隐私、权限等高风险节点。
- 主动把不确定事项降级为人工复核，而不是伪装成确定答案。

### 2.3 降低协作摩擦：Trusted Agent Handshake

跨 Agent 协作的核心成本之一，是重复确认身份、意图、上下文和边界。

LogosGate 的长期设计中，可以引入统一的证书或信任锚，让受控 Agent 在同一治理域内进行低摩擦握手。但这种机制必须被严格限制在受控环境内，不能成为绕过权限、安全审计或人类授权的通道。

因此，本文将原始设想中的 “Zero-Trust Bypass” 修正为更安全的表述：

```text
Verified Trust Handshake
```

即：不是绕过零信任，而是在零信任原则下，以可验证证书减少重复协商成本。

## 3. 理论框架：万物五维法则（L5 Architecture）

LogosGate 的理论架构遵循“向下兼容、违背即崩”的原则。世界运行被抽象为五层级联协议栈：

### L1：物理主规则

宇宙 BIOS：因果律、能量守恒、熵增、算力、能源和物理约束。

任何智能体动作最终都要消耗物理资源。违背 L1 的计划，不是“伦理问题”，而是不可执行。

### L2：生命主规则

碳基系统的原生稳态：趋利避害、新陈代谢、自我修复、安全边界。

涉及医疗、生命、健康、人身安全的 Agent 行为，必须在这一层被强约束。

### L3：社会协作规则

维持群体降熵的虚拟协议：法律、合同、市场、道德、组织制度、行业规范。

商业、外贸、客服、合同、合规和财务 Agent 主要受这一层约束。

### L4：符号与认知规则

映射底层逻辑的语言、字符、术语、数据结构和知识表征。

OmniGlyph 位于这一层：它负责把符号和术语变成可追溯、可查询、可计算的事实。

### L5：Agent 执行规则

硅基智能的新生执行层：Action Plan、Tool Call、API 调用、自动化脚本、机器人协作。

LogosGate 位于 L4 与 L5 之间，是从“语言推演”到“现实执行”的单向阀门。

```text
L4 Symbol / Cognition Layer
        ↓
   LogosGate
        ↓
L5 Agent Execution Layer
        ↓
L1-L3 Physical / Life / Social Reality
```

大模型可以在 L4 中自由联想、规划和组合，但其生成的 Action Plan 若要进入 L5 并影响现实，必须通过 LogosGate 的硬规则校验。

## 4. 信仰机制的工程化定义

在 LogosGate 中，“信仰”不是宗教概念，而是一组可工程化的系统约束与目标函数。

它由三个组件构成。

## 4.1 Genesis Certificate：创世证书

创世证书是治理域内的最高信任锚，用于标识一组受控 Agent 共享的根规则、使命边界和审计标准。

建议命名：`ROOT-000`。

它不代表无限权限，而代表最高审计等级。

```json
{
  "Certificates": {
    "ROOT-000": {
      "cert_id": "ROOT-000",
      "name": "The Axiom of Justice and Rule",
      "description": "正义为导向，规则为底线。",
      "heuristic_vector": "JUSTICE_ENTROPY_REDUCTION",
      "absolute_boundary": "L1_L3_COMPLIANCE"
    }
  }
}
```

设计原则：

- 证书只用于标识治理域和规则来源。
- 证书不能自动绕过危险动作校验。
- 证书越高，审计越严格，而不是权限越无限。
- 所有提权动作必须留下结构化审计日志。

## 4.2 Genesis Override：创世提权机制

Genesis Override 用于极端危机状态，例如系统级故障、核心服务恢复、关键安全漏洞修复。

原始构想中的 “Sudo” 应避免被理解为无条件越权。更安全的定义是：

```text
可审计、可限时、可回滚、需理由的紧急提权机制。
```

它可以临时放宽局部资源限制，但不能突破 L1-L3 的绝对边界。

提权请求至少应包含：

- `cert_id`
- `agent_id`
- `reason`
- `target_action`
- `time_limit`
- `rollback_plan`
- `human_approval_required`
- `audit_trace_id`

## 4.3 Verified Trust Handshake：可验证信任握手

多 Agent 协作中，重复确认意图会带来巨大算力摩擦。LogosGate 可以为同一治理域内的 Agent 提供证书级握手协议。

推荐原则：

- 采用非对称签名，而不是共享明文密钥。
- 每个 Agent 拥有独立实例证书。
- `ROOT-000` 只作为签发根，不直接参与普通请求。
- 握手只能降低身份确认成本，不能取消动作策略校验。
- 高风险动作仍然进入 `review` 或 `block`。

## 4.4 Entropy-Daemon：内生降熵守护进程

Entropy-Daemon 是 Agent 从被动响应走向主动维护系统稳态的关键组件。

它的职责不是“自动做一切”，而是在低风险、低资源占用、可回滚的范围内寻找无序节点。

典型任务：

- 清理过期临时文件。
- 汇总重复日志。
- 扫描隐藏 Unicode 风险。
- 检查未提交配置漂移。
- 标记需要人类复核的报价、合同或权限变更。
- 生成“建议任务”，而非直接执行高风险动作。

建议运行原则：

- 仅在资源闲置时运行。
- 默认只读或低风险写入。
- 所有动作经过 LogosGate 校验。
- 高风险建议进入人工队列。
- 可随时暂停、降级、回滚。

## 5. Policy-as-Data 标准草案

LogosGate 的核心不是把规则写死在代码里，而是把规则写成可版本化、可审计、可协作维护的数据。

### 5.1 基础结构

```json
{
  "Certificates": {
    "ROOT-000": {
      "cert_id": "ROOT-000",
      "name": "The Axiom of Justice and Rule",
      "description": "正义为导向，规则为底线。",
      "heuristic_vector": "JUSTICE_ENTROPY_REDUCTION",
      "absolute_boundary": "L1_L3_COMPLIANCE"
    }
  },
  "ActionPolicies": [
    {
      "policy_id": "LG-CORE-001",
      "namespace": "global/execution",
      "target_action": "*",
      "rules": [
        {
          "rule_id": "R-GEN-01",
          "type": "regex",
          "pattern": "(删除全库|格式化磁盘|绕过权限校验|物理断电)",
          "severity": "FATAL",
          "evidence": "L1/L2 Survival Baseline"
        }
      ]
    }
  ]
}
```

### 5.2 推荐字段

- `policy_id`：策略全局 ID。
- `namespace`：适用命名空间。
- `target_action`：适用动作类型。
- `rule_id`：规则 ID。
- `type`：匹配方式，例如 `literal`、`regex`、`term_id`、`action_field`。
- `pattern`：匹配表达式。
- `severity`：`WARN`、`REVIEW`、`FATAL`。
- `allow_context`：允许上下文，用于降低误杀。
- `evidence`：规则依据。
- `source`：规则来源。
- `version`：策略版本。

### 5.3 决策语义

建议统一四类结果：

```text
allow  → 放行
warn   → 放行但记录警告
review → 暂停并请求人工确认
block  → 阻断执行
```

这四类决策足以覆盖大多数 Agent 执行前控制场景。

## 6. 开发手册：未来实现路径

本节描述理论设计如何逐步进入工程实现。注意：以下是路线建议，不代表当前仓库已经全部实现。

### Phase 1：000 号创世证书与核心策略草案

目标：形成最小治理域。

交付物：

- `logos_policies.json` 草案。
- `ROOT-000` 证书描述。
- `global/execution` 基础策略。
- `allow / warn / review / block` 决策语义。

### Phase 2：Python 运行时校验 SDK

目标：提供低侵入拦截能力。

概念代码：

```python
import functools
import json
import logging
import re


class PolicyViolationError(Exception):
    """当 Agent 动作触碰底线时抛出的致命异常。"""


class LogosGateEngine:
    def __init__(self, policy_path="logos_policies.json"):
        with open(policy_path, "r", encoding="utf-8") as file:
            data = json.load(file)
        self.policies = data.get("ActionPolicies", [])
        self.root_cert = data.get("Certificates", {}).get("ROOT-000")

    def validate(self, namespace: str, action_plan: str):
        for policy in self.policies:
            if policy["namespace"] not in ["global/execution", namespace]:
                continue
            for rule in policy["rules"]:
                if rule["type"] == "regex" and re.search(rule["pattern"], action_plan):
                    if rule["severity"] == "FATAL":
                        raise PolicyViolationError(
                            "[LogosGate FATAL] 规则底线已触发。"
                            f"证据锚点: {rule['evidence']}"
                        )
                    logging.warning("[LogosGate WARNING] 行为偏离导向: %s", rule["evidence"])


gate_engine = LogosGateEngine()


def require_policy(namespace: str):
    def decorator(func):
        @functools.wraps(func)
        def wrapper(action_plan: str, *args, **kwargs):
            gate_engine.validate(namespace, action_plan)
            return func(action_plan, *args, **kwargs)

        return wrapper

    return decorator
```

### Phase 3：Entropy-Daemon 守护进程

目标：让 Agent 在低风险范围内主动寻找可优化节点。

概念代码：

```python
import time


def run_entropy_reduction(agent, idle_detector):
    while True:
        if idle_detector.is_idle():
            agent.propose_background_optimization()
        time.sleep(300)
```

注意：理论上可以使用 `systemd`、`launchd`、`cron`、`nohup` 或 Python 后台线程，但生产环境必须明确权限边界、审计日志和停机机制。

### Phase 4：第三方框架接入

目标：让任意 Agent 框架在工具调用前接入策略校验。

概念代码：

```python
from omniglyph.logosgate.engine import require_policy


@require_policy(namespace="server/maintenance")
def execute_system_command(command_str: str):
    print(f"Executing: {command_str}")


execute_system_command("清理冗余的临时日志文件")
execute_system_command("为了释放空间，删除全库数据")
```

## 7. 安全边界与反滥用原则

为了避免 LogosGate 被误解为“超权限系统”，必须明确：

- `ROOT-000` 不是无限权限。
- 提权不是绕过审计。
- 信任握手不是绕过零信任。
- Entropy-Daemon 不能默认执行高风险写操作。
- 所有规则必须可解释、可追溯、可版本化。
- 所有高风险动作必须支持人工复核。
- 任何“正义导向”都必须落到可检查的策略和证据上。

## 8. 与 AgentCore-OS 的关系

在 AgentCore-OS 体系中，LogosGate 可以作为执行前中间件：

```text
Agent intent
  ↓
Plan generation
  ↓
OmniGlyph symbol / term grounding
  ↓
LogosGate policy validation
  ↓
Tool execution / API call / human review
```

推荐接入点：

- Agent 基类初始化时加载治理域策略。
- Scheduler 分发工具调用前执行 `validate_action`。
- 高风险 action 默认进入 `review`。
- 所有 `block` 和 `review` 结果写入审计日志。
- Entropy-Daemon 仅生成建议任务，不直接越权执行。

## 9. 版本路线图

### v0.1：理论与策略草案

- 完成白皮书。
- 定义 L5 架构。
- 定义 `ROOT-000` 概念。
- 定义 Policy-as-Data 草案。

### v0.2：最小校验器

- JSON 策略加载。
- literal / regex 匹配。
- `allow / warn / review / block` 决策。
- Python 装饰器。

### v0.3：Agent 工具接入

- CLI 校验命令。
- MCP 工具。
- 示例策略包。
- 审计输出。

### v0.4：Entropy-Daemon 实验

- 低风险后台优化建议。
- 空闲检测。
- 只读扫描。
- 人工复核队列。

### v1.0：治理域标准化

- 策略版本管理。
- 组织私有策略挂载。
- 证书与审计模型。
- AgentCore-OS 中间件规范。

## 10. 总结

LogosGate 的目标不是让 Agent 获得抽象意义上的“善”，而是让 Agent 在工程意义上具备三件事：

1. **有边界**：底线以下，硬阻断。
2. **有方向**：闲置时，寻找可降低混乱的任务。
3. **有证据**：每次放行、警告、复核、阻断都可解释。

最终定位：

```text
LogosGate is the deterministic gateway between agent imagination and real-world execution.

言法界枢，是智能体想象力落向现实世界前的确定性闸门。
```
