"""
Schema 单元测试
"""

import pytest
from datetime import datetime
from app.core.schemas import (
    FramePacket,
    SelectedFrame,
    VideoEvent,
    CameraAction,
    RunMetrics,
)


class TestFramePacket:
    """测试 FramePacket 数据结构"""

    def test_valid_frame_packet(self):
        frame = FramePacket(
            source_id="test_video",
            frame_index=42,
            timestamp_ms=1400,
            width=1920,
            height=1080,
        )
        assert frame.source_id == "test_video"
        assert frame.frame_index == 42
        assert frame.timestamp_ms == 1400
        assert frame.image_path is None

    def test_frame_packet_with_image_path(self):
        frame = FramePacket(
            source_id="test_video",
            frame_index=42,
            timestamp_ms=1400,
            image_path="keyframes/frame_042.jpg",
            width=1920,
            height=1080,
        )
        assert frame.image_path == "keyframes/frame_042.jpg"

    def test_frame_packet_validation(self):
        """测试验证规则"""
        # 负数帧索引应该失败
        with pytest.raises(ValueError):
            FramePacket(
                source_id="test",
                frame_index=-1,
                timestamp_ms=1000,
                width=1920,
                height=1080,
            )

        # 零宽度应该失败
        with pytest.raises(ValueError):
            FramePacket(
                source_id="test",
                frame_index=0,
                timestamp_ms=1000,
                width=0,
                height=1080,
            )


class TestSelectedFrame:
    """测试 SelectedFrame 数据结构"""

    def test_valid_selected_frame(self):
        frame = FramePacket(
            source_id="test_video",
            frame_index=42,
            timestamp_ms=1400,
            width=1920,
            height=1080,
        )
        selected = SelectedFrame(
            frame=frame,
            change_score=0.75,
            novelty_score=0.82,
            selection_reason=["high_motion", "scene_change"],
        )
        assert selected.change_score == 0.75
        assert selected.novelty_score == 0.82
        assert len(selected.selection_reason) == 2

    def test_score_validation(self):
        """测试分数范围验证"""
        frame = FramePacket(
            source_id="test",
            frame_index=0,
            timestamp_ms=0,
            width=1920,
            height=1080,
        )

        # 分数超过 1.0 应该失败
        with pytest.raises(ValueError):
            SelectedFrame(frame=frame, change_score=1.5, novelty_score=0.5)


class TestVideoEvent:
    """测试 VideoEvent 数据结构"""

    def test_valid_event(self):
        event = VideoEvent(
            event_id="evt_001",
            start_ms=12000,
            end_ms=15000,
            event_type="action_peak",
            subjects=["person_1"],
            description="骑马者完成跳跃动作",
            confidence=0.91,
            highlight_score=0.85,
            evidence_frame_ids=[240, 245, 250],
        )
        assert event.event_type == "action_peak"
        assert len(event.subjects) == 1
        assert len(event.evidence_frame_ids) == 3

    def test_event_type_validation(self):
        """测试事件类型枚举验证"""
        # 无效的事件类型应该失败
        with pytest.raises(ValueError):
            VideoEvent(
                event_id="evt_001",
                start_ms=12000,
                end_ms=15000,
                event_type="invalid_type",
                description="测试",
                confidence=0.9,
                highlight_score=0.8,
            )


class TestCameraAction:
    """测试 CameraAction 数据结构"""

    def test_valid_action(self):
        action = CameraAction(
            device="link2",
            action="track_subject",
            args={"subject_id": "person_1", "composition": "half_body"},
            reason="用户要求跟拍红衣选手",
            confidence=0.91,
            timestamp_ms=12500,
        )
        assert action.device == "link2"
        assert action.action == "track_subject"
        assert "subject_id" in action.args

    def test_action_enum_validation(self):
        """测试动作类型枚举验证"""
        with pytest.raises(ValueError):
            CameraAction(
                device="mock",
                action="invalid_action",
                reason="测试",
                confidence=0.9,
            )


class TestRunMetrics:
    """测试 RunMetrics 数据结构"""

    def test_valid_metrics(self):
        metrics = RunMetrics(
            session_id="session_001",
            video_duration_ms=120000,
            decoded_frames=240,
            selected_frames=52,
            compression_ratio=0.783,
            api_batches=18,
            avg_semantic_latency_ms=1820.5,
            events_detected=7,
            highlights_generated=3,
            total_processing_time_sec=45.2,
        )
        assert metrics.compression_ratio == 0.783
        assert metrics.decoded_frames == 240
        assert isinstance(metrics.created_at, datetime)

    def test_compression_ratio_calculation(self):
        """测试压缩率计算逻辑"""
        metrics = RunMetrics(
            session_id="test",
            video_duration_ms=60000,
            decoded_frames=100,
            selected_frames=25,
            compression_ratio=0.75,
            api_batches=10,
            avg_semantic_latency_ms=1000.0,
            events_detected=5,
            highlights_generated=2,
            total_processing_time_sec=30.0,
        )
        # 压缩率 = 1 - (25 / 100) = 0.75
        expected_ratio = 1 - (metrics.selected_frames / metrics.decoded_frames)
        assert abs(metrics.compression_ratio - expected_ratio) < 0.01


class TestSchemaJsonSerialization:
    """测试 Schema 的 JSON 序列化"""

    def test_frame_packet_json_roundtrip(self):
        frame = FramePacket(
            source_id="test_video",
            frame_index=42,
            timestamp_ms=1400,
            width=1920,
            height=1080,
        )
        json_str = frame.model_dump_json()
        restored = FramePacket.model_validate_json(json_str)
        assert restored.frame_index == frame.frame_index
        assert restored.timestamp_ms == frame.timestamp_ms

    def test_event_json_roundtrip(self):
        event = VideoEvent(
            event_id="evt_001",
            start_ms=12000,
            end_ms=15000,
            event_type="action_peak",
            subjects=["person_1"],
            description="测试事件",
            confidence=0.91,
            highlight_score=0.85,
        )
        json_str = event.model_dump_json()
        restored = VideoEvent.model_validate_json(json_str)
        assert restored.event_id == event.event_id
        assert restored.event_type == event.event_type
