"""
语义理解 Provider 抽象接口
用于将关键帧序列转换为结构化事件
"""

from abc import ABC, abstractmethod
from typing import List, Optional

from app.core.schemas import SelectedFrame, VideoEvent


class SemanticProvider(ABC):
    """
    语义理解 Provider 抽象基类
    不同的实现可以使用不同的模型（百炼、GPT-4V、Gemini等）
    """

    @abstractmethod
    async def analyze(
        self,
        frames: List[SelectedFrame],
        user_intent: str,
        context: Optional[dict] = None,
    ) -> List[VideoEvent]:
        """
        分析关键帧序列，返回结构化事件

        Args:
            frames: 关键帧列表（带图像路径）
            user_intent: 用户意图描述（如"跟拍骑马的人，记录动作高潮"）
            context: 上下文信息（如历史事件、场景类型等）

        Returns:
            检测到的事件列表
        """
        pass

    @abstractmethod
    def get_model_info(self) -> dict:
        """获取模型信息"""
        pass
