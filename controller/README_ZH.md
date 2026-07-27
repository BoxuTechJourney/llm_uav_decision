# MultiUAV-Plat 控制系统——GUI 控制器

语言：[English](README.md) | **中文**

这是一个通过 RESTful API 控制无人机的 Python GUI 应用。系统提供直观的图形界面，用于管理会话、无人机、目标和环境。

## 功能

### 会话管理

- **创建会话**：使用自定义名称和描述创建新会话。
- **加载会话**：加载已有会话并在不同会话之间切换。
- **导出/导入会话**：将会话保存为 JSON 文件，并在之后重新加载。
- **会话详情**：查看会话统计信息，包括无人机、目标和障碍物数量。
- **删除会话**：移除不再需要的会话。

### 无人机管理

- **无人机管理**：添加无人机，并发送起飞、降落、移动和紧急处理等命令。
- **目标管理**：创建航点、移动目标和固定观测目标。
- **环境管理**：创建和管理不同的天气环境。
- **实时更新**：刷新数据，查看无人机的当前状态和位置。
- **友好界面**：使用选项卡和易于操作的对话框。

## 前置条件

运行 GUI 控制器前，请确认：

1. 已安装 Python 3.7 或更高版本。
2. MultiUAV-Plat 控制系统 API 服务正在 `http://127.0.0.1:8000` 上运行。

## 安装

1. 安装所需依赖：

```bash
pip install -r requirements.txt
```

注意：Python 通常自带 `tkinter`。如果遇到问题，可能需要根据操作系统单独安装。

## 使用方法

### 启动应用

应用现在会先打开会话管理器，让你在进入主 GUI 控制器之前管理会话：

```bash
python main.py
```

也可以直接启动 GUI 控制器，但此时需要通过 API 管理会话：

```bash
python gui_controller.py
```

### 会话管理工作流

1. **启动应用**：运行 `python main.py` 打开会话管理器。
2. **创建或选择会话**：
   - 使用 “Create New Session” 创建会话。
   - 从列表中选择已有会话。
   - 从 JSON 文件导入会话。
3. **启动会话**：双击会话，或单击 “Launch Session” 进入主 GUI。
4. **返回会话管理器**：退出主 GUI 后，会返回会话管理器。

### 会话管理器功能

#### 会话操作

- **Create New Session**：使用自定义名称、描述和可选示例数据创建会话。
- **Launch Session**：进入所选会话的主 GUI 控制器。
- **Load Session**：查看完整会话数据，包括无人机、目标、障碍物和环境。
- **Delete Session**：删除不再需要的会话，操作前会要求确认。
- **Export Session**：使用增强的 `/data` 接口，将完整会话数据保存为 JSON 文件。
- **Import Session**：使用新的 `/restore` 接口，从 JSON 文件恢复会话数据。
- **Refresh**：从 API 获取最新数据并更新会话列表。

#### 会话详情面板

选择会话后，可以查看：

- 会话名称和状态。
- 描述。
- 无人机、目标和障碍物数量。
- 创建时间。

### 界面概览

应用包含三个主要选项卡。

#### 1. 无人机选项卡

- **View Drones**：列出所有已注册无人机及其状态、电量和位置。
- **Add Drone**：使用自定义参数注册新无人机。
- **Take Off**：命令选定无人机起飞到指定高度。
- **Land**：命令选定无人机降落。
- **Move To**：将选定无人机移动到指定坐标 `(x, y, z)`。
- **Emergency**：让选定无人机执行紧急降落。
- **Refresh**：使用最新数据更新无人机列表。

#### 2. 目标选项卡

- **View Targets**：列出所有目标及其类型和位置。
- **Add Waypoint**：创建静态航点目标。
- **Add Moving Target**：创建按照指定速度移动的目标。
- **Add Fixed**：创建固定目标，也用于表示兴趣点。
- **Delete Target**：删除选定目标。
- **Refresh**：更新目标列表。

#### 3. 环境选项卡

- **View Environments**：列出所有环境及其天气条件。
- **Create Environment**：使用自定义条件创建天气环境。
- **Set as Current**：将选定环境设为当前环境。
- **Delete Environment**：删除选定环境。
- **Refresh**：更新环境列表。

### 操作步骤

1. **启动 API 服务**：确认 MultiUAV-Plat 控制系统 API 正在 8000 端口运行。
2. **启动应用**：运行 `python main.py` 打开会话管理器。
3. **管理会话**：创建新会话或选择已有会话。
4. **启动 GUI**：双击会话或单击 “Launch Session” 进入主控制器。
5. **添加无人机**：使用 “Add Drone” 注册无人机。
6. **控制无人机**：在列表中选择无人机，然后使用控制按钮。
7. **管理目标**：切换到目标选项卡，创建航点和任务目标。
8. **设置环境**：在环境选项卡中创建并启用天气条件。
9. **退出会话**：关闭主 GUI，返回会话管理器。

### 示例工作流

1. **创建并启动会话**
   - 运行 `python main.py` 启动会话管理器。
   - 单击 “Create New Session”，填写名称和描述。
   - 选择新会话，然后单击 “Launch Session”。

2. **添加新无人机**
   - 在无人机选项卡中单击 “Add Drone”。
   - 填写无人机参数，包括名称、型号、能力和初始位置。
   - 单击 “Add Drone” 完成注册。

3. **起飞并移动**
   - 从列表中选择无人机。
   - 单击 “Take Off”，指定高度，例如 10 米。
   - 单击 “Move To”，指定目标坐标。
   - 在列表中监控无人机状态。

4. **创建目标**
   - 切换到目标选项卡。
   - 单击 “Add Waypoint” 创建导航点。
   - 单击 “Add Moving Target” 创建动态目标。
   - 使用 “Add POI” 创建观测点。

5. **设置环境**
   - 切换到环境选项卡。
   - 单击 “Create Environment” 定义天气条件。
   - 选择环境并单击 “Set as Current”。

6. **导出会话**
   - 退出主 GUI，返回会话管理器。
   - 选择会话并单击 “Export Session” 保存工作成果。
   - 导出内容包含完整会话数据：无人机、目标、障碍物和环境。

7. **导入会话**
   - 单击 “Import Session”，恢复之前导出的会话。
   - 系统兼容新旧两种导出格式。
   - 完整恢复会包含所有关联数据。

### 增强的会话管理

会话管理器已使用新的 API 接口改进相关功能。

#### 导出功能

- **完整数据导出**：使用 `/sessions/{id}/data` 接口导出全部会话数据。
- **导出元数据**：包含导出时间戳和版本信息。
- **详细日志**：记录导出内容的完整信息。
- **用户反馈**：显示带有导出统计信息的详细成功消息。

#### 导入功能

- **会话恢复**：使用新的 `/sessions/restore` 接口完整恢复会话。
- **向后兼容**：支持新旧两种导出文件格式。
- **完整数据导入**：恢复无人机、目标、障碍物和环境数据。
- **导入校验**：校验导入数据并提供详细反馈。
- **冲突处理**：处理导入时发生的会话名称冲突。

#### 加载会话功能

- **查看数据**：通过新的 “Load Session” 按钮查看完整会话数据。
- **增强显示**：在格式化、可滚动的窗口中展示会话数据。
- **详细日志**：记录所加载会话内容的完整信息。
- **状态更新**：加载期间提供详细状态信息。

### 使用的 API 接口

应用会访问以下 API 接口。

#### 会话管理

- **会话**：`/sessions`、`/sessions/{id}`、`/sessions/{id}/set-current`
- **会话数据**：`/sessions/{id}/data`，用于完整数据导出。
- **会话恢复**：`/sessions/restore`，用于导入完整会话数据。

#### 主 GUI 控制器

- **无人机**：`/drones`、`/drones/{id}/command`
- **目标**：`/targets`、`/targets/{id}`
- **环境**：`/environments`、`/environments/{id}/set-current`

### 错误处理

- API 服务未运行时会显示连接错误。
- 输入校验会确保坐标和参数使用正确的数据类型。
- 状态栏会显示当前操作状态和结果。

### 故障排查

**“Could not connect to the API server”**

- 确认 MultiUAV-Plat 控制系统 API 正在 `http://127.0.0.1:8000` 运行。
- 在浏览器中访问 `http://127.0.0.1:8000/docs`，检查服务是否可用。

**“No Selection” 警告**

- 使用控制按钮前，请先在列表中选择一个对象。

**“Invalid Input” 错误**

- 确认数字字段中包含有效数字。
- 检查必填字段是否为空。

## 功能详解

### 无人机命令

- **Take Off**：让无人机起飞到指定高度。
- **Land**：让无人机下降到地面。
- **Move To**：让无人机飞往指定三维坐标。
- **Emergency**：立即执行紧急降落流程。

### 目标类型

- **Waypoint**：静态导航点。
- **Moving**：带有速度向量的移动目标。
- **Fixed**：静态观测目标或任务目标，也用于替代原有兴趣点。

### 环境条件

- 天气类型：晴朗、多云、下雨、暴风、雾、雪。
- 风向：八方位罗盘方向，如北、东北等。
- 可配置温度、湿度、风速和能见度。

## 开发

GUI 使用 Python 的 tkinter 库构建，并采用模块化设计：

- `UAVControllerGUI`：主应用类。
- `DroneDialog`：添加无人机的对话框。
- `MoveToDialog`：发送无人机移动命令的对话框。
- `TargetDialog`：创建目标的对话框。
- `EnvironmentDialog`：创建环境的对话框。
- `utils.py`：共享工具，包括日志、对话框辅助函数、会话 API 辅助函数和编辑器数学函数。

所有 API 通信都通过 `make_request()` 方法处理，并提供适当的错误处理和用户反馈。

### 日志系统

应用使用统一日志系统，确保会话管理器和 GUI 控制器写入同一个日志文件。

#### 共享日志功能

- **单一日志文件**：`session_manager.py` 和 `gui_controller.py` 都写入同一个带时间戳的日志文件 `logs/uav_system_YYYYMMDD_HHMMSS.log`。
- **模块标识**：日志条目包含模块名称（SessionManager 或 UAVController），便于识别。
- **统一格式**：日志统一包含时间戳、级别、模块、函数、行号和消息。
- **双重输出**：日志同时写入文件和控制台，便于开发。
- **自动创建目录**：如果 `logs/` 目录不存在，系统会自动创建。

#### 日志格式

```text
2025-07-20 22:38:13 - INFO - [SessionManager:setup_logging:61] - Session Manager started
2025-07-20 22:38:13 - INFO - [UAVController:setup_logging:38] - UAV Controller GUI started
```

#### 使用方式

任一模块启动时都会自动配置共享日志，无需手动设置。日志文件保存在 `logs/` 目录中，并自动加入时间戳以避免冲突。

## 使用 PyInstaller 构建可执行文件

可以使用 [PyInstaller](https://pyinstaller.org/) 在任意平台上将应用打包为独立可执行文件。

### 前置条件

1. 安装 PyInstaller：

```bash
pip install pyinstaller
```

2. 确认已安装所有依赖：

```bash
pip install -r requirements.txt
```

### 构建可执行文件

**重要**：应用使用动态导入模块 `session_editor` 和 `session_editor_dialogs`，PyInstaller 无法自动检测它们。必须使用项目提供的 spec 文件，确保这些模块被包含在内。

#### 推荐方法（所有平台）

使用随项目提供的 `uav_controller.spec`：

```bash
pyinstaller uav_controller.spec
```

可执行文件会生成在 `dist/` 目录中。

#### 各平台注意事项

**Windows**

- spec 文件使用 `img/controller.ico` 作为图标。
- 为获得最佳结果，请确认 `img/` 目录中存在 `controller.ico`。
- 可执行文件为 `dist/uav_controller.exe`。

**macOS**

- spec 文件使用 `img/controller.png` 作为图标。
- 为获得最佳结果，可转换为 `.icns` 格式并创建 `img/controller.icns`。
- Gatekeeper 可能要求为发布版本执行代码签名。
- 如需生成窗口应用包，请在 spec 文件中将 `console=True` 改为 `console=False`。

**Linux**

- 可执行文件为 `dist/uav_controller`，格式是 ELF 二进制。
- 确认文件具有执行权限：`chmod +x dist/uav_controller`。
- 如果缺少 tkinter，请安装操作系统提供的相关软件包。

### 备选方法：手动构建（不推荐）

如果不使用 spec 文件进行构建，`session_editor` 功能可能无法正常工作。

**Windows**

```powershell
pyinstaller --noconfirm --clean --onefile --add-data "./logs;logs" --add-data "./img;img" --hidden-import=session_editor --hidden-import=session_editor_dialogs --icon "img/controller.ico" --name "uav_controller" main.py
```

**macOS/Linux**

```bash
pyinstaller --noconfirm --clean --onefile --add-data "./logs:logs" --add-data "./img:img" --hidden-import=session_editor --hidden-import=session_editor_dialogs --icon "img/controller.png" --name "uav_controller" main.py
```

### PyInstaller 构建故障排查

**可执行文件中无法打开会话编辑器**

- 原因是 `session_editor.py` 没有包含在应用包中。
- **解决方法**：始终使用 `uav_controller.spec`，不要使用手动命令。
- spec 文件会明确包含所有动态导入的模块。

**缺少 tkinter 或 GUI 库**

- 安装系统软件包：Debian/Ubuntu 使用 `python3-tk`，其他系统可使用 `tk`。
- 构建前确认 tkinter 正常工作：`python -m tkinter`。

**没有显示图标**

- Windows：使用 `.ico` 格式，即 `img/controller.ico`。
- macOS：使用 `.icns` 格式，即 `img/controller.icns`。
- Linux：使用 `.png` 格式，即 `img/controller.png`。

### 分发

- `dist/` 中生成的可执行文件是独立程序，可以直接分发。
- 目标机器应满足以下条件：
  - 可以访问 MultiUAV-Plat API 服务。
  - 能够连接 `http://127.0.0.1:8000`，或连接配置的其他服务地址。
- 用于生产部署时，请在设置中更新 API 服务 URL。

### 提示

- 建议从虚拟环境中运行构建，隔离依赖。
- spec 文件会自动包含项目目录中的所有 Python 模块。
- 日志会创建在相对于可执行文件的 `logs/` 目录中。
- 如需自定义构建，请编辑注释完善的 `uav_controller.spec`。
