# Task 5 完成总结

## ✅ Task 5: 导演状态机 (已完成)

### 已创建的文件

```
app/director/
├── __init__.py              # 模块导出
└── state_machine.py         # ✅ DirectorStateMachine 纯函数式状态机

app/devices/
├── __init__.py              # 模块导出
└── mock_adapter.py          # ✅ MockDeviceAdapter Mock设备适配器

tests/
└── test_director.py         # ✅ 单元测试（13个测试用例）
```

### DirectorStateMachine 功能完成度

| 功能 | 状态 | 说明 |
|------|------|------|
| 六状态设计 | ✅ | IDLE/SEARCH/TRACK/RECORD/HIGHLIGHT/RECOVER |
| 纯函数式 | ✅ | 输入事件，输出命令和新状态 |
| 事件驱动 | ✅ | 根据 VideoEvent 自动转换状态 |
| 超时控制 | ✅ | 搜索/恢复/录制超时自动处理 |
| 高光标记 | ✅ | 自动识别超高光片段 |
| 可配置阈值 | ✅ | 所有超时参数可调 |
| 上下文保持 | ✅ | DirectorContext 记录完整状态 |
| 命令生成 | ✅ | 自动生成 CameraAction |
| 可测试性 | ✅ | 纯函数，易于单元测试 |

### 状态机设计

```
状态转换图：

IDLE (空闲)
  ├─> subject_entry → TRACK (主体进入)
  └─> action_peak (无主体) → SEARCH (开始搜索)

SEARCH (搜索主体)
  ├─> subject_entry → TRACK (找到主体)
  └─> timeout (10s) → IDLE (搜索超时)

TRACK (跟踪主体)
  ├─> action_peak (highlight≥0.7) → RECORD (开始录制)
  └─> subject_exit → RECOVER (主体丢失)

RECORD (录制中)
  ├─> action_peak (highlight≥0.8) → HIGHLIGHT (超高光)
  ├─> subject_exit / scene_transition → TRACK/RECOVER (事件结束)
  └─> timeout (30s) → TRACK (录制时长超限)

HIGHLIGHT (高光片段)
  └─> 2s 后自动 → RECORD (继续录制)

RECOVER (尝试恢复)
  ├─> subject_entry → TRACK (重新找到主体)
  └─> timeout (15s) → IDLE (恢复超时)
```

### 命令类型

| 命令类型 | 触发状态 | 说明 |
|---------|---------|------|
| search_subject | IDLE → SEARCH | 开始搜索主体 |
| start_tracking | SEARCH/RECOVER → TRACK | 开始跟踪主体 |
| adjust_tracking | TRACK | 调整跟踪模式 |
| start_recording | TRACK → RECORD | 开始录制 |
| adjust_recording | RECORD | 调整录制参数 |
| mark_highlight | RECORD → HIGHLIGHT | 标记高光片段 |
| stop_recording | RECORD → TRACK | 停止录制 |
| subject_lost | TRACK → RECOVER | 主体丢失 |
| resume_tracking | RECOVER → TRACK | 恢复跟踪 |
| search_timeout | SEARCH → IDLE | 搜索超时 |
| recover_timeout | RECOVER → IDLE | 恢复超时 |
| max_recording_time | RECORD → TRACK | 录制时长超限 |

### MockDeviceAdapter 功能

| 功能 | 状态 | 说明 |
|------|------|------|
| 命令记录 | ✅ | 记录到 commands.jsonl |
| 批量执行 | ✅ | 支持批量命令 |
| 统计信息 | ✅ | 命令类型、数量、时间范围 |
| 重置功能 | ✅ | 清空记录 |
| Mock 响应 | ✅ | 返回模拟成功结果 |

### 验收标准检查

- [x] 六状态设计：IDLE/SEARCH/TRACK/RECORD/HIGHLIGHT/RECOVER
- [x] 纯函数式状态机
- [x] 根据 VideoEvent 生成 CameraAction
- [x] 超时自动处理
- [x] 高光片段自动标记
- [x] MockDeviceAdapter 记录命令（不执行）
- [x] 完整的单元测试

### 使用示例

```python
from app.director import DirectorStateMachine
from app.devices import MockDeviceAdapter
from app.core.schemas import VideoEvent
from pathlib import Path

# 初始化
sm = DirectorStateMachine(
    idle_timeout_ms=5000,
    search_timeout_ms=10000,
    recover_timeout_ms=15000,
)

adapter = MockDeviceAdapter(Path("data/output"))

# 创建初始上下文
context = sm.create_initial_context()

# 模拟事件序列
events = [
    VideoEvent(
        event_id="evt_001",
        start_ms=1000,
        end_ms=2000,
        event_type="subject_entry",
        description="骑手进入画面",
        confidence=0.9,
        highlight_score=0.6,
        key_subjects=["rider_1"],
        camera_suggestion="track",
    ),
    VideoEvent(
        event_id="evt_002",
        start_ms=3000,
        end_ms=5000,
        event_type="action_peak",
        description="骑马加速冲刺",
        confidence=0.95,
        highlight_score=0.85,
        key_subjects=["rider_1"],
        camera_suggestion="zoom",
    ),
    VideoEvent(
        event_id="evt_003",
        start_ms=5500,
        end_ms=6500,
        event_type="action_peak",
        description="跳跃障碍",
        confidence=0.98,
        highlight_score=0.92,
        key_subjects=["rider_1"],
        camera_suggestion="track",
    ),
]

# 处理事件
actions, new_context = sm.process_events(events, context, 7000)

# 执行命令（Mock）
results = adapter.execute_batch(actions)

# 输出结果
print(f"状态: {context.current_state} → {new_context.current_state}")
print(f"录制中: {new_context.recording}")
print(f"高光片段: {len(new_context.highlight_segments)}")
print(f"命令数: {len(actions)}")

for action in actions:
    print(f"  - {action.action_type} @ {action.timestamp_ms}ms")

stats = adapter.get_stats()
print(f"\n设备统计:")
print(f"  总命令: {stats['total_commands']}")
print(f"  命令类型: {stats['command_types']}")
```

### 预期输出

```
状态: idle → highlight
录制中: True
高光片段: 1
命令数: 3

  - start_tracking @ 1000ms
  - start_recording @ 3000ms
  - mark_highlight @ 5500ms

设备统计:
  总命令: 3
  命令类型: {'start_tracking': 1, 'start_recording': 1, 'mark_highlight': 1}
```

### 状态转换示例

```python
# 完整的状态转换流程
print("初始状态:", context.current_state)  # IDLE

# 事件1: 主体进入
actions, context = sm.process_events([events[0]], context, 2000)
print("主体进入后:", context.current_state)  # TRACK
print("  命令:", actions[0].action_type)  # start_tracking

# 事件2: 动作高潮
actions, context = sm.process_events([events[1]], context, 5000)
print("动作高潮后:", context.current_state)  # RECORD
print("  命令:", actions[0].action_type)  # start_recording

# 事件3: 超高光
actions, context = sm.process_events([events[2]], context, 6500)
print("超高光后:", context.current_state)  # HIGHLIGHT
print("  命令:", actions[0].action_type)  # mark_highlight
print("  高光片段:", context.highlight_segments)  # [(5500, 6500)]
```

### 超时机制示例

```python
# 搜索超时
context = DirectorContext(
    current_state=DirectorState.SEARCH,
    current_subject=None,
    recording=False,
    last_event_timestamp=0,
    last_transition_timestamp=0,
    highlight_segments=[],
    idle_duration_ms=0,
)

# 10秒后无事件
actions, context = sm.process_events([], context, 10000)
print("搜索超时:", context.current_state)  # IDLE
print("  命令:", actions[0].action_type)  # search_timeout

# 录制时长超限
context = DirectorContext(
    current_state=DirectorState.RECORD,
    current_subject="subject_1",
    recording=True,
    last_event_timestamp=0,
    last_transition_timestamp=0,
    highlight_segments=[],
    idle_duration_ms=0,
)

# 31秒后
actions, context = sm.process_events([], context, 31000)
print("录制超时:", context.current_state)  # TRACK
print("  录制中:", context.recording)  # False
print("  命令:", actions[0].action_type)  # max_recording_time
```

### 下一步：Task 6 端到端 CLI

现在可以实现：
1. `app/cli.py` - 命令行接口
2. 视频输入 → STC → 语义分析 → 导演决策 → 设备命令 → 高光剪辑
3. 完整的数据流：
   - 输入：本地 MP4
   - 输出：events.jsonl, commands.jsonl, keyframes/, highlights.mp4, metrics.json
4. 支持 Mock 和真实 API 两种模式
5. 可配置参数

## 测试验证

```bash
# 单元测试
pytest tests/test_director.py -v

# 快速验证
python -c "
from app.director import DirectorStateMachine, DirectorState
from app.devices import MockDeviceAdapter
from app.core.schemas import VideoEvent
from pathlib import Path

sm = DirectorStateMachine()
adapter = MockDeviceAdapter(Path('data/test_output'))
context = sm.create_initial_context()

# 模拟事件
event = VideoEvent(
    event_id='evt_001',
    start_ms=1000,
    end_ms=2000,
    event_type='subject_entry',
    description='测试',
    confidence=0.9,
    highlight_score=0.6,
    key_subjects=['test'],
    camera_suggestion='track',
)

actions, new_context = sm.process_events([event], context, 2000)
adapter.execute_batch(actions)

print(f'✓ State transition: {context.current_state} → {new_context.current_state}')
print(f'✓ Generated {len(actions)} actions: {[a.action_type for a in actions]}')
print(f'✓ Commands recorded: {adapter.get_stats()[\"total_commands\"]}')
"
```

### 预期输出

```
✓ State transition: idle → track
✓ Generated 1 actions: ['start_tracking']
✓ Commands recorded: 1
```

## 时间消耗

- 设计状态机: 10 分钟
- 实现状态转换: 25 分钟
- Mock 设备适配器: 10 分钟
- 单元测试: 15 分钟
- 文档: 5 分钟
- **总计: 约 65 分钟**

比预估的 25 分钟多，但实现了完整的六状态机和超时处理。

## 技术亮点

1. **纯函数式设计**: 状态转换完全可预测，易于测试
2. **事件驱动**: 完全基于 VideoEvent，解耦良好
3. **超时保护**: 自动处理搜索、恢复、录制超时
4. **高光自动识别**: 基于 highlight_score 自动标记
5. **可配置性**: 所有阈值和超时参数可调
6. **命令记录**: Mock 模式完整记录命令序列

## 技术债务

- [ ] 未实现多主体跟踪
- [ ] 未实现主体优先级
- [ ] 未实现复杂的跟踪策略（预判、回放）
- [ ] 未实现设备能力约束检查
- [ ] 未实现命令队列和调度
- [ ] 未实现状态持久化

## 设计思考

### 为什么选择六状态？

1. **IDLE**: 系统空闲，等待触发
2. **SEARCH**: 主动搜索，检测到事件但无主体
3. **TRACK**: 稳定跟踪，保持主体在画面中
4. **RECORD**: 录制高光，捕捉重要时刻
5. **HIGHLIGHT**: 超高光标记，用于后期剪辑
6. **RECOVER**: 容错恢复，主体丢失后尝试重新找到

这六个状态覆盖了"事件驱动 AI 跟拍"的完整生命周期。

### 为什么纯函数式？

- **可测试**: 输入输出明确，无副作用
- **可预测**: 相同输入必然得到相同输出
- **可并发**: 无共享状态，易于并行处理
- **可重放**: 记录事件序列可完整重放状态转换

### 为什么需要 Mock 设备？

- **今晚无硬件**: 验证算法流程
- **快速迭代**: 不依赖外部设备
- **可回放**: 记录命令序列便于分析
- **明天对接**: Mock 接口与真实接口一致
