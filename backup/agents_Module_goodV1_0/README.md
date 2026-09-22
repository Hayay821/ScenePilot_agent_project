# ScenePilot Fast

这是一个轻量级的四 Agent 影像制作原型，目标是验证核心能力：**读取媒体、调用多模态模型分析、输出导演/摄影/剪辑结果**。

**重要说明**：当前版本使用 `data/` 目录下的图片和视频作为输入来模拟真实拍摄场景，因为实际摄像机 SDK 暂未集成。这些图片和视频代表「已拍摄的素材」或「参考素材」，用于测试和验证 Agent 的分析能力。

---

## 📚 文档导航

- **[完整文档索引](docs/README.md)** - 所有文档的导航和分类
- **[快速开始](docs/guides/快速开始.md)** ⭐ 新手必读
- **[专家技能创作指南](docs/guides/专家技能创作指南.md)** ⭐ 新功能：用自然语言创建拍摄技能
- **[测试所有 Agent](docs/guides/测试所有Agent.md)** ⭐ 详细测试指南
- **[独立测试指南](docs/guides/TEST_INDIVIDUAL_AGENTS.md)** - 单独测试每个 Agent
- **[模型配置说明](docs/reference/MODEL_CONFIGURATION.md)** - 模型配置和故障排查

---

## 四个 Agent 的功能说明

### 🎬 1. SkillsManager（技能管理器）

**功能**：中文意图理解和 Skill 匹配 + 专家技能创作

**核心能力**：
1. **Skill 匹配**：根据用户意图自动匹配相关拍摄技巧
2. **专家创作**：从专业摄影师的自然语言输入提取结构化技能 ✨ 新功能

**输入**：
- 用户的中文拍摄意图（如"我想拍自然的人像"）
- 当前阶段（director/cinematographer/editor）
- 专家经验描述（自然语言）✨ 新增

**输出**：
- 匹配的 Skill 列表（从本地 YAML 库）
- 中文解释和下一步提示
- 提取的结构化技能（YAML 格式）✨ 新增
- 输出文件：`outputs/skills_manager/skills_director.json`

**使用场景**：
- 当用户描述拍摄需求时，自动匹配相关的拍摄技巧和规则
- 专业摄影师可以用自然语言分享经验，系统自动转化为可复用的技能库 ✨ 新增

**测试方式**：

```bash
# 1. Skill 匹配（原有功能）
python test_agents.py skills --mode bailian --text "拍摄自然人像视频"

# 2. 专家技能创作（新功能）✨
python test_agents.py skills-author --mode bailian --expert-input "拍摄人像时，我会让模特面向主光源，确保眼睛有眼神光。逆光时使用反光板补光。"
```

**使用的模型**：`qwen3-vl-plus`（文本理解，无需视觉能力）

**详细文档**：**[专家技能创作指南](docs/guides/专家技能创作指南.md)** ⭐ 新功能详解

---

### 🎥 2. Director（导演 Agent）

**功能**：拍摄前的导演计划

**输入**：
- 用户的拍摄目标（中文文本）
- 参考图片（单张图片）

**输出**：
- 拍摄计划（shot_plan）：分阶段的镜头安排
- 参考图片分析（reference_analysis）：构图、光线、主体分析（**中文输出**）
- 匹配的 Skill ID 列表
- 置信度和中文总结
- 输出文件：`outputs/director/director.json`

**使用场景**：
- 在开始拍摄前，根据用户需求和参考图片，规划镜头顺序和拍摄策略
- 例如：先拍环境全景（establish），再拍人物中景（subject），最后拍特写（detail）

**测试方式**：
```bash
python test_agents.py director --mode bailian --text "拍摄自然人像" --image data/img/img1.jpg
```

**使用的模型**：`qwen3-vl-flash`（多模态，支持图片分析）

---

### 📹 3. Cinematographer（摄影 Agent）

**功能**：拍摄中的实时画面分析和拍摄建议

**输入**：
- 用户的拍摄目标（中文文本）
- 视频文件（自动抽帧分析）

**输出**：
- 画面分析（analysis）：主体可见性、构图质量、跟踪置信度（**中文输出**）
- 拍摄建议（suggestion）：`capture_frame`（捕获此帧）或 `wait_and_recheck`（继续等待）
- 如果建议捕获，会保存该帧到 `outputs/cinematographer/captures/`
- 置信度和中文总结
- 输出文件：
  - `outputs/cinematographer/filming.json` - 分析结果
  - `outputs/cinematographer/frames/` - 视频抽帧
  - `outputs/cinematographer/captures/` - 捕获的优质帧

**使用场景**：
- 模拟真实拍摄时，摄影师实时查看取景器画面
- 当前版本通过分析视频的抽取帧来模拟「实时画面」
- 判断当前画面是否达到拍摄标准（主体清晰、构图合理）
- 给出专业建议：是否需要调整角度、等待更好时机

**测试方式**：
```bash
python test_agents.py cinematographer --mode bailian --text "拍摄自然人像" --video data/video/test_video1.mp4
```

**使用的模型**：`qwen3-vl-flash`（多模态，支持视频帧分析）

**重要说明**：
- `capture_frame` 是结构化建议，当前会保存帧图片
- 未来接入真实摄像机 SDK 时，可以触发实际的拍摄动作

### X4 Air / Link2 多流接入边界

当前电脑摄像头只作为测试适配器。最终设备输入应由本地 Edge Adapter 转成统一帧：

```text
BrowserCameraAdapter / Link2Adapter / X4AirAdapter
                         |
                         v
                    VideoFrame
                         |
                         v
              Cinematographer Session
```

建议统一格式：

```json
{
  "stream_id": "link2_main",
  "device_id": "link2_serial_001",
  "timestamp_ms": 12400,
  "sequence": 248,
  "frame_data": "data:image/jpeg;base64,..."
}
```

当前已经实现：

- 浏览器摄像头单流会话。
- 首次请求使用用户目标和 Cinematographer Skills。
- 后续请求使用当前帧和本地短记忆。
- 每 0.5 秒分析一帧。
- 用户手动停止。
- `capture_frame` 保存当前帧。

当前尚未实现：

- X4 Air Camera/Media SDK 适配器。
- Link2 UVC/Link SDK 适配器。
- 多个 `stream_id` 的并发调度和融合。
- 真实设备抓拍执行。

因此，当前 API 是未来 X4 Air/Link2 接入的上层契约基础。设备适配器只需输出统一 `VideoFrame`，不需要重写 Cinematographer 的模型记忆和 Skill 指导逻辑。

### 实时视频流接入边界

当前浏览器摄像头只是测试输入源。最终目标是通过本地 Edge Adapter 接入 X4 Air/Link2：

```text
X4AirAdapter / Link2Adapter / BrowserAdapter
                |
                v
        统一 VideoFrame
                |
                v
      Cinematographer Session
```

统一帧格式建议：

```json
{
  "stream_id": "link2_main",
  "device_id": "link2_serial_001",
  "timestamp_ms": 12400,
  "sequence": 248,
  "frame_data": "data:image/jpeg;base64,..."
}
```

因此架构上可以支持非当前电脑前置摄像头、X4 Air、Link2 和多个视频流，但当前 Fast 版本已经实现的是：

- 浏览器摄像头单流会话。
- 本地图片/视频帧输入。
- 首次会话加载用户目标和 Cinematographer Skill。
- 后续帧使用本地短记忆摘要。
- 手动停止和优质帧保存。

当前尚未实现：

- X4 Air Camera/Media SDK 适配器。
- Link2 UVC/Link SDK 适配器。
- 多个 `stream_id` 的并发调度。
- 多流融合分析。
- 真实设备抓拍执行。

接入真实设备时不应修改 Cinematographer 的业务协议，只需让设备适配器输出统一 `VideoFrame`。

### 面向比赛的可解释导演报告

完整流程现在会额外生成 `decision_trace`，把以下内容串联展示：

```text
用户需求
  -> 匹配的 Skill 和规则
  -> Director 镜头计划
  -> Cinematographer 证据帧和拍摄建议
  -> Editor 时间线和预览视频
```

这不是普通的“输入一句话生成视频”，用户可以看到规则来源、证据和可编辑控制项，体现：

- 开放性：Skill、规则和设备适配器可替换。
- 可编程性：用户可以修改 Skill 和镜头计划。
- 可解释性：Agent 输出关联素材证据和规则。
- 人机共创：AI 提议，用户确认或修改。

决策报告接口：

```text
GET /api/v1/demo/decision-trace
```

---

### ✂️ 4. Editor（剪辑 Agent）

**功能**：后期剪辑时间线规划

**输入**：
- 视频素材（单个视频文件）
- 图片素材（可选）

**输出**：
- 剪辑时间线（timeline）：每个素材的角色和使用理由（**中文输出**）
- 输出格式建议（9:16 竖屏或 16:9 横屏）
- FFmpeg 生成的预览视频（前 10 秒粗剪）
- 素材质量分析（**中文输出**）
- 置信度和中文总结
- 输出文件：
  - `outputs/editor/edit_plan.json` - 剪辑计划
  - `outputs/editor/preview.mp4` - 预览视频

**使用场景**：
- 分析所有拍摄的素材（视频、图片）
- 规划剪辑顺序和每个片段的作用
- 生成快速预览，验证剪辑逻辑

**测试方式**：
```bash
python test_agents.py editor --mode bailian --video data/video/test_video1.mp4
```

**使用的模型**：`qwen3-vl-flash`（多模态，支持视频/图片分析）

---

## 完整工作流程

### 独立测试模式（推荐）⭐

每个 Agent 单独测试，输入单个文件，输出到独立子目录：

```
用户命令：python test_agents.py [agent] --mode bailian --text "..." --image/--video "file"

1. SkillsManager
   输入：用户文本（中文）
   ↓ 匹配相关 Skill（如 portrait_story_director.yaml）
   输出：outputs/skills_manager/skills_director.json

2. Director Agent
   输入：用户目标 + 单张参考图片
   ↓ 分析参考图片的构图、光线、主体（中文输出）
   输出：outputs/director/director.json

3. Cinematographer Agent
   输入：用户目标 + 单个视频（自动抽帧）
   ↓ 分析每一帧的画面质量（中文输出）
   输出：outputs/cinematographer/filming.json
        outputs/cinematographer/frames/
        outputs/cinematographer/captures/

4. Editor Agent
   输入：单个视频或图片
   ↓ 分析素材内容和质量（中文输出）
   输出：outputs/editor/edit_plan.json
        outputs/editor/preview.mp4
```

### 完整流程模式

使用 `fast.py run` 处理整个目录的所有文件：

```
用户命令：python fast.py run --mode bailian --text "拍摄自然人像短片" --media data

串行执行：
1. SkillsManager → 匹配 Skills
2. Director → 分析 data/img/ 中所有图片
3. Cinematographer → 分析 data/video/ 中所有视频帧
4. Editor → 生成剪辑时间线和预览

最终输出：outputs/run.json（完整结果汇总）
```

## Editor 工作区过渡 Demo

Editor 另提供一个双视频工作区接口，用于测试：

```text
v1.mp4 + v2.mp4
  -> 读取 v1 最后一帧和 v2 第一帧
  -> 调用 DashScope 首尾帧视频模型生成 transition.mp4
  -> 统一视频规格
  -> FFmpeg 拼接
  -> output.mp4
```

接口：

```text
POST /api/v1/editor/workspace
```

前端页面中填写：

- `v1` 视频路径。
- `v2` 视频路径。
- AI 过渡提示词。
- 点击“生成 Editor 工作区视频”。

默认示例：

```text
data/video/test_video1.mp4
```

工作区输出：

```text
outputs/editor_workspace/
  frames/
  normalized/
  transitions/
  renders/
  <workspace_id>.json
```

AI 过渡配置不是普通 Qwen-VL 配置，必须额外确认百炼视频生成模型、提交 endpoint、状态查询 endpoint 和模型请求字段。可配置：

```env
DASHSCOPE_VIDEO_MODEL=your_available_first_last_frame_model
DASHSCOPE_VIDEO_API_URL=your_video_generation_endpoint
DASHSCOPE_VIDEO_STATUS_URL=your_task_status_endpoint_prefix
DASHSCOPE_VIDEO_TIMEOUT_SEC=300
```

如果视频模型配置、权限、endpoint 或请求格式不正确，系统会在 `transition.fallback` 写入错误，并自动退化为：

```text
v1_normalized + v2_normalized -> output.mp4
```

因此最终拼接视频仍然应该能够生成。当前 Demo 只执行一次，不实现多轮工作区剪辑。

## 黑客松 Demo 主线：开放导演工作台

当前推荐展示主线不是“AI 自动生成一个视频”，而是：

```text
用户提出拍摄目标
  -> SkillsManager 匹配摄影 Skill
  -> 用户看到 Skill 和规则
  -> Director 生成导演计划
  -> Cinematographer 分析取景帧并给出建议
  -> Editor 生成时间线和预览
  -> decision_trace 展示每条规则、证据和 Agent 决策
  -> 用户修改需求后重新运行，对比结果变化
```

完整流程会生成：

```text
outputs/run.json
outputs/director.json
outputs/filming.json
outputs/edit_plan.json
outputs/preview.mp4
```

`run.json` 中的 `decision_trace` 是展示开放性和可解释性的核心：

- `skill_trace`：使用了哪些 Skill 和具体规则。
- `agent_decisions`：三个 Agent 分别做了什么决定。
- `evidence`：决定依据的图片、视频帧和时间线。
- `editable_controls`：用户可以修改的导演控制项。

前端会把这些内容显示为规则标签、Agent 决策摘要和完整 JSON。用户修改左侧需求后重新点击“运行完整流程”，可以直接展示人机共创，而不是一次性黑盒出片。

展示口号：

> AI 不替你创作；它把摄影专家的规则、证据和选择权交还给你，让每个人都能成为导演。

---

## 当前测试方式说明

由于真实摄像机 SDK 暂未集成，当前使用以下方式模拟真实场景：

| 真实场景 | 当前模拟方式 | 数据来源 |
|---|---|---|
| 用户描述拍摄需求 | 命令行 `--text` 参数 | 用户输入 |
| 查看参考图片 | Director 分析本地图片 | `data/img/` |
| 实时查看取景器画面 | Cinematographer 分析视频抽帧 | `data/video/` 抽帧 |
| 拍摄完成的素材 | 本地视频和图片 | `data/img/` + `data/video/` |
| 捕获优质帧 | 保存到 `outputs/captures/` | Cinematographer 标记 |
| 剪辑预览 | FFmpeg 生成 `preview.mp4` | Editor 调用 FFmpeg |

**这意味着**：
- `data/img/` 中的图片 = 参考图片或已拍摄的静态素材
- `data/video/` 中的视频 = 已拍摄的视频素材
- 视频抽帧 = 模拟「实时拍摄」中的取景器画面
- `capture_frame` = 标记优质帧，未来可以触发真实拍摄

---

## 特性

✅ **真实多模态集成**：支持百炼 Qwen-VL 视觉模型  
✅ **四 Agent 协作**：SkillsManager、Director、Cinematographer、Editor  
✅ **本地媒体处理**：图片分析、视频抽帧、FFmpeg 预览生成  
✅ **结构化输出**：JSON 格式的计划、分析和时间线  
✅ **中英文交互**：中文用户输入，英文 Skill 库  
✅ **HTTP API**：FastAPI 服务，支持独立调用各 Agent  

## 快速开始

### 🚀 最快上手方式

```bash
# 1. 一键测试所有 Agent（推荐）
test_all_agents.bat

# 2. 查看输出结果
explorer outputs
```

详细说明请查看 **[快速开始文档](docs/guides/快速开始.md)**

---

## 核心模块说明

### 📦 项目结构

```
agents_Module_fast/
├── fast.py                          # 主程序：完整流程入口
├── test_agents.py                   # 独立测试脚本（推荐）⭐
├── test_all_agents.bat              # 一键测试所有 Agent
├── agents/                          # Agent 模块目录（新）⭐
│   ├── __init__.py
│   ├── skills_manager_agent/        # SkillsManager Agent 模块
│   │   ├── __init__.py
│   │   └── skills_manager.py
│   ├── director_agent/              # Director Agent 模块
│   │   ├── __init__.py
│   │   └── director.py
│   ├── cinematographer_agent/       # Cinematographer Agent 模块
│   │   ├── __init__.py
│   │   └── cinematographer.py
│   └── editor_agent/                # Editor Agent 模块
│       ├── __init__.py
│       └── editor.py
├── data/                            # 测试数据目录
│   ├── img/                         # 参考图片
│   └── video/                       # 测试视频
├── skills/repository/               # Skill 技能库（YAML）
├── outputs/                         # 输出目录
│   ├── skills_manager/              # SkillsManager 输出
│   ├── director/                    # Director 输出
│   ├── cinematographer/             # Cinematographer 输出
│   └── editor/                      # Editor 输出
└── docs/                            # 文档中心
    ├── guides/                      # 使用指南
    ├── reference/                   # 参考文档
    └── changelog/                   # 更新日志
```

**⭐ 最新更新（v1.1）**：
- 将所有 Agent 代码迁移到 `agents/` 子目录
- 每个 Agent 有独立的子目录，便于单元测试和功能扩展
- 所有 Agent 在执行前会先调用 SkillsManager 获取相关 Skills
- 用户可见的 Skills 匹配和应用反馈

---

## 安装和配置

### 1. 安装依赖

```bash
conda activate base  # 或你的 Python 环境
cd F:\BoldMaker\project00\agents_Module_fast
pip install -r requirements.txt
```

**必需依赖**：
- `openai` - 调用百炼 API
- `python-dotenv` - 加载环境变量
- `pillow` - 图片处理
- `ffmpeg-python` - 视频处理（需要系统安装 FFmpeg）

### 2. 配置 API Key

在 `.env` 文件中配置百炼 API：

```env
API_KEY=sk-ws-xxx...
API_URL=https://llm-xxx.cn-beijing.maas.aliyuncs.com/compatible-mode/v1

# 模型配置
QWEN_VL_MODEL=qwen3-vl-flash          # 视觉理解模型（多模态）
QWEN_TEXT_MODEL=qwen3-vl-plus         # 文本理解模型

# 各 Agent 专用模型配置
SKILLS_MODEL=qwen3-vl-plus            # SkillsManager: 文本理解
DIRECTOR_MODEL=qwen3-vl-flash         # Director: 图片分析
CINEMATOGRAPHER_MODEL=qwen3-vl-flash  # Cinematographer: 视频帧分析
EDITOR_MODEL=qwen3-vl-flash           # Editor: 素材分析
```

⚠️ **重要提示**：
- 确保 `API_KEY` 行末尾**没有空格**（会导致 HTTP 请求失败）
- API_URL 必须使用 `/compatible-mode/v1` 端点（OpenAI 兼容格式）
- 所有 Agent 的输出现在都是**中文**

**模型说明**：

| Agent | 模型 | 原因 |
|---|---|---|
| **SkillsManager** | `qwen3-vl-plus` | 中文意图理解、YAML Skill 匹配 |
| **Director** | `qwen3-vl-flash` | 参考图片分析 → 导演计划 |
| **Cinematographer** | `qwen3-vl-flash` | 视频抽帧分析 → 拍摄建议 |
| **Editor** | `qwen3-vl-flash` | 视频/图片素材 → 剪辑时间线 |

详细配置说明请查看 **[模型配置文档](docs/reference/MODEL_CONFIGURATION.md)**

### 3. 准备测试数据

默认从以下目录读取：

```text
data/
  img/          # 图片素材（至少一张，用于 Director 测试）
  video/        # 视频素材（至少一个，用于 Cinematographer 和 Editor 测试）
```

Skill 库（自动加载）：

```text
skills/repository/
  builtin/
    director/
    cinematographer/
    editor/
```

---

## 测试和使用

### 方法 1：一键测试所有 Agent（推荐）⭐

```bash
# Windows 下直接运行
test_all_agents.bat

# 或命令行执行
python test_agents.py all --mode bailian --text "拍摄自然人像" --image data/img/img1.jpg --video data/video/test_video1.mp4
```

这会依次测试所有 4 个 Agent，每个 Agent 输出到独立的子目录。

### 方法 2：独立测试单个 Agent

```bash
# 1. 测试 SkillsManager（纯文本，不需要图片/视频）
python test_agents.py skills_manager --mode bailian --text "拍摄自然人像视频"

# 2. 测试 Director（需要一张参考图片）
python test_agents.py director --mode bailian --text "拍摄自然人像" --image data/img/img1.jpg

# 3. 测试 Cinematographer（需要一个视频）
python test_agents.py cinematographer --mode bailian --text "拍摄自然人像" --video data/video/test_video1.mp4

# 4. 测试 Editor（需要一个视频或图片）
python test_agents.py editor --mode bailian --video data/video/test_video1.mp4
```

**输出目录结构**：
```
outputs/
  ├── skills_manager/
  │   └── skills_director.json
  ├── director/
  │   └── director.json
  ├── cinematographer/
  │   ├── filming.json
  │   ├── frames/              # 视频抽帧
  │   └── captures/            # 捕获的优质帧
  └── editor/
      ├── edit_plan.json
      └── preview.mp4          # 预览视频
```

### 方法 3：完整流程测试（处理整个目录）

```bash
# Mock 模式（不调用真实 API，快速验证逻辑）
python fast.py run --mode mock --text "请拍摄一组自然的人像短片" --media data

# 真实百炼模式（调用真实 API）
python fast.py run --mode bailian --text "请拍摄一组自然的人像短片，保留人物和环境关系" --media data
```

这会处理 `data/` 目录下的所有图片和视频，输出汇总到 `outputs/run.json`。

### 🎯 推荐使用方式

- **日常开发和调试**：使用 `test_agents.py` 单独测试每个 Agent
- **完整流程验证**：使用 `fast.py run` 测试整体协作

详细测试指南：
- **[测试所有 Agent](docs/guides/测试所有Agent.md)** - 完整测试手册
- **[独立测试指南](docs/guides/TEST_INDIVIDUAL_AGENTS.md)** - 单个 Agent 测试

---

## 其他命令行工具

### 基础命令

```bash
# 检查媒体文件
python fast.py inspect --media data

# 视频抽帧
python fast.py frames --video data/video/test_video1.mp4

# Skill 匹配测试
python fast.py skills --text "我想拍自然的人像"

# 启动 HTTP API 服务
python fast.py serve

# 运行测试
pytest -q
```

### HTTP API 服务

启动服务：

```bash
python fast.py serve
```

服务地址：`http://127.0.0.1:8765`

**API 端点**：

- `GET /health` - 健康检查
- `POST /skills/interact` - Skill 交互
- `POST /director` - 导演计划
- `POST /cinematographer` - 摄影分析
- `POST /editor` - 剪辑计划
- `POST /run` - 完整流程

详细 API 文档请查看代码中的 FastAPI 接口定义。

---

## 输出文件说明

### 独立测试模式输出

运行 `test_agents.py` 后，会在 `outputs/` 目录生成各 Agent 的独立输出：

```text
outputs/
  ├── skills_manager/
  │   └── skills_director.json      # Skill 匹配结果
  ├── director/
  │   └── director.json              # 导演计划（中文分析）
  ├── cinematographer/
  │   ├── filming.json               # 摄影分析（中文建议）
  │   ├── frames/                    # 视频抽帧
  │   │   └── test_video1/
  │   │       ├── frame_0001.jpg
  │   │       └── frame_0002.jpg
  │   └── captures/                  # 捕获的优质帧
  │       └── frame_0001.jpg
  └── editor/
      ├── edit_plan.json             # 剪辑时间线（中文分析）
      └── preview.mp4                # 预览视频（前10秒）
```

### 完整流程模式输出

运行 `fast.py run` 后，会生成：

```text
outputs/
  ├── run.json              # 完整流程结果汇总
  ├── director.json         # 导演计划
  ├── filming.json          # 摄影分析
  ├── edit_plan.json        # 剪辑时间线
  ├── preview.mp4           # 预览视频
  ├── frames/               # 视频抽帧
  └── captures/             # 捕获的优质帧
```

### 各文件内容说明

**director.json** - 拍摄前导演计划：
- `goal`: 用户拍摄目标
- `shot_plan`: 分阶段镜头计划
- `reference_analysis`: 参考图片分析（**中文**）
- `confidence`: 置信度
- `user_summary_zh`: 中文总结

**filming.json** - 实时摄影分析：
- `source_frames`: 分析的帧列表
- `analysis`: 画面质量分析（**中文**）
- `suggestion`: 拍摄建议（capture_frame 或 wait_and_recheck）
- `captured_frame`: 标记的帧路径

**edit_plan.json** - 剪辑时间线：
- `timeline`: 素材列表和角色分配
- `rendered_preview`: 预览视频路径
- `render`: 输出格式建议（9:16 或 16:9）
- `analysis_summary`: 素材质量分析（**中文**）

详细输出字段说明请查看 **[测试所有 Agent](docs/guides/测试所有Agent.md#每个-agent-的输出)**

---

## 技术特性

✅ **真实多模态集成**：支持百炼 Qwen3-VL 视觉模型（qwen3-vl-flash 和 qwen3-vl-plus）  
✅ **模块化架构**：所有 Agent 代码迁移到 `agents/` 子目录，便于单元测试和功能扩展  
✅ **Skills 驱动工作流**：每个 Agent 执行前自动调用 SkillsManager 获取相关技能指导  
✅ **用户可见反馈**：实时显示 Skills 匹配结果和应用过程  
✅ **四 Agent 协作**：SkillsManager、Director、Cinematographer、Editor  
✅ **本地媒体处理**：图片分析、视频抽帧、FFmpeg 预览生成  
✅ **结构化输出**：JSON 格式的计划、分析和时间线  
✅ **中文交互**：所有 Agent 输出均为中文  
✅ **独立测试**：每个 Agent 可单独测试，输出到独立子目录  
✅ **HTTP API**：FastAPI 服务，支持独立调用各 Agent  

---

## 架构设计

### 最小架构

```text
SkillsManager Agent
  -> 输入：中文用户意图
  -> 处理：匹配本地英文 YAML Skill 库
  -> 输出：匹配的 Skill + 中文解释
  -> 模型：qwen3-vl-plus（文本理解）

Director Agent
  -> 输入：用户目标 + 单张参考图片
  -> 处理：分析图片构图、光线、主体
  -> 输出：拍摄前导演计划（shot_plan + reference_analysis）
  -> 模型：qwen3-vl-flash（多模态）
  -> 文件：outputs/director/director.json

Cinematographer Agent
  -> 输入：用户目标 + 单个视频（自动抽帧）
  -> 处理：分析画面质量（主体、构图、跟踪）
  -> 输出：当前帧分析 + 拍摄建议（capture_frame / wait_and_recheck）
  -> 模型：qwen3-vl-flash（多模态）
  -> 文件：outputs/cinematographer/filming.json + captures/frame_*.jpg

Editor Agent
  -> 输入：单个视频或图片
  -> 处理：分析素材内容和质量
  -> 输出：剪辑时间线 + FFmpeg 预览视频
  -> 模型：qwen3-vl-flash（多模态）
  -> 文件：outputs/editor/edit_plan.json + preview.mp4

ScenePilotFast.run_all
  -> 串行运行三个 Agent：Director → Cinematographer → Editor
  -> 汇总结果到 outputs/run.json

test_agents.py（推荐）
  -> 独立测试每个 Agent
  -> 输入单个文件（一张图片或一个视频）
  -> 输出到独立子目录（outputs/agent_name/）
```

**重要说明**：
- 当前版本不接真实相机 SDK
- `data/img/` 和 `data/video/` 中的媒体文件模拟「已拍摄的素材」或「参考素材」
- Cinematographer 的 `capture_frame` 是结构化建议，保存优质帧到 `outputs/captures/`
- 未来接入设备执行器时，`capture_frame` 可以触发真实拍摄动作
- Editor 已经可以使用 FFmpeg 生成预览视频

---

## 目录接口

| 目录 | 用途 |
|---|---|
| `data/` | 输入图片和视频（`img/` 和 `video/` 子目录）|
| `skills/repository/` | 英文 YAML Skill 数据库 |
| `outputs/` | 抽帧、JSON 输出、预览视频 |
| `tests/` | 核心闭环测试 |
| `docs/` | 完整文档和指南 |

---

## SkillsManager 交互

编程接口：

```python
from fast import ScenePilotFast

app = ScenePilotFast(mode="bailian")

# 交互式 Skill 匹配
result = app.manager.interact("我想拍自然人像", "director")

# 专家创作 Skill
draft = app.manager.author(
    name="My Portrait Rule",
    description="Keep space in the gaze direction",
    rules=[{"condition": "gaze_left", "advice": "leave_left_space"}]
)
```

Skill 会保存为本地英文 YAML `draft`。当前没有云端功能。

## 详细文档

- 🧪 **[TEST_INDIVIDUAL_AGENTS.md](TEST_INDIVIDUAL_AGENTS.md)** - 独立测试指南 ⭐ 推荐
  - 每个 Agent 单独测试方法
  - 输入单个文件（不是整个目录）
  - 输出到独立子目录
  - 完整测试示例和命令

- 📘 **[QUICK_TEST_GUIDE.md](QUICK_TEST_GUIDE.md)** - 快速测试手册
  - 完整测试步骤
  - 真实 API 调用示例
  - 输出文件字段说明
  - 常见问题解决方案
  - 验收清单

- 🎯 **[MODEL_CONFIGURATION.md](MODEL_CONFIGURATION.md)** - 模型配置说明
  - 各 Agent 模型选型原则
  - 成本优化建议
  - 环境变量优先级
  - 可用模型列表
  - 故障排查指南

- 🎬 **[USAGE_SCENARIOS.md](USAGE_SCENARIOS.md)** - 使用场景说明
  - 测试数据的含义（data/img/ 和 data/video/）
  - 各 Agent 如何使用这些文件
  - 与真实场景的对应关系
  - 常见误解澄清

- 📋 **[REAL_BAILIAN_QWEN_IMPLEMENTATION.md](tasks/REAL_BAILIAN_QWEN_IMPLEMENTATION.md)** - 实现任务文档
  - 技术需求和约束
  - 真实数据路径
  - Agent 实现边界
  - 验收标准

## 开发约束

当前只允许修改：
- `fast.py` - 主程序
- `*_agent.py` - 各 Agent 实现
- `skills/repository/**/*.yaml` - Skill 定义
- 必要的核心测试
- README 和文档

不要引入：
- 数据库、Redis、Kafka、消息队列
- 复杂 Agent 基类和编排层
- 真实相机 SDK
- 云端 Skill 库
- 大量测试文件
- Web 前端

保持轻量、聚焦核心闭环。

---

## 常见问题

### Q1: 为什么视觉 API 调用失败？

**错误信息**：`Connection error` 或 `Illegal header value`

**解决方法**：
1. 检查 `.env` 文件中的 `API_KEY` **末尾是否有空格**（最常见原因）
2. 确认 `API_URL` 使用的是 `/compatible-mode/v1` 端点
3. 验证模型名称是否正确（`qwen3-vl-flash` 和 `qwen3-vl-plus`）

详细排查方法请查看 **[模型配置文档](docs/reference/MODEL_CONFIGURATION.md#故障排查)**

### Q2: 如何测试单个 Agent？

使用 `test_agents.py` 脚本：

```bash
# 测试 Director
python test_agents.py director --mode bailian --text "拍摄自然人像" --image data/img/img1.jpg

# 测试 Cinematographer
python test_agents.py cinematographer --mode bailian --text "拍摄自然人像" --video data/video/test_video1.mp4

# 测试 Editor
python test_agents.py editor --mode bailian --video data/video/test_video1.mp4
```

详细说明请查看 **[测试所有 Agent](docs/guides/测试所有Agent.md)**

### Q3: 输出是英文怎么办？

所有 Agent 的 prompt 已经更新为强制中文输出。如果仍然出现英文输出：
1. 确认使用的是最新版本的代码
2. 检查 `*_agent.py` 文件中的 prompt 是否包含 "你必须使用中文回答"
3. 查看 **[更新日志](docs/changelog/CHANGELOG.md)** 了解最新修复

### Q4: data/ 目录下的文件是什么？

- `data/img/` - 参考图片或已拍摄的静态素材
- `data/video/` - 已拍摄的视频素材
- 这些文件用于模拟真实拍摄场景，因为真实摄像机 SDK 暂未集成

详细说明请查看 **[使用场景说明](docs/reference/USAGE_SCENARIOS.md)**

---

## 贡献和支持

如有问题或建议，请查看 `docs/` 目录下的完整文档，或联系开发团队。

---

## 许可证

本项目为内部原型，未公开发布。
