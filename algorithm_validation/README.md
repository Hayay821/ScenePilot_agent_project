# ScenePilot - 算法验证

事件驱动 AI 跟拍导演系统的算法验证实现。

## 快速开始

### 1. 安装依赖

```bash
# 激活 conda 环境
conda activate scenepilot

# 安装依赖
pip install -r requirements.txt
```

### 2. 配置环境变量

复制 `.env.example` 到 `.env` 并填入你的百炼 API Key：

```bash
cp .env.example .env
# 编辑 .env 文件
```

### 3. 运行分析

```bash
# Mock 模式（无需 API Key）
python -m app.cli analyze \
  --input data/input/demo.mp4 \
  --intent "跟拍骑马的人，记录动作高潮" \
  --mock

# 真实 API 模式
python -m app.cli analyze \
  --input data/input/demo.mp4 \
  --intent "跟拍骑马的人，记录动作高潮"
```

### 4. 查看结果

```bash
# 输出目录结构
data/output/
├── keyframes/          # 关键帧图像
├── events.jsonl        # 事件时间线
├── commands.jsonl      # 设备命令
├── metrics.json        # 运行指标
└── highlights.mp4      # 高光视频

# 查看事件统计
python -m app.cli stats --events data/output/events.jsonl
```

## 项目结构

```
algorithm_validation/
├── app/
│   ├── core/              # 核心数据结构
│   │   ├── schemas.py     # Pydantic Schema
│   │   └── settings.py    # 配置管理
│   ├── ingest/            # 视频输入
│   │   ├── file_source.py # 本地文件视频源
│   │   └── ring_buffer.py # 环形缓冲区
│   ├── stc/               # 时空压缩
│   │   └── heuristic.py   # 启发式 STC
│   ├── perception/        # 本地检测（占位）
│   ├── semantic/          # 语义理解
│   │   ├── base.py        # Provider 基类
│   │   ├── mock.py        # Mock Provider
│   │   └── dashscope.py   # 百炼 Provider
│   ├── director/          # 导演状态机
│   │   └── state_machine.py
│   ├── devices/           # 设备适配器
│   │   └── mock_adapter.py
│   ├── editing/           # 高光剪辑
│   │   └── highlight_editor.py
│   └── cli.py             # 命令行接口
├── data/
│   ├── input/             # 输入视频
│   └── output/            # 输出结果
├── tests/                 # 单元测试
├── .env.example           # 环境变量示例
├── requirements.txt       # Python 依赖
└── README.md
```

## 核心模块

### 1. 视频输入 (app.ingest)

**FileVideoSource**: 流式读取本地视频

```python
from app.ingest import FileVideoSource

with FileVideoSource("video.mp4", realtime=False) as source:
    for frame_packet in source:
        print(f"Frame {frame_packet.frame_index} @ {frame_packet.timestamp_ms}ms")
```

- 支持实时模式（按真实时间播放）和快速模式
- 10 秒环形缓冲区
- 单调递增时间戳

### 2. STC 压缩 (app.stc)

**HeuristicSTC**: 启发式时空压缩

```python
from app.stc import HeuristicSTC

stc = HeuristicSTC()
selected = stc.select(frame_packet, frame_data)

if selected:
    print(f"选中原因: {selected.selection_reason}")
    print(f"变化分数: {selected.change_score}")
```

- 帧差检测（灰度差、直方图、感知哈希）
- 可配置阈值
- 输出选择原因和压缩率

### 3. 语义理解 (app.semantic)

**DashScopeVLSemanticProvider**: 百炼视觉理解

```python
from app.semantic import DashScopeVLSemanticProvider

provider = DashScopeVLSemanticProvider()
events = await provider.analyze(
    frames=selected_frames,
    user_intent="跟拍骑马的人"
)

for event in events:
    print(f"{event.event_type}: {event.description}")
```

- 批量发送 2-4 张关键帧
- 结构化 JSON 输出
- 超时、重试、缓存

**MockSemanticProvider**: 模拟模式

- 无需 API Key
- 返回模拟事件
- 快速验证流程

### 4. 导演状态机 (app.director)

**DirectorStateMachine**: 纯函数式状态机

```python
from app.director import DirectorStateMachine

director = DirectorStateMachine()
context = director.create_initial_context()

actions, new_context = director.process_events(
    events=events,
    context=context,
    current_timestamp_ms=10000
)

for action in actions:
    print(f"{action.action_type} @ {action.timestamp_ms}ms")
```

**六状态设计**:
- IDLE: 空闲
- SEARCH: 搜索主体
- TRACK: 跟踪主体
- RECORD: 录制高光
- HIGHLIGHT: 超高光标记
- RECOVER: 容错恢复

### 5. 设备适配器 (app.devices)

**MockDeviceAdapter**: Mock 设备

```python
from app.devices import MockDeviceAdapter

adapter = MockDeviceAdapter(Path("data/output"))
adapter.execute_batch(actions)

stats = adapter.get_stats()
print(f"总命令: {stats['total_commands']}")
```

- 记录命令到 `commands.jsonl`
- 不执行真实操作
- 统计信息

### 6. 高光剪辑 (app.editing)

**HighlightEditor**: FFmpeg 高光提取

```python
from app.editing import HighlightEditor

editor = HighlightEditor()
success = editor.extract_highlights(
    input_video=Path("input.mp4"),
    segments=[(1000, 5000), (10000, 15000)],
    output_path=Path("highlights.mp4")
)
```

- 基于时间段提取
- 自动合并多个片段
- 可配置编码参数

## 命令行接口

### analyze - 分析视频

```bash
python -m app.cli analyze \
  --input VIDEO_PATH \
  --intent "USER_INTENT" \
  [--output-dir OUTPUT_DIR] \
  [--mock] \
  [--realtime] \
  [--save-keyframes/--no-save-keyframes]
```

**参数**:
- `--input, -i`: 输入视频路径（必需）
- `--intent`: 用户拍摄意图（必需）
- `--output-dir, -o`: 输出目录（默认: data/output）
- `--mock`: 使用 Mock 模式（无需 API Key）
- `--realtime/--fast`: 实时模式/快速模式（默认: 快速）
- `--save-keyframes`: 是否保存关键帧（默认: 是）

**输出**:
- `keyframes/`: 关键帧图像（JPG）
- `events.jsonl`: 事件列表（每行一个 JSON）
- `commands.jsonl`: 设备命令（每行一个 JSON）
- `metrics.json`: 运行指标
- `highlights.mp4`: 高光视频（如有）

### stats - 事件统计

```bash
python -m app.cli stats --events data/output/events.jsonl
```

显示事件类型分布、时长、置信度等统计信息。

## 验证实验

### 实验 E1: 基线性能

```bash
# 无 STC，固定 2fps 全送
# 修改 settings.py 禁用 STC
python -m app.cli analyze -i video.mp4 --intent "测试" --mock
```

### 实验 E2: STC 压缩效果

```bash
# 启用 STC 压缩
python -m app.cli analyze -i video.mp4 --intent "测试" --mock

# 对比 metrics.json:
# - compression_ratio: 压缩率
# - selected_frames: 关键帧数
```

### 实验 E3: Mock vs 真实 API

```bash
# Mock 模式
python -m app.cli analyze -i video.mp4 --intent "测试" --mock

# 真实 API 模式
python -m app.cli analyze -i video.mp4 --intent "测试"

# 对比 events.jsonl 的 Schema 一致性
```

### 实验 E4: 不同窗口大小

```bash
# 修改 .env:
# STC_MAX_FRAMES_PER_WINDOW=2  # 2 帧窗口
python -m app.cli analyze -i video.mp4 --intent "测试"

# STC_MAX_FRAMES_PER_WINDOW=4  # 4 帧窗口
python -m app.cli analyze -i video.mp4 --intent "测试"

# 对比延迟与事件召回
```

### 实验 E5: 不同意图

```bash
# 意图 1
python -m app.cli analyze -i video.mp4 --intent "跟拍主体"

# 意图 2
python -m app.cli analyze -i video.mp4 --intent "记录高光时刻"

# 对比事件类型和命令类型的差异
```

## 测试

```bash
# 运行所有测试
pytest tests/ -v

# 运行特定测试
pytest tests/test_stc.py -v
pytest tests/test_director.py -v

# 测试覆盖率
pytest --cov=app tests/
```

## 性能指标

查看 `data/output/metrics.json`:

```json
{
  "total_frames": 3600,
  "selected_frames": 240,
  "compression_ratio": 0.933,
  "events_detected": 12,
  "commands_generated": 15,
  "highlight_segments": 3,
  "processing_time_sec": 45.2,
  "frames_per_second": 79.6
}
```

## 配置

编辑 `.env` 文件：

```bash
# 百炼 API
DASHSCOPE_API_KEY=your_key_here
DASHSCOPE_BASE_URL=https://dashscope.aliyuncs.com/compatible-mode/v1
QWEN_VL_MODEL=qwen-vl-max
QWEN_TEXT_MODEL=qwen-plus

# STC 参数
STC_FRAME_DIFF_THRESHOLD=0.15
STC_HIST_DIFF_THRESHOLD=0.20
STC_MAX_GAP_SEC=3
STC_MIN_FRAMES_PER_WINDOW=1
STC_MAX_FRAMES_PER_WINDOW=4

# 日志级别
LOG_LEVEL=INFO
```

## 故障排查

### FFmpeg 未找到

```bash
# Windows
# 下载 FFmpeg: https://ffmpeg.org/download.html
# 添加到 PATH

# Linux
sudo apt install ffmpeg

# macOS
brew install ffmpeg
```

### OpenCV 无法读取视频

```bash
# 确认视频格式
ffprobe video.mp4

# 转换格式
ffmpeg -i input.avi -c:v libx264 -c:a aac output.mp4
```

### 百炼 API 超时

```bash
# 增加超时时间（settings.py）
SEMANTIC_TIMEOUT_SEC=120

# 减少批次大小
STC_MAX_FRAMES_PER_WINDOW=2
```

### 内存不足

```bash
# 关闭关键帧保存
python -m app.cli analyze ... --no-save-keyframes

# 增加压缩阈值（选择更少的帧）
STC_FRAME_DIFF_THRESHOLD=0.25
```

## 后续步骤

今晚验证完成后，明天需要：

1. **硬件接入**: 对接 X4 Air 和 Link 2 SDK
2. **C++ Bridge**: 创建设备桥服务
3. **Edge Agent**: 边缘代理实现
4. **Cloud Service**: 云端服务实现

详见 `hardware_platform/` 目录。

## 许可证

MIT License
