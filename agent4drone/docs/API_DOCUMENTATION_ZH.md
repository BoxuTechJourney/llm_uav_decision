# MultiUAV-Plat 服务器系统 API 文档

> MultiUAV-Plat 服务器系统的全面 API 参考 —— 控制无人机、管理环境和模拟飞行场景的完整指南。

**版本：** 1.0.0
**基础URL：** `http://localhost:8000`
**交互式文档：** http://localhost:8000/docs

---

## 目录

### 入门
1. [基础URL](#base-url)
2. [认证](#authentication)
3. [响应格式](#response-format)
4. [快速入门指南](#quick-start-guide)

### 核心功能
5. [自动充电系统](#automatic-charging-system)
6. [会话管理](#session-api)
7. [无人机控制](#drone-api)
8. [命令执行](#command-api)

### API 端点
9. [会话 API](#session-api)
10. [任务管理 API](#task-management-api)
11. [无人机 API](#drone-api)
12. [命令 API](#command-api)
13. [直接命令 API](#direct-command-api)
14. [电池管理 API](#battery-management-api)
15. [目标 API](#target-api)
16. [航点 API](#waypoint-api)
17. [环境 API](#environment-api)
18. [障碍物 API](#obstacle-api)
19. [碰撞检测 API](#collision-detection-api)

---

## 基础URL

所有 API 端点均相对于您服务器部署的基础 URL。

**默认值：** `http://localhost:8000`

您可以使用命令行参数自定义主机和端口：
```bash
python main.py --host 0.0.0.0 --port 8080

# Override the per-session stored request-history retention
python main.py --api-only --request-history-limit 10000
```

## 认证

该 API 使用基于 **API 密钥的认证**，并附带基于角色的访问控制 (RBAC)。

### 角色

共有 **四种用户角色**：

| 角色 | 访问级别 | 是否需要认证 | 权限 |
|------|-------------|------------------------|-------------|
| **AGENT** | 基本访问 | 不需要 - 当 `X-API-Key` 省略或为空时，默认为该角色；可接受可选的 AGENT 密钥 | 可以控制无人机并查看 AGENT 可见性限制内的资源 |
| **USER** | 基本访问 | 需要 - 提供 USER API 密钥 | 继承 AGENT 权限，并可查看其他场景资源 |
| **SYSTEM** | 管理 | 需要 - 提供 SYSTEM API 密钥 | 可以管理所有资源（继承 USER/AGENT 权限） |
| **ADMIN** | 完全访问 | 需要 - 提供 ADMIN API 密钥 | 对所有端点具有完全访问权限 |

### 认证头

当 `X-API-Key` 省略或留空时，请求默认使用 AGENT 角色。要使用其他角色，请在 `X-API-Key` 头中包含该角色的一个有效密钥：

```bash
# Example with AGENT key
curl -H "X-API-Key: <AGENT_API_KEY>" http://localhost:8000/drones

# Example with SYSTEM key
curl -H "X-API-Key: <SYSTEM_API_KEY>" http://localhost:8000/sessions
```

**API 密钥：**
- AGENT：`<AGENT_API_KEY>`
- USER：硬编码的 USER 权限密钥之一
- SYSTEM：硬编码的 SYSTEM 权限密钥之一
- ADMIN：硬编码的 ADMIN 权限密钥之一

实际的密钥值存储在软件中，故意未在文档中列出。

有关完整的认证详情，请参阅 [AUTHENTICATION_ZH.md](AUTHENTICATION_ZH.md)。

## 响应格式

所有 API 响应均使用 JSON 格式，结构一致。

### 成功响应
```json
{
  "id": "drone-123",
  "name": "Scout Alpha",
  "status": "flying",
  ...
}
```

### 错误响应
```json
{
  "detail": "Drone not found"
}
```

### HTTP 状态码

| 代码 | 含义 | 使用场景 |
|------|---------|-------|
| 200 | 成功 | 成功的 GET、PUT 请求 |
| 201 | 已创建 | 成功的 POST 请求 |
| 204 | 无内容 | 成功的 DELETE 请求 |
| 400 | 错误请求 | 无效的请求参数 |
| 404 | 未找到 | 资源不存在 |
| 500 | 服务器内部错误 | 服务器错误 |

## 快速入门指南

### 1. 启动服务器
```bash
python main.py --api-only
```

### 2. 验证服务器正在运行
```bash
curl http://localhost:8000/
# Response: {"status":"online","message":"MultiUAV-Plat Server System API is running"}
```

### 3. 检查服务器版本
```bash
curl http://localhost:8000/version
# Response: {"name":"MultiUAV-Plat Server System API","version":"1.0.0"}
```

### 4. 创建您的第一架无人机
```bash
curl -X POST "http://localhost:8000/drones" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Test Drone",
    "model": "Quadcopter X1",
    "max_speed": 15.0,
    "max_altitude": 100.0,
    "battery_capacity": 100.0
  }'
```

### 5. 控制无人机
```bash
# Take off
curl -X POST "http://localhost:8000/drones/{drone_id}/command/take_off?altitude=10.0"

# Move to location
curl -X POST "http://localhost:8000/drones/{drone_id}/command/move_to?x=50&y=50&z=15"

# Land
curl -X POST "http://localhost:8000/drones/{drone_id}/command/land"
```

---

## 自动充电系统

MultiUAV-Plat 服务器系统包含自动充电功能，可在运行期间保持无人机电池电量，无需手动充电命令。

### 工作原理

1. **航点目标**：创建带有 `charge_amount` 属性的航点目标，作为充电站
2. **自动检测**：系统持续监控无人机相对于航点目标的位置
3. **自动充电**：当无人机在航点半径范围内 **着陆或空闲**（非悬停）时，系统会自动为其电池充电
4. **即时充电**：`charge_amount` 在每个更新周期即时应用（默认：每周期 25%）
5. **无需手动命令**：与手动 `CHARGE` 命令不同，此过程自动进行，无需用户干预
6. **电池管理**：当电池电量达到 100% 或无人机离开航点半径时，充电停止

### 充电要求

要实现自动充电，必须满足以下条件：
- 无人机必须处于 **IDLE** 或 **READY** 状态（降落在地面，非悬停状态）
- 无人机必须在航点目标的 **半径** 范围内（球形距离检查）
- 目标必须是 **waypoint** 类型，并具有有效的 `charge_amount`
- 无人机电池电量必须低于 100%

**重要提示：** 处于空中悬停状态的无人机不会自动充电，即使它在航点半径范围内。无人机必须着陆。

### 用于充电的航点属性

用作充电站的航点目标具有以下属性：
- `type`：必须设置为 `waypoint`
- `radius`：定义充电区域半径，单位为米（通常为 5-10 米）
- `charge_amount`：每个更新周期增加的电量百分比（默认值：25%，范围：0.1-100%）
- `position`：充电站的位置 {x, y, z}

### 使用示例

1. 创建一个具备充电功能的航点目标：
```bash
curl -X POST http://localhost:8000/targets \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Charging Station Alpha",
    "type": "waypoint",
    "position": {"x": 0.0, "y": 0.0, "z": 0.0},
    "radius": 10.0,
    "charge_amount": 25.0
  }'
```

2. 将无人机降落在航点半径内（无人机将自动充电）
3. 通过无人机 API 监控电量水平——您将看到电量的自动增加
4. 充电发生时，系统日志将显示 `[AUTO-CHARGE]` 消息

### 手动充电与自动充电

- **手动充电**：使用显式的 `charge_amount` 参数执行 `CHARGE` 命令
- **自动充电**：当无人机降落在航点半径内时自动发生
- 两种方式均为即时充电，可充至 100%
- 自动充电激活时不会阻止电池消耗

### API 集成

自动充电系统与以下端点协作：
- **目标 API**：创建和管理航点充电站
- **无人机 API**：查看实时电池状态和自动充电效果
- **命令 API**：如有需要，仍可通过 `CHARGE` 命令进行手动充电

## 会话 API

会话 API 允许您管理包含所有无人机、目标、障碍物和环境数据的仿真会话。会话提供了一种组织和隔离不同场景或任务的方式。

**注意：** 服务器启动时，会自动创建一个包含示例数据的“示例会话”，其中包括无人机、目标、障碍物和环境设置。这确保了系统立即可用，无需手动创建会话。

### 获取所有会话

**端点：** `GET /sessions`

**认证：** 需要 USER 角色（SYSTEM 和 ADMIN 继承）

**描述：** 检索系统中所有会话的列表。对于 AGENT/USER 角色，仅返回元数据（无历史记录，无实体数据）。对于 SYSTEM/ADMIN 角色，返回完整的会话元数据。

**参数：** 无

**响应：** 会话对象数组

**示例请求：**
```bash
curl -X GET http://localhost:8000/sessions
```

**示例响应：**
```json
[
  {
    "id": "session-123e4567-e89b-12d3-a456-426614174000",
    "name": "Example Session",
    "description": "A comprehensive example session with drones, targets, obstacles, and environment setup",
    "status": "active",
    "task_type": "area_search",
    "task_description": "Search designated areas for targets of interest",
    "created_at": 1620000000.0,
    "last_updated": 1620000100.0,
    "statistics": {
      "drone_count": 3,
      "target_count": 6,
      "obstacle_count": 6,
      "environment_id": "env-456",
      "commands_executed": 15,
      "total_flight_time": 120.5,
      "total_distance_traveled": 450.2
    }
  }
]
```

### 创建新会话

**端点：** `POST /sessions`

**描述：** 创建一个具有自动生成 ID 的新会话。可以选择包含要与会话一起创建的无人机、目标、障碍物和环境数据。

**请求体参数：**

| 名称 | 类型 | 必需 | 描述 |
|------|------|----------|-------------|
| name | string | 是 | 会话名称 |
| description | string | 否 | 会话描述 |
| with_examples | boolean | 否 | 是否创建示例数据（默认值：false） |
| task_type | string | 否 | 任务类型：'area_search'、'area_assignment_and_patrol'、'target_assignment'、'target_tracking' 或 'others'（默认值：'others'） |
| task_description | string | 否 | 任务/使命的详细描述 |
| is_distance_3d | boolean | 否 | 是否使用 3D 距离进行计算（默认值：false） |
| canvas_width | number | 否 | 仿真画布宽度（米）（默认值：1024.0） |
| canvas_height | number | 否 | 仿真画布高度（米）（默认值：768.0） |
| creator | string | 否 | 创建会话的用户名称；若省略，则默认为调用者的角色 |
| drones | array | 否 | 要创建的无人机对象数组（默认值：[]） |
| targets | array | 否 | 要创建的目标对象数组（默认值：[]） |
| obstacles | array | 否 | 要创建的障碍物对象数组（默认值：[]） |
| environment | object | 否 | 要创建的环境对象（默认值：null） |

如果未提供 `creator`，服务器会将调用者的角色记录为创建者。

**查询参数：**

| 名称 | 类型 | 必需 | 默认值 | 描述 |
|------|------|----------|---------|-------------|
| data | boolean | 否 | true | 若为 true，则返回完整的会话数据，包括所有创建的实体。若为 false，则仅返回会话元数据。 |

**响应：** 会话对象

**示例请求（简单会话）：**
```bash
curl -X POST http://localhost:8000/sessions \
  -H "Content-Type: application/json" \
  -H "X-API-Key: <SYSTEM_API_KEY>" \
  -d '{
    "name": "My Custom Session",
    "description": "A custom session for testing",
    "creator": "planner-ops",
    "with_examples": false,
    "task_type": "target_tracking",
    "task_description": "Track and monitor moving targets"
  }'
```

**示例响应：**
```json
{
  "id": "session-789a0123-b456-78c9-d012-345678901234",
  "name": "My Custom Session",
  "description": "A custom session for testing",
  "status": "active",
  "creator": "planner-ops",
  "task_type": "target_tracking",
  "task_description": "Track and monitor moving targets",
  "created_at": 1620000200.0,
  "last_updated": 1620000200.0,
  "statistics": {
    "drone_count": 0,
    "target_count": 0,
    "obstacle_count": 0,
    "environment_id": null
  }
}
```

**示例请求（包含实体）：**
```bash
curl -X POST http://localhost:8000/sessions \
  -H "Content-Type: application/json" \
  -H "X-API-Key: <SYSTEM_API_KEY>" \
  -d '{
    "name": "Mission with Fleet",
    "description": "Pre-configured mission",
    "drones": [
      {
        "name": "Scout-1",
        "model": "Model-D4",
        "max_speed": 20.0,
        "max_altitude": 120.0,
        "battery_capacity": 4000.0,
        "position": {"x": 0, "y": 0, "z": 0}
      }
    ],
    "targets": [
      {
        "name": "Waypoint Alpha",
        "type": "fixed",
        "position": {"x": 100, "y": 100, "z": 0},
        "radius": 5.0
      }
    ]
  }'
```

**示例响应：**
```json
{
  "id": "session-abc456",
  "name": "Mission with Fleet",
  "description": "Pre-configured mission",
  "status": "active",
  "creator": "system",
  "task_type": "others",
  "task_description": "",
  "created_at": 1620000200.0,
  "last_updated": 1620000200.0,
  "statistics": {
    "drone_count": 1,
    "target_count": 1,
    "obstacle_count": 0,
    "environment_id": null,
    "total_commands_executed": 0,
    "total_flight_time": 0.0,
    "total_distance_traveled": 0.0,
    "session_time": 0.0
  }
}
```

---

### 使用特定 ID 创建/恢复会话

**端点：** `POST /sessions/{session_id}`

**描述：** 创建或恢复具有特定 ID 的会话。非常适合从备份中恢复会话。如果请求体包含无人机、目标、障碍物或环境数据，它们将被自动创建/恢复。

**路径参数：**

| 名称 | 类型 | 必需 | 描述 |
|------|------|----------|-------------|
| session_id | string | 是 | 要用于会话的特定 ID |

**请求体参数：**

| 名称 | 类型 | 必需 | 描述 |
|------|------|----------|-------------|
| name | string | 是 | 会话名称 |
| description | string | 否 | 会话描述 |
| status | string | 否 | 会话状态（默认值：'active'） |
| task_type | string | 否 | 任务类型（默认值：'others'） |
| task_description | string | 否 | 详细任务描述 |
| is_distance_3d | boolean | 否 | 使用 3D 距离进行计算（默认值：false） |
| canvas_width | number | 否 | 仿真画布宽度（米）（默认值：1024.0） |
| canvas_height | number | 否 | 仿真画布高度（米）（默认值：768.0） |
| creator | string | 否 | 创建/恢复会话的用户名称；若省略，则默认为调用者的角色 |
| drones | array | 否 | 待恢复的无人机对象数组（默认值：[]） |
| targets | array | 否 | 待恢复的目标对象数组（默认值：[]） |
| obstacles | array | 否 | 待恢复的障碍物对象数组（默认值：[]） |
| environment | object | 否 | 待恢复的环境对象（默认值：null） |

若未提供 `creator`，服务器将把调用方角色记录为创建者。

**查询参数：**

| 名称 | 类型 | 是否必需 | 默认值 | 描述 |
|------|------|----------|---------|-------------|
| data | boolean | 否 | true | 若为 true，返回完整的会话数据；若为 false，仅返回元数据。 |

**响应：** 会话对象（默认仅包含元数据；若 `data=true` 则包含完整数据）

**错误：**
- **500 内部服务器错误：** 删除现有会话失败时触发

**示例请求（从备份恢复）：**
```bash
curl -X POST "http://localhost:8000/sessions/mission-backup-2024?data=true" \
  -H "Content-Type: application/json" \
  -H "X-API-Key: <SYSTEM_API_KEY>" \
  -d '{
    "name": "Restored Mission",
    "description": "Restored from backup",
    "creator": "planner-ops",
    "drones": [
      {
        "id": "drone-original-001",
        "name": "Scout Alpha",
        "model": "Model-D4",
        "position": {"x": 50, "y": 30, "z": 15},
        "battery_level": 85.5
      }
    ],
    "targets": [
      {
        "id": "target-original-001",
        "name": "Search Zone",
        "type": "circle",
        "position": {"x": 100, "y": 100, "z": 0},
        "radius": 25.0
      }
    ],
    "obstacles": [],
    "environment": {
      "name": "Clear Weather",
      "weather": "clear",
      "temperature": 22.0,
      "humidity": 45.0
    }
  }'
```

**示例响应（完整数据 - 扁平格式）：**
```json
{
  "id": "mission-backup-2024",
  "name": "Restored Mission",
  "description": "Restored from backup",
  "status": "active",
  "creator": "planner-ops",
  "task_type": "others",
  "task_description": "",
  "created_at": 1620000300.0,
  "last_updated": 1620000300.0,
  "statistics": {
    "drone_count": 1,
    "target_count": 1,
    "obstacle_count": 0,
    "environment_id": "env-restored-001",
    "total_commands_executed": 0,
    "total_flight_time": 0.0,
    "total_distance_traveled": 0.0,
    "session_time": 0.0,
    "task_progress": {...}
  },
  "drones": [
    {
      "id": "drone-original-001",
      "name": "Scout Alpha",
      "model": "Model-D4",
      "status": "hovering",
      "position": {"x": 50, "y": 30, "z": 15},
      "battery_level": 85.5
    }
  ],
  "targets": [
    {
      "id": "target-original-001",
      "name": "Search Zone",
      "type": "circle",
      "position": {"x": 100, "y": 100, "z": 0},
      "radius": 25.0
    }
  ],
  "obstacles": [],
  "environment": {
    "id": "env-restored-001",
    "name": "Clear Weather",
    "weather": "clear",
    "temperature": 22.0,
    "humidity": 45.0
  },
  "history": {
    "command_history": [],
    "status_history": {},
    "target_reaches": {},
    "area_coverage": {},
    "path_history": {}
  }
}
```



**行为说明：**
- 若会话已存在：删除现有会话，然后使用相同 ID 创建新会话（自动覆盖）
- 若会话不存在：使用指定的 ID 创建新会话
- 从备份恢复时，使用此端点替换现有会话

---

### 获取当前会话

**端点：** `GET /sessions/current`

**描述：** 获取当前活动会话。默认仅返回元数据和统计信息。使用 `data` 参数可获取包含所有无人机、目标、障碍物及环境的完整会话数据。

**查询参数：**

| 名称 | 类型 | 是否必需 | 默认值 | 描述 |
|------|------|----------|---------|-------------|
| data | boolean | 否 | false | 若为 true，返回包含所有实体的完整会话数据；若为 false，仅返回元数据和统计信息。 |

**响应：** 当前会话对象（默认仅包含元数据；若 `data=true` 则包含完整数据）

**响应字段（当 data=false 时，默认情况）：**
- 所有标准会话字段（id、name、description、status 等）
- `statistics`：包含无人机数量、飞行时间等的会话统计信息
- `task_progress`：实时任务完成进度（task_type、progress_percentage、is_completed、status_message、details）

**响应字段（当 data=true 时）：**
- `session`：会话元数据与统计信息
- `drones`：所有无人机及其当前状态的数组
- `targets`：所有目标（固定、移动、航点、环形、多边形）的数组
- `obstacles`：所有障碍物的数组
- `environment`：当前环境设置

**示例请求（仅元数据）：**
```bash
curl -X GET http://localhost:8000/sessions/current
# or explicitly
curl -X GET "http://localhost:8000/sessions/current?data=false"
```

**示例响应：**
```json
{
  "id": "session-abc123",
  "name": "Area Search Mission",
  "description": "Urban search and rescue operation",
  "is_distance_3d": false,
  "canvas_width": 1024.0,
  "canvas_height": 768.0,
  "created_at": 1705449600.0,
  "last_updated": 1705449700.0,
  "statistics": {
    "drone_count": 3,
    "target_count": 5,
    "obstacle_count": 8,
    "environment_id": "env-456",
    "total_commands_executed": 127,
    "total_flight_time": 450.5,
    "total_distance_traveled": 2340.8,
    "total_target_reaches": 15,
    "drones_with_target_reaches": 3,
    "unique_targets_reached": 5,
    "session_time": 3600.0,
    "command_history_size": 127,
    "target_reach_log_size": 15,
    "task_progress": {
      "task_type": "area_search",
      "progress_percentage": 45,
      "is_completed": false,
      "status_message": "Task to be Done",
      "details": {
        "total_targets": 2,
        "average_coverage": 45.5,
        "coverage_by_target": {
          "target-abc": 50.0,
          "target-def": 41.0
        }
      },
      "target_reach_summary": {
        "total_reaches": 15,
        "drones_with_reaches": 3,
        "unique_targets_reached": 5
      },
      "area_coverage_summary": {
        "total_targets_tracked": 2,
        "average_coverage": 45.5,
        "fully_covered_targets": 0
      }
    }
  },
  "history": {
    "target_reaches": {
      "drone-001": {
        "target-abc": [1705449650.0, 1705449750.0],
        "target-def": [1705449800.0]
      }
    },
    "area_coverage": {
      "target-abc": {
        "area_type": "circle",
        "total_area": 1000.0,
        "covered_area": 500.0,
        "coverage_percentage": 50.0,
        "covered_points": [[10,10], [11,10]]
      }
    },
    "command_history": [
      {
        "drone_id": "drone-001",
        "command": "move_to",
        "parameters": {"x": 50.0, "y": 50.0, "z": 15.0},
        "timestamp": 1705449750.0
      }
    ],
    "status_history": {},
    "path_history": {}
  }
}
```

**示例请求（完整数据）：**
```bash
curl -X GET "http://localhost:8000/sessions/current?data=true"
```

**示例响应（完整数据 - 扁平格式）：**
```json
{
  "id": "session-abc123",
  "name": "Area Search Mission",
  "description": "Urban search and rescue operation",
  "status": "active",
  "creator": "system",
  "task_type": "area_search",
  "task_description": "Search grid zones for targets",
  "is_distance_3d": false,
  "canvas_width": 1024.0,
  "canvas_height": 768.0,
  "created_at": 1705449600.0,
  "last_updated": 1705449700.0,
  "statistics": {
    "drone_count": 3,
    "target_count": 5,
    "obstacle_count": 8,
    "environment_id": "env-456",
    "total_commands_executed": 25,
    "total_flight_time": 450.5,
    "total_distance_traveled": 1250.75,
    "session_time": 600.0,
    "task_progress": {
      "task_type": "area_search",
      "progress_percentage": 45,
      "is_completed": false,
      "status_message": "Task to be Done",
      "details": {
        "total_targets": 5,
        "average_coverage": 45.2
      },
      "target_reach_summary": {
        "total_reaches": 0,
        "drones_with_reaches": 0,
        "unique_targets_reached": 0
      },
      "area_coverage_summary": {
        "total_targets_tracked": 5,
        "average_coverage": 45.2,
        "fully_covered_targets": 0
      }
    }
  },
  "history": {
    "target_reaches": {},
    "area_coverage": {},
    "command_history": [],
    "status_history": {},
    "path_history": {}
  },
  "drones": [
    {
      "id": "drone-001",
      "name": "Scout Alpha",
      "model": "QuadX-450 Pro",
      "status": "hovering",
      "position": {"x": 50.0, "y": 30.0, "z": 15.0},
      "battery_level": 85.5
    }
  ],
  "targets": [
    {
      "id": "target-001",
      "name": "Search Zone Alpha",
      "type": "circle",
      "position": {"x": 100.0, "y": 100.0, "z": 0.0},
      "radius": 25.0
    }
  ],
  "obstacles": [
    {
      "id": "obstacle-001",
      "name": "Building A",
      "type": "circle",
      "position": {"x": 150.0, "y": 150.0, "z": 0.0},
      "radius": 15.0,
      "height": 30.0
    }
  ],
  "environment": {
    "id": "env-456",
    "name": "Clear Weather",
    "weather": "clear",
    "temperature": 22.0,
    "humidity": 45.0
  }
}
```

### 获取当前会话数据（便捷端点）

**端点：** `GET /sessions/current/data`

**描述：** 便捷端点，返回当前活动会话的完整数据。等效于 `GET /sessions/current?data=true`。

**身份验证：** 需要 SYSTEM 角色或更高权限

**查询参数：** 无

**响应：** 完整的会话数据对象，包含所有无人机、目标、障碍物及环境信息。

**示例请求：**
```bash
curl -X GET http://localhost:8000/sessions/current/data
```

**示例响应：**
与上文中 `GET /sessions/current?data=true` 的响应结构相同。

### 获取指定会话

**端点：** `GET /sessions/{session_id}`

**描述：** 获取特定会话的信息。默认仅返回元数据和统计信息。使用 `data` 参数可获取包含所有无人机、目标、障碍物及环境的完整会话数据。

**路径参数：**

| 名称 | 类型 | 是否必需 | 描述 |
|------|------|----------|-------------|
| session_id | string | 是 | 会话的 ID（位于 URL 路径中） |

**查询参数：**

| 名称 | 类型 | 是否必需 | 默认值 | 描述 |
|------|------|----------|---------|-------------|
| data | boolean | 否 | false | 若为 true，返回包含所有实体的完整会话数据；若为 false，仅返回元数据和统计信息。 |

**响应：** 会话对象（默认仅包含元数据；若 `data=true` 则包含完整数据）

**响应字段（当 data=false 时，默认情况）：**
- 所有标准会话字段（id、name、description、status、task 等）
- `statistics`：全面的会话统计信息
- `task_progress`：实时任务完成进度

**响应字段（当 data=true 时）：**
- `session`：会话元数据与统计信息
- `drones`：所有无人机及其当前状态的数组
- `targets`：所有目标（固定、移动、航点、环形、多边形）的数组
- `obstacles`：所有障碍物的数组
- `environment`：当前环境设置
- `history`：一个对象，包含：
- `command_history`：已执行命令的数组
- `status_history`：无人机状态日志
- `target_reaches`：按无人机和目标分组的紧凑到达历史记录，包含计数及最近时间戳
- `moving_target_tracking`：紧凑的移动目标跟踪历史，包含状态、总跟踪事件数及最近跟踪时段
- `area_coverage`：区域覆盖跟踪数据
- `path_history`：无人机移动轨迹/迹线

**示例请求（仅元数据）：**
```bash
curl -X GET http://localhost:8000/sessions/session-abc123
# or explicitly
curl -X GET "http://localhost:8000/sessions/session-abc123?data=false"
```

**示例响应（仅元数据）：**
与上文“获取当前会话”的元数据响应结构相同。

**示例请求（完整数据）：**
```bash
curl -X GET "http://localhost:8000/sessions/session-abc123?data=true"
```

**示例响应（完整数据）：**
结构与上文“获取当前会话”的完整数据响应相同。

### 更新会话

**端点：** `PUT /sessions/{session_id}`

**描述：** 更新会话的元数据（名称、描述、状态）。此端点仅更新会话元数据——如需更新无人机、目标或障碍物，请使用各自对应的端点。

**路径参数：**

| 名称 | 类型 | 必需 | 描述 |
|------|------|----------|-------------|
| session_id | string | 是 | 会话的 ID（位于 URL 路径中） |

**请求体参数：**

| 名称 | 类型 | 必需 | 描述 |
|------|------|----------|-------------|
| name | string | 否 | 会话的新名称 |
| description | string | 否 | 会话的新描述 |
| status | string | 否 | 新状态（active、paused、completed、archived） |
| is_distance_3d | boolean | 否 | 是否使用三维距离进行计算 |
| canvas_width | number | 否 | 模拟画布的新宽度 |
| canvas_height | number | 否 | 模拟画布的新高度 |

**查询参数：**

| 名称 | 类型 | 必需 | 默认值 | 描述 |
|------|------|----------|---------|-------------|
| data | boolean | 否 | false | 若为 true，则返回完整的会话数据；若为 false，则仅返回元数据。 |

**响应：** 更新后的会话对象（默认仅元数据，若 `data=true` 则返回完整数据）

**示例请求（仅元数据）：**
```bash
curl -X PUT http://localhost:8000/sessions/session-abc123 \
  -H "Content-Type: application/json" \
  -H "X-API-Key: <SYSTEM_API_KEY>" \
  -d '{
    "name": "Updated Mission Session",
    "status": "completed",
    "is_distance_3d": true
  }'
```

**示例响应（仅元数据）：**
```json
{
  "id": "session-abc123",
  "name": "Updated Mission Session",
  "description": "Original description",
  "status": "completed",
  "is_distance_3d": true,
  "canvas_width": 1024.0,
  "canvas_height": 768.0,
  "created_at": 1620000200.0,
  "last_updated": 1620000500.0,
  "statistics": {
    "drone_count": 3,
    "target_count": 5
  }
}
```

**示例请求（含完整数据）：**
```bash
curl -X PUT "http://localhost:8000/sessions/session-abc123?data=true" \
  -H "Content-Type: application/json" \
  -H "X-API-Key: <SYSTEM_API_KEY>" \
  -d '{
    "name": "Mission Complete",
    "status": "completed"
  }'
```

**示例响应（完整数据 - 扁平格式）：**
```json
{
  "id": "session-abc123",
  "name": "Mission Complete",
  "description": "Original description",
  "status": "completed",
  "creator": "system",
  "task_type": "area_search",
  "task_description": "Search grid zones for targets",
  "created_at": 1620000200.0,
  "last_updated": 1620000600.0,
  "statistics": {
    "drone_count": 3,
    "target_count": 5,
    "obstacle_count": 2,
    "environment_id": "env-456",
    "task_progress": {...}
  },
  "target_reaches": {},
  "drones": [...],
  "targets": [...],
  "obstacles": [...],
  "environment": {...},
  "history": {
    "command_history": [...],
    "status_history": {...},
    "target_reaches": {},
    "area_coverage": {...}
  }
}
```

### 删除会话

**端点：** `DELETE /sessions/{session_id}`

**描述：** 从系统中删除一个会话。

**参数：**

| 名称 | 类型 | 必需 | 描述 |
|------|------|----------|-------------|
| session_id | string | 是 | 会话的 ID（位于 URL 路径中） |

**响应：** 无内容（204）

**示例请求：**
```bash
curl -X DELETE http://localhost:8000/sessions/session-123e4567-e89b-12d3-a456-426614174000
```

### 设为当前会话

**端点：** `POST /sessions/{session_id}/set-current`

**认证：** 需要 USER 角色（SYSTEM 与 ADMIN 继承该权限）

**描述：** 将会话设置为当前活跃会话。对于 AGENT/USER 角色，仅返回元数据（不含历史记录或实体数据）；对于 SYSTEM/ADMIN 角色，返回完整的会话元数据。

**参数：**

| 名称 | 类型 | 必需 | 描述 |
|------|------|----------|-------------|
| session_id | string | 是 | 会话的 ID（位于 URL 路径中） |

**响应：** 会话对象（AGENT/USER 角色仅含元数据）

**示例请求：**
```bash
curl -X POST http://localhost:8000/sessions/session-123e4567-e89b-12d3-a456-426614174000/set-current
```

### 重置会话

**端点：** `POST /sessions/{session_id}/reset`

**描述：** 将会话重置到初始状态。清除无人机、目标、障碍物、环境、统计信息、命令/状态历史记录以及计时器，同时保留会话 ID、名称和描述。若会话处于活跃状态，还会清除所有控制器。

**参数：**

| 名称 | 类型 | 必需 | 描述 |
|------|------|----------|-------------|
| session_id | string | 是 | 会话的 ID（位于 URL 路径中） |

**响应：** 重置后的会话对象

**示例请求：**
```bash
curl -X POST http://localhost:8000/sessions/session-123e4567-e89b-12d3-a456-426614174000/reset
```

### 重置当前会话

**端点：** `POST /sessions/current/reset`

**描述：** 将当前活跃会话重置到初始状态。此端点会清除所有历史跟踪数据，同时保留会话实体与配置。

**将被清除的内容：**
- 命令历史（发送给无人机的所有命令）
- 状态历史（无人机状态变更记录）
- 路径历史（无人机移动轨迹/路线）
- 目标抵达日志（无人机抵达目标的记录）
- 区域覆盖数据（区域搜索任务的覆盖跟踪）
- 统计信息（已执行命令总数、飞行时长、飞行距离）
- 会话计时器（重置为 0）

**将被保留的内容：**
- 会话 ID、名称和描述
- 所有无人机及其当前位置和状态
- 所有目标
- 所有障碍物
- 环境配置
- 任务定义

**认证：** 需要 SYSTEM 角色或更高权限

**响应：** 重置后的会话对象

**示例请求：**
```bash
curl -X POST http://localhost:8000/sessions/current/reset
```

**示例响应：**
```json
{
  "id": "session-123e4567-e89b-12d3-a456-426614174000",
  "name": "Current Session",
  "description": "Active session for testing",
  "status": "active",
  "task_type": "area_search",
  "task_description": "Search designated areas",
  "creator": "system",
  "created_at": 1734000000.0,
  "last_updated": 1734001234.5,
  "total_commands_executed": 0,
  "total_flight_time": 0.0,
  "total_distance_traveled": 0.0,
  "session_time": 0.0,
  "num_drones": 3,
  "num_targets": 5,
  "num_obstacles": 2,
  "has_environment": true
}
```

### 获取会话数据

**端点：** `GET /sessions/{session_id}/data`

**描述：** 便捷端点，用于获取完整的会话数据，包括所有无人机、目标、障碍物和环境信息。等同于 `GET /sessions/{session_id}?data=true`。

**路径参数：**

| 名称 | 类型 | 必需 | 描述 |
|------|------|----------|-------------|
| session_id | string | 是 | 会话的 ID（位于 URL 路径中） |

**查询参数：** 无

**响应：** 完整的会话数据对象

**示例请求：**
```bash
curl -X GET http://localhost:8000/sessions/session-123e4567-e89b-12d3-a456-426614174000/data
```

**示例响应（扁平格式）：**
```json
{
  "id": "session-123e4567-e89b-12d3-a456-426614174000",
  "name": "Example Session",
  "description": "A comprehensive example session",
  "status": "active",
  "creator": "system",
      "task_type": "area_search",
      "task_description": "Search designated areas for targets",
          "is_distance_3d": false,
          "canvas_width": 1024.0,
          "canvas_height": 768.0,
          "created_at": 1620000000.0,  "last_updated": 1620000100.0,
  "statistics": {
    "drone_count": 3,
    "target_count": 6,
    "obstacle_count": 6,
    "environment_id": "env-456",
    "total_commands_executed": 15,
    "total_flight_time": 120.5,
    "total_distance_traveled": 450.2,
    "session_time": 300.0,
    "task_progress": {...}
  },
  "target_reaches": {},
  "target_reach_statistics": {...},
  "area_coverage_summary": {...},
  "recent_commands": [...],
  "drones": [
    {
      "id": "drone-001",
      "name": "Scout Alpha",
      "model": "QuadX-450 Pro",
      "status": "idle",
      "position": {"x": 10.0, "y": 10.0, "z": 0.0},
      "battery_level": 100.0
    }
  ],
  "targets": [
    {
      "id": "target-001",
      "name": "Primary Landing Zone",
      "type": "fixed",
      "position": {"x": 100.0, "y": 100.0, "z": 0.0}
    }
  ],
  "obstacles": [
    {
      "id": "obstacle-001",
      "name": "Corporate Headquarters",
      "type": "building",
      "position": {"x": 120.0, "y": 180.0, "z": 0.0}
    }
  ],
  "environment": {
    "id": "env-456",
    "name": "Clear Weather Environment",
    "weather": "clear",
    "temperature": 22.0,
    "humidity": 45.0
  },
  "history": {
    "target_reaches": {},
    "area_coverage": {},
    "command_history": [...],
    "status_history": {}
  }
}
```

### 会话截图

提供当前会话 UI 的渲染截图，支持 PNG、JPG、PDF、SVG 或 EPS 格式。适用于报告、快速预览和导出视觉化状态。

#### 获取当前会话截图

- 端点： `GET /sessions/current/screenshot`
- 描述： 返回当前活跃会话 UI 的截图。
- 查询参数：
- `format`（字符串，可选）：可选值为 `png`、`jpg`、`jpeg`、`pdf`、`svg`、`eps`（默认：`png`）。
- `width`（整数，可选）：图像宽度（像素，默认值：`1024`）。
- `height`（整数，可选）：图像高度（像素，默认值：`768`）。
- `center_x`（浮点数，可选）：画布中心 X 坐标（米）。
- `center_y`（浮点数，可选）：画布中心 Y 坐标（米）。
- `scale_px_per_meter`（浮点数，可选）：画布比例（像素/米）。
- `show_status`（布尔值，可选）：当为 `true` 时，包含无人机路径轨迹、区域搜索覆盖叠加层、已到达/追踪目标状态以及 UI 显示的状态栏元数据。默认值为 `false`。
- 响应：二进制图像/矢量内容。媒体类型根据 `format` 为 `image/png`、`image/jpeg`、`application/pdf`、`image/svg+xml` 或 `application/postscript`。

示例请求：

```bash
# PNG
curl -X GET "http://localhost:8000/sessions/current/screenshot?format=png&width=1024&height=768" \
  --output current_session.png

# JPG
curl -X GET "http://localhost:8000/sessions/current/screenshot?format=jpg" \
  --output current_session.jpg

# PDF
curl -X GET "http://localhost:8000/sessions/current/screenshot?format=pdf" \
  --output current_session.pdf

# SVG with status overlays
curl -X GET "http://localhost:8000/sessions/current/screenshot?format=svg&show_status=true" \
  --output current_session.svg

# EPS with status overlays
curl -X GET "http://localhost:8000/sessions/current/screenshot?format=eps&show_status=true" \
  --output current_session.eps
```

#### 获取特定会话的截图

- 端点：`GET /sessions/{session_id}/screenshot`
- 描述：返回指定会话的截图。
- 路径参数：
- `session_id`（字符串，必需）：要渲染的会话 ID。
- 查询参数：
- `format`（字符串，可选）：`png`、`jpg`、`jpeg`、`pdf`、`svg`、`eps` 之一（默认：`png`）。
- `width`（整数，可选）：图像宽度（像素，默认值：`1024`）。
- `height`（整数，可选）：图像高度（像素，默认值：`768`）。
- `center_x`（浮点数，可选）：画布中心 X 坐标（米）。
- `center_y`（浮点数，可选）：画布中心 Y 坐标（米）。
- `scale_px_per_meter`（浮点数，可选）：画布比例（像素/米）。
- `show_status`（布尔值，可选）：当为 `true` 时，包含无人机路径轨迹、区域搜索覆盖叠加层、已到达/追踪目标状态以及 UI 显示的状态栏元数据。默认值为 `false`。
- 响应：二进制图像/矢量内容。媒体类型根据 `format` 为 `image/png`、`image/jpeg`、`application/pdf`、`image/svg+xml` 或 `application/postscript`。

示例请求：

```bash
curl -X GET "http://localhost:8000/sessions/session-123e4567-e89b-12d3-a456-426614174000/screenshot?format=png&width=1280&height=720" \
  --output session_123e4567.png

curl -X GET "http://localhost:8000/sessions/session-123e4567-e89b-12d3-a456-426614174000/screenshot?format=svg&show_status=true" \
  --output session_123e4567.svg
```

### 会话追踪

其他端点提供每个会话的丰富追踪数据，包括命令历史、状态变化、目标到达和区域覆盖。

#### 获取命令历史

- 端点：`GET /sessions/{session_id}/command-history`
- 当前会话端点：`GET /sessions/current/command-history`
- 查询参数：
- `limit`（整数，可选）：要返回的最近命令的最大数量（默认：`100`，最大：`1000`）。
- 响应：`{ "command_history": [ ... ] }`，包含会话的最近命令。
- 当前会话端点在无活动会话时返回 `404` 及 `"No current session found"`。

示例：
```bash
curl -X GET "http://localhost:8000/sessions/session-123e4567/command-history?limit=50"

curl -X GET "http://localhost:8000/sessions/current/command-history?limit=50"
```

#### 获取请求历史

- 端点：
- `GET /sessions/current/request-history`
- `GET /sessions/{session_id}/request-history`
- 所需权限：
- `GET /sessions/current/request-history`：AGENT、SYSTEM 或 ADMIN。
- `GET /sessions/{session_id}/request-history`：SYSTEM 或 ADMIN。
- 查询参数：
- `limit`（整数，可选）：要返回的最近请求的最大数量（默认值和最大值：`1000`）。
- AGENT 调用者应发送一个稳定的非机密 `X-Agent-ID` 头。如果省略，AGENT 请求将归因于 `default_agent`。
- AGENT 调用者只能从具有相同 `agent_id` 的 AGENT 认证请求中检索当前会话的请求历史记录。SYSTEM 和 ADMIN 调用者接收未过滤的请求历史。
- 默认情况下，服务器每个会话存储多达 `5000` 条记录。此保留量可在启动时通过 `--request-history-limit` 配置；这与端点的 1000 条记录响应上限是分开的。
- 响应：按时间顺序排列的 `{ "request_history": [ ... ] }`。
- 记录与每个响应完成后活动的会话相关联。在没有活动会话的情况下发出的请求不会添加到会话历史中。
- 请求历史仅是运行时的。它不包含在会话对象、JSON 导出、导入或恢复中，并且在进程重新启动时丢失。
- 会话重置会清除运行时请求历史。
- 对这些端点的调用在产生响应后被记录，并且 `response_body: null`，因此它们出现在下一次查询中，而不会递归地嵌入先前的历史记录。
- 出于性能和递归安全性考虑，结构化 API 日志和会话请求历史记录中有意省略了请求历史端点的响应正文。

每条记录具有以下形状：

```json
{
  "request_id": "550e8400-e29b-41d4-a716-446655440000",
  "timestamp": "2026-06-23T10:30:00Z",
  "method": "POST",
  "path": "/drones/drone-1/command",
  "client_ip": "127.0.0.1",
  "client_port": 54321,
  "client_privilege": "ADMIN",
  "authentication_status": "api_key",
  "session_id": "session-123e4567",
  "query_params": {
    "tag": ["alpha", "beta"],
    "limit": "10"
  },
  "user_agent": "client-name/1.0",
  "agent_id": "agent-alpha",
  "request_body": {
    "command": "take_off",
    "parameters": {"altitude": 10}
  },
  "status_code": 200,
  "success": true,
  "duration_sec": 0.123,
  "response_body": {},
  "error": null
}
```

- `client_ip` 和 `client_port` 标识直接套接字对等端。转发的 IP 头不被信任。
- `client_privilege` 为 `AGENT`、`USER`、`SYSTEM`、`ADMIN` 或 `null`。
- `authentication_status` 为 `api_key`、`default_agent` 或 `invalid`。
- `agent_id` 是 AGENT 请求的标准化 `X-Agent-ID` 值，对于没有该标头的 AGENT 请求为 `default_agent`，对于非 AGENT 或旧记录为 `null`。
- `query_params` 保留原始查询字符串值以供重放。提供一次的键使用字符串值；重复的键使用有序数组；没有查询字符串的请求使用 `{}`。
- 敏感查询键使用与请求和响应正文相同的策略以不区分大小写的方式进行编辑。
- 缺少 `query_params` 的运行时记录显示为 `{}`。
- `user_agent` 最多 512 个字符。
- 绝不包含 API 密钥和不受限制的请求标头。
- 请求或响应正文中的敏感键、机密、密码和令牌被编辑。二进制截图正文不存储。

示例：

```bash
curl -X GET "http://localhost:8000/sessions/current/request-history?limit=1000" \
  -H "X-API-Key: <AGENT_API_KEY>" \
  -H "X-Agent-ID: agent-alpha"

curl -X GET "http://localhost:8000/sessions/session-123e4567/request-history?limit=100" \
  -H "X-API-Key: <SYSTEM_API_KEY>"
```

#### 清除请求历史

- 端点：
- `DELETE /sessions/current/request-history`
- `DELETE /sessions/{session_id}/request-history`
- 所需权限：SYSTEM 或 ADMIN。
- 说明：仅清除所选会话的运行时请求历史记录。它不会重置会话、清除命令历史、状态历史、路径历史、任务进度、实体、统计数据或已配置的请求历史记录保留限制。
- 清除请求本身不会被记录回请求历史记录。
- 响应：

```json
{
  "cleared": true,
  "session_id": "session-123e4567",
  "cleared_count": 42
}
```

示例：

```bash
curl -X DELETE "http://localhost:8000/sessions/current/request-history" \
  -H "X-API-Key: <SYSTEM_API_KEY>"

curl -X DELETE "http://localhost:8000/sessions/session-123e4567/request-history" \
  -H "X-API-Key: <SYSTEM_API_KEY>"
```

#### 获取状态历史

- 端点：`GET /sessions/{session_id}/status-history`
- 查询参数：
- `drone_id`（字符串，可选）：如果提供，则将状态历史过滤为特定无人机。
- 响应：`{ "status_history": { "drone_id": [ ... ] } }`，若未提供 `drone_id` 则返回所有无人机。

示例：
```bash
curl -X GET "http://localhost:8000/sessions/session-123e4567/status-history?drone_id=drone-001"
```

#### 获取目标到达记录

- 端点：`GET /sessions/{session_id}/target-reaches`
- 说明：返回紧凑的目标到达历史记录和汇总统计信息。对同一目标的**多次访问**仍会被记录，但会汇总成摘要，而不是作为原始事件日志返回。
- 响应：
- `target_reaches.by_drone`：按无人机的到达目标映射，包含 `count`、`first_reached_at`、`last_reached_at` 和 `recent_reached_at`
- `target_reaches.by_target`：按目标的映射，包含 `total_reaches`、`unique_drones`、`reached_by`、`first_reached_at`、`last_reached_at` 和 `recent_reached_at`
- `summary`：汇总信息，包含 `total_reaches`、`drones_with_reaches` 和 `unique_targets_reached`
- **注意**：此端点有意设计得简洁。它不会将每个历史事件作为独立记录返回。

示例：
```bash
curl -X GET "http://localhost:8000/sessions/session-123e4567/target-reaches"
```

响应示例：
```json
{
  "target_reaches": {
    "by_drone": {
      "drone-001": {
        "target-abc": {
          "count": 3,
          "first_reached_at": 1705449650.0,
          "last_reached_at": 1705449850.0,
          "recent_reached_at": [1705449650.0, 1705449750.0, 1705449850.0]
        }
      }
    },
    "by_target": {
      "target-abc": {
        "total_reaches": 4,
        "unique_drones": 2,
        "reached_by": ["drone-001", "drone-002"],
        "first_reached_at": 1705449650.0,
        "last_reached_at": 1705449850.0,
        "recent_reached_at": [1705449700.0, 1705449750.0, 1705449850.0]
      }
    }
  },
  "summary": {
    "total_reaches": 4,
    "drones_with_reaches": 2,
    "unique_targets_reached": 1
  }
}
```

#### 获取移动目标跟踪

- 端点：`GET /sessions/{session_id}/moving-target-tracking`
- 说明：返回指定会话的紧凑移动目标跟踪历史记录。
- 响应：
- `moving_target_tracking.{target_id}.tracking_status`：`tracked`、`stale` 或 `never_tracked`
- `moving_target_tracking.{target_id}.first_tracked_at` / `last_tracked_at`
- `moving_target_tracking.{target_id}.total_track_events`
- `moving_target_tracking.{target_id}.tracked_by`
- `moving_target_tracking.{target_id}.recent_periods`：最近的跟踪时间段，包含 `start_at`、`end_at`、`last_update_at`、`event_count`、`last_tracked_by` 和 `tracked_by`
- `moving_target_tracking.{target_id}.by_drone.{drone_id}`：按无人机的紧凑跟踪摘要，包含 `first_tracked_at`、`last_tracked_at`、`total_track_events` 和 `recent_periods`
- **注意**：跟踪数据基于时间段并面向近期历史。它不是一个无界的原始事件流。

#### 获取区域覆盖

- 端点：`GET /sessions/{session_id}/area-coverage`
- 说明：返回区域覆盖跟踪以及每个目标的汇总视图。
- 响应：
- `area_coverage`：`target_id` 到覆盖数据的映射 `{area_type, total_area, covered_area, coverage_percentage, covered_points}`。
- `summary`：汇总信息，包含 `total_targets_tracked`、`average_coverage`、`fully_covered_targets`、`coverage_by_target`（带有 `num_covered_points`）。

示例：
```bash
curl -X GET "http://localhost:8000/sessions/session-123e4567/area-coverage"
```

#### 获取任务进度

- 端点：`GET /sessions/{session_id}/task-progress`
- 说明：根据会话的任务类型返回任务完成进度。不同任务类型的进度计算方式各异：
- **area_search** / **area_assignment_and_patrol**：无人机已探索区域的百分比（≥90% 时完成）
- **target_assignment**：在任务半径内至少访问过一次的目标百分比（100% 时完成）
- **target_tracking**：当前跟踪的目标百分比。对于移动目标，“当前跟踪”由后端根据跟踪事件的新鲜度窗口得出（当所有目标都至少被跟踪过一次时完成）
- **others**：无进度跟踪
- 响应：
- `task_type`：任务类型（例如 "area_search"、"target_assignment"、"target_tracking"、"others"）
- `progress_percentage`：任务完成百分比的整数（0-100）
- `is_completed`：布尔值，指示任务是否完成
- `status_message`：人类可读的状态（"待完成任务" 或 "任务已完成"）
- `details`：有关进度的任务特定详细信息

示例：
```bash
curl -X GET "http://localhost:8000/sessions/session-123e4567/task-progress"
```

area_search 任务的响应示例：
```json
{
  "task_type": "area_search",
  "progress_percentage": 45,
  "is_completed": false,
  "status_message": "Task to be Done",
  "details": {
    "total_targets": 2,
    "average_coverage": 45.5,
    "coverage_by_target": {
      "target-abc": 50.0,
      "target-def": 41.0
    }
  }
}
```

target_assignment 任务的响应示例：
```json
{
  "task_type": "target_assignment",
  "progress_percentage": 75,
  "is_completed": false,
  "status_message": "Task to be Done",
  "details": {
    "total_targets": 4,
    "visited_targets": 3,
    "unvisited_targets": 1
  }
}
```

target_tracking 任务的响应示例：
```json
{
  "task_type": "target_tracking",
  "progress_percentage": 50,
  "is_completed": true,
  "status_message": "Task Finished",
  "details": {
    "total_targets": 4,
    "currently_tracked": 2,
    "ever_tracked": 4,
    "currently_tracked_ids": ["target-abc", "target-def"],
    "ever_tracked_ids": ["target-abc", "target-def", "target-ghi", "target-jkl"]
  }
}
```

移动目标跟踪语义：
- `reach`：无人机在任务半径内到达目标时记录的历史事件
- `tracking`：基于新鲜度的移动目标状态
- 默认移动目标跟踪新鲜度窗口：`10.0` 秒
- UI 和 API 消费者应使用目标响应中的 `tracking_status`，而不是从原始 `target_reaches` 推断移动目标的新鲜度

## 任务管理 API

任务管理 API 允许您在会话中创建、管理和跟踪任务。任务代表无人机/客户端在会话期间应完成的特定目标或活动，例如侦察任务、区域搜索、目标跟踪或其他任务目标。

### 概述

任务关联到特定会话，并包含：
- **标识**：唯一 ID、名称
- **详细信息**：内容/指令、描述
- **元数据**：创建者、时间戳、完成状态
- **集成**：相关 API 端点、执行检查端点以及所需的无人机命令

任务可以标记为已完成或待处理，允许客户端跟踪任务进度和完成状态。

#### 相关 API 结构

`related_apis` 字段包含与完成任务相关的 API 端点对象数组。每个对象包含：

- **endpoint**：API 端点路径（例如 `/drones/{id}/command/move_to`）
- **parameters**：描述此端点所需参数的字典
- 键：参数名称
- 值：参数的描述或示例值

**示例：**
```json
{
  "endpoint": "/drones/{id}/command/move_to",
  "parameters": {
    "x": "X coordinate in meters",
    "y": "Y coordinate in meters",
    "z": "Z coordinate (altitude) in meters"
  }
}
```

此结构为客户端提供了清晰的指引，说明应使用哪些 API 以及完成每项任务所需的参数。

#### 执行检查 API 结构

`execution_check_apis` 字段是一个**逻辑树**，描述如何使用 `/check` 端点验证执行情况。

- **logic**：逻辑运算符（默认为 `and`，还有 `or`、`not`）
- **checks**：子节点数组
- **叶节点**包含：
- **endpoint**：`/check/...` 端点路径
- **parameters**：调用该端点的参数字典
- **expect**（可选，默认值：true）：期望从检查端点返回的布尔值 `result`
- 任务检查请求可能包含 `since_timestamp`；服务器会将其转发给兼容的叶节点 `/check` 端点，这些端点接受 `since_timestamp`，除非叶节点已设置 `parameters.since_timestamp`。

### 获取会话中的所有任务

**端点：** `GET /sessions/{session_id}/tasks`

**描述：** 检索特定会话中的所有任务。

**身份验证：** 需要 USER 角色（SYSTEM 和 ADMIN 继承此权限）

**路径参数：**

| 名称 | 类型 | 是否必需 | 描述 |
|------|------|----------|-------------|
| session_id | string | 是 | 会话 ID |

**响应：** 任务对象数组

**示例请求：**
```bash
curl -X GET http://localhost:8000/sessions/session-123/tasks
```

**示例响应：**
```json
[
  {
    "id": "task-abc123",
    "name": "area-search-alpha",
    "content": "Conduct a systematic search of Area Alpha (100x100m grid starting at coordinates 0,0) to identify and catalog all targets within the designated zone.",
    "content_aliases": ["search alpha", "scan zone 1"],
    "description": "Systematic area search mission",
    "creator": "system",
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
    "commands": ["take_off", "move_to", "take_photo", "land"],
    "is_done": false,
    "is_passed": false,
    "created_at": 1620000000.0,
    "last_updated": 1620000000.0
  },
  {
    "id": "task-def456",
    "name": "battery-check",
    "content": "Continuously monitor all drone battery levels and ensure they return to charging stations before reaching 20% battery.",
    "content_aliases": [],
    "description": "Battery management task",
    "creator": "admin",
    "difficulty": "easy",
    "related_apis": [
      {
        "endpoint": "/drones",
        "parameters": {}
      },
      {
        "endpoint": "/targets/type/waypoint",
        "parameters": {}
      }
    ],
    "commands": ["return_home", "charge"],
    "is_done": true,
    "is_passed": true,
    "created_at": 1620000100.0,
    "last_updated": 1620000500.0
  }
]
```

### 创建新任务

**端点：** `POST /sessions/{session_id}/tasks`

**描述：** 在会话中创建新任务。

**身份验证：** 需要 SYSTEM 或 ADMIN 角色

**路径参数：**

| 名称 | 类型 | 是否必需 | 描述 |
|------|------|----------|-------------|
| session_id | string | 是 | 会话 ID |

**请求体参数：**

| 名称 | 类型 | 是否必需 | 描述 |
|------|------|----------|-------------|
| name | string | 是 | 任务的简短名称/标识符 |
| content | string | 否 | 详细内容/指令（默认值：""） |
| content_aliases | 字符串数组 | 否 | 内容的别名或替代名称列表（默认值：[]） |
| description | string | 否 | 简短描述（默认值：""） |
| creator | string | 否 | 创建任务的用户名；如果省略，则默认为调用者的角色 |
| originated_from | string | 否 | 发起任务的主体（默认值为 `creator`） |
| difficulty | string | 否 | 难度级别："easy"、"medium" 或 "hard"（默认值："medium"） |
| related_apis | 对象数组 | 否 | 包含 "endpoint" 和 "parameters" 字段的 API 端点对象列表（默认值：[]） |
| execution_check_apis | 对象 | 否 | 描述 `/check` 验证的逻辑树：包含 `logic`（`and`/`or`/`not`）和 `checks` 数组；叶节点包含 `endpoint`、`parameters` 和可选的 `expect` 布尔值（默认为 `true`） |
| commands | 数组 | 否 | 任务的无人机命令列表（默认值：[]） |

如果未提供 `creator`，服务器会将调用者的角色记录为创建者。

**响应：** 已创建的任务对象

**示例请求：**
```bash
curl -X POST http://localhost:8000/sessions/session-123/tasks \
  -H "Content-Type: application/json" \
  -H "X-API-Key: <SYSTEM_API_KEY>" \
  -d '{
    "name": "target-tracking-mission",
    "content": "Maintain visual contact with Target Bravo as it moves through the patrol zone. Document position every 30 seconds.",
    "content_aliases": ["track bravo", "follow bravo"],
    "description": "Track and document Target Bravo movement",
    "creator": "mission-lead",
    "difficulty": "hard",
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
                      }          ]
        }
      ]
    },
    "commands": ["take_off", "move_to", "hover", "take_photo"]
  }'
```

**示例响应：**
```json
{
  "id": "task-ghi789",
  "name": "target-tracking-mission",
  "content": "Maintain visual contact with Target Bravo as it moves through the patrol zone. Document position every 30 seconds.",
  "content_aliases": ["track bravo", "follow bravo"],
  "description": "Track and document Target Bravo movement",
  "creator": "mission-lead",
  "originated_from": "mission-lead",
  "difficulty": "hard",
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
    "checks": []
  },
  "commands": ["take_off", "move_to", "hover", "take_photo"],
  "is_done": false,
  "is_passed": false,
  "created_at": 1620001000.0,
  "last_updated": 1620001000.0
}
```

### 获取特定任务

**端点：** `GET /sessions/{session_id}/tasks/{task_id}`

**描述：** 检索特定任务的详细信息。

**身份验证：** 需要 SYSTEM 角色（ADMIN 继承此权限）

**路径参数：**

| 名称 | 类型 | 是否必需 | 描述 |
|------|------|----------|-------------|
| session_id | string | 是 | 会话 ID |
| task_id | string | 是 | 任务 ID |

**响应：** 任务对象

**示例请求：**
```bash
curl -X GET http://localhost:8000/sessions/session-123/tasks/task-abc123
```

**示例响应：**
```json
{
  "id": "task-abc123",
  "name": "area-search-alpha",
  "content": "Conduct a systematic search of Area Alpha...",
  "content_aliases": ["search alpha", "scan zone 1"],
  "description": "Systematic area search mission",
  "creator": "system",
  "originated_from": "system",
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
  "commands": ["take_off", "move_to", "take_photo", "land"],
  "is_done": false,
  "is_passed": false,
  "created_at": 1620000000.0,
  "last_updated": 1620000000.0
}
```

### 更新任务

**端点：** `PUT /sessions/{session_id}/tasks/{task_id}`

**描述：** 更新任务的属性。所有字段均为可选。

**身份验证：** 需要 SYSTEM 或 ADMIN 角色

**路径参数：**

| 名称 | 类型 | 是否必需 | 描述 |
|------|------|----------|-------------|
| session_id | string | 是 | 会话 ID |
| task_id | string | 是 | 任务 ID |

**请求体参数（均为可选）：**

| 名称 | 类型 | 描述 |
|------|------|-------------|
| name | string | 任务的简短名称 |
| content | string | 详细内容/指令 |
| content_aliases | 字符串数组 | 内容的别名或替代名称列表 |
| description | string | 简短描述 |
| related_apis | 对象数组 | 包含 "endpoint" 和 "parameters" 字段的 API 端点对象列表 |
| commands | 数组 | 无人机命令列表 |
| is_done | boolean | 任务完成状态 |

**注意：** `is_passed` 由服务器管理，无法通过此端点设置。

**响应：** 更新后的任务对象

**示例请求：**
```bash
curl -X PUT http://localhost:8000/sessions/session-123/tasks/task-abc123 \
  -H "Content-Type: application/json" \
  -H "X-API-Key: <SYSTEM_API_KEY>" \
  -d '{
    "description": "Updated: Systematic area search with photo documentation",
    "difficulty": "hard",
    "is_done": true
  }'
```

**示例响应：**
```json
{
  "id": "task-abc123",
  "name": "area-search-alpha",
  "content": "Conduct a systematic search of Area Alpha...",
  "content_aliases": [],
  "description": "Updated: Systematic area search with photo documentation",
  "creator": "system",
  "difficulty": "hard",
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
  "commands": ["take_off", "move_to", "take_photo", "land"],
  "is_done": true,
  "is_passed": true,
  "created_at": 1620000000.0,
  "last_updated": 1620002000.0
}
```

### 删除任务

**端点：** `DELETE /sessions/{session_id}/tasks/{task_id}`

**描述：** 从会话中删除任务。

**身份验证：** 需要 SYSTEM 或 ADMIN 角色

**路径参数：**

| 名称 | 类型 | 必需 | 描述 |
|------|------|----------|-------------|
| session_id | string | Yes | 会话的ID |
| task_id | string | Yes | 任务的ID |

**响应：** 成功时返回204无内容

**示例请求：**
```bash
curl -X DELETE http://localhost:8000/sessions/session-123/tasks/task-abc123 \
  -H "X-API-Key: <SYSTEM_API_KEY>"
```

### 将任务标记为完成（特定会话）

**端点：** `POST /sessions/{session_id}/tasks/{task_id}/mark-done`

**描述：** 将任务标记为已完成。

**认证：** 需要SYSTEM角色（ADMIN继承）

**路径参数：**

| 名称 | 类型 | 必需 | 描述 |
|------|------|----------|-------------|
| session_id | string | Yes | 会话的ID |
| task_id | string | Yes | 任务的ID |

**响应：** 更新后的任务对象，且`is_done: true`

**示例请求：**
```bash
curl -X POST http://localhost:8000/sessions/session-123/tasks/task-abc123/mark-done
```

**示例响应：**
```json
{
  "id": "task-abc123",
  "name": "area-search-alpha",
  "difficulty": "medium",
  "is_done": true,
  "last_updated": 1620003000.0,
  ...
}
```

### 将任务标记为待处理（特定会话）

**端点：** `POST /sessions/{session_id}/tasks/{task_id}/mark-pending`

**描述：** 将任务标记为待处理（未完成）。

**认证：** 需要SYSTEM角色（ADMIN继承）

**路径参数：**

| 名称 | 类型 | 必需 | 描述 |
|------|------|----------|-------------|
| session_id | string | Yes | 会话的ID |
| task_id | string | Yes | 任务的ID |

**响应：** 更新后的任务对象，且`is_done: false`

**示例请求：**
```bash
curl -X POST http://localhost:8000/sessions/session-123/tasks/task-abc123/mark-pending
```

### 将任务标记为完成（当前会话）

**端点：** `POST /sessions/current/tasks/{task_id}/mark-done`

**描述：** 将当前会话中的任务标记为已完成。

**认证：** 需要AGENT角色（USER、SYSTEM和ADMIN继承）

**路径参数：**

| 名称 | 类型 | 必需 | 描述 |
|------|------|----------|-------------|
| task_id | string | Yes | 任务的ID |

**响应：** 更新后的任务对象，且`is_done: true`

**示例请求：**
```bash
curl -X POST http://localhost:8000/sessions/current/tasks/task-abc123/mark-done
```

### 将任务标记为待处理（当前会话）

**端点：** `POST /sessions/current/tasks/{task_id}/mark-pending`

**描述：** 将当前会话中的任务标记为待处理（未完成）。

**认证：** 需要AGENT角色（USER、SYSTEM和ADMIN继承）

**路径参数：**

| 名称 | 类型 | 必需 | 描述 |
|------|------|----------|-------------|
| task_id | string | Yes | 任务的ID |

**响应：** 更新后的任务对象，且`is_done: false`

**示例请求：**
```bash
curl -X POST http://localhost:8000/sessions/current/tasks/task-abc123/mark-pending
```

### 交换任务

**端点：** `POST /sessions/{session_id}/tasks/swap`

**描述：** 交换会话中两个任务的顺序。通过交换位置重新排列任务。

**认证：** 需要SYSTEM或ADMIN角色

**路径参数：**

| 名称 | 类型 | 必需 | 描述 |
|------|------|----------|-------------|
| session_id | string | Yes | 包含任务的会话的ID |

**请求正文：**
```json
{
  "task_id_1": "task-abc123",
  "task_id_2": "task-def456"
}
```

**响应：** 会话中所有任务按新顺序排列的数组

**示例请求：**
```bash
curl -X POST http://localhost:8000/sessions/session-123/tasks/swap \
  -H "Content-Type: application/json" \
  -d '{
    "task_id_1": "task-abc123",
    "task_id_2": "task-def456"
  }'
```

**示例响应（200 OK）：**
```json
[
  {
    "id": "task-def456",
    "name": "area-patrol-bravo",
    "content": "Patrol area bravo and monitor for activity",
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
    "content": "Search area alpha for targets",
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

**错误响应：**
- `404 Not Found`：会话未找到，或一个/两个任务未找到

### 获取当前会话任务

**端点：** `GET /sessions/current/tasks`

**描述：** 从当前活动会话中获取所有任务。

**认证：** 需要AGENT角色（USER、SYSTEM和ADMIN继承）

**响应：** 任务对象数组

**示例请求：**
```bash
curl -X GET http://localhost:8000/sessions/current/tasks
```

### 从当前会话获取下一个待处理任务

**端点：** `GET /sessions/current/tasks/next`

**描述：** 从当前活动会话中获取下一个待处理（未完成）的任务。

**认证：** 需要AGENT角色（USER、SYSTEM和ADMIN继承）

**响应：** 任务对象

**示例请求：**
```bash
curl -X GET http://localhost:8000/sessions/current/tasks/next
```

**错误响应：**
- `404 Not Found`：未找到当前会话
- `404 Not Found`：未找到待处理任务

### 从当前会话获取特定任务

**端点：** `GET /sessions/current/tasks/{task_id}`

**描述：** 从当前活动会话中获取特定任务。

**认证：** 需要AGENT角色（USER、SYSTEM和ADMIN继承）

**路径参数：**

| 名称 | 类型 | 必需 | 描述 |
|------|------|----------|-------------|
| task_id | string | Yes | 任务的ID |

**响应：** 任务对象

**示例请求：**
```bash
curl -X GET http://localhost:8000/sessions/current/tasks/task-abc123
```

### 检查当前会话中的任务

**端点：** `GET /sessions/current/tasks/{task_id}/check`

**描述：** 评估任务的`execution_check_apis`，并在检查通过时设置`is_passed: true`。可选的`since_timestamp`将兼容的历史记录检查范围限定在该时间戳或之后的事件上。

**认证：** 需要AGENT角色（USER、SYSTEM和ADMIN继承）

**路径参数：**

| 名称 | 类型 | 必需 | 描述 |
|------|------|----------|-------------|
| task_id | string | Yes | 任务的ID |

**查询参数：**

| 名称 | 类型 | 必需 | 描述 |
|------|------|----------|-------------|
| since_timestamp | float | 否 | 传递到兼容的`/check`子端点的默认时间戳过滤器。子级`parameters.since_timestamp`优先级更高。 |

**Response:** 包含`result`和`task`的对象。对于SYSTEM/ADMIN，包含带有完整评估输出的`details`。

**示例请求：**
```bash
curl -X GET http://localhost:8000/sessions/current/tasks/task-abc123/check
```

**示例响应：**
```json
{
  "result": true,
  "task": {
    "id": "task-abc123",
    "name": "area-search-alpha",
    "is_done": false,
    "is_passed": true
  }
}
```

### 任务管理工作流示例

以下是一个完整的工作流，演示了任务的创建、分配与完成：

```python
import requests

API_BASE = "http://localhost:8000"
SYSTEM_KEY = "<SYSTEM_API_KEY>"
HEADERS = {"X-API-Key": SYSTEM_KEY, "Content-Type": "application/json"}

# 1. Get current session ID
response = requests.get(f"{API_BASE}/sessions/current")
session_id = response.json()["id"]
print(f"Current session: {session_id}")

# 2. Create a task for area search
task_data = {
    "name": "zone-1-search-rescue",
    "content": "Systematically search Zone 1 (coordinates 0,0 to 100,100) for survivors. Take photos of any findings.",
    "description": "Search and rescue operation - Zone 1",
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
    "commands": ["take_off", "move_to", "hover", "take_photo", "land"]
}

response = requests.post(
    f"{API_BASE}/sessions/{session_id}/tasks",
    headers=HEADERS,
    json=task_data
)
task = response.json()
task_id = task["id"]
print(f"Created task: {task_id}")

# 3. Client executes the mission commands
drone_id = "drone-001"

# Take off
requests.post(f"{API_BASE}/drones/{drone_id}/command/take_off?altitude=15")

# Move to search area and take photos
search_points = [
    {"x": 25, "y": 25, "z": 15},
    {"x": 75, "y": 25, "z": 15},
    {"x": 75, "y": 75, "z": 15},
    {"x": 25, "y": 75, "z": 15}
]

for point in search_points:
    requests.post(
        f"{API_BASE}/drones/{drone_id}/command/move_to",
        json={"command": "move_to", "parameters": point}
    )
    requests.post(f"{API_BASE}/drones/{drone_id}/command/take_photo")

# Land
requests.post(f"{API_BASE}/drones/{drone_id}/command/land")

# 4. Mark task as completed
response = requests.post(
    f"{API_BASE}/sessions/{session_id}/tasks/{task_id}/mark-done"
)
print(f"Task completed: {response.json()['is_done']}")
print(f"Task passed: {response.json().get('is_passed')}")

# 5. Get all tasks to see completion status
response = requests.get(f"{API_BASE}/sessions/{session_id}/tasks", headers=HEADERS)
tasks = response.json()
print(f"Total tasks: {len(tasks)}")
print(f"Completed tasks: {sum(1 for t in tasks if t['is_done'])}")
print(f"Passed tasks: {sum(1 for t in tasks if t.get('is_passed'))}")
```

## 无人机 API

### 获取所有无人机

**端点：** `GET /drones`

**描述：** 获取系统中所有已注册无人机的列表。

**参数：** 无

**响应：** 无人机对象数组

**示例请求：**
```bash
curl -X GET http://localhost:8000/drones
```

**示例响应：**
```json
[
  {
    "id": "550e8400-e29b-41d4-a716-446655440000",
    "name": "Scout-1",
    "model": "Model-D4",
    "status": "idle",
    "position": {"x": 0.0, "y": 0.0, "z": 0.0},
    "heading": 0.0,
    "speed": 0.0,
    "perceived_radius": 100.0,
    "task_radius": 10.0,
    "home_position": {"x": 0.0, "y": 0.0, "z": 0.0},
    "created_at": 1704067200.0,
    "last_updated": 1704067350.5
  }
]
```

### 注册新无人机

**端点：** `POST /drones`

**描述：** 在系统中注册一架新无人机。

**参数：**

| 参数名 | 类型 | 必填 | 描述 |
|------|------|----------|-------------|
| name | string | 是 | 无人机名称 |
| model | string | 是 | 无人机型号 |
| max_speed | float | 是 | 最大速度 (米/秒) |
| max_altitude | float | 是 | 最大高度 (米) |
| battery_capacity | float | 是 | 电池容量 (毫安时) |
| position | object | 否 | 包含 x, y, z 坐标的初始位置 (默认: {x: 0, y: 0, z: 0}) |
| heading | float | 否 | 初始航向角 (度) (默认: 0.0) |
| speed | float | 否 | 初始速度 (米/秒) (默认: 0.0) |
| battery_level | float | 否 | 初始电池电量百分比 (默认: 100.0) |
| battery_volume | float | 否 | 初始电池电量 (毫安时) (若提供，则优先于 battery_level) |
| status | string | 否 | 初始状态 (默认: 根据高度自动确定) |
| home_position | object | 否 | 包含 x, y, z 坐标的家位置 (若未指定，则默认为初始位置) |
| perceived_radius | float | 否 | 感知半径 (米) (默认: 100.0) |
| task_radius | float | 否 | 任务半径 (米) (默认: 10.0) |

**响应：** 新创建的无人机对象

**示例请求：**
```bash
curl -X POST http://localhost:8000/drones \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Scout-1",
    "model": "Model-D4",
    "max_speed": 20.0,
    "max_altitude": 120.0,
    "battery_capacity": 5000.0,
    "position": {"x": 100.0, "y": 100.0, "z": 0.0},
    "heading": 45.0,
    "speed": 0.0,
    "battery_volume": 4000.0,
    "status": "idle",
    "home_position": {"x": 0.0, "y": 0.0, "z": 0.0},
    "perceived_radius": 100.0,
    "task_radius": 10.0
  }'
```

**示例响应：**
```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "name": "Scout-1",
  "model": "Model-D4",
  "status": "idle",
  "position": {"x": 100.0, "y": 100.0, "z": 0.0},
  "heading": 45.0,
  "speed": 0.0,
  "perceived_radius": 100.0,
  "task_radius": 10.0,
  "battery_level": 100.0,
  "battery_volume": 5000.0,
  "battery_capacity": 5000.0,
  "max_speed": 20.0,
  "max_altitude": 120.0,
  "home_position": {"x": 100.0, "y": 100.0, "z": 0.0},
  "created_at": 1620000000.0,
  "last_updated": 1620000000.0
}
```

### 获取特定无人机

**端点：** `GET /drones/{drone_id}`

**描述：** 获取特定无人机的信息。

**参数：**

| 参数名 | 类型 | 必填 | 描述 |
|------|------|----------|-------------|
| drone_id | string | 是 | 无人机 ID (在 URL 路径中) |

**响应：** 无人机对象

**示例请求：**
```bash
curl -X GET http://localhost:8000/drones/550e8400-e29b-41d4-a716-446655440000
```

**示例响应：**
```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "name": "Scout-1",
  "model": "Model-D4",
  "status": "idle",
  "position": {"x": 0.0, "y": 0.0, "z": 0.0},
  "heading": 0.0,
  "speed": 0.0,
  "perceived_radius": 100.0,
  "task_radius": 10.0,
  "home_position": {"x": 0.0, "y": 0.0, "z": 0.0},
  "created_at": 1704067200.0,
  "last_updated": 1704067350.5
}
```

### 更新无人机属性

**端点：** `PUT /drones/{drone_id}`

**描述：** 更新无人机的属性，包括元数据、性能规格、状态属性、电池电量、位置和家位置。所有字段均为可选 — 仅更新提供的字段。

**需要身份验证：** SYSTEM 角色

**参数：**

| 参数名 | 类型 | 必填 | 描述 |
|------|------|----------|-------------|
| drone_id | string | 是 | 无人机 ID (在 URL 路径中) |

**请求体字段 (全部可选)：**

| 字段 | 类型 | 描述 |
|-------|------|-------------|
| name | string | 无人机名称 |
| model | string | 无人机型号 |
| max_speed | float | 最大速度 (米/秒) (必须 > 0) |
| max_altitude | float | 最大高度 (米) (必须 > 0) |
| battery_capacity | float | 电池容量 (毫安时) (必须 > 0) |
| perceived_radius | float | 感知半径 (米) (必须 > 0) |
| task_radius | float | 任务半径 (米) (必须 > 0) |
| status | string | 当前状态 (idle, ready, flying, hovering 等) |
| position | object | 当前位置 {x, y, z} - 支持部分更新 |
| heading | float | 航向角 (度) (0-359) |
| speed | float | 当前速度 (米/秒) (必须 ≥ 0) |
| battery_level | float | 电池电量百分比 (0-100) |
| battery_volume | float | 电池电量 (毫安时) (必须 ≥ 0) |
| home_position | object | 家位置 {x, y, z} - 支持部分更新 |

**响应：** 更新后的无人机对象

**示例请求 - 更新元数据：**
```bash
curl -X PUT http://localhost:8000/drones/550e8400-e29b-41d4-a716-446655440000 \
  -H "Content-Type: application/json" \
  -H "X-API-Key: <SYSTEM_API_KEY>" \
  -d '{
    "name": "Scout-1 Enhanced",
    "model": "Model-D5",
    "max_speed": 25.0,
    "perceived_radius": 125.0
  }'
```

**示例请求 - 更新状态：**
```bash
curl -X PUT http://localhost:8000/drones/550e8400-e29b-41d4-a716-446655440000 \
  -H "Content-Type: application/json" \
  -H "X-API-Key: <SYSTEM_API_KEY>" \
  -d '{
    "status": "hovering",
    "heading": 90.0,
    "speed": 5.0,
    "battery_level": 85.5
  }'
```

**示例请求 - 部分位置更新 (仅高度)：**
```bash
curl -X PUT http://localhost:8000/drones/550e8400-e29b-41d4-a716-446655440000 \
  -H "Content-Type: application/json" \
  -H "X-API-Key: <SYSTEM_API_KEY>" \
  -d '{
    "position": {"z": 50.0}
  }'
```

**示例请求 - 综合更新：**
```bash
curl -X PUT http://localhost:8000/drones/550e8400-e29b-41d4-a716-446655440000 \
  -H "Content-Type: application/json" \
  -H "X-API-Key: <SYSTEM_API_KEY>" \
  -d '{
    "name": "Advanced Scout Alpha",
    "status": "flying",
    "position": {"x": 100.0, "y": 200.0, "z": 50.0},
    "heading": 45.0,
    "speed": 15.0,
    "battery_level": 90.0
  }'
```

**示例响应：**
```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "name": "Advanced Scout Alpha",
  "model": "Model-D5",
  "status": "flying",
  "position": {"x": 100.0, "y": 200.0, "z": 50.0},
  "heading": 45.0,
  "speed": 15.0,
    "perceived_radius": 120.0,
    "task_radius": 15.0,
    "home_position": {"x": 0.0, "y": 0.0, "z": 0.0},
    "created_at": 1704067200.0,
    "last_updated": 1704067500.0
  }
```

**注意：**
- 所有字段均为可选 — 仅发送您想要更新的字段
- 位置和家位置支持部分更新 (例如，仅更新 z 坐标)
- 当更新 battery_level 时，battery_volume 会自动重新计算
- 当更新 battery_capacity 时，battery_volume 会根据当前的 battery_level 重新计算
- 需要 SYSTEM 角色身份验证

### 更新无人机位置

**端点：** `PUT /drones/{drone_id}/position`

**描述：** 直接更新无人机的位置。这是一个管理功能，设置位置而不模拟移动。无人机的状态将根据高度自动更新。

**需要身份验证：** SYSTEM 角色

**参数：**

| 参数名 | 类型 | 必填 | 描述 |
|------|------|----------|-------------|
| drone_id | string | 是 | 无人机 ID (在 URL 路径中) |
| x | float | 是 | X 坐标 (米) |
| y | float | 是 | Y 坐标 (米) |
| z | float | 是 | Z 坐标 (高度) (米) |

**请求体：**
```json
{
  "x": 100.0,
  "y": 200.0,
  "z": 50.0
}
```

**响应：** 更新后的无人机对象

**请求示例：**
```bash
curl -X PUT http://localhost:8000/drones/550e8400-e29b-41d4-a716-446655440000/position \
  -H "Content-Type: application/json" \
  -H "X-API-Key: <SYSTEM_API_KEY>" \
  -d '{
    "x": 100.0,
    "y": 200.0,
    "z": 50.0
  }'
```

**响应示例：**
```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "name": "Scout-1",
  "model": "Model-D4",
  "status": "hovering",
  "position": {"x": 100.0, "y": 200.0, "z": 50.0},
  "heading": 0.0,
  "speed": 0.0,
  "perceived_radius": 100.0,
  "task_radius": 10.0,
  "battery_level": 100.0,
  "battery_volume": 5000.0,
  "battery_capacity": 5000.0,
  "max_speed": 20.0,
  "max_altitude": 120.0,
  "home_position": {"x": 0.0, "y": 0.0, "z": 0.0},
  "created_at": 1620000000.0,
  "last_updated": 1620000100.0
}
```

**自动状态更新：**
- 如果 z > 0 且无人机状态为 IDLE/READY → 状态变为 HOVERING
- 如果 z == 0 且无人机状态为 HOVERING/FLYING/MOVING → 状态变为 IDLE

**注意事项：**
- 此端点需要所有三个坐标（x, y, z）
- 如需部分位置更新（例如仅更改高度），请改用 `PUT /drones/{drone_id}`
- 检查目标位置是否存在障碍物碰撞
- 不消耗电量（管理功能）
- 不模拟移动过程，也不检查路径碰撞

### 删除无人机

**端点：** `DELETE /drones/{drone_id}`

**描述：** 从系统中删除一架无人机。

**参数：**

| 名称 | 类型 | 必需 | 描述 |
|------|------|----------|-------------|
| drone_id | string | 是 | 无人机 ID（在 URL 路径中） |

**响应：** 无内容 (204)

**请求示例：**
```bash
curl -X DELETE http://localhost:8000/drones/550e8400-e29b-41d4-a716-446655440000
```

### 附近实体

提供邻近查询，用于查找无人机附近的实体。使用无人机的 `perceived_radius` 确定搜索区域。

#### 获取聚合的附近实体

**端点：** `GET /drones/{drone_id}/nearby`

**描述：** 使用无人机的感知半径获取其周围的附近无人机、目标和障碍物。

**参数：**

| 名称 | 类型 | 必需 | 描述 |
|------|------|----------|-------------|
| drone_id | string | 是 | 参考无人机 ID（路径） |

**响应：**

```json
{
  "drones": [
    {
      "id": "drone-2",
      "name": "Scout-2",
      "position": {"x": 12.5, "y": -3.2, "z": 5.0},
      "distance": 14.3
    }
  ],
  "targets": [
    {
      "id": "target-1",
      "name": "Waypoint A",
      "position": {"x": 20.0, "y": 10.0, "z": 0.0},
      "distance": 22.4
    }
  ],
  "obstacles": [
    {
      "id": "obstacle-3",
      "name": "Building B",
      "position": {"x": 30.0, "y": 5.0, "z": 0.0},
      "distance": 28.7
    }
  ]
}
```

**请求示例：**
```bash
curl -X GET "http://localhost:8000/drones/{drone_id}/nearby"
```

#### 获取附近的无人机

**端点：** `GET /drones/{drone_id}/nearby/drones`

**描述：** 使用无人机的感知半径获取其周围的附近无人机。

**参数：**

| 名称 | 类型 | 必需 | 描述 |
|------|------|----------|-------------|
| drone_id | string | 是 | 参考无人机 ID（路径） |

**响应：** 附近无人机对象数组

**请求示例：**
```bash
curl -X GET "http://localhost:8000/drones/{drone_id}/nearby/drones"
```

#### 获取附近的目标

**端点：** `GET /drones/{drone_id}/nearby/targets`

**描述：** 使用无人机的感知半径获取其周围的附近目标。

**参数：**

| 名称 | 类型 | 必需 | 描述 |
|------|------|----------|-------------|
| drone_id | string | 是 | 参考无人机 ID（路径） |

**响应：** 附近目标对象数组

**请求示例：**
```bash
curl -X GET "http://localhost:8000/drones/{drone_id}/nearby/targets"
```

#### 获取附近的障碍物

**端点：** `GET /drones/{drone_id}/nearby/obstacles`

**描述：** 使用无人机的感知半径获取其周围的附近障碍物。

**参数：**

| 名称 | 类型 | 必需 | 描述 |
|------|------|----------|-------------|
| drone_id | string | 是 | 参考无人机 ID（路径） |

**响应：** 附近障碍物对象数组

**请求示例：**
```bash
curl -X GET "http://localhost:8000/drones/{drone_id}/nearby/obstacles"
```

## 命令 API

### 向无人机发送命令

**端点：** `POST /drones/{drone_id}/command`

**描述：** 向特定无人机发送命令。

**参数：**

| 名称 | 类型 | 必需 | 描述 |
|------|------|----------|-------------|
| drone_id | string | 是 | 无人机 ID（在 URL 路径中） |
| command | string | 是 | 要发送的命令（参见 DroneCommand 枚举） |
| parameters | object | 否 | 命令特定参数 |

**可用命令：**
- `connect` - 连接无人机
- `disconnect` - 断开与无人机的连接
- `take_off` - 从地面起飞
- `land` - 降落至地面
- `move_to` - 移动到指定位置 (x, y, z)
- `change_altitude` - 仅更改高度（z 坐标）
- `hover` - 原地悬停
- `rotate` - 旋转到特定航向
- `return_home` - 返回起始位置
- `set_home` - 设置起始位置
- `calibrate` - 校准传感器
- `take_photo` - 使用无人机相机拍照
- `send_message` - 向另一架无人机发送消息
- `broadcast` - 向所有附近无人机广播消息

**响应：** 命令响应对象。命令 `status` 值包括 `success`（表示完全完成）、`partial_success`（表示部分完成并改变状态）和 `error`（表示命令未成功执行）。只有 `move_along_path` 会提供额外的路径点反馈字段：`successful_points_count`、`successful_points`、`unsuccessful_points_count` 和 `unsuccessful_points`。

**请求示例：**
```bash
curl -X POST http://localhost:8000/drones/550e8400-e29b-41d4-a716-446655440000/command \
  -H "Content-Type: application/json" \
  -d '{
    "command": "take_off",
    "parameters": {"altitude": 10.0}
  }'
```

**响应示例：**
```json
{
  "command_id": "a1b2c3d4-e5f6-4a5b-8c7d-9e0f1a2b3c4d",
  "drone_id": "550e8400-e29b-41d4-a716-446655440000",
  "command": "take_off",
  "status": "executing",
  "message": "Taking off to altitude 10.0m"
}
```

### 获取无人机命令历史

**端点：** `GET /drones/{drone_id}/commands`

**描述：** 检索特定无人机的命令历史记录。

**参数：**

| 名称 | 类型 | 必需 | 描述 |
|------|------|----------|-------------|
| drone_id | string | 是 | 无人机 ID（在 URL 路径中） |

**响应：** 命令响应对象数组

**请求示例：**
```bash
curl -X GET http://localhost:8000/drones/550e8400-e29b-41d4-a716-446655440000/commands
```

**响应示例：**
```json
[
  {
    "command_id": "a1b2c3d4-e5f6-4a5b-8c7d-9e0f1a2b3c4d",
    "drone_id": "550e8400-e29b-41d4-a716-446655440000",
    "command": "take_off",
    "status": "completed",
    "message": "Took off to altitude 10.0m"
  }
]
```

### 获取命令状态

**端点：** `GET /commands/{command_id}`

**描述：** 检索特定命令的状态。

**参数：**

| 名称 | 类型 | 必需 | 描述 |
|------|------|----------|-------------|
| command_id | string | 是 | 命令 ID（在 URL 路径中） |

**响应：** 命令响应对象

**请求示例：**
```bash
curl -X GET http://localhost:8000/commands/a1b2c3d4-e5f6-4a5b-8c7d-9e0f1a2b3c4d
```

**响应示例：**
```json
{
  "command_id": "a1b2c3d4-e5f6-4a5b-8c7d-9e0f1a2b3c4d",
  "drone_id": "550e8400-e29b-41d4-a716-446655440000",
  "command": "take_off",
  "status": "completed",
  "message": "Took off to altitude 10.0m"
}
```

## 直接命令 API

这些端点提供了一种更直接的方式，用于向无人机发送特定命令，而无需构造命令对象。

### 起飞

**端点：** `POST /drones/{drone_id}/command/take_off`

**描述：** 命令无人机起飞。

**参数：**

| 名称 | 类型 | 必填 | 描述 |
|------|------|----------|-------------|
| drone_id | string | 是 | 无人机ID（在URL路径中） |
| altitude | float | 否 | 目标高度，单位米（默认值：10.0） |

**响应：** 命令响应对象

**示例请求：**
```bash
curl -X POST "http://localhost:8000/drones/550e8400-e29b-41d4-a716-446655440000/command/take_off?altitude=15.0"
```

### 降落

**端点：** `POST /drones/{drone_id}/command/land`

**描述：** 命令无人机降落。

**参数：**

| 名称 | 类型 | 必填 | 描述 |
|------|------|----------|-------------|
| drone_id | string | 是 | 无人机ID（在URL路径中） |

**响应：** 命令响应对象

**示例请求：**
```bash
curl -X POST http://localhost:8000/drones/550e8400-e29b-41d4-a716-446655440000/command/land
```

### 移动到

**端点：** `POST /drones/{drone_id}/command/move_to`

**描述：** 命令无人机移动到指定坐标。

**参数：**

| 名称 | 类型 | 必填 | 描述 |
|------|------|----------|-------------|
| drone_id | string | 是 | 无人机ID（在URL路径中） |
| x | float | 是 | X坐标，单位米 |
| y | float | 是 | Y坐标，单位米 |
| z | float | 是 | Z坐标（高度），单位米 |

**响应：** 命令响应对象

**示例请求：**
```bash
curl -X POST "http://localhost:8000/drones/550e8400-e29b-41d4-a716-446655440000/command/move_to?x=10.0&y=20.0&z=15.0"
```

### 朝特定方向移动

**端点：** `POST /drones/{drone_id}/command/move_towards`

**描述：** 命令无人机朝特定方向移动一定距离。方向可通过三种方法指定：罗盘航向、方向向量或球坐标（方位角/仰角）。如果未指定方向，无人机将沿其当前航向移动。

**参数：**

| 名称 | 类型 | 必填 | 描述 |
|------|------|----------|-------------|
| drone_id | string | 是 | 无人机ID（在URL路径中） |
| distance | float | 是 | 移动距离，单位米 |
| **方向方法1：罗盘航向** | | | |
| heading | float | 条件性 | 罗盘方位角，单位度（0=北，90=东，180=南，270=西） |
| dz | float | 否 | 可选的垂直分量（高度变化） |
| **方向方法2：方向向量** | | | |
| dx | float | 条件性 | 方向向量的X分量 |
| dy | float | 条件性 | 方向向量的Y分量 |
| dz | float | 否 | 方向向量的Z分量（默认值：0.0） |
| **方向方法3：球坐标** | | | |
| azimuth | float | 条件性 | 水平角，单位度（0=北，顺时针） |
| elevation | float | 否 | 垂直角，单位度（默认值：0.0） |

**注意：**
- 如果未提供任何方向参数（heading、dx/dy或azimuth均为None），无人机将沿其当前航向移动
- 否则，您必须使用上述三种方法中的恰好一种来指定方向
- 无人机的航向会根据移动方向自动更新

**响应：** 命令响应对象

**示例请求：**

```bash
# No direction specified: Move 50m in current heading direction
curl -X POST "http://localhost:8000/drones/drone-123/command/move_towards?distance=50.0"

# Method 1: Move 50 meters towards East (90°)
curl -X POST "http://localhost:8000/drones/drone-123/command/move_towards?distance=50.0&heading=90.0"

# Method 1: Move 30 meters Northeast with 5m altitude gain
curl -X POST "http://localhost:8000/drones/drone-123/command/move_towards?distance=30.0&heading=45.0&dz=5.0"

# Method 2: Move 25 meters using normalized direction vector
curl -X POST "http://localhost:8000/drones/drone-123/command/move_towards?distance=25.0&dx=1.0&dy=1.0&dz=0.5"

# Method 3: Move 40 meters with azimuth 135° and elevation 15°
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

**示例响应：**
```json
{
  "command_id": "cmd-123",
  "drone_id": "drone-123",
  "command": "move_towards",
  "status": "success",
  "message": "Drone moved 50.00m to position (150.00, 100.00, 15.00)"
}
```

**方向方法说明：**

1. **罗盘航向**：当您想沿特定罗盘方向移动时使用
- `heading=0`：北（+Y方向）
- `heading=90`：东（+X方向）
- `heading=180`：南（-Y方向）
- `heading=270`：西（-X方向）
- 可选的`dz`用于高度变化

2. **方向向量**：当您有特定方向向量时使用
- 指定`dx`、`dy`、`dz`分量
- 向量将自动归一化
- 适合相对运动

3. **球坐标**：用于三维方向控制
- `azimuth`：水平角（0-360°）
- `elevation`：垂直角（-90°至+90°）
- 适合复杂的三维机动

### 改变高度

**端点：** `POST /drones/{drone_id}/command/change_altitude`

**描述：** 命令无人机改变其高度。

**参数：**

| 名称 | 类型 | 必填 | 描述 |
|------|------|----------|-------------|
| drone_id | string | 是 | 无人机ID（在URL路径中） |
| altitude | float | 是 | 目标高度，单位米 |

**响应：** 命令响应对象

**示例请求：**
```bash
curl -X POST "http://localhost:8000/drones/550e8400-e29b-41d4-a716-446655440000/command/change_altitude?altitude=25.0"
```

### 悬停

**端点：** `POST /drones/{drone_id}/command/hover`

**描述：** 命令无人机原地悬停。

**参数：**

| 名称 | 类型 | 必填 | 描述 |
|------|------|----------|-------------|
| drone_id | string | 是 | 无人机ID（在URL路径中） |
| duration | float | 否 | 悬停持续时间，单位秒（默认值：无限/直到下一个命令） |

**响应：** 命令响应对象

**示例请求：**
```bash
# Hover indefinitely
curl -X POST http://localhost:8000/drones/550e8400-e29b-41d4-a716-446655440000/command/hover

# Hover for 5 seconds
curl -X POST "http://localhost:8000/drones/550e8400-e29b-41d4-a716-446655440000/command/hover?duration=5.0"
```

### 旋转（改变航向）

**端点：** `POST /drones/{drone_id}/command/rotate`

**描述：** 命令无人机旋转/改变其航向（朝向），而不改变位置。无人机的航向决定了在使用`move_towards`且未指定方向时它将移动的方向。

**参数：**

| 名称 | 类型 | 必需 | 描述 |
|------|------|----------|-------------|
| drone_id | string | 是 | 无人机 ID（位于 URL 路径中）|
| heading | float | 是 | 目标航向角度（0=北，90=东，180=南，270=西）|

**响应：** 命令响应对象

**示例请求：**
```bash
# Rotate to face North
curl -X POST "http://localhost:8000/drones/drone-123/command/rotate?heading=0.0"

# Rotate to face East
curl -X POST "http://localhost:8000/drones/drone-123/command/rotate?heading=90.0"

# Rotate to face Southwest
curl -X POST "http://localhost:8000/drones/drone-123/command/rotate?heading=225.0"

# Using generic command endpoint
curl -X POST http://localhost:8000/drones/drone-123/command \
  -H "Content-Type: application/json" \
  -d '{
    "command": "rotate",
    "parameters": {
      "heading": 180.0
    }
  }'
```

**示例响应：**
```json
{
  "command_id": "cmd-456",
  "drone_id": "drone-123",
  "command": "rotate",
  "status": "success",
  "message": "Drone heading set to 180.0°"
}
```

**使用场景：**
- 在拍摄照片或视频前调整无人机朝向
- 为特定方向的 `move_towards` 命令做好准备
- 将传感器或相机指向特定方向
- 在接近前与航点或目标对齐

### 返航

**端点：** `POST /drones/{drone_id}/command/return_home`

**描述：** 命令无人机返回其起始位置。

**参数：**

| 名称 | 类型 | 必需 | 描述 |
|------|------|----------|-------------|
| drone_id | string | 是 | 无人机 ID（位于 URL 路径中）|

**响应：** 命令响应对象

**示例请求：**
```bash
curl -X POST http://localhost:8000/drones/550e8400-e29b-41d4-a716-446655440000/command/return_home
```

### 设置返航点

**端点：** `POST /drones/{drone_id}/command/set_home`

**描述：** 将当前位置设为无人机的起始位置。

**参数：**

| 名称 | 类型 | 必需 | 描述 |
|------|------|----------|-------------|
| drone_id | string | 是 | 无人机 ID（位于 URL 路径中）|

**响应：** 命令响应对象

**示例请求：**
```bash
curl -X POST http://localhost:8000/drones/550e8400-e29b-41d4-a716-446655440000/command/set_home
```

### 校准

**端点：** `POST /drones/{drone_id}/command/calibrate`

**描述：** 校准无人机的传感器。

**参数：**

| 名称 | 类型 | 必需 | 描述 |
|------|------|----------|-------------|
| drone_id | string | 是 | 无人机 ID（位于 URL 路径中）|

**响应：** 命令响应对象

**示例请求：**
```bash
curl -X POST http://localhost:8000/drones/550e8400-e29b-41d4-a716-446655440000/command/calibrate
```

### 拍照

**端点：** `POST /drones/{drone_id}/command/take_photo`

**描述：** 命令无人机使用其相机拍摄照片。

**参数：**

| 名称 | 类型 | 必需 | 描述 |
|------|------|----------|-------------|
| drone_id | string | 是 | 无人机 ID（位于 URL 路径中）|

**响应：** 命令响应对象

**示例请求：**
```bash
curl -X POST http://localhost:8000/drones/550e8400-e29b-41d4-a716-446655440000/command/take_photo
```

### 发送消息

**端点：** `POST /drones/{drone_id}/command/send_message`

**描述：** 命令无人机向另一架无人机发送消息。

**参数：**

| 名称 | 类型 | 必需 | 描述 |
|------|------|----------|-------------|
| drone_id | string | 是 | 发送方无人机的 ID（位于 URL 路径中）|
| target_drone_id | string | 是 | 目标无人机的 ID |
| message | string | 是 | 消息内容 |

**响应：** 命令响应对象

**示例请求：**
```bash
curl -X POST "http://localhost:8000/drones/550e8400-e29b-41d4-a716-446655440000/command/send_message?target_drone_id=550e8400-e29b-41d4-a716-446655440001&message=Hello%20from%20Scout-1"
```

### 广播消息

**端点：** `POST /drones/{drone_id}/command/broadcast`

**描述：** 命令无人机向附近所有无人机广播消息。

**参数：**

| 名称 | 类型 | 必需 | 描述 |
|------|------|----------|-------------|
| drone_id | string | 是 | 发送方无人机的 ID（位于 URL 路径中）|
| message | string | 是 | 消息内容 |

**响应：** 命令响应对象

**示例请求：**
```bash
curl -X POST "http://localhost:8000/drones/550e8400-e29b-41d4-a716-446655440000/command/broadcast?message=Emergency%20landing%20required"
```

### 沿路径移动

**端点：** `POST /drones/{drone_id}/command/move_along_path`

**描述：** 命令无人机沿由一个或多个航点组成的指定路径移动。单个航点也可接受，行为类似于单步移动。航点可以省略 `z` 坐标；省略的高度将默认为无人机当前的高度。

**参数：**

| 名称 | 类型 | 必需 | 描述 |
|------|------|----------|-------------|
| drone_id | string | 是 | 无人机 ID（位于 URL 路径中）|
| waypoints | array | 是 | 有序的航点坐标 `[{x, y, z}, ...]` 或二维坐标 `[{x, y}, ...]`，至少包含一个航点。缺失 `z` 时使用无人机当前的高度。|
| allow_partial_move | boolean | 否 | 默认为 `false`。设为 `true` 时，无人机将在障碍物阻挡下一个航点/路段之前，或在电量不足以到达下一个航点之前，停在最后一个可到达的航点。|

**请求体：**
```json
{
  "waypoints": [
    {"x": 10.0, "y": 20.0, "z": 15.0},
    {"x": 30.0, "y": 40.0},
    {"x": 50.0, "y": 60.0, "z": 15.0}
  ],
  "allow_partial_move": false
}
```

**响应：** MoveAlongPathCommandResponse 对象。`move_to` 和 `move_along_path` 的电量消耗基于距离，无基础移动成本。当 `allow_partial_move=true` 时，如果在障碍物或电量不足阻止剩余路径之前至少完成了一个航点，命令将返回 `partial_success`；响应消息会说明路径仅部分完成。`success` 表示所有请求的航点均已到达。如果第一个航点无法安全到达或电量不足，命令将返回 `error` 并且无人机不会移动。成功和部分成功的路径响应包含 `successful_points_count`、`successful_points`、`unsuccessful_points_count` 和 `unsuccessful_points`，其中点列表包含规范化的 `(x, y, z)` 三元组；错误响应不填充点反馈值。

大型航点列表通过分批内部覆盖追踪、复用路径计算和轻量级会话状态同步来处理。这提高了命令响应时间，同时保持了相同的请求和响应模式、航点历史记录、目标到达追踪、电量语义以及同步完成行为。

**示例请求：**
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

### 充电

**端点：** `POST /drones/{drone_id}/command/charge`

**描述：** 命令无人机为其电池充电。

**参数：**

| 名称 | 类型 | 必填 | 描述 |
|------|------|----------|-------------|
| drone_id | string | Yes | 无人机的ID（位于URL路径中） |
| charge_amount | float | Yes | 充电百分比量（0-100） |

**响应：** 命令响应对象

**示例请求：**
```bash
curl -X POST "http://localhost:8000/drones/550e8400-e29b-41d4-a716-446655440000/command/charge?charge_amount=25.0"
```

## 电池管理API

### 更新电池电量

**端点：** `POST /drones/{drone_id}/battery`

**描述：** 直接更新无人机电池电量（用于测试目的）。

**参数：**

| 名称 | 类型 | 必填 | 描述 |
|------|------|----------|-------------|
| drone_id | string | Yes | 无人机的ID（位于URL路径中） |
| battery_level | float | Yes | 电池电量百分比（0-100） |

**请求体：**
```json
{
  "battery_level": 75.0
}
```

**响应：** 更新后的无人机对象

**示例请求：**
```bash
curl -X POST http://localhost:8000/drones/550e8400-e29b-41d4-a716-446655440000/battery \
  -H "Content-Type: application/json" \
  -d '{"battery_level": 75.0}'
```

**示例响应：**
```json
{
  "message": "Battery level updated to 75.0%",
  "drone_id": "550e8400-e29b-41d4-a716-446655440000",
  "battery_level": 75.0,
  "status": "idle"
}
```

### 降落所有无人机

**端点：** `POST /drones/land_all`

**认证：** 需要SYSTEM角色（ADMIN继承）

**描述：** 用于立即降落系统中所有无人机的管理命令。此管理命令绕过正常的命令队列，直接将所有无人机降至地面。

**行为：**
- 将所有无人机降落至地面（高度 = 0）
- 将所有无人机的状态更改为IDLE（EMERGENCY状态的无人机除外）
- 不消耗电池
- 非用户命令——此为管理/系统功能
- 将会话历史中的状态变更记录下来

**参数：** 无

**响应：** 包含每架无人机详细信息的摘要对象

**示例请求：**
```bash
curl -X POST http://localhost:8000/drones/land_all \
  -H "X-API-Key: <SYSTEM_API_KEY>"
```

**示例响应：**
```json
{
  "message": "Successfully landed 3 drone(s)",
  "total_drones": 3,
  "drones_landed": 2,
  "drones_already_grounded": 1,
  "details": [
    {
      "drone_id": "drone-001",
      "drone_name": "Alpha",
      "previous_status": "hovering",
      "previous_altitude": 15.0,
      "new_status": "idle",
      "new_altitude": 0.0,
      "action": "landed"
    },
    {
      "drone_id": "drone-002",
      "drone_name": "Beta",
      "previous_status": "flying",
      "previous_altitude": 20.0,
      "new_status": "idle",
      "new_altitude": 0.0,
      "action": "landed"
    },
    {
      "drone_id": "drone-003",
      "drone_name": "Gamma",
      "previous_status": "idle",
      "previous_altitude": 0.0,
      "new_status": "idle",
      "new_altitude": 0.0,
      "action": "already_on_ground"
    }
  ]
}
```

**用例：**
- 所有飞行操作的紧急关闭
- 将仿真重置为地面状态
- 任务结束程序
- 测试与开发场景

**注意：** 处于EMERGENCY状态的无人机将被降落，但保留其EMERGENCY状态。


### 全部无人机充电

**端点：** `POST /drones/charge_all`

**认证：** 需要SYSTEM角色（ADMIN继承）

**描述：** 用于立即将所有无人机电池充满的管理命令。此管理命令绕过正常的命令队列，直接更新每架无人机的电池电量，不论其位置或状态。

**行为：**
- 将所有无人机电池电量设为100%
- 相应更新电池容量
- 不改变位置或状态
- 非用户命令——此为管理/系统功能
- 将会话历史中的状态更新记录下来

**参数：** 无

**响应：** 包含每架无人机详细信息的摘要对象

**示例请求：**
```bash
curl -X POST http://localhost:8000/drones/charge_all \
  -H "X-API-Key: <SYSTEM_API_KEY>"
```

**示例响应：**
```json
{
  "message": "Successfully charged 3 drone(s)",
  "total_drones": 3,
  "drones_charged": 2,
  "drones_already_full": 1,
  "details": [
    {
      "drone_id": "drone-001",
      "drone_name": "Alpha",
      "previous_battery_level": 45.0,
      "previous_battery_volume": 450.0,
      "new_battery_level": 100.0,
      "new_battery_volume": 1000.0,
      "action": "charged"
    },
    {
      "drone_id": "drone-002",
      "drone_name": "Beta",
      "previous_battery_level": 100.0,
      "previous_battery_volume": 1000.0,
      "new_battery_level": 100.0,
      "new_battery_volume": 1000.0,
      "action": "already_full"
    }
  ]
}
```

**用例：**
- 重置整个机队的仿真能量状态
- 使用充满电的电池进行测试
- 在开发中快速从低电量场景中恢复



## 目标API
### 获取所有目标

**端点：** `GET /targets`

**描述：** 检索系统中所有目标的列表。

**参数：** 无

**响应：** 目标对象数组

**示例请求：**
```bash
curl -X GET http://localhost:8000/targets
```

**示例响应：**
```json
[
  {
    "id": "550e8400-e29b-41d4-a716-446655440000",
    "name": "Landing Zone Alpha",
    "type": "fixed",
    "position": {"x": 100.0, "y": 200.0, "z": 0.0},
    "description": "Primary landing zone",
    "velocity": {"x": 0.0, "y": 0.0, "z": 0.0},
    "radius": 5.0,
    "created_at": 1620000000.0,
    "last_updated": 1620000000.0,
    "moving_path": null,
    "current_path_index": null,
    "charge_amount": null
  }
]
```

### 添加新目标

**端点：** `POST /targets`

**描述：** 向系统添加新目标。

**参数：**

| 名称 | 类型 | 必填 | 描述 |
|------|------|----------|-------------|
| name | string | Yes | 目标名称 |
| type | string | Yes | 目标类型（fixed, moving, waypoint, circle, polygon）——注意：fixed类型也可表示兴趣点 |
| position | object | Yes | 位置坐标 {x, y, z} |
| description | string | No | 目标描述（默认: ""） |
| velocity | object | No | 移动目标的速度 {x, y, z}。**优先级1**：若非零，则使用基于速度的移动（忽略 moving_path）。可为一维、二维或三维（默认值：{x: 0, y: 0, z: 0}） |
| radius | float | No | 目标半径/大小，单位米（默认值：1.0） |
| moving_path | array | No | 移动目标的路径点坐标数组 [{x, y, z}, ...]。**优先级2**：仅在速度为零/空时使用。目标沿路径往返移动。连续的重复路径点会被拒绝，路径点/段会进行障碍物校验。 |
| moving_duration | float | No | 时间，单位秒。**速度模式**：反向移动前的时间。**路径模式**：完成单向移动的时间（速度自动计算为 路径长度/时长）。**若为0**：目标静止（默认值：10.0） |
| charge_amount | float | No | 路径点目标的即时充电量（电池百分比） |
| vertices | array | No（多边形必填） | 多边形顶点 [{x, y}, ...]，绝对世界坐标 |

**移动目标的移动优先级系统：**
1. **速度（优先级1）**：如果 `velocity` 包含非零分量且 `moving_duration > 0` → 基于速度的往返移动（忽略 `moving_path`）
2. **路径（优先级2）**：如果 `velocity` 为零/空，并且 `moving_path` 存在且 `moving_duration > 0` → 基于路径的移动，速度自动计算
3. **静止**：如果 `moving_duration == 0` → 目标不移动

**返回的移动目标标准运行时字段：**
- `movement_mode`：值可为 `velocity`、`path` 或 `stationary` 之一
- `last_motion_update`：最近一次运动更新的时间戳
- `tracking_status`：`tracked`、`stale` 或 `never_tracked` 之一
- `last_tracked_at`：最近的后端跟踪时间戳

**兼容性说明：** 现有请求字段保持不变。为保持兼容性，`is_reached` 和 `reached_by` 等旧版响应字段仍会返回，但移动目标的时效性由后端根据跟踪状态派生，而非基于仅 UI 端的超时。

**响应：** 新创建的目标对象

**示例请求（固定目标）：**
```bash
curl -X POST http://localhost:8000/targets \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Landing Zone Alpha",
    "type": "fixed",
    "position": {"x": 100.0, "y": 200.0, "z": 0.0},
    "description": "Primary landing zone",
    "radius": 5.0
  }'
```

**示例请求（移动目标 - 基于路径）：**
```bash
curl -X POST http://localhost:8000/targets \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Patrol Target",
    "type": "moving",
    "position": {"x": 200.0, "y": 200.0, "z": 10.0},
    "description": "Moving patrol target",
    "velocity": {"x": 2.0, "y": 2.0, "z": 0.0},
    "radius": 3.0,
    "moving_path": [
      {"x": 250.0, "y": 200.0, "z": 10.0},
      {"x": 250.0, "y": 250.0, "z": 10.0},
      {"x": 200.0, "y": 250.0, "z": 10.0},
      {"x": 200.0, "y": 200.0, "z": 10.0}
    ]
  }'
```

**示例请求（移动目标 - 基于速度的乒乓运动）：**
```bash
# PRIORITY 1: Velocity-based movement (ignores moving_path even if present)
curl -X POST http://localhost:8000/targets \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Oscillating Target",
    "type": "moving",
    "position": {"x": 300.0, "y": 300.0, "z": 5.0},
    "description": "Target moving back and forth every 10 seconds",
    "velocity": {"x": 3.0, "y": 0.0, "z": 0.0},
    "radius": 2.0,
    "moving_duration": 10.0
  }'
# Result: Moves in X direction at 3 m/s, reverses every 10 seconds
```

**示例请求（移动目标 - 基于路径并自动计算速度）：**
```bash
# PRIORITY 2: Path-based movement (only when velocity is zero/null)
curl -X POST http://localhost:8000/targets \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Patrol Target",
    "type": "moving",
    "position": {"x": 0.0, "y": 0.0, "z": 0.0},
    "description": "Target patrolling a square path",
    "velocity": null,
    "radius": 2.0,
    "moving_path": [
      {"x": 0, "y": 0, "z": 0},
      {"x": 100, "y": 0, "z": 0},
      {"x": 100, "y": 100, "z": 0},
      {"x": 0, "y": 100, "z": 0}
    ],
    "moving_duration": 30.0
  }'
# Result: Path length = 300m. Speed = 300/30 = 10 m/s.
# Completes one-way traverse in 30 seconds, then reverses
```

**示例请求（移动目标 - 静止）：**
```bash
# STATIONARY: moving_duration = 0
curl -X POST http://localhost:8000/targets \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Static Target",
    "type": "moving",
    "position": {"x": 200.0, "y": 200.0, "z": 5.0},
    "description": "Target that does not move",
    "velocity": {"x": 3.0, "y": 0.0, "z": 0.0},
    "radius": 2.0,
    "moving_duration": 0.0
  }'
# Result: Target remains stationary at position
```

**示例请求（航点/充电站）：**
```bash
curl -X POST http://localhost:8000/targets \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Charging Station 1",
    "type": "waypoint",
    "position": {"x": 50.0, "y": 50.0, "z": 0.0},
    "description": "Charging station for drones",
    "radius": 10.0,
    "charge_amount": 30.0
  }'
```

**示例请求（圆形目标）：**
```bash
curl -X POST http://localhost:8000/targets \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Circular Survey Area",
    "type": "circle",
    "position": {"x": 260.0, "y": 40.0, "z": 0.0},
    "description": "Geometric circle target",
    "radius": 12.0
  }'
```

**示例请求（多边形目标）：**
```bash
curl -X POST http://localhost:8000/targets \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Polygon Inspection Zone",
    "type": "polygon",
    "position": {"x": 520.0, "y": 220.0, "z": 0.0},
    "description": "Geometric polygon target",
    "vertices": [
      {"x": 500.0, "y": 200.0},
      {"x": 540.0, "y": 200.0},
      {"x": 560.0, "y": 240.0},
      {"x": 520.0, "y": 260.0},
      {"x": 480.0, "y": 240.0}
    ]
  }'
```

**示例响应：**
```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "name": "Landing Zone Alpha",
  "type": "fixed",
  "position": {"x": 100.0, "y": 200.0, "z": 0.0},
  "description": "Primary landing zone",
  "velocity": null,
  "radius": 5.0,
  "created_at": 1620000000.0,
  "last_updated": 1620000000.0,
  "moving_path": null,
  "current_path_index": null,
  "charge_amount": null
}
```

### 获取特定目标

**端点：** `GET /targets/{target_id}`

**描述：** 获取特定目标的信息。

**参数：**

| 名称 | 类型 | 必需 | 描述 |
|------|------|----------|-------------|
| target_id | string | 是 | 目标 ID（位于 URL 路径中） |

**响应：** 目标对象

**示例请求：**
```bash
curl -X GET http://localhost:8000/targets/550e8400-e29b-41d4-a716-446655440000
```

**示例响应：**
```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "name": "Landing Zone Alpha",
  "type": "fixed",
  "position": {"x": 100.0, "y": 200.0, "z": 0.0},
  "description": "Primary landing zone",
  "velocity": null,
  "radius": 5.0,
  "created_at": 1620000000.0,
  "last_updated": 1620000000.0,
  "moving_path": null,
  "current_path_index": null,
  "charge_amount": null
}
```

### 按类型获取目标

**端点：** `GET /targets/type/{type}`

**描述：** 获取特定类型的所有目标。

**参数：**

| 名称 | 类型 | 必需 | 描述 |
|------|------|----------|-------------|
| type | string | 是 | 要获取的目标类型（位于 URL 路径中） |

**响应：** 目标对象数组

**示例请求：**
```bash
curl -X GET "http://localhost:8000/targets/type/waypoint"
```

**可用的目标类型：**
- `fixed` - 具有特定位置和半径的固定目标（也可用作兴趣点）
- `moving` - 具有速度和可选路径航点的移动目标
- `waypoint` - 用于无人机导航的充电站或航点
- `circle` - 由 `position` 位置的 `radius` 定义的几何圆形目标
- `polygon` - 由 `vertices`（绝对坐标）定义的几何多边形目标

#### 用户界面渲染说明（目标）
- `circle`：填充渲染，带细白轮廓；选中时，使用以目标为中心的小矩形指示器。
- `polygon`：填充渲染，带白色轮廓；选中时，高亮显示多边形边界，并在形状周围扩展边距以提高清晰度。标签渲染在右上边界之外。

## 航点 API

### 检查航点处的无人机

**端点：** `POST /targets/waypoints/{waypoint_id}/check-drone`

**描述：** 检查无人机是否位于航点半径内，并在适用时返回充电信息。

**参数：**

| 名称 | 类型 | 必需 | 描述 |
|------|------|----------|-------------|
| waypoint_id | string | 是 | 航点 ID（位于 URL 路径中） |
| drone_position | object | 是 | 无人机位置坐标 {x, y, z}（位于请求体中） |

**请求体：**
```json
{
  "x": 52.0,
  "y": 48.0,
  "z": 0.0
}
```

**响应：**
```json
{
  "waypoint_id": "sim-waypoint-001",
  "drone_in_range": true,
  "charge_amount": 30.0,
  "drone_position": {"x": 52.0, "y": 48.0, "z": 0.0}
}
```

**示例请求：**
```bash
curl -X POST "http://localhost:8000/targets/waypoints/sim-waypoint-001/check-drone" \
  -H "Content-Type: application/json" \
  -d '{"x": 52.0, "y": 48.0, "z": 0.0}'
```

### 更新目标

**端点：** `PUT /targets/{target_id}`

**描述：** 更新目标的属性。

**参数：**

| 名称 | 类型 | 必需 | 描述 |
|------|------|----------|-------------|
| target_id | string | 是 | 目标 ID（位于 URL 路径中） |
| name | string | 否 | 目标的新名称 |
| position | object | 否 | 新位置坐标 {x, y, z} |
| description | string | 否 | 目标的新描述 |
| velocity | object | 否 | 移动目标的新速度 {x, y, z}。设置为零或空将切换为基于路径的模式 |
| radius | float | 否 | 新的目标半径/大小（米） |
| moving_path | array | 否 | 移动目标的新路径航点 [{x, y, z}, ...]。如果处于路径模式，将重新计算速度。连续的重复航点会被拒绝，并且路径航点/段落会针对障碍物进行验证。 |
| moving_duration | float | 否 | 新的时间长度（秒）。更新会影响路径模式的速度计算 |
| charge_amount | float | 否 | 航点目标的新即时充电量 |

**注意：** 根据优先级规则，更改 `velocity`、`moving_path` 或 `moving_duration` 可能会切换移动模式。更新后的目标响应中包含 `movement_mode`，移动目标还包含 `tracking_status` 和 `last_tracked_at`。

**响应：** 更新后的目标对象

**示例请求：**
```bash
curl -X PUT http://localhost:8000/targets/550e8400-e29b-41d4-a716-446655440000 \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Landing Zone Bravo",
    "description": "Secondary landing zone"
  }'
```

**示例响应：**
```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "name": "Landing Zone Bravo",
  "type": "fixed",
  "position": {"x": 100.0, "y": 200.0, "z": 0.0},
  "description": "Secondary landing zone",
  "velocity": null,
  "radius": 5.0,
  "created_at": 1620000000.0,
  "last_updated": 1620000100.0,
  "moving_path": null,
  "current_path_index": null,
  "charge_amount": null
}
```

### 删除目标

**端点：** `DELETE /targets/{target_id}`

**描述：** 从系统中删除目标。

**参数：**

| 名称 | 类型 | 必需 | 描述 |
|------|------|----------|-------------|
| target_id | string | 是 | 目标 ID（位于 URL 路径中） |

**响应：** 无内容 (204)

**示例请求：**
```bash
curl -X DELETE http://localhost:8000/targets/550e8400-e29b-41d4-a716-446655440000
```

## 环境 API

### 获取所有环境

**端点：** `GET /environments`

**描述：** 获取系统中所有环境的列表。

**参数：** 无

**响应：** 环境对象数组

**示例请求：**
```bash
curl -X GET http://localhost:8000/environments
```

**示例响应：**
```json
[
  {
    "id": "550e8400-e29b-41d4-a716-446655440000",
    "name": "Sunny Day",
    "weather": "clear",
    "temperature": 25.0,
    "humidity": 40.0,
    "pressure": 1013.25,
    "wind_speed": 5.0,
    "wind_direction": "north",
    "visibility": 10000.0,
    "created_at": 1620000000.0,
    "last_updated": 1620000000.0
  }
]
```

### 创建新环境

**端点：** `POST /environments`

**描述：** 在系统中创建新环境。

**参数：**

| 名称 | 类型 | 必需 | 描述 |
|------|------|----------|-------------|
| name | string | Yes | 环境名称 |
| weather | string | Yes | 天气状况 (clear, partly_cloudy, cloudy, rain, heavy_rain, snow, fog, windy, storm) |
| temperature | float | Yes | 摄氏温度 |
| humidity | float | Yes | 湿度百分比 |
| pressure | float | No | 大气压力（百帕），默认：1013.25 |
| wind_speed | float | No | 风速（米/秒），默认：0.0 |
| wind_direction | string | No | 风向（北、东北、东、东南、南、西南、西、西北），默认：北 |
| visibility | float | No | 能见度（米），默认：10000.0 |

**响应:** 新创建的环境对象

**请求示例:**
```bash
curl -X POST http://localhost:8000/environments \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Stormy Weather",
    "weather": "storm",
    "temperature": 15.0,
    "humidity": 80.0,
    "wind_speed": 20.0,
    "wind_direction": "west",
    "visibility": 2000.0
  }'
```

**响应示例:**
```json
{
  "id": "550e8400-e29b-41d4-a716-446655440001",
  "name": "Stormy Weather",
  "weather": "storm",
  "temperature": 15.0,
  "humidity": 80.0,
  "pressure": 1013.25,
  "wind_speed": 20.0,
  "wind_direction": "west",
  "visibility": 2000.0,
  "created_at": 1620000100.0,
  "last_updated": 1620000100.0
}
```

### 获取当前环境

**端点:** `GET /environments/current`

**描述:** 获取当前活跃的环境。

**参数:** 无

**响应:** 环境对象

**请求示例:**
```bash
curl -X GET http://localhost:8000/environments/current
```

**响应示例:**
```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "name": "Sunny Day",
  "weather": "clear",
  "temperature": 25.0,
  "humidity": 40.0,
  "pressure": 1013.25,
  "wind_speed": 5.0,
  "wind_direction": "north",
  "visibility": 10000.0,
  "created_at": 1620000000.0,
  "last_updated": 1620000000.0
}
```

### 设置当前环境

**端点:** `POST /environments/{environment_id}/set-current`

**描述:** 将一个环境设置为当前活跃的环境。

**参数:**

| 名称 | 类型 | 必需 | 描述 |
|------|------|----------|-------------|
| environment_id | string | Yes | 环境ID（在URL路径中） |

**响应:** 被设置为当前环境的环境对象

**请求示例:**
```bash
curl -X POST http://localhost:8000/environments/550e8400-e29b-41d4-a716-446655440001/set-current
```

**响应示例:**
```json
{
  "id": "550e8400-e29b-41d4-a716-446655440001",
  "name": "Stormy Weather",
  "weather": "storm",
  "temperature": 15.0,
  "humidity": 80.0,
  "pressure": 1013.25,
  "wind_speed": 20.0,
  "wind_direction": "west",
  "visibility": 2000.0,
  "created_at": 1620000100.0,
  "last_updated": 1620000100.0
}
```

### 获取特定环境

**端点:** `GET /environments/{environment_id}`

**描述:** 获取特定环境的信息。

**参数:**

| 名称 | 类型 | 必需 | 描述 |
|------|------|----------|-------------|
| environment_id | string | Yes | 环境ID（在URL路径中） |

**响应:** 环境对象

**请求示例:**
```bash
curl -X GET http://localhost:8000/environments/550e8400-e29b-41d4-a716-446655440001
```

**响应示例:**
```json
{
  "id": "550e8400-e29b-41d4-a716-446655440001",
  "name": "Stormy Weather",
  "weather": "storm",
  "temperature": 15.0,
  "humidity": 80.0,
  "pressure": 1013.25,
  "wind_speed": 20.0,
  "wind_direction": "west",
  "visibility": 2000.0,
  "created_at": 1620000100.0,
  "last_updated": 1620000100.0
}
```

### 更新环境

**端点:** `PUT /environments/{environment_id}`

**描述:** 更新环境的属性。

**参数:**

| 名称 | 类型 | 必需 | 描述 |
|------|------|----------|-------------|
| environment_id | string | Yes | 环境ID（在URL路径中） |
| name | string | No | 环境的新名称 |
| weather | string | No | 新的天气状况 |
| temperature | float | No | 新的摄氏温度 |
| humidity | float | No | 新的湿度百分比 |
| pressure | float | No | 新的大气压力（百帕） |
| wind_speed | float | No | 新的风速（米/秒） |
| wind_direction | string | No | 新的风向 |
| visibility | float | No | 新的能见度（米） |

**响应:** 更新后的环境对象

**请求示例:**
```bash
curl -X PUT http://localhost:8000/environments/550e8400-e29b-41d4-a716-446655440001 \
  -H "Content-Type: application/json" \
  -d '{
    "weather": "heavy_rain",
    "wind_speed": 25.0
  }'
```

**响应示例:**
```json
{
  "id": "550e8400-e29b-41d4-a716-446655440001",
  "name": "Stormy Weather",
  "weather": "heavy_rain",
  "temperature": 15.0,
  "humidity": 80.0,
  "pressure": 1013.25,
  "wind_speed": 25.0,
  "wind_direction": "west",
  "visibility": 2000.0,
  "created_at": 1620000100.0,
  "last_updated": 1620000200.0
}
```

### 删除环境

**端点:** `DELETE /environments/{environment_id}`

**描述:** 从系统中删除一个环境。不能删除唯一的环境。

**参数:**

| 名称 | 类型 | 必需 | 描述 |
|------|------|----------|-------------|
| environment_id | string | Yes | 环境ID（在URL路径中） |

**响应:** 无内容 (204)

**请求示例:**
```bash
curl -X DELETE http://localhost:8000/environments/550e8400-e29b-41d4-a716-446655440001
```

## 障碍物 API

### 获取所有障碍物

**端点:** `GET /obstacles`

**描述:** 获取系统中所有障碍物的列表。

**参数:** 无

**响应:** 障碍物对象数组

**请求示例:**
```bash
curl -X GET http://localhost:8000/obstacles
```

**响应示例:**
```json
[
  {
    "id": "550e8400-e29b-41d4-a716-446655440000",
    "name": "Tall Building",
    "type": "polygon",
    "position": {"x": 100.0, "y": 200.0, "z": 0.0},
    "description": "Office building",
    "radius": null,
    "width": null,
    "length": null,
    "vertices": [
      {"x": 90.0, "y": 190.0, "z": 0.0},
      {"x": 110.0, "y": 190.0, "z": 0.0},
      {"x": 110.0, "y": 210.0, "z": 0.0},
      {"x": 90.0, "y": 210.0, "z": 0.0}
    ],
    "height": 50.0,
    "area": 400.0,
    "created_at": 1620000000.0,
    "last_updated": 1620000000.0
  },
  {
    "id": "550e8400-e29b-41d4-a716-446655440001",
    "name": "Water Tower",
    "type": "circle",
    "position": {"x": 300.0, "y": 400.0, "z": 0.0},
    "description": "Water tower",
    "radius": 15.0,
    "width": null,
    "length": null,
    "vertices": [],
    "height": 30.0,
    "area": 706.86,
    "created_at": 1620000100.0,
    "last_updated": 1620000100.0
  },
  {
    "id": "550e8400-e29b-41d4-a716-446655440002",
    "name": "Garden Pond",
    "type": "ellipse",
    "position": {"x": 180.0, "y": 120.0, "z": 0.0},
    "description": "Elliptical pond area",
    "radius": null,
    "width": 20.0,
    "length": 15.0,
    "vertices": [],
    "height": 0.0,
    "area": 942.48,
    "created_at": 1620000200.0,
    "last_updated": 1620000200.0
  }
]
```

### 创建新障碍物

**端点:** `POST /obstacles`

**描述:** 在系统中创建一个新障碍物。

**参数:**

| 名称 | 类型 | 必需 | 描述 |
|------|------|----------|-------------|
| name | string | Yes | 障碍物名称 |
| type | string | Yes | 障碍物类型（点、圆形、椭圆、多边形） |
| position | object | Yes | 位置坐标 {x, y, z} |
| description | string | No | 障碍物描述（默认：""） |
| radius | float | Conditional | 点/圆形障碍物的半径（圆形障碍物必需；点障碍物默认为1.0） |
| width | float | Conditional | 椭圆障碍物的半长轴（椭圆类型必需） |
| length | float | Conditional | 椭圆障碍物的半短轴（椭圆类型必需） |
| vertices | array | Conditional | 多边形障碍物的顶点（多边形类型必需，至少3个顶点） |
| height | float | No | 高度（米），默认：10.0；0表示在任何高度都无法通过 |

**响应:** 新创建的障碍物对象

**请求示例（圆形）:**
```bash
curl -X POST http://localhost:8000/obstacles \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Water Tower",
    "type": "circle",
    "position": {"x": 300.0, "y": 400.0, "z": 0.0},
    "description": "Water tower",
    "radius": 15.0,
    "height": 30.0
  }'
```

**请求示例（多边形）:**
```bash
curl -X POST http://localhost:8000/obstacles \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Tall Building",
    "type": "polygon",
    "position": {"x": 100.0, "y": 200.0, "z": 0.0},
    "description": "Office building",
    "vertices": [
      {"x": 90.0, "y": 190.0, "z": 0.0},
      {"x": 110.0, "y": 190.0, "z": 0.0},
      {"x": 110.0, "y": 210.0, "z": 0.0},
      {"x": 90.0, "y": 210.0, "z": 0.0}
    ],
    "height": 50.0
  }'
```

**请求示例（椭圆）:**
```bash
curl -X POST http://localhost:8000/obstacles \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Garden Pond",
    "type": "ellipse",
    "position": {"x": 180.0, "y": 120.0, "z": 0.0},
    "description": "Elliptical pond - no fly zone",
    "width": 20.0,
    "length": 15.0,
    "height": 0.0
  }'
```

**请求示例（点）:**
```bash
curl -X POST http://localhost:8000/obstacles \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Landing Marker",
    "type": "point",
    "position": {"x": 220.0, "y": 160.0, "z": 0.0},
    "description": "Landing zone marker",
    "radius": 2.0,
    "height": 0.5
  }'
```

**响应示例:**
```json
{
  "id": "550e8400-e29b-41d4-a716-446655440001",
  "name": "Water Tower",
  "type": "circle",
  "position": {"x": 300.0, "y": 400.0, "z": 0.0},
  "description": "Water tower",
  "radius": 15.0,
  "vertices": null,
  "height": 30.0,
  "created_at": 1620000100.0,
  "last_updated": 1620000100.0
}
```

### 获取特定障碍物

**端点:** `GET /obstacles/{obstacle_id}`

**描述:** 获取特定障碍物的信息。

**参数:**

| 名称 | 类型 | 必需 | 描述 |
|------|------|----------|-------------|
| obstacle_id | string | Yes | 障碍物ID（在URL路径中） |

**响应:** 障碍物对象

**请求示例:**
```bash
curl -X GET http://localhost:8000/obstacles/550e8400-e29b-41d4-a716-446655440001
```

**示例响应：**
```json
{
  "id": "550e8400-e29b-41d4-a716-446655440001",
  "name": "Water Tower",
  "type": "circle",
  "position": {"x": 300.0, "y": 400.0, "z": 0.0},
  "description": "Water tower",
  "radius": 15.0,
  "vertices": null,
  "height": 30.0,
  "created_at": 1620000100.0,
  "last_updated": 1620000100.0
}
```

### 更新障碍物

**端点：** `PUT /obstacles/{obstacle_id}`

**描述：** 更新障碍物的属性。

**参数：**

| 名称 | 类型 | 必需 | 描述 |
|------|------|----------|-------------|
| obstacle_id | string | 是 | 障碍物的ID（在URL路径中） |
| name | string | 否 | 障碍物的新名称 |
| position | object | 否 | 新的位置坐标 {x, y, z} |
| description | string | 否 | 障碍物的新描述 |
| radius | float | 否 | 圆形障碍物的新半径 |
| vertices | array | 否 | 多边形障碍物的新顶点 |
| height | float | 否 | 障碍物的新高度（米） |

**响应：** 更新后的障碍物对象

**示例请求：**
```bash
curl -X PUT http://localhost:8000/obstacles/550e8400-e29b-41d4-a716-446655440001 \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Large Water Tower",
    "radius": 20.0
  }'
```

**示例响应：**
```json
{
  "id": "550e8400-e29b-41d4-a716-446655440001",
  "name": "Large Water Tower",
  "type": "circle",
  "position": {"x": 300.0, "y": 400.0, "z": 0.0},
  "description": "Water tower",
  "radius": 20.0,
  "vertices": null,
  "height": 30.0,
  "created_at": 1620000100.0,
  "last_updated": 1620000200.0
}
```

### 删除障碍物

**端点：** `DELETE /obstacles/{obstacle_id}`

**描述：** 从系统中删除障碍物。

**参数：**

| 名称 | 类型 | 必需 | 描述 |
|------|------|----------|-------------|
| obstacle_id | string | 是 | 障碍物的ID（在URL路径中） |

**响应：** 无内容 (204)

**示例请求：**
```bash
curl -X DELETE http://localhost:8000/obstacles/550e8400-e29b-41d4-a716-446655440001
```

### 按类型获取障碍物

**端点：** `GET /obstacles/type/{type}`

**描述：** 检索特定类型的所有障碍物。

**参数：**

| 名称 | 类型 | 必需 | 描述 |
|------|------|----------|-------------|
| type | string | 是 | 障碍物的类型（point, circle, ellipse, polygon）（在URL路径中） |

**响应：** 障碍物对象数组

**示例请求：**
```bash
curl -X GET http://localhost:8000/obstacles/type/polygon
```

**示例响应：**
```json
[
  {
    "id": "550e8400-e29b-41d4-a716-446655440000",
    "name": "Tall Building",
    "type": "building",
    "position": {"x": 100.0, "y": 200.0, "z": 0.0},
    "description": "Office building",
    "radius": null,
    "vertices": [
      {"x": 90.0, "y": 190.0},
      {"x": 110.0, "y": 190.0},
      {"x": 110.0, "y": 210.0},
      {"x": 90.0, "y": 210.0}
    ],
    "height": 50.0,
    "created_at": 1620000000.0,
    "last_updated": 1620000000.0
  }
]
```

## 碰撞检测 API

### 检查路径碰撞

**端点：** `POST /obstacles/path_collision`

**认证：** 需要 SYSTEM 角色（ADMIN 继承）

**描述：** 检查从起点到终点的飞行路径是否与任何障碍物发生碰撞。返回与路径碰撞的**第一个**障碍物。

**参数：**

| 名称 | 类型 | 必需 | 描述 |
|------|------|----------|-------------|
| start | object | 是 | 起点 {x, y, z} |
| end | object | 是 | 终点 {x, y, z} |
| safety_margin | float | 否 | 飞行路径周围的额外净空距离（米）（默认：0.0）。在每侧创建指定宽度的安全走廊。使用 0.0 表示直线路径，使用 > 0.0 表示安全走廊（例如，5.0 创建 10 米宽的走廊）。注意：无人机移动命令默认使用 0.0 |

**高度逻辑：**
- `height = 0`：在任何高度都不可通行
- `height > 0`：仅当最大飞行高度 <= obstacle.height 时发生碰撞

**响应：** 碰撞响应对象，若无碰撞则为 null

**示例请求：**
```bash
curl -X POST http://localhost:8000/obstacles/path_collision \
  -H "Content-Type: application/json" \
  -H "X-API-Key: <SYSTEM_API_KEY>" \
  -d '{
    "start": {"x": 0.0, "y": 0.0, "z": 10.0},
    "end": {"x": 200.0, "y": 300.0, "z": 10.0},
    "safety_margin": 2.0
  }'
```

**示例响应（有碰撞）：**
```json
{
  "obstacle_id": "550e8400-e29b-41d4-a716-446655440001",
  "obstacle_name": "Water Tower",
  "type": "circle",
  "collision_type": "path_intersection",
  "distance": 5.0
}
```

**示例响应（无碰撞）：**
```json
null
```

### 检查点碰撞

**端点：** `POST /obstacles/point_collision`

**认证：** 需要 SYSTEM 角色（ADMIN 继承）

**描述：** 检查一个点是否在任何障碍物内部或其边界上（带余量）。返回包含该点的**所有**障碍物。

**参数：**

| 名称 | 类型 | 必需 | 描述 |
|------|------|----------|-------------|
| x | float | 是 | 点的 X 坐标 |
| y | float | 是 | 点的 Y 坐标 |
| z | float | 否 | 点的 Z 坐标（高度）。如果未提供，只进行二维检查 |
| margin | float | 否 | 障碍物周围的余量（米）（默认：0.0）。按此量扩展障碍物几何和高度 |

**高度逻辑：**
- **未提供 z**：仅检查二维区域（所有障碍物均为不可飞行）
- **提供了 z + 障碍物高度 = 0**：在任何高度都不可飞行
- **提供了 z + 障碍物高度 > 0**：
- 若 `z <= obstacle.height + margin`，点位于内部
- 若 `z > obstacle.height + margin`，点位于外部

**响应：** 点位于障碍物中的响应对象，包含所有匹配障碍物的列表

**示例请求（二维检查）：**
```bash
curl -X POST http://localhost:8000/obstacles/point_collision \
  -H "Content-Type: application/json" \
  -H "X-API-Key: <SYSTEM_API_KEY>" \
  -d '{
    "x": 100.0,
    "y": 200.0,
    "margin": 0.0
  }'
```

**示例请求（带高度和余量的三维检查）：**
```bash
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

**示例响应（点位于多个障碍物内）：**
```json
{
  "result": true,
  "inside_obstacle_ids": [
    "550e8400-e29b-41d4-a716-446655440000",
    "550e8400-e29b-41d4-a716-446655440001"
  ],
  "inside_obstacles": [
    {
      "id": "550e8400-e29b-41d4-a716-446655440000",
      "name": "Building A",
      "type": "circle",
      "height": 30.0,
      "distance_to_boundary": -5.3
    },
    {
      "id": "550e8400-e29b-41d4-a716-446655440001",
      "name": "No-Fly Zone",
      "type": "polygon",
      "height": 0.0,
      "distance_to_boundary": -12.8
    }
  ],
  "point": {"x": 100.0, "y": 200.0, "z": 5.0},
  "margin": 2.0,
  "message": "Point is inside 2 obstacle(s)"
}
```

**示例响应（点位于所有障碍物外）：**
```json
{
  "result": false,
  "inside_obstacle_ids": [],
  "inside_obstacles": [],
  "point": {"x": 100.0, "y": 200.0, "z": 5.0},
  "margin": 0.0,
  "message": "Point is not inside any obstacles"
}
```
---

## 检查端点（仅限 ADMIN）

`/check/` 端点提供验证和确认功能，用于测试、监控和自动化场景。此类别中的所有端点都需要通过 `X-API-Key` 进行 ADMIN 角色认证。

### 标准响应格式

每个检查端点至少返回：

```json
{
  "result": true,
  "value": 0.75
}
```

- `result`：检查的布尔结果（若无法确定，默认为 `false`）
- `value`：主要测量值（距离、高度、进度比等）
- 其他字段提供上下文（ID、容差、列表、百分比等）

### 端点（概述）

- **GET** `/check/drone_position` — 到期望位置的距离（若提供 `z` 则为三维）
- 参数：`drone_id`、`x`、`y`、`z?`、`tolerance?`
- `value`：距离（米）；`result`：是否在容差范围内
- **GET** `/check/drone_altitude` — 高度接近程度
- 参数：`drone_id`、`expected_altitude`、`tolerance?`
- `value`：当前高度
- **GET** `/check/drone_status` — 状态相等性
- 参数：`drone_id`、`expected_status`
- `value`：当前状态
- **GET** `/check/drone_on_ground` — 高度接近地面且状态类地面的检查
- 参数：`drone_id`、`tolerance?`
- `value`：高度
- **GET** `/check/all_drones_on_ground` — 机队地面状态计数
- 参数：`tolerance?`
- `value`：地面上的无人机数量
- **GET** `/check/drone_hovering` — 悬停状态检查（高于地面）
- 参数：`drone_id`、`tolerance?`
- `value`：当前状态
- **GET** `/check/all_drones_hovering` — 机队悬停计数
- 参数：`tolerance?`
- `value`：悬停无人机数量
- **GET** `/check/drone_over_height` — 高度超过最低高度的检查
- 参数：`drone_id`、`min_height`、`tolerance?`
- `value`：高度（米）
- **GET** `/check/target_within_drone_distance` — 目标是否在无人机最大距离内
- 参数：`drone_id`、`target_id`、`max_distance`
- `value`：距离（米）
- **GET** `/check/obstacle_within_drone_distance` — 障碍物是否在无人机最大距离内
- 参数：`drone_id`、`obstacle_id`、`max_distance`
- `value`：距离（米）
- **GET** `/check/two_drones_distance` — 两架无人机是否在距离范围内
- 参数：`drone_1_id`、`drone_2_id`、`max_distance?`、`min_distance?`
- `value`：实际距离
- **GET** `/check/drone_group_distance` — 无人机群对是否满足距离范围规则
- 参数：重复的 `drone_ids`（至少2个）、`max_distance?`、`min_distance?`、`mode?`（默认为 `all_pairs`，或 `any_pair`）
- `value`：通过的对数
- **GET** `/check/drone_battery_level` — 电池电量与最低值对比
- 参数：`drone_id`、`min_level?`
- `value`：电池电量（%）
- **GET** `/check/drone_heading` — 航向是否在容差范围内
- 参数：`drone_id`、`expected_heading`、`tolerance?`
- `value`：当前航向（度）
- **GET** `/check/drone_in_target` — 无人机是否在目标半径内
- 参数：`drone_id`、`target_id`
- `value`：到目标中心的距离（米）
- **GET** `/check/drone_at_home` — 无人机是否在家的容差范围内
- 参数：`drone_id`、`tolerance?`
- `value`：到家的距离（米）
- **GET** `/check/target_within_drone_task_radius` — 目标是否在无人机任务半径内
- 参数：`drone_id`、`target_id`
- `value`：距离（米）
- **GET** `/check/target_within_drone_perceived_radius` — 目标是否在无人机感知半径内
- 参数：`drone_id`、`target_id`
- `value`：距离（米）
- **GET** `/check/obstacle_within_drone_perceived_radius` — 障碍物是否在无人机感知半径内
- 参数：`drone_id`、`obstacle_id`
- `value`：距离（米）
- **GET** `/check/drone_has_taken_off` — 检查无人机历史中是否起飞
- 参数：`drone_id`、`min_altitude?`、`max_altitude?`、`tolerance?`、`since_timestamp?`
- `value`：符合请求高度范围的起飞事件数量
- 模式：
- 阈值模式：省略 `max_altitude`；匹配高度 `>= min_altitude - tolerance` 的起飞
- 范围模式：同时提供 `min_altitude` 和 `max_altitude`；匹配高度在 `[min_altitude - tolerance, max_altitude + tolerance]` 范围内的起飞
- 精确高度模式：设置 `min_altitude == max_altitude`，并使用 `tolerance` 作为该高度周围的接受范围
- 响应扩展：`takeoff_count`、`last_takeoff_time`、`max_altitude_reached`、`min_altitude_threshold`、`max_altitude_threshold`、`tolerance`
- **GET** `/check/drone_has_landed` — 检查无人机历史中是否降落
- 参数：`drone_id`、`min_count?`、`since_timestamp?`
- `value`：找到的降落事件数量
- **GET** `/check/drone_has_visited_position` — 检查无人机是否访问过某位置
- 参数：`drone_id`、`x`、`y`、`z?`、`tolerance?`、`since_timestamp?`
- `value`：访问该位置的次数
- **GET** `/check/drone_has_moved_distance` — 检查无人机是否移动了最小距离
- 参数：`drone_id`、`min_distance`、`since_timestamp?`
- `value`：总移动距离（米）
- **GET** `/check/drone_has_moved_directed_distance` — 检查无人机是否沿特定方向移动了最小距离
- 参数：`drone_id`、`min_distance`、`heading`、`tolerance?`、`since_timestamp?`
- `value`：总定向移动距离（米）
- **GET** `/check/drone_has_hovered` — 检查无人机历史中是否悬停
- 参数：`drone_id`、`min_duration?`、`since_timestamp?`
- `value`：找到的悬停事件数量
- **GET** `/check/drone_has_taken_photo` — 检查无人机是否拍摄了照片
- 参数：`drone_id`、`min_count?`、`since_timestamp?`
- `value`：拍摄的照片数量
- **GET** `/check/target_in_photo_taken_by_drone` — 检查目标是否在无人机拍摄的照片中
- 参数：`drone_id`、`target_id`
- `value`：布尔结果
- **GET** `/check/drone_has_charged` — 检查无人机历史中是否充电
- 参数：`drone_id`、`min_charge_amount?`、`since_timestamp?`
- `value`：找到的充电事件数量
- 注意：即使实际充电量较小，充满至100%的充电事件也满足 `min_charge_amount`。
- **GET** `/check/drone_has_sent_message` — 检查无人机是否发送了消息（包括广播）
- 参数：`drone_id`、`to_drone_id?`、`min_count?`、`since_timestamp?`
- `value`：发送的消息数量
- **GET** `/check/drone_has_sent_message_content` — 检查无人机是否发送了包含指定内容的短信
- 参数: `drone_id`, `content`, `to_drone_id?`, `min_count?`, `since_timestamp?`
- `value`: 匹配消息的数量
- **GET** `/check/all_drones_have_taken_off` — 检查所有无人机是否已起飞
- 参数: `min_altitude?`, `since_timestamp?`, `check_history?`
- `value`: 已起飞的无人机数量；`percentage` 包含机队百分比
- **GET** `/check/all_drones_have_landed` — 检查所有无人机是否已降落
- 参数: `min_count?`, `since_timestamp?`, `check_history?`
- `value`: 已降落的无人机数量；`percentage` 包含机队百分比
- **GET** `/check/target_is_reached` — 任意无人机到达目标
- 参数: `target_id`, `since_timestamp?`
- `value`: 到达目标的无人机数量
- **GET** `/check/target_is_reached_by_drone` — 指定无人机到达目标
- 参数: `target_id`, `drone_id`, `since_timestamp?`
- `value`: 该无人机的访问次数
- **GET** `/check/target_reached_drone_number` — 已到达无人机数量与期望值的对比
- 参数: `target_id`, `expected_count?`, `since_timestamp?`
- `value`: 到达目标的无人机数量
- **GET** `/check/moving_target_tracked` — 移动目标被跟踪至少一段时间
- 参数: `target_id`, `drone_id?`, `min_duration?`, `since_timestamp?`
- `value`: 最大保持跟踪时长（秒）
- **GET** `/check/target_is_fully_searched` — 区域覆盖阈值（默认 0.99）
- 参数: `target_id`, `coverage_threshold?`
- `value`: 覆盖率（0-1）
- **GET** `/check/target_searched_area_percentage` — 覆盖率与期望值的比率
- 参数: `target_id`, `expected_percentage` (0-1)
- `value`: 覆盖率（0-1）
- **GET** `/check/task_progress` — 进度与期望值的比率
- 参数: `expected_progress?` (0-1)
- `value`: 进度比率（0-1）
- **GET** `/check/task_done` — 使用会话进度判断的完成标志
- 参数: *(无)*
- `value`: 进度比率（0-1）

### 示例

```bash
# Position within tolerance
curl -X GET "http://localhost:8000/check/drone_position?drone_id=drone-1&x=50.0&y=30.0&z=5.0&tolerance=2.0" \
  -H "X-API-Key: <ADMIN_API_KEY>"

# Target reach by specific drone
curl -X GET "http://localhost:8000/check/target_is_reached_by_drone?target_id=target-1&drone_id=drone-1" \
  -H "X-API-Key: <ADMIN_API_KEY>"

# Moving target tracked by any drone for at least 10 seconds
curl -X GET "http://localhost:8000/check/moving_target_tracked?target_id=target-1&min_duration=10.0" \
  -H "X-API-Key: <ADMIN_API_KEY>"

# Moving target tracked by a specific drone for at least 10 seconds
curl -X GET "http://localhost:8000/check/moving_target_tracked?target_id=target-1&drone_id=drone-1&min_duration=10.0" \
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

# Task progress meets expectation
curl -X GET "http://localhost:8000/check/task_progress?expected_progress=0.8" \
  -H "X-API-Key: <ADMIN_API_KEY>"

# Check if drone has taken off (history)
curl -X GET "http://localhost:8000/check/drone_has_taken_off?drone_id=drone-1&min_altitude=5.0" \
  -H "X-API-Key: <ADMIN_API_KEY>"

# Check if drone has taken off within an altitude range
curl -X GET "http://localhost:8000/check/drone_has_taken_off?drone_id=drone-1&min_altitude=9.0&max_altitude=11.0&tolerance=0.2" \
  -H "X-API-Key: <ADMIN_API_KEY>"

# Check if drone has taken off to about 10m (10.0 +/- 0.5)
curl -X GET "http://localhost:8000/check/drone_has_taken_off?drone_id=drone-1&min_altitude=10.0&max_altitude=10.0&tolerance=0.5" \
  -H "X-API-Key: <ADMIN_API_KEY>"

# Check if drone has visited a specific position
curl -X GET "http://localhost:8000/check/drone_has_visited_position?drone_id=drone-1&x=50.0&y=30.0&z=10.0&tolerance=2.0" \
  -H "X-API-Key: <ADMIN_API_KEY>"

# Check if drone has moved minimum distance
curl -X GET "http://localhost:8000/check/drone_has_moved_distance?drone_id=drone-1&min_distance=100.0" \
  -H "X-API-Key: <ADMIN_API_KEY>"

# Check if drone has moved minimum distance in a specific direction
curl -X GET "http://localhost:8000/check/drone_has_moved_directed_distance?drone_id=drone-1&min_distance=10.0&heading=90.0&tolerance=5.0" \
  -H "X-API-Key: <ADMIN_API_KEY>"

# Check if drone has taken photos
curl -X GET "http://localhost:8000/check/drone_has_taken_photo?drone_id=drone-1&min_count=3" \
  -H "X-API-Key: <ADMIN_API_KEY>"

# Check if all drones have taken off (check current status)
curl -X GET "http://localhost:8000/check/all_drones_have_taken_off?check_history=false&min_altitude=5.0" \
  -H "X-API-Key: <ADMIN_API_KEY>"

# Check if all drones are currently hovering
curl -X GET "http://localhost:8000/check/all_drones_hovering" \
  -H "X-API-Key: <ADMIN_API_KEY>"
```

---

"session_name": "区域搜索任务",
"task_type": "area_search",
"is_completed": false,
"progress_percentage": 75,
"status_message": "任务待完成",
"details": {
"total_targets": 2,
"average_coverage": 75.5
}
}
```

**使用场景：**
- 自动化测试与验证
- 任务监控与完成情况跟踪
- CI/CD 流水线集成
- 性能基准测试
