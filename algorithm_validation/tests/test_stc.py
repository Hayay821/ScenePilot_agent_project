"""
STC 模块测试
"""

import pytest
import numpy as np
import cv2
from app.stc import HeuristicSTC
from app.core.schemas import FramePacket


class TestHeuristicSTC:
    """测试启发式 STC"""

    def test_stc_init(self):
        """测试初始化"""
        stc = HeuristicSTC(
            frame_diff_threshold=0.15,
            hist_diff_threshold=0.20,
            max_gap_sec=3,
        )
        assert stc.frame_diff_threshold == 0.15
        assert stc.hist_diff_threshold == 0.20
        assert stc.max_gap_sec == 3

    def test_first_frame_always_selected(self):
        """测试第一帧总是被选中"""
        stc = HeuristicSTC()

        # 创建测试帧
        frame = FramePacket(
            source_id="test",
            frame_index=0,
            timestamp_ms=0,
            width=640,
            height=480,
        )

        # 创建黑色图像
        frame_data = np.zeros((480, 640, 3), dtype=np.uint8)

        # 第一帧应该被选中
        selected = stc.select(frame, frame_data)
        assert selected is not None
        assert "first_frame" in selected.selection_reason

    def test_identical_frames_not_selected(self):
        """测试相同帧不会被连续选中"""
        stc = HeuristicSTC(
            frame_diff_threshold=0.15,
            max_gap_sec=10,  # 增大间隔避免强制选择
        )

        # 第一帧
        frame1 = FramePacket(
            source_id="test", frame_index=0, timestamp_ms=0,
            width=640, height=480
        )
        frame_data1 = np.zeros((480, 640, 3), dtype=np.uint8)
        selected1 = stc.select(frame1, frame_data1)
        assert selected1 is not None

        # 完全相同的第二帧
        frame2 = FramePacket(
            source_id="test", frame_index=1, timestamp_ms=500,
            width=640, height=480
        )
        frame_data2 = np.zeros((480, 640, 3), dtype=np.uint8)
        selected2 = stc.select(frame2, frame_data2)
        assert selected2 is None  # 应该不被选中

    def test_high_change_frame_selected(self):
        """测试高变化帧会被选中"""
        stc = HeuristicSTC(frame_diff_threshold=0.15)

        # 第一帧：黑色
        frame1 = FramePacket(
            source_id="test", frame_index=0, timestamp_ms=0,
            width=640, height=480
        )
        frame_data1 = np.zeros((480, 640, 3), dtype=np.uint8)
        stc.select(frame1, frame_data1)

        # 第二帧：白色（大变化）
        frame2 = FramePacket(
            source_id="test", frame_index=1, timestamp_ms=500,
            width=640, height=480
        )
        frame_data2 = np.ones((480, 640, 3), dtype=np.uint8) * 255
        selected2 = stc.select(frame2, frame_data2)

        assert selected2 is not None
        assert selected2.change_score > 0.5  # 应该有高变化分数

    def test_max_gap_enforcement(self):
        """测试最大间隔强制选择"""
        stc = HeuristicSTC(
            frame_diff_threshold=0.9,  # 设置很高的阈值
            max_gap_sec=1,  # 1 秒最大间隔
        )

        # 第一帧
        frame1 = FramePacket(
            source_id="test", frame_index=0, timestamp_ms=0,
            width=640, height=480
        )
        frame_data1 = np.zeros((480, 640, 3), dtype=np.uint8)
        stc.select(frame1, frame_data1)

        # 第二帧：1.5 秒后，变化很小
        frame2 = FramePacket(
            source_id="test", frame_index=30, timestamp_ms=1500,
            width=640, height=480
        )
        frame_data2 = np.zeros((480, 640, 3), dtype=np.uint8)
        frame_data2[0, 0] = 1  # 微小变化

        selected2 = stc.select(frame2, frame_data2)
        assert selected2 is not None  # 应该因为超过最大间隔而被选中
        assert any("max_gap" in r for r in selected2.selection_reason)

    def test_compression_ratio(self):
        """测试压缩率计算"""
        stc = HeuristicSTC(frame_diff_threshold=0.5)  # 较高阈值

        # 处理 10 帧，大部分相似
        for i in range(10):
            frame = FramePacket(
                source_id="test", frame_index=i, timestamp_ms=i * 500,
                width=640, height=480
            )
            # 生成微小变化的图像
            frame_data = np.ones((480, 640, 3), dtype=np.uint8) * (i % 3)
            stc.select(frame, frame_data)

        stats = stc.get_stats()
        assert stats["total_frames"] == 10
        assert stats["selected_frames"] < 10  # 应该有压缩
        assert 0 <= stats["compression_ratio"] <= 1

    def test_reset(self):
        """测试重置功能"""
        stc = HeuristicSTC()

        # 处理一些帧
        for i in range(5):
            frame = FramePacket(
                source_id="test", frame_index=i, timestamp_ms=i * 500,
                width=640, height=480
            )
            frame_data = np.random.randint(0, 255, (480, 640, 3), dtype=np.uint8)
            stc.select(frame, frame_data)

        stats_before = stc.get_stats()
        assert stats_before["total_frames"] > 0

        # 重置
        stc.reset()
        stats_after = stc.get_stats()
        assert stats_after["total_frames"] == 0
        assert stats_after["selected_frames"] == 0

    def test_selection_reasons(self):
        """测试选择原因记录"""
        stc = HeuristicSTC(frame_diff_threshold=0.1)

        # 第一帧
        frame1 = FramePacket(
            source_id="test", frame_index=0, timestamp_ms=0,
            width=100, height=100
        )
        frame_data1 = np.zeros((100, 100, 3), dtype=np.uint8)
        selected1 = stc.select(frame1, frame_data1)

        assert selected1 is not None
        assert isinstance(selected1.selection_reason, list)
        assert len(selected1.selection_reason) > 0


# 集成测试
@pytest.mark.integration
class TestSTCIntegration:
    """STC 集成测试"""

    def test_stc_with_real_video(self):
        """使用真实视频测试 STC（需要视频文件）"""
        # 需要准备测试视频
        pass

    def test_stc_compression_effectiveness(self):
        """测试 STC 压缩效果"""
        # 生成模拟视频序列，验证压缩率
        pass
