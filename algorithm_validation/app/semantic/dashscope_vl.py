"""
百炼视觉模型 Provider
通过 OpenAI 兼容端点调用 Qwen-VL
"""

import base64
import json
from pathlib import Path
from typing import List, Optional
import asyncio

from openai import AsyncOpenAI
from tenacity import (
    retry,
    stop_after_attempt,
    wait_exponential,
    retry_if_exception_type,
)
from diskcache import Cache
from loguru import logger

from app.core.schemas import SelectedFrame, VideoEvent
from app.core.settings import settings
from .base import SemanticProvider


class DashScopeVLSemanticProvider(SemanticProvider):
    """
    百炼视觉模型 Provider
    使用 Qwen-VL 进行视觉理解和事件检测
    """

    def __init__(
        self,
        api_key: Optional[str] = None,
        base_url: Optional[str] = None,
        model: Optional[str] = None,
        batch_size: Optional[int] = None,
        timeout: Optional[int] = None,
        max_retries: Optional[int] = None,
        enable_cache: bool = True,
    ):
        """
        Args:
            api_key: DashScope API Key
            base_url: API 端点 URL
            model: 模型名称
            batch_size: 批处理大小（每次最多几张图）
            timeout: 超时时间（秒）
            max_retries: 最大重试次数
            enable_cache: 是否启用缓存
        """
        self.api_key = api_key or settings.dashscope_api_key
        self.base_url = base_url or settings.dashscope_base_url
        self.model = model or settings.qwen_vl_model
        self.batch_size = batch_size or settings.semantic_batch_size
        self.timeout = timeout or settings.semantic_timeout_sec
        self.max_retries = max_retries or settings.semantic_max_retries

        # 初始化 OpenAI 客户端（兼容模式）
        self.client = AsyncOpenAI(
            api_key=self.api_key,
            base_url=self.base_url,
            timeout=self.timeout,
        )

        # 初始化缓存
        self.enable_cache = enable_cache
        if enable_cache:
            cache_dir = settings.cache_dir / "semantic"
            cache_dir.mkdir(parents=True, exist_ok=True)
            self.cache = Cache(str(cache_dir))
            logger.info(f"Semantic cache enabled: {cache_dir}")
        else:
            self.cache = None

        logger.info(
            f"DashScopeVLSemanticProvider initialized: "
            f"model={self.model}, batch_size={self.batch_size}, "
            f"timeout={self.timeout}s, retries={self.max_retries}"
        )

    async def analyze(
        self,
        frames: List[SelectedFrame],
        user_intent: str,
        context: Optional[dict] = None,
    ) -> List[VideoEvent]:
        """分析关键帧序列"""
        if not frames:
            return []

        logger.info(
            f"Analyzing {len(frames)} frames with intent: '{user_intent}'"
        )

        # 分批处理
        all_events = []
        for i in range(0, len(frames), self.batch_size):
            batch = frames[i : i + self.batch_size]

            # 检查缓存
            cache_key = self._make_cache_key(batch, user_intent)
            if self.cache and cache_key in self.cache:
                logger.info(f"Cache hit for batch {i//self.batch_size + 1}")
                events = self.cache[cache_key]
            else:
                # 调用 API
                events = await self._analyze_batch(batch, user_intent, context)

                # 保存到缓存
                if self.cache and events:
                    self.cache.set(cache_key, events, expire=settings.semantic_cache_ttl)

            all_events.extend(events)

        logger.info(f"Total events detected: {len(all_events)}")
        return all_events

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        retry=retry_if_exception_type((TimeoutError, ConnectionError)),
    )
    async def _analyze_batch(
        self,
        frames: List[SelectedFrame],
        user_intent: str,
        context: Optional[dict] = None,
    ) -> List[VideoEvent]:
        """分析一批关键帧"""
        # 构建消息
        messages = [
            {
                "role": "system",
                "content": self._build_system_prompt(),
            },
            {
                "role": "user",
                "content": self._build_user_prompt(frames, user_intent, context),
            },
        ]

        try:
            # 调用 API
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                response_format={"type": "json_object"},
                temperature=0.1,  # 低温度，提高确定性
                max_tokens=2000,
            )

            # 解析响应
            content = response.choices[0].message.content
            result = json.loads(content)

            # 转换为 VideoEvent
            events = self._parse_events(result, frames)
            logger.info(f"Batch analysis complete: {len(events)} events")
            return events

        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse JSON response: {e}")
            return []
        except Exception as e:
            logger.error(f"API call failed: {e}")
            raise

    def _build_system_prompt(self) -> str:
        """构建系统提示词"""
        return """你是一个专业的视频分析AI，负责从视频关键帧中检测事件。

你的任务是：
1. 分析每张关键帧的内容
2. 识别帧序列中的重要事件（动作高潮、情绪变化、场景切换等）
3. 评估每个事件的置信度和高光价值
4. 提供拍摄建议（track/observe/zoom等）

返回JSON格式：
{
  "events": [
    {
      "start_ms": 整数，事件开始时间（毫秒）,
      "end_ms": 整数，事件结束时间（毫秒）,
      "event_type": 字符串，事件类型（action_peak/emotion_change/scene_transition/subject_entry/subject_exit等）,
      "description": 字符串，事件描述,
      "confidence": 浮点数（0-1），检测置信度,
      "highlight_score": 浮点数（0-1），高光价值评分,
      "key_subjects": 字符串数组，关键主体ID,
      "camera_suggestion": 字符串，拍摄建议（track/observe/zoom/wide等）
    }
  ]
}

注意：
- 只返回高置信度的重要事件
- 事件时间必须在提供的帧时间范围内
- highlight_score 基于动作强度、情感价值、视觉吸引力综合评估
"""

    def _build_user_prompt(
        self,
        frames: List[SelectedFrame],
        user_intent: str,
        context: Optional[dict] = None,
    ) -> list:
        """构建用户提示词（包含图像）"""
        content = []

        # 添加意图描述
        content.append({
            "type": "text",
            "text": f"用户意图：{user_intent}\n\n分析以下关键帧序列：\n"
        })

        # 添加每帧信息和图像
        for i, selected in enumerate(frames):
            frame = selected.frame

            # 帧信息
            content.append({
                "type": "text",
                "text": f"帧 {i+1}: 时间={frame.timestamp_ms}ms, 变化分数={selected.change_score:.3f}\n"
            })

            # 图像（Base64编码）
            if frame.image_path:
                image_data = self._encode_image(frame.image_path)
                if image_data:
                    content.append({
                        "type": "image_url",
                        "image_url": {
                            "url": f"data:image/jpeg;base64,{image_data}"
                        }
                    })

        # 添加分析要求
        content.append({
            "type": "text",
            "text": "\n请分析以上帧序列，检测重要事件，返回JSON格式结果。"
        })

        return content

    def _encode_image(self, image_path: str) -> Optional[str]:
        """Base64编码图像"""
        try:
            path = Path(image_path)
            if not path.exists():
                logger.warning(f"Image not found: {image_path}")
                return None

            with open(path, "rb") as f:
                return base64.b64encode(f.read()).decode("utf-8")
        except Exception as e:
            logger.error(f"Failed to encode image {image_path}: {e}")
            return None

    def _parse_events(
        self,
        result: dict,
        frames: List[SelectedFrame]
    ) -> List[VideoEvent]:
        """解析API返回的事件"""
        events = []

        if "events" not in result:
            logger.warning("No 'events' field in API response")
            return events

        for i, event_data in enumerate(result["events"]):
            try:
                event = VideoEvent(
                    event_id=f"evt_{len(events):04d}",
                    start_ms=event_data["start_ms"],
                    end_ms=event_data["end_ms"],
                    event_type=event_data["event_type"],
                    description=event_data["description"],
                    confidence=event_data.get("confidence", 0.8),
                    highlight_score=event_data.get("highlight_score", 0.5),
                    key_subjects=event_data.get("key_subjects", []),
                    camera_suggestion=event_data.get("camera_suggestion", "observe"),
                )
                events.append(event)
            except Exception as e:
                logger.error(f"Failed to parse event {i}: {e}")
                continue

        return events

    def _make_cache_key(
        self,
        frames: List[SelectedFrame],
        user_intent: str
    ) -> str:
        """生成缓存键"""
        # 使用帧时间戳和意图生成唯一键
        frame_ids = [f.frame.timestamp_ms for f in frames]
        key = f"{user_intent}:{','.join(map(str, frame_ids))}"
        return key

    def get_model_info(self) -> dict:
        """获取模型信息"""
        return {
            "provider": "dashscope",
            "model": self.model,
            "base_url": self.base_url,
            "batch_size": self.batch_size,
            "timeout": self.timeout,
            "max_retries": self.max_retries,
            "cache_enabled": self.enable_cache,
        }
