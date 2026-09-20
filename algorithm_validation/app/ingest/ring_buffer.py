"""
环形缓冲区实现
用于保存最近 N 秒的视频帧，支持事件发生时回溯
"""

from collections import deque
from typing import Optional
from loguru import logger

from app.core.schemas import FramePacket
from app.core.settings import settings


class RingBuffer:
    """
    环形缓冲区
    维护固定时长的帧历史，用于事件发生时回溯 pre-roll
    """

    def __init__(self, duration_sec: Optional[int] = None):
        """
        Args:
            duration_sec: 缓冲区时长（秒），None 使用配置默认值
        """
        self.duration_sec = duration_sec or settings.ring_buffer_duration_sec
        self.duration_ms = self.duration_sec * 1000
        self.buffer: deque[FramePacket] = deque()
        self._total_added = 0
        self._total_dropped = 0

        logger.info(f"RingBuffer initialized: {self.duration_sec}s capacity")

    def add(self, frame: FramePacket):
        """
        添加新帧到缓冲区
        自动清理超过时间窗口的旧帧
        """
        self.buffer.append(frame)
        self._total_added += 1

        # 清理过期帧
        self._cleanup(frame.timestamp_ms)

    def _cleanup(self, current_timestamp_ms: int):
        """清理超出时间窗口的旧帧"""
        cutoff_timestamp = current_timestamp_ms - self.duration_ms

        while self.buffer and self.buffer[0].timestamp_ms < cutoff_timestamp:
            self.buffer.popleft()
            self._total_dropped += 1

    def get_recent(self, duration_ms: Optional[int] = None) -> list[FramePacket]:
        """
        获取最近指定时长的帧

        Args:
            duration_ms: 时长（毫秒），None 返回所有缓冲帧

        Returns:
            按时间顺序排列的帧列表
        """
        if not self.buffer:
            return []

        if duration_ms is None:
            return list(self.buffer)

        current_timestamp = self.buffer[-1].timestamp_ms
        cutoff_timestamp = current_timestamp - duration_ms

        result = []
        for frame in self.buffer:
            if frame.timestamp_ms >= cutoff_timestamp:
                result.append(frame)

        return result

    def get_range(self, start_ms: int, end_ms: int) -> list[FramePacket]:
        """
        获取指定时间范围的帧

        Args:
            start_ms: 开始时间戳（毫秒）
            end_ms: 结束时间戳（毫秒）

        Returns:
            时间范围内的帧列表
        """
        result = []
        for frame in self.buffer:
            if start_ms <= frame.timestamp_ms <= end_ms:
                result.append(frame)

        return result

    def get_before(self, timestamp_ms: int, duration_ms: int) -> list[FramePacket]:
        """
        获取指定时间戳之前的帧（用于 pre-roll）

        Args:
            timestamp_ms: 参考时间戳
            duration_ms: 向前回溯的时长

        Returns:
            Pre-roll 帧列表
        """
        start_ms = max(0, timestamp_ms - duration_ms)
        return self.get_range(start_ms, timestamp_ms)

    def get_after(self, timestamp_ms: int, duration_ms: int) -> list[FramePacket]:
        """
        获取指定时间戳之后的帧（用于 post-roll）

        Args:
            timestamp_ms: 参考时间戳
            duration_ms: 向后延伸的时长

        Returns:
            Post-roll 帧列表
        """
        end_ms = timestamp_ms + duration_ms
        return self.get_range(timestamp_ms, end_ms)

    def get_around(
        self, timestamp_ms: int, before_ms: int, after_ms: int
    ) -> list[FramePacket]:
        """
        获取指定时间戳前后的帧

        Args:
            timestamp_ms: 中心时间戳
            before_ms: 向前回溯时长
            after_ms: 向后延伸时长

        Returns:
            前后帧列表
        """
        start_ms = max(0, timestamp_ms - before_ms)
        end_ms = timestamp_ms + after_ms
        return self.get_range(start_ms, end_ms)

    def clear(self):
        """清空缓冲区"""
        dropped = len(self.buffer)
        self.buffer.clear()
        self._total_dropped += dropped
        logger.debug(f"RingBuffer cleared: {dropped} frames dropped")

    def __len__(self) -> int:
        """返回当前缓冲区帧数"""
        return len(self.buffer)

    @property
    def is_empty(self) -> bool:
        """缓冲区是否为空"""
        return len(self.buffer) == 0

    @property
    def current_duration_ms(self) -> int:
        """当前缓冲区的实际时长（毫秒）"""
        if len(self.buffer) < 2:
            return 0
        return self.buffer[-1].timestamp_ms - self.buffer[0].timestamp_ms

    @property
    def stats(self) -> dict:
        """获取缓冲区统计信息"""
        return {
            "capacity_sec": self.duration_sec,
            "current_frames": len(self.buffer),
            "current_duration_ms": self.current_duration_ms,
            "total_added": self._total_added,
            "total_dropped": self._total_dropped,
            "oldest_timestamp_ms": self.buffer[0].timestamp_ms if self.buffer else None,
            "newest_timestamp_ms": self.buffer[-1].timestamp_ms if self.buffer else None,
        }
