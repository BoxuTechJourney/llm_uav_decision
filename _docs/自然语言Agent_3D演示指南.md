# 自然语言 Agent + 3D 可视化 Demo 演示指南

文中相对路径和命令均以仓库根目录作为工作目录。

本文档用于下次演示时快速复现“用自然语言控制无人机，并在 3D 可视化环境中查看执行效果”的流程。

适用环境：

- Windows PowerShell
- conda 环境：`llm_uav_decision`
- 仓库根目录：`C:\Users\Administrator\Desktop\Code\multi_uav_decision`
- UAV Server：`http://127.0.0.1:8000`
- Agent API：`http://127.0.0.1:18000`
- 3D Viewer：`http://127.0.0.1:5173`

安全要求：

- 不把真实 LLM API key 写入本文档。
- 不把真实系统权限 key 写入本文档。
- `API_key.txt`、`agent4drone/llm_settings.json` 只作为本地配置使用，不要提交到 Git。
- `agent4drone/llm_settings.json` 必须保存为 UTF-8 无 BOM。

## 1. 演示前检查

打开 PowerShell，进入仓库根目录：

```powershell
cd C:\Users\Administrator\Desktop\Code\multi_uav_decision
```

激活 conda 环境：

```powershell
& "$env:USERPROFILE\miniconda3\shell\condabin\conda-hook.ps1"
conda activate llm_uav_decision
python --version
```

预期结果：

- `python --version` 显示 Python 3.11。
- 不要使用 `C:\Users\Administrator\anaconda3\python.exe` 作为本项目运行解释器。

检查关键 Python 包：

```powershell
python -c "import fastapi, uvicorn, pygame, requests, shapely, langchain, langchain_openai, langchain_ollama, matplotlib; print('imports ok')"
```

如果这里报 `No module named shapely`，通常说明当前 PowerShell 没有激活 `llm_uav_decision`，或者 `python` 指向了错误解释器。

## 2. LLM 配置检查

Agent API 启动前，需要确保本地存在：

```text
agent4drone/llm_settings.json
```

该文件应由本地配置生成或手动维护，不应提交到 Git。

如果本地测试使用 `API_key.txt`，建议只在本机读取，不要复制真实 key 到文档、README 或提交记录中。

如果启动 Agent API 时出现：

```text
Unexpected UTF-8 BOM
```

说明 `agent4drone/llm_settings.json` 带 BOM，需要重新保存为 UTF-8 无 BOM。可用 PowerShell 修复编码：

```powershell
$path = "agent4drone\llm_settings.json"
$content = Get-Content -LiteralPath $path -Raw -Encoding UTF8
[System.IO.File]::WriteAllText((Resolve-Path $path), $content, [System.Text.UTF8Encoding]::new($false))
```

## 3. 启动三端服务

建议打开 3 个 PowerShell 窗口，每个窗口都先进入仓库根目录并激活 conda 环境。

### 3.1 启动 UAV Server

窗口 1：

```powershell
cd C:\Users\Administrator\Desktop\Code\multi_uav_decision
conda activate llm_uav_decision
cd server
python main.py --api-only --host 127.0.0.1 --port 8000
```

另开一个 PowerShell 检查：

```powershell
Invoke-RestMethod http://127.0.0.1:8000/version
```

能返回版本信息即为正常。

### 3.2 启动 Agent API

窗口 2：

```powershell
cd C:\Users\Administrator\Desktop\Code\multi_uav_decision
conda activate llm_uav_decision
cd agent4drone
python agent_api_service.py
```

检查：

```powershell
Invoke-RestMethod http://127.0.0.1:18000/health
```

如果 `health` 返回可用状态，说明 Agent API 已启动。

### 3.3 启动 3D Viewer

窗口 3：

```powershell
cd C:\Users\Administrator\Desktop\Code\multi_uav_decision\view3d
npm run dev
```

浏览器打开：

```text
http://127.0.0.1:5173
```

注意：

- 3D Viewer 页面主要负责可视化，不负责自然语言输入。
- 自然语言任务通过 Agent API 提交。
- 如果 3D 页面只显示静态示例数据，通常是没有成功连接后端。

如果 Viewer 访问后端接口需要系统权限 key，可以只在当前 PowerShell 会话中设置环境变量，不要写入文档或提交文件：

```powershell
$prefix = "s" + "ys_"
$pattern = '"' + [regex]::Escape($prefix) + '[^"]+"'
$line = Select-String -Path ..\server\config\privilege_keys.py -Pattern $pattern | Select-Object -First 1
$env:VITE_API_BASE_URL = "http://127.0.0.1:8000"
$env:VITE_API_KEY = $line.Matches[0].Value.Trim('"')
npm run dev
```

## 4. 用自然语言控制无人机

3D Viewer 启动后，使用 PowerShell 调用 Agent API 下发自然语言任务。

可以在一个新的 PowerShell 窗口中定义 helper：

```powershell
function Send-UavAgentCommand {
  param(
    [Parameter(Mandatory=$true)]
    [string]$Command
  )

  $body = @{ command = $Command } | ConvertTo-Json
  $job = Invoke-RestMethod `
    -Uri "http://127.0.0.1:18000/agent/command/async" `
    -Method Post `
    -ContentType "application/json" `
    -Body $body

  Write-Host "Job ID:" $job.job_id

  do {
    Start-Sleep -Seconds 3
    $status = Invoke-RestMethod "http://127.0.0.1:18000/agent/jobs/$($job.job_id)"
    Write-Host "Status:" $status.status
  } while ($status.status -in @("queued", "running"))

  $status.result.output
}
```

### 示例 1：单机移动

```powershell
Send-UavAgentCommand "让 Drone 1 起飞到 20 米，然后向东移动 30 米。完成后汇报当前位置。"
```

观察 3D Viewer 中 Drone 1 的位置变化。

### 示例 2：双机移动演示

```powershell
Send-UavAgentCommand "让两架空闲无人机起飞到 20 米，并分别向不同方向移动 25 米，方便我在 3D 中观察轨迹。"
```

适合演示自然语言任务拆解和多无人机可视化。

### 示例 3：读取并完成当前任务

```powershell
Send-UavAgentCommand "读取当前会话中的下一个待完成任务，执行它，检查是否通过。如果通过，就把任务标记为完成。"
```

如果当前会话没有任务，接口可能返回空任务列表。这不是 Agent 启动失败，而是当前 session 没有配置待完成任务。

## 5. 障碍物避让演示

之前演示中，用户要求：

```text
让 drone1 飞到 Obstacle · Polygon Obstacle 1 上去
```

如果直接让无人机低空直线飞向目标点，可能出现中途碰撞或视觉上穿过障碍物的问题。

关键原因：

- 目标点在障碍物上方，不代表整条飞行路径安全。
- `move_to` 类动作如果按单段直线执行，中间路径可能穿过其它高障碍物。
- 对障碍物演示，应明确要求“先升高、再水平移动、最后下降”。

推荐自然语言指令：

```powershell
Send-UavAgentCommand "让 Drone 1 飞到 Polygon Obstacle 1 上方。要求先爬升到 90 米安全高度，再在 90 米高度水平移动到目标上方，最后垂直下降到目标上方 10 米处。不要使用低空直线穿越障碍物。完成后汇报最终位置。"
```

演示讲解点：

- 90 米是安全巡航高度示例，用于避开当前场景中的高障碍物。
- 最终下降点应仍保持在障碍物顶部以上。
- 如果场景变化，应先读取障碍物高度，再选择高于相关障碍物的安全高度。

## 6. 任务完成检查

如果只是让无人机移动，Agent 可能完成了动作，但系统任务列表仍然为空或未变化。

检查当前任务：

```powershell
Invoke-RestMethod http://127.0.0.1:8000/sessions/current/tasks
```

检查下一个任务：

```powershell
Invoke-RestMethod http://127.0.0.1:8000/sessions/current/tasks/next
```

如果有任务 ID，可以检查任务是否通过：

```powershell
$taskId = "TASK_ID_PLACEHOLDER"
Invoke-RestMethod "http://127.0.0.1:8000/sessions/current/tasks/$taskId/check"
```

通过后标记完成：

```powershell
$taskId = "TASK_ID_PLACEHOLDER"
Invoke-RestMethod `
  -Uri "http://127.0.0.1:8000/sessions/current/tasks/$taskId/mark-done" `
  -Method Post
```

实际 demo 中，如果需要展示“任务完成”，应提前创建带检查条件的任务，例如检查某架无人机是否到达指定坐标附近。

## 7. 常见故障排查

### 7.1 `No module named shapely`

原因：

- 当前 PowerShell 没有激活 `llm_uav_decision`。
- 或者 `python` 指向了错误环境。

处理：

```powershell
conda activate llm_uav_decision
python -c "import shapely; print(shapely.__version__)"
```

### 7.2 `No module named encodings`

原因：

- 系统正在使用异常的 Anaconda Python。
- Python 前缀被错误解析到项目目录。

处理：

```powershell
& "$env:USERPROFILE\miniconda3\envs\llm_uav_decision\python.exe" --version
```

后续启动服务时优先使用该环境中的 Python。

### 7.3 `Unexpected UTF-8 BOM`

原因：

- `agent4drone/llm_settings.json` 文件编码带 BOM。

处理：

- 重新保存为 UTF-8 无 BOM。
- 可参考本文“LLM 配置检查”中的 PowerShell 修复命令。

### 7.4 npm 报 `'VITE_VIEWER_DATA_SOURCE' 不是内部或外部命令`

原因：

- Windows PowerShell 不支持 Unix 风格的 `NAME=value command` 写法。

处理：

- `package.json` 中应使用 `cross-env`。
- 如已安装依赖，直接运行：

```powershell
npm run dev
```

### 7.5 3D 页面没有实时数据或接口返回 403

原因：

- Viewer 未连接到 UAV Server。
- 或缺少访问 `/sessions/current/data` 所需的系统权限 key。

处理：

- 确认 UAV Server 正在运行。
- 确认 Vite 启动前已设置 `VITE_API_BASE_URL` 和 `VITE_API_KEY`。
- 不要把真实权限 key 写入文档或提交文件。

### 7.6 Agent 连接 LLM 失败

常见原因：

- `API_key.txt` 中同时包含 provider 名和真实 key，但配置时把整个文件内容当成 key。
- `llm_settings.json` 中选择的 provider 与 key 不匹配。
- 本地网络或 LLM 服务端不可达。

处理：

- 只把真实 key 内容写入对应 provider 的 `api_key` 字段。
- provider 名只用于选择配置，不应进入 Authorization header。
- 重启 Agent API 后再次调用 `/health` 和自然语言任务。

## 8. 推荐 demo 流程

正式演示时按以下顺序执行：

1. 打开 3 个 PowerShell 窗口。
2. 分别启动 UAV Server、Agent API、3D Viewer。
3. 浏览器打开 `http://127.0.0.1:5173`。
4. 用 `Send-UavAgentCommand` 下发一个简单移动任务。
5. 在 3D Viewer 中观察无人机移动。
6. 下发双机移动任务，展示自然语言多无人机控制。
7. 下发障碍物上方飞行任务，强调安全高度和分段路径。
8. 如需展示任务完成，提前准备带检查条件的任务，再让 Agent 执行、检查并标记完成。

最小可演示命令：

```powershell
Send-UavAgentCommand "让 Drone 1 起飞到 20 米，然后向东移动 30 米。完成后汇报当前位置。"
```

障碍物安全演示命令：

```powershell
Send-UavAgentCommand "让 Drone 1 飞到 Polygon Obstacle 1 上方。要求先爬升到 90 米安全高度，再在 90 米高度水平移动到目标上方，最后垂直下降到目标上方 10 米处。不要使用低空直线穿越障碍物。完成后汇报最终位置。"
```
