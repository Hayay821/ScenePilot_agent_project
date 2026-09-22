# 测试所有 4 个 Agent - 完整指南

## 🚀 快速开始

### 方法 1：一键测试所有 Agent（推荐）

```bash
test_all_agents.bat
```

这个脚本会自动依次测试所有 4 个 Agent。

### 方法 2：手动测试单个 Agent

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

---

## 📂 每个 Agent 的输出

### 1. SkillsManager

**输入**：用户文本（中文）  
**输出目录**：`outputs/skills_manager/`  
**输出文件**：`skills_director.json`

**作用**：理解用户意图，匹配合适的拍摄技能

**输出示例**：
```json
{
  "user_intent": "拍摄自然人像视频",
  "matched_skills": [
    {
      "id": "portrait_reel_editor",
      "name": "人像短片剪辑",
      "confidence": 0.9
    }
  ],
  "confidence": 0.85,
  "user_summary_zh": "已识别用户意图：拍摄自然人像视频"
}
```

---

### 2. Director

**输入**：用户文本 + 参考图片  
**输出目录**：`outputs/director/`  
**输出文件**：`director.json`

**作用**：分析参考图片，生成拍摄前的导演计划

**输出示例**：
```json
{
  "goal": "拍摄自然人像",
  "skills": ["portrait_reel_editor"],
  "shot_plan": [
    {
      "stage": "establish",
      "shot": "wide_context",
      "reason": "建立环境和背景"
    },
    {
      "stage": "subject",
      "shot": "medium_portrait",
      "reason": "聚焦主体，清晰的人物构图"
    },
    {
      "stage": "result",
      "shot": "reaction",
      "reason": "捕捉情感反应或结果"
    }
  ],
  "reference_analysis": [
    {
      "image_index": 0,
      "summary": "图片显示温暖的舞台灯光",
      "composition": "中景人像",
      "lighting": "温暖的舞台灯光",
      "subject_position": "居中",
      "emotional_tone": "欢快、团结"
    }
  ],
  "confidence": 0.87,
  "user_summary_zh": "已生成导演拍摄计划"
}
```

---

### 3. Cinematographer

**输入**：用户文本 + 视频（自动抽帧）  
**输出目录**：`outputs/cinematographer/`  
**输出文件**：
- `filming.json` - 拍摄分析结果
- `frames/test_video1/` - 视频抽帧（自动生成）
- `captures/` - 捕获的优质帧（如果 confidence > 0.6）

**作用**：实时分析相机画面，决定是否拍摄

**输出示例**：
```json
{
  "source_frames": [
    {
      "path": "outputs/frames/test_video1/frame_0001.jpg",
      "index": 0,
      "timestamp_ms": 0
    }
  ],
  "analysis": {
    "subject_visible": true,
    "face_visible": true,
    "tracking_confidence": 0.87,
    "composition_quality": 0.80,
    "summary": "画面清晰，人物居中，构图良好",
    "confidence": 0.85
  },
  "suggestion": {
    "action": "capture_frame",
    "composition": "medium_portrait",
    "reason": "当前画面质量优秀，适合拍摄"
  },
  "captured_frame": "outputs/captures/frame_0001.jpg",
  "user_summary_zh": "已分析当前画面并标记拍摄建议。"
}
```

---

### 4. Editor

**输入**：视频 + 图片（可选）  
**输出目录**：`outputs/editor/`  
**输出文件**：
- `edit_plan.json` - 剪辑计划
- `preview.mp4` - 预览视频（前 10 秒）

**作用**：分析视频素材，生成剪辑时间线和预览

**输出示例**：
```json
{
  "timeline": [
    {
      "source": "data/video/test_video1.mp4",
      "role": "portrait_source",
      "reason": "主要视频素材",
      "keep": true,
      "ai_role": "main_portrait",
      "ai_reason": "主要人物特写"
    }
  ],
  "rendered_preview": "outputs/editor/preview.mp4",
  "render": {
    "ratio": "9:16",
    "format": "mp4"
  },
  "analysis_summary": "素材光照良好，构图一致，适合剪辑成温馨的人像短片",
  "user_summary_zh": "已生成剪辑时间线和预览视频。素材光照良好..."
}
```

---

## 🧪 测试命令汇总

### 使用真实 API（Bailian 模式）

```bash
# 一键测试所有
test_all_agents.bat

# 或手动测试
python test_agents.py skills_manager --mode bailian --text "拍摄自然人像视频"
python test_agents.py director --mode bailian --text "拍摄自然人像" --image data/img/img1.jpg
python test_agents.py cinematographer --mode bailian --text "拍摄自然人像" --video data/video/test_video1.mp4
python test_agents.py editor --mode bailian --video data/video/test_video1.mp4
```

### 使用 Mock 模式（不调用 API，快速测试）

```bash
python test_agents.py skills_manager --mode mock --text "拍摄自然人像视频"
python test_agents.py director --mode mock --text "拍摄自然人像" --image data/img/img1.jpg
python test_agents.py cinematographer --mode mock --text "拍摄自然人像" --video data/video/test_video1.mp4
python test_agents.py editor --mode mock --video data/video/test_video1.mp4
```

---

## 📋 测试前检查清单

- [ ] `.env` 文件配置正确
  - `API_KEY` 已设置且有效
  - `API_URL` 指向百炼 API
  - 模型设置为 `qwen3-vl-flash` 和 `qwen3-vl-plus`

- [ ] 测试数据已准备
  - `data/img/img1.jpg` 存在（用于 Director 测试）
  - `data/video/test_video1.mp4` 存在（用于 Cinematographer 和 Editor 测试）

- [ ] 依赖已安装
  ```bash
  pip install openai python-dotenv pillow
  ```

- [ ] FFmpeg 已安装（用于视频处理）
  ```bash
  ffmpeg -version
  ```

---

## 🎯 查看测试结果

### 方法 1：命令行查看 JSON

```bash
# Windows
type outputs\skills_manager\skills_director.json
type outputs\director\director.json
type outputs\cinematographer\filming.json
type outputs\editor\edit_plan.json

# Linux/Mac
cat outputs/skills_manager/skills_director.json
cat outputs/director/director.json
cat outputs/cinematographer/filming.json
cat outputs/editor/edit_plan.json
```

### 方法 2：播放预览视频

```bash
# 使用 ffplay（FFmpeg 自带）
ffplay outputs\editor\preview.mp4

# 或用系统默认播放器打开
start outputs\editor\preview.mp4
```

### 方法 3：打开输出目录

```bash
explorer outputs
```

---

## ⚠️ 常见问题

### 1. 视觉分析失败

**问题**：看到 `Warning: Vision analysis failed: Connection error`

**原因**：
- API Key 有空格或格式错误
- API URL 配置错误
- 模型名称不正确

**解决方案**：
1. 检查 `.env` 文件，确保 `API_KEY` 行末尾没有空格
2. 确认 `API_URL` 是 `https://...aliyuncs.com/compatible-mode/v1`
3. 确认模型名称是 `qwen3-vl-flash` 和 `qwen3-vl-plus`

### 2. 输出是英文

**问题**：JSON 中的 `summary`、`reason` 等字段是英文

**解决方案**：
- 已修复！所有 Agent 的 prompt 已改为中文
- 重新运行测试即可

### 3. FFmpeg 相关错误

**问题**：`FileNotFoundError: [WinError 2] The system cannot find the file specified`

**解决方案**：
1. 下载 FFmpeg：https://ffmpeg.org/download.html
2. 解压后将 `ffmpeg.exe` 所在目录添加到系统 PATH
3. 验证安装：`ffmpeg -version`

### 4. 测试数据不存在

**问题**：`FileNotFoundError: data/img/img1.jpg`

**解决方案**：
- 确保测试数据存在：
  - `data/img/img1.jpg` - 任意图片
  - `data/video/test_video1.mp4` - 任意视频

---

## 🎉 测试成功标志

如果看到以下内容，说明测试成功：

```
✅ SkillsManager 测试完成
✅ Director 测试完成
✅ Cinematographer 测试完成
✅ Editor 测试完成
```

并且：
- `outputs/skills_manager/skills_director.json` 存在
- `outputs/director/director.json` 存在
- `outputs/cinematographer/filming.json` 存在
- `outputs/editor/edit_plan.json` 存在
- `outputs/editor/preview.mp4` 存在（可播放）

---

## 📞 需要帮助？

如果遇到问题：
1. 查看上面的"常见问题"章节
2. 检查 `.env` 文件配置
3. 确认测试数据存在
4. 使用 `--mode mock` 先测试逻辑是否正确

**祝测试顺利！** 🚀
