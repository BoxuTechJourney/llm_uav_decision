# MultiUAV-Plat 服务系统

语言：[English](README.md) | **中文**

这是一个完整的无人机控制与仿真系统，提供基于 FastAPI 构建的 RESTful API，以及使用 Pygame 实现的交互式可视化 UI。系统为动态环境中的多架无人机仿真、控制和监控提供了完整框架。

## 主要功能

### 无人机管理

- **支持多架无人机**：同时注册和控制多架无人机。
- **实时监控**：跟踪位置、电量、状态和飞行参数。
- **命令执行**：发送起飞、降落和移动等命令。
- **紧急处理**：电量达到危险水平时自动执行紧急降落。
- **电池管理**：模拟真实的电量消耗和充电站。

### 环境仿真

- **天气条件**：支持晴朗、多云、下雨和暴风等多种天气。
- **动态环境要素**：支持建筑物、禁飞区和圆形障碍物。
- **碰撞检测**：检查路径和点位碰撞，并支持安全余量。
- **移动目标**：支持巡逻路线和航点导航。
- **充电站**：支持能够自动为无人机充电的航点。

### 开发者友好的 API

- **RESTful 接口**：使用 FastAPI 提供清晰且文档完善的 API。
- **会话管理**：保存、恢复和管理多个仿真场景。
- **交互式文档**：在 `/docs` 提供内置 Swagger UI。
- **Python 客户端库**：在 `/client` 中提供开箱即用的客户端示例。

## 项目结构

```text
.
├── api/                           # FastAPI 实现
│   ├── __init__.py
│   └── server.py                  # API 接口和服务配置
├── controllers/                   # 业务逻辑
│   ├── __init__.py
│   ├── drone_controller.py        # 无人机控制逻辑
│   ├── target_controller.py       # 目标管理逻辑
│   ├── obstacle_controller.py     # 障碍物管理和碰撞检测
│   └── environment_controller.py  # 环境管理逻辑
├── models/                        # 数据模型
│   ├── __init__.py
│   ├── drone.py                   # 无人机模型和枚举
│   ├── target.py                  # 目标模型和枚举
│   ├── obstacle.py                # 障碍物模型和碰撞检测
│   └── environment.py             # 环境模型和枚举
├── ui/                            # 用户界面
│   ├── __init__.py
│   └── interface.py               # Pygame UI 实现
├── main.py                        # 应用入口
├── requirements.txt              # 项目依赖
├── README.md                      # 英文文档
└── README_ZH.md                   # 中文文档
```

## 快速开始

### 前置条件

- Conda；推荐服务端环境使用 Python 3.11。
- 在已激活的 Conda 环境中使用 pip。

### 安装

1. **克隆仓库**

   ```bash
   git clone <repository-url>
   cd MultiUAV-Plat/server
   ```

2. **安装依赖**

   ```bash
   conda create -n multiuav-server python=3.11
   conda activate multiuav-server
   python -m pip install -r requirements.txt
   ```

3. **运行系统**

   ```bash
   # 同时运行 API 服务和 UI
   python main.py

   # 只运行 API 服务
   python main.py --api-only

   # 只运行 UI
   python main.py --ui

   # 运行 API 服务和带无人机控制功能的 UI，并跳过启动时的 UI 询问
   python main.py --ui-drone-control

   # 当前会话最多保留 10,000 条 HTTP 请求历史记录
   python main.py --api-only --request-history-limit 10000
   ```

4. **访问 API 文档**

   - 在浏览器中打开 <http://127.0.0.1:8000/docs>，使用交互式 Swagger UI。
   - 或访问 <http://127.0.0.1:8000/redoc>，查看 ReDoc 文档。

## 系统架构

### 核心组件

1. **API 服务**（`api/server.py`）
   - 基于 FastAPI 的 RESTful API。
   - 处理所有 HTTP 请求和响应。
   - 管理路由和请求校验。
   - 自动生成 OpenAPI 文档。

2. **控制器**（`controllers/`）
   - `drone_controller.py`：无人机生命周期和命令执行。
   - `target_controller.py`：目标和航点管理。
   - `obstacle_controller.py`：障碍物管理和碰撞检测。
   - `environment_controller.py`：天气和环境条件。
   - `session_controller.py`：会话状态管理。

3. **模型**（`models/`）
   - `drone.py`：无人机数据模型和枚举，如 `DroneStatus`、`DroneCommand`。
   - `target.py`：固定目标、移动目标、航点和充电站等目标类型。
   - `obstacle.py`：障碍物类型和碰撞几何。
   - `environment.py`：天气条件和环境参数。
   - `session.py`：会话状态和统计信息。

4. **UI 界面**（`ui/interface.py`）
   - 基于 Pygame 的可视化。
   - 实时无人机跟踪。
   - 交互式地图操作。
   - 障碍物和目标的可视化表示。

### 数据流

```text
客户端请求 → FastAPI 路由 → 控制器 → 模型 → 数据库/内存状态
                                      ↓
                               响应 → JSON 序列化
```

## 交互式 UI 操作

运行 UI（`python main.py` 或 `python main.py --ui`）时：

启动时用于询问是否打开图形仪表盘的对话框，与仪表盘本身使用相同的 `ui/img/drone.png` 窗口图标。

默认禁用 UI 中的无人机控制操作。使用 `--ui-drone-control` 启动后，界面会显示 **Take Off**/**Land** 按钮，并允许通过单击地图移动当前选中的、正在飞行的无人机。如果使用该选项时没有同时指定 `--ui` 或 `--api-only`，程序会直接启动图形仪表盘，不再询问是否打开 UI。

| 操作 | 功能 |
|---|---|
| **左键单击无人机** | 选择无人机并查看详情 |
| **左键单击目标** | 选择目标并查看信息 |
| **左键单击障碍物** | 选择障碍物并查看详情 |
| **左键单击地图** | 启用 `--ui-drone-control` 时，将选中的无人机移动到单击位置 |
| **鼠标滚轮** | 放大或缩小地图 |
| **方向键** | 平移地图视图 |
| **About 按钮** | 显示版本、版权、许可证、论文、项目和网站信息及可单击链接；单击外部区域关闭 |
| **R 键** | 从 API 服务刷新所有数据 |
| **ESC 键** | 退出应用 |

### UI 功能

- 实时更新所有无人机的位置。
- 显示电量指示器。
- 使用不同颜色显示无人机状态。
- 显示障碍物边界和禁飞区。
- 显示充电站位置。
- 显示移动目标轨迹。

## API 概览

系统提供完整的 RESTful API，主要分为以下几类。

### 核心接口分组

| 类别 | 基础路径 | 说明 |
|---|---|---|
| **会话** | `/sessions` | 管理仿真会话和场景 |
| **无人机** | `/drones` | 注册、控制和监控无人机 |
| **命令** | `/drones/{id}/command` | 执行无人机命令 |
| **目标** | `/targets` | 管理航点和任务目标 |
| **障碍物** | `/obstacles` | 创建和管理障碍物 |
| **碰撞** | `/obstacles/collision` | 检查路径和点位碰撞 |
| **环境** | `/environments` | 管理天气和环境条件 |

### 可用的无人机命令

| 命令 | 参数 | 说明 |
|---|---|---|
| `take_off` | `altitude`（float） | 起飞到指定高度 |
| `land` | 无 | 在当前位置降落 |
| `move_to` | `x, y, z`（float） | 移动到指定坐标 |
| `move_towards` | `distance, heading`（后者可选） | 沿指定方向移动；未指定方向时使用当前航向 |
| `move_along_path` | `waypoints`（至少 1 个）、`allow_partial_move`（可选 bool） | 沿一个或多个航点移动；也可在遇到障碍物时停在最后一个安全航点 |
| `change_altitude` | `altitude`（float） | 只改变高度 |
| `hover` | 无 | 保持当前位置 |
| `rotate` | `heading`（float） | 改变航向，0=北、90=东、180=南、270=西 |
| `return_home` | 无 | 返回起飞位置 |
| `set_home` | 无 | 将当前位置设为返航点 |
| `charge` | `charge_amount`（float） | 位于航点时为电池充电 |
| `take_photo` | 无 | 在当前位置拍照 |
| `send_message` | `target_drone_id, message` | 向另一架无人机发送消息 |
| `broadcast` | `message` | 向所有无人机广播消息 |
| `calibrate` | 无 | 校准传感器 |

如需包含请求和响应示例的详细 API 文档，请参阅：

- **[API_DOCUMENTATION.md](docs/API_DOCUMENTATION.md)**：包含示例的完整指南。
- **[API_REFERENCE.md](docs/API_REFERENCE.md)**：开发者快速参考。

```python
import requests

API_BASE_URL = "http://127.0.0.1:8000"

# 注册无人机
response = requests.post(f"{API_BASE_URL}/drones", json={
    "name": "Scout Alpha",
    "model": "Model-D4",
    "max_speed": 20.0,
    "max_altitude": 120.0,
    "battery_capacity": 100.0
})
drone = response.json()
drone_id = drone["id"]

# 起飞
requests.post(
    f"{API_BASE_URL}/drones/{drone_id}/command",
    json={"command": "take_off", "parameters": {"altitude": 10.0}}
)

# 移动到指定位置
requests.post(
    f"{API_BASE_URL}/drones/{drone_id}/command",
    json={"command": "move_to", "parameters": {"x": 50.0, "y": 50.0, "z": 15.0}}
)

# 沿路径移动；如果之后的航段被阻挡，则提前停止
requests.post(
    f"{API_BASE_URL}/drones/{drone_id}/command",
    json={
        "command": "move_along_path",
        "parameters": {
            "waypoints": [
                {"x": 10.0, "y": 20.0, "z": 15.0},
                {"x": 30.0, "y": 40.0, "z": 15.0},
                {"x": 50.0, "y": 60.0, "z": 15.0}
            ],
            "allow_partial_move": True
        }
    }
)

# 降落
requests.post(
    f"{API_BASE_URL}/drones/{drone_id}/command",
    json={"command": "land", "parameters": {}}
)
```

#### 使用 cURL

```bash
# 注册无人机
curl -X POST "http://127.0.0.1:8000/drones" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Scout Alpha",
    "model": "Model-D4",
    "max_speed": 20.0,
    "max_altitude": 120.0,
    "battery_capacity": 100.0
  }'

# 使用直接接口发送命令
curl -X POST "http://127.0.0.1:8000/drones/{drone_id}/command/take_off?altitude=10.0"

# 移动到指定坐标
curl -X POST "http://127.0.0.1:8000/drones/{drone_id}/command/move_to?x=50.0&y=30.0&z=15.0"
```

如需目标、障碍物、环境和高级功能等更完整的示例，请查看 `/client` 目录和完整 API 文档。

## 高级功能

### 会话管理

系统支持会话管理，可以保存和恢复完整的仿真状态。会话会记录创建者的角色，例如 user、system 或 admin：

```python
# 使用自动生成的 ID 创建会话，需要 SYSTEM 或 ADMIN 角色
headers = {"X-API-Key": "<SYSTEM_API_KEY>"}
response = requests.post(f"{API_BASE_URL}/sessions", headers=headers, json={
    "name": "Mission Alpha",
    "description": "Patrol mission scenario",
    "with_examples": True
})
session_id = response.json()["id"]

# 使用指定 ID 和完整数据创建会话
response = requests.post(f"{API_BASE_URL}/sessions/mission-backup-001?data=true",
    headers=headers,
    json={
        "name": "Restored Mission",
        "description": "From backup",
        "drones": [...],      # 恢复无人机
        "targets": [...],     # 恢复目标
        "obstacles": [...],   # 恢复障碍物
        "environment": {...}  # 恢复环境
    }
)
# 返回包含所有已恢复实体的完整会话数据

# 覆盖已有会话，适合用于恢复备份
response = requests.post(f"{API_BASE_URL}/sessions/mission-backup-001?overwrite=true&data=true",
    headers=headers,
    json={
        "name": "Restored Mission (Overwritten)",
        "description": "Replaces existing session",
        "drones": [...],
        "targets": [...]
    }
)
# 删除旧会话，并使用相同 ID 创建新会话

# 获取当前会话及其完整数据
session_data = requests.get(f"{API_BASE_URL}/sessions/current?data=true").json()
# 也可以使用便捷地址
session_data = requests.get(f"{API_BASE_URL}/sessions/current/data").json()

# 更新会话元数据
requests.put(f"{API_BASE_URL}/sessions/{session_id}",
    headers=headers,
    json={"name": "Updated Mission Name", "status": "completed"}
)
```

### 自动充电站

创建具有充电能力的航点目标：

```python
# 创建充电站
requests.post(f"{API_BASE_URL}/targets", json={
    "name": "Charging Station 1",
    "type": "waypoint",
    "position": {"x": 50.0, "y": 50.0, "z": 0.0},
    "radius": 10.0,
    "charge_amount": 30.0  # 即时充电百分比
})

# 无人机位于航点时为其充电
requests.post(f"{API_BASE_URL}/drones/{drone_id}/command", json={
    "command": "charge",
    "parameters": {"charge_amount": 30.0}
})
```

### 碰撞检测

移动无人机前检查障碍物：

```python
# 检查路径是否安全
collision = requests.post(f"{API_BASE_URL}/obstacles/collision/path", json={
    "start": {"x": 0.0, "y": 0.0, "z": 10.0},
    "end": {"x": 100.0, "y": 100.0, "z": 10.0},
    "safety_margin": 5.0
}).json()

if collision:
    print(f"检测到与 {collision['obstacle_name']} 的碰撞")
```

## 项目文件

- **[API_DOCUMENTATION.md](docs/API_DOCUMENTATION.md)**：包含示例的完整 API 参考。
- **[API_REFERENCE.md](docs/API_REFERENCE.md)**：开发者接口快速参考。
- **`BATTERY_SYSTEM.md`**：电池管理系统文档；该文件可能只在部分发布版本中提供。
- **`/client`** 目录：开箱即用的 Python 客户端示例。
- **`/config`** 目录：系统配置，例如电量消耗和设置。
- **`test_*.py`** 文件：API 测试示例。

## 系统要求

- Python 3.8+
- FastAPI
- Uvicorn（ASGI 服务）
- Pygame（用于 UI）
- Pydantic（数据校验）

## 依赖

所有依赖都列在 `requirements.txt` 中：

- fastapi
- uvicorn[standard]
- pygame
- pydantic

## 部署为独立可执行文件

可以使用共享 PyInstaller spec 文件 [`multiuav_plat.spec`](multiuav_plat.spec)，为 Windows、macOS 或 Linux 构建独立可执行文件。由于 PyInstaller 的产物不能跨平台使用，请在目标操作系统上进行构建。

### 前置条件

安装项目依赖和 PyInstaller：

```bash
conda activate multiuav-server
python -m pip install -r requirements.txt
python -m pip install pyinstaller
```

### 构建命令

Windows、macOS 和 Linux 使用相同的命令：

```bash
pyinstaller --clean --noconfirm multiuav_plat.spec
```

生成的可执行文件位于 `dist/` 中。文件名使用 `main.py` 中的紧凑应用版本格式：

- Windows：`dist/MultiUAV-Plat.Server.v0.xx.exe`
- macOS：`dist/MultiUAV-Plat.Server.v0.xx`
- Linux：`dist/MultiUAV-Plat.Server.v0.xx`

### spec 文件包含的内容

共享 spec 文件消除了不同平台之间 `--add-data` 语法的差异，并打包应用运行所需的目录：

- `config/`
- `models/`
- `controllers/`
- `api/`
- `ui/`

它还会收集 `fastapi`、`uvicorn` 和 `pygame` 的包数据与子模块，以及 `api`、`config`、`controllers`、`models` 和 `ui` 下的项目子模块，从而覆盖冻结后的 API 服务和 UI 所使用的导入。

项目包含从 `ui/img/drone.png` 转换得到的原生可执行文件图标：

- Windows：`ui/img/drone.ico`
- macOS：`ui/img/drone.icns`

### 运行编译后的应用

直接运行 `dist/` 中的可执行文件：

```bash
# Windows
.\dist\MultiUAV-Plat.Server.v0.xx.exe

# macOS / Linux
./dist/MultiUAV-Plat.Server.v0.xx
```

支持的命令行选项与从源码运行时相同：

```bash
# 只运行 API
./dist/MultiUAV-Plat.Server.v0.xx --api-only

# 只运行 UI
./dist/MultiUAV-Plat.Server.v0.xx --ui

# 运行 API 服务和带无人机控制的 UI，并跳过启动时的 UI 询问
./dist/MultiUAV-Plat.Server.v0.xx --ui-drone-control

# 只运行带无人机控制的 UI
./dist/MultiUAV-Plat.Server.v0.xx --ui --ui-drone-control

# 自定义主机和端口
./dist/MultiUAV-Plat.Server.v0.xx --host 0.0.0.0 --port 8080

# 当前会话最多保留 10,000 条 HTTP 请求历史记录
./dist/MultiUAV-Plat.Server.v0.xx --api-only --request-history-limit 10000
```

启动后，在 [http://localhost:8000/docs](http://localhost:8000/docs) 打开 API 文档。

### 平台说明

- Windows、macOS 和 Linux 需要分别构建。
- macOS 和 Linux 版本可能需要运行 `chmod +x dist/MultiUAV-Plat.Server.v0.xx`。
- spec 文件会打包 `ui/img/drone.png`，因此冻结版本中的 Pygame 仪表盘和启动对话框仍能显示窗口图标。
- 如果存在平台支持的原生图标文件，spec 会自动设置可执行文件图标。
- Windows 版本使用 `ui/img/drone.ico`，macOS 版本使用 `ui/img/drone.icns`。
- Linux 桌面图标的行为取决于打包格式和桌面环境，而不是仅由 PyInstaller 二进制文件决定。

### 故障排查

如果冻结后的应用无法找到打包文件，请清理后重新构建：

```bash
pyinstaller --clean --noconfirm multiuav_plat.spec
```

如果防病毒软件或平台安全检查阻止程序启动，请在发布前根据目标平台对生成的二进制文件进行签名或公证。

---

## 开发

### 运行测试

```bash
# 测试会话管理
python test_session_isolation.py
python test_session_status.py
python test_session_id_generation.py

# 测试新会话行为
python test_new_session_behavior.py
```

### 项目状态

- ✅ 多无人机管理
- ✅ 会话保存/恢复
- ✅ 充电站
- ✅ 碰撞检测
- ✅ 天气仿真
- ✅ 移动目标
- ✅ 交互式 UI
- ✅ 带 OpenAPI 文档的 RESTful API
- ✅ 独立可执行文件部署

## 许可证

本项目使用 GNU General Public License v3.0（GPL-3.0）许可证。

Copyright (C) 2026 MultiUAV-Plat Server System Project

本程序是自由软件：你可以按照自由软件基金会发布的 GNU 通用公共许可证第 3 版，或你选择的任何更高版本，对其进行再分发和/或修改。

本程序的发布是希望它能够发挥作用，但不提供任何保证；甚至不包含对适销性或特定用途适用性的默示保证。更多详情请参阅 GNU 通用公共许可证。

你应该已经随本程序收到 GNU 通用公共许可证副本。如果没有，请访问 <https://www.gnu.org/licenses/>。

完整许可证文本见仓库根目录中的 [LICENSE](../LICENSE)，或访问 <https://www.gnu.org/licenses/gpl-3.0.html>。

## 贡献

[请在此处补充贡献指南]

## 支持

如果遇到问题、需要提问或希望贡献代码，请查阅项目仓库。

### 目标类型

支持以下目标类型：

- `fixed`：固定点，包含 `position` 和 `radius`。
- `moving`：移动目标，包含 `velocity` 和可选的 `moving_path`。
- `waypoint`：带有 `charge_amount` 的充电站航点。
- `interest`：任务中的兴趣点。
- `circle`：由 `position` 和 `radius` 定义的圆形几何目标；UI 使用带细轮廓的填充圆形进行渲染。
- `polygon`：由绝对坐标顶点列表 `vertices` 定义的多边形几何目标；UI 使用带轮廓的填充多边形进行渲染。选中时会在多边形边界外留出一定边距进行高亮，并将标签放在右上边界外侧以提高可读性。
