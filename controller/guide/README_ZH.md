# 用户指南

语言：[English](README.md) | **中文**

本文件夹包含 MultiUAV-Plat 控制系统各个 UI 工具的实用用户指南。

如需了解整个项目，请参阅上级目录中的 [README_ZH](../README_ZH.md)。如需了解 API 详情，请参阅 [API 文档](../API_doc/API_DOCUMENTATION.md)。

## 前置条件

在项目根目录安装依赖：

```bash
pip install -r requirements.txt
```

使用 GUI 工具前，请先启动无人机 API 服务：

```bash
python api_server.py
```

默认 API 地址为 `http://127.0.0.1:8000`。如果你的本地配置不同，请在会话管理器中打开 `Settings` 进行修改。

## 启动主应用

启动会话管理器：

```bash
python main.py
```

建议从会话管理器开始使用系统。你可以在其中创建会话、启动控制器、打开可视化编辑器、创建任务，以及运行 AI 智能体检查。

## 指南目录

1. [会话管理器](session-manager.md)
2. [会话 GUI 控制器](session-gui-controller.md)
3. [会话编辑器](session-editor.md)
4. [任务生成器](task-generator.md)
5. [AI 智能体检查器](ai-agent-checker.md)

## 推荐工作流程

1. 运行 `python main.py`，打开[会话管理器](session-manager.md)。
2. 创建、导入、克隆或选择一个会话。
3. 需要可视化放置无人机、目标或障碍物时，使用 `Edit`。
4. 使用 `Launch` 打开[会话 GUI 控制器](session-gui-controller.md)，执行详细的会话操作。
5. 通过[任务生成器](task-generator.md)手动添加任务、根据模板添加任务，或随机生成任务。
6. 使用 [AI 智能体检查器](ai-agent-checker.md)让智能体执行队列中的任务并导出结果。

## 常见问题排查

- 如果 UI 无法连接，请确认 `python api_server.py` 正在运行，并检查 `http://127.0.0.1:8000/docs` 是否可以访问。
- 如果模板操作没有显示兼容选项，请检查当前会话是否包含所选模板要求的无人机、目标或障碍物。
- 如果 AI 检查器无法运行任务，请确认无人机 API 服务和智能体服务都已启动。
