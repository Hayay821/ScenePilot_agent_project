# ScenePilot Fast：真实百炼多模态实现任务

目标执行者：Claude Coding  
工作目录：`F:\BoldMaker\project00\agents_Module_fast`  
当前任务：使用本地真实图片/视频和 `.env` 中已有的百炼 API 配置，完成四 Agent 的真实多模态闭环。

## 1. 重要范围

这是对当前 Fast 版本的增量实现，不要迁移旧的 `agents_Module`，不要引入旧项目的复杂架构。

必须保留当前轻量结构：

```text
fast.py
skills/repository/
data/img/
data/video/
outputs/
tests/test_fast.py
```

允许修改：

- `fast.py`
- `tests/test_fast.py`
- `README.md`
- `skills/repository/**/*.yaml` 的必要兼容字段
- `requirements.txt`，仅增加必要依赖

不要新增：

- 数据库、Redis、Kafka、消息队列。
- 多个 Agent 基类和复杂编排层。
- 真实相机 SDK。
- 云端 Skill 库。
- 大量测试文件。
- Web 前端。

## 2. 当前真实数据路径

不要再使用 `media/` 作为默认输入目录。当前测试数据是：

```text
F:\BoldMaker\project00\agents_Module_fast\data\img
F:\BoldMaker\project00\agents_Module_fast\data\video
```

当前媒体：

- `data/img/`：15 张本地图片，包括 `img1.jpg`、`img2.jpg` 和多张微信图片。
- `data/video/test_video1.mp4`：横屏视频，已确认可以读取，1280x720，约 30 FPS。
- `data/video/test_video2.mp4`：竖屏视频，已确认可以读取，720x1280，约 30 FPS。

默认配置：

```python
MEDIA_ROOT = PROJECT_ROOT / "data"
IMAGE_ROOT = MEDIA_ROOT / "img"
VIDEO_ROOT = MEDIA_ROOT / "video"
SKILLS_ROOT = PROJECT_ROOT / "skills" / "repository"
OUTPUT_ROOT = PROJECT_ROOT / "outputs"
```

所有路径都必须支持命令行覆盖。

## 3. Skill 数据路径和兼容格式

Skill 根目录：

```text
F:\BoldMaker\project00\agents_Module_fast\skills\repository
```

当前结构：

```text
skills/repository/
  builtin/
    director/portrait_story_director.yaml
    cinematographer/portrait_composition_coach.yaml
    editor/portrait_reel_editor.yaml
```

当前 YAML 使用的字段包括：

- `skill_id`
- `version`
- `name`
- `name_en`
- `description`
- `agent_bindings`
- `tags`
- `rules`
- `teaching`
- `safety`

代码加载时生成内部统一字段：

```python
skill["id"] = skill.get("id") or skill.get("skill_id")
```

不要要求用户把现有 YAML 重写成另一种格式。Skill 的匹配可以同时使用：

- 中文用户输入的轻量关键词映射。
- YAML `tags`。
- `agent_bindings`。
- Skill 所在的 `director/cinematographer/editor` 目录。

## 4. `.env` 和百炼配置

API Key 已存在于：

```text
F:\BoldMaker\project00\agents_Module_fast\.env
```
支持以下变量名：

```text
DASHSCOPE_API_KEY=...
DASHSCOPE_BASE_URL=https://dashscope.aliyuncs.com/compatible-mode/v1
DASHSCOPE_MODEL=...
```

兼容别名：

```text
BAILIAN_API_KEY
BAILIAN_BASE_URL
BAILIAN_MODEL
```

优先级：命令行参数 > 进程环境变量 > `.env` > 默认值。

如果 `.env` 中已经配置了模型名，优先使用该模型；如果没有，默认选择账号可用的快速 Qwen 视觉模型。不要硬编码一个未经账号确认的模型名。建议初始默认值为：

```text
qwen-vl-plus
```

如果该模型不可用，错误信息必须明确提示“请检查 DASHSCOPE_MODEL”，而不是静默回退 Mock。

## 5. 真实 Provider 要求

当前主流程使用真实百炼，不使用 Mock。

保留 Mock 仅用于离线单元测试和 API 失败时的显式测试模式。

### 5.1 OpenAI 兼容接口

使用：

```python
from openai import OpenAI

client = OpenAI(
    api_key=api_key,
    base_url=base_url,
)
```

调用：

```python
client.chat.completions.create(
    model=model,
    messages=[...],
    temperature=0.2,
)
```

### 5.2 多模态图片输入

本地图片先转换成 data URL：

```text
data:image/jpeg;base64,...
```

一次调用最多发送 4 到 6 张图片，避免请求过大。必须记录：

- 图片路径。
- 图片 SHA256。
- 模型名。
- 请求时间。
- 响应耗时。
- 解析状态。

不要把完整原图写入日志。

### 5.3 结构化输出

模型要求输出 JSON，不要依赖模型自然语言解析。至少支持以下结果：

```json
{
  "summary": "...",
  "observations": [
    {
      "type": "subject_visibility",
      "value": "clear",
      "confidence": 0.92
    }
  ],
  "events": ["subject_visible", "portrait_usable"],
  "suggestions": [
    {
      "action": "capture_frame",
      "composition": "medium_portrait",
      "reason": "..."
    }
  ],
  "confidence": 0.88
}
```

实现一个轻量 JSON 提取函数，处理模型偶尔返回 Markdown code fence 的情况：

```text
```json
{...}
```
```

解析失败：

- 重试一次，提示“只返回 JSON”。
- 第二次失败返回明确错误，不伪造成功结果。
- 只有命令行明确指定 `--mode mock` 时才允许 Mock。

## 6. 四 Agent 的真实实现边界

### 6.1 SkillsManager Agent

输入：

- 中文用户需求。
- 阶段：`director`、`cinematographer`、`editor`。
- 本地 Skill YAML。

输出：

- 匹配的 Skill ID。
- Skill 英文规则摘要。
- 中文解释。
- 给目标 Agent 的 Skill 文本上下文。

当前不做云端 Skill 查询。

### 6.2 Director Agent

输入：

- 中文用户目标。
- Director Skill。
- `data/img` 中的最多 6 张参考图片。

真实调用 Qwen-VL，要求：

1. 分析图片中人物、环境、光线、构图和情绪。
2. 结合用户目标生成拍摄前导演计划。
3. 输出 3 到 6 个阶段镜头意图。
4. 给中文用户返回说明。

输出：

```json
{
  "goal": "...",
  "reference_analysis": [
    {
      "path": "...",
      "summary": "...",
      "composition": "...",
      "lighting": "..."
    }
  ],
  "shot_plan": [
    {"stage": "establish", "shot": "wide_context", "reason": "..."},
    {"stage": "subject", "shot": "medium_portrait", "reason": "..."},
    {"stage": "result", "shot": "reaction", "reason": "..."}
  ],
  "confidence": 0.85,
  "user_summary_zh": "..."
}
```

### 6.3 Cinematographer Agent

输入：

- `data/video` 中视频抽取的帧。
- `data/img` 中用户指定的当前图像。
- Cinematographer Skill。
- 用户当前拍摄目标。

视频处理要求：

- 不把完整视频直接发送给模型。
- 使用 OpenCV 抽帧。
- 默认每 2 秒抽一帧，最多 12 帧。
- 输出到 `outputs/frames/<video_stem>/`。
- 每帧保留原始视频路径和时间戳。

真实调用 Qwen-VL，要求判断：

- 主体是否可见。
- 主体是否被遮挡。
- 构图是否可用。
- 脸部是否清晰。
- 是否应该拍照/标记当前帧。
- 下一步景别、构图和跟踪建议。

输出：

```json
{
  "source_frames": [
    {"path": "...", "timestamp_ms": 0}
  ],
  "analysis": {
    "subject_visible": true,
    "face_visible": true,
    "tracking_confidence": 0.87,
    "composition_quality": 0.80,
    "summary": "..."
  },
  "suggestion": {
    "action": "capture_frame",
    "composition": "medium_portrait",
    "reason": "..."
  },
  "captured_frame": "outputs/frames/...jpg",
  "user_summary_zh": "..."
}
```

注意：当前没有真实相机，因此“拍照”表示保存当前可用帧到 `outputs/captures/`。未来设备执行器接入后，沿用 `action=capture_frame`，不改 Agent 输出协议。

### 6.4 Editor Agent

输入：

- `data/video` 中的视频。
- `data/img` 中的图片。
- Editor Skill。
- Director 输出的目标或用户后期要求。

真实调用 Qwen-VL 分析抽取帧和素材摘要，生成：

- 片段角色。
- 选择理由。
- 时间线顺序。
- 人像/环境/反应镜头组织。
- 9:16/16:9 输出建议。

然后必须执行本地 FFmpeg 粗剪：

- 默认取第一个视频前 10 秒作为可播放预览。
- 输出 `outputs/preview.mp4`。
- 不要求本晚实现复杂转场、音乐和全景重投影。
- JSON 计划必须保存为 `outputs/edit_plan.json`。

输出：

```json
{
  "timeline": [
    {
      "source": "data/video/test_video1.mp4",
      "role": "portrait_source",
      "reason": "...",
      "keep": true
    }
  ],
  "rendered_preview": "outputs/preview.mp4",
  "render": {"ratio": "9:16", "format": "mp4"},
  "user_summary_zh": "..."
}
```

## 7. 真实媒体运行命令

先检查媒体：

```powershell
cd F:\BoldMaker\project00\agents_Module_fast
python fast.py inspect --media data
```

生成视频抽帧：

```powershell
python fast.py frames --video data\video\test_video1.mp4
```

直接调用真实百炼跑完整流程：

```powershell
python fast.py run \
  --mode bailian \
  --text "请拍摄一组自然的人像短片，保留人物和环境关系，不要明显摆拍" \
  --media data
```

Windows PowerShell 也可以使用单行命令：

```powershell
python fast.py run --mode bailian --text "请拍摄一组自然的人像短片，保留人物和环境关系，不要明显摆拍" --media data
```

输出检查：

```text
outputs/run.json
outputs/director.json
outputs/filming.json
outputs/edit_plan.json
outputs/frames/
outputs/captures/
outputs/preview.mp4
```

如果当前 CLI 还没有拆分保存 `director.json`、`filming.json`、`edit_plan.json`，Claude 必须补上，但不要改变 `run.json` 既有输出。

## 8. 真实 API 测试要求

不要用 Mock 代替真实多模态测试。最少完成：

1. 用 `data/img` 的 2 到 6 张图片调用 Director。
2. 用 `data/video/test_video1.mp4` 抽取帧调用 Cinematographer。
3. 用 `data/video/test_video2.mp4` 验证竖屏视频处理。
4. 用两个视频和若干图片调用 Editor。
5. 生成 `outputs/preview.mp4` 并检查文件存在且大小大于 0。
6. 保存真实模型响应的结构化摘要，不保存 API Key。

真实 API 测试失败时必须输出具体原因：

- API Key 未加载。
- Base URL 错误。
- 模型不存在或无权限。
- 请求超时。
- 图片过大。
- JSON 解析失败。

不得在真实 API 失败时静默显示 Mock 成功。

## 9. Claude Coding 最小任务顺序

### Task 1：配置加载

```text
读取 agents_Module_fast/.env，不打印密钥；支持 DASHSCOPE_API_KEY、DASHSCOPE_BASE_URL、DASHSCOPE_MODEL；默认使用 qwen-vl-plus；命令行 --mode bailian 时必须真实调用，不自动 fallback 到 Mock。
```

### Task 2：Skill Repository 兼容

```text
让 SkillManager 递归读取 skills/repository/**/*.yaml，兼容 skill_id/id、agent_bindings/stage、中文 tags 和现有 builtin 子目录。不要重写 Skill 文件。
```

### Task 3：真实图片 Provider

```text
实现 Qwen vision provider：本地图片转 data URL，多图请求，JSON 解析，Markdown code fence 清理，超时和一次重试。把 Director、Cinematographer、Editor 的视觉调用接入该 Provider。
```

### Task 4：真实视频预处理

```text
使用 OpenCV 读取 data/video 下的视频，每 2 秒抽帧最多 12 帧，保存时间戳 manifest。不要把完整视频上传模型。
```

### Task 5：真实 Editor 输出

```text
根据真实模型返回的时间线生成 edit_plan.json，并使用 FFmpeg 导出 outputs/preview.mp4。保持现有 run.json 兼容。
```

### Task 6：真实验收

```text
使用 data/img、test_video1.mp4、test_video2.mp4 和 .env 运行真实百炼流程；保存每个 Agent 的 JSON 输出、抽帧目录和 preview.mp4；运行 pytest，Mock 测试和真实 CLI smoke test 都通过。
```

## 10. 只允许的代码范围

优先只改：

```text
fast.py
README.md
IMPLEMENTATION_PLAN.md
requirements.txt
tests/test_fast.py
```

允许新增：

```text
tasks/REAL_BAILIAN_QWEN_IMPLEMENTATION.md
```

不要创建几十个 Python 文件。真实多模态实现仍然集中在 `fast.py`，等本晚闭环稳定后再拆分。

## 11. 验收标准

- [ ] `.env` 被安全加载，密钥不进入日志和输出。
- [ ] `data/img` 图片被真实读取。
- [ ] `data/video/test_video1.mp4` 可以抽帧。
- [ ] `data/video/test_video2.mp4` 可以处理竖屏输入。
- [ ] `skills/repository` 下三个现有 Skill 被加载。
- [ ] Director 使用真实 Qwen-VL 分析图片并输出导演计划。
- [ ] Cinematographer 使用真实抽取帧并输出拍摄建议。
- [ ] `capture_frame` 会保存当前帧到输出目录。
- [ ] Editor 使用真实素材输出时间线。
- [ ] FFmpeg 成功生成 `outputs/preview.mp4`。
- [ ] 三个 Agent 可以通过独立 HTTP endpoint 调用。
- [ ] `/run` 可以串行调用三个 Agent。
- [ ] Mock 仅用于离线 pytest，真实 CLI `--mode bailian` 不静默降级。
- [ ] `pytest -q` 通过。
