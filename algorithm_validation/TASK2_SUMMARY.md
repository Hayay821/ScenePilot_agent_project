# Task 2 完成总结

## ✅ Task 2: 流式视频输入 (已完成)

### 已创建的文件

```
app/ingest/
├── __init__.py              # 模块导出
├── video_source.py          # ✅ FileVideoSource 实现
└── ring_buffer.py           # ✅ RingBuffer 实现

tests/
└── test_ingest.py           # ✅ 单元测试
```

### FileVideoSource 功能完成度

| 功能 | 状态 | 说明 |
|------|------|------|
| 读取本地视频 | ✅ | 支持 MP4/AVI 等 OpenCV 支持的格式 |
| realtime 模式 | ✅ | True=模拟实时播放，False=快速读取 |
| 采样控制 | ✅ | 可配置 FPS，默认 2fps |
| 帧缩放 | ✅ | 自动缩放到最大尺寸，保持宽高比 |
| 单调时间戳 | ✅ | 基于帧索引和原始 FPS 计算 |
| 迭代器接口 | ✅ | 支持 `for frame in source` |
| 上下文管理 | ✅ | 支持 `with FileVideoSource() as source` |
| 自动资源释放 | ✅ | __del__ 和 __exit__ 确保释放 |
| 详细日志 | ✅ | 初始化和释放时记录日志 |

### RingBuffer 功能完成度

| 功能 | 状态 | 说明 |
|------|------|------|
| 固定时长缓冲 | ✅ | 默认 10 秒，可配置 |
| 自动清理 | ✅ | 添加新帧时自动清理过期帧 |
| get_recent() | ✅ | 获取最近 N 秒的帧 |
| get_range() | ✅ | 获取指定时间范围的帧 |
| get_before() | ✅ | Pre-roll：事件前 N 秒 |
| get_after() | ✅ | Post-roll：事件后 N 秒 |
| get_around() | ✅ | 事件前后各 N 秒 |
| 统计信息 | ✅ | 帧数、时长、添加/丢弃统计 |

### 验收标准检查

- [x] 使用 OpenCV 读取本地 MP4
- [x] 支持 realtime=False 快速模式
- [x] 支持 realtime=True 模拟实时模式
- [x] 输出单调递增时间戳（基于帧索引和 FPS）
- [x] 10 秒环形缓冲区实现
- [x] 缓冲区支持时间范围查询
- [x] 结束后正确释放文件
- [x] 有完整的单元测试

### 关键设计亮点

1. **抽象接口**: VideoSource 基类便于扩展（摄像头、RTSP等）
2. **时间精确**: 基于帧索引计算时间戳，避免浮点累积误差
3. **实时模拟**: 可选的 sleep 延迟，模拟真实播放速度
4. **自动缩放**: 保持宽高比缩放，减少后续计算量
5. **灵活采样**: 可配置采样帧率，避免处理所有帧
6. **智能缓冲**: RingBuffer 自动维护固定时间窗口
7. **Pre/Post-roll**: 支持事件前后帧查询，用于高光剪辑

### 使用示例

```python
from app.ingest import FileVideoSource, RingBuffer
from app.core.settings import settings

# 快速模式读取视频
with FileVideoSource("data/input/demo.mp4", realtime=False) as source:
    buffer = RingBuffer(duration_sec=10)
    
    for frame in source:
        buffer.add(frame)
        
        # 处理帧
        print(f"Frame {frame.frame_index} at {frame.timestamp_ms}ms")
        
        # 当检测到事件时，可以回溯
        if event_detected:
            preroll_frames = buffer.get_before(
                frame.timestamp_ms, 
                duration_ms=3000
            )

# 实时模式（模拟实时播放）
with FileVideoSource("data/input/demo.mp4", realtime=True) as source:
    for frame in source:
        # 会按照采样帧率延迟输出
        process_frame(frame)
```

### 时间戳计算逻辑

```python
# 原始视频: 30fps, 900 帧
# 采样: 2fps, 间隔 15 帧

frame_index = 0   -> timestamp_ms = 0
frame_index = 15  -> timestamp_ms = 500    (15/30 * 1000)
frame_index = 30  -> timestamp_ms = 1000   (30/30 * 1000)
frame_index = 45  -> timestamp_ms = 1500
...

# 单调递增保证，不受采样影响
```

### 下一步：Task 3 STC 启发式压缩

现在可以实现：
1. `app/stc/base.py` - STCAdapter 抽象接口
2. `app/stc/heuristic.py` - HeuristicSTC 实现
3. 计算帧差、直方图距离、感知哈希
4. 基于变化分数和时间间隔选择关键帧
5. 输出压缩率和选择原因

## 测试验证

```bash
# 安装依赖（如果还没装）
pip install opencv-python-headless loguru

# 单元测试
pytest tests/test_ingest.py -v

# 快速验证（需要真实视频）
python -c "
from app.ingest import FileVideoSource, RingBuffer

# 替换为你的测试视频路径
source = FileVideoSource('data/input/test.mp4', realtime=False)
info = source.get_info()
print(f'视频信息: {info}')

buffer = RingBuffer(duration_sec=10)
count = 0
for frame in source:
    buffer.add(frame)
    count += 1
    if count >= 10:
        break

print(f'读取 {count} 帧')
print(f'缓冲区: {len(buffer)} 帧')
print(f'统计: {buffer.stats}')
source.release()
"
```

### 预期输出

```
INFO - VideoSource initialized: test.mp4 (1920x1080, 30.0fps, 900 frames, 30000ms) -> sample at 2fps, realtime=False
视频信息: {'source_id': 'test', 'width': 1920, 'height': 1080, 'fps': 30.0, ...}
读取 10 帧
缓冲区: 10 帧
统计: {'current_frames': 10, 'total_added': 10, ...}
INFO - VideoSource released: test.mp4
```

## 时间消耗

- 设计接口: 5 分钟
- FileVideoSource 实现: 15 分钟
- RingBuffer 实现: 15 分钟
- 单元测试: 10 分钟
- 文档: 5 分钟
- **总计: 约 50 分钟**

比预估的 20 分钟多，但实现了完整的功能和多种查询方法。

## 技术债务

- [ ] FileVideoSource 暂时不保存帧图片（由调用方决定）
- [ ] 未实现 WebcamVideoSource（今晚不需要）
- [ ] 未实现 RTSP/RTMP 流源（今晚不需要）
- [ ] 集成测试需要准备测试视频文件
