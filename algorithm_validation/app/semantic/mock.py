"""
Mock 语义 Provider
用于无 API Key 时的测试和演示
"""

import random
from typing import List, Optional
from loguru import logger

from app.core.schemas import SelectedFrame, VideoEvent
from .base import SemanticProvider


class MockSemanticProvider(SemanticProvider):
    """
    Mock 语义 Provider
    返回模拟事件，不调用真实 API
    """

    def __init__(self):
        logger.info("MockSemanticProvider initialized (no API calls)")

    async def analyze(
        self,
        frames: List[SelectedFrame],
        user_intent: str,
        context: Optional[dict] = None,
    ) -> List[VideoEvent]:
        """生成模拟事件"""
        if not frames:
            return []

        logger.info(
            f"MockSemanticProvider analyzing {len(frames)} frames "
            f"with intent: '{user_intent}'"
        )

        events = []

        # 根据帧数生成不同数量的事件
        num_events = min(len(frames) // 2, 5)  # 最多 5 个事件

        for i in range(num_events):
            # 随机选择事件类型
            event_types = [
                "action_peak",
                "emotion_change",
                "scene_transition",
                "subject_entry",
                "subject_exit",
            ]
            event_type = random.choice(event_types)

            # 随机选择时间段
            start_idx = random.randint(0, max(0, len(frames) - 2))
            end_idx = random.randint(start_idx, len(frames) - 1)

            start_ms = frames[start_idx].frame.timestamp_ms
            end_ms = frames[end_idx].frame.timestamp_ms

            # 生成描述
            descriptions = {
                "action_peak": "检测到动作高潮：快速移动、跳跃或冲刺",
                "emotion_change": "检测到情绪变化：从专注到兴奋",
                "scene_transition": "场景切换：从室内到户外",
                "subject_entry": "主体进入画面：人物从左侧进入",
                "subject_exit": "主体离开画面：人物向右侧移动出画面",
            }

            event = VideoEvent(
                event_id=f"mock_event_{i:03d}",
                start_ms=start_ms,
                end_ms=end_ms,
                event_type=event_type,
                description=descriptions.get(
                    event_type, "模拟事件"
                ),
                confidence=random.uniform(0.7, 0.95),
                highlight_score=random.uniform(0.5, 0.9),
                key_subjects=["subject_1"] if random.random() > 0.3 else [],
                camera_suggestion="track" if event_type == "action_peak" else "observe",
            )

            events.append(event)

        # 按时间排序
        events.sort(key=lambda e: e.start_ms)

        logger.info(f"MockSemanticProvider generated {len(events)} events")
        return events

    def get_model_info(self) -> dict:
        """获取模型信息"""
        return {
            "provider": "mock",
            "model": "mock-semantic-v1",
            "capabilities": ["vision", "event_detection"],
            "cost_per_request": 0.0,
        }
