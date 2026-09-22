# ScenePilot Fast API 使用与测试指南

版本：v1.0  
项目目录：`F:\BoldMaker\project00\agents_Module_fast`

本文用于前端开发、接口联调和本地测试。当前服务使用 FastAPI，数据模型定义在 `api/schemas.py`，核心处理逻辑在 `fast.py`。

## 1. 当前服务能力

ScenePilot Fast 当前提供：

- 本地图片和视频目录读取。
- 视频信息读取和抽帧。
- 本地摄像头捕获帧。
- 本地 Skill 列表、详情和关键词选择。
- SkillsManager 用户意图交互。
- Director Agent：用户需求 + 参考图片 -> 导演计划。
- Cinematographer Agent：图片/视频帧 -> 当前画面分析和拍摄建议。
- Editor Agent：图片/视频 -> 剪辑时间线和 FFmpeg 预览。
- 三 Agent 完整串行流程。
- Mock Provider 和百炼 Qwen Provider。

当前默认数据目录：

```text
F:\BoldMaker\project00\agents_Module_fast\data
  img/
  video/
```

当前默认 Skill 目录：

```text
F:\BoldMaker\project00\agents_Module_fast\skills\repository
```

当前默认输出目录：

```text
F:\BoldMaker\project00\agents_Module_fast\outputs
```

## 2. 启动服务

### 2.1 Mock 模式

Mock 模式不调用百炼，适合接口结构测试和前端联调：

```powershell
cd F:\BoldMaker\project00\agents_Module_fast
python fast.py serve --mode mock
```

服务地址：

```text
http://127.0.0.1:8765
```

### 2.2 百炼模式

API 配置从项目根目录 `.env` 加载：

```text
F:\BoldMaker\project00\agents_Module_fast\.env
```

推荐配置：

```env
DASHSCOPE_API_KEY=your_key
DASHSCOPE_BASE_URL=https://dashscope.aliyuncs.com/compatible-mode/v1
DASHSCOPE_MODEL=qwen-vl-plus
```

启动：

```powershell
cd F:\BoldMaker\project00\agents_Module_fast
python fast.py serve --mode bailian
```

不要把 `.env` 内容提交到 Git、接口响应或前端代码中。

### 2.3 API 文档页面

服务启动后打开：

```text
Swagger UI: http://127.0.0.1:8765/docs
ReDoc:      http://127.0.0.1:8765/redoc
OpenAPI:    http://127.0.0.1:8765/openapi.json
```

Swagger UI 可以直接填写 JSON 请求并调用接口。

## 3. 统一响应格式

成功响应：

```json
{
  "success": true,
  "data": {},
  "agent_type": "director",
  "timestamp": "2026-09-23T10:30:00+00:00"
}
```

错误响应可能来自 FastAPI 参数校验或业务处理：

```json
{
  "detail": "video file not found"
}
```

前端应同时检查：

```javascript
if (!response.ok) {
  throw new Error(`HTTP ${response.status}`);
}
const body = await response.json();
if (body.success === false) {
  throw new Error(body.error?.message || 'API request failed');
}
```

## 4. 健康检查

### 请求

```http
GET /api/v1/health
```

PowerShell：

```powershell
Invoke-RestMethod http://127.0.0.1:8765/api/v1/health
```

预期：

```json
{
  "success": true,
  "data": {
    "ok": true,
    "mode": "mock"
  }
}
```

## 5. 媒体接口

### 5.1 获取媒体信息

```http
GET /api/v1/media/info?path=<absolute-or-project-relative-path>
```

PowerShell：

```powershell
$path = [uri]::EscapeDataString('data/video/test_video1.mp4')
Invoke-RestMethod "http://127.0.0.1:8765/api/v1/media/info?path=$path"
```

视频响应示例：

```json
{
  "success": true,
  "data": {
    "path": "data/video/test_video1.mp4",
    "type": "video",
    "width": 1280,
    "height": 720,
    "fps": 30.0,
    "frames": 669
  }
}
```

### 5.2 列出媒体目录

```http
GET /api/v1/media/list?directory=data&type=all
```

`type` 可选：

```text
all
images
videos
```

PowerShell：

```powershell
Invoke-RestMethod 'http://127.0.0.1:8765/api/v1/media/list?directory=data&type=all'
```

### 5.3 视频抽帧

```http
POST /api/v1/media/extract-frames
Content-Type: application/json
```

请求：

```json
{
  "video_path": "data/video/test_video1.mp4",
  "output_dir": "outputs/frames/test_video1_api",
  "every_seconds": 2.0,
  "max_frames": 12
}
```

PowerShell：

```powershell
$body = @{
  video_path = 'data/video/test_video1.mp4'
  output_dir = 'outputs/frames/test_video1_api'
  every_seconds = 2.0
  max_frames = 12
} | ConvertTo-Json

Invoke-RestMethod `
  -Uri 'http://127.0.0.1:8765/api/v1/media/extract-frames' `
  -Method Post `
  -ContentType 'application/json' `
  -Body $body
```

### 5.4 捕获本地摄像头帧

当前使用 OpenCV 摄像头 ID，不是 X4 Air/Link2 SDK。

```json
{
  "camera_id": 0,
  "num_frames": 5,
  "interval": 1.0,
  "output_dir": "outputs/captures",
  "resolution": [1280, 720]
}
```

请求：

```http
POST /api/v1/media/capture-webcam
```

如果本机没有可用摄像头，接口会返回 400。

## 6. Skill 接口

### 6.1 列出 Skill

```http
GET /api/v1/skills?stage=director&limit=10
```

`stage` 可选：

```text
director
cinematographer
editor
```

PowerShell：

```powershell
Invoke-RestMethod 'http://127.0.0.1:8765/api/v1/skills?stage=director&limit=10'
```

### 6.2 获取 Skill 详情

```http
GET /api/v1/skills/portrait_story_director
```

返回 Skill 原始结构摘要，包括：

- ID。
- 名称。
- 阶段。
- 标签。
- 规则。
- 文件路径。

### 6.3 智能选择 Skill

```http
POST /api/v1/skills/select
```

请求：

```json
{
  "user_text": "我想拍自然的人像短片，保留人物反应",
  "stage": "director",
  "limit": 3
}
```

响应：

```json
{
  "success": true,
  "data": {
    "skills": [
      {
        "id": "portrait_story_director",
        "name": "Portrait Story Director",
        "relevance_score": 1.0
      }
    ],
    "total": 1
  },
  "agent_type": "skills_manager"
}
```

### 6.4 SkillsManager 用户交互

```http
POST /api/v1/skills/interact
```

请求：

```json
{
  "user_text": "我想拍自然的人像，不要明显摆拍",
  "stage": "director",
  "limit": 3
}
```

该接口返回：

- 用户输入。
- 匹配 Skill。
- Skill 解释。
- 下一步提示。

## 7. Director Agent

### 请求

```http
POST /api/v1/agents/director
```

请求示例：

```json
{
  "user_text": "请拍摄一组自然的人像短片，保留人物与环境关系",
  "media_input": {
    "source_type": "FILE",
    "paths": [
      "data/img/img1.jpg",
      "data/img/img2.jpg"
    ]
  },
  "skills_filter": {
    "stage": "director",
    "limit": 3
  },
  "output_config": {
    "output_dir": "outputs/director",
    "save_intermediate": true,
    "formats": ["json"]
  }
}
```

PowerShell：

```powershell
$body = @{
  user_text = '请拍摄一组自然的人像短片，保留人物与环境关系'
  media_input = @{
    source_type = 'FILE'
    paths = @('data/img/img1.jpg', 'data/img/img2.jpg')
  }
  skills_filter = @{
    stage = 'director'
    limit = 3
  }
  output_config = @{
    output_dir = 'outputs/director'
    save_intermediate = $true
  }
} | ConvertTo-Json -Depth 6

Invoke-RestMethod `
  -Uri 'http://127.0.0.1:8765/api/v1/agents/director' `
  -Method Post `
  -ContentType 'application/json' `
  -Body $body
```

Director 输出包括：

- 匹配 Skill。
- Skill 指导摘要。
- 参考图片分析。
- 分阶段拍摄计划。
- 中文用户总结。

## 8. Cinematographer Agent

### 使用本地图片/已抽取视频帧

```http
POST /api/v1/agents/cinematographer
```

请求：

```json
{
  "user_text": "分析当前画面构图，判断是否适合拍摄",
  "media_input": {
    "source_type": "FILE",
    "paths": [
      "outputs/frames/test_video1/frame_000000.jpg",
      "outputs/frames/test_video1/frame_000060.jpg"
    ]
  },
  "skills_filter": {
    "stage": "cinematographer",
    "limit": 3
  }
}
```

如果输入的是视频路径，建议先调用抽帧接口，再把返回的帧路径传给摄影指导接口。这样前端可以控制采样数量和频率。

输出包括：

- 源帧列表。
- 主体和脸部可见性。
- 构图质量。
- 跟踪置信度。
- `capture_frame` 或 `wait_and_recheck`。
- 已保存的捕获帧路径。

## 9. Editor Agent

### 请求

```http
POST /api/v1/agents/editor
```

请求：

```json
{
  "user_text": "生成自然的人像短片，保留人物反应和环境关系",
  "media_input": {
    "source_type": "FILE",
    "paths": [
      "data/video/test_video1.mp4",
      "data/video/test_video2.mp4",
      "data/img/img1.jpg"
    ]
  },
  "skills_filter": {
    "stage": "editor",
    "limit": 3
  },
  "output_config": {
    "output_dir": "outputs/editor_api",
    "save_intermediate": true,
    "formats": ["json", "preview"]
  }
}
```

输出包括：

- 时间线片段。
- 每段素材角色和选择理由。
- 输出比例和格式。
- `preview.mp4` 路径。
- AI 分析摘要。

## 10. 完整串行流程

### 请求

```http
POST /api/v1/agents/run-all
```

请求：

```json
{
  "user_text": "请生成一组自然的人像短片，突出人物和环境关系",
  "media_dir": "data",
  "output_config": {
    "output_dir": "outputs/run_api",
    "save_intermediate": true,
    "formats": ["json", "preview"]
  }
}
```

该接口按顺序调用：

```text
SkillsManager
  -> Director
  -> Cinematographer
  -> Editor
```

输出的 `data` 包含：

skills
director
filming
editing
```

## 10.1 Editor 工作区过渡 Demo

这个接口用于验证一次完整的双视频工作区流程：

```text
v1.mp4 + v2.mp4
  -> 提取 v1 最后一帧和 v2 第一帧
  -> 可选 DashScope 首尾帧视频过渡
  -> 统一为 1280x720、30fps、yuv420p、无音频
  -> concat
  -> output.mp4
```

接口：

```http
POST /api/v1/editor/workspace
```

请求：

```json
{
  "v1_path": "data/video/test_video1.mp4",
  "v2_path": "data/video/test_video2.mp4",
  "reference_frame": "data/img/img1.jpg",
  "prompt": "Smooth natural camera movement, preserve subject identity and lighting continuity.",
  "use_ai_transition": true,
  "workspace_dir": "outputs/editor_workspace"
}
```

结果包含：

- 工作区 ID。
- v1 最后一帧路径。
- v2 第一帧路径。
- AI transition 任务状态。
- 最终 `output_video` 路径。
- 实际拼接片段列表。

工作区目录结构：

```text
outputs/editor_workspace/
  frames/
  normalized/
  transitions/
  renders/
  <workspace_id>.json
```

AI 过渡配置：

```env
DASHSCOPE_VIDEO_MODEL=your_available_first_last_frame_model
DASHSCOPE_VIDEO_API_URL=your_dashscope_video_endpoint
DASHSCOPE_VIDEO_STATUS_URL=your_dashscope_task_endpoint_prefix
DASHSCOPE_VIDEO_TIMEOUT_SEC=300
```

如果 DashScope 任务失败、模型不可用、网络超时或没有配置视频模型，接口会自动降级为纯 FFmpeg 拼接，仍然生成最终视频。当前 Demo 只运行一次，不实现工作区历史版本和多轮剪辑对话。

## 11. 前端调用示例

项目自带示例页面：

```text
frontend/index.html
```

启动服务后直接用浏览器打开该文件即可。

### 通用 JavaScript 请求函数

```javascript
const API_BASE = 'http://127.0.0.1:8765/api/v1';

async function apiRequest(path, options = {}) {
  const response = await fetch(`${API_BASE}${path}`, {
    headers: {
      'Content-Type': 'application/json',
      ...(options.headers || {})
    },
    ...options
  });

  const body = await response.json();
  if (!response.ok || body.success === false) {
    throw new Error(body.error?.message || body.detail || `HTTP ${response.status}`);
  }
  return body.data;
}
```

### 调用 Director

```javascript
const result = await apiRequest('/agents/director', {
  method: 'POST',
  body: JSON.stringify({
    user_text: '请拍摄自然的人像短片',
    media_input: {
      source_type: 'FILE',
      paths: ['data/img/img1.jpg', 'data/img/img2.jpg']
    },
    skills_filter: {
      stage: 'director',
      limit: 3
    }
  })
});

console.log(result.shot_plan);
```

### 调用完整流程

```javascript
const result = await apiRequest('/agents/run-all', {
  method: 'POST',
  body: JSON.stringify({
    user_text: '请生成自然的人像短片',
    media_dir: 'data'
  })
});

console.log(result.director);
console.log(result.filming);
console.log(result.editing);
```

### 调用 Skill 列表

```javascript
const result = await apiRequest('/skills?stage=director&limit=10');
console.log(result.skills);
```

## 12. 启动和联调顺序

建议按以下顺序检查：

### 第一步：启动 Mock 服务

```powershell
cd F:\BoldMaker\project00\agents_Module_fast
python fast.py serve --mode mock
```

### 第二步：健康检查

```powershell
Invoke-RestMethod http://127.0.0.1:8765/api/v1/health
```

### 第三步：列媒体

```powershell
Invoke-RestMethod 'http://127.0.0.1:8765/api/v1/media/list?directory=data&type=all'
```

### 第四步：列 Skill

```powershell
Invoke-RestMethod 'http://127.0.0.1:8765/api/v1/skills?limit=20'
```

### 第五步：单独测试三个 Agent

依次调用：

```text
/api/v1/agents/director
/api/v1/agents/cinematographer
/api/v1/agents/editor
```

### 第六步：完整流程

调用：

```text
/api/v1/agents/run-all
```

## 13. Mock 与百炼模式

### Mock 模式

用途：

- 前端接口联调。
- 参数校验。
- 目录和文件路径测试。
- 不消耗 API 额度。

启动：

```powershell
python fast.py serve --mode mock
```

### 百炼模式

用途：

- Director 参考图片分析。
- Cinematographer 视频帧分析。
- Editor 素材语义分析。

启动：

```powershell
python fast.py serve --mode bailian
```

API Key 只从 `.env` 或环境变量读取，不由前端发送。

## 14. 常见问题

### 14.1 返回 404

确认使用的是规范路径：

```text
/api/v1/agents/director
```

不是旧路径以外的自定义路径。

### 14.2 文件不存在

前端传给后端的路径必须是后端进程可访问的路径。浏览器本地文件路径不会自动上传到服务端。

当前接口使用的是服务端路径：

```text
data/img/img1.jpg
data/video/test_video1.mp4
```

如果未来前端需要上传文件，需要另加 multipart 上传接口；当前版本没有把浏览器文件上传伪装成本地路径。

### 14.3 API Key 错误

检查：

- `.env` 是否位于项目根目录。
- `DASHSCOPE_API_KEY` 是否存在。
- `DASHSCOPE_BASE_URL` 与 Key 所属地域是否匹配。
- `DASHSCOPE_MODEL` 是否是账号可用模型。

### 14.4 摄影指导没有帧

先调用：

```text
POST /api/v1/media/extract-frames
```

再把返回的 `frames` 路径传给：

```text
POST /api/v1/agents/cinematographer
```

### 14.5 Editor 没有预览视频

检查：

- 输入视频路径是否存在。
- FFmpeg 是否在 PATH 中。
- 输出目录是否可写。
- 视频是否能被 OpenCV/FFmpeg 读取。

## 15. 测试命令

运行单元测试：

```powershell
cd F:\BoldMaker\project00\agents_Module_fast
pytest -q
```

语法检查：

```powershell
python -m py_compile fast.py api\schemas.py
```

检查 OpenAPI：

```powershell
Invoke-WebRequest http://127.0.0.1:8765/openapi.json
```

## 16. 当前接口边界

当前已实现：

- 本地文件路径输入。
- 本地目录媒体扫描。
- 图片输入。
- 视频抽帧。
- 本地摄像头帧捕获。
- Agent 独立调用。
- Agent 串行调用。
- 本地 Skill 查询和选择。
- Mock/百炼 Provider。

当前未实现：

- 浏览器文件上传。
- X4 Air/Link2 真实设备控制。
- WebSocket 实时摄像头接口。
- 云端 Skill 库。
- Skill CRUD 的完整写接口。

前端不要调用未实现的接口。以 `/openapi.json` 为当前运行代码的最终契约。 
