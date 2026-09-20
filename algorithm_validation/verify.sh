#!/bin/bash
# 快速验证脚本

echo "=========================================="
echo "ScenePilot 算法验证 - 快速测试"
echo "=========================================="

# 检查 Python 环境
if ! command -v python &> /dev/null; then
    echo "❌ Python 未找到，请先安装 Python 3.11+"
    exit 1
fi

echo "✓ Python 版本: $(python --version)"

# 检查 FFmpeg
if ! command -v ffmpeg &> /dev/null; then
    echo "⚠️  FFmpeg 未找到，高光剪辑功能将不可用"
    echo "   请安装: https://ffmpeg.org/download.html"
else
    echo "✓ FFmpeg 版本: $(ffmpeg -version | head -n1)"
fi

# 检查依赖
echo ""
echo "检查 Python 依赖..."
python -c "
import sys
missing = []
try:
    import cv2
except ImportError:
    missing.append('opencv-python')
try:
    import pydantic
except ImportError:
    missing.append('pydantic')
try:
    import click
except ImportError:
    missing.append('click')
try:
    import loguru
except ImportError:
    missing.append('loguru')

if missing:
    print(f'❌ 缺少依赖: {', '.join(missing)}')
    print('   请运行: pip install -r requirements.txt')
    sys.exit(1)
else:
    print('✓ 所有依赖已安装')
"

if [ $? -ne 0 ]; then
    exit 1
fi

# 测试 Schema
echo ""
echo "测试核心 Schema..."
python -c "
from app.core.schemas import FramePacket, SelectedFrame, VideoEvent, CameraAction, RunMetrics
print('✓ Schema 导入成功')

# 创建测试实例
fp = FramePacket(source_id='test', frame_index=0, timestamp_ms=0, width=1920, height=1080)
print(f'✓ FramePacket: {fp.frame_index}')

event = VideoEvent(
    event_id='test',
    start_ms=0,
    end_ms=1000,
    event_type='action_peak',
    description='测试',
    confidence=0.9,
    highlight_score=0.8,
)
print(f'✓ VideoEvent: {event.event_type}')

action = CameraAction(
    action_id='test',
    action_type='start_tracking',
    timestamp_ms=0,
    params={},
)
print(f'✓ CameraAction: {action.action_type}')
"

if [ $? -ne 0 ]; then
    echo "❌ Schema 测试失败"
    exit 1
fi

# 测试状态机
echo ""
echo "测试导演状态机..."
python -c "
from app.director import DirectorStateMachine, DirectorState
from app.core.schemas import VideoEvent

sm = DirectorStateMachine()
context = sm.create_initial_context()
print(f'✓ 初始状态: {context.current_state}')

event = VideoEvent(
    event_id='test',
    start_ms=1000,
    end_ms=2000,
    event_type='subject_entry',
    description='主体进入',
    confidence=0.9,
    highlight_score=0.6,
    key_subjects=['test'],
    camera_suggestion='track',
)

actions, new_context = sm.process_events([event], context, 2000)
print(f'✓ 状态转换: {context.current_state} → {new_context.current_state}')
print(f'✓ 生成命令: {len(actions)} 条')
"

if [ $? -ne 0 ]; then
    echo "❌ 状态机测试失败"
    exit 1
fi

# 测试 Mock Provider
echo ""
echo "测试 Mock Provider..."
python -c "
import asyncio
from app.semantic import MockSemanticProvider
from app.core.schemas import FramePacket, SelectedFrame

async def test():
    provider = MockSemanticProvider()

    frame = FramePacket(source_id='test', frame_index=0, timestamp_ms=0, width=1920, height=1080)
    selected = SelectedFrame(frame=frame, change_score=0.5, novelty_score=0.5)

    events = await provider.analyze([selected], 'test intent')
    print(f'✓ Mock Provider 返回 {len(events)} 个事件')

    for event in events:
        print(f'  - {event.event_type}: {event.description[:30]}...')

asyncio.run(test())
"

if [ $? -ne 0 ]; then
    echo "❌ Mock Provider 测试失败"
    exit 1
fi

# 检查输出目录
echo ""
echo "准备输出目录..."
mkdir -p data/input
mkdir -p data/output
echo "✓ 输出目录已创建"

echo ""
echo "=========================================="
echo "✅ 所有测试通过！"
echo "=========================================="
echo ""
echo "接下来："
echo "1. 准备测试视频到 data/input/"
echo "2. 运行分析:"
echo "   python -m app.cli analyze -i data/input/demo.mp4 --intent '跟拍骑马' --mock"
echo ""
echo "查看帮助:"
echo "   python -m app.cli --help"
echo ""
