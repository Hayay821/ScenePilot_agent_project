"""
语义理解模块测试
"""

import pytest
from app.semantic import MockSemanticProvider, DashScopeVLSemanticProvider
from app.core.schemas import FramePacket, SelectedFrame


class TestMockSemanticProvider:
    """测试 Mock 语义 Provider"""

    @pytest.mark.asyncio
    async def test_mock_provider_init(self):
        """测试初始化"""
        provider = MockSemanticProvider()
        info = provider.get_model_info()
        assert info["provider"] == "mock"
        assert info["cost_per_request"] == 0.0

    @pytest.mark.asyncio
    async def test_mock_provider_returns_events(self):
        """测试返回模拟事件"""
        provider = MockSemanticProvider()

        # 创建测试帧
        frames = []
        for i in range(10):
            frame = FramePacket(
                source_id="test",
                frame_index=i * 15,
                timestamp_ms=i * 500,
                width=1920,
                height=1080,
            )
            selected = SelectedFrame(
                frame=frame,
                change_score=0.8,
                novelty_score=0.7,
                selection_reason=["test"],
            )
            frames.append(selected)

        # 分析
        events = await provider.analyze(
            frames=frames,
            user_intent="跟拍骑马的人",
        )

        assert len(events) > 0
        assert all(hasattr(e, "event_type") for e in events)
        assert all(hasattr(e, "confidence") for e in events)
        assert all(0 <= e.confidence <= 1 for e in events)

    @pytest.mark.asyncio
    async def test_mock_provider_empty_frames(self):
        """测试空帧列表"""
        provider = MockSemanticProvider()
        events = await provider.analyze(
            frames=[],
            user_intent="测试",
        )
        assert events == []

    @pytest.mark.asyncio
    async def test_mock_events_time_ordering(self):
        """测试事件时间顺序"""
        provider = MockSemanticProvider()

        frames = []
        for i in range(5):
            frame = FramePacket(
                source_id="test",
                frame_index=i,
                timestamp_ms=i * 1000,
                width=1920,
                height=1080,
            )
            selected = SelectedFrame(
                frame=frame,
                change_score=0.8,
                novelty_score=0.7,
                selection_reason=["test"],
            )
            frames.append(selected)

        events = await provider.analyze(frames, "测试")

        # 验证事件按时间排序
        for i in range(len(events) - 1):
            assert events[i].start_ms <= events[i + 1].start_ms


class TestDashScopeVLSemanticProvider:
    """测试百炼视觉 Provider"""

    def test_dashscope_provider_init(self):
        """测试初始化（不调用API）"""
        provider = DashScopeVLSemanticProvider(
            api_key="test_key",
            enable_cache=False,
        )
        info = provider.get_model_info()
        assert info["provider"] == "dashscope"
        assert info["cache_enabled"] is False

    def test_dashscope_cache_key_generation(self):
        """测试缓存键生成"""
        provider = DashScopeVLSemanticProvider(
            api_key="test_key",
            enable_cache=False,
        )

        frames = []
        for i in range(3):
            frame = FramePacket(
                source_id="test",
                frame_index=i,
                timestamp_ms=i * 1000,
                width=1920,
                height=1080,
            )
            selected = SelectedFrame(
                frame=frame,
                change_score=0.8,
                novelty_score=0.7,
                selection_reason=["test"],
            )
            frames.append(selected)

        key1 = provider._make_cache_key(frames, "意图1")
        key2 = provider._make_cache_key(frames, "意图2")
        key3 = provider._make_cache_key(frames[:2], "意图1")

        # 不同意图应该生成不同键
        assert key1 != key2
        # 不同帧应该生成不同键
        assert key1 != key3

    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_dashscope_real_api_call(self):
        """集成测试：真实 API 调用（需要 API Key）"""
        # 这个测试需要真实的 API Key 和图像
        # 跳过自动测试，仅在有 API Key 时手动运行
        pytest.skip("Requires real API key and images")


# 辅助函数测试
class TestSemanticHelpers:
    """测试辅助函数"""

    def test_encode_image(self):
        """测试图像编码"""
        provider = DashScopeVLSemanticProvider(
            api_key="test_key",
            enable_cache=False,
        )

        # 测试不存在的文件
        result = provider._encode_image("nonexistent.jpg")
        assert result is None

    def test_parse_events(self):
        """测试事件解析"""
        provider = DashScopeVLSemanticProvider(
            api_key="test_key",
            enable_cache=False,
        )

        # 创建测试帧
        frames = []
        for i in range(2):
            frame = FramePacket(
                source_id="test",
                frame_index=i,
                timestamp_ms=i * 1000,
                width=1920,
                height=1080,
            )
            selected = SelectedFrame(
                frame=frame,
                change_score=0.8,
                novelty_score=0.7,
                selection_reason=["test"],
            )
            frames.append(selected)

        # 模拟 API 响应
        mock_result = {
            "events": [
                {
                    "start_ms": 0,
                    "end_ms": 1000,
                    "event_type": "action_peak",
                    "description": "测试事件",
                    "confidence": 0.9,
                    "highlight_score": 0.8,
                    "key_subjects": ["subject_1"],
                    "camera_suggestion": "track",
                }
            ]
        }

        events = provider._parse_events(mock_result, frames)
        assert len(events) == 1
        assert events[0].event_type == "action_peak"
        assert events[0].confidence == 0.9
