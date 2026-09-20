"""
STC (Streaming Token Compression) 抽象接口
用于从连续视频流中选择关键帧，减少语义模型的输入
"""

from abc import ABC, abstractmethod
from typing import Optional

from app.core.schemas import FramePacket, SelectedFrame


class STCAdapter(ABC):
    """
    STC 适配器抽象基类
    不同的实现可以使用不同的压缩策略
    """

    @abstractmethod
    def select(
        self,
        frame: FramePacket,
        frame_data: Optional[any] = None,
        context: Optional[dict] = None
    ) -> Optional[SelectedFrame]:
        """
        判断是否选择当前帧作为关键帧

        Args:
            frame: 当前帧数据包
            frame_data: 帧的像素数据（numpy array）
            context: 上下文信息（如用户意图、历史事件等）

        Returns:
            SelectedFrame 如果选中，None 如果丢弃
        """
        pass

    @abstractmethod
    def reset(self):
        """重置内部状态"""
        pass

    @abstractmethod
    def get_stats(self) -> dict:
        """获取统计信息"""
        pass
