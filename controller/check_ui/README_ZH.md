# AI 智能体自动检查 UI 工具

语言：[English](README.md) | **中文**

这是一个独立的 UI 应用，用于借助 AI 智能体自动测试无人机控制任务、监控智能体响应，并检查任务完成结果。

## 功能

- **自动导入会话**：与会话管理器相同，自动从配置的存储文件夹导入会话。
- **多会话与任务选择**：可以从多个会话中选择任务并加入自动测试队列。
- **AI 智能体集成**：自动向 AI 智能体发送命令并监控执行过程。
- **任务完成检查**：使用 `execution_check_apis` 评估任务是否完成。
- **暂停/继续控制**：完整控制测试工作流。
- **强制降落安全措施**：可选择在执行每项任务前让无人机降落。
- **完整结果导出**：将详细统计信息和 MD5 哈希值导出为 JSON。

## 前置条件

1. **API 服务**运行在 8000 端口（默认）。
2. **智能体服务**运行在 18000 端口（参阅 [AGENT_README_API.md](AGENT_README_API.md)）。
3. Python 依赖（已包含在主项目中）：
   - tkinter
   - requests
   - 项目中的所有公共工具（`api_server`、`utils` 等）

## 快速开始

### 方法一：使用启动脚本

```bash
cd check_ui
python run_agent_checker.py
```

### 方法二：直接运行

```bash
cd check_ui
python agent_checker.py
```

### 方法三：从项目根目录运行

```bash
python -m check_ui.agent_checker
```

## 使用指南

### 1. 加载会话和任务

1. 单击 **“Refresh Sessions”** 加载所有可用会话。
   - 应用会自动从设置中配置的存储文件夹导入会话文件。
   - 会话同时从存储文件夹和 API 加载。
   - 为避免重复，只会导入新会话。
2. 从列表中选择一个会话，查看其中的任务。
3. 任务及其状态会显示在任务树中。
4. 使用 **“Filter”** 按关键词筛选可见任务。
   - 匹配不区分大小写。
   - 如果数据中存在，会将任务所属的会话名称/ID、任务名称/ID 和任务类别元数据纳入匹配。
   - 筛选不会改变会话列表、任务队列或已有结果。

**注意**：会话存储文件夹与会话管理器使用的文件夹相同，通过设置进行配置，默认是 `./sessions/`。刷新会话时，该文件夹中的所有 JSON 会话文件都会被自动导入。

### 2. 建立任务队列

1. 在任务树中选择一个或多个任务（按 Ctrl/Cmd 并单击可多选）。
2. 单击 **“Add Selected to Queue”**，将任务添加到检查队列。
3. 可以使用 **“Select All”** / **“Deselect All”** 快速全选或取消全选。
4. 队列会显示所有等待检查的任务。

### 3. 配置选项

- **Force land all drones before each task**：勾选后，每次执行任务命令前都会先让所有无人机降落，作为安全措施。

### 4. 运行自动检查

1. 单击 **“Start”** 开始自动检查。
2. 应用会对队列中的每个任务依次执行：
   - 如果启用了强制降落，则先让所有无人机降落。
   - 向 AI 智能体（18000 端口）发送任务命令。
   - 等待智能体完成，每 5 秒轮询一次状态。
   - 使用 `execution_check_apis` 评估任务完成情况。
   - 记录通过或失败结果。
   - 自动进入下一个任务。
3. 可以通过以下区域监控进度：
   - 进度条显示整体完成度。
   - 当前任务区域显示正在执行的任务。
   - 日志区域显示详细执行步骤。

### 5. 控制工作流

- **Pause**：暂时停止检查，之后可以继续。
- **Resume**：从暂停的位置继续。
- **Stop**：完全停止工作流。
- **Clear Queue**：清空任务队列，仅可在暂停或停止状态使用。

### 6. 导出结果

1. 可以随时单击 **“Export Results”**。
2. 选择 JSON 文件的保存位置。
3. 导出内容包括：
   - 总体统计信息，如通过率和任务总数。
   - 每项任务的结果和详细检查信息。
   - 时间戳和错误消息。
   - 作为唯一 ID 的 MD5 哈希值。

## 导出格式

```json
{
  "id": "md5_hash_of_results",
  "export_timestamp": "2025-12-26T10:30:00",
  "tool": "AI Agent Auto-Check",
  "statistics": {
    "total_tasks": 10,
    "passed_tasks_count": 8,
    "failed_tasks_count": 2,
    "task_pass_rate": 0.8,
    "total_checks": 45,
    "passed_checks": 40,
    "failed_checks": 5,
    "check_pass_rate": 0.8889
  },
  "results": [
    {
      "session_id": "session-uuid",
      "session_name": "Test Session",
      "task_id": "task-uuid",
      "task_name": "Task Name",
      "status": "passed",
      "timestamp": "2025-12-26T10:25:30",
      "error": null,
      "statistics": {
        "total_checks_apis": 5,
        "passed_checks_apis": 5,
        "failed_checks_apis": 0,
        "pass_rate": 1.0
      },
      "details": [...]
    }
  ]
}
```

## 架构

### 文件结构

```text
check_ui/
├── __init__.py              # 包初始化
├── README.md                # 英文说明
├── README_ZH.md             # 中文说明
├── AGENT_README_API.md      # 智能体 API 文档
├── agent_client.py          # 智能体 API 客户端封装
├── agent_checker.py         # 主 UI 应用
└── run_agent_checker.py     # 启动脚本
```

### 核心组件

1. **AgentClient**（`agent_client.py`）
   - 负责与智能体服务（18000 端口）通信。
   - 负责异步任务提交和状态轮询。
   - 提供健康检查和错误处理。

2. **AgentCheckerApp**（`agent_checker.py`）
   - Tkinter 主 UI 应用。
   - 会话和任务选择界面。
   - 基于线程的自动检查工作流。
   - 任务完成评估，复用 `gui_controller.py` 中的逻辑。
   - 结果导出功能。

3. **API 集成**
   - 复用主项目中的 `api_server.py`。
   - 新增 `api_land_all_drones()` 方法，用于强制降落。
   - 使用现有的检查评估逻辑。

## 工作流详情

### 单项任务的检查过程

1. **准备**
   - 如果启用了强制降落：调用 `POST /drones/land_all`。
   - 将会话设为当前会话：`POST /sessions/{id}/set-current`。

2. **获取任务命令**
   - 获取任务数据：`GET /sessions/{session_id}/tasks/{task_id}`。
   - 从任务正文或别名中随机选择一条命令。

3. **智能体执行**
   - 提交命令：`POST http://localhost:18000/agent/command/async`。
   - 从响应中取得 `job_id`。
   - 每 5 秒轮询状态：`GET http://localhost:18000/agent/jobs/{job_id}`。
   - 等待状态变为 `completed` 或 `failed`。

4. **任务检查**
   - 递归评估 `execution_check_apis`。
   - 支持 AND/OR/NOT 逻辑组。
   - 调用各项检查 API。
   - 将结果与期望值进行比较。
   - 记录详细的通过/失败信息。

5. **记录结果**
   - 保存状态、详情和时间戳。
   - 所有检查通过时，将任务标记为已完成。
   - 将结果记录到 UI 日志中。

## 配置

应用通过 `get_settings()` 使用共享的 `settings.json`：

- `api_base_url`：无人机 API 的基础 URL，默认为 `http://127.0.0.1:8000`。
- `agent_base_url`：智能体 API 的基础 URL，默认为 `http://localhost:18000`。
- `api_key`：用于身份验证的 API 密钥。

## 故障排查

### 智能体服务不可用

- 确认 `agent_server.py` 正在运行：`python agent_server.py`。
- 检查 18000 端口是否被阻止。
- 检查智能体服务健康状态：`curl http://localhost:18000/health`。

### API 服务连接问题

- 确认 `api_server.py` 正在 8000 端口运行。
- 检查设置中的 API 密钥。
- 检查网络连接。

### 无法加载任务

- 确认 API 中存在会话。
- 检查 API 身份验证。
- 尝试单击 “Refresh Sessions”。

### 检查卡住或超时

- 每项任务的默认超时时间为 300 秒（5 分钟）。
- 智能体命令通常可能需要 1～3 分钟。
- 查看智能体服务日志中的错误。
- 使用 “Stop” 按钮取消。

## 与主项目的集成

这个工具被设计为可以**独立运行**，但会**复用**主项目中的现有功能：

- **复用模块**：`api_server.py`、`utils.py`、`app_settings.py`。
- **复用逻辑**：`gui_controller.py` 中的任务检查算法。
- **新增功能**：`api_server.py` 中的 `api_land_all_drones()` 方法。
- **无破坏性改动**：所有代码都隔离在 `check_ui/` 文件夹中。

## 开发说明

### 添加功能

代码采用模块化设计，可以通过以下方式扩展：

- 修改 `AgentClient`，支持新的智能体 API 功能。
- 在 `setup_ui()` 方法中添加 UI 面板。
- 在 `check_single_task()` 中扩展检查逻辑。
- 在 `export_results()` 中自定义导出格式。

### 线程模型

- 主 UI 运行在 Tkinter 主线程中。
- 检查工作流运行在后台线程 `worker_thread` 中。
- UI 更新通过 `root.after(0, callback)` 执行，以保证线程安全。
- 暂停/继续功能通过轮询 `is_paused` 标志实现。

## 许可证

本工具属于无人机控制系统项目的一部分。

## 支持

如果遇到问题：

1. 查看智能体服务文档：[AGENT_README_API.md](AGENT_README_API.md)。
2. 查看主项目文档。
3. 检查应用日志中的错误详情。
