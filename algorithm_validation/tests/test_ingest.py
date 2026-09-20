"""
视频输入模块测试
"""

import pytest
from pathlib import Path
from app.ingest import FileVideoSource, RingBuffer
from app.core.schemas import FramePacket


class TestRingBuffer:
    """测试环形缓冲区"""

    def test_ring_buffer_init(self):
        """测试初始化"""
        buffer = RingBuffer(duration_sec=10)
        assert buffer.duration_sec == 10
        assert buffer.duration_ms == 10000
        assert len(buffer) == 0
        assert buffer.is_empty

    def test_add_and_get_recent(self):
        """测试添加帧和获取最近帧"""
        buffer = RingBuffer(duration_sec=5)

        # 添加帧
        for i in range(10):
            frame = FramePacket(
                source_id="test",
                frame_index=i,
                timestamp_ms=i * 1000,
                width=1920,
                height=1080,
            )
            buffer.add(frame)

        assert len(buffer) == 10

        # 获取最近 3 秒的帧
        recent = buffer.get_recent(duration_ms=3000)
        assert len(recent) >= 3  # 至少 3 帧

    def test_automatic_cleanup(self):
        """测试自动清理过期帧"""
        buffer = RingBuffer(duration_sec=5)

        # 添加 20 帧，跨度 20 秒
        for i in range(20):
            frame = FramePacket(
                source_id="test",
                frame_index=i,
                timestamp_ms=i * 1000,
                width=1920,
                height=1080,
            )
            buffer.add(frame)

        # 缓冲区只保留最近 5 秒（5-6 帧）
        assert len(buffer) <= 6
        assert buffer.current_duration_ms <= 5000

    def test_get_range(self):
        """测试获取时间范围内的帧"""
        buffer = RingBuffer(duration_sec=10)

        for i in range(10):
            frame = FramePacket(
                source_id="test",
                frame_index=i,
                timestamp_ms=i * 1000,
                width=1920,
                height=1080,
            )
            buffer.add(frame)

        # 获取 2000-5000ms 的帧
        range_frames = buffer.get_range(2000, 5000)
        assert len(range_frames) == 4  # 2, 3, 4, 5
        assert range_frames[0].timestamp_ms == 2000
        assert range_frames[-1].timestamp_ms == 5000

    def test_get_before_and_after(self):
        """测试 pre-roll 和 post-roll"""
        buffer = RingBuffer(duration_sec=10)

        for i in range(10):
            frame = FramePacket(
                source_id="test",
                frame_index=i,
                timestamp_ms=i * 1000,
                width=1920,
                height=1080,
            )
            buffer.add(frame)

        # Pre-roll: 5000ms 之前的 2000ms
        before = buffer.get_before(timestamp_ms=5000, duration_ms=2000)
        assert len(before) == 3  # 3000, 4000, 5000

        # Post-roll: 5000ms 之后的 2000ms
        after = buffer.get_after(timestamp_ms=5000, duration_ms=2000)
        assert len(after) == 3  # 5000, 6000, 7000

    def test_get_around(self):
        """测试获取前后帧"""
        buffer = RingBuffer(duration_sec=10)

        for i in range(10):
            frame = FramePacket(
                source_id="test",
                frame_index=i,
                timestamp_ms=i * 1000,
                width=1920,
                height=1080,
            )
            buffer.add(frame)

        # 5000ms 前后各 2000ms
        around = buffer.get_around(
            timestamp_ms=5000, before_ms=2000, after_ms=2000
        )
        assert len(around) == 5  # 3000, 4000, 5000, 6000, 7000
        assert around[0].timestamp_ms == 3000
        assert around[-1].timestamp_ms == 7000

    def test_stats(self):
        """测试统计信息"""
        buffer = RingBuffer(duration_sec=5)

        for i in range(5):
            frame = FramePacket(
                source_id="test",
                frame_index=i,
                timestamp_ms=i * 1000,
                width=1920,
                height=1080,
            )
            buffer.add(frame)

        stats = buffer.stats
        assert stats["current_frames"] == 5
        assert stats["total_added"] == 5
        assert stats["oldest_timestamp_ms"] == 0
        assert stats["newest_timestamp_ms"] == 4000


class TestFileVideoSource:
    """测试文件视频源"""

    def test_video_source_requires_file(self):
        """测试视频源需要文件存在"""
        with pytest.raises(FileNotFoundError):
            FileVideoSource("nonexistent.mp4")

    def test_video_source_info_structure(self):
        """测试视频信息结构（需要真实视频文件）"""
        # 这个测试需要真实视频文件，暂时跳过
        # 实际测试时需要提供测试视频
        pass

    def test_frame_packet_monotonic_timestamps(self):
        """测试时间戳单调递增（需要真实视频）"""
        # 需要真实视频文件来测试
        pass


# 集成测试标记
@pytest.mark.integration
class TestVideoSourceIntegration:
    """
    集成测试 - 需要真实视频文件
    运行: pytest -m integration
    """

    def test_video_source_with_real_file(self, tmp_path):
        """使用真实视频文件测试完整流程"""
        # 此测试需要准备测试视频文件
        # video_path = "path/to/test/video.mp4"
        # source = FileVideoSource(video_path, realtime=False)
        # ...
        pass
