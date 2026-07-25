# API 智能体指南

本指南面向在 MultiUAV-Plat 无人机服务器上构建 LLM 驱动型智能体的开发人员，以及需要安全、正确操作该服务器的 AI 智能体。

这不是完整的 REST 参考文档。如需按端点查看详细信息，请参阅 [API_REFERENCE_ZH.md](./API_REFERENCE_ZH.md)、[API_DOCUMENTATION_ZH.md](./API_DOCUMENTATION_ZH.md) 和 [AUTHENTICATION_ZH.md](./AUTHENTICATION_ZH.md)。

## 1. 适用范围

本文档重点介绍自主智能体的默认运行时约定：

- 智能体使用 `AGENT` API 密钥进行身份验证。
- 智能体仅使用 `AGENT` 角色可用的端点。
- 智能体通过观察当前会话、控制无人机、检查任务状态以及将任务标记为已完成来完成任务。

这是用于类生产环境中智能体行为的预期基线。`SYSTEM` 和 `ADMIN` 角色用于平台工具、场景编写、评分和维护，但它们并非任务求解型智能体的默认操作模式。

## 2. 思维模型

智能体与五个核心概念进行交互：

- `Session`（会话）：活跃的任务世界，包括无人机、任务和任务元数据。
- `Task`（任务）：智能体应完成的工作单元。
- `Drone`（无人机）：执行命令的可控角色。
- `Perception`（感知）：无人机可见的局部信息，例如附近的无人机、目标和障碍物。
- `Validation`（验证）：用于确定任务是否已满足的机制。

最重要的操作事实是，服务器始终具有**当前活动会话**的概念。默认智能体应针对当前会话进行操作，而不应假设它们可以创建、恢复或全局检查任意会话。

## 3. 身份验证与角色约定

API 使用 `X-API-Key` 标头。

示例：

```bash
curl -H "X-API-Key: <AGENT_API_KEY>" \
  http://localhost:8000/sessions/current/tasks
```

### 默认智能体规则

就本指南而言，运行时任务求解智能体：

- 使用 `AGENT` 密钥，
- 仅假定具有 `AGENT` 权限，
- 不依赖 `SYSTEM` 或 `ADMIN` 端点，
- 不假定隐藏的验证细节可见。

### 角色层次结构

该实现定义了：

- `ADMIN > SYSTEM > USER > AGENT`

来自服务器的重要实现细节：

- 如果未提供 API 密钥，代码当前默认设为 `AGENT` 角色。

即便如此，真实的智能体集成应显式发送 `AGENT` 密钥，而不是依赖于省略密钥的行为。

## 4. AGENT 角色可见与不可见的内容

`AGENT` 角色可以：

- 列出无人机，
- 检查特定无人机，
- 发送无人机命令，
- 读取当前会话元数据，
- 读取当前会话任务，
- 获取下一个待处理任务，
- 运行当前会话任务检查端点，
- 将当前会话任务标记为已完成或待处理，
- 读取无人机周围的局部感知信息，
- 读取当前环境，
- 检查命令历史和命令状态。

`AGENT` 角色不应假定它可以：

- 创建、删除或编辑无人机，
- 创建、编辑或删除会话，
- 创建、编辑或删除任务，
- 调用原始的 `/check/*` 评分端点，
- 列出全局目标或障碍物，
- 检查完整的隐藏任务验证树。

这种限制是故意的。它迫使智能体像场景内的操作员一样行事，而不是像拥有特权的场景编写者。

## 5. 隐藏字段与任务掩码

任务包含如下字段：

- `related_apis`
- `commands`
- `execution_check_apis`

对于 `AGENT` 和 `USER` 角色，服务器会掩码这些字段：

- `related_apis` 变为空列表，
- `commands` 变为空列表，
- `execution_check_apis` 变为 `null`。

这意味着 `AGENT` 角色必须主要根据以下内容来求解任务：

- `name`
- `content`
- `content_aliases`
- `description`
- `difficulty`
- `is_done`
- `is_passed`

不要构建依赖于隐藏检查定义或特权提示的默认智能体。如果一个任务只有在隐藏字段可见时才能求解，那么对于 AGENT 模式的使用来说，该任务编写得过于脆弱。

## 6. 标准智能体循环

推荐的控制循环是：

1. 获取当前会话。
2. 获取下一个待处理任务。
3. 检查无人机并选择一个或多个候选无人机。
4. 使用无人机状态和附近感知端点收集局部上下文。
5. 执行少量命令。
6. 重新检查任务。
7. 如果任务已满足，将其标记为已完成。
8. 重复此过程，直到没有剩余待处理任务。

这是有意为之的短视行为。相较于冗长的推测性命令链，稳健的智能体应更偏向于频繁的观察和验证。

## 7. AGENT 安全端点集合

以下端点是默认智能体的核心工作集。

### 会话

- `GET /sessions/current`
- `GET /sessions/current/tasks`
- `GET /sessions/current/tasks/next`
- `GET /sessions/current/tasks/{task_id}`
- `GET /sessions/current/tasks/{task_id}/check`
- `POST /sessions/current/tasks/{task_id}/mark-done`
- `POST /sessions/current/tasks/{task_id}/mark-pending`
- `GET /sessions/current/task-progress`

### 无人机

- `GET /drones`
- `GET /drones/{id}`
- `GET /drones/{id}/commands`
- `GET /commands/{command_id}`

### 无人机感知

- `GET /drones/{id}/nearby`
- `GET /drones/{id}/nearby/drones`
- `GET /drones/{id}/nearby/targets`
- `GET /drones/{id}/nearby/obstacles`

### 无人机控制

- `POST /drones/{id}/command`
- `POST /drones/{id}/command/take_off`
- `POST /drones/{id}/command/land`
- `POST /drones/{id}/command/move_to`
- `POST /drones/{id}/command/move_towards`
- `POST /drones/{id}/command/move_along_path`
- `POST /drones/{id}/command/change_altitude`
- `POST /drones/{id}/command/hover`
- `POST /drones/{id}/command/rotate`
- `POST /drones/{id}/command/return_home`
- `POST /drones/{id}/command/set_home`
- `POST /drones/{id}/command/calibrate`
- `POST /drones/{id}/command/take_photo`
- `POST /drones/{id}/command/send_message`
- `POST /drones/{id}/command/broadcast`
- `POST /drones/{id}/command/charge`

命令响应使用语义化的 `status` 值。`success` 表示请求的命令完全执行完毕。对于 `move_along_path`，`partial_success` 表示 `allow_partial_move=true` 使无人机至少到达一个航点，但因障碍物或电量不足阻挡剩余路径而在最终请求航点前停止。`error` 表示失败的命令未执行任何允许的移动。路径响应包含 `successful_points_count`、`successful_points`、`unsuccessful_points_count` 和 `unsuccessful_points`；点列表包含归一化的 `(x, y, z)` 三元组。

### 环境

- `GET /environments/current`

## 8. 当前会话用途

默认代理应以活动会话为基础：

```bash
curl -H "X-API-Key: <AGENT_API_KEY>" \
  http://localhost:8000/sessions/current
```

当前会话响应提供：

- 任务元数据，
- 任务类型，
- 任务描述，
- 汇总统计，
- 任务计数，
- 聚合任务进度。

对于 `AGENT`，应将当前会话视为权威任务上下文。请勿假设可以检查所有历史或隐藏的会话内部信息。

## 9. 任务语义

每个任务至少包含：

- `id`
- `name`
- `content`
- `content_aliases`
- `description`
- `difficulty`
- `is_done`
- `is_passed`

### 重要状态字段

- `is_done`：操作完成标志
- `is_passed`：验证/通过标志

这两个字段相关但不完全相同。

典型流程：

- 代理执行动作。
- 代理调用 `GET /sessions/current/tasks/{task_id}/check`。
- 若检查成功，服务器将 `is_passed` 设为 `true`。
- 代理随后调用 `POST /sessions/current/tasks/{task_id}/mark-done`。

代理不应盲目标记任务完成。推荐做法：

1. 执行，
2. 检查，
3. 仅在检查成功或有明确可观察证据后标记完成。

### 下一个待处理任务

`GET /sessions/current/tasks/next` 返回第一个 `is_done` 为 `false` 的任务。

这意味着：

- 任务顺序很重要，
- “下一个”类似队列，并非由计划器生成，
- 若任务列表按不同顺序编写，代理不应假设返回的是语义上最紧急的任务。

## 10. 会话级进度

`GET /sessions/current/task-progress` 返回从会话 `task_type` 得出的任务级进度。

系统支持以下进度模型：

- `area_search`
- `area_assignment_and_patrol`
- `target_assignment`
- `target_tracking`
- `others`

代理可将此端点用作粗略的任务信号，但任务执行仍应主要由任务队列和任务检查端点驱动。

## 11. 无人机状态模型

无人机对象包含以下运行状态：

- `id`
- `name`
- `status`
- `position`
- `heading`
- `speed`
- `battery_level`
- `max_speed`
- `max_altitude`
- `perceived_radius`
- `task_radius`
- `home_position`

这些字段对代理规划至关重要：

- `position`：导航用的当前位置
- `status`：指示是否适合起飞、降落、悬停或移动
- `battery_level`：任务可否安全继续
- `perceived_radius`：可感知的局部信息范围
- `task_radius`：许多任务相关检查所需的无人机接近距离
- `home_position`：安全回退与返回目标

## 12. 无人机指令模型

服务器支持两种指令风格：

- 通用：`POST /drones/{id}/command`
- 直接：`POST /drones/{id}/command/{command_name}`

两者均有效。对LLM代理而言，直接端点通常更简单，因为它们减少了格式歧义。

### 常见指令模式

起飞：

```bash
curl -X POST \
  -H "X-API-Key: <AGENT_API_KEY>" \
  "http://localhost:8000/drones/drone-1/command/take_off?altitude=20"
```

移动：

```bash
curl -X POST \
  -H "X-API-Key: <AGENT_API_KEY>" \
  "http://localhost:8000/drones/drone-1/command/move_to?x=120&y=80&z=20"
```

拍照：

```bash
curl -X POST \
  -H "X-API-Key: <AGENT_API_KEY>" \
  "http://localhost:8000/drones/drone-1/command/take_photo"
```

降落：

```bash
curl -X POST \
  -H "X-API-Key: <AGENT_API_KEY>" \
  "http://localhost:8000/drones/drone-1/command/land"
```

### 指令策略指导

推荐：

- 小批次动作，
- 在指令之间重新检查状态，
- 明确的高度控制，
- 明确的位置目标，
- 考虑电量的保守执行。

避免：

- 冗长且未经验证的指令链，
- 未重新读取无人机状态就假设移动成功，
- 假设AGENT实际不具备的隐藏地图知识。

## 13. 感知驱动规划

AGENT 通常不应依赖特权全局目标或障碍列表，而应使用局部感知：

- `GET /drones/{id}/nearby`
- `GET /drones/{id}/nearby/targets`
- `GET /drones/{id}/nearby/obstacles`
- `GET /drones/{id}/nearby/drones`

这将使智能体循环更加真实：

- 观察附近的实体，
- 推断对当前任务重要的内容，
- 谨慎移动，
- 移动后重新观察。

### 实用规划规则

- 如果任务引用了目标名称或地标，首先检查它是否已在感知范围内。
- 若不可见，则逐步移动，而非假设有一条直接的全局路径。
- 在决定穿越杂乱空间的路径前，再次检查附近的障碍物。
- 在决定靠近、悬停、搜索或验证时，使用无人机的 `task_radius` 和 `perceived_radius`。

## 14. 验证与完成

对于默认 AGENT，权威验证端点为：

- `GET /sessions/current/tasks/{task_id}/check`

此端点将在服务器端评估隐藏的任务验证逻辑。如果任务通过，服务器会将 `is_passed` 更新为 `true`。

### 为什么这很重要

`AGENT` 无法访问任务编写和评分所用的原始 `/check/*` 端点。这是有意为之。默认智能体应将任务检查视为服务器持有的契约，而非本地重新实现。

### 推荐的完成流程

1. 阅读任务。
2. 执行所需的最少操作。
3. 调用任务检查端点。
4. 如果结果为 `true`，标记任务完成。
5. 如果结果为 `false`，检查无人机状态和局部上下文，然后重试。

### 无隐藏检查的任务

如果任务没有 `execution_check_apis`，当前会话的任务检查端点会将其视为已通过。这意味着在需要时，任务可以编写为纯操作任务，但此类任务仍应表述清晰。

## 15. 推荐的 LLM 智能体架构

一个良好的实现通常包含四个内部阶段：

- `Observe`（观察）：读取当前会话、任务、无人机和感知信息
- `Plan`（规划）：选择下一个小的动作序列
- `Act`（执行）：执行一条或几条命令
- `Verify`（验证）：检查任务状态并更新完成情况

这可以实现为一个带有紧凑内存对象的循环：

```text
session_id
current_task_id
candidate_drone_ids
last_seen_drone_states
last_check_result
retry_count
```

### 设计原则

- 优先使用短周期计划，而非长脚本。
- 在执行有意义的操作后重新读取服务器状态。
- 将命令响应视为试探性的，直到状态确认它们为止。
- 将 `partial_success` 视为移动进展，而非终点到达。
- 使用 `successful_points` 和 `unsuccessful_points` 来了解已到达的请求路径航点。
- 限制重试次数。
- 在情况不明时，回退到安全状态，如悬停、返航或降落。

## 16. 多无人机策略

存在多架无人机时，智能体应基于以下因素选择无人机：

- 相对于任务的当前位置，
- 电量水平，
- 状态，
- 另一架无人机是否已经更靠近，
- 任务是否看起来可并行化。

推荐的模式：

- 使用一架无人机作为主要执行者，除非任务明确受益于协同。
- 避免无故向多架无人机发送冲突的命令。
- 仅在智能体架构明确建模了无人机间协调时使用 `send_message` 或 `broadcast`。

## 17. 错误处理

健壮的智能体应明确处理以下情况：

- `401 Unauthorized`（未授权）：密钥配置错误或缺失
- `403 Forbidden`（禁止）：智能体尝试使用非 AGENT 安全的端点
- `404 Not Found`（未找到）：缺少当前会话、任务、无人机或命令
- `400 Bad Request`（错误请求）：命令参数格式错误或无效的状态转换

典型的恢复规则：

- 如果没有当前会话，停止并报告配置/运行时问题。
- 如果没有待处理任务，则优雅停止。
- 如果命令失败，在重试前重新读取无人机和当前任务状态。
- 如果反复的任务检查失败，从执行模式切换到诊断模式，并收集新的上下文。

## 18. 端到端工作流示例

以下顺序是一个良好的基线：

1. `GET /sessions/current`
2. `GET /sessions/current/tasks/next`
3. `GET /drones`
4. `GET /drones/{id}`
5. `GET /drones/{id}/nearby`
6. 一条或多条无人机命令调用
7. `GET /sessions/current/tasks/{task_id}/check`
8. `POST /sessions/current/tasks/{task_id}/mark-done`

示例 shell 流程：

```bash
# 1. Get next task
curl -H "X-API-Key: <AGENT_API_KEY>" \
  http://localhost:8000/sessions/current/tasks/next

# 2. Inspect drones
curl -H "X-API-Key: <AGENT_API_KEY>" \
  http://localhost:8000/drones

# 3. Move a drone
curl -X POST \
  -H "X-API-Key: <AGENT_API_KEY>" \
  "http://localhost:8000/drones/drone-1/command/move_to?x=100&y=100&z=20"

# 4. Check completion
curl -H "X-API-Key: <AGENT_API_KEY>" \
  http://localhost:8000/sessions/current/tasks/task-1/check

# 5. Mark done if passed
curl -X POST \
  -H "X-API-Key: <AGENT_API_KEY>" \
  http://localhost:8000/sessions/current/tasks/task-1/mark-done
```

## 19. Python 示例

```python
import requests

BASE_URL = "http://localhost:8000"
HEADERS = {"X-API-Key": "<AGENT_API_KEY>"}

session_resp = requests.get(f"{BASE_URL}/sessions/current", headers=HEADERS)
session_resp.raise_for_status()
session_data = session_resp.json()

task_resp = requests.get(f"{BASE_URL}/sessions/current/tasks/next", headers=HEADERS)
task_resp.raise_for_status()
task = task_resp.json()

drones_resp = requests.get(f"{BASE_URL}/drones", headers=HEADERS)
drones_resp.raise_for_status()
drones = drones_resp.json()

if not drones:
    raise RuntimeError("No drones available")

drone_id = drones[0]["id"]

move_resp = requests.post(
    f"{BASE_URL}/drones/{drone_id}/command/move_to",
    headers=HEADERS,
    params={"x": 100, "y": 100, "z": 20},
)
move_resp.raise_for_status()

check_resp = requests.get(
    f"{BASE_URL}/sessions/current/tasks/{task['id']}/check",
    headers=HEADERS,
)
check_resp.raise_for_status()
check_data = check_resp.json()

if check_data.get("result"):
    done_resp = requests.post(
        f"{BASE_URL}/sessions/current/tasks/{task['id']}/mark-done",
        headers=HEADERS,
    )
    done_resp.raise_for_status()
```

此示例有意保持简单。生产级智能体应：

- 慎重选择无人机，
- 在移动前读取局部上下文，
- 处理重试，
- 在命令执行后验证状态，
- 为每个任务设置有限的操作预算。

## 20. 任务编写者指南

如果你正在设计 AGENT 模式下 LLM 应能完成的任务，请遵循以下规则：

- 将操作目标放在 `content` 中，而不仅仅放在隐藏的检查逻辑中。
- 假设运行时智能体无法访问隐藏字段。
- 使成功能够通过正常的 AGENT 操作和服务器端任务检查观察到。
- 避免要求 AGENT 无法获取的特权世界知识。
- 使用可通过感知和运动落实的明确目标名称、区域或行为。

良好的 AGENT 兼容任务应能从可见的任务文本中理解，并可通过正常的无人机控制和观测来解决。

## 21. SYSTEM 与 ADMIN 工具化指南

`SYSTEM` 和 `ADMIN` 角色适用于：

- 创建会话，
- 编写任务，
- 编辑场景实体，
- 运行评分检查，
- 调试代理故障，
- 导出或重置场景。

请将此与运行时代理行为分开。最清晰的平台设计是：

- `SYSTEM`/`ADMIN` 准备并评估场景，
- `AGENT` 仅使用 AGENT 安全的能力来解决场景。

## 22. 常见陷阱

### 构建期望隐藏任务字段的代理

此做法会失败，因为 AGENT 响应有意屏蔽了 `related_apis`、`commands` 和 `execution_check_apis`。

### 将 `/check/*` 视为 AGENT 合约的一部分

这些端点用于更高权限的评分和工具化，而非默认的 AGENT 执行。

### 假设具备全局地图知识

AGENT 通常应根据可见的任务文本、无人机状态和附近感知来导航，而非依据特权目标/障碍物列表。

### 在检查之前标记为完成

这会产生虚假完成，并削弱代理的可靠性。

### 缺乏观察的长指令链

这会增加漂移、无效假设和可避免故障的风险。

## 23. LLM 代理的推荐起始提示词

以下提示词结构适用于纯 AGENT 集成：

```text
You are an autonomous drone task agent. You may use only AGENT-role endpoints and the AGENT API key.
Work only against the current active session.
Your loop is: read current mission context, get the next pending task, inspect drones, gather nearby perception, take a small number of actions, check the task, and mark it done only when it passes.
Do not assume access to hidden validation logic, privileged global target lists, obstacle lists, or ADMIN/SYSTEM endpoints.
Prefer short-horizon, verifiable actions and re-read state after acting.
```

## 24. 交叉引用

- [API_REFERENCE_ZH.md](./API_REFERENCE_ZH.md)
- [API_DOCUMENTATION_ZH.md](./API_DOCUMENTATION_ZH.md)
- [AUTHENTICATION_ZH.md](./AUTHENTICATION_ZH.md)
- [TASK_TEMPLATE_EDIT_GUIDE_ZH.md](./TASK_TEMPLATE_EDIT_GUIDE_ZH.md)

## 25. 总结

为此服务器构建 LLM 代理最安全、最正确的方法是：

- 以 `AGENT` 身份进行认证，
- 仅在当前会话中操作，
- 根据可见的任务文本和可观测状态解决任务，
- 使用局部无人机感知而非特权全局知识，
- 通过当前会话的任务检查端点验证完成情况，
- 仅在验证后将任务标记为完成。

这是该服务器向默认自主代理暴露的核心合约。
