# ScenePilot Fast 快速测试手册

## 前置准备

### 1. 激活环境并安装依赖

```bash
conda activate base
cd F:\BoldMaker\project00\agents_Module_fast
pip install -r requirements.txt
```

### 2. 确认 .env 配置

确保 `.env` 文件包含以下配置（已存在）：

```env
API_KEY=sk-ws-H.EEMDYID.QmDS.MEUCIQC4GJuh3AE0w0IMCaQ8XewoDACnQQaUWdFlD9mGYA-RYgIgH5wpMhWP7GMToYjoJrXshltncDcmx8PPn6x-uGRuKgw
API_URL=https://llm-fq43z9u2tnoy3m7o.cn-beijing.maas.aliyuncs.com/compatible-mode/v1

# 各 Agent 专用模型配置（性价比优化）
SKILLS_MODEL=qwen-turbo              # SkillsManager: 轻量文本理解
DIRECTOR_MODEL=qwen-vl-plus          # Director: 多模态图片分析
CINEMATOGRAPHER_MODEL=qwen-vl-plus   # Cinematographer: 视频帧分析
EDITOR_MODEL=qwen-vl-plus            # Editor: 素材分析和时间线
```

**模型选型说明**：

| Agent | 模型 | 原因 |
|---|---|---|
| **SkillsManager** | `qwen-turbo` | 中文意图理解、YAML Skill 匹配，轻量高性价比。无需视觉能力 |
| **Director** | `qwen-vl-plus` | 用户目标 + 参考图片分析 → 导演计划。多模态均衡 |
| **Cinematographer** | `qwen-vl-plus` | 视频抽帧分析 → 拍摄建议。视觉理解核心 |
| **Editor** | `qwen-vl-plus` | 视频/图片素材 → 剪辑时间线。兼顾效果与成本 |

支持的环境变量名（按优先级）：
- `DASHSCOPE_API_KEY` / `BAILIAN_API_KEY` / `API_KEY`
- `DASHSCOPE_BASE_URL` / `BAILIAN_BASE_URL` / `API_URL`
- Agent 专用：`SKILLS_MODEL`, `DIRECTOR_MODEL`, `CINEMATOGRAPHER_MODEL`, `EDITOR_MODEL`
- 通用（向后兼容）：`DASHSCOPE_MODEL` / `BAILIAN_MODEL` / `MODEL`

## 快速测试步骤

### 测试 1：检查媒体文件

```bash
python fast.py inspect --media data
```

**预期输出**：显示 data 目录下所有图片和视频的信息

---

### 测试 2：视频抽帧测试

```bash
python fast.py frames --video data/video/test_video1.mp4
```

**预期输出**：
- 在 `outputs/frames/test_video1/` 生成抽取的帧图片
- 终端显示抽取的帧路径列表

---

### 测试 3：Skill 匹配测试（Mock 模式）

```bash
python fast.py skills --text "我想拍自然的人像"
```

**预期输出**：
- 匹配的 Skill 列表
- 中文解释和下一步提示

---

### 测试 4：完整流程 Mock 测试

```bash
python fast.py run --mode mock --text "请拍摄一组自然的人像短片" --media data
```

**预期输出**：
- 使用 Mock provider，不调用真实 API
- 生成 `outputs/run.json`, `outputs/director.json`, `outputs/filming.json`, `outputs/edit_plan.json`
- 如果有视频，生成 `outputs/preview.mp4`

---

### 测试 5：真实百炼 API 完整流程 ⭐

```bash
python fast.py run --mode bailian --text "请拍摄一组自然的人像短片，保留人物和环境关系，不要明显摆拍" --media data
```

**预期输出**：
- 调用真实百炼 Qwen-VL 模型
- Director Agent 分析参考图片并生成拍摄计划
- Cinematographer Agent 分析视频帧并给出拍摄建议
- Editor Agent 生成剪辑时间线和预览视频
- 生成以下文件：
  - `outputs/director.json` - 导演计划
  - `outputs/filming.json` - 摄影分析和建议
  - `outputs/edit_plan.json` - 剪辑时间线
  - `outputs/run.json` - 完整结果汇总
  - `outputs/preview.mp4` - 视频预览（如果有视频素材）
  - `outputs/frames/` - 视频抽帧
  - `outputs/captures/` - 标记的拍摄帧

**注意**：
- 如果 API key 无效，会报错：`API authentication failed`
- 如果模型不可用，会报错：`Model 'xxx' not available`
- 图片会转换为 base64 发送给模型，单次最多 6 张

---

### 测试 6：启动 HTTP 服务

```bash
python fast.py serve
```

服务地址：`http://127.0.0.1:8765`

可用的 API 端点：
- `GET /health` - 健康检查
- `POST /skills/interact` - Skill 交互
- `POST /director` - Director Agent
- `POST /cinematographer` - Cinematographer Agent
- `POST /editor` - Editor Agent
- `POST /run` - 完整流程

测试示例：

```bash
# 健康检查
curl http://127.0.0.1:8765/health

# 完整流程（需要在 PowerShell 中运行）
curl -X POST http://127.0.0.1:8765/run -H "Content-Type: application/json" -d "{\"text\":\"拍摄自然人像\"}"
```

---

### 测试 7：运行单元测试

```bash
pytest -q
```

**预期输出**：
- 所有测试通过
- 测试覆盖：Skill 加载、Mock 模式、专家 Skill 创建、媒体文件发现

---

## 输出文件说明

### 目录结构

```
outputs/
  ├── run.json              # 完整流程结果汇总
  ├── director.json         # 导演计划（拍摄前）
  ├── filming.json          # 摄影分析和建议
  ├── edit_plan.json        # 剪辑时间线
  ├── preview.mp4           # 预览视频（前10秒）
  ├── frames/               # 视频抽帧
  │   └── test_video1/
  │       ├── frame_000000.jpg
  │       ├── frame_000050.jpg
  │       └── ...
  └── captures/             # 标记的拍摄帧
      └── frame_000000.jpg
```

### JSON 字段说明

**director.json**:
```json
{
  "goal": "用户拍摄目标",
  "skills": ["skill_id_list"],
  "shot_plan": [
    {"stage": "establish", "shot": "wide_context", "reason": "原因"},
    {"stage": "subject", "shot": "medium_portrait", "reason": "原因"}
  ],
  "reference_analysis": [
    {
      "image_index": 0,
      "summary": "图片描述",
      "composition": "构图类型",
      "lighting": "光线描述"
    }
  ],
  "confidence": 0.85,
  "user_summary_zh": "中文总结"
}
```

**filming.json**:
```json
{
  "source_frames": [
    {"path": "帧路径", "index": 0, "timestamp_ms": 0}
  ],
  "analysis": {
    "subject_visible": true,
    "face_visible": true,
    "tracking_confidence": 0.87,
    "composition_quality": 0.80,
    "summary": "分析总结"
  },
  "suggestion": {
    "action": "capture_frame",
    "composition": "medium_portrait",
    "reason": "建议理由"
  },
  "captured_frame": "captures/frame_xxx.jpg",
  "user_summary_zh": "中文总结"
}
```

**edit_plan.json**:
```json
{
  "timeline": [
    {
      "source": "视频/图片路径",
      "role": "portrait_source",
      "reason": "选择理由",
      "keep": true
    }
  ],
  "rendered_preview": "outputs/preview.mp4",
  "render": {"ratio": "9:16", "format": "mp4"},
  "analysis_summary": "素材分析总结",
  "user_summary_zh": "中文总结"
}
```

---

## 常见问题

### 1. API Key 错误

**错误信息**：`Bailian mode requires API key`

**解决方案**：
- 确认 `.env` 文件存在且包含 `API_KEY`
- 或者在命令行设置：
  ```bash
  set DASHSCOPE_API_KEY=your_key_here
  python fast.py run --mode bailian --text "测试" --media data
  ```

### 2. 模型不可用

**错误信息**：`Model 'xxx' not available`

**解决方案**：
- 检查 `.env` 中的 `MODEL` 配置
- 尝试使用 `qwen-vl-plus` 或 `qwen-vl-max`
- 确认账号有模型访问权限

### 3. FFmpeg 未安装

**错误信息**：`Failed to generate preview`

**解决方案**：
- 安装 FFmpeg：`conda install ffmpeg` 或从官网下载
- 确认 `ffmpeg` 在系统 PATH 中

### 4. OpenCV 视频读取失败

**错误信息**：视频帧为空或无法打开

**解决方案**：
- 确认视频文件完整且未损坏
- 尝试使用其他视频格式（mp4, mov）
- 检查视频编解码器兼容性

---

## 验收清单

完成以下检查项即为成功：

- [ ] `.env` 文件正确加载，API key 不在日志中泄露
- [ ] `data/img` 图片可以被读取和分析
- [ ] `data/video/test_video1.mp4` 可以抽帧
- [ ] `data/video/test_video2.mp4` 竖屏视频可以处理
- [ ] `skills/repository` 下的 3 个 Skill 文件被正确加载
- [ ] Director Agent 使用真实 Qwen-VL 分析图片并输出导演计划
- [ ] Cinematographer Agent 使用真实抽取帧并输出拍摄建议
- [ ] `capture_frame` 动作会保存帧到 `outputs/captures/`
- [ ] Editor Agent 使用真实素材输出时间线
- [ ] FFmpeg 成功生成 `outputs/preview.mp4`
- [ ] HTTP API 可以独立调用各个 Agent
- [ ] `/run` 端点可以串行调用三个 Agent
- [ ] Mock 模式用于 pytest，真实 `--mode bailian` 不降级
- [ ] `pytest -q` 全部通过
