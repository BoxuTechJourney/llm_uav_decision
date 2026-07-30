# GridUAV v0 平台规格

本文档是 GridUAV v0 实现的权威依据。此前的研究与架构文档仅作为背景材料。

## 1. 冻结范围

GridUAV v0 提供二维静态障碍网格、一个或多个 UAV、一个隐藏目标、确定性局部感知、JSONL
轨迹、离线 PNG/GIF 回放、random/sweep/greedy 基线、PettingZoo `ParallelEnv`
适配器，以及使用配对随机种子的批量评测。

贝叶斯信念、EIG、LLM 集成、语义地图、Scout-Responder 角色、多目标、噪声感知、动态障碍、
实时 UI、Pygame 和随机障碍生成均不在范围内。

坐标始终使用 `(row, col)`，左上角为 `(0, 0)`。

## 2. 核心接口与数据模式

```python
model = GridUAVModel(config)
state, observation = model.reset(seed)
transition = model.step(state, actions)
```

`GridUAVModel` 是纯进程内模块。`step` 是确定性的，不写文件、不调用策略，也不持有可变的
episode 状态。

公开核心类型均为不可变 dataclass：

- `Cell(row, col)`。
- `UAVState(uav_id, cell)`。
- `WorldState(obstacle_map, target_cell, uav_states, observed_count,
  target_detected, step, terminated, truncated)`。
- `SensorResult(uav_id, visible_cells, newly_observed_cells, detected)`。
- `AgentObservation(obstacle_map, observed_mask, uav_states,
  latest_sensor_results, step)`。
- `MoveAction(destination)`。
- `ActionResult(uav_id, requested_destination, previous_cell, next_cell,
  status, reason, distance_delta)`。
- `Transition(previous_state, next_state, observation, action_results,
  sensor_results, terminated, truncated, success, info)`。

核心类型公开的 NumPy 数组均为只读。`AgentObservation` 绝不包含 `target_cell` 或
`WorldState`。

`ScenarioConfig` 包含 `env_id`、网格尺寸、显式障碍 cell、固定 UAV id 与起始 cell、一个
可选的固定目标 cell、感知半径以及 `max_steps`。省略目标时，使用种子控制的随机放置。
配置校验会拒绝无效尺寸、重复的 id 或起点、越界或相互重叠的起点/障碍、无效目标、负感知
半径以及非正的步数上限。

## 3. Reset 与 step 语义

随机目标从排序后的可通行 cell 中均匀采样；候选 cell 必须至少可由一架 UAV 到达，并且
位于所有初始感知足迹的并集之外。固定目标可以在初始时可见，此时 reset 会返回 step 0
成功终止状态。

每架 UAV 在 reset 后以及每次 step 后进行感知。可见范围是配置半径内、位于边界内的
Chebyshev 球；障碍不会遮挡感知。每架 UAV 都会对每个可见 cell 的 `observed_count`
加一，重叠区域也分别累计。任何感知足迹包含目标时即发生检测。

动作可以指定任意目标 cell。每个 step 最多沿确定性最短路径前进一个网格线段：

- 使用 8 邻域移动；
- 直移代价为 `1`，斜移代价为 `sqrt(2)`；
- 禁止斜向穿过障碍角；
- 按 `(row, col)` 确定性打破平局。

缺失动作时原地停留，并记录 `invalid/missing_action`。未知 UAV id 会被忽略，并列入
`Transition.info["unknown_action_ids"]`。目的地越界、位于障碍上或不可达时，产生稳定的
status/reason 值。

移动提议同时解析。静止占用者保留其 cell。否则，多个 UAV 争用同一目的地时，由
UAV id 字典序最小者胜出。允许跟随链进入同一步中同步腾出的 cell。交换以及更长的闭合
占用环会被阻止。阻塞会沿跟随链向后传播。

检测会设置 `terminated=True` 和 `success=True`。未检测到目标并达到 `max_steps`
时设置 `truncated=True`。若二者发生在同一步，以检测结果优先。对已经终止或截断的状态
调用 `step` 会引发 `RuntimeError`。

## 4. 策略与 PettingZoo 适配器

`TeamPolicy` 接收共享的 `AgentObservation`，并返回包含所有 UAV 动作的一个映射。策略
持有自己的 RNG，且不能接收 `WorldState`。

- Random 为每架 UAV 独立采样可通行的目的地。
- Sweep 从共享的逐行往返 lawn-mower 序列中分配互不相同的下一 cell。
- Greedy 按 UAV id 顺序分配最近且未被预留的未观测 cell，并使用与 core 相同的路径
  度量和平局规则。

`GridUAVParallelEnv` 使用 `MultiDiscrete([height, width])` 动作。每个 agent 都收到
相同的 Gymnasium `Dict` observation，其中包含障碍 mask、已观测 mask、所有 UAV 位置、
各 UAV 最新检测结果以及 step。终止结果会返回给该 step 之前处于 active 状态的 agent，
随后 `agents` 变为空。

在成功 step 中，每个 active agent 获得 `+1.0`。否则，动作结果为 `moved` 的 agent
获得 `-0.01`，所有其他 agent 获得 `0.0`。奖励仅用于兼容，不作为研究指标。

## 5. Trace 与 replay

`trace.jsonl` 数据模式版本 1 是自包含的：

1. 一条 `header` 记录，包含数据模式版本、seed、policy、序列化 scenario、初始私有
   state 和初始公共 observation。
2. 每个 transition 对应一条 `step` 记录，包含 actions、action results、sensor
   results、完整 next state、公共 observation 和终止标志。

Replay 只读取 trace，绝不调用 core。对于 `T` 个 transition，它会先为初始状态生成
`replay_step_000.png`，再生成 `T` 个 transition 帧，随后以相同顺序生成 GIF。

- `public`：绝不绘制目标真值；可以显示公共检测状态。
- `debug`：始终绘制目标真值。
- `paper`：仅从第一个已检测状态开始绘制目标真值。

Trace 包含私有真值，不得作为公共产物分发。

## 6. 评测与验收

批量评测会在同一组有序 seed 上运行配置的每一种 policy。CSV 行先按 seed 排序，再按配置
中的 policy 顺序排序。字段包括：`episode_id`、`seed`、`policy`、`num_uav`、
`grid_width`、`grid_height`、`success`、`time_to_discovery`、
`total_distance`、`coverage_ratio`、`coverage_redundancy`、
`blocked_actions`、`invalid_actions` 和 `makespan`。发现失败时，
`time_to_discovery` 留空。

覆盖率只统计可通行 cell。冗余度定义为：
`(可通行 cell 的观测总次数 - 已观测的不同可通行 cell 数) /
可通行 cell 的观测总次数`；没有观测时取零。

验收要求全部 pytest 测试、PettingZoo `parallel_api_test` 和
`parallel_seed_test`、单 UAV 与三 UAV 策略 smoke run、batch CLI 输出、离线 replay
输出以及最终 code review 全部通过。
