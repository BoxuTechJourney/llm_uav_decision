# API 认证与角色指南

MultiUAV-Plat 服务器系统 API 使用基于 **API 密钥的认证**，并采用分层级的基于角色的访问控制（RBAC）系统。

---

## 1. 认证概览

### 🔓 默认行为
**当未提供 API 密钥时，系统默认分配为 AGENT 角色。**

### API 密钥用法
要访问特定角色，请在 `X-API-Key` 标头中提供有效的 API 密钥：

```bash
# Example for SYSTEM access
curl -H "X-API-Key: <SYSTEM_API_KEY>" http://localhost:8000/drones
```

### 🔑 API 密钥
该软件接受一个 AGENT 密钥，以及多个针对 USER、SYSTEM 和 ADMIN 的硬编码特权密钥。实际的密钥值存储在应用程序代码中，本文档中有意省略。

| 角色 | 接受的密钥 |
|:---|:---|
| **AGENT** | `<AGENT_API_KEY>` |
| **USER** | 3 个以上硬编码的 USER 特权密钥 |
| **SYSTEM** | 3 个以上硬编码的 SYSTEM 特权密钥 |
| **ADMIN** | 3 个以上硬编码的 ADMIN 特权密钥 |

### 用户角色

| 角色 | 访问级别 | 描述 |
|:---|:---|:---|
| **AGENT** | **飞行员访问** | 可以控制无人机飞行，查看周边环境以及基本会话统计信息；无法查看全局列表（目标/障碍物）。 |
| **USER** | **查看者访问** | 继承 AGENT 权限；可以查看完整的全局场景（所有目标/障碍物）和会话实体。 |
| **SYSTEM** | **管理** | 继承 USER 权限；可以创建/编辑/删除实体（无人机、目标等）并管理会话。 |
| **ADMIN** | **完全访问** | 继承 SYSTEM 权限；独享验证与评分（`/check/*`）端点的访问权限。 |

---

## 2. 角色层级与对比

系统采用线性继承模型：**ADMIN > SYSTEM > USER > AGENT**。

| 类别 | 功能/端点 | AGENT | USER | SYSTEM | ADMIN |
|:---|:---|:---:|:---:|:---:|:---:|
| **无人机** | 控制无人机（飞行指令） | ✅ | ✅ | ✅ | ✅ |
| | 获取指令历史/状态 | ✅ | ✅ | ✅ | ✅ |
| | **注册/删除无人机** | ❌ | ❌ | ✅ | ✅ |
| **目标** | 获取特定目标信息 | ✅ | ✅ | ✅ | ✅ |
| | **列出所有目标（全局）** | ❌ | ✅ | ✅ | ✅ |
| | **添加/更新/删除目标** | ❌ | ❌ | ✅ | ✅ |
| **障碍物** | 获取特定障碍物信息 | ✅ | ✅ | ✅ | ✅ |
| | **列出所有障碍物（全局）** | ❌ | ✅ | ✅ | ✅ |
| | **添加/更新/删除障碍物** | ❌ | ❌ | ✅ | ✅ |
| **会话** | 获取会话元数据 | ✅ | ✅ | ✅ | ✅ |
| | **获取会话实体数据** | ❌ | ✅ | ✅ | ✅ |
| | **获取会话历史数据** | ❌ | ❌ | ✅ | ✅ |
| | **重置当前会话** | ❌ | ❌ | ✅ | ✅ |
| | **创建/恢复/删除会话** | ❌ | ❌ | ✅ | ✅ |
| **任务** | 查看/标记完成 | ✅ | ✅ | ✅ | ✅ |
| | **创建/更新/删除任务** | ❌ | ❌ | ✅ | ✅ |
| **验证** | **所有 `/check` 端点** | ❌ | ❌ | ❌ | ✅ |

### 数据可见性与屏蔽
为保护场景完整性：
*   **AGENT**：`GET /sessions/current` 始终只返回**元数据**。
*   **USER**：`GET /sessions/current?data=true` 返回实体（无人机、目标），但会**隐藏历史**。
*   **任务详情**：对于 AGENT/USER，敏感任务字段（例如隐藏的 API 检查）会被屏蔽。

---

## 3. 详细的 API 端点权限

下表列出了所有 API 端点以及访问所需的**最低角色**。

### 图例
- **AGENT+**：可由 AGENT、USER、SYSTEM 和 ADMIN 访问。
- **USER+**：可由 USER、SYSTEM 和 ADMIN 访问。
- **SYSTEM+**：仅可由 SYSTEM 和 ADMIN 访问。
- **ADMIN**：仅可由 ADMIN 访问。

### 🚁 无人机

| 方法 | 端点 | 描述 | 最低角色 |
|:---|:---|:---|:---:|
| `GET` | `/drones` | 获取所有已注册的无人机 | **AGENT+** |
| `POST` | `/drones` | 注册新无人机 | **SYSTEM+** |
| `GET` | `/drones/{id}` | 获取特定无人机的详细信息 | **AGENT+** |
| `PUT` | `/drones/{id}` | 更新无人机属性 | **SYSTEM+** |
| `DELETE` | `/drones/{id}` | 删除无人机 | **SYSTEM+** |
| `PUT` | `/drones/{id}/position` | 管理员设置位置 | **SYSTEM+** |
| `GET` | `/drones/{id}/nearby` | 本地感知（所有类型） | **AGENT+** |
| `GET` | `/drones/{id}/nearby/drones` | 本地感知（无人机） | **AGENT+** |
| `GET` | `/drones/{id}/nearby/targets` | 本地感知（目标） | **AGENT+** |
| `GET` | `/drones/{id}/nearby/obstacles` | 本地感知（障碍物） | **AGENT+** |
| `POST` | `/drones/{id}/battery` | 更新电量（测试） | **AGENT+** |
| `POST` | `/drones/land_all` | 所有无人机降落（管理） | **SYSTEM+** |
| `POST` | `/drones/charge_all` | 所有无人机充电（管理） | **SYSTEM+** |

### 🎮 无人机指令（飞行员）

| 方法 | 端点 | 描述 | 最低角色 |
|:---|:---|:---|:---:|
| `POST` | `/drones/{id}/command` | 发送通用指令 | **AGENT+** |
| `GET` | `/drones/{id}/commands` | 获取指令历史 | **AGENT+** |
| `GET` | `/commands/{id}` | 获取指令状态 | **AGENT+** |
| `POST` | `/drones/{id}/command/take_off` | 起飞 | **AGENT+** |
| `POST` | `/drones/{id}/command/land` | 降落 | **AGENT+** |
| `POST` | `/drones/{id}/command/move_to` | 移动到坐标位置 | **AGENT+** |
| `POST` | `/drones/{id}/command/move_towards` | 向某方向移动 | **AGENT+** |
| `POST` | `/drones/{id}/command/move_along_path` | 沿路径飞行 | **AGENT+** |
| `POST` | `/drones/{id}/command/change_altitude` | 改变高度 | **AGENT+** |
| `POST` | `/drones/{id}/command/hover` | 悬停 | **AGENT+** |
| `POST` | `/drones/{id}/command/rotate` | 旋转航向 | **AGENT+** |
| `POST` | `/drones/{id}/command/return_home` | 返回原点 | **AGENT+** |
| `POST` | `/drones/{id}/command/set_home` | 将当前位置设为原点 | **AGENT+** |
| `POST` | `/drones/{id}/command/calibrate` | 校准传感器 | **AGENT+** |
| `POST` | `/drones/{id}/command/take_photo` | 拍照 | **AGENT+** |
| `POST` | `/drones/{id}/command/send_message` | 发送消息 | **AGENT+** |
| `POST` | `/drones/{id}/command/broadcast` | 广播消息 | **AGENT+** |
| `POST` | `/drones/{id}/command/charge` | 为电池充电 | **AGENT+** |

### 🎯 目标

| 方法 | 端点 | 描述 | 最低角色要求 |
|:---|:---|:---|:---:|
| `GET` | `/targets` | 获取所有目标（全局列表） | **USER+** |
| `POST` | `/targets` | 创建新目标 | **SYSTEM+** |
| `GET` | `/targets/{id}` | 获取特定目标 | **AGENT+** |
| `PUT` | `/targets/{id}` | 更新目标 | **SYSTEM+** |
| `DELETE` | `/targets/{id}` | 删除目标 | **SYSTEM+** |
| `GET` | `/targets/type/{type}` | 按类型获取目标 | **USER+** |
| `POST` | `/targets/waypoints/{id}/check-drone` | 检查充电状态 | **USER+** |

### 🧱 障碍物

| 方法 | 端点 | 描述 | 最低角色要求 |
|:---|:---|:---|:---:|
| `GET` | `/obstacles` | 获取所有障碍物（全局列表） | **USER+** |
| `POST` | `/obstacles` | 创建新障碍物 | **SYSTEM+** |
| `GET` | `/obstacles/{id}` | 获取特定障碍物 | **AGENT+** |
| `PUT` | `/obstacles/{id}` | 更新障碍物 | **SYSTEM+** |
| `DELETE` | `/obstacles/{id}` | 删除障碍物 | **SYSTEM+** |
| `GET` | `/obstacles/type/{type}` | 按类型获取障碍物 | **USER+** |
| `POST` | `/obstacles/path_collision` | 检查路径碰撞 | **SYSTEM+** |
| `POST` | `/obstacles/point_collision` | 检查点碰撞 | **SYSTEM+** |

### 🌤️ 环境

| 方法 | 端点 | 描述 | 最低角色要求 |
|:---|:---|:---|:---:|
| `GET` | `/environments` | 获取所有环境 | **SYSTEM+** |
| `POST` | `/environments` | 创建环境 | **SYSTEM+** |
| `GET` | `/environments/current` | 获取当前环境 | **AGENT+** |
| `GET` | `/environments/{id}` | 获取特定环境 | **AGENT+** |
| `PUT` | `/environments/{id}` | 更新环境 | **SYSTEM+** |
| `DELETE` | `/environments/{id}` | 删除环境 | **SYSTEM+** |
| `POST` | `/environments/{id}/set-current` | 设置活跃环境 | **SYSTEM+** |

### 🎬 会话

| 方法 | 端点 | 描述 | 最低角色要求 |
|:---|:---|:---|:---:|
| `GET` | `/sessions` | 获取所有会话（仅元数据） | **AGENT+** |
| `POST` | `/sessions` | 创建新会话 | **SYSTEM+** |
| `GET` | `/sessions/current` | 获取当前会话元数据 | **AGENT+** |
| `GET` | `/sessions/current/data` | 获取完整会话数据及历史记录 | **SYSTEM+** |
| `POST` | `/sessions/current/reset` | 重置会话历史记录 | **SYSTEM+** |
| `GET` | `/sessions/current/screenshot` | 获取当前截图 | **AGENT+** |
| `GET` | `/sessions/{id}` | 获取会话元数据 | **SYSTEM+** |
| `POST` | `/sessions/{id}` | 使用 ID 创建/恢复会话 | **SYSTEM+** |
| `PUT` | `/sessions/{id}` | 更新会话元数据 | **SYSTEM+** |
| `DELETE` | `/sessions/{id}` | 删除会话 | **SYSTEM+** |
| `POST` | `/sessions/{id}/set-current` | 设置活跃会话（仅元数据） | **AGENT+** |
| `POST` | `/sessions/{id}/reset` | 重置会话历史记录 | **SYSTEM+** |
| `GET` | `/sessions/{id}/data` | 获取完整会话数据 | **SYSTEM+** |
| `GET` | `/sessions/{id}/screenshot` | 获取特定截图 | **SYSTEM+** |

### 📋 任务与追踪

| 方法 | 端点 | 描述 | 最低角色要求 |
|:---|:---|:---|:---:|
| `GET` | `/sessions/current/task-progress` | 获取当前任务进度 | **AGENT+** |
| `GET` | `/sessions/current/tasks` | 获取当前任务列表 | **AGENT+** |
| `GET` | `/sessions/current/tasks/next` | 获取下一个待处理任务 | **AGENT+** |
| `GET` | `/sessions/current/tasks/{id}/check` | 检查任务并设置通过状态 | **AGENT+** |
| `GET` | `/sessions/current/tasks/{id}` | 获取特定任务 | **AGENT+** |
| `POST` | `/sessions/current/tasks/{id}/mark-done` | 将任务标记为已完成（当前会话） | **AGENT+** |
| `POST` | `/sessions/current/tasks/{id}/mark-pending` | 将任务标记为待处理（当前会话） | **AGENT+** |
| `GET` | `/sessions/{id}/tasks` | 获取会话中的所有任务 | **USER+** |
| `POST` | `/sessions/{id}/tasks` | 创建新任务 | **SYSTEM+** |
| `GET` | `/sessions/{id}/tasks/{id}` | 获取特定任务 | **USER+** |
| `PUT` | `/sessions/{id}/tasks/{id}` | 更新任务 | **SYSTEM+** |
| `DELETE` | `/sessions/{id}/tasks/{id}` | 删除任务 | **SYSTEM+** |
| `POST` | `/sessions/{id}/tasks/{id}/mark-done` | 将任务标记为已完成 | **SYSTEM+** |
| `POST` | `/sessions/{id}/tasks/{id}/mark-pending` | 将任务标记为待处理 | **SYSTEM+** |
| `POST` | `/sessions/{id}/tasks/swap` | 交换任务顺序 | **SYSTEM+** |
| `GET` | `/sessions/{id}/command-history` | 获取命令历史 | **SYSTEM+** |
| `GET` | `/sessions/{id}/status-history` | 获取状态历史 | **SYSTEM+** |
| `GET` | `/sessions/{id}/target-reaches` | 获取目标到达记录 | **SYSTEM+** |
| `GET` | `/sessions/{id}/moving-target-tracking` | 获取移动目标追踪摘要 | **SYSTEM+** |
| `GET` | `/sessions/{id}/area-coverage` | 获取区域覆盖日志 | **SYSTEM+** |
| `GET` | `/sessions/{id}/task-progress` | 获取任务进度 | **SYSTEM+** |

### ✅ 系统检查（仅限管理员）

| 方法 | 端点 | 描述 | 最低角色 |
|:---|:---|:---|:---:|
| `GET` | `/check/drone_position` | 验证无人机坐标 | **ADMIN** |
| `GET` | `/check/drone_status` | 验证无人机状态 | **ADMIN** |
| `GET` | `/check/drone_battery_level` | 验证电池电量 | **ADMIN** |
| `GET` | `/check/drone_heading` | 验证航向 | **ADMIN** |
| `GET` | `/check/drone_over_height` | 验证最小高度 | **ADMIN** |
| `GET` | `/check/drone_altitude` | 验证精确高度 | **ADMIN** |
| `GET` | `/check/drone_in_target` | 验证无人机在目标内 | **ADMIN** |
| `GET` | `/check/drone_at_home` | 验证无人机在起飞点 | **ADMIN** |
| `GET` | `/check/target_within_drone_distance` | 检查目标与无人机的距离 | **ADMIN** |
| `GET` | `/check/target_in_photo_taken_by_drone` | 检查目标是否在照片中 | **ADMIN** |
| `GET` | `/check/obstacle_within_drone_distance` | 检查障碍物与无人机的距离 | **ADMIN** |
| `GET` | `/check/two_drones_distance` | 检查无人机之间的距离（参数：`drone_1_id`, `drone_2_id`） | **ADMIN** |
| `GET` | `/check/drone_on_ground` | 验证无人机在地面 | **ADMIN** |
| `GET` | `/check/all_drones_on_ground` | 验证所有无人机在地面 | **ADMIN** |
| `GET` | `/check/drone_hovering` | 验证无人机悬停 | **ADMIN** |
| `GET` | `/check/all_drones_hovering` | 验证所有无人机悬停 | **ADMIN** |
| `GET` | `/check/target_is_reached` | 验证目标已到达（任一无人机） | **ADMIN** |
| `GET` | `/check/target_is_reached_by_drone` | 验证目标已到达（特定无人机） | **ADMIN** |
| `GET` | `/check/drone_group_distance` | 检查无人机群内成对距离（参数：重复的 `drone_ids`, `mode`） | **ADMIN** |
| `GET` | `/check/moving_target_tracked` | 验证移动目标追踪时长 | **ADMIN** |
| `GET` | `/check/target_is_fully_searched` | 验证搜索覆盖率 | **ADMIN** |
| `GET` | `/check/task_progress` | 验证任务进度百分比 | **ADMIN** |
| `GET` | `/check/task_done` | 验证任务完成 | **ADMIN** |
| `GET` | `/check/drone_has_taken_off` | 历史记录：检查起飞 | **ADMIN** |
| `GET` | `/check/drone_has_landed` | 历史记录：检查降落 | **ADMIN** |
| `GET` | `/check/drone_has_visited_position` | 历史记录：检查位置访问 | **ADMIN** |
| `GET` | `/check/drone_has_moved_distance` | 历史记录：检查飞行距离 | **ADMIN** |
| `GET` | `/check/drone_has_moved_directed_distance` | 历史记录：检查定向距离 | **ADMIN** |
| `GET` | `/check/drone_has_hovered` | 历史记录：检查悬停时长 | **ADMIN** |
| `GET` | `/check/drone_has_taken_photo` | 历史记录：检查拍摄照片数量 | **ADMIN** |
| `GET` | `/check/drone_has_charged` | 历史记录：检查充电 | **ADMIN** |
| `GET` | `/check/drone_has_sent_message` | 历史记录：检查消息发送 | **ADMIN** |
| `GET` | `/check/drone_has_sent_message_content` | 历史记录：检查消息内容匹配 | **ADMIN** |
| `GET` | `/check/all_drones_have_taken_off` | 历史记录：检查所有无人机起飞 | **ADMIN** |
| `GET` | `/check/all_drones_have_landed` | 历史记录：检查所有无人机降落 | **ADMIN** |

### 🌐 公共/杂项

| 方法 | 端点 | 描述 | 最低角色 |
|:---|:---|:---|:---:|
| `GET` | `/` | 系统健康检查 | **Public** |
| `GET` | `/version` | 服务器版本信息 | **AGENT+** |
