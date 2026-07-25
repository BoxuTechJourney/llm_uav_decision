# MultiUAV-Plat 服务器系统 API 参考

**面向开发者的快速参考指南**

> 如需包含示例的完整文档，请参阅 [API_DOCUMENTATION_ZH.md](API_DOCUMENTATION_ZH.md)

## 基础 URL

```
http://localhost:8000
```

**交互式文档:** http://localhost:8000/docs

## 认证

该 API 使用基于角色的访问控制，包含四种角色:

| 角色 | 权限 | API 密钥要求 |
|------|--------|-----------------|
| **USER** | 基本（控制与查看） | Yes |
| **AGENT** | 与 USER 相同 | Yes |
| **SYSTEM** | 管理 + USER/AGENT | Yes |
| **ADMIN** | 完全访问 | Yes |

**请求头:** `X-API-Key: <your-key>`

若未提供 API 密钥，服务器默认使用 AGENT 角色。USER、SYSTEM 和 ADMIN 各自接受多个硬编码的权限密钥；实际密钥值存储在软件中，未在文档中列出。

详情请参阅 [AUTHENTICATION_ZH.md](AUTHENTICATION_ZH.md)。

---

## 快速链接

| 类别 | 端点 |
|----------|-----------|
| [健康检查](#health-check) | 服务器状态 |
| [会话](#session-management) | 会话增删改查、重置、恢复 |
| [会话跟踪](#session-tracking) | 命令历史、状态、到达、覆盖范围 |
| [任务管理](#task-management) | 任务增删改查、标记完成/待处理 |
| [无人机](#drone-management) | 无人机增删改查、电池 |
| [命令](#command-management) | 通用命令与直接命令 |
| [目标](#target-management) | 目标与航点 |
| [障碍物](#obstacle-management) | 障碍物与碰撞 |
| [环境](#environment-management) | 天气条件 |
| [邻近查询](#proximity) | 某无人机周围的邻近实体 |
| [检查](#check-endpoints-admin-only) | 状态验证（仅限 ADMIN） |

---

## 健康检查

| 方法 | 端点 | 响应 |
|--------|----------|----------|
| GET | `/` | `{"status":"online","message":"..."}` |
| GET | `/version` | `{"name":"...","version":"1.0.0"}` |

## 无人机管理

| 方法 | 端点 | 描述 |
|--------|----------|-------------|
| GET | `/drones` | 列出所有无人机 |
| POST | `/drones` | 注册新无人机 |
| GET | `/drones/{id}` | 获取无人机详情 |
| PUT | `/drones/{id}` | 更新无人机属性（元数据、状态、电池、位置、返航点） |
| PUT | `/drones/{id}/position` | 仅更新无人机位置 |
| DELETE | `/drones/{id}` | 删除无人机 |
| POST | `/drones/{id}/battery` | 更新电池电量 |
| POST | `/drones/land_all` | 立即降落所有无人机（SYSTEM+，管理命令） |
| POST | `/drones/charge_all` | 将所有无人机充满电（SYSTEM+，管理命令） |

## 命令管理

### 通用命令端点

| 方法 | 端点 | 描述 |
|--------|----------|-------------|
| POST | `/drones/{id}/command` | 发送任意命令 |
| GET | `/drones/{id}/commands` | 获取命令历史 |
| GET | `/commands/{command_id}` | 获取命令状态 |

### 直接命令端点

所有命令均使用 **POST** 方法与 `/drones/{id}/command/{command_name}` 路径。

| 命令 | 参数 | 描述 |
|---------|-----------|-------------|
| `take_off` | `?altitude=10.0` | 起飞至指定高度 |
| `land` | - | 在某位置降落 |
| `move_to` | `?x=50&y=50&z=15` | 移动至指定坐标；电池消耗无基础值 |
| `move_towards` | `?distance=20&heading=90` | 向某方向移动指定距离（若未指定航向，则使用当前航向） |
| `move_along_path` | 请求体：`{waypoints:[...]}` | 沿一个或多个航点飞行；二维航点使用当前高度；电池消耗无单个航点基础费用 |
| `change_altitude` | `?altitude=20.0` | 仅改变高度 |
| `hover` | `duration`（可选） | 保持位置悬停 |
| `rotate` | `?heading=180.0` | 改变航向/方向 |
| `return_home` | - | 返回出发点 |
| `set_home` | - | 设置返航点 |
| `calibrate` | - | 校准传感器 |
| `take_photo` | - | 拍照 |
| `send_message` | `?target_drone_id=X&message=Y` | 向指定无人机发送消息 |
| `broadcast` | `?message=text` | 向所有无人机广播 |
| `charge` | `?charge_amount=30.0` | 充电 |

## 目标管理

| 方法 | 端点 | 描述 |
|--------|----------|-------------|
| GET | `/targets` | 列出所有目标 |
| POST | `/targets` | 创建目标 |
| GET | `/targets/{id}` | 获取目标详情 |
| PUT | `/targets/{id}` | 更新目标 |
| DELETE | `/targets/{id}` | 删除目标 |
| GET | `/targets/type/{type}` | 按类型获取 |
| POST | `/targets/waypoints/{id}/check-drone` | 检查无人机是否在航点充电范围内 |



## 环境管理

| 方法 | 端点 | 描述 |
|--------|----------|-------------|
| GET | `/environments` | 列出所有环境 |
| POST | `/environments` | 创建环境 |
| GET | `/environments/current` | 获取当前活动环境 |
| POST | `/environments/{id}/set-current` | 设为当前活动环境 |
| GET | `/environments/{id}` | 获取环境详情 |
| PUT | `/environments/{id}` | 更新环境 |
| DELETE | `/environments/{id}` | 删除环境 |

## 障碍物管理

| 方法 | 端点 | 描述 |
|--------|----------|-------------|
| GET | `/obstacles` | 列出所有障碍物 |
| POST | `/obstacles` | 创建障碍物 |
| GET | `/obstacles/{id}` | 获取障碍物 |
| PUT | `/obstacles/{id}` | 更新障碍物 |
| DELETE | `/obstacles/{id}` | 删除障碍物 |
| GET | `/obstacles/type/{type}` | 按类型获取 |

### 碰撞检测

| 方法 | 端点 | 描述 | 认证 |
|--------|----------|-------------|------|
| POST | `/obstacles/path_collision` | 检查飞行路径是否与障碍物碰撞 | SYSTEM |
| POST | `/obstacles/point_collision` | 检查点是否在任何障碍物内（返回所有匹配项） | SYSTEM |

## 邻近

| 方法 | 端点 | 描述 |
|--------|----------|-------------|
| GET | `/drones/{id}/nearby` | 聚合附近的无人机、目标和障碍物（使用无人机的 perceived_radius） |
| GET | `/drones/{id}/nearby/drones` | 附近的无人机（使用无人机的 perceived_radius） |
| GET | `/drones/{id}/nearby/targets` | 附近的目标（使用无人机的 perceived_radius） |
| GET | `/drones/{id}/nearby/obstacles` | 附近的障碍物（使用无人机的 perceived_radius） |

所有邻近端点均使用无人机的 `perceived_radius` 来确定搜索区域。

## 会话管理

| 方法 | 端点 | 描述 |
|--------|----------|-------------|
| GET | `/sessions` | 列出所有会话（AGENT+ 权限，AGENT/USER 仅返回元数据） |
| POST | `/sessions` | 创建新会话并自动生成ID（默认返回完整数据） |
| POST | `/sessions/{id}` | 使用指定ID创建或恢复会话（默认返回完整数据，智能实体检测） |
| GET | `/sessions/current` | 获取当前活动会话（支持 `?data=true` 返回完整数据） |
| GET | `/sessions/current/data` | 获取当前活动会话的完整数据 |
| POST | `/sessions/current/reset` | **新增：** 重置当前会话历史记录（清除统计/历史，保留实体）（SYSTEM+ 权限） |
| GET | `/sessions/{id}` | 获取指定会话（支持 `?data=true` 返回完整数据） |
| PUT | `/sessions/{id}` | 更新会话元数据（支持 `?data=true`） |
| DELETE | `/sessions/{id}` | 删除会话 |
| POST | `/sessions/{id}/set-current` | 设为当前活动会话（AGENT+ 权限，AGENT/USER 仅返回元数据） |
| POST | `/sessions/{id}/reset` | 重置为初始状态（SYSTEM+ 权限） |
| GET | `/sessions/{id}/data` | 导出完整的会话数据 |

会话创建端点接受可选的 `creator` 参数；如果省略，服务器将记录调用者的角色。

---

## 会话跟踪

| 方法 | 端点 | 描述 |
|--------|----------|-------------|
| GET | `/sessions/current/request-history` | 当前会话最近的 HTTP 请求（可通过查询参数 `limit` 限制数量） |
| GET | `/sessions/{id}/request-history` | 指定会话最近的 HTTP 请求（可通过查询参数 `limit` 限制数量） |
| DELETE | `/sessions/current/request-history` | 清除当前会话的运行时请求历史（SYSTEM+ 权限） |
| DELETE | `/sessions/{id}/request-history` | 清除指定会话的运行时请求历史（SYSTEM+ 权限） |
| GET | `/sessions/current/command-history` | 当前会话最近的命令（可通过查询参数 `limit` 限制数量） |
| GET | `/sessions/{id}/command-history` | 最近的命令（可通过查询参数 `limit` 限制数量） |
| GET | `/sessions/{id}/status-history` | 状态变更记录（可选的 `drone_id` 参数） |
| GET | `/sessions/{id}/target-reaches` | 简洁的目标到达摘要与统计 |
| GET | `/sessions/{id}/moving-target-tracking` | 简洁的移动目标跟踪摘要 |
| GET | `/sessions/{id}/area-coverage` | 覆盖数据与摘要 |
| GET | `/sessions/{id}/task-progress` | 基于任务类型的任务完成进度 |

请求历史记录包含请求/响应详情，以及直接套接字
`client_ip`/`client_port`、解析后的 `client_privilege`、
`authentication_status`、关联的 `session_id`、`query_params`、一个
长度限制为512字符的 `user_agent` 和 `agent_id`。API 密钥和转发
的客户端IP头不会被暴露或信任。查询参数值保留为原始字符串
以便回放，重复的键以有序数组表示，敏感键会被脱敏，并且
缺失的旧版 `query_params` 值将规范化为 `{}`。

请求历史记录的存储默认每会话保留5,000条记录，并可通过
`main.py --request-history-limit N` 进行更改。端点的 `limit` 查询
参数仍然限制为每条响应最多1,000条记录。

请求历史记录仅在运行时存在，并且只能通过专用的
请求历史记录端点获取。它不包含在会话对象、导出、
导入和恢复中，并且在服务器进程退出时会丢失。
出于性能和递归安全的考虑，请求历史记录端点的响应正文会特意从
结构化 API 日志和会话请求历史记录中省略，
以避免递归安全问题。
`client_privilege` 使用大写的角色名称：`AGENT`、`USER`、`SYSTEM` 和
`ADMIN`。AGENT 客户端仅能调用 `GET /sessions/current/request-history`；
它们只能看到经过 AGENT 认证的记录，且这些记录具有相同的规范化 `X-Agent-ID`
值。没有 `X-Agent-ID` 的 AGENT 请求会被归属到 `default_agent`。
SYSTEM 和 ADMIN 客户端可以看到未过滤的请求历史，包括
`GET /sessions/{id}/request-history`。

SYSTEM 和 ADMIN 客户端可以通过以下方式清除运行时请求历史：
`DELETE /sessions/current/request-history` 或
`DELETE /sessions/{id}/request-history`。这些操作仅清除请求历史，
返回 `{"cleared": true, "session_id": "...", "cleared_count": N}`，并且是
不会被记录回已清除的请求历史中。

**关于目标访问次数的说明**：对同一目标的多次访问仍会在内部记录，但 API 返回的是简洁的分组摘要，而非原始的无限事件日志。



---

## 任务管理

| 方法 | 端点 | 描述 |
|--------|----------|-------------|
| GET | `/sessions/current/tasks` | 获取当前会话中的所有任务（AGENT+） |
| GET | `/sessions/current/tasks/next` | 获取当前会话中下一个待处理任务（AGENT+） |
| GET | `/sessions/current/tasks/{task_id}` | 从当前会话中获取特定任务（AGENT+） |
| GET | `/sessions/current/tasks/{task_id}/check` | 检查任务，并在通过时设置 is_passed；可选 `since_timestamp` 参数限定兼容的历史记录检查范围（AGENT+） |
| POST | `/sessions/current/tasks/{task_id}/mark-done` | 在当前会话中将任务标记为已完成（AGENT+） |
| POST | `/sessions/current/tasks/{task_id}/mark-pending` | 在当前会话中将任务标记为待处理（AGENT+） |
| GET | `/sessions/{session_id}/tasks` | 获取某个会话中的所有任务（USER+） |
| GET | `/sessions/{session_id}/tasks/{task_id}` | 获取特定任务（USER+） |
| POST | `/sessions/{session_id}/tasks` | 创建新任务（SYSTEM+） |
| PUT | `/sessions/{session_id}/tasks/{task_id}` | 更新任务（SYSTEM+） |
| DELETE | `/sessions/{session_id}/tasks/{task_id}` | 删除任务（SYSTEM+） |
| POST | `/sessions/{session_id}/tasks/{task_id}/mark-done` | 将任务标记为已完成（SYSTEM+） |
| POST | `/sessions/{session_id}/tasks/{task_id}/mark-pending` | 将任务标记为待处理（SYSTEM+） |
| POST | `/sessions/{session_id}/tasks/swap` | 交换两个任务的顺序（SYSTEM+） |

**注意：**
- `related_apis` 是一个对象数组，每个对象包含：
- `endpoint`：API 端点路径（例如 `/drones/{id}/command/move_to`）
- `parameters`：参数名到描述/示例值的字典
- `execution_check_apis` 是一个结构化对象，描述 `/check` 调用的逻辑组合：
- `logic`：`and`（默认）、`or` 或 `not`
- `checks`：子节点数组
- 叶子节点包含 `endpoint`（例如 `/check/drone_position`）、`parameters`（字典）、可选的 `expect`（布尔值，默认为 `true`）表示预期的 `result`
- `GET /sessions/current/tasks/{task_id}/check?since_timestamp=...` 将时间戳传递给接受 `since_timestamp` 的兼容 `/check` 叶子端点。叶子级别的 `parameters.since_timestamp` 优先级更高。

**任务请求体（POST /sessions/{session_id}/tasks）：**
```json
{
  "name": "area-search-alpha",
  "content": "Seach the area alpha",
  "content_aliases": ["search alpha", "scan zone 1"],
  "description": "Brief description",
  "creator": "mission-lead",
  "originated_from": "mission-lead",
  "difficulty": "medium",
  "related_apis": [
    {
      "endpoint": "/drones/{id}/command/move_to",
      "parameters": {
        "x": "X coordinate in meters",
        "y": "Y coordinate in meters",
        "z": "Z coordinate (altitude) in meters"
      }
    },
    {
      "endpoint": "/drones/{id}/command/take_photo",
      "parameters": {}
    }
  ],
  "execution_check_apis": {
    "logic": "and",
    "checks": [
      {
        "endpoint": "/check/drone_position",
        "parameters": {
          "drone_id": "drone-1",
          "x": "Expected X",
          "y": "Expected Y",
          "tolerance": "Distance tolerance"
        },
        "expect": true
      },
      {
        "logic": "or",
        "checks": [
          {
            "endpoint": "/check/task_done",
            "parameters": {},
            "expect": true
          },
          {
            "endpoint": "/check/task_progress",
            "parameters": { "expected_progress": 0.9 },
            "expect": true
          }
        ]
      }
    ]
  },
  "commands": ["take_off", "move_to", "take_photo", "land"]
}
```

如果省略 `creator`，服务器会将调用者的角色记录为创建者。

**任务响应：**
```json
{
  "id": "task-abc123",
  "name": "area-search-alpha",
  "content": " Search Area Alpha for Targets",
  "content_aliases": ["search alpha", "scan zone 1"],
  "description": "Brief description",
  "creator": "system",
  "originated_from": "system",
  "related_apis": [
    {
      "endpoint": "/drones/{id}/command/move_to",
      "parameters": {
        "x": "X coordinate in meters",
        "y": "Y coordinate in meters",
        "z": "Z coordinate (altitude) in meters"
      }
    }
  ],
  "execution_check_apis": {
    "logic": "and",
    "checks": []
  },
  "commands": ["take_off", "move_to", "take_photo", "land"],
  "is_done": false,
  "is_passed": false,
  "created_at": 1620000000.0,
  "last_updated": 1620000000.0
}
```

**交换任务请求体（POST /sessions/{session_id}/tasks/swap）：**
```json
{
  "task_id_1": "task-abc123",
  "task_id_2": "task-def456"
}
```

**交换任务响应（200 OK）：**
返回会话中所有任务按其新顺序组成的数组：
```json
[
  {
    "id": "task-def456",
    "name": "area-patrol-bravo",
    "content": "Patrol area bravo...",
    "description": "Brief description",
    "creator": "system",
    "difficulty": "medium",
    "related_apis": [],
    "commands": [],
    "is_done": false,
    "is_passed": false,
    "created_at": 1620000000.0,
    "last_updated": 1620000000.0
  },
  {
    "id": "task-abc123",
    "name": "area-search-alpha",
    "content": "Search area alpha...",
    "description": "Brief description",
    "creator": "system",
    "difficulty": "easy",
    "related_apis": [],
    "commands": [],
    "is_done": false,
    "is_passed": false,
    "created_at": 1620000000.0,
    "last_updated": 1620000000.0
  }
]
```

---

## 快速参考 - 数据模型

### 关键请求体

#### 注册无人机（POST /drones）

**请求体：**
```json
{
  "name": "Scout Alpha",
  "model": "Model-D4",
  "max_speed": 20.0,
  "max_altitude": 120.0,
  "battery_capacity": 4000.0,
  "position": {"x": 100.0, "y": 100.0, "z": 0.0},
  "heading": 45.0,
  "speed": 0.0,
  "battery_volume": 3200.0,
  "status": "idle",
  "home_position": {"x": 0.0, "y": 0.0, "z": 0.0},
  "perceived_radius": 100.0,
  "task_radius": 10.0
}
```

**响应（201 Created）：**
```json
{
  "id": "d4f3a9b2",
  "name": "Scout Alpha",
  "model": "Model-D4",
  "status": "idle",
  "position": {"x": 100.0, "y": 100.0, "z": 0.0},
  "heading": 45.0,
  "speed": 0.0,
  "battery_level": 100.0,
  "battery_volume": 4000.0,
  "battery_capacity": 4000.0,
  "max_speed": 20.0,
  "max_altitude": 120.0,
  "perceived_radius": 100.0,
  "task_radius": 10.0,
  "home_position": {"x": 100.0, "y": 100.0, "z": 0.0},
  "created_at": 1704067200.0,
  "last_updated": 1704067200.0
}
```

#### 更新无人机（PUT /drones/{id}）

**请求体（所有字段均为可选）：**
```json
{
  "name": "Scout Alpha Updated",
  "model": "Model-D5",
  "max_speed": 25.0,
  "max_altitude": 150.0,
  "battery_capacity": 5000.0,
  "perceived_radius": 120.0,
  "task_radius": 15.0,
  "status": "hovering",
  "position": {"x": 100.0, "y": 50.0, "z": 20.0},
  "heading": 90.0,
  "speed": 5.0,
  "battery_level": 80.0,
  "battery_volume": 4000.0,
  "home_position": {"x": 0.0, "y": 0.0, "z": 0.0}
}
```

**部分位置更新（仅高度）：**
```json
{
  "position": {"z": 25.0}
}
```

**响应（200 OK）：**
```json
{
  "id": "d4f3a9b2",
  "name": "Scout Alpha Updated",
  "model": "Model-D5",
  "status": "hovering",
  "position": {"x": 100.0, "y": 50.0, "z": 20.0},
  "heading": 90.0,
  "speed": 5.0,
  "battery_level": 80.0,
  "battery_volume": 4000.0,
  "battery_capacity": 5000.0,
  "max_speed": 25.0,
  "max_altitude": 150.0,
  "perceived_radius": 120.0,
  "task_radius": 15.0,
  "home_position": {"x": 0.0, "y": 0.0, "z": 0.0},
  "created_at": 1704067200.0,
  "last_updated": 1704067500.0
}
```

#### 发送指令
```json
POST /drones/{id}/command
{
  "command": "move_to",
  "parameters": {"x": 50.0, "y": 50.0, "z": 15.0}
}
```

#### 创建目标（POST /targets）

**请求体（固定目标）：**
```json
{
  "name": "Checkpoint Alpha",
  "type": "fixed",
  "position": {"x": 100.0, "y": 50.0, "z": 0.0},
  "radius": 5.0,
  "description": "Primary checkpoint for mission"
}
```

**响应（201 Created）：**
```json
{
  "id": "t1a2b3c4",
  "name": "Checkpoint Alpha",
  "type": "fixed",
  "position": {"x": 100.0, "y": 50.0, "z": 0.0},
  "description": "Primary checkpoint for mission",
  "radius": 5.0,
  "velocity": null,
  "moving_path": null,
  "current_path_index": null,
  "charge_amount": null,
  "vertices": null,
  "created_at": 1704067200.0,
  "last_updated": 1704067200.0
}
```

**请求体（路径点/充电站）：**
```json
{
  "name": "Charging Station 1",
  "type": "waypoint",
  "position": {"x": 100.0, "y": 50.0, "z": 0.0},
  "radius": 10.0,
  "charge_amount": 30.0,
  "description": "Primary charging station"
}
```

**响应（201 Created）：**
```json
{
  "id": "w5d6e7f8",
  "name": "Charging Station 1",
  "type": "waypoint",
  "position": {"x": 100.0, "y": 50.0, "z": 0.0},
  "description": "Primary charging station",
  "radius": 10.0,
  "velocity": null,
  "moving_path": null,
  "current_path_index": null,
  "charge_amount": 30.0,
  "vertices": null,
  "created_at": 1704067200.0,
  "last_updated": 1704067200.0
}
```

**请求体（移动目标）：**
```json
{
  "name": "Moving Target 1",
  "type": "moving",
  "position": {"x": 50.0, "y": 50.0, "z": 10.0},
  "radius": 3.0,
  "velocity": {"x": 2.0, "y": 1.0, "z": 0.0},
  "moving_path": [
    {"x": 50.0, "y": 50.0, "z": 10.0},
    {"x": 100.0, "y": 80.0, "z": 10.0},
    {"x": 150.0, "y": 50.0, "z": 10.0}
  ],
  "description": "Patrol target with predefined path"
}
```

**响应（201 Created）：**
```json
{
  "id": "m9g0h1i2",
  "name": "Moving Target 1",
  "type": "moving",
  "position": {"x": 50.0, "y": 50.0, "z": 10.0},
  "description": "Patrol target with predefined path",
  "radius": 3.0,
  "velocity": {"x": 2.0, "y": 1.0, "z": 0.0},
  "moving_path": [
    {"x": 50.0, "y": 50.0, "z": 10.0},
    {"x": 100.0, "y": 80.0, "z": 10.0},
    {"x": 150.0, "y": 50.0, "z": 10.0}
  ],
  "current_path_index": 0,
  "moving_duration": 10.0,
  "path_direction": 1,
  "time_in_direction": 0.0,
  "movement_mode": "velocity",
  "calculated_speed": null,
  "last_motion_update": 1704067200.0,
  "tracking_status": "never_tracked",
  "last_tracked_at": null,
  "charge_amount": null,
  "vertices": null,
  "is_reached": false,
  "reached_by": [],
  "created_at": 1704067200.0,
  "last_updated": 1704067200.0
}
```

**请求体（移动目标 - 基于速度的乒乓模式 / 优先级1）：**
```json
{
  "name": "Oscillating Target",
  "type": "moving",
  "position": {"x": 100.0, "y": 100.0, "z": 5.0},
  "radius": 2.0,
  "velocity": {"x": 3.0, "y": 0.0, "z": 0.0},
  "moving_duration": 10.0,
  "description": "Target moving back and forth along X-axis every 10 seconds"
}
```

**响应（201 Created）：**
```json
{
  "id": "m9g0h1i3",
  "name": "Oscillating Target",
  "type": "moving",
  "position": {"x": 100.0, "y": 100.0, "z": 5.0},
  "description": "Target moving back and forth along X-axis every 10 seconds",
  "radius": 2.0,
  "velocity": {"x": 3.0, "y": 0.0, "z": 0.0},
  "moving_path": [],
  "current_path_index": 0,
  "moving_duration": 10.0,
  "path_direction": 1,
  "time_in_direction": 0.0,
  "movement_mode": "velocity",
  "calculated_speed": null,
  "last_motion_update": 1704067200.0,
  "tracking_status": "never_tracked",
  "last_tracked_at": null,
  "charge_amount": null,
  "vertices": null,
  "is_reached": false,
  "reached_by": [],
  "created_at": 1704067200.0,
  "last_updated": 1704067200.0
}
```

**请求体（移动目标 - 基于路径并自动调速 / 优先级2）：**
```json
{
  "name": "Patrol Target",
  "type": "moving",
  "position": {"x": 0.0, "y": 0.0, "z": 0.0},
  "radius": 2.0,
  "velocity": null,
  "moving_path": [
    {"x": 0, "y": 0, "z": 0},
    {"x": 100, "y": 0, "z": 0},
    {"x": 100, "y": 100, "z": 0}
  ],
  "moving_duration": 20.0,
  "description": "Target with auto-calculated speed from path and duration"
}
```

**响应（201 Created）：**
```json
{
  "id": "m9g0h1i4",
  "name": "Patrol Target",
  "type": "moving",
  "position": {"x": 0.0, "y": 0.0, "z": 0.0},
  "description": "Target with auto-calculated speed from path and duration",
  "radius": 2.0,
  "velocity": null,
  "moving_path": [
    {"x": 0, "y": 0, "z": 0},
    {"x": 100, "y": 0, "z": 0},
    {"x": 100, "y": 100, "z": 0}
  ],
  "current_path_index": 0,
  "moving_duration": 20.0,
  "path_direction": 1,
  "time_in_direction": 0.0,
  "movement_mode": "path",
  "calculated_speed": 10.0,
  "last_motion_update": 1704067200.0,
  "tracking_status": "never_tracked",
  "last_tracked_at": null,
  "charge_amount": null,
  "vertices": null,
  "is_reached": false,
  "reached_by": [],
  "created_at": 1704067200.0,
  "last_updated": 1704067200.0
}
// Path length: 100 + 100 = 200m
// Speed: 200m / 20s = 10 m/s (auto-calculated)
```

**请求体（圆形目标）：**
```json
{
  "name": "Search Area Alpha",
  "type": "circle",
  "position": {"x": 200.0, "y": 150.0, "z": 0.0},
  "radius": 25.0,
  "description": "Circular search area"
}
```

**响应（201 Created）：**
```json
{
  "id": "c3j4k5l6",
  "name": "Search Area Alpha",
  "type": "circle",
  "position": {"x": 200.0, "y": 150.0, "z": 0.0},
  "description": "Circular search area",
  "radius": 25.0,
  "velocity": null,
  "moving_path": null,
  "current_path_index": null,
  "charge_amount": null,
  "vertices": null,
  "created_at": 1704067200.0,
  "last_updated": 1704067200.0
}
```

**请求体（多边形目标）：**
```json
{
  "name": "Zone Bravo",
  "type": "polygon",
  "position": {"x": 100.0, "y": 100.0, "z": 0.0},
  "radius": 1.0,
  "vertices": [
    {"x": 100.0, "y": 100.0, "z": 0.0},
    {"x": 150.0, "y": 100.0, "z": 0.0},
    {"x": 150.0, "y": 150.0, "z": 0.0},
    {"x": 100.0, "y": 150.0, "z": 0.0}
  ],
  "description": "Rectangular patrol zone"
}
```

**响应（201 Created）：**
```json
{
  "id": "p7m8n9o0",
  "name": "Zone Bravo",
  "type": "polygon",
  "position": {"x": 100.0, "y": 100.0, "z": 0.0},
  "description": "Rectangular patrol zone",
  "radius": 1.0,
  "velocity": null,
  "moving_path": null,
  "current_path_index": null,
  "charge_amount": null,
  "vertices": [
    {"x": 100.0, "y": 100.0, "z": 0.0},
    {"x": 150.0, "y": 100.0, "z": 0.0},
    {"x": 150.0, "y": 150.0, "z": 0.0},
    {"x": 100.0, "y": 150.0, "z": 0.0}
  ],
  "created_at": 1704067200.0,
  "last_updated": 1704067200.0
}
```

#### 创建障碍物（POST /obstacles）

**请求体（圆形障碍物）：**
```json
{
  "name": "Building A",
  "type": "circle",
  "position": {"x": 50.0, "y": 50.0, "z": 0.0},
  "radius": 15.0,
  "height": 30.0,
  "description": "Circular building structure"
}
```

**响应（201 Created）：**
```json
{
  "id": "o1a2b3c4",
  "name": "Building A",
  "type": "circle",
  "position": {"x": 50.0, "y": 50.0, "z": 0.0},
  "description": "Circular building structure",
  "radius": 15.0,
  "width": null,
  "length": null,
  "vertices": [],
  "height": 30.0,
  "area": 706.8583470577034,
  "created_at": 1704067200.0,
  "last_updated": 1704067200.0
}
```

**请求体（椭圆障碍物）：**
```json
{
  "name": "Garden Pond",
  "type": "ellipse",
  "position": {"x": 100.0, "y": 80.0, "z": 0.0},
  "width": 25.0,
  "length": 18.0,
  "height": 0.0,
  "description": "Elliptical pond - no fly zone"
}
```

**响应（201 Created）：**
```json
{
  "id": "o5d6e7f8",
  "name": "Garden Pond",
  "type": "ellipse",
  "position": {"x": 100.0, "y": 80.0, "z": 0.0},
  "description": "Elliptical pond - no fly zone",
  "radius": null,
  "width": 25.0,
  "length": 18.0,
  "vertices": [],
  "height": 0.0,
  "area": 1413.7166941154069,
  "created_at": 1704067200.0,
  "last_updated": 1704067200.0
}
```

**请求体（点状障碍物）：**
```json
{
  "name": "Landing Marker",
  "type": "point",
  "position": {"x": 200.0, "y": 150.0, "z": 0.0},
  "radius": 2.0,
  "height": 0.5,
  "description": "Landing zone marker"
}
```

**响应（201 Created）：**
```json
{
  "id": "o9g0h1i2",
  "name": "Landing Marker",
  "type": "point",
  "position": {"x": 200.0, "y": 150.0, "z": 0.0},
  "description": "Landing zone marker",
  "radius": 2.0,
  "width": null,
  "length": null,
  "vertices": [],
  "height": 0.5,
  "area": 12.566370614359172,
  "created_at": 1704067200.0,
  "last_updated": 1704067200.0
}
```

**请求体（多边形障碍物）：**
```json
{
  "name": "Office Complex",
  "type": "polygon",
  "position": {"x": 50.0, "y": 50.0, "z": 0.0},
  "vertices": [
    {"x": 40.0, "y": 40.0, "z": 0.0},
    {"x": 60.0, "y": 40.0, "z": 0.0},
    {"x": 60.0, "y": 60.0, "z": 0.0},
    {"x": 40.0, "y": 60.0, "z": 0.0}
  ],
  "height": 30.0,
  "description": "Rectangular office building"
}
```

**响应（201 Created）：**
```json
{
  "id": "p3j4k5l6",
  "name": "Office Complex",
  "type": "polygon",
  "position": {"x": 40.0, "y": 40.0, "z": 0.0},
  "description": "Rectangular office building",
  "radius": null,
  "width": null,
  "length": null,
  "vertices": [
    {"x": 40.0, "y": 40.0, "z": 0.0},
    {"x": 60.0, "y": 40.0, "z": 0.0},
    {"x": 60.0, "y": 60.0, "z": 0.0},
    {"x": 40.0, "y": 60.0, "z": 0.0}
  ],
  "height": 30.0,
  "area": 400.0,
  "created_at": 1704067200.0,
  "last_updated": 1704067200.0
}
```

### 关键响应对象

#### DroneResponse（GET /drones/{id}）
```json
{
  "id": "d4f3a9b2",
  "name": "Scout Alpha",
  "model": "Model-D4",
  "status": "hovering",
  "position": {"x": 50.0, "y": 30.0, "z": 15.0},
  "heading": 90.0,
  "speed": 0.0,
  "battery_level": 85.5,
  "battery_volume": 3420.0,
  "battery_capacity": 4000.0,
  "max_speed": 20.0,
  "max_altitude": 120.0,
  "perceived_radius": 100.0,
  "task_radius": 10.0,
  "home_position": {"x": 0.0, "y": 0.0, "z": 0.0},
  "created_at": 1704067200.0,
  "last_updated": 1704067350.5
}
```

#### BatteryUpdateRequest
```json
{
  "battery_level": "number (0-100)"
}
```

#### ChargeRequest
```json
{
  "charge_amount": "number (0.1-100)"
}
```

#### MoveAlongPathRequest
```json
{
  "waypoints": [
    {
      "x": "number",
      "y": "number",
      "z": "number (optional; defaults to current drone altitude)"
    }
  ],
  "allow_partial_move": "boolean (optional, default false; stop at the last reachable waypoint before an obstacle or insufficient battery)"
}
```

#### MoveTowardsRequest
```json
POST /drones/{id}/command
{
  "command": "move_towards",
  "parameters": {
    "distance": 50.0,
    // Choose ONE direction method:

    // Method 1: Compass heading (0=North, 90=East, 180=South, 270=West)
    "heading": 90.0,
    "dz": 5.0  // optional vertical component

    // Method 2: Direction vector
    // "dx": 1.0, "dy": 1.0, "dz": 0.5

    // Method 3: Spherical coordinates
    // "azimuth": 45.0, "elevation": 15.0
  }
}
```

#### CommandRequest
```json
{
  "command": "string (connect, disconnect, take_off, land, move_to, move_towards, move_along_path, change_altitude, hover, rotate, return_home, set_home, calibrate, take_photo, send_message, broadcast, charge)",
  "parameters": {}
}
```

#### CommandResponse
```json
{
  "command_id": "string",
  "drone_id": "string",
  "command": "string",
  "status": "string (success, partial_success, error)",
  "message": "string"
}
```

#### MoveAlongPathCommandResponse
```json
{
  "command_id": "string",
  "drone_id": "string",
  "command": "move_along_path",
  "status": "string (success, partial_success, error)",
  "message": "string",
  "successful_points_count": "integer (optional; move_along_path only)",
  "successful_points": "array of (x, y, z) triples (optional; move_along_path only)",
  "unsuccessful_points_count": "integer (optional; move_along_path only)",
  "unsuccessful_points": "array of (x, y, z) triples (optional; move_along_path only)"
}
```

命令状态值是语义化的命令结果。`success` 表示请求的命令已完全完成，`partial_success` 表示状态变更命令取得了部分进展但并未完成全部请求，`error` 表示命令未成功执行。
只有 `MoveAlongPathCommandResponse` 会提供路径点反馈字段。成功和部分成功的路径响应会使用这些字段，以标准化的 `(x, y, z)` 三元组形式列出已达到或未达到的请求路径点。错误响应不会填充路径点反馈值。

### 目标模型

#### TargetRequest
```json
{
  "name": "string",
  "type": "string (fixed, moving, waypoint, circle, polygon)",
  "position": {"x": "float", "y": "float", "z": "float"},
  "description": "string (optional)",
  "velocity": {"x": "float", "y": "float", "z": "float"} (optional, PRIORITY 1: if non-zero, uses velocity mode),
  "radius": "float (optional, default: 1.0)",
  "moving_path": [{"x": "float", "y": "float", "z": "float"}, ...] (optional, PRIORITY 2: used only if velocity is zero/null; consecutive duplicate waypoints are rejected and path segments are obstacle-validated),
  "moving_duration": "float (optional, default: 10.0, time in seconds. Velocity mode: time before reversing. Path mode: time to complete path (speed auto-calculated). If 0: stationary)",
  "charge_amount": "float (optional, for waypoint targets)",
  "vertices": [{"x": "float", "y": "float"}, ...] (required for polygon targets; absolute world coordinates)
}

// Movement Priority for moving targets:
// 1. VELOCITY (Priority 1): velocity non-zero + moving_duration > 0 → velocity-based ping-pong
// 2. PATH (Priority 2): velocity zero/null + moving_path exists + moving_duration > 0 → path-based with auto speed
// 3. STATIONARY: moving_duration == 0 → no movement
// Canonical moving-target response fields:
// - movement_mode: "velocity" | "path" | "stationary"
// - last_motion_update: float | null
// - tracking_status: "tracked" | "stale" | "never_tracked"
// - last_tracked_at: float | null
```

#### 更新目标（PUT /targets/{id}）

**请求体（所有字段均为可选）：**
```json
{
  "name": "Checkpoint Alpha Updated",
  "position": {"x": 105.0, "y": 55.0, "z": 0.0},
  "description": "Updated primary checkpoint",
  "radius": 8.0
}
```

**响应（200 OK）：**
```json
{
  "id": "t1a2b3c4",
  "name": "Checkpoint Alpha Updated",
  "type": "fixed",
  "position": {"x": 105.0, "y": 55.0, "z": 0.0},
  "description": "Updated primary checkpoint",
  "radius": 8.0,
  "velocity": null,
  "moving_path": null,
  "current_path_index": null,
  "charge_amount": null,
  "vertices": null,
  "created_at": 1704067200.0,
  "last_updated": 1704067500.0
}
```

**移动目标更新（基于路径）：**
```json
{
  "velocity": {"x": 3.0, "y": 2.0, "z": 0.5},
  "moving_path": [
    {"x": 50.0, "y": 50.0, "z": 10.0},
    {"x": 100.0, "y": 80.0, "z": 15.0},
    {"x": 150.0, "y": 50.0, "z": 10.0},
    {"x": 100.0, "y": 20.0, "z": 10.0}
  ]
}
```

**移动目标更新（基于速度的乒乓模式）：**
```json
{
  "velocity": {"x": 4.0, "y": 0.0, "z": 0.0},
  "moving_duration": 15.0,
  "moving_path": []
}
```

**路径点更新：**
```json
{
  "charge_amount": 35.0,
  "radius": 12.0
}
```

#### TargetResponse（GET /targets/{id}）
```json
{
  "id": "t1a2b3c4",
  "name": "Checkpoint Alpha",
  "type": "fixed",
  "position": {"x": 100.0, "y": 50.0, "z": 0.0},
  "description": "Primary checkpoint for mission",
  "velocity": null,
  "moving_path": null,
  "current_path_index": null,
  "radius": 5.0,
  "charge_amount": null,
  "vertices": null,
  "created_at": 1704067200.0,
  "last_updated": 1704067200.0
}
```

#### WaypointCheckResponse
```json
{
  "waypoint_id": "string",
  "drone_in_range": "boolean",
  "charge_amount": "float",
  "drone_position": {"x": "float", "y": "float", "z": "float"}
}
```

#### NearestWaypointResponse
```json
{
  "id": "string",
  "name": "string",
  "type": "waypoint",
  "position": {"x": "float", "y": "float", "z": "float"},
  "description": "string",
  "velocity": "object or null",
  "moving_path": "array or null",
  "current_path_index": "integer or null",
  "radius": "float",
  "charge_amount": "float",
  "vertices": "array or null",
  "created_at": "float",
  "last_updated": "float"
}
```

### 环境模型

#### EnvironmentRequest
```json
{
  "name": "string",
  "weather": "string (clear, partly_cloudy, cloudy, rain, heavy_rain, snow, fog, windy, storm)",
  "temperature": "float",
  "humidity": "float",
  "pressure": "float (optional, default: 1013.25)",
  "wind_speed": "float (optional, default: 0.0)",
  "wind_direction": "string (north, northeast, east, southeast, south, southwest, west, northwest) (optional, default: north)",
  "visibility": "float (optional, default: 10000.0)"
}
```

#### EnvironmentResponse
```json
{
  "id": "string",
  "name": "string",
  "weather": "string",
  "temperature": "float",
  "humidity": "float",
  "pressure": "float",
  "wind_speed": "float",
  "wind_direction": "string",
  "visibility": "float",
  "created_at": "float (timestamp)",
  "last_updated": "float (timestamp)"
}
```

#### EnvironmentUpdateRequest
```json
{
  "name": "string (optional)",
  "weather": "string (optional)",
  "temperature": "float (optional)",
  "humidity": "float (optional)",
  "pressure": "float (optional)",
  "wind_speed": "float (optional)",
  "wind_direction": "string (optional)",
  "visibility": "float (optional)"
}
```

### 障碍物模型

#### ObstacleRequest
```json
{
  "name": "string",
  "type": "string (point, circle, ellipse, polygon)",
  "position": {"x": "float", "y": "float", "z": "float"},
  "description": "string (optional)",
  "radius": "float (required for point and circle; defaults to 1.0 for point)",
  "width": "float (required for ellipse - semi-major axis)",
  "length": "float (required for ellipse - semi-minor axis)",
  "vertices": [{"x": "float", "y": "float", "z": "float"}, ...] (required for polygon, 3+ vertices),
  "height": "float (optional, default: 10.0) - 0 means impassable at any altitude"
}
```

#### 更新障碍物 (PUT /obstacles/{id})

**请求体（所有字段可选）：**
```json
{
  "name": "Building A Updated",
  "position": {"x": 55.0, "y": 55.0, "z": 0.0},
  "radius": 18.0,
  "height": 35.0,
  "description": "Updated circular building"
}
```

**响应（200 OK）：**
```json
{
  "id": "o1a2b3c4",
  "name": "Building A Updated",
  "type": "circle",
  "position": {"x": 55.0, "y": 55.0, "z": 0.0},
  "description": "Updated circular building",
  "radius": 18.0,
  "width": null,
  "length": null,
  "vertices": [],
  "height": 35.0,
  "area": 1017.8760197630929,
  "created_at": 1704067200.0,
  "last_updated": 1704067500.0
}
```

#### ObstacleResponse (GET /obstacles/{id})
```json
{
  "id": "o1a2b3c4",
  "name": "Building A",
  "type": "circle",
  "position": {"x": 50.0, "y": 50.0, "z": 0.0},
  "description": "Circular building structure",
  "radius": 15.0,
  "width": null,
  "length": null,
  "vertices": [],
  "height": 30.0,
  "area": 706.8583470577034,
  "created_at": 1704067200.0,
  "last_updated": 1704067200.0
}
```

### 碰撞检测模型

#### PathCollisionCheckRequest
```json
{
  "start": {"x": "float", "y": "float", "z": "float"},
  "end": {"x": "float", "y": "float", "z": "float"},
  "safety_margin": "float (optional, default: 0.0)"
}
```

**参数：**
- `start`：路径起点（x、y、z 坐标）
- `end`：路径终点（x、y、z 坐标）
- `safety_margin`：飞行路径周围的额外安全距离（单位：米）
- `0.0` = 仅检查直接线路（无人机命令的默认值）
- `> 0.0` = 创建一条在路径两侧具有指定宽度的走廊
- 示例：`safety_margin=5.0` 创建一条10米宽的走廊（每侧5米）

**注意：**内部无人机移动命令（`move_to`、`move_along_path`）默认使用 `safety_margin=0.0`。碰撞检查API端点允许为规划目的设置自定义安全裕度。

#### CollisionResponse
```json
{
  "obstacle_id": "string",
  "obstacle_name": "string",
  "type": "string",
  "collision_type": "string",
  "distance": "float or null"
}
```

**注意：**此响应返回关于找到的**第一个**障碍物碰撞的信息。

#### PointInObstaclesRequest
```json
{
  "x": "float",
  "y": "float",
  "z": "float (optional)",
  "margin": "float (optional, default: 0.0)"
}
```

**参数：**
- `x`：点的X坐标
- `y`：点的Y坐标
- `z`：点的Z坐标（高度，可选）
- 如果未提供：仅执行二维检查（将所有障碍物视为不可飞行区域）
- 如果提供：检查时会考虑障碍物高度
- `margin`：障碍物周围的裕度，单位米（默认值：0.0）
- 将障碍物几何形状扩大此量
- 在高度检查时也会添加到障碍物高度上

**高度逻辑：**
- **未提供 z**：仅检查二维区域（所有障碍物视为不可飞行）
- **提供了 z 且障碍物高度 = 0**：在任何高度都不可飞行
- **提供了 z 且障碍物高度 > 0**：
- 如果 `z <= 障碍物高度 + 裕度`，则该点位于内部
- 如果 `z > 障碍物高度 + 裕度`，则该点位于外部

#### PointInObstaclesResponse
```json
{
  "result": "boolean",
  "inside_obstacle_ids": ["string", ...],
  "inside_obstacles": [
    {
      "id": "string",
      "name": "string",
      "type": "string",
      "height": "float",
      "distance_to_boundary": "float"
    }
  ],
  "point": {"x": "float", "y": "float", "z": "float (optional)"},
  "margin": "float",
  "message": "string"
}
```

**响应字段：**
- `result`：如果点在任何障碍物的内部或边界上，则为 `true`
- `inside_obstacle_ids`：包含该点的所有障碍物ID列表
- `inside_obstacles`：每个障碍物的详细信息
- `distance_to_boundary`：如果在内部则为负值，如果在边界上则为 0
- `point`：被检查的点
- `margin`：检查时使用的裕度
- `message`：人类可读的结果描述

**注意：**与 `CollisionResponse` 不同，此响应返回包含该点的**所有**障碍物。

### 会话模型

#### SessionRequest
```json
{
  "name": "string",
  "description": "string (optional)",
  "with_examples": "boolean (optional, default: true)",
  "task_type": "string (optional, default: others) - 'area_search', 'area_assignment_and_patrol', 'target_assignment', 'target_tracking', or 'others'",
  "task_description": "string (optional) - Detailed description of the task/mission",
  "is_distance_3d": "boolean (optional, default: false) - Whether to use 3D distance for calculations",
  "canvas_width": "number (optional, default: 1024.0) - Width of simulation canvas in meters",
  "canvas_height": "number (optional, default: 768.0) - Height of simulation canvas in meters",
  "target_reach_statistics": "object (optional) - Summary statistics for target reach events",
  "area_coverage_summary": "object (optional) - Area coverage progress summary",
  "recent_commands": "array (optional) - Recent command executions"
}
```

#### 创建会话 (POST /sessions)

**请求体：**
```json
{
  "name": "Mission Alpha",
  "description": "Search and rescue mission in sector 7",
  "with_examples": false,
  "task_type": "area_search",
  "task_description": "Search designated area for survivors"
}
```

**响应（201 已创建）：**
```json
{
  "id": "s1a2b3c4d5e6f",
  "name": "Mission Alpha",
  "description": "Search and rescue mission in sector 7",
  "status": "active",
  "creator": "system",
  "task_type": "area_search",
  "task_description": "Search designated area for survivors",
  "is_distance_3d": false,
  "canvas_width": 1024.0,
  "canvas_height": 768.0,
  "created_at": 1704067200.0,
  "last_updated": 1704067200.0,
  "statistics": {
    "drone_count": 0,
    "target_count": 0,
    "obstacle_count": 0,
    "environment_id": null,
    "total_commands_executed": 0,
    "total_flight_time": 0.0,
    "total_distance_traveled": 0.0,
    "total_target_reaches": 0,
    "drones_with_target_reaches": 0,
    "unique_targets_reached": 0,
    "session_time": 0.0,
    "command_history_size": 0,
    "target_reach_log_size": 0,
    "task_progress": {
      "task_type": "area_search",
      "progress_percentage": 0,
      "is_completed": false,
      "status_message": "Task to be Done",
      "details": {
        "total_targets": 0,
        "average_coverage": 0.0
      },
      "target_reach_summary": {
        "total_reaches": 0,
        "drones_with_reaches": 0,
        "unique_targets_reached": 0
      },
      "area_coverage_summary": {
        "total_targets_tracked": 0,
        "average_coverage": 0.0,
        "fully_covered_targets": 0
      }
    }
  },
  "target_reaches": {},
  "moving_target_tracking": {},
  "target_reach_statistics": {
    "total_reaches": 0,
    "unique_drones": 0,
    "unique_targets": 0,
    "reaches_by_drone": {},
    "reaches_by_target": {}
  },
  "area_coverage_summary": {
    "total_targets_tracked": 0,
    "average_coverage": 0.0,
    "fully_covered_targets": 0,
    "coverage_by_target": {}
  },
  "recent_commands": []
}
```

#### 更新会话 (PUT /sessions/{id})

**请求体（所有字段可选）：**
```json
{
  "name": "Mission Alpha Updated",
  "description": "Updated search and rescue mission",
  "status": "inactive",
  "is_distance_3d": true,
  "canvas_width": 1200.0,
  "canvas_height": 800.0
}
```

**响应（200 OK）：**
```json
{
  "id": "s1a2b3c4d5e6f",
  "name": "Mission Alpha Updated",
  "description": "Updated search and rescue mission",
  "status": "inactive",
  "creator": "system",
  "task_type": "area_search",
  "task_description": "Search designated area for survivors",
  "is_distance_3d": true,
  "canvas_width": 1200.0,
  "canvas_height": 800.0,
  "created_at": 1704067200.0,
  "last_updated": 1704067500.0,
  "statistics": {
    "drone_count": 2,
    "target_count": 3,
    "obstacle_count": 1,
    "environment_id": "env123",
    "total_commands_executed": 15,
    "total_flight_time": 450.5,
    "total_distance_traveled": 1250.75,
    "total_target_reaches": 5,
    "drones_with_target_reaches": 2,
    "unique_targets_reached": 3,
    "session_time": 600.0,
    "command_history_size": 15,
    "target_reach_log_size": 5,
    "task_progress": {
      "task_type": "area_search",
      "progress_percentage": 45,
      "is_completed": false,
      "status_message": "Task to be Done",
      "details": {
        "total_targets": 3,
        "average_coverage": 45.2
      },
      "target_reach_summary": {
        "total_reaches": 5,
        "drones_with_reaches": 2,
        "unique_targets_reached": 3
      },
      "area_coverage_summary": {
        "total_targets_tracked": 3,
        "average_coverage": 45.2,
        "fully_covered_targets": 0
      }
    }
  },
  "target_reaches": {
    "by_drone": {
      "drone1": {
        "target1": {
          "count": 2,
          "first_reached_at": 1704067300.0,
          "last_reached_at": 1704067400.0,
          "recent_reached_at": [1704067300.0, 1704067400.0]
        }
      }
    },
    "by_target": {
      "target1": {
        "total_reaches": 2,
        "unique_drones": 1,
        "reached_by": ["drone1"],
        "first_reached_at": 1704067300.0,
        "last_reached_at": 1704067400.0,
        "recent_reached_at": [1704067300.0, 1704067400.0]
      }
    }
  },
  "moving_target_tracking": {
    "target1": {
      "tracking_status": "tracked",
      "first_tracked_at": 1704067300.0,
      "last_tracked_at": 1704067400.0,
      "last_tracked_by": "drone1",
      "tracked_by": ["drone1"],
      "total_track_events": 2,
      "active_period_start": 1704067300.0,
      "recent_periods": [
        {
          "start_at": 1704067300.0,
          "end_at": 1704067410.0,
          "last_update_at": 1704067400.0,
          "event_count": 2,
          "last_tracked_by": "drone1",
          "tracked_by": ["drone1"]
        }
      ],
      "by_drone": {
        "drone1": {
          "first_tracked_at": 1704067300.0,
          "last_tracked_at": 1704067400.0,
          "total_track_events": 2,
          "recent_periods": [
            {
              "start_at": 1704067300.0,
              "end_at": 1704067410.0,
              "last_update_at": 1704067400.0,
              "event_count": 2
            }
          ]
        }
      }
    }
  },
  "area_coverage_summary": {
    "total_targets_tracked": 3,
    "average_coverage": 45.2,
    "fully_covered_targets": 0,
    "coverage_by_target": {
      "target1": {
        "area_type": "circle",
        "total_area": 1963.4954084936207,
        "covered_area": 887.5,
        "coverage_percentage": 45.2,
        "num_covered_points": 150,
        "covered_points": [[100.0, 100.0], [101.0, 100.0]]
      }
    }
  },
  "recent_commands": [
    {
      "command_id": "cmd123",
      "drone_id": "drone1",
      "command": "move_to",
      "parameters": {"x": 100.0, "y": 50.0, "z": 15.0},
      "status": "success",
      "message": "Moved to position",
      "timestamp": 1704067400.0
    }
  ]
}
```

#### SessionResponse (GET /sessions/{id})
```json
{
  "id": "s1a2b3c4d5e6f",
  "name": "Mission Alpha",
  "description": "Search and rescue mission in sector 7",
  "status": "active",
  "creator": "system",
  "task_type": "area_search",
  "task_description": "Search designated area for survivors",
  "is_distance_3d": false,
  "canvas_width": 1024.0,
  "canvas_height": 768.0,
  "created_at": 1704067200.0,
  "last_updated": 1704067500.0,
  "statistics": {
    "drone_count": 2,
    "target_count": 3,
    "obstacle_count": 1,
    "environment_id": "env123",
    "total_commands_executed": 15,
    "total_flight_time": 450.5,
    "total_distance_traveled": 1250.75,
    "total_target_reaches": 5,
    "drones_with_target_reaches": 2,
    "unique_targets_reached": 3,
    "session_time": 600.0,
    "command_history_size": 15,
    "target_reach_log_size": 5,
    "task_progress": {
      "task_type": "area_search",
      "progress_percentage": 45,
      "is_completed": false,
      "status_message": "Task to be Done",
      "details": {
        "total_targets": 3,
        "average_coverage": 45.2
      },
      "target_reach_summary": {
        "total_reaches": 5,
        "drones_with_reaches": 2,
        "unique_targets_reached": 3
      },
      "area_coverage_summary": {
        "total_targets_tracked": 3,
        "average_coverage": 45.2,
        "fully_covered_targets": 0
      }
    }
  },
  "target_reach_statistics": {
    "total_reaches": 5,
    "unique_drones": 2,
    "unique_targets": 3,
    "reaches_by_drone": {},
    "reaches_by_target": {}
  },
  "area_coverage_summary": {
    "total_targets_tracked": 3,
    "average_coverage": 45.2,
    "fully_covered_targets": 0,
    "coverage_by_target": {}
  },
  "recent_commands": [
    {
      "command": "move_to",
      "timestamp": 1704067400.0,
      "parameters": {
        "x": 10,
        "y": 5,
        "z": 0
      },
      "result": "success"
    }
  ]
}
```

#### SessionDataResponse

平面结构的完整会话数据。在同一层级通过实体数组扩展了SessionResponse。

```json
{
  "id": "string",
  "name": "string",
  "description": "string",
  "status": "string",
  "creator": "string",
  "task_type": "string",
  "task_description": "string",
  "is_distance_3d": "boolean",
  "canvas_width": "number",
  "canvas_height": "number",
  "created_at": "float",
  "last_updated": "float",
  "statistics": {
    "drone_count": "integer",
    "target_count": "integer",
    "obstacle_count": "integer",
    "environment_id": "string or null",
    "total_commands_executed": "integer",
    "total_flight_time": "float",
    "total_distance_traveled": "float",
    "total_target_reaches": "integer",
    "drones_with_target_reaches": "integer",
    "unique_targets_reached": "integer",
    "session_time": "float",
    "command_history_size": "integer",
    "target_reach_log_size": "integer",
    "task_progress": {
      "task_type": "string",
      "progress_percentage": "integer (0-100)",
      "is_completed": "boolean",
      "status_message": "string",
      "details": "object",
      "target_reach_summary": "object",
      "area_coverage_summary": "object"
    }
  },
  "target_reaches": "object",
  "target_reach_statistics": "object",
  "area_coverage_summary": "object",
  "recent_commands": "array",
  "drones": "Array of DroneResponse",
  "targets": "Array of TargetResponse",
  "obstacles": "Array of ObstacleResponse",
  "environment": "EnvironmentResponse or null",
  "history": {
    "command_history": "array",
    "status_history": "object",
    "target_reaches": "object",
    "moving_target_tracking": "object",
    "area_coverage": "object",
    "path_history": "object"
  }
}
```

### 会话截图端点

#### GET /sessions/current/screenshot
- 查询参数：
- `format`：`string`（可选）— 可选值：`png`、`jpg`、`jpeg`、`pdf`、`svg`、`eps`（默认：`png`）
- `width`：`integer`（可选）— 图像宽度，单位像素（默认：`1024`）
- `height`：`integer`（可选）— 图像高度，单位像素（默认：`768`）
- `show_status`：`boolean`（可选）— 包含UI等效的路径轨迹、区域覆盖、已到达/跟踪的目标状态和状态栏详情（默认：`false`）
- 响应：二进制内容，媒体类型根据 `format` 为 `image/png`、`image/jpeg`、`application/pdf`、`image/svg+xml` 或 `application/postscript`。

#### GET /sessions/{session_id}/screenshot
- 路径参数：
- `session_id`：`string` — 目标会话ID
- 查询参数：
- `format`：`string`（可选）— 可选值：`png`、`jpg`、`jpeg`、`pdf`、`svg`、`eps`（默认：`png`）
- `width`：`integer`（可选）— 图像宽度，单位像素（默认：`1024`）
- `height`：`integer`（可选）— 图像高度，单位像素（默认：`768`）
- `show_status`：`boolean`（可选）— 包含UI等效的路径轨迹、区域覆盖、已到达/跟踪的目标状态和状态栏详情（默认：`false`）
- 响应：二进制内容，媒体类型根据 `format` 为 `image/png`、`image/jpeg`、`application/pdf`、`image/svg+xml` 或 `application/postscript`。

#### POST /sessions/current/reset

通过清除所有历史跟踪数据，同时保留实体，将当前活动会话重置为其初始状态。

**身份验证：**需要 USER 角色或更高权限

**清除内容：**
- 命令历史（发送给无人机的所有命令）
- 状态历史（无人机状态变更记录）
- 路径历史（无人机移动轨迹/航迹）
- 目标抵达日志
- 区域覆盖数据
- 统计数据（已执行命令总数、飞行时间、飞行距离）
- 会话计时器（重置为 0）

**保留内容：**
- 会话ID、名称和描述
- 所有无人机及其当前位置和状态
- 所有目标
- 所有障碍物
- 环境配置
- 任务定义

**请求：** 无需请求体

**响应 (200 OK)：**
```json
{
  "id": "session-123abc",
  "name": "Current Session",
  "description": "Active session",
  "status": "active",
  "creator": "system",
  "task_type": "area_search",
  "task_description": "Search designated areas",
  "created_at": 1734000000.0,
  "last_updated": 1734001234.5,
  "statistics": {
    "drone_count": 10,
    "target_count": 5,
    "obstacle_count": 2,
    "total_commands_executed": 0,
    "total_flight_time": 0.0,
    "total_distance_traveled": 0.0,
    "session_time": 0.0,
    "command_history_size": 0,
    "target_reach_log_size": 0
  }
}
```

**示例：**
```bash
curl -X POST http://localhost:8000/sessions/current/reset
```

### 电池管理模型

#### BatteryUpdateRequest
```json
{
  "battery_level": "float (0.0-100.0)"
}
```

#### PathRequest
```json
{
  "path": [
    {"x": "float", "y": "float", "z": "float"},
    {"x": "float", "y": "float", "z": "float"}
  ]
}
```

## 使用示例

### 注册无人机

```bash
curl -X POST http://localhost:8000/drones \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Scout-1",
    "model": "Model-D4",
    "max_speed": 20.0,
    "max_altitude": 120.0,
    "battery_capacity": 100.0
  }'
```

### 向无人机发送指令

```bash
curl -X POST http://localhost:8000/drones/550e8400-e29b-41d4-a716-446655440000/command \
  -H "Content-Type: application/json" \
  -d '{
    "command": "take_off",
    "parameters": {"altitude": 10.0}
  }'
```

### 向指定方向移动无人机

```bash
# Move 50 meters in current heading direction (no heading parameter = use current)
curl -X POST "http://localhost:8000/drones/drone-123/command/move_towards?distance=50.0"

# Move 50 meters towards East (90 degrees)
curl -X POST "http://localhost:8000/drones/drone-123/command/move_towards?distance=50.0&heading=90.0"

# Move 30 meters Northeast with 5m altitude gain
curl -X POST "http://localhost:8000/drones/drone-123/command/move_towards?distance=30.0&heading=45.0&dz=5.0"

# Move using direction vector
curl -X POST "http://localhost:8000/drones/drone-123/command/move_towards?distance=25.0&dx=1.0&dy=1.0&dz=0.5"

# Move using azimuth and elevation angles
curl -X POST "http://localhost:8000/drones/drone-123/command/move_towards?distance=40.0&azimuth=135.0&elevation=15.0"

# Using generic command endpoint
curl -X POST http://localhost:8000/drones/drone-123/command \
  -H "Content-Type: application/json" \
  -d '{
    "command": "move_towards",
    "parameters": {
      "distance": 50.0,
      "heading": 90.0
    }
  }'
```

### 更改无人机航向（旋转）

```bash
# Rotate to face North
curl -X POST "http://localhost:8000/drones/drone-123/command/rotate?heading=0.0"

# Rotate to face East
curl -X POST "http://localhost:8000/drones/drone-123/command/rotate?heading=90.0"

# Rotate to face South
curl -X POST "http://localhost:8000/drones/drone-123/command/rotate?heading=180.0"

# Using generic command endpoint
curl -X POST http://localhost:8000/drones/drone-123/command \
  -H "Content-Type: application/json" \
  -d '{
    "command": "rotate",
    "parameters": {
      "heading": 270.0
    }
  }'
```

### 沿路径移动无人机

当 `allow_partial_move=true` 时，`status: "partial_success"` 表示无人机至少到达了一个航点，但由于障碍物或电量不足阻挡了剩余路径，它在到达最终请求的航点之前停止。`status: "success"` 表示所有请求的航点均已到达，而 `status: "error"` 表示该失败的路径命令未执行任何允许的移动。成功和部分成功的响应包括 `successful_points_count`、`successful_points`、`unsuccessful_points_count` 和 `unsuccessful_points`；点列表包含归一化的 `(x, y, z)` 三元组。

```bash
curl -X POST http://localhost:8000/drones/550e8400-e29b-41d4-a716-446655440000/command/move_along_path \
  -H "Content-Type: application/json" \
  -d '{
    "waypoints": [
      {"x": 10.0, "y": 20.0, "z": 15.0},
      {"x": 30.0, "y": 40.0},
      {"x": 50.0, "y": 60.0, "z": 15.0}
    ],
    "allow_partial_move": true
  }'
```

### 更新无人机电池

```bash
curl -X POST http://localhost:8000/drones/550e8400-e29b-41d4-a716-446655440000/battery \
  -H "Content-Type: application/json" \
  -d '{"battery_level": 75.0}'
```

### 创建障碍物

```bash
curl -X POST http://localhost:8000/obstacles \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Tall Building",
    "type": "building",
    "position": {"x": 100.0, "y": 200.0, "z": 0.0},
    "description": "Office building",
    "vertices": [
      {"x": 90.0, "y": 190.0},
      {"x": 110.0, "y": 190.0},
      {"x": 110.0, "y": 210.0},
      {"x": 90.0, "y": 210.0}
    ],
    "height": 50.0
  }'
```

### 检查路径碰撞

```bash
# Requires SYSTEM role
curl -X POST http://localhost:8000/obstacles/path_collision \
  -H "Content-Type: application/json" \
  -H "X-API-Key: <SYSTEM_API_KEY>" \
  -d '{
    "start": {"x": 0.0, "y": 0.0, "z": 10.0},
    "end": {"x": 200.0, "y": 300.0, "z": 10.0},
    "safety_margin": 2.0
  }'
```

### 检查点碰撞

```bash
# 2D check (no altitude) - requires SYSTEM role
curl -X POST http://localhost:8000/obstacles/point_collision \
  -H "Content-Type: application/json" \
  -H "X-API-Key: <SYSTEM_API_KEY>" \
  -d '{
    "x": 100.0,
    "y": 200.0,
    "margin": 0.0
  }'

# 3D check with altitude and margin - requires SYSTEM role
curl -X POST http://localhost:8000/obstacles/point_collision \
  -H "Content-Type: application/json" \
  -H "X-API-Key: <SYSTEM_API_KEY>" \
  -d '{
    "x": 100.0,
    "y": 200.0,
    "z": 5.0,
    "margin": 2.0
  }'
```

### 创建会话

```bash
curl -X POST http://localhost:8000/sessions \
  -H "Content-Type: application/json" \
  -d '{
    "name": "My Custom Session",
    "description": "A custom session for testing",
    "with_examples": true
  }'
```

### 会话创建与管理

```bash
# Create new session with auto-generated ID
curl -X POST http://localhost:8000/sessions \
  -H "Content-Type: application/json" \
  -H "X-API-Key: <SYSTEM_API_KEY>" \
  -d '{"name": "Mission Alpha", "description": "Search mission", "creator": "planner-ops"}'

# Create session with entities
curl -X POST http://localhost:8000/sessions \
  -H "Content-Type: application/json" \
  -H "X-API-Key: <SYSTEM_API_KEY>" \
  -d '{
    "name": "Mission with Fleet",
    "creator": "planner-ops",
    "drones": [{"name": "Scout-1", "model": "Model-D", "position": {"x": 0, "y": 0, "z": 0}}],
    "targets": [{"name": "Target-1", "type": "fixed", "position": {"x": 100, "y": 100, "z": 0}}]
  }'

# Restore session with specific ID from backup (automatically overwrites if exists)
curl -X POST "http://localhost:8000/sessions/mission-backup-2024?data=true" \
  -H "Content-Type: application/json" \
  -H "X-API-Key: <SYSTEM_API_KEY>" \
  -d @backup.json

# Update session metadata
curl -X PUT http://localhost:8000/sessions/session-abc123 \
  -H "Content-Type: application/json" \
  -H "X-API-Key: <SYSTEM_API_KEY>" \
  -d '{"name": "Updated Name", "status": "completed"}'

# Update session and get complete data
curl -X PUT "http://localhost:8000/sessions/session-abc123?data=true" \
  -H "Content-Type: application/json" \
  -H "X-API-Key: <SYSTEM_API_KEY>" \
  -d '{"status": "completed"}'
```

### 通过数据参数获取会话

```bash
# Get current session metadata only (default)
curl -X GET http://localhost:8000/sessions/current

# Get current session with complete data (all drones, targets, obstacles, environment)
curl -X GET "http://localhost:8000/sessions/current?data=true"

# Get current session with complete data (convenience endpoint)
curl -X GET http://localhost:8000/sessions/current/data

# Get specific session metadata only
curl -X GET http://localhost:8000/sessions/session-abc123

# Get specific session with complete data
curl -X GET "http://localhost:8000/sessions/session-abc123?data=true"

# Get specific session with complete data (convenience endpoint)
curl -X GET http://localhost:8000/sessions/session-abc123/data
```

### 完整的保存/恢复工作流程

```bash
# 1. Export current session to file (data is already in flat format)
curl -X GET "http://localhost:8000/sessions/current?data=true" > session_backup.json

# The backup file has flat structure with all fields at root level:
# {
#   "id": "session-123",
#   "name": "Mission Alpha",
#   "status": "active",
#   "statistics": {...},
#   "drones": [...],
#   "targets": [...],
#   "obstacles": [...],
#   "environment": {...},
#   "history": {...}
# }

# 2. Later, restore with specific ID and verify in one call
curl -X POST "http://localhost:8000/sessions/mission-restored-$(date +%s)?data=true" \
  -H "Content-Type: application/json" \
  -H "X-API-Key: <SYSTEM_API_KEY>" \
  -d @session_backup.json

# Response includes all restored drones, targets, obstacles, and environment in flat format!

# 3. Force overwrite if session already exists (useful for re-restoring backups)
curl -X POST "http://localhost:8000/sessions/mission-backup-001?overwrite=true&data=true" \
  -H "Content-Type: application/json" \
  -H "X-API-Key: <SYSTEM_API_KEY>" \
  -d @session_backup.json

# Deletes existing session and replaces it with backup data
```

---

## 重要说明

### 无人机状态值
- `idle` - 地面待命，未激活
- `ready` - 地面就绪，等待起飞
- `taking_off` - 起飞中
- `flying` - 空中稳定飞行
- `moving` - 空中移动至目的地
- `hovering` - 空中悬停
- `landing` - 降落中
- `emergency` - 紧急状态（电量不足）
- `offline` - 未连接

### 目标类型
- `fixed` - 静态目标（也可用于兴趣点）
- `moving` - 具有速度/路径的移动目标
- `waypoint` - 充电站
- `circle` - 几何圆形目标（使用 `position` 处的 `radius`）
- `polygon` - 几何多边形目标（使用 `vertices` 绝对坐标）

#### 用户界面说明
- `point`：金色小圆形障碍物
- `circle`：棕色填充圆，白色轮廓
- `ellipse`：中兰花紫色填充椭圆，白色轮廓
- `polygon`：暗灰色填充多边形；选中时带有扩展边界轮廓

### 障碍物类型
- `point` - 点状障碍物（需要 `position`；`radius` 默认为 1.0 米）
- `circle` - 圆形障碍物（需要 `position` 和 `radius`）
- `ellipse` - 椭圆形障碍物（需要 `position`、`width` 和 `length`）
- `polygon` - 多边形障碍物（需要包含 3 个以上点的 `vertices`）

### 基于高度的可通过性
- `height = 0`：任何高度均不可通行的区域（无人机无法飞越）
- `height > 0`：无人机若飞行高度超过障碍物高度则可飞越

### 天气条件
`clear`, `partly_cloudy`, `cloudy`, `rain`, `heavy_rain`, `snow`, `fog`, `windy`, `storm`

### 风向
`north`, `northeast`, `east`, `southeast`, `south`, `southwest`, `west`, `northwest`

---

## 其他资源

- **完整文档**：[API_DOCUMENTATION_ZH.md](API_DOCUMENTATION_ZH.md)
- **主 README**：[README.md](README.md)
- **交互式 API 文档**：http://localhost:8000/docs （服务器运行时）
- **客户端示例**：`/client` 目录
- **测试**：`test_*.py` 文件

---

## 检查端点（仅限管理员）

**需要身份验证：**所有 `/check/` 端点都需要通过 `X-API-Key` 标头进行 ADMIN 角色身份验证。响应始终包含 `result`（布尔值）和 `value`（主要测量值）。

| 方法 | 端点 | 描述 |
|--------|----------|-------------|
| GET | `/check/drone_position` | 与预期位置的距离（若提供 `z` 则为 3D）|
| GET | `/check/drone_altitude` | 高度与预期值的接近度 |
| GET | `/check/drone_status` | 状态相等性 |
| GET | `/check/drone_on_ground` | 地面检查（高度 + 地面状态）|
| GET | `/check/all_drones_on_ground` | 全体无人机地面状态（数量/全部）|
| GET | `/check/drone_hovering` | 悬停检查（高度 + 悬停状态）|
| GET | `/check/all_drones_hovering` | 悬停无人机数量/全部悬停 |
| GET | `/check/drone_over_height` | 高度高于最低高度 |
| GET | `/check/target_within_drone_distance` | 目标在无人机距离范围内 |
| GET | `/check/obstacle_within_drone_distance` | 障碍物在无人机距离范围内 |
| GET | `/check/two_drones_distance` | 两架无人机在指定距离内 |
| GET | `/check/drone_group_distance` | 无人机群成对距离检查 |
| GET | `/check/drone_battery_level` | 电池电量是否低于最低值 |
| GET | `/check/drone_heading` | 航向在容差范围内 |
| GET | `/check/drone_in_target` | 无人机在目标半径内 |
| GET | `/check/drone_at_home` | 无人机靠近初始位置 |
| GET | `/check/target_within_drone_task_radius` | 目标在无人机任务半径内 |
| GET | `/check/target_within_drone_perceived_radius` | 目标在无人机感知半径内 |
| GET | `/check/obstacle_within_drone_perceived_radius` | 障碍物在无人机感知半径内 |
| GET | `/check/drone_has_taken_off` | 检查无人机是否已起飞（历史记录）|
| GET | `/check/drone_has_landed` | 检查无人机是否已降落（历史记录）|
| GET | `/check/drone_has_visited_position` | 检查无人机是否曾到访过某位置（历史记录）|
| GET | `/check/drone_has_moved_distance` | 检查无人机是否移动了最小距离（历史记录） |
| GET | `/check/drone_has_moved_directed_distance` | 检查无人机是否朝指定方向移动了距离（历史记录） |
| GET | `/check/drone_has_hovered` | 检查无人机是否悬停过（历史记录） |
| GET | `/check/drone_has_taken_photo` | 检查无人机是否拍摄过照片（历史记录） |
| GET | `/check/target_in_photo_taken_by_drone` | 检查目标是否在无人机拍摄的照片中 |
| GET | `/check/drone_has_charged` | 检查无人机是否充过电（历史记录） |
| GET | `/check/drone_has_sent_message` | 检查无人机是否发送过消息（历史记录） |
| GET | `/check/all_drones_have_taken_off` | 检查是否所有无人机都已起飞 |
| GET | `/check/all_drones_have_landed` | 检查是否所有无人机都已降落 |
| GET | `/check/target_is_reached` | 是否有无人机到达目标 |
| GET | `/check/target_is_reached_by_drone` | 指定无人机是否到达目标 |
| GET | `/check/target_reached_drone_number` | 到达的无人机数量与预期对比 |
| GET | `/check/moving_target_tracked` | 移动目标是否被追踪了至少一段时间 |
| GET | `/check/target_is_fully_searched` | 覆盖程度是否达到阈值（默认0.99） |
| GET | `/check/target_searched_area_percentage` | 覆盖面积与预期比率（0-1） |
| GET | `/check/task_progress` | 任务进度与预期比率（0-1） |
| GET | `/check/task_done` | 通过会话进度检查任务是否完成 |

### 检查无人机位置

**GET** `/check/drone_position` — 与预期位置的距离（若提供 `z` 则为三维距离）  
查询参数：`drone_id`、`x`、`y`、`z?`、`tolerance?`  
响应：`result`（是否在容差范围内）、`value`（距离），以及 ID/位置/容差。

**GET** `/check/drone_altitude` — 高度接近程度  
查询参数：`drone_id`、`expected_altitude`、`tolerance?`  
响应：`result`（是否在容差范围内）、`value`（当前高度）、`difference`、`tolerance`。

**GET** `/check/drone_status` — 状态是否相等  
查询参数：`drone_id`、`expected_status`  
响应：`result`（是否相等）、`value`（当前状态）。

**GET** `/check/drone_on_ground` — 高度接近地面且状态类似在地面  
查询参数：`drone_id`、`tolerance?`  
响应：`result`、`value`（当前高度）、`status`。

**GET** `/check/all_drones_on_ground` — 机队中已接地的数量  
查询参数：`tolerance?`  
响应：`result`（是否全部接地）、`value`（接地数量）、已接地/未接地的 ID 列表。

**GET** `/check/drone_hovering` — 悬停状态  
查询参数：`drone_id`、`tolerance?`  
响应：`result`、`value`（状态）、`altitude`。

**GET** `/check/all_drones_hovering` — 机队中正在悬停的数量  
查询参数：`tolerance?`  
响应：`result`（是否全部悬停）、`value`（悬停数量）、悬停/未悬停的 ID 列表。

**GET** `/check/drone_over_height` — 高度是否高于最低高度
查询参数：`drone_id`、`min_height`、`tolerance?`
响应：`result`、`value`（当前高度）、`min_height`、`tolerance`。

**GET** `/check/target_within_drone_distance` — 目标是否在无人机指定距离内
查询参数：`drone_id`、`target_id`、`max_distance`
响应：`result`、`value`（距离）、`max_distance`。

**GET** `/check/obstacle_within_drone_distance` — 障碍物是否在无人机指定距离内
查询参数：`drone_id`、`obstacle_id`、`max_distance`
响应：`result`、`value`（距离）、`max_distance`。

**GET** `/check/two_drones_distance` — 两架无人机是否在指定距离范围内
查询参数：`drone_1_id`、`drone_2_id`、`max_distance?`（可选）、`min_distance?`（默认 0）  
响应：`result`（布尔值）、`value`（距离）、`drone_1_id`、`drone_2_id`。

**GET** `/check/drone_group_distance` — 无人机组内各配对是否满足距离范围规则
查询参数：重复的 `drone_ids`（至少 2 个）、`max_distance?`（可选）、`min_distance?`（默认 0）、`mode?`（默认 `all_pairs`，或 `any_pair`）  
响应：`result`（布尔值）、`value`（通过的配对数）、`mode`、`total_pairs`、`passing_pairs`、`failing_pairs`、`pair_distances`。

**GET** `/check/drone_battery_level` — 电池电量是否满足最低要求
查询参数：`drone_id`、`min_level?`
响应：`result`、`value`（电量百分比）、`min_level`。

**GET** `/check/drone_heading` — 航向是否在容差范围内
查询参数：`drone_id`、`expected_heading`、`tolerance?`
响应：`result`、`value`（当前航向）、`heading_delta`、`tolerance`。

**GET** `/check/drone_in_target` — 无人机是否在目标半径内（基于目标中心）
查询参数：`drone_id`、`target_id`
响应：`result`、`value`（距离）、`target_radius`。

**GET** `/check/drone_at_home` — 无人机是否靠近其起始位置
查询参数：`drone_id`、`tolerance?`
响应：`result`、`value`（距离）、`tolerance`、`home_position`。

**GET** `/check/target_within_drone_task_radius` — 目标是否在无人机任务半径内
查询参数：`drone_id`、`target_id`
响应：`result`、`value`（距离）、`task_radius`。

**GET** `/check/target_within_drone_perceived_radius` — 目标是否在无人机感知半径内
查询参数：`drone_id`、`target_id`  
响应：`result`、`value`（距离）、`perceived_radius`。

**GET** `/check/obstacle_within_drone_perceived_radius` — 障碍物是否在无人机感知半径内
查询参数：`drone_id`、`obstacle_id`
响应：`result`、`value`（距离）、`perceived_radius`。

### 历史记录检查端点

**GET** `/check/drone_has_taken_off` — 检查历史记录中无人机是否已起飞
查询参数：`drone_id`、`min_altitude?`（默认 5.0）、`max_altitude?`、`tolerance?`（默认 0.0）、`since_timestamp?`
响应：`result`（存在匹配的起飞），`value`（匹配的起飞事件数量），`takeoff_count`，`last_takeoff_time`，`max_altitude_reached`，`min_altitude_threshold`，`max_altitude_threshold`，`tolerance`。

模式：
- 阈值模式：省略 `max_altitude`；匹配高度满足 `>= min_altitude - tolerance` 的起飞事件
- 区间模式：同时提供 `min_altitude` 和 `max_altitude`；匹配高度在 `[min_altitude - tolerance, max_altitude + tolerance]` 范围内的起飞事件
- 精确高度模式：设置 `min_altitude == max_altitude`；此时 `tolerance` 定义该高度附近的容许范围

示例：
```bash
# Backward-compatible minimum threshold check
curl -X GET "http://localhost:8000/check/drone_has_taken_off?drone_id=drone-1&min_altitude=5.0" \
  -H "X-API-Key: <ADMIN_API_KEY>"

# Check whether a takeoff was within an altitude range
curl -X GET "http://localhost:8000/check/drone_has_taken_off?drone_id=drone-1&min_altitude=9.0&max_altitude=11.0&tolerance=0.2" \
  -H "X-API-Key: <ADMIN_API_KEY>"

# Check whether a takeoff reached about 10 meters (10.0 +/- 0.5)
curl -X GET "http://localhost:8000/check/drone_has_taken_off?drone_id=drone-1&min_altitude=10.0&max_altitude=10.0&tolerance=0.5" \
  -H "X-API-Key: <ADMIN_API_KEY>"
```

**GET** `/check/drone_has_landed` — 检查历史记录中无人机是否已降落
查询：`drone_id`，`min_count?`（默认 1），`since_timestamp?`
响应：`result`（至少存在 `min_count` 次降落），`value`（降落事件数量），`last_landing_time`，`last_landing_position`。

**GET** `/check/drone_has_visited_position` — 检查无人机是否曾到访特定位置
查询：`drone_id`，`x`，`y`，`z?`，`tolerance?`（默认 2.0），`since_timestamp?`
响应：`result`（已到访），`value`（到访次数），`visits`（该位置处的航点事件列表）。

**GET** `/check/drone_has_moved_distance` — 检查无人机是否移动了至少指定距离
查询：`drone_id`，`min_distance`，`since_timestamp?`
响应：`result`（已移动足够距离），`value`（总移动距离，米），`waypoint_count`（航点数量）。

**GET** `/check/drone_has_moved_directed_distance` — 检查无人机是否沿特定方向移动了至少指定距离
查询：`drone_id`，`min_distance`，`heading`，`tolerance?`（默认 5.0），`since_timestamp?`
响应：`result`（已移动足够距离），`value`（总定向移动距离），`heading`，`tolerance`。

**GET** `/check/drone_has_hovered` — 检查历史记录中无人机是否曾悬停
查询：`drone_id`，`min_duration?`（默认 0），`since_timestamp?`
响应：`result`（已悬停），`value`（悬停事件数量），`hover_events`（带持续时间的事件列表）。

**GET** `/check/drone_has_taken_photo` — 检查无人机是否拍摄了照片
查询：`drone_id`，`min_count?`（默认 1），`since_timestamp?`
响应：`result`（已拍摄照片），`value`（照片数量），`photo_events`（拍照事件列表）。

**GET** `/check/target_in_photo_taken_by_drone` — 检查目标是否出现在无人机拍摄的照片中
查询：`drone_id`，`target_id`
响应：`result`（目标在照片中），`value`（布尔值），`matching_photos`（列表）。

**GET** `/check/drone_has_charged` — 检查历史记录中无人机是否曾充电
查询：`drone_id`，`min_charge_amount?`（默认 0），`since_timestamp?`
响应：`result`（已充电），`value`（充电事件数量），`charge_events`（充电事件列表）。
注意：若充电事件将电池充至 100%，即使实际充电量较小，也视为满足 `min_charge_amount` 条件。

**GET** `/check/drone_has_sent_message` — 检查无人机是否发送过消息（含广播）
查询：`drone_id`，`to_drone_id?`，`min_count?`（默认 1），`since_timestamp?`
响应：`result`（布尔值），`value`（整型），`drone_id`，`to_drone_id`，`min_count`，`recipient_drones`（列表），`last_message_time`。

**GET** `/check/drone_has_sent_message_content` — 检查无人机发送的消息文本是否包含指定内容
查询：`drone_id`，`content`，`to_drone_id?`，`min_count?`（默认 1），`since_timestamp?`
响应：`result`（布尔值），`value`（整型），`drone_id`，`content`，`to_drone_id`，`min_count`，`recipient_drones`（列表），`last_message_time`，`matched_messages`，`match_mode`。

### 历史聚合检查端点

**GET** `/check/all_drones_have_taken_off` — 检查是否所有无人机均已起飞
查询：`min_altitude?`（默认 5.0），`since_timestamp?`，`check_history?`（默认 true）
响应：`result`（所有均已起飞），`value`（已起飞无人机数量），`percentage`，`drones_taken_off`（列表），`drones_not_taken_off`（列表），`total_drones`。

**GET** `/check/all_drones_have_landed` — 检查是否所有无人机均已降落
查询：`min_count?`（默认 1），`since_timestamp?`，`check_history?`（默认 true）
响应：`result`（所有均已降落），`value`（已降落无人机数量），`percentage`，`drones_landed`（列表），`drones_not_landed`（列表），`total_drones`。

### 目标与任务检查端点

**GET** `/check/target_is_reached` — 检查是否有无人机到达目标  
查询：`target_id`，`since_timestamp?`  
响应：`result`，`value`（无人机数量），`reached_by` 列表。

**GET** `/check/target_is_reached_by_drone` — 检查特定无人机是否到达目标  
查询：`target_id`，`drone_id`，`since_timestamp?`  
响应：`result`，`value`（到访次数），`target_id`，`drone_id`。

**GET** `/check/target_reached_drone_number` — 检查到达的无人机数量是否与预期相符  
查询：`target_id`，`expected_count?`，`since_timestamp?`  
响应：`result`，`value`（数量），`reached_by`。

**GET** `/check/moving_target_tracked` — 检查移动目标至少被跟踪了指定时长  
查询：`target_id`，`drone_id?`，`min_duration?`，`since_timestamp?`  
响应：`result`，`value`（最长跟踪时长，秒），`tracking_status`，`matching_periods`。

**GET** `/check/target_is_fully_searched` — 检查覆盖率是否达到阈值（默认 0.99）  
查询：`target_id`，`coverage_threshold?`  
响应：`result`，`value`（覆盖率，0-1），`coverage_percentage`。

**GET** `/check/target_searched_area_percentage` — 检查覆盖率是否达到预期比例（0-1）  
查询：`target_id`，`expected_percentage`（0-1）  
响应：`result`，`value`（覆盖率），`coverage_percentage`。

**GET** `/check/task_progress` — 任务进度与预期比率（0-1）  
查询参数：`expected_progress?` (0-1)  
响应：`result`、`value`（进度比率）、`progress_percentage`、`is_completed`。  

**GET** `/check/task_done` — 基于会话进度的完成状态  
查询参数：*（无）*  
响应：`result`、`value`（进度比率）、`progress_percentage`、`status_message`、`details`。  

### 检查端点示例  

```bash
# Check drone position within tolerance
curl -X GET "http://localhost:8000/check/drone_position?drone_id=drone-1&x=50.0&y=30.0&z=10.0&tolerance=2.0" \
  -H "X-API-Key: <ADMIN_API_KEY>"

# Check drone battery level
curl -X GET "http://localhost:8000/check/drone_battery_level?drone_id=drone-1&min_level=20.0" \
  -H "X-API-Key: <ADMIN_API_KEY>"

# Check if drone is at home position
curl -X GET "http://localhost:8000/check/drone_at_home?drone_id=drone-1&tolerance=5.0" \
  -H "X-API-Key: <ADMIN_API_KEY>"

# Check if target is within drone distance
curl -X GET "http://localhost:8000/check/target_within_drone_distance?drone_id=drone-1&target_id=target-1&max_distance=50.0" \
  -H "X-API-Key: <ADMIN_API_KEY>"

# Check if two drones are within distance
curl -X GET "http://localhost:8000/check/two_drones_distance?drone_1_id=drone-1&drone_2_id=drone-2&max_distance=100.0" \
  -H "X-API-Key: <ADMIN_API_KEY>"

# Check whether all pairwise distances in a drone group stay within bounds
curl -X GET "http://localhost:8000/check/drone_group_distance?drone_ids=drone-1&drone_ids=drone-2&drone_ids=drone-3&min_distance=10.0&max_distance=100.0" \
  -H "X-API-Key: <ADMIN_API_KEY>"

# Check whether any pair in a drone group satisfies the distance bounds
curl -X GET "http://localhost:8000/check/drone_group_distance?drone_ids=drone-1&drone_ids=drone-2&drone_ids=drone-3&min_distance=10.0&max_distance=100.0&mode=any_pair" \
  -H "X-API-Key: <ADMIN_API_KEY>"

# Check whether a drone sent message text containing a substring
curl -X GET "http://localhost:8000/check/drone_has_sent_message_content?drone_id=drone-1&content=alert" \
  -H "X-API-Key: <ADMIN_API_KEY>"

# Check whether a drone sent matching content to a specific recipient
curl -X GET "http://localhost:8000/check/drone_has_sent_message_content?drone_id=drone-1&to_drone_id=drone-2&content=hold%20position" \
  -H "X-API-Key: <ADMIN_API_KEY>"

# Check if drone has taken off (history)
curl -X GET "http://localhost:8000/check/drone_has_taken_off?drone_id=drone-1&min_altitude=5.0" \
  -H "X-API-Key: <ADMIN_API_KEY>"

# Check if drone has visited a position (history)
curl -X GET "http://localhost:8000/check/drone_has_visited_position?drone_id=drone-1&x=50.0&y=30.0&z=10.0&tolerance=2.0" \
  -H "X-API-Key: <ADMIN_API_KEY>"

# Check if drone has moved minimum distance (history)
curl -X GET "http://localhost:8000/check/drone_has_moved_distance?drone_id=drone-1&min_distance=100.0" \
  -H "X-API-Key: <ADMIN_API_KEY>"

# Check if drone has taken photos (history)
curl -X GET "http://localhost:8000/check/drone_has_taken_photo?drone_id=drone-1&min_count=3" \
  -H "X-API-Key: <ADMIN_API_KEY>"

# Check if drone has hovered (history)
curl -X GET "http://localhost:8000/check/drone_has_hovered?drone_id=drone-1&min_duration=5.0" \
  -H "X-API-Key: <ADMIN_API_KEY>"

# Check if all drones have taken off (check history)
curl -X GET "http://localhost:8000/check/all_drones_have_taken_off?check_history=true&min_altitude=5.0" \
  -H "X-API-Key: <ADMIN_API_KEY>"

# Check if all drones have taken off (check current status only)
curl -X GET "http://localhost:8000/check/all_drones_have_taken_off?check_history=false&min_altitude=5.0" \
  -H "X-API-Key: <ADMIN_API_KEY>"

# Check if all drones are currently hovering
curl -X GET "http://localhost:8000/check/all_drones_hovering" \
  -H "X-API-Key: <ADMIN_API_KEY>"

# Check if all drones have landed at least once (check history)
curl -X GET "http://localhost:8000/check/all_drones_have_landed?check_history=true&min_count=1" \
  -H "X-API-Key: <ADMIN_API_KEY>"

# Check if all drones are on ground
curl -X GET "http://localhost:8000/check/all_drones_on_ground" \
  -H "X-API-Key: <ADMIN_API_KEY>"

# Check if target has been reached
curl -X GET "http://localhost:8000/check/target_is_reached?target_id=target-1" \
  -H "X-API-Key: <ADMIN_API_KEY>"

# Check if specific drone reached target
curl -X GET "http://localhost:8000/check/target_is_reached_by_drone?target_id=target-1&drone_id=drone-1" \
  -H "X-API-Key: <ADMIN_API_KEY>"

# Check task progress
curl -X GET "http://localhost:8000/check/task_progress?expected_progress=0.8" \
  -H "X-API-Key: <ADMIN_API_KEY>"

# Check if task is done
curl -X GET "http://localhost:8000/check/task_done" \
  -H "X-API-Key: <ADMIN_API_KEY>"
```

---  

**最后更新：** 2025  
**API 版本：** 1.0.0
