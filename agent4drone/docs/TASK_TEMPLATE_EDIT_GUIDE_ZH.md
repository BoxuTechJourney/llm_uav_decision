# 任务模板编辑指南（单一来源）

这是创建、编辑和使用任务模板的一站式指南。它整合了所有占位符和模板文档，因此其他 Markdown 文件可以安全移除。

## 1) 模板系统的作用
- 通过可复用的模板（内置或自定义）快速生成任务。
- 将模板本地存储于 `./templates/task_templates.json`。内置模板受到保护，无法删除。
- 在内容、内容别名及相关 API 参数中应用占位符替换。
- 支持单实体、多实体（索引化）、数组和随机占位符，具备粘性/随机化行为。

## 2) 在图形界面中使用模板
1. 打开 **任务模板** 浏览器（任务选项卡 → “来自模板”）。
2. 选择一个模板查看其描述/内容；双击或点击 **使用模板**。
3. 在 **自定义模板** 中：
- 设置任务名称（必填）。
- 填写无人机/目标/障碍物的实体下拉菜单（或选择 `[RANDOM]` 或 `[ORDERED]`）。
- 为其他占位符输入值；随机占位符无需输入。
- 创建者默认为设置中的用户名。
4. 点击 **创建任务** 生成一个任务，或 **批量创建** 生成多个（名称将自动编号）。在任务创建前，会应用占位符替换。

## 3) 模板结构（JSON 字段）
```json
{
  "name": "Template Name",                // required
  "description": "Short summary",
  "content": "Main task text with {placeholders}",
  "content_aliases": ["Alt phrasing 1", "Alt phrasing 2"],
  "difficulty": "easy|medium|hard",
  "creator": "Creator Name",
  "category": "Category Name",
  "is_builtin": true|false,
  "related_apis": [
    {
      "method": "POST",
      "path": "/drones/{drone_1_id}/command/move_to",
      "parameters": {
        "id": "{drone_1_id}",
        "x": "{random_x}",
        "y": "{random_y}",
        "z": "{random_altitude}"
      }
    }
  ]
}
```
- 模板位于 `~/.multiuav/templates/`；可使用图形界面编辑器或直接编辑 JSON。
- 系统会自动添加 `created_at` 和 `last_modified` 时间戳。

## 4) 占位符参考（所有支持类型）

### A) 单实体标识符
- 无人机：`{drone_id}`, `{drone_name}`
- 目标：`{target_id}`, `{target_name}`
- 障碍物：`{obstacle_id}`, `{obstacle_name}`

### B) 多实体索引化标识符（按索引粘性）
- 无人机：`{drone_1_id}`…`{drone_5_id}`, `{drone_1_name}`…`{drone_5_name}`
- 目标：`{target_1_id}`…`{target_3_id}`, `{target_1_name}`…`{target_3_name}`
- 障碍物：`{obstacle_1_id}`…`{obstacle_3_id}`, `{obstacle_1_name}`…`{obstacle_3_name}`
- 界面会为任何索引配对（`_id` / `_name`）显示下拉菜单。选择 `[RANDOM]` 时，尽可能选取唯一实体；选择 `[ORDERED]` 时，按列表顺序循环选取实体（1..n，然后回到 1）。相同的索引在出现之处均会被复用。

### C) 用户提供 / 自由格式
- 任何不匹配上述规则的占位符（如 `{mission_name}`、`{area}`）会在自定义对话框中提示手动输入。

### D) 随机数占位符

**粘性（同一任务中所有出现均重复使用相同值）：**
- **预定义的粘性随机量：**
- `{random_altitude}`, `{random_distance}`, `{random_speed}`, `{random_heading}`
- `{random_x}`, `{random_y}`, `{random_z}`, `{random_hovertime}`, `{random_duration}`
- **命名变量（粘性）：**
- `{random_var:min:max}`：命名随机浮点数
- `{random_var:min:max:decimals}`：带小数位的命名随机浮点数
- `{randint_var:min:max}`：命名随机整数
- `{randx_var}`, `{randy_var}`, `{randz_var}`：命名坐标变量（可附带范围）

**匿名（每次出现均生成新值）：**
- **基础坐标（无碰撞避免）：**
- `{randx}`：随机 X 坐标（0-1024）
- `{randy}`：随机 Y 坐标（0-768）
- `{randz}`：随机 Z 坐标（0-100）
- **基础复合类型（带碰撞避免）：**
- `{randxy}`：“x y”（例如，“127 89”）
- `{randxyc}`：“x, y”（例如，“127, 89”）
- `{randxyz}`：“x y z”（例如，“127 89 18”）
- `{randpos}`：“x, y, z”（例如，“127, 89, 18”）
- 注意：这些会遵守安全边际并避开障碍物
- **可自定义范围的动态随机量：**
- `{random:min:max}`：匿名随机浮点数
- `{random:min:max:decimals}`：带小数位的匿名随机浮点数
- `{randint:min:max}`：匿名随机整数
- `{randx:min:max}`, `{randy:min:max}`, `{randz:min:max}`：带自定义范围的匿名坐标

**变量坐标类型（粘性，可选择碰撞避免）：**
- **变量与范围（严格冒号语法）：**
- `{randx_varname}`：粘性变量。所有 `{randx_varname}` 实例共享同一个值。
- `{randx:min:max}`：带自定义范围的匿名随机量（例如，`{randx:10:50}`）。
- `{randx_varname:min:max}`：定义带范围的变量（例如，`{randx_v1:10:50}`）。
- `{randx_varname:min:max:decimals}`：定义带范围和小数位的变量。
- **优先级说明：** 对于变量，首次定义决定值。若您定义了 `{randx_v1:10:20}`，之后使用 `{randx_v1}`，则范围 10-20 适用于所有位置。若您首先使用 `{randx_v1}`（默认），则后续对该变量的范围定义将被忽略。
- **协调位置变量（带碰撞避免）：**
- 当 `{randx_varname}` 和 `{randy_varname}` 一起使用时（可附带 `{randz_varname}`），它们会被自动视为一个协调的位置，该位置会避开障碍物并保持安全边际，类似于 `{randxy}` 和 `{randxyz}` 复合类型。
- 示例：`{randx_target}`, `{randy_target}`, `{randz_target}` 会生成一个无碰撞的位置。
- **要求**：仅当 **X 和 Y 两个变量** 共享同一变量名时才适用。Z 坐标是可选的。
- **不适用于**：
- 单个坐标：单独使用 `{randx_var}` → 简单随机
- 仅 X+Z：使用 `{randx_var}`, `{randz_var}` 而不使用 `{randy_var}` → 独立随机
- 仅Y+Z：`{randy_var}`、`{randz_var}` 不带 `{randx_var}` → 独立的随机量
- 安全余量和避障行为与复合类型保持一致。
- **复合-标量集成（优先级规则）：**
- **重要**：当复合类型（`{randxy_var}`、`{randxyz_var}`、`{randpos_var}`、`{randxyc_var}`）和标量坐标（`{randx_var}`、`{randy_var}`、`{randz_var}`）使用**相同的变量名**时，复合类型优先。
- 位置由复合类型生成一次（带碰撞避免），标量分量自动从复合结果中提取对应值。
- 示例：如果同时使用 `{randxy_pos}` 和 `{randx_pos}`，系统为 `{randxy_pos}` 生成一个位置，`{randx_pos}` 则直接使用其X分量。
- 这样可以确保：
- 不重复生成位置
- 复合值与标量值完全一致
- 仅需一次碰撞检测，提升效率
- **实际用例**：`"移动到 {randxyz_wp}。API调用：x={randx_wp}, y={randy_wp}, z={randz_wp}"` — 复合类型生成带碰撞避免的位置，API参数使用完全相同的数值。
- **顺序无关**：无论标量类型或复合类型在模板中出现的先后顺序，复合类型始终优先。系统在生成值之前会预扫描所有占位符。
- **变量名匹配**：名称必须完全一致。`{randx_tar}` + `{randz_alti}` + `{randpos_tar}` → 仅有 `{randx_tar}` 和 `{randy_tar}` 会使用 `{randpos_tar}` 的值，`{randz_alti}` 保持独立。
- **单个标量行为**：单独的 `{randx_var}` 若没有匹配的 `{randy_var}` 或复合类型，将正常生成且不进行碰撞避免。
- **Z坐标独立性**：当使用 `{randxy_var}`（二维复合）和 `{randz_var}` 时，Z坐标独立生成，使用默认范围（0‑100）。如需Z与XY联动，请使用 `{randxyz_var}` 或 `{randpos_var}` 复合类型。

## 5) 替换工作机制
- 实体：同一索引的 `_id` 和 `_name` 占位符会由所选实体同时填充。
- 随机量：粘性占位符在同一任务内复用相同的值；匿名动态占位符每次出现都会重新随机。
- 相关API：路径和参数使用与内容/别名相同的替换规则和缓存。

## 6) 内置模板（参考）
常见内置模板包括基本操作和多实体任务（示例：`basic_takeoff_land`、`patrol_mission`、`search_task`、`delivery_mission`、`grid_search`、`emergency_return`、`formation_triangle`、`dual_patrol`、`perimeter_search`、`multi_target_survey`）。内置模板标记为 `is_builtin: true`，不可删除，但可以复制/编辑为自定义版本。

## 7) 示例

**含随机量的多无人机内容**
```
Drone {drone_1_name} and {drone_2_name} inspect {target_1_name} at {random_altitude}m,
then hold at ({random:0:100}, {random:0:100}, {random_altitude}).
```
- `{drone_1_*}` 和 `{drone_2_*}` 来自两个不同的下拉选择。
- `{target_1_name}` 来自目标下拉选择。
- `{random_altitude}` 在任务内粘性固定；`{random:0:100}` 每次出现都重新随机。

**带碰撞避免的坐标协同变量**
```
Fly drone {drone_1_name} from ({randx_start}, {randy_start}, {randz_start})
to waypoint ({randx_wp:100:500}, {randy_wp:100:400}, {randz_wp:10:50}).
Return to ({randx_start}, {randy_start}, {randz_start}).
```
- `{randx_start}`、`{randy_start}`、`{randz_start}` 构成一个协同组，会避开障碍物。
- `{randx_wp}`、`{randy_wp}`、`{randz_wp}` 构成另一个协同组，使用自定义范围。
- 所有位置的生成都会避开障碍物并遵守安全余量。
- 变量具有粘性：`{randx_start}` 在整个模板中保持相同值。

**复合-标量集成（高效位置生成）**
```
Navigate to position {randxyz_target}.
Detailed log: Moving to X={randx_target}, Y={randy_target}, Z={randz_target}.
API: POST /drones/{drone_1_id}/move_to with x={randx_target}, y={randy_target}, z={randz_target}
```
- `{randxyz_target}` 生成一次位置，并执行碰撞避免（例如 "127 89 18"）
- `{randx_target}`、`{randy_target}`、`{randz_target}` 自动从复合结果中提取（127, 89, 18）
- 无重复生成 — 高效且保证一致
- 非常适合同时需要人类可读格式和API参数的模板
- 适用于 `{randxy_var}`、`{randxyc_var}`、`{randxyz_var}` 和 `{randpos_var}`

**API代码片段**
```json
{
  "method": "POST",
  "path": "/drones/{drone_1_id}/command/move_to",
  "parameters": {
    "id": "{drone_1_id}",
    "x": "{random_x}",
    "y": "{random_y}",
    "z": "{random_altitude}"
  }
}
```

## 8) 编辑技巧与最佳实践
- 保持 `_id` 和 `_name` 对一致，以便界面显示实体下拉列表。
- 需要一次抽取复用时用命名随机量；需要不同值时使用匿名 `{random:...}`。
- 在内容、别名和API中复用占位符，以构建连贯任务。
- 编辑模板后通过创建任务并验证替换值进行测试。
- 批量创建时，仅任务名称会自动编号；其他随机量/实体每次生成任务时抽取。

## 9) 故障排除
- **占位符未被替换**：确认其匹配支持的格式且在模板中存在；填充必填的自由文本字段。
- **显示的实体错误**：确认使用了正确的索引（`drone_2_id` 与 `drone_1_id`），并且 `_id` 和 `_name` 成对。
- **随机值被意外复用**：命名或预定义随机量是粘性的；如需每次出现重新随机，请改用匿名 `{random:min:max}` 或 `{randint:min:max}`。
- **下拉菜单缺失**：UI 仅自动检测符合 `_id`/`_name` 模式的无人机/目标/障碍物占位符。
- **复合值与标量值不匹配**：确保变量名完全一致。`{randx_tar}` 和 `{randpos_target}` 是不同的变量（'tar' 与 'target'），它们不会共享值。
- **复合中Z坐标与XY不匹配**：如果使用 `{randxyz_pos}` 和 `{randx_pos}`、`{randy_pos}`、`{randz_alt}`（Z名称不同），Z将不匹配。请使用一致的名称：`{randxyz_pos}` 与 `{randz_pos}`。
- **单独使用 randx 不会回避障碍物**：若仅有 `{randx_var}` 而没有 `{randy_var}` 或复合类型，将不会启用碰撞避免。请添加同变量名的 `{randy_var}`，或使用诸如 `{randxy_var}` 的复合类型。
- **X 和 Z 没有 Y 时无法协调**：`{randx_tar}` + `{randz_tar}` 若缺少 `{randy_tar}`，则不会协调。协调要求同时具备 X 与 Y。否则二者将独立生成且没有碰撞避免。
- **基础占位符与变量的区别**：`{randx}`（无下划线）是匿名的（每次均产生新值），而非粘性的。要使用粘性值，请用 `{randx_varname}`。若需带碰撞避免的协调位置，请用 `{randx_varname}` + `{randy_varname}` 或诸如 `{randxy_varname}` 的复合类型。
- **randxy 复合与独立的 Z**：`{randxy_pos}` + `{randz_pos}` → XY 以碰撞避免方式协调，但 Z 独立生成（范围 0 - 100）。要获得完全协调的 3D 位置，请用 `{randxyz_pos}` 或 `{randpos_pos}`。

## 10) 编程用法（可选）
```python
from task_template_manager import TaskTemplateManager

manager = TaskTemplateManager()
task = manager.instantiate_template('formation_triangle', {
    'name': 'Triangle Patrol',
    'drone_1_id': 'alpha',
    'drone_2_id': 'bravo',
    'drone_3_id': 'charlie'
})
```
- `instantiate_template` 会应用与 GUI 相同的替换规则。

请将本指南作为权威参考；其余占位符和模板文档可待此就位后删除。
