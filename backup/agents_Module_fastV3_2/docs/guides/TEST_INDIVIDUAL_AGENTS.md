# 独立测试各个 Agent 指南

## 概述

使用 `test_agents.py` 脚本可以独立测试每个 Agent，每个 Agent 的输出保存在独立的子目录中。

## 模型配置

当前使用的模型（已在 `.env` 中配置）：

- **视觉模型**：`qwen3-vl-flash` - 用于图片和视频分析
- **文本模型**：`qwen3-vl-plus` - 用于文本理解

各 Agent 使用的模型：
- `SKILLS_MODEL=qwen3-vl-plus` - SkillsManager（文本理解）
- `DIRECTOR_MODEL=qwen3-vl-flash` - Director（图片分析）
- `CINEMATOGRAPHER_MODEL=qwen3-vl-flash` - Cinematographer（视频帧分析）
- `EDITOR_MODEL=qwen3-vl-flash` - Editor（素材分析）

## 测试命令

### 1. 测试 SkillsManager

```bash
# 测试意图理解和 Skill 匹配
python test_agents.py skills --text "我想拍自然的人像" --stage director

# 输出: outputs/skills_manager/skills_director.json
```

**输入**：
- `--text`: 用户的中文拍摄意图
- `--stage`: 当前阶段（director/cinematographer/editor）

**输出**：
- `outputs/skills_manager/skills_{stage}.json` - 匹配的 Skills 和中文解释

---

### 2. 测试 Director Agent

```bash
# 使用单张参考图片
python test_agents.py director --text "请拍摄自然人像" --image data/img/img1.jpg

# 输出: outputs/director/director.json
```

**输入**：
- `--text`: 用户拍摄目标
- `--image`: **单张参考图片路径**

**输出**：
- `outputs/director/director.json` - 导演计划（shot_plan + reference_analysis）

**重要**：只输入一张图片，不是整个目录。

---

### 3. 测试 Cinematographer Agent

```bash
# 使用单个视频文件
python test_agents.py cinematographer --text "拍摄自然人像" --video data/video/test_video1.mp4

# 输出:
#   outputs/cinematographer/filming.json
#   outputs/cinematographer/frames/test_video1/
#   outputs/cinematographer/captures/ (如果有捕获帧)
```

**输入**：
- `--text`: 用户拍摄目标
- `--video`: **单个视频文件路径**

**输出**：
- `outputs/cinematographer/filming.json` - 摄影分析和拍摄建议
- `outputs/cinematographer/frames/` - 抽取的视频帧
- `outputs/cinematographer/captures/` - 标记的优质帧

**重要**：只输入一个视频，不是整个目录。

---

### 4. 测试 Editor Agent

```bash
# 使用视频素材
python test_agents.py editor --video data/video/test_video1.mp4

# 使用图片素材
python test_agents.py editor --image data/img/img1.jpg

# 使用视频+图片
python test_agents.py editor --video data/video/test_video1.mp4 --image data/img/img1.jpg

# 输出:
#   outputs/editor/edit_plan.json
#   outputs/editor/preview.mp4 (如果有视频素材)
```

**输入**：
- `--video`: **单个视频文件路径**（可选）
- `--image`: **单张图片路径**（可选）
- 至少提供一个

**输出**：
- `outputs/editor/edit_plan.json` - 剪辑时间线
- `outputs/editor/preview.mp4` - 预览视频（如果有视频素材）

**重要**：只输入单个文件，不是整个目录。

---

### 5. 测试所有 Agent（完整流程）

```bash
# 完整流程测试
python test_agents.py all --text "请拍摄自然人像短片" --image data/img/img1.jpg --video data/video/test_video1.mp4

# 输出:
#   outputs/skills_manager/
#   outputs/director/
#   outputs/cinematographer/
#   outputs/editor/
```

**输入**：
- `--text`: 用户拍摄目标
- `--image`: 参考图片（用于 Director）
- `--video`: 视频素材（用于 Cinematographer 和 Editor）

**执行顺序**：
1. SkillsManager - 匹配 Skills
2. Director - 分析参考图片，生成拍摄计划
3. Cinematographer - 分析视频帧，给出拍摄建议
4. Editor - 分析素材，生成剪辑时间线

---

## 输出目录结构

```
outputs/
├── skills_manager/
│   └── skills_director.json          # SkillsManager 输出
├── director/
│   └── director.json                  # Director 输出
├── cinematographer/
│   ├── filming.json                   # Cinematographer 输出
│   ├── frames/                        # 视频抽帧
│   │   └── test_video1/
│   │       ├── frame_000000.jpg
│   │       └── frame_000050.jpg
│   └── captures/                      # 捕获的优质帧
│       └── frame_000000.jpg
└── editor/
    ├── edit_plan.json                 # Editor 输出
    └── preview.mp4                    # 预览视频
```

每个 Agent 的输出完全独立，不会互相干扰。

---

## 运行模式

### Mock 模式（不调用真实 API）

```bash
python test_agents.py director --mode mock --image data/img/img1.jpg
```

用于快速测试脚本逻辑，不消耗 API 额度。

### Bailian 模式（调用真实 API）⭐

```bash
python test_agents.py director --mode bailian --image data/img/img1.jpg
```

使用真实的百炼 Qwen-VL 模型，需要在 `.env` 中配置有效的 API Key。

---

## 完整测试示例

### 示例 1：测试 Director

```bash
# 准备一张参考图片
python test_agents.py director \
  --mode bailian \
  --text "请拍摄一组自然的人像短片，保留人物和环境关系" \
  --image data/img/img1.jpg
```

**预期输出**：
```
============================================================
测试 Director Agent
============================================================
输入文本: 请拍摄一组自然的人像短片，保留人物和环境关系
参考图片: data/img/img1.jpg
匹配的 Skills: ['portrait_story_director']

✅ Director 测试完成
输出目录: outputs\director
结果文件: outputs\director\director.json
置信度: 0.85
总结: 建议先拍摄环境全景建立空间感，再拍摄人物中景突出主体
```

### 示例 2：测试 Cinematographer

```bash
# 准备一个视频文件
python test_agents.py cinematographer \
  --mode bailian \
  --text "拍摄自然人像，注意构图和光线" \
  --video data/video/test_video1.mp4
```

**预期输出**：
```
============================================================
测试 Cinematographer Agent
============================================================
输入文本: 拍摄自然人像，注意构图和光线
视频文件: data/video/test_video1.mp4

正在抽取视频帧...
抽取了 12 帧
匹配的 Skills: ['portrait_story_cinematographer']

✅ Cinematographer 测试完成
输出目录: outputs\cinematographer
结果文件: outputs\cinematographer\filming.json
抽帧目录: outputs\cinematographer\frames\test_video1
拍摄建议: capture_frame
捕获帧: outputs/cinematographer/captures/frame_000000.jpg
总结: 当前画面主体清晰，构图合理，建议捕获此帧
```

### 示例 3：测试 Editor

```bash
# 准备视频和图片素材
python test_agents.py editor \
  --mode bailian \
  --video data/video/test_video1.mp4 \
  --image data/img/img1.jpg
```

**预期输出**：
```
============================================================
测试 Editor Agent
============================================================
视频素材: ['data/video/test_video1.mp4']
图片素材: ['data/img/img1.jpg']
匹配的 Skills: ['portrait_story_editor']

✅ Editor 测试完成
输出目录: outputs\editor
结果文件: outputs\editor\edit_plan.json
预览视频: outputs/editor/preview.mp4
总结: 视频作为主要素材，图片作为环境建立镜头，建议 9:16 竖屏格式
```

### 示例 4：完整流程测试

```bash
# 一次性测试所有 Agent
python test_agents.py all \
  --mode bailian \
  --text "请拍摄一组自然的人像短片" \
  --image data/img/img1.jpg \
  --video data/video/test_video1.mp4
```

**预期输出**：
```
============================================================
运行完整测试流程
============================================================

[依次运行 SkillsManager、Director、Cinematographer、Editor]

============================================================
所有测试完成
============================================================
输出根目录: outputs
```

---

## 查看输出结果

### 查看 JSON 文件

```bash
# Windows
type outputs\director\director.json
type outputs\cinematographer\filming.json
type outputs\editor\edit_plan.json

# Linux/Mac
cat outputs/director/director.json
cat outputs/cinematographer/filming.json
cat outputs/editor/edit_plan.json
```

### 查看抽取的视频帧

```bash
dir outputs\cinematographer\frames\test_video1
```

### 播放预览视频

```bash
# 使用 ffplay
ffplay outputs\editor\preview.mp4

# 或直接用媒体播放器打开
outputs\editor\preview.mp4
```

---

## 常见问题

### 1. 错误：需要提供图片或视频参数

**错误信息**：`❌ 错误: Director 测试需要提供 --image 参数`

**解决方案**：确保提供了对应 Agent 需要的输入文件。

```bash
# Director 需要图片
python test_agents.py director --image data/img/img1.jpg

# Cinematographer 需要视频
python test_agents.py cinematographer --video data/video/test_video1.mp4

# Editor 需要视频或图片（至少一个）
python test_agents.py editor --video data/video/test_video1.mp4
```

### 2. API 认证失败

**错误信息**：`API authentication failed`

**解决方案**：检查 `.env` 文件中的 `API_KEY` 是否正确。

```env
API_KEY=sk-ws-xxx...
```

### 3. 模型不可用

**错误信息**：`Model 'qwen3-vl-flash' not available`

**解决方案**：
- 确认账号有该模型的访问权限
- 登录百炼控制台查看可用模型列表
- 如果模型名称错误，更新 `.env` 中的配置

### 4. 视频抽帧失败

**错误信息**：视频帧为空或无法打开

**解决方案**：
- 确认视频文件完整且未损坏
- 尝试使用其他视频格式（mp4, mov）
- 检查 OpenCV 是否正确安装：`pip install opencv-python`

---

## 对比原始 fast.py

### 原始 `fast.py run` 命令的问题

```bash
# 原始命令会读取整个目录
python fast.py run --mode bailian --text "拍摄人像" --media data

# 问题:
# 1. Director 读取 data/img/ 下所有图片（可能很多）
# 2. Cinematographer 处理 data/video/ 下所有视频
# 3. Editor 分析所有素材
# 4. 输出都在 outputs/ 根目录，不分 Agent
```

### 新的 `test_agents.py` 的优势

```bash
# 每个 Agent 独立测试，输入单个文件
python test_agents.py director --image data/img/img1.jpg
python test_agents.py cinematographer --video data/video/test_video1.mp4
python test_agents.py editor --video data/video/test_video1.mp4

# 优势:
# ✅ 输入明确：每次只输入一个文件
# ✅ 输出独立：每个 Agent 有自己的子目录
# ✅ 易于调试：可以单独测试某个 Agent
# ✅ 结果清晰：不会混在一起
```

---

## 验收清单

完成以下检查项即为成功：

- [ ] SkillsManager 能够正确匹配中文意图到 Skills
- [ ] Director 能够分析单张参考图片并生成导演计划
- [ ] Cinematographer 能够抽取视频帧并分析画面质量
- [ ] Cinematographer 能够标记优质帧并保存到 captures/
- [ ] Editor 能够分析单个视频或图片素材
- [ ] Editor 能够生成预览视频（如果有视频素材）
- [ ] 每个 Agent 的输出保存在独立的子目录中
- [ ] 所有 JSON 输出文件格式正确，字段完整
- [ ] 使用 `qwen3-vl-flash` 和 `qwen3-vl-plus` 模型
- [ ] Mock 模式可以快速测试逻辑
- [ ] Bailian 模式调用真实 API 并返回结果

---

## 下一步

1. **准备测试数据**：确保 `data/img/` 和 `data/video/` 中有测试文件
2. **配置 API**：确保 `.env` 中的 API Key 正确
3. **运行测试**：先用 Mock 模式测试逻辑，再用 Bailian 模式测试真实 API
4. **查看结果**：检查 `outputs/` 下各个子目录中的输出文件

```bash
# 快速测试（Mock 模式）
python test_agents.py all --mode mock --image data/img/img1.jpg --video data/video/test_video1.mp4

# 真实测试（Bailian 模式）
python test_agents.py all --mode bailian --image data/img/img1.jpg --video data/video/test_video1.mp4
```
