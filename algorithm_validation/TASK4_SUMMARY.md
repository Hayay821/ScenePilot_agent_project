# Task 4 完成总结

## ✅ Task 4: 语义 Provider (已完成)

### 已创建的文件

```
app/semantic/
├── __init__.py              # 模块导出
├── base.py                  # ✅ SemanticProvider 抽象接口
├── mock.py                  # ✅ MockSemanticProvider 实现
└── dashscope_vl.py          # ✅ DashScopeVLSemanticProvider 实现

tests/
└── test_semantic.py         # ✅ 单元测试（10个测试用例）
```

### MockSemanticProvider 功能完成度

| 功能 | 状态 | 说明 |
|------|------|------|
| 无需 API Key | ✅ | 不调用任何外部服务 |
| 生成模拟事件 | ✅ | 基于帧数生成合理数量的事件 |
| 多种事件类型 | ✅ | action_peak/emotion_change/scene_transition/subject_entry/subject_exit |
| 随机但合理 | ✅ | 置信度、高光分数在合理范围内 |
| 时间顺序 | ✅ | 事件按时间排序 |

### DashScopeVLSemanticProvider 功能完成度

| 功能 | 状态 | 说明 |
|------|------|------|
| OpenAI 兼容端点 | ✅ | 通过 OpenAI SDK 调用百炼 |
| 批量处理 | ✅ | 每次发送 2-4 张图（可配置） |
| JSON 输出 | ✅ | 要求结构化输出 |
| Pydantic 校验 | ✅ | 解析后自动验证 |
| Base64 图像编码 | ✅ | 自动编码本地图像 |
| 超时控制 | ✅ | 可配置超时时间 |
| 重试机制 | ✅ | tenacity 自动重试（指数退避） |
| 磁盘缓存 | ✅ | diskcache 避免重复调用 |
| 详细日志 | ✅ | 记录每次 API 调用 |

### API 调用流程

```
1. 输入检查
   ├─> 帧列表为空？返回 []
   └─> 帧列表非空，继续

2. 分批处理
   ├─> 按 batch_size 分组（默认 3 张/批）
   └─> 每批独立处理

3. 缓存检查
   ├─> 生成缓存键（意图 + 帧时间戳）
   ├─> 缓存命中？返回缓存结果
   └─> 缓存未命中，调用 API

4. 构建请求
   ├─> System Prompt（任务描述 + JSON Schema）
   ├─> User Prompt（意图 + 帧信息）
   └─> 图像（Base64 编码）

5. API 调用
   ├─> response_format: json_object
   ├─> temperature: 0.1（低温度，提高稳定性）
   └─> max_tokens: 2000

6. 解析响应
   ├─> JSON 解析
   ├─> Pydantic 验证
   └─> 转换为 VideoEvent 对象

7. 保存缓存
   └─> 过期时间 3600s（1小时）

8. 返回结果
   └─> 所有批次的事件合并
```

### System Prompt 设计

```
你是一个专业的视频分析AI，负责从视频关键帧中检测事件。

任务：
1. 分析每张关键帧的内容
2. 识别帧序列中的重要事件
3. 评估置信度和高光价值
4. 提供拍摄建议

返回 JSON：
{
  "events": [
    {
      "start_ms": 整数,
      "end_ms": 整数,
      "event_type": 字符串,
      "description": 字符串,
      "confidence": 0-1,
      "highlight_score": 0-1,
      "key_subjects": 字符串数组,
      "camera_suggestion": 字符串
    }
  ]
}
```

### User Prompt 结构

```
用户意图：跟拍骑马的人，记录动作高潮

分析以下关键帧序列：

帧 1: 时间=0ms, 变化分数=1.000
[图像1 Base64]

帧 2: 时间=1500ms, 变化分数=0.623
[图像2 Base64]

帧 3: 时间=3000ms, 变化分数=0.412
[图像3 Base64]

请分析以上帧序列，检测重要事件，返回JSON格式结果。
```

### 验收标准检查

- [x] MockSemanticProvider 可在无 API Key 时运行
- [x] Mock 返回结构化事件
- [x] DashScopeVLSemanticProvider 使用 OpenAI SDK
- [x] 批量发送 2-4 张关键帧
- [x] 要求 JSON 输出（response_format）
- [x] Pydantic 自动校验
- [x] 超时控制（可配置）
- [x] 重试机制（tenacity）
- [x] 磁盘缓存（diskcache）
- [x] 完整的单元测试

### 使用示例

```python
from app.semantic import MockSemanticProvider, DashScopeVLSemanticProvider
from app.core.schemas import FramePacket, SelectedFrame
from app.core.settings import settings

# 创建测试帧
frames = []
for i in range(3):
    frame = FramePacket(
        source_id="demo",
        frame_index=i * 15,
        timestamp_ms=i * 1500,
        image_path=f"data/keyframes/frame_{i:04d}.jpg",
        width=1920,
        height=1080,
    )
    selected = SelectedFrame(
        frame=frame,
        change_score=0.8,
        novelty_score=0.7,
        selection_reason=["high_change"],
    )
    frames.append(selected)

# Mock 模式（无需 API Key）
async def test_mock():
    provider = MockSemanticProvider()
    events = await provider.analyze(
        frames=frames,
        user_intent="跟拍骑马的人，记录动作高潮"
    )
    for event in events:
        print(f"{event.event_type}: {event.description} "
              f"({event.start_ms}-{event.end_ms}ms, "
              f"score={event.highlight_score:.2f})")

# 真实 API 模式
async def test_real():
    if settings.is_mock_mode:
        print("需要设置 DASHSCOPE_API_KEY")
        return
    
    provider = DashScopeVLSemanticProvider()
    events = await provider.analyze(
        frames=frames,
        user_intent="跟拍骑马的人，记录动作高潮"
    )
    print(f"检测到 {len(events)} 个事件")
    for event in events:
        print(f"- {event.event_type}: {event.description}")

# 运行
import asyncio
asyncio.run(test_mock())
# asyncio.run(test_real())  # 需要 API Key
```

### 预期输出（Mock 模式）

```
action_peak: 检测到动作高潮：快速移动、跳跃或冲刺 (0-1500ms, score=0.78)
emotion_change: 检测到情绪变化：从专注到兴奋 (1500-3000ms, score=0.65)
```

### 预期输出（真实 API）

```
检测到 2 个事件
- action_peak: 骑手加速冲刺，马匹奔跑姿态明显
- subject_entry: 第二位骑手从左侧进入画面
```

### 成本估算

| 配置 | 每分钟视频 | 关键帧数 | 批次数 | 估算成本 |
|------|-----------|----------|--------|---------|
| 2fps + STC(80%) | 120 → 24 | 24 | 8 | ¥0.08-0.16 |
| 1fps + STC(85%) | 60 → 9 | 9 | 3 | ¥0.03-0.06 |
| 无 STC, 2fps | 120 | 120 | 40 | ¥0.40-0.80 |

**结论**: STC 压缩可节省 75-85% 的 API 成本。

### 下一步：Task 5 导演状态机

现在可以实现：
1. `app/director/state_machine.py` - DirectorStateMachine
2. 状态：IDLE → SEARCH → TRACK → RECORD → HIGHLIGHT → RECOVER
3. 根据 VideoEvent 生成 CameraAction
4. 纯函数式状态机，可测试
5. Mock 设备适配器记录命令

## 测试验证

```bash
# 安装新增依赖
pip install openai tenacity diskcache

# 单元测试
pytest tests/test_semantic.py -v

# 快速验证 Mock 模式
python -c "
import asyncio
from app.semantic import MockSemanticProvider
from app.core.schemas import FramePacket, SelectedFrame

async def test():
    provider = MockSemanticProvider()
    
    frames = []
    for i in range(5):
        frame = FramePacket(
            source_id='test',
            frame_index=i,
            timestamp_ms=i * 1000,
            width=1920,
            height=1080
        )
        selected = SelectedFrame(
            frame=frame,
            change_score=0.8,
            novelty_score=0.7,
            selection_reason=['test']
        )
        frames.append(selected)
    
    events = await provider.analyze(frames, '跟拍骑马')
    print(f'✓ Mock provider generated {len(events)} events')
    for event in events:
        print(f'  - {event.event_type}: {event.description[:40]}...')

asyncio.run(test())
"
```

### 预期输出

```
✓ Mock provider generated 2 events
  - action_peak: 检测到动作高潮：快速移动、跳跃或冲刺...
  - scene_transition: 场景切换：从室内到户外...
```

## 时间消耗

- 设计接口: 5 分钟
- Mock 实现: 10 分钟
- DashScope 实现: 25 分钟
- 单元测试: 10 分钟
- 文档: 5 分钟
- **总计: 约 55 分钟**

比预估的 30 分钟多，但实现了完整的重试、缓存和错误处理。

## 技术亮点

1. **OpenAI 兼容**: 使用标准 SDK，易于切换其他模型
2. **智能缓存**: 基于意图和帧时间戳的缓存键
3. **优雅重试**: tenacity 自动处理网络故障
4. **结构化输出**: JSON Schema 确保格式一致
5. **成本控制**: 批量处理和缓存显著降低成本
6. **可测试性**: Mock 模式完整覆盖流程

## 技术债务

- [ ] 未实现多模型对比（GPT-4V/Gemini）
- [ ] 未实现流式输出（SSE）
- [ ] 未实现并行批次处理
- [ ] 缓存过期策略可优化
- [ ] 图像压缩优化（减少传输量）
