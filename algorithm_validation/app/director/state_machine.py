"""
导演状态机
纯函数式状态机，根据事件生成设备命令
"""

from enum import Enum
from typing import List, Optional, Tuple
from dataclasses import dataclass
from loguru import logger

from app.core.schemas import VideoEvent, CameraAction
from app.core.settings import settings


class DirectorState(str, Enum):
    """导演状态"""
    IDLE = "idle"  # 空闲：等待主体出现
    SEARCH = "search"  # 搜索：寻找主体
    TRACK = "track"  # 跟踪：稳定跟随主体
    RECORD = "record"  # 录制：记录高光时刻
    HIGHLIGHT = "highlight"  # 高光：标记精彩片段
    RECOVER = "recover"  # 恢复：主体丢失，尝试重新找到


@dataclass
class DirectorContext:
    """导演上下文"""
    current_state: DirectorState
    current_subject: Optional[str]  # 当前跟踪的主体 ID
    recording: bool  # 是否正在录制
    last_event_timestamp: int  # 上一个事件的时间戳
    last_transition_timestamp: int  # 上一次状态转换的时间戳
    highlight_segments: List[Tuple[int, int]]  # 高光片段 (start_ms, end_ms)
    idle_duration_ms: int  # 空闲时长（毫秒）


class DirectorStateMachine:
    """
    导演状态机
    纯函数式设计，输入事件，输出命令和新状态
    """

    def __init__(
        self,
        idle_timeout_ms: Optional[int] = None,
        search_timeout_ms: Optional[int] = None,
        recover_timeout_ms: Optional[int] = None,
    ):
        """
        Args:
            idle_timeout_ms: 空闲超时（毫秒）
            search_timeout_ms: 搜索超时（毫秒）
            recover_timeout_ms: 恢复超时（毫秒）
        """
        self.idle_timeout_ms = idle_timeout_ms or settings.director_idle_timeout_ms
        self.search_timeout_ms = search_timeout_ms or settings.director_search_timeout_ms
        self.recover_timeout_ms = recover_timeout_ms or settings.director_recover_timeout_ms

        logger.info(
            f"DirectorStateMachine initialized: "
            f"idle_timeout={self.idle_timeout_ms}ms, "
            f"search_timeout={self.search_timeout_ms}ms, "
            f"recover_timeout={self.recover_timeout_ms}ms"
        )

    def create_initial_context(self) -> DirectorContext:
        """创建初始上下文"""
        return DirectorContext(
            current_state=DirectorState.IDLE,
            current_subject=None,
            recording=False,
            last_event_timestamp=0,
            last_transition_timestamp=0,
            highlight_segments=[],
            idle_duration_ms=0,
        )

    def process_events(
        self,
        events: List[VideoEvent],
        context: DirectorContext,
        current_timestamp_ms: int,
    ) -> Tuple[List[CameraAction], DirectorContext]:
        """
        处理事件列表，生成命令和新上下文

        Args:
            events: 事件列表
            context: 当前上下文
            current_timestamp_ms: 当前时间戳

        Returns:
            (命令列表, 新上下文)
        """
        actions = []
        new_context = context

        # 处理每个事件
        for event in events:
            event_actions, new_context = self._process_event(
                event, new_context, current_timestamp_ms
            )
            actions.extend(event_actions)

        # 检查超时
        timeout_actions, new_context = self._check_timeouts(
            new_context, current_timestamp_ms
        )
        actions.extend(timeout_actions)

        return actions, new_context

    def _process_event(
        self,
        event: VideoEvent,
        context: DirectorContext,
        current_timestamp_ms: int,
    ) -> Tuple[List[CameraAction], DirectorContext]:
        """处理单个事件"""
        actions = []
        new_context = DirectorContext(**vars(context))  # 复制上下文

        # 根据当前状态和事件类型决定行为
        if context.current_state == DirectorState.IDLE:
            actions, new_context = self._handle_idle_state(event, new_context, current_timestamp_ms)

        elif context.current_state == DirectorState.SEARCH:
            actions, new_context = self._handle_search_state(event, new_context, current_timestamp_ms)

        elif context.current_state == DirectorState.TRACK:
            actions, new_context = self._handle_track_state(event, new_context, current_timestamp_ms)

        elif context.current_state == DirectorState.RECORD:
            actions, new_context = self._handle_record_state(event, new_context, current_timestamp_ms)

        elif context.current_state == DirectorState.HIGHLIGHT:
            actions, new_context = self._handle_highlight_state(event, new_context, current_timestamp_ms)

        elif context.current_state == DirectorState.RECOVER:
            actions, new_context = self._handle_recover_state(event, new_context, current_timestamp_ms)

        # 更新最后事件时间
        new_context.last_event_timestamp = event.end_ms

        return actions, new_context

    def _handle_idle_state(
        self, event: VideoEvent, context: DirectorContext, current_timestamp_ms: int
    ) -> Tuple[List[CameraAction], DirectorContext]:
        """处理 IDLE 状态"""
        actions = []

        if event.event_type == "subject_entry":
            # 主体进入 → 开始跟踪
            actions.append(self._create_action(
                "start_tracking",
                event.start_ms,
                {"subject_id": event.key_subjects[0] if event.key_subjects else "unknown"}
            ))
            context.current_state = DirectorState.TRACK
            context.current_subject = event.key_subjects[0] if event.key_subjects else None
            context.last_transition_timestamp = current_timestamp_ms
            logger.info(f"IDLE → TRACK: subject entered")

        elif event.event_type in ["action_peak", "emotion_change"]:
            # 检测到重要事件但无主体 → 搜索模式
            actions.append(self._create_action("search_subject", event.start_ms))
            context.current_state = DirectorState.SEARCH
            context.last_transition_timestamp = current_timestamp_ms
            logger.info(f"IDLE → SEARCH: event detected but no subject")

        return actions, context

    def _handle_search_state(
        self, event: VideoEvent, context: DirectorContext, current_timestamp_ms: int
    ) -> Tuple[List[CameraAction], DirectorContext]:
        """处理 SEARCH 状态"""
        actions = []

        if event.event_type == "subject_entry" and event.key_subjects:
            # 找到主体 → 开始跟踪
            actions.append(self._create_action(
                "start_tracking",
                event.start_ms,
                {"subject_id": event.key_subjects[0]}
            ))
            context.current_state = DirectorState.TRACK
            context.current_subject = event.key_subjects[0]
            context.last_transition_timestamp = current_timestamp_ms
            logger.info(f"SEARCH → TRACK: subject found")

        return actions, context

    def _handle_track_state(
        self, event: VideoEvent, context: DirectorContext, current_timestamp_ms: int
    ) -> Tuple[List[CameraAction], DirectorContext]:
        """处理 TRACK 状态"""
        actions = []

        if event.event_type == "action_peak" and event.highlight_score >= 0.7:
            # 动作高潮 → 开始录制
            actions.append(self._create_action("start_recording", event.start_ms))
            context.current_state = DirectorState.RECORD
            context.recording = True
            context.last_transition_timestamp = current_timestamp_ms
            logger.info(f"TRACK → RECORD: action peak detected")

        elif event.event_type == "subject_exit":
            # 主体离开 → 尝试恢复
            actions.append(self._create_action("subject_lost", event.start_ms))
            context.current_state = DirectorState.RECOVER
            context.last_transition_timestamp = current_timestamp_ms
            logger.info(f"TRACK → RECOVER: subject exited")

        else:
            # 持续跟踪
            if event.camera_suggestion:
                actions.append(self._create_action(
                    "adjust_tracking",
                    event.start_ms,
                    {"mode": event.camera_suggestion}
                ))

        return actions, context

    def _handle_record_state(
        self, event: VideoEvent, context: DirectorContext, current_timestamp_ms: int
    ) -> Tuple[List[CameraAction], DirectorContext]:
        """处理 RECORD 状态"""
        actions = []

        if event.event_type == "action_peak" and event.highlight_score >= 0.8:
            # 超高光时刻 → 标记
            actions.append(self._create_action("mark_highlight", event.start_ms))
            context.current_state = DirectorState.HIGHLIGHT
            context.highlight_segments.append((event.start_ms, event.end_ms))
            context.last_transition_timestamp = current_timestamp_ms
            logger.info(f"RECORD → HIGHLIGHT: super highlight detected")

        elif event.event_type in ["subject_exit", "scene_transition"]:
            # 事件结束 → 停止录制，返回跟踪
            actions.append(self._create_action("stop_recording", event.end_ms))
            context.current_state = DirectorState.TRACK if event.event_type != "subject_exit" else DirectorState.RECOVER
            context.recording = False
            context.last_transition_timestamp = current_timestamp_ms
            logger.info(f"RECORD → {context.current_state.value.upper()}: event ended")

        else:
            # 持续录制
            if event.camera_suggestion:
                actions.append(self._create_action(
                    "adjust_recording",
                    event.start_ms,
                    {"mode": event.camera_suggestion}
                ))

        return actions, context

    def _handle_highlight_state(
        self, event: VideoEvent, context: DirectorContext, current_timestamp_ms: int
    ) -> Tuple[List[CameraAction], DirectorContext]:
        """处理 HIGHLIGHT 状态"""
        actions = []

        # 高光状态持续一段时间后自动返回录制
        if current_timestamp_ms - context.last_transition_timestamp > 2000:  # 2秒
            context.current_state = DirectorState.RECORD
            logger.info(f"HIGHLIGHT → RECORD: highlight marked")

        return actions, context

    def _handle_recover_state(
        self, event: VideoEvent, context: DirectorContext, current_timestamp_ms: int
    ) -> Tuple[List[CameraAction], DirectorContext]:
        """处理 RECOVER 状态"""
        actions = []

        if event.event_type == "subject_entry" and event.key_subjects:
            # 重新找到主体 → 恢复跟踪
            actions.append(self._create_action(
                "resume_tracking",
                event.start_ms,
                {"subject_id": event.key_subjects[0]}
            ))
            context.current_state = DirectorState.TRACK
            context.current_subject = event.key_subjects[0]
            context.last_transition_timestamp = current_timestamp_ms
            logger.info(f"RECOVER → TRACK: subject recovered")

        return actions, context

    def _check_timeouts(
        self, context: DirectorContext, current_timestamp_ms: int
    ) -> Tuple[List[CameraAction], DirectorContext]:
        """检查超时"""
        actions = []
        new_context = DirectorContext(**vars(context))

        time_since_transition = current_timestamp_ms - context.last_transition_timestamp

        if context.current_state == DirectorState.SEARCH:
            if time_since_transition > self.search_timeout_ms:
                # 搜索超时 → 返回空闲
                actions.append(self._create_action("search_timeout", current_timestamp_ms))
                new_context.current_state = DirectorState.IDLE
                new_context.last_transition_timestamp = current_timestamp_ms
                logger.info(f"SEARCH → IDLE: search timeout")

        elif context.current_state == DirectorState.RECOVER:
            if time_since_transition > self.recover_timeout_ms:
                # 恢复超时 → 返回空闲
                actions.append(self._create_action("recover_timeout", current_timestamp_ms))
                new_context.current_state = DirectorState.IDLE
                new_context.current_subject = None
                new_context.last_transition_timestamp = current_timestamp_ms
                logger.info(f"RECOVER → IDLE: recover timeout")

        elif context.current_state == DirectorState.RECORD:
            if time_since_transition > 30000:  # 30秒最大录制时长
                # 录制时间过长 → 强制停止
                actions.append(self._create_action("max_recording_time", current_timestamp_ms))
                new_context.current_state = DirectorState.TRACK
                new_context.recording = False
                new_context.last_transition_timestamp = current_timestamp_ms
                logger.info(f"RECORD → TRACK: max recording time reached")

        return actions, new_context

    def _create_action(
        self,
        action_type: str,
        timestamp_ms: int,
        params: Optional[dict] = None
    ) -> CameraAction:
        """创建设备命令"""
        return CameraAction(
            action_id=f"action_{timestamp_ms}_{action_type}",
            action_type=action_type,
            timestamp_ms=timestamp_ms,
            params=params or {},
        )
