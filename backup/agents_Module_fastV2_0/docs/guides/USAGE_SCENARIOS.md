# ScenePilot Fast 使用场景说明

## 重要前提

当前版本使用 `F:\BoldMaker\project00\agents_Module_fast\data\` 目录下的图片和视频作为输入，**不是接入真实摄像机**。这些媒体文件用于模拟真实拍摄场景，测试和验证各 Agent 的分析能力。

## 媒体文件的含义

### data/img/ - 参考图片或已拍摄素材
- **在真实场景中**：用户提供的参考图片（如 Pinterest 灵感图、之前拍过的作品）
- **在当前测试中**：15 张本地图片，包括 `img1.jpg`、`img2.jpg` 等
- **被谁使用**：Director Agent 分析这些图片，学习构图、光线、风格
- **输出到哪里**：`outputs/director.json` 的 `reference_analysis` 字段

**示例**：用户说"我想拍自然的人像"，并提供几张喜欢的参考图。Director Agent 分析这些图片后说：
- 图 1：medium portrait，soft natural light，subject centered
- 图 2：wide context，golden hour，subject off-center left
- 建议：先拍 wide_context 建立环境，再拍 medium_portrait 突出人物

---

### data/video/ - 已拍摄的视频素材
- **在真实场景中**：用户已经用手机/相机拍摄完成的视频文件
- **在当前测试中**：`test_video1.mp4`（横屏 1280x720）和 `test_video2.mp4`（竖屏 720x1280）
- **被谁使用**：
  - Cinematographer Agent 抽取视频帧，分析每一帧的画面质量
  - Editor Agent 分析完整视频，规划剪辑时间线
- **输出到哪里**：
  - `outputs/frames/test_video1/` - 抽取的帧图片
  - `outputs/filming.json` - Cinematographer 的画面分析
  - `outputs/edit_plan.json` - Editor 的剪辑计划
  - `outputs/preview.mp4` - Editor 生成的预览视频

---

## 各 Agent 如何使用这些文件

### 1. SkillsManager
- **不读取媒体文件**
- 只处理用户的中文文本输入
- 匹配本地 YAML Skill 库

---

### 2. Director Agent（拍摄前规划）

**输入**：
- 用户目标：`--text "请拍摄一组自然的人像短片"`
- 参考图片：`data/img/` 中的所有图片（最多 6 张）

**处理**：
1. 使用 Qwen-VL 多模态模型分析每张参考图片
2. 提取构图类型（wide_context, medium_portrait, close_detail）
3. 提取光线特点（natural, soft, golden_hour）
4. 提取主体状态（centered, off-center, in-motion）

**输出**：`outputs/director.json`
```json
{
  "goal": "拍摄自然人像短片",
  "shot_plan": [
    {"stage": "establish", "shot": "wide_context", "reason": "建立环境和人物关系"},
    {"stage": "subject", "shot": "medium_portrait", "reason": "突出人物表情和姿态"}
  ],
  "reference_analysis": [
    {
      "image_index": 0,
      "summary": "自然光下的中景人像",
      "composition": "medium_portrait",
      "lighting": "soft_natural"
    }
  ]
}
```

**现实类比**：导演在开拍前看参考图，制定拍摄方案

---

### 3. Cinematographer Agent（拍摄中指导）

**输入**：
- 用户目标：`--text "请拍摄自然人像"`
- 视频抽帧：从 `data/video/test_video1.mp4` 抽取帧（默认 2 秒一帧）

**处理**：
1. 使用 OpenCV 从视频中抽取关键帧
2. 使用 Qwen-VL 分析每一帧的画面质量：
   - 主体是否可见（subject_visible）
   - 面部是否清晰（face_visible）
   - 构图质量（composition_quality: 0-1）
   - 跟踪置信度（tracking_confidence: 0-1）
3. 判断是否值得捕获此帧

**输出**：`outputs/filming.json`
```json
{
  "source_frames": [
    {"path": "outputs/frames/test_video1/frame_000000.jpg", "timestamp_ms": 0}
  ],
  "analysis": {
    "subject_visible": true,
    "face_visible": true,
    "composition_quality": 0.85,
    "tracking_confidence": 0.90
  },
  "suggestion": {
    "action": "capture_frame",
    "composition": "medium_portrait",
    "reason": "主体清晰，构图合理，光线自然"
  },
  "captured_frame": "outputs/captures/frame_000000.jpg"
}
```

**现实类比**：
- **真实场景**：摄影师实时查看取景器，判断当前画面是否值得按下快门
- **当前模拟**：分析视频的每一帧，标记哪些帧画面质量好
- **未来扩展**：接入真实相机后，`capture_frame` 可以触发真实拍摄

**重要说明**：
- 抽取的帧 ≈ 取景器中的实时画面
- `capture_frame` ≈ 按下快门的时机建议
- 当前会保存标记的帧到 `outputs/captures/`

---

### 4. Editor Agent（后期剪辑）

**输入**：
- 所有视频：`data/video/*.mp4`
- 所有图片：`data/img/*.jpg`
- 捕获的帧：`outputs/captures/*.jpg`

**处理**：
1. 使用 Qwen-VL 分析每个素材的内容和质量
2. 判断每个素材的角色（portrait_source, context_source, transition）
3. 规划剪辑顺序
4. 使用 FFmpeg 生成预览视频（前 10 秒粗剪）

**输出**：
- `outputs/edit_plan.json` - 剪辑计划
- `outputs/preview.mp4` - 预览视频

```json
{
  "timeline": [
    {
      "source": "data/video/test_video1.mp4",
      "role": "portrait_source",
      "reason": "包含清晰的人物镜头，适合作为主要素材",
      "keep": true
    },
    {
      "source": "data/img/img1.jpg",
      "role": "context_source",
      "reason": "环境建立镜头",
      "keep": true
    }
  ],
  "rendered_preview": "outputs/preview.mp4",
  "render": {"ratio": "9:16", "format": "mp4"}
}
```

**现实类比**：剪辑师在 Premiere/Final Cut 中分析素材，规划剪辑时间线

---

## 完整测试流程

### 准备数据
```bash
# 确认测试数据存在
dir F:\BoldMaker\project00\agents_Module_fast\data\img
dir F:\BoldMaker\project00\agents_Module_fast\data\video
```

### 运行完整流程
```bash
cd F:\BoldMaker\project00\agents_Module_fast
python fast.py run --mode bailian --text "请拍摄一组自然的人像短片，保留人物和环境关系" --media data
```

### 执行过程

1. **Director 阶段**
   - 读取 `data/img/` 中的图片（最多 6 张）
   - 调用 Qwen-VL 分析每张图片
   - 生成 `outputs/director.json`

2. **Cinematographer 阶段**
   - 发现 `data/video/test_video1.mp4` 和 `test_video2.mp4`
   - 使用 OpenCV 抽帧到 `outputs/frames/`
   - 调用 Qwen-VL 分析每一帧
   - 标记优质帧，保存到 `outputs/captures/`
   - 生成 `outputs/filming.json`

3. **Editor 阶段**
   - 读取所有视频、图片、捕获的帧
   - 调用 Qwen-VL 分析素材内容
   - 规划剪辑时间线
   - 使用 FFmpeg 生成 `outputs/preview.mp4`
   - 生成 `outputs/edit_plan.json`

4. **汇总**
   - 生成 `outputs/run.json`，包含三个 Agent 的完整结果

### 检查输出
```bash
# 查看导演计划
cat outputs/director.json

# 查看摄影分析
cat outputs/filming.json

# 查看剪辑计划
cat outputs/edit_plan.json

# 播放预览视频
ffplay outputs/preview.mp4
```

---

## 与真实场景的对应关系

| 真实场景 | 当前模拟 | 数据来源 | 未来扩展 |
|---|---|---|---|
| 用户描述需求 | `--text` 参数 | 命令行输入 | 语音输入、对话界面 |
| 提供参考图片 | Director 分析本地图片 | `data/img/` | 用户上传、网络图片 |
| 实时查看取景器 | Cinematographer 分析视频帧 | `data/video/` 抽帧 | 真实相机 SDK 实时流 |
| 按下快门拍摄 | 保存优质帧到 captures/ | `capture_frame` 建议 | 触发相机拍摄 API |
| 查看已拍摄素材 | Editor 分析本地文件 | `data/` 所有媒体 | 相机存储卡、云端素材库 |
| 在 Premiere 中剪辑 | FFmpeg 生成预览 | `outputs/preview.mp4` | 导出到 Premiere XML |

---

## 常见误解澄清

### ❌ 误解 1：Cinematographer 会控制真实摄像机拍摄
**实际**：当前只是分析视频抽帧，标记优质画面。未来接入 SDK 时才能触发真实拍摄。

### ❌ 误解 2：data/ 中的视频是实时拍摄的
**实际**：这些是预先准备的测试视频，用于模拟「已拍摄的素材」。

### ❌ 误解 3：Director 会指导如何拍摄
**实际**：Director 根据参考图片生成拍摄计划（shot_plan），Cinematographer 根据实时画面给出拍摄建议。

### ✅ 正确理解
- **Director**：拍摄前规划师（根据参考图制定方案）
- **Cinematographer**：拍摄中指导师（分析当前画面质量）
- **Editor**：后期剪辑师（分析素材并规划时间线）
- **SkillsManager**：技术顾问（提供拍摄技巧和规则）

---

## 总结

ScenePilot Fast 通过分析 `data/` 目录下的媒体文件，验证了四个 Agent 的核心能力：

1. **读取媒体**：图片、视频、抽帧 ✅
2. **调用多模态模型**：Qwen-VL 图片/视频分析 ✅
3. **结构化输出**：JSON 格式的计划、分析、时间线 ✅
4. **生成预览**：FFmpeg 视频合成 ✅

未来接入真实设备后，`capture_frame` 等建议可以直接触发硬件动作。
