# 🚀 今晚验证快速启动指南

## 第一步：环境准备 (10分钟)

### 1. 创建 conda 环境

```bash
# 打开终端
cd F:\BoldMaker\project00\algorithm_validation

# 创建环境
conda create -n scenepilot python=3.11 -y

# 激活环境
conda activate scenepilot
```

### 2. 安装依赖

```bash
pip install -r requirements.txt
```

### 3. 验证安装

```bash
# Windows Git Bash
bash verify.sh

# 或者手动验证
python -c "from app.core.schemas import VideoEvent; print('✓ 安装成功')"
```

---

## 第二步：准备测试视频 (15分钟)

### 方案A：拼接 ride_horse 视频 (推荐)

```bash
cd F:\BoldMaker\project00\data\hmdb51_org\ride_horse\ride_horse

# 列出前15个视频
ls *.avi | head -15

# 创建 FFmpeg concat 文件
echo "# 拼接列表" > concat_list.txt
for file in $(ls *.avi | head -15); do
  echo "file '$(cygpath -w $(pwd)/$file)'" >> concat_list.txt
done

# 拼接视频（约2分钟）
ffmpeg -f concat -safe 0 -i concat_list.txt \
  -c:v libx264 -preset fast -crf 23 \
  -c:a aac -b:a 128k \
  F:\BoldMaker\project00\algorithm_validation\data\input\validation_2min.mp4

# 验证视频
ffprobe F:\BoldMaker\project00\algorithm_validation\data\input\validation_2min.mp4
```

### 方案B：使用单个视频 (最快)

```bash
# 直接复制一个视频到输入目录
cp "F:\BoldMaker\project00\data\hmdb51_org\ride_horse\ride_horse\*.avi" \
   F:\BoldMaker\project00\algorithm_validation\data\input\test.avi

# 转换为 MP4
cd F:\BoldMaker\project00\algorithm_validation
ffmpeg -i data/input/test.avi \
  -c:v libx264 -c:a aac \
  data/input/test.mp4
```

---

## 第三步：运行第一次验证 (Mock模式) (5分钟)

```bash
cd F:\BoldMaker\project00\algorithm_validation

python -m app.cli analyze --input data/input/validation_2min.mp4  --intent "跟拍骑马的人，记录动作高潮和跳跃瞬间"  --mock  --output-dir data/output/test1
```

### 预期输出

```
==========================================
ScenePilot 视频分析
==========================================
输入视频: data\input\validation_2min.mp4
用户意图: 跟拍骑马的人，记录动作高潮和跳跃瞬间
输出目录: data\output\test1
模式: Mock
==========================================
📦 初始化模块...
🎥 开始流式读取视频...
  ✓ 选中第 1 帧: index=30, time=1000ms, score=0.654
  ✓ 选中第 2 帧: index=120, time=4000ms, score=0.723
  ...
🎯 STC 压缩完成:
  总帧数: 3600
  选中帧数: 240
  压缩率: 93.33%
🧠 开始语义分析...
✓ 检测到 12 个事件:
  - subject_entry: 骑手进入画面 (1000-2500ms, score=0.65)
  - action_peak: 骑马加速 (5000-8000ms, score=0.85)
  ...
💾 事件已保存: data\output\test1\events.jsonl
🎬 生成导演决策...
✓ 生成 15 条设备命令:
  - start_tracking @ 1000ms
  - start_recording @ 5000ms
  ...
💾 命令已保存: data\output\test1\commands.jsonl
✂️  提取高光片段...
✓ 高光视频已生成: data\output\test1\highlights.mp4
==========================================
📊 运行指标:
  处理时长: 45.23s
  处理速度: 79.6 fps
  总帧数: 3600
  关键帧: 240
  压缩率: 93.33%
  事件数: 12
  命令数: 15
  高光片段: 3
==========================================
✅ 分析完成！输出目录: data\output\test1
==========================================
```

---

## 第四步：检查输出结果 (5分钟)

```bash
# 查看输出文件
ls data/output/test1/

# 应该看到:
# keyframes/         - 关键帧图像
# events.jsonl       - 事件列表
# commands.jsonl     - 设备命令
# metrics.json       - 运行指标
# highlights.mp4     - 高光视频

# 查看运行指标
cat data/output/test1/metrics.json

# 查看事件统计
python -m app.cli stats --events data/output/test1/events.jsonl

# 播放高光视频 (如果有)
# 使用任何视频播放器打开 highlights.mp4
```

---

## 第五步：对比实验 (可选，30分钟)

### 实验 E1: 无 STC vs 有 STC

**修改配置禁用 STC**:
编辑 `.env` 文件：
```bash
STC_FRAME_DIFF_THRESHOLD=0.0
STC_HIST_DIFF_THRESHOLD=0.0
```

```bash
# 运行无 STC
python -m app.cli analyze \
  -i data/input/validation_2min.mp4 \
  --intent "跟拍骑马" \
  --mock \
  -o data/output/e1_no_stc
```

**恢复 STC 配置**:
编辑 `.env` 文件：
```bash
STC_FRAME_DIFF_THRESHOLD=0.15
STC_HIST_DIFF_THRESHOLD=0.20
```

```bash
# 运行有 STC
python -m app.cli analyze \
  -i data/input/validation_2min.mp4 \
  --intent "跟拍骑马" \
  --mock \
  -o data/output/e2_with_stc
```

**对比结果**:
```bash
echo "=== 无 STC ==="
jq . data/output/e1_no_stc/metrics.json

echo "=== 有 STC ==="
jq . data/output/e2_with_stc/metrics.json
```

### 实验 E2: Mock vs 真实 API

**配置百炼 API**:
编辑 `.env` 文件：
```bash
DASHSCOPE_API_KEY=your_actual_key_here
```

```bash
# Mock 模式
python -m app.cli analyze -i data/input/validation_2min.mp4  --intent "跟拍骑马" --mock -o data/output/e3_mock

# 真实 API 模式
python -m app.cli analyze -i data/input/validation_2min.mp4 --intent "跟拍骑马" -o data/output/e3_real
```

**对比事件质量**:
```bash
# Mock 事件
head -3 data/output/e3_mock/events.jsonl

# 真实 API 事件
head -3 data/output/e3_real/events.jsonl
```

---

## 常见问题

### Q1: ModuleNotFoundError: No module named 'app'

**解决**:
```bash
# 确保在正确目录
cd F:\BoldMaker\project00\algorithm_validation

# 确保环境激活
conda activate scenepilot
```

### Q2: FFmpeg 未找到

**解决**:
```bash
# 下载 FFmpeg: https://ffmpeg.org/download.html
# 添加到系统 PATH

# 或在代码中指定完整路径
# 编辑 app/editing/highlight_editor.py
ffmpeg_path = "C:/path/to/ffmpeg.exe"
```

### Q3: OpenCV 无法读取视频

**解决**:
```bash
# 转换视频格式
ffmpeg -i input.avi -c:v libx264 -c:a aac output.mp4
```

### Q4: 百炼 API 超时

**解决**:
```bash
# 增加超时时间
# 编辑 app/core/settings.py
SEMANTIC_TIMEOUT_SEC: int = 120

# 或减少批次大小
# 编辑 .env
STC_MAX_FRAMES_PER_WINDOW=2
```

### Q5: 内存不足

**解决**:
```bash
# 不保存关键帧
python -m app.cli analyze ... --no-save-keyframes

# 增加压缩阈值
# 编辑 .env
STC_FRAME_DIFF_THRESHOLD=0.25
```

---

## 验收标准检查清单

今晚完成的定义：

- [x] ✅ 输入一个本地 MP4 视频
- [x] ✅ 模拟实时播放，按时间顺序读取帧
- [x] ✅ STC 模块丢弃重复帧，保留变化帧
- [x] ✅ 批量传给百炼/Mock，返回结构化事件
- [x] ✅ 状态机输出虚拟设备命令
- [x] ✅ 保存 events.jsonl、commands.jsonl、关键帧、指标
- [x] ✅ FFmpeg 导出高光片段
- [x] ✅ Mock 模式无需 API Key 可运行

---

## 下一步

### 今晚完成后

1. **记录实验结果**: 保存 metrics.json 和截图
2. **验证输出**: 确认 events.jsonl 和 commands.jsonl 格式正确
3. **播放高光**: 确认 highlights.mp4 质量
4. **准备硬件**: 明天硬件到达前检查 SDK 文档

### 明天硬件接入

1. **硬件检查**: 按 02.md 第1节检查清单验证设备
2. **SDK 集成**: 创建 C++ Bridge (Link 2 + X4 Air)
3. **Python Adapter**: 统一设备接口
4. **Edge Agent**: 边缘代理实现
5. **真实测试**: 硬件闭环测试

---

## 需要帮助？

如果遇到问题：

1. **查看日志**: 日志会显示详细的错误信息
2. **查看文档**: `README.md` 和 `COMPLETION_SUMMARY.md`
3. **运行测试**: `pytest tests/ -v` 定位问题
4. **简化场景**: 先用单个短视频测试

---

## 预期时间线

| 步骤 | 预计时间 | 说明 |
|------|---------|------|
| 环境准备 | 10分钟 | conda + pip install |
| 准备视频 | 15分钟 | 拼接或转换 |
| 第一次运行 | 5分钟 | Mock 模式快速验证 |
| 检查输出 | 5分钟 | 确认结果正确 |
| 对比实验 | 30分钟 | 可选：STC 效果、API 对比 |
| **总计** | **约1小时** | 基础验证完成 |

---

## 成功标志

当你看到这些输出时，说明验证成功：

```
✅ 分析完成！输出目录: data/output/test1
```

并且：
- `data/output/test1/` 包含所有预期文件
- `metrics.json` 显示合理的压缩率 (>85%)
- `events.jsonl` 包含至少几个事件
- `commands.jsonl` 包含设备命令
- `highlights.mp4` 可以播放（如果有高光片段）

---

## 现在开始！

```bash
# 1. 激活环境
conda activate scenepilot

# 2. 切换目录
cd F:\BoldMaker\project00\algorithm_validation

# 3. 运行验证脚本
bash verify.sh

# 4. 准备视频（如果还没有）
# 按上面的方案A或B操作

# 5. 运行第一次分析
python -m app.cli analyze \
  --input data/input/validation_2min.mp4 \
  --intent "跟拍骑马的人，记录动作高潮" \
  --mock \
  --output-dir data/output/test1

# 6. 查看结果
python -m app.cli stats --events data/output/test1/events.jsonl
cat data/output/test1/metrics.json
```

祝验证顺利！🎉
