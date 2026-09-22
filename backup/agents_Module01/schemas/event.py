"""
Event Schema

Represents detected events in media.
"""

from typing import Optional, Dict, Any
from enum import Enum
from pydantic import BaseModel, Field


class EventType(str, Enum):
    """Event types"""
    # Action events
    ACTION_START = "action_start"
    ACTION_PEAK = "action_peak"
    ACTION_END = "action_end"

    # Emotion events
    CELEBRATION = "celebration"
    EXCITEMENT = "excitement"
    TENSION = "tension"
    CALM = "calm"

    # Social events
    CONVERSATION = "conversation"
    GROUP_ACTIVITY = "group_activity"
    INTERACTION = "interaction"

    # Environmental events
    SCENE_CHANGE = "scene_change"
    LIGHTING_CHANGE = "lighting_change"

    # Technical events
    MOTION_START = "motion_start"
    MOTION_STOP = "motion_stop"
    SUBJECT_ENTER = "subject_enter"
    SUBJECT_EXIT = "subject_exit"

    # Generic
    HIGHLIGHT = "highlight"
    UNKNOWN = "unknown"


class Event(BaseModel):
    """
    Detected event in media

    Used by all agents to understand what's happening.
    """
    event_id: str
    event_type: EventType

    # Timing
    start_ms: int = Field(ge=0)
    end_ms: int = Field(ge=0)
    peak_ms: Optional[int] = None

    # Source
    source_id: str = Field(description="Source media ID")
    frame_index: Optional[int] = None

    # Detection
    confidence: float = Field(ge=0.0, le=1.0)
    detector: str = Field(description="What detected this: yolo, qwen_vl, human")

    # Subject
    subject_id: Optional[str] = None
    subject_type: Optional[str] = None

    # Context
    description: Optional[str] = None
    tags: list[str] = Field(default_factory=list)
    metadata: Dict[str, Any] = Field(default_factory=dict)

    # Validation
    human_verified: bool = False
    verified_by: Optional[str] = None

    def duration_ms(self) -> int:
        """Get event duration in milliseconds"""
        return self.end_ms - self.start_ms

    def overlaps(self, other: "Event") -> bool:
        """Check if this event overlaps with another"""
        return not (
            self.end_ms <= other.start_ms or
            self.start_ms >= other.end_ms
        )
